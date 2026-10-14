# 注意事项与已知坑点

> 使用 mp（微信公众号）模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 微信回调端点的租户上下文是手动恢复的，新代码不能脱离该调用链

**问题**: 微信服务器推送消息/事件到 `/mp/open/{appId}` 时，请求不带租户标识，框架的自动多租户被 `@TenantIgnore` 关闭。二次开发时如果在 Handler 里直接查 `mp_account` 等租户表，会抛 `TenantContextHolder 不存在租户编号` 空指针异常。

**原因**: `MpOpenController#handleMessage` 上标注 `@TenantIgnore`，先从本地缓存按 appId 定位账号，再用 `TenantUtils.execute(account.getTenantId(), ...)` 手动把租户上下文包住整个消息路由过程，并在 `finally` 中 `MpContextHolder.clear()`。租户上下文只在这个方法内部有效。

**解决**:
- 新增回调处理逻辑时，挂在 `WxMpMessageHandler` 体系内由 `DefaultMpServiceFactory#buildMpMessageRouter` 路由，天然处于租户上下文中。
- 需要公众号 appId 时从 `MpContextHolder.getAppId()` 获取（`MpOpenController` 已 `setAppId`），不要自己解析。
- 如果绕开 `MpOpenController` 自建回调入口，必须复刻同样的 `@TenantIgnore` + `TenantUtils.execute` + `MpContextHolder.setAppId/clear` 三件套。

### 1.2 8 张表中只有 mp_account 做了 DB 层租户隔离，其余表靠 appId 冗余字段隔离

**问题**: 以为所有 mp 表都会自动拼 `tenant_id`，自己写的查询不带账号条件，结果查出所有租户、所有公众号的数据（粉丝、消息串号）。

**原因**: 只有 `MpAccountDO` 继承 `TenantBaseDO`；`MpUserDO`、`MpMessageDO`、`MpTagDO`、`MpMenuDO`、`MpAutoReplyDO`、`MpMaterialDO`、`MpMessageTemplateDO` 都继承 `BaseDO`，`TenantDatabaseInterceptor#computeIgnoreTable` 对非 `TenantBaseDO` 实体直接忽略租户过滤。这些表的数据隔离依赖 `appId` / `accountId` 冗余列，例如 `MpUserServiceImpl#saveUser` 用 `selectByAppIdAndOpenid` 定位粉丝。

**解决**: 自写 Mapper 查询时必须显式带上 `appId` 或 `accountId` 条件（项目内 Mapper 均以 `selectListByAccountId`、`selectByAppIdAndXxx` 命名，可循此惯例）；写入时通过 Convert 层从 `MpAccountDO` 回填 `accountId` + `appId` 两个冗余字段，缺一不可。

## 2. 缓存相关

### 2.1 公众号账号缓存在 JVM 本地，多节点最长 60 秒不一致

**问题**: 新增/修改公众号后，立刻在另一台节点上调用回调校验或粉丝同步，报 `找到对应 appId(xxx) 的 WxMpService，请核实！`（`MpServiceFactory#getRequiredMpService` 的断言）。

**原因**: `MpAccountServiceImpl#initLocalCache` 在 `@PostConstruct` 中把全部账号加载进 `volatile Map<String, MpAccountDO> accountCache`，并联动 `mpServiceFactory.init(accounts)` 重建 `WxMpService`/`WxMpMessageRouter`；节点间同步靠 `@Scheduled(fixedRate = 60, timeUnit = SECONDS)` 的 `refreshLocalCache` 轮询 `update_time` 变化，而 `createAccount/updateAccount/deleteAccount` 里的 `initLocalCache()` 只刷新本节点。

**解决**: 多节点部署要容忍最长 60 秒的缓存窗口；账号变更后不要立即依赖其它节点生效。如需强一致，可改造为 Redis 发布订阅通知各节点主动 `initLocalCache`（项目尚未实现）。

### 2.2 逻辑删除的账号对轮询刷新"不可见"，建表前异常被静默吞掉

**问题**: 删除公众号后，其它节点缓存里该账号长期残留，回调仍会路由到已删除账号；新环境忘了导入 mp 表结构时，启动不报错，但所有回调报 `公众号 appId(xxx) 不存在`。

**原因**: 两个盲区都在 `MpAccountServiceImpl`：其一，`refreshLocalCache` 用 `selectCountByUpdateTimeGt`（裸 SQL `WHERE update_time > #{maxUpdateTime}`）判断变更，而 `deleteById` 是逻辑删除、不更新 `update_time`，删除动作不会触发其它节点刷新；其二，`initLocalCache` 捕获 `Throwable` 且仅当消息包含 `doesn't exist` 时只打 error 日志（提示参考 https://doc.iocoder.cn/mp/build/ ），表未建时缓存静默为空。

**解决**: 删除账号后建议同步调用 `mpServiceFactory` 重建或直接清理对应缓存条目；新环境部署先按官方文档执行 mp 模块建表 SQL，再用 `/mp/open/{appId}` 联调回调。

### 2.3 access_token 存 Redis 共享，keyPrefix 混用会互相覆盖

