# 系统管理代码模式与扩展指南 (system)

> 本文档移植自模块 Skill 知识库（skill-system.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

**常用注解**：

- `@Tag(name = '管理后台 - XXX')`：OpenAPI 3.0 文档标签
- `@RestController`：RESTful 控制器
- `@RequestMapping('/system/xxx')`：路由前缀
- `@Validated`：参数校验
- `@Operation(summary = 'XXX')`：接口文档说明
- `@PreAuthorize('@ss.hasPermission('system:xxx:add')')`：权限校验
- `@PermitAll`：允许匿名访问（如登录接口）

**示例**：

```java
@Tag(name = "管理后台 - 用户")
@RestController
@RequestMapping("/system/user")
@Validated
public class UserController {
    @PostMapping("/create")
    @Operation(summary = "创建用户")
    @PreAuthorize("@ss.hasPermission('system:user:create')")
    public CommonResult<Long> createUser(@Valid @RequestBody UserSaveReqVO createReqVO) {
        return success(userService.createUser(createReqVO));
    }
}
```

### Service 层规范

**接口定义**：

- 接口定义在 service 包下
- 方法参数使用 `@Valid` 注解进行校验
- 返回值使用具体类型或 void

**实现类**：

- 实现类放在 service 包下，命名为 `XxxServiceImpl`
- 使用 `@Service` 注解
- 使用 `@Resource` 注入 Mapper 和其他 Service
- 使用 `@Transactional(rollbackFor = Exception.class)` 标记事务方法
- 使用 `@Cacheable`/`@CacheEvict` 进行缓存操作

**示例**：

```java
@Service
@Slf4j
public class PermissionServiceImpl implements PermissionService {

    @Resource
    private RoleMenuMapper roleMenuMapper;
    @Resource
    private UserRoleMapper userRoleMapper;

    @Override
    @DSTransactional // 多数据源事务
    @Caching(evict = {
        @CacheEvict(value = RedisKeyConstants.MENU_ROLE_ID_LIST, allEntries = true),
        @CacheEvict(value = RedisKeyConstants.PERMISSION_MENU_ID_LIST, allEntries = true)
    })
    public void assignRoleMenu(Long roleId, Set<Long> menuIds) {
        // 业务逻辑
    }
}
```

### 数据访问层（DAL）规范

- Mapper 接口继承 `BaseMapperX<DO类>`
- 使用 `@Mapper` 注解
- 复杂查询使用 MPJLambdaWrapperWrapper 或 XML

**示例**：

```java
@Mapper
public interface UserMapper extends BaseMapperX<AdminUserDO> {

    default AdminUserDO selectByUsername(String username) {
        return selectOne(AdminUserDO::getUsername, username);
    }

    default List<AdminUserDO> selectListByDeptIds(Collection<Long> deptIds) {
        return selectList(new LambdaQueryWrapperX<AdminUserDO>()
            .inIfPresent(AdminUserDO::getDeptId, deptIds));
    }
}
```

### 异常处理

- 错误码前缀：`1-002-XXX-XXX`，格式为「模块号-子模块号-序号」

**典型错误码**：

| 错误码 | 错误消息 | 子模块 |
|-------|---------|-------|
| 1_002_000_000 | 登录失败，账号密码不正确 | AUTH |
| 1_002_001_000 | 已经存在该名字的菜单 | MENU |
| 1_002_002_000 | 角色不存在 | ROLE |
| 1_002_003_000 | 用户账号已经存在 | USER |
| 1_002_004_000 | 已经存在该名字的部门 | DEPT |
| 1_002_015_000 | 租户不存在 | TENANT |

**使用示例**：

```java
// 在Service中抛出业务异常
if (user == null) {
    throw exception(USER_NOT_EXISTS);
}
// 带参数的异常
throw exception(ROLE_NAME_DUPLICATE, name);
```

### 统一响应

- 成功响应：`CommonResult.success(data)`
- 失败响应：`CommonResult.error(errorCode)`

```java
// 成功响应
return success(userService.getUser(id));
// 失败响应（通常由全局异常处理器处理）
throw exception(USER_NOT_EXISTS);
```

