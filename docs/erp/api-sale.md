# 销售域 API 文档

## 概述

销售域涵盖客户管理、销售订单、销售出库、销售退货的完整业务流程。
控制器路径前缀：`/erp/sale-*`、`/erp/customer`

## 业务流程

```
销售订单(创建) -> 销售订单(审核) -> 销售出库(创建) -> 销售出库(审核，库存减少)
                                                     -> 销售退货(创建) -> 销售退货(审核，库存增加)
```

关键规则：
- 销售出库/退货必须关联销售订单
- 审核销售出库时，系统自动扣减库存并创建库存记录
- 审核销售退货时，系统自动增加库存并创建库存记录
- 反审核时，系统自动回滚库存变动
- 已审核的单据不可修改/删除，需先反审核

---

## 客户管理

### 创建客户

- **接口**: `POST /erp/customer/create`
- **权限**: `erp:customer:create`
- **请求参数**: `ErpCustomerSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 客户名称 |
| contact | String | 否 | 联系人 |
| mobile | String | 否 | 手机号 |
| status | Integer | 否 | 状态 |

- **响应**: `CommonResult<Long>` - 客户编号

### 更新客户

- **接口**: `PUT /erp/customer/update`
- **权限**: `erp:customer:update`
- **请求参数**: `ErpCustomerSaveReqVO`（含 id）

### 删除客户

- **接口**: `DELETE /erp/customer/delete`
- **权限**: `erp:customer:delete`
- **请求参数**: `id` (Long)

### 查询客户分页

- **接口**: `GET /erp/customer/page`
- **权限**: `erp:customer:query`
- **请求参数**: `ErpCustomerPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 客户名称（模糊查询） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpCustomerRespVO>>`

---

## 销售订单

### 创建销售订单

- **接口**: `POST /erp/sale-order/create`
- **权限**: `erp:sale-order:create`
- **请求参数**: `ErpSaleOrderSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customerId | Long | 是 | 客户ID |
| accountId | Long | 否 | 结算账户ID |
| saleUserId | Long | 否 | 销售员ID |
| orderTime | Date | 是 | 下单时间 |
| items | List | 是 | 订单项列表 |

**订单项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| count | BigDecimal | 是 | 数量 |
| productPrice | BigDecimal | 是 | 产品单价 |

- **响应**: `CommonResult<Long>` - 销售订单编号

**业务逻辑**:
1. 校验客户是否存在
2. 校验订单项产品是否存在
3. 自动生成单据号（前缀：XSDD）
4. 计算合计数量和价格
5. 保存主表和子表（使用事务）

### 更新销售订单

- **接口**: `PUT /erp/sale-order/update`
- **权限**: `erp:sale-order:update`
- **请求参数**: `ErpSaleOrderSaveReqVO`（含 id）

**业务逻辑**:
- 已审核的订单不可更新
- 使用 diffList 差量更新订单项（新增、修改、删除）

### 删除销售订单

- **接口**: `DELETE /erp/sale-order/delete`
- **权限**: `erp:sale-order:delete`
- **请求参数**: `ids` (List<Long>)

**业务逻辑**:
- 已审核的订单不可删除
- 检查是否有关联的销售出库单或退货单

### 更新销售订单状态

- **接口**: `PUT /erp/sale-order/update-status`
- **权限**: `erp:sale-order:update-status`
- **请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 订单编号 |
| status | Integer | 是 | 目标状态(10未审核 20已审核) |

**状态流转**:
- `PROCESS(10)` -> `APPROVE(20)`: 审核
- `APPROVE(20)` -> `PROCESS(10)`: 反审核（需检查关联的出库/退货单）

### 查询销售订单分页

- **接口**: `GET /erp/sale-order/page`
- **权限**: `erp:sale-order:query`
- **请求参数**: `ErpSaleOrderPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 订单号（模糊查询） |
| status | Integer | 否 | 状态 |
| customerId | Long | 否 | 客户ID |
| orderTime | Date[] | 否 | 下单时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpSaleOrderRespVO>>`

### 查询销售订单详情

- **接口**: `GET /erp/sale-order/get`
- **权限**: `erp:sale-order:query`
- **请求参数**: `id` (Long)
- **响应**: `CommonResult<ErpSaleOrderRespVO>`（含订单项列表）

---

## 销售出库

### 创建销售出库

