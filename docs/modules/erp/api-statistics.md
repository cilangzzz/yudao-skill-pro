# 统计报表接口 (ErpPurchaseStatisticsController / ErpSaleStatisticsController)

> ERP 统计报表域，提供采购、销售两大业务的全局汇总（今日/昨日/本月/今年）与按月时间段趋势统计，金额口径为"已审核入库（出库）金额 − 已审核退货金额"，即仅统计 `status = 20`（`ErpAuditStatus.APPROVE`，已审核）的单据。

## 接口路径前缀

- /erp/purchase-statistics  (Controller: ErpPurchaseStatisticsController)
- /erp/sale-statistics  (Controller: ErpSaleStatisticsController)

---

## 1. 采购统计（/erp/purchase-statistics）

### 1.1 获得采购统计

- **路径**: GET /erp/purchase-statistics/summary
- **权限**: erp:statistics:query
- **说明**: 获得今日、昨日、本月、今年四个维度的采购金额汇总

**请求参数**: 无

**响应**: CommonResult&lt;ErpPurchaseSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| todayPrice | BigDecimal | 今日采购金额 |
| yesterdayPrice | BigDecimal | 昨日采购金额 |
| monthPrice | BigDecimal | 本月采购金额 |
| yearPrice | BigDecimal | 今年采购金额 |

**业务逻辑**: 1. 分别计算四个统计区间的起始时间：今日（today 开始）、昨日（yesterday 开始）、本月（month 开始）、今年（year 开始）；2. 每个区间调用 getPurchasePrice(beginTime, endTime)，Service 直接透传至 Mapper；3. SQL 统计 erp_purchase_in 表 in_time 落在 [beginTime, endTime) 内、且 status = 20（已审核，ErpAuditStatus.APPROVE）的 total_price 合计（endTime 为 null 时不设上界），再减去 erp_purchase_return 表 return_time 落在同区间、status = 20 的 total_price 合计，差值即为净采购金额（已审核入库 − 已审核退货）；4. 查询带 tenant_id 租户过滤、deleted = 0 逻辑删除过滤与 status = 20 审核状态过滤；合计使用 `COALESCE(SUM(total_price), 0)` 做空值合并（空合计返回 0），语句末尾追加 `${SqlDialectUtils.fromDual()}` 方言片段（Oracle 输出 FROM DUAL，MySQL/PostgreSQL/SQLServer 为空串），以支持无顶层 FROM 的标量汇总在 Oracle 执行；5. 组装为 ErpPurchaseSummaryRespVO 返回。

### 1.2 获得采购时间段统计

- **路径**: GET /erp/purchase-statistics/time-summary
- **权限**: erp:statistics:query
- **说明**: 获得最近 count 个自然月、逐月汇总的采购金额列表，用于趋势图展示

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| count | Integer | 否 | 默认值 6（@RequestParam defaultValue） | 时间段数量（最近 count 个月） |

**响应**: CommonResult&lt;List&lt;ErpPurchaseTimeSummaryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间，格式 yyyy-MM（如 2022-03） |
| price | BigDecimal | 该月采购金额 |

**业务逻辑**: 1. 从 i = count-1 到 0 倒序遍历，取当前时间往前推 i 个月；2. 对每个月计算月初 beginOfMonth 与月末 endOfMonth 构成统计区间；3. 调用 getPurchasePrice(startTime, endTime) 得到该月净采购金额（口径同 1.1：已审核入库 − 已审核退货，仅统计 status = 20 的单据）；4. time 字段按 NORM_MONTH_PATTERN（yyyy-MM）格式化月初时间；5. 按时间从早到晚的顺序组装列表返回。SQL 的多数据库兼容处理（COALESCE 与 `${SqlDialectUtils.fromDual()}`）与 1.1 相同。

---

## 2. 销售统计（/erp/sale-statistics）

### 2.1 获得销售统计

- **路径**: GET /erp/sale-statistics/summary
- **权限**: erp:statistics:query
- **说明**: 获得今日、昨日、本月、今年四个维度的销售金额汇总

**请求参数**: 无

**响应**: CommonResult&lt;ErpSaleSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| todayPrice | BigDecimal | 今日销售金额 |
| yesterdayPrice | BigDecimal | 昨日销售金额 |
| monthPrice | BigDecimal | 本月销售金额 |
| yearPrice | BigDecimal | 今年销售金额 |

**业务逻辑**: 1. 分别计算今日、昨日、本月、今年四个统计区间的起始时间；2. 每个区间调用 getSalePrice(beginTime, endTime)，Service 直接透传至 Mapper；3. SQL 统计 erp_sale_out 表 out_time 落在 [beginTime, endTime) 内、且 status = 20（已审核，ErpAuditStatus.APPROVE）的 total_price 合计（endTime 为 null 时不设上界），再减去 erp_sale_return 表 return_time 落在同区间、status = 20 的 total_price 合计，差值即为净销售金额（已审核销售出库 − 已审核销售退货）；4. 查询带 tenant_id 租户过滤、deleted = 0 逻辑删除过滤与 status = 20 审核状态过滤；合计使用 `COALESCE(SUM(total_price), 0)` 做空值合并（空合计返回 0），语句末尾追加 `${SqlDialectUtils.fromDual()}` 方言片段（Oracle 输出 FROM DUAL，其它数据库为空串）；5. 组装为 ErpSaleSummaryRespVO 返回。

### 2.2 获得销售时间段统计

- **路径**: GET /erp/sale-statistics/time-summary
- **权限**: erp:statistics:query
- **说明**: 获得最近 count 个自然月、逐月汇总的销售金额列表，用于趋势图展示

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| count | Integer | 否 | 默认值 6（@RequestParam defaultValue） | 时间段数量（最近 count 个月） |

**响应**: CommonResult&lt;List&lt;ErpSaleTimeSummaryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间，格式 yyyy-MM（如 2022-03） |
| price | BigDecimal | 该月销售金额 |

**业务逻辑**: 1. 从 i = count-1 到 0 倒序遍历，取当前时间往前推 i 个月；2. 对每个月计算月初 beginOfMonth 与月末 endOfMonth 构成统计区间；3. 调用 getSalePrice(startTime, endTime) 得到该月净销售金额（口径同 2.1：已审核销售出库 − 已审核销售退货，仅统计 status = 20 的单据）；4. time 字段按 NORM_MONTH_PATTERN（yyyy-MM）格式化月初时间；5. 按时间从早到晚的顺序组装列表返回。SQL 的多数据库兼容处理（COALESCE 与 `${SqlDialectUtils.fromDual()}`）与 2.1 相同。

---

## 附注

- 本域为纯查询统计接口，ErrorCodeConstants 中无统计域专属错误码，端点调用过程不抛业务异常。
- 采购与销售统计口径一致：净金额 = 已审核入库/出库单金额合计 − 已审核退货单金额合计，未审核（status = 10）单据不计入，反审核后单据会从统计中移除；时间段统计固定按自然月切片。
- 两个统计 Mapper XML 均为无顶层 FROM 的标量汇总：空值合并使用标准 `COALESCE`（非 MySQL 专属 `IFNULL`），并在语句末尾用 `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@fromDual()}` 补充方言片段（Oracle 为 FROM DUAL，MySQL/PostgreSQL/SQLServer 为空串），以支持多数据库执行。
- 既有行为保持不变：summary 的今日/本月/今年传入 endTime = null，SQL 不设上界；time-summary 传入月末 endTime，SQL 使用严格小于 `<`。
