# 注意事项与已知坑点

> 使用 hrm 模块时的常见问题、易踩坑点和最佳实践。

## 1. 模块启用与初始化

### 1.1 模块默认被注释禁用，且官方 SQL 脚本不含建表 DDL

**问题**: 拉取代码后启动 yudao-server 发现没有任何 hrm 接口；或放开依赖后启动直接报 `hrm_xxx` 表不存在。

**原因**: 该模块在根 `pom.xml` 中 `<module>yudao-module-hrm</module>` 和 `yudao-server/pom.xml` 中 `yudao-module-hrm` 依赖默认均处于注释状态；而 `sql/mysql/ruoyi-vue-pro.sql` 只包含 hrm 的菜单（system_menu）、字典（约 40 个 `hrm_*` 字典类型）、站内信与 `infra_job` 数据（共 288 行含 `hrm_` 的 INSERT），没有任何 `CREATE TABLE hrm_*` 建表语句。

**解决**: 手工放开两个 pom 中的注释并重新编译；参考 `yudao-module-hrm/src/test/resources/sql/create_tables.sql`（含全部 50 张表）在目标库执行建表；同时初始化 `hrm_salary_option_template` 标准薪资项目录数据——它是全局共享表，`HrmSalaryOptionServiceImpl.syncSalaryOption` 同步标准薪资项时完全依赖它，为空则同步逻辑直接跳过。

### 1.2 请假审批依赖 BPM 流程模型，站内信模板缺失会中断业务

**问题**: 员工提交请假直接报错；或工资条发放、绩效推进等操作莫名整批失败。

**原因**: 两个隐式外部依赖。其一，`HrmAttendanceLeaveServiceImpl.createLeave` 调用 `BpmProcessInstanceApi.createProcessInstance`，流程 key 固定为 `hrm_attendance_leave`（`LEAVE_PROCESS_KEY`），流程变量含 `employeeDeptId`/`employeeId`/`leaveType`/`day` 等，官方 SQL 并未内置该流程模型，未部署时发起流程即抛错、整个事务回滚。其二，`HrmSalarySlipServiceImpl.sendSalarySlipMessage`、绩效通知（`HrmPerformanceAssessmentProcessServiceImpl.notifyPendingStage`/`notifyProcessResult`）、招聘面试（`HrmRecruitInterviewServiceImpl`）、社保月表（`HrmInsuranceMonthEmployeeRecordServiceImpl`）都是裸调 `NotifyMessageSendApi.sendSingleMessageToAdmin`，无 try-catch，对应站内信模板缺失或停用时会抛异常使业务事务回滚（仅员工模块的 `HrmEmployeeServiceImpl.sendEmployeeMessage` 做了 catch 降级）。

**解决**: 在 BPM 管理端创建并部署 key 为 `hrm_attendance_leave` 的流程模型（审批人可基于 `employeeDeptId` 等变量配置）；上线前在 system 模块确认 `MessageTemplateConstants` 中 7 个模板（`hrm_salary_slip_sent`、`hrm_performance_task_pending`、`hrm_performance_process_result`、`hrm_recruit_interview_arranged`、`hrm_insurance_month_record_created`、`hrm_employee_opened`、`hrm_employee_archive_fill`）全部存在且开启。此外门户所有接口（`/hrm/portal/**`）要求登录用户已绑定员工档案（`validateEmployeeBySelf` 查不到即抛 `EMPLOYEE_NOT_EXISTS`），员工须有后台账号且 `HrmEmployeeDO.userId` 已绑定。

## 2. 定时任务相关

### 2.1 三个 Job 预置为停止状态，且 hrmSalaryChangeJob 的参数写死了日期

**问题**: 部署后调薪、员工异动/转正/离职一直不生效；或启用任务后只应用了某个历史日期的调薪记录。

