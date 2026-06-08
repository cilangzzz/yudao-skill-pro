# 仓库管理 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 仓库管理（Warehouse）

**Controller**: `MesWarehouseController`
**路径前缀**: `/admin-api/mes/warehouse`
**权限前缀**: `mes:warehouse:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建仓库 | `mes:warehouse:create` |
| PUT | `/update` | 更新仓库 | `mes:warehouse:update` |
| DELETE | `/delete` | 删除仓库 | `mes:warehouse:delete` |
| GET | `/get` | 获取仓库详情 | `mes:warehouse:query` |
| GET | `/page` | 仓库分页查询 | `mes:warehouse:query` |
| GET | `/list-all` | 获取所有仓库 | `mes:warehouse:query` |

---

## 2. 库区管理（WarehouseArea）

**Controller**: `MesWarehouseAreaController`
**路径前缀**: `/admin-api/mes/warehouse-area`
**权限前缀**: `mes:warehouse-area:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建库区 | `mes:warehouse-area:create` |
| PUT | `/update` | 更新库区 | `mes:warehouse-area:update` |
| DELETE | `/delete` | 删除库区 | `mes:warehouse-area:delete` |
| GET | `/get` | 获取库区详情 | `mes:warehouse-area:query` |
| GET | `/page` | 库区分页查询 | `mes:warehouse-area:query` |

---

## 3. 库位管理（WarehouseLocation）

**Controller**: `MesWarehouseLocationController`
**路径前缀**: `/admin-api/mes/warehouse-location`
**权限前缀**: `mes:warehouse-location:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建库位 | `mes:warehouse-location:create` |
| PUT | `/update` | 更新库位 | `mes:warehouse-location:update` |
| DELETE | `/delete` | 删除库位 | `mes:warehouse-location:delete` |
| GET | `/get` | 获取库位详情 | `mes:warehouse-location:query` |
| GET | `/page` | 库位分页查询 | `mes:warehouse-location:query` |

### 仓库层级结构

```
仓库 (Warehouse)
  └── 库区 (WarehouseArea)
        └── 库位 (WarehouseLocation)
```

---

## 4. 物料库存（MaterialStock）

**Controller**: `MesMaterialStockController`
**路径前缀**: `/admin-api/mes/material-stock`
**权限前缀**: `mes:material-stock:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 物料库存分页查询 | `mes:material-stock:query` |
| GET | `/get` | 获取库存详情 | `mes:material-stock:query` |
| GET | `/list-by-item` | 按物料查询库存汇总 | `mes:material-stock:query` |

### 库存维度

物料库存按以下维度管理：
- 物料编号（itemId）
- 仓库编号（warehouseId）
- 库位编号（locationId）
- 批次号（batchId）

---

## 5. 批次管理（Batch）

**Controller**: `MesBatchController`
**路径前缀**: `/admin-api/mes/batch`
**权限前缀**: `mes:batch:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建批次 | `mes:batch:create` |
| GET | `/get` | 获取批次详情 | `mes:batch:query` |
| GET | `/page` | 批次分页查询 | `mes:batch:query` |

---

## 6. 条码管理（Barcode）

**Controller**: `MesBarcodeController`
**路径前缀**: `/admin-api/mes/barcode`
**权限前缀**: `mes:barcode:*`

### 6.1 条码管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 生成条码 | `mes:barcode:create` |
| GET | `/get` | 获取条码详情 | `mes:barcode:query` |
| GET | `/page` | 条码分页查询 | `mes:barcode:query` |
| POST | `/scan` | 扫码查询 | `mes:barcode:query` |

### 6.2 条码配置

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/config/create` | 创建条码配置 | `mes:barcode:create` |
| PUT | `/config/update` | 更新条码配置 | `mes:barcode:update` |
| GET | `/config/get` | 获取配置详情 | `mes:barcode:query` |

### 6.3 SN 序列号

`mes_wm_sn` 表管理产品的序列号（Serial Number），支持单件追溯。

---

## 7. 到货通知（ArrivalNotice）

