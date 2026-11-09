# 数据模型详情

> ai 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

## 1. 实体继承体系

ai 模块全部 15 个 DO 位于 `cn.iocoder.yudao.module.ai.dal.dataobject` 下，按业务域分为 chat / knowledge / model / image / music / mindmap / write / workflow / requestlog 九个包，**全部直接继承框架的 BaseDO，无一使用 TenantBaseDO**：

```text
Serializable + TransPojo（Easy-Trans 数据翻译接口）
│
└── BaseDO（yudao-spring-boot-starter-mybatis，cn.iocoder.yudao.framework.mybatis.core.dataobject）
    ├── creator      String          创建者，SysUser 的 userId（INSERT 自动填充）
    ├── createTime   LocalDateTime   创建时间（INSERT 自动填充）
    ├── updater      String          更新者（INSERT_UPDATE 自动填充）
    ├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 自动填充）
    ├── deleted      Boolean         逻辑删除标记（@TableLogic，查询自动过滤已删除数据）
    │
    └── TenantBaseDO（yudao-spring-boot-starter-biz-tenant，cn.iocoder.yudao.framework.tenant.core.db）
        └── tenantId  Long            多租户编号
```

使用规则：

- ai 模块所有 DO 只继承 BaseDO，即 AI 业务表均不含 `tenant_id` 字段，不做多租户隔离。虽然模块 pom 依赖了 `yudao-spring-boot-starter-biz-tenant`，但表设计采用「平台级配置共享 + userId 数据归属」模式。
- 配置类数据（ApiKey / Model / 公开 Role / Tool / Workflow / Knowledge）全局共享；用户创作类数据（Conversation / Message / Image / Music / MindMap / Write）通过 `userId` 字段归属到用户，绘画、音乐、角色三张表额外用 `publicStatus` 控制是否公开。
- BaseDO 的四个审计字段由 MyBatis-Plus 的 `MetaObjectHandler` 自动填充，业务代码不要手工赋值；`deleted` 走逻辑删除，做唯一性判断时需注意已删除数据的影响。
- 特别注意：Midjourney 回调端点 `/ai/image/midjourney/notify` 是 `@PermitAll` + `@TenantIgnore` 的匿名入口，写入 `ai_image` 时不经过任何租户/用户上下文。

## 2. 核心 DO 实体

> 索引说明（本节通用）：仓库 `sql/` 目录的各数据库初始化脚本（mysql / oracle / postgresql 等）未包含 ai 模块的建表语句，DO 代码中也只显式声明了主键 `@TableId`（非 MySQL 数据库通过 `@KeySequence` 走对应序列，如 `ai_model_seq`）。因此下文「索引」一栏仅列出代码中可确认的约束，不编造数据库二级索引。

### 2.1 模型配置聚合（模型接入的基石）

#### AiApiKeyDO (ai_api_key)

AI API 秘钥。一个平台可配置多条秘钥，供 `AiModelFactory` 按平台构建大模型客户端。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 名称 |
| apiKey | String | api_key | 密钥 |
| platform | String | platform | 平台，枚举 `AiPlatformEnum`（TongYi、YiYan、DeepSeek、ZhiPu、XingHuo、DouBao、HunYuan、SiliconFlow、MiniMax、Moonshot、BaiChuan、StepFun、MiMo、OpenAI、AzureOpenAI、Anthropic、Gemini、Ollama、StableDiffusion、Midjourney、Suno、Grok 共 22 个） |
| url | String | url | API 地址（OpenAI 兼容地址 / midjourney-proxy / suno 代理等） |
| status | Integer | status | 状态，枚举 `CommonStatusEnum`（0 开启、1 禁用） |

**继承**: BaseDO
**索引**: 主键 id；代码与仓库 SQL 均未声明其他索引

#### AiModelDO (ai_model)