**原因**: `sql/mysql/ruoyi-vue-pro.sql` 中 `infra_job` 预置了三条记录（`hrmSalaryChangeJob`、`hrmEmployeeChangeJob`、`hrmPerformanceAppealTimeoutJob`），`status` 均为 2（暂停）；并且 `hrmSalaryChangeJob` 的 `handler_param` 是写死的 `'2026-08-01'`——`HrmSalaryChangeJob.execute` 在 param 非空时执行 `LocalDate.parse(param)` 按该日期应用调薪，而不是当天。

**解决**: 在「基础设施 - 定时任务」中清空 `hrmSalaryChangeJob` 的任务参数后再启动三个任务（cron 分别为每日 0:10、0:05、每 5 分钟）；只在需要按指定日期补历史数据时才临时填 param。注意三者都标注了 `@TenantJob`，会自动逐租户执行，无需手工遍历租户。

### 2.2 调薪生效 Job 是整批一个事务，一条失败全部回滚

**问题**: 某条调薪记录数据异常时，当天所有员工的调薪都不生效，且日志只有一条异常。

**原因**: `HrmSalaryChangeJob` 调用的 `HrmSalaryEmployeeInfoServiceImpl.applyDueSalaryChanges` 整体标注 `@Transactional(rollbackFor = Exception.class)`，循环内没有逐条 try-catch，任何一条 `saveEffectiveSalaryEmployeeInfo` 抛异常都会回滚全部已处理记录。对比 `HrmEmployeeChangeJob.execute` 对异动/转正/离职三类记录都是逐条 `catch (RuntimeException)` 并 `log.error` 后继续，容错粒度完全不同。

**解决**: 出现整批回滚时优先从 `applyDueSalaryChanges` 的异常栈定位脏数据（常见为薪资项编码与 `hrm_salary_option` 不匹配）；自行扩展 Job 时参照 `HrmEmployeeChangeJob` 的逐条独立容错模式，或把单条处理拆成独立事务（`REQUIRES_NEW`）。

## 3. 多租户相关

### 3.1 标准薪资项目录与平台级默认工资条模板是跨租户共享数据

**问题**: 在自己租户下修改/删除「平台级默认工资条模板」时报错，租户无法直接改平台默认模板；排查薪资项数据时发现所有租户看到同一份标准薪资项目录。

**原因**: 两处刻意的跨租户设计。`HrmSalaryOptionTemplateDO` 标注了 `@TenantIgnore`，表 `hrm_salary_option_template` 完全不参与租户隔离；平台级默认工资条模板固定以 `tenant_id = 0`（`TenantUtils.GLOBAL_TENANT_ID`）保存，`HrmSalarySlipTemplateDO` 继承 `TenantBaseDO`，读取时通过 `TenantUtils.executeIgnore` 绕过租户拦截器（`HrmSalarySlipTemplateServiceImpl.getGlobalDefaultSalarySlipTemplate`）。更新/删除时，Service 先经 `validateSalarySlipTemplateExists` 找到模板——租户内按 id 查不到会回退平台级默认模板且要求 id 一致——再判断 `defaultStatus = true` 并抛 `SALARY_DATA_ILLEGAL`（1_050_400_014）；**不是**命中 0 行后静默失败。若请求的 id 属于其它租户，则租户内查不到、也不会误回退平台模板，直接抛 `SALARY_SLIP_TEMPLATE_NOT_EXISTS`（1_050_400_011）。

**解决**: 标准薪资项目录由平台侧统一维护，租户差异通过 `syncSalaryOption` 同步到租户隔离的 `hrm_salary_option`（同步会保留租户自己的 `enabled`/`visible`）；前端不要提供对平台级默认模板（`defaultStatus=true`）的编辑/删除入口，租户个性化直接新建自定义模板。

### 3.2 工资条模板改为 TenantBaseDO 后的写入约定

**问题**: 二次开发中手工 `insert` 工资条模板时，若想写平台级默认模板却落到了当前租户（之后读取不到）；或误把租户模板写成 `tenantId = 0`，导致它不再属于该租户、反而可能被平台默认模板的回退/列表逻辑当作平台级默认模板。

