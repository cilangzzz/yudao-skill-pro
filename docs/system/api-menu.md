# 菜单权限接口 (MenuController)

> 菜单是权限的最小单元，支持目录、菜单、按钮三种类型，通过角色-菜单关联实现功能权限控制。

## 接口路径前缀

`/system/menu`  (Controller: `MenuController`)

---

## 1. 创建菜单

- **路径**: `POST /system/menu/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:menu:create')")`
- **说明**: 创建新的菜单节点

**请求参数 (MenuSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| name | String | 是 | @NotBlank @Size(2,50) | 菜单名称 |
| permission | String | 否 | @Size(2,100) | 权限标识（如 system:user:create） |
| type | Integer | 是 | @NotNull | 菜单类型（1目录 2菜单 3按钮） |
| sort | Integer | 是 | @NotNull | 显示排序 |
| parentId | Long | 否 | - | 父菜单ID（为空则为顶级） |
| path | String | 否 | @Size(0,200) | 路由地址（目录/菜单类型需填） |
| icon | String | 否 | @Size(0,100) | 菜单图标 |
| component | String | 否 | @Size(0,255) | 组件路径 |
| componentName | String | 否 | @Size(0,100) | 组件名称 |
| status | Integer | 否 | - | 状态（0正常 1停用） |
| visible | Boolean | 否 | - | 是否可见（默认true） |
| keepAlive | Boolean | 否 | - | 是否缓存（默认true） |
| alwaysShow | Boolean | 否 | - | 是否总是显示 |

**响应**: `CommonResult<Long>` — 返回菜单ID

**业务逻辑**:
1. 校验父菜单是否存在（如果指定了 parentId）
2. 校验菜单名称在同级下是否唯一
3. 校验权限标识是否全局唯一（如有）
4. 插入菜单记录

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_001_000 | 已经存在该名字的菜单 |
| 1_002_001_001 | 父菜单不存在 |
| 1_002_001_002 | 权限标识已存在 |

## 2. 更新菜单

- **路径**: `PUT /system/menu/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:menu:update')")`

**请求参数 (MenuSaveReqVO)**: 同创建，额外包含 `id` 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 菜单ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验菜单是否存在
2. 不允许将自己设为自己的父菜单（防止循环引用）
3. 校验名称和权限标识唯一性（排除自身）
4. 更新菜单记录

## 3. 删除菜单

- **路径**: `DELETE /system/menu/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:menu:delete')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 菜单ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验菜单是否存在
2. 检查是否有子菜单，如有则拒绝删除（需先删除子菜单）
3. 逻辑删除菜单记录
4. 清理角色-菜单关联

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_001_003 | 存在子菜单，不允许删除 |

## 4. 获取菜单详情

- **路径**: `GET /system/menu/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:menu:query')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 菜单ID |

**响应**: `CommonResult<MenuRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 菜单ID |
| name | String | 菜单名称 |
| permission | String | 权限标识 |
| type | Integer | 菜单类型 |
| sort | Integer | 排序 |
| parentId | Long | 父菜单ID |
| path | String | 路由地址 |
| icon | String | 图标 |
| component | String | 组件路径 |
| componentName | String | 组件名 |
| status | Integer | 状态 |
| visible | Boolean | 是否可见 |
| keepAlive | Boolean | 是否缓存 |
| alwaysShow | Boolean | 是否总是显示 |
| createTime | LocalDateTime | 创建时间 |

## 5. 获取菜单列表

- **路径**: `GET /system/menu/get-list`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:menu:query')")`

**请求参数 (MenuListReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 菜单名称（模糊查询） |
| status | Integer | 否 | 状态 |

**响应**: `CommonResult<List<MenuRespVO>>`

**说明**: 返回所有菜单的平铺列表，前端自行组装为树形结构。

## 6. 获取菜单精简列表

- **路径**: `GET /system/menu/get-simple-list`
- **权限**: 已认证（无需特殊权限）
- **说明**: 返回菜单精简信息，用于下拉选择、树形选择器等

**请求参数**: 无

**响应**: `CommonResult<List<MenuSimpleRespVO>>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 菜单ID |
| name | String | 菜单名称 |
| parentId | Long | 父菜单ID |
| type | Integer | 菜单类型 |

---

## 7. 跨模块 API 接口 (PermissionApi)

### 7.1 校验权限

- **接口**: `PermissionApi.hasAnyPermissions(Long userId, String... permissions)`
- **返回**: `boolean`
- **说明**: 校验用户是否拥有指定权限中的任意一个
- **消费方**: yudao-module-infra, yudao-module-member

### 7.2 校验角色

- **接口**: `PermissionApi.hasAnyRoles(Long userId, String... roles)`
- **返回**: `boolean`
- **说明**: 校验用户是否拥有指定角色中的任意一个

### 7.3 获取用户角色ID列表

- **接口**: `PermissionApi.getUserRoleIdListByRoleIds(Collection<Long> roleIds)`
- **返回**: `Map<Long, Set<Long>>`
- **说明**: 根据角色ID列表查询关联的用户ID列表

---

## 菜单类型枚举 (MenuTypeEnum)

| 值 | 类型 | 说明 | 权限标识 | 路由 | 组件 |
|----|------|------|---------|------|------|
| 1 | DIR | 目录 | 可选 | 必填 | 选填 |
| 2 | MENU | 菜单 | 可选 | 必填 | 必填 |
| 3 | BUTTON | 按钮 | 必填 | - | - |

**权限标识命名规范**: `模块:功能:操作`，例如:
- `system:user:create` — 系统模块-用户功能-创建操作
- `system:role:update` — 系统模块-角色功能-更新操作
- `system:menu:delete` — 系统模块-菜单功能-删除操作