## 扩展指南

### 新增业务功能（以新增“操作日志”功能为例）

| 步骤 | 说明 |
|------|------|
| 1. 创建 DO 实体类 | 在 `dal/dataobject/logger/` 下创建 OperateLogDO.java，继承 BaseDO 或 TenantBaseDO，使用 `@TableName` 指定表名 |
| 2. 创建 Mapper 接口 | 在 `dal/mysql/logger/` 下创建 OperateLogMapper.java，继承 `BaseMapperX<OperateLogDO>` |
| 3. 创建 Service 接口和实现 | 在 `service/logger/` 下创建 OperateLogService.java 接口与 OperateLogServiceImpl.java 实现，使用 `@Service` 和 `@Resource` 注解 |
| 4. 创建 Controller | 在 `controller/admin/logger/` 下创建 OperateLogController.java，使用 `@RestController`、`@RequestMapping`、`@Tag` 等注解，使用 `@PreAuthorize` 进行权限控制 |
| 5. 创建 VO 类 | 在 `controller/admin/logger/vo/` 下创建请求和响应 VO，使用 `@Data`、`@Valid` 等注解进行参数校验 |
| 6. 添加错误码 | 在 `enums/ErrorCodeConstants.java` 中添加错误码，格式：`ErrorCode XXX_NOT_EXISTS = new ErrorCode(1_002_XXX_000, "XXX不存在");` |
| 7. 添加菜单权限 | 在数据库 `system_menu` 表中添加菜单记录，配置权限标识如 `system:operate-log:query` |

### 新增短信渠道（以新增“华为云短信”为例）

| 步骤 | 说明 |
|------|------|
| 1. 添加渠道枚举 | 在 `SmsChannelEnum` 中添加新渠道类型：`HUAWEI("huawei", "华为云")` |
| 2. 创建客户端实现 | 在 `framework/sms/core/client/impl/` 下创建 HuaweiSmsClient.java，继承 `AbstractSmsClient` 抽象类，实现 `doSendSms()` 方法 |
| 3. 注册到工厂 | 在 `SmsClientFactory` 中注册新渠道：`clients.put(SmsChannelEnum.HUAWEI, new HuaweiSmsClient());` |
| 4. 添加配置类 | 创建 `HuaweiSmsChannelProperties` 配置类，继承 `SmsChannelProperties` 基类 |

### 新增字典类型

| 步骤 | 说明 |
|------|------|
| 1. 通过管理后台添加 | 登录管理后台 → 系统管理 → 字典管理 → 新增字典类型，填写字典名称、字典类型（如 `system_user_sex`） |
| 2. 添加字典数据 | 在字典类型下添加字典数据项，设置字典标签、字典值、排序、状态等 |
| 3. 代码中使用 | 通过 `DictDataApi` 获取与解析字典数据（见下方示例） |

```java
// 获取字典数据列表
List<DictDataRespDTO> dictList = dictDataApi.getDictDataList("system_user_sex");
// 解析字典值
String label = dictDataApi.parseDictData("system_user_sex", "1");
```

### 最佳实践

| 实践 | 说明 |
|------|------|
| 权限标识命名规范 | 使用 `模块:功能:操作` 格式，如 `system:user:create`、`system:role:update` |
| 数据权限使用 | 在 Service 方法上使用 `@DataPermission` 注解控制数据权限，使用 `enable=false` 关闭 |
| 缓存使用 | 权限相关数据使用 `@Cacheable` 缓存，修改时使用 `@CacheEvict` 清除 |
| 多租户注意 | 不需要租户隔离的表使用 `@TenantIgnore` 注解，如字典表、菜单表 |
| 事务处理 | 跨数据源操作使用 `@DSTransactional`，单数据源使用 `@Transactional` |
| 日志记录 | 使用 `@OperateLog` 注解记录操作日志，使用 Lombok 的 `@Slf4j` 记录调试日志 |
| 参数校验 | VO 类使用 `@Valid`、`@NotNull`、`@NotBlank` 等注解进行参数校验 |
| API 设计 | 跨模块调用通过 API 层，不要直接调用 Service 层 |