**原因**: `HrmSalarySlipTemplateDO` 继承 `TenantBaseDO` 后拥有 `tenantId` 字段。普通上下文中若不显式 `setTenantId`，由租户拦截器按当前租户自动填值（单测 `testCreateSalarySlipTemplate_success` 已覆盖）；而一旦显式设置了 `tenantId`（TenantBaseDO 场景下租户列已存在，MyBatis-Plus 租户插件不会再改写），就会按字面值落库。平台级默认模板必须在 `TenantUtils.executeIgnore(...)` 上下文中显式指定 `tenant_id = 0`（`TenantUtils.GLOBAL_TENANT_ID`）写入。

**解决**: 租户模板交由框架自动填租户，不要手写 `tenantId`；写平台级默认模板时必须包在 `TenantUtils.executeIgnore` 中并显式设 `tenantId = GLOBAL_TENANT_ID`，否则未显式赋值时会被租户拦截器按当前租户填值，无法被 `selectGlobalDefaultTemplate`（按 tenant_id=0 过滤）读到。

## 4. 缓存相关

### 4.1 标准参保数据缓存 7 天且依赖外部 HTTP 接口

**问题**: 参保类型/缴费比例偶尔查不到（返回空），或外部网站调整后数据长期陈旧。

**原因**: `HrmInsuranceStandardServiceImpl.getStandardTypeList`/`getStandardProjectList` 通过 `HttpRequest` 访问 `user.1renshi.com` 与 `shebao100.cn` 两个外部站点（超时 5 秒），并以 `@Cacheable(cacheNames = ...#7d)` 缓存 7 天（Redis Key 见 `RedisKeyConstants`：`hrm:insurance_standard_type:{areaId}`、`hrm:insurance_standard_project:{areaId}:{typeCode}`）。`unless = "#result.isEmpty()"` 保证空结果不缓存，但城市名由 `AreaUtils.getParentIdByType` 推导并剥掉「市/城区」后缀，外部接口匹配不到时只 `log.warn` 后返回空列表，不会重试。

**解决**: 偶发为空属外部站点抖动，重试即可；持续为空时检查 warn 日志中的 `areaId` 是否为非地级市下辖区县等特殊区划。需要强制刷新时可手动删除上述 Redis Key；扩展时不要把该 Service 的方法通过同类内部调用绕过代理，否则 `@Cacheable` 失效。

## 5. 并发与幂等相关

### 5.1 门户打卡没有并发锁，快速双击可能产生重复打卡

**问题**: 员工快速连点两次打卡按钮，出现两条相同类型的上班（或下班）打卡记录。

**原因**: `HrmAttendanceClockServiceImpl.createMyAttendanceClock` 先 `selectList` 查当日已有打卡、计算 `nextClock` 后直接 `insert`，查询与写入之间没有加锁。对比请假创建 `HrmAttendanceLeaveServiceImpl.createLeave`，它显式调用 `employeeService.validateEmployeeExistsForUpdate`（SELECT FOR UPDATE 锁员工行）后再查重叠申请，防止并发创建重叠请假。

**解决**: 前端做按钮防抖/置灰即可覆盖绝大多数场景；要彻底解决可仿照请假的做法对员工行加锁，或给 `(employee_id, type, attendance_time)` 建唯一索引兜底。

### 5.2 BPM 请假状态回写是幂等的，但 businessKey 必须是数字

**问题**: 复用流程监听模式时监听器抛 `NumberFormatException`；反之，审批事件与取消操作并发不会产生脏数据。

**原因**: `HrmAttendanceLeaveStatusListener.onEvent` 中 `Long.parseLong(event.getBusinessKey())` 要求 businessKey 是请假记录 id（`createLeave` 里 `setBusinessKey(String.valueOf(attendanceLeave.getId()))`）；`HrmAttendanceLeaveServiceImpl.updateLeaveApprovalStatus` 只在「processInstanceId 匹配且 `approvalStatus` 仍为 RUNNING」时通过条件更新 `updateApprovalResultByIdAndProcessInstanceIdAndApprovalStatus` 写入一次终态，重复事件或乱序事件（`isProcessEndStatus` 之外的状态）都会被安全忽略。

