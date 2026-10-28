# AI Agent 模块 (ai1)

> 参考 XXL-AI 优化重写的 AI Agent 能力模块，与旧 ai 模块（yudao-module-ai）定位互补：不再按平台枚举硬编码多家 SDK，而是基于 Spring AI 以 OpenAI 兼容协议统一接入 DeepSeek、GLM、Ollama(/v1) 等任意供应商模型。提供 Agent 编排（对话模型 + 系统指令 + 知识库 + MCP + SKILL 多选绑定）、SSE 流式对话（思考过程 + 回复双流）、知识库 RAG、MCP 工具、SKILL 技能、长期记忆等能力，生成链路基于 Redis Stream 消费组实现集群部署、断线续传与 worker 独立扩容。

## 模块概述

- **模块路径**: `yudao-module-ai1-springai`（单模块布局，无子模块拆分；当前在 `yudao-server/pom.xml` 中处于注释未启用状态）
- **业务定位**: 参考 XXL-AI 重新实现的 AI Agent 能力模块，采用「harness 编排层 + service 业务层」的分层结构。`harness` 包是平台调用大模型（`Ai1LlmChatTool` / `Ai1LlmModelFactory`）、MCP 服务（`Ai1McpClientTool` / `Ai1McpToolFactory`）、知识库 RAG（`Ai1RagTool`）、SKILL 物化（`Ai1SkillToolFactory`）、长期记忆（`Ai1MemoryTool` / `Ai1MemoryArchiveTool`）、供应商探测（`Ai1ProviderTool`）与会话流（`Ai1SessionStreamTool`）的客户端与工厂集合，模型可调用的工具在会话时才另行装配；Service 层只做校验与消息落库，流式生成与下发整体委托 `Ai1SessionStreamTool`。所有对话/嵌入模型统一按 OpenAI 兼容协议经 Spring AI 程序化构建，配置存数据库（支持 `${ENV}` 占位符，密钥留在环境变量），按「编号 + 配置指纹」Guava 缓存。
- **技术栈**: Spring Boot 2.7.18（本仓库 JDK8 分支根 pom 实际版本，模块按 Spring AI 1.x 设计、当前注释未启用，校验体系为 javax，见 [pitfalls.md](pitfalls.md) 1.1）+ Spring AI 1.x（BOM 管理：spring-ai-openai / spring-ai-client-chat / spring-ai-advisors-vector-store / spring-ai-milvus-store）+ MyBatis-Plus + Redisson（RStream / RLock / RTopic，原生 StringCodec）+ Milvus 向量库（milvus-sdk-java 3.0.10）+ MCP Java SDK 2.0.1（stdio / Streamable HTTP 客户端）+ spring-ai-agent-utils 0.13.0（SkillsTool 及 Shell / FileSystem / Glob / Grep / ListDirectory 执行工具）+ Quartz JobHandler

## 设计原则