AI 模型定义：挂在某个秘钥（keyId）之下，是聊天 / 绘画 / 向量等一切能力使用的模型元数据。「默认模型」= status 开启且 sort 排序第一。`@TableName(autoResultMap = true)`（`input_modalities`、`reasoning_config` 需 TypeHandler）。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| keyId | Long | key_id | API 秘钥编号，关联 `AiApiKeyDO.id` |
| name | String | name | 模型名称 |
| model | String | model | 模型标志（如 `gpt-4o`），下游各表冗余该字段 |
| platform | String | platform | 平台，枚举 `AiPlatformEnum` |
| type | Integer | type | 模型类型，枚举 `AiModelTypeEnum`：1 对话、2 图片、3 语音、4 视频、5 向量、6 重排序 |
| sort | Integer | sort | 排序值（决定默认模型） |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |
| temperature | Double | temperature | 温度参数（对话配置） |
| maxTokens | Integer | max_tokens | 单条回复的最大 Token 数量（对话配置） |
| maxContexts | Integer | max_contexts | 上下文的最大 Message 数量（对话配置） |
| inputModalities | List\<String\> | input_modalities | 输入模态数组，`StringListTypeHandler` 存字符串数组；枚举 `AiModelInputModalityEnum`（text / image / video），仅 CHAT 使用；为空（历史数据）视为仅支持 text |
| reasoningConfig | ReasoningConfig | reasoning_config | 思考配置，`JacksonTypeHandler` 存 JSON：`{levels:[{level,options}], defaultLevel}`；null 表示不管理思考、保持平台原有行为。内部类 `AiModelDO.ReasoningConfig` / `AiModelDO.ReasoningLevel` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiChatRoleDO (ai_chat_role)

AI 聊天角色：角色设定（system prompt）+ 模型 / 知识库 / 工具 / MCP Client 的组合预设。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 角色名称 |
| avatar | String | avatar | 角色头像 |
| category | String | category | 角色分类 |
| description | String | description | 角色描述 |
| systemMessage | String | system_message | 角色设定（system prompt） |
| userId | Long | user_id | 所属用户编号（私有角色的归属人） |
| modelId | Long | model_id | 关联 `AiModelDO.id` |
| knowledgeIds | List\<Long\> | knowledge_ids | 引用的知识库编号列表，`LongListTypeHandler` 存 JSON，关联 `AiKnowledgeDO.id` |
| toolIds | List\<Long\> | tool_ids | 引用的工具编号列表，`LongListTypeHandler` 存 JSON，关联 `AiToolDO.id` |
| mcpClientNames | List\<String\> | mcp_client_names | 引用的 MCP Client 名字列表，`StringListTypeHandler` 存 JSON，对应配置 `spring.ai.mcp.client` 下的名字 |
| publicStatus | Boolean | public_status | 是否公开：true 公开（管理员在【角色管理】创建）、false 私有（个人在【我的角色】创建） |
| sort | Integer | sort | 排序值 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiToolDO (ai_tool)

AI 工具（Function Calling）。`name` 即 Spring Bean 名字，例如 `DirectoryListToolFunction` → `directory_list`、`WeatherQueryToolFunction` → `weather_query`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 工具名称（对应 Bean 名字） |
| description | String | description | 工具描述 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

### 2.2 聊天对话聚合

#### AiChatConversationDO (ai_chat_conversation)

AI Chat 对话（会话）：用户每次发起聊天时创建，把消息聚合在一起。默认标题常量 `TITLE_DEFAULT = "新对话"`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| userId | Long | user_id | 用户编号 |
| title | String | title | 对话标题（系统默认生成，用户可改） |
| pinned | Boolean | pinned | 是否置顶 |
| pinnedTime | LocalDateTime | pinned_time | 置顶时间 |
| roleId | Long | role_id | 角色编号，关联 `AiChatRoleDO.id` |
| modelId | Long | model_id | 模型编号，关联 `AiModelDO.id` |
| model | String | model | 模型标志，冗余 `AiModelDO.model` |
| systemMessage | String | system_message | 角色设定（对话配置） |
| temperature | Double | temperature | 温度参数（对话配置） |
| maxTokens | Integer | max_tokens | 单条回复的最大 Token 数量（对话配置） |
| maxContexts | Integer | max_contexts | 上下文的最大 Message 数量（对话配置） |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiChatMessageDO (ai_chat_message)

