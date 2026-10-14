# 商品分类接口 (ProductCategoryController)

> 管理后台商品分类（product_category）的维护接口：提供分类的创建、更新、删除与查询。分类为两级树形结构（parentId=0 为根分类，只允许二级分类作为商品 SPU 的归属）。

## 接口路径前缀

/product/category  (Controller: ProductCategoryController)

## 1. 分类写操作

### 1.1 创建商品分类

- **路径**: POST /product/category/create
- **权限**: product:category:create
- **说明**: 新增一个商品分类，返回新分类编号。

**请求参数 (ProductCategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 分类编号（新增时忽略） |
| parentId | Long | 是 | @NotNull | 父分类编号，0 表示根分类 |
| name | String | 是 | @NotBlank | 分类名称 |
| picUrl | String | 是 | @NotBlank | 移动端分类图（建议 180*180 分辨率） |
| sort | Integer | 否 | - | 分类排序 |
| status | Integer | 是 | @NotNull | 开启状态（CommonStatusEnum 枚举） |
| description | String | 否 | - | 分类描述 |

**响应**: CommonResult&lt;Long&gt; —— 新增分类的编号。

**业务逻辑**:
1. 校验父分类：若 parentId 不为 0（非根分类），父分类必须已存在，否则抛「父分类不存在」。
2. 父分类存在时还要求其必须是一级分类（父分类的 parentId 必须为 0），否则抛「父分类不能是二级分类」——即最多建到第二级。
3. 将 ReqVO 转换为 ProductCategoryDO，插入 product_category 表。
4. 返回自增主键 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1-008-001-001 | 父分类不存在 |
| 1-008-001-002 | 父分类不能是二级分类 |

### 1.2 更新商品分类

- **路径**: PUT /product/category/update
- **权限**: product:category:update
- **说明**: 更新指定分类，请求体与新增共用 ProductCategorySaveReqVO（此时 id 必传）。

**请求参数 (ProductCategorySaveReqVO)**: 字段同 1.1，更新时 id 为必传。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验分类存在，不存在抛「商品分类不存在」。
2. 环检测：父分类不能设置为分类自身，否则抛「父分类不能设置为分类自身」。
3. 校验父分类：与新增一致，父分类必须存在且必须是一级分类。
4. 转换为 ProductCategoryDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1-008-001-000 | 商品分类不存在 |
| 1-008-001-001 | 父分类不存在 |
| 1-008-001-002 | 父分类不能是二级分类 |
| 1-008-001-006 | 父分类不能设置为分类自身 |

### 1.3 删除商品分类

- **路径**: DELETE /product/category/delete
- **权限**: product:category:delete
- **说明**: 删除指定分类，删除前校验无子分类且未绑定商品。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 分类编号（查询参数） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验分类存在，不存在抛「商品分类不存在」。
2. 校验是否存在子分类（按 parentId 统计），存在则抛「存在子分类，无法删除」。
3. 校验分类下是否绑定了 SPU（调用 ProductSpuService.getSpuCountByCategoryId，通过 @Lazy 解决循环依赖），存在则抛「类别下存在商品，无法删除」。
4. 按 id 删除分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1-008-001-000 | 商品分类不存在 |
| 1-008-001-003 | 存在子分类，无法删除 |
| 1-008-001-005 | 类别下存在商品，无法删除 |

## 2. 分类查询

### 2.1 获得商品分类

- **路径**: GET /product/category/get
- **权限**: product:category:query
- **说明**: 按编号获取单个分类详情。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 分类编号（查询参数） |

**响应**: CommonResult&lt;ProductCategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| parentId | Long | 父分类编号 |
| name | String | 分类名称 |
| picUrl | String | 移动端分类图 |
| sort | Integer | 分类排序 |
| status | Integer | 开启状态 |
| description | String | 分类描述 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 ProductCategoryDO（未命中时返回 null，响应 data 为空，不抛异常）。
2. 通过 BeanUtils 转换为 ProductCategoryRespVO 返回。

> 注意：ProductCategoryDO 实体并无 description 字段（仅存在于 VO 层），数据库实际不持久化该字段。

### 2.2 获得商品分类列表

- **路径**: GET /product/category/list
- **权限**: product:category:query
- **说明**: 按条件查询分类列表（非分页），前端一般用于构建分类树。

**请求参数 (ProductCategoryListReqVO)**（查询参数，均可选）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 分类名称（模糊匹配） |
| status | Integer | 否 | - | 开启状态 |
| parentId | Long | 否 | - | 父分类编号 |
| parentIds | Collection&lt;Long&gt; | 否 | - | 父分类编号数组 |

**响应**: CommonResult&lt;List&lt;ProductCategoryRespVO&gt;&gt; —— 字段同 2.1 的 ProductCategoryRespVO。

**业务逻辑**:
1. 按 name、status、parentId、parentIds 条件构造查询，执行 selectList。
2. 结果按 sort 字段升序排序（Controller 内 Comparator.comparing）。
3. 批量转换为 ProductCategoryRespVO 列表返回。

## 附：分类域错误码汇总（1-008-001-000 段）

| 错误码 | 常量 | 说明 |
|-------|------|------|
| 1-008-001-000 | CATEGORY_NOT_EXISTS | 商品分类不存在 |
| 1-008-001-001 | CATEGORY_PARENT_NOT_EXISTS | 父分类不存在 |
| 1-008-001-002 | CATEGORY_PARENT_NOT_FIRST_LEVEL | 父分类不能是二级分类 |
| 1-008-001-003 | CATEGORY_EXISTS_CHILDREN | 存在子分类，无法删除 |
| 1-008-001-004 | CATEGORY_DISABLED | 商品分类({})已禁用，无法使用 |
| 1-008-001-005 | CATEGORY_HAVE_BIND_SPU | 类别下存在商品，无法删除 |
| 1-008-001-006 | CATEGORY_PARENT_IS_SELF | 父分类不能设置为分类自身 |

> 1-008-001-004（CATEGORY_DISABLED）与 1-008-005-001（SPU_SAVE_FAIL_CATEGORY_LEVEL_ERROR，必须使用第二级及以下的商品分类）由 Service 的 validateCategory / validateCategoryList 方法抛出，供 SPU 保存等其它业务域内部校验调用，不直接对应本 Controller 的端点。
