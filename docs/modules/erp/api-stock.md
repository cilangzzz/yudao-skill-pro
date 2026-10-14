# 仓库库存接口 (ErpWarehouseController / ErpStockController / ErpStockRecordController / ErpStockInController / ErpStockOutController / ErpStockMoveController / ErpStockCheckController)

> ERP 仓库库存域：管理仓库档案、产品库存与库存明细流水，并提供其它入库单、其它出库单、库存调拨单、库存盘点单四类单据的录入、审核与库存变更能力。

## 接口路径前缀

- /erp/warehouse (Controller: ErpWarehouseController)
- /erp/stock (Controller: ErpStockController)
- /erp/stock-record (Controller: ErpStockRecordController)
- /erp/stock-in (Controller: ErpStockInController)
- /erp/stock-out (Controller: ErpStockOutController)
- /erp/stock-move (Controller: ErpStockMoveController)
- /erp/stock-check (Controller: ErpStockCheckController)

分页查询均继承 `PageParam` 通用参数：`pageNo`（页码，默认 1）、`pageSize`（每页条数，默认 10）。

所有单据类接口的状态字段 `status` 取值来自 `ErpAuditStatus`：10 = 未审核（PROCESS）、20 = 已审核（APPROVE）。

库存明细业务类型 `bizType` 取值来自 `ErpStockRecordBizTypeEnum`：10 其它入库、11 其它入库（作废）、20 其它出库、21 其它出库（作废）、30 调拨入库、31 调拨入库（作废）、32 调拨出库、33 调拨出库（作废）、40 盘盈入库、41 盘盈入库（作废）、42 盘亏出库、43 盘亏出库（作废）、50 销售出库、51 销售出库（作废）、60 销售退货入库、61 销售退货入库（作废）、70 采购入库、71 采购入库（作废）、80 采购退货出库、81 采购退货出库（作废）。

---

## 1. 仓库管理（ErpWarehouseController）

### 1.1 创建仓库

- **路径**: POST /erp/warehouse/create
- **权限**: erp:warehouse:create
- **说明**: 新增一个仓库档案，返回仓库编号。

