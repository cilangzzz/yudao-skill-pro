# 系统管理模块 (system)

> 平台核心基础设施模块，提供用户认证、权限校验、租户隔离等系统级管理能力，是所有业务模块的基础。

## 模块概述

- **模块路径**: yudao-module-system
- **业务定位**: 整个平台的核心基础设施模块，负责用户管理、角色权限、部门组织、租户多租、字典配置、消息通知、OAuth2/社交登录等系统级管理功能，为其他所有业务模块提供统一的用户认证、权限校验、租户隔离能力
- **技术栈**: Spring Boot 2.7.x / MyBatis-Plus 3.5.x / Spring Security / MapStruct / Redis Cache / Knife4j

## 设计原则

| 原则 | 说明 |
|------|------|
| RBAC权限模型 | 用户-角色-菜单三层关联，支持细粒度按钮级权限控制 |
| 多租户架构 | TenantBaseDO基类实现租户数据隔离，所有业务表自动携带tenant_id |
| 数据权限 | 5种范围：全部、自定义部门、本部门、本部门及子部门、仅本人 |
| 分层架构 | 严格遵循Controller-Service-DAL三层架构，API层提供跨模块调用能力 |
| 接口隔离 | Service接口与实现分离，便于测试和扩展 |
| 缓存优先 | 权限数据使用Spring Cache + Redis缓存，减少数据库查询压力 |
| 统一异常处理 | ErrorCodeConstants定义统一错误码，格式为1-002-XXX-XXX |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|--------|------|---------|
| 用户管理 | 后台用户增删改查、密码管理、状态控制 | AdminUserDO, UserRoleDO, UserPostDO |
| 角色管理 | RBAC角色定义与权限分配 | RoleDO, RoleMenuDO |
| 菜单权限 | 目录/菜单/按钮三种类型，权限标识控制 | MenuDO |
| 部门管理 | 组织架构树形结构管理 | DeptDO |
| 岗位管理 | 岗位信息维护 | PostDO |
| 租户管理 | 多租户创建、套餐绑定、过期控制 | TenantDO, TenantPackageDO |
| 字典管理 | 字典类型与字典数据维护 | DictTypeDO, DictDataDO |
| 短信服务 | 短信渠道/模板/发送/验证码 | SmsChannelDO, SmsTemplateDO, SmsLogDO |
| 邮件服务 | 邮箱账号/模板/发送 | MailAccountDO, MailTemplateDO |
| 站内信服务 | 站内信模板/消息发送 | NotifyTemplateDO, NotifyMessageDO |
| OAuth2 | OAuth2客户端/令牌/授权码管理 | OAuth2ClientDO, OAuth2AccessTokenDO |
| 社交登录 | 第三方登录集成（微信、钉钉等） | SocialUserDO, SocialClientDO |
| 日志 | 登录日志、操作日志记录 | LoginLogDO, OperateLogDO |

## API 接口索引

### 认证接口 (AuthController，/system/auth)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/auth/login | POST | 账号密码登录 | @PermitAll |
| /system/auth/logout | POST | 用户登出 | @PermitAll |
| /system/auth/refresh-token | POST | 刷新令牌 | @PermitAll |
| /system/auth/get-permission-info | GET | 获取当前用户权限信息 | 已认证 |
| /system/auth/register | POST | 注册用户 | @PermitAll |
| /system/auth/sms-login | POST | 短信验证码登录 | @PermitAll |
| /system/auth/send-sms-code | POST | 发送手机验证码 | @PermitAll |
| /system/auth/reset-password | POST | 重置密码 | @PermitAll |
| /system/auth/social-auth-redirect | GET | 获取社交授权跳转地址 | @PermitAll |
| /system/auth/social-login | POST | 社交快捷登录 | @PermitAll |
| /system/auth/create-qrcode | POST | 生成扫码登录二维码 | @PermitAll |
| /system/auth/confirm-qrcode | POST | 手机确认扫码登录 | 已认证 |
| /system/auth/qrcode-login | POST | 电脑轮询领取登录结果 | @PermitAll |

### 验证码接口 (CaptchaController，/system/captcha)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/captcha/get | POST | 获取 AJ-Captcha 行为验证码 | @PermitAll |
| /system/captcha/check | POST | 校验行为验证码 | @PermitAll |

