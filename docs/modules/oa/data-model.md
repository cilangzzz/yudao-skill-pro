# 数据模型详情

> oa 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

oa 模块共 48 张数据表、48 个 DO（一表一 DO），全部位于 `yudao-module-oa` 的 `cn.iocoder.yudao.module.oa.dal.dataobject` 包下，按业务域分包（announcement / attendance / contact / discussion / file / leave / mail / meetingroom / note / officialdoc / overtime / plan / regular / reimbursement / resign / schedule / seal / supply / task / travel / vehicle / workreport）。表名统一 `oa_` 前缀 + snake_case；无 `controller/app` 与跨模块 api 包，VO 按 admin 域组织（mail 域 vo 再按 account/message/provider 细分）。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，yudao-spring-boot-starter-mybatis）
│   creator      String          创建者（system 用户编号，String 类型预留扩展；INSERT 自动填充）
│   createTime   LocalDateTime   创建时间（INSERT 自动填充）
│   updater      String          更新者（INSERT_UPDATE 自动填充）
│   updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 自动填充）
│   deleted      Boolean         逻辑删除标记（@TableLogic，不物理删除）
│
└── oa 模块全部 48 个 DO 直接继承 BaseDO
    ├── 协作域: OaScheduleDO / OaScheduleParticipantDO / OaPlanDO / OaWorkReportDO
    │          OaTaskDO / OaTaskReceiverDO / OaTaskLogDO
    ├── 公告讨论域: OaAnnouncementDO / OaAnnouncementReceiverDO / OaDiscussionDO
    │              OaDiscussionReplyDO / OaDiscussionLikeDO / OaVoteOptionDO / OaVoteRecordDO
    ├── 个人办公域: OaAttendanceDO / OaNoteDO / OaNoteCategoryDO / OaNoteReceiverDO
    │              OaContactDO / OaContactCategoryDO / OaContactShareDO
    ├── 云盘域: OaFileNodeDO / OaFilePermissionDO / OaFileFavoriteDO
    ├── 邮箱域: OaMailProviderDO / OaMailAccountDO / OaMailFolderDO / OaMailMessageDO
    ├── 资源域: OaMeetingRoomDO / OaMeetingRoomBookingDO / OaVehicleDO
    │          OaVehicleApplyDO / OaVehicleReturnDO / OaSealDO / OaSealApplyDO
    └── 审批单据域: OaLeaveApplyDO / OaOvertimeApplyDO / OaRegularApplyDO / OaResignApplyDO
                   OaReimbursementDO / OaTravelApplyDO / OaTravelReimbursementDO
                   OaOfficialDocTemplateDO / OaOfficialDocSendDO / OaOfficialDocReceiveDO
                   OaSupplyItemDO / OaSupplyApplyDO / OaSupplyApplyItemDO

cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO extends BaseDO
└── tenantId     Long            多租户编号（oa 模块未使用该基类）
```

**使用规则**：

- **BaseDO**：oa 全部 48 个 DO 统一继承，逻辑删除走 `deleted` 字段；表格主键统一 `id bigint`（`@TableId`），兼容 Oracle/PG 的序列通过 `@KeySequence("oa_xxx_seq")` 声明。
- **TenantBaseDO**：oa 未使用。oa 不做模块级多租户，DO 层未映射 `tenantId`；但测试建表 SQL（`src/test/resources/sql/create_tables.sql`）为每张表保留了 `tenant_id bigint NOT NULL DEFAULT 0` 列以兼容租户环境部署，二级索引在 SQL 中也统一以 `tenant_id` 为最左前缀列。
- **申请人约定**：各审批申请 DO（请假/加班/转正/离职/报销/出差等）不设申请人字段，统一复用 `BaseDO.creator` 表示申请人、`BaseDO.createTime` 表示申请时间（DO 注释明确此约定）。
- **JSON 扩展字段**：列表、附件、明细类字段通过 `@TableField(typeHandler = JacksonTypeHandler.class)` + `autoResultMap = true` 以 JSON 存储在单列中（`file_urls`、`items`、`equipments` 等），不建从表。
- **回收站约定**：云盘节点的回收站状态使用业务字段 `status` 表达，不占用 `BaseDO.deleted`；`deleted = true` 表示彻底删除。

## 2. 核心 DO 实体

> 以下各表仅列业务字段，`creator / create_time / updater / update_time / deleted` 为 BaseDO 继承字段，不再重复列出。除主键外，全部索引均为普通索引（无数据库唯一索引），少数"唯一"语义由业务层 `selectOne` 查重保证（如 `oa_contact_share(contact_id, user_id)`、`oa_file_favorite(user_id, node_id)`、`oa_note_receiver(note_id, user_id)`、`oa_schedule_participant(schedule_id, user_id)`、`oa_file_permission(node_id, subject_type, subject_id)`）；二级索引在测试 SQL 中以 `(tenant_id, 业务列...)` 复合形式定义，下文仅列业务列。

### 2.1 日程与工作协作

#### OaScheduleDO (oa_schedule)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日程编号，主键 |
| type | Integer | type | 日程类型，枚举 OaScheduleTypeEnum |
| priority | Integer | priority | 优先级，枚举 OaPriorityEnum |
| title | String | title | 标题 |
| description | String | description | 描述 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| remind | Boolean | remind | 是否提醒 |
| reminded | Boolean | reminded | 是否已提醒（创建人和全部参与人发送成功后标记），由 OaScheduleReminderJob 定时扫描 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaScheduleParticipantDO (oa_schedule_participant)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 参与记录编号，主键 |
| scheduleId | Long | schedule_id | 日程编号，关联 OaScheduleDO.id |
| userId | Long | user_id | 参与人用户编号，关联 system AdminUser |
| readStatus | Boolean | read_status | 是否已读 |
| readTime | LocalDateTime | read_time | 首次阅读时间 |

**继承**: BaseDO
**索引**: idx_schedule_id_user_id（schedule_id, user_id, deleted），加速按日程查参与人及按人查日程

#### OaPlanDO (oa_plan)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 计划编号，主键 |
| type | Integer | type | 计划类型，枚举 OaPlanTypeEnum |
| status | Integer | status | 计划状态，枚举 OaPlanStatusEnum |
| title | String | title | 标题 |
| label | String | label | 标签 |
| content | String | content | 计划内容 |
| summary | String | summary | 计划总结 |
| comment | String | comment | 计划点评 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaWorkReportDO (oa_work_report)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 汇报编号，主键 |
| no | String | no | 汇报单号 |
| type | Integer | type | 汇报类型（日报/周报/月报等），枚举 OaWorkReportTypeEnum |
| status | Integer | status | 汇报状态，枚举 OaWorkReportStatusEnum |
| deptId | Long | dept_id | 汇报人所属部门编号，关联 system Dept |
| startTime | LocalDateTime | start_time | 周期开始时间 |
| endTime | LocalDateTime | end_time | 周期结束时间 |
| title | String | title | 汇报标题 |
| summary | String | summary | 工作总结 |
| plan | String | plan | 工作计划补充说明 |
| problem | String | problem | 问题与协调事项 |
| workItems | List\<WorkItem\> | work_items | 已完成工作项 JSON 数组，元素：content（工作内容）、progress（完成进度） |
| planItems | List\<PlanItem\> | plan_items | 工作计划项 JSON 数组，元素：content（计划内容） |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: work_report_idx_no（no），按单号查询

#### OaTaskDO (oa_task)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 任务编号，主键 |
| type | Integer | type | 任务类型，枚举 OaTaskTypeEnum |
| status | Integer | status | 总体状态，枚举 OaTaskStatusEnum |
| title | String | title | 标题 |
| description | String | description | 任务描述 |
| comment | String | comment | 任务评价 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| publishTime | LocalDateTime | publish_time | 业务发布时间，新增及编辑任务时刷新 |
| top | Boolean | top | 是否置顶 |
| canceled | Boolean | canceled | 是否取消（取消后禁止反馈；恢复时保留原进度，不改 status 与接收人状态） |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaTaskReceiverDO (oa_task_receiver)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| taskId | Long | task_id | 任务编号，关联 OaTaskDO.id |
| userId | Long | user_id | 接收人用户编号，关联 system AdminUser |
| status | Integer | status | 该接收人的任务状态，枚举 OaTaskStatusEnum |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaTaskLogDO (oa_task_log)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| taskId | Long | task_id | 任务编号，关联 OaTaskDO.id |
| userId | Long | user_id | 反馈人用户编号，关联 system AdminUser |
| status | Integer | status | 变更后的状态，枚举 OaTaskStatusEnum |
| content | String | content | 反馈内容 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

### 2.2 公告与讨论投票

#### OaAnnouncementDO (oa_announcement)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 公告编号，主键 |
| type | Integer | type | 公告类型，枚举 OaAnnouncementTypeEnum |
| priority | Integer | priority | 优先级，枚举 OaPriorityEnum |
| title | String | title | 标题 |
| content | String | content | 内容 |
| url | String | url | 相关链接 |
| top | Boolean | top | 是否置顶 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）。公告创建即发布，发布时间复用 BaseDO.createTime，编辑时保持不变

#### OaAnnouncementReceiverDO (oa_announcement_receiver)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 接收关系编号，主键 |
| announcementId | Long | announcement_id | 公告编号，关联 OaAnnouncementDO.id |
| receiverUserId | Long | receiver_user_id | 接收人用户编号，关联 system AdminUser |
| readStatus | Boolean | read_status | 是否已读 |

**继承**: BaseDO
**索引**: announcement_receiver_idx_announcement_id_receiver_user_id（announcement_id, receiver_user_id, deleted）

#### OaDiscussionDO (oa_discussion)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 讨论编号，主键 |
| userId | Long | user_id | 发布人用户编号，关联 system AdminUser |
| type | Integer | type | 类型（讨论/投票），枚举 OaDiscussionTypeEnum |
| title | String | title | 标题 |
| content | String | content | 内容 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |
| visitCount | Integer | visit_count | 访问次数 |
| voteMultiple | Boolean | vote_multiple | 是否允许多选投票（投票类型专用） |
| voteStartTime | LocalDateTime | vote_start_time | 投票开始时间 |
| voteEndTime | LocalDateTime | vote_end_time | 投票结束时间 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaDiscussionReplyDO (oa_discussion_reply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 回复编号，主键 |
| discussionId | Long | discussion_id | 讨论编号，关联 OaDiscussionDO.id |
| userId | Long | user_id | 回复人用户编号，关联 system AdminUser |
| parentId | Long | parent_id | 父回复编号，关联本表 id；根回复固定 0（PARENT_ID_ROOT） |
| replyUserId | Long | reply_user_id | 被回复人用户编号，关联 system AdminUser |
| content | String | content | 回复内容 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaDiscussionLikeDO (oa_discussion_like)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 点赞记录编号，主键 |
| discussionId | Long | discussion_id | 讨论编号，关联 OaDiscussionDO.id（对讨论点赞时） |
| replyId | Long | reply_id | 回复编号，关联 OaDiscussionReplyDO.id（对回复点赞时） |
| userId | Long | user_id | 点赞人用户编号，关联 system AdminUser |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；同一用户对同一讨论/回复的点赞由业务层 selectOne(discussionId/replyId + userId) 查重

#### OaVoteOptionDO (oa_vote_option)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 投票选项编号，主键 |
| discussionId | Long | discussion_id | 讨论编号，关联 OaDiscussionDO.id |
| title | String | title | 选项标题 |
| color | String | color | 选项颜色 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaVoteRecordDO (oa_vote_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 投票记录编号，主键 |
| discussionId | Long | discussion_id | 讨论编号，关联 OaDiscussionDO.id |
| optionId | Long | option_id | 投票选项编号，关联 OaVoteOptionDO.id |
| userId | Long | user_id | 投票人用户编号，关联 system AdminUser |

**继承**: BaseDO
**索引**: vote_record_idx_option_id_user_id（option_id, user_id, deleted），统计各选项票数及查重

### 2.3 个人办公（考勤、笔记、外部联系人）

#### OaAttendanceDO (oa_attendance)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 考勤编号，主键 |
| userId | Long | user_id | 用户编号，关联 system AdminUser |
| type | Integer | type | 考勤类型（上班/下班打卡），枚举 OaAttendanceTypeEnum |
| status | Integer | status | 考勤状态（正常/迟到等），枚举 OaAttendanceStatusEnum |
| attendanceTime | LocalDateTime | attendance_time | 考勤时间 |
| attendanceIp | String | attendance_ip | 考勤 IP |
| remark | String | remark | 考勤备注 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）。打卡时段/应出勤天数由配置类 OaProperties（前缀 `yudao.oa`）控制

#### OaNoteDO (oa_note)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 笔记编号，主键 |
| categoryId | Long | category_id | 目录编号，关联 OaNoteCategoryDO.id |
| type | Integer | type | 笔记类型，枚举 OaNoteTypeEnum |
| priority | Integer | priority | 优先级，枚举 OaPriorityEnum |
| title | String | title | 标题 |
| content | String | content | 内容 |
| favorite | Boolean | favorite | 是否收藏 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaNoteCategoryDO (oa_note_category)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 目录编号，主键 |
| userId | Long | user_id | 用户编号（目录归属人），关联 system AdminUser |
| name | String | name | 目录名称 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；同用户同名目录由业务层 selectByUserIdAndName 查重

#### OaNoteReceiverDO (oa_note_receiver)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 持有关系编号，主键 |
| noteId | Long | note_id | 笔记编号，关联 OaNoteDO.id |
| userId | Long | user_id | 持有人用户编号（包含创建人和共享接收人），关联 system AdminUser |

**继承**: BaseDO
**索引**: idx_note_id_user_id（note_id, user_id, deleted）；(noteId, userId) 组合由业务层查重

#### OaContactDO (oa_contact)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 联系人编号，主键 |
| categoryId | Long | category_id | 分类编号，关联 OaContactCategoryDO.id |
| name | String | name | 姓名 |
| pinyin | String | pinyin | 姓名拼音（pinyin4j 生成，用于排序检索） |
| sex | Integer | sex | 性别，枚举 system SexEnum |
| mobile | String | mobile | 手机号码 |
| email | String | email | 邮箱 |
| address | String | address | 地址 |
| companyName | String | company_name | 公司名称 |
| companyPhone | String | company_phone | 公司电话 |
| avatar | String | avatar | 头像地址 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaContactCategoryDO (oa_contact_category)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分类编号，主键 |
| userId | Long | user_id | 用户编号（分类归属人），关联 system AdminUser |
| name | String | name | 分类名称 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；同用户同名分类由业务层 selectByUserIdAndName 查重

#### OaContactShareDO (oa_contact_share)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 共享记录编号，主键 |
| contactId | Long | contact_id | 联系人编号，关联 OaContactDO.id |
| userId | Long | user_id | 共享接收人用户编号，关联 system AdminUser |
| categoryId | Long | category_id | 接收人侧分类编号，关联 OaContactCategoryDO.id |
| handleStatus | Boolean | handle_status | 是否已处理 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）。DO 注释约定：creator 为实际共享人，userId 为持有人；(contactId, userId) 组合由业务层 selectByContactIdAndUserId 查重

### 2.4 云盘

#### OaFileNodeDO (oa_file_node)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| parentId | Long | parent_id | 父目录编号，关联本表 id；根目录固定 0（PARENT_ID_ROOT），自关联构成目录树 |
| type | Integer | type | 节点类型（文件夹/文件），枚举 OaFileNodeTypeEnum |
| name | String | name | 节点名称 |
| extension | String | extension | 扩展名 |
| category | Integer | category | 文件分类，枚举 OaFileCategoryEnum（按扩展名计算，文件夹为空） |
| size | Long | size | 文件大小，单位字节 |
| url | String | url | 文件访问地址（infra FileApi 上传结果），文件夹为空 |
| deptId | Long | dept_id | 所属部门编号（部门空间），关联 system Dept |
| status | Integer | status | 节点状态（正常/回收站），枚举 OaFileNodeStatusEnum；回收站走本字段，彻底删除走 BaseDO.deleted |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）。个人/部门默认容量（5GB）与下载地址有效期由 OaProperties 配置

#### OaFilePermissionDO (oa_file_permission)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| nodeId | Long | node_id | 共享节点编号，关联 OaFileNodeDO.id |
| subjectType | Integer | subject_type | 共享主体类型（用户/部门），枚举 OaFileSubjectTypeEnum |
| subjectId | Long | subject_id | 共享主体编号，关联 system AdminUser 或 Dept |
| level | Integer | level | 共享权限级别（可见/可编辑等），枚举 OaFilePermissionLevelEnum |
| inherit | Boolean | inherit | 是否继承到子目录 |
| expireTime | LocalDateTime | expire_time | 权限到期时间 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；(nodeId, subjectType, subjectId) 组合由业务层 selectOne 查重

#### OaFileFavoriteDO (oa_file_favorite)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| nodeId | Long | node_id | 收藏节点编号，关联 OaFileNodeDO.id |
| userId | Long | user_id | 收藏用户编号，关联 system AdminUser |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；(userId, nodeId) 组合由业务层 selectByUserIdAndNodeId 查重

### 2.5 企业邮箱

> 该域由 OaMailMessageClient/Impl（JavaMail IMAP/SMTP 封装）驱动：本地仅保存服务配置、账号凭据和手动同步的邮件索引，不缓存附件文件，正文经 jsoup 清洗后存储。

#### OaMailProviderDO (oa_mail_provider)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 服务配置编号，主键 |
| name | String | name | 服务配置名称 |
| imap | ConnectionConfig | imap | IMAP 连接配置，JSON 存储：host（服务器域名）、port（端口）、sslEnable（是否 SSL）、starttlsEnable（是否 STARTTLS） |
| smtp | ConnectionConfig | smtp | SMTP 连接配置，JSON 存储同 imap |
| status | Integer | status | 状态，枚举 CommonStatusEnum（开启/停用） |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaMailAccountDO (oa_mail_account)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 账号编号，主键 |
| providerId | Long | provider_id | 服务配置编号，关联 OaMailProviderDO.id |
| mail | String | mail | 邮箱地址 |
| username | String | username | 登录用户名 |
| password | String | password | 密码或授权码 |
| defaultStatus | Boolean | default_status | 是否默认发件账号 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）。账号归属人复用 BaseDO.creator（关联 system AdminUser）

#### OaMailFolderDO (oa_mail_folder)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| accountId | Long | account_id | 邮箱账号编号，关联 OaMailAccountDO.id |
| name | String | name | 远端文件夹完整名称 |
| type | String | type | 文件夹类型（INBOX/SENT 等），枚举 OaMailFolderTypeEnum |
| uidValidity | Long | uid_validity | 远端文件夹 UID 有效期（IMAP UIDVALIDITY） |
| syncTime | LocalDateTime | sync_time | 最近完整同步时间 |
| available | Boolean | available | 远端文件夹是否可用 |

**继承**: BaseDO
**索引**: mail_folder_idx_account_folder（account_id, name），按账号取文件夹列表

#### OaMailMessageDO (oa_mail_message)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| accountId | Long | account_id | 邮箱账号编号，关联 OaMailAccountDO.id |
| folderId | Long | folder_id | 文件夹编号，关联 OaMailFolderDO.id |
| uidValidity | Long | uid_validity | 远端文件夹 UID 有效期 |
| uid | Long | uid | 远端邮件 UID |
| subject | String | subject | 邮件主题 |
| content | String | content | 经安全过滤的正文缓存（jsoup 清洗 HTML）；null 表示未读取，空字符串表示正文为空 |
| replyTos | List\<String\> | reply_tos | 回复地址列表，JSON 存储 |
| attachments | List\<Attachment\> | attachments | 附件目录缓存 JSON 数组，元素：part（MIME 部件路径）、name（附件名）、size（字节）；附件文件仍从远端读取 |
| sender | String | sender | 发件人 |
| recipients | List\<String\> | recipients | 收件人列表，JSON 存储 |
| ccs | List\<String\> | ccs | 抄送人列表，JSON 存储 |
| receiveTime | LocalDateTime | receive_time | 接收时间 |
| readStatus | Boolean | read_status | 是否已读 |
| hasAttach | Boolean | has_attach | 是否有附件 |
| size | Integer | size | 邮件大小（字节） |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；(accountId, folderId, uidValidity, uid) 组合定位远端唯一邮件

### 2.6 会议室与车辆

#### OaMeetingRoomDO (oa_meeting_room)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| name | String | name | 会议室名称 |
| location | String | location | 会议室位置 |
| type | Integer | type | 会议室类型，枚举 OaMeetingRoomTypeEnum |
| managerUserId | Long | manager_user_id | 负责人用户编号，关联 system AdminUser（联系方式取其 mobile） |
| status | Integer | status | 可用状态，枚举 OaMeetingRoomStatusEnum |
| picUrl | String | pic_url | 会议室图片 URL |
| seatCount | Integer | seat_count | 坐席数 |
| equipments | List\<Integer\> | equipments | 设备列表（字典 MEETING_ROOM_EQUIPMENT），JSON 存储 |
| allowBooking | Boolean | allow_booking | 是否允许预定 |
| needApproval | Boolean | need_approval | 预定是否需要审批 |
| bookingScope | Integer | booking_scope | 可预定范围，枚举 OaMeetingRoomBookingScopeEnum |
| bookingUserIds | List\<Long\> | booking_user_ids | 可预定用户编号列表，JSON 存储 |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaMeetingRoomBookingDO (oa_meeting_room_booking)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 预定申请单号 |
| roomId | Long | room_id | 会议室编号，关联 OaMeetingRoomDO.id |
| title | String | title | 会议主题 |
| startTime | LocalDateTime | start_time | 会议开始时间 |
| endTime | LocalDateTime | end_time | 会议结束时间 |
| moderatorUserId | Long | moderator_user_id | 主持人用户编号，关联 system AdminUser |
| attendeeUserIds | List\<Long\> | attendee_user_ids | 参会用户编号列表，JSON 存储 |
| reminderType | Integer | reminder_type | 会议提醒类型，枚举 OaMeetingRoomReminderTypeEnum |
| reminded | Boolean | reminded | 是否已发送会议开始提醒（OaMeetingRoomBookingReminderJob 扫描；该 Job 同时取消过期预定） |
| description | String | description | 会议说明 |
| deptId | Long | dept_id | 申请部门编号，关联 system Dept |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum；无需审批时提交后直接通过 |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable HistoricProcessInstance.id；无需审批时为空 |
| needApproval | Boolean | need_approval | 提交时是否需要审批（快照自会议室配置，草稿可为空） |
| useStatus | Integer | use_status | 使用状态，枚举 OaMeetingRoomUseStatusEnum |
| remark | String | remark | 申请备注 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: meeting_room_booking_idx_no（no），按单号查询

#### OaVehicleDO (oa_vehicle)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 车牌号 |
| name | String | name | 车辆名称 |
| deptId | Long | dept_id | 所属部门编号，关联 system Dept（FieldStrategy.ALWAYS，支持清空） |
| type | String | type | 车型 |
| category | String | category | 车辆分类（字典 VEHICLE_CATEGORY） |
| brandModel | String | brand_model | 品牌型号 |
| seatCount | Integer | seat_count | 座位数 |
| barePrice | BigDecimal | bare_price | 裸车价格（元） |
| compulsoryInsuranceExpireTime | LocalDateTime | compulsory_insurance_expire_time | 交强险到期时间 |
| commercialInsuranceExpireTime | LocalDateTime | commercial_insurance_expire_time | 商业险到期时间 |
| inspectionExpireTime | LocalDateTime | inspection_expire_time | 年检到期时间 |
| picUrl | String | pic_url | 车辆照片 URL |
| status | Integer | status | 车辆台账状态，枚举 OaVehicleStatusEnum |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: vehicle_idx_no（no），按车牌号查询

#### OaVehicleApplyDO (oa_vehicle_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 用车申请单号 |
| vehicleId | Long | vehicle_id | 车辆编号，关联 OaVehicleDO.id |
| vehicleNo | String | vehicle_no | 车牌号快照，冗余 OaVehicleDO.no |
| userId | Long | user_id | 申请人用户编号，关联 system AdminUser |
| deptId | Long | dept_id | 申请部门编号，关联 system Dept |
| startTime | LocalDateTime | start_time | 预计出车时间 |
| endTime | LocalDateTime | end_time | 预计回车时间 |
| startLocation | String | start_location | 出车地点 |
| endLocation | String | end_location | 预计回车地点 |
| reason | String | reason | 用车事由 |
| passenger | String | passenger | 随行人 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum |
| returnStatus | Integer | return_status | 还车业务状态，枚举 OaVehicleReturnStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| remark | String | remark | 备注 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: vehicle_apply_idx_no（no）、vehicle_apply_idx_process_instance（process_instance_id）

#### OaVehicleReturnDO (oa_vehicle_return)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 还车申请单号 |
| applyId | Long | apply_id | 用车申请编号，关联 OaVehicleApplyDO.id |
| vehicleId | Long | vehicle_id | 车辆编号（从用车申请生成），关联 OaVehicleDO.id |
| userId | Long | user_id | 申请人用户编号，关联 system AdminUser |
| deptId | Long | dept_id | 申请部门编号，关联 system Dept |
| actualStartTime | LocalDateTime | actual_start_time | 实际出车时间 |
| startLocation | String | start_location | 实际出车地点 |
| reason | String | reason | 用车事由 |
| passenger | String | passenger | 随行人 |
| actualReturnTime | LocalDateTime | actual_return_time | 实际回车时间 |
| returnLocation | String | return_location | 实际回车地点 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| remark | String | remark | 还车说明 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: vehicle_return_idx_no（no）、vehicle_return_idx_process_instance（process_instance_id）

### 2.7 印章管理

#### OaSealDO (oa_seal)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| deptId | Long | dept_id | 所属部门编号，关联 system Dept（与保管部门独立维护） |
| no | String | no | 印章编号 |
| name | String | name | 印章名称 |
| type | Integer | type | 印章类型（字典 SEAL_TYPE） |
| category | Integer | category | 印章分类（字典 SEAL_CATEGORY） |
| keeperUserId | Long | keeper_user_id | 保管人用户编号，关联 system AdminUser |
| keeperDeptId | Long | keeper_dept_id | 保管部门编号，关联 system Dept |
| status | Integer | status | 印章台账状态（在用/停用等），枚举 OaSealStatusEnum、字典 SEAL_STATUS |
| purchaseTime | LocalDateTime | purchase_time | 购买时间 |
| enableTime | LocalDateTime | enable_time | 启用时间 |
| disableTime | LocalDateTime | disable_time | 停用时间 |
| picUrl | String | pic_url | 印章照片地址 |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: seal_idx_no（no），按印章编号查询

#### OaSealApplyDO (oa_seal_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 申请单号 |
| userId | Long | user_id | 申请人用户编号，关联 system AdminUser |
| deptId | Long | dept_id | 申请部门编号，关联 system Dept |
| sealId | Long | seal_id | 印章编号，关联 OaSealDO.id |
| sealNo | String | seal_no | 印章编号快照，冗余 OaSealDO.no |
| sealName | String | seal_name | 印章名称快照，冗余 OaSealDO.name |
| sealType | Integer | seal_type | 印章类型快照，冗余 OaSealDO.type |
| keeperDeptId | Long | keeper_dept_id | 保管部门编号快照，冗余 OaSealDO.keeperDeptId |
| keeperUserId | Long | keeper_user_id | 保管人用户编号快照，冗余 OaSealDO.keeperUserId |
| reason | String | reason | 用印事由 |
| type | Integer | type | 用印类型（用印/借用等），枚举 OaSealApplyTypeEnum、字典 SEAL_APPLY_TYPE |
| mode | Integer | mode | 用印方式（现场/外借等），枚举 OaSealUseModeEnum、字典 SEAL_USE_MODE |
| documentTitle | String | document_title | 文件标题 |
| documentType | String | document_type | 文件类型 |
| documentCount | Integer | document_count | 文件份数 |
| contractPrice | BigDecimal | contract_price | 合同金额 |
| contractParty | String | contract_party | 合同对方 |
| expectedUseTime | LocalDateTime | expected_use_time | 预计用印时间 |
| actualUseTime | LocalDateTime | actual_use_time | 实际用印时间 |
| expectedReturnTime | LocalDateTime | expected_return_time | 预计归还时间 |
| actualReturnTime | LocalDateTime | actual_return_time | 实际归还时间 |
| useStatus | Integer | use_status | 用印业务状态，枚举 OaSealUseStatusEnum、字典 SEAL_USE_STATUS |
| status | Integer | status | 审批状态，取 BPM 流程实例状态，枚举 BpmProcessInstanceStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| urgent | Boolean | urgent | 是否紧急 |
| remark | String | remark | 备注 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: seal_apply_idx_no（no）、seal_apply_idx_process_instance（process_instance_id）

### 2.8 人事审批单据（请假、加班、转正、离职）

> 四张表结构同构：`title + urgency + 业务字段 + status + process_instance_id`；申请人/申请时间复用 BaseDO.creator/createTime；status 均为 BpmProcessInstanceStatusEnum（未开始 = 未提交草稿），process_instance_id 关联 Flowable 流程实例。均无二级索引（仅主键）。

#### OaLeaveApplyDO (oa_leave_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| title | String | title | 申请标题 |
| urgency | Integer | urgency | 紧急程度（字典 APPLY_URGENCY） |
| type | Integer | type | 请假类型（字典 LEAVE_TYPE） |
| startTime | LocalDateTime | start_time | 请假开始时间 |
| endTime | LocalDateTime | end_time | 请假结束时间 |
| days | Integer | days | 请假天数 |
| reason | String | reason | 申请原因 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum（未开始表示草稿） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable HistoricProcessInstance.id |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaOvertimeApplyDO (oa_overtime_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| title | String | title | 申请标题 |
| urgency | Integer | urgency | 紧急程度（字典 APPLY_URGENCY） |
| type | Integer | type | 加班类型（字典 OVERTIME_TYPE） |
| startTime | LocalDateTime | start_time | 加班开始时间 |
| endTime | LocalDateTime | end_time | 加班结束时间 |
| days | BigDecimal | days | 加班天数（支持 0.5 等精度） |
| reason | String | reason | 申请原因 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum（未开始表示草稿） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaRegularApplyDO (oa_regular_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| title | String | title | 申请标题 |
| urgency | Integer | urgency | 紧急程度（字典 APPLY_URGENCY） |
| startTime | LocalDateTime | start_time | 试用开始时间 |
| endTime | LocalDateTime | end_time | 试用结束时间 |
| days | Integer | days | 试用天数（按起止时间计算，不重复保存流程公共天数） |
| experience | String | experience | 试用期或实习期心得体会 |
| understanding | String | understanding | 对本岗位职责要求的理解 |
| growth | String | growth | 试用期或实习期的成长 |
| deficiency | String | deficiency | 目前存在的不足 |
| improvement | String | improvement | 本岗位工作改进计划 |
| suggestion | String | suggestion | 对公司产品的意见及建议 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum（未开始表示草稿） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaResignApplyDO (oa_resign_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| title | String | title | 申请标题 |
| urgency | Integer | urgency | 紧急程度（字典 APPLY_URGENCY） |
| reason | String | reason | 申请原因 |
| handoverUserId | Long | handover_user_id | 工作交接人用户编号，关联 system AdminUser |
| unfinishedWork | String | unfinished_work | 未完成事宜 |
| hasPendingReimbursement | Boolean | has_pending_reimbursement | 是否有未完成的费用报销 |
| suggestion | String | suggestion | 申请人的意见及建议 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum（未开始表示草稿） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

### 2.9 费用审批单据（报销、出差、出差报销）

#### OaReimbursementDO (oa_reimbursement)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| title | String | title | 申请标题 |
| urgency | Integer | urgency | 紧急程度（字典 APPLY_URGENCY） |
| reason | String | reason | 申请原因 |
| witnessUserId | Long | witness_user_id | 证明人用户编号，关联 system AdminUser |
| customerName | String | customer_name | 相关客户名称（文本，不关联客户档案） |
| paymentMethod | Integer | payment_method | 报销方式（字典 REIMBURSEMENT_PAYMENT_METHOD） |
| invoiceCount | Integer | invoice_count | 票据总数（汇总明细，不由用户单独填写） |
| totalPrice | BigDecimal | total_price | 报销总金额（元，汇总明细） |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum（未开始表示草稿） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| items | List\<Item\> | items | 报销明细 JSON 数组，元素：expenseTime（费用产生时间）、expenseType（费用类型，字典 EXPENSE_TYPE）、description（费用说明）、invoiceCount（票据张数）、price（报销金额）；明细随单保存，不维护独立编号及生命周期 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaTravelApplyDO (oa_travel_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 单据编号 |
| deptId | Long | dept_id | 申请部门编号，关联 system Dept |
| reason | String | reason | 出差事由 |
| startTime | LocalDateTime | start_time | 出差开始时间 |
| endTime | LocalDateTime | end_time | 出差结束时间 |
| days | Integer | days | 出差天数 |
| companion | String | companion | 同行人（姓名文本，不关联用户编号） |
| estimatedPrice | BigDecimal | estimated_price | 预计费用（元） |
| reimburseStatus | Boolean | reimburse_status | 是否已报销 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| remark | String | remark | 备注 |
| items | List\<Item\> | items | 行程明细 JSON 数组，元素：departureAreaId（出发地区编号，关联 Area）、arrivalAreaId（到达地区编号）、startTime/endTime（行程起止时间）、transportType（交通方式，字典 TRANSPORT_TYPE）、remark |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: travel_apply_idx_no（no），按单号查询

#### OaTravelReimbursementDO (oa_travel_reimbursement)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 单据编号 |
| deptId | Long | dept_id | 申请部门编号（保存申请时的部门，不随调岗变化），关联 system Dept |
| travelApplyId | Long | travel_apply_id | 关联出差申请编号，关联 OaTravelApplyDO.id，未关联时为空 |
| reason | String | reason | 出差事由 |
| startTime | LocalDateTime | start_time | 出差开始时间 |
| endTime | LocalDateTime | end_time | 出差结束时间 |
| days | Integer | days | 出差天数（冗余，按时长除以 24 向上取整） |
| totalPrice | BigDecimal | total_price | 报销总金额（元，冗余明细合计） |
| payStatus | Boolean | pay_status | 是否已支付 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum（与出差申请的审批状态独立） |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| remark | String | remark | 备注 |
| items | List\<Item\> | items | 费用明细 JSON 数组，元素：expenseType（费用类型，字典 EXPENSE_TYPE）、expenseTime（费用发生时间）、departureCity（出发地）、arrivalCity（到达地）、price（金额）、description（费用说明） |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |

**继承**: BaseDO
**索引**: travel_reimbursement_idx_no（no），按单号查询

### 2.10 公文管理（套红模板、发文、收文）

#### OaOfficialDocTemplateDO (oa_official_doc_template)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| name | String | name | 模板名称 |
| authorityName | String | authority_name | 红头名称（模板版式文本，非 system 部门名称冗余） |
| fontSize | Integer | font_size | 红头名称字号 |
| noPrefix | String | no_prefix | 发文字号前缀（供发文初始化文号前缀） |
| sealPicUrl | String | seal_pic_url | 印章图片地址（复用平台图片上传，不关联印章资产） |
| separatorType | Integer | separator_type | 分隔线类型（字典 OFFICIAL_DOC_SEPARATOR_TYPE） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）

#### OaOfficialDocSendDO (oa_official_doc_send)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 单据编号（发文业务单号，与公文文号 documentNo 独立） |
| templateId | Long | template_id | 套红模板编号，关联 OaOfficialDocTemplateDO.id |
| title | String | title | 标题 |
| noPrefix | String | no_prefix | 发文字号前缀（初始取自模板，保存后不随模板联动） |
| year | Integer | year | 发文年度 |
| sequence | Integer | sequence | 发文序号 |
| documentNo | String | document_no | 公文文号（冗余 noPrefix + year + sequence 组成的完整文号，用于查询展示） |
| secrecyLevel | Integer | secrecy_level | 密级（字典 OFFICIAL_DOC_SECRET_LEVEL） |
| urgencyLevel | Integer | urgency_level | 紧急程度（字典 OFFICIAL_DOC_URGENCY_LEVEL） |
| disclosureType | Integer | disclosure_type | 公开类别（字典 OFFICIAL_DOC_PUBLIC_CATEGORY） |
| issueTime | LocalDateTime | issue_time | 发文时间 |
| sendDeptId | Long | send_dept_id | 发文部门编号，关联 system Dept |
| mainDeptIds | List\<Long\> | main_dept_ids | 主送部门编号列表，JSON 存储 |
| copyDeptIds | List\<Long\> | copy_dept_ids | 抄送部门编号列表，JSON 存储 |
| signerUserId | Long | signer_user_id | 签发人用户编号，关联 system AdminUser |
| content | String | content | 正文 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |
| formalFileUrl | String | formal_file_url | 正式公文地址（套红成文文件） |
| remark | String | remark | 附注 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；单号 no 由业务层 selectOne(no) 查询

#### OaOfficialDocReceiveDO (oa_official_doc_receive)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 单据编号 |
| sendId | Long | send_id | 来源发文编号，关联 OaOfficialDocSendDO.id；手工新增收文时为空 |
| receiveType | Integer | receive_type | 收文类型，枚举 OaOfficialDocReceiveTypeEnum、字典 OFFICIAL_DOC_RECEIVE_TYPE |
| title | String | title | 标题（自动生成时冗余发文标题，手工收文直接填写） |
| documentNo | String | document_no | 来文字号（自动生成时冗余发文文号） |
| secrecyLevel | Integer | secrecy_level | 密级（字典 OFFICIAL_DOC_SECRET_LEVEL） |
| urgencyLevel | Integer | urgency_level | 紧急程度（字典 OFFICIAL_DOC_URGENCY_LEVEL） |
| receiveTime | LocalDateTime | receive_time | 收文时间 |
| receiveDeptId | Long | receive_dept_id | 收文部门编号，关联 system Dept |
| handlerUserId | Long | handler_user_id | 主办人用户编号，关联 system AdminUser |
| instruction | String | instruction | 领导批示 |
| result | String | result | 办理结果（独立于流程审批意见） |
| deadlineTime | LocalDateTime | deadline_time | 办理期限 |
| summary | String | summary | 内容摘要 |
| remark | String | remark | 备注 |
| fileUrls | List\<String\> | file_urls | 收文自身附件列表，JSON 存储（不等同于来源发文附件） |
| formalFileUrl | String | formal_file_url | 正式公文地址（冗余来源发文，独立于收文附件） |
| handleStatus | Integer | handle_status | 办理状态，枚举 OaOfficialDocHandleStatusEnum、字典 OFFICIAL_DOC_HANDLE_STATUS |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |

**继承**: BaseDO
**索引**: 无二级索引（仅主键）；单号 no 由业务层 selectOne(no) 查询

### 2.11 办公用品（物品台账、领用申请、申请明细）

#### OaSupplyItemDO (oa_supply_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| deptId | Long | dept_id | 所属部门编号，关联 system Dept |
| name | String | name | 物品名称 |
| no | String | no | 物品编码 |
| category | Integer | category | 类别，枚举 OaSupplyCategoryEnum、字典 SUPPLY_CATEGORY |
| manageType | Integer | manage_type | 管理类型（领用后是否需归还），枚举 OaSupplyManageTypeEnum |
| model | String | model | 规格型号 |
| unit | String | unit | 计量单位 |
| referencePrice | BigDecimal | reference_price | 参考单价 |
| stockQuantity | Integer | stock_quantity | 库存数量 |
| minStockQuantity | Integer | min_stock_quantity | 最低库存预警 |
| picUrl | String | pic_url | 物品图片 URL |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| sort | Integer | sort | 显示顺序 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: supply_item_idx_no（no, deleted），按物品编码查询

#### OaSupplyApplyDO (oa_supply_apply)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| no | String | no | 申请单号 |
| deptId | Long | dept_id | 申请部门编号，关联 system Dept |
| applyTime | LocalDateTime | apply_time | 领用日期 |
| useType | Integer | use_type | 使用类型，枚举 OaSupplyUseTypeEnum |
| pickupMethod | Integer | pickup_method | 领取方式（字典 SUPPLY_PICKUP_METHOD） |
| reason | String | reason | 申请事由 |
| status | Integer | status | 审批状态，枚举 BpmProcessInstanceStatusEnum |
| processInstanceId | String | process_instance_id | BPM 流程实例编号，关联 Flowable 流程实例 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: supply_apply_idx_no（no, deleted）、supply_apply_idx_creator（creator, deleted, id），支持按申请人在"我的申请"分页查询

#### OaSupplyApplyItemDO (oa_supply_apply_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键 |
| applyId | Long | apply_id | 领用申请编号，关联 OaSupplyApplyDO.id |
| itemId | Long | item_id | 办公用品编号，关联 OaSupplyItemDO.id |
| itemName | String | item_name | 物品名称快照，冗余 OaSupplyItemDO.name |
| model | String | model | 规格型号快照，冗余 OaSupplyItemDO.model |
| unit | String | unit | 计量单位快照，冗余 OaSupplyItemDO.unit |
| manageType | Integer | manage_type | 管理类型快照，冗余 OaSupplyItemDO.manageType |
| applyQuantity | Integer | apply_quantity | 申请数量 |
| issuedQuantity | Integer | issued_quantity | 实发数量 |
| returnedQuantity | Integer | returned_quantity | 累计归还数量 |
| status | Integer | status | 明细状态，枚举 OaSupplyApplyItemStatusEnum |
| issueUserId | Long | issue_user_id | 发放人用户编号，关联 system AdminUser |
| issueTime | LocalDateTime | issue_time | 发放时间 |
| issueRemark | String | issue_remark | 发放备注 |
| returnRemark | String | return_remark | 归还备注 |

**继承**: BaseDO
**索引**: supply_apply_item_idx_apply_id（apply_id, deleted, id）、supply_apply_item_idx_item_id（item_id, deleted）

## 3. 实体关系

所有关联均为**逻辑外键**（不建物理 FOREIGN KEY）；对 system 用户/部门、infra 文件、bpm 流程的引用通过 API（AdminUserApi / DeptApi / PermissionApi / DictDataApi / NotifyMessageSendApi / FileApi / BpmProcessInstanceApi）查询组装。

### 3.1 模块内 1:N 从属关系

```
oa_mail_provider 1 ──< N oa_mail_account 1 ──< N oa_mail_folder 1 ──< N oa_mail_message
                     （provider_id）        （account_id）           （folder_id；uid_validity+uid 定位远端邮件）

