# 数据模型详情

> system 模块的核心数据模型，包括 DO（数据对象）、DTO（数据传输对象）、VO（视图对象）及其之间的关系。

## 1. 实体继承体系

```
BaseDO
├── id: Long                    # 主键
├── creator: String             # 创建人
├── createTime: LocalDateTime   # 创建时间
├── updater: String             # 更新人
├── updateTime: LocalDateTime   # 更新时间
└── deleted: Boolean            # 逻辑删除标记（false=未删除，true=已删除）

TenantBaseDO extends BaseDO
└── tenantId: Long              # 租户编号（多租户隔离）
```

**使用规则**:
- 需要租户隔离的表继承 `TenantBaseDO`（如用户、角色、部门等）
- 不需要租户隔离的表继承 `BaseDO`（如菜单、字典等）
- 使用 `@TenantIgnore` 注解标记不隔离的表

## 2. 核心 DO 实体

### 2.1 用户聚合

#### AdminUserDO (system_users)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 用户ID，主键 |
| username | String | username VARCHAR(30) | 用户账号 |
| password | String | password VARCHAR(100) | 加密密码（BCrypt） |
| nickname | String | nickname VARCHAR(30) | 用户昵称 |
| deptId | Long | dept_id BIGINT | 部门ID |
| postIds | String | post_ids VARCHAR(255) | 岗位编号数组（JSON） |
| email | String | email VARCHAR(50) | 用户邮箱 |
| mobile | String | mobile VARCHAR(20) | 手机号码 |
| sex | Integer | sex TINYINT | 用户性别（0男 1女 2未知） |
| avatar | String | avatar VARCHAR(100) | 用户头像URL |
| status | Integer | status TINYINT | 帐号状态（0正常 1停用） |
| loginIp | String | login_ip VARCHAR(50) | 最后登录IP |
| loginDate | LocalDateTime | login_date DATETIME | 最后登录时间 |

**继承**: `TenantBaseDO`

**索引**:
- `uk_username(username, tenant_id)` — 用户名在租户内唯一
- `uk_mobile(mobile, tenant_id)` — 手机号在租户内唯一

#### UserRoleDO (system_user_role)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 主键 |
| userId | Long | user_id BIGINT | 用户ID |
| roleId | Long | role_id BIGINT | 角色ID |

**继承**: `BaseDO`

**索引**: `idx_user_id`, `idx_role_id`

**说明**: 用户与角色的多对多关联表，不继承 TenantBaseDO，通过用户表的租户隔离间接实现。

### 2.2 角色聚合

#### RoleDO (system_role)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 角色ID |
| name | String | name VARCHAR(30) | 角色名称 |
| code | String | code VARCHAR(100) | 角色标识（如 admin） |
| sort | Integer | sort INT | 角色排序 |
| status | Integer | status TINYINT | 角色状态（0正常 1停用） |
| type | Integer | type TINYINT | 角色类型（1系统内置 2自定义） |
| dataScope | Integer | data_scope TINYINT | 数据范围 |
| dataScopeDeptIds | String | data_scope_dept_ids VARCHAR(500) | 数据范围部门ID（JSON） |

**继承**: `TenantBaseDO`

**索引**: `uk_code(code, tenant_id)` — 角色标识在租户内唯一

#### RoleMenuDO (system_role_menu)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 主键 |
| roleId | Long | role_id BIGINT | 角色ID |
| menuId | Long | menu_id BIGINT | 菜单ID |

**继承**: `TenantBaseDO`

**索引**: `idx_role_id`, `idx_menu_id`

### 2.3 菜单聚合

#### MenuDO (system_menu)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 菜单ID |
| name | String | name VARCHAR(50) | 菜单名称 |
| permission | String | permission VARCHAR(100) | 权限标识 |
| type | Integer | type TINYINT | 菜单类型（1目录 2菜单 3按钮） |
| sort | Integer | sort INT | 显示顺序 |
| parentId | Long | parent_id BIGINT | 父菜单ID |
| path | String | path VARCHAR(200) | 路由地址 |
| icon | String | icon VARCHAR(100) | 菜单图标 |
| component | String | component VARCHAR(255) | 组件路径 |
| componentName | String | component_name VARCHAR(100) | 组件名 |
| status | Integer | status TINYINT | 菜单状态（0正常 1停用） |
| visible | Boolean | visible BIT | 是否可见 |
| keepAlive | Boolean | keep_alive BIT | 是否缓存 |
| alwaysShow | Boolean | always_show BIT | 是否总是显示 |

**继承**: `BaseDO`

**注解**: `@TenantIgnore`（菜单全局共享，不区分租户）

