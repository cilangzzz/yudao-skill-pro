# 社交用户接口 (SocialUserController、SocialClientController)

> 提供管理后台的社交登录能力：当前登录用户的社交账号绑定/解绑/查询、社交用户档案管理，以及各平台社交客户端（OAuth 密钥）配置管理与微信小程序订阅消息发送测试。

## 接口路径前缀

- /system/social-user  (Controller: SocialUserController)
- /system/social-client  (Controller: SocialClientController)

## 1. 社交用户绑定 (SocialUserController)

当前登录管理员对自己社交账号的自助操作，三个端点均无 @PreAuthorize 权限标识，仅要求已认证（从登录态取 userId，userType 固定为 ADMIN）。

### 1.1 社交绑定（使用 code 授权码）

- **路径**: POST /system/social-user/bind
- **权限**: 已认证
- **说明**: 使用三方平台回调的授权码 code，将社交账号绑定到当前登录的管理员用户。

**请求参数 (SocialUserBindReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| type | Integer | 是 | @NotNull、@InEnum(SocialTypeEnum) | 社交平台的类型，如 10-Gitee、20-钉钉、30-企业微信、31-微信公众号、32-微信开放平台、34-微信小程序、40-支付宝小程序 |
| code | String | 是 | @NotEmpty | 授权码 |
| state | String | 是 | @NotEmpty | state（防 CSRF 校验值） |

**响应**: CommonResult&lt;Boolean&gt;（是否绑定成功）

**业务逻辑**:
1. 调用 authSocialUser 授权获取社交用户：优先按 socialType + code + state 从数据库查询（code 一次性可用，社交登录未绑定时需复用 code）；未命中则通过 SocialClientService 构建 justauth AuthRequest 请求三方平台，保存或更新 SocialUserDO（openid、token、昵称、头像、原始 Token/用户信息等）。
2. 若该社交用户此前绑定过其他用户，删除旧的绑定关系（按 userType + socialUserId）。
3. 若当前用户此前绑定过同社交类型的其他账号，也删除旧绑定关系（按 userType + userId + socialType）。
4. 插入新的 SocialUserBindDO 绑定记录（userId、userType、socialUserId、socialType），返回社交用户 openid。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_000 | 社交授权失败，原因是：{} |

### 1.2 取消社交绑定

- **路径**: DELETE /system/social-user/unbind
- **权限**: 已认证
- **说明**: 按社交类型 + openid 解除当前登录用户与指定社交账号的绑定。

**请求参数 (SocialUserUnbindReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| type | Integer | 是 | @NotNull、@InEnum(SocialTypeEnum) | 社交平台的类型 |
| openid | String | 是 | @NotEmpty | 社交用户的 openid |

**响应**: CommonResult&lt;Boolean&gt;（是否解绑成功）

**业务逻辑**:
1. 按 socialType + openid 查询 SocialUserDO 社交用户，不存在则抛出 SOCIAL_USER_NOT_FOUND。
2. 按 userType + userId + socialType 删除对应的 SocialUserBindDO 绑定关系。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_001 | 社交授权失败，找不到对应的用户 |

### 1.3 获得绑定社交用户列表

- **路径**: GET /system/social-user/get-bind-list
- **权限**: 已认证
- **说明**: 获得当前登录用户已绑定的全部社交用户列表（精简信息）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;SocialUserRespVO&gt;&gt;（仅返回部分字段）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 社交用户编号 |
| type | Integer | 社交平台的类型 |
| openid | String | 社交 openid |
| nickname | String | 用户昵称 |
| avatar | String | 用户头像 |

**业务逻辑**:
1. 按 userId + userType 查询 SocialUserBindDO 绑定列表，为空则直接返回空列表。
2. 按绑定记录中的 socialUserId 集合批量查询 SocialUserDO。
3. Controller 层转换仅保留 id/type/openid/nickname/avatar 精简字段返回。

## 2. 社交用户管理 (SocialUserController)

社交用户档案的只读查询，需 system:social-user:query 权限。

### 2.1 获得社交用户

- **路径**: GET /system/social-user/get
- **权限**: system:social-user:query
- **说明**: 按编号获得社交用户详情。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @Parameter required | 社交用户编号 |

**响应**: CommonResult&lt;SocialUserRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键(自增策略) |
| type | Integer | 社交平台的类型 |
| openid | String | 社交 openid |
| token | String | 社交 token |
| rawTokenInfo | String | 原始 Token 数据，一般是 JSON 格式 |
| nickname | String | 用户昵称 |
| avatar | String | 用户头像 |
| rawUserInfo | String | 原始用户数据，一般是 JSON 格式 |
| code | String | 最后一次的认证 code |
| state | String | 最后一次的认证 state |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 按 id 调用 Mapper selectById 查询 SocialUserDO。
2. 通过 BeanUtils 转换为 SocialUserRespVO 返回。

### 2.2 获得社交用户分页

- **路径**: GET /system/social-user/page
- **权限**: system:social-user:query
- **说明**: 分页查询社交用户列表。

**请求参数 (SocialUserPageReqVO，继承 PageParam: pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| type | Integer | 否 | - | 社交平台的类型 |
| nickname | String | 否 | - | 用户昵称 |
| openid | String | 否 | - | 社交 openid |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;SocialUserRespVO&gt;&gt;，列表项字段同 2.1。

**业务逻辑**:
1. 按条件构造分页查询，调用 Mapper selectPage 查询 SocialUserDO 分页结果。
2. 通过 BeanUtils 转换为 SocialUserRespVO 分页结果返回。

## 3. 社交客户端管理 (SocialClientController)

各社交平台 OAuth 客户端（appId/secret 等）的配置管理。同一 userType + socialType 只允许一条配置。

### 3.1 创建社交客户端

- **路径**: POST /system/social-client/create
- **权限**: system:social-client:create
- **说明**: 新增一个社交平台的客户端配置。

**请求参数 (SocialClientSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| name | String | 是 | @NotNull | 应用名 |
| socialType | Integer | 是 | @NotNull、@InEnum(SocialTypeEnum) | 社交平台的类型 |
| userType | Integer | 是 | @NotNull、@InEnum(UserTypeEnum) | 用户类型 |
| clientId | String | 是 | @NotNull | 客户端编号（appId） |
| clientSecret | String | 是 | @NotNull | 客户端密钥 |
| agentId | String | 否 | @AssertTrue：企业微信必填 | 授权方的网页应用编号 |
| publicKey | String | 否 | @AssertTrue：支付宝小程序必填 | publicKey 公钥 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（1 开启 / 2 禁用） |

**响应**: CommonResult&lt;Long&gt;（新客户端编号）

**业务逻辑**:
1. 校验 userType + socialType 组合唯一，已存在则抛出 SOCIAL_CLIENT_UNIQUE（保证每个端使用某社交登录时能唯一定位配置）。
2. 通过 BeanUtils 转换为 SocialClientDO 插入数据库。
3. 返回新记录 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_211 | 社交客户端已存在配置 |

### 3.2 更新社交客户端

- **路径**: PUT /system/social-client/update
- **权限**: system:social-client:update
- **说明**: 修改已存在的社交客户端配置。

**请求参数 (SocialClientSaveReqVO)**: 字段同 3.1，其中 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验对应 id 的社交客户端存在，不存在抛出 SOCIAL_CLIENT_NOT_EXISTS。
2. 校验 userType + socialType 组合唯一（排除自身 id），重复抛出 SOCIAL_CLIENT_UNIQUE。
3. 通过 BeanUtils 转换后按 id 更新数据库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_210 | 社交客户端不存在 |
| 1_002_018_211 | 社交客户端已存在配置 |

### 3.3 删除社交客户端

- **路径**: DELETE /system/social-client/delete
- **权限**: system:social-client:delete
- **说明**: 按编号删除社交客户端配置。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @Parameter required | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验对应 id 的社交客户端存在，不存在抛出 SOCIAL_CLIENT_NOT_EXISTS。
2. 调用 Mapper deleteById 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_210 | 社交客户端不存在 |

### 3.4 批量删除社交客户端

- **路径**: DELETE /system/social-client/delete-list
- **权限**: system:social-client:delete
- **说明**: 按编号列表批量删除社交客户端配置。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| ids | List&lt;Long&gt; | 是 | @Parameter required | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 调用 Mapper deleteByIds 按编号列表批量删除。

### 3.5 获得社交客户端

- **路径**: GET /system/social-client/get
- **权限**: system:social-client:query
- **说明**: 按编号获得社交客户端详情。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @Parameter required | 编号 |

**响应**: CommonResult&lt;SocialClientRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 应用名 |
| socialType | Integer | 社交平台的类型 |
| userType | Integer | 用户类型 |
| clientId | String | 客户端编号 |
| clientSecret | String | 客户端密钥 |
| agentId | String | 授权方的网页应用编号 |
| publicKey | String | publicKey 公钥 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 调用 Mapper selectById 查询 SocialClientDO。
2. 通过 BeanUtils 转换为 SocialClientRespVO 返回。

### 3.6 获得社交客户端分页

- **路径**: GET /system/social-client/page
- **权限**: system:social-client:query
- **说明**: 分页查询社交客户端列表。

**请求参数 (SocialClientPageReqVO，继承 PageParam: pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| name | String | 否 | - | 应用名 |
| socialType | Integer | 否 | - | 社交平台的类型 |
| userType | Integer | 否 | - | 用户类型 |
| clientId | String | 否 | - | 客户端编号 |
| status | Integer | 否 | - | 状态 |

**响应**: CommonResult&lt;PageResult&lt;SocialClientRespVO&gt;&gt;，列表项字段同 3.5。

**业务逻辑**:
1. 按条件构造分页查询，调用 Mapper selectPage 查询 SocialClientDO 分页结果。
2. 通过 BeanUtils 转换为 SocialClientRespVO 分页结果返回。

## 4. 订阅消息 (SocialClientController)

微信小程序订阅消息发送的调试入口，复用 API 层的完整发送链路。

### 4.1 发送订阅消息

- **路径**: POST /system/social-client/send-subscribe-message
- **权限**: system:social-client:query
- **说明**: 发送微信小程序订阅消息（注释标注"用于测试"），按模板标题匹配模板后发给指定用户。

**请求参数 (SocialWxaSubscribeMessageSendReqDTO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| userId | Long | 是 | @NotNull | 用户编号（关联 AdminUserDO / MemberUserDO 的 id） |
| userType | Integer | 是 | @NotNull | 用户类型（关联 UserTypeEnum） |
| templateTitle | String | 是 | @NotEmpty | 消息模版标题 |
| page | String | 否 | - | 点击模板卡片后跳转的小程序内页面，支持带参数（如 index?foo=bar），不填则无跳转 |
| messages | Map&lt;String, String&gt; | 否 | - | 模板内容的参数（key-value） |

**响应**: 无（void，不返回 CommonResult）

**业务逻辑**:
1. 按 userType 获取小程序订阅消息模板列表（带 Redis 缓存 @Cacheable(WXA_SUBSCRIBE_TEMPLATE)，底层按 DB 配置或 yaml 配置构建并缓存 WxMaService），模板列表为空仅告警并返回。
2. 按 templateTitle 匹配所需模板 TemplateInfo，未匹配到仅告警并返回。
3. 按 userType + userId + 社交类型（微信小程序）查询该用户的绑定社交用户，取其 openid；缺失则仅告警并返回。
4. 按模板 priTmplId + openid 构建订阅消息（语言 zh_CN、miniprogramState 由配置 yudao.wxa-subscribe-message.miniprogram-state 决定、page、messages 数据项），调用微信 subscribeService.sendSubscribeMsg 发送。
5. 微信调用失败抛出 SOCIAL_CLIENT_WEIXIN_MINI_APP_SUBSCRIBE_MESSAGE_ERROR。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_018_202 | 获得小程序订阅消息模版失败 |
| 1_002_018_203 | 发送小程序订阅消息失败 |

## 域相关错误码汇总（前缀 1_002_018）

| 错误码 | 说明 |
|-------|------|
| 1_002_018_000 | 社交授权失败，原因是：{} |
| 1_002_018_001 | 社交授权失败，找不到对应的用户 |
| 1_002_018_200 | 获得手机号失败 |
| 1_002_018_201 | 获得小程序码失败 |
| 1_002_018_202 | 获得小程序订阅消息模版失败 |
| 1_002_018_203 | 发送小程序订阅消息失败 |
| 1_002_018_204 | 上传微信小程序发货信息失败 |
| 1_002_018_205 | 上传微信小程序订单收货信息失败 |
| 1_002_018_210 | 社交客户端不存在 |
| 1_002_018_211 | 社交客户端已存在配置 |
