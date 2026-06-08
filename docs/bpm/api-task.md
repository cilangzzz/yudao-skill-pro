# API - 流程任务管理 (BpmTaskController)

> 路径前缀：`/bpm/task`
> 对应服务：`BpmTaskService`

## 概述

流程任务是流程实例中的审批节点。当流程运行到某个用户任务节点时，会创建任务并分配给指定审批人。

任务管理是 BPM 模块最核心的功能，包含待办/已办查询、审批通过/拒绝、退回、委派、转办、加签/减签等操作。

---

## 接口列表

### 1. 查询待办任务

- **接口：** `GET /bpm/task/todo-page`
- **权限：** 无（当前用户）
- **说明：** 查询当前用户的待办任务列表

**请求参数（BpmTaskTodoPageReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| processDefinitionKey | String | 否 | 流程定义 Key |
| name | String | 否 | 任务名称（模糊匹配） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

---

### 2. 查询已办任务

- **接口：** `GET /bpm/task/done-page`
- **权限：** 无（当前用户）
- **说明：** 查询当前用户的已办任务列表

---

### 3. 审批通过

- **接口：** `PUT /bpm/task/approve`
- **权限：** `bpm:task:update`

**请求参数（BpmTaskApproveReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 任务编号 |
| comment | String | 否 | 审批意见 |
| variables | Map\<String, Object\> | 否 | 流程变量（条件分支等） |

**代码示例：**

```java
@PutMapping("/approve")
@Operation(summary = "通过任务")
@PreAuthorize("@ss.hasPermission('bpm:task:update')")
public CommonResult<Boolean> approveTask(@Valid @RequestBody BpmTaskApproveReqVO reqVO) {
    taskService.approveTask(getLoginUserId(), reqVO);
    return success(true);
}
```

---

### 4. 审批拒绝

- **接口：** `PUT /bpm/task/reject`
- **权限：** `bpm:task:update`

**请求参数（BpmTaskRejectReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 任务编号 |
| comment | String | 否 | 拒绝原因 |

---

### 5. 任务退回

- **接口：** `PUT /bpm/task/return`
- **权限：** `bpm:task:update`
- **说明：** 将任务退回到指定的某个历史节点

**请求参数（BpmTaskReturnReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 任务编号 |
| targetTaskId | String | 是 | 目标任务编号（退回的节点） |
| comment | String | 否 | 退回原因 |

---

### 6. 任务委派

- **接口：** `PUT /bpm/task/delegate`
- **权限：** `bpm:task:update`
- **说明：** 将任务委派给其他人处理，处理完后自动回到原审批人

**请求参数（BpmTaskDelegateReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 任务编号 |
| userId | Long | 是 | 被委派人用户编号 |
| comment | String | 否 | 委派原因 |

---

### 7. 任务转办

- **接口：** `PUT /bpm/task/transfer`
- **权限：** `bpm:task:update`
- **说明：** 将任务转给其他人处理，原审批人不再参与

---

### 8. 加签

- **接口：** `PUT /bpm/task/add-sign`
- **权限：** `bpm:task:update`
- **说明：** 在当前节点前/后增加审批人

---

### 9. 减签

- **接口：** `PUT /bpm/task/delete-sign`
- **权限：** `bpm:task:update`
- **说明：** 移除当前节点的某个审批人

---

### 10. 获取任务详情

- **接口：** `GET /bpm/task/get`
- **权限：** `bpm:task:query`

---

## 审批人策略 (BpmTaskCandidateStrategy)

审批人策略决定了任务分配给谁。通过 `BpmTaskCandidateStrategyEnum` 枚举标识：

| 策略 | 说明 |
|------|------|
| ROLE | 按角色分配，指定角色下的所有用户 |
| DEPT_MEMBER | 按部门成员分配 |
| DEPT_LEADER | 按部门负责人分配 |
| POST | 按岗位分配 |
| USER | 指定具体用户 |
| USER_GROUP | 按用户组分配 |
| EXPRESSION | 按流程表达式分配 |
| START_USER | 发起人自己 |
| START_USER_DEPT_LEADER | 发起人的部门负责人 |

**自定义策略实现：**

```java
@Component
public class BpmTaskCandidateCustomStrategy implements BpmTaskCandidateStrategy {

    @Override
    public BpmTaskCandidateStrategyEnum getStrategy() {
        return BpmTaskCandidateStrategyEnum.CUSTOM;
    }

    @Override
    public void validateParam(String param) {
        // 校验参数
    }

    @Override
    public Set<Long> calculateUsersByTask(DelegateExecution execution, String param) {
        // 计算审批人
        return calculateUsers(param);
    }
}
```

---

## 设计要点

1. **审批人校验：** 操作任务前校验当前用户是否为任务审批人，否则抛出 `1_009_005_001` 错误
2. **委派 vs 转办：** 委派后任务还会回到原审批人；转办后原审批人不再参与
3. **退回：** 退回到历史节点后，流程会重新执行该节点
4. **加签/减签：** 适用于多人会签场景，动态调整审批人列表
5. **流程变量传递：** 审批时可通过 `variables` 传递变量，用于后续条件分支判断
