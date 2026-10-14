# 数据统计接口 (MpStatisticsController)

> 对接微信"数据统计"接口（数据立方 DataCube），按公众号账号与时间范围查询粉丝增减、粉丝累计、消息发送概况、接口分析四类统计数据，数据实时透传自微信服务器，不落库。

## 接口路径前缀

/mp/statistics  (Controller: MpStatisticsController)

## 1. 数据统计

本域 4 个端点共用同一个请求 VO（`MpStatisticsGetReqVO`），且均为 GET 查询，权限统一为 `mp:statistics:query`。

### 1.1 获得粉丝增减数据

- **路径**: GET /mp/statistics/user-summary
- **权限**: mp:statistics:query
- **说明**: 获取指定公众号在某时间段内、按粉丝来源（渠道）拆分的每日新关注 / 取消关注粉丝数量。

**请求参数 (MpStatisticsGetReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| date | LocalDateTime[] | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 查询时间范围（起止时间数组，长度 2） |

**响应**: CommonResult&lt;List&lt;MpStatisticsUserSummaryRespVO&gt;&gt;（列表，每天、每种粉丝来源一条记录）

| 字段 | 类型 | 说明 |
|-----|------|------|
| refDate | LocalDateTime | 日期 |
| userSource | Integer | 粉丝来源（渠道） |
| newUser | Integer | 新关注的粉丝数量 |
| cancelUser | Integer | 取消关注的粉丝数量 |

**业务逻辑**:
1. 通过 `MpServiceFactory.getRequiredMpService(accountId)` 按账号编号获取对应的 `WxMpService` 实例（账号不存在时断言失败报错）。
2. 将时间范围的起止 `LocalDateTime` 转为 `Date`，调用微信数据立方服务 `getDataCubeService().getUserSummary(beginDate, endDate)`。
3. 微信接口调用抛出 `WxErrorException` 时，包装为 `STATISTICS_GET_USER_SUMMARY_FAIL` 错误码并携带微信错误信息返回。
4. 成功结果由 `MpStatisticsConvert.INSTANCE.convertList01` 转换为 `MpStatisticsUserSummaryRespVO` 列表返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_001_000 | 获取粉丝增减数据失败，原因：{} |

### 1.2 获得粉丝累计数据

- **路径**: GET /mp/statistics/user-cumulate
- **权限**: mp:statistics:query
- **说明**: 获取指定公众号在某时间段内每天的累计粉丝总量。

**请求参数 (MpStatisticsGetReqVO)**: 同 1.1（accountId + date）

**响应**: CommonResult&lt;List&lt;MpStatisticsUserCumulateRespVO&gt;&gt;（列表，每天一条记录）

| 字段 | 类型 | 说明 |
|-----|------|------|
| refDate | LocalDateTime | 日期 |
| cumulateUser | Integer | 累计粉丝量 |

**业务逻辑**:
1. 通过 `MpServiceFactory.getRequiredMpService(accountId)` 获取该公众号对应的 `WxMpService` 实例。
2. 将起止时间转为 `Date`，调用微信数据立方服务 `getDataCubeService().getUserCumulate(beginDate, endDate)`。
3. 微信调用失败（`WxErrorException`）时，抛出 `STATISTICS_GET_USER_CUMULATE_FAIL` 错误码并携带微信错误信息。
4. 成功结果由 `MpStatisticsConvert.INSTANCE.convertList02` 转换为 `MpStatisticsUserCumulateRespVO` 列表返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_001_001 | 获得粉丝累计数据失败，原因：{} |

### 1.3 获取消息发送概况数据

- **路径**: GET /mp/statistics/upstream-message
- **权限**: mp:statistics:query
- **说明**: 获取指定公众号在某时间段内粉丝上行（向公众号发送）消息的概况数据。

**请求参数 (MpStatisticsGetReqVO)**: 同 1.1（accountId + date）

**响应**: CommonResult&lt;List&lt;MpStatisticsUpstreamMessageRespVO&gt;&gt;（列表，每天一条记录）

| 字段 | 类型 | 说明 |
|-----|------|------|
| refDate | LocalDateTime | 日期 |
| messageUser | Integer | 上行发送了（向公众号发送了）消息的粉丝数 |
| messageCount | Integer | 上行发送了消息的消息总数 |

**业务逻辑**:
1. 通过 `MpServiceFactory.getRequiredMpService(accountId)` 获取该公众号对应的 `WxMpService` 实例。
2. 将起止时间转为 `Date`，调用微信数据立方服务 `getDataCubeService().getUpstreamMsg(beginDate, endDate)`。
3. 微信调用失败（`WxErrorException`）时，抛出 `STATISTICS_GET_UPSTREAM_MESSAGE_FAIL` 错误码并携带微信错误信息。
4. 成功结果由 `MpStatisticsConvert.INSTANCE.convertList03` 转换为 `MpStatisticsUpstreamMessageRespVO` 列表返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_001_002 | 获得消息发送概况数据失败，原因：{} |

### 1.4 获取接口分析数据

- **路径**: GET /mp/statistics/interface-summary
- **权限**: mp:statistics:query
- **说明**: 获取指定公众号在某时间段内"接口分析"数据（通过服务器配置地址获得消息后被动回复粉丝消息的次数与耗时）。源码中该端点的 `@Operation` 描述写作"获取消息发送概况数据"，与实际返回的接口分析数据不符，以 `RespVO` 字段语义为准。

**请求参数 (MpStatisticsGetReqVO)**: 同 1.1（accountId + date）

**响应**: CommonResult&lt;List&lt;MpStatisticsInterfaceSummaryRespVO&gt;&gt;（列表，每天一条记录）

| 字段 | 类型 | 说明 |
|-----|------|------|
| refDate | LocalDateTime | 日期 |
| callbackCount | Integer | 通过服务器配置地址获得消息后，被动回复粉丝消息的次数 |
| failCount | Integer | 上述动作的失败次数 |
| totalTimeCost | Integer | 总耗时，除以 callbackCount 即为平均耗时 |
| maxTimeCost | Integer | 最大耗时 |

**业务逻辑**:
1. 通过 `MpServiceFactory.getRequiredMpService(accountId)` 获取该公众号对应的 `WxMpService` 实例。
2. 将起止时间转为 `Date`，调用微信数据立方服务 `getDataCubeService().getInterfaceSummary(beginDate, endDate)`。
3. 微信调用失败（`WxErrorException`）时，抛出 `STATISTICS_GET_INTERFACE_SUMMARY_FAIL` 错误码并携带微信错误信息。
4. 成功结果由 `MpStatisticsConvert.INSTANCE.convertList04` 转换为 `MpStatisticsInterfaceSummaryRespVO` 列表返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_001_003 | 获得接口分析数据失败，原因：{} |

## 域级备注

- 本域所有数据均实时调用微信公众号数据统计接口（`wx-mp-sdk` DataCubeService），mp 模块自身不存储统计数据，因此无对应数据库表与 Mapper。
- 4 个端点的业务流程完全一致，仅调用的微信 DataCube 方法、错误码与转换方法（convertList01~04）不同；差异点已在上文逐端点列出。
- 请求 VO 的 `date` 数组通过 `@DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)` 按 `yyyy-MM-dd HH:mm:ss` 格式解析，GET 传参形如 `date[0]=2022-07-01 00:00:00&date[1]=2022-07-01 23:59:59`。
- `MpServiceFactory.getRequiredMpService(accountId)` 内部使用 `Assert.notNull` 校验账号必须已初始化对应的 `WxMpService`，否则直接断言失败（提示"找到对应 id({}) 的 WxMpService，请核实！"）。
