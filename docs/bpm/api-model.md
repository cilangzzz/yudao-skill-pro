# API - 流程模型管理 (BpmModelController)

> 路径前缀：`/bpm/model`
> 对应服务：`BpmModelService`

## 概述

流程模型是流程定义的设计阶段产物。支持两种设计器类型：

- **BPMN 模型** (`modelType=10`) -- 标准 BPMN 2.0 流程设计器，适用于复杂流程
- **Simple 模型** (`modelType=20`) -- 仿钉钉/飞书的简易设计器，适用于简单审批流程

模型设计完成后，通过"部署"操作生成流程定义（ProcessDefinition）。

---

## 接口列表

### 1. 创建模型

- **接口：** `POST /bpm/model/create`
- **权限：** `bpm:model:create`
- **说明：** 创建一个新的流程模型，初始状态为未部署

**请求参数（BpmModelCreateReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 模型名称 |
| key | String | 是 | 模型标识（唯一） |
| category | String | 是 | 流程分类编码 |
| modelType | Integer | 是 | 模型类型：10-BPMN，20-Simple |
| description | String | 否 | 模型描述 |
| formType | Integer | 否 | 表单类型 |
| formId | Long | 否 | 动态表单编号 |
| formConf | String | 否 | 表单配置 JSON |
| formFields | List\<String\> | 否 | 表单字段列表 |

**返回：** `CommonResult<String>` -- 模型编号

---

### 2. 修改模型

- **接口：** `PUT /bpm/model/update`
- **权限：** `bpm:model:update`
- **说明：** 修改模型基本信息（名称、描述等）

---

### 3. 删除模型

- **接口：** `DELETE /bpm/model/delete`
- **权限：** `bpm:model:delete`
- **说明：** 删除未部署的模型。已部署的模型不允许删除。

---

### 4. 获取模型详情

- **接口：** `GET /bpm/model/get`
- **权限：** `bpm:model:query`
- **说明：** 获取模型详细信息，包括 BPMN XML 或 Simple 模型数据

**返回（BpmModelRespVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 模型编号 |
| name | String | 模型名称 |
| key | String | 模型标识 |
| category | String | 流程分类 |
| modelType | Integer | 模型类型 |
| description | String | 模型描述 |
| bpmnXml | String | BPMN XML（BPMN 类型） |
| simpleModel | String | Simple 模型 JSON（Simple 类型） |
| formType | Integer | 表单类型 |
| formId | Long | 表单编号 |
| formConf | String | 表单配置 |
| formFields | List\<String\> | 表单字段 |
| deploymentId | String | 部署编号（已部署时有值） |
| processDefinitionId | String | 流程定义编号（已部署时有值） |

---

### 5. 分页查询模型

- **接口：** `GET /bpm/model/page`
- **权限：** `bpm:model:query`

**请求参数（BpmModelPageReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 模型名称（模糊匹配） |
| category | String | 否 | 流程分类 |
| modelType | Integer | 否 | 模型类型 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

---

### 6. 部署模型

- **接口：** `PUT /bpm/model/deploy`
- **权限：** `bpm:model:deploy`
- **说明：** 将模型部署为流程定义。部署后会生成新的流程定义版本。

---

### 7. 更新 BPMN XML

- **接口：** `PUT /bpm/model/update-bpmn`
- **权限：** `bpm:model:update`
- **说明：** 更新 BPMN 模型的 XML 内容（由前端设计器调用）

---

## 设计要点

1. **模型与定义的关系：** 一个模型可部署多次，每次部署生成一个新的流程定义版本
2. **Simple 模型数据格式：** Simple 设计器使用 JSON 格式存储模型数据，节点结构为 `BpmSimpleModelNodeVO`
3. **模型元信息：** `BpmModelMetaInfoVO` 存储模型的扩展配置（表单、分类、权限等）
4. **未部署模型可编辑：** 已部署的模型需要取消部署后才能修改
