# 生产管理 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 工单管理（WorkOrder）

**Controller**: `MesWorkOrderController`
**路径前缀**: `/admin-api/mes/work-order`
**权限前缀**: `mes:work-order:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建工单 | `mes:work-order:create` |
| PUT | `/update` | 更新工单 | `mes:work-order:update` |
| DELETE | `/delete` | 删除工单 | `mes:work-order:delete` |
| GET | `/get` | 获取工单详情（含 BOM 子表） | `mes:work-order:query` |
| GET | `/page` | 工单分页查询 | `mes:work-order:query` |
| PUT | `/update-status` | 更新工单状态（确认/完工/取消） | `mes:work-order:update` |

### 1.2 请求/响应 VO

**MesWorkOrderSaveReqVO**（创建/更新请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 是 | 工单编号 |
| itemId | Long | 是 | 产品物料编号 |
| bomId | Long | 否 | BOM 编号 |
| routeId | Long | 否 | 工艺路线编号 |
| quantity | BigDecimal | 是 | 计划数量 |
| startDate | LocalDate | 否 | 计划开始日期 |
| endDate | LocalDate | 否 | 计划结束日期 |
| priority | Integer | 否 | 优先级 |
| sourceCode | String | 否 | 来源单号（ERP 下推） |
| remark | String | 否 | 备注 |

**MesWorkOrderPageReqVO**（分页查询请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| no | String | 否 | 工单编号（模糊查询） |
| itemId | Long | 否 | 产品物料编号 |
| status | Integer | 否 | 工单状态 |
| startDate | LocalDate[] | 否 | 计划开始日期范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

### 1.3 状态枚举

**MesWorkOrderStatusEnum**:

| 值 | 说明 | 可流转到 |
|----|------|---------|
| 0 | 草稿 | 确认(1), 取消(3) |
| 1 | 已确认 | 完工(2), 取消(3) |
| 2 | 已完工 | - |
| 3 | 已取消 | - |

### 1.4 工单 BOM 子表

工单创建时可关联 BOM 子表 `mes_pro_work_order_bom`，记录生产所需的物料明细。

### 1.5 创建流程

```
1. 校验物料是否存在 (ItemService)
2. 校验 BOM 是否存在（如指定） (ProductBomService)
3. 校验工艺路线是否存在（如指定） (RouteService)
4. 生成工单编号（如未指定，使用自动编码规则）
5. 设置初始状态为"草稿"
6. 插入工单记录
7. 插入工单 BOM 子表记录（如有）
```

---

## 2. 生产任务（Task）

**Controller**: `MesTaskController`
**路径前缀**: `/admin-api/mes/task`
**权限前缀**: `mes:task:*`

### 2.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建任务 | `mes:task:create` |
| PUT | `/update` | 更新任务 | `mes:task:update` |
| DELETE | `/delete` | 删除任务 | `mes:task:delete` |
| GET | `/get` | 获取任务详情 | `mes:task:query` |
| GET | `/page` | 任务分页查询 | `mes:task:query` |
| GET | `/gantt-list` | 甘特图数据查询 | `mes:task:query` |
| PUT | `/update-gantt` | 更新甘特图（拖拽调整） | `mes:task:update` |

### 2.2 甘特图支持

任务接口支持甘特图展示：
- `gantt-list` 返回任务列表，包含计划开始/结束时间、实际开始/结束时间
- `update-gantt` 支持前端拖拽调整任务时间
- 任务可按工单、工位、设备等维度分组展示

### 2.3 任务下发

任务与工序关联，每个工序对应一个或多个任务：
- `mes_pro_task_issue` 记录任务的领料信息
- 任务关联工单、工序、工位、设备、操作员

---

## 3. 工艺路线（Route）

**Controller**: `MesRouteController`
**路径前缀**: `/admin-api/mes/route`
**权限前缀**: `mes:route:*`

### 3.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建工艺路线 | `mes:route:create` |
| PUT | `/update` | 更新工艺路线 | `mes:route:update` |
| DELETE | `/delete` | 删除工艺路线 | `mes:route:delete` |
| GET | `/get` | 获取工艺路线详情（含工序/产品/BOM） | `mes:route:query` |
| GET | `/page` | 工艺路线分页查询 | `mes:route:query` |

### 3.2 工艺路线结构

工艺路线定义产品的生产步骤：

| 子表 | 说明 |
|------|------|
| `mes_pro_route_process` | 工序列表（工序序号、名称、工位、标准工时） |
| `mes_pro_route_product` | 适用产品列表 |
| `mes_pro_route_product_bom` | 产品 BOM 关联 |

---

## 4. 工序管理（Process）

**Controller**: `MesProcessController`
**路径前缀**: `/admin-api/mes/process`
**权限前缀**: `mes:process:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建工序 | `mes:process:create` |
| PUT | `/update` | 更新工序 | `mes:process:update` |
| DELETE | `/delete` | 删除工序 | `mes:process:delete` |
| GET | `/get` | 获取工序详情（含工序内容） | `mes:process:query` |
| GET | `/page` | 工序分页查询 | `mes:process:query` |
| GET | `/list-all` | 获取所有工序 | `mes:process:query` |

