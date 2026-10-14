# 采购管理接口 (ErpSupplierController / ErpPurchaseOrderController / ErpPurchaseInController / ErpPurchaseReturnController)

> ERP 采购管理域，覆盖供应商档案维护、采购订单、采购入库与采购退货四类单据的创建、审核（状态流转）、删除、查询与 Excel 导出；入库/退货审核时自动变更库存并回写采购订单的入库/退货数量。

## 接口路径前缀

- `/erp/supplier` (Controller: ErpSupplierController)
- `/erp/purchase-order` (Controller: ErpPurchaseOrderController)
- `/erp/purchase-in` (Controller: ErpPurchaseInController)
- `/erp/purchase-return` (Controller: ErpPurchaseReturnController)

单据类接口（采购订单/入库/退货）共用一套审核状态：`10 = 未审核（PROCESS）`、`20 = 已审核（APPROVE）`（枚举 `ErpAuditStatus`）。

---

## 1. 供应商管理（/erp/supplier）

### 1.1 创建供应商

- **路径**: POST /erp/supplier/create
- **权限**: erp:supplier:create
- **说明**: 新增一个供应商档案，返回新供应商编号。

**请求参数 (ErpSupplierSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 供应商编号（新增时不传） |
| name | String | 是 | @NotEmpty | 供应商名称 |
| contact | String | 否 | | 联系人 |
| mobile | String | 否 | @Mobile | 手机号码 |
| telephone | String | 否 | @Telephone | 联系电话 |
| email | String | 否 | @Email | 电子邮箱 |
| fax | String | 否 | | 传真 |
| remark | String | 否 | | 备注 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 开启状态 |
| sort | Integer | 是 | @NotNull | 排序 |
| taxNo | String | 否 | | 纳税人识别号 |
| taxPercent | BigDecimal | 否 | | 税率 |
| bankName | String | 否 | | 开户行 |
| bankAccount | String | 否 | | 开户账号 |
| bankAddress | String | 否 | | 开户地址 |

**响应**: `CommonResult<Long>` — 新创建的供应商编号。

**业务逻辑**: 1. 将 ReqVO 转换为 ErpSupplierDO；2. 插入数据库；3. 返回自增主键 id。

### 1.2 更新供应商

- **路径**: PUT /erp/supplier/update
- **权限**: erp:supplier:update
- **说明**: 按 id 更新供应商档案。

**请求参数 (ErpSupplierSaveReqVO)**: 字段同 1.1，此时 id 必传。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**: 1. 校验供应商存在，不存在抛 SUPPLIER_NOT_EXISTS；2. 转换为 DO 后按 id 全量更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_100_000 | 供应商不存在 |

### 1.3 删除供应商

- **路径**: DELETE /erp/supplier/delete
- **权限**: erp:supplier:delete
- **说明**: 按编号删除单个供应商。

**请求参数**: Query 参数 `id`（Long，必填，供应商编号）。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**: 1. 校验供应商存在，不存在抛 SUPPLIER_NOT_EXISTS；2. 按 id 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_100_000 | 供应商不存在 |

### 1.4 获得供应商详情

- **路径**: GET /erp/supplier/get
- **权限**: erp:supplier:query
- **说明**: 按编号查询供应商详情。

**请求参数**: Query 参数 `id`（Long，必填，供应商编号）。

**响应**: `CommonResult<ErpSupplierRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 供应商编号 |
| name | String | 供应商名称 |
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

**业务逻辑**: 1. 按 id 查询 DO；2. 转换为 RespVO 返回（不存在时返回 null 数据）。

### 1.5 获得供应商分页

- **路径**: GET /erp/supplier/page
- **权限**: erp:supplier:query
- **说明**: 分页查询供应商列表。

**请求参数 (ErpSupplierPageReqVO)**: 继承 PageParam（`pageNo` 页码、`pageSize` 每页条数）。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | | 页码 |
| pageSize | Integer | 是 | | 每页条数 |
| name | String | 否 | | 供应商名称（模糊匹配） |
| mobile | String | 否 | | 手机号码 |
| telephone | String | 否 | | 联系电话 |

**响应**: `CommonResult<PageResult<ErpSupplierRespVO>>` — 列表项字段同 1.4 的 RespVO 表。

**业务逻辑**: 1. 按条件分页查询；2. DO 列表转换为 RespVO 分页结果。

### 1.6 获得供应商精简列表

- **路径**: GET /erp/supplier/simple-list
- **权限**: 已认证（无 @PreAuthorize 权限标识）
- **说明**: 获取全部开启状态的供应商，仅含 id/name，用于前端下拉选项。

**请求参数**: 无

**响应**: `CommonResult<List<ErpSupplierRespVO>>` — 列表项仅填充 `id`、`name` 两个字段。

**业务逻辑**: 1. 查询状态为开启（CommonStatusEnum.ENABLE）的供应商列表；2. 仅提取 id 与 name 组装返回。

### 1.7 导出供应商 Excel

- **路径**: GET /erp/supplier/export-excel
- **权限**: erp:supplier:export
- **说明**: 按分页条件导出供应商 Excel 文件（供应商.xls）。

**请求参数 (ErpSupplierPageReqVO)**: 同 1.5（服务端强制 pageSize = PAGE_SIZE_NONE，一次导出全部）。

**响应**: 无 CommonResult，直接向 HttpServletResponse 输出 Excel 文件流（列定义来自 ErpSupplierRespVO 的 @ExcelProperty 注解）。

**业务逻辑**: 1. 将 pageSize 设置为不分页上限；2. 复用分页查询取出全量数据；3. 转换为 RespVO 后通过 ExcelUtils 写出文件；4. 记录导出操作日志（@ApiAccessLog EXPORT）。

---

## 2. 采购订单（/erp/purchase-order）

### 2.1 创建采购订单

- **路径**: POST /erp/purchase-order/create
- **权限**: erp:purchase-order:create
- **说明**: 创建采购订单（初始状态为未审核），返回订单编号。

**请求参数 (ErpPurchaseOrderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（新增时不传） |
| supplierId | Long | 是 | @NotNull | 供应商编号 |
| accountId | Long | 否 | | 结算账户编号 |
| orderTime | LocalDateTime | 是 | @NotNull | 采购时间 |
| discountPercent | BigDecimal | 否 | | 优惠率，百分比 |
| depositPrice | BigDecimal | 否 | | 定金金额，单位：元 |
| fileUrl | String | 否 | | 附件地址 |
| remark | String | 否 | | 备注 |
| items | List&lt;Item&gt; | 否 | | 订单清单列表 |

Item 子对象：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 订单项编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productUnitId | Long | 是 | @NotNull | 产品单位编号 |
| productPrice | BigDecimal | 否 | | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| taxPercent | BigDecimal | 否 | | 税率，百分比 |
| remark | String | 否 | | 备注 |

**响应**: `CommonResult<Long>` — 新创建的采购订单编号。

**业务逻辑**:
1. 校验订单项有效性：校验产品存在并启用，按产品补全 productUnitId，计算订单项总价 totalPrice（单价 × 数量）与税额 taxPrice（总价 × 税率）。
2. 校验供应商有效（存在且启用），无效抛 SUPPLIER_NOT_EXISTS / SUPPLIER_NOT_ENABLE。
3. 若传了结算账户 accountId，校验结算账户有效。
4. 通过 ErpNoRedisDAO 生成采购单号（前缀 PURCHASE_ORDER_NO_PREFIX），若单号已存在抛 PURCHASE_ORDER_NO_EXISTS。
5. 组装订单 DO：状态置为未审核（PROCESS），计算合计数量 totalCount、合计产品价格 totalProductPrice、合计税额 totalTaxPrice、优惠金额 discountPrice（= 合计 × 优惠率）、最终 totalPrice（= 产品合计 + 税额合计 - 优惠金额），插入订单表。
6. 为订单项回填 orderId 后批量插入订单项表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_100_000 | 供应商({})未启用 |
| 1_030_101_004 | 生成采购单号失败，请重新提交 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 2.2 更新采购订单

- **路径**: PUT /erp/purchase-order/update
- **权限**: erp:purchase-order:update
- **说明**: 更新未审核状态的采购订单及其订单项。

**请求参数 (ErpPurchaseOrderSaveReqVO)**: 同 2.1，此时 id 必传。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 校验订单存在，不存在抛 PURCHASE_ORDER_NOT_EXISTS。
2. 若订单已审核（APPROVE），抛 PURCHASE_ORDER_UPDATE_FAIL_APPROVE，禁止修改。
3. 校验供应商有效；若传了 accountId 则校验结算账户。
4. 校验订单项有效性（同 2.1 第 1 步）。
5. 重新计算各合计金额后更新订单。
6. 对比新旧订单项列表做 diff：新增项批量插入、已有项批量更新、被移除项批量删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_101_000 | 采购订单不存在 |
| 1_030_101_005 | 采购订单({})已审核，无法修改 |
| 1_030_100_000 | 供应商({})未启用 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 2.3 更新采购订单的状态

- **路径**: PUT /erp/purchase-order/update-status
- **权限**: erp:purchase-order:update-status
- **说明**: 审核或反审核采购订单。

**请求参数**: Query 参数
- `id`（Long，必填，订单编号）
- `status`（Integer，必填，目标状态：20 审核 / 10 反审核）

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 校验订单存在。
2. 校验目标状态与当前状态不同，相同则抛 PURCHASE_ORDER_APPROVE_FAIL（审核）或 PURCHASE_ORDER_PROCESS_FAIL（反审核）。
3. 反审核时校验：订单已有入库数量（inCount > 0）抛 PURCHASE_ORDER_PROCESS_FAIL_EXISTS_IN；已有退货数量（returnCount > 0）抛 PURCHASE_ORDER_PROCESS_FAIL_EXISTS_RETURN。
4. 使用 `updateByIdAndStatus`（带旧状态条件的乐观更新）更新状态，更新行数为 0 时抛对应审核/反审核失败错误码。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_101_000 | 采购订单不存在 |
| 1_030_101_002 | 反审核失败，只有已审核的采购订单才能反审核 |
| 1_030_101_003 | 审核失败，只有未审核的采购订单才能审核 |
| 1_030_101_008 | 反审核失败，已存在对应的采购入库单 |
| 1_030_101_010 | 反审核失败，已存在对应的采购退货单 |

### 2.4 删除采购订单

- **路径**: DELETE /erp/purchase-order/delete
- **权限**: erp:purchase-order:delete
- **说明**: 批量删除采购订单（含订单项），仅限未审核订单。

**请求参数**: Query 参数 `ids`（List&lt;Long&gt;，必填，订单编号数组）。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 按编号批量查询订单，为空直接返回。
2. 遍历校验：任一订单已审核（APPROVE）则抛 PURCHASE_ORDER_DELETE_FAIL_APPROVE。
3. 逐个删除订单主表记录及其全部订单项。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_101_001 | 采购订单({})已审核，无法删除 |

### 2.5 获得采购订单详情

- **路径**: GET /erp/purchase-order/get
- **权限**: erp:purchase-order:query
- **说明**: 查询订单详情，含订单项及产品、库存等关联信息。

**请求参数**: Query 参数 `id`（Long，必填，订单编号）。

**响应**: `CommonResult<ErpPurchaseOrderRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 采购单编号 |
| status | Integer | 采购状态（10 未审核 / 20 已审核） |
| supplierId | Long | 供应商编号 |
| supplierName | String | 供应商名称 |
| accountId | Long | 结算账户编号 |
| orderTime | LocalDateTime | 采购时间 |
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
| productNames | String | 产品信息（订单项产品名拼接） |
| inCount | BigDecimal | 采购入库数量 |
| returnCount | BigDecimal | 采购退货数量 |

Item 子对象：

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
| inCount | BigDecimal | 该项已入库数量 |
| returnCount | BigDecimal | 该项已退货数量 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 库存数量（该产品总库存，仅详情/编辑时使用） |

**业务逻辑**:
1. 按 id 查询订单，不存在返回 null 数据。
2. 查询该订单的全部订单项。
3. 批量查询订单项涉及产品的信息 Map。
4. 为每个订单项填充当前产品总库存 stockCount（无库存记录时置 0）以及产品名称/条码/单位名称。

### 2.6 获得采购订单分页

- **路径**: GET /erp/purchase-order/page
- **权限**: erp:purchase-order:query
- **说明**: 分页查询采购订单，附带订单项、产品、供应商、创建人信息。

**请求参数 (ErpPurchaseOrderPageReqVO)**: 继承 PageParam（`pageNo`、`pageSize`）。类内定义入库/退货状态常量：`IN_STATUS_NONE=0 / PART=1 / ALL=2`、`RETURN_STATUS_NONE=0 / PART=1 / ALL=2`。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | | 页码 |
| pageSize | Integer | 是 | | 每页条数 |
| no | String | 否 | | 采购单编号 |
| supplierId | Long | 否 | | 供应商编号 |
| orderTime | LocalDateTime[] | 否 | | 采购时间范围（格式 yyyy-MM-dd HH:mm:ss） |
| remark | String | 否 | | 备注 |
| status | Integer | 否 | | 采购状态 |
| creator | String | 否 | | 创建者 |
| productId | Long | 否 | | 产品编号 |
| inStatus | Integer | 否 | | 入库状态（0 无 / 1 部分 / 2 全部） |
| returnStatus | Integer | 否 | | 退货状态（0 无 / 1 部分 / 2 全部） |
| inEnable | Boolean | 否 | | 是否可入库 |
| returnEnable | Boolean | 否 | | 是否可退货 |

**响应**: `CommonResult<PageResult<ErpPurchaseOrderRespVO>>` — 字段同 2.5 的 RespVO 表。

**业务逻辑**:
1. 分页查询订单主表。
2. 批量查询订单项，按 orderId 分组；批量查询产品信息、供应商信息、创建人（AdminUserApi）信息。
3. 拼接每个订单：填充订单项的产品名称/条码/单位名称、productNames（产品名以"，"拼接）、supplierName、creatorName。

### 2.7 导出采购订单 Excel

- **路径**: GET /erp/purchase-order/export-excel
- **权限**: erp:purchase-order:export
- **说明**: 按分页条件导出采购订单 Excel（采购订单.xls），数据组装逻辑与分页一致。

**请求参数 (ErpPurchaseOrderPageReqVO)**: 同 2.6（服务端强制 pageSize = PAGE_SIZE_NONE 全量导出）。

**响应**: 无 CommonResult，直接输出 Excel 文件流（列来自 ErpPurchaseOrderRespVO 的 @ExcelProperty 注解）。

**业务逻辑**: 1. pageSize 置为不分页；2. 复用分页查询与 VO 组装逻辑取全量数据；3. 通过 ExcelUtils 写出文件；4. 记录导出操作日志（@ApiAccessLog EXPORT）。

---

## 3. 采购入库（/erp/purchase-in）

### 3.1 创建采购入库

- **路径**: POST /erp/purchase-in/create
- **权限**: erp:purchase-in:create
- **说明**: 基于已审核的采购订单创建采购入库单（初始未审核），返回入库单编号。

**请求参数 (ErpPurchaseInSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（新增时不传） |
| accountId | Long | 否 | | 结算账户编号 |
| inTime | LocalDateTime | 是 | @NotNull | 入库时间 |
| orderId | Long | 是 | @NotNull | 采购订单编号 |
| discountPercent | BigDecimal | 否 | | 优惠率，百分比 |
| otherPrice | BigDecimal | 否 | | 其它金额，单位：元 |
| fileUrl | String | 否 | | 附件地址 |
| remark | String | 否 | | 备注 |
| items | List&lt;Item&gt; | 否 | @Valid | 入库清单列表 |

Item 子对象：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 入库项编号 |
| orderItemId | Long | 是 | @NotNull | 采购订单项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productUnitId | Long | 是 | @NotNull | 产品单位编号 |
| productPrice | BigDecimal | 否 | | 产品单价 |
| count | BigDecimal | 是 | @NotNull、@DecimalMin(value = "0", inclusive = false) | 产品数量（必须大于 0） |
| taxPercent | BigDecimal | 否 | | 税率，百分比 |
| remark | String | 否 | | 备注 |

**响应**: `CommonResult<Long>` — 新创建的入库单编号。

**业务逻辑**:
1. 校验关联采购订单已审核（存在且状态为 APPROVE），否则抛 PURCHASE_ORDER_NOT_EXISTS / PURCHASE_ORDER_NOT_APPROVE。
2. 校验入库项有效性：产品存在并启用，补全 productUnitId，计算 totalPrice 与 taxPrice。
3. 校验结算账户有效。
4. 生成入库单号（PURCHASE_IN_NO_PREFIX），重复则抛 PURCHASE_IN_NO_EXISTS。
5. 组装入库单 DO：状态置为未审核，从采购订单取 orderNo、supplierId；计算 totalCount、totalProductPrice、totalTaxPrice、discountPrice、最终 totalPrice（产品合计 + 税额 - 优惠 + 其它金额），插入入库单；回填 inId 后批量插入入库项。
6. 重算并更新采购订单的入库数量：按已审核入库单汇总各项入库数回写订单项/订单，且校验全部入库单占用数量不得超过订单项数量，超过抛 PURCHASE_ORDER_ITEM_IN_FAIL_PRODUCT_EXCEED。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_101_000 | 采购订单不存在 |
| 1_030_101_006 | 采购订单未审核，无法操作 |
| 1_030_101_007 | 采购订单项({})超过最大允许入库数量({}) |
| 1_030_102_004 | 生成入库单失败，请重新提交 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 3.2 更新采购入库

- **路径**: PUT /erp/purchase-in/update
- **权限**: erp:purchase-in:update
- **说明**: 更新未审核状态的入库单及其入库项。

**请求参数 (ErpPurchaseInSaveReqVO)**: 同 3.1，此时 id 必传。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 校验入库单存在，不存在抛 PURCHASE_IN_NOT_EXISTS。
2. 若已审核（APPROVE），抛 PURCHASE_IN_UPDATE_FAIL_APPROVE，禁止修改。
3. 校验关联采购订单已审核、结算账户有效、入库项有效（同 3.1）。
4. 重新计算金额后更新入库单；diff 方式更新入库项（增/改/删）。
5. 更新新关联采购订单的入库数量。
6. 若订单编号发生变更，同步重算并更新"老"采购订单的入库数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_102_000 | 采购入库单不存在 |
| 1_030_102_005 | 采购入库单({})已审核，无法修改 |
| 1_030_101_006 | 采购订单未审核，无法操作 |
| 1_030_101_007 | 采购订单项({})超过最大允许入库数量({}) |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 3.3 更新采购入库的状态

- **路径**: PUT /erp/purchase-in/update-status
- **权限**: erp:purchase-in:update-status
- **说明**: 审核或反审核入库单；审核时增加库存，反审核时扣减库存并回滚订单入库进度。

**请求参数**: Query 参数
- `id`（Long，必填，入库单编号）
- `status`（Integer，必填，目标状态：20 审核 / 10 反审核）

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 校验入库单存在。
2. 校验目标状态与当前状态不同，相同抛 PURCHASE_IN_APPROVE_FAIL / PURCHASE_IN_PROCESS_FAIL。
3. 反审核时校验已有付款金额（paymentPrice > 0），有则抛 PURCHASE_IN_PROCESS_FAIL_EXISTS_PAYMENT。
4. 通过 `updateByIdAndStatus` 乐观更新状态，失败抛对应错误码。
5. 变更库存：逐个入库项创建库存记录（审核为 PURCHASE_IN 正数入库，反审核为 PURCHASE_IN_CANCEL 负数出库），底层校验仓库库存不足时抛 STOCK_COUNT_NEGATIVE / STOCK_COUNT_NEGATIVE2。
6. 重算并更新采购订单的入库数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_102_000 | 采购入库单不存在 |
| 1_030_102_002 | 反审核失败，只有已审核的入库单才能反审核 |
| 1_030_102_003 | 审核失败，只有未审核的入库单才能审核 |
| 1_030_102_008 | 反审核失败，已存在对应的付款单 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |

### 3.4 删除采购入库

- **路径**: DELETE /erp/purchase-in/delete
- **权限**: erp:purchase-in:delete
- **说明**: 批量删除未审核的采购入库单。

**请求参数**: Query 参数 `ids`（List&lt;Long&gt;，必填，入库单编号数组）。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 批量查询入库单，为空直接返回。
2. 遍历校验：任一单据已审核则抛 PURCHASE_IN_DELETE_FAIL_APPROVE。
3. 逐个删除入库单主表与入库项，并重算对应采购订单的入库数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_102_001 | 采购入库单({})已审核，无法删除 |

### 3.5 获得采购入库详情

- **路径**: GET /erp/purchase-in/get
- **权限**: erp:purchase-in:query
- **说明**: 查询入库单详情，含入库项、产品与"产品 + 仓库"维度库存。

**请求参数**: Query 参数 `id`（Long，必填，入库单编号）。

**响应**: `CommonResult<ErpPurchaseInRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 入库单编号 |
| status | Integer | 入库状态（10 未审核 / 20 已审核） |
| supplierId | Long | 供应商编号 |
| supplierName | String | 供应商名称 |
| accountId | Long | 结算账户编号 |
| inTime | LocalDateTime | 入库时间 |
| orderId | Long | 采购订单编号 |
| orderNo | String | 采购订单号 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 最终合计价格 |
| paymentPrice | BigDecimal | 已付款金额，单位：元 |
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
| items | List&lt;Item&gt; | 入库项列表 |
| productNames | String | 产品信息（入库项产品名拼接） |

Item 子对象：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 入库项编号 |
| orderItemId | Long | 采购订单项编号 |
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
| stockCount | BigDecimal | 库存数量（该产品在该仓库的库存，仅详情/编辑时使用） |

**业务逻辑**:
1. 按 id 查询入库单，不存在返回 null 数据。
2. 查询全部入库项与涉及产品的信息 Map。
3. 为每个入库项查询"产品 + 仓库"维度的库存 ErpStockDO，填充 stockCount（无记录置 0），并补充产品名称/条码/单位名称。

### 3.6 获得采购入库分页

- **路径**: GET /erp/purchase-in/page
- **权限**: erp:purchase-in:query
- **说明**: 分页查询采购入库单，附带入库项、产品、供应商、创建人信息。

**请求参数 (ErpPurchaseInPageReqVO)**: 继承 PageParam（`pageNo`、`pageSize`）。类内定义付款状态常量：`PAYMENT_STATUS_NONE=0 / PART=1 / ALL=2`。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | | 页码 |
| pageSize | Integer | 是 | | 每页条数 |
| no | String | 否 | | 入库单编号 |
| supplierId | Long | 否 | | 供应商编号 |
| inTime | LocalDateTime[] | 否 | | 入库时间范围 |
| remark | String | 否 | | 备注 |
| status | Integer | 否 | | 入库状态 |
| creator | String | 否 | | 创建者 |
| productId | Long | 否 | | 产品编号 |
| warehouseId | Long | 否 | | 仓库编号 |
| accountId | Long | 否 | | 结算账户编号 |
| paymentStatus | Integer | 否 | | 付款状态（0 未付 / 1 部分 / 2 全部） |
| paymentEnable | Boolean | 否 | | 是否可付款（对应 paymentStatus = [0, 1]） |
| orderNo | String | 否 | | 采购订单号 |

**响应**: `CommonResult<PageResult<ErpPurchaseInRespVO>>` — 字段同 3.5 的 RespVO 表。

**业务逻辑**:
1. 分页查询入库单主表。
2. 批量查询入库项、产品、供应商、创建人信息。
3. 拼接每个入库单：入库项产品信息、productNames、supplierName、creatorName。

### 3.7 导出采购入库 Excel

- **路径**: GET /erp/purchase-in/export-excel
- **权限**: erp:purchase-in:export
- **说明**: 按分页条件导出采购入库 Excel（采购入库.xls）。

**请求参数 (ErpPurchaseInPageReqVO)**: 同 3.6（pageSize 强制为不分页）。

**响应**: 无 CommonResult，直接输出 Excel 文件流（列来自 ErpPurchaseInRespVO 的 @ExcelProperty 注解）。

**业务逻辑**: 1. pageSize 置为不分页；2. 复用分页查询与 VO 组装取全量数据；3. ExcelUtils 写出文件；4. 记录导出操作日志（@ApiAccessLog EXPORT）。

---

## 4. 采购退货（/erp/purchase-return）

### 4.1 创建采购退货

- **路径**: POST /erp/purchase-return/create
- **权限**: erp:purchase-return:create
- **说明**: 基于已审核的采购订单创建采购退货单（初始未审核），返回退货单编号。

**请求参数 (ErpPurchaseReturnSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（新增时不传） |
| accountId | Long | 否 | | 结算账户编号 |
| returnTime | LocalDateTime | 是 | @NotNull | 退货时间 |
| orderId | Long | 是 | @NotNull | 采购订单编号 |
| discountPercent | BigDecimal | 否 | | 优惠率，百分比 |
| otherPrice | BigDecimal | 否 | | 其它金额，单位：元 |
| fileUrl | String | 否 | | 附件地址 |
| remark | String | 否 | | 备注 |
| items | List&lt;Item&gt; | 否 | | 退货清单列表 |

Item 子对象：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 退货项编号 |
| orderItemId | Long | 是 | @NotNull | 采购订单项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productUnitId | Long | 是 | @NotNull | 产品单位编号 |
| productPrice | BigDecimal | 否 | | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| taxPercent | BigDecimal | 否 | | 税率，百分比 |
| remark | String | 否 | | 备注 |

**响应**: `CommonResult<Long>` — 新创建的退货单编号。

**业务逻辑**:
1. 校验关联采购订单已审核，否则抛 PURCHASE_ORDER_NOT_EXISTS / PURCHASE_ORDER_NOT_APPROVE。
2. 校验退货项有效性：产品存在并启用，补全 productUnitId，计算 totalPrice 与 taxPrice。
3. 校验结算账户有效。
4. 生成退货单号（PURCHASE_RETURN_NO_PREFIX），重复则抛 PURCHASE_RETURN_NO_EXISTS。
5. 组装退货单 DO：状态置为未审核，从采购订单取 orderNo、supplierId；计算各合计金额与最终 totalPrice（产品合计 + 税额 - 优惠 + 其它金额），插入退货单；回填 returnId 后批量插入退货项。
6. 汇总该订单全部退货单的退货数量，更新采购订单的退货数量（订单项退货数不得超过其入库数，超过抛 PURCHASE_ORDER_ITEM_RETURN_FAIL_IN_EXCEED）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_101_000 | 采购订单不存在 |
| 1_030_101_006 | 采购订单未审核，无法操作 |
| 1_030_101_009 | 采购订单项({})超过最大允许退货数量({}) |
| 1_030_103_004 | 生成退货单失败，请重新提交 |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 4.2 更新采购退货

- **路径**: PUT /erp/purchase-return/update
- **权限**: erp:purchase-return:update
- **说明**: 更新未审核状态的退货单及其退货项。

**请求参数 (ErpPurchaseReturnSaveReqVO)**: 同 4.1，此时 id 必传。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 校验退货单存在，不存在抛 PURCHASE_RETURN_NOT_EXISTS。
2. 若已审核（APPROVE），抛 PURCHASE_RETURN_UPDATE_FAIL_APPROVE，禁止修改。
3. 校验关联采购订单已审核、结算账户有效、退货项有效（同 4.1）。
4. 重新计算金额后更新退货单；diff 方式更新退货项（增/改/删）。
5. 更新新关联采购订单的退货数量。
6. 若订单编号变更，同步重算并更新"老"采购订单的退货数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_103_000 | 采购退货单不存在 |
| 1_030_103_005 | 采购退货单({})已审核，无法修改 |
| 1_030_101_006 | 采购订单未审核，无法操作 |
| 1_030_101_009 | 采购订单项({})超过最大允许退货数量({}) |
| 1_030_500_000 | 产品不存在 |
| 1_030_500_001 | 产品({})未启用 |

### 4.3 更新采购退货的状态

- **路径**: PUT /erp/purchase-return/update-status
- **权限**: erp:purchase-return:update-status
- **说明**: 审核或反审核退货单；审核时按退货数量扣减库存，反审核时回加库存。

**请求参数**: Query 参数
- `id`（Long，必填，退货单编号）
- `status`（Integer，必填，目标状态：20 审核 / 10 反审核）

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 校验退货单存在。
2. 校验目标状态与当前状态不同，相同抛 PURCHASE_RETURN_APPROVE_FAIL / PURCHASE_RETURN_PROCESS_FAIL。
3. 反审核时校验已有退款金额（refundPrice > 0），有则抛 PURCHASE_RETURN_PROCESS_FAIL_EXISTS_REFUND。
4. 通过 `updateByIdAndStatus` 乐观更新状态，失败抛对应错误码。
5. 变更库存：逐个退货项创建库存记录（审核为 PURCHASE_RETURN 负数出库，反审核为 PURCHASE_RETURN_CANCEL 正数回加），库存不足时底层抛 STOCK_COUNT_NEGATIVE / STOCK_COUNT_NEGATIVE2。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_103_000 | 采购退货单不存在 |
| 1_030_103_002 | 反审核失败，只有已审核的退货单才能反审核 |
| 1_030_103_003 | 审核失败，只有未审核的退货单才能审核 |
| 1_030_103_008 | 反审核失败，已存在对应的退款单 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |

### 4.4 删除采购退货

- **路径**: DELETE /erp/purchase-return/delete
- **权限**: erp:purchase-return:delete
- **说明**: 批量删除未审核的采购退货单。

**请求参数**: Query 参数 `ids`（List&lt;Long&gt;，必填，退货单编号数组）。

**响应**: `CommonResult<Boolean>` — 固定返回 true。

**业务逻辑**:
1. 批量查询退货单，为空直接返回。
2. 遍历校验：任一单据已审核则抛 PURCHASE_RETURN_DELETE_FAIL_APPROVE。
3. 逐个删除退货单主表与退货项，并重算对应采购订单的退货数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_103_001 | 采购退货单({})已审核，无法删除 |

### 4.5 获得采购退货详情

- **路径**: GET /erp/purchase-return/get
- **权限**: erp:purchase-return:query
- **说明**: 查询退货单详情，含退货项、产品与"产品 + 仓库"维度库存。

**请求参数**: Query 参数 `id`（Long，必填，退货单编号）。

**响应**: `CommonResult<ErpPurchaseReturnRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 退货单编号 |
| status | Integer | 退货状态（10 未审核 / 20 已审核） |
| supplierId | Long | 供应商编号 |
| supplierName | String | 供应商名称 |
| accountId | Long | 结算账户编号 |
| returnTime | LocalDateTime | 退货时间 |
| orderId | Long | 采购订单编号 |
| orderNo | String | 采购订单号 |
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
| productNames | String | 产品信息（退货项产品名拼接） |

Item 子对象：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 退货项编号 |
| orderItemId | Long | 采购订单项编号 |
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
| stockCount | BigDecimal | 库存数量（该产品在该仓库的库存，仅详情/编辑时使用） |

**业务逻辑**:
1. 按 id 查询退货单，不存在返回 null 数据。
2. 查询全部退货项与涉及产品的信息 Map。
3. 为每个退货项查询"产品 + 仓库"维度库存，填充 stockCount（无记录置 0），并补充产品名称/条码/单位名称。

### 4.6 获得采购退货分页

- **路径**: GET /erp/purchase-return/page
- **权限**: erp:purchase-return:query
- **说明**: 分页查询采购退货单，附带退货项、产品、供应商、创建人信息。

**请求参数 (ErpPurchaseReturnPageReqVO)**: 继承 PageParam（`pageNo`、`pageSize`）。类内定义退款状态常量：`REFUND_STATUS_NONE=0 / PART=1 / ALL=2`。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | | 页码 |
| pageSize | Integer | 是 | | 每页条数 |
| no | String | 否 | | 退货单编号 |
| supplierId | Long | 否 | | 供应商编号 |
| returnTime | LocalDateTime[] | 否 | | 退货时间范围 |
| remark | String | 否 | | 备注 |
| status | Integer | 否 | | 退货状态 |
| creator | String | 否 | | 创建者 |
| productId | Long | 否 | | 产品编号 |
| warehouseId | Long | 否 | | 仓库编号 |
| accountId | Long | 否 | | 结算账户编号 |
| orderNo | String | 否 | | 采购订单号 |
| refundStatus | Integer | 否 | | 退款状态（0 未退 / 1 部分 / 2 全部） |
| refundEnable | Boolean | 否 | | 是否可退款（对应 refundStatus = [0, 1]） |

**响应**: `CommonResult<PageResult<ErpPurchaseReturnRespVO>>` — 字段同 4.5 的 RespVO 表。

**业务逻辑**:
1. 分页查询退货单主表。
2. 批量查询退货项、产品、供应商、创建人信息。
3. 拼接每个退货单：退货项产品信息、productNames、supplierName、creatorName。

### 4.7 导出采购退货 Excel

- **路径**: GET /erp/purchase-return/export-excel
- **权限**: erp:purchase-return:export
- **说明**: 按分页条件导出采购退货 Excel（采购退货.xls）。

**请求参数 (ErpPurchaseReturnPageReqVO)**: 同 4.6（pageSize 强制为不分页）。

**响应**: 无 CommonResult，直接输出 Excel 文件流（列来自 ErpPurchaseReturnRespVO 的 @ExcelProperty 注解）。

**业务逻辑**: 1. pageSize 置为不分页；2. 复用分页查询与 VO 组装取全量数据；3. ExcelUtils 写出文件；4. 记录导出操作日志（@ApiAccessLog EXPORT）。

---

## 附：采购域相关错误码汇总（ErrorCodeConstants）

| 错误码 | 说明 |
|-------|------|
| 1_030_100_000 | 供应商不存在 / 供应商({})未启用（两个常量共用该编号） |
| 1_030_101_000 | 采购订单不存在 |
| 1_030_101_001 | 采购订单({})已审核，无法删除 |
| 1_030_101_002 | 反审核失败，只有已审核的采购订单才能反审核 |
| 1_030_101_003 | 审核失败，只有未审核的采购订单才能审核 |
| 1_030_101_004 | 生成采购单号失败，请重新提交 |
| 1_030_101_005 | 采购订单({})已审核，无法修改 |
| 1_030_101_006 | 采购订单未审核，无法操作 |
| 1_030_101_007 | 采购订单项({})超过最大允许入库数量({}) |
| 1_030_101_008 | 反审核失败，已存在对应的采购入库单 |
| 1_030_101_009 | 采购订单项({})超过最大允许退货数量({}) |
| 1_030_101_010 | 反审核失败，已存在对应的采购退货单 |
| 1_030_102_000 | 采购入库单不存在 |
| 1_030_102_001 | 采购入库单({})已审核，无法删除 |
| 1_030_102_002 | 反审核失败，只有已审核的入库单才能反审核 |
| 1_030_102_003 | 审核失败，只有未审核的入库单才能审核 |
| 1_030_102_004 | 生成入库单失败，请重新提交 |
| 1_030_102_005 | 采购入库单({})已审核，无法修改 |
| 1_030_102_006 | 采购入库单未审核，无法操作 |
| 1_030_102_007 | 付款金额({})超过采购入库单总金额({}) |
| 1_030_102_008 | 反审核失败，已存在对应的付款单 |
| 1_030_103_000 | 采购退货单不存在 |
| 1_030_103_001 | 采购退货单({})已审核，无法删除 |
| 1_030_103_002 | 反审核失败，只有已审核的退货单才能反审核 |
| 1_030_103_003 | 审核失败，只有未审核的退货单才能审核 |
| 1_030_103_004 | 生成退货单失败，请重新提交 |
| 1_030_103_005 | 采购退货单({})已审核，无法修改 |
| 1_030_103_006 | 采购退货单未审核，无法操作 |
| 1_030_103_007 | 退款金额({})超过采购退货单总金额({}) |
| 1_030_103_008 | 反审核失败，已存在对应的退款单 |
| 1_030_500_002 | 产品已被采购订单引用，无法删除 |
| 1_030_500_003 | 产品已被采购入库单引用，无法删除 |
| 1_030_500_004 | 产品已被采购退货单引用，无法删除 |