AI Chat 消息：一问一答各存一条，通过 `replyId` 关联「问」与「答」。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增），每条聊天记录的唯一标识 |
| conversationId | Long | conversation_id | 对话编号，关联 `AiChatConversationDO.id` |
| replyId | Long | reply_id | 回复消息编号，关联本表 `id`，用于「问答」关联 |
| type | String | type | 消息类型，等价于 OpenAI 的 role，枚举 Spring AI `MessageType`（user / assistant / system 等） |
| userId | Long | user_id | 用户编号 |
| roleId | Long | role_id | 角色编号，关联 `AiChatRoleDO.id` |
| modelId | Long | model_id | 模型编号，关联 `AiModelDO.id` |
| model | String | model | 模型标志，冗余 `AiModelDO.model` |
| content | String | content | 聊天内容 |
| reasoningContent | String | reasoning_content | 推理内容（深度思考模型的思维链输出） |
| useContext | Boolean | use_context | 是否携带上下文 |
| segmentIds | List\<Long\> | segment_ids | 知识库段落编号数组，`LongListTypeHandler` 存 JSON，关联 `AiKnowledgeSegmentDO.id` |
| webSearchPages | List\<WebPage\> | web_search_pages | 联网搜索的网页内容数组，`JacksonTypeHandler` 存 JSON（`AiWebSearchResponse.WebPage`） |
| attachmentUrls | List\<String\> | attachment_urls | 附件 URL 数组，`StringListTypeHandler` 存 JSON |
| requestId | String | request_id | 请求编号，仅 assistant 消息有值，关联 `AiRequestLogDO.requestId`（详见下表 `ai_request_log`） |
| inputTokens | Long | input_tokens | 输入 Token 数，未知为 null |
| outputTokens | Long | output_tokens | 输出 Token 数，未知为 null |
| totalTokens | Long | total_tokens | 合计 Token 数，输入、输出都已知时才有值，否则为 null |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

### 2.3 知识库聚合（RAG）

#### AiKnowledgeDO (ai_knowledge)

AI 知识库：绑定一个向量模型（embedding model）与召回参数。`@TableName(autoResultMap = true)`；向量库实现由 `AiModelServiceImpl#getOrCreateVectorStore` 决定——当前默认 `SimpleVectorStore`（向量持久化到本地文件），Qdrant / Redis / Milvus 的构建代码已存在但默认被注释未启用。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 知识库名称 |
| description | String | description | 知识库描述 |
| embeddingModelId | Long | embedding_model_id | 向量模型编号，关联 `AiModelDO.id` |
| embeddingModel | String | embedding_model | 模型标识，冗余 `AiModelDO.model` |
| topK | Integer | top_k | 检索返回的相似段落条数 |
| similarityThreshold | Double | similarity_threshold | 相似度阈值 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiKnowledgeDocumentDO (ai_knowledge_document)

AI 知识库-文档：一篇接入文档（URL 或文本），按 `segmentMaxTokens` 切片入库。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| knowledgeId | Long | knowledge_id | 知识库编号，关联 `AiKnowledgeDO.id` |
| name | String | name | 文档名称 |
| url | String | url | 文件 URL |
| content | String | content | 文档内容 |
| contentLength | Integer | content_length | 文档长度 |
| tokens | Integer | tokens | 文档 token 数量 |
| segmentMaxTokens | Integer | segment_max_tokens | 分片最大 Token 数 |
| retrievalCount | Integer | retrieval_count | 召回次数 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiKnowledgeSegmentDO (ai_knowledge_segment)

AI 知识库-文档分段：切片内容 + 向量库中的引用编号。常量 `VECTOR_ID_EMPTY = ""` 表示尚未写入向量库。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| knowledgeId | Long | knowledge_id | 知识库编号，关联 `AiKnowledgeDO.id` |
| documentId | Long | document_id | 文档编号，关联 `AiKnowledgeDocumentDO.id` |
| content | String | content | 切片内容 |
| contentLength | Integer | content_length | 切片内容长度 |
| vectorId | String | vector_id | 向量库中对应向量记录的 id（SimpleVectorStore / Qdrant / Redis / Milvus 通用）；`VECTOR_ID_EMPTY` 表示尚未写入 |
| tokens | Integer | tokens | token 数量 |
| retrievalCount | Integer | retrieval_count | 召回次数 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

### 2.4 AIGC 创作聚合（绘画 / 音乐 / 思维导图 / 写作）

#### AiImageDO (ai_image)

