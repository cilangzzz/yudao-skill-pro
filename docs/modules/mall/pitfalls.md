# 注意事项与已知坑点

> 使用 mall 模块时的常见问题、易踩坑点和最佳实践。mall 为多子模块布局（product / promotion / trade / statistics / trade-api），下文以 `子模块名.类名` 标注代码位置，包根均为 `cn.iocoder.yudao.module.{子模块}`。

## 1. 多租户相关

### 1.1 mall 表未启用租户隔离，但定时任务必须加 @TenantJob

**问题**: 新增 mall 的表或 Job 时，容易套用 system/member 模块的写法给 DO 继承 `TenantBaseDO`，或者新写 Job 时漏加 `@TenantJob`，导致任务执行报错或行为异常。

**原因**: mall 五个子模块全部 49 个 DO 均继承 `BaseDO`（无 `tenantId` 字段），商品、订单、优惠券等表不参与租户隔离。但 Job 的 DB 查询仍需要租户上下文（框架的 `TenantContextHolder` 缺失时会拦截报错），现有 8 个 Job 全部通过 `@TenantJob` 逐租户执行：trade 的 `TradeOrderAutoCancelJob`、`TradeOrderAutoReceiveJob`、`TradeOrderAutoCommentJob`、`BrokerageRecordUnfreezeJob`，promotion 的 `CouponExpireJob`、`CombinationRecordExpireJob`，statistics 的 `TradeStatisticsJob`、`ProductStatisticsJob`。

**解决**: mall 表的 DO 一律继承 `BaseDO`；新增 Job 必须加 `@TenantJob`，例如：

```java
@Component
public class TradeOrderAutoCancelJob implements JobHandler {

    @Resource
    private TradeOrderUpdateService tradeOrderUpdateService;

    @Override
    @TenantJob
    public String execute(String param) {
        int count = tradeOrderUpdateService.cancelOrderBySystem();
        return StrUtil.format("取消订单 {} 个", count);
    }
}
```

## 2. 缓存相关

### 2.1 物流轨迹缓存的 @Cacheable 依赖 getSelf() 生效，且无主动失效

**问题**: 自己写代码直接 `this.getExpressTrackList(...)` 调用时缓存完全不生效，每次都真实调用物流 API；同时缓存里查到的是旧轨迹，发新包裹后要等缓存过期才能看到最新结果。

**原因**: trade 模块唯一的 `@Cacheable` 在 `TradeOrderQueryServiceImpl.getExpressTrackList`（cacheNames 为 `RedisKeyConstants.EXPRESS_TRACK`，key 为 `code-logisticsNo-receiverMobile`）。同类内部调用不经过 Spring 代理，注解失效，所以 `getExpressTrackList(TradeOrderDO)` 内部通过 `getSelf()`（`SpringUtil.getBean(getClass())`）调用了它。此外该缓存没有配套的 `@CacheEvict`（整个 mall 无一处 `@CacheEvict`），cacheName 也没用框架支持的 `express_track#ttl` 后缀格式（见 `TimeoutRedisCacheManager`），TTL 完全依赖 `yudao-server` application.yaml 里的全局 `spring.data.redis.time-to-live`（当前 1h）。

**解决**: 调用该方法一律走 Service 接口（或类内 `getSelf()`）；修改全局 TTL 时注意它会连带影响该缓存；如果需要精细控制，把 cacheName 改成 `"express_track#30m"` 的格式即可单独设置过期时间。

## 3. 事务与 AOP 相关

### 3.1 同类内部调用 @Transactional / @Async 注解方法会失效，必须走 getSelf()

**问题**: 在 Service 内部直接 `this.xxxMethod()` 调用带注解的方法，事务、异步、操作日志注解全部静默失效，且编译运行都不报错，只能通过数据异常（如部分落库、日志缺失）发现。

