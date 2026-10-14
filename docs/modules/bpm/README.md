# 工作流模块 (bpm)

> 基于 Flowable 6 引擎的工作流管理模块，覆盖流程模型设计、流程定义、动态表单、流程实例发起与审批、任务操作（退回/委派/加签/抄送）等完整 BPM 能力。

## 模块概述

- **模块路径**: yudao-module-bpm
- **业务定位**: 提供企业级 BPM（Business Process Management）工作流能力：管理员通过流程模型（BPMN / 仿钉钉 SIMPLE 两种设计器）维护流程，用户发起流程实例并进行审批。审批人分配、消息通知、超时处理、HTTP 回调等通过监听器与触发器机制扩展；同时以 Api 接口形式向 CRM（合同/回款审批）、OA（各类申请单）、HRM（考勤请假）等模块提供流程发起与状态回调能力。
- **技术栈**: Spring Boot 2.7.18 / MyBatis-Plus / Flowable 6（flowable-spring-boot-starter-process + flowable-spring-boot-starter-actuator）/ Swagger v3（springdoc）/ Jackson TypeHandler（JSON 字段存储）

## 设计原则

| 原则 | 说明 |
|-----|------|
| 引擎本地集成 | 通过 flowable-spring-boot-starter-process 内嵌 Flowable 6 引擎，流程数据存于 Flowable 自带的 ACT_* 表，业务扩展数据存于 bpm_* 表，互不侵入 |
| 扩展表模式 | Flowable 的 Model / ProcessDefinition 不支持扩展字段，通过 `bpm_process_definition_info` 扩展表补充表单配置、审批人规则、图标、可见性等业务属性 |
| 审批人策略化 | 候选人计算抽象为 `BpmTaskCandidateStrategy` 策略族（15 个实现），通过自定义 `BpmActivityBehaviorFactory` 替换 Flowable 默认的用户任务分配行为 |
| 双设计器并存 | 同时支持 BPMN 设计器与仿钉钉/飞书的 SIMPLE 精简设计器，`SimpleModelUtils` 负责钉钉风格节点 JSON 与 BPMN XML 的互转 |
| 事件驱动解耦 | 流程实例状态变更后通过 Spring 事件发布 `BpmProcessInstanceStatusEvent`，下游模块以监听器方式回调业务状态，避免与业务模块双向耦合 |
| 统一审计基类 | 全部业务表继承 BaseDO（creator/createTime/updater/updateTime/deleted），JSON 数组字段使用 JacksonTypeHandler / LongListTypeHandler 存储 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 流程模型 | 模型 CRUD、BPMN XML 维护、JSON 导入导出、部署/挂起、SIMPLE 精简设计模型、批量排序 | BpmProcessDefinitionInfoDO |
| 流程分类 | 流程分类 CRUD 与批量排序，部署模型时归属分类 | BpmCategoryDO |
| 动态表单 | 表单设计器 JSON 配置的增删改查，供流程模型绑定 | BpmFormDO |
| 用户组 | 审批人用户组管理，用于"用户组"类型的候选人策略 | BpmUserGroupDO |
| 流程表达式 | 可复用的 UEL 表达式库，供条件分支/监听器引用 | BpmProcessExpressionDO |
| 流程监听器 | 任务/执行监听器配置（类、表达式、委托 Bean 三种形式） | BpmProcessListenerDO |
| 流程定义 | 流程定义分页查询、挂起状态过滤、发起权限过滤 | BpmProcessDefinitionInfoDO |
| 流程实例 | 发起、取消（发起人/管理员）、审批详情、下一节点预测、BPMN 视图、打印数据 | BpmProcessDefinitionInfoDO |
| 流程任务 | 待办/已办/全部任务分页，审批通过/不通过、退回、委派、转派、加减签、抄送、撤回 | BpmTaskStatusEnum |
| 实例抄送 | 任务抄送记录查询（抄送人视角分页） | BpmProcessInstanceCopyDO |
| 流程评论 | 按流程实例维度发布与查看评论（基于 Flowable Comment 机制） | — |
| OA 请假示例 | 自建业务表接入工作流的完整演示（创建申请 → 发起实例 → 状态回写） | BpmOALeaveDO |

## API 接口索引