**Controller**: `MesArrivalNoticeController`
**路径前缀**: `/admin-api/mes/arrival-notice`
**权限前缀**: `mes:arrival-notice:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建到货通知 | `mes:arrival-notice:create` |
| PUT | `/update` | 更新到货通知 | `mes:arrival-notice:update` |
| DELETE | `/delete` | 删除到货通知 | `mes:arrival-notice:delete` |
| GET | `/get` | 获取通知详情（含明细行） | `mes:arrival-notice:query` |
| GET | `/page` | 通知分页查询 | `mes:arrival-notice:query` |

### 结构

| 层级 | 表 | 说明 |
|------|---|------|
| 通知主表 | `mes_wm_arrival_notice` | 供应商、到货日期、状态 |
| 明细行 | `mes_wm_arrival_notice_line` | 物料、数量、批次 |

---

## 8. 采购入库（ItemReceipt）

**Controller**: `MesItemReceiptController`
**路径前缀**: `/admin-api/mes/item-receipt`
**权限前缀**: `mes:item-receipt:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建采购入库单 | `mes:item-receipt:create` |
| PUT | `/update` | 更新入库单 | `mes:item-receipt:update` |
| DELETE | `/delete` | 删除入库单 | `mes:item-receipt:delete` |
| GET | `/get` | 获取入库单详情（含明细/明细详情） | `mes:item-receipt:query` |
| GET | `/page` | 入库单分页查询 | `mes:item-receipt:query` |

### 结构

| 层级 | 表 | 说明 |
|------|---|------|
| 入库单主表 | `mes_wm_item_receipt` | 供应商、仓库、入库日期 |
| 入库明细 | `mes_wm_item_receipt_line` | 物料、数量 |
| 入库详情 | `mes_wm_item_receipt_detail` | 批次、库位、条码等详细信息 |

---

## 9. 产品入库（ProductReceipt）

**Controller**: `MesProductReceiptController`
**路径前缀**: `/admin-api/mes/product-receipt`
**权限前缀**: `mes:product-receipt:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建产品入库单 | `mes:product-receipt:create` |
| PUT | `/update` | 更新入库单 | `mes:product-receipt:update` |
| DELETE | `/delete` | 删除入库单 | `mes:product-receipt:delete` |
| GET | `/get` | 获取入库单详情 | `mes:product-receipt:query` |
| GET | `/page` | 入库单分页查询 | `mes:product-receipt:query` |

> 产品入库用于生产完工后，将成品从车间入库到成品仓库。

---

## 10. 生产领料（ProductIssue）

**Controller**: `MesProductIssueController`
**路径前缀**: `/admin-api/mes/product-issue`
**权限前缀**: `mes:product-issue:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建领料单 | `mes:product-issue:create` |
| PUT | `/update` | 更新领料单 | `mes:product-issue:update` |
| DELETE | `/delete` | 删除领料单 | `mes:product-issue:delete` |
| GET | `/get` | 获取领料单详情 | `mes:product-issue:query` |
| GET | `/page` | 领料单分页查询 | `mes:product-issue:query` |

> 生产领料根据工单 BOM 从仓库领取原材料到车间。

---

## 11. 生产退料（ReturnIssue）

**Controller**: `MesReturnIssueController`
**路径前缀**: `/admin-api/mes/return-issue`
**权限前缀**: `mes:return-issue:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建退料单 | `mes:return-issue:create` |
| PUT | `/update` | 更新退料单 | `mes:return-issue:update` |
| DELETE | `/delete` | 删除退料单 | `mes:return-issue:delete` |
| GET | `/get` | 获取退料单详情 | `mes:return-issue:query` |
| GET | `/page` | 退料单分页查询 | `mes:return-issue:query` |

---

## 12. 其他出库（MiscIssue）

**Controller**: `MesMiscIssueController`
**路径前缀**: `/admin-api/mes/misc-issue`
**权限前缀**: `mes:misc-issue:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建其他出库单 | `mes:misc-issue:create` |
| PUT | `/update` | 更新出库单 | `mes:misc-issue:update` |
| DELETE | `/delete` | 删除出库单 | `mes:misc-issue:delete` |
| GET | `/get` | 获取出库单详情 | `mes:misc-issue:query` |
| GET | `/page` | 出库单分页查询 | `mes:misc-issue:query` |

> 其他出库用于非生产性的物料出库，如维修用料、样品出库、报废等。

---

## 13. 其他入库（MiscReceipt）

