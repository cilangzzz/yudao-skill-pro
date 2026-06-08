# 库存域 API 文档

## 概述

库存域涵盖库存查询、其它入库、其它出库、库存调拨、库存盘点、仓库管理。
控制器路径前缀：`/erp/stock*`、`/erp/warehouse`

## 库存核心机制

### 库存增量更新

库存变动统一通过 `ErpStockMapper.updateCountIncrement()` 实现，使用 SQL 级别的增量更新避免并发问题。

```java
// 入库：count 为正数
// 出库：count 为负数
updateCountIncrement(Long id, BigDecimal count, Boolean negativeEnable)
```

### 库存记录

每次库存变动都会创建一条 `ErpStockRecordDO` 记录，包含：
- 产品ID、仓库ID
- 变动数量（正数入库，负数出库）
- 变动后库存量
- 业务类型、业务编号、业务单号

### 业务类型枚举 (ErpStockRecordBizTypeEnum)

| 类型 | 编码 | 说明 |
|------|------|------|
| PURCHASE_IN | 10 | 采购入库 |
| PURCHASE_IN_CANCEL | 11 | 采购入库（作废） |
| PURCHASE_RETURN | 12 | 采购退货 |
| PURCHASE_RETURN_CANCEL | 13 | 采购退货（作废） |
| SALE_OUT | 20 | 销售出库 |
| SALE_OUT_CANCEL | 21 | 销售出库（作废） |
| SALE_RETURN | 22 | 销售退货 |
| SALE_RETURN_CANCEL | 23 | 销售退货（作废） |
| STOCK_IN | 30 | 其它入库 |
| STOCK_IN_CANCEL | 31 | 其它入库（作废） |
| STOCK_OUT | 32 | 其它出库 |
| STOCK_OUT_CANCEL | 33 | 其它出库（作废） |
| STOCK_MOVE | 34 | 库存调拨 |
| STOCK_MOVE_CANCEL | 35 | 库存调拨（作废） |

---

## 库存查询

### 查询库存分页

- **接口**: `GET /erp/stock/page`
- **权限**: `erp:stock:query`
- **请求参数**: `ErpStockPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 否 | 产品ID |
| warehouseId | Long | 否 | 仓库ID |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpStockRespVO>>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 库存编号 |
| productId | Long | 产品ID |
| productName | String | 产品名称 |
| warehouseId | Long | 仓库ID |
| warehouseName | String | 仓库名称 |
| count | BigDecimal | 库存数量 |

---

## 其它入库

### 创建其它入库

- **接口**: `POST /erp/stock-in/create`
- **权限**: `erp:stock-in:create`
- **请求参数**: `ErpStockInSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
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
1. 自动生成单据号（前缀：QTRK）
2. 计算合计数量和价格
3. 保存主表和子表

### 更新其它入库

- **接口**: `PUT /erp/stock-in/update`
- **权限**: `erp:stock-in:update`
- **请求参数**: `ErpStockInSaveReqVO`（含 id）

### 删除其它入库

- **接口**: `DELETE /erp/stock-in/delete`
- **权限**: `erp:stock-in:delete`
- **请求参数**: `ids` (List<Long>)

### 更新其它入库状态

- **接口**: `PUT /erp/stock-in/update-status`
- **权限**: `erp:stock-in:update-status`
- **请求参数**: `id` (Long), `status` (Integer)

**审核逻辑**:
1. 校验入库单存在且状态匹配
2. 遍历入库项，调用 `stockRecordService.createStockRecord()` 增加库存
3. 更新入库单状态

**反审核逻辑**:
1. 调用 `stockRecordService.deleteStockRecord()` 回滚库存
2. 更新入库单状态

### 查询其它入库分页

- **接口**: `GET /erp/stock-in/page`
- **权限**: `erp:stock-in:query`
- **请求参数**: `ErpStockInPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 入库单号（模糊查询） |
| status | Integer | 否 | 状态 |
| warehouseId | Long | 否 | 仓库ID |
| inTime | Date[] | 否 | 入库时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 其它出库

### 创建其它出库

- **接口**: `POST /erp/stock-out/create`
- **权限**: `erp:stock-out:create`
- **请求参数**: `ErpStockOutSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
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
1. 自动生成单据号（前缀：QCKD）
2. 校验库存充足（如果配置不允许负库存）
3. 计算合计数量和价格
4. 保存主表和子表

### 更新其它出库

- **接口**: `PUT /erp/stock-out/update`
- **权限**: `erp:stock-out:update`

### 删除其它出库

- **接口**: `DELETE /erp/stock-out/delete`
- **权限**: `erp:stock-out:delete`

### 更新其它出库状态

- **接口**: `PUT /erp/stock-out/update-status`
- **权限**: `erp:stock-out:update-status`

**审核逻辑**:
1. 校验出库单存在且状态匹配
2. 遍历出库项，调用 `stockRecordService.createStockRecord()` 扣减库存（负数）
3. 更新出库单状态

**反审核逻辑**:
1. 调用 `stockRecordService.deleteStockRecord()` 回滚库存
2. 更新出库单状态

### 查询其它出库分页