### 用户管理 (UserController / UserProfileController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/user/create | POST | 创建用户 | system:user:create |
| /system/user/update | PUT | 更新用户 | system:user:update |
| /system/user/delete | DELETE | 删除用户 | system:user:delete |
| /system/user/delete-list | DELETE | 批量删除用户 | system:user:delete |
| /system/user/update-password | PUT | 重置用户密码 | system:user:update-password |
| /system/user/update-status | PUT | 更新用户状态 | system:user:update |
| /system/user/page | GET | 获取用户分页 | system:user:query |
| /system/user/list | GET | 获取用户列表 | system:user:query |
| /system/user/list-all-simple（别名 /simple-list） | GET | 获取用户精简列表 | 已认证 |
| /system/user/get | GET | 获取用户详情 | system:user:query |
| /system/user/get-simple | GET | 获取用户精简信息 | 已认证 |
| /system/user/list-by-nickname | GET | 按昵称模糊查询用户 | 已认证 |
| /system/user/export-excel | GET | 导出用户 Excel | system:user:export |
| /system/user/get-import-template | GET | 获取用户导入模板 | 已认证 |
| /system/user/import | POST | 导入用户 | system:user:import |
| /system/user/profile/get | GET | 获取个人信息 | 已认证 |
| /system/user/profile/update | PUT | 修改个人信息 | 已认证 |
| /system/user/profile/update-password | PUT | 修改个人密码 | 已认证 |

### 角色与权限 (RoleController / PermissionController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/role/create | POST | 创建角色 | system:role:create |
| /system/role/update | PUT | 更新角色 | system:role:update |
| /system/role/delete | DELETE | 删除角色 | system:role:delete |
| /system/role/delete-list | DELETE | 批量删除角色 | system:role:delete |
| /system/role/get | GET | 获取角色详情 | system:role:query |
| /system/role/page | GET | 获取角色分页 | system:role:query |
| /system/role/list-all-simple（别名 /simple-list） | GET | 获取角色精简列表 | 已认证 |
| /system/role/export-excel | GET | 导出角色 Excel | system:role:export |
| /system/permission/list-role-menus | GET | 获取角色已分配的菜单编号 | system:permission:assign-role-menu |
| /system/permission/assign-role-menu | POST | 分配角色菜单 | system:permission:assign-role-menu |
| /system/permission/assign-role-data-scope | POST | 分配角色数据权限 | system:permission:assign-role-data-scope |
| /system/permission/list-user-roles | GET | 获取用户已分配的角色编号 | system:permission:assign-user-role |
| /system/permission/assign-user-role | POST | 分配用户角色 | system:permission:assign-user-role |

### 菜单管理 (MenuController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/menu/create | POST | 创建菜单 | system:menu:create |
| /system/menu/update | PUT | 更新菜单 | system:menu:update |
| /system/menu/delete | DELETE | 删除菜单 | system:menu:delete |
| /system/menu/delete-list | DELETE | 批量删除菜单 | system:menu:delete |
| /system/menu/get | GET | 获取菜单详情 | system:menu:query |
| /system/menu/list | GET | 获取菜单列表（按租户套餐过滤，超管不受限） | system:menu:query |
| /system/menu/list-all-simple（别名 /system/menu/simple-list） | GET | 获取菜单精简列表（超管不受租户套餐限制） | 已认证 |

### 部门与岗位 (DeptController / PostController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/dept/create | POST | 创建部门 | system:dept:create |
| /system/dept/update | PUT | 更新部门 | system:dept:update |
| /system/dept/delete | DELETE | 删除部门 | system:dept:delete |
| /system/dept/delete-list | DELETE | 批量删除部门（含数据权限校验） | system:dept:delete |
| /system/dept/get | GET | 获取部门详情 | system:dept:query |
| /system/dept/list | GET | 获取部门列表 | system:dept:query |
| /system/dept/list-all-simple（别名 /simple-list） | GET | 获取部门精简列表 | 已认证 |
| /system/post/create | POST | 创建岗位 | system:post:create |
| /system/post/update | PUT | 更新岗位 | system:post:update |
| /system/post/delete | DELETE | 删除岗位 | system:post:delete |
| /system/post/delete-list | DELETE | 批量删除岗位 | system:post:delete |
| /system/post/get | GET | 获取岗位详情 | system:post:query |
| /system/post/page | GET | 获取岗位分页 | system:post:query |
| /system/post/list-all-simple（别名 /simple-list） | GET | 获取岗位精简列表 | 已认证 |
| /system/post/export-excel | GET | 导出岗位 Excel | system:post:export |

