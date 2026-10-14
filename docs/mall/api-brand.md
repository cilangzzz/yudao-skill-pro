# 商品品牌接口 (ProductBrandController)

> 提供管理后台的商品品牌管理能力，包括品牌的创建、更新、删除、详情查询、分页/列表查询，以及供前端下拉框使用的精简品牌列表。

## 接口路径前缀

/product/brand  (Controller: ProductBrandController)

---

## 1. 品牌管理

### 1.1 创建品牌

- **路径**: POST /product/brand/create
- **权限**: product:brand:create
- **说明**: 创建一个新的商品品牌，品牌名称全局唯一。

**请求参数 (ProductBrandCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 品牌名称，如「苹果」 |
| picUrl | String | 是 | @NotNull | 品牌图片 |
| sort | Integer | 是 | @NotNull | 品牌排序 |
| description | String | 否 | - | 品牌描述 |
| status | Integer | 是 | @NotNull | 状态（0 开启 / 1 禁用，见 CommonStatusEnum） |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的品牌编号 |

**业务逻辑**:
1. 校验品牌名称唯一（`validateBrandNameUnique`），若已存在同名品牌抛出 `BRAND_NAME_EXISTS`。
2. 将请求 VO 转换为 `ProductBrandDO` 并插入数据库。
3. 返回新品牌的编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_002_002 | 品牌名称已存在 |

### 1.2 更新品牌

- **路径**: PUT /product/brand/update
- **权限**: product:brand:update
- **说明**: 根据编号更新品牌信息，品牌名称保持全局唯一。

**请求参数 (ProductBrandUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 品牌编号 |
| name | String | 是 | @NotNull | 品牌名称 |
| picUrl | String | 是 | @NotNull | 品牌图片 |
| sort | Integer | 是 | @NotNull | 品牌排序 |
| description | String | 否 | - | 品牌描述 |
| status | Integer | 是 | @NotNull | 状态 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 `true`。

**业务逻辑**:
1. 校验品牌编号对应的品牌是否存在，不存在抛出 `BRAND_NOT_EXISTS`。
2. 校验品牌名称唯一，若被其他品牌占用抛出 `BRAND_NAME_EXISTS`。
3. 将请求 VO 转换为 `ProductBrandDO`，按编号执行更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_002_000 | 品牌不存在 |
| 1_008_002_002 | 品牌名称已存在 |

### 1.3 删除品牌

- **路径**: DELETE /product/brand/delete
- **权限**: product:brand:delete
- **说明**: 根据编号删除品牌（逻辑删除）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 品牌编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 `true`。

**业务逻辑**:
1. 校验品牌编号对应的品牌是否存在，不存在抛出 `BRAND_NOT_EXISTS`。
2. 调用 Mapper 按编号删除品牌记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_002_000 | 品牌不存在 |

### 1.4 获得品牌

- **路径**: GET /product/brand/get
- **权限**: product:brand:query
- **说明**: 根据编号获得品牌详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 品牌编号 |

**响应**: CommonResult&lt;ProductBrandRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 品牌编号 |
| name | String | 品牌名称 |
| picUrl | String | 品牌图片 |
| sort | Integer | 品牌排序 |
| description | String | 品牌描述 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 Service 按编号查询品牌记录（未命中返回 null，接口返回 data 为空）。
2. 通过 `ProductBrandConvert` 将 DO 转换为 RespVO 返回。

### 1.5 获取品牌精简信息列表

- **路径**: GET /product/brand/list-all-simple
- **权限**: 已认证（无 @PreAuthorize，主要用于前端的下拉选项）
- **说明**: 获取所有开启状态的品牌精简信息，用于前端下拉选择。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ProductBrandSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 品牌编号 |
| name | String | 品牌名称 |

**业务逻辑**:
1. 查询状态为开启（`CommonStatusEnum.ENABLE`）的品牌列表。
2. 通过 `ProductBrandConvert` 转换为精简 RespVO 列表返回。

### 1.6 获得品牌分页

- **路径**: GET /product/brand/page
- **权限**: product:brand:query
- **说明**: 分页查询品牌，支持名称模糊、状态、创建时间区间过滤。

**请求参数 (ProductBrandPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数，最大 200，默认 10 |
| name | String | 否 | - | 品牌名称，模糊匹配 |
| status | Integer | 否 | - | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ProductBrandRespVO&gt;&gt;，列表元素字段同 1.4 的 ProductBrandRespVO。

**业务逻辑**:
1. 按条件构造查询（名称 like、状态 eq、创建时间 between，均为条件存在才生效），按 id 倒序分页查询。
2. 通过 `ProductBrandConvert` 将分页结果转换为 RespVO 返回。

### 1.7 获得品牌列表

- **路径**: GET /product/brand/list
- **权限**: product:brand:query
- **说明**: 按名称条件查询品牌全量列表，按 sort 字段升序返回。

**请求参数 (ProductBrandListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 品牌名称，模糊匹配 |

**响应**: CommonResult&lt;List&lt;ProductBrandRespVO&gt;&gt;，列表元素字段同 1.4 的 ProductBrandRespVO。

**业务逻辑**:
1. 按名称模糊条件查询品牌列表（条件为空时查询全部）。
2. 在内存中按 `sort` 字段升序排序。
3. 通过 `ProductBrandConvert` 转换为 RespVO 列表返回。
