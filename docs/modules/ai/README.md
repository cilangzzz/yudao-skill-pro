# AI 大模型模块 (ai)

> 接入 LLM 大模型的统一 AI 能力模块，提供聊天对话、知识库 RAG、绘画、音乐、写作、思维导图、工作流等功能，已接入通义千问、文心一言、讯飞星火、智谱 GLM、DeepSeek、OpenAI、Ollama、Midjourney、StableDiffusion、Suno 等国内外主流模型。

## 模块概述

- **模块路径**: `yudao-module-ai`（单模块布局，无子模块拆分）
- **业务定位**: 基于 Spring AI 构建的企业级 AI 中台，向上为管理后台提供聊天助手、知识库问答、多平台绘画/音乐/写作/思维导图生成与 AI 工作流编排能力；向下通过统一的模型工厂对接 21 个 AI 平台（Chat / Image / Embedding / VectorStore 四类模型），并内置 MCP Server/Client 与 Function Calling 工具扩展机制。
- **技术栈**: Spring Boot 3.x + Spring AI 1.1.8（BOM）+ Spring AI Alibaba 1.1.2.2（通义千问 DashScope）+ MyBatis-Plus + Reactor（SSE 流式）+ 向量库（Qdrant / Redis / Milvus）+ Tika 文档解析 + MCP Server(WebMVC)/Client + TinyFlow 1.2.6 工作流引擎 + Midjourney Proxy / Suno 私有 API

## 设计原则

| 原则 | 说明 |
|-----|------|
| 统一模型接入层 | `framework/ai/core/model/AiModelFactory` 按 platform 动态创建并缓存 ChatModel / ImageModel / EmbeddingModel / VectorStore / MidjourneyApi / SunoApi，业务 Service 不直接感知具体平台 SDK |
| 平台枚举驱动 | `AiPlatformEnum` 收录 21 个平台，业务表统一冗余 `platform` + `model` 字段，支撑多平台多模型并存 |
| 流式优先 | 聊天消息、写作、思维导图的生成端点均提供 SSE 流式版本（`TEXT_EVENT_STREAM` + Reactor `Flux<CommonResult<T>>`），同时保留段式接口 |
| 个人与管理双视角 | 对话、角色、绘画、音乐等功能同时提供「我的」端点（仅登录校验、按 userId 隔离）与管理端点（`@PreAuthorize` 权限控制） |
| 异步任务同步 | Midjourney 绘画、Suno 音乐为异步任务：Proxy 回调（`@PermitAll` + `@TenantIgnore`）+ 定时 Job（`AiMidjourneySyncJob` / `AiSunoSyncJob`）双通道同步进展 |
| 知识库 RAG 三层结构 | 知识库 → 文档 → 段落，段落向量化写入向量库并回存 `vectorId`，聊天与角色可引用段落做增强问答 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 聊天对话 | 对话/消息管理，段式与流式发送，支持角色设定、上下文数、温度等参数，消息可携带知识库段落引用、联网搜索结果与附件 | `AiChatConversationDO`、`AiChatMessageDO` |
| 知识库 | 知识库/文档/段落三级管理，基于 Tika 下载解析文档，按 Token/语义/Markdown QA 策略切片，向量化后支持相似度检索与召回计数 | `AiKnowledgeDO`、`AiKnowledgeDocumentDO`、`AiKnowledgeSegmentDO` |
| 模型管理 | API 密钥、模型（含默认模型机制）、聊天角色（公开/私有、可挂知识库/工具/MCP Client）、工具（Function Calling Bean）四类配置 | `AiApiKeyDO`、`AiModelDO`、`AiChatRoleDO`、`AiToolDO` |
| AI 绘画 | 多平台文生图（OpenAI、Stability 等），Midjourney 专属 imagine/action/notify 回调链路，公开图库与绘画管理 | `AiImageDO` |
| AI 音乐 | Suno 音乐生成（描述模式/歌词模式），异步任务回传音频/视频/封面，支持我的音乐与管理 | `AiMusicDO` |
| AI 写作 | 撰写（含原文润色）与回复两种类型，流式生成，支持长度/格式/语气/语言提示词 | `AiWriteDO` |
| AI 思维导图 | 提示词流式生成 Markdown 格式导图内容 | `AiMindMapDO` |
| AI 工作流 | 基于 TinyFlow 编排 LLM 节点（graph JSON 存储），支持试运行测试 | `AiWorkflowDO` |

