# 财务管理模块 (fms)

> 面向中小企业的财务管理系统（FMS），围绕「账套」提供凭证、账簿、报表、期末结账全流程核算能力。

## 模块概述
- **模块路径**: yudao-module-fms
- **业务定位**: 提供多账套财务核算能力：账套初始化与用户授权、会计科目与辅助核算等基础配置、凭证录入/审核/整理、明细账/总账/科目余额表等账簿查询、三大报表（资产负债表/利润表/现金流量表）生成与公式维护、期末结账与损益结转。模块内所有业务数据通过 accountSetId（账套编号）隔离，用户与账套之间通过 `fms_account_user` 授权关联。
- **技术栈**: Spring Boot 2.7.18 / MyBatis-Plus / Swagger v3 (springdoc) / Aviator 表达式引擎（现金流量表公式计算）/ EasyExcel（凭证、科目、余额等导入导出）

## 设计原则
| 原则 | 说明 |
|-----|------|
| 账套隔离 | 所有业务表携带 `account_set_id`，以账套为数据隔离单元；DO 均继承 `BaseDO`（未启用多租户 TenantBaseDO），租户隔离由账套机制替代 |
| 账套级数据权限 | Service 层统一通过 `FmsAccountSetService.validateAccountSetReadPermission / WritePermission / OwnerPermission` 校验当前用户对账套的访问权限，权限级别由 `FmsAccountUserLevelEnum` 定义 |
| 配置与数据快照分离 | 报表采用「配置表 + 期间快照表」双表结构（如 `fms_balance_sheet_config` / `fms_balance_sheet_report`），历史期间报表保存当时的公式快照，不受后续公式调整影响 |
| 表达式化公式 | 报表与结账方案公式统一使用 `L行次`、科目等取数语法（`FmsFormulaRuleEnum`），现金流量表复杂表达式交由 Aviator 引擎求值 |
| 预置数据 JSON 化 | 结账模板、结账方案、首页财务指标的系统预置数据以 resources JSON 维护（`resources/fms/`），随账套初始化导入 |
| 操作留痕 | 凭证增删改、审核、整理、移动及结转凭证生成等关键操作通过 `@LogRecord` 记录操作日志 |

## 核心功能点
| 功能域 | 说明 | 关键实体 |
|-----|------|---------|
| 基础配置 | 账套管理/初始化/用户授权、会计科目（含科目模板导入）、辅助核算类别/项目/组合、币别、凭证字、凭证模板、常用摘要、财务参数、首页财务指标 | FmsAccountSetDO、FmsSubjectDO、FmsAuxiliaryTypeDO、FmsVoucherTemplateDO、FmsFinanceParameterDO |
| 凭证管理 | 凭证录入/修改/删除、审核与反审核、整理（重排凭证号）、移动、附件管理、分页/打印/导出、Excel 导入、凭证汇总统计 | FmsVoucherDO、FmsVoucherEntryDO |
| 账簿查询 | 明细账、总账、科目余额表、多栏账、核算项目明细账/余额表、数量金额明细账/总账，均支持导出 Excel | FmsVoucherEntryDO |
| 财务报表 | 资产负债表、利润表、现金流量表的查询/导出/公式维护/勾稽检查；现金流量表辅助数据（调整项）维护 | FmsBalanceSheetConfigDO、FmsIncomeStatementConfigDO、FmsCashFlowStatementConfigDO |
| 期末结账 | 结账期间管理（结账/反结账）、结账模板（预置 + 自定义）、结账方案、结转损益/方案凭证批量生成 | FmsClosingPeriodDO、FmsClosingSchemeDO、FmsClosingTemplateDO、FmsClosingVoucherDO |
| 财务首页 | 首页经营概览与财务指标明细（指标公式支持报表行次/科目取数） | FmsFinanceIndicatorDO |

## API 接口索引

> 端点总数 141，超过 120，按业务域分节给出控制器级摘要；各端点的完整路径、HTTP 方法与权限标识见对应 `api-{key}.md`。

