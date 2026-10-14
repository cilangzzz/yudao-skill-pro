# BPM 工作流代码模式与扩展指南 (bpm)

> 本文档移植自模块 Skill 知识库（skill-bpm.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

标准注解组合：

- `@Tag(name = "管理后台 - XXX")`
- `@RestController`
- `@RequestMapping("/bpm/xxx")`
- `@Validated`
- `@PreAuthorize("@ss.hasPermission(xxx)")`

示例（BpmTaskController）：

```java
@Tag(name = "管理后台 - 流程任务实例")
@RestController
@RequestMapping("/bpm/task")
@Validated
public class BpmTaskController {

    @Resource
    private BpmTaskService taskService;

    @PutMapping("/approve")
    @Operation(summary = "通过任务")
    @PreAuthorize("@ss.hasPermission('bpm:task:update')")
    public CommonResult<Boolean> approveTask(@Valid @RequestBody BpmTaskApproveReqVO reqVO) {
        taskService.approveTask(getLoginUserId(), reqVO);
        return success(true);
    }
}
```

### Service 层规范

接口定义在 `service/` 目录下，命名规则：`Bpm{Entity}Service`。

核心服务接口：

- `BpmModelService`：流程模型管理
- `BpmProcessDefinitionService`：流程定义管理
- `BpmProcessInstanceService`：流程实例管理
- `BpmTaskService`：流程任务管理

方法分类：

1. Query 查询相关方法 - 查询操作
2. Update 写入相关方法 - 修改操作
3. Event 事件相关方法 - 事件处理

实现类放在同目录下，命名规则：`Bpm{Entity}ServiceImpl`，使用 `@Service` 和 `@Validated` 注解。注意事项：

1. 循环依赖使用 `@Lazy` 注解
2. 事务操作使用 `@Transactional`
3. 数据权限使用 `@DataPermission`

示例（BpmProcessInstanceServiceImpl）：

```java
@Service
@Validated
@Slf4j
public class BpmProcessInstanceServiceImpl implements BpmProcessInstanceService {

    @Resource
    private RuntimeService runtimeService;  // Flowable 运行时服务
    @Resource
    private HistoryService historyService;  // Flowable 历史服务

    @Override
    public String createProcessInstance(Long userId, BpmProcessInstanceCreateReqDTO createReqDTO) {
        // 1. 获取流程定义
        ProcessDefinition processDefinition = processDefinitionService.getProcessDefinition(
            createReqDTO.getProcessDefinitionKey());
        // 2. 构建流程实例
        ProcessInstanceBuilder builder = runtimeService.createProcessInstanceBuilder()
            .processDefinitionKey(createReqDTO.getProcessDefinitionKey())
            .businessKey(createReqDTO.getBusinessKey())
            .variables(createReqDTO.getVariables());
        // 3. 启动流程实例
        return builder.start().getId();
    }
}
```

### DAL 层规范

Mapper 继承 `BaseMapperX`，提供基础 CRUD 操作，使用 `@Mapper` 注解。

特殊查询：

- 使用 MyBatis-Plus 的 `LambdaQueryWrapper`
- 复杂查询使用自定义 XML 或 `@Select` 注解

示例（BpmFormMapper）：

```java
@Mapper
public interface BpmFormMapper extends BaseMapperX<BpmFormDO> {

    default PageResult<BpmFormDO> selectPage(BpmFormPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<BpmFormDO>()
            .likeIfPresent(BpmFormDO::getName, reqVO.getName())
            .orderByDesc(BpmFormDO::getId));
    }
}
```

### 异常处理

BPM 模块错误码前缀为 `1-009-XXX-XXX`，常量统一定义在 `ErrorCodeConstants` 中，典型错误码：

| 错误码 | 说明 |
|-------|------|
| 1_009_002_000 | 已经存在流程标识为【{}】的流程 |
| 1_009_003_002 | 流程定义不存在 |
| 1_009_004_000 | 流程实例不存在 |
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |

### 统一响应

- 成功响应：`CommonResult.success(data)`
- 失败响应：`throw exception(ERROR_CODE, params...)`

### 流程发起示例

