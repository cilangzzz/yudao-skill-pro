# 数据模型详情

> hrm 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。hrm 模块共 50 个 DO、50 张表，全部位于 `cn.iocoder.yudao.module.hrm.dal.dataobject` 下，按 employee（员工）、recruit（招聘）、attendance（考勤）、salary（薪资）、insurance（社保）、performance（绩效）、config（通用配置）七个包组织。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，yudao-spring-boot-starter-mybatis）
│   implements Serializable, TransPojo（Easy-Trans）
│
│   creator      String          创建者（system_users 用户编号，INSERT 自动填充，varchar(64)）
│   createTime   LocalDateTime   创建时间（INSERT 自动填充）
│   updater      String          更新者（INSERT/UPDATE 自动填充，varchar(64)）
│   updateTime   LocalDateTime   最后更新时间（INSERT/UPDATE 自动填充）
│   deleted      Boolean         逻辑删除标记（@TableLogic，bit）
│
├── TenantBaseDO（yudao-spring-boot-starter-biz-tenant，仅多增加 tenantId 字段）
│   └── ✗ hrm 模块无任何 DO 继承 TenantBaseDO
│
└── hrm 模块全部 50 个 DO 直接继承 BaseDO：
    ├── 员工：HrmEmployeeDO、HrmEmployeeContactDO、HrmEmployeeFileDO、HrmEmployeePersonalNoteDO、
    │         HrmEmployeeChangeRecordDO、HrmEmployeeContractDO、HrmEmployeeQuitInfoDO、HrmEmployeeSalaryCardDO、
    │         HrmEmployeeEducationExperienceDO、HrmEmployeeWorkExperienceDO、HrmEmployeeTrainingExperienceDO、
    │         HrmEmployeeCertificateDO                    （12 个）
    ├── 招聘：HrmRecruitPostDO、HrmRecruitPostTypeDO、HrmRecruitChannelDO、HrmRecruitCandidateDO、
    │         HrmRecruitInterviewDO                       （5 个）
    ├── 考勤：HrmAttendanceGroupDO、HrmAttendanceHolidayDO、HrmAttendanceClockDO、HrmAttendanceLeaveDO（4 个）
    ├── 薪资：HrmSalaryConfigDO、HrmSalaryGroupDO、HrmSalaryOptionDO、HrmSalaryOptionTemplateDO、
    │         HrmSalaryTaxRuleDO、HrmSalaryChangeTemplateDO、HrmSalaryEmployeeInfoDO、HrmSalaryChangeRecordDO、
    │         HrmSalaryMonthRecordDO、HrmSalaryMonthEmployeeRecordDO、HrmSalarySlipTemplateDO、
    │         HrmSalarySlipSendRecordDO、HrmSalarySlipDO   （13 个）
    ├── 社保：HrmInsuranceSchemeDO、HrmInsuranceSchemeProjectDO、HrmInsuranceEmployeeInfoDO、
    │         HrmInsuranceMonthRecordDO、HrmInsuranceMonthEmployeeRecordDO（5 个）
    ├── 绩效：HrmPerformanceAssessmentTemplateDO、HrmPerformanceResultTemplateDO、HrmPerformancePlanDO、
    │         HrmPerformanceAssessmentDO、HrmPerformanceAssessmentStageDO、HrmPerformanceAssessmentDimensionDO、
    │         HrmPerformanceAssessmentQuotaDO、HrmPerformanceAssessmentQuotaScoreDO、
    │         HrmPerformanceAssessmentActionRecordDO、HrmPerformanceAssessmentAppealRecordDO（10 个）
    └── 配置：HrmConfigDO                                 （1 个）
