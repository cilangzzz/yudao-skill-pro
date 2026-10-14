# 工作台接口 (HrmHomeController)

> 提供 HRM 首页工作台数据：HR 工作台与团队工作台的人员/招聘/薪资统计摘要，以及覆盖备忘、生日、入职、转正、离职、招聘面试等事项的日程日历。

## 接口路径前缀

/hrm/home  (Controller: HrmHomeController)

- **HR 工作台**：面向 HR 管理员，聚合全公司人事、招聘、薪资数据与全员工日历
- **团队工作台**：面向团队主管，聚合直属下属的团队概况与下属人事日历

---

## 1. HR 工作台

### 1.1 获得 HR 工作台统计

- **路径**: GET /hrm/home/hr-statistics-summary
- **权限**: `hrm:home:hr-query`
- **说明**: 一次性返回人事概况、招聘动态、上月薪资、待办提醒四类统计摘要

**请求参数**: 无

**响应**: CommonResult<HrmHrHomeStatisticsRespVO>

| 字段 | 类型 | 说明 |
|-----|------|-----|
| employeeSurvey | EmployeeSurvey | 人事概况 |
| recruitSurvey | RecruitSurvey | 招聘动态 |
| salarySurvey | SalarySurvey | 上月薪资 |
| todoSurvey | TodoSurvey | 待办提醒 |

**EmployeeSurvey（人事概况）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| activeCount | Long | 在职人数 |
| entryThisMonthCount | Long | 本月入职人数 |
| pendingEntryThisMonthCount | Long | 本月待入职人数 |
| leaveThisMonthCount | Long | 本月离职人数 |
| pendingLeaveThisMonthCount | Long | 本月待离职人数 |
| regularThisMonthCount | Long | 本月转正人数 |
| transferThisMonthCount | Long | 本月调岗人数 |

**RecruitSurvey（招聘动态）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| recruitingPostCount | Long | 招聘中职位数量 |
| candidateInProcessCount | Long | 招聘流程中候选人数 |
| pendingEntryCount | Long | 待入职人数（近六个月） |
| joinedCount | Long | 已入职人数（近六个月） |

**SalarySurvey（上月薪资）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| monthRecordId | Long | 工资表编号 |
| employeeCount | Integer | 员工数量 |
| realPaySalary | BigDecimal | 实发工资 |
| deptProportions | List&lt;SalaryDept&gt; | 部门薪资占比列表 |

**SalaryDept（部门薪资占比）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| deptId | Long | 部门编号（0 表示无部门） |
| deptName | String | 部门名称（部门已删除时显示"部门已删除"） |
| proportion | BigDecimal | 薪资占比（4 位小数） |
| totalSalary | BigDecimal | 实发工资 |

**TodoSurvey（待办提醒）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| toEntryCount | Long | 待入职人数 |
| toLeaveCount | Long | 待离职人数 |
| toExpireContractCount | Long | 合同待到期人数 |
| toRegularCount | Long | 待转正人数 |
| toSalaryComputeCount | Long | 待核算工资表数量 |
| toBirthdayCount | Long | 本月生日员工数量 |

**业务逻辑**:
1. 构建人事概况：统计当前在职员工总数；基于员工主档、离职状态和异动记录聚合统计本月入职/待入职/离职/待离职/转正/调岗六类人数
2. 构建招聘动态：统计"招聘中"职位数量与流程中（处理中状态）候选人数；再统计近六个月内待入职和已入职的候选人数量
3. 构建上月薪资：查询上个月的月度工资表，仅当其状态为"历史（HISTORY）"时继续；否则填充默认值（0 人、0 元、空占比列表）
4. 查询该工资表下的员工工资明细，按员工当前部门汇总实发工资，并经 DeptApi 转换部门名称（员工无部门归入"无部门"，部门已删除显示"部门已删除"）
5. 计算各部门薪资占比（部门实发工资 / 总实发工资，保留 4 位小数向上取整），按实发工资降序排列
6. 构建待办提醒：待入职/待离职人数复用人事概况数据；另统计本月合同到期人数、待转正人数、待核算工资表数量和本月生日员工数量

### 1.2 获得 HR 工作台日历

- **路径**: GET /hrm/home/hr-calendar
- **权限**: `hrm:home:hr-query`
- **说明**: 返回指定日期范围内 HR 视角的全员日历事项（备忘/生日/入职/转正/离职/面试）

**请求参数**（Query 参数，无独立 ReqVO 类）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| startDate | LocalDate | 是 | @DateTimeFormat(iso = DATE) | 开始日期，如 2026-08-01 |
| endDate | LocalDate | 是 | @DateTimeFormat(iso = DATE) | 结束日期，如 2026-08-31 |

**响应**: CommonResult&lt;List&lt;HrmHomeCalendarItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| personalNoteId | Long | 员工个人备忘编号（仅备忘事项有值） |
| type | Integer | 事项类型：1 备忘、2 生日、3 入职、4 转正、5 离职、6 招聘、7 考勤 |
| typeName | String | 事项类型名称 |
| content | String | 事项内容（如"张三 25岁生日"、"上午 10:30 面试"） |
| typeId | Long | 关联业务编号（员工编号 / 候选人编号，备忘为 null） |
| date | LocalDate | 事项日期 |
| eventTime | LocalDateTime | 事项时间 |

