# 仓储管理模块 (wms)

> wms 模块是仓储管理系统，提供仓库、物料、库存、入库、出库、移库、盘点等全流程仓储业务能力支撑。

## 模块概述

- **模块路径**: yudao-module-wms
- **业务定位**: 面向仓储管理场景，管理仓库、物料、库存及四大单据（入库、出库、移库、盘点）的完整业务闭环
- **核心职责**: 仓库管理、物料管理（含 SKU）、库存管理、入库管理、出库管理、移库管理、盘点管理、仪表盘统计

## 核心功能点

| 功能 | 说明 | 关键实体 |
|-----|------|---------|
| 仓库管理 | 仓库基本信息维护，支持编码、名称、排序 | WarehouseDO |
| 物料管理 | 物料主数据管理，包含品牌、分类（树结构）、SKU（多规格） | ItemDO, ItemSkuDO, ItemBrandDO, ItemCategoryDO |
| 商户管理 | 客户/供应商/既是客户也是供应商的业务伙伴管理 | MerchantDO |
| 库存管理 | 基于 SKU+仓库 维度的库存余额管理，只读，仅通过单据完成变更 | InventoryDO |
| 库存历史 | 库存变动流水记录，包含变动前后数量、价格、来源单据 | InventoryHistoryDO |
| 入库管理 | 入库单创建、审核、完成、取消，支持明细行管理 | ReceiptOrderDO, ReceiptOrderDetailDO |
| 出库管理 | 出库单创建、审核、完成、取消，支持明细行管理 | ShipmentOrderDO, ShipmentOrderDetailDO |
| 移库管理 | 库间调拨单创建、审核、完成、取消，支持明细行管理 | MovementOrderDO, MovementOrderDetailDO |
| 盘点管理 | 库存盘点单创建、审核、完成、取消，支持明细行管理 | CheckOrderDO, CheckOrderDetailDO |
| 首页统计 | 订单汇总、订单趋势、库存汇总等仪表盘数据 | - |

## API 接口索引

### 主数据接口

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| `/wms/item/create` | POST | 创建物料 | wms:item:create |
| `/wms/item/update` | PUT | 更新物料 | wms:item:update |
| `/wms/item/delete` | DELETE | 删除物料 | wms:item:delete |
| `/wms/item/get` | GET | 获取物料详情 | wms:item:query |
| `/wms/item/page` | GET | 物料分页查询 | wms:item:query |
| `/wms/item/simple-list` | GET | 物料精简列表 | - |
| `/wms/item/export-excel` | GET | 导出物料 Excel | wms:item:export |
| `/wms/item-sku/page` | GET | SKU 分页查询 | wms:item-sku:query |
| `/wms/item-brand/create` | POST | 创建品牌 | wms:item-brand:create |
| `/wms/item-brand/update` | PUT | 更新品牌 | wms:item-brand:update |
| `/wms/item-brand/delete` | DELETE | 删除品牌 | wms:item-brand:delete |
| `/wms/item-brand/get` | GET | 获取品牌详情 | wms:item-brand:query |
| `/wms/item-brand/page` | GET | 品牌分页查询 | wms:item-brand:query |
| `/wms/item-brand/simple-list` | GET | 品牌精简列表 | - |
| `/wms/item-brand/export-excel` | GET | 导出品牌 Excel | wms:item-brand:export |
| `/wms/item-category/create` | POST | 创建分类 | wms:item-category:create |
| `/wms/item-category/update` | PUT | 更新分类 | wms:item-category:update |
| `/wms/item-category/delete` | DELETE | 删除分类 | wms:item-category:delete |
| `/wms/item-category/get` | GET | 获取分类详情 | wms:item-category:query |
| `/wms/item-category/list` | GET | 分类树形列表 | wms:item-category:query |
| `/wms/item-category/simple-list` | GET | 分类精简列表 | - |
| `/wms/merchant/create` | POST | 创建商户 | wms:merchant:create |
| `/wms/merchant/update` | PUT | 更新商户 | wms:merchant:update |
| `/wms/merchant/delete` | DELETE | 删除商户 | wms:merchant:delete |
| `/wms/merchant/get` | GET | 获取商户详情 | wms:merchant:query |
| `/wms/merchant/page` | GET | 商户分页查询 | wms:merchant:query |
| `/wms/merchant/simple-list` | GET | 商户精简列表 | - |
| `/wms/merchant/export-excel` | GET | 导出商户 Excel | wms:merchant:export |
| `/wms/warehouse/create` | POST | 创建仓库 | wms:warehouse:create |
| `/wms/warehouse/update` | PUT | 更新仓库 | wms:warehouse:update |
| `/wms/warehouse/delete` | DELETE | 删除仓库 | wms:warehouse:delete |
| `/wms/warehouse/get` | GET | 获取仓库详情 | wms:warehouse:query |
| `/wms/warehouse/page` | GET | 仓库分页查询 | wms:warehouse:query |
| `/wms/warehouse/simple-list` | GET | 仓库精简列表 | - |
| `/wms/warehouse/export-excel` | GET | 导出仓库 Excel | wms:warehouse:export |

