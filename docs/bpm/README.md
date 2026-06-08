# BPM 工作流模块

> 基于 Flowable 6 实现的完整业务流程管理模块，解决企业内部审批流程与业务流程自动化问题。

## 模块定位

BPM (Business Process Management) 模块是 yudao-skill-pro 的工作流引擎核心模块。它封装 Flowable 工作流引擎，提供流程定义、流程实例、任务审批、表单管理等完整能力，供业务模块（如 OA 请假、报销、采购等）集成使用。

**模块路径：** `yudao-module-bpm`

---

## 核心功能

| 功能域 | 说明 | 关键服务 |
|--------|------|----------|
| 流程模型管理 | 创建、修改、部署流程模型，支持 BPMN 2.0 和仿钉钉 Simple 两种设计器 | `BpmModelService` |
| 流程定义管理 | 查询已部署的流程定义，支持版本管理、启用/停用 | `BpmProcessDefinitionService` |
| 流程表单管理 | 动态表单配置，表单与流程定义绑定，支持业务表单和流程表单两种模式 | `BpmFormService` |
| 流程实例管理 | 发起、取消、查询流程实例，支持流程变量传递 | `BpmProcessInstanceService` |
| 任务审批管理 | 待办/已办查询，审批通过/拒绝，退回/委派/转办/加签/减签 | `BpmTaskService` |
| 流程抄送 | 流程节点抄送指定用户 | `BpmProcessInstanceService` |
| 流程监听器 | 执行监听器和任务监听器，支持 class/delegateExpression/expression 三种类型 | `BpmProcessListenerDO` |
| 审批人策略 | 角色、部门负责人、用户组、指定用户、流程表达式等多种分配方式 | `BpmTaskCandidateStrategy` |
| 流程消息 | 流程状态变更消息通知 | `BpmMessageService` |
| OA 请假示例 | 内置 OA 请假业务作为集成示例 | `BpmOALeaveController` |

---

## 架构分层

```
api/                    -- 模块间 API 接口，供其他业务模块调用
  BpmProcessInstanceApi   流程实例创建
  BpmProcessTaskApi       流程任务触发
  BpmProcessInstanceStatusEvent  流程状态变更事件
controller/             -- HTTP 接口，供前端调用
  admin/                  管理后台接口
  app/                    用户端接口
service/                -- 业务逻辑层
  definition/             流程定义与模型
  task/                   流程实例与任务
  form/                   表单管理
  message/                消息通知
  oa/                     OA 业务示例
dal/                    -- 数据访问层
  dataobject/             DO 实体
  mysql/                  MyBatis Mapper
framework/flowable/     -- Flowable 集成层
  config/                 Flowable 配置
  core/candidate/         审批人策略
  core/listener/          流程监听器
  core/behavior/          自定义行为
```

---

## API 索引

### 管理后台接口 (admin)

| Controller | 路径前缀 | 详细文档 |
|-----------|---------|----------|
| BpmModelController | `/bpm/model` | [api-model.md](./api-model.md) |
| BpmProcessDefinitionController | `/bpm/process-definition` | [api-definition.md](./api-definition.md) |
| BpmProcessInstanceController | `/bpm/process-instance` | [api-instance.md](./api-instance.md) |
| BpmTaskController | `/bpm/task` | [api-task.md](./api-task.md) |
| BpmFormController | `/bpm/form` | [api-form.md](./api-form.md) |
| BpmCategoryController | `/bpm/category` | [api-category.md](./api-category.md) |
| BpmUserGroupController | `/bpm/user-group` | [api-usergroup.md](./api-usergroup.md) |
| BpmOALeaveController | `/bpm/oa-leave` | [api-task.md](./api-task.md) (OA 示例) |

### 模块间 API

| 接口 | 方法 | 说明 |
|------|------|------|
| BpmProcessInstanceApi | `createProcessInstance` | 供其他模块发起流程实例 |
| BpmProcessTaskApi | `triggerTask` | 触发流程任务执行 |
| BpmProcessInstanceStatusEvent | - | 流程状态变更事件（Spring Event） |

---

## 数据模型

详见 [data-model.md](./data-model.md)

**核心聚合根：**

- **流程定义 (ProcessDefinition)** -- 包含表单配置、分类、审批人规则、监听器、表达式等元数据
- **流程实例 (ProcessInstance)** -- 流程定义的一次执行，运行时数据由 Flowable 原生表管理
- **流程任务 (Task)** -- 流程实例中的审批节点，由 Flowable 原生表管理

