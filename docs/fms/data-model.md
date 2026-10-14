# 数据模型详情

> fms 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。fms 为面向中小企业的财务管理系统，围绕账套（AccountSet）提供科目、辅助核算、凭证、账簿、三大报表、期末结账全流程核算能力，共 30 张数据表。

## 1. 实体继承体系

FMS 模块全部 30 个 DO 均直接继承 `BaseDO`，**未使用** `TenantBaseDO`（DO 层不映射 `tenant_id` 字段）：

```text
BaseDO (cn.iocoder.yudao.framework.mybatis.core.dataobject)
├── creator      String    创建者（后台用户编号，字符串型留扩展性）
├── createTime   LocalDateTime 创建时间（INSERT 自动填充）
├── updater      String    更新者（INSERT_UPDATE 自动填充）
├── updateTime   LocalDateTime 最后更新时间（INSERT_UPDATE 自动填充）
├── deleted      Boolean   逻辑删除标记（@TableLogic，查询自动过滤）
│
├── TenantBaseDO (yudao-spring-boot-starter-biz-tenant)
│   └── tenantId Long      租户编号
│   —— fms 模块未使用该基类 ——
│
└── FMS 模块 DO（30 个，全部直接继承 BaseDO）
    ├── config 域（15 个）
    │   ├── FmsAccountSetDO               账套
    │   ├── FmsAccountUserDO              账套用户
    │   ├── FmsSubjectDO                  会计科目
    │   ├── FmsSubjectTemplateDO          科目模板   [@TenantIgnore]
    │   ├── FmsAuxiliaryTypeDO            辅助核算类别
    │   ├── FmsAuxiliaryItemDO            辅助核算项目
    │   ├── FmsAuxiliaryCombinationDO     辅助核算组合
    │   ├── FmsCurrencyDO                 币别
    │   ├── FmsDigestDO                   常用摘要
    │   ├── FmsVoucherWordDO              凭证字
    │   ├── FmsVoucherTemplateDO          凭证模板
    │   ├── FmsVoucherTemplateCategoryDO  凭证模板分类
    │   ├── FmsFinanceParameterDO         财务参数
    │   ├── FmsFinanceIndicatorDO         首页财务指标
    │   └── FmsInitialBalanceDO           科目期初余额
    ├── voucher 域（2 个）
    │   ├── FmsVoucherDO                  凭证
    │   └── FmsVoucherEntryDO             凭证分录
    ├── closing 域（4 个）
    │   ├── FmsClosingSchemeDO            结账方案   → 表 fms_closing
    │   ├── FmsClosingTemplateDO          结账模板
    │   ├── FmsClosingVoucherDO           结账凭证
    │   └── FmsClosingPeriodDO            结账期间
    └── report 域（9 个）
        ├── FmsReportTemplateDO           报表模板   [@TenantIgnore]
        ├── FmsBalanceSheetConfigDO       资产负债表配置
        ├── FmsBalanceSheetReportDO       资产负债表数据
        ├── FmsIncomeStatementConfigDO    利润表配置
        ├── FmsIncomeStatementReportDO    利润表数据
        ├── FmsCashFlowStatementConfigDO  现金流量表配置
        ├── FmsCashFlowStatementReportDO  现金流量表数据
        ├── FmsCashFlowExtendConfigDO     现金流量表扩展配置
        └── FmsCashFlowExtendDataDO       现金流量表扩展数据
```

### 使用规则

1. **统一继承 BaseDO**：所有 DO 均含 `creator/create_time/updater/update_time/deleted` 五个公共字段，下文各字段表不再重复列出，仅列业务字段。
2. **租户隔离在 SQL 层而非 DO 层**：物理表仍带 `tenant_id` 列（见 `yudao-module-fms/src/test/resources/sql/create_tables.sql`，其注释声明与 `sql/mysql/fms.sql` 业务字段保持同步），由 `yudao-spring-boot-starter-biz-tenant` 的 `TenantDatabaseInterceptor` 通过 SQL 改写自动追加 `tenant_id` 条件与写入值（`yudao.tenant.ignore-tables` 为空）。
3. **全局共享表**：`FmsSubjectTemplateDO`、`FmsReportTemplateDO` 两个 DO 标注 `@TenantIgnore`，对应表不参与租户 SQL 改写，为全系统共享的预置模板数据。
4. **业务层隔离**：账套内数据隔离依赖 `account_set_id` 外键 + `fms_account_user` 账套用户授权（Owner / Write / Read 三级权限，见 `FmsAccountUserLevelEnum`：1 主管、2 查看者、3 会计），Service 层统一经 `FmsAccountSetService#validateAccountSetReadPermission/WritePermission/OwnerPermission` 校验。
5. **@KeySequence**：全部 DO 声明 `@KeySequence("{表名}_seq")`，用于 Oracle/PostgreSQL 等数据库的主键序列兼容。

## 2. 核心 DO 实体

