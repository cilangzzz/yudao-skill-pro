# 商品统计接口 (ProductStatisticsController)

> 提供商城商品维度的统计分析能力：基于每日离线统计表 `product_statistics`，支持时间范围的指标汇总对比、日期维度明细查询与导出、商品维度排行榜分页查询。

## 接口路径前缀

/statistics/product  (Controller: ProductStatisticsController)

## 1. 商品统计分析

### 1.1 获得商品统计分析

- **路径**: GET /statistics/product/analyse
- **权限**: statistics:product:query
- **说明**: 统计指定时间段内的商品核心指标（浏览量、访客量、收藏、加购、下单、支付、退款等），并自动取等长度的上一个时间段作为对照，返回数据对比结果。

**请求参数 (ProductStatisticsReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 统计时间范围，[开始时间, 结束时间] |

**响应**: CommonResult&lt;DataComparisonRespVO&lt;ProductStatisticsRespVO&gt;&gt;

DataComparisonRespVO 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| value | ProductStatisticsRespVO | 当前时间段统计数据 |
| reference | ProductStatisticsRespVO | 参照（上一等长时段）统计数据 |

**业务逻辑**: 1. 取 `times[0]`、`times[1]` 作为当前统计时间范围的起止时间。 2. 调用 Mapper 按时间范围汇总查询当前时段统计数据（对浏览量、访客量、收藏数、加购数、下单件数、支付件数、支付金额、退款件数、退款金额求 SUM，对访客支付转化率求 AVG）。 3. 用 `beginTime - (endTime - beginTime)` 计算出与当前时段等长度的上一时段作为参照时间范围。 4. 以参照时间范围再执行一次相同的汇总查询，得到对照数据。 5. 将当前数据与对照数据封装为 `DataComparisonRespVO(value, reference)` 返回。

### 1.2 获得商品统计明细（日期维度）

- **路径**: GET /statistics/product/list
- **权限**: statistics:product:query
- **说明**: 按统计日期分组，返回时间范围内每一天的商品统计汇总列表（用于趋势图表展示）。

**请求参数 (ProductStatisticsReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 统计时间范围，[开始时间, 结束时间] |

**响应**: CommonResult&lt;List&lt;ProductStatisticsRespVO&gt;&gt;

每个元素为 ProductStatisticsRespVO：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号，主键自增 |
| time | LocalDate | 统计日期（yyyy-MM-dd） |
| spuId | Long | 商品 SPU 编号 |
| name | String | 商品名称 |
| picUrl | String | 商品封面图 |
| browseCount | Integer | 浏览量 |
| browseUserCount | Integer | 访客量 |
| favoriteCount | Integer | 收藏数量 |
| cartCount | Integer | 加购数量 |
| orderCount | Integer | 下单件数 |
| orderPayCount | Integer | 支付件数 |
| orderPayPrice | Integer | 支付金额，单位：分 |
| afterSaleCount | Integer | 退款件数 |
| afterSaleRefundPrice | Integer | 退款金额，单位：分 |
| browseConvertPercent | Integer | 访客支付转化率（百分比） |

**业务逻辑**: 1. 按 `times` 时间范围过滤统计记录（`betweenIfPresent`，时间为空则不过滤）。 2. 按统计日期 `time` 分组（GROUP BY time）。 3. 对各业务指标列求 SUM、对访客支付转化率求 AVG，得到每个日期一条的汇总记录。 4. 将 DO 列表转换为 ProductStatisticsRespVO 列表返回（日期维度下 name、picUrl、spuId 等商品字段为空）。

### 1.3 导出商品统计明细 Excel（日期维度）

- **路径**: GET /statistics/product/export-excel
- **权限**: statistics:product:export
- **说明**: 与日期维度明细查询同口径，将结果以 Excel 文件（`商品状况.xls`）形式导出下载。

**请求参数 (ProductStatisticsReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 统计时间范围，[开始时间, 结束时间] |

**响应**: 无 CommonResult 包装，直接向 HttpServletResponse 写入 Excel 文件流（文件名「商品状况.xls」，导出列见 1.2 响应字段表中带 @ExcelProperty 注解的字段：统计日期、商品SPU编号、商品名称、商品封面图、浏览量、访客量、收藏数量、加购数量、下单件数、支付件数、支付金额、退款件数、退款金额）。

**业务逻辑**: 1. 调用 Mapper 按时间范围、按统计日期分组汇总查询（与 1.2 相同逻辑）得到统计记录列表。 2. 将 DO 列表转换为 ProductStatisticsRespVO 列表。 3. 通过 ExcelUtils 将 VO 列表按 `@ExcelProperty` 注解的列写入响应流，输出文件名为「商品状况.xls」。

### 1.4 获得商品统计排行榜分页（商品维度）

- **路径**: GET /statistics/product/rank-page
- **权限**: statistics:product:query
- **说明**: 按商品（SPU）维度分组汇总统计指标，支持自定义排序字段，返回商品统计排行榜分页数据，并回填商品名称与封面图。

**请求参数 (ProductStatisticsReqVO + SortablePageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 统计时间范围，[开始时间, 结束时间] |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| sortingFields | List&lt;SortingField&gt; | 否 | 无 | 排序字段列表（field 为排序列，asc/desc 方向），未指定时默认按浏览量 browse_count 倒序 |

**响应**: CommonResult&lt;PageResult&lt;ProductStatisticsRespVO&gt;&gt;

PageResult.list 中每个元素为 ProductStatisticsRespVO（字段同 1.2），其中 name（商品名称）、picUrl（商品封面图）由商品 SPU 信息回填。

**业务逻辑**: 1. 通过 `PageUtils.buildDefaultSortingField` 设置默认排序字段为浏览量（browseCount）倒序（若未显式传入排序字段）。 2. 调用 Mapper 按时间范围过滤，并按 `spuId` 分组（GROUP BY spu_id）分页查询，对各指标列求 SUM、对转化率求 AVG，得到商品维度的排行榜分页结果。 3. 提取分页结果中所有 SPU 编号，调用 `ProductSpuApi.getSpuList` 批量获取商品信息并转为 id 到 SPU 的映射。 4. 遍历分页记录，从映射中按 spuId 找到对应商品，回填 `name`（商品名称）与 `picUrl`（商品封面图）到响应 VO。 5. 将分页结果转换为 `PageResult<ProductStatisticsRespVO>` 返回。

## 补充说明

- **数据来源**: 本域接口只读 `product_statistics` 统计表，不实时计算。数据由 `ProductStatisticsService#statisticsProduct(days)` 定时任务离线生成：按天回溯，逐日检查该日是否已有统计数据（已存在则跳过并提示需先删除），然后分页（每页 100 条）聚合交易、浏览、收藏、售后等来源数据，计算访客支付转化率（`100 * 支付件数 / 访客量`）后批量插入。
- **错误码**: 商品统计模块未定义专属错误码（statistics 模块无 ErrorCodeConstants）；相关商品 SPU 错误码位于 product 模块 1-008-005-000 段（如 1_008_005_000 商品 SPU 不存在），但本域接口不直接抛出这些错误码。
