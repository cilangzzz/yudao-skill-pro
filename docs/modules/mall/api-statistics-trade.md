# 交易统计接口 (TradeStatisticsController)

> 管理后台的交易统计中心：汇总昨日/本月交易概况、交易状况趋势（营业额、退款、佣金、充值等）对照分析、待办订单数量提醒，以及交易状况明细的查询与 Excel 导出。

## 接口路径前缀
/statistics/trade  (Controller: TradeStatisticsController)

## 1. 交易统计（TradeStatisticsController）

### 1.1 获得交易统计

- **路径**: GET /statistics/trade/summary
- **权限**: statistics:trade:query
- **说明**: 获得交易统计概览，返回「昨日 + 本月」的订单数量与支付金额，并附带「前日 + 上月」的对照数据。

**请求参数**: 无

**响应**: CommonResult&lt;DataComparisonRespVO&lt;TradeSummaryRespVO&gt;&gt;

外层为数据对照结构（DataComparisonRespVO）：`value` 为当前数据（昨日 + 本月），`reference` 为参照数据（前日 + 上月）。

TradeSummaryRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| yesterdayOrderCount | Integer | 昨日订单数量 |
| yesterdayPayPrice | Integer | 昨日支付金额 |
| monthOrderCount | Integer | 本月订单数量 |
| monthPayPrice | Integer | 本月支付金额 |

**业务逻辑**:
1. 调用 getTradeSummaryByDays(-1) 统计昨天、getTradeSummaryByDays(-2) 统计前天的订单创建数与支付金额（按当天 [00:00:00, 23:59:59] 时间区间汇总 trade_statistics 表）。
2. 调用 getTradeSummaryByMonths(0) 统计本月、getTradeSummaryByMonths(-1) 统计上月的订单创建数与支付金额（按自然月起止时间区间汇总）。
3. 将「昨天 + 本月」数据合并为一个 TradeSummaryRespVO 作为当前数据 value。
4. 将「前天 + 上月」数据合并为一个 TradeSummaryRespVO 作为参照数据 reference。
5. 组装为 DataComparisonRespVO 返回，便于前端进行环比对照展示。

### 1.2 获得交易状况统计

- **路径**: GET /statistics/trade/analyse
- **权限**: statistics:trade:query
- **说明**: 按时间范围统计交易状况（营业额、订单支付金额、余额支付、退款、佣金、充值等），并返回等长的上一周期对照数据。