**原因**: Spring AOP 基于代理实现，内部调用绕过了代理对象。mall 中此类场景很多：`TradeOrderUpdateServiceImpl` 的 `receiveOrderBySystem(TradeOrderDO)`、`cancelOrderBySystem(TradeOrderDO)`、`pickUpOrder`（带 `@Transactional` + `@TradeOrderLog`）、`sendDeliveryOrderMessage`（带 `@Async`）、`updateOrderPaid`（被 `syncOrderPayStatusQuietly` 调用）；`CouponServiceImpl.invalidateCoupon`（`@Transactional(REQUIRES_NEW)`）；`CombinationRecordServiceImpl.handleExpireRecord`、`handleVirtualGroupRecord`；`BrokerageRecordServiceImpl.unfreezeRecord`；`KeFuMessageServiceImpl.sendAsyncMessageToMember/sendAsyncMessageToAdmin`；`TradeOrderQueryServiceImpl.getExpressTrackList`（`@Cacheable`）。这些类的源码里都统一用 `getSelf()` 解决：

**解决**: 类内复制的标准写法（已存在于上述 6 个类中，新增同类场景照抄即可）：

```java
/**
 * 获得自身的代理对象，解决 AOP 生效问题
 */
private TradeOrderUpdateServiceImpl getSelf() {
    return SpringUtil.getBean(getClass());
}
```

### 3.2 管理员批量赠券/收券是"部分成功"语义，失败只打日志

**问题**: 后台给用户补发优惠券、订单售后收回赠送优惠券时，部分券发放/收回失败，接口却不报错；支付成功后赠送的优惠券发放失败，也不会重试，最终只能靠日志发现"需要手工补偿"。

**原因**: promotion 的 `CouponServiceImpl.takeCouponsByAdmin` 对每种券循环调用 `getSelf().takeCoupon(...)`，`invalidateCouponsByAdmin` 循环调用 `getSelf().invalidateCoupon(...)`（单张券 `@Transactional(REQUIRES_NEW)`，注释写明"每次调用开启一个新的事务，避免在一个大的事务里面"），单张失败仅 `log.error` 后继续。trade 的 `TradeCouponOrderHandler.afterPayOrder` 在支付回调里发放赠送优惠券，失败同样是 `log.error("[afterPayOrder][order({}) 赠送优惠券({})失败，需要手工补偿]"...)`，没有任何补偿任务。

**解决**: 排查用户"券没到账"问题时，先搜这些 error 日志；做二次开发时不要把这几个方法包进一个大事务里"顺便"改成全量回滚——单张券 REQUIRES_NEW 是有意为之（一张失败不影响其它券）；如需强一致，需自行基于日志表增加补偿 Job。

### 3.3 订单日志切面的 ThreadLocal 在异常路径不清理，线程池复用有串单风险

**问题**: 带 `@TradeOrderLog` 的方法在成功路径会正确写订单操作日志；但如果方法在 `TradeOrderLogUtils.setOrderInfo(...)` 之后抛异常（例如 `cancelOrder0` 里 `tradeOrderHandlers.afterCancelOrder` 抛出），该日志写入被跳过，且 ThreadLocal 中的 orderId/状态残留在线程上。

**原因**: `TradeOrderLogAspect` 的 5 个上下文（USER_ID/USER_TYPE/ORDER_ID/BEFORE_STATUS/AFTER_STATUS/EXTS）是普通 `ThreadLocal`，切面用的是 `@AfterReturning` 而非 `@After`/`@Around`——方法抛异常时增强逻辑不执行，`finally { clear() }` 也就不会运行。Tomcat/Job 线程复用后，下一个走到 `@TradeOrderLog` 方法但没有调用 `setOrderInfo` 的路径，会把残留的 orderId 当作本次日志的订单号写入。

