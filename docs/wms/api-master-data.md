# 主数据管理接口

## 概述

主数据管理包含物料、SKU、品牌、分类、商户、仓库六大基础数据的 CRUD 操作，是仓储业务的数据基础。

### 业务定位

- 物料是仓储管理的核心对象，通过 SKU 支持多规格管理
- 品牌和分类提供物料的组织维度，分类支持树形结构
- 商户管理客户和供应商信息，仓库管理库位信息
- 所有主数据均支持 Excel 导出功能

### 核心实体

| 实体 | 说明 |
|-----|------|
| ItemDO | 物料主数据 |
| ItemSkuDO | 物料 SKU（多规格） |
| ItemBrandDO | 品牌 |
| ItemCategoryDO | 分类（树结构） |
| MerchantDO | 商户（客户/供应商） |
| WarehouseDO | 仓库 |

---

## 物料管理

### 1. 创建物料

- **路径**: `POST /wms/item/create`
- **说明**: 创建物料及其 SKU 信息
- **权限**: `wms:item:create`
- **请求参数**: `ItemSaveReqVO`（包含物料基本信息和嵌入的 SKU 列表）
- **响应**: `CommonResult<Long>` - 物料编号
- **实现逻辑**:
  1. 校验物料编码唯一性
  2. 插入 wms_item 记录
  3. 批量插入 wms_item_sku 记录

### 2. 更新物料

- **路径**: `PUT /wms/item/update`
- **说明**: 更新物料信息及 SKU
- **权限**: `wms:item:update`
- **请求参数**: `ItemSaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`

### 3. 删除物料

- **路径**: `DELETE /wms/item/delete`
- **说明**: 删除物料及其关联 SKU
- **权限**: `wms:item:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 物料编号 |

- **响应**: `CommonResult<Boolean>`

### 4. 获取物料详情

- **路径**: `GET /wms/item/get`
- **说明**: 获取物料详情，包含 SKU 列表
- **权限**: `wms:item:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 物料编号 |

- **响应**: `CommonResult<ItemRespVO>`

### 5. 物料分页查询

- **路径**: `GET /wms/item/page`
- **说明**: 分页查询物料列表
- **权限**: `wms:item:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 物料名称（模糊匹配） |
| code | String | 否 | 物料编码（模糊匹配） |
| status | Integer | 否 | 物料状态 |
| categoryId | Long | 否 | 分类编号 |
| brandId | Long | 否 | 品牌编号 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ItemRespVO>>`

### 6. 物料精简列表

- **路径**: `GET /wms/item/simple-list`
- **说明**: 获取物料精简列表（下拉选择用）
- **权限**: 无需特定权限
- **响应**: `CommonResult<List<ItemSimpleRespVO>>`

### 7. 导出物料 Excel

- **路径**: `GET /wms/item/export-excel`
- **说明**: 导出物料数据为 Excel
- **权限**: `wms:item:export`
- **响应**: Excel 文件流

---

## SKU 管理

### 8. SKU 分页查询

- **路径**: `GET /wms/item-sku/page`
- **说明**: 分页查询 SKU 列表（只读，SKU 通过物料接口管理）
- **权限**: `wms:item-sku:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| itemId | Long | 否 | 物料编号 |
| skuNo | String | 否 | SKU 编号 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ItemSkuRespVO>>`

---

## 品牌管理

### 9. 创建品牌

- **路径**: `POST /wms/item-brand/create`
- **说明**: 创建品牌
- **权限**: `wms:item-brand:create`
- **请求参数**: `ItemBrandSaveReqVO`
- **响应**: `CommonResult<Long>` - 品牌编号

### 10. 更新品牌

- **路径**: `PUT /wms/item-brand/update`
- **说明**: 更新品牌信息
- **权限**: `wms:item-brand:update`
- **请求参数**: `ItemBrandSaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`

### 11. 删除品牌

- **路径**: `DELETE /wms/item-brand/delete`
- **说明**: 删除品牌
- **权限**: `wms:item-brand:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 品牌编号 |

- **响应**: `CommonResult<Boolean>`

### 12. 获取品牌详情

- **路径**: `GET /wms/item-brand/get`
- **说明**: 获取品牌详情
- **权限**: `wms:item-brand:query`

### 13. 品牌分页查询

- **路径**: `GET /wms/item-brand/page`
- **说明**: 分页查询品牌列表
- **权限**: `wms:item-brand:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 品牌名称（模糊匹配） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ItemBrandRespVO>>`

### 14. 品牌精简列表

- **路径**: `GET /wms/item-brand/simple-list`
- **说明**: 获取品牌精简列表（下拉选择用）
- **权限**: 无需特定权限

### 15. 导出品牌 Excel

- **路径**: `GET /wms/item-brand/export-excel`
- **说明**: 导出品牌数据为 Excel
- **权限**: `wms:item-brand:export`

---

## 分类管理

### 16. 创建分类

- **路径**: `POST /wms/item-category/create`
- **说明**: 创建分类
- **权限**: `wms:item-category:create`
- **请求参数**: `ItemCategorySaveReqVO`（包含 parentId）
- **响应**: `CommonResult<Long>` - 分类编号

### 17. 更新分类

- **路径**: `PUT /wms/item-category/update`
- **说明**: 更新分类信息
- **权限**: `wms:item-category:update`
- **请求参数**: `ItemCategorySaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`

### 18. 删除分类

- **路径**: `DELETE /wms/item-category/delete`
- **说明**: 删除分类（需校验无子分类和关联物料）
- **权限**: `wms:item-category:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 分类编号 |

