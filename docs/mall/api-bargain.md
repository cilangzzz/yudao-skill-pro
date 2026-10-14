# 砍价接口 (BargainActivityController / BargainRecordController / BargainHelpController)

> 商城营销砍价功能的管理后台接口，覆盖砍价活动（BargainActivity）的创建/修改/关闭/删除/查询、砍价记录（BargainRecord）分页查询、砍价助力（BargainHelp）分页查询。

## 接口路径前缀

- /promotion/bargain-activity  (Controller: BargainActivityController)
- /promotion/bargain-record  (Controller: BargainRecordController)
- /promotion/bargain-help  (Controller: BargainHelpController)

---

## 1. 砍价活动（BargainActivityController）

### 1.1 创建砍价活动

- **路径**: POST /promotion/bargain-activity/create
- **权限**: promotion:bargain-activity:create
- **说明**: 创建一个砍价活动，状态初始为开启，总库存等于活动库存。

**请求参数 (BargainActivityCreateReqVO)**: 继承 BargainActivityBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 是 | @NotNull | 砍价活动名称 |
| spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| skuId | Long | 是 | @NotNull | 商品 skuId |
| bargainFirstPrice | Integer | 是 | @NotNull | 砍价起始价格，单位：分 |
| bargainMinPrice | Integer | 是 | @NotNull | 砍价底价，单位：分 |
| stock | Integer | 是 | @NotNull | 活动库存 |
| totalLimitCount | Integer | 是 | @NotNull | 总限购数量 |
| startTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 活动开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 活动结束时间 |
| helpMaxCount | Integer | 是 | @NotNull | 最大助力次数 |
| bargainCount | Integer | 是 | @NotNull | 最大帮砍次数 |
| randomMinPrice | Integer | 是 | @NotNull | 用户每次砍价的最小金额，单位：分 |
| randomMaxPrice | Integer | 是 | @NotNull | 用户每次砍价的最大金额，单位：分 |

**响应**: CommonResult&lt;Long&gt;（活动编号）

**业务逻辑**: 1. 校验商品 SPU 是否已参加其它开启中的砍价活动（validateBargainConflict，冲突抛 BARGAIN_ACTIVITY_SPU_CONFLICTS）。 2. 校验商品 SKU 是否存在（ProductSkuApi.getSku，不存在抛 SKU_NOT_EXISTS）。 3. 转换为 BargainActivityDO 插入，totalStock 置为 stock，status 置为开启（CommonStatusEnum.ENABLE）。 4. 返回新活动编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_012_001 | 存在商品参加了其它砍价活动 |
| 1_008_006_000 | 商品 SKU 不存在（product 模块错误码） |

### 1.2 更新砍价活动

- **路径**: PUT /promotion/bargain-activity/update
- **权限**: promotion:bargain-activity:update
- **说明**: 修改砍价活动信息，已关闭的活动不允许修改。

**请求参数 (BargainActivityUpdateReqVO)**: 继承 BargainActivityBaseVO，在 1.1 全部字段基础上增加：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**: 1. 校验活动是否存在（不存在抛 BARGAIN_ACTIVITY_NOT_EXISTS）。 2. 校验活动状态，已关闭（DISABLE）则抛 BARGAIN_ACTIVITY_STATUS_DISABLE，不允许修改。 3. 校验商品 SPU 是否参加了其它砍价活动（排除自身）。 4. 校验商品 SKU 是否存在。 5. 更新活动；若新 stock 大于原 totalStock，则同步把总库存更新为新 stock。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_012_000 | 砍价活动不存在 |
| 1_013_012_002 | 砍价活动已关闭，不能修改 |
| 1_013_012_001 | 存在商品参加了其它砍价活动 |
| 1_008_006_000 | 商品 SKU 不存在（product 模块错误码） |

### 1.3 关闭砍价活动

- **路径**: PUT /promotion/bargain-activity/close
- **权限**: promotion:bargain-activity:close
- **说明**: 将开启中的砍价活动关闭（状态置为 DISABLE）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required) | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**: 1. 校验砍价活动是否存在（不存在抛 BARGAIN_ACTIVITY_NOT_EXISTS）。 2. 校验活动状态，已关闭则抛 BARGAIN_ACTIVITY_STATUS_DISABLE。 3. 更新活动状态为关闭（CommonStatusEnum.DISABLE）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_012_000 | 砍价活动不存在 |
| 1_013_012_002 | 砍价活动已关闭，不能修改 |

