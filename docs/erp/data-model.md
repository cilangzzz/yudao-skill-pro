# 数据模型详情

> erp 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。模块定位为进销存一体化的企业资源计划：产品主数据 + 采购/销售全流程单据 + 仓库库存统一台账 + 财务付款收款结算。共 33 张数据表，全部为单模块布局（`yudao-module-erp` 无子模块），statistics 统计域不建表（走 XML Mapper 实时聚合）。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO        （抽象基类，yudao-spring-boot-starter-mybatis）
│   ├── creator      String         创建者（SysUser 的 id，插入时自动填充）
│   ├── createTime   LocalDateTime  创建时间（插入时自动填充）
│   ├── updater      String         更新者（更新时自动填充）
│   ├── updateTime   LocalDateTime  最后更新时间（插入/更新时自动填充）
│   └── deleted      Boolean        逻辑删除标记（@TableLogic）
│
cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO           （抽象基类，yudao-spring-boot-starter-biz-tenant）
│   └── 继承 BaseDO 全部字段
│   └── tenantId     Long           多租户编号
│
└── erp 模块全部 33 个 DO：统一继承 BaseDO
    ├── ErpProductDO / ErpProductCategoryDO / ErpProductUnitDO
    ├── ErpSupplierDO / ErpPurchaseOrderDO(Item) / ErpPurchaseInDO(Item) / ErpPurchaseReturnDO(Item)
    ├── ErpCustomerDO / ErpSaleOrderDO(Item) / ErpSaleOutDO(Item) / ErpSaleReturnDO(Item)
    ├── ErpWarehouseDO / ErpStockDO / ErpStockRecordDO / ErpStockInDO(Item) / ErpStockOutDO(Item)
    │   / ErpStockMoveDO(Item) / ErpStockCheckDO(Item)
    └── ErpAccountDO / ErpFinancePaymentDO(Item) / ErpFinanceReceiptDO(Item)