### 库存接口

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| `/wms/inventory/page` | GET | 库存分页查询 | wms:inventory:query |
| `/wms/inventory/list` | GET | 库存列表查询 | wms:inventory:query |
| `/wms/inventory-history/page` | GET | 库存历史分页查询 | wms:inventory-history:query |

### 单据接口

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| `/wms/receipt-order/create` | POST | 创建入库单 | wms:receipt-order:create |
| `/wms/receipt-order/update` | PUT | 更新入库单 | wms:receipt-order:update |
| `/wms/receipt-order/delete` | DELETE | 删除入库单 | wms:receipt-order:delete |
| `/wms/receipt-order/complete` | PUT | 完成入库 | wms:receipt-order:update |
| `/wms/receipt-order/cancel` | PUT | 取消入库 | wms:receipt-order:update |
| `/wms/receipt-order/get` | GET | 获取入库单详情 | wms:receipt-order:query |
| `/wms/receipt-order/page` | GET | 入库单分页查询 | wms:receipt-order:query |
| `/wms/receipt-order/export-excel` | GET | 导出入库单 Excel | wms:receipt-order:export |
| `/wms/receipt-order-detail/list-by-order-id` | GET | 入库明细列表 | wms:receipt-order:query |
| `/wms/shipment-order/create` | POST | 创建出库单 | wms:shipment-order:create |
| `/wms/shipment-order/update` | PUT | 更新出库单 | wms:shipment-order:update |
| `/wms/shipment-order/delete` | DELETE | 删除出库单 | wms:shipment-order:delete |
| `/wms/shipment-order/complete` | PUT | 完成出库 | wms:shipment-order:update |
| `/wms/shipment-order/cancel` | PUT | 取消出库 | wms:shipment-order:update |
| `/wms/shipment-order/get` | GET | 获取出库单详情 | wms:shipment-order:query |
| `/wms/shipment-order/page` | GET | 出库单分页查询 | wms:shipment-order:query |
| `/wms/shipment-order/export-excel` | GET | 导出出库单 Excel | wms:shipment-order:export |
| `/wms/shipment-order-detail/list-by-order-id` | GET | 出库明细列表 | wms:shipment-order:query |
| `/wms/movement-order/create` | POST | 创建移库单 | wms:movement-order:create |
| `/wms/movement-order/update` | PUT | 更新移库单 | wms:movement-order:update |
| `/wms/movement-order/delete` | DELETE | 删除移库单 | wms:movement-order:delete |
| `/wms/movement-order/complete` | PUT | 完成移库 | wms:movement-order:update |
| `/wms/movement-order/cancel` | PUT | 取消移库 | wms:movement-order:update |
| `/wms/movement-order/get` | GET | 获取移库单详情 | wms:movement-order:query |
| `/wms/movement-order/page` | GET | 移库单分页查询 | wms:movement-order:query |
| `/wms/movement-order/export-excel` | GET | 导出移库单 Excel | wms:movement-order:export |
| `/wms/movement-order-detail/list-by-order-id` | GET | 移库明细列表 | wms:movement-order:query |
| `/wms/check-order/create` | POST | 创建盘点单 | wms:check-order:create |
| `/wms/check-order/update` | PUT | 更新盘点单 | wms:check-order:update |
| `/wms/check-order/delete` | DELETE | 删除盘点单 | wms:check-order:delete |
| `/wms/check-order/complete` | PUT | 完成盘点 | wms:check-order:update |
| `/wms/check-order/cancel` | PUT | 取消盘点 | wms:check-order:update |
| `/wms/check-order/get` | GET | 获取盘点单详情 | wms:check-order:query |
| `/wms/check-order/page` | GET | 盘点单分页查询 | wms:check-order:query |
| `/wms/check-order/export-excel` | GET | 导出盘点单 Excel | wms:check-order:export |
| `/wms/check-order-detail/list-by-order-id` | GET | 盘点明细列表 | wms:check-order:query |

