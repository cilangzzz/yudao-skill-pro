# API - 表单管理 (BpmFormController)

> 路径前缀：`/bpm/form`
> 对应服务：`BpmFormService`

## 概述

BPM 模块提供动态表单管理功能，支持两种表单模式：

- **业务表单 (formType=10)：** 使用业务系统自有的页面作为表单，通过 `formId` 关联业务模块
- **流程表单 (formType=20)：** 使用 BPM 模块内置的动态表单设计器，表单配置以 JSON 存储

---

## 接口列表

### 1. 创建表单

- **接口：** `POST /bpm/form/create`
- **权限：** `bpm:form:create`

**请求参数（BpmFormCreateReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 表单名称 |
| status | Integer | 是 | 状态 |
| conf | String | 否 | 表单配置 JSON（动态表单） |
| fields | List\<String\> | 否 | 表单项数组（动态表单） |
| remark | String | 否 | 备注 |

**返回：** `CommonResult<Long>` -- 表单编号

---

### 2. 修改表单

- **接口：** `PUT /bpm/form/update`
- **权限：** `bpm:form:update`

---

### 3. 删除表单

- **接口：** `DELETE /bpm/form/delete`
- **权限：** `bpm:form:delete`
- **说明：** 删除表单。已被流程定义引用的表单不允许删除。

---

### 4. 获取表单详情

- **接口：** `GET /bpm/form/get`
- **权限：** `bpm:form:query`

**返回（BpmFormRespVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 表单编号 |
| name | String | 表单名称 |
| status | Integer | 状态 |
| conf | String | 表单配置 JSON |
| fields | List\<String\> | 表单项数组 |
| remark | String | 备注 |

---

### 5. 分页查询表单

- **接口：** `GET /bpm/form/page`
- **权限：** `bpm:form:query`

**请求参数（BpmFormPageReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 表单名称（模糊匹配） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

---

### 6. 获取表单简单列表

- **接口：** `GET /bpm/form/list-all-simple`
- **权限：** 无（登录用户）
- **说明：** 获取所有启用状态的表单简要列表，用于下拉选择

---

## 设计要点

1. **表单与流程绑定：** 在流程定义（`bpm_process_definition_info`）中通过 `form_type` 和 `form_id` 关联表单
2. **动态表单数据格式：** `conf` 存储表单整体配置（布局、校验规则等），`fields` 存储表单项标识列表
3. **业务表单模式：** 当 `formType=10` 时，`formId` 指向业务模块的表单页面编号，BPM 模块不管理表单内容
4. **表单变量注入：** 流程发起时，表单数据会作为流程变量注入到 Flowable 引擎中
