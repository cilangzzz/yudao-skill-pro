# 出库单接口

## 概述

出库单管理是 wms 模块的核心功能之一，负责物料的出库操作，完成出库后会减少对应 SKU 在源仓库的库存。

### 业务定位

- 出库单是库存减少的唯一途径，支持销售出库、退货出库等场景
- 单据采用 Header + Detail 主子表结构，单据头存储汇总信息，明细行存储 SKU 级别数据
- 单据状态机：PREPARE(0) -> FINISHED(4) 或 CANCELED(5)

### 核心实体

| 实体 | 说明 |
|-----|------|
| ShipmentOrderDO | 出库单头，包含单号、仓库、商户、状态等 |
| ShipmentOrderDetailDO | 出库明细行，包含 SKU、数量、单价等 |

## 接口列表

### 1. 创建出库单

- **路径**: `POST /wms/shipment-order/create`
- **说明**: 创建出库单及明细行
- **权限**: `wms:shipment-order:create`
- **请求参数**: `ShipmentOrderSaveReqVO`（包含单据头信息和明细行列表）
- **响应**: `CommonResult<Long>` - 出库单编号
- **实现逻辑**:
  1. 校验仓库和商户是否存在
  2. 生成出库单号
  3. 插入 wms_shipment_order 记录
  4. 批量插入 wms_shipment_order_detail 记录

### 2. 更新出库单

- **路径**: `PUT /wms/shipment-order/update`
- **说明**: 更新出库单及明细行（仅 PREPARE 状态可更新）
- **权限**: `wms:shipment-order:update`
- **请求参数**: `ShipmentOrderSaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`

### 3. 删除出库单

- **路径**: `DELETE /wms/shipment-order/delete`
- **说明**: 删除出库单（仅 PREPARE 状态可删除）
- **权限**: `wms:shipment-order:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 出库单编号 |

- **响应**: `CommonResult<Boolean>`

### 4. 完成出库

- **路径**: `PUT /wms/shipment-order/complete`
- **说明**: 完成出库操作，触发库存减少
- **权限**: `wms:shipment-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 出库单编号 |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验单据状态为 PREPARE
  2. 遍历明细行，对每个 SKU 执行库存减少：
     - `SELECT ... FOR UPDATE` 锁定库存记录
     - 校验库存数量足够
     - 更新库存数量
  3. 记录库存变动历史（InventoryHistoryDO）
  4. 更新单据状态为 FINISHED

### 5. 取消出库

- **路径**: `PUT /wms/shipment-order/cancel`
- **说明**: 取消出库单（仅 PREPARE 状态可取消）
- **权限**: `wms:shipment-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 出库单编号 |

- **响应**: `CommonResult<Boolean>`

### 6. 获取出库单详情

- **路径**: `GET /wms/shipment-order/get`
- **说明**: 获取出库单详情，包含明细行
- **权限**: `wms:shipment-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 出库单编号 |

- **响应**: `CommonResult<ShipmentOrderRespVO>`

### 7. 出库单分页查询

- **路径**: `GET /wms/shipment-order/page`
- **说明**: 分页查询出库单列表
- **权限**: `wms:shipment-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| no | String | 否 | 出库单号（模糊匹配） |
| warehouseId | Long | 否 | 仓库编号 |
| merchantId | Long | 否 | 商户编号 |
| status | Integer | 否 | 单据状态 |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ShipmentOrderRespVO>>`

### 8. 导出出库单 Excel

- **路径**: `GET /wms/shipment-order/export-excel`
- **说明**: 导出出库单数据为 Excel
- **权限**: `wms:shipment-order:export`
- **响应**: Excel 文件流

---

## 出库明细接口

### 9. 根据单据查询明细列表

- **路径**: `GET /wms/shipment-order-detail/list-by-order-id`
- **说明**: 查询指定出库单的明细行列表
- **权限**: `wms:shipment-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| orderId | Long | 是 | 出库单编号 |

- **响应**: `CommonResult<List<ShipmentOrderDetailRespVO>>`

## 关键实现

- **单号生成**: 出库单号通过规则自动生成，确保唯一性
- **并发库存更新**: 完成出库时使用 `SELECT ... FOR UPDATE` 行锁保证并发安全
- **库存校验**: 出库前校验库存数量足够，不足时抛出业务异常
- **来源类型标识**: 出库单类型范围为 [200, 300)，用于库存历史记录的 sourceOrderType
