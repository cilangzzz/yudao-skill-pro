# 人力资源管理模块 (hrm)

> 一体化人力资源管理系统（HRM）：员工档案与生命周期、招聘、考勤、薪资、社保、绩效，配套 HR 工作台与员工自助门户。

## 模块概述

- **模块路径**: `yudao-module-hrm`（单模块，非多子模块布局）
- **业务定位**: 覆盖 HR 全流程 —— 员工建档与异动（入职/转正/调岗/晋升/离职）、招聘职位与候选人管理、考勤组与打卡/请假、薪资组与月度工资核算、社保方案与月度社保表、绩效考核计划与阶段流转。同时提供 HR 工作台统计与员工自助门户（手机打卡、查工资条、查社保、办理请假等）。
- **技术栈**: Spring Boot 2.7.18（仓库 2026.09-jdk8 分支，Java 8）/ MyBatis-Plus（`yudao-spring-boot-starter-mybatis`）/ Quartz（`yudao-spring-boot-starter-job`）/ EasyExcel（`yudao-spring-boot-starter-excel`）/ Spring Security 权限注解 / mzt-biz-log `@LogRecord` 操作日志

> 注意：本模块在根 `pom.xml` 与 `yudao-server/pom.xml` 中默认被注释禁用，使用时需手动开启依赖并导入表结构。

## 设计原则

| 原则 | 说明 |
|-----|------|
| 域内细分三层 | 单模块但按业务域划分包：`controller/admin/{域}`、`service/{域}/{子域}`、`dal/dataobject/{域}/{子域}`，如 attendance 再分 config/record/statistics |
| 复杂配置 JSON 化 | 考勤组班次/打卡点/WiFi/扣罚规则、薪资项 Option、绩效阶段/评分配置等以 TypeHandler JSON 列存储（如 `HrmAttendanceGroupDO.shifts`），避免大量子表 |
| 状态机式流转 | 员工生命周期（待入职/在职/待离职/离职）、招聘候选人状态、绩效阶段流转均由 `status` 字段 + 错误码严格约束合法流转 |
| 与 BPM 松耦合集成 | 请假审批通过 `BpmProcessInstanceApi` 发起流程，`HrmAttendanceLeaveStatusListener` 监听流程状态事件回写审批结果 |
| 月度快照不可变 | 工资表/社保表按月生成快照记录，仅允许删除最新月份，历史数据只读 |
| 统一操作留痕 | 核心写操作均加 `@LogRecord` 注解，操作日志经 system 模块 `OperateLogApi` 查询 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 员工管理 | 员工档案、联系人、合同、工资卡、异动记录、离职信息、教育/工作/培训经历、证书、材料附件、字段配置，支持批量建档/导入导出/生命周期办理 | HrmEmployeeDO、HrmEmployeeChangeRecordDO |
| 招聘管理 | 招聘职位与职位类型、招聘渠道、候选人（状态流转/淘汰/转员工）、面试安排与结果、淘汰原因配置 | HrmRecruitPostDO、HrmRecruitCandidateDO、HrmRecruitInterviewDO |
| 考勤管理 | 考勤组（班次/打卡点/WiFi/扣罚规则）、节假日、打卡记录（GPS/WiFi 校验）、请假审批（对接 BPM）、月度考勤统计与导出 | HrmAttendanceGroupDO、HrmAttendanceClockDO、HrmAttendanceLeaveDO |
| 薪资管理 | 薪资配置/薪资组/薪资项/计税规则/调薪模板、员工薪资档案与定薪调薪、月度工资表核算与导入、工资条发放与阅读状态 | HrmSalaryEmployeeInfoDO、HrmSalaryMonthRecordDO、HrmSalarySlipDO |
| 社保管理 | 社保方案与参保项目、员工参保信息、月度社保表（首月/次月创建）、员工月度参保项目调整与停缴 | HrmInsuranceSchemeDO、HrmInsuranceMonthRecordDO |
| 绩效管理 | 考核模板/结果模板、绩效计划（启动/评分/面谈/归档/终止）、员工绩效考核与多阶段评分、申诉、绩效归档，结果可同步薪资系数 | HrmPerformancePlanDO、HrmPerformanceAssessmentDO |
| 工作台 | HR 工作台与团队工作台的统计摘要和日历 | 无独立 DO（聚合查询） |
| 员工自助门户 | 员工端（portal）自助：档案查看/更新、打卡、请假、查工资条/社保、绩效任务处理与申诉 | 复用各域 DO |
| 操作日志 | 查询 HRM 业务操作日志（转发 system 模块 OperateLogApi） | 无本地 DO |
| 通用配置 | HRM 通用键值业务配置（如招聘淘汰原因、员工字段配置载体） | HrmConfigDO |