| 原则 | 说明 |
|-----|------|
| harness 工具化、编排与业务解耦 | `harness/package-info` 明确定位：该包是平台调用大模型、MCP、知识库和 SKILL 的客户端与工厂，不是注册给模型调用的 function tool；Service 层只做校验与消息落库，流式生成与下发整体委托 `Ai1SessionStreamTool` |
| OpenAI 兼容协议统一接入 | 所有供应商的对话与嵌入模型都程序化构建为 `OpenAiChatModel` / `OpenAiEmbeddingModel`（DeepSeek、GLM、Ollama(/v1) 等），连接参数（baseUrl/apiKey/headers/completionsPath）在 Spring AI 1.x 的 `OpenAiApi` 边界适配；`normalizeBaseUrl` 裸地址自动补 `/v1` |
| 配置进 DB、密钥留环境 | Provider/模型/MCP/SKILL 配置存数据库并支持 `${ENV}` 占位符，仅在发起调用前经 `Ai1Utils.resolveSpringPlaceholders` 解析，接口响应仍返回占位符本身 |
| 无状态编排 + Redis Stream | 生成任务队列（消费组）、结果流（助手消息编号即结果流标识）、停止意图/通知、执行锁全放 Redis；生成与连接解耦——任意节点都能转发、续传，worker 可独立扩容；会话/消息/记忆水位线落 MySQL |
| Redisson 原生 RStream + StringCodec | 字段按纯字符串存储，刻意不用项目 RedisTemplate（JSON 序列化会破坏 Stream 字段），也不用 Spring Data opsForStream（阻塞读取无数据时抛 ClassCastException 且占满连接池） |
| 缓存 + 配置指纹 | 模型（providerId:modelId:配置指纹）、MCP 客户端/工具列表（编号+指纹）、向量存储（嵌入模型实例引用）、SKILL 快照（编号:更新时间指纹）都以指纹为 key，配置变化自然命中新 key 并淘汰旧实例；模型缓存 10 分钟过期兜底其他节点 |
| SKILL 物化执行 | 数据库文件树物化到 `agent_{agentId}` 本地沙箱，先清空再物化防残留，spring-ai-agent-utils 的 SkillsTool/ShellTools/FileSystemTools/Glob/Grep/ListDirectory 全部限定 allowedDirectory，Shell 后台进程由 `Ai1SkillShellTracker` 统一回收 |
| 降级与安全兜底 | RAG/记忆装配失败降级跳过并把提示写入思考流；RAG 集合按「调用方先在当前租户查出知识库再传入」防越权；SKILL 路径名 sanitize 防目录穿越；HTTP 探测异常信息脱敏；工具名超长用 sha256 摘要防冲突 |
| 多租户贯穿 | 全部 11 张业务表 100% 继承 TenantBaseDO；任务投递存在租户才携带 tenantId，worker 统一在 `TenantUtils.execute` 中还原租户上下文（禁止 executeIgnore）；归档 Job 用 @TenantJob 按租户执行 + Redisson 归档锁互斥 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| Agent 编排 | 以「providerId + modelId（对话模型）+ systemPrompt（系统指令）+ knowledgeBaseIds（RAG）+ mcpIds（MCP 工具）+ skillIds（SKILL 技能）+ memoryEnabled（长期记忆）」把平台能力聚合为一个可执行的智能体，status 开启后才可在「Agent 会话」中使用 | `Ai1AgentDO` |
| 会话与消息 | 会话创建/重命名/删除与消息落库；LLM 流式生成采用「落库占位 + Redis Stream 任务队列 + worker 异步生成 + 结果流回放」异步架构，SSE 连接与生成完全解耦，支持断线续传、停止生成、超时认领与多实例集群扩容 | `Ai1SessionDO`、`Ai1SessionMessageDO` |
| 模型与供应商 | 供应商维护 OpenAI 兼容端点的 baseUrl/apiKey/自定义 Header（支持 {session} 占位符），模型分对话与嵌入两种类型；提供连通测试（/models 优先，回退 /chat/completions）与远程模型拉取导入 | `Ai1ProviderDO`、`Ai1ModelDO` |
| 知识库 RAG | 知识库 → 文档 → 向量化 → 检索 → 对话注入全链路；文档纯文本存 MySQL（支持粘贴与 .txt/.md 上传），手动触发向量化（字符级分片 → OpenAI 兼容嵌入 → 写入 Milvus 集合 `knowledge_base_{id}`）；对话链路经 QuestionAnswerAdvisor 注入召回上下文，失败降级跳过 | `Ai1KnowledgeBaseDO`、`Ai1KnowledgeDocumentDO` |
| MCP 工具 | 管理端维护 MCP 配置（远程 Streamable HTTP / 本地 stdio 进程），提供连通测试（initialize + tools/list）；会话时由 `Ai1McpToolFactory` 把 MCP 工具桥接为 Spring AI FunctionToolCallback，LLM 以 function calling 方式调用 | `Ai1McpDO` |
| SKILL 技能 | Claude Agent Skills 风格的提示词能力包，以「管理信息表 + 内容文件树表」存储（SKILL.md 为入口，scripts/、reference/ 为固定目录），文件树级 CRUD；物化到本地沙箱目录并注册 SkillsTool 与执行类工具 | `Ai1SkillDO`、`Ai1SkillFileDO` |
| 长期记忆 | 每个「用户 × Agent」一条 Markdown 记忆（按用户画像/偏好习惯/关键事实/目标与意图/近期进展五个维度），归档 Job 按水位线增量生成；对话时开启 memoryEnabled 的 Agent 自动注入；管理端只提供查询/修改/删除 | `Ai1MemoryDO` |
| 工作台首页 | 资源总量（Agent/SKILL/MCP/模型数量）、近 N 天每日消息趋势、近 N 天各 Agent 消息排行三类只读统计，无独立表，由 `Ai1HomeMapper` 原生 @Select 聚合 | 无独立实体（`Ai1HomeMapper`） |

