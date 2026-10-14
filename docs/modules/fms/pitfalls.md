# 注意事项与已知坑点

> 使用 fms（财务管理）模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 fms 表受租户拦截器管控，但 DO 未映射 tenantId 字段

**问题**: fms 所有 DO 只继承 `BaseDO`（代码里看不到 tenantId 字段），但建表 SQL 中每张表都有 `tenant_id bigint NOT NULL DEFAULT 0` 列，且唯一索引普遍包含 tenant_id（如 `UNIQUE (company_code, deleted, tenant_id)`）。在定时任务、MQ 消费、自建异步线程等无租户上下文的场景直接调用 fms Service 会抛异常。

**原因**: 框架 `TenantDatabaseInterceptor.computeIgnoreTable`（yudao-spring-boot-starter-biz-tenant）只对两类表跳过租户过滤：继承 `TenantBaseDO` 的表、标注 `@TenantIgnore` 的表。fms DO 属于"两者皆非"，因此 MyBatis-Plus 租户插件会对全部 fms 表自动拼 `tenant_id = ?`；取租户值时调用 `TenantContextHolder.getRequiredTenantId()`，无上下文即抛错。fms 的数据隔离是"SQL 层 tenant_id + 业务层 account_set_id + fms_account_user 授权"双重机制。

**解决**: 不要在 DO/Mapper 手写 tenant_id 条件（DO 无该字段，也不需要）；在非 Web 线程调用 fms Service 前必须用 `TenantUtils.execute(tenantId, ...)` 包裹补齐租户上下文；单测不走 Web 层时注意 mock 或设置 `TenantContextHolder`。跨租户查询（如预置模板）必须走 `@TenantIgnore` 表或在 `TenantContextHolder.isIgnore()` 下执行。

### 1.2 两张 @TenantIgnore 模板表为全局共享数据

**问题**: `FmsSubjectTemplateDO`（表 `fms_subject_template`，科目模板）和 `FmsReportTemplateDO`（表 `fms_report_template`，三大报表行次模板）标注了 `@TenantIgnore`，查询不过滤租户，所有租户读到同一份模板。

**原因**: 这两张表存放的是产品级预置数据（会计准则科目模板、报表行次与公式），账套初始化时由 `FmsSubjectService.initializeDefaultSubjects` 等逻辑复制为账套私有数据；模板本身设计为跨租户共享，因此用注解豁免租户过滤。

**解决**: 直接修改这两张表的数据会影响所有租户后续新建账套的初始化结果；个性化行次、科目应在账套私有表（`fms_finance_indicator`、`fms_subject` 等）上修改，不要动模板表。

## 2. 权限相关

### 2.1 数据权限完全依赖 Service 层显式 userId 校验，simple-list 无 @PreAuthorize

**问题**: 模块内大量 `simple-list` 端点没有 `@PreAuthorize` 注解（如 `FmsSubjectController#getSubjectSimpleList`），仅要求登录。若新增端点时绕过 Service 直接查 Mapper，会完全绕开账套数据隔离。

**原因**: fms 不靠菜单权限码做数据隔离，而是 Service 方法显式接收 `userId` 参数，统一走 `FmsAccountSetService` 的三个校验方法：`validateAccountSetReadPermission` / `validateAccountSetWritePermission` / `validateAccountSetOwnerPermission`，内部查 `fms_account_user` 按 `FmsAccountUserLevelEnum`（OWNER=1 主管、WRITE=3 会计、READ=2 查看者）判定；`isReadable` 对三个级别全部放行。注意级别数值大小与权限强度不是线性关系（OWNER=1 最强）。

**解决**: Controller 必须用 `SecurityFrameworkUtils.getLoginUserId()` 取当前用户并传入 Service；新写 Service 方法涉及账套数据时，第一步就调用对应 validate 方法（读用 Read、写用 Write、账套设置/成员管理用 Owner）。自定义端点若遗漏 userId 参数，权限校验形同虚设。

## 3. 事务与并发相关

### 3.1 lockAccountSet 的 FOR UPDATE 行锁必须在事务内调用才有效

**问题**: `FmsAccountSetServiceImpl#lockAccountSet` 底层是 `BaseMapperX#selectOneForUpdate`，即 `selectOne(queryWrapper.last("FOR UPDATE"))`。在无事务的方法里调用时，行锁随 auto-commit 立即释放，串行化完全失效。

**原因**: 凭证创建/更新/删除/整理/移动（`FmsVoucherServiceImpl` 的 createVoucher、updateVoucher、deleteVoucherList、tidyVoucher、moveVoucher）以及结账/反结账（`FmsClosingPeriodServiceImpl#validateCloseTargetPeriod`、`cancelClosePeriod`）都依赖该行锁串行化同一账套的凭证号分配与结账状态变更。

**解决**: 新增涉及凭证编号分配、凭证号整理、结账状态变更的写操作时，方法必须加 `@Transactional(rollbackFor = Exception.class)` 并在写前调用 `accountSetService.lockAccountSet(accountSetId)`；纯查询不要加锁。

