# OAuth2 认证接口 (OAuth2OpenController / OAuth2ClientController / OAuth2TokenController / OAuth2UserController)

> 提供 OAuth2.0 开放授权能力：支持授权码、密码、客户端凭证、刷新令牌、简化五种授权模式的令牌发放与校验，配套 OAuth2 客户端管理、访问令牌管理以及基于 scope 的用户信息读写接口。

## 接口路径前缀

- /system/oauth2  (Controller: OAuth2OpenController) —— OAuth2 开放授权（令牌发放/校验/授权确认）
- /system/oauth2-client  (Controller: OAuth2ClientController) —— OAuth2 客户端管理
- /system/oauth2-token  (Controller: OAuth2TokenController) —— 访问令牌管理
- /system/oauth2/user  (Controller: OAuth2UserController) —— OAuth2 用户信息（scope 控制）

## 1. OAuth2 开放授权（OAuth2OpenController）

面向外部应用的开放接口。获取 access token 的接口通过 HTTP Basic 认证传递 client_id + client_secret；除 `/authorize` 两个接口需用户登录外，其余 `@PermitAll` 放行，由客户端校验保证安全。

### 1.1 获得访问令牌

- **路径**: POST /system/oauth2/token
- **权限**: @PermitAll（通过 Basic 认证校验客户端）
- **说明**: OAuth2 令牌端点，支持 authorization_code / password / client_credentials / refresh_token 四种授权模式获取访问令牌，不支持 implicit 模式。

**请求参数**（@RequestParam 表单参数，另需 Basic 认证头）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| grant_type | String | 是 | - | 授权类型：authorization_code / password / client_credentials / refresh_token |
| code | String | 否 | - | 授权码（authorization_code 模式） |
| redirect_uri | String | 否 | - | 重定向 URI（authorization_code 模式） |
| state | String | 否 | - | 状态（authorization_code 模式） |
| username | String | 否 | - | 账号（password 模式） |
| password | String | 否 | - | 密码（password 模式） |
| scope | String | 否 | - | 授权范围，多个使用空格分隔（password / client_credentials 模式） |
| refresh_token | String | 否 | - | 刷新令牌（refresh_token 模式） |
| Basic 认证 | - | 是 | - | HTTP Header：client_id + client_secret |

**响应**: CommonResult&lt;OAuth2OpenAccessTokenRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| access_token | String | 访问令牌 |
| refresh_token | String | 刷新令牌 |
| token_type | String | 令牌类型（bearer） |
| expires_in | Long | 过期时间，单位：秒 |
| scope | String | 授权范围，多个使用空格分隔 |

**业务逻辑**: 1. 校验 grant_type 为合法授权类型，且不允许 implicit 模式；2. 从 Basic 认证中解析 client_id / client_secret，校验客户端存在、启用、授权类型、scope 范围与 redirect_uri 合法；3. 按模式分发：authorization_code 消费授权码（校验 code 存在、未过期，且 clientId / redirect_uri / state 与授权码记录匹配）后创建令牌；password 模式先 authenticate 账号密码再创建令牌；client_credentials 模式以 userId=0 创建令牌；refresh_token 模式刷新令牌（旧访问令牌删除、刷新令牌过期则拒绝）；4. 创建令牌时生成刷新令牌与访问令牌（UUID），访问令牌有效期取客户端 accessTokenValiditySeconds，写入 MySQL 与 Redis；5. 转换为 OAuth2OpenAccessTokenRespVO 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |
| 1_002_020_002 | OAuth2 客户端已禁用 |
| 1_002_020_003 | 不支持该授权类型 |
| 1_002_020_004 | 授权范围过大 |
| 1_002_020_005 | 无效 redirect_uri |
| 1_002_020_006 | 无效 client_secret |
| 1_002_021_000 | client_id 不匹配 |
| 1_002_021_001 | redirect_uri 不匹配 |
| 1_002_021_002 | state 不匹配 |
| 1_002_022_000 | code 不存在 |
| 1_002_022_001 | code 已过期 |

### 1.2 删除访问令牌

- **路径**: DELETE /system/oauth2/token
- **权限**: @PermitAll（通过 Basic 认证校验客户端）
- **说明**: 客户端主动吊销某个访问令牌。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| token | String | 是 | - | 访问令牌 |
| Basic 认证 | - | 是 | - | HTTP Header：client_id + client_secret |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否删除成功（令牌不存在或不属于该客户端时返回 false） |

**业务逻辑**: 1. 从 Basic 认证解析并校验客户端；2. 查询访问令牌，若不存在或 clientId 与当前客户端不匹配则返回 false；3. 匹配则删除访问令牌，并级联删除对应刷新令牌及 Redis 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |
| 1_002_020_002 | OAuth2 客户端已禁用 |
| 1_002_020_006 | 无效 client_secret |

