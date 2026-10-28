# AI1 Agent 代码模式与扩展指南 (ai1)

> 本文档描述 `yudao-module-ai1-springai` 模块（参考 XXL-AI 重新实现的 AI Agent 能力）的分层结构、代码模式、扩展指南与关键文件索引。格式风格与 [AI 大模型模块 (ai)](../ai/code-patterns.md) 对齐，内容全部来自 ai1 模块源码。

## 模块分层结构

模块在 yudao 标准 `controller / service / dal / framework` 之外，新增了独立的 `harness` 编排层，五层职责边界由 [harness/package-info.java](../../../yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/package-info.java) 明确约定：

```text
cn.iocoder.yudao.module.ai1
├── controller/admin   # HTTP 接口层：VO 校验、权限标识、拼接关联名称
├── service            # 业务逻辑层：CRUD 校验、消息落库、生成编排的发起入口
│   └── model/bo       # Ai1ModelRespBO：模型运行时参数快照（跨层契约）
├── dal
│   ├── dataobject     # DO 实体（Agent/会话/记忆/模型/知识库/MCP/SKILL）
│   ├── mysql          # MyBatis Mapper
│   └── redis          # Redis Key 常量 + Redisson 锁 DAO
├── harness            # 平台调用大模型/MCP/知识库/SKILL 的客户端与工厂（非 function tool）
│   ├── llm            # Ai1LlmChatTool / Ai1LlmModelFactory
│   ├── mcp            # Ai1McpClientTool / Ai1McpToolFactory
│   ├── rag            # Ai1RagTool（Milvus）
│   ├── skill          # Ai1SkillToolFactory / Ai1SkillShellTracker
│   ├── memory         # Ai1MemoryTool / Ai1MemoryArchiveTool
│   ├── model          # Ai1ProviderTool（HTTP 探测）
│   └── session        # Ai1SessionStreamTool（投递/worker/结果流/SSE 转发一体）
├── framework          # 极薄：只注册配置属性与 Swagger 分组
├── job                # 定时任务（JobHandler + @TenantJob）
├── enums              # 错误码与业务枚举
└── util               # Ai1Utils 静态工具
```

| 层 | 职责 | 边界约定 |
|---|------|---------|
| controller | 接口校验、`@PreAuthorize` 权限、VO 拼接 | 不持有业务状态；关联名称在 Controller 用 `getXxxMap` + `MapUtils.findAndThen` 回填 |
| service | 业务校验、事务落库 | 流式生成整体委托 `Ai1SessionStreamTool`，Service 不直接调模型 |
| harness | 调用外部资源的客户端与工厂 | **不是**注册给模型调用的 function tool；模型可调用的工具在会话时由 MCP/SKILL 工厂另行装配 |
| framework | 自动装配 | `Ai1AutoConfiguration` 只注册 `YudaoAi1Properties`；模型/向量存储/MCP 均由 harness 程序化构建，不注册 Bean |
| dal/redis | Redisson 原生操作 | Stream 一律 `RStream + StringCodec`，不用项目 RedisTemplate |

## 代码模式

### Controller 层规范

- 注解组合：`@Tag(name = "管理后台 - AI1 XXX")`、`@RestController`、`@RequestMapping("/ai1/xxx")`、`@Operation(summary = "xxx")`
- 权限标识：`@PreAuthorize("@ss.hasPermission('ai1:域:动作')")`，用户侧读写统一用 `ai1:session:my`
- 「我的」数据归属校验收口在 `Ai1SessionService#validateSessionMy(userId, id)`，失败统一抛 `SESSION_NOT_EXISTS`

```java
@Tag(name = "管理后台 - AI1 Agent")
@RestController
@RequestMapping("/ai1/agent")
@Validated
public class Ai1AgentController {

    @PostMapping("/create")
    @Operation(summary = "创建 Agent")
    @PreAuthorize("@ss.hasPermission('ai1:agent:create')")
    public CommonResult<Long> createAgent(@Valid @RequestBody Ai1AgentSaveReqVO createReqVO) {
        return success(agentService.createAgent(createReqVO));
    }
}
```

