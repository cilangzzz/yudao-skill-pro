# 采购域 API 文档

## 概述

采购域涵盖供应商管理、采购订单、采购入库、采购退货的完整业务流程。
控制器路径前缀：`/erp/purchase-*`、`/erp/supplier`

## 业务流程

```
采购订单(创建) -> 采购订单(审核) -> 采购入库(创建) -> 采购入库(审核，库存增加)
                                                     -> 采购退货(创建) -> 采购退货(审核，库存减少)
```

关键规则：
- 采购入库/退货必须关联采购订单
- 审核采购入库时，系统自动增加库存并创建库存记录
- 审核采购退货时，系统自动扣减库存并创建库存记录
- 反审核时，系统自动回滚库存变动
- 已审核的单据不可修改/删除，需先反审核

---

## 供应商管理

### 创建供应商

- **接口**: `POST /erp/supplier/create`
- **权限**: `erp:supplier:create`
- **请求参数**: `ErpSupplierSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 供应商名称 |
| contact | String | 否 | 联系人 |
| mobile | String | 否 | 手机号 |
| status | Integer | 否 | 状态 |

- **响应**: `CommonResult<Long>` - 供应商编号

### 更新供应商

- **接口**: `PUT /erp/supplier/update`
- **权限**: `erp:supplier:update`
- **请求参数**: `ErpSupplierSaveReqVO`（含 id）

### 删除供应商

- **接口**: `DELETE /erp/supplier/delete`
- **权限**: `erp:supplier:delete`
- **请求参数**: `id` (Long)

### 查询供应商分页

- **接口**: `GET /erp/supplier/page`
- **权限**: `erp:supplier:query`
- **请求参数**: `ErpSupplierPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 供应商名称（模糊查询） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpSupplierRespVO>>`

---

## 采购订单

### 创建采购订单

- **接口**: `POST /erp/purchase-order/create`
- **权限**: `erp:purchase-order:create`
- **请求参数**: `ErpPurchaseOrderSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplierId | Long | 是 | 供应商ID |
| accountId | Long | 否 | 结算账户ID |
| orderTime | Date | 是 | 下单时间 |
| discountPercent | BigDecimal | 否 | 优惠率(%) |
| items | List | 是 | 订单项列表 |

**订单项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| productUnitId | Long | 否 | 产品单位ID |
| count | BigDecimal | 是 | 数量 |
| productPrice | BigDecimal | 是 | 产品单价 |
| taxPercent | BigDecimal | 否 | 税率(%) |

- **响应**: `CommonResult<Long>` - 采购订单编号

**业务逻辑**:
1. 校验供应商是否存在
2. 校验订单项产品是否存在
3. 自动生成单据号（前缀：CGDD）
4. 计算合计数量、合计价格、税额等
5. 保存主表和子表（使用事务）

### 更新采购订单

- **接口**: `PUT /erp/purchase-order/update`
- **权限**: `erp:purchase-order:update`
- **请求参数**: `ErpPurchaseOrderSaveReqVO`（含 id）

**业务逻辑**:
- 已审核的订单不可更新
- 使用 diffList 差量更新订单项（新增、修改、删除）

### 删除采购订单

- **接口**: `DELETE /erp/purchase-order/delete`
- **权限**: `erp:purchase-order:delete`
- **请求参数**: `ids` (List<Long>)

**业务逻辑**:
- 已审核的订单不可删除
- 检查是否有关联的采购入库单或退货单

### 更新采购订单状态

- **接口**: `PUT /erp/purchase-order/update-status`
- **权限**: `erp:purchase-order:update-status`
- **请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 订单编号 |
| status | Integer | 是 | 目标状态(10未审核 20已审核) |

**状态流转**:
- `PROCESS(10)` -> `APPROVE(20)`: 审核
- `APPROVE(20)` -> `PROCESS(10)`: 反审核（需检查关联的入库/退货单）

### 查询采购订单分页

- **接口**: `GET /erp/purchase-order/page`
- **权限**: `erp:purchase-order:query`
- **请求参数**: `ErpPurchaseOrderPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 订单号（模糊查询） |
| status | Integer | 否 | 状态 |
| supplierId | Long | 否 | 供应商ID |
| orderTime | Date[] | 否 | 下单时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpPurchaseOrderRespVO>>`

### 查询采购订单详情

- **接口**: `GET /erp/purchase-order/get`
- **权限**: `erp:purchase-order:query`
- **请求参数**: `id` (Long)
- **响应**: `CommonResult<ErpPurchaseOrderRespVO>`（含订单项列表）

---

## 采购入库

### 创建采购入库

