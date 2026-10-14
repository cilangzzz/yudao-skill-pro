# 数据统计接口 (CrmStatistics*Controller)

> 提供 CRM 数据统计中心的全部只读分析接口：员工客户分析（客户总量/跟进/公海/成交周期/客户转化率）、销售漏斗分析、员工业绩统计与业绩目标完成情况、客户画像（地区/行业/级别/来源）、产品销售分析、员工业绩排行榜。统计范围均按「部门（含子部门）或指定用户」+「时间范围」聚合。

## 接口路径前缀

- /crm/statistics-customer  (Controller: CrmStatisticsCustomerController) —— 员工客户统计
- /crm/statistics-funnel  (Controller: CrmStatisticsFunnelController) —— 销售漏斗
- /crm/statistics-performance  (Controller: CrmStatisticsPerformanceController) —— 员工业绩
- /crm/statistics-performance-target  (Controller: CrmStatisticsPerformanceTargetController) —— 业绩目标
- /crm/statistics-portrait  (Controller: CrmStatisticsPortraitController) —— 客户画像
- /crm/statistics-product  (Controller: CrmStatisticsProductController) —— 产品统计
- /crm/statistics-rank  (Controller: CrmStatisticsRankController) —— 排行榜

> 本域全部为只读统计接口（仅 GET），Service 层不抛业务错误码，参数校验失败由框架统一返回 400；仅在关联查询商机/业绩目标配置/产品分类时可能涉及相关域的错误码，已在对应分组列出。

## 1. 员工客户统计（CrmStatisticsCustomerController）

### 1.0 通用请求参数 (CrmStatisticsCustomerReqVO)

本控制器 12 个端点共用同一请求 VO：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userId | Long | 否 | - | 负责人用户编号（为空则统计该部门及子部门下全部用户） |
| userIds | List&lt;Long&gt; | 否 | hidden | 负责人用户编号集合（后端根据 deptId/userId 回填，前端无需传递） |
| interval | Integer | 是 | @InEnum(DateIntervalEnum) | 时间间隔类型：0 小时 / 1 天 / 2 周 / 3 月 / 4 季度 / 5 年 |
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@Size(min=2, max=2) | 时间范围（起止时间） |

> Service 通用前置逻辑（下述各端点「业务逻辑」第 1 步不再重复）：确定统计用户集合 —— 若 userId 非空则只统计该用户；否则取该部门及其全部子部门下的用户编号集合，用户集合为空时直接返回空列表。

### 1.1 获取客户总量分析(按日期)

- **路径**: GET /crm/statistics-customer/get-customer-summary-by-date
- **权限**: crm:statistics-customer:query
- **说明**: 按时间间隔统计新建客户数与成交客户数的时间趋势。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerSummaryByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴（按 interval 格式化的区间） |
| customerCreateCount | Integer | 新建客户数 |
| customerDealCount | Integer | 成交客户数 |

**业务逻辑**:
1. 确定统计用户编号集合（见 1.0 通用逻辑），为空返回空列表。
2. 分别按日期分组查询新建客户数、成交客户数两组分项统计数据。
3. 根据 times 与 interval 生成日期区间列表，将分项数据逐区间求和合并。
4. 格式化时间轴并返回趋势列表。

### 1.2 获取客户总量分析(按用户)

- **路径**: GET /crm/statistics-customer/get-customer-summary-by-user
- **权限**: crm:statistics-customer:query
- **说明**: 按负责人统计新建客户数、成交客户数、合同总金额与回款金额。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerSummaryByUserRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| ownerUserId | Long | 负责人编号（继承自 CrmStatisticsCustomerByUserBaseRespVO） |
| ownerUserName | String | 负责人昵称（继承自 CrmStatisticsCustomerByUserBaseRespVO） |
| customerCreateCount | Integer | 新建客户数 |
| customerDealCount | Integer | 成交客户数 |
| contractPrice | BigDecimal | 合同总金额 |
| receivablePrice | BigDecimal | 回款金额 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 分别按用户分组查询新建客户数、成交客户数、合同金额、回款金额四组分项数据。
3. 逐个用户将四组分项数据求和，组装为汇总 VO。
4. 批量拼接负责人昵称后返回。

