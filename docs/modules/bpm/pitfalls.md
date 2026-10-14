# 注意事项与已知坑点

> 使用 bpm 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 Flowable 异步执行/定时器线程会丢失租户上下文

**问题**: 在定时器超时（延迟器、审批超时）、SIMPLE 触发器等 Flowable 异步路径里执行自定义代码时，`TenantContextHolder.getTenantId()` 返回 null，导致后续调用 system 模块接口或业务 Mapper 时查不到数据。

**原因**: Flowable 的 Job 执行线程不是请求线程，TenantContextHolder 基于 ThreadLocal，天然为空。框架自身代码对此有大量防御：`BpmTaskCandidateInvoker.calculateUsersByTask` 的注释明确写了"解决极端情况下，Flowable 异步调用，导致租户 id 丢失的情况。例如说，SIMPLE 延迟器在 trigger 的时候！！！"，并用 `FlowableUtils.execute(execution.getTenantId(), ...)` 包裹；`BpmTaskEventListener` 的 taskCreated/taskAssigned/taskCompleted/timerFired、`BpmTaskServiceImpl.processTaskTimeout`、`triggerTask`、`processTaskAssigned`（注释："需要基于 instance 设置租户编号，避免 Flowable 内部异步执行时【例如：超时自动通过】丢失租户编号"）都做了同样包装。

**解决**: 自定义 Flowable 监听器、JavaDelegate、Trigger 时，必须从 Flowable 实体上取 tenantId 后用 `FlowableUtils.execute(tenantId, runnable)` 包裹业务逻辑，不要直接裸写：

```java
// BpmTaskEventListener 的标准姿势
Task entity = (Task) event.getEntity();
FlowableUtils.execute(entity.getTenantId(), () -> taskService.processTaskCreated(entity));
```

### 1.2 bpm 业务表没有租户字段，租户过滤完全依赖查询条件

**问题**: 期望 MyBatis-Plus 租户拦截器自动过滤 bpm 表数据，实际不会；按流程 key 查询时可能跨租户命中其他租户的数据，极端情况下会误删。

**原因**: bpm 全部 8 个 DO（`BpmProcessDefinitionInfoDO`、`BpmFormDO`、`BpmUserGroupDO`、`BpmProcessInstanceCopyDO`、`BpmOALeaveDO` 等）都继承 `BaseDO` 而非 `TenantBaseDO`，表里没有 tenant_id 列，拦截器无从过滤。租户隔离靠 Flowable 引擎的 `TENANT_ID_` 列 + 代码里手工拼条件：`BpmModelServiceImpl.getModelByKey` 用 `modelTenantId(FlowableUtils.getTenantId())`，`getProcessInstancePage` 用 `processInstanceTenantId(...)`。但 `BpmModelServiceImpl.cleanModel` 按 `processDefinitionKey(model.getKey())` 查运行中实例、历史实例、任务时没有带租户条件——而同一个 key 允许在不同租户各自创建（getModelByKey 是租户内唯一），执行"清理流程数据"会把其他租户同 key 流程的实例和抄送一并删掉。此外 `cleanModel` 没有 `@Transactional`，删除是分步执行、失败后不回滚。

**解决**: 自定义 Flowable 查询必须显式带上租户条件（`modelTenantId` / `processInstanceTenantId` / `taskTenantId` / `processDefinitionTenantId`）；不要假设有拦截器兜底。使用 cleanModel 前先确认同 key 只存在于当前租户，或先修复其查询条件。

## 2. 事务与外部调用相关

### 2.1 流程结束的短信、事件、HTTP 通知都在同一个事务内同步执行

**问题**: 审批通过/拒绝时，如果下游接口不可用或监听器抛异常，整个审批操作一起失败回滚；HTTP 通知参数配错会导致流程无法继续。

