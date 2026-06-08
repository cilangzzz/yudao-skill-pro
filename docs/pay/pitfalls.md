# Pay 模块常见陷阱与最佳实践

> 开发和维护支付模块时需要注意的关键问题。

## 1. 金额精度问题

**陷阱**：使用 `Double` 或 `Float` 类型存储金额，导致浮点精度丢失。

```java
// 错误：浮点精度问题
double price = 0.1 + 0.2;  // 0.30000000000000004

// 正确：使用 Integer，单位为分
Integer price = 30;  // 30分 = 0.30元
```

**最佳实践**：
- 所有金额字段统一使用 `Integer` 类型，单位为分
- 外部接口如果接收元，转换时使用 `BigDecimal`：`new BigDecimal("0.30").multiply(new BigDecimal("100")).intValue()`
- 数据库字段也统一为 `Integer`/`BIGINT`

## 2. 并发安全问题

**陷阱**：订单状态变更和余额扣减在并发场景下可能出现问题。

```java
// 错误：先查后改，存在并发竞争
PayOrderDO order = orderMapper.selectById(id);
if (order.getStatus() == WAITING) {
    order.setStatus(SUCCESS);
    orderMapper.updateById(order);  // 并发时可能覆盖其他修改
}

// 正确：使用乐观锁
orderMapper.updateByIdAndStatus(id, WAITING,
    new PayOrderDO().setStatus(SUCCESS).setSuccessTime(LocalDateTime.now()));
```

**最佳实践**：
- 订单状态变更使用 `updateByIdAndStatus` 方法（WHERE 条件包含当前状态）
- 钱包余额扣减使用 CAS 方式（UPDATE SET balance = balance - amount WHERE balance >= amount）
- 返回影响行数为 0 时表示更新失败，需要重试或报错

## 3. 支付回调验签

**陷阱**：未验签或验签不严格，导致伪造回调攻击。

```java
// 错误：直接信任回调数据
public String handleNotify(String data) {
    // 直接解析 data 更新订单状态 -- 危险！
}

// 正确：先验签再处理
public String handleNotify(PayNotifyDataDTO notifyData) {
    PayClient client = channelService.getPayClient(channelId);
    // 验签失败会抛出异常
    PayOrderNotifyRespDTO resp = client.parseOrderNotify(notifyData);
    // 验签通过后才更新订单
}
```

**最佳实践**：
- 所有回调处理的第一步必须验签
- 使用各渠道 SDK 提供的验签方法
- 验签失败返回错误响应，不处理业务逻辑

## 4. 回调重复处理

**陷阱**：渠道可能重复发送回调（网络超时重试），导致重复处理。

```java
// 错误：直接更新状态，不判断当前状态
order.setStatus(PayOrderStatusEnum.SUCCESS);
orderMapper.updateById(order);  // 重复回调时会重复处理

// 正确：使用乐观锁，仅在目标状态时才更新
int updated = orderMapper.updateByIdAndStatus(orderId,
    PayOrderStatusEnum.WAITING.getStatus(),
    new PayOrderDO().setStatus(PayOrderStatusEnum.SUCCESS.getStatus()));
if (updated == 0) {
    log.info("订单已处理，忽略重复回调, orderId={}", orderId);
}
```

**最佳实践**：
- 回调处理使用乐观锁，仅在预期状态时才更新
- 更新成功（影响行数 > 0）才执行后续业务逻辑
- 更新失败（影响行数 = 0）说明已处理过，直接返回成功

## 5. 退款金额校验

**陷阱**：未正确校验累计退款金额，导致超额退款。

```java
// 错误：只校验本次退款金额
if (refundPrice <= order.getPrice()) {
    // 允许退款 -- 但没考虑已退款金额！
}

// 正确：校验累计退款金额
Integer totalRefunded = order.getRefundPrice() + refundPrice;
if (totalRefunded > order.getPrice()) {
    throw exception(REFUND_PRICE_EXCEED, order.getPrice() - order.getRefundPrice());
}
```