### 基础配置 (config)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| FmsAccountSetController | 账套管理（创建/更新/初始化/查询） | 5 |
| FmsAccountUserController | 账套用户授权与默认账套设置 | 3 |
| FmsSubjectController | 会计科目（增删改查/状态/使用情况/导入导出） | 11 |
| FmsAuxiliaryTypeController | 辅助核算类别 | 5 |
| FmsAuxiliaryItemController | 辅助核算项目（含 Excel 导入导出） | 10 |
| FmsCurrencyController | 币别 | 5 |
| FmsVoucherWordController | 凭证字 | 5 |
| FmsVoucherTemplateController | 凭证模板 | 5 |
| FmsVoucherTemplateCategoryController | 凭证模板分类 | 5 |
| FmsDigestController | 常用摘要 | 5 |
| FmsFinanceIndicatorController | 首页财务指标 | 5 |
| FmsFinanceParameterController | 财务参数 | 2 |
| FmsInitialBalanceController | 科目初始余额（含试算平衡/导入导出） | 6 |

代表性端点（权限标识前缀 `fms:config:*`）：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|-----|------|------|---------|
| /fms/config/account-set/create | POST | 创建账套 | fms:config:account-set:create |
| /fms/config/account-set/initialize | PUT | 初始化账套 | fms:config:account-set:initialize |
| /fms/config/account-set/list | GET | 获得当前用户账套列表 | fms:config:account-set:query |
| /fms/config/account-user/update | PUT | 更新账套用户列表 | fms:config:account-set:authorize |
| /fms/config/subject/page 等 | - | 科目查询/增删改/导入导出 | fms:config:subject:* |
| /fms/config/initial-balance/trial-balance | GET | 获得试算平衡结果 | fms:config:initial-balance:query |
| /fms/config/finance-parameter/get | GET | 获得财务参数 | fms:config:finance-parameter:query |

### 凭证管理 (voucher)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| FmsVoucherController | 凭证全生命周期：录入/修改/删除/审核/整理/移动/附件/分页/打印/导出/导入/汇总/下一凭证号 | 18 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|-----|------|------|---------|
| /fms/voucher/create | POST | 创建凭证 | fms:voucher:create |
| /fms/voucher/update-review-status | PUT | 审核或反审核凭证 | fms:voucher:review |
| /fms/voucher/tidy | PUT | 整理凭证 | fms:voucher:tidy |
| /fms/voucher/move | PUT | 移动凭证 | fms:voucher:move |
| /fms/voucher/page | GET | 获得凭证分页 | fms:voucher:query |
| /fms/voucher/import | POST | 导入凭证 | fms:voucher:import |
| /fms/voucher/statistics/list | GET | 获得凭证汇总 | fms:voucher:statistics:query |

### 账簿查询 (ledger)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| FmsLedgerController | 明细账/总账/科目余额表/多栏账/核算项目明细账与余额表/数量金额明细账与总账，各含导出 | 17 |

代表性端点（权限标识 `fms:ledger:{明细|总账|余额表}:query/export`）：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|-----|------|------|---------|
| /fms/ledger/detail/list | GET | 获得明细账 | fms:ledger:detail:query |
| /fms/ledger/general/list | GET | 获得总账 | fms:ledger:general:query |
| /fms/ledger/subject-balance/list | GET | 获得科目余额表 | fms:ledger:subject-balance:query |
| /fms/ledger/multi-column/list | GET | 获得多栏账 | fms:ledger:multi-column:query |
| /fms/ledger/auxiliary-detail/list | GET | 获得核算项目明细账 | fms:ledger:detail:query |
| /fms/ledger/quantity-general/list | GET | 获得数量金额总账 | fms:ledger:general:query |

### 财务报表 (report)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| FmsBalanceSheetController | 资产负债表查询/导出/公式更新/勾稽检查 | 4 |
| FmsIncomeStatementController | 利润表查询/导出/公式更新/勾稽检查 | 4 |
| FmsCashFlowStatementController | 现金流量表查询/导出/更新/检查 + 辅助数据维护 | 7 |

