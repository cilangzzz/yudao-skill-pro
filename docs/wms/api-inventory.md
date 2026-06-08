# 库存管理接口

## 概述

库存管理是 wms 模块的核心功能之一，提供库存余额查询和库存变动历史查询能力。

### 业务定位

- 库存以 SKU + 仓库维度跟踪，是整个仓储系统的数据中枢
- 库存 Controller 为只读设计，所有库存变更必须通过单据完成操作触发
- 库存历史记录每笔变动的前后数量、价格和来源单据，支持完整的审计追踪

### 核心实体

| 实体 | 说明 |
|-----|------|
| InventoryDO | 库存余额，记录某 SKU 在某仓库的当前库存数量 |
| InventoryHistoryDO | 库存变动历史，记录每次库存变动的详情（前后数量、价格、来源单据） |

## 接口列表

### 1. 库存分页查询

- **路径**: `GET /wms/inventory/page`
- **说明**: 分页查询库存余额列表
- **权限**: `wms:inventory:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| skuId | Long | 否 | SKU 编号 |
| warehouseId | Long | 否 | 仓库编号 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<InventoryRespVO>>`
- **实现逻辑**:
  1. 根据查询条件分页查询 wms_inventory 表
  2. 返回库存列表，包含 SKU 和仓库信息

### 2. 库存列表查询

- **路径**: `GET /wms/inventory/list`
- **说明**: 查询库存列表（不分页）
- **权限**: `wms:inventory:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| skuId | Long | 否 | SKU 编号 |
| warehouseId | Long | 否 | 仓库编号 |

- **响应**: `CommonResult<List<InventoryRespVO>>`

### 3. 库存历史分页查询

- **路径**: `GET /wms/inventory-history/page`
- **说明**: 分页查询库存变动历史
- **权限**: `wms:inventory-history:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| skuId | Long | 否 | SKU 编号 |
| warehouseId | Long | 否 | 仓库编号 |
| sourceOrderType | Integer | 否 | 来源单据类型 |
| sourceOrderId | Long | 否 | 来源单据编号 |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<InventoryHistoryRespVO>>`

## 库存变更机制

### 变更触发

库存变更仅通过以下单据完成操作触发：

| 单据类型 | 操作 | 库存影响 | 来源类型范围 |
|---------|------|---------|------------|
| 入库单 | complete | 增加库存 | [100, 200) |
| 出库单 | complete | 减少库存 | [200, 300) |
| 移库单 | complete | 源仓库减少、目标仓库增加 | - |
| 盘点单 | complete | 按实际数量调整 | - |

### 并发安全

- 使用 `SELECT ... FOR UPDATE` 行锁确保库存更新的原子性
- 首次入库时库存记录可能不存在，通过 `DuplicateKeyException` 捕获实现懒初始化
- 详见 [pitfalls.md](pitfalls.md) 中的并发安全说明

## 关键实现

- **InventoryService**: 库存服务接口，提供库存查询和变更方法
- **InventoryMapper**: 库存 Mapper，继承 BaseMapperX，提供分页和列表查询
- **InventoryHistoryService**: 库存历史服务，记录每笔库存变动
- **WmsOrderTypeConstants**: 订单类型常量，定义入库 [100,200)、出库 [200,300) 等类型范围
