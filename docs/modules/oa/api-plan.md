# OA 工作计划接口 (OaPlanController)

> 提供个人工作计划的创建、维护、查询，以及管理者对下属成员计划进行点评和报表统计的能力。

## 接口路径前缀

/oa/plan  (Controller: OaPlanController)

---

## 1. 我的计划

当前登录用户对自己创建的工作计划进行管理，全部端点按 `creator` 做归属校验或过滤。

### 1.1 创建工作计划

- **路径**: POST /oa/plan/create
- **权限**: oa:plan:create
- **说明**: 新增一条本人的工作计划，返回计划编号。

**请求参数 (OaPlanSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | | 计划编号（新增时不传） |
| type | Integer | 是 | @NotNull、@InEnum(OaPlanTypeEnum) | 计划类型：1 日计划 / 2 周计划 / 3 月计划 |
| status | Integer | 是 | @NotNull、@InEnum(OaPlanStatusEnum) | 计划状态：1 未完成 / 2 已完成 / 3 已取消 |
| title | String | 是 | @NotBlank、@Size(max=50) | 标题 |
| label | String | 否 | @Size(max=255) | 标签 |
| content | String | 是 | @NotBlank、@Size(min=20) | 计划内容，不少于 20 个字符 |
| summary | String | 否 | @AssertTrue（非空时 trim 后不少于 20 字符） | 计划总结 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@AssertTrue（须晚于 startTime） | 结束时间 |
| fileUrls | List\<String\> | 否 | 元素 @NotBlank、@Size(max=512) | 附件地址列表 |

**响应**: CommonResult\<Long\> — 计划编号。

**业务逻辑**:
1. 将请求 VO 转换为 OaPlanDO。
2. 插入数据库，返回新计划的主键编号。

### 1.2 更新工作计划

- **路径**: PUT /oa/plan/update
- **权限**: oa:plan:update
- **说明**: 修改本人创建的工作计划，请求参数同 1.1 的 OaPlanSaveReqVO（id 必传）。

**请求参数 (OaPlanSaveReqVO)**: 同 1.1，其中 id 为计划编号。

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作计划存在（不存在抛 PLAN_NOT_EXISTS）。
2. 校验计划的 creator 与当前登录用户一致，否则抛 PLAN_ACCESS_DENIED。
3. 按 id 更新计划记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_110_000 | 工作计划不存在 |
| 1_054_110_001 | 无权操作该工作计划 |

### 1.3 删除工作计划

- **路径**: DELETE /oa/plan/delete
- **权限**: oa:plan:delete
- **说明**: 删除本人创建的工作计划。

**请求参数**: Query 参数 id（Long，必填，计划编号）。

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作计划存在。
2. 校验计划属于当前登录用户。
3. 按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_110_000 | 工作计划不存在 |
| 1_054_110_001 | 无权操作该工作计划 |

### 1.4 获得工作计划详情

- **路径**: GET /oa/plan/get
- **权限**: oa:plan:query
- **说明**: 获取本人某条工作计划的详情，附带创建人昵称与部门信息。

**请求参数**: Query 参数 id（Long，必填，计划编号）。

**响应**: CommonResult\<OaPlanRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 计划编号 |
| userId | Long | 创建人用户编号（取自 creator） |
| userName | String | 用户昵称 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| type | Integer | 计划类型 |
| status | Integer | 计划状态 |
| title | String | 标题 |
| label | String | 标签 |
| content | String | 计划内容 |
| summary | String | 计划总结 |
| comment | String | 计划点评 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| fileUrls | List\<String\> | 附件地址列表 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验工作计划存在且属于当前登录用户（否则抛 PLAN_NOT_EXISTS / PLAN_ACCESS_DENIED）。
2. 按计划的 creator 批量查询用户信息，再按用户 deptId 查询部门信息。
3. 拼接 userId、userName、deptId、deptName 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_110_000 | 工作计划不存在 |
| 1_054_110_001 | 无权操作该工作计划 |

### 1.5 获得工作计划分页

- **路径**: GET /oa/plan/page
- **权限**: oa:plan:query
- **说明**: 分页查询当前登录用户本人的工作计划，按创建时间倒序。

**请求参数 (OaPlanPageReqVO)**，继承 PageParam（pageNo、pageSize 必填）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| title | String | 否 | | 标题，模糊匹配 |
| label | String | 否 | | 标签，模糊匹配 |
| type | Integer | 否 | @InEnum(OaPlanTypeEnum) | 计划类型 |
| status | Integer | 否 | @InEnum(OaPlanStatusEnum) | 计划状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult\<PageResult\<OaPlanRespVO\>\> — 列表项字段同 1.4 的 OaPlanRespVO。

**业务逻辑**:
1. 以 `creator = 当前登录用户` 为固定条件，叠加 title/label 模糊、type/status 精确、createTime 区间过滤。
2. 按创建时间、id 倒序分页查询。
3. 批量补齐创建人昵称与部门名称后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_110_000 | 工作计划不存在（间接校验时使用） |

---

## 2. 计划报表

面向管理者的下属成员计划统计与点评。

### 2.1 获得工作计划报表分页

- **路径**: GET /oa/plan/report-page
- **权限**: oa:plan:query
- **说明**: 按成员维度分页展示其管理范围内成员在统计周期内的最新一条计划。

**请求参数 (OaPlanReportPageReqVO)**，继承 PageParam（pageNo、pageSize 必填）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userName | String | 否 | | 成员昵称，模糊筛选 |
| type | Integer | 是 | @NotNull、@InEnum(OaPlanTypeEnum) | 计划类型 |
| createTime | LocalDateTime[] | 是 | @NotNull、@Size(min=2, max=2)、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围（统计周期） |

**响应**: CommonResult\<PageResult\<OaPlanReportRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| userName | String | 用户昵称 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| planId | Long | 最新计划编号（无计划时为空） |
| status | Integer | 计划状态 |
| title | String | 标题 |
| label | String | 标签 |
| content | String | 计划内容 |
| summary | String | 计划总结 |
| comment | String | 计划点评 |
| fileUrls | List\<String\> | 附件地址列表 |
| createTime | LocalDateTime | 计划创建时间 |

**业务逻辑**:
1. 通过 AdminUserApi 获取当前登录用户管理范围内（下属）的用户列表。
2. 按成员昵称模糊过滤 userName，并按用户编号排序保证分页稳定。
3. 对成员列表在内存中分页。
4. 查询分页内成员在指定计划类型、统计周期内的计划，每位成员仅保留创建时间最新的一条。
5. 拼接用户、部门与最新计划信息，返回成员维度的报表分页。

### 2.2 点评工作计划

- **路径**: PUT /oa/plan/add-comment
- **权限**: oa:plan:comment
- **说明**: 对管理范围内成员的工作计划追加点评内容，多次点评按换行追加。

**请求参数 (OaPlanCommentReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 计划编号 |
| comment | String | 是 | @NotBlank、@Size(max=1000) | 计划点评内容 |

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作计划存在（不存在抛 PLAN_NOT_EXISTS）。
2. 获取当前用户管理范围内的用户集合，校验计划创建人在其中，否则抛 PLAN_ACCESS_DENIED。
3. 将本次点评以换行符追加到已有点评之后。
4. 对追加后的完整点评内容执行 Bean 校验（长度不超过 1000）。
5. 更新计划的 comment 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_110_000 | 工作计划不存在 |
| 1_054_110_001 | 无权操作该工作计划 |
