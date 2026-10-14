# 数据模型详情

> wms 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

wms 是轻量级仓库管理系统：主数据（仓库/商品/SKU/分类/品牌/往来企业）+ 入库/出库/移库/盘库四类单据驱动的库存与流水管理。共 16 张业务表，全部 DO 位于 `yudao-module-wms` 的 `cn.iocoder.yudao.module.wms.dal.dataobject` 包下。

## 1. 实体继承体系

```text
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，实现 Serializable / TransPojo）
├── creator     String          创建者（SysUser 用户编号，INSERT 时自动填充）
├── createTime  LocalDateTime   创建时间（INSERT 时自动填充）
├── updater     String          更新者（SysUser 用户编号，INSERT/UPDATE 时自动填充）
├── updateTime  LocalDateTime   最后更新时间（INSERT/UPDATE 时自动填充）
└── deleted     Boolean         逻辑删除标记（@TableLogic，查询自动拼接 deleted = 0）
     │
     └── TenantBaseDO（yudao-spring-boot-starter-biz-tenant，在 BaseDO 上扩展）
          └── tenantId  Long  多租户编号

cn.iocoder.yudao.module.wms.dal.dataobject（全部 16 个 DO 直接继承 BaseDO）
├── md.warehouse.WmsWarehouseDO            （wms_warehouse）
├── md.item.WmsItemDO                      （wms_item）
├── md.item.WmsItemSkuDO                   （wms_item_sku）
├── md.item.WmsItemCategoryDO              （wms_item_category）
├── md.item.WmsItemBrandDO                 （wms_item_brand）
├── md.merchant.WmsMerchantDO              （wms_merchant）
├── inventory.WmsInventoryDO               （wms_inventory）
├── inventory.WmsInventoryHistoryDO        （wms_inventory_history）
├── order.receipt.WmsReceiptOrderDO        （wms_receipt_order）
├── order.receipt.WmsReceiptOrderDetailDO  （wms_receipt_order_detail）
├── order.shipment.WmsShipmentOrderDO      （wms_shipment_order）
├── order.shipment.WmsShipmentOrderDetailDO（wms_shipment_order_detail）
├── order.movement.WmsMovementOrderDO      （wms_movement_order）
├── order.movement.WmsMovementOrderDetailDO（wms_movement_order_detail）
├── order.check.WmsCheckOrderDO            （wms_check_order）
└── order.check.WmsCheckOrderDetailDO      （wms_check_order_detail）
```

**使用规则**

- 本模块 16 个 DO **全部直接继承 BaseDO，无一使用 TenantBaseDO**：wms 各表均不含 `tenant_id` 字段，未启用多租户（需要租户隔离的模块如 system/mall 才继承 TenantBaseDO）。
- BaseDO 的 5 个公共字段（`creator`/`create_time`/`updater`/`update_time`/`deleted`）由框架字段填充器与 `@TableLogic` 统一维护，下文各 DO 字段表不再重复列出。
- 所有 DO 均标注 `@TableName("wms_xxx")` 与 `@KeySequence("wms_xxx_seq")`，后者供 Oracle/PostgreSQL 等序列型数据库生成主键，MySQL 下不生效。
- 仓库 `sql/` 目录的初始化 SQL **不含 wms 业务表 DDL**（仅部分方言文件含 wms 字典与菜单 INSERT），建表语句需另行维护；因此下文索引信息除特别标注外均从代码推断，仅有主键 id 可确认。

## 2. 核心 DO 实体

### 2.1 主数据聚合（md）

#### WmsWarehouseDO（wms_warehouse）

WMS 仓库。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| code | String | code | 仓库编号 |
| name | String | name | 名称 |
| remark | String | remark | 备注 |
| sort | Integer | sort | 排序 |

**继承**: BaseDO
**索引**: 主键 id

#### WmsItemDO（wms_item）

WMS 商品（SPU）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| code | String | code | 商品编号 |
| name | String | name | 商品名称 |
| unit | String | unit | 单位 |
| categoryId | Long | category_id | 商品分类编号，关联 wms_item_category.id |
| brandId | Long | brand_id | 商品品牌编号，关联 wms_item_brand.id |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id