**解决**: 扩展订单操作时遵循现有约定：`@TradeOrderLog` 方法内部在业务更新成功后再调 `TradeOrderLogUtils.setOrderInfo(...)`（参考 `updateOrderPaid` 第 5 步）；如果改造切面，把 `@AfterReturning` 换成 `@After` 并在 `clear()` 中兜底清理，可彻底消除残留。

## 4. 订单与售后状态机相关

### 4.1 状态流转必须走 updateByIdAndStatus 的 CAS 更新，不要用 updateById 直改状态

**问题**: 二次开发时若直接 `tradeOrderMapper.updateById(...)` 改订单状态，在支付回调、自动取消等并发场景下会出现状态被覆盖、重复扣库存、重复退款等问题；支付回调重复通知也可能被误处理。

**原因**: `TradeOrderUpdateServiceImpl` 的所有状态迁移都带前置状态条件：`updateOrderPaid` 先比对 `payOrderId` 实现回调幂等（已支付且支付单号相同直接 `return`，不同则抛 `ORDER_UPDATE_PAID_FAIL_PAY_ORDER_ID_ERROR`），再用 `tradeOrderMapper.updateByIdAndStatus(id, order.getStatus(), ...)` 做乐观更新，`updateCount == 0` 抛异常；`deliveryOrder`、`receiveOrder0`、`cancelOrder0` 同款。售后单 `AfterSaleServiceImpl.updateAfterSaleStatus`、优惠券 `CouponServiceImpl.useCoupon` 也是同一模式。例外要注意：`updateOrderItemWhenAfterSaleSuccess` 里对订单的 `refundStatus/refundPrice` 用的是普通 `updateById`，且 `isAllOrderItemAfterSaleSuccess` 是先查后判，本身非原子（见 4.3）。

**解决**: 新增状态迁移一律套用现有模板：

```java
int updateCount = tradeOrderMapper.updateByIdAndStatus(id, oldStatus,
        new TradeOrderDO().setStatus(newStatus)...);
if (updateCount == 0) {
    throw exception(ORDER_UPDATE_PAID_STATUS_NOT_UNPAID); // CAS 失败 = 并发修改，抛业务异常
}
```

### 4.2 取消订单与支付回调存在竞态窗口，靠"先查支付单"缓解

**问题**: 用户在超时边缘取消订单时，可能支付回调刚好到达，出现"订单已取消但钱已扣"的情况。

**原因**: `cancelOrderByMember` / `cancelOrderBySystem(order)` 在执行 `cancelOrder0` 前会额外调 `payOrderApi.getOrder(order.getPayOrderId())` 检查支付单是否已成功（日志明确写了"支付单已支付（支付回调延迟），不支持取消"），但这是先查后改，查完到 CAS 更新之间回调仍可能插入。`cancelOrderBySystem` 遇到该情况直接 `return` 跳过（留给下一轮 Job 再核对），`cancelOrderByMember` 则抛 `ORDER_CANCEL_FAIL_STATUS_NOT_UNPAID` 让用户走售后。

**解决**: 不要"优化"掉这两处对 `payOrderApi.getOrder` 的前置检查；出现此类边界数据时，业务侧按已支付订单走 `AfterSaleService` 售后退款流程，而不是强行把取消订单改回来。

### 4.3 售后"整单退款完成"的判断非原子，整单取消依赖售后回调串联

**问题**: 多订单项同时售后时，极端并发下 `refundStatus`（PART/ALL）判断可能不准；整单退款后的取消动作发生在退款回调链路里，链路中任何一环异常都会导致订单残留"已退款但未取消"。