**请求参数 (ErpWarehouseSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否（新增时不传） | - | 仓库编号 |
| name | String | 是 | @NotEmpty | 仓库名称 |
| address | String | 否 | - | 仓库地址 |
| sort | Long | 是 | @NotNull | 排序 |
| remark | String | 否 | - | 备注 |
| principal | String | 否 | - | 负责人 |
| warehousePrice | BigDecimal | 否 | - | 仓储费，单位：元 |
| truckagePrice | BigDecimal | 否 | - | 搬运费，单位：元 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 开启状态（0 开启 / 1 禁用） |

**响应**: CommonResult&lt;Long&gt;（仓库编号）

**业务逻辑**: 1. 将请求 VO 转换为 ErpWarehouseDO；2. 插入仓库表；3. 返回自增主键作为仓库编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_400_000 | 仓库不存在 |

### 1.2 更新仓库

- **路径**: PUT /erp/warehouse/update
- **权限**: erp:warehouse:update
- **说明**: 修改仓库档案信息。

**请求参数 (ErpWarehouseSaveReqVO)**: 同 1.1（id 必传，用于定位更新的仓库）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验仓库存在，不存在抛 WAREHOUSE_NOT_EXISTS；2. 转换为 ErpWarehouseDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_400_000 | 仓库不存在 |

### 1.3 更新仓库默认状态

- **路径**: PUT /erp/warehouse/update-default-status
- **权限**: erp:warehouse:update
- **说明**: 设置/取消默认仓库；设置默认时会关闭其它仓库的默认标志，保证全局唯一默认仓库。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 仓库编号 |
| defaultStatus | Boolean | 是 | - | 是否默认（true 设为默认 / false 取消默认） |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验仓库存在，不存在抛 WAREHOUSE_NOT_EXISTS；2. 若要设为默认（defaultStatus = true），查询当前的默认仓库，若存在则先将其 defaultStatus 更新为 false；3. 更新目标仓库的 defaultStatus。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_400_000 | 仓库不存在 |

### 1.4 删除仓库

- **路径**: DELETE /erp/warehouse/delete
- **权限**: erp:warehouse:delete
- **说明**: 删除指定仓库。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 仓库编号 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验仓库存在，不存在抛 WAREHOUSE_NOT_EXISTS；2. 删除该仓库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_400_000 | 仓库不存在 |

### 1.5 获得仓库

- **路径**: GET /erp/warehouse/get
- **权限**: erp:warehouse:query
- **说明**: 按编号查询单个仓库详情。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 仓库编号 |

**响应**: CommonResult&lt;ErpWarehouseRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 仓库编号 |
| name | String | 仓库名称 |
| address | String | 仓库地址 |
| sort | Long | 排序 |
| remark | String | 备注 |
| principal | String | 负责人 |
| warehousePrice | BigDecimal | 仓储费，单位：元 |
| truckagePrice | BigDecimal | 搬运费，单位：元 |
| status | Integer | 开启状态 |
| defaultStatus | Boolean | 是否默认 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 ErpWarehouseDO；2. 转换为 ErpWarehouseRespVO 返回。

### 1.6 获得仓库分页

- **路径**: GET /erp/warehouse/page
- **权限**: erp:warehouse:query
- **说明**: 分页查询仓库列表。

**请求参数 (ErpWarehousePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| name | String | 否 | - | 仓库名称，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 开启状态 |

**响应**: CommonResult&lt;PageResult&lt;ErpWarehouseRespVO&gt;&gt;，ErpWarehouseRespVO 字段同 1.5。

**业务逻辑**: 1. 按条件分页查询仓库；2. 转换为 RespVO 分页返回。

### 1.7 获得仓库精简列表

- **路径**: GET /erp/warehouse/simple-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 只包含开启状态的仓库，主要用于前端下拉选项，仅返回 id / name / defaultStatus 三个字段。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ErpWarehouseRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 仓库编号 |
| name | String | 仓库名称 |
| defaultStatus | Boolean | 是否默认 |

**业务逻辑**: 1. 查询状态为开启（CommonStatusEnum.ENABLE）的仓库列表；2. 仅组装 id、name、defaultStatus 三个字段返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_400_001 | 仓库({})未启用（该错误码在单据校验仓库时抛出） |

### 1.8 导出仓库 Excel

- **路径**: GET /erp/warehouse/export-excel
- **权限**: erp:warehouse:export
- **说明**: 按分页条件查询全量仓库并导出 Excel（文件名：仓库.xls）。

**请求参数 (ErpWarehousePageReqVO)**: 同 1.6（pageSize 强制设为 PAGE_SIZE_NONE，查询全部数据）。

**响应**: Excel 文件流（ErpWarehouseRespVO 注解列：仓库编号、仓库名称、仓库地址、排序、备注、负责人、仓储费、搬运费、开启状态、是否默认、创建时间）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部符合条件的仓库；2. 通过 ExcelUtils 写出 Excel 文件流；3. 记录 EXPORT 操作日志。

---

## 2. 产品库存（ErpStockController）

### 2.1 获得产品库存

- **路径**: GET /erp/stock/get
- **权限**: erp:stock:query
- **说明**: 查询单条产品库存，支持两种方式：按库存记录 id，或按 productId + warehouseId 组合。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否（与 productId+warehouseId 二选一） | - | 库存编号 |
| productId | Long | 否 | - | 产品编号（方式二，需与 warehouseId 同时传递） |
| warehouseId | Long | 否 | - | 仓库编号（方式二） |

**响应**: CommonResult&lt;ErpStockRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| productId | Long | 产品编号 |
| warehouseId | Long | 仓库编号 |
| count | BigDecimal | 库存数量 |
| productName | String | 产品名称（分页/导出时组装） |
| categoryName | String | 产品分类（分页/导出时组装） |
| unitName | String | 单位（分页/导出时组装） |
| warehouseName | String | 仓库名称（分页/导出时组装） |

**业务逻辑**: 1. 若传入 id 则按 id 查询库存；2. 否则按 productId + warehouseId 查询库存；3. 转换为 ErpStockRespVO 返回。

### 2.2 获得产品库存数量

- **路径**: GET /erp/stock/get-count
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 统计指定产品在全部仓库的库存总和。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| productId | Long | 是 | - | 产品编号 |

**响应**: CommonResult&lt;BigDecimal&gt;（库存总数量，无库存记录时返回 0）

**业务逻辑**: 1. 按产品编号求和所有仓库的库存数量；2. 汇总结果为 null 时返回 BigDecimal.ZERO。

### 2.3 获得产品库存分页

- **路径**: GET /erp/stock/page
- **权限**: erp:stock:query
- **说明**: 分页查询产品库存，并组装产品名称、分类、单位、仓库名称。

**请求参数 (ErpStockPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| productId | Long | 否 | - | 产品编号 |
| warehouseId | Long | 否 | - | 仓库编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpStockRespVO&gt;&gt;，字段同 2.1。

**业务逻辑**: 1. 按条件分页查询库存记录；2. 批量查询产品信息（含分类、单位）与仓库信息；3. 将产品名称/分类/单位、仓库名称填充到 RespVO 中返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |
| 1_030_404_001 | 操作失败，产品({})所在仓库({})的库存不足 |

（以上两个错误码由库存变更服务 `updateStockCountIncrement` 在入库/出库/调拨/盘点审核时抛出。）

### 2.4 导出产品库存 Excel

- **路径**: GET /erp/stock/export-excel
- **权限**: erp:stock:export
- **说明**: 按分页条件查询全量产品库存并导出 Excel（文件名：产品库存.xls）。

**请求参数 (ErpStockPageReqVO)**: 同 2.3（pageSize 强制设为 PAGE_SIZE_NONE）。

**响应**: Excel 文件流（导出列：编号、产品名称、产品分类、单位、仓库名称、库存数量）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部库存；2. 组装产品/仓库关联信息；3. 写出 Excel 文件流并记录 EXPORT 操作日志。

---

## 3. 产品库存明细（ErpStockRecordController）

### 3.1 获得产品库存明细

- **路径**: GET /erp/stock-record/get
- **权限**: erp:stock-record:query
- **说明**: 按编号查询单条库存出入库明细。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 明细编号 |

**响应**: CommonResult&lt;ErpStockRecordRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| productId | Long | 产品编号 |
| warehouseId | Long | 仓库编号 |
| count | BigDecimal | 出入库数量（正数入库 / 负数出库） |
| totalCount | BigDecimal | 变更后的总库存量 |
| bizType | Integer | 业务类型（见文档头部枚举说明） |
| bizId | Long | 业务编号 |
| bizItemId | Long | 业务项编号 |
| bizNo | String | 业务单号 |
| createTime | LocalDateTime | 创建时间 |
| creator | String | 创建人编号 |
| productName | String | 产品名称（分页/导出时组装） |
| categoryName | String | 产品分类（分页/导出时组装） |
| unitName | String | 单位（分页/导出时组装） |
| warehouseName | String | 仓库名称（分页/导出时组装） |
| creatorName | String | 创建人昵称（分页/导出时组装） |

**业务逻辑**: 1. 按 id 查询 ErpStockRecordDO；2. 转换为 ErpStockRecordRespVO 返回。

### 3.2 获得产品库存明细分页

- **路径**: GET /erp/stock-record/page
- **权限**: erp:stock-record:query
- **说明**: 分页查询库存出入库明细流水，并组装产品、仓库、创建人信息。

**请求参数 (ErpStockRecordPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| productId | Long | 否 | - | 产品编号 |
| warehouseId | Long | 否 | - | 仓库编号 |
| bizType | Integer | 否 | - | 业务类型（见文档头部枚举说明） |
| bizNo | String | 否 | - | 业务单号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ErpStockRecordRespVO&gt;&gt;，字段同 3.1。

**业务逻辑**: 1. 按条件分页查询库存明细；2. 批量查询产品信息、仓库信息与管理员用户信息；3. 填充产品名称/分类/单位、仓库名称、创建人昵称后返回。

### 3.3 导出产品库存明细 Excel

- **路径**: GET /erp/stock-record/export-excel
- **权限**: erp:stock-record:export
- **说明**: 按分页条件查询全量库存明细并导出 Excel（文件名：产品库存明细.xls）。

**请求参数 (ErpStockRecordPageReqVO)**: 同 3.2（pageSize 强制设为 PAGE_SIZE_NONE）。

**响应**: Excel 文件流（导出列：编号、产品名称、产品分类、单位、仓库名称、出入库数量、总库存量、业务类型、业务编号、业务项编号、业务单号、创建时间、创建人）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部明细；2. 组装产品/仓库/创建人信息；3. 写出 Excel 文件流并记录 EXPORT 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |
| 1_030_404_001 | 操作失败，产品({})所在仓库({})的库存不足 |

（明细创建入口 `createStockRecord` 会先调用库存变更服务更新库存，库存不足时抛出上述错误码。）

---

## 4. 其它入库单（ErpStockInController）

### 4.1 创建其它入库单

- **路径**: POST /erp/stock-in/create
- **权限**: erp:stock-in:create
- **说明**: 创建其它入库单（含明细项），初始状态为未审核，不直接变更库存。

**请求参数 (ErpStockInSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否（创建时不传） | - | 入库编号 |
| supplierId | Long | 否 | - | 供应商编号 |
| inTime | LocalDateTime | 是 | @NotNull | 入库时间 |
| remark | String | 否 | - | 备注 |
| fileUrl | String | 否 | - | 附件 URL |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 入库项列表 |

**Item 子对象**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 入库项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;（入库单编号）

**业务逻辑**: 1. 校验入库项：校验产品存在且启用、仓库存在且启用；将每项转换为 ErpStockInItemDO，补充产品单位编号，并按 单价 × 数量 计算小计金额 totalPrice；2. 校验供应商存在且启用；3. 通过 Redis 生成 QTRK + 日期 + 6 位自增的入库单号，若单号已存在则抛 STOCK_IN_NO_EXISTS；4. 插入入库单主表，状态置为未审核（PROCESS），汇总合计数量 totalCount、合计金额 totalPrice；5. 批量插入入库单项，返回入库单编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_401_000 | 其它入库单不存在 |
| 1_030_401_001 | 其它入库单({})已审核，无法删除 |
| 1_030_401_002 | 反审核失败，只有已审核的入库单才能反审核 |
| 1_030_401_003 | 审核失败，只有未审核的入库单才能审核 |
| 1_030_401_004 | 生成入库单失败，请重新提交 |
| 1_030_401_005 | 其它入库单({})已审核，无法修改 |
| 1_030_400_000 | 仓库不存在（校验入库项仓库时抛出） |
| 1_030_400_001 | 仓库({})未启用（校验入库项仓库时抛出） |
| 1_030_500_000 | 产品不存在（校验入库项产品时抛出） |
| 1_030_500_001 | 产品({})未启用（校验入库项产品时抛出） |

### 4.2 更新其它入库单

- **路径**: PUT /erp/stock-in/update
- **权限**: erp:stock-in:update
- **说明**: 修改未审核的其它入库单；已审核单据不允许修改。

**请求参数 (ErpStockInSaveReqVO)**: 同 4.1（id 必传）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验入库单存在，不存在抛 STOCK_IN_NOT_EXISTS；2. 校验状态，若已审核则抛 STOCK_IN_UPDATE_FAIL_APPROVE；3. 校验供应商；4. 校验入库项（同创建），重新计算各明细小计金额；5. 更新入库单主表并重算 totalCount / totalPrice；6. 对比新老明细列表（diff：新增、更新、删除三类）批量维护入库单项。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_401_000 | 其它入库单不存在 |
| 1_030_401_005 | 其它入库单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |

### 4.3 更新其它入库单的状态

- **路径**: PUT /erp/stock-in/update-status
- **权限**: erp:stock-in:update-status
- **说明**: 审核或反审核入库单；审核时增加库存，反审核时扣回库存。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 入库单编号 |
| status | Integer | 是 | - | 目标状态：10 未审核 / 20 已审核 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验入库单存在；2. 校验状态流转：目标状态与当前状态相同则抛 STOCK_IN_APPROVE_FAIL（审核）或 STOCK_IN_PROCESS_FAIL（反审核）；3. 通过 updateByIdAndStatus 乐观更新状态，更新失败同样抛出上述错误码；4. 查询全部入库单项：审核时按明细数量逐条创建库存明细（bizType = 10 其它入库，数量为正）；反审核时数量取负（bizType = 11 其它入库（作废）），由库存服务完成库存增减。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_401_000 | 其它入库单不存在 |
| 1_030_401_002 | 反审核失败，只有已审核的入库单才能反审核 |
| 1_030_401_003 | 审核失败，只有未审核的入库单才能审核 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |
| 1_030_404_001 | 操作失败，产品({})所在仓库({})的库存不足 |

### 4.4 删除其它入库单

- **路径**: DELETE /erp/stock-in/delete
- **权限**: erp:stock-in:delete
- **说明**: 批量删除其它入库单；已审核的单据不允许删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | - | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 批量查询入库单，列表为空直接返回；2. 逐条校验状态，存在已审核单据则抛 STOCK_IN_DELETE_FAIL_APPROVE；3. 遍历删除入库单主表与明细表记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_401_001 | 其它入库单({})已审核，无法删除 |

### 4.5 获得其它入库单

- **路径**: GET /erp/stock-in/get
- **权限**: erp:stock-in:query
- **说明**: 查询入库单详情，含明细项、产品信息与当前库存数量。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 入库单编号 |

**响应**: CommonResult&lt;ErpStockInRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 入库编号 |
| no | String | 入库单号 |
| supplierId | Long | 供应商编号 |
| supplierName | String | 供应商名称（分页/详情时组装） |
| inTime | LocalDateTime | 入库时间 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 合计金额，单位：元 |
| status | Integer | 状态（10 未审核 / 20 已审核） |
| remark | String | 备注 |
| fileUrl | String | 附件 URL |
| creator | String | 创建人编号 |
| creatorName | String | 创建人名称（分页/详情时组装） |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 入库项列表 |
| productNames | String | 产品信息（分页/导出时按明细产品名拼接） |

**Item 子对象**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 入库项编号 |
| warehouseId | Long | 仓库编号 |
| productId | Long | 产品编号 |
| productPrice | BigDecimal | 产品单价 |
| count | BigDecimal | 产品数量 |
| remark | String | 备注 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 该仓库该产品的当前库存数量（仅在详情和编辑时使用） |

**业务逻辑**: 1. 查询入库单，不存在则返回 null；2. 查询该单的入库项列表；3. 批量查询产品信息；4. 逐项查询产品在该仓库的当前库存填充 stockCount（无库存记录时为 0），并填充产品名称/条码/单位。

### 4.6 获得其它入库单分页

- **路径**: GET /erp/stock-in/page
- **权限**: erp:stock-in:query
- **说明**: 分页查询其它入库单，组装明细、产品、供应商、创建人信息。

**请求参数 (ErpStockInPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| no | String | 否 | - | 入库单号 |
| supplierId | Long | 否 | - | 供应商编号 |
| inTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 入库时间区间 |
| status | Integer | 否 | @InEnum(ErpAuditStatus) | 状态 |
| remark | String | 否 | - | 备注 |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |
| warehouseId | Long | 否 | - | 仓库编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpStockInRespVO&gt;&gt;，字段同 4.5（Item 中 stockCount 不填充）。

**业务逻辑**: 1. 按条件分页查询入库单；2. 批量查询全部入库单项并按单号分组；3. 批量查询产品信息、供应商信息、创建人信息；4. 组装明细、productNames、supplierName、creatorName 后返回。

### 4.7 导出其它入库单 Excel

- **路径**: GET /erp/stock-in/export-excel
- **权限**: erp:stock-in:export
- **说明**: 按分页条件查询全量入库单并导出 Excel（文件名：其它入库单.xls）。

**请求参数 (ErpStockInPageReqVO)**: 同 4.6（pageSize 强制设为 PAGE_SIZE_NONE）。

**响应**: Excel 文件流（导出列：入库编号、入库单号、供应商名称、入库时间、合计数量、合计金额、状态、备注、产品信息、创建时间）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部入库单；2. 组装明细/产品/供应商/创建人信息；3. 写出 Excel 文件流并记录 EXPORT 操作日志。

---

## 5. 其它出库单（ErpStockOutController）

### 5.1 创建其它出库单

- **路径**: POST /erp/stock-out/create
- **权限**: erp:stock-out:create
- **说明**: 创建其它出库单（含明细项），初始状态为未审核，不直接变更库存。

**请求参数 (ErpStockOutSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否（创建时不传） | - | 出库编号 |
| customerId | Long | 否 | - | 客户编号 |
| outTime | LocalDateTime | 是 | @NotNull | 出库时间 |
| remark | String | 否 | - | 备注 |
| fileUrl | String | 否 | - | 附件 URL |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 出库项列表 |

**Item 子对象**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 出库项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;（出库单编号）

**业务逻辑**: 1. 校验出库项：校验产品存在且启用、仓库存在且启用；转换为明细 DO，补充产品单位编号，按 单价 × 数量 计算小计金额；2. 校验客户存在且启用；3. 生成 QCKD 前缀的出库单号（Redis 日期自增），单号重复则抛 STOCK_OUT_NO_EXISTS；4. 插入出库单主表，状态置为未审核，汇总 totalCount / totalPrice；5. 批量插入出库项，返回出库单编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_000 | 其它出库单不存在 |
| 1_030_402_001 | 其它出库单({})已审核，无法删除 |
| 1_030_402_002 | 反审核失败，只有已审核的出库单才能反审核 |
| 1_030_402_003 | 审核失败，只有未审核的出库单才能审核 |
| 1_030_402_004 | 生成出库单失败，请重新提交 |
| 1_030_402_005 | 其它出库单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |
| 1_020_200_000 / 1_020_200_001 | 客户不存在 / 客户({})未启用 |

### 5.2 更新其它出库单

- **路径**: PUT /erp/stock-out/update
- **权限**: erp:stock-out:update
- **说明**: 修改未审核的其它出库单；已审核单据不允许修改。

**请求参数 (ErpStockOutSaveReqVO)**: 同 5.1（id 必传）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验出库单存在；2. 校验状态，已审核则抛 STOCK_OUT_UPDATE_FAIL_APPROVE；3. 校验客户与出库项；4. 更新出库单主表并重算 totalCount / totalPrice；5. diff 对比新老明细，批量新增、更新、删除出库项。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_000 | 其它出库单不存在 |
| 1_030_402_005 | 其它出库单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |
| 1_020_200_000 / 1_020_200_001 | 客户不存在 / 客户({})未启用 |

### 5.3 更新其它出库单的状态

- **路径**: PUT /erp/stock-out/update-status
- **权限**: erp:stock-out:update-status
- **说明**: 审核或反审核出库单；审核时扣减库存（数量取负），反审核时回补库存。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 出库单编号 |
| status | Integer | 是 | - | 目标状态：10 未审核 / 20 已审核 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验出库单存在；2. 校验状态流转，重复流转抛 STOCK_OUT_APPROVE_FAIL / STOCK_OUT_PROCESS_FAIL；3. 乐观更新状态，失败抛同上错误码；4. 查询全部出库项：审核时数量取负创建库存明细（bizType = 20 其它出库），反审核时数量为正（bizType = 21 其它出库（作废）），由库存服务校验并扣减/回补库存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_000 | 其它出库单不存在 |
| 1_030_402_002 | 反审核失败，只有已审核的出库单才能反审核 |
| 1_030_402_003 | 审核失败，只有未审核的出库单才能审核 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |
| 1_030_404_001 | 操作失败，产品({})所在仓库({})的库存不足 |

### 5.4 删除其它出库单

- **路径**: DELETE /erp/stock-out/delete
- **权限**: erp:stock-out:delete
- **说明**: 批量删除其它出库单；已审核的单据不允许删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | - | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 批量查询出库单，为空直接返回；2. 校验存在已审核单据则抛 STOCK_OUT_DELETE_FAIL_APPROVE；3. 遍历删除出库单主表与明细表记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_001 | 其它出库单({})已审核，无法删除 |

### 5.5 获得其它出库单

- **路径**: GET /erp/stock-out/get
- **权限**: erp:stock-out:query
- **说明**: 查询出库单详情，含明细项、产品信息与当前库存数量。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 出库单编号 |

**响应**: CommonResult&lt;ErpStockOutRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 出库编号 |
| no | String | 出库单号 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称（分页/详情时组装） |
| outTime | LocalDateTime | 出库时间 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 合计金额，单位：元 |
| status | Integer | 状态（10 未审核 / 20 已审核） |
| remark | String | 备注 |
| fileUrl | String | 附件 URL |
| creator | String | 创建人编号 |
| creatorName | String | 创建人名称（分页/详情时组装） |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 出库项列表 |
| productNames | String | 产品信息（分页/导出时拼接） |

**Item 子对象**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 出库项编号 |
| warehouseId | Long | 仓库编号 |
| productId | Long | 产品编号 |
| productPrice | BigDecimal | 产品单价 |
| count | BigDecimal | 产品数量 |
| remark | String | 备注 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 该仓库该产品的当前库存数量（仅在详情和编辑时使用） |

**业务逻辑**: 1. 查询出库单，不存在则返回 null；2. 查询该单出库项列表；3. 批量查询产品信息；4. 逐项填充当前库存 stockCount（无记录为 0）及产品名称/条码/单位。

### 5.6 获得其它出库单分页

- **路径**: GET /erp/stock-out/page
- **权限**: erp:stock-out:query
- **说明**: 分页查询其它出库单，组装明细、产品、客户、创建人信息。

**请求参数 (ErpStockOutPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| no | String | 否 | - | 出库单号 |
| customerId | Long | 否 | - | 客户编号 |
| outTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 出库时间区间 |
| status | Integer | 否 | @InEnum(ErpAuditStatus) | 状态 |
| remark | String | 否 | - | 备注 |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |
| warehouseId | Long | 否 | - | 仓库编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpStockOutRespVO&gt;&gt;，字段同 5.5。

**业务逻辑**: 1. 按条件分页查询出库单；2. 批量查询出库项并按单号分组，批量查询产品、客户、创建人信息；3. 组装明细、productNames、customerName、creatorName 后返回。

### 5.7 导出其它出库单 Excel

- **路径**: GET /erp/stock-out/export-excel
- **权限**: erp:stock-out:export
- **说明**: 按分页条件查询全量出库单并导出 Excel（文件名：其它出库单.xls）。

**请求参数 (ErpStockOutPageReqVO)**: 同 5.6（pageSize 强制设为 PAGE_SIZE_NONE）。

**响应**: Excel 文件流（导出列：出库编号、出库单号、客户名称、出库时间、合计数量、合计金额、状态、备注、产品信息、创建时间）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部出库单；2. 组装关联信息；3. 写出 Excel 文件流并记录 EXPORT 操作日志。

---

## 6. 库存调拨单（ErpStockMoveController）

### 6.1 创建库存调拨单

- **路径**: POST /erp/stock-move/create
- **权限**: erp:stock-move:create
- **说明**: 创建库存调拨单（跨仓库调拨明细），初始状态为未审核，不直接变更库存。

**请求参数 (ErpStockMoveSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否（创建时不传） | - | 调拨编号 |
| customerId | Long | 否 | - | 客户编号 |
| moveTime | LocalDateTime | 是 | @NotNull | 调拨时间 |
| remark | String | 否 | - | 备注 |
| fileUrl | String | 否 | - | 附件 URL |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 调拨项列表 |

**Item 子对象**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 调拨项编号 |
| fromWarehouseId | Long | 是 | @NotNull | 调出仓库编号 |
| toWarehouseId | Long | 是 | @NotNull、@AssertTrue（与调出仓库不同） | 调入仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| count | BigDecimal | 是 | @NotNull | 产品数量 |
| remark | String | 否 | - | 备注 |

（Item 内自定义校验 `isWarehouseValid`：调出、调入仓库不能相同，否则校验失败。）

**响应**: CommonResult&lt;Long&gt;（调拨单编号）

**业务逻辑**: 1. 校验调拨项：校验产品存在且启用，校验调出/调入两类仓库存在且启用；转换明细 DO，补充产品单位，计算小计金额；2. 生成 QCDB 前缀的调拨单号（Redis 日期自增），单号重复则抛 STOCK_MOVE_NO_EXISTS；3. 插入调拨单主表，状态置为未审核，汇总 totalCount / totalPrice；4. 批量插入调拨项，返回调拨单编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_000 | 库存调拨单不存在 |
| 1_030_402_001 | 库存调拨单({})已审核，无法删除 |
| 1_030_402_002 | 反审核失败，只有已审核的调拨单才能反审核 |
| 1_030_402_003 | 审核失败，只有未审核的调拨单才能审核 |
| 1_030_402_004 | 生成调拨号失败，请重新提交 |
| 1_030_402_005 | 库存调拨单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |

（注意：源码中调拨单错误码与其它出库单共用 1_030_402_xxx 段。）

### 6.2 更新库存调拨单

- **路径**: PUT /erp/stock-move/update
- **权限**: erp:stock-move:update
- **说明**: 修改未审核的库存调拨单；已审核单据不允许修改。

**请求参数 (ErpStockMoveSaveReqVO)**: 同 6.1（id 必传）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验调拨单存在；2. 校验状态，已审核则抛 STOCK_MOVE_UPDATE_FAIL_APPROVE；3. 校验调拨项（产品、调出/调入仓库）；4. 更新调拨单主表并重算 totalCount / totalPrice；5. diff 对比新老调拨项，批量新增、更新、删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_000 | 库存调拨单不存在 |
| 1_030_402_005 | 库存调拨单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |

### 6.3 更新库存调拨单的状态

- **路径**: PUT /erp/stock-move/update-status
- **权限**: erp:stock-move:update-status
- **说明**: 审核或反审核调拨单；审核时调出仓库扣库存、调入仓库加库存，反审核时反向冲销。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 调拨单编号 |
| status | Integer | 是 | - | 目标状态：10 未审核 / 20 已审核 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验调拨单存在；2. 校验状态流转，重复流转抛 STOCK_MOVE_APPROVE_FAIL / STOCK_MOVE_PROCESS_FAIL；3. 乐观更新状态，失败抛同上错误码；4. 查询全部调拨项，对每一项创建两条库存明细：调出仓库（审核时数量取负，bizType = 32 调拨出库；反审核 bizType = 33）、调入仓库（审核时数量为正，bizType = 30 调拨入库；反审核 bizType = 31），由库存服务完成增减。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_000 | 库存调拨单不存在 |
| 1_030_402_002 | 反审核失败，只有已审核的调拨单才能反审核 |
| 1_030_402_003 | 审核失败，只有未审核的调拨单才能审核 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |
| 1_030_404_001 | 操作失败，产品({})所在仓库({})的库存不足 |

### 6.4 删除库存调拨单

- **路径**: DELETE /erp/stock-move/delete
- **权限**: erp:stock-move:delete
- **说明**: 批量删除库存调拨单；已审核的单据不允许删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | - | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 批量查询调拨单，为空直接返回；2. 校验存在已审核单据则抛 STOCK_MOVE_DELETE_FAIL_APPROVE；3. 遍历删除调拨单主表与调拨项记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_402_001 | 库存调拨单({})已审核，无法删除 |

### 6.5 获得库存调拨单

- **路径**: GET /erp/stock-move/get
- **权限**: erp:stock-move:query
- **说明**: 查询调拨单详情，含调拨项、产品信息与调出仓库当前库存。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 调拨单编号 |

**响应**: CommonResult&lt;ErpStockMoveRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 调拨编号 |
| no | String | 调拨单号 |
| moveTime | LocalDateTime | 调拨时间 |
| totalCount | BigDecimal | 合计数量 |
| totalPrice | BigDecimal | 合计金额，单位：元 |
| status | Integer | 状态（10 未审核 / 20 已审核） |
| remark | String | 备注 |
| fileUrl | String | 附件 URL |
| creator | String | 创建人编号 |
| creatorName | String | 创建人名称（分页/详情时组装） |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 调拨项列表 |
| productNames | String | 产品信息（分页/导出时拼接） |

**Item 子对象**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 调拨项编号 |
| fromWarehouseId | Long | 调出仓库编号 |
| toWarehouseId | Long | 调入仓库编号 |
| productId | Long | 产品编号 |
| productPrice | BigDecimal | 产品单价 |
| count | BigDecimal | 产品数量 |
| remark | String | 备注 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |
| stockCount | BigDecimal | 调出仓库该产品的当前库存数量（仅在详情和编辑时使用） |

**业务逻辑**: 1. 查询调拨单，不存在则返回 null；2. 查询该单调拨项列表；3. 批量查询产品信息；4. 逐项查询产品在调出仓库的当前库存填充 stockCount（无记录为 0），并填充产品名称/条码/单位。

### 6.6 获得库存调拨单分页

- **路径**: GET /erp/stock-move/page
- **权限**: erp:stock-move:query
- **说明**: 分页查询库存调拨单，组装调拨项、产品、创建人信息。

**请求参数 (ErpStockMovePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| no | String | 否 | - | 调拨单号 |
| moveTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 调拨时间区间 |
| status | Integer | 否 | @InEnum(ErpAuditStatus) | 状态 |
| remark | String | 否 | - | 备注 |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |
| fromWarehouseId | Long | 否 | - | 调出仓库编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpStockMoveRespVO&gt;&gt;，字段同 6.5。

**业务逻辑**: 1. 按条件分页查询调拨单；2. 批量查询调拨项并按单号分组，批量查询产品、创建人信息；3. 组装明细、productNames、creatorName 后返回。

### 6.7 导出库存调拨单 Excel

- **路径**: GET /erp/stock-move/export-excel
- **权限**: erp:stock-move:export
- **说明**: 按分页条件查询全量调拨单并导出 Excel（文件名：库存调拨单.xls）。

**请求参数 (ErpStockMovePageReqVO)**: 同 6.6（pageSize 强制设为 PAGE_SIZE_NONE）。

**响应**: Excel 文件流（导出列：调拨编号、调拨单号、调拨时间、合计数量、合计金额、状态、备注、产品信息、创建时间）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部调拨单；2. 组装关联信息；3. 写出 Excel 文件流并记录 EXPORT 操作日志。

---

## 7. 库存盘点单（ErpStockCheckController）

> 注：该控制器的 @Tag/@Operation 源码注解沿用了“库存调拨单”文案（源码复制遗留），实际权限前缀、VO、单号前缀（QCPD）均为库存盘点。

### 7.1 创建库存盘点单

- **路径**: POST /erp/stock-check/create
- **权限**: erp:stock-check:create
- **说明**: 创建库存盘点单（含盘点明细：账面数量、实际数量、盈亏数量），初始状态为未审核，不直接变更库存。

**请求参数 (ErpStockCheckSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否（创建时不传） | - | 盘点编号 |
| checkTime | LocalDateTime | 是 | @NotNull | 盘点时间 |
| remark | String | 否 | - | 备注 |
| fileUrl | String | 否 | - | 附件 URL |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 盘点项列表 |

**Item 子对象**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 盘点项编号 |
| warehouseId | Long | 是 | @NotNull | 仓库编号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| productPrice | BigDecimal | 否 | - | 产品单价 |
| stockCount | BigDecimal | 是 | @NotNull | 账面数量（当前库存） |
| actualCount | BigDecimal | 是 | @NotNull | 实际数量（实际库存） |
| count | BigDecimal | 是 | @NotNull | 盈亏数量（实际 - 账面，正数盘盈 / 负数盘亏） |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;（盘点单编号）

**业务逻辑**: 1. 校验盘点项：校验产品存在且启用、仓库存在且启用；转换明细 DO，补充产品单位，计算小计金额；2. 生成 QCPD 前缀的盘点单号（Redis 日期自增），单号重复则抛 STOCK_CHECK_NO_EXISTS；3. 插入盘点单主表，状态置为未审核，汇总 totalCount（盈亏数量合计）/ totalPrice；4. 批量插入盘点项，返回盘点单编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_403_000 | 库存盘点单不存在 |
| 1_030_403_001 | 库存盘点单({})已审核，无法删除 |
| 1_030_403_002 | 反审核失败，只有已审核的盘点单才能反审核 |
| 1_030_403_003 | 审核失败，只有未审核的盘点单才能审核 |
| 1_030_403_004 | 生成盘点号失败，请重新提交 |
| 1_030_403_005 | 库存盘点单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |

### 7.2 更新库存盘点单

- **路径**: PUT /erp/stock-check/update
- **权限**: erp:stock-check:update
- **说明**: 修改未审核的库存盘点单；已审核单据不允许修改。

**请求参数 (ErpStockCheckSaveReqVO)**: 同 7.1（id 必传）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验盘点单存在；2. 校验状态，已审核则抛 STOCK_CHECK_UPDATE_FAIL_APPROVE；3. 校验盘点项（产品、仓库）；4. 更新盘点单主表并重算 totalCount / totalPrice；5. diff 对比新老盘点项，批量新增、更新、删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_403_000 | 库存盘点单不存在 |
| 1_030_403_005 | 库存盘点单({})已审核，无法修改 |
| 1_030_400_000 / 1_030_400_001 | 仓库不存在 / 仓库({})未启用 |
| 1_030_500_000 / 1_030_500_001 | 产品不存在 / 产品({})未启用 |

### 7.3 更新库存盘点单的状态

- **路径**: PUT /erp/stock-check/update-status
- **权限**: erp:stock-check:update-status
- **说明**: 审核或反审核盘点单；审核时按盈亏数量调整库存（盘盈入库 / 盘亏出库），反审核时反向冲销。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 盘点单编号 |
| status | Integer | 是 | - | 目标状态：10 未审核 / 20 已审核 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 校验盘点单存在；2. 校验状态流转，重复流转抛 STOCK_CHECK_APPROVE_FAIL / STOCK_CHECK_PROCESS_FAIL；3. 乐观更新状态，失败抛同上错误码；4. 查询全部盘点项，盈亏数量为 0 的项跳过不产生库存变动；5. 审核时按盈亏数量创建库存明细（大于 0 为 40 盘盈入库，小于 0 为 42 盘亏出库）；反审核时数量取负（41 盘盈入库（作废）/ 43 盘亏出库（作废）），由库存服务完成增减。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_403_000 | 库存盘点单不存在 |
| 1_030_403_002 | 反审核失败，只有已审核的盘点单才能反审核 |
| 1_030_403_003 | 审核失败，只有未审核的盘点单才能审核 |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} |
| 1_030_404_001 | 操作失败，产品({})所在仓库({})的库存不足 |

### 7.4 删除库存盘点单

- **路径**: DELETE /erp/stock-check/delete
- **权限**: erp:stock-check:delete
- **说明**: 批量删除库存盘点单；已审核的单据不允许删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | - | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 批量查询盘点单，为空直接返回；2. 校验存在已审核单据则抛 STOCK_CHECK_DELETE_FAIL_APPROVE；3. 遍历删除盘点单主表与盘点项记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_403_001 | 库存盘点单({})已审核，无法删除 |

### 7.5 获得库存盘点单

- **路径**: GET /erp/stock-check/get
- **权限**: erp:stock-check:query
- **说明**: 查询盘点单详情，含盘点项与产品信息。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 盘点单编号 |

**响应**: CommonResult&lt;ErpStockCheckRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 盘点编号 |
| no | String | 盘点单号 |
| checkTime | LocalDateTime | 盘点时间 |
| totalCount | BigDecimal | 合计数量（盈亏合计） |
| totalPrice | BigDecimal | 合计金额，单位：元 |
| status | Integer | 状态（10 未审核 / 20 已审核） |
| remark | String | 备注 |
| fileUrl | String | 附件 URL |
| creator | String | 创建人编号 |
| creatorName | String | 创建人名称（分页/详情时组装） |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 盘点项列表 |
| productNames | String | 产品信息（分页/导出时拼接） |

**Item 子对象**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 盘点项编号 |
| warehouseId | Long | 仓库编号 |
| productId | Long | 产品编号 |
| productPrice | BigDecimal | 产品单价 |
| stockCount | BigDecimal | 账面数量（当前库存） |
| actualCount | BigDecimal | 实际数量（实际库存） |
| count | BigDecimal | 盈亏数量 |
| remark | String | 备注 |
| productName | String | 产品名称 |
| productBarCode | String | 产品条码 |
| productUnitName | String | 产品单位名称 |

**业务逻辑**: 1. 查询盘点单，不存在则返回 null；2. 查询该单盘点项列表；3. 批量查询产品信息；4. 逐项填充产品名称/条码/单位后返回。

### 7.6 获得库存盘点单分页

- **路径**: GET /erp/stock-check/page
- **权限**: erp:stock-check:query
- **说明**: 分页查询库存盘点单，组装盘点项、产品、创建人信息。

**请求参数 (ErpStockCheckPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，默认 1（PageParam） |
| pageSize | Integer | 否 | - | 每页条数，默认 10（PageParam） |
| no | String | 否 | - | 盘点单号 |
| warehouseId | Long | 否 | - | 仓库编号 |
| checkTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 盘点时间区间 |
| status | Integer | 否 | @InEnum(ErpAuditStatus) | 状态 |
| remark | String | 否 | - | 备注 |
| creator | String | 否 | - | 创建者 |
| productId | Long | 否 | - | 产品编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpStockCheckRespVO&gt;&gt;，字段同 7.5。

**业务逻辑**: 1. 按条件分页查询盘点单；2. 批量查询盘点项并按单号分组，批量查询产品、创建人信息；3. 组装明细、productNames、creatorName 后返回。

### 7.7 导出库存盘点单 Excel

- **路径**: GET /erp/stock-check/export-excel
- **权限**: erp:stock-check:export
- **说明**: 按分页条件查询全量盘点单并导出 Excel（源码导出文件名为：库存调拨单.xls）。

**请求参数 (ErpStockCheckPageReqVO)**: 同 7.6（pageSize 强制设为 PAGE_SIZE_NONE）。

**响应**: Excel 文件流（导出列：盘点编号、盘点单号、盘点时间、合计数量、合计金额、状态、备注、产品信息、创建时间）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE 查询全部盘点单；2. 组装关联信息；3. 写出 Excel 文件流并记录 EXPORT 操作日志。