## 模块依赖

### 内部依赖（框架与其他模块）

| 依赖模块 | 主要 API | 用途 |
|---------|---------|------|
| yudao-framework-common | CommonResult, PageResult, ErrorCode | 通用响应、分页、错误码 |
| yudao-framework-security | SecurityFrameworkUtils, @PreAuthorize | 安全框架、权限注解 |
| yudao-framework-tenant | TenantBaseDO, @TenantIgnore | 多租户支持 |
| yudao-framework-mybatis | BaseMapperX, BaseDO | MyBatis 增强 |
| yudao-framework-redis | @Cacheable, RedisKeyConstants | Redis 缓存 |
| yudao-module-infra | FileApi | 文件上传 |

### 外部依赖（第三方库）

| 依赖 | 版本 | 用途 |
|-----|------|------|
| spring-boot-starter-web | 2.7.x | Web 框架 |
| mybatis-plus-boot-starter | 3.5.x | MyBatis 增强 |
| spring-boot-starter-security | 2.7.x | 安全框架 |
| spring-boot-starter-validation | 2.7.x | 参数校验 |
| spring-boot-starter-cache | 2.7.x | 缓存支持 |
| mapstruct | 1.5.x | 对象转换 |
| lombok | 1.18.x | 代码简化 |
| hutool-all | 5.8.x | 工具类库 |
| knife4j-spring-boot-starter | 3.0.x | API 文档 |

## 关键文件

| 文件路径 | 说明 |
|--------|------|
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/enums/ErrorCodeConstants.java | 错误码常量定义，所有业务异常的统一入口 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/dal/dataobject/user/AdminUserDO.java | 用户实体类，核心聚合根 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/dal/dataobject/permission/RoleDO.java | 角色实体类，权限载体 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/dal/dataobject/permission/MenuDO.java | 菜单实体类，权限最小单元 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/service/permission/PermissionServiceImpl.java | 权限服务实现，核心业务逻辑 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/service/auth/AdminAuthServiceImpl.java | 认证服务实现，登录登出逻辑 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/controller/admin/auth/AuthController.java | 认证控制器，登录接口入口 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/api/permission/PermissionApi.java | 权限 API 接口，跨模块调用入口 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/enums/permission/DataScopeEnum.java | 数据权限枚举，5 种数据范围定义 |
| yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/enums/permission/MenuTypeEnum.java | 菜单类型枚举，目录/菜单/按钮 |

## 领域模型

### 聚合根

| 聚合 | 包含实体 | 说明 |
|-----|---------|------|
| User（用户聚合） | AdminUserDO、UserRoleDO、UserPostDO | 用户是系统的核心实体，关联角色和岗位，属于租户 |
| Role（角色聚合） | RoleDO、RoleMenuDO | 角色是权限的载体，关联菜单实现功能权限控制 |
| Menu（菜单聚合） | MenuDO | 菜单是权限的最小单元，支持目录、菜单、按钮三种类型 |
| Dept（部门聚合） | DeptDO | 部门是组织架构的核心，树形结构，支持数据权限 |
| Tenant（租户聚合） | TenantDO、TenantPackageDO | 租户是 SaaS 架构的核心，绑定套餐控制功能范围 |

### 值对象

| 值对象 | 说明 |
|-------|------|
| Post（岗位） | 岗位是用户的职位标识，不涉及复杂业务逻辑 |
| DictType/DictData（字典） | 字典是系统配置的枚举值，全局共享不区分租户 |
| Notice（通知公告） | 通知公告是系统级消息，简单 CRUD |

### 领域服务

| 领域服务 | 说明 |
|---------|------|
| PermissionService | 权限领域服务，处理用户-角色-菜单的关联关系 |
| AdminAuthService | 认证领域服务，处理登录、登出、令牌刷新 |
| TenantService | 租户领域服务，处理租户生命周期管理 |

## 设计与架构补充

### 实体继承体系

- BaseDO：包含 id、creator、createTime、updater、updateTime、deleted 字段
- TenantBaseDO：继承 BaseDO，额外包含 tenantId 字段，实现多租户隔离
- 使用 `@TenantIgnore` 注解标记不需要租户隔离的表（如 system_menu、system_dict_data）

