# 注意事项与已知坑点

> 使用 crm 模块时的常见问题、易踩坑点和最佳实践。

CRM 模块没有使用 Spring Security 的 `@PreAuthorize` 做数据级权限，而是自建了一套 `@CrmPermission` AOP 数据权限体系，加上"公海/负责人/转移"业务规则，坑点集中在数据权限、租户上下文和事务边界三块。

## 1. 数据权限相关（CrmPermission 体系）

### 1.1 @CrmPermission 是 Service 层 AOP 注解，内部 this 调用会绕过校验

**问题**: 在 Service 内部直接 `this.xxx()` 调用带 `@CrmPermission` 的方法（如 `CrmCustomerServiceImpl#putCustomerPool(Long)` 内部调用 `putCustomerPool(CrmCustomerDO)`），数据权限校验不会执行；另外 `CrmCustomerService#createCustomer(CrmCustomerCreateReqBO, Long)`、`getCustomerList` 等内部方法本身没有 `@CrmPermission`，被新 Controller 直接暴露时等于无数据权限。

**原因**: `CrmPermissionAspect`（`framework/permission/core/aop`）是 `@Before("@annotation(crmPermission)")` 的 Spring AOP 切面，只拦截经过代理对象的调用，注解加在 Service 方法而非 Controller 上。

**解决**:
- 跨 Service 调用时通过注入的代理对象调用（CRM 各 Service 之间互查已用 `@Resource @Lazy` 解决循环依赖，参考 `CrmCustomerServiceImpl` 注入 `CrmContactService` 的写法）；
- 同类内部需要走切面/事务时，用 `getSelf()` 模式取代理：`SpringUtil.getBean(getClass())`（见 `CrmCustomerServiceImpl#getSelf()`，`autoPutCustomerPool`、`importCustomerList` 均如此调用）；
- 二开新增 Controller 入口时，确认对应的 Service 方法上有 `@CrmPermission`，或自行调用 `CrmPermissionService#hasPermission` 校验。

### 1.2 两类场景下数据权限校验会被跳过或放行

**问题**: ① 定时任务、BPM 事件回调等无登录用户的调用链（如 `CrmCustomerAutoPutPoolJob` → `autoPutCustomerPool`、`CrmContractStatusListener` → `updateContractAuditStatus`）不经过任何数据权限校验；② 公海客户（`owner_user_id` 为 null 且 `CrmPermissionDO` 无记录）对**所有登录用户**开放 READ 权限。

**原因**: `CrmPermissionAspect#doBefore` 开头 `getUserId() == null` 直接 return（源码注释说明：否则 `CrmPermissionUtils.isCrmAdmin()` 会以 null 用户查角色缓存抛 Null key 异常）；`validatePermission` 中无任何权限记录且要求级别为 READ 时也直接 return。

**解决**:
- 系统内部调用链中不要依赖 `@CrmPermission` 做防线，也不要在该链路上新加 `@CrmPermission` 后以为它生效了（它只会被静默跳过）；
- 公海数据"人人可读"是设计行为，若业务要求公海也对部分人隐藏，需要在 Mapper 查询层（`CrmPermissionUtils#appendPermissionCondition`）另行处理。

### 1.3 transferPermission 在管理员转移时存在 NPE 风险

**问题**: CRM 管理员（拥有 `crm_admin` 角色但本人不是数据负责人）调用任意 transfer 接口并传入 `oldOwnerPermissionLevel` 时，接口抛 NullPointerException。

**原因**: `CrmPermissionServiceImpl#transferPermission` 的校验逻辑是"是负责人 **或** 是管理员"即可通过（`oldPermission == null || !isOwner(...)` 且非管理员才拒绝）；但第 3 步回退老负责人权限时 `oldPermission.getId()` 未判空——管理员本人没有权限记录时 `oldPermission` 为 null。

**解决**: 前端只在当前用户是负责人时传 `oldOwnerPermissionLevel`（`CrmCustomerTransferReqVO` 中该字段本身可空，null 表示直接移除）；二开修复时给第 3 步加 `ObjUtil.equal` 判空。

### 1.4 更新接口锁定了归属字段，改负责人/归属必须走专用接口

