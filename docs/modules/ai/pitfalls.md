# 注意事项与已知坑点

> 使用 ai 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 AI 模块的数据表不做租户隔离

**问题**: 误以为 `ai_model`、`ai_api_key`、`ai_chat_role`、`ai_workflow`、`ai_knowledge` 等数据按租户隔离，实际上所有租户共享同一套模型、密钥与知识库；"我的"类接口（如 `/ai/image/my-page`）只按 `userId` 过滤，与租户无关。

**原因**: 模块 14 个 DO 全部继承 `BaseDO` 而非 `TenantBaseDO`。框架的 `TenantDatabaseInterceptor#computeIgnoreTable` 对未继承 `TenantBaseDO` 的实体自动跳过租户 SQL 拼接；模块虽然依赖 `yudao-spring-boot-starter-biz-tenant`，但只用于 `@TenantIgnore`、`TenantUtils` 等工具，并不代表数据已隔离。

**解决**: 需要租户隔离时，将对应 DO 改为继承 `TenantBaseDO` 并给表补充 `tenant_id` 列；跨租户共享的数据（模型、密钥）保持 `BaseDO` 即可。新增 DO 时要明确这个选择，不要默认照抄。

### 1.2 SSE 流式回调线程不透传租户上下文

**问题**: 在聊天/写作/思维导图的流式接口回调里追加数据库操作时，出现租户相关异常或查询不到数据。

**原因**: `sendChatMessageStream`、`generateWriteContent`、`generateMindMap` 返回 Reactor `Flux`，`doOnComplete`/`doOnError`/`doOnCancel` 回调在 Reactor 线程执行，`TenantContextHolder` 不会跨线程透传（源码注释："忽略租户，因为 Flux 异步无法透传租户"）。

**解决**: 回调内的 DB 操作统一用 `TenantUtils.executeIgnore(...)` 包裹，参照 `AiChatMessageServiceImpl#sendChatMessageStream` 的 doOnComplete/doOnError/doOnCancel 写法；若回调中确实需要租户上下文（如写租户表），应改用 `TenantUtils.execute(tenantId, ...)` 显式传递。

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

### 3.3 Midjourney 定时同步假设所有任务共用一个 API 配置

**问题**: 配置了多个 Midjourney 模型（不同 Proxy 地址/密钥）后，部分绘画任务永远停留在"进行中"，日志持续报"查询不到进展"。

**原因**: `AiImageServiceImpl#midjourneySync` 用 `images.get(0).getModelId()` 构建 `MidjourneyApi`，即拿第一条记录的密钥去批量查询全部 `taskId`，其它配置下的任务自然查不到。

**解决**: 同步前按 `modelId` 分组，分别构建 `MidjourneyApi` 查询；或运维上约束 Midjourney 平台只配置一个可用模型。

## 4. 缓存与模型客户端相关

### 4.1 知识库向量默认存储在本地文件（SimpleVectorStore）

**问题**: 多节点部署时各节点召回结果不一致；容器重建后向量文件丢失；更换知识库 Embedding 模型后召回质量莫名下降。

**原因**: `AiModelServiceImpl#getOrCreateVectorStore` 硬编码使用 `SimpleVectorStore`（Qdrant/Redis/Milvus 三行被注释）；`AiModelFactoryImpl#buildSimpleVectorStore` 把向量持久化到 `{user.home}/vector_store/simple_{EmbeddingModel类名}.json`，由 `Timer` 每分钟落盘一次。文件名只按 Embedding 模型类名区分、不按模型 id 区分，所有知识库的向量混存，检索时仅靠 `knowledgeId` 元数据过滤。

**解决**: 生产环境放开 `getOrCreateVectorStore` 中的注释，切换为 `buildQdrantVectorStore`/`buildRedisVectorStore`/`buildMilvusVectorStore` 之一；更换知识库的 Embedding 模型后必须重新索引，否则新旧向量空间混用。

### 4.2 平台客户端 Bean 受 yudao.ai.*.enable 开关控制

**问题**: 管理后台配好了豆包、硅基流动、Gemini 等平台的模型，运行时调用却报找不到 Bean。

**原因**: `AiModelFactoryImpl#buildChatModel` 通过 `SpringUtil.getBean(XxxChatModel.class)` 获取平台客户端，而 `AiAutoConfiguration` 中这些 Bean 由 `@ConditionalOnProperty`（如 `yudao.ai.doubao.enable`、`yudao.ai.gemini.enable`）控制注册；未开启时配置阶段不报错，直到调用才失败。TONG_YI/Ollama/OpenAI/DeepSeek/Anthropic/Azure 等由 Spring AI starter 自动装配，不受开关影响。

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

**原因**: `ErrorCodeConstants` 存在多处编号问题：`1_040_009_102` 被 `KNOWLEDGE_DOCUMENT_FILE_EMPTY`、`KNOWLEDGE_DOCUMENT_FILE_DOWNLOAD_FAIL`、`KNOWLEDGE_DOCUMENT_FILE_READ_FAIL` 三个错误码重复使用；`CHAT_ROLE_DISABLE` 误用了 `MODEL_DISABLE` 的 `1_040_001_001`（聊天角色段应为 1_040_002_xxx）；`WRITE_STREAM_ERROR` 写成 `1_040_07_001`（少一位，写作段应为 1_040_007_xxx）。另外 `AiMusicServiceImpl#deleteMusicMy` 校验失败抛的是 `IMAGE_NOT_EXISTS`（"图片不存在!"）。命名方面，`enums` 根包的 `AiChatRoleEnum` 是"写作助手/导图助手"两个内置角色的 systemMessage 枚举，与 `AiChatRoleDO`（ai_chat_role 表）没有任何关系。

**解决**: 扩展错误码前先检查 1_040 段内的唯一性；修复编号笔误属于不兼容变更（前端可能已按旧 code 判断），需统一评估后调整。引用聊天角色时注意区分：查库用 `AiChatRoleDO`/`AiChatRoleService`，内置提示词用 `AiChatRoleEnum`；`AiWriteServiceImpl`、`AiMindMapServiceImpl` 通过 `getChatRoleListByName(枚举.getName())` 按名称查找角色记录，找不到时回退枚举内置 systemMessage，重命名内置角色前需确认这层依赖。
