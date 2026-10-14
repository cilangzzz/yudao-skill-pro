# 产品管理接口 (ErpProductController / ErpProductCategoryController / ErpProductUnitController)

> ERP 产品管理域，提供产品档案、产品分类（树形）、产品单位三类主数据的管理，供采购、销售等业务单据引用。

## 接口路径前缀

- /erp/product  (Controller: ErpProductController)
- /erp/product-category  (Controller: ErpProductCategoryController)
- /erp/product-unit  (Controller: ErpProductUnitController)

---

## 1. 产品管理（/erp/product）

### 1.1 创建产品

- **路径**: POST /erp/product/create
- **权限**: erp:product:create
- **说明**: 创建一条产品档案记录

**请求参数 (ProductSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 产品编号（新增时不传） |
| name | String | 是 | @NotEmpty | 产品名称 |
| barCode | String | 是 | @NotEmpty | 产品条码 |
| categoryId | Long | 是 | @NotNull | 产品分类编号 |
| unitId | Long | 是 | @NotNull | 单位编号 |
| status | Integer | 是 | @NotNull | 产品状态 |
| standard | String | 否 | - | 产品规格 |
| remark | String | 否 | - | 产品备注 |
| expiryDay | Integer | 否 | - | 保质期天数 |
| weight | BigDecimal | 否 | - | 基础重量（kg） |
| purchasePrice | BigDecimal | 否 | - | 采购价格，单位：元 |
| salePrice | BigDecimal | 否 | - | 销售价格，单位：元 |
| minPrice | BigDecimal | 否 | - | 最低价格，单位：元 |

**响应**: CommonResult&lt;Long&gt; — 产品编号

**业务逻辑**: 1. 将 ReqVO 转换为 ErpProductDO；2. 插入产品表；3. 返回产品编号（分类有效性校验为 TODO 待实现）。

### 1.2 更新产品

- **路径**: PUT /erp/product/update
- **权限**: erp:product:update
- **说明**: 更新产品档案信息

**请求参数 (ProductSaveReqVO)**: 同 1.1 创建产品（id 必传用于定位记录）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**: 1. 校验产品是否存在（不存在抛 PRODUCT_NOT_EXISTS）；2. ReqVO 转换为 DO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_500_000 | 产品不存在 |

### 1.3 删除产品

- **路径**: DELETE /erp/product/delete
- **权限**: erp:product:delete
- **说明**: 删除指定产品，若被业务单据引用则禁止删除

**请求参数**: Query 参数 id（Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**: 1. 校验产品存在；2. 依次校验六类业务单据明细的引用计数：采购订单（PRODUCT_DELETE_FAIL_PURCHASE_ORDER_EXISTS）、采购入库单（PRODUCT_DELETE_FAIL_PURCHASE_IN_EXISTS）、采购退货单（PRODUCT_DELETE_FAIL_PURCHASE_RETURN_EXISTS）、销售订单（PRODUCT_DELETE_FAIL_SALE_ORDER_EXISTS）、销售出库单（PRODUCT_DELETE_FAIL_SALE_OUT_EXISTS）、销售退货单（PRODUCT_DELETE_FAIL_SALE_RETURN_EXISTS），任一引用计数 > 0 则抛对应错误；3. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_500_000 | 产品不存在 |
| 1_030_500_002 | 产品已被采购订单引用，无法删除 |
| 1_030_500_003 | 产品已被采购入库单引用，无法删除 |
| 1_030_500_004 | 产品已被采购退货单引用，无法删除 |
| 1_030_500_005 | 产品已被销售订单引用，无法删除 |
| 1_030_500_006 | 产品已被销售出库单引用，无法删除 |
| 1_030_500_007 | 产品已被销售退货单引用，无法删除 |

### 1.4 获得产品

- **路径**: GET /erp/product/get
- **权限**: erp:product:query
- **说明**: 按编号查询单个产品详情

**请求参数**: Query 参数 id（Long，必填，编号）

**响应**: CommonResult&lt;ErpProductRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| barCode | String | 产品条码 |
| categoryId | Long | 产品分类编号 |
| categoryName | String | 产品分类名称 |
| unitId | Long | 单位编号 |
| unitName | String | 单位名称 |
| status | Integer | 产品状态 |
| standard | String | 产品规格 |
| remark | String | 产品备注 |
| expiryDay | Integer | 保质期天数 |
| weight | BigDecimal | 基础重量（kg） |
| purchasePrice | BigDecimal | 采购价格，单位：元 |
| salePrice | BigDecimal | 销售价格，单位：元 |
| minPrice | BigDecimal | 最低价格，单位：元 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 ErpProductDO；2. BeanUtils 转换为 ErpProductRespVO 返回（不含分类/单位名称填充）。

### 1.5 获得产品分页

- **路径**: GET /erp/product/page
- **权限**: erp:product:query
- **说明**: 分页查询产品列表，附带分类名称、单位名称

**请求参数 (ErpProductPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 产品名称，模糊匹配 |
| categoryId | Long | 否 | - | 产品分类编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ErpProductRespVO&gt;&gt; — 列表字段同 1.4 响应表

**业务逻辑**: 1. 按 ErpProductMapper.selectPage 分页查询产品 DO；2. 收集结果中的 categoryId/unitId，批量查询分类 Map 与单位 Map；3. 转换为 RespVO 并回填 categoryName、unitName。

### 1.6 获得产品精简列表

- **路径**: GET /erp/product/simple-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 获得已启用（CommonStatusEnum.ENABLE）产品的精简列表，用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ErpProductRespVO&gt;&gt; — 仅填充以下字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| barCode | String | 产品条码 |
| categoryId | Long | 产品分类编号 |
| categoryName | String | 产品分类名称 |
| unitId | Long | 单位编号 |
| unitName | String | 单位名称 |
| purchasePrice | BigDecimal | 采购价格，单位：元 |
| salePrice | BigDecimal | 销售价格，单位：元 |
| minPrice | BigDecimal | 最低价格，单位：元 |

**业务逻辑**: 1. 按状态=开启查询全部启用产品；2. 复用 buildProductVOList 回填分类/单位名称；3. 在 Controller 中裁剪为仅含 id、名称、条码、分类、单位、三个价格字段的精简 VO 列表。

### 1.7 导出产品 Excel

- **路径**: GET /erp/product/export-excel
- **权限**: erp:product:export
- **说明**: 按分页查询条件导出全部产品为 Excel 文件（产品.xls）

**请求参数 (ErpProductPageReqVO)**: 同 1.5 分页查询（pageSize 强制置为 PAGE_SIZE_NONE 导出全部）

**响应**: Excel 文件流（ErpProductRespVO 为导出行结构，含 @ExcelProperty 注解列）

**业务逻辑**: 1. 将分页参数 pageSize 设置为 PAGE_SIZE_NONE；2. 调用 getProductVOPage 查询全部（含分类/单位名称回填）；3. ExcelUtils.write 输出"产品.xls"。

---

## 2. 产品分类管理（/erp/product-category）

### 2.1 创建产品分类

- **路径**: POST /erp/product-category/create
- **权限**: erp:product-category:create
- **说明**: 创建一条产品分类（支持树形父分类）

**请求参数 (ErpProductCategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 分类编号（新增时不传） |
| parentId | Long | 是 | @NotNull | 父分类编号 |
| name | String | 是 | @NotEmpty | 分类名称 |
| code | String | 是 | @NotEmpty | 分类编码 |
| sort | Integer | 是 | @NotNull | 分类排序 |
| status | Integer | 是 | @NotNull | 开启状态 |

**响应**: CommonResult&lt;Long&gt; — 分类编号

**业务逻辑**: 1. 校验父分类有效性：parentId 为空或为根（PARENT_ID_ROOT）直接通过，不能设置自己为父分类（PRODUCT_CATEGORY_PARENT_ERROR），父分类必须存在（PRODUCT_CATEGORY_PARENT_NOT_EXITS），新增时不做环路校验；2. 校验同一父分类下分类名称唯一（PRODUCT_CATEGORY_NAME_DUPLICATE）；3. 转换为 DO 插入并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_501_002 | 父级产品分类不存在 |
| 1_030_501_003 | 不能设置自己为父产品分类 |
| 1_030_501_004 | 已经存在该分类名称的产品分类 |

### 2.2 更新产品分类

- **路径**: PUT /erp/product-category/update
- **权限**: erp:product-category:update
- **说明**: 更新产品分类信息

**请求参数 (ErpProductCategorySaveReqVO)**: 同 2.1 创建产品分类（id 必传）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**: 1. 校验分类存在；2. 校验父分类有效性：不能自设为父分类、父分类必须存在，并沿父链递归校验，若父分类是自己的子孙分类则抛环路错误（PRODUCT_CATEGORY_PARENT_IS_CHILD）；3. 校验同父下名称唯一（排除自身）；4. 转换为 DO 按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_501_000 | 产品分类不存在 |
| 1_030_501_002 | 父级产品分类不存在 |
| 1_030_501_003 | 不能设置自己为父产品分类 |
| 1_030_501_004 | 已经存在该分类名称的产品分类 |
| 1_030_501_005 | 不能设置自己的子分类为父分类 |

### 2.3 删除产品分类

- **路径**: DELETE /erp/product-category/delete
- **权限**: erp:product-category:delete
- **说明**: 删除产品分类，存在子分类或存在引用产品时禁止删除

**请求参数**: Query 参数 id（Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**: 1. 校验分类存在；2. 校验是否存在子产品分类（selectCountByParentId > 0 抛 PRODUCT_CATEGORY_EXITS_CHILDREN）；3. 校验是否有产品使用该分类（productService.getProductCountByCategoryId > 0 抛 PRODUCT_CATEGORY_EXITS_PRODUCT）；4. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_501_000 | 产品分类不存在 |
| 1_030_501_001 | 存在存在子产品分类，无法删除 |
| 1_030_502_002 | 存在产品使用该分类，无法删除（注：源码中 PRODUCT_CATEGORY_EXITS_PRODUCT 复用产品单位错误码段 1_030_502_002） |

### 2.4 获得产品分类

- **路径**: GET /erp/product-category/get
- **权限**: erp:product-category:query
- **说明**: 按编号查询单个产品分类

**请求参数**: Query 参数 id（Long，必填，编号）

**响应**: CommonResult&lt;ErpProductCategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| parentId | Long | 父分类编号 |
| name | String | 分类名称 |
| code | String | 分类编码 |
| sort | Integer | 分类排序 |
| status | Integer | 开启状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 ErpProductCategoryDO；2. BeanUtils 转换为 RespVO 返回。

### 2.5 获得产品分类列表

- **路径**: GET /erp/product-category/list
- **权限**: erp:product-category:query
- **说明**: 按条件查询产品分类列表（不分页）

**请求参数 (ErpProductCategoryListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | - | 分类名称，模糊匹配 |
| status | Integer | 否 | - | 开启状态 |

**响应**: CommonResult&lt;List&lt;ErpProductCategoryRespVO&gt;&gt; — 字段同 2.4 响应表

**业务逻辑**: 1. 按 ErpProductCategoryMapper.selectList 条件查询分类 DO 列表；2. BeanUtils 批量转换为 RespVO 返回。

### 2.6 获得产品分类精简列表

- **路径**: GET /erp/product-category/simple-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 获得已开启（CommonStatusEnum.ENABLE）的产品分类精简列表，用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ErpProductCategoryRespVO&gt;&gt; — 仅填充以下字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| name | String | 分类名称 |
| parentId | Long | 父分类编号 |

**业务逻辑**: 1. 构造 status=开启 的 ListReqVO 查询启用分类；2. 在 Controller 中裁剪为仅含 id、name、parentId 的精简 VO 列表返回。

### 2.7 导出产品分类 Excel

- **路径**: GET /erp/product-category/export-excel
- **权限**: erp:product-category:export
- **说明**: 按列表查询条件导出产品分类为 Excel 文件（产品分类.xls）

**请求参数 (ErpProductCategoryListReqVO)**: 同 2.5 列表查询

**响应**: Excel 文件流（ErpProductCategoryRespVO 为导出行结构，状态列经 DictConvert 字典转换）

**业务逻辑**: 1. 按条件查询全部分类 DO；2. BeanUtils 批量转换为 RespVO；3. ExcelUtils.write 输出"产品分类.xls"。

---

## 3. 产品单位管理（/erp/product-unit）

### 3.1 创建产品单位

- **路径**: POST /erp/product-unit/create
- **权限**: erp:product-unit:create
- **说明**: 创建一条产品计量单位

**请求参数 (ErpProductUnitSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 单位编号（新增时不传） |
| name | String | 是 | @NotEmpty | 单位名字 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum.class) | 单位状态 |

**响应**: CommonResult&lt;Long&gt; — 单位编号

**业务逻辑**: 1. 校验单位名字唯一（selectByName 存在即抛 PRODUCT_UNIT_NAME_DUPLICATE）；2. 转换为 DO 插入并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_502_001 | 已存在该名字的产品单位 |

### 3.2 更新产品单位

- **路径**: PUT /erp/product-unit/update
- **权限**: erp:product-unit:update
- **说明**: 更新产品单位信息

**请求参数 (ErpProductUnitSaveReqVO)**: 同 3.1 创建产品单位（id 必传）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**: 1. 校验单位存在；2. 校验单位名字唯一（排除自身 id）；3. 转换为 DO 按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_502_000 | 产品单位不存在 |
| 1_030_502_001 | 已存在该名字的产品单位 |

### 3.3 删除产品单位

- **路径**: DELETE /erp/product-unit/delete
- **权限**: erp:product-unit:delete
- **说明**: 删除产品单位，存在产品使用该单位时禁止删除

**请求参数**: Query 参数 id（Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**: 1. 校验单位存在；2. 校验是否有产品使用该单位（productService.getProductCountByUnitId > 0 抛 PRODUCT_UNIT_EXITS_PRODUCT）；3. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_502_000 | 产品单位不存在 |
| 1_030_502_002 | 存在产品使用该单位，无法删除 |

### 3.4 获得产品单位

- **路径**: GET /erp/product-unit/get
- **权限**: erp:product-unit:query
- **说明**: 按编号查询单个产品单位

**请求参数**: Query 参数 id（Long，必填，编号）

**响应**: CommonResult&lt;ErpProductUnitRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 单位编号 |
| name | String | 单位名字 |
| status | Integer | 单位状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 ErpProductUnitDO；2. BeanUtils 转换为 RespVO 返回。

### 3.5 获得产品单位分页

- **路径**: GET /erp/product-unit/page
- **权限**: erp:product-unit:query
- **说明**: 分页查询产品单位列表

**请求参数 (ErpProductUnitPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 单位名字，模糊匹配 |
| status | Integer | 否 | - | 单位状态 |

**响应**: CommonResult&lt;PageResult&lt;ErpProductUnitRespVO&gt;&gt; — 字段同 3.4 响应表

**业务逻辑**: 1. 按 ErpProductUnitMapper.selectPage 分页查询单位 DO；2. BeanUtils 批量转换为 RespVO 返回。

### 3.6 获得产品单位精简列表

- **路径**: GET /erp/product-unit/simple-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 获得已开启（CommonStatusEnum.ENABLE）的单位精简列表，用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ErpProductUnitRespVO&gt;&gt; — 仅填充以下字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 单位编号 |
| name | String | 单位名字 |

**业务逻辑**: 1. 按状态=开启查询全部启用单位；2. 在 Controller 中裁剪为仅含 id、name 的精简 VO 列表返回。

### 3.7 导出产品单位 Excel

- **路径**: GET /erp/product-unit/export-excel
- **权限**: erp:product-unit:export
- **说明**: 按分页查询条件导出全部产品单位为 Excel 文件（产品单位.xls）

**请求参数 (ErpProductUnitPageReqVO)**: 同 3.5 分页查询（pageSize 强制置为 PAGE_SIZE_NONE 导出全部）

**响应**: Excel 文件流（ErpProductUnitRespVO 为导出行结构）

**业务逻辑**: 1. 将分页参数 pageSize 设置为 PAGE_SIZE_NONE；2. 分页查询单位 DO 列表；3. BeanUtils 批量转换为 RespVO 后 ExcelUtils.write 输出"产品单位.xls"。