**原因**: `TradeOrderUpdateServiceImpl.updateOrderItemWhenAfterSaleSuccess` 的流程是：CAS 更新订单项售后状态 → 执行 handler 退还库存/积分 → 累加 `order.refundPrice` 并用 `updateById` 更新 `refundStatus`（先 `isAllOrderItemAfterSaleSuccess` 全查判断）→ `getSelf().cancelOrderByAfterSale(order, orderRefundPrice)`（仅当 `refundPrice >= payPrice` 才取消订单并 `updateById` 改状态，无 CAS）。售后单状态由 `AfterSaleController /update-refunded`（`@PermitAll`，由 pay-module 的 `PayNotifyJob` 回调）驱动，回调按 `merchantRefundId` 是否以 `order-` 开头分流：整单退款（拼团失败取消，`cancelPaidOrder` 里用 `"order-" + orderId`）走 `updatePaidOrderRefunded`，售后退款直接用售后单号走 `updateAfterSaleRefunded`。

**解决**: 理解该链路后再改：订单项售后状态用 CAS（`tradeOrderItemMapper.updateAfterSaleStatus` 旧状态不匹配抛 `ORDER_ITEM_UPDATE_AFTER_SALE_STATUS_FAIL`）；不要把 `cancelOrderByAfterSale` 改成无前置判断的调用；对账时以 `trade_after_sale` 状态 + `trade_order_item.after_sale_status` 双侧核对。

### 4.4 优惠券领取限额是"先查后写"，并发可超领

**问题**: 限时限量优惠券在用户秒抢场景下，实际发放数量可能超过 `takeLimitCount`（每人限领）或 `totalCount`（总量）。

**原因**: `CouponServiceImpl.takeCoupon` 的流程是 `removeTakeLimitUser`（先 `couponMapper.selectListByTemplateIdAndUserId` 统计已领数）→ `validateCouponTemplateCanTake`（判断 `takeCount > totalCount` 即已领超过总量才报 `COUPON_TEMPLATE_NOT_ENOUGH`）→ `couponMapper.insertBatch` → `updateCouponTemplateTakeCount(+n)`。全程无锁、无唯一索引兜底，两个并发请求都能通过校验。代码注释里还保留了两个线上案例链接（`validateCouponTemplateCanTake` 中 `https://t.zsxq.com/mElGQ` 等）。

**解决**: 量小接受超领即可（项目现状）；要严格防超领需自行加锁（如 Redis 分布式锁按 templateId）或建 `(template_id, user_id)` 唯一索引配合捕获重复键异常。另外注意 `takeCoupon` 里 `userIds` 集合会被 `removeTakeLimitUser` 原地 `removeIf` 修改，外部复用集合时留意。

### 4.5 拼团成团人数判断非原子，依赖过期 Job 兜底

**问题**: 最后一个名额被两人并发参团时，可能出现 `userCount` 超过 `userSize`、双方都看到"拼团成功"的脏数据。

**原因**: `CombinationRecordServiceImpl.createCombinationRecord` 中"校验拼团是否已满"（`record.getUserCount() == record.getUserSize()` 抛 `COMBINATION_RECORD_USER_FULL`）与 `updateCombinationRecordWhenCreate` 的 `records.size() >= activity.getUserSize()` 判断都是先查后写，`updateBatch` 无行锁。成团成功后的订阅消息通过 `getSelf().sendCombinationResultMessage(...)`（`@Async`）发送。兜底逻辑是 `CombinationRecordExpireJob` → `expireCombinationRecord()`：过期团按 `activity.virtualGroup` 分流到 `handleExpireRecord`（整团置 FAILED 并调 `tradeOrderApi.cancelPaidOrder` 取消已支付订单）或 `handleVirtualGroupRecord`（插入虚拟团员补齐并置 SUCCESS）。

**解决**: 出现脏数据时以 Job 的处理结果为准（Job 会按团长记录统一重置整团状态）；如果做秒杀级并发优化，需要在 `createCombinationRecord` 上加针对 headId 的分布式锁，而不是改判断语句。

### 4.6 订单发货状态白名单与错误码文案不一致，且已发货订单可再次发货

**问题**: 按错误码 `1_011_000_017`「交易订单发货失败，订单不是【待发货】状态」的字面理解写业务判断，会把已发货订单当成不可再发货；实际行为恰好相反——【已发货】订单允许再次发货以修改物流公司/单号，而未付款/已取消/已完成等状态会抛该错误。

