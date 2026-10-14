# 优惠劵接口 (CouponTemplateController / CouponController)

> 提供优惠劵模板的创建、修改、状态管理与查询，以及面向会员的优惠劵发放、回收（删除）与明细查询能力。用户领取优惠劵时依据模板生成 `CouponDO` 优惠劵记录。

## 接口路径前缀

- `/promotion/coupon-template` (Controller: CouponTemplateController) —— 优惠劵模板管理
- `/promotion/coupon` (Controller: CouponController) —— 会员优惠劵管理

## 1. 优惠劵模板（CouponTemplateController）

### 1.1 创建优惠劵模板

- **路径**: POST /promotion/coupon-template/create
- **权限**: promotion:coupon-template:create
- **说明**: 创建一张优惠劵模板，创建后初始状态为开启（ENABLE）。

**请求参数 (CouponTemplateCreateReqVO)**: 继承 CouponTemplateBaseVO，字段如下

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 优惠劵名 |
| description | String | 否 | - | 优惠券说明 |
| totalCount | Integer | 是 | @NotNull | 发行总量，-1 表示不限制发放数量 |
| takeLimitCount | Integer | 是 | @NotNull | 每人限领个数，-1 表示不限制 |
| takeType | Integer | 是 | @NotNull | 领取方式：1 直接领取、2 指定发放、3 新人券（CouponTakeTypeEnum） |
| usePrice | Integer | 是 | @NotNull | 满多少金额可用，单位：分；0 表示不限制 |
| productScope | Integer | 是 | @NotNull、@InEnum(PromotionProductScopeEnum) | 商品范围：1 全部商品、2 指定商品、3 指定品类 |
| productScopeValues | List&lt;Long&gt; | 条件 | @AssertTrue | 商品范围编号数组；productScope 为 2/3 时不能为空 |
| validityType | Integer | 是 | @NotNull、@InEnum(CouponTemplateValidityTypeEnum) | 生效日期类型：1 固定日期、2 领取之后 |
| validStartTime | LocalDateTime | 条件 | @AssertTrue | 固定日期 - 生效开始时间；validityType=1 时必填 |
| validEndTime | LocalDateTime | 条件 | @AssertTrue | 固定日期 - 生效结束时间；validityType=1 时必填 |
| fixedStartTerm | Integer | 条件 | @Min(0)、@AssertTrue | 领取日期 - 开始天数；validityType=2 时必填 |
| fixedEndTerm | Integer | 条件 | @Min(1)、@AssertTrue | 领取日期 - 结束天数；validityType=2 时必填 |
| discountType | Integer | 是 | @NotNull、@InEnum(PromotionDiscountTypeEnum) | 优惠类型：1 满减、2 折扣 |
| discountPercent | Integer | 条件 | @AssertTrue | 折扣百分比；discountType=2 时必须介于 1~99 |
| discountPrice | Integer | 条件 | @Min(0)、@AssertTrue | 优惠金额，单位：分；discountType=1 时必填 |
| discountLimitPrice | Integer | 条件 | @AssertTrue | 折扣上限，单位：分；仅 discountType=2 时生效且必填 |

**响应**: CommonResult&lt;Long&gt; —— 模板编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的优惠劵模板编号 |

**业务逻辑**:
1. 校验发放数量不能小于每人限领数量（仅在领取方式为"用户直接领取"且两者均非 -1 不限制时，不满足抛 COUPON_TEMPLATE_NOT_ENOUGH）。
2. 校验商品范围：productScope 为指定商品时调用 ProductSpuApi 校验 SPU 列表存在；为指定品类时调用 ProductCategoryApi 校验分类列表存在。
3. 将请求 VO 转换为 CouponTemplateDO，并设置状态为开启（CommonStatusEnum.ENABLE）。
4. 插入数据库，返回新模板编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_004_002 | 当前剩余数量不够领取 |

### 1.2 更新优惠劵模板

- **路径**: PUT /promotion/coupon-template/update
- **权限**: promotion:coupon-template:update
- **说明**: 更新已存在的优惠劵模板基础信息与规则。

**请求参数 (CouponTemplateUpdateReqVO)**: 在 1.1 全部字段基础上增加

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否更新成功 |

**业务逻辑**:
1. 校验优惠劵模板存在（不存在抛 COUPON_TEMPLATE_NOT_EXISTS）。
2. 校验发放数量不能小于每人限领数量（用户领取且均非不限制时）。
3. 校验发放数量不能过小：用户领取且总量非不限制时，新 totalCount 不得小于模板已领取数量 takeCount，否则抛 COUPON_TEMPLATE_TOTAL_COUNT_TOO_SMALL。
4. 校验商品范围（同创建逻辑）。
5. 按编号更新模板记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_004_000 | 优惠劵模板不存在 |
| 1_013_004_001 | 发放数量不能小于已领取数量({}) |
| 1_013_004_002 | 当前剩余数量不够领取 |

### 1.3 更新优惠劵模板状态

- **路径**: PUT /promotion/coupon-template/update-status
- **权限**: promotion:coupon-template:update
- **说明**: 开启或关闭优惠劵模板（如暂停发行）。