### 3.2 凭证号整理/移动采用"负数临时号"两段更新

**问题**: `tidyVoucher` / `moveVoucher` 先把涉及凭证的号码批量改成负数临时号（`-index - 1`），再用第二次 `updateBatch` 写入最终号码，而不是一步到位。

**原因**: 代码注释明确说明（FmsVoucherServiceImpl 约 322、375 行）：`updateBatch` 逐条更新仍会触发凭证号唯一键校验，直接写最终号码可能与尚未更新的原号码冲突；负数临时号不占用正常号段，可在同一事务内安全完成号码交换。另外 `createVoucher` 捕获 `DuplicateKeyException` 转为 `VOUCHER_NUMBER_DUPLICATE`，注释说明是兼容尚未移除凭证业务唯一索引的存量数据库。

**解决**: 自行实现改号类逻辑时沿用"临时负号 → 最终号"两段式写法并置于事务内，不要试图靠调整单条更新顺序规避唯一键冲突；生产库清理历史唯一索引前不要删除该 catch 分支。

### 3.3 账套初始化是一次性大事务且未加账套行锁

**问题**: `FmsAccountSetServiceImpl#initializeAccountSet` 在一个事务里串行初始化 9 类基础数据（本位币、财务参数、默认凭证字、辅助核算类别、科目、结账模板、结账方案、财务指标，最后回写 `initialized=true`）；重复初始化抛 `ACCOUNT_SET_ALREADY_INITIALIZED`。但 `initialized` 状态是无锁读（`validateAccountSetWritePermission` 内 `selectById`），没有像结账那样调用 `lockAccountSet`。

**原因**: 校验 `accountSet.getInitialized()` 与事务提交回写之间存在竞态窗口，两个并发请求可能都读到 `initialized=false`，各自执行一套初始化，造成重复预置数据或唯一键冲突。

**解决**: 初始化入口做好防并发（前端按钮置灰 + 后端按账套加锁）；如需加固，可在 `initializeAccountSet` 开头补 `lockAccountSet(initializeReqVO.getAccountSetId())`。初始化中途任一步失败整体回滚、不留半初始化账套，可放心重试。

## 4. 依赖注入相关

### 4.1 Service 层循环依赖普遍靠 @Lazy 解决

**问题**: `FmsAccountSetServiceImpl` 注入的 9 个 Service（accountUserService、currencyService、financeParameterService、voucherWordService、auxiliaryTypeService、subjectService、closingSchemeService、financeIndicatorService、closingTemplateService）全部标注 `@Lazy`；`FmsVoucherServiceImpl` 对 closingPeriodService / closingVoucherService、`FmsReportCommonServiceImpl` 对 closingSchemeService 同样如此。

**原因**: fms 各域（config/voucher/closing/report/ledger/home）互相调用密集：账套（config）被几乎所有域引用，而账套初始化又要反向调用各域的 `initializeXxx` 方法；凭证域与结账域互相校验期间状态，形成双向依赖。

**解决**: 在该模块新增 Service 并与上述类互相注入时，启动可能报循环依赖错误；同样加 `@Lazy`，或把公共计算逻辑下沉到无 Controller 的共享 Service（参考 `FmsReportCommonService` 只承载报表公共计算的做法），减少环。

## 5. 状态机相关

### 5.1 凭证状态机简单，但结账生成的凭证只读

**问题**: 凭证状态只有 `PENDING_REVIEW`（待审核）与 `APPROVED`（已审核）双向流转，其他目标状态抛 `VOUCHER_STATUS_INVALID`；批量审核时任何一张凭证状态不符，整批抛异常、无部分成功。结账生成的凭证不能编辑、审核或删除（`VOUCHER_CLOSING_GENERATED_NOT_EDITABLE`）。

**原因**: `FmsVoucherServiceImpl#updateVoucherReviewStatus` 逐张校验 canApprove / canCancel（待审核→已审核、已审核→待审核），任一不符抛错；`validateClosingVoucherEditable` 在编辑、删除、审核入口统一拦截结账凭证。

**解决**: 需要修改结账生成的凭证时必须先反结账对应期间；调用批量审核接口时按"整批成功或整批失败"语义处理异常，不要假设部分成功。

### 5.2 结账校验链长；反结账专用错误码 1_052_105_002 实际未被抛出

**问题**: `closePeriod` 逐月执行完整校验链：未审核凭证（`CLOSING_VOUCHER_PENDING_REVIEW`）→ 初始余额试算平衡 → 凭证号连续（`CLOSING_VOUCHER_NUMBER_DISCONTINUOUS`）→ 损益结转凭证已生成 → 损益余额为零 → 利润表勾稽平衡（`CLOSING_INCOME_STATEMENT_UNBALANCED`）→ 报表科目未映射（`CLOSING_REPORT_SUBJECT_UNMAPPED`）→ 资产负债表平衡。新增科目后若未配置报表公式，科目未映射数 > 0 会直接阻断结账。另外错误码 `CLOSING_NOT_LATEST_PERIOD`（1_052_105_002，"只能反结账最近的已结账期间"）当前没有任何代码路径抛出——`cancelClosePeriod` 不满足条件时抛的是 `CLOSING_PERIOD_NOT_CLOSED`，且实际支持从最近已结账期间连续往前反结账到目标期间。

