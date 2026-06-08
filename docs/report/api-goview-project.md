# GoView 项目管理 API

> 路径前缀：`/report/go-view/project`
> Controller：`GoViewProjectController`

## 概述

GoView 项目管理负责大屏报表项目的 CRUD 操作。项目按 `creator` 字段实现数据隔离，用户只能操作自己创建的项目。项目创建时默认状态为**未发布**（`status=1`），需手动发布。

## 接口列表

### 1. 创建项目

- **路径**：`POST /report/go-view/project/create`
- **权限**：`report:go-view-project:create`
- **请求体**：`GoViewProjectCreateReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 项目名称 |
| picUrl | String | 否 | 预览图片 URL |
| content | String | 否 | 报表内容（JSON 格式配置） |
| remark | String | 否 | 项目备注 |

- **响应**：`CommonResult<Long>` -- 返回项目 ID
- **业务逻辑**：
  1. 将 VO 转换为 DO（MapStruct）
  2. 设置默认状态为未发布（`CommonStatusEnum.DISABLE`）
  3. 插入数据库并返回主键

### 2. 更新项目

- **路径**：`PUT /report/go-view/project/update`
- **权限**：`report:go-view-project:update`
- **请求体**：`GoViewProjectUpdateReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 项目 ID |
| name | String | 否 | 项目名称 |
| picUrl | String | 否 | 预览图片 URL |
| content | String | 否 | 报表内容（JSON 格式配置） |
| status | Integer | 否 | 发布状态：0-已发布，1-未发布 |
| remark | String | 否 | 项目备注 |

- **响应**：`CommonResult<Boolean>`
- **业务逻辑**：校验项目存在后更新

### 3. 删除项目

- **路径**：`DELETE /report/go-view/project/delete`
- **权限**：`report:go-view-project:delete`
- **参数**：`id`（Long，项目 ID）
- **响应**：`CommonResult<Boolean>`
- **业务逻辑**：校验项目存在后逻辑删除

### 4. 查询项目详情

- **路径**：`GET /report/go-view/project/get`
- **权限**：`report:go-view-project:query`
- **参数**：`id`（Long，项目 ID）
- **响应**：`CommonResult<GoViewProjectDO>`

### 5. 分页查询我的项目

- **路径**：`GET /report/go-view/project/my-page`
- **权限**：`report:go-view-project:query`
- **参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

- **响应**：`CommonResult<PageResult<GoViewProjectDO>>`
- **业务逻辑**：根据当前登录用户 ID 过滤，按 ID 倒序排列

## 数据访问层

### GoViewProjectMapper

继承 `BaseMapperX<GoViewProjectDO>`，提供自定义查询方法：

```java
default PageResult<GoViewProjectDO> selectPage(PageParam reqVO, Long userId) {
    return selectPage(reqVO, new LambdaQueryWrapperX<GoViewProjectDO>()
            .eq(GoViewProjectDO::getCreator, userId)
            .orderByDesc(GoViewProjectDO::getId));
}
```

## 对象转换

`GoViewProjectConvert`（MapStruct）负责：

- `GoViewProjectCreateReqVO` -> `GoViewProjectDO`
- `GoViewProjectUpdateReqVO` -> `GoViewProjectDO`

## 错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| `1_003_000_000` | `GO_VIEW_PROJECT_NOT_EXISTS` | GoView 项目不存在 |
