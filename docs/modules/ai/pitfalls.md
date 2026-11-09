# 注意事项与已知坑点

> 使用 ai 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 AI 模块的数据表不做租户隔离

**问题**: 误以为 `ai_model`、`ai_api_key`、`ai_chat_role`、`ai_workflow`、`ai_knowledge` 等数据按租户隔离，实际上所有租户共享同一套模型、密钥与知识库；"我的"类接口（如 `/ai/image/my-page`）只按 `userId` 过滤，与租户无关。

**原因**: 模块 15 个 DO 全部继承 `BaseDO` 而非 `TenantBaseDO`。框架的 `TenantDatabaseInterceptor#computeIgnoreTable` 对未继承 `TenantBaseDO` 的实体自动跳过租户 SQL 拼接；模块虽然依赖 `yudao-spring-boot-starter-biz-tenant`，但只用于 `@TenantIgnore`、`TenantUtils` 等工具，并不代表数据已隔离。

**解决**: 需要租户隔离时，将对应 DO 改为继承 `TenantBaseDO` 并给表补充 `tenant_id` 列；跨租户共享的数据（模型、密钥）保持 `BaseDO` 即可。新增 DO 时要明确这个选择，不要默认照抄。

### 1.2 SSE 流式回调线程不透传租户上下文

**问题**: 在聊天/写作/思维导图的流式接口回调里追加数据库操作时，出现租户相关异常或查询不到数据。

**原因**: `sendChatMessageStream`、`generateWriteContent`、`generateMindMap` 返回 Reactor `Flux`，`doOnComplete`/`doOnError`/`doOnCancel` 回调在 Reactor 线程执行，`TenantContextHolder` 不会跨线程透传（源码注释："忽略租户，因为 Flux 异步无法透传租户"）。

**解决**: 在请求开始时先捕获当前 `tenantId`（写入请求日志快照），回调内的 DB 操作统一用 `TenantUtils.execute(tenantId, ...)` 包裹，参照 `AiChatMessageServiceImpl#finishChatStream`、`AiWriteServiceImpl`、`AiMindMapServiceImpl` 的写法。不要用 `TenantUtils.executeIgnore(...)` 处理需要租户上下文的写操作（它只是跳过租户条件，并不恢复上下文）；异步/回调链路上另外记录请求日志时，也沿用同一个捕获的租户。

### 1.3 Midjourney 回调端点是匿名入口

**问题**: `/admin-api/ai/image/midjourney/notify` 无需登录即可调用：可伪造通知把绘画改为"成功"，且 `imageUrl` 指向的任意文件会被服务端下载并转存进文件服务。

**原因**: `AiImageController#midjourneyNotify` 标注了 `@PermitAll + @TenantIgnore`（Midjourney Proxy 回调时无法携带登录态，只能匿名）；回调地址来自全局配置 `YudaoAiProperties.Midjourney#notifyUrl`，服务端对通知内容无签名校验。

**解决**: 生产环境通过网关或网络策略限制该路径仅允许 MJ Proxy 来源访问，或自行扩展 `MidjourneyApi` 增加签名校验；注意该端点必须保持 POST 方法（源码注释：必须是 POST 方法，否则会报错）。

## 2. 事务与流式落库相关

### 2.1 @Transactional 事务内包含远程 HTTP / 大模型调用

**问题**: 发消息、MJ 绘画、音乐生成接口偶发拖垮数据库连接池；模型调用失败时用户消息等本地记录一并回滚。

**原因**: 多个写操作把远程调用包进了事务：

- `AiChatMessageServiceImpl#sendMessage` 在 `@Transactional` 内同步执行 `chatModel.call(prompt)`（阻塞式 LLM 调用，可达数十秒）；
- `AiImageServiceImpl#midjourneyImagine` 在 `@Transactional` 内 `HttpUtil.downloadBytes` 下载垫图并调用 Midjourney Proxy；
- `AiMusicServiceImpl#generateMusic` 在 `@Transactional` 内调用 Suno API。

