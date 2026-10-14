# 商品 SPU 接口 (ProductSpuController)

> 提供管理后台的商品 SPU（标准产品单元）管理能力，涵盖商品创建、更新、上下架、删除（回收站机制）、明细/列表/分页查询、Tab 数量统计与 Excel 导出，并在保存时级联维护 SKU 与 SPU 冗余统计字段。

## 接口路径前缀

/product/spu  (Controller: ProductSpuController)

## 1. 商品创建与维护

### 1.1 创建商品 SPU

- **路径**: POST /product/spu/create
- **权限**: product:spu:create
- **说明**: 新增商品 SPU 及其 SKU 列表，新商品默认为上架状态。

**请求参数 (ProductSpuSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 否 | - | 商品编号（创建时不传） |
| name | String | 是 | @NotEmpty | 商品名称 |
| keyword | String | 是 | @NotEmpty | 关键字 |
| introduction | String | 是 | @NotEmpty | 商品简介 |
| description | String | 是 | @NotEmpty | 商品详情 |
| categoryId | Long | 是 | @NotNull | 商品分类编号（必须为二级及以下分类） |
| brandId | Long | 是 | @NotNull | 商品品牌编号 |
| picUrl | String | 是 | @NotEmpty | 商品封面图 |
| sliderPicUrls | List&lt;String&gt; | 否 | - | 商品轮播图 |
| sort | Integer | 是 | @NotNull | 排序字段 |
| specType | Boolean | 是 | @NotNull | 规格类型（true 多规格 / false 单规格） |
| deliveryTypes | List&lt;Integer&gt; | 是 | @NotEmpty | 配送方式数组 |
| deliveryTemplateId | Long | 否 | - | 物流配置模板编号 |
| giveIntegral | Integer | 是 | @NotNull | 赠送积分 |
| subCommissionType | Boolean | 是 | @NotNull | 分销类型 |
| virtualSalesCount | Integer | 否 | - | 虚拟销量 |
| salesCount | Integer | 否 | - | 商品销量（保存时按 SKU 重新统计） |
| browseCount | Integer | 否 | - | 浏览量（保存时按 SKU 重新统计） |
| skus | List&lt;ProductSkuSaveReqVO&gt; | 否 | @Valid（级联校验） | SKU 数组 |

**子对象 ProductSkuSaveReqVO**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| name | String | 是 | @NotEmpty | 商品 SKU 名字 |
| price | Integer | 是 | @NotNull、@Min(0) | 销售价格，单位：分 |
| marketPrice | Integer | 否 | @Min(0) | 市场价 |
| costPrice | Integer | 否 | @Min(0) | 成本价 |
| barCode | String | 否 | - | 条形码 |
| picUrl | String | 是 | @NotNull | 图片地址 |
| stock | Integer | 是 | @NotNull | 库存 |
| weight | Double | 否 | - | 商品重量，单位：kg |
| volume | Double | 否 | - | 商品体积，单位：m³ |
| firstBrokeragePrice | Integer | 否 | @Min(0) | 一级分销的佣金，单位：分 |
| secondBrokeragePrice | Integer | 否 | @Min(0) | 二级分销的佣金，单位：分 |
| properties | List&lt;Property&gt; | 否 | - | 属性数组（propertyId/propertyName/valueId/valueName） |

**响应**: CommonResult&lt;Long&gt;（新创建的商品 SPU 编号）

**业务逻辑**:
1. 校验商品分类合法（`categoryService.validateCategory`），并要求分类层级必须为二级（CATEGORY_LEVEL）及以下，否则抛分类层级错误。
2. 校验品牌存在且未被禁用（`brandService.validateProductBrand`）。
3. 校验 SKU 列表（`productSkuService.validateSkuList`）：SKU 不能为空；单规格自动补充默认属性（默认属性项/属性值）；多规格依次校验属性项存在、单个 SKU 内属性不重复、每个 SKU 属性数量一致、SKU 之间属性组合不重复。
4. VO 转 `ProductSpuDO` 后基于 SKU 初始化冗余字段：price/marketPrice/costPrice 取所有 SKU 最低值，stock 取所有 SKU 合计；status 为空时默认上架，销量、浏览量默认 0。
5. 插入 SPU，随后批量插入关联 SKU（`createSkuList`，初始销量 0），整体事务回滚，返回 SPU 编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_005_001 | 商品分类不正确，原因：必须使用第二级的商品分类及以下 |
| 1_008_001_000 | 商品分类不存在 |
| 1_008_001_004 | 商品分类({})已禁用，无法使用 |
| 1_008_002_000 | 品牌不存在 |
| 1_008_002_001 | 品牌已禁用 |
| 1_008_006_000 | 商品 SKU 不存在（SKU 列表为空时同样抛出） |
| 1_008_006_005 | 多规格商品必须从规格列表选择属性组合，SKU 属性不能为空 |
| 1_008_003_000 | 属性项不存在 |
| 1_008_006_001 | 商品 SKU 的属性组合存在重复 |
| 1_008_006_002 | 一个 SPU 下的每个 SKU，其属性项必须一致 |
| 1_008_006_003 | 一个 SPU 下的每个 SKU，必须不重复 |

### 1.2 更新商品 SPU

- **路径**: PUT /product/spu/update
- **权限**: product:spu:update
- **说明**: 更新商品 SPU 基础信息，并按属性组合对账式更新其 SKU 列表。

**请求参数 (ProductSpuSaveReqVO)**: 与 1.1 创建接口相同（id 必传，用于定位更新的 SPU）。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验 SPU 存在（不存在抛 `SPU_NOT_EXISTS`）。
2. 校验商品分类与品牌合法性（同创建接口的 1、2 步）。
3. 校验 SKU 列表合法性（同创建接口第 3 步）。
4. 更新 SPU：转换 VO 后强制保留原 status（不允许通过更新接口变更状态），并基于新 SKU 重新初始化 price/marketPrice/costPrice/stock 冗余字段。
5. 批量更新 SKU（`updateSkuList`）：以"属性组合 key"与已有 SKU 对账，已存在的更新、不存在的新插入、数据库中多余的删除，整体事务回滚。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_005_001 | 商品分类不正确，原因：必须使用第二级的商品分类及以下 |
| 1_008_001_000 | 商品分类不存在 |
| 1_008_001_004 | 商品分类({})已禁用，无法使用 |
| 1_008_002_000 | 品牌不存在 |
| 1_008_002_001 | 品牌已禁用 |
| 1_008_006_000 | 商品 SKU 不存在（SKU 列表为空时同样抛出） |
| 1_008_006_005 | 多规格商品必须从规格列表选择属性组合，SKU 属性不能为空 |
| 1_008_003_000 | 属性项不存在 |
| 1_008_006_001 | 商品 SKU 的属性组合存在重复 |
| 1_008_006_002 | 一个 SPU 下的每个 SKU，其属性项必须一致 |
| 1_008_006_003 | 一个 SPU 下的每个 SKU，必须不重复 |

### 1.3 更新商品 SPU 状态

- **路径**: PUT /product/spu/update-status
- **权限**: product:spu:update
- **说明**: 上架/下架/移入回收站商品，状态取值 -1 回收站、0 下架、1 上架。

**请求参数 (ProductSpuUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @NotNull | 商品编号 |
| status | Integer | 是 | @NotNull、@InEnum(ProductSpuStatusEnum) | 商品状态（-1 回收站 / 0 下架 / 1 上架） |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验 SPU 存在（不存在抛 `SPU_NOT_EXISTS`）。
2. 将 SPU 状态更新为请求中的 status 并持久化。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_008_005_000 | 商品 SPU 不存在 |

### 1.4 删除商品 SPU

- **路径**: DELETE /product/spu/delete
- **权限**: product:spu:delete
- **说明**: 删除商品，仅允许删除处于回收站状态的商品。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @Parameter(required = true) | 商品编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验 SPU 存在（不存在抛 `SPU_NOT_EXISTS`）。
2. 校验商品状态处于回收站（`RECYCLE = -1`），否则抛 `SPU_NOT_RECYCLE`，即必须先移入回收站才能删除。
3. 删除 SPU 记录，并级联删除该 SPU 关联的全部 SKU（`deleteSkuBySpuId`），整体事务回滚。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_008_005_000 | 商品 SPU 不存在 |
| 1_008_005_004 | 商品 SPU 不处于回收站状态 |

## 2. 商品查询

### 2.1 获得商品 SPU 明细

- **路径**: GET /product/spu/get-detail
- **权限**: product:spu:query
- **说明**: 按编号获取商品 SPU 详情，包含其下全部 SKU。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @Parameter(required = true) | 商品编号 |

**响应**: CommonResult&lt;ProductSpuRespVO&gt;（SPU 不存在时返回 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 商品 SPU 编号 |
| name | String | 商品名称 |
| keyword | String | 关键字 |
| introduction | String | 商品简介 |
| description | String | 商品详情 |
| categoryId | Long | 商品分类编号 |
| brandId | Long | 商品品牌编号 |
| picUrl | String | 商品封面图 |
| sliderPicUrls | List&lt;String&gt; | 商品轮播图 |
| sort | Integer | 排序字段 |
| status | Integer | 商品状态（-1 回收站 / 0 下架 / 1 上架） |
| createTime | LocalDateTime | 商品创建时间 |
| specType | Boolean | 规格类型 |
| price | Integer | 商品价格（SKU 最低价），单位：分 |
| marketPrice | Integer | 市场价（SKU 最低），单位：分 |
| costPrice | Integer | 成本价（SKU 最低），单位：分 |
| stock | Integer | 商品库存（SKU 合计） |
| skus | List&lt;ProductSkuRespVO&gt; | SKU 数组（id/name/price/marketPrice/costPrice/barCode/picUrl/stock/weight/volume/firstBrokeragePrice/secondBrokeragePrice/properties） |
| deliveryTypes | List&lt;Integer&gt; | 配送方式数组 |
| deliveryTemplateId | Long | 物流配置模板编号 |
| giveIntegral | Integer | 赠送积分 |
| subCommissionType | Boolean | 分销类型 |
| salesCount | Integer | 商品销量 |
| virtualSalesCount | Integer | 虚拟销量 |
| browseCount | Integer | 浏览量 |

**业务逻辑**:
1. 按编号查询 SPU（`getSpu`），不存在时直接返回 null。
2. 查询该 SPU 下的全部 SKU 列表。
3. 通过 `ProductSpuConvert.convert(spu, skus)` 组装为含 skus 的 `ProductSpuRespVO`。

### 2.2 获得商品 SPU 精简列表

- **路径**: GET /product/spu/list-all-simple
- **权限**: product:spu:query
- **说明**: 获取全部上架状态的 SPU 精简信息（用于下拉选择等场景）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ProductSpuSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 |
| name | String | 商品名称 |
| price | Integer | 商品价格，单位：分 |
| marketPrice | Integer | 商品市场价，单位：分 |
| costPrice | Integer | 商品成本价，单位：分 |
| stock | Integer | 商品库存 |
| salesCount | Integer | 商品销量 |
| virtualSalesCount | Integer | 商品虚拟销量 |
| browseCount | Integer | 商品浏览量 |

**业务逻辑**:
1. 查询所有状态为上架（`ENABLE = 1`）的 SPU 列表。
2. 按 sort 字段降序排序。
3. 转换为 `ProductSpuSimpleRespVO` 列表返回。

### 2.3 获得商品 SPU 详情列表

- **路径**: GET /product/spu/list
- **权限**: product:spu:query
- **说明**: 按编号集合批量获取 SPU 详情（含 SKU），常用于店铺装修等已选商品回显。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| spuIds | Collection&lt;Long&gt; | 是 | @Parameter(required = true) | spu 编号列表 |

**响应**: CommonResult&lt;List&lt;ProductSpuRespVO&gt;&gt;（字段同 2.1，且严格按传入 spuIds 的顺序返回）

**业务逻辑**:
1. 按 spuIds 批量查询 SPU 列表（`getSpuList`），结果按传入 ids 的顺序排列。
2. 批量查询这些 SPU 下的全部 SKU（`getSkuListBySpuId(Collection)`）。
3. 通过 `ProductSpuConvert.convertForSpuDetailRespListVO` 组装为 `ProductSpuRespVO` 列表。

### 2.4 获得商品 SPU 分页

- **路径**: GET /product/spu/page
- **权限**: product:spu:query
- **说明**: 分页查询商品列表，支持按 Tab（出售中/仓库中/已售空/警戒库存/回收站）与名称、分类、创建时间筛选。

**请求参数 (ProductSpuPageReqVO，继承 PageParam 分页参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| pageNo | Integer | 否 | PageParam 默认值 1 | 页码 |
| pageSize | Integer | 否 | PageParam 默认值 10 | 每页条数 |
| name | String | 否 | - | 商品名称（模糊匹配） |
| tabType | Integer | 否 | - | Tab 类型：0 出售中、1 仓库中、2 已售空、3 警戒库存、4 回收站 |
| categoryId | Long | 否 | - | 商品分类编号（精确匹配） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ProductSpuRespVO&gt;&gt;（list 字段元素结构同 2.1 的 ProductSpuRespVO，不含 skus）

**业务逻辑**:
1. 构建查询条件：name 模糊匹配、categoryId 精确匹配、createTime 区间过滤。
2. 按 tabType 追加 Tab 条件：0 出售中=status=1；1 仓库中=status=0（下架）；2 已售空=stock=0；3 警戒库存=stock≤系统警戒值且排除回收站商品；4 回收站=status=-1。
3. 按 sort 降序、id 降序排序后执行分页查询。
4. `BeanUtils.toBean` 转换为 `ProductSpuRespVO` 分页结果返回。

### 2.5 获得商品 SPU 分页 Tab 数量

- **路径**: GET /product/spu/get-count
- **权限**: product:spu:query
- **说明**: 一次性统计 5 个 Tab 的商品数量，支持与分页一致的 name/categoryId/createTime 筛选。

**请求参数 (ProductSpuPageReqVO)**: 同 2.4 分页请求（tabType 不参与本次筛选，筛选条件 name/categoryId/createTime 生效）。

**响应**: CommonResult&lt;Map&lt;Integer, Long&gt;&gt;（key 为 tabType：0 出售中、1 仓库中、2 已售空、3 警戒库存、4 回收站；value 为数量）

**业务逻辑**:
1. 以请求中的 name/categoryId/createTime 作为公共筛选条件。
2. 对 5 个 tab（FOR_SALE/IN_WAREHOUSE/SOLD_OUT/ALERT_STOCK/RECYCLE_BIN）分别调用 `selectCountByTab`，各自叠加对应的状态/库存条件后 count。
3. 汇总为按 tabType 有序的 Map 返回。

## 3. 导出

### 3.1 导出商品 Excel

- **路径**: GET /product/spu/export-excel
- **权限**: product:spu:export（操作日志类型为导出 EXPORT）
- **说明**: 按分页筛选条件导出商品列表 Excel（不分页，导出全部符合条件数据）。

**请求参数 (ProductSpuPageReqVO)**: 同 2.4 分页请求（pageSize 在后端被强制设为 PAGE_SIZE_NONE 以查询全部）。

**响应**: 二进制文件流 `商品列表.xls`（Excel 下载，非 CommonResult）

**业务逻辑**:
1. 将请求的 pageSize 强制设置为 `PAGE_SIZE_NONE`，即不分页查询全部数据。
2. 复用分页查询（含 Tab 条件与 name/categoryId/createTime 筛选）获取 SPU 列表。
3. 转换为 `ProductSpuRespVO` 后经 `ExcelUtils.write` 输出；导出列由 @ExcelProperty 注解决定，价格字段经 `MoneyConvert` 分转元，商品状态经 `DictConvert` 按字典 PRODUCT_SPU_STATUS 转换为文本。