#### WmsItemSkuDO（wms_item_sku）

WMS 商品 SKU。SKU 无独立写接口，随 WmsItemController 商品接口一并维护（新增/修改/删除）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| name | String | name | 规格名称 |
| itemId | Long | item_id | 商品编号，关联 wms_item.id |
| barCode | String | bar_code | 条码 |
| code | String | code | 规格编号 |
| length | BigDecimal | length | 长，单位 cm |
| width | BigDecimal | width | 宽，单位 cm |
| height | BigDecimal | height | 高，单位 cm |
| grossWeight | BigDecimal | gross_weight | 毛重，单位 kg |
| netWeight | BigDecimal | net_weight | 净重，单位 kg |
| costPrice | BigDecimal | cost_price | 成本价，单位元 |
| sellingPrice | BigDecimal | selling_price | 销售价，单位元 |

**继承**: BaseDO
**索引**: 主键 id；库存/单据明细均以 sku_id 引用本表

#### WmsItemCategoryDO（wms_item_category）

WMS 商品分类，parentId 自关联的树形结构。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| parentId | Long | parent_id | 父级编号，关联本表 id；根节点固定 0（PARENT_ID_ROOT） |
| code | String | code | 分类编号 |
| name | String | name | 分类名称 |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 CommonStatusEnum（0 开启 / 1 禁用） |

**继承**: BaseDO
**索引**: 主键 id

#### WmsItemBrandDO（wms_item_brand）

WMS 商品品牌。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| code | String | code | 品牌编号 |
| name | String | name | 品牌名称 |

**继承**: BaseDO
**索引**: 主键 id

#### WmsMerchantDO（wms_merchant）

WMS 往来企业（客户/供应商共用一张表，靠 type 区分）。入库单引用的 merchantId 必须是供应商（或客供两用），出库单必须是客户，由 WmsMerchantTypeEnum 在单据服务中校验。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| code | String | code | 往来企业编号 |
| name | String | name | 往来企业名称 |
| type | Integer | type | 企业类型，枚举 WmsMerchantTypeEnum（1 客户 / 2 供应商 / 3 客户与供应商），字典 merchant_type |
| level | String | level | 级别 |
| bankName | String | bank_name | 开户行 |
| bankAccount | String | bank_account | 银行账户 |
| address | String | address | 地址 |
| mobile | String | mobile | 手机号 |
| telephone | String | telephone | 座机号 |
| contact | String | contact | 联系人 |
| email | String | email | Email |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id

### 2.2 库存聚合（inventory）

#### WmsInventoryDO（wms_inventory）

WMS 库存余额表，按「SKU + 仓库」维度一行一条，是整个模块的核心表。所有入库/出库/移库/盘库单据的完成动作都汇聚到 `WmsInventoryServiceImpl.changeInventory/checkInventory` 两个入口更新本表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| skuId | Long | sku_id | 商品 SKU 编号，关联 wms_item_sku.id |
| warehouseId | Long | warehouse_id | 仓库编号，关联 wms_warehouse.id |
| quantity | BigDecimal | quantity | 库存数量（不允许为负，扣减前校验） |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；**(sku_id, warehouse_id) 唯一索引**——从代码推断：`WmsInventoryMapper.selectBySkuIdAndWarehouseId` 按「唯一键」查询，并发补建库存行时捕获 `DuplicateKeyException` 后按维度回查已有行。并发更新通过 `selectByIdForUpdate`/`selectListByIdsForUpdate`（`FOR UPDATE` 悲观锁）按库存行加锁。

#### WmsInventoryHistoryDO（wms_inventory_history）

