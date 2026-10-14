# ERP 企业资源管理模块 (erp)

> 企业资源计划（ERP）模块：覆盖产品主数据、采购（订单/入库/退货）、销售（订单/出库/退货）、仓库库存（其它出入库/调拨/盘点/流水台账）与财务结算（付款/收款）的一体化管理。

## 模块概述
- **模块路径**: yudao-module-erp
- **业务定位**: 提供中小企业进销存 + 财务结算能力。以"单据驱动"为核心：采购订单 → 采购入库 → 付款单、销售订单 → 销售出库 → 收款单，单据间通过订单项回写（inCount/outCount/returnCount）联动数量控制；所有库存变动统一经由库存台账（erp_stock + erp_stock_record）记账。业务单据均为"未审核/已审核"两态审核流（审核/反审核）。
- **技术栈**: Spring Boot 2.7.18（JDK8 版本，仓库 revision 2026.09-jdk8-SNAPSHOT）/ MyBatis-Plus（yudao-spring-boot-starter-mybatis）/ springdoc-openapi（Swagger v3 注解）/ EasyExcel（starter-excel）/ Redis（starter-redis）；统计查询使用原生 XML Mapper。

## 设计原则
| 原则 | 说明 |
|-----|------|
| 单据-明细主子表 | 所有业务单据（订单/出入库/退货/付款收款）均为主表 + 明细子表两张表，明细随主表级联保存与删除 |
| 统一库存台账 | 8 类出入库单据不直接改库存，统一调用 `ErpStockRecordService.createStockRecord`（入参 `ErpStockRecordCreateReqBO`）完成"库存增减 + 流水写入"，保证 erp_stock 与 erp_stock_record 一致 |
| 两态审核状态机 | 单据统一使用 `ErpAuditStatus`（10 未审核 / 20 已审核）+ 字典 `erp_audit_status`；已审核单据禁止改删，反审核校验下游单据是否存在 |
| 数量联动防超扣 | 订单明细维护 inCount/outCount/returnCount 累计字段，入库/出库/退货时校验"不得超过最大允许数量"，删除时回滚累计值 |
| 全部 DO 继承 BaseDO | ERP 表不含 tenant_id，不支持多租户隔离；权限统一为 `erp:{功能}:{操作}` 五段式操作（create/update/delete/query/export 及 update-status 等） |

## 核心功能点
| 功能域 | 说明 | 关键实体 |
|-----|------|---------|
| 产品管理 | 产品、产品分类（树形）、产品单位维护；产品含采购价/销售价/最低价与保质期 | ErpProductDO、ErpProductCategoryDO、ErpProductUnitDO |
| 采购管理 | 供应商档案；采购订单 → 采购入库 → 采购退货全流程，含审核/反审核与数量校验 | ErpSupplierDO、ErpPurchaseOrderDO、ErpPurchaseInDO、ErpPurchaseReturnDO |
| 销售管理 | 客户档案；销售订单 → 销售出库 → 销售退货全流程，支持销售员（saleUserId）归属 | ErpCustomerDO、ErpSaleOrderDO、ErpSaleOutDO、ErpSaleReturnDO |
| 仓库库存 | 仓库档案、产品库存（按仓库+产品）、其它入库/出库、库存调拨（跨仓库）、库存盘点（差异回补）、库存流水明细 | ErpWarehouseDO、ErpStockDO、ErpStockInDO、ErpStockOutDO、ErpStockMoveDO、ErpStockCheckDO、ErpStockRecordDO |
| 财务管理 | 结算账户、付款单（对采购入库/退货核销）、收款单（对销售出库/退货核销），明细按业务单（bizType/bizId）核销金额 | ErpAccountDO、ErpFinancePaymentDO、ErpFinanceReceiptDO |
| 统计报表 | 采购/销售金额汇总统计（全部 + 时间段），基于 XML SQL 聚合 | 复用 purchase/sale 单据表，无独立表 |