### 1.3 获取客户跟进次数分析(按日期)

- **路径**: GET /crm/statistics-customer/get-follow-up-summary-by-date
- **权限**: crm:statistics-customer:query
- **说明**: 按时间间隔统计跟进次数与跟进客户数的时间趋势。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsFollowUpSummaryByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴 |
| followUpRecordCount | Integer | 跟进次数 |
| followUpCustomerCount | Integer | 跟进客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 分别按日期分组查询跟进次数、跟进客户数两组分项数据。
3. 按日期区间合并求和并格式化时间轴返回。

### 1.4 获取客户跟进次数分析(按用户)

- **路径**: GET /crm/statistics-customer/get-follow-up-summary-by-user
- **权限**: crm:statistics-customer:query
- **说明**: 按负责人统计跟进次数与跟进客户数。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsFollowUpSummaryByUserRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人昵称 |
| followUpRecordCount | Integer | 跟进次数 |
| followUpCustomerCount | Integer | 跟进客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 分别按用户分组查询跟进次数、跟进客户数两组分项数据。
3. 逐个用户求和组装汇总 VO，并批量拼接负责人昵称。

### 1.5 获取客户跟进次数分析(按类型)

- **路径**: GET /crm/statistics-customer/get-follow-up-summary-by-type
- **权限**: crm:statistics-customer:query
- **说明**: 按跟进方式（类型）统计跟进次数分布。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsFollowUpSummaryByTypeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| followUpType | Integer | 跟进类型 |
| followUpRecordCount | Integer | 跟进次数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 直接按跟进类型分组查询跟进次数并返回。

### 1.6 获取客户的首次合同、回款信息列表

- **路径**: GET /crm/statistics-customer/get-contract-summary
- **权限**: crm:statistics-customer:query
- **说明**: 查询客户的合同、回款明细列表，用于【客户转化率】页面。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerContractSummaryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| customerName | String | 客户名称 |
| contractName | String | 合同名称 |
| totalPrice | BigDecimal | 合同总金额 |
| receivablePrice | BigDecimal | 回款金额 |
| industryId | Integer | 客户行业编号 |
| source | Integer | 客户来源编号 |
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人 |
| creator | String | 创建人编号 |
| creatorUserName | String | 创建人 |
| createTime | LocalDateTime | 创建时间 |
| orderDate | LocalDateTime | 下单日期 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 查询用户范围内客户的合同、回款汇总明细。
3. 批量查询用户信息，拼接负责人昵称（ownerUserName）与创建人昵称（creatorUserName）。

### 1.7 获取公海客户分析(按日期)

- **路径**: GET /crm/statistics-customer/get-pool-summary-by-date
- **权限**: crm:statistics-customer:query
- **说明**: 按时间间隔统计进入公海客户数与公海领取客户数的趋势。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsPoolSummaryByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴 |
| customerPutCount | Integer | 进入公海客户数 |
| customerTakeCount | Integer | 公海领取客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 通过 CrmOwnerRecordService 分别按日期查询进入公海、公海领取两组客户数分项数据。
3. 按日期区间合并求和并格式化时间轴返回。

### 1.8 获取公海客户分析(按用户)

- **路径**: GET /crm/statistics-customer/get-pool-summary-by-user
- **权限**: crm:statistics-customer:query
- **说明**: 按负责人统计进入公海客户数与公海领取客户数。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsPoolSummaryByUserRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人昵称 |
| customerPutCount | Integer | 进入公海客户数 |
| customerTakeCount | Integer | 公海领取客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 通过 CrmOwnerRecordService 分别按用户查询进入公海、公海领取客户数分项数据。
3. 逐个用户求和组装汇总 VO，并批量拼接负责人昵称。