## API 接口索引

### Agent 编排 (Ai1AgentController)

前缀 `/ai1/agent`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/agent/create | POST | 创建 Agent（初始为关闭状态） | ai1:agent:create |
| /ai1/agent/update | PUT | 更新 Agent（状态不在此修改） | ai1:agent:update |
| /ai1/agent/delete | DELETE | 删除 Agent，级联删除会话与消息 | ai1:agent:delete |
| /ai1/agent/delete-list | DELETE | 批量删除 Agent，级联删除会话与消息 | ai1:agent:delete |
| /ai1/agent/get | GET | 获得 Agent 详情 | ai1:agent:query |
| /ai1/agent/page | GET | 获得 Agent 分页 | ai1:agent:query |
| /ai1/agent/simple-list | GET | 获得 Agent 精简列表（会话页选择器用） | 已认证 |
| /ai1/agent/update-status | PUT | 修改 Agent 状态（开启后才可在会话中使用） | ai1:agent:update |

### 工作台首页 (Ai1HomeController)

前缀 `/ai1/home`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/home/summary | GET | 获得总量统计（Agent、SKILL、MCP、模型数量） | ai1:home:query |
| /ai1/home/message-summary-by-date | GET | 获得按日消息统计：近 days 个自然日（含今天）每日消息数量，没有消息的日期补 0 | ai1:home:query |
| /ai1/home/message-summary-by-agent | GET | 获得按 Agent 消息统计：近 days 个自然日（含今天）各 Agent 的消息数量，按数量倒序 | ai1:home:query |

### 知识库 (Ai1KnowledgeBaseController)

前缀 `/ai1/knowledge`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/knowledge/create | POST | 创建知识库 | ai1:knowledge:create |
| /ai1/knowledge/update | PUT | 更新知识库 | ai1:knowledge:update |
| /ai1/knowledge/delete | DELETE | 删除知识库（连带删除文档与向量集合） | ai1:knowledge:delete |
| /ai1/knowledge/delete-list | DELETE | 批量删除知识库（连带删除文档与向量集合） | ai1:knowledge:delete |
| /ai1/knowledge/get | GET | 获得知识库 | ai1:knowledge:query |
| /ai1/knowledge/page | GET | 获得知识库分页 | ai1:knowledge:query |
| /ai1/knowledge/simple-list | GET | 获得知识库精简列表（只含开启状态，供 Agent 绑定下拉） | 已认证 |
| /ai1/knowledge/search | GET | 知识库检索测试 | ai1:knowledge:search |

### 知识文档 (Ai1KnowledgeDocumentController)

前缀 `/ai1/knowledge/document`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/knowledge/document/create | POST | 创建文档（粘贴文本） | ai1:knowledge-document:create |
| /ai1/knowledge/document/upload | POST | 上传文档（仅支持 .txt / .md 文本文件） | ai1:knowledge-document:create |
| /ai1/knowledge/document/update | PUT | 更新文档（内容变更后需重新向量化） | ai1:knowledge-document:update |
| /ai1/knowledge/document/delete | DELETE | 删除文档 | ai1:knowledge-document:delete |
| /ai1/knowledge/document/delete-list | DELETE | 批量删除文档 | ai1:knowledge-document:delete |
| /ai1/knowledge/document/get | GET | 获得文档（包含完整内容） | ai1:knowledge-document:query |
| /ai1/knowledge/document/page | GET | 获得文档分页（不返回文档内容） | ai1:knowledge-document:query |
| /ai1/knowledge/document/vectorize | POST | 文档向量化（返回分片数量） | ai1:knowledge-document:vectorize |
| /ai1/knowledge/document/vectorize-all | POST | 知识库批量向量化 | ai1:knowledge-document:vectorize |

### MCP 工具 (Ai1McpController)

