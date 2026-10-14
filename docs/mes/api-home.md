# 首页统计接口 (MesHomeStatisticsController)

> 提供 MES 管理后台首页的汇总统计、工单状态分布与生产趋势数据，聚合工单、报工、设备、安灯、维修等模块的统计结果。

## 接口路径前缀

/mes/home-statistics  (Controller: MesHomeStatisticsController)

## 1. 首页统计（MesHomeStatisticsController）

本组全部端点仅需 `mes:home:query` 权限，均为只读统计查询，无请求体。

### 1.1 获得首页汇总统计

- **路径**: GET /mes/home-statistics/summary
- **权限**: mes:home:query
- **说明**: 一次性返回工单、今日/昨日产量、设备状态、安灯报警与维修工单的汇总统计。

**请求参数**: 无

**响应**: CommonResult&lt;MesHomeSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| workOrderActiveCount | Long | 进行中工单数（已确认） |
| workOrderPrepareCount | Long | 待排产工单数（草稿） |
| workOrderFinishedCount | Long | 已完成工单数 |
| todayOutput | BigDecimal | 今日报工总产量 |
| yesterdayOutput | BigDecimal | 昨日报工总产量 |
| todayQualifiedQuantity | BigDecimal | 今日合格品数量 |
| todayUnqualifiedQuantity | BigDecimal | 今日不良品数量 |
| machineryTotal | Long | 设备总数 |
| machineryProducing | Long | 运行中设备数 |
| machineryStop | Long | 停机设备数 |
| machineryMaintenance | Long | 维护中设备数 |
| andonActiveCount | Long | 未处置安灯报警数 |
| repairActiveCount | Long | 未完成维修工单数 |

**业务逻辑**:
1. 按状态分组统计生产工单数量，提取"已确认"（进行中）、"草稿"（待排产）、"已完成"三类工单数填入汇总。
2. 以今天零点为界，查询今日报工汇总（报工总数、合格数、不合格数），无数据时填 0。
3. 查询昨日报工汇总，取昨日报工总产量。
4. 按状态分组统计设备数量，累计总数，并分别提取"运行中"、"停机"、"维护中"三类数量。
5. 分别查询未处置的安灯报警数量与未完成的维修工单数量，填入异常/待办统计后返回。

### 1.2 获得工单状态分布

- **路径**: GET /mes/home-statistics/work-order-status
- **权限**: mes:home:query
- **说明**: 按工单状态枚举逐个返回数量，用于首页饼图/柱状图展示。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MesHomeWorkOrderStatusRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 状态值（0=草稿、1=已确认、2=已完成、3=已取消） |
| statusName | String | 状态名 |
| count | Long | 工单数量 |

**业务逻辑**:
1. 按状态分组统计生产工单数量。
2. 遍历工单状态枚举（草稿/已确认/已完成/已取消）的全部枚举值。
3. 对每个状态从分组统计结果中匹配数量，未命中则记 0，组装为状态分布列表返回。

### 1.3 获得生产趋势

- **路径**: GET /mes/home-statistics/production-trend
- **权限**: mes:home:query
- **说明**: 返回最近 N 天的每日产量/合格品/不良品趋势曲线数据。

**请求参数 (days)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| days | Integer | 否（默认 7） | @Min(1)/@Max(90) | 统计天数，范围 1-90 |

**响应**: CommonResult&lt;List&lt;MesHomeProductionTrendRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | String | 日期（yyyy-MM-dd） |
| quantity | BigDecimal | 当日产量 |
| qualifiedQuantity | BigDecimal | 当日合格品数量 |
| unqualifiedQuantity | BigDecimal | 当日不良品数量 |

**业务逻辑**:
1. 以明天零点为结束时间，向前推 `days` 天计算统计起始时间。
2. 查询时间范围内按日聚合的报工数据（产量、合格数、不合格数），按日期建立映射。
3. 从起始日到结束日逐日遍历，命中数据库数据则取实际值，否则补 0。
4. 组装为连续完整的每日趋势列表返回，保证无数据日期不缺点。