### 租户管理 (TenantController / TenantPackageController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/tenant/create | POST | 创建租户 | system:tenant:create |
| /system/tenant/update | PUT | 更新租户 | system:tenant:update |
| /system/tenant/delete | DELETE | 删除租户 | system:tenant:delete |
| /system/tenant/delete-list | DELETE | 批量删除租户 | system:tenant:delete |
| /system/tenant/get | GET | 获取租户详情 | system:tenant:query |
| /system/tenant/page | GET | 获取租户分页 | system:tenant:query |
| /system/tenant/simple-list | GET | 获取租户精简列表 | 已认证 |
| /system/tenant/get-id-by-name | GET | 根据名称获取租户编号 | 已认证 |
| /system/tenant/get-by-website | GET | 根据域名获取租户 | 已认证 |
| /system/tenant/export-excel | GET | 导出租户 Excel | system:tenant:export |
| /system/tenant-package/create | POST | 创建租户套餐 | system:tenant-package:create |
| /system/tenant-package/update | PUT | 更新租户套餐 | system:tenant-package:update |
| /system/tenant-package/delete | DELETE | 删除租户套餐 | system:tenant-package:delete |
| /system/tenant-package/delete-list | DELETE | 批量删除租户套餐 | system:tenant-package:delete |
| /system/tenant-package/get | GET | 获取套餐详情 | system:tenant-package:query |
| /system/tenant-package/page | GET | 获取套餐分页 | system:tenant-package:query |
| /system/tenant-package/get-simple-list（别名 /simple-list） | GET | 获取套餐精简列表 | 已认证 |

### 字典管理 (DictTypeController / DictDataController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/dict-type/create | POST | 创建字典类型 | system:dict:create |
| /system/dict-type/update | PUT | 更新字典类型 | system:dict:update |
| /system/dict-type/delete | DELETE | 删除字典类型 | system:dict:delete |
| /system/dict-type/delete-list | DELETE | 批量删除字典类型 | system:dict:delete |
| /system/dict-type/get | GET | 获取字典类型详情 | system:dict:query |
| /system/dict-type/page | GET | 获取字典类型分页 | system:dict:query |
| /system/dict-type/list-all-simple（别名 /simple-list） | GET | 获取字典类型精简列表 | 已认证 |
| /system/dict-type/export-excel | GET | 导出字典类型 Excel | system:dict:query |
| /system/dict-data/create | POST | 创建字典数据 | system:dict:create |
| /system/dict-data/update | PUT | 更新字典数据 | system:dict:update |
| /system/dict-data/delete | DELETE | 删除字典数据 | system:dict:delete |
| /system/dict-data/delete-list | DELETE | 批量删除字典数据 | system:dict:delete |
| /system/dict-data/get | GET | 获取字典数据详情 | system:dict:query |
| /system/dict-data/page | GET | 获取字典数据分页 | system:dict:query |
| /system/dict-data/list-all-simple（别名 /simple-list） | GET | 获取字典数据精简列表 | 已认证 |
| /system/dict-data/export-excel | GET | 导出字典数据 Excel | system:dict:export |

### 短信服务 (SmsChannelController / SmsTemplateController / SmsLogController / SmsCallbackController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/sms-channel/create、/update、/delete、/delete-list | POST/PUT/DELETE | 短信渠道增删改、批量删除 | system:sms-channel:create/update/delete |
| /system/sms-channel/get、/page | GET | 短信渠道详情、分页 | system:sms-channel:query |
| /system/sms-channel/list-all-simple（别名 /simple-list） | GET | 短信渠道精简列表 | 已认证 |
| /system/sms-template/create、/update、/delete、/delete-list | POST/PUT/DELETE | 短信模板增删改、批量删除 | system:sms-template:create/update/delete |
| /system/sms-template/get、/page | GET | 短信模板详情、分页 | system:sms-template:query |
| /system/sms-template/list-all-simple（别名 /simple-list） | GET | 短信模板精简列表 | 已认证 |
| /system/sms-template/export-excel | GET | 导出短信模板 Excel | system:sms-template:export |
| /system/sms-template/send-sms | POST | 发送短信 | system:sms-template:send-sms |
| /system/sms-log/page、/get | GET | 短信日志分页、详情 | system:sms-log:query |
| /system/sms-log/export-excel | GET | 导出短信日志 Excel | system:sms-log:export |
| /system/sms/callback/aliyun、/tencent、/huawei、/qiniu | POST | 各短信渠道回调 | @PermitAll |