oa_meeting_room  1 ──< N oa_meeting_room_booking          （room_id；need_approval 快照冗余）
oa_vehicle       1 ──< N oa_vehicle_apply 1 ──< 1 oa_vehicle_return
                     （vehicle_id + vehicle_no 快照）        （apply_id）
oa_seal          1 ──< N oa_seal_apply                    （seal_id + seal_no/seal_name/seal_type/keeper 快照）
oa_official_doc_template 1 ──< N oa_official_doc_send 1 ──< N oa_official_doc_receive
                             （template_id）                （send_id，手工收文为空；title/document_no 等冗余）
oa_supply_item   1 ──< N oa_supply_apply_item N ──> 1 oa_supply_apply
                     （item_id + name/model/unit/manage_type 快照）（apply_id）
oa_travel_apply  1 ──< N oa_travel_reimbursement          （travel_apply_id，可空）

oa_schedule      1 ──< N oa_schedule_participant          （schedule_id）
oa_announcement  1 ──< N oa_announcement_receiver         （announcement_id）
oa_discussion    1 ──< N oa_discussion_reply              （discussion_id；reply.parent_id 自关联两级）
                 1 ──< N oa_discussion_like               （discussion_id 或 reply_id 二选一）
                 1 ──< N oa_vote_option 1 ──< N oa_vote_record（option_id）