**最佳实践**：
- 退款前查询订单的 `refund_price`（已退款金额）
- 校验：`已退款金额 + 本次退款金额 <= 支付金额`
- 使用事务保证退款单创建和订单退款金额更新的原子性

## 6. 过期订单处理

**陷阱**：未设置过期时间或未处理过期订单，导致用户支付后无法完成。

```java
// 问题：订单长期处于 WAITING 状态
// 用户扫码后未支付，订单一直占着资源
```

**最佳实践**：
- 创建订单时设置 `expire_time`（如 30 分钟后过期）
- `PayOrderExpireJob` 定时任务扫描过期订单，调用 `PayClient.closeOrder()` 关闭
- 用户提交支付时校验订单是否已过期：`1_007_002_003`（支付订单已经过期）

## 7. 回调地址配置

**陷阱**：回调地址配置错误或不可达，导致支付成功但状态未更新。

**最佳实践**：
- `PayApp.order_notify_url` 和 `refund_notify_url` 必须配置为公网可访问的地址
- 回调地址使用 HTTPS
- 配合 `PayOrderSyncJob` 作为兜底，定时主动查询渠道确认订单状态
- 回调地址变更后及时更新配置

## 8. 客户端配置热刷新

**陷阱**：修改渠道配置后未刷新客户端，导致使用旧配置。

```java
// 修改了 pay_channel 的 config，但 PayClientFactory 缓存了旧实例
PayClient client = payClientFactory.getPayClient(channelId);  // 仍是旧配置
```

**最佳实践**：
- 修改渠道配置后调用 `PayClientFactory.refresh(channelId)`
- `refresh` 方法清除缓存的客户端实例
- 下次 `getPayClient` 时会使用新配置重新创建客户端

## 9. 支付客户端异常处理

**陷阱**：直接将渠道 SDK 异常抛给调用方，导致错误信息不友好。

```java
// 错误：直接抛出 SDK 异常
public PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
    return alipayClient.execute(request);  // SDK 异常直接抛出
}

// 正确：统一异常处理（AbstractPayClient 已处理）
public final PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
    ValidationUtils.validate(reqDTO);
    try {
        return doUnifiedOrder(reqDTO);
    } catch (Throwable ex) {
        throw buildPayException(ex);  // 转换为统一的支付异常
    }
}
```

**最佳实践**：
- 继承 `AbstractPayClient`，其模板方法已包含统一异常处理
- 子类只需关注业务逻辑，异常由基类统一捕获和转换

## 10. 多租户隔离

**陷阱**：`PayApp` 和 `PayChannel` 支持多租户，但查询时未过滤租户。

**最佳实践**：
- 继承 `TenantBaseDO` 的表自动带租户过滤
- 跨租户操作需要特别注意权限控制
- 其他表通过 `app_id` 间接关联租户

## 11. 测试环境模拟支付

**陷阱**：测试环境对接真实支付渠道，产生真实交易。

**最佳实践**：
- 测试环境使用 `mock` 渠道编码，对应 `MockPayClient`
- `MockPayClient` 模拟支付成功/失败，不产生真实交易
- 生产环境禁用 `mock` 渠道

## 12. 日志与排查

**陷阱**：支付流程关键节点缺少日志，出问题后难以排查。

**最佳实践**：
- 订单创建、提交、回调、状态变更等关键节点记录日志
- `PayOrderExtension.channel_notify_data` 保存回调原始数据
- 日志中包含 `orderId`, `channelOrderNo`, `merchantOrderId` 等关键标识
- 错误日志记录完整的异常堆栈

## 错误码速查

| 错误码 | 说明 | 常见原因 |
|--------|------|----------|
| `1_007_000_000` | App 不存在 | appKey 配置错误或应用未创建 |
| `1_007_001_000` | 支付渠道配置不存在 | 渠道未配置或已被删除 |
| `1_007_002_000` | 支付订单不存在 | 订单 ID 错误或已被清理 |
| `1_007_002_003` | 支付订单已过期 | 用户在订单过期后才支付 |
| `1_007_006_000` | 退款金额超过可退款金额 | 累计退款金额校验失败 |
