# 数据模型详情

## 实体继承体系

所有 DO 实体继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| creator | VARCHAR | 创建人 |
| createTime | DATETIME | 创建时间 |
| updater | VARCHAR | 更新人 |
| updateTime | DATETIME | 更新时间 |
| deleted | BIT | 是否删除（逻辑删除） |

## 表关系总览

```
wms_item_brand (品牌)
    |
    | 1:N
    v
wms_item (物料) <-- wms_item_category (分类，树结构 parentId)
    |
    | 1:N
    v
wms_item_sku (物料SKU)
    |
    | 1:N (SKU + 仓库 维度)
    v
wms_inventory (库存余额) --> wms_warehouse (仓库)
    |
    | 1:N
    v
wms_inventory_history (库存变动历史)

wms_merchant (商户) ----+
    |                   |
    | 1:N               | 1:N
    v                   v
wms_receipt_order (入库单)      wms_shipment_order (出库单)
    |                               |
    | 1:N                           | 1:N
    v                               v
wms_receipt_order_detail        wms_shipment_order_detail

wms_movement_order (移库单) --> wms_warehouse (源仓库)
                             --> wms_warehouse (目标仓库)
    |
    | 1:N
    v
wms_movement_order_detail

wms_check_order (盘点单) --> wms_warehouse (仓库)
    |
    | 1:N
    v
wms_check_order_detail
```

## 物料聚合

### wms_item_brand（品牌表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 品牌编号 |
| name | VARCHAR | | 品牌名称 |
| sort | INT | | 排序 |
| remark | VARCHAR | | 备注 |

### wms_item_category（分类表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 分类编号 |
| name | VARCHAR | | 分类名称 |
| parent_id | BIGINT | | 父分类编号（0=顶级） |
| sort | INT | | 排序 |
| remark | VARCHAR | | 备注 |

**索引**: idx_parent_id(parent_id)

### wms_item（物料表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 物料编号 |
| name | VARCHAR | | 物料名称 |
| code | VARCHAR | UNIQUE | 物料编码 |
| unit | VARCHAR | | 计量单位 |
| category_id | BIGINT | FK -> wms_item_category.id | 分类编号 |
| brand_id | BIGINT | FK -> wms_item_brand.id | 品牌编号 |
| status | TINYINT | | 物料状态 |
| remark | VARCHAR | | 备注 |

**索引**: idx_code(code), idx_category_id(category_id), idx_brand_id(brand_id)

### wms_item_sku（物料 SKU 表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | SKU 编号 |
| item_id | BIGINT | FK -> wms_item.id | 物料编号 |
| sku_no | VARCHAR | | SKU 编号/条码 |
| specifications | VARCHAR | | 规格属性 |
| bar_code | VARCHAR | | 条形码 |
| weight | DECIMAL | | 重量 |
| volume | DECIMAL | | 体积 |
| purchase_price | DECIMAL | | 采购价格 |
| selling_price | DECIMAL | | 销售价格 |
| status | TINYINT | | SKU 状态 |
| remark | VARCHAR | | 备注 |

**索引**: idx_item_id(item_id), idx_sku_no(sku_no)

---

## 商户与仓库

### wms_merchant（商户表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 商户编号 |
| name | VARCHAR | | 商户名称 |
| type | TINYINT | | 商户类型（1=客户 2=供应商 3=两者） |
| contact | VARCHAR | | 联系人 |
| phone | VARCHAR | | 联系电话 |
| address | VARCHAR | | 地址 |
| remark | VARCHAR | | 备注 |

### wms_warehouse（仓库表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 仓库编号 |
| code | VARCHAR | UNIQUE | 仓库编码 |
| name | VARCHAR | | 仓库名称 |
| sort | INT | | 排序 |
| remark | VARCHAR | | 备注 |

**索引**: idx_code(code)

---

## 库存聚合

### wms_inventory（库存表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 库存编号 |
| sku_id | BIGINT | FK -> wms_item_sku.id | SKU 编号 |
| warehouse_id | BIGINT | FK -> wms_warehouse.id | 仓库编号 |
| quantity | DECIMAL | | 库存数量 |
| price | DECIMAL | | 库存均价 |

**索引**: uk_sku_warehouse(sku_id, warehouse_id) UNIQUE

