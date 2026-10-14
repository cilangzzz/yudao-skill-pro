# 满减送活动接口 (RewardActivityController)

> 商城促销模块的满减送活动管理：按商品范围（全部/指定商品/指定品类）配置满 N 元或满 N 件的多级优惠规则（减价、包邮、送积分、送优惠券），支持活动生命周期管理（创建、更新、关闭、删除）与分页查询。

## 接口路径前缀

/promotion/reward-activity  (Controller: RewardActivityController)

## 1. 活动管理

### 1.1 创建满减送活动

- **路径**: POST /promotion/reward-activity/create
- **权限**: promotion:reward-activity:create
- **说明**: 新建满减送活动，创建后状态固定为开启。

**请求参数 (RewardActivityCreateReqVO)**: 继承满减送活动 BaseVO 全部字段（见下表），无额外字段。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 是 | @NotNull | 活动标题 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@Future | 结束时间，必须大于当前时间 |
| remark | String | 否 | 无 | 备注 |
| conditionType | Integer | 是 | @NotNull、@InEnum(PromotionConditionTypeEnum) | 条件类型：10 满 N 元、20 满 N 件 |
| productScope | Integer | 是 | @NotNull、@InEnum(PromotionProductScopeEnum) | 商品范围：1 全部商品、2 指定商品、3 指定品类 |
| productScopeValues | List\<Long\> | 否 | @AssertTrue（商品范围非全部时不能为空） | 商品范围编号的数组（SPU 编号或分类编号） |
| rules | List\<Rule\> | 否 | @Valid（递归校验子对象） | 优惠规则的数组 |

**Rule 子对象字段**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| limit | Integer | 是 | @Min(1) | 优惠门槛：满 N 元（单位分）或满 N 件 |
| discountPrice | Integer | 是 | @Min(1) | 优惠价格（单位分） |
| freeDelivery | Boolean | 是 | @NotNull | 是否包邮 |
| point | Integer | 否 | @AssertTrue（不能小于 0） | 赠送的积分 |
| giveCouponTemplateCounts | Map\<Long, Integer\> | 否 | 无 | 赠送的优惠券编号 → 数量映射 |

**响应**: CommonResult\<Long\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 活动编号 |

**业务逻辑**:
1. 校验商品范围：商品范围为指定商品时校验 SPU 存在，指定品类时校验商品分类存在。
2. 校验商品范围冲突：查询所有开启状态的活动，先排除活动时间与本次不重叠的，再按三种情况交叉校验——任一方商品范围为全部则直接冲突；品类对品类校验分类编号是否重叠；品类对商品/商品对商品则查询 SPU 归属分类后判断是否重叠，冲突即抛错。
3. 将请求转换为 RewardActivityDO，状态固定设置为开启（ENABLE），插入数据库。
4. 返回新活动编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_006_001 | 该时间段存在商品参加了其它满减送活动 |
| 1_013_006_005 | 与该时间段满减送活动【{}】商品范围冲突，原因：{} |

### 1.2 更新满减送活动

- **路径**: PUT /promotion/reward-activity/update
- **权限**: promotion:reward-activity:update
- **说明**: 修改未关闭的满减送活动。

**请求参数 (RewardActivityUpdateReqVO)**: 继承满减送活动 BaseVO 全部字段（同 1.1），额外字段如下。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 活动编号 |

**响应**: CommonResult\<Boolean\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 更新成功返回 true |

**业务逻辑**:
1. 校验活动存在，不存在抛 REWARD_ACTIVITY_NOT_EXISTS。
2. 校验活动状态：已关闭（DISABLE）的活动不允许修改。
3. 校验商品范围（同创建逻辑）。
4. 校验商品范围冲突（同创建逻辑，但排除自身活动）。
5. 更新活动记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_006_000 | 满减送活动不存在 |
| 1_013_006_002 | 满减送活动已关闭，不能修改 |
| 1_013_006_001 | 该时间段存在商品参加了其它满减送活动 |
| 1_013_006_005 | 与该时间段满减送活动【{}】商品范围冲突，原因：{} |

### 1.3 关闭满减送活动

- **路径**: PUT /promotion/reward-activity/close
- **权限**: promotion:reward-activity:close
- **说明**: 将开启中的活动置为关闭状态。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 活动编号 |

**响应**: CommonResult\<Boolean\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 关闭成功返回 true |

**业务逻辑**:
1. 校验活动存在。
2. 校验活动状态：已关闭的活动不能重复关闭。
3. 将活动状态更新为关闭（DISABLE）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_006_000 | 满减送活动不存在 |
| 1_013_006_004 | 满减送活动已关闭，不能重复关闭 |

### 1.4 删除满减送活动

- **路径**: DELETE /promotion/reward-activity/delete
- **权限**: promotion:reward-activity:delete
- **说明**: 删除已关闭的活动。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 活动编号 |

**响应**: CommonResult\<Boolean\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**:
1. 校验活动存在。
2. 校验活动状态：未关闭（ENABLE）的活动不能删除。
3. 删除活动记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_006_000 | 满减送活动不存在 |
| 1_013_006_003 | 满减送活动未关闭，不能删除 |

### 1.5 获得满减送活动

- **路径**: GET /promotion/reward-activity/get
- **权限**: promotion:reward-activity:query
- **说明**: 按编号获取活动详情。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 活动编号 |

**响应**: CommonResult\<RewardActivityRespVO\>，字段继承满减送活动 BaseVO 全部字段（同 1.1），额外字段如下。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 活动编号 |
| status | Integer | 活动状态：1 开启、0 关闭 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询活动记录并返回（不存在时返回 null，不抛错）。

### 1.6 获得满减送活动分页

- **路径**: GET /promotion/reward-activity/page
- **权限**: promotion:reward-activity:query
- **说明**: 分页查询活动列表。

**请求参数 (RewardActivityPageReqVO)**: 继承 PageParam（pageNo 页码，默认 1；pageSize 每页条数，默认 10），额外字段如下。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | 无 | 活动标题，模糊匹配 |
| status | Integer | 否 | 无 | 活动状态 |

**响应**: CommonResult\<PageResult\<RewardActivityRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | List\<RewardActivityRespVO\> | 活动列表，字段同 1.5 |
| total | Long | 总条数 |

**业务逻辑**:
1. 按标题模糊匹配、状态精确匹配（均可选）构建查询条件，按 id 倒序分页查询。
