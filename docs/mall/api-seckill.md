# 秒杀接口（时段/活动） (SeckillConfigController / SeckillActivityController)

> 秒杀促销域：管理秒杀时段配置（每天可参与秒杀的时间段）与秒杀活动（商品在指定时段内以秒杀价限时销售），覆盖时段与活动的创建、修改、状态管理、查询等能力。

## 接口路径前缀

- /promotion/seckill-config (Controller: SeckillConfigController) —— 秒杀时段
- /promotion/seckill-activity (Controller: SeckillActivityController) —— 秒杀活动

---

## 1. 秒杀时段（SeckillConfigController）

### 1.1 创建秒杀时段

- **路径**: POST /promotion/seckill-config/create
- **权限**: promotion:seckill-config:create
- **说明**: 新增一个秒杀时段配置，创建前校验时间段与已有时段不重叠。

**请求参数 (SeckillConfigCreateReqVO)**: 继承 SeckillConfigBaseVO，无新增字段

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 秒杀时段名称，如"早上场" |
| startTime | String | 是 | @NotNull | 开始时间点，如 09:00:00 |
| endTime | String | 是 | @NotNull | 结束时间点，如 16:00:00 |
| sliderPicUrls | List&lt;String&gt; | 是 | @NotNull | 秒杀轮播图地址列表 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum） |

附加校验（Base VO 中 @AssertTrue）：开始与结束时间不能相等；开始时间不能在结束时间之后。

**响应**: CommonResult&lt;Long&gt; —— 秒杀时段编号

**业务逻辑**:
1. 校验时间段是否冲突：解析 startTime/endTime 为 LocalTime，查询所有时段配置，判断是否与任一已有时段时间重叠，冲突则抛 SECKILL_CONFIG_TIME_CONFLICTS。
2. 转换为 SeckillConfigDO 插入数据库。
3. 返回新时段编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_009_001 | 秒杀时段冲突 |

### 1.2 更新秒杀时段

- **路径**: PUT /promotion/seckill-config/update
- **权限**: promotion:seckill-config:update
- **说明**: 修改已有时段配置，校验存在性与时间段冲突。

**请求参数 (SeckillConfigUpdateReqVO)**: 继承 SeckillConfigBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 时段编号 |
| name | String | 是 | @NotNull | 秒杀时段名称 |
| startTime | String | 是 | @NotNull | 开始时间点 |
| endTime | String | 是 | @NotNull | 结束时间点 |
| sliderPicUrls | List&lt;String&gt; | 是 | @NotNull | 秒杀轮播图 |
| status | Integer | 是 | @NotNull | 状态 |

（同样继承 Base VO 的 @AssertTrue 时间先后校验）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验时段是否存在，不存在抛 SECKILL_CONFIG_NOT_EXISTS。
2. 校验时间段冲突（与其它时段比对时排除自己）。
3. 转换为 DO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_009_000 | 秒杀时段不存在 |
| 1_013_009_001 | 秒杀时段冲突 |

### 1.3 修改时段配置状态

- **路径**: PUT /promotion/seckill-config/update-status
- **权限**: promotion:seckill-config:update
- **说明**: 开启/关闭某个秒杀时段。

**请求参数 (SeckillConfigUpdateStatusReqVo)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 时段配置编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 关闭） |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验时段是否存在，不存在抛 SECKILL_CONFIG_NOT_EXISTS。
2. 仅更新该时段的 status 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_009_000 | 秒杀时段不存在 |

### 1.4 删除秒杀时段

- **路径**: DELETE /promotion/seckill-config/delete
- **权限**: promotion:seckill-config:delete
- **说明**: 按编号删除时段配置。

**请求参数**: 无（Query 参数 id：Long，必填，时段编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验时段存在，不存在抛 SECKILL_CONFIG_NOT_EXISTS。
2. 按 id 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_009_000 | 秒杀时段不存在 |

### 1.5 获得秒杀时段

- **路径**: GET /promotion/seckill-config/get
- **权限**: promotion:seckill-config:query
- **说明**: 按编号查询单个时段详情。

**请求参数**: 无（Query 参数 id：Long，必填，时段编号）

