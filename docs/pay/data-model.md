# Pay 模块数据模型

> 支付中台模块共 9 张核心表，覆盖应用管理、渠道配置、支付订单、退款、钱包、转账、通知任务等业务域。

## 实体继承体系

| 基类 | 说明 | 使用表 |
|------|------|--------|
| `TenantBaseDO` | 多租户基类，包含租户ID、创建时间、更新时间等 | `pay_app`, `pay_channel` |
| `BaseDO` | 基础基类，包含创建时间、更新时间等 | `pay_order`, `pay_order_extension`, `pay_refund`, `pay_wallet`, `pay_wallet_transaction`, `pay_transfer`, `pay_notify_task` |

## ER 关系图

```
pay_app (1) ----< (N) pay_channel
    |                       |
    |                       |
    +----< (N) pay_order ---+
              |
              +----< (N) pay_order_extension
              |
              +----< (N) pay_refund

pay_wallet (1) ----< (N) pay_wallet_transaction

[独立表] pay_transfer
[独立表] pay_notify_task
```

## 表详细定义

### 1. pay_app -- 支付应用表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 应用编号（主键） |
| `name` | `String` | 是 | - | 应用名称 |
| `status` | `Integer` | 是 | - | 开启状态 |
| `order_notify_url` | `String` | 否 | - | 订单回调地址 |
| `refund_notify_url` | `String` | 否 | - | 退款回调地址 |

继承字段：`tenant_id`, `create_time`, `update_time`, `creator`, `updater`, `deleted`

**业务说明**：每个业务系统（如商城、会员）创建一个支付应用，配置独立的回调地址。

---

### 2. pay_channel -- 支付渠道表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 渠道编号（主键） |
| `code` | `String` | 是 | - | 渠道编码（如 `wx_pub`, `alipay_wap`） |
| `status` | `Integer` | 是 | - | 开启状态 |
| `fee_rate` | `Double` | 否 | - | 渠道费率 |
| `app_id` | `Long` | 是 | - | 应用编号（外键 -> pay_app） |
| `config` | `PayClientConfig` | 是 | - | 支付配置（JSON 存储） |

继承字段：`tenant_id`, `create_time`, `update_time`, `creator`, `updater`, `deleted`

**关系**：`pay_app` 1:N `pay_channel`，一个应用可配置多个支付渠道。

**config 字段示例**（微信）：

```json
{
  "appId": "wx1234567890",
  "mchId": "1234567890",
  "apiKey": "...",
  "apiKeyV3": "...",
  "certPath": "/path/to/cert.p12",
  "certPemPath": "/path/to/cert.pem",
  "keyPemPath": "/path/to/key.pem"
}
```

---

### 3. pay_order -- 支付订单表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 订单编号（主键） |
| `app_id` | `Long` | 是 | - | 应用编号（外键 -> pay_app） |
| `channel_id` | `Long` | 是 | - | 渠道编号（外键 -> pay_channel） |
| `channel_code` | `String` | 是 | - | 渠道编码 |
| `user_id` | `Long` | 否 | - | 用户编号 |
| `merchant_order_id` | `String` | 是 | - | 商户订单号 |
| `subject` | `String` | 是 | - | 商品标题 |
| `body` | `String` | 否 | - | 商品描述 |
| `price` | `Integer` | 是 | - | 支付金额（分） |
| `status` | `Integer` | 是 | 0 | 支付状态：0待支付 / 10成功 / 20退款 / 30关闭 |
| `refund_price` | `Integer` | 否 | 0 | 已退款金额（分） |
| `channel_order_no` | `String` | 否 | - | 渠道订单号 |
| `expire_time` | `LocalDateTime` | 否 | - | 过期时间 |
| `success_time` | `LocalDateTime` | 否 | - | 支付成功时间 |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

**索引**：`idx_app_merchant (app_id, merchant_order_id)` -- 保证同一应用下商户订单号唯一。

**关系**：
- `pay_app` 1:N `pay_order`
- `pay_channel` 1:N `pay_order`

**状态说明**：

| 状态值 | 枚举 | 说明 |
|--------|------|------|
| 0 | `WAITING` | 待支付 |
| 10 | `SUCCESS` | 支付成功 |
| 20 | `REFUND` | 已退款 |
| 30 | `CLOSED` | 已关闭 |

---

### 4. pay_order_extension -- 支付订单扩展表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 扩展编号（主键） |
| `order_id` | `Long` | 是 | - | 订单编号（外键 -> pay_order） |
| `no` | `String` | 是 | - | 外部订单号（每次支付尝试的唯一标识） |
| `channel_id` | `Long` | 是 | - | 渠道编号 |
| `channel_code` | `String` | 是 | - | 渠道编码 |
| `status` | `Integer` | 是 | - | 支付状态 |
| `channel_notify_data` | `String` | 否 | - | 渠道回调原始数据 |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

**关系**：`pay_order` 1:N `pay_order_extension`，一个订单可有多次支付尝试（如切换渠道重试）。

