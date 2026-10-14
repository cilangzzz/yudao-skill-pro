# 拼团（活动/记录）接口 (CombinationActivityController / CombinationRecordController)

> 管理后台的拼团促销能力：拼团活动的创建/修改/关闭/删除/查询，以及拼团记录的分页查询与统计概要。

## 接口路径前缀

- /promotion/combination-activity  (Controller: CombinationActivityController)
- /promotion/combination-record  (Controller: CombinationRecordController)

---

## 1. 拼团活动管理（CombinationActivityController）

### 1.1 创建拼团活动

- **路径**: POST /promotion/combination-activity/create
- **权限**: promotion:combination-activity:create
- **说明**: 创建拼团活动及其拼团商品（SKU 级价格配置），新活动固定为开启状态。

**请求参数 (CombinationActivityCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 是 | @NotNull | 拼团名称 |
| spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| totalLimitCount | Integer | 是 | @NotNull | 总限购数量 |
| singleLimitCount | Integer | 是 | @NotNull | 单次限购数量 |
| startTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 活动开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 活动结束时间 |
| userSize | Integer | 是 | @NotNull | 开团人数（成团所需人数） |
| virtualGroup | Boolean | 是 | @NotNull | 是否虚拟成团 |
| limitDuration | Integer | 是 | @NotNull | 限制时长（小时），团长开团后的成团有效期 |
| products | List&lt;CombinationProductBaseVO&gt; | 是 | @Valid | 拼团商品列表 |

其中 CombinationProductBaseVO：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号 |
| combinationPrice | Integer | 是 | @NotNull | 拼团价格，单位分 |

**响应**: CommonResult&lt;Long&gt;（新活动编号）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 拼团活动编号 |

**业务逻辑**:
1. 校验商品冲突：查询所有开启中的拼团活动，若存在其它活动已使用同一 SPU，抛出 COMBINATION_ACTIVITY_SPU_CONFLICTS。
2. 校验商品存在：调用 ProductSpuApi 校验 SPU 存在（否则 SPU_NOT_EXISTS）；再校验请求中每个 skuId 都属于该 SPU（否则 SKU_NOT_EXISTS）。
3. 插入拼团活动记录，状态固定设置为开启（CommonStatusEnum.ENABLE）。
4. 将 products 批量转换为 CombinationProductDO 并批量插入拼团商品表。
5. 返回新活动编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_010_001 | 存在商品参加了其它拼团活动 |
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 1.2 更新拼团活动

- **路径**: PUT /promotion/combination-activity/update
- **权限**: promotion:combination-activity:update
- **说明**: 修改拼团活动基础信息，并按 diff 增量维护活动下的拼团商品。

**请求参数 (CombinationActivityUpdateReqVO)**: 继承 CombinationActivityBaseVO（字段同 1.1 的 name/totalLimitCount/startTime 等，均必填），另有：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 活动编号 |
| products | List&lt;CombinationProductBaseVO&gt; | 是 | @Valid | 拼团商品列表（结构同 1.1） |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验活动存在（不存在抛 COMBINATION_ACTIVITY_NOT_EXISTS）。
2. 校验活动状态：已关闭（DISABLE）的活动不允许修改，抛 COMBINATION_ACTIVITY_STATUS_DISABLE_NOT_UPDATE。
3. 校验商品冲突：其它开启中的活动不得使用同一 SPU（排除自身活动）。
4. 校验 SPU 与全部 SKU 存在。
5. 更新拼团活动主记录。
6. 对比新旧拼团商品列表（以 skuId 为匹配键），通过 diffList 计算出需新增、更新、删除的记录并批量执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_010_000 | 拼团活动不存在 |
| 1_013_010_002 | 拼团活动已关闭不能修改 |
| 1_013_010_001 | 存在商品参加了其它拼团活动 |
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 1.3 关闭拼团活动

- **路径**: PUT /promotion/combination-activity/close
- **权限**: promotion:combination-activity:close
- **说明**: 将开启中的拼团活动状态置为关闭。

**请求参数**: 无（Query 参数 id）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required) | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验活动存在。
2. 若活动已是关闭状态，抛 COMBINATION_ACTIVITY_STATUS_DISABLE_NOT_UPDATE。
3. 更新活动状态为关闭（CommonStatusEnum.DISABLE）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_010_000 | 拼团活动不存在 |
| 1_013_010_002 | 拼团活动已关闭不能修改 |

### 1.4 删除拼团活动

- **路径**: DELETE /promotion/combination-activity/delete
- **权限**: promotion:combination-activity:delete
- **说明**: 删除拼团活动，仅允许删除已关闭的活动。

