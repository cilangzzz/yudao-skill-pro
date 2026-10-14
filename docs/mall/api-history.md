# 商品浏览记录接口 (ProductBrowseHistoryController)

> 管理后台查询会员的商品浏览记录，分页展示并联动商品 SPU 的名称、封面、价格等实时信息。

## 接口路径前缀
/product/browse-history  (Controller: ProductBrowseHistoryController)

## 1. 浏览记录查询

### 1.1 获得商品浏览记录分页

- **路径**: GET /product/browse-history/page
- **权限**: product:browse-history:query
- **说明**: 分页查询会员的商品浏览记录，并补充每条记录对应商品 SPU 的名称、封面图、单价、销量、库存信息。

**请求参数 (ProductBrowseHistoryPageReqVO)**: 继承 SortablePageParam（含 pageNo/pageSize/sortingFields）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，最大 200（继承 PageParam，默认 10） |
| sortingFields | List&lt;SortingField&gt; | 否 | - | 排序字段（继承 SortablePageParam） |
| userId | Long | 否 | - | 用户编号 |
| userDeleted | Boolean | 否 | - | 用户是否删除 |
| spuId | Long | 否 | - | 商品 SPU 编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ProductBrowseHistoryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| spuId | Long | 商品 SPU 编号 |
| spuName | String | 商品 SPU 名称 |
| picUrl | String | 商品封面图 |
| price | Integer | 商品单价 |
| salesCount | Integer | 商品销量 |
| stock | Integer | 库存 |

**业务逻辑**: 1. 按 userId、userDeleted、spuId 等值条件与 createTime 区间条件过滤，按 id 倒序分页查询浏览记录（ProductBrowseHistoryMapper.selectPage）。 2. 若分页结果为空，直接返回空 PageResult。 3. 收集结果中的 spuId 集合，通过 ProductSpuService.getSpuMap 批量查询商品 SPU 信息。 4. 将浏览记录转换为 ProductBrowseHistoryRespVO，并回填对应 SPU 的名称（spuName）、封面图（picUrl）、单价（price）、销量（salesCount）、库存（stock）。

**错误码**: 本域错误码暂无（Service 层不抛出业务异常）