代表性端点（权限标识前缀 `fms:report:*`）：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|-----|------|------|---------|
| /fms/report/balance-sheet/get | GET | 获得资产负债表 | fms:report:balance-sheet:query |
| /fms/report/income-statement/update | PUT | 更新利润表公式 | fms:report:income-statement:update |
| /fms/report/cash-flow-statement/get | GET | 获得现金流量表 | fms:report:cash-flow-statement:query |
| /fms/report/cash-flow-statement/adjustment/update | PUT | 更新现金流量辅助数据 | fms:report:cash-flow-statement:update |

### 期末结账 (closing)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| FmsClosingPeriodController | 会计期间查询、结账/反账 | 4 |
| FmsClosingTemplateController | 结账模板增删改查 | 4 |
| FmsClosingSchemeController | 结账方案增删改查与损益/专用结转设置 | 6 |
| FmsClosingVoucherController | 结转损益/方案/批量结转凭证生成 | 3 |

代表性端点（权限标识前缀 `fms:closing:*`）：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|-----|------|------|---------|
| /fms/closing/period/current-month | GET | 获得当前会计期间 | 已认证（无 @PreAuthorize） |
| /fms/closing/period/close | PUT | 结账 | fms:closing:close |
| /fms/closing/period/cancel | DELETE | 反结账 | fms:closing:cancel |
| /fms/closing/voucher/generate-profit-loss | POST | 生成结转损益凭证 | fms:closing:profit-loss |
| /fms/closing/voucher/generate-list | POST | 批量生成结转凭证 | fms:closing:profit-loss |

### 财务首页 (home)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| FmsHomeController | 首页概览与财务指标明细 | 2 |

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|-----|------|------|---------|
| /fms/home/get | GET | 获得首页 | fms:home:query |
| /fms/home/metric-detail | GET | 获得财务指标明细 | fms:home:query |