WMS 库存流水表，每次库存变动（入库/出库/移库/盘库）生成一条，记录变化前后数量与来源单据，不可修改删除。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| warehouseId | Long | warehouse_id | 仓库编号，关联 wms_warehouse.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 wms_item_sku.id |
| quantity | BigDecimal | quantity | 库存变化数量（带符号，正增负减） |
| beforeQuantity | BigDecimal | before_quantity | 变化前库存数量 |
| afterQuantity | BigDecimal | after_quantity | 变化后库存数量 |
| price | BigDecimal | price | 单价 |
| totalPrice | BigDecimal | total_price | 库存变化金额（单价 × 变化数量） |
| remark | String | remark | 备注 |
| orderId | Long | order_id | 来源单据编号（四类单据的 id） |
| orderNo | String | order_no | 来源单据号 |
| orderType | Integer | order_type | 来源单据类型，枚举 WmsOrderTypeEnum（1 入库单 / 2 出库单 / 3 移库单 / 4 盘库单），字典 wms_order_type |

**继承**: BaseDO
**索引**: 主键 id；按 order_id + order_type 查询单据相关流水（代码中存在按单据维度的查询）

### 2.3 单据聚合（order）

四类单据均为「主表 + 明细表」结构，状态统一使用 `WmsOrderStatusEnum`（0 草稿 PREPARE / 4 已完成 FINISHED / 5 已作废 CANCELED，字典 wms_order_status），仅草稿态允许修改、删除、完成、作废。完成单据时按明细逐行写库存流水并增减 wms_inventory。

#### WmsReceiptOrderDO（wms_receipt_order）

WMS 入库单主表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| no | String | no | 入库单号 |
| type | Integer | type | 入库类型，枚举 WmsReceiptOrderTypeEnum（100 生产入库 / 101 采购入库 / 102 退货入库 / 103 归还入库），字典 wms_receipt_order_type |
| orderTime | LocalDateTime | order_time | 单据日期 |
| status | Integer | status | 入库状态，枚举 WmsOrderStatusEnum（0 草稿 / 4 已完成 / 5 已作废），字典 wms_order_status |
| bizOrderNo | String | biz_order_no | 业务订单号（上游业务单据号） |
| merchantId | Long | merchant_id | 供应商编号，关联 wms_merchant.id（校验必须为供应商类型） |
| remark | String | remark | 备注 |
| warehouseId | Long | warehouse_id | 入库仓库编号，关联 wms_warehouse.id |
| totalQuantity | BigDecimal | total_quantity | 总数量（明细汇总） |
| totalPrice | BigDecimal | total_price | 总金额（明细汇总） |

**继承**: BaseDO
**索引**: 主键 id

#### WmsReceiptOrderDetailDO（wms_receipt_order_detail）

WMS 入库单明细表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| orderId | Long | order_id | 入库单编号，关联 wms_receipt_order.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 wms_item_sku.id |
| warehouseId | Long | warehouse_id | 入库仓库编号，关联 wms_warehouse.id |
| quantity | BigDecimal | quantity | 入库数量（完成时为库存增量） |
| price | BigDecimal | price | 单价 |
| totalPrice | BigDecimal | total_price | 行金额（数量 × 单价） |

**继承**: BaseDO
**索引**: 主键 id；按 order_id 查询明细（list-by-order-id 接口）

#### WmsShipmentOrderDO（wms_shipment_order）

WMS 出库单主表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| no | String | no | 出库单号 |
| type | Integer | type | 出库类型，枚举 WmsShipmentOrderTypeEnum（200 退货出库 / 201 销售出库 / 202 生产出库），字典 wms_shipment_order_type |
| orderTime | LocalDateTime | order_time | 单据日期 |
| status | Integer | status | 出库状态，枚举 WmsOrderStatusEnum（0 草稿 / 4 已完成 / 5 已作废），字典 wms_order_status |
| bizOrderNo | String | biz_order_no | 业务订单号 |
| merchantId | Long | merchant_id | 客户编号，关联 wms_merchant.id（校验必须为客户类型） |
| remark | String | remark | 备注 |
| warehouseId | Long | warehouse_id | 出库仓库编号，关联 wms_warehouse.id |
| totalQuantity | BigDecimal | total_quantity | 总数量（明细汇总） |
| totalPrice | BigDecimal | total_price | 总金额（明细汇总） |

**继承**: BaseDO
**索引**: 主键 id

