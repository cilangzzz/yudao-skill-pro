# OA 考勤接口 (OaAttendanceController)

> 提供 OA 考勤的员工自助打卡、考勤记录管理（改/删/查）以及周报、月报统计能力，考勤记录由打卡与请假、出差审批自动写入。

## 接口路径前缀

/oa/attendance  (Controller: OaAttendanceController)

## 1. 我的考勤

### 1.1 执行当前用户打卡

- **路径**: POST /oa/attendance/clock
- **权限**: 已认证（无独立权限标识，按当前登录用户打卡）
- **说明**: 当前用户执行打卡，自动判断是上班打卡、下班打卡还是刷新下班打卡，返回考勤记录编号。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 考勤记录编号（新建或刷新的下班记录 id） |

**业务逻辑**:
1. 取当前时间（截断到秒），校验必须在配置的每日最早打卡时间之后、标准下班时间之前（均不含边界，默认 05:00~17:00），否则抛出打卡时间无效错误。
2. 查询当前用户当天的全部考勤记录，判断是否已存在上班打卡记录。
3. 情况一：尚无上班记录，创建上班打卡记录，状态按打卡时间计算（晚于标准上班时间为迟到，否则正常），同时记录打卡时间与客户端 IP。
4. 情况二：已有上班记录但无下班记录，创建下班打卡记录，状态按打卡时间计算（早于标准下班时间为早退，否则正常）。
5. 情况三：已有下班记录，刷新该下班记录的打卡时间、状态与 IP，返回原记录编号。整个过程在事务中执行。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_160_001 | 仅允许在每天 {} 之后、{} 之前打卡（{} 为配置的最早打卡时间与标准下班时间） |

### 1.2 获得我的考勤分页列表

- **路径**: GET /oa/attendance/my-page
- **权限**: 已认证（无独立权限标识，仅查询本人记录）
- **说明**: 分页查询当前登录用户自己的考勤记录，支持类型、状态、时间范围筛选。