### 1.9 获取客户成交周期(按日期)

- **路径**: GET /crm/statistics-customer/get-customer-deal-cycle-by-date
- **权限**: crm:statistics-customer:query
- **说明**: 按时间间隔统计客户成交周期（从创建到成交的天数）的趋势。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerDealCycleByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴 |
| customerDealCycle | Double | 成交周期 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按日期分组查询客户成交周期分项数据。
3. 按日期区间合并求和并格式化时间轴返回。

### 1.10 获取客户成交周期(按用户)

- **路径**: GET /crm/statistics-customer/get-customer-deal-cycle-by-user
- **权限**: crm:statistics-customer:query
- **说明**: 按负责人统计成交周期与成交客户数。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerDealCycleByUserRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人昵称 |
| customerDealCycle | Double | 成交周期 |
| customerDealCount | Integer | 成交客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 分别按用户分组查询成交周期、成交客户数两组分项数据。
3. 逐个用户求和组装汇总 VO，并批量拼接负责人昵称。

### 1.11 获取客户成交周期(按区域)

- **路径**: GET /crm/statistics-customer/get-customer-deal-cycle-by-area
- **权限**: crm:statistics-customer:query
- **说明**: 按省份统计成交周期与成交客户数。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerDealCycleByAreaRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| areaId | Integer | 省份编号（@JsonIgnore，不序列化到前端） |
| areaName | String | 省份名称 |
| customerDealCycle | Double | 成交周期 |
| customerDealCount | Integer | 成交客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按客户地区编号（areaId）分组查询成交周期统计数据，为空返回空列表。
3. 通过 AreaUtils 将客户的地区编号向上归一到省级，并拼接省份名称。

### 1.12 获取客户成交周期(按产品)

- **路径**: GET /crm/statistics-customer/get-customer-deal-cycle-by-product
- **权限**: crm:statistics-customer:query
- **说明**: 按产品统计成交周期与成交客户数。

**请求参数**: CrmStatisticsCustomerReqVO（见 1.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsCustomerDealCycleByProductRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| productName | String | 产品名称 |
| customerDealCycle | Double | 成交周期 |
| customerDealCount | Integer | 成交客户数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 直接按产品分组查询成交周期统计数据并返回。

## 2. 销售漏斗（CrmStatisticsFunnelController）

### 2.0 通用请求参数 (CrmStatisticsFunnelReqVO)

本控制器 6 个端点共用同一请求 VO（继承 PageParam，第 2.6 端点使用分页参数）：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userId | Long | 否 | - | 负责人用户编号（为空则统计该部门及子部门下全部用户） |
| statusTypeId | Long | 否 | - | 商机状态组编号 |
| userIds | List&lt;Long&gt; | 否 | hidden | 负责人用户编号集合（后端回填，前端无需传递） |
| interval | Integer | 是 | @InEnum(DateIntervalEnum) | 时间间隔类型：0 小时 / 1 天 / 2 周 / 3 月 / 4 季度 / 5 年 |
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@Size(min=2, max=2) | 时间范围 |
| pageNo | Integer | 是（有默认值 1） | @NotNull、@Min(1) | 页码（继承 PageParam，仅 2.6 使用） |
| pageSize | Integer | 是（有默认值 10） | @NotNull、@Min(1)、@Max(200) | 每页条数（继承 PageParam，仅 2.6 使用） |

> Service 通用前置逻辑与第 1 节相同：userId 非空取该用户，否则取部门及子部门全部用户；用户集合为空返回空结果。

### 2.1 获取销售漏斗统计数据

- **路径**: GET /crm/statistics-funnel/get-funnel-summary
- **权限**: crm:statistics-funnel:query
- **说明**: 统计客户数、商机数、赢单数，用于【销售漏斗】页面的【销售漏斗分析】。

**请求参数**: CrmStatisticsFunnelReqVO（见 2.0）