**原因**: `BpmProcessInstanceEventListener.processCompleted` 在 Flowable 完成事务内调用 `processProcessInstanceCompleted`，其中依次同步执行：短信（`BpmMessageServiceImpl.sendMessageWhenProcessInstanceApprove`）、Spring 事件（`BpmProcessInstanceEventPublisher` 用 `ApplicationEventPublisher.publishEvent`，`BpmProcessInstanceStatusEventListener` 是普通 `ApplicationListener` 而非 `@TransactionalEventListener`，crm/oa/hrm 的回写监听器都在同一事务里跑）、流程后置 HTTP 通知（`BpmHttpRequestUtils.executeBpmHttpRequest`，`sendHttpRequest` 出错直接抛 `PROCESS_INSTANCE_HTTP_CALL_ERROR`）。另外 `BpmHttpRequestUtils.addHttpRequestParam` 对 FROM_FORM 类型参数直接 `processVariables.get(item.getValue()).toString()`，流程变量不存在就 NPE。

**解决**: 配置流程/任务前后置 HTTP 通知时确保目标服务高可用、参数变量一定存在；下游监听器（继承 `BpmProcessInstanceStatusEventListener`）内部要自行捕获异常，不能让异常冒泡，否则审批人会直接收到报错。

### 2.2 第一个任务就"自动通过/自动拒绝"时，afterCommit 回调不会触发

**问题**: 仿照 `processTaskCreated` 写事务提交后逻辑（用 afterCommit），在"第一个节点自动通过"等场景下回调不执行。

**原因**: `BpmTaskServiceImpl.processTaskCreated` / `processTaskAssigned` 的注释明确记录了该问题："部分情况下，TransactionSynchronizationManager 注册 afterCommit 监听时，不会被调用，但是 afterCompletion 可以（例如说：第一个 task 就是配置【自动通过】或者【自动拒绝】时）"，参见 yudao-cloud issue IB7V7Q。并且 afterCompletion 里还要特判 `STATUS_UNKNOWN`（第一个 task 自动通过时第二个任务设置审批人会出现该状态），先查 `getTask(task.getId()) == null` 判断任务是否真的不存在再继续。

**解决**: 依赖事务收尾的逻辑用 `registerSynchronization` 的 `afterCompletion` 实现，并照抄对 `STATUS_ROLLED_BACK`、`STATUS_UNKNOWN` 的两个防御分支，不要改回 afterCommit。

### 2.3 同一个 Service 内部调用带注解的方法会绕过 AOP 代理

**问题**: 在 `BpmTaskServiceImpl` 内部直接调用本类的 `approveTask`/`rejectTask` 时，方法上的 `@DataPermission(enable = false)` 与 `@Transactional` 注解不生效，可能因数据权限过滤查不到数据导致自动审批失败。

**原因**: Spring AOP 基于代理。该类专门提供了 `getSelf()`（注释："获得自身的代理对象，解决 AOP 生效问题"，用 `SpringUtil.getBean(getClass())` 获取代理），`processTaskCreated`、`processTaskAssigned` 里的自动通过/转办都走 `getSelf().approveTask(...)`。但 `processTaskTimeout`（超时自动同意/拒绝）里是直接 `approveTask(...)` 直调，注解被绕过，属于已知不一致。

**解决**: 在类内部调用本类的 `@Transactional`、`@DataPermission` 方法时，一律通过 `getSelf()`；编写类似超时处理逻辑时不要模仿 `processTaskTimeout` 的直调写法。

## 3. 状态机与查询相关

### 3.1 Flowable 版本锁定 6.8.0，升级会破坏回退功能，并行分支取消是已知薄弱点

**问题**: 升级 Flowable 版本后回退（退回）功能阻塞；并行分支场景下取消/终止流程会走"强制删除"的兜底路径。

