# 注意事项与已知坑点

> 使用 ai1 模块（yudao-module-ai1-springai）时的常见问题、易踩坑点和最佳实践。本模块基于 Spring AI 1.x + 官方 MCP SDK + Milvus + Redisson Stream 自建会话流，坑点集中在「校验命名空间、流式生成、多节点缓存、向量一致性、执行类工具安全」几个主题。
>
> 除特别说明外，源码路径均相对 `yudao-module-ai1-springai/src/main/java/cn/iocoder/yudao/module/ai1/`。

## 1. 参数校验相关

### 1.1 javax 与 jakarta validation 注解混用，大量参数校验静默失效（本模块第一大坑）

**问题**: 部分接口的参数校验形同虚设——消息内容非空、Agent 状态非空、首页 days 的 1~30 范围、MCP config 的 @AssertTrue 校验等在运行时都不生效，但代码里明明写了注解。

**原因**: 本仓库是 JDK8 + Spring Boot 2.7.18（根 `pom.xml`：`revision` 2026.09-jdk8-SNAPSHOT、`spring.boot.version` 2.7.18），运行时验证器是 hibernate-validator 6（javax.validation 体系）。而模块内 32 个文件 import 了 `jakarta.validation`（共 54 处：其中 `jakarta.validation.constraints` 19 个文件 40 处，另有 `jakarta.validation.Valid` 14 处；javax.validation 15 处）：Spring AI 1.x 依赖把 jakarta.validation-api 3.x 带进了编译期 classpath，所以 jakarta 注解能编译通过，但 javax 验证器根本看不到它们，校验被**静默跳过**。注意 Controller 方法参数上的 jakarta `@Valid` 同样不被 Spring MVC 5.x 识别，批量替换时需连同 `@Valid` 一起换回 javax。典型受害文件：

- `controller/admin/session/vo/message/Ai1SessionMessageSendReqVO.java` —— content 的 `@NotBlank`（send-stream 消息内容非空校验失效）；
- `controller/admin/agent/vo/Ai1AgentUpdateStatusReqVO.java` —— `@NotNull`；
- `controller/admin/home/Ai1HomeController.java` —— 类级 `@Validated` 配合方法参数 `@Min(1)/@Max(30)`，方法级校验同样走 javax ExecutableValidator，days 范围限制全部失效；
- `controller/admin/mcp/vo/Ai1McpSaveReqVO.java` —— `@AssertTrue` 校验方法不执行。

对照：`Ai1AgentSaveReqVO`、`Ai1SessionMessagePageReqVO`、`Ai1MemoryUpdateReqVO` 用的是 `javax.validation.constraints`，这些校验正常生效。同一模块两种命名空间并存，极易误判「校验到底有没有生效」。

**解决**: 新增/改造 VO 与 Controller 一律使用 `javax.validation`；排查「参数没校验」类问题，第一步先检查 import 的命名空间是 javax 还是 jakarta；有条件时把存量 jakarta 注解批量替换回 javax 并逐接口复核。

## 2. 会话流与 SSE 相关

### 2.1 Redis Stream 必须用 Redisson 原生 RStream + StringCodec，SSE data 统一 JSON 字符串

**问题**: 改用项目统一的 RedisTemplate 或 Spring Data 的 `opsForStream` 读写会话流后，字段错乱、阻塞读取抛 `ClassCastException`，甚至连接池被占满。

**原因**: `harness/session/Ai1SessionStreamTool.java` 类 javadoc【关键约定】3/4 写明了两条硬约束：① 项目 RedisTemplate 的 JSON 序列化会破坏 Stream 字段；② Spring Data 的 Redisson 适配层在阻塞读取无数据时抛 ClassCastException，且阻塞时长超过命令超时会占满连接池。因此 `getTaskStream/getResultStream/getStopBucket/getStopTopic` 全部用 `redissonClient.getXxx(..., StringCodec.INSTANCE)`，`tenantId/messageId/type/data` 等字段按纯字符串存取。配套约定：SSE 事件的 data 统一 `JsonUtils.toJsonString(...)` 后再 `emitter.send`（`#sendEvent`），直接发送含换行的文本会被 SSE 协议按 `data:` 行切分、首字符空格被截断，导致前端内容错乱。

**解决**: 自定义流/桶读写必须沿用 Redisson 原生 API + StringCodec；扩展 SSE 事件时保持 data 为 JSON 字符串，由前端解析后展示。

### 2.2 worker 与 SSE 转发线程无登录上下文，租户必须显式还原，禁止 TenantUtils.executeIgnore

