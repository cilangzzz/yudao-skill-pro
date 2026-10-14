# 流程定义接口（BpmModelController / BpmProcessDefinitionController / BpmCategoryController / BpmFormController / BpmUserGroupController / BpmProcessExpressionController / BpmProcessListenerController）

> BPM 流程定义域的管理端接口：覆盖流程模型（含仿钉钉精简设计器）的增删改查、导入导出与部署，流程定义的查询与挂起状态管理，以及流程分类、动态表单、用户组、流程表达式、流程监听器等流程配置数据的完整维护。

## 接口路径前缀

- `/bpm/model`（Controller: BpmModelController）
- `/bpm/process-definition`（Controller: BpmProcessDefinitionController）
- `/bpm/category`（Controller: BpmCategoryController）
- `/bpm/form`（Controller: BpmFormController）
- `/bpm/user-group`（Controller: BpmUserGroupController）
- `/bpm/process-expression`（Controller: BpmProcessExpressionController）
- `/bpm/process-listener`（Controller: BpmProcessListenerController）

---

## 1. 流程模型（BpmModelController）

### 1.1 获得模型列表

- **路径**: GET /bpm/model/list
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 按名称模糊查询当前租户的流程模型列表，并关联返回表单、分类、最新部署的流程定义、可发起用户/部门等信息

**请求参数**: 无（可选 query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | 无 | 模型名称，模糊匹配 |

**响应**: CommonResult<List<BpmModelRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | String | 模型编号 |
| key | String | 流程标识 |
| name | String | 流程名称 |
| icon | String | 流程图标 |
| category | String | 流程分类编码 |
| categoryName | String | 流程分类名字 |
| formName | String | 表单名字 |
| createTime | LocalDateTime | 创建时间 |
| startUsers | List\<UserSimpleBaseVO\> | 可发起的用户数组（id/nickname/avatar/deptId/deptName） |
| startDepts | List\<DeptSimpleBaseVO\> | 可发起的部门数组（id/name） |
| bpmnXml | String | BPMN XML |
| simpleModel | BpmSimpleModelNodeVO | 仿钉钉流程设计模型对象 |
| processDefinition | BpmProcessDefinitionRespVO | 最新部署的流程定义 |
| （继承 BpmModelMetaInfoVO） | - | description、type、formType、formId、formCustomCreatePath、formCustomViewPath、visible、startUserIds、startDeptIds、managerUserIds、sort、allowCancelRunningProcess、allowWithdrawTask、processIdRule、autoApprovalType、titleSetting、summarySetting、processBeforeTriggerSetting、processAfterTriggerSetting、taskBeforeTriggerSetting、taskAfterTriggerSetting、printTemplateSetting |

**业务逻辑**:
1. 构建模型查询：name 非空时按名称模糊匹配，并限定当前租户
2. 模型列表为空则直接返回空列表
3. 解析各模型 metaInfo，收集 formIds 查询表单 Map，收集 category 查询分类 Map
4. 根据 deploymentId 查询部署 Map 及其对应的流程定义 Map
5. 收集 startUserIds、startDeptIds，分别调用 AdminUserApi、DeptApi 查询用户、部门 Map
6. 通过 BpmModelConvert.buildModelList 组装 BpmModelRespVO 列表返回

### 1.2 获得模型

- **路径**: GET /bpm/model/get
- **权限**: bpm:model:query
- **说明**: 获得单个流程模型详情，含 BPMN XML 与仿钉钉设计模型

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | 无 | 模型编号 |

**响应**: CommonResult<BpmModelRespVO>（字段同 1.1）

**业务逻辑**:
1. 按租户过滤查询 Model，不存在时返回 null
2. 读取模型的 BPMN XML（模型编辑器源）
3. 读取仿钉钉设计器 JSON 并反序列化为 BpmSimpleModelNodeVO
4. buildModel 组装 BpmModelRespVO 返回

### 1.3 导出模型

- **路径**: GET /bpm/model/export
- **权限**: bpm:model:export
- **说明**: 导出模型为可保存/导入的 JSON 结构

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | 无 | 模型编号 |

**响应**: CommonResult<BpmModelSaveReqVO>（字段同 1.4 请求参数）

**业务逻辑**:
1. 校验模型存在（按租户过滤），不存在抛 MODEL_NOT_EXISTS
2. 将 Model 转换为 BpmModelSaveReqVO
3. 类型为 BPMN 设计器时，读取 BPMN XML 填入 bpmnXml 字段
4. 类型为 SIMPLE 设计器时，读取 JSON 反序列化填入 simpleModel 字段

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |

### 1.4 新建模型

- **路径**: POST /bpm/model/create
- **权限**: bpm:model:create
- **说明**: 新建流程模型（BPMN 或仿钉钉设计器）

