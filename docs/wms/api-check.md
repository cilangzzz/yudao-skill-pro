# 盘点单接口

## 概述

盘点单管理是 wms 模块的核心功能之一，负责库存盘点操作，完成盘点后会按实际数量调整库存。

### 业务定位

- 盘点单用于核对系统库存与实际库存的差异，并进行调整
- 单据采用 Header + Detail 主子表结构，单据头存储仓库信息，明细行记录系统数量和实际数量
- 单据状态机：PREPARE(0) -> FINISHED(4) 或 CANCELED(5)

### 核心实体

| 实体 | 说明 |
|-----|------|
| CheckOrderDO | 盘点单头，包含单号、仓库、状态等 |
| CheckOrderDetailDO | 盘点明细行，包含 SKU、系统数量、实际数量等 |

## 接口列表

### 1. 创建盘点单

- **路径**: `POST /wms/check-order/create`
- **说明**: 创建盘点单及明细行
- **权限**: `wms:check-order:create`
- **请求参数**: `CheckOrderSaveReqVO`（包含单据头信息和明细行列表）
- **响应**: `CommonResult<Long>` - 盘点单编号
- **实现逻辑**:
  1. 校验仓库是否存在
  2. 生成盘点单号
  3. 插入 wms_check_order 记录
  4. 批量插入 wms_check_order_detail 记录

### 2. 更新盘点单

- **路径**: `PUT /wms/check-order/update`
- **说明**: 更新盘点单及明细行（仅 PREPARE 状态可更新）
- **权限**: `wms:check-order:update`
- **请求参数**: `CheckOrderSaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`

### 3. 删除盘点单

- **路径**: `DELETE /wms/check-order/delete`
- **说明**: 删除盘点单（仅 PREPARE 状态可删除）
- **权限**: `wms:check-order:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 盘点单编号 |

- **响应**: `CommonResult<Boolean>`

### 4. 完成盘点

- **路径**: `PUT /wms/check-order/complete`
- **说明**: 完成盘点操作，按实际数量调整库存
- **权限**: `wms:check-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 盘点单编号 |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验单据状态为 PREPARE
  2. 遍历明细行，对每个 SKU 执行库存调整：
     - `SELECT ... FOR UPDATE` 锁定库存记录
     - 计算差异：actualQuantity - systemQuantity
     - 更新库存数量为实际数量
  3. 记录库存变动历史（InventoryHistoryDO）
  4. 更新单据状态为 FINISHED

### 5. 取消盘点

- **路径**: `PUT /wms/check-order/cancel`
- **说明**: 取消盘点单（仅 PREPARE 状态可取消）
- **权限**: `wms:check-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 盘点单编号 |

- **响应**: `CommonResult<Boolean>`

### 6. 获取盘点单详情

- **路径**: `GET /wms/check-order/get`
- **说明**: 获取盘点单详情，包含明细行
- **权限**: `wms:check-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 盘点单编号 |

- **响应**: `CommonResult<CheckOrderRespVO>`

### 7. 盘点单分页查询

- **路径**: `GET /wms/check-order/page`
- **说明**: 分页查询盘点单列表
- **权限**: `wms:check-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| no | String | 否 | 盘点单号（模糊匹配） |
| warehouseId | Long | 否 | 仓库编号 |
| status | Integer | 否 | 单据状态 |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<CheckOrderRespVO>>`

### 8. 导出盘点单 Excel

- **路径**: `GET /wms/check-order/export-excel`
- **说明**: 导出盘点单数据为 Excel
- **权限**: `wms:check-order:export`
- **响应**: Excel 文件流

---

## 盘点明细接口

### 9. 根据单据查询明细列表

- **路径**: `GET /wms/check-order-detail/list-by-order-id`
- **说明**: 查询指定盘点单的明细行列表
- **权限**: `wms:check-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| orderId | Long | 是 | 盘点单编号 |

- **响应**: `CommonResult<List<CheckOrderDetailRespVO>>`

## 关键实现

- **系统数量**: 盘点明细中的 systemQuantity 记录盘点时的系统库存数量，actualQuantity 为实际盘点数量
- **库存调整**: 完成盘点时直接将库存数量设置为实际数量，而非增量调整
- **并发安全**: 完成盘点时使用 `SELECT ... FOR UPDATE` 行锁保证并发安全