**解决**: 参照 `AiImageServiceImpl#drawImage` 的做法：事务（或无事务）内先落库，远程调用通过 `@Async` 的 `executeDrawImage` 后置执行；必须保留事务时，把远程调用移到事务边界之外，缩短事务持连接时间。

### 2.2 流式消息"先插空记录、流结束回填"存在残留窗口

**问题**: 流式对话后偶见 `content` 为空的 assistant 消息长期残留在 `ai_chat_message` 中。

**原因**: `sendChatMessageStream` 先插入 `content=""` 的 assistant 消息，之后完全依赖 `doOnComplete`（回填内容）、`doOnError`/`doOnCancel`（有内容保留、无内容删除）收尾；进程被强杀（kill -9、OOM）时这些回调不会执行，而 job 包只有 `AiMidjourneySyncJob`、`AiSunoSyncJob`，没有聊天消息补偿任务。

**解决**: 为"长时间为空的 assistant 消息"增加清理 Job；或扩展时给消息增加中间状态字段，落库与回填都围绕状态推进。

## 3. 异步任务相关

### 3.1 @Async 方法自调用不走代理

**问题**: 绘画异步逻辑被改成同步执行，HTTP 请求阻塞到大模型绘图结束才返回。

**原因**: `AiImageServiceImpl#executeDrawImage` 的 `@Async` 依赖 Spring AOP 代理，同类内 `this.executeDrawImage(...)` 不经过代理，注解失效。

**解决**: 参照 `drawImage` 的写法，通过 `getSelf()`（`SpringUtil.getBean(getClass())`）拿到代理对象再调用；新增异步方法沿用该模式，或拆分到独立 Bean。

```java
// AiImageServiceImpl#drawImage
getSelf().executeDrawImage(image, drawReqVO, model);
```

### 3.2 知识库切片异步失败后无补偿，段落缺向量

**问题**: 文档切片后部分段落无法被知识库召回，文档处理进度一直不完成，且没有报错提示。

**原因**: `AiKnowledgeSegmentService` 的 `createKnowledgeSegmentBySplitContentAsync`、`reindexByKnowledgeIdAsync` 是接口 default 方法上的 `@Async`，void 异步方法的异常被吞掉；`createKnowledgeSegmentBySplitContent` 先 `insertBatch` 落库、再逐段 `writeVectorStore`，中途失败后剩余段落 `vectorId` 停留在 `VECTOR_ID_EMPTY`，而 `searchKnowledgeSegment` 按 `selectListByVectorIds` 召回，空 `vectorId` 的段落永远召回不到。

**解决**: 出现缺向量时调用"重新索引"（`reindexKnowledgeSegmentByKnowledgeId`）重建；二次开发时在异步方法内 try-catch 并回写文档/段落状态，避免静默失败。

### 3.3 Midjourney 定时同步需按模型分组（已修复）

**问题（历史）**: 配置了多个 Midjourney 模型（不同 Proxy 地址/密钥）后，部分绘画任务永远停留在"进行中"，日志持续报"查询不到进展"。

**现状**: `AiImageServiceImpl#midjourneySync` 已改为按 `modelId` 分组、逐组用各自的 `MidjourneyApi` 查询 task，多 Proxy 配置可正常同步。未关联 `modelId` 的历史图片（早期 Action 生成）会被跳过并打 warn，依赖回调 `/midjourney/notify` 更新状态。

**仍要注意**: 新建绘画记录（含 Midjourney Action 生成的新记录）必须写入 `modelId`，否则无法被定时同步覆盖；扩展同步逻辑时保持"分组 + 各自 API"的写法，不要退回用第一条记录的 `modelId` 批量查询。

## 4. 缓存与模型客户端相关

### 4.1 知识库向量默认存储在本地文件（SimpleVectorStore）

**问题**: 多节点部署时各节点召回结果不一致；容器重建后向量文件丢失；更换知识库 Embedding 模型后召回质量莫名下降。

