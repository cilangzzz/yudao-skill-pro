# 入库单接口

## 概述

入库单管理是 wms 模块的核心功能之一，负责物料的入库操作，完成入库后会增加对应 SKU 在目标仓库的库存。

### 业务定位

- 入库单是库存增加的唯一途径，支持采购入库、退货入库等场景
- 单据采用 Header + Detail 主子表结构，单据头存储汇总信息，明细行存储 SKU 级别数据
- 单据状态机：PREPARE(0) -> FINISHED(4) 或 CANCELED(5)

### 核心实体

| 实体 | 说明 |
|-----|------|
| ReceiptOrderDO | 入库单头，包含单号、仓库、商户、状态等 |
| ReceiptOrderDetailDO | 入库明细行，包含 SKU、数量、单价等 |

## 接口列表

### 1. 创建入库单

- **路径**: `POST /wms/receipt-order/create`
- **说明**: 创建入库单及明细行
- **权限**: `wms:receipt-order:create`
- **请求参数**: `ReceiptOrderSaveReqVO`（包含单据头信息和明细行列表）
- **响应**: `CommonResult<Long>` - 入库单编号
- **实现逻辑**:
  1. 校验仓库和商户是否存在
  2. 生成入库单号
  3. 插入 wms_receipt_order 记录
  4. 批量插入 wms_receipt_order_detail 记录

### 2. 更新入库单

- **路径**: `PUT /wms/receipt-order/update`
- **说明**: 更新入库单及明细行（仅 PREPARE 状态可更新）
- **权限**: `wms:receipt-order:update`
- **请求参数**: `ReceiptOrderSaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验单据状态为 PREPARE
  2. 更新 wms_receipt_order 记录
  3. 先删除旧明细行，再批量插入新明细行

### 3. 删除入库单

- **路径**: `DELETE /wms/receipt-order/delete`
- **说明**: 删除入库单（仅 PREPARE 状态可删除）
- **权限**: `wms:receipt-order:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 入库单编号 |

- **响应**: `CommonResult<Boolean>`

### 4. 完成入库

- **路径**: `PUT /wms/receipt-order/complete`
- **说明**: 完成入库操作，触发库存增加
- **权限**: `wms:receipt-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 入库单编号 |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验单据状态为 PREPARE
  2. 遍历明细行，对每个 SKU 执行库存增加：
     - `SELECT ... FOR UPDATE` 锁定库存记录
     - 若记录不存在则插入（捕获 DuplicateKeyException）
     - 更新库存数量
  3. 记录库存变动历史（InventoryHistoryDO）
  4. 更新单据状态为 FINISHED

### 5. 取消入库

- **路径**: `PUT /wms/receipt-order/cancel`
- **说明**: 取消入库单（仅 PREPARE 状态可取消）
- **权限**: `wms:receipt-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 入库单编号 |

- **响应**: `CommonResult<Boolean>`

### 6. 获取入库单详情

- **路径**: `GET /wms/receipt-order/get`
- **说明**: 获取入库单详情，包含明细行
- **权限**: `wms:receipt-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 入库单编号 |

- **响应**: `CommonResult<ReceiptOrderRespVO>`

### 7. 入库单分页查询

- **路径**: `GET /wms/receipt-order/page`
- **说明**: 分页查询入库单列表
- **权限**: `wms:receipt-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| no | String | 否 | 入库单号（模糊匹配） |
| warehouseId | Long | 否 | 仓库编号 |
| merchantId | Long | 否 | 商户编号 |
| status | Integer | 否 | 单据状态 |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ReceiptOrderRespVO>>`
- **实现逻辑**:
  1. 分页查询 wms_receipt_order 表
  2. 批量查询关联的用户信息（AdminUserApi.getUserMap()）
  3. 通过 BeanUtils.toBean() 组装 VO

### 8. 导出入库单 Excel

- **路径**: `GET /wms/receipt-order/export-excel`
- **说明**: 导出入库单数据为 Excel
- **权限**: `wms:receipt-order:export`
- **响应**: Excel 文件流

---

## 入库明细接口

### 9. 根据单据查询明细列表

- **路径**: `GET /wms/receipt-order-detail/list-by-order-id`
- **说明**: 查询指定入库单的明细行列表
- **权限**: `wms:receipt-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| orderId | Long | 是 | 入库单编号 |

- **响应**: `CommonResult<List<ReceiptOrderDetailRespVO>>`

## 关键实现

- **单号生成**: 入库单号通过规则自动生成，确保唯一性
- **并发库存更新**: 完成入库时使用 `SELECT ... FOR UPDATE` 行锁保证并发安全
- **库存懒初始化**: 首次入库时库存记录可能不存在，通过 `DuplicateKeyException` 捕获实现懒初始化
- **来源类型标识**: 入库单类型范围为 [100, 200)，用于库存历史记录的 sourceOrderType