```

**使用规则**：

- **BaseDO**：不含 `tenant_id` 的表使用。erp 模块所有 33 张表均属此类——erp 表**不支持多租户**，产品、供应商、客户、单据等数据全库共享，DO 层没有任何一个类继承 `TenantBaseDO`。
- **TenantBaseDO**：需要租户隔离的表使用（`tenant_id` 列 + 租户插件自动拼 WHERE）。erp 表若未来需要租户隔离，需将继承改为 `TenantBaseDO` 并给表补 `tenant_id` 列，当前代码中没有这种用法。
- erp 全部表都通过 `@KeySequence("{表名}_seq")` 声明主键序列，供 Oracle/PostgreSQL/Kingbase/DB2/H2 等数据库自增使用（MySQL 下不生效、可忽略）；主键统一为 `id`（`@TableId`）。

## 2. 核心 DO 实体

按业务聚合分为 5 组：产品主数据、采购、销售、仓库库存、财务结算。33 个 DO 全部详细展开。

**公共约定**（适用于本节所有字段表）：

- 每张表除下列出的子类字段外，均含基类公共列：`creator`、`create_time`、`updater`、`update_time`、`deleted`（见第 1 节）。
- 数据库列为 MyBatis-Plus 驼峰转下划线的默认映射结果。
- 索引说明：erp 各表的建表 DDL **未包含在仓库 `sql/` 脚本中**（仓库脚本仅含 erp 相关字典数据），因此除主键与正文中明确给出代码依据的"逻辑唯一"约束外，不罗列未经佐证的索引。各表主键均为 `id`，下文不再重复。
- 明细表命名不统一：purchase/sale 域为复数 `_items`（如 `erp_purchase_order_items`），stock/finance 域为单数 `_item`（如 `erp_stock_in_item`）。
- 金额字段除特别说明外单位均为元，数量字段用 `BigDecimal` 以支持小数计量。

### 2.1 产品主数据聚合

主数据三者构成"分类 → 产品 → 单位"的引用关系，被采购、销售、库存、财务全部单据引用。

#### ErpProductDO (erp_product)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 产品编号 |
| name | String | name | 产品名称 |
| barCode | String | bar_code | 产品条码 |
| categoryId | Long | category_id | 产品分类编号，关联 ErpProductCategoryDO |
| unitId | Long | unit_id | 单位编号，关联 ErpProductUnitDO |
| status | Integer | status | 产品状态，枚举 CommonStatusEnum（开启/关闭） |
| standard | String | standard | 产品规格 |
| remark | String | remark | 产品备注 |
| expiryDay | Integer | expiry_day | 保质期天数 |
| weight | BigDecimal | weight | 基础重量（kg） |
| purchasePrice | BigDecimal | purchase_price | 采购价格，单位：元 |
| salePrice | BigDecimal | sale_price | 销售价格，单位：元 |
| minPrice | BigDecimal | min_price | 最低价格，单位：元 |

**继承**: BaseDO
**索引**: 无其他代码声明。被全模块单据明细以 `productId` 引用，是 erp 的核心主数据。

#### ErpProductCategoryDO (erp_product_category)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分类编号 |
| parentId | Long | parent_id | 父分类编号，0 表示根节点（常量 `PARENT_ID_ROOT = 0L`），自关联构成分类树 |
| name | String | name | 分类名称 |
| code | String | code | 分类编码 |
| sort | Integer | sort | 分类排序 |
| status | Integer | status | 开启状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 无其他代码声明；`parent_id` 自关联实现树形结构。

#### ErpProductUnitDO (erp_product_unit)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 单位编号 |
| name | String | name | 单位名字 |
| status | Integer | status | 单位状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 无其他代码声明。

### 2.2 供应商与采购聚合

采购域为"订单 → 入库 / 退货"三单结构，两张下游单据均通过 `orderId` 回指订单，并通过明细行的 `orderItemId` 回写订单执行进度。

#### ErpSupplierDO (erp_supplier)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 供应商编号 |
| name | String | name | 供应商名称 |
| contact | String | contact | 联系人 |
| mobile | String | mobile | 手机号码 |
| telephone | String | telephone | 联系电话 |
| email | String | email | 电子邮箱 |
| fax | String | fax | 传真 |
| remark | String | remark | 备注 |
| status | Integer | status | 开启状态，枚举 CommonStatusEnum |
| sort | Integer | sort | 排序 |
| taxNo | String | tax_no | 纳税人识别号 |
| taxPercent | BigDecimal | tax_percent | 税率 |
| bankName | String | bank_name | 开户行 |
| bankAccount | String | bank_account | 开户账号 |
| bankAddress | String | bank_address | 开户地址 |

**继承**: BaseDO
**索引**: 无其他代码声明。被采购三单的 `supplierId`、其它入库单、付款单引用。

#### ErpPurchaseOrderDO (erp_purchase_order)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 采购订单号 |
| status | Integer | status | 采购状态，枚举 ErpAuditStatus（10 未审核 / 20 已审核，字典 erp_audit_status） |
| supplierId | Long | supplier_id | 供应商编号，关联 ErpSupplierDO |
| accountId | Long | account_id | 结算账户编号，关联 ErpAccountDO |
| orderTime | LocalDateTime | order_time | 下单时间 |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 最终合计价格（元）= totalProductPrice + totalTaxPrice - discountPrice |
| totalProductPrice | BigDecimal | total_product_price | 合计产品价格（元） |
| totalTaxPrice | BigDecimal | total_tax_price | 合计税额（元） |
| discountPercent | BigDecimal | discount_percent | 优惠率，百分比 |
| discountPrice | BigDecimal | discount_price | 优惠金额（元）= (totalProductPrice + totalTaxPrice) * discountPercent |
| depositPrice | BigDecimal | deposit_price | 定金金额（元） |
| fileUrl | String | file_url | 附件地址 |
| remark | String | remark | 备注 |
| inCount | BigDecimal | in_count | 采购入库数量（执行进度，由入库单回写） |
| returnCount | BigDecimal | return_count | 采购退货数量（执行进度，由退货单回写） |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpPurchaseOrderItemDO (erp_purchase_order_items)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| orderId | Long | order_id | 采购订单编号，关联 ErpPurchaseOrderDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单位单价（元） |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总价（元）= productPrice * count |
| taxPercent | BigDecimal | tax_percent | 税率，百分比 |
| taxPrice | BigDecimal | tax_price | 税额（元）= totalPrice * taxPercent |
| remark | String | remark | 备注 |
| inCount | BigDecimal | in_count | 采购入库数量（进度） |
| returnCount | BigDecimal | return_count | 采购退货数量（进度） |

**继承**: BaseDO
**索引**: 无其他代码声明；`order_id` 为逻辑外键（1:N 主从关联），`in_count`/`return_count` 被入库/退货明细行回写。

#### ErpPurchaseInDO (erp_purchase_in)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 采购入库单号 |
| status | Integer | status | 入库状态，枚举 ErpAuditStatus |
| supplierId | Long | supplier_id | 供应商编号，关联 ErpSupplierDO |
| accountId | Long | account_id | 结算账户编号，关联 ErpAccountDO |
| inTime | LocalDateTime | in_time | 入库时间 |
| orderId | Long | order_id | 采购订单编号，关联 ErpPurchaseOrderDO |
| orderNo | String | order_no | 采购订单号，冗余 ErpPurchaseOrderDO.no |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 最终合计价格（元）= totalProductPrice + totalTaxPrice - discountPrice + otherPrice |
| paymentPrice | BigDecimal | payment_price | 已支付金额（元），与付款单 ErpFinancePaymentDO 联动记录 |
| totalProductPrice | BigDecimal | total_product_price | 合计产品价格（元） |
| totalTaxPrice | BigDecimal | total_tax_price | 合计税额（元） |
| discountPercent | BigDecimal | discount_percent | 优惠率，百分比 |
| discountPrice | BigDecimal | discount_price | 优惠金额（元）= (totalProductPrice + totalTaxPrice) * discountPercent |
| otherPrice | BigDecimal | other_price | 其它金额（元） |
| fileUrl | String | file_url | 附件地址 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。审核后通过 ErpStockRecordService.createStockRecord 记入库存台账（bizType = 70 采购入库）。

#### ErpPurchaseInItemDO (erp_purchase_in_items)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| inId | Long | in_id | 采购入库编号，关联 ErpPurchaseInDO |
| orderItemId | Long | order_item_id | 采购订单项编号，关联 ErpPurchaseOrderItemDO（用于回写订单项入库数量） |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单位单价（元） |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总价（元）= productPrice * count |
| taxPercent | BigDecimal | tax_percent | 税率，百分比 |
| taxPrice | BigDecimal | tax_price | 税额（元）= totalPrice * taxPercent |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpPurchaseReturnDO (erp_purchase_return)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 采购退货单号 |
| status | Integer | status | 退货状态，枚举 ErpAuditStatus |
| supplierId | Long | supplier_id | 供应商编号，关联 ErpSupplierDO |
| accountId | Long | account_id | 结算账户编号，关联 ErpAccountDO |
| returnTime | LocalDateTime | return_time | 退货时间 |
| orderId | Long | order_id | 采购订单编号，关联 ErpPurchaseOrderDO |
| orderNo | String | order_no | 采购订单号，冗余 ErpPurchaseOrderDO.no |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 最终合计价格（元）= totalProductPrice + totalTaxPrice - discountPrice + otherPrice |
| refundPrice | BigDecimal | refund_price | 已退款金额（元），与付款单 ErpFinancePaymentDO 联动记录 |
| totalProductPrice | BigDecimal | total_product_price | 合计产品价格（元） |
| totalTaxPrice | BigDecimal | total_tax_price | 合计税额（元） |
| discountPercent | BigDecimal | discount_percent | 优惠率，百分比 |
| discountPrice | BigDecimal | discount_price | 优惠金额（元）= (totalProductPrice + totalTaxPrice) * discountPercent |
| otherPrice | BigDecimal | other_price | 其它金额（元） |
| fileUrl | String | file_url | 附件地址 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。审核后记入库存台账（bizType = 80 采购退货出库）。

#### ErpPurchaseReturnItemDO (erp_purchase_return_items)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| returnId | Long | return_id | 采购退货编号，关联 ErpPurchaseReturnDO |
| orderItemId | Long | order_item_id | 采购订单项编号，关联 ErpPurchaseOrderItemDO（用于回写订单项退货数量） |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单位单价（元） |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总价（元）= productPrice * count |
| taxPercent | BigDecimal | tax_percent | 税率，百分比 |
| taxPrice | BigDecimal | tax_price | 税额（元）= totalPrice * taxPercent |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

### 2.3 客户与销售聚合

销售域与采购域镜像对称："订单 → 出库 / 退货"三单结构，`saleUserId` 关联 system 模块的管理员（AdminUserDO）。

#### ErpCustomerDO (erp_customer)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 客户编号 |
| name | String | name | 客户名称 |
| contact | String | contact | 联系人 |
| mobile | String | mobile | 手机号码 |
| telephone | String | telephone | 联系电话 |
| email | String | email | 电子邮箱 |
| fax | String | fax | 传真 |
| remark | String | remark | 备注 |
| status | Integer | status | 开启状态，枚举 CommonStatusEnum |
| sort | Integer | sort | 排序 |
| taxNo | String | tax_no | 纳税人识别号 |
| taxPercent | BigDecimal | tax_percent | 税率 |
| bankName | String | bank_name | 开户行 |
| bankAccount | String | bank_account | 开户账号 |
| bankAddress | String | bank_address | 开户地址 |

**继承**: BaseDO
**索引**: 无其他代码声明。字段结构与 ErpSupplierDO 完全一致。被销售三单的 `customerId`、其它出库单、收款单引用。

#### ErpSaleOrderDO (erp_sale_order)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 销售订单号 |
| status | Integer | status | 销售状态，枚举 ErpAuditStatus |
| customerId | Long | customer_id | 客户编号，关联 ErpCustomerDO |
| accountId | Long | account_id | 结算账户编号，关联 ErpAccountDO |
| saleUserId | Long | sale_user_id | 销售员编号，关联 AdminUserDO（system 模块） |
| orderTime | LocalDateTime | order_time | 下单时间 |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 最终合计价格（元）= totalProductPrice + totalTaxPrice - discountPrice |
| totalProductPrice | BigDecimal | total_product_price | 合计产品价格（元） |
| totalTaxPrice | BigDecimal | total_tax_price | 合计税额（元） |
| discountPercent | BigDecimal | discount_percent | 优惠率，百分比 |
| discountPrice | BigDecimal | discount_price | 优惠金额（元）= (totalProductPrice + totalTaxPrice) * discountPercent |
| depositPrice | BigDecimal | deposit_price | 定金金额（元） |
| fileUrl | String | file_url | 附件地址 |
| remark | String | remark | 备注 |
| outCount | BigDecimal | out_count | 销售出库数量（执行进度） |
| returnCount | BigDecimal | return_count | 销售退货数量（执行进度） |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpSaleOrderItemDO (erp_sale_order_items)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| orderId | Long | order_id | 销售订单编号，关联 ErpSaleOrderDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单位单价（元） |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总价（元）= productPrice * count |
| taxPercent | BigDecimal | tax_percent | 税率，百分比 |
| taxPrice | BigDecimal | tax_price | 税额（元）= totalPrice * taxPercent |
| remark | String | remark | 备注 |
| outCount | BigDecimal | out_count | 销售出库数量（进度） |
| returnCount | BigDecimal | return_count | 销售退货数量（进度） |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpSaleOutDO (erp_sale_out)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 销售出库单号 |
| status | Integer | status | 出库状态，枚举 ErpAuditStatus |
| customerId | Long | customer_id | 客户编号，关联 ErpCustomerDO |
| accountId | Long | account_id | 结算账户编号，关联 ErpAccountDO |
| saleUserId | Long | sale_user_id | 销售员编号，关联 AdminUserDO（system 模块） |
| outTime | LocalDateTime | out_time | 出库时间 |
| orderId | Long | order_id | 销售订单编号，关联 ErpSaleOrderDO |
| orderNo | String | order_no | 销售订单号，冗余 ErpSaleOrderDO.no |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 最终合计价格（元）= totalProductPrice + totalTaxPrice - discountPrice + otherPrice |
| receiptPrice | BigDecimal | receipt_price | 已收款金额（元），与收款单 ErpFinanceReceiptDO 联动记录 |
| totalProductPrice | BigDecimal | total_product_price | 合计产品价格（元） |
| totalTaxPrice | BigDecimal | total_tax_price | 合计税额（元） |
| discountPercent | BigDecimal | discount_percent | 优惠率，百分比 |
| discountPrice | BigDecimal | discount_price | 优惠金额（元）= (totalProductPrice + totalTaxPrice) * discountPercent |
| otherPrice | BigDecimal | other_price | 其它金额（元） |
| fileUrl | String | file_url | 附件地址 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。审核后记入库存台账（bizType = 50 销售出库）。

#### ErpSaleOutItemDO (erp_sale_out_items)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| outId | Long | out_id | 销售出库编号，关联 ErpSaleOutDO（注意：代码 javadoc 误写为关联 ErpStockOutDO，属复制粘贴残留） |
| orderItemId | Long | order_item_id | 销售订单项编号，关联 ErpSaleOrderItemDO（用于回写订单项出库数量） |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单位单价（元） |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总价（元）= productPrice * count |
| taxPercent | BigDecimal | tax_percent | 税率，百分比 |
| taxPrice | BigDecimal | tax_price | 税额（元）= totalPrice * taxPercent |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpSaleReturnDO (erp_sale_return)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 销售退货单号 |
| status | Integer | status | 退货状态，枚举 ErpAuditStatus |
| customerId | Long | customer_id | 客户编号，关联 ErpCustomerDO |
| accountId | Long | account_id | 结算账户编号，关联 ErpAccountDO |
| saleUserId | Long | sale_user_id | 销售员编号，关联 AdminUserDO（system 模块） |
| returnTime | LocalDateTime | return_time | 退货时间 |
| orderId | Long | order_id | 销售订单编号，关联 ErpSaleOrderDO |
| orderNo | String | order_no | 销售订单号，冗余 ErpSaleOrderDO.no |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 最终合计价格（元）= totalProductPrice + totalTaxPrice - discountPrice + otherPrice |
| refundPrice | BigDecimal | refund_price | 已退款金额（元），与收款单 ErpFinanceReceiptDO 联动记录 |
| totalProductPrice | BigDecimal | total_product_price | 合计产品价格（元） |
| totalTaxPrice | BigDecimal | total_tax_price | 合计税额（元） |
| discountPercent | BigDecimal | discount_percent | 优惠率，百分比 |
| discountPrice | BigDecimal | discount_price | 优惠金额（元）= (totalProductPrice + totalTaxPrice) * discountPercent |
| otherPrice | BigDecimal | other_price | 其它金额（元） |
| fileUrl | String | file_url | 附件地址 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。审核后记入库存台账（bizType = 60 销售退货入库）。

#### ErpSaleReturnItemDO (erp_sale_return_items)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| returnId | Long | return_id | 销售退货编号，关联 ErpSaleReturnDO |
| orderItemId | Long | order_item_id | 销售订单项编号，关联 ErpSaleOrderItemDO（用于回写订单项退货数量） |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单位单价（元） |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总价（元）= productPrice * count |
| taxPercent | BigDecimal | tax_percent | 税率，百分比 |
| taxPrice | BigDecimal | tax_price | 税额（元）= totalPrice * taxPercent |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

### 2.4 仓库与库存聚合

库存采用"实时台账（erp_stock）+ 流水明细（erp_stock_record）"双表结构：所有出入库业务统一经 `ErpStockRecordService.createStockRecord(ErpStockRecordCreateReqBO)` 入账，count 正数为入库、负数为出库，库存不足抛 `STOCK_COUNT_NEGATIVE` 错误。调用方共 8 个 ServiceImpl：purchase-in / purchase-return / sale-out / sale-return / stock-in / stock-out / stock-move / stock-check。

#### ErpWarehouseDO (erp_warehouse)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 仓库编号 |
| name | String | name | 仓库名称 |
| address | String | address | 仓库地址 |
| sort | Long | sort | 排序（注意为 Long，与其他主数据的 Integer 不一致） |
| remark | String | remark | 备注 |
| principal | String | principal | 负责人 |
| warehousePrice | BigDecimal | warehouse_price | 仓储费，单位：元 |
| truckagePrice | BigDecimal | truckage_price | 搬运费，单位：元 |
| status | Integer | status | 开启状态，枚举 CommonStatusEnum |
| defaultStatus | Boolean | default_status | 是否默认仓库 |

**继承**: BaseDO
**索引**: 无其他代码声明。被所有单据明细行的 `warehouseId` 及 `erp_stock` 引用；默认仓库标记由 account/warehouse 的 update-default-status 端点维护。

#### ErpStockDO (erp_stock)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| count | BigDecimal | count | 库存数量 |

**继承**: BaseDO
**索引**: **逻辑唯一** `(product_id, warehouse_id)`——`ErpStockMapper.selectByProductIdAndWarehouseId` 使用 `selectOne` 按"产品 + 仓库"定位唯一库存行；数量变更走 `updateCountIncrement` 原子增减（SQL 层 `count = count + ?`），并发下不会丢更新。

#### ErpStockRecordDO (erp_stock_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| count | BigDecimal | count | 出入库数量：正数表示入库，负数表示出库 |
| totalCount | BigDecimal | total_count | 总库存量（本次出入库之后该仓库该产品的当前库存） |
| bizType | Integer | biz_type | 业务类型，枚举 ErpStockRecordBizTypeEnum（字典 erp_stock_record_biz_type） |
| bizId | Long | biz_id | 业务编号（如 ErpStockInDO 的 id） |
| bizItemId | Long | biz_item_id | 业务项编号（如 ErpStockInItemDO 的 id） |
| bizNo | String | biz_no | 业务单号（如 ErpStockInDO 的 no） |

**继承**: BaseDO
**索引**: 无其他代码声明。`biz_type + biz_id + biz_item_id` 构成**多态关联**，指向 8 类业务单据：10/11 其它入库（作废）、20/21 其它出库（作废）、30-33 调拨入库/出库（作废）、40-43 盘盈入库/盘亏出库（作废）、50/51 销售出库（作废）、60/61 销售退货入库（作废）、70/71 采购入库（作废）、80/81 采购退货出库（作废）。

#### ErpStockInDO (erp_stock_in)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 入库编号 |
| no | String | no | 入库单号 |
| supplierId | Long | supplier_id | 供应商编号，关联 ErpSupplierDO |
| inTime | LocalDateTime | in_time | 入库时间 |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| status | Integer | status | 状态，枚举 ErpAuditStatus |
| remark | String | remark | 备注 |
| fileUrl | String | file_url | 附件 URL |

**继承**: BaseDO
**索引**: 无其他代码声明。"其它入库"业务单，审核后记台账（bizType = 10）。

#### ErpStockInItemDO (erp_stock_in_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 入库项编号 |
| inId | Long | in_id | 入库编号，关联 ErpStockInDO |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单价 |
| count | BigDecimal | count | 产品数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpStockOutDO (erp_stock_out)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 出库编号 |
| no | String | no | 出库单号 |
| customerId | Long | customer_id | 客户编号（代码标注 TODO 芋艿：待关联，目前仅存值不校验） |
| outTime | LocalDateTime | out_time | 出库时间 |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| status | Integer | status | 状态，枚举 ErpAuditStatus |
| remark | String | remark | 备注 |
| fileUrl | String | file_url | 附件 URL |

**继承**: BaseDO
**索引**: 无其他代码声明。"其它出库"业务单，审核后记台账（bizType = 20）。注意 ErpStockMoveController 的错误码复用了本表的 1_030_402_xxx 段。

#### ErpStockOutItemDO (erp_stock_out_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 出库项编号 |
| outId | Long | out_id | 出库编号，关联 ErpStockOutDO |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单价 |
| count | BigDecimal | count | 产品数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpStockMoveDO (erp_stock_move)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 调拨编号 |
| no | String | no | 调拨单号 |
| moveTime | LocalDateTime | move_time | 调拨时间 |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| status | Integer | status | 状态，枚举 ErpAuditStatus |
| remark | String | remark | 备注 |
| fileUrl | String | file_url | 附件 URL |

**继承**: BaseDO
**索引**: 无其他代码声明。库存调拨单（接口路径 `/erp/stock-move`；注意 ErpStockCheckController 的 Swagger @Tag 误写为"库存调拨单"，实际调拨单在本表）。

#### ErpStockMoveItemDO (erp_stock_move_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 调拨项编号 |
| moveId | Long | move_id | 调拨编号，关联 ErpStockMoveDO |
| fromWarehouseId | Long | from_warehouse_id | 调出仓库编号，关联 ErpWarehouseDO |
| toWarehouseId | Long | to_warehouse_id | 调入仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单价 |
| count | BigDecimal | count | 产品数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。审核后按"调出仓库记 bizType = 32 出库、调入仓库记 bizType = 30 入库"两笔流水入账。

#### ErpStockCheckDO (erp_stock_check)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 盘点编号 |
| no | String | no | 盘点单号 |
| checkTime | LocalDateTime | check_time | 盘点时间 |
| totalCount | BigDecimal | total_count | 合计数量 |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| status | Integer | status | 状态，枚举 ErpAuditStatus |
| remark | String | remark | 备注 |
| fileUrl | String | file_url | 附件 URL |

**继承**: BaseDO
**索引**: 无其他代码声明。库存盘点单，审核后按盈亏记台账（盘盈 bizType = 40 / 盘亏 bizType = 42）。

#### ErpStockCheckItemDO (erp_stock_check_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 盘点项编号 |
| checkId | Long | check_id | 盘点编号，关联 ErpStockCheckDO |
| warehouseId | Long | warehouse_id | 仓库编号，关联 ErpWarehouseDO |
| productId | Long | product_id | 产品编号，关联 ErpProductDO |
| productUnitId | Long | product_unit_id | 产品单位编号，冗余 ErpProductDO.unitId |
| productPrice | BigDecimal | product_price | 产品单价 |
| stockCount | BigDecimal | stock_count | 账面数量（当前库存） |
| actualCount | BigDecimal | actual_count | 实际数量（实际库存） |
| count | BigDecimal | count | 盈亏数量（代码注释：count = stockCount - actualCount） |
| totalPrice | BigDecimal | total_price | 合计金额，单位：元 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

### 2.5 财务结算聚合

财务域为"付款单（对应采购）/ 收款单（对应销售）+ 结算账户"结构，通过明细行的 `bizType + bizId` 多态关联采购入库/退货单、销售出库/退货单。

#### ErpAccountDO (erp_account)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 结算账户编号 |
| name | String | name | 账户名称 |
| no | String | no | 账户编码 |
| remark | String | remark | 备注 |
| status | Integer | status | 开启状态，枚举 CommonStatusEnum |
| sort | Integer | sort | 排序 |
| defaultStatus | Boolean | default_status | 是否默认账户 |

**继承**: BaseDO
**索引**: 无其他代码声明。被采购/销售全部单据的 `accountId`、付款单、收款单引用；默认账户由 update-default-status 端点维护（该端点及 simple-list 无 @PreAuthorize，仅登录即可）。

#### ErpFinancePaymentDO (erp_finance_payment)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 付款单号 |
| status | Integer | status | 付款状态，枚举 ErpAuditStatus |
| paymentTime | LocalDateTime | payment_time | 付款时间 |
| financeUserId | Long | finance_user_id | 财务人员编号，关联 AdminUserDO（system 模块） |
| supplierId | Long | supplier_id | 供应商编号，关联 ErpSupplierDO |
| accountId | Long | account_id | 付款账户编号，关联 ErpAccountDO |
| totalPrice | BigDecimal | total_price | 合计价格，单位：元（代码注释如此；明细行注释却写"单位：分"，金额单位注释在 finance 域内部不一致） |
| discountPrice | BigDecimal | discount_price | 优惠金额，单位：元 |
| paymentPrice | BigDecimal | payment_price | 实付金额，代码注释：单位：分，paymentPrice = totalPrice - discountPrice |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpFinancePaymentItemDO (erp_finance_payment_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（javadoc 误写为"入库项编号"，复制粘贴残留） |
| paymentId | Long | payment_id | 付款单编号，关联 ErpFinancePaymentDO |
| bizType | Integer | biz_type | 业务类型，枚举 ErpBizTypeEnum 的采购入库、退货 |
| bizId | Long | biz_id | 业务编号（如 ErpPurchaseInDO 的 id） |
| bizNo | String | biz_no | 业务单号（如 ErpPurchaseInDO 的 no） |
| totalPrice | BigDecimal | total_price | 应付金额，代码注释：单位：分 |
| paidPrice | BigDecimal | paid_price | 已付金额，代码注释：单位：分 |
| paymentPrice | BigDecimal | payment_price | 本次付款，代码注释：单位：分 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。`biz_type + biz_id` 多态指向采购入库单/采购退货单。

#### ErpFinanceReceiptDO (erp_finance_receipt)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| no | String | no | 收款单号 |
| status | Integer | status | 收款状态，枚举 ErpAuditStatus |
| receiptTime | LocalDateTime | receipt_time | 收款时间 |
| financeUserId | Long | finance_user_id | 财务人员编号，关联 AdminUserDO（system 模块） |
| customerId | Long | customer_id | 客户编号，关联 ErpCustomerDO |
| accountId | Long | account_id | 收款账户编号，关联 ErpAccountDO |
| totalPrice | BigDecimal | total_price | 合计价格，单位：元 |
| discountPrice | BigDecimal | discount_price | 优惠金额，单位：元 |
| receiptPrice | BigDecimal | receipt_price | 实付（实收）金额，代码注释：单位：分，receiptPrice = totalPrice - discountPrice |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。

#### ErpFinanceReceiptItemDO (erp_finance_receipt_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号（javadoc 误写为"入库项编号"，复制粘贴残留） |
| receiptId | Long | receipt_id | 收款单编号，关联 ErpFinanceReceiptDO |
| bizType | Integer | biz_type | 业务类型，枚举 ErpBizTypeEnum 的销售出库、退货 |
| bizId | Long | biz_id | 业务编号（如 ErpSaleOutDO 的 id） |
| bizNo | String | biz_no | 业务单号（如 ErpSaleOutDO 的 no） |
| totalPrice | BigDecimal | total_price | 应收金额，代码注释：单位：分 |
| receiptedPrice | BigDecimal | receipted_price | 已收金额，代码注释：单位：分 |
| receiptPrice | BigDecimal | receipt_price | 本次收款，代码注释：单位：分 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无其他代码声明。`biz_type + biz_id` 多态指向销售出库单/销售退货单。

## 3. 实体关系

**主数据引用**（被全部业务单据引用）：

```
erp_product_category (parent_id 自关联树)
        ▲ category_id
   erp_product ──unit_id──> erp_product_unit
        ▲ product_id（所有明细行）