## API 接口索引

### AI 聊天对话 (AiChatConversationController)

前缀 `/ai/chat/conversation`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/chat/conversation/create-my | POST | 创建【我的】聊天对话 | 已认证 |
| /ai/chat/conversation/update-my | PUT | 更新【我的】聊天对话 | 已认证 |
| /ai/chat/conversation/my-list | GET | 获得【我的】聊天对话列表 | 已认证 |
| /ai/chat/conversation/get-my | GET | 获得【我的】聊天对话 | 已认证 |
| /ai/chat/conversation/delete-my | DELETE | 删除聊天对话 | 已认证 |
| /ai/chat/conversation/delete-by-unpinned | DELETE | 删除未置顶的聊天对话 | 已认证 |
| /ai/chat/conversation/page | GET | 获得对话分页（对话管理菜单） | ai:chat-conversation:query |
| /ai/chat/conversation/get | GET | 获得对话（对话管理菜单） | ai:chat-conversation:query |
| /ai/chat/conversation/delete-by-admin | DELETE | 管理员删除对话 | ai:chat-conversation:delete |

### 聊天消息 (AiChatMessageController)

前缀 `/ai/chat/message`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/chat/message/send | POST | 发送消息（段式，一次性返回） | 已认证 |
| /ai/chat/message/send-stream | POST | 发送消息（流式，SSE） | 已认证 |
| /ai/chat/message/list-by-conversation-id | GET | 获得指定对话的消息列表（含知识库段落） | 已认证 |
| /ai/chat/message/delete | DELETE | 删除消息 | 已认证 |
| /ai/chat/message/delete-by-conversation-id | DELETE | 删除指定对话的消息 | 已认证 |
| /ai/chat/message/page | GET | 获得消息分页（对话管理菜单） | ai:chat-message:query |
| /ai/chat/message/get | GET | 获得消息（对话管理菜单） | ai:chat-message:query |
| /ai/chat/message/delete-by-admin | DELETE | 管理员删除消息 | ai:chat-message:delete |

### AI 知识库 (AiKnowledgeController)

前缀 `/ai/knowledge`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/knowledge/page | GET | 获取知识库分页 | ai:knowledge:query |
| /ai/knowledge/get | GET | 获得知识库 | ai:knowledge:query |
| /ai/knowledge/create | POST | 创建知识库 | ai:knowledge:create |
| /ai/knowledge/update | PUT | 更新知识库 | ai:knowledge:update |
| /ai/knowledge/delete | DELETE | 删除知识库 | ai:knowledge:delete |
| /ai/knowledge/simple-list | GET | 获得知识库的精简列表 | 已认证 |

### AI 知识库文档 (AiKnowledgeDocumentController)

前缀 `/ai/knowledge/document`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/knowledge/document/page | GET | 获取文档分页 | ai:knowledge:query |
| /ai/knowledge/document/get | GET | 获取文档详情 | ai:knowledge:query |
| /ai/knowledge/document/create | POST | 新建文档（单个） | ai:knowledge:create |
| /ai/knowledge/document/create-list | POST | 新建文档（多个） | ai:knowledge:create |
| /ai/knowledge/document/update | PUT | 更新文档 | ai:knowledge:update |
| /ai/knowledge/document/update-status | PUT | 更新文档状态 | ai:knowledge:update |
| /ai/knowledge/document/delete | DELETE | 删除文档 | ai:knowledge:delete |

### AI 知识库段落 (AiKnowledgeSegmentController)

前缀 `/ai/knowledge/segment`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/knowledge/segment/get | GET | 获取段落详情 | ai:knowledge:query |
| /ai/knowledge/segment/page | GET | 获取段落分页 | ai:knowledge:query |
| /ai/knowledge/segment/create | POST | 创建段落 | ai:knowledge:create |
| /ai/knowledge/segment/update | PUT | 更新段落内容 | ai:knowledge:update |
| /ai/knowledge/segment/update-status | PUT | 启禁用段落内容 | ai:knowledge:update |
| /ai/knowledge/segment/delete | DELETE | 删除段落 | ai:knowledge:delete |
| /ai/knowledge/segment/split | GET | 切片内容（按 URL + 最大 Token 预览切片） | ai:knowledge:query |
| /ai/knowledge/segment/get-process-list | GET | 获取文档处理列表 | ai:knowledge:query |
| /ai/knowledge/segment/search | GET | 搜索段落内容（向量相似度检索） | ai:knowledge:query |

