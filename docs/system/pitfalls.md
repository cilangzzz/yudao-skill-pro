# 注意事项与已知坑点

> 使用 system 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 @TenantIgnore 遗漏

**问题**: 新增表时忘记标注 `@TenantIgnore`，导致不该隔离的表被强制加上 `tenant_id` 条件，查询结果为空或数据异常。

**受影响的表**: `system_menu`、`system_dict_type`、`system_dict_data`、`system_tenant`、`system_tenant_package`

**解决**: 这些表全局共享，不区分租户，必须使用 `@TenantIgnore` 注解。

### 1.2 租户ID透传丢失

**问题**: 在异步线程、MQ消费者、定时任务中调用系统服务时，`TenantContextHolder` 中的租户ID丢失，导致查询到错误租户的数据或报错。

**解决**:
- 异步线程使用 `TenantContextHolder.set(tenantId)` 手动设置
- MQ消息体中携带 `tenantId`，消费时手动恢复
- 定时任务遍历所有租户逐个处理

### 1.3 租户套餐修改不生效

**问题**: 修改租户套餐的 `menuIds` 后，租户管理员的权限没有立即更新。

**原因**: 权限数据被 Redis 缓存，未清除。

**解决**: 更新套餐时需要同步清除相关缓存：
```java
@Caching(evict = {
    @CacheEvict(value = RedisKeyConstants.MENU_ROLE_ID_LIST, allEntries = true),
    @CacheEvict(value = RedisKeyConstants.PERMISSION_MENU_ID_LIST, allEntries = true)
})
```

## 2. 权限相关

### 2.1 缓存注解不生效

**问题**: 在同一个类中调用带 `@Cacheable` 注解的方法，缓存不生效。

**原因**: Spring AOP 基于代理，同类内部调用不经过代理。

**解决**: 通过 `getSelf()` 方法获取代理对象再调用：
```java
@Resource
@Lazy
private PermissionService self; // 代理对象

public void someMethod() {
    self.getCachedPermission(userId); // 通过代理调用，缓存生效
}
```

### 2.2 数据权限注解位置错误

**问题**: `@DataPermission` 注解加在 Controller 层，不生效。

**解决**: `@DataPermission` 必须加在 Service 层方法上，因为它通过 AOP 拦截 SQL 实现。

### 2.3 权限标识大小写

**问题**: 权限标识不一致导致校验失败，如 `System:user:create` vs `system:user:create`。

**解决**: 统一使用小写，格式为 `模块:功能:操作`。

### 2.4 删除角色后用户权限未更新

**问题**: 删除角色后，已分配该角色的用户的权限没有立即更新。

**原因**: 用户的角色列表和权限数据被缓存。

**解决**: 删除角色时清除相关缓存，并记录关联的用户ID以便精确清除用户级缓存。

## 3. 用户相关

### 3.1 用户名唯一索引范围

**问题**: 同一用户名在不同租户下可以重复，但同一租户下不能重复。创建用户时报唯一索引冲突。

**解决**: `uk_username(username, tenant_id)` 是联合唯一索引，校验时需要限定租户范围。

### 3.2 手机号唯一索引范围

**问题**: 与用户名同理，`uk_mobile(mobile, tenant_id)` 也是租户内唯一。

**注意**: 如果业务需要全局唯一手机号，需要额外逻辑处理。

### 3.3 密码加密方式

**问题**: 存储密码时使用了错误的加密方式，登录时密码比对失败。

**解决**: 使用 BCrypt 加密：
```java
String encodedPassword = passwordEncoder.encode(rawPassword);
boolean matches = passwordEncoder.matches(rawPassword, encodedPassword);
```

### 3.4 postIds 使用 JSON 字段

**问题**: `system_users.post_ids` 存储的是 JSON 数组格式，直接查询无法使用索引。

**解决**: 如需按岗位查询用户，应通过 `system_user_post` 关联表（如已建立）或使用 JSON 函数查询。

## 4. 部门相关

### 4.1 树形结构循环引用

**问题**: 更新部门时将 `parentId` 设置为自身或子部门ID，导致树形结构出现循环。

**解决**: 更新前校验新父部门不能是自身或自身的任何后代节点。

### 4.2 部门删除级联检查

**问题**: 删除部门时未检查子部门和关联用户，导致数据孤立。

**解决**: 删除前必须检查：
1. 是否存在子部门
2. 是否有用户归属该部门
3. 是否有角色的数据权限范围包含该部门

## 5. 菜单相关

### 5.1 菜单删除后角色权限残留

**问题**: 删除菜单后，`system_role_menu` 表中仍保留关联记录，导致权限数据不一致。

**解决**: 删除菜单时同步清理 `system_role_menu` 中的关联记录，并清除权限缓存。

### 5.2 菜单类型与权限标识

**问题**: 按钮类型（type=3）的菜单没有设置 `permission`，导致权限校验失败。

**解决**: 按钮类型的菜单必须设置权限标识，目录和菜单类型可选。

## 6. 字典相关

### 6.1 字典数据缓存

**问题**: 修改字典数据后，前端显示的仍是旧值。

**原因**: 字典数据通常有缓存，修改后未清除。

**解决**: 修改字典类型/数据时清除对应的 Redis 缓存。

### 6.2 字典类型删除

**问题**: 删除字典类型时未级联删除字典数据，导致孤立数据。

**解决**: 删除字典类型前，先删除其下所有字典数据。

## 7. 短信/邮件相关

### 7.1 策略模式切换渠道

**问题**: 新增短信渠道后，发送时找不到对应的客户端实现。

**解决**: 确保在 `SmsClientFactory` 中注册了新渠道的客户端实例。

### 7.2 验证码防刷

**问题**: 短信验证码接口没有防刷限制，可被恶意频繁调用。

**解决**: 使用 `SmsCodeService` 管理验证码，内置：
- 发送频率限制（如60秒内不能重复发送）
- 每日发送次数上限
- 验证码有效期

## 8. OAuth2 相关

### 8.1 令牌存储在数据库

**问题**: 高并发场景下，数据库存储令牌可能成为性能瓶颈。

**解决**: 当前实现在数据库中存储令牌，可通过索引优化。如有高并发需求，考虑迁移到 Redis 存储。

### 8.2 客户端密钥安全

**问题**: `system_oauth2_client.secret` 存储明文密钥。

**解决**: 密钥应加密存储，对比时使用加密比对。

## 9. 通用注意事项

### 9.1 逻辑删除

**问题**: 查询时未排除已删除记录，返回了脏数据。

**解决**: MyBatis-Plus 的逻辑删除会自动在查询条件中加上 `deleted = 0`，但需要确保：
- DO 中有 `@TableLogic` 注解的字段
- 唯一索引查询需要考虑已删除记录（如用户软删除后重新创建同名用户）

### 9.2 数据权限与分页

**问题**: 使用 `@DataPermission` 时，分页查询的 count 总数不正确。

**解决**: 确保数据权限的 SQL 注入同时应用于数据查询和 count 查询。

### 9.3 事务注解选择

**问题**: 跨数据源操作使用 `@Transactional` 导致事务不生效。

**解决**:
- 单数据源：使用 `@Transactional(rollbackFor = Exception.class)`
- 跨数据源：使用 `@DSTransactional`

### 9.4 MapStruct 转换空值

**问题**: MapStruct 转换时，源对象的 null 值覆盖了目标对象的默认值。

**解决**: 使用 `@Mapping(target = "xxx", ignore = true)` 或在策略中配置 null 值处理。
