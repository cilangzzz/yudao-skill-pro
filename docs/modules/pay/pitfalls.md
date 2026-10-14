# 注意事项与已知坑点

> 使用 pay 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 渠道回调入口关闭了租户上下文，靠 Service 层手动恢复

**问题**: 支付渠道（微信/支付宝）的回调请求没有登录态、也没有请求头里的租户标识。`PayNotifyController` 的 `notifyOrder`/`notifyRefund`/`notifyTransfer` 三个入口都标注了 `@PermitAll` + `@TenantIgnore`，此时 `TenantContextHolder` 中没有租户；若直接在 Controller 里查询/更新 `PayChannelDO`、`PayNotifyTaskDO` 等 `TenantBaseDO` 表，会因租户过滤（`tenant_id = null`）查不到数据或写入错误租户。

**原因**: 回调来自第三方渠道服务器，无法携带租户信息，因此框架层先禁用租户过滤，由 Service 层从渠道记录中反查租户。

**解决**: 保持现有模式：Controller 里只做渠道解析，租户内操作统一交给 Service 层包裹的 `TenantUtils.execute(channel.getTenantId(), ...)`。例如 `PayOrderServiceImpl.notifyOrder(Long channelId, PayOrderRespDTO notify)`：

```java
PayChannelDO channel = channelService.validPayChannel(channelId);
TenantUtils.execute(channel.getTenantId(), () -> getSelf().notifyOrder(channel, notify));
```

新增回调入口（如自定义渠道）时必须复用这一模式，不能省略 `TenantUtils.execute`。

### 1.2 异步通知链路的租户传递依赖两处显式代码

**问题**: `PayNotifyServiceImpl.executeNotifyAsync` 在独立线程池（`NOTIFY_THREAD_POOL_TASK_EXECUTOR`）中执行，线程上没有租户上下文；同时最终回调业务方的 HTTP 请求是裸的 `HttpUtil.createPost(...)`，业务方接口若开启了租户过滤，会因缺少 `tenant-id` 请求头被拦截。

**原因**: 任务扫描由 `PayNotifyJob` 的 `@TenantJob` 按租户逐个执行，保证 `selectListByNotify()` 能查到 `PayNotifyTaskDO`（`TenantBaseDO`）；但线程池切换和跨服务 HTTP 调用都不会自动传递租户。

**解决**: 两处约定都不能动：一是所有支付相关定时任务（`PayNotifyJob`/`PayOrderSyncJob`/`PayOrderExpireJob`/`PayRefundSyncJob`/`PayTransferSyncJob`）必须保留 `@TenantJob` 注解；二是 `executeNotifyInvoke` 回调业务方时通过 `TenantUtils.addTenantHeader(headers, task.getTenantId())` 显式带上租户头。业务方自己的"更新支付状态"回调接口也应支持该请求头鉴权。

## 2. 事务相关

### 2.1 submitOrder 故意不加事务注解，重构时不要"补上"

**问题**: `PayOrderServiceImpl.submitOrder` 上没有 `@Transactional`，看起来像遗漏。如果有人好心加上，会导致：调用渠道下单失败时，本地 `PayOrderExtensionDO`（支付拓展单）一起被回滚，而渠道侧实际可能已经创建了预支付单，两边数据从此对不上，重试时还会用新的拓展单号重复下单。

**原因**: 代码中有明确注释：`// 注意，这里不能添加事务注解，避免调用支付渠道失败时，将 PayOrderExtensionDO 回滚了`。拓展单是排查对账问题的关键留痕，必须先落库。

**解决**: 保持 `submitOrder` 无事务。本地单据（拓展单）先插入并提交，再调用 `client.unifiedOrder(...)`；渠道调用结果通过后续的 `notifyOrder` 回调/同步任务补偿，而不是靠事务回滚。

### 2.2 自调用导致 @Transactional / @Async 失效，模块内统一用 getSelf()

**问题**: `PayOrderServiceImpl.notifyOrder(PayChannelDO, PayOrderRespDTO)`、`PayRefundServiceImpl.notifyRefund`、`PayTransferServiceImpl.notifyTransfer`（`@Transactional`）以及 `PayNotifyServiceImpl.executeNotifyAsync`、`PayWalletRechargeServiceImpl.sendWalletRechargerPaidMessage`（`@Async`）都是同类内非接口方法。若通过 `this.xxx()` 直接调用，Spring AOP 代理不生效：事务不开启、异步退化为同步。

