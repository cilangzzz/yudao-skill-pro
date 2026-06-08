# 租户管理接口 (TenantController / TenantPackageController)

> 多租户架构的核心支撑，管理租户的创建、套餐绑定、过期控制，实现SaaS化的数据隔离。

## 1. 租户管理接口

接口路径前缀: `/system/tenant`  (Controller: `TenantController`)

### 1.1 创建租户

- **路径**: `POST /system/tenant/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant:create')")`
- **说明**: 创建新的租户

**请求参数 (TenantSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| name | String | 是 | @NotBlank @Size(2,100) | 租户名称 |
| contactName | String | 否 | @Size(0,100) | 联系人姓名 |
| contactMobile | String | 否 | @Mobile | 联系手机号 |
| packageId | Long | 是 | @NotNull | 租户套餐编号 |
| expireTime | LocalDateTime | 是 | @NotNull | 过期时间 |
| accountCount | Integer | 是 | @NotNull @Min(1) | 账号数量上限 |
| status | Integer | 否 | - | 状态（0正常 1停用） |
| websites | String | 否 | - | 绑定域名列表 |
| username | String | 是 | @NotBlank | 管理员账号 |
| password | String | 是 | @NotBlank | 管理员密码 |

**响应**: `CommonResult<Long>` — 返回租户编号

**业务逻辑**:
1. 校验租户套餐是否存在且状态正常
2. 创建租户记录
3. 创建租户管理员用户（归属租户下）
4. 创建默认管理员角色并关联套餐菜单
5. 为管理员用户分配角色

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_015_001 | 租户套餐不存在 |

### 1.2 更新租户

- **路径**: `PUT /system/tenant/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant:update')")`

**请求参数 (TenantSaveReqVO)**: 同创建，额外包含 `id` 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 租户编号 |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验租户是否存在
2. 校验套餐是否存在
3. 更新租户基本信息
4. 如套餐变更，同步更新管理员角色的菜单权限

### 1.3 删除租户

- **路径**: `DELETE /system/tenant/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant:delete')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 租户编号 |

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验租户是否存在
2. 逻辑删除租户记录
3. 禁用租户下所有用户
4. 清理相关缓存

### 1.4 获取租户详情

- **路径**: `GET /system/tenant/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant:query')")`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | 是 | 租户编号 |

**响应**: `CommonResult<TenantRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 租户编号 |
| name | String | 租户名称 |
| contactName | String | 联系人 |
| contactMobile | String | 联系手机 |
| packageId | Long | 套餐编号 |
| packageName | String | 套餐名称 |
| expireTime | LocalDateTime | 过期时间 |
| accountCount | Integer | 账号数量上限 |
| status | Integer | 状态 |
| websites | String | 绑定域名 |
| username | String | 管理员账号 |
| createTime | LocalDateTime | 创建时间 |

### 1.5 获取租户分页列表

- **路径**: `POST /system/tenant/get-page`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant:query')")`

**请求参数 (TenantPageReqVO)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |
| name | String | 否 | 租户名称（模糊查询） |
| status | Integer | 否 | 状态 |
| contactMobile | String | 否 | 联系手机 |

**响应**: `CommonResult<PageResult<TenantRespVO>>`

### 1.6 获取租户列表

- **路径**: `GET /system/tenant/get-list`
- **权限**: 已认证
- **说明**: 返回所有状态正常的租户，用于下拉选择

**响应**: `CommonResult<List<TenantRespVO>>`

---

## 2. 租户套餐接口

接口路径前缀: `/system/tenant-package`  (Controller: `TenantPackageController`)

### 2.1 创建套餐

- **路径**: `POST /system/tenant-package/create`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant-package:create')")`

**请求参数 (TenantPackageSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| name | String | 是 | @NotBlank @Size(2,100) | 套餐名称 |
| status | Integer | 否 | - | 状态（0正常 1停用） |
| menuIds | Set\<Long\> | 否 | - | 关联菜单编号数组 |
| remark | String | 否 | - | 备注 |

**响应**: `CommonResult<Long>` — 返回套餐编号

**业务逻辑**:
1. 校验套餐名称是否唯一
2. 插入套餐记录，menuIds 以JSON格式存储

### 2.2 更新套餐

- **路径**: `PUT /system/tenant-package/update`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant-package:update')")`

**请求参数**: 同创建，额外包含 `id`

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验套餐是否存在
2. 更新套餐信息
3. 同步更新使用该套餐的所有租户管理员角色的菜单权限

### 2.3 删除套餐

- **路径**: `DELETE /system/tenant-package/delete`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant-package:delete')")`

**请求参数**: `id` (Long)

**响应**: `CommonResult<Boolean>`

**业务逻辑**:
1. 校验套餐是否存在
2. 检查是否有租户绑定该套餐，如有则拒绝删除

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_002_016_000 | 套餐下存在租户，不允许删除 |

### 2.4 获取套餐详情

- **路径**: `GET /system/tenant-package/get`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant-package:query')")`

**请求参数**: `id` (Long)

**响应**: `CommonResult<TenantPackageRespVO>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 套餐编号 |
| name | String | 套餐名称 |
| status | Integer | 状态 |
| menuIds | Set\<Long\> | 关联菜单编号 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

### 2.5 获取所有套餐列表

- **路径**: `GET /system/tenant-package/get-all`
- **权限**: `@PreAuthorize("@ss.hasPermission('system:tenant-package:query')")`

**请求参数**: 无

**响应**: `CommonResult<List<TenantPackageRespVO>>`

---

## 3. 租户工作机制

### 3.1 租户隔离原理

```
请求 -> TenantContextFilter -> 从Header/Cookie提取租户ID -> TenantContextHolder
                                                                    |
                              MyBatis拦截器 <-----------------------+
                                    |
                              自动拼接 tenant_id = ?
```

- 通过 `TenantBaseDO` 基类，所有业务表自动携带 `tenant_id` 字段
- MyBatis 拦截器自动在 SQL 中注入租户条件
- 使用 `@TenantIgnore` 注解标记不需要租户隔离的表（如 `system_menu`、`system_dict_data`）

### 3.2 租户过期处理

- 登录时校验租户是否过期
- 定时任务扫描即将过期的租户并发送通知
- 过期租户下的用户无法登录

### 3.3 套餐功能控制

- 套餐通过 `menu_ids` 字段控制租户可用的功能范围
- 租户管理员角色的菜单权限由套餐决定
- 修改套餐时自动同步关联租户的功能权限