**响应**: CommonResult&lt;SeckillConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 秒杀时段名称 |
| startTime | String | 开始时间点 |
| endTime | String | 结束时间点 |
| sliderPicUrls | List&lt;String&gt; | 秒杀轮播图 |
| status | Integer | 状态 |
| seckillActivityCount | Integer | 该时段下的秒杀活动数量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 SeckillConfigDO。
2. 通过 SeckillConfigConvert 转换为 RespVO 返回。

### 1.6 获得所有秒杀时段列表

- **路径**: GET /promotion/seckill-config/list
- **权限**: promotion:seckill-config:query
- **说明**: 返回全部时段（不分页、不过滤状态），响应字段同 1.5 的 SeckillConfigRespVO。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;SeckillConfigRespVO&gt;&gt;

**业务逻辑**:
1. 查询全部时段列表（selectList）。
2. 转换为 RespVO 列表返回。

### 1.7 获得所有开启状态的秒杀时段精简列表

- **路径**: GET /promotion/seckill-config/simple-list
- **权限**: 已认证（无 @PreAuthorize，主要用于前端下拉选项）
- **说明**: 返回开启状态的时段精简信息，按开始时间升序排序。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;SeckillConfigSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 秒杀时段名称 |
| startTime | String | 开始时间点 |
| endTime | String | 结束时间点 |

**业务逻辑**:
1. 按状态 = 开启（CommonStatusEnum.ENABLE）查询时段列表。
2. 按 startTime 升序排序后返回。

### 1.8 获得秒杀时间段分页

- **路径**: GET /promotion/seckill-config/page
- **权限**: promotion:seckill-config:query
- **说明**: 分页查询时段配置，响应字段同 1.5 的 SeckillConfigRespVO。