> 库存以 SKU + 仓库为唯一维度，每条记录代表某 SKU 在某仓库的库存余额。

### wms_inventory_history（库存历史表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 历史编号 |
| sku_id | BIGINT | FK -> wms_item_sku.id | SKU 编号 |
| warehouse_id | BIGINT | FK -> wms_warehouse.id | 仓库编号 |
| before_quantity | DECIMAL | | 变动前数量 |
| after_quantity | DECIMAL | | 变动后数量 |
| quantity | DECIMAL | | 变动数量（正=增加，负=减少） |
| price | DECIMAL | | 变动价格 |
| source_order_type | INTEGER | | 来源单据类型 |
| source_order_id | BIGINT | | 来源单据编号 |
| source_order_no | VARCHAR | | 来源单号 |

**索引**: idx_sku_warehouse(sku_id, warehouse_id), idx_source_order(source_order_type, source_order_id)

---

## 入库单聚合

### wms_receipt_order（入库单表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 入库单编号 |
| no | VARCHAR | UNIQUE | 入库单号 |
| warehouse_id | BIGINT | FK -> wms_warehouse.id | 仓库编号 |
| merchant_id | BIGINT | FK -> wms_merchant.id | 商户编号 |
| status | TINYINT | | 单据状态（0=PREPARE, 4=FINISHED, 5=CANCELED） |
| remark | VARCHAR | | 备注 |

**索引**: idx_no(no), idx_warehouse_id(warehouse_id), idx_status(status)

### wms_receipt_order_detail（入库明细表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 明细编号 |
| order_id | BIGINT | FK -> wms_receipt_order.id | 入库单编号 |
| sku_id | BIGINT | FK -> wms_item_sku.id | SKU 编号 |
| quantity | DECIMAL | | 入库数量 |
| price | DECIMAL | | 入库单价 |
| remark | VARCHAR | | 备注 |

**索引**: idx_order_id(order_id)

---

## 出库单聚合

### wms_shipment_order（出库单表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 出库单编号 |
| no | VARCHAR | UNIQUE | 出库单号 |
| warehouse_id | BIGINT | FK -> wms_warehouse.id | 仓库编号 |
| merchant_id | BIGINT | FK -> wms_merchant.id | 商户编号 |
| status | TINYINT | | 单据状态（0=PREPARE, 4=FINISHED, 5=CANCELED） |
| remark | VARCHAR | | 备注 |

**索引**: idx_no(no), idx_warehouse_id(warehouse_id), idx_status(status)

### wms_shipment_order_detail（出库明细表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 明细编号 |
| order_id | BIGINT | FK -> wms_shipment_order.id | 出库单编号 |
| sku_id | BIGINT | FK -> wms_item_sku.id | SKU 编号 |
| quantity | DECIMAL | | 出库数量 |
| price | DECIMAL | | 出库单价 |
| remark | VARCHAR | | 备注 |

**索引**: idx_order_id(order_id)

---

## 移库单聚合

### wms_movement_order（移库单表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 移库单编号 |
| no | VARCHAR | UNIQUE | 移库单号 |
| from_warehouse_id | BIGINT | FK -> wms_warehouse.id | 源仓库编号 |
| to_warehouse_id | BIGINT | FK -> wms_warehouse.id | 目标仓库编号 |
| status | TINYINT | | 单据状态（0=PREPARE, 4=FINISHED, 5=CANCELED） |
| remark | VARCHAR | | 备注 |

**索引**: idx_no(no), idx_from_warehouse_id(from_warehouse_id), idx_to_warehouse_id(to_warehouse_id), idx_status(status)

### wms_movement_order_detail（移库明细表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 明细编号 |
| order_id | BIGINT | FK -> wms_movement_order.id | 移库单编号 |
| sku_id | BIGINT | FK -> wms_item_sku.id | SKU 编号 |
| quantity | DECIMAL | | 移库数量 |
| remark | VARCHAR | | 备注 |

**索引**: idx_order_id(order_id)

---

## 盘点单聚合

### wms_check_order（盘点单表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 盘点单编号 |
| no | VARCHAR | UNIQUE | 盘点单号 |
| warehouse_id | BIGINT | FK -> wms_warehouse.id | 仓库编号 |
| status | TINYINT | | 单据状态（0=PREPARE, 4=FINISHED, 5=CANCELED） |
| remark | VARCHAR | | 备注 |