### 2.4 部门聚合

#### DeptDO (system_dept)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 部门ID |
| name | String | name VARCHAR(30) | 部门名称 |
| parentId | Long | parent_id BIGINT | 父部门ID |
| sort | Integer | sort INT | 显示顺序 |
| leaderUserId | Long | leader_user_id BIGINT | 负责人用户ID |
| phone | String | phone VARCHAR(20) | 联系电话 |
| email | String | email VARCHAR(50) | 邮箱 |
| status | Integer | status TINYINT | 部门状态（0正常 1停用） |

**继承**: `TenantBaseDO`

### 2.5 岗位 (值对象)

#### PostDO (system_post)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 岗位ID |
| name | String | name VARCHAR(50) | 岗位名称 |
| code | String | code VARCHAR(64) | 岗位编码 |
| sort | Integer | sort INT | 显示顺序 |
| status | Integer | status TINYINT | 状态（0正常 1停用） |

**继承**: `BaseDO`

### 2.6 租户聚合

#### TenantDO (system_tenant)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 租户编号 |
| name | String | name VARCHAR(100) | 租户名 |
| contactUserId | Long | contact_user_id BIGINT | 联系人的用户编号 |
| contactName | String | contact_name VARCHAR(100) | 联系人 |
| contactMobile | String | contact_mobile VARCHAR(20) | 联系手机 |
| status | Integer | status TINYINT | 租户状态（0正常 1停用） |
| websites | String | websites VARCHAR(500) | 绑定域名列表 |
| packageId | Long | package_id BIGINT | 租户套餐编号 |
| expireTime | LocalDateTime | expire_time DATETIME | 过期时间 |
| accountCount | Integer | account_count INT | 账号数量上限 |

**继承**: `BaseDO`

**注解**: `@TenantIgnore`（租户表自身不隔离）

#### TenantPackageDO (system_tenant_package)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 套餐编号 |
| name | String | name VARCHAR(100) | 套餐名 |
| status | Integer | status TINYINT | 套餐状态 |
| menuIds | String | menu_ids VARCHAR(2000) | 关联菜单编号数组（JSON） |
| remark | String | remark VARCHAR(255) | 备注 |

**继承**: `BaseDO`

### 2.7 字典 (值对象)

#### DictTypeDO (system_dict_type)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 字典主键 |
| name | String | name VARCHAR(100) | 字典名称 |
| type | String | type VARCHAR(100) | 字典类型（唯一标识） |
| status | Integer | status TINYINT | 字典状态 |

**继承**: `BaseDO`，**注解**: `@TenantIgnore`

#### DictDataDO (system_dict_data)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 字典主键 |
| sort | Integer | sort INT | 字典排序 |
| label | String | label VARCHAR(100) | 字典标签 |
| value | String | value VARCHAR(100) | 字典值 |
| dictType | String | dict_type VARCHAR(100) | 字典类型 |
| status | Integer | status TINYINT | 状态 |
| colorType | String | color_type VARCHAR(20) | 颜色类型 |

**继承**: `BaseDO`，**注解**: `@TenantIgnore`

### 2.8 短信相关

#### SmsChannelDO (system_sms_channel)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 渠道编号 |
| signature | String | signature VARCHAR(12) | 短信签名 |
| code | String | code VARCHAR(63) | 渠道编码 |
| status | Integer | status TINYINT | 开启状态 |
| apiKey | String | api_key VARCHAR(128) | 短信API密钥 |
| callbackUrl | String | callback_url VARCHAR(255) | 回调URL |

#### SmsTemplateDO (system_sms_template)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 模板编号 |
| name | String | name VARCHAR(63) | 模板名称 |
| code | String | code VARCHAR(63) | 模板编码 |
| content | String | content VARCHAR(255) | 模板内容 |
| channelId | Long | channel_id BIGINT | 短信渠道编号 |
| channelCode | String | channel_code VARCHAR(63) | 短信渠道编码 |
| status | Integer | status TINYINT | 开启状态 |

#### SmsLogDO (system_sms_log)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 日志编号 |
| channelId | Long | channel_id BIGINT | 短信渠道编号 |
| templateId | Long | template_id BIGINT | 模板编号 |
| templateCode | String | template_code VARCHAR(63) | 模板编码 |
| templateContent | String | template_content VARCHAR(255) | 模板内容 |
| templateParams | String | template_params VARCHAR(255) | 模板参数 |
| mobile | String | mobile VARCHAR(11) | 手机号 |
| sendStatus | Integer | send_status TINYINT | 发送状态 |
| sendTime | LocalDateTime | send_time DATETIME | 发送时间 |
| receiveStatus | Integer | receive_status TINYINT | 接收状态 |
| receiveTime | LocalDateTime | receive_time DATETIME | 接收时间 |

