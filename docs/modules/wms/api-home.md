# 首页统计接口 (WmsHomeStatisticsController)

> 提供 WMS 首页看板的只读统计接口：单据汇总（按类型/状态计数）、近 N 天单据趋势、库存总量与商品/仓库维度库存排行。

## 接口路径前缀

/wms/home-statistics  (Controller: WmsHomeStatisticsController)

所有接口均为只读查询（GET），无写接口；权限统一为 `wms:home:query`。

## 1. 首页统计（WmsHomeStatisticsController）

### 1.1 获得首页单据汇总统计

- **路径**: GET /wms/home-statistics/order-summary
- **权限**: wms:home:query
- **说明**: 按单据类型（入库/出库/移库/盘库）与单据状态（草稿/已完成/已作废）分组统计单据数量，每种类型返回总数与状态分布。

**请求参数**: 无 ReqVO，查询参数如下

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| warehouseId | Long | 否 | - | 仓库编号，传入时按该仓库过滤，并校验仓库存在 |

**响应**: `CommonResult<List<WmsHomeOrderSummaryRespVO>>`（每种单据类型一条记录，固定返回 4 条）

| 字段 | 类型 | 说明 |
|-----|------|------|
| type | Integer | 单据类型：1 入库单、2 出库单、3 移库单、4 盘库单 |
| total | Long | 该类型单据总数（各状态计数之和） |
| statuses | List\<WmsHomeOrderStatusRespVO\> | 状态分布列表，每个状态一条 |

`statuses` 元素（WmsHomeOrderStatusRespVO）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 状态值：0 草稿、4 已完成、5 已作废 |
| count | Long | 该类型该状态的单据数量，无数据补 0 |

**业务逻辑**:
1. warehouseId 非空时校验仓库存在，避免前端误传任意 id 直接落到 SQL。
2. 调用 Mapper `selectOrderCountGroupByTypeAndStatus` 按单据类型 + 单据状态分组统计单据数量。
3. 遍历 `WmsOrderTypeEnum`（入库/出库/移库/盘库 4 种类型），每种类型下遍历 `WmsOrderStatusEnum`（草稿/已完成/已作废 3 种状态）构造状态计数列表，统计结果中缺失的组合补 0。
4. 每种类型的 total 取各状态计数之和，组装返回 4 条汇总记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_100_000 | 仓库不存在（传入 warehouseId 校验失败时抛出） |

### 1.2 获得首页单据趋势

- **路径**: GET /wms/home-statistics/order-trend
- **权限**: wms:home:query
- **说明**: 统计最近 N 天（含今天）每天入库/出库/移库/盘库四类单据的数量趋势，保证每天都有数据点。

**请求参数**: 无 ReqVO，查询参数如下

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| days | Integer | 否 | 默认 7；@Min(1)、@Max(90) | 统计天数 |
| warehouseId | Long | 否 | - | 仓库编号，传入时按该仓库过滤，并校验仓库存在 |

**响应**: `CommonResult<List<WmsHomeOrderTrendRespVO>>`（按时间升序，固定返回 days 条）

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | LocalDateTime | 日期（当天 0 点） |
| receiptCount | Long | 入库单数量 |
| shipmentCount | Long | 出库单数量 |
| movementCount | Long | 移库单数量 |
| checkCount | Long | 盘库单数量 |

**业务逻辑**:
1. warehouseId 非空时校验仓库存在。
2. 计算统计区间为 [今天 - days + 1, 明天)，保证最近 days 天包含今天。
3. 调用 Mapper `selectDailyOrderTrend` 按天 + 单据类型聚合该区间内的单据数量。
4. 将查询结果行按日期分组到 `Map<日期, Map<单据类型, 数量>>`。
5. 按日期列表 `getDateList(startDate, days)` 逐天构造结果，从分组 Map 中取对应类型的数量，缺失的日期或类型补 0，返回按时间升序的 days 条趋势数据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_100_000 | 仓库不存在（传入 warehouseId 校验失败时抛出） |

### 1.3 获得首页库存汇总统计

- **路径**: GET /wms/home-statistics/inventory-summary
- **权限**: wms:home:query
- **说明**: 返回库存总数量，以及商品维度库存占比排行、仓库维度库存分布排行。

**请求参数**: 无 ReqVO，查询参数如下

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| warehouseId | Long | 否 | - | 仓库编号，传入时按该仓库过滤，并校验仓库存在 |
| goodsLimit | Integer | 否 | 默认 5；@Min(1)、@Max(20) | 商品库存排行条数上限 |
| warehouseLimit | Integer | 否 | 默认 8；@Min(1)、@Max(20) | 仓库库存排行条数上限 |

**响应**: `CommonResult<WmsHomeInventorySummaryRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalQuantity | BigDecimal | 总库存数量 |
| goodsShareList | List\<ItemRank\> | 商品库存占比列表 |
| warehouseDistributionList | List\<WarehouseRank\> | 仓库库存分布列表 |

`goodsShareList` 元素（ItemRank）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 商品编号 |
| name | String | 商品名称 |
| quantity | BigDecimal | 库存数量 |

`warehouseDistributionList` 元素（WarehouseRank）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 仓库编号 |
| name | String | 仓库名称 |
| quantity | BigDecimal | 库存数量 |

**业务逻辑**:
1. warehouseId 非空时校验仓库存在。
2. 调用 Mapper `selectInventoryTotalQuantity` 汇总库存总数量，结果为 null 时补 0。
3. 调用 Mapper `selectInventoryItemRank` 查询商品维度库存排行（Top goodsLimit）。
4. 调用 Mapper `selectInventoryWarehouseRank` 查询仓库维度库存排行（Top warehouseLimit）。
5. 组装排行列表时兼容 `id/name` 与 `itemId/itemName`、`warehouseId/warehouseName` 两组字段别名，缺失数量补 0，与总数量一并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_100_000 | 仓库不存在（传入 warehouseId 校验失败时抛出） |