erp_product_unit ── 冗余于各明细行 product_unit_id
```

**采购链**：

```
erp_supplier ◄──supplier_id── erp_purchase_order ──account_id──> erp_account
                                    │ 1:N (order_id)
                                    ▼
                          erp_purchase_order_items ◄──order_item_id──（回写 in_count / return_count 进度）
                                    ▲ product_id            ▲ warehouse_id
                                    │                       │
erp_purchase_order ──order_id──> erp_purchase_in ──1:N(in_id)──> erp_purchase_in_items
erp_purchase_order ──order_id──> erp_purchase_return ──1:N(return_id)──> erp_purchase_return_items
        （purchase_in / purchase_return 明细行均携带 warehouse_id、product_id，
          审核后经 ErpStockRecordService 记入 erp_stock / erp_stock_record）
```

**销售链**（与采购链镜像，supplier 换成 customer，入库换成出库）：

```
erp_customer ◄──customer_id── erp_sale_order ◄──sale_user_id── system.AdminUserDO
                                    │ 1:N (order_id)
                                    ▼
                          erp_sale_order_items ◄──order_item_id──（回写 out_count / return_count 进度）
erp_sale_order ──order_id──> erp_sale_out ──1:N(out_id)──> erp_sale_out_items
erp_sale_order ──order_id──> erp_sale_return ──1:N(return_id)──> erp_sale_return_items
```

**库存统一台账**（核心枢纽）：

```
erp_warehouse ◄──warehouse_id──┐
                               ▼
