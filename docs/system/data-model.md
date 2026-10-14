# 数据模型详情

> system 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。作为全平台的后台管理基础设施，system 模块承载 RBAC 用户/角色/菜单权限、组织架构（部门/岗位）、多租户、字典主数据、认证登录（账号/短信/社交/OAuth2.0）、消息触达（短信/邮件/站内信）与日志审计，共 32 张数据表。
>
> 说明：当前仓库为 JDK8 分支（revision 2026.09-jdk8-SNAPSHOT，Spring Boot 2.7.x），文档中的类型与注解均以实际代码为准。所有 DO 均标注 `@KeySequence("{table}_seq")`，用于 Oracle/PostgreSQL/Kingbase/DB2/H2 等非自增数据库的主键序列，MySQL 下无实际作用。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，实现 Serializable/TransPojo）
│   creator       String          创建者（用户编号，INSERT 时自动填充）
│   createTime    LocalDateTime   创建时间（INSERT 时自动填充）
│   updater       String          更新者（INSERT/UPDATE 时自动填充）
│   updateTime    LocalDateTime   最后更新时间（INSERT/UPDATE 时自动填充）
│   deleted       Boolean         逻辑删除标记（@TableLogic）
│
├── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO（多租户基类）
│   │   tenantId   Long            多租户编号（由租户拦截器自动填充与过滤）
│   │
│   └── system 模块 7 个 DO 直接继承：核心的租户隔离实体
│       AdminUserDO / DeptDO / RoleDO / RoleMenuDO /
│       OAuth2AccessTokenDO / OAuth2RefreshTokenDO / SocialClientDO
│
└── 其余 25 个 DO 继承 BaseDO，按租户策略分为两类：

    【租户隔离表，未标注 @TenantIgnore（11 个）】
    DO 中无 tenantId 字段，但表结构含 tenant_id 列，
    由 TenantLineInnerInterceptor 在 SQL 层自动填充/过滤：
    PostDO / UserPostDO / UserRoleDO            岗位与角色关联
    OAuth2CodeDO / OAuth2ApproveDO              OAuth2 授权码/批准
    NotifyMessageDO / NoticeDO                  站内信/通知公告
    SocialUserDO / SocialUserBindDO             社交用户/绑定
    LoginLogDO / OperateLogDO                   登录/操作日志

    【全局表，@TenantIgnore 标注在 DO 类上（14 个）】
    租户拦截器视为全局表，SQL 不追加 tenant_id 过滤：
    MenuDO                                      菜单（全租户共享的权限资源）
    DictTypeDO / DictDataDO                     字典（主数据）
    TenantDO / TenantPackageDO                  租户自身与其套餐（管理租户的表）
    OAuth2ClientDO                              OAuth2 客户端定义
    SmsChannelDO / SmsTemplateDO / SmsLogDO / SmsCodeDO       短信四表
    MailAccountDO / MailTemplateDO / MailLogDO                邮件三表
    NotifyTemplateDO                            站内信模板