**自建数据表：** `bpm_category`, `bpm_form`, `bpm_user_group`, `bpm_process_definition_info`, `bpm_process_listener`, `bpm_process_expression`, `bpm_process_instance_copy`, `bpm_oa_leave`

**Flowable 原生表：** `ACT_RE_DEPLOYMENT`, `ACT_RE_PROCDEF`, `ACT_RE_MODEL`, `ACT_RU_EXECUTION`, `ACT_RU_TASK`, `ACT_HI_PROCINST`, `ACT_HI_TASKINST`, `ACT_HI_VARINST`

---

## 设计模式

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| 策略模式 | `BpmTaskCandidateStrategy` | 审批人分配策略，支持角色、部门、用户、表达式等多种方式 |
| 事件驱动 | `BpmProcessInstanceStatusEvent` | 流程状态变更事件，通过 Spring ApplicationEvent 通知其他模块 |
| 监听器模式 | `BpmTaskEventListener` | 监听 Flowable 任务事件，执行自定义逻辑 |
| 工厂模式 | `BpmActivityBehaviorFactory` | 创建自定义 ActivityBehavior，扩展 Flowable 行为 |
| 模板方法模式 | `BpmTrigger` | 流程触发器抽象，支持 HTTP 请求、表单操作等触发类型 |
| 适配器模式 | Flowable API 封装层 | 隔离底层工作流引擎实现 |

---

## 依赖关系

### 内部模块依赖

| 模块 | API | 用途 |
|------|-----|------|
| yudao-module-system | AdminUserApi | 获取用户信息 |
| yudao-module-system | DeptApi | 获取部门信息（部门负责人策略） |
| yudao-module-system | PermissionApi | 获取用户角色（角色审批策略） |
| yudao-module-system | PostApi | 获取岗位信息（岗位审批策略） |

### 外部依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| flowable-spring-boot-starter-process | 6.x | Flowable 工作流引擎核心 |
| flowable-spring-boot-starter-actuator | 6.x | Flowable 监控端点 |
| yudao-spring-boot-starter-mybatis | ${revision} | MyBatis-Plus 数据访问 |
| yudao-spring-boot-starter-biz-tenant | ${revision} | 多租户支持 |
| yudao-spring-boot-starter-biz-data-permission | ${revision} | 数据权限控制 |

---

## 扩展指南

### 新增审批类型（如报销、采购）

1. 创建业务 DO 实体，包含 `processInstanceId` 字段
2. 创建对应数据库表
3. 创建 Service，调用 `BpmProcessInstanceApi.createProcessInstance()` 发起流程
4. 实现 `BpmProcessInstanceStatusEventListener`，监听流程状态变更更新业务状态
5. 在管理后台配置流程定义、表单、流程图、审批人策略

### 自定义审批人策略

1. 在 `BpmTaskCandidateStrategyEnum` 中添加策略枚举
2. 实现 `BpmTaskCandidateStrategy` 接口
3. 使用 `@Component` 注册为 Spring Bean

### 自定义流程监听器

1. 实现 `ExecutionListener` 或 `TaskListener` 接口
2. 通过 `bpm_process_listener` 数据库表或 BPMN XML 配置注册

---

## 常见陷阱

详见 [pitfalls.md](./pitfalls.md)

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/task/BpmProcessInstanceService.java` | 流程实例核心服务接口 |
| `service/task/BpmTaskService.java` | 任务审批核心服务接口 |
| `service/definition/BpmModelService.java` | 流程模型管理服务接口 |
| `api/task/BpmProcessInstanceApi.java` | 模块间流程实例 API |
| `api/event/BpmProcessInstanceStatusEvent.java` | 流程状态变更事件 |
| `framework/flowable/core/candidate/BpmTaskCandidateStrategy.java` | 审批人策略接口 |
| `enums/ErrorCodeConstants.java` | BPM 模块错误码 |
| `enums/definition/BpmModelTypeEnum.java` | 模型类型枚举（BPMN/Simple） |
| `enums/task/BpmProcessInstanceStatusEnum.java` | 流程实例状态枚举 |
| `controller/admin/task/BpmTaskController.java` | 任务管理 Controller |
| `controller/admin/task/BpmProcessInstanceController.java` | 流程实例 Controller |
| `service/oa/listener/BpmOALeaveStatusListener.java` | 请假流程状态监听示例 |