**业务逻辑**:
1. 校验日期范围：startDate/endDate 非空、endDate 不早于 startDate、跨度不超过 370 天，否则抛出 `HOME_CALENDAR_DATE_RANGE_ILLEGAL` 错误
2. 收集本人备忘事项：查询当前登录员工在日期范围内的个人备忘，按提醒时间生成备忘事项
3. 收集全量员工的人事事项：非离职员工按生日生成"XX N岁生日"事项（支持 2 月 29 日生日按年校验）；待入职员工生成入职事项；在职员工生成转正事项；待离职员工按离职信息中的计划离职时间生成离职事项
4. 收集招聘面试事项：查询日期范围内的面试安排，过滤候选人不存在、候选人状态不在日历展示状态、面试已取消、面试阶段与候选人当前阶段不一致的记录，生成"候选人名 + 上午/下午 HH:mm + 面试"事项
5. 按事项时间（空值排最后）、类型、内容进行稳定排序后返回

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_900_001 | HRM 首页日期范围不合法 |

---

## 2. 团队工作台

### 2.1 获得团队工作台统计

- **路径**: GET /hrm/home/team-statistics-summary
- **权限**: `hrm:home:team-query`
- **说明**: 返回当前登录主管的直属团队人数变动概况与人员结构分析

**请求参数**: 无

**响应**: CommonResult<HrmTeamHomeStatisticsRespVO>

| 字段 | 类型 | 说明 |
|-----|------|-----|
| leaderEmployeeId | Long | 当前主管员工编号（登录用户未关联员工档案时为 null） |
| teamOverview | TeamOverview | 我的团队（人数变动概况） |
| teamSurvey | TeamSurvey | 团队概况（人员结构占比） |

**TeamOverview（我的团队）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| employeeCount | Long | 团队人数（当前在职） |
| entryThisMonthCount | Long | 本月入职人数 |
| leaveThisMonthCount | Long | 本月离职人数 |
| regularThisMonthCount | Long | 本月转正人数 |

**TeamSurvey（团队概况）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| statusAnalysis | List&lt;AnalysisItem&gt; | 员工状态占比 |
| sexAnalysis | List&lt;AnalysisItem&gt; | 男女性别占比 |
| ageAnalysis | List&lt;AnalysisItem&gt; | 成员年龄占比 |
| companyAgeAnalysis | List&lt;AnalysisItem&gt; | 成员司龄占比 |

**AnalysisItem（统计分析项）**:

| 字段 | 类型 | 说明 |
|-----|------|-----|
| type | Integer | 分类类型（对应各枚举值；null 表示未填写） |
| count | Long | 数量 |

**业务逻辑**:
1. 根据当前登录用户查询对应员工档案，再查询其直属下属（以该员工为主管），过滤出在职状态的团队成员；登录用户未关联员工档案时团队为空列表
2. 统计我的团队概况：在职团队人数、本月入职人数（排除待入职状态）、本月离职人数（按离职时间）
3. 本月转正人数通过团队员工的异动记录（效果时间在本月、类型为转正）按员工去重统计
4. 统计团队概况：对在职团队成员分别按员工状态、性别、年龄（优先按生日实时计算）、司龄（按司龄起始时间计算天数换算区间）四个维度分组计数
5. 各维度统计结果包含全部分类（含计数为 0 的分类），未填写对应字段的员工归入 null 分类

### 2.2 获得团队工作台日历

- **路径**: GET /hrm/home/team-calendar
- **权限**: `hrm:home:team-query`
- **说明**: 返回指定日期范围内当前主管本人备忘及直属下属的人事日历事项

**请求参数**（Query 参数，无独立 ReqVO 类）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| startDate | LocalDate | 是 | @DateTimeFormat(iso = DATE) | 开始日期，如 2026-08-01 |
| endDate | LocalDate | 是 | @DateTimeFormat(iso = DATE) | 结束日期，如 2026-08-31 |

**响应**: CommonResult&lt;List&lt;HrmHomeCalendarItemRespVO&gt;&gt;

字段结构同 [1.2 获得 HR 工作台日历](#12-获得-hr-工作台日历) 的 HrmHomeCalendarItemRespVO（团队日历仅包含备忘/生日/入职/转正/离职类型，不含招聘面试）。

**业务逻辑**:
1. 校验日期范围：startDate/endDate 非空、endDate 不早于 startDate、跨度不超过 370 天，否则抛出 `HOME_CALENDAR_DATE_RANGE_ILLEGAL` 错误
2. 查询当前登录用户对应的员工档案；未关联员工档案时直接返回空列表
3. 收集本人备忘事项：查询当前主管在日期范围内的个人备忘
4. 收集直属下属的人事日历事项：非离职下属的生日事项、待入职下属的入职事项、在职下属的转正事项、待离职下属按计划离职时间的离职事项
5. 按事项时间（空值排最后）、类型、内容进行稳定排序后返回

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_900_001 | HRM 首页日期范围不合法 |
