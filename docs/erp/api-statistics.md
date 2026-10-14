# 统计报表接口 (ErpPurchaseStatisticsController / ErpSaleStatisticsController)

> ERP 统计报表域，提供采购、销售两大业务的全局汇总（今日/昨日/本月/今年）与按月时间段趋势统计，金额口径为"入库（出库）金额 − 退货金额"。

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

**业务逻辑**: 1. 分别计算四个统计区间的起始时间：今日（today 开始）、昨日（yesterday 开始）、本月（month 开始）、今年（year 开始）；2. 每个区间调用 getPurchasePrice(beginTime, endTime)，Service 直接透传至 Mapper；3. SQL 统计 erp_purchase_in 表 in_time 落在 [beginTime, endTime) 内的 total_price 合计（endTime 为 null 时不设上界），再减去 erp_purchase_return 表 return_time 落在同区间的 total_price 合计，差值即为净采购金额（入库 − 退货）；4. 查询带 tenant_id 租户过滤与 deleted = 0 逻辑删除过滤，合计为空按 0 计算；5. 组装为 ErpPurchaseSummaryRespVO 返回。

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

**业务逻辑**: 1. 从 i = count-1 到 0 倒序遍历，取当前时间往前推 i 个月；2. 对每个月计算月初 beginOfMonth 与月末 endOfMonth 构成统计区间；3. 调用 getPurchasePrice(startTime, endTime) 得到该月净采购金额（口径同 1.2 的入库 − 退货）；4. time 字段按 NORM_MONTH_PATTERN（yyyy-MM）格式化月初时间；5. 按时间从早到晚的顺序组装列表返回。

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

**业务逻辑**: 1. 分别计算今日、昨日、本月、今年四个统计区间的起始时间；2. 每个区间调用 getSalePrice(beginTime, endTime)，Service 直接透传至 Mapper；3. SQL 统计 erp_sale_out 表 out_time 落在 [beginTime, endTime) 内的 total_price 合计（endTime 为 null 时不设上界），再减去 erp_sale_return 表 return_time 落在同区间的 total_price 合计，差值即为净销售金额（销售出库 − 销售退货）；4. 查询带 tenant_id 租户过滤与 deleted = 0 逻辑删除过滤，合计为空按 0 计算；5. 组装为 ErpSaleSummaryRespVO 返回。

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

**业务逻辑**: 1. 从 i = count-1 到 0 倒序遍历，取当前时间往前推 i 个月；2. 对每个月计算月初 beginOfMonth 与月末 endOfMonth 构成统计区间；3. 调用 getSalePrice(startTime, endTime) 得到该月净销售金额（口径同 2.1 的出库 − 退货）；4. time 字段按 NORM_MONTH_PATTERN（yyyy-MM）格式化月初时间；5. 按时间从早到晚的顺序组装列表返回。

---

## 附注

- 本域为纯查询统计接口，ErrorCodeConstants 中无统计域专属错误码，端点调用过程不抛业务异常。
- 采购与销售统计口径一致：净金额 = 有效入库/出库单金额合计 − 有效退货单金额合计；时间段统计固定按自然月切片。