### AI API 密钥 (AiApiKeyController)

前缀 `/ai/api-key`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/api-key/create | POST | 创建 API 密钥 | ai:api-key:create |
| /ai/api-key/update | PUT | 更新 API 密钥 | ai:api-key:update |
| /ai/api-key/delete | DELETE | 删除 API 密钥 | ai:api-key:delete |
| /ai/api-key/get | GET | 获得 API 密钥 | ai:api-key:query |
| /ai/api-key/page | GET | 获得 API 密钥分页 | ai:api-key:query |
| /ai/api-key/simple-list | GET | 获得 API 密钥分页列表 | 已认证 |

### AI 模型 (AiModelController)

前缀 `/ai/model`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/model/create | POST | 创建模型 | ai:model:create |
| /ai/model/update | PUT | 更新模型 | ai:model:update |
| /ai/model/delete | DELETE | 删除模型 | ai:model:delete |
| /ai/model/get | GET | 获得模型 | ai:model:query |
| /ai/model/page | GET | 获得模型分页 | ai:model:query |
| /ai/model/simple-list | GET | 获得模型列表（按类型 + 平台过滤） | 已认证 |

### AI 工具 (AiToolController)

前缀 `/ai/tool`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/tool/create | POST | 创建工具 | ai:tool:create |
| /ai/tool/update | PUT | 更新工具 | ai:tool:update |
| /ai/tool/delete | DELETE | 删除工具 | ai:tool:delete |
| /ai/tool/get | GET | 获得工具 | ai:tool:query |
| /ai/tool/page | GET | 获得工具分页 | ai:tool:query |
| /ai/tool/simple-list | GET | 获得工具列表 | 已认证 |

### AI 聊天角色 (AiChatRoleController)

前缀 `/ai/chat-role`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/chat-role/my-page | GET | 获得【我的】聊天角色分页 | 已认证 |
| /ai/chat-role/get-my | GET | 获得【我的】聊天角色 | 已认证 |
| /ai/chat-role/create-my | POST | 创建【我的】聊天角色 | 已认证 |
| /ai/chat-role/update-my | PUT | 更新【我的】聊天角色 | 已认证 |
| /ai/chat-role/delete-my | DELETE | 删除【我的】聊天角色 | 已认证 |
| /ai/chat-role/category-list | GET | 获得聊天角色的分类列表 | 已认证 |
| /ai/chat-role/create | POST | 创建聊天角色（角色管理） | ai:chat-role:create |
| /ai/chat-role/update | PUT | 更新聊天角色（角色管理） | ai:chat-role:update |
| /ai/chat-role/delete | DELETE | 删除聊天角色（角色管理） | ai:chat-role:delete |
| /ai/chat-role/get | GET | 获得聊天角色（角色管理） | ai:chat-role:query |
| /ai/chat-role/page | GET | 获得聊天角色分页（角色管理） | ai:chat-role:query |

### AI 工作流 (AiWorkflowController)

前缀 `/ai/workflow`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/workflow/create | POST | 创建 AI 工作流 | ai:workflow:create |
| /ai/workflow/update | PUT | 更新 AI 工作流 | ai:workflow:update |
| /ai/workflow/delete | DELETE | 删除 AI 工作流 | ai:workflow:delete |
| /ai/workflow/get | GET | 获得 AI 工作流 | ai:workflow:query |
| /ai/workflow/page | GET | 获得 AI 工作流分页 | ai:workflow:query |
| /ai/workflow/test | POST | 测试 AI 工作流（试运行） | ai:workflow:test |

### AI 绘画 (AiImageController)