**响应**: CommonResult&lt;CrmStatisticFunnelSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| customerCount | Long | 客户数 |
| businessCount | Long | 商机数 |
| businessWinCount | Long | 赢单数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回 null。
2. 分别查询时间段内客户总数、商机总数（不限结束状态）、赢单商机数（结束状态为赢单）。
3. 组装为漏斗汇总 VO 返回。

### 2.2 获取商机结束状态统计

- **路径**: GET /crm/statistics-funnel/get-business-summary-by-end-status
- **权限**: crm:statistics-funnel:query
- **说明**: 按结束状态（赢单/输单/放弃）统计商机数量与总金额，用于【销售漏斗】页面。

**请求参数**: CrmStatisticsFunnelReqVO（见 2.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsBusinessSummaryByEndStatusRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| endStatus | Integer | 结束状态 |
| businessCount | Long | 商机数 |
| totalPrice | BigDecimal | 商机总金额，单位：元 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按商机结束状态分组统计商机数量与总金额并返回。

### 2.3 获取商机阶段统计

- **路径**: GET /crm/statistics-funnel/get-business-summary-by-status
- **权限**: crm:statistics-funnel:query
- **说明**: 按商机所处阶段统计商机数量与总金额，用于【销售漏斗】页面。

**请求参数**: CrmStatisticsFunnelReqVO（见 2.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsBusinessSummaryByStatusRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| statusId | Long | 商机阶段编号 |
| statusName | String | 商机阶段名称 |
| statusPercent | Integer | 赢单率，百分比 |
| sort | Integer | 排序 |
| businessCount | Long | 商机数 |
| totalPrice | BigDecimal | 商机总金额，单位：元 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按商机阶段分组统计商机数量与总金额（含阶段名称、赢单率、排序）并返回。

### 2.4 获取新增商机分析(按日期)

- **路径**: GET /crm/statistics-funnel/get-business-summary-by-date
- **权限**: crm:statistics-funnel:query
- **说明**: 按时间间隔统计新增商机数量与商机金额的趋势，用于【销售漏斗】页面。

**请求参数**: CrmStatisticsFunnelReqVO（见 2.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsBusinessSummaryByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴 |
| businessCreateCount | Long | 新增商机数量 |
| totalPrice | BigDecimal | 新增商机金额 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按日期分组查询新增商机数量与金额分项数据。
3. 按 interval 生成日期区间，逐区间合并求和并格式化时间轴返回。

### 2.5 获取商机转化率分析(按日期)

- **路径**: GET /crm/statistics-funnel/get-business-inversion-rate-summary-by-date
- **权限**: crm:statistics-funnel:query
- **说明**: 按时间间隔统计商机数量与赢单商机数，用于计算转化率，用于【销售漏斗】页面。

**请求参数**: CrmStatisticsFunnelReqVO（见 2.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsBusinessInversionRateSummaryByDateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴 |
| businessCount | Long | 商机数量 |
| businessWinCount | Long | 赢单商机数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按日期分组查询商机数量与赢单商机数分项数据。
3. 按 interval 生成日期区间，逐区间合并求和并格式化时间轴返回。

### 2.6 获得商机分页(按日期)

- **路径**: GET /crm/statistics-funnel/get-business-page-by-date
- **权限**: crm:business:query
- **说明**: 分页返回时间段内新增商机明细（含产品列表等详情），用于【销售漏斗】页面的【新增商机分析】下钻。

**请求参数**: CrmStatisticsFunnelReqVO（见 2.0，含 pageNo/pageSize 分页参数）