**问题**: 通过 update 接口传 `ownerUserId` 想直接换负责人，结果静默不生效：客户负责人没变、操作日志里也没体现。

**原因**: 更新方法在入口处强制清空归属字段——`CrmCustomerServiceImpl#updateCustomer` 第 135 行 `updateReqVO.setOwnerUserId(null)`，`CrmBusinessServiceImpl#updateBusiness` 第 131 行 `setOwnerUserId(null).setStatusTypeId(null)`，`CrmReceivablePlanServiceImpl#updateReceivablePlan` 第 89 行 `setOwnerUserId(null).setCustomerId(null).setContractId(null)`。

**解决**: 负责人变更一律走 `transferCustomer` / `transferBusiness` / `transferContact` / `transferContract`（内部会同步 `CrmPermissionDO`、`ownerTime`，客户还支持级联转移联系人/商机/合同 `toBizTypes`）；新增实体时保持同样约定，避免 update 通道绕过数据权限体系。

## 2. 多租户相关

### 2.1 全部 DO 继承 BaseDO，租户隔离完全依赖 biz-tenant SQL 拦截器

**问题**: 21 张表的 DO（`CrmCustomerDO`、`CrmPermissionDO` 等）全部继承 `BaseDO` 而非 `TenantBaseDO`，代码里完全看不到 `tenantId`；新写 Job 或手写 SQL 时容易出错——Job 忘加 `@TenantJob` 会直接报 `NullPointerException: TenantContextHolder 不存在租户编号`。

**原因**: 租户隔离由 `yudao-spring-boot-starter-biz-tenant` 的 `TenantDatabaseInterceptor` 在 SQL 层统一追加 `tenant_id` 条件并自动填充插入值（`TenantContextHolder#getRequiredTenantId` 无上下文时抛 NPE）；statistics 域的 XML mapper（如 `CrmStatisticsCustomerMapper.xml`）里看不到 tenant_id 是正常现象。

**解决**:
- 新增 CRM 表：建表带 `tenant_id` 列，DO 继承 `BaseDO` 即可，代码中不要手动读写 tenant_id；
- 新增定时任务必须加 `@TenantJob`（参考 `CrmCustomerAutoPutPoolJob`），`TenantJobAspect` 会逐租户并行执行，且框架注释明确要求 Job 幂等——某租户失败重试时，已成功租户会再次执行（`autoPutCustomerPool` 靠 `putCustomerPool` 内部状态校验兜底）；
- 异步线程池注意 `TenantContextHolder` 基于 TransmittableThreadLocal，普通 `new Thread` 不会传递租户上下文。

## 3. 事务相关

### 3.1 createFollowUpRecord 缺少 @Transactional，多表联动非原子

**问题**: 新建跟进记录后，目标对象已被并发删除/状态变化导致后续更新失败时，跟进记录已落库但客户/商机的"最近跟进"字段没更新，出现孤儿跟进记录。

**原因**: `CrmFollowUpRecordServiceImpl#createFollowUpRecord` 没有 `@Transactional`，却在一个方法内：插入 `CrmFollowUpRecordDO` → 按 `bizType` 更新客户/商机/线索/联系人/合同五类表的跟进字段 → 再批量更新 `contactIds`、`businessIds` 的 `contactNextTime`，共 7+ 次写库。

**解决**: 二开时给该方法补 `@Transactional(rollbackFor = Exception.class)`（同模块 `createCustomer`、`transferCustomer` 均有）；或明确接受最终一致并自行补偿。注意对比 `transformClue`（`CrmClueServiceImpl`）：线索转化链路是有事务的。

### 3.2 putCustomerPool 的事务代理与执行顺序敏感

**问题**: ① 修改 `putCustomerPool(CrmCustomerDO)` 内部步骤顺序（比如把删数据权限提到最前）后，公海掉落开始报"没有权限"；② `receiveCustomer` 领取公海后联系人的负责人没有跟着设置，和掉落时的联动不对称。