```

**使用规则**：

- **BaseDO**：所有 DO 的公共基类，提供审计字段（creator/createTime/updater/updateTime）与逻辑删除（deleted）。字段值由 MyBatis-Plus 的 `FieldFill` 机制自动填充，业务代码不应手工设置（DO 提供 `clean()` 方法清空，防止前端注入）。
- **TenantBaseDO**：需要按租户隔离且 DO 层直接读写 `tenantId` 的核心业务实体使用。system 模块中用户、部门、角色、角色菜单、OAuth2 令牌、社交客户端属于此类——这些数据是租户的"私有资产"，是租户隔离的第一批对象。
- **BaseDO + 无 @TenantIgnore**：DO 不携带 tenantId 字段，但对应表结构含 `tenant_id` 列，租户隔离在 SQL 拦截器层完成（INSERT 自动补列、SELECT 自动追加 `WHERE tenant_id = ?`）。适用于关联表、日志、通知等"从属"数据。
- **BaseDO + @TenantIgnore**：平台级全局数据，所有租户共享同一份（菜单、字典、消息模板/渠道）或本身是"管理租户的表"（租户、套餐、OAuth2 客户端）。注意：OAuth2 访问/刷新令牌虽然继承 TenantBaseDO（令牌按租户隔离），但客户端定义是全局的。
- **特例**：`DictTypeDO` 额外有 `deletedTime` 字段，配合软删实现"删除后可重建同名类型"的唯一性处理；`MailLogDO` 在 BaseDO 之外又显式 `implements Serializable`（冗余声明）。

## 2. 核心 DO 实体

### 2.1 用户与组织聚合（user / dept）

#### AdminUserDO (system_users)

管理后台的用户账号，全系统权限体系的主体，被 OAuth2 令牌、社交绑定、各类日志、消息记录通过 `userId + userType` 引用，也是 `AdminUserApi` 对外暴露的核心实体。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 用户ID，主键自增 |
| username | String | username | 用户账号（登录名） |
| password | String | password | 加密后的密码（BCryptPasswordEncoder，盐内置于密文） |
| nickname | String | nickname | 用户昵称 |
| remark | String | remark | 备注 |
| deptId | Long | dept_id | 部门 ID，关联 DeptDO.id |
| postIds | Set\<Long\> | post_ids | 岗位编号数组，JSON 存储（JacksonTypeHandler，autoResultMap） |
| email | String | email | 用户邮箱 |
| mobile | String | mobile | 手机号码 |
| sex | Integer | sex | 用户性别，枚举 SexEnum |
| avatar | String | avatar | 用户头像 |
| status | Integer | status | 帐号状态，枚举 CommonStatusEnum（0 开启 / 1 禁用） |
| loginIp | String | login_ip | 最后登录 IP |
| loginDate | LocalDateTime | login_date | 最后登录时间 |

**继承**: TenantBaseDO
**索引**: 主键 `id`；普通索引 `idx_username(username)`（登录查询）、`idx_mobile(mobile)`（手机号登录/找回）、`idx_email(email)`、`idx_dept_id(dept_id)`（按部门查成员）。
**特性**: 表名 `system_users` 复数——SQL Server 中 `system_user` 是关键字；`postIds` 用 JSON 列冗余岗位关系，与 `system_user_post` 关联表双写。

#### DeptDO (system_dept)

组织架构部门，树形结构（parentId 自关联），是 AdminUserDO 的归属与数据权限（DataScopeEnum）的作用范围。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 部门ID，主键自增 |
| name | String | name | 部门名称 |
| parentId | Long | parent_id | 父部门 ID，关联本表 id（根节点固定 0，常量 PARENT_ID_ROOT） |
| sort | Integer | sort | 显示顺序 |
| leaderUserId | Long | leader_user_id | 负责人，关联 AdminUserDO.id |
| phone | String | phone | 联系电话 |
| email | String | email | 邮箱 |
| status | Integer | status | 部门状态，枚举 CommonStatusEnum |

**继承**: TenantBaseDO
**索引**: 主键 `id`；无二级索引（树形遍历在内存中完成，数据量小）。

#### PostDO (system_post)

岗位信息，与用户多对多（经 UserPostDO），同时以 JSON 冗余在 AdminUserDO.postIds。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 岗位序号，主键自增 |
| name | String | name | 岗位名称 |
| code | String | code | 岗位编码 |
| sort | Integer | sort | 岗位排序 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；无二级索引。

#### UserPostDO (system_user_post)

用户与岗位的关联表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增主键 |
| userId | Long | user_id | 用户 ID，关联 AdminUserDO.id |
| postId | Long | post_id | 岗位 ID，关联 PostDO.id（DO 注释误写为"角色 ID"，以关联关系为准） |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；无二级索引（按 userId/postId 的查询走全表或覆盖主键，数据量小）。

### 2.2 权限聚合（permission，RBAC 模型）

#### RoleDO (system_role)

角色定义，RBAC 的中枢：向上被 UserRoleDO 关联用户，向下经 RoleMenuDO 圈定菜单权限，并通过 dataScope 控制数据权限。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 角色ID，主键自增 |
| name | String | name | 角色名称 |
| code | String | code | 角色标识（如 super_admin、tenant_admin） |
| sort | Integer | sort | 角色排序 |
| status | Integer | status | 角色状态，枚举 CommonStatusEnum |
| type | Integer | type | 角色类型，枚举 RoleTypeEnum（1 系统内置 / 2 自定义） |
| remark | String | remark | 备注 |
| dataScope | Integer | data_scope | 数据范围，枚举 DataScopeEnum（1 全部 / 2 自定义部门 / 3 本部门 / 4 本部门及以下 / 5 仅本人） |
| dataScopeDeptIds | Set\<Long\> | data_scope_dept_ids | 自定义数据范围的部门数组，仅 dataScope=2 时生效，JSON 存储 |

**继承**: TenantBaseDO
**索引**: 主键 `id`；无二级索引。

#### MenuDO (system_menu)

菜单/权限资源，树形结构（parentId 自关联），权限标识 permission 配合 `@PreAuthorize` 实现按钮级权限控制。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 菜单编号，主键自增（根节点固定 0，常量 ID_ROOT） |
| name | String | name | 菜单名称 |
| permission | String | permission | 权限标识，格式 `${系统}:${模块}:${操作}`（如 system:user:create） |
| type | Integer | type | 菜单类型，枚举 MenuTypeEnum（1 目录 / 2 菜单 / 3 按钮） |
| sort | Integer | sort | 显示顺序 |
| parentId | Long | parent_id | 父菜单 ID，关联本表 id |
| path | String | path | 路由地址（http(s) 开头为外链） |
| icon | String | icon | 菜单图标 |
| component | String | component | 组件路径 |
| componentName | String | component_name | 组件名（keepAlive 缓存必需） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| visible | Boolean | visible | 是否可见（false 时路由存在但不显示在侧边栏） |
| keepAlive | Boolean | keep_alive | 是否缓存（Vue 路由 keep-alive） |
| alwaysShow | Boolean | always_show | 只有一个子菜单时是否仍显示自己 |

**继承**: BaseDO，类上标注 `@TenantIgnore`（菜单是全租户共享的权限资源定义）
**索引**: 主键 `id`；无二级索引（树形结构内存组装）。
**特性**: 租户套餐（TenantPackageDO.menuIds）与角色授权（RoleMenuDO）共同决定某租户某角色可见的菜单集合。

#### RoleMenuDO (system_role_menu)

角色与菜单的关联表，授权操作的核心落点。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增主键 |
| roleId | Long | role_id | 角色ID，关联 RoleDO.id |
| menuId | Long | menu_id | 菜单ID，关联 MenuDO.id |

**继承**: TenantBaseDO（授权关系按租户隔离，租户分配菜单时仅能从本租户套餐范围内选择）
**索引**: 主键 `id`；普通索引 `idx_role_id(role_id)` —— 按角色加载其全部菜单授权。

#### UserRoleDO (system_user_role)

用户与角色的关联表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增主键 |
| userId | Long | user_id | 用户 ID，关联 AdminUserDO.id |
| roleId | Long | role_id | 角色 ID，关联 RoleDO.id |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_user_id(user_id)` —— 登录后按用户加载角色集合。