**Controller**: `MesMiscReceiptController`
**路径前缀**: `/admin-api/mes/misc-receipt`
**权限前缀**: `mes:misc-receipt:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建其他入库单 | `mes:misc-receipt:create` |
| PUT | `/update` | 更新入库单 | `mes:misc-receipt:update` |
| DELETE | `/delete` | 删除入库单 | `mes:misc-receipt:delete` |
| GET | `/get` | 获取入库单详情 | `mes:misc-receipt:query` |
| GET | `/page` | 入库单分页查询 | `mes:misc-receipt:query` |

---

## 14. 销售出库（ProductSales）

**Controller**: `MesProductSalesController`
**路径前缀**: `/admin-api/mes/product-sales`
**权限前缀**: `mes:product-sales:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建销售出库单 | `mes:product-sales:create` |
| PUT | `/update` | 更新出库单 | `mes:product-sales:update` |
| DELETE | `/delete` | 删除出库单 | `mes:product-sales:delete` |
| GET | `/get` | 获取出库单详情 | `mes:product-sales:query` |
| GET | `/page` | 出库单分页查询 | `mes:product-sales:query` |

---

## 15. 销售退货（ReturnSales）

**Controller**: `MesReturnSalesController`
**路径前缀**: `/admin-api/mes/return-sales`
**权限前缀**: `mes:return-sales:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建销售退货单 | `mes:return-sales:create` |
| PUT | `/update` | 更新退货单 | `mes:return-sales:update` |
| DELETE | `/delete` | 删除退货单 | `mes:return-sales:delete` |
| GET | `/get` | 获取退货单详情 | `mes:return-sales:query` |
| GET | `/page` | 退货单分页查询 | `mes:return-sales:query` |

---

## 16. 委外发料（OutsourceIssue）

**Controller**: `MesOutsourceIssueController`
**路径前缀**: `/admin-api/mes/outsource-issue`
**权限前缀**: `mes:outsource-issue:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建委外发料单 | `mes:outsource-issue:create` |
| PUT | `/update` | 更新发料单 | `mes:outsource-issue:update` |
| DELETE | `/delete` | 删除发料单 | `mes:outsource-issue:delete` |
| GET | `/get` | 获取发料单详情 | `mes:outsource-issue:query` |
| GET | `/page` | 发料单分页查询 | `mes:outsource-issue:query` |

---

## 17. 委外收料（OutsourceReceipt）

**Controller**: `MesOutsourceReceiptController`
**路径前缀**: `/admin-api/mes/outsource-receipt`
**权限前缀**: `mes:outsource-receipt:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建委外收料单 | `mes:outsource-receipt:create` |
| PUT | `/update` | 更新收料单 | `mes:outsource-receipt:update` |
| DELETE | `/delete` | 删除收料单 | `mes:outsource-receipt:delete` |
| GET | `/get` | 获取收料单详情 | `mes:outsource-receipt:query` |
| GET | `/page` | 收料单分页查询 | `mes:outsource-receipt:query` |

---

## 18. 供应商退货（ReturnVendor）

**Controller**: `MesReturnVendorController`
**路径前缀**: `/admin-api/mes/return-vendor`
**权限前缀**: `mes:return-vendor:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建供应商退货单 | `mes:return-vendor:create` |
| PUT | `/update` | 更新退货单 | `mes:return-vendor:update` |
| DELETE | `/delete` | 删除退货单 | `mes:return-vendor:delete` |
| GET | `/get` | 获取退货单详情 | `mes:return-vendor:query` |
| GET | `/page` | 退货单分页查询 | `mes:return-vendor:query` |

> 供应商退货用于 IQC 检验不合格的来料退回供应商。

---

## 19. 库存调拨（Transfer）

**Controller**: `MesTransferController`
**路径前缀**: `/admin-api/mes/transfer`
**权限前缀**: `mes:transfer:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建调拨单 | `mes:transfer:create` |
| PUT | `/update` | 更新调拨单 | `mes:transfer:update` |
| DELETE | `/delete` | 删除调拨单 | `mes:transfer:delete` |
| GET | `/get` | 获取调拨单详情 | `mes:transfer:query` |
| GET | `/page` | 调拨单分页查询 | `mes:transfer:query` |
| POST | `/submit` | 提交调拨单 | `mes:transfer:update` |
| POST | `/confirm` | 确认调拨 | `mes:transfer:update` |

### 调拨状态

| 值 | 说明 |
|----|------|
| 0 | 草稿 |
| 1 | 待确认 |
| 2 | 已完成 |

---

## 20. 包装管理（Package）

**Controller**: `MesPackageController`
**路径前缀**: `/admin-api/mes/package`
**权限前缀**: `mes:package:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建包装单 | `mes:package:create` |
| PUT | `/update` | 更新包装单 | `mes:package:update` |
| DELETE | `/delete` | 删除包装单 | `mes:package:delete` |
| GET | `/get` | 获取包装单详情（含包装行） | `mes:package:query` |
| GET | `/page` | 包装单分页查询 | `mes:package:query` |