- **响应**: `CommonResult<Boolean>`

### 19. 获取分类详情

- **路径**: `GET /wms/item-category/get`
- **说明**: 获取分类详情
- **权限**: `wms:item-category:query`

### 20. 分类树形列表

- **路径**: `GET /wms/item-category/list`
- **说明**: 获取分类树形结构列表
- **权限**: `wms:item-category:query`
- **响应**: `CommonResult<List<ItemCategoryRespVO>>` - 树形结构

### 21. 分类精简列表

- **路径**: `GET /wms/item-category/simple-list`
- **说明**: 获取分类精简列表（下拉选择用，平铺或树形）
- **权限**: 无需特定权限

---

## 商户管理

### 22. 创建商户

- **路径**: `POST /wms/merchant/create`
- **说明**: 创建商户
- **权限**: `wms:merchant:create`
- **请求参数**: `MerchantSaveReqVO`
- **响应**: `CommonResult<Long>` - 商户编号

### 23. 更新商户

- **路径**: `PUT /wms/merchant/update`
- **说明**: 更新商户信息
- **权限**: `wms:merchant:update`

### 24. 删除商户

- **路径**: `DELETE /wms/merchant/delete`
- **说明**: 删除商户
- **权限**: `wms:merchant:delete`

### 25. 获取商户详情

- **路径**: `GET /wms/merchant/get`
- **说明**: 获取商户详情
- **权限**: `wms:merchant:query`

### 26. 商户分页查询

- **路径**: `GET /wms/merchant/page`
- **说明**: 分页查询商户列表
- **权限**: `wms:merchant:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 商户名称（模糊匹配） |
| type | Integer | 否 | 商户类型（1=客户 2=供应商 3=两者） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<MerchantRespVO>>`

### 27. 商户精简列表

- **路径**: `GET /wms/merchant/simple-list`
- **说明**: 获取商户精简列表（下拉选择用）
- **权限**: 无需特定权限

### 28. 导出商户 Excel

- **路径**: `GET /wms/merchant/export-excel`
- **说明**: 导出商户数据为 Excel
- **权限**: `wms:merchant:export`

---

## 仓库管理

### 29. 创建仓库

- **路径**: `POST /wms/warehouse/create`
- **说明**: 创建仓库
- **权限**: `wms:warehouse:create`
- **请求参数**: `WarehouseSaveReqVO`
- **响应**: `CommonResult<Long>` - 仓库编号

### 30. 更新仓库

- **路径**: `PUT /wms/warehouse/update`
- **说明**: 更新仓库信息
- **权限**: `wms:warehouse:update`

### 31. 删除仓库

- **路径**: `DELETE /wms/warehouse/delete`
- **说明**: 删除仓库
- **权限**: `wms:warehouse:delete`

### 32. 获取仓库详情

- **路径**: `GET /wms/warehouse/get`
- **说明**: 获取仓库详情
- **权限**: `wms:warehouse:query`

### 33. 仓库分页查询

- **路径**: `GET /wms/warehouse/page`
- **说明**: 分页查询仓库列表
- **权限**: `wms:warehouse:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 仓库名称（模糊匹配） |
| code | String | 否 | 仓库编码（模糊匹配） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<WarehouseRespVO>>`

### 34. 仓库精简列表

- **路径**: `GET /wms/warehouse/simple-list`
- **说明**: 获取仓库精简列表（下拉选择用）
- **权限**: 无需特定权限

### 35. 导出仓库 Excel

- **路径**: `GET /wms/warehouse/export-excel`
- **说明**: 导出仓库数据为 Excel
- **权限**: `wms:warehouse:export`

---

## 关键实现

- **VO 组装模式**: 物料等主数据查询时，通过批量查询关联实体到 Map 中，再通过 BeanUtils.toBean() 丰富 VO
- **SKU 嵌入管理**: 物料创建/更新时，SKU 列表作为嵌入数据一起处理，通过先删后插的方式同步
- **树形结构**: 分类使用 parentId 实现树形结构，查询时递归构建树
- **Excel 导出**: 所有主数据支持基于 EasyExcel 的 Excel 导出