**请求参数 (OaAttendancePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull/@Min(1) | 页码，从 1 开始（继承 PageParam） |
| pageSize | Integer | 是 | @NotNull/@Min(1)/@Max(200) | 每页条数（继承 PageParam） |
| userId | Long | 否 | 无 | 用户编号（本人查询场景忽略，按登录用户过滤） |
| type | Integer | 否 | @InEnum(OaAttendanceTypeEnum) | 考勤类型：1 上班打卡、2 下班打卡、3 请假、4 出差 |
| status | Integer | 否 | @InEnum(OaAttendanceStatusEnum) | 考勤状态：1 正常、2 迟到、3 早退、4 请假、5 出差 |
| attendanceTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 考勤时间范围（开始、结束） |

**响应**: CommonResult&lt;PageResult&lt;OaAttendanceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 考勤记录编号 |
| userId | Long | 用户编号 |
| userName | String | 用户昵称（来自 system 用户） |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称（来自 system 部门） |
| type | Integer | 考勤类型：1 上班打卡、2 下班打卡、3 请假、4 出差 |
| status | Integer | 考勤状态：1 正常、2 迟到、3 早退、4 请假、5 出差 |
| attendanceTime | LocalDateTime | 考勤时间 |
| attendanceIp | String | 考勤 IP |
| remark | String | 考勤备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按当前登录用户编号与筛选条件分页查询本人考勤记录。
2. Controller 批量查询用户昵称与部门名称，拼装进响应 VO 列表。

### 1.3 获得我的今日考勤列表

- **路径**: GET /oa/attendance/my-today-list
- **权限**: 已认证（无独立权限标识，仅查询本人记录）
- **说明**: 查询当前登录用户今天（0 点至 24 点）的全部考勤记录，用于打卡页面展示。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;OaAttendanceRespVO&gt;&gt;，字段同 1.2 响应。

**业务逻辑**:
1. 按当前登录用户编号查询当天日期范围内的考勤记录列表。
2. Controller 批量拼装用户昵称与部门名称后返回。

## 2. 考勤管理

### 2.1 更新考勤记录

- **路径**: PUT /oa/attendance/update
- **权限**: oa:attendance:update
- **说明**: 管理员修正下属员工的考勤状态与备注，如将迟到改为正常。

**请求参数 (OaAttendanceUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 考勤记录编号 |
| status | Integer | 是 | @NotNull/@InEnum(OaAttendanceStatusEnum) | 考勤状态：1 正常、2 迟到、3 早退、4 请假、5 出差 |
| remark | String | 否 | @Size(max = 500) | 考勤备注 |

**响应**: CommonResult&lt;Boolean&gt;（true 表示成功）

**业务逻辑**:
1. 校验考勤记录存在，且属于当前操作用户的管理范围（下属员工），越界记录与不存在记录统一按不存在处理，避免泄露他人考勤。
2. 校验考勤类型与状态组合合法：上班打卡只能是正常/迟到，下班打卡只能是正常/早退，请假记录保持请假状态，出差记录保持出差状态。
3. 更新考勤记录的状态与备注。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_160_000 | 考勤记录不存在 |
| 1_054_160_002 | 考勤类型与状态不匹配 |

### 2.2 删除考勤记录

- **路径**: DELETE /oa/attendance/delete
- **权限**: oa:attendance:delete
- **说明**: 删除指定考勤记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 考勤记录编号 |

**响应**: CommonResult&lt;Boolean&gt;（true 表示成功）

**业务逻辑**:
1. 校验考勤记录存在且属于当前操作用户的管理范围，否则按不存在处理。
2. 删除考勤记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_160_000 | 考勤记录不存在 |

### 2.3 获得考勤详情

- **路径**: GET /oa/attendance/get
- **权限**: oa:attendance:query
- **说明**: 获得指定考勤记录详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 考勤记录编号 |

**响应**: CommonResult&lt;OaAttendanceRespVO&gt;，字段同 1.2 响应。

**业务逻辑**:
1. 校验考勤记录存在且属于当前操作用户的管理范围，否则按不存在处理。
2. 查询记录并拼装用户昵称与部门名称后返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_160_000 | 考勤记录不存在 |

### 2.4 获得考勤分页列表

- **路径**: GET /oa/attendance/page
- **权限**: oa:attendance:query
- **说明**: 分页查询当前操作用户管理范围（下属员工）内的考勤记录。

**请求参数 (OaAttendancePageReqVO)**: 同 1.2 请求参数。

**响应**: CommonResult&lt;PageResult&lt;OaAttendanceRespVO&gt;&gt;，字段同 1.2 响应。

**业务逻辑**:
1. 查询当前操作用户的下属用户列表，与请求中的 userId 筛选取交集，得到可见用户范围；范围为空直接返回空分页。
2. 在可见用户范围内按筛选条件分页查询考勤记录。
3. Controller 批量拼装用户昵称与部门名称后返回。

**错误码**: 无专属错误码。

## 3. 考勤报表

### 3.1 获得考勤周报

- **路径**: GET /oa/attendance/week-report
- **权限**: oa:attendance:query
- **说明**: 按周输出管理范围内每位用户 7 天的每日打卡明细（上班/下班记录编号、时间、状态）。

**请求参数 (OaAttendanceWeekReportReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| startDate | LocalDate | 是 | @NotNull/@DateTimeFormat(iso=DATE) | 周开始日期，自动归一到所在周的周一 |
| userId | Long | 否 | 无 | 用户编号，不传时查询全部下属 |

**响应**: CommonResult&lt;List&lt;OaAttendanceWeekReportRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| userName | String | 用户昵称（来自 system 用户） |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称（来自 system 部门） |
| dailyAttendances | List&lt;DailyAttendance&gt; | 每日考勤列表，固定 7 天 |
| dailyAttendances[].date | LocalDate | 日期 |
| dailyAttendances[].clockInId | Long | 上班考勤记录编号 |
| dailyAttendances[].clockInTime | LocalDateTime | 上班打卡时间 |
| dailyAttendances[].clockInStatus | Integer | 上班打卡状态 |
| dailyAttendances[].clockOutId | Long | 下班考勤记录编号 |
| dailyAttendances[].clockOutTime | LocalDateTime | 下班打卡时间 |
| dailyAttendances[].clockOutStatus | Integer | 下班打卡状态 |

**业务逻辑**:
1. 查询当前操作用户的下属用户列表，与请求中的 userId 筛选取交集；范围为空返回空列表，无打卡记录的用户也保留在结果中。
2. 将传入的开始日期归一到所在周的周一，计算周一至周日 7 天的时间范围，批量查询范围内的考勤记录。
3. 按用户、按日期分组，为每位用户构建 7 天的每日明细：取当天的上班记录与下班记录，填充记录编号、打卡时间与状态。
4. Controller 批量拼装用户昵称与部门名称后返回。

**错误码**: 无专属错误码。

### 3.2 获得考勤月报

- **路径**: GET /oa/attendance/month-report
- **权限**: oa:attendance:query
- **说明**: 按月汇总管理范围内每位用户的打卡次数、正常/迟到/早退次数以及请假、出差、旷工天数。

**请求参数 (OaAttendanceMonthReportReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| year | Integer | 是 | @NotNull/@Min(2000) | 年份 |
| month | Integer | 是 | @NotNull/@Min(1)/@Max(12) | 月份 |
| userId | Long | 否 | 无 | 用户编号，不传时查询全部下属 |

**响应**: CommonResult&lt;List&lt;OaAttendanceMonthReportRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| userName | String | 用户昵称（来自 system 用户） |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称（来自 system 部门） |
| clockInCount | Integer | 上班打卡次数 |
| clockOutCount | Integer | 下班打卡次数 |
| normalCount | Integer | 正常次数 |
| lateCount | Integer | 迟到次数 |
| earlyCount | Integer | 早退次数 |
| leaveDays | Integer | 请假天数，审批通过且开始时间在当月的申请天数合计 |
| travelDays | Integer | 出差天数，审批通过且开始时间在当月的申请天数合计 |
| absentDays | Integer | 旷工天数，仅统计过去月份（应出勤天数 - 下班打卡次数），当月为 0 |

**业务逻辑**:
1. 查询当前操作用户的下属用户列表，与请求中的 userId 筛选取交集；范围为空返回空列表，无记录用户也保留。
2. 计算指定月份的起止时间，批量查询该月考勤记录；同时批量汇总审批通过的请假天数与出差天数（整笔申请归入其开始时间所在月份）。
3. 按用户汇总：统计上班/下班打卡次数，以及正常、迟到、早退状态的记录数。
4. 请假天数、出差天数分别取自请假、出差申请服务的审批通过汇总结果。
5. 旷工天数仅对已过去的月份计算，等于配置的月报应出勤天数（默认 22）减去下班打卡次数，当月不计算旷工。
6. Controller 批量拼装用户昵称与部门名称后返回。

**错误码**: 无专属错误码。

## 补充说明

- **考勤记录来源**：除打卡接口外，请假、出差审批通过后由 `OaLeaveApplyService`、`OaTravelApplyService` 调用内部方法 `createApplyAttendance` 自动写入类型为请假/出差的考勤记录（沿用申请开始时间），不产生打卡次数。
- **打卡时间窗口与状态判定参数** 来自 OA 模块配置 `OaProperties.Attendance`：每日最早打卡时间（默认 05:00）、标准上班时间（默认 08:00）、标准下班时间（默认 17:00，同时是打卡截止时间）、月报应出勤天数（默认 22）。
- **数据范围控制**：管理端查询、修改、删除均以当前登录用户的下属员工列表（`AdminUserApi#getUserListBySubordinate`）为可见范围，越界记录与不存在记录统一返回"考勤记录不存在"，防止横向越权。
