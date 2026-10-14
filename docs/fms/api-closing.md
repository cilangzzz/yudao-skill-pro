# 期末结账接口 (FmsClosingPeriodController / FmsClosingSchemeController / FmsClosingTemplateController / FmsClosingVoucherController)

> 提供 FMS 财务核算的期末结账能力：会计期间查询与结账/反结账登记、结账前检查项概况、结账方案与结转损益/专用结转设置维护、结账模板管理，以及结转损益凭证与方案结转凭证的生成。

## 接口路径前缀

- /fms/closing/period (Controller: FmsClosingPeriodController) —— 结账期间
- /fms/closing/scheme (Controller: FmsClosingSchemeController) —— 结账方案
- /fms/closing/template (Controller: FmsClosingTemplateController) —— 结账模板
- /fms/closing/voucher (Controller: FmsClosingVoucherController) —— 结转凭证

## 1. 结账期间（FmsClosingPeriodController）

### 1.1 获得当前会计期间

- **路径**: GET /fms/closing/period/current-month
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 返回账套当前会计期间（最近已结账期间的下一月份），前端结账页与凭证录入均以此为准。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;String&gt;，当前会计期间字符串，格式 `yyyy-MM`（如 "2026-08"）。

**业务逻辑**:
1. 校验账套读权限。
2. 校验账套已完成初始化且启用于期不为空，否则报错。
3. 查询账套最近一条结账期间记录，返回其结账月份的下一月份；无结账记录时返回账套启用月份。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_005 | 账套尚未完成初始化 |

### 1.2 获得结账概况

- **路径**: GET /fms/closing/period/overview
- **权限**: fms:closing:query
- **说明**: 汇总指定会计期间的全部结账前检查项，并给出是否满足结账条件的综合判定。

