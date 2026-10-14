# 文章与文章分类接口 (ArticleController、ArticleCategoryController)

> 商城促销模块的文章管理域，提供营销文章（关联商品 SP）及其分类的增删改查，供小程序端文章展示、热门推荐与轮播图配置使用。

## 接口路径前缀

- /promotion/article  (Controller: ArticleController)
- /promotion/article-category  (Controller: ArticleCategoryController)

## 1. 文章管理（ArticleController）

### 1.1 创建文章

- **路径**: POST /promotion/article/create
- **权限**: promotion:article:create
- **说明**: 创建一篇营销文章，需归属某个文章分类并关联商品 SP。

**请求参数 (ArticleCreateReqVO，继承 ArticleBaseVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| categoryId | Long | 是 | @NotNull | 文章分类编号 |
| spuId | Long | 是 | @NotNull | 关联商品编号（ProductSpuDO 的 id） |
| title | String | 是 | @NotNull | 文章标题 |
| author | String | 否 | - | 文章作者 |
| picUrl | String | 是 | @NotNull | 文章封面图片地址 |
| introduction | String | 否 | - | 文章简介 |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum：0 开启 / 1 禁用） |
| recommendHot | Boolean | 是 | @NotNull | 是否热门（小程序） |
| recommendBanner | Boolean | 是 | @NotNull | 是否轮播图（小程序） |
| content | String | 是 | @NotNull | 文章内容 |

**响应**: CommonResult&lt;Long&gt; —— 文章编号

**业务逻辑**:
1. 校验请求中的文章分类（categoryId）是否存在，不存在时抛出「文章分类不存在」错误。
2. 将请求 VO 转换为 ArticleDO，并设置初始浏览量 browseCount = 0。
3. 插入数据库，返回新文章的编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_015_000 | 文章分类不存在 |

### 1.2 更新文章

- **路径**: PUT /promotion/article/update
- **权限**: promotion:article:update
- **说明**: 按编号更新文章内容，包括所属分类、关联商品与推荐属性。

**请求参数 (ArticleUpdateReqVO，继承 ArticleBaseVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文章编号 |
| categoryId | Long | 是 | @NotNull | 文章分类编号 |
| spuId | Long | 是 | @NotNull | 关联商品编号 |
| title | String | 是 | @NotNull | 文章标题 |
| author | String | 否 | - | 文章作者 |
| picUrl | String | 是 | @NotNull | 文章封面图片地址 |
| introduction | String | 否 | - | 文章简介 |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum） |
| recommendHot | Boolean | 是 | @NotNull | 是否热门（小程序） |
| recommendBanner | Boolean | 是 | @NotNull | 是否轮播图（小程序） |
| content | String | 是 | @NotNull | 文章内容 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验文章（id）是否存在，不存在时抛出「文章不存在」错误。
2. 校验新的文章分类（categoryId）是否存在，不存在时抛出「文章分类不存在」错误。
3. 转换为 ArticleDO 后按编号更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_016_000 | 文章不存在 |
| 1_013_015_000 | 文章分类不存在 |

### 1.3 删除文章

- **路径**: DELETE /promotion/article/delete
- **权限**: promotion:article:delete
- **说明**: 按编号删除文章记录。

**请求参数**: 无（Query 参数 id：文章编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验文章（id）是否存在，不存在时抛出「文章不存在」错误。
2. 按编号删除该文章记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_016_000 | 文章不存在 |

### 1.4 获得文章详情

- **路径**: GET /promotion/article/get
- **权限**: promotion:article:query
- **说明**: 按编号查询单篇文章的完整信息。

**请求参数**: 无（Query 参数 id：文章编号，必填）

**响应**: CommonResult&lt;ArticleRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文章编号 |
| categoryId | Long | 文章分类编号 |
| spuId | Long | 关联商品编号 |
| title | String | 文章标题 |
| author | String | 文章作者 |
| picUrl | String | 文章封面图片地址 |
| introduction | String | 文章简介 |
| sort | Integer | 排序 |
| status | Integer | 状态（CommonStatusEnum） |
| recommendHot | Boolean | 是否热门（小程序） |
| recommendBanner | Boolean | 是否轮播图（小程序） |
| content | String | 文章内容 |
| browseCount | Integer | 浏览量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询文章记录（selectById）。
2. 通过 ArticleConvert 转换为 ArticleRespVO 返回。

### 1.5 获得文章分页

- **路径**: GET /promotion/article/page
- **权限**: promotion:article:query
- **说明**: 多条件分页查询文章列表，供管理后台文章列表页使用。

**请求参数 (ArticlePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| categoryId | Long | 否 | - | 文章分类编号 |
| spuId | Long | 否 | - | 关联商品编号 |
| title | String | 否 | - | 文章标题 |
| author | String | 否 | - | 文章作者 |
| status | Integer | 否 | - | 状态 |
| recommendHot | Boolean | 否 | - | 是否热门（小程序） |
| recommendBanner | Boolean | 否 | - | 是否轮播图（小程序） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围（起止） |

**响应**: CommonResult&lt;PageResult&lt;ArticleRespVO&gt;&gt;，PageResult.list 元素字段同 [1.4 获得文章详情](#14-获得文章详情) 的 ArticleRespVO。

**业务逻辑**:
1. 按分类编号、商品编号、标题、作者、状态、热门、轮播图、创建时间范围等条件构建分页查询。
2. 执行分页查询返回 PageResult&lt;ArticleDO&gt;。
3. 通过 ArticleConvert 批量转换为 ArticleRespVO 分页结果。

## 2. 文章分类（ArticleCategoryController）

### 2.1 创建文章分类

- **路径**: POST /promotion/article-category/create
- **权限**: promotion:article-category:create
- **说明**: 创建文章分类（如「秒杀」「新人专享」等营销栏目）。

**请求参数 (ArticleCategoryCreateReqVO，继承 ArticleCategoryBaseVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 文章分类名称 |
| picUrl | String | 否 | - | 图标地址 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum：0 开启 / 1 禁用） |
| sort | Integer | 是 | @NotNull | 排序 |

**响应**: CommonResult&lt;Long&gt; —— 文章分类编号

**业务逻辑**:
1. 将请求 VO 转换为 ArticleCategoryDO。
2. 插入数据库，返回新分类的编号。

### 2.2 更新文章分类

- **路径**: PUT /promotion/article-category/update
- **权限**: promotion:article-category:update
- **说明**: 按编号更新文章分类的名称、图标、状态与排序。

**请求参数 (ArticleCategoryUpdateReqVO，继承 ArticleCategoryBaseVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文章分类编号 |
| name | String | 是 | @NotNull | 文章分类名称 |
| picUrl | String | 否 | - | 图标地址 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum） |
| sort | Integer | 是 | @NotNull | 排序 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验文章分类（id）是否存在，不存在时抛出「文章分类不存在」错误。
2. 转换为 ArticleCategoryDO 后按编号更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_015_000 | 文章分类不存在 |

### 2.3 删除文章分类

- **路径**: DELETE /promotion/article-category/delete
- **权限**: promotion:article-category:delete
- **说明**: 按编号删除文章分类，存在关联文章时禁止删除。

**请求参数**: 无（Query 参数 id：文章分类编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验文章分类（id）是否存在，不存在时抛出「文章分类不存在」错误。
2. 统计该分类下关联的文章数量，若大于 0 则抛出「文章分类删除失败，存在关联文章」错误。
3. 校验通过后按编号删除该分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_015_000 | 文章分类不存在 |
| 1_013_015_001 | 文章分类删除失败，存在关联文章 |

### 2.4 获得文章分类详情

- **路径**: GET /promotion/article-category/get
- **权限**: promotion:article-category:query
- **说明**: 按编号查询单个文章分类的完整信息。

**请求参数**: 无（Query 参数 id：文章分类编号，必填）

**响应**: CommonResult&lt;ArticleCategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文章分类编号 |
| name | String | 文章分类名称 |
| picUrl | String | 图标地址 |
| status | Integer | 状态（CommonStatusEnum） |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询文章分类记录（selectById）。
2. 通过 ArticleCategoryConvert 转换为 ArticleCategoryRespVO 返回。

### 2.5 获取文章分类精简信息列表

- **路径**: GET /promotion/article-category/list-all-simple
- **权限**: 已认证（接口无 @PreAuthorize 权限标识，仅要求登录）
- **说明**: 只包含开启状态的文章分类，主要用于前端的下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ArticleCategorySimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文章分类编号 |
| name | String | 文章分类名称 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）的全部分类列表。
2. 按排序字段 sort 降序排序。
3. 批量转换为仅含 id、name 的精简 VO 列表返回。

### 2.6 获得文章分类分页

- **路径**: GET /promotion/article-category/page
- **权限**: promotion:article-category:query
- **说明**: 多条件分页查询文章分类列表。

**请求参数 (ArticleCategoryPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | - | 文章分类名称 |
| status | Integer | 否 | - | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围（起止） |

**响应**: CommonResult&lt;PageResult&lt;ArticleCategoryRespVO&gt;&gt;，PageResult.list 元素字段同 [2.4 获得文章分类详情](#24-获得文章分类详情) 的 ArticleCategoryRespVO。

**业务逻辑**:
1. 按分类名称、状态、创建时间范围等条件构建分页查询。
2. 执行分页查询返回 PageResult&lt;ArticleCategoryDO&gt;。
3. 通过 ArticleCategoryConvert 批量转换为 ArticleCategoryRespVO 分页结果。