#### WmsShipmentOrderDetailDO（wms_shipment_order_detail）

WMS 出库单明细表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| orderId | Long | order_id | 出库单编号，关联 wms_shipment_order.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 wms_item_sku.id |
| warehouseId | Long | warehouse_id | 出库仓库编号，关联 wms_warehouse.id |
| quantity | BigDecimal | quantity | 出库数量（完成时为库存减量，不足则报错） |
| price | BigDecimal | price | 单价 |
| totalPrice | BigDecimal | total_price | 行金额（数量 × 单价） |

**继承**: BaseDO
**索引**: 主键 id；按 order_id 查询明细（list-by-order-id 接口）

#### WmsMovementOrderDO（wms_movement_order）

WMS 移库单主表，来源仓库与目标仓库必须不同（服务层校验）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| no | String | no | 移库单号 |
| orderTime | LocalDateTime | order_time | 单据日期 |
| status | Integer | status | 移库状态，枚举 WmsOrderStatusEnum（0 草稿 / 4 已完成 / 5 已作废），字典 wms_order_status |
| remark | String | remark | 备注 |
| sourceWarehouseId | Long | source_warehouse_id | 来源仓库编号，关联 wms_warehouse.id（≠ targetWarehouseId） |
| targetWarehouseId | Long | target_warehouse_id | 目标仓库编号，关联 wms_warehouse.id |
| totalQuantity | BigDecimal | total_quantity | 总数量（明细汇总） |
| totalPrice | BigDecimal | total_price | 总金额（明细汇总） |

**继承**: BaseDO
**索引**: 主键 id

#### WmsMovementOrderDetailDO（wms_movement_order_detail）

WMS 移库单明细表。完成时按行生成两条流水：来源仓库出库（负）、目标仓库入库（正）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| orderId | Long | order_id | 移库单编号，关联 wms_movement_order.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 wms_item_sku.id |
| sourceWarehouseId | Long | source_warehouse_id | 来源仓库编号，关联 wms_warehouse.id |
| targetWarehouseId | Long | target_warehouse_id | 目标仓库编号，关联 wms_warehouse.id |
| quantity | BigDecimal | quantity | 移库数量 |
| price | BigDecimal | price | 单价 |
| totalPrice | BigDecimal | total_price | 行金额（数量 × 单价） |

**继承**: BaseDO
**索引**: 主键 id；按 order_id 查询明细（list-by-order-id 接口）

#### WmsCheckOrderDO（wms_check_order）

WMS 盘库单主表，针对单一仓库盘点。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| no | String | no | 盘库单号 |
| orderTime | LocalDateTime | order_time | 单据日期 |
| status | Integer | status | 盘库状态，枚举 WmsOrderStatusEnum（0 草稿 / 4 已完成 / 5 已作废），字典 wms_order_status |
| remark | String | remark | 备注 |
| warehouseId | Long | warehouse_id | 盘点仓库编号，关联 wms_warehouse.id |
| totalQuantity | BigDecimal | total_quantity | 盈亏数量（实盘数量 - 账面数量） |
| totalPrice | BigDecimal | total_price | 总金额（账面数量 × 单价） |
| actualPrice | BigDecimal | actual_price | 实际金额（实盘数量 × 单价） |

**继承**: BaseDO
**索引**: 主键 id

#### WmsCheckOrderDetailDO（wms_check_order_detail）

WMS 盘库单明细表，逐条对应一行库存（inventoryId）。盘库完成时以实盘数量直接覆盖库存（`checkInventory`），并按差额生成流水。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键编号 |
| orderId | Long | order_id | 盘库单编号，关联 wms_check_order.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 wms_item_sku.id |
| warehouseId | Long | warehouse_id | 盘点仓库编号，关联 wms_warehouse.id |
| inventoryId | Long | inventory_id | 库存编号，关联 wms_inventory.id（存量库存行） |
| receiptTime | LocalDateTime | receipt_time | 入库时间 |
| quantity | BigDecimal | quantity | 账面数量 |
| checkQuantity | BigDecimal | check_quantity | 实盘数量 |
| price | BigDecimal | price | 单价 |

