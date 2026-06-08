# ERP 模块文档

## 模块概述

ERP（企业资源计划）模块是企业管理核心系统，实现进销存一体化管理。
模块路径：`yudao-module-erp`

### 业务定位

| 业务域 | 说明 | 核心流程 |
|--------|------|----------|
| 采购管理 | 供应商采购全流程 | 采购订单 -> 采购入库 -> 采购退货 -> 付款 |
| 销售管理 | 客户销售全流程 | 销售订单 -> 销售出库 -> 销售退货 -> 收款 |
| 库存管理 | 仓库库存全场景 | 其它入库/出库、库存调拨、库存盘点、库存查询 |
| 财务管理 | 结算账户与收付款 | 结算账户、付款单、收款单 |
| 基础资料 | 业务基础数据 | 产品、产品分类、产品单位、供应商、客户、仓库 |

## 核心功能点

### 采购域

| 功能 | 说明 | 详细文档 |
|------|------|----------|
| 采购订单 | 创建、编辑、删除、审核、反审核采购订单 | [api-purchase.md](api-purchase.md) |
| 采购入库 | 关联采购订单，记录入库明细，审核后更新库存 | [api-purchase.md](api-purchase.md) |
| 采购退货 | 关联采购订单，记录退货明细，审核后扣减库存 | [api-purchase.md](api-purchase.md) |
| 供应商管理 | 供应商增删改查 | [api-purchase.md](api-purchase.md) |

### 销售域

| 功能 | 说明 | 详细文档 |
|------|------|----------|
| 销售订单 | 创建、编辑、删除、审核、反审核销售订单 | [api-sale.md](api-sale.md) |
| 销售出库 | 关联销售订单，记录出库明细，审核后扣减库存 | [api-sale.md](api-sale.md) |
| 销售退货 | 关联销售订单，记录退货明细，审核后更新库存 | [api-sale.md](api-sale.md) |
| 客户管理 | 客户增删改查 | [api-sale.md](api-sale.md) |

### 库存域

| 功能 | 说明 | 详细文档 |
|------|------|----------|
| 库存查询 | 按产品、仓库查询实时库存 | [api-stock.md](api-stock.md) |
| 其它入库 | 非采购场景的入库操作 | [api-stock.md](api-stock.md) |
| 其它出库 | 非销售场景的出库操作 | [api-stock.md](api-stock.md) |
| 库存调拨 | 跨仓库库存转移 | [api-stock.md](api-stock.md) |
| 库存盘点 | 仓库库存盘点 | [api-stock.md](api-stock.md) |
| 仓库管理 | 仓库增删改查 | [api-stock.md](api-stock.md) |

### 财务域

| 功能 | 说明 | 详细文档 |
|------|------|----------|
| 付款单 | 采购付款管理，关联采购入库单 | [api-finance.md](api-finance.md) |
| 收款单 | 销售收款管理，关联销售出库单 | [api-finance.md](api-finance.md) |
| 结算账户 | 结算账户增删改查 | [api-finance.md](api-finance.md) |

### 产品域

| 功能 | 说明 | 详细文档 |
|------|------|----------|
| 产品管理 | 产品增删改查，含价格、条码、规格 | [api-product.md](api-product.md) |
| 产品分类 | 树形分类管理 | [api-product.md](api-product.md) |
| 产品单位 | 计量单位管理 | [api-product.md](api-product.md) |

## API 索引

### 采购域 API