**请求参数**: 无（Query 参数 id）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required) | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验活动存在。
2. 校验活动状态：开启中的活动不允许删除，抛 COMBINATION_ACTIVITY_DELETE_FAIL_STATUS_NOT_CLOSED_OR_END。
3. 删除拼团活动记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_010_000 | 拼团活动不存在 |
| 1_013_010_003 | 拼团活动未关闭或未结束，不能删除 |

### 1.5 获得拼团活动

- **路径**: GET /promotion/combination-activity/get
- **权限**: promotion:combination-activity:query
- **说明**: 按编号获取拼团活动详情，附拼团商品列表。

**请求参数**: 无（Query 参数 id）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required) | 活动编号 |

**响应**: CommonResult&lt;CombinationActivityRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 活动编号 |
| name | String | 拼团名称 |
| spuId | Long | 商品 SPU 编号 |
| totalLimitCount | Integer | 总限购数量 |
| singleLimitCount | Integer | 单次限购数量 |
| startTime / endTime | LocalDateTime | 活动起止时间 |
| userSize | Integer | 开团人数 |
| virtualGroup | Boolean | 是否虚拟成团 |
| limitDuration | Integer | 限制时长（小时） |
| createTime | LocalDateTime | 创建时间 |
| products | List&lt;CombinationProductRespVO&gt; | 拼团商品（含 id、spuId、skuId、combinationPrice、createTime） |
| spuName | String | 商品 SPU 名字（来自 SPU） |
| picUrl | String | 商品图片（来自 SPU） |
| marketPrice | Integer | 商品市场价，单位分（来自 SPU） |
| combinationPrice | Integer | 拼团金额，单位分（取 products 中最小价） |

**业务逻辑**:
1. 校验并获取活动（不存在抛 COMBINATION_ACTIVITY_NOT_EXISTS）。
2. 按活动编号查询其下全部拼团商品。
3. 通过 CombinationActivityConvert 组装为 RespVO 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_010_000 | 拼团活动不存在 |

### 1.6 获得拼团活动列表（基于活动编号数组）

- **路径**: GET /promotion/combination-activity/list-by-ids
- **权限**: 已认证（无 @PreAuthorize，登录即可访问）
- **说明**: 按编号数组获取开启中的拼团活动列表（自动过滤已关闭活动），供其它模块/前端联动使用。

**请求参数**: 无（Query 参数 ids）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam(required) | 活动编号数组 |

**响应**: CommonResult&lt;List&lt;CombinationActivityRespVO&gt;&gt;（字段同 1.5 的 RespVO）

**业务逻辑**:
1. 按编号数组查询活动列表，并剔除状态为关闭（DISABLE）的活动；为空则返回空列表。
2. 查询这些活动下的拼团商品列表。
3. 通过 ProductSpuApi 批量获取活动对应 SPU 信息。
4. 组装为 RespVO 列表（含 spuName/picUrl/marketPrice）返回。

### 1.7 获得拼团活动分页

- **路径**: GET /promotion/combination-activity/page
- **权限**: promotion:combination-activity:query
- **说明**: 分页查询拼团活动，并统计每个活动的开团/成团组数与购买次数。

**请求参数 (CombinationActivityPageReqVO)**: 继承 PageParam（pageNo/pageNo 默认 1、pageSize 默认 10），另有：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | - | 拼团名称（模糊匹配） |
| status | Integer | 否 | - | 活动状态（CommonStatusEnum） |

**响应**: CommonResult&lt;PageResult&lt;CombinationActivityPageItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 活动编号 |
| name / spuId / totalLimitCount / singleLimitCount / startTime / endTime / userSize / virtualGroup / limitDuration | - | 同 BaseVO（见 1.1） |
| createTime | LocalDateTime | 创建时间 |
| status | Integer | 活动状态 |
| products | List&lt;CombinationProductRespVO&gt; | 拼团商品 |
| spuName | String | 商品名称（来自 SPU） |
| picUrl | String | 商品主图（来自 SPU） |
| marketPrice | Integer | 商品市场价，单位分 |
| groupCount | Integer | 开团组数（团长记录数） |
| groupSuccessCount | Integer | 成团组数（成团状态的团长记录数） |
| recordCount | Integer | 购买次数（该活动全部记录数） |

**业务逻辑**:
1. 按条件分页查询拼团活动，空结果直接返回空分页。
2. 统计开团组数：按活动统计 headId=HEAD_ID_GROUP 的记录数。
3. 统计成团组数：按活动统计 headId=HEAD_ID_GROUP 且状态为成团（SUCCESS）的记录数。
4. 统计购买次数：按活动统计全部拼团记录数。
5. 查询各活动的拼团商品及对应 SPU 信息。
6. 组装为分页项 RespVO（含统计字段）返回。

**错误码**: 无专属错误码。

---

## 2. 拼团记录（CombinationRecordController）