**原因**: `TradeOrderUpdateServiceImpl.validateOrderDeliverable` 现在先做状态白名单校验：`TradeOrderStatusEnum.isUndelivered(status) || isDelivered(status)` 才放行，否则抛 `ORDER_DELIVERY_FAIL_STATUS_NOT_UNDELIVERED`（1_011_000_017）；随后才校验 `refundStatus == NONE`。基线版本只校验 refundStatus、不校验订单状态（未付款/已取消订单理论上也能被发货），本次按官方 issue https://github.com/YunaiV/ruoyi-vue-pro/issues/1310 收紧。CAS 更新条件也改为读取时的 `order.getStatus()`，避免并发收货/取消被覆盖。

**解决**: 扩展发货相关逻辑时以 `isUndelivered/isDelivered` 白名单为准，不要按错误码文案判断；需要"仅首次发货"的附加值逻辑时，自行判断 `order.getStatus()` 是否已为 DELIVERED，不能依赖该错误码。

### 4.7 重复发货会重复触发站内信、订阅消息与 afterDeliveryOrder

**问题**: 对已发货订单再次发货（修改物流单号）时，除了刷新物流信息，站内信、微信小程序订阅消息和 `TradeOrderHandler.afterDeliveryOrder` 都会再执行一遍，用户可能收到重复通知，后置 Handler 也可能重复处理。

**原因**: `deliveryOrder` 在 CAS 更新成功后无条件执行 4.1 站内信、4.2 订阅消息与第 5 步 `tradeOrderHandlers.forEach(handler -> handler.afterDeliveryOrder(order))`，没有区分"首次发货"与"再次发货"。当前唯一的发货后置 Handler 是 `TradeStatusSyncToWxaOrderHandler`（同步物流到小程序），重复执行影响较小。

**解决**: 新增发货后置 Handler 时必须自行保证幂等（例如按订单号 + 物流单号去重，或先判断订单原状态）；需要区分场景时可对比 `order.getStatus()` 是否已为 DELIVERED。

### 4.8 支付/退款/转账回调必须双向核对回调单号，仅校验金额与商户单号不足以防串单

**问题**: 支付回调、售后退款回调、佣金提现转账回调如果只校验"商户单号 + 金额"，其它支付应用中恰好相同商户单号、相同金额的单据可能被用于串单，把别人的支付/退款/转账结果错误地记到本单上。

**原因**: 本次在三条回调链路统一追加「业务单绑定单号 == 回调单号」校验：`TradeOrderUpdateServiceImpl.updateOrderPaid` 校验 `order.payOrderId == payOrderId`（不一致抛 1_011_000_014）；`AfterSaleServiceImpl.updateAfterSaleRefunded` 校验 `afterSale.payRefundId == payRefundId`（不一致抛 1_011_000_114，位于校验支付退款单之前）；`BrokerageWithdrawServiceImpl.updateBrokerageWithdrawTransferred` 校验 `withdraw.payTransferId == payTransferId`（不一致抛 1_011_008_005，位于「提现单已结束」判断之后、「校验转账单合法性」之前）。原有的幂等分支（已支付且支付单号相同直接 return）保持不变。

**解决**: 二次开发新增任何支付/退款/转账回调入口时，必须照做"业务单绑定单号 == 回调单号"校验，不能只依赖金额与商户单号；排查回调异常时优先看这三处 `log.error` 中的「绑定单号与回调单号不匹配」。

### 4.9 DIY 模板删除会级联删除其下全部装修页面

**问题**: 删除装修模板后，模板下的装修页面（含 App 首页/我的等）会一起被删除，且数据不可恢复；如果有其它业务仍按页面 id 引用这些页面，会出现悬空引用。

