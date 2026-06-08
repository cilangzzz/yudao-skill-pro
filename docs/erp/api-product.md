# 产品域 API 文档

## 概述

产品域涵盖产品管理、产品分类、产品单位的基础资料管理。
控制器路径前缀：`/erp/product*`

---

## 产品管理

### 创建产品

- **接口**: `POST /erp/product/create`
- **权限**: `erp:product:create`
- **请求参数**: `ErpProductSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 产品名称 |
| barCode | String | 否 | 产品条码 |
| categoryId | Long | 否 | 产品分类ID |
| unitId | Long | 否 | 单位ID |
| status | Integer | 否 | 状态(0正常 1停用) |
| standard | String | 否 | 规格 |
| purchasePrice | BigDecimal | 否 | 采购价 |
| salePrice | BigDecimal | 否 | 销售价 |
| minPrice | BigDecimal | 否 | 最低价 |

- **响应**: `CommonResult<Long>` - 产品编号

### 更新产品

- **接口**: `PUT /erp/product/update`
- **权限**: `erp:product:update`
- **请求参数**: `ErpProductSaveReqVO`（含 id）

### 删除产品

- **接口**: `DELETE /erp/product/delete`
- **权限**: `erp:product:delete`
- **请求参数**: `ids` (List<Long>)

### 查询产品分页

- **接口**: `GET /erp/product/page`
- **权限**: `erp:product:query`
- **请求参数**: `ErpProductPageReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 产品名称（模糊查询） |
| barCode | String | 否 | 产品条码 |
| categoryId | Long | 否 | 产品分类ID |
| status | Integer | 否 | 状态 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ErpProductRespVO>>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| barCode | String | 产品条码 |
| categoryId | Long | 产品分类ID |
| categoryName | String | 产品分类名称 |
| unitId | Long | 单位ID |
| unitName | String | 单位名称 |
| status | Integer | 状态 |
| standard | String | 规格 |
| purchasePrice | BigDecimal | 采购价 |
| salePrice | BigDecimal | 销售价 |
| minPrice | BigDecimal | 最低价 |

### 查询产品详情

- **接口**: `GET /erp/product/get`
- **权限**: `erp:product:query`
- **请求参数**: `id` (Long)
- **响应**: `CommonResult<ErpProductRespVO>`

### 查询产品列表

- **接口**: `GET /erp/product/list-all-simple`
- **权限**: 无（内部使用）
- **说明**: 返回简化的产品列表，用于下拉选择

---

## 产品分类

### 创建产品分类

- **接口**: `POST /erp/product-category/create`
- **权限**: `erp:product-category:create`
- **请求参数**: `ErpProductCategorySaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 分类名称 |
| parentId | Long | 否 | 父分类ID（默认0为顶级） |
| status | Integer | 否 | 状态 |

- **响应**: `CommonResult<Long>` - 分类编号

### 更新产品分类

- **接口**: `PUT /erp/product-category/update`
- **权限**: `erp:product-category:update`
- **请求参数**: `ErpProductCategorySaveReqVO`（含 id）

### 删除产品分类

- **接口**: `DELETE /erp/product-category/delete`
- **权限**: `erp:product-category:delete`
- **请求参数**: `id` (Long)

**业务逻辑**:
- 检查是否有子分类
- 检查是否有产品引用该分类

### 查询产品分类列表

- **接口**: `GET /erp/product-category/list`
- **权限**: `erp:product-category:query`
- **请求参数**: 无
- **响应**: `CommonResult<List<ErpProductCategoryRespVO>>`

**说明**: 返回树形结构的分类列表

---

## 产品单位

### 创建产品单位

- **接口**: `POST /erp/product-unit/create`
- **权限**: `erp:product-unit:create`
- **请求参数**: `ErpProductUnitSaveReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 单位名称 |
| status | Integer | 否 | 状态 |

- **响应**: `CommonResult<Long>` - 单位编号

### 更新产品单位

- **接口**: `PUT /erp/product-unit/update`
- **权限**: `erp:product-unit:update`
- **请求参数**: `ErpProductUnitSaveReqVO`（含 id）

### 删除产品单位

- **接口**: `DELETE /erp/product-unit/delete`
- **权限**: `erp:product-unit:delete`
- **请求参数**: `id` (Long)

**业务逻辑**:
- 检查是否有产品引用该单位

### 查询产品单位列表

- **接口**: `GET /erp/product-unit/list`
- **权限**: `erp:product-unit:query`
- **请求参数**: 无
- **响应**: `CommonResult<List<ErpProductUnitRespVO>>`

---

## 错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_030_000_000 | PRODUCT_NOT_EXISTS | 产品不存在 |
| 1_030_001_000 | PRODUCT_CATEGORY_NOT_EXISTS | 产品分类不存在 |
| 1_030_001_001 | PRODUCT_CATEGORY_EXISTS_CHILDREN | 该分类下存在子分类，无法删除 |
| 1_030_001_002 | PRODUCT_CATEGORY_EXISTS_PRODUCT | 该分类下存在产品，无法删除 |
| 1_030_002_000 | PRODUCT_UNIT_NOT_EXISTS | 产品单位不存在 |
| 1_030_002_001 | PRODUCT_UNIT_EXISTS_PRODUCT | 该单位被产品引用，无法删除 |