**请求参数 (CouponTemplateUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 优惠劵模板编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态：0 开启、1 关闭 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否更新成功 |

**业务逻辑**:
1. 校验优惠劵模板存在。
2. 按编号仅更新 status 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_004_000 | 优惠劵模板不存在 |

### 1.4 删除优惠劵模板

- **路径**: DELETE /promotion/coupon-template/delete
- **权限**: promotion:coupon-template:delete
- **说明**: 按编号删除优惠劵模板（逻辑删除）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否删除成功 |

**业务逻辑**:
1. 校验优惠劵模板存在。
2. 按编号删除（MyBatis-Plus 逻辑删除）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_004_000 | 优惠劵模板不存在 |

### 1.5 获得优惠劵模板

- **路径**: GET /promotion/coupon-template/get
- **权限**: promotion:coupon-template:query
- **说明**: 按编号查询单个优惠劵模板详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 模板编号 |

**响应**: CommonResult&lt;CouponTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模板编号 |
| status | Integer | 状态：0 开启、1 关闭 |
| takeCount | Integer | 已领取优惠券的数量 |
| useCount | Integer | 使用优惠券的次数 |
| createTime | LocalDateTime | 创建时间 |
| （其余字段） | - | 同 1.1 请求参数中的模板基础字段（name/description/totalCount/takeLimitCount/takeType/usePrice/productScope/productScopeValues/validityType/validStartTime/validEndTime/fixedStartTerm/fixedEndTerm/discountType/discountPercent/discountPrice/discountLimitPrice） |

**业务逻辑**:
1. 按编号查询模板 DO（不存在时返回 null，前端据空数据处理）。
2. 通过 CouponTemplateConvert 转换为 RespVO 返回。

### 1.6 获得优惠劵模板分页

- **路径**: GET /promotion/coupon-template/page
- **权限**: promotion:coupon-template:query
- **说明**: 分页查询优惠劵模板列表，支持多条件筛选。

**请求参数 (CouponTemplatePageReqVO)**: 继承 PageParam（pageNo 页码、pageSize 每页条数），筛选字段均可选

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 优惠劵名，模糊匹配 |
| status | Integer | 否 | - | 状态：0 开启、1 关闭 |
| discountType | Integer | 否 | - | 优惠类型：1 满减、2 折扣 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间范围 |
| canTakeTypes | List&lt;Integer&gt; | 否 | @InEnum(CouponTakeTypeEnum) | 可以领取的类型集合 |
| productScope | Integer | 否 | @InEnum(PromotionProductScopeEnum) | 商品范围 |
| productScopeValue | Long | 否 | - | 商品范围编号 |

**响应**: CommonResult&lt;PageResult&lt;CouponTemplateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | CouponTemplateRespVO[] | 模板列表，单条字段同 1.5 |
| total | Long | 总条数 |

**业务逻辑**:
1. 按筛选条件执行分页查询（Mapper selectPage，name 模糊、createTime 区间等拼接）。
2. 通过 CouponTemplateConvert.convertPage 转换为分页 RespVO。

### 1.7 获得优惠劵模板列表

- **路径**: GET /promotion/coupon-template/list
- **权限**: promotion:coupon-template:query
- **说明**: 按编号集合批量查询优惠劵模板（不含分页）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Collection&lt;Long&gt; | 是 | - | 模板编号列表，逗号分隔，如 `1024,2048` |

**响应**: CommonResult&lt;List&lt;CouponTemplateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | CouponTemplateRespVO[] | 模板列表，单条字段同 1.5 |

**业务逻辑**:
1. 按编号集合批量查询模板 DO 列表。
2. 转换为 RespVO 列表返回。

## 2. 优惠劵（CouponController）

### 2.1 回收优惠劵

- **路径**: DELETE /promotion/coupon/delete
- **权限**: promotion:coupon:delete
- **说明**: 管理员回收（删除）会员持有的未使用/已过期优惠劵，已使用的不可回收。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 优惠劵编号 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否回收成功 |

**业务逻辑**:
1. 校验优惠劵存在（不存在抛 COUPON_NOT_EXISTS）。
2. 删除该优惠劵，仅允许状态为"未使用"或"已过期"的记录被删除；更新行数为 0（即已被使用）时抛 COUPON_DELETE_FAIL_USED。
3. 事务内将对应优惠劵模板的领取数量 takeCount 减 1（调用 updateCouponTemplateTakeCount(id, -1)，剩余不足会抛 COUPON_TEMPLATE_NOT_ENOUGH）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_005_000 | 优惠券不存在 |
| 1_013_005_001 | 回收优惠劵失败，优惠劵已被使用 |
| 1_013_004_002 | 当前剩余数量不够领取 |

### 2.2 获得优惠劵分页

- **路径**: GET /promotion/coupon/page
- **权限**: promotion:coupon:query
- **说明**: 分页查询会员优惠劵列表，支持按模板、状态、时间、昵称、用户筛选，并拼接用户昵称。

**请求参数 (CouponPageReqVO)**: 继承 PageParam（pageNo、pageSize），筛选字段均可选

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| templateId | Long | 否 | - | 优惠劵模板编号 |
| status | Integer | 否 | @InEnum(CouponStatusEnum) | 优惠劵状态：1 未使用、2 已使用、3 已过期 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间范围 |
| nickname | String | 否 | - | 用户昵称（按昵称反查用户后筛选） |
| userIds | Collection&lt;Long&gt; | 否 | - | 用户编号列表 |

**响应**: CommonResult&lt;PageResult&lt;CouponPageItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 优惠劵编号 |
| createTime | LocalDateTime | 领取（创建）时间 |
| nickname | String | 用户昵称（由会员模块拼接） |
| （其余字段） | - | 继承 CouponBaseVO：templateId/name/status/userId/takeType/usePrice/validStartTime/validEndTime/productScope/productScopeValues/discountType/discountPercent/discountPrice/discountLimitPrice/useOrderId/useTime |
| total | Long | 总条数 |

**业务逻辑**:
1. 若传入昵称 nickname，调用 MemberUserApi.getUserListByNickname 反查会员；查不到用户直接返回空分页，否则将用户编号集合写入查询条件 userIds。
2. 按条件分页查询优惠劵（Mapper selectPage）。
3. 通过 CouponConvert.convertPage 转换为 CouponPageItemRespVO 分页结果。
4. 批量查询分页记录涉及的会员用户 Map，将用户昵称 nickname 填充到每条记录后返回。

### 2.3 获得优惠劵

- **路径**: GET /promotion/coupon/get
- **权限**: promotion:coupon:query
- **说明**: 按编号查询单张优惠劵详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 优惠劵编号 |

**响应**: CommonResult&lt;CouponRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 优惠劵编号 |
| createTime | LocalDateTime | 领取（创建）时间 |
| （其余字段） | - | 继承 CouponBaseVO：templateId/name/status/userId/takeType/usePrice/validStartTime/validEndTime/productScope/productScopeValues/discountType/discountPercent/discountPrice/discountLimitPrice/useOrderId/useTime |

**业务逻辑**:
1. 按编号查询优惠劵 DO。
2. 通过 BeanUtils.toBean 转换为 CouponRespVO 返回。

### 2.4 发送优惠劵

- **路径**: POST /promotion/coupon/send
- **权限**: promotion:coupon:send
- **说明**: 管理员按模板向指定会员批量发放优惠劵（领取方式为"指定发放"）。

**请求参数 (CouponSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| templateId | Long | 是 | @NotNull | 优惠劵模板编号 |
| userIds | Set&lt;Long&gt; | 是 | @NotEmpty | 用户编号列表 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否发送成功 |

**业务逻辑**:
1. 调用 takeCouponByAdmin → takeCoupon(templateId, userIds, ADMIN)：过滤掉已达到模板"每人限领个数"上限的用户（限领数 -1 表示不限制）。
2. 校验优惠劵可领取：所有用户均被过滤则抛 COUPON_TEMPLATE_USER_ALREADY_TAKE；模板不存在抛 COUPON_TEMPLATE_NOT_EXISTS；模板领取方式与 ADMIN 不匹配抛 COUPON_TEMPLATE_CANNOT_TAKE。
3. 校验剩余发放数量（用户领取类模板且总量非不限制时，已领数量不得超过总量，否则抛 COUPON_TEMPLATE_NOT_ENOUGH）；校验固定日期型模板是否已过有效期（过期抛 COUPON_TEMPLATE_EXPIRED）。
4. 为过滤后的每个用户批量生成并插入 CouponDO 优惠劵记录。
5. 调用 updateCouponTemplateTakeCount 将模板领取数量增加发放人数（底层更新失败时抛 COUPON_TEMPLATE_NOT_ENOUGH）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_004_000 | 优惠劵模板不存在 |
| 1_013_004_002 | 当前剩余数量不够领取 |
| 1_013_004_003 | 用户已领取过此优惠券 |
| 1_013_004_004 | 优惠券已过期 |
| 1_013_004_005 | 领取方式不正确 |

## 附：优惠劵相关错误码汇总（promotion 模块 1-013 段）

### 优惠劵模板（1-013-004-000）

| 错误码 | 说明 |
|-------|------|
| 1_013_004_000 | 优惠劵模板不存在 |
| 1_013_004_001 | 发放数量不能小于已领取数量({}) |
| 1_013_004_002 | 当前剩余数量不够领取 |
| 1_013_004_003 | 用户已领取过此优惠券 |
| 1_013_004_004 | 优惠券已过期 |
| 1_013_004_005 | 领取方式不正确 |

### 优惠劵（1-013-005-000）

| 错误码 | 说明 |
|-------|------|
| 1_013_005_000 | 优惠券不存在 |
| 1_013_005_001 | 回收优惠劵失败，优惠劵已被使用 |
| 1_013_005_002 | 优惠劵不处于待使用状态 |
| 1_013_005_003 | 优惠券不在使用时间范围内 |
| 1_013_005_004 | 优惠劵不是已使用状态 |
