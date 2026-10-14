# 流程实例与任务接口 (BpmProcessInstanceController / BpmTaskController / BpmProcessInstanceCopyController)

> 流程实例域负责发起流程、查询"我的流程/全部流程"、审批详情预测与 BPMN 进度视图、取消流程；流程任务域负责待办/已办/全部任务分页、通过/不通过/退回/委派/转派/加签/减签/撤回/抄送等审批操作；抄送域提供抄送记录分页查询。

## 接口路径前缀

- /bpm/process-instance (Controller: BpmProcessInstanceController)
- /bpm/task (Controller: BpmTaskController)
- /bpm/process-instance/copy (Controller: BpmProcessInstanceCopyController)

> 下文 Response VO 中的用户信息均为 `UserSimpleBaseVO`（用户精简信息）：| 字段 | 类型 | 说明 | 其中 id/nickname/deptId/deptName 必返，avatar 可空 |。下文分页请求 VO 均继承 `PageParam`：pageNo（Integer，必填，@NotNull @Min(1)，页码从 1 开始）、pageSize（Integer，必填，@NotNull @Min(1) @Max(200)，最大 200）。

---

## 一、流程实例（BpmProcessInstanceController）

公共请求 VO **BpmProcessInstancePageReqVO**（继承 PageParam，1.1 / 1.2 共用）：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| name | String | 否 | 无 | 流程名称（模糊匹配） |
| processDefinitionKey | String | 否 | 无 | 流程定义的标识（精准匹配） |
| status | Integer | 否 | @InEnum(BpmProcessInstanceStatusEnum) | 流程实例的状态 |
| category | String | 否 | 无 | 流程分类 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| endTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 结束时间区间 |
| startUserId | Long | 否 | 无 | 发起用户编号（仅【流程实例】管理菜单使用） |
| formFieldsParams | String | 否 | 无 | 动态表单字段查询 JSON 字符串 |

公共响应 VO **BpmProcessInstanceRespVO**（1.1 / 1.2 / 1.4 共用）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 流程实例的编号 |
| name | String | 流程名称 |
| summary | List\<KeyValue\<String,String\>\> | 流程摘要（仅流程表单有） |
| category / categoryName | String | 流程分类编码 / 名称 |
| status | Integer | 流程实例状态（BpmProcessInstanceStatusEnum） |
| startTime / endTime | LocalDateTime | 发起时间 / 结束时间 |
| durationInMillis | Long | 持续时间（毫秒） |
| formVariables | Map\<String,Object\> | 提交的表单值 |
| businessKey | String | 业务的唯一标识（如请假申请编号） |
| startUser | UserSimpleBaseVO | 发起流程的用户 |
| processDefinitionId | String | 流程定义的编号 |
| processDefinition | BpmProcessDefinitionRespVO | 流程定义信息 |
| tasks | List\<Task\> | 当前审批中的任务（仅分页接口返回），Task 含 id、name、assigneeUser |

### 1.1 获得我的流程实例分页

- **路径**: GET /bpm/process-instance/my-page
- **权限**: bpm:process-instance:query
- **说明**: 【我的流程】菜单，分页查询当前登录用户发起的流程实例。

**请求参数 (BpmProcessInstancePageReqVO)**: 见上方公共 VO（startUserId 不生效，固定按当前登录用户过滤）。

**响应**: CommonResult\<PageResult\<BpmProcessInstanceRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 按当前登录用户构建 Flowable 历史流程实例查询（含流程变量、租户过滤、按发起时间倒序），叠加名称/Key/状态/分类/创建时间/结束时间/动态表单字段等条件分页查询。
2. 批量查询各实例当前运行中的任务 Map。
3. 批量查询流程定义 Map，并级联查询流程分类 Map、流程定义扩展信息 Map。
4. 收集发起人与运行任务审批人的用户编号，批量查询用户与部门信息。
5. 通过 BpmProcessInstanceConvert.buildProcessInstancePage 拼接分页结果返回。

### 1.2 获得管理流程实例的分页列表

- **路径**: GET /bpm/process-instance/manager-page
- **权限**: bpm:process-instance:manager-query
- **说明**: 【流程实例】管理菜单，分页查询全部用户的流程实例。

**请求参数 (BpmProcessInstancePageReqVO)**: 见上方公共 VO（此时 startUserId 生效，可按发起人过滤）。

**响应**: CommonResult\<PageResult\<BpmProcessInstanceRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 不限制发起人分页查询历史流程实例，查询条件同 1.1。
2. 查询运行任务、流程定义、分类、扩展信息 Map。
3. 按发起人批量查询用户与部门信息。
4. 拼接分页结果返回。

### 1.3 新建流程实例

- **路径**: POST /bpm/process-instance/create
- **权限**: bpm:process-instance:query
- **说明**: 发起流程，返回流程实例编号。