### 2.3 多租户聚合（tenant）

#### TenantDO (system_tenant)

租户主表，每个租户一条记录；系统内置租户使用 `packageId = 0`（常量 PACKAGE_ID_SYSTEM）标识不绑定套餐。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 租户编号，主键自增 |
| name | String | name | 租户名（唯一，Service 层校验） |
| contactUserId | Long | contact_user_id | 联系人的用户编号，关联 AdminUserDO.id（租户管理员账号） |
| contactName | String | contact_name | 联系人姓名 |
| contactMobile | String | contact_mobile | 联系手机 |
| status | Integer | status | 租户状态，枚举 CommonStatusEnum |
| websites | List\<String\> | websites | 绑定域名列表（StringListTypeHandler，逗号分隔存储；兼容小程序 appid） |
| packageId | Long | package_id | 租户套餐编号，关联 TenantPackageDO.id |
| expireTime | LocalDateTime | expire_time | 过期时间（过期后禁止登录） |
| accountCount | Integer | account_count | 账号数量上限 |

**继承**: BaseDO，类上标注 `@TenantIgnore`（管理租户的表本身不能被租户过滤）
**索引**: 主键 `id`；无二级索引（按 name/域名查租户在 Service 层全量缓存）。

#### TenantPackageDO (system_tenant_package)

租户套餐，定义一类租户可使用的菜单集合。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 套餐编号，主键自增 |
| name | String | name | 套餐名（唯一，Service 层校验） |
| status | Integer | status | 租户套餐状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |
| menuIds | Set\<Long\> | menu_ids | 关联的菜单编号集合，JSON 存储（JacksonTypeHandler） |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引。

### 2.4 字典聚合（dict）

#### DictTypeDO (system_dict_type)

字典类型定义（如 system_user_sex、common_status），全平台的枚举值元数据来源。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 字典主键，主键自增 |
| name | String | name | 字典名称（如"用户性别"） |
| type | String | type | 字典类型（如 system_user_sex），业务按 type 取值 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |
| deletedTime | LocalDateTime | deleted_time | 删除时间（软删辅助字段，本模块特有） |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；type 的唯一性由 Service 层校验（配合 deletedTime 软删后允许重建同名类型），数据库层未建唯一索引。
**特性**: `deletedTime` 是全模块唯一的软删辅助时间字段——逻辑删除时记录时间，使"同名 type"在旧记录软删后可重新创建。

#### DictDataDO (system_dict_data)

字典数据项，一条 DictTypeDO 对应多条 DictDataDO。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 字典数据编号，主键自增 |
| sort | Integer | sort | 字典排序 |
| label | String | label | 字典标签（展示值，如"男"） |
| value | String | value | 字典值（存储值，如 "1"） |
| dictType | String | dict_type | 字典类型，冗余关联 DictTypeDO.type（字符串弱关联） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| colorType | String | color_type | 颜色类型（element-ui 语义色：default/primary/success/info/warning/danger） |
| cssClass | String | css_class | css 样式类（FieldStrategy.ALWAYS，允许更新为空） |
| remark | String | remark | 备注 |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引（全量加载进本地/Redis 缓存后按 dictType 分组）。

