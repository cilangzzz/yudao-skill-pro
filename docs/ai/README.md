# AI 模块文档

> 模块路径：`yudao-module-ai` | skill-ai.yaml v1.0.0

## 模块概述

AI 模块是系统的智能化核心，提供大模型集成能力。基于 Spring AI 框架实现多平台统一抽象，支持 20+ AI 服务商的接入。模块覆盖聊天对话、图像生成、音乐创作、知识库 RAG、写作助手、思维导图、工作流编排等七大业务域。

## 核心功能

| 业务域 | 说明 | Controller | 详细文档 |
|--------|------|------------|----------|
| 聊天对话 | 多模型切换、流式响应、知识库增强、联网搜索 | `AiChatMessageController` / `AiChatConversationController` | [api-chat.md](api-chat.md) |
| 图像生成 | DALL-E、Stable Diffusion、Midjourney、硅基流动 | `AiImageController` | [api-image.md](api-image.md) |
| 模型配置 | API 密钥管理、模型配置管理 | `AiModelController` | [api-model.md](api-model.md) |
| 知识库 | RAG 检索增强、文档分片、向量存储、语义检索 | `AiKnowledgeController` | [api-knowledge.md](api-knowledge.md) |
| 音乐生成 | Suno AI 音乐创作 | `AiMusicController` | [api-music.md](api-music.md) |
| 写作助手 | AI 辅助写作 | `AiWriteController` | [api-write.md](api-write.md) |
| 思维导图 | AI 生成思维导图 | `AiMindMapController` | [api-mindmap.md](api-mindmap.md) |
| 工作流 | 可视化 AI 工作流编排 | `AiWorkflowController` | [api-workflow.md](api-workflow.md) |

## API 索引

### 聊天对话
- `POST /ai/chat/message/send` - 同步发送消息
- `POST /ai/chat/message/send-stream` - 流式发送消息（SSE）
- 对话管理 CRUD：`/ai/chat/conversation/**`

### 图像生成
- `POST /ai/image/generate` - 生成图像
- `GET /ai/image/get` - 获取图像详情
- `GET /ai/image/page` - 分页查询

### 模型配置
- API 密钥 CRUD：`/ai/api-key/**`
- 模型 CRUD：`/ai/model/**`

### 知识库
- 知识库 CRUD：`/ai/knowledge/**`
- 文档管理：`/ai/knowledge/document/**`
- 分段管理：`/ai/knowledge/segment/**`

### 音乐生成
- `POST /ai/music/generate` - 生成音乐
- 音乐 CRUD：`/ai/music/**`

### 写作助手
- `POST /ai/write/generate` - AI 写作
- 写作 CRUD：`/ai/write/**`

### 思维导图
- `POST /ai/mind-map/generate` - 生成思维导图
- 思维导图 CRUD：`/ai/mind-map/**`

### 工作流
- 工作流 CRUD：`/ai/workflow/**`

## 数据模型

| 表名 | 实体类 | 说明 |
|------|--------|------|
| `ai_api_key` | `AiApiKeyDO` | AI API 密钥表 |
| `ai_model` | `AiModelDO` | AI 模型配置表 |
| `ai_chat_role` | `AiChatRoleDO` | AI 聊天角色表 |
| `ai_tool` | `AiToolDO` | AI 工具表 |
| `ai_chat_conversation` | `AiChatConversationDO` | 聊天对话表 |
| `ai_chat_message` | `AiChatMessageDO` | 聊天消息表 |
| `ai_image` | `AiImageDO` | 绘画记录表 |
| `ai_knowledge` | `AiKnowledgeDO` | 知识库表 |
| `ai_knowledge_document` | `AiKnowledgeDocumentDO` | 知识库文档表 |
| `ai_knowledge_segment` | `AiKnowledgeSegmentDO` | 知识库分段表 |
| `ai_music` | `AiMusicDO` | 音乐表 |
| `ai_write` | `AiWriteDO` | 写作表 |
| `ai_mind_map` | `AiMindMapDO` | 思维导图表 |
| `ai_workflow` | `AiWorkflowDO` | 工作流表 |

详细表结构参见 [data-model.md](data-model.md)。

## 架构分层

```
controller/          HTTP 接口层
  chat/              聊天消息、对话管理
  image/             图像生成
  knowledge/         知识库管理
  model/             模型配置
  music/             音乐生成
  write/             写作助手
  mindmap/           思维导图
  workflow/          工作流

service/             业务逻辑层（按领域划分）
dal/                 数据访问层
  dataobject/        DO 实体类
  mysql/             MyBatis Mapper

framework/ai/        AI 框架集成层
  core/model/        模型工厂和多平台适配
  core/websearch/    联网搜索客户端
  config/            自动配置类
```

