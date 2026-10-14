# 账簿查询接口 (FmsLedgerController)

> 提供 FMS 财务账簿的查询与 Excel 导出能力，覆盖明细账、总账、科目余额表、多栏账、核算项目（辅助核算）明细账/余额表、数量金额明细账/总账八大账簿。

## 接口路径前缀

/fms/ledger  (Controller: FmsLedgerController)

所有接口均需登录，Service 层会先通过 `FmsAccountSetService#validateAccountSetReadPermission` 校验账套存在且当前用户为账套可读成员；数据范围由账套 + 会计期间决定。

## 公共请求参数

### FmsLedgerListReqVO（普通账簿查询）

明细账、总账、科目余额表、多栏账、数量金额明细账、数量金额总账共用。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| startMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 开始会计期间，格式 yyyy-MM |
| endMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 结束会计期间，格式 yyyy-MM |
| subjectId | Long | 否 | - | 科目编号（明细账/多栏账/数量金额明细账业务必传） |
| startSubjectId | Long | 否 | - | 起始科目编号（总账/余额表按科目编码区间过滤） |
| endSubjectId | Long | 否 | - | 结束科目编号（含其全部下级科目） |
| minLevel | Integer | 否 | @Min(1)、@Max(10) | 最小科目级次 |
| maxLevel | Integer | 否 | @Min(1)、@Max(10) | 最大科目级次 |

### FmsLedgerAuxiliaryListReqVO（核算项目账簿查询）

核算项目明细账、核算项目余额表共用。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| startMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 开始会计期间，格式 yyyy-MM |
| endMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 结束会计期间，格式 yyyy-MM |
| auxiliaryTypeId | Long | 是 | @NotNull | 辅助核算类别编号 |
| subjectId | Long | 否 | - | 科目编号（不传时统计全部科目） |
| auxiliaryItemId | Long | 否 | - | 辅助核算项目编号（明细账业务必传；余额表不传时统计全部项目） |

## 1. 明细账

### 1.1 获得明细账

- **路径**: GET /fms/ledger/detail/list
- **权限**: fms:ledger:detail:query
- **说明**: 按科目及期间查询明细账，输出期初余额、逐月凭证分录、本期合计、本年累计行。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」，其中 `subjectId` 业务必传（科目不存在时抛错）。

**响应**: CommonResult&lt;List&lt;FmsLedgerDetailRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| rowType | Integer | 行类型：1 期初余额、2 凭证分录、3 本期合计、4 本年累计、5 期末余额 |
| entryId | Long | 分录编号（仅凭证行） |
| entrySubjectId | Long | 分录所属科目编号（仅凭证行） |
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| period | String | 会计期间（yyyy-MM） |
| accountDate | LocalDate | 记账日期 |
| voucherId | Long | 凭证编号 |
| voucherNumber | String | 凭证字号（凭证字-凭证号） |
| digest | String | 摘要 |
| debitAmount | BigDecimal | 借方金额 |
| creditAmount | BigDecimal | 贷方金额 |
| balanceDirection | String | 余额方向（借/贷/平） |
| balance | BigDecimal | 余额 |
| debitQuantity | BigDecimal | 借方数量 |
| creditQuantity | BigDecimal | 贷方数量 |
| balanceQuantity | BigDecimal | 结存数量 |
| unitPrice | BigDecimal | 单价 |
| quantityUnit | String | 计量单位 |
| columnAmounts | Map&lt;Long, BigDecimal&gt; | 多栏账科目金额（仅多栏账使用） |