AI 绘画任务：支持多平台（OpenAI、StabilityAI、Midjourney 等），Midjourney 走 midjourney-proxy 异步任务 + `AiMidjourneySyncJob` 定时补偿。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| userId | Long | user_id | 用户编号 |
| prompt | String | prompt | 提示词 |
| platform | String | platform | 平台，枚举 `AiPlatformEnum` |
| modelId | Long | model_id | 模型编号，关联 `AiModelDO.id` |
| model | String | model | 模型标识，冗余 `AiModelDO.model` |
| width | Integer | width | 图片宽度 |
| height | Integer | height | 图片高度 |
| status | Integer | status | 生成状态，枚举 `AiImageStatusEnum`：10 进行中、20 已完成、30 已失败 |
| finishTime | LocalDateTime | finish_time | 完成时间 |
| errorMessage | String | error_message | 绘画错误信息 |
| picUrl | String | pic_url | 图片地址 |
| publicStatus | Boolean | public_status | 是否公开 |
| options | Map\<String, Object\> | options | 各平台差异化绘制参数，`JacksonTypeHandler` 存 JSON（如 OpenAiImageOptions、StabilityAiImageOptions） |
| buttons | List\<Button\> | buttons | Midjourney 按钮（U1/U2、重新生成等），`JacksonTypeHandler` 存 JSON（`MidjourneyApi.Button`） |
| taskId | String | task_id | 任务编号（midjourney-proxy 的 task id） |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiMusicDO (ai_music)

AI 音乐任务：Suno 平台异步生成 + `AiSunoSyncJob` 定时补偿。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| userId | Long | user_id | 用户编号 |
| title | String | title | 音乐名称 |
| lyric | String | lyric | 歌词 |
| imageUrl | String | image_url | 封面图片地址 |
| audioUrl | String | audio_url | 音频地址 |
| videoUrl | String | video_url | 视频地址 |
| status | Integer | status | 音乐状态，枚举 `AiMusicStatusEnum`：10 进行中、20 已完成、30 已失败 |
| generateMode | Integer | generate_mode | 生成模式，枚举 `AiMusicGenerateModeEnum`：1 描述模式、2 歌词模式 |
| description | String | description | 描述词 |
| platform | String | platform | 平台，枚举 `AiPlatformEnum` |
| model | String | model | 模型 |
| tags | List\<String\> | tags | 音乐风格标签，`JacksonTypeHandler` 存 JSON |
| duration | Double | duration | 音乐时长（秒） |
| publicStatus | Boolean | public_status | 是否公开 |
| taskId | String | task_id | 任务编号（Suno） |
| errorMessage | String | error_message | 错误信息 |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiMindMapDO (ai_mind_map)

AI 思维导图：`generate-stream` SSE 流式生成 Markdown 格式导图内容。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| userId | Long | user_id | 用户编号 |
| platform | String | platform | 平台，枚举 `AiPlatformEnum` |
| modelId | Long | model_id | 模型编号，关联 `AiModelDO.id` |
| model | String | model | 模型标识 |
| prompt | String | prompt | 生成内容提示 |
| generatedContent | String | generated_content | 生成的内容 |
| errorMessage | String | error_message | 错误信息 |
| requestId | String | request_id | 请求编号，关联 `AiRequestLogDO.requestId` |
| inputTokens | Long | input_tokens | 输入 Token 数，未知为 null |
| outputTokens | Long | output_tokens | 输出 Token 数，未知为 null |
| totalTokens | Long | total_tokens | 合计 Token 数，输入、输出都已知时才有值 |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

#### AiWriteDO (ai_write)

AI 写作：撰写（1）/ 回复（2）两种类型，`generate-stream` SSE 流式生成。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| userId | Long | user_id | 用户编号 |
| type | Integer | type | 写作类型，枚举 `AiWriteTypeEnum`：1 撰写、2 回复 |
| platform | String | platform | 平台，枚举 `AiPlatformEnum` |
| modelId | Long | model_id | 模型编号，关联 `AiModelDO.id` |
| model | String | model | 模型标识 |
| prompt | String | prompt | 生成内容提示 |
| generatedContent | String | generated_content | 生成的内容 |
| originalContent | String | original_content | 原文（回复类型时被回复的内容） |
| length | Integer | length | 长度提示词，字典 `AI_WRITE_LENGTH` |
| format | Integer | format | 格式提示词，字典 `AI_WRITE_FORMAT` |
| tone | Integer | tone | 语气提示词，字典 `AI_WRITE_TONE` |
| language | Integer | language | 语言提示词，字典 `AI_WRITE_LANGUAGE` |
| errorMessage | String | error_message | 错误信息 |
| requestId | String | request_id | 请求编号，关联 `AiRequestLogDO.requestId` |
| inputTokens | Long | input_tokens | 输入 Token 数，未知为 null |
| outputTokens | Long | output_tokens | 输出 Token 数，未知为 null |
| totalTokens | Long | total_tokens | 合计 Token 数，输入、输出都已知时才有值 |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