```java
// 方式一：通过 API 接口发起流程（推荐）
@Resource
private BpmProcessInstanceApi processInstanceApi;

public void submitLeave(LeaveCreateReqVO createReqVO) {
    // 1. 创建业务数据
    BpmOALeaveDO leave = new BpmOALeaveDO();
    // ... 设置属性
    leaveMapper.insert(leave);

    // 2. 发起流程
    BpmProcessInstanceCreateReqDTO reqDTO = new BpmProcessInstanceCreateReqDTO();
    reqDTO.setProcessDefinitionKey("oa_leave"); // 流程定义 Key
    reqDTO.setBusinessKey(leave.getId().toString()); // 业务主键
    reqDTO.setVariables(BeanUtil.beanToMap(createReqVO)); // 流程变量
    String processInstanceId = processInstanceApi.createProcessInstance(userId, reqDTO);

    // 3. 关联流程实例
    leave.setProcessInstanceId(processInstanceId);
    leaveMapper.updateById(leave);
}

// 方式二：通过 Controller 接口发起流程（前端调用）
@PostMapping("/create")
public CommonResult<String> createProcessInstance(@Valid @RequestBody BpmProcessInstanceCreateReqVO createReqVO) {
    return success(processInstanceService.createProcessInstance(getLoginUserId(), createReqVO));
}
```

### 任务审批示例

```java
// 审批通过
@PutMapping("/approve")
public CommonResult<Boolean> approveTask(@Valid @RequestBody BpmTaskApproveReqVO reqVO) {
    taskService.approveTask(getLoginUserId(), reqVO);
    return success(true);
}

// 审批拒绝
@PutMapping("/reject")
public CommonResult<Boolean> rejectTask(@Valid @RequestBody BpmTaskRejectReqVO reqVO) {
    taskService.rejectTask(getLoginUserId(), reqVO);
    return success(true);
}

// 任务退回
@PutMapping("/return")
public CommonResult<Boolean> returnTask(@Valid @RequestBody BpmTaskReturnReqVO reqVO) {
    taskService.returnTask(getLoginUserId(), reqVO);
    return success(true);
}

// 任务委派
@PutMapping("/delegate")
public CommonResult<Boolean> delegateTask(@Valid @RequestBody BpmTaskDelegateReqVO reqVO) {
    taskService.delegateTask(getLoginUserId(), reqVO);
    return success(true);
}
```

## 扩展指南

### 新增审批类型（如报销、采购等）

**步骤 1：创建业务 DO 实体**

在 `dal/dataobject/` 下创建业务实体类，如 `BpmExpenseDO`，需要包含 `processInstanceId` 字段关联流程实例。

**步骤 2：创建业务表**

创建对应数据库表，包含业务字段和 `process_instance_id` 字段。

**步骤 3：创建业务服务**

创建 Service 接口和实现类，实现业务逻辑，调用 `BpmProcessInstanceApi` 发起流程。

**步骤 4：实现流程状态监听**

实现 `BpmProcessInstanceStatusEventListener`，监听流程状态变更，更新业务表状态。示例：

```java
@Component
public class BpmExpenseStatusListener extends BpmProcessInstanceStatusEventListener {
    @Override
    protected void onEvent(BpmProcessInstanceStatusEvent event) {
        if ("expense".equals(event.getProcessDefinitionKey())) {
            // 更新报销单状态
            expenseMapper.updateStatus(event.getBusinessKey(), event.getStatus());
        }
    }
}
```

**步骤 5：配置流程定义**

在管理后台配置流程定义：

1. 创建流程分类
2. 创建流程表单
3. 设计流程图（BPMN 或 Simple）
4. 配置审批人策略

### 自定义审批人策略

**步骤 1：添加策略枚举**

在 `BpmTaskCandidateStrategyEnum` 中添加新的策略类型。

**步骤 2：实现策略接口**

实现 `BpmTaskCandidateStrategy` 接口。示例：

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

**步骤 3：注册策略 Bean**

使用 `@Component` 注解，Spring 自动注册到策略工厂。

### 自定义流程监听器

**步骤 1：创建监听器类**

实现 `ExecutionListener` 或 `TaskListener` 接口。

示例（执行监听器）：

```java
@Component
public class CustomExecutionListener implements ExecutionListener {
    @Override
    public void notify(DelegateExecution execution) {
        // 监听逻辑
    }
}
```