**原因**: `AiModelServiceImpl#getOrCreateVectorStore` 硬编码使用 `SimpleVectorStore`（Qdrant/Redis/Milvus 三行被注释）；`AiModelFactoryImpl#buildSimpleVectorStore` 把向量持久化到 `{user.home}/vector_store/simple_{EmbeddingModel类名}.json`，由 `Timer` 每分钟落盘一次。文件名只按 Embedding 模型类名区分、不按模型 id 区分，所有知识库的向量混存，检索时仅靠 `knowledgeId` 元数据过滤。

**解决**: 生产环境放开 `getOrCreateVectorStore` 中的注释，切换为 `buildQdrantVectorStore`/`buildRedisVectorStore`/`buildMilvusVectorStore` 之一；更换知识库的 Embedding 模型后必须重新索引，否则新旧向量空间混用。

### 4.2 平台客户端 Bean 受 yudao.ai.*.enable 开关控制

**问题**: 管理后台配好了豆包、硅基流动、Gemini 等平台的模型，运行时调用却报找不到 Bean。

**原因**: `AiModelFactoryImpl#buildChatModel` 通过 `SpringUtil.getBean(XxxChatModel.class)` 获取平台客户端，而 `AiAutoConfiguration` 中这些 Bean 由 `@ConditionalOnProperty`（如 `yudao.ai.doubao.enable`、`yudao.ai.gemini.enable`、`yudao.ai.mimo.enable`）控制注册；未开启时配置阶段不报错，直到调用才失败。TONG_YI/Ollama/OpenAI/DeepSeek/Anthropic/Azure 等由 Spring AI starter 自动装配，不受开关影响。小米 MiMo 是最新接入的第 22 个平台，Bean 受 `yudao.ai.mimo.enable=true` 控制，默认 `false`。

**解决**: 使用某平台前，在 `application.yaml` 打开对应的 `yudao.ai.{platform}.enable`。另外客户端以 `buildClientCacheKey`（含 apiKey、url）做 Singleton 缓存，修改密钥后会新建客户端，旧实例不会回收，频繁更换 Key 时注意内存占用。

## 5. 知识库检索相关

### 5.1 向量元数据与 Rerank 的隐式约定

**问题**: 自定义向量库实现或检索逻辑时，元数据写入报类型错误；开启 Rerank 后配置的"相似度阈值"看似失效；高频对话下数据库出现额外写压力。

**原因**: 三条隐式约定都集中在 `AiKnowledgeSegmentServiceImpl`：

- `writeVectorStore` 把 `knowledgeId/documentId/segmentId` 全部 `toString` 写入（部分 VectorStore 实现——如 QdrantVectorStore——不支持 Long），`VECTOR_STORE_METADATA_TYPES` 也全部声明为 `String.class`，查询 `filterExpression` 同样按字符串 eq；
- `searchDocument` 在 `rerankModel != null` 时按 `topK * RERANK_RETRIEVAL_FACTOR`（4 倍）检索并使用 `SIMILARITY_THRESHOLD_ACCEPT_ALL`，阈值改在 Rerank 之后生效，且 Rerank 选项硬编码为 `DashScopeRerankOptions`；
- `searchKnowledgeSegment` 每次召回都会 `updateRetrievalCountIncrByIds` 自增检索次数，查询带写副作用。

**解决**: 新增向量元数据字段保持 String 类型；调整阈值前先确认 Rerank 分支的存在；高频调用场景评估 `retrievalCount` 的写放大，必要时改为异步累计。

## 6. 错误码与命名相关

### 6.1 错误码冲突、笔误与易混淆命名

**问题**: 前端按 `code` 区分错误时，不同错误返回同一个码；开发者把 `AiChatRoleEnum` 当成聊天角色表实体使用。