### 统计接口

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| `/wms/home-statistics/order-summary` | GET | 订单汇总统计 | wms:home-statistics:query |
| `/wms/home-statistics/order-trend` | GET | 订单趋势统计 | wms:home-statistics:query |
| `/wms/home-statistics/inventory-summary` | GET | 库存汇总统计 | wms:home-statistics:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| wms_warehouse | 仓库表 | BaseDO | code, name, sort |
| wms_item | 物料表 | BaseDO | name, code, unit, status |
| wms_item_sku | 物料 SKU 表 | BaseDO | item_id, sku_no, dimensions, weight, price |
| wms_item_brand | 品牌表 | BaseDO | name, sort |
| wms_item_category | 分类表 | BaseDO | name, parent_id, sort |
| wms_merchant | 商户表 | BaseDO | name, type(客户/供应商/两者), contact |
| wms_inventory | 库存表 | BaseDO | sku_id, warehouse_id, quantity |
| wms_inventory_history | 库存历史表 | BaseDO | sku_id, warehouse_id, before_quantity, after_quantity, source_order_type, source_order_id |
| wms_receipt_order | 入库单表 | BaseDO | no, warehouse_id, merchant_id, status |
| wms_receipt_order_detail | 入库明细表 | BaseDO | order_id, sku_id, quantity, price |
| wms_shipment_order | 出库单表 | BaseDO | no, warehouse_id, merchant_id, status |
| wms_shipment_order_detail | 出库明细表 | BaseDO | order_id, sku_id, quantity, price |
| wms_movement_order | 移库单表 | BaseDO | no, from_warehouse_id, to_warehouse_id, status |
| wms_movement_order_detail | 移库明细表 | BaseDO | order_id, sku_id, quantity |
| wms_check_order | 盘点单表 | BaseDO | no, warehouse_id, status |
| wms_check_order_detail | 盘点明细表 | BaseDO | order_id, sku_id, system_quantity, actual_quantity |

## 设计模式

- **单据头/明细模式**: 所有四大单据（入库、出库、移库、盘点）均采用 Header + Detail 的主子表结构，单据头存储汇总信息，明细行存储 SKU 级别的数据
- **VO 组装模式**: Service 层通过批量查询关联实体到 Map 中，再通过 BeanUtils.toBean() 丰富 VO 对象，避免 N+1 查询
- **只读库存控制器**: 库存和库存历史 Controller 均为只读，所有库存变更必须通过单据完成（complete）操作触发
- **并发安全库存更新**: 使用 SELECT ... FOR UPDATE 行锁 + DuplicateKeyException 捕获实现库存初始化的并发安全
- **单据状态机**: PREPARE(0) -> FINISHED(4) 或 CANCELED(5)，单据只有在 PREPARE 状态下才能完成或取消
- **SKU 作为库存单位**: 库存以 SKU + 仓库维度跟踪，不跟踪物料级别库存
- **订单类型常量分段**: WmsOrderTypeConstants 定义订单类型范围：入库 [100,200)、出库 [200,300)，用于库存历史来源标识
- **Excel 导出**: 所有主数据和单据均支持 Excel 导出功能
- **细粒度权限控制**: 权限标识格式 `wms:{entity}:{action}`，如 `wms:receipt-order:create`
- **字典集成**: 单据状态、子类型等使用系统字典管理

## 依赖关系

### 内部依赖

| 模块 | 用途 |
|-----|------|
| yudao-module-system | AdminUserApi - 获取用户信息用于 VO 组装 |
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |

### 外部依赖

| 库 | 用途 |
|---|------|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| Hutool | Java 工具类库 |
| Swagger/OpenAPI | API 文档注解 |
| Apache POI | Excel 导入导出 |

## 模块间通信

| 接口 | 方法 | 说明 | 调用方 |
|-----|------|------|-------|
| AdminUserApi | getUserMap() | 批量获取用户信息，用于 VO 中展示用户名 | wms 模块内部 VO 组装 |

## 详细文档

- [api-master-data.md](api-master-data.md) - 主数据接口（物料、品牌、分类、商户、仓库）
- [api-inventory.md](api-inventory.md) - 库存管理接口
- [api-receipt.md](api-receipt.md) - 入库单接口
- [api-shipment.md](api-shipment.md) - 出库单接口
- [api-movement.md](api-movement.md) - 移库单接口
- [api-check.md](api-check.md) - 盘点单接口
- [api-home.md](api-home.md) - 首页统计接口
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项