```

**使用规则**：

1. **统一继承 BaseDO**：hrm 模块 50 个 DO 全部直接继承 `BaseDO`，统一获得 creator/createTime/updater/updateTime/deleted 五个公共字段；没有需要按 DO 字段读写 tenantId 的场景，因此无人继承 `TenantBaseDO`。
2. **租户隔离在 SQL 层实现**：除 `hrm_salary_option_template` 外，其余 49 张表的 DDL 都带 `tenant_id bigint NOT NULL DEFAULT 0` 物理列。DO 不声明 tenantId 字段，由框架的 `TenantLineInnerInterceptor` + `TenantDatabaseInterceptor` 在 SQL 解析层自动追加 `tenant_id` 过滤条件并在 INSERT 时自动填值（未继承 TenantBaseDO 且未标注 `@TenantIgnore` 的已注册实体，默认参与租户隔离）。
3. **全局共享表**：`HrmSalaryOptionTemplateDO`（标准薪资项目录）类上标注 `@TenantIgnore`，对应表无 `tenant_id` 列，作为全系统共享的字典性质目录，code 全局唯一。
4. **主键策略**：全部 DO 主键为 `@TableId Long id`，表声明 `@KeySequence("hrm_xxx_seq")`（Oracle/PostgreSQL 等使用序列，MySQL 自增）。
5. **复杂结构用 JSON 列**：涉及列表/嵌套配置的字段统一用 TypeHandler（`StringListTypeHandler` / `LongListTypeHandler` / `JacksonTypeHandler`）映射为 varchar JSON 字符串，对应 DO 上 `@TableName(autoResultMap = true)`。这类字段（如考勤组班次、工资条项、绩效计划配置快照）**无法在 SQL 中直接过滤或索引**，查询过滤需在内存中完成。
6. **DDL 来源**：仓库根 `sql/` 目录未提供 hrm 生产建表脚本，模块内自带 H2 单测脚本 `yudao-module-hrm/src/test/resources/sql/create_tables.sql`（50 张表与 DO 一一对应），本文索引信息均以该脚本为准；除下文列出的唯一约束外，其余表仅声明 PRIMARY KEY，无二级索引。

## 2. 核心 DO 实体

### 2.1 员工聚合（employee，12 张表）

以 `HrmEmployeeDO` 员工档案为中心，一对多挂接联系人、材料、经历、合同等从表。

#### HrmEmployeeDO (hrm_employee)

员工档案主档，全模块的核心实体，绝大多数表通过 `employee_id` 关联本表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 员工编号，主键 |
| name | String | name | 员工姓名（NOT NULL） |
| jobNumber | String | job_number | 工号 |
| userId | Long | user_id | 关联 system_users.id，允许为空（待入职、离职历史员工无登录账号） |
| mobile | String | mobile | 手机号码 |
| country | String | country | 国家或地区 |
| nation | String | nation | 民族 |
| idType | Integer | id_type | 证件类型（枚举 HrmEmployeeIdTypeEnum） |
| idNumber | String | id_number | 证件号码 |
| sex | Integer | sex | 性别（system 模块 SexEnum） |
| email | String | email | 邮箱 |
| nativePlace | String | native_place | 籍贯 |
| birthday | LocalDateTime | birthday | 出生时间 |
| age | Integer | age | 年龄 |
| address | String | address | 户籍地址 |
| highestEducation | Integer | highest_education | 最高学历（枚举 HrmEmployeeEducationEnum，字典 hrm_employee_education） |
| deptId | Long | dept_id | 关联 system_dept.id（所属部门） |
| leaderEmployeeId | Long | leader_employee_id | 直属上级员工编号，自关联本表 id |
| entryStatus | Integer | entry_status | 入职状态（枚举 HrmEmployeeEntryStatusEnum，字典 hrm_employee_entry_status） |
| status | Integer | status | 员工状态（枚举 HrmEmployeeStatusEnum，字典 hrm_employee_status） |
| type | Integer | type | 聘用形式（枚举 HrmEmployeeTypeEnum，字典 hrm_employee_type） |
| entryTime | LocalDateTime | entry_time | 入职时间 |
| probation | Integer | probation | 试用期（月），0 表示无试用期 |
| regularTime | LocalDateTime | regular_time | 转正时间 |
| leaveTime | LocalDateTime | leave_time | 离职时间 |
| postName | String | post_name | 职位名称 |
| postLevel | String | post_level | 岗位职级 |
| workCity | String | work_city | 工作城市 |
| workAddress | String | work_address | 工作地址 |
| workDetailAddress | String | work_detail_address | 工作详细地址 |
| channelId | Long | channel_id | 关联 hrm_recruit_channel.id（招聘渠道） |
| companyAgeStartTime | LocalDateTime | company_age_start_time | 司龄开始时间 |
| companyAge | Integer | company_age | 司龄（年） |
| candidateId | Long | candidate_id | 关联 hrm_recruit_candidate.id（入职来源候选人） |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；无其余显式索引

#### HrmEmployeeContactDO (hrm_employee_contact)

员工紧急联系人/联系人。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 联系人编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| name | String | name | 联系人名称 |
| relation | String | relation | 与员工的关系 |
| phone | String | phone | 联系人电话 |
| workUnit | String | work_unit | 联系人工作单位 |
| postName | String | post_name | 联系人职务 |
| address | String | address | 联系人地址 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeFileDO (hrm_employee_file)

员工材料附件（证件照、学历证明等文件）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 附件编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| type | Integer | type | 附件类型（枚举 HrmEmployeeFileTypeEnum，NOT NULL） |
| url | String | url | 附件地址（NOT NULL，varchar(512)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeePersonalNoteDO (hrm_employee_personal_note)

员工个人备忘（首页待办提醒用）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 备忘编号，主键 |
| employeeId | Long | employee_id | 所属员工编号，关联 hrm_employee.id |
| content | String | content | 备忘内容（NOT NULL，varchar(1024)） |
| reminderTime | LocalDateTime | reminder_time | 提醒时间（NOT NULL） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeChangeRecordDO (hrm_employee_change_record)

员工异动记录（转正、调岗、调薪、调部门等），由 `HrmEmployeeChangeJob` 定时任务在生效日自动应用（@TenantJob）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 异动记录编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| type | Integer | type | 异动类型（枚举 HrmEmployeeChangeTypeEnum） |
| reason | Integer | reason | 异动原因（枚举 HrmEmployeeChangeReasonEnum） |
| oldDeptId | Long | old_dept_id | 原部门，关联 system_dept.id |
| newDeptId | Long | new_dept_id | 新部门，关联 system_dept.id |
| oldPostName | String | old_post_name | 原岗位 |
| newPostName | String | new_post_name | 新岗位 |
| oldPostLevel | String | old_post_level | 原职级 |
| newPostLevel | String | new_post_level | 新职级 |
| oldWorkAddress | String | old_work_address | 原工作地点 |
| newWorkAddress | String | new_work_address | 新工作地点 |
| oldLeaderEmployeeId | Long | old_leader_employee_id | 原直属上级员工编号，关联 hrm_employee.id |
| newLeaderEmployeeId | Long | new_leader_employee_id | 新直属上级员工编号，关联 hrm_employee.id |
| probation | Integer | probation | 试用期（月） |
| effectTime | LocalDateTime | effect_time | 计划生效日期 |
| appliedTime | LocalDateTime | applied_time | 实际生效时间（Job 应用后回写） |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeContractDO (hrm_employee_contract)

员工劳动合同，含到期提醒与附件。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| no | String | no | 合同编号 |
| type | Integer | type | 合同类型（枚举 HrmEmployeeContractTypeEnum） |
| startTime | LocalDateTime | start_time | 合同开始日期 |
| endTime | LocalDateTime | end_time | 合同结束日期 |
| term | Integer | term | 合同期限（年） |
| status | Integer | status | 合同状态（枚举 HrmEmployeeContractStatusEnum） |
| signCompany | String | sign_company | 签约公司 |
| signTime | LocalDateTime | sign_time | 合同签订日期 |
| remark | String | remark | 备注 |
| expireRemind | Boolean | expire_remind | 是否到期提醒 |
| sort | Integer | sort | 显示顺序 |
| fileUrls | List\<String\> | file_urls | 附件地址数组，StringListTypeHandler 存 JSON（varchar(2048)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeQuitInfoDO (hrm_employee_quit_info)

员工离职信息（一个员工一次离职流程一条记录）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 离职信息编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| planQuitTime | LocalDateTime | plan_quit_time | 计划离职时间 |
| applyQuitTime | LocalDateTime | apply_quit_time | 申请离职时间 |
| salarySettlementTime | LocalDateTime | salary_settlement_time | 薪资结算时间 |
| type | Integer | type | 离职类型（枚举 HrmEmployeeQuitTypeEnum） |
| reason | Integer | reason | 离职原因（枚举 HrmEmployeeQuitReasonEnum） |
| remark | String | remark | 备注 |
| oldEmployeeStatus | Integer | old_employee_status | 离职前员工状态（枚举 HrmEmployeeStatusEnum） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeSalaryCardDO (hrm_employee_salary_card)

员工工资卡（银行账户信息）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| bankCardNumber | String | bank_card_number | 银行卡号 |
| bankAreaId | Integer | bank_area_id | 开户地区编号（框架 ip 模块 Area.id） |
| bankName | String | bank_name | 银行名称 |
| bankBranchName | String | bank_branch_name | 开户支行名称 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeEducationExperienceDO (hrm_employee_education_experience)

员工教育经历。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 教育经历编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| education | Integer | education | 学历（枚举 HrmEmployeeEducationEnum，字典 hrm_employee_education） |
| graduateSchool | String | graduate_school | 毕业院校 |
| major | String | major | 专业 |
| admissionTime | LocalDateTime | admission_time | 入学日期 |
| graduationTime | LocalDateTime | graduation_time | 毕业日期 |
| teachingMethods | Integer | teaching_methods | 教学方式（枚举 HrmEmployeeTeachingMethodEnum） |
| firstDegree | Boolean | first_degree | 是否第一学历 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeWorkExperienceDO (hrm_employee_work_experience)

员工工作经历（入职前）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 工作经历编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| workUnit | String | work_unit | 工作单位 |
| postName | String | post_name | 职务 |
| startTime | LocalDateTime | start_time | 工作开始日期 |
| endTime | LocalDateTime | end_time | 工作结束日期 |
| reason | String | reason | 离职原因 |
| witnessName | String | witness_name | 证明人 |
| witnessPhone | String | witness_phone | 证明人手机号 |
| remark | String | remark | 工作备注 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeTrainingExperienceDO (hrm_employee_training_experience)

员工培训经历。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 培训经历编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| course | String | course | 培训课程 |
| organizationName | String | organization_name | 培训机构名称 |
| startTime | LocalDateTime | start_time | 培训开始日期 |
| endTime | LocalDateTime | end_time | 培训结束日期 |
| duration | String | duration | 培训时长 |
| result | String | result | 培训成绩 |
| certificateName | String | certificate_name | 培训证书名称 |
| remark | String | remark | 备注 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmEmployeeCertificateDO (hrm_employee_certificate)

员工资格证书。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 证书编号，主键 |
| employeeId | Long | employee_id | 关联 hrm_employee.id（NOT NULL） |
| name | String | name | 证书名称 |
| level | String | level | 证书级别 |
| no | String | no | 证书编号 |
| startTime | LocalDateTime | start_time | 有效开始日期 |
| endTime | LocalDateTime | end_time | 有效结束日期 |
| issuingAuthority | String | issuing_authority | 发证机构 |
| issuingTime | LocalDateTime | issuing_time | 发证日期 |
| remark | String | remark | 备注 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 主键 id

### 2.2 招聘聚合（recruit，5 张表）

职位类型/渠道为字典配置，职位挂招聘负责人与面试官，候选人投递职位并产生多轮面试记录；候选人入职后转为员工档案。

#### HrmRecruitPostDO (hrm_recruit_post)

招聘职位。约定值：`minSalary`/`maxSalary` 为 -1 表示面议（SALARY_NEGOTIABLE_VALUE），`minAge`/`maxAge` 为 -1 表示不限（AGE_UNLIMITED_VALUE）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 招聘职位编号，主键 |
| postName | String | post_name | 职位名称（NOT NULL） |
| deptId | Long | dept_id | 关联 system_dept.id（用人部门） |
| jobNature | Integer | job_nature | 工作性质（字典 hrm_recruit_job_nature：全职/实习/兼职） |
| areaId | Integer | area_id | 工作城市地区编号（框架 ip 模块 Area.id） |
| recruitNum | Integer | recruit_num | 招聘人数 |
| reason | String | reason | 招聘原因 |
| workTime | Integer | work_time | 工作经验要求（字典 hrm_recruit_work_time） |
| educationRequire | Integer | education_require | 学历要求（字典 hrm_recruit_post_education） |
| minSalary | BigDecimal | min_salary | 最低薪资（decimal(10,2)，-1 表示面议） |
| maxSalary | BigDecimal | max_salary | 最高薪资（decimal(10,2)，-1 表示面议） |
| salaryUnit | Integer | salary_unit | 薪资单位（字典 hrm_recruit_salary_unit） |
| minAge | Integer | min_age | 最小年龄（-1 表示不限） |
| maxAge | Integer | max_age | 最大年龄（-1 表示不限） |
| latestEntryTime | LocalDateTime | latest_entry_time | 最迟到岗时间 |
| ownerEmployeeId | Long | owner_employee_id | 招聘负责人员工编号，关联 hrm_employee.id |
| interviewEmployeeIds | List\<Long\> | interview_employee_ids | 面试官员工编号数组，LongListTypeHandler 存 JSON（varchar(255)） |
| description | String | description | 职位描述（varchar(4000)） |
| emergencyLevel | Integer | emergency_level | 紧急程度（字典 hrm_recruit_emergency_level） |
| postTypeId | Long | post_type_id | 职位类型，关联 hrm_recruit_post_type.id |
| status | Integer | status | 职位状态（枚举 HrmRecruitPostStatusEnum，字典 hrm_recruit_post_status） |
| stopReason | String | stop_reason | 停止招聘原因 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmRecruitPostTypeDO (hrm_recruit_post_type)

招聘职位类型（树形结构）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 职位类型编号，主键 |
| name | String | name | 类型名称 |
| parentId | Long | parent_id | 父类型编号，自关联本表 id |
| sort | Integer | sort | 显示顺序 |
| status | Integer | status | 状态（CommonStatusEnum） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmRecruitChannelDO (hrm_recruit_channel)

招聘渠道（系统内置 + 自定义）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 招聘渠道编号，主键 |
| systemFlag | Boolean | system_flag | 是否系统内置（默认 false） |
| status | Integer | status | 状态（CommonStatusEnum） |
| name | String | name | 渠道名称（NOT NULL） |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmRecruitCandidateDO (hrm_recruit_candidate)

招聘候选人。入职转化后由 `hrm_employee.candidate_id` 反向关联。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 候选人编号，主键 |
| name | String | name | 候选人姓名（NOT NULL） |
| mobile | String | mobile | 手机号码（NOT NULL） |
| sex | Integer | sex | 性别（SexEnum，NOT NULL） |
| age | Integer | age | 年龄 |
| email | String | email | 邮箱 |
| postId | Long | post_id | 应聘职位，关联 hrm_recruit_post.id（NOT NULL） |
| stageNumber | Integer | stage_number | 面试轮次 |
| workTime | Integer | work_time | 工作年限（年） |
| education | Integer | education | 学历（字典 hrm_recruit_candidate_education，NOT NULL） |
| graduateSchool | String | graduate_school | 毕业院校 |
| latestWorkPlace | String | latest_work_place | 最近工作单位 |
| channelId | Long | channel_id | 招聘渠道，关联 hrm_recruit_channel.id |
| remark | String | remark | 备注 |
| status | Integer | status | 候选人状态（枚举 HrmRecruitCandidateStatusEnum，字典 hrm_recruit_candidate_status） |
| eliminate | String | eliminate | 淘汰原因 |
| statusUpdateTime | LocalDateTime | status_update_time | 状态更新时间 |
| entryTime | LocalDateTime | entry_time | 入职时间 |
| resumeUrls | List\<String\> | resume_urls | 简历附件地址数组，StringListTypeHandler 存 JSON（varchar(4000)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmRecruitInterviewDO (hrm_recruit_interview)

招聘面试记录（一个候选人多轮面试）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 面试编号，主键 |
| candidateId | Long | candidate_id | 候选人，关联 hrm_recruit_candidate.id（NOT NULL） |
| type | Integer | type | 面试方式（字典 hrm_recruit_interview_type） |
| stageNumber | Integer | stage_number | 面试轮次 |
| interviewEmployeeId | Long | interview_employee_id | 主面试官员工编号，关联 hrm_employee.id |
| otherInterviewEmployeeIds | List\<Long\> | other_interview_employee_ids | 其他面试官员工编号数组，LongListTypeHandler 存 JSON（varchar(255)） |
| interviewTime | LocalDateTime | interview_time | 面试时间 |
| address | String | address | 面试地址 |
| remark | String | remark | 备注 |
| result | Integer | result | 面试结果（枚举 HrmRecruitInterviewResultEnum，字典 hrm_recruit_interview_result） |
| evaluate | String | evaluate | 面试评价 |
| cancelReason | String | cancel_reason | 取消原因 |

**继承**: BaseDO
**索引**: 主键 id

### 2.3 考勤聚合（attendance，4 张表）

考勤组承担班次/打卡方式/扣款规则的全部配置（JSON 列）；打卡与请假为流水记录，请假审批对接 BPM 工作流。

#### HrmAttendanceGroupDO (hrm_attendance_group)

考勤组，班次、打卡地点、WiFi、扣款规则全部内嵌 JSON 列。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考勤组编号，主键 |
| name | String | name | 考勤组名称（NOT NULL，varchar(50)） |
| deptIds | List\<Long\> | dept_ids | 适用部门编号数组，LongListTypeHandler 存 JSON（varchar(4000)） |
| employeeIds | List\<Long\> | employee_ids | 适用员工编号数组，LongListTypeHandler 存 JSON（varchar(4000)） |
| openWifiCard | Boolean | open_wifi_card | 是否启用 WiFi 打卡（NOT NULL，默认 false） |
| openPointCard | Boolean | open_point_card | 是否启用定位打卡（NOT NULL，默认 false） |
| shifts | List\<Shift\> | shifts | 班次配置，JacksonTypeHandler 存 JSON（varchar(10000)，NOT NULL）。Shift 内嵌：weeks 工作日数组、startTime/endTime 上下班时间、clockInStart/EndTime 上班打卡窗口、clockOutStart/EndTime 下班打卡窗口、restStart/EndTime 休息时间、excludeRestTime 休息是否不计时长 |
| rest | Boolean | rest | 是否法定节假日休息（NOT NULL，默认 true） |
| specialDates | List\<SpecialDate\> | special_dates | 特殊日期设置数组，JacksonTypeHandler 存 JSON（varchar(4000)，NOT NULL）。SpecialDate 内嵌：type 日期类型（HrmAttendanceHolidayTypeEnum）、date 日期 |
| points | List\<Point\> | points | 打卡地点配置，JacksonTypeHandler 存 JSON（varchar(10000)，NOT NULL）。Point 内嵌：name、address、latitude/longitude 经纬度、radius 有效打卡半径（米） |
| wifis | List\<Wifi\> | wifis | WiFi 打卡配置，JacksonTypeHandler 存 JSON（varchar(10000)，NOT NULL）。Wifi 内嵌：ssid、mac |
| deductRule | DeductRule | deduct_rule | 扣款规则，JacksonTypeHandler 存 JSON（varchar(4000)，NOT NULL）。DeductRule 内嵌：lateMethod/lateDeductMoney 迟到、earlyMethod/earlyDeductMoney 早退、absenteeismMethod/absenteeismDeductMoney 旷工、misscardMethod/misscardDeductMoney 缺卡 |
| defaultStatus | Boolean | default_status | 是否默认考勤组（NOT NULL，默认 false） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmAttendanceHolidayDO (hrm_attendance_holiday)

考勤节假日表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 节假日编号，主键 |
| date | LocalDateTime | date | 日期（NOT NULL） |
| type | Integer | type | 日期类型（枚举 HrmAttendanceHolidayTypeEnum，字典 hrm_attendance_holiday_type，默认 2） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmAttendanceClockDO (hrm_attendance_clock)

考勤打卡记录（上下班打卡流水）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 打卡记录编号，主键 |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id |
| clockTime | LocalDateTime | clock_time | 打卡时间（NOT NULL） |
| type | Integer | type | 打卡类型（枚举 HrmAttendanceClockTypeEnum，字典 hrm_attendance_clock_type，NOT NULL） |
| attendanceTime | LocalDateTime | attendance_time | 应打卡时间（NOT NULL） |
| sourceType | Integer | source_type | 打卡来源（枚举 HrmAttendanceClockSourceEnum，字典 hrm_attendance_clock_source，默认 2） |
| status | Integer | status | 打卡状态（枚举 HrmAttendanceClockStatusEnum，字典 hrm_attendance_clock_status，默认 0） |
| stage | Integer | stage | 打卡阶段（枚举 HrmAttendanceClockStageEnum，默认 1） |
| address | String | address | 打卡地址 |
| longitude | BigDecimal | longitude | 经度（decimal(10,6)） |
| latitude | BigDecimal | latitude | 纬度（decimal(10,6)） |
| ssid | String | ssid | WiFi 名称 |
| mac | String | mac | WiFi MAC 地址 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmAttendanceLeaveDO (hrm_attendance_leave)

考勤请假单，审批走 BPM 流程（`HrmAttendanceLeaveServiceImpl` 通过 `BpmProcessInstanceApi` 发起，`HrmAttendanceLeaveStatusListener` 监听流程结果回写状态）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 请假记录编号，主键 |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| type | String | type | 请假类型（字典 hrm_attendance_leave_type，varchar(64)） |
| startTime | LocalDateTime | start_time | 请假开始时间 |
| endTime | LocalDateTime | end_time | 请假结束时间 |
| day | BigDecimal | day | 请假时长（天，decimal(10,2)） |
| reason | String | reason | 请假理由（varchar(300)） |
| remark | String | remark | 备注 |
| approvalStatus | Integer | approval_status | 审批状态（BPM 的 BpmProcessInstanceStatusEnum，NOT NULL） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号（varchar(64)） |
| approvalTime | LocalDateTime | approval_time | 审批完成时间 |
| approvalReason | String | approval_reason | 审批或取消原因 |

**继承**: BaseDO
**索引**: 主键 id；唯一约束 `uk_hrm_attendance_leave_process_instance_id(process_instance_id)` —— 一条 BPM 流程实例唯一对应一张请假单

### 2.4 薪资聚合（salary，13 张表）

分为四层：配置层（计薪配置/薪资组/薪资项/计税规则/调薪模板）→ 员工定薪层（员工薪资信息 + 调薪记录）→ 月度核算层（月度工资表 + 员工月度工资）→ 工资条层（模板/发放批次/工资条）。薪资项体系采用「标准目录（全局）+ 企业自定义项（租户内）」两级设计。

#### HrmSalaryConfigDO (hrm_salary_config)

计薪配置（全局参数，每租户一条）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| cycleStartDay | Integer | cycle_start_day | 计薪周期开始日 |
| cycleEndDay | Integer | cycle_end_day | 计薪周期结束日 |
| socialSecurityMonthType | Integer | social_security_month_type | 社保对应月份类型（枚举 HrmSalarySocialSecurityMonthTypeEnum） |
| startYear | Integer | start_year | 工资开始年份 |
| startMonth | Integer | start_month | 工资开始月份 |

**继承**: BaseDO
**索引**: 主键 id；唯一约束 `uk_hrm_salary_config_tenant_id(tenant_id)` —— 每租户仅一条计薪配置

#### HrmSalaryGroupDO (hrm_salary_group)

薪资组（按部门/员工圈定适用范围并绑定计税规则）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| name | String | name | 薪资组名称（NOT NULL，varchar(64)） |
| salaryStandard | BigDecimal | salary_standard | 月计薪标准（decimal(12,2)，默认 21.75 天） |
| changeRule | String | change_rule | 转正、调薪月规则（默认“按转正/调薪前后的工资混合计算”） |
| deptIds | List\<Long\> | dept_ids | 适用部门编号列表，JacksonTypeHandler 存 JSON（varchar(20000)） |
| employeeIds | List\<Long\> | employee_ids | 适用员工编号列表，JacksonTypeHandler 存 JSON（varchar(20000)） |
| taxRuleId | Long | tax_rule_id | 计税规则，关联 hrm_salary_tax_rule.id |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalaryOptionDO (hrm_salary_option)

企业工资表薪资项（租户内树形目录，编码 code 自关联）。自定义薪资项编码从 `CUSTOM_OPTION_CODE_BASE = 1_000_000_000` 起，避免与预置目录冲突。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| templateId | Long | template_id | 来源标准薪资项，关联 hrm_salary_option_template.id（可空） |
| code | Integer | code | 薪资项编码（NOT NULL） |
| parentCode | Integer | parent_code | 父薪资项编码，自关联本表 code（NOT NULL，根节点为 0） |
| name | String | name | 薪资项名称（NOT NULL，varchar(64)） |
| remark | String | remark | 备注 |
| systemFlag | Boolean | system_flag | 是否系统默认项（默认 false） |
| type | Integer | type | 薪资项类型（枚举 HrmSalaryOptionTypeEnum，默认 1） |
| visible | Boolean | visible | 是否显示（默认 true） |
| enabled | Boolean | enabled | 是否启用（默认 true） |
| taxEnabled | Boolean | tax_enabled | 是否计税（默认 true） |
| calculateEnabled | Boolean | calculate_enabled | 是否参与计算（默认 true） |

**继承**: BaseDO
**索引**: 主键 id；唯一约束 `uk_hrm_salary_option_tenant_code(tenant_id, code)` —— 租户内编码唯一

#### HrmSalaryOptionTemplateDO (hrm_salary_option_template)

标准薪资项目录（全局共享，`@TenantIgnore`，无 tenant_id 列），作为各租户初始化薪资项的模板。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 标准薪资项编号，主键 |
| code | Integer | code | 薪资项编码（NOT NULL） |
| parentCode | Integer | parent_code | 父薪资项编码，自关联本表 code（NOT NULL，根节点为 0） |
| name | String | name | 薪资项名称（NOT NULL，varchar(64)） |
| remark | String | remark | 备注 |
| systemFlag | Boolean | system_flag | 是否系统默认项（默认 false） |
| type | Integer | type | 薪资项类型（枚举 HrmSalaryOptionTypeEnum，默认 1） |
| visible | Boolean | visible | 是否显示（默认 true） |
| taxEnabled | Boolean | tax_enabled | 是否计税（默认 true） |
| calculateEnabled | Boolean | calculate_enabled | 是否参与计算（默认 true） |

**继承**: BaseDO（类上另标注 `@TenantIgnore`，跳过租户隔离）
**索引**: 主键 id；唯一约束 `uk_hrm_salary_option_template_code(code)` —— 全局编码唯一

#### HrmSalaryTaxRuleDO (hrm_salary_tax_rule)

计税规则。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| name | String | name | 计税规则名称（NOT NULL，varchar(64)） |
| type | Integer | type | 计税类型（枚举 HrmSalaryTaxTypeEnum） |
| taxEnabled | Boolean | tax_enabled | 是否计税 |
| threshold | BigDecimal | threshold | 起征阈值（decimal(12,2)，FieldStrategy.ALWAYS 保证可更新为 null） |
| decimalScale | Integer | decimal_scale | 小数位数（FieldStrategy.ALWAYS） |
| cycleType | Integer | cycle_type | 计税周期类型（枚举 HrmSalaryTaxCycleTypeEnum，FieldStrategy.ALWAYS） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalaryChangeTemplateDO (hrm_salary_change_template)

调薪模板（预设调薪时可见/可改的薪资项集合）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 调薪模板编号，主键 |
| name | String | name | 模板名称（NOT NULL，varchar(64)） |
| defaultStatus | Boolean | default_status | 是否默认模板（默认 false） |
| options | List\<Option\> | options | 调薪项配置，JacksonTypeHandler 存 JSON（varchar(4000)）。Option 内嵌：name 薪资项名称快照、code 薪资项编码（关联 hrm_salary_option） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalaryEmployeeInfoDO (hrm_salary_employee_info)

员工当前薪资档案（每员工一条，1:1），正式/试用期两套薪资项整体以 JSON 快照维护。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| changeReason | Integer | change_reason | 定薪/调薪原因（枚举 HrmSalaryChangeReasonEnum） |
| effectTime | LocalDateTime | effect_time | 生效时间 |
| changeType | Integer | change_type | 薪资信息变更类型（枚举 HrmSalaryEmployeeInfoChangeTypeEnum） |
| probationSalary | BigDecimal | probation_salary | 试用期工资（decimal(12,2)） |
| regularSalary | BigDecimal | regular_salary | 正式工资（decimal(12,2)） |
| remark | String | remark | 备注 |
| salaryOptions | List\<SalaryOption\> | salary_options | 正式薪资项快照，JacksonTypeHandler 存 JSON（varchar(20000)）。SalaryOption 内嵌：code、name、value 金额 |
| probationSalaryOptions | List\<SalaryOption\> | probation_salary_options | 试用期薪资项快照，JacksonTypeHandler 存 JSON（varchar(20000)） |

**继承**: BaseDO
**索引**: 主键 id；唯一约束 `uk_hrm_salary_employee_info_employee_id(employee_id)` —— 每员工一条薪资档案

#### HrmSalaryChangeRecordDO (hrm_salary_change_record)

定薪/调薪记录（含调整前后金额与后态薪资项快照；到期生效由 `HrmSalaryChangeJob` 定时任务驱动，@TenantJob）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| type | Integer | type | 记录类型（枚举 HrmSalaryChangeRecordTypeEnum：定薪/调薪） |
| reason | Integer | reason | 调整原因（枚举 HrmSalaryChangeReasonEnum） |
| effectTime | LocalDateTime | effect_time | 生效时间 |
| beforeTotal | BigDecimal | before_total | 调整前正式薪资（decimal(12,2)） |
| afterTotal | BigDecimal | after_total | 调整后正式薪资（decimal(12,2)） |
| probationBeforeTotal | BigDecimal | probation_before_total | 调整前试用期薪资（decimal(12,2)） |
| probationAfterTotal | BigDecimal | probation_after_total | 调整后试用期薪资（decimal(12,2)） |
| salaryOptions | List\<SalaryOption\> | salary_options | 正式薪资项后态快照，JacksonTypeHandler 存 JSON（varchar(4000)） |
| probationSalaryOptions | List\<SalaryOption\> | probation_salary_options | 试用期薪资项后态快照，JacksonTypeHandler 存 JSON（varchar(4000)） |
| status | Integer | status | 状态（枚举 HrmSalaryChangeRecordStatusEnum） |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalaryMonthRecordDO (hrm_salary_month_record)

月度工资表（核算批次头表）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| title | String | title | 工资表标题（varchar(128)） |
| year | Integer | year | 年份（NOT NULL） |
| month | Integer | month | 月份（NOT NULL） |
| employeeCount | Integer | employee_count | 员工人数 |
| startTime | LocalDateTime | start_time | 计薪开始日期 |
| endTime | LocalDateTime | end_time | 计薪结束日期 |
| expectedPaySalary | BigDecimal | expected_pay_salary | 应发工资合计（decimal(12,2)） |
| personalTax | BigDecimal | personal_tax | 个人所得税合计（decimal(12,2)） |
| realPaySalary | BigDecimal | real_pay_salary | 实发工资合计（decimal(12,2)） |
| personalInsuranceAmount | BigDecimal | personal_insurance_amount | 个人社保金额合计（decimal(12,2)） |
| personalProvidentFundAmount | BigDecimal | personal_provident_fund_amount | 个人公积金金额合计（decimal(12,2)） |
| corporateInsuranceAmount | BigDecimal | corporate_insurance_amount | 公司社保金额合计（decimal(12,2)） |
| corporateProvidentFundAmount | BigDecimal | corporate_provident_fund_amount | 公司公积金金额合计（decimal(12,2)） |
| optionHeaders | List\<OptionHeader\> | option_headers | 薪资项表头快照，JacksonTypeHandler 存 JSON（varchar(20000)）。OptionHeader 内嵌：code、name、children 子薪资项（树形） |
| status | Integer | status | 状态（枚举 HrmSalaryMonthRecordStatusEnum） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalaryMonthEmployeeRecordDO (hrm_salary_month_employee_record)

员工月度工资记录（月度工资表明细行，一个批次多条）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| monthRecordId | Long | month_record_id | 月度工资表编号，关联 hrm_salary_month_record.id（NOT NULL） |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| actualWorkDay | BigDecimal | actual_work_day | 实际工作天数（decimal(10,2)） |
| needWorkDay | BigDecimal | need_work_day | 应工作天数（decimal(10,2)） |
| year | Integer | year | 年份（NOT NULL） |
| month | Integer | month | 月份（NOT NULL） |
| expectedPaySalary | BigDecimal | expected_pay_salary | 应发工资（decimal(12,2)） |
| taxableSalary | BigDecimal | taxable_salary | 应税工资（decimal(12,2)） |
| personalTax | BigDecimal | personal_tax | 个人所得税（decimal(12,2)） |
| realPaySalary | BigDecimal | real_pay_salary | 实发工资（decimal(12,2)） |
| optionValues | List\<OptionValue\> | option_values | 薪资项值快照，JacksonTypeHandler 存 JSON（varchar(20000)）。OptionValue 内嵌：code、name、value 金额 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalarySlipTemplateDO (hrm_salary_slip_template)

工资条模板（控制员工可见的薪资项及展示顺序，树形）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| name | String | name | 模板名称（NOT NULL，varchar(64)） |
| hideEmpty | Boolean | hide_empty | 是否隐藏空项（默认 false） |
| defaultStatus | Boolean | default_status | 是否默认模板（默认 false） |
| options | List\<Option\> | options | 工资条模板项，JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL），通过 Option.children 表达父子关系。Option 内嵌：name、type（枚举 HrmSalarySlipTemplateOptionTypeEnum）、code 薪资项编码、remark 说明、hidden 是否隐藏、sort 排序、children 子项 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalarySlipSendRecordDO (hrm_salary_slip_send_record)

工资条发放记录（同一月度工资表可分多批次发放，故为独立实体）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| monthRecordId | Long | month_record_id | 月度工资表编号，关联 hrm_salary_month_record.id（NOT NULL） |
| employeeCount | Integer | employee_count | 工资表总人数 |
| sendEmployeeCount | Integer | send_employee_count | 本批次发放人数 |
| year | Integer | year | 年份（NOT NULL） |
| month | Integer | month | 月份（NOT NULL） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmSalarySlipDO (hrm_salary_slip)

员工工资条（发放时按模板从员工月度工资记录生成快照）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| sendRecordId | Long | send_record_id | 发放记录编号，关联 hrm_salary_slip_send_record.id（NOT NULL） |
| monthEmployeeRecordId | Long | month_employee_record_id | 员工月度工资记录编号，关联 hrm_salary_month_employee_record.id（NOT NULL） |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| year | Integer | year | 年份（NOT NULL） |
| month | Integer | month | 月份（NOT NULL） |
| readStatus | Integer | read_status | 阅读状态（枚举 HrmSalarySlipReadStatusEnum） |
| realPaySalary | BigDecimal | real_pay_salary | 实发工资（decimal(12,2)） |
| remark | String | remark | 备注 |
| options | List\<Option\> | options | 工资条项快照，JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL），通过 Option.children 表达父子关系。Option 内嵌：name、type、code、value 金额、remark、sort、children |

**继承**: BaseDO
**索引**: 主键 id

### 2.5 社保聚合（insurance，5 张表）

方案（scheme）+ 方案项目（scheme_project）构成参保配置；员工参保信息 1:1 挂员工；月度社保表 + 员工月度社保记录为核算流水，项目明细以 JSON 快照固化。

#### HrmInsuranceSchemeDO (hrm_insurance_scheme)

社保方案（按参保地区 + 户籍类型定义）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| name | String | name | 方案名称（NOT NULL，varchar(64)） |
| areaId | Integer | area_id | 参保地区编号（框架 ip 模块 Area.id） |
| householdType | String | household_type | 户籍类型（varchar(64)） |
| type | Integer | type | 方案类型（枚举 HrmInsuranceSchemeTypeEnum，NOT NULL） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmInsuranceSchemeProjectDO (hrm_insurance_scheme_project)

社保方案项目（养老、医疗、公积金等单个险种的基数与比例）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| schemeId | Long | scheme_id | 社保方案编号，关联 hrm_insurance_scheme.id（NOT NULL） |
| type | Integer | type | 项目类型（枚举 HrmInsuranceProjectTypeEnum，NOT NULL） |
| name | String | name | 项目名称（NOT NULL，varchar(64)） |
| baseAmount | BigDecimal | base_amount | 缴纳基数（decimal(12,2)） |
| corporateRate | BigDecimal | corporate_rate | 公司缴纳比例（decimal(10,2)） |
| personalRate | BigDecimal | personal_rate | 个人缴纳比例（decimal(10,2)） |
| corporateAmount | BigDecimal | corporate_amount | 公司缴纳金额（decimal(12,2)） |
| personalAmount | BigDecimal | personal_amount | 个人缴纳金额（decimal(12,2)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmInsuranceEmployeeInfoDO (hrm_insurance_employee_info)

员工参保信息（每员工一条，1:1）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| firstSocialSecurity | Boolean | first_social_security | 是否首次参保（默认 false） |
| firstAccumulationFund | Boolean | first_accumulation_fund | 是否首次缴纳公积金（默认 false） |
| socialSecurityNumber | String | social_security_number | 社保账号（varchar(64)） |
| accumulationFundNumber | String | accumulation_fund_number | 公积金账号（varchar(64)） |
| socialSecurityStartMonth | LocalDateTime | social_security_start_month | 社保起缴月份 |
| schemeId | Long | scheme_id | 社保方案编号，关联 hrm_insurance_scheme.id |

**继承**: BaseDO
**索引**: 主键 id

#### HrmInsuranceMonthRecordDO (hrm_insurance_month_record)

月度社保表（核算批次头表）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| title | String | title | 标题（varchar(128)） |
| year | Integer | year | 年份（NOT NULL） |
| month | Integer | month | 月份（NOT NULL） |
| insuredEmployeeCount | Integer | insured_employee_count | 参保人数 |
| stoppedEmployeeCount | Integer | stopped_employee_count | 停保人数 |
| status | Integer | status | 状态（枚举 HrmInsuranceMonthStatusEnum） |
| personalInsuranceAmount | BigDecimal | personal_insurance_amount | 个人社保金额合计（decimal(12,2)） |
| personalProvidentFundAmount | BigDecimal | personal_provident_fund_amount | 个人公积金金额合计（decimal(12,2)） |
| corporateInsuranceAmount | BigDecimal | corporate_insurance_amount | 公司社保金额合计（decimal(12,2)） |
| corporateProvidentFundAmount | BigDecimal | corporate_provident_fund_amount | 公司公积金金额合计（decimal(12,2)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmInsuranceMonthEmployeeRecordDO (hrm_insurance_month_employee_record)

员工月度社保记录（月度社保表明细行，参保项目以 JSON 快照固化当期方案）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| monthRecordId | Long | month_record_id | 月度社保表编号，关联 hrm_insurance_month_record.id（NOT NULL） |
| employeeId | Long | employee_id | 员工编号，关联 hrm_employee.id（NOT NULL） |
| schemeId | Long | scheme_id | 社保方案编号，关联 hrm_insurance_scheme.id |
| year | Integer | year | 年份（NOT NULL） |
| month | Integer | month | 月份（NOT NULL） |
| personalInsuranceAmount | BigDecimal | personal_insurance_amount | 个人社保金额（decimal(12,2)） |
| personalProvidentFundAmount | BigDecimal | personal_provident_fund_amount | 个人公积金金额（decimal(12,2)） |
| corporateInsuranceAmount | BigDecimal | corporate_insurance_amount | 公司社保金额（decimal(12,2)） |
| corporateProvidentFundAmount | BigDecimal | corporate_provident_fund_amount | 公司公积金金额（decimal(12,2)） |
| status | Integer | status | 参保状态（枚举 HrmInsuranceEmployeeStatusEnum） |
| projects | List\<Project\> | projects | 参保项目快照，JacksonTypeHandler 存 JSON（varchar(10000)，NOT NULL）。Project 内嵌：schemeProjectId 来源方案项目编号、type、name、baseAmount、corporateRate、personalRate、corporateAmount、personalAmount |

**继承**: BaseDO
**索引**: 主键 id

### 2.6 绩效聚合（performance，10 张表）

考核模板与结果模板为配置，绩效计划引用模板并把配置固化为 JSON 快照；计划按考评范围为每个员工生成绩效考核单，其下挂阶段（评分流程）、维度、指标三级，指标评分记录 = 阶段 × 指标。

#### HrmPerformanceAssessmentTemplateDO (hrm_performance_assessment_template)

绩效考核模板（计分方式、分数上限、维度与指标配置）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考核模板编号，主键 |
| name | String | name | 模板名称（NOT NULL，varchar(500)） |
| illustrate | String | illustrate | 模板说明（varchar(1000)） |
| scoreCalculation | Integer | score_calculation | 计分方式（枚举 HrmPerformanceScoreCalculationEnum，默认 1） |
| upperLimitType | Integer | upper_limit_type | 分数上限类型（枚举 HrmPerformanceUpperLimitTypeEnum，默认 0） |
| upperLimitScore | BigDecimal | upper_limit_score | 分数上限（decimal(10,2)，默认 100.00） |
| dimensionCount | Integer | dimension_count | 维度数量（默认 0） |
| quotaCount | Integer | quota_count | 指标数量（默认 0） |
| dimensions | List\<Dimension\> | dimensions | 考核维度配置，JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL）。Dimension 内嵌：name、quotaType（枚举 HrmPerformanceQuotaTypeEnum）、weight、remark、allowEdit 是否允许员工编辑、quotas 考核指标列表。Quota 内嵌：name、illustrate、standard 评分标准、weight、scoreType（枚举 HrmPerformanceQuotaScoreTypeEnum）。另有 AssessmentConfig 快照结构（name + scoreCalculation + upperLimitType + upperLimitScore + dimensions）供计划引用时整体快照 |
| status | Integer | status | 状态（CommonStatusEnum，默认 0） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceResultTemplateDO (hrm_performance_result_template)

绩效结果模板（结果等级 + 绩效系数）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 结果模板编号，主键 |
| name | String | name | 模板名称（NOT NULL，varchar(255)） |
| status | Integer | status | 状态（CommonStatusEnum，默认 0） |
| levels | List\<Level\> | levels | 结果等级配置，JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL）。Level 内嵌：name 等级名称、minScore 最低分数、maxScore 最高分数、coefficient 绩效系数 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformancePlanDO (hrm_performance_plan)

绩效考核计划（配置 + 运行状态一体：基础设置/指标设置/流程设置/结果设置四段，模板配置以 JSON 快照固化）。阶段推进状态由 `stageType` + `operationType` 驱动，申诉超期由 `HrmPerformanceAppealTimeoutJob` 定时处理（@TenantJob）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 计划编号，主键 |
| status | Integer | status | 计划状态（枚举 HrmPerformancePlanStatusEnum，默认 2） |
| stageType | Integer | stage_type | 当前业务阶段类型（枚举 HrmPerformanceStageTypeEnum，默认 0） |
| operationType | Integer | operation_type | 当前可执行操作类型（枚举 HrmPerformancePlanOperationTypeEnum） |
| terminateTime | LocalDateTime | terminate_time | 终止时间 |
| name | String | name | 计划名称（NOT NULL，varchar(255)） |
| cycleType | Integer | cycle_type | 考核周期类型（枚举 HrmPerformanceCycleTypeEnum） |
| cycle | String | cycle | 考核周期（varchar(255)） |
| quarter | Integer | quarter | 季度（枚举 HrmPerformanceQuarterEnum） |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| description | String | description | 考核说明（varchar(1000)） |
| scopes | List\<Scope\> | scopes | 考评范围列表，JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL）。Scope 内嵌：type 范围类型（枚举 HrmPerformancePlanScopeTypeEnum）、employeeIds、deptIds、employeeType 聘用形式、employeeStatuses 员工状态列表 |
| assessmentTemplateId | Long | assessment_template_id | 考核模板，关联 hrm_performance_assessment_template.id（NOT NULL） |
| assessmentConfig | AssessmentConfig | assessment_config | 考核配置快照（模板内容的 JSON 固化），JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL） |
| quotaSettingType | Integer | quota_setting_type | 指标制定类型（枚举 HrmPerformanceQuotaSettingTypeEnum，默认 1） |
| targetConfirmation | Boolean | target_confirmation | 是否开启目标确认（默认 false） |
| targetConfirmationStage | HandlerStage | target_confirmation_stage | 目标确认节点，JacksonTypeHandler 存 JSON。HandlerStage 内嵌：type 处理人类型（枚举 HrmPerformanceRaterTypeEnum）、level 上级/部门层级、employeeId 指定处理员工 |
| reviewStages | List\<ReviewStage\> | review_stages | 评分阶段列表，JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL）。ReviewStage 内嵌：name、rater 评分人（HandlerStage）、weight 评分权重、scoringType 评分方式、visibleContent 评分内容可见范围、requiredSetting 评语必填、rejectAuthority 是否允许驳回 |
| resultAudit | Boolean | result_audit | 是否开启结果审核（默认 true） |
| resultAuditStages | List\<HandlerStage\> | result_audit_stages | 结果审核节点列表，JacksonTypeHandler 存 JSON |
| resultConfirmation | Boolean | result_confirmation | 是否开启结果确认（默认 true） |
| appealStages | List\<HandlerStage\> | appeal_stages | 申诉处理节点列表，JacksonTypeHandler 存 JSON |
| appealTimeoutDays | Integer | appeal_timeout_days | 申诉超期天数（NOT NULL，默认 2） |
| appealTimeoutAction | Integer | appeal_timeout_action | 申诉超期处理动作（枚举 HrmPerformanceAppealTimeoutActionEnum，NOT NULL，默认 1） |
| resultTemplateId | Long | result_template_id | 结果模板，关联 hrm_performance_result_template.id（NOT NULL） |
| resultConfig | ResultConfig | result_config | 结果配置快照（模板名称 + 结果等级 levels），JacksonTypeHandler 存 JSON（varchar(20000)，NOT NULL） |
| syncToSalary | Boolean | sync_to_salary | 是否同步到薪资（默认 false） |
| paidForMonth | String | paid_for_month | 计薪月份（varchar(20)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentDO (hrm_performance_assessment)

员工绩效考核单（计划 × 员工一行，承载目标确认/自评/他评/结果审核/申诉/归档全过程状态）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 员工绩效考核编号，主键 |
| planId | Long | plan_id | 绩效计划，关联 hrm_performance_plan.id（NOT NULL） |
| employeeId | Long | employee_id | 员工，关联 hrm_employee.id（NOT NULL） |
| status | Integer | status | 考核状态（枚举 HrmPerformancePlanStatusEnum，默认 2） |
| processStatus | Integer | process_status | 流程处理状态（枚举 HrmPerformanceAssessmentProcessStatusEnum，默认 1） |
| stageType | Integer | stage_type | 当前业务阶段类型（枚举 HrmPerformanceStageTypeEnum，默认 0） |
| stageSort | Integer | stage_sort | 当前阶段排序（默认 0） |
| score | BigDecimal | score | 综合得分（decimal(10,2)，默认 0.00） |
| resultLevel | String | result_level | 结果等级（varchar(64)） |
| coefficient | BigDecimal | coefficient | 绩效系数（decimal(10,2)，默认 1.00） |
| targetConfirmationResult | Integer | target_confirmation_result | 目标确认结果（枚举 HrmPerformanceConfirmationResultEnum） |
| targetConfirmationComment | String | target_confirmation_comment | 目标确认意见（varchar(1000)） |
| targetConfirmationTime | LocalDateTime | target_confirmation_time | 目标确认时间 |
| selfComment | String | self_comment | 自评说明（varchar(2000)） |
| reviewerComment | String | reviewer_comment | 他评说明（varchar(2000)） |
| resultComment | String | result_comment | 结果说明（varchar(2000)） |
| resultConfirmationTime | LocalDateTime | result_confirmation_time | 结果确认时间 |
| resultAuditStatus | Integer | result_audit_status | 结果审核状态（枚举 HrmPerformanceResultAuditStatusEnum） |
| resultAuditTime | LocalDateTime | result_audit_time | 结果审核时间 |
| resultAuditReason | String | result_audit_reason | 结果审核意见（varchar(1000)） |
| appealReason | String | appeal_reason | 申诉原因（varchar(1000)） |
| appealFileUrls | List\<String\> | appeal_file_urls | 申诉附件地址列表，StringListTypeHandler 存 JSON（varchar(2000)） |
| appealSubmitTime | LocalDateTime | appeal_submit_time | 申诉提交时间 |
| appealStatus | Integer | appeal_status | 申诉状态（枚举 HrmPerformanceAppealStatusEnum，默认 0） |
| appealTime | LocalDateTime | appeal_time | 申诉完成时间 |
| appealComment | String | appeal_comment | 申诉处理意见（varchar(1000)） |
| archiveTime | LocalDateTime | archive_time | 归档时间 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentStageDO (hrm_performance_assessment_stage)

员工绩效考核阶段（自评/他评/结果审核/申诉处理等流程节点实例，规则从计划快照而来）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考核阶段编号，主键 |
| assessmentId | Long | assessment_id | 员工绩效考核，关联 hrm_performance_assessment.id（NOT NULL） |
| type | Integer | type | 业务阶段类型（枚举 HrmPerformanceStageTypeEnum，NOT NULL） |
| name | String | name | 阶段名称（NOT NULL，varchar(128)） |
| handlerEmployeeId | Long | handler_employee_id | 实际处理员工编号，关联 hrm_employee.id |
| raterType | Integer | rater_type | 评分人类型（枚举 HrmPerformanceRaterTypeEnum） |
| weight | BigDecimal | weight | 评分权重快照（decimal(10,2)） |
| scoringType | Integer | scoring_type | 评分方式快照（枚举 HrmPerformanceReviewScoringTypeEnum） |
| visibleContent | Integer | visible_content | 评分内容可见范围快照（枚举 HrmPerformanceReviewVisibleContentEnum） |
| requiredSetting | Boolean | required_setting | 评语是否必填 |
| rejectAuthority | Boolean | reject_authority | 是否允许驳回 |
| sort | Integer | sort | 排序（NOT NULL，默认 0） |
| status | Integer | status | 阶段处理状态（枚举 HrmPerformanceAssessmentStageStatusEnum，NOT NULL，默认 0） |
| score | BigDecimal | score | 阶段汇总得分（decimal(10,2)） |
| resultLevel | String | result_level | 阶段结果等级（varchar(64)） |
| comment | String | comment | 阶段意见（varchar(2000)） |
| rejectReason | String | reject_reason | 最近一次驳回原因（varchar(1000)） |
| submitTime | LocalDateTime | submit_time | 提交时间 |
| deadlineTime | LocalDateTime | deadline_time | 截止时间 |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentDimensionDO (hrm_performance_assessment_dimension)

员工绩效考核维度（模板维度实例化到考核单）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考核维度编号，主键 |
| assessmentId | Long | assessment_id | 员工绩效考核，关联 hrm_performance_assessment.id（NOT NULL） |
| name | String | name | 维度名称（NOT NULL，varchar(255)） |
| quotaType | Integer | quota_type | 指标类型（枚举 HrmPerformanceQuotaTypeEnum） |
| weight | BigDecimal | weight | 维度权重（decimal(10,2)） |
| remark | String | remark | 备注（varchar(255)） |
| allowEdit | Boolean | allow_edit | 是否允许员工编辑指标（NOT NULL，默认 false） |
| sort | Integer | sort | 排序（NOT NULL，默认 0） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentQuotaDO (hrm_performance_assessment_quota)

员工绩效考核指标（维度下挂指标，含目标值/实际值与自评/他评/最终得分汇总）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考核指标编号，主键 |
| assessmentId | Long | assessment_id | 员工绩效考核，关联 hrm_performance_assessment.id（NOT NULL） |
| dimensionId | Long | dimension_id | 考核维度，关联 hrm_performance_assessment_dimension.id（NOT NULL） |
| preset | Boolean | preset | 是否预置指标（NOT NULL，默认 true） |
| name | String | name | 指标名称（varchar(255)） |
| description | String | description | 指标说明（varchar(1000)） |
| standard | String | standard | 评分标准（varchar(1000)） |
| weight | BigDecimal | weight | 指标权重（decimal(10,2)，默认 100.00） |
| scoreType | Integer | score_type | 评分类型（枚举 HrmPerformanceQuotaScoreTypeEnum） |
| targetValue | String | target_value | 目标值（varchar(1000)） |
| actualValue | String | actual_value | 实际值（varchar(1000)） |
| selfScore | BigDecimal | self_score | 自评汇总分（decimal(10,2)，默认 0.00） |
| reviewerScore | BigDecimal | reviewer_score | 他评汇总分（decimal(10,2)，默认 0.00） |
| finalScore | BigDecimal | final_score | 最终指标得分（decimal(10,2)，默认 0.00） |
| sort | Integer | sort | 排序（默认 0） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentQuotaScoreDO (hrm_performance_assessment_quota_score)

员工绩效考核指标评分（评分阶段 × 考核指标一条评分记录）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考核指标评分编号，主键 |
| assessmentStageId | Long | assessment_stage_id | 考核阶段，关联 hrm_performance_assessment_stage.id（NOT NULL） |
| assessmentQuotaId | Long | assessment_quota_id | 考核指标，关联 hrm_performance_assessment_quota.id（NOT NULL） |
| score | BigDecimal | score | 指标得分（decimal(10,2)，NOT NULL） |
| comment | String | comment | 指标评语（varchar(1000)） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentActionRecordDO (hrm_performance_assessment_action_record)

员工绩效考核动作记录（提交、驳回、确认等操作留痕）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 动作记录编号，主键 |
| assessmentId | Long | assessment_id | 员工绩效考核，关联 hrm_performance_assessment.id（NOT NULL） |
| stageId | Long | stage_id | 考核阶段，关联 hrm_performance_assessment_stage.id |
| employeeId | Long | employee_id | 操作员工编号，关联 hrm_employee.id |
| type | Integer | type | 动作类型（枚举 HrmPerformanceAssessmentActionTypeEnum，NOT NULL） |
| title | String | title | 动作标题（NOT NULL，varchar(128)） |
| content | String | content | 动作内容（varchar(2000)） |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JacksonTypeHandler 存 JSON（varchar(2000)） |
| status | Integer | status | 动作完成后的阶段状态（枚举 HrmPerformanceAssessmentStageStatusEnum） |

**继承**: BaseDO
**索引**: 主键 id

#### HrmPerformanceAssessmentAppealRecordDO (hrm_performance_assessment_appeal_record)

员工绩效考核申诉记录（申诉处理节点流转记录）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 申诉记录编号，主键 |
| assessmentId | Long | assessment_id | 员工绩效考核，关联 hrm_performance_assessment.id（NOT NULL） |
| stageId | Long | stage_id | 考核阶段，关联 hrm_performance_assessment_stage.id（NOT NULL） |
| status | Integer | status | 处理状态（枚举 HrmPerformanceAppealRecordStatusEnum，NOT NULL） |

**继承**: BaseDO
**索引**: 主键 id

### 2.7 通用配置（config，1 张表）

#### HrmConfigDO (hrm_config)

HRM 通用业务配置（键值对，type 区分用途，如首页/门户的功能开关）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键 |
| type | Integer | type | 配置类型（枚举 HrmConfigTypeEnum，NOT NULL） |
| value | String | value | 配置值（NOT NULL，varchar(255)） |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 主键 id

## 3. 实体关系

全模块以 `hrm_employee` 为中心：所有从表通过 `employee_id` 逻辑外键关联员工主档（无物理外键约束，关联完整性由 Service 层保证）。

```
                                    system_users(AdminUserDO)   system_dept(DeptDO)
                                            ^ user_id                  ^ dept_id
                                            |                          |
  hrm_recruit_post_type(树,自关联 parent_id) <── post_type_id ── hrm_recruit_post
  hrm_recruit_channel <── channel_id ──┐       ^ post_id
                                       │       |
                                       │  hrm_recruit_candidate ──< hrm_recruit_interview(candidate_id)
                                       │       ^     (候选人转正入职)
                                       │       └── candidate_id ──┐
                                       └── channel_id ──> ┌──────────────────┐
                                                          │   hrm_employee   │ ←──── 全模块主档
                                                          └──────────────────┘
        ┌──────────────┬───────────────┬───────────────┬──────────────┬───────────────┐
     employee_id   employee_id     employee_id     employee_id    employee_id     employee_id
          │              │               │               │              │               │
  hrm_employee_contact  hrm_employee_file  hrm_employee_personal_note  hrm_employee_salary_card(1:1)
  hrm_employee_education_experience / work_experience / training_experience / certificate
  hrm_employee_change_record(old/new_dept_id、old/new_leader_employee_id 自关联 hrm_employee)
  hrm_employee_contract(file_urls JSON)   hrm_employee_quit_info(1:1 一次离职)

  考勤域：
  hrm_attendance_group(dept_ids/employee_ids/shifts/points/wifis/deduct_rule JSON)   hrm_attendance_holiday
        └── employee_id ──> hrm_attendance_clock(打卡流水，含经纬度/WiFi)
        └── employee_id ──> hrm_attendance_leave ── process_instance_id ──> BPM 流程实例(审批回写)

  薪资域：
  hrm_salary_option_template(全局 @TenantIgnore, code 唯一)
        └── template_id ──> hrm_salary_option(tenant_id+code 唯一, parent_code 自关联成树)
  hrm_salary_config(tenant_id 唯一, 每租户一条)
  hrm_salary_tax_rule <── tax_rule_id ── hrm_salary_group(dept_ids/employee_ids JSON)
  hrm_salary_employee_info(1:1 员工当前薪资档案, employee_id 唯一) <── employee_id ── hrm_salary_change_record
  hrm_salary_month_record(option_headers JSON 表头快照)
        └── month_record_id ──> hrm_salary_month_employee_record(option_values JSON 值快照)
        └── month_record_id ──> hrm_salary_slip_send_record(可多批次)
                                     └── send_record_id ──> hrm_salary_slip(工资条, options JSON)
                                             └── month_employee_record_id ──> hrm_salary_month_employee_record

  社保域：
  hrm_insurance_scheme ──< hrm_insurance_scheme_project(scheme_id)
        ├── scheme_id ──> hrm_insurance_employee_info(1:1 员工参保档案)
        └── scheme_id ──> hrm_insurance_month_employee_record.projects(项目 JSON 快照引用 scheme_project_id)
  hrm_insurance_month_record ──< hrm_insurance_month_employee_record(month_record_id)

  绩效域：
  hrm_performance_assessment_template ── assessment_template_id + assessment_config(JSON 快照) ──> hrm_performance_plan
  hrm_performance_result_template   ── result_template_id   + result_config(JSON 快照)   ──> hrm_performance_plan
  hrm_performance_plan(scopes/review_stages/... JSON) ──< hrm_performance_assessment(plan_id, plan×员工)
        └── assessment_id ──> hrm_performance_assessment_stage(阶段)
        └── assessment_id ──> hrm_performance_assessment_dimension(维度)
                                   └── dimension_id ──> hrm_performance_assessment_quota(指标)
        └── assessment_id ──> hrm_performance_assessment_action_record(动作留痕, 另含 stage_id/employee_id)
        └── assessment_id ──> hrm_performance_assessment_appeal_record(申诉, 另含 stage_id)
  阶段×指标评分：hrm_performance_assessment_quota_score(assessment_stage_id + assessment_quota_id)