### 2.9 邮件相关

#### MailAccountDO (system_mail_account)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 主键 |
| mail | String | mail VARCHAR(100) | 邮箱 |
| username | String | username VARCHAR(100) | 用户名 |
| password | String | password VARCHAR(100) | 密码 |
| host | String | host VARCHAR(100) | SMTP服务器域名 |
| port | Integer | port INT | SMTP服务器端口 |
| sslEnable | Boolean | ssl_enable BIT | 是否开启SSL |

#### MailTemplateDO (system_mail_template)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 主键 |
| name | String | name VARCHAR(63) | 模板名称 |
| code | String | code VARCHAR(63) | 模板编码 |
| accountId | Long | account_id BIGINT | 发送的邮箱账号编号 |
| nickname | String | nickname VARCHAR(255) | 发送人名称 |
| title | String | title VARCHAR(255) | 邮件标题 |
| content | String | content VARCHAR(10240) | 邮件内容（HTML） |
| status | Integer | status TINYINT | 开启状态 |

### 2.10 OAuth2 相关

#### OAuth2ClientDO (system_oauth2_client)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 编号 |
| clientId | String | client_id VARCHAR(255) | 客户端编号 |
| secret | String | secret VARCHAR(255) | 客户端密钥 |
| name | String | name VARCHAR(255) | 应用名 |
| logo | String | logo VARCHAR(255) | 应用图标 |
| authorizedGrantTypes | String | authorized_grant_types VARCHAR(255) | 授权类型（逗号分隔） |
| scopes | String | scopes VARCHAR(255) | 授权范围（逗号分隔） |
| redirectUris | String | redirect_uris VARCHAR(255) | 回调地址（逗号分隔） |
| accessTokenValiditySeconds | Integer | access_token_validity_seconds INT | 访问令牌有效期 |
| refreshTokenValiditySeconds | Integer | refresh_token_validity_seconds INT | 刷新令牌有效期 |

**继承**: `TenantBaseDO`

#### OAuth2AccessTokenDO (system_oauth2_access_token)

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id BIGINT | 编号 |
| accessToken | String | access_token VARCHAR(255) | 访问令牌 |
| userId | Long | user_id BIGINT | 用户编号 |
| userType | Integer | user_type TINYINT | 用户类型 |
| clientId | String | client_id VARCHAR(255) | 客户端编号 |
| expiresTime | LocalDateTime | expires_time DATETIME | 过期时间 |

**继承**: `TenantBaseDO`

## 3. 表关系 (ER)

```
system_users ──N:1──> system_dept          (dept_id)
system_users ──N:N──> system_post          (post_ids JSON)
system_user_role ──N:1──> system_users     (user_id)
system_user_role ──N:1──> system_role      (role_id)
system_role_menu ──N:1──> system_role      (role_id)
system_role_menu ──N:1──> system_menu      (menu_id)
system_menu ──N:1──> system_menu           (parent_id, 树形自关联)
system_dept ──N:1──> system_dept           (parent_id, 树形自关联)
system_tenant ──N:1──> system_tenant_package (package_id)
system_dict_data ──N:1──> system_dict_type (dict_type)
system_sms_template ──N:1──> system_sms_channel (channel_id)
system_mail_template ──N:1──> system_mail_account (account_id)
```

## 4. DTO 对象（跨模块传输）

跨模块 API 使用 DTO 对象传输数据，隔离内部 DO 实体：

| DTO | 来源 | 用途 |
|-----|------|------|
| AdminUserRespDTO | AdminUserApi.getUser() | 用户信息查询 |
| RoleRespDTO | RoleApi.getRole() | 角色信息查询 |
| DeptRespDTO | DeptApi.getDept() | 部门信息查询 |
| PostRespDTO | PostApi.getPost() | 岗位信息查询 |
| DictDataRespDTO | DictDataApi.getDictDataList() | 字典数据查询 |

**规则**: DTO 放在 `api/dto/` 包下，不暴露 DO 实体到外部模块。

## 5. VO 对象（前端交互）

Controller 层使用 VO 对象与前端交互：

| VO 类型 | 命名规范 | 示例 |
|---------|---------|------|
| 请求VO | XxxSaveReqVO / XxxPageReqVO | UserSaveReqVO, RolePageReqVO |
| 响应VO | XxxRespVO / XxxSimpleRespVO | UserRespVO, MenuSimpleRespVO |

**规则**: VO 放在 `controller/admin/xxx/vo/` 包下，使用 `@Data`、`@Valid` 注解。