**问题**: 在生成 worker、结果流转发或失败回写代码里追加 DB 操作时，查不到数据或读到别的租户的数据。

**原因**: 消费线程（`consumeLoop → handleTask → generate`）与 SSE 转发线程都脱离了 HTTP 请求，`TenantContextHolder` 无值。投递任务（`#submit`）时存在租户才把 `tenantId` 写进任务字段，`#handleTask` 用 `TenantUtils.execute(tenantId, ...)` 还原上下文；类注释【关键约定】2 明确「禁止使用 executeIgnore（关闭租户过滤会导致跨租户读取）」。`#failLostMessage` 回写时同样要用转发线程捕获的 tenantId 恢复上下文。

**解决**: worker/回调里的 DB 操作必须带租户上下文执行；关闭多租户部署时任务不携带 tenantId，按空租户上下文执行。任何新代码都不要图省事用 `executeIgnore` 包住对 `TenantBaseDO` 表的访问。

### 2.3 执行锁校验必须传 worker 线程编号，而非当前线程

**问题**: 停止/接管生成后，旧 worker 仍在往结果流写增量，或正常 worker 被误判失去执行权而中断，输出重复、互相覆盖。

**原因**: 流式生成的增量回调可能在 Spring AI 的模型线程执行，不在 worker 线程上。`Ai1SessionStreamTool#checkTaskLock`（L861-870）因此显式接收 `workerThreadId` 参数做 `lock.isHeldByThread(workerThreadId)` 校验，javadoc 写明「增量回调可能在模型线程执行，因此不能使用当前回调线程编号」；每次写库/写流前都校验，失效即抛「生成任务执行权已失效」中止旧 worker，由新持有者收尾。

**解决**: 自己实现类似「执行权校验」时，锁的归属一律用发起执行时的线程编号（或显式 token）判断，不要在回调里用 `Thread.currentThread()`。

### 2.4 数据库回填与结果流写入非同一事务，靠终态补偿兜底且绝不重新生成

**问题**: worker 在「回填助手消息」与「写结果流 + XACK」之间退出后，消息状态已终态但结果流缺 done/error，前端续传连接永远不结束；或者接管方重新生成导致输出重复、工具调用重复执行。

**原因**: 两步不是同一事务（`#completeTaskResult` javadoc：「数据库回填与结果流写入不是同一事务，worker 可能在两者之间退出」）。补偿逻辑集中在 `#completeTaskResult`（L833-859）：只查结果流最后一条事件，已有 done 直接返回；FAILED 且末尾非 error 时按 `getSavedNotice` 解析正文提示补写 error——人工终止（`TERMINATED_NOTICE`）只补 done 不补 error；最后补 done 使续传连接能结束。被认领（reclaimed）或结果流已存在的任务一律按中断处理（`#executeTask` 1.3 分支），只还原部分输出并标 FAILED，不重新生成。XACK 必须在全部写入成功后执行，不能放 finally 无条件确认。

**解决**: 扩展生成流程时保持「先回填 DB、再写结果流、最后 XACK」的顺序与补偿入口；XACK 放在成功路径末尾；任何接管场景都走 `completeTaskResult` 补齐缺失终态，不要重跑生成。

## 3. 事务与 AOP 相关

### 3.1 同类内部调用 @Transactional 失效，需 getSelf() 自代理

**问题**: 在编排链路里给同类私有流程（如 `createRoundMessages`）新加 `@Transactional` 后，事务不生效，异常时部分落库已提交。

**原因**: `service/session/Ai1SessionMessageServiceImpl.java#sendSessionMessageStream` 以 lambda 方式调用 `getSelf().createRoundMessages(...)`（L110-111，在记忆快照锁内提交），`#getSelf`（L221-226）即 `SpringUtil.getBean(getClass())`，注释「获得自身的代理对象，解决 AOP 生效问题」——同类内 `this.xxx()` 不经过代理，注解失效。

**解决**: 新增同类内部的事务/异步方法时沿用 `getSelf()` 模式，或拆分到独立 Bean；参照 `#createRoundMessages` 的写法。

## 4. 多节点部署与缓存相关

### 4.1 各类运行时缓存的 evict 只作用于本节点，跨节点靠 TTL/指纹兜底

**问题**: 修改了 Provider 地址/密钥、MCP 配置、嵌入模型或 SKILL 内容后，集群部分节点的行为迟迟不变，误以为改动没生效。

**原因**: 四处运行时缓存的失效接口都只清当前 JVM：

