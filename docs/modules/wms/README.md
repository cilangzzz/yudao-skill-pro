# 仓库管理模块 (wms)

> 面向仓储场景的轻量级 WMS（Warehouse Management System）：仓库/商品等主数据维护，入库、出库、移库、盘库四类单据驱动库存余额与库存流水变化，并提供首页统计看板。

## 模块概述

- **模块路径**: yudao-module-wms
- **业务定位**: 提供仓库管理的基础主数据（仓库、商品/SKU、分类、品牌、往来企业）与核心作业单据（入库单、出库单、移库单、盘库单）。四类单据遵循统一的「草稿 → 完成 / 作废」状态机，完成时通过统一的库存变更入口（`WmsInventoryService.changeInventory / checkInventory`）更新库存余额并记录库存流水，保证库存可追溯。同时提供库存统计、库存流水分页查询与首页汇总/趋势/排行榜统计接口。
- **技术栈**: Spring Boot 2.7.18（JDK 8）+ MyBatis-Plus（yudao-spring-boot-starter-mybatis）+ Spring Security 权限 + Redis（yudao-spring-boot-starter-redis）+ EasyExcel 导出（yudao-spring-boot-starter-excel）；Swagger 分组 `wms` 由 `WmsWebConfiguration` 注册

## 设计原则

| 原则 | 说明 |
|-----|------|
| 单据驱动库存 | 库存余额（wms_inventory）不允许直接修改，只能由四类单据「完成」动作触发的 changeInventory/checkInventory 统一变更，并强制写入库存流水 |
| 单据状态机 | 所有单据只有三个状态：草稿(0)、已完成(4)、已作废(5)；仅草稿可编辑/删除/完成/作废，完成与作废前均做状态前置校验 |
| 并发安全优先 | 库存变更统一按库存行 ID 加 `SELECT ... FOR UPDATE` 悲观锁后再计算；新建库存行依赖 (sku_id, warehouse_id) 唯一索引，冲突时回查兜底 |
| 明细整体维护 | 单据与明细（order + order_detail 两张表）同事务保存：单据更新时明细整单删除重建，删除单据时级联删除明细 |
| 只读统计分离 | 库存/流水/首页统计仅提供查询接口，不提供写接口；VO 拼接（SKU、商品、仓库名称等）统一在 Controller 私有 build 方法内完成 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 主数据-仓库 | 仓库的增删改查、精简下拉、Excel 导出；删除前校验未被单据/库存使用 | WmsWarehouseDO |
| 主数据-商品 | 商品 + SKU 一体化维护（商品弹窗内维护 SKU），分类为树形结构，品牌独立维护；SKU 维度提供分页查询（选择器场景） | WmsItemDO、WmsItemSkuDO、WmsItemCategoryDO、WmsItemBrandDO |
| 主数据-往来企业 | 客户/供应商（或两者兼具）档案维护；入库单校验供应商类型、出库单校验客户类型 | WmsMerchantDO |
| 入库单 | 生产/采购/退货/归还四类入库，草稿可改，完成时按明细增加库存并写流水 | WmsReceiptOrderDO、WmsReceiptOrderDetailDO |
| 出库单 | 退货/销售/生产三类出库，完成时校验并扣减库存，库存不足报错 | WmsShipmentOrderDO、WmsShipmentOrderDetailDO |
| 移库单 | 同一 SKU 在来源仓库扣减、目标仓库增加；校验来源与目标仓库不能相同 | WmsMovementOrderDO、WmsMovementOrderDetailDO |
| 盘库单 | 按仓库生成账面库存快照，完成时逐行复核（账面数量或库存已变化则报错），按实盘数量调整库存 | WmsCheckOrderDO、WmsCheckOrderDetailDO |
| 库存统计 | 库存余额分页/列表查询（SKU 维度），以及含单价、前后数量的库存流水分页 | WmsInventoryDO、WmsInventoryHistoryDO |
| 首页统计 | 单据汇总（按类型/状态计数）、近 N 天单据趋势、库存总量与商品/仓库维度库存排行 | 复用上述 DO（Mapper 聚合查询） |

## API 接口索引

### 首页统计 (WmsHomeStatisticsController)