**业务逻辑**:
1. 构建账簿上下文：校验账套读权限；校验会计期间（开始期间不能晚于结束期间、不能早于账套启用期间）；加载财务参数、账套全部科目（构建父子层级）、科目初始余额，以及结束期间次月 1 日零点之前的全部凭证分录。
2. 校验 `subjectId` 对应科目存在，不存在时抛出「科目不存在」。
3. 汇总科目及其全部下级科目的凭证分录，计算期初余额 = 科目初始余额 + 开始期间之前的发生借贷净额，按科目余额方向确定正负号。
4. 逐月循环：凭证分录逐行生成凭证行并滚动累加余额，生成「本期合计」行（本期借贷发生额汇总）和「本年累计」行（年初至当月末发生额，账套启用年度叠加初始余额的年初累计）。
5. 按财务参数的余额展示模式（与科目方向一致 / 按实际借贷方向）填充每行的余额方向、余额和结存数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_101_000 | 科目不存在 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |
| 1_052_104_010 | 开始会计期间不能早于账套启用期间 |

### 1.2 获得指定期间有发生额的明细账科目

- **路径**: GET /fms/ledger/detail/subject-list
- **权限**: 已认证（无 @PreAuthorize，仅校验账套读权限）
- **说明**: 查询指定账套与会计期间内有凭证发生额的科目列表，并补齐父级科目，供明细账科目下拉使用。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」。

**响应**: CommonResult&lt;List&lt;FmsSubjectRespVO&gt;&gt;（本端点仅填充以下基础字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 科目编号 |
| parentId | Long | 上级科目编号 |
| code | String | 科目编码 |
| name | String | 科目名称 |
| type | Integer | 科目类型 |
| balanceDirection | Integer | 余额方向 |
| status | Integer | 状态 |
| level | Integer | 科目层级 |
| auxiliaryTypeIds | List&lt;Long&gt; | 辅助核算类别编号数组 |
| quantityAccounting | Boolean | 是否启用数量核算 |
| quantityUnit | String | 数量单位 |

**业务逻辑**:
1. 构建指定期间的账簿上下文（同 1.1）。
2. 收集开始期间月初至结束期间月末内有凭证发生额的科目编号。
3. 逐个向上补齐这些科目的全部父级科目编号，形成可见科目集合。
4. 过滤账套科目列表，仅返回可见科目并转换为响应 VO。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |
| 1_052_104_010 | 开始会计期间不能早于账套启用期间 |

### 1.3 导出明细账

- **路径**: GET /fms/ledger/detail/export-excel
- **权限**: fms:ledger:detail:export
- **说明**: 按 1.1 的计算结果导出 Excel（明细账.xls），导出记录含日志注解 @ApiAccessLog(EXPORT)。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」，`subjectId` 业务必传。

**响应**: 无 CommonResult，直接输出 Excel 文件流，列结构如下（FmsLedgerDetailExportRespVO）：

| 字段 | 类型 | 说明 |
|------|------|------|
| subject | String | 科目（科目编码 + 空格 + 科目名称） |
| accountDate | LocalDate | 日期 |
| voucherNumber | String | 凭证字号 |
| digest | String | 摘要 |
| debitAmount | BigDecimal | 借方 |
| creditAmount | BigDecimal | 贷方 |
| balanceDirection | String | 方向 |
| balance | BigDecimal | 余额 |

**业务逻辑**:
1. 调用明细账查询逻辑获得明细账行列表。
2. 转换为导出 VO，并将科目编码与科目名称拼接为「科目」列。
3. 通过 ExcelUtils 输出「明细账.xls」。

**错误码**: 同 1.1。

## 2. 总账

### 2.1 获得总账

- **路径**: GET /fms/ledger/general/list
- **权限**: fms:ledger:general:query
- **说明**: 按科目范围与级次查询总账（月汇总视角，不含凭证分录行）。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」；`startSubjectId`/`endSubjectId`/`minLevel`/`maxLevel` 用于筛选科目范围。

**响应**: CommonResult&lt;List&lt;FmsLedgerGeneralRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| rowType | Integer | 行类型：1 期初余额、3 本期合计、4 本年累计 |
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| period | String | 会计期间（yyyy-MM） |
| digest | String | 摘要（期初余额/本期合计/本年累计） |
| debitAmount | BigDecimal | 借方金额 |
| creditAmount | BigDecimal | 贷方金额 |
| balanceDirection | String | 余额方向 |
| balance | BigDecimal | 余额 |

