# 踩坑与最佳实践

> 模块路径：`yudao-module-mall`

---

## 1. 价格与金额

### 踩坑：浮点精度丢失

**问题**：使用 `Double` / `Float` 存储或计算金额，导致精度丢失（如 0.1 + 0.2 != 0.3）。

**正确做法**：所有金额使用 `Integer` 类型，单位为分。

```java
// 错误
double price = 9.99;

// 正确
int price = 999; // 单位：分
```

### 踩坑：金额计算顺序

**问题**：先除后乘导致精度丢失。

**正确做法**：先乘后除，保持中间结果为整数。

```java
// 错误：先除会丢失精度
int discount = totalPrice * discountPercent / 100;

// 正确：先乘后除
int discount = totalPrice * discountPercent / 100;
```

---

## 2. 库存管理

### 踩坑：超卖问题

**问题**：并发下单时多个线程同时读取库存为 1，都扣减成功导致超卖。

**解决方案**：

- **方案一：数据库乐观锁**

```sql
UPDATE product_sku SET stock = stock - #{count}
WHERE id = #{skuId} AND stock >= #{count}
```

- **方案二：Redis 原子扣减**

```java
Long result = redisTemplate.opsForValue().decrement(stockKey, count);
if (result < 0) {
    // 库存不足，回滚
    redisTemplate.opsForValue().increment(stockKey, count);
    throw new ServiceException(SKU_STOCK_NOT_ENOUGH);
}
```

### 踩坑：库存回滚

**问题**：订单取消/超时后库存未恢复，导致实际有库存但无法下单。

**正确做法**：

1. 订单取消时必须调用 `ProductSkuApi.updateSkuStock(skuId, -count)` 恢复库存
2. 优惠券也要同步退回 `CouponApi.returnCoupon(couponId)`
3. 使用定时任务兜底，扫描超时未支付订单自动取消并回滚库存

---

## 3. 订单状态机

### 踩坑：状态流转不严格

**问题**：未校验前置状态，导致状态跳变（如从"待付款"直接变为"已收货"）。

**正确做法**：状态变更前必须校验当前状态是否合法。

```java
// 错误：直接更新状态
tradeOrderMapper.updateStatus(orderId, newStatus);

// 正确：校验前置状态
TradeOrderDO order = tradeOrderMapper.selectById(orderId);
if (!TradeOrderStatusEnum.canTransit(order.getStatus(), newStatus)) {
    throw new ServiceException(ORDER_STATUS_TRANSIT_FAIL);
}
tradeOrderMapper.updateStatus(orderId, newStatus);
```

### 踩坑：并发状态变更

**问题**：两个请求同时变更同一订单状态，导致状态覆盖。

**正确做法**：使用 CAS（Compare And Swap）方式更新。

```sql
UPDATE trade_order SET status = #{newStatus}
WHERE id = #{orderId} AND status = #{oldStatus}
```

---

## 4. 优惠券使用

### 踩坑：优惠券重复使用

**问题**：并发请求导致同一张优惠券被多次使用。

**正确做法**：使用乐观锁 + 状态校验。

```sql
UPDATE promotion_coupon SET status = 2  -- 已使用
WHERE id = #{couponId} AND status = 1   -- 未使用
```

### 踩坑：订单取消后优惠券未退回

**问题**：用户取消订单或超时未支付，优惠券状态仍为"已使用"，用户无法再次使用。

**正确做法**：订单取消流程中必须退回优惠券。

---

## 5. 秒杀场景

### 踩坑：库存扣减时机

**问题**：在下单时才扣减库存，高并发下大量请求穿透到数据库。

**正确做法**：预扣库存。

```
1. 活动开始前：将库存加载到 Redis
2. 用户请求时：Redis 原子扣减库存（DECR）
3. Redis 扣减成功：进入下单流程
4. 下单失败/超时：Redis 回滚库存（INCR）
```

### 踩坑：恶意刷单

**问题**：同一用户秒杀多件超出限购数量。

**正确做法**：

1. Redis 记录用户已抢购数量
2. 判断 `已购数量 + 本次数量 <= 限购数量`
3. 使用 Lua 脚本保证原子性