前缀 `/ai/image`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/image/my-page | GET | 获取【我的】绘图分页 | 已认证 |
| /ai/image/public-page | GET | 获取公开的绘图分页 | 已认证 |
| /ai/image/get-my | GET | 获取【我的】绘图记录 | 已认证 |
| /ai/image/my-list-by-ids | GET | 获取【我的】绘图记录列表 | 已认证 |
| /ai/image/draw | POST | 生成图片（多平台文生图） | 已认证 |
| /ai/image/delete-my | DELETE | 删除【我的】绘画记录 | 已认证 |
| /ai/image/midjourney/imagine | POST | 【Midjourney】生成图片 | 已认证 |
| /ai/image/midjourney/notify | POST | 【Midjourney】通知图片进展（Proxy 回调） | 匿名回调（@PermitAll + @TenantIgnore） |
| /ai/image/midjourney/action | POST | 【Midjourney】Action 操作（二次生成，如 U1/U2/放大） | 已认证 |
| /ai/image/page | GET | 获得绘画分页（绘画管理） | ai:image:query |
| /ai/image/get | GET | 获得绘画（绘画管理） | ai:image:query |
| /ai/image/update | PUT | 更新绘画（绘画管理） | ai:image:update |
| /ai/image/delete | DELETE | 删除绘画（绘画管理） | ai:image:delete |

### AI 思维导图 (AiMindMapController)

前缀 `/ai/mind-map`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/mind-map/generate-stream | POST | 导图生成（流式，SSE） | 已认证 |
| /ai/mind-map/delete | DELETE | 删除思维导图 | ai:mind-map:delete |
| /ai/mind-map/get | GET | 获得思维导图 | ai:mind-map:query |
| /ai/mind-map/page | GET | 获得思维导图分页 | ai:mind-map:query |

### AI 音乐 (AiMusicController)

前缀 `/ai/music`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/music/my-page | GET | 获得【我的】音乐分页 | 已认证 |
| /ai/music/generate | POST | 音乐生成（Suno） | 已认证 |
| /ai/music/delete-my | DELETE | 删除【我的】音乐记录 | 已认证 |
| /ai/music/get-my | GET | 获取【我的】音乐 | 已认证 |
| /ai/music/update-my | POST | 修改【我的】音乐（目前只支持修改标题） | 已认证 |
| /ai/music/page | GET | 获得音乐分页（音乐管理） | ai:music:query |
| /ai/music/get | GET | 获得音乐（音乐管理） | ai:music:query |
| /ai/music/delete | DELETE | 删除音乐（音乐管理） | ai:music:delete |
| /ai/music/update | PUT | 更新音乐（音乐管理） | ai:music:update |

### AI 写作 (AiWriteController)

