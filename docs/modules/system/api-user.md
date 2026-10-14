# 用户管理接口 (UserController / UserProfileController)

> 提供管理后台用户账号的全生命周期管理（增删改查、密码重置、状态管理、Excel 导入导出）以及登录用户个人中心（个人资料、个人密码）能力。

## 接口路径前缀

- `/system/user`  (Controller: UserController)
- `/system/user/profile`  (Controller: UserProfileController)

---

## 1. 用户管理（UserController，前缀 /system/user）

### 1.1 新增用户

- **路径**: POST /system/user/create
- **权限**: system:user:create
- **说明**: 创建后台用户账号，密码加密存储，默认状态为开启。

**请求参数 (UserSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 用户编号（新增时不传） |
| username | String | 是 | @NotBlank、@Pattern(`^[a-zA-Z0-9]{4,30}$`)、@Size(min=4, max=30) | 用户账号，由数字、字母组成，长度 4-30 |
| nickname | String | 否 | @Size(max=30) | 用户昵称，不超过 30 字符 |
| remark | String | 否 | - | 备注 |
| deptId | Long | 否 | - | 部门编号 |
| postIds | Set\<Long\> | 否 | - | 岗位编号数组 |
| email | String | 否 | @Email、@Size(max=50) | 用户邮箱 |
| mobile | String | 否 | @Mobile | 手机号码 |
| sex | Integer | 否 | - | 用户性别，参见 SexEnum 枚举类 |
| avatar | String | 否 | - | 用户头像 |
| password | String | 创建必填 | @Length(min=4, max=16)、@AssertTrue（新增时必须传递） | 密码，长度 4-16 位 |

**响应**: CommonResult\<Long\>（新用户编号）

**业务逻辑**:
1. 校验租户账户配额：当前用户数达到租户 accountCount 上限时抛出 USER_COUNT_MAX 异常。
2. 校验正确性（在关闭数据权限的上下文中执行）：用户名唯一、手机号唯一、邮箱唯一、部门处于开启状态、岗位处于开启状态。
3. 插入用户记录：状态默认置为开启（ENABLE），密码加密后存储。
4. 若岗位编号数组非空，批量插入用户-岗位关联（user_post）。
5. 记录操作日志上下文（LogRecord 操作日志）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_000 | 用户账号已经存在 |
| 1_002_003_001 | 手机号已经存在 |
| 1_002_003_002 | 邮箱已经存在 |
| 1_002_003_008 | 创建用户失败，原因：超过租户最大租户配额({})！ |

### 1.2 修改用户

- **路径**: PUT /system/user/update
- **权限**: system:user:update
- **说明**: 修改用户基本信息与岗位，不更新密码。

**请求参数 (UserSaveReqVO)**: 同 1.1（id 必传，password 不生效）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 强制将 password 置空，保证本接口不更新密码。
2. 校验正确性：用户存在、用户名唯一、手机号唯一、邮箱唯一、部门开启、岗位开启。
3. 更新用户记录。
4. 差量更新用户-岗位关联：计算新增与删除的岗位编号，分别插入/删除。
5. 昵称或头像发生变化时，发送 AdminUserProfileUpdateMessage 消息供下游订阅（如 IM 模块推送好友信息变更）。
6. 记录操作日志（新旧数据 diff）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_000 | 用户账号已经存在 |
| 1_002_003_001 | 手机号已经存在 |
| 1_002_003_002 | 邮箱已经存在 |
| 1_002_003_003 | 用户不存在 |

### 1.3 删除用户

- **路径**: DELETE /system/user/delete
- **权限**: system:user:delete
- **说明**: 根据 id 删除单个用户及其关联数据。

**请求参数**: Query 参数 id（Long，用户编号，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验用户存在。
2. 校验该用户不是超级管理员或租户管理员（拥有 super_admin / tenant_admin 角色）。
3. 删除用户记录。
4. 删除用户关联数据（权限信息，permissionService.processUserDeleted）。
5. 删除用户-岗位关联。
6. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_003 | 用户不存在 |
| 1_002_003_013 | 超级管理员或租户管理员账号不能删除 |

### 1.4 批量删除用户

- **路径**: DELETE /system/user/delete-list
- **权限**: system:user:delete
- **说明**: 根据编号列表批量删除用户及关联数据。

**请求参数**: Query 参数 ids（List\<Long\>，用户编号列表，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 逐个校验待删除用户均不是超级管理员或租户管理员。
2. 批量删除用户记录。
3. 在事务内逐个删除用户权限关联数据与用户-岗位关联。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_013 | 超级管理员或租户管理员账号不能删除 |

### 1.5 重置用户密码

- **路径**: PUT /system/user/update-password
- **权限**: system:user:update-password
- **说明**: 管理员为指定用户重置密码（无需旧密码）。

**请求参数 (UserUpdatePasswordReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| password | String | 是 | @NotEmpty、@Length(min=4, max=16) | 新密码，长度 4-16 位 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验用户存在。
2. 新密码加密后更新用户记录。
3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_003 | 用户不存在 |

### 1.6 修改用户状态

- **路径**: PUT /system/user/update-status
- **权限**: system:user:update
- **说明**: 开启/禁用用户账号；禁用时强制下线。

**请求参数 (UserUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum)、@InDict(COMMON_STATUS) | 状态，见 CommonStatusEnum 枚举 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验用户存在。
2. 若为禁用操作，校验该用户不是超级管理员或租户管理员。
3. 更新用户状态。
4. 若为禁用操作，删除该用户 admin 端的 OAuth2 访问令牌（强制下线）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_003 | 用户不存在 |
| 1_002_003_012 | 超级管理员或租户管理员账号不能禁用 |

### 1.7 获得用户分页列表

- **路径**: GET /system/user/page
- **权限**: system:user:query
- **说明**: 分页查询用户，支持多条件筛选，结果拼接部门信息。

**请求参数 (UserPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，最大 200，默认 10 |
| username | String | 否 | - | 用户账号，模糊匹配 |
| mobile | String | 否 | - | 手机号码，模糊匹配 |
| status | Integer | 否 | - | 展示状态，参见 CommonStatusEnum 枚举类 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |
| deptId | Long | 否 | - | 部门编号，同时筛选子部门 |
| roleId | Long | 否 | - | 角色编号，筛选拥有该角色的用户 |

**响应**: CommonResult\<PageResult\<UserRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 用户编号 |
| username | String | 用户账号 |
| nickname | String | 用户昵称 |
| remark | String | 备注 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称（拼接） |
| postIds | Set\<Long\> | 岗位编号数组 |
| email | String | 用户邮箱 |
| mobile | String | 手机号码 |
| sex | Integer | 用户性别，参见 SexEnum 枚举类 |
| avatar | String | 用户头像 |
| status | Integer | 状态，参见 CommonStatusEnum 枚举类 |
| loginIp | String | 最后登录 IP |
| loginDate | LocalDateTime | 最后登录时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 若传了角色编号 roleId，查询该角色关联的用户编号集合；若集合为空直接返回空分页。
2. 计算部门筛选条件：查询指定部门及其全部子部门的编号集合（含自身）。
3. 按条件分页查询用户。
4. 批量查询部门信息，拼接部门名称后返回。

### 1.8 获得用户详情列表

- **路径**: GET /system/user/list
- **权限**: system:user:query
- **说明**: 根据编号列表批量获取用户详情，结果拼接部门信息。

**请求参数**: Query 参数 ids（List\<Long\>，用户编号列表，必填）

**响应**: CommonResult\<List\<UserRespVO\>\>（字段同 1.7）

**业务逻辑**:
1. 按编号列表批量查询用户。
2. 批量查询部门信息并拼接部门名称后返回。

### 1.9 获取用户精简信息列表

- **路径**: GET /system/user/list-all-simple（别名 /simple-list）
- **权限**: 已认证（无 @PreAuthorize 权限校验）
- **说明**: 获取全部开启状态的用户精简信息，主要用于前端下拉选项；支持按部门过滤。

**请求参数**: Query 参数 deptId（Long，可选，部门编号）

**响应**: CommonResult\<List\<UserSimpleRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 用户编号 |
| nickname | String | 用户昵称 |
| avatar | String | 头像 |
| sex | Integer | 性别 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称（拼接） |

**业务逻辑**:
1. 查询状态为开启（ENABLE）的用户列表，可按部门编号过滤。
2. 批量查询部门信息并拼接部门名称后返回。

### 1.10 获得用户详情

- **路径**: GET /system/user/get
- **权限**: system:user:query
- **说明**: 根据编号获取单个用户详情，拼接部门信息。

**请求参数**: Query 参数 id（Long，用户编号，必填）

**响应**: CommonResult\<UserRespVO\>（字段同 1.7）

**业务逻辑**:
1. 按编号查询用户，不存在时返回 null。
2. 查询用户所属部门并拼接后返回。

### 1.11 导出用户

- **路径**: GET /system/user/export-excel
- **权限**: system:user:export
- **说明**: 按分页查询条件导出全部用户数据为 Excel 文件。

**请求参数 (UserPageReqVO)**: 同 1.7（pageSize 强制置为不限，导出全部）

**响应**: Excel 文件流（用户数据.xls，导出列为 UserRespVO 的 @ExcelProperty 字段）

**业务逻辑**:
1. 将 pageSize 设置为 PAGE_SIZE_NONE，按条件不分页查询全部用户。
2. 批量查询部门信息并拼接。
3. 通过 ExcelUtils 写出 Excel 文件（含操作日志记录，操作类型为导出）。

### 1.12 获得导入用户模板

- **路径**: GET /system/user/get-import-template
- **权限**: 已认证（无 @PreAuthorize 权限校验）
- **说明**: 下载用户导入 Excel 模板（内置两条示例数据）。

**请求参数**: 无

**响应**: Excel 文件流（用户导入模板.xls）

**Excel 模板列 (UserImportExcelVO)**:

| 列名 | 字段 | 类型 | 说明 |
|-----|------|------|------|
| 登录名称 | username | String | 用户账号 |
| 用户名称 | nickname | String | 用户昵称 |
| 部门编号 | deptId | Long | 部门编号 |
| 用户邮箱 | email | String | 用户邮箱 |
| 手机号码 | mobile | String | 手机号码 |
| 用户性别 | sex | Integer | 字典转换（USER_SEX） |
| 账号状态 | status | Integer | 字典转换（COMMON_STATUS） |

**业务逻辑**:
1. 构造两条示例数据（芋道/源码）。
2. 通过 ExcelUtils 写出模板文件。

### 1.13 导入用户

- **路径**: POST /system/user/import
- **权限**: system:user:import
- **说明**: 上传 Excel 批量导入用户，不存在则创建，存在则按 updateSupport 决定是否更新。

**请求参数**: multipart/form-data

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| file | MultipartFile | 是 | Excel 文件，列结构见 1.12 |
| updateSupport | Boolean | 否（默认 false） | 是否支持更新已存在用户 |

**响应**: CommonResult\<UserImportRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| createUsernames | List\<String\> | 创建成功的用户名数组 |
| updateUsernames | List\<String\> | 更新成功的用户名数组 |
| failureUsernames | Map\<String, String\> | 导入失败的用户集合，key 为用户名，value 为失败原因 |

**业务逻辑**:
1. 校验导入数据非空，否则抛出 USER_IMPORT_LIST_IS_EMPTY。
2. 从配置中心读取初始化密码（配置键 system.user.init-password），为空抛出 USER_IMPORT_INIT_PASSWORD。
3. 整个导入在一个事务内执行，任一异常全部回滚；逐行遍历处理。
4. 逐行进行 JSR-303 字段校验（转换为 UserSaveReqVO 并设置初始化密码），失败记录到 failureUsernames 并跳过。
5. 逐行校验手机号/邮箱唯一、部门与岗位开启状态，失败记录到 failureUsernames 并跳过。
6. 用户名不存在则插入新用户（密码为加密后的初始化密码，岗位为空数组），记录创建成功；存在且不允许更新则记录失败（用户账号已存在）。
7. 存在且允许更新时：若状态为禁用，先校验非超管/租户管理员，然后更新用户，记录更新成功。
8. 返回创建/更新成功及失败的用户名集合。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_004 | 导入用户数据不能为空！ |
| 1_002_003_009 | 初始密码不能为空 |
| 1_002_003_000 | 用户账号已经存在（作为行级失败原因记录） |
| 1_002_003_012 | 超级管理员或租户管理员账号不能禁用（作为行级失败原因记录） |

### 1.14 获得用户精简信息

- **路径**: GET /system/user/get-simple
- **权限**: 免鉴权（用于点头像弹名片等场景）
- **说明**: 根据编号获取单个用户精简信息，拼接部门名称。

**请求参数**: Query 参数 id（Long，用户编号，必填）

**响应**: CommonResult\<UserSimpleRespVO\>（字段同 1.9）

**业务逻辑**:
1. 按编号查询用户，不存在时返回 null。
2. 查询用户所属部门（deptId 为空则跳过）。
3. 转换为精简 VO 并返回。

### 1.15 按昵称模糊搜索用户精简信息

- **路径**: GET /system/user/list-by-nickname
- **权限**: 免鉴权（用于加好友等场景）
- **说明**: 按昵称关键词模糊搜索用户精简信息，当前仅按昵称匹配。

**请求参数**: Query 参数 nickname（String，昵称关键词，必填）

**响应**: CommonResult\<List\<UserSimpleRespVO\>\>（字段同 1.9）

**业务逻辑**:
1. 关键词为空白时直接返回空列表。
2. 按昵称模糊查询用户列表。
3. 批量查询部门信息并拼接部门名称后返回。

---

## 2. 用户个人中心（UserProfileController，前缀 /system/user/profile）

> 以下接口均无权限标识，操作对象固定为当前登录用户（已认证）。

### 2.1 获得登录用户信息

- **路径**: GET /system/user/profile/get
- **权限**: 已认证
- **说明**: 获取当前登录用户的完整个人信息，含角色、部门、岗位。

**请求参数**: 无

**响应**: CommonResult\<UserProfileRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 用户编号 |
| username | String | 用户账号 |
| nickname | String | 用户昵称 |
| email | String | 用户邮箱 |
| mobile | String | 手机号码 |
| sex | Integer | 用户性别，参见 SexEnum 枚举类 |
| avatar | String | 用户头像 |
| loginIp | String | 最后登录 IP |
| loginDate | LocalDateTime | 最后登录时间 |
| createTime | LocalDateTime | 创建时间 |
| roles | List\<RoleSimpleRespVO\> | 所属角色列表 |
| dept | DeptSimpleRespVO | 所在部门 |
| posts | List\<PostSimpleRespVO\> | 所属岗位数组 |

**业务逻辑**:
1. 查询当前登录用户的基本信息（该接口通过 @DataPermission(enable = false) 关闭数据权限，避免仅查看自己时查询不到部门）。
2. 基于用户的角色编号列表，从缓存中获取角色信息列表。
3. 查询用户所属部门信息（deptId 为空则跳过）。
4. 查询用户所属岗位列表（postIds 为空则跳过）。
5. 转换为 UserProfileRespVO 返回。

### 2.2 修改用户个人信息

- **路径**: PUT /system/user/profile/update
- **权限**: 已认证
- **说明**: 修改当前登录用户的个人资料（昵称、邮箱、手机号、性别、头像）。

**请求参数 (UserProfileUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| nickname | String | 否 | @Size(max=30) | 用户昵称 |
| email | String | 否 | @Email、@Size(max=50) | 用户邮箱 |
| mobile | String | 否 | @Length(min=11, max=11) | 手机号码，长度必须 11 位 |
| sex | Integer | 否 | - | 用户性别，参见 SexEnum 枚举类 |
| avatar | String | 否 | @URL | 用户头像，必须为合法 URL |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验当前用户存在。
2. 校验邮箱唯一。
3. 校验手机号唯一。
4. 执行更新用户信息。
5. 昵称或头像发生变化时，发送 AdminUserProfileUpdateMessage 消息供下游订阅（如 IM 模块推送好友信息变更）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_003 | 用户不存在 |
| 1_002_003_001 | 手机号已经存在 |
| 1_002_003_002 | 邮箱已经存在 |

### 2.3 修改用户个人密码

- **路径**: PUT /system/user/profile/update-password
- **权限**: 已认证
- **说明**: 修改当前登录用户密码，需校验旧密码。

**请求参数 (UserProfileUpdatePasswordReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| oldPassword | String | 是 | @NotEmpty、@Length(min=4, max=16) | 旧密码 |
| newPassword | String | 是 | @NotEmpty、@Length(min=4, max=16) | 新密码，长度 4-16 位 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验旧密码：用户必须存在，且旧密码与库中加密密码匹配，否则抛出 USER_PASSWORD_FAILED。
2. 新密码加密后更新用户记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_003 | 用户不存在 |
| 1_002_003_005 | 用户密码校验失败 |

---

## 附：用户域相关错误码汇总（1_002_003 段）

| 错误码 | 说明 |
|-------|------|
| 1_002_003_000 | 用户账号已经存在 |
| 1_002_003_001 | 手机号已经存在 |
| 1_002_003_002 | 邮箱已经存在 |
| 1_002_003_003 | 用户不存在 |
| 1_002_003_004 | 导入用户数据不能为空！ |
| 1_002_003_005 | 用户密码校验失败 |
| 1_002_003_006 | 名字为【{}】的用户已被禁用 |
| 1_002_003_008 | 创建用户失败，原因：超过租户最大租户配额({})！ |
| 1_002_003_009 | 初始密码不能为空 |
| 1_002_003_010 | 该手机号尚未注册（用于手机号登录/找回流程） |
| 1_002_003_011 | 注册功能已关闭（用于自注册流程） |
| 1_002_003_012 | 超级管理员或租户管理员账号不能禁用 |
| 1_002_003_013 | 超级管理员或租户管理员账号不能删除 |
