# BPM 模块 - 数据模型

## 实体继承体系

所有 DO 实体继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| creator | String | 创建人 |
| createTime | Date | 创建时间 |
| updater | String | 更新人 |
| updateTime | Date | 更新时间 |
| deleted | Boolean | 是否删除（逻辑删除） |

---

## 自建数据表

### bpm_category -- 流程分类表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分类编号（主键） |
| name | String | 分类名称 |
| code | String | 分类编码（唯一标识，流程定义通过此字段关联分类） |
| description | String | 分类描述 |
| status | Integer | 分类状态 |
| sort | Integer | 排序号 |

**实体类：** `BpmCategoryDO`

---

### bpm_form -- 流程表单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 表单编号（主键） |
| name | String | 表单名称 |
| status | Integer | 状态 |
| conf | String | 表单配置 JSON（动态表单的布局、校验规则等） |
| fields | List\<String\> | 表单项数组（动态表单的字段标识列表） |
| remark | String | 备注 |

**实体类：** `BpmFormDO`

---

### bpm_user_group -- 审批用户组表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户组编号（主键） |
| name | String | 用户组名称 |
| description | String | 用户组描述 |
| status | Integer | 状态 |
| user_ids | Set\<Long\> | 成员用户编号数组（JSON 存储） |

**实体类：** `BpmUserGroupDO`

---

### bpm_process_definition_info -- 流程定义扩展信息表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号（主键） |
| process_definition_id | String | 流程定义编号（关联 Flowable ACT_RE_PROCDEF.ID） |
| model_id | String | 流程模型编号（关联 Flowable ACT_RE_MODEL.ID） |
| model_type | Integer | 模型类型：10-BPMN，20-Simple |
| category | String | 流程分类编码（关联 bpm_category.code） |
| form_type | Integer | 表单类型：10-业务表单，20-流程表单 |
| form_id | Long | 动态表单编号（关联 bpm_form.id） |
| form_conf | String | 表单配置 |
| form_fields | List\<String\> | 表单字段列表 |
| start_user_ids | List\<Long\> | 可发起用户编号列表 |
| manager_user_ids | List\<Long\> | 可管理用户编号列表 |
| simple_model | String | Simple 设计器模型数据 JSON |

**实体类：** `BpmProcessDefinitionInfoDO`

**说明：** Flowable 原生的流程定义表（`ACT_RE_PROCDEF`）不包含表单、分类、权限等扩展信息，这些信息存储在此表中。

---

### bpm_process_listener -- 流程监听器表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键 ID |
| name | String | 监听器名称 |
| status | Integer | 状态 |
| type | String | 监听类型：`execution`（执行监听器）/ `task`（任务监听器） |
| event | String | 监听事件（如 start、end、create、complete 等） |
| value_type | String | 值类型：`class` / `delegateExpression` / `expression` |
| value | String | 值（类名、表达式等） |

**实体类：** `BpmProcessListenerDO`

---

### bpm_process_expression -- 流程表达式表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号（主键） |
| name | String | 表达式名称 |
| status | Integer | 状态 |
| expression | String | 表达式内容（用于审批人策略等） |

**实体类：** `BpmProcessExpressionDO`

---

### bpm_process_instance_copy -- 流程抄送表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号（主键） |
| start_user_id | Long | 发起人 ID |
| process_instance_id | String | 流程实例编号 |
| process_definition_id | String | 流程定义编号 |
| activity_id | String | 流程活动编号 |
| task_id | String | 任务编号 |
| user_id | Long | 被抄送用户编号 |
| reason | String | 抄送意见 |

**实体类：** `BpmProcessInstanceCopyDO`

---

### bpm_oa_leave -- OA 请假申请表（示例业务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 请假表单主键 |
| user_id | Long | 申请人用户编号 |
| type | String | 请假类型 |
| reason | String | 请假原因 |
| start_time | LocalDateTime | 开始时间 |
| end_time | LocalDateTime | 结束时间 |
| day | Long | 请假天数 |
| status | Integer | 审批结果 |
| process_instance_id | String | 流程实例编号（关联 Flowable ACT_HI_PROCINST.ID_） |

**实体类：** `BpmOALeaveDO`

**说明：** 此表为业务集成示例，展示如何将业务数据与流程实例关联。

---

## 表关系 (ER)

```
bpm_category.code  <───  bpm_process_definition_info.category    (N:1)
bpm_form.id        <───  bpm_process_definition_info.form_id     (N:1)
ACT_RE_PROCDEF.ID_  <───  bpm_process_definition_info.process_definition_id  (N:1)
ACT_HI_PROCINST.ID_ <───  bpm_process_instance_copy.process_instance_id  (N:1)
ACT_HI_PROCINST.ID_ <───  bpm_oa_leave.process_instance_id  (1:1)
```

---

## Flowable 原生表

BPM 模块依赖以下 Flowable 引擎表，这些表由 Flowable 自动管理，不需要手动操作：

| 表名 | 说明 |
|------|------|
| ACT_RE_DEPLOYMENT | 部署信息表 -- 存储流程部署记录 |
| ACT_RE_PROCDEF | 流程定义表 -- 存储已部署的流程定义（含版本号） |
| ACT_RE_MODEL | 流程模型表 -- 存储流程模型数据（BPMN JSON） |
| ACT_RU_EXECUTION | 运行时执行实例表 -- 存储正在运行的流程执行信息 |
| ACT_RU_TASK | 运行时任务表 -- 存储当前待处理的任务 |
| ACT_HI_PROCINST | 历史流程实例表 -- 存储已完成的流程实例 |
| ACT_HI_TASKINST | 历史任务实例表 -- 存储已完成的任务 |
| ACT_HI_VARINST | 历史变量表 -- 存储流程变量（含表单数据） |

**前缀说明：**
- `ACT_RE_*` -- Repository，流程定义和模型
- `ACT_RU_*` -- Runtime，运行时数据（流程结束后清理）
- `ACT_HI_*` -- History，历史数据（永久保留）