**业务逻辑**:
1. 构建账簿上下文（同 1.1）。
2. 按科目范围筛选科目：起始/结束科目编码区间（结束科目含其全部下级）、最小/最大科目级次。
3. 对每个科目复用明细账行计算逻辑，但不生成凭证分录行。
4. 过滤掉没有凭证行且借/贷/余额八项金额全为零的科目。
5. 转换为总账响应 VO 返回。

**错误码**: 同 1.1（起始/结束科目不存在时抛 1_052_101_000）。

### 2.2 导出总账

- **路径**: GET /fms/ledger/general/export-excel
- **权限**: fms:ledger:general:export
- **说明**: 按 2.1 的计算结果导出「总账.xls」，列为科目编码/科目名称/期间/摘要/借方/贷方/方向/余额。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」。

**响应**: 无 CommonResult，直接输出 Excel 文件流（FmsLedgerGeneralRespVO 标注的 Excel 列）。

**业务逻辑**:
1. 调用总账查询逻辑获得总账行列表。
2. 直接以 FmsLedgerGeneralRespVO 的 Excel 注解列写出「总账.xls」。

**错误码**: 同 2.1。

## 3. 科目余额表

### 3.1 获得科目余额表

- **路径**: GET /fms/ledger/subject-balance/list
- **权限**: fms:ledger:subject-balance:query
- **说明**: 输出科目余额树，每个科目节点含期初、本期发生、本年累计、期末四组借贷金额（及数量/单价），非零辅助核算组合余额作为子节点挂载。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」。

**响应**: CommonResult&lt;List&lt;FmsLedgerSubjectBalanceRespVO&gt;&gt;（树形，children 递归同结构）

| 字段 | 类型 | 说明 |
|------|------|------|
| nodeKey | String | 节点唯一键（科目 S:{id}、辅助组合 A:{id}） |
| nodeType | Integer | 节点类型：1 科目、2 辅助核算组合 |
| subjectId | Long | 科目编号 |
| assistCombinationId | Long | 辅助核算组合编号（仅组合节点） |
| subjectCode | String | 科目编码（组合节点为 科目编码_项目编码后缀） |
| subjectName | String | 科目名称（组合节点为 科目名称_项目名称后缀） |
| level | Integer | 科目级次（组合节点为科目级次 + 1） |
| quantityAccounting | Boolean | 是否启用数量核算 |
| quantityUnit | String | 计量单位 |
| openingDebitAmount | BigDecimal | 期初借方余额 |
| openingCreditAmount | BigDecimal | 期初贷方余额 |
| openingBalanceDirection | String | 期初余额方向 |
| openingQuantity | BigDecimal | 期初数量 |
| openingUnitPrice | BigDecimal | 期初单价 |
| periodDebitAmount | BigDecimal | 本期借方发生额 |
| periodCreditAmount | BigDecimal | 本期贷方发生额 |
| periodDebitQuantity | BigDecimal | 本期借方数量 |
| periodCreditQuantity | BigDecimal | 本期贷方数量 |
| yearDebitAmount | BigDecimal | 本年累计借方发生额 |
| yearCreditAmount | BigDecimal | 本年累计贷方发生额 |
| yearDebitQuantity | BigDecimal | 本年累计借方数量 |
| yearCreditQuantity | BigDecimal | 本年累计贷方数量 |
| endingDebitAmount | BigDecimal | 期末借方余额 |
| endingCreditAmount | BigDecimal | 期末贷方余额 |
| endingBalanceDirection | String | 期末余额方向 |
| endingQuantity | BigDecimal | 期末数量 |
| endingUnitPrice | BigDecimal | 期末单价 |
| children | List | 下级节点 |

