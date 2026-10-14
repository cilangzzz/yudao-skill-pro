# 主数据接口 (WmsItemController / WmsItemSkuController / WmsItemCategoryController / WmsItemBrandController / WmsMerchantController / WmsWarehouseController)

> WMS 主数据域：仓库、商品（含 SKU 规格）、商品分类、商品品牌、往来企业（供应商/客户）的基础资料维护，供入库、出库、移库、盘库、库存等业务模块引用。

## 接口路径前缀

- `/wms/item` (Controller: WmsItemController) —— 商品管理
- `/wms/item-sku` (Controller: WmsItemSkuController) —— 商品 SKU 查询
- `/wms/item-category` (Controller: WmsItemCategoryController) —— 商品分类
- `/wms/item-brand` (Controller: WmsItemBrandController) —— 商品品牌
- `/wms/merchant` (Controller: WmsMerchantController) —— 往来企业
- `/wms/warehouse` (Controller: WmsWarehouseController) —— 仓库

---

## 1. 商品管理（/wms/item）

### 1.1 创建商品

- **路径**: POST /wms/item/create
- **权限**: wms:item:create
- **说明**: 创建商品及其 SKU 规格列表。

**请求参数 (WmsItemSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时忽略） |
| code | String | 是 | @NotBlank、@Size(max=20) | 商品编号 |
| name | String | 是 | @NotBlank、@Size(max=60) | 商品名称 |
| categoryId | Long | 是 | @NotNull | 商品分类编号 |
| unit | String | 否 | @Size(max=20) | 单位 |
| brandId | Long | 否 | - | 商品品牌编号 |
| remark | String | 否 | @Size(max=255) | 备注 |
| skus | List&lt;WmsItemSkuSaveReqVO&gt; | 是 | @Valid、@NotEmpty | 规格列表（字段见 2.1 末尾说明） |

其中 `WmsItemSkuSaveReqVO` 字段：id（Long，否）、name（String，是，@NotBlank、@Size(max=255)，规格名称）、itemId（Long，否，商品编号，由后端填充）、barCode（String，否，@Size(max=64)，条码）、code（String，否，@Size(max=64)，规格编号）、length/width/height（BigDecimal，否，@DecimalMin("0")，长宽高 cm）、grossWeight/netWeight（BigDecimal，否，@DecimalMin("0")，毛重/净重 kg）、costPrice/sellingPrice（BigDecimal，否，@DecimalMin("0")，成本价/销售价 元）。

**响应**: CommonResult&lt;Long&gt; —— 商品编号

**业务逻辑**:
1. 校验商品编号（code）全局唯一，重复抛 `ITEM_CODE_DUPLICATE`。
2. 校验商品名称（name）全局唯一，重复抛 `ITEM_NAME_DUPLICATE`。
3. 校验商品分类存在；品牌编号不为空时校验品牌存在。
4. 插入商品记录。
5. 事务内批量插入 SKU 列表（先校验至少一个 SKU、SKU 名称不重复，id 置空由数据库自增分配）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_104_000 | 商品不存在 |
| 1_060_104_001 | 商品名称重复 |
| 1_060_104_007 | 商品编号重复 |
| 1_060_104_002 | 至少包含一个商品规格 |
| 1_060_104_003 | 商品规格名称【{}】重复 |
| 1_060_102_000 | 商品分类不存在 |
| 1_060_103_000 | 商品品牌不存在 |

### 1.2 更新商品

- **路径**: PUT /wms/item/update
- **权限**: wms:item:update
- **说明**: 更新商品基本信息并同步维护 SKU 列表（请求体同 1.1 的 WmsItemSaveReqVO）。

**请求参数 (WmsItemSaveReqVO)**: 同 1.1（更新时 id 必传）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验商品存在，不存在抛 `ITEM_NOT_EXISTS`。
2. 校验商品编号、名称唯一（排除自身），分类存在、品牌存在。
3. 更新商品记录。
4. 事务内 diff 新老 SKU 列表（按 id 对比）：被删除的 SKU 先校验未被库存和四类单据使用，再批量删除。
5. 新增 SKU 忽略前端误传的 id（置 null）后批量插入；保留的 SKU 批量更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_104_000 | 商品不存在 |
| 1_060_104_001 | 商品名称重复 |
| 1_060_104_007 | 商品编号重复 |
| 1_060_104_002 | 至少包含一个商品规格 |
| 1_060_104_003 | 商品规格名称【{}】重复 |
| 1_060_104_005 | 删除失败！商品规格【{}】已被库存业务使用！ |
| 1_060_104_006 | 删除失败！商品规格【{}】已被{}使用！ |

### 1.3 删除商品

- **路径**: DELETE /wms/item/delete
- **权限**: wms:item:delete
- **说明**: 删除商品及其全部 SKU。

**请求参数**: 无（Query 参数 `id`：Long，必填，商品编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验商品存在。
2. 查询该商品全部 SKU，逐个校验未被库存业务使用（存在库存余额则抛 `ITEM_SKU_HAS_INVENTORY`）。
3. 逐个校验 SKU 未被入库/出库/移库/盘库单明细使用，否则抛 `ITEM_SKU_HAS_ORDER`。
4. 删除该商品全部 SKU。
5. 删除商品记录（整体事务）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_104_000 | 商品不存在 |
| 1_060_104_005 | 删除失败！商品规格【{}】已被库存业务使用！ |
| 1_060_104_006 | 删除失败！商品规格【{}】已被{}使用！ |

### 1.4 获得商品

- **路径**: GET /wms/item/get
- **权限**: wms:item:query
- **说明**: 按编号获得商品详情，拼接分类名、品牌名与 SKU 列表。

**请求参数**: 无（Query 参数 `id`：Long，必填，商品编号）

**响应**: CommonResult&lt;WmsItemRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 商品编号 |
| name | String | 商品名称 |
| categoryId | Long | 商品分类编号 |
| categoryName | String | 商品分类名称（关联拼接） |
| unit | String | 单位 |
| brandId | Long | 商品品牌编号 |
| brandName | String | 商品品牌名称（关联拼接） |
| remark | String | 备注 |
| skus | List&lt;WmsItemSkuRespVO&gt; | 规格列表 |
| createTime | LocalDateTime | 创建时间 |

其中 `WmsItemSkuRespVO` 字段：id、name（规格名称）、itemId、itemCode、itemName、categoryId、categoryName、unit、brandId、brandName、barCode、code（规格编号）、length、width、height、grossWeight、netWeight、costPrice、sellingPrice、createTime。

**业务逻辑**:
1. 按编号查询商品。
2. 批量查询关联分类 Map、品牌 Map、SKU 多值 Map。
3. 拷贝为 RespVO 并回填 categoryName、brandName 与 skus 列表。

### 1.5 获得商品分页

- **路径**: GET /wms/item/page
- **权限**: wms:item:query
- **说明**: 分页查询商品，分类条件自动扩展为自身及全部子分类。

**请求参数 (WmsItemPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| code | String | 否 | - | 商品编号（模糊） |
| name | String | 否 | - | 商品名称（模糊） |
| categoryId | Long | 否 | - | 商品分类编号（含子分类） |
| brandId | Long | 否 | - | 商品品牌编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;WmsItemRespVO&gt;&gt; —— 列表字段同 1.4，另含 total 总条数

**业务逻辑**:
1. 将 categoryId 递归扩展为「自身 + 全部子分类」id 集合。
2. 按条件分页查询商品。
3. 批量查询分类/品牌/SKU 关联数据并拼接 categoryName、brandName、skus。

### 1.6 获得商品精简列表

- **路径**: GET /wms/item/simple-list
- **权限**: wms:item:query
- **说明**: 不分页查询商品列表（弹窗/选择器场景），查询条件同 1.5。

**请求参数 (WmsItemListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| code | String | 否 | - | 商品编号 |
| name | String | 否 | - | 商品名称 |
| categoryId | Long | 否 | - | 商品分类编号（含子分类） |
| brandId | Long | 否 | - | 商品品牌编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;List&lt;WmsItemRespVO&gt;&gt; —— 字段同 1.4

**业务逻辑**:
1. categoryId 递归扩展为自身及子分类 id 集合。
2. 按条件查询全量商品列表并拼接分类名、品牌名、SKU 列表。

### 1.7 导出商品 Excel

- **路径**: GET /wms/item/export-excel
- **权限**: wms:item:export
- **说明**: 按分页条件导出全量商品 Excel（文件名「商品.xls」），导出列同 WmsItemRespVO 的 @ExcelProperty 字段。

**请求参数 (WmsItemPageReqVO)**: 同 1.5

**响应**: Excel 文件流（无 CommonResult 包装）

**业务逻辑**:
1. 将 pageSize 置为不分页。
2. 按条件查询全量商品并拼接分类名、品牌名、SKU。
3. 通过 ExcelUtils 写出文件流。

## 2. 商品 SKU 查询（/wms/item-sku）

### 2.1 获得商品 SKU 分页

- **路径**: GET /wms/item-sku/page
- **权限**: wms:item:query（复用商品查询权限，不单独建权限点）
- **说明**: 按 SKU 一行展开的分页查询，支持商品/品牌/分类多表联查筛选，用于弹窗与选择器场景。SKU 的新增/修改/删除随商品接口（1.1/1.2/1.3）维护，不在本 Controller 暴露。

**请求参数 (WmsItemSkuPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| itemCode | String | 否 | - | 商品编号（模糊） |
| itemName | String | 否 | - | 商品名称（模糊） |
| categoryId | Long | 否 | - | 商品分类编号 |
| brandId | Long | 否 | - | 商品品牌编号 |
| code | String | 否 | - | 规格编号 |
| name | String | 否 | - | 规格名称 |
| barCode | String | 否 | - | 条码 |

**响应**: CommonResult&lt;PageResult&lt;WmsItemSkuRespVO&gt;&gt; —— 字段见 1.4 中的 WmsItemSkuRespVO

**业务逻辑**:
1. 按 SKU 维度分页查询（Mapper 中联查商品表按 itemCode/itemName 等筛选）。
2. 批量查询 SKU 关联的商品 Map。
3. 基于商品的 categoryId、brandId 批量查询分类 Map 与品牌 Map。
4. 拼接 itemCode、itemName、unit、categoryId、brandId、categoryName、brandName 到 RespVO。

## 3. 商品分类（/wms/item-category）

### 3.1 创建商品分类

- **路径**: POST /wms/item-category/create
- **权限**: wms:item-category:create
- **说明**: 创建树形商品分类节点。

**请求参数 (WmsItemCategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时忽略） |
| parentId | Long | 是 | @NotNull | 父级编号（0 表示根节点） |
| code | String | 是 | @NotEmpty、@Size(max=20) | 分类编号 |
| name | String | 是 | @NotEmpty、@Size(max=30) | 分类名称 |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 停用） |

**响应**: CommonResult&lt;Long&gt; —— 分类编号

**业务逻辑**:
1. 校验分类编号（code）全局唯一。
2. 校验同一父级下分类名称唯一。
3. 校验父分类合法：不能设置自己为父分类；父分类必须存在；递归校验父分类链不能形成环路。
4. 插入分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_102_007 | 商品分类编号重复 |
| 1_060_102_001 | 商品分类名称重复 |
| 1_060_102_002 | 父商品分类不存在 |
| 1_060_102_003 | 不能设置自己为父商品分类 |
| 1_060_102_004 | 不能设置自己的子商品分类为父商品分类 |

### 3.2 更新商品分类

- **路径**: PUT /wms/item-category/update
- **权限**: wms:item-category:update
- **说明**: 更新商品分类（请求体同 3.1 的 WmsItemCategorySaveReqVO，id 必传）。

**请求参数 (WmsItemCategorySaveReqVO)**: 同 3.1

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验分类存在，不存在抛 `ITEM_CATEGORY_NOT_EXISTS`。
2. 校验编号唯一、同级名称唯一。
3. 校验父分类合法（不能自指、必须存在、不能把子孙分类设为父分类形成环路）。
4. 更新分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_102_000 | 商品分类不存在 |
| 1_060_102_007 | 商品分类编号重复 |
| 1_060_102_001 | 商品分类名称重复 |
| 1_060_102_002 | 父商品分类不存在 |
| 1_060_102_003 | 不能设置自己为父商品分类 |
| 1_060_102_004 | 不能设置自己的子商品分类为父商品分类 |

### 3.3 删除商品分类

- **路径**: DELETE /wms/item-category/delete
- **权限**: wms:item-category:delete
- **说明**: 删除叶子分类节点。

**请求参数**: 无（Query 参数 `id`：Long，必填，分类编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验分类存在。
2. 存在子分类则抛 `ITEM_CATEGORY_HAS_CHILDREN`。
3. 分类下存在商品则抛 `ITEM_CATEGORY_HAS_ITEM`。
4. 删除分类记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_102_000 | 商品分类不存在 |
| 1_060_102_005 | 删除失败！请先删除该分类下的子分类！ |
| 1_060_102_006 | 删除失败！分类已被商品使用！ |

### 3.4 获得商品分类

- **路径**: GET /wms/item-category/get
- **权限**: wms:item-category:query
- **说明**: 按编号获得分类详情。

**请求参数**: 无（Query 参数 `id`：Long，必填，分类编号）

**响应**: CommonResult&lt;WmsItemCategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| parentId | Long | 父级编号 |
| code | String | 分类编号 |
| name | String | 分类名称 |
| sort | Integer | 排序 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询分类并拷贝为 RespVO。

### 3.5 获得商品分类列表

- **路径**: GET /wms/item-category/list
- **权限**: wms:item-category:query
- **说明**: 按条件查询分类列表。

**请求参数 (WmsItemCategoryListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| parentId | Long | 否 | - | 父级编号 |
| code | String | 否 | - | 分类编号 |
| name | String | 否 | - | 分类名称 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态 |

**响应**: CommonResult&lt;List&lt;WmsItemCategoryRespVO&gt;&gt; —— 字段同 3.4

**业务逻辑**: 1. 按条件查询分类列表并拷贝为 RespVO。

### 3.6 获得商品分类精简列表

- **路径**: GET /wms/item-category/simple-list
- **权限**: wms:item-category:query
- **说明**: 全量分类列表，主要用于前端下拉。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;WmsItemCategoryRespVO&gt;&gt; —— 字段同 3.4

**业务逻辑**: 1. 以空条件调用列表查询，返回全量分类。

## 4. 商品品牌（/wms/item-brand）

### 4.1 创建商品品牌

- **路径**: POST /wms/item-brand/create
- **权限**: wms:item-brand:create
- **说明**: 创建商品品牌。

**请求参数 (WmsItemBrandSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时忽略） |
| code | String | 是 | @NotEmpty、@Size(max=20) | 品牌编号 |
| name | String | 是 | @NotEmpty、@Size(max=30) | 品牌名称 |

**响应**: CommonResult&lt;Long&gt; —— 品牌编号

**业务逻辑**:
1. 校验品牌编号（code）全局唯一。
2. 校验品牌名称全局唯一。
3. 插入品牌记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_103_002 | 商品品牌编号重复 |
| 1_060_103_003 | 商品品牌名称重复 |

### 4.2 更新商品品牌

- **路径**: PUT /wms/item-brand/update
- **权限**: wms:item-brand:update
- **说明**: 更新商品品牌（请求体同 4.1，id 必传）。

**请求参数 (WmsItemBrandSaveReqVO)**: 同 4.1

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验品牌存在，不存在抛 `ITEM_BRAND_NOT_EXISTS`。
2. 校验品牌编号、名称唯一（排除自身）。
3. 更新品牌记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_103_000 | 商品品牌不存在 |
| 1_060_103_002 | 商品品牌编号重复 |
| 1_060_103_003 | 商品品牌名称重复 |

### 4.3 删除商品品牌

- **路径**: DELETE /wms/item-brand/delete
- **权限**: wms:item-brand:delete
- **说明**: 删除未被商品使用的品牌。

**请求参数**: 无（Query 参数 `id`：Long，必填，品牌编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验品牌存在。
2. 品牌下存在商品则抛 `ITEM_BRAND_HAS_ITEM`。
3. 删除品牌记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_103_000 | 商品品牌不存在 |
| 1_060_103_001 | 删除失败！品牌已被商品使用！ |

### 4.4 获得商品品牌

- **路径**: GET /wms/item-brand/get
- **权限**: wms:item-brand:query
- **说明**: 按编号获得品牌详情。

**请求参数**: 无（Query 参数 `id`：Long，必填，品牌编号）

**响应**: CommonResult&lt;WmsItemBrandRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 品牌编号 |
| name | String | 品牌名称 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询品牌并拷贝为 RespVO。

### 4.5 获得商品品牌分页

- **路径**: GET /wms/item-brand/page
- **权限**: wms:item-brand:query
- **说明**: 分页查询品牌。

**请求参数 (WmsItemBrandPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| code | String | 否 | - | 品牌编号（模糊） |
| name | String | 否 | - | 品牌名称（模糊） |

**响应**: CommonResult&lt;PageResult&lt;WmsItemBrandRespVO&gt;&gt; —— 字段同 4.4

**业务逻辑**: 1. 按条件分页查询品牌。

### 4.6 获得商品品牌精简列表

- **路径**: GET /wms/item-brand/simple-list
- **权限**: wms:item-brand:query
- **说明**: 全量品牌列表，主要用于前端下拉。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;WmsItemBrandRespVO&gt;&gt; —— 字段同 4.4

**业务逻辑**: 1. 查询全量品牌列表。

### 4.7 导出商品品牌 Excel

- **路径**: GET /wms/item-brand/export-excel
- **权限**: wms:item-brand:export
- **说明**: 按分页条件导出全量品牌 Excel（文件名「商品品牌.xls」）。

**请求参数 (WmsItemBrandPageReqVO)**: 同 4.5

**响应**: Excel 文件流（无 CommonResult 包装）

**业务逻辑**:
1. 将 pageSize 置为不分页。
2. 按条件查询全量品牌。
3. 通过 ExcelUtils 写出文件流。

## 5. 往来企业（/wms/merchant）

### 5.1 创建往来企业

- **路径**: POST /wms/merchant/create
- **权限**: wms:merchant:create
- **说明**: 创建供应商/客户等往来企业资料。

**请求参数 (WmsMerchantSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时忽略） |
| code | String | 是 | @NotBlank、@Size(max=20) | 往来企业编号 |
| name | String | 是 | @NotBlank、@Size(max=60) | 往来企业名称 |
| type | Integer | 是 | @NotNull、@InEnum(WmsMerchantTypeEnum) | 类型（1 客户 / 2 供应商 / 3 客户&amp;供应商） |
| level | String | 否 | @Size(max=10) | 级别 |
| bankName | String | 否 | @Size(max=255) | 开户行 |
| bankAccount | String | 否 | @Size(max=40) | 银行账户 |
| address | String | 否 | @Size(max=200) | 地址 |
| mobile | String | 否 | @Size(max=13) | 手机号 |
| telephone | String | 否 | @Size(max=13) | 座机号 |
| contact | String | 否 | @Size(max=30) | 联系人 |
| email | String | 否 | @Size(max=50) | Email |
| remark | String | 否 | @Size(max=255) | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 往来企业编号

**业务逻辑**:
1. 校验企业编号（code）全局唯一。
2. 校验企业名称全局唯一。
3. 插入往来企业记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_105_004 | 往来企业编号重复 |
| 1_060_105_005 | 往来企业名称重复 |

### 5.2 更新往来企业

- **路径**: PUT /wms/merchant/update
- **权限**: wms:merchant:update
- **说明**: 更新往来企业（请求体同 5.1，id 必传）。

**请求参数 (WmsMerchantSaveReqVO)**: 同 5.1

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验企业存在，不存在抛 `MERCHANT_NOT_EXISTS`。
2. 校验企业编号、名称唯一（排除自身）。
3. 更新往来企业记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_105_000 | 往来企业不存在 |
| 1_060_105_004 | 往来企业编号重复 |
| 1_060_105_005 | 往来企业名称重复 |

### 5.3 删除往来企业

- **路径**: DELETE /wms/merchant/delete
- **权限**: wms:merchant:delete
- **说明**: 删除未被单据使用的往来企业。

**请求参数**: 无（Query 参数 `id`：Long，必填，企业编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验企业存在。
2. 校验未被入库单使用，否则抛 `MERCHANT_HAS_ORDER`（提示「入库单」）。
3. 校验未被出库单使用，否则抛 `MERCHANT_HAS_ORDER`（提示「出库单」）。
4. 删除往来企业记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_105_000 | 往来企业不存在 |
| 1_060_105_003 | 删除失败！往来企业已被{}使用！ |

### 5.4 获得往来企业

- **路径**: GET /wms/merchant/get
- **权限**: wms:merchant:query
- **说明**: 按编号获得往来企业详情。

**请求参数**: 无（Query 参数 `id`：Long，必填，企业编号）

**响应**: CommonResult&lt;WmsMerchantRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 往来企业编号 |
| name | String | 往来企业名称 |
| type | Integer | 往来企业类型 |
| level | String | 级别 |
| bankName | String | 开户行 |
| bankAccount | String | 银行账户 |
| address | String | 地址 |
| mobile | String | 手机号 |
| telephone | String | 座机号 |
| contact | String | 联系人 |
| email | String | Email |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询往来企业并拷贝为 RespVO。

### 5.5 获得往来企业分页

- **路径**: GET /wms/merchant/page
- **权限**: wms:merchant:query
- **说明**: 分页查询往来企业，支持单类型或类型数组筛选。

**请求参数 (WmsMerchantPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| code | String | 否 | - | 往来企业编号（模糊） |
| name | String | 否 | - | 往来企业名称（模糊） |
| type | Integer | 否 | @InEnum(WmsMerchantTypeEnum) | 类型 |
| types | List&lt;Integer&gt; | 否 | @InEnum(WmsMerchantTypeEnum) | 类型数组 |

**响应**: CommonResult&lt;PageResult&lt;WmsMerchantRespVO&gt;&gt; —— 字段同 5.4

**业务逻辑**: 1. 按条件分页查询往来企业。

### 5.6 获得往来企业精简列表

- **路径**: GET /wms/merchant/simple-list
- **权限**: wms:merchant:query
- **说明**: 按条件查询往来企业列表，主要用于前端下拉（可按类型过滤出供应商/客户）。

**请求参数 (WmsMerchantListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| code | String | 否 | - | 往来企业编号 |
| name | String | 否 | - | 往来企业名称 |
| type | Integer | 否 | @InEnum(WmsMerchantTypeEnum) | 类型 |
| types | List&lt;Integer&gt; | 否 | @InEnum(WmsMerchantTypeEnum) | 类型数组 |

**响应**: CommonResult&lt;List&lt;WmsMerchantRespVO&gt;&gt; —— 字段同 5.4

**业务逻辑**: 1. 按条件查询往来企业列表。

### 5.7 导出往来企业 Excel

- **路径**: GET /wms/merchant/export-excel
- **权限**: wms:merchant:export
- **说明**: 按分页条件导出全量往来企业 Excel（文件名「往来企业.xls」，类型列按字典 MERCHANT_TYPE 转换）。

**请求参数 (WmsMerchantPageReqVO)**: 同 5.5

**响应**: Excel 文件流（无 CommonResult 包装）

**业务逻辑**:
1. 将 pageSize 置为不分页。
2. 按条件查询全量往来企业。
3. 通过 ExcelUtils 写出文件流。

## 6. 仓库（/wms/warehouse）

### 6.1 创建仓库

- **路径**: POST /wms/warehouse/create
- **权限**: wms:warehouse:create
- **说明**: 创建仓库。

**请求参数 (WmsWarehouseSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时忽略） |
| code | String | 是 | @NotEmpty、@Size(max=20) | 仓库编号 |
| name | String | 是 | @NotEmpty | 仓库名称 |
| sort | Integer | 是 | @NotNull | 排序 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 仓库编号

**业务逻辑**:
1. 校验仓库名称全局唯一。
2. 校验仓库编号（code）全局唯一。
3. 插入仓库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_100_001 | 仓库名称重复 |
| 1_060_100_002 | 仓库编号重复 |

### 6.2 更新仓库

- **路径**: PUT /wms/warehouse/update
- **权限**: wms:warehouse:update
- **说明**: 更新仓库（请求体同 6.1，id 必传）。

**请求参数 (WmsWarehouseSaveReqVO)**: 同 6.1

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验仓库存在，不存在抛 `WAREHOUSE_NOT_EXISTS`。
2. 校验仓库名称、编号唯一（排除自身）。
3. 更新仓库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_100_000 | 仓库不存在 |
| 1_060_100_001 | 仓库名称重复 |
| 1_060_100_002 | 仓库编号重复 |

### 6.3 删除仓库

- **路径**: DELETE /wms/warehouse/delete
- **权限**: wms:warehouse:delete
- **说明**: 删除未被库存和单据使用的仓库。

**请求参数**: 无（Query 参数 `id`：Long，必填，仓库编号）

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功

**业务逻辑**:
1. 校验仓库存在。
2. 校验无库存余额，否则抛 `WAREHOUSE_HAS_INVENTORY`。
3. 依次校验未被入库单、出库单、移库单、盘库单使用，否则抛 `WAREHOUSE_HAS_ORDER`（提示对应单据名）。
4. 删除仓库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_100_000 | 仓库不存在 |
| 1_060_100_004 | 删除失败！仓库已被{}使用！ |
| 1_060_100_005 | 删除失败！仓库已存在库存余额！ |

### 6.4 获得仓库

- **路径**: GET /wms/warehouse/get
- **权限**: wms:warehouse:query
- **说明**: 按编号获得仓库详情。

**请求参数**: 无（Query 参数 `id`：Long，必填，仓库编号）

**响应**: CommonResult&lt;WmsWarehouseRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 仓库编号 |
| name | String | 仓库名称 |
| remark | String | 备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询仓库并拷贝为 RespVO。

### 6.5 获得仓库分页

- **路径**: GET /wms/warehouse/page
- **权限**: wms:warehouse:query
- **说明**: 分页查询仓库。

**请求参数 (WmsWarehousePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| code | String | 否 | - | 仓库编号（模糊） |
| name | String | 否 | - | 仓库名称（模糊） |

**响应**: CommonResult&lt;PageResult&lt;WmsWarehouseRespVO&gt;&gt; —— 字段同 6.4

**业务逻辑**: 1. 按条件分页查询仓库。

### 6.6 获得仓库精简列表

- **路径**: GET /wms/warehouse/simple-list
- **权限**: wms:warehouse:query
- **说明**: 全量仓库列表，主要用于前端下拉。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;WmsWarehouseRespVO&gt;&gt; —— 字段同 6.4

**业务逻辑**: 1. 查询全量仓库列表（按排序）。

### 6.7 导出仓库 Excel

- **路径**: GET /wms/warehouse/export-excel
- **权限**: wms:warehouse:export
- **说明**: 按分页条件导出全量仓库 Excel（文件名「仓库.xls」）。

**请求参数 (WmsWarehousePageReqVO)**: 同 6.5

**响应**: Excel 文件流（无 CommonResult 包装）

**业务逻辑**:
1. 将 pageSize 置为不分页。
2. 按条件查询全量仓库。
3. 通过 ExcelUtils 写出文件流。