**解决**: 保持 businessKey = 请假记录 id 的约定；不要绕过 Service 直接 UPDATE `approvalStatus` 字段，否则可能破坏「终态只写一次」的保护，导致后到的 BPM 事件再次覆盖。

### 5.3 月度社保表三个写操作共用全局分布式锁，跨租户互斥且可能返回 423

**问题**: 高峰期或批量操作时，创建首月/次月社保表、删除月度社保表偶发返回 **423「请求失败，请稍后重试」**；A 租户操作时 B 租户的同类操作会一起卡住。

**原因**: `HrmInsuranceMonthRecordServiceImpl` 的 `createFirstMonthRecord` / `createNextMonthRecord` / `deleteMonthRecord` 共用 `HrmInsuranceMonthRecordLockRedisDAO` 提供的**全局分布式锁**，Redis Key 固定为 `hrm:insurance_month_record_mutation_lock`（`RedisKeyConstants.INSURANCE_MONTH_RECORD_MUTATION_LOCK`），不区分租户、跨租户串行。使用 Redisson `tryLock`，等待上限硬编码 10 秒（`LOCK_WAIT_SECONDS`），抢锁超时或等待期间线程被中断均抛全局错误码 `LOCKED`（423）；不设租期、由 Redisson 看门狗续期（各租户的数据仍按租户过滤）。

**解决**: 批量/高频操作做串行或错峰，并对 423 做重试；三个操作本身已是互斥关系，不要再在外层包一层长事务或在锁内调用外部 HTTP、站内信批量发送等慢操作——锁在事务提交或回滚后才释放（`TransactionSynchronization.afterCompletion`），长事务会长时间占用这把全局锁。

### 5.4 月度社保表变更锁必须在事务中获取，且强依赖 Redis

**问题**: 二次开发中直接调用 `HrmInsuranceMonthRecordLockRedisDAO.lock(...)` 抛 `IllegalStateException`（「月度社保表变更锁需要在事务中获得」）；或 Redis 不可用时首月/次月创建、删除直接失败。

**原因**: `lock` 方法先校验 `TransactionSynchronizationManager.isActualTransactionActive()` 与 `isSynchronizationActive()`，只有在 Spring 事务上下文中才能注册 `afterCompletion` 回调来释放锁。三个入口 Service 方法均标注 `@Transactional`，但若通过非事务上下文或绕过 Spring 代理的自调用（同类内部调用）进入，则事务校验失败。此外该锁是唯一的并发保护，没有「仅靠数据库行锁」的降级路径。

**解决**: 始终从事务入口（Controller → Service 代理方法）调用；自调用会绕过事务与锁，如需复用抽独立 Bean。运维上必须保证 Redis/Redisson 可用，否则月度社保表的创建与删除不可用。

### 5.5 锁定读统一走框架 selectOneForUpdate / selectFirstOneForUpdate，Wrapper 有约束

**问题**: 二次开发复制旧写法拼 `.last("FOR UPDATE")` 加锁，在 SQL Server（不支持 `FOR UPDATE`/`LIMIT`）或 Oracle（不支持 `LIMIT 1 FOR UPDATE`）上报语法错误；或 Wrapper 里带了 `last`/`groupBy`/`having`/自定义参数别名，锁定读直接抛 `IllegalArgumentException`；或条件不唯一时 `selectOneForUpdate` 抛 `TooManyResultsException`。

**原因**: 框架已将锁定读重写为 `SelectForUpdateMethod` 内置查询 + `ForUpdateInnerInterceptor`（拦截器链末尾按方言改写：SQL Server 生成 `WITH (UPDLOCK, ROWLOCK)` 与 `TOP (1)`，Oracle 的首行锁定改为「查候选主键 → 按主键加锁 → 重读校验」的多次查询，最多重试 5 次后抛 `LOCKED`）。hrm 内部模式：员工/参保方案/工资表/社保表等按 `selectOneForUpdate(xxx::getId, id)` 锁单行（`HrmEmployeeMapper`、`HrmInsuranceSchemeMapper` 等）；`selectFirstOneForUpdate` 用于按业务条件锁首行（`HrmInsuranceMonthRecordMapper` 月度表、`HrmSalaryOptionMapper` 含已删除的薪资项目）；绩效流程用 `selectOneForUpdate` 锁阶段行串行化推进。