流式接口（发送/续传）用 `SseEmitter` 而非 `Flux`，`produces = MediaType.TEXT_EVENT_STREAM_VALUE`；校验失败不抛异常，返回只含 `error` 事件的 SSE。

### Service 层规范

- 接口 + Impl 模式；`@Resource` 注入依赖
- 同类自调用 `@Transactional` 方法时，通过 `getSelf()`（`SpringUtil.getBean(getClass())`）取代理保证事务生效
- 与 harness 双向依赖处用 `@Resource @Lazy` 打破循环依赖

```java
// Ai1SessionMessageServiceImpl：快照锁内经代理调用事务方法
Long messageId = memoryLockRedisDAO.lockSnapshot(session.getAgentId(), session.getUserId(),
        () -> getSelf().createRoundMessages(session, sendReqVO.getContent()));

private Ai1SessionMessageServiceImpl getSelf() {
    return SpringUtil.getBean(getClass());
}
```

业务校验方法 `validateXxxExists` 统一「不存在即抛错误码、存在则返回 DO」，避免二次查询；接口另提供 `default` 方法 `getXxxMap/getXxxList` 供跨域引用计数与名称回填复用。

### 数据访问层（DAL）规范

- MySQL：Mapper 继承 `BaseMapperX`，通用查询封装为接口 `default` 方法，用 `LambdaQueryWrapperX` 的 `eqIfPresent/likeIfPresent`
- DO 继承 `TenantBaseDO`（Agent/会话/记忆等租户表）；Agent 的集合绑定字段用 `@TableField(typeHandler = LongListTypeHandler.class)` 存 JSON 数组，DO 必须保持 `autoResultMap = true`

```java
@TableName(value = "ai1_agent", autoResultMap = true)
public class Ai1AgentDO extends TenantBaseDO {

    @TableField(typeHandler = LongListTypeHandler.class)
    private List<Long> knowledgeBaseIds;   // MCP、SKILL 同构
}
```

- JSON 数组列做引用计数时不能用 `IN`，用 `MyBatisUtils.findInSet` 拼 `FIND_IN_SET`（见 `Ai1AgentMapper#selectCountBySkillIds`）
- Redis：`Ai1RedisKeyConstants` 集中定义 key 与多租户约定（结果流 key 不带 tenantId、由字段隔离）；锁封装在 `Ai1MemoryLockRedisDAO`，不设租期、由 Redisson 看门狗续期
- 统计类查询（`Ai1HomeMapper`）用原生 `@Select` + 标量子查询，列别名与 VO 字段同名直接映射；**原生 SQL 必须手写 `deleted = FALSE`**（不享受 `@TableLogic` 自动拼接），日期聚合用 `CAST(create_time AS DATE)` 兼容 MySQL/H2 单测

### harness 层规范（AI 调用统一入口）

业务层不直接依赖 Spring AI SDK，统一经 harness 工具调用：

- 模型获取：`Ai1ModelService#getModelRespBO(providerId, modelId)` 校验后组装不可变快照 `Ai1ModelRespBO`（modelId/model/modelType + providerId/baseUrl/apiKey/headers，`${ENV}` 占位符已解析），harness 不反查 DB、不感知租户
- 对话执行：`Ai1LlmChatTool#chat(model, systemPrompt, histories, content, tools, advisors, sessionId, onThinking, onContent)` 只执行一次流式会话，通过 `Consumer<String>` 回调思考/回复增量；传输方式（SSE、Redis Stream）由调用方决定，记忆归档等场景复用同一入口
- 增量回调来自两个 channel：`metadata.get("reasoningContent")` → onThinking、`getText()` → onContent；只含 usage 无输出的尾部分片直接跳过防 NPE

```java
// Ai1LlmChatTool#chat 内部：tools 参数中混有 MCP/SKILL 的 ToolCallback 与 @Tool 对象：前者 instanceof 直接加入，后者经 ToolCallbacks.from 转换
List<ToolCallback> callbacks = new ArrayList<>();
for (Object tool : tools) {
    if (tool instanceof ToolCallback callback) { callbacks.add(callback); }
    else { callbacks.addAll(Arrays.asList(ToolCallbacks.from(tool))); }
}
// spec.toolCallbacks(callbacks) 统一注册，不能直接传 @Tool 对象
```