**原因**: ① 该方法为 protected + `@Transactional`（源码注释："需要 protected 修饰，因为需要在事务中调用"），依赖 `getSelf()` 代理调用才开事务；方法内顺序为：`updateOwnerUserIdById` 置空负责人 → `contactService.updateOwnerUserIdByCustomerId` 联动联系人 → 最后 `permissionService.deletePermission(..., OWNER)`，源码注释明确"需要放在 contactService 后面，不然【客户】数据权限已经被删除，无法操作"（后续调用要靠 OWNER 权限过 `@CrmPermission` 校验）；② `receiveCustomer` 中处理关联联系人的位置留有 `TODO @芋艿：要不要处理关联的联系人？？？`（`CrmCustomerServiceImpl` 第 432 行），尚未实现。

**解决**: 保持既有顺序不动；批量掉落 `autoPutCustomerPool` 逐客户 `try/catch(Throwable)` 且外层故意不加事务（部分成功设计），扩展时不要在循环外包一层 `@Transactional`，否则一个客户失败会回滚整批；如需联系人跟随领取，需自行补齐 TODO 处逻辑。

## 4. 错误码相关

### 4.1 错误码段位存在两处冲突（源码即如此）

**问题**: 按错误码 code 做前端提示映射或日志监控时，两组业务返回同一个 code，文案互相覆盖、无法区分来源：`RECEIVABLE_PLAN_UPDATE_FAIL` 与 `CUSTOMER_NOT_EXISTS` 都是 `1_020_006_000`；`BUSINESS_STATUS_UPDATE_FAIL_USED` 与 `BUSINESS_STATUS_DELETE_FAIL_USED` 都是 `1_020_010_002`。

**原因**: `enums/ErrorCodeConstants.java` 中回款计划段（1_020_005_000）只定义了 `RECEIVABLE_PLAN_NOT_EXISTS` 就越界占用了客户管理段的 `1_020_006_000/001`；商机状态组两个错误码复制粘贴漏改尾号。

**解决**: 新增错误码前先在 `ErrorCodeConstants` 内 grep 目标段位是否已占用；二开项目建议把 `RECEIVABLE_PLAN_UPDATE_FAIL/EXISTS_RECEIVABLE` 迁回 1_020_005_000 段并核对前端引用（注意 `CUSTOMER_NAME_EXISTS` 等带 `{}` 占位符的错误码需 `StrUtil.format` 手工填充，参考 `importCustomerList` 的用法）。

## 5. 状态机相关

### 5.1 合同审批状态机严格受限，回写走同步事件监听

**问题**: 直接 update `audit_status`/`process_instance_id` 绕过状态机后，BPM 回调开始抛"合同不是审核中状态"；或不经提交直接把状态改成审批中，导致无法再次发起审批。

**原因**: `CrmContractServiceImpl` 状态流转约束为：仅 `DRAFT`、`PROCESS` 可编辑（`CONTRACT_UPDATE_FAIL_NOT_DRAFT`）、仅 `DRAFT` 可提交（`submitContract`）、审批结果仅能从 `PROCESS` 变更（`updateContractAuditStatus` 抛 `CONTRACT_UPDATE_AUDIT_STATUS_FAIL_NOT_PROCESS`）；审批结果通过 `CrmContractStatusListener`（同步 `ApplicationListener`，监听 key 为 `crm-contract-audit`）回写，链路上无登录用户、无 `@CrmPermission`，监听器内抛出的异常会沿事件发布链传播。

**解决**: 状态变更只走 `submitContract` / BPM 审批完成回调；二开新增审批域（参考 `CrmReceivableStatusListener` 的同款模式）时，保证监听器幂等并容忍"事件与本地状态不一致"的乱序场景，必要时 catch 后记日志而非继续抛出。

### 5.2 商机结束状态（赢单/输单）不可逆

**问题**: 商机推进到结束状态后想改回推进中，接口直接报"更新商机状态失败，原因：已经是结束状态"，且没有解除接口。

**原因**: `CrmBusinessServiceImpl#updateBusinessStatus` 校验 `business.getEndStatus() != null` 即抛 `BUSINESS_UPDATE_STATUS_FAIL_END_STATUS`；同时重复设置同一状态抛 `BUSINESS_UPDATE_STATUS_FAIL_STATUS_EQUALS`。`endStatus` 一旦写入无重置路径。