**原因**: Spring 的事务/异步基于代理对象，内部 this 调用绕过了代理。

**解决**: 模块内这些 Service 都提供了 `getSelf()`（`SpringUtil.getBean(getClass())`）获取自身代理。内部调用必须写 `getSelf().notifyOrder(channel, notify)`，方法上也保留了注释提醒（如 `// 注意，如果是方法内调用该方法，需要通过 getSelf().notifyTransfer(channel, notify) 调用，否则事务不生效`）。新增类似方法时沿用此模式，不要直接 this 调用。

### 2.3 createPayNotifyTask 依赖 afterCommit 回调，且必须在事务上下文中调用

**问题**: `PayNotifyServiceImpl.createPayNotifyTask` 通过 `TransactionSynchronizationManager.registerSynchronization` 在 `afterCommit` 里才发起异步通知（注释：`必须在事务提交后，在发起任务，否则 PayNotifyTaskDO 还没入库，就提前回调接入的业务`）。两点风险：一是在无事务的上下文中调用 `registerSynchronization` 会直接抛 `IllegalStateException`（事务同步未激活）；二是如果把异步通知挪到事务提交前执行，业务方回调进来查订单会查不到（状态还没提交）。

**原因**: `createPayNotifyTask` 的调用方 `notifyOrderSuccess`/`notifyRefundSuccess` 都处于 `@Transactional` 的 `notifyOrder`/`notifyRefund` 事务内，前置条件天然满足。

**解决**: 保持"事务内插入任务 + afterCommit 后异步执行"的结构。若业务方模块要接入类似"支付成功后通知"逻辑，同样要避免在事务未提交时触发对外通知。

### 2.4 通知任务的事务里包含最长 120 秒的 HTTP 回调

**问题**: `PayNotifyServiceImpl.executeNotify0` 标注了 `@Transactional`，而它内部 `executeNotifyInvoke` 发起的 HTTP 回调超时时间为 `NOTIFY_TIMEOUT_MILLIS`（120 秒）。业务方接口响应慢时，每个通知任务都会长时间占用一个数据库连接；`PayNotifyJob` 还会用线程池并发执行多个任务，连接池可能被拖垮。

**原因**: 事务边界覆盖了"HTTP 调用 + 写 PayNotifyLog + 更新 PayNotifyTask"全过程，IO 等待被包进了事务。

**解决**: 知晓该特性并在部署时保障：业务方回调接口要快速返回（收到即落库异步处理），`application.yaml` 中数据库连接池要留够余量；不要随意调大 `NOTIFY_TIMEOUT`，也不要把 `NOTIFY_THREAD_POOL_TASK_EXECUTOR` 的核心线程数改得过大。

## 3. 状态机相关

### 3.1 回调幂等靠 CAS 条件更新，并发重复回调抛异常属预期行为

**问题**: 支付渠道会重复推送回调（如支付宝/微信先有支付结果直接返回、后又推回调）。`PayOrderServiceImpl.updateOrderSuccess` 等更新都走 `updateByIdAndStatus(id, 期望旧状态, 新状态)`，更新数为 0 时抛 `PAY_ORDER_STATUS_IS_NOT_WAITING`；`submitOrder` 里同步触发 `getSelf().notifyOrder(...)` 时也可能因此抛异常。

**原因**: 状态流转（WAITING → SUCCESS → REFUND / CLOSED）不加悲观锁，全部依赖"旧状态匹配才更新"的乐观并发控制；已在代码注释中说明这是已知并发场景（参考 yudao-cloud issue I8SM9H）。

**解决**: 保持现有模式：重复成功回调直接 return 幂等跳过，CAS 失败抛出的异常在 `submitOrder` 中用 try-catch 降级为 warn 日志。新增回调处理逻辑时不要把这类异常当成系统错误告警，也不要改成"先查后改"的非原子写法。

### 3.2 过期关单与同步任务有严格的前置校验顺序，不能"先关再说"

