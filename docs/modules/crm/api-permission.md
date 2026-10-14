# CRM 数据权限接口 (CrmPermissionController)

> 提供 CRM 各业务数据（客户、联系人、商机、合同等）的团队成员协作权限管理：为成员授予/调整/移除数据权限级别，并支持负责人变更记录（CrmOwnerRecordService 为内部服务，无独立 admin 端点，供客户转移、公海领取/放入及公海统计调用）。

## 接口路径前缀

/crm/permission  (Controller: CrmPermissionController)

说明：

- `bizType` 对应 `CrmBizTypeEnum`（如 1=线索、2=客户、3=联系人、5=商机、6=合同 等），`bizId` 为对应业务数据编号。
- `level` 对应 `CrmPermissionLevelEnum`（READ 只读、WRITE 读写、OWNER 负责人）。
- 本控制器端点均未使用 `@PreAuthorize` 菜单权限，仅要求登录；数据级权限通过 CRM 专属 `@CrmPermission` 注解（AOP 切面）在业务数据维度校验。

## 1. 数据权限管理 (CrmPermissionController)

### 1.1 创建数据权限

- **路径**: POST /crm/permission/create
- **权限**: 已认证（Service 层 `@CrmPermission` 校验当前操作人为该数据的 OWNER 负责人）
- **说明**: 为指定用户添加某条 CRM 业务数据的团队协作权限，支持"同时添加"至该客户下的联系人、商机、合同。

**请求参数 (CrmPermissionSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 用户编号 |
| bizType | Integer | 是 | @NotNull、@InEnum(CrmBizTypeEnum) | CRM 类型 |
| bizId | Long | 是 | @NotNull | CRM 类型数据编号 |
| level | Integer | 是 | @NotNull、@InEnum(CrmPermissionLevelEnum) | 权限级别 |
| toBizTypes | List&lt;Integer&gt; | 否 | 无 | 同时添加的业务类型列表（添加客户团队成员时，可同时为该用户添加其联系人/商机/合同的权限） |

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 通过 `@CrmPermission` 切面校验当前操作人是该数据（bizType + bizId）的负责人（OWNER 级别）。
2. 校验待创建的权限不存在重复（同 bizType + bizId + userId 已有权限则抛出创建失败错误码），并校验被添加用户真实存在。
3. 插入一条 CrmPermissionDO 数据权限记录。
4. 若 `toBizTypes` 非空，按类型分别查询该客户（bizId）下归属于当前操作人的联系人、商机、合同列表。
5. 对每条关联数据校验被添加用户是否已拥有权限，已拥有则抛出"同时添加失败"错误码（含用户昵称、模块名、数据名、已有级别）；否则组装对应权限记录。
6. 批量插入"同时添加"生成的全部权限记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_007_008 | 创建数据权限失败，原因：所加用户已有权限 |
| 1_020_007_009 | 同时添加数据权限失败，原因：用户【{}】已有模块【{}】数据【{}】的【{}】权限 |

### 1.2 编辑数据权限

- **路径**: PUT /crm/permission/update
- **权限**: 已认证（控制器 `@CrmPermission` 校验当前操作人为该数据的 OWNER 负责人）
- **说明**: 将指定的一批数据权限记录统一调整为新的权限级别。

**请求参数 (CrmPermissionUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @NotNull | 数据权限编号列表 |
| bizType | Integer | 是 | @NotNull、@InEnum(CrmBizTypeEnum) | CRM 类型 |
| bizId | Long | 是 | @NotNull | CRM 类型数据编号 |
| level | Integer | 是 | @NotNull、@InEnum(CrmPermissionLevelEnum) | 权限级别 |

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 校验 `ids` 对应的数据权限记录是否全部存在，数量不一致则抛出"数据权限不存在"错误。
2. 将这批权限记录的 `level` 批量更新为请求中的权限级别。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_007_000 | 数据权限不存在 |

### 1.3 删除数据权限

- **路径**: DELETE /crm/permission/delete
- **权限**: 已认证（Service 层校验当前操作人为该数据的 OWNER 负责人）
- **说明**: 负责人批量移除某条业务数据上其他团队成员的数据权限。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| ids | Collection&lt;Long&gt; | 是 | 数据权限编号（支持逗号分隔多个） |

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 根据 `ids` 查询数据权限记录，记录为空则抛出"数据权限不存在"错误。
2. 校验所有记录属于同一个 `bizId`（同一业务数据），否则抛出"删除失败：只能属于同一个 bizId"错误。
3. 校验当前操作人在该 bizType + bizId 下存在权限记录，且级别为 OWNER 负责人，否则抛出"删除失败：没有权限"错误。
4. 批量删除这些数据权限记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_007_000 | 数据权限不存在 |
| 1_020_007_004 | 删除数据权限失败，原因：批量删除权限的时候，只能属于同一个 bizId 下 |
| 1_020_007_006 | 删除数据权限失败，原因：没有权限 |

### 1.4 删除自己的数据权限

- **路径**: DELETE /crm/permission/delete-self
- **权限**: 已认证
- **说明**: 团队成员主动退出协作，移除自己在某条业务数据上的数据权限（负责人不可退出）。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 数据权限编号 |

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 查询该 `id` 且归属当前登录用户的数据权限记录，不存在则抛出"数据权限不存在"错误。
2. 校验该记录级别不是 OWNER 负责人，负责人不允许删除自身权限，否则抛出"不能删除负责人"错误。
3. 删除该数据权限记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_007_000 | 数据权限不存在 |
| 1_020_007_007 | 删除数据权限失败，原因：不能删除负责人 |

### 1.5 获得数据权限列表

- **路径**: GET /crm/permission/list
- **权限**: 已认证
- **说明**: 查询某条业务数据（如某客户）的全部团队成员数据权限，并补充用户昵称、部门、岗位信息。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| bizType | Integer | 是 | CRM 类型 |
| bizId | Long | 是 | CRM 类型数据编号 |

**响应**: CommonResult&lt;List&lt;CrmPermissionRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 数据权限编号 |
| userId | Long | 用户编号 |
| bizType | Integer | CRM 类型 |
| bizId | Long | CRM 类型数据编号 |
| level | Integer | 权限级别 |
| nickname | String | 用户昵称 |
| deptName | String | 部门名称 |
| postNames | Set&lt;String&gt; | 岗位名称数组 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 根据 bizType + bizId 查询该业务数据的全部数据权限记录，为空直接返回空列表。
2. 批量查询权限记录涉及的用户信息（AdminUserApi）。
3. 根据用户所属部门批量查询部门信息（DeptApi），并根据用户岗位编号批量查询岗位信息（PostApi）。
4. 逐条拼接返回结果：补充用户昵称、部门名称、岗位名称集合。

**错误码**: 无专属错误码