### 异常处理

错误码前缀为 `1-041-XXX-XXX`，按域分段（定义于 `enums/Ai1ErrorCodeConstants.java`）：

| 分段 | 域 | 典型错误码 |
|-----|-----|-----------|
| 1_041_000_xxx | 供应商 | `PROVIDER_NOT_EXISTS`、`PROVIDER_HEADERS_INVALID`、`CONFIG_PLACEHOLDER_NOT_RESOLVED` |
| 1_041_001_xxx | 模型 | `MODEL_TYPE_NOT_CHAT`、`MODEL_USED_BY_AGENT`、`MODEL_IMPORT_ALL_EXISTS` |
| 1_041_002_xxx | 知识库 | `KNOWLEDGE_BASE_USED_BY_AGENT` |
| 1_041_003_xxx | 知识文档 | `KNOWLEDGE_DOCUMENT_VECTORIZE_FAIL` |
| 1_041_004_xxx | MCP | `MCP_COMMAND_REQUIRED`（stdio 必须配 command）、`MCP_URL_REQUIRED` |
| 1_041_005/006_xxx | SKILL/文件 | `SKILL_USED_BY_AGENT`、`SKILL_FILE_LOCKED` |
| 1_041_007/008/009/010_xxx | Agent/会话/消息/记忆 | `AGENT_DISABLE`、`SESSION_NOT_EXISTS`、`SESSION_MESSAGE_NOT_EXISTS` |

### 统一响应

- 成功：`CommonResult.success(data)`；失败：`CommonResult.error(ErrorCode)`
- SSE 事件 data 统一为 JSON 字符串（`JsonUtils.toJsonString(StrUtil.nullToEmpty(data))`）

## 核心技术模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| harness 工具化 | `harness/` 全部 `*Tool` / `*Factory` | 编排（`Ai1SessionStreamTool#generate`）与执行（`Ai1LlmChatTool#chat`）分离；编排失败一律降级跳过（RAG/记忆提示写入思考流），不中断对话 |
| 工厂 + 配置指纹缓存 | `Ai1LlmModelFactory`（Guava Cache，容量 128、写入后 10 分钟过期） | 缓存 key = `providerId:modelId:Objects.hash(配置指纹)[:sessionKey]`；配置变化自然命中新 key，Service 变更时显式 `evictByModelId/evictByProviderId`（仅本节点，其他节点靠 TTL 收敛） |
| Redis Stream 生产者-消费者 | `Ai1SessionStreamTool`：任务流 `ai1:session:tasks` + 消费组 `ai1-session-workers` | XADD 投递 → XREADGROUP 消费 → XACK 确认；`reclaimTasks` 认领 PEL 超时任务（接管不重跑）；实现 SmartLifecycle 启停 worker；Redisson 原生 `RStream + StringCodec` 纯字符串存取 |
| 结果流断点续传 | 助手消息编号即结果流 `ai1:session:result:{messageId}` 标识 | SSE 事件 id = 结果流条目编号，携带 lastEventId 从断点重放不重新生成；DB 回填与结果流写入非同一事务，XACK 前由 `completeTaskResult` 补齐缺失终态 |
| SKILL 物化执行 | `Ai1SkillToolFactory`（spring-ai-agent-utils 0.13.0） | DB 文件树物化到 `${yudao.ai1.skill.root}/agent_{agentId}`，按「编号:更新时间」指纹整目录重建（先清空防残留）+ `.fingerprint` 标记文件；Shell 后台进程经 `Ai1SkillShellTracker`（装饰器实现 ExecBackend）登记回收 |
| MCP 桥接 | `Ai1McpToolFactory` + `Ai1McpClientTool`（MCP SDK 2.0.1） | 工具名 = `slugify(MCP名称) + "__" + 原始名`，超 64 字符截短 + sha256 摘要防重名；客户端按「编号+指纹」缓存（闲置 30 分钟过期），`callTool` 在 `synchronized(client)` 内串行 |
| 水位线增量归档 | `Ai1MemoryArchiveTool` + `Ai1MemoryLockRedisDAO` | 只取水位线之后、第一条 GENERATING 之前的「安全前缀」（≤100 条），写入前 CAS 比对防覆盖人工修改；锁顺序固定「归档锁 → 快照锁」 |
| RAG 收口 | `Ai1RagTool`（Milvus + QuestionAnswerAdvisor） | 建集合/分片/检索/清理全部收口；向量存储缓存项记录嵌入模型实例引用，实例变化即重建；集合名 = `knowledge_base_{知识库编号}`，调用方必须先在当前租户查出知识库再传入 |
| 占位符装配 | `Ai1Utils#resolveSpringPlaceholders` + `{session}` + `{agentName}` | 库中只存 `${ENV}`/`{session}` 占位符，调用前边界处解析；密钥留环境变量，接口响应返回占位符原文 |