### 2.1 获得拼团记录分页

- **路径**: GET /promotion/combination-record/page
- **权限**: promotion:combination-record:query
- **说明**: 分页查询拼团记录，附带活动信息与团长昵称。

**请求参数 (CombinationRecordReqPageVO)**: 继承 PageParam（pageNo/pageSize），另有：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| status | Integer | 否 | @InEnum(CombinationRecordStatusEnum) | 拼团状态 |
| headId | Long | 否 | - | 团长编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;CombinationRecordPageItemRespVO&gt;&gt;，分页项继承 CombinationRecordBaseVO：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 拼团记录编号 |
| activityId | Long | 拼团活动编号 |
| headId | Long | 团长编号（HEAD_ID_GROUP 表示自己是团长） |
| userId / nickname / avatar | Long / String / String | 参团用户编号、昵称、头像 |
| spuId / skuId / spuName / picUrl | Long / Long / String / String | 商品 SPU/SKU 编号、名字、图片 |
| expireTime | LocalDateTime | 过期时间 |
| userSize / userCount | Integer | 可参团人数 / 已参团人数 |
| status | Integer | 拼团状态（CombinationRecordStatusEnum） |
| virtualGroup | Boolean | 是否虚拟成团 |
| startTime / endTime | LocalDateTime | 开始时间（订单付款后）/ 结束时间（成团或失败时间） |
| headNickname | String | 团长昵称（补齐字段） |
| activity | CombinationActivityRespVO | 关联的拼团活动信息 |

**业务逻辑**:
1. 按条件分页查询拼团记录。
2. 批量查询记录关联的拼团活动与拼团商品，组装进分页项（activity 字段）。
3. 收集分页内有效的 headId（非空、>0 且不为 HEAD_ID_GROUP），批量查询对应团长记录。
4. 遍历分页项补齐团长昵称：团长记录自身（headId 为空或等于 HEAD_ID_GROUP）取自己昵称，团成员取团长记录的昵称。
5. 返回分页结果。

**错误码**: 无专属错误码。

### 2.2 获得拼团记录概要信息

- **路径**: GET /promotion/combination-record/get-summary
- **权限**: promotion:combination-record:query
- **说明**: 拼团记录页面顶部的统计概要（参与用户数、成团数、虚拟成团数）。

**请求参数**: 无

**响应**: CommonResult&lt;CombinationRecordSummaryVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| userCount | Long | 所有拼团记录（参与拼团的用户数量） |
| successCount | Long | 成团记录数 |
| virtualGroupCount | Long | 虚拟成团记录数 |

**业务逻辑**:
1. 统计拼团用户参与数量（按用户去重计数）。
2. 统计成团记录数：状态为成团（SUCCESS）且 headId=HEAD_ID_GROUP 的团长记录数。
3. 统计虚拟成团记录数：virtualGroup=TRUE 且 headId=HEAD_ID_GROUP 的团长记录数。
4. 组装概要 VO 返回。

---

## 附：本域错误码一览（promotion 模块 1_013_010_000 起 / 1_013_011_000 起）

| 错误码 | 说明 |
|-------|------|
| 1_013_010_000 | 拼团活动不存在 |
| 1_013_010_001 | 存在商品参加了其它拼团活动 |
| 1_013_010_002 | 拼团活动已关闭不能修改 |
| 1_013_010_003 | 拼团活动未关闭或未结束，不能删除 |
| 1_013_010_004 | 拼团失败，原因：拼团活动已关闭 |
| 1_013_010_005 | 拼团失败，原因：拼团活动商品不存在 |
| 1_013_010_006 | 拼团失败，原因：拼团活动商品库存不足 |
| 1_013_011_000 | 拼团不存在 |
| 1_013_011_001 | 拼团失败，已参与过该拼团 |
| 1_013_011_002 | 拼团失败，父拼团不存在 |
| 1_013_011_003 | 拼团失败，拼团人数已满 |
| 1_013_011_004 | 拼团失败，原因：存在该活动正在进行的拼团记录 |
| 1_013_011_005 | 拼团失败，活动未开始 |
| 1_013_011_006 | 拼团失败，活动已经结束 |
| 1_013_011_007 | 拼团失败，原因：单次限购超出 |
| 1_013_011_008 | 拼团失败，原因：超出总购买次数 |
| 1_013_011_009 | 拼团失败，原因：存在未支付订单，请先支付 |

其中 1_013_010_004 ~ 1_013_010_006 与 1_013_011_000 ~ 1_013_011_009 主要在交易下单链路（App 端参与拼团、校验参团资格）抛出；管理端活动 CRUD 直接使用 1_013_010_000 ~ 1_013_010_003 及商品域的 1_008_005_000（SPU 不存在）、1_008_006_000（SKU 不存在）。
