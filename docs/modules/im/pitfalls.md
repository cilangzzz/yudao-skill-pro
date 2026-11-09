# 注意事项与已知坑点

> 使用 im 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 DO 继承 BaseDO 不等于「忽略租户」：租户插件仍会拼接 tenant_id

**问题**: 两个方向的误解都会踩坑：一是以为 DO 继承 `BaseDO`（未映射 tenantId 字段）就会跳过租户过滤，新建表漏加 `tenant_id` 列，启动后 SQL 报「Unknown column 'tenant_id'」；二是反过来以为只有继承 `TenantBaseDO` 才参与租户，从而得出「im 数据全租户共享」的错误结论，写全局统计 / 清理时漏掉租户隔离前提。

**原因**: 框架判定逻辑在 `TenantDatabaseInterceptor#computeIgnoreTable`，并非「继承 TenantBaseDO 才拦截」：找不到 TableInfo（非本项目表）→ 忽略；实体类带 `@TenantIgnore` → 忽略；其余一律**不忽略**，包括只继承 `BaseDO` 的普通实体。im 的 17 个 `@TableName` DO（`ImGroupDO`、`ImFriendDO`、`ImPrivateMessageDO`、`ImRtcCallDO` 等）全部只继承 `BaseDO`、也未加 `@TenantIgnore`，因此租户插件照常给 SQL 追加 `tenant_id = ?`（查询）与 tenant_id 插入值；模块单测建表脚本 `create_tables.sql` 中每张 im 表都带 `tenant_id bigint NOT NULL DEFAULT 0`。`TenantBaseDO` 的作用只是把 tenantId 映射为 DO 字段（需要在 DO/VO 读写租户号的场景），并不决定是否拦截。整个模块唯一的 `@TenantIgnore` 在 LiveKit Webhook 入口（见 1.2）。

**解决**: im 新增表必须带 `tenant_id` 列，DO 继承 `BaseDO` 即可，不要把它当成「忽略租户」的标志。若某张表确实要全租户共享，需要在实体类上标 `@TenantIgnore`（并确认跨租户读写语义可接受），或把表加入 `yudao.tenant.ignore-tables`；这属于改变数据隔离语义的决策，不能只改基类。

### 1.2 LiveKit Webhook 是唯一的 @PermitAll + @TenantIgnore 端点，整条链路运行在无租户上下文中

**问题**: 在 `ImRtcCallServiceImpl#handleLiveKitEvent` 的调用链里新增逻辑时，调用了需要租户上下文的代码（如 `TenantContextHolder.getRequiredTenantId()`、租户级缓存、带租户过滤的跨模块 API），本机联调不报错（请求碰巧带了租户头），生产环境 LiveKit 回调时抛 `NullPointerException: TenantContextHolder 不存在租户编号` 或查不到数据。

**原因**: `ImRtcLiveKitController#webhook` 是模块内唯一的 `@PermitAll + @TenantIgnore` 端点。框架启动时会把带 `@TenantIgnore` 的接口 URL 自动加入 `TenantSecurityWebFilter` 的忽略清单（`YudaoTenantAutoConfiguration#getTenantIgnoreUrls`），请求不带 tenant-id 头也放行，并设置 `TenantContextHolder.setIgnore(true)`。此后整条链路（签名校验 → `handleParticipantLeft` / `handleRoomFinished` → `endSession` → 消息落库、WebSocket 推送）都没有租户编号。

**解决**: Webhook 链路内保持「租户无关」：只操作 im 自身表（`TenantContextHolder.isIgnore()` 为 true 时租户插件不追加 tenant_id 条件，按主键 / room / userId 精确定位即可），不调用任何 `getRequiredTenantId()` 或依赖租户上下文的组件。需要跨模块取用户信息时用 `adminUserApi.getUser(userId)` 按 id 查（ignore 态下不过租户过滤，仍能查到）。安全由 `liveKitClient.verifyWebhookSignature` 的 JWT + body sha256 签名校验兜底，不要为了「方便联调」把签名校验短路。

### 1.3 @TenantIgnore 上下文里 Spring Cache 键不带租户后缀，webhook 链路与正常请求是两套缓存

**问题**: 群成员被移出后，LiveKit Webhook 兜底触发的群通话结束通知（RTC_CALL_END）偶尔仍把已移除成员算进接收者，最长持续约 1 小时。