### 邮件服务 (MailAccountController / MailTemplateController / MailLogController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/mail-account/create、/update、/delete、/delete-list | POST/PUT/DELETE | 邮箱账号增删改、批量删除 | system:mail-account:create/update/delete |
| /system/mail-account/get、/page | GET | 邮箱账号详情、分页 | system:mail-account:query |
| /system/mail-account/list-all-simple（别名 /simple-list） | GET | 邮箱账号精简列表 | 已认证 |
| /system/mail-template/create、/update、/delete、/delete-list | POST/PUT/DELETE | 邮件模板增删改、批量删除 | system:mail-template:create/update/delete |
| /system/mail-template/get、/page | GET | 邮件模板详情、分页 | system:mail-template:query |
| /system/mail-template/list-all-simple（别名 /simple-list） | GET | 邮件模板精简列表 | 已认证 |
| /system/mail-template/send-mail | POST | 发送邮件 | system:mail-template:send-mail |
| /system/mail-log/page、/get | GET | 邮件日志分页、详情 | system:mail-log:query |

### 站内信与通知公告 (NotifyTemplateController / NotifyMessageController / NoticeController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/notify-template/create、/update、/delete、/delete-list | POST/PUT/DELETE | 站内信模板增删改、批量删除 | system:notify-template:create/update/delete |
| /system/notify-template/get、/page | GET | 站内信模板详情、分页 | system:notify-template:query |
| /system/notify-template/list-all-simple（别名 /simple-list） | GET | 站内信模板精简列表 | 已认证 |
| /system/notify-template/send-notify | POST | 发送站内信 | system:notify-template:send-notify |
| /system/notify-message/get、/page | GET | 站内信详情、分页 | system:notify-message:query |
| /system/notify-message/my-page | GET | 我的站内信分页 | 已认证 |
| /system/notify-message/update-read | PUT | 标记指定站内信已读 | 已认证 |
| /system/notify-message/update-all-read | PUT | 标记全部站内信已读 | 已认证 |
| /system/notify-message/get-unread-list | GET | 获取未读站内信列表 | 已认证 |
| /system/notify-message/get-unread-count | GET | 获取未读站内信数量 | 已认证 |
| /system/notice/create、/update、/delete、/delete-list | POST/PUT/DELETE | 通知公告增删改、批量删除 | system:notice:create/update/delete |
| /system/notice/get、/page | GET | 通知公告详情、分页 | system:notice:query |
| /system/notice/push | POST | 通过 WebSocket 推送公告 | system:notice:update |

### OAuth2 (OAuth2OpenController / OAuth2ClientController / OAuth2TokenController / OAuth2UserController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/oauth2/token | POST / DELETE | 获取 / 吊销访问令牌（Basic 认证客户端） | @PermitAll |
| /system/oauth2/check-token | POST | 校验访问令牌 | @PermitAll |
| /system/oauth2/authorize | GET / POST | 获取授权信息 / 申请授权 | 已认证 |
| /system/oauth2-client/create、/update、/delete、/delete-list | POST/PUT/DELETE | OAuth2 客户端增删改、批量删除 | system:oauth2-client:create/update/delete |
| /system/oauth2-client/get、/page | GET | OAuth2 客户端详情、分页 | system:oauth2-client:query |
| /system/oauth2-token/page | GET | 访问令牌分页 | system:oauth2-token:page |
| /system/oauth2-token/delete、/delete-list | DELETE | 删除 / 批量删除访问令牌（强制下线） | system:oauth2-token:delete |
| /system/oauth2/user/get | GET | 获取 OAuth2 用户信息 | @ss.hasScope('user.read') |
| /system/oauth2/user/update | PUT | 更新 OAuth2 用户信息 | @ss.hasScope('user.write') |