**响应**: CommonResult&lt;PageResult&lt;CrmBusinessRespVO&gt;&gt; —— 字段同商机详情，此处列主要字段（完整定义见 [api-business.md](api-business.md)）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 商机编号 |
| name | String | 商机名称 |
| customerId / customerName | Long / String | 客户编号 / 名称 |
| followUpStatus | Boolean | 跟进状态 |
| contactLastTime / contactNextTime | LocalDateTime | 最后跟进时间 / 下次联系时间 |
| ownerUserId / ownerUserName / ownerUserDeptName | Long / String / String | 负责人编号 / 姓名 / 部门 |
| statusTypeId / statusTypeName | Long / String | 商机状态组编号 / 名称 |
| statusId / statusName | Long / String | 商机阶段编号 / 名称 |
| endStatus / endRemark | Integer / String | 结束状态 / 结束备注 |
| dealTime | LocalDateTime | 预计成交日期 |
| totalProductPrice / discountPercent / totalPrice | BigDecimal | 产品总金额 / 整单折扣 / 商机总金额 |
| remark | String | 备注 |
| creator / creatorName | String | 创建人编号 / 姓名 |
| createTime / updateTime | LocalDateTime | 创建 / 更新时间 |
| products | List&lt;Product&gt; | 商机产品列表（含 productId、productName、productNo、productUnit、productPrice、businessPrice、count、totalPrice） |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空分页。
2. 委托 CrmBusinessService 按时间范围与用户集合分页查询商机。
3. 复用 CrmBusinessController 的 buildBusinessDetailList 将商机 DO 转换为带产品明细的 RespVO。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在（关联商机域，查询明细相关） |

## 3. 员工业绩统计（CrmStatisticsPerformanceController）

### 3.0 通用请求参数 (CrmStatisticsPerformanceReqVO)

本控制器 4 个端点共用同一请求 VO：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userId | Long | 否 | - | 负责人用户编号（为空则统计该部门及子部门下全部用户） |
| userIds | List&lt;Long&gt; | 否 | - | 负责人用户编号集合（后端根据 deptId/userId 回填） |
| times | LocalDateTime[] | 是 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@NotEmpty | 时间范围（取起始时间的年份，按 1-12 月逐月统计） |

> Service 通用前置逻辑同前：userId 非空取该用户，否则取部门及子部门全部用户；用户集合为空返回空列表。3.1～3.3 三个端点为同一套统计模式，仅统计的 SQL 指标不同（合同数量 / 合同金额 / 回款金额），统计时会额外查询上一年同期的数据用于同比。

### 3.1 合同数量统计

- **路径**: GET /crm/statistics-performance/get-contract-count-performance
- **权限**: crm:statistics-performance:query
- **说明**: 按月统计签约合同数量，并给出上月、去年同期对比，用于【合同数量分析】页面。

**请求参数**: CrmStatisticsPerformanceReqVO（见 3.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsPerformanceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴（yyyyMM） |
| currentMonthCount | BigDecimal | 当月统计结果 |
| lastMonthCount | BigDecimal | 上月统计结果 |
| lastYearCount | BigDecimal | 去年同期统计结果 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 将查询起始时间前推一年，统计「今年 + 去年」两个年度的逐月合同数量。
3. 遍历查询年份的 1～12 月，逐月拼接当月、上月（1 月取上一年 12 月）、去年同期数据，缺失月份补 0。

### 3.2 合同金额统计

- **路径**: GET /crm/statistics-performance/get-contract-price-performance
- **权限**: crm:statistics-performance:query
- **说明**: 按月统计合同金额，并给出上月、去年同期对比。

**请求参数**: CrmStatisticsPerformanceReqVO（见 3.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsPerformanceRespVO&gt;&gt;（字段同 3.1）

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 将查询起始时间前推一年，统计两个年度的逐月合同金额。
3. 遍历 1～12 月拼接当月、上月、去年同期数据，缺失月份补 0。

### 3.3 回款金额统计

- **路径**: GET /crm/statistics-performance/get-receivable-price-performance
- **权限**: crm:statistics-performance:query
- **说明**: 按月统计回款金额，并给出上月、去年同期对比。

