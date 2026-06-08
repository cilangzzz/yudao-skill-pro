# 订单域 API 文档

> 模块路径：`yudao-module-mall/yudao-module-trade`

---

## 1. 订单管理（admin）

**Controller**: `TradeOrderController`
**路径前缀**: `/admin-api/trade/order`
**权限前缀**: `trade:order:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 订单分页查询 | `trade:order:query` |
| GET | `/get` | 获取订单详情 | `trade:order:query` |
| PUT | `/update-address` | 修改收货地址 | `trade:order:update` |
| PUT | `/delivery` | 订单发货 | `trade:order:update` |
| PUT | `/receive` | 确认收货 | `trade:order:update` |
| PUT | `/cancel` | 取消订单 | `trade:order:update` |
| PUT | `/remark` | 订单备注 | `trade:order:update` |

### 1.2 请求/响应 VO

**TradeOrderPageReqVO**（分页查询请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 订单流水号 |
| userId | Long | 否 | 用户编号 |
| status | Integer | 否 | 订单状态 |
| payStatus | Boolean | 否 | 是否已支付 |
| deliveryType | Integer | 否 | 配送方式 |
| createTime | LocalDateTime[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

**TradeOrderDeliveryReqVO**（发货请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 订单编号 |
| logisticsId | Long | 是 | 物流公司编号 |
| logisticsNo | String | 是 | 物流单号 |

### 1.3 订单状态机

```
[待付款] --支付--> [待发货] --发货--> [待收货] --收货--> [已完成]
    |                                      |
    +--超时/取消--> [已取消]                +--申请售后--> [售后中]
```

**TradeOrderStatusEnum**:

| 值 | 状态 | 说明 |
|----|------|------|
| 0 | 待付款 | 订单创建后等待支付 |
| 1 | 待发货 | 支付完成等待发货 |
| 2 | 待收货 | 已发货等待确认收货 |
| 3 | 已完成 | 交易完成 |
| 4 | 已取消 | 超时未付或手动取消 |
| 5 | 售后中 | 申请售后处理中 |

---

## 2. 用户下单（app）

**Controller**: `AppTradeOrderController`
**路径前缀**: `/app-api/trade/order`

### 2.1 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 创建订单 |
| PUT | `/cancel` | 用户取消订单 |
| PUT | `/receive` | 用户确认收货 |
| GET | `/get` | 获取订单详情 |
| GET | `/page` | 用户订单列表 |
| GET | `/count` | 各状态订单数量统计 |

### 2.2 创建订单流程

```
1. 校验商品信息 (ProductSpuApi/ProductSkuApi)
2. 校验库存充足 (ProductSkuApi.validateSkuStock)
3. 校验优惠券 (CouponApi)
4. 计算价格 (TradePriceService)
5. 扣减库存 (ProductSkuApi.updateSkuStock)
6. 使用优惠券 (CouponApi)
7. 创建订单及订单项
8. 删除购物车对应商品
9. 创建支付订单 (PayOrderApi)
```

**TradeOrderCreateReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | List\<Item\> | 是 | 商品列表 |
| addressId | Long | 是 | 收货地址编号 |
| couponId | Long | 否 | 优惠券编号 |
| deliveryType | Integer | 是 | 配送方式 |
| remark | String | 否 | 订单备注 |

**TradeOrderCreateReqVO.Item**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuId | Long | 是 | SKU 编号 |
| count | Integer | 是 | 购买数量 |

---

## 3. 购物车（app）

**Controller**: `AppCartController`
**路径前缀**: `/app-api/trade/cart`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/add` | 添加商品到购物车 |
| PUT | `/update` | 更新购物车商品数量 |
| DELETE | `/delete` | 删除购物车商品 |
| GET | `/list` | 获取购物车列表 |
| GET | `/count` | 购物车商品数量 |

**CartSaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuId | Long | 是 | SKU 编号 |
| count | Integer | 是 | 数量 |

---

## 4. 售后管理

### 4.1 admin 端

**Controller**: `TradeAfterSaleController`
**路径前缀**: `/admin-api/trade/after-sale`
**权限前缀**: `trade:after-sale:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 售后单分页查询 | `trade:after-sale:query` |
| GET | `/get` | 获取售后单详情 | `trade:after-sale:query` |
| PUT | `/agree` | 同意售后 | `trade:after-sale:update` |
| PUT | `/reject` | 拒绝售后 | `trade:after-sale:update` |
| PUT | `/receive` | 确认收到退货 | `trade:after-sale:update` |
| PUT | `/refund` | 确认退款 | `trade:after-sale:update` |

### 4.2 app 端

**Controller**: `AppTradeAfterSaleController`
**路径前缀**: `/app-api/trade/after-sale`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 申请售后 |
| PUT | `/cancel` | 取消售后 |
| GET | `/get` | 售后单详情 |
| GET | `/page` | 售后单列表 |

**AfterSaleCreateReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | Long | 是 | 订单编号 |
| orderItemId | Long | 是 | 订单项编号 |
| type | Integer | 是 | 售后类型：0 退款 1 退货退款 |
| way | Integer | 是 | 退款方式 |
| refundPrice | Integer | 是 | 退款金额（分） |
| applyReason | String | 是 | 申请原因 |
| applyPicUrls | List\<String\> | 否 | 凭证图片 |

**AfterSaleStatusEnum**:

| 值 | 状态 |
|----|------|
| 0 | 待审批 |
| 1 | 退货中（等待用户寄回） |
| 2 | 待退款（已收到退货） |
| 3 | 退款成功 |
| 4 | 退款失败（拒绝） |
| 5 | 已取消 |

---

## 5. 物流管理

**Controller**: `DeliveryExpressController`
**路径前缀**: `/admin-api/trade/delivery`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/list-all` | 获取所有物流公司 |
| GET | `/track` | 查询物流轨迹 |

---

## 6. 价格计算服务（TradePriceService）

价格计算核心逻辑：

```
商品原价 totalPrice = SUM(sku.price * count)
优惠金额 discountPrice = couponDiscount + promotionDiscount
运费金额 deliveryPrice = 从运费模板计算
应付金额 payPrice = totalPrice - discountPrice + deliveryPrice
```

### 6.1 价格计算策略

| 策略 | 说明 |
|------|------|
| 普通商品 | 直接按 SKU 价格计算 |
| 秒杀商品 | 使用秒杀活动价格 |
| 拼团商品 | 使用拼团活动价格 |
| 砍价商品 | 使用砍价后价格 |
| 优惠券抵扣 | 减去优惠券面额 |
| 满减送 | 满足条件自动减免 |

---

## 7. 跨模块调用

| 被调用模块 | API | 场景 |
|-----------|-----|------|
| product | `ProductSpuApi` | 下单时查询商品信息、扣减库存 |
| product | `ProductSkuApi` | 下单时校验 SKU、扣减库存 |
| promotion | `CouponApi` | 下单时使用优惠券 |
| promotion | `SeckillActivityApi` | 秒杀商品下单校验 |
| pay | `PayOrderApi` | 创建支付订单、支付回调 |

---

## 8. 消息队列

| Topic | 触发时机 | 处理逻辑 |
|-------|---------|---------|
| `order.paid` | 支付成功 | 触发积分发放、优惠券赠送等 |
| `order.delivered` | 订单发货 | 通知用户 |

---

## 9. 错误码

| 错误码 | 说明 |
|--------|------|
| `1_011_000_011` | 交易订单不存在 |
| `1_011_000_017` | 交易订单发货失败，订单不是【待发货】状态 |
