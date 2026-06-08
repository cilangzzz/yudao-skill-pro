# 移库单接口

## 概述

移库单管理是 wms 模块的核心功能之一，负责物料在不同仓库之间的调拨操作，完成移库后会减少源仓库库存并增加目标仓库库存。

### 业务定位

- 移库单是库间调拨的唯一途径，支持仓库间的物料转移
- 单据采用 Header + Detail 主子表结构，单据头存储源仓库和目标仓库，明细行存储 SKU 级别数据
- 单据状态机：PREPARE(0) -> FINISHED(4) 或 CANCELED(5)

### 核心实体

| 实体 | 说明 |
|-----|------|
| MovementOrderDO | 移库单头，包含单号、源仓库、目标仓库、状态等 |
| MovementOrderDetailDO | 移库明细行，包含 SKU、数量等 |

## 接口列表

### 1. 创建移库单

- **路径**: `POST /wms/movement-order/create`
- **说明**: 创建移库单及明细行
- **权限**: `wms:movement-order:create`
- **请求参数**: `MovementOrderSaveReqVO`（包含单据头信息和明细行列表）
- **响应**: `CommonResult<Long>` - 移库单编号
- **实现逻辑**:
  1. 校验源仓库和目标仓库是否存在且不相同
  2. 生成移库单号
  3. 插入 wms_movement_order 记录
  4. 批量插入 wms_movement_order_detail 记录

### 2. 更新移库单

- **路径**: `PUT /wms/movement-order/update`
- **说明**: 更新移库单及明细行（仅 PREPARE 状态可更新）
- **权限**: `wms:movement-order:update`
- **请求参数**: `MovementOrderSaveReqVO`（包含 id）
- **响应**: `CommonResult<Boolean>`

### 3. 删除移库单

- **路径**: `DELETE /wms/movement-order/delete`
- **说明**: 删除移库单（仅 PREPARE 状态可删除）
- **权限**: `wms:movement-order:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 移库单编号 |

- **响应**: `CommonResult<Boolean>`

### 4. 完成移库

- **路径**: `PUT /wms/movement-order/complete`
- **说明**: 完成移库操作，触发源仓库库存减少和目标仓库库存增加
- **权限**: `wms:movement-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 移库单编号 |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验单据状态为 PREPARE
  2. 遍历明细行，对每个 SKU 执行双向库存变更：
     - 源仓库：`SELECT ... FOR UPDATE` 锁定库存记录，减少库存数量
     - 目标仓库：`SELECT ... FOR UPDATE` 锁定库存记录，增加库存数量
  3. 记录两条库存变动历史（一减一增）
  4. 更新单据状态为 FINISHED

### 5. 取消移库

- **路径**: `PUT /wms/movement-order/cancel`
- **说明**: 取消移库单（仅 PREPARE 状态可取消）
- **权限**: `wms:movement-order:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 移库单编号 |

- **响应**: `CommonResult<Boolean>`

### 6. 获取移库单详情

- **路径**: `GET /wms/movement-order/get`
- **说明**: 获取移库单详情，包含明细行
- **权限**: `wms:movement-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 移库单编号 |

- **响应**: `CommonResult<MovementOrderRespVO>`

### 7. 移库单分页查询

- **路径**: `GET /wms/movement-order/page`
- **说明**: 分页查询移库单列表
- **权限**: `wms:movement-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| no | String | 否 | 移库单号（模糊匹配） |
| fromWarehouseId | Long | 否 | 源仓库编号 |
| toWarehouseId | Long | 否 | 目标仓库编号 |
| status | Integer | 否 | 单据状态 |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<MovementOrderRespVO>>`

### 8. 导出移库单 Excel

- **路径**: `GET /wms/movement-order/export-excel`
- **说明**: 导出移库单数据为 Excel
- **权限**: `wms:movement-order:export`
- **响应**: Excel 文件流

---

## 移库明细接口

### 9. 根据单据查询明细列表

- **路径**: `GET /wms/movement-order-detail/list-by-order-id`
- **说明**: 查询指定移库单的明细行列表
- **权限**: `wms:movement-order:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| orderId | Long | 是 | 移库单编号 |

- **响应**: `CommonResult<List<MovementOrderDetailRespVO>>`

## 关键实现

- **双向库存变更**: 完成移库时同时操作源仓库和目标仓库的库存，需注意两个锁的获取顺序避免死锁
- **库存校验**: 移库前校验源仓库库存数量足够
- **源目标仓库校验**: 创建时校验源仓库和目标仓库不相同