> JSON 类型字段（`JacksonTypeHandler`）在数据库中以 varchar/text 存储；金额列统一 `decimal(18,2)`，数量列 `decimal(18,4)`，单价/汇率列 `decimal(18,6)`（结账凭证金额为 `decimal(24,6)`）。索引信息来源于与业务建表 SQL 同步的测试建表脚本 `yudao-module-fms/src/test/resources/sql/create_tables.sql`。

### 2.1 账套聚合（config）

#### FmsAccountSetDO (fms_account_set)

账套是 FMS 全模块的数据隔离根实体，除科目模板/报表模板外，所有表都通过 `account_set_id` 从属于账套。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| companyCode | String | company_code | 公司编码 |
| companyName | String | company_name | 公司名称 |
| companyProfile | String | company_profile | 公司简介 |
| industry | String | industry | 所在行业 |
| location | String | location | 所在地 |
| legalRepresentative | String | legal_representative | 法人代表 |
| legalRepresentativeIdNumber | String | legal_representative_id_number | 身份证号 |
| businessLicenseNumber | String | business_license_number | 营业执照号 |
| organizationCode | String | organization_code | 组织机构代码 |
| remark | String | remark | 备注 |
| contactName | String | contact_name | 联系人 |
| officeTelephone | String | office_telephone | 办公电话 |
| mobile | String | mobile | 手机号码 |
| faxNumber | String | fax_number | 传真号码 |
| qqNumber | String | qq_number | QQ 号码 |
| email | String | email | 邮箱 |
| otherContact | String | other_contact | 其他联系方式 |
| address | String | address | 详细地址 |
| currencyId | Long | currency_id | 记账本位币，关联 FmsCurrencyDO.id |
| startTime | LocalDateTime | start_time | 启用期间（账套启用时间） |
| standard | Integer | standard | 会计制度，枚举 FmsAccountingStandardEnum（1 小企业会计准则 2013） |
| initialized | Boolean | initialized | 是否已完成初始化（期初建账） |

**继承**: BaseDO
**索引**: `UNIQUE (company_code, deleted, tenant_id)` — 同一租户下公司编码唯一（逻辑删除感知）

#### FmsAccountUserDO (fms_account_user)

账套成员授权表，是业务层数据权限的核心：用户与账套的多对多关系。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| userId | Long | user_id | 后台用户编号，关联 system 模块 AdminUserDO.id |
| defaultStatus | Boolean | default_status | 是否该用户的默认账套 |
| founder | Boolean | founder | 是否账套创建人 |
| level | Integer | level | 成员权限级别，枚举 FmsAccountUserLevelEnum（1 主管、2 查看者、3 会计） |

**继承**: BaseDO
**索引**: 仅主键索引；业务上依赖 (account_set_id, user_id) 组合查询保证一用户一账套一条授权

#### FmsFinanceParameterDO (fms_finance_parameter)

账套级财务参数，每账套一条，控制科目编码规则与结账校验行为。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| level | Integer | level | 科目层级上限，默认 4 |
| subjectCodeRule | String | subject_code_rule | 科目编码规则，默认 "4-2-2-2" |
| ledgerBalanceMode | Integer | ledger_balance_mode | 账簿余额方向模式，枚举 FmsLedgerBalanceModeEnum（1 与科目方向相同、2 与科目方向相反） |
| deficitCheck | Boolean | deficit_check | 是否检查现金及银行存款科目赤字，默认 false |
| voucherReviewRequired | Boolean | voucher_review_required | 结账前是否要求凭证审核，默认 false |
| assetPeriodLocked | Boolean | asset_period_locked | 生成折旧凭证后是否锁定以前期间资产卡片，默认 false |
| taxpayerName | String | taxpayer_name | 纳税人名称 |
| taxpayerNumber | String | taxpayer_number | 纳税人识别号 |

**继承**: BaseDO
**索引**: `UNIQUE (account_set_id, deleted, tenant_id)` — 每账套仅一条参数

#### FmsCurrencyDO (fms_currency)

账套内核算币种，本位币（standard = true）供外币折算。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| code | String | code | 币种编码 |
| name | String | name | 币种名称 |
| exchangeRate | BigDecimal | exchange_rate | 汇率，decimal(18,6) |
| standard | Boolean | standard | 是否本位币 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: `UNIQUE (account_set_id, code, deleted, tenant_id)` — 账套内币种编码唯一

#### FmsDigestDO (fms_digest)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| content | String | content | 摘要内容（NOT NULL） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsVoucherWordDO (fms_voucher_word)

凭证字即凭证类型字（记、收、付、转等），凭证头通过 voucherWordId 引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| name | String | name | 凭证字（如：记） |
| printTitle | String | print_title | 打印标题 |
| defaultStatus | Boolean | default_status | 是否默认凭证字 |
| sort | Integer | sort | 显示顺序 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: 仅主键索引

### 2.2 科目与辅助核算聚合（config）

#### FmsSubjectDO (fms_subject)