oa_note_category 1 ──< N oa_note 1 ──< N oa_note_receiver（category_id / note_id，receiver 含创建人+共享接收人）
oa_contact_category 1 ──< N oa_contact 1 ──< N oa_contact_share（category_id / contact_id）
oa_file_node（parent_id 自关联目录树）1 ──< N oa_file_permission / oa_file_favorite（node_id）
oa_task          1 ──< N oa_task_receiver / oa_task_log   （task_id）
```

独立单表：oa_attendance（打卡流水）、oa_plan（工作计划）、oa_work_report（工作汇报，work_items/plan_items JSON 明细内嵌）、oa_leave_apply、oa_overtime_apply、oa_regular_apply、oa_resign_apply、oa_reimbursement（items JSON 明细内嵌）。

### 3.2 对外部模块的引用

```
system 模块（AdminUser / Dept）
    userId / creator / receiverUserId / managerUserId / moderatorUserId / keeperUserId
    handoverUserId / witnessUserId / signerUserId / handlerUserId / issueUserId 等  ──→  AdminUser.id
    deptId / sendDeptId / receiveDeptId / keeperDeptId 等                        ──→  Dept.id
infra 模块：file_urls / pic_url / url / formal_file_url / seal_pic_url / avatar   ──→  FileApi 上传的文件地址
bpm 模块（Flowable）：
    14 张审批表.process_instance_id ──→ HistoricProcessInstance.id（Flowable 流程实例）
    14 张审批表.status             ──→ BpmProcessInstanceStatusEnum（未开始=草稿/审批中/通过/不通过/已取消）