**原因**: `TenantRedisCacheManager#getCache` 在租户上下文正常时给缓存名拼后缀（`group_member_ids:{groupId}:{tenantId}`），但 `TenantContextHolder.isIgnore()` 为 true 时保持原名。Webhook 链路 `endSession → pushCallChatMessage → ImGroupMessageServiceImpl#sendGroupMessage → ImGroupMemberServiceImpl#getActiveGroupMemberUserIdsByGroupId`（`@Cacheable(GROUP_MEMBER_IDS)`）读写的是**无后缀**的 `group_member_ids:{groupId}`；而正常请求路径的 `@CacheEvict`（`addGroupMember` / `removeGroupMember` 等）只清**带后缀**的键。两套缓存互不感知，无后缀那份只能靠 `spring.cache.redis.time-to-live: 1h` 过期兜底。

**解决**: 认识到这是已知边界，依赖 1h TTL 收敛即可，影响仅限通知受众多算（条件 UPDATE 保证状态机本身不受影响）。若要彻底消除，可在 Webhook 链路读成员时绕过 Spring Cache（直接走 `groupMemberMapper` 查询），或在 `invalidateSensitiveWordBsCaches` 同款的主动失效里补 `invalidateAll`。注意不要在正常请求路径里也读无后缀键，否则同一份数据两处缓存更难排查。

### 1.4 RTC 兜底 Job 必须保留 @TenantJob：Job 按租户逐个执行，im 表也按租户隔离

**问题**: 部署多租户环境后，`ImRtcCallCleanupJob`（僵尸通话清理）和 `ImRtcParticipantTimeoutJob`（振铃超时）每次调度的耗时随租户数增长，容易被误判为「重复扫描」而去掉 `@TenantJob`，结果 Job 在没有租户上下文时直接失败（`getRequiredTenantId()` 抛异常）或查不到任何数据。

**原因**: `TenantJobAspect#around` 会取全量租户列表并 `parallelStream` 逐租户执行（`TenantUtils.execute(tenantId, ...)`）。im 表虽只继承 `BaseDO`，但仍受租户插件过滤（见 1.1），每个租户的执行只会扫到本租户 `tenant_id` 的数据：`cleanupZombieCalls` 扫 `selectListByStatusInAndStartTimeBefore`，`timeoutInvitingParticipants` 扫 `selectListByStatusAndInviteTimeBefore`。因此开销是「租户数 × 单租户数据量」的累加，而不是同一批全局行被扫 N 遍；同一租户内多实例并发命中同一通话时，靠 `endSession` / `timeoutInvitingParticipant` 的条件 UPDATE（影响 0 行即跳过）保证不重复处理。

**解决**: 保留 `@TenantJob`，不要改成单次全局执行（那样没有租户上下文，且会漏掉其它租户的数据）。耗时随租户增多属于预期；若单租户数据量大，调大 `cleanupZombieThresholdMinutes` / `inviteTimeoutMinutes`（`ImProperties.Rtc`，默认 5 / 1 分钟）降低扫描频率。

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

**问题**: 新消息类型没登记枚举，发送时 `ImContentTypeEnum.validate(type)` 直接 `Assert` 失败；或者登记了但标志位配错：`persistent` 错会让离线用户 pull 不到（或系统事件被错误落库），`normal` 错会让引导用户消息被当成系统事件拒绝发送，或让系统事件被当成普通聊天消息（可发送 / 可置顶 / 计入运营统计）。

**原因**: 模块的消息类型、WebSocket 通知 contentType 都收敛在 `ImContentTypeEnum` 一个枚举里，编号大量复用 OpenIM 段位：普通聊天消息 101 文本 / 102 图片 / 103 语音 / 104 视频 / 105 文件 / 107 合并转发 / 108 名片 / 115 表情 / 125 素材（频道扩展段起步）、好友通知 1201-1210、群事件 1501-1533、通话信令 1601-1603（`persistent=false` 不入库）、RTC 通话 tip 1610/1611（入库）、撤回 2101、回执 2200、已读 2201。每个枚举值带两个标志：`persistent`（是否入 `im_xxx_message` 表，决定离线 pull 能否拉到）与 `normal`（是否普通用户聊天消息：决定用户能否发送、能否被置顶、是否计入运营统计）；内部触达类消息（RTC_CALL_END、群事件等）靠 `sendGroupMessage(senderId, dto)` 重载按 `type.persistent` 决定落库，并用 `ImContentTypeEnum.validate` 强制登记。

