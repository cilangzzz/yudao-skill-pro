# 数据模型详情

> bpm 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

bpm 模块的业务表共 8 张（`dal/dataobject` 下 8 个 DO），全部继承 `BaseDO`，**不使用 `TenantBaseDO`**（流程数据全局共享，不做租户隔离）。Flowable 6 引擎自身的模型/运行/历史数据存放在 `ACT_*` 系统表中，由引擎自动维护，不属于业务 DO 范畴；`bpm_process_definition_info` 是 Flowable `ACT_RE_PROCDEF` 的业务扩展表，用于弥补 `ProcessDefinition` 无法扩展字段的限制。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，实现 Serializable/TransPojo）
│   ├── creator        String          创建者（SysUser 的 id，INSERT 时自动填充）
│   ├── createTime     LocalDateTime   创建时间（INSERT 时自动填充）
│   ├── updater        String          更新者（INSERT_UPDATE 时自动填充）
│   ├── updateTime     LocalDateTime   最后更新时间（INSERT_UPDATE 时自动填充）
│   └── deleted        Boolean         逻辑删除标记（@TableLogic，MyBatis-Plus 自动过滤）
│
├── bpm.dal.dataobject.definition.BpmCategoryDO              流程分类
├── bpm.dal.dataobject.definition.BpmFormDO                  动态表单
├── bpm.dal.dataobject.definition.BpmProcessDefinitionInfoDO 流程定义扩展信息
├── bpm.dal.dataobject.definition.BpmProcessExpressionDO     流程表达式
├── bpm.dal.dataobject.definition.BpmProcessListenerDO       流程监听器模板
├── bpm.dal.dataobject.definition.BpmUserGroupDO             用户组
├── bpm.dal.dataobject.task.BpmProcessInstanceCopyDO         流程抄送
└── bpm.dal.dataobject.oa.BpmOALeaveDO                       OA 请假申请

cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO extends BaseDO
└── 增加字段：tenantId Long 多租户编号 —— bpm 模块未使用
```

**使用规则**：

- **BaseDO**：所有表通用的 4 个审计字段 + 逻辑删除。bpm 模块全部 8 个 DO 均直接继承它，因为流程定义、表单、分类等数据是全局共享的，流程实例运行数据由 Flowable 引擎管理，均不走多租户隔离。
- **TenantBaseDO**：仅当业务表需要按租户隔离时才继承（需同时配合 `TenantIgnore` 策略与框架租户拦截器）。bpm 模块的 `controller/app` 无 App 端接口、全部为 admin 管理端，数据不区分租户，故无任何 DO 使用它。
- 每张表均声明 `@KeySequence("表名_seq")`，用于 Oracle/PostgreSQL/Kingbase/DB2/H2 等数据库的主键自增；MySQL 使用自增主键即可。

## 2. 核心 DO 实体

### 2.1 流程定义聚合（dal/dataobject/definition）

#### BpmCategoryDO (bpm_category)

流程分类，BPMN 模型按分类归组，在"发起流程"列表中作为分组维度。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 分类编号，主键自增 |
| name | String | name | 分类名 |
| code | String | code | 分类标志（编码），被 `BpmProcessDefinitionInfoDO.category` 冗余引用 |
| description | String | description | 分类描述 |
| status | Integer | status | 分类状态，枚举 `CommonStatusEnum`（0 开启 / 1 禁用） |
| sort | Integer | sort | 分类排序 |

**继承**: BaseDO
**索引**: 主键 `id`；`code` 为业务唯一编码（服务层 `CATEGORY_CODE_DUPLICATE` 校验重复，未建数据库唯一索引）

#### BpmFormDO (bpm_form)

工作流的动态表单定义，用于申请表单需要动态配置的场景，存储 form-generator 生成的 JSON。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 表单名 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |
| conf | String | conf | 表单的配置（form-generator 的 conf JSON 串） |
| fields | List\<String\> | fields | 表单项的数组，form-generator 生成的 JSON 串集合，`JacksonTypeHandler` 序列化为 JSON 存储 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 `id`。被 `BpmProcessDefinitionInfoDO.formId` 引用，其 `conf`/`fields` 在流程发布时冗余到 `formConf`/`formFields`

#### BpmProcessDefinitionInfoDO (bpm_process_definition_info)

流程定义的业务扩展信息表（模块最核心、字段最多的表）。Flowable 的 `ProcessDefinition` 不支持扩展字段，本表通过 `processDefinitionId` 一对一挂接扩展配置。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键自增 |
| processDefinitionId | String | process_definition_id | Flowable 流程定义编号，关联 `ProcessDefinition#getId()` |
| modelId | String | model_id | Flowable 流程模型编号，关联 `Model#getId()` |
| modelType | Integer | model_type | 流程模型类型，枚举 `BpmModelTypeEnum` |
| category | String | category | 流程分类编码，关联 `BpmCategoryDO.code`（因 `ProcessDefinition#getCategory()` 无法设置而冗余存储） |
| icon | String | icon | 图标 |
| description | String | description | 描述 |
| formType | Integer | form_type | 表单类型，枚举 `BpmModelFormTypeEnum`（NORMAL 动态表单 / CUSTOM 自定义表单） |
| formId | Long | form_id | 动态表单编号，NORMAL 时关联 `BpmFormDO.id` |
| formConf | String | form_conf | 表单配置，NORMAL 时冗余 `BpmFormDO.conf` |
| formFields | List\<String\> | form_fields | 表单项数组，NORMAL 时冗余 `BpmFormDO.fields`，`JacksonTypeHandler` |
| formCustomCreatePath | String | form_custom_create_path | 自定义表单的提交路径（Vue 路由地址），CUSTOM 时使用 |
| formCustomViewPath | String | form_custom_view_path | 自定义表单的查看路径（Vue 路由地址），CUSTOM 时使用 |
| simpleModel | String | simple_model | SIMPLE（仿钉钉）设计器的模型数据 JSON 快照，发布时保存 |
| visible | Boolean | visible | 是否可见：false 时不展示在"发起流程"列表（仍可发起） |
| sort | Long | sort | 排序值 |
| startUserIds | List\<Long\> | start_user_ids | 可发起用户编号数组，空表示全部可发起；`LongListTypeHandler`（逗号分隔）以支持 `find_in_set` 过滤 |
| startDeptIds | List\<Long\> | start_dept_ids | 可发起部门编号数组，`LongListTypeHandler` |
| managerUserIds | List\<Long\> | manager_user_ids | 可管理用户编号数组，`LongListTypeHandler` |
| allowCancelRunningProcess | Boolean | allow_cancel_running_process | 是否允许撤销审批中的申请 |
| allowWithdrawTask | Boolean | allow_withdraw_task | 是否允许审批人撤回任务 |
| processIdRule | ProcessIdRule | process_id_rule | 流程 ID 规则（嵌套 JSON），`JacksonTypeHandler` |
| autoApprovalType | Integer | auto_approval_type | 自动去重类型，枚举 `BpmAutoApproveTypeEnum` |
| titleSetting | TitleSetting | title_setting | 流程标题设置（嵌套 JSON），`JacksonTypeHandler` |
| summarySetting | SummarySetting | summary_setting | 流程摘要设置（嵌套 JSON），`JacksonTypeHandler` |
| processBeforeTriggerSetting | HttpRequestSetting | process_before_trigger_setting | 流程前置 HTTP 通知设置，`JacksonTypeHandler` |
| processAfterTriggerSetting | HttpRequestSetting | process_after_trigger_setting | 流程后置 HTTP 通知设置，`JacksonTypeHandler` |
| taskBeforeTriggerSetting | HttpRequestSetting | task_before_trigger_setting | 任务前置 HTTP 通知设置，`JacksonTypeHandler` |
| taskAfterTriggerSetting | HttpRequestSetting | task_after_trigger_setting | 任务后置 HTTP 通知设置，`JacksonTypeHandler` |
| printTemplateSetting | PrintTemplateSetting | print_template_setting | 自定义打印模板设置，`JacksonTypeHandler` |

**继承**: BaseDO
**索引**: 主键 `id`；`process_definition_id` 与 Flowable `ACT_RE_PROCDEF.ID_` 一对一关联，`model_id` 关联 `ACT_RE_MODEL.ID_`（均为代码层面关联，未在 DO 上声明数据库唯一索引）

#### BpmProcessExpressionDO (bpm_process_expression)

流程表达式模板，供 BPMN 设计时直接选择使用。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 表达式名字 |
| status | Integer | status | 表达式状态（CommonStatus） |
| expression | String | expression | 表达式内容 |