### 1.4 删除砍价活动

- **路径**: DELETE /promotion/bargain-activity/delete
- **权限**: promotion:bargain-activity:delete
- **说明**: 删除砍价活动，仅允许删除已关闭或已结束的活动。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required) | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**: 1. 校验活动是否存在（不存在抛 BARGAIN_ACTIVITY_NOT_EXISTS）。 2. 校验活动状态，若仍处于开启（ENABLE）则抛 BARGAIN_ACTIVITY_DELETE_FAIL_STATUS_NOT_CLOSED_OR_END。 3. 执行删除（deleteById）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_012_000 | 砍价活动不存在 |
| 1_013_012_003 | 砍价活动未关闭或未结束，不能删除 |

### 1.5 获得砍价活动

- **路径**: GET /promotion/bargain-activity/get
- **权限**: promotion:bargain-activity:query
- **说明**: 按编号获得砍价活动详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required) | 活动编号 |

**响应**: CommonResult&lt;BargainActivityRespVO&gt;（不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 活动编号 |
| name | String | 砍价活动名称 |
| spuId | Long | 商品 SPU 编号 |
| skuId | Long | 商品 skuId |
| bargainFirstPrice | Integer | 砍价起始价格，单位：分 |
| bargainMinPrice | Integer | 砍价底价，单位：分 |
| stock | Integer | 活动库存 |
| totalLimitCount | Integer | 总限购数量 |
| startTime | LocalDateTime | 活动开始时间 |
| endTime | LocalDateTime | 活动结束时间 |
| helpMaxCount | Integer | 最大助力次数 |
| bargainCount | Integer | 最大帮砍次数 |
| randomMinPrice | Integer | 用户每次砍价的最小金额，单位：分 |
| randomMaxPrice | Integer | 用户每次砍价的最大金额，单位：分 |
| status | Integer | 活动状态（0 开启、1 关闭） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 根据编号查询活动（selectById），经 BargainActivityConvert 转换为 RespVO 返回。

### 1.6 获得砍价活动分页

- **路径**: GET /promotion/bargain-activity/page
- **权限**: promotion:bargain-activity:query
- **说明**: 分页获得砍价活动列表，并拼接商品信息与砍价/助力统计。

**请求参数 (BargainActivityPageReqVO)**: 继承 PageParam（pageNo 页码，默认 1，@NotNull/@Min(1)；pageSize 每页条数，默认 10，@NotNull/@Min(1)/@Max(200)）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（基类 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（基类 PageParam） | 每页条数 |
| name | String | 否 | 无 | 砍价名称，模糊匹配 |
| status | Integer | 否 | 无 | 活动状态 |

**响应**: CommonResult&lt;PageResult&lt;BargainActivityPageItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 活动编号 |
| spuName | String | 商品名称（拼接自 SPU） |
| picUrl | String | 商品主图（拼接自 SPU） |
| status | Integer | 活动状态（0 开启、1 关闭） |
| totalStock | Integer | 活动总库存 |
| createTime | LocalDateTime | 创建时间 |
| （继承 BargainActivityBaseVO 字段） | - | name/spuId/skuId/bargainFirstPrice/bargainMinPrice/stock/totalLimitCount/startTime/endTime/helpMaxCount/bargainCount/randomMinPrice/randomMaxPrice |
| recordUserCount | Integer | 总砍价的用户数量（统计） |
| recordSuccessUserCount | Integer | 成功砍价的用户数量（统计） |
| helpUserCount | Integer | 帮助砍价的用户数量（统计） |

**业务逻辑**: 1. 按 name/status 分页查询砍价活动。 2. 结果为空时直接返回空分页。 3. 通过 ProductSpuApi.getSpuList 拼接商品名称与主图。 4. 通过 bargainRecordService.getBargainRecordUserCountMap 统计每个活动的总砍价用户数（不限状态）与成功砍价用户数（SUCCESS 状态）。 5. 通过 bargainHelpService.getBargainHelpUserCountMapByActivity 统计每个活动的助力用户数。 6. 经 BargainActivityConvert.convertPage 组装分页项返回。

