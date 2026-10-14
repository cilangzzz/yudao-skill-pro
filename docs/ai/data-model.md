# 数据模型详情

> ai 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

## 1. 实体继承体系

ai 模块全部 14 个 DO 位于 `cn.iocoder.yudao.module.ai.dal.dataobject` 下，按业务域分为 chat / knowledge / model / image / music / mindmap / write / workflow 八个包，**全部直接继承框架的 BaseDO，无一使用 TenantBaseDO**：

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
| platform | String | platform | 平台，枚举 `AiPlatformEnum`（TongYi、YiYan、DeepSeek、ZhiPu、XingHuo、DouBao、HunYuan、SiliconFlow、MiniMax、Moonshot、BaiChuan、StepFun、OpenAI、AzureOpenAI、Anthropic、Gemini、Ollama、StableDiffusion、Midjourney、Suno、Grok 共 21 个） |
| url | String | url | API 地址（OpenAI 兼容地址 / midjourney-proxy / suno 代理等） |
| status | Integer | status | 状态，枚举 `CommonStatusEnum`（0 开启、1 禁用） |

**继承**: BaseDO
**索引**: 主键 id；代码与仓库 SQL 均未声明其他索引

#### AiModelDO (ai_model)

AI 模型定义：挂在某个秘钥（keyId）之下，是聊天 / 绘画 / 向量等一切能力使用的模型元数据。「默认模型」= status 开启且 sort 排序第一。

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

**继承**: BaseDO
**索引**: 主键 id；无其他已声明索引

### 2.3 知识库聚合（RAG）

#### AiKnowledgeDO (ai_knowledge)

AI 知识库：绑定一个向量模型（embedding model）与召回参数。`@TableName(autoResultMap = true)`；向量库支持 Qdrant / Redis / Milvus。

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
| vectorId | String | vector_id | 向量库的编号（Qdrant / Redis / Milvus 中对应记录的 id） |
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
各表 userId ──跨模块逻辑关联──> system 模块 AdminUserDO.id
```

关系要点：

- **ai_api_key → ai_model**：秘钥与模型的 1:N 关系，模型构建时通过 `AiModelFactory` 用秘钥创建对应平台客户端。
- **ai_model → 各业务表**：`modelId` + 冗余 `model` 标志，是本模块被引用最多的表；ai_knowledge 通过 `embeddingModelId` 引用向量类型的模型（type=5）。
- **ai_chat_role → ai_chat_conversation**：会话记录使用的角色；会话把 `systemMessage`、`temperature`、`maxTokens`、`maxContexts` 从角色/模型快照到自身，后续发送消息不再依赖角色当前配置。
- **ai_chat_conversation → ai_chat_message**：1:N；消息表内 `replyId` 自关联实现「用户提问 → 模型回答」配对；`segmentIds` 以 JSON 数组弱引用命中的知识库分段（RAG 引用溯源）。
- **ai_knowledge → ai_knowledge_document → ai_knowledge_segment**：知识库三级结构；segment 的 `vectorId` 指向外部向量库（Qdrant/Redis/Milvus）中的真实向量记录，向量数据不落本模块数据库。
- **ai_chat_role 对 knowledge / tool 的引用**：通过 `LongListTypeHandler` 存 JSON 数组实现逻辑多对多，没有中间表。
- **跨模块**：仅通过 `userId` 弱关联 system 模块用户；本模块无 api 包，不对外暴露跨模块接口，仅由 `yudao-server` 聚合引用。
- **ai_workflow**：独立聚合，`code` 应用层唯一，供 TinyFlow 流程执行时按 code 调用。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|------|-----|------|
| ai_api_key | AiApiKeyDO | AI API 秘钥（21 个大模型平台的接入密钥） |
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
