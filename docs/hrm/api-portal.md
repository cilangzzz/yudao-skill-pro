# 员工自助门户接口 (HrmPortal*Controller)

> 提供员工自助门户（员工端）能力：首页日历、我的员工档案与档案字段配置、联系人/离职信息/证书/教育/培训/工作经历查询、考勤打卡与请假、月度考勤统计与导出、工资条查询与已读标记、社保记录查询、绩效考核全流程（指标填写、目标确认、评分、结果审核、结果确认、申诉）处理。

## 接口路径前缀

- /hrm/portal/home  (Controller: HrmPortalHomeController)
- /hrm/portal/employee  (Controller: HrmPortalEmployeeController)
- /hrm/portal/employee/field-config  (Controller: HrmPortalEmployeeFieldConfigController)
- /hrm/portal/employee/contact  (Controller: HrmPortalEmployeeContactController)
- /hrm/portal/employee/quit-info  (Controller: HrmPortalEmployeeQuitInfoController)
- /hrm/portal/employee/certificate  (Controller: HrmPortalEmployeeCertificateController)
- /hrm/portal/employee/education-experience  (Controller: HrmPortalEmployeeEducationExperienceController)
- /hrm/portal/employee/training-experience  (Controller: HrmPortalEmployeeTrainingExperienceController)
- /hrm/portal/employee/work-experience  (Controller: HrmPortalEmployeeWorkExperienceController)
- /hrm/portal/attendance/clock  (Controller: HrmPortalAttendanceClockController)
- /hrm/portal/attendance/leave  (Controller: HrmPortalAttendanceLeaveController)
- /hrm/portal/attendance/statistics  (Controller: HrmPortalAttendanceStatisticsController)
- /hrm/portal/salary/slip  (Controller: HrmPortalSalarySlipController)
- /hrm/portal/insurance/record  (Controller: HrmPortalInsuranceController)
- /hrm/portal/performance/assessment  (Controller: HrmPortalPerformanceAssessmentController)

> 所有接口均以当前登录账号（getLoginUserId）为视角，绝大多数查询类接口权限为 `hrm:portal:query`，档案更新为 `hrm:portal:employee:update`，请假提交/取消与绩效操作分别使用 `hrm:portal:attendance:leave`、`hrm:portal:performance:action`。

---

## 1. 首页日历（HrmPortalHomeController）

### 1.1 获得员工端首页日历

- **路径**: GET /hrm/portal/home/calendar
- **权限**: hrm:portal:query
- **说明**: 返回当前员工在指定日期范围内的日历事项（个人备忘、考勤打卡）

**请求参数**（Query 参数，无独立 ReqVO 类）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| startDate | LocalDate | 是 | @DateTimeFormat(iso = DATE) | 开始日期，如 2026-08-01 |
| endDate | LocalDate | 是 | @DateTimeFormat(iso = DATE) | 结束日期，如 2026-08-31 |

**响应**: CommonResult&lt;List&lt;HrmHomeCalendarItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| personalNoteId | Long | 员工个人备忘编号（仅备忘事项有值） |
| type | Integer | 事项类型 |
| typeName | String | 事项类型名称 |
| content | String | 事项内容 |
| typeId | Long | 关联业务编号（员工编号，备忘为 null） |
| date | LocalDate | 事项日期 |
| eventTime | LocalDateTime | 事项时间 |

**业务逻辑**:
1. 校验日期范围：startDate/endDate 非空、endDate 不早于 startDate、跨度不超过 370 天，否则抛出 `HOME_CALENDAR_DATE_RANGE_ILLEGAL`
2. 查询当前登录账号绑定的员工，收集日期范围内的个人备忘事项（按提醒时间生成）
3. 收集本人考勤事项：查询日期范围内的打卡记录，按打卡日期去重并有序生成"考勤打卡"事项
4. 按事项时间、类型、内容稳定排序后返回

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_900_001 | HRM 首页日期范围不合法 |

---

## 2. 我的员工档案（HrmPortalEmployeeController / HrmPortalEmployeeFieldConfigController）

### 2.1 获得当前账号的员工绑定状态

- **路径**: GET /hrm/portal/employee/get-bind-status
- **权限**: hrm:portal:query
- **说明**: 判断当前登录账号是否已绑定员工档案

**请求参数**: 无

**响应**: CommonResult&lt;Boolean&gt;（true 表示已绑定）

**业务逻辑**:
1. 按当前登录用户编号查询员工档案
2. 返回是否存在绑定记录（不校验、不抛错）

### 2.2 获得我的员工档案

- **路径**: GET /hrm/portal/employee/get
- **权限**: hrm:portal:query
- **说明**: 获得当前登录员工的档案详情，含年龄/司龄/入职天数等计算字段，并按字段配置隐藏不可见字段

**请求参数**: 无

**响应**: CommonResult&lt;HrmPortalEmployeeRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 员工档案编号 |
| name | String | 员工姓名（不可见时为 null） |
| avatar | String | 员工头像（来自后台用户） |
| jobNumber | String | 工号 |
| mobile | String | 手机号（不可见时为 null） |
| country | String | 国家或地区（不可见时为 null） |
| nation | String | 民族（不可见时为 null） |
| idType | Integer | 证件类型（不可见时为 null） |
| idNumber | String | 证件号码（不可见时为 null） |
| sex | Integer | 性别（不可见时为 null） |
| email | String | 邮箱（不可见时为 null） |
| nativePlace | String | 籍贯（不可见时为 null） |
| birthday | LocalDateTime | 出生日期（不可见时为 null） |
| age | Integer | 年龄（不可见时为 null） |
| address | String | 户籍地址（不可见时为 null） |
| highestEducation | Integer | 最高学历（不可见时为 null） |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| leaderEmployeeId | Long | 直属上级员工编号 |
| leaderEmployeeName | String | 直属上级员工姓名 |
| entryStatus | Integer | 入职状态 |
| status | Integer | 员工状态 |
| type | Integer | 聘用形式 |
| entryTime | LocalDateTime | 入职时间 |
| entryDay | Long | 入职天数（入职时间至今天数 + 1，最小 0） |
| probation | Integer | 试用期（月，0 表示无试用期） |
| regularTime | LocalDateTime | 转正时间 |
| leaveTime | LocalDateTime | 离职时间 |
| postName | String | 职位名称 |
| postLevel | String | 岗位职级 |
| workCity | String | 工作城市 |
| workAddress | String | 工作地点 |
| workDetailAddress | String | 工作详细地址 |
| companyAgeStartTime | LocalDateTime | 司龄开始时间 |
| companyAge | Integer | 司龄（年） |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案，未绑定抛出 `EMPLOYEE_NOT_EXISTS`
2. 转换为响应 VO 并计算：年龄（出生日期至今整年数）、司龄（司龄开始时间至今整年数）、入职天数（入职时间至今天数 + 1，最小 0）
3. 经 AdminUserApi 拼接头像、DeptApi 拼接部门名称，查询直属上级员工姓名
4. 按档案字段配置的可见字段集合，将姓名/国家/民族/证件类型/证件号码/性别/籍贯/出生日期/年龄/最高学历/手机号/邮箱/户籍地址中不可见的字段置为 null

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |

### 2.3 更新我的员工档案