**问题**: `PayOrderServiceImpl.expireOrder(order)` 必须先遍历该订单所有 `PayOrderExtensionDO`：拓展单已支付 → 直接返回不关单（可能是数据不一致）；渠道查询结果为已退款 → 返回并要求人工介入（说明丢了 SUCCESS 中间态）；渠道查询已支付 → 先补 `notifyOrder`。`syncOrder` 中查询渠道返回"订单不存在/已关闭"时也不能关闭本地订单——用户可能还没付完，渠道回调尚未到达。

**原因**: 定时任务是回调的兜底手段，优先级低于渠道回调；贸然关单会导致"用户实际支付成功、本地却是已关闭"的资损级故障。

**解决**: 修改 `expireOrder`/`syncOrder` 时保持"先拓展单、后主单；先查渠道、再落库"的顺序，保留 `syncOrder` 中对 `isClosed(respDTO.getStatus())` 直接 `return false` 的兜底注释逻辑，让订单随渠道一起过期后再关闭。

### 3.3 钱包充值退款的冻结/解冻状态机与 afterBalance 特例

**问题**: 钱包充值退款分三步：`PayWalletRechargeServiceImpl.refundWalletRecharge` 先 `payWalletService.freezePrice` 冻结余额并创建退款单（WAITING）；退款成功回调 `updateWalletRechargeRefunded` 调 `reduceWalletBalance(walletId, id, RECHARGE_REFUND, ...)` 只扣冻结金额；失败则 `unfreezePrice` 解冻。`PayWalletServiceImpl.reduceWalletBalance` 中 `RECHARGE_REFUND` 类型的流水 `afterBalance` 特殊处理为不减 `balance`（代码注释引用了知识星球讨论）。

**原因**: 充值退款扣的是 `freeze_price` 而不是 `balance`（冻结时余额已扣），若按普通扣减计算 afterBalance 会导致流水余额不连贯。

**解决**: 新增钱包资金操作时，先确认它扣的是 `balance` 还是 `freeze_price`，再决定流水 `afterBalance` 的算法；不要把 `RECHARGE_REFUND` 改成通用的减余额逻辑。另外注意 `freezePrice`/`unfreezePrice` 失败分别抛 `WALLET_BALANCE_NOT_ENOUGH` / `WALLET_FREEZE_PRICE_NOT_ENOUGH`，两个错误码不要混用。

## 4. 缓存与客户端相关

### 4.1 PayClient 是 JVM 本地缓存对象，删除渠道不清理、配置热更新靠 equals 比对

**问题**: `PayClientFactoryImpl` 用 `ConcurrentMap<Long, AbstractPayClient<?>> clients` 按 channelId 缓存客户端实例（持有 wxjava/alipay SDK 连接）。三个易踩坑点：一是 `getPayClient` 只查缓存不创建，查不到仅打 error 日志返回 null（调用方需自行抛 `CHANNEL_NOT_FOUND`）；二是 `PayChannelServiceImpl.deleteChannel` 只删除数据库记录，**不会**从工厂缓存中移除客户端，已删渠道的实例在进程内仍可解析回调；三是配置变更的热更新依赖下次 `getPayClient` → `createOrUpdatePayClient` 时 `AbstractPayClient.refresh(config)` 的 `config.equals(...)` 比对，比较逻辑依赖 `PayClientConfig` 的 equals 实现（Lombok `@Data`）。

**原因**: 客户端创建成本高（初始化 SDK），采用惰性创建 + 值比对刷新的策略。

**解决**: 新增 `PayClientConfig` 子类时必须带 `@Data`（保证 equals 覆盖全部配置字段），否则改配置不会触发 `refresh` 重新初始化，表现为"改了商户密钥但还是用旧密钥支付"。若需要彻底剔除已删渠道的客户端，需自行扩展工厂提供 `removeClient(channelId)` 能力。

## 5. 安全相关

### 5.1 回调接口 @PermitAll 的安全性完全依赖渠道验签

**问题**: `PayNotifyController` 三个回调入口均为 `@PermitAll` + `@TenantIgnore`，任何人都能 POST `/pay/notify/order/{channelId}` 等地址。安全防线只有一层：`payClient.parseOrderNotify(params, body, headers)` 内部的签名/加密校验（微信 V3 证书验签、支付宝 RSA 验签）。

**原因**: 渠道服务器无法携带系统登录态，只能靠验签证明请求来源。