### 2.5 工作流

#### AiWorkflowDO (ai_workflow)

AI 工作流：基于 TinyFlow 引擎，`graph` 字段存储流程图 JSON 模型。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 工作流名称 |
| code | String | code | 工作流标识 |
| graph | String | graph | 工作流模型 JSON 数据 |
| remark | String | remark | 备注 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引。`code` 的唯一性由服务层校验（`AiWorkflowServiceImpl#validateCodeUnique`，冲突抛 `WORKFLOW_CODE_EXISTS`），属应用层逻辑唯一约束

### 2.6 请求日志

#### AiRequestLogDO (ai_request_log)

AI 请求日志：每次业务生成尝试（聊天回复 / 写作 / 思维导图）落一条记录，不承诺对应每一次底层 HTTP 调用；用于 Token 用量统计、失败排查与链路追踪。`@TableName(value = "ai_request_log", autoResultMap = true)`。日志写入使用独立事务（`REQUIRES_NEW`），不影响主业务事务。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| requestId | String | request_id | 请求编号，本地生成的 UUID（非厂商返回的 id），业务表通过该字段关联本记录 |
| userId | Long | user_id | 发起请求的用户编号 |
| bizType | Integer | biz_type | 业务类型，枚举 `AiRequestLogBizTypeEnum`：1 聊天、2 写作、3 思维导图 |
| bizId | Long | biz_id | 业务单据编号（对话消息 id / 写作记录 id / 导图记录 id） |
| platform | String | platform | 平台，枚举 `AiPlatformEnum` |
| modelId | Long | model_id | 模型编号，关联 `AiModelDO.id` |
| model | String | model | 模型标识，冗余 `AiModelDO.model` |
| status | Integer | status | 状态，枚举 `AiRequestLogStatusEnum`：20 成功、30 失败、40 取消 |
| errorMessage | String | error_message | 失败信息（失败 / 取消时记录） |
| beginTime | LocalDateTime | begin_time | 请求开始时间 |
| endTime | LocalDateTime | end_time | 请求结束时间 |
| duration | Long | duration | 耗时（毫秒），由开始与结束时间计算 |
| inputTokens | Long | input_tokens | 输入 Token 数，未知为 null（不做估算） |
| outputTokens | Long | output_tokens | 输出 Token 数，未知为 null |
| totalTokens | Long | total_tokens | 合计 Token 数，输入、输出都已知时才 = 两者之和，否则为 null |
| responseMetadata | Map\<String, Object\> | response_metadata | 响应元数据快照，`JacksonTypeHandler` 存 JSON（含厂商返回的 usage 原始信息等） |

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

## 3. 实体关系

核心外键 / 从属关系（均为逻辑外键，靠业务代码维护，未建数据库外键约束）：

```text
ai_api_key ──1:N(keyId)──> ai_model
                             │  modelId（对话/绘画/音乐/导图/写作/知识库向量模型 共用）
    ┌────────────────────────┼──────────────────────────────┬─────────────────┐
    │                        │                              │                 │
    ▼                        ▼                              ▼                 ▼
ai_chat_role ─1:N─> ai_chat_conversation ─1:N─> ai_chat_message   ai_image / ai_music
 (roleId)            (roleId, modelId)          (conversationId,   ai_mind_map / ai_write
                                                 replyId 自关联)    (modelId)
                                                 │
                                                 └─ segmentIds ──逻辑关联──> ai_knowledge_segment

ai_model ─1:N(embeddingModelId)─> ai_knowledge ─1:N─> ai_knowledge_document ─1:N─> ai_knowledge_segment
                                                                                      （vectorId → 向量库）
ai_chat_role.knowledgeIds ──逻辑多对多──> ai_knowledge.id      （JSON 数组存储）
ai_chat_role.toolIds      ──逻辑多对多──> ai_tool.id           （JSON 数组存储）
ai_chat_role.mcpClientNames ──配置关联──> spring.ai.mcp.client 客户端名（非数据库外键）
ai_request_log ──逻辑关联──> ai_chat_message / ai_write / ai_mind_map   （通过 requestId + bizType/bizId）
各表 userId ──跨模块逻辑关联──> system 模块 AdminUserDO.id
```