- 模型实例：`harness/llm/Ai1LlmModelFactory.java` 的 `evictByProviderId/evictByModelId` 只对本节点两个 Guava Cache `removeIf`，`CACHE_EXPIRE = 10 分钟`（L53-55）注释明确「修改 Provider / 模型时只能失效本节点，其他节点最迟在该时间后按新配置重建」；
- MCP 客户端：`harness/mcp/Ai1McpClientTool.java` `CACHE_EXPIRE_AFTER_ACCESS = 30 分钟`（L62-66），其他节点的旧客户端（含 stdio 子进程）等闲置过期或按配置指纹（`#buildCacheKey`）自然 miss 重建；
- 向量存储：`harness/rag/Ai1RagTool.java#evict` 注释「只作用于当前节点；其他节点在嵌入模型变更后，会因嵌入模型实例不一致自然重建」（L201-207）；
- SKILL 快照：`harness/skill/Ai1SkillToolFactory.java` `snapshotCache` 为 JVM 内对象，靠每次使用前按「编号:更新时间」指纹校验自动重建。

**解决**: 排查「改了配置不生效」先确认多节点延迟（模型最长 10 分钟、MCP 最长 30 分钟）；对时效敏感的变更，重启节点或运维上保证配置变更落在单一节点验证。

## 5. 长期记忆归档相关

### 5.1 归档依赖「安全前缀 + 水位线 + 锁顺序」三重约定，破坏任一条都会丢消息或阻塞

**问题**: 自行修改归档逻辑后出现：记忆漏消息（水位线越过未完成的回复）、归档永久卡住、或消息发送被归档阻塞。

**原因**: `harness/memory/Ai1MemoryArchiveTool.java` 类 javadoc【关键约定】定义了三重约定：① `#getNewMessageList` 只取「水位线之后到第一条 GENERATING 消息为止」的 SUCCESS 消息（安全前缀），否则水位线会越过尚未完成的回复；② 归档前先 `#failStaleMessages` 收尾超时且无 worker 的孤儿生成（SSE 超时 + 60s 缓冲，按 createTime 判断，锁内二次校验后标 FAILED 并写终态），否则它们永久阻塞安全前缀；③ 锁顺序固定为「归档锁 → 消息执行锁（tryLock）」，快照锁（`MEMORY_SNAPSHOT_LOCK`）只用于读取新消息且与 `createRoundMessages` 落库共用（消息在锁内提交，保证读到的已完成消息都已提交）——收尾要抢消息执行锁并读写结果流、模型调用耗时不可控，都必须放在快照锁外。另外写入前 `updateMemoryIfUnchanged` 乐观校验：记忆被人工修改则放弃本次结果（水位线不推进，这批消息下一轮重新归档，最终不丢数据只是延迟一轮）。

**解决**: 扩展归档时严格保持三重约定；监控归档不要把「抢不到归档锁返回 0」当异常（`#archive` 有意跳过做削峰）；单用户归档失败不影响其他用户（`#archiveAll` 逐用户 try/catch），单次封顶 `BATCH_SIZE=100` 条。

## 6. Milvus / 向量相关

### 6.1 手动构建的 MilvusVectorStore 必须显式调用 afterPropertiesSet，清理向量为最终一致

**问题**: ① 绕过 Spring 装配手动构建向量存储后，首次写入/检索报集合不存在；② 删除知识库/文档后 Milvus 中残留孤儿集合或旧向量，且没有任何报错。

**原因**: ① `harness/rag/Ai1RagTool.java#getOrCreateVectorStore` 用 `MilvusVectorStore.builder(...)` 手动构建实例，注释写明「手动构建的实例不会触发 Spring 生命周期回调，需主动初始化」——必须调用 `vectorStore.afterPropertiesSet()` 完成建集合、建索引、加载（L242-247），失败被包装为 `IllegalStateException("向量集合(xxx) 初始化失败")`。② 清理都是「尽力而为」：知识库删除时 `dropCollection` 由 `Ai1KnowledgeBaseServiceImpl#deleteKnowledgeBaseListByIds` 注册 `TransactionSynchronization.afterCommit` 才执行（L104-113，注释「外部资源无法回滚，事务提交后再执行，失败仅记录日志」），内部 catch 全部异常仅 log.warn——应用在提交后、drop 前崩溃或 Milvus 不可用会遗留孤儿集合；文档删除/更新时 `#deleteByDocumentIds`（L154-164）同样失败仅 log.warn，旧向量残留，靠重新向量化时 `#vectorize` 先 `delete(documentId)` 再 add 自愈。

