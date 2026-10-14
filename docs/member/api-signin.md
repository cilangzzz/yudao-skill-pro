# 签到接口 (MemberSignInConfigController / MemberSignInRecordController)

> 会员签到域：管理端维护「签到规则」（第 x 天奖励积分/经验），并查询会员的「签到记录」分页；App 端用户签到动作会按规则发放积分与经验。

## 接口路径前缀

- `/member/sign-in/config` (Controller: MemberSignInConfigController) —— 签到规则
- `/member/sign-in/record` (Controller: MemberSignInRecordController) —— 签到记录

## 1. 签到规则（MemberSignInConfigController）

### 1.1 创建签到规则

- **路径**: POST /member/sign-in/config/create
- **权限**: point:sign-in-config:create
- **说明**: 新增一条签到天数奖励规则，签到天数不允许重复。

**请求参数 (MemberSignInConfigCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| day | Integer | 是 | @NotNull | 签到第 x 天 |
| point | Integer | 是 | @NotNull、@PositiveOrZero、@AssertTrue(isConfigAward) | 奖励积分，不能小于 0 |
| experience | Integer | 是 | @NotNull、@PositiveOrZero、@AssertTrue(isConfigAward) | 奖励经验，不能小于 0 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 禁用） |

> 类级校验 `isConfigAward`：奖励积分和经验不能同时为 0。

**响应**: CommonResult&lt;Long&gt; —— 新规则的编号

**业务逻辑**: 1. 校验签到天数 day 是否已存在（重复则抛 SIGN_IN_CONFIG_EXISTS）；2. VO 转换为 MemberSignInConfigDO；3. 插入数据库并返回自增主键 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_009_001 | 签到天数规则已存在 |

### 1.2 更新签到规则

- **路径**: PUT /member/sign-in/config/update
- **权限**: point:sign-in-config:update
- **说明**: 修改指定签到规则，同样校验天数不与其它规则重复。

**请求参数 (MemberSignInConfigUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 规则自增主键 |
| day | Integer | 是 | @NotNull | 签到第 x 天 |
| point | Integer | 是 | @NotNull、@PositiveOrZero、@AssertTrue(isConfigAward) | 奖励积分，不能小于 0 |
| experience | Integer | 是 | @NotNull、@PositiveOrZero、@AssertTrue(isConfigAward) | 奖励经验，不能小于 0 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 禁用） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 校验规则 id 是否存在（不存在抛 SIGN_IN_CONFIG_NOT_EXISTS）；2. 校验签到天数是否与其它规则重复（排除自身，重复抛 SIGN_IN_CONFIG_EXISTS）；3. 转换为 DO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_009_000 | 签到天数规则不存在 |
| 1_004_009_001 | 签到天数规则已存在 |

### 1.3 删除签到规则

- **路径**: DELETE /member/sign-in/config/delete
- **权限**: point:sign-in-config:delete
- **说明**: 按编号删除签到规则。

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 校验规则 id 是否存在（不存在抛 SIGN_IN_CONFIG_NOT_EXISTS）；2. 按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_009_000 | 签到天数规则不存在 |

### 1.4 获得签到规则

- **路径**: GET /member/sign-in/config/get
- **权限**: point:sign-in-config:query
- **说明**: 按编号查询单条签到规则详情。

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult&lt;MemberSignInConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 自增主键 |
| day | Integer | 签到第 x 天 |
| point | Integer | 奖励积分 |
| experience | Integer | 奖励经验 |
| status | Integer | 状态（0 开启 / 1 禁用） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 MemberSignInConfigDO；2. 转换为 RespVO 返回（id 不存在时返回 null 数据）。

### 1.5 获得签到规则列表

- **路径**: GET /member/sign-in/config/list
- **权限**: point:sign-in-config:query
- **说明**: 查询全部签到规则，按签到天数升序排列（不分页）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberSignInConfigRespVO&gt;&gt;，元素字段同 1.4 响应表。

**业务逻辑**: 1. 查询全部签到规则记录；2. 按 day（签到天数）升序排序后返回。

## 2. 签到记录（MemberSignInRecordController）

### 2.1 获得签到记录分页

- **路径**: GET /member/sign-in/record/page
- **权限**: point:sign-in-record:query
- **说明**: 分页查询会员签到记录，支持按用户昵称、天数、时间范围筛选，结果拼接用户昵称。

**请求参数 (MemberSignInRecordPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | （继承 PageParam，默认 1） | 页码 |
| pageSize | Integer | 否 | （继承 PageParam，默认 10） | 每页条数 |
| nickname | String | 否 | 无 | 签到用户昵称（模糊匹配） |
| day | Integer | 否 | 无 | 第几天签到 |
| userId | Long | 否 | 无 | 用户编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 签到时间范围（区间查询） |

**响应**: CommonResult&lt;PageResult&lt;MemberSignInRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 签到自增 id |
| userId | Long | 签到用户编号 |
| nickname | String | 用户昵称（关联会员表拼接） |
| day | Integer | 第几天签到（连续签到的天数序号） |
| point | Integer | 该次签到获得的积分 |
| createTime | LocalDateTime | 签到时间 |

**业务逻辑**: 1. 若传入 nickname 非空，先按昵称查询会员用户列表，结果为空则直接返回空分页；2. 将匹配到的用户 id 集合与其它条件组合，执行签到记录分页查询；3. Controller 层将分页结果中的 userId 批量查询会员用户，拼接昵称（nickname）后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_010_000 | 今日已签到，请勿重复签到 |

> 说明：`1_004_010_000` 由 App 端签到动作（Service `createSignRecord`）触发，管理端记录查询接口本身不会抛出；`1_004_009_000` / `1_004_009_001` 为签到规则的校验错误码，见第 1 节各端点。
