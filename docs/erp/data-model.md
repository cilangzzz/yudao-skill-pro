# ERP 模块数据模型

## 实体继承体系

所有 DO 实体类继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| creator | VARCHAR | 创建人 |
| create_time | DATETIME | 创建时间 |
| updater | VARCHAR | 更新人 |
| update_time | DATETIME | 更新时间 |
| deleted | BIT | 逻辑删除标记 |

---

## 数据表清单

### 产品相关表

#### erp_product - 产品表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 产品编号（主键） |
| name | VARCHAR | 产品名称 |
| bar_code | VARCHAR | 产品条码 |
| category_id | BIGINT | 产品分类ID（FK -> erp_product_category） |
| unit_id | BIGINT | 单位ID（FK -> erp_product_unit） |
| status | INT | 状态（0正常 1停用） |
| standard | VARCHAR | 规格 |
| purchase_price | DECIMAL | 采购价 |
| sale_price | DECIMAL | 销售价 |
| min_price | DECIMAL | 最低价 |

#### erp_product_category - 产品分类表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 分类编号（主键） |
| parent_id | BIGINT | 父分类ID（自关联，0为顶级） |
| name | VARCHAR | 分类名称 |
| status | INT | 状态 |

#### erp_product_unit - 产品单位表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 单位编号（主键） |
| name | VARCHAR | 单位名称 |
| status | INT | 状态 |

---

### 采购相关表

#### erp_supplier - 供应商表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 供应商编号（主键） |
| name | VARCHAR | 供应商名称 |
| contact | VARCHAR | 联系人 |
| mobile | VARCHAR | 手机号 |
| status | INT | 状态 |

#### erp_purchase_order - 采购订单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 采购订单号（CGDD+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| supplier_id | BIGINT | 供应商ID（FK -> erp_supplier） |
| account_id | BIGINT | 结算账户ID（FK -> erp_account） |
| order_time | DATETIME | 下单时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 最终合计价格 |
| total_product_price | DECIMAL | 合计产品价格 |
| total_tax_price | DECIMAL | 合计税额 |
| discount_percent | DECIMAL | 优惠率(%) |
| discount_price | DECIMAL | 优惠金额 |
| in_count | DECIMAL | 已入库数量 |
| return_count | DECIMAL | 已退货数量 |

#### erp_purchase_order_item - 采购订单项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| order_id | BIGINT | 采购订单ID（FK -> erp_purchase_order） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| product_unit_id | BIGINT | 产品单位ID（FK -> erp_product_unit） |
| count | DECIMAL | 数量 |
| product_price | DECIMAL | 产品单价 |
| tax_percent | DECIMAL | 税率(%) |
| in_count | DECIMAL | 已入库数量 |
| return_count | DECIMAL | 已退货数量 |

#### erp_purchase_in - 采购入库表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 入库单号 |
| status | INT | 状态（10未审核 20已审核） |
| supplier_id | BIGINT | 供应商ID（FK -> erp_supplier） |
| order_id | BIGINT | 采购订单ID（FK -> erp_purchase_order） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| in_time | DATETIME | 入库时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 合计价格 |
| payment_price | DECIMAL | 已付款金额 |

#### erp_purchase_in_item - 采购入库项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| in_id | BIGINT | 采购入库ID（FK -> erp_purchase_in） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 入库数量 |
| product_price | DECIMAL | 产品单价 |

#### erp_purchase_return - 采购退货表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 退货单号 |
| status | INT | 状态（10未审核 20已审核） |
| supplier_id | BIGINT | 供应商ID（FK -> erp_supplier） |
| order_id | BIGINT | 采购订单ID（FK -> erp_purchase_order） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| return_time | DATETIME | 退货时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 合计价格 |
| refund_price | DECIMAL | 已退款金额 |

#### erp_purchase_return_item - 采购退货项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| return_id | BIGINT | 采购退货ID（FK -> erp_purchase_return） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 退货数量 |
| product_price | DECIMAL | 产品单价 |

---

### 销售相关表

#### erp_customer - 客户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 客户编号（主键） |
| name | VARCHAR | 客户名称 |
| contact | VARCHAR | 联系人 |
| mobile | VARCHAR | 手机号 |
| status | INT | 状态 |

#### erp_sale_order - 销售订单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 销售订单号（XSDD+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| customer_id | BIGINT | 客户ID（FK -> erp_customer） |
| account_id | BIGINT | 结算账户ID（FK -> erp_account） |
| sale_user_id | BIGINT | 销售员ID |
| order_time | DATETIME | 下单时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 最终合计价格 |
| out_count | DECIMAL | 已出库数量 |
| return_count | DECIMAL | 已退货数量 |

#### erp_sale_order_item - 销售订单项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| order_id | BIGINT | 销售订单ID（FK -> erp_sale_order） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 数量 |
| product_price | DECIMAL | 产品单价 |
| out_count | DECIMAL | 已出库数量 |
| return_count | DECIMAL | 已退货数量 |