**请求参数 (BpmModelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 否 | 无 | 编号（更新时传入） |
| key | String | 是 | @NotEmpty | 流程标识，需为合法 XML NCName |
| name | String | 是 | @NotEmpty | 流程名称 |
| category | String | 否 | 无 | 流程分类 |
| bpmnXml | String | 否 | 无 | BPMN XML |
| simpleModel | BpmSimpleModelNodeVO | 否 | @Valid | 仿钉钉流程设计模型对象 |
| icon | String | 否 | @URL | 流程图标 |
| description | String | 否 | 无 | 流程描述 |
| type | Integer | 是 | @NotNull、@InEnum(BpmModelTypeEnum) | 流程类型（10=BPMN 设计器、20=仿钉钉 SIMPLE 设计器） |
| formType | Integer | 是 | @NotNull、@InEnum(BpmModelFormTypeEnum) | 表单类型（10=流程表单、20=自定义表单） |
| formId | Long | 条件必填 | 无 | 表单编号，formType 为 NORMAL 时必须非空 |
| formCustomCreatePath | String | 条件必填 | 无 | 自定义表单的提交路径（Vue 路由地址），formType 为 CUSTOM 时必须非空 |
| formCustomViewPath | String | 条件必填 | 无 | 自定义表单的查看路径（Vue 路由地址），formType 为 CUSTOM 时必须非空 |
| visible | Boolean | 是 | @NotNull | 是否可见 |
| startUserIds | List\<Long\> | 否 | 无 | 可发起用户编号数组 |
| startDeptIds | List\<Long\> | 否 | 无 | 可发起部门编号数组 |
| managerUserIds | List\<Long\> | 是 | @NotEmpty | 可管理用户编号数组 |
| sort | Long | 否 | 无 | 排序（后端自动以时间戳生成） |
| allowCancelRunningProcess | Boolean | 否 | 无 | 允许撤销审批中的申请 |
| allowWithdrawTask | Boolean | 否 | 无 | 允许审批人撤回任务 |
| processIdRule | ProcessIdRule | 否 | @Valid | 流程 ID 规则（enable/prefix/infix/postfix/length） |
| autoApprovalType | Integer | 否 | @InEnum(BpmAutoApproveTypeEnum) | 自动去重类型 |
| titleSetting | TitleSetting | 否 | @Valid | 标题设置（enable/title） |
| summarySetting | SummarySetting | 否 | 无 | 摘要设置（enable/summary） |
| processBeforeTriggerSetting | HttpRequestSetting | 否 | 无 | 流程前置通知设置（url/header/body/response） |
| processAfterTriggerSetting | HttpRequestSetting | 否 | 无 | 流程后置通知设置 |
| taskBeforeTriggerSetting | HttpRequestSetting | 否 | 无 | 任务前置通知设置 |
| taskAfterTriggerSetting | HttpRequestSetting | 否 | 无 | 任务后置通知设置 |
| printTemplateSetting | PrintTemplateSetting | 否 | @Valid | 自定义打印模板设置（enable/template） |

**响应**: CommonResult\<String\>（返回新建模型编号）

**业务逻辑**:
1. 校验 key 是合法的 XML NCName 格式，否则抛 MODEL_KEY_VALID
2. 校验当前租户下相同流程标识的模型不存在，否则抛 MODEL_KEY_EXISTS
3. 以当前时间戳作为 sort，创建 Flowable Model 并拷贝 metaInfo 属性，设置租户
4. 保存模型基础信息
5. 类型为 BPMN 且 bpmnXml 非空时保存 BPMN XML；类型为 SIMPLE 且 simpleModel 非空时，将 JSON 转换为 BpmnModel，分别保存 BPMN XML 与 JSON 数据

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_000 | 已经存在流程标识为【{}】的流程 |
| 1_009_002_002 | 流程标识格式不正确 |

### 1.5 导入模型

- **路径**: POST /bpm/model/import
- **权限**: bpm:model:import
- **说明**: 上传模型 JSON 文件导入为新模型，可用请求参数覆盖流程标识/名称

**请求参数**: 无（multipart/form-data 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| file | MultipartFile | 是 | 无 | 流程模型 JSON 文件（BpmModelSaveReqVO 结构） |
| key | String | 否 | 无 | 流程标识，非空时替换导入文件中的标识 |
| name | String | 否 | 无 | 流程名称，非空时替换导入文件中的名称 |

**响应**: CommonResult\<String\>（返回导入后模型编号）

**业务逻辑**:
1. 将上传文件解析为 BpmModelSaveReqVO，解析失败或内容为空抛 MODEL_IMPORT_FAIL_INVALID
2. 请求参数 key、name 非空时覆盖 VO 中的流程标识、流程名称
3. 通过 ValidationUtils.validate 对 VO 执行 JSR-303 校验
4. 与新建模型一致：校验 key 合法且在当前租户下唯一，以当前时间戳作为 sort 创建 Model
5. 保存模型基础信息与流程图（BPMN XML 或仿钉钉 JSON）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_009 | 导入流程失败，流程模型文件为空或 JSON 格式不正确 |
| 1_009_002_000 | 已经存在流程标识为【{}】的流程 |
| 1_009_002_002 | 流程标识格式不正确 |

### 1.6 修改模型

- **路径**: PUT /bpm/model/update
- **权限**: bpm:model:update
- **说明**: 修改流程模型的基本信息与流程图，仅模型管理员可操作

**请求参数 (BpmModelSaveReqVO)**: 字段同 1.4（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateModelManager：校验模型存在（租户过滤），且当前登录用户位于 metaInfo.managerUserIds 中，否则分别抛 MODEL_NOT_EXISTS / MODEL_UPDATE_FAIL_NOT_MANAGER
2. 将请求 VO 拷贝到 Model
3. 保存模型基础信息与流程图（BPMN XML，或仿钉钉 JSON 转换为 BpmnModel 后保存）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |

### 1.7 批量修改模型排序

- **路径**: PUT /bpm/model/update-sort-batch
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 按 ids 顺序批量调整模型与对应流程定义的排序

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List\<String\> | 是 | 无 | 模型编号数组，逗号分隔，顺序即排序顺序 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 查询当前租户全部模型并按 ids 过滤，数量与 ids 不一致时抛 MODEL_NOT_EXISTS
2. 逐个校验当前用户是模型管理员（validateModelManager）
3. 从列表末尾向前以递减时间戳更新各模型的 metaInfo.sort
4. 同步调用 updateProcessDefinitionSortByModelId 更新流程定义拓展表的 sort

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |

### 1.8 部署模型

- **路径**: POST /bpm/model/deploy
- **权限**: bpm:model:deploy
- **说明**: 将模型部署为新的流程定义，只有最新部署的流程定义可发起流程

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | 无 | 模型编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateModelManager 校验模型存在且当前用户是管理员，并解析 metaInfo
2. 读取 BPMN XML 并校验流程图：BpmnModel 解析非空；必须存在开始事件；所有 UserTask 的 name 非空；首个用户任务（BPMN 设计器取第 1 个，SIMPLE 设计器首个固定为发起人、取第 2 个）的审批人策略不能是“审批人自选”
3. validateFormConfig 校验表单配置：formType 为空、NORMAL 类型 formId 为空或表单不存在、CUSTOM 类型提交/查看路径为空时抛错
4. taskCandidateInvoker.validateBpmnConfig 校验所有用户任务已配置审批人
5. 读取仿钉钉 JSON，调用 createProcessDefinition：创建 Deployment（禁用 XML Schema 校验）、设置流程定义分类、校验 key/name 与模型一致、插入拓展表 BpmProcessDefinitionInfoDO（NORMAL 表单时冗余 formConf/formFields）
6. 将旧的流程定义挂起，保证仅最新部署的流程定义可发起
7. 更新 Model 的 deploymentId 并保存

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_003 | 部署流程失败，原因：流程表单未配置 |
| 1_009_002_004 | 部署流程失败，原因：用户任务({})未配置审批人 |
| 1_009_002_005 | 部署流程失败，原因：BPMN 流程图中，没有开始事件 |
| 1_009_002_006 | 部署流程失败，原因：BPMN 流程图中，用户任务({})的名字不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |
| 1_009_002_008 | 部署流程失败，原因：首个任务({})的审批人不能是【审批人自选】 |
| 1_009_010_000 | 动态表单不存在 |
| 1_009_003_000 | 流程定义的标识期望是({})，当前是({}) |
| 1_009_003_001 | 流程定义的名字期望是({})，当前是({}) |

### 1.9 修改模型的状态

- **路径**: PUT /bpm/model/update-state
- **权限**: bpm:model:update
- **说明**: 实际更新模型已部署流程定义的激活/挂起状态

**请求参数 (BpmModelUpdateStateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | @NotNull | 模型编号 |
| state | Integer | 是 | @NotNull | 状态，参见 Flowable SuspensionState 枚举（1=激活、2=挂起） |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateModelManager 校验模型存在且当前用户是管理员
2. 根据 model.deploymentId 查询流程定义，不存在抛 PROCESS_DEFINITION_NOT_EXISTS
3. state 为激活时，若流程定义处于挂起则激活（不挂起进行中的流程实例）
4. state 为挂起时，若流程定义处于激活则挂起（suspendProcessInstances=false，进行中的任务不挂起，仅禁止新发起）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |
| 1_009_003_002 | 流程定义不存在 |

### 1.10 修改模型的 BPMN（已废弃）

- **路径**: PUT /bpm/model/update-bpmn
- **权限**: bpm:model:update
- **说明**: 已废弃接口，直接覆盖模型的 BPMN XML

**请求参数 (BpmModeUpdateBpmnReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | @NotEmpty | 流程编号 |
| bpmnXml | String | 是 | @NotEmpty | BPMN XML |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. bpmnXml 非空时写入模型的编辑器源（addModelEditorSource）

### 1.11 删除模型

- **路径**: DELETE /bpm/model/delete
- **权限**: bpm:model:delete
- **说明**: 删除模型并挂起其已部署的流程定义

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | 无 | 模型编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateModelManager 校验模型存在且当前用户是管理员
2. 删除 Flowable Model
3. 挂起该模型 deploymentId 对应的旧流程定义

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |

### 1.12 清理模型

- **路径**: DELETE /bpm/model/clean
- **权限**: bpm:model:clean
- **说明**: 清理模型关联的所有流程实例、历史数据与任务

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | 无 | 模型编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateModelManager 校验模型存在且当前用户是管理员
2. 查询该流程 key 下全部运行中的流程实例，逐个删除运行实例、历史实例与流程抄送
3. 查询该 key 下全部历史流程实例，逐个删除历史实例与流程抄送
4. 查询该 key 下全部任务并逐个删除

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |

### 1.13 获得仿钉钉流程设计模型

- **路径**: GET /bpm/model/simple/get
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 获得仿钉钉/飞书精简设计器的模型节点树

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | 无 | 流程模型编号 |

**响应**: CommonResult<BpmSimpleModelNodeVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | String | 模型节点编号 |
| type | Integer | 模型节点类型（BpmSimpleModelNodeTypeEnum） |
| name | String | 模型节点名称 |
| showText | String | 节点展示内容 |
| childNode | BpmSimpleModelNodeVO | 子节点（有且仅有一个） |
| conditionNodes | List\<BpmSimpleModelNodeVO\> | 条件/并行/包容分支的分支节点列表 |
| candidateStrategy | Integer | 候选人策略（审批、抄送节点） |
| candidateParam | String | 候选人参数 |
| approveType | Integer | 审批节点类型 |
| approveMethod | Integer | 多人审批方式 |
| approveRatio | Integer | 通过比例 |
| fieldsPermission | List\<Map\<String,String\>\> | 表单权限 |
| buttonsSetting | List\<OperationButtonSetting\> | 操作按钮设置（id/displayName/enable） |
| signEnable | Boolean | 是否需要签名 |
| reasonRequire | Boolean | 是否填写审批意见 |
| skipExpression | String | 跳过表达式 |
| rejectHandler | RejectHandler | 拒绝处理（type/returnNodeId） |
| timeoutHandler | TimeoutHandler | 超时处理（enable/type/timeDuration/maxRemindCount） |
| assignStartUserHandlerType | Integer | 审批人与发起人相同时的处理类型 |
| assignEmptyHandler | AssignEmptyHandler | 空处理策略（type/userIds） |
| taskCreateListener / taskAssignListener / taskCompleteListener | ListenerHandler | 任务监听器（enable/path/header/body） |
| delaySetting | DelaySetting | 延迟器设置（delayType/delayTime） |
| conditionSetting | ConditionSetting | 条件节点设置（conditionType/conditionExpression/defaultFlow/conditionGroups） |
| routerGroups | List\<RouterSetting\> | 路由分支组（nodeId/conditionType/conditionExpression/conditionGroups） |
| triggerSetting | TriggerSetting | 触发器节点设置（type/httpRequestSetting/formSettings） |
| childProcessSetting | ChildProcessSetting | 子流程设置（calledProcessDefinitionKey/async/inVariables/outVariables/startUserSetting/timeoutSetting/multiInstanceSetting 等） |

**业务逻辑**:
1. 校验模型存在（按租户过滤）
2. 从 ACT_RE_MODEL 表的 EDITOR_SOURCE_EXTRA_VALUE_ID_ 字段读取仿钉钉模型 JSON
3. 反序列化为 BpmSimpleModelNodeVO 返回（未保存过则返回 null）

### 1.14 保存仿钉钉流程设计模型（已废弃）

- **路径**: POST /bpm/model/simple/update
- **权限**: bpm:model:update
- **说明**: 已废弃接口，由“修改模型”接口的 simpleModel 字段承担

**请求参数 (BpmSimpleModelUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | @NotEmpty | 流程模型编号（对应 act_re_model 表 ID_ 字段） |
| simpleModel | BpmSimpleModelNodeVO | 是 | @NotNull、@Valid | 仿钉钉流程设计模型对象 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateModelManager 校验模型存在且当前用户是管理员
2. 将仿钉钉 JSON 转换为 BpmnModel（SimpleModelUtils.buildBpmnModel）
3. 保存 BPMN XML 到模型
4. 保存 JSON 数据到模型

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_002_001 | 流程模型不存在 |
| 1_009_002_007 | 操作流程失败，原因：你不是该流程({})的管理员 |

---

## 2. 流程定义（BpmProcessDefinitionController）

### 2.1 获得流程定义分页

- **路径**: GET /bpm/process-definition/page
- **权限**: bpm:process-definition:query
- **说明**: 分页查询流程定义，附带分类、部署时间、表单等拓展信息

**请求参数 (BpmProcessDefinitionPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| key | String | 否 | 无 | 流程定义标识，精准匹配 |

**响应**: CommonResult<PageResult<BpmProcessDefinitionRespVO>>，BpmProcessDefinitionRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | String | 流程定义编号 |
| version | Integer | 版本 |
| name | String | 流程名称 |
| key | String | 流程标识 |
| category | String | 流程分类编码 |
| categoryName | String | 流程分类名字 |
| modelType | Integer | 流程模型的类型（BpmModelTypeEnum） |
| modelId | String | 流程模型的编号 |
| formConf | String | 表单配置 JSON（CUSTOM 表单类型时使用） |
| formFields | List\<String\> | 表单项数组（CUSTOM 表单类型时使用） |
| formName | String | 表单名字 |
| suspensionState | Integer | 中断状态（1=激活、2=挂起） |
| deploymentTime | LocalDateTime | 部署时间 |
| bpmnXml | String | BPMN XML |
| simpleModel | String | SIMPLE 设计器模型数据（JSON 格式） |
| sort | Long | 流程定义排序 |
| （继承 BpmModelMetaInfoVO） | - | icon、description、type、formType、formId、visible、startUserIds、startDeptIds、managerUserIds 等 |

**业务逻辑**:
1. 构建流程定义查询，限定当前租户，key 非空时精准匹配
2. 统计总数后按版本号倒序分页查询
3. 查询分类 Map、部署 Map（含部署时间）
4. 查询拓展表 BpmProcessDefinitionInfoDO Map 及关联的表单 Map
5. buildProcessDefinitionPage 组装分页结果返回

### 2.2 获得流程定义列表

- **路径**: GET /bpm/process-definition/list
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 按挂起状态查询流程定义，并过滤掉不可见、无权发起的定义

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| suspensionState | Integer | 是 | 无 | 挂起状态，参见 Flowable SuspensionState 枚举（1=激活、2=挂起） |

**响应**: CommonResult<List<BpmProcessDefinitionRespVO>>（字段同 2.1，不含 bpmnXml/simpleModel）

**业务逻辑**:
1. 按挂起状态查询当前租户的流程定义列表，为空返回空列表
2. 查询拓展表 BpmProcessDefinitionInfoDO Map
3. 过滤列表：拓展记录不存在、visible 为 false、或当前用户无发起权限（canUserStartProcessDefinition）的定义被移除
4. 发起权限规则：startUserIds 非空时用户须在列表中；否则 startDeptIds 非空时用户所在部门须在列表中；均为空则所有人可发起
5. buildProcessDefinitionList 组装返回

### 2.3 获得流程定义精简列表

- **路径**: GET /bpm/process-definition/simple-list
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 只包含未挂起的流程定义，主要用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult<List<BpmProcessDefinitionRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | String | 流程定义编号 |
| name | String | 流程名称 |
| key | String | 流程标识 |

**业务逻辑**:
1. 只查询激活（ACTIVE，未挂起）状态的当前租户流程定义
2. 仅返回 id、name、key 三个字段

### 2.4 获得流程定义

- **路径**: GET /bpm/process-definition/get
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 按 id 或 key 获得单个流程定义详情（含 BPMN XML）

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 与 key 二选一 | 无 | 流程定义编号，优先使用 |
| key | String | 与 id 二选一 | 无 | 流程定义标识，id 为空时按 key 查询 |

**响应**: CommonResult<BpmProcessDefinitionRespVO>（字段同 2.1，含 bpmnXml）

**业务逻辑**:
1. id 非空时按流程定义编号查询；否则按 key 查询当前租户下激活（未挂起）的流程定义
2. 查询不到时返回 null
3. 读取拓展表 BpmProcessDefinitionInfoDO 与 BpmnModel
4. buildProcessDefinition 组装返回（含 bpmnXml 等流程图信息）

---

## 3. 流程分类（BpmCategoryController）

### 3.1 创建流程分类

- **路径**: POST /bpm/category/create
- **权限**: bpm:category:create
- **说明**: 创建流程分类，校验名称与编码唯一

**请求参数 (BpmCategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 分类编号（更新时传入） |
| name | String | 是 | @NotEmpty | 分类名 |
| description | String | 否 | 无 | 分类描述 |
| code | String | 是 | @NotEmpty | 分类标志（编码） |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 分类状态（0=开启、1=禁用） |
| sort | Integer | 是 | @NotNull | 分类排序 |

**响应**: CommonResult\<Long\>（返回分类编号）

**业务逻辑**:
1. 校验分类名在库中唯一
2. 校验分类编码在库中唯一
3. 插入 BpmCategoryDO 并返回编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_012_001 | 流程分类名字【{}】重复 |
| 1_009_012_002 | 流程分类编码【{}】重复 |

### 3.2 更新流程分类

- **路径**: PUT /bpm/category/update
- **权限**: bpm:category:update
- **说明**: 更新流程分类，校验存在性与名称/编码唯一

**请求参数 (BpmCategorySaveReqVO)**: 字段同 3.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验分类存在
2. 校验分类名唯一
3. 校验分类编码唯一
4. 更新 BpmCategoryDO

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_012_000 | 流程分类不存在 |
| 1_009_012_001 | 流程分类名字【{}】重复 |
| 1_009_012_002 | 流程分类编码【{}】重复 |

### 3.3 批量更新流程分类的排序

- **路径**: PUT /bpm/category/update-sort-batch
- **权限**: bpm:category:update
- **说明**: 按 ids 顺序批量更新分类排序

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List\<Long\> | 是 | 无 | 分类编号列表，逗号分隔，顺序即排序顺序 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 批量查询分类，数量与 ids 不一致时抛 CATEGORY_NOT_EXISTS
2. 按 ids 顺序以数组下标作为 sort，批量更新

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_012_000 | 流程分类不存在 |

### 3.4 删除流程分类

- **路径**: DELETE /bpm/category/delete
- **权限**: bpm:category:delete
- **说明**: 删除分类，已被流程模型使用的分类不可删除

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 分类编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验分类存在
2. 通过 modelService.getModelCountByCategory 统计使用该分类编码的流程模型数量，大于 0 时抛错
3. 删除分类

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_012_000 | 流程分类不存在 |
| 1_009_012_003 | 删除失败，流程分类【{}】已被流程模型使用 |

### 3.5 获得流程分类

- **路径**: GET /bpm/category/get
- **权限**: bpm:category:query
- **说明**: 按编号获得单个流程分类

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 分类编号 |

**响应**: CommonResult<BpmCategoryRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| name | String | 分类名 |
| code | String | 分类标志 |
| description | String | 分类描述 |
| status | Integer | 分类状态 |
| sort | Integer | 分类排序 |
| createTime | LocalDateTime | 创建时间 |

### 3.6 获得流程分类分页

- **路径**: GET /bpm/category/page
- **权限**: bpm:category:query
- **说明**: 分页查询流程分类

**请求参数 (BpmCategoryPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | 无 | 分类名，模糊匹配 |
| code | String | 否 | 无 | 分类标志 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 分类状态 |
| createTime | LocalDateTime[] | 否 | 无 | 创建时间区间 |

**响应**: CommonResult<PageResult<BpmCategoryRespVO>>（字段同 3.5）

### 3.7 获取流程分类的精简信息列表

- **路径**: GET /bpm/category/simple-list
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 只包含被开启的分类，主要用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult<List<BpmCategoryRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| name | String | 分类名 |
| code | String | 分类标志 |

**业务逻辑**:
1. 查询启用（ENABLE）状态的分类
2. 按 sort 升序排序后仅返回 id、name、code

---

## 4. 动态表单（BpmFormController）

### 4.1 创建动态表单

- **路径**: POST /bpm/form/create
- **权限**: bpm:form:create
- **说明**: 创建流程动态表单

**请求参数 (BpmFormSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 表单编号（更新时传入） |
| name | String | 是 | @NotNull | 表单名称 |
| conf | String | 是 | @NotNull | 表单的配置 JSON 字符串 |
| fields | List\<String\> | 是 | @NotNull | 表单项数组（JSON 字符串的数组） |
| status | Integer | 是 | @NotNull | 表单状态，参见 CommonStatusEnum 枚举 |
| remark | String | 否 | 无 | 备注 |

**响应**: CommonResult\<Long\>（返回表单编号）

**业务逻辑**:
1. validateFields 校验表单项字段名不重复（当前版本因采用新表单设计器，该校验暂时跳过）
2. 插入 BpmFormDO 并返回编号

### 4.2 更新动态表单

- **路径**: PUT /bpm/form/update
- **权限**: bpm:form:update
- **说明**: 更新动态表单

**请求参数 (BpmFormSaveReqVO)**: 字段同 4.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. validateFields 校验表单项字段名不重复
2. 校验表单存在
3. 更新 BpmFormDO

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_010_000 | 动态表单不存在 |
| 1_009_010_001 | 表单项({})和({})使用了相同的字段名({}) |

### 4.3 删除动态表单

- **路径**: DELETE /bpm/form/delete
- **权限**: bpm:form:delete
- **说明**: 删除动态表单

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 表单编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验表单存在
2. 删除表单

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_010_000 | 动态表单不存在 |

### 4.4 获得动态表单

- **路径**: GET /bpm/form/get
- **权限**: bpm:form:query
- **说明**: 按编号获得单个动态表单

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 表单编号 |

**响应**: CommonResult<BpmFormRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 表单编号 |
| name | String | 表单名称 |
| conf | String | 表单的配置 JSON 字符串 |
| fields | List\<String\> | 表单项数组 |
| status | Integer | 表单状态 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

### 4.5 获得动态表单的精简列表

- **路径**: GET /bpm/form/list-all-simple 或 GET /bpm/form/simple-list
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 用于表单下拉框，仅返回编号与名称

**请求参数**: 无

**响应**: CommonResult<List<BpmFormRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 表单编号 |
| name | String | 表单名称 |

**业务逻辑**:
1. 查询全部表单列表
2. 仅返回 id、name 两个字段

### 4.6 获得动态表单分页

- **路径**: GET /bpm/form/page
- **权限**: bpm:form:query
- **说明**: 分页查询动态表单

**请求参数 (BpmFormPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | 无 | 表单名称，模糊匹配 |

**响应**: CommonResult<PageResult<BpmFormRespVO>>（字段同 4.4）

---

## 5. 用户组（BpmUserGroupController）

### 5.1 创建用户组

- **路径**: POST /bpm/user-group/create
- **权限**: bpm:user-group:create
- **说明**: 创建用户组，用于审批人候选等场景

**请求参数 (BpmUserGroupSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 编号（更新时传入） |
| name | String | 是 | @NotNull | 组名 |
| description | String | 否 | 无 | 描述 |
| userIds | Set\<Long\> | 是 | @NotNull | 成员编号数组 |
| status | Integer | 是 | @NotNull | 状态（0=开启、1=禁用） |

**响应**: CommonResult\<Long\>（返回用户组编号）

**业务逻辑**:
1. 将请求 VO 转换为 BpmUserGroupDO 插入
2. 返回用户组编号

### 5.2 更新用户组

- **路径**: PUT /bpm/user-group/update
- **权限**: bpm:user-group:update
- **说明**: 更新用户组

**请求参数 (BpmUserGroupSaveReqVO)**: 字段同 5.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验用户组存在
2. 更新 BpmUserGroupDO

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_011_000 | 用户分组不存在 |

### 5.3 删除用户组

- **路径**: DELETE /bpm/user-group/delete
- **权限**: bpm:user-group:delete
- **说明**: 删除用户组

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验用户组存在
2. 删除用户组

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_011_000 | 用户分组不存在 |

### 5.4 获得用户组

- **路径**: GET /bpm/user-group/get
- **权限**: bpm:user-group:query
- **说明**: 按编号获得单个用户组

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 编号 |

**响应**: CommonResult<BpmUserGroupRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 组名 |
| description | String | 描述 |
| userIds | Set\<Long\> | 成员编号数组 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

### 5.5 获得用户组分页

- **路径**: GET /bpm/user-group/page
- **权限**: bpm:user-group:query
- **说明**: 分页查询用户组

**请求参数 (BpmUserGroupPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| id | Long | 否 | 无 | 编号 |
| name | String | 否 | 无 | 组名，模糊匹配 |
| status | Integer | 否 | 无 | 状态 |
| createTime | LocalDateTime[] | 否 | 无 | 创建时间区间 |

**响应**: CommonResult<PageResult<BpmUserGroupRespVO>>（字段同 5.4）

### 5.6 获取用户组精简信息列表

- **路径**: GET /bpm/user-group/simple-list
- **权限**: 已认证（未声明 @PreAuthorize）
- **说明**: 只包含被开启的用户组，主要用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult<List<BpmUserGroupRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 组名 |

**业务逻辑**:
1. 查询启用（ENABLE）状态的用户组
2. 仅返回 id、name 两个字段

---

## 6. 流程表达式（BpmProcessExpressionController）

### 6.1 创建流程表达式

- **路径**: POST /bpm/process-expression/create
- **权限**: bpm:process-expression:create
- **说明**: 创建可在流程设计中复用的流程表达式

**请求参数 (BpmProcessExpressionSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 编号（更新时传入） |
| name | String | 是 | @NotEmpty | 表达式名字 |
| status | Integer | 是 | @NotNull | 表达式状态（0=开启、1=禁用） |
| expression | String | 是 | @NotEmpty | 表达式内容 |

**响应**: CommonResult\<Long\>（返回表达式编号）

**业务逻辑**:
1. 将请求 VO 转换为 BpmProcessExpressionDO 插入
2. 返回编号

### 6.2 更新流程表达式

- **路径**: PUT /bpm/process-expression/update
- **权限**: bpm:process-expression:update
- **说明**: 更新流程表达式

**请求参数 (BpmProcessExpressionSaveReqVO)**: 字段同 6.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验表达式存在
2. 更新 BpmProcessExpressionDO

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_014_000 | 流程表达式不存在 |

### 6.3 删除流程表达式

- **路径**: DELETE /bpm/process-expression/delete
- **权限**: bpm:process-expression:delete
- **说明**: 删除流程表达式

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验表达式存在
2. 删除表达式

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_014_000 | 流程表达式不存在 |

### 6.4 获得流程表达式

- **路径**: GET /bpm/process-expression/get
- **权限**: bpm:process-expression:query
- **说明**: 按编号获得单个流程表达式

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 编号 |

**响应**: CommonResult<BpmProcessExpressionRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 表达式名字 |
| status | Integer | 表达式状态 |
| expression | String | 表达式内容 |
| createTime | LocalDateTime | 创建时间 |

### 6.5 获得流程表达式分页

- **路径**: GET /bpm/process-expression/page
- **权限**: bpm:process-expression:query
- **说明**: 分页查询流程表达式

**请求参数 (BpmProcessExpressionPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | 无 | 表达式名字，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 表达式状态 |
| createTime | LocalDateTime[] | 否 | 无 | 创建时间区间 |

**响应**: CommonResult<PageResult<BpmProcessExpressionRespVO>>（字段同 6.4）

---

## 7. 流程监听器（BpmProcessListenerController）

### 7.1 创建流程监听器

- **路径**: POST /bpm/process-listener/create
- **权限**: bpm:process-listener:create
- **说明**: 创建流程/任务监听器，校验监听器值的合法性

**请求参数 (BpmProcessListenerSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 编号（更新时传入） |
| name | String | 是 | @NotEmpty | 监听器名字 |
| type | String | 是 | @NotEmpty | 监听器类型（execution=执行监听、task=任务监听） |
| status | Integer | 是 | @NotNull | 监听器状态（0=开启、1=禁用） |
| event | String | 是 | @NotEmpty | 监听事件（如 start、end） |
| valueType | String | 是 | @NotEmpty | 监听器值类型（class=类、expression=表达式） |
| value | String | 是 | @NotEmpty | 监听器值（类全名或 ${...} 表达式） |

**响应**: CommonResult\<Long\>（返回监听器编号）

**业务逻辑**:
1. valueType 为 class 时通过 Class.forName 反射加载类，类不存在抛 PROCESS_LISTENER_CLASS_NOT_FOUND
2. 校验类实现接口：type 为 execution 时必须实现 JavaDelegate，type 为 task 时必须实现 TaskListener，否则抛 PROCESS_LISTENER_CLASS_IMPLEMENTS_ERROR
3. valueType 为表达式时，值必须以 `${` 开头且以 `}` 结尾，否则抛 PROCESS_LISTENER_EXPRESSION_INVALID
4. 校验通过后插入 BpmProcessListenerDO 并返回编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_013_001 | 流程监听器类({})不存在 |
| 1_009_013_002 | 流程监听器类({})没有实现接口({}) |
| 1_009_013_003 | 流程监听器表达式({})不合法 |

### 7.2 更新流程监听器

- **路径**: PUT /bpm/process-listener/update
- **权限**: bpm:process-listener:update
- **说明**: 更新流程监听器

**请求参数 (BpmProcessListenerSaveReqVO)**: 字段同 7.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验监听器存在
2. 校验监听器值合法性（同 7.1 的 class/表达式校验）
3. 更新 BpmProcessListenerDO

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_013_000 | 流程监听器不存在 |
| 1_009_013_001 | 流程监听器类({})不存在 |
| 1_009_013_002 | 流程监听器类({})没有实现接口({}) |
| 1_009_013_003 | 流程监听器表达式({})不合法 |

### 7.3 删除流程监听器

- **路径**: DELETE /bpm/process-listener/delete
- **权限**: bpm:process-listener:delete
- **说明**: 删除流程监听器

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验监听器存在
2. 删除监听器

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_013_000 | 流程监听器不存在 |

### 7.4 获得流程监听器

- **路径**: GET /bpm/process-listener/get
- **权限**: bpm:process-listener:query
- **说明**: 按编号获得单个流程监听器

**请求参数**: 无（query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | 无 | 编号 |

**响应**: CommonResult<BpmProcessListenerRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 监听器名字 |
| type | String | 监听器类型（execution/task） |
| status | Integer | 监听器状态 |
| event | String | 监听事件 |
| valueType | String | 监听器值类型（class/expression） |
| value | String | 监听器值 |
| createTime | LocalDateTime | 创建时间 |

### 7.5 获得流程监听器分页

- **路径**: GET /bpm/process-listener/page
- **权限**: bpm:process-listener:query
- **说明**: 分页查询流程监听器

**请求参数 (BpmProcessListenerPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | 无 | 监听器名字，模糊匹配 |
| type | String | 否 | 无 | 监听器类型 |
| event | String | 否 | 无 | 监听事件 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态 |

**响应**: CommonResult<PageResult<BpmProcessListenerRespVO>>（字段同 7.4）