**原因**: `ErrorCodeConstants` 存在多处编号问题：`1_040_009_102` 被 `KNOWLEDGE_DOCUMENT_FILE_EMPTY`、`KNOWLEDGE_DOCUMENT_FILE_DOWNLOAD_FAIL`、`KNOWLEDGE_DOCUMENT_FILE_READ_FAIL` 三个错误码重复使用；`CHAT_ROLE_DISABLE` 误用了 `MODEL_DISABLE` 的 `1_040_001_001`（聊天角色段应为 1_040_002_xxx）；`WRITE_STREAM_ERROR` 写成 `1_040_07_001`（少一位，写作段应为 1_040_007_xxx）。另外 `AiMusicServiceImpl#deleteMusicMy` 曾误抛绘画域的 `IMAGE_NOT_EXISTS`，现已在源码中修正为音乐域 `MUSIC_NOT_EXISTS`（`1_040_006_000`）。命名方面，`enums` 根包的 `AiChatRoleEnum` 是"写作助手/导图助手"两个内置角色的 systemMessage 枚举，与 `AiChatRoleDO`（ai_chat_role 表）没有任何关系。

**解决**: 扩展错误码前先检查 1_040 段内的唯一性；修复编号笔误属于不兼容变更（前端可能已按旧 code 判断），需统一评估后调整。引用聊天角色时注意区分：查库用 `AiChatRoleDO`/`AiChatRoleService`，内置提示词用 `AiChatRoleEnum`；`AiWriteServiceImpl`、`AiMindMapServiceImpl` 通过 `getChatRoleListByName(枚举.getName())` 按名称查找角色记录，找不到时回退枚举内置 systemMessage，重命名内置角色前需确认这层依赖。

## 7. 思考（Reasoning）档位相关

### 7.1 思考配置与平台强绑定

**问题**: 给模型配置了思考档位却保存失败或运行时无效；把同一个模型的思考参数复制到另一个平台的模型上。

**原因**: 思考参数按平台路由（`AiReasoningUtils.ReasoningRoute`）落地，不同平台的键规则完全不同：

| 路由 | 适用平台 | 键规则 |
|------|---------|--------|
| HTTP | DeepSeek、豆包、混元、硅基流动、文心、智谱、星火、MiniMax、月之暗面、百川、阶跃、MiMo | 整体合并进请求体，禁止 `model`、`messages`、`stream`、`stream_options`、`tools`、`tool_choice` 等 SDK 负责的顶层键 |
| OPENAI | OpenAI、Grok、Gemini（JDK17 走 OpenAI 兼容层） | `reasoning_effort` 写入强类型字段（必须非空字符串），其余键进 `extraBody`，键名不得与 SDK 强类型字段同名（如 `temperature`、`max_tokens`、`response_format` 等） |
| TONG_YI | 通义 | 只认 `enable_thinking`（必填布尔）与 `thinking_budget`（可选正整数） |
| UNSUPPORTED | AzureOpenAI、Anthropic、Ollama、StableDiffusion、Midjourney、Suno 等 | 不支持思考配置 |

另外校验要求：只有**对话模型**（type=1）能配置思考；模型平台必须与所属 API 密钥的平台一致。

**解决**: 新增平台的思考参数前先在 `AiReasoningUtils#getReasoningRoute` 确认路由，并按该路由的键规则实现校验；模型未配置思考（`reasoning_config` 为 null 或档位为空）时，请求里带 `reasoningLevel` 会抛「模型未配置思考」错误——这是预期行为，不是 Bug。

### 7.2 HTTP 路由的思考参数靠请求体补丁落地，限制较多

**问题**: 复用 DeepSeek 客户端的平台（如豆包、智谱）配了 `thinking` 之类的参数却没有任何效果；或者请求体不是 JSON 时直接报错。

**原因**: Spring AI 1.1.8 的 DeepSeek 请求是固定字段的 record，没有 thinking / reasoning_effort / extraBody 入口，因此 `AiRequestBodyPatcher` 在客户端的 HTTP 层对已序列化的 JSON 请求体做 RFC 7396 合并补丁。该补丁有明确的生效前提：请求体必须是**非空的 JSON 对象**、Content-Type 必须是 JSON、编码必须是 UTF-8；流式请求还要求一次性写出（不支持分段写出 `writeAndFlushWith`）。任何一项不满足都会直接抛异常，且**不会发出未打补丁的请求**。

