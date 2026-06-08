# 商品域 API 文档

> 模块路径：`yudao-module-mall/yudao-module-product`

---

## 1. SPU 管理（admin）

**Controller**: `ProductSpuController`
**路径前缀**: `/admin-api/product/spu`
**权限前缀**: `product:spu:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建商品 SPU | `product:spu:create` |
| PUT | `/update` | 更新商品 SPU | `product:spu:update` |
| DELETE | `/delete` | 删除商品 SPU | `product:spu:delete` |
| GET | `/get` | 获取 SPU 详情 | `product:spu:query` |
| GET | `/page` | SPU 分页查询 | `product:spu:query` |
| PUT | `/update-status` | 更新 SPU 状态（上架/下架） | `product:spu:update` |

### 1.2 请求/响应 VO

**ProductSpuSaveReqVO**（创建/更新请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 商品名称 |
| keyword | String | 否 | 关键字 |
| introduction | String | 否 | 商品简介 |
| description | String | 否 | 商品详情（富文本） |
| categoryId | Long | 是 | 分类编号 |
| brandId | Long | 否 | 品牌编号 |
| picUrl | String | 是 | 商品封面图 |
| sliderPicUrls | List\<String\> | 否 | 轮播图 |
| specType | Boolean | 是 | 规格类型：false 单规格 true 多规格 |
| deliveryTemplateId | Long | 否 | 运费模板编号 |
| deliveryTypes | List\<Integer\> | 否 | 配送方式 |
| skus | List\<ProductSkuSaveReqVO\> | 是 | SKU 列表 |

**ProductSkuSaveReqVO**（SKU 请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| properties | List\<Property\> | 否 | 属性数组（多规格时必填） |
| price | Integer | 是 | 价格（分） |
| marketPrice | Integer | 否 | 市场价（分） |
| costPrice | Integer | 否 | 成本价（分） |
| barCode | String | 否 | 商品条码 |
| picUrl | String | 否 | 图片地址 |
| stock | Integer | 是 | 库存 |
| weight | Double | 否 | 重量（kg） |
| volume | Double | 否 | 体积（m^3） |

**ProductSpuPageReqVO**（分页查询请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 商品名称（模糊查询） |
| categoryId | Long | 否 | 分类编号 |
| status | Integer | 否 | 商品状态 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

### 1.3 创建流程

```
1. 校验分类是否存在 (ProductCategoryService)
2. 校验品牌是否存在 (ProductBrandService)
3. 校验 SKU 列表 (ProductSkuService.validateSkuList)
4. 初始化 SPU 信息：从 SKU 计算最低价、总库存
5. 插入 SPU 记录
6. 批量插入 SKU 记录
```

### 1.4 状态枚举

**ProductSpuStatusEnum**:

| 值 | 说明 |
|----|------|
| -1 | 回收站 |
| 0 | 下架 |
| 1 | 上架 |

---

## 2. SKU 管理（admin）

**Controller**: `ProductSkuController`
**路径前缀**: `/admin-api/product/sku`
**权限前缀**: `product:spu:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/list` | 获取 SPU 下的 SKU 列表 | `product:spu:query` |
| PUT | `/update` | 更新 SKU 信息 | `product:spu:update` |

---

## 3. 分类管理（admin）

**Controller**: `ProductCategoryController`
**路径前缀**: `/admin-api/product/category`
**权限前缀**: `product:category:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建分类 | `product:category:create` |
| PUT | `/update` | 更新分类 | `product:category:update` |
| DELETE | `/delete` | 删除分类 | `product:category:delete` |
| GET | `/get` | 获取分类详情 | `product:category:query` |
| GET | `/list` | 获取分类列表（树形） | `product:category:query` |
| GET | `/list-all` | 获取所有分类 | `product:category:query` |

**ProductCategorySaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parentId | Long | 是 | 父分类编号（0 为顶级） |
| name | String | 是 | 分类名称 |
| picUrl | String | 否 | 分类图片 |
| sort | Integer | 否 | 排序 |
| status | Integer | 是 | 状态：0 启用 1 禁用 |

---

## 4. 品牌管理（admin）

**Controller**: `ProductBrandController`
**路径前缀**: `/admin-api/product/brand`
**权限前缀**: `product:brand:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建品牌 | `product:brand:create` |
| PUT | `/update` | 更新品牌 | `product:brand:update` |
| DELETE | `/delete` | 删除品牌 | `product:brand:delete` |
| GET | `/get` | 获取品牌详情 | `product:brand:query` |
| GET | `/list-all` | 获取所有品牌 | `product:brand:query` |

**ProductBrandSaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 品牌名称 |
| picUrl | String | 否 | 品牌图片 |
| sort | Integer | 否 | 排序 |
| status | Integer | 是 | 状态 |

---

## 5. 属性管理（admin）

**Controller**: `ProductPropertyController`
**路径前缀**: `/admin-api/product/property`
**权限前缀**: `product:property:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建属性 | `product:property:create` |
| PUT | `/update` | 更新属性 | `product:property:update` |
| DELETE | `/delete` | 删除属性 | `product:property:delete` |
| GET | `/get` | 获取属性详情 | `product:property:query` |
| GET | `/list` | 获取属性列表 | `product:property:query` |

---

## 6. 商品展示（app）

**Controller**: `AppProductSpuController`
**路径前缀**: `/app-api/product/spu`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/get` | 获取商品详情（上架状态） |
| GET | `/list` | 商品列表（分页、分类筛选） |
| GET | `/search` | 商品搜索 |

---

## 7. RPC API 跨模块接口

### ProductSpuApi

| 方法 | 说明 |
|------|------|
| `getSpu(Long id)` | 查询 SPU 信息 |
| `getSpuList(List<Long> ids)` | 批量查询 SPU |
| `validateSpu(Long id)` | 校验 SPU 是否有效 |
| `updateSpuStock(Long id, Integer count)` | 更新 SPU 库存 |

### ProductSkuApi

| 方法 | 说明 |
|------|------|
| `getSku(Long id)` | 查询 SKU 信息 |
| `getSkuList(List<Long> ids)` | 批量查询 SKU |
| `validateSkuStock(Long skuId, Integer count)` | 校验 SKU 库存是否充足 |
| `updateSkuStock(Long skuId, Integer count)` | 扣减/恢复 SKU 库存 |

---

## 8. 错误码

| 错误码 | 说明 |
|--------|------|
| `1_008_005_000` | 商品 SPU 不存在 |
| `1_008_006_004` | 商品 SKU 库存不足 |
