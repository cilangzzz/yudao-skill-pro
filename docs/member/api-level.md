# 会员等级与经验接口 (MemberLevelController / MemberLevelRecordController / MemberExperienceRecordController)

> 管理会员等级配置（创建/修改/删除/查询），以及会员等级变动记录、经验变动记录的查询。

## 接口路径前缀

- `/member/level` (Controller: MemberLevelController)
- `/member/level-record` (Controller: MemberLevelRecordController)
- `/member/experience-record` (Controller: MemberExperienceRecordController)

## 1. 会员等级管理（MemberLevelController）

### 1.1 创建会员等级

- **路径**: POST /member/level/create
- **权限**: member:level:create
- **说明**: 新增一个会员等级配置，校验名称、等级值唯一及升级经验区间合法。

**请求参数 (MemberLevelCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotBlank | 等级名称 |
| experience | Integer | 是 | @NotNull、@Positive | 升级经验（必须大于 0） |
| level | Integer | 是 | @NotNull、@Positive | 等级值（必须大于 0） |
| discountPercent | Integer | 是 | @NotNull、@Range(min=0, max=100) | 享受折扣（0-100） |
| icon | String | 否 | @URL | 等级图标（URL 格式） |
| backgroundUrl | String | 否 | @URL | 等级背景图（URL 格式） |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（1 开启 / 0 禁用） |

**响应**: CommonResult<Long>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的等级编号 |

**业务逻辑**:
1. 校验等级配置有效性：校验等级名称在全部等级中唯一，重复则报错
2. 校验等级值唯一，重复则报错
3. 校验升级经验必须大于上一个等级的升级经验、小于下一个等级的升级经验，否则报错
4. 将请求 VO 转换为 MemberLevelDO 插入数据库
5. 返回新等级的编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_011_001 | 用户等级名称[{}]已被使用 |
| 1_004_011_002 | 用户等级值[{}]已被[{}]使用 |
| 1_004_011_003 | 升级经验必须大于上一个等级[{}]设置的升级经验[{}] |
| 1_004_011_004 | 升级经验必须小于下一个等级[{}]设置的升级经验[{}] |

### 1.2 更新会员等级

- **路径**: PUT /member/level/update
- **权限**: member:level:update
- **说明**: 修改已有会员等级配置，校验规则与创建一致。

**请求参数 (MemberLevelUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 等级编号 |
| name | String | 是 | @NotBlank | 等级名称 |
| experience | Integer | 是 | @NotNull、@Positive | 升级经验（必须大于 0） |
| level | Integer | 是 | @NotNull、@Positive | 等级值（必须大于 0） |
| discountPercent | Integer | 是 | @NotNull、@Range(min=0, max=100) | 享受折扣（0-100） |
| icon | String | 否 | @URL | 等级图标（URL 格式） |
| backgroundUrl | String | 否 | @URL | 等级背景图（URL 格式） |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态 |

**响应**: CommonResult<Boolean>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 固定返回 true |

**业务逻辑**:
1. 校验等级存在，不存在则报错
2. 校验配置有效性：名称唯一、等级值唯一、升级经验处于相邻等级区间内（排除自身）
3. 将请求 VO 转换为 MemberLevelDO，按编号更新数据库

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_011_000 | 用户等级不存在 |
| 1_004_011_001 | 用户等级名称[{}]已被使用 |
| 1_004_011_002 | 用户等级值[{}]已被[{}]使用 |
| 1_004_011_003 | 升级经验必须大于上一个等级[{}]设置的升级经验[{}] |
| 1_004_011_004 | 升级经验必须小于下一个等级[{}]设置的升级经验[{}] |

### 1.3 删除会员等级

- **路径**: DELETE /member/level/delete
- **权限**: member:level:delete
- **说明**: 删除指定等级，等级下存在用户时禁止删除。

**请求参数**: 无（Query 参数 id：Long，编号，必填）

**响应**: CommonResult<Boolean>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 固定返回 true |

**业务逻辑**:
1. 校验等级存在，不存在则报错
2. 通过会员服务统计该等级下的用户数量，大于 0 则报错无法删除
3. 按编号删除等级记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_011_000 | 用户等级不存在 |
| 1_004_011_005 | 用户等级下存在用户，无法删除 |

### 1.4 获得会员等级

- **路径**: GET /member/level/get
- **权限**: member:level:query
- **说明**: 按编号查询单个会员等级详情。

**请求参数**: 无（Query 参数 id：Long，编号，必填）

**响应**: CommonResult<MemberLevelRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 等级编号 |
| name | String | 等级名称 |
| experience | Integer | 升级经验 |
| level | Integer | 等级值 |
| discountPercent | Integer | 享受折扣 |
| icon | String | 等级图标 |
| backgroundUrl | String | 等级背景图 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 编号非空且大于 0 时，按编号查询 MemberLevelDO，否则返回 null
2. 转换为 MemberLevelRespVO 返回

### 1.5 获取会员等级精简信息列表

- **路径**: GET /member/level/list-all-simple
- **权限**: 已认证（仅登录，无 @PreAuthorize 权限校验）
- **说明**: 只返回开启状态的会员等级精简信息，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberLevelSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 等级编号 |
| name | String | 等级名称 |
| icon | String | 等级图标 |

**业务逻辑**:
1. 查询所有开启状态的等级，按等级值（level）升序排序
2. 转换为精简 VO 列表（仅含编号、名称、图标）返回

### 1.6 获得会员等级列表

- **路径**: GET /member/level/list
- **权限**: member:level:query
- **说明**: 按条件筛选全部会员等级（不分页），结果按等级值升序。

**请求参数 (MemberLevelListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 等级名称（模糊匹配） |
| status | Integer | 否 | - | 状态（1 开启 / 0 禁用） |

**响应**: CommonResult&lt;List&lt;MemberLevelRespVO&gt;&gt;，字段同 1.4 的 MemberLevelRespVO。

**业务逻辑**:
1. 按名称模糊匹配、状态精确匹配构建查询条件（条件为空时忽略），按等级值升序查询全部记录
2. 转换为 MemberLevelRespVO 列表返回

## 2. 会员等级记录（MemberLevelRecordController）

### 2.1 获得会员等级记录

- **路径**: GET /member/level-record/get
- **权限**: member:level-record:query
- **说明**: 按编号查询单条会员等级变动记录。

**请求参数**: 无（Query 参数 id：Long，编号，必填）

**响应**: CommonResult<MemberLevelRecordRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 记录编号 |
| userId | Long | 用户编号 |
| levelId | Long | 等级编号 |
| level | Integer | 变动后的会员等级 |
| discountPercent | Integer | 享受折扣 |
| experience | Integer | 变动的经验值（正为增加，负为扣减） |
| userExperience | Integer | 会员此时的经验 |
| remark | String | 备注（变动原因） |
| description | String | 描述 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询等级记录 MemberLevelRecordDO
2. 转换为 MemberLevelRecordRespVO 返回

### 2.2 获得会员等级记录分页

- **路径**: GET /member/level-record/page
- **权限**: member:level-record:query
- **说明**: 分页查询会员等级变动记录，支持按用户、等级、时间区间筛选。

**请求参数 (MemberLevelRecordPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| userId | Long | 否 | - | 用户编号 |
| levelId | Long | 否 | - | 等级编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;MemberLevelRecordRespVO&gt;&gt;，记录字段同 2.1 的 MemberLevelRecordRespVO。

**业务逻辑**:
1. 按用户编号、等级编号、创建时间区间构建条件，分页查询等级记录
2. 转换为 MemberLevelRecordRespVO 分页结果返回

## 3. 会员经验记录（MemberExperienceRecordController）

### 3.1 获得会员经验记录

- **路径**: GET /member/experience-record/get
- **权限**: member:experience-record:query
- **说明**: 按编号查询单条会员经验变动记录。

**请求参数**: 无（Query 参数 id：Long，编号，必填）

**响应**: CommonResult<MemberExperienceRecordRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 记录编号 |
| userId | Long | 用户编号 |
| bizId | String | 业务编号 |
| bizType | Integer | 业务类型 |
| title | String | 标题 |
| experience | Integer | 经验（正为增加，负为扣减） |
| totalExperience | Integer | 变更后的经验 |
| description | String | 描述 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询经验记录 MemberExperienceRecordDO
2. 转换为 MemberExperienceRecordRespVO 返回

### 3.2 获得会员经验记录分页

- **路径**: GET /member/experience-record/page
- **权限**: member:experience-record:query
- **说明**: 分页查询会员经验变动记录，支持按用户、业务类型、时间区间等筛选。

**请求参数 (MemberExperienceRecordPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| userId | Long | 否 | - | 用户编号 |
| bizId | String | 否 | - | 业务编号 |
| bizType | Integer | 否 | - | 业务类型 |
| title | String | 否 | - | 标题 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;MemberExperienceRecordRespVO&gt;&gt;，记录字段同 3.1 的 MemberExperienceRecordRespVO。

**业务逻辑**:
1. 按用户编号、业务编号、业务类型、标题、创建时间区间构建条件，分页查询经验记录
2. 转换为 MemberExperienceRecordRespVO 分页结果返回

## 附：等级与经验域相关错误码（1-004-011-XXX 段）

| 错误码 | 说明 |
|-------|------|
| 1_004_011_000 | 用户等级不存在 |
| 1_004_011_001 | 用户等级名称[{}]已被使用 |
| 1_004_011_002 | 用户等级值[{}]已被[{}]使用 |
| 1_004_011_003 | 升级经验必须大于上一个等级[{}]设置的升级经验[{}] |
| 1_004_011_004 | 升级经验必须小于下一个等级[{}]设置的升级经验[{}] |
| 1_004_011_005 | 用户等级下存在用户，无法删除 |
| 1_004_011_201 | 用户经验业务类型不支持 |

> 说明：等级记录与经验记录由内部服务写入（管理员调整用户等级 `updateUserLevel`、经验增减 `addExperience` 等），admin 端仅提供查询接口。