### 流程模型 (BpmModelController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/model/list | GET | 获得模型列表 | 已认证 |
| /bpm/model/get | GET | 获得模型（含 BPMN XML 与 SIMPLE 模型） | bpm:model:query |
| /bpm/model/export | GET | 导出模型 | bpm:model:export |
| /bpm/model/create | POST | 新建模型 | bpm:model:create |
| /bpm/model/import | POST | 导入模型（JSON 文件） | bpm:model:import |
| /bpm/model/update | PUT | 修改模型 | bpm:model:update |
| /bpm/model/update-sort-batch | PUT | 批量修改模型排序 | 已认证 |
| /bpm/model/deploy | POST | 部署模型 | bpm:model:deploy |
| /bpm/model/update-state | PUT | 修改模型的状态（挂起/激活流程定义） | bpm:model:update |
| /bpm/model/update-bpmn | PUT | 修改模型的 BPMN（已废弃） | bpm:model:update |
| /bpm/model/delete | DELETE | 删除模型 | bpm:model:delete |
| /bpm/model/clean | DELETE | 清理模型 | bpm:model:clean |
| /bpm/model/simple/get | GET | 获得仿钉钉流程设计模型 | 已认证 |
| /bpm/model/simple/update | POST | 保存仿钉钉流程设计模型（已废弃） | bpm:model:update |

### 流程定义 (BpmProcessDefinitionController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/process-definition/page | GET | 获得流程定义分页 | bpm:process-definition:query |
| /bpm/process-definition/list | GET | 获得流程定义列表（按挂起状态过滤并发起权限） | 已认证 |
| /bpm/process-definition/simple-list | GET | 获得流程定义精简列表（下拉选项） | 已认证 |
| /bpm/process-definition/get | GET | 获得流程定义（按 id 或 key） | 已认证 |

### 流程分类 (BpmCategoryController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/category/create | POST | 创建流程分类 | bpm:category:create |
| /bpm/category/update | PUT | 更新流程分类 | bpm:category:update |
| /bpm/category/update-sort-batch | PUT | 批量更新流程分类的排序 | bpm:category:update |
| /bpm/category/delete | DELETE | 删除流程分类 | bpm:category:delete |
| /bpm/category/get | GET | 获得流程分类 | bpm:category:query |
| /bpm/category/page | GET | 获得流程分类分页 | bpm:category:query |
| /bpm/category/simple-list | GET | 获取流程分类的精简信息列表 | 已认证 |

### 动态表单 (BpmFormController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/form/create | POST | 创建动态表单 | bpm:form:create |
| /bpm/form/update | PUT | 更新动态表单 | bpm:form:update |
| /bpm/form/delete | DELETE | 删除动态表单 | bpm:form:delete |
| /bpm/form/get | GET | 获得动态表单 | bpm:form:query |
| /bpm/form/list-all-simple 或 /bpm/form/simple-list | GET | 获得动态表单的精简列表 | 已认证 |
| /bpm/form/page | GET | 获得动态表单分页 | bpm:form:query |

### 用户组 (BpmUserGroupController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/user-group/create | POST | 创建用户组 | bpm:user-group:create |
| /bpm/user-group/update | PUT | 更新用户组 | bpm:user-group:update |
| /bpm/user-group/delete | DELETE | 删除用户组 | bpm:user-group:delete |
| /bpm/user-group/get | GET | 获得用户组 | bpm:user-group:query |
| /bpm/user-group/page | GET | 获得用户组分页 | bpm:user-group:query |
| /bpm/user-group/simple-list | GET | 获取用户组精简信息列表 | 已认证 |

### 流程表达式 (BpmProcessExpressionController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/process-expression/create | POST | 创建流程表达式 | bpm:process-expression:create |
| /bpm/process-expression/update | PUT | 更新流程表达式 | bpm:process-expression:update |
| /bpm/process-expression/delete | DELETE | 删除流程表达式 | bpm:process-expression:delete |
| /bpm/process-expression/get | GET | 获得流程表达式 | bpm:process-expression:query |
| /bpm/process-expression/page | GET | 获得流程表达式分页 | bpm:process-expression:query |

### 流程监听器 (BpmProcessListenerController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/process-listener/create | POST | 创建流程监听器 | bpm:process-listener:create |
| /bpm/process-listener/update | PUT | 更新流程监听器 | bpm:process-listener:update |
| /bpm/process-listener/delete | DELETE | 删除流程监听器 | bpm:process-listener:delete |
| /bpm/process-listener/get | GET | 获得流程监听器 | bpm:process-listener:query |
| /bpm/process-listener/page | GET | 获得流程监听器分页 | bpm:process-listener:query |