- **接口**: `POST /erp/purchase-in/create`
- **权限**: `erp:purchase-in:create`
- **请求参数**: `ErpPurchaseInSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | Long | 是 | 关联采购订单ID |
| supplierId | Long | 是 | 供应商ID |
| warehouseId | Long | 是 | 入库仓库ID |
| inTime | Date | 是 | 入库时间 |
| items | List | 是 | 入库项列表 |

**入库项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| count | BigDecimal | 是 | 入库数量 |
| productPrice | BigDecimal | 是 | 产品单价 |

- **响应**: `CommonResult<Long>` - 入库单编号

**业务逻辑**:
1. 校验采购订单是否存在且已审核
2. 校验入库数量不超过订单剩余可入库数量
3. 自动生成单据号
4. 计算合计数量和价格

### 更新采购入库

- **接口**: `PUT /erp/purchase-in/update`
- **权限**: `erp:purchase-in:update`
- **请求参数**: `ErpPurchaseInSaveReqVO`（含 id）

### 删除采购入库

- **接口**: `DELETE /erp/purchase-in/delete`
- **权限**: `erp:purchase-in:delete`
- **请求参数**: `ids` (List<Long>)

### 更新采购入库状态

- **接口**: `PUT /erp/purchase-in/update-status`
- **权限**: `erp:purchase-in:update-status`
- **请求参数**: `id` (Long), `status` (Integer)

**审核逻辑**:
1. 校验入库单存在且状态匹配
2. 遍历入库项，调用 `stockRecordService.createStockRecord()` 增加库存
3. 更新采购订单的已入库数量 (`updatePurchaseOrderInCount`)
4. 更新入库单状态

**反审核逻辑**:
1. 调用 `stockRecordService.deleteStockRecord()` 回滚库存
2. 回退采购订单的已入库数量
3. 更新入库单状态

### 查询采购入库分页

- **接口**: `GET /erp/purchase-in/page`
- **权限**: `erp:purchase-in:query`
- **请求参数**: `ErpPurchaseInPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 入库单号（模糊查询） |
| status | Integer | 否 | 状态 |
| supplierId | Long | 否 | 供应商ID |
| orderId | Long | 否 | 关联采购订单ID |
| warehouseId | Long | 否 | 仓库ID |
| inTime | Date[] | 否 | 入库时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 采购退货

### 创建采购退货

- **接口**: `POST /erp/purchase-return/create`
- **权限**: `erp:purchase-return:create`
- **请求参数**: `ErpPurchaseReturnSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | Long | 是 | 关联采购订单ID |
| supplierId | Long | 是 | 供应商ID |
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
1. 校验采购订单是否存在且已审核
2. 校验退货数量不超过订单剩余可退货数量
3. 自动生成单据号
4. 计算合计数量和价格

### 更新采购退货

- **接口**: `PUT /erp/purchase-return/update`
- **权限**: `erp:purchase-return:update`

### 删除采购退货

- **接口**: `DELETE /erp/purchase-return/delete`
- **权限**: `erp:purchase-return:delete`

### 更新采购退货状态

- **接口**: `PUT /erp/purchase-return/update-status`
- **权限**: `erp:purchase-return:update-status`

**审核逻辑**:
1. 校验退货单存在且状态匹配
2. 遍历退货项，调用 `stockRecordService.createStockRecord()` 扣减库存（负数）
3. 更新采购订单的已退货数量 (`updatePurchaseOrderReturnCount`)
4. 更新退货单状态

**反审核逻辑**:
1. 调用 `stockRecordService.deleteStockRecord()` 回滚库存
2. 回退采购订单的已退货数量
3. 更新退货单状态

### 查询采购退货分页

- **接口**: `GET /erp/purchase-return/page`
- **权限**: `erp:purchase-return:query`
- **请求参数**: `ErpPurchaseReturnPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 退货单号（模糊查询） |
| status | Integer | 否 | 状态 |
| supplierId | Long | 否 | 供应商ID |
| orderId | Long | 否 | 关联采购订单ID |
| warehouseId | Long | 否 | 仓库ID |
| returnTime | Date[] | 否 | 退货时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_030_100_000 | SUPPLIER_NOT_EXISTS | 供应商不存在 |
| 1_030_101_000 | PURCHASE_ORDER_NOT_EXISTS | 采购订单不存在 |
| 1_030_101_001 | PURCHASE_ORDER_DELETE_FAIL_APPROVE | 采购订单已审核，无法删除 |
| 1_030_101_003 | PURCHASE_ORDER_APPROVE_FAIL | 审核失败，只有未审核的采购订单才能审核 |