### 分层架构

| 层 | 职责 | 主要组件 |
|---|------|---------|
| api | 模块间 API 接口，供其他模块 RPC 调用 | PermissionApi（权限校验接口）、AdminUserApi（用户信息查询接口）、DeptApi（部门信息查询接口）、PostApi（岗位信息查询接口）、DictDataApi（字典数据查询接口）、RoleApi（角色信息查询接口）、SmsSendApi（短信发送接口）、MailSendApi（邮件发送接口）、NotifyMessageSendApi（站内信发送接口）、SocialUserApi（社交用户接口）、LoginLogApi（登录日志接口）、OperateLogApi（操作日志接口） |
| controller | HTTP 接口，供前端调用 | AuthController（认证：登录、登出、刷新令牌）、UserController（用户管理）、RoleController（角色管理）、MenuController（菜单管理）、DeptController（部门管理）、PostController（岗位管理）、DictTypeController/DictDataController（字典管理）、TenantController（租户管理）、TenantPackageController（租户套餐管理）、SmsChannelController/SmsTemplateController（短信管理）、MailAccountController/MailTemplateController（邮件管理）、NotifyTemplateController/NotifyMessageController（站内信管理）、OAuth2ClientController（OAuth2 客户端管理）、SocialClientController（社交客户端管理） |
| service | 业务逻辑层 | auth（AdminAuthService 认证服务）、permission（PermissionService、RoleService、MenuService 权限服务）、user（AdminUserService 用户服务）、dept（DeptService、PostService 组织服务）、dict（DictTypeService、DictDataService 字典服务）、tenant（TenantService、TenantPackageService 租户服务）、sms（SmsChannelService、SmsTemplateService、SmsSendService、SmsCodeService 短信服务）、mail（MailAccountService、MailTemplateService、MailSendService 邮件服务）、notify（NotifyTemplateService、NotifyMessageService、NotifySendService 站内信服务）、oauth2（OAuth2ClientService、OAuth2TokenService、OAuth2CodeService OAuth2 服务）、social（SocialClientService、SocialUserService 社交服务）、logger（LoginLogService、OperateLogService 日志服务） |
| dal | 数据访问层 | dataobject（32 个 DO 实体类）、mysql（MyBatis Mapper 接口）、redis（Redis 缓存操作） |

### 模块间通信

对外暴露的 API 及其消费方（PermissionApi、AdminUserApi、DeptApi、DictDataApi、SmsSendApi、MailSendApi 等）见 [README.md](README.md) 的「对外暴露的 API」一节，此处不再重复。

**消费的其他模块 API**：

| API | 用途 |
|-----|------|
| PermissionCommonApi（framework-common） | 基础权限校验能力 |
| FileApi（yudao-module-infra） | 文件上传（用户头像等） |

**消息队列**：暂未使用。

### 表关系（ER 关系）

| 表 | 关联表 | 关系 | 外键 | 说明 |
|---|-------|------|------|------|
| system_users | system_dept | N:1 | dept_id | 用户属于一个部门 |
| system_users | system_post | N:N | post_ids（JSON 数组） | 用户可关联多个岗位 |
| system_user_role | system_users | N:1 | user_id | 用户与角色的关联 |
| system_user_role | system_role | N:1 | role_id | 用户与角色的关联 |
| system_role_menu | system_role | N:1 | role_id | 角色与菜单的关联 |
| system_role_menu | system_menu | N:1 | menu_id | 角色与菜单的关联 |
| system_menu | system_menu | N:1 | parent_id | 菜单树形结构 |
| system_dept | system_dept | N:1 | parent_id | 部门树形结构 |
| system_tenant | system_tenant_package | N:1 | package_id | 租户绑定套餐 |
| system_dict_data | system_dict_type | N:1 | dict_type | 字典数据归属字典类型 |
| system_sms_template | system_sms_channel | N:1 | channel_id | 短信模板归属渠道 |
| system_mail_template | system_mail_account | N:1 | account_id | 邮件模板归属邮箱账号 |
