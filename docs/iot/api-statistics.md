# 数据统计接口 (IotStatisticsController)

> 提供 IoT 平台全局数据总览（品类/产品/设备/消息数量、设备状态分布、品类设备分布）与设备消息按时间维度的趋势统计。

## 接口路径前缀

/iot/statistics  (Controller: IotStatisticsController)

## 1. 数据统计

### 1.1 获取全局数据统计

- **路径**: GET /iot/statistics/get-summary
- **权限**: 已认证（无 @PreAuthorize 注解，仅要求登录）
- **说明**: 一次返回平台总览数据：品类/产品/设备/设备消息的总数量与今日新增数量、设备在线状态分布、各品类下的设备数量分布。

**请求参数**: 无

**响应**: CommonResult&lt;IotStatisticsSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| productCategoryCount | Long | 品类数量 |
| productCount | Long | 产品数量 |
| deviceCount | Long | 设备数量 |
| deviceMessageCount | Long | 上报（设备消息）数量 |
| productCategoryTodayCount | Long | 今日新增品类数量 |
| productTodayCount | Long | 今日新增产品数量 |
| deviceTodayCount | Long | 今日新增设备数量 |
| deviceMessageTodayCount | Long | 今日新增上报数量 |
| deviceOnlineCount | Long | 在线设备数量 |
| deviceOfflineCount | Long | 离线设备数量 |
| deviceInactiveCount | Long | 待激活设备数量 |
| productCategoryDeviceCounts | Map&lt;String, Integer&gt; | 按品类名称统计的设备数量 Map |

**业务逻辑**（统计逻辑直接实现在 Controller 中，聚合调用四个 Service）:
1. 分别调用品类、产品、设备、设备消息四个 Service 的 Count 方法（参数为 null，不限定时间），获取四类数据的总数。
2. 取今日零点（LocalDateTimeUtils.getToday()）作为时间下限，再次调用同一组 Count 方法，获得四类数据的今日新增数量。
3. 调用 IotProductCategoryService 的 getProductCategoryDeviceCountMap()：查询全部分类与全部产品、按产品分组统计设备数量，再按产品所属分类累加，得到「分类名 → 设备数」Map。
4. 调用 IotDeviceService 的 getDeviceCountMapByState() 获取按状态分组的设备数量 Map，从中取 ONLINE / OFFLINE / INACTIVE 三种状态的值（缺失时补 0），填充在线、离线、待激活三个字段。
5. 组装 IotStatisticsSummaryRespVO 返回。

### 1.2 获取设备消息数据统计

- **路径**: GET /iot/statistics/get-device-message-summary-by-date
- **权限**: 已认证（无 @PreAuthorize 注解，仅要求登录）
- **说明**: 按时间间隔（小时/天/周/月/季度/年）统计指定时间范围内的设备上行、下行消息数量趋势。

**请求参数 (IotStatisticsDeviceMessageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| interval | Integer | 是（Schema 标注必填，无 @NotNull） | @InEnum(DateIntervalEnum) | 时间间隔类型：0 小时 / 1 天 / 2 周 / 3 月 / 4 季度 / 5 年 |
| times | LocalDateTime[] | 否 | @Size(min = 2, max = 2)、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 时间范围，固定两个元素：起始时间、结束时间 |

**响应**: CommonResult&lt;List&lt;IotStatisticsDeviceMessageSummaryByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴（按 interval 格式化的日期区间标签，如 202401） |
| upstreamCount | Integer | 上行消息数量 |
| downstreamCount | Integer | 下行消息数量 |

**业务逻辑**（IotDeviceMessageServiceImpl#getDeviceMessageSummaryByDate）:
1. 将 times[0]、times[1] 转为毫秒时间戳，调用 TDengine Mapper（IotDeviceMessageMapper）的 selectDeviceMessageCountGroupByDate，对超级表 device_message 按 TIMETRUNCATE(ts, 1h) 逐小时分组，分别统计 upstream = true（上行）与 upstream = false（下行）的消息数。
2. 使用 LocalDateTimeUtils.getDateRangeList 按请求的 interval 将整个时间范围切分为若干个连续的时间区间。
3. 遍历每个时间区间，从逐小时统计结果中筛选落在该区间内的记录，分别累加 upstream_count 与 downstream_count。
4. 按区间格式化时间轴标签（LocalDateTimeUtils.formatDateRange），组装为 IotStatisticsDeviceMessageSummaryByDateRespVO 列表返回。

**错误码**: 该域无专属错误码（未在 ErrorCodeConstants 中定义 statistics 段错误码）。