### 2.5 OAuth2 认证聚合（oauth2）

#### OAuth2ClientDO (system_oauth2_client)

OAuth2 客户端定义（接入方应用），全局唯一的一份配置。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| clientId | String | client_id | 客户端编号（业务主键，如 default） |
| secret | String | secret | 客户端密钥 |
| name | String | name | 应用名 |
| logo | String | logo | 应用图标 |
| description | String | description | 应用描述 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| accessTokenValiditySeconds | Integer | access_token_validity_seconds | 访问令牌有效期（秒） |
| refreshTokenValiditySeconds | Integer | refresh_token_validity_seconds | 刷新令牌有效期（秒） |
| redirectUris | List\<String\> | redirect_uris | 可重定向的 URI 地址列表，JSON 存储 |
| authorizedGrantTypes | List\<String\> | authorized_grant_types | 授权类型（模式），枚举 OAuth2GrantTypeEnum（password/authorization_code/implicit/refresh_token/client_credentials），JSON 存储 |
| scopes | List\<String\> | scopes | 授权范围，JSON 存储 |
| autoApproveScopes | List\<String\> | auto_approve_scopes | 自动授权的 Scope（code 授权时自动通过），JSON 存储 |
| authorities | List\<String\> | authorities | 权限，JSON 存储 |
| resourceIds | List\<String\> | resource_ids | 资源列表，JSON 存储 |
| additionalInformation | String | additional_information | 附加信息，JSON 格式字符串 |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；普通索引 `idx_client_id(client_id)` —— 按客户端编号加载配置。

#### OAuth2AccessTokenDO (system_oauth2_access_token)

访问令牌，认证后的每次请求都携带其中 accessToken，经 TokenAuthenticationFilter 反查本表完成鉴权。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| accessToken | String | access_token | 访问令牌（UUID） |
| refreshToken | String | refresh_token | 刷新令牌，关联 OAuth2RefreshTokenDO.refreshToken |
| userId | Long | user_id | 用户编号（AdminUserDO 或 MemberUserDO，由 userType 区分） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| userInfo | Map\<String, String\> | user_info | 用户信息快照，JSON 存储 |
| clientId | String | client_id | 客户端编号，关联 OAuth2ClientDO.clientId |
| scopes | List\<String\> | scopes | 授权范围，JSON 存储 |
| expiresTime | LocalDateTime | expires_time | 过期时间（TokenCleanJob 定时清理过期记录） |

**继承**: TenantBaseDO
**索引**: 主键 `id`；普通索引 `idx_access_token(access_token)`（每次请求鉴权的高频查询）、`idx_refresh_token(refresh_token)`（刷新令牌时反查）。

#### OAuth2RefreshTokenDO (system_oauth2_refresh_token)

刷新令牌，用于在访问令牌过期后换发新令牌。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| refreshToken | String | refresh_token | 刷新令牌 |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| clientId | String | client_id | 客户端编号，关联 OAuth2ClientDO.clientId |
| scopes | List\<String\> | scopes | 授权范围，JSON 存储 |
| expiresTime | LocalDateTime | expires_time | 过期时间 |

**继承**: TenantBaseDO
**索引**: 主键 `id`；普通索引 `idx_refresh_token(refresh_token)`。
**特性**: `@KeySequence` 复用 `system_oauth2_access_token_seq`——Oracle 序列名长度受限，代码注释说明"反正也没啥问题"。

#### OAuth2CodeDO (system_oauth2_code)

OAuth2 授权码（authorization_code 模式的一次性凭据）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| code | String | code | 授权码 |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| clientId | String | client_id | 客户端编号，关联 OAuth2ClientDO.clientId |
| scopes | List\<String\> | scopes | 授权范围，JSON 存储 |
| redirectUri | String | redirect_uri | 重定向地址 |
| state | String | state | 状态（防 CSRF 的透传参数） |
| expiresTime | LocalDateTime | expires_time | 过期时间 |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_code(code)` —— 按授权码换取令牌的高频查询。

#### OAuth2ApproveDO (system_oauth2_approve)

OAuth2 批准记录，用户在 SSO 授权页对 scope 的接受/拒绝结果。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| clientId | String | client_id | 客户端编号，关联 OAuth2ClientDO.clientId |
| scope | String | scope | 授权范围（单个 scope 一条记录） |
| approved | Boolean | approved | 是否接受（true 接受 / false 拒绝） |
| expiresTime | LocalDateTime | expires_time | 过期时间（批准记忆的有效期） |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_user_id_user_type_client_id(user_id, user_type, client_id)` —— 按用户+客户端加载其批准记录。

### 2.6 社交登录聚合（social）

#### SocialClientDO (system_social_client)