## API 接口索引

> 全模块共 **311** 个端点（62 个 Controller，全部位于 `controller/admin`，无 `controller/app`）。端点数超过 120，按域分节给出控制器摘要与代表性端点，完整明细见 `api-{key}.md`。

### 员工管理（employee）— 13 个 Controller，63 端点，详见 [api-employee.md](api-employee.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmEmployeeController | 员工档案：建档/批量建档/导入导出/入职转正调岗晋升离职等生命周期办理 | 26 |
| HrmEmployeeFieldConfigController | 新建员工/员工档案字段配置 | 4 |
| HrmEmployeeEducationExperienceController | 教育经历 CRUD | 4 |
| HrmEmployeeWorkExperienceController | 工作经历 CRUD | 4 |
| HrmEmployeeTrainingExperienceController | 培训经历 CRUD | 4 |
| HrmEmployeeCertificateController | 证书 CRUD | 4 |
| HrmEmployeeContactController | 联系人 CRUD | 4 |
| HrmEmployeeContractController | 合同 CRUD | 4 |
| HrmEmployeeChangeRecordController | 异动记录列表 | 1 |
| HrmEmployeeQuitInfoController | 离职信息查询 | 1 |
| HrmEmployeeSalaryCardController | 工资卡查询/保存/删除 | 3 |
| HrmEmployeeFileController | 材料附件列表/保存 | 2 |
| HrmEmployeePersonalNoteController | 个人备忘创建/删除 | 2 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/employee/create | POST | 创建员工档案 | `hrm:employee:create` |
| /hrm/employee/confirm-entry | PUT | 确认员工入职 | `hrm:employee:update` |
| /hrm/employee/quit | POST | 办理员工离职 | `hrm:employee:update` |
| /hrm/employee/page | GET | 获得员工档案分页 | `hrm:employee:query` |
| /hrm/employee/import | POST | 导入员工档案 | `hrm:employee:import` |
| /hrm/employee/simple-list | GET | 员工精简列表（选择器） | 已认证（无 @PreAuthorize） |

### 招聘管理（recruit）— 6 个 Controller，35 端点，详见 [api-recruit.md](api-recruit.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmRecruitPostController | 招聘职位 CRUD/状态/精简列表/状态统计 | 7 |
| HrmRecruitCandidateController | 候选人 CRUD/状态流转/淘汰/转员工/清理 | 12 |
| HrmRecruitInterviewController | 面试安排/结果/按候选人列表 | 6 |
| HrmRecruitChannelController | 招聘渠道 CRUD/状态/精简列表 | 7 |
| HrmRecruitPostTypeController | 职位类型列表 | 1 |
| HrmRecruitConfigController | 淘汰原因保存/列表 | 2 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/recruit/candidate/convert-employee | POST | 候选人转员工档案 | `hrm:recruit:candidate:update` |
| /hrm/recruit/candidate/eliminate | PUT | 淘汰招聘候选人 | `hrm:recruit:candidate:update` |
| /hrm/recruit/interview/update-result | PUT | 更新招聘面试结果 | `hrm:recruit:interview:update` |
| /hrm/recruit/post/page | GET | 获得招聘职位分页 | `hrm:recruit:post:query` |
| /hrm/recruit/channel/simple-list | GET | 招聘渠道精简列表 | `hrm:recruit:channel:query` |

### 考勤管理（attendance）— 5 个 Controller，30 端点，详见 [api-attendance.md](api-attendance.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmAttendanceGroupController | 考勤组 CRUD/我的考勤组/精简列表 | 7 |
| HrmAttendanceClockController | 打卡记录 CRUD/批量删除/班次窗口/导出 | 8 |
| HrmAttendanceLeaveController | 请假查询/分页/导出（创建走 portal） | 3 |
| HrmAttendanceHolidayController | 节假日 CRUD/日期检查 | 6 |
| HrmAttendanceStatisticsController | 每日打卡明细/月度汇总/月度概况/导出/月度详情 | 6 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/attendance/clock/get-shift | GET | 获得员工实际班次和允许打卡时间 | `hrm:attendance:clock:create` 或 `hrm:attendance:clock:update` |
| /hrm/attendance/leave/get | GET | 获得请假 | `hrm:attendance:leave:query` 或 `hrm:attendance:clock:query` |
| /hrm/attendance/statistics/month-record-page | GET | 查询员工月度考勤汇总 | `hrm:attendance:statistics:query` |
| /hrm/attendance/group/my | GET | 获得员工所在考勤组 | `hrm:attendance:group:query` |