会计科目树，凭证分录、期初余额、结账方案等全部围绕科目展开，是全模块引用最密集的实体。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| code | String | code | 科目编码（按财务参数 subjectCodeRule 分级编码） |
| name | String | name | 科目名称 |
| parentId | Long | parent_id | 上级科目编号，关联 FmsSubjectDO.id（自引用），根节点为 0 |
| type | Integer | type | 科目类型，枚举 FmsSubjectTypeEnum（1 资产、2 负债、3 所有者权益、4 成本、5 损益、6 共同） |
| category | Integer | category | 科目类别 |
| balanceDirection | Integer | balance_direction | 余额方向，枚举 FmsDebitCreditDirectionEnum（1 借、2 贷） |
| quantityUnit | String | quantity_unit | 数量核算计量单位 |
| quantityAccounting | Boolean | quantity_accounting | 是否启用数量核算 |
| cash | Boolean | cash | 是否现金科目（现金流量表取数依据） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| level | Integer | level | 科目层级 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| auxiliaryTypeIds | List\<Long\> | auxiliary_type_ids | 启用的辅助核算类别编号数组（JSON，varchar(10000)），关联 FmsAuxiliaryTypeDO.id |
| currencyIds | List\<Long\> | currency_ids | 核算币种编号数组（JSON，varchar(4000)），关联 FmsCurrencyDO.id |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 (account_set_id, code) 保证账套内科目编码唯一，按 (account_set_id, parent_id) 遍历科目树

#### FmsSubjectTemplateDO (fms_subject_template)

系统预置科目模板（与 fms_subject 同构，但无账套/租户维度），初始化账套时复制生成科目。标注 `@TenantIgnore`，全系统共享。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| code | String | code | 科目编码 |
| name | String | name | 科目名称 |
| parentId | Long | parent_id | 上级科目编号，关联 FmsSubjectTemplateDO.id（自引用），根节点为 0 |
| type | Integer | type | 科目类型，枚举 FmsSubjectTypeEnum |
| category | Integer | category | 科目类别 |
| balanceDirection | Integer | balance_direction | 余额方向，枚举 FmsDebitCreditDirectionEnum |
| quantityUnit | String | quantity_unit | 数量核算计量单位 |
| quantityAccounting | Boolean | quantity_accounting | 是否启用数量核算 |
| cash | Boolean | cash | 是否现金科目 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| level | Integer | level | 科目层级 |

**继承**: BaseDO（类上标注 `@TenantIgnore`）
**索引**: 仅主键索引

#### FmsAuxiliaryTypeDO (fms_auxiliary_type)

辅助核算类别（客户、供应商、职员、项目、部门、存货、自定义），账套内可扩展自定义类别。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| name | String | name | 辅助核算名称 |
| type | Integer | type | 类别类型，枚举 FmsAuxiliaryTypeEnum（1 客户、2 供应商、3 职员、4 项目、5 部门、6 存货、7 自定义） |
| systemPreset | Boolean | system_preset | 是否系统预置类别 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: `UNIQUE (account_set_id, name, deleted, tenant_id)` — 账套内类别名称唯一

#### FmsAuxiliaryItemDO (fms_auxiliary_item)

辅助核算项目（具体某个客户/供应商/存货等），存货类额外带规格与单位。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| code | String | code | 编码 |
| name | String | name | 名称 |
| auxiliaryTypeId | Long | auxiliary_type_id | 辅助核算类别编号，关联 FmsAuxiliaryTypeDO.id |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| remark | String | remark | 备注 |
| specification | String | specification | 规格（存货类） |
| unit | String | unit | 单位（存货类） |

**继承**: BaseDO
**索引**: `UNIQUE (account_set_id, auxiliary_type_id, code, deleted, tenant_id)` — 账套内同类别下编码唯一

#### FmsAuxiliaryCombinationDO (fms_assist_combination)

辅助核算组合：科目 + 一组辅助核算项目的组合，供分录与辅助余额表引用。注意表名为 `fms_assist_combination`（assist 拼写），与 DO 名 Auxiliary 不一致。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| subjectId | Long | subject_id | 科目编号，关联 FmsSubjectDO.id |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| items | List\<AuxiliaryItem\> | items | 辅助核算项目数组（JSON，varchar(10000)），内嵌字段：type（类别，枚举 FmsAuxiliaryTypeEnum）、typeId（类别编号）、itemId（项目编号，关联 FmsAuxiliaryItemDO.id）、name（项目名称快照） |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 (account_set_id, subject_id, items) 定位唯一组合

#### FmsInitialBalanceDO (fms_initial_balance)