### Redis Key 约定

会话流与长期记忆的 Redis key 集中定义于 `dal/redis/Ai1RedisKeyConstants.java`，全部用 Redisson 原生 `RStream/RLock/RTopic/RBucket + StringCodec`：

| KEY 格式 | 数据类型 | 用途与多租户约定 |
|---------|---------|----------------|
| `ai1:session:tasks` | Stream（字段 tenantId/messageId/agentId/sessionId/content） | 任务队列，所有租户共用，KEY 不带 tenantId，worker 从字段还原租户上下文 |
| `ai1-session-workers` | Stream 消费组 | 生成 worker 消费组，NOGROUP 时自动重建 |
| `ai1:session:task-lock:{messageId}` | RLock | 单条消息生成执行锁，按助手消息编号隔离，看门狗续期 |
| `ai1:session:result:{messageId}` | Stream（字段 type/data） | 结果流，messageId 全局唯一故 KEY 不带 tenantId |
| `ai1:session:stop:{messageId}` | String | 停止意图，覆盖排队中与其他节点执行中的任务 |
| `ai1:session:stop` | RTopic | 停止通知广播，即时唤醒执行节点中断生成 |
| `ai1:memory:archive-lock:{tenantId}` | RLock | 归档锁按租户互斥（tryLock 不等待，抢不到跳过） |
| `ai1:memory:snapshot-lock:{agentId}:{userId}` | RLock | 快照锁：消息落库事务与归档读取互斥（Agent 编号全局唯一，不带 tenantId） |

## 关键链路

### 消息发送端到端

```text
用户发消息
  → Ai1SessionMessageController#sendSessionMessageStream（POST /ai1/session/message/send-stream，ai1:session:my）
  → Ai1SessionMessageServiceImpl#sendSessionMessageStream
      校验会话归属 validateSessionMy + Agent 已开启 validateAgentEnabled
      → 快照锁 lockSnapshot(agentId, userId) 内 getSelf().createRoundMessages(...)：
        首条消息自动生成会话标题 → 落库 user 消息（SUCCESS）+ assistant 占位（GENERATING）
  → Ai1SessionStreamTool#submit：XADD 任务队列（maxLen 5000 近似裁剪）
  → Ai1SessionStreamTool#open：SseEmitter 提交有界线程池，先下发 stream 事件（data=助手消息编号）
      随后 streamResult 从结果流 XREAD 转发 SSE 事件（thinking/message/ping/done/error）

worker 侧（SmartLifecycle start 拉起，默认 4 线程）
  → consumeLoop：每 60s reclaimTasks 认领 PEL 超时任务 + XREADGROUP 阻塞消费
  → handleTask：tryLock 执行锁 → TenantUtils.execute(tenantId) → executeTask
  → generate 编排：
    ① validateAgentExists 重新校验（任务可能路由到其他节点）
    ② getModelRespBO + Ai1ModelTypeEnum.isChat 校验
    ③ 取最近 history.limit（默认 20）条历史（跳过 GENERATING 占位、移除末尾当前提问）
    ④ 系统指令（缺省用 default-system-prompt 替换 {agentName}）+ 记忆注入（失败降级）
    ⑤ MCP + SKILL 工具装配
    ⑥ RAG Advisor（失败降级跳过并把提示写入思考流）
    ⑦ Ai1LlmChatTool#chat 流式执行，增量回调写结果流
  → 收尾：saveAssistantMessage 回填 + appendResult(done) + XACK
```

### 长期记忆归档