**继承**: BaseDO
**索引**: 主键 `id`

#### BpmProcessListenerDO (bpm_process_listener)

流程监听器模板：本质是监听器的预置模板，BPMN 设计时直接选择。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，自增 |
| name | String | name | 监听器名字 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |
| type | String | type | 监听类型，枚举 `BpmProcessListenerTypeEnum`：`execution` 执行监听器 / `task` 任务监听器 |
| event | String | event | 监听事件：execution 为 start/end；task 为 create/assignment/complete/delete/update/timeout |
| valueType | String | value_type | 值类型：`class` Java 类 / `delegateExpression` 委托表达式（Spring Bean）/ `expression` 表达式 |
| value | String | value | 值（类全名或表达式） |

**继承**: BaseDO
**索引**: 主键 `id`

#### BpmUserGroupDO (bpm_user_group)

用户组，作为任务候选人策略（`BpmTaskCandidateStrategyEnum` 的用户组策略）的审批人来源之一。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 组名 |
| description | String | description | 描述 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |
| userIds | Set\<Long\> | user_ids | 成员用户编号数组，关联 system_users 的 id，`JacksonTypeHandler` 存 JSON |

**继承**: BaseDO
**索引**: 主键 `id`

### 2.2 流程运行聚合（dal/dataobject/task）

#### BpmProcessInstanceCopyDO (bpm_process_instance_copy)

流程抄送记录：审批过程中将任务/节点抄送给指定用户。大量冗余流程实例字段以支持列表直接展示。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键自增 |
| startUserId | Long | start_user_id | 发起人编号，冗余 ProcessInstance 的 startUserId |
| processInstanceName | String | process_instance_name | 流程名，冗余 ProcessInstance 的 name |
| processInstanceId | String | process_instance_id | 流程实例编号，关联 ProcessInstance 的 id |
| processDefinitionId | String | process_definition_id | 流程定义编号，关联 ProcessInstance 的 processDefinitionId |
| category | String | category | 流程分类，冗余 ProcessInstance 的 category |
| activityId | String | activity_id | 流程活动编号，冗余 BPMN `FlowNode#getId()`；仿钉钉/飞书抄送节点（ServiceTask）无 taskId 只有 activityId，用于查询抄送节点的表单字段权限 |
| activityName | String | activity_name | 流程活动名字，冗余 `FlowNode#getName()` |
| taskId | String | task_id | 任务编号，关联 `HistoricTaskInstance#getId()`（节点抄送时可为空） |
| userId | Long | user_id | 被抄送的用户编号，关联 system_users 的 id |
| reason | String | reason | 抄送意见 |

**继承**: BaseDO
**索引**: 主键 `id`；常用查询维度为 `user_id`（我收到的抄送）与 `process_instance_id`，未在 DO 上声明数据库唯一索引

### 2.3 OA 示例聚合（dal/dataobject/oa）

#### BpmOALeaveDO (bpm_oa_leave)

OA 请假申请，模块自带的"业务表单 + 流程审批"示例，演示如何通过 `BpmProcessInstanceApi` 发起流程并通过事件监听回写审批结果。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 请假表单主键，自增 |
| userId | Long | user_id | 申请人的用户编号，关联 AdminUserDO 的 id |
| type | Integer | type | 请假类型，字典 `bpm_oa_leave_type`（1 病假 / 2 事假 / 3 婚假） |
| reason | String | reason | 原因 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| day | Long | day | 请假天数（简单实现：1 整天或 0.5 半天） |
| status | Integer | status | 审批结果，复用枚举 `BpmTaskStatusEnum`（即 `BpmProcessInstanceStatusEnum` 语义） |
| processInstanceId | String | process_instance_id | 对应的流程编号，关联 Flowable ProcessInstance 的 id |

**继承**: BaseDO
**索引**: 主键 `id`；`process_instance_id` 关联流程实例，用于流程结束回调（`BpmProcessInstanceStatusEvent`）时反查业务单据

## 3. 实体关系