**解决**: 新增自定义 `PayClient` 时，`doParseOrderNotify`/`doParseRefundNotify`/`doParseTransferNotify` 必须完整实现验签，校验失败直接抛异常，绝不能直接反序列化 body 就当支付成功处理。同时不要把 `channelId` 之外的敏感信息拼进回调 URL。

### 5.2 /pay/order/submit 没有 @PreAuthorize，钱包支付自动绑定当前登录用户

**问题**: `PayOrderController.submitPayOrder`（`POST /pay/order/submit`）仅要求登录、无权限标识，与其他 admin 接口的 `@PreAuthorize("@ss.hasPermission('pay:order:query')")` 风格不同。当 `channelCode = wallet` 时，Controller 会用 `getLoginUserId()`/`getLoginUserType()` 调 `payWalletService.getOrCreateWallet` 并把 `walletId` 塞进 `channelExtras`（`WalletPayClient.WALLET_ID_KEY`），即用户只能花自己的钱包。

**原因**: 提交支付是 C 端用户行为（该接口同时服务 admin/app 两端），按"登录即可"设计；钱包 ID 由服务端注入而非前端传入，防止越权扣他人钱包。

**解决**: 不要给该接口补上资源级权限（会导致普通用户无法支付）；也不要信任前端传入的 `walletId`——保持服务端覆盖 `channelExtras` 的写法。接入新的"账户类"支付渠道时，参照钱包模式在 Controller 层注入当前用户身份。

## 6. 错误码与通知重试相关

### 6.1 钱包等业务异常以"渠道错误码"形式透传，最终被包装成 PAY_ORDER_SUBMIT_CHANNEL_ERROR

**问题**: 钱包支付时余额不足，前端看到的不是直接的 `WALLET_BALANCE_NOT_ENOUGH`（1_007_007_001），而是 `PAY_ORDER_SUBMIT_CHANNEL_ERROR`（1_007_002_004，"发起支付报错，错误码：{}，错误提示：{}"）。链路是：`WalletPayClient.doUnifiedOrder` catch 所有异常（`ServiceException` 时取其 code/msg），返回 `PayOrderRespDTO.closedOf(errorCode, errorMsg, ...)`；`PayOrderServiceImpl.submitOrder` 检查 `unifiedOrderResp.getChannelErrorCode()` 非空后抛出包装异常。

**原因**: `AbstractPayClient.unifiedOrder` 的模板方法约定"渠道内异常不抛出、通过 RespDTO 的 channelErrorCode/channelErrorMsg 回传"，统一了各渠道的错误出口。

**解决**: 做前端提示或监控告警时，要解析 `PAY_ORDER_SUBMIT_CHANNEL_ERROR` 的占位符内容判断真实原因；新增渠道实现时遵循同一约定（业务异常翻译进 RespDTO，系统异常由模板方法包装为 `PayClientException`）。另注意该错误码带 `{}` 占位符，抛出时必须用 `exception(PAY_ORDER_SUBMIT_CHANNEL_ERROR, code, msg)` 传参。

### 6.2 支付通知最多重试 9 次，之后置 FAILURE 需人工补偿

**问题**: `PayNotifyTaskDO.NOTIFY_FREQUENCY` 定义了 8 个间隔（15、15、30、180、1800、1800、1800、3600 秒），`maxNotifyTimes = NOTIFY_FREQUENCY.length + 1` 即最多 9 次。`PayNotifyServiceImpl.processNotifyResult` 中通知次数达到上限后任务置为 `FAILURE`，`selectListByNotify()` 只扫描 `WAITING`/`REQUEST_SUCCESS`/`REQUEST_FAILURE` 三种状态，FAILURE 任务不会再被投递，业务方将永远收不到这笔支付/退款通知。

**原因**: 重试梯度最终拉长到 1 小时，总计约 2.5 小时；设计上认为超过该窗口的失败需要人工介入，避免无限重试。

**解决**: 运营上要监控 `pay_notify_task` 中 `status = FAILURE` 的记录并及时手工补偿（可通过管理后台"回调通知"菜单 `getNotifyTaskDetail` 查看每次通知的响应日志定位原因）。业务方回调接口务必保证幂等（以 `merchantOrderId` 为键），因为同一任务可能被并发投递两次——`executeNotify` 虽有 `PayNotifyLockRedisDAO` 分布式锁 + `notifyTimes` 比对兜底，但极端情况下仍可能重复通知。