### 工序内容

`mes_pro_process_content` 记录工序的详细操作内容（检验项目、操作说明等）。

---

## 5. 流转卡（Card）

**Controller**: `MesCardController`
**路径前缀**: `/admin-api/mes/card`
**权限前缀**: `mes:card:*`

### 5.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建流转卡 | `mes:card:create` |
| PUT | `/update` | 更新流转卡 | `mes:card:update` |
| DELETE | `/delete` | 删除流转卡 | `mes:card:delete` |
| GET | `/get` | 获取流转卡详情 | `mes:card:query` |
| GET | `/page` | 流转卡分页查询 | `mes:card:query` |
| POST | `/submit` | 提交流转卡（开始生产） | `mes:card:update` |
| POST | `/finish` | 完成流转卡 | `mes:card:update` |
| POST | `/cancel` | 取消流转卡 | `mes:card:update` |

### 5.2 状态枚举

**MesCardStatusEnum**:

| 值 | 说明 | 可流转到 |
|----|------|---------|
| 0 | 草稿 | 提交(1), 取消(3) |
| 1 | 进行中 | 完成(2), 取消(3) |
| 2 | 已完成 | - |
| 3 | 已取消 | - |

### 5.3 流转卡工序

`mes_card_process` 记录流转卡在各工序的执行情况，包括实际用时、数量、状态等。

---

## 6. 报工反馈（Feedback）

**Controller**: `MesFeedbackController`
**路径前缀**: `/admin-api/mes/feedback`
**权限前缀**: `mes:feedback:*`

### 6.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建报工 | `mes:feedback:create` |
| PUT | `/update` | 更新报工 | `mes:feedback:update` |
| DELETE | `/delete` | 删除报工 | `mes:feedback:delete` |
| GET | `/get` | 获取报工详情 | `mes:feedback:query` |
| GET | `/page` | 报工分页查询 | `mes:feedback:query` |
| POST | `/submit` | 提交报工（进入审批） | `mes:feedback:update` |
| POST | `/reject` | 驳回报工 | `mes:feedback:update` |
| POST | `/approve` | 审批通过 | `mes:feedback:update` |

### 6.2 状态枚举

**MesFeedbackStatusEnum**:

| 值 | 说明 | 可流转到 |
|----|------|---------|
| 0 | 草稿 | 提交(1) |
| 1 | 待审批 | 审批通过(2), 驳回(3) |
| 2 | 已通过 | - |
| 3 | 已驳回 | 提交(1)（重新提交） |

---

## 7. 报工记录（WorkRecord）

**Controller**: `MesWorkRecordController`
**路径前缀**: `/admin-api/mes/work-record`
**权限前缀**: `mes:work-record:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 报工记录分页查询 | `mes:work-record:query` |
| GET | `/get` | 获取记录详情 | `mes:work-record:query` |

### 报工日志

`mes_pro_work_record_log` 记录报工的操作日志（状态变更、审批记录等）。

---

## 8. 安灯管理（Andon）

**Controller**: `MesAndonController`
**路径前缀**: `/admin-api/mes/andon`
**权限前缀**: `mes:andon:*`

### 8.1 安灯配置

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/config/create` | 创建安灯配置 | `mes:andon:create` |
| PUT | `/config/update` | 更新安灯配置 | `mes:andon:update` |
| DELETE | `/config/delete` | 删除安灯配置 | `mes:andon:delete` |
| GET | `/config/get` | 获取配置详情 | `mes:andon:query` |
| GET | `/config/page` | 配置分页查询 | `mes:andon:query` |

### 8.2 安灯记录

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/record/create` | 发起安灯呼叫 | `mes:andon:create` |
| GET | `/record/page` | 安灯记录分页查询 | `mes:andon:query` |
| PUT | `/record/update` | 处理安灯记录 | `mes:andon:update` |

> 安灯（Andon）系统用于车间异常呼叫，操作员发现问题时发起呼叫，相关人员接收并处理。

---

## 核心设计要点

### VO Assembly 模式

生产管理的查询接口普遍使用 VO Assembly 模式：

```java
// 1. 查询主表数据
PageResult<WorkOrderDO> pageResult = workOrderMapper.selectPage(reqVO);

// 2. 批量获取关联数据
List<ItemDO> items = itemService.getItems(itemIds);

// 3. 组装 VO（MapStruct + 手动补充）
return buildVOList(pageResult, items);
```

### 状态机管理

工单、流转卡、报工、维修等实体都使用状态机模式：
- 状态变更前校验前置状态是否合法
- 使用 CAS 方式更新状态，防止并发覆盖
- 状态变更记录操作日志

### 自动编码

工单编号等业务单号支持自动生成，基于 `MesAutoCodeRuleDO` 定义的规则：
- 日期部分 + 固定字符 + 序列号
- 序列号按日期重置或连续递增