```text
infra 定时任务触发 Ai1MemoryArchiveJob#execute（@TenantJob 逐租户）
  → Ai1MemoryArchiveTool#archive：tryLockArchive 抢租户归档锁（抢不到跳过）
  → 遍历开启且 memoryEnabled 的 Agent × 其下用户 archiveOne：
    ① 读水位线 lastMessageId → failStaleMessages 收尾超时孤儿生成
    ② 快照锁内读「安全前缀」（水位线后、第一条 GENERATING 前，≤100 条 SUCCESS 消息）
    ③ Ai1MemoryTool#generate 按 MEMORY_SECTIONS 五维度生成（用户画像/偏好习惯/关键事实/目标与意图/近期进展）
       → Ai1Utils.normalizeMemoryMarkdown 规范化 + limitLength 截断
    ④ 首次 createMemoryIfAgentExists / 再次 updateMemoryIfUnchanged（CAS 防覆盖人工修改）→ 推进水位线
```

## 扩展指南

### 新增模型供应商

无需改代码——所有供应商统一走 OpenAI 兼容协议（DeepSeek、GLM、Ollama `/v1` 等）：

1. 管理后台创建 Provider（baseUrl + apiKey + headers，密钥用 `${ENV}` 占位符，Header 支持 `{session}` 占位符按会话隔离）
2. 添加模型，或用「远程模型导入」（`Ai1ProviderTool#listModels` 拉 `GET /models` 解析 `data[].id`）
3. `Ai1LlmModelFactory` 按 `providerId:modelId:配置指纹` 自动构建并缓存，配置变更由对应 Service 显式失效

若供应商非 OpenAI 兼容协议，需在 `harness/llm/Ai1LlmModelFactory` 扩展新的模型构建分支（当前仅 OpenAI 兼容一种），连接参数在 `OpenAiApi` 边界适配而非模型 Options。

### 新增 MCP 服务

1. 管理后台创建 MCP：transport 选 `http`（Streamable HTTP，url + headers）或 `stdio`（config JSON 配 command/args/env）
2. Agent 保存时绑定 `mcpIds`，会话时 `Ai1McpToolFactory#buildTools` 自动经 `tools/list` 桥接为 `FunctionToolCallback`（入参 JSON Schema 透传）
3. 用「连通测试」（`Ai1McpClientTool#testConnect`，临时客户端 initialize + listTools）验证

新增 MCP 配置字段时，除了 DO/VO/建表 SQL，**必须把新字段纳入 `buildCacheKey` 的 `Objects.hash` 指纹**，否则修改该字段不会触发客户端重建。

### 新增 SKILL

1. SKILL 管理中创建文件树（根级 `SKILL.md` 必需，缺失则只物化文件不注册技能）
2. Agent 绑定 `skillIds`，`Ai1SkillToolFactory` 按指纹自动物化重建沙箱
3. 需要新执行能力时，在 `Ai1SkillToolFactory#buildTools` 追加 agent-utils 工具（当前固定 Shell/FileSystem/Glob/Grep/ListDirectory，均限定 `allowedDirectory`）；会启动外部进程的工具必须经 `Ai1SkillShellTracker` 登记，保证停止/停机时回收
4. 批量写文件若绕过 `Ai1SkillFileService` 既有写方法，结束后必须手动调 `Ai1SkillServiceImpl#touchSkill` 刷新指纹

### 新增知识库策略

1. 文档上传格式：在 `Ai1KnowledgeDocumentServiceImpl` 的 `UPLOAD_FILE_SUFFIXES` 追加扩展名（当前仅 `.txt/.md`，用 `IoUtil.readUtf8` 读内容）
2. 检索增强（rerank/混合检索）：扩展 `Ai1RagTool#search` 与 `#buildAdvisor`，保持「调用方先在当前租户查出知识库 DO 再传入」的租户隔离约定
3. 更换向量数据库：当前 `getOrCreateVectorStore` 直接构建 `MilvusVectorStore`（依赖 `MilvusServiceClient`），更换向量库需在该方法新增构建分支并把返回类型放宽为 `VectorStore`；新实现同样需手动 `afterPropertiesSet` 建集合/索引

### 给 Agent 新增可编排能力（新工具来源）