### 1.3 校验访问令牌

- **路径**: POST /system/oauth2/check-token
- **权限**: @PermitAll（通过 Basic 认证校验客户端）
- **说明**: 校验访问令牌是否有效，返回令牌关联的用户与授权信息。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| token | String | 是 | - | 访问令牌 |
| Basic 认证 | - | 是 | - | HTTP Header：client_id + client_secret |

**响应**: CommonResult&lt;OAuth2OpenCheckTokenRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| user_id | Long | 用户编号 |
| user_type | Integer | 用户类型，参见 UserTypeEnum 枚举 |
| tenant_id | Long | 租户编号 |
| client_id | String | 客户端编号 |
| scopes | List&lt;String&gt; | 授权范围 |
| access_token | String | 访问令牌 |
| exp | Long | 过期时间，时间戳 / 1000，单位：秒 |

**业务逻辑**: 1. 从 Basic 认证解析并校验客户端；2. 查询令牌：优先从 Redis 获取，未命中查 MySQL，仍不存在时尝试将未过期的刷新令牌转换为访问令牌兜底（解决积木报表、WebSocket 等无法传 refresh_token 的场景）；3. 令牌不存在抛"访问令牌不存在"，已过期抛"访问令牌已过期"；4. 转换为 OAuth2OpenCheckTokenRespVO 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |
| 1_002_020_002 | OAuth2 客户端已禁用 |
| 1_002_020_006 | 无效 client_secret |

### 1.4 获得授权信息

- **路径**: GET /system/oauth2/authorize
- **权限**: 已认证（需用户登录）
- **说明**: 授权码 / 简化模式下单点登录页（sso.vue）进入时调用，返回客户端信息与用户历史 scope 授权选中状态。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| clientId | String | 是 | - | 客户端编号 |

**响应**: CommonResult&lt;OAuth2OpenAuthorizeInfoRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| client | Client | 客户端信息 |
| client.name | String | 应用名 |
| client.logo | String | 应用图标 |
| scopes | List&lt;KeyValue&lt;String, Boolean&gt;&gt; | scope 选中信息（有序），Key 为 scope，Value 为是否选中 |

**业务逻辑**: 1. 登录校验由 Spring Security 完成；2. 从缓存校验客户端存在；3. 查询当前用户对该客户端的历史授权记录，并剔除已过期的记录；4. 拼接客户端信息与 scope 选中状态返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |

### 1.5 申请授权

- **路径**: POST /system/oauth2/authorize
- **权限**: 已认证（需用户登录）
- **说明**: 授权码 / 简化模式下用户提交授权（同意或拒绝），返回重定向 URL 由前端处理跳转。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| response_type | String | 是 | - | 响应类型，仅允许 code（授权码模式）或 token（简化模式） |
| client_id | String | 是 | - | 客户端编号 |
| scope | String | 否 | - | 授权范围，JSON Map 格式（Key 为 scope，Value 为是否勾选） |
| redirect_uri | String | 是 | - | 重定向 URI |
| auto_approve | Boolean | 是 | - | 是否为自动授权场景（true 场景一 / false 场景二） |
| state | String | 否 | - | 状态 |

**响应**: CommonResult&lt;String&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | String | 重定向 URL；自动授权未通过时返回 null（前端不跳转），用户拒绝时返回携带 access_denied 错误的 URL |

**业务逻辑**: 1. 校验 response_type 只允许 code 或 token；2. 校验客户端存在、启用、授权类型、scope 在客户端授权范围内、redirect_uri 匹配；3. auto_approve=true（场景一）：执行预授权检查——请求 scope 全部在客户端 autoApproveScopes 中则写入批准记录并通过，否则结合用户历史批准记录判断，不通过返回 null；4. auto_approve=false（场景二）：逐个保存 scope 批准记录（有效期 30 天，先更新后插入），至少一个 scope 被同意才通过，否则返回 access_denied 错误重定向 URL；5. code 模式生成授权码（UUID，有效期 5 分钟）并拼接重定向 URL；token 模式直接创建访问令牌并拼接重定向 URL。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |
| 1_002_020_002 | OAuth2 客户端已禁用 |
| 1_002_020_003 | 不支持该授权类型 |
| 1_002_020_004 | 授权范围过大 |
| 1_002_020_005 | 无效 redirect_uri |

## 2. OAuth2 客户端管理（OAuth2ClientController）

管理后台维护 OAuth2 客户端（应用）信息，客户端数据带 Redis 缓存，增删改时清空缓存。

### 2.1 创建 OAuth2 客户端

- **路径**: POST /system/oauth2-client/create
- **权限**: system:oauth2-client:create
- **说明**: 创建一个 OAuth2 客户端，返回新客户端编号。