关系要点：

- **ai_api_key → ai_model**：秘钥与模型的 1:N 关系，模型构建时通过 `AiModelFactory` 用秘钥创建对应平台客户端。
- **ai_model → 各业务表**：`modelId` + 冗余 `model` 标志，是本模块被引用最多的表；ai_knowledge 通过 `embeddingModelId` 引用向量类型的模型（type=5）。
- **ai_chat_role → ai_chat_conversation**：会话记录使用的角色；会话把 `systemMessage`、`temperature`、`maxTokens`、`maxContexts` 从角色/模型快照到自身，后续发送消息不再依赖角色当前配置。
- **ai_chat_conversation → ai_chat_message**：1:N；消息表内 `replyId` 自关联实现「用户提问 → 模型回答」配对；`segmentIds` 以 JSON 数组弱引用命中的知识库分段（RAG 引用溯源）。
- **ai_knowledge → ai_knowledge_document → ai_knowledge_segment**：知识库三级结构；segment 的 `vectorId` 指向向量库（当前默认 SimpleVectorStore，可切换 Qdrant/Redis/Milvus）中的真实向量记录，向量数据不落本模块数据库。
- **ai_chat_role 对 knowledge / tool 的引用**：通过 `LongListTypeHandler` 存 JSON 数组实现逻辑多对多，没有中间表。
- **跨模块**：仅通过 `userId` 弱关联 system 模块用户；本模块无 api 包，不对外暴露跨模块接口，仅由 `yudao-server` 聚合引用。
- **ai_workflow**：独立聚合，`code` 应用层唯一，供 TinyFlow 流程执行时按 code 调用。
- **ai_request_log**：请求日志与业务表通过 `requestId`（本地 UUID）逻辑关联，`bizType` 标识来源业务（对话 / 写作 / 思维导图）、`bizId` 指向对应记录；写入使用独立事务，业务事务回滚不影响日志落库。`ai_chat_message`（仅 assistant 消息）、`ai_write`、`ai_mind_map` 各自镜像了 `requestId` 与 Token 三字段，便于随业务数据直接展示用量。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|------|-----|------|
| ai_api_key | AiApiKeyDO | AI API 秘钥（22 个大模型平台的接入密钥） |
| ai_model | AiModelDO | AI 模型（挂在秘钥下的模型元数据与对话默认参数） |
| ai_chat_role | AiChatRoleDO | AI 聊天角色（system prompt + 模型/知识库/工具/MCP 组合预设） |
| ai_tool | AiToolDO | AI 工具（Function Calling 的 Bean 定义） |
| ai_chat_conversation | AiChatConversationDO | AI 对话（会话，含置顶与对话参数快照） |
| ai_chat_message | AiChatMessageDO | AI 聊天消息（问答配对、RAG 段落引用、联网搜索、附件） |
| ai_knowledge | AiKnowledgeDO | AI 知识库（向量模型 + 召回参数） |
| ai_knowledge_document | AiKnowledgeDocumentDO | AI 知识库-文档 |
| ai_knowledge_segment | AiKnowledgeSegmentDO | AI 知识库-文档分段（含向量库编号 vectorId） |
| ai_image | AiImageDO | AI 绘画（含 Midjourney 异步任务与按钮） |
| ai_music | AiMusicDO | AI 音乐（Suno 异步生成） |
| ai_mind_map | AiMindMapDO | AI 思维导图 |
| ai_write | AiWriteDO | AI 写作（撰写/回复） |
| ai_workflow | AiWorkflowDO | AI 工作流（TinyFlow 流程图 JSON） |
| ai_request_log | AiRequestLogDO | AI 请求日志（Token 用量、状态、耗时与响应元数据） |
