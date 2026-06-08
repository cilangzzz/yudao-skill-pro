# 排班日历 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 日历管理（Calendar）

**Controller**: `MesCalController`
**路径前缀**: `/admin-api/mes/cal`
**权限前缀**: `mes:cal:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/list` | 获取日历列表 | `mes:cal:query` |
| GET | `/get-month` | 获取某月日历（含排班信息） | `mes:cal:query` |

> 日历管理提供工厂日历视图，展示每天的工作/休息状态及排班信息。

---

## 2. 节假日管理（Holiday）

**Controller**: `MesCalHolidayController`
**路径前缀**: `/admin-api/mes/cal/holiday`
**权限前缀**: `mes:cal:holiday:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建节假日 | `mes:cal:holiday:create` |
| PUT | `/update` | 更新节假日 | `mes:cal:holiday:update` |
| DELETE | `/delete` | 删除节假日 | `mes:cal:holiday:delete` |
| GET | `/get` | 获取节假日详情 | `mes:cal:holiday:query` |
| GET | `/list` | 获取节假日列表 | `mes:cal:holiday:query` |

### 请求 VO

**MesCalHolidaySaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 节假日名称 |
| date | LocalDate | 是 | 日期 |
| type | Integer | 是 | 类型：0 法定假日 1 调休工作日 |
| remark | String | 否 | 备注 |

---

## 3. 排班计划（Plan）

**Controller**: `MesCalPlanController`
**路径前缀**: `/admin-api/mes/cal/plan`
**权限前缀**: `mes:cal:plan:*`

### 3.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建排班计划 | `mes:cal:plan:create` |
| PUT | `/update` | 更新排班计划 | `mes:cal:plan:update` |
| DELETE | `/delete` | 删除排班计划 | `mes:cal:plan:delete` |
| GET | `/get` | 获取计划详情（含班次/班组） | `mes:cal:plan:query` |
| GET | `/page` | 计划分页查询 | `mes:cal:plan:query` |
| POST | `/submit` | 提交排班计划 | `mes:cal:plan:update` |
| POST | `/approve` | 审批排班计划 | `mes:cal:plan:update` |

### 3.2 排班计划结构

| 子表 | 说明 |
|------|------|
| `mes_cal_plan_shift` | 计划关联的班次列表 |
| `mes_cal_plan_team` | 计划关联的班组列表 |

### 3.3 排班计划状态

| 值 | 说明 |
|----|------|
| 0 | 草稿 |
| 1 | 待审批 |
| 2 | 已生效 |
| 3 | 已驳回 |

---

## 4. 班组管理（Team）

**Controller**: `MesCalTeamController`
**路径前缀**: `/admin-api/mes/cal/team`
**权限前缀**: `mes:cal:team:*`

### 4.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建班组 | `mes:cal:team:create` |
| PUT | `/update` | 更新班组 | `mes:cal:team:update` |
| DELETE | `/delete` | 删除班组 | `mes:cal:team:delete` |
| GET | `/get` | 获取班组详情（含成员/班次） | `mes:cal:team:query` |
| GET | `/page` | 班组分页查询 | `mes:cal:team:query` |
| GET | `/list-all` | 获取所有班组 | `mes:cal:team:query` |

### 4.2 班组关联关系

| 子表 | 说明 |
|------|------|
| `mes_cal_team_member` | 班组成员列表（关联操作工人） |
| `mes_cal_team_shift` | 班组班次列表 |

### 4.3 班次定义

`mes_cal_team_shift` 定义班次的时间安排：

| 字段 | 说明 |
|------|------|
| name | 班次名称（早班/中班/晚班） |
| start_time | 开始时间 |
| end_time | 结束时间 |
| is_next_day | 是否跨天 |

---

## 5. 排班计划-班次关联（PlanShift）

**Controller**: `MesCalPlanShiftController`
**路径前缀**: `/admin-api/mes/cal/plan-shift`
**权限前缀**: `mes:cal:plan-shift:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建班次 | `mes:cal:plan-shift:create` |
| PUT | `/update` | 更新班次 | `mes:cal:plan-shift:update` |
| DELETE | `/delete` | 删除班次 | `mes:cal:plan-shift:delete` |
| GET | `/get` | 获取班次详情 | `mes:cal:plan-shift:query` |
| GET | `/list` | 获取班次列表 | `mes:cal:plan-shift:query` |

---

## 6. 排班计划-班组关联（PlanTeam）

**Controller**: `MesCalPlanTeamController`
**路径前缀**: `/admin-api/mes/cal/plan-team`
**权限前缀**: `mes:cal:plan-team:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建计划班组 | `mes:cal:plan-team:create` |
| PUT | `/update` | 更新计划班组 | `mes:cal:plan-team:update` |
| DELETE | `/delete` | 删除计划班组 | `mes:cal:plan-team:delete` |
| GET | `/get` | 获取计划班组详情 | `mes:cal:plan-team:query` |
| GET | `/list` | 获取计划班组列表 | `mes:cal:plan-team:query` |

---

## 7. 班组成员管理（TeamMember）

**Controller**: `MesCalTeamMemberController`
**路径前缀**: `/admin-api/mes/cal/team-member`
**权限前缀**: `mes:cal:team-member:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 添加班组成员 | `mes:cal:team-member:create` |
| DELETE | `/delete` | 移除班组成员 | `mes:cal:team-member:delete` |
| GET | `/list` | 获取班组成员列表 | `mes:cal:team-member:query` |

---

## 核心设计要点

### 排班层级关系

```
排班计划 (CalPlan)
  ├── 班次 (CalPlanShift) - 定义时间安排
  └── 班组 (CalPlanTeam) - 定义人员安排
        ├── 班组成员 (CalTeamMember) - 关联操作工人
        └── 班组班次 (CalTeamShift) - 班组的默认班次
```

### 与生产联动

排班计划与生产管理关联：
- 生产任务分配时参考排班信息
- 报工记录关联实际出勤班组
- 工位操作员从班组成员中选择

### 日历视图

日历接口提供月度视图：
- 每天显示工作/休息状态
- 工作日显示排班的班组和班次
- 节假日特殊标记
- 调休工作日标记