### 流程实例 (BpmProcessInstanceController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/process-instance/my-page | GET | 获得我的实例分页列表（我的流程） | bpm:process-instance:query |
| /bpm/process-instance/manager-page | GET | 获得管理流程实例的分页列表（流程实例管理） | bpm:process-instance:manager-query |
| /bpm/process-instance/create | POST | 新建流程实例 | bpm:process-instance:query |
| /bpm/process-instance/get | GET | 获得指定流程实例 | bpm:process-instance:query |
| /bpm/process-instance/cancel-by-start-user | DELETE | 用户取消流程实例 | bpm:process-instance:cancel |
| /bpm/process-instance/cancel-by-admin | DELETE | 管理员取消流程实例 | bpm:process-instance:cancel-by-admin |
| /bpm/process-instance/get-approval-detail | GET | 获得审批详情 | bpm:process-instance:query |
| /bpm/process-instance/get-next-approval-nodes | GET | 获取下一个执行的流程节点 | bpm:process-instance:query |
| /bpm/process-instance/get-bpmn-model-view | GET | 获取流程实例的 BPMN 模型视图 | bpm:process-instance:query |
| /bpm/process-instance/get-print-data | GET | 获得流程实例的打印数据 | bpm:process-instance:query |

### 流程实例抄送 (BpmProcessInstanceCopyController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/process-instance/copy/page | GET | 获得抄送流程分页列表 | bpm:process-instance-cc:query |

### 流程任务 (BpmTaskController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/task/todo-page | GET | 获取 Todo 待办任务分页 | bpm:task:query |
| /bpm/task/done-page | GET | 获取 Done 已办任务分页 | bpm:task:query |
| /bpm/task/manager-page | GET | 获取全部任务的分页（流程任务管理） | bpm:task:manager-query |
| /bpm/task/list-by-process-instance-id | GET | 获得指定流程实例的任务列表（含完成/未完成） | bpm:task:query |
| /bpm/task/approve | PUT | 通过任务 | bpm:task:update |
| /bpm/task/reject | PUT | 不通过任务 | bpm:task:update |
| /bpm/task/list-by-return | GET | 获取所有可退回的节点 | bpm:task:update |
| /bpm/task/return | PUT | 退回任务 | bpm:task:update |
| /bpm/task/delegate | PUT | 委派任务 | bpm:task:update |
| /bpm/task/transfer | PUT | 转派任务 | bpm:task:update |
| /bpm/task/create-sign | PUT | 加签（before 前加签 / after 后加签） | bpm:task:update |
| /bpm/task/delete-sign | DELETE | 减签 | bpm:task:update |
| /bpm/task/copy | PUT | 抄送任务 | bpm:task:update |
| /bpm/task/withdraw | PUT | 撤回任务 | bpm:task:update |
| /bpm/task/list-by-parent-task-id | GET | 获得指定父级任务的子任务列表 | bpm:task:query |

### 流程评论 (BpmCommentController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/comment/list-by-process-instance-id | GET | 获得指定流程实例的评论列表 | bpm:task:query |
| /bpm/comment/create | POST | 创建流程评论 | bpm:task:update |

### OA 请假申请 (BpmOALeaveController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /bpm/oa/leave/create | POST | 创建请假申请（同时发起流程实例） | bpm:oa-leave:create |
| /bpm/oa/leave/get | GET | 获得请假申请 | bpm:oa-leave:query |
| /bpm/oa/leave/page | GET | 获得请假申请分页 | bpm:oa-leave:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| bpm_category | 流程分类 | BaseDO | name、code、description、status、sort |
| bpm_form | 动态表单 | BaseDO | name、status、conf（表单配置 JSON）、fields（表单项数组 JSON）、remark |
| bpm_user_group | 用户组 | BaseDO | name、description、status、userIds（成员编号数组 JSON） |
| bpm_process_definition_info | 流程定义扩展信息 | BaseDO | processDefinitionId、modelId、modelType、category、formType、formId、formConf、formFields、simpleModel、visible、startUserIds、startDeptIds、managerUserIds、allowCancelRunningProcess、allowWithdrawTask |
| bpm_process_expression | 流程表达式 | BaseDO | name、status、expression |
| bpm_process_listener | 流程监听器 | BaseDO | name、status、type（类型）、event（事件）、valueType、value |
| bpm_process_instance_copy | 流程实例抄送 | BaseDO | startUserId、processInstanceId、processDefinitionId、category、activityId、activityName、taskId、userId、reason |
| bpm_oa_leave | OA 请假申请（示例） | BaseDO | userId、type、reason、startTime、endTime、day、status、processInstanceId |