**业务说明**：每次调用 `submitOrder` 都会创建一条扩展记录，用于追踪每次支付尝试的状态和回调数据。

---

### 5. pay_refund -- 退款订单表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 退款编号（主键） |
| `no` | `String` | 是 | - | 外部退款号 |
| `app_id` | `Long` | 是 | - | 应用编号 |
| `channel_id` | `Long` | 是 | - | 渠道编号 |
| `order_id` | `Long` | 是 | - | 支付订单编号（外键 -> pay_order） |
| `order_no` | `String` | 是 | - | 支付订单号 |
| `merchant_order_id` | `String` | 是 | - | 商户订单号 |
| `merchant_refund_id` | `String` | 是 | - | 商户退款号 |
| `pay_price` | `Integer` | 是 | - | 原支付金额（分） |
| `refund_price` | `Integer` | 是 | - | 退款金额（分） |
| `status` | `Integer` | 是 | 0 | 退款状态：0待退款 / 1成功 / 2失败 |
| `reason` | `String` | 否 | - | 退款原因 |
| `channel_refund_no` | `String` | 否 | - | 渠道退款单号 |
| `success_time` | `LocalDateTime` | 否 | - | 退款成功时间 |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

**关系**：`pay_order` 1:N `pay_refund`，一个支付订单可多次部分退款。

---

### 6. pay_wallet -- 钱包表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 钱包编号（主键） |
| `user_id` | `Long` | 是 | - | 用户编号（唯一） |
| `balance` | `Integer` | 是 | 0 | 余额（分） |
| `freeze_price` | `Integer` | 否 | 0 | 冻结金额（分） |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

**业务说明**：每个用户一个钱包，可用余额 = `balance - freeze_price`。

---

### 7. pay_wallet_transaction -- 钱包交易表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 交易编号（主键） |
| `wallet_id` | `Long` | 是 | - | 钱包编号（外键 -> pay_wallet） |
| `biz_type` | `Integer` | 是 | - | 业务类型 |
| `biz_id` | `String` | 是 | - | 业务编号 |
| `amount` | `Integer` | 是 | - | 交易金额（分） |
| `balance` | `Integer` | 是 | - | 交易后余额（分） |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

**关系**：`pay_wallet` 1:N `pay_wallet_transaction`

---

### 8. pay_transfer -- 转账表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 转账编号（主键） |
| `no` | `String` | 是 | - | 外部转账号 |
| `app_id` | `Long` | 是 | - | 应用编号 |
| `channel_id` | `Long` | 是 | - | 渠道编号 |
| `type` | `Integer` | 是 | - | 转账类型 |
| `price` | `Integer` | 是 | - | 转账金额（分） |
| `status` | `Integer` | 是 | - | 转账状态 |
| `user_name` | `String` | 否 | - | 收款人姓名 |
| `user_account` | `String` | 否 | - | 收款人账号 |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

---

### 9. pay_notify_task -- 通知任务表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | `Long` | 是 | 自增 | 任务编号（主键） |
| `app_id` | `Long` | 是 | - | 应用编号 |
| `type` | `Integer` | 是 | - | 通知类型：1订单 / 2退款 |
| `data_id` | `Long` | 是 | - | 数据编号（订单ID或退款ID） |
| `status` | `Integer` | 是 | - | 通知状态 |
| `notify_times` | `Integer` | 是 | 0 | 已通知次数 |
| `max_notify_times` | `Integer` | 是 | - | 最大通知次数 |

继承字段：`create_time`, `update_time`, `creator`, `updater`, `deleted`

## 关系汇总

| 关系 | 类型 | 外键 | 说明 |
|------|------|------|------|
| pay_app -> pay_channel | 1:N | `channel.app_id` | 一个应用多个渠道 |
| pay_app -> pay_order | 1:N | `order.app_id` | 一个应用多个订单 |
| pay_channel -> pay_order | 1:N | `order.channel_id` | 一个渠道多个订单 |
| pay_order -> pay_order_extension | 1:N | `extension.order_id` | 一个订单多次支付尝试 |
| pay_order -> pay_refund | 1:N | `refund.order_id` | 一个订单多次退款 |
| pay_wallet -> pay_wallet_transaction | 1:N | `transaction.wallet_id` | 一个钱包多笔交易 |

## 设计要点

1. **金额单位**：所有金额字段统一使用 `Integer` 类型，单位为分，避免浮点精度问题。

2. **多租户**：`pay_app` 和 `pay_channel` 继承 `TenantBaseDO`，支持多租户数据隔离。其他表通过 `app_id` 间接关联租户。

3. **乐观锁**：订单状态变更使用 `updateByIdAndStatus` 方法，通过状态条件保证并发安全。

4. **索引设计**：`pay_order` 的 `idx_app_merchant (app_id, merchant_order_id)` 索引支持按应用+商户订单号的高效查询和幂等校验。

5. **JSON 存储**：`pay_channel.config` 使用 JSON 格式存储不同渠道的配置，灵活性高。

6. **回调数据留存**：`pay_order_extension.channel_notify_data` 保存渠道回调原始数据，便于问题排查和审计。
