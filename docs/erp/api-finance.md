# 财务域 API 文档

## 概述

财务域涵盖结算账户管理、付款单、收款单。
控制器路径前缀：`/erp/finance-*`、`/erp/account`

## 业务流程

```
采购入库(审核) -> 付款单(创建) -> 付款单(审核，更新已付款金额)
销售出库(审核) -> 收款单(创建) -> 收款单(审核，更新已收款金额)
```

关键规则：
- 付款单关联采购入库单，记录采购付款
- 收款单关联销售出库单，记录销售收款
- 审核付款/收款单后，更新关联单据的已付/已收金额

---

## 结算账户

### 创建结算账户

- **接口**: `POST /erp/account/create`
- **权限**: `erp:account:create`
- **请求参数**: `ErpAccountSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 账户名称 |
| no | String | 否 | 账户编号 |
| status | Integer | 否 | 状态 |

- **响应**: `CommonResult<Long>` - 账户编号

### 更新结算账户

- **接口**: `PUT /erp/account/update`
- **权限**: `erp:account:update`
- **请求参数**: `ErpAccountSaveReqVO`（含 id）

### 删除结算账户

- **接口**: `DELETE /erp/account/delete`
- **权限**: `erp:account:delete`
- **请求参数**: `id` (Long)

### 查询结算账户分页

- **接口**: `GET /erp/account/page`
- **权限**: `erp:account:query`
- **请求参数**: `ErpAccountPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 账户名称（模糊查询） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpAccountRespVO>>`

---

## 付款单

### 创建付款单

- **接口**: `POST /erp/finance-payment/create`
- **权限**: `erp:finance-payment:create`
- **请求参数**: `ErpFinancePaymentSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplierId | Long | 是 | 供应商ID |
| accountId | Long | 是 | 付款账户ID |
| paymentTime | Date | 是 | 付款时间 |
| discountPrice | BigDecimal | 否 | 优惠金额 |
| items | List | 是 | 付款项列表 |

**付款项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchaseInId | Long | 是 | 关联采购入库单ID |
| price | BigDecimal | 是 | 付款金额 |

- **响应**: `CommonResult<Long>` - 付款单编号

**业务逻辑**:
1. 校验供应商是否存在
2. 校验结算账户是否存在
3. 校验采购入库单是否存在且已审核
4. 自动生成单据号（前缀：FKD）
5. 计算合计金额和实付金额
6. 保存主表和子表

### 更新付款单

- **接口**: `PUT /erp/finance-payment/update`
- **权限**: `erp:finance-payment:update`
- **请求参数**: `ErpFinancePaymentSaveReqVO`（含 id）

**业务逻辑**:
- 已审核的付款单不可更新
- 使用 diffList 差量更新付款项

### 删除付款单

- **接口**: `DELETE /erp/finance-payment/delete`
- **权限**: `erp:finance-payment:delete`
- **请求参数**: `ids` (List<Long>)

**业务逻辑**:
- 已审核的付款单不可删除

### 更新付款单状态

- **接口**: `PUT /erp/finance-payment/update-status`
- **权限**: `erp:finance-payment:update-status`
- **请求参数**: `id` (Long), `status` (Integer)

**审核逻辑**:
1. 校验付款单存在且状态匹配
2. 遍历付款项，更新采购入库单的已付款金额
3. 更新付款单状态

**反审核逻辑**:
1. 回退采购入库单的已付款金额
2. 更新付款单状态

### 查询付款单分页

- **接口**: `GET /erp/finance-payment/page`
- **权限**: `erp:finance-payment:query`
- **请求参数**: `ErpFinancePaymentPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 付款单号（模糊查询） |
| status | Integer | 否 | 状态 |
| supplierId | Long | 否 | 供应商ID |
| accountId | Long | 否 | 付款账户ID |
| paymentTime | Date[] | 否 | 付款时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpFinancePaymentRespVO>>`

---

## 收款单

### 创建收款单

- **接口**: `POST /erp/finance-receipt/create`
- **权限**: `erp:finance-receipt:create`
- **请求参数**: `ErpFinanceReceiptSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customerId | Long | 是 | 客户ID |
| accountId | Long | 是 | 收款账户ID |
| receiptTime | Date | 是 | 收款时间 |
| discountPrice | BigDecimal | 否 | 优惠金额 |
| items | List | 是 | 收款项列表 |

**收款项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| saleOutId | Long | 是 | 关联销售出库单ID |
| price | BigDecimal | 是 | 收款金额 |

- **响应**: `CommonResult<Long>` - 收款单编号

**业务逻辑**:
1. 校验客户是否存在
2. 校验结算账户是否存在
3. 校验销售出库单是否存在且已审核
4. 自动生成单据号（前缀：SKD）
5. 计算合计金额和实收金额
6. 保存主表和子表

### 更新收款单

- **接口**: `PUT /erp/finance-receipt/update`
- **权限**: `erp:finance-receipt:update`
- **请求参数**: `ErpFinanceReceiptSaveReqVO`（含 id）

**业务逻辑**:
- 已审核的收款单不可更新
- 使用 diffList 差量更新收款项

### 删除收款单

- **接口**: `DELETE /erp/finance-receipt/delete`
- **权限**: `erp:finance-receipt:delete`
- **请求参数**: `ids` (List<Long>)

**业务逻辑**:
- 已审核的收款单不可删除

### 更新收款单状态

- **接口**: `PUT /erp/finance-receipt/update-status`
- **权限**: `erp:finance-receipt:update-status`
- **请求参数**: `id` (Long), `status` (Integer)

**审核逻辑**:
1. 校验收款单存在且状态匹配
2. 遍历收款项，更新销售出库单的已收款金额
3. 更新收款单状态

**反审核逻辑**:
1. 回退销售出库单的已收款金额
2. 更新收款单状态

### 查询收款单分页

- **接口**: `GET /erp/finance-receipt/page`
- **权限**: `erp:finance-receipt:query`
- **请求参数**: `ErpFinanceReceiptPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 收款单号（模糊查询） |
| status | Integer | 否 | 状态 |
| customerId | Long | 否 | 客户ID |
| accountId | Long | 否 | 收款账户ID |
| receiptTime | Date[] | 否 | 收款时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpFinanceReceiptRespVO>>`

---

## 错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_030_300_000 | ACCOUNT_NOT_EXISTS | 结算账户不存在 |
| 1_030_301_000 | FINANCE_PAYMENT_NOT_EXISTS | 付款单不存在 |
| 1_030_301_001 | FINANCE_PAYMENT_DELETE_FAIL_APPROVE | 付款单已审核，无法删除 |
| 1_030_301_003 | FINANCE_PAYMENT_APPROVE_FAIL | 审核失败，只有未审核的付款单才能审核 |
| 1_030_302_000 | FINANCE_RECEIPT_NOT_EXISTS | 收款单不存在 |
| 1_030_302_001 | FINANCE_RECEIPT_DELETE_FAIL_APPROVE | 收款单已审核，无法删除 |
| 1_030_302_003 | FINANCE_RECEIPT_APPROVE_FAIL | 审核失败，只有未审核的收款单才能审核 |