科目期初余额（期初建账数据），启用辅助核算的科目按组合拆分到 assistBalances JSON。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| subjectId | Long | subject_id | 科目编号，关联 FmsSubjectDO.id |
| auxiliaryAccounting | Boolean | auxiliary_accounting | 是否启用辅助核算 |
| openingAmount | BigDecimal | opening_amount | 期初金额 |
| openingQuantity | BigDecimal | opening_quantity | 期初数量 |
| yearDebitAmount | BigDecimal | year_debit_amount | 本年累计借方金额 |
| yearDebitQuantity | BigDecimal | year_debit_quantity | 本年累计借方数量 |
| yearCreditAmount | BigDecimal | year_credit_amount | 本年累计贷方金额 |
| yearCreditQuantity | BigDecimal | year_credit_quantity | 本年累计贷方数量 |
| yearOpeningAmount | BigDecimal | year_opening_amount | 年初金额 |
| yearOpeningQuantity | BigDecimal | year_opening_quantity | 年初数量 |
| profitLossAmount | BigDecimal | profit_loss_amount | 实际损益发生额 |
| profitLossQuantity | BigDecimal | profit_loss_quantity | 实际损益发生数量 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| assistBalances | List\<AssistBalance\> | assist_balances | 辅助核算余额数组（JSON，varchar(10000)），内嵌字段：assistCombinationId（关联 fms_assist_combination.id）、auxiliaries（项目数组）、以及与主记录同构的 11 个金额/数量字段 |

**继承**: BaseDO
**索引**: `UNIQUE (account_set_id, subject_id, deleted, tenant_id)` — 账套内每科目一条期初余额

### 2.3 凭证聚合（voucher）

#### FmsVoucherDO (fms_voucher)

记账凭证主表，金额三要素（借方合计/贷方合计/总计）冗余自分录汇总，status 驱动凭证全生命周期。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| voucherWordId | Long | voucher_word_id | 凭证字编号，关联 FmsVoucherWordDO.id |
| voucherNumber | Integer | voucher_number | 凭证号（账套内按月连续编号） |
| voucherTime | LocalDateTime | voucher_time | 凭证日期 |
| attachmentUrls | List\<String\> | attachment_urls | 附件地址数组（JSON，varchar(10000)） |
| attachmentCount | Integer | attachment_count | 附单据张数 |
| debitAmount | BigDecimal | debit_amount | 借方金额合计 |
| creditAmount | BigDecimal | credit_amount | 贷方金额合计 |
| total | BigDecimal | total | 合计金额 |
| status | Integer | status | 状态，枚举 FmsVoucherStatusEnum（0 待审核、1 已审核、2 已驳回、3 审核中、4 已撤回、5 未提交、6 已创建、7 已删除、8 已作废） |
| reviewerUserId | Long | reviewer_user_id | 审核人，关联 system 模块 AdminUserDO.id |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: 仅主键索引；数据库含生成列 `voucher_period`（= YEAR(voucher_time)*100 + MONTH(voucher_time)，yyyyMM 格式），用于按会计期间检索，DO 层不映射该列

#### FmsVoucherEntryDO (fms_voucher_entry)

凭证分录（借贷明细），科目编码/名称为快照字段，科目后续改名不影响历史凭证。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| voucherId | Long | voucher_id | 凭证编号，关联 FmsVoucherDO.id |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| digest | String | digest | 摘要内容 |
| subjectId | Long | subject_id | 科目编号，关联 FmsSubjectDO.id |
| subjectCode | String | subject_code | 科目编码快照，冗余 FmsSubjectDO.code |
| subjectName | String | subject_name | 科目名称快照，冗余 FmsSubjectDO.name |
| sort | Integer | sort | 分录显示顺序 |
| quantity | BigDecimal | quantity | 数量，decimal(18,4) |
| unitPrice | BigDecimal | unit_price | 单价，decimal(18,6) |
| debitAmount | BigDecimal | debit_amount | 借方金额 |
| creditAmount | BigDecimal | credit_amount | 贷方金额 |
| assistCombinationId | Long | assist_combination_id | 辅助核算组合编号，关联 fms_assist_combination.id |
| auxiliaries | List\<AuxiliaryItem\> | auxiliaries | 辅助核算项目数组（JSON，varchar(10000)），内嵌字段：type（枚举 FmsAuxiliaryTypeEnum）、typeId、itemId（关联 FmsAuxiliaryItemDO.id）、name（名称快照） |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 (voucher_id, sort) 读取分录，按 (account_set_id, subject_id) 汇总账簿发生额

#### FmsVoucherTemplateDO (fms_voucher_template)

凭证模板：预置常用分录组合，制单时一键套用。分录结构以 JSON 存储。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| name | String | name | 凭证模板名称（NOT NULL） |
| categoryId | Long | category_id | 模板分类编号，关联 FmsVoucherTemplateCategoryDO.id |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| entries | List\<Entry\> | entries | 模板分录数组（JSON，text），Entry 内嵌字段：digest（摘要）、subjectId（科目，关联 FmsSubjectDO.id）、quantity（数量）、unitPrice（单价）、debitAmount（借方金额）、creditAmount（贷方金额）、auxiliaries（辅助核算项目数组，复用 FmsVoucherEntryDO.AuxiliaryItem 结构） |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsVoucherTemplateCategoryDO (fms_voucher_template_category)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| name | String | name | 凭证模板分类名称（NOT NULL） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: 仅主键索引

### 2.4 结账聚合（closing）