### 薪资管理（salary）— 12 个 Controller，71 端点，详见 [api-salary.md](api-salary.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmSalaryConfigController | 薪资配置创建/更新/查询 | 3 |
| HrmSalaryGroupController | 薪资组 CRUD/精简列表 | 6 |
| HrmSalaryOptionController | 薪资项 CRUD/启停/显隐/同步标准项 | 7 |
| HrmSalaryTaxRuleController | 计税规则 CRUD/列表 | 5 |
| HrmSalaryChangeTemplateController | 调薪模板 CRUD/列表 | 5 |
| HrmSalaryEmployeeInfoController | 薪资档案分页/定薪调薪/批量调薪/导入 | 10 |
| HrmSalaryChangeRecordController | 定薪调薪记录查询/取消/删除 | 4 |
| HrmSalaryMonthRecordController | 月度工资表创建/核算/导入模板/准备度/汇总 | 12 |
| HrmSalaryMonthEmployeeRecordController | 员工月度工资分页/批量修改/绩效系数 | 6 |
| HrmSalarySlipTemplateController | 工资条模板 CRUD/列表 | 5 |
| HrmSalarySlipController | 工资条分页/详情/备注 | 3 |
| HrmSalarySlipSendRecordController | 工资条发放/待发员工/发放记录管理 | 5 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/salary/employee-info/update-list | PUT | 批量调薪 | `hrm:salary:employee-info:update` |
| /hrm/salary/month-record/compute | POST | 核算工资表 | `hrm:salary:month-record:update` |
| /hrm/salary/month-record/compute-import | POST | 带导入文件核算工资表 | `hrm:salary:month-record:update` |
| /hrm/salary/slip-send-record/create | POST | 发放工资条 | `hrm:salary:slip:create` |
| /hrm/salary/option/sync | PUT | 同步标准薪资项 | `hrm:salary:option:update` |

### 社保管理（insurance）— 5 个 Controller，23 端点，详见 [api-insurance.md](api-insurance.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmInsuranceSchemeController | 社保方案 CRUD/列表/精简列表 | 6 |
| HrmInsuranceStandardController | 标准参保类型/项目列表 | 2 |
| HrmInsuranceEmployeeInfoController | 员工参保信息查询/保存/换方案 | 3 |
| HrmInsuranceMonthRecordController | 月度社保表首月/次月创建/删除/查询 | 6 |
| HrmInsuranceMonthEmployeeRecordController | 员工月度社保分页/调项/停缴/添加参保 | 6 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/insurance/month-record/create-next | POST | 创建下月社保表 | `hrm:insurance:month-record:create` |
| /hrm/insurance/month-employee-record/stop-list | PUT | 批量停止员工参保 | `hrm:insurance:month-employee-record:delete` |
| /hrm/insurance/employee-info/update-scheme | PUT | 更新员工参保方案 | `hrm:insurance:employee-info:update` |
| /hrm/insurance/scheme/simple-list | GET | 社保方案精简列表 | `hrm:insurance:scheme:query` |

### 绩效管理（performance）— 4 个 Controller，40 端点，详见 [api-performance.md](api-performance.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmPerformanceAssessmentTemplateController | 考核模板 CRUD/精简列表 | 7 |
| HrmPerformanceResultTemplateController | 结果模板 CRUD/精简列表 | 7 |
| HrmPerformancePlanController | 绩效计划 CRUD/启动/开评分/面谈/归档/终止/统计 | 13 |
| HrmPerformanceAssessmentController | 员工考核增删/分页/流程记录/归档系列 | 13 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/performance/plan/start | POST | 启动绩效计划 | `hrm:performance:plan:update` |
| /hrm/performance/plan/archive | POST | 归档绩效计划 | `hrm:performance:plan:update` |
| /hrm/performance/assessment/create-list | POST | 添加员工绩效考核 | `hrm:performance:assessment:create` |
| /hrm/performance/assessment/archive-page | GET | 获得绩效归档分页 | `hrm:performance:assessment:query` |