社交客户端配置，对应 JustAuth 的 AuthConfig；每个租户可为自己的管理端/会员端配置独立的第三方应用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 应用名 |
| socialType | Integer | social_type | 社交类型，枚举 SocialTypeEnum（微信公众号/小程序/钉钉/支付宝等） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum（不同用户类型对应不同小程序配置） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| clientId | String | client_id | 客户端 id（三方平台发放） |
| clientSecret | String | client_secret | 客户端 Secret |
| agentId | String | agent_id | 代理编号（企业微信：授权方网页应用 ID） |
| publicKey | String | public_key | 公钥（支付宝：支付宝公钥） |

**继承**: TenantBaseDO
**索引**: 主键 `id`；无二级索引（按 tenantId + socialType + userType 组合查询，租户拦截器先行过滤）。

#### SocialUserDO (system_social_user)

社交（三方）平台的用户信息。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增主键 |
| type | Integer | type | 社交平台的类型，枚举 SocialTypeEnum |
| openid | String | openid | 社交 openid（平台内唯一） |
| token | String | token | 社交 token |
| rawTokenInfo | String | raw_token_info | 原始 Token 数据，JSON 格式 |
| nickname | String | nickname | 用户昵称 |
| avatar | String | avatar | 用户头像 |
| rawUserInfo | String | raw_user_info | 原始用户数据，JSON 格式 |
| code | String | code | 最后一次的认证 code |
| state | String | state | 最后一次的认证 state |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_type_openid(type, openid)`（按平台+openid 定位社交用户）、`idx_type_code_state(type, code, state)`（回调时按 code/state 反查）。

#### SocialUserBindDO (system_social_user_bind)

社交用户与本系统用户的绑定关系。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 关联的用户编号（AdminUserDO 或 MemberUserDO） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| socialUserId | Long | social_user_id | 社交平台的用户编号，关联 SocialUserDO.id |
| socialType | Integer | social_type | 社交平台的类型，冗余 SocialUserDO.type |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_user_type_social_user_id(user_type, social_user_id)` —— 三方登录回调时按社交用户反查绑定。

### 2.7 短信聚合（sms）

#### SmsChannelDO (system_sms_channel)

短信渠道（阿里云、腾讯云、调试钉钉等），模板方法模式下的具体渠道配置。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 渠道编号，主键自增 |
| signature | String | signature | 短信签名 |
| code | String | code | 渠道编码，枚举 SmsChannelEnum（ALIYUN/TENCENT/DEBUG_DING_TALK 等） |
| status | Integer | status | 启用状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |
| apiKey | String | api_key | 短信 API 的账号 |
| apiSecret | String | api_secret | 短信 API 的密钥 |
| callbackUrl | String | callback_url | 短信发送回调 URL |

**继承**: BaseDO，类上标注 `@TenantIgnore`（渠道与签名是平台级资源）
**索引**: 主键 `id`；无二级索引。

#### SmsTemplateDO (system_sms_template)

短信模板，属于某渠道，code 全局唯一用于业务侧引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增编号，主键 |
| type | Integer | type | 短信类型，枚举 SmsTemplateTypeEnum（1 验证码 / 2 通知 / 3 营销） |
| status | Integer | status | 启用状态，枚举 CommonStatusEnum |
| code | String | code | 模板编码（保证唯一，Service 层校验） |
| name | String | name | 模板名称 |
| content | String | content | 模板内容，参数用 `{name}` 占位 |
| params | List\<String\> | params | 参数数组（根据 content 自动解析生成），JSON 存储 |
| remark | String | remark | 备注 |
| apiTemplateId | String | api_template_id | 短信 API 的模板编号（三方平台侧 ID） |
| channelId | Long | channel_id | 短信渠道编号，关联 SmsChannelDO.id |
| channelCode | String | channel_code | 短信渠道编码，冗余 SmsChannelDO.code |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引（按 code 查询走 Service 缓存）。

#### SmsLogDO (system_sms_log)

短信发送日志，记录每一次发送的渠道/模板/手机号/发送结果/接收回执全链路。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增编号，主键 |
| channelId | Long | channel_id | 短信渠道编号，关联 SmsChannelDO.id |
| channelCode | String | channel_code | 短信渠道编码，冗余 SmsChannelDO.code |
| templateId | Long | template_id | 模板编号，关联 SmsTemplateDO.id |
| templateCode | String | template_code | 模板编码，冗余 SmsTemplateDO.code |
| templateType | Integer | template_type | 短信类型，冗余 SmsTemplateDO.type |
| templateContent | String | template_content | 基于 content 格式化后的最终内容 |
| templateParams | Map\<String, Object\> | template_params | 模板参数，JSON 存储 |
| apiTemplateId | String | api_template_id | 短信 API 的模板编号，冗余 |
| mobile | String | mobile | 手机号 |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| sendStatus | Integer | send_status | 发送状态，枚举 SmsSendStatusEnum |
| sendTime | LocalDateTime | send_time | 发送时间 |
| apiSendCode | String | api_send_code | 短信 API 发送结果编码（三方错误码可能是字符串，故用 String） |
| apiSendMsg | String | api_send_msg | 短信 API 发送失败提示 |
| apiRequestId | String | api_request_id | 短信 API 发送返回的唯一请求 ID（排错定位） |
| apiSerialNo | String | api_serial_no | 短信 API 发送返回的序号（关联三方平台发送记录） |
| receiveStatus | Integer | receive_status | 接收状态，枚举 SmsReceiveStatusEnum |
| receiveTime | LocalDateTime | receive_time | 接收时间 |
| apiReceiveCode | String | api_receive_code | 短信 API 接收结果编码 |
| apiReceiveMsg | String | api_receive_msg | 短信 API 接收结果提示 |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引（管理端分页查询按条件过滤，数据量可控）。