**解决**: 赢单/输单前与业务确认；确需重开只能二开放开该校验并评估关联合同、回款数据的一致性。商机创建时状态默认取状态组第一个（`createBusiness` 第 100 行 `getBusinessStatusListByTypeId(...).get(0)`），状态组被引用后不可更新/删除（`BUSINESS_STATUS_UPDATE_FAIL_USED`）。

### 5.3 线索转化：幂等靠 transformStatus 标记，且 BO 重载不校验拥有上限

**问题**: ① 重复点击转化报 `CLUE_TRANSFORM_FAIL_ALREADY`（正常幂等）；② 客户拥有数已达上限的用户仍能通过"线索转化"拿到新客户——与页面新建客户行为不一致。

**原因**: `CrmClueServiceImpl#transformClue` 调用的是 `CrmCustomerServiceImpl#createCustomer(CrmCustomerCreateReqBO, userId)` 内部 BO 重载，该重载**不调用** `validateCustomerExceedOwnerLimit`；而页面的 `createCustomer(CrmCustomerSaveReqVO, userId)` 会校验。转化本身只把线索打上 `transformStatus=true` 并回写 `customerId`，线索记录不删除。

**解决**: 二开新入口调用 BO 重载时自行补上限校验；查询线索列表时注意 `transformStatus` 过滤语义（已转化的线索仍占列表，靠前端/条件区分）。

## 6. 其他

### 6.1 合同/回款序号依赖 Redis 自增，Redis 数据丢失后当天序号会重复

**问题**: 合同（前缀 `HT`）、回款（前缀 `HK`）序号偶发生成重复，接口报 `CONTRACT_NO_EXISTS`（"生成合同序列号重复，请重试"），需用户手动重试。

**原因**: `CrmNoRedisDAO#generate` 用 Redis `INCR + EXPIRE` 两步操作（非原子，expire 每次调用刷新为 1 天），序号格式为 `前缀 + yyyyMMdd + 6 位自增`；Redis 当天数据丢失后自增从 1 重来，与已落库序号冲突，靠 `createContract` 里 `selectByNo` 查重兜底——check-then-insert 之间存在并发窗口。

**解决**: 重试即可（自增会推进）；生产环境开启 Redis 持久化（AOF/RDB）降低丢失概率；量大或强一致场景建议给 `no` 列加唯一索引，把冲突从"查重"提前到"插入"拦截。

### 6.2 Mapper 查询的两个隐蔽细节：DO 类型混用与 selectOne 重名

**问题**: ① `CrmCustomerMapper#selectCountByFollow` 中条件误写为 `CrmClueDO::getFollowUpStatus`（而非 `CrmCustomerDO`），目前因为两个 DO 的列名相同恰好能跑，一旦任何一方改列名即崩；② `selectByCustomerName` 用 `selectOne`，库里存在同名客户时抛 `TooManyResultsException`——客户导入是 check-then-insert 且无唯一约束兜底，并发导入可产生重名。

**原因**: ① lambda 列名解析只看属性对应的列名，不校验实体归属；② `importCustomerList` 用 `selectByCustomerName` 判重后插入，两次并发导入同名客户都能通过校验。

**解决**: 扩展 `CrmCustomerMapper` 时统一引用 `CrmCustomerDO` 的列；客户名强唯一场景加 DB 唯一索引，或把判重改为 `selectList` + 取第一条的容错写法。

## 附：排查提示

- **"没有权限"类报错**: 先查 `crm_permission` 表该 bizType/bizId 的记录（`CrmBizTypeEnum` 定义了 20+ 业务类型，跟进记录、数据权限、操作日志共用），再确认操作人是否负责人或 `crm_admin` 角色（`CrmPermissionUtils#isCrmAdmin`）。
- **统计数据不准**: 统计 SQL 全部手写在 `resources/mapper/statistics/*.xml`，合同相关统计统一过滤 `audit_status = APPROVE`（`${@CrmAuditStatusEnum@APPROVE.status}` OGNL 常量写法，非 SQL 注入入口）；数据不对先核对合同审批状态。
- **操作日志缺失**: 日志由 `mzt-biz-log` 的 `@LogRecord` 打点（各 Service 方法上），同类内部调用必须走 `getSelf()` 代理，否则日志静默丢失（参考 `importCustomerLog`、`receiveCustomerLog` 的调用方式）。
