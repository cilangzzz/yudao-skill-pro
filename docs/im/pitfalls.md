# 注意事项与已知坑点

> 使用 im 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 im 全部业务表没有 tenant_id，新增 DO 不要随手继承 TenantBaseDO

**问题**: 新增表时习惯性让 DO 继承 `TenantBaseDO`，启动后所有 SQL 直接报「Unknown column 'tenant_id'」；或者反过来，误以为 im 数据按租户隔离，实际同一套数据全租户共享。

**原因**: im 模块 17 张 `@TableName` 表的 DO（`ImGroupDO`、`ImFriendDO`、`ImPrivateMessageDO`、`ImRtcCallDO` 等）全部继承 `BaseDO`，表里没有 tenant_id 列。框架的租户拦截不是靠配置表清单，而是 `TenantDatabaseInterceptor#computeIgnoreTable` 按实体类型自动判定：继承 `TenantBaseDO` → 拼租户条件，否则忽略。im 全部表因此自动跳过租户过滤，数据物理上全局共享，租户概念只体现在「不同租户的用户是不同的人」这一层。

**解决**: im 模块内新增 DO 一律继承 `BaseDO`，建表不要加 tenant_id 列；需要按租户区分的数据只能通过用户归属（system 侧的租户）间接体现。若某张表确实要接入租户体系，必须同时改表结构 + 换基类 + 排查所有历史数据，不能只改一处。

### 1.2 LiveKit Webhook 是唯一的 @PermitAll + @TenantIgnore 端点，整条链路运行在无租户上下文中

**问题**: 在 `ImRtcCallServiceImpl#handleLiveKitEvent` 的调用链里新增逻辑时，调用了需要租户上下文的代码（如 `TenantContextHolder.getRequiredTenantId()`、租户级缓存、带租户过滤的跨模块 API），本机联调不报错（请求碰巧带了租户头），生产环境 LiveKit 回调时抛 `NullPointerException: TenantContextHolder 不存在租户编号` 或查不到数据。

**原因**: `ImRtcLiveKitController#webhook` 是模块内唯一的 `@PermitAll + @TenantIgnore` 端点。框架启动时会把带 `@TenantIgnore` 的接口 URL 自动加入 `TenantSecurityWebFilter` 的忽略清单（`YudaoTenantAutoConfiguration#getTenantIgnoreUrls`），请求不带 tenant-id 头也放行，并设置 `TenantContextHolder.setIgnore(true)`。此后整条链路（签名校验 → `handleParticipantLeft` / `handleRoomFinished` → `endSession` → 消息落库、WebSocket 推送）都没有租户编号。

**解决**: Webhook 链路内保持「租户无关」：只操作 im 自身表（本来就不参与租户过滤），按 room/userId 精确定位数据，不调用任何 `getRequiredTenantId()` 或依赖租户上下文的组件。需要跨模块取用户信息时用 `adminUserApi.getUser(userId)` 按 id 查（ignore 态下不过租户过滤，仍能查到）。安全由 `liveKitClient.verifyWebhookSignature` 的 JWT + body sha256 签名校验兜底，不要为了「方便联调」把签名校验短路。

### 1.3 @TenantIgnore 上下文里 Spring Cache 键不带租户后缀，webhook 链路与正常请求是两套缓存

**问题**: 群成员被移出后，LiveKit Webhook 兜底触发的群通话结束通知（RTC_CALL_END）偶尔仍把已移除成员算进接收者，最长持续约 1 小时。

**原因**: `TenantRedisCacheManager#getCache` 在租户上下文正常时给缓存名拼后缀（`group_member_ids:{groupId}:{tenantId}`），但 `TenantContextHolder.isIgnore()` 为 true 时保持原名。Webhook 链路 `endSession → pushCallChatMessage → ImGroupMessageServiceImpl#sendGroupMessage → ImGroupMemberServiceImpl#getActiveGroupMemberUserIdsByGroupId`（`@Cacheable(GROUP_MEMBER_IDS)`）读写的是**无后缀**的 `group_member_ids:{groupId}`；而正常请求路径的 `@CacheEvict`（`addGroupMember` / `removeGroupMember` 等）只清**带后缀**的键。两套缓存互不感知，无后缀那份只能靠 `spring.cache.redis.time-to-live: 1h` 过期兜底。