> 说明：各 Controller 下的 `simple-list`（精简下拉列表）端点多数未加 @PreAuthorize，仅需登录（已认证），用于录凭证等场景的前端下拉；模块无 controller/app 端点。

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|--------|---------|
| fms_account_set | FMS 账套 | BaseDO | company_code、company_name、industry、legal_rep、start_time、accounting_standard |
| fms_account_user | FMS 账套用户 | BaseDO | account_set_id、user_id、default_status、founder、level（成员权限级别） |
| fms_subject | FMS 会计科目 | BaseDO | code、name、parent_id、type、category、balance_direction、quantity_accounting、auxiliary_type_ids |
| fms_subject_template | FMS 科目模板（系统预置科目结构） | BaseDO | 与 fms_subject 同构：code、name、parent_id、type、category |
| fms_auxiliary_type | FMS 辅助核算类别 | BaseDO | name、preset（系统预置）、account_set_id、type |
| fms_auxiliary_item | FMS 辅助核算项目 | BaseDO | code、name、type_id、status、account_set_id、specification、unit |
| fms_assist_combination | FMS 辅助核算组合（科目 + 辅助项目组合） | BaseDO | subject_id、account_set_id、items（辅助核算项目数组） |
| fms_currency | FMS 币别 | BaseDO | code、name、exchange_rate、standard（是否本位币）、account_set_id |
| fms_digest | FMS 常用摘要 | BaseDO | content、account_set_id |
| fms_voucher_word | FMS 凭证字 | BaseDO | name、print_title、default_status、sort、account_set_id |
| fms_voucher_template | FMS 凭证模板 | BaseDO | name、category_id、entries（分录数组）、account_set_id |
| fms_voucher_template_category | FMS 凭证模板分类 | BaseDO | name、account_set_id |
| fms_finance_parameter | FMS 财务参数 | BaseDO | account_set_id、subject_level、科目编码规则、账簿余额方向模式、结账校验开关 |
| fms_finance_indicator | FMS 首页财务指标 | BaseDO | account_set_id、name、code、report_type、formula、sort、status |
| fms_initial_balance | FMS 科目期初余额 | BaseDO | subject_id、auxiliary 启用、期初/本年累计借贷金额与数量、年初金额、auxiliaries |
| fms_voucher | FMS 凭证 | BaseDO | voucher_word_id、voucher_number、voucher_time、attachment、debit/credit/total_amount、status、reviewer_user_id |
| fms_voucher_entry | FMS 凭证分录 | BaseDO | voucher_id、digest、subject_id、subject_code/name（快照）、debit_amount、credit_amount、auxiliaries |
| fms_closing_period | FMS 结账期间 | BaseDO | close_time、account_set_id |
| fms_closing | FMS 结账方案（注意表名无 scheme 后缀） | BaseDO | name、subject_id、formula_rule、time_type、voucher_word_id、digest、voucher_type |
| fms_closing_template | FMS 结账模板 | BaseDO | account_set_id、preset_code、name、category、subject_id、formula_rule |
| fms_closing_voucher | FMS 结账凭证 | BaseDO | scheme_id、voucher_id、voucher_time、amount、closed、account_set_id |
| fms_report_template | FMS 报表模板（预置报表行结构） | BaseDO | name、row_no、formula、type、cash_flow_category、level、editable |
| fms_balance_sheet_config | FMS 资产负债表配置 | BaseDO | name、row_no、formula、editable、sort、account_set_id、level |
| fms_balance_sheet_report | FMS 资产负债表数据（按期间快照公式） | BaseDO | start/end_period、period_type、名称/行次/公式/层级快照 |
| fms_income_statement_config | FMS 利润表配置 | BaseDO | name、row_no、formula、sort、editable、account_set_id、level |
| fms_income_statement_report | FMS 利润表数据（按期间快照公式） | BaseDO | period_type、start/end_period、名称/行次/公式/显示顺序/层级快照 |
| fms_cash_flow_statement_config | FMS 现金流量表配置 | BaseDO | name、row_no、formula、editable、sort、cash_flow_category、account_set_id |
| fms_cash_flow_statement_report | FMS 现金流量表数据（按期间快照公式） | BaseDO | start_period、名称/行次/公式/是否可编辑/层级快照、本期金额 |
| fms_cash_flow_extend_config | FMS 现金流量表扩展配置（补充表） | BaseDO | name、row_no、formula、table_key、extend_type、account_set_id |
| fms_cash_flow_extend_data | FMS 现金流量表扩展数据 | BaseDO | name、row_no、formula、cash_flow_category、本期/本年累计金额、account_set_id |

## 设计模式
| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 快照模式 | FmsBalanceSheetReportDO / FmsIncomeStatementReportDO / FmsCashFlowStatementReportDO | 按会计期间保存报表配置的名称/行次/公式/层级快照，保证历史期间报表不受后续公式调整影响 |
| 表达式求值（Aviator 引擎） | FmsCashFlowStatementServiceImpl | 将现金流量表公式中的 BA/IN/EX/L 参数替换为变量后交由 Aviator 计算复杂表达式 |
| 预置数据外置 | resources/fms/closing/*.json、resources/fms/config/finance-indicator-presets.json | 结账方案/结账模板/财务指标的系统预置数据以 JSON 维护，账套初始化时导入 |

## 依赖关系
- **上游**（本模块依赖）:
  - 业务模块：yudao-module-system（AdminUserApi 用户信息、DeptApi 部门信息）、yudao-module-infra（FileApi 凭证导入错误文件上传）
  - framework starter：yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-mybatis（另以 yudao-spring-boot-starter-test 支撑单测）
  - 三方库：aviator（现金流量表公式计算）
- **下游**（依赖本模块）: 无（仅 yudao-server 聚合打包引入，无其他业务模块依赖）

## 对外暴露的 API
无（模块未提供 api 包与跨模块 Api 接口，仅通过 admin Controller 对前端暴露能力）。

## 详细文档
- [api-closing.md](api-closing.md) - 期末结账
- [api-config.md](api-config.md) - 基础配置
- [api-home.md](api-home.md) - 财务首页
- [api-ledger.md](api-ledger.md) - 账簿查询
- [api-report.md](api-report.md) - 财务报表
- [api-voucher.md](api-voucher.md) - 凭证管理
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