基础路径：`/wms/home-statistics`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/home-statistics/order-summary | GET | 获得首页单据汇总统计 | wms:home:query |
| /wms/home-statistics/order-trend | GET | 获得首页单据趋势 | wms:home:query |
| /wms/home-statistics/inventory-summary | GET | 获得首页库存汇总统计 | wms:home:query |

### 库存统计 (WmsInventoryController)

基础路径：`/wms/inventory`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/inventory/page | GET | 获得库存统计分页 | wms:inventory:query |
| /wms/inventory/list | GET | 获得库存统计列表 | wms:inventory:query |

### 库存流水 (WmsInventoryHistoryController)

基础路径：`/wms/inventory-history`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/inventory-history/page | GET | 获得库存流水分页 | wms:inventory-history:query |

### 商品 (WmsItemController)

基础路径：`/wms/item`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/item/create | POST | 创建商品 | wms:item:create |
| /wms/item/update | PUT | 更新商品 | wms:item:update |
| /wms/item/delete | DELETE | 删除商品 | wms:item:delete |
| /wms/item/get | GET | 获得商品 | wms:item:query |
| /wms/item/page | GET | 获得商品分页 | wms:item:query |
| /wms/item/simple-list | GET | 获得商品精简列表 | wms:item:query |
| /wms/item/export-excel | GET | 导出商品 Excel | wms:item:export |

### 商品 SKU (WmsItemSkuController)

基础路径：`/wms/item-sku`（仅查询入口，SKU 的新增/修改/删除随商品接口一并维护；复用商品权限）

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/item-sku/page | GET | 获得商品 SKU 分页（支持商品/品牌/分类联查筛选） | wms:item:query |

### 商品分类 (WmsItemCategoryController)

基础路径：`/wms/item-category`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/item-category/create | POST | 创建商品分类 | wms:item-category:create |
| /wms/item-category/update | PUT | 更新商品分类 | wms:item-category:update |
| /wms/item-category/delete | DELETE | 删除商品分类 | wms:item-category:delete |
| /wms/item-category/get | GET | 获得商品分类 | wms:item-category:query |
| /wms/item-category/list | GET | 获得商品分类列表 | wms:item-category:query |
| /wms/item-category/simple-list | GET | 获得商品分类精简列表（前端下拉） | wms:item-category:query |

### 商品品牌 (WmsItemBrandController)

基础路径：`/wms/item-brand`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/item-brand/create | POST | 创建商品品牌 | wms:item-brand:create |
| /wms/item-brand/update | PUT | 更新商品品牌 | wms:item-brand:update |
| /wms/item-brand/delete | DELETE | 删除商品品牌 | wms:item-brand:delete |
| /wms/item-brand/get | GET | 获得商品品牌 | wms:item-brand:query |
| /wms/item-brand/page | GET | 获得商品品牌分页 | wms:item-brand:query |
| /wms/item-brand/simple-list | GET | 获得商品品牌精简列表（前端下拉） | wms:item-brand:query |
| /wms/item-brand/export-excel | GET | 导出商品品牌 Excel | wms:item-brand:export |

### 往来企业 (WmsMerchantController)

基础路径：`/wms/merchant`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/merchant/create | POST | 创建往来企业 | wms:merchant:create |
| /wms/merchant/update | PUT | 更新往来企业 | wms:merchant:update |
| /wms/merchant/delete | DELETE | 删除往来企业 | wms:merchant:delete |
| /wms/merchant/get | GET | 获得往来企业 | wms:merchant:query |
| /wms/merchant/page | GET | 获得往来企业分页 | wms:merchant:query |
| /wms/merchant/simple-list | GET | 获得往来企业精简列表（前端下拉） | wms:merchant:query |
| /wms/merchant/export-excel | GET | 导出往来企业 Excel | wms:merchant:export |

### 仓库 (WmsWarehouseController)

基础路径：`/wms/warehouse`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/warehouse/create | POST | 创建仓库 | wms:warehouse:create |
| /wms/warehouse/update | PUT | 更新仓库 | wms:warehouse:update |
| /wms/warehouse/delete | DELETE | 删除仓库 | wms:warehouse:delete |
| /wms/warehouse/get | GET | 获得仓库 | wms:warehouse:query |
| /wms/warehouse/page | GET | 获得仓库分页 | wms:warehouse:query |
| /wms/warehouse/simple-list | GET | 获得仓库精简列表（前端下拉） | wms:warehouse:query |
| /wms/warehouse/export-excel | GET | 导出仓库 Excel | wms:warehouse:export |

