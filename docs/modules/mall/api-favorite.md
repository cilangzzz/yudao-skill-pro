# 商品收藏接口 (ProductFavoriteController)

> 记录会员用户对商品 SPU 的收藏关系（表 `product_favorite`），管理后台提供收藏记录的分页查询；收藏的创建、取消等操作由 App 端提供。

## 接口路径前缀
/product/favorite  (Controller: ProductFavoriteController)

## 1. 商品收藏管理

### 1.1 获得商品收藏分页
- **路径**: GET /product/favorite/page
- **权限**: product:favorite:query
- **说明**: 分页查询商品收藏记录，并拼接每条收藏对应的商品 SPU 信息

**请求参数 (ProductFavoritePageReqVO)**: 继承 PageParam

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1（继承 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10；传 -1 时不分页（继承 PageParam） |
| userId | Long | 否 | - | 用户编号，按收藏用户筛选 |

**响应**: CommonResult&lt;PageResult&lt;ProductFavoriteRespVO&gt;&gt;

ProductFavoriteRespVO 继承 ProductSpuRespVO，即每条记录为「收藏人 userId + 完整商品 SPU 信息」：

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 收藏用户编号（关联 MemberUserDO 的 id） |
| spuId | Long | 商品 SPU 编号（等于继承自 ProductSpuRespVO 的 id） |
| id | Long | 商品 SPU 编号（继承 ProductSpuRespVO） |
| name | String | 商品名称（继承） |
| keyword | String | 关键字（继承） |
| introduction | String | 商品简介（继承） |
| description | String | 商品详情（继承） |
| categoryId | Long | 商品分类编号（继承） |
| brandId | Long | 商品品牌编号（继承） |
| picUrl | String | 商品封面图（继承） |
| sliderPicUrls | List&lt;String&gt; | 商品轮播图（继承） |
| sort | Integer | 排序字段（继承） |
| status | Integer | 商品状态（继承，字典 PRODUCT_SPU_STATUS） |
| createTime | LocalDateTime | 商品创建时间（继承） |
| specType | Boolean | 规格类型：true 多规格 / false 单规格（继承） |
| price | Integer | 商品价格，单位分（继承） |
| marketPrice | Integer | 市场价，单位分（继承） |
| costPrice | Integer | 成本价，单位分（继承） |
| stock | Integer | 商品库存（继承） |
| skus | List&lt;ProductSkuRespVO&gt; | SKU 数组（继承） |
| deliveryTypes | List&lt;Integer&gt; | 配送方式数组（继承） |
| deliveryTemplateId | Long | 物流配置模板编号（继承） |
| giveIntegral | Integer | 赠送积分（继承） |
| subCommissionType | Boolean | 分销类型（继承） |
| salesCount | Integer | 商品销量（继承） |
| virtualSalesCount | Integer | 虚拟销量（继承） |
| browseCount | Integer | 浏览量（继承） |

**业务逻辑**:
1. 调用 `ProductFavoriteService.getFavoritePage(ProductFavoritePageReqVO)`，按 `userId` 条件（有值才匹配，`eqIfPresent`）查询 `product_favorite` 表，按 id 倒序分页。
2. 若分页结果为空列表，直接返回空的 PageResult，不再查商品。
3. 收集分页结果中的 `spuId` 集合，调用 `ProductSpuService.getSpuList` 批量查询对应的商品 SPU 信息。
4. 通过 `ProductFavoriteConvert.convertPage` 将收藏记录（userId）与 SPU 信息拼接为 ProductFavoriteRespVO 分页结果返回。

**错误码**: 该域错误码（前缀 1-008-008）定义于 product 模块 ErrorCodeConstants，由 App 端收藏 / 取消收藏操作触发：

| 错误码 | 说明 |
|-------|------|
| 1_008_008_000 | 该商品已经被收藏 |
| 1_008_008_001 | 商品收藏不存在 |

## 附：App 端收藏接口（AppFavoriteController，非 admin 端）

AppFavoriteController 与 admin 控制器共用 `/product/favorite` 前缀，全部仅要求已认证（登录用户，无 @PreAuthorize 权限标识）：

| 操作 | 路径 | 说明 |
|------|------|------|
| 添加商品收藏 | POST /product/favorite/create | 请求 AppFavoriteReqVO（spuId 必填）；已收藏则抛 1_008_008_000，成功返回收藏记录编号 |
| 取消单个商品收藏 | DELETE /product/favorite/delete | 请求 AppFavoriteReqVO（spuId 必填）；不存在则抛 1_008_008_001，按 userId + spuId 删除 |
| 获得商品收藏分页 | GET /product/favorite/page | 按 AppFavoritePageReqVO（分页参数）查询当前用户收藏，拼接 SPU 信息返回 AppFavoriteRespVO |
| 检查是否收藏过商品 | GET /product/favorite/exits | 按 userId + spuId 查询，返回 Boolean |
| 获得商品收藏数量 | GET /product/favorite/get-count | 统计当前用户收藏总数，返回 Long |
