# 租户管理接口 (TenantController、TenantPackageController)

> 提供 SaaS 多租户能力的管理端接口：租户（含租户管理员账号初始化）与租户套餐（控制租户可用菜单范围）的维护，以及登录页所需的免认证租户查询。

## 接口路径前缀

- `/system/tenant` (Controller: TenantController)
- `/system/tenant-package` (Controller: TenantPackageController)

---

## 1. 租户管理（TenantController）

### 1.1 使用租户名，获得租户编号

- **路径**: GET /system/tenant/get-id-by-name
- **权限**: @PermitAll（免认证，且 @TenantIgnore 忽略租户过滤）
- **说明**: 登录界面根据用户输入的租户名，换取租户编号。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | - | 租户名 |

**响应**: CommonResult<Long>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 租户编号，租户不存在时为 null |

**业务逻辑**: 1. 按租户名查询租户记录；2. 存在则返回其 id，否则返回 null。

### 1.2 获取租户精简信息列表

- **路径**: GET /system/tenant/simple-list
- **权限**: @PermitAll（免认证，且 @TenantIgnore 忽略租户过滤）
- **说明**: 只包含开启状态的租户，用于【首页】选择租户下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;TenantRespVO>&gt;（仅填充 id、name 两个字段）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 租户编号 |
| name | String | 租户名 |

**业务逻辑**: 1. 查询状态为开启（CommonStatusEnum.ENABLE）的全部租户；2. 转换为仅含 id/name 的精简 VO 列表返回。

### 1.3 使用域名，获得租户信息

- **路径**: GET /system/tenant/get-by-website
- **权限**: @PermitAll（免认证，且 @TenantIgnore 忽略租户过滤）
- **说明**: 登录界面根据访问域名，识别对应租户。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| website | String | 是 | @Pattern(域名格式) | 域名，正则 `^[a-zA-Z0-9.-]+(:\d{1,5})?$` |

**响应**: CommonResult&lt;TenantRespVO>（仅填充 id、name 两个字段，可能为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 租户编号 |
| name | String | 租户名 |

**业务逻辑**: 1. 按域名查询绑定了该域名的租户列表，取第一条；2. 租户不存在或已停用时返回 null；3. 否则返回仅含 id/name 的精简 VO。

### 1.4 创建租户

- **路径**: POST /system/tenant/create
- **权限**: system:tenant:create
- **说明**: 创建租户，并自动初始化租户管理员角色与账号。