#### SmsCodeDO (system_sms_code)

手机验证码，登录/注册/改密等场景的一次性验证码。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| mobile | String | mobile | 手机号 |
| code | String | code | 验证码（6 位） |
| scene | Integer | scene | 发送场景（1 管理后台登录 / 2 会员注册等） |
| createIp | String | create_ip | 创建 IP（发送时的客户端 IP，限流依据） |
| todayIndex | Integer | today_index | 今日发送的第几条（每日限流计数） |
| used | Boolean | used | 是否使用 |
| usedTime | LocalDateTime | used_time | 使用时间 |
| usedIp | String | used_ip | 使用 IP |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；普通索引 `idx_mobile(mobile)` —— 按手机号查最新验证码校验（DO 注释显式说明该索引用途）。

### 2.8 邮件聚合（mail）

#### MailAccountDO (system_mail_account)

发件邮箱账号（SMTP 配置）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键，自增 |
| mail | String | mail | 邮箱地址 |
| username | String | username | SMTP 用户名 |
| password | String | password | SMTP 密码/授权码 |
| host | String | host | SMTP 服务器域名 |
| port | Integer | port | SMTP 服务器端口 |
| sslEnable | Boolean | ssl_enable | 是否开启 SSL |
| starttlsEnable | Boolean | starttls_enable | 是否开启 STARTTLS |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引。

#### MailTemplateDO (system_mail_template)

邮件模板，绑定一个发件账号。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键，自增 |
| name | String | name | 模版名称 |
| code | String | code | 模版编码（业务引用键） |
| accountId | Long | account_id | 发送的邮箱账号编号，关联 MailAccountDO.id |
| nickname | String | nickname | 发送人名称 |
| title | String | title | 邮件标题（支持 {param} 占位） |
| content | String | content | 模版内容（支持 {param} 占位） |
| params | List\<String\> | params | 参数数组（自动根据内容生成），JSON 存储 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引。

#### MailLogDO (system_mail_log)

邮件发送日志，记录每一次邮件发送（支持多收件人/抄送/密送）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日志编号，主键自增 |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| toMails | List\<String\> | to_mails | 接收邮箱地址列表（StringListTypeHandler） |
| ccMails | List\<String\> | cc_mails | 抄送邮箱地址列表（StringListTypeHandler） |
| bccMails | List\<String\> | bcc_mails | 密送邮箱地址列表（StringListTypeHandler） |
| accountId | Long | account_id | 邮箱账号编号，关联 MailAccountDO.id |
| fromMail | String | from_mail | 发送邮箱地址，冗余 MailAccountDO.mail |
| templateId | Long | template_id | 模版编号，关联 MailTemplateDO.id |
| templateCode | String | template_code | 模版编码，冗余 MailTemplateDO.code |
| templateNickname | String | template_nickname | 模版发送人名称，冗余 |
| templateTitle | String | template_title | 格式化后的邮件标题 |
| templateContent | String | template_content | 基于 content 格式化后的最终内容 |
| templateParams | Map\<String, Object\> | template_params | 模版参数，JSON 存储 |
| sendStatus | Integer | send_status | 发送状态，枚举 MailSendStatusEnum |
| sendTime | LocalDateTime | send_time | 发送时间 |
| sendMessageId | String | send_message_id | 发送返回的消息 ID |
| sendException | String | send_exception | 发送异常信息 |

**继承**: BaseDO（冗余 implements Serializable），类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引。

### 2.9 站内信聚合（notify）

#### NotifyTemplateDO (system_notify_template)

站内信模板，业务方经 `NotifyMessageSendApi` 按 code 发送。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键，自增 |
| name | String | name | 模版名称 |
| code | String | code | 模版编码（业务引用键） |
| type | Integer | type | 模版类型，对应字典 system_notify_template_type |
| nickname | String | nickname | 发送人名称（展示用） |
| content | String | content | 模版内容（{param} 占位） |
| params | List\<String\> | params | 参数数组，JSON 存储 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**继承**: BaseDO，类上标注 `@TenantIgnore`
**索引**: 主键 `id`；无二级索引。