**继承**: BaseDO
**索引**: 主键 id；按 order_id 查询明细（list-by-order-id 接口）

## 3. 实体关系

- **主数据**：分类（parentId 自关联树）、品牌、仓库、往来企业均为独立主数据；商品挂在分类 + 品牌下，一个商品（wms_item）下挂多个 SKU（wms_item_sku），SKU 是库存与单据明细的最小计量单元。
- **库存**：wms_inventory 由 (sku_id, warehouse_id) 唯一定位，逻辑上是 wms_item_sku × wms_warehouse 的交集实体；wms_inventory_history 是它的变动流水，通过 order_id + order_type 弱关联到四类单据（无数据库外键，仅逻辑关联）。
- **单据**：四类单据（入库/出库/移库/盘库）均为 1:N 主明细结构；主表引用仓库（入库/出库/盘库单仓库，移库单来源+目标仓库）与往来企业（入库=供应商、出库=客户），明细行引用 SKU 与仓库；盘库明细额外引用库存行（inventory_id）。
- 所有跨表引用均为逻辑外键（代码层 `@link` 注释约定），数据库层不建立 FOREIGN KEY 约束。

```text
wms_item_category ──(parent_id 自关联树)──┐
wms_item_brand ──────────────────────────┤
                                         ▼
                                    wms_item (category_id, brand_id)
                                         │ 1:N item_id
                                         ▼
                                    wms_item_sku (item_id)
                                         │ 1:N sku_id
              ┌──────────────────────────┼──────────────────────────────┐
              ▼                          ▼                              │
      wms_inventory ◄──1:1── wms_check_order_detail (inventory_id)      │
     (sku_id+warehouse_id 唯一)         │ N:1 order_id                  │
              │ 流动                    ▼                              │
              ▼                   wms_check_order (warehouse_id)        │
      wms_inventory_history                                             │
     (sku_id, warehouse_id,                                             │
      order_id+order_type 弱关联四类单据)                                │
                                                                       │
wms_warehouse (id) ──┬── wms_receipt_order (warehouse_id, merchant_id[供应商]) ──1:N── wms_receipt_order_detail (sku_id, warehouse_id)
                     ├── wms_shipment_order (warehouse_id, merchant_id[客户])   ──1:N── wms_shipment_order_detail (sku_id, warehouse_id)
                     ├── wms_movement_order (source/target_warehouse_id)        ──1:N── wms_movement_order_detail (sku_id, source/target_warehouse_id)
                     └── wms_check_order (warehouse_id)
wms_merchant (id) ──── 被 wms_receipt_order.merchant_id（供应商）/ wms_shipment_order.merchant_id（客户）引用
```

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|------|
| wms_warehouse | WmsWarehouseDO | 仓库 |
| wms_item | WmsItemDO | 商品（SPU） |
| wms_item_sku | WmsItemSkuDO | 商品 SKU（规格/条码/重量体积/价格） |
| wms_item_category | WmsItemCategoryDO | 商品分类（树形） |
| wms_item_brand | WmsItemBrandDO | 商品品牌 |
| wms_merchant | WmsMerchantDO | 往来企业（客户/供应商） |
| wms_inventory | WmsInventoryDO | 库存余额（SKU + 仓库 唯一） |
| wms_inventory_history | WmsInventoryHistoryDO | 库存流水（含来源单据信息） |
| wms_receipt_order | WmsReceiptOrderDO | 入库单主表 |
| wms_receipt_order_detail | WmsReceiptOrderDetailDO | 入库单明细 |
| wms_shipment_order | WmsShipmentOrderDO | 出库单主表 |
| wms_shipment_order_detail | WmsShipmentOrderDetailDO | 出库单明细 |
| wms_movement_order | WmsMovementOrderDO | 移库单主表 |
| wms_movement_order_detail | WmsMovementOrderDetailDO | 移库单明细 |
| wms_check_order | WmsCheckOrderDO | 盘库单主表 |
| wms_check_order_detail | WmsCheckOrderDetailDO | 盘库单明细 |