**解决**: 新增向量库使用场景必须显式调 `afterPropertiesSet`；把「孤儿集合/残留向量」当已知最终一致问题，提供定期对账或手动清理入口；不要试图把 Milvus 写入包进 DB 事务。

## 7. MCP 相关

### 7.1 stdio 传输与 SKILL 执行类工具会在服务器上启动进程、执行命令（安全风险）

**问题**: 拥有 MCP/SKILL 管理权限的用户可以让应用服务器执行任意本地命令，多租户场景下是横向越权风险。

**原因**: `harness/mcp/Ai1McpClientTool.java` 类注释（L45）「stdio 会在服务器上启动本地进程，与源工程行为一致，多租户不可信部署需自行评估」——`command/args/env` 由用户配置，`#buildStdioTransport` 直接启动子进程；`harness/skill/Ai1SkillToolFactory.java` 的 `buildTools` 注册 ShellTools（bash）、FileSystemTools 等，类注释同样声明「多租户不可信部署需自行评估」。隔离仅靠目录限定：物化目录名经 `#sanitize`（替换 `\` `/` 与 `..`）软防护，exec backend 只设置工作目录，对 Shell 命令本身约束有限；Shell 进程经 `Ai1SkillShellTracker` 跟踪以便终止时回收。

**解决**: `ai1:mcp:create`、SKILL 管理等权限只分配给可信管理员；不可信租户部署必须自行评估，容器级沙箱/网络限制需在模块外补充。

### 7.2 同一 MCP 客户端的调用被 synchronized 串行化，失败不自动重试，初始化失败必须主动关闭

**问题**: ① 同一 MCP 服务上一个慢工具会阻塞该服务的其它工具调用；② 工具调用失败后不会自动重跑；③ 连接初始化失败时若处理不当会泄漏 HTTP 连接或 stdio 子进程。

**原因**: ① `#callTool` 在 `synchronized (client)` 内执行（L128-129，stdio 管道不支持并发读写），代价是串行；② `McpError`（服务端 JSON-RPC 业务错误）不视为连接失效直接上抛，其他异常只按 `clientCache.asMap().remove(cacheKey, client)` 双参 remove 精确清理本次失败实例（防误删已重建的新连接），注释「不自动重跑有副作用的工具」；③ `#getOrCreateClient` 中 `client.initialize()` 抛异常的客户端尚未进入缓存，RemovalListener 不会触发，必须 catch 后主动 `closeQuietly(client)`（L247-253）。另外 `#listTools` 失败返回空列表且不写缓存——空列表是合法成功态（服务确实没有工具），下次会话可重试。

**解决**: 对耗时敏感的 MCP 服务拆分为多个 MCP 记录以并行；扩展失败处理时保持「精确移除失败实例 + 不自动重跑」语义，不要无条件重试有副作用的工具；新建客户端的 catch 路径必须关闭资源。

### 7.3 MCP 配置的 null 语义：切换 stdio 必须显式置 null url，清空 headers 存空集合

**问题**: ① MCP 从远程 http 切回本地 stdio 后，客户端仍连旧地址；② 清空请求头保存后，旧 Authorization 等鉴权头依然生效。

**原因**: ① MyBatis-Plus `updateById` 默认忽略 null 字段，若误用会残留旧 url；而 `dal/mysql/mcp/Ai1McpMapper.java#updateForSave`（L34-37）用 `LambdaUpdateWrapper.set(mcp.getUrl() == null, Ai1McpDO::getUrl, null)` 主动置空——`Ai1McpServiceImpl#updateMcp` 必须走它。且 `Ai1McpClientTool#parseConfig` 在 config.url 缺失时会回退平铺列，残留旧值会被静默读回。② `#buildMcp`（L147-152）把 null headers 归一为空集合，空时从 config 中 `remove("headers")`，注释「空请求头统一保存为空集合，避免更新时跳过 null 后残留旧鉴权」。

**解决**: MCP 保存逻辑必须经 `updateForSave`；新增类似「可清空」字段时同样注意 null/空集合的保存语义，不要直接 `updateById`。

## 8. SKILL 物化相关

### 8.1 物化失败静默降级、指纹只认 update_time、frontmatter 与管理字段是两套数据

**问题**: ① Agent 对话突然没有任何 SKILL 工具，但接口无任何报错；② DBA 或其他模块直改 `ai1_skill_file` 表后，本地技能目录迟迟不更新；③ 改了 SKILL 名称/描述，模型看到的技能介绍却没变。

