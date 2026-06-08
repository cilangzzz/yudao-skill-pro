# 设备管理 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 设备台账（Machinery）

**Controller**: `MesMachineryController`
**路径前缀**: `/admin-api/mes/machinery`
**权限前缀**: `mes:machinery:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建设备 | `mes:machinery:create` |
| PUT | `/update` | 更新设备 | `mes:machinery:update` |
| DELETE | `/delete` | 删除设备 | `mes:machinery:delete` |
| GET | `/get` | 获取设备详情 | `mes:machinery:query` |
| GET | `/page` | 设备分页查询 | `mes:machinery:query` |
| GET | `/list-all` | 获取所有设备（下拉选择用） | `mes:machinery:query` |

### 1.2 请求/响应 VO

**MesMachinerySaveReqVO**（创建/更新请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 设备名称 |
| machineryTypeId | Long | 是 | 设备类型编号 |
| code | String | 是 | 设备编码 |
| specification | String | 否 | 规格型号 |
| workshopId | Long | 否 | 所属车间编号 |
| workstationId | Long | 否 | 所属工位编号 |
| purchaseDate | LocalDate | 否 | 购置日期 |
| warrantyDate | LocalDate | 否 | 保修到期日期 |
| status | Integer | 是 | 设备状态 |
| remark | String | 否 | 备注 |

### 1.3 设备状态

| 值 | 说明 |
|----|------|
| 0 | 正常运行 |
| 1 | 维修中 |
| 2 | 保养中 |
| 3 | 停用 |

---

## 2. 设备类型（MachineryType）

**Controller**: `MesMachineryTypeController`
**路径前缀**: `/admin-api/mes/machinery-type`
**权限前缀**: `mes:machinery-type:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建设备类型 | `mes:machinery-type:create` |
| PUT | `/update` | 更新设备类型 | `mes:machinery-type:update` |
| DELETE | `/delete` | 删除设备类型 | `mes:machinery-type:delete` |
| GET | `/get` | 获取类型详情 | `mes:machinery-type:query` |
| GET | `/list` | 获取类型列表（树形） | `mes:machinery-type:query` |

---

## 3. 点检计划（CheckPlan）

**Controller**: `MesCheckPlanController`
**路径前缀**: `/admin-api/mes/check-plan`
**权限前缀**: `mes:check-plan:*`

### 3.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建点检计划 | `mes:check-plan:create` |
| PUT | `/update` | 更新点检计划 | `mes:check-plan:update` |
| DELETE | `/delete` | 删除点检计划 | `mes:check-plan:delete` |
| GET | `/get` | 获取计划详情（含关联设备/检查项） | `mes:check-plan:query` |
| GET | `/page` | 计划分页查询 | `mes:check-plan:query` |

### 3.2 点检计划结构

| 子表 | 说明 |
|------|------|
| `mes_dv_check_plan_machinery` | 计划关联的设备列表 |
| `mes_dv_check_plan_subject` | 计划关联的检查项目 |

### 3.3 检查项目（Subject）