```

接入 BPM 的 14 张审批表：oa_leave_apply、oa_overtime_apply、oa_reimbursement、oa_regular_apply、oa_resign_apply、oa_supply_apply、oa_travel_apply、oa_travel_reimbursement、oa_seal_apply、oa_vehicle_apply、oa_vehicle_return、oa_meeting_room_booking、oa_official_doc_send、oa_official_doc_receive，统一走 create/update(草稿) → submit(发起流程) → cancel 生命周期。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|----|------|
| oa_attendance | OaAttendanceDO | 考勤打卡记录 |
| oa_schedule | OaScheduleDO | 日程 |
| oa_schedule_participant | OaScheduleParticipantDO | 日程参与人及已读状态 |
| oa_plan | OaPlanDO | 工作计划（含总结、点评） |
| oa_work_report | OaWorkReportDO | 工作汇报（日报/周报/月报） |
| oa_task | OaTaskDO | 任务发布主表 |
| oa_task_receiver | OaTaskReceiverDO | 任务接收人及各自进度状态 |
| oa_task_log | OaTaskLogDO | 任务反馈日志 |
| oa_announcement | OaAnnouncementDO | 公告 |
| oa_announcement_receiver | OaAnnouncementReceiverDO | 公告接收关系及已读状态 |
| oa_discussion | OaDiscussionDO | 讨论/投票（投票配置内嵌） |
| oa_discussion_reply | OaDiscussionReplyDO | 讨论回复（两级楼中楼） |
| oa_discussion_like | OaDiscussionLikeDO | 讨论/回复点赞记录 |
| oa_vote_option | OaVoteOptionDO | 投票选项 |
| oa_vote_record | OaVoteRecordDO | 投票记录 |
| oa_note | OaNoteDO | 笔记 |
| oa_note_category | OaNoteCategoryDO | 笔记目录 |
| oa_note_receiver | OaNoteReceiverDO | 笔记持有关系（创建人+共享接收人） |
| oa_contact | OaContactDO | 外部联系人 |
| oa_contact_category | OaContactCategoryDO | 联系人分类 |
| oa_contact_share | OaContactShareDO | 联系人共享记录 |
| oa_file_node | OaFileNodeDO | 云盘文件/目录节点（自关联树，含回收站状态） |
| oa_file_permission | OaFilePermissionDO | 云盘共享权限（用户/部门主体，可继承、可过期） |
| oa_file_favorite | OaFileFavoriteDO | 云盘收藏 |
| oa_mail_provider | OaMailProviderDO | 企业邮箱服务配置（IMAP/SMTP JSON） |
| oa_mail_account | OaMailAccountDO | 企业邮箱账号（凭据） |
| oa_mail_folder | OaMailFolderDO | 邮箱远端文件夹索引 |
| oa_mail_message | OaMailMessageDO | 邮件索引及正文缓存 |
| oa_meeting_room | OaMeetingRoomDO | 会议室台账 |
| oa_meeting_room_booking | OaMeetingRoomBookingDO | 会议室预定申请（BPM 审批） |
| oa_vehicle | OaVehicleDO | 车辆台账 |
| oa_vehicle_apply | OaVehicleApplyDO | 用车申请（BPM 审批） |
| oa_vehicle_return | OaVehicleReturnDO | 还车申请（BPM 审批） |
| oa_seal | OaSealDO | 印章台账 |
| oa_seal_apply | OaSealApplyDO | 用印申请（BPM 审批，含印章快照） |
| oa_leave_apply | OaLeaveApplyDO | 请假申请（BPM 审批） |
| oa_overtime_apply | OaOvertimeApplyDO | 加班申请（BPM 审批） |
| oa_regular_apply | OaRegularApplyDO | 转正申请（BPM 审批） |
| oa_resign_apply | OaResignApplyDO | 离职申请（BPM 审批） |
| oa_reimbursement | OaReimbursementDO | 费用报销（BPM 审批，明细 JSON 内嵌） |
| oa_travel_apply | OaTravelApplyDO | 出差申请（BPM 审批，行程明细 JSON 内嵌） |
| oa_travel_reimbursement | OaTravelReimbursementDO | 出差报销（BPM 审批，可关联出差申请） |
| oa_official_doc_template | OaOfficialDocTemplateDO | 公文套红模板 |
| oa_official_doc_send | OaOfficialDocSendDO | 公文发文（BPM 审批） |
| oa_official_doc_receive | OaOfficialDocReceiveDO | 公文收文（BPM 审批，可关联来源发文） |
| oa_supply_item | OaSupplyItemDO | 办公用品台账（含库存） |
| oa_supply_apply | OaSupplyApplyDO | 用品领用申请（BPM 审批） |
| oa_supply_apply_item | OaSupplyApplyItemDO | 用品申请明细（发放/归还，含物品快照） |