前缀 `/ai1/mcp`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/mcp/create | POST | 创建 MCP | ai1:mcp:create |
| /ai1/mcp/update | PUT | 更新 MCP | ai1:mcp:update |
| /ai1/mcp/delete | DELETE | 删除 MCP | ai1:mcp:delete |
| /ai1/mcp/delete-list | DELETE | 批量删除 MCP | ai1:mcp:delete |
| /ai1/mcp/get | GET | 获得 MCP | ai1:mcp:query |
| /ai1/mcp/page | GET | 获得 MCP 分页 | ai1:mcp:query |
| /ai1/mcp/simple-list | GET | 获得 MCP 精简列表（只包含开启状态，用于 Agent 绑定 MCP 的下拉选择） | 已认证 |
| /ai1/mcp/test | POST | MCP 连通测试（initialize + tools/list） | ai1:mcp:test |

### 长期记忆 (Ai1MemoryController)

前缀 `/ai1/memory`。记忆由归档 Job 自动生成，无手工创建入口。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/memory/update | PUT | 更新长期记忆（仅正文） | ai1:memory:update |
| /ai1/memory/delete | DELETE | 删除长期记忆（之后根据历史对话重新生成） | ai1:memory:delete |
| /ai1/memory/delete-list | DELETE | 批量删除长期记忆（之后根据历史对话重新生成） | ai1:memory:delete |
| /ai1/memory/get | GET | 获得长期记忆 | ai1:memory:query |
| /ai1/memory/page | GET | 获得长期记忆分页 | ai1:memory:query |

### 模型 (Ai1ModelController)

前缀 `/ai1/model`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/model/create | POST | 创建模型 | ai1:model:create |
| /ai1/model/update | PUT | 更新模型 | ai1:model:update |
| /ai1/model/delete | DELETE | 删除模型 | ai1:model:delete |
| /ai1/model/delete-list | DELETE | 批量删除模型 | ai1:model:delete |
| /ai1/model/get | GET | 获得模型 | ai1:model:query |
| /ai1/model/page | GET | 获得模型分页 | ai1:model:query |
| /ai1/model/simple-list | GET | 获得模型精简列表（仅开启状态，用于 Agent 模型、知识库向量化模型下拉） | 已认证 |
| /ai1/model/remote-list | GET | 拉取供应商远程可用模型并标注是否已导入 | ai1:model:import |
| /ai1/model/import | POST | 批量导入远程模型，返回实际导入数量 | ai1:model:import |

### 供应商 (Ai1ProviderController)

前缀 `/ai1/provider`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/provider/create | POST | 创建供应商 | ai1:provider:create |
| /ai1/provider/update | PUT | 更新供应商（API 密钥为空表示保持原密钥） | ai1:provider:update |
| /ai1/provider/delete | DELETE | 删除供应商 | ai1:provider:delete |
| /ai1/provider/delete-list | DELETE | 批量删除供应商 | ai1:provider:delete |
| /ai1/provider/get | GET | 获得供应商（apiKey 脱敏返回） | ai1:provider:query |
| /ai1/provider/page | GET | 获得供应商分页（apiKey 脱敏） | ai1:provider:query |
| /ai1/provider/simple-list | GET | 获得供应商精简列表（仅开启状态，用于下拉选择） | 已认证 |
| /ai1/provider/test | POST | 供应商连通测试（GET /models 优先，失败时回退 POST /chat/completions） | ai1:provider:test |

### 会话 (Ai1SessionController)

前缀 `/ai1/session`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/session/create-my | POST | 创建【我的】会话 | ai1:session:my |
| /ai1/session/update-my | PUT | 修改【我的】会话标题 | ai1:session:my |
| /ai1/session/delete-my | DELETE | 删除【我的】会话，连带删除消息 | ai1:session:my |
| /ai1/session/my-list | GET | 获得【我的】会话列表（指定 Agent 下，按创建时间倒序） | ai1:session:my |
| /ai1/session/page | GET | 获得会话分页（管理端查看全部用户的会话） | ai1:session:query |

### 会话消息 (Ai1SessionMessageController)

前缀 `/ai1/session/message`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/session/message/my-list | GET | 获得【我的】会话消息列表 | ai1:session:my |
| /ai1/session/message/send-stream | POST | 发送消息（流式，SSE：事件 stream/thinking/message/ping/done/error，思考过程与回复双流输出） | ai1:session:my |
| /ai1/session/message/resume-stream | POST | 断线续传（流式，SSE），从结果流 lastEventId 之后继续转发，不重新生成 | ai1:session:my |
| /ai1/session/message/stop-my | POST | 停止【我的】会话生成，终止生成中的助手消息并保留已生成内容 | ai1:session:my |
| /ai1/session/message/page | GET | 获得会话消息分页（按消息编号倒序取最新页，页内按时间正序） | ai1:session:query |
| /ai1/session/message/list | GET | 获得会话消息列表（管理端查看任意用户的会话明细） | ai1:session:query |

