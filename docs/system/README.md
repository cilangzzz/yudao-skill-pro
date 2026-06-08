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

### 认证接口 (AuthController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/auth/login | POST | 用户登录 | @PermitAll |
| /system/auth/logout | POST | 用户登出 | 已认证 |
| /system/auth/refresh-token | POST | 刷新令牌 | 已认证 |
| /system/auth/get-permission-info | GET | 获取当前用户权限信息 | 已认证 |

### 用户管理 (UserController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/user/create | POST | 创建用户 | system:user:create |
| /system/user/update | PUT | 更新用户 | system:user:update |
| /system/user/delete | DELETE | 删除用户 | system:user:delete |
| /system/user/get | GET | 获取用户详情 | system:user:query |
| /system/user/get-page | POST | 获取用户分页列表 | system:user:query |
| /system/user/export | POST | 导出用户 | system:user:export |
| /system/user/update-password | PUT | 重置密码 | system:user:update-password |
| /system/user/update-profile | PUT | 修改个人信息 | 已认证 |
| /system/user/update-avatar | PUT | 修改头像 | 已认证 |

### 角色管理 (RoleController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/role/create | POST | 创建角色 | system:role:create |
| /system/role/update | PUT | 更新角色 | system:role:update |
| /system/role/delete | DELETE | 删除角色 | system:role:delete |
| /system/role/get | GET | 获取角色详情 | system:role:query |
| /system/role/get-all | GET | 获取所有角色列表 | system:role:query |
| /system/role/get-page | POST | 获取角色分页列表 | system:role:query |
| /system/role/assign-menu | PUT | 分配角色菜单 | system:role:assign-menu |
| /system/role/assign-data-scope | PUT | 分配数据权限 | system:role:assign-data-scope |

### 菜单管理 (MenuController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/menu/create | POST | 创建菜单 | system:menu:create |
| /system/menu/update | PUT | 更新菜单 | system:menu:update |
| /system/menu/delete | DELETE | 删除菜单 | system:menu:delete |
| /system/menu/get | GET | 获取菜单详情 | system:menu:query |
| /system/menu/get-list | GET | 获取菜单列表 | system:menu:query |
| /system/menu/get-simple-list | GET | 获取菜单精简列表 | 已认证 |

### 部门管理 (DeptController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/dept/create | POST | 创建部门 | system:dept:create |
| /system/dept/update | PUT | 更新部门 | system:dept:update |
| /system/dept/delete | DELETE | 删除部门 | system:dept:delete |
| /system/dept/get | GET | 获取部门详情 | system:dept:query |
| /system/dept/get-list | GET | 获取部门列表 | system:dept:query |
| /system/dept/get-simple-list | GET | 获取部门精简列表 | 已认证 |

### 租户管理 (TenantController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /system/tenant/create | POST | 创建租户 | system:tenant:create |
| /system/tenant/update | PUT | 更新租户 | system:tenant:update |
| /system/tenant/delete | DELETE | 删除租户 | system:tenant:delete |
| /system/tenant/get | GET | 获取租户详情 | system:tenant:query |
| /system/tenant/get-page | POST | 获取租户分页列表 | system:tenant:query |
| /system/tenant/get-list | GET | 获取租户列表 | 已认证 |
| /system/tenant-package/create | POST | 创建租户套餐 | system:tenant-package:create |
| /system/tenant-package/update | PUT | 更新租户套餐 | system:tenant-package:update |
| /system/tenant-package/delete | DELETE | 删除租户套餐 | system:tenant-package:delete |
| /system/tenant-package/get | GET | 获取套餐详情 | system:tenant-package:query |
| /system/tenant-package/get-all | GET | 获取所有套餐列表 | system:tenant-package:query |

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
| system_oauth2_client | OAuth2客户端表 | TenantBaseDO | client_id, secret, authorized_grant_types |
| system_oauth2_access_token | OAuth2访问令牌表 | TenantBaseDO | access_token, user_id, client_id, expires_time |

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
  - yudao-module-infra (FileApi): 文件上传
- **下游**（依赖本模块）:
  - yudao-module-infra: 调用PermissionApi、AdminUserApi、DeptApi
  - yudao-module-member: 调用PermissionApi、SmsSendApi、MailSendApi
  - yudao-module-pay: 调用AdminUserApi
  - 所有模块: 调用DictDataApi

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|---------|------|--------|
| PermissionApi | hasAnyPermissions, hasAnyRoles, getUserRoleIdListByRoleIds | yudao-module-infra, yudao-module-member |
| AdminUserApi | getUser, getUserList | yudao-module-infra, yudao-module-pay |
| DeptApi | getDept, getDeptList | yudao-module-infra |
| DictDataApi | parseDictData, getDictDataList | 所有模块 |
| SmsSendApi | sendSingleSms | yudao-module-member |
| MailSendApi | sendSingleMail | yudao-module-member |

## 详细文档

- [api-user.md](api-user.md) - 用户管理接口详情
- [api-role.md](api-role.md) - 角色管理接口详情
- [api-menu.md](api-menu.md) - 菜单权限接口详情
- [api-dept.md](api-dept.md) - 部门管理接口详情
- [api-tenant.md](api-tenant.md) - 租户管理接口详情
- [data-model.md](data-model.md) - 数据模型详情（DO/DTO/VO及关系）
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