### 社交登录 (SocialClientController / SocialUserController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/social-client/create、/update、/delete、/delete-list | POST/PUT/DELETE | 社交客户端增删改、批量删除 | system:social-client:create/update/delete |
| /system/social-client/get、/page | GET | 社交客户端详情、分页 | system:social-client:query |
| /system/social-client/send-subscribe-message | POST | 发送订阅消息 | system:social-client:query |
| /system/social-user/bind | POST | 绑定社交用户 | 已认证 |
| /system/social-user/unbind | DELETE | 解绑社交用户 | 已认证 |
| /system/social-user/get-bind-list | GET | 获取当前用户绑定列表 | 已认证 |
| /system/social-user/get、/page | GET | 社交用户详情、分页 | system:social-user:query |

### 日志与 IP (LoginLogController / OperateLogController / AreaController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/login-log/get、/page | GET | 登录日志详情、分页 | system:login-log:query |
| /system/login-log/export-excel | GET | 导出登录日志 Excel | system:login-log:export |
| /system/operate-log/get、/page | GET | 操作日志详情、分页 | system:operate-log:query |
| /system/operate-log/export-excel | GET | 导出操作日志 Excel | system:operate-log:export |
| /system/area/tree | GET | 获取地区树 | @PermitAll |
| /system/area/get-by-ip | GET | 根据 IP 获取地区 | @PermitAll |