**原因**: `getClosingOverview` 汇总全部前置条件计算 `canClose`；反结账从 `selectLatestByAccountSetId` 取最近期间逐月向前取消，历史预留的"只能反最近期间"约束已放开，错误码未清理。

**解决**: 结账失败时先调结账概况接口查看 `canClose` 与各 `*UnmappedSubjectCount` 字段定位卡点；新增科目后同步维护利润表/资产负债表公式；集成测试断言反结账错误时不要断言 1_052_105_002。

## 6. 报表公式相关

### 6.1 现金流量表公式非法字符静默按零处理

**问题**: 现金流量表行次公式经 Aviator 引擎求值（`FmsCashFlowStatementServiceImpl#calculateCashFlowFormula`），将 BA/IN/EX/L 参数替换为变量后，若表达式含非法字符（不匹配 `CASH_FLOW_EXPRESSION_PATTERN`），直接返回 `BigDecimal.ZERO`，不抛任何错误。

**原因**: 这是防止公式注入任意代码的兜底逻辑（FmsCashFlowStatementServiceImpl 约 493-496 行），公式为空时同样按零处理；报表金额异常显示为 0 时无任何日志提示。

**解决**: 排查现金流量表某行金额恒为 0 的问题时，先检查公式配置是否混入全角字符、非法运算符或引用了不存在的行次；公式合法性以保存时 `FmsReportCommonService` 的 `REPORT_FORMULA_*` 系列校验为准，计算期静默容错比保存期校验宽松，两者行为不一致需心中有数。

## 7. 数据模型相关

### 7.1 两处表名与 DO 类名不一致

**问题**: `FmsClosingSchemeDO`（结账方案）映射表是 `fms_closing` 而非 `fms_closing_scheme`；`FmsAuxiliaryCombinationDO`（辅助核算组合）映射表是 `fms_assist_combination`（assist 而非 auxiliary）。

**原因**: 历史命名遗留，通过 `@TableName` 显式指定，且两张表都开了 `autoResultMap = true`（JSON 字段依赖）。

**解决**: 编写 SQL 脚本、DDL、排错时以 `@TableName` 注解为准，不要按类名猜测表名；`fms_closing_period`（结账期间登记）才是真正的"结账记录"表，与 `fms_closing`（结账方案）注意区分。

### 7.2 预置 JSON 与科目初始化强耦合

**问题**: 结账模板、结账方案的预置数据（`resources/fms/closing/closing-template-presets.json`、`closing-scheme-presets.json`，财务指标在 `resources/fms/config/finance-indicator-presets.json`）按科目编码引用预置科目；账套初始化时若找不到对应科目，抛 `CLOSING_TEMPLATE_PRESET_SUBJECT_NOT_EXISTS` / `CLOSING_SCHEME_PRESET_SUBJECT_NOT_EXISTS`，导致整个初始化事务回滚。

**原因**: `FmsClosingTemplateServiceImpl#initializeClosingTemplates` 先按账套科目建立 code 索引再转换预置数据，科目初始化（`initializeDefaultSubjects`）必须先于结账模板/方案执行；科目编码还受 `subjectCodeRule`（科目级次编码规则）推导影响。

**解决**: 修改预置 JSON 或科目预置逻辑时保持两者科目编码一致；调整编码规则时注意 `FmsSubjectServiceImpl#expandSubjectCodes` 只扩展存量科目编码，不会同步模板表和预置 JSON 中的编码引用。

## 8. 代码线索与待改进点

### 8.1 科目树向上递归存在死循环隐患

**问题**: `FmsLedgerServiceImpl#getDetailSubjectList` 从有发生额的科目向上补齐父级节点时使用 `while (parentId != null)` 循环（FmsLedgerServiceImpl 186 行有 TODO 标注"尽量不要 while true 死循环"）；若科目数据 `parentId` 成环，线程将永久自旋。

**原因**: 科目层级靠 `parentId` 维护，常规写入路径有 `SUBJECT_PARENT_INVALID`（上级科目必须同账套、同类型同类别）等校验保护，但直接改库或异常导入数据可能造出环。对照实现 `FmsSubjectServiceImpl#getSubjectIdSetWithChildren` 用 `for (int i = 0; i < Short.MAX_VALUE; i++)` 设置了递归上限。

**解决**: 科目写入始终走 Service 校验路径；在其他地方复制"向上递归找父级"逻辑时，参考 `getSubjectIdSetWithChildren` 加循环次数上限，或顺手把该 TODO 修复为带上限的循环。