#### erp_sale_out - 销售出库表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 出库单号 |
| status | INT | 状态（10未审核 20已审核） |
| customer_id | BIGINT | 客户ID（FK -> erp_customer） |
| order_id | BIGINT | 销售订单ID（FK -> erp_sale_order） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| out_time | DATETIME | 出库时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 合计价格 |
| receipt_price | DECIMAL | 已收款金额 |

#### erp_sale_out_item - 销售出库项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| out_id | BIGINT | 销售出库ID（FK -> erp_sale_out） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 出库数量 |
| product_price | DECIMAL | 产品单价 |

#### erp_sale_return - 销售退货表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 退货单号 |
| status | INT | 状态（10未审核 20已审核） |
| customer_id | BIGINT | 客户ID（FK -> erp_customer） |
| order_id | BIGINT | 销售订单ID（FK -> erp_sale_order） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| return_time | DATETIME | 退货时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 合计价格 |
| refund_price | DECIMAL | 已退款金额 |

#### erp_sale_return_item - 销售退货项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| return_id | BIGINT | 销售退货ID（FK -> erp_sale_return） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 退货数量 |
| product_price | DECIMAL | 产品单价 |

---

### 库存相关表

#### erp_warehouse - 仓库表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 仓库编号（主键） |
| name | VARCHAR | 仓库名称 |
| address | VARCHAR | 仓库地址 |
| status | INT | 状态 |

#### erp_stock - 产品库存表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| count | DECIMAL | 库存数量 |

**说明**: product_id + warehouse_id 唯一确定一个库存记录

#### erp_stock_record - 库存明细表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| count | DECIMAL | 出入库数量（正数入库/负数出库） |
| total_count | DECIMAL | 变动后库存量 |
| biz_type | INT | 业务类型（见 ErpStockRecordBizTypeEnum） |
| biz_id | BIGINT | 业务编号 |
| biz_item_id | BIGINT | 业务项编号 |
| biz_no | VARCHAR | 业务单号 |

#### erp_stock_in - 其它入库表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 入库单号（QTRK+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| in_time | DATETIME | 入库时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 合计价格 |

#### erp_stock_in_item - 其它入库项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| in_id | BIGINT | 入库单ID（FK -> erp_stock_in） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 入库数量 |
| product_price | DECIMAL | 产品单价 |

#### erp_stock_out - 其它出库表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 出库单号（QCKD+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| out_time | DATETIME | 出库时间 |
| total_count | DECIMAL | 合计数量 |
| total_price | DECIMAL | 合计价格 |

#### erp_stock_out_item - 其它出库项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| out_id | BIGINT | 出库单ID（FK -> erp_stock_out） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 出库数量 |
| product_price | DECIMAL | 产品单价 |

#### erp_stock_move - 库存调拨表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 调拨单号（QCDB+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| from_warehouse_id | BIGINT | 调出仓库ID（FK -> erp_warehouse） |
| to_warehouse_id | BIGINT | 调入仓库ID（FK -> erp_warehouse） |
| move_time | DATETIME | 调拨时间 |
| total_count | DECIMAL | 合计数量 |

#### erp_stock_move_item - 库存调拨项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| move_id | BIGINT | 调拨单ID（FK -> erp_stock_move） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 调拨数量 |

#### erp_stock_check - 库存盘点表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 盘点单号（QCPD+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| warehouse_id | BIGINT | 仓库ID（FK -> erp_warehouse） |
| check_time | DATETIME | 盘点时间 |
| total_count | DECIMAL | 合计数量 |

#### erp_stock_check_item - 库存盘点项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| check_id | BIGINT | 盘点单ID（FK -> erp_stock_check） |
| product_id | BIGINT | 产品ID（FK -> erp_product） |
| count | DECIMAL | 盘点数量 |

---

### 财务相关表

#### erp_account - 结算账户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 账户编号（主键） |
| name | VARCHAR | 账户名称 |
| no | VARCHAR | 账户编号 |
| status | INT | 状态 |

#### erp_finance_payment - 付款单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 付款单号（FKD+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| supplier_id | BIGINT | 供应商ID（FK -> erp_supplier） |
| account_id | BIGINT | 付款账户ID（FK -> erp_account） |
| payment_time | DATETIME | 付款时间 |
| total_price | DECIMAL | 合计金额 |
| discount_price | DECIMAL | 优惠金额 |
| payment_price | DECIMAL | 实付金额 |

#### erp_finance_payment_item - 付款单项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| payment_id | BIGINT | 付款单ID（FK -> erp_finance_payment） |
| purchase_in_id | BIGINT | 关联采购入库单ID（FK -> erp_purchase_in） |
| price | DECIMAL | 付款金额 |