**Controller**: `MesSubjectController`
**路径前缀**: `/admin-api/mes/subject`
**权限前缀**: `mes:subject:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建检查项目 | `mes:subject:create` |
| PUT | `/update` | 更新检查项目 | `mes:subject:update` |
| DELETE | `/delete` | 删除检查项目 | `mes:subject:delete` |
| GET | `/get` | 获取项目详情 | `mes:subject:query` |
| GET | `/page` | 项目分页查询 | `mes:subject:query` |
| GET | `/list-all` | 获取所有检查项目 | `mes:subject:query` |

> 检查项目（Subject）定义点检的具体检查内容，如温度、压力、振动、润滑等。

---

## 4. 点检记录（CheckRecord）

**Controller**: `MesCheckRecordController`
**路径前缀**: `/admin-api/mes/check-record`
**权限前缀**: `mes:check-record:*`

### 4.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建点检记录 | `mes:check-record:create` |
| PUT | `/update` | 更新点检记录 | `mes:check-record:update` |
| DELETE | `/delete` | 删除点检记录 | `mes:check-record:delete` |
| GET | `/get` | 获取记录详情（含检查行） | `mes:check-record:query` |
| GET | `/page` | 记录分页查询 | `mes:check-record:query` |

### 4.2 点检记录结构

| 层级 | 表 | 说明 |
|------|---|------|
| 记录主表 | `mes_dv_check_record` | 设备、点检日期、点检人、整体结果 |
| 检查行 | `mes_dv_check_record_line` | 每个检查项目的实际值、判定结果 |

---

## 5. 保养记录（MaintenRecord）

**Controller**: `MesMaintenRecordController`
**路径前缀**: `/admin-api/mes/mainten-record`
**权限前缀**: `mes:mainten-record:*`

### 5.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建保养记录 | `mes:mainten-record:create` |
| PUT | `/update` | 更新保养记录 | `mes:mainten-record:update` |
| DELETE | `/delete` | 删除保养记录 | `mes:mainten-record:delete` |
| GET | `/get` | 获取记录详情（含保养行） | `mes:mainten-record:query` |
| GET | `/page` | 记录分页查询 | `mes:mainten-record:query` |

### 5.2 保养记录结构

| 层级 | 表 | 说明 |
|------|---|------|
| 记录主表 | `mes_dv_mainten_record` | 设备、保养日期、保养人、保养类型 |
| 保养行 | `mes_dv_mainten_record_line` | 保养项目明细（保养内容、用料、工时） |

---

## 6. 维修管理（Repair）

**Controller**: `MesRepairController`
**路径前缀**: `/admin-api/mes/repair`
**权限前缀**: `mes:repair:*`

### 6.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建维修单 | `mes:repair:create` |
| PUT | `/update` | 更新维修单 | `mes:repair:update` |
| DELETE | `/delete` | 删除维修单 | `mes:repair:delete` |
| GET | `/get` | 获取维修单详情（含维修行） | `mes:repair:query` |
| GET | `/page` | 维修单分页查询 | `mes:repair:query` |
| POST | `/submit` | 提交维修单 | `mes:repair:update` |
| POST | `/confirm` | 确认维修单 | `mes:repair:update` |
| POST | `/finish` | 完成维修 | `mes:repair:update` |

### 6.2 状态枚举

**MesRepairStatusEnum**:

| 值 | 说明 | 可流转到 |
|----|------|---------|
| 0 | 草稿 | 提交(1) |
| 1 | 待确认 | 确认(2) |
| 2 | 维修中 | 完成(3) |
| 3 | 已完成 | - |

### 6.3 维修单结构

| 层级 | 表 | 说明 |
|------|---|------|
| 维修单主表 | `mes_dv_repair` | 设备、故障描述、维修人、状态 |
| 维修行 | `mes_dv_repair_line` | 维修明细（更换配件、维修内容、工时） |

### 6.4 维修流程

```
1. 发现设备故障 -> 创建维修单（草稿状态）
2. 提交维修单 -> 进入待确认状态
3. 维修人员确认 -> 开始维修（维修中状态）
4. 维修完成 -> 记录维修明细 -> 完成维修
5. 设备状态自动恢复为"正常运行"
```

---

## 核心设计要点

### 设备状态联动

设备状态与各类操作联动：
- 提交维修单 -> 设备状态变为"维修中"
- 完成维修 -> 设备状态恢复为"正常"
- 开始保养 -> 设备状态变为"保养中"
- 完成保养 -> 设备状态恢复为"正常"

### 点检计划执行

点检计划支持周期性执行：
- 计划定义检查频率（日检、周检、月检）
- 按计划自动生成待办点检任务
- 点检完成后记录实际检查结果
- 异常结果自动触发维修流程

### 与生产联动

设备管理与生产管理紧密关联：
- 工位绑定设备（`mes_md_workstation_machine`）
- 生产任务关联设备
- 设备维修/保养期间，关联的生产任务需要调整

### 与仓库联动

设备维修涉及备件管理：
- 维修用料通过仓库出库（MiscIssue）
- 设备备件作为物料管理（ItemDO）
- 维修成本统计
