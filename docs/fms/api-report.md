# 财务报表接口 (FmsBalanceSheetController / FmsIncomeStatementController / FmsCashFlowStatementController)

> 提供 FMS 财务三大报表：资产负债表、利润表和现金流量表的查询、导出、公式维护与勾稽检查，报表配置首次查询时按模板初始化，并按会计期间生成报表快照。

## 接口路径前缀

- /fms/report/balance-sheet  (Controller: FmsBalanceSheetController)
- /fms/report/income-statement  (Controller: FmsIncomeStatementController)
- /fms/report/cash-flow-statement  (Controller: FmsCashFlowStatementController)

## 通用请求参数

三大报表查询接口共用 **FmsReportListReqVO**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| startMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 开始会计期间，格式如 `2026-08` |
| endMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 结束会计期间 |

三大报表公式维护接口共用 **FmsReportFormulaUpdateReqVO**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 报表项目（配置）编号 |
| formulas | List&lt;Formula&gt; | 是 | @NotNull、@Valid（嵌套校验） | 公式项数组 |

Formula 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| subjectId | Long | 是 | @NotNull | 科目编号 |
| operator | String | 是 | @NotNull、@Pattern(`[+-]`) | 运算符，`+` 或 `-` |
| rules | Integer | 是 | @NotNull、@InEnum(FmsFormulaRuleEnum) | 取数规则 |

## 通用响应结构（FmsReportItemRespVO）

利润表、现金流量表项目共用 FmsReportItemRespVO：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 配置编号 |
| name | String | 项目名称 |
| rowNo | Integer | 行次 |
| level | Integer | 层级 |
| editable | Boolean | 是否可编辑 |
| formula | String | 公式（科目公式为含取数结果的 JSON，行次公式为 `["L1-L2"]` 形式） |
| openingAmount | BigDecimal | 期初金额 |
| closingAmount | BigDecimal | 期末金额 |
| yearAmount | BigDecimal | 本年累计金额 |
| currentAmount | BigDecimal | 本期金额 |

## 1. 资产负债表（FmsBalanceSheetController）

### 1.1 获得资产负债表

- **路径**: GET /fms/report/balance-sheet/get
- **权限**: fms:report:balance-sheet:query
- **说明**: 获得指定账套和会计期间的资产负债表，资产侧与负债侧项目按行编号配对返回。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;List&lt;FmsBalanceSheetRowRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| rowId | Integer | 行编号 |
| assetId | Long | 资产项目配置编号 |
| assetName | String | 资产项目名称 |
| assetRowNo | Integer | 资产项目行次 |
| assetClosingAmount | BigDecimal | 资产项目期末余额 |
| assetOpeningAmount | BigDecimal | 资产项目年初余额 |
| assetLevel | Integer | 资产项目层级 |
| assetEditable | Boolean | 资产项目是否可编辑 |
| assetFormula | String | 资产项目公式 |
| liabilityId | Long | 负债和所有者权益项目配置编号 |
| liabilityName | String | 负债和所有者权益项目名称 |
| liabilityRowNo | Integer | 负债和所有者权益项目行次 |
| liabilityClosingAmount | BigDecimal | 负债和所有者权益项目期末余额 |
| liabilityOpeningAmount | BigDecimal | 负债和所有者权益项目年初余额 |
| liabilityLevel | Integer | 负债和所有者权益项目层级 |
| liabilityEditable | Boolean | 负债和所有者权益项目是否可编辑 |
| liabilityFormula | String | 负债和所有者权益项目公式 |

**业务逻辑**:
1. 校验当前用户对账套的读权限。
2. 加载账套下全部科目；首次查询时按资产负债表模板初始化报表配置（模板公式中的科目编码绑定为本账套科目编号，编码不存在的科目编号置空），并按查询期间创建报表快照（金额初始化为零、未结账），均通过锁定账套避免并发重复初始化。
3. 查询年初（账套启用年度或结账年度年初）至期末的科目余额，由报表共用服务从损益类科目及其父级余额中扣除结转损益凭证的发生额。
4. 逐行计算报表项目：行次公式（`L行次` 表达式）直接引用已计算的行次金额；科目公式按取数规则（余额、借方余额、贷方余额、科目借方余额、科目贷方余额）逐项取数，按运算符累加到期初、期末金额，并将取数结果回写公式供前端公式编辑弹窗展示。
5. 按行编号将资产侧与负债侧项目配对成行返回（正文行次不超过资产总计行次 30 的为资产侧，其余为负债和所有者权益侧）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |

### 1.2 导出资产负债表

- **路径**: GET /fms/report/balance-sheet/export-excel
- **权限**: fms:report:balance-sheet:export
- **说明**: 按查询条件计算资产负债表并导出为 Excel 文件（`资产负债表.xls`），导出逻辑与 1.1 相同，无响应 Body（Excel 流）。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: Excel 文件流，列包括资产、行次、期末余额、年初余额、负债和所有者权益、行次、期末余额、年初余额

**业务逻辑**:
1. 调用与 1.1 相同的查询逻辑获得报表行数据。
2. 使用 ExcelUtils 按 FmsBalanceSheetRowRespVO 上的 `@ExcelProperty` 注解写出 Excel 文件。

**错误码**: 同 1.1

### 1.3 更新资产负债表公式

- **路径**: PUT /fms/report/balance-sheet/update
- **权限**: fms:report:balance-sheet:update
- **说明**: 更新指定资产负债表项目的取数公式。

**请求参数**: FmsReportFormulaUpdateReqVO（见通用请求参数，取数规则范围：余额类规则）

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验当前用户对账套的写权限。
2. 查询报表快照项目，校验其存在、属于该账套且允许编辑公式（不可编辑时抛出对应错误码）。
3. 按项目名称、行次、层级、显示顺序匹配同账套的基础配置，匹配不到时抛出 `REPORT_CONFIG_NOT_EXISTS`。
4. 校验并构造公式：科目不能重复、运算符必须是 `+`/`-`、取数规则必须在资产负债表允许范围内（余额、借方余额、贷方余额、科目借方余额、科目贷方余额）、科目必须存在。
5. 将公式 JSON 同时更新到当前期间报表快照和基础配置（后续期间使用新配置）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_101_000 | 科目不存在 |
| 1_052_106_000 | 报表项目不存在 |
| 1_052_106_001 | 该报表项目不允许编辑公式 |
| 1_052_106_002 | 报表公式科目不能重复 |
| 1_052_106_003 | 报表公式取数规则不正确 |
| 1_052_106_004 | 报表公式运算符不正确 |

### 1.4 检查资产负债表

- **路径**: GET /fms/report/balance-sheet/check
- **权限**: fms:report:balance-sheet:query
- **说明**: 检查资产负债表平衡、初始余额、损益结转状态，并列出未纳入报表公式的科目。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;FmsBalanceSheetCheckRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| balanced | Boolean | 报表是否平衡（年初与期末差额均为零） |
| initialBalanceBalanced | Boolean | 初始余额是否平衡（试算平衡结果） |
| profitLossTransferred | Boolean | 查询期间内各月损益是否均已结转 |
| openingDifferenceAmount | BigDecimal | 年初余额差额（资产总计 - 负债和所有者权益总计） |
| closingDifferenceAmount | BigDecimal | 期末余额差额 |
| unmappedSubjects | List&lt;UnmappedSubject&gt; | 未纳入报表公式的科目 |

UnmappedSubject 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 科目编号 |
| code | String | 科目编码 |
| name | String | 科目名称 |

**业务逻辑**:
1. 计算资产负债表，取资产总计（行次 30）与负债和所有者权益总计（行次 53）的年初、期末金额，计算两侧差额并判断是否平衡。
2. 查询初始余额试算平衡结果。
3. 从开始期间逐月检查到结束期间，当月损益余额不为零时说明损益尚未结转。
4. 收集报表各行公式引用的科目编号，检查存在期初或期末余额但未纳入公式的一级非损益类科目（沿公式科目父级链向上匹配；资本化支出科目，按财务参数编码规则转换后的 `4404` 除外），作为待补充公式的科目返回。

**错误码**: 同 1.1

## 2. 利润表（FmsIncomeStatementController）

### 2.1 获得利润表

- **路径**: GET /fms/report/income-statement/get
- **权限**: fms:report:income-statement:query
- **说明**: 获得指定账套和会计期间的利润表项目列表。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;List&lt;FmsReportItemRespVO&gt;&gt;（见通用响应结构，本表使用本期金额 currentAmount 和本年累计金额 yearAmount）