| 接口 | 方法 | 路径 | 权限 |
|------|------|------|------|
| 创建采购订单 | POST | /erp/purchase-order/create | erp:purchase-order:create |
| 更新采购订单 | PUT | /erp/purchase-order/update | erp:purchase-order:update |
| 删除采购订单 | DELETE | /erp/purchase-order/delete | erp:purchase-order:delete |
| 更新订单状态 | PUT | /erp/purchase-order/update-status | erp:purchase-order:update-status |
| 查询订单分页 | GET | /erp/purchase-order/page | erp:purchase-order:query |
| 创建采购入库 | POST | /erp/purchase-in/create | erp:purchase-in:create |
| 更新采购入库 | PUT | /erp/purchase-in/update | erp:purchase-in:update |
| 删除采购入库 | DELETE | /erp/purchase-in/delete | erp:purchase-in:delete |
| 更新入库状态 | PUT | /erp/purchase-in/update-status | erp:purchase-in:update-status |
| 查询入库分页 | GET | /erp/purchase-in/page | erp:purchase-in:query |
| 创建采购退货 | POST | /erp/purchase-return/create | erp:purchase-return:create |
| 更新采购退货 | PUT | /erp/purchase-return/update | erp:purchase-return:update |
| 删除采购退货 | DELETE | /erp/purchase-return/delete | erp:purchase-return:delete |
| 更新退货状态 | PUT | /erp/purchase-return/update-status | erp:purchase-return:update-status |
| 查询退货分页 | GET | /erp/purchase-return/page | erp:purchase-return:query |
| 创建供应商 | POST | /erp/supplier/create | erp:supplier:create |
| 更新供应商 | PUT | /erp/supplier/update | erp:supplier:update |
| 删除供应商 | DELETE | /erp/supplier/delete | erp:supplier:delete |
| 查询供应商分页 | GET | /erp/supplier/page | erp:supplier:query |

### 销售域 API

| 接口 | 方法 | 路径 | 权限 |
|------|------|------|------|
| 创建销售订单 | POST | /erp/sale-order/create | erp:sale-order:create |
| 更新销售订单 | PUT | /erp/sale-order/update | erp:sale-order:update |
| 删除销售订单 | DELETE | /erp/sale-order/delete | erp:sale-order:delete |
| 更新订单状态 | PUT | /erp/sale-order/update-status | erp:sale-order:update-status |
| 查询订单分页 | GET | /erp/sale-order/page | erp:sale-order:query |
| 创建销售出库 | POST | /erp/sale-out/create | erp:sale-out:create |
| 更新销售出库 | PUT | /erp/sale-out/update | erp:sale-out:update |
| 删除销售出库 | DELETE | /erp/sale-out/delete | erp:sale-out:delete |
| 更新出库状态 | PUT | /erp/sale-out/update-status | erp:sale-out:update-status |
| 查询出库分页 | GET | /erp/sale-out/page | erp:sale-out:query |
| 创建销售退货 | POST | /erp/sale-return/create | erp:sale-return:create |
| 更新销售退货 | PUT | /erp/sale-return/update | erp:sale-return:update |
| 删除销售退货 | DELETE | /erp/sale-return/delete | erp:sale-return:delete |
| 更新退货状态 | PUT | /erp/sale-return/update-status | erp:sale-return:update-status |
| 查询退货分页 | GET | /erp/sale-return/page | erp:sale-return:query |
| 创建客户 | POST | /erp/customer/create | erp:customer:create |
| 更新客户 | PUT | /erp/customer/update | erp:customer:update |
| 删除客户 | DELETE | /erp/customer/delete | erp:customer:delete |
| 查询客户分页 | GET | /erp/customer/page | erp:customer:query |

### 库存域 API