**请求参数 (SeckillConfigPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码 |
| pageSize | Integer | 否 | 分页参数 | 每页条数 |
| name | String | 否 | - | 秒杀时段名称（模糊匹配） |
| status | Integer | 否 | - | 状态 |

**响应**: CommonResult&lt;PageResult&lt;SeckillConfigRespVO&gt;&gt;

**业务逻辑**:
1. 按查询条件分页查询时段配置。
2. 转换为分页 RespVO 返回。

**错误码**（该域通用）:

| 错误码 | 说明 |
|-------|------|
| 1_013_009_000 | 秒杀时段不存在 |
| 1_013_009_001 | 秒杀时段冲突 |
| 1_013_009_004 | 秒杀时段已关闭（时段被引用校验时抛出） |

---

## 2. 秒杀活动（SeckillActivityController）

### 2.1 创建秒杀活动

- **路径**: POST /promotion/seckill-activity/create
- **权限**: promotion:seckill-activity:create
- **说明**: 创建秒杀活动并批量设置参与的 SKU 及秒杀价、库存。

**请求参数 (SeckillActivityCreateReqVO)**: 继承 SeckillActivityBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| spuId | Long | 是 | @NotNull | 秒杀活动商品 SPU 编号 |
| name | String | 是 | @NotNull | 秒杀活动名称 |
| remark | String | 否 | - | 备注 |
| startTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 活动开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 活动结束时间 |
| sort | Integer | 是 | @NotNull | 排序 |
| configIds | List&lt;Long&gt; | 是 | @NotNull | 参与的秒杀时段 id 列表 |
| totalLimitCount | Integer | 否 | - | 总限购数量 |
| singleLimitCount | Integer | 否 | - | 单次限购数量 |
| products | List&lt;SeckillProductBaseVO&gt; | 是（业务校验） | - | 秒杀商品列表 |

其中 SeckillProductBaseVO 字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| skuId | Long | 是 | @NotNull | 商品 SKU 编号 |
| seckillPrice | Integer | 是 | @NotNull | 秒杀金额，单位：分 |
| stock | Integer | 是 | @NotNull | 秒杀库存 |

**响应**: CommonResult&lt;Long&gt; —— 秒杀活动编号

**业务逻辑**:
1. 校验商品秒杀时段冲突：所有 configIds 对应时段必须存在且开启（否则抛 SECKILL_CONFIG_NOT_EXISTS / SECKILL_CONFIG_DISABLE）；查询该 SPU 下所有开启状态的秒杀活动（排除自己），若存在与所传 configIds 有交集的活动则抛 SECKILL_ACTIVITY_SPU_CONFLICTS。
2. 校验商品存在：SPU 不存在抛 SPU_NOT_EXISTS；每个秒杀商品的 skuId 必须属于该 SPU 的 SKU 列表，否则抛 SKU_NOT_EXISTS。
3. 插入秒杀活动：初始状态为开启，stock 取所有秒杀商品库存之和，totalStock = stock。
4. 批量插入秒杀商品（SeckillProductDO）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_008_002 | 存在商品参加了其它秒杀活动，秒杀时段冲突 |
| 1_013_009_000 | 秒杀时段不存在 |
| 1_013_009_004 | 秒杀时段已关闭 |
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 2.2 更新秒杀活动

- **路径**: PUT /promotion/seckill-activity/update
- **权限**: promotion:seckill-activity:update
- **说明**: 修改活动基础信息与秒杀商品配置（已关闭的活动不可修改）。

**请求参数 (SeckillActivityUpdateReqVO)**: 继承 SeckillActivityBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 秒杀活动编号 |
| spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| name | String | 是 | @NotNull | 秒杀活动名称 |
| remark | String | 否 | - | 备注 |
| startTime | LocalDateTime | 是 | @NotNull | 活动开始时间 |
| endTime | LocalDateTime | 是 | @NotNull | 活动结束时间 |
| sort | Integer | 是 | @NotNull | 排序 |
| configIds | List&lt;Long&gt; | 是 | @NotNull | 秒杀时段 id 列表 |
| totalLimitCount | Integer | 否 | - | 总限购数量 |
| singleLimitCount | Integer | 否 | - | 单次限购数量 |
| products | List&lt;SeckillProductBaseVO&gt; | 是 | - | 秒杀商品列表（字段同 2.1） |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验活动存在，且状态不是已关闭，否则抛 SECKILL_ACTIVITY_UPDATE_FAIL_STATUS_CLOSED。
2. 校验商品秒杀时段冲突（校验逻辑同创建，排除自己）。
3. 校验 SPU 与全部 SKU 存在。
4. 更新活动：stock 更新为新商品库存之和；若新 stock 大于原 totalStock 则同步上调 totalStock。
5. 对比新老商品列表（按 skuId 匹配），批量新增、修改、删除秒杀商品。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_008_000 | 秒杀活动不存在 |
| 1_013_008_002 | 存在商品参加了其它秒杀活动，秒杀时段冲突 |
| 1_013_008_003 | 秒杀活动已关闭，不能修改 |
| 1_013_009_000 | 秒杀时段不存在 |
| 1_013_009_004 | 秒杀时段已关闭 |
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 2.3 关闭秒杀活动

- **路径**: PUT /promotion/seckill-activity/close
- **权限**: promotion:seckill-activity:close
- **说明**: 将活动状态置为关闭。

**请求参数**: 无（Query 参数 id：Long，必填，活动编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验活动存在，不存在抛 SECKILL_ACTIVITY_NOT_EXISTS。
2. 若活动已是关闭状态，抛 SECKILL_ACTIVITY_CLOSE_FAIL_STATUS_CLOSED。
3. 更新活动状态为关闭（DISABLE）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_008_000 | 秒杀活动不存在 |
| 1_013_008_005 | 秒杀活动已关闭，不能重复关闭 |

### 2.4 删除秒杀活动

- **路径**: DELETE /promotion/seckill-activity/delete
- **权限**: promotion:seckill-activity:delete
- **说明**: 删除活动及其秒杀商品（仅允许删除已关闭的活动）。

**请求参数**: 无（Query 参数 id：Long，必填，活动编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验活动存在，不存在抛 SECKILL_ACTIVITY_NOT_EXISTS。
2. 若活动仍为开启状态，抛 SECKILL_ACTIVITY_DELETE_FAIL_STATUS_NOT_CLOSED_OR_END。
3. 删除活动，并删除该活动下全部秒杀商品。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_008_000 | 秒杀活动不存在 |
| 1_013_008_004 | 秒杀活动未关闭或未结束，不能删除 |

### 2.5 获得秒杀活动详情

- **路径**: GET /promotion/seckill-activity/get
- **权限**: promotion:seckill-activity:query
- **说明**: 查询活动基础信息及其秒杀商品列表。

**请求参数**: 无（Query 参数 id：Long，必填，活动编号）

**响应**: CommonResult&lt;SeckillActivityDetailRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 秒杀活动编号 |
| spuId | Long | 商品 SPU 编号 |
| name | String | 活动名称 |
| remark | String | 备注 |
| startTime | LocalDateTime | 活动开始时间 |
| endTime | LocalDateTime | 活动结束时间 |
| sort | Integer | 排序 |
| configIds | List&lt;Long&gt; | 秒杀时段 id 列表 |
| totalLimitCount | Integer | 总限购数量 |
| singleLimitCount | Integer | 单次限购数量 |
| products | List&lt;SeckillProductRespVO&gt; | 秒杀商品列表 |

SeckillProductRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 秒杀参与商品编号 |
| skuId | Long | 商品 SKU 编号 |
| seckillPrice | Integer | 秒杀金额，单位：分 |
| stock | Integer | 秒杀库存 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询活动。
2. 按 activityId 查询该活动的秒杀商品列表。
3. 组合转换为 SeckillActivityDetailRespVO 返回。

### 2.6 获得秒杀活动分页

- **路径**: GET /promotion/seckill-activity/page
- **权限**: promotion:seckill-activity:query
- **说明**: 分页查询活动，并拼接商品名称、主图、市场价等 SPU 信息。

**请求参数 (SeckillActivityPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码 |
| pageSize | Integer | 否 | 分页参数 | 每页条数 |
| name | String | 否 | - | 秒杀活动名称 |
| status | Integer | 否 | - | 活动状态 |
| configId | Long | 否 | - | 秒杀时段 id |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;SeckillActivityRespVO&gt;&gt;，除 2.5 的基础字段外还包含：

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 活动状态 |
| totalPrice | Integer | 订单实付金额，单位：分 |
| stock | Integer | 秒杀库存（剩余） |
| totalStock | Integer | 秒杀总库存 |
| orderCount | Integer | 新增订单数 |
| userCount | Integer | 付款人数 |
| createTime | LocalDateTime | 创建时间 |
| spuName | String | 商品名称（从 SPU 拼接） |
| picUrl | String | 商品主图（从 SPU 拼接） |
| marketPrice | Integer | 商品市场价，单位：分（从 SPU 拼接） |
| seckillPrice | Integer | 秒杀金额，单位：分（取 products 中最小 price） |

**业务逻辑**:
1. 按条件分页查询活动列表。
2. 若结果为空，直接返回空分页。
3. 按活动 id 集合批量查询秒杀商品列表。
4. 通过 ProductSpuApi 按 spuId 集合批量查询 SPU 信息。
5. 转换并拼接为 SeckillActivityRespVO 分页返回。

### 2.7 获得秒杀活动列表（基于活动编号数组）

- **路径**: GET /promotion/seckill-activity/list-by-ids
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 按 ids 批量查询活动，自动过滤掉已关闭的活动，响应字段同 2.6 的 SeckillActivityRespVO。

**请求参数**: 无（Query 参数 ids：List&lt;Long&gt;，必填，活动编号数组）

**响应**: CommonResult&lt;List&lt;SeckillActivityRespVO&gt;&gt;

**业务逻辑**:
1. 按 ids 查询活动列表，并移除状态为关闭（DISABLE）的活动；若为空返回空列表。
2. 按活动 id 集合批量查询秒杀商品，通过 ProductSpuApi 批量查询 SPU 信息。
3. 转换拼接为 RespVO 列表返回。

**错误码**（该域通用）:

| 错误码 | 说明 |
|-------|------|
| 1_013_008_000 | 秒杀活动不存在 |
| 1_013_008_003 | 秒杀活动已关闭，不能修改 |
| 1_013_008_004 | 秒杀活动未关闭或未结束，不能删除 |
| 1_013_008_005 | 秒杀活动已关闭，不能重复关闭 |
| 1_013_008_006 | 秒杀失败，原因：秒杀库存不足 |
| 1_013_008_002 | 存在商品参加了其它秒杀活动，秒杀时段冲突 |
