# API - 流程分类管理 (BpmCategoryController)

> 路径前缀：`/bpm/category`
> 对应服务：`BpmCategoryService`（基于 BpmCategoryMapper 直接操作）

## 概述

流程分类用于对流程定义进行分组管理。每个流程定义关联一个分类，前端按分类展示流程列表。

分类数据存储在 `bpm_category` 表中。

---

## 接口列表

### 1. 创建分类

- **接口：** `POST /bpm/category/create`
- **权限：** `bpm:category:create`

**请求参数（BpmCategoryCreateReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 分类名称 |
| code | String | 是 | 分类编码（唯一标识） |
| description | String | 否 | 分类描述 |
| status | Integer | 是 | 状态 |
| sort | Integer | 否 | 排序号 |

**返回：** `CommonResult<Long>` -- 分类编号

---

### 2. 修改分类

- **接口：** `PUT /bpm/category/update`
- **权限：** `bpm:category:update`

---

### 3. 删除分类

- **接口：** `DELETE /bpm/category/delete`
- **权限：** `bpm:category:delete`
- **说明：** 删除分类。已被流程定义引用的分类不允许删除。

---

### 4. 获取分类详情

- **接口：** `GET /bpm/category/get`
- **权限：** `bpm:category:query`

**返回（BpmCategoryRespVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分类编号 |
| name | String | 分类名称 |
| code | String | 分类编码 |
| description | String | 分类描述 |
| status | Integer | 状态 |
| sort | Integer | 排序号 |

---

### 5. 获取分类列表

- **接口：** `GET /bpm/category/list`
- **权限：** `bpm:category:query`
- **说明：** 获取全部分类列表（非分页），用于下拉选择

---

## 设计要点

1. **code 唯一性：** 分类编码 `code` 是业务唯一标识，流程定义通过 `category` 字段关联此编码
2. **状态控制：** 分类禁用后，关联的流程定义仍可正常使用，但新创建流程定义时无法选择该分类
3. **排序：** 通过 `sort` 字段控制分类在前端的展示顺序