| 接口 | 方法 | 路径 | 权限 |
|------|------|------|------|
| 查询库存分页 | GET | /erp/stock/page | erp:stock:query |
| 创建其它入库 | POST | /erp/stock-in/create | erp:stock-in:create |
| 更新其它入库 | PUT | /erp/stock-in/update | erp:stock-in:update |
| 删除其它入库 | DELETE | /erp/stock-in/delete | erp:stock-in:delete |
| 更新入库状态 | PUT | /erp/stock-in/update-status | erp:stock-in:update-status |
| 查询入库分页 | GET | /erp/stock-in/page | erp:stock-in:query |
| 创建其它出库 | POST | /erp/stock-out/create | erp:stock-out:create |
| 更新其它出库 | PUT | /erp/stock-out/update | erp:stock-out:update |
| 删除其它出库 | DELETE | /erp/stock-out/delete | erp:stock-out:delete |
| 更新出库状态 | PUT | /erp/stock-out/update-status | erp:stock-out:update-status |
| 查询出库分页 | GET | /erp/stock-out/page | erp:stock-out:query |
| 创建库存调拨 | POST | /erp/stock-move/create | erp:stock-move:create |
| 更新库存调拨 | PUT | /erp/stock-move/update | erp:stock-move:update |
| 删除库存调拨 | DELETE | /erp/stock-move/delete | erp:stock-move:delete |
| 更新调拨状态 | PUT | /erp/stock-move/update-status | erp:stock-move:update-status |
| 查询调拨分页 | GET | /erp/stock-move/page | erp:stock-move:query |
| 创建库存盘点 | POST | /erp/stock-check/create | erp:stock-check:create |
| 更新库存盘点 | PUT | /erp/stock-check/update | erp:stock-check:update |
| 删除库存盘点 | DELETE | /erp/stock-check/delete | erp:stock-check:delete |
| 更新盘点状态 | PUT | /erp/stock-check/update-status | erp:stock-check:update-status |
| 查询盘点分页 | GET | /erp/stock-check/page | erp:stock-check:query |
| 创建仓库 | POST | /erp/warehouse/create | erp:warehouse:create |
| 更新仓库 | PUT | /erp/warehouse/update | erp:warehouse:update |
| 删除仓库 | DELETE | /erp/warehouse/delete | erp:warehouse:delete |
| 查询仓库分页 | GET | /erp/warehouse/page | erp:warehouse:query |

### 财务域 API

| 接口 | 方法 | 路径 | 权限 |
|------|------|------|------|
| 创建付款单 | POST | /erp/finance-payment/create | erp:finance-payment:create |
| 更新付款单 | PUT | /erp/finance-payment/update | erp:finance-payment:update |
| 删除付款单 | DELETE | /erp/finance-payment/delete | erp:finance-payment:delete |
| 更新付款单状态 | PUT | /erp/finance-payment/update-status | erp:finance-payment:update-status |
| 查询付款单分页 | GET | /erp/finance-payment/page | erp:finance-payment:query |
| 创建收款单 | POST | /erp/finance-receipt/create | erp:finance-receipt:create |
| 更新收款单 | PUT | /erp/finance-receipt/update | erp:finance-receipt:update |
| 删除收款单 | DELETE | /erp/finance-receipt/delete | erp:finance-receipt:delete |
| 更新收款单状态 | PUT | /erp/finance-receipt/update-status | erp:finance-receipt:update-status |
| 查询收款单分页 | GET | /erp/finance-receipt/page | erp:finance-receipt:query |
| 创建结算账户 | POST | /erp/account/create | erp:account:create |
| 更新结算账户 | PUT | /erp/account/update | erp:account:update |
| 删除结算账户 | DELETE | /erp/account/delete | erp:account:delete |
| 查询结算账户分页 | GET | /erp/account/page | erp:account:query |

### 产品域 API

| 接口 | 方法 | 路径 | 权限 |
|------|------|------|------|
| 创建产品 | POST | /erp/product/create | erp:product:create |
| 更新产品 | PUT | /erp/product/update | erp:product:update |
| 删除产品 | DELETE | /erp/product/delete | erp:product:delete |
| 查询产品分页 | GET | /erp/product/page | erp:product:query |
| 创建产品分类 | POST | /erp/product-category/create | erp:product-category:create |
| 更新产品分类 | PUT | /erp/product-category/update | erp:product-category:update |
| 删除产品分类 | DELETE | /erp/product-category/delete | erp:product-category:delete |
| 查询产品分类列表 | GET | /erp/product-category/list | erp:product-category:query |
| 创建产品单位 | POST | /erp/product-unit/create | erp:product-unit:create |
| 更新产品单位 | PUT | /erp/product-unit/update | erp:product-unit:update |
| 删除产品单位 | DELETE | /erp/product-unit/delete | erp:product-unit:delete |
| 查询产品单位列表 | GET | /erp/product-unit/list | erp:product-unit:query |

## 数据模型

详见 [data-model.md](data-model.md)

## 设计模式