**请求参数 (TradeTrendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 时间范围数组，取第 1 个元素为开始时间、第 2 个元素为结束时间 |

**响应**: CommonResult&lt;DataComparisonRespVO&lt;TradeTrendSummaryRespVO&gt;&gt;

外层为数据对照结构：`value` 为当前区间数据，`reference` 为对照区间数据。

TradeTrendSummaryRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | LocalDate | 日期（yyyy-MM-dd） |
| turnoverPrice | Integer | 营业额（= 商品支付金额 + 充值金额） |
| orderPayPrice | Integer | 订单支付金额 |
| walletPayPrice | Integer | 余额支付金额 |
| afterSaleRefundPrice | Integer | 订单退款金额 |
| brokerageSettlementPrice | Integer | 支付佣金金额 |
| rechargePrice | Integer | 充值金额 |
| expensePrice | Integer | 支出金额（= 余额支付金额 + 支付佣金金额 + 商品退款金额） |

**业务逻辑**:
1. 通过 ArrayUtil.get 取 times[0] 为 beginTime、times[1] 为 endTime 作为统计区间。
2. 查询 [beginTime, endTime] 区间内 trade_statistics 表的汇总数据（TradeStatisticsMapper.selectVoByTimeBetween）。
3. 计算等长的对照区间 [beginTime - (endTime - beginTime), beginTime)，即紧邻当前区间之前的同期。
4. 查询对照区间的同结构汇总数据。
5. 通过 TradeStatisticsConvert 组装为 DataComparisonRespVO（value 当前、reference 对照）返回。

### 1.3 获得交易状况明细

- **路径**: GET /statistics/trade/list
- **权限**: statistics:trade:query
- **说明**: 按时间范围查询按天维度的交易状况统计明细列表。

**请求参数 (TradeTrendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 时间范围数组，取第 1 个元素为开始时间、第 2 个元素为结束时间 |

**响应**: CommonResult&lt;List&lt;TradeTrendSummaryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | LocalDate | 统计日期 |
| turnoverPrice | Integer | 营业额（= 商品支付金额 + 充值金额） |
| orderPayPrice | Integer | 订单支付金额 |
| walletPayPrice | Integer | 余额支付金额 |
| afterSaleRefundPrice | Integer | 订单退款金额 |
| brokerageSettlementPrice | Integer | 支付佣金金额 |
| rechargePrice | Integer | 充值金额 |
| expensePrice | Integer | 支出金额（= 余额支付金额 + 支付佣金金额 + 商品退款金额） |

**业务逻辑**:
1. 取 times[0]、times[1] 作为统计时间区间。
2. 查询区间内 trade_statistics 表的按天记录列表（TradeStatisticsMapper.selectListByTimeBetween）。
3. 通过 TradeStatisticsConvert.convertList 逐条转换为 TradeTrendSummaryRespVO：date 取统计日；营业额 = 订单支付金额 + 充值金额；支出金额 = 余额支付金额 + 支付佣金金额 + 商品退款金额。
4. 返回明细列表。

### 1.4 导出交易状况明细 Excel

- **路径**: GET /statistics/trade/export-excel
- **权限**: statistics:trade:export
- **说明**: 按时间范围查询交易状况明细并导出为 Excel 文件（文件名「交易状况.xls」，Sheet 名「数据」）。

**请求参数 (TradeTrendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 时间范围数组，取第 1 个元素为开始时间、第 2 个元素为结束时间 |

**响应**: 无 CommonResult 包裹，直接向 HttpServletResponse 写出 Excel 文件流。

TradeTrendSummaryExcelVO 导出列：日期（date）、营业额（turnoverPrice）、商品支付金额（orderPayPrice）、充值金额（rechargePrice）、支出金额（expensePrice）、余额支付金额（walletPayPrice）、支付佣金金额（brokerageSettlementPrice）、商品退款金额（afterSaleRefundPrice），金额列通过 MoneyConvert 转换为「元」展示。

**业务逻辑**:
1. 取 times[0]、times[1] 作为统计时间区间，查询区间内按天的交易统计记录列表。
2. 通过 TradeStatisticsConvert.convertList 转换为 TradeTrendSummaryRespVO 列表。
3. 再通过 convertList02 转换为 TradeTrendSummaryExcelVO 导出列表。
4. 通过 ExcelUtils.write 将数据以「交易状况.xls」写入响应流，完成下载。

### 1.5 获得交易订单数量

- **路径**: GET /statistics/trade/order-count
- **权限**: statistics:trade:query
- **说明**: 获得交易待办数量统计：待发货、待核销、退款中、提现待审核四项计数。

**请求参数**: 无

**响应**: CommonResult&lt;TradeOrderCountRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| undelivered | Long | 待发货（待发货 + 快递配送 的订单数） |
| pickUp | Long | 待核销（已发货 + 用户自提 的订单数） |
| afterSaleApply | Long | 退款中（申请中的售后单数） |
| auditingWithdraw | Long | 提现待审核（审核中的佣金提现单数） |

**业务逻辑**:
1. 调用 TradeOrderStatisticsService.getCountByStatusAndDeliveryType 统计订单状态为「待发货」且配送方式为「快递」的订单数（undelivered）。
2. 统计订单状态为「已发货」且配送方式为「用户自提」的订单数（pickUp，即待核销；代码中 TODO 注明订单支付后门店自提订单需更新为 DELIVERED，目前尚未实现）。
3. 调用 AfterSaleStatisticsService.getCountByStatus 统计售后状态为「申请中（APPLY）」的售后单数（afterSaleApply）。
4. 调用 BrokerageStatisticsService.getWithdrawCountByStatus 统计提现状态为「审核中（AUDITING）」的佣金提现单数（auditingWithdraw）。
5. 通过 TradeStatisticsConvert.convert 汇总为 TradeOrderCountRespVO 返回。

### 1.6 获得交易订单数量对照

- **路径**: GET /statistics/trade/order-comparison
- **权限**: statistics:trade:query
- **说明**: 获得今天与昨天已支付订单的商品数、支付金额对照数据。

**请求参数**: 无

**响应**: CommonResult&lt;DataComparisonRespVO&lt;TradeOrderSummaryRespVO&gt;&gt;

外层为数据对照结构：`value` 为今天数据，`reference` 为昨天数据。

TradeOrderSummaryRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| orderPayCount | Integer | 支付订单商品数 |
| orderPayPrice | Integer | 总支付金额 |

**业务逻辑**:
1. 以今天为统计日期，取 [当天 00:00:00, 23:59:59] 区间，查询已支付（payStatus=true）订单的支付商品数与总支付金额，作为当前数据 value。
2. 以昨天（当前时间减 1 天）为统计日期，按同样口径查询，作为参照数据 reference。
3. 组装为 DataComparisonRespVO 返回。

### 1.7 获得订单量趋势统计

- **路径**: GET /statistics/trade/order-count-trend
- **权限**: statistics:trade:query
- **说明**: 按日期范围类型（天/周/月/年）统计已支付订单量与支付金额趋势，并返回等长的上一周期对照序列。

**请求参数 (TradeOrderTrendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @NotNull(message = "日期范围类型不能为空")、@InEnum(TimeRangeTypeEnum.class) | 日期范围类型：1 天、7 周、30 月、365 年 |
| beginTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 起始时间 |
| endTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 截止时间 |

**响应**: CommonResult&lt;List&lt;DataComparisonRespVO&lt;TradeOrderTrendRespVO&gt;&gt;&gt;

列表元素为数据对照结构：`value` 为当前区间该时点数据，`reference` 为对照区间对应时点数据。

TradeOrderTrendRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | String | 日期（按天或按月分组的时间标识） |
| orderPayCount | Integer | 订单数量（已支付） |
| orderPayPrice | Integer | 订单支付金额 |

**业务逻辑**:
1. 以 [beginTime, endTime] 为当前统计区间，查询已支付订单的统计趋势：当 type 为「年（365）」时按月分组查询（selectListByPayTimeBetweenAndGroupByMonth），其余类型（天/周/月）按天分组查询（selectListByPayTimeBetweenAndGroupByDay）。
2. 以 beginTime 的前一天（beginTime - 1 天）作为对照区间结束点，再向前推等长时长得到对照区间起始点。
3. 按同样分组规则查询对照区间的趋势数据。
4. 将当前序列与对照序列按索引一一配对（CollUtil.get），组装为 List&lt;DataComparisonRespVO&lt;TradeOrderTrendRespVO&gt;&gt; 返回。

**错误码**: 交易统计域为只读聚合查询，Service 层不抛出业务异常，statistics 模块未定义专属错误码。其统计口径依赖的交易/售后/佣金数据的相关错误码见交易模块（前缀 1_011，如售后 1_011_000_100 起、佣金提现 1_011_008_000 起，详见 api-trade.md）。