**原因**: ① `harness/skill/Ai1SkillToolFactory.java#sync` 在物化异常时仅 `log.warn` 后 `return cached`（可能为 null 或旧快照，L188-191），`buildTools` 随即返回空列表——该次会话可能完全没有 SKILL/Shell 工具，排查只能查服务端 warn 日志。② 变更指纹 = 按 id 排序的「编号:更新时间」串（`#buildFingerprint`，L201-205），只感知 `ai1_skill.update_time`；`service/skill/Ai1SkillServiceImpl.java#touchSkill`（L124-126）用空对象 `updateById`，完全依赖 MyBatis-Plus MetaObjectHandler 自动填充 update_time——自动填充失效或绕过 Service 直写 `ai1_skill_file` 都不会触发重建。防护是 `#isSnapshotValid` 同时校验目录内 `.fingerprint` 文件内容，防止目录被外部清理后误用缓存。③ 创建时用管理信息初始化 SKILL.md frontmatter（`Ai1SkillFileServiceImpl#createDefaultSkillFileList` L72-92，name/description 压成单行防换行破坏 YAML），注释写明「后续面向模型的名称、描述由文件编辑器独立维护」——`updateSkill` 改表字段不同步 SKILL.md，而 SkillsTool 读取的是 SKILL.md frontmatter。

**解决**: 排查「技能不生效」先看 warn 日志与物化目录；所有 SKILL 文件写路径必须走 `Ai1SkillFileService` 并调用 `touchSkill`；修改技能的模型可见名称/描述要走文件编辑接口，而不是管理表字段。另注意：多个 SKILL 物化到同一 Agent 目录时按 id 升序固定注册（L173 注释），frontmatter name 相同时由 agent-utils 首次注册规则决定生效者，排查时需检查跨 SKILL 的 name 冲突。

## 9. 模型 / 供应商配置相关

### 9.1 apiKey 更新语义：空白 = 保持原值，但脱敏回显值回传会覆盖为脏数据

**问题**: 前端把详情接口回显的脱敏密钥（如 `sk-****abcd`）原样提交保存后，下次模型调用必然鉴权失败。

**原因**: `service/model/Ai1ProviderServiceImpl.java#updateProvider`（L59-74）对空白 apiKey 显式 `setApiKey(null)`，借 MyBatis-Plus `updateById` 跳过 null 保持原值；而 `controller/admin/model/Ai1ProviderController.java#buildProviderRespVO`（L105-122）返回的是脱敏值（≤8 字符返回 `"****"`，否则 `StrUtil.hide` 中段打码；仅 `${...}` 变量占位符原样返回）。脱敏串非空，会被当成新密钥入库。

**解决**: 前端交互必须把 apiKey 输入框留空表示「不修改」，禁止回显值回传；扩展 Provider 时保持「空 = 不变」语义，不要新增「空 = 清空」的分支。

## 10. 首页统计相关

### 10.1 统计口径与直觉不符：role/status 不区分、agentName 可为 null、原生 SQL 依赖租户插件

**问题**: 消息趋势把失败消息和「生成中」占位消息都计入；按 Agent 排行里出现 agentName 为空的行；统计 SQL 被搬到 Job/异步线程后跨租户。

**原因**: `dal/mysql/home/Ai1HomeMapper.java` 三条 `@Select` 是手写原生 SQL（L21-48）：① 不带 role/status 条件，`Ai1SessionMessageRoleEnum`、`Ai1SessionMessageStatusEnum` 的状态都参与 COUNT；② 只手写 `deleted = FALSE`（原生 SQL 不走 MyBatis-Plus 逻辑删除拼接），且未写 tenant_id——租户隔离完全依赖 `TenantLineInnerInterceptor` 对 @Select 的自动改写，DO 均继承 TenantBaseDO；③ 按 Agent 统计仅 INNER JOIN `ai1_session` 并过滤 `c.deleted = FALSE`，已删除 Agent 名下的未删除消息仍计入，Controller 回填名称用 `MapUtils.findAndThen`，Agent 已删除（`getAgentMap` 查不到）时跳过，`agentName` 保持 null（`Ai1HomeMessageSummaryByAgentRespVO` 注释「Agent 已删除时为空」）。另外统计无 `@Cacheable`、无预聚合，`GROUP BY CAST(create_time AS DATE)` 在大消息量下可能触发临时表/filesort。

**解决**: 调整统计口径必须改 `Ai1HomeMapper` 的 SQL，而非枚举判断；前端需容忍 `agentName` 为空的行；把统计复用到无租户上下文的场景（定时 Job、异步线程、工具调用）前，先评估租户改写是否仍然生效。
