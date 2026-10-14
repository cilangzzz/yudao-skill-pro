# 用户分组接口 (MemberGroupController)

> 管理后台对会员用户分组（如"购物达人"）的维护，支持分组的增删改查、状态管理与精简下拉列表，供会员分组营销/筛选等场景使用。

## 接口路径前缀

/member/group  (Controller: MemberGroupController)

## 1. 分组管理

### 1.1 创建用户分组

- **路径**: POST /member/group/create
- **权限**: member:group:create
- **说明**: 新增一个用户分组，返回新分组编号。

**请求参数 (MemberGroupCreateReqVO)**: 继承 MemberGroupBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 分组名称，如"购物达人" |
| remark | String | 否 | 无 | 备注 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启、1 禁用） |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的用户分组编号 |

**业务逻辑**:
1. 将创建请求 VO 转换为 MemberGroupDO 实体。
2. 通过 Mapper 插入数据库。
3. 返回新分组的编号 id。

### 1.2 更新用户分组

- **路径**: PUT /member/group/update
- **权限**: member:group:update
- **说明**: 按编号更新用户分组的名称、备注、状态等信息。

**请求参数 (MemberGroupUpdateReqVO)**: 继承 MemberGroupBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 分组编号 |
| name | String | 是 | @NotNull | 分组名称 |
| remark | String | 否 | 无 | 备注 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启、1 禁用） |

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验指定 id 的分组是否存在，不存在则抛出 GROUP_NOT_EXISTS 异常。
2. 将更新请求 VO 转换为 MemberGroupDO 实体。
3. 按主键 id 执行更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_012_000 | 用户分组不存在 |

### 1.3 删除用户分组

- **路径**: DELETE /member/group/delete
- **权限**: member:group:delete
- **说明**: 按编号删除用户分组，若分组下仍存在用户则禁止删除。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无 | 分组编号 |

**响应**: CommonResult&lt;Boolean&gt;，成功返回 true

**业务逻辑**:
1. 校验指定 id 的分组是否存在，不存在则抛出 GROUP_NOT_EXISTS 异常。
2. 通过 MemberUserService 查询该分组下的用户数量。
3. 若分组下存在用户，抛出 GROUP_HAS_USER 异常，禁止删除。
4. 校验通过后按主键 id 删除分组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_012_000 | 用户分组不存在 |
| 1_004_012_001 | 用户分组下存在用户，无法删除 |

### 1.4 获得用户分组

- **路径**: GET /member/group/get
- **权限**: member:group:query
- **说明**: 按编号查询单个用户分组的详细信息。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无 | 分组编号 |

**响应**: CommonResult&lt;MemberGroupRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分组编号 |
| name | String | 分组名称 |
| remark | String | 备注 |
| status | Integer | 状态（0 开启、1 禁用） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号 id 查询 MemberGroupDO 记录。
2. 通过 MemberGroupConvert 将 DO 转换为 RespVO 返回。

### 1.5 获取会员分组精简信息列表

- **路径**: GET /member/group/list-all-simple
- **权限**: 已认证（无 @PreAuthorize 权限校验）
- **说明**: 只包含开启状态的会员分组，主要用于前端的下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberGroupSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分组编号 |
| name | String | 分组名称 |

**业务逻辑**:
1. 调用 getEnableGroupList 获取开启状态的分组列表（按 status 过滤）。
2. 通过 MemberGroupConvert.convertSimpleList 转换为精简 VO 列表返回。

### 1.6 获得用户分组分页

- **路径**: GET /member/group/page
- **权限**: member:group:query
- **说明**: 分页查询用户分组列表，支持名称、状态、创建时间筛选。

**请求参数 (MemberGroupPageReqVO)**: 继承 PageParam（分页参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull | 每页条数，最大值为 200 |
| name | String | 否 | 无 | 分组名称，模糊匹配 |
| status | Integer | 否 | 无 | 状态（0 开启、1 禁用） |
| createTime | LocalDateTime[] | 否 | 无 | 创建时间区间，格式 yyyy-MM-dd HH:mm:ss |

**响应**: CommonResult&lt;PageResult&lt;MemberGroupRespVO&gt;&gt;，列表项字段同 [1.4 获得用户分组](#14-获得用户分组)

**业务逻辑**:
1. 按分页查询条件（名称、状态、创建时间区间）执行 selectPage 查询。
2. 通过 MemberGroupConvert.convertPage 将分页结果转换为 RespVO 分页返回。