**请求参数 (OAuth2ClientSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| clientId | String | 是 | @NotNull | 客户端编号 |
| secret | String | 是 | @NotNull | 客户端密钥 |
| name | String | 是 | @NotNull | 应用名 |
| logo | String | 是 | @NotNull、@URL | 应用图标 |
| description | String | 否 | - | 应用描述 |
| status | Integer | 是 | @NotNull | 状态，参见 CommonStatusEnum 枚举 |
| accessTokenValiditySeconds | Integer | 是 | @NotNull | 访问令牌的有效期（秒） |
| refreshTokenValiditySeconds | Integer | 是 | @NotNull | 刷新令牌的有效期（秒） |
| redirectUris | List&lt;String&gt; | 是 | @NotNull，元素 @NotEmpty、@URL | 可重定向的 URI 地址 |
| authorizedGrantTypes | List&lt;String&gt; | 是 | @NotNull | 授权类型，参见 OAuth2GrantTypeEnum 枚举 |
| scopes | List&lt;String&gt; | 否 | - | 授权范围 |
| autoApproveScopes | List&lt;String&gt; | 否 | - | 自动通过的授权范围 |
| authorities | List&lt;String&gt; | 否 | - | 权限 |
| resourceIds | List&lt;String&gt; | 否 | - | 资源 |
| additionalInformation | String | 否 | @AssertTrue（必须是 JSON 格式） | 附加信息 |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的客户端编号 |

**业务逻辑**: 1. 校验 clientId 未被已有客户端占用（占用则抛 OAUTH2_CLIENT_EXISTS）；2. 将 ReqVO 转换为 OAuth2ClientDO；3. 插入数据库并返回主键 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_001 | OAuth2 客户端编号已存在 |

### 2.2 更新 OAuth2 客户端

- **路径**: PUT /system/oauth2-client/update
- **权限**: system:oauth2-client:update
- **说明**: 根据 id 更新 OAuth2 客户端。

**请求参数 (OAuth2ClientSaveReqVO)**: 字段同 2.1，其中 id 必传（更新目标）。

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 更新成功返回 true |

**业务逻辑**: 1. 校验客户端存在（不存在抛 OAUTH2_CLIENT_NOT_EXISTS）；2. 校验 clientId 未被其它客户端占用；3. 更新数据库，并清空 OAUTH_CLIENT 缓存（可能修改 clientId，全部清空）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |
| 1_002_020_001 | OAuth2 客户端编号已存在 |

### 2.3 删除 OAuth2 客户端

- **路径**: DELETE /system/oauth2-client/delete
- **权限**: system:oauth2-client:delete
- **说明**: 根据 id 删除 OAuth2 客户端。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 客户端编号 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**: 1. 校验客户端存在；2. 删除记录；3. 清空 OAUTH_CLIENT 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_020_000 | OAuth2 客户端不存在 |

### 2.4 批量删除 OAuth2 客户端

- **路径**: DELETE /system/oauth2-client/delete-list
- **权限**: system:oauth2-client:delete
- **说明**: 根据编号列表批量删除 OAuth2 客户端。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | - | 客户端编号列表 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**: 1. 按编号列表批量删除记录；2. 清空 OAUTH_CLIENT 缓存（不逐条校验存在性）。

### 2.5 获得 OAuth2 客户端

- **路径**: GET /system/oauth2-client/get
- **权限**: system:oauth2-client:query
- **说明**: 根据 id 获得单个 OAuth2 客户端详情。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | - | 客户端编号 |

**响应**: CommonResult&lt;OAuth2ClientRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| clientId | String | 客户端编号 |
| secret | String | 客户端密钥 |
| name | String | 应用名 |
| logo | String | 应用图标 |
| description | String | 应用描述 |
| status | Integer | 状态，参见 CommonStatusEnum 枚举 |
| accessTokenValiditySeconds | Integer | 访问令牌的有效期（秒） |
| refreshTokenValiditySeconds | Integer | 刷新令牌的有效期（秒） |
| redirectUris | List&lt;String&gt; | 可重定向的 URI 地址 |
| authorizedGrantTypes | List&lt;String&gt; | 授权类型 |
| scopes | List&lt;String&gt; | 授权范围 |
| autoApproveScopes | List&lt;String&gt; | 自动通过的授权范围 |
| authorities | List&lt;String&gt; | 权限 |
| resourceIds | List&lt;String&gt; | 资源 |
| additionalInformation | String | 附加信息 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询客户端记录；2. 转换为 OAuth2ClientRespVO 返回（记录不存在时返回 null 数据）。

### 2.6 获得 OAuth2 客户端分页

- **路径**: GET /system/oauth2-client/page
- **权限**: system:oauth2-client:query
- **说明**: 分页查询 OAuth2 客户端列表。

**请求参数 (OAuth2ClientPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，从 1 开始（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| name | String | 否 | - | 应用名，模糊匹配 |
| status | Integer | 否 | - | 状态，参见 CommonStatusEnum 枚举 |

**响应**: CommonResult&lt;PageResult&lt;OAuth2ClientRespVO&gt;&gt;，列表项字段同 2.5 响应。

**业务逻辑**: 1. 按应用名模糊、状态条件分页查询；2. 转换为 OAuth2ClientRespVO 分页结果返回。

## 3. 访问令牌管理（OAuth2TokenController）

管理后台查询与强制下线（删除）当前有效的访问令牌。

### 3.1 获得访问令牌分页

- **路径**: GET /system/oauth2-token/page
- **权限**: system:oauth2-token:page
- **说明**: 分页查询访问令牌，只返回有效期内的。

**请求参数 (OAuth2AccessTokenPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，从 1 开始（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| userId | Long | 否 | - | 用户编号 |
| userType | Integer | 否 | - | 用户类型，参见 UserTypeEnum 枚举 |
| clientId | String | 否 | - | 客户端编号 |

**响应**: CommonResult&lt;PageResult&lt;OAuth2AccessTokenRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| accessToken | String | 访问令牌 |
| refreshToken | String | 刷新令牌 |
| userId | Long | 用户编号 |
| userType | Integer | 用户类型 |
| clientId | String | 客户端编号 |
| createTime | LocalDateTime | 创建时间 |
| expiresTime | LocalDateTime | 过期时间 |

**业务逻辑**: 1. 按用户编号、用户类型、客户端编号条件分页查询访问令牌；2. 转换为 OAuth2AccessTokenRespVO 分页结果返回。

### 3.2 删除访问令牌

- **路径**: DELETE /system/oauth2-token/delete
- **权限**: system:oauth2-token:delete
- **说明**: 管理员强制下线，删除指定访问令牌。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accessToken | String | 是 | - | 访问令牌 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**: 1. 调用 AdminAuthService.logout，登出类型为"管理员删除"（LOGOUT_DELETE）；2. 内部移除访问令牌（MySQL + Redis）及其刷新令牌，并记录登出日志。

### 3.3 批量删除访问令牌

- **路径**: DELETE /system/oauth2-token/delete-list
- **权限**: system:oauth2-token:delete
- **说明**: 管理员批量强制下线，删除多个访问令牌。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accessTokens | List&lt;String&gt; | 是 | - | 访问令牌数组 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**: 1. 遍历访问令牌数组，逐个调用 AdminAuthService.logout（LOGOUT_DELETE 类型）删除并记录登出日志。

## 4. OAuth2 用户信息（OAuth2UserController）

提供给外部应用通过 OAuth2 access token 读写当前用户基本信息，通过 scope 控制访问权限（示例：user.read / user.write）。

### 4.1 获得用户基本信息

- **路径**: GET /system/oauth2/user/get
- **权限**: 已认证 + @ss.hasScope('user.read')
- **说明**: 获取当前登录用户的基本信息、部门与岗位。

**请求参数**: 无

**响应**: CommonResult&lt;OAuth2UserInfoRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 用户编号 |
| username | String | 用户账号 |
| nickname | String | 用户昵称 |
| email | String | 用户邮箱 |
| mobile | String | 手机号码 |
| sex | Integer | 用户性别，参见 SexEnum 枚举类 |
| avatar | String | 用户头像 |
| dept | Dept | 所在部门 |
| dept.id | Long | 部门编号 |
| dept.name | String | 部门名称 |
| posts | List&lt;Post&gt; | 所属岗位数组 |
| posts[].id | Long | 岗位编号 |
| posts[].name | String | 岗位名称 |

**业务逻辑**: 1. 获取当前登录用户基本信息；2. 用户有部门时查询部门信息并填充；3. 用户有岗位时批量查询岗位列表并填充；4. 返回 OAuth2UserInfoRespVO。

### 4.2 更新用户基本信息

- **路径**: PUT /system/oauth2/user/update
- **权限**: 已认证 + @ss.hasScope('user.write')
- **说明**: 更新当前登录用户的基本信息（复用个人资料更新逻辑）。

**请求参数 (OAuth2UserUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| nickname | String | 否 | @Size(max = 30) | 用户昵称 |
| email | String | 否 | @Email、@Size(max = 50) | 用户邮箱 |
| mobile | String | 否 | @Length(min = 11, max = 11) | 手机号码 |
| sex | Integer | 否 | - | 用户性别，参见 SexEnum 枚举类 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 更新成功返回 true |

**业务逻辑**: 1. 将 OAuth2UserUpdateReqVO 转换为 UserProfileUpdateReqVO（复用 AdminUserService 的个人资料更新逻辑）；2. 调用 updateUserProfile 按当前登录用户编号更新资料。
