# 积分商城活动接口 (PointActivityController)

> 提供管理后台的积分商城活动管理能力：创建/更新/关闭/删除积分商城活动，查询活动详情、分页与列表，活动商品（SKU 级）的积分、金额、库存配置与冲突校验。

## 接口路径前缀

/promotion/point-activity  (Controller: PointActivityController)

## 1. 积分商城活动管理

### 1.1 创建积分商城活动

- **路径**: POST /promotion/point-activity/create
- **权限**: promotion:point-activity:create
- **说明**: 新增一个积分商城活动及其商品（SKU 级）配置，活动状态固定为开启。

**请求参数 (PointActivitySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 积分商城活动编号（创建时不传） |
| spuId | Long | 是 | @NotNull | 积分商城活动商品 SPU 编号 |
| remark | String | 否 | - | 备注 |
| sort | Integer | 是 | @NotNull | 排序 |
| products | List&lt;PointProductSaveReqVO&gt; | 否 | - | 积分商城商品列表 |

**PointProductSaveReqVO**（products 元素）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 积分商城商品编号 |
| activityId | Long | 是 | @NotNull | 积分商城活动编号 |
| spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号 |
| count | Integer | 是 | @NotNull | 可兑换数量（单次限购数量） |
| point | Integer | 是 | @NotNull | 兑换积分 |
| price | Integer | 是 | @NotNull | 兑换金额，单位：分 |
| stock | Integer | 是 | @NotNull | 积分商城商品库存 |
| activityStatus | Integer | 是 | @NotNull | 积分商城商品状态 |

**响应**: CommonResult&lt;Long&gt;（活动编号）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的积分商城活动编号 |

**业务逻辑**: 
1. 校验商品 SPU 是否存在（productSpuApi.getSpu），不存在抛 SPU_NOT_EXISTS；再校验所有 SKU 是否属于该 SPU，不存在抛 SKU_NOT_EXISTS。
2. 校验商品是否已参加其它开启中的积分商城活动，冲突抛 POINT_ACTIVITY_SPU_CONFLICTS。
3. 插入积分商城活动：状态固定为开启（ENABLE），库存 stock 取所有商品 stock 之和，总库存 totalStock 等于 stock。
4. 批量插入积分商城活动商品（补充 spuId、activityId、activityStatus）。
5. 返回活动编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |
| 1_013_007_001 | 存在商品参加了其它积分商城活动 |

### 1.2 更新积分商城活动

- **路径**: PUT /promotion/point-activity/update
- **权限**: promotion:point-activity:update
- **说明**: 修改积分商城活动及其商品配置，已关闭的活动不允许修改。

**请求参数 (PointActivitySaveReqVO)**: 同 1.1（id 必传，为要更新的活动编号）

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 固定返回 true |

**业务逻辑**: 
1. 校验活动存在（不存在抛 POINT_ACTIVITY_NOT_EXISTS），若活动已关闭（DISABLE）抛 POINT_ACTIVITY_UPDATE_FAIL_STATUS_CLOSED。
2. 校验商品 SPU 与所有 SKU 是否存在。
3. 校验商品是否已参加其它开启中的积分商城活动（排除自身），冲突抛 POINT_ACTIVITY_SPU_CONFLICTS。
4. 更新活动：stock 取所有商品 stock 之和；若新 stock 大于原 totalStock，则同步更新 totalStock。
5. 对比新老商品列表（按 skuId 差异比较），批量新增、修改、删除积分商城商品。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_007_000 | 积分商城活动不存在 |
| 1_013_007_001 | 存在商品参加了其它积分商城活动 |
| 1_013_007_002 | 积分商城活动已关闭，不能修改 |
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 1.3 关闭积分商城活动

- **路径**: PUT /promotion/point-activity/close
- **权限**: promotion:point-activity:close
- **说明**: 关闭指定积分商城活动，并同步关闭其下所有商品。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 固定返回 true |

**业务逻辑**: 
1. 校验活动存在，不存在抛 POINT_ACTIVITY_NOT_EXISTS。
2. 若活动已关闭（DISABLE）抛 POINT_ACTIVITY_CLOSE_FAIL_STATUS_CLOSED。
3. 更新活动状态为关闭（DISABLE）。
4. 同步更新该活动下所有积分商城商品的 activityStatus 为关闭。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_007_000 | 积分商城活动不存在 |
| 1_013_007_004 | 积分商城活动已关闭，不能重复关闭 |

### 1.4 删除积分商城活动

- **路径**: DELETE /promotion/point-activity/delete
- **权限**: promotion:point-activity:delete
- **说明**: 删除指定积分商城活动及其商品，开启中的活动不允许删除。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 固定返回 true |

**业务逻辑**: 
1. 校验活动存在，不存在抛 POINT_ACTIVITY_NOT_EXISTS。
2. 若活动仍在开启状态（ENABLE）抛 POINT_ACTIVITY_DELETE_FAIL_STATUS_NOT_CLOSED_OR_END。
3. 删除积分商城活动。
4. 查询并删除该活动下所有积分商城商品。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_007_000 | 积分商城活动不存在 |
| 1_013_007_003 | 积分商城活动未关闭或未结束，不能删除 |

## 2. 积分商城活动查询

### 2.1 获得积分商城活动

- **路径**: GET /promotion/point-activity/get
- **权限**: promotion:point-activity:query
- **说明**: 按编号获得积分商城活动详情，附带活动商品列表。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 活动编号 |

**响应**: CommonResult&lt;PointActivityRespVO&gt;（活动不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 积分商城活动编号 |
| spuId | Long | 积分商城活动商品 SPU 编号 |
| status | Integer | 活动状态 |
| stock | Integer | 积分商城活动库存（剩余库存，积分兑换时扣减） |
| totalStock | Integer | 积分商城活动总库存 |
| remark | String | 备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |
| products | List&lt;PointProductRespVO&gt; | 积分商城商品列表 |
| spuName | String | 商品名称（从 SPU name 拼接） |
| picUrl | String | 商品主图（从 SPU picUrl 拼接） |
| marketPrice | Integer | 商品市场价，单位：分（从 SPU 拼接） |
| point | Integer | 兑换积分（取该活动下兑换积分最少的 SKU） |
| price | Integer | 兑换金额，单位：分（取该活动下兑换积分最少的 SKU） |

**PointProductRespVO**（products 元素）:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 积分商城商品编号 |
| activityId | Long | 积分商城活动编号 |
| spuId | Long | 商品 SPU 编号 |
| skuId | Long | 商品 SKU 编号 |
| count | Integer | 可兑换数量 |
| point | Integer | 兑换积分 |
| price | Integer | 兑换金额，单位：分 |
| stock | Integer | 积分商城商品库存 |
| activityStatus | Integer | 积分商城商品状态 |

**业务逻辑**: 
1. 按 id 查询积分商城活动，不存在时返回 null。
2. 查询该活动下的积分商城商品列表，转换为 PointProductRespVO 填充到 products。

### 2.2 获得积分商城活动分页

- **路径**: GET /promotion/point-activity/page
- **权限**: promotion:point-activity:query
- **说明**: 分页获得积分商城活动列表，并拼接商品与 SPU 信息。

**请求参数 (PointActivityPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 继承 PageParam（@NotNull/@Min） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 继承 PageParam（@NotNull/@Min） | 每页条数 |
| status | Integer | 否 | - | 活动状态 |

**响应**: CommonResult&lt;PageResult&lt;PointActivityRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | List&lt;PointActivityRespVO&gt; | 活动列表，字段同 2.1 |
| total | Long | 总条数 |

**业务逻辑**: 
1. 按条件分页查询积分商城活动。
2. 批量查询活动下的积分商城商品，按 activityId 分组。
3. 通过 productSpuApi.getSpuMap 批量查询活动关联的 SPU 信息。
4. 每个活动取兑换积分最少（point 最小）的商品，回填活动的 point 与 price 字段。
5. 回填 SPU 的 spuName、picUrl、marketPrice 字段。

### 2.3 获得积分商城活动列表（基于活动编号数组）

- **路径**: GET /promotion/point-activity/list-by-ids
- **权限**: 已认证（未标注 @PreAuthorize，仅要求登录）
- **说明**: 基于活动编号数组获得开启中的积分商城活动列表，并拼接商品与 SPU 信息（供商城前端使用）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam | 活动编号数组，如 [1024, 1025] |

**响应**: CommonResult&lt;List&lt;PointActivityRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | List&lt;PointActivityRespVO&gt; | 开启中的活动列表，字段同 2.1 |

**业务逻辑**: 
1. 按编号数组查询活动列表，并过滤掉已关闭（禁用状态）的活动；为空时返回空列表。
2. 批量查询活动商品与 SPU 信息。
3. 每个活动取兑换积分最少的商品，回填 point 与 price，并回填 SPU 的 spuName、picUrl、marketPrice。

## 域级错误码汇总

来源：`yudao-module-promotion` 的 ErrorCodeConstants（前缀 1_013_007）及 `yudao-module-product` 的 ErrorCodeConstants。

| 错误码 | 说明 |
|-------|------|
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |
| 1_013_007_000 | 积分商城活动不存在 |
| 1_013_007_001 | 存在商品参加了其它积分商城活动 |
| 1_013_007_002 | 积分商城活动已关闭，不能修改 |
| 1_013_007_003 | 积分商城活动未关闭或未结束，不能删除 |
| 1_013_007_004 | 积分商城活动已关闭，不能重复关闭 |
| 1_013_007_005 | 积分商品兑换失败，原因：积分商城活动已关闭 |
| 1_013_007_006 | 积分商品兑换失败，原因：单次限购超出 |
| 1_013_007_007 | 积分商品兑换失败，原因：商品不存在 |
| 1_013_007_008 | 积分商品兑换失败，原因：积分商品库存不足 |

> 注：1_013_007_005 ~ 1_013_007_008 主要由 App 端兑换流程及 Service 内部库存扣减（updatePointStockDecr）、兑换校验（validateJoinPointActivity）使用，管理端接口本身不直接抛出。