### 员工自助门户（portal）— 15 个 Controller，44 端点，详见 [api-portal.md](api-portal.md)

> portal 为员工自助域，子包按 home/attendance/salary/insurance/performance/employee 划分，复用各业务域 Service。权限统一走 `hrm:portal:query`（查）与 `hrm:portal:{模块}:action/update/leave`（操作）。

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmPortalEmployeeController（employee 子包） | 我的档案绑定状态/查看/更新 | 3 |
| HrmPortalEmployee*Experience/Certificate/Contact/QuitInfo/FieldConfigController | 我的经历/证书/联系人/离职信息/字段配置查询 | 各 1 |
| HrmPortalAttendanceClockController | 手机打卡/打卡详情/我的考勤记录 | 3 |
| HrmPortalAttendanceLeaveController | 我的请假创建/列表/取消 | 3 |
| HrmPortalAttendanceStatisticsController | 我的月度考勤详情/导出 | 2 |
| HrmPortalSalarySlipController | 我的工资条列表/详情/已读/未读概况 | 4 |
| HrmPortalInsuranceController | 我的社保记录列表/详情 | 2 |
| HrmPortalPerformanceAssessmentController | 我的绩效任务分页（指标填写/目标确认/评分/审核/确认/申诉）与各动作 | 19 |
| HrmPortalHomeController | 员工端首页日历 | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /hrm/portal/attendance/clock/create | POST | 手机端打卡 | `hrm:portal:query` |
| /hrm/portal/attendance/leave/create | POST | 创建我的请假申请（发起 BPM 审批） | `hrm:portal:attendance:leave` |
| /hrm/portal/salary/slip/read | PUT | 标记我的工资条为已读 | `hrm:portal:query` |
| /hrm/portal/performance/assessment/score | PUT | 提交绩效自评或他评 | `hrm:portal:performance:action` |
| /hrm/portal/performance/assessment/submit-appeal | PUT | 提交我的绩效申诉 | `hrm:portal:performance:action` |
| /hrm/portal/employee/update | PUT | 更新我的员工档案 | `hrm:portal:employee:update` |

### 工作台（home）— 1 个 Controller，4 端点，详见 [api-home.md](api-home.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmHomeController | HR 工作台/团队工作台的统计摘要与日历 | 4 |

代表性端点：`/hrm/home/hr-statistics-summary`（GET，`hrm:home:hr-query`）、`/hrm/home/team-calendar`（GET，`hrm:home:team-query`）

### 操作日志（operatelog）— 1 个 Controller，1 端点，详见 [api-operatelog.md](api-operatelog.md)

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| HrmOperateLogController | 查询 HRM 操作日志（转发 system 模块 OperateLogApi，无本地表） | 1 |

代表性端点：`/hrm/operate-log/page`（GET，`hrm:recruit:post:query` 等多权限 hasAnyPermissions）

## 数据模型