#### erp_finance_receipt - 收款单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| no | VARCHAR | 收款单号（SKD+yyyyMMdd+6位序号） |
| status | INT | 状态（10未审核 20已审核） |
| customer_id | BIGINT | 客户ID（FK -> erp_customer） |
| account_id | BIGINT | 收款账户ID（FK -> erp_account） |
| receipt_time | DATETIME | 收款时间 |
| total_price | DECIMAL | 合计金额 |
| discount_price | DECIMAL | 优惠金额 |
| receipt_price | DECIMAL | 实收金额 |

#### erp_finance_receipt_item - 收款单项表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 编号（主键） |
| receipt_id | BIGINT | 收款单ID（FK -> erp_finance_receipt） |
| sale_out_id | BIGINT | 关联销售出库单ID（FK -> erp_sale_out） |
| price | DECIMAL | 收款金额 |

---

## ER 关系图

### 产品域

```
erp_product_category (1) <-- (N) erp_product (N) --> (1) erp_product_unit
```

### 采购域

```
erp_supplier (1) <-- (N) erp_purchase_order (1) --> (N) erp_purchase_order_item
                           |
                           +--- (N) erp_purchase_in (1) --> (N) erp_purchase_in_item
                           |
                           +--- (N) erp_purchase_return (1) --> (N) erp_purchase_return_item
```

### 销售域

```
erp_customer (1) <-- (N) erp_sale_order (1) --> (N) erp_sale_order_item
                          |
                          +--- (N) erp_sale_out (1) --> (N) erp_sale_out_item
                          |
                          +--- (N) erp_sale_return (1) --> (N) erp_sale_return_item
```

### 库存域

```
erp_product (1) <-- (N) erp_stock (N) --> (1) erp_warehouse
                       erp_stock_record (N) --> (1) erp_product
                       erp_stock_record (N) --> (1) erp_warehouse

erp_warehouse (1) <-- (N) erp_stock_in / erp_stock_out / erp_stock_move / erp_stock_check
```

### 财务域

```
erp_account (1) <-- (N) erp_finance_payment (1) --> (N) erp_finance_payment_item --> erp_purchase_in
             (1) <-- (N) erp_finance_receipt (1) --> (N) erp_finance_receipt_item --> erp_sale_out

erp_supplier (1) <-- (N) erp_finance_payment
erp_customer (1) <-- (N) erp_finance_receipt
```

---

## 单据号规则

| 前缀 | 单据类型 | 格式 | 示例 |
|------|----------|------|------|
| CGDD | 采购订单 | CGDD + yyyyMMdd + 6位序号 | CGDD20260318000001 |
| XSDD | 销售订单 | XSDD + yyyyMMdd + 6位序号 | XSDD20260318000001 |
| QTRK | 其它入库 | QTRK + yyyyMMdd + 6位序号 | QTRK20260318000001 |
| QCKD | 其它出库 | QCKD + yyyyMMdd + 6位序号 | QCKD20260318000001 |
| QCDB | 库存调拨 | QCDB + yyyyMMdd + 6位序号 | QCDB20260318000001 |
| QCPD | 库存盘点 | QCPD + yyyyMMdd + 6位序号 | QCPD20260318000001 |
| FKD | 付款单 | FKD + yyyyMMdd + 6位序号 | FKD20260318000001 |
| SKD | 收款单 | SKD + yyyyMMdd + 6位序号 | SKD20260318000001 |

单据号通过 `ErpNoRedisDAO.generate()` 基于 Redis 生成，保证分布式环境下的唯一性和有序性。

---

## 状态枚举

### ErpAuditStatus - 审核状态

| 值 | 名称 | 说明 |
|----|------|------|
| 10 | PROCESS | 未审核 |
| 20 | APPROVE | 已审核 |

### ErpStockRecordBizTypeEnum - 库存记录业务类型

| 值 | 名称 | 说明 |
|----|------|------|
| 10 | PURCHASE_IN | 采购入库 |
| 11 | PURCHASE_IN_CANCEL | 采购入库（作废） |
| 12 | PURCHASE_RETURN | 采购退货 |
| 13 | PURCHASE_RETURN_CANCEL | 采购退货（作废） |
| 20 | SALE_OUT | 销售出库 |
| 21 | SALE_OUT_CANCEL | 销售出库（作废） |
| 22 | SALE_RETURN | 销售退货 |
| 23 | SALE_RETURN_CANCEL | 销售退货（作废） |
| 30 | STOCK_IN | 其它入库 |
| 31 | STOCK_IN_CANCEL | 其它入库（作废） |
| 32 | STOCK_OUT | 其它出库 |
| 33 | STOCK_OUT_CANCEL | 其它出库（作废） |
| 34 | STOCK_MOVE | 库存调拨 |
| 35 | STOCK_MOVE_CANCEL | 库存调拨（作废） |