### 入库单 (WmsReceiptOrderController)

基础路径：`/wms/receipt-order`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/receipt-order/create | POST | 创建入库单 | wms:receipt-order:create |
| /wms/receipt-order/update | PUT | 更新入库单 | wms:receipt-order:update |
| /wms/receipt-order/delete | DELETE | 删除入库单 | wms:receipt-order:delete |
| /wms/receipt-order/complete | PUT | 完成入库 | wms:receipt-order:complete |
| /wms/receipt-order/cancel | PUT | 作废入库单 | wms:receipt-order:cancel |
| /wms/receipt-order/get | GET | 获得入库单（含明细） | wms:receipt-order:query |
| /wms/receipt-order/page | GET | 获得入库单分页 | wms:receipt-order:query |
| /wms/receipt-order/export-excel | GET | 导出入库单 Excel | wms:receipt-order:export |

### 入库单明细 (WmsReceiptOrderDetailController)

基础路径：`/wms/receipt-order-detail`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/receipt-order-detail/list-by-order-id | GET | 获得入库单明细列表 | wms:receipt-order:query |

### 出库单 (WmsShipmentOrderController)

基础路径：`/wms/shipment-order`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/shipment-order/create | POST | 创建出库单 | wms:shipment-order:create |
| /wms/shipment-order/update | PUT | 更新出库单 | wms:shipment-order:update |
| /wms/shipment-order/delete | DELETE | 删除出库单 | wms:shipment-order:delete |
| /wms/shipment-order/complete | PUT | 完成出库 | wms:shipment-order:complete |
| /wms/shipment-order/cancel | PUT | 作废出库单 | wms:shipment-order:cancel |
| /wms/shipment-order/get | GET | 获得出库单（含明细） | wms:shipment-order:query |
| /wms/shipment-order/page | GET | 获得出库单分页 | wms:shipment-order:query |
| /wms/shipment-order/export-excel | GET | 导出出库单 Excel | wms:shipment-order:export |

### 出库单明细 (WmsShipmentOrderDetailController)

基础路径：`/wms/shipment-order-detail`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/shipment-order-detail/list-by-order-id | GET | 获得出库单明细列表 | wms:shipment-order:query |

### 移库单 (WmsMovementOrderController)

基础路径：`/wms/movement-order`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/movement-order/create | POST | 创建移库单 | wms:movement-order:create |
| /wms/movement-order/update | PUT | 更新移库单 | wms:movement-order:update |
| /wms/movement-order/delete | DELETE | 删除移库单 | wms:movement-order:delete |
| /wms/movement-order/complete | PUT | 完成移库 | wms:movement-order:complete |
| /wms/movement-order/cancel | PUT | 作废移库单 | wms:movement-order:cancel |
| /wms/movement-order/get | GET | 获得移库单（含明细） | wms:movement-order:query |
| /wms/movement-order/page | GET | 获得移库单分页 | wms:movement-order:query |
| /wms/movement-order/export-excel | GET | 导出移库单 Excel | wms:movement-order:export |

### 移库单明细 (WmsMovementOrderDetailController)

基础路径：`/wms/movement-order-detail`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/movement-order-detail/list-by-order-id | GET | 获得移库单明细列表 | wms:movement-order:query |

### 盘库单 (WmsCheckOrderController)

基础路径：`/wms/check-order`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/check-order/create | POST | 创建盘库单 | wms:check-order:create |
| /wms/check-order/update | PUT | 更新盘库单 | wms:check-order:update |
| /wms/check-order/delete | DELETE | 删除盘库单 | wms:check-order:delete |
| /wms/check-order/complete | PUT | 完成盘库 | wms:check-order:complete |
| /wms/check-order/cancel | PUT | 作废盘库单 | wms:check-order:cancel |
| /wms/check-order/get | GET | 获得盘库单（含明细） | wms:check-order:query |
| /wms/check-order/page | GET | 获得盘库单分页 | wms:check-order:query |
| /wms/check-order/export-excel | GET | 导出盘库单 Excel | wms:check-order:export |