**业务逻辑**:
1. 构建账簿上下文（同 1.1）。
2. 加载账套全部辅助核算项目，从初始余额的辅助核算余额（AssistBalance）与凭证分录中收集实际使用的辅助核算组合，逐组合计算期初/本期/本年/期末八项金额，得到「科目 → 组合余额」映射。
3. 按科目范围筛选科目，逐科目汇总其子树的期初余额、本期发生额、本年累计（启用年度叠加初始余额年初数）与期末余额，过滤八项金额全零且无辅助组合余额的科目。
4. 按科目父子关系组装余额树。
5. 将非零辅助核算组合余额节点追加到对应科目的 children 中。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_101_000 | 科目不存在 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |
| 1_052_104_010 | 开始会计期间不能早于账套启用期间 |

### 3.2 导出科目余额表

- **路径**: GET /fms/ledger/subject-balance/export-excel
- **权限**: fms:ledger:subject-balance:export
- **说明**: 按 3.1 的结果导出「科目余额表.xls」，导出前将余额树递归平铺为一维列表。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」。

**响应**: 无 CommonResult，直接输出 Excel 文件流，列结构为 FmsLedgerSubjectBalanceRespVO 的 Excel 列（科目编码、科目名称、期初借方/贷方、本期借方/贷方、本年累计借方/贷方、期末借方/贷方）。

**业务逻辑**:
1. 调用科目余额表查询逻辑获得余额树。
2. 递归平铺树节点（父节点在前、子节点紧随）。
3. 输出「科目余额表.xls」。

**错误码**: 同 3.1。

## 4. 多栏账

### 4.1 获得多栏账

- **路径**: GET /fms/ledger/multi-column/list
- **权限**: fms:ledger:multi-column:query
- **说明**: 以指定科目为查询主体，将其下级有业务的科目展开为动态金额列。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」，`subjectId` 业务必传。

**响应**: CommonResult&lt;FmsLedgerMultiColumnRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| columns | List&lt;Column&gt; | 动态科目列 |
| columns[].subjectId | Long | 科目编号 |
| columns[].subjectCode | String | 科目编码 |
| columns[].subjectName | String | 科目名称 |
| columns[].balanceDirection | Integer | 余额方向 |
| rows | List&lt;FmsLedgerDetailRespVO&gt; | 账簿行，结构与 1.1 一致，其中 columnAmounts 为各动态列（key=科目编号）的金额；每期「本年累计」行后附带一行「期末余额」行（rowType=5） |

**业务逻辑**:
1. 构建账簿上下文并校验科目存在。
2. 收集科目子树内「有凭证发生额，或有非零初始余额（期初/年初借、贷）」的下级科目，作为动态科目列。
3. 复用明细账行计算逻辑（含凭证分录行），并在每期「本年累计」行后追加「期末余额」行。
4. 逐行计算各动态列金额：凭证行取分录对应列的按科目方向的名义金额，期初/期末/汇总行按列科目汇总对应时间范围的发生净额。
5. 组装 columns + rows 返回。

**错误码**: 同 1.1。

### 4.2 导出多栏账

- **路径**: GET /fms/ledger/multi-column/export-excel
- **权限**: fms:ledger:multi-column:export
- **说明**: 按 4.1 的结果导出「多栏账.xls」，表头按动态科目列动态生成。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」，`subjectId` 业务必传。

**响应**: 无 CommonResult，直接输出 Excel 文件流。

**业务逻辑**:
1. 调用多栏账查询逻辑获得动态列与账簿行。
2. 由动态列构建多级 Excel 表头（FmsLedgerMultiColumnExcelHelper.buildHead）。
3. 将各行金额按动态列展开为数据行并输出「多栏账.xls」。

**错误码**: 同 4.1。

## 5. 核算项目明细账

### 5.1 获得核算项目明细账

- **路径**: GET /fms/ledger/auxiliary-detail/list
- **权限**: fms:ledger:detail:query
- **说明**: 按辅助核算类别 + 项目查询核算项目明细账，输出期初余额、逐月凭证分录、本期合计、本年累计行。