**请求参数 (BpmProcessInstanceCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| processDefinitionId | String | 是 | @NotEmpty | 流程定义的编号 |
| variables | Map\<String,Object\> | 否 | 无 | 变量实例（动态表单） |
| startUserSelectAssignees | Map\<String,List\<Long\>\> | 否 | 无 | 发起人自选审批人 Map（taskKey → 用户编号列表） |

**响应**: CommonResult\<String\>（流程实例编号）。

**业务逻辑**:
1. 获取流程定义；校验动态表单必填字段（仅普通表单类型），缺失时抛 PROCESS_INSTANCE_START_FORM_FIELD_REQUIRED。
2. 校验流程定义存在（PROCESS_DEFINITION_NOT_EXISTS）且未挂起（PROCESS_DEFINITION_IS_SUSPENDED），扩展信息存在。
3. 校验当前用户有权限发起该流程（PROCESS_INSTANCE_START_USER_CAN_START）。
4. 预测流程走向，校验"发起人自选"审批人节点均已配置人选（PROCESS_INSTANCE_START_USER_SELECT_ASSIGNEES_NOT_CONFIG）且用户存在（PROCESS_INSTANCE_START_USER_SELECT_ASSIGNEES_NOT_EXISTS）。
5. 过滤系统级流程变量，写入发起人 ID、流程状态（审批中）、skipExpression 开关、自选审批人变量。
6. 若配置自定义流程 ID 规则则通过 Redis 生成实例 ID，按标题规则生成流程名称，启动流程实例并返回编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_003_002 | 流程定义不存在 |
| 1_009_003_003 | 流程定义处于挂起状态 |
| 1_009_004_003 | 任务({})的候选人未配置 |
| 1_009_004_004 | 任务({})的候选人({})不存在 |
| 1_009_004_005 | 发起流程失败，你没有权限发起该流程 |
| 1_009_004_009 | 发起流程失败，表单字段（{}）为必填项，不能为空 |

### 1.4 获得指定流程实例

- **路径**: GET /bpm/process-instance/get
- **权限**: bpm:process-instance:query
- **说明**: 【流程详细】界面，查询单个流程实例。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 id 为 String、必填、无校验注解、流程实例的编号（query 参数） |

**响应**: CommonResult\<BpmProcessInstanceRespVO\>，字段见公共 VO。

**业务逻辑**:
1. 查询历史流程实例（不存在返回 null）。
2. 查询流程定义及扩展信息。
3. 查询发起人用户及其部门。
4. 拼接 BpmProcessInstanceRespVO 返回。

### 1.5 用户取消流程实例

- **路径**: DELETE /bpm/process-instance/cancel-by-start-user
- **权限**: bpm:process-instance:cancel
- **说明**: 发起人取消自己发起的流程。

**请求参数 (BpmProcessInstanceCancelReqVO)**（1.5 / 1.6 共用）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 流程实例的编号 |
| reason | String | 是 | @NotEmpty | 取消原因 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验流程实例处于运行中，否则抛 PROCESS_INSTANCE_CANCEL_FAIL_NOT_EXISTS。
2. 校验是本人发起的流程，否则抛 PROCESS_INSTANCE_CANCEL_FAIL_NOT_SELF。
3. 校验流程定义允许撤销审批中的申请（allowCancelRunningProcess），否则抛 PROCESS_INSTANCE_CANCEL_FAIL_NOT_ALLOW。
4. 校验不是子流程（superExecutionId 为空），否则抛 PROCESS_INSTANCE_CANCEL_CHILD_FAIL_NOT_ALLOW。
5. 更新流程实例状态为已取消并记录原因，递归取消所有子流程，最后将运行任务移动到 EndEvent 结束流程。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_004_001 | 流程取消失败，流程不处于运行中 |
| 1_009_004_002 | 流程取消失败，该流程不是你发起的 |
| 1_009_004_005 | 流程取消失败，该流程不允许取消 |
| 1_009_004_008 | 子流程取消失败，子流程不允许取消 |

### 1.6 管理员取消流程实例

- **路径**: DELETE /bpm/process-instance/cancel-by-admin
- **权限**: bpm:process-instance:cancel-by-admin
- **说明**: 管理员撤回任意运行中的流程。

**请求参数 (BpmProcessInstanceCancelReqVO)**: 同 1.5。

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验流程实例处于运行中，否则抛 PROCESS_INSTANCE_CANCEL_FAIL_NOT_EXISTS。
2. 以"管理员昵称 + 取消原因"更新流程状态为已取消。
3. 递归取消所有子流程并结束流程（同 1.5 第 5 步）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_004_001 | 流程取消失败，流程不处于运行中 |

### 1.7 获得审批详情

- **路径**: GET /bpm/process-instance/get-approval-detail
- **权限**: bpm:process-instance:query
- **说明**: 流程发起与详情页核心接口，返回节点审批进度、待办任务、表单权限及未来节点预测。

**请求参数 (BpmApprovalDetailReqVO)**（1.7 / 1.8 共用）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| processDefinitionId | String | 否 | 无 | 流程定义的编号（发起流程时使用） |
| processVariables | Map\<String,Object\> | 否 | 无 | 流程变量（用于流程预测） |
| processVariablesStr | String | 否 | 无 | 流程变量字符串（GET 传参兼容，最终转 processVariables） |
| processInstanceId | String | 否 | 无 | 流程实例的编号（流程已发起时使用） |
| activityId | String | 否 | 无 | 流程活动编号（用于获取表单权限） |
| taskId | String | 否 | 无 | 流程任务编号（用于获取表单权限） |

> 类级校验：@AssertTrue 校验 processDefinitionId 与 processInstanceId 不能同时为空。

**响应**: CommonResult\<BpmApprovalDetailRespVO\>：

| 字段 | 类型 | 说明 |
|------|------|------|
| status | Integer | 流程实例的状态 |
| activityNodes | List\<ActivityNode\> | 活动节点列表 |
| formFieldsPermission | Map\<String,String\> | 表单字段权限 |
| todoTask | BpmTaskRespVO | 当前用户待办任务 |
| processDefinition | BpmProcessDefinitionRespVO | 所属流程定义 |
| processInstance | BpmProcessInstanceRespVO | 所属流程实例 |

ActivityNode：id、name、nodeType（BpmSimpleModelNodeType）、status（BpmTaskStatusEnum）、startTime/endTime、tasks（List\<ActivityNodeTask\>）、candidateStrategy（候选人策略）、candidateUsers（候选人用户列表）、processInstanceId（仅子流程节点有值）。ActivityNodeTask：id、ownerUser、assigneeUser、status、reason、signPicUrl、attachments。

**业务逻辑**:
1. 已发起场景校验流程实例存在（PROCESS_INSTANCE_NOT_EXISTS），合并 DB 与前端传递的流程变量（前端优先）；未发起场景注入发起人变量。
2. 加载流程定义、扩展信息与 BpmnModel。
3. 已发起时计算【已结束】活动节点（含任务附件、StartEvent/EndEvent/CallActivity 特殊处理）与【进行中】活动节点（含加签子任务、依次审批后续候选人预测）。
4. 流程已结束则直接拼接返回，不再预测。
5. 计算当前登录用户的待办任务 todoTask；读取退回操作写入的"需预测节点"流程变量。
6. 预测未来节点：BPMN 设计器走 BpmnModelUtils.simulateProcess，SIMPLE 设计器走 SimpleModelUtils.simulateProcess，为审批节点计算候选人。
7. 拼接用户/部门信息与表单字段权限后返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_004_000 | 流程实例不存在 |

### 1.8 获取下一个执行的流程节点

- **路径**: GET /bpm/process-instance/get-next-approval-nodes
- **权限**: bpm:process-instance:query
- **说明**: 审批时预览下一个节点的审批人（用于"审批人自选"场景）。

**请求参数 (BpmApprovalDetailReqVO)**: 同 1.7（主要使用 taskId 与 processVariables）。

**响应**: CommonResult\<List\<BpmApprovalDetailRespVO.ActivityNode\>\>。

**业务逻辑**:
1. 校验任务存在且属于当前用户（TASK_NOT_EXISTS / TASK_OPERATE_FAIL_ASSIGN_NOT_SELF）。
2. 校验运行中与历史流程实例存在（PROCESS_INSTANCE_NOT_EXISTS），校验 BpmnModel 存在。
3. 合并历史流程变量与前端传递的流程变量（前端优先）。
4. 基于当前任务节点解析下一个 UserTask 集合，逐节点解析候选人策略并计算候选人用户列表。
5. 批量查询用户与部门信息，拼接 candidateUsers 返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_004_000 | 流程实例不存在 |

### 1.9 获取流程实例的 BPMN 模型视图

- **路径**: GET /bpm/process-instance/get-bpmn-model-view
- **权限**: bpm:process-instance:query
- **说明**: 【流程详细】界面，返回 BPMN 模型及各节点审批进度高亮信息。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 id 为 String、必填、无校验注解、流程实例的编号（query 参数） |

**响应**: CommonResult\<BpmProcessInstanceBpmnModelViewRespVO\>：

| 字段 | 类型 | 说明 |
|------|------|------|
| processInstance | BpmProcessInstanceRespVO | 流程实例信息 |
| tasks | List\<BpmTaskRespVO\> | 任务列表 |
| bpmnXml | String | BPMN XML |
| simpleModel | BpmSimpleModelNodeVO | SIMPLE 设计器模型 |
| unfinishedTaskActivityIds | Set\<String\> | 进行中的活动节点编号（仅 UserTask） |
| finishedTaskActivityIds | Set\<String\> | 已完成的活动节点编号（UserTask、Gateway 等） |
| finishedSequenceFlowActivityIds | Set\<String\> | 已完成的连线编号（仅 SequenceFlow） |
| rejectedTaskActivityIds | Set\<String\> | 已拒绝的活动节点编号（仅 UserTask） |

**业务逻辑**:
1. 查询历史流程实例与 BpmnModel（任一不存在返回 null）。
2. SIMPLE 模型类型时解析扩展信息中的 simpleModel JSON。
3. 查询活动实例与任务列表，计算进行中 / 已完成 / 已完成连线节点编号集合（会签场景从已完成集合移除进行中节点）。
4. 流程被拒绝时取最后一个被拒绝任务的活动编号加入 rejectedTaskActivityIds，并从已完成集合移除。
5. 拼接发起人/审批人用户与部门信息返回。

### 1.10 获得流程实例的打印数据

- **路径**: GET /bpm/process-instance/get-print-data
- **权限**: bpm:process-instance:query
- **说明**: 流程实例打印视图数据。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 processInstanceId 为 String、必填、无校验注解、流程实例的编号（query 参数） |

**响应**: CommonResult\<BpmProcessPrintDataRespVO\>：

| 字段 | 类型 | 说明 |
|------|------|------|
| processInstance | BpmProcessInstanceRespVO | 流程实例数据 |
| printTemplateEnable | Boolean | 是否开启自定义打印模板 |
| printTemplateHtml | String | 自定义打印模板 HTML |
| tasks | List\<Task\> | 审批任务列表（id、name、signPicUrl 签名 URL、description 任务描述） |

**业务逻辑**:
1. 校验流程实例存在，否则抛 PROCESS_INSTANCE_NOT_EXISTS。
2. 查询发起人用户及部门信息。
3. 查询该实例已完成且非取消状态的任务列表。
4. 批量查询任务审批人用户信息。
5. 拼接打印模板开关、模板 HTML 与审批任务列表（含签名 URL 与描述）返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_004_000 | 流程实例不存在 |

---

## 二、流程任务（BpmTaskController）

公共请求 VO **BpmTaskPageReqVO**（继承 PageParam，2.1 / 2.2 / 2.3 共用）：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| name | String | 否 | 无 | 流程任务名（模糊匹配） |
| category | String | 否 | 无 | 流程分类 |
| processDefinitionKey | String | 否 | 无 | 流程定义的标识（精准匹配） |
| status | Integer | 否 | @InEnum(BpmTaskStatusEnum) | 审批状态（仅【已办】使用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

公共响应 VO **BpmTaskRespVO**（2.1 ~ 2.4、2.7、2.15 共用）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 任务编号 |
| name | String | 任务名字 |
| createTime / endTime | LocalDateTime | 创建时间 / 结束时间 |
| durationInMillis | Long | 持续时间（毫秒） |
| status | Integer | 任务状态（BpmTaskStatusEnum） |
| reason | String | 审批理由 |
| signPicUrl | String | 签名 |
| attachments | List\<String\> | 附件 URL 列表 |
| ownerUser / assigneeUser | UserSimpleBaseVO | 负责人 / 审批人用户信息 |
| taskDefinitionKey | String | 任务定义的标识 |
| processInstanceId | String | 所属流程实例编号 |
| processInstance | ProcessInstance | 所属流程实例（id、name、createTime、processDefinitionId、summary、startUser） |
| parentTaskId | String | 父任务编号 |
| children | List\<BpmTaskRespVO\> | 子任务列表（由加签生成，多层） |
| formId / formName / formConf / formFields | Long / String / String / List\<String\> | 表单编号、名字、配置、项数组 |
| formVariables | Map\<String,Object\> | 提交的表单值 |
| buttonsSetting | Map\<Integer,OperationButtonSetting\> | 操作按钮设置（displayName、enable） |
| signEnable | Boolean | 是否需要签名 |
| reasonRequire | Boolean | 是否必须填写审批意见 |
| nodeType | Integer | 节点类型（BpmSimpleModelNodeTypeEnum） |

### 2.1 获取 Todo 待办任务分页

- **路径**: GET /bpm/task/todo-page
- **权限**: bpm:task:query
- **说明**: 【待办任务】菜单，查询当前用户待审批任务。

**请求参数 (BpmTaskPageReqVO)**: 见上方公共 VO。

**响应**: CommonResult\<PageResult\<BpmTaskRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 以当前用户为审批人查询 Flowable 活动任务（active、含流程变量、租户过滤、创建时间倒序），叠加名称模糊/分类/流程定义 Key/创建时间条件分页查询。
2. 批量查询任务所属流程实例及发起人用户信息。
3. 批量查询流程定义扩展信息。
4. 拼接待办任务分页返回。

### 2.2 获取 Done 已办任务分页

- **路径**: GET /bpm/task/done-page
- **权限**: bpm:task:query
- **说明**: 【已办任务】菜单，查询当前用户已审批任务。

**请求参数 (BpmTaskPageReqVO)**: 见上方公共 VO。

**响应**: CommonResult\<PageResult\<BpmTaskRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 查询当前用户已完成（finished）的历史任务，按结束时间倒序，支持按审批状态过滤。
2. 内存过滤：强制移除自动完成的"发起人"节点；按创建时间区间过滤（规避 Flowable taskCreatedAfter/Before 拼接 OR 的 bug）。
3. 批量查询流程实例、发起人用户、流程定义扩展信息。
4. 查询任务附件（TASK_ATTACHMENT 类型）并按任务分组。
5. 拼接已办任务分页返回。

### 2.3 获取全部任务的分页

- **路径**: GET /bpm/task/manager-page
- **权限**: bpm:task:manager-query
- **说明**: 【流程任务】管理菜单，查询全部用户的历史任务。

**请求参数 (BpmTaskPageReqVO)**: 见上方公共 VO。

**响应**: CommonResult\<PageResult\<BpmTaskRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 查询全部历史任务（不限制用户与完成状态），按结束时间倒序，叠加名称/分类/创建时间条件分页查询。
2. 批量查询流程实例，并收集发起人与任务审批人用户编号。
3. 批量查询用户与部门信息、流程定义扩展信息。
4. 查询任务附件并按任务分组。
5. 拼接任务分页返回。

### 2.4 获得指定流程实例的任务列表

- **路径**: GET /bpm/task/list-by-process-instance-id
- **权限**: bpm:task:query
- **说明**: 流程详情页审批记录，含已完成与未完成任务。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 processInstanceId 为 String、必填、无校验注解、流程实例的编号（query 参数） |

**响应**: CommonResult\<List\<BpmTaskRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 查询该流程实例全部历史任务（按开始时间升序）。
2. 收集审批人（assignee）与负责人（owner）用户编号，批量查询用户与部门信息。
3. 按任务 formKey 批量查询表单信息。
4. 查询任务附件并按任务分组。
5. 拼接任务列表返回。

### 2.5 通过任务

- **路径**: PUT /bpm/task/approve
- **权限**: bpm:task:update
- **说明**: 审批通过任务，推进流程到下一节点。

**请求参数 (BpmTaskApproveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 任务编号 |
| reason | String | 否 | 无 | 审批意见 |
| signPicUrl | String | 否 | 无 | 签名图片 URL |
| attachments | List\<String\> | 否 | 无 | 附件 URL 列表 |
| variables | Map\<String,Object\> | 否 | 无 | 变量实例（动态表单） |
| nextAssignees | Map\<String,List\<Long\>\> | 否 | 无 | 下一个节点审批人 Map（节点支持多个，如并行网关） |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务属于当前用户、流程实例存在；按节点配置校验签名必填（TASK_SIGNATURE_NOT_EXISTS）与审批意见必填（TASK_REASON_REQUIRE）。
2. 被委派任务（DelegationState.PENDING）：添加委派完成评论，resolveTask 归还原审批人继续审批。
3. 后加签任务：更新为审批中（APPROVING）中间状态，激活全部子任务（resolveTask + RUNNING）。
4. 普通任务：更新任务状态为通过并记录理由、签名，添加审批评论与附件。
5. 合并历史与前端流程变量（前端优先）；校验并设置下一节点"发起人自选 / 审批人自选"的审批人，漏选抛 PROCESS_INSTANCE_START_USER_SELECT_ASSIGNEES_NOT_CONFIG / PROCESS_INSTANCE_APPROVE_USER_SELECT_ASSIGNEES_NOT_CONFIG。
6. 清理回退预测节点变量与退回标记变量。
7. 调用 Flowable complete 完成任务；若父任务为加签任务且子任务全部处理完，递归处理父任务（前加签重新激活、后加签自动完成）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_015 | 签名不能为空！ |
| 1_009_005_016 | 审批意见不能为空！ |
| 1_009_004_000 | 流程实例不存在 |
| 1_009_004_003 | 任务({})的候选人未配置 |
| 1_009_004_007 | 下一个任务({})的审批人未配置 |

### 2.6 不通过任务

- **路径**: PUT /bpm/task/reject
- **权限**: bpm:task:update
- **说明**: 审批不通过，按节点驳回策略退回指定节点或结束流程。

**请求参数 (BpmTaskRejectReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 任务编号 |
| reason | String | 是（Schema 标记） | 无 | 审批意见 |
| attachments | List\<String\> | 否 | 无 | 附件 URL 列表 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务属于当前用户、流程实例存在。
2. 更新任务状态为不通过并记录理由，添加驳回评论与附件。
3. 若任务由加签生成，递归找到根父任务并同步标记为不通过并添加评论。
4. 按节点驳回处理策略：配置"驳回到指定节点"（RETURN_USER_TASK）时，调用退回逻辑驳回到配置节点。
5. 否则标记流程实例为不通过、记录原因，并 moveTaskToEnd 结束流程。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_004_000 | 流程实例不存在 |

### 2.7 获取所有可退回的节点

- **路径**: GET /bpm/task/list-by-return
- **权限**: bpm:task:update
- **说明**: 【流程详情】的【退回】按钮，列出可退回的目标节点。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 id 为 String、必填、无校验注解、当前任务编号（query 参数） |

**响应**: CommonResult\<List\<BpmTaskRespVO\>\>（仅返回 name、taskDefinitionKey 两个字段）。

**业务逻辑**:
1. 校验当前任务存在（TASK_NOT_EXISTS）。
2. 加载 BpmnModel，解析当前节点的前置 UserTask 列表。
3. 过滤：仅串行可到达的节点可退回（非串行、子流程不可退回）。
4. 过滤：仅保留已经处理过的节点（排除审批未经过的节点）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_002 | 流程任务不存在 |

### 2.8 退回任务

- **路径**: PUT /bpm/task/return
- **权限**: bpm:task:update
- **说明**: 【流程详情】的【退回】按钮，将流程退回到指定历史节点。

**请求参数 (BpmTaskReturnReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 任务编号 |
| targetTaskDefinitionKey | String | 是 | @NotEmpty | 退回到的任务 Key |
| reason | String | 是 | @NotEmpty | 退回意见 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务属于当前用户且未挂起（TASK_IS_PENDING）。
2. 校验目标节点存在（TASK_TARGET_NODE_NOT_EXISTS）、与当前节点串行可达（TASK_RETURN_FAIL_SOURCE_TARGET_ERROR）。
3. 计算需回撤的任务节点：本人任务标记 RETURN 状态并添加评论，他人任务标记取消。
4. 计算需要预测的节点 Key 集合（当前节点 + 目标节点之后串行可达的已结束节点）。
5. 调用 Flowable changeActivityState 移动到目标节点，并写入"需预测节点"与"退回标记"流程变量（防止发起人节点自动通过策略误触发）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_003 | 当前任务处于挂起状态，不能操作 |
| 1_009_005_004 | 目标节点不存在 |
| 1_009_005_006 | 退回任务失败，目标节点是在并行网关上或非同一路线上，不可跳转 |

### 2.9 委派任务

- **路径**: PUT /bpm/task/delegate
- **权限**: bpm:task:update
- **说明**: 【流程详情】的【委派】按钮，将任务临时委派给他人，对方审批后回到当前用户。

**请求参数 (BpmTaskDelegateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 任务编号 |
| delegateUserId | Long | 是 | @NotNull | 被委派人 ID |
| reason | String | 是 | @NotEmpty | 委派原因 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务属于当前用户；校验被委派人与当前审批人不是同一人（TASK_DELEGATE_FAIL_USER_REPEAT）。
2. 校验被委派人存在（TASK_DELEGATE_FAIL_USER_NOT_EXISTS）。
3. 添加委派开始（DELEGATE_START）评论。
4. owner 为空时设置 owner 为原审批人；调用 Flowable delegateTask 委派任务（委派状态通过 DelegationState.PENDING 标识，不单独记录状态变量）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_007 | 任务委派失败，委派人和当前审批人为同一人 |
| 1_009_005_008 | 任务委派失败，被委派人不存在 |

### 2.10 转派任务

- **路径**: PUT /bpm/task/transfer
- **权限**: bpm:task:update
- **说明**: 【流程详情】的【转派】按钮，将任务直接转给新审批人。

**请求参数 (BpmTaskTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 任务编号 |
| assigneeUserId | Long | 是 | @NotNull | 新审批人的用户编号 |
| reason | String | 是 | @NotEmpty | 转办原因 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务属于当前用户；校验转办人与当前审批人不是同一人（TASK_TRANSFER_FAIL_USER_REPEAT）。
2. 校验转办人存在（TASK_TRANSFER_FAIL_USER_NOT_EXISTS）。
3. 添加转办（TRANSFER）评论。
4. owner 为空时设置 owner 为原审批人；调用 setAssignee 直接变更审批人（与委派的差别所在）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_013 | 任务转办失败，转办人和当前审批人为同一人 |
| 1_009_005_014 | 任务转办失败，转办人不存在 |

### 2.11 加签

- **路径**: PUT /bpm/task/create-sign
- **权限**: bpm:task:update
- **说明**: 当前任务增加临时审批人，before 前加签 / after 后加签。

**请求参数 (BpmTaskSignCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 需要加签的任务编号 |
| userIds | Set\<Long\> | 是 | @NotEmpty | 加签的用户编号集合 |
| type | String | 是 | @NotEmpty | 加签类型（before / after，BpmTaskSignTypeEnum） |
| reason | String | 是 | @NotEmpty | 加签原因 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务属于当前用户；校验前后加签类型不能混用（TASK_SIGN_CREATE_TYPE_ERROR）。
2. 校验加签用户与该节点现有审批人（含 owner）不重复（TASK_SIGN_CREATE_USER_REPEAT），且用户存在（TASK_SIGN_CREATE_USER_NOT_EXIST）。
3. 处理父任务：开启子任务计数；前加签时 owner=原审批人、清空 assignee 并置状态 WAIT；记录 scopeType 加签方式。
4. 为每个加签用户基于父任务创建子任务（前加签设 assignee、后加签设 owner；后加签子任务状态置 WAIT）。
5. 添加加签（ADD_SIGN）评论，记录加签人与原因。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_009 | 任务加签：选择的用户不存在 |
| 1_009_005_010 | 任务加签：当前任务已经{}，不能{} |
| 1_009_005_011 | 任务加签失败，加签人与现有审批人[{}]重复 |

### 2.12 减签

- **路径**: DELETE /bpm/task/delete-sign
- **权限**: bpm:task:update
- **说明**: 移除通过加签生成的任务。

**请求参数 (BpmTaskSignDeleteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 被减签的任务编号 |
| reason | String | 是 | @NotEmpty | 减签原因 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务存在且必须是通过加签生成的任务（有父任务且父任务 scopeType 为加签类型），否则抛 TASK_SIGN_DELETE_NO_PARENT。
2. 校验取消人存在（优先 assignee，其次 owner）。
3. 递归获取全部子任务，全部标记为已取消（CANCEL）并说明原因，然后删除任务及所有子任务。
4. 在父任务上记录减签（SUB_SIGN）评论（先记录再处理，避免父任务已被完成后报错）。
5. 处理父任务：前加签重新激活父任务、后加签在子任务全部处理完后自动完成父任务。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_012 | 任务减签失败，被减签的任务必须是通过加签生成的任务 |

### 2.13 抄送任务

- **路径**: PUT /bpm/task/copy
- **权限**: bpm:task:update
- **说明**: 手动将当前任务抄送给指定用户。

**请求参数 (BpmTaskCopyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | String | 是 | @NotEmpty | 任务编号 |
| copyUserIds | Collection\<Long\> | 是 | @NotEmpty | 抄送的用户编号数组 |
| reason | String | 否 | 无 | 抄送意见 |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验任务存在（TASK_NOT_EXISTS）。
2. 校验流程实例存在（PROCESS_INSTANCE_NOT_EXISTS）、流程定义存在（PROCESS_DEFINITION_NOT_EXISTS）。
3. 批量插入抄送记录（含抄送人、发起人、任务/活动信息、分类、意见）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_002 | 流程任务不存在 |
| 1_009_004_000 | 流程实例不存在 |
| 1_009_003_002 | 流程定义不存在 |

### 2.14 撤回任务

- **路径**: PUT /bpm/task/withdraw
- **权限**: bpm:task:update
- **说明**: 已办任务的发起节点撤回，拉回到本节点重新审批。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 taskId 为 String、必填、无校验注解、任务编号（query 参数） |

**响应**: CommonResult\<Boolean\>（固定 true）。

**业务逻辑**:
1. 校验本人已办（finished）任务存在，否则抛 TASK_WITHDRAW_FAIL_TASK_NOT_EXISTS。
2. 校验流程实例仍在运行中，否则抛 TASK_WITHDRAW_FAIL_PROCESS_NOT_RUNNING。
3. 校验流程定义允许撤回（allowWithdrawTask），否则抛 TASK_WITHDRAW_FAIL_NOT_ALLOW。
4. 校验下一节点存在且尚未被审批（按任务创建时间在本人任务结束之后统计），否则抛 TASK_WITHDRAW_FAIL_NEXT_TASK_NOT_ALLOW。
5. 校验下一节点存在运行中任务，否则抛 TASK_WITHDRAW_FAIL_NEXT_TASK_NOT_ALLOW。
6. 取消下一节点运行中任务（标记 CANCEL、添加"前一节点撤回"评论），通过 changeActivityState 将执行移回当前任务节点。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_009_005_017 | 撤回失败，流程实例未运行！ |
| 1_009_005_018 | 撤回失败，未查询到用户已办任务！ |
| 1_009_005_019 | 撤回失败，此流程不允许撤回操作！ |
| 1_009_005_020 | 撤回失败，下一节点不满足撤回条件！ |

### 2.15 获得指定父级任务的子任务列表

- **路径**: GET /bpm/task/list-by-parent-task-id
- **权限**: bpm:task:query
- **说明**: 减签时查看父任务加签产生的子任务列表。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 | 其中 parentTaskId 为 String、必填、无校验注解、父级任务编号（query 参数） |

**响应**: CommonResult\<List\<BpmTaskRespVO\>\>，字段见公共 VO。

**业务逻辑**:
1. 通过原生 SQL 查询 Flowable 任务表 PARENT_TASK_ID_ 匹配的子任务（TaskQuery 无 parentId 参数）。
2. 收集子任务 assignee 与 owner 用户编号，批量查询用户与部门信息。
3. 拼接子任务列表返回。

---

## 三、流程抄送（BpmProcessInstanceCopyController）

### 3.1 获得抄送流程分页列表

- **路径**: GET /bpm/process-instance/copy/page
- **权限**: bpm:process-instance-cc:query
- **说明**: 【抄送我的】菜单，分页查询当前用户的抄送记录。

**请求参数 (BpmProcessInstanceCopyPageReqVO)**（继承 PageParam）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| processInstanceName | String | 否 | 无 | 流程名称（模糊匹配） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<BpmProcessInstanceCopyRespVO\>\>：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 抄送主键 |
| startUser | UserSimpleBaseVO | 发起人 |
| processInstanceId | String | 流程实例编号 |
| processInstanceName | String | 流程实例的名称 |
| processInstanceStartTime | LocalDateTime | 流程实例的发起时间 |
| activityId / activityName | String | 流程活动的编号 / 名字 |
| taskId | String | 流程活动的编号（任务编号） |
| reason | String | 抄送人意见 |
| createUser | UserSimpleBaseVO | 创建人（执行抄送的人） |
| createTime | LocalDateTime | 抄送时间 |
| summary | List\<KeyValue\<String,String\>\> | 流程摘要 |

**业务逻辑**:
1. 分页查询当前用户的抄送记录（按流程名称、创建时间过滤）。
2. 批量查询对应流程实例历史信息。
3. 批量查询抄送人与发起人的用户信息、流程定义扩展信息。
4. 拼接 createUser / startUser 精简用户信息。
5. 按流程实例拼接流程摘要（FlowableUtils.getSummary）与流程实例发起时间。

---

## 错误码汇总（流程实例 1_009_004_xxx / 流程任务 1_009_005_xxx）

| 错误码 | 说明 |
|--------|------|
| 1_009_004_000 | 流程实例不存在 |
| 1_009_004_001 | 流程取消失败，流程不处于运行中 |
| 1_009_004_002 | 流程取消失败，该流程不是你发起的 |
| 1_009_004_003 | 任务({})的候选人未配置 |
| 1_009_004_004 | 任务({})的候选人({})不存在 |
| 1_009_004_005 | 发起流程失败，你没有权限发起该流程 |
| 1_009_004_005 | 流程取消失败，该流程不允许取消 |
| 1_009_004_006 | 流程 Http 请求调用失败 |
| 1_009_004_007 | 下一个任务({})的审批人未配置 |
| 1_009_004_008 | 子流程取消失败，子流程不允许取消 |
| 1_009_004_009 | 发起流程失败，表单字段（{}）为必填项，不能为空 |
| 1_009_005_001 | 操作失败，原因：该任务的审批人不是你 |
| 1_009_005_002 | 流程任务不存在 |
| 1_009_005_003 | 当前任务处于挂起状态，不能操作 |
| 1_009_005_004 | 目标节点不存在 |
| 1_009_005_006 | 退回任务失败，目标节点是在并行网关上或非同一路线上，不可跳转 |
| 1_009_005_007 | 任务委派失败，委派人和当前审批人为同一人 |
| 1_009_005_008 | 任务委派失败，被委派人不存在 |
| 1_009_005_009 | 任务加签：选择的用户不存在 |
| 1_009_005_010 | 任务加签：当前任务已经{}，不能{} |
| 1_009_005_011 | 任务加签失败，加签人与现有审批人[{}]重复 |
| 1_009_005_012 | 任务减签失败，被减签的任务必须是通过加签生成的任务 |
| 1_009_005_013 | 任务转办失败，转办人和当前审批人为同一人 |
| 1_009_005_014 | 任务转办失败，转办人不存在 |
| 1_009_005_015 | 签名不能为空！ |
| 1_009_005_016 | 审批意见不能为空！ |
| 1_009_005_017 | 撤回失败，流程实例未运行！ |
| 1_009_005_018 | 撤回失败，未查询到用户已办任务！ |
| 1_009_005_019 | 撤回失败，此流程不允许撤回操作！ |
| 1_009_005_020 | 撤回失败，下一节点不满足撤回条件！ |