### SKILL 技能 (Ai1SkillController)

前缀 `/ai1/skill`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/skill/create | POST | 创建 SKILL，自动播种固定文件 SKILL.md、scripts/、reference/ | ai1:skill:create |
| /ai1/skill/update | PUT | 更新 SKILL 的管理信息（名称/描述/版本/状态） | ai1:skill:update |
| /ai1/skill/delete | DELETE | 删除 SKILL，级联删除内容文件 | ai1:skill:delete |
| /ai1/skill/delete-list | DELETE | 批量删除 SKILL，级联删除内容文件 | ai1:skill:delete |
| /ai1/skill/get | GET | 获得 SKILL 详情 | ai1:skill:query |
| /ai1/skill/page | GET | 获得 SKILL 分页 | ai1:skill:query |
| /ai1/skill/simple-list | GET | 获得 SKILL 精简列表，只含开启状态，供 Agent 绑定 SKILL 的下拉选择 | 已认证 |

### SKILL 内容文件 (Ai1SkillFileController)

前缀 `/ai1/skill/file`。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ai1/skill/file/list | GET | 获得 SKILL 文件列表，平铺返回、不返回文件内容 | ai1:skill:query |
| /ai1/skill/file/get | GET | 获得 SKILL 文件（含内容），编辑时加载 | ai1:skill:query |
| /ai1/skill/file/create | POST | 创建 SKILL 目录或文件 | ai1:skill:update |
| /ai1/skill/file/rename | PUT | 重命名 SKILL 目录或文件，固定节点禁止 | ai1:skill:update |
| /ai1/skill/file/move | PUT | 移动 SKILL 目录或文件，不能移入自身或其后代 | ai1:skill:update |
| /ai1/skill/file/update-content | PUT | 保存 SKILL 文件内容，目录不支持 | ai1:skill:update |
| /ai1/skill/file/delete | DELETE | 删除 SKILL 目录或文件，目录递归删除后代 | ai1:skill:delete |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| ai1_provider | AI1 供应商（OpenAI 兼容端点） | TenantBaseDO | name、baseUrl、apiKey、headers（支持 {session} 占位符按会话隔离）、status |
| ai1_model | AI1 模型（挂在供应商下） | TenantBaseDO | providerId、name、model（模型标识）、type（0 对话 / 1 嵌入）、status |
| ai1_agent | AI1 Agent（智能体编排核心） | TenantBaseDO | name、introduction、providerId、modelId、systemPrompt、knowledgeBaseIds、mcpIds、skillIds（三组逗号分隔逻辑多对多）、memoryEnabled、status |
| ai1_knowledge_base | AI1 知识库（向量在 Milvus，不落 MySQL） | TenantBaseDO | name、description、embeddingProviderId、embeddingModelId、chunkSize、chunkOverlap、topK、status |
| ai1_knowledge_document | AI1 知识文档（原文存 MySQL） | TenantBaseDO | knowledgeBaseId、name、content、chunkCount、status（0 未处理 / 1 已向量化 / 2 失败） |
| ai1_session | AI1 会话（用户与 Agent 的一次会话） | TenantBaseDO | agentId、userId、title（默认「新会话」，首条提问后替换，上限 50 字符） |
| ai1_session_message | AI1 会话消息（助手消息编号即 Redis 结果流标识） | TenantBaseDO | sessionId、role（user / assistant）、reasoning（思考过程）、content、status（0 生成中 / 1 完成 / 2 失败） |
| ai1_memory | AI1 长期记忆（按 Agent + 用户归档） | TenantBaseDO | agentId、userId、content（Markdown 按维度分节）、lastMessageId（增量归档水位线） |
| ai1_mcp | AI1 MCP 服务连接配置 | TenantBaseDO | name、transport（http / stdio）、url、headers、config（完整 MCP 配置 JSON）、status |
| ai1_skill | AI1 SKILL（技能定义） | TenantBaseDO | name（兼作物化目录名，租户内唯一）、description、version、status |
| ai1_skill_file | AI1 SKILL 内容文件（parentId 目录树） | TenantBaseDO | skillId、parentId、name、type（0 目录 / 1 文件）、fileType、content、locked（固定节点不可删改移）、sort |