**解决**: 认识到这是已知边界，依赖 1h TTL 收敛即可，影响仅限通知受众多算（条件 UPDATE 保证状态机本身不受影响）。若要彻底消除，可在 Webhook 链路读成员时绕过 Spring Cache（直接走 `groupMemberMapper` 查询），或在 `invalidateSensitiveWordBsCaches` 同款的主动失效里补 `invalidateAll`。注意不要在正常请求路径里也读无后缀键，否则同一份数据两处缓存更难排查。

### 1.4 RTC 兜底 Job 加了 @TenantJob，但 im 表不分租户，N 个租户会把同一批数据扫 N 遍

**问题**: 部署多租户环境后，`ImRtcCallCleanupJob`（僵尸通话清理）和 `ImRtcParticipantTimeoutJob`（振铃超时）每次调度的耗时和 LiveKit `listParticipants` 调用量随租户数线性膨胀；任务日志里清理数量看起来也「偏多」。

**原因**: `TenantJobAspect#around` 会取全量租户列表并 `parallelStream` 逐租户执行（`TenantUtils.execute(tenantId, ...)`）。im 表不参与租户过滤（见 1.1），每个租户的执行都是对同一批全局数据的全量扫描：`cleanupZombieCalls` 扫 `selectListByStatusInAndStartTimeBefore`，`timeoutInvitingParticipants` 扫 `selectListByStatusAndInviteTimeBefore`。并发租户同时命中同一通话时，靠 `endSession` / `timeoutInvitingParticipant` 的条件 UPDATE（影响 0 行即跳过）保证不重复处理。

**解决**: 正确性有 CAS 兜底，可以不改；但要明白开销来自「租户数 × 全表扫描」。若租户多、数据量大，可去掉 `@TenantJob` 改为单次全局执行（内部方法已不依赖租户上下文），或在 Job 参数里调大 `cleanupZombieThresholdMinutes` / `inviteTimeoutMinutes`（`ImProperties.Rtc`，默认 5 / 1 分钟）降低扫描频率。

## 2. 缓存相关

### 2.1 FRIEND_STATE 双向失效依赖调用方 @Caching 模板，内部方法 addFriend0 / deleteFriend0 不主动 evict

**问题**: 新写了一条会改动好友关系的路径（如批量导入、数据修复脚本），直接调了 `addFriend0` / `deleteFriend0`，之后发私聊仍报 `FRIEND_NOT_FRIEND`（1_040_600_001）或 `FRIEND_BLOCKED_BY_PEER`，但数据库里关系明明是对的。

**原因**: `ImFriendServiceImpl#getFriendState` 是 `@Cacheable(cacheNames = FRIEND_STATE, key = "#userId + '_' + #friendUserId")`，缓存的是单向关系状态。所有写路径（`becomeFriends` / `silentReAddFriend` / `deleteFriend` / `blockFriend` / `unblockFriend`）都靠方法上的 `@Caching(evict = {正向键, 反向键})` 同时失效两个方向；而 `addFriend0` / `deleteFriend0` 的 javadoc 明确写了「FRIEND_STATE 缓存失效由调用方的 @Caching 注解统一处理，本方法不主动 evict」。

**解决**: 任何新的好友关系写路径，要么挂到上述五个带 `@Caching` 的公开方法上，要么照抄双向 evict 模板：

```java
@Caching(evict = {
        @CacheEvict(cacheNames = FRIEND_STATE, key = "#userId + '_' + #friendUserId"),
        @CacheEvict(cacheNames = FRIEND_STATE, key = "#friendUserId + '_' + #userId")
})
public void myWritePath(Long userId, Long friendUserId) { ... }
```

另外注意 `getFriendState` 从不返回 null（NONE 也缓存），`unless = "#result == null"` 形同虚设，不要指望「查不到就不缓存」。

### 2.2 敏感词词库按租户 Guava LoadingCache 缓存：本机即时失效，多实例最长 1 分钟收敛

