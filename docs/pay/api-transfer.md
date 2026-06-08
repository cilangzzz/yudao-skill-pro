# 转账 API 详解

> 业务域：企业付款到零钱、转账到银行卡。

## 核心领域模型

**实体**：`PayTransfer`

- 管理转账单生命周期
- 支持多种转账类型（到零钱、到银行卡）

## 模块间 API

### PayTransferApi

供内部使用的转账接口。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| 创建转账 | `PayTransferCreateReqDTO` | `Long` (转账ID) | 发起转账 |

**PayTransferCreateReqDTO 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `appKey` | `String` | 应用标识 |
| `type` | `Integer` | 转账类型 |
| `price` | `Integer` | 转账金额（分） |
| `userName` | `String` | 收款人姓名 |
| `userAccount` | `String` | 收款人账号 |

## 数据表

### pay_transfer

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 转账编号（主键） |
| `no` | `String` | 外部转账号 |
| `app_id` | `Long` | 应用编号 |
| `channel_id` | `Long` | 渠道编号 |
| `type` | `Integer` | 转账类型 |
| `price` | `Integer` | 转账金额（分） |
| `status` | `Integer` | 转账状态 |
| `user_name` | `String` | 收款人姓名 |
| `user_account` | `String` | 收款人账号 |

## 转账流程

```
1. 业务模块调用 PayTransferApi 创建转账单
2. 获取对应渠道的 PayClient
3. 调用 PayClient.unifiedTransfer() 发起转账
4. 等待渠道回调或主动查询转账结果
5. 更新转账单状态
```

## 关键设计要点

1. **实名校验**：转账到零钱需要收款人姓名与微信实名一致。
2. **金额限制**：企业付款到零钱单笔最低 1 元，最高根据商户资质确定。
3. **转账到银行卡**：需要额外的加密处理（公钥加密敏感信息）。