```

要点说明：

1. **员工 ↔ 各从表**：1:N（联系人、附件、三类经历、证书、异动记录、合同、调薪记录等）；工资卡、离职信息、当前薪资档案、参保信息为业务上 1:1（其中 `hrm_salary_employee_info.employee_id` 有唯一约束）。
2. **招聘 → 员工**：候选人入职转化时 `hrm_employee.candidate_id`、`channel_id` 分别回指 `hrm_recruit_candidate`、`hrm_recruit_channel`，招聘链路与员工档案通过这两个弱外键衔接。
3. **考勤 → BPM**：`hrm_attendance_leave.process_instance_id` 关联 BPM 流程实例并有唯一约束，请假审批状态由 `HrmAttendanceLeaveStatusListener`（BpmProcessInstanceStatusEventListener）回写。
4. **配置快照模式**：绩效模板、结果模板、薪资项、社保项目等配置在被计划/工资表/工资条/月度社保引用时，均以 JSON 快照整体固化到目标表，后续修改模板不影响已生成的历史数据；这也是大量字段无法用 SQL 直接过滤的原因。
5. **树形自关联**：`hrm_recruit_post_type.parent_id`、`hrm_salary_option.parent_code`、`hrm_salary_option_template.parent_code`、`hrm_employee.leader_employee_id`（员工自关联直属上级）。
6. **跨模块引用**：system_users（user_id）、system_dept（dept_id）、框架 ip 模块 Area（area_id/bank_area_id）、BPM 流程实例（process_instance_id），均为逻辑外键。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|----|------|
| hrm_employee | HrmEmployeeDO | 员工档案主档 |
| hrm_employee_contact | HrmEmployeeContactDO | 员工联系人 |
| hrm_employee_file | HrmEmployeeFileDO | 员工材料附件 |
| hrm_employee_personal_note | HrmEmployeePersonalNoteDO | 员工个人备忘 |
| hrm_employee_change_record | HrmEmployeeChangeRecordDO | 员工异动记录（定时任务生效） |
| hrm_employee_contract | HrmEmployeeContractDO | 员工合同 |
| hrm_employee_quit_info | HrmEmployeeQuitInfoDO | 员工离职信息 |
| hrm_employee_salary_card | HrmEmployeeSalaryCardDO | 员工工资卡 |
| hrm_employee_education_experience | HrmEmployeeEducationExperienceDO | 员工教育经历 |
| hrm_employee_work_experience | HrmEmployeeWorkExperienceDO | 员工工作经历 |
| hrm_employee_training_experience | HrmEmployeeTrainingExperienceDO | 员工培训经历 |
| hrm_employee_certificate | HrmEmployeeCertificateDO | 员工证书 |
| hrm_recruit_post | HrmRecruitPostDO | 招聘职位 |
| hrm_recruit_post_type | HrmRecruitPostTypeDO | 招聘职位类型（树形） |
| hrm_recruit_channel | HrmRecruitChannelDO | 招聘渠道 |
| hrm_recruit_candidate | HrmRecruitCandidateDO | 招聘候选人 |
| hrm_recruit_interview | HrmRecruitInterviewDO | 招聘面试记录 |
| hrm_attendance_group | HrmAttendanceGroupDO | 考勤组（班次/打卡/扣款规则 JSON） |
| hrm_attendance_holiday | HrmAttendanceHolidayDO | 考勤节假日 |
| hrm_attendance_clock | HrmAttendanceClockDO | 考勤打卡记录 |
| hrm_attendance_leave | HrmAttendanceLeaveDO | 考勤请假（BPM 审批） |
| hrm_salary_config | HrmSalaryConfigDO | 计薪配置（每租户一条） |
| hrm_salary_group | HrmSalaryGroupDO | 薪资组 |
| hrm_salary_option | HrmSalaryOptionDO | 企业工资表薪资项（租户内树形） |
| hrm_salary_option_template | HrmSalaryOptionTemplateDO | 标准薪资项目录（全局共享，@TenantIgnore） |
| hrm_salary_tax_rule | HrmSalaryTaxRuleDO | 计税规则 |
| hrm_salary_change_template | HrmSalaryChangeTemplateDO | 调薪模板 |
| hrm_salary_employee_info | HrmSalaryEmployeeInfoDO | 员工当前薪资档案（1:1） |
| hrm_salary_change_record | HrmSalaryChangeRecordDO | 定薪/调薪记录 |
| hrm_salary_month_record | HrmSalaryMonthRecordDO | 月度工资表（批次头） |
| hrm_salary_month_employee_record | HrmSalaryMonthEmployeeRecordDO | 员工月度工资记录（明细行） |
| hrm_salary_slip_template | HrmSalarySlipTemplateDO | 工资条模板 |
| hrm_salary_slip_send_record | HrmSalarySlipSendRecordDO | 工资条发放记录（批次） |
| hrm_salary_slip | HrmSalarySlipDO | 员工工资条 |
| hrm_insurance_scheme | HrmInsuranceSchemeDO | 社保方案 |
| hrm_insurance_scheme_project | HrmInsuranceSchemeProjectDO | 社保方案项目 |
| hrm_insurance_employee_info | HrmInsuranceEmployeeInfoDO | 员工参保信息（1:1） |
| hrm_insurance_month_record | HrmInsuranceMonthRecordDO | 月度社保表（批次头） |
| hrm_insurance_month_employee_record | HrmInsuranceMonthEmployeeRecordDO | 员工月度社保记录（明细行，项目 JSON 快照） |
| hrm_performance_assessment_template | HrmPerformanceAssessmentTemplateDO | 绩效考核模板 |
| hrm_performance_result_template | HrmPerformanceResultTemplateDO | 绩效结果模板 |
| hrm_performance_plan | HrmPerformancePlanDO | 绩效考核计划 |
| hrm_performance_assessment | HrmPerformanceAssessmentDO | 员工绩效考核单（计划×员工） |
| hrm_performance_assessment_stage | HrmPerformanceAssessmentStageDO | 员工绩效考核阶段 |
| hrm_performance_assessment_dimension | HrmPerformanceAssessmentDimensionDO | 员工绩效考核维度 |
| hrm_performance_assessment_quota | HrmPerformanceAssessmentQuotaDO | 员工绩效考核指标 |
| hrm_performance_assessment_quota_score | HrmPerformanceAssessmentQuotaScoreDO | 员工绩效考核指标评分（阶段×指标） |
| hrm_performance_assessment_action_record | HrmPerformanceAssessmentActionRecordDO | 员工绩效考核动作记录 |
| hrm_performance_assessment_appeal_record | HrmPerformanceAssessmentAppealRecordDO | 员工绩效考核申诉记录 |
| hrm_config | HrmConfigDO | 通用业务配置（键值对） |