**解决**: 不要把这些平台的思考参数塞进 SDK 强类型字段；保持请求体为单个 JSON 对象。补丁按"档位参数的规范化 JSON + sha256 哈希"参与客户端缓存键（`AiReasoningUtils#hashReasoningOptions`），参数变化会新建客户端实例，旧实例不会回收，频繁调整档位时注意内存占用。

## 8. 多模态与 Token 用量相关

### 8.1 input_modalities 为空时图片退化为 Base64 文本

**问题**: 模型明明支持看图，图片却被当成一长串 Base64 文本塞进提示词，模型"看不见"图片。

**原因**: 只有「附件是图片 **且** 模型的 `input_modalities` 包含 `image`」时，图片才会以 `Media`（`ByteArrayResource`）形式与文本放在同一条 `UserMessage` 中传输。`input_modalities` 为空（历史数据）时视为**仅支持 text**，图片会走旧的附件通道，转成 Base64 文本拼到提示词里。

**解决**: 接入多模态模型时，先在模型管理里把 `input_modalities` 配成 `["text","image"]`（枚举 `AiModelInputModalityEnum`：text / image / video）；否则前端传图也无效。

### 8.2 图片读取失败不降级，整轮消息不落库

**问题**: 用户发了张图，接口直接报错，且聊天记录里连用户消息都没有。

**原因**: 图片下载失败时抛 `CHAT_MESSAGE_IMAGE_READ_FAIL`，不做"降级为纯文本"的兜底；并且 Prompt 在**插入消息之前**构建，构建失败时不会插入 user / assistant 消息（流式接口返回错误帧）。

**解决**: 排查时先确认附件 URL 可直接访问、且服务器能出网下载；前端需要在发送前校验图片可访问性。若业务确实需要"图片读不到就当纯文本"，需要显式改造 `AiChatMessageServiceImpl#buildUserMessage`。

### 8.3 Token 用量未知就是 null，不做估算

**问题**: 统计里有的请求 Token 为 0、有的为空，前端展示对不上。

**原因**: `AiUsageUtils` 只提取厂商返回的 usage，未返回即为 null，不做任何估算；`totalTokens` 只有在 input 与 output **都已知**时才等于两者之和，否则为 null。流式场景取的是请求日志里的**最新整份快照**，不是逐帧累加。

**解决**: 统计接口用 `knownUsageCount` / `unknownUsageCount` 区分已知与未知用量，不要把 null 当成 0 参与求和。

## 9. 请求日志相关

### 9.1 请求日志走独立事务，并按捕获的租户上下文写入

**问题**: 主业务事务回滚后请求日志也丢了；或异步链路写日志时缺少租户上下文。

**原因**: `AiRequestLogServiceImpl#createRequestLog` 标注 `@Transactional(propagation = REQUIRES_NEW)`，与主事务独立；日志插入又在 `TenantUtils.execute(tenantId, ...)` 中执行，`tenantId` 来自请求开始时捕获的快照，避免 Reactor 回调线程丢失 `TenantContextHolder`。当前 ai 模块的表均不继承 `TenantBaseDO`（本身无 `tenant_id` 列），该包裹主要是保持上下文一致，为后续扩展留出余地。

**解决**: 在异步 / 回调链路里记录请求日志时，沿用同一个捕获的 `tenantId`，不要用 `TenantUtils.executeIgnore(...)`（它只跳过租户条件，不恢复上下文）；日志写入失败只打日志、不影响主流程（`finishChatStream` 等方法内部已 try-catch）。

### 9.2 ai:request-log:query 的菜单与按钮数据缺失

**问题**: `/ai/request-log` 三个接口在后台访问提示无权限。

**原因**: `AiRequestLogController` 的三个接口都标注 `@PreAuthorize("@ss.hasPermission('ai:request-log:query')")`，但仓库 `sql/` 目录的菜单初始化脚本中没有对应的菜单与按钮数据，权限标识未落到 `system_menu` 表。

**解决**: 部署时补一条菜单（或按钮）数据并把权限标识配置为 `ai:request-log:query`；参考 [菜单权限配置](../../../skills/usage/menu-permission.md) 的规范。
