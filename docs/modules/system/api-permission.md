# 权限管理接口（RoleController / MenuController / PermissionController）

> 提供 RBAC 权限模型的三大能力：角色管理（角色的增删改查、导出）、菜单管理（菜单/按钮资源的维护）、权限分配（角色-菜单授权、用户-角色授权、角色数据范围设置）。

## 接口路径前缀

- /system/role  (Controller: RoleController)
- /system/menu  (Controller: MenuController)
- /system/permission  (Controller: PermissionController)

---

## 1. 角色管理（RoleController）

### 1.1 创建角色

- **路径**: POST /system/role/create
- **权限**: system:role:create
- **说明**: 创建自定义类型角色，默认开启状态、数据范围为全部数据。

**请求参数 (RoleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 角色编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=30) | 角色名称 |
| code | String | 是 | @NotBlank、@Size(max=100) | 角色标志 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 禁用） |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult\<Long\>（角色编号）

**业务逻辑**:
1. 校验角色唯一性：code 不能是超级管理员标识 super_admin，否则抛出"标识不能使用"错误。
2. 校验角色名称未被其它角色使用、角色编码未被其它角色使用（编码为空时跳过编码校验）。
3. 转换为 RoleDO 并设置默认值：type 默认为 CUSTOM（自定义角色），status 缺省为开启，dataScope 默认为 ALL（可查看所有数据，兼容不需要数据权限的项目）。
4. 插入数据库，记录操作日志上下文，返回角色编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_002_005 | 标识【{}】不能使用（超级管理员编码） |
| 1_002_002_001 | 已经存在名为【{}】的角色 |
| 1_002_002_002 | 已经存在标识为【{}】的角色 |

### 1.2 修改角色

- **路径**: PUT /system/role/update
- **权限**: system:role:update
- **说明**: 更新角色基本信息，同时清除该角色的缓存。

**请求参数 (RoleSaveReqVO)**: 同 1.1，id 更新时必传。

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 校验角色存在，且不是系统内置类型角色（SYSTEM 类型不允许修改）。
2. 校验角色名称、编码不与其它角色重复，编码不能为 super_admin。
3. 更新数据库，并通过 @CacheEvict 清除 Redis 中该角色的缓存。
4. 记录操作日志（对比修改前后的角色数据）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_002_000 | 角色不存在 |
| 1_002_002_003 | 不能操作类型为系统内置的角色 |
| 1_002_002_005 | 标识【{}】不能使用 |
| 1_002_002_001 | 已经存在名为【{}】的角色 |
| 1_002_002_002 | 已经存在标识为【{}】的角色 |

### 1.3 删除角色

- **路径**: DELETE /system/role/delete
- **权限**: system:role:delete
- **说明**: 删除单个角色，并级联清理其关联的用户-角色、角色-菜单数据。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 角色编号 |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 校验角色存在，且不是系统内置类型角色。
2. 标记删除角色记录，并清除该角色的缓存。
3. 级联调用 PermissionService.processRoleDeleted：删除该角色的所有用户-角色关联（user_role）和角色-菜单关联（role_menu）。
4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_002_000 | 角色不存在 |
| 1_002_002_003 | 不能操作类型为系统内置的角色 |

### 1.4 批量删除角色

- **路径**: DELETE /system/role/delete-list
- **权限**: system:role:delete
- **说明**: 批量删除多个角色，逻辑同单个删除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List\<Long\> | 是 | @RequestParam | 角色编号列表 |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 逐个校验每个角色存在，且不是系统内置类型角色。
2. 批量标记删除角色记录。
3. 逐个级联删除角色的用户-角色、角色-菜单关联数据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_002_000 | 角色不存在 |
| 1_002_002_003 | 不能操作类型为系统内置的角色 |

### 1.5 获得角色信息

- **路径**: GET /system/role/get
- **权限**: system:role:query
- **说明**: 按编号查询单个角色详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 角色编号 |

**响应**: CommonResult\<RoleRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 角色编号 |
| name | String | 角色名称 |
| code | String | 角色标志 |
| sort | Integer | 显示顺序 |
| status | Integer | 状态（CommonStatusEnum） |
| type | Integer | 角色类型（RoleTypeEnum：1 系统 / 2 自定义） |
| remark | String | 备注 |
| dataScope | Integer | 数据范围（DataScopeEnum） |
| dataScopeDeptIds | Set\<Long\> | 数据范围（指定部门数组） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按主键查询角色记录。
2. 转换为 RoleRespVO 返回。

