# AI 思维导图接口 (AiMindMapController)

> 提供 AI 思维导图的流式生成（SSE）与生成记录的管理（查询、删除），生成结果基于 AI 对话模型按提示词输出思维导图内容。

## 接口路径前缀

/ai/mind-map  (Controller: AiMindMapController)

## 1. 导图生成

### 1.1 导图生成（流式）

- **路径**: POST /ai/mind-map/generate-stream（响应类型 text/event-stream，SSE 流式返回）
- **权限**: 已认证（仅登录，无 @PreAuthorize 权限标识，内部通过 getLoginUserId() 取当前用户）
- **说明**: 根据提示词调用 AI 对话模型流式生成思维导图内容，并保存生成记录

**请求参数 (AiMindMapGenerateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| prompt | String | 是 | @NotBlank | 思维导图内容提示，如「Java 学习路线」 |

**响应**: Flux<CommonResult<String>>（SSE 流，每个 chunk 为一段增量生成文本；出错时返回错误码 chunk）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | String | 流式返回的思维导图内容增量片段（Markdown 格式，由模型生成） |

**业务逻辑**:
1. 获取导图模型：按名称查找「思维导图助手」角色（AiChatRoleEnum.AI_MIND_MAP_ROLE），若角色存在且配置了 modelId 则使用该模型，否则获取默认的 CHAT 类型模型；校验模型存在且类型为 CHAT，否则抛出 MODEL_NOT_EXISTS / MODEL_USE_TYPE_ERROR。
2. 确定系统提示词：优先取「思维导图助手」角色的 systemMessage，角色不存在或为空时使用内置的导图角色提示词。
3. 校验模型平台合法性（AiPlatformEnum.validatePlatform），并按模型 ID 获取对应平台的 ChatModel 实例。
4. 将请求插入 ai_mind_map 记录，保存 userId、prompt、platform、modelId、model 等信息。
5. 构建 Prompt（SystemMessage 角色设定 + UserMessage 用户提示词），并按平台构建 ChatOptions（temperature、maxTokens），流式调用模型。
6. 流式返回每个 chunk 的增量文本给前端，同时在内存中累积完整内容；流结束时忽略租户上下文（Flux 异步无法透传租户），将完整生成内容更新回记录的 generatedContent。
7. 调用发生异常时，将异常信息写入记录的 errorMessage，并向前端返回 WRITE_STREAM_ERROR 错误。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_001_000 | 模型不存在!（MODEL_NOT_EXISTS） |
| 1_040_001_002 | 操作失败，找不到默认模型（MODEL_DEFAULT_NOT_EXISTS） |
| 1_040_001_003 | 操作失败，该模型的模型类型不正确（MODEL_USE_TYPE_ERROR） |
| 1_040_07_001 | 写作生成异常!（WRITE_STREAM_ERROR，流式生成出错时返回） |

## 2. 导图管理

### 2.1 删除思维导图

- **路径**: DELETE /ai/mind-map/delete
- **权限**: ai:mind-map:delete
- **说明**: 删除指定编号的思维导图记录

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 思维导图编号 |

**响应**: CommonResult<Boolean>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**:
1. 校验思维导图记录存在，不存在则抛出 MIND_MAP_NOT_EXISTS。
2. 删除该思维导图记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_008_000 | 思维导图不存在!（MIND_MAP_NOT_EXISTS） |

### 2.2 获得思维导图

- **路径**: GET /ai/mind-map/get
- **权限**: ai:mind-map:query
- **说明**: 获得指定编号的思维导图详情

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 思维导图编号 |

**响应**: CommonResult<AiMindMapRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| prompt | String | 生成内容提示 |
| generatedContent | String | 生成的思维导图内容 |
| platform | String | 平台，如 OpenAI |
| model | String | 模型，如 gpt-3.5-turbo-0125 |
| errorMessage | String | 错误信息 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询思维导图记录并转换为 RespVO 返回（记录不存在时返回 null 数据，不抛错）。

### 2.3 获得思维导图分页

- **路径**: GET /ai/mind-map/page
- **权限**: ai:mind-map:query
- **说明**: 分页获得思维导图记录列表

**请求参数 (AiMindMapPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| userId | Long | 否 | 无 | 用户编号 |
| prompt | String | 否 | 无 | 生成内容提示 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult<PageResult<AiMindMapRespVO>>（list 内元素字段同 2.2 的 AiMindMapRespVO）

**业务逻辑**:
1. 按查询条件（用户编号、提示词、创建时间范围）分页查询思维导图记录，转换为 RespVO 分页结果返回。