**业务逻辑**:
1. 校验当前用户对账套的读权限。
2. 加载账套科目；首次查询时按利润表模板初始化报表配置（科目编码绑定本账套科目），并按查询期间创建报表快照（金额初始化为零、未结账），锁定账套避免并发重复初始化。
3. 查询本期至期末的科目余额，由报表共用服务扣除结转损益凭证发生额。
4. 逐行计算报表项目：行次公式直接引用已计算的行次金额；科目公式按发生额取数规则（借方发生额、贷方发生额、损益发生额）取数，`+` 运算时借贷方向互相抵销后累加，并将取数结果回写公式。
5. 返回报表项目列表（表头行行次为空或 0，不参与行次引用）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |

### 2.2 导出利润表

- **路径**: GET /fms/report/income-statement/export-excel
- **权限**: fms:report:income-statement:export
- **说明**: 按查询条件计算利润表并导出为 Excel 文件（`利润表.xls`），导出逻辑与 2.1 相同，无响应 Body（Excel 流）。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: Excel 文件流，列包括项目、行次、本期金额、本年累计金额

**业务逻辑**:
1. 调用与 2.1 相同的查询逻辑获得报表项目数据。
2. 使用 ExcelUtils 按 FmsReportItemRespVO 上的 `@ExcelProperty` 注解写出 Excel 文件。

**错误码**: 同 2.1

### 2.3 更新利润表公式

- **路径**: PUT /fms/report/income-statement/update
- **权限**: fms:report:income-statement:update
- **说明**: 更新指定利润表项目的取数公式。

**请求参数**: FmsReportFormulaUpdateReqVO（见通用请求参数，取数规则范围：发生额类规则）

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验当前用户对账套的写权限。
2. 查询报表快照项目，校验其存在、属于该账套且允许编辑公式。
3. 校验并构造公式：科目不能重复、运算符必须是 `+`/`-`、取数规则必须在利润表允许范围内（借方发生额、贷方发生额、损益发生额）、科目必须存在。
4. 只更新当前期间报表快照的公式，后续期间仍使用基础配置。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_101_000 | 科目不存在 |
| 1_052_106_000 | 报表项目不存在 |
| 1_052_106_001 | 该报表项目不允许编辑公式 |
| 1_052_106_002 | 报表公式科目不能重复 |
| 1_052_106_003 | 报表公式取数规则不正确 |
| 1_052_106_004 | 报表公式运算符不正确 |

### 2.4 检查利润表

- **路径**: GET /fms/report/income-statement/check
- **权限**: fms:report:income-statement:query
- **说明**: 检查利润表与资产负债表的勾稽关系，并列出未纳入利润表公式的损益科目。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;FmsIncomeStatementCheckRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| balanced | Boolean | 净利润与未分配利润变动是否一致 |
| differenceAmount | BigDecimal | 利润表与资产负债表勾稽差额 |
| unmappedSubjects | List&lt;UnmappedSubject&gt; | 未纳入报表公式的科目（结构同 1.4） |

**业务逻辑**:
1. 计算利润表与资产负债表，取净利润（行次 32）的本年累计金额，与资产负债表未分配利润（行次 51）的期末减年初变动额相减得到勾稽差额，差额为零时勾稽平衡。
2. 收集利润表各行公式引用的科目编号。
3. 检查未纳入公式的一级损益类科目（沿公式科目父级链向上匹配；以前年度损益调整等 `6` 开头科目编码除外），作为待补充公式的科目返回。

**错误码**: 同 2.1

## 3. 现金流量表（FmsCashFlowStatementController）

### 3.1 获得现金流量表

- **路径**: GET /fms/report/cash-flow-statement/get
- **权限**: fms:report:cash-flow-statement:query
- **说明**: 获得指定账套和会计期间的现金流量表，公式为跨报表表达式（BA/IN/EX/L 取数），由系统计算并支持人工调整。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;List&lt;FmsReportItemRespVO&gt;&gt;（见通用响应结构，本表使用本期金额 currentAmount 和本年累计金额 yearAmount）

