# OA 日程接口 (OaScheduleController)

> 提供个人日程的创建、维护、查询与已读回执，支持"我的日程 / 共享给我的日程 / 全部日程"三类分页视图，并在日程开始前向创建人与参与人发送提醒通知。

## 接口路径前缀

/oa/schedule  (Controller: OaScheduleController)

---

## 1. 日程维护（写操作）

仅日程创建人可修改或删除自己的日程，修改、删除前均按 creator 做归属校验。

### 1.1 创建日程

- **路径**: POST /oa/schedule/create
- **权限**: oa:schedule:create
- **说明**: 新增一条日程并为参与人建立参与关系，返回日程编号。

**请求参数 (OaScheduleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | | 日程编号（新增时不传） |
| type | Integer | 是 | @NotNull、@InEnum(OaScheduleTypeEnum) | 日程类型：1 日程提醒 / 2 假日安排 |
| priority | Integer | 是 | @NotNull、@InEnum(OaPriorityEnum) | 优先级：1 一般 / 2 重要 / 3 紧急 |
| title | String | 是 | @NotBlank、@Size(max=255) | 标题 |
| description | String | 否 | @Size(max=1000) | 描述 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@AssertTrue（须晚于 startTime） | 结束时间 |
| remind | Boolean | 是 | @NotNull | 是否提醒 |
| participantUserIds | List\<Long\> | 否 | 元素 @NotNull | 参与人用户编号列表 |

**响应**: CommonResult\<Long\> — 日程编号。

**业务逻辑**:
1. 校验参与人用户编号列表中的用户均存在。
2. 将请求 VO 转换为 OaScheduleDO，设置 reminded=false 后插入日程。
3. 参与人编号去重后批量插入参与关系，readStatus 初始化为 false。

### 1.2 更新日程

- **路径**: PUT /oa/schedule/update
- **权限**: oa:schedule:update
- **说明**: 修改本人创建的日程并按差异增量维护参与关系，请求参数同 1.1 的 OaScheduleSaveReqVO（id 必传）。

**请求参数 (OaScheduleSaveReqVO)**: 同 1.1，其中 id 为日程编号。

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验日程存在且 creator 为当前登录用户（否则抛 SCHEDULE_ACCESS_DENIED）。
2. 校验参与人用户均存在。
3. 更新日程并将 reminded 重置为 false，重新进入提醒周期（不清空阅读回执）。
4. 查询原参与关系，与去重后的新参与人列表按 userId 计算 diff。
5. 批量插入新增的参与关系（readStatus=false），删除被取消的参与关系。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_100_000 | 日程不存在 |
| 1_054_100_001 | 无权访问该日程 |

### 1.3 删除日程

- **路径**: DELETE /oa/schedule/delete
- **权限**: oa:schedule:delete
- **说明**: 删除本人创建的日程及其全部参与关系。

**请求参数**: Query 参数 id（Long，必填，日程编号）。

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验日程存在且属于当前登录用户。
2. 先删除该日程的全部参与关系。
3. 再删除日程记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_100_000 | 日程不存在 |
| 1_054_100_001 | 无权访问该日程 |

---

## 2. 日程查询（读操作）

按创建人或参与关系过滤可见日程；列表类接口统一拼装创建人昵称、部门名称及参与人信息。

### 2.1 获得日程详情

- **路径**: GET /oa/schedule/get
- **权限**: oa:schedule:query
- **说明**: 获得日程详情，创建人或参与人可访问，并附带各参与人的阅读回执（仅详情返回 participants）。

**请求参数**: Query 参数 id（Long，必填，日程编号）。

**响应**: CommonResult\<OaScheduleRespVO\>，字段见 2.3 响应表，其中额外包含：

| 字段 | 类型 | 说明 |
|-----|------|------|
| participants | List\<Participant\> | 参与人阅读信息列表，仅详情返回 |

Participant 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 参与人用户编号 |
| userName | String | 参与人用户昵称 |
| readStatus | Boolean | 是否已读 |
| readTime | LocalDateTime | 首次阅读时间 |

**业务逻辑**:
1. 校验日程存在；创建人可直接访问。
2. 非创建人时，查询该日程参与关系，当前用户不在参与人中则抛 SCHEDULE_ACCESS_DENIED。
3. 查询全部参与关系，批量查询参与人昵称后转换为 Participant 列表返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_100_000 | 日程不存在 |
| 1_054_100_001 | 无权访问该日程 |

### 2.2 标记本人已阅读日程

- **路径**: PUT /oa/schedule/update-read-status
- **权限**: oa:schedule:query
- **说明**: 当前参与人标记本人已读该日程，并记录首次阅读时间。

**请求参数**: Query 参数 id（Long，必填，日程编号）。

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 复用详情访问校验（创建人或参与人可访问，否则抛对应错误码）。
2. 查询本人的参与关系；当前用户不是参与人（如创建人未参与）或已读时直接返回。
3. 更新参与关系 readStatus=true 并记录 readTime 为当前时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_100_000 | 日程不存在 |
| 1_054_100_001 | 无权访问该日程 |

### 2.3 获得日程分页

- **路径**: GET /oa/schedule/page
- **权限**: oa:schedule:query
- **说明**: 组合查询"我的日程"与"共享给我的日程"，由 includeMine / includeReceived 控制范围。

**请求参数 (OaSchedulePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数（继承 PageParam） | 页码，默认 1 |
| pageSize | Integer | 否 | 分页参数（继承 PageParam） | 每页条数，默认 10 |
| includeMine | Boolean | 否 | | 是否包含我的日程 |
| includeReceived | Boolean | 否 | | 是否包含共享给我的日程 |
| title | String | 否 | | 标题，模糊匹配 |
| type | Integer | 否 | @InEnum(OaScheduleTypeEnum) | 日程类型：1 日程提醒 / 2 假日安排 |
| priority | Integer | 否 | @InEnum(OaPriorityEnum) | 优先级：1 一般 / 2 重要 / 3 紧急 |
| startTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 开始时间范围 |
| overlapTime | LocalDateTime[] | 否 | @Size(min=2, max=2) | 日历显示时间范围，查询与该范围相交的日程 |

**响应**: CommonResult\<PageResult\<OaScheduleRespVO\>\>，OaScheduleRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 日程编号 |
| creator | String | 创建人用户编号 |
| creatorName | String | 创建人用户昵称 |
| creatorDeptName | String | 创建人部门名称 |
| type | Integer | 日程类型 |
| priority | Integer | 优先级 |
| title | String | 标题 |
| description | String | 描述 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| remind | Boolean | 是否提醒 |
| participantUserIds | List\<Long\> | 参与人用户编号列表 |
| participantUserNames | List\<String\> | 参与人用户昵称列表 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. includeMine=false 时仅查共享日程：includeReceived=true 复用"共享给我的"查询，否则返回空分页。
2. 仅选本人日程（includeReceived=false）时复用"我的日程"分页查询。
3. 两者都包含时，先查询本人参与关系；无共享日程则退化为"我的日程"分页。
4. 否则按创建人或参与关系统一分页查询，同一日程只返回一次。
5. 批量查询参与人、创建人昵称及部门名称后拼装 RespVO 列表。

### 2.4 获得我的日程分页

- **路径**: GET /oa/schedule/my-page
- **权限**: oa:schedule:query
- **说明**: 分页查询当前登录用户创建的日程。

**请求参数 (OaSchedulePageReqVO)**: 同 2.3（includeMine / includeReceived 在本接口不生效）。

**响应**: CommonResult\<PageResult\<OaScheduleRespVO\>\> — 字段同 2.3。

**业务逻辑**:
1. 按 creator=当前用户加筛选条件执行本人日程分页查询。
2. 批量查询参与人、创建人昵称及部门名称后拼装 RespVO 列表。

### 2.5 获得共享给我的日程分页

- **路径**: GET /oa/schedule/received-page
- **权限**: oa:schedule:query
- **说明**: 分页查询其他用户共享给当前用户（本人为参与人）的日程。

**请求参数 (OaSchedulePageReqVO)**: 同 2.3（includeMine / includeReceived 在本接口不生效）。

**响应**: CommonResult\<PageResult\<OaScheduleRespVO\>\> — 字段同 2.3。

**业务逻辑**:
1. 查询当前用户的全部参与关系，为空时返回空分页。
2. 取参与关系中的日程编号集合，按筛选条件执行共享日程分页查询。
3. 批量查询参与人、创建人昵称及部门名称后拼装 RespVO 列表。

---

## 附：定时提醒（非 Controller 端点）

`OaScheduleServiceImpl#sendScheduleReminders` 由定时任务触发：查询 remind=true、未提醒且开始时间落在未来 remindBeforeHours 配置窗口内的日程，逐条通过自身代理在独立事务中向创建人与参与人发送 SCHEDULE_REMINDER 模板的站内信（参数含日程标题、开始时间及跳转路径 /oa/schedule/calendar），成功后置 reminded=true；单条失败仅记录日志，不影响其他日程。
