# 会员统计接口 (MemberStatisticsController)

> 提供管理后台的会员统计能力：会员实时汇总、会员分析（访客/下单/成交/客单价漏斗 + 对照数据）、按省份/性别/终端的分布统计、用户数量今昨对照、以及按日期的注册数量趋势。

## 接口路径前缀

/statistics/member  (Controller: MemberStatisticsController)

## 1. 会员统计查询

> 全部端点均为只读统计查询，权限统一为 `statistics:member:query`。

### 1.1 获得会员统计（实时统计）

- **路径**: GET /statistics/member/summary
- **权限**: statistics:member:query
- **说明**: 实时统计会员总数、充值会员数、充值金额与支出金额（消费金额）。

**请求参数**: 无

**响应**: CommonResult&lt;MemberSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| userCount | Integer | 会员数量 |
| rechargeUserCount | Integer | 充值会员数量 |
| rechargePrice | Integer | 充值金额，单位：分 |
| expensePrice | Integer | 支出金额，单位：分（只计算 mall 交易订单的支付金额，不考虑退款） |

**业务逻辑**: 
1. 调用 PayWalletStatisticsService.getUserRechargeSummary(null, null) 查询全部时间的钱包充值汇总（充值会员数、充值金额）。
2. 调用 TradeStatisticsService.getExpensePrice(null, null) 实时计算支出金额：按 trade_order 的已支付 pay_price 汇总（不走 TradeStatistics 统计表，保证实时性）。
3. 调用 MemberStatisticsMapper.selectUserCount(null, null) 统计会员总数。
4. 通过 MemberStatisticsConvert 拼接三者返回 MemberSummaryRespVO。

### 1.2 获得会员分析数据

- **路径**: GET /statistics/member/analyse
- **权限**: statistics:member:query
- **说明**: 按时间范围查询会员分析数据，包含 访客 → 下单 → 成交 用户漏斗、客单价，以及与上一等长区间的对照数据。