---

## 6. 事务管理

### 踩坑：跨服务事务

**问题**：订单创建涉及扣库存（product 模块）、使用优惠券（promotion 模块）、创建订单（trade 模块），任一步失败但前面步骤已提交。

**正确做法**：

- 关键操作放在同一事务中（同模块内）
- 跨模块操作使用补偿机制：失败时调用回滚接口
- 使用消息队列最终一致性：先创建订单（本地事务），异步通知其他模块

### 踩坑：事务范围过大

**问题**：一个事务包含太多操作（查商品、算价格、扣库存、创建订单），导致长事务和锁竞争。

**正确做法**：

- 将查询操作移到事务外
- 事务只包含写操作（插入订单、扣减库存）
- 使用 `@Transactional(rollbackFor = Exception.class)` 显式指定回滚异常

---

## 7. 查询性能

### 踩坑：N+1 查询

**问题**：查询订单列表后逐个查询订单项，产生 N+1 查询。

**正确做法**：

```java
// 错误：逐个查询
List<TradeOrderDO> orders = tradeOrderMapper.selectList(queryWrapper);
for (TradeOrderDO order : orders) {
    List<TradeOrderItemDO> items = tradeOrderItemMapper.selectByOrderId(order.getId());
}

// 正确：批量查询
List<Long> orderIds = orders.stream().map(TradeOrderDO::getId).collect(Collectors.toList());
Map<Long, List<TradeOrderItemDO>> itemMap = tradeOrderItemMapper.selectByOrderIds(orderIds);
```

### 踩坑：分页查询未加索引

**问题**：按 `name` 模糊查询、`category_id`、`status` 等字段分页，数据量大时查询缓慢。

**正确做法**：为常用查询字段添加索引。

---

## 8. 对象转换

### 踩坑：手动 Bean 拷贝遗漏字段

**问题**：手动 `set/get` 转换 VO 和 DO，新增字段时遗漏。

**正确做法**：使用框架提供的 `BeanUtils.toBean()` 或 MapStruct。

```java
// 错误
ProductSpuRespVO vo = new ProductSpuRespVO();
vo.setId(spu.getId());
vo.setName(spu.getName());
// 遗漏了新增字段...

// 正确
ProductSpuRespVO vo = BeanUtils.toBean(spu, ProductSpuRespVO.class);
```

---

## 9. 异常处理

### 踩坑：吞掉异常

**问题**：catch 异常后只打日志不抛出，导致上层逻辑误以为操作成功。

**正确做法**：使用框架统一异常处理。

```java
// 错误
try {
    productSkuService.deductStock(skuId, count);
} catch (Exception e) {
    log.error("扣减库存失败", e);
}

// 正确：让异常抛出，由全局异常处理器处理
productSkuService.deductStock(skuId, count);
```

### 踩坑：错误码不规范

**问题**：使用魔法数字或字符串作为错误码，难以维护和定位。

**正确做法**：在 `ErrorCodeConstants.java` 中统一定义错误码。

```java
// 错误
throw new ServiceException(1001, "商品不存在");

// 正确
ErrorCodeConstants.java:
  ErrorCode PRODUCT_SPU_NOT_EXISTS = new ErrorCode(1_008_005_000, "商品 SPU 不存在");

throw exception(PRODUCT_SPU_NOT_EXISTS);
```

---

## 10. 最佳实践速查表

| 场景 | 建议 |
|------|------|
| 金额存储 | Integer，单位为分 |
| 库存扣减 | 乐观锁 或 Redis 原子操作 |
| 订单状态变更 | CAS 更新 + 状态机校验 |
| 优惠券使用 | 乐观锁防重 + 订单取消退回 |
| 秒杀高并发 | Redis 预扣库存 + 限购校验 |
| 跨模块调用 | 通过 API 接口，不直接依赖实现类 |
| 事务管理 | `@Transactional(rollbackFor = Exception.class)` |
| 对象转换 | `BeanUtils.toBean()` 或 MapStruct |
| 异常处理 | `throw exception(ERROR_CODE, args)` |
| 分布式锁 | 秒杀、拼团等高并发场景使用 Redis 分布式锁 |
