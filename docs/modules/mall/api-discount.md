# 限时折扣活动接口 (DiscountActivityController)

> 管理后台限时折扣活动管理：创建/修改/关闭/删除活动，并为活动商品（SKU 级）设置满减金额或折扣百分比优惠，支持分页查询。

## 接口路径前缀

/promotion/discount-activity  (Controller: DiscountActivityController)

---

## 1. 活动写操作

### 1.1 创建限时折扣活动

- **路径**: POST /promotion/discount-activity/create
- **权限**: promotion:discount-activity:create
- **说明**: 创建限时折扣活动，并批量指定参与活动的商品 SKU 及其优惠方式。

**请求参数 (DiscountActivityCreateReqVO)**（继承 DiscountActivityBaseVO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 活动标题 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间（格式 yyyy-MM-dd HH:mm:ss） |
| endTime | LocalDateTime | 是 | @NotNull | 结束时间（格式 yyyy-MM-dd HH:mm:ss） |
| remark | String | 否 | - | 备注 |
| products | List&lt;Product&gt; | 是 | @NotEmpty、@Valid（级联校验） | 商品列表 |
| products[].spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| products[].skuId | Long | 是 | @NotNull | 商品 SKU 编号 |
| products[].discountType | Integer | 是 | @NotNull、@InEnum(PromotionDiscountTypeEnum) | 优惠类型：1 满减（优惠金额）、2 折扣（百分比） |
| products[].discountPercent | Integer | 条件必填 | @AssertTrue：折扣类型时必须在 1~9999（对应 0.01%~99.99%） | 折扣百分比 |
| products[].discountPrice | Integer | 条件必填 | @Min(0)、@AssertTrue：满减类型时不能为空 | 优惠金额（单位：分） |

**响应**: CommonResult&lt;Long&gt; —— 活动编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的限时折扣活动编号 |

**业务逻辑**:
1. 校验商品是否冲突：查询所有开启中的限时折扣活动（更新时排除自身），比对请求中的 SPU 与已有活动商品的 SPU，存在交集则抛出冲突错误并提示活动名称。
2. 校验商品是否存在：通过 ProductSkuApi 按 SPU 查询 SKU 列表，逐个校验请求中的 skuId 是否存在。
3. 插入限时折扣活动，状态固定为开启（CommonStatusEnum.ENABLE）。
4. 批量插入活动商品（DiscountProductDO），冗余活动编号、活动名称、活动状态、活动开始/结束时间。
5. 返回活动编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_001_001 | 存在商品参加了其它限时折扣活动【{}】 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 1.2 更新限时折扣活动

- **路径**: PUT /promotion/discount-activity/update
- **权限**: promotion:discount-activity:update
- **说明**: 修改未关闭的限时折扣活动，并按 diff 结果同步增删改活动商品。

**请求参数 (DiscountActivityUpdateReqVO)**（继承 DiscountActivityBaseVO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 活动编号 |
| name | String | 是 | @NotNull | 活动标题 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间（格式 yyyy-MM-dd HH:mm:ss） |
| endTime | LocalDateTime | 是 | @NotNull | 结束时间（格式 yyyy-MM-dd HH:mm:ss） |
| remark | String | 否 | - | 备注 |
| products | List&lt;Product&gt; | 是 | @NotEmpty、@Valid（级联校验） | 商品列表 |
| products[].spuId | Long | 是 | @NotNull | 商品 SPU 编号 |
| products[].skuId | Long | 是 | @NotNull | 商品 SKU 编号 |
| products[].discountType | Integer | 是 | @NotNull、@InEnum(PromotionDiscountTypeEnum) | 优惠类型：1 满减、2 折扣 |
| products[].discountPercent | Integer | 条件必填 | @AssertTrue：折扣类型时必须在 1~9999 | 折扣百分比 |
| products[].discountPrice | Integer | 条件必填 | @Min(0)、@AssertTrue：满减类型时不能为空 | 优惠金额（单位：分） |

**响应**: CommonResult&lt;Boolean&gt; —— 是否更新成功（固定 true）