> 补充：分片向量存于 Milvus 集合 `{collectionPrefix}{知识库编号}`（默认 `knowledge_base_{id}`），不落 MySQL；Redis 键（任务流 `ai1:session:tasks`、结果流 `ai1:session:result:{messageId}`、停止意图、归档/快照锁等）与本地 SKILL 物化目录见 [data-model.md](data-model.md)。所有 DO 均标注 `@KeySequence`（如 `ai1_agent_seq`）。

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 工厂模式 + 配置指纹缓存 | `Ai1LlmModelFactory`（构建 OpenAiChatModel/OpenAiEmbeddingModel）、`Ai1McpToolFactory`（MCP 工具桥接为 FunctionToolCallback）、`Ai1SkillToolFactory`（物化并构建 SkillsTool + 执行类工具） | 按数据库运行时快照程序化构建，缓存 key 携带配置指纹，配合显式 evict/evictByProviderId/evictByModelId 失效与 TTL 兜底，双重检查锁 + 按 ID 串行初始化避免并发重建 |
| Redis Stream 生产者-消费者 + PEL 超时认领 | `Ai1SessionStreamTool` 的 submit / consumeLoop / reclaimTasks / handleTask（队列 `ai1:session:tasks`，消费组 `ai1-session-workers`） | 生成任务异步化：XADD 投递 → XREADGROUP 消费 → XACK 确认；listPending + claim 认领超时遗留任务实现 worker 故障接管；NOGROUP 时自动重建消费组 |
| 结果流断点续传 + 双写补偿 | `Ai1SessionStreamTool#streamResult`（XREAD 转发 + lastEventId 重放）、`#completeTaskResult`（终态补偿） | 助手消息编号即结果流标识，SSE 事件 id=条目编号实现续传；DB 回填与结果流写入非同一事务，补偿只补齐缺失 error/done 后才 XACK，接管任务不重跑、按结果流还原部分输出 |
| 装配-执行-回调骨架（模板方法思想） | `Ai1LlmChatTool.chat` | 固定「装配消息 → 附加 tools/advisors → 流式执行 → 增量回调」骨架，onThinking/onContent 由调用方注入，传输方式（SSE、Redis Stream）由调用方决定，记忆归档等场景复用 |
| 生命周期回调（SmartLifecycle） | `Ai1SessionStreamTool` implements SmartLifecycle；`Ai1McpClientTool` / `Ai1RagTool` 的 @PreDestroy | worker 依赖其他 Bean 与 Redis，容器刷新完成后启动；stop 时中断生成并逐线程 join 退出、统一等待 Shell 进程回收；@PreDestroy 释放 MCP 连接与 Milvus 连接 |
| 装饰器模式 | `Ai1SkillShellTracker` 实现 ExecBackend 包装 LocalExecBackend | 在第三方执行后端之上叠加进程生命周期管理：start 登记、cancel 按「移出集合」认领回收，幂等可并发，不侵入 agent-utils 实现 |
| 分布式锁 + Redisson 看门狗 | `SESSION_TASK_LOCK:{messageId}`（生成执行锁）、`Ai1MemoryLockRedisDAO`（归档锁 tryLock / 快照锁 lock） | 执行锁防并发生成与旧 worker 写入，每次写库/写流前校验锁归属；归档锁按租户互斥、抢不到跳过；快照锁使消息落库事务与归档读取互斥；锁不设租期由看门狗续期 |
| 水位线（Watermark）增量归档 + 写前 CAS | `Ai1MemoryArchiveTool.archiveOne/getNewMessageList`、`Ai1MemoryServiceImpl.createMemoryIfAgentExists/updateMemoryIfUnchanged` | 只取水位线之后到第一条 GENERATING 消息前的「安全前缀」SUCCESS 消息增量归档；写入前比对水位线与正文，人工改过/删除则放弃，保证人工操作不被覆盖 |
| 占位符延迟解析 | `Ai1Utils.resolveSpringPlaceholders`（${ENV}）、`Ai1LlmModelFactory.SESSION_PLACEHOLDER`（{session}）、`YudaoAi1Properties.Session.AGENT_NAME_PLACEHOLDER`（{agentName}） | 库中只存占位符、真实密钥留环境变量，仅调用前解析；{session} 支撑按会话隔离的请求 Header 与缓存 key；{agentName} 用于默认系统指令 |
| 降级容错（fail-soft） | `Ai1SessionStreamTool#generate`（RAG 装配失败跳过并把提示写入思考流）、`#injectMemory`、`Ai1McpToolFactory#buildTools`（单个 MCP 失败跳过） | 记忆/RAG 属增强能力，任何故障都不阻断主对话；单个 MCP 加载失败返回空列表且仅缓存成功结果，允许下次重试 |
| 适配器/桥接：外部能力 → Spring AI ToolCallback | `Ai1McpToolFactory#buildToolCallback`（FunctionToolCallback + 入参 JSON Schema 透传）、`Ai1SkillToolFactory#buildTools`（SkillsTool + Shell/FileSystem/Glob/Grep/ListDirectory） | 把 MCP 工具与 SKILL 执行能力统一包装为 Spring AI 工具回调，工具名 slugify + 64 字符截短 + sha256 摘要防重名 |
| 回退探测 | `Ai1ProviderTool.testConnect` | GET /models 优先，非认证失败（非 401/403）时回退 POST /chat/completions 最小请求体，兼容不实现 /models 的 OpenAI 兼容服务 |
| 反向引用计数防误删 | `Ai1AgentMapper.selectCountByModelIds/selectCountByKnowledgeBaseIds/selectCountBySkillIds`、`Ai1ModelMapper.selectCountByProviderIds`、`Ai1KnowledgeBaseMapper.selectCountByEmbeddingModelIds` | 删除被 Agent 引用的 Provider/模型/知识库/SKILL 前先 selectCount，命中则抛对应错误码，替代外键约束 |

