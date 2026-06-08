# 钱包 API 详解

> 业务域：用户钱包余额管理，包括充值、消费、提现、冻结。

## 核心领域模型

**实体**：`PayWallet`

- 每个用户对应一个钱包
- 余额单位为分（Integer），避免浮点精度问题
- 支持余额冻结（`freeze_price`）

**关联实体**：`PayWalletTransaction`

- 记录每笔钱包交易流水
- 通过 `wallet_id` 关联钱包
- 通过 `biz_type` + `biz_id` 关联业务来源

## 模块间 API

### PayWalletApi

供其他模块（会员模块、订单模块）调用的内部接口。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `addBalance` | `userId`, `amount`, `bizType`, `bizId` | `void` | 增加余额（充值/退款入账） |
| `getWallet` | `userId` | `PayWalletDO` | 查询用户钱包 |

**消费场景**：订单模块通过 `PayClient` 调用 `WalletPayClient` 进行余额扣减。

## HTTP 接口

钱包管理接口通常在管理后台提供查询能力：

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 查询钱包 | GET | `/pay/wallet/get` | 查询用户钱包信息 |
| 查询交易流水 | GET | `/pay/wallet-transaction/page` | 分页查询交易记录 |

## 数据表

### pay_wallet

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 钱包编号（主键） |
| `user_id` | `Long` | 用户编号（唯一索引） |
| `balance` | `Integer` | 余额（分） |
| `freeze_price` | `Integer` | 冻结金额（分） |

### pay_wallet_transaction

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 交易编号（主键） |
| `wallet_id` | `Long` | 钱包编号（关联 pay_wallet） |
| `biz_type` | `Integer` | 业务类型（充值/消费/提现等） |
| `biz_id` | `String` | 业务编号 |
| `amount` | `Integer` | 交易金额（分） |
| `balance` | `Integer` | 交易后余额（分） |

## 钱包支付流程

钱包支付通过 `WalletPayClient` 实现，走 `PayClient` 统一接口：

```
1. 订单模块调用 PayOrderApi.createOrder()，channelCode = "wallet"
2. PayOrderServiceImpl 获取 WalletPayClient
3. WalletPayClient.doUnifiedOrder():
   a. 查询用户钱包
   b. 校验余额 >= 支付金额
   c. 扣减余额（乐观锁）
   d. 插入交易流水
   e. 返回支付成功结果
```

## 关键设计要点

1. **金额精度**：所有金额字段统一使用 `Integer` 类型，单位为分。

2. **乐观锁**：余额扣减使用 `updateByIdAndStatus` 或 CAS 方式，防止并发超扣。

3. **交易流水**：每笔余额变动必须记录交易流水（`PayWalletTransactionDO`），保证可追溯。

4. **冻结机制**：`freeze_price` 用于提现等场景，冻结金额不可用于消费。可用余额 = `balance - freeze_price`。

5. **幂等处理**：`biz_type` + `biz_id` 组合保证同一笔业务不会重复入账/扣款。
