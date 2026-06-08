# 用户管理接口 (UserController)

> 管理后台用户的增删改查、密码管理、状态控制，以及认证相关接口。

## 接口路径前缀

`/system/user`  (Controller: `UserController`)

---

## 1. 用户认证接口 (AuthController)

接口路径前缀: `/system/auth`

### 1.1 用户登录

- **路径**: `POST /system/auth/login`
- **权限**: `@PermitAll` (匿名访问)
- **说明**: 使用账号密码获取访问令牌

**请求参数 (AuthLoginReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| username | String | 是 | @NotBlank | 用户账号 |
| password | String | 是 | @NotBlank | 密码（明文，后端加密比对） |

**响应**: `CommonResult<AuthLoginRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| accessToken | String | 访问令牌 |
| refreshToken | String | 刷新令牌 |
| expiresTime | LocalDateTime | 过期时间 |

**业务逻辑**:
1. 校验用户名密码是否正确
2. 检查用户状态是否正常
3. 检查所属租户是否有效（未过期、未禁用）
4. 生成 OAuth2 访问令牌和刷新令牌
5. 记录登录日志
6. 返回令牌信息

**错误码**:
| 错误码 | 说明 |
|--------|------|
| 1_002_000_000 | 登录失败，账号密码不正确 |
| 1_002_000_002 | 用户已被禁用 |
| 1_002_015_002 | 租户已被禁用 |
| 1_002_015_003 | 租户已过期 |

### 1.2 用户登出

- **路径**: `POST /system/auth/logout`
- **权限**: 已认证
- **说明**: 清除当前用户的令牌

**请求参数**: 无（从请求头获取令牌）

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 从请求头提取访问令牌
2. 删除 Redis 中的令牌缓存
3. 记录登出日志

### 1.3 刷新令牌

- **路径**: `POST /system/auth/refresh-token`
- **权限**: `@PermitAll`
- **说明**: 使用刷新令牌获取新的访问令牌

**请求参数 (AuthRefreshTokenReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refreshToken | String | 是 | 刷新令牌 |

**响应**: `CommonResult<AuthLoginRespVO>` (同登录响应)

### 1.4 获取权限信息

- **路径**: `GET /system/auth/get-permission-info`
- **权限**: 已认证
- **说明**: 获取当前登录用户的权限集合

**请求参数**: 无

**响应**: `CommonResult<AuthPermissionInfoRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| user | AdminUserRespVO | 用户基本信息 |
| roles | Set\<String\> | 角色标识集合 |
| permissions | Set\<String\> | 权限标识集合 |

**业务逻辑**:
1. 根据用户ID查询关联的角色列表
2. 根据角色列表查询关联的菜单权限
3. 组装权限标识集合
4. 返回用户信息和权限数据

---

## 2. 用户管理接口

### 2.1 创建用户

- **路径**: `POST /system/user/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:create')")`
- **说明**: 创建新的后台用户

**请求参数 (UserSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| username | String | 是 | @NotBlank @Size(4,30) | 用户账号 |
| password | String | 是 | @NotBlank @Size(5,30) | 密码 |
| nickname | String | 是 | @NotBlank @Size(2,30) | 用户昵称 |
| deptId | Long | 是 | @NotNull | 部门ID |
| postIds | Set\<Long\> | 否 | - | 岗位编号数组 |
| email | String | 否 | @Email | 邮箱 |
| mobile | String | 否 | @Mobile | 手机号码 |
| sex | Integer | 否 | - | 性别（0男 1女 2未知） |
| remark | String | 否 | - | 备注 |
| status | Integer | 否 | - | 状态（0正常 1停用） |

**响应**: `CommonResult<Long>` — 返回用户ID

**业务逻辑**:
1. 校验用户名在当前租户下是否唯一（uk_username 唯一索引）
2. 手机号在当前租户下是否唯一（uk_mobile 唯一索引）
3. 校验部门是否存在且状态正常
4. 密码加密存储（BCrypt）
5. 插入用户记录
6. 批量插入用户-角色关联（如有）
7. 批量插入用户-岗位关联（如有）

**错误码**:
| 错误码 | 说明 |
|--------|------|
| 1_002_003_000 | 用户账号已经存在 |
| 1_002_003_001 | 手机号已存在 |
| 1_002_004_001 | 部门不存在 |

### 2.2 更新用户

- **路径**: `PUT /system/user/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:update')")`
- **说明**: 更新用户信息

**请求参数 (UserSaveReqVO)**: 同创建，额外包含 `id` 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 用户ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验用户是否存在
2. 校验用户名/手机号是否与其他用户冲突（排除自身）
3. 更新用户基本信息
4. 重建用户-角色关联（先删后增）
5. 重建用户-岗位关联（先删后增）

### 2.3 删除用户

- **路径**: `DELETE /system/user/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:delete')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 用户ID |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验用户是否存在
2. 逻辑删除用户记录（deleted = 1）
3. 清理用户-角色关联
4. 清理用户-岗位关联

### 2.4 获取用户详情

- **路径**: `GET /system/user/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:query')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 用户ID |

**响应**: `CommonResult<UserRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户ID |
| username | String | 用户账号 |
| nickname | String | 用户昵称 |
| deptId | Long | 部门ID |
| deptName | String | 部门名称 |
| postIds | Set\<Long\> | 岗位编号数组 |
| email | String | 邮箱 |
| mobile | String | 手机号 |
| sex | Integer | 性别 |
| avatar | String | 头像URL |
| status | Integer | 状态 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

### 2.5 获取用户分页列表

- **路径**: `POST /system/user/get-page`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:query')")`

**请求参数 (UserPageReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |
| username | String | 否 | 用户账号（模糊查询） |
| mobile | String | 否 | 手机号（模糊查询） |
| status | Integer | 否 | 状态 |
| deptId | Long | 否 | 部门ID |
| createTime | LocalDateTime[] | 否 | 创建时间范围 |

**响应**: `CommonResult<PageResult<UserRespVO>>`

**业务逻辑**:
1. 应用数据权限注解（@DataPermission），根据当前用户的数据权限范围过滤
2. 支持按部门查询时自动包含子部门数据
3. 返回分页结果

### 2.6 导出用户

- **路径**: `POST /system/user/export`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:export')")`

**请求参数**: 同分页查询参数（不含分页字段）

**响应**: Excel 文件流

### 2.7 重置密码

- **路径**: `PUT /system/user/update-password`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:user:update-password')")`

**请求参数 (UserUpdatePasswordReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 是 | @NotNull | 用户ID |
| password | String | 是 | @NotBlank @Size(5,30) | 新密码 |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验用户是否存在
2. 加密新密码
3. 更新数据库中的密码字段

### 2.8 修改个人信息

- **路径**: `PUT /system/user/update-profile`
- **权限**: 已认证（仅修改自己）

**请求参数 (UserProfileUpdateReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | String | 否 | 用户昵称 |
| email | String | 否 | 邮箱 |
| mobile | String | 否 | 手机号 |
| sex | Integer | 否 | 性别 |

**响应**: `CommonResult<Boolean>`

### 2.9 修改头像

- **路径**: `PUT /system/user/update-avatar`
- **权限**: 已认证

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| avatarFile | MultipartFile | 是 | 头像文件 |

**响应**: `CommonResult<String>` — 返回头像URL

**业务逻辑**:
1. 调用 FileApi 上传头像文件
2. 更新用户头像URL

---

## 3. 跨模块 API 接口 (AdminUserApi)

供其他模块 RPC 调用，不暴露为 HTTP 接口。

### 3.1 获取用户

- **接口**: `AdminUserApi.getUser(Long id)`
- **返回**: `AdminUserRespDTO`
- **消费方**: yudao-module-infra, yudao-module-pay

### 3.2 批量获取用户

- **接口**: `AdminUserApi.getUserList(Collection<Long> ids)`
- **返回**: `List<AdminUserRespDTO>`
- **消费方**: yudao-module-infra