### 结构

| 层级 | 表 | 说明 |
|------|---|------|
| 包装单主表 | `mes_wm_package` | 包装单号、客户、状态 |
| 包装行 | `mes_wm_package_line` | 物料、数量、箱号 |

---

## 21. 盘点管理（StockTaking）

**Controller**: `MesStockTakingController`
**路径前缀**: `/admin-api/mes/stock-taking`
**权限前缀**: `mes:stock-taking:*`

### 21.1 盘点计划

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/plan/create` | 创建盘点计划 | `mes:stock-taking:create` |
| PUT | `/plan/update` | 更新盘点计划 | `mes:stock-taking:update` |
| DELETE | `/plan/delete` | 删除盘点计划 | `mes:stock-taking:delete` |
| GET | `/plan/get` | 获取计划详情 | `mes:stock-taking:query` |
| GET | `/plan/page` | 计划分页查询 | `mes:stock-taking:query` |

### 21.2 盘点任务

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/task/page` | 盘点任务分页查询 | `mes:stock-taking:query` |
| POST | `/task/result/submit` | 提交盘点结果 | `mes:stock-taking:update` |

### 21.3 盘点结果

`mes_wm_stock_taking_task_result` 记录每个库位/物料的盘点结果（账面数量、实盘数量、差异）。

### 21.4 盘点流程

```
1. 创建盘点计划 -> 指定盘点范围（仓库/库区/物料）
2. 生成盘点任务 -> 按库位分配盘点任务
3. 执行盘点 -> 录入实盘数量
4. 提交盘点结果 -> 系统计算差异
5. 审核盘点结果 -> 确认差异调整库存
```

---

## 22. 物料消耗（ItemConsume）

**Controller**: `MesItemConsumeController`
**路径前缀**: `/admin-api/mes/item-consume`
**权限前缀**: `mes:item-consume:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 物料消耗分页查询 | `mes:item-consume:query` |

> 记录生产过程中的物料实际消耗，用于与 BOM 标准用量对比分析。

---

## 23. 产品产出（ProductProduce）

**Controller**: `MesProductProduceController`
**路径前缀**: `/admin-api/mes/product-produce`
**权限前缀**: `mes:product-produce:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 产品产出分页查询 | `mes:product-produce:query` |

> 记录生产过程中的产品实际产出数量。

---

## 24. 销售通知（SalesNotice）

**Controller**: `MesSalesNoticeController`
**路径前缀**: `/admin-api/mes/sales-notice`
**权限前缀**: `mes:sales-notice:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建销售通知 | `mes:sales-notice:create` |
| PUT | `/update` | 更新销售通知 | `mes:sales-notice:update` |
| DELETE | `/delete` | 删除销售通知 | `mes:sales-notice:delete` |
| GET | `/get` | 获取通知详情 | `mes:sales-notice:query` |
| GET | `/page` | 通知分页查询 | `mes:sales-notice:query` |

---

## 核心设计要点

### 出入库单据通用结构

所有出入库单据遵循主子表结构：
- **主表**: 单据基本信息（单号、仓库、日期、来源单号）
- **明细行（Line）**: 物料、数量
- **明细详情（Detail）**: 批次、库位、条码等（部分单据有此层）

### 库存更新规则

所有出入库操作统一通过 `MaterialStockService` 更新库存：
- 入库操作：增加库存记录
- 出库操作：扣减库存记录
- 调拨操作：扣减源库位 + 增加目标库位
- 盘点调整：按差异调整库存

### 条码追溯

通过条码和 SN 实现全流程追溯：
- 物料入库时生成/打印条码
- 生产过程中扫码领料、报工
- 成品出库时关联 SN 序列号
- 可通过条码/SN 反向追溯到供应商、批次、生产工单

### 与质量联动

仓库操作触发质量检验：
- 采购入库前 -> IQC 检验
- 生产完工后 -> IPQC 检验
- 销售出库前 -> OQC 检验
- 退货入库 -> RQC 检验