#### FmsClosingSchemeDO (fms_closing)

结账方案（注意：DO 名 Scheme，表名 `fms_closing`，二者不一致）。定义期末结转凭证的取数与生成规则，预置数据来自 `resources/fms/closing/closing-scheme-presets.json`。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| name | String | name | 结账名称 |
| type | Integer | type | 类型，枚举 FmsClosingTypeEnum（1 常规结账、2 结转损益、3 转出未交增值税、4 计提地税、5 计提所得税） |
| periodEnd | Boolean | period_end | 是否期末结转 |
| closingDay | Integer | closing_day | 结转损益日期（1-31，超过 31 默认最后一天） |
| subjectId | Long | subject_id | 来源科目编号，关联 FmsSubjectDO.id |
| formulaRule | Integer | formula_rule | 取数规则，枚举 FmsFormulaRuleEnum（0 余额、1 借方余额、2 贷方余额、3 科目借方余额、4 科目贷方余额、5 借方发生额、6 贷方发生额、7 损益发生额） |
| timeType | Integer | time_type | 取数时间类型，枚举 FmsClosingTimeTypeEnum（1 期末、2 期初、3 年初） |
| voucherWordId | Long | voucher_word_id | 生成的凭证字编号，关联 FmsVoucherWordDO.id |
| digest | String | digest | 凭证摘要 |
| voucherType | Integer | voucher_type | 结转凭证类型，枚举 FmsClosingVoucherTypeEnum（1 收益和损失分开结转、2 收益和损失同时结转） |
| priorYearAdjustmentSubjectId | Long | prior_year_adjustment_subject_id | "以前年度损益调整"科目，关联 FmsSubjectDO.id |
| adjustmentClosingSubjectId | Long | adjustment_closing_subject_id | "以前年度损益调整"科目的结转科目，关联 FmsSubjectDO.id |
| otherClosingSubjectId | Long | other_closing_subject_id | 其他损益科目的结转科目，关联 FmsSubjectDO.id |
| reverseBalance | Boolean | reverse_balance | 是否按余额反向结转 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| subjectRules | List\<SubjectRule\> | subject_rules | 结转科目规则数组（JSON，varchar(10000)），SubjectRule 内嵌字段：subjectId（关联 FmsSubjectDO.id）、subjectCode（编码快照）、digest（摘要）、direction（借贷方向，枚举 FmsDebitCreditDirectionEnum）、amountRatio（金额比例 0-100） |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsClosingTemplateDO (fms_closing_template)

结账模板：系统预置的结账方案蓝本（日常开支、采购销售、往来款、转账业务四类），初始化时按模板生成账套结账方案。预置数据来自 `resources/fms/closing/closing-template-presets.json`。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| presetCode | String | preset_code | 系统预置编码（如 profit-loss） |
| name | String | name | 模板名称 |
| category | Integer | category | 模板分类，枚举 FmsClosingTemplateCategoryEnum（1 日常开支、2 采购销售、3 往来款、4 转账业务） |
| periodEnd | Boolean | period_end | 是否期末结转 |
| subjectId | Long | subject_id | 来源科目编号，关联 FmsSubjectDO.id |
| formulaRule | Integer | formula_rule | 取数规则，枚举 FmsFormulaRuleEnum |
| timeType | Integer | time_type | 取数时间类型，枚举 FmsClosingTimeTypeEnum |
| sort | Integer | sort | 显示顺序 |
| subjectRules | List\<SubjectRule\> | subject_rules | 结转科目规则数组（JSON，varchar(10000)），结构同 FmsClosingSchemeDO.SubjectRule |

**继承**: BaseDO
**索引**: `UNIQUE INDEX uk_fms_closing_template_active (account_set_id, preset_code, unique_active, tenant_id)` — 其中 `unique_active` 为生成列（未删除时为 1，已删除为 NULL），实现"仅未删除记录内预置编码唯一"

#### FmsClosingVoucherDO (fms_closing_voucher)

结账生成的凭证记录：结账方案 × 会计期间 → 凭证 的执行结果。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| closingId | Long | closing_id | 结账方案编号，关联 fms_closing.id |
| voucherId | Long | voucher_id | 生成的凭证编号，关联 FmsVoucherDO.id |
| voucherTime | LocalDateTime | voucher_time | 凭证日期 |
| amount | BigDecimal | amount | 结转金额，decimal(24,6) |
| closed | Boolean | closed | 是否已结账（反结账后置 false） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 (account_set_id, closing_id, voucher_time) 定位某期间某方案的结账凭证

#### FmsClosingPeriodDO (fms_closing_period)

已结账期间记录，每结账一次生成一条，是"是否允许再修改该期间凭证"的判断依据。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| closingTime | LocalDateTime | closing_time | 结账时间 |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 account_set_id 判断最新已结账期间

### 2.5 报表聚合（report）