- **接口**: `POST /erp/sale-out/create`
- **权限**: `erp:sale-out:create`
- **请求参数**: `ErpSaleOutSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | Long | 是 | 关联销售订单ID |
| customerId | Long | 是 | 客户ID |
| warehouseId | Long | 是 | 出库仓库ID |
| outTime | Date | 是 | 出库时间 |
| items | List | 是 | 出库项列表 |

**出库项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| count | BigDecimal | 是 | 出库数量 |
| productPrice | BigDecimal | 是 | 产品单价 |

- **响应**: `CommonResult<Long>` - 出库单编号

**业务逻辑**:
1. 校验销售订单是否存在且已审核
2. 校验出库数量不超过订单剩余可出库数量
3. 自动生成单据号
4. 计算合计数量和价格

### 更新销售出库

- **接口**: `PUT /erp/sale-out/update`
- **权限**: `erp:sale-out:update`

### 删除销售出库

- **接口**: `DELETE /erp/sale-out/delete`
- **权限**: `erp:sale-out:delete`

### 更新销售出库状态

- **接口**: `PUT /erp/sale-out/update-status`
- **权限**: `erp:sale-out:update-status`

**审核逻辑**:
1. 校验出库单存在且状态匹配
2. 遍历出库项，调用 `stockRecordService.createStockRecord()` 扣减库存（负数）
3. 更新销售订单的已出库数量
4. 更新出库单状态

**反审核逻辑**:
1. 调用 `stockRecordService.deleteStockRecord()` 回滚库存
2. 回退销售订单的已出库数量
3. 更新出库单状态

### 查询销售出库分页

- **接口**: `GET /erp/sale-out/page`
- **权限**: `erp:sale-out:query`
- **请求参数**: `ErpSaleOutPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 出库单号（模糊查询） |
| status | Integer | 否 | 状态 |
| customerId | Long | 否 | 客户ID |
| orderId | Long | 否 | 关联销售订单ID |
| warehouseId | Long | 否 | 仓库ID |
| outTime | Date[] | 否 | 出库时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 销售退货

### 创建销售退货

- **接口**: `POST /erp/sale-return/create`
- **权限**: `erp:sale-return:create`
- **请求参数**: `ErpSaleReturnSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | Long | 是 | 关联销售订单ID |
| customerId | Long | 是 | 客户ID |
| warehouseId | Long | 是 | 退货仓库ID |
| returnTime | Date | 是 | 退货时间 |
| items | List | 是 | 退货项列表 |

**退货项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| count | BigDecimal | 是 | 退货数量 |
| productPrice | BigDecimal | 是 | 产品单价 |

- **响应**: `CommonResult<Long>` - 退货单编号

**业务逻辑**:
1. 校验销售订单是否存在且已审核
2. 校验退货数量不超过订单剩余可退货数量
3. 自动生成单据号
4. 计算合计数量和价格

### 更新销售退货

- **接口**: `PUT /erp/sale-return/update`
- **权限**: `erp:sale-return:update`

### 删除销售退货

- **接口**: `DELETE /erp/sale-return/delete`
- **权限**: `erp:sale-return:delete`

### 更新销售退货状态

- **接口**: `PUT /erp/sale-return/update-status`
- **权限**: `erp:sale-return:update-status`

**审核逻辑**:
1. 校验退货单存在且状态匹配
2. 遍历退货项，调用 `stockRecordService.createStockRecord()` 增加库存
3. 更新销售订单的已退货数量
4. 更新退货单状态

**反审核逻辑**:
1. 调用 `stockRecordService.deleteStockRecord()` 回滚库存
2. 回退销售订单的已退货数量
3. 更新退货单状态

### 查询销售退货分页

- **接口**: `GET /erp/sale-return/page`
- **权限**: `erp:sale-return:query`
- **请求参数**: `ErpSaleReturnPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 退货单号（模糊查询） |
| status | Integer | 否 | 状态 |
| customerId | Long | 否 | 客户ID |
| orderId | Long | 否 | 关联销售订单ID |
| warehouseId | Long | 否 | 仓库ID |
| returnTime | Date[] | 否 | 退货时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_030_200_000 | CUSTOMER_NOT_EXISTS | 客户不存在 |
| 1_030_201_000 | SALE_ORDER_NOT_EXISTS | 销售订单不存在 |
| 1_030_201_001 | SALE_ORDER_DELETE_FAIL_APPROVE | 销售订单已审核，无法删除 |
| 1_030_201_003 | SALE_ORDER_APPROVE_FAIL | 审核失败，只有未审核的销售订单才能审核 |
