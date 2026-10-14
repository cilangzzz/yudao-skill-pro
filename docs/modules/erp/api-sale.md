# 销售管理接口 (ErpCustomerController / ErpSaleOrderController / ErpSaleOutController / ErpSaleReturnController)

> 提供 ERP 销售域完整能力：客户档案维护、销售订单（含审核与出库/退货数量联动）、销售出库（扣减库存）、销售退货（回补库存）。

## 接口路径前缀

- /erp/customer  (Controller: ErpCustomerController)
- /erp/sale-order  (Controller: ErpSaleOrderController)
- /erp/sale-out  (Controller: ErpSaleOutController)
- /erp/sale-return  (Controller: ErpSaleReturnController)

## 1. 客户管理（ErpCustomerController）

### 1.1 创建客户

- **路径**: POST /erp/customer/create
- **权限**: erp:customer:create
- **说明**: 新增一个客户档案。

**请求参数 (ErpCustomerSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 客户编号（创建时不传） |
| name | String | 是 | @NotEmpty | 客户名称 |
| contact | String | 否 | - | 联系人 |
| mobile | String | 否 | - | 手机号码 |
| telephone | String | 否 | - | 联系电话 |
| email | String | 否 | - | 电子邮箱 |
| fax | String | 否 | - | 传真 |
| remark | String | 否 | - | 备注 |
| status | Integer | 是 | @NotNull | 开启状态（CommonStatusEnum） |
| sort | Integer | 是 | @NotNull | 排序 |
| taxNo | String | 否 | - | 纳税人识别号 |
| taxPercent | BigDecimal | 否 | - | 税率 |
| bankName | String | 否 | - | 开户行 |
| bankAccount | String | 否 | - | 开户账号 |
| bankAddress | String | 否 | - | 开户地址 |

**响应**: CommonResult&lt;Long&gt; —— 新客户编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的客户编号 |

**业务逻辑**:
1. 将请求 VO 转换为 ErpCustomerDO。
2. 插入客户表。
3. 返回新客户编号。

### 1.2 更新客户

- **路径**: PUT /erp/customer/update
- **权限**: erp:customer:update
- **说明**: 更新指定客户档案。

**请求参数 (ErpCustomerSaveReqVO)**: 同 1.1，其中 id 为更新目标客户编号。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验客户存在，不存在抛出 CUSTOMER_NOT_EXISTS。
2. 将请求 VO 转换为 ErpCustomerDO 并按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_200_000 | 客户不存在 |

### 1.3 删除客户

- **路径**: DELETE /erp/customer/delete
- **权限**: erp:customer:delete
- **说明**: 删除指定客户。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 客户编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验客户存在，不存在抛出 CUSTOMER_NOT_EXISTS。
2. 按 id 删除客户。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_200_000 | 客户不存在 |

### 1.4 获得客户

- **路径**: GET /erp/customer/get
- **权限**: erp:customer:query
- **说明**: 按编号查询单个客户详情。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 客户编号 |

**响应**: CommonResult&lt;ErpCustomerRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 客户编号 |
| name | String | 客户名称 |
| contact | String | 联系人 |
| mobile | String | 手机号码 |
| telephone | String | 联系电话 |
| email | String | 电子邮箱 |
| fax | String | 传真 |
| remark | String | 备注 |
| status | Integer | 开启状态 |
| sort | Integer | 排序 |
| taxNo | String | 纳税人识别号 |
| taxPercent | BigDecimal | 税率 |
| bankName | String | 开户行 |
| bankAccount | String | 开户账号 |
| bankAddress | String | 开户地址 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询客户。
2. 转换为 ErpCustomerRespVO 返回（不存在时返回 null）。

### 1.5 获得客户分页

- **路径**: GET /erp/customer/page
- **权限**: erp:customer:query
- **说明**: 分页查询客户列表，支持名称、手机号、联系电话模糊筛选。

**请求参数 (ErpCustomerPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | @Min(value = 1)（PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 否 | @Min(value = 1)（PageParam） | 每页条数 |
| name | String | 否 | - | 客户名称，模糊匹配 |
| mobile | String | 否 | - | 手机号码 |
| telephone | String | 否 | - | 联系电话 |

**响应**: CommonResult&lt;PageResult&lt;ErpCustomerRespVO&gt;&gt; —— 字段同 1.4

**业务逻辑**:
1. 按筛选条件分页查询客户。
2. 转换为 ErpCustomerRespVO 分页结果返回。

### 1.6 获得客户精简列表

- **路径**: GET /erp/customer/simple-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 只包含开启状态的客户，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ErpCustomerRespVO&gt;&gt; —— 仅返回精简字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 客户编号 |
| name | String | 客户名称 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）的客户列表。
2. 只取 id、name 两个字段返回。

### 1.7 导出客户 Excel

- **路径**: GET /erp/customer/export-excel
- **权限**: erp:customer:export
- **说明**: 按分页条件导出客户 Excel 文件（客户.xls）。

**请求参数 (ErpCustomerPageReqVO)**: 同 1.5（导出时 pageSize 被置为不分页）

**响应**: Excel 文件流（客户.xls）

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE，查询全部符合条件的客户。
2. 使用 ExcelUtils 按 ErpCustomerRespVO 注解导出 Excel。

## 2. 销售订单（ErpSaleOrderController）

### 2.1 创建销售订单

- **路径**: POST /erp/sale-order/create
- **权限**: erp:sale-order:create
- **说明**: 创建销售订单（初始为未审核状态），自动生成销售单号并计算各项金额。

**请求参数 (ErpSaleOrderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| customerId | Long | 是 | @NotNull | 客户编号 |
| orderTime | LocalDateTime | 是 | @NotNull | 下单时间 |
| saleUserId | Long | 否 | - | 销售员编号 |
| accountId | Long | 否 | - | 结算账户编号 |
| discountPercent | BigDecimal | 否 | - | 优惠率，百分比 |
| depositPrice | BigDecimal | 否 | - | 定金金额，单位：元 |
| fileUrl | String | 否 | - | 附件地址 |
| remark | String | 否 | - | 备注 |
| items | List&lt;Item&gt; | 否 | - | 订单清单列表 |

Item 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 订单项编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productUnitId | Long | 是 | @NotNull | 产品单位编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| taxPercent | BigDecimal | 否 | - | 税率，百分比 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 新销售订单编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的销售订单编号 |

**业务逻辑**:
1. 校验订单项：产品存在且启用，按产品信息回填单位编号，计算每项小计金额（单价 × 数量），税率非空时计算税额（小计 × 税率%）。
2. 校验客户存在且启用，否则抛 CUSTOMER_NOT_EXISTS / CUSTOMER_NOT_ENABLE。
3. 结算账户编号非空时校验结算账户存在且启用。
4. 销售员编号非空时校验用户存在。
5. 通过 ErpNoRedisDAO 生成销售单号（前缀前生成），并校验单号唯一，重复抛 SALE_ORDER_NO_EXISTS。
6. 插入销售订单：状态置为未审核（ErpAuditStatus.PROCESS），计算合计数量、合计产品金额、合计税额、优惠金额（总价 × 优惠率%）、最终总价（产品金额 + 税额 - 优惠金额）。
7. 批量插入订单项并关联订单编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_200_000 | 客户不存在 |
| 1_020_200_001 | 客户({})未启用 |
| 1_020_201_004 | 生成销售单号失败，请重新提交 |
| 1_030_600_000 | 结算账户不存在 |
| 1_030_600_001 | 结算账户({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 2.2 更新销售订单

- **路径**: PUT /erp/sale-order/update
- **权限**: erp:sale-order:update
- **说明**: 更新未审核的销售订单及其订单项。

**请求参数 (ErpSaleOrderSaveReqVO)**: 同 2.1，其中 id 为更新目标订单编号。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验订单存在，不存在抛 SALE_ORDER_NOT_EXISTS；已审核则抛 SALE_ORDER_UPDATE_FAIL_APPROVE。
2. 校验客户存在且启用。
3. 结算账户、销售员非空时分别校验。
4. 校验订单项（同创建逻辑）。
5. 重算合计金额后更新订单。
6. 对比新老订单项列表（diffList），分别批量新增、更新、删除订单项。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_201_000 | 销售订单不存在 |
| 1_020_201_005 | 销售订单({})已审核，无法修改 |
| 1_020_200_000 | 客户不存在 |
| 1_020_200_001 | 客户({})未启用 |
| 1_030_600_000 | 结算账户不存在 |
| 1_030_600_001 | 结算账户({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 2.3 更新销售订单的状态

- **路径**: PUT /erp/sale-order/update-status
- **权限**: erp:sale-order:update-status
- **说明**: 审核或反审核销售订单（ErpAuditStatus：PROCESS 未审核 / APPROVE 已审核）。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 销售订单编号 |
| status | Integer | 是 | 目标状态（10 未审核 / 20 已审核） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验订单存在。
2. 校验状态未发生变化，相同则按目标抛 SALE_ORDER_APPROVE_FAIL / SALE_ORDER_PROCESS_FAIL。
3. 反审核时校验：订单已出库数量大于 0 抛 SALE_ORDER_PROCESS_FAIL_EXISTS_OUT；已退货数量大于 0 抛 SALE_ORDER_PROCESS_FAIL_EXISTS_RETURN。
4. 通过 updateByIdAndStatus（CAS）更新状态，更新行数为 0 时抛审核/反审核失败错误。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_201_000 | 销售订单不存在 |
| 1_020_201_002 | 反审核失败，只有已审核的销售订单才能反审核 |
| 1_020_201_003 | 审核失败，只有未审核的销售订单才能审核 |
| 1_020_201_008 | 反审核失败，已存在对应的销售出库单 |
| 1_020_201_010 | 反审核失败，已存在对应的销售退货单 |

### 2.4 删除销售订单

- **路径**: DELETE /erp/sale-order/delete
- **权限**: erp:sale-order:delete
- **说明**: 批量删除销售订单（仅未审核状态允许）。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| ids | List&lt;Long&gt; | 是 | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 按 ids 批量查询订单，列表为空直接返回。
2. 任一订单已审核则抛 SALE_ORDER_DELETE_FAIL_APPROVE。
3. 遍历删除订单及其全部订单项。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_201_001 | 销售订单({})已审核，无法删除 |

### 2.5 获得销售订单

- **路径**: GET /erp/sale-order/get
- **权限**: erp:sale-order:query
- **说明**: 查询订单详情，含订单项、产品信息与当前库存数量。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 销售订单编号 |

**响应**: CommonResult&lt;ErpSaleOrderRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 销售单编号 |
| status | Integer | 销售状态（10 未审核 / 20 已审核） |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| accountId | Long | 结算账户编号 |
| saleUserId | Long | 销售员编号 |
| orderTime | LocalDateTime | 下单时间 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 最终合计价格 |
| totalProductPrice | BigDecimal | 合计产品价格，单位：元 |
| totalTaxPrice | BigDecimal | 合计税额，单位：元 |
| discountPercent | BigDecimal | 优惠率，百分比 |
| discountPrice | BigDecimal | 优惠金额，单位：元 |
| depositPrice | BigDecimal | 定金金额，单位：元 |
| fileUrl | String | 附件地址 |
| remark | String | 备注 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称 |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 订单项列表 |
| productNames | String | 产品信息（名称拼接） |
| outCount | BigDecimal | 销售出库数量 |
| returnCount | BigDecimal | 销售退货数量 |

Item 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 订单项编号 |
| productId | Long | 产品编号 |
| productUnitId | Long | 产品单位编号 |
| productPrice | BigDecimal | 产品单价 |
| count | BigDecimal | 产品数量 |
| taxPercent | BigDecimal | 税率，百分比 |
| taxPrice | BigDecimal | 税额，单位：元 |
| remark | String | 备注 |
| outCount | BigDecimal | 销售出库数量 |
| returnCount | BigDecimal | 销售退货数量 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 库存数量（仅详情/编辑时使用） |

**业务逻辑**:
1. 查询订单，不存在返回 null。
2. 查询订单全部订单项。
3. 批量查询产品信息（产品名称、条码、单位名称）。
4. 按订单项的产品编号查询库存数量，为空时置 0。
5. 组装 ErpSaleOrderRespVO 返回。

### 2.6 获得销售订单分页

- **路径**: GET /erp/sale-order/page
- **权限**: erp:sale-order:query
- **说明**: 分页查询销售订单，附带订单项、产品、客户、创建人信息。

**请求参数 (ErpSaleOrderPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | @Min(value = 1)（PageParam） | 页码 |
| pageSize | Integer | 否 | @Min(value = 1)（PageParam） | 每页条数 |
| no | String | 否 | - | 销售单编号 |
| customerId | Long | 否 | - | 客户编号 |
| orderTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 下单时间范围 |
| remark | String | 否 | - | 备注 |
| status | Integer | 否 | - | 销售状态（10 未审核 / 20 已审核） |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |
| outStatus | Integer | 否 | - | 出库状态（0 无 / 1 部分 / 2 全部） |
| returnStatus | Integer | 否 | - | 退货状态（0 无 / 1 部分 / 2 全部） |
| outEnable | Boolean | 否 | - | 是否可出库 |
| returnEnable | Boolean | 否 | - | 是否可退货 |

**响应**: CommonResult&lt;PageResult&lt;ErpSaleOrderRespVO&gt;&gt; —— 字段同 2.5（Item 中 stockCount 不填充）

**业务逻辑**:
1. 按条件分页查询销售订单。
2. 批量查询各订单的订单项。
3. 批量查询产品信息、客户信息、创建人（AdminUserApi）信息。
4. 拼接每行：订单项（含产品名称/条码/单位名称）、productNames（产品名称以「，」拼接）、customerName、creatorName。

### 2.7 导出销售订单 Excel

- **路径**: GET /erp/sale-order/export-excel
- **权限**: erp:sale-order:export
- **说明**: 按分页条件导出销售订单 Excel（销售订单.xls）。

**请求参数 (ErpSaleOrderPageReqVO)**: 同 2.6（导出时 pageSize 被置为不分页）

**响应**: Excel 文件流（销售订单.xls）

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE，查询全部符合条件的订单并完成与分页一致的数据拼接。
2. 使用 ExcelUtils 按 ErpSaleOrderRespVO 注解导出 Excel。

## 3. 销售出库（ErpSaleOutController）

### 3.1 创建销售出库

- **路径**: POST /erp/sale-out/create
- **权限**: erp:sale-out:create
- **说明**: 基于已审核的销售订单创建出库单（初始未审核），并联动更新订单出库数量。

**请求参数 (ErpSaleOutSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| accountId | Long | 否 | - | 结算账户编号 |
| saleUserId | Long | 否 | - | 销售员编号 |
| outTime | LocalDateTime | 是 | @NotNull | 出库时间 |
| orderId | Long | 是 | @NotNull | 销售订单编号 |
| discountPercent | BigDecimal | 否 | - | 优惠率，百分比 |
| otherPrice | BigDecimal | 否 | - | 其它金额，单位：元 |
| fileUrl | String | 否 | - | 附件地址 |
| remark | String | 否 | - | 备注 |
| items | List&lt;Item&gt; | 否 | - | 出库清单列表 |

Item 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 出库项编号 |
| orderItemId | Long | 是 | @NotNull | 销售订单项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productUnitId | Long | 是 | @NotNull | 产品单位编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| taxPercent | BigDecimal | 否 | - | 税率，百分比 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 新出库单编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的销售出库单编号 |

**业务逻辑**:
1. 校验销售订单存在且已审核（未审核抛 SALE_ORDER_NOT_APPROVE）。
2. 校验出库项：产品存在且启用，回填单位编号，计算小计金额与税额。
3. 校验结算账户存在且启用。
4. 销售员编号非空时校验用户存在。
5. 通过 ErpNoRedisDAO 生成出库单号（SALE_OUT 前缀），校验唯一，重复抛 SALE_OUT_NO_EXISTS。
6. 插入出库单：状态置为未审核，冗余销售单号与客户编号，计算合计数量/产品金额/税额/优惠金额/最终总价（含其它金额）；批量插入出库项。
7. 按订单下全部出库单重新聚合各订单项的出库数量并更新销售订单，超出订单项数量时抛 SALE_ORDER_ITEM_OUT_FAIL_PRODUCT_EXCEED。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_201_000 | 销售订单不存在 |
| 1_020_201_006 | 销售订单未审核，无法操作 |
| 1_020_201_007 | 销售订单项({})超过最大允许出库数量({}) |
| 1_020_202_004 | 生成出库单失败，请重新提交 |
| 1_030_600_000 | 结算账户不存在 |
| 1_030_600_001 | 结算账户({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 3.2 更新销售出库

- **路径**: PUT /erp/sale-out/update
- **权限**: erp:sale-out:update
- **说明**: 更新未审核的出库单，并联动更新销售订单出库数量。

**请求参数 (ErpSaleOutSaveReqVO)**: 同 3.1，其中 id 为更新目标出库单编号。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验出库单存在，不存在抛 SALE_OUT_NOT_EXISTS；已审核则抛 SALE_OUT_UPDATE_FAIL_APPROVE。
2. 校验销售订单存在且已审核。
3. 校验结算账户、销售员。
4. 校验出库项有效性。
5. 重算金额后更新出库单（冗余销售单号、客户编号），并 diff 更新出库项（批量新增/更新/删除）。
6. 更新新订单的出库数量；若订单编号变更，同步更新老订单的出库数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_202_000 | 销售出库单不存在 |
| 1_020_202_005 | 销售出库单({})已审核，无法修改 |
| 1_020_201_006 | 销售订单未审核，无法操作 |
| 1_020_201_007 | 销售订单项({})超过最大允许出库数量({}) |
| 1_030_600_000 | 结算账户不存在 |
| 1_030_600_001 | 结算账户({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 3.3 更新销售出库的状态

- **路径**: PUT /erp/sale-out/update-status
- **权限**: erp:sale-out:update-status
- **说明**: 审核或反审核出库单；审核扣减库存，反审核回补库存。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 出库单编号 |
| status | Integer | 是 | 目标状态（10 未审核 / 20 已审核） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验出库单存在。
2. 校验状态未发生变化，相同则按目标抛 SALE_OUT_APPROVE_FAIL / SALE_OUT_PROCESS_FAIL。
3. 反审核时校验已收款金额为 0，大于 0 抛 SALE_OUT_PROCESS_FAIL_EXISTS_RECEIPT。
4. 通过 updateByIdAndStatus（CAS）更新状态，失败抛审核/反审核失败错误。
5. 变更库存：审核时按出库项数量负数创建库存记录（业务类型 SALE_OUT），反审核时正数回补（SALE_OUT_CANCEL）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_202_000 | 销售出库单不存在 |
| 1_020_202_002 | 反审核失败，只有已审核的出库单才能反审核 |
| 1_020_202_003 | 审核失败，只有未审核的出库单才能审核 |
| 1_020_202_008 | 反审核失败，已存在对应的收款单 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存小于变更数量 |

### 3.4 删除销售出库

- **路径**: DELETE /erp/sale-out/delete
- **权限**: erp:sale-out:delete
- **说明**: 批量删除出库单（仅未审核状态允许），并回滚订单出库数量。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| ids | List&lt;Long&gt; | 是 | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 按 ids 批量查询出库单，列表为空直接返回。
2. 任一出库单已审核则抛 SALE_OUT_DELETE_FAIL_APPROVE。
3. 遍历删除出库单及其出库项，并重新聚合更新对应销售订单的出库数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_202_001 | 销售出库单({})已审核，无法删除 |
| 1_020_201_007 | 销售订单项({})超过最大允许出库数量({}) |

### 3.5 获得销售出库

- **路径**: GET /erp/sale-out/get
- **权限**: erp:sale-out:query
- **说明**: 查询出库单详情，含出库项、产品信息与仓库当前库存。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 出库单编号 |

**响应**: CommonResult&lt;ErpSaleOutRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 出库单编号 |
| status | Integer | 出库状态（10 未审核 / 20 已审核） |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| accountId | Long | 结算账户编号 |
| saleUserId | Long | 出库员编号 |
| outTime | LocalDateTime | 出库时间 |
| orderId | Long | 销售订单编号 |
| orderNo | String | 销售订单号 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 最终合计价格 |
| receiptPrice | BigDecimal | 已收款金额，单位：元 |
| totalProductPrice | BigDecimal | 合计产品价格，单位：元 |
| totalTaxPrice | BigDecimal | 合计税额，单位：元 |
| discountPercent | BigDecimal | 优惠率，百分比 |
| discountPrice | BigDecimal | 优惠金额，单位：元 |
| otherPrice | BigDecimal | 其它金额，单位：元 |
| fileUrl | String | 附件地址 |
| remark | String | 备注 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称 |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 出库项列表 |
| productNames | String | 产品信息（名称拼接） |

Item 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 出库项编号 |
| orderItemId | Long | 销售订单项编号 |
| warehouseId | Long | 仓库编号 |
| productId | Long | 产品编号 |
| productUnitId | Long | 产品单位编号 |
| productPrice | BigDecimal | 产品单价 |
| count | BigDecimal | 产品数量 |
| taxPercent | BigDecimal | 税率，百分比 |
| taxPrice | BigDecimal | 税额，单位：元 |
| remark | String | 备注 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 库存数量（仅详情/编辑时使用） |

**业务逻辑**:
1. 查询出库单，不存在返回 null。
2. 查询出库单全部出库项。
3. 批量查询产品信息（名称、条码、单位名称）。
4. 按出库项的产品 + 仓库查询库存数量，为空时置 0。
5. 组装 ErpSaleOutRespVO 返回。

### 3.6 获得销售出库分页

- **路径**: GET /erp/sale-out/page
- **权限**: erp:sale-out:query
- **说明**: 分页查询销售出库单，附得出库项、产品、客户、创建人信息。

**请求参数 (ErpSaleOutPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | @Min(value = 1)（PageParam） | 页码 |
| pageSize | Integer | 否 | @Min(value = 1)（PageParam） | 每页条数 |
| no | String | 否 | - | 出库单编号 |
| customerId | Long | 否 | - | 客户编号 |
| outTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 出库时间范围 |
| remark | String | 否 | - | 备注 |
| status | Integer | 否 | - | 出库状态（10 未审核 / 20 已审核） |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |
| warehouseId | Long | 否 | - | 仓库编号 |
| accountId | Long | 否 | - | 结算账户编号 |
| receiptStatus | Integer | 否 | - | 收款状态（0 未收款 / 1 部分收款 / 2 全部收款） |
| receiptEnable | Boolean | 否 | - | 是否可收款（对应 receiptStatus 为 0 或 1） |
| orderNo | String | 否 | - | 销售单号 |

**响应**: CommonResult&lt;PageResult&lt;ErpSaleOutRespVO&gt;&gt; —— 字段同 3.5（Item 中 stockCount 不填充）

**业务逻辑**:
1. 按条件分页查询销售出库单。
2. 批量查询各出库单的出库项。
3. 批量查询产品信息、客户信息、创建人信息。
4. 拼接每行：出库项（含产品名称/条码/单位名称）、productNames、customerName、creatorName。

### 3.7 导出销售出库 Excel

- **路径**: GET /erp/sale-out/export-excel
- **权限**: erp:sale-out:export
- **说明**: 按分页条件导出销售出库 Excel（销售出库.xls）。

**请求参数 (ErpSaleOutPageReqVO)**: 同 3.6（导出时 pageSize 被置为不分页）

**响应**: Excel 文件流（销售出库.xls）

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE，查询全部符合条件的出库单并完成数据拼接。
2. 使用 ExcelUtils 按 ErpSaleOutRespVO 注解导出 Excel。

## 4. 销售退货（ErpSaleReturnController）

### 4.1 创建销售退货

- **路径**: POST /erp/sale-return/create
- **权限**: erp:sale-return:create
- **说明**: 基于已审核的销售订单创建退货单（初始未审核），并联动更新订单退货数量。

**请求参数 (ErpSaleReturnSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| accountId | Long | 否 | - | 结算账户编号 |
| saleUserId | Long | 否 | - | 销售员编号 |
| returnTime | LocalDateTime | 是 | @NotNull | 退货时间 |
| orderId | Long | 是 | @NotNull | 销售订单编号 |
| discountPercent | BigDecimal | 否 | - | 优惠率，百分比 |
| otherPrice | BigDecimal | 否 | - | 其它金额，单位：元 |
| fileUrl | String | 否 | - | 附件地址 |
| remark | String | 否 | - | 备注 |
| items | List&lt;Item&gt; | 否 | - | 退货清单列表 |

Item 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 退货项编号 |
| orderItemId | Long | 是 | @NotNull | 销售订单项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productUnitId | Long | 是 | @NotNull | 产品单位编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| taxPercent | BigDecimal | 否 | - | 税率，百分比 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 新退货单编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的销售退货单编号 |

**业务逻辑**:
1. 校验销售订单存在且已审核（未审核抛 SALE_ORDER_NOT_APPROVE）。
2. 校验退货项：产品存在且启用，回填单位编号，计算小计金额与税额。
3. 校验结算账户存在且启用。
4. 销售员编号非空时校验用户存在。
5. 通过 ErpNoRedisDAO 生成退货单号（SALE_RETURN 前缀），校验唯一，重复抛 SALE_RETURN_NO_EXISTS。
6. 插入退货单：状态置为未审核，冗余销售单号与客户编号，计算合计数量/产品金额/税额/优惠金额/最终总价（含其它金额）；批量插入退货项。
7. 按订单下全部退货单重新聚合各订单项的退货数量并更新销售订单，退货数量超过已出库数量时抛 SALE_ORDER_ITEM_RETURN_FAIL_OUT_EXCEED。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_201_000 | 销售订单不存在 |
| 1_020_201_006 | 销售订单未审核，无法操作 |
| 1_020_201_009 | 销售订单项({})超过最大允许退货数量({}) |
| 1_020_203_004 | 生成退货单失败，请重新提交 |
| 1_030_600_000 | 结算账户不存在 |
| 1_030_600_001 | 结算账户({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 4.2 更新销售退货

- **路径**: PUT /erp/sale-return/update
- **权限**: erp:sale-return:update
- **说明**: 更新未审核的退货单，并联动更新销售订单退货数量。

**请求参数 (ErpSaleReturnSaveReqVO)**: 同 4.1，其中 id 为更新目标退货单编号。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验退货单存在，不存在抛 SALE_RETURN_NOT_EXISTS；已审核则抛 SALE_RETURN_UPDATE_FAIL_APPROVE。
2. 校验销售订单存在且已审核。
3. 校验结算账户、销售员。
4. 校验退货项有效性。
5. 重算金额后更新退货单（冗余销售单号、客户编号），并 diff 更新退货项（批量新增/更新/删除）。
6. 更新新订单的退货数量；若订单编号变更，同步更新老订单的退货数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_203_000 | 销售退货单不存在 |
| 1_020_203_005 | 销售退货单({})已审核，无法修改 |
| 1_020_201_006 | 销售订单未审核，无法操作 |
| 1_020_201_009 | 销售订单项({})超过最大允许退货数量({}) |
| 1_030_600_000 | 结算账户不存在 |
| 1_030_600_001 | 结算账户({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 4.3 更新销售退货的状态

- **路径**: PUT /erp/sale-return/update-status
- **权限**: erp:sale-return:update-status
- **说明**: 审核或反审核退货单；审核回补库存，反审核扣减库存。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 退货单编号 |
| status | Integer | 是 | 目标状态（10 未审核 / 20 已审核） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验退货单存在。
2. 校验状态未发生变化，相同则按目标抛 SALE_RETURN_APPROVE_FAIL / SALE_RETURN_PROCESS_FAIL。
3. 反审核时校验已退款金额为 0，大于 0 抛 SALE_RETURN_PROCESS_FAIL_EXISTS_REFUND。
4. 通过 updateByIdAndStatus（CAS）更新状态，失败抛审核/反审核失败错误。
5. 变更库存：审核时按退货项数量正数创建库存记录（业务类型 SALE_RETURN），反审核时负数扣减（SALE_RETURN_CANCEL）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_203_000 | 销售退货单不存在 |
| 1_020_203_002 | 反审核失败，只有已审核的退货单才能反审核 |
| 1_020_203_003 | 审核失败，只有未审核的退货单才能审核 |
| 1_020_203_008 | 反审核失败，已存在对应的退款单 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存小于变更数量 |

### 4.4 删除销售退货

- **路径**: DELETE /erp/sale-return/delete
- **权限**: erp:sale-return:delete
- **说明**: 批量删除退货单（仅未审核状态允许），并回滚订单退货数量。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| ids | List&lt;Long&gt; | 是 | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 按 ids 批量查询退货单，列表为空直接返回。
2. 任一退货单已审核则抛 SALE_RETURN_DELETE_FAIL_APPROVE。
3. 遍历删除退货单及其退货项，并重新聚合更新对应销售订单的退货数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_203_001 | 销售退货单({})已审核，无法删除 |
| 1_020_201_009 | 销售订单项({})超过最大允许退货数量({}) |

### 4.5 获得销售退货

- **路径**: GET /erp/sale-return/get
- **权限**: erp:sale-return:query
- **说明**: 查询退货单详情，含退货项、产品信息与仓库当前库存。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 退货单编号 |

**响应**: CommonResult&lt;ErpSaleReturnRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 退货单编号 |
| status | Integer | 退货状态（10 未审核 / 20 已审核） |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| accountId | Long | 结算账户编号 |
| saleUserId | Long | 退货员编号 |
| returnTime | LocalDateTime | 退货时间 |
| orderId | Long | 销售订单编号 |
| orderNo | String | 销售订单号 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 最终合计价格 |
| refundPrice | BigDecimal | 已退款金额，单位：元 |
| totalProductPrice | BigDecimal | 合计产品价格，单位：元 |
| totalTaxPrice | BigDecimal | 合计税额，单位：元 |
| discountPercent | BigDecimal | 优惠率，百分比 |
| discountPrice | BigDecimal | 优惠金额，单位：元 |
| otherPrice | BigDecimal | 其它金额，单位：元 |
| fileUrl | String | 附件地址 |
| remark | String | 备注 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称 |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 退货项列表 |
| productNames | String | 产品信息（名称拼接） |

Item 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 退货项编号 |
| orderItemId | Long | 销售订单项编号 |
| warehouseId | Long | 仓库编号 |
| productId | Long | 产品编号 |
| productUnitId | Long | 产品单位编号 |
| productPrice | BigDecimal | 产品单价 |
| count | BigDecimal | 产品数量 |
| taxPercent | BigDecimal | 税率，百分比 |
| taxPrice | BigDecimal | 税额，单位：元 |
| remark | String | 备注 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 库存数量（仅详情/编辑时使用） |

**业务逻辑**:
1. 查询退货单，不存在返回 null。
2. 查询退货单全部退货项。
3. 批量查询产品信息（名称、条码、单位名称）。
4. 按退货项的产品 + 仓库查询库存数量，为空时置 0。
5. 组装 ErpSaleReturnRespVO 返回。

### 4.6 获得销售退货分页

- **路径**: GET /erp/sale-return/page
- **权限**: erp:sale-return:query
- **说明**: 分页查询销售退货单，附带退货项、产品、客户、创建人信息。

**请求参数 (ErpSaleReturnPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | @Min(value = 1)（PageParam） | 页码 |
| pageSize | Integer | 否 | @Min(value = 1)（PageParam） | 每页条数 |
| no | String | 否 | - | 退货单编号 |
| customerId | Long | 否 | - | 客户编号 |
| returnTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 退货时间范围 |
| remark | String | 否 | - | 备注 |
| status | Integer | 否 | - | 退货状态（10 未审核 / 20 已审核） |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |
| warehouseId | Long | 否 | - | 仓库编号 |
| accountId | Long | 否 | - | 结算账户编号 |
| orderNo | String | 否 | - | 销售单号 |
| refundStatus | Integer | 否 | - | 退款状态（0 未退款 / 1 部分退款 / 2 全部退款） |
| refundEnable | Boolean | 否 | - | 是否可退款（对应 refundStatus 为 0 或 1） |

**响应**: CommonResult&lt;PageResult&lt;ErpSaleReturnRespVO&gt;&gt; —— 字段同 4.5（Item 中 stockCount 不填充）

**业务逻辑**:
1. 按条件分页查询销售退货单。
2. 批量查询各退货单的退货项。
3. 批量查询产品信息、客户信息、创建人信息。
4. 拼接每行：退货项（含产品名称/条码/单位名称）、productNames、customerName、creatorName。

### 4.7 导出销售退货 Excel

- **路径**: GET /erp/sale-return/export-excel
- **权限**: erp:sale-return:export
- **说明**: 按分页条件导出销售退货 Excel（销售退货.xls）。

**请求参数 (ErpSaleReturnPageReqVO)**: 同 4.6（导出时 pageSize 被置为不分页）

**响应**: Excel 文件流（销售退货.xls）

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE，查询全部符合条件的退货单并完成数据拼接。
2. 使用 ExcelUtils 按 ErpSaleReturnRespVO 注解导出 Excel。