**解决**: 加锁读一律用框架方法并放在 `@Transactional` 内（否则锁随 auto-commit 立即释放）；`selectOneForUpdate` 的条件要能唯一定位一行，多于 1 条会抛 `TooManyResultsException`；`selectFirstOneForUpdate` 未设置排序时返回任意一条满足条件的记录，只适合「判断是否存在/加锁兜底」场景，需要确定性时显式 `orderBy`；Wrapper 不能使用 `last`、`groupBy`、`having`、参数别名（内置查询只支持实体条件、普通条件与排序）。

## 6. 状态机相关

### 6.1 月度工资表只能向前流转，且只能删除最新一张

**问题**: 想修改或重算历史月份的工资被状态错误码拦截；想把某月工资表删掉重建也不行。

**原因**: `HrmSalaryMonthRecordServiceImpl` 的状态机为 UNCOMPUTED → COMPUTED → HISTORY：`createNextMonthRecord` 会自动把最近一张工资表置为 HISTORY 再建下月表；`deleteMonthRecord` 只允许删除最新的工资表（`SALARY_MONTH_RECORD_NOT_LATEST`）且至少保留一张（`SALARY_MONTH_RECORD_CANNOT_DELETE_ONLY`）；发放工资条前校验状态非 UNCOMPUTED（`HrmSalarySlipSendRecordServiceImpl.sendSalarySlip`）。核算入口 `computeMonthRecord` 还会先 `validateMonthRecordEditableForUpdate` 加行锁。

**解决**: 核算/发放前先确认状态；历史月数据有误时通过新建更正月份处理，不要直接改库绕过状态机（工资表与工资条、社保表之间存在快照引用，直接改库会造成对不上账）。

### 6.2 绩效计划启动时校验所有必办节点处理人必须绑定后台账号

**问题**: 给批量员工发起绩效考核时整体失败，报「绩效必办节点处理人【xx】未绑定后台账号」。

**原因**: `HrmPerformanceAssessmentProcessServiceImpl.initializeAssessmentStages` 在批量插入阶段前，统一校验每个阶段 `handlerEmployeeId` 对应员工 `userId` 非空，任一不满足即抛 `PERFORMANCE_STAGE_HANDLER_USER_NOT_BOUND`；评分阶段按 `plan.getReviewStages()` 的 rater 解析处理人，解析不到时权重合并到相邻阶段保证合计 100%，若全部无法解析则抛 `PERFORMANCE_REVIEW_STAGE_CONFIG_INVALID`。申诉超期由 `HrmPerformanceAppealTimeoutJob` 处理：`processAppealTimeout` 以 `selectOneForUpdate` + 状态/截止时间双重校验保证幂等，按计划配置的 `appealTimeoutAction` 自动通过或驳回。

**解决**: 发起考核前确保直接上级、自评等处理人都已绑定后台账号；调整评分人配置时留意权重合并规则对最终评分权重的影响；绩效通知依赖站内信模板（见 1.2）。

## 7. 错误码相关

### 7.1 1_050_400_029 与 1_050_400_030 各被两个错误码重复占用

**问题**: 前端按错误码 code 做提示分支、或按 code 做告警统计时，无法区分两组完全不同的业务错误。

**原因**: `enums/ErrorCodeConstants.java` 中 `SALARY_OPTION_CODE_OCCUPIED`（薪资项编码被占用）与 `SALARY_OPTION_STANDARD_CANNOT_MODIFY`（标准薪资项不允许修改或删除）都是 `1_050_400_029`；`SALARY_CHANGE_EFFECT_DATE_INVALID`（调薪生效日期不合法）与 `SALARY_SLIP_ALREADY_SENT`（工资条已发放）都是 `1_050_400_030`。