**问题**: 运营在 A 实例上增删敏感词后立刻发消息，B 实例上仍然放行/误杀；或者自己写了绕过 `ImSensitiveWordService#validateText` 的敏感词逻辑，行为和消息发送入口不一致。

**原因**: `ImSensitiveWordServiceImpl` 里 `sensitiveWordBsCaches` 是 `CacheUtils.buildAsyncReloadingCache(Duration.ofMinutes(1), ...)` 的按租户 LoadingCache，value 是重建好的 `SensitiveWordBs` trie 实例 + 基线 `max(update_time)`。CRUD 后 `invalidateSensitiveWordBsCaches()` 只失效**本机**（当前租户；无租户上下文则 invalidateAll；关闭多租户时统一用 `SINGLE_TENANT_CACHE_KEY = 0`）；其它实例靠每分钟的异步 reload，先比对 `selectMaxUpdateTime` 没变就复用旧实例。reload 里用 `TenantUtils.execute(tenantId, ...)` 恢复租户上下文，自己仿写时漏掉这一步会查错租户的词库。

**解决**: 敏感词校验统一走 `validateText`（仅对 `ImContentTypeEnum.TEXT` 类型消息调用）；不要在别处自建词库缓存，也不要期望增删词对全集群秒级生效——多实例部署接受最长 1 分钟收敛，或改用集中式缓存。

### 2.3 CacheManager 开了 transactionAware，@CacheEvict 延迟到 afterCommit，事务内回读拿到旧值

**问题**: 在 `@Transactional` 方法里先写库再调 `getXxx`（带 `@Cacheable`）做后续判断，拿到的是**修改前**的旧值；或者事务内 evict 后立刻回读，缓存里居然还有。

**原因**: `YudaoTenantAutoConfiguration#tenantRedisCacheManager` 和 `YudaoCacheAutoConfiguration#redisCacheManager` 都设置了 `cacheManager.setTransactionAware(true)`：`@CacheEvict` / `@CachePut` 在事务内被延迟到 afterCommit 才执行，避免「事务未提交就清缓存、并发读穿回填脏值」。典型如 `ImGroupServiceImpl#updateGroup`（`@CacheEvict(GROUP)` + `@Transactional`），事务提交前 GROUP 缓存键仍是旧群信息。

**解决**: 同一事务内写后需要「新值」时，直接用方法内的内存对象（`updateGroup` 就是用老值备份 + `BeanUtil.copyProperties` 内存合并返回），不要再走 `@Cacheable` 读缓存；跨方法的写后读要么拆到事务外，要么显式绕过缓存走 Mapper。反之，也不要在事务内手动操作缓存「提前生效」，会破坏 afterCommit 语义。

## 3. 事务与异步相关

### 3.1 WebSocket 推送统一「事务提交后 + @Async + getSelf() 代理」，afterCommit 异常会被 Spring 静默吞掉

**问题**: 自己仿写推送/通知逻辑时踩三种坑：直接 `this.doSendNotification(...)` 导致 `@Async` 失效变同步执行；在 afterCommit 回调里抛异常却看不到任何日志，下游永远收不到通知；无事务调用方以为推送也是异步的，实际是同步。

**原因**: `ImWebSocketServiceImpl` 的设计是三件套：`executeAfterTransaction` 判断 `TransactionSynchronizationManager.isSynchronizationActive()`——有事务则注册 afterCommit 回调（保证客户端收到推送时库里的变更已可见），无事务则 `task.run()` **同步**执行；真正发送走 `getSelf().doSendNotification(...)`（`SpringUtil.getBean(getClass())` 取代理，`@Async` 才生效）；`@Async` 线程池由框架统一加了 `TtlRunnable` 装饰器（`YudaoAsyncAutoConfiguration`），租户上下文可传递，但 afterCommit 阶段抛出的异常 Spring 会静默吞掉。同类先例：`ImFriendRequestServiceImpl#applyFriend` 的 autoAccept 回调特意包了 try/catch，注释写明「afterCommit 异常会被 Spring 静默吞掉，否则同意失败时申请方永远等不到 APPROVED」。