示例（任务监听器）：

```java
@Component
public class CustomTaskListener implements TaskListener {
    @Override
    public void notify(DelegateTask delegateTask) {
        // 监听逻辑
    }
}
```

**步骤 2：注册监听器**

方式一：通过数据库配置（推荐），在 `bpm_process_listener` 表中添加监听器配置。

方式二：在 BPMN XML 中配置：

```xml
<extensionElements>
    <flowable:executionListener event="start" delegateExpression="${customExecutionListener}"/>
</extensionElements>
```

### 最佳实践

- 流程设计原则：流程定义和业务数据分离，通过 businessKey 关联
- 审批人策略：优先使用已有的审批人策略，如角色、部门负责人、用户组等
- 流程变量：使用流程变量传递表单数据，避免过度依赖业务查询
- 事件监听：通过监听流程状态变更事件更新业务状态，实现解耦
- Simple 设计器：对于简单审批流程，推荐使用 Simple 设计器，降低学习成本
- 流程版本：同一流程定义可以部署多个版本，已运行的实例使用旧版本
- 权限控制：通过 managerUserIds 配置流程管理员，实现流程管理权限分离

## 模块依赖

### 内部依赖（其他模块）

| 模块 | API | 用途 |
|-----|-----|------|
| yudao-module-system | AdminUserApi | 获取用户信息，用于审批人计算和流程发起人信息 |
| yudao-module-system | DeptApi | 获取部门信息，用于部门负责人审批策略 |
| yudao-module-system | PermissionApi | 获取用户角色，用于角色审批策略 |
| yudao-module-system | PostApi | 获取岗位信息，用于岗位审批策略 |

### 外部依赖（三方库与框架 Starter）

| 依赖 | 版本 | 用途 |
|-----|------|------|
| flowable-spring-boot-starter-process | 6.x | Flowable 工作流引擎核心 |
| flowable-spring-boot-starter-actuator | 6.x | Flowable 监控端点 |
| yudao-spring-boot-starter-mybatis | ${revision} | MyBatis-Plus 数据访问 |
| yudao-spring-boot-starter-biz-tenant | ${revision} | 多租户支持 |
| yudao-spring-boot-starter-biz-data-permission | ${revision} | 数据权限控制 |

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/service/task/BpmProcessInstanceService.java | 流程实例服务接口，定义流程实例的核心操作 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/service/task/BpmTaskService.java | 流程任务服务接口，定义任务审批的核心操作 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/service/definition/BpmModelService.java | 流程模型服务接口，定义流程模型管理操作 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/api/task/BpmProcessInstanceApi.java | 流程实例 API 接口，供其他模块调用发起流程 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/api/event/BpmProcessInstanceStatusEvent.java | 流程状态变更事件，实现模块间解耦 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/framework/flowable/core/candidate/BpmTaskCandidateStrategy.java | 审批人策略接口，定义审批人计算的标准 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/framework/flowable/core/enums/BpmTaskCandidateStrategyEnum.java | 审批人策略枚举，列出所有支持的审批人分配方式 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/enums/ErrorCodeConstants.java | 错误码常量，定义 BPM 模块所有错误码 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/enums/definition/BpmModelTypeEnum.java | 流程模型类型枚举，区分 BPMN 和 Simple 设计器 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/enums/task/BpmProcessInstanceStatusEnum.java | 流程实例状态枚举，定义流程的所有状态 |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/controller/admin/task/BpmTaskController.java | 任务管理 Controller，提供任务审批相关 API |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/controller/admin/task/BpmProcessInstanceController.java | 流程实例 Controller，提供流程实例管理 API |
| yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/service/oa/listener/BpmOALeaveStatusListener.java | 请假流程状态监听示例，展示如何监听流程状态变更 |
| yudao-module-bpm/pom.xml | Maven 依赖配置，包含 Flowable 等核心依赖 |

## 领域模型

### 聚合与实体