**问题**: 多实例或多环境共用一个 Redis 时，公众号 access_token 出现互相覆盖、频繁刷新或 40001 invalid credential。

**原因**: `DefaultMpServiceFactory#buildMpService` 用 `WxMpRedisConfigImpl(redisTemplateWxRedisOps, mpProperties.getConfigStorage().getKeyPrefix())` 存储 token，Redis key 前缀来自 `wx.mp.config-storage.key-prefix` 配置，所有 `WxMpService` 实例共用同一个前缀空间。

**解决**: 不同环境/不同集群务必配置不同的 `key-prefix`；同一 Redis 内多套 yudao 环境尤其要注意。

## 3. 事务相关

### 3.1 "先调微信接口、后写本地库"的两步写不是原子的

**问题**: 创建/更新/删除标签、菜单、模板时，微信平台操作成功但本地数据库写入失败，造成平台与本地数据不一致（如平台上多出一个本地没有的"孤儿标签"，下次 `syncTag` 才能纠正）。

**原因**: `MpTagServiceImpl#createTag/updateTag/deleteTag`、`MpMenuServiceImpl#saveMenu/deleteMenuByAccountId`、`MpMessageTemplateServiceImpl#deleteMessageTemplate` 都是第一步调 `WxMpService` 远程接口，第二步才操作 `mpTagMapper`/`mpMenuMapper`；中间任一 DB 异常，微信侧已生效且无法被本地事务回滚。

**解决**: 二次开发遵循同样顺序（先平台后落库），并接受"以平台为准 + 手动同步兜底"的最终一致模型；对一致性要求高的场景，第二步失败时捕获并调用平台对应删除/回退接口补偿。

### 3.2 @Transactional 包裹了微信远程调用，形成长事务占用数据库连接

**问题**: 保存菜单、同步标签/模板时微信接口响应慢（超时数秒），数据库连接被长时间占用，高并发下连接池耗尽。

**原因**: `MpMenuServiceImpl#saveMenu`、`MpTagServiceImpl#syncTag`、`MpMessageTemplateServiceImpl#syncMessageTemplate` 的 `@Transactional(rollbackFor = Exception.class)` 覆盖了整个方法体，`menuCreate`/`tagGet`/`getAllPrivateTemplate` 等 HTTP 调用都在事务内执行。

**解决**: 扩展此类逻辑时，把远程调用移出事务（先调用微信拿到结果，再开短事务批量落库），或改用 `TransactionTemplate` 只包裹本地写操作段。

## 4. 异步与上下文传递

### 4.1 @Async 的 syncUser 依赖 TTL 装饰器传递租户上下文，且是 fire-and-forget

**问题**: 自定义线程池跑粉丝同步时报 `TenantContextHolder 不存在租户编号`；或前端点"同步粉丝"后返回成功，但后台实际同步失败却无任何提示。

**原因**: `MpUserServiceImpl#syncUser` 标注 `@Async`，在 `MpUserController#syncUser` 中直接调用后立即返回 `true`；方法内部 `mpAccountService.getRequiredAccount(accountId)` 会查租户表 `mp_account`，租户上下文能传进异步线程全靠 `YudaoAsyncAutoConfiguration` 给异步执行器设置的 `TtlRunnable` TaskDecorator。同步过程中 `WxErrorException` 仅 `log.error` 后 `break`。

**解决**: 自定义异步线程池必须同样包 `TtlRunnable::get`（或复用 Spring 的 `ThreadPoolTaskExecutor`）；需要同步结果时，不要依赖该接口返回值，应轮询 `mp_user` 数据或自行改造为同步执行 + 进度落库。

### 4.2 WxMpMessageRouter 的异步规则跑在内建线程池里，不走 Spring 的 TTL 装饰器

**问题**: 自定义消息 Handler 时发现 `MpContextHolder.getAppId()` 或租户上下文"时有时无"，或消息记录延迟、异常"消失"。

**原因**: `DefaultMpServiceFactory#buildMpMessageRouter` 中，第一条规则 `router.rule().handler(messageReceiveHandler).next()` 未显式 `async(false)`，而 WxJava `WxMpMessageRouterRule` 构造时默认 `async = true`，因此 `MessageReceiveHandler`（记录消息）被提交到 Router 自建的 `ThreadPoolExecutor`（非 Spring 管理、无 TTL 包装）执行；其余业务 Handler 均显式 `async(false)` 在回调线程同步执行。此外 `MpMessageServiceImpl#receiveMessage` 在粉丝尚未落库时会 `ThreadUtil.sleep(5, SECONDS)` 重试 3 次（最多阻塞 15 秒），占用 Router 线程池线程——这是代码注释里明确写出的"异步记录与 SubscribeHandler 落库的竞态"兜底。

**解决**: 自定义 Handler 一律显式声明 `async(false)`（需要同步返回 XML 响应时必须如此）；不要在 Handler 内依赖租户上下文查租户表（消息记录只用 `accountCache` + 非租户表，所以能工作）；关注高并发关注事件时评估 Router 线程池排队风险。