1. `Ai1AgentDO` 增加 `List<Long>` 字段（`@TableField(typeHandler = LongListTypeHandler.class)`，保持 `autoResultMap = true`），同步建表 SQL 与 `Ai1AgentSaveReqVO/Ai1AgentRespVO`
2. harness 新建 `XxxToolFactory`（`@Component`），提供 `buildTools(Ai1AgentDO)` 返回工具列表，内部缓存用「编号:配置指纹」key 并提供 `evict(agentId)`
3. `Ai1SessionStreamTool#generate` 工具装配处 `tools.addAll(...)` 挂载；`Ai1AgentServiceImpl#deleteAgentListByIds` 增加 evict 清理
4. 目标域删除前增加引用计数：`Ai1AgentService` 暴露 `getAgentCountByXxxIds`，命中抛 `XXX_USED_BY_AGENT`

### 新增模型类型（如 RERANK）

1. `enums/model/Ai1ModelTypeEnum` 增加枚举值与 `isXxx()` 静态方法
2. `Ai1LlmModelFactory` 仿照 `getOrCreateEmbeddingModel` 增加对应 Cache 与构建方法
3. 消费方用 `isXxx` 校验并新增 `MODEL_TYPE_NOT_XXX` 错误码（1_041_001_0xx 段顺延）；保存 VO（`Ai1ModelSaveReqVO`）的 type 字段已有 `@InEnum(Ai1ModelTypeEnum.class)`，新增枚举值后校验自动放行、无需改动 VO；分页 VO（`Ai1ModelPageReqVO`）的 type 未加该注解
4. 若新字段参与模型构建，必须同步加入缓存 key 的 `Objects.hash` 指纹

### 新增配置项 / 定时任务

- 配置项：在 `YudaoAi1Properties` 增加嵌套属性类并给默认值即可（`@EnableConfigurationProperties` 已由 `Ai1AutoConfiguration` 开启）
- 定时任务：实现 yudao `JobHandler`（参考 `Ai1MemoryArchiveJob` 的 `@TenantJob` 逐租户执行），多节点互斥参考 `Ai1MemoryLockRedisDAO#tryLockArchive` 的 Redisson `tryLock` 用法

### 最佳实践

- 生成与连接解耦：SSE 断开不影响生成，任意节点可转发、续传；worker 可独立扩容
- 降级容错：RAG/记忆/MCP 单点失败跳过并把提示写入思考流，不让会话中断；不要自动重跑有副作用的工具
- 写入前校验执行权：每次写 DB/结果流前 `checkTaskLock(lock, workerThreadId)`，XACK 不能放 finally 无条件执行
- 安全兜底：SKILL 路径 sanitize 防目录穿越；HTTP 探测异常只回传异常类名不回传原文；worker 执行禁止 `TenantUtils.executeIgnore`（会跨租户读取）
- MCP stdio 与 SKILL Shell/FileSystem 工具会在服务器启动本地进程，多租户不可信部署需自行评估

## 模块依赖

当前在 `yudao-server/pom.xml` 中处于注释未启用状态（「AI1 Agent 相关模块（Spring AI）。默认注释，保证编译速度」），启用需取消该段注释后随 yudao-server 打包。上游内部依赖 system / infra 与 tenant/security/mybatis/redis 等 starter，模块特有的外部依赖明细如下：