**原因**: `DiyTemplateServiceImpl.deleteDiyTemplate` 新增 `@Transactional(rollbackFor = Exception.class)`，删除模板记录后按 `templateId` 查出全部 `promotion_diy_page` 并逐个 `deleteDiyPage`。基线版本只删模板本身，页面会残留为孤儿数据。

**解决**: 删除前确认模板未处于使用中（接口本身会拦截），并评估页面是否被其它业务引用；不要把"删模板"当作轻量操作。

### 4.10 优惠券模板已被逻辑删除时，回收优惠券不回退 takeCount

**问题**: 回收某张优惠券后，模板的 `takeCount` 没有减 1，排查"领取数与实际发放数不一致"时容易误判为 bug。

**原因**: `CouponServiceImpl.deleteCoupon` 现在先判断 `getCouponTemplate(coupon.getTemplateId()) != null`，模板已被逻辑删除时跳过 `updateCouponTemplateTakeCount(id, -1)`。因为 `updateTakeCount` 对逻辑删除的模板匹配 0 行，基线版本会误抛 `COUPON_TEMPLATE_NOT_ENOUGH`（1_013_004_002）导致删券失败。

**解决**: 模板已删场景下的计数差值属于预期；回收逻辑不要恢复成无条件回退。

## 5. 库存相关

### 5.1 所有库存扣减都是数据库条件更新（CAS），没有 Redis 预扣

**问题**: 秒杀/积分兑换等高并发场景下，库存热点行会成为数据库瓶颈；同时若自写扣库存逻辑漏掉 `stock >= ?` 条件，会出现超卖。

**原因**: mall 的库存模型统一是 `UPDATE ... SET stock = stock - ? WHERE id = ? AND stock >= ?`：product 的 `ProductSkuMapper.updateStockDecr`（同时 `sales_count + 1`，返回 0 时 `ProductSkuServiceImpl.updateSkuStock` 抛 `SKU_STOCK_NOT_ENOUGH`）；promotion 的 `SeckillActivityMapper/SeckillProductMapper/PointActivityMapper/PointProductMapper` 的 `updateStockDecr` 同款（`SeckillActivityServiceImpl.updateSeckillStockDecr` 先读后判 `count > stock` 只是快速失败，真正兜底是 CAS）。下单扣库存发生在 `TradeProductSkuOrderHandler.beforeOrderCreate`，与订单创建同一事务，取消/售后由 `afterCancelOrder`、`afterCancelOrderItem` 回补（已售后的订单项会在回补时用 `filterOrderItemListByNoneAfterSale` 去重，避免双重回补）。

**解决**: 扩展扣库存场景时复用这套 Mapper 方法，不要手写 `updateById(sku.setStock(新值))`；接受秒杀热点行打满数据库的现状，或自行引入 Redis 预扣 + 异步落库改造（框架未提供）。

## 6. 价格计算相关

### 6.1 积分抵扣禁止 0 元购（直接抛异常），砍价优惠金额为负未处理

**问题**: 用户积分充足时提交订单报"支付金额错误"（`PRICE_CALCULATE_PAY_PRICE_ILLEGAL`），而不是自动只抵扣到 0.01 元；砍价活动若后台把 `bargainPrice` 配得高于商品现价，订单支付价格反而会被抬高。

**原因**: `TradePointUsePriceCalculator.calculatePointPrice` 中 `if (result.getPrice().getPayPrice() <= pointPrice) throw exception(PRICE_CALCULATE_PAY_PRICE_ILLEGAL)`，源码里注释 `// TODO @疯狂：这里应该是，抵扣到只剩下 0.01；`，被注释掉的"允许 0 元购"反推逻辑未启用。`TradeBargainActivityPriceCalculator` 第 43 行 `discountPrice = payPrice - bargainPrice * count` 后同样留着 `// TODO 芋艿：极端情况，优惠金额为负数，需要处理`。价格计算整体是责任链：`TradePriceService.calculateOrderPrice` 按 `@Order` 顺序执行 10 个 `TradePriceCalculator` 实现，新增优惠类型必须复用 `TradePriceCalculatorHelper.dividePrice/recountPayPrice/recountAllPrice`，否则分摊金额与订单总额对不上。