## 5. 消息幂等

### 5.1 微信超时重推没有 MsgId 去重，消息会重复入库、自动回复会重复发送

**问题**: 微信服务器 5 秒内未收到 XML 响应会重试推送（最多 3 次），粉丝收到重复的欢迎语/自动回复，`mp_message` 出现重复记录。

**原因**: `MpMessageDO` 只把 `msgId` 作为普通字段存储，全模块没有任何按 `msgId` 的查重逻辑或唯一索引；`MessageReceiveHandler` 收到重推消息会再次走 `receiveMessage` 落库，`MessageAutoReplyHandler` 会再次触发 `replyForMessage` 回复。

**解决**: 给 `mp_message` 增加 `(appId, msg_id)` 唯一索引，或在 `receiveMessage`/`replyForMessage` 入口先按 `wxMessage.getMsgId()` 查重；事件类消息（无 msgId）可按 `createTime + fromUser + event` 组合近似判重。

## 6. 错误码与权限标识

### 6.1 appId 重复校验借用了 system 模块的错误码，提示信息与场景不符

**问题**: 新增公众号填了重复的 appId，前端报"用户账号已经存在"（错误码 1_002_003_000），用户和运维都摸不着头脑；按错误码段做监控统计时该报错被记到 system 模块头上。

**原因**: `MpAccountServiceImpl#validateAppIdUnique` 直接 `throw exception(USER_USERNAME_EXISTS)`，静态导入了 `cn.iocoder.yudao.module.system.enums.ErrorCodeConstants.USER_USERNAME_EXISTS`，而 mp 自己的错误码段是 1_006_000_000 起（`ErrorCodeConstants`），账号段只定义到 1_006_000_002，没有 appId 重复的错误码。

**解决**: 在 mp 的 `ErrorCodeConstants` 账号段补充如 `ACCOUNT_APPID_EXISTS = 1_006_000_003 "公众号 appId 已存在"` 并替换引用；排查该类报错时记得先看入参是 appId 还是用户名。

### 6.2 MpTagController 的 list-all-simple 权限标识疑似复制粘贴笔误

**问题**: 只授予 `mp:tag:query` 权限的角色无法使用标签下拉框（`GET /mp/tag/list-all-simple`），反而需要 `mp:account:query` 权限。

**原因**: `MpTagController#listAllSimple` 标注 `@PreAuthorize("@ss.hasPermission('mp:account:query')")`，且 `@Operation(summary = "获取公众号账号精简信息列表")`——从 `MpAccountController` 复制后权限和描述都忘了改，返回的实际是标签列表（`convertList02`）。源码保持原样，此处如实标注。

**解决**: 给角色分配权限时按现状授予 `mp:account:query`；改造时建议改为 `mp:tag:query` 并同步修正 summary 文案（注意前端菜单权限标识配套调整）。

## 7. 数据模型

### 7.1 mp_tag 的主键 id 与微信标签 tagId 是两个字段，粉丝 tagIds 关联的是后者

**问题**: 前端或二次开发把 `mp_tag.id`（本地自增主键）当成微信标签 id 传给粉丝标签更新，调用微信 `batchTagging` 失败或打错标签。

**原因**: `MpTagDO` 主键标注 `@TableId(type = IdType.INPUT)`，另有独立的 `tagId` 字段存微信标签 id（`MpTagConvert` 映射 `WxUserTag.id -> tagId` 且插入时 `id` 为 `ignore`）；`MpUserServiceImpl#updateUserTag` 把 `MpUserUpdateReqVO#tagIds` 的值直接传给 `mpService.getUserTagService().batchTagging(tagId, ...)`，即这些值必须是微信标签 id（`MpUserDO#tagIds` 关联 `MpTagDO#tagId` 而非 `id`）；`MpTagServiceImpl#syncTag` 合并数据也以 `tagId` 为匹配键。

**解决**: 前端粉丝标签下拉应取 `MpTagRespVO` 的 `tagId` 字段作为提交值；判断两个标签是否同一，永远用 `tagId` 比对，不要用本地主键 `id`。

### 7.2 MpMessageDO.Article 被菜单、自动回复以 JSON 复用，改字段影响三张表的存量数据

**问题**: 修改 `MpMessageDO.Article`（图文消息内嵌类）的字段名或类型后，自定义菜单（`mp_menu.reply_articles`）、自动回复（`mp_auto_reply.response_articles`）的存量 JSON 反序列化报错或丢字段，图文回复/菜单点击回复异常。

**原因**: `MpMessageDO.Article` 同时被 `MpMenuDO#replyArticles` 和 `MpAutoReplyDO#responseArticles` 以 `@TableField(typeHandler = JacksonTypeHandler.class)` 存储（三张表的 DO 均已开 `autoResultMap = true`），JSON 结构与 Java 类强耦合。

**解决**: 对 `Article` 只做加字段（可空兼容）演进，禁止改字段名/类型；确需破坏性变更时，先写数据迁移脚本刷三张表的 JSON 列。新增图文类场景应复用 `MpMessageDO.Article` 而不是另造一个结构。