**业务逻辑**:
1. 校验当前用户对账套的读权限；首次查询时按现金流量表模板初始化报表配置（跨报表表达式公式，不涉及科目绑定），并按查询期间创建报表快照，锁定账套避免并发重复初始化。
2. 查询取数数据：本期和本年两套资产负债表行次数据（本年自年初起算）、利润表项目和现金流量辅助数据。
3. 逐行计算跨报表表达式：`BA[行次,1|2]` 取资产负债表行次期初/期末金额、`IN行次` 取利润表行次金额、`EX行次` 取辅助数据行次金额、`L行次` 取本表已计算行次金额，参数替换为变量并校验表达式只含合法字符后交由 Aviator 计算；表达式为空或含非法字符时按零处理。
4. 允许调整金额的项目（有行次且非行次公式）已保存非零金额时，覆盖公式计算结果。
5. 将未明确归类的经营活动现金流倒挤归入"其他经营活动"行（行次 6）：按期末现金及现金等价物余额（行次 22）与资产负债表货币资金期末余额的差额计算，差额为正且原值为零时覆盖，并重算其后的行次公式项目使净额和余额联动更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |

### 3.2 导出现金流量表

- **路径**: GET /fms/report/cash-flow-statement/export-excel
- **权限**: fms:report:cash-flow-statement:export
- **说明**: 按查询条件计算现金流量表并导出为 Excel 文件（`现金流量表.xls`），导出逻辑与 3.1 相同，无响应 Body（Excel 流）。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: Excel 文件流，列包括项目、行次、本期金额、本年累计金额

**业务逻辑**:
1. 调用与 3.1 相同的查询逻辑获得报表项目数据。
2. 使用 ExcelUtils 按 FmsReportItemRespVO 上的 `@ExcelProperty` 注解写出 Excel 文件。

**错误码**: 同 3.1

### 3.3 更新现金流量表

- **路径**: PUT /fms/report/cash-flow-statement/update
- **权限**: fms:report:cash-flow-statement:update
- **说明**: 人工调整指定期间现金流量表项目的本期和本年累计金额。