**原因**: `yudao-dependencies/pom.xml` 明确注释 `<flowable.version>6.8.0</flowable.version> <!-- 不要升级 6.8.1：退回有 bug https://github.com/flowable/flowable-engine/issues/3944 -->`。`BpmTaskServiceImpl.returnTask` 的长注释记录了 `moveActivityIdsToSingleActivityId` 与 `moveExecutionsToSingleActivityId` 在多实例（芋道用户任务默认多实例）、flowable 6.8.1~7.2.0、8.0.0 各版本上的取舍。`moveTaskToEnd` 结尾还有兜底："如果跳转到 EndEvent 流程还未结束，执行 deleteProcessInstance 方法"（注释 TODO："目前发现并行分支情况下，会存在这个情况"），并行分支取消时不会正常走 EndEvent。另外 TODO 记录 Flowable 的 `taskCreatedAfter/taskCreatedBefore` 拼接 OR 的 bug 需要升级 7.1.0 才能修复。

**解决**: 不要随意升级 Flowable；确需升级时必须回归回退、加签、并行分支、超时提醒四类场景。业务建模尽量避免在并行网关分支上做"取消流程"操作。

### 3.2 任务列表按创建时间过滤是"先分页、后内存过滤"，分页总数不准

**问题**: 待办/已办任务按创建时间区间筛选时，返回的 total 偏大、单页条数少于 pageSize，甚至翻到整页空数据。

**原因**: Flowable 的 `taskCreatedAfter/taskCreatedBefore` 拼接条件是 OR（`BpmTaskServiceImpl` 两处 TODO 注释），框架只能把查询侧代码注释掉，改为查询后内存过滤：先 `taskQuery.count()` 拿总数、`listPage` 取当前页，再 `tasks.removeIf(...)` 过滤时间。过滤发生在分页之后，count 里包含了不满足时间的任务。

**解决**: 前端理解 total 为近似值；对时间筛选准确性要求高时，自定义 SQL 按 `ACT_HI_TASKINST.START_TIME_` 过滤，不要复用这两个分页方法。

### 3.3 任务状态和审批意见存在 VariableLocal 里，不是表字段

**问题**: 直接查 `ACT_RU_TASK`/`ACT_HI_TASKINST` 表或自定义 SQL 时看不到任务审批状态（通过/拒绝/退回/取消）和审批意见；查询遗漏 include 参数时状态永远是 null。

**原因**: `BpmTaskServiceImpl.updateTaskStatus` 的实现就是 `taskService.setVariableLocal(id, BpmnVariableConstants.TASK_VARIABLE_STATUS, status)`，reason 同理。读取时靠 `FlowableUtils.getTaskStatus/getTaskReason` 从 `getTaskLocalVariables()` 取；历史查询必须 `.includeTaskLocalVariables()`，条件过滤用 `taskVariableValueEquals(TASK_VARIABLE_STATUS, ...)`。另外待办列表会在查询后内存移除发起人节点：`tasks.removeIf(task -> task.getTaskDefinitionKey().equals(START_USER_NODE_ID))`（发起人节点自动通过，属于系统内部节点）。

**解决**: 判断任务状态一律走 `BpmTaskService` / `FlowableUtils` 封装，不要直查表；流程实例状态同理存在流程变量 `PROCESS_INSTANCE_VARIABLE_STATUS` 中（`FlowableUtils.getProcessInstanceStatus`），Flowable 自身的 `endTime/ deleteReason` 不能替代该状态。

## 4. 部署与模型相关

### 4.1 修改模型不重新发布不生效；每次发布会挂起旧定义；key/name 必须与 BPMN 一致

**问题**: 修改流程图/审批人配置后流程行为不变；重新发布后老单据"看起来被挂起"；导入外部 BPMN 报"流程定义的标识期望是({})，当前是({})"。

**原因**: `saveModel`/`updateSimpleModel` 只更新 `ACT_RE_MODEL`，运行时读取的是 `ProcessDefinition` 的 BpmnModel，必须执行 `deployModel` 生成新版本才生效。`deployModel` 中"将老的流程定义进行挂起。也就是说，只有最新部署的流程定义，才可以发起任务"（`updateProcessDefinitionSuspended(model.getDeploymentId())`），但 `updateProcessDefinitionState` 挂起时 `suspendProcessInstances = false`，在途实例继续按旧版本跑完。`createProcessDefinition` 里校验 ProcessDefinition 的 key/name 由 BPMN XML 中 `<bpmn2:process/>` 的 id/name 决定，与 Model 不一致直接抛 `PROCESS_DEFINITION_KEY_NOT_MATCH` / `PROCESS_DEFINITION_NAME_NOT_MATCH`。