| 依赖 | 版本 | 用途 |
|-----|------|-----|
| spring-ai-openai | spring-ai-bom 管理 | 对话/嵌入模型（OpenAI 兼容协议），排除 swagger-annotations-jakarta |
| spring-ai-client-chat | spring-ai-bom 管理 | ChatClient 1.x（agent-utils 的 Spring AI 依赖为 provided，显式对齐基础项目 BOM） |
| spring-ai-advisors-vector-store | spring-ai-bom 管理 | RAG Advisor（QuestionAnswerAdvisor） |
| spring-ai-milvus-store | spring-ai-bom 管理 | Milvus 向量存储，排除 slf4j-reload4j 解决日志冲突 |
| milvus-sdk-java | 3.0.10 | Milvus Java SDK，同样排除 slf4j-reload4j |
| spring-ai-agent-utils | 0.13.0 | SkillsTool 技能系统（SKILL.md）及 Shell/FileSystem/Glob/Grep/ListDirectory 执行工具 |
| mcp-json-jackson2 | 2.0.1 | 官方 Java MCP SDK（stdio / Streamable HTTP 客户端） |

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/package-info.java` | harness 层边界约定的权威定义 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/session/Ai1SessionStreamTool.java` | 会话流一体工具：投递/续传入口 + 生成 worker + 结果流 + SSE 转发（SmartLifecycle） |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/llm/Ai1LlmChatTool.java` | LLM 会话工具：按给定模型与消息执行一次流式会话 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/llm/Ai1LlmModelFactory.java` | LLM 模型工厂：程序化构建 OpenAI 兼容模型 + 配置指纹缓存 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/mcp/Ai1McpToolFactory.java` | MCP 工具工厂：MCP 工具桥接为 FunctionToolCallback |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/mcp/Ai1McpClientTool.java` | MCP 客户端工具：http/stdio 传输、连接缓存与串行保护 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/rag/Ai1RagTool.java` | RAG 工具：Milvus 向量化/检索/清理 + QuestionAnswerAdvisor 装配 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/skill/Ai1SkillToolFactory.java` | SKILL 工具工厂：文件树物化 + agent-utils 工具集构建 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/skill/Ai1SkillShellTracker.java` | Shell 进程跟踪器：装饰 ExecBackend，统一回收后台进程 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/memory/Ai1MemoryTool.java` | 长期记忆工具：读取/合并/生成 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/memory/Ai1MemoryArchiveTool.java` | 记忆归档工具：水位线增量归档 + 乐观写回 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/harness/model/Ai1ProviderTool.java` | 供应商工具：OpenAI 兼容接口原始 HTTP 探测 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/framework/ai/config/YudaoAi1Properties.java` | 配置类（prefix=yudao.ai1）：Milvus/Session/Skill/Memory 四组 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/framework/ai/config/Ai1AutoConfiguration.java` | 自动配置入口：只注册配置属性绑定 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/dal/redis/Ai1RedisKeyConstants.java` | Redis Key 常量：会话流与记忆锁的 key 格式与多租户约定 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/util/Ai1Utils.java` | 静态工具：`${ENV}` 占位符解析、Header 校验、记忆 Markdown 规范化 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/enums/Ai1ErrorCodeConstants.java` | 错误码定义（1-041 段） |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/controller/admin/agent/Ai1AgentController.java` | Agent Controller 模板（权限标识、VO 拼接写法参考） |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/service/session/Ai1SessionMessageServiceImpl.java` | 消息发送入口：快照锁 + getSelf() 事务代理的标准用法 |
| `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/job/Ai1MemoryArchiveJob.java` | 定时任务模板：JobHandler + @TenantJob |

## 领域模型

### 聚合根

| 聚合根 | 包含实体 | 说明 |
|-------|---------|------|
| Agent | `Ai1AgentDO` | 编排核心：绑定 Provider/Model/知识库/MCP/SKILL（后三者 `LongListTypeHandler` JSON 数组列）+ 系统指令 + 记忆开关 |
| 会话 | `Ai1SessionDO`、`Ai1SessionMessageDO` | 会话包含消息；助手消息编号同时是 Redis 结果流标识 |
| 知识库 | `Ai1KnowledgeBaseDO`、`Ai1KnowledgeDocumentDO` | 文档向量化进 Milvus，集合名按知识库编号隔离 |
| SKILL | `Ai1SkillDO`、`Ai1SkillFileDO` | 文件树（parentId 邻接表）物化到本地沙箱执行 |

### 值对象

| 值对象 | 说明 |
|-------|------|
| `Ai1ModelRespBO` | 模型调用参数运行时快照（harness 与 service 的跨层契约） |
| `Ai1ModelTypeEnum` | 模型类型枚举（当前 CHAT/EMBEDDING） |
| `Ai1McpTransportEnum` | MCP 传输方式（http/stdio） |
| `Ai1SessionStreamEventEnum` | SSE 事件枚举（stream/thinking/message/ping/done/error，done/error 为终态） |
| `Ai1SessionMessageStatusEnum` | 消息状态机（GENERATING → SUCCESS/FAILED） |
