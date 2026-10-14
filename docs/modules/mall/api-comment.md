# 商品评价接口 (ProductCommentController)

> 管理后台商品评价中心：分页查询商品评价、查看评价详情、控制评价是否可见（显示/隐藏）、商家回复评价，以及管理员代客添加自评。

## 接口路径前缀

/product/comment  (Controller: ProductCommentController)

## 1. 查询类接口

### 1.1 获得商品评价分页

- **路径**: GET /product/comment/page
- **权限**: product:comment:query
- **说明**: 按评价人、订单、商品、星级、回复状态、创建时间等条件分页查询商品评价列表。

**请求参数 (ProductCommentPageReqVO)**（继承 PageParam 分页参数 pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码（来自 PageParam） |
| pageSize | Integer | 否 | 分页参数 | 每页条数（来自 PageParam） |
| userNickname | String | 否 | 无 | 评价人名称 |
| orderId | Long | 否 | 无 | 交易订单编号 |
| spuId | Long | 否 | 无 | 商品 SPU 编号 |
| spuName | String | 否 | 无 | 商品 SPU 名称 |
| scores | Integer | 否 | @InEnum(ProductCommentScoresEnum.class) | 评分星级 1-5 分 |
| replyStatus | Boolean | 否 | 无 | 商家是否回复 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult<PageResult<ProductCommentRespVO>>，分页项字段见 [1.2 获得商品评价](#12-获得商品评价) 的响应表。

**业务逻辑**:
1. 接收分页与筛选条件（评价人名称、订单编号、SPU 编号/名称、星级、回复状态、创建时间区间）。
2. 调用 `ProductCommentMapper.selectPage(pageReqVO)` 按条件构造查询并分页查询评价记录。
3. 将 `ProductCommentDO` 分页结果通过 BeanUtils 批量转换为 `ProductCommentRespVO` 返回。

### 1.2 获得商品评价

- **路径**: GET /product/comment/get
- **权限**: product:comment:query
- **说明**: 根据评价编号查询单条商品评价详情。

**请求参数**: 查询参数 `id`（Long，必填，评价编号）

**响应**: CommonResult<ProductCommentRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 评价编号 |
| userId | Long | 评价人编号 |
| userNickname | String | 评价人名称 |
| userAvatar | String | 评价人头像 |
| anonymous | Boolean | 是否匿名 |
| orderId | Long | 交易订单编号 |
| orderItemId | Long | 评价订单项编号 |
| spuId | Long | 商品 SPU 编号 |
| skuId | Long | 商品 SKU 编号 |
| spuName | String | 商品 SPU 名称 |
| skuPicUrl | String | 商品 SKU 图片地址 |
| skuProperties | List<ProductSkuSaveReqVO.Property> | 商品 SKU 规格值数组 |
| visible | Boolean | 是否可见 |
| scores | Integer | 评分星级 1-5 分 |
| descriptionScores | Integer | 描述星级 1-5 分 |
| benefitScores | Integer | 服务星级 1-5 分 |
| content | String | 评论内容 |
| picUrls | List<String> | 评论图片地址数组，最多 9 张 |
| replyStatus | Boolean | 商家是否回复 |
| replyUserId | Long | 回复管理员编号 |
| replyContent | String | 商家回复内容 |
| replyTime | LocalDateTime | 商家回复时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 `productCommentMapper.selectById(id)` 查询评价记录。
2. 若评价不存在，抛出 `COMMENT_NOT_EXISTS`（商品评价不存在）异常。
3. 将 `ProductCommentDO` 转换为 `ProductCommentRespVO` 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_007_000 | 商品评价不存在 |

## 2. 管理操作类接口

### 2.1 显示 / 隐藏评论

- **路径**: PUT /product/comment/update-visible
- **权限**: product:comment:update
- **说明**: 修改指定评价的可见状态，用于审核场景下隐藏不当评论或恢复显示。

**请求参数 (ProductCommentUpdateVisibleReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 评价编号 |
| visible | Boolean | 是 | @NotNull | 是否可见 |

**响应**: CommonResult<Boolean>（固定返回 true）

**业务逻辑**:
1. 根据 `id` 查询评价记录，校验评论是否存在，不存在则抛出 `COMMENT_NOT_EXISTS` 异常。
2. 构造仅含 `id` 与 `visible` 的 `ProductCommentDO`，调用 `updateById` 更新可见状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_007_000 | 商品评价不存在 |

### 2.2 商家回复

- **路径**: PUT /product/comment/reply
- **权限**: product:comment:update
- **说明**: 管理员（商家）对指定评价进行回复。

**请求参数 (ProductCommentReplyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 评价编号 |
| replyContent | String | 是 | @NotEmpty | 商家回复内容 |

**响应**: CommonResult<Boolean>（固定返回 true）

**业务逻辑**:
1. 根据 `id` 查询评价记录，校验评论是否存在，不存在则抛出 `COMMENT_NOT_EXISTS` 异常。
2. 取当前登录管理员编号（`SecurityFrameworkUtils.getLoginUserId()`）作为回复人。
3. 更新评价记录：写入回复内容 `replyContent`、回复时间 `replyTime`（当前时间）、回复管理员编号 `replyUserId`，并将 `replyStatus` 置为 true。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_007_000 | 商品评价不存在 |

### 2.3 添加自评

- **路径**: POST /product/comment/create
- **权限**: product:comment:update
- **说明**: 管理员手动为商品添加评价（自评）。

**请求参数 (ProductCommentCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| userId | Long | 否 | 无 | 评价人编号 |
| orderItemId | Long | 否 | 无 | 评价订单项编号 |
| userNickname | String | 是 | @NotNull | 评价人名称 |
| userAvatar | String | 是 | @NotNull | 评价人头像 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号 |
| descriptionScores | Integer | 是 | @NotNull | 描述星级 1-5 分 |
| benefitScores | Integer | 是 | @NotNull | 服务星级 1-5 分 |
| content | String | 是 | @NotNull | 评论内容 |
| picUrls | List<String> | 否 | @Size(max = 9) | 评论图片地址数组，最多 9 张 |

**响应**: CommonResult<Boolean>（固定返回 true）

**业务逻辑**:
1. 根据 `skuId` 校验商品 SKU 是否存在（`ProductSkuService.getSku(skuId, true)`），不存在则抛出 `SKU_NOT_EXISTS` 异常。
2. 根据 SKU 的 `spuId` 校验商品 SPU 是否存在（`ProductSpuService.getSpu(spuId, true)`），不存在则抛出 `SPU_NOT_EXISTS` 异常。
3. 通过 `ProductCommentConvert.convert(createReqVO, spu, sku)` 将请求 VO 与 SPU/SKU 信息（如 SPU 名称、SKU 图片、规格值）组装为 `ProductCommentDO`。
4. 调用 `productCommentMapper.insert(comment)` 插入评价记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_006_000 | 商品 SKU 不存在 |

## 附：本域相关错误码汇总（来源 ErrorCodeConstants，前缀 1_008_007）

| 错误码 | 说明 |
|-------|------|
| 1_008_007_000 | 商品评价不存在 |
| 1_008_007_001 | 订单的商品评价已存在（仅 API 内部调用创建评价时校验，admin 端点不直接触发） |