- **路径**: PUT /hrm/portal/employee/update
- **权限**: hrm:portal:employee:update
- **说明**: 员工自助修改个人档案信息，仅允许更新字段配置中"允许员工编辑"的字段

**请求参数 (HrmPortalEmployeeUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| name | String | 否 | @Size(max = 255) | 员工姓名 |
| mobile | String | 否 | @Mobile | 手机号 |
| country | String | 否 | @Size(max = 64) | 国家或地区 |
| nation | String | 否 | @Size(max = 64) | 民族 |
| idType | Integer | 否 | @InEnum(HrmEmployeeIdTypeEnum) | 证件类型 |
| idNumber | String | 否 | @Size(max = 255)；@AssertTrue 校验身份证格式 | 证件号码（证件类型为身份证时校验合法性） |
| sex | Integer | 否 | - | 性别 |
| email | String | 否 | @Email、@Size(max = 255) | 邮箱 |
| nativePlace | String | 否 | @Size(max = 128) | 籍贯 |
| birthday | LocalDateTime | 否 | @PastOrPresent | 出生日期（不能晚于当前时间） |
| address | String | 否 | @Size(max = 255) | 户籍地址 |
| highestEducation | Integer | 否 | @InEnum(HrmEmployeeEducationEnum) | 最高学历 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 读取"允许员工编辑"的档案字段白名单；白名单为空时直接返回
3. 姓名在白名单内但提交为空时抛出 `EMPLOYEE_PROFILE_FIELD_REQUIRED`；手机号非空时校验唯一性，重复抛出 `EMPLOYEE_MOBILE_DUPLICATE`
4. 按字段白名单构造更新对象，不在白名单内的字段保留数据库原值
5. 证件类型/证件号码可编辑时联动更新出生日期；出生日期更新时联动更新年龄
6. 更新员工档案，并记录操作日志（记录变更前后对象）

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_003 | 手机号已绑定员工档案 |
| 1_050_100_035 | 员工档案字段【{}】不能为空 |

### 2.4 获得我的员工档案字段配置

- **路径**: GET /hrm/portal/employee/field-config/list
- **权限**: hrm:portal:query
- **说明**: 获得员工档案各字段的显示/编辑配置，用于员工端档案页渲染

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmEmployeeFieldConfigRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| name | String | 字段名称（如 name） |
| title | String | 字段标题（如 员工姓名） |
| groupName | String | 字段分组名称（如 基本信息） |
| visible | Boolean | 是否显示 |
| editable | Boolean | 是否允许员工编辑 |
| visibleLocked | Boolean | 是否锁定显示 |
| editableLocked | Boolean | 是否锁定编辑 |

**业务逻辑**:
1. 读取员工档案字段配置（HRM 配置项）
2. 枚举全部档案字段：无配置时取字段的默认显示/默认可编辑值
3. 字段不显示或编辑被锁定时，强制置为不可编辑
4. 返回字段名、标题、分组及显示/编辑标记

---

## 3. 我的档案明细（联系人 / 离职信息 / 证书 / 教育 / 培训 / 工作经历）

> 本组 6 个控制器均为只读查询，模式一致：先校验当前登录账号已绑定员工档案，再按员工编号查询列表/详情并转换 VO。权限均为 hrm:portal:query，均无请求参数。

### 3.1 获得我的联系人列表

- **路径**: GET /hrm/portal/employee/contact/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的联系人列表

**响应**: CommonResult&lt;List&lt;HrmEmployeeContactRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 联系人编号 |
| employeeId | Long | 员工编号 |
| name | String | 联系人名称 |
| relation | String | 关系 |
| phone | String | 联系人电话 |
| workUnit | String | 联系人工作单位 |
| postName | String | 联系人职务 |
| address | String | 联系人地址 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

### 3.2 获得我的离职信息

- **路径**: GET /hrm/portal/employee/quit-info/get
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的离职信息

**响应**: CommonResult&lt;HrmEmployeeQuitInfoRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 离职信息编号 |
| employeeId | Long | 员工编号 |
| planQuitTime | LocalDateTime | 计划离职时间 |
| applyQuitTime | LocalDateTime | 申请离职时间 |
| salarySettlementTime | LocalDateTime | 薪资结算时间 |
| type | Integer | 离职类型 |
| reason | Integer | 离职原因 |
| remark | String | 备注 |
| oldEmployeeStatus | Integer | 离职前员工状态 |
| createTime | LocalDateTime | 创建时间 |

### 3.3 获得我的证书列表

- **路径**: GET /hrm/portal/employee/certificate/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的证书列表

**响应**: CommonResult&lt;List&lt;HrmEmployeeCertificateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 证书编号 |
| employeeId | Long | 员工编号 |
| name | String | 证书名称 |
| level | String | 证书级别 |
| no | String | 证书编号（证件号） |
| startTime | LocalDateTime | 有效起始日期 |
| endTime | LocalDateTime | 有效结束日期 |
| issuingAuthority | String | 发证机构 |
| issuingTime | LocalDateTime | 发证日期 |
| remark | String | 备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

### 3.4 获得我的教育经历列表

- **路径**: GET /hrm/portal/employee/education-experience/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的教育经历列表

**响应**: CommonResult&lt;List&lt;HrmEmployeeEducationExperienceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 教育经历编号 |
| employeeId | Long | 员工编号 |
| education | Integer | 学历 |
| graduateSchool | String | 毕业院校 |
| major | String | 专业 |
| admissionTime | LocalDateTime | 入学日期 |
| graduationTime | LocalDateTime | 毕业日期 |
| teachingMethods | Integer | 教学方式 |
| firstDegree | Boolean | 是否第一学历 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

### 3.5 获得我的培训经历列表

- **路径**: GET /hrm/portal/employee/training-experience/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的培训经历列表

**响应**: CommonResult&lt;List&lt;HrmEmployeeTrainingExperienceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 培训经历编号 |
| employeeId | Long | 员工编号 |
| course | String | 培训课程 |
| organizationName | String | 培训机构名称 |
| startTime | LocalDateTime | 培训开始日期 |
| endTime | LocalDateTime | 培训结束日期 |
| duration | String | 培训时长 |
| result | String | 培训成绩 |
| certificateName | String | 培训证书名称 |
| remark | String | 备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

### 3.6 获得我的工作经历列表

- **路径**: GET /hrm/portal/employee/work-experience/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的工作经历列表

**响应**: CommonResult&lt;List&lt;HrmEmployeeWorkExperienceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 工作经历编号 |
| employeeId | Long | 员工编号 |
| workUnit | String | 工作单位 |
| postName | String | 职务 |
| startTime | LocalDateTime | 工作开始日期 |
| endTime | LocalDateTime | 工作结束日期 |
| reason | String | 离职原因 |
| witnessName | String | 证明人 |
| witnessPhone | String | 证明人手机号 |
| remark | String | 工作备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑（本组通用）**:
1. 校验当前登录账号已绑定员工档案（未绑定抛出 `EMPLOYEE_NOT_EXISTS`）
2. 按员工编号查询对应业务数据（列表查询按 employeeId 全量查询；离职信息为单条查询）
3. BeanUtils 转换为对应 RespVO 返回

---

## 4. 考勤打卡（HrmPortalAttendanceClockController）

### 4.1 获得我的打卡详情

- **路径**: GET /hrm/portal/attendance/clock/get-detail
- **权限**: hrm:portal:query
- **说明**: 手机端打卡页数据：考勤组、班次窗口、打卡点/WiFi、下一次可打卡动作与当日时间线

**请求参数**: 无

**响应**: CommonResult&lt;HrmPortalAttendanceClockDetailRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| groupName | String | 考勤组名称 |
| openPointCard | Boolean | 是否启用定位打卡 |
| openWifiCard | Boolean | 是否启用 WiFi 打卡 |
| attendanceDate | LocalDate | 班次所属考勤日 |
| shiftTitle | String | 班次标题（如 09:00-18:00，含休息时段；无班次为"休息"） |
| restDay | Boolean | 是否休息日 |
| onDutyAttendanceTime | LocalDateTime | 上班应打卡时间 |
| offDutyAttendanceTime | LocalDateTime | 下班应打卡时间 |
| points | List&lt;Point&gt; | 打卡地点列表（未启用定位打卡时为空列表） |
| wifis | List&lt;Wifi&gt; | WiFi 列表（未启用 WiFi 打卡时为空列表） |
| nextClock | NextClock | 下一次可打卡动作 |
| timeline | List&lt;TimelineItem&gt; | 当日打卡时间线 |

**Point（打卡地点）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| name | String | 地点名称 |
| address | String | 定位地址 |
| latitude | BigDecimal | 纬度 |
| longitude | BigDecimal | 经度 |
| radius | Integer | 有效半径（米） |

**Wifi**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| ssid | String | WiFi 名称 |
| mac | String | MAC 地址 |

**NextClock（下一次打卡动作）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| type | Integer | 打卡类型 |
| stage | Integer | 打卡阶段 |
| attendanceTime | LocalDateTime | 应打卡时间 |
| buttonStatus | Integer | 按钮状态：0 未到时间、1 正常、2 更新、3 迟到、4 早退 |

**TimelineItem（当日打卡时间线条目）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| type | Integer | 打卡类型 |
| attendanceTime | LocalDateTime | 应打卡时间 |
| clockTime | LocalDateTime | 实际打卡时间（缺卡时为空） |
| status | Integer | 打卡状态 |
| missCard | Boolean | 是否缺卡 |
| address | String | 打卡地址 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案，并匹配其考勤组；未匹配到考勤组抛出 `ATTENDANCE_CLOCK_GROUP_NOT_EXISTS`
2. 按当前时间解析班次所属考勤日与上/下班应打卡时间窗口
3. 查询当日打卡记录，计算下一次可打卡动作（打卡类型、阶段、应打卡时间、按钮状态）
4. 构建当日打卡时间线（每次应打卡及实际打卡情况、是否缺卡）
5. Controller 拼接：考勤组名称、定位/WiFi 开关、班次标题（HH:mm-HH:mm，存在休息时段时追加"休息:HH:mm-HH:mm"，无班次显示"休息"）、打卡地点列表与 WiFi 列表（按开关决定是否返回）

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_300_038 | 未匹配到考勤组，无法打卡 |

### 4.2 手机端打卡

- **路径**: POST /hrm/portal/attendance/clock/create
- **权限**: hrm:portal:query
- **说明**: 员工手机端提交打卡，写入一条来源为手机端的打卡记录

**请求参数 (HrmPortalAttendanceClockCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| address | String | 否 | @Size(max = 255) | 打卡地址 |
| longitude | BigDecimal | 否 | @DecimalMin(-180)、@DecimalMax(180) | 经度 |
| latitude | BigDecimal | 否 | @DecimalMin(-90)、@DecimalMax(90) | 纬度 |
| ssid | String | 否 | @Size(max = 50) | WiFi 名称 |
| mac | String | 否 | @Size(max = 50) | WiFi MAC 地址 |

**响应**: CommonResult&lt;Long&gt;（打卡记录编号）

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案并匹配考勤组；未匹配抛出 `ATTENDANCE_CLOCK_GROUP_NOT_EXISTS`
2. 按当前时间解析班次与下一步打卡动作；当日无班次抛出 `ATTENDANCE_CLOCK_REST_DAY`
3. 下一步动作的按钮状态不可打卡（未到时间等）时抛出 `ATTENDANCE_CLOCK_NOT_ALLOWED`
4. 按考勤组开关校验定位：启用定位打卡时校验经纬度在打卡点有效半径内，否则抛出 `ATTENDANCE_CLOCK_POINT_INVALID`；启用 WiFi 打卡时校验 ssid/mac 匹配，否则抛出 `ATTENDANCE_CLOCK_WIFI_INVALID`
5. 写入打卡记录：员工编号、打卡类型与应打卡时间取自下一步动作、实际打卡时间为当前时间，并保存地址/经纬度/WiFi 信息，来源标记为手机端（MOBILE）

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_300_034 | 今日休息，无需打卡 |
| 1_050_300_035 | 当前不在可打卡时间 |
| 1_050_300_036 | 不在考勤打卡范围内 |
| 1_050_300_037 | 未连接指定的考勤 WiFi |
| 1_050_300_038 | 未匹配到考勤组，无法打卡 |

### 4.3 获得我的考勤记录

- **路径**: GET /hrm/portal/attendance/clock/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工指定月份的打卡记录列表（默认当月）

**请求参数**（Query 参数，无独立 ReqVO 类）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| year | Integer | 否 | - | 年份，如 2026 |
| month | Integer | 否 | - | 月份，如 8 |

**响应**: CommonResult&lt;List&lt;HrmPortalAttendanceRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| employeeId | Long | 员工编号 |
| clockTime | LocalDateTime | 打卡时间 |
| type | Integer | 员工端考勤记录类型（上班/下班打卡） |
| attendanceTime | LocalDateTime | 应打卡时间 |
| sourceType | Integer | 来源类型（手机端/手工录入等） |
| status | Integer | 员工端考勤记录状态（正常/迟到/早退等） |
| stage | Integer | 阶段 |
| address | String | 地址 |
| longitude | BigDecimal | 经度 |
| latitude | BigDecimal | 纬度 |
| ssid | String | WiFi 名称 |
| mac | String | WiFi MAC 地址 |
| remark | String | 备注 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. year/month 未传时取当前月份，计算所选月份的起止时间闭区间
3. 查询该员工在所选月份内的全部打卡记录并转换返回

---

## 5. 考勤请假（HrmPortalAttendanceLeaveController）

### 5.1 获得我的请假申请列表

- **路径**: GET /hrm/portal/attendance/leave/list
- **权限**: hrm:portal:query
- **说明**: 获得当前员工的全部请假申请列表

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmAttendanceLeaveRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 请假记录编号 |
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| type | String | 请假类型（字典 HRM_ATTENDANCE_LEAVE_TYPE） |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| day | BigDecimal | 请假天数 |
| reason | String | 请假事由 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| approvalStatus | Integer | 审批状态（BPM 流程实例状态） |
| processInstanceId | String | 流程实例编号 |
| approvalTime | LocalDateTime | 审批时间 |
| approvalReason | String | 审批意见 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 按员工编号查询全部请假申请并转换返回

### 5.2 创建我的请假申请

- **路径**: POST /hrm/portal/attendance/leave/create
- **权限**: hrm:portal:attendance:leave
- **说明**: 提交请假申请并发起 BPM 审批流程

**请求参数 (HrmAttendanceLeaveCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| type | String | 是 | @NotBlank、@Size(max = 64) | 请假类型 |
| startTime | LocalDateTime | 是 | @NotNull | 请假开始时间 |
| endTime | LocalDateTime | 是 | @NotNull；@AssertTrue 校验晚于开始时间 | 请假结束时间 |
| day | BigDecimal | 是 | @NotNull、@DecimalMin(0.01)、@Digits(整数 8 位, 小数 2 位) | 请假天数 |
| reason | String | 是 | @NotBlank、@Size(max = 300) | 请假事由 |
| remark | String | 否 | @Size(max = 500) | 备注 |

**响应**: CommonResult&lt;Long&gt;（请假记录编号）

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 锁定员工记录，避免同一员工并发创建重叠请假
3. 校验请假时间不与审批中、已通过的申请重叠，重叠抛出 `ATTENDANCE_LEAVE_TIME_CONFLICT`
4. 创建审批状态为"审批中（RUNNING）"的请假记录
5. 构建流程变量（员工部门/编号/姓名、请假类型、起止时间、天数、事由）并发起 BPM 请假审批流程，回写流程实例编号

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_300_031 | 请假时间与已有申请重叠 |

### 5.3 取消我的请假申请

- **路径**: PUT /hrm/portal/attendance/leave/cancel
- **权限**: hrm:portal:attendance:leave
- **说明**: 取消本人审批中的请假申请，同时取消 BPM 审批流程

**请求参数 (HrmAttendanceLeaveCancelReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 请假记录编号 |
| reason | String | 是 | @NotBlank、@Size(max = 500) | 取消原因 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案，请假记录存在且属于本人（否则抛出 `ATTENDANCE_LEAVE_NOT_EXISTS`）
2. 校验申请处于审批中且已关联流程实例，否则抛出 `ATTENDANCE_LEAVE_STATUS_INVALID`
3. 以当前用户身份取消 BPM 流程实例（附取消原因），并将请假审批状态更新为"已取消"

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_300_030 | 请假申请不存在 |
| 1_050_300_032 | 只有审批中的请假申请可以取消 |

---

## 6. 考勤统计（HrmPortalAttendanceStatisticsController）

### 6.1 获得我的月度考勤详情

- **路径**: GET /hrm/portal/attendance/statistics/month-detail
- **权限**: hrm:portal:query
- **说明**: 获得当前员工指定月份的考勤汇总、每日打卡明细与请假记录

**请求参数**（Query 参数，无独立 ReqVO 类）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| year | Integer | 否 | - | 年份，缺省取当前年 |
| month | Integer | 否 | - | 月份，缺省取当前月 |

**响应**: CommonResult&lt;HrmAttendanceMonthDetailRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| summary | HrmAttendanceMonthRecordRespVO | 月度汇总（应出勤/实际出勤天数、迟到/早退/缺卡次数与时长、旷工天数、请假天数、各类扣款与考勤扣款合计、是否全勤等） |
| dailyDetails | List&lt;HrmAttendanceDailyDetailRespVO&gt; | 每日打卡明细 |
| leaves | List&lt;HrmAttendanceLeaveRespVO&gt; | 当月请假记录 |

**HrmAttendanceDailyDetailRespVO（每日明细，同时为 Excel 导出列）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| attendanceTime | LocalDateTime | 日期 |
| shiftName | String | 班次 |
| scheduled | Boolean | 是否排班 |
| requiredClockCount | Integer | 应打卡次数 |
| scheduledMinutes | Integer | 排班分钟数 |
| misscardCount | Integer | 缺卡次数 |
| absenteeism | Boolean | 是否旷工 |
| absenteeismMinutes | Integer | 旷工分钟数 |
| absenteeismDays | BigDecimal | 旷工天数 |
| leaveStatus | Boolean | 是否请假 |
| leaveMinutes | Integer | 请假分钟数 |
| leaveDays | BigDecimal | 请假天数 |
| attendanceResult | String | 考勤结果 |
| clockCount | Integer | 打卡次数 |
| lateCount | Integer | 迟到次数 |
| lateMinutes | Integer | 迟到分钟 |
| earlyCount | Integer | 早退次数 |
| earlyMinutes | Integer | 早退分钟 |
| clockList | List&lt;HrmAttendanceClockRespVO&gt; | 打卡列表 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. year/month 未传时取当前月份
3. 查询员工当月的考勤关联数据（排班、打卡、请假等）
4. 拼接月度汇总（含各类考勤结果与扣款统计）
5. 过滤与所选月份存在闭区间重叠的请假记录并拼接员工信息

### 6.2 导出我的月度考勤日报

- **路径**: GET /hrm/portal/attendance/statistics/export-excel
- **权限**: hrm:portal:query
- **说明**: 按月导出当前员工的个人考勤日报 Excel（以每日明细为行）

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| year | Integer | 是 | - | 年份 |
| month | Integer | 是 | - | 月份 |

**响应**: Excel 文件下载（文件名"{year}年{month}月个人考勤日报.xls"，sheet"考勤日报"）

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 查询该员工指定月份的月度考勤详情
3. 以每日明细列表（HrmAttendanceDailyDetailRespVO）为数据源写出 Excel 响应

---

## 7. 我的工资条（HrmPortalSalarySlipController）

### 7.1 获得我的未读工资条概况

- **路径**: GET /hrm/portal/salary/slip/unread-summary
- **权限**: hrm:portal:query
- **说明**: 返回未读工资条数量及最新一条未读工资条的提醒文案

**请求参数**: 无

**响应**: CommonResult&lt;HrmPortalSalarySlipUnreadSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| unreadCount | Long | 未读工资条数量 |
| reminder | String | 最新未读工资条提醒（如"张三更新了您8月的工资条，前往查看"；无未读时为 null） |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 查询本人全部工资条，过滤出未读（UNREAD）状态的记录
3. 取最新一条未读工资条构建提醒：发布人优先取创建人对应后台用户昵称（创建人编号无法解析或为空时显示"HR"），拼接"更新了您{month}月的工资条，前往查看"

### 7.2 获得我的工资条列表

- **路径**: GET /hrm/portal/salary/slip/list
- **权限**: hrm:portal:query
- **说明**: 按月份范围与排序条件查询本人工资条列表

**请求参数 (HrmPortalSalarySlipListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| startMonth | String | 否 | @Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 开始月份，格式 yyyy-MM |
| endMonth | String | 否 | @Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 结束月份，格式 yyyy-MM |
| orderType | Integer | 否 | @Range(min = 1, max = 2) | 排序类型（1/2） |
| order | Integer | 否 | @Range(min = 1, max = 2) | 排序方向（1/2） |

**响应**: CommonResult&lt;List&lt;HrmPortalSalarySlipRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| sendRecordId | Long | 工资条发放记录编号 |
| monthEmployeeRecordId | Long | 员工月度工资记录编号 |
| employeeId | Long | 员工编号 |
| year | Integer | 年份 |
| month | Integer | 月份 |
| readStatus | Integer | 已读状态 |
| realPaySalary | BigDecimal | 实发工资 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| options | List&lt;HrmPortalSalarySlipOptionRespVO&gt; | 工资条选项列表（薪资项明细） |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 解析开始/结束月份（未传则不限制该边界）
3. 按员工编号、月份范围与排序条件查询工资条列表并转换返回

### 7.3 获得我的工资条详情

- **路径**: GET /hrm/portal/salary/slip/get
- **权限**: hrm:portal:query
- **说明**: 获得单条工资条详情，仅允许查看本人工资条

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | - | 工资条编号 |

**响应**: CommonResult&lt;HrmPortalSalarySlipRespVO&gt;（字段同 7.2）

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 按工资条编号 + 员工编号查询，校验工资条归属本人（否则抛出 `SALARY_SLIP_NOT_EXISTS`）
3. 转换为响应 VO 返回

### 7.4 标记我的工资条为已读

- **路径**: PUT /hrm/portal/salary/slip/read
- **权限**: hrm:portal:query
- **说明**: 批量将本人工资条标记为已读

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| ids | List&lt;Long&gt; | 是 | @NotEmpty（"工资条编号列表不能为空"） | 工资条编号列表，如 1024,1025 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 去重后校验工资条全部存在且均属于本人，否则抛出 `SALARY_SLIP_NOT_EXISTS`
3. 批量更新这批工资条的阅读状态为已读

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_400_013 | 工资条不存在 |

---

## 8. 我的社保（HrmPortalInsuranceController）

### 8.1 获得我的社保记录

- **路径**: GET /hrm/portal/insurance/record/list
- **权限**: hrm:portal:query
- **说明**: 按年份查询本人月度社保记录（不含项目明细）

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| year | Integer | 否 | - | 年份，如 2026；不传查全部 |

**响应**: CommonResult&lt;List&lt;HrmPortalInsuranceRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| monthRecordId | Long | 月度社保记录编号 |
| employeeId | Long | 员工编号 |
| schemeId | Long | 社保方案编号 |
| schemeName | String | 社保方案名称 |
| schemeType | Integer | 社保方案类型 |
| schemeCity | String | 参保城市 |
| year | Integer | 年份 |
| month | Integer | 月份 |
| personalInsuranceAmount | BigDecimal | 个人社保金额 |
| personalProvidentFundAmount | BigDecimal | 个人公积金金额 |
| corporateInsuranceAmount | BigDecimal | 公司社保金额 |
| corporateProvidentFundAmount | BigDecimal | 公司公积金金额 |
| status | Integer | 员工端社保记录状态 |
| createTime | LocalDateTime | 创建时间 |
| projects | List&lt;HrmPortalInsuranceProjectRespVO&gt; | 社保项目列表（列表接口恒为 null，仅详情返回） |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 按员工编号与年份查询月度员工社保记录
3. 批量查询涉及的社保方案，拼接方案名称、类型与参保城市（按方案地区格式化）
4. 列表模式不返回社保项目明细

### 8.2 获得我的社保记录详情

- **路径**: GET /hrm/portal/insurance/record/get
- **权限**: hrm:portal:query
- **说明**: 获得单条社保记录详情，含社保项目明细

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | - | 社保记录编号 |

**响应**: CommonResult&lt;HrmPortalInsuranceRecordRespVO&gt;（字段同 8.1，projects 返回明细）

**HrmPortalInsuranceProjectRespVO（社保项目）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| schemeProjectId | Long | 社保项目编号 |
| type | Integer | 社保项目类型 |
| name | String | 社保项目名称 |
| baseAmount | BigDecimal | 默认缴纳金额（基数） |
| corporateRate | BigDecimal | 公司缴纳比例 |
| personalRate | BigDecimal | 个人缴纳比例 |
| corporateAmount | BigDecimal | 公司缴纳金额 |
| personalAmount | BigDecimal | 个人缴纳金额 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 查询社保记录；记录不存在或不属于本人时抛出 `INSURANCE_MONTH_EMP_RECORD_NOT_EXISTS`
3. 查询关联社保方案并拼接方案名称、类型与参保城市，返回社保项目明细

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_500_006 | 员工月度社保记录不存在 |

---

## 9. 我的绩效考核（HrmPortalPerformanceAssessmentController）

> 绩效域端点较多，按"查询类"（权限 hrm:portal:query）与"操作类"（权限 hrm:portal:performance:action）两组说明。

### 9.1 获得我的绩效分页

- **路径**: GET /hrm/portal/performance/assessment/page
- **权限**: hrm:portal:query
- **说明**: 分页查询本人参与的绩效考核（按是否归档区分"我的绩效"与"历史绩效"页签）

**请求参数 (HrmPortalPerformanceAssessmentPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | PageParam 分页参数 | 页码 |
| pageSize | Integer | 否 | PageParam 分页参数 | 每页条数 |
| search | String | 否 | - | 绩效计划名称关键字 |
| archived | Boolean | 是 | @NotNull | 是否已归档 |

**响应**: CommonResult&lt;PageResult&lt;HrmPortalPerformanceAssessmentRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| planId | Long | 绩效计划编号 |
| name | String | 绩效计划名称 |
| status | Integer | 考核状态 |
| stageType | Integer | 阶段状态（当前所处流程阶段类型） |
| score | BigDecimal | 得分 |
| resultLevel | String | 结果等级 |
| coefficient | BigDecimal | 绩效系数 |
| resultAuditStatus | Integer | 结果审核状态 |
| resultAuditTime | LocalDateTime | 结果审核时间 |
| resultAuditReason | String | 结果审核意见 |
| appealReason | String | 申诉原因 |
| appealStatus | Integer | 申诉状态 |
| appealTime | LocalDateTime | 申诉处理时间 |
| appealComment | String | 申诉处理意见 |
| startTime | LocalDateTime | 开始日期 |
| endTime | LocalDateTime | 结束日期 |
| archiveTime | LocalDateTime | 归档时间 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 按员工编号 + 计划名称关键字 + 是否归档分页查询绩效考核
3. 复用管理端查询服务拼接绩效计划、维度、指标、阶段等信息
4. 转换为员工端响应 VO 分页返回

### 9.2 获得我的绩效任务数量

- **路径**: GET /hrm/portal/performance/assessment/task-count
- **权限**: hrm:portal:query
- **说明**: 一次性返回员工端各绩效待办页签的待处理/已处理数量

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| search | String | 否 | - | 员工姓名或工号 |

**响应**: CommonResult&lt;HrmPortalPerformanceTaskCountRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| fillPendingCount | Long | 待填写指标数量 |
| fillCompletedCount | Long | 已填写指标数量 |
| targetPendingCount | Long | 待确认目标数量 |
| targetCompletedCount | Long | 已确认目标数量 |
| reviewPendingCount | Long | 待评分数量 |
| reviewCompletedCount | Long | 已评分数量 |
| resultAuditPendingCount | Long | 待审核结果数量 |
| resultAuditCompletedCount | Long | 已审核结果数量 |
| resultConfirmationPendingCount | Long | 待确认结果数量 |
| resultConfirmationCompletedCount | Long | 已确认结果数量 |
| resultConfirmationAppealedCount | Long | 已申诉结果数量 |
| appealPendingCount | Long | 待处理申诉数量 |
| appealCompletedCount | Long | 已处理申诉数量 |

**业务逻辑**:
1. 校验当前登录账号已绑定员工档案
2. 按流程阶段类型 × 处理状态统计本人任务数量（支持按姓名/工号过滤）
3. 按待处理（PENDING）、已处理（PROCESSED）、已申诉（APPEALED）三种状态，组装指标填写/目标确认/评分/结果审核/结果确认/申诉处理六类页签的 13 项计数

### 9.3 获得我的绩效指标填写任务分页

- **路径**: GET /hrm/portal/performance/assessment/fill-quota-task-page
- **权限**: hrm:portal:query
- **说明**: 分页查询当前用户作为"指标填写"阶段处理人的任务

### 9.4 获得我的绩效目标确认任务分页

- **路径**: GET /hrm/portal/performance/assessment/target-confirmation-task-page
- **权限**: hrm:portal:query
- **说明**: 分页查询当前用户作为"目标确认"阶段处理人的任务

### 9.5 获得我的绩效评分任务分页

- **路径**: GET /hrm/portal/performance/assessment/review-task-page
- **权限**: hrm:portal:query
- **说明**: 分页查询当前用户作为"评分"（自评/他评等评分类型）阶段处理人的任务

### 9.6 获得我的绩效结果审核任务分页

- **路径**: GET /hrm/portal/performance/assessment/result-audit-task-page
- **权限**: hrm:portal:query
- **说明**: 分页查询当前用户作为"结果审核"阶段处理人的任务

### 9.7 获得我的绩效结果确认任务分页

- **路径**: GET /hrm/portal/performance/assessment/result-confirmation-task-page
- **权限**: hrm:portal:query
- **说明**: 分页查询当前用户作为"结果确认"阶段处理人的任务

### 9.8 获得我的绩效申诉处理任务分页

- **路径**: GET /hrm/portal/performance/assessment/appeal-task-page
- **权限**: hrm:portal:query
- **说明**: 分页查询当前用户作为"申诉处理"阶段处理人的任务

**9.3 ~ 9.8 请求参数 (HrmPortalPerformanceTaskPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | PageParam 分页参数 | 页码 |
| pageSize | Integer | 否 | PageParam 分页参数 | 每页条数 |
| search | String | 否 | - | 绩效计划名称、员工姓名或工号 |
| stageStatus | Integer | 是 | @NotNull、@InEnum(HrmPerformanceAssessmentStageStatusEnum) | 阶段处理状态（待处理/已处理等） |

**9.3 ~ 9.8 响应**: CommonResult&lt;PageResult&lt;HrmPerformanceAssessmentRespVO&gt;&gt;（管理端绩效员工 VO，任务视角拼接）

主要字段：

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| planId / name | Long / String | 绩效计划编号 / 名称 |
| cycleType / cycle | Integer / String | 考核周期类型 / 周期 |
| startTime / endTime | LocalDateTime | 考核开始 / 结束日期 |
| upperLimitScore | BigDecimal | 单项评分上限 |
| employeeId / employeeName / jobNumber / mobile | - | 被考核员工信息 |
| deptId / deptName / postName / employeeType / employeeStatus | - | 员工部门、职位、聘用形式与状态 |
| currentHandlerName | String | 当前处理人 |
| status / processStatus | Integer | 考核状态 / 激活状态 |
| stageType / stageSort | Integer | 阶段状态 / 阶段排序 |
| score / resultLevel / coefficient | BigDecimal / String / BigDecimal | 得分、结果等级、绩效系数 |
| targetConfirmationEmployeeName / targetConfirmationResult / targetConfirmationComment / targetConfirmationTime / canConfirmTarget | - | 目标确认人、结果、意见、时间与是否可确认 |
| selfComment / reviewerComment / resultComment / resultConfirmationTime | - | 自评说明、评分人说明、结果说明与结果确认时间 |
| resultAuditStatus / resultAuditTime / resultAuditReason | - | 结果审核状态、时间与意见 |
| appealReason / appealFileUrls / appealReviewStageIds / appealSubmitTime / appealStatus / appealTime / appealComment | - | 申诉原因、附件、退回评分阶段、提交时间、状态与处理结果 |
| archiveTime / createTime | LocalDateTime | 归档时间 / 创建时间 |
| dimensions | List | 指标维度列表 |
| quotas | List | 指标列表 |
| reviewStages / currentReviewStage | List / Object | 评分阶段列表 / 当前评分阶段 |
| stages / currentStage | List / Object | 运行阶段列表 / 当前待处理阶段 |

**9.3 ~ 9.8 业务逻辑（通用）**:
1. 根据当前登录账号查询员工，未绑定时返回空分页
2. 按阶段类型（指标填写 / 目标确认 / 评分类型集合 / 结果审核 / 结果确认 / 申诉处理）与阶段处理状态，分页查询处理人为本人的绩效考核阶段
3. 批量加载阶段关联的绩效考核，过滤已不存在的考核记录
4. 按任务顺序拼接考核详情（含指标、阶段与当前任务上下文、可操作标记）返回

### 9.9 获得我的员工绩效考核明细

- **路径**: GET /hrm/portal/performance/assessment/get
- **权限**: hrm:portal:query
- **说明**: 查看绩效考核明细；带 stageId 时返回任务视角（供阶段处理人操作），否则返回流程视角（仅本人考核）

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | - | 员工绩效考核编号 |
| stageId | Long | 否 | - | 运行阶段编号（任务视角必传） |

**响应**: CommonResult&lt;HrmPerformanceAssessmentRespVO&gt;（结构同 9.3 ~ 9.8）

**业务逻辑**:
1. stageId 为空时：校验当前登录账号绑定的员工是该考核的被考核人（否则抛出 `PERFORMANCE_ASSESSMENT_NOT_EXISTS`）
2. stageId 非空时：校验阶段存在且属于该考核（否则 `PERFORMANCE_STAGE_ACTION_INVALID`），并校验当前账号绑定员工是该阶段处理人（否则 `PERFORMANCE_STAGE_NO_PERMISSION`）
3. stageId 非空返回任务视角明细（含当前任务可操作信息）；为空返回流程视角明细（含指标、评分阶段与运行阶段）

### 9.10 获得我的绩效流程记录

- **路径**: GET /hrm/portal/performance/assessment/process-record-list
- **权限**: hrm:portal:query
- **说明**: 获得绩效考核的流程处理记录（时间线），按查看者身份过滤可见性

**请求参数**（Query 参数）: 同 9.9（id 必填、stageId 可选）

**响应**: CommonResult&lt;List&lt;HrmPerformanceProcessRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| title | String | 标题 |
| content | String | 内容 |
| source | String | 来源 |
| status | Integer | 绩效流程记录状态 |
| operatorName | String | 操作人姓名 |
| operateTime | LocalDateTime | 操作时间 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |

**业务逻辑**:
1. 按 9.9 相同规则校验查看权限（本人考核或指定阶段处理人）
2. 查询考核的追加式动作记录
3. 按当前查看者的员工身份过滤记录可见性后返回

### 9.11 填写我的绩效指标

- **路径**: PUT /hrm/portal/performance/assessment/fill-quota
- **权限**: hrm:portal:performance:action
- **说明**: 被考核员工填写/修改绩效指标，并推进考核进入目标确认或执行阶段

**请求参数 (HrmPortalPerformanceFillQuotaReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| assessmentId | Long | 是 | @NotNull | 员工绩效考核编号 |
| quotas | List&lt;HrmPortalPerformanceQuotaSaveReqVO&gt; | 否 | 元素 @Valid | 指标列表 |

**HrmPortalPerformanceQuotaSaveReqVO（指标条目）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | - | 编号（已有指标） |
| dimensionId | Long | 否 | - | 员工绩效维度编号 |
| name | String | 否 | @Size(max = 255) | 指标名称 |
| description | String | 否 | @Size(max = 1000) | 指标说明 |
| standard | String | 否 | @Size(max = 1000) | 标准值 |
| weight | BigDecimal | 否 | - | 指标权重 |
| scoreType | Integer | 否 | - | 分数类型 |
| targetValue | String | 否 | @Size(max = 1000) | 目标值 |
| actualValue | String | 否 | @Size(max = 1000) | 实际值 |
| selfScore | BigDecimal | 否 | - | 自评分数 |
| reviewerScore | BigDecimal | 否 | - | 评分人得分 |
| finalScore | BigDecimal | 否 | - | 最终得分 |
| comment | String | 否 | @Size(max = 1000) | 说明 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前登录账号绑定的员工是该考核的被考核人（控制器预校验，Service 内锁定考核记录再次校验）
2. 校验绩效计划处于运行中且指标制定方式为"员工填写"，否则抛出 `PERFORMANCE_QUOTA_SETTING_INVALID`；校验存在待处理的指标填写阶段
3. 替换员工提交的自定义指标，完成指标填写阶段并清空历史目标确认结果
4. 计划启用目标确认时：重置并激活目标确认阶段，切换考核阶段状态，通知目标确认人处理待办；未启用时直接进入绩效执行阶段
5. 刷新绩效计划的完成状态，并追加"填写指标"绩效动作记录

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_019 | 绩效指标制定数据不合法 |
| 1_050_600_020 | 绩效目标确认人配置不合法 |

### 9.12 确认我的绩效目标

- **路径**: PUT /hrm/portal/performance/assessment/confirm-target
- **权限**: hrm:portal:performance:action
- **说明**: 目标确认人对考核目标进行确认或驳回

**请求参数 (HrmPortalPerformanceConfirmReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| assessmentId | Long | 是 | @NotNull | 员工绩效考核编号 |
| pass | Integer | 是 | @NotNull、@InEnum(HrmPerformanceConfirmationResultEnum) | 是否通过（确认结果） |
| comment | String | 否 | @Size(max = 1000) | 说明 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验考核存在、绩效计划运行中、考核处于目标确认阶段且该阶段待处理
2. 校验当前用户是目标确认人，否则抛出 `PERFORMANCE_TARGET_CONFIRM_NO_PERMISSION`；校验确认结果取值合法
3. 通过时完成目标确认阶段并进入绩效执行阶段；驳回时完成阶段（REJECTED），重置指标填写阶段为待处理并通知被考核人重新填写
4. 保存目标确认结果/意见/时间，刷新绩效计划完成状态，追加"确认目标/驳回目标"动作记录

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_021 | 当前用户不是该绩效目标的确认人 |

### 9.13 试算绩效评分

- **路径**: POST /hrm/portal/performance/assessment/score-preview
- **权限**: hrm:portal:performance:action
- **说明**: 按当前提交的评分输入试算阶段得分与累计得分，不落库

**请求参数 (HrmPortalPerformanceScoreReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| assessmentId | Long | 是 | @NotNull | 员工绩效考核编号 |
| reviewStageId | Long | 否 | - | 评分阶段编号（缺省定位当前待处理评分阶段） |
| comment | String | 否 | @Size(max = 2000) | 说明 |
| selfComment | String | 否 | @Size(max = 2000) | 自评说明 |
| reviewerComment | String | 否 | @Size(max = 2000) | 评分人说明 |
| quotas | List&lt;HrmPortalPerformanceQuotaSaveReqVO&gt; | 否 | 元素 @Valid | 指标列表（含分数） |

**响应**: CommonResult&lt;HrmPortalPerformanceScorePreviewRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| stageScore | BigDecimal | 阶段得分 |
| stageResultLevel | String | 阶段结果等级 |
| cumulativeScore | BigDecimal | 当前累计得分 |
| cumulativeResultLevel | String | 当前累计结果等级（全部评分阶段完成时返回） |

**业务逻辑**:
1. 校验考核存在、绩效计划运行中，定位待处理的评分阶段并校验当前用户是评分人（否则 `PERFORMANCE_REVIEW_STAGE_NOT_EXISTS` / `PERFORMANCE_REVIEW_STAGE_NO_PERMISSION`）
2. 校验评分指标：考核必须已配置指标，提交的指标编号与考核指标一一对应（缺失、重复、多余均抛 `PERFORMANCE_DATA_ILLEGAL`）
3. 按计划上限校验各指标分数后，计算当前阶段得分与阶段结果等级
4. 按阶段权重合并当前输入与已完成阶段的评分，计算累计得分；仅当本次为最后一个评分阶段时匹配累计结果等级

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_007 | 绩效数据不合法 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_012 | 绩效评分任务不存在 |
| 1_050_600_013 | 当前用户不是该绩效阶段的评分人 |

### 9.14 提交绩效自评或他评

- **路径**: PUT /hrm/portal/performance/assessment/score
- **权限**: hrm:portal:performance:action
- **说明**: 提交当前评分阶段的评分（自评/他评），推进考核流程

**请求参数**: HrmPortalPerformanceScoreReqVO（同 9.13）

**响应**: CommonResult&lt;HrmPortalPerformanceProcessRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| nextStageId | Long | 下一运行阶段编号 |

**业务逻辑**:
1. 锁定校验员工绩效考核存在且绩效计划运行中
2. 加载考核的评分阶段列表，缺失时抛出 `PERFORMANCE_REVIEW_STAGE_NOT_EXISTS`
3. 校验当前用户是当前评分阶段处理人后，保存指标评分与说明，完成当前评分阶段并推进至下一评分阶段或后续流程阶段
4. 刷新绩效计划完成状态并追加动作记录，返回下一运行阶段编号

**错误码**: 同 9.13（另含 1_050_600_015 驳回相关除外）

### 9.15 驳回上一绩效评分阶段

- **路径**: PUT /hrm/portal/performance/assessment/reject-review-stage
- **权限**: hrm:portal:performance:action
- **说明**: 具备驳回权限的评分阶段处理人，将上一已完成的评分阶段退回重新评分

**请求参数 (HrmPortalPerformanceReviewRejectReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| assessmentId | Long | 是 | @NotNull | 员工绩效考核编号 |
| reviewStageId | Long | 是 | @NotNull | 当前评分阶段编号 |
| reason | String | 是 | @NotBlank、@Size(max = 1000) | 驳回原因 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 锁定校验考核存在、计划运行中，指定的评分阶段必须处于待处理状态（否则 `PERFORMANCE_REVIEW_STAGE_NOT_EXISTS`）
2. 校验当前用户是该阶段评分人，且该阶段配置了驳回权限（否则 `PERFORMANCE_REVIEW_STAGE_REJECT_INVALID`）
3. 定位排序在当前阶段之前、最近一个已完成的评分阶段，将其重置为待处理并记录驳回原因
4. 刷新绩效计划完成状态并追加"驳回评分"动作记录

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_012 | 绩效评分任务不存在 |
| 1_050_600_013 | 当前用户不是该绩效阶段的评分人 |
| 1_050_600_015 | 当前绩效评分阶段不能驳回上一阶段 |

### 9.16 处理绩效结果审核

- **路径**: PUT /hrm/portal/performance/assessment/handle-result-audit
- **权限**: hrm:portal:performance:action
- **说明**: 结果审核节点处理人审核考核结果（通过或驳回）

**请求参数 (HrmPortalPerformanceHandleStageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| assessmentId | Long | 是 | @NotNull | 员工绩效考核编号 |
| stageId | Long | 是 | @NotNull | 运行阶段编号 |
| pass | Integer | 是 | @NotNull、@InEnum(HrmPerformanceConfirmationResultEnum) | 是否通过（处理结果） |
| comment | String | 否 | @Size(max = 500) | 处理意见 |
| reviewStageIds | List&lt;Long&gt; | 否 | - | 退回评分阶段编号列表（驳回时使用） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验考核存在、绩效计划运行中、考核处于结果审核阶段，且指定阶段待处理
2. 校验当前用户是该阶段处理人（否则 `PERFORMANCE_STAGE_NO_PERMISSION`）
3. 通过时激活下一审核节点或推进至结果确认阶段；驳回时按 reviewStageIds 将指定评分阶段退回重评
4. 刷新绩效计划完成状态并追加"结果审核"动作记录

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_027 | 当前用户不是该绩效阶段的处理人 |

### 9.17 确认我的绩效结果

- **路径**: PUT /hrm/portal/performance/assessment/confirm-result
- **权限**: hrm:portal:performance:action
- **说明**: 被考核员工确认绩效结果，考核进入结束阶段

**请求参数**: HrmPortalPerformanceConfirmReqVO（同 9.12）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验考核存在、计划运行中、考核属于当前登录员工（控制器预校验 + Service 校验）
2. 校验考核处于结果确认阶段且阶段待处理，确认结果取值合法
3. 完成结果确认阶段，关闭排序在其后未执行的申诉确认阶段，并完成绩效结束阶段
4. 保存结果说明与结果确认时间，考核流程状态置为"已结束"、阶段切至结束阶段
5. 刷新绩效计划完成状态，追加"确认结果"动作记录

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |

### 9.18 提交我的绩效申诉

- **路径**: PUT /hrm/portal/performance/assessment/submit-appeal
- **权限**: hrm:portal:performance:action
- **说明**: 被考核员工在结果确认阶段对考核结果发起申诉，退回指定评分阶段

**请求参数 (HrmPortalPerformanceAppealReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| assessmentId | Long | 是 | @NotNull | 员工绩效考核编号 |
| appealReason | String | 是 | @NotBlank、@Size(max = 500) | 申诉原因 |
| appealFileUrls | List&lt;String&gt; | 否 | - | 申诉附件地址列表 |
| reviewStageIds | List&lt;Long&gt; | 是 | @NotNull | 退回评分节点编号列表 |

**响应**: CommonResult&lt;HrmPortalPerformanceProcessRespVO&gt;（id + nextStageId，结构同 9.14）

**业务逻辑**:
1. 校验考核存在、属于当前登录员工、计划运行中、处于结果确认阶段；已存在待处理的申诉时抛出 `PERFORMANCE_PROCESS_RUNNING_CANNOT_MODIFY`
2. 校验退回的评分阶段编号均属于该考核
3. 将结果确认阶段标记为"已申诉"，激活首个申诉确认阶段（截止时间为当前时间 + 计划申诉超期天数）
4. 批量保存申诉关联的评分阶段记录（未处理状态），并保存申诉原因、附件、提交时间与申诉状态
5. 清空历史申诉处理结果，刷新绩效计划完成状态并追加"提交申诉"动作记录，返回申诉阶段编号

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_009 | 绩效流程处理中，不能修改当前记录 |

### 9.19 处理绩效申诉

- **路径**: PUT /hrm/portal/performance/assessment/handle-appeal
- **权限**: hrm:portal:performance:action
- **说明**: 申诉处理节点处理人处理绩效申诉（通过或驳回）

**请求参数**: HrmPortalPerformanceHandleStageReqVO（同 9.16）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验考核存在、绩效计划运行中、考核处于申诉确认阶段，且指定阶段待处理
2. 校验当前用户是该阶段处理人（否则 `PERFORMANCE_STAGE_NO_PERMISSION`）
3. 通过时结束申诉流程并推进至后续阶段；驳回时按申诉记录将涉及的评分阶段退回重新评分
4. 保存申诉处理意见，刷新绩效计划完成状态并追加"申诉处理"动作记录

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_600_004 | 绩效计划不存在 |
| 1_050_600_006 | 员工绩效考核不存在 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 |
| 1_050_600_027 | 当前用户不是该绩效阶段的处理人 |

---

## 附：员工自助门户通用错误码

| 错误码 | 说明 | 涉及域 |
|-------|-----|-------|
| 1_050_100_000 | 员工档案不存在 | 全部（本人身份校验） |
| 1_050_100_003 | 手机号已绑定员工档案 | 员工档案更新 |
| 1_050_100_035 | 员工档案字段【{}】不能为空 | 员工档案更新 |
| 1_050_300_030 | 请假申请不存在 | 考勤请假 |
| 1_050_300_031 | 请假时间与已有申请重叠 | 考勤请假 |
| 1_050_300_032 | 只有审批中的请假申请可以取消 | 考勤请假 |
| 1_050_300_034 | 今日休息，无需打卡 | 考勤打卡 |
| 1_050_300_035 | 当前不在可打卡时间 | 考勤打卡 |
| 1_050_300_036 | 不在考勤打卡范围内 | 考勤打卡 |
| 1_050_300_037 | 未连接指定的考勤 WiFi | 考勤打卡 |
| 1_050_300_038 | 未匹配到考勤组，无法打卡 | 考勤打卡 |
| 1_050_400_013 | 工资条不存在 | 工资条 |
| 1_050_500_006 | 员工月度社保记录不存在 | 社保 |
| 1_050_600_004 | 绩效计划不存在 | 绩效考核 |
| 1_050_600_006 | 员工绩效考核不存在 | 绩效考核 |
| 1_050_600_007 | 绩效数据不合法 | 绩效考核 |
| 1_050_600_008 | 当前绩效阶段不允许执行该操作 | 绩效考核 |
| 1_050_600_009 | 绩效流程处理中，不能修改当前记录 | 绩效考核 |
| 1_050_600_012 | 绩效评分任务不存在 | 绩效考核 |
| 1_050_600_013 | 当前用户不是该绩效阶段的评分人 | 绩效考核 |
| 1_050_600_015 | 当前绩效评分阶段不能驳回上一阶段 | 绩效考核 |
| 1_050_600_019 | 绩效指标制定数据不合法 | 绩效考核 |
| 1_050_600_020 | 绩效目标确认人配置不合法 | 绩效考核 |
| 1_050_600_021 | 当前用户不是该绩效目标的确认人 | 绩效考核 |
| 1_050_600_027 | 当前用户不是该绩效阶段的处理人 | 绩效考核 |
| 1_050_900_001 | HRM 首页日期范围不合法 | 首页日历 |