## API 接口索引

> 端点总数 146（超过 120），按域分节给出控制器级摘要，完整端点清单见各 `api-{key}.md`。

### 产品管理（21 端点）→ 详情见 [api-product.md](api-product.md)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| ErpProductController | 产品管理（/erp/product） | 7 |
| ErpProductCategoryController | 产品分类管理（/erp/product-category） | 7 |
| ErpProductUnitController | 产品单位管理（/erp/product-unit） | 7 |

代表性端点：`POST /erp/product/create`（erp:product:create）、`GET /erp/product/page`（erp:product:query）、`GET /erp/product/simple-list`（仅登录，无权限校验）、`GET /erp/product-category/list`（erp:product-category:query）。

### 采购管理（28 端点）→ 详情见 [api-purchase.md](api-purchase.md)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| ErpSupplierController | 供应商管理（/erp/supplier） | 7 |
| ErpPurchaseOrderController | 采购订单管理（/erp/purchase-order） | 7 |
| ErpPurchaseInController | 采购入库管理（/erp/purchase-in） | 7 |
| ErpPurchaseReturnController | 采购退货管理（/erp/purchase-return） | 7 |

代表性端点：`POST /erp/purchase-order/create`（erp:purchase-order:create）、`PUT /erp/purchase-order/update-status`（erp:purchase-order:update-status，审核/反审核）、`GET /erp/purchase-in/page`（erp:purchase-in:query）、`DELETE /erp/purchase-return/delete`（erp:purchase-return:delete，支持批量 ids）。

### 销售管理（28 端点）→ 详情见 [api-sale.md](api-sale.md)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| ErpCustomerController | 客户管理（/erp/customer） | 7 |
| ErpSaleOrderController | 销售订单管理（/erp/sale-order） | 7 |
| ErpSaleOutController | 销售出库管理（/erp/sale-out） | 7 |
| ErpSaleReturnController | 销售退货管理（/erp/sale-return） | 7 |

代表性端点：`POST /erp/sale-order/create`（erp:sale-order:create）、`PUT /erp/sale-out/update-status`（erp:sale-out:update-status）、`GET /erp/sale-return/get`（erp:sale-return:query）、`GET /erp/customer/simple-list`（仅登录）。

### 仓库库存（43 端点）→ 详情见 [api-stock.md](api-stock.md)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| ErpWarehouseController | 仓库管理（/erp/warehouse） | 8 |
| ErpStockController | 产品库存查询（/erp/stock） | 4 |
| ErpStockRecordController | 库存流水明细（/erp/stock-record） | 3 |
| ErpStockInController | 其它入库单管理（/erp/stock-in） | 7 |
| ErpStockOutController | 其它出库单管理（/erp/stock-out） | 7 |
| ErpStockMoveController | 库存调拨单管理（/erp/stock-move） | 7 |
| ErpStockCheckController | 库存盘点单管理（/erp/stock-check） | 7 |

代表性端点：`GET /erp/stock/get`（erp:stock:query，支持 id 或 productId+warehouseId 两种查询方式）、`GET /erp/stock/get-count`（仅登录）、`POST /erp/stock-check/create`（erp:stock-check:create）、`PUT /erp/stock-move/update-status`（erp:stock-move:update-status）、`GET /erp/stock-record/page`（erp:stock-record:query）。

### 财务管理（22 端点）→ 详情见 [api-finance.md](api-finance.md)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| ErpAccountController | 结算账户管理（/erp/account） | 8 |
| ErpFinancePaymentController | 付款单管理（/erp/finance-payment） | 7 |
| ErpFinanceReceiptController | 收款单管理（/erp/finance-receipt） | 7 |

代表性端点：`POST /erp/finance-payment/create`（erp:finance-payment:create）、`PUT /erp/finance-receipt/update-status`（erp:finance-receipt:update-status）、`PUT /erp/account/update-default-status`（仅登录，无 @PreAuthorize）、`GET /erp/account/simple-list`（仅登录）。

