# 部门管理接口 (DeptController)

> 部门是组织架构的核心，采用树形结构管理，同时作为数据权限的载体。

## 接口路径前缀

`/system/dept`  (Controller: `DeptController`)

---

## 1. 创建部门

- **路径**: `POST /system/dept/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:dept:create')")`
- **说明**: 创建新的部门节点

**请求参数 (DeptSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| name | String | 是 | @NotBlank @Size(2,30) | 部门名称 |
| parentId | Long | 是 | @NotNull | 父部门ID（顶级传0） |
| sort | Integer | 是 | @NotNull | 显示排序 |
| leaderUserId | Long | 否 | - | 负责人用户ID |
| phone | String | 否 | @Mobile | 联系电话 |
| email | String | 否 | @Email | 邮箱 |
| status | Integer | 否 | - | 状态（0正常 1停用），默认正常 |

**响应**: `CommonResult<Long>` — 返回部门ID

**业务逻辑**:
1. 校验父部门是否存在
2. 校验部门名称在同级下是否唯一
3. 插入部门记录

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_004_000 | 已经存在该名字的部门 |
| 1_002_004_001 | 父部门不存在 |

## 2. 更新部门

- **路径**: `PUT /system/dept/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:dept:update')")`

**请求参数 (DeptSaveReqVO)**: 同创建，额外包含 `id` 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 部门ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验部门是否存在
2. 不允许将自己设为自己的父部门（防止循环引用）
3. 校验部门名称在同级下是否唯一（排除自身）
4. 更新部门记录

## 3. 删除部门

- **路径**: `DELETE /system/dept/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:dept:delete')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 部门ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验部门是否存在
2. 检查是否有子部门，如有则拒绝删除
3. 检查是否有用户归属该部门，如有则拒绝删除
4. 逻辑删除部门记录

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_004_002 | 存在子部门，不允许删除 |
| 1_002_004_003 | 部门下存在用户，不允许删除 |

## 4. 获取部门详情

- **路径**: `GET /system/dept/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:dept:query')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 部门ID |

**响应**: `CommonResult<DeptRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 部门ID |
| name | String | 部门名称 |
| parentId | Long | 父部门ID |
| sort | Integer | 排序 |
| leaderUserId | Long | 负责人用户ID |
| leaderUserName | String | 负责人姓名 |
| phone | String | 联系电话 |
| email | String | 邮箱 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

## 5. 获取部门列表

- **路径**: `GET /system/dept/get-list`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:dept:query')")`

**请求参数 (DeptListReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 部门名称（模糊查询） |
| leaderUserId | Long | 否 | 负责人 |
| status | Integer | 否 | 状态 |

**响应**: `CommonResult<List<DeptRespVO>>`

**说明**: 返回所有部门的平铺列表，前端自行组装为树形结构。

## 6. 获取部门精简列表

- **路径**: `GET /system/dept/get-simple-list`
- **权限**: 已认证（无需特殊权限）
- **说明**: 返回部门精简信息，用于下拉树形选择器

**请求参数**: 无

**响应**: `CommonResult<List<DeptSimpleRespVO>>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 部门ID |
| name | String | 部门名称 |
| parentId | Long | 父部门ID |

---

## 7. 跨模块 API 接口 (DeptApi)

### 7.1 获取部门

- **接口**: `DeptApi.getDept(Long id)`
- **返回**: `DeptRespDTO`
- **消费方**: yudao-module-infra

### 7.2 批量获取部门

- **接口**: `DeptApi.getDeptList(Collection<Long> ids)`
- **返回**: `List<DeptRespDTO>`
- **消费方**: yudao-module-infra

---

## 8. 岗位管理接口 (PostController)

接口路径前缀: `/system/post`

### 8.1 创建岗位

- **路径**: `POST /system/post/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:post:create')")`

**请求参数 (PostSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| name | String | 是 | @NotBlank @Size(2,50) | 岗位名称 |
| code | String | 是 | @NotBlank @Size(2,64) | 岗位编码 |
| sort | Integer | 是 | @NotNull | 显示排序 |
| status | Integer | 否 | - | 状态（0正常 1停用） |
| remark | String | 否 | - | 备注 |

**响应**: `CommonResult<Long>` — 返回岗位ID

### 8.2 更新岗位

- **路径**: `PUT /system/post/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:post:update')")`

**请求参数**: 同创建，额外包含 `id`

**响应**: `CommonResult<Boolean>`

### 8.3 删除岗位

- **路径**: `DELETE /system/post/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:post:delete')")`

**请求参数**: `id` (Long)

**响应**: `CommonResult<Boolean>`

### 8.4 获取岗位详情

- **路径**: `GET /system/post/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:post:query')")`

**请求参数**: `id` (Long)

**响应**: `CommonResult<PostRespVO>`

### 8.5 获取岗位分页列表

- **路径**: `POST /system/post/get-page`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:post:query')")`

**请求参数 (PostPageReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |
| name | String | 否 | 岗位名称 |
| code | String | 否 | 岗位编码 |
| status | Integer | 否 | 状态 |

**响应**: `CommonResult<PageResult<PostRespVO>>`

### 8.6 获取岗位精简列表

- **路径**: `GET /system/post/get-simple-list`
- **权限**: 已认证
- **说明**: 返回状态正常的岗位列表，用于下拉选择

**响应**: `CommonResult<List<PostSimpleRespVO>>`

### 8.7 跨模块 API (PostApi)

- `PostApi.getPost(Long id)` — 获取岗位信息
- `PostApi.getPostList(Collection<Long> ids)` — 批量获取岗位