**解决**: 推送一律注入 `ImWebSocketService` 调 `sendNotificationAsync` / `broadcastNotificationAsync`，不要自己注册 afterCommit；类内部调本类 `@Async` 方法必须走 `getSelf()`（`ImGroupMessageServiceImpl#readGroupMessageEvent`、`ImChannelMessageServiceImpl#readChannelMessageEvent` 同款）；如果必须自己写 afterCommit 回调，方法体整体 try/catch + log.error 兜底。

## 4. 状态机与并发相关

### 4.1 RTC 状态推进全部依赖条件 UPDATE（CAS），不要改成「先查再改」

**问题**: 新增 RTC 状态迁移逻辑时用了「select 判断状态 → updateById」两步写，用户接口、LiveKit Webhook、定时 Job 三方并发下出现状态覆盖：刚标记 NO_ANSWER 的参与者被 Webhook 又改回 LEFT，或已 ENDED 的通话被重复结算。

**原因**: `ImRtcCallServiceImpl` 的所有状态迁移都是「条件 UPDATE + 影响行数判定」：`acceptCall` / `rejectCall` 用 `updateByIdAndStatus(..., INVITING, ...)`，`maybeMarkOngoing` 用 `rtcCallMapper.updateByIdAndStatus(call.getId(), CREATED, ...)`，`endSession` 用 `updateByIdAndStatusIn(..., ACTIVE_STATUSES, ...)` 且影响 0 行时打日志「已被另一路径终结，跳过」；`joinParticipant` 靠 `im_rtc_participant` 唯一键，`DuplicateKeyException` 降级为回查复用。Webhook 兜底（`handleParticipantLeft`、`handleRoomFinished`）与正常接口/Job 并发全靠这套幂等。

**解决**: 扩展 RTC 状态机时沿用 CAS 写法：UPDATE 带「期望的旧状态」条件，`updated == 0` 视为并发已处理直接返回；唯一键冲突降级回查。永远不要基于内存里的旧 `call.getStatus()` 做无条件 update。

### 4.2 群通知必须 send-before-remove：receiver_user_ids 是发送时刻的成员快照

**问题**: 自己写群操作（踢人、退群、解散）时先改成员表再发通知，被移除者收不到 GROUP_MEMBER_KICK / GROUP_DISSOLVE，前端群列表残留；或者引用定向消息时把内容泄漏给了本来看不到的人。

**原因**: 群消息可见性按发送当时的成员快照固化：`ImGroupMessageServiceImpl#sendGroupMessage` 先取 `getActiveGroupMemberUserIdsByGroupId`（GROUP_MEMBER_IDS 缓存）算出 `receiverUserIds` 存进 `im_group_message.receiver_user_ids`，后续 pull/历史查询都按这个快照过滤。所以 `ImGroupServiceImpl` 的注释反复强调顺序：`dissolveGroup0`「先发 GROUP_DISSOLVE 通知：放在成员移除前，sendGroupMessage 才能查到全员」，踢人同理（「先发 GROUP_MEMBER_KICK 通知：放在被踢者移除前」）。另外引用消息有防泄漏校验：`normalizeQuoteContent` 要求新消息可见集合必须是被引用消息可见集合的**子集**，否则抛 `MESSAGE_QUOTE_INVALID`（1_040_300_008），防止定向消息内容随广播引用外泄。

**解决**: 所有「变更成员集合 + 群内广播」的组合操作，广播永远放在成员变更之前；新场景需要引用/转发时保留快照子集校验，不要为了「体验」放开。

## 5. 业务规则易混淆点

### 5.1 撤回时限只约束「撤回自己的消息」，群主 / 管理员治理他人消息不受时间窗限制

**问题**: 联调时发现群主 10 分钟后还能撤回成员的消息，以为「超过 5 分钟不能撤回」的规则失效了；或者给普通成员开放撤回接口时误以为超时也能撤他人消息。

