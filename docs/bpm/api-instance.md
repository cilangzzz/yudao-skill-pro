# API - 流程实例管理 (BpmProcessInstanceController)

> 路径前缀：`/bpm/process-instance`
> 对应服务：`BpmProcessInstanceService`

## 概述

流程实例是流程定义的一次执行。用户发起流程时创建流程实例，经过各审批节点后完成或终止。

运行时数据由 Flowable 引擎管理（`ACT_RU_EXECUTION`, `ACT_HI_PROCINST` 等表），扩展信息（如抄送记录）存储在自建表中。

---

## 接口列表

### 1. 发起流程实例

- **接口：** `POST /bpm/process-instance/create`
- **权限：** `bpm:process-instance:create`
- **说明：** 发起一个新的流程实例

**请求参数（BpmProcessInstanceCreateReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| processDefinitionKey | String | 是 | 流程定义 Key |
| businessKey | String | 否 | 业务主键（关联业务数据） |
| variables | Map\<String, Object\> | 否 | 流程变量（表单数据等） |

**返回：** `CommonResult<String>` -- 流程实例编号

**模块间调用方式（推荐）：**

```java
@Resource
private BpmProcessInstanceApi processInstanceApi;

BpmProcessInstanceCreateReqDTO reqDTO = new BpmProcessInstanceCreateReqDTO();
reqDTO.setProcessDefinitionKey("oa_leave");
reqDTO.setBusinessKey(leave.getId().toString());
reqDTO.setVariables(BeanUtil.beanToMap(createReqVO));
String processInstanceId = processInstanceApi.createProcessInstance(userId, reqDTO);
```

---

### 2. 取消流程实例

- **接口：** `PUT /bpm/process-instance/cancel`
- **权限：** `bpm:process-instance:cancel`
- **说明：** 取消（终止）正在运行的流程实例

**请求参数（BpmProcessInstanceCancelReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 流程实例编号 |
| reason | String | 否 | 取消原因 |

---

### 3. 获取流程实例详情

- **接口：** `GET /bpm/process-instance/get`
- **权限：** `bpm:process-instance:query`
- **说明：** 获取流程实例详情，包括当前节点、审批记录、表单数据等

**返回（BpmProcessInstanceRespVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 流程实例编号 |
| name | String | 流程实例名称 |
| processDefinitionId | String | 流程定义编号 |
| processDefinitionKey | String | 流程定义标识 |
| processDefinitionName | String | 流程定义名称 |
| category | String | 流程分类 |
| startTime | LocalDateTime | 发起时间 |
| endTime | LocalDateTime | 结束时间 |
| status | Integer | 流程状态 |
| tasks | List | 审批任务列表 |
| formVariables | Map | 表单变量 |

---

### 4. 分页查询我的发起

- **接口：** `GET /bpm/process-instance/my-page`
- **权限：** 无（当前用户）
- **说明：** 查询当前用户发起的流程实例

---

### 5. 分页查询流程实例（管理端）

- **接口：** `GET /bpm/process-instance/page`
- **权限：** `bpm:process-instance:query`
- **说明：** 管理端分页查询所有流程实例

**请求参数（BpmProcessInstancePageReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 流程实例名称（模糊匹配） |
| processDefinitionKey | String | 否 | 流程定义 Key |
| status | Integer | 否 | 流程状态 |
| category | String | 否 | 流程分类 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

---

### 6. 获取流程实例的审批节点列表

- **接口：** `GET /bpm/process-instance/get-tasks`
- **权限：** `bpm:process-instance:query`
- **说明：** 获取流程实例所有审批节点（包括已完成和进行中的），用于流程进度展示

---

### 7. 流程抄送

- **接口：** `POST /bpm/process-instance/copy`
- **权限：** `bpm:process-instance:copy`
- **说明：** 将流程实例抄送给指定用户

---

### 8. 查询我的抄送

- **接口：** `GET /bpm/process-instance/copy-page`
- **权限：** 无（当前用户）
- **说明：** 查询抄送给当前用户的流程实例

---

## 流程状态枚举 (BpmProcessInstanceStatusEnum)

| 状态 | 值 | 说明 |
|------|---|------|
| 进行中 | 1 | 流程正在运行 |
| 已通过 | 2 | 流程审批通过 |
| 已拒绝 | 3 | 流程审批拒绝 |
| 已取消 | 4 | 流程被发起人取消 |
| 已撤回 | 5 | 流程被发起人撤回 |

---

## 设计要点

1. **businessKey 关联：** 通过 `businessKey` 将流程实例与业务数据关联，实现流程与业务分离
2. **流程变量：** `variables` 用于传递表单数据，流程中各节点可通过变量获取表单值
3. **状态事件：** 流程状态变更时，发布 `BpmProcessInstanceStatusEvent` 事件，业务模块监听该事件更新业务状态
4. **发起权限：** 通过 `bpm_process_definition_info.start_user_ids` 控制可发起用户
5. **撤回规则：** 只有当前节点未被处理时，发起人才可以撤回流程