**解决**: 运营侧配置 `pointTradeDeductMaxPrice`（单笔最多抵扣积分）避免积分大额抵扣触发异常；砍价活动价格变更前核对当前 SKU 价格。二次开发若要支持 0.01 元购，在 `calculatePointPrice` 里按支付金额反推 `usePoint`（被注释的代码即参考实现），不要只把 `<=` 改成 `<`。

## 7. 商品与消息通知相关

### 7.1 编辑 SPU 规格会删除重建 SKU，skuId 变化导致购物车旧引用失效

**问题**: 商家修改了商品规格值（如"红色"改"酒红色"）后，用户购物车里旧 SKU 下单报错或计算异常。

**原因**: `ProductSkuServiceImpl.updateSkuList` 按 `ProductSkuConvert.buildPropertyKey`（属性值 id 集合）匹配现有 SKU：key 能匹配上的走 `updateById` 保留原 id；匹配不上的全部 `insertBatch` 新建，剩余旧 SKU `deleteByIds` 物理删除。规格值一变 key 就变，旧 skuId 作废。下单链路 `TradeOrderConvert.convert(userId, settlementReqVO, cartList)` 直接拿购物车的 `skuId` 参与价格计算，不会提示"SKU 已失效"。另外 `updateSpu` 里 `BeanUtils.toBean(...).setStatus(spu.getStatus())` 会强制回写数据库中的原状态——改商品接口改不了上下架状态，必须走 `updateSpuStatus`（且其内部 TODO 标明"参与活动中的商品，不允许下架"尚未实现，删除前必须先入回收站，见 `deleteSpu` 的 `SPU_NOT_RECYCLE` 校验）。

**解决**: 变更规格属于高危操作，前端应对已加购商品做失效提示；如只需改价格/库存，直接编辑 SKU 保持属性不变即可保留 skuId。状态变更一律走 `updateSpuStatus` 接口。

### 7.2 发货站内信被 `if (true) return;` 代码写死关闭

**问题**: 订单发货后收不到站内信通知，只有微信小程序订阅消息（`@Async sendDeliveryOrderMessage`）会发送，配置站内信模板也没有效果。

**原因**: `TradeMessageServiceImpl.sendMessageWhenDeliveryOrder` 方法第一行就是无条件 `if (true) { return; }`，后面构造 `NotifyMessageSendApi` 发送的逻辑永远不会执行，源码处留有 `// TODO 芋艿：看下模版`。`TradeOrderUpdateServiceImpl.deliveryOrder` 第 4.1 步调用的正是这个方法。

**解决**: 需要站内信通知时，删除该方法开头的 `if (true) return;` 并补齐模板配置（`MessageTemplateConstants.SMS_ORDER_DELIVERY`）；不要误以为是配置问题反复排查通知模板。

## 8. Mapper 与 SQL 可移植性约定

### 8.1 取前 N 条/单条不要再用 `.last("LIMIT n")`

**问题**: 用 `wrapper.last("LIMIT " + count)` 或 `selectOne(... .last("LIMIT 1"))` 取前 N 条/单条，在非 MySQL 数据库（Oracle/SQL Server/PostgreSQL）上会因方言不支持而报错；在 SQL Server 上还要求分页语句必须带 ORDER BY。

**原因**: 框架已在 `BaseMapperX` 提供 `selectListLimitN(Wrapper, int)` 与 `selectFirstOne(Wrapper)`：前者走 MyBatis-Plus 分页插件，按当前数据库生成 LIMIT / ROWNUM / OFFSET FETCH，且不执行 COUNT；后者等价于 `selectListLimitN(wrapper, 1)` 取第一条。本次 mall 已把 `BargainActivityMapper`、`BargainRecordMapper`、`CombinationRecordMapper`、`CouponTemplateMapper`、`KeFuMessageMapper` 等处的 `.last("LIMIT n")` 全部迁移，并为砍价相关查询补齐了确定性的 `ORDER BY id`。

