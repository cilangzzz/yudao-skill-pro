# API - 流程定义管理 (BpmProcessDefinitionController)

> 路径前缀：`/bpm/process-definition`
> 对应服务：`BpmProcessDefinitionService`

## 概述

流程定义是流程模型部署后的产物，是流程实例运行的模板。流程定义由 Flowable 引擎管理（`ACT_RE_PROCDEF` 表），扩展信息存储在 `bpm_process_definition_info` 表中。

流程定义支持版本管理：同一流程 Key 可以有多个版本，已运行的实例使用创建时的版本。

---

## 接口列表

### 1. 获取流程定义详情

- **接口：** `GET /bpm/process-definition/get`
- **权限：** `bpm:process-definition:query`
- **说明：** 获取流程定义详情，包括 BPMN XML、表单配置、Simple 模型数据等

**返回（BpmProcessDefinitionRespVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 流程定义编号 |
| name | String | 流程定义名称 |
| key | String | 流程定义标识 |
| version | Integer | 版本号 |
| category | String | 流程分类编码 |
| formType | Integer | 表单类型 |
| formId | Long | 动态表单编号 |
| formConf | String | 表单配置 |
| formFields | List\<String\> | 表单字段 |
| modelType | Integer | 模型类型 |
| simpleModel | String | Simple 模型数据 |
| startUserIds | List\<Long\> | 可发起用户列表 |
| managerUserIds | List\<Long\> | 可管理用户列表 |
| bpmnXml | String | BPMN XML |
| suspensionState | Integer | 激活/挂起状态 |

---

### 2. 分页查询流程定义

- **接口：** `GET /bpm/process-definition/page`
- **权限：** `bpm:process-definition:query`

**请求参数（BpmProcessDefinitionPageReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 流程定义名称（模糊匹配） |
| key | String | 否 | 流程定义标识 |
| category | String | 否 | 流程分类编码 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

---

### 3. 获取流程定义列表（simple）

- **接口：** `GET /bpm/process-definition/list-all-simple`
- **权限：** 无（登录用户可访问）
- **说明：** 获取所有已激活的流程定义简要信息，用于前端下拉选择

---

### 4. 激活/挂起流程定义

- **接口：** `PUT /bpm/process-definition/update-suspension-state`
- **权限：** `bpm:process-definition:update`
- **说明：** 激活或挂起流程定义。挂起后，该定义无法发起新的流程实例。

---

### 5. 删除流程定义

- **接口：** `DELETE /bpm/process-definition/delete`
- **权限：** `bpm:process-definition:delete`
- **说明：** 删除流程定义（级联删除部署信息）

---

### 6. 获取流程定义的 BPMN XML

- **接口：** `GET /bpm/process-definition/get-bpmn-xml`
- **权限：** `bpm:process-definition:query`
- **说明：** 获取指定流程定义的 BPMN XML，用于前端流程图渲染

---

## 设计要点

1. **版本管理：** 同一流程 Key 每次部署会自动递增版本号，`page` 接口默认返回最新版本
2. **扩展信息：** Flowable 原生的流程定义不包含表单、分类等信息，这些存储在 `bpm_process_definition_info` 表中
3. **权限控制：** `startUserIds` 控制哪些用户可以发起流程，`managerUserIds` 控制哪些用户可以管理流程
4. **激活/挂起：** 挂起流程定义会影响所有使用该定义的新建流程，但不影响已运行的流程实例