**请求参数 (FmsClosingQueryReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| month | String | 是 | @NotBlank、@Pattern(yyyy-MM) | 目标会计期间 |

**响应**: CommonResult&lt;FmsClosingOverviewRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| month | String | 会计期间 |
| closed | Boolean | 是否已结账 |
| voucherReviewRequired | Boolean | 财务参数是否要求凭证审核 |
| pendingVoucherCount | Long | 未审核凭证数量（不含结转流程生成的凭证） |
| voucherCount | Long | 当期凭证数量 |
| profitLossBalance | BigDecimal | 末级损益科目本期借贷差额绝对值合计 |
| balanceSheetDifference | BigDecimal | 资产负债表资产合计与负债合计的差额绝对值 |
| profitLossVoucherId | Long | 当期结转损益凭证编号（未生成则为空） |
| initialBalanceBalanced | Boolean | 初始余额是否试算平衡 |
| voucherNumberContinuous | Boolean | 各凭证字凭证号是否从 1 开始连续 |
| profitLossVoucherGenerated | Boolean | 当期有损益发生额时是否已生成结转损益凭证 |
| incomeStatementBalanced | Boolean | 利润表勾稽是否平衡 |
| incomeStatementUnmappedSubjectCount | Integer | 利润表未纳入公式的科目数量 |
| balanceSheetProfitLossTransferred | Boolean | 资产负债表损益是否已结转 |
| balanceSheetBalanced | Boolean | 资产负债表是否平衡 |
| balanceSheetUnmappedSubjectCount | Integer | 资产负债表未纳入公式的科目数量 |
| canClose | Boolean | 是否满足全部结账条件 |

**业务逻辑**:
1. 校验账套读权限，解析会计期间的起止时间。
2. 查询当期凭证与结转凭证，统计待审核凭证数（结转凭证不提供人工审核入口，不计入）；计算末级损益科目余额与资产负债表差额；查询结转损益方案及当期对应结转凭证。
3. 查询其余检查项：初始余额试算平衡、凭证号连续性、损益结转凭证是否已生成（无损益发生额视为已生成）、利润表与资产负债表勾稽检查结果。
4. 读取财务参数判断是否强制凭证审核，逐项汇总 `canClose`：未结账、待审核凭证为 0、试算平衡、凭证号连续、损益凭证已生成、损益余额为 0、利润表与资产负债表平衡且无未映射科目。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_104_010 | 开始会计期间不能早于账套启用期间 |

### 1.3 结账

- **路径**: PUT /fms/closing/period/close
- **权限**: fms:closing:close
- **说明**: 对目标会计期间执行结账检查并登记结账状态，支持从当前期间逐月连续结账到目标期间。

**请求参数 (FmsClosingQueryReqVO)**（RequestBody）: 字段同 1.2。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限并锁定账套（串行化结账状态变更），校验账套已初始化；目标期间不能早于当前会计期间。
2. 从当前会计期间到目标期间逐月执行单期结账。
3. 每期先获取结账概况并校验：未结账、启用审核时待审核凭证数为 0、初始余额试算平衡、凭证号连续。
4. 校验损益项：损益结转凭证已生成、损益余额为 0、利润表勾稽平衡且无未映射科目、资产负债表损益已结转且平衡且无未映射科目。
5. 插入结账期间记录（结账时间为当月月末）。
6. 将当期结转凭证标记为已结账。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_105_000 | 该会计期间已结账 |
| 1_052_105_003 | 存在未审核凭证，不能结账 |
| 1_052_105_004 | 损益类科目尚有余额，请先结转损益 |
| 1_052_105_005 | 资产负债表不平衡，不能结账 |
| 1_052_105_013 | 只能操作当前会计期间 |
| 1_052_105_018 | 初始余额试算不平衡，不能结账 |
| 1_052_105_019 | 当前期间存在断号凭证，请先整理凭证号 |
| 1_052_105_020 | 当前期间存在损益发生额，请先生成结转损益凭证 |
| 1_052_105_021 | 利润表勾稽不平衡，不能结账 |
| 1_052_105_022 | 存在未纳入报表公式的科目，不能结账 |

### 1.4 反结账

- **路径**: DELETE /fms/closing/period/cancel
- **权限**: fms:closing:cancel
- **说明**: 从最近已结账期间逐月撤销结账状态到目标期间，恢复期间可编辑。

**请求参数 (FmsClosingQueryReqVO)**（Query 参数）: 字段同 1.2。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限并锁定账套。
2. 校验目标期间已结账：存在结账记录、目标期间不晚于最近结账期间、不早于账套启用期间，否则报错。
3. 从最近结账期间逐月向前撤销到目标期间。
4. 每期删除结账期间记录，并将当期结转凭证标记为未结账。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_105_001 | 该会计期间尚未结账 |

## 2. 结账方案（FmsClosingSchemeController）

> 结账方案分三类：结转损益（type=2，每账套一条）、常规结账方案（type=1，可增删改）、专用结转方案（type=3/4/5，转出未交增值税、计提地税、计提所得税，仅可修改凭证字与科目规则）。账套初始化时按预置 JSON 自动创建。

### 2.1 获得结账方案列表

- **路径**: GET /fms/closing/scheme/list
- **权限**: fms:closing:query
- **说明**: 查询账套全部期末结转方案，并计算各方案当期待结转金额与已生成凭证信息。

**请求参数 (FmsClosingQueryReqVO)**: 字段同 1.2。

**响应**: CommonResult&lt;List&lt;FmsClosingSchemeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 方案编号 |
| accountSetId | Long | 账套编号 |
| name | String | 方案名称 |
| periodEnd | Boolean | 是否期末结转 |
| subjectId | Long | 来源科目编号（常规方案） |
| formulaRule | Integer | 取数规则（0 余额/1 借方余额/2 贷方余额/3 科目借方余额/4 科目贷方余额/5 借方发生额/6 贷方发生额/7 损益发生额） |
| timeType | Integer | 取数时间类型（1 期末/2 期初/3 年初） |
| voucherWordId | Long | 凭证字编号 |
| digest | String | 凭证摘要 |
| voucherType | Integer | 结转凭证类型（1 收益和损失分开结转/2 收益和损失同时结转，仅结转损益方案） |
| priorYearAdjustmentSubjectId | Long | 以前年度损益调整科目编号（仅结转损益方案） |
| adjustmentClosingSubjectId | Long | 以前年度损益调整结转科目编号（仅结转损益方案） |
| otherClosingSubjectId | Long | 其他损益结转科目编号（仅结转损益方案） |
| reverseBalance | Boolean | 是否按余额反向结转（仅结转损益方案） |
| closingDay | Integer | 结转日期（1-31，仅结转损益方案） |
| type | Integer | 方案类型（1 常规结账/2 结转损益/3 转出未交增值税/4 计提地税/5 计提所得税） |
| subjects | List&lt;SubjectRule&gt; | 结转科目规则数组 |
| balance | BigDecimal | 待结转金额（已生成凭证时为其金额合计） |
| voucherIds | List&lt;Long&gt; | 当前期间已生成凭证编号数组 |

SubjectRule 结构:

| 字段 | 类型 | 说明 |
|-----|------|------|
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码快照 |
| digest | String | 摘要 |
| direction | Integer | 借贷方向（1 借/2 贷） |
| amountRatio | BigDecimal | 金额比例 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套全部期末结转方案，为空直接返回；加载当期科目余额，存在年初口径方案时额外加载年初至当期区间余额；按方案分组加载当期已生成结转凭证；查询账套科目供专用方案取数。
3. 按类型计算待结转金额：结转损益方案取末级损益科目本期借贷差额绝对值合计；常规方案按取数时间类型（期初/期末余额、本期/本年发生额）与取数规则计算；专用方案按预置公式（转出未交增值税取应交增值税期末贷方净额，计提地税按增值税与消费税合计乘比例，计提所得税按利润总额减已计提后乘比例）。
4. 已生成凭证的方案展示凭证金额合计作为 balance，并回填已生成凭证编号数组。
5. 转换科目规则并组装响应列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_105_017 | 专用结转所需的预置科目不存在 |

### 2.2 创建结账方案

- **路径**: POST /fms/closing/scheme/create
- **权限**: fms:closing:update
- **说明**: 创建常规结账方案。

**请求参数 (FmsClosingSchemeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 方案编号（创建时忽略） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 方案名称 |
| periodEnd | Boolean | 是 | @NotNull | 是否期末结转 |
| subjectId | Long | 是 | @NotNull | 来源科目编号 |
| formulaRule | Integer | 是 | @NotNull、@InEnum(FmsFormulaRuleEnum) | 取数规则 |
| timeType | Integer | 是 | @NotNull、@InEnum(FmsClosingTimeTypeEnum) | 取数时间类型 |
| voucherWordId | Long | 是 | @NotNull | 凭证字编号 |
| subjects | List&lt;SubjectRule&gt; | 是 | @Valid、@NotEmpty、@Size(min=2) | 结转科目规则数组（至少两条） |

SubjectRule 结构:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| subjectId | Long | 是 | @NotNull | 科目编号 |
| digest | String | 是 | @NotBlank、@Size(max=500) | 摘要 |
| direction | Integer | 是 | @NotNull、@InEnum(FmsDebitCreditDirectionEnum) | 借贷方向（1 借/2 贷） |
| amountRatio | BigDecimal | 是 | @NotNull、@DecimalMin(0, excl)、@DecimalMax(100) | 金额比例 |

**响应**: CommonResult&lt;Long&gt;，方案编号。

**业务逻辑**:
1. 校验账套写权限。
2. 校验凭证字存在。
3. 校验来源科目与各规则科目存在且为末级科目。
4. 校验借方、贷方金额比例分别合计等于 100%。
5. 构造方案（类型固定为常规结账，摘要取方案名称），按科目编号补充科目编码快照后插入。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_009 | 结账方案科目不正确 |
| 1_052_105_010 | 结账方案借贷金额比例必须分别等于 100% |

### 2.3 修改结账方案

- **路径**: PUT /fms/closing/scheme/update
- **权限**: fms:closing:update
- **说明**: 修改常规结账方案（仅常规方案可修改）。

**请求参数 (FmsClosingSchemeSaveReqVO)**: 字段同 2.2（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验方案存在且类型为常规结账，否则报"结账方案不存在"。
3. 校验凭证字存在。
4. 校验来源科目与规则科目末级、借贷比例各为 100%。
5. 更新方案并重建科目规则编码快照。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_008 | 结账方案不存在 |
| 1_052_105_009 | 结账方案科目不正确 |
| 1_052_105_010 | 结账方案借贷金额比例必须分别等于 100% |

### 2.4 保存结转损益设置

- **路径**: PUT /fms/closing/scheme/update-profit-loss-settings
- **权限**: fms:closing:update
- **说明**: 创建或更新账套的结转损益方案设置（每账套一条，返回方案编号）。

**请求参数 (FmsProfitLossSettingsSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| voucherWordId | Long | 是 | @NotNull | 凭证字编号 |
| digest | String | 是 | @NotBlank、@Size(max=500) | 凭证摘要 |
| voucherType | Integer | 是 | @NotNull、@InEnum(FmsClosingVoucherTypeEnum) | 结转凭证类型（1 收益和损失分开结转/2 收益和损失同时结转） |
| priorYearAdjustmentSubjectId | Long | 是 | @NotNull | 以前年度损益调整科目编号 |
| adjustmentClosingSubjectId | Long | 是 | @NotNull | 以前年度损益调整结转科目编号 |
| otherClosingSubjectId | Long | 是 | @NotNull | 其他损益结转科目编号 |
| reverseBalance | Boolean | 是 | @NotNull | 是否按余额反向结转 |
| closingDay | Integer | 是 | @NotNull、@Min(1)、@Max(31) | 结转日期 |

**响应**: CommonResult&lt;Long&gt;，结转损益方案编号。

**业务逻辑**:
1. 校验账套写权限。
2. 校验凭证字存在。
3. 校验科目合法性：以前年度损益调整科目必须为末级损益科目，两个结转科目必须为末级非损益科目。
4. 按结转损益类型查询已有方案：不存在则新增，存在则更新，方案名称与类型由系统固定。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_014 | 结转损益科目设置不正确 |

### 2.5 保存专用结转设置

- **路径**: PUT /fms/closing/scheme/update-special-settings
- **权限**: fms:closing:update
- **说明**: 修改专用结转方案（转出未交增值税/计提地税/计提所得税）的凭证字与科目规则。

**请求参数 (FmsSpecialClosingSettingsSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 方案编号 |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| voucherWordId | Long | 是 | @NotNull | 凭证字编号 |
| subjects | List&lt;SubjectRule&gt; | 是 | @Valid、@NotEmpty、@Size(min=2) | 结转科目规则数组（至少两条） |

SubjectRule 结构:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| subjectId | Long | 是 | @NotNull | 科目编号 |
| digest | String | 是 | @NotBlank、@Size(max=500) | 摘要 |
| direction | Integer | 是 | @NotNull、@InEnum(FmsDebitCreditDirectionEnum) | 借贷方向（1 借/2 贷） |
| amountRatio | BigDecimal | 是 | @NotNull、@DecimalMin(0, excl)、@DecimalMax(100) | 金额比例 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验方案存在且为专用结转方案，否则报"结账方案不存在"。
3. 校验凭证字存在，规则科目存在且为末级科目。
4. 校验借方比例等于贷方比例、大于 0 且不超过 100%；转出未交增值税方案借方比例必须等于 100%。
5. 更新方案的凭证字与科目规则（补充科目编码快照）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_008 | 结账方案不存在 |
| 1_052_105_016 | 专用结转设置不正确 |

### 2.6 删除结账方案

- **路径**: DELETE /fms/closing/scheme/delete
- **权限**: fms:closing:update
- **说明**: 删除常规结账方案，已生成过结转凭证的方案不可删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 方案编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验方案存在且类型为常规结账，否则报"结账方案不存在"。
3. 校验方案未生成过结转凭证。
4. 删除方案。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_105_008 | 结账方案不存在 |
| 1_052_105_012 | 结账方案已生成凭证，不能删除 |

## 3. 结账模板（FmsClosingTemplateController）

> 结账模板是常见结转业务的凭证分录模板（按借贷比例分摊），可作为快速创建结账方案的参照；系统预置模板在账套初始化时从 JSON 导入。

### 3.1 获得结账模板列表

- **路径**: GET /fms/closing/template/list
- **权限**: fms:closing:query
- **说明**: 查询账套全部结账模板（含系统预置与自定义）。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsClosingTemplateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模板编号 |
| accountSetId | Long | 账套编号 |
| presetCode | String | 系统预置编码（自定义模板为空） |
| name | String | 模板名称 |
| category | Integer | 模板分类（1 日常开支/2 采购销售/3 往来款/4 转账业务） |
| periodEnd | Boolean | 是否期末结转 |
| subjectId | Long | 来源科目编号 |
| formulaRule | Integer | 取数规则 |
| timeType | Integer | 取数时间类型 |
| subjects | List&lt;SubjectRule&gt; | 结转科目规则数组 |
| sort | Integer | 显示顺序 |
| createTime | LocalDateTime | 创建时间 |

SubjectRule 结构:

| 字段 | 类型 | 说明 |
|-----|------|------|
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| digest | String | 摘要 |
| direction | Integer | 借贷方向（1 借/2 贷） |
| amountRatio | BigDecimal | 金额比例 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套全部结账模板，转换科目规则数组后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |

### 3.2 创建结账模板

- **路径**: POST /fms/closing/template/create
- **权限**: fms:closing:update
- **说明**: 创建自定义结账模板。

**请求参数 (FmsClosingTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 模板编号（创建时忽略） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 模板名称 |
| category | Integer | 是 | @NotNull、@InEnum(FmsClosingTemplateCategoryEnum) | 模板分类（1 日常开支/2 采购销售/3 往来款/4 转账业务） |
| periodEnd | Boolean | 是 | @NotNull | 是否期末结转 |
| subjectId | Long | 否 | - | 来源科目编号 |
| formulaRule | Integer | 否 | @InEnum(FmsFormulaRuleEnum) | 取数规则 |
| timeType | Integer | 否 | @InEnum(FmsClosingTimeTypeEnum) | 取数时间类型 |
| subjects | List&lt;SubjectRule&gt; | 是 | @Valid、@NotEmpty、@Size(min=2) | 结转科目规则数组（至少两条） |
| sort | Integer | 是 | @NotNull | 显示顺序 |

SubjectRule 结构:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| subjectId | Long | 是 | @NotNull | 科目编号 |
| digest | String | 是 | @NotBlank、@Size(max=500) | 摘要 |
| direction | Integer | 是 | @NotNull、@InEnum(FmsDebitCreditDirectionEnum) | 借贷方向（1 借/2 贷） |
| amountRatio | BigDecimal | 是 | @NotNull、@DecimalMin(0, excl)、@DecimalMax(100) | 金额比例 |

**响应**: CommonResult&lt;Long&gt;，模板编号。

**业务逻辑**:
1. 校验账套写权限。
2. 校验来源科目（填写时）与各规则科目存在且为末级科目。
3. 校验借方、贷方金额比例分别合计等于 100%。
4. 构造模板并按科目编号补充科目编码快照，插入后返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_105_009 | 结账方案科目不正确 |
| 1_052_105_010 | 结账方案借贷金额比例必须分别等于 100% |

### 3.3 更新结账模板

- **路径**: PUT /fms/closing/template/update
- **权限**: fms:closing:update
- **说明**: 更新结账模板。

**请求参数 (FmsClosingTemplateSaveReqVO)**: 字段同 3.2（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验结账模板存在。
3. 校验来源科目与规则科目末级、借贷比例各为 100%。
4. 更新模板并重建科目规则编码快照。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_105_009 | 结账方案科目不正确 |
| 1_052_105_010 | 结账方案借贷金额比例必须分别等于 100% |
| 1_052_105_023 | 结账模板不存在 |

### 3.4 删除结账模板

- **路径**: DELETE /fms/closing/template/delete
- **权限**: fms:closing:update
- **说明**: 删除结账模板（预置模板同样可删除）。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验结账模板存在。
3. 删除模板。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_105_023 | 结账模板不存在 |

## 4. 结转凭证（FmsClosingVoucherController）

> 按结账方案自动生成结转凭证并登记方案-凭证关联；同一方案同一期间重复生成时先删除旧凭证及其关联再重建。

### 4.1 生成结转损益凭证

- **路径**: POST /fms/closing/voucher/generate-profit-loss
- **权限**: fms:closing:profit-loss
- **说明**: 按结转损益设置，将当期末级损益科目余额结转至利润类科目，支持按收益/损失分开或合并生成凭证。

**请求参数 (FmsProfitLossGenerateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| month | String | 是 | @NotBlank、@Pattern(yyyy-MM) | 会计期间 |

**响应**: CommonResult&lt;Long&gt;，首张结转凭证编号（收支分开结转时可能生成两张）。

**业务逻辑**:
1. 校验账套写权限与初始化状态并锁定账套，指定期间必须为账套当前会计期间且未结账。
2. 校验结转损益设置已配置、凭证字存在、三个科目合法；重新生成时先删除当前期间已生成的旧凭证及关联。
3. 计算末级损益科目本期发生额与当期凭证分录，按凭证类型构造分录：收支分开结转时分别生成收益、损失两组分录，否则合并生成。
4. 逐个损益科目按余额方向与"是否按余额反向结转"生成分录，启用辅助核算时按辅助核算组合逐一结平；以前年度损益调整科目结转至专用结转科目；无可结转余额时报错。
5. 按结转日期（不超过当月天数）生成凭证并自动取凭证号，登记方案-凭证关联（金额为分录借方合计），返回首张凭证编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_000 | 该会计期间已结账 |
| 1_052_105_007 | 当前期间无需结转损益 |
| 1_052_105_013 | 只能操作当前会计期间 |
| 1_052_105_014 | 结转损益科目设置不正确 |
| 1_052_105_015 | 请先完成结转损益参数设置 |

### 4.2 生成结账方案凭证

- **路径**: POST /fms/closing/voucher/generate-scheme
- **权限**: fms:closing:profit-loss
- **说明**: 按单个常规或专用结账方案计算结转金额并生成结转凭证。

**请求参数 (FmsClosingSchemeGenerateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 方案编号 |
| month | String | 是 | @NotBlank、@Pattern(yyyy-MM) | 会计期间 |

**响应**: CommonResult&lt;Long&gt;，结转凭证编号。

**业务逻辑**:
1. 校验账套写权限、初始化状态并锁定账套，指定期间必须为当前会计期间且未结账。
2. 校验方案存在且为常规或专用结转方案；常规方案必须已启用期末结转；校验凭证字存在。
3. 重新生成时先删除当前期间的旧结转凭证及关联。
4. 加载科目余额（年初口径方案取年初至当期区间），按方案类型计算结转金额：专用方案按预置公式，常规方案按取数规则；余额为零报错。
5. 按科目规则构造分录：常规方案按金额比例分摊；专用方案借贷两侧按比例分摊、每侧最后一条倒挤剩余金额保证合计等于结转金额。
6. 以当月月末为凭证日期生成凭证并自动取凭证号，登记方案-凭证关联。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_000 | 该会计期间已结账 |
| 1_052_105_008 | 结账方案不存在 |
| 1_052_105_011 | 当前期间无需生成该结转凭证 |
| 1_052_105_013 | 只能操作当前会计期间 |
| 1_052_105_017 | 专用结转所需的预置科目不存在 |
| 1_052_105_027 | 该结账方案未启用期末结转 |

### 4.3 批量生成结转凭证

- **路径**: POST /fms/closing/voucher/generate-list
- **权限**: fms:closing:profit-loss
- **说明**: 一键结账场景下批量生成多个方案的结转凭证，余额为零的方案自动跳过。

**请求参数 (FmsClosingVoucherGenerateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 是 | @NotEmpty、元素 @NotNull | 方案编号数组 |
| month | String | 是 | @NotBlank、@Pattern(yyyy-MM) | 会计期间 |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt;，本次实际生成的凭证编号数组。

**业务逻辑**:
1. 校验账套写权限、初始化状态并锁定账套，指定期间必须为当前会计期间且未结账。
2. 方案编号去重后逐一校验：方案存在且类型为结转损益、常规或专用结转方案，常规方案必须已启用期末结转。
3. 统一删除本批方案当前期间的旧结转凭证及关联，避免逐个重建造成凭证号断号。
4. 在同一事务中逐个生成：结转损益方案走结转损益流程，其余走方案凭证流程。
5. 生成中仅"余额为零"类错误被捕获并跳过该方案，其他错误中断回滚；返回成功生成的凭证编号数组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_105_000 | 该会计期间已结账 |
| 1_052_105_008 | 结账方案不存在 |
| 1_052_105_013 | 只能操作当前会计期间 |
| 1_052_105_027 | 该结账方案未启用期末结转 |