**解决**: 新增/修改查询统一写成：

```java
// 前 N 条：wrapper 必须自带 orderBy（SQL Server 分页要求排序）
return selectListLimitN(new LambdaQueryWrapperX<XxxDO>()
        .eq(XxxDO::getStatus, status)
        .orderByAsc(XxxDO::getId), count);

// 单条
return selectFirstOne(new LambdaQueryWrapper<XxxDO>()
        .eq(XxxDO::getUserId, userId)
        .orderByDesc(XxxDO::getId));
```

`selectListLimitN` 对 limit 为负数会直接抛 `IllegalArgumentException`（防负数被分页插件视为不分页而查全表），limit=0 直接返回空列表。

### 8.2 统计 XML 的日期分组必须走 SqlDialectUtils，布尔/逻辑删除字面量不要硬编码

**问题**: 统计 Mapper XML 中直接写 `CAST(create_time AS DATE)`、`CONCAT(EXTRACT(...))`、`pay_status = TRUE`、`deleted = FALSE`，在部分数据库不可用。

**原因**: 日期分组已统一改为方言片段 `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@castDate('create_time')}` / `castDateText(...)` / `formatYearDashMonth(...)`，并用 `resultMap` 显式把 `statDate` 映射回响应字段 `date`（`MemberStatisticsMapper.xml`、`TradeOrderStatisticsMapper.xml`）；布尔字面量改为 `<bind name="trueValue" value="true"/>` + `#{trueValue}` 绑定（`ProductStatisticsMapper.xml`、`TradeOrderStatisticsMapper.xml`）；注解 SQL 中的 `deleted = FALSE` 统一改为 `deleted = 0`（`BrokerageRecordMapper`、`BrokerageUserMapper`）。以上改动不改变任何接口的入参/出参（`date` / `orderPayCount` / `orderPayPrice` / `count` 字段保持不变）。

**解决**: 新增统计 SQL 时不要直接写 `CAST`/`EXTRACT`/`TRUE`/`FALSE`；日期分组用 `SqlDialectUtils` 对应方法并配 `resultMap`，布尔值用 `#{trueValue}`，逻辑删除条件写 `deleted = 0`。`formatYearDashMonth` 等方法的列名参数只接受代码中固定的安全列名（内部有 `checkColumn` 校验）。

## 9. 子模块依赖与参数校验约定

### 9.1 product 子模块新增对 trade-api 的依赖，SPU 配送方式在参数校验阶段拦截

**问题**: 给 `ProductSpuSaveReqVO.deliveryTypes` 传非法配送方式（非 1/2）时，接口直接返回 HTTP 400「配送方式不正确」，不会落库；同时 product 的 `pom.xml` 多了一条对 `yudao-module-trade-api` 的依赖。

**原因**: 本次为 `deliveryTypes` 新增 `@InEnum(value = DeliveryTypeEnum.class, message = "配送方式不正确")`，`DeliveryTypeEnum` 位于 `yudao-module-trade-api`（取值：1 快递发货 / 2 用户自提），因此 product → trade-api 成为新的内部依赖方向。基线版本只有 `@NotEmpty`，非法值会被静默写入数据库。

**解决**: 跨子模块共享枚举优先放 `yudao-module-trade-api`（其中已含 18 个订单/售后/分销/配送/通知枚举，另含 ErrorCodeConstants 等 3 个常量类），但 trade-api 的定位是「纯 API 骨架包」，不要在 trade-api 中引入任何实现类依赖，以免重新形成循环依赖。新增需要枚举校验的字段时，直接复用 `@InEnum(XxxEnum.class)`，不要手写 if 判断。