三大报表均为 **Config + Report 双表结构**：`*ConfigDO` 保存当前公式配置（可编辑），`*ReportDO` 按会计期间快照配置与计算结果（公式冗余存储，保证历史期间报表不受后续公式调整影响）。共享计算逻辑在 `FmsReportCommonService`（无独立 Controller），现金流量表公式经 Aviator 引擎求值。`FmsReportTemplateDO` 为系统级报表行模板（标注 `@TenantIgnore`）。

#### FmsReportTemplateDO (fms_report_template)

系统预置报表行模板，通过 type 区分报表，初始化时生成各账套的报表配置。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| type | Integer | type | 报表类型，枚举 FmsReportTypeEnum（1 资产负债表、2 利润表、3 现金流量表、4 现金流量辅助数据） |
| name | String | name | 配置名称（报表项目名） |
| rowNo | Integer | row_no | 行次 |
| rowId | Integer | row_id | 行编号（资产负债表资产行与负债行配对） |
| formula | String | formula | 公式（取数/计算表达式） |
| category | Integer | category | 现金流量表分类 |
| level | Integer | level | 层级 |
| editable | Boolean | editable | 是否可编辑 |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO（类上标注 `@TenantIgnore`）
**索引**: 仅主键索引

#### FmsBalanceSheetConfigDO (fms_balance_sheet_config)

资产负债表行配置（账套级当前生效公式）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| name | String | name | 配置名称（报表项目名） |
| rowNo | Integer | row_no | 行次 |
| rowId | Integer | row_id | 行编号（资产行与负债行配对） |
| formula | String | formula | 公式（text，科目/取数规则表达式） |
| level | Integer | level | 层级（缩进展示） |
| editable | Boolean | editable | 是否可编辑 |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 (account_set_id, sort) 读取报表行

#### FmsBalanceSheetReportDO (fms_balance_sheet_report)

资产负债表数据快照：配置行 + 期间 + 期初/期末金额。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| type | Integer | type | 报表期间类型，枚举 FmsReportPeriodTypeEnum（1 月度、2 季度） |
| fromPeriod | Integer | from_period | 开始会计期间（yyyyMM） |
| toPeriod | Integer | to_period | 结束会计期间（yyyyMM） |
| name / rowNo / rowId / formula / remark / editable / sort / level | 快照字段 | name, row_no, row_id, formula, remark, editable, sort, level | 依次冗余自 FmsBalanceSheetConfigDO 同名字段，保留历史期间的展示层级、行次、公式与行配对关系 |
| openingAmount | BigDecimal | opening_amount | 期初金额 |
| closingAmount | BigDecimal | closing_amount | 期末金额 |
| settled | Boolean | settled | 是否已结账期间的数据 |

**继承**: BaseDO
**索引**: 仅主键索引；业务上按 (account_set_id, from_period, to_period, type) 读取某期间报表

#### FmsIncomeStatementConfigDO (fms_income_statement_config)

利润表行配置（账套级当前生效公式），无 remark/rowId 字段，结构较资产负债表配置精简。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| name | String | name | 配置名称（报表项目名） |
| rowNo | Integer | row_no | 行次 |
| formula | String | formula | 公式（text） |
| level | Integer | level | 层级 |
| editable | Boolean | editable | 是否可编辑 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsIncomeStatementReportDO (fms_income_statement_report)

利润表数据快照：本期金额 + 本年累计金额。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| type | Integer | type | 报表期间类型，枚举 FmsReportPeriodTypeEnum（1 月度、2 季度） |
| fromPeriod | Integer | from_period | 开始会计期间（yyyyMM） |
| toPeriod | Integer | to_period | 结束会计期间（yyyyMM） |
| name / rowNo / formula / sort / editable / level | 快照字段 | name, row_no, formula, sort, editable, level | 依次冗余自 FmsIncomeStatementConfigDO 同名字段 |
| currentAmount | BigDecimal | current_amount | 本期金额 |
| yearAmount | BigDecimal | year_amount | 本年累计金额 |
| settled | Boolean | settled | 是否已结账期间的数据 |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsCashFlowStatementConfigDO (fms_cash_flow_statement_config)

现金流量表行配置。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| name | String | name | 配置名称（报表项目名） |
| rowNo | Integer | row_no | 行次 |
| formula | String | formula | 公式（text，经 Aviator 引擎求值） |
| category | Integer | category | 现金流量表分类（经营/投资/筹资活动等） |
| level | Integer | level | 层级 |
| editable | Boolean | editable | 是否可编辑 |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsCashFlowStatementReportDO (fms_cash_flow_statement_report)

现金流量表数据快照。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| type | Integer | type | 报表期间类型，枚举 FmsReportPeriodTypeEnum（1 月度、2 季度） |
| fromPeriod | Integer | from_period | 开始会计期间（yyyyMM） |
| toPeriod | Integer | to_period | 结束会计期间（yyyyMM） |
| name / rowNo / formula / remark / editable / sort / level | 快照字段 | name, row_no, formula, remark, editable, sort, level | 依次冗余自 FmsCashFlowStatementConfigDO 同名字段 |
| currentAmount | BigDecimal | current_amount | 本期金额 |
| yearAmount | BigDecimal | year_amount | 本年累计金额 |
| category | Integer | category | 现金流量表分类快照 |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsCashFlowExtendConfigDO (fms_cash_flow_extend_config)