**原因**: `ImGroupMessageServiceImpl#recallGroupMessage` 的判定顺序：普通成员只能撤自己的消息（否则 `MESSAGE_RECALL_DENIED`，1_040_300_002）；时间窗校验在 `if (ObjUtil.equal(message.getSenderId(), userId))` 分支内——`message.getSendTime().plusMinutes(recallTimeoutMinutes).isBefore(now)` 才抛 `MESSAGE_RECALL_TIMEOUT`（1_040_300_007），阈值来自 `ImProperties.Message#recallTimeoutMinutes`（默认 5 分钟，`yudao.im.message.recall-timeout-minutes` 可配）。群主 / 管理员（`ImGroupMemberRoleEnum.isOwnerOrAdmin`）撤他人违规消息完全跳过时间窗。撤回后原消息 `status` 置 RECALL，再通过 `sendGroupMessage` 发一条 `ImContentTypeEnum.RECALL`（2101，persistent=true）的撤回事件进消息流。

**解决**: 前端倒计时按「5 分钟内可撤回自己的消息」展示即可；治理类（撤他人）入口不要套时间窗逻辑。若产品要求「管理员也受限」，需显式改动该分支，而不是改配置——配置只影响本人消息的时间窗。

## 6. 扩展与二次开发

### 6.1 新增消息类型必须登记 ImContentTypeEnum（OpenIM 段位复用 + persistent / normal 双标志）

**问题**: 新消息类型没登记枚举，发送时 `ImContentTypeEnum.validate(type)` 直接 `Assert` 失败；或者登记了但 `persistent` 配错，导致离线用户 pull 不到、或系统事件被当成聊天消息计未读。

**原因**: 模块的消息类型、WebSocket 通知 contentType 都收敛在 `ImContentTypeEnum` 一个枚举里，编号大量复用 OpenIM 段位：聊天消息 101-105（文本/图片/语音/视频/文件）、好友通知 1201-1210、群事件 1501-1520、通话信令 1601-1603（`persistent=false` 不入库）、RTC 通话 tip 1610/1611（入库）、撤回 2101、回执 2200、已读 2201、频道扩展自 125 起步。每个枚举值带 `persistent`（是否入 `im_xxx_message` 表，决定离线 pull 能否拉到）和 `normal`（是否计会话未读）两个标志；内部触达类消息（RTC_CALL_END、群事件等）靠 `sendGroupMessage(senderId, dto)` 重载按 `type.persistent` 决定落库，并用 `ImContentTypeEnum.validate` 强制登记。

**解决**: 加类型先在枚举里按段位表选号并正确配置 persistent / normal；需要「仅在线推送、离线丢弃」的信号类设 `persistent=false`；需要「多端同步但不打扰对方」的场景参考 `silentReAddFriend` 的 `setPersistent(false)` 单边语义（senderId 收 `ImPrivateMessageSendDTO`，对方完全不感知）。

### 6.2 错误码段位 1_040_XXX_XXX 与权限点 im:manager:{域}:{操作} 的登记约定

**问题**: 新增业务域时错误码随手编号，与其它段位撞号导致前端文案错乱；新加的用户侧接口照抄 manager 侧的 `@PreAuthorize`，Web 客户端全部 403。

**原因**: im 错误码固定用 `1_040_000_000` 段，域内再分段（`ErrorCodeConstants`）：消息 1_040_300_xxx、群 1_040_400_xxx、群成员 1_040_500_xxx、加群申请 1_040_510_xxx、好友 1_040_600_xxx、好友申请 1_040_610_xxx、敏感词 1_040_700_xxx、表情 1_040_800_xxx、频道 1_040_810_xxx、RTC 1_040_900_xxx（段内 001 / 006 / 012 等空号是历史预留，新增按已有最大值顺延）。权限模型是双轨：用户侧控制器（channel / face / friend / group / message / rtc 业务域包）全部**无** `@PreAuthorize`，只靠登录态 + 业务校验（`validateParticipant`、`validateMemberInGroup` 等从 `getLoginUserId` 推操作者）；运营侧 `controller/admin/manager` 统一 `im:manager:{域}:{操作}`，仅 `ImChannelManagerController` 与 `ImChannelMaterialManagerController` 的 `/simple-list` 两个端点无权限注解。

**解决**: 新域先查 `ErrorCodeConstants` 选段位，权限点按 `im:manager:{域}:{操作}` 登记 SQL 菜单；用户侧接口永远不接收参数里的 userId，一律 `getLoginUserId()` 推导，防越权靠业务校验而不是注解。