erp_stock（product_id + warehouse_id 逻辑唯一，实库存）
erp_stock_record（biz_type + biz_id + biz_item_id + biz_no 多态关联业务单据）
    ▲ 8 类业务来源（createStockRecord 统一入口，count 正=入 / 负=出）：
      10 其它入库 · 20 其它出库 · 30/32 调拨入/出库 · 40/42 盘盈/盘亏
      50 销售出库 · 60 销售退货入库 · 70 采购入库 · 80 采购退货出库
      （各对应 erp_stock_in / erp_stock_out / erp_stock_move / erp_stock_check /
        erp_sale_out / erp_sale_return / erp_purchase_in / erp_purchase_return）
```

**财务结算链**：

```
erp_supplier ◄──supplier_id── erp_finance_payment ──1:N(payment_id)── erp_finance_payment_item
erp_customer ◄──customer_id── erp_finance_receipt  ──1:N(receipt_id)── erp_finance_receipt_item
两者均 ──account_id──> erp_account，finance_user_id ──> system.AdminUserDO
明细行 biz_type + biz_id 多态指向：
  payment_item → 采购入库单(erp_purchase_in) / 采购退货单(erp_purchase_return)
  receipt_item → 销售出库单(erp_sale_out) / 销售退货单(erp_sale_return)
