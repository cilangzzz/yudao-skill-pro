# AI 工作流接口 (AiWorkflowController)

> 提供 AI 工作流（基于 TinyFlow 执行引擎）的管理能力：工作流配置的增删改查、分页查询，以及基于 graph 模型 JSON 的工作流测试执行。

## 接口路径前缀

/ai/workflow  (Controller: AiWorkflowController)

## 1. 工作流配置管理

### 1.1 创建 AI 工作流

- **路径**: POST /ai/workflow/create
- **权限**: ai:workflow:create
- **说明**: 创建一个新的 AI 工作流配置，工作流标识（code）全局唯一。

**请求参数 (AiWorkflowSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 否 | - | 编号（创建时无需传递） |
| code | String | 是 | @NotEmpty | 工作流标识，全局唯一，如 FLOW |
| name | String | 是 | @NotEmpty | 工作流名称 |
| remark | String | 否 | - | 备注 |
| graph | String | 是 | @NotEmpty | 工作流模型（流程图 JSON 字符串） |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum：0 开启 / 1 禁用） |

**响应**: CommonResult<Long>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| data | Long | 新创建的工作流编号 |

**业务逻辑**:
1. 校验工作流标识 code 是否为空，非空时按 code 查询数据库，若已存在则抛出"工作流标识已存在"异常。
2. 将 SaveReqVO 转换为 AiWorkflowDO 实体。
3. 插入工作流配置记录，返回自增主键 id。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1-040-011-001 | 工作流标识已存在 |

### 1.2 更新 AI 工作流

- **路径**: PUT /ai/workflow/update
- **权限**: ai:workflow:update
- **说明**: 更新已有 AI 工作流的配置信息，更新时同样校验标识唯一性。

**请求参数 (AiWorkflowSaveReqVO)**: 同 1.1，其中 id 必传（用于定位待更新记录）。

**响应**: CommonResult<Boolean>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| data | Boolean | 固定返回 true 表示更新成功 |

**业务逻辑**:
1. 校验工作流是否存在（id 为空或数据库中查不到均抛出"工作流不存在"异常）。
2. 校验工作流标识 code 唯一性：按 code 查询，若存在其他记录（id 不同）占用该标识则抛出异常。
3. 将 SaveReqVO 转换为 AiWorkflowDO，按 id 更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1-040-011-000 | 工作流不存在 |
| 1-040-011-001 | 工作流标识已存在 |

### 1.3 删除 AI 工作流

- **路径**: DELETE /ai/workflow/delete
- **权限**: ai:workflow:delete
- **说明**: 根据编号删除指定的工作流配置。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @RequestParam required | 工作流编号 |

**响应**: CommonResult<Boolean>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| data | Boolean | 固定返回 true 表示删除成功 |

**业务逻辑**:
1. 校验工作流是否存在，不存在则抛出"工作流不存在"异常。
2. 按主键删除工作流配置记录（逻辑删除）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1-040-011-000 | 工作流不存在 |

### 1.4 获得 AI 工作流

- **路径**: GET /ai/workflow/get
- **权限**: ai:workflow:query
- **说明**: 根据编号查询单个工作流配置详情。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @RequestParam required | 工作流编号，示例 1024 |

**响应**: CommonResult<AiWorkflowRespVO>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| id | Long | 编号 |
| code | String | 工作流标识 |
| name | String | 工作流名称 |
| remark | String | 备注 |
| status | Integer | 状态（0 开启 / 1 禁用） |
| graph | String | 工作流模型 JSON |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按主键查询 AiWorkflowDO（未命中时返回 null，不做存在性校验）。
2. 通过 BeanUtils 将 DO 转换为 AiWorkflowRespVO 返回。

### 1.5 获得 AI 工作流分页

- **路径**: GET /ai/workflow/page
- **权限**: ai:workflow:query
- **说明**: 分页查询工作流列表，支持名称、标识、状态、创建时间等条件过滤。

**请求参数 (AiWorkflowPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| pageNo | Integer | 否 | - | 页码（PageParam 默认值 1） |
| pageSize | Integer | 否 | - | 每页条数（PageParam 默认值 10） |
| name | String | 否 | - | 名称，模糊匹配 |
| code | String | 否 | - | 标识，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult<PageResult<AiWorkflowRespVO>>，列表项字段同 1.4 响应表。

**业务逻辑**:
1. 将分页查询条件透传给 AiWorkflowMapper 执行 selectPage。
2. 将 PageResult<AiWorkflowDO> 转换为 PageResult<AiWorkflowRespVO> 返回。

### 1.6 测试 AI 工作流

- **路径**: POST /ai/workflow/test
- **权限**: ai:workflow:test
- **说明**: 按传入的 graph（或已保存工作流的 graph）构建 TinyFlow 执行链并试运行，返回执行结果。

**请求参数 (AiWorkflowTestReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 与 graph 二选一 | @AssertTrue(isGraphValid) | 工作流编号，从数据库加载 graph |
| graph | String | 与 id 二选一 | @AssertTrue(isGraphValid) | 工作流模型 JSON，直接测试未保存的流程 |
| params | Map&lt;String, Object&gt; | 是 | - | 执行时传入的流程变量 |

> 类级校验 `@AssertTrue`（isGraphValid 方法）：id 与 graph 必须至少传递一个。

**响应**: CommonResult<Object>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| data | Object | TinyFlow 执行结果（executeForResult 输出） |

**业务逻辑**:
1. 确定 graph 来源：请求中传了 graph 则直接使用；否则按 id 校验工作流存在并读取其已保存的 graph。
2. 解析 graph JSON，创建 Tinyflow 实例。
3. 遍历 nodes 节点数组：对 `llmNode` 类型节点，按 data.llmId 调用 AiModelService 获取对应的 LLM Provider 并注册到 Tinyflow；`internalNode` 等其他类型暂不处理。
4. 以请求中的 params 作为流程变量，调用 tinyflow.toChain().executeForResult(variables) 执行流程并返回结果。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1-040-011-000 | 工作流不存在（按 id 加载 graph 时） |
