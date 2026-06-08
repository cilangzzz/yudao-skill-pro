# 异步通知 API 详解

> 业务域：支付/退款异步回调处理、通知任务管理、重试机制。

## 核心领域模型

**实体**：`PayNotifyTask`

- 管理向业务模块发送异步通知的任务
- 支持订单通知和退款通知两种类型
- 内置重试机制，记录通知次数和最大重试次数

## 通知流程

### 支付回调处理

```
渠道服务器 --异步回调--> PayNotifyController
    |
    v
PayNotifyService.parseOrderNotify()
    |
    +-- 1. 验签（使用渠道提供的验签方法）
    +-- 2. 解析回调数据
    +-- 3. 更新 PayOrder 状态
    +-- 4. 更新 PayOrderExtension 回调数据
    +-- 5. 创建 PayNotifyTask（通知业务模块）
    |
    v
返回 SUCCESS 给渠道
```

### 退款回调处理

```
渠道服务器 --异步回调--> PayNotifyController
    |
    v
PayNotifyService.parseRefundNotify()
    |
    +-- 1. 验签
    +-- 2. 解析回调数据
    +-- 3. 更新 PayRefund 状态
    +-- 4. 更新 PayOrder 的 refund_price
    +-- 5. 创建 PayNotifyTask（通知业务模块）
    |
    v
返回 SUCCESS 给渠道
```

### 通知业务模块

```
PayNotifyJob（定时任务）
    |
    v
查询待处理的 PayNotifyTask
    |
    v
调用业务模块配置的回调地址（order_notify_url / refund_notify_url）
    |
    +-- 成功 -> 更新任务状态为成功
    +-- 失败 -> 通知次数 +1
    |          如果 notify_times >= max_notify_times -> 标记为失败
    |          否则 -> 等待下次重试
```

## HTTP 接口

### PayNotifyController

路径前缀：`/pay/notify`

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 微信支付回调 | POST | `/wx/pay` | `@PermitAll` | 微信支付异步回调 |
| 微信退款回调 | POST | `/wx/refund` | `@PermitAll` | 微信退款异步回调 |
| 支付宝支付回调 | POST | `/alipay/pay` | `@PermitAll` | 支付宝支付异步回调 |
| 支付宝退款回调 | POST | `/alipay/refund` | `@PermitAll` | 支付宝退款异步回调 |

注意：所有回调接口使用 `@PermitAll` 注解，因为回调请求来自第三方渠道服务器，无法进行身份认证。安全性通过验签机制保证。

## 数据表

### pay_notify_task

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 任务编号（主键） |
| `app_id` | `Long` | 应用编号 |
| `type` | `Integer` | 通知类型：1订单 / 2退款 |
| `data_id` | `Long` | 数据编号（订单ID或退款ID） |
| `status` | `Integer` | 通知状态 |
| `notify_times` | `Integer` | 已通知次数 |
| `max_notify_times` | `Integer` | 最大通知次数 |

## 定时任务

### PayNotifyJob

- **职责**：定时扫描待处理的 `PayNotifyTask`，调用业务模块的回调地址
- **重试策略**：失败后递增 `notify_times`，超过 `max_notify_times` 后标记为最终失败
- **回调地址**：从 `PayApp` 的 `order_notify_url` 或 `refund_notify_url` 获取

### PayOrderSyncJob

- **职责**：定时同步待支付订单状态
- **场景**：对于长时间处于 WAITING 状态的订单，主动查询渠道确认实际状态
- **必要性**：某些场景下回调可能丢失，主动查询作为兜底

### PayOrderExpireJob

- **职责**：定时关闭过期订单
- **逻辑**：查询 `expire_time < now` 且状态为 WAITING 的订单，调用 `PayClient.closeOrder()` 关闭

## Service 层

### PayNotifyService

| 方法 | 说明 |
|------|------|
| `parseOrderNotify(PayNotifyDataDTO)` | 处理支付回调 |
| `parseRefundNotify(PayNotifyDataDTO)` | 处理退款回调 |
| `notify(PayNotifyTaskDO)` | 执行通知业务模块 |

**PayNotifyDataDTO 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `channelCode` | `String` | 渠道编码 |
| `channelId` | `Long` | 渠道编号 |
| `data` | `String` | 回调原始数据 |
| `signature` | `String` | 签名 |
| `nonce` | `String` | 随机串 |
| `timestamp` | `String` | 时间戳 |

## 关键设计要点

1. **验签优先**：所有回调处理的第一步是验签，防止伪造请求。

2. **幂等处理**：回调可能重复到达（渠道重试），更新订单状态时使用乐观锁（`updateByIdAndStatus`）保证幂等。

3. **异步解耦**：回调处理完成后不直接通知业务模块，而是创建 `PayNotifyTask`，由定时任务异步通知，降低耦合。

4. **重试机制**：通知失败自动重试，支持配置最大重试次数。

5. **兜底同步**：`PayOrderSyncJob` 主动查询渠道状态，应对回调丢失的场景。

6. **回调数据留存**：`PayOrderExtension.channel_notify_data` 保存渠道回调原始数据，便于排查问题。