## 依赖关系

- **上游**（本模块依赖）
  - 业务模块: `yudao-module-system`（用户、部门、租户等系统能力，AdminUserApi 查询用户昵称）、`yudao-module-infra`（文件、配置等基础设施能力）
  - framework starter: `yudao-spring-boot-starter-biz-tenant`（多租户，任务投递携带 tenantId、@TenantJob）、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-redis`（Redis/Redisson：RStream、RLock、RTopic、RBucket）、`yudao-spring-boot-starter-test`
  - 三方 AI: Spring AI（spring-ai-openai 对话/嵌入模型，spring-ai-client-chat，spring-ai-advisors-vector-store 的 QuestionAnswerAdvisor，spring-ai-milvus-store 向量存储，版本由 spring-ai-bom 管理）、`milvus-sdk-java` 3.0.10、`spring-ai-agent-utils` 0.13.0（SkillsTool 技能系统及 Shell/FileSystem/Glob/Grep/ListDirectory 执行工具）、`mcp-json-jackson2` 2.0.1（官方 Java MCP SDK，stdio / Streamable HTTP 客户端）
- **下游**（依赖本模块）
  - `yudao-server` 聚合引用（当前 `yudao-server/pom.xml` 第 112-116 行处于注释未启用状态，启用需取消该段注释后随 yudao-server 打包；无其他业务模块依赖 ai1 模块）

## 对外暴露的 API

本模块未提供 `api` 包与跨模块 Api 接口，仅通过 `yudao-server` 以 HTTP 方式对外提供服务（当前处于注释未启用状态）。

## 详细文档

- [api-agent.md](api-agent.md) - Agent 编排（模型/知识库/MCP/SKILL 多选绑定与会话链路编排）
- [api-home.md](api-home.md) - 工作台首页（总量、每日消息趋势、Agent 消息排行）
- [api-knowledge.md](api-knowledge.md) - 知识库 RAG（文档、向量化、检索测试）
- [api-mcp.md](api-mcp.md) - MCP 工具接入（连通测试与工具桥接）
- [api-memory.md](api-memory.md) - 长期记忆（增量归档与水位线）
- [api-model.md](api-model.md) - 供应商与模型（连通测试、远程模型导入）
- [api-session.md](api-session.md) - 会话与消息（SSE 流式、断线续传、停止生成）
- [api-skill.md](api-skill.md) - SKILL 技能（文件树管理与物化执行）
- [data-model.md](data-model.md) - 数据模型详情（DO、Redis 键、Milvus 集合与物化目录）
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南（新增供应商/MCP/SKILL/配置项步骤、关键文件索引）