**请求参数 (FmsLedgerAuxiliaryListReqVO)**: 复用「公共请求参数 - FmsLedgerAuxiliaryListReqVO」，`auxiliaryItemId` 业务必传。

**响应**: CommonResult&lt;List&lt;FmsLedgerAuxiliaryDetailRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| rowType | Integer | 行类型：1 期初余额、2 凭证分录、3 本期合计、4 本年累计 |
| entryId | Long | 分录编号（仅凭证行） |
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| period | String | 会计期间（yyyy-MM） |
| accountDate | LocalDate | 记账日期 |
| voucherId | Long | 凭证编号 |
| voucherNumber | String | 凭证字号 |
| digest | String | 摘要 |
| debitAmount | BigDecimal | 借方金额 |
| creditAmount | BigDecimal | 贷方金额 |
| balanceDirection | String | 余额方向 |
| balance | BigDecimal | 余额 |

**业务逻辑**:
1. 构建辅助核算账簿上下文：校验账套读权限与会计期间；加载财务参数、指定辅助核算类别下的全部项目、账套科目；指定 `subjectId` 时校验存在并限定科目子树范围。
2. 校验 `auxiliaryItemId` 对应的辅助核算项目存在，不存在时抛错。
3. 筛选科目范围内、辅助核算中包含该类别的该项目的凭证分录。
4. 计算期初余额：从初始余额的辅助核算余额中取出包含该项目的记录，按科目余额方向加总。
5. 逐月生成凭证分录行（滚动累加余额）、「本期合计」行与「本年累计」行（启用年度叠加初始余额年初数），按余额展示模式填充余额方向与余额。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_101_000 | 科目不存在 |
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |
| 1_052_104_010 | 开始会计期间不能早于账套启用期间 |

### 5.2 导出核算项目明细账

- **路径**: GET /fms/ledger/auxiliary-detail/export-excel
- **权限**: fms:ledger:detail:export
- **说明**: 按 5.1 的结果导出「核算项目明细账.xls」，列为日期/凭证字号/摘要/借方/贷方/方向/余额。

**请求参数 (FmsLedgerAuxiliaryListReqVO)**: 复用「公共请求参数 - FmsLedgerAuxiliaryListReqVO」，`auxiliaryItemId` 业务必传。

**响应**: 无 CommonResult，直接输出 Excel 文件流（FmsLedgerAuxiliaryDetailRespVO 的 Excel 列）。

**业务逻辑**:
1. 调用核算项目明细账查询逻辑获得行列表。
2. 直接以 FmsLedgerAuxiliaryDetailRespVO 的 Excel 注解列写出「核算项目明细账.xls」。

**错误码**: 同 5.1。

## 6. 核算项目余额表

### 6.1 获得核算项目余额表

- **路径**: GET /fms/ledger/auxiliary-balance/list
- **权限**: fms:ledger:subject-balance:query
- **说明**: 按辅助核算类别查询各项目的期初/本期/本年累计/期末借贷余额，自动过滤无业务的项目。

**请求参数 (FmsLedgerAuxiliaryListReqVO)**: 复用「公共请求参数 - FmsLedgerAuxiliaryListReqVO」；`auxiliaryItemId` 可选，指定时仅返回该项目。

**响应**: CommonResult&lt;List&lt;FmsLedgerAuxiliaryBalanceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| auxiliaryItemId | Long | 辅助核算项目编号 |
| code | String | 项目编码 |
| name | String | 项目名称 |
| openingDebitAmount | BigDecimal | 期初借方余额 |
| openingCreditAmount | BigDecimal | 期初贷方余额 |
| periodDebitAmount | BigDecimal | 本期借方发生额 |
| periodCreditAmount | BigDecimal | 本期贷方发生额 |
| yearDebitAmount | BigDecimal | 本年累计借方发生额 |
| yearCreditAmount | BigDecimal | 本年累计贷方发生额 |
| endingDebitAmount | BigDecimal | 期末借方余额 |
| endingCreditAmount | BigDecimal | 期末贷方余额 |