**请求参数 (TenantSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | - | - | 租户编号（创建时不传） |
| name | String | 是 | @NotNull | 租户名 |
| contactName | String | 是 | @NotNull | 联系人 |
| contactMobile | String | 否 | - | 联系手机 |
| status | Integer | 是 | @NotNull | 租户状态（CommonStatusEnum） |
| websites | List&lt;String> | 否 | - | 绑定域名数组 |
| packageId | Long | 是 | @NotNull | 租户套餐编号 |
| expireTime | LocalDateTime | 是 | @NotNull | 过期时间 |
| accountCount | Integer | 是 | @NotNull | 账号数量 |
| username | String | 创建必填 | @Pattern(数字字母)、@Size(min=4, max=30)、@AssertTrue | 管理员用户账号（仅创建时传递，由数字、字母组成，4-30 位） |
| password | String | 创建必填 | @Length(min=4, max=16)、@AssertTrue | 管理员密码（仅创建时传递，4-16 位） |

> @AssertTrue 校验 `isUsernameValid`：新建时 username、password 必须同时传递；修改时不要求。

**响应**: CommonResult&lt;Long>（新租户编号）

**业务逻辑**:
1. 校验租户名不重复（TENANT_NAME_DUPLICATE）。
2. 校验每个绑定域名不与其他租户重复（TENANT_WEBSITE_DUPLICATE）。
3. 校验套餐有效：套餐必须存在且未禁用（validTenantPackage）。
4. 插入租户记录。
5. 在新租户上下文中（TenantUtils.execute）创建租户管理员角色：名称/编码取 RoleCodeEnum.TENANT_ADMIN，类型为系统内置，并将套餐的菜单权限分配给该角色。
6. 创建管理员用户（username/password 来自请求），并分配租户管理员角色。
7. 回写租户的 contactUserId 为该管理员用户编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_015_004 | 名字为【{}】的租户已存在 |
| 1_002_015_005 | 域名为【{}】的租户已存在 |
| 1_002_016_000 | 租户套餐不存在 |
| 1_002_016_002 | 名字为【{}】的租户套餐已被禁用 |

### 1.5 更新租户

- **路径**: PUT /system/tenant/update
- **权限**: system:tenant:update
- **说明**: 更新租户基本信息；套餐变更时同步调整租户内角色权限。

**请求参数 (TenantSaveReqVO)**: 同 1.4（id 必传；username/password 更新时无需传递，@AssertTrue 校验自动放行）

**响应**: CommonResult&lt;Boolean>（固定 true）

**业务逻辑**:
1. 校验租户存在（TENANT_NOT_EXISTS），且非系统内置租户（packageId=0 时抛 TENANT_CAN_NOT_UPDATE_SYSTEM）。
2. 校验租户名不重复（排除自身）。
3. 校验绑定域名不重复（排除自身）。
4. 校验套餐存在且未禁用。
5. 更新租户记录。
6. 若套餐发生变化：在该租户上下文中，租户管理员角色的菜单权限重置为新套餐菜单；其他角色的菜单权限与新套餐菜单取交集（剔除超出套餐的权限）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_015_000 | 租户不存在 |
| 1_002_015_003 | 系统租户不能进行修改、删除等操作！ |
| 1_002_015_004 | 名字为【{}】的租户已存在 |
| 1_002_015_005 | 域名为【{}】的租户已存在 |
| 1_002_016_000 | 租户套餐不存在 |
| 1_002_016_002 | 名字为【{}】的租户套餐已被禁用 |

### 1.6 删除租户

- **路径**: DELETE /system/tenant/delete
- **权限**: system:tenant:delete
- **说明**: 删除单个租户。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 租户编号 |

**响应**: CommonResult&lt;Boolean>（固定 true）

**业务逻辑**: 1. 校验租户存在且非系统内置租户（validateUpdateTenant）；2. 删除租户记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_015_000 | 租户不存在 |
| 1_002_015_003 | 系统租户不能进行修改、删除等操作！ |

### 1.7 批量删除租户

- **路径**: DELETE /system/tenant/delete-list
- **权限**: system:tenant:delete
- **说明**: 批量删除多个租户。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long> | 是 | - | 租户编号列表 |

**响应**: CommonResult&lt;Boolean>（固定 true）

**业务逻辑**: 1. 逐个校验租户存在且非系统内置租户；2. 批量删除租户记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_015_000 | 租户不存在 |
| 1_002_015_003 | 系统租户不能进行修改、删除等操作！ |

### 1.8 获得租户

- **路径**: GET /system/tenant/get
- **权限**: system:tenant:query
- **说明**: 按编号获得租户详情。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 租户编号 |

**响应**: CommonResult&lt;TenantRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 租户编号 |
| name | String | 租户名 |
| contactName | String | 联系人 |
| contactMobile | String | 联系手机 |
| status | Integer | 租户状态 |
| websites | List&lt;String> | 绑定域名数组 |
| packageId | Long | 租户套餐编号 |
| expireTime | LocalDateTime | 过期时间 |
| accountCount | Integer | 账号数量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询租户并转换为 RespVO 返回。

### 1.9 获得租户分页

- **路径**: GET /system/tenant/page
- **权限**: system:tenant:query
- **说明**: 分页查询租户列表。

**请求参数 (TenantPageReqVO)**（继承 PageParam：pageNo/pageNo 默认 1、pageSize 默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 租户名（模糊匹配） |
| contactName | String | 否 | - | 联系人 |
| contactMobile | String | 否 | - | 联系手机 |
| status | Integer | 否 | - | 租户状态（0正常 1停用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;TenantRespVO>>（列表项字段同 1.8）

**业务逻辑**: 1. 按查询条件执行租户分页查询并转换返回。

### 1.10 导出租户 Excel

- **路径**: GET /system/tenant/export-excel
- **权限**: system:tenant:export（@ApiAccessLog 记录导出操作日志）
- **说明**: 按分页条件导出全量租户 Excel（文件名：租户.xls）。

**请求参数 (TenantPageReqVO)**: 同 1.9（pageSize 强制设为 PAGE_SIZE_NONE，不分页取全量）

**响应**: 无 CommonResult 包装，直接向 HttpServletResponse 输出 Excel 文件流。导出列（来自 TenantRespVO 的 @ExcelProperty）：租户编号、租户名、联系人、联系手机、状态（字典转换）、创建时间。

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 按条件查询全部租户。
3. 通过 ExcelUtils 写出 Excel 到响应流。

---

## 2. 租户套餐管理（TenantPackageController）

### 2.1 创建租户套餐

- **路径**: POST /system/tenant-package/create
- **权限**: system:tenant-package:create
- **说明**: 创建租户套餐，绑定可使用的菜单集合。

**请求参数 (TenantPackageSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | - | - | 套餐编号（创建时不传） |
| name | String | 是 | @NotEmpty | 套餐名 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态 |
| remark | String | 否 | - | 备注 |
| menuIds | Set&lt;Long> | 是 | @NotNull | 关联的菜单编号集合 |

**响应**: CommonResult&lt;Long>（新套餐编号）

**业务逻辑**:
1. 校验套餐名不重复（TENANT_PACKAGE_NAME_DUPLICATE）。
2. 插入套餐记录并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_016_003 | 已经存在该名字的租户套餐 |

### 2.2 更新租户套餐

- **路径**: PUT /system/tenant-package/update
- **权限**: system:tenant-package:update
- **说明**: 更新套餐信息；菜单集合变化时同步刷新使用该套餐的所有租户的角色权限。

**请求参数 (TenantPackageSaveReqVO)**: 同 2.1（id 必传）

**响应**: CommonResult&lt;Boolean>（固定 true）

**业务逻辑**:
1. 校验套餐存在（TENANT_PACKAGE_NOT_EXISTS）。
2. 校验套餐名不重复（排除自身）。
3. 更新套餐记录。
4. 若菜单集合发生变化：查询使用该套餐的全部租户，逐个调用 updateTenantRoleMenu —— 租户管理员角色权限重置为新菜单集合，其他角色权限与新菜单集合取交集。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_016_000 | 租户套餐不存在 |
| 1_002_016_003 | 已经存在该名字的租户套餐 |

### 2.3 删除租户套餐

- **路径**: DELETE /system/tenant-package/delete
- **权限**: system:tenant-package:delete
- **说明**: 删除单个套餐，要求没有租户正在使用。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 套餐编号 |

**响应**: CommonResult&lt;Boolean>（固定 true）

**业务逻辑**:
1. 校验套餐存在。
2. 校验无租户使用该套餐（按 packageId 统计租户数，>0 时抛 TENANT_PACKAGE_USED）。
3. 删除套餐记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_016_000 | 租户套餐不存在 |
| 1_002_016_001 | 租户正在使用该套餐，请给租户重新设置套餐后再尝试删除 |

### 2.4 批量删除租户套餐

- **路径**: DELETE /system/tenant-package/delete-list
- **权限**: system:tenant-package:delete
- **说明**: 批量删除套餐，任一被使用即失败。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long> | 是 | - | 套餐编号列表 |

**响应**: CommonResult&lt;Boolean>（固定 true）

**业务逻辑**:
1. 逐个校验无租户使用该套餐（计数 >0 抛 TENANT_PACKAGE_USED）。
2. 批量删除套餐记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_016_001 | 租户正在使用该套餐，请给租户重新设置套餐后再尝试删除 |

### 2.5 获得租户套餐

- **路径**: GET /system/tenant-package/get
- **权限**: system:tenant-package:query
- **说明**: 按编号获得套餐详情。

**请求参数**: 无独立 VO，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 套餐编号 |

**响应**: CommonResult&lt;TenantPackageRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 套餐编号 |
| name | String | 套餐名 |
| status | Integer | 状态 |
| remark | String | 备注 |
| menuIds | Set&lt;Long> | 关联的菜单编号集合 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询套餐并转换为 RespVO 返回。

### 2.6 获得租户套餐分页

- **路径**: GET /system/tenant-package/page
- **权限**: system:tenant-package:query
- **说明**: 分页查询套餐列表。

**请求参数 (TenantPackagePageReqVO)**（继承 PageParam：pageNo 默认 1、pageSize 默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 套餐名 |
| status | Integer | 否 | - | 状态 |
| remark | String | 否 | - | 备注 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;TenantPackageRespVO>>（列表项字段同 2.5）

**业务逻辑**: 1. 按查询条件执行套餐分页查询并转换返回。

### 2.7 获取租户套餐精简信息列表

- **路径**: GET /system/tenant-package/get-simple-list（别名 /system/tenant-package/simple-list）
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 只包含开启状态的套餐，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;TenantPackageSimpleRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 套餐编号 |
| name | String | 套餐名 |

**业务逻辑**: 1. 查询状态为开启（CommonStatusEnum.ENABLE）的全部套餐；2. 转换为精简 VO 列表返回。

---

## 附：本域错误码汇总（ErrorCodeConstants，前缀 1_002_015 / 1_002_016）

| 错误码 | 常量 | 说明 |
|-------|------|------|
| 1_002_015_000 | TENANT_NOT_EXISTS | 租户不存在 |
| 1_002_015_001 | TENANT_DISABLE | 名字为【{}】的租户已被禁用 |
| 1_002_015_002 | TENANT_EXPIRE | 名字为【{}】的租户已过期 |
| 1_002_015_003 | TENANT_CAN_NOT_UPDATE_SYSTEM | 系统租户不能进行修改、删除等操作！ |
| 1_002_015_004 | TENANT_NAME_DUPLICATE | 名字为【{}】的租户已存在 |
| 1_002_015_005 | TENANT_WEBSITE_DUPLICATE | 域名为【{}】的租户已存在 |
| 1_002_016_000 | TENANT_PACKAGE_NOT_EXISTS | 租户套餐不存在 |
| 1_002_016_001 | TENANT_PACKAGE_USED | 租户正在使用该套餐，请给租户重新设置套餐后再尝试删除 |
| 1_002_016_002 | TENANT_PACKAGE_DISABLE | 名字为【{}】的租户套餐已被禁用 |
| 1_002_016_003 | TENANT_PACKAGE_NAME_DUPLICATE | 已经存在该名字的租户套餐 |

> 说明：TENANT_DISABLE / TENANT_EXPIRE 由 `validTenant` 在登录鉴权链路中抛出（校验租户状态与有效期），本域管理端点不直接触发。系统租户指 packageId = 0（TenantDO.PACKAGE_ID_SYSTEM）的内置租户，不使用套餐，禁止修改与删除。