**索引**: idx_no(no), idx_warehouse_id(warehouse_id), idx_status(status)

### wms_check_order_detail（盘点明细表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 明细编号 |
| order_id | BIGINT | FK -> wms_check_order.id | 盘点单编号 |
| sku_id | BIGINT | FK -> wms_item_sku.id | SKU 编号 |
| system_quantity | DECIMAL | | 系统数量 |
| actual_quantity | DECIMAL | | 实际数量 |
| remark | VARCHAR | | 备注 |

**索引**: idx_order_id(order_id)

---

## ER 关系定义

| 关系 | 类型 | 外键 | 说明 |
|-----|------|------|------|
| wms_item -> wms_item_category | N:1 | category_id | 物料属于某个分类 |
| wms_item -> wms_item_brand | N:1 | brand_id | 物料属于某个品牌 |
| wms_item_sku -> wms_item | N:1 | item_id | SKU 属于某个物料 |
| wms_inventory -> wms_item_sku | N:1 | sku_id | 库存关联 SKU |
| wms_inventory -> wms_warehouse | N:1 | warehouse_id | 库存关联仓库 |
| wms_inventory_history -> wms_item_sku | N:1 | sku_id | 库存历史关联 SKU |
| wms_inventory_history -> wms_warehouse | N:1 | warehouse_id | 库存历史关联仓库 |
| wms_receipt_order -> wms_warehouse | N:1 | warehouse_id | 入库单关联仓库 |
| wms_receipt_order -> wms_merchant | N:1 | merchant_id | 入库单关联商户 |
| wms_receipt_order_detail -> wms_receipt_order | N:1 | order_id | 入库明细属于入库单 |
| wms_receipt_order_detail -> wms_item_sku | N:1 | sku_id | 入库明细关联 SKU |
| wms_shipment_order -> wms_warehouse | N:1 | warehouse_id | 出库单关联仓库 |
| wms_shipment_order -> wms_merchant | N:1 | merchant_id | 出库单关联商户 |
| wms_shipment_order_detail -> wms_shipment_order | N:1 | order_id | 出库明细属于出库单 |
| wms_shipment_order_detail -> wms_item_sku | N:1 | sku_id | 出库明细关联 SKU |
| wms_movement_order -> wms_warehouse | N:1 | from_warehouse_id | 移库单关联源仓库 |
| wms_movement_order -> wms_warehouse | N:1 | to_warehouse_id | 移库单关联目标仓库 |
| wms_movement_order_detail -> wms_movement_order | N:1 | order_id | 移库明细属于移库单 |
| wms_movement_order_detail -> wms_item_sku | N:1 | sku_id | 移库明细关联 SKU |
| wms_check_order -> wms_warehouse | N:1 | warehouse_id | 盘点单关联仓库 |
| wms_check_order_detail -> wms_check_order | N:1 | order_id | 盘点明细属于盘点单 |
| wms_check_order_detail -> wms_item_sku | N:1 | sku_id | 盘点明细关联 SKU |

## Mapper 规范

所有 Mapper 继承 `BaseMapperX<T>`，获得通用 CRUD 方法：

```java
public interface InventoryMapper extends BaseMapperX<InventoryDO> {
    default PageResult<InventoryDO> selectPage(InventoryPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<InventoryDO>()
                .eqIfPresent(InventoryDO::getSkuId, reqVO.getSkuId())
                .eqIfPresent(InventoryDO::getWarehouseId, reqVO.getWarehouseId())
                .orderByDesc(InventoryDO::getId));
    }
}
```

## 订单类型常量

WmsOrderTypeConstants 定义各单据类型范围：

| 常量 | 范围 | 说明 |
|-----|------|------|
| RECEIPT_ORDER_TYPE | [100, 200) | 入库单类型 |
| SHIPMENT_ORDER_TYPE | [200, 300) | 出库单类型 |
| MOVEMENT_ORDER_TYPE | [300, 400) | 移库单类型 |
| CHECK_ORDER_TYPE | [400, 500) | 盘点单类型 |

> 此常量用于库存历史记录的 sourceOrderType 字段，标识库存变动的来源单据类型。