**业务逻辑**:
1. 构建辅助核算账簿上下文（同 5.1，`auxiliaryItemId` 可不传）。
2. 指定 `auxiliaryItemId` 时校验该项目存在。
3. 对类别下每个辅助核算项目：汇总其科目范围内的凭证分录与初始余额记录，计算期初、期末借贷净额及本期、本年累计发生额。
4. 过滤：指定项目时仅保留该项目；且项目必须存在分录或初始余额记录。
5. 最终过滤八项金额全零的项目后返回。

**错误码**: 同 5.1。

### 6.2 导出核算项目余额表

- **路径**: GET /fms/ledger/auxiliary-balance/export-excel
- **权限**: fms:ledger:subject-balance:export
- **说明**: 按 6.1 的结果导出「核算项目余额表.xls」，列为编码/项目名称/期初借方、贷方/本期借方、贷方/本年累计借方、贷方/期末借方、贷方。

**请求参数 (FmsLedgerAuxiliaryListReqVO)**: 复用「公共请求参数 - FmsLedgerAuxiliaryListReqVO」。

**响应**: 无 CommonResult，直接输出 Excel 文件流（FmsLedgerAuxiliaryBalanceRespVO 的 Excel 列）。

**业务逻辑**:
1. 调用核算项目余额表查询逻辑获得余额列表。
2. 直接以 FmsLedgerAuxiliaryBalanceRespVO 的 Excel 注解列写出「核算项目余额表.xls」。

**错误码**: 同 6.1。

## 7. 数量金额明细账

### 7.1 获得数量金额明细账

- **路径**: GET /fms/ledger/quantity-detail/list
- **权限**: fms:ledger:detail:query
- **说明**: 在明细账基础上叠加数量与单价维度，仅汇总子树内启用数量核算的科目。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」，`subjectId` 业务必传。

**响应**: CommonResult&lt;List&lt;FmsLedgerQuantityDetailRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| rowType | Integer | 行类型：1 期初余额、2 凭证分录、3 本期合计、4 本年累计 |
| entryId | Long | 分录编号（仅凭证行） |
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| period | String | 会计期间 |
| accountDate | LocalDate | 记账日期 |
| voucherId | Long | 凭证编号 |
| voucherNumber | String | 凭证字号 |
| digest | String | 摘要 |
| debitAmount | BigDecimal | 借方金额 |
| creditAmount | BigDecimal | 贷方金额 |
| balanceDirection | String | 余额方向 |
| balance | BigDecimal | 结存金额 |
| debitQuantity | BigDecimal | 借方数量 |
| creditQuantity | BigDecimal | 贷方数量 |
| balanceQuantity | BigDecimal | 结存数量 |
| unitPrice | BigDecimal | 分录单价（仅凭证行） |
| openingUnitPrice | BigDecimal | 期初单价 |
| periodUnitPrice | BigDecimal | 本期单价 |
| yearUnitPrice | BigDecimal | 累计单价 |
| endingUnitPrice | BigDecimal | 期末单价 |
| quantityUnit | String | 计量单位 |

**业务逻辑**:
1. 构建账簿上下文并校验科目存在。
2. 收集科目子树中启用数量核算的科目编号，数量仅汇总这些科目的分录。
3. 复用明细账行计算逻辑（含凭证分录行，限定数量科目集合），得到含借贷数量与结存数量的账簿行。
4. 按行类型补充单价：期初行算期初单价、本期合计行算本期单价、本年累计行算累计单价、凭证行取分录单价。
5. 统一按「结存金额 / 结存数量」（6 位小数四舍五入）计算期末单价。

**错误码**: 同 1.1。

### 7.2 导出数量金额明细账

- **路径**: GET /fms/ledger/quantity-detail/export-excel
- **权限**: fms:ledger:detail:export
- **说明**: 按 7.1 的结果导出「数量金额明细账.xls」，含金额、数量、各阶段单价与单位列。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」，`subjectId` 业务必传。