**业务逻辑**:
1. 校验活动是否存在，不存在抛 DISCOUNT_ACTIVITY_NOT_EXISTS。
2. 若活动已关闭（状态为 DISABLE），不允许修改。
3. 校验商品是否与其它开启中的限时折扣活动冲突（排除当前活动自身）。
4. 校验商品 SKU 是否都存在。
5. 更新活动主表记录。
6. 对比新旧活动商品列表（按 skuId 匹配）：新增的商品批量插入，skuId 相同的批量更新（继承活动名称/状态/起止时间），被移除的批量删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_001_000 | 限时折扣活动不存在 |
| 1_013_001_002 | 限时折扣活动已关闭，不能修改 |
| 1_013_001_001 | 存在商品参加了其它限时折扣活动【{}】 |
| 1_008_006_000 | 商品 SKU 不存在 |

### 1.3 关闭限时折扣活动

- **路径**: PUT /promotion/discount-activity/close
- **权限**: promotion:discount-activity:close
- **说明**: 关闭指定活动，同步关闭其下所有活动商品。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否关闭成功（固定 true）

**业务逻辑**:
1. 校验活动是否存在。
2. 若活动已关闭，不允许重复关闭。
3. 更新活动状态为关闭（CommonStatusEnum.DISABLE）。
4. 按活动编号批量更新其下活动商品的活动状态为关闭。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_001_000 | 限时折扣活动不存在 |
| 1_013_001_004 | 限时折扣活动已关闭，不能重复关闭 |

### 1.4 删除限时折扣活动

- **路径**: DELETE /promotion/discount-activity/delete
- **权限**: promotion:discount-activity:delete
- **说明**: 删除已关闭的活动及其活动商品，未关闭的活动不允许删除。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 活动编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否删除成功（固定 true）

**业务逻辑**:
1. 校验活动是否存在。
2. 若活动未关闭（状态为开启），不允许删除。
3. 删除活动主表记录。
4. 按活动编号删除其下所有活动商品记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_001_000 | 限时折扣活动不存在 |
| 1_013_001_003 | 限时折扣活动未关闭，不能删除 |

---

## 2. 活动查询

### 2.1 获得限时折扣活动

- **路径**: GET /promotion/discount-activity/get
- **权限**: promotion:discount-activity:query
- **说明**: 按编号获得限时折扣活动详情，并拼接其商品列表；活动不存在时返回 null。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 活动编号 |

**响应**: CommonResult&lt;DiscountActivityRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 活动编号 |
| name | String | 活动标题 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| remark | String | 备注 |
| status | Integer | 活动状态（0 开启、1 关闭） |
| createTime | LocalDateTime | 创建时间 |
| products | List&lt;Product&gt; | 限时折扣商品列表，元素含 spuId、skuId、discountType、discountPercent、discountPrice |

**业务逻辑**:
1. 按编号查询活动，不存在时直接返回 null（不报错）。
2. 按活动编号查询其下活动商品列表。
3. 通过 DiscountActivityConvert 将活动与商品列表拼接为 RespVO 返回。

### 2.2 获得限时折扣活动分页

- **路径**: GET /promotion/discount-activity/page
- **权限**: promotion:discount-activity:query
- **说明**: 分页查询限时折扣活动，并批量拼接每条活动的商品列表。

**请求参数 (DiscountActivityPageReqVO)**（继承 PageParam）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10，-1 表示不分页 |
| name | String | 否 | - | 活动标题，模糊匹配 |
| status | Integer | 否 | - | 活动状态 |
| createTime | LocalDateTime[] | 否 | - | 创建时间区间（格式 yyyy-MM-dd HH:mm:ss） |

**响应**: CommonResult&lt;PageResult&lt;DiscountActivityRespVO&gt;&gt;，列表元素字段同 2.1 的 RespVO。

**业务逻辑**:
1. 按条件分页查询活动列表。
2. 结果为空时直接返回空分页（仅含总数）。
3. 收集本页活动编号，批量查询其下活动商品。
4. 通过 DiscountActivityConvert 将活动分页与商品列表拼接为分页 RespVO 返回。
