# 产品管理接口 (CrmProductController / CrmProductCategoryController)

> CRM 产品与产品分类管理：产品的增删改查、分页、导出 Excel、精简下拉列表，以及产品分类（最多两级）的增删改查与列表。

## 接口路径前缀

- `/crm/product` (Controller: CrmProductController)
- `/crm/product-category` (Controller: CrmProductCategoryController)

## 1. 产品管理（/crm/product）

### 1.1 创建产品

- **路径**: POST /crm/product/create
- **权限**: crm:product:create
- **说明**: 创建产品，校验负责人、产品编码唯一性与分类存在性，并插入数据权限（负责人）。

**请求参数 (CrmProductSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 产品编号（创建时不传） |
| name | String | 是 | @NotNull | 产品名称 |
| no | String | 是 | @NotNull | 产品编码 |
| unit | int | 否 | - | 单位（字典 CRM_PRODUCT_UNIT） |
| price | BigDecimal | 是 | @NotNull | 价格，单位：分 |
| status | Integer | 是 | @NotNull | 状态（1 上架 / 0 下架） |
| categoryId | Long | 是 | @NotNull | 产品分类编号 |
| description | String | 否 | - | 产品描述 |
| ownerUserId | Long | 是 | @NotNull | 负责人的用户编号 |

**响应**: CommonResult&lt;Long&gt;（产品编号）

**业务逻辑**:
1. 校验负责人用户存在（adminUserApi.validateUserList）。
2. 校验产品编码不重复（PRODUCT_NO_EXISTS）。
3. 校验产品分类存在（PRODUCT_CATEGORY_NOT_EXISTS）。
4. 插入产品记录（CrmProductDO）。
5. 插入数据权限：负责人对产品拥有 OWNER 级权限（CrmPermissionService）。
6. 记录操作日志上下文（productId）并返回产品编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_008_000 | 产品不存在 |
| 1_020_008_001 | 产品编号已存在 |
| 1_020_009_000 | 产品分类不存在 |

### 1.2 更新产品

- **路径**: PUT /crm/product/update
- **权限**: crm:product:update
- **说明**: 更新产品（不支持修改负责人），需对产品拥有写权限。

**请求参数 (CrmProductSaveReqVO)**: 同 1.1（id 必传用于定位记录）

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 强制将 ownerUserId 置为 null，即不允许通过更新修改负责人。
2. 校验产品存在（PRODUCT_NOT_EXISTS）。
3. 校验产品编码不与其他产品重复（PRODUCT_NO_EXISTS）。
4. 校验产品分类存在（PRODUCT_CATEGORY_NOT_EXISTS）。
5. 更新产品记录，并记录新旧对象差异用于操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_008_000 | 产品不存在 |
| 1_020_008_001 | 产品编号已存在 |
| 1_020_009_000 | 产品分类不存在 |

### 1.3 删除产品

- **路径**: DELETE /crm/product/delete
- **权限**: crm:product:delete
- **说明**: 删除产品，需为产品负责人，且产品未被合同/商机引用。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 产品编号 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 校验产品存在（PRODUCT_NOT_EXISTS）。
2. 校验产品未被合同引用（PRODUCT_DELETE_FAIL_CONTRACT_EXISTS）。
3. 校验产品未被商机引用（PRODUCT_DELETE_FAIL_BUSINESS_EXISTS）。
4. 删除产品记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_008_000 | 产品不存在 |
| 1_020_008_003 | 产品已被合同引用，无法删除 |
| 1_020_008_004 | 产品已被商机引用，无法删除 |

### 1.4 获得产品详情

- **路径**: GET /crm/product/get
- **权限**: crm:product:query（Service 层还需对产品具备 READ 数据权限）
- **说明**: 按编号获得产品详情，响应经 @TransMethodResult 自动翻译分类名/负责人昵称等。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 产品编号 |

**响应**: CommonResult&lt;CrmProductRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| no | String | 产品编码 |
| unit | int | 单位（字典翻译） |
| price | BigDecimal | 价格，单位：分 |
| status | Integer | 状态（1 上架 / 0 下架） |
| categoryId | Long | 产品分类编号 |
| categoryName | String | 产品分类名字（Trans 翻译） |
| description | String | 产品描述 |
| ownerUserId | Long | 负责人的用户编号 |
| ownerUserName | String | 负责人的用户昵称（Trans 翻译） |
| creator | String | 创建人编号 |
| creatorName | String | 创建人名字（Trans 翻译） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 校验当前用户对产品具备 READ 数据权限（@CrmPermission）。
2. 按编号查询产品，转换为 CrmProductRespVO 返回。

### 1.5 获得产品精简列表

- **路径**: GET /crm/product/simple-list
- **权限**: 已认证（无 @PreAuthorize，仅登录即可）
- **说明**: 只包含上架状态的产品，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;CrmProductRespVO&gt;&gt;（仅填充部分字段）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| unit | int | 单位 |
| no | String | 产品编码 |
| price | BigDecimal | 价格，单位：分 |

**业务逻辑**:
1. 查询状态为 ENABLE（上架，status=1）的全部产品。
2. 转换为仅含 id/name/unit/no/price 的精简 VO 列表返回。

### 1.6 获得产品分页

- **路径**: GET /crm/product/page
- **权限**: crm:product:query
- **说明**: 分页获得产品列表，响应经 @TransMethodResult 自动翻译。

**请求参数 (CrmProductPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 产品名称（模糊查询） |
| status | Integer | 否 | - | 状态（1 上架 / 0 下架） |

**响应**: CommonResult&lt;PageResult&lt;CrmProductRespVO&gt;&gt;（列表项字段同 1.4）

**业务逻辑**:
1. 按名称/状态条件分页查询产品（CrmProductMapper.selectPage）。
2. 转换为 CrmProductRespVO 分页结果返回。

### 1.7 导出产品 Excel

- **路径**: GET /crm/product/export-excel
- **权限**: crm:product:export
- **说明**: 按分页条件导出产品 Excel（文件名"产品.xls"），记录导出操作日志。

**请求参数 (CrmProductPageReqVO)**: 同 1.6（导出时 pageSize 被置为 PAGE_SIZE_NONE，即不分页导出全部）

**响应**: Excel 文件流（产品.xls），列同 CrmProductRespVO 的 @ExcelProperty 注解（产品编号/产品名称/产品编码/单位/价格/产品分类/产品描述/负责人/创建人/创建时间/更新时间）

**业务逻辑**:
1. 将 pageSize 设置为 PAGE_SIZE_NONE 以查询全部数据。
2. 按条件分页查询产品，转换为 CrmProductRespVO 列表并执行字典翻译。
3. 通过 ExcelUtils 写出 Excel 文件流。

## 2. 产品分类管理（/crm/product-category）

### 2.1 创建产品分类

- **路径**: POST /crm/product-category/create
- **权限**: crm:product-category:create
- **说明**: 创建产品分类（最多两级），校验父分类与同级名称唯一性。

**请求参数 (CrmProductCategoryCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 分类编号（创建时不传） |
| name | String | 是 | @NotNull | 分类名称 |
| parentId | Long | 是 | @NotNull | 父级编号（根分类传 PARENT_ID_NULL） |

**响应**: CommonResult&lt;Long&gt;（分类编号）

**业务逻辑**:
1. 校验父分类存在；根分类直接放行；父分类若已是二级分类则报错（PRODUCT_CATEGORY_PARENT_NOT_FIRST_LEVEL），即分类最多两级。
2. 校验同一父分类下名称不重复（PRODUCT_CATEGORY_EXISTS）。
3. 插入分类记录并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_009_000 | 产品分类不存在 |
| 1_020_009_001 | 产品分类已存在 |
| 1_020_009_003 | 父分类不存在 |
| 1_020_009_004 | 父分类不能是二级分类 |

### 2.2 更新产品分类

- **路径**: PUT /crm/product-category/update
- **权限**: crm:product-category:update
- **说明**: 更新产品分类，复用 CrmProductCategoryCreateReqVO（含 id）。

**请求参数 (CrmProductCategoryCreateReqVO)**: 同 2.1（id 必传用于定位记录）

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 校验分类存在（PRODUCT_CATEGORY_NOT_EXISTS）。
2. 校验父分类存在且为一级分类（PRODUCT_CATEGORY_PARENT_NOT_EXISTS / PRODUCT_CATEGORY_PARENT_NOT_FIRST_LEVEL）。
3. 校验同一父分类下名称不重复（PRODUCT_CATEGORY_EXISTS）。
4. 更新分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_009_000 | 产品分类不存在 |
| 1_020_009_001 | 产品分类已存在 |
| 1_020_009_003 | 父分类不存在 |
| 1_020_009_004 | 父分类不能是二级分类 |

### 2.3 删除产品分类

- **路径**: DELETE /crm/product-category/delete
- **权限**: crm:product-category:delete
- **说明**: 删除产品分类，要求无子分类且未被产品使用。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 分类编号 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 校验分类存在（PRODUCT_CATEGORY_NOT_EXISTS）。
2. 校验是否存在子分类（PRODUCT_CATEGORY_EXISTS_CHILDREN）。
3. 校验是否被产品使用（PRODUCT_CATEGORY_USED）。
4. 删除分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_009_000 | 产品分类不存在 |
| 1_020_009_002 | 产品分类已关联产品 |
| 1_020_009_005 | 存在子分类，无法删除 |

### 2.4 获得产品分类详情

- **路径**: GET /crm/product-category/get
- **权限**: crm:product-category:query
- **说明**: 按编号获得产品分类详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 分类编号 |

**响应**: CommonResult&lt;CrmProductCategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| name | String | 分类名称 |
| parentId | Long | 父级编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询分类，转换为 CrmProductCategoryRespVO 返回（不存在时返回 null 数据）。

### 2.5 获得产品分类列表

- **路径**: GET /crm/product-category/list
- **权限**: crm:product-category:query
- **说明**: 按条件获得产品分类列表（不分页）。

**请求参数 (CrmProductCategoryListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 名称 |
| parentId | Long | 否 | - | 父级编号 |
| createTime | LocalDateTime | 否 | - | 创建时间 |

**响应**: CommonResult&lt;List&lt;CrmProductCategoryRespVO&gt;&gt;（字段同 2.4）

**业务逻辑**:
1. 按名称/父级编号/创建时间条件查询分类列表。
2. 转换为 CrmProductCategoryRespVO 列表返回。
