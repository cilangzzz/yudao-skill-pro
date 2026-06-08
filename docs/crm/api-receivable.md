# 回款管理 API

## 概述

回款管理跟踪合同的实际回款情况，支持回款计划和实际回款两个维度。回款计划定义预期的回款安排，实际回款记录真实的资金到账。回款同样需要通过 BPM 审批流程。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmReceivableController | `/crm/receivable` | 回款管理接口 |
| CrmReceivablePlanController | `/crm/receivable-plan` | 回款计划接口 |

## 接口列表

### 回款管理

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建回款 | POST | `/crm/receivable/create` | `crm:receivable:create` | 录入实际回款 |
| 更新回款 | PUT | `/crm/receivable/update` | `crm:receivable:update` | 需要 WRITE 权限 |
| 删除回款 | DELETE | `/crm/receivable/delete` | `crm:receivable:delete` | 需要 OWNER 权限 |
| 获取回款详情 | GET | `/crm/receivable/get` | `crm:receivable:query` | 需要 READ 权限 |
| 回款分页查询 | GET | `/crm/receivable/page` | `crm:receivable:query` | 按客户、合同等条件过滤 |

### 回款计划

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建回款计划 | POST | `/crm/receivable-plan/create` | `crm:receivable:plan:create` | 创建回款计划 |
| 更新回款计划 | PUT | `/crm/receivable-plan/update` | `crm:receivable:plan:update` | 编辑回款计划 |
| 删除回款计划 | DELETE | `/crm/receivable-plan/delete` | `crm:receivable:plan:delete` | 删除回款计划 |
| 获取回款计划详情 | GET | `/crm/receivable-plan/get` | `crm:receivable:plan:query` | 查询详情 |
| 回款计划分页查询 | GET | `/crm/receivable-plan/page` | `crm:receivable:plan:query` | 按合同、客户等条件过滤 |

## 核心数据模型

### CrmReceivableDO（回款表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| no | VARCHAR | 回款编号 |
| plan_id | BIGINT | 回款计划ID |
| customer_id | BIGINT | 客户ID |
| contract_id | BIGINT | 合同ID |
| owner_user_id | BIGINT | 负责人用户编号 |
| return_time | DATETIME | 回款日期 |
| return_type | INT | 回款方式 |
| price | DECIMAL | 回款金额 |
| remark | VARCHAR | 备注 |
| process_instance_id | VARCHAR | 工作流实例ID |
| audit_status | INT | 审批状态 |

### CrmReceivablePlanDO（回款计划表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| period | INT | 期数 |
| customer_id | BIGINT | 客户ID |
| contract_id | BIGINT | 合同ID |
| owner_user_id | BIGINT | 负责人用户编号 |
| return_time | DATETIME | 计划回款日期 |
| return_type | INT | 计划回款类型 |
| price | DECIMAL | 计划回款金额 |
| receivable_id | BIGINT | 实际回款ID |
| remind_days | INT | 提前提醒天数 |
| remind_time | DATETIME | 提醒日期 |
| remark | VARCHAR | 备注 |

## 业务规则

1. **回款计划与实际回款**：回款计划（plan）定义预期安排，实际回款（receivable）记录真实到账，通过 plan_id 和 receivable_id 双向关联
2. **审批流程**：实际回款通过 BPM 审批，CrmReceivableStatusListener 监听审批结果
3. **关联合同**：回款必须关联合同（contract_id），一个合同可有多笔回款
4. **提醒机制**：回款计划支持设置提前提醒天数（remind_days），到期自动提醒
5. **期数管理**：回款计划支持按期数（period）管理分期回款

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/receivable/CrmReceivableService.java` | 回款服务接口 |
| `service/receivable/CrmReceivablePlanService.java` | 回款计划服务接口 |
| `controller/admin/receivable/CrmReceivableController.java` | 回款控制器 |
| `controller/admin/receivable/CrmReceivablePlanController.java` | 回款计划控制器 |
| `dal/dataobject/receivable/CrmReceivableDO.java` | 回款实体类 |
| `dal/dataobject/receivable/CrmReceivablePlanDO.java` | 回款计划实体类 |
| `CrmReceivableStatusListener` | 审批状态监听器 |