| 模式 | 位置 | 用途 |
|------|------|------|
| 状态机模式 | `ErpAuditStatus` | 定义单据审核状态 PROCESS(10) -> APPROVE(20)，控制单据生命周期 |
| 主子表模式 | `ErpPurchaseOrderDO + ErpPurchaseOrderItemDO` | 订单类单据采用主子表设计，支持明细项差量更新 |
| 策略模式 | `ErpStockRecordBizTypeEnum` | 库存记录业务类型枚举，定义不同业务场景的库存变动类型 |
| 分布式ID生成 | `ErpNoRedisDAO` | 基于Redis的分布式单据号生成，保证唯一性和有序性 |
| 增量更新模式 | `ErpStockMapper.updateCountIncrement` | 库存增量更新，使用乐观锁避免并发问题 |

## 依赖关系

| 依赖类型 | 模块/库 | 用途 |
|----------|---------|------|
| 内部依赖 | system (AdminUserApi) | 获取用户信息，显示操作人姓名 |
| 外部依赖 | MyBatis-Plus 3.x | ORM框架，简化数据库操作 |
| 外部依赖 | Hutool 5.x | Java工具类库，日期、集合等工具 |
| 外部依赖 | Spring Redis 2.x | Redis操作，单据号生成 |

## 控制器清单

| 控制器 | 路径前缀 | 说明 |
|--------|----------|------|
| ErpPurchaseOrderController | /erp/purchase-order | 采购订单接口 |
| ErpPurchaseInController | /erp/purchase-in | 采购入库接口 |
| ErpPurchaseReturnController | /erp/purchase-return | 采购退货接口 |
| ErpSaleOrderController | /erp/sale-order | 销售订单接口 |
| ErpSaleOutController | /erp/sale-out | 销售出库接口 |
| ErpSaleReturnController | /erp/sale-return | 销售退货接口 |
| ErpStockController | /erp/stock | 库存查询接口 |
| ErpStockInController | /erp/stock-in | 其它入库接口 |
| ErpStockOutController | /erp/stock-out | 其它出库接口 |
| ErpStockMoveController | /erp/stock-move | 库存调拨接口 |
| ErpStockCheckController | /erp/stock-check | 库存盘点接口 |
| ErpFinancePaymentController | /erp/finance-payment | 付款单接口 |
| ErpFinanceReceiptController | /erp/finance-receipt | 收款单接口 |
| ErpProductController | /erp/product | 产品接口 |
| ErpSupplierController | /erp/supplier | 供应商接口 |
| ErpCustomerController | /erp/customer | 客户接口 |
| ErpWarehouseController | /erp/warehouse | 仓库接口 |

## 关键文件清单

| 文件路径 | 说明 |
|----------|------|
| `enums/ErpAuditStatus.java` | 审核状态枚举，定义单据状态流转 |
| `enums/ErrorCodeConstants.java` | 错误码常量，定义所有业务异常 |
| `enums/stock/ErpStockRecordBizTypeEnum.java` | 库存记录业务类型枚举 |
| `service/purchase/ErpPurchaseOrderServiceImpl.java` | 采购订单服务实现，展示标准业务流程 |
| `service/stock/ErpStockServiceImpl.java` | 库存服务实现，展示库存增量更新 |
| `service/stock/ErpStockRecordServiceImpl.java` | 库存记录服务，管理库存变动明细 |
| `dal/redis/no/ErpNoRedisDAO.java` | 单据号生成器，分布式唯一ID |
| `dal/dataobject/purchase/ErpPurchaseOrderDO.java` | 采购订单DO，展示主表设计 |
| `dal/dataobject/stock/ErpStockDO.java` | 库存DO，展示库存表设计 |
| `dal/dataobject/stock/ErpStockRecordDO.java` | 库存记录DO，展示库存明细设计 |
| `service/stock/bo/ErpStockRecordCreateReqBO.java` | 库存记录创建请求BO，展示值对象设计 |
| `controller/admin/purchase/ErpPurchaseOrderController.java` | 采购订单控制器，展示标准Controller设计 |

## 详细文档

- [采购域 API 文档](api-purchase.md)
- [销售域 API 文档](api-sale.md)
- [库存域 API 文档](api-stock.md)
- [财务域 API 文档](api-finance.md)
- [产品域 API 文档](api-product.md)
- [数据模型文档](data-model.md)
- [踩坑与注意事项](pitfalls.md)