### 1.6 获得角色分页

- **路径**: GET /system/role/page
- **权限**: system:role:query
- **说明**: 分页查询角色列表，支持名称/编码模糊匹配。

**请求参数 (RolePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承自 PageParam，默认 1） |
| pageSize | Integer | 否 | - | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | - | 角色名称，模糊匹配 |
| code | String | 否 | - | 角色标志，模糊匹配 |
| status | Integer | 否 | - | 展示状态（CommonStatusEnum） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<RoleRespVO\>\>，列表元素字段同 1.5 的 RoleRespVO。

**业务逻辑**:
1. 按查询条件（名称模糊、编码模糊、状态、创建时间区间）执行分页查询。
2. 分页结果转换为 RoleRespVO 列表返回。

### 1.7 获取角色精简信息列表

- **路径**: GET /system/role/list-all-simple（别名 /system/role/simple-list）
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 只包含开启状态的角色，按 sort 升序排列，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult\<List\<RoleRespVO\>\>，元素字段同 1.5 的 RoleRespVO。

**业务逻辑**:
1. 查询状态为开启（ENABLE）的所有角色。
2. 按显示顺序 sort 升序排序后返回。

### 1.8 导出角色 Excel

- **路径**: GET /system/role/export-excel
- **权限**: system:role:export
- **说明**: 按分页条件导出全量角色数据为 Excel 文件，记录导出操作日志。

**请求参数 (RolePageReqVO)**: 同 1.6（pageSize 被强制置为 PAGE_SIZE_NONE，即不分页查全量）。

**响应**: Excel 文件流（角色数据.xls），列由 RoleRespVO 上的 @ExcelProperty 注解决定（角色序号、角色名称、角色标志、角色排序、角色状态、数据范围）。

**业务逻辑**:
1. 将查询条件的 pageSize 设置为 PAGE_SIZE_NONE，查询全量角色。
2. 通过 ExcelUtils 按RoleRespVO 的 Excel 注解配置写出文件到响应流。

---

## 2. 菜单管理（MenuController）

### 2.1 创建菜单

- **路径**: POST /system/menu/create
- **权限**: system:menu:create
- **说明**: 创建目录/菜单/按钮类型的菜单资源。

**请求参数 (MenuSaveVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 菜单编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=50) | 菜单名称 |
| permission | String | 否 | @Size(max=100) | 权限标识，仅菜单类型为按钮时需要传递 |
| type | Integer | 是 | @NotNull | 类型（MenuTypeEnum：1 目录 / 2 菜单 / 3 按钮） |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| parentId | Long | 是 | @NotNull | 父菜单 ID（0 表示根节点） |
| path | String | 否 | @Size(max=200) | 路由地址，仅目录或菜单类型需要传 |
| icon | String | 否 | - | 菜单图标，仅目录或菜单类型需要传 |
| component | String | 否 | @Size(max=200) | 组件路径，仅菜单类型需要传 |
| componentName | String | 否 | - | 组件名 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum） |
| visible | Boolean | 否 | - | 是否可见 |
| keepAlive | Boolean | 否 | - | 是否缓存 |
| alwaysShow | Boolean | 否 | - | 是否总是显示 |

**响应**: CommonResult\<Long\>（菜单编号）

**业务逻辑**:
1. 校验父菜单合法：不能设置自己为父菜单，父菜单必须存在，且父菜单类型必须是目录或菜单。
2. 校验同一父菜单下菜单名称不重复。
3. 校验组件名（componentName）不重复（为空时跳过）。
4. 初始化菜单属性：按钮类型菜单将 component、componentName、icon、path 置空。
5. 插入数据库；若携带 permission 权限标识，则清除对应的菜单权限缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_001_002 | 不能设置自己为父菜单 |
| 1_002_001_001 | 父菜单不存在 |
| 1_002_001_005 | 父菜单的类型必须是目录或者菜单 |
| 1_002_001_000 | 已经存在该名字的菜单 |
| 1_002_001_006 | 已经存在该组件名的菜单 |

### 2.2 修改菜单

- **路径**: PUT /system/menu/update
- **权限**: system:menu:update
- **说明**: 更新菜单信息，清空全部菜单权限缓存。

**请求参数 (MenuSaveVO)**: 同 2.1，id 更新时必传。

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 校验待更新的菜单存在。
2. 校验父菜单合法（不能是自己、父菜单存在、类型必须是目录或菜单）。
3. 校验同一父菜单下菜单名称不重复、组件名不重复。
4. 初始化菜单属性（按钮类型清空 component/componentName/icon/path）。
5. 更新数据库，并通过 @CacheEvict 清空所有菜单权限缓存（permission 变更涉及新老两个标识，统一全清）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_001_003 | 菜单不存在 |
| 1_002_001_002 | 不能设置自己为父菜单 |
| 1_002_001_001 | 父菜单不存在 |
| 1_002_001_005 | 父菜单的类型必须是目录或者菜单 |
| 1_002_001_000 | 已经存在该名字的菜单 |
| 1_002_001_006 | 已经存在该组件名的菜单 |

### 2.3 删除菜单

- **路径**: DELETE /system/menu/delete
- **权限**: system:menu:delete
- **说明**: 删除单个菜单，存在子菜单时禁止删除，并级联清理角色授权。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 菜单编号 |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 校验该菜单下不存在子菜单，否则抛出"存在子菜单，无法删除"。
2. 校验菜单存在。
3. 标记删除菜单记录。
4. 级联调用 PermissionService.processMenuDeleted：删除授予给各角色的该菜单关联（role_menu）。
5. 清空所有菜单权限缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_001_004 | 存在子菜单，无法删除 |
| 1_002_001_003 | 菜单不存在 |

### 2.4 批量删除菜单

- **路径**: DELETE /system/menu/delete-list
- **权限**: system:menu:delete
- **说明**: 批量删除多个菜单，逻辑同单个删除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List\<Long\> | 是 | @RequestParam | 菜单编号列表 |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 逐个校验每个菜单下不存在子菜单。
2. 批量标记删除菜单记录。
3. 逐个级联删除各菜单的角色-菜单关联数据。
4. 清空所有菜单权限缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_001_004 | 存在子菜单，无法删除 |

### 2.5 获取菜单列表

- **路径**: GET /system/menu/list
- **权限**: system:menu:query
- **说明**: 查询全部菜单（支持名称/状态过滤），用于【菜单管理】界面。

**请求参数 (MenuListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 菜单名称，模糊匹配 |
| status | Integer | 否 | - | 展示状态（CommonStatusEnum） |

**响应**: CommonResult\<List\<MenuRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 菜单编号 |
| name | String | 菜单名称 |
| permission | String | 权限标识 |
| type | Integer | 类型（MenuTypeEnum） |
| sort | Integer | 显示顺序 |
| parentId | Long | 父菜单 ID |
| path | String | 路由地址 |
| icon | String | 菜单图标 |
| component | String | 组件路径 |
| componentName | String | 组件名 |
| status | Integer | 状态 |
| visible | Boolean | 是否可见 |
| keepAlive | Boolean | 是否缓存 |
| alwaysShow | Boolean | 是否总是显示 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按名称模糊、状态条件查询菜单列表。
2. 按显示顺序 sort 升序排序后返回。

### 2.6 获取菜单精简信息列表

- **路径**: GET /system/menu/list-all-simple（别名 /system/menu/simple-list）
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 只包含开启状态的菜单，用于【角色分配菜单】的选项；多租户场景下只返回租户套餐包含的菜单。

**请求参数**: 无

**响应**: CommonResult\<List\<MenuSimpleRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 菜单编号 |
| name | String | 菜单名称 |
| parentId | Long | 父菜单 ID |
| type | Integer | 类型（MenuTypeEnum） |

**业务逻辑**:
1. 查询状态为开启的菜单列表，并过滤掉租户套餐未开通的菜单（多租户场景）。
2. 递归过滤掉自身或任一祖先被禁用的菜单（父级禁用则子级一并剔除）。
3. 按显示顺序 sort 升序排序后返回。

### 2.7 获取菜单信息

- **路径**: GET /system/menu/get
- **权限**: system:menu:query
- **说明**: 按编号查询单个菜单详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 菜单编号 |

**响应**: CommonResult\<MenuRespVO\>，字段同 2.5。

**业务逻辑**:
1. 按主键查询菜单记录。
2. 转换为 MenuRespVO 返回。

---

## 3. 权限分配（PermissionController）

### 3.1 获得角色拥有的菜单编号

- **路径**: GET /system/permission/list-role-menus
- **权限**: system:permission:assign-role-menu
- **说明**: 查询指定角色已勾选的菜单编号集合，用于角色分配菜单界面的回显。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| roleId | Long | 是 | @RequestParam | 角色编号 |

**响应**: CommonResult\<Set\<Long\>\>（菜单编号集合）

**业务逻辑**:
1. 若角色列表中包含超级管理员角色，则返回系统全部菜单编号。
2. 否则查询 role_menu 关联表，返回该角色拥有的菜单编号集合。

### 3.2 赋予角色菜单

- **路径**: POST /system/permission/assign-role-menu
- **权限**: system:permission:assign-role-menu
- **说明**: 全量设置角色拥有的菜单，采用差集计算增量更新。

**请求参数 (PermissionAssignRoleMenuReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| roleId | Long | 是 | @NotNull | 角色编号 |
| menuIds | Set\<Long\> | 否 | - | 菜单编号列表（默认空集合） |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 开启多租户时，通过 TenantService.handleTenantMenu 过滤掉租户套餐未开通的菜单编号。
2. 查询该角色在 role_menu 表中已有的菜单编号，与传入的 menuIds 计算差集，得到需新增和需删除的菜单。
3. 批量插入新增的 role_menu 关联记录、删除取消的关联记录（两边都有的菜单不做任何处理）。
4. 清空 MENU_ROLE_ID_LIST 与 PERMISSION_MENU_ID_LIST 两类缓存。

**错误码**: 无该域专属错误码（参数校验失败由全局异常处理）。

### 3.3 赋予角色数据权限

- **路径**: POST /system/permission/assign-role-data-scope
- **权限**: system:permission:assign-role-data-scope
- **说明**: 设置角色的数据权限范围（全部/自定义部门/本部门/本部门及以下/仅本人）。

**请求参数 (PermissionAssignRoleDataScopeReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| roleId | Long | 是 | @NotNull | 角色编号 |
| dataScope | Integer | 是 | @NotNull、@InEnum(DataScopeEnum) | 数据范围（DataScopeEnum：1 全部 / 2 自定义部门 / 3 本部门 / 4 本部门及以下 / 5 仅本人） |
| dataScopeDeptIds | Set\<Long\> | 否 | - | 部门编号列表，仅 dataScope 为自定义部门（DEPT_CUSTOM）时需要（默认空集合） |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 委托 RoleService.updateRoleDataScope 执行。
2. 校验角色存在，且不是系统内置类型角色。
3. 更新角色的 dataScope 与 dataScopeDeptIds 字段到数据库。
4. 清除该角色的 Redis 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_002_000 | 角色不存在 |
| 1_002_002_003 | 不能操作类型为系统内置的角色 |

### 3.4 获得管理员拥有的角色编号列表

- **路径**: GET /system/permission/list-user-roles
- **权限**: system:permission:assign-user-role
- **说明**: 查询指定用户已分配的角色编号集合，用于用户分配角色界面的回显。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @RequestParam | 用户编号 |

**响应**: CommonResult\<Set\<Long\>\>（角色编号集合）

**业务逻辑**:
1. 查询 user_role 关联表，返回该用户拥有的角色编号集合。

### 3.5 赋予用户角色

- **路径**: POST /system/permission/assign-user-role
- **权限**: system:permission:assign-user-role
- **说明**: 全量设置用户拥有的角色，采用差集计算增量更新。

**请求参数 (PermissionAssignUserRoleReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 用户编号 |
| roleIds | Set\<Long\> | 否 | - | 角色编号列表（默认空集合） |

**响应**: CommonResult\<Boolean\>（固定 true）

**业务逻辑**:
1. 查询该用户在 user_role 表中已有的角色编号，与传入的 roleIds 计算差集，得到需新增和需删除的角色。
2. 批量插入新增的 user_role 关联记录、删除取消的关联记录（两边都有的角色不做任何处理）。
3. 清除该用户的 USER_ROLE_ID_LIST 缓存。

**错误码**: 无该域专属错误码（参数校验失败由全局异常处理）。