前缀 `/ai/write`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai/write/generate-stream | POST | 写作生成（流式，SSE） | 已认证 |
| /ai/write/delete | DELETE | 删除写作 | ai:write:delete |
| /ai/write/get | GET | 获得写作 | ai:write:query |
| /ai/write/page | GET | 获得写作分页 | ai:write:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| ai_chat_conversation | AI 聊天对话 | BaseDO | userId、title、pinned、roleId、modelId、model、systemMessage、temperature、maxTokens、maxContexts |
| ai_chat_message | AI 聊天消息 | BaseDO | conversationId、replyId、type、userId、roleId、modelId、model、content、reasoningContent、useContext、segmentIds、webSearchPages、attachmentUrls |
| ai_knowledge | AI 知识库 | BaseDO | name、description、embeddingModelId、embeddingModel、topK、similarityThreshold、status |
| ai_knowledge_document | AI 知识库文档 | BaseDO | knowledgeId、name、url、content、contentLength、tokens、segmentMaxTokens、retrievalCount、status |
| ai_knowledge_segment | AI 知识库文档分段 | BaseDO | knowledgeId、documentId、content、contentLength、vectorId、tokens、retrievalCount、status |
| ai_api_key | AI API 密钥 | BaseDO | name、apiKey、platform、url、status |
| ai_model | AI 模型 | BaseDO | keyId、name、model、platform、type、sort、status、temperature、maxTokens、maxContexts |
| ai_chat_role | AI 聊天角色 | BaseDO | name、avatar、category、description、systemMessage、userId、modelId、knowledgeIds、toolIds、mcpClientNames、publicStatus、sort、status |
| ai_tool | AI 工具 | BaseDO | name（对应 Bean 名）、description、status |
| ai_image | AI 绘画 | BaseDO | userId、prompt、platform、modelId、model、width、height、status、finishTime、errorMessage、picUrl、publicStatus、options、buttons、taskId |
| ai_music | AI 音乐 | BaseDO | userId、title、lyric、imageUrl、audioUrl、videoUrl、status、generateMode、description、platform、model、tags、duration、publicStatus、taskId、errorMessage |
| ai_mind_map | AI 思维导图 | BaseDO | userId、platform、modelId、model、prompt、generatedContent、errorMessage |
| ai_write | AI 写作 | BaseDO | userId、type、platform、modelId、model、prompt、generatedContent、originalContent、length、format、tone、language、errorMessage |
| ai_workflow | AI 工作流 | BaseDO | name、code、graph（TinyFlow JSON）、remark、status |

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 工厂模式 | `framework/ai/core/model/AiModelFactory` + `AiModelFactoryImpl` | 按 platform + apiKey + url 惰性创建并缓存各平台 ChatModel / ImageModel / EmbeddingModel / VectorStore / MidjourneyApi / SunoApi，屏蔽 21 个平台 SDK 差异 |
| 策略模式 | `service/knowledge/splitter`（`SemanticTextSplitter`、`MarkdownQaSplitter` 继承 Spring AI `TextSplitter`）+ `AiDocumentSplitStrategyEnum` | 文档切片支持 Token / 语义 / Markdown QA 多种策略，`AiKnowledgeSegmentServiceImpl.splitContentByStrategy` 按策略（支持 AUTO 自动检测）路由 |
| 工具回调（Function Calling） | `tool/function` 包：`DirectoryListToolFunction`、`WeatherQueryToolFunction`、`UserProfileQueryToolFunction` | 将 Spring Bean 注册为 LLM 可调用的工具函数，`AiToolDO.name` 与 Bean 名对应 |
| 工作流引擎模式 | `service/workflow/AiWorkflowServiceImpl`（TinyFlow `Tinyflow` 链式执行） | 解析 graph JSON 构建 TinyFlow 执行链，`AiModelService.getLLmProvider4Tinyflow` 注入 LLM Provider |
| 异步回调 + 定时补偿 | Midjourney（`/midjourney/notify` 回调 + `AiMidjourneySyncJob`）、Suno（`AiSunoSyncJob`） | 异步生成任务进展的可靠同步 |

## 依赖关系

- **上游**（本模块依赖）
  - framework starter: `yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-redis`、`yudao-spring-boot-starter-biz-tenant`、`yudao-spring-boot-starter-job`、`yudao-spring-boot-starter-excel`、`yudao-spring-boot-starter-test`
  - 业务模块: `yudao-module-system`（AdminUserApi 查询用户资料）、`yudao-module-infra`（FileApi 上传绘画图片/音乐文件）
  - 三方 AI: Spring AI（openai/azure-openai/anthropic/deepseek/ollama/stability-ai）、Spring AI Alibaba（DashScope）、Qdrant/Redis/Milvus 向量库、Tika、MCP Server(WebMVC)/Client、TinyFlow
- **下游**（依赖本模块）
  - 无（`yudao-server` 聚合打包引用，无其他业务模块依赖 ai 模块）

## 对外暴露的 API

本模块未提供 `api` 包与跨模块 Api 接口，仅通过 `yudao-server` 以 HTTP 方式对外提供服务。

## 详细文档

- [api-chat.md](api-chat.md) - AI 聊天对话与消息
- [api-knowledge.md](api-knowledge.md) - AI 知识库（文档/段落/切片/检索）
- [api-model.md](api-model.md) - API 密钥、模型、聊天角色与工具
- [api-image.md](api-image.md) - AI 绘画与 Midjourney
- [api-music.md](api-music.md) - AI 音乐（Suno）
- [api-write.md](api-write.md) - AI 写作
- [api-mindmap.md](api-mindmap.md) - AI 思维导图
- [api-workflow.md](api-workflow.md) - AI 工作流（TinyFlow）
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南（分层代码规范、模型调用、新增平台/能力步骤、关键文件索引）