### 统计报表（4 端点）→ 详情见 [api-statistics.md](api-statistics.md)
| Controller | 说明 | 端点数 |
|-----|------|-------|
| ErpPurchaseStatisticsController | 采购统计（/erp/purchase-statistics） | 2 |
| ErpSaleStatisticsController | 销售统计（/erp/sale-statistics） | 2 |

代表性端点：`GET /erp/purchase-statistics/summary`、`GET /erp/sale-statistics/time-summary`，权限均为 `erp:statistics:query`。

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| erp_product | 产品 | BaseDO | name、barCode、categoryId、unitId、status、purchasePrice、salePrice、minPrice、expiryDay、weight |
| erp_product_category | 产品分类（树形） | BaseDO | parentId、name、code、sort、status |
| erp_product_unit | 产品单位 | BaseDO | name、status |
| erp_supplier | 供应商 | BaseDO | name、contact、mobile、taxNo、taxPercent、bankName、bankAccount、status、sort |
| erp_purchase_order | 采购订单 | BaseDO | no、supplierId、accountId、orderTime、totalCount、totalPrice、totalTaxPrice、discountPercent、depositPrice、inCount、returnCount、status |
| erp_purchase_order_items | 采购订单明细 | BaseDO | orderId、productId、productUnitId、productPrice、count、totalPrice、taxPercent、taxPrice、inCount、returnCount |
| erp_purchase_in | 采购入库单 | BaseDO | no、supplierId、accountId、orderId、orderNo、inTime、totalCount、totalPrice、paymentPrice、otherPrice、status |
| erp_purchase_in_items | 采购入库明细 | BaseDO | inId、orderItemId、warehouseId、productId、productPrice、count、totalPrice、taxPercent、taxPrice |
| erp_purchase_return | 采购退货单 | BaseDO | no、supplierId、accountId、orderId、returnTime、totalCount、totalPrice、refundPrice、status |
| erp_purchase_return_items | 采购退货明细 | BaseDO | returnId、orderItemId、warehouseId、productId、count、totalPrice |
| erp_customer | 客户 | BaseDO | name、contact、mobile、taxNo、taxPercent、bankName、bankAccount、status、sort |
| erp_sale_order | 销售订单 | BaseDO | no、customerId、saleUserId、accountId、orderTime、totalCount、totalPrice、discountPercent、depositPrice、outCount、returnCount、status |
| erp_sale_order_items | 销售订单明细 | BaseDO | orderId、productId、productUnitId、productPrice、count、totalPrice、taxPercent、taxPrice、outCount、returnCount |
| erp_sale_out | 销售出库单 | BaseDO | no、customerId、saleUserId、orderId、orderNo、outTime、totalCount、totalPrice、receiptPrice、status |
| erp_sale_out_items | 销售出库明细 | BaseDO | outId、orderItemId、warehouseId、productId、count、totalPrice |
| erp_sale_return | 销售退货单 | BaseDO | no、customerId、saleUserId、orderId、returnTime、totalCount、totalPrice、refundPrice、status |
| erp_sale_return_items | 销售退货明细 | BaseDO | returnId、orderItemId、warehouseId、productId、count、totalPrice |
| erp_warehouse | 仓库 | BaseDO | name、address、principal、warehousePrice、truckagePrice、sort、status、defaultStatus |
| erp_stock | 产品库存（仓库+产品唯一） | BaseDO | productId、warehouseId、count |
| erp_stock_record | 库存流水明细 | BaseDO | productId、warehouseId、count（正入负出）、totalCount（变动后余额）、bizType、bizId、bizItemId、bizNo |
| erp_stock_in | 其它入库单 | BaseDO | no、supplierId、inTime、totalCount、totalPrice、status |
| erp_stock_in_item | 其它入库明细 | BaseDO | inId、warehouseId、productId、productUnitId、productPrice、count、totalPrice |
| erp_stock_out | 其它出库单 | BaseDO | no、customerId、outTime、totalCount、totalPrice、status |
| erp_stock_out_item | 其它出库明细 | BaseDO | outId、warehouseId、productId、productPrice、count、totalPrice |
| erp_stock_move | 库存调拨单 | BaseDO | no、moveTime、totalCount、totalPrice、status |
| erp_stock_move_item | 库存调拨明细 | BaseDO | moveId、fromWarehouseId、toWarehouseId、productId、productPrice、count、totalPrice |
| erp_stock_check | 库存盘点单 | BaseDO | no、checkTime、totalCount、totalPrice、status、fileUrl |
| erp_stock_check_item | 库存盘点明细 | BaseDO | checkId、warehouseId、productId、stockCount（账面）、actualCount（实际）、count（差异）、totalPrice |
| erp_account | 结算账户 | BaseDO | name、no、status、sort、defaultStatus |
| erp_finance_payment | 付款单 | BaseDO | no、supplierId、accountId、financeUserId、paymentTime、totalPrice、discountPrice、paymentPrice、status |
| erp_finance_payment_item | 付款单明细 | BaseDO | paymentId、bizType、bizId、bizNo、totalPrice、paidPrice、paymentPrice |
| erp_finance_receipt | 收款单 | BaseDO | no、customerId、accountId、financeUserId、receiptTime、totalPrice、discountPrice、receiptPrice、status |
| erp_finance_receipt_item | 收款单明细 | BaseDO | receiptId、bizType、bizId、bizNo、totalPrice、receiptedPrice、receiptPrice |