**解决**: 改完模型必须点发布；理解"挂起"只拦截新发起、不影响在途实例；导入/编辑 BPMN XML 时保持 process 的 id、name 与 Model 的 key、name 一致。

## 5. 审批人规则相关

### 5.1 "审批人与发起人相同时自动跳过"在单一候选人时不生效

**问题**: 节点配置了"审批人与发起人相同时跳过"，但当该节点算出来的候选人只有发起人自己时，任务仍会分配给发起人，出现"自己审自己"。

**原因**: `BpmTaskCandidateInvoker.removeStartUserIfSkip` 开头就是 `if (CollUtil.size(assigneeUserIds) <= 1) { return; }`，注释明确："注意：如果只有一个候选人，则不处理，避免无法审批"。即移除发起人的前提是移除后还有别的候选人。此外候选人计算会先 `removeDisableUsers` 移除禁用用户，再走"审批人为空"策略（ASSIGN_EMPTY），禁用用户恰好被移空时不会触发"发起人相同跳过"。

**解决**: 设计流程时不要让"发起人相同跳过"的节点候选人是发起人单人；需要覆盖该场景时应配置"审批人为空"的处理策略（自动通过/自动拒绝/转交部门负责人）兜底。

## 6. 其它

### 6.1 错误码 1_009_004_005 被两个不同语义的错误重复使用

**问题**: 前端或调用方按错误码分支处理"无权限发起"与"不允许取消"时无法区分，提示语错乱。

**原因**: `enums/ErrorCodeConstants` 中 `PROCESS_INSTANCE_START_USER_CAN_START = new ErrorCode(1_009_004_005, "发起流程失败，你没有权限发起该流程")` 与 `PROCESS_INSTANCE_CANCEL_FAIL_NOT_ALLOW = new ErrorCode(1_009_004_005, "流程取消失败，该流程不允许取消")` 编号完全相同。新增错误码时按段分配（模型 1_009_002_xxx、定义 1_009_003_xxx、实例 1_009_004_xxx、任务 1_009_005_xxx、表单 1_009_010_xxx 等）即可避免。

**解决**: 自定义扩展时先全局搜索确认编号未被占用；如有升级窗口建议把 `PROCESS_INSTANCE_CANCEL_FAIL_NOT_ALLOW` 调整为 `1_009_004_010` 之后的空位（注意与已有 1_009_004_006~009 错开）。

### 6.2 自定义流程 ID 规则：Redis 序号的过期条件与注释相反

**问题**: 流程 ID 规则不配置日期中缀（infix）时，Redis 序号 key 一天后过期，序号从 0 重新开始；由于生成的序号经 `predefineProcessInstanceId` 直接作为流程实例 ID，重复后创建流程会撞 Flowable 主键。而配置了日期中缀时，历史日期 key 反而永不过期，Redis 键持续累积。

**原因**: `BpmProcessIdRedisDAO.generate` 中 `if (StrUtil.isEmpty(infix)) { stringRedisTemplate.expire(key, Duration.ofDays(1L)); }` 与其上方注释"没有前缀，则不能过期，不能每次都是从 0 开始"语义相反：infix 为空时 key 固定不变却每次续 1 天过期；infix 非空（DAY/HOUR 等）时 key 每天自然轮换却从不设置过期。每次调用都会刷新 TTL，因此只有"整整一天没有任何新流程发起"时序号才会清零，隐蔽性强。

**解决**: 配置流程 ID 规则时务必选择日期中缀（至少 DAY 粒度），避免纯前缀+后缀；修复代码时应将条件改为 `StrUtil.isNotEmpty(infix)`（有日期中缀才对旧 key 设置过期清理）。