- **接口**: `GET /erp/stock-out/page`
- **权限**: `erp:stock-out:query`
- **请求参数**: `ErpStockOutPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 出库单号（模糊查询） |
| status | Integer | 否 | 状态 |
| warehouseId | Long | 否 | 仓库ID |
| outTime | Date[] | 否 | 出库时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 库存调拨

### 创建库存调拨

- **接口**: `POST /erp/stock-move/create`
- **权限**: `erp:stock-move:create`
- **请求参数**: `ErpStockMoveSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fromWarehouseId | Long | 是 | 调出仓库ID |
| toWarehouseId | Long | 是 | 调入仓库ID |
| moveTime | Date | 是 | 调拨时间 |
| items | List | 是 | 调拨项列表 |

**调拨项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| count | BigDecimal | 是 | 调拨数量 |

- **响应**: `CommonResult<Long>` - 调拨单编号

**业务逻辑**:
1. 自动生成单据号（前缀：QCDB）
2. 校验调出仓库和调入仓库不同
3. 计算合计数量
4. 保存主表和子表

### 更新库存调拨

- **接口**: `PUT /erp/stock-move/update`
- **权限**: `erp:stock-move:update`

### 删除库存调拨

- **接口**: `DELETE /erp/stock-move/delete`
- **权限**: `erp:stock-move:delete`

### 更新库存调拨状态

- **接口**: `PUT /erp/stock-move/update-status`
- **权限**: `erp:stock-move:update-status`

**审核逻辑**:
1. 校验调拨单存在且状态匹配
2. 遍历调拨项：
   - 调出仓库扣减库存（负数）
   - 调入仓库增加库存（正数）
3. 更新调拨单状态

**反审核逻辑**:
1. 回滚调出仓库库存（增加）
2. 回滚调入仓库库存（减少）
3. 更新调拨单状态

### 查询库存调拨分页

- **接口**: `GET /erp/stock-move/page`
- **权限**: `erp:stock-move:query`
- **请求参数**: `ErpStockMovePageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 调拨单号（模糊查询） |
| status | Integer | 否 | 状态 |
| fromWarehouseId | Long | 否 | 调出仓库ID |
| toWarehouseId | Long | 否 | 调入仓库ID |
| moveTime | Date[] | 否 | 调拨时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 库存盘点

### 创建库存盘点

- **接口**: `POST /erp/stock-check/create`
- **权限**: `erp:stock-check:create`
- **请求参数**: `ErpStockCheckSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| warehouseId | Long | 是 | 盘点仓库ID |
| checkTime | Date | 是 | 盘点时间 |
| items | List | 是 | 盘点项列表 |

**盘点项字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | Long | 是 | 产品ID |
| count | BigDecimal | 是 | 盘点数量 |

- **响应**: `CommonResult<Long>` - 盘点单编号

**业务逻辑**:
1. 自动生成单据号（前缀：QCPD）
2. 计算合计数量
3. 保存主表和子表

### 更新库存盘点

- **接口**: `PUT /erp/stock-check/update`
- **权限**: `erp:stock-check:update`

### 删除库存盘点

- **接口**: `DELETE /erp/stock-check/delete`
- **权限**: `erp:stock-check:delete`

### 更新库存盘点状态

- **接口**: `PUT /erp/stock-check/update-status`
- **权限**: `erp:stock-check:update-status`

### 查询库存盘点分页

- **接口**: `GET /erp/stock-check/page`
- **权限**: `erp:stock-check:query`
- **请求参数**: `ErpStockCheckPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 盘点单号（模糊查询） |
| status | Integer | 否 | 状态 |
| warehouseId | Long | 否 | 仓库ID |
| checkTime | Date[] | 否 | 盘点时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 仓库管理

### 创建仓库

- **接口**: `POST /erp/warehouse/create`
- **权限**: `erp:warehouse:create`
- **请求参数**: `ErpWarehouseSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 仓库名称 |
| address | String | 否 | 仓库地址 |
| status | Integer | 否 | 状态 |

- **响应**: `CommonResult<Long>` - 仓库编号

### 更新仓库

- **接口**: `PUT /erp/warehouse/update`
- **权限**: `erp:warehouse:update`

### 删除仓库

- **接口**: `DELETE /erp/warehouse/delete`
- **权限**: `erp:warehouse:delete`

### 查询仓库分页

- **接口**: `GET /erp/warehouse/page`
- **权限**: `erp:warehouse:query`
- **请求参数**: `ErpWarehousePageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 仓库名称（模糊查询） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

---

## 错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_030_400_000 | WAREHOUSE_NOT_EXISTS | 仓库不存在 |
| 1_030_404_000 | STOCK_COUNT_NEGATIVE | 操作失败，产品所在仓库的库存不足 |
| 1_030_401_000 | STOCK_IN_NOT_EXISTS | 其它入库单不存在 |
| 1_030_402_000 | STOCK_OUT_NOT_EXISTS | 其它出库单不存在 |
| 1_030_403_000 | STOCK_MOVE_NOT_EXISTS | 库存调拨单不存在 |
| 1_030_405_000 | STOCK_CHECK_NOT_EXISTS | 库存盘点单不存在 |