现金流量表扩展配置（现金流量辅助数据，FmsReportTypeEnum.CASH_FLOW_ADJUSTMENT），type 区分用户配置行与固定公式行，含常驻金额列。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| name | String | name | 配置名称 |
| rowNo | Integer | row_no | 行次 |
| formula | String | formula | 公式（text） |
| category | Integer | category | 表格标识 |
| type | Integer | type | 公式类型，枚举 FmsCashFlowExtendTypeEnum（0 用户配置、1 固定公式） |
| currentAmount | BigDecimal | current_amount | 本期金额 |
| yearAmount | BigDecimal | year_amount | 本年累计金额 |
| editable | Boolean | editable | 是否可编辑 |
| sort | Integer | sort | 显示顺序 |
| level | Integer | level | 层级 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 仅主键索引

#### FmsCashFlowExtendDataDO (fms_cash_flow_extend_data)

现金流量表扩展数据快照（按期间保存扩展配置行与金额）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| type | Integer | type | 报表期间类型，枚举 FmsReportPeriodTypeEnum（1 月度、2 季度） |
| fromPeriod | Integer | from_period | 开始会计期间（yyyyMM） |
| toPeriod | Integer | to_period | 结束会计期间（yyyyMM） |
| name / rowNo / formula / remark / category / editable / sort / level | 快照字段 | name, row_no, formula, remark, category, editable, sort, level | 依次冗余自 FmsCashFlowExtendConfigDO 同名字段 |
| currentAmount | BigDecimal | current_amount | 本期金额 |
| yearAmount | BigDecimal | year_amount | 本年累计金额 |

**继承**: BaseDO
**索引**: 仅主键索引

### 2.6 首页指标（config）

#### FmsFinanceIndicatorDO (fms_finance_indicator)

首页财务指标卡：从资产负债表/利润表取数计算，预置数据来自 `resources/fms/config/finance-indicator-presets.json`。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（主键） |
| accountSetId | Long | account_set_id | 账套编号，关联 FmsAccountSetDO.id |
| name | String | name | 指标名称（varchar(100)，NOT NULL） |
| code | String | code | 指标编码（varchar(64)，NOT NULL） |
| type | Integer | type | 取数报表类型，枚举 FmsFinanceIndicatorTypeEnum（1 资产负债表、2 利润表） |
| formula | String | formula | 指标公式（varchar(2000)，支持报表行次公式或科目公式 JSON） |
| sort | Integer | sort | 展示顺序 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 仅主键索引

## 3. 实体关系

所有业务表通过 `account_set_id` 从属于账套；账套与后台用户通过 `fms_account_user` 授权关联（业务层权限隔离），账套内再叠加租户 SQL 改写（tenant_id）实现双重隔离。核心外键关系如下：

```text
system.AdminUserDO ──< fms_account_user >── fms_account_set（账套，隔离根）
                                 │              │ founder / level 控制权限
                                 │              ├── currency_id ──> fms_currency（本位币）
                                 │              ├── 1:1 ── fms_finance_parameter（财务参数）
                                 │              └──< fms_voucher_word / fms_digest
                                 │
    fms_subject（科目树，parent_id 自引用）
        │ ├── auxiliary_type_ids (JSON) ──> fms_auxiliary_type ──< fms_auxiliary_item
        │ ├── currency_ids (JSON) ──> fms_currency
        │ ├── 1:1 ── fms_initial_balance ── assist_balances(JSON) ──> fms_assist_combination
        │ └──< fms_assist_combination（科目 × 辅助项目组合，items JSON）
        │
    fms_voucher（凭证）──< fms_voucher_entry（分录）
        │        │            ├── subject_id ──> fms_subject
        │        │            └── assist_combination_id ──> fms_assist_combination
        │        ├── voucher_word_id ──> fms_voucher_word
        │        └── reviewer_user_id ──> system.AdminUserDO
        │
    fms_closing（结账方案，DO 名 FmsClosingSchemeDO）
        │ ├── subject_id / *_closing_subject_id ──> fms_subject
        │ ├── voucher_word_id ──> fms_voucher_word
        │ ├── subject_rules (JSON) ──> fms_subject
        │ └──< fms_closing_voucher >── fms_voucher（结账方案某期间生成凭证）
        │
    fms_closing_template（结账模板）──按账套初始化──> fms_closing
    fms_subject_template（科目模板，@TenantIgnore）──初始化复制──> fms_subject
    fms_report_template（报表行模板，@TenantIgnore）──初始化复制──> fms_*_config
        │
    报表双表结构（Config 当前公式 → Report 按期间快照公式 + 金额）
    fms_balance_sheet_config ──快照──> fms_balance_sheet_report
    fms_income_statement_config ──快照──> fms_income_statement_report
    fms_cash_flow_statement_config ──快照──> fms_cash_flow_statement_report
    fms_cash_flow_extend_config ──快照──> fms_cash_flow_extend_data
    fms_closing_period（已结账期间，控制报表 settled 与凭证可改性）
```

