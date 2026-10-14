# 会员用户接口 (MemberUserController)

> 管理端会员用户域：维护会员资料（手机/昵称/标签/分组等）、分页查询会员列表（返显标签/等级/分组名称），以及管理员直接调整会员等级与积分。

## 接口路径前缀

/member/user  (Controller: MemberUserController)

## 1. 会员资料维护

### 1.1 更新会员用户

- **路径**: PUT /member/user/update
- **权限**: member:user:update
- **说明**: 管理员修改会员基础资料（手机号、状态、昵称、标签、分组、等级归属等）

**请求参数 (MemberUserUpdateReqVO)**（继承 MemberUserBaseVO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| mobile | String | 是 | @NotNull | 手机号 |
| status | Byte | 是 | @NotNull | 状态（0 开启 / 1 禁用） |
| email | String | 否 | @Email、@Size(max=50) | 邮箱 |
| nickname | String | 是 | @NotNull | 用户昵称 |
| avatar | String | 否 | @URL | 头像（必须 URL 格式） |
| name | String | 否 | 无 | 用户真实姓名 |
| sex | Integer | 否 | 无 | 用户性别 |
| areaId | Long | 否 | 无 | 所在地编号 |
| areaName | String | 否 | 无 | 所在地全称 |
| birthday | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd) | 出生日期 |
| mark | String | 否 | 无 | 会员备注 |
| tagIds | List\<Long> | 否 | 无 | 会员标签编号列表 |
| levelId | Long | 否 | 无 | 会员等级编号 |
| groupId | Long | 否 | 无 | 用户分组编号 |

**响应**: CommonResult\<Boolean>（更新成功返回 true）

**业务逻辑**: 1. 校验用户是否存在，不存在抛 USER_NOT_EXISTS 2. 校验手机号唯一，被其他用户占用抛 USER_MOBILE_USED 3. 校验邮箱唯一，被其他用户占用抛 USER_EMAIL_USED 4. 转换为 MemberUserDO 更新会员表 5. 若状态被置为禁用，调用 oauth2TokenApi.removeAccessToken 删除该会员的访问 Token，强制其下线

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_001_000 | 用户不存在 |
| 1_004_001_002 | 修改手机失败，该手机号({})已经被使用 |
| 1_004_001_004 | 修改邮箱失败，该邮箱({})已经被使用 |

### 1.2 更新会员用户等级

- **路径**: PUT /member/user/update-level
- **权限**: member:user:update-level
- **说明**: 管理员调整会员等级（levelId 传空表示取消等级），自动补偿经验并留下等级/经验变动流水

**请求参数 (MemberUserUpdateLevelReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| levelId | Long | 否 | 无 | 用户等级编号（取消用户等级时值为空） |
| reason | String | 是 | @NotBlank | 修改原因 |

**响应**: CommonResult\<Boolean>（调整成功返回 true）

**业务逻辑**:（由 MemberLevelService#updateUserLevel 实现）1. 查询会员用户，不存在抛 USER_NOT_EXISTS 2. 等级未发生变化时直接返回 3. 构建等级变动记录：取消等级时变动经验 = -当前经验、当前经验归零；调整等级时校验目标等级存在（不存在抛 LEVEL_NOT_EXISTS），变动经验 = 目标等级升级经验 - 会员当前经验，写入 member_level_record 4. 写入会员经验变动记录（member_experience_record，业务类型 ADMIN） 5. 更新会员表上的等级编号、经验值（levelId 为空时按 0 存储，避免被更新过滤） 6. 给会员发送等级变动消息（notifyMemberLevelChange，当前为预留空实现）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_001_000 | 用户不存在 |
| 1_004_011_000 | 用户等级不存在 |

### 1.3 更新会员用户积分

- **路径**: PUT /member/user/update-point
- **权限**: member:user:update-point
- **说明**: 管理员手动增减会员积分，正数增加、负数扣减，并写入积分变动流水

**请求参数 (MemberUserUpdatePointReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| point | Integer | 是 | @NotNull | 变动积分，正数为增加，负数为减少 |

**响应**: CommonResult\<Boolean>（调整成功返回 true）

**业务逻辑**:（由 MemberPointRecordService#createPointRecord 实现，业务类型 ADMIN、业务编号为当前登录管理员 ID）1. 变动积分为 0 时直接返回 2. 校验积分余额：当前积分 + 变动积分小于 0 时记录错误日志并直接返回（不生效） 3. 更新用户积分：正数走 updatePointIncr 累加；负数走 updatePointDecr 扣减，未命中行数（积分不足）时抛 USER_POINT_NOT_ENOUGH 4. 写入积分变动记录 member_point_record（含变动后总积分 totalPoint）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_001_003 | 用户积分余额不足 |

## 2. 会员查询

### 2.1 获得会员用户

- **路径**: GET /member/user/get
- **权限**: member:user:query
- **说明**: 按编号查询单个会员详情，附加返显会员等级名称

**请求参数**: 无（Query 参数 `id`：Long，必填，用户编号）

**响应**: CommonResult\<MemberUserRespVO>（用户不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| mobile | String | 手机号 |
| status | Byte | 状态 |
| email | String | 邮箱 |
| nickname | String | 用户昵称 |
| avatar | String | 头像 |
| name | String | 用户姓名 |
| sex | Integer | 用户性别 |
| areaId | Long | 所在地编号 |
| areaName | String | 所在地全称 |
| birthday | LocalDateTime | 出生日期 |
| mark | String | 会员备注 |
| tagIds | List\<Long> | 会员标签编号列表 |
| levelId | Long | 会员等级编号 |
| groupId | Long | 用户分组编号 |
| registerIp | String | 注册 IP |
| loginIp | String | 最后登录 IP |
| loginDate | LocalDateTime | 最后登录时间 |
| createTime | LocalDateTime | 创建时间 |
| point | Integer | 积分 |
| totalPoint | Integer | 总积分 |
| tagNames | List\<String> | 会员标签名称 |
| levelName | String | 会员等级名称（Controller 单独查询返显） |
| groupName | String | 用户分组名称 |
| experience | Integer | 用户经验值 |

**业务逻辑**: 1. 按编号查询会员用户，为空直接返回 null 2. 转换为 MemberUserRespVO 3. 若 levelId 非空，查询会员等级并把等级名称写入 levelName

### 2.2 获得会员用户分页

- **路径**: GET /member/user/page
- **权限**: member:user:query
- **说明**: 分页查询会员列表，支持手机号/邮箱/昵称/登录时间/创建时间/标签/等级/分组组合筛选，并批量返显标签、等级、分组名称

**请求参数 (MemberUserPageReqVO)**（继承 PageParam 分页参数 pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | 无（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 否 | 无（继承 PageParam） | 每页条数 |
| mobile | String | 否 | 无 | 手机号（模糊匹配） |
| email | String | 否 | 无 | 邮箱（模糊匹配） |
| nickname | String | 否 | 无 | 用户昵称（模糊匹配） |
| loginDate | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 最后登录时间区间 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| tagIds | List\<Long> | 否 | 无 | 会员标签编号列表（FIND_IN_SET 命中任一即返回） |
| levelId | Long | 否 | 无 | 会员等级编号（精确匹配） |
| groupId | Long | 否 | 无 | 用户分组编号（精确匹配） |

**响应**: CommonResult\<PageResult\<MemberUserRespVO>>，列表元素字段同 [2.1 获得会员用户](#21-获得会员用户) 的响应表

**业务逻辑**: 1. 组装查询条件分页查询会员表：mobile/email/nickname LIKE、loginDate/createTime BETWEEN、levelId/groupId 等值、tagIds 以 FIND_IN_SET 匹配逗号分隔的 tag_ids 字段，按 id 倒序 2. 结果为空时返回空分页 3. 汇总结果中所有 tagIds，批量查询会员标签 4. 批量查询结果中涉及的会员等级与用户分组 5. 转换为 MemberUserRespVO 并批量返显 tagNames、levelName、groupName

**错误码**: 无（纯查询）