### 盘库单明细 (WmsCheckOrderDetailController)

基础路径：`/wms/check-order-detail`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /wms/check-order-detail/list-by-order-id | GET | 获得盘库单明细列表 | wms:check-order:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| wms_warehouse | 仓库 | BaseDO | code、name、sort、remark |
| wms_item | 商品 | BaseDO | code、name、unit、categoryId、brandId、remark |
| wms_item_sku | 商品 SKU | BaseDO | itemId、name、barCode、code、length/width/height、grossWeight/netWeight、costPrice、sellingPrice |
| wms_item_category | 商品分类（树形） | BaseDO | parentId（0 为根）、code、name、sort、status |
| wms_item_brand | 商品品牌 | BaseDO | code、name |
| wms_merchant | 往来企业（客户/供应商） | BaseDO | code、name、type（1 客户/2 供应商/3 客户供应商）、level、bankName、bankAccount、mobile、contact、email |
| wms_inventory | 库存余额（SKU + 仓库唯一） | BaseDO | skuId、warehouseId、quantity、remark |
| wms_inventory_history | 库存流水 | BaseDO | warehouseId、skuId、quantity、beforeQuantity、afterQuantity、price、totalPrice、orderId、orderNo、orderType |
| wms_receipt_order | 入库单 | BaseDO | no、type（生产/采购/退货/归还入库）、orderTime、status、bizOrderNo、merchantId（供应商）、warehouseId、totalQuantity、totalPrice |
| wms_receipt_order_detail | 入库单明细 | BaseDO | orderId、skuId、warehouseId、quantity、price、totalPrice |
| wms_shipment_order | 出库单 | BaseDO | no、type（退货/销售/生产出库）、orderTime、status、bizOrderNo、merchantId（客户）、warehouseId、totalQuantity、totalPrice |
| wms_shipment_order_detail | 出库单明细 | BaseDO | orderId、skuId、warehouseId、quantity、price、totalPrice |
| wms_movement_order | 移库单 | BaseDO | no、orderTime、status、sourceWarehouseId、targetWarehouseId、totalQuantity、totalPrice |
| wms_movement_order_detail | 移库单明细 | BaseDO | orderId、skuId、sourceWarehouseId、targetWarehouseId、quantity、price、totalPrice |
| wms_check_order | 盘库单 | BaseDO | no、orderTime、status、warehouseId、totalQuantity（盈亏数量）、totalPrice（账面金额）、actualPrice（实际金额） |
| wms_check_order_detail | 盘库单明细 | BaseDO | orderId、skuId、warehouseId、inventoryId、receiptTime、quantity（账面数量）、checkQuantity（实盘数量）、price |

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 单据状态机（约定式模板） | 四类单据 Service（如 `WmsReceiptOrderServiceImpl` 的 validateXxxOrderPrepare / completeXxx / cancelXxx） | 四类单据共享「草稿 → 已完成/已作废」的同一套流转与校验骨架，仅库存动作不同 |
| 悲观锁（行锁） | `WmsInventoryServiceImpl` + `WmsInventoryMapper.selectByIdForUpdate / selectListByIdsForUpdate` | 库存变更与盘库完成时锁定库存行后再计算前后数量，防止并发超卖/错算 |
| 唯一索引冲突兜底 | `WmsInventoryServiceImpl#createMissingInventoryList` | 并发创建同一 (skuId, warehouseId) 库存行时捕获 `DuplicateKeyException` 并回查已有行 |

## 依赖关系

- **上游**（本模块依赖）:
  - framework starter：yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-test
  - 业务模块：yudao-module-system（通过 `AdminUserApi` 查询单据创建人/更新人昵称）
- **下游**（依赖本模块）:
  - yudao-server（聚合启动模块，唯一引用方）；仓库内暂无其他业务模块依赖 wms

## 详细文档

- [api-home.md](api-home.md) - 首页统计
- [api-inventory.md](api-inventory.md) - 库存（库存统计与库存流水）
- [api-md.md](api-md.md) - 主数据（仓库、商品/SKU、分类、品牌、往来企业）
- [api-order.md](api-order.md) - 业务单据（入库、出库、移库、盘库）
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