**解决**: 业务分支判断依赖异常消息或直接捕获具体异常，不要按 code 区分；二次开发新增薪资域错误码时避开 `1_050_400_029/030` 两个值，若修复该冲突需同时排查是否有调用方按旧 code 匹配。

## 8. 数据存储相关

### 8.1 大量业务结构存 JSON 列，SQL 无法直接过滤，且保存考勤组会隐式改其它考勤组

**问题**: 想在 SQL 层按班次、打卡点、工资条选项、绩效评分阶段等字段做筛选或统计做不到；新建/更新一个考勤组后发现其它考勤组的部门与员工范围「莫名其妙」被改动。

**原因**: 该模块大量使用 TypeHandler JSON 列存储复杂结构：`HrmAttendanceGroupDO` 的 `shifts`/`points`/`wifis`/`deductRule`/`specialDates`、`HrmSalarySlipDO.options`、`HrmSalaryMonthEmployeeRecordDO.optionValues`、`HrmPerformancePlanDO` 的 `scopes`/`reviewStages`/`resultConfig` 等，MyBatis-Plus 的查询条件无法下推到 JSON 内部字段。同时 `HrmAttendanceGroupServiceImpl.transferAttendanceGroupScope` 在创建/更新考勤组时会展开子部门、把范围内全部员工收编到本组，并把冲突范围从其它考勤组移除（同一部门/员工只归属一个考勤组）；考勤组匹配 `matchAttendanceGroup` 是全量加载所有组后按「显式员工 > 上级部门 > 默认组」顺序内存匹配。

**解决**: 涉及 JSON 字段的筛选/统计在 Java 层完成或另建宽表；保存考勤组前核对预期「接管」的部门与员工范围，避免误改其它组；员工规模大时注意 `getAttendanceGroupMap` 的全量匹配成本，必要时为统计场景做缓存或预计算（月度考勤统计已由 `HrmAttendanceStatisticsService` 单独实现）。

## 9. 多数据库兼容

### 9.1 不要手写 LIMIT 1 / TOP 1 / ROWNUM

**问题**: 在 Oracle / SQL Server / PostgreSQL 等非 MySQL 数据库下，自定义查询报语法错误，或「取第一条/最近一条」取到错误行数。

**原因**: hrm 内多处「取第一条/最近一条」查询已由写死 MySQL `LIMIT 1` 改为按方言生成：`HrmSalaryConfigMapper.selectFirst`、`HrmSalaryMonthRecordMapper.selectLast`、`HrmRecruitInterviewMapper.selectLatestByCandidateId` 改用 `BaseMapperX.selectFirstOne`（由 MyBatis-Plus 分页插件生成 LIMIT / ROWNUM / OFFSET FETCH）；`HrmSalaryOptionMapper.selectByCodeIncludeDeleted` 通过 `SqlDialectUtils.limitRows(1, false)` 在 `@Select` 中拼装方言分页。MySQL 下行为与原 `LIMIT 1` 完全一致。

**解决**: 二次开发不要在新的自定义 SQL/XML 中手写 `LIMIT 1`、`TOP 1` 或 `ROWNUM`，应使用 `BaseMapperX.selectFirstOne(wrapper)` / `selectFirstOne(column, value)`，或在注解 SQL 中使用 `SqlDialectUtils.limitRows` / `limitParam`。

### 9.2 日期函数（月份、日）也应按方言生成

**问题**: 把员工待办「本月生日」的筛选条件复制到其它查询或在其它数据库中运行时，`MONTH(birthday)` / `DAYOFMONTH(birthday)` 不被支持或语义不同。

**原因**: `HrmEmployeeMapper` 的生日筛选已改用 `SqlDialectUtils.month("birthday")` 与 `SqlDialectUtils.dayOfMonth("birthday")`，按当前路由数据源方言生成（MySQL / H2 仍输出 `MONTH` / `DAYOFMONTH`）；非闰年 2 月仍额外排除 29 日，以与首页日历、年龄计算保持一致。

**解决**: 新增日期函数条件时优先使用 `SqlDialectUtils` 提供的方言方法，不要硬编码 MySQL 函数名。
