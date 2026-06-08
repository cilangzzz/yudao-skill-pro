# 首页统计接口

## 概述

首页统计为仓储管理后台提供仪表盘数据，包含订单汇总、订单趋势和库存汇总三大统计维度。

### 业务定位

- 为管理者提供仓储运营数据概览
- 支持订单维度和库存维度的数据分析
- 通过图表展示数据趋势，辅助决策

## 接口列表

### 1. 订单汇总统计

- **路径**: `GET /wms/home-statistics/order-summary`
- **说明**: 获取各类型单据的汇总统计数据
- **权限**: `wms:home-statistics:query`
- **响应**: `CommonResult<HomeOrderSummaryRespVO>`
- **返回字段**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| receiptOrderCount | Integer | 入库单总数 |
| shipmentOrderCount | Integer | 出库单总数 |
| movementOrderCount | Integer | 移库单总数 |
| checkOrderCount | Integer | 盘点单总数 |
| receiptOrderAmount | BigDecimal | 入库总金额 |
| shipmentOrderAmount | BigDecimal | 出库总金额 |

### 2. 订单趋势统计

- **路径**: `GET /wms/home-statistics/order-trend`
- **说明**: 获取指定时间范围内的订单趋势数据
- **权限**: `wms:home-statistics:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| beginTime | Date | 是 | 开始时间 |
| endTime | Date | 是 | 结束时间 |

- **响应**: `CommonResult<List<HomeOrderTrendRespVO>>`
- **返回字段**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | String | 日期 |
| receiptOrderCount | Integer | 当日入库单数 |
| shipmentOrderCount | Integer | 当日出库单数 |
| movementOrderCount | Integer | 当日移库单数 |
| checkOrderCount | Integer | 当日盘点单数 |

### 3. 库存汇总统计

- **路径**: `GET /wms/home-statistics/inventory-summary`
- **说明**: 获取库存汇总统计数据
- **权限**: `wms:home-statistics:query`
- **响应**: `CommonResult<HomeInventorySummaryRespVO>`
- **返回字段**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalQuantity | BigDecimal | 库存总数量 |
| totalAmount | BigDecimal | 库存总金额 |
| warehouseCount | Integer | 仓库数量 |
| skuCount | Integer | SKU 数量 |

## 关键实现

- **数据聚合**: 统计数据通过 SQL 聚合查询直接从数据库计算，避免加载大量数据到内存
- **时间范围**: 订单趋势统计支持自定义时间范围，按天粒度聚合