**解决**: 加类型先在枚举里按段位表选号并正确配置 persistent / normal；需要「仅在线推送、离线丢弃」的信号类设 `persistent=false`；需要「多端同步但不打扰对方」的场景参考 `silentReAddFriend` 的 `setPersistent(false)` 单边语义（senderId 收 `ImPrivateMessageSendDTO`，对方完全不感知）。

### 6.2 错误码段位 1_040_XXX_XXX 与权限点 im:manager:{域}:{操作} 的登记约定

**问题**: 新增业务域时错误码随手编号，与其它段位撞号导致前端文案错乱；新加的用户侧接口照抄 manager 侧的 `@PreAuthorize`，Web 客户端全部 403。

**原因**: im 错误码固定用 `1_040_000_000` 段，域内再分段（`ErrorCodeConstants`）：消息 1_040_300_xxx、群 1_040_400_xxx、群成员 1_040_500_xxx、加群申请 1_040_510_xxx、好友 1_040_600_xxx、好友申请 1_040_610_xxx、敏感词 1_040_700_xxx、表情 1_040_800_xxx、频道 1_040_810_xxx、RTC 1_040_900_xxx（部分子段存在历史空号，如消息段的 001 / 006 / 012、群成员段的 000 / 002；新增按该子段已有最大值顺延，不要回填空号）。权限模型是双轨：用户侧控制器（channel / face / friend / group / message / rtc 业务域包）全部**无** `@PreAuthorize`，只靠登录态 + 业务校验（`validateParticipant`、`validateMemberInGroup` 等从 `getLoginUserId` 推操作者）；运营侧 `controller/admin/manager` 统一 `im:manager:{域}:{操作}`，仅 `ImChannelManagerController` 与 `ImChannelMaterialManagerController` 的 `/simple-list` 两个端点无权限注解。

**解决**: 新域先查 `ErrorCodeConstants` 选段位，权限点按 `im:manager:{域}:{操作}` 登记 SQL 菜单；用户侧接口永远不接收参数里的 userId，一律 `getLoginUserId()` 推导，防越权靠业务校验而不是注解。

### 6.3 新增或移动 VO 时包目录必须全小写（`useritem`，不是 `userItem`）

**问题**: 新增表情包个人表情 VO 时照旧目录或按 Windows 本地习惯写成 `controller/admin/face/vo/userItem/`，本机编译通过，提交到 Linux CI 后报「程序包不存在」或找不到 `ImFaceUserItemRespVO`。

**原因**: Windows 文件系统大小写不敏感，Linux 大小写敏感。模块已将两个个人表情 VO 统一到全小写目录 `controller/admin/face/vo/useritem/`，`package` 声明同步为 `cn.iocoder.yudao.module.im.controller.admin.face.vo.useritem`，控制器 import 也使用小写路径。

**解决**: 新建、移动 VO 时目录名与 `package` / `import` 全部使用小写 `useritem`；不要保留 `userItem` 目录或大小写混用的路径。

## 7. 多数据库兼容与 DAL 约定

### 7.1 手写 SQL / Wrapper 不要硬编码 `LIMIT`、`FOR UPDATE`、`DATE()`

**问题**: 二次开发复制旧代码，继续写 `.last("LIMIT " + size)`、`.last("FOR UPDATE")`、手写统计 SQL 里的 `DATE(create_time)`；MySQL 联调一切正常，切到 PostgreSQL / Oracle / SQL Server 后报语法错误或统计结果类型不一致。

**原因**: im 已适配多数据库，相关能力由基线之后新增的框架层提供：`SqlDialectUtils` 按实际执行的数据源输出日期分桶、行数限制等片段；`BaseMapperX#selectListLimitN` 走 MyBatis-Plus 分页插件生成 `LIMIT` / `FETCH FIRST` / `OFFSET ... FETCH`；`selectOneForUpdate` 由锁定读拦截器改写锁定 SQL。硬编码会绕过这些适配。

**解决**: 沿用 im 既有 Mapper 写法完成替换：

