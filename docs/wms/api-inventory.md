# 库存接口 (WmsInventoryController / WmsInventoryHistoryController)

> WMS 库存域负责库存余额（按 SKU + 仓库维度）的统计查询与库存流水（库存变动记录）的查询；库存余额的写入由入库/出库/移库/盘库等单据域通过 Service 内部调用完成，本域对 admin 端只提供只读查询接口。

## 接口路径前缀

- /wms/inventory (Controller: WmsInventoryController) —— 库存统计
- /wms/inventory-history (Controller: WmsInventoryHistoryController) —— 库存流水

## 1. 库存统计（WmsInventoryController）

### 1.1 获得库存统计分页

- **路径**: GET /wms/inventory/page
- **权限**: wms:inventory:query
- **说明**: 按"仓库"或"商品"两种统计维度分页查询库存余额，支持按商品编码/名称、SKU、仓库、最小库存数量等条件过滤。

**请求参数 (WmsInventoryPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 分页参数（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 分页参数（继承 PageParam） | 每页条数 |
| type | String | 是 | @NotBlank | 统计维度：`warehouse`（按仓库维度统计）或 `item`（按商品维度统计），仅影响排序方式 |
| itemCode | String | 否 | — | 商品编码（模糊匹配） |
| itemName | String | 否 | — | 商品名称（模糊匹配） |
| skuId | Long | 否 | — | 商品 SKU 编号（精确匹配） |
| skuCode | String | 否 | — | 规格编号（模糊匹配） |
| skuName | String | 否 | — | 规格名称（模糊匹配） |
| warehouseId | Long | 否 | — | 仓库编号（精确匹配） |
| minQuantity | BigDecimal | 否 | — | 最小库存数量（quantity >= minQuantity） |
| onlyPositiveQuantity | Boolean | 否 | — | 是否只查询正库存（为 true 时仅返回 quantity > 0 的记录） |

**响应**: CommonResult&lt;PageResult&lt;WmsInventoryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 库存余额行编号 |
| itemId | Long | 商品编号（由 SKU 反查填充） |
| itemCode | String | 商品编码 |
| itemName | String | 商品名称 |
| unit | String | 商品单位 |
| skuId | Long | 商品 SKU 编号 |
| skuCode | String | 规格编号 |
| skuName | String | 规格名称 |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称 |
| quantity | BigDecimal | 库存数量 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. Mapper 使用 MPJ 联表查询库存余额表，inner join 商品 SKU 表（wms_item_sku）和商品表（wms_item），按传入条件拼接模糊/精确过滤与最小库存、正库存过滤。
2. 根据统计维度 `type` 决定排序：`warehouse` 按仓库编号 → 商品编号 → SKU 编号 → 库存行 ID 升序；`item` 按商品编号 → SKU 编号 → 仓库编号 → 库存行 ID 升序；传入未知维度抛出 IllegalArgumentException。
3. Service 直接调用 Mapper 分页查询返回 PageResult&lt;WmsInventoryDO&gt;。
4. Controller 批量根据 skuId 集合查询 SKU Map，再根据 SKU 的 itemId 集合查询商品 Map，根据 warehouseId 集合查询仓库 Map。
5. 将库存 DO 拷贝为 RespVO，并回填 skuCode/skuName/itemId、itemCode/itemName/unit、warehouseName 等关联展示字段后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_060_300_000 | 库存不足，商品：{}，商品规格：{}，仓库：{}，当前库存：{}，变更数量：{}（库存域通用错误码，由单据域变更库存时抛出） |

### 1.2 获得库存统计列表

- **路径**: GET /wms/inventory/list
- **权限**: wms:inventory:query
- **说明**: 查询指定仓库下的全部库存余额列表（不分页），常用于下拉选择、盘库单加载库存等场景。

**请求参数 (WmsInventoryListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| warehouseId | Long | 是 | @NotNull | 仓库编号 |

**响应**: CommonResult&lt;List&lt;WmsInventoryRespVO&gt;&gt;，List 元素字段同 1.1 的 WmsInventoryRespVO。

**业务逻辑**:
1. Service 调用 Mapper 按仓库编号精确查询库存余额列表。
2. 结果按 skuId 升序、库存行 ID 升序排序。
3. Controller 复用与分页接口相同的 VO 拼接逻辑：批量查询 SKU、商品、仓库 Map 并回填关联展示字段后返回。

## 2. 库存流水（WmsInventoryHistoryController）

### 2.1 获得库存流水分页

- **路径**: GET /wms/inventory-history/page
- **权限**: wms:inventory-history:query
- **说明**: 分页查询库存变动流水（由入库、出库、移库、盘库等单据在变更库存时写入），支持按商品/SKU/仓库/单据号/单据类型/操作时间区间过滤。

**请求参数 (WmsInventoryHistoryPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 分页参数（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | 分页参数（继承 PageParam） | 每页条数 |
| itemCode | String | 否 | — | 商品编码（模糊匹配） |
| itemName | String | 否 | — | 商品名称（模糊匹配） |
| skuId | Long | 否 | — | 商品 SKU 编号（精确匹配） |
| skuCode | String | 否 | — | 规格编号（模糊匹配） |
| skuName | String | 否 | — | 规格名称（模糊匹配） |
| warehouseId | Long | 否 | — | 仓库编号（精确匹配） |
| orderNo | String | 否 | — | 单据号（精确匹配），如 RK202605110001 |
| orderType | Integer | 否 | — | 单据类型（精确匹配） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 操作时间区间（数组两个元素为起止时间） |

**响应**: CommonResult&lt;PageResult&lt;WmsInventoryHistoryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 流水编号 |
| itemId | Long | 商品编号（由 SKU 反查填充） |
| itemCode | String | 商品编码 |
| itemName | String | 商品名称 |
| unit | String | 商品单位 |
| skuId | Long | 商品 SKU 编号 |
| skuCode | String | 规格编号 |
| skuName | String | 规格名称 |
| warehouseId | Long | 仓库编号 |
| warehouseName | String | 仓库名称 |
| quantity | BigDecimal | 库存变化数量（正数为增加、负数为减少；盘库时为盘盈亏数量） |
| beforeQuantity | BigDecimal | 变化前库存数量 |
| afterQuantity | BigDecimal | 变化后库存数量 |
| price | BigDecimal | 单价 |
| totalPrice | BigDecimal | 库存变化金额 |
| remark | String | 备注 |
| orderId | Long | 单据编号 |
| orderNo | String | 单据号 |
| orderType | Integer | 单据类型 |
| createTime | LocalDateTime | 创建时间（操作时间） |

**业务逻辑**:
1. Mapper 使用 MPJ 联表查询库存流水表，left join 商品 SKU 表（wms_item_sku）和商品表（wms_item），按传入条件拼接过滤（商品/规格模糊、SKU/仓库/单据号/单据类型精确、创建时间 between）。
2. 结果按创建时间降序、流水 ID 降序排序后分页返回。
3. Controller 批量根据 skuId 集合查询 SKU Map，再根据 SKU 的 itemId 集合查询商品 Map，根据 warehouseId 集合查询仓库 Map。
4. 将流水 DO 拷贝为 RespVO，并回填 skuCode/skuName/itemId、itemCode/itemName/unit、warehouseName 等关联展示字段后返回。

## 附：库存域内部机制说明（无 admin 端点）

库存余额与流水的写入不通过 admin 接口暴露，而由各单据域在事务内调用 WmsInventoryService 完成：

- **changeInventory（库存变更）**: 先按"SKU + 仓库"唯一键补齐并批量锁定（FOR UPDATE）库存余额行（缺失行创建为 0 库存，并发插入冲突时按唯一索引回查）；在内存中计算变更前后数量并校验库存充足（不足抛 1_060_300_000），全部通过后批量更新库存数量，并批量写入库存流水（含变更前后数量、单价、金额、单据信息）。
- **checkInventory（盘库复核）**: 逐条锁定或创建盘库明细对应的库存余额行（已有行校验 SKU/仓库/当前库存与盘库单加载时一致，不一致抛 1_060_203_007 盘库单库存已变化）；账面数量与盘库数量一致（无盈亏）时跳过，有差异时批量更新库存数量并按 0 → 盘库数量或差额生成盘库流水。
- **库存行唯一键**: wms_inventory 以 skuId + warehouseId 为唯一索引；wms_inventory_history 为只增不改的流水表，由 createInventoryHistoryList 批量插入。
