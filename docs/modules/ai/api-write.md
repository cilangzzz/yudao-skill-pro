# AI 写作接口 (AiWriteController)

> 提供 AI 写作生成（撰写文章 / 回复内容）的流式输出，以及写作记录的管理（分页查询、详情、删除）。

## 接口路径前缀

/ai/write  (Controller: AiWriteController)

## 1. 写作生成

### 1.1 写作生成（流式）

- **路径**: POST /ai/write/generate-stream（produces = text/event-stream）
- **权限**: 已认证（仅要求登录，无 @PreAuthorize 权限标识）
- **说明**: 流式（SSE）返回 AI 写作生成结果，响应较快；同时将本次写作记录落库，生成完成后回写生成内容，异常时回写错误信息。

**请求参数 (AiWriteGenerateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @InEnum(AiWriteTypeEnum) | 写作类型：1 撰写、2 回复 |
| prompt | String | 否 | 无 | 写作内容提示（撰写时为文章主题；回复时为回复参考内容），示例：`1.撰写：田忌赛马；2.回复：不批` |
| originalContent | String | 否 | 无 | 原文（写作类型为「回复」时使用），示例：`领导我要辞职` |
| length | Integer | 是 | @NotNull | 长度（字典 AI_WRITE_LENGTH） |
| format | Integer | 是 | @NotNull | 格式（字典 AI_WRITE_FORMAT） |
| tone | Integer | 是 | @NotNull | 语气（字典 AI_WRITE_TONE） |
| language | Integer | 是 | @NotNull | 语言（字典 AI_WRITE_LANGUAGE） |

**响应**: Flux&lt;CommonResult&lt;String&gt;&gt;，每个流式分片为一段增量生成文本（data 为字符串片段，非 VO 对象）。

**业务逻辑**:
1. 尝试按名称获取「写作助手」聊天角色（AiChatRoleEnum.AI_WRITE_ROLE）；若角色配置了模型则使用该模型，否则回退到系统默认的 CHAT 类型模型；角色未设置 systemMessage 时使用枚举内置的角色设定。
2. 校验模型平台（AiPlatformEnum.validatePlatform），并获取对应的流式 ChatModel；若模型不存在抛 MODEL_NOT_EXISTS，模型类型非 CHAT 抛 MODEL_USE_TYPE_ERROR。
3. 将请求参数转换为 AiWriteDO（补充 userId、platform、modelId、model 字段）插入数据库，形成写作记录。
4. 构建 Prompt：SystemMessage 为角色设定；UserMessage 按写作类型套用模板（撰写模板使用 prompt，回复模板使用 originalContent + prompt），并将 format/tone/language/length 字典值翻译为中文标签后填入模板。
5. 通过 ChatOptions（平台、模型名、temperature、maxTokens）发起流式调用，逐片将增量文本以 CommonResult.success 返回。
6. 流结束后（doOnComplete）忽略租户上下文，将累计的完整生成内容回写到写作记录的 generatedContent 字段。
7. 流发生异常（doOnError）时记录错误日志，忽略租户上下文将异常信息回写到 errorMessage 字段，并向前端返回 WRITE_STREAM_ERROR 错误。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_001_000 | 模型不存在! |
| 1_040_001_003 | 操作失败，该模型的模型类型不正确 |
| 1_040_07_001 | 写作生成异常! |

## 2. 写作管理

### 2.1 删除写作

- **路径**: DELETE /ai/write/delete
- **权限**: ai:write:delete
- **说明**: 根据 id 删除一条写作记录。

**请求参数**: 无（Query 参数 `id`，Long，必填，写作记录编号）

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true。

**业务逻辑**:
1. 校验写作记录存在，不存在则抛 WRITE_NOT_EXISTS。
2. 根据主键删除该条写作记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_007_000 | 作文不存在! |

### 2.2 获得写作

- **路径**: GET /ai/write/get
- **权限**: ai:write:query
- **说明**: 根据 id 获取写作记录详情。

**请求参数**: 无（Query 参数 `id`，Long，必填，写作记录编号）

**响应**: CommonResult&lt;AiWriteRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| type | Integer | 写作类型：1 撰写、2 回复 |
| platform | String | 平台，示例：TongYi |
| model | String | 模型，示例：qwen |
| prompt | String | 生成内容提示 |
| generatedContent | String | 生成的内容 |
| originalContent | String | 原文 |
| length | Integer | 长度提示词 |
| format | Integer | 格式提示词 |
| tone | Integer | 语气提示词 |
| language | Integer | 语言提示词 |
| errorMessage | String | 错误信息 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 根据主键查询写作记录（不存在时返回 null，不抛异常）。
2. 将 AiWriteDO 转换为 AiWriteRespVO 返回。

### 2.3 获得写作分页

- **路径**: GET /ai/write/page
- **权限**: ai:write:query
- **说明**: 分页查询写作记录列表。

**请求参数 (AiWritePageReqVO)**: 继承 PageParam（pageNo 页码、pageSize 每页条数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 继承 PageParam | 页码，默认 1 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数，默认 10 |
| userId | Long | 否 | 无 | 用户编号 |
| type | Integer | 否 | 无 | 写作类型 |
| platform | String | 否 | 无 | 平台，示例：TongYi |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;AiWriteRespVO&gt;&gt;，list 元素结构同 2.2 的 AiWriteRespVO 字段表。

**业务逻辑**:
1. 按请求条件（userId、type、platform、createTime 区间）分页查询写作记录。
2. 将 PageResult&lt;AiWriteDO&gt; 转换为 PageResult&lt;AiWriteRespVO&gt; 返回。