#### NotifyMessageDO (system_notify_message)

站内信消息，按模板渲染后投递给具体用户的一封"站内信"。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 站内信编号，主键自增 |
| userId | Long | user_id | 用户编号（AdminUserDO 或 MemberUserDO） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| templateId | Long | template_id | 模版编号，关联 NotifyTemplateDO.id |
| templateCode | String | template_code | 模版编码，冗余 |
| templateType | Integer | template_type | 模版类型，冗余 NotifyTemplateDO.type |
| templateNickname | String | template_nickname | 模版发送人名称，冗余 |
| templateContent | String | template_content | 基于 content 格式化后的内容 |
| templateParams | Map\<String, Object\> | template_params | 模版参数，JSON 存储 |
| readStatus | Boolean | read_status | 是否已读 |
| readTime | LocalDateTime | read_time | 阅读时间 |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_user_id_user_type_read_status(user_id, user_type, read_status)` —— 站内信列表与"未读数"统计的组合查询。

### 2.10 通知公告与日志审计（notice / logger）

#### NoticeDO (system_notice)

通知公告，管理后台发布的公告/通知。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 公告ID，主键自增 |
| title | String | title | 公告标题 |
| type | Integer | type | 公告类型，枚举 NoticeTypeEnum（1 通知 / 2 公告） |
| content | String | content | 公告内容（富文本） |
| status | Integer | status | 公告状态，枚举 CommonStatusEnum |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；无二级索引。

#### LoginLogDO (system_login_log)

登录日志，记录登录与登出两类行为（LoginLogTypeEnum）及成功/失败结果。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日志主键，自增 |
| logType | Integer | log_type | 日志类型，枚举 LoginLogTypeEnum（100 登录 / 101 登出） |
| traceId | String | trace_id | 链路追踪编号（串联访问日志/错误日志排错） |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| username | String | username | 用户账号（冗余快照——账号可变更，日志按当时值记录） |
| result | Integer | result | 登录结果，枚举 LoginResultEnum（0 成功，非 0 为各错误码） |
| userIp | String | user_ip | 用户 IP |
| userAgent | String | user_agent | 浏览器 UA |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_username(username)`（按账号查登录历史）、`idx_create_time(create_time)`（时间范围筛选）。
**特性**: 经 `LoginLogApi` 暴露给其他模块（含 framework 认证过滤器）异步写入。

#### OperateLogDO (system_operate_log)

操作日志（V2 版本），由 @LogRecord 注解经 OperateLogAspect 解析方法参数/返回值后异步落库。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日志主键，自增 |
| traceId | String | trace_id | 链路追踪编号 |
| userId | Long | user_id | 用户编号（AdminUserDO 或 MemberUserDO） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| type | String | type | 操作模块类型（如"用户管理"，源自 @LogRecord 模块名） |
| subType | String | sub_type | 操作名（如"创建用户"） |
| bizId | Long | biz_id | 操作模块业务编号（如被操作的用户 id） |
| action | String | action | 日志内容，记录操作明细（如"将性别从男改成女"） |
| extra | String | extra | 拓展字段，JSON 格式（记录复杂业务的附加键值） |
| requestMethod | String | request_method | 请求方法名 |
| requestUrl | String | request_url | 请求地址 |
| userIp | String | user_ip | 用户 IP |
| userAgent | String | user_agent | 浏览器 UA |

**继承**: BaseDO（表含 tenant_id 列，SQL 拦截器层隔离）
**索引**: 主键 `id`；普通索引 `idx_user_id(user_id)`（按操作人筛选）、`idx_create_time(create_time)`（时间范围筛选）。

## 3. 实体关系

system 模块内无数据库层外键，全部为逻辑外键（代码层维护），核心关系如下：