**请求参数**: CrmStatisticsPerformanceReqVO（见 3.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsPerformanceRespVO&gt;&gt;（字段同 3.1）

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 将查询起始时间前推一年，统计两个年度的逐月回款金额。
3. 遍历 1～12 月拼接当月、上月、去年同期数据，缺失月份补 0。

### 3.4 合同汇总表

- **路径**: GET /crm/statistics-performance/get-contract-summary
- **权限**: crm:statistics-performance:query
- **说明**: 按月汇总合同数量、合同金额、回款金额与未回款金额。

**请求参数**: CrmStatisticsPerformanceReqVO（见 3.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsPerformanceSummaryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| time | String | 时间轴（yyyyMM） |
| contractCount | Integer | 合同数量 |
| contractPrice | BigDecimal | 合同金额 |
| receivablePrice | BigDecimal | 回款金额 |
| unreceivedPrice | BigDecimal | 未回款金额 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按月分组统计合同数量、合同金额、回款金额、未回款金额。
3. 以查询起始时间的年份为基准，遍历 1～12 月逐月对齐数据，缺失月份补 0，保证全年 12 条记录。

## 4. 业绩目标统计（CrmStatisticsPerformanceTargetController）

### 4.1 获取业绩目标完成情况

- **路径**: GET /crm/statistics-performance-target/get-performance-target-summary
- **权限**: crm:statistics-performance-target:query
- **说明**: 按月统计业绩目标金额、实际完成金额与完成率，目标类型支持合同金额 / 回款金额。