**请求参数 (MemberAnalyseReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(pattern = yyyy-MM-dd HH:mm:ss) | 时间范围数组，times[0] 为开始时间、times[1] 为结束时间（Query 参数绑定） |

**响应**: CommonResult&lt;MemberAnalyseRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| visitUserCount | Integer | 访客数量（按 IP 去重） |
| orderUserCount | Integer | 下单用户数量 |
| payUserCount | Integer | 成交用户数量 |
| atv | Integer | 客单价，单位：分（payPrice / payUserCount） |
| comparison | DataComparisonRespVO&lt;MemberAnalyseDataRespVO&gt; | 对照数据（当前区间 vs 上一等长区间） |

**MemberAnalyseDataRespVO**（comparison.value / comparison.reference）:

| 字段 | 类型 | 说明 |
|-----|------|------|
| registerUserCount | Integer | 会员数量（区间内注册数） |
| visitUserCount | Integer | 活跃用户数量（区间内访问数） |
| rechargeUserCount | Integer | 充值会员数量 |

**业务逻辑**: 
1. 从 reqVO.times 解析出 beginTime、endTime。
2. 调用 getMemberAnalyseComparisonData 查询分析对照数据：先统计当前区间数据（注册用户数 selectUserCount、活跃用户数 apiAccessLogStatisticsService.getUserCount、充值会员数 getUserRechargeSummary.rechargeUserCount）；再计算对照区间 —— referenceEndDate = beginTime 减 1 天（防止时间重叠），referenceBeginDate = referenceEndDate 再往前推等长时间段，同样统计三项指标。
3. 调用 TradeOrderStatisticsService.getPayUserCount 查询区间内成交用户数量（按 create_time 查询，保证 访问 > 下单 > 支付 漏斗维度统一）。
4. 若成交用户数大于 0，调用 getOrderPayPrice 查询支付金额并计算客单价 atv = payPrice / payUserCount（整数除法），否则 atv 为 0。
5. 调用 ApiAccessLogStatisticsService.getIpCount(MEMBER) 查询区间内访客数量（按 IP 去重）。
6. 调用 TradeOrderStatisticsService.getOrderUserCount 查询区间内下单用户数量。
7. 通过 MemberStatisticsConvert 将 访客数、下单用户数、成交用户数、客单价、对照数据 拼接为 MemberAnalyseRespVO 返回。

### 1.3 按照省份，获得会员统计列表

- **路径**: GET /statistics/member/area-statistics-list
- **权限**: statistics:member:query
- **说明**: 按省份维度统计会员数量、下单/支付会员数与支付金额，返回全量省份列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberAreaStatisticsRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| areaId | Integer | 省份编号（“未知” 行为 null） |
| areaName | String | 省份名称 |
| userCount | Integer | 会员数量 |
| orderCreateUserCount | Integer | 下单的会员数量 |
| orderPayUserCount | Integer | 支付订单的会员数量 |
| orderPayPrice | Integer | 订单支付金额，单位：分 |

**业务逻辑**: 
1. 调用 MemberStatisticsMapper.selectSummaryListByAreaId() 按地区统计会员数量，并通过 AreaUtils.getParentIdByType(areaId, PROVINCE) 归并到省份维度（同省数量求和）。
2. 调用 TradeOrderStatisticsService.getSummaryListByAreaId() 按地区统计订单数据，同样归并到省份维度，合并时对 orderCreateUserCount、orderPayUserCount、orderPayPrice 分别累加（null 按 0 处理）。
3. 获取全国所有省份列表（AreaUtils.getByType(PROVINCE)），并追加一条 id 为 null、名称为“未知”的记录。
4. 通过 MemberStatisticsConvert.convertList 将省份列表与用户数、订单数两张 Map 拼接为统计列表返回。

### 1.4 按照性别，获得会员统计列表

- **路径**: GET /statistics/member/sex-statistics-list
- **权限**: statistics:member:query
- **说明**: 按性别维度统计会员数量。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberSexStatisticsRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| sex | Integer | 性别（对应 DictDataConstants 性别字典值） |
| userCount | Integer | 会员数量 |

**业务逻辑**: 
1. 直接调用 MemberStatisticsMapper.selectSummaryListBySex() 按 sex 分组统计会员数量并返回。

### 1.5 按照终端，获得会员统计列表

- **路径**: GET /statistics/member/terminal-statistics-list
- **权限**: statistics:member:query
- **说明**: 按注册终端维度统计会员数量。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberTerminalStatisticsRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| terminal | Integer | 终端（对应 TerminalEnum 终端编号） |
| userCount | Integer | 会员数量 |

**业务逻辑**: 
1. 直接调用 MemberStatisticsMapper.selectSummaryListByRegisterTerminal() 按注册终端分组统计会员数量并返回。

### 1.6 获得用户数量对照

- **路径**: GET /statistics/member/user-count-comparison
- **权限**: statistics:member:query
- **说明**: 统计今日与昨日的注册用户数量和访问用户数量（UV），做今日/昨日对照。

**请求参数**: 无

**响应**: CommonResult&lt;DataComparisonRespVO&lt;MemberCountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| value | MemberCountRespVO | 当前数据（今日） |
| reference | MemberCountRespVO | 参照数据（昨日） |

**MemberCountRespVO**（value / reference）:

| 字段 | 类型 | 说明 |
|-----|------|------|
| visitUserCount | Integer | 用户访问量（按 IP 去重） |
| registerUserCount | Integer | 注册用户数量 |

**业务逻辑**: 
1. 计算今日时间范围：beginOfToday = 当天 00:00:00，endOfToday = 当天 23:59:59。
2. 计算昨日时间范围：beginOfYesterday / endOfYesterday 为今日往前推 1 天的起止。
3. 私有方法 getUserCount 统计单个时间范围：注册用户数（selectUserCount）+ 访问用户数（ApiAccessLogStatisticsService.getIpCount(MEMBER)，按 IP 去重）。
4. 分别以今日、昨日范围统计，组装为 DataComparisonRespVO（value = 今日，reference = 昨日）返回。

### 1.7 获得会员注册数量列表

- **路径**: GET /statistics/member/register-count-list
- **权限**: statistics:member:query
- **说明**: 按日期统计时间范围内的会员注册数量，用于注册趋势图。

**请求参数 (MemberAnalyseReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(pattern = yyyy-MM-dd HH:mm:ss) | 时间范围数组，times[0] 为开始时间、times[1] 为结束时间（Query 参数绑定） |

**响应**: CommonResult&lt;List&lt;MemberRegisterCountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | LocalDate | 日期（格式 yyyy-MM-dd） |
| count | Integer | 该日注册数量 |

**业务逻辑**: 
1. 从 reqVO.times 解析出 beginTime、endTime。
2. 调用 MemberStatisticsMapper.selectListByCreateTimeBetween(beginTime, endTime) 按 create_time 所在日期分组统计注册数量并返回。