```
【RBAC 权限模型 —— 三层关联】
AdminUserDO.id ──< UserRoleDO >── RoleDO.id ──< RoleMenuDO >── MenuDO.id
AdminUserDO.deptId ────────────────────────────────────────→ DeptDO.id（部门树，parentId 自关联）
AdminUserDO.postIds(JSON) ≈── UserPostDO(user_id, post_id) ──→ PostDO.id
MenuDO.parentId ──→ MenuDO.id（菜单树自关联）
RoleDO.dataScopeDeptIds(JSON) ──→ DeptDO.id 集合（自定义数据权限范围）

【多租户】
TenantDO.packageId ──→ TenantPackageDO.id
TenantPackageDO.menuIds(JSON) ──→ MenuDO.id 集合（圈定租户可用菜单上限）
TenantDO.contactUserId ──→ AdminUserDO.id（租户管理员账号）
AdminUserDO/DeptDO/RoleDO/RoleMenuDO.tenantId ──→ TenantDO.id

【OAuth2 认证】
OAuth2ClientDO.clientId ←── clientId ──┬─ OAuth2AccessTokenDO
                                       ├─ OAuth2RefreshTokenDO
                                       ├─ OAuth2CodeDO
                                       └─ OAuth2ApproveDO
OAuth2AccessTokenDO.refreshToken ⇄ OAuth2RefreshTokenDO.refreshToken（一对一同源换发）
上述四表 (userId, userType) ──→ AdminUserDO.id 或 MemberUserDO.id（UserTypeEnum 区分）

【社交登录】
SocialClientDO（tenantId + socialType + userType）── 提供三方客户端配置（租户级）
SocialUserBindDO.socialUserId ──→ SocialUserDO.id
SocialUserBindDO.(userId, userType) ──→ AdminUserDO.id 或 MemberUserDO.id

【消息触达】
SmsTemplateDO.channelId ──→ SmsChannelDO.id        （短信：模板从属渠道）
SmsLogDO.(channelId/channelCode + templateId/templateCode/…) ── 冗余快照，弱关联
SmsCodeDO.mobile ── 独立验证码记录（无外键，按手机号 + scene 校验）
MailTemplateDO.accountId ──→ MailAccountDO.id      （邮件：模板从属账号）
MailLogDO.(accountId/fromMail + templateId/templateCode/…) ── 冗余快照，弱关联
NotifyMessageDO.templateId ──→ NotifyTemplateDO.id （站内信：消息从属模板）

【日志审计】
LoginLogDO / OperateLogDO.(userId, userType) ──→ AdminUserDO.id 或 MemberUserDO.id
（日志表只存快照，用户删除后日志保留；traceId 串联 infra 模块的访问/错误日志）
```

共性说明：

- **多态用户引用**：`(userId, userType)` 组合是贯穿全模块的"弱外键"，userType=2 指向本模块 AdminUserDO，userType=1 指向 member 模块的 MemberUserDO（通过反射调用避免编译依赖）。
- **模板-日志快照模式**：短信/邮件/站内信的 Log 表大量冗余模板字段（code/content/params 等），保证模板修改或删除后历史记录仍完整可读。
- **JSON 列**：`postIds`、`dataScopeDeptIds`、`menuIds`、`websites`、`redirectUris`、`scopes`、`params`、`templateParams` 等集合/Map 字段经 JacksonTypeHandler/StringListTypeHandler 以 JSON 字符串落库（需要 `autoResultMap = true`）。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|------|
| system_users | AdminUserDO | 用户信息表（管理后台账号） |
| system_dept | DeptDO | 部门表（树形组织架构） |
| system_post | PostDO | 岗位信息表 |
| system_user_post | UserPostDO | 用户岗位关联表 |
| system_role | RoleDO | 角色信息表（含数据权限范围） |
| system_menu | MenuDO | 菜单权限表（目录/菜单/按钮） |
| system_role_menu | RoleMenuDO | 角色和菜单关联表 |
| system_user_role | UserRoleDO | 用户和角色关联表 |
| system_tenant | TenantDO | 租户表 |
| system_tenant_package | TenantPackageDO | 租户套餐表 |
| system_dict_type | DictTypeDO | 字典类型表 |
| system_dict_data | DictDataDO | 字典数据表 |
| system_oauth2_client | OAuth2ClientDO | OAuth2 客户端表 |
| system_oauth2_access_token | OAuth2AccessTokenDO | OAuth2 访问令牌表 |
| system_oauth2_refresh_token | OAuth2RefreshTokenDO | OAuth2 刷新令牌表 |
| system_oauth2_code | OAuth2CodeDO | OAuth2 授权码表 |
| system_oauth2_approve | OAuth2ApproveDO | OAuth2 批准表（SSO scope 授权记忆） |
| system_social_client | SocialClientDO | 社交客户端表（三方登录配置） |
| system_social_user | SocialUserDO | 社交用户表 |
| system_social_user_bind | SocialUserBindDO | 社交用户绑定表 |
| system_sms_channel | SmsChannelDO | 短信渠道表 |
| system_sms_template | SmsTemplateDO | 短信模板表 |
| system_sms_log | SmsLogDO | 短信日志表 |
| system_sms_code | SmsCodeDO | 手机验证码表 |
| system_mail_account | MailAccountDO | 邮箱账号表（SMTP 配置） |
| system_mail_template | MailTemplateDO | 邮件模版表 |
| system_mail_log | MailLogDO | 邮件日志表 |
| system_notify_template | NotifyTemplateDO | 站内信模板表 |
| system_notify_message | NotifyMessageDO | 站内信消息表 |
| system_notice | NoticeDO | 通知公告表 |
| system_login_log | LoginLogDO | 登录日志表（系统访问记录） |
| system_operate_log | OperateLogDO | 操作日志表（V2 版本） |