| 聚合/实体 | 类型 | 包含实体 | 说明 |
|----------|------|---------|------|
| 流程定义 (ProcessDefinition) | 聚合根 | BpmFormDO（流程表单）、BpmCategoryDO（流程分类）、BpmUserGroupDO（审批用户组）、BpmProcessDefinitionInfoDO（流程定义扩展信息）、BpmProcessListenerDO（流程监听器）、BpmProcessExpressionDO（流程表达式） | 流程定义是流程的模板，包含流程结构、表单配置、审批规则等元数据 |
| 流程实例 (ProcessInstance) | 聚合根 | BpmProcessInstanceCopyDO（流程抄送记录） | 流程实例是流程定义的一次执行，由 Flowable 原生表管理，扩展信息存储在 DO 中 |
| 流程任务 (Task) | 实体 | — | 流程任务是流程实例中的审批节点，由 Flowable 原生表管理 |

### 值对象

- `BpmProcessInstanceCreateReqDTO` - 流程实例创建请求
- `BpmModelMetaInfoVO` - 流程模型元信息
- `BpmSimpleModelNodeVO` - Simple 设计器节点定义

### 领域服务

- `BpmModelService` - 流程模型管理服务
- `BpmProcessDefinitionService` - 流程定义管理服务
- `BpmProcessInstanceService` - 流程实例管理服务
- `BpmTaskService` - 流程任务管理服务
- `BpmFormService` - 表单管理服务
- `BpmMessageService` - 流程消息服务

## 设计与架构补充

### 限界上下文与引擎适配

- **领域驱动设计 (DDD)**：按流程定义（Definition）、流程实例（Instance）、任务（Task）划分限界上下文，`service/` 层的 `definition/`、`task/` 目录结构与之对应。
- **适配器模式**：Service 层封装 Flowable 原生 API（`RuntimeService`、`HistoryService` 等），隔离底层工作流引擎实现，业务代码不直接依赖引擎内部类型。

### 分层架构

| 层 | 职责 | 主要组件 |
|---|------|---------|
| api | 模块间 API 接口，供其他模块调用 | BpmProcessInstanceApi（流程实例创建接口）、BpmProcessTaskApi（流程任务操作接口）、BpmProcessInstanceStatusEvent（流程状态变更事件） |
| controller | HTTP 接口，供前端调用 | BpmModelController（流程模型）、BpmProcessDefinitionController（流程定义）、BpmProcessInstanceController（流程实例）、BpmTaskController（流程任务）、BpmFormController（表单）、BpmCategoryController（分类）、BpmUserGroupController（用户组）、BpmOALeaveController（请假申请示例） |
| service | 业务逻辑层，封装核心业务 | definition/（流程定义相关服务）、task/（流程任务相关服务）、message/（消息通知服务）、oa/（OA 业务示例，请假） |
| dal | 数据访问层，与数据库交互 | dataobject/definition/（定义相关 DO）、dataobject/task/（任务相关 DO）、dataobject/oa/（OA 相关 DO）、mysql/（MyBatis Mapper）、redis/（Redis 缓存） |
| framework/flowable | Flowable 框架集成层 | config/BpmFlowableConfiguration（Flowable 配置）、core/candidate/（审批人策略实现）、core/listener/（流程监听器）、core/behavior/（自定义行为）、core/util/（工具类） |

### 表关系与 Flowable 原生表

业务扩展表之间的关系（ER）：

| 源表 | 目标表 | 关系 | 外键 |
|-----|-------|------|------|
| bpm_process_definition_info | bpm_category | N:1 | category -> code |
| bpm_process_definition_info | bpm_form | N:1 | form_id -> id |
| bpm_process_instance_copy | Flowable ProcessInstance | N:1 | process_instance_id -> id |
| bpm_oa_leave | Flowable ProcessInstance | 1:1 | process_instance_id -> id |

流程本体数据存于 Flowable 原生表，由引擎自动维护：

| 表名 | 说明 |
|-----|------|
| ACT_RE_DEPLOYMENT | 部署信息表 |
| ACT_RE_PROCDEF | 流程定义表 |
| ACT_RE_MODEL | 流程模型表 |
| ACT_RU_EXECUTION | 运行时执行实例表 |
| ACT_RU_TASK | 运行时任务表 |
| ACT_HI_PROCINST | 历史流程实例表 |
| ACT_HI_TASKINST | 历史任务实例表 |
| ACT_HI_VARINST | 历史变量表 |
