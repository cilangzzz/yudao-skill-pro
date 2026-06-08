# 工具管理 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 工具台账（Tool）

**Controller**: `MesToolController`
**路径前缀**: `/admin-api/mes/tool`
**权限前缀**: `mes:tool:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建工具 | `mes:tool:create` |
| PUT | `/update` | 更新工具 | `mes:tool:update` |
| DELETE | `/delete` | 删除工具 | `mes:tool:delete` |
| GET | `/get` | 获取工具详情 | `mes:tool:query` |
| GET | `/page` | 工具分页查询 | `mes:tool:query` |
| GET | `/list-all` | 获取所有工具（下拉选择用） | `mes:tool:query` |

### 1.2 请求/响应 VO

**MesToolSaveReqVO**（创建/更新请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 工具名称 |
| toolTypeId | Long | 是 | 工具类型编号 |
| code | String | 是 | 工具编码 |
| spec | String | 否 | 规格型号 |
| workshopId | Long | 否 | 所属车间编号 |
| workstationId | Long | 否 | 所属工位编号 |
| status | Integer | 是 | 工具状态 |
| remark | String | 否 | 备注 |

### 1.3 工具状态

| 值 | 说明 |
|----|------|
| 0 | 正常 |
| 1 | 使用中 |
| 2 | 维修中 |
| 3 | 报废 |

---

## 2. 工具类型（ToolType）

**Controller**: `MesToolTypeController`
**路径前缀**: `/admin-api/mes/tool-type`
**权限前缀**: `mes:tool-type:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建工具类型 | `mes:tool-type:create` |
| PUT | `/update` | 更新工具类型 | `mes:tool-type:update` |
| DELETE | `/delete` | 删除工具类型 | `mes:tool-type:delete` |
| GET | `/get` | 获取类型详情 | `mes:tool-type:query` |
| GET | `/list` | 获取类型列表（树形） | `mes:tool-type:query` |

---

## 核心设计要点

### 工位关联

工具可通过 `mes_md_workstation_tool` 表与工位关联，表示该工位使用的工具。

### 与生产联动

- 生产任务执行时记录使用的工具
- 工具状态变更（使用中/空闲）与生产任务关联
- 工具维修期间，关联的工位任务可能需要调整

### 工具追溯

通过工具编码可追溯：
- 工具的使用历史（哪些工单、哪些工序使用过）
- 工具的维修记录
- 工具的使用寿命统计