关系要点：

1. **一对多主从**：账套→科目/币种/凭证字/摘要/辅助核算；凭证→分录；结账方案→结账凭证；凭证模板分类→凭证模板。
2. **自引用树**：`fms_subject.parent_id`、`fms_subject_template.parent_id` 构成科目树（根节点 parent_id = 0）。
3. **快照冗余**：分录冗余科目编码/名称；报表 Report 表冗余 Config 表全部展示字段；结账规则冗余科目编码——目的都是历史数据不受主数据后续修改影响。
4. **JSON 内嵌关系**：辅助核算组合、期初余额辅助拆分、凭证分录辅助核算、结转科目规则均以 JSON 数组内嵌外键（typeId/itemId/subjectId），无物理外键，查询时在 Service 层组装。
5. **跨模块引用**：仅引用 `system_admin_user`（创建者/审核者/账套成员），fms 不被其他业务模块依赖。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|----|------|
| fms_account_set | FmsAccountSetDO | 账套（公司信息 + 会计制度 + 启用期间），数据隔离根实体 |
| fms_account_user | FmsAccountUserDO | 账套用户授权（用户 ↔ 账套多对多，含权限级别） |
| fms_subject | FmsSubjectDO | 会计科目（树形结构，支持数量核算与辅助核算） |
| fms_subject_template | FmsSubjectTemplateDO | 科目模板（系统预置，@TenantIgnore 全局共享） |
| fms_auxiliary_type | FmsAuxiliaryTypeDO | 辅助核算类别（客户/供应商/职员/项目/部门/存货/自定义） |
| fms_auxiliary_item | FmsAuxiliaryItemDO | 辅助核算项目（具体往来单位/职员/存货等档案） |
| fms_assist_combination | FmsAuxiliaryCombinationDO | 辅助核算组合（科目 × 辅助项目组合，注意表名 assist 拼写） |
| fms_currency | FmsCurrencyDO | 币别（账套内核算币种与汇率，含本位币标识） |
| fms_digest | FmsDigestDO | 常用摘要（凭证摘要快捷短语） |
| fms_voucher_word | FmsVoucherWordDO | 凭证字（记/收/付/转及打印标题） |
| fms_voucher_template | FmsVoucherTemplateDO | 凭证模板（预置分录组合，entries JSON） |
| fms_voucher_template_category | FmsVoucherTemplateCategoryDO | 凭证模板分类 |
| fms_finance_parameter | FmsFinanceParameterDO | 财务参数（科目层级/编码规则/赤字检查/结账校验，每账套一条） |
| fms_finance_indicator | FmsFinanceIndicatorDO | 首页财务指标（报表取数公式卡） |
| fms_initial_balance | FmsInitialBalanceDO | 科目期初余额（期初建账，含辅助核算余额 JSON 拆分） |
| fms_voucher | FmsVoucherDO | 凭证主表（含 DB 生成列 voucher_period 会计期间） |
| fms_voucher_entry | FmsVoucherEntryDO | 凭证分录（借贷明细 + 科目快照 + 辅助核算） |
| fms_closing | FmsClosingSchemeDO | 结账方案（期末结转凭证生成规则，表名与 DO 名不一致） |
| fms_closing_template | FmsClosingTemplateDO | 结账模板（系统预置方案蓝本，激活态唯一索引） |
| fms_closing_voucher | FmsClosingVoucherDO | 结账凭证（结账方案某期间生成的凭证记录） |
| fms_closing_period | FmsClosingPeriodDO | 结账期间（已结账期间记录，反结账依据） |
| fms_report_template | FmsReportTemplateDO | 报表行模板（系统预置，@TenantIgnore 全局共享） |
| fms_balance_sheet_config | FmsBalanceSheetConfigDO | 资产负债表行配置（当前生效公式） |
| fms_balance_sheet_report | FmsBalanceSheetReportDO | 资产负债表数据（按期间快照公式 + 期初/期末金额） |
| fms_income_statement_config | FmsIncomeStatementConfigDO | 利润表行配置（当前生效公式） |
| fms_income_statement_report | FmsIncomeStatementReportDO | 利润表数据（按期间快照公式 + 本期/本年累计金额） |
| fms_cash_flow_statement_config | FmsCashFlowStatementConfigDO | 现金流量表行配置（公式经 Aviator 求值） |
| fms_cash_flow_statement_report | FmsCashFlowStatementReportDO | 现金流量表数据（按期间快照公式 + 金额） |
| fms_cash_flow_extend_config | FmsCashFlowExtendConfigDO | 现金流量表扩展配置（辅助数据，用户配置/固定公式两类） |
| fms_cash_flow_extend_data | FmsCashFlowExtendDataDO | 现金流量表扩展数据（按期间快照） |