共 **50** 张表，全部继承 `BaseDO`（无 TenantBaseDO）。未标注 @TableName 的表由 MyBatis-Plus 按驼峰转下划线推导。

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| hrm_employee | 员工档案 | BaseDO | job_number、user_id、dept_id、leader_employee_id、entry_status、status、type、entry_time、probation、regular_time、candidate_id、channel_id |
| hrm_employee_contact | 员工联系人 | BaseDO | employee_id、name、relation、phone、work_unit |
| hrm_employee_file | 员工材料附件 | BaseDO | employee_id、type、url |
| hrm_employee_personal_note | 员工个人备忘 | BaseDO | employee_id、content、reminder_time |
| hrm_employee_change_record | 员工异动记录 | BaseDO | employee_id、type、reason、old/new_dept_id、old/new_post_name、old/new_leader_employee_id、effect_time、applied_time |
| hrm_employee_contract | 员工合同 | BaseDO | employee_id、no、type、start_time、end_time、term、status、sign_company、file_urls |
| hrm_employee_quit_info | 员工离职信息 | BaseDO | employee_id、plan_quit_time、apply_quit_time、salary_settlement_time、type、reason、old_employee_status |
| hrm_employee_salary_card | 员工工资卡 | BaseDO | employee_id、bank_card_number、bank_area_id、bank_name、bank_branch_name |
| hrm_employee_education_experience | 员工教育经历 | BaseDO | employee_id、education、graduate_school、major、admission_time、graduation_time、first_degree |
| hrm_employee_work_experience | 员工工作经历 | BaseDO | employee_id、work_unit、post_name、start_time、end_time、witness_name |
| hrm_employee_training_experience | 员工培训经历 | BaseDO | employee_id、course、organization_name、start_time、end_time、result |
| hrm_employee_certificate | 员工证书 | BaseDO | employee_id、name、level、no、issuing_authority、issuing_time |
| hrm_recruit_post | 招聘职位 | BaseDO | post_name、dept_id、job_nature、recruit_num、post_type_id、owner_employee_id、interview_employee_ids、status |
| hrm_recruit_post_type | 招聘职位类型 | BaseDO | name、parent_id、sort、status |
| hrm_recruit_channel | 招聘渠道 | BaseDO | name、system_flag、status、sort |
| hrm_recruit_candidate | 招聘候选人 | BaseDO | name、mobile、post_id、channel_id、stage_number、education、status、eliminate、resume_urls |
| hrm_recruit_interview | 招聘面试 | BaseDO | candidate_id、type、stage_number、interview_employee_id、other_interview_employee_ids、interview_time、result、cancel_reason |
| hrm_attendance_group | 考勤组 | BaseDO | name、dept_ids、employee_ids、shifts(JSON)、special_dates(JSON)、points(JSON)、wifis(JSON)、deduct_rule(JSON)、default_status |
| hrm_attendance_holiday | 考勤节假日 | BaseDO | date、type |
| hrm_attendance_clock | 打卡记录 | BaseDO | employee_id、clock_time、type、attendance_time、source_type、status、stage、longitude、latitude、ssid、mac |
| hrm_attendance_leave | 请假申请 | BaseDO | employee_id、type、start_time、end_time、day、approval_status、process_instance_id、approval_reason |
| hrm_salary_config | 薪资配置 | BaseDO | cycle_start_day、cycle_end_day、social_security_month_type、start_year、start_month |
| hrm_salary_group | 薪资组 | BaseDO | name、salary_standard、change_rule、dept_ids、employee_ids、tax_rule_id |
| hrm_salary_option | 薪资项 | BaseDO | template_id、code、parent_code、name、type、system_flag、visible、enabled、tax_enabled、calculate_enabled |
| hrm_salary_option_template | 薪资项模板（标准项） | BaseDO | code、parent_code、name、system_flag、type、visible、tax_enabled、calculate_enabled |
| hrm_salary_tax_rule | 计税规则 | BaseDO | name、type、tax_enabled、threshold、decimal_scale、cycle_type |
| hrm_salary_change_template | 调薪模板 | BaseDO | name、default_status、options(JSON) |
| hrm_salary_employee_info | 员工薪资档案 | BaseDO | employee_id、change_type、change_reason、effect_time、probation_salary、regular_salary、salary_options(JSON)、probation_salary_options(JSON) |
| hrm_salary_change_record | 定薪调薪记录 | BaseDO | employee_id、type、reason、effect_time、before_total、after_total、salary_options(JSON)、status |
| hrm_salary_month_record | 月度工资表 | BaseDO | title、year、month、employee_count、expected_pay_salary、personal_tax、real_pay_salary、option_headers(JSON)、status |
| hrm_salary_month_employee_record | 员工月度工资记录 | BaseDO | month_record_id、employee_id、year、month、need_work_day、actual_work_day、taxable_salary、personal_tax、option_values(JSON) |
| hrm_salary_slip_template | 工资条模板 | BaseDO | name、hide_empty、default_status、options(JSON) |
| hrm_salary_slip_send_record | 工资条发放记录 | BaseDO | month_record_id、employee_count、send_employee_count、year、month |
| hrm_salary_slip | 工资条 | BaseDO | send_record_id、month_employee_record_id、employee_id、year、month、read_status、real_pay_salary、options(JSON) |
| hrm_insurance_scheme | 社保方案 | BaseDO | name、area_id、household_type、type |
| hrm_insurance_scheme_project | 社保方案项目 | BaseDO | scheme_id、type、name、base_amount、corporate_rate、personal_rate、corporate_amount、personal_amount |
| hrm_insurance_employee_info | 员工参保信息 | BaseDO | employee_id、scheme_id、first_social_security、social_security_number、accumulation_fund_number、social_security_start_month |
| hrm_insurance_month_record | 月度社保表 | BaseDO | title、year、month、insured_employee_count、stopped_employee_count、status、personal/corporate_insurance_amount、personal/corporate_provident_fund_amount |
| hrm_insurance_month_employee_record | 员工月度社保记录 | BaseDO | month_record_id、employee_id、scheme_id、year、month、projects(JSON)、status |
| hrm_performance_assessment_template | 绩效考核模板 | BaseDO | name、score_calculation、upper_limit_type、dimensions(JSON)、status |
| hrm_performance_result_template | 绩效结果模板 | BaseDO | name、status、levels(JSON：name/min_score/max_score/coefficient) |
| hrm_performance_plan | 绩效计划 | BaseDO | name、cycle_type、cycle、scopes(JSON)、assessment_template_id、assessment_config(JSON)、review_stages(JSON)、result_template_id、sync_to_salary、status、stage_type |
| hrm_performance_assessment | 员工绩效考核 | BaseDO | plan_id、employee_id、status、process_status、stage_type、score、result_level、coefficient、target_confirmation_result、appeal_status、archive_time |
| hrm_performance_assessment_stage | 绩效评分阶段 | BaseDO | assessment_id、type、name、handler_employee_id、rater_type、weight、scoring_type、status、score、deadline_time |
| hrm_performance_assessment_dimension | 绩效考核维度 | BaseDO | assessment_id、name、quota_type、weight、allow_edit |
| hrm_performance_assessment_quota | 绩效考核指标 | BaseDO | assessment_id、dimension_id、preset、name、weight、score_type、target_value、actual_value、self_score、reviewer_score、final_score |
| hrm_performance_assessment_quota_score | 指标阶段评分 | BaseDO | assessment_stage_id、assessment_quota_id、score、comment |
| hrm_performance_assessment_action_record | 绩效流程/操作记录 | BaseDO | assessment_id、stage_id、employee_id、type、title、content、file_urls |
| hrm_performance_assessment_appeal_record | 绩效申诉记录 | BaseDO | assessment_id、stage_id、status |
| hrm_config | HRM 通用业务配置（键值） | BaseDO | type、value、sort |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|---------|------|
| 观察者模式（事件监听） | `service/attendance/record/listener/HrmAttendanceLeaveStatusListener`（继承 `BpmProcessInstanceStatusEventListener`） | 订阅 BPM 流程实例状态事件，按 processDefinitionKey 过滤后回写请假审批结果 |
| 策略模式（JobHandler 多实现） | `job/employee/HrmEmployeeChangeJob`、`job/salary/HrmSalaryChangeJob`、`job/performance/HrmPerformanceAppealTimeoutJob` | 实现框架 `JobHandler` 接口统一调度：异动/调薪到期生效、绩效申诉超时自动处理，均配合 `@TenantJob` 按租户执行 |
| 注解切面（操作日志） | 各 `ServiceImpl` 的 `@LogRecord`（常量定义于 `enums/LogRecordConstants`） | 创建/更新/删除/状态流转等关键操作自动记录操作日志模板文案（含 `{_DIFF}` 差量） |

## 依赖关系

- **上游**（本模块依赖）:
  - framework：`yudao-spring-boot-starter-web`、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-excel`、`yudao-spring-boot-starter-job`、`yudao-spring-boot-starter-test`（test）
  - 业务模块：`yudao-module-system`（DeptApi、AdminUserApi、NotifyMessageSendApi、OperateLogApi）、`yudao-module-bpm`（BpmProcessInstanceApi、BpmProcessInstanceStatusEvent 事件监听）
- **下游**（依赖本模块）: 无 —— 本模块未提供 `api` 包，无其他模块调用；且当前在根 pom 与 yudao-server 中默认注释禁用

## 详细文档

- [api-employee.md](api-employee.md) - 员工管理 API
- [api-recruit.md](api-recruit.md) - 招聘管理 API
- [api-attendance.md](api-attendance.md) - 考勤管理 API
- [api-salary.md](api-salary.md) - 薪资管理 API
- [api-insurance.md](api-insurance.md) - 社保管理 API
- [api-performance.md](api-performance.md) - 绩效管理 API
- [api-portal.md](api-portal.md) - 员工自助门户 API
- [api-home.md](api-home.md) - 工作台 API
- [api-operatelog.md](api-operatelog.md) - 操作日志 API
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
