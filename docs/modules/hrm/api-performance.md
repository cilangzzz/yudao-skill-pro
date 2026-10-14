# 绩效管理接口 (HrmPerformanceAssessmentTemplateController / HrmPerformanceResultTemplateController / HrmPerformancePlanController / HrmPerformanceAssessmentController)

> 提供 HRM 绩效管理全流程：绩效考核模板与绩效结果模板的版本化维护、绩效计划（考评范围/评分流程/申诉配置）的创建与启动/评分/面谈/归档/终止流转、员工绩效考核的分页查询与流程记录查看，以及绩效归档（归档分页、员工档案、归档删除）。

## 接口路径前缀

- /hrm/performance/assessment-template  (Controller: HrmPerformanceAssessmentTemplateController) —— 绩效考核模板
- /hrm/performance/result-template  (Controller: HrmPerformanceResultTemplateController) —— 绩效结果模板
- /hrm/performance/plan  (Controller: HrmPerformancePlanController) —— 绩效计划
- /hrm/performance/assessment  (Controller: HrmPerformanceAssessmentController) —— 员工绩效考核与归档

---

## 1. 绩效考核模板

### 1.1 创建绩效考核模板

- **路径**: POST /hrm/performance/assessment-template/create
- **权限**: `hrm:performance:assessment-template:create`
- **说明**: 新建考核模板（名称、计分方式、分数上限、维度与指标配置），创建后状态固定为开启

**请求参数 (HrmPerformanceAssessmentTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | | 模板编号（创建时为空） |
| name | String | 是 | @NotBlank、@Size(max=50) | 模板名称 |
| illustrate | String | 否 | @Size(max=200) | 模板说明 |
| scoreCalculation | Integer | 是 | @NotNull、@InEnum(HrmPerformanceScoreCalculationEnum) | 计分方式 |
| upperLimitType | Integer | 是 | @NotNull、@InEnum(HrmPerformanceUpperLimitTypeEnum) | 分数上限类型 |
| upperLimitScore | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@DecimalMax(100) | 分数上限 |
| dimensions | List&lt;Dimension&gt; | 是 | @Valid、@NotEmpty、元素 @NotNull | 考核维度列表 |

**Dimension（考核维度）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| name | String | 是 | @NotBlank、@Size(max=50) | 维度名称 |
| quotaType | Integer | 是 | @NotNull、@InEnum(HrmPerformanceQuotaTypeEnum) | 指标类型 |
| weight | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@DecimalMax(100) | 维度权重 |
| remark | String | 否 | @Size(max=200) | 备注 |
| allowEdit | Boolean | 是 | @NotNull | 是否允许员工编辑 |
| quotas | List&lt;Quota&gt; | 是 | @Valid、@NotEmpty、元素 @NotNull | 考核指标列表 |

**Quota（考核指标）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| name | String | 是 | @NotBlank、@Size(max=50) | 指标名称 |
| illustrate | String | 否 | @Size(max=200) | 指标说明 |
| standard | String | 是 | @NotBlank、@Size(max=200) | 评分标准 |
| weight | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@DecimalMax(100) | 指标权重 |
| scoreType | Integer | 是 | @NotNull、@InEnum(HrmPerformanceQuotaScoreTypeEnum) | 评分类型 |

类级 @AssertTrue 校验：维度名称不能重复、指标名称（跨维度）不能重复、维度权重总和必须等于 100%、不可编辑维度的指标权重总和必须等于 100%、可编辑维度的指标权重总和不能大于 100%。

**响应**: CommonResult&lt;Long&gt; —— 模板编号

**业务逻辑**:
1. 校验模板名称唯一（同名且不同编号时抛出错误码 `1_050_600_001`）
2. VO 转 DO，状态固定为开启（ENABLE）
3. 规范化模板：模板名称、说明、维度名称、维度备注、指标名称、指标说明、评分标准去除首尾空白，allowEdit 归一化为布尔值，并重新计算维度数量与指标数量
4. 插入模板并返回编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_001 | 绩效考核模板名称已存在 |
| 1_050_600_007 | 绩效数据不合法 |

### 1.2 更新绩效考核模板

- **路径**: PUT /hrm/performance/assessment-template/update
- **权限**: `hrm:performance:assessment-template:update`
- **说明**: 采用版本化更新——停用旧模板并创建新版本，既有绩效计划继续引用旧模板编号

**请求参数 (HrmPerformanceAssessmentTemplateSaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验模板存在且为启用状态（否则抛出 `1_050_600_000`）
2. 校验新模板名称唯一
3. 将旧模板置为停用状态，避免修改已被绩效计划引用的模板版本
4. 以新内容创建新版本（编号置空、状态开启、保留原创建人与创建时间）并插入，既有绩效计划继续引用旧模板编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_000 | 绩效考核模板不存在（不存在或已停用） |
| 1_050_600_001 | 绩效考核模板名称已存在 |

### 1.3 删除绩效考核模板

- **路径**: DELETE /hrm/performance/assessment-template/delete
- **权限**: `hrm:performance:assessment-template:delete`
- **说明**: 删除单个考核模板，已被绩效计划引用时禁止删除

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验模板存在
2. 校验模板未被绩效计划使用（引用数大于 0 时抛出 `1_050_600_007`）
3. 删除考核模板

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_000 | 绩效考核模板不存在 |
| 1_050_600_007 | 绩效数据不合法（模板已被绩效计划使用） |

### 1.4 批量删除绩效考核模板

- **路径**: DELETE /hrm/performance/assessment-template/delete-list
- **权限**: `hrm:performance:assessment-template:delete`
- **说明**: 批量删除考核模板

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| ids | List&lt;Long&gt; | 是 | @RequestParam | 模板编号列表，如 1024,1025 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 批量查询模板，查询数量与去重后的编号数量不一致时抛出 `1_050_600_000`
2. 逐一校验模板未被绩效计划使用（否则抛出 `1_050_600_007`）
3. 批量删除考核模板

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_000 | 绩效考核模板不存在 |
| 1_050_600_007 | 绩效数据不合法 |

### 1.5 获得绩效考核模板

- **路径**: GET /hrm/performance/assessment-template/get
- **权限**: `hrm:performance:assessment-template:query`
- **说明**: 按编号获得考核模板详情，拼接创建人名称

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;HrmPerformanceAssessmentTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 模板编号 |
| name | String | 模板名称 |
| illustrate | String | 模板说明 |
| scoreCalculation | Integer | 计分方式 |
| upperLimitType | Integer | 分数上限类型 |
| upperLimitScore | BigDecimal | 分数上限 |
| dimensionCount | Integer | 维度数量 |
| quotaCount | Integer | 指标数量 |
| status | Integer | 状态 |
| dimensions | List&lt;Dimension&gt; | 考核维度列表 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称（拼接） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**Dimension**: name（维度名称）、quotaType（指标类型）、weight（维度权重）、remark（备注）、allowEdit（是否允许员工编辑）、quotas（考核指标列表）
**Quota**: name（指标名称）、illustrate（指标说明）、standard（评分标准）、weight（指标权重）、scoreType（评分类型）

**业务逻辑**:
1. 按编号查询考核模板
2. 批量查询创建人用户信息，将创建人昵称拼接到 creatorName

### 1.6 获得绩效考核模板分页

- **路径**: GET /hrm/performance/assessment-template/page
- **权限**: `hrm:performance:assessment-template:query`
- **说明**: 按名称模糊分页查询考核模板，拼接创建人名称

**请求参数 (HrmPerformanceAssessmentTemplatePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| name | String | 否 | | 模板名称，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;HrmPerformanceAssessmentTemplateRespVO&gt;&gt; —— 字段同 1.5

**业务逻辑**:
1. 按名称模糊分页查询考核模板
2. 结果为空时直接返回空分页
3. 批量拼接创建人昵称

### 1.7 获得绩效考核模板精简列表

- **路径**: GET /hrm/performance/assessment-template/simple-list
- **权限**: `hrm:performance:assessment-template:query`
- **说明**: 获得全部启用状态的考核模板精简列表（供下拉选择）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmPerformanceAssessmentTemplateRespVO&gt;&gt; —— 字段同 1.5

**业务逻辑**:
1. 查询状态为开启（ENABLE）的考核模板列表
2. VO 转换后返回（不拼接创建人）

---

## 2. 绩效结果模板

### 2.1 创建绩效结果模板

- **路径**: POST /hrm/performance/result-template/create
- **权限**: `hrm:performance:result-template:create`
- **说明**: 新建绩效结果模板（结果等级名称、分数区间、绩效系数），创建后状态固定为开启

**请求参数 (HrmPerformanceResultTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | | 结果模板编号（创建时为空） |
| name | String | 是 | @NotBlank、@Size(max=255) | 结果模板名称 |
| levels | List&lt;Level&gt; | 是 | @Valid、@NotEmpty、元素 @NotNull | 结果等级列表 |

类级 @AssertTrue 校验：结果等级名称不能重复、结果等级分数区间必须连续覆盖 0 到 100 分。

**Level（结果等级）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| name | String | 是 | @NotBlank、@Size(max=255) | 等级名称 |
| minScore | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@DecimalMax(100)、@Digits(integer=3, fraction=2) | 最低分数 |
| maxScore | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@DecimalMax(100)、@Digits(integer=3, fraction=2) | 最高分数 |
| coefficient | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@Digits(integer=8, fraction=2) | 绩效系数 |

Level 内 @AssertTrue 校验：最低分数不能大于最高分数。

**响应**: CommonResult&lt;Long&gt; —— 结果模板编号

**业务逻辑**:
1. 校验结果模板名称唯一（同名且不同编号时抛出 `1_050_600_003`）
2. VO 转 DO，状态固定为开启（ENABLE）
3. 插入结果模板并返回编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_003 | 绩效结果模板名称已存在 |

### 2.2 更新绩效结果模板

- **路径**: PUT /hrm/performance/result-template/update
- **权限**: `hrm:performance:result-template:update`
- **说明**: 版本化更新——停用旧模板并创建新版本，既有绩效计划继续引用旧模板编号和结果配置快照

**请求参数 (HrmPerformanceResultTemplateSaveReqVO)**: 同 2.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验结果模板存在且为启用状态（否则抛出 `1_050_600_002`）
2. 校验新结果模板名称唯一
3. 将旧模板置为停用状态，避免修改已被绩效计划引用的模板版本
4. 以新内容创建新版本（编号置空、状态开启、保留原创建人与创建时间）并插入

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_002 | 绩效结果模板不存在（不存在或已停用） |
| 1_050_600_003 | 绩效结果模板名称已存在 |

### 2.3 删除绩效结果模板

- **路径**: DELETE /hrm/performance/result-template/delete
- **权限**: `hrm:performance:result-template:delete`
- **说明**: 删除单个结果模板，已被绩效计划引用时禁止删除

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验结果模板存在
2. 校验结果模板未被绩效计划使用（引用数大于 0 时抛出 `1_050_600_007`）
3. 删除结果模板

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_002 | 绩效结果模板不存在 |
| 1_050_600_007 | 绩效数据不合法（模板已被绩效计划使用） |

### 2.4 批量删除绩效结果模板

- **路径**: DELETE /hrm/performance/result-template/delete-list
- **权限**: `hrm:performance:result-template:delete`
- **说明**: 批量删除结果模板

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| ids | List&lt;Long&gt; | 是 | @RequestParam | 模板编号列表，如 1024,1025 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 批量查询结果模板，查询数量与去重后的编号数量不一致时抛出 `1_050_600_002`
2. 逐一校验模板未被绩效计划使用（否则抛出 `1_050_600_007`）
3. 批量删除结果模板

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_002 | 绩效结果模板不存在 |
| 1_050_600_007 | 绩效数据不合法 |

### 2.5 获得绩效结果模板

- **路径**: GET /hrm/performance/result-template/get
- **权限**: `hrm:performance:result-template:query`
- **说明**: 按编号获得结果模板详情，拼接创建人名称

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;HrmPerformanceResultTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 结果模板编号 |
| name | String | 结果模板名称 |
| status | Integer | 状态 |
| levels | List&lt;Level&gt; | 结果等级列表 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称（拼接） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**Level**: name（等级名称）、minScore（最低分数）、maxScore（最高分数）、coefficient（绩效系数）

**业务逻辑**:
1. 按编号查询结果模板
2. 批量查询创建人用户信息，将创建人昵称拼接到 creatorName

### 2.6 获得绩效结果模板分页

- **路径**: GET /hrm/performance/result-template/page
- **权限**: `hrm:performance:result-template:query`
- **说明**: 按名称模糊分页查询结果模板，拼接创建人名称

**请求参数 (HrmPerformanceResultTemplatePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| name | String | 否 | | 结果模板名称，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;HrmPerformanceResultTemplateRespVO&gt;&gt; —— 字段同 2.5

**业务逻辑**:
1. 按名称模糊分页查询结果模板
2. 结果为空时直接返回空分页
3. 批量拼接创建人昵称

### 2.7 获得绩效结果模板精简列表

- **路径**: GET /hrm/performance/result-template/simple-list
- **权限**: `hrm:performance:result-template:query`
- **说明**: 按状态获得结果模板精简列表（供下拉选择）

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| status | Integer | 否 | @RequestParam | 状态，不传时查询全部 |

**响应**: CommonResult&lt;List&lt;HrmPerformanceResultTemplateRespVO&gt;&gt; —— 字段同 2.5

**业务逻辑**:
1. 按状态（可为空）查询结果模板列表
2. VO 转换后返回（不拼接创建人）

---

## 3. 绩效计划

### 3.1 创建绩效计划

- **路径**: POST /hrm/performance/plan/create
- **权限**: `hrm:performance:plan:create`
- **说明**: 创建绩效计划，快照考核/结果模板配置，并按考评范围生成员工绩效考核

**请求参数 (HrmPerformancePlanSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | | 编号（创建时为空） |
| name | String | 是 | @NotBlank、@Size(max=50) | 绩效计划名称 |
| cycleType | Integer | 是 | @NotNull、@InEnum(HrmPerformanceCycleTypeEnum) | 考核周期类型 |
| cycle | String | 否 | @Size(max=255) | 考核周期（如 2026-08） |
| quarter | Integer | 否 | @InEnum(HrmPerformanceQuarterEnum) | 季度 |
| startTime | LocalDateTime | 条件 | 类级校验必填 | 开始日期 |
| endTime | LocalDateTime | 条件 | 类级校验必填且不早于开始日期 | 结束日期 |
| description | String | 否 | @Size(max=200) | 考核说明 |
| scopes | List&lt;Scope&gt; | 是 | @Valid、@NotEmpty、@Size(max=3)、元素 @NotNull | 考评范围列表 |
| assessmentTemplateId | Long | 是 | @NotNull | 考核模板编号 |
| assessmentConfig | AssessmentConfig | 是 | @Valid、@NotNull | 考核配置快照 |
| quotaSettingType | Integer | 是 | @NotNull、@InEnum(HrmPerformanceQuotaSettingTypeEnum) | 指标设置类型 |
| targetConfirmation | Boolean | 是 | @NotNull | 是否需要目标确认 |
| targetConfirmationStage | HandlerStage | 条件 | @Valid | 目标确认节点（需要目标确认且员工自设指标时必填） |
| reviewStages | List&lt;ReviewStage&gt; | 是 | @Valid、@NotEmpty、元素 @NotNull | 评分阶段列表 |
| resultAudit | Boolean | 是 | @NotNull | 是否需要结果审核 |
| resultAuditStages | List&lt;HandlerStage&gt; | 条件 | @Valid、最多 3 个且不重复 | 结果审核节点列表 |
| resultConfirmation | Boolean | 是 | @NotNull | 是否需要结果确认 |
| appealStages | List&lt;HandlerStage&gt; | 条件 | @Valid、最多 3 个且不重复 | 申诉处理节点列表 |
| appealTimeoutDays | Integer | 是 | @NotNull、@Min(1)、@Max(100) | 申诉超期天数 |
| appealTimeoutAction | Integer | 是 | @NotNull、@InEnum(HrmPerformanceAppealTimeoutActionEnum) | 申诉超期处理方式 |
| resultTemplateId | Long | 是 | @NotNull | 结果模板编号 |
| resultConfig | ResultConfig | 是 | @Valid、@NotNull | 结果配置快照 |
| syncToSalary | Boolean | 是 | @NotNull | 是否同步薪资 |
| paidForMonth | String | 条件 | @Size(max=20)、类级校验 syncToSalary=true 时必填且为合法年月 | 计薪月份 |

**Scope（考评范围）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| type | Integer | 是 | @NotNull、@InEnum(HrmPerformancePlanScopeTypeEnum) | 范围类型（指定员工/部门、聘用形式；排除员工类型仅内部维护不可提交） |
| employeeIds | List&lt;Long&gt; | 否 | 元素 @NotNull | 员工编号列表 |
| deptIds | List&lt;Long&gt; | 否 | 元素 @NotNull | 部门编号列表 |
| employeeType | Integer | 否 | @InEnum(HrmEmployeeTypeEnum) | 聘用形式 |
| employeeStatuses | List&lt;Integer&gt; | 否 | @InEnum(HrmEmployeeStatusEnum) | 员工状态列表 |

类级 @AssertTrue 校验（Scope 相关）：指定员工/部门范围时 employeeIds 与 deptIds 不能同时为空；聘用形式范围时 employeeType 与 employeeStatuses 必填；禁止提交排除员工范围。

**HandlerStage（处理节点）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| type | Integer | 是 | @NotNull、@InEnum(HrmPerformanceRaterTypeEnum) | 处理人类型（本人/上级/部门负责人/指定员工） |
| level | Integer | 条件 | @Min(1)、@Max(10) | 上级或部门层级（上级/部门负责人类型必填） |
| employeeId | Long | 条件 | | 指定处理员工编号（指定员工类型必填） |

**ReviewStage（评分阶段）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| name | String | 是 | @NotBlank、@Size(max=50) | 评分阶段名称 |
| rater | HandlerStage | 是 | @Valid、@NotNull | 评分人（不允许配置为本人时允许驳回） |
| weight | BigDecimal | 是 | @NotNull、@DecimalMin(0.01)、@DecimalMax(100) | 评分权重 |
| scoringType | Integer | 是 | @NotNull、@InEnum(HrmPerformanceReviewScoringTypeEnum) | 评分方式 |
| visibleContent | Integer | 是 | @NotNull、@InEnum(HrmPerformanceReviewVisibleContentEnum) | 评分内容可见范围 |
| requiredSetting | Boolean | 是 | @NotNull | 评语是否必填 |
| rejectAuthority | Boolean | 是 | @NotNull | 是否允许驳回 |

类级 @AssertTrue 校验（评分相关）：评分人配置必须合法、评分人不能重复、评分权重总和必须等于 100%、评分人类型为本人时不能允许驳回。
类级 @AssertTrue 校验（周期相关）：startTime/endTime 必填且 endTime 不早于 startTime；自定义周期 cycle 必填且 quarter 为空；月度/季度/上下半年周期时 cycle 与起止日期必须与周期区间精确匹配（季度必须传 quarter）。
类级 @AssertTrue 校验（AssessmentConfig）：同 1.1 的维度/指标权重与名称唯一校验。
类级 @AssertTrue 校验（ResultConfig）：同 2.1 的等级名称唯一与分数区间连续覆盖 0 到 100 分校验。

**响应**: CommonResult&lt;Long&gt; —— 绩效计划编号

**业务逻辑**:
1. 校验计划名称唯一
2. 校验考核模板、结果模板存在且为启用状态
3. 校验计划引用数据：考评范围中的员工与部门、评分/目标确认/结果审核/申诉节点中的指定处理员工必须存在
4. 校验考核模板分数上限不能为空且不大于 100（否则抛出 `1_050_600_007`）
5. 创建计划：从模板快照考核配置与结果配置，状态置为未开始、阶段置为未开始；未开启同步薪资时清空计薪月份
6. 按考评范围解析参评员工（员工/部门范围与聘用形式范围取交集，再排除排除员工），为每个员工创建绩效考核记录
7. 记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_005 | 绩效计划名称已存在 |
| 1_050_600_000 | 绩效考核模板不存在 |
| 1_050_600_002 | 绩效结果模板不存在 |
| 1_050_600_007 | 绩效数据不合法 |

### 3.2 更新绩效计划

- **路径**: PUT /hrm/performance/plan/update
- **权限**: `hrm:performance:plan:update`
- **说明**: 更新计划配置并同步员工考核，仅未开始/草稿状态可修改

**请求参数 (HrmPerformancePlanSaveReqVO)**: 同 3.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 行锁（selectOneForUpdate）查询旧计划并校验可编辑：计划不存在抛 `1_050_600_004`，状态不是草稿/未开始抛 `1_050_600_014`
2. 校验计划名称唯一；考核模板/结果模板未变更时校验存在即可，发生变更时要求为启用状态
3. 校验计划引用数据与考核模板分数上限
4. 更新计划：快照最新模板配置，保留原状态/阶段/操作类型；排除员工范围不由表单提交，需从原计划合并到本次更新数据
5. 按最新考评范围解析参评员工，同步员工绩效考核（删除不再参与的考核、新增新参与员工的考核）
6. 记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_005 | 绩效计划名称已存在 |
| 1_050_600_014 | 绩效计划启动后不能修改计划配置或参评员工 |
| 1_050_600_000 | 绩效考核模板不存在 |
| 1_050_600_002 | 绩效结果模板不存在 |
| 1_050_600_007 | 绩效数据不合法 |

### 3.3 删除绩效计划

- **路径**: DELETE /hrm/performance/plan/delete
- **权限**: `hrm:performance:plan:delete`
- **说明**: 删除绩效计划及其全部员工考核，仅草稿/未开始/已归档状态允许删除

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 计划编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验计划存在；状态不是草稿/未开始/已归档时抛出 `1_050_600_025`
2. 删除计划下全部员工绩效考核及其关联数据（指标评分、动作记录、申诉记录、阶段、指标、维度）
3. 删除绩效计划并记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_025 | 当前状态的绩效计划不允许删除 |

### 3.4 获得绩效计划

- **路径**: GET /hrm/performance/plan/get
- **权限**: `hrm:performance:plan:query`
- **说明**: 按编号获得绩效计划详情，拼接执行进度与可操作节点

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;HrmPerformancePlanRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| name | String | 绩效计划名称 |
| cycleType | Integer | 考核周期类型 |
| cycle | String | 考核周期 |
| quarter | Integer | 季度 |
| startTime | LocalDateTime | 开始日期 |
| endTime | LocalDateTime | 结束日期 |
| description | String | 考核说明 |
| scopes | List&lt;Scope&gt; | 考评范围列表（已过滤内部维护的排除员工范围） |
| assessmentTemplateId | Long | 考核模板编号 |
| assessmentConfig | AssessmentConfig | 考核配置快照 |
| resultTemplateId | Long | 结果模板编号 |
| resultConfig | ResultConfig | 结果配置快照 |
| quotaSettingType | Integer | 指标设置类型 |
| targetConfirmation | Boolean | 是否需要目标确认 |
| targetConfirmationStage | HandlerStage | 目标确认节点 |
| reviewStages | List&lt;ReviewStage&gt; | 评分阶段列表 |
| resultAudit | Boolean | 是否需要结果审核 |
| resultAuditStages | List&lt;HandlerStage&gt; | 结果审核节点列表 |
| resultConfirmation | Boolean | 是否需要结果确认 |
| appealStages | List&lt;HandlerStage&gt; | 申诉处理节点列表 |
| appealTimeoutDays | Integer | 申诉超期天数 |
| appealTimeoutAction | Integer | 申诉超期处理方式 |
| syncToSalary | Boolean | 是否同步薪资 |
| paidForMonth | String | 计薪月份 |
| stageCountMap | Map&lt;Integer, Long&gt; | 各阶段员工数量 |
| stageType | Integer | 阶段状态 |
| status | Integer | 绩效计划状态 |
| operationType | Integer | 当前操作阶段 |
| terminateTime | LocalDateTime | 终止时间 |
| assessmentTemplateName | String | 考核模板名称（从快照拼接） |
| resultTemplateName | String | 结果模板名称（从快照拼接） |
| employeeCount | Integer | 员工数量 |
| finishedCount | Integer | 已完成数量 |
| scoringReady | Boolean | 是否可开始评分 |
| interviewReady | Boolean | 是否可开始面谈 |
| archiveReady | Boolean | 是否可归档 |
| createTime | LocalDateTime | 创建时间 |

**Scope**: type（范围类型）、employeeIds（员工编号列表）、deptIds（部门编号列表）、employeeType（聘用形式）、employeeStatuses（员工状态列表）
**HandlerStage**: type（处理人类型）、level（上级或部门层级）、employeeId（指定处理员工编号）
**ReviewStage**: name（评分阶段名称）、rater（评分人）、weight（评分权重）、scoringType（评分方式）、visibleContent（评分内容可见范围）、requiredSetting（评语是否必填）、rejectAuthority（是否允许驳回）
**AssessmentConfig**: name、scoreCalculation、upperLimitType、upperLimitScore、dimensions（含 quotas）
**ResultConfig**: name、levels（name/minScore/maxScore/coefficient）

**业务逻辑**:
1. 查询绩效计划
2. 查询计划下全部员工考核及各考核的流程阶段
3. 拼接响应：过滤内部维护的排除员工范围；从配置快照回填考核模板/结果模板名称；统计员工数量、已完成（流程结束）数量、各阶段员工数量；计算 scoringReady（运行中且全部考核处于执行中）、interviewReady（全部考核进入结束/结果确认阶段且未处理的结果确认节点齐全）、archiveReady（运行中、下一步操作为归档且全部考核进入结束阶段）

### 3.5 获得绩效计划分页

- **路径**: GET /hrm/performance/plan/page
- **权限**: `hrm:performance:plan:query`
- **说明**: 分页查询绩效计划，拼接执行进度与可操作节点

**请求参数 (HrmPerformancePlanPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| name | String | 否 | | 绩效计划名称 |
| status | Integer | 否 | @InEnum(HrmPerformancePlanStatusEnum) | 绩效计划状态 |
| stageType | Integer | 否 | @InEnum(HrmPerformanceStageTypeEnum) | 阶段状态 |

**响应**: CommonResult&lt;PageResult&lt;HrmPerformancePlanRespVO&gt;&gt; —— 字段同 3.4

**业务逻辑**:
1. 按名称、状态、阶段状态分页查询绩效计划
2. 每条计划拼接员工考核、阶段信息、执行进度与可操作节点（同 3.4 步骤 2-3）

### 3.6 启动绩效计划

- **路径**: POST /hrm/performance/plan/start
- **权限**: `hrm:performance:plan:update`
- **说明**: 启动未开始的绩效计划，按范围补齐参评员工并初始化考核流程

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 行锁查询计划并校验可编辑（仅草稿/未开始可启动）
2. 按考评范围解析并补齐参评员工的绩效考核
3. 启动全部员工考核：校验存在员工考核（否则抛 `1_050_600_007`）；初始化每个考核的指标和流程阶段（指标设置类型为员工自设时初始阶段为填写指标，否则为执行中）
4. 更新计划状态为进行中，并更新阶段与下一步操作类型（初始阶段为执行中时下一步为开启评分）
5. 记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_014 | 绩效计划启动后不能修改计划配置或参评员工（计划不可编辑） |
| 1_050_600_007 | 绩效数据不合法（计划下无员工考核） |
| 1_050_600_011 | 绩效评分流程配置不合法（无法解析出评分阶段） |
| 1_050_600_020 | 绩效目标确认人配置不合法 |
| 1_050_600_026 | 绩效必办节点处理人【{}】未绑定后台账号 |

### 3.7 开启绩效评分

- **路径**: POST /hrm/performance/plan/open-scoring
- **权限**: `hrm:performance:plan:update`
- **说明**: 指标制定/目标确认完成后开启全部员工的评分流程

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验计划存在
2. 校验全部员工考核可以开启评分：计划进行中、存在员工考核且全部考核处于执行中阶段，否则抛出 `1_050_600_018`
3. 初始化每个考核的指标与流程阶段，激活首个评分阶段（不存在可激活的评分阶段时抛 `1_050_600_012`），更新考核的阶段状态并通知评分人
4. 更新计划阶段为首个评分阶段并记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_018 | 指标制定或目标确认尚未全部完成，无法开启评分 |
| 1_050_600_012 | 绩效评分任务不存在 |
| 1_050_600_011 | 绩效评分流程配置不合法 |
| 1_050_600_020 | 绩效目标确认人配置不合法 |
| 1_050_600_026 | 绩效必办节点处理人【{}】未绑定后台账号 |

### 3.8 发起绩效面谈

- **路径**: POST /hrm/performance/plan/start-interview
- **权限**: `hrm:performance:plan:update`
- **说明**: 评分/结果审核全部结束后发起绩效面谈，进入结果确认或结束阶段

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验计划存在
2. 校验全部员工考核可以发起面谈：计划进行中且存在员工考核；未启用结果确认时全部考核须处于结束阶段且下一步操作为发起面谈；启用结果确认时全部考核须处于结果确认阶段且结果审核均已通过，并且每个考核都存在未处理的结果确认节点，否则抛出 `1_050_600_016`
3. 需要员工确认结果时，激活每个考核的结果确认阶段并更新考核阶段状态
4. 更新计划阶段：需要结果确认时进入结果确认阶段，否则进入结束阶段且下一步操作为归档；记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_016 | 绩效结果审核尚未全部完成，无法发起绩效面谈 |

### 3.9 归档绩效计划

- **路径**: POST /hrm/performance/plan/archive
- **权限**: `hrm:performance:plan:update`
- **说明**: 面谈/申诉全部结束后归档绩效计划与全部员工考核

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验计划存在
2. 校验全部员工考核可以归档：计划进行中、下一步操作为归档、存在员工考核且全部考核处于结束阶段，否则抛出 `1_050_600_017`
3. 归档全部员工考核：状态置为已归档、流程状态置为已结束、阶段置为归档，记录归档时间
4. 归档绩效计划并记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_017 | 绩效面谈或申诉尚未全部结束，无法归档 |

### 3.10 终止绩效计划

- **路径**: POST /hrm/performance/plan/terminate
- **权限**: `hrm:performance:plan:update`
- **说明**: 终止运行中的绩效计划，保留全部流程历史

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验计划存在且状态为进行中，否则抛出 `1_050_600_008`
2. 按当前登录用户查找对应的员工档案（可为空）
3. 终止计划下全部员工考核：状态置为已终止、流程状态置为已结束，并写入终止动作记录（保留流程快照）
4. 更新计划状态为已终止、清空下一步操作并记录终止时间
5. 记录操作日志（LogRecord）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作（仅运行中计划允许终止） |

### 3.11 获得绩效计划状态统计

- **路径**: GET /hrm/performance/plan/status-count
- **权限**: `hrm:performance:plan:query`
- **说明**: 按查询条件（不含状态）统计各状态的绩效计划数量

**请求参数 (HrmPerformancePlanPageReqVO)**: 同 3.5（status 不参与统计过滤）

**响应**: CommonResult&lt;Map&lt;Integer, Long&gt;&gt; —— 状态 -> 计划数量

**业务逻辑**:
1. 复用分页查询条件（名称、阶段状态）按状态分组统计计划数量
2. 返回状态到数量的 Map

### 3.12 获得绩效计划阶段统计

- **路径**: GET /hrm/performance/plan/stage-count
- **权限**: `hrm:performance:plan:query`
- **说明**: 统计指定绩效计划下员工考核在各阶段的数量

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| planId | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;List&lt;HrmPerformancePlanStageCountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| stageType | Integer | 阶段状态 |
| count | Long | 数量 |

**业务逻辑**:
1. 校验绩效计划存在
2. 查询计划下全部员工考核，按阶段类型分组统计数量（仅统计阶段类型非空的考核）
3. 按阶段类型枚举顺序转换响应，只返回数量大于 0 的阶段

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |

### 3.13 获得绩效结果等级统计

- **路径**: GET /hrm/performance/plan/level-count
- **权限**: `hrm:performance:plan:query`
- **说明**: 按结果模板等级顺序统计指定计划下各绩效等级的人数

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| planId | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;List&lt;HrmPerformancePlanResultLevelCountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| levelName | String | 等级名称 |
| count | Long | 数量 |

**业务逻辑**:
1. 查询绩效计划，计划不存在时返回空列表
2. 查询计划下全部员工考核
3. 按结果配置快照中的等级顺序初始化全部等级（初始人数 0），再累计考核结果等级（非空）的实际人数

---

## 4. 员工绩效考核与归档

### 4.1 添加员工绩效考核

- **路径**: POST /hrm/performance/assessment/create-list
- **权限**: `hrm:performance:plan:update`
- **说明**: 向未开始的绩效计划手工添加参评员工并生成考核记录

**请求参数 (HrmPerformanceAssessmentBatchReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| planId | Long | 是 | @NotNull | 绩效计划编号 |
| employeeIds | List&lt;Long&gt; | 是 | @NotEmpty | 员工编号列表 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 行锁查询计划并校验可编辑（仅草稿/未开始可修改）
2. 校验员工编号列表对应的员工存在
3. 更新计划考评范围：手工加入的员工写入普通员工范围，并从排除员工范围移除
4. 添加员工绩效考核：跳过已参与计划的员工；运行中的计划同步初始化新员工的考核指标

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_014 | 绩效计划启动后不能修改计划配置或参评员工 |
| 1_050_100_000 | 员工档案不存在 |

### 4.2 移除员工绩效考核

- **路径**: DELETE /hrm/performance/assessment/delete-list
- **权限**: `hrm:performance:plan:update`
- **说明**: 从未开始的绩效计划移除参评员工并删除其考核记录

**请求参数 (HrmPerformanceAssessmentBatchReqVO)**: 同 4.1

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 行锁查询计划并校验可编辑；员工编号为空时直接返回
2. 校验员工编号列表对应的员工存在
3. 更新计划考评范围：从普通员工范围移除，并记录到排除员工范围（避免按部门/聘用形式范围再次加入）
4. 删除对应员工的绩效考核及其关联数据

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_014 | 绩效计划启动后不能修改计划配置或参评员工 |
| 1_050_100_000 | 员工档案不存在 |

### 4.3 获得员工绩效考核分页

- **路径**: GET /hrm/performance/assessment/page
- **权限**: `hrm:performance:plan:query`
- **说明**: 分页查询员工绩效考核，拼接计划/员工/部门/维度/指标/阶段/评分信息与当前用户处理权限

**请求参数 (HrmPerformanceAssessmentPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| planId | Long | 否 | | 绩效计划编号 |
| employeeId | Long | 否 | | 员工编号 |
| employeeIds | List&lt;Long&gt; | 否 | | 员工编号列表 |
| search | String | 否 | | 员工姓名或工号 |
| deptId | Long | 否 | | 部门编号 |
| employeeType | Integer | 否 | | 聘用形式 |
| employeeStatus | Integer | 否 | | 员工状态 |
| status | Integer | 否 | @InEnum(HrmPerformancePlanStatusEnum) | 考核状态 |
| stageType | Integer | 否 | @InEnum(HrmPerformanceStageTypeEnum) | 阶段状态 |
| appealStatus | Integer | 否 | @InEnum(HrmPerformanceAppealStatusEnum) | 申诉状态 |
| resultLevel | String | 否 | | 结果等级 |
| resultLevelEmpty | Boolean | 否 | | 结果等级是否为空 |

**响应**: CommonResult&lt;PageResult&lt;HrmPerformanceAssessmentRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| planId | Long | 绩效计划编号 |
| name | String | 绩效计划名称 |
| cycleType | Integer | 考核周期类型 |
| cycle | String | 考核周期 |
| startTime | LocalDateTime | 开始日期 |
| endTime | LocalDateTime | 结束日期 |
| upperLimitScore | BigDecimal | 单项评分上限 |
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| mobile | String | 手机号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| employeeType | Integer | 聘用形式 |
| employeeStatus | Integer | 员工状态 |
| currentHandlerName | String | 当前处理人 |
| status | Integer | 考核状态 |
| processStatus | Integer | 激活状态 |
| stageType | Integer | 阶段状态 |
| stageSort | Integer | 阶段排序 |
| score | BigDecimal | 得分 |
| resultLevel | String | 结果等级 |
| coefficient | BigDecimal | 绩效系数 |
| targetConfirmationEmployeeName | String | 目标确认员工姓名 |
| targetConfirmationResult | Integer | 目标确认结果 |
| targetConfirmationComment | String | 目标确认意见 |
| targetConfirmationTime | LocalDateTime | 目标确认时间 |
| canConfirmTarget | Boolean | 是否可确认目标 |
| selfComment | String | 自评说明 |
| reviewerComment | String | 评分人说明 |
| resultComment | String | 结果说明 |
| resultConfirmationTime | LocalDateTime | 结果确认时间 |
| resultAuditStatus | Integer | 结果审核状态 |
| resultAuditTime | LocalDateTime | 结果审核时间 |
| resultAuditReason | String | 结果审核意见 |
| appealReason | String | 申诉原因 |
| appealFileUrls | List&lt;String&gt; | 申诉附件地址列表 |
| appealReviewStageIds | List&lt;Long&gt; | 申诉退回评分阶段编号列表 |
| appealSubmitTime | LocalDateTime | 申诉提交时间 |
| appealStatus | Integer | 申诉状态 |
| appealTime | LocalDateTime | 申诉处理时间 |
| appealComment | String | 申诉处理意见 |
| archiveTime | LocalDateTime | 归档时间 |
| createTime | LocalDateTime | 创建时间 |
| dimensions | List&lt;DimensionRespVO&gt; | 指标维度列表 |
| quotas | List&lt;QuotaRespVO&gt; | 指标列表 |
| reviewStages | List&lt;StageRespVO&gt; | 评分阶段列表 |
| currentReviewStage | StageRespVO | 当前评分阶段 |
| stages | List&lt;StageRespVO&gt; | 运行阶段列表 |
| currentStage | StageRespVO | 当前待处理阶段 |

**DimensionRespVO**: id、assessmentId、name（维度名称）、quotaType（指标类型）、weight（维度权重）、remark（备注）、allowEdit（是否允许编辑）、sort（排序）
**QuotaRespVO**: id、assessmentId、dimensionId、dimensionName（维度名称）、dimensionWeight（维度权重）、allowEdit、preset（预设值）、name（指标名称）、description（指标说明）、standard（标准值）、weight（指标权重）、scoreType（分数类型）、targetValue（目标值）、actualValue（实际值）、selfScore（自评分数）、reviewerScore（评分人得分）、finalScore（最终得分）、comment（说明）、sort（排序）
**StageRespVO**: id、assessmentId、type（阶段类型）、handlerEmployeeId（处理员工编号）、handlerName（处理人姓名）、name（阶段名称）、raterType（评分人类型）、weight（权重）、scoringType（评分类型）、visibleContent（可见内容）、requiredSetting（是否必填）、rejectAuthority（驳回权限）、sort（排序）、status（阶段状态）、score（得分）、resultLevel（结果等级）、comment（说明）、rejectReason（驳回原因）、submitTime（提交时间）、deadlineTime（截止时间）、canHandle（是否可处理）、canScore（是否可评分）、quotaScoreList（指标评分列表）
**QuotaScoreRespVO**: id、assessmentStageId（员工评分阶段编号）、assessmentQuotaId（员工绩效指标编号）、score（得分）、comment（说明）

**业务逻辑**:
1. 请求包含员工姓名/工号、部门、聘用形式或员工状态条件时，先查询符合条件的员工列表；无匹配员工时返回空分页，否则以员工编号列表过滤考核
2. 按条件分页查询员工绩效考核
3. 批量拼接响应：绩效计划信息（名称、周期、起止时间、单项评分上限）、员工与部门信息、指标维度、指标（含维度名称/权重）、流程阶段与各阶段指标评分
4. 分页场景不标记当前用户处理权限（canHandle/canScore 固定为 false）

### 4.4 获得未加入指定绩效计划的员工编号列表

- **路径**: GET /hrm/performance/assessment/unassigned-employee-id-list
- **权限**: `hrm:performance:plan:query`
- **说明**: 查询尚未参与指定绩效计划的全部员工编号

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| planId | Long | 是 | @RequestParam | 绩效计划编号 |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt; —— 员工编号列表

**业务逻辑**:
1. 校验绩效计划存在
2. 查询已参与计划的员工考核，得到已参评员工编号集合
3. 查询全部员工，过滤出尚未参与计划的员工编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_004 | 绩效计划不存在 |

### 4.5 获得员工绩效考核

- **路径**: GET /hrm/performance/assessment/get
- **权限**: `hrm:performance:plan:query`
- **说明**: 按编号获得员工绩效考核详情，标记当前登录用户的处理/评分权限并按可见范围过滤评分内容

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 员工绩效考核编号 |

**响应**: CommonResult&lt;HrmPerformanceAssessmentRespVO&gt; —— 字段同 4.3

**业务逻辑**:
1. 按编号查询员工绩效考核
2. 拼接完整响应（计划、员工、部门、维度、指标、阶段、评分）
3. 查询待处理申诉记录并按当前登录用户标记各阶段处理/评分权限：当前处理人可处理（评分阶段可评分）、本人可确认目标、申诉确认节点回填可退回的评分阶段
4. 当前用户命中某个评分阶段且该阶段评分内容可见范围受限时，仅保留本人评分阶段并清空自评/评分人评分、最终得分与评语

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_600_006 | 员工绩效考核不存在（前端按 id 查询前可自行校验） |

### 4.6 获得绩效流程记录列表

- **路径**: GET /hrm/performance/assessment/process-record-list
- **权限**: `hrm:performance:plan:query`
- **说明**: 获得员工绩效考核的追加式流程动作记录时间线

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 员工绩效考核编号 |

**响应**: CommonResult&lt;List&lt;HrmPerformanceProcessRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| title | String | 标题 |
| content | String | 内容 |
| source | String | 来源（固定 ACTION，动作记录） |
| status | Integer | 绩效流程记录状态 |
| operatorName | String | 操作人姓名 |
| operateTime | LocalDateTime | 操作时间 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |

**业务逻辑**:
1. 按编号查询员工绩效考核
2. 查询该考核的全部追加式动作记录
3. 批量查询操作人员工信息并拼接操作人姓名
4. 转换为流程记录响应并按操作时间升序排序（空值置后）

### 4.7 获得绩效归档分页

- **路径**: GET /hrm/performance/assessment/archive-page
- **权限**: `hrm:performance:archive:query`
- **说明**: 分页查询已归档的员工绩效考核

**请求参数 (HrmPerformanceArchivePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| planId | Long | 否 | | 绩效计划编号 |
| employeeId | Long | 否 | | 员工编号 |
| employeeIds | List&lt;Long&gt; | 否 | | 员工编号列表 |

**响应**: CommonResult&lt;PageResult&lt;HrmPerformanceAssessmentRespVO&gt;&gt; —— 字段同 4.3

**业务逻辑**:
1. 按条件分页查询状态为已归档的员工绩效考核
2. 拼接完整响应（同 4.3 步骤 3）

### 4.8 获得员工绩效档案分页

- **路径**: GET /hrm/performance/assessment/archive-employee-page
- **权限**: `hrm:performance:archive:query`
- **说明**: 按员工维度分页查询绩效档案（员工信息 + 归档考核汇总）

**请求参数 (HrmPerformanceArchiveEmployeePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| search | String | 否 | | 员工姓名或工号，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;HrmPerformanceArchiveEmployeeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| mobile | String | 手机号码 |
| employeeStatus | Integer | 员工状态 |
| employeeType | Integer | 聘用形式 |
| latestAssessmentId | Long | 最近考核编号 |
| latestPlanName | String | 最近考核计划 |
| latestScore | BigDecimal | 最近绩效评分 |
| latestResultLevel | String | 最近绩效等级 |
| assessmentCount | Long | 考核次数 |

**业务逻辑**:
1. 按姓名/工号模糊分页查询员工
2. 批量查询员工的已归档考核、绩效计划与部门信息
3. 拼接响应：员工基础信息、部门名称、归档考核次数；最近一次归档考核的编号、评分、结果等级与所属计划名称

### 4.9 获得绩效归档详情

- **路径**: GET /hrm/performance/assessment/archive-get
- **权限**: `hrm:performance:archive:query`
- **说明**: 按编号获得已归档的员工绩效考核详情

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 员工绩效考核编号 |

**响应**: CommonResult&lt;HrmPerformanceAssessmentRespVO&gt; —— 字段同 4.3

**业务逻辑**:
1. 按编号查询员工绩效考核，考核不存在或状态不是已归档时返回 null
2. 拼接完整响应（同 4.3 步骤 3，不标记处理权限）

### 4.10 获得绩效归档流程记录列表

- **路径**: GET /hrm/performance/assessment/archive-process-record-list
- **权限**: `hrm:performance:archive:query`
- **说明**: 获得已归档员工绩效考核的流程记录时间线

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam | 员工绩效考核编号 |

**响应**: CommonResult&lt;List&lt;HrmPerformanceProcessRecordRespVO&gt;&gt; —— 字段同 4.6

**业务逻辑**:
1. 查询已归档的员工绩效考核
2. 查询该考核的全部追加式动作记录并拼接操作人姓名
3. 按操作时间升序排序返回

### 4.11 获得绩效归档计划精简列表

- **路径**: GET /hrm/performance/assessment/archive-plan-simple-list
- **权限**: `hrm:performance:archive:query`
- **说明**: 获得存在归档考核的绩效计划精简列表（供归档筛选）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmPerformancePlanRespVO&gt;&gt;（仅含 id、name 字段）

**业务逻辑**:
1. 查询状态为已归档的全部员工考核，按计划编号去重（保持顺序）
2. 查询对应的绩效计划
3. 转换为仅含编号与名称的精简响应

### 4.12 删除绩效归档记录

- **路径**: DELETE /hrm/performance/assessment/archive-delete
- **权限**: `hrm:performance:archive:delete`
- **说明**: 按编号列表删除已归档的绩效考核记录及其关联数据

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| ids | List&lt;Long&gt; | 是 | @RequestParam、@NotEmpty | 绩效归档记录编号列表，如 1024,1025 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 仅查询编号中状态为已归档的员工考核
2. 删除考核及其全部关联数据：阶段指标评分、动作记录、申诉记录、流程阶段、考核指标、考核维度、考核本体

### 4.13 删除员工的全部绩效档案

- **路径**: DELETE /hrm/performance/assessment/archive-employee-delete
- **权限**: `hrm:performance:archive:delete`
- **说明**: 按员工编号列表删除其全部已归档绩效考核

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| employeeIds | List&lt;Long&gt; | 是 | @RequestParam、@NotEmpty | 员工编号列表，如 1024,1025 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 查询指定员工状态为已归档的全部员工考核
2. 删除考核及其全部关联数据（同 4.12 步骤 2）

---

## 附：绩效域错误码总表（1_050_600_XXX）

| 错误码 | 说明 |
|-------|------|
| 1_050_600_000 | 绩效考核模板不存在 |
| 1_050_600_001 | 绩效考核模板名称已存在 |
| 1_050_600_002 | 绩效结果模板不存在 |
| 1_050_600_003 | 绩效结果模板名称已存在 |
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_005 | 绩效计划名称已存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_007 | 绩效数据不合法 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_009 | 绩效流程处理中，不能修改当前记录 |
| 1_050_600_011 | 绩效评分流程配置不合法 |
| 1_050_600_012 | 绩效评分任务不存在 |
| 1_050_600_013 | 当前用户不是该绩效阶段的评分人 |
| 1_050_600_014 | 绩效计划启动后不能修改计划配置或参评员工 |
| 1_050_600_015 | 当前绩效评分阶段不能驳回上一阶段 |
| 1_050_600_016 | 绩效结果审核尚未全部完成，无法发起绩效面谈 |
| 1_050_600_017 | 绩效面谈或申诉尚未全部结束，无法归档 |
| 1_050_600_018 | 指标制定或目标确认尚未全部完成，无法开启评分 |
| 1_050_600_019 | 绩效指标制定数据不合法 |
| 1_050_600_020 | 绩效目标确认人配置不合法 |
| 1_050_600_021 | 当前用户不是该绩效目标的确认人 |
| 1_050_600_024 | 绩效流程配置不合法 |
| 1_050_600_025 | 当前状态的绩效计划不允许删除 |
| 1_050_600_026 | 绩效必办节点处理人【{}】未绑定后台账号 |
| 1_050_600_027 | 当前用户不是该绩效阶段的处理人 |
| 1_050_600_028 | 绩效总分未匹配到结果等级，请检查绩效结果模板 |
