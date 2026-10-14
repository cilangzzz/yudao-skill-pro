# 业务单据接口（入库/出库/移库/盘库）

> WMS 业务单据域覆盖四类核心库存单据：入库单（增加库存）、出库单（扣减库存）、移库单（跨仓移动库存）、盘库单（按实盘数校准库存）。每类单据均为"单头 + 明细"结构，遵循统一的单据状态机（草稿 → 已完成 / 已作废），创建与更新仅允许草稿态，完成单据时在事务内调用库存域写入库存变动。

## 接口路径前缀

- /wms/receipt-order (Controller: WmsReceiptOrderController) —— 入库单
- /wms/receipt-order-detail (Controller: WmsReceiptOrderDetailController) —— 入库单明细
- /wms/shipment-order (Controller: WmsShipmentOrderController) —— 出库单
- /wms/shipment-order-detail (Controller: WmsShipmentOrderDetailController) —— 出库单明细
- /wms/movement-order (Controller: WmsMovementOrderController) —— 移库单
- /wms/movement-order-detail (Controller: WmsMovementOrderDetailController) —— 移库单明细
- /wms/check-order (Controller: WmsCheckOrderController) —— 盘库单
- /wms/check-order-detail (Controller: WmsCheckOrderDetailController) —— 盘库单明细

**单据状态枚举（WmsOrderStatusEnum，四类单据通用）**: `0` 草稿（PREPARE）、`4` 已完成（FINISHED）、`5` 已作废（CANCELED）

**入库类型枚举（WmsReceiptOrderTypeEnum）**: `100` 生产入库、`101` 采购入库、`102` 退货入库、`103` 归还入库

**出库类型枚举（WmsShipmentOrderTypeEnum）**: `200` 退货出库、`201` 销售出库、`202` 生产出库

---

## 1. 入库单（WmsReceiptOrderController）

### 1.1 创建入库单

- **路径**: POST /wms/receipt-order/create
- **权限**: wms:receipt-order:create
- **说明**: 创建入库单（状态为草稿），同时保存入库明细。