## 设计模式

| 模式 | 位置 | 用途 |
|------|------|------|
| 工厂模式 | `AiModelFactory` / `AiModelFactoryImpl` | 统一创建各平台 AI 模型实例 |
| 策略模式 | `AiModelFactoryImpl` | 根据平台类型选择不同模型创建策略 |
| 单例模式 | `AiModelFactoryImpl` | Hutool Singleton 缓存 AI 客户端 |
| 模板方法 | `AiChatMessageServiceImpl` | 聊天消息处理统一流程 |

## 依赖关系

### 内部依赖
- `system` 模块 - `AdminUserApi`：获取用户信息

### 外部依赖
| 库 | 版本 | 用途 |
|----|------|------|
| spring-ai-core | 1.0.x | Spring AI 核心框架 |
| spring-ai-openai | 1.0.x | OpenAI 集成 |
| spring-ai-anthropic | 1.0.x | Anthropic Claude 集成 |
| spring-ai-ollama | 1.0.x | Ollama 本地模型 |
| spring-ai-zhipuai | 1.0.x | 智谱 AI 集成 |
| spring-ai-deepseek | 1.0.x | DeepSeek 集成 |
| spring-ai-minimax | 1.0.x | MiniMax 集成 |
| spring-ai-milvus | 1.0.x | Milvus 向量数据库 |
| spring-ai-qdrant | 1.0.x | Qdrant 向量数据库 |
| spring-ai-redis | 1.0.x | Redis 向量存储 |
| hutool | 5.x | Singleton 缓存、工具类 |

## 设计原则

- **策略模式**：通过 `AiModelFactory` 统一创建不同平台的 AI 模型实例
- **工厂模式**：`AiModelFactoryImpl` 负责创建 ChatModel、ImageModel、EmbeddingModel
- **单例缓存**：使用 Hutool Singleton 缓存 AI 客户端实例，避免重复创建
- **Spring AI 集成**：基于 Spring AI 框架实现多模型统一抽象
- **开放-封闭原则**：新增 AI 平台只需扩展 `AiPlatformEnum` 和工厂方法
- **接口隔离**：Service 层接口按领域划分，职责单一

## 扩展指南

### 新增 AI 平台
1. `AiPlatformEnum` 添加枚举值
2. `AiModelFactoryImpl` 添加模型创建方法
3. 如需自定义模型类，在 `framework/ai/core/model/` 下创建
4. `YudaoAiProperties` 添加配置属性
5. `AiAutoConfiguration` 添加自动配置

### 新增 AI 能力类型
1. `AiModelTypeEnum` 添加新类型
2. 创建对应 DO 实体类
3. 创建 Controller / Service / Mapper
4. `AiModelFactory` 添加对应模型获取方法

## 最佳实践

- 模型实例缓存：使用 `Singleton.get()` 缓存，避免重复创建连接
- 流式响应优先：聊天推荐使用流式接口，用户体验更好
- 错误处理：捕获 AI 调用异常，记录 `errorMessage` 字段
- 向量存储选择：生产推荐 Milvus / Qdrant，测试可用 SimpleVectorStore
- 知识库分片：根据文档特点选择分片策略（语义分片、Markdown QA 分片）
- 多模态支持：`ChatMessage` 支持携带 `attachmentUrls` 实现多模态对话

## 关键文件

| 文件 | 说明 |
|------|------|
| `framework/ai/core/model/AiModelFactory.java` | AI 模型工厂接口 |
| `framework/ai/core/model/AiModelFactoryImpl.java` | AI 模型工厂实现 |
| `enums/model/AiPlatformEnum.java` | AI 平台枚举（20+） |
| `enums/model/AiModelTypeEnum.java` | 模型类型枚举 |
| `service/model/AiModelService.java` | 模型配置服务 |
| `service/chat/AiChatMessageService.java` | 聊天消息服务 |
| `service/knowledge/AiKnowledgeService.java` | 知识库服务 |
| `framework/ai/config/AiAutoConfiguration.java` | AI 自动配置类 |

## 详细文档

- [api-chat.md](api-chat.md) - 聊天对话 API
- [api-image.md](api-image.md) - 图像生成 API
- [api-model.md](api-model.md) - 模型配置 API
- [api-knowledge.md](api-knowledge.md) - 知识库 API
- [api-music.md](api-music.md) - 音乐生成 API
- [api-write.md](api-write.md) - 写作助手 API
- [api-mindmap.md](api-mindmap.md) - 思维导图 API
- [api-workflow.md](api-workflow.md) - 工作流 API
- [data-model.md](data-model.md) - 数据模型
- [pitfalls.md](pitfalls.md) - 常见陷阱
