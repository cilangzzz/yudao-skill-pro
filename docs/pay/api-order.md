# 支付订单 API 详解

> 业务域：支付订单的创建、提交、回调、状态同步。

## 核心领域模型

**聚合根**：`PayOrder`

- 管理订单完整生命周期
- 包含子实体 `PayOrderExtension`（多次支付尝试的扩展记录）

**状态机**：

```
WAITING (待支付) --支付成功--> SUCCESS (已支付)
WAITING (待支付) --主动关闭/超时--> CLOSED (已关闭)
SUCCESS (已支付) --退款--> REFUND (已退款)
```

**业务不变量**：
- 退款金额不能超过支付金额
- 状态变更使用乐观锁保证并发安全

## 模块间 API

### PayOrderApi

供其他模块（订单模块、会员模块）调用的内部接口。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `createOrder` | `PayOrderCreateReqDTO` | `Long` (订单ID) | 创建支付订单（幂等：相同 appId + merchantOrderId 返回已有订单ID） |
| `getOrder` | `Long id` | `PayOrderDO` | 查询支付订单 |

**PayOrderCreateReqDTO 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `appKey` | `String` | 应用标识 |
| `merchantOrderId` | `String` | 商户订单号（业务侧唯一） |
| `subject` | `String` | 商品标题 |
| `body` | `String` | 商品描述 |
| `price` | `Integer` | 支付金额（分） |
| `channelCode` | `String` | 渠道编码 |
| `userId` | `Long` | 用户编号 |
| `expireTime` | `LocalDateTime` | 过期时间 |

### Service 层

#### PayOrderService

| 方法 | 说明 |
|------|------|
| `createOrder(PayOrderCreateReqDTO)` | 创建支付订单，校验 App 并做幂等处理 |
| `submitOrder(PayOrderSubmitReqVO, String clientIP)` | 提交支付订单到渠道，返回支付参数 |
| `notifyOrder(PayOrderNotifyReqDTO)` | 处理渠道异步回调 |

**createOrder 流程**：

```
1. 校验 PayApp 存在且有效
2. 按 appId + merchantOrderId 查询是否已存在
3. 若已存在 -> 直接返回 orderId（幂等）
4. 创建 PayOrderDO，状态设为 WAITING
5. 插入数据库，返回 orderId
```

**submitOrder 流程**：

```
1. 查询 PayOrder，校验状态为 WAITING
2. 校验订单未过期
3. 根据 channelCode 获取对应的 PayClient
4. 创建 PayOrderExtension 扩展记录
5. 调用 PayClient.unifiedOrder() 发起支付
6. 返回支付参数（如支付 URL、表单等）
```

## HTTP 接口

### PayOrderController

路径前缀：`/pay/order`

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 提交支付 | POST | `/submit` | `@PermitAll` | 提交支付订单，返回支付参数 |
| 查询订单 | GET | `/get` | 需要权限 | 查询订单详情 |
| 分页查询 | GET | `/page` | 需要权限 | 分页查询订单列表 |

**提交支付接口** (`POST /pay/order/submit`)：

请求体 `PayOrderSubmitReqVO`：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `appKey` | `String` | 是 | 应用标识 |
| `channelCode` | `String` | 是 | 渠道编码（如 `wx_pub`, `alipay_pc`） |
| `merchantOrderId` | `String` | 是 | 商户订单号 |
| `subject` | `String` | 是 | 商品标题 |
| `body` | `String` | 否 | 商品描述 |
| `price` | `Integer` | 是 | 支付金额（分） |
| `userId` | `Long` | 否 | 用户编号 |
| `expireTime` | `LocalDateTime` | 否 | 过期时间 |

响应 `PayOrderSubmitRespVO`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `payOrderId` | `Long` | 支付订单 ID |
| `formKey` | `String` | 支付表单参数标识（用于后续查询） |

注意：`@PermitAll` 注解表示支付提交允许匿名访问，因为支付回调由第三方渠道发起。

## 数据表

### pay_order

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 订单编号（主键） |
| `app_id` | `Long` | 应用编号 |
| `channel_id` | `Long` | 渠道编号 |
| `channel_code` | `String` | 渠道编码 |
| `user_id` | `Long` | 用户编号 |
| `merchant_order_id` | `String` | 商户订单号 |
| `subject` | `String` | 商品标题 |
| `body` | `String` | 商品描述 |
| `price` | `Integer` | 支付金额（分） |
| `status` | `Integer` | 支付状态：0待支付 / 10成功 / 20退款 / 30关闭 |
| `refund_price` | `Integer` | 已退款金额（分） |
| `channel_order_no` | `String` | 渠道订单号 |
| `expire_time` | `LocalDateTime` | 过期时间 |
| `success_time` | `LocalDateTime` | 支付成功时间 |

索引：`idx_app_merchant (app_id, merchant_order_id)`

### pay_order_extension

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 扩展编号（主键） |
| `order_id` | `Long` | 订单编号（关联 pay_order） |
| `no` | `String` | 外部订单号 |
| `channel_id` | `Long` | 渠道编号 |
| `channel_code` | `String` | 渠道编码 |
| `status` | `Integer` | 支付状态 |
| `channel_notify_data` | `String` | 渠道回调原始数据 |

## Mapper 接口

### PayOrderMapper

继承 `BaseMapperX<PayOrderDO>`，提供以下默认方法：

| 方法 | 说明 |
|------|------|
| `selectByAppIdAndMerchantOrderId(appId, merchantOrderId)` | 按应用+商户订单号查询（幂等校验） |
| `updateByIdAndStatus(id, status, updateObj)` | 乐观锁更新：仅当状态匹配时才更新 |

## 设计模式在本域的应用

**模板方法**：`AbstractPayClient.unifiedOrder()` 定义统一下单流程，子类实现 `doUnifiedOrder()`。

**工厂**：`PayClientFactory.getPayClient(channelId)` 根据渠道 ID 获取对应的支付客户端。

**策略**：不同渠道（微信/支付宝/钱包/模拟）的 `doUnifiedOrder()` 实现各不相同，但对 Service 层透明。

## 代码示例

### 业务模块调用支付 API

```java
// 在订单模块中调用
Long payOrderId = payOrderApi.createOrder(new PayOrderCreateReqDTO()
        .setAppKey("trade")
        .setMerchantOrderId(order.getOrderNo())
        .setSubject(order.getTitle())
        .setPrice(order.getPayPrice())
        .setChannelCode(PayChannelEnum.WX_PUB.getCode())
        .setUserId(order.getUserId()));
```

### Service 层提交支付

```java
// 1. 获取支付客户端
PayClient client = channelService.getPayClient(channelId);

// 2. 构建统一下单请求
PayOrderUnifiedReqDTO reqDTO = new PayOrderUnifiedReqDTO()
        .setOutTradeNo(orderExtension.getNo())
        .setSubject(order.getSubject())
        .setPrice(order.getPrice())
        .setExpireTime(order.getExpireTime())
        .setNotifyUrl(notifyUrl);

// 3. 调用支付渠道
PayOrderRespDTO respDTO = client.unifiedOrder(reqDTO);
```