### 用户 App 端接口（controller.app 包，前缀 /app-api）

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /app-api/system/dict-data/type | GET | 按字典类型获取启用的字典数据 | @PermitAll |
| /app-api/system/area/tree | GET | 获取地区树 | @PermitAll |
| /app-api/system/tenant/get-by-website | GET | 根据域名获取租户 | @PermitAll |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| system_users | 用户表 | TenantBaseDO | username, password, nickname, dept_id, status |
| system_user_role | 用户-角色关联表 | BaseDO | user_id, role_id |
| system_role | 角色表 | TenantBaseDO | name, code, data_scope, status |
| system_role_menu | 角色-菜单关联表 | TenantBaseDO | role_id, menu_id |
| system_menu | 菜单表 | BaseDO (@TenantIgnore) | name, permission, type, parent_id, path |
| system_dept | 部门表 | TenantBaseDO | name, parent_id, leader_user_id, status |
| system_post | 岗位表 | BaseDO | name, code, sort, status |
| system_tenant | 租户表 | BaseDO (@TenantIgnore) | name, package_id, expire_time, account_count |
| system_tenant_package | 租户套餐表 | BaseDO | name, menu_ids, status |
| system_dict_type | 字典类型表 | BaseDO (@TenantIgnore) | name, type, status |
| system_dict_data | 字典数据表 | BaseDO (@TenantIgnore) | label, value, dict_type |
| system_sms_channel | 短信渠道表 | BaseDO | signature, code, api_key |
| system_sms_template | 短信模板表 | BaseDO | name, code, content, channel_id |
| system_sms_log | 短信日志表 | BaseDO | mobile, template_code, send_status |
| system_mail_account | 邮箱账号表 | BaseDO | mail, host, port |
| system_mail_template | 邮件模板表 | BaseDO | name, code, title, content |
| system_oauth2_client | OAuth2客户端表 | BaseDO (@TenantIgnore) | client_id, secret, authorized_grant_types, redirect_uris |
| system_oauth2_access_token | OAuth2访问令牌表 | TenantBaseDO | access_token, refresh_token, user_id, client_id, expires_time |
| system_oauth2_refresh_token | OAuth2刷新令牌表 | TenantBaseDO | refresh_token, user_id, client_id, expires_time |
| system_sms_code | 手机验证码表 | BaseDO (@TenantIgnore) | mobile, code, scene, used（IntegerBooleanTypeHandler，0/1） |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|---------|------|
| 策略模式 | SmsChannelService, MailSendService | 不同短信/邮件渠道的发送策略切换 |
| 模板方法模式 | NotifySendService, SmsSendService | 消息发送的统一流程，子类实现具体发送逻辑 |
| 工厂模式 | SmsClientFactory, MailClientFactory | 根据渠道类型创建对应的客户端实例 |
| 代理模式 | PermissionServiceImpl.getSelf() | 解决Spring AOP缓存注解生效问题 |
| DTO模式 | api/dto/* | 跨模块数据传输对象，隔离内部实体 |
| 转换器模式 | convert/* | DO与VO之间的对象转换，使用MapStruct |

## 依赖关系

- **上游**（本模块依赖）:
  - yudao-framework-common: 通用响应、分页、错误码
  - yudao-framework-security: 安全框架、权限注解
  - yudao-framework-tenant: 多租户支持
  - yudao-framework-mybatis: MyBatis增强
  - yudao-framework-redis: Redis缓存
  - yudao-module-infra (FileApi、WebSocketSenderApi): 文件上传、WebSocket 推送
- **下游**（依赖本模块）:
  - yudao-module-member: 调用 LoginLogApi、SmsCodeApi、SocialClientApi、SocialUserApi
  - yudao-module-pay: 调用 SocialClientApi
  - yudao-module-bpm: 调用 PermissionApi、SmsSendApi、AdminUserApi、DeptApi、PostApi、RoleApi
  - yudao-module-oa、pms、report: 调用 PermissionApi
  - yudao-module-mes、oa: 调用 DictDataApi
  - yudao-module-hrm、oa、pms: 调用 NotifyMessageSendApi
  - yudao-module-crm、hrm: 调用 OperateLogApi
  - yudao-module-ai、ai1、crm、erp、fms、hrm、im、mes、oa、pms、wms: 调用 AdminUserApi、DeptApi 等基础查询 API

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|---------|------|--------|
| PermissionApi | getUserRoleIdListByRoleIds；继承 PermissionCommonApi 的 hasAnyPermissions、hasAnyRoles、getDeptDataPermission | bpm、oa、pms、report |
| AdminUserApi | getUser、getUserByMobile、getUserList、getUserListByDeptIds、getUserListByPostIds、getUserListByNickname、getUserListByStatus、getUserListBySubordinate、validateUser、validateUserList | ai、ai1、bpm、crm、erp、fms、hrm、im、mes、oa、pms、wms |
| DeptApi | getDept、getDeptList、validateDeptList、getChildDeptList、getParentDeptList | bpm、crm、fms、hrm、oa、pms |
| PostApi | getPostList、validPostList | bpm、crm、mes |
| RoleApi | getRole、getRoleList、validRoleList | bpm、mes |
| DictDataApi | validateDictDataList；继承 DictDataCommonApi 的 getDictDataList | mes、oa |
| SmsSendApi | sendSingleSmsToAdmin、sendSingleSmsToMember | bpm |
| MailSendApi | sendSingleMailToAdmin、sendSingleMailToMember | 暂无外部模块调用（预留扩展） |
| SmsCodeApi | sendSmsCode、useSmsCode、validateSmsCode | member |
| SocialClientApi | getAuthorizeUrl、createWxMpJsapiSignature、getWxMaPhoneNumberInfo、getWxaQrcode、getWxaSubscribeTemplateList、sendWxaSubscribeMessage、uploadWxaOrderShippingInfo、notifyWxaOrderConfirmReceive | member、pay |
| SocialUserApi | bindSocialUser、unbindSocialUser、getSocialUserByUserId、getSocialUserByCode | member |
| NotifyMessageSendApi | sendSingleMessageToAdmin、sendSingleMessageToMember | hrm、oa、pms |
| LoginLogApi | createLoginLog | member |
| OperateLogApi | getOperateLogPage | crm、hrm |

## 详细文档

- [api-auth.md](api-auth.md) - 认证与验证码接口详情（登录/登出/刷新令牌/注册/短信登录/社交登录/验证码）
- [api-user.md](api-user.md) - 用户管理接口详情
- [api-permission.md](api-permission.md) - 权限管理接口详情（角色/菜单/权限分配）
- [api-dept.md](api-dept.md) - 部门管理接口详情
- [api-dict.md](api-dict.md) - 字典管理接口详情
- [api-tenant.md](api-tenant.md) - 租户管理接口详情
- [api-oauth2.md](api-oauth2.md) - OAuth2 开放授权、客户端与访问令牌管理接口详情
- [api-social.md](api-social.md) - 社交登录接口详情
- [api-sms.md](api-sms.md) - 短信服务接口详情
- [api-mail.md](api-mail.md) - 邮件服务接口详情
- [api-notify.md](api-notify.md) - 站内信接口详情
- [api-notice.md](api-notice.md) - 通知公告接口详情
- [api-ip.md](api-ip.md) - IP 归属地查询接口详情
- [api-logger.md](api-logger.md) - 日志审计接口详情
- [data-model.md](data-model.md) - 数据模型详情（DO/DTO/VO及关系）
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