付款/收款金额回写对应业务单的 payment_price / refund_price / receipt_price 字段
```

**跨模块关联**：erp 无对外 api 包，仅上游依赖 yudao-module-system——`sale_user_id`、`finance_user_id`、`creator`/`updater` 均指向 system 的管理员（AdminUserApi 共 19 处调用）；下游仅 yudao-server 装配引用。statistics 统计域不建表，直接对上述业务表做 XML Mapper 聚合查询。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|------|
| erp_product | ErpProductDO | 产品 |
| erp_product_category | ErpProductCategoryDO | 产品分类（parent_id 自关联树） |
| erp_product_unit | ErpProductUnitDO | 产品单位 |
| erp_supplier | ErpSupplierDO | 供应商 |
| erp_purchase_order | ErpPurchaseOrderDO | 采购订单 |
| erp_purchase_order_items | ErpPurchaseOrderItemDO | 采购订单项（复数 _items 命名） |
| erp_purchase_in | ErpPurchaseInDO | 采购入库单 |
| erp_purchase_in_items | ErpPurchaseInItemDO | 采购入库项 |
| erp_purchase_return | ErpPurchaseReturnDO | 采购退货单（出库方向） |
| erp_purchase_return_items | ErpPurchaseReturnItemDO | 采购退货项 |
| erp_customer | ErpCustomerDO | 客户 |
| erp_sale_order | ErpSaleOrderDO | 销售订单 |
| erp_sale_order_items | ErpSaleOrderItemDO | 销售订单项 |
| erp_sale_out | ErpSaleOutDO | 销售出库单 |
| erp_sale_out_items | ErpSaleOutItemDO | 销售出库项 |
| erp_sale_return | ErpSaleReturnDO | 销售退货单（入库方向） |
| erp_sale_return_items | ErpSaleReturnItemDO | 销售退货项 |
| erp_warehouse | ErpWarehouseDO | 仓库 |
| erp_stock | ErpStockDO | 产品实时库存（product_id + warehouse_id 逻辑唯一） |
| erp_stock_record | ErpStockRecordDO | 产品库存明细账（8 类业务多态流水） |
| erp_stock_in | ErpStockInDO | 其它入库单 |
| erp_stock_in_item | ErpStockInItemDO | 其它入库项（单数 _item 命名） |
| erp_stock_out | ErpStockOutDO | 其它出库单 |
| erp_stock_out_item | ErpStockOutItemDO | 其它出库项 |
| erp_stock_move | ErpStockMoveDO | 库存调拨单 |
| erp_stock_move_item | ErpStockMoveItemDO | 库存调拨项 |
| erp_stock_check | ErpStockCheckDO | 库存盘点单 |
| erp_stock_check_item | ErpStockCheckItemDO | 库存盘点项 |
| erp_account | ErpAccountDO | 结算账户 |
| erp_finance_payment | ErpFinancePaymentDO | 付款单 |
| erp_finance_payment_item | ErpFinancePaymentItemDO | 付款项 |
| erp_finance_receipt | ErpFinanceReceiptDO | 收款单 |
| erp_finance_receipt_item | ErpFinanceReceiptItemDO | 收款项 |

> 注：statistics 统计域无独立数据表，统计查询直接基于上述业务表（Mapper XML 位于 `src/main/resources/mapper/statistics/`）。