## 设计模式
| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 统一台账入口（内部 BO 封装） | `ErpStockRecordService.createStockRecord(ErpStockRecordCreateReqBO)`，被 purchase-in/purchase-return/sale-out/sale-return/stock-in/stock-out/stock-move/stock-check 共 8 个 ServiceImpl 调用 | 所有出入库变动收敛到一个事务入口：先更新 erp_stock 余量（不足则报 STOCK_COUNT_NEGATIVE），再写 erp_stock_record 流水，避免各单据各自维护库存逻辑 |
| 单据-明细主子表模式 | 各订单/出入库/退货/付款收款 Service | 主表与明细同事务级联保存；明细行携带业务回链字段（orderItemId、bizType/bizId）支撑跨单据数量校验与核销 |
| 枚举状态机 | `ErpAuditStatus`（PROCESS=10 未审核 / APPROVE=20 已审核）+ `DictTypeConstants`（erp_audit_status、erp_stock_record_biz_type 字典） | 全模块单据审核/反审核统一状态语义，预留接入 BPM 工作流的 TODO |

## 依赖关系
- **上游**（本模块依赖）:
  - 业务模块：yudao-module-system（唯一业务依赖，经 pom 引入；代码中 19 处使用 `AdminUserApi` 查询用户昵称用于单据创建人/审核人展示）
  - framework starter：yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-test
- **下游**（依赖本模块）: 仅 yudao-server（装配入口）依赖本模块；无其它业务模块依赖 erp

## 对外暴露的 API
无。erp 模块未提供 `api` 包，不向其它业务模块暴露跨模块 Api（属纯终端业务模块）。

## 详细文档
- [api-product.md](api-product.md) - 产品管理（产品/分类/单位）
- [api-purchase.md](api-purchase.md) - 采购管理（供应商/采购订单/入库/退货）
- [api-sale.md](api-sale.md) - 销售管理（客户/销售订单/出库/退货）
- [api-stock.md](api-stock.md) - 仓库库存（仓库/库存/出入库/调拨/盘点/流水）
- [api-finance.md](api-finance.md) - 财务管理（结算账户/付款单/收款单）
- [api-statistics.md](api-statistics.md) - 统计报表（采购/销售统计）
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南（Controller/Service/DAL 编码规范、单据与库存类型扩展步骤、关键文件索引）