| 旧写法 | 新写法 |
|---|---|
| `.last("LIMIT " + n)` + `selectList(...)` | `selectListLimitN(wrapper, n)` |
| `.last("FOR UPDATE")` + `selectOne(...)` | `selectOneForUpdate(...)`；群记录用 `ImGroupMapper#selectByIdForUpdate` |
| 手写 `@Select` 中的 `DATE(col)` | `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@date('col')}`，`SELECT` 与 `GROUP BY` 复用同一片段 |
| 手写 `@Select` 中的 `LIMIT #{limit}` | `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@limitParam('limit', true)}` |

这些是框架能力，不要写成 im 模块自研逻辑。

### 7.2 `selectListLimitN` 的边界行为，以及 SQL Server 的排序要求

**问题**: 给 `selectListLimitN` 传 0 或负数，或复用到 SQL Server 时抛分页语法错误；也有人在它外面再叠加 `.last("LIMIT ...")`，导致限量重复或 SQL 解析失败。

**原因**: 框架实现为：`limit == 0` 不查询、直接返回空列表；`limit < 0` 抛 `IllegalArgumentException`（因为分页插件会把负数 size 视为不分页，从而查全表）；内部走 `selectPage` 且不执行 COUNT。SQL Server 的 `OFFSET ... FETCH` 必须跟在 `ORDER BY` 之后，因此 Wrapper 需要设置排序。

**解决**: 调用前保证 `limit >= 1`；im 的增量拉取/历史查询均已在 Wrapper 上设置 `orderByAsc` / `orderByDesc`，新增查询也必须保留排序；不要再叠加 `.last("LIMIT ...")`。对外接口的入参校验（`size` / `limit` 上的 `@Min(1)`，部分列表接口另有 `@Max(200)`）继续保留。

### 7.3 `selectOneForUpdate` 必须在事务中调用，且 Wrapper 不能带 `last` / `groupBy` / `having` / 参数别名

**问题**: 在无事务的方法里调用锁定读，看似查到了数据但并发下仍会超卖/重复操作；或者给锁定读 Wrapper 加了 `last("LIMIT 1")`、`groupBy`、自定义参数别名，直接抛 `IllegalArgumentException`。

**原因**: 锁定读依赖数据库行锁，auto-commit 下语句结束即释放锁，起不到互斥作用；框架的 `checkForUpdateWrapper` 会校验 Wrapper：`last`、`groupBy`、`having`、参数别名都会使内置锁定 SQL 与条件片段不一致，因此主动拒绝。

**解决**: 在 `@Transactional(rollbackFor = Exception.class)` 的公开方法内调用；Wrapper 只使用实体字段条件与排序。群操作的锁定读路径（`validateGroupOwnerForUpdate` / `validateGroupExistsForUpdate`）目前都在事务方法内：群治理类方法自身带 `@Transactional`，`validateMemberCountLimit` 自身未标注，但调用方 `ImGroupRequestServiceImpl#applyJoinGroup` / `#agreeGroupRequest` 带 `@Transactional`。新增群治理逻辑时不要绕开这两个方法直接查群，也不要在无事务的方法里调用锁定读。

### 7.4 统计 SQL 行键是 `statDate` / `sizeRange`，对外接口字段仍是 `range`

**问题**: 二次开发读取看板统计结果时仍用 `row.get("date")` / `row.get("range")`，得到 null 或类型转换异常；或者误以为接口契约变了，把 `ImStatisticsManagerGroupSizeRespVO.range` 也改掉导致前端字段消失。

**原因**: 手写统计 SQL 的列别名已改为 `statDate`（按天统计）与 `sizeRange`（群规模分桶），避免 `date`、`range` 等数据库保留字在部分数据库上报错。`ImStatisticsManagerServiceImpl` 已同步读取新键（`toDailyCountMap` 读 `statDate`，`getGroupSizeCountMap` 读 `sizeRange`），但 Controller 组装响应时仍映射到 VO 的 `range` / `count`，对外契约不变。

**解决**: 业务侧读取 Mapper 返回的 `Map` 时使用 `statDate` / `sizeRange`；对外响应继续使用原有字段名，不要混用内外两层命名。新增统计 SQL 时同样给别名取业务名，避开数据库保留字。