**请求参数 (CrmStatisticsPerformanceTargetReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userId | Long | 否 | - | 负责人用户编号（为空则统计该部门及子部门下全部用户） |
| userIds | List&lt;Long&gt; | 否 | hidden | 负责人用户编号集合（后端回填） |
| year | Integer | 是 | @NotNull | 年份 |
| bizType | Integer | 是 | @NotNull、@InEnum(CrmPerformanceConfigBizTypeEnum) | 目标类型（如合同金额、回款金额） |

**响应**: CommonResult&lt;List&lt;CrmStatisticsPerformanceTargetRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| month | Integer | 月份（1～12） |
| targetPrice | BigDecimal | 目标金额 |
| currentPrice | BigDecimal | 完成金额 |
| completionRate | BigDecimal | 完成率（百分比，保留 2 位小数） |

**业务逻辑**:
1. 确定统计用户编号集合：userId 非空取该用户，否则取部门及子部门全部用户，为空返回空列表。
2. 查询目标配置：userId 非空时按「用户」维度取该用户当年的业绩目标配置，否则按「部门」维度取部门列表的配置。
3. 查询实际完成金额：bizType 为回款时按月统计回款金额，否则按月统计合同金额。
4. 遍历 1～12 月，从目标配置中取对应月份的目标金额（多配置求和，无配置补 0）。
5. 逐月计算完成金额与完成率（完成金额 / 目标金额 × 100，目标为 0 时完成率为 0），组装返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_011_000 | 业绩目标配置不存在（关联业绩目标配置域） |
| 1_020_011_001 | 该对象当前年份的业绩目标配置已存在（关联业绩目标配置域） |
| 1_020_011_002 | 目标对象类型不正确（关联业绩目标配置域） |

## 5. 客户画像（CrmStatisticsPortraitController）

### 5.0 通用请求参数 (CrmStatisticsPortraitReqVO)

本控制器 4 个端点共用同一请求 VO：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userId | Long | 否 | - | 负责人用户编号（为空则统计该部门及子部门下全部用户） |
| userIds | List&lt;Long&gt; | 否 | hidden | 负责人用户编号集合（后端回填，前端无需传递） |
| times | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@Size(min=2, max=2) | 时间范围 |

> Service 通用前置逻辑同前：userId 非空取该用户，否则取部门及子部门全部用户；用户集合为空返回空列表。4 个端点均为「按某一维度分组统计客户数与成交数」，仅分组维度不同。

### 5.1 获取客户地区统计数据

- **路径**: GET /crm/statistics-portrait/get-customer-area-summary
- **权限**: crm:statistics-portrait:query
- **说明**: 按省份统计客户数与成交数，用于【城市分布分析】页面。

**请求参数**: CrmStatisticsPortraitReqVO（见 5.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticCustomerAreaRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| areaId | Integer | 省份编号 |
| areaName | String | 省份名称 |
| customerCount | Integer | 客户个数 |
| dealCount | Integer | 成交个数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按客户地区编号分组统计客户数与成交数，为空返回空列表。
3. 将地区编号向上归一到省级并拼接省份名称；无法归属省级行政区的数据归为「未知」。

### 5.2 获取客户行业统计数据

- **路径**: GET /crm/statistics-portrait/get-customer-industry-summary
- **权限**: crm:statistics-portrait:query
- **说明**: 按客户行业统计客户数与成交数，用于【客户行业分析】页面。

**请求参数**: CrmStatisticsPortraitReqVO（见 5.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticCustomerIndustryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| industryId | Integer | 客户行业 ID |
| customerCount | Integer | 客户个数 |
| dealCount | Integer | 成交个数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按行业编号分组统计客户数与成交数并返回。

### 5.3 获取客户级别统计数据

- **路径**: GET /crm/statistics-portrait/get-customer-level-summary
- **权限**: crm:statistics-portrait:query
- **说明**: 按客户级别统计客户数与成交数，用于【客户级别分析】页面。

**请求参数**: CrmStatisticsPortraitReqVO（见 5.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticCustomerLevelRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| level | Integer | 客户级别编号 |
| customerCount | Integer | 客户个数 |
| dealCount | Integer | 成交个数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按客户级别分组统计客户数与成交数并返回。

### 5.4 获取客户来源统计数据

- **路径**: GET /crm/statistics-portrait/get-customer-source-summary
- **权限**: crm:statistics-portrait:query
- **说明**: 按客户来源统计客户数与成交数，用于【客户来源分析】页面。

**请求参数**: CrmStatisticsPortraitReqVO（见 5.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticCustomerSourceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| source | Integer | 客户来源编号 |
| customerCount | Integer | 客户个数 |
| dealCount | Integer | 成交个数 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 按客户来源分组统计客户数与成交数并返回。

## 6. 产品统计（CrmStatisticsProductController）

### 6.0 通用请求参数 (CrmStatisticsProductReqVO)

本控制器 2 个端点共用同一请求 VO：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userId | Long | 否 | - | 负责人用户编号（为空则统计该部门及子部门下全部用户） |
| userIds | List&lt;Long&gt; | 否 | hidden | 负责人用户编号集合（后端回填） |
| times | LocalDateTime[] | 是 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@NotEmpty、@Size(min=2, max=2) | 时间范围 |
| categoryId | Long | 否 | - | 产品分类编号（选择父分类时自动包含其子分类） |
| categoryIds | List&lt;Long&gt; | 否 | hidden | 产品分类编号集合（后端根据 categoryId 展开子分类后回填） |
| productId | Long | 否 | - | 产品编号 |

### 6.1 获取产品销售情况统计

- **路径**: GET /crm/statistics-product/get-product-sales-list
- **权限**: crm:statistics-product:query
- **说明**: 查询时间段内合同产品的销售明细（按合同 × 产品粒度）。

**请求参数**: CrmStatisticsProductReqVO（见 6.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsProductSalesRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| categoryId / categoryName | Long / String | 产品分类编号 / 名称 |
| productId / productName | Long / String | 产品编号 / 名称 |
| contractId / contractNo / contractName | Long / String / String | 合同编号 / 编码 / 名称 |
| ownerUserId / ownerUserName | Long / String | 负责人编号 / 姓名 |
| customerId / customerName | Long / String | 客户编号 / 名称 |
| productPrice | BigDecimal | 产品单价 |
| productCount | BigDecimal | 销售数量 |
| productTotalPrice | BigDecimal | 销售金额 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 若传入 categoryId，则查询产品分类列表并展开其直接子分类，回填 categoryIds。
3. 按用户、时间范围、分类 / 产品条件查询合同产品销售明细并返回。

### 6.2 获取产品分类销售分析

- **路径**: GET /crm/statistics-product/get-product-category-summary
- **权限**: crm:statistics-product:query
- **说明**: 按产品分类汇总合同数量、销售数量与销售金额。

**请求参数**: CrmStatisticsProductReqVO（见 6.0）

**响应**: CommonResult&lt;List&lt;CrmStatisticsProductCategoryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| categoryId / categoryName | Long / String | 产品分类编号 / 名称 |
| contractCount | Integer | 合同数量 |
| productCount | BigDecimal | 销售数量 |
| productTotalPrice | BigDecimal | 销售金额 |

**业务逻辑**:
1. 确定统计用户编号集合，为空返回空列表。
2. 若传入 categoryId，则展开其直接子分类并回填 categoryIds。
3. 按产品分类分组统计合同数量、销售数量、销售金额并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_008_000 | 产品不存在（关联产品域） |
| 1_020_009_000 | 产品分类不存在（关联产品分类域） |

## 7. 排行榜统计（CrmStatisticsRankController）

### 7.0 通用请求参数 (CrmStatisticsRankReqVO)

本控制器 8 个排行端点共用同一请求 VO，统计模式完全一致（仅排行 SQL 指标不同），Service 统一处理：确定部门（含子部门）用户集合 → 查询排行数据 → 按数量倒序排序 → 拼接用户昵称与部门名称。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| deptId | Long | 是 | @NotNull | 部门编号 |
| userIds | List&lt;Long&gt; | 否 | - | 负责人用户编号集合（后端根据 deptId 回填，前端无需传递） |
| times | LocalDateTime[] | 是 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@NotEmpty | 时间范围 |

**通用响应**: CommonResult&lt;List&lt;CrmStatisticsRankRespVO&gt;&gt;（8 个端点一致）

| 字段 | 类型 | 说明 |
|-----|------|------|
| ownerUserId | Long | 负责人编号 |
| nickname | String | 姓名 |
| deptName | String | 部门名称 |
| count | BigDecimal | 数量（金额类排行代表金额，数量类排行代表个数） |

**通用业务逻辑**:
1. 根据部门编号获取该部门及全部子部门的用户编号集合，为空返回空列表。
2. 按对应指标在时间范围内分组统计各用户的数量 / 金额。
3. 按 count 倒序排列生成排行榜。
4. 批量拼接用户昵称与所属部门名称后返回。

### 7.1 获得合同金额排行榜

- **路径**: GET /crm/statistics-rank/get-contract-price-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按合同金额对员工排名。

### 7.2 获得回款金额排行榜

- **路径**: GET /crm/statistics-rank/get-receivable-price-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按回款金额对员工排名。

### 7.3 获得签约合同数量排行榜

- **路径**: GET /crm/statistics-rank/get-contract-count-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按签约合同数量对员工排名。

### 7.4 获得产品销量排行榜

- **路径**: GET /crm/statistics-rank/get-product-sales-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按产品销量对员工排名。

### 7.5 获得新增客户数排行榜

- **路径**: GET /crm/statistics-rank/get-customer-count-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按新增客户数对员工排名。

### 7.6 获得新增联系人数排行榜

- **路径**: GET /crm/statistics-rank/get-contacts-count-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按新增联系人数对员工排名。

### 7.7 获得跟进次数排行榜

- **路径**: GET /crm/statistics-rank/get-follow-count-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按跟进次数对员工排名。

### 7.8 获得跟进客户数排行榜

- **路径**: GET /crm/statistics-rank/get-follow-customer-count-rank
- **权限**: crm:statistics-rank:query
- **说明**: 按跟进客户数对员工排名。