**响应**: 无 CommonResult，直接输出 Excel 文件流（FmsLedgerQuantityDetailRespVO 的 Excel 列）。

**业务逻辑**:
1. 调用数量金额明细账查询逻辑获得行列表。
2. 直接以 FmsLedgerQuantityDetailRespVO 的 Excel 注解列写出「数量金额明细账.xls」。

**错误码**: 同 7.1。

## 8. 数量金额总账

### 8.1 获得数量金额总账

- **路径**: GET /fms/ledger/quantity-general/list
- **权限**: fms:ledger:general:query
- **说明**: 输出数量金额总账科目树，仅保留启用数量核算且有数量业务的节点及其父级汇总节点。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」。

**响应**: CommonResult&lt;List&lt;FmsLedgerQuantityGeneralRespVO&gt;&gt;（树形，children 递归同结构）

| 字段 | 类型 | 说明 |
|------|------|------|
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| level | Integer | 科目级次 |
| quantityAccounting | Boolean | 是否启用数量核算 |
| quantityUnit | String | 计量单位 |
| openingBalanceDirection | String | 期初余额方向 |
| openingQuantity | BigDecimal | 期初数量 |
| openingUnitPrice | BigDecimal | 期初单价 |
| openingDebitAmount | BigDecimal | 期初借方余额 |
| openingCreditAmount | BigDecimal | 期初贷方余额 |
| openingAmount | BigDecimal | 期初金额（取借贷余额中非零一侧） |
| periodDebitQuantity | BigDecimal | 本期借方数量 |
| periodDebitAmount | BigDecimal | 本期借方发生额 |
| periodCreditQuantity | BigDecimal | 本期贷方数量 |
| periodCreditAmount | BigDecimal | 本期贷方发生额 |
| yearDebitQuantity | BigDecimal | 本年累计借方数量 |
| yearDebitAmount | BigDecimal | 本年累计借方发生额 |
| yearCreditQuantity | BigDecimal | 本年累计贷方数量 |
| yearCreditAmount | BigDecimal | 本年累计贷方发生额 |
| endingBalanceDirection | String | 期末余额方向 |
| endingQuantity | BigDecimal | 期末数量 |
| endingUnitPrice | BigDecimal | 期末单价 |
| endingDebitAmount | BigDecimal | 期末借方余额 |
| endingCreditAmount | BigDecimal | 期末贷方余额 |
| endingAmount | BigDecimal | 期末金额（取借贷余额中非零一侧） |
| children | List | 下级科目 |

**业务逻辑**:
1. 构建账簿上下文（同 1.1）。
2. 按科目范围筛选科目并逐科目计算余额；财务参数为「与科目方向一致」模式时，期初/期末借、贷金额按科目余额方向填充。
3. 裁剪余额树：自底向上移除无子节点且期初/本期金额数量全为零的节点，仅保留数量核算业务节点及其父级汇总节点。
4. 将科目余额树转换为数量金额总账树，期初/期末金额取借贷余额中的非零一侧。

**错误码**: 同 3.1。

### 8.2 导出数量金额总账

- **路径**: GET /fms/ledger/quantity-general/export-excel
- **权限**: fms:ledger:general:export
- **说明**: 按 8.1 的结果导出「数量金额总账.xls」，导出前将树平铺（保留数量核算节点及其子树）。

**请求参数 (FmsLedgerListReqVO)**: 复用「公共请求参数 - FmsLedgerListReqVO」。

**响应**: 无 CommonResult，直接输出 Excel 文件流，列结构为 FmsLedgerQuantityGeneralRespVO 的多级 Excel 列（科目/基础信息/期初余额/本期借方/本期贷方/本年累计借方/本年累计贷方/期末余额）。

**业务逻辑**:
1. 调用数量金额总账查询逻辑获得科目树。
2. 递归平铺：启用数量核算的节点或存在子节点的节点保留，子节点紧随其后。
3. 输出「数量金额总账.xls」。

**错误码**: 同 8.1。