```
                 ┌───────────────┐
                 │ BpmCategoryDO │（code 分类编码）
                 └───────┬───────┘
                         │ 1
                         │ category（冗余 code，非外键）
                         │ N
┌──────────┐  formId     ┌──────────────────────────────┐  processDefinitionId / modelId
│BpmFormDO ├────────────►│ BpmProcessDefinitionInfoDO   ├────────────► Flowable ACT_RE_PROCDEF / ACT_RE_MODEL
└──────────┘  N……1（1）  │ （1 : 1 扩展流程定义）        │    （引擎表，由 Flowable 管理）
        │                └──────────────┬───────────────┘
        │ conf/fields 冗余为            │ startUserIds / startDeptIds / managerUserIds
        │ formConf/formFields           ▼
        │                 system_users / system_dept（system 模块，用户/部门编号数组）
        │
        │ formType=NORMAL 时流程发起渲染动态表单
        ▼
  Flowable 流程实例（ACT_RU_EXECUTION / ACT_RU_TASK / ACT_HI_*）
        │ processInstanceId
        ├────────────►┌─────────────────────────────┐   taskId → ACT_HI_TASKINST
        │             │ BpmProcessInstanceCopyDO    ├──►（任务/活动抄送）
        │             └──────────────┬──────────────┘   userId → system_users（被抄送人）
        │                            │ startUserId → system_users（发起人）
        │
        │ processInstanceId
        ▼
  ┌──────────────┐  userId → system_users
  │ BpmOALeaveDO │  status 由 BpmProcessInstanceStatusEvent 回调回写
  └──────────────┘
        ▲
        │ 同样模式：crm 合同/回款、hrm 考勤请假等业务单据
        │（processInstanceId 关联 + 流程状态事件监听）

  BpmUserGroupDO.userIds ──► system_users（任务候选人策略的用户组来源）
  BpmProcessListenerDO / BpmProcessExpressionDO ──► 被 BPMN 模型（ACT_GE_BYTEARRAY 中的 XML）引用，独立模板表
```

核心关联说明：

1. **流程定义扩展（1:1）**：`bpm_process_definition_info.process_definition_id` ↔ Flowable `ACT_RE_PROCDEF.ID_`；`model_id` ↔ `ACT_RE_MODEL.ID_`。模型发布时由 `BpmProcessDefinitionInfoDO` 保存表单、可见性、触发器等扩展配置。
2. **表单引用（N:1）**：`bpm_process_definition_info.form_id` → `bpm_form.id`，且 `conf`/`fields` 在发布时**冗余**到 `form_conf`/`form_fields`，保证历史流程定义不受表单后续修改影响。
3. **分类引用（N:1）**：`bpm_process_definition_info.category` → `bpm_category.code`（存编码而非 id）。
4. **用户组（多对多）**：`bpm_user_group.user_ids` 以 JSON 数组存 system_users 的 id 集合，无中间表。
5. **抄送（N:1）**：`bpm_process_instance_copy.process_instance_id` → 流程实例；`task_id` → 历史任务；`user_id`/`start_user_id` → system_users。
6. **业务单据挂接流程（1:1）**：`bpm_oa_leave.process_instance_id` → 流程实例 id；流程状态变更通过 `BpmProcessInstanceStatusEvent`（api/event）通知监听器回写 `status`。CRM/HRM 等模块的业务单据采用相同模式。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|------|-----|------|
| bpm_category | BpmCategoryDO | 流程分类 |
| bpm_form | BpmFormDO | 动态表单定义 |
| bpm_process_definition_info | BpmProcessDefinitionInfoDO | 流程定义业务扩展信息（Flowable ACT_RE_PROCDEF 的 1:1 扩展表） |
| bpm_process_expression | BpmProcessExpressionDO | 流程表达式模板 |
| bpm_process_listener | BpmProcessListenerDO | 流程监听器模板 |
| bpm_user_group | BpmUserGroupDO | 用户组（审批人分组） |
| bpm_process_instance_copy | BpmProcessInstanceCopyDO | 流程抄送记录 |
| bpm_oa_leave | BpmOALeaveDO | OA 请假申请（业务表单 + 流程审批示例） |

> 补充：Flowable 引擎自身的表（`ACT_RE_*` 流程定义、`ACT_RU_*` 运行时、`ACT_HI_*` 历史、`ACT_GE_*` 通用存储等）由 Flowable 6 自动建表与维护，不映射为本模块的 DO，业务上通过 `bpm_process_definition_info`、`processInstanceId`/`taskId` 等字段与上述业务表关联。
