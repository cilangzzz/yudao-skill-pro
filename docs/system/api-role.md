# 角色管理接口 (RoleController)

> 基于RBAC模型的角色定义与权限分配，控制用户可访问的功能菜单和数据范围。

## 接口路径前缀

`/system/role`  (Controller: `RoleController`)

---

## 1. 创建角色

- **路径**: `POST /system/role/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:create')")`
- **说明**: 创建新的角色

**请求参数 (RoleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| name | String | 是 | @NotBlank @Size(2,30) | 角色名称 |
| code | String | 是 | @NotBlank @Size(2,100) | 角色标识（如 admin、common） |
| sort | Integer | 是 | @NotNull | 显示排序 |
| status | Integer | 否 | - | 状态（0正常 1停用），默认正常 |
| type | Integer | 否 | - | 角色类型（1系统内置 2自定义） |
| remark | String | 否 | - | 备注 |

**响应**: `CommonResult<Long>` — 返回角色ID

**业务逻辑**:
1. 校验角色标识在当前租户下是否唯一（uk_code 唯一索引）
2. 校验角色名称在当前租户下是否唯一
3. 插入角色记录

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_002_001 | 角色标识已存在 |
| 1_002_002_002 | 角色名称已存在 |

## 2. 更新角色

- **路径**: `PUT /system/role/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:update')")`

**请求参数 (RoleSaveReqVO)**: 同创建，额外包含 `id` 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 角色ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验角色是否存在
2. 系统内置角色不允许修改标识
3. 校验标识和名称是否与其他角色冲突（排除自身）
4. 更新角色记录

## 3. 删除角色

- **路径**: `DELETE /system/role/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:delete')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 角色ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验角色是否存在
2. 系统内置角色不允许删除
3. 检查是否有用户关联该角色，如有则拒绝删除
4. 逻辑删除角色记录
5. 清理角色-菜单关联

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_002_003 | 系统内置角色不允许删除 |
| 1_002_002_004 | 角色下存在用户，不允许删除 |

## 4. 获取角色详情

- **路径**: `GET /system/role/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:query')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 角色ID |

**响应**: `CommonResult<RoleRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 角色ID |
| name | String | 角色名称 |
| code | String | 角色标识 |
| sort | Integer | 排序 |
| status | Integer | 状态 |
| type | Integer | 角色类型 |
| dataScope | Integer | 数据范围 |
| dataScopeDeptIds | Set\<Long\> | 数据范围（自定义）部门ID列表 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

## 5. 获取所有角色列表

- **路径**: `GET /system/role/get-all`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:query')")`

**请求参数**: 无

**响应**: `CommonResult<List<RoleRespVO>>`

**说明**: 返回所有状态正常的角色，用于下拉选择。

## 6. 获取角色分页列表

- **路径**: `POST /system/role/get-page`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:query')")`

**请求参数 (RolePageReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |
| name | String | 否 | 角色名称（模糊查询） |
| code | String | 否 | 角色标识（模糊查询） |
| status | Integer | 否 | 状态 |

**响应**: `CommonResult<PageResult<RoleRespVO>>`

## 7. 分配角色菜单

- **路径**: `PUT /system/role/assign-menu`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:assign-menu')")`
- **说明**: 为角色分配可访问的菜单权限

**请求参数 (RoleAssignMenuReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 角色ID |
| menuIds | Set\<Long\> | 是 | 菜单ID数组 |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验角色是否存在
2. 删除角色原有的菜单关联
3. 批量插入新的角色-菜单关联
4. 清除权限相关缓存（MENU_ROLE_ID_LIST、PERMISSION_MENU_ID_LIST）

**缓存操作**:
```java
@Caching(evict = {
    @CacheEvict(value = RedisKeyConstants.MENU_ROLE_ID_LIST, allEntries = true),
    @CacheEvict(value = RedisKeyConstants.PERMISSION_MENU_ID_LIST, allEntries = true)
})
```

## 8. 分配数据权限

- **路径**: `PUT /system/role/assign-data-scope`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:role:assign-data-scope')")`
- **说明**: 设置角色的数据权限范围

**请求参数 (RoleAssignDataScopeReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 角色ID |
| dataScope | Integer | 是 | 数据范围（1全部 2自定义 3本部门 4本部门及子部门 5仅本人） |
| dataScopeDeptIds | Set\<Long\> | 否 | 自定义部门ID列表（dataScope=2时必填） |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验角色是否存在
2. 更新角色的 dataScope 和 dataScopeDeptIds 字段
3. 清除权限相关缓存

**数据权限范围 (DataScopeEnum)**:

| 值 | 枚举 | 说明 |
|----|------|------|
| 1 | ALL | 全部数据权限 |
| 2 | DEPT_CUSTOM | 自定义部门数据权限 |
| 3 | DEPT_ONLY | 本部门数据权限 |
| 4 | DEPT_AND_CHILD | 本部门及子部门数据权限 |
| 5 | SELF_ONLY | 仅本人数据权限 |

---

## 9. 跨模块 API 接口 (RoleApi)

### 9.1 获取角色

- **接口**: `RoleApi.getRole(Long id)`
- **返回**: `RoleRespDTO`

### 9.2 批量获取角色

- **接口**: `RoleApi.getRoleList(Collection<Long> ids)`
- **返回**: `List<RoleRespDTO>`