**请求参数 (WmsReceiptOrderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 编号（创建时不传） |
| no | String | 是 | @NotBlank；@Size(max=64) | 入库单号，如 RK202605110001，全局唯一 |
| type | Integer | 是 | @NotNull；@InEnum(WmsReceiptOrderTypeEnum) | 入库类型：100 生产入库 / 101 采购入库 / 102 退货入库 / 103 归还入库 |
| orderTime | LocalDateTime | 是 | @NotNull | 单据日期 |
| bizOrderNo | String | 否 | @Size(max=64) | 关联业务单号，如采购单号 |
| merchantId | Long | 否 | — | 供应商编号（传入时校验必须为供应商或客户/供应商类型） |
| remark | String | 否 | @Size(max=255) | 备注 |
| warehouseId | Long | 是 | @NotNull | 入库仓库编号 |
| details | List\<WmsReceiptOrderDetailSaveReqVO\> | 否 | @Valid 级联校验 | 入库明细列表，元素字段见下表 |

**明细元素 (WmsReceiptOrderDetailSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 明细编号 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号（校验 SKU 存在） |
| quantity | BigDecimal | 是 | @NotNull；@DecimalMin(value="0", inclusive=false) | 入库数量，必须大于 0 |
| price | BigDecimal | 否 | @DecimalMin(value="0") | 单价 |
| totalPrice | BigDecimal | 否 | @DecimalMin(value="0") | 行金额（不传时按 price × quantity 计算） |

**响应**: CommonResult\<Long\>（新入库单编号）

**业务逻辑**:
1. 校验保存数据：入库单号唯一（重复抛 RECEIPT_ORDER_NO_DUPLICATE）；校验仓库存在；merchantId 非空时校验供应商类型（必须是供应商或客户/供应商类型）。
2. 将 VO 转换为 DO，状态置为草稿（PREPARE = 0）。
3. 汇总明细填充 totalQuantity（Σ入库数量）与 totalPrice（Σ行金额，行金额优先取传入 totalPrice，否则按 price × quantity 计算）。
4. 插入入库单主表。
5. 逐条校验明细 SKU 存在，明细 warehouseId 统一取单头仓库，行金额为空时自动按 price × quantity 补齐，批量插入入库单明细表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_200_001 | 入库单号重复 |
| 1_060_100_000 | 仓库不存在 |
| 1_060_105_001 | 往来企业必须是供应商或客户/供应商类型 |
| 1_060_104_004 | 商品规格不存在（明细 SKU 校验） |

### 1.2 更新入库单

- **路径**: PUT /wms/receipt-order/update
- **权限**: wms:receipt-order:update
- **说明**: 更新草稿态入库单及其明细（整体覆盖式更新明细）。

**请求参数 (WmsReceiptOrderSaveReqVO)**: 字段同 1.1（此时 id 必传，作为更新目标）。

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验入库单存在且为草稿状态（不存在抛 RECEIPT_ORDER_NOT_EXISTS，非草稿抛 RECEIPT_ORDER_STATUS_NOT_PREPARE）。
2. 校验保存数据：单号唯一、仓库存在、供应商类型（同创建）。
3. 以"状态 = 草稿"为条件乐观更新主表（updateByIdAndStatus），更新行数为 0 时抛 RECEIPT_ORDER_STATUS_NOT_PREPARE；重新汇总 totalQuantity/totalPrice。
4. 更新明细：查询旧明细列表，与新明细按 id 对比（diffList）拆分为新增/修改/删除三部分；新增明细携带非空 id 时抛 RECEIPT_ORDER_DETAIL_NOT_EXISTS，随后分别批量插入、更新、删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_200_000 | 入库单不存在 |
| 1_060_200_002 | 入库单状态不是草稿，不能操作 |
| 1_060_200_001 | 入库单号重复 |
| 1_060_200_007 | 入库单明细不存在（明细 diff 更新时 id 异常） |

### 1.3 删除入库单

- **路径**: DELETE /wms/receipt-order/delete
- **权限**: wms:receipt-order:delete
- **说明**: 删除草稿或已作废状态的入库单及其明细。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 入库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验入库单存在（不存在抛 RECEIPT_ORDER_NOT_EXISTS）。
2. 校验状态为草稿（0）或已作废（5），否则抛 RECEIPT_ORDER_STATUS_NOT_DELETABLE。
3. 删除入库单主表记录。
4. 按入库单编号删除全部入库单明细。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_200_000 | 入库单不存在 |
| 1_060_200_005 | 入库单状态不是草稿或已作废，不能删除 |

### 1.4 完成入库

- **路径**: PUT /wms/receipt-order/complete
- **权限**: wms:receipt-order:complete
- **说明**: 将草稿入库单置为已完成，并按明细增加库存。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 入库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验入库单存在且为草稿状态。
2. 校验入库单明细存在（至少一条，否则抛 RECEIPT_ORDER_DETAIL_REQUIRED）。
3. 以"状态 = 草稿"为条件乐观更新状态为已完成（FINISHED = 4），更新行数为 0 时抛 RECEIPT_ORDER_STATUS_NOT_PREPARE。
4. 在同一事务内将明细转换为库存变更项（数量为正数、金额为行金额），调用库存域 changeInventory 批量增加库存，库存变更记录的单据类型为入库（RECEIPT）；库存不足等异常由库存域抛出并回滚整个事务。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_200_000 | 入库单不存在 |
| 1_060_200_002 | 入库单状态不是草稿，不能操作 |
| 1_060_200_003 | 入库单至少包含一条明细 |
| 1_060_300_000 | 库存不足，商品：{}，商品规格：{}，仓库：{}，当前库存：{}，变更数量：{}（由库存域抛出） |

### 1.5 作废入库单

- **路径**: PUT /wms/receipt-order/cancel
- **权限**: wms:receipt-order:cancel
- **说明**: 将草稿入库单作废（作废后不可再操作，仅可删除）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 入库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验入库单存在且为草稿状态。
2. 以"状态 = 草稿"为条件乐观更新状态为已作废（CANCELED = 5），更新行数为 0 时抛 RECEIPT_ORDER_STATUS_NOT_PREPARE。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_200_000 | 入库单不存在 |
| 1_060_200_002 | 入库单状态不是草稿，不能操作 |

### 1.6 获得入库单

- **路径**: GET /wms/receipt-order/get
- **权限**: wms:receipt-order:query
- **说明**: 获得入库单详情，含全部入库明细及关联的供应商/仓库/操作人名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 入库单编号 |

**响应**: CommonResult\<WmsReceiptOrderRespVO\>（单据不存在时返回 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 入库单号 |
| type | Integer | 入库类型（100 生产入库 / 101 采购入库 / 102 退货入库 / 103 归还入库） |
| orderTime | LocalDateTime | 单据日期 |
| status | Integer | 入库状态（0 草稿 / 4 已完成 / 5 已作废） |
| bizOrderNo | String | 业务单号 |
| merchantId | Long | 供应商编号 |
| merchantName | String | 供应商名称（关联填充） |
| remark | String | 备注 |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称（关联填充） |
| totalQuantity | BigDecimal | 入库数量（明细汇总） |
| totalPrice | BigDecimal | 总金额（明细汇总） |
| details | List\<WmsReceiptOrderDetailRespVO\> | 入库明细列表，元素字段同 2.1 |
| createTime | LocalDateTime | 创建时间 |
| creator | String | 创建者 |
| creatorName | String | 创建者名称（关联填充） |
| updateTime | LocalDateTime | 更新时间 |
| updater | String | 更新者 |
| updaterName | String | 更新者名称（关联填充） |

**业务逻辑**:
1. 按编号查询入库单，不存在直接返回 null。
2. 查询该入库单的全部明细列表。
3. 批量查询供应商 Map、仓库 Map、创建者/更新者用户 Map。
4. DO 拷贝为 RespVO 并回填 merchantName、warehouseName、creatorName、updaterName。
5. 明细列表按 2.1 的拼接逻辑回填商品/SKU/仓库信息后，设置到 RespVO 的 details 返回。

### 1.7 获得入库单分页

- **路径**: GET /wms/receipt-order/page
- **权限**: wms:receipt-order:query
- **说明**: 分页查询入库单列表，支持单号、状态、仓库、供应商、类型、数量/金额区间等多条件过滤。

**请求参数 (WmsReceiptOrderPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 分页参数（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 分页参数（继承 PageParam） | 每页条数 |
| no | String | 否 | — | 入库单号 |
| status | Integer | 否 | @InEnum(WmsOrderStatusEnum) | 单据状态：0 草稿 / 4 已完成 / 5 已作废 |
| warehouseId | Long | 否 | — | 仓库编号 |
| merchantId | Long | 否 | — | 供应商编号 |
| orderTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 单据日期区间 |
| totalQuantityMin | BigDecimal | 否 | — | 最小入库数量 |
| totalQuantityMax | BigDecimal | 否 | — | 最大入库数量 |
| totalPriceMin | BigDecimal | 否 | — | 最小总金额 |
| totalPriceMax | BigDecimal | 否 | — | 最大总金额 |
| type | Integer | 否 | @InEnum(WmsReceiptOrderTypeEnum) | 入库类型 |
| bizOrderNo | String | 否 | — | 业务单号 |
| creator | String | 否 | — | 创建用户 |
| updater | String | 否 | — | 更新用户 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| updateTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 更新时间区间 |

**响应**: CommonResult\<PageResult\<WmsReceiptOrderRespVO\>\>，元素字段同 1.6 的 WmsReceiptOrderRespVO（不含 details）。

**业务逻辑**:
1. Service 按分页条件查询入库单分页结果。
2. 批量查询供应商 Map、仓库 Map、创建者/更新者用户 Map。
3. DO 列表拷贝为 RespVO 列表并回填 merchantName、warehouseName、creatorName、updaterName 后返回。

### 1.8 导出入库单 Excel

- **路径**: GET /wms/receipt-order/export-excel
- **权限**: wms:receipt-order:export
- **说明**: 按分页查询条件导出全部入库单 Excel（文件名"入库单.xls"），查询条件同 1.7。

**请求参数 (WmsReceiptOrderPageReqVO)**: 同 1.7（pageSize 由服务端强制置为不分页）。

**响应**: Excel 文件流（导出字段为 RespVO 上标注 @ExcelProperty 的列：入库单号、入库类型、单据日期、入库状态、业务单号、供应商、仓库、入库数量、总金额、创建时间）。

**业务逻辑**:
1. 将分页参数 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 按条件查询全部入库单。
3. 批量拼接供应商/仓库/操作人名称后，通过 ExcelUtils 写出 Excel 文件；接口标注 @ApiAccessLog(operateType = EXPORT) 记录导出操作日志。

---

## 2. 入库单明细（WmsReceiptOrderDetailController）

### 2.1 获得入库单明细列表

- **路径**: GET /wms/receipt-order-detail/list-by-order-id
- **权限**: wms:receipt-order:query
- **说明**: 按入库单编号查询全部入库明细，并回填商品/SKU/仓库展示字段。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| orderId | Long | 是 | @RequestParam required | 入库单编号 |

**响应**: CommonResult\<List\<WmsReceiptOrderDetailRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 明细编号 |
| orderId | Long | 入库单编号 |
| itemId | Long | 商品编号（由 SKU 反查填充） |
| itemCode | String | 商品编码（关联填充） |
| itemName | String | 商品名称（关联填充） |
| unit | String | 商品单位（关联填充） |
| skuId | Long | 商品 SKU 编号 |
| skuCode | String | 规格编号（关联填充） |
| skuName | String | 规格名称（关联填充） |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称（关联填充） |
| quantity | BigDecimal | 入库数量 |
| price | BigDecimal | 单价 |
| totalPrice | BigDecimal | 行金额 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. Service 按入库单编号查询明细列表。
2. 批量查询 SKU Map，并由 SKU 的 itemId 集合查询商品 Map、按 warehouseId 查询仓库 Map。
3. DO 拷贝为 RespVO 并回填 skuCode/skuName/itemId、itemCode/itemName/unit、warehouseName 后返回。

---

## 3. 出库单（WmsShipmentOrderController）

### 3.1 创建出库单

- **路径**: POST /wms/shipment-order/create
- **权限**: wms:shipment-order:create
- **说明**: 创建出库单（状态为草稿），同时保存出库明细。

**请求参数 (WmsShipmentOrderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 编号（创建时不传） |
| no | String | 是 | @NotBlank；@Size(max=64) | 出库单号，如 CK202605110001，全局唯一 |
| type | Integer | 是 | @NotNull；@InEnum(WmsShipmentOrderTypeEnum) | 出库类型：200 退货出库 / 201 销售出库 / 202 生产出库 |
| orderTime | LocalDateTime | 是 | @NotNull | 单据日期 |
| bizOrderNo | String | 否 | @Size(max=64) | 关联业务单号，如销售订单号 |
| merchantId | Long | 否 | — | 客户编号（传入时校验必须为客户或客户/供应商类型） |
| remark | String | 否 | @Size(max=255) | 备注 |
| warehouseId | Long | 是 | @NotNull | 出库仓库编号 |
| details | List\<WmsShipmentOrderDetailSaveReqVO\> | 否 | @Valid 级联校验 | 出库明细列表，元素字段见下表 |

**明细元素 (WmsShipmentOrderDetailSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 明细编号 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号（校验 SKU 存在） |
| quantity | BigDecimal | 是 | @NotNull；@DecimalMin(value="0", inclusive=false) | 出库数量，必须大于 0 |
| price | BigDecimal | 否 | @DecimalMin(value="0") | 单价 |
| totalPrice | BigDecimal | 否 | @DecimalMin(value="0") | 行金额（不传时按 price × quantity 计算） |

**响应**: CommonResult\<Long\>（新出库单编号）

**业务逻辑**:
1. 校验保存数据：出库单号唯一（重复抛 SHIPMENT_ORDER_NO_DUPLICATE）；校验仓库存在；merchantId 非空时校验客户类型（必须是客户或客户/供应商类型）。
2. 将 VO 转换为 DO，状态置为草稿（PREPARE = 0）。
3. 汇总明细填充 totalQuantity 与 totalPrice（行金额优先取传入 totalPrice，否则按 price × quantity 计算）。
4. 插入出库单主表。
5. 逐条校验明细 SKU 存在，明细 warehouseId 统一取单头仓库，行金额为空时自动补齐，批量插入出库单明细表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_201_001 | 出库单号重复 |
| 1_060_100_000 | 仓库不存在 |
| 1_060_105_002 | 往来企业必须是客户或客户/供应商类型 |
| 1_060_104_004 | 商品规格不存在（明细 SKU 校验） |

### 3.2 更新出库单

- **路径**: PUT /wms/shipment-order/update
- **权限**: wms:shipment-order:update
- **说明**: 更新草稿态出库单及其明细（整体覆盖式更新明细）。

**请求参数 (WmsShipmentOrderSaveReqVO)**: 字段同 3.1（此时 id 必传）。

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验出库单存在且为草稿状态（不存在抛 SHIPMENT_ORDER_NOT_EXISTS，非草稿抛 SHIPMENT_ORDER_STATUS_NOT_PREPARE）。
2. 校验保存数据：单号唯一、仓库存在、客户类型（同创建）。
3. 以"状态 = 草稿"为条件乐观更新主表，更新行数为 0 时抛 SHIPMENT_ORDER_STATUS_NOT_PREPARE；重新汇总 totalQuantity/totalPrice。
4. 更新明细：新旧明细按 id 对比拆分为新增/修改/删除三部分分别批量处理；新增明细携带非空 id 时抛 SHIPMENT_ORDER_DETAIL_NOT_EXISTS。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_201_000 | 出库单不存在 |
| 1_060_201_002 | 出库单状态不是草稿，不能操作 |
| 1_060_201_001 | 出库单号重复 |
| 1_060_201_007 | 出库单明细不存在（明细 diff 更新时 id 异常） |

### 3.3 删除出库单

- **路径**: DELETE /wms/shipment-order/delete
- **权限**: wms:shipment-order:delete
- **说明**: 删除草稿或已作废状态的出库单及其明细。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 出库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验出库单存在。
2. 校验状态为草稿（0）或已作废（5），否则抛 SHIPMENT_ORDER_STATUS_NOT_DELETABLE。
3. 删除出库单主表记录。
4. 按出库单编号删除全部出库单明细。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_201_000 | 出库单不存在 |
| 1_060_201_005 | 出库单状态不是草稿或已作废，不能删除 |

### 3.4 完成出库

- **路径**: PUT /wms/shipment-order/complete
- **权限**: wms:shipment-order:complete
- **说明**: 将草稿出库单置为已完成，并按明细扣减库存。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 出库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验出库单存在且为草稿状态。
2. 校验出库单明细存在（至少一条，否则抛 SHIPMENT_ORDER_DETAIL_REQUIRED）。
3. 以"状态 = 草稿"为条件乐观更新状态为已完成（FINISHED = 4），更新行数为 0 时抛 SHIPMENT_ORDER_STATUS_NOT_PREPARE。
4. 在同一事务内将明细转换为库存变更项，出库数量与行金额均取负数，调用库存域 changeInventory 批量扣减库存，单据类型为出库（SHIPMENT）；库存不足时由库存域抛出异常并回滚。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_201_000 | 出库单不存在 |
| 1_060_201_002 | 出库单状态不是草稿，不能操作 |
| 1_060_201_003 | 出库单至少包含一条明细 |
| 1_060_300_000 | 库存不足，商品：{}，商品规格：{}，仓库：{}，当前库存：{}，变更数量：{}（由库存域抛出） |

### 3.5 作废出库单

- **路径**: PUT /wms/shipment-order/cancel
- **权限**: wms:shipment-order:cancel
- **说明**: 将草稿出库单作废。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 出库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验出库单存在且为草稿状态。
2. 以"状态 = 草稿"为条件乐观更新状态为已作废（CANCELED = 5），更新行数为 0 时抛 SHIPMENT_ORDER_STATUS_NOT_PREPARE。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_201_000 | 出库单不存在 |
| 1_060_201_002 | 出库单状态不是草稿，不能操作 |

### 3.6 获得出库单

- **路径**: GET /wms/shipment-order/get
- **权限**: wms:shipment-order:query
- **说明**: 获得出库单详情，含全部出库明细及关联的客户/仓库/操作人名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 出库单编号 |

**响应**: CommonResult\<WmsShipmentOrderRespVO\>（单据不存在时返回 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 出库单号 |
| type | Integer | 出库类型（200 退货出库 / 201 销售出库 / 202 生产出库） |
| orderTime | LocalDateTime | 单据日期 |
| status | Integer | 出库状态（0 草稿 / 4 已完成 / 5 已作废） |
| bizOrderNo | String | 业务单号 |
| merchantId | Long | 客户编号 |
| merchantName | String | 客户名称（关联填充） |
| remark | String | 备注 |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称（关联填充） |
| totalQuantity | BigDecimal | 出库数量（明细汇总） |
| totalPrice | BigDecimal | 总金额（明细汇总） |
| details | List\<WmsShipmentOrderDetailRespVO\> | 出库明细列表，元素字段同 4.1 |
| createTime | LocalDateTime | 创建时间 |
| creator | String | 创建者 |
| creatorName | String | 创建者名称（关联填充） |
| updateTime | LocalDateTime | 更新时间 |
| updater | String | 更新者 |
| updaterName | String | 更新者名称（关联填充） |

**业务逻辑**:
1. 按编号查询出库单，不存在直接返回 null。
2. 查询该出库单的全部明细列表。
3. 批量查询客户 Map、仓库 Map、创建者/更新者用户 Map。
4. DO 拷贝为 RespVO 并回填 merchantName、warehouseName、creatorName、updaterName。
5. 明细列表按 4.1 的拼接逻辑回填商品/SKU/仓库信息后设置到 details 返回。

### 3.7 获得出库单分页

- **路径**: GET /wms/shipment-order/page
- **权限**: wms:shipment-order:query
- **说明**: 分页查询出库单列表，支持单号、状态、仓库、客户、类型、数量/金额区间等多条件过滤。

**请求参数 (WmsShipmentOrderPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 分页参数（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 分页参数（继承 PageParam） | 每页条数 |
| no | String | 否 | — | 出库单号 |
| status | Integer | 否 | @InEnum(WmsOrderStatusEnum) | 单据状态：0 草稿 / 4 已完成 / 5 已作废 |
| warehouseId | Long | 否 | — | 仓库编号 |
| merchantId | Long | 否 | — | 客户编号 |
| orderTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 单据日期区间 |
| totalQuantityMin | BigDecimal | 否 | — | 最小出库数量 |
| totalQuantityMax | BigDecimal | 否 | — | 最大出库数量 |
| totalPriceMin | BigDecimal | 否 | — | 最小总金额 |
| totalPriceMax | BigDecimal | 否 | — | 最大总金额 |
| type | Integer | 否 | @InEnum(WmsShipmentOrderTypeEnum) | 出库类型 |
| bizOrderNo | String | 否 | — | 业务单号 |
| creator | String | 否 | — | 创建用户 |
| updater | String | 否 | — | 更新用户 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| updateTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 更新时间区间 |

**响应**: CommonResult\<PageResult\<WmsShipmentOrderRespVO\>\>，元素字段同 3.6 的 WmsShipmentOrderRespVO（不含 details）。

**业务逻辑**:
1. Service 按分页条件查询出库单分页结果。
2. 批量查询客户 Map、仓库 Map、创建者/更新者用户 Map。
3. DO 列表拷贝为 RespVO 列表并回填 merchantName、warehouseName、creatorName、updaterName 后返回。

### 3.8 导出出库单 Excel

- **路径**: GET /wms/shipment-order/export-excel
- **权限**: wms:shipment-order:export
- **说明**: 按分页查询条件导出全部出库单 Excel（文件名"出库单.xls"），查询条件同 3.7。

**请求参数 (WmsShipmentOrderPageReqVO)**: 同 3.7（pageSize 由服务端强制置为不分页）。

**响应**: Excel 文件流（导出字段为 RespVO 上标注 @ExcelProperty 的列：出库单号、出库类型、单据日期、出库状态、业务单号、客户、仓库、出库数量、总金额、创建时间）。

**业务逻辑**:
1. 将分页参数 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 按条件查询全部出库单。
3. 批量拼接客户/仓库/操作人名称后，通过 ExcelUtils 写出 Excel 文件；接口标注 @ApiAccessLog(operateType = EXPORT) 记录导出操作日志。

---

## 4. 出库单明细（WmsShipmentOrderDetailController）

### 4.1 获得出库单明细列表

- **路径**: GET /wms/shipment-order-detail/list-by-order-id
- **权限**: wms:shipment-order:query
- **说明**: 按出库单编号查询全部出库明细，并回填商品/SKU/仓库展示字段。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| orderId | Long | 是 | @RequestParam required | 出库单编号 |

**响应**: CommonResult\<List\<WmsShipmentOrderDetailRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 明细编号 |
| orderId | Long | 出库单编号 |
| itemId | Long | 商品编号（由 SKU 反查填充） |
| itemCode | String | 商品编码（关联填充） |
| itemName | String | 商品名称（关联填充） |
| unit | String | 商品单位（关联填充） |
| skuId | Long | 商品 SKU 编号 |
| skuCode | String | 规格编号（关联填充） |
| skuName | String | 规格名称（关联填充） |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称（关联填充） |
| quantity | BigDecimal | 出库数量 |
| price | BigDecimal | 单价 |
| totalPrice | BigDecimal | 行金额 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. Service 按出库单编号查询明细列表。
2. 批量查询 SKU Map、商品 Map、仓库 Map。
3. DO 拷贝为 RespVO 并回填 skuCode/skuName/itemId、itemCode/itemName/unit、warehouseName 后返回。

---

## 5. 移库单（WmsMovementOrderController）

### 5.1 创建移库单

- **路径**: POST /wms/movement-order/create
- **权限**: wms:movement-order:create
- **说明**: 创建移库单（状态为草稿），将商品从来源仓库移到目标仓库，同时保存移库明细。

**请求参数 (WmsMovementOrderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 编号（创建时不传） |
| no | String | 是 | @NotBlank；@Size(max=64) | 移库单号，如 YK202605110001，全局唯一 |
| orderTime | LocalDateTime | 是 | @NotNull | 单据日期 |
| remark | String | 否 | @Size(max=255) | 备注 |
| sourceWarehouseId | Long | 是 | @NotNull | 来源仓库编号（校验仓库存在） |
| targetWarehouseId | Long | 是 | @NotNull | 目标仓库编号（校验仓库存在，不能与来源仓库相同） |
| details | List\<WmsMovementOrderDetailSaveReqVO\> | 否 | @Valid 级联校验 | 移库明细列表，元素字段见下表 |

**明细元素 (WmsMovementOrderDetailSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 明细编号 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号（校验 SKU 存在） |
| quantity | BigDecimal | 是 | @NotNull；@DecimalMin(value="0", inclusive=false) | 移库数量，必须大于 0 |
| price | BigDecimal | 否 | @DecimalMin(value="0") | 单价 |
| totalPrice | BigDecimal | 否 | @DecimalMin(value="0") | 行金额（不传时按 price × quantity 计算） |

**响应**: CommonResult\<Long\>（新移库单编号）

**业务逻辑**:
1. 校验保存数据：移库单号唯一（重复抛 MOVEMENT_ORDER_NO_DUPLICATE）；分别校验来源仓库与目标仓库存在；来源仓库与目标仓库不能相同（相同抛 MOVEMENT_ORDER_WAREHOUSE_SAME）。
2. 将 VO 转换为 DO，状态置为草稿（PREPARE = 0）。
3. 汇总明细填充 totalQuantity 与 totalPrice。
4. 插入移库单主表。
5. 逐条校验明细 SKU 存在，明细的 sourceWarehouseId/targetWarehouseId 统一取单头仓库，行金额为空时自动补齐，批量插入移库单明细表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_202_001 | 移库单号重复 |
| 1_060_100_000 | 仓库不存在 |
| 1_060_202_007 | 来源仓库和目标仓库不能相同 |
| 1_060_104_004 | 商品规格不存在（明细 SKU 校验） |

### 5.2 更新移库单

- **路径**: PUT /wms/movement-order/update
- **权限**: wms:movement-order:update
- **说明**: 更新草稿态移库单及其明细（整体覆盖式更新明细）。

**请求参数 (WmsMovementOrderSaveReqVO)**: 字段同 5.1（此时 id 必传）。

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验移库单存在且为草稿状态（不存在抛 MOVEMENT_ORDER_NOT_EXISTS，非草稿抛 MOVEMENT_ORDER_STATUS_NOT_PREPARE）。
2. 校验保存数据：单号唯一、来源/目标仓库存在且不相同（同创建）。
3. 以"状态 = 草稿"为条件乐观更新主表，更新行数为 0 时抛 MOVEMENT_ORDER_STATUS_NOT_PREPARE；重新汇总 totalQuantity/totalPrice。
4. 更新明细：新旧明细按 id 对比拆分为新增/修改/删除三部分分别批量处理；新增明细携带非空 id 时抛 MOVEMENT_ORDER_DETAIL_NOT_EXISTS。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_202_000 | 移库单不存在 |
| 1_060_202_002 | 移库单状态不是草稿，不能操作 |
| 1_060_202_001 | 移库单号重复 |
| 1_060_202_006 | 移库单明细不存在（明细 diff 更新时 id 异常） |

### 5.3 删除移库单

- **路径**: DELETE /wms/movement-order/delete
- **权限**: wms:movement-order:delete
- **说明**: 删除草稿或已作废状态的移库单及其明细。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 移库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验移库单存在。
2. 校验状态为草稿（0）或已作废（5），否则抛 MOVEMENT_ORDER_STATUS_NOT_DELETABLE。
3. 删除移库单主表记录。
4. 按移库单编号删除全部移库单明细。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_202_000 | 移库单不存在 |
| 1_060_202_005 | 移库单状态不是草稿或已作废，不能删除 |

### 5.4 完成移库

- **路径**: PUT /wms/movement-order/complete
- **权限**: wms:movement-order:complete
- **说明**: 将草稿移库单置为已完成，并按明细在来源仓库扣减、目标仓库增加库存。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 移库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验移库单存在且为草稿状态。
2. 校验移库单明细存在（至少一条，否则抛 MOVEMENT_ORDER_DETAIL_REQUIRED）。
3. 以"状态 = 草稿"为条件乐观更新状态为已完成（FINISHED = 4），更新行数为 0 时抛 MOVEMENT_ORDER_STATUS_NOT_PREPARE。
4. 在同一事务内为每条明细生成两条库存变更项：来源仓库数量与金额取负（扣减）、目标仓库数量与金额为正（增加），调用库存域 changeInventory，单据类型为移库（MOVEMENT）；来源仓库库存不足时由库存域抛出异常并回滚。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_202_000 | 移库单不存在 |
| 1_060_202_002 | 移库单状态不是草稿，不能操作 |
| 1_060_202_003 | 移库单至少包含一条明细 |
| 1_060_300_000 | 库存不足，商品：{}，商品规格：{}，仓库：{}，当前库存：{}，变更数量：{}（由库存域抛出） |

### 5.5 作废移库单

- **路径**: PUT /wms/movement-order/cancel
- **权限**: wms:movement-order:cancel
- **说明**: 将草稿移库单作废。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 移库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验移库单存在且为草稿状态。
2. 以"状态 = 草稿"为条件乐观更新状态为已作废（CANCELED = 5），更新行数为 0 时抛 MOVEMENT_ORDER_STATUS_NOT_PREPARE。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_202_000 | 移库单不存在 |
| 1_060_202_002 | 移库单状态不是草稿，不能操作 |

### 5.6 获得移库单

- **路径**: GET /wms/movement-order/get
- **权限**: wms:movement-order:query
- **说明**: 获得移库单详情，含全部移库明细及关联的来源/目标仓库与操作人名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 移库单编号 |

**响应**: CommonResult\<WmsMovementOrderRespVO\>（单据不存在时返回 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 移库单号 |
| orderTime | LocalDateTime | 单据日期 |
| status | Integer | 移库状态（0 草稿 / 4 已完成 / 5 已作废） |
| remark | String | 备注 |
| sourceWarehouseId | Long | 来源仓库编号 |
| sourceWarehouseName | String | 来源仓库名称（关联填充） |
| targetWarehouseId | Long | 目标仓库编号 |
| targetWarehouseName | String | 目标仓库名称（关联填充） |
| totalQuantity | BigDecimal | 移库数量（明细汇总） |
| totalPrice | BigDecimal | 总金额（明细汇总） |
| details | List\<WmsMovementOrderDetailRespVO\> | 移库明细列表，元素字段同 6.1 |
| createTime | LocalDateTime | 创建时间 |
| creator | String | 创建者 |
| creatorName | String | 创建者名称（关联填充） |
| updateTime | LocalDateTime | 更新时间 |
| updater | String | 更新者 |
| updaterName | String | 更新者名称（关联填充） |

**业务逻辑**:
1. 按编号查询移库单，不存在直接返回 null。
2. 查询该移库单的全部明细列表。
3. 批量按 sourceWarehouseId/targetWarehouseId 查询仓库 Map，按创建者/更新者查询用户 Map。
4. DO 拷贝为 RespVO 并回填 sourceWarehouseName、targetWarehouseName、creatorName、updaterName。
5. 明细列表按 6.1 的拼接逻辑回填商品/SKU/来源/目标仓库信息后设置到 details 返回。

### 5.7 获得移库单分页

- **路径**: GET /wms/movement-order/page
- **权限**: wms:movement-order:query
- **说明**: 分页查询移库单列表，支持单号、状态、来源/目标仓库、数量/金额区间等多条件过滤。

**请求参数 (WmsMovementOrderPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 分页参数（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 分页参数（继承 PageParam） | 每页条数 |
| no | String | 否 | — | 移库单号 |
| status | Integer | 否 | @InEnum(WmsOrderStatusEnum) | 单据状态：0 草稿 / 4 已完成 / 5 已作废 |
| sourceWarehouseId | Long | 否 | — | 来源仓库编号 |
| targetWarehouseId | Long | 否 | — | 目标仓库编号 |
| orderTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 单据日期区间 |
| totalQuantityMin | BigDecimal | 否 | — | 最小移库数量 |
| totalQuantityMax | BigDecimal | 否 | — | 最大移库数量 |
| totalPriceMin | BigDecimal | 否 | — | 最小总金额 |
| totalPriceMax | BigDecimal | 否 | — | 最大总金额 |
| creator | String | 否 | — | 创建用户 |
| updater | String | 否 | — | 更新用户 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| updateTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 更新时间区间 |

**响应**: CommonResult\<PageResult\<WmsMovementOrderRespVO\>\>，元素字段同 5.6 的 WmsMovementOrderRespVO（不含 details）。

**业务逻辑**:
1. Service 按分页条件查询移库单分页结果。
2. 批量查询来源/目标仓库 Map、创建者/更新者用户 Map。
3. DO 列表拷贝为 RespVO 列表并回填仓库名称、操作人名称后返回。

### 5.8 导出移库单 Excel

- **路径**: GET /wms/movement-order/export-excel
- **权限**: wms:movement-order:export
- **说明**: 按分页查询条件导出全部移库单 Excel（文件名"移库单.xls"），查询条件同 5.7。

**请求参数 (WmsMovementOrderPageReqVO)**: 同 5.7（pageSize 由服务端强制置为不分页）。

**响应**: Excel 文件流（导出字段为 RespVO 上标注 @ExcelProperty 的列：移库单号、单据日期、移库状态、来源仓库、目标仓库、移库数量、总金额、创建时间）。

**业务逻辑**:
1. 将分页参数 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 按条件查询全部移库单。
3. 批量拼接来源/目标仓库名称、操作人名称后，通过 ExcelUtils 写出 Excel 文件；接口标注 @ApiAccessLog(operateType = EXPORT) 记录导出操作日志。

---

## 6. 移库单明细（WmsMovementOrderDetailController）

### 6.1 获得移库单明细列表

- **路径**: GET /wms/movement-order-detail/list-by-order-id
- **权限**: wms:movement-order:query
- **说明**: 按移库单编号查询全部移库明细，并回填商品/SKU/来源与目标仓库展示字段。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| orderId | Long | 是 | @RequestParam required | 移库单编号 |

**响应**: CommonResult\<List\<WmsMovementOrderDetailRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 明细编号 |
| orderId | Long | 移库单编号 |
| itemId | Long | 商品编号（由 SKU 反查填充） |
| itemCode | String | 商品编码（关联填充） |
| itemName | String | 商品名称（关联填充） |
| unit | String | 商品单位（关联填充） |
| skuId | Long | 商品 SKU 编号 |
| skuCode | String | 规格编号（关联填充） |
| skuName | String | 规格名称（关联填充） |
| sourceWarehouseId | Long | 来源仓库编号 |
| sourceWarehouseName | String | 来源仓库名称（关联填充） |
| targetWarehouseId | Long | 目标仓库编号 |
| targetWarehouseName | String | 目标仓库名称（关联填充） |
| quantity | BigDecimal | 移库数量 |
| price | BigDecimal | 单价 |
| totalPrice | BigDecimal | 行金额 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. Service 按移库单编号查询明细列表。
2. 批量查询 SKU Map、商品 Map，并按 sourceWarehouseId/targetWarehouseId 查询仓库 Map。
3. DO 拷贝为 RespVO 并回填 skuCode/skuName/itemId、itemCode/itemName/unit、sourceWarehouseName、targetWarehouseName 后返回。

---

## 7. 盘库单（WmsCheckOrderController）

### 7.1 创建盘库单

- **路径**: POST /wms/check-order/create
- **权限**: wms:check-order:create
- **说明**: 创建盘库单（状态为草稿），录入各库存的账面数量与实盘数量，同时保存盘库明细。

**请求参数 (WmsCheckOrderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 编号（创建时不传） |
| no | String | 是 | @NotBlank；@Size(max=64) | 盘库单号，如 PK202605110001，全局唯一 |
| orderTime | LocalDateTime | 是 | @NotNull | 单据日期 |
| remark | String | 否 | @Size(max=255) | 备注 |
| warehouseId | Long | 是 | @NotNull | 盘库仓库编号 |
| details | List\<WmsCheckOrderDetailSaveReqVO\> | 否 | @Valid 级联校验 | 盘库明细列表，元素字段见下表 |

**明细元素 (WmsCheckOrderDetailSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 明细编号 |
| skuId | Long | 是 | @NotNull | 商品 SKU 编号（校验 SKU 存在） |
| inventoryId | Long | 否 | — | 库存余额行编号（关联被盘点的库存记录） |
| receiptTime | LocalDateTime | 否 | — | 入库时间 |
| quantity | BigDecimal | 是 | @NotNull；@DecimalMin(value="0") | 账面数量，不能小于 0 |
| checkQuantity | BigDecimal | 是 | @NotNull；@DecimalMin(value="0") | 实盘数量，不能小于 0 |
| price | BigDecimal | 否 | @DecimalMin(value="0") | 单价 |

**响应**: CommonResult\<Long\>（新盘库单编号）

**业务逻辑**:
1. 校验保存数据：盘库单号唯一（重复抛 CHECK_ORDER_NO_DUPLICATE）；校验仓库存在。
2. 将 VO 转换为 DO，状态置为草稿（PREPARE = 0）。
3. 汇总明细填充 totalQuantity（盈亏数量 = Σ(实盘数量 − 账面数量)）、totalPrice（账面金额 = Σ(price × 账面数量)）、actualPrice（实际金额 = Σ(price × 实盘数量)）。
4. 插入盘库单主表。
5. 逐条校验明细 SKU 存在，明细 warehouseId 统一取单头仓库，批量插入盘库单明细表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_203_001 | 盘库单号重复 |
| 1_060_100_000 | 仓库不存在 |
| 1_060_104_004 | 商品规格不存在（明细 SKU 校验） |

### 7.2 更新盘库单

- **路径**: PUT /wms/check-order/update
- **权限**: wms:check-order:update
- **说明**: 更新草稿态盘库单及其明细（整体覆盖式更新明细）。

**请求参数 (WmsCheckOrderSaveReqVO)**: 字段同 7.1（此时 id 必传）。

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验盘库单存在且为草稿状态（不存在抛 CHECK_ORDER_NOT_EXISTS，非草稿抛 CHECK_ORDER_STATUS_NOT_PREPARE）。
2. 校验保存数据：单号唯一、仓库存在（同创建）。
3. 以"状态 = 草稿"为条件乐观更新主表，更新行数为 0 时抛 CHECK_ORDER_STATUS_NOT_PREPARE；重新汇总盈亏数量、账面金额、实际金额。
4. 更新明细：新旧明细按 id 对比拆分为新增/修改/删除三部分分别批量处理；新增明细携带非空 id 时抛 CHECK_ORDER_DETAIL_NOT_EXISTS。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_203_000 | 盘库单不存在 |
| 1_060_203_002 | 盘库单状态不是草稿，不能操作 |
| 1_060_203_001 | 盘库单号重复 |
| 1_060_203_006 | 盘库单明细不存在（明细 diff 更新时 id 异常） |

### 7.3 删除盘库单

- **路径**: DELETE /wms/check-order/delete
- **权限**: wms:check-order:delete
- **说明**: 删除草稿或已作废状态的盘库单及其明细。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 盘库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验盘库单存在。
2. 校验状态为草稿（0）或已作废（5），否则抛 CHECK_ORDER_STATUS_NOT_DELETABLE。
3. 删除盘库单主表记录。
4. 按盘库单编号删除全部盘库单明细。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_203_000 | 盘库单不存在 |
| 1_060_203_005 | 盘库单状态不是草稿或已作废，不能删除 |

### 7.4 完成盘库

- **路径**: PUT /wms/check-order/complete
- **权限**: wms:check-order:complete
- **说明**: 将草稿盘库单置为已完成，并按"实盘数量"校准库存（库存域按账面与实盘差异调整余额）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 盘库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验盘库单存在且为草稿状态。
2. 校验盘库单明细存在（至少一条，否则抛 CHECK_ORDER_DETAIL_REQUIRED）。
3. 以"状态 = 草稿"为条件乐观更新状态为已完成（FINISHED = 4），更新行数为 0 时抛 CHECK_ORDER_STATUS_NOT_PREPARE。
4. 在同一事务内将明细转换为库存盘点请求（含 inventoryId、账面数量、实盘数量等），调用库存域 checkInventory 按实盘数量校准库存，单据类型为盘库（CHECK）；若对应库存余额在盘点期间已发生变化，库存域抛 CHECK_ORDER_INVENTORY_CHANGED 并回滚。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_203_000 | 盘库单不存在 |
| 1_060_203_002 | 盘库单状态不是草稿，不能操作 |
| 1_060_203_003 | 盘库单至少包含一条明细 |
| 1_060_203_007 | 盘库单库存已变化，请重新加载库存后再完成 |

### 7.5 作废盘库单

- **路径**: PUT /wms/check-order/cancel
- **权限**: wms:check-order:cancel
- **说明**: 将草稿盘库单作废。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 盘库单编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**:
1. 校验盘库单存在且为草稿状态。
2. 以"状态 = 草稿"为条件乐观更新状态为已作废（CANCELED = 5），更新行数为 0 时抛 CHECK_ORDER_STATUS_NOT_PREPARE。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_203_000 | 盘库单不存在 |
| 1_060_203_002 | 盘库单状态不是草稿，不能操作 |

### 7.6 获得盘库单

- **路径**: GET /wms/check-order/get
- **权限**: wms:check-order:query
- **说明**: 获得盘库单详情，含全部盘库明细及关联的仓库/操作人名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 盘库单编号 |

**响应**: CommonResult\<WmsCheckOrderRespVO\>（单据不存在时返回 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 盘库单号 |
| orderTime | LocalDateTime | 单据日期 |
| status | Integer | 盘库状态（0 草稿 / 4 已完成 / 5 已作废） |
| remark | String | 备注 |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称（关联填充） |
| totalQuantity | BigDecimal | 盈亏数量（Σ(实盘数量 − 账面数量)，可为负） |
| totalPrice | BigDecimal | 总金额（账面金额 = Σ(price × 账面数量)） |
| actualPrice | BigDecimal | 实际金额（Σ(price × 实盘数量)） |
| details | List\<WmsCheckOrderDetailRespVO\> | 盘库明细列表，元素字段同 8.1 |
| createTime | LocalDateTime | 创建时间 |
| creator | String | 创建者 |
| creatorName | String | 创建者名称（关联填充） |
| updateTime | LocalDateTime | 更新时间 |
| updater | String | 更新者 |
| updaterName | String | 更新者名称（关联填充） |

**业务逻辑**:
1. 按编号查询盘库单，不存在直接返回 null。
2. 查询该盘库单的全部明细列表。
3. 批量查询仓库 Map、创建者/更新者用户 Map。
4. DO 拷贝为 RespVO 并回填 warehouseName、creatorName、updaterName。
5. 明细列表按 8.1 的拼接逻辑回填商品/SKU/仓库信息后设置到 details 返回。

### 7.7 获得盘库单分页

- **路径**: GET /wms/check-order/page
- **权限**: wms:check-order:query
- **说明**: 分页查询盘库单列表，支持单号、状态、仓库、盈亏数量/账面金额/实际金额区间等多条件过滤。

**请求参数 (WmsCheckOrderPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 分页参数（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 分页参数（继承 PageParam） | 每页条数 |
| no | String | 否 | — | 盘库单号 |
| status | Integer | 否 | @InEnum(WmsOrderStatusEnum) | 单据状态：0 草稿 / 4 已完成 / 5 已作废 |
| warehouseId | Long | 否 | — | 仓库编号 |
| orderTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 单据日期区间 |
| totalQuantityMin | BigDecimal | 否 | — | 最小盈亏数量（可为负数） |
| totalQuantityMax | BigDecimal | 否 | — | 最大盈亏数量 |
| totalPriceMin | BigDecimal | 否 | — | 最小账面总金额 |
| totalPriceMax | BigDecimal | 否 | — | 最大账面总金额 |
| actualPriceMin | BigDecimal | 否 | — | 最小实际金额 |
| actualPriceMax | BigDecimal | 否 | — | 最大实际金额 |
| creator | String | 否 | — | 创建用户 |
| updater | String | 否 | — | 更新用户 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| updateTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 更新时间区间 |

**响应**: CommonResult\<PageResult\<WmsCheckOrderRespVO\>\>，元素字段同 7.6 的 WmsCheckOrderRespVO（不含 details）。

**业务逻辑**:
1. Service 按分页条件查询盘库单分页结果。
2. 批量查询仓库 Map、创建者/更新者用户 Map。
3. DO 列表拷贝为 RespVO 列表并回填 warehouseName、creatorName、updaterName 后返回。

### 7.8 导出盘库单 Excel

- **路径**: GET /wms/check-order/export-excel
- **权限**: wms:check-order:export
- **说明**: 按分页查询条件导出全部盘库单 Excel（文件名"盘库单.xls"），查询条件同 7.7。

**请求参数 (WmsCheckOrderPageReqVO)**: 同 7.7（pageSize 由服务端强制置为不分页）。

**响应**: Excel 文件流（导出字段为 RespVO 上标注 @ExcelProperty 的列：盘库单号、单据日期、盘库状态、仓库、盈亏数量、总金额、实际金额、创建时间）。

**业务逻辑**:
1. 将分页参数 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 按条件查询全部盘库单。
3. 批量拼接仓库名称、操作人名称后，通过 ExcelUtils 写出 Excel 文件；接口标注 @ApiAccessLog(operateType = EXPORT) 记录导出操作日志。

---

## 8. 盘库单明细（WmsCheckOrderDetailController）

### 8.1 获得盘库单明细列表

- **路径**: GET /wms/check-order-detail/list-by-order-id
- **权限**: wms:check-order:query
- **说明**: 按盘库单编号查询全部盘库明细，并回填商品/SKU/仓库展示字段。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| orderId | Long | 是 | @RequestParam required | 盘库单编号 |

**响应**: CommonResult\<List\<WmsCheckOrderDetailRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 明细编号 |
| orderId | Long | 盘库单编号 |
| itemId | Long | 商品编号（由 SKU 反查填充） |
| itemCode | String | 商品编码（关联填充） |
| itemName | String | 商品名称（关联填充） |
| unit | String | 商品单位（关联填充） |
| skuId | Long | 商品 SKU 编号 |
| skuCode | String | 规格编号（关联填充） |
| skuName | String | 规格名称（关联填充） |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称（关联填充） |
| inventoryId | Long | 库存余额行编号 |
| receiptTime | LocalDateTime | 入库时间 |
| quantity | BigDecimal | 账面数量 |
| checkQuantity | BigDecimal | 实盘数量 |
| price | BigDecimal | 单价 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. Service 按盘库单编号查询明细列表。
2. 批量查询 SKU Map、商品 Map、仓库 Map。
3. DO 拷贝为 RespVO 并回填 skuCode/skuName/itemId、itemCode/itemName/unit、warehouseName 后返回。

---

## 附：单据域错误码总表

四类单据的错误码按 `1_060_2XX_XXX` 段划分（入库 1_060_200_xxx、出库 1_060_201_xxx、移库 1_060_202_xxx、盘库 1_060_203_xxx），同位置错误码语义一致：

| 错误码段 | 通用语义 | 域特有 |
|---------|---------|--------|
| 1_060_200_xxx（入库单） | _000 单不存在、_001 单号重复、_002 状态不是草稿不能操作、_003 至少一条明细、_005 状态不是草稿或已作废不能删除、_007 明细不存在 | — |
| 1_060_201_xxx（出库单） | 同上（_007 为明细不存在） | — |
| 1_060_202_xxx（移库单） | _000 ~ _005、_006 明细不存在 | _007 来源仓库和目标仓库不能相同 |
| 1_060_203_xxx（盘库单） | _000 ~ _005、_006 明细不存在 | _007 盘库单库存已变化，请重新加载库存后再完成 |
| 1_060_300_000（库存域） | 库存不足（入库/出库/移库完成时由库存域抛出） | — |
