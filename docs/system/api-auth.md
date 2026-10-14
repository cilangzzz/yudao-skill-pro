# 认证与验证码接口 (AuthController / CaptchaController)

> 管理后台的认证入口：账号密码登录、注册、短信登录、社交登录、令牌刷新与登出、权限信息获取，以及 AJ-Captcha 行为验证码的获取与校验。

## 接口路径前缀

- `/system/auth` (Controller: AuthController)
- `/system/captcha` (Controller: CaptchaController)

---

## 1. 认证接口（AuthController）

### 1.1 使用账号密码登录

- **路径**: POST /system/auth/login
- **权限**: @PermitAll（匿名可访问；开启验证码开关时需先通过验证码校验）
- **说明**: 使用账号密码登录，可选同时绑定社交用户（传 social 开头参数）。

**请求参数 (AuthLoginReqVO，继承 CaptchaVerificationReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| username | String | 是 | @NotEmpty、@Length(min=4, max=30)、@Pattern(^[a-zA-Z0-9]{4,30}$) | 账号 |
| password | String | 是 | @NotEmpty、@Length(min=4, max=16) | 密码 |
| socialType | Integer | 否 | @InEnum(SocialTypeEnum) | 社交平台的类型，参见 SocialTypeEnum 枚举值；登录并绑定社交用户时传递 |
| socialCode | String | 条件 | @AssertTrue（socialType 非空时不能为空） | 授权码 |
| socialState | String | 条件 | @AssertTrue（socialType 非空时不能为空） | state |
| captchaVerification | String | 条件 | @NotEmpty(groups = CodeEnableGroup)（验证码开启时必填） | 验证码凭证 |

**响应**: CommonResult&lt;AuthLoginRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| accessToken | String | 访问令牌 |
| refreshToken | String | 刷新令牌 |
| expiresTime | LocalDateTime | 过期时间 |

**业务逻辑**:
1. 校验图形验证码：`yudao.captcha.enable`（默认 true）开启时，对 captchaVerification 做 JSR-303 分组校验并调用 AJ-Captcha verification 校验；失败则记录"验证码错误"登录日志并抛出 AUTH_LOGIN_CAPTCHA_CODE_ERROR。
2. authenticate 账号密码认证：按用户名查询用户，不存在或密码不匹配均记录 BAD_CREDENTIALS 登录日志并抛出 AUTH_LOGIN_BAD_CREDENTIALS。
3. 校验用户状态，被禁用则记录 USER_DISABLED 日志并抛出 AUTH_LOGIN_USER_DISABLED。
4. 若 socialType 非空，调用 socialUserService.bindSocialUser 将社交用户绑定到当前管理员账号。
5. 登录成功收尾（createTokenAfterLoginSuccess）：记录登录成功日志并通过 userService.updateUserLogin 更新最后登录 IP。
6. 调用 OAuth2TokenService.createAccessToken（默认客户端 default）创建访问令牌，返回 userId/accessToken/refreshToken/expiresTime。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_000_000 | 登录失败，账号密码不正确 |
| 1_002_000_001 | 登录失败，账号被禁用 |
| 1_002_000_004 | 验证码不正确，原因：{} |

### 1.2 登出系统

- **路径**: POST /system/auth/logout
- **权限**: @PermitAll（匿名可访问，实际依赖请求头/参数中的 accessToken）
- **说明**: 从请求头（token-header）或请求参数中取出访问令牌并删除，记录登出日志。

**请求参数**: 无（token 取自 HttpServletRequest，由 SecurityFrameworkUtils.obtainAuthorization 解析）

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 从请求头或请求参数中解析访问令牌，为空则直接返回 true。
2. 调用 OAuth2TokenService.removeAccessToken 删除访问令牌。
3. 令牌不存在（返回 null）时直接结束，不记日志。
4. 删除成功后记录登出日志（LOGOUT_SELF 类型）：管理员用户取用户名，其他用户类型取会员手机号。

### 1.3 刷新令牌

- **路径**: POST /system/auth/refresh-token
- **权限**: @PermitAll（匿名可访问）
- **说明**: 使用刷新令牌换取新的访问令牌。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| refreshToken | String | 是 | @RequestParam(required) | 刷新令牌 |

**响应**: CommonResult&lt;AuthLoginRespVO&gt;（字段同 1.1）

**业务逻辑**:
1. 调用 OAuth2TokenService.refreshAccessToken(refreshToken, 默认客户端 default) 刷新访问令牌。
2. 将新的 OAuth2AccessTokenDO 转换为 AuthLoginRespVO 返回（含新 accessToken/refreshToken/expiresTime）。

### 1.4 获取登录用户的权限信息

- **路径**: GET /system/auth/get-permission-info
- **权限**: 已认证（无 @PreAuthorize，需登录后访问）
- **说明**: 获取当前登录管理员的用户信息、角色标识数组、操作权限数组和菜单树；方法上通过 @DataPermission(enable=false) 忽略数据权限，避免过滤导致查询不到用户。

**请求参数**: 无

**响应**: CommonResult&lt;AuthPermissionInfoRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| user | UserVO | 用户信息 |
| roles | Set&lt;String&gt; | 角色标识数组 |
| permissions | Set&lt;String&gt; | 操作权限数组 |
| menus | List&lt;MenuVO&gt; | 菜单树 |

内嵌 **UserVO** 字段:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 用户编号 |
| nickname | String | 用户昵称 |
| avatar | String | 用户头像 |
| deptId | Long | 部门编号 |
| username | String | 用户账号 |
| email | String | 用户邮箱 |

内嵌 **MenuVO** 字段:

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 菜单编号 |
| parentId | Long | 父菜单 ID |
| name | String | 菜单名称 |
| path | String | 路由地址（仅目录/菜单类型） |
| component | String | 组件路径（仅菜单类型） |
| componentName | String | 组件名 |
| icon | String | 菜单图标（仅目录/菜单类型） |
| visible | Boolean | 是否可见 |
| keepAlive | Boolean | 是否缓存 |
| alwaysShow | Boolean | 是否总是显示 |
| children | List&lt;MenuVO&gt; | 子路由 |

**业务逻辑**:
1. 按当前登录用户 ID 查询管理员用户，不存在则返回 null。
2. 查询用户的角色 ID 列表；为空则直接返回仅含用户信息、空角色与空菜单的结果。
3. 查询角色列表并移除状态为禁用的角色。
4. 根据角色 ID 集合查询角色-菜单关联，得到菜单 ID 集合，再查询菜单列表并过滤掉被禁用的菜单。
5. 通过 AuthConvert 将用户、角色、菜单拼装为 AuthPermissionInfoRespVO（含角色标识、权限标识、菜单树）返回。

### 1.5 注册用户

- **路径**: POST /system/auth/register
- **权限**: @PermitAll（匿名可访问；受配置开关控制）
- **说明**: 自助注册管理员账号，成功后直接返回登录令牌。

**请求参数 (AuthRegisterReqVO，继承 CaptchaVerificationReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| username | String | 是 | @NotBlank、@Pattern(^[a-zA-Z0-9]{4,30}$)、@Size(min=4, max=30) | 用户账号 |
| nickname | String | 是 | @NotBlank、@Size(max=30) | 用户昵称 |
| password | String | 是 | @NotEmpty、@Length(min=4, max=16) | 密码 |
| captchaVerification | String | 条件 | @NotEmpty(groups = CodeEnableGroup)（验证码开启时必填） | 验证码凭证 |

**响应**: CommonResult&lt;AuthLoginRespVO&gt;（字段同 1.1）

**业务逻辑**:
1. 校验图形验证码（开启时），失败抛出 AUTH_REGISTER_CAPTCHA_CODE_ERROR。
2. 校验注册开关：读取配置项 `system.user.register-enabled`，未开启抛出 USER_REGISTER_DISABLED。
3. 校验租户账号配额：当前租户用户数达到上限时抛出 USER_COUNT_MAX。
4. 校验账号唯一性（用户名/手机号/邮箱），用户名已存在抛出 USER_USERNAME_EXISTS，随后插入用户。
5. 登录成功收尾（createTokenAfterLoginSuccess）：校验用户状态、记录 LOGIN_USERNAME 成功登录日志、创建 OAuth2 访问令牌并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_000_008 | 验证码不正确，原因：{} |
| 1_002_003_000 | 用户账号已经存在 |
| 1_002_003_008 | 创建用户失败，原因：超过租户最大租户配额({})！ |
| 1_002_003_011 | 注册功能已关闭 |

### 1.6 使用短信验证码登录

- **路径**: POST /system/auth/sms-login
- **权限**: @PermitAll（匿名可访问）
- **说明**: 使用手机号 + 短信验证码登录管理员账号。

**请求参数 (AuthSmsLoginReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| mobile | String | 是 | @NotEmpty、@Mobile | 手机号 |
| code | String | 是 | @NotEmpty | 短信验证码 |

**响应**: CommonResult&lt;AuthLoginRespVO&gt;（字段同 1.1）

**业务逻辑**:
1. 调用 SmsCodeApi.useSmsCode 校验并核销短信验证码（场景：ADMIN_MEMBER_LOGIN，携带客户端 IP）。
2. 按手机号查询管理员用户，不存在抛出 USER_NOT_EXISTS。
3. 登录成功收尾（createTokenAfterLoginSuccess）：统一校验用户状态（禁用抛 AUTH_LOGIN_USER_DISABLED）、记录 LOGIN_MOBILE 成功登录日志并更新最后登录 IP、创建 OAuth2 访问令牌并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_000_001 | 登录失败，账号被禁用 |
| 1_002_003_003 | 用户不存在 |
| 1_002_014_000 | 验证码不存在 |
| 1_002_014_001 | 验证码已过期 |
| 1_002_014_002 | 验证码已使用 |

### 1.7 发送手机验证码

- **路径**: POST /system/auth/send-sms-code
- **权限**: @PermitAll（匿名可访问）
- **说明**: 向指定手机号发送短信验证码，支持登录、重置密码等场景。

**请求参数 (AuthSmsSendReqVO，继承 CaptchaVerificationReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| mobile | String | 是 | @NotEmpty、@Mobile | 手机号 |
| scene | Integer | 是 | @NotNull、@InEnum(SmsSceneEnum) | 短信场景，参见 SmsSceneEnum |
| captchaVerification | String | 条件 | @NotEmpty(groups = CodeEnableGroup)（重置密码场景必填） | 验证码凭证 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 若 scene 为 ADMIN_MEMBER_RESET_PASSWORD（重置密码），先校验图形验证码，失败抛出 AUTH_REGISTER_CAPTCHA_CODE_ERROR。
2. 校验手机号对应的用户是否存在，不存在抛出 AUTH_MOBILE_NOT_EXISTS。
3. 调用 SmsCodeApi.sendSmsCode 发送验证码，携带客户端 IP。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_000_007 | 手机号不存在 |
| 1_002_000_008 | 验证码不正确，原因：{} |
| 1_002_014_004 | 超过每日短信发送数量 |
| 1_002_014_005 | 短信发送过于频繁 |

### 1.8 重置密码

- **路径**: POST /system/auth/reset-password
- **权限**: @PermitAll（匿名可访问，需短信验证码）
- **说明**: 通过手机号 + 短信验证码重置账号密码。

**请求参数 (AuthResetPasswordReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| password | String | 是 | @NotEmpty、@Length(min=4, max=16) | 新密码 |
| mobile | String | 是 | @NotEmpty、@Mobile | 手机号 |
| code | String | 是 | @NotEmpty | 手机短信验证码 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按手机号查询管理员用户，不存在抛出 USER_MOBILE_NOT_EXISTS。
2. 调用 SmsCodeApi.useSmsCode 校验并核销短信验证码（场景：ADMIN_MEMBER_RESET_PASSWORD）。
3. 调用 userService.updateUserPassword 更新用户密码（方法带 @Transactional 事务保证）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_010 | 该手机号尚未注册 |
| 1_002_014_000 | 验证码不存在 |
| 1_002_014_001 | 验证码已过期 |
| 1_002_014_002 | 验证码已使用 |

### 1.9 社交授权的跳转

- **路径**: GET /system/auth/social-auth-redirect
- **权限**: @PermitAll（匿名可访问）
- **说明**: 获取第三方社交平台的授权跳转 URL，前端跳转后用户授权再回调。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @RequestParam(required) | 社交平台的类型（SocialTypeEnum） |
| redirectUri | String | 是 | @RequestParam(required) | 授权完成后的回调路径 |

**响应**: CommonResult&lt;String&gt;（社交平台的授权跳转 URL）

**业务逻辑**:
1. 调用 SocialClientService.getAuthorizeUrl(type, UserTypeEnum.ADMIN, redirectUri) 生成管理后台用户类型的社交授权地址并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_000 | 社交授权失败，原因是：{} |
| 1_002_018_210 | 社交客户端不存在 |

### 1.10 社交快捷登录

- **路径**: POST /system/auth/social-login
- **权限**: @PermitAll（匿名可访问）
- **说明**: 使用 code 授权码快捷登录，适合未登录但社交账号已绑定管理员用户的场景。

**请求参数 (AuthSocialLoginReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @NotNull、@InEnum(SocialTypeEnum) | 社交平台的类型 |
| code | String | 是 | @NotEmpty | 授权码 |
| state | String | 是 | @NotEmpty | state |

**响应**: CommonResult&lt;AuthLoginRespVO&gt;（字段同 1.1）

**业务逻辑**:
1. 调用 socialUserService.getSocialUserByCode 以 code 换取社交用户信息；社交用户不存在或未绑定用户时抛出 AUTH_THIRD_LOGIN_NOT_BIND。
2. 按绑定的 userId 查询管理员用户，不存在抛出 USER_NOT_EXISTS。
3. 登录成功收尾（createTokenAfterLoginSuccess）：校验用户状态（禁用抛 AUTH_LOGIN_USER_DISABLED）、记录 LOGIN_SOCIAL 成功登录日志并更新最后登录 IP、创建 OAuth2 访问令牌并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_000_001 | 登录失败，账号被禁用 |
| 1_002_000_005 | 未绑定账号，需要进行绑定 |
| 1_002_003_003 | 用户不存在 |
| 1_002_018_000 | 社交授权失败，原因是：{} |

---

## 2. 验证码接口（CaptchaController）

> 接入 AJ-Captcha（anji-plus）行为验证码，两类端点均 @PermitAll + @TenantIgnore（忽略租户），请求体 browserInfo 由服务端根据客户端 IP + User-Agent 自动填充。响应为第三方 ResponseModel（非 CommonResult），repCode 为 "0000" 表示成功。

### 2.1 获得验证码

- **路径**: POST /system/captcha/get
- **权限**: @PermitAll（匿名可访问）
- **说明**: 生成行为验证码（滑动拼图/文字点选），返回底图数据。

**请求参数 (CaptchaVO，AJ-Captcha 第三方 VO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| captchaType | String | 是 | 无 | 验证码类型：blockPuzzle（滑动拼图）/ clickWord（文字点选） |
| clientUid | String | 否 | 无 | 客户端唯一标识 |
| ts | Long | 否 | 无 | 时间戳 |
| browserInfo | String | 否 | 无 | 浏览器信息，服务端强制覆盖为 客户端IP + User-Agent |

**响应**: ResponseModel（AJ-Captcha 原生响应，非 CommonResult）

| 字段 | 类型 | 说明 |
|-----|------|------|
| repCode | String | 响应码，"0000" 表示成功 |
| repMsg | String | 响应说明 |
| repData | Object | 验证码数据（底图、密钥 token 等） |

**业务逻辑**:
1. 从请求中提取客户端 IP（取不到则用 remoteAddr）拼接 User-Agent，作为 browserInfo 写入 CaptchaVO。
2. 委托 AJ-Captcha 的 CaptchaService.get 生成验证码并返回 ResponseModel。

### 2.2 校验验证码

- **路径**: POST /system/captcha/check
- **权限**: @PermitAll（匿名可访问）
- **说明**: 二次校验行为验证码的滑动/点选结果，通过后发放一次性 token 供登录等接口使用。

**请求参数 (CaptchaVO，AJ-Captcha 第三方 VO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| captchaType | String | 是 | 无 | 验证码类型：blockPuzzle / clickWord |
| token | String | 条件 | 无 | get 步骤返回的一次性校验 token |
| captchaVerification | String | 条件 | 无 | 加密的校验串（滑动坐标/点选坐标 + 密钥） |
| browserInfo | String | 否 | 无 | 浏览器信息，服务端强制覆盖为 客户端IP + User-Agent |

**响应**: ResponseModel（同 2.1）

**业务逻辑**:
1. 同样以 客户端IP + User-Agent 填充 browserInfo。
2. 委托 AJ-Captcha 的 CaptchaService.check 校验验证码，返回 ResponseModel（repCode "0000" 表示校验通过）。
3. 校验通过后前端将 captchaVerification 凭证随登录/注册/发送验证码请求提交，由 AdminAuthServiceImpl 中的 captchaService.verification 完成二次校验。

---

## 附：认证域相关错误码汇总（AUTH 模块 1-002-000-000 段）

| 错误码 | 说明 |
|-------|------|
| 1_002_000_000 | 登录失败，账号密码不正确 |
| 1_002_000_001 | 登录失败，账号被禁用 |
| 1_002_000_004 | 验证码不正确，原因：{} |
| 1_002_000_005 | 未绑定账号，需要进行绑定 |
| 1_002_000_007 | 手机号不存在 |
| 1_002_000_008 | 验证码不正确，原因：{} |