---

## 2. 砍价记录（BargainRecordController）

### 2.1 获得砍价记录分页

- **路径**: GET /promotion/bargain-record/page
- **权限**: promotion:bargain-record:query
- **说明**: 分页查询用户发起的砍价记录，拼接用户、活动信息与帮砍次数。

**请求参数 (BargainRecordPageReqVO)**: 继承 PageParam（pageNo/pageSize 同 1.6）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（基类 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（基类 PageParam） | 每页条数 |
| status | Integer | 否 | 无 | 砍价状态（1 进行中、2 成功、3 失败） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;BargainRecordPageItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 记录编号 |
| createTime | LocalDateTime | 创建时间 |
| helpCount | Integer | 帮砍次数（统计自助力表） |
| nickname | String | 用户昵称（拼接自会员） |
| avatar | String | 用户头像（拼接自会员） |
| activity | BargainActivityRespVO | 砍价活动信息（嵌套，结构同 1.5） |
| （继承 BargainRecordBaseVO 字段） | - | activityId/userId/spuId/skuId/bargainFirstPrice/bargainPrice/status/orderId/endTime |

**业务逻辑**: 1. 按 status/createTime 分页查询砍价记录。 2. 结果为空时直接返回空分页。 3. 通过 MemberUserApi.getUserMap 拼接用户昵称与头像。 4. 通过 bargainActivityService.getBargainActivityList 拼接砍价活动信息。 5. 通过 bargainHelpService.getBargainHelpUserCountMapByRecord 统计每条记录的帮砍次数。 6. 经 BargainRecordConvert.convertPage 组装分页项返回。

---

## 3. 砍价助力（BargainHelpController）

### 3.1 获得砍价助力分页

- **路径**: GET /promotion/bargain-help/page
- **权限**: promotion:bargain-help:query
- **说明**: 分页查询砍价助力（帮砍）记录，拼接助力用户信息。

**请求参数 (BargainHelpPageReqVO)**: 继承 PageParam（pageNo/pageSize 同 1.6）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（基类 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（基类 PageParam） | 每页条数 |
| recordId | Long | 否 | 无 | 砍价记录编号 |

**响应**: CommonResult&lt;PageResult&lt;BargainHelpRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 砍价助力编号 |
| createTime | LocalDateTime | 创建时间 |
| nickname | String | 助力用户昵称（拼接自会员） |
| avatar | String | 助力用户头像（拼接自会员） |
| （继承 BargainHelpBaseVO 字段） | - | userId/activityId/recordId/reducePrice（减少砍价金额，单位：分） |

**业务逻辑**: 1. 按 recordId 分页查询砍价助力记录。 2. 结果为空时直接返回空分页。 3. 通过 MemberUserApi.getUserMap 拼接助力用户的昵称与头像。 4. 经 BargainHelpConvert.convertPage 组装返回。

---

## 附：砍价域错误码总览（promotion 模块 ErrorCodeConstants）

| 错误码 | 说明 |
|-------|------|
| 1_013_012_000 | 砍价活动不存在 |
| 1_013_012_001 | 存在商品参加了其它砍价活动 |
| 1_013_012_002 | 砍价活动已关闭，不能修改 |
| 1_013_012_003 | 砍价活动未关闭或未结束，不能删除 |
| 1_013_012_004 | 砍价活动库存不足 |
| 1_013_012_005 | 砍价活动已关闭 |
| 1_013_012_006 | 砍价活动已经结束 |
| 1_013_013_000 | 砍价记录不存在 |
| 1_013_013_001 | 参与失败，您已经参与当前砍价活动 |
| 1_013_013_002 | 参与失败，您已达到当前砍价活动的参与上限 |
| 1_013_013_004 | 下单失败，砍价未成功 |
| 1_013_013_005 | 下单失败，该砍价已经下单 |
| 1_013_014_000 | 助力失败，砍价记录不处于进行中 |
| 1_013_014_001 | 助力失败，不能助力自己 |
| 1_013_014_002 | 助力失败，您已达到当前砍价活动的助力上限 |
| 1_013_014_003 | 助力失败，请重试 |
| 1_013_014_004 | 助力失败，您已经助力过了 |