**请求参数 (FmsCashFlowStatementUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| startMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 开始会计期间 |
| endMonth | String | 是 | @NotNull、@Pattern(`\d{4}-(0[1-9]|1[0-2])`) | 结束会计期间 |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid（嵌套校验） | 现金流量表项目 |

Item 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 报表项目编号 |
| currentAmount | BigDecimal | 是 | @NotNull | 本期金额 |
| yearAmount | BigDecimal | 是 | @NotNull | 本年累计金额 |

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验当前用户对账套的写权限。
2. 按账套和期间解析查询期间类型（单月/跨月），校验所有项目编号均属于该账套和期间的报表快照，缺失时抛出 `REPORT_CONFIG_NOT_EXISTS`。
3. 逐项校验允许调整金额（有行次且非行次公式的项目，表头和汇总行由系统自动计算），不允许时抛出 `REPORT_AMOUNT_NOT_ADJUSTABLE`。
4. 批量更新本期和本年累计金额（保存零值时下次查询重新按公式计算）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |
| 1_052_106_000 | 报表项目不存在 |
| 1_052_106_006 | 该现金流量表项目不允许调整金额 |

### 3.4 检查现金流量表

- **路径**: GET /fms/report/cash-flow-statement/check
- **权限**: fms:report:cash-flow-statement:query
- **说明**: 检查现金流量表取数前提，复用资产负债表检查结果并汇总是否满足取数条件。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;FmsCashFlowCheckRespVO&gt;（继承 FmsBalanceSheetCheckRespVO 全部字段）

| 字段 | 类型 | 说明 |
|-----|------|------|
| balanced | Boolean | 资产负债表是否平衡（继承字段） |
| initialBalanceBalanced | Boolean | 初始余额是否平衡（继承字段） |
| profitLossTransferred | Boolean | 损益是否已结转（继承字段） |
| openingDifferenceAmount | BigDecimal | 年初余额差额（继承字段） |
| closingDifferenceAmount | BigDecimal | 期末余额差额（继承字段） |
| unmappedSubjects | List&lt;UnmappedSubject&gt; | 未纳入报表公式的科目（继承字段，结构同 1.4） |
| balanceSheetReady | Boolean | 资产负债表是否满足现金流量表取数条件 |

**业务逻辑**:
1. 现金流量表本身无独立平衡关系，直接复用资产负债表检查（平衡状态、初始余额平衡、损益结转、未纳入公式科目）。
2. 四项检查全部通过（平衡、初始余额平衡、损益已结转、无未纳入公式的科目）时，`balanceSheetReady` 返回 true。

**错误码**: 同 3.1

### 3.5 获得现金流量辅助数据列表

- **路径**: GET /fms/report/cash-flow-statement/adjustment/list
- **权限**: fms:report:cash-flow-statement:query
- **说明**: 获得指定账套和会计期间的现金流量辅助数据（主表分类），用于辅助现金流量表取数。

**请求参数**: FmsReportListReqVO（见通用请求参数）

**响应**: CommonResult&lt;List&lt;FmsCashFlowAdjustmentRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 数据编号 |
| name | String | 项目名称 |
| rowNo | Integer | 行次 |
| formula | String | 公式（科目公式为含取数结果的 JSON，行次公式为 `["L1+L2"]` 形式） |
| remark | String | 说明 |
| editable | Boolean | 是否可编辑 |
| currentAmount | BigDecimal | 本期金额 |
| yearAmount | BigDecimal | 本年累计金额 |
| level | Integer | 层级 |

**业务逻辑**:
1. 校验当前用户对账套的读权限。
2. 首次查询时按现金流量辅助数据模板初始化配置：行次公式的辅助数据标记为固定类型、科目公式标记为自定义类型，模板公式中的科目编码绑定为本账套科目编号；并按查询期间创建辅助数据快照（金额初始化为零），锁定账套避免并发重复初始化。
3. 查询本期至期末的科目余额（扣除结转损益凭证影响）。
4. 逐项计算：行次公式直接引用已计算行次的金额；科目公式按发生额取数规则取数并按运算符累加，取数结果回写公式。
5. 人工调整金额非零时覆盖公式计算结果。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |

### 3.6 更新现金流量辅助数据

- **路径**: PUT /fms/report/cash-flow-statement/adjustment/update
- **权限**: fms:report:cash-flow-statement:update
- **说明**: 批量更新现金流量辅助数据的人工调整金额。

**请求参数 (FmsCashFlowAdjustmentUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid（嵌套校验） | 辅助数据项 |

Item 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 数据编号 |
| currentAmount | BigDecimal | 是 | @NotNull | 本期金额 |
| yearAmount | BigDecimal | 是 | @NotNull | 本年累计金额 |

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验当前用户对账套的写权限。
2. 校验所有辅助数据编号均属于该账套，缺失时抛出 `REPORT_ADJUSTMENT_NOT_EXISTS`。
3. 逐项校验允许编辑（editable 为 false 时抛出 `REPORT_CONFIG_NOT_EDITABLE`）。
4. 批量更新本期和本年累计金额。
5. 辅助数据变化后清空同期间现金流量表主表的人工调整金额，下次查询重新按公式计算。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_106_001 | 该报表项目不允许编辑公式 |
| 1_052_106_005 | 现金流量辅助数据不存在 |

### 3.7 更新现金流量辅助数据公式

- **路径**: PUT /fms/report/cash-flow-statement/adjustment/update-formula
- **权限**: fms:report:cash-flow-statement:update
- **说明**: 更新指定现金流量辅助数据项的取数公式，并将金额清零等待重算。

**请求参数**: FmsReportFormulaUpdateReqVO（见通用请求参数，取数规则范围：发生额类规则）

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验当前用户对账套的写权限。
2. 查询辅助数据，校验其存在、属于该账套（否则抛 `REPORT_ADJUSTMENT_NOT_EXISTS`）且允许编辑（否则抛 `REPORT_CONFIG_NOT_EDITABLE`）。
3. 校验并构造公式：科目不能重复、运算符必须是 `+`/`-`、取数规则必须在发生额类规则范围内、科目必须存在。
4. 更新当前期间辅助数据的公式，并将本期、本年累计金额清零，下次查询重新按公式计算。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_101_000 | 科目不存在 |
| 1_052_106_001 | 该报表项目不允许编辑公式 |
| 1_052_106_002 | 报表公式科目不能重复 |
| 1_052_106_003 | 报表公式取数规则不正确 |
| 1_052_106_004 | 报表公式运算符不正确 |
| 1_052_106_005 | 现金流量辅助数据不存在 |