> 说明：流程模型与流程定义的"本体"数据存于 Flowable 引擎自带的 ACT_RE_MODEL、ACT_RE_PROCDEF、ACT_RU_/ACT_HI_ 系列表；上表仅为业务扩展表。所有 bpm_* 表均为 BaseDO 审计字段，模块未启用 TenantBaseDO 租户隔离（流程数据为全局共享）。

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 策略模式 | framework/flowable/core/candidate/strategy（`BpmTaskCandidateStrategy` 接口 + 15 个实现，如 Role/Post/UserGroup/DeptMember/DeptLeader/FormUser/Expression 等） | 按不同规则计算任务审批人，`BpmTaskCandidateInvoker` 按枚举路由到对应策略 |
| 模板方法模式 | candidate/strategy/dept/`AbstractBpmTaskCandidateDeptLeaderStrategy` | 抽取"部门负责人"类策略的公共层级查找逻辑，子类只实现差异步骤 |
| 工厂模式 | framework/flowable/core/behavior/`BpmActivityBehaviorFactory`（继承 Flowable DefaultActivityBehaviorFactory） | 接管用户任务 Behavior 与多实例 Behavior 的创建，注入自定义分配逻辑 |
| 策略模式 | service/task/trigger（`BpmTrigger` 接口 + `BpmSyncHttpRequestTrigger`/`BpmHttpCallbackTrigger`/`BpmFormUpdateTrigger`/`BpmFormDeleteTrigger`） | 流程节点触发时按触发类型分发到 HTTP 请求/回调或表单联动处理 |
| 观察者模式 | api/event（`BpmProcessInstanceStatusEvent` + `BpmProcessInstanceStatusEventListener` 抽象监听器） | 流程实例状态变更后发布 Spring 事件，CRM/OA/HRM 模块订阅后回写业务单据状态 |
| 事件监听模式 | framework/flowable/core/listener（`BpmProcessInstanceEventListener`、`BpmTaskEventListener`）与 service/task/listener（`BpmUserTaskListener`、`BpmCallActivityListener`） | 监听 Flowable 引擎实例/任务事件，维护扩展状态、超时提醒与抄送；service/message（`BpmMessageService`）负责审批短信通知 |

## 依赖关系

- **上游**（本模块依赖）:
  - framework: yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-test、yudao-spring-boot-starter-biz-data-permission、yudao-spring-boot-starter-biz-tenant
  - 业务模块: yudao-module-system（AdminUserApi、DeptApi、PostApi、RoleApi、PermissionApi、SmsSendApi）
  - 三方引擎: Flowable 6（flowable-spring-boot-starter-process、flowable-spring-boot-starter-actuator）

- **下游**（依赖本模块）:
  - yudao-module-crm（合同、回款审批接入）
  - yudao-module-oa（各类申请单接入流程审批）
  - yudao-module-hrm（考勤请假审批接入）
  - yudao-server（启动装配）

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|--------|------|-------|
| BpmProcessInstanceApi | createProcessInstance（创建流程实例）、cancelProcessInstanceByStartUser（发起人取消） | crm（CrmContractServiceImpl、CrmReceivableServiceImpl）、oa（各申请单 Service）、hrm（HrmAttendanceLeaveServiceImpl） |
| BpmProcessTaskApi | triggerTask（触发流程任务执行） | 内部扩展点（配合 HTTP 回调触发器） |
| BpmProcessInstanceStatusEvent / BpmProcessInstanceStatusEventListener | 事件订阅（extends ApplicationListener） | crm（CrmContractStatusListener、CrmReceivableStatusListener）、oa（各申请单状态监听器）、hrm（HrmAttendanceLeaveStatusListener） |

## 详细文档

- [api-definition.md](api-definition.md) - 流程定义域（模型/分类/表单/用户组/表达式/监听器/流程定义）
- [api-task.md](api-task.md) - 流程实例与任务域
- [api-comment.md](api-comment.md) - 流程评论域
- [api-oa.md](api-oa.md) - OA 请假示例域
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
