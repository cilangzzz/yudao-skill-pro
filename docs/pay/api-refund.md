# 退款 API 详解

> 业务域：退款发起、退款回调、退款状态同步。

## 核心领域模型

**聚合根**：`PayRefund`

- 管理退款单完整生命周期
- 一个支付订单（`PayOrder`）可以有多个退款单

**状态机**：

```
WAITING (待退款) --退款成功--> SUCCESS (退款成功)
WAITING (待退款) --退款失败--> FAILURE (退款失败)
```

**业务不变量**：
- 退款金额累计不能超过原支付金额
- 退款单关联的支付订单必须处于 SUCCESS 状态

## 模块间 API

### PayRefundApi

供其他模块（订单模块）调用的内部接口。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `createRefund` | `PayRefundCreateReqDTO` | `Long` (退款ID) | 创建退款单 |
| `getRefund` | `Long id` | `PayRefundDO` | 查询退款单 |

**PayRefundCreateReqDTO 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `appKey` | `String` | 应用标识 |
| `merchantRefundId` | `String` | 商户退款号（业务侧唯一） |
| `payOrderId` | `Long` | 关联的支付订单 ID |
| `refundPrice` | `Integer` | 退款金额（分） |
| `reason` | `String` | 退款原因 |

### Service 层

#### PayRefundService

| 方法 | 说明 |
|------|------|
| `createRefund(PayRefundCreateReqDTO)` | 创建退款单，校验退款金额 |
| `notifyRefund(PayRefundNotifyReqDTO)` | 处理退款异步回调 |

**createRefund 流程**：

```
1. 校验 PayApp 存在且有效
2. 查询 PayOrder，校验状态为 SUCCESS
3. 校验退款金额：累计退款金额 <= 支付金额
   错误码：1_007_006_000（退款金额超过订单可退款金额）
4. 创建 PayRefundDO，状态设为 WAITING
5. 获取 PayClient，调用 unifiedRefund() 发起退款
6. 更新 PayOrder 的 refund_price 累计值
7. 返回 refundId
```

**notifyRefund 流程**：

```
1. 验签（使用渠道提供的验签方法）
2. 解析回调数据，确定退款成功或失败
3. 更新 PayRefundDO 状态
4. 如果退款成功，更新 PayOrder 的 refund_price
5. 创建 PayNotifyTask 通知业务模块
```

## HTTP 接口

### PayRefundController

路径前缀：`/pay/refund`

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 发起退款 | POST | `/create` | 需要权限 | 创建退款单 |
| 查询退款 | GET | `/get` | 需要权限 | 查询退款详情 |
| 分页查询 | GET | `/page` | 需要权限 | 分页查询退款列表 |

## 数据表

### pay_refund

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 退款编号（主键） |
| `no` | `String` | 外部退款号 |
| `app_id` | `Long` | 应用编号 |
| `channel_id` | `Long` | 渠道编号 |
| `order_id` | `Long` | 支付订单编号（关联 pay_order） |
| `order_no` | `String` | 支付订单号 |
| `merchant_order_id` | `String` | 商户订单号 |
| `merchant_refund_id` | `String` | 商户退款号 |
| `pay_price` | `Integer` | 原支付金额（分） |
| `refund_price` | `Integer` | 退款金额（分） |
| `status` | `Integer` | 退款状态：0待退款 / 1成功 / 2失败 |
| `reason` | `String` | 退款原因 |
| `channel_refund_no` | `String` | 渠道退款单号 |
| `success_time` | `LocalDateTime` | 退款成功时间 |

**与 pay_order 的关系**：`order_id` 外键关联，1:N（一个支付订单可多次部分退款）。

## 代码示例

### 业务模块调用退款 API

```java
// 在订单模块中调用
Long refundId = payRefundApi.createRefund(new PayRefundCreateReqDTO()
        .setAppKey("trade")
        .setMerchantRefundId("REF_" + order.getOrderNo())
        .setPayOrderId(order.getPayOrderId())
        .setRefundPrice(refundAmount)
        .setReason("用户申请退款"));
```

### Service 层发起退款

```java
// 1. 获取支付客户端
PayClient client = channelService.getPayClient(channelId);

// 2. 构建退款请求
PayRefundUnifiedReqDTO reqDTO = new PayRefundUnifiedReqDTO()
        .setOutTradeNo(order.getNo())
        .setOutRefundNo(refund.getNo())
        .setRefundPrice(refund.getRefundPrice())
        .setReason(refund.getReason());

// 3. 调用退款接口
PayRefundRespDTO respDTO = client.unifiedRefund(reqDTO);
```

## 关键设计要点

1. **退款金额校验**：在 Service 层做累计校验，防止并发退款导致超额退款。校验逻辑：`已退款金额 + 本次退款金额 <= 支付金额`。

2. **乐观锁更新**：PayOrder 的 `refund_price` 更新使用 `updateByIdAndStatus` 保证并发安全。

3. **退款回调验签**：必须使用渠道提供的验签方法验证回调来源合法性。

4. **通知业务模块**：退款成功后通过 `PayNotifyTask` 异步通知业务模块，支持重试。
