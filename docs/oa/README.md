# 办公自动化模块 (oa)

> 提供协同办公、行政管理与业务审批一站式能力：日程/计划/任务/笔记等个人协同，公告/讨论/通讯录等企业协同，考勤/会议室/车辆/印章/办公用品/公文等行政管理，以及请假、加班、报销、出差、转正、离职、用印、用车等 BPM 流程审批。

## 模块概述

- **模块路径**: yudao-module-oa（单模块 jar 布局，无子模块）
- **业务定位**: OA（Office Automation）模块覆盖企业内部办公全场景，包含三大类能力：个人/团队协同（日程、工作计划、任务、笔记、工作汇报、讨论区、公告、通讯录、企业云盘、企业邮箱）、行政管理（考勤、会议室、车辆、印章、办公用品、公文收发）与人事/财务审批流程（请假、加班、费用报销、出差及报销、转正、离职、用印、用车、用品领用）。所有需要审批的单据统一接入 BPM 工作流模块。
- **技术栈**: Spring Boot 2.7.18（JDK8 变体，javax 命名空间）/ MyBatis-Plus / Swagger v3（springdoc）/ yudao-spring-boot-starter-web、security、mybatis、job（Quartz）/ spring-boot-starter-mail（JavaMail IMAP+SMTP）/ jsoup（邮件 HTML 清洗）/ pinyin4j（联系人拼音检索）

## 设计原则

| 原则 | 说明 |
|-----|------|
| 审批全托管 BPM | 14 个审批单据域统一在 `BpmModelConstants` 中定义流程 key（`oa_leave_apply`、`oa_reimbursement` 等），单据表只保存流程实例 ID，审批状态由 `BpmProcessInstanceApi` 驱动 |
| 草稿-提交两段式单据 | 审批类 Service 统一遵循 `create/update（草稿）→ submit（发起流程）→ cancel（撤回）` 生命周期，复用 `APPLY_*` 通用错误码 |
| 非多租户设计 | 全部 48 张表 DO 继承 `BaseDO` 而非 `TenantBaseDO`，数据按"创建人/部门/共享接收人"维度做权限隔离 |
| 个人视角与共享视角分离 | 日程、笔记、任务、公告、联系人等均拆分 `my-page/published-page`（我发出的）与 `received-page`（发给我的）两组接口，配套 `xxx_receiver/share` 关系表与 `update-read-status` 已读标记 |
| 权限标识统一前缀 | 权限串统一为 `oa:{域}:{操作}`（如 `oa:leave-apply:create`）；出差/差旅报销使用 `:save` 覆盖新增与修改；纯个人操作（打卡、我的分页等）不挂权限仅要求登录 |
| 配置外置 | `OaProperties`（前缀 `yudao.oa`）集中配置考勤打卡时段/应出勤天数、日程提前提醒小时数、云盘默认容量（5GB）与下载地址有效期 |
| 邮箱"本地索引"模型 | 邮件只存索引（UID + folder），远端 IMAP/SMTP 操作不可回滚，失败后通过再次同步恢复；同步与写操作按账号加锁 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| OA 公告 (announcement) | 公告发布/转发给下属/接收与已读管理 | OaAnnouncementDO、OaAnnouncementReceiverDO |
| OA 考勤 (attendance) | 打卡、个人/管理分页、周报与月报统计 | OaAttendanceDO |
| OA 通讯录 (contact) | 外部联系人分类、共享与共享处理 | OaContactDO、OaContactCategoryDO、OaContactShareDO |
| OA 讨论区 (discussion) | 讨论主题、楼中楼回复、点赞、单/多选投票 | OaDiscussionDO、OaDiscussionReplyDO、OaDiscussionLikeDO、OaVoteOptionDO、OaVoteRecordDO |
| 企业云盘 (file) | 树形文件节点（上传/复制/移动/重命名/回收站）、共享权限、收藏、容量统计 | OaFileNodeDO、OaFilePermissionDO、OaFileFavoriteDO |
| 请假申请 (leave) | 请假单草稿/提交/查询，BPM 审批 | OaLeaveApplyDO |
| 企业邮箱 (mail) | 服务商配置、账号管理、文件夹、邮件索引同步/收发/草稿/附件 | OaMailProviderDO、OaMailAccountDO、OaMailFolderDO、OaMailMessageDO |
| 会议室管理 (meetingroom) | 会议室台账、可预定查询、预定审批/开始/结束、日程与提醒 Job | OaMeetingRoomDO、OaMeetingRoomBookingDO |
| OA 笔记 (note) | 笔记目录、收藏、共享接收人、收到共享分页 | OaNoteDO、OaNoteCategoryDO、OaNoteReceiverDO |
| 公文管理 (officialdoc) | 套红模板、发文审批、收文签收（claim），发文字号/收发编号防重 | OaOfficialDocTemplateDO、OaOfficialDocSendDO、OaOfficialDocReceiveDO |
| 加班申请 (overtime) | 加班单草稿/提交/查询，BPM 审批 | OaOvertimeApplyDO |
| OA 工作计划 (plan) | 计划管理、报表分页、上级点评 | OaPlanDO |
| 转正申请 (regular) | 转正单草稿/提交/查询，BPM 审批 | OaRegularApplyDO |
| 费用报销 (reimbursement) | 报销单草稿/提交/查询，BPM 审批 | OaReimbursementDO |
| 离职申请 (resign) | 离职单（含交接人、待报销事项）草稿/提交/查询，BPM 审批 | OaResignApplyDO |
| OA 日程 (schedule) | 日程管理、参与人共享、提醒 Job | OaScheduleDO、OaScheduleParticipantDO |
| 印章管理 (seal) | 印章台账（保管人/部门）、用印申请与审批 | OaSealDO、OaSealApplyDO |
| 办公用品 (supply) | 用品台账、入库、领用申请（明细）、发放/归还 | OaSupplyItemDO、OaSupplyApplyDO、OaSupplyApplyItemDO |
| OA 任务 (task) | 任务下发/接收/反馈、状态统计、完成排行 | OaTaskDO、OaTaskReceiverDO、OaTaskLogDO |
| 出差管理 (travel) | 出差申请与出差报销（关联已通过出差单），BPM 审批 | OaTravelApplyDO、OaTravelReimbursementDO |
| 车辆管理 (vehicle) | 车辆档案、用车申请审批、还车登记审批 | OaVehicleDO、OaVehicleApplyDO、OaVehicleReturnDO |
| OA 工作汇报 (workreport) | 日报/周报等汇报提交、统计 | OaWorkReportDO |

## API 接口索引

> 全模块 41 个 Controller、264 个端点，超出单页容量，按域分节给出控制器摘要与代表性端点；完整端点清单见各 `api-{key}.md`。所有路径前缀为 `/admin-api`（yudao 网关约定）。

### OA 公告 (announcement) — 9 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaAnnouncementController | OA 公告发布/接收 | 9 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/announcement/create | POST | 创建公告 | oa:announcement:create |
| /oa/announcement/published-page | GET | 已发布公告分页 | oa:announcement:query |
| /oa/announcement/received-page | GET | 收到的公告分页 | oa:announcement:query |
| /oa/announcement/update-read-status | PUT | 标记公告为已读 | 已认证 |
| /oa/announcement/forward | POST | 转发公告给下属 | 已认证 |

### OA 考勤 (attendance) — 9 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaAttendanceController | 打卡与考勤报表 | 9 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/attendance/clock | POST | 执行当前用户打卡 | 已认证 |
| /oa/attendance/my-page | GET | 我的考勤分页 | 已认证 |
| /oa/attendance/page | GET | 考勤管理分页 | oa:attendance:query |
| /oa/attendance/week-report | GET | 获得考勤周报 | oa:attendance:query |
| /oa/attendance/month-report | GET | 获得考勤月报 | oa:attendance:query |

### OA 通讯录 (contact) — 16 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaContactController | 外部联系人管理与共享 | 10 |
| OaContactCategoryController | 联系人分类 | 6 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/contact/create | POST | 创建外部联系人 | oa:contact:create |
| /oa/contact/share | POST | 共享外部联系人 | 已认证 |
| /oa/contact/handle-share | PUT | 处理外部联系人共享 | 已认证 |
| /oa/contact/received-page | GET | 收到的共享联系人分页 | oa:contact:query |
| /oa/contact-category/list | GET | 分类列表 | oa:contact:query |

### OA 讨论区 (discussion) — 12 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaDiscussionController | 讨论主题管理 | 6 |
| OaDiscussionReplyController | 讨论回复 | 3 |
| OaDiscussionLikeController | 讨论点赞 | 2 |
| OaDiscussionVoteController | 讨论投票 | 1 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/discussion/create | POST | 发布讨论（含投票配置） | oa:discussion:create |
| /oa/discussion/manage-page | GET | 获得管理范围内的讨论分页 | oa:discussion:query |
| /oa/discussion-reply/create | POST | 回复讨论 | 已认证 |
| /oa/discussion-like/create | POST | 点赞讨论/主回复 | 已认证 |
| /oa/discussion-vote/create | POST | 参与投票 | 已认证 |

### 企业云盘 (file) — 16 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaFileNodeController | 文件/目录节点管理 | 11 |
| OaFilePermissionController | 共享权限 | 3 |
| OaFileFavoriteController | 收藏 | 2 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/file-node/get-storage | GET | 获得本人云盘空间 | oa:file:query |
| /oa/file-node/create | POST | 创建文件/目录 | oa:file:create |
| /oa/file-node/copy | POST | 复制节点 | oa:file:create |
| /oa/file-node/recycle | PUT | 移入回收站 | oa:file:delete |
| /oa/file-node/restore | PUT | 从回收站恢复 | oa:file:delete |
| /oa/file-permission/save | POST | 保存共享权限 | oa:file:share |

### 请假申请 (leave) — 5 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaLeaveApplyController | 请假单草稿/提交/查询 | 5 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/leave-apply/create | POST | 创建请假申请草稿 | oa:leave-apply:create |
| /oa/leave-apply/submit | POST | 提交请假申请（发起 BPM 流程） | oa:leave-apply:create |
| /oa/leave-apply/page | GET | 获得本人请假申请分页 | oa:leave-apply:query |
| /oa/leave-apply/get | GET | 获得请假申请详情 | oa:leave-apply:query |

### 企业邮箱 (mail) — 27 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaMailProviderController | 邮箱服务商配置（IMAP/SMTP） | 6 |
| OaMailAccountController | 用户邮箱账号 | 8 |
| OaMailFolderController | 邮箱文件夹 | 1 |
| OaMailMessageController | 邮件同步/收发/草稿（类级 oa:mail-account:query） | 12 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/mail-message/sync | POST | 同步本人邮箱索引 | 已认证（类级 oa:mail-account:query） |
| /oa/mail-message/compose | GET | 获得写信预填数据 | 已认证（类级 oa:mail-account:query） |
| /oa/mail-message/send | POST | 发送邮件（JSON/附件两种 form） | 已认证（类级 oa:mail-account:query） |
| /oa/mail-account/create | POST | 创建邮箱账号 | oa:mail-account:create |
| /oa/mail-account/test-connection | POST | 测试账号 IMAP/SMTP 连接 | oa:mail-account:query |
| /oa/mail-provider/list | GET | 服务商配置列表 | oa:mail-provider:query |
| /oa/mail-folder/list | GET | 文件夹列表 | oa:mail-account:query |

### 会议室管理 (meetingroom) — 16 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaMeetingRoomController | 会议室台账 | 6 |
| OaMeetingRoomBookingController | 会议室预定（BPM 审批） | 10 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/meeting-room/bookable-page | GET | 获得可预定会议室分页 | 已认证 |
| /oa/meeting-room-booking/create | POST | 创建会议预定 | oa:meeting-room-booking:create |
| /oa/meeting-room-booking/submit | PUT | 提交预定审批 | oa:meeting-room-booking:create |
| /oa/meeting-room-booking/start | PUT | 开始会议 | oa:meeting-room-booking:update |
| /oa/meeting-room-booking/schedule | GET | 获得会议室日程 | oa:meeting-room:query 或 oa:meeting-room-booking:query |

### OA 笔记 (note) — 15 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaNoteController | 笔记管理与共享 | 9 |
| OaNoteCategoryController | 笔记目录 | 6 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/note/create | POST | 创建笔记 | oa:note:create |
| /oa/note/update-share | PUT | 更新笔记共享接收人 | oa:note:update |
| /oa/note/update-favorite | PUT | 更新笔记收藏状态 | 已认证 |
| /oa/note/received-page | GET | 收到的共享笔记分页 | oa:note:query |
| /oa/note-category/simple-list | GET | 获得笔记目录精简列表 | 已认证 |

### 公文管理 (officialdoc) — 21 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaOfficialDocTemplateController | 套红模板 | 6 |
| OaOfficialDocSendController | 发文（BPM 审批） | 7 |
| OaOfficialDocReceiveController | 收文（BPM 审批） | 8 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/officialdoc-template/create | POST | 创建套红模板 | oa:officialdoc-template:create |
| /oa/officialdoc-send/create | POST | 创建发文 | oa:officialdoc-send:create |
| /oa/officialdoc-send/submit | POST | 提交发文审批 | oa:officialdoc-send:update |
| /oa/officialdoc-receive/create | POST | 创建收文 | oa:officialdoc-receive:create |
| /oa/officialdoc-receive/claim | PUT | 签收公文收文 | oa:officialdoc-receive:update |
| /oa/officialdoc-send/get | GET | 发文详情（收发文双方可查） | oa:officialdoc-send:query 或 oa:officialdoc-receive:query |

### 加班申请 (overtime) — 5 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaOvertimeApplyController | 加班单草稿/提交/查询 | 5 |

代表端点：`POST /oa/overtime-apply/create`（创建草稿，oa:overtime-apply:create）、`POST /oa/overtime-apply/submit`（提交，oa:overtime-apply:create）、`GET /oa/overtime-apply/page`（本人分页，oa:overtime-apply:query）

### OA 工作计划 (plan) — 7 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaPlanController | 工作计划管理/报表/点评 | 7 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/plan/create | POST | 创建工作计划 | oa:plan:create |
| /oa/plan/report-page | GET | 获得工作计划报表分页 | oa:plan:query |
| /oa/plan/add-comment | PUT | 点评工作计划 | oa:plan:comment |

### 转正申请 (regular) — 5 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaRegularApplyController | 转正单草稿/提交/查询 | 5 |

代表端点：`POST /oa/regular-apply/create`（创建草稿，oa:regular-apply:create）、`POST /oa/regular-apply/submit`（提交，oa:regular-apply:create）、`GET /oa/regular-apply/page`（本人分页，oa:regular-apply:query）

### 费用报销 (reimbursement) — 5 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaReimbursementController | 报销单草稿/提交/查询 | 5 |

代表端点：`POST /oa/reimbursement/create`（创建草稿，oa:reimbursement:create）、`POST /oa/reimbursement/submit`（提交，oa:reimbursement:create）、`GET /oa/reimbursement/page`（本人分页，oa:reimbursement:query）

### 离职申请 (resign) — 5 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaResignApplyController | 离职单草稿/提交/查询 | 5 |

代表端点：`POST /oa/resign-apply/create`（创建草稿，oa:resign-apply:create）、`POST /oa/resign-apply/submit`（提交，oa:resign-apply:create）、`GET /oa/resign-apply/page`（本人分页，oa:resign-apply:query）

### OA 日程 (schedule) — 8 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaScheduleController | 日程管理与共享 | 8 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/schedule/create | POST | 创建日程 | oa:schedule:create |
| /oa/schedule/my-page | GET | 获得我的日程分页 | oa:schedule:query |
| /oa/schedule/received-page | GET | 获得共享给我的日程分页 | oa:schedule:query |
| /oa/schedule/update-read-status | PUT | 标记日程已读 | oa:schedule:query |

### 印章管理 (seal) — 13 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaSealController | 印章台账 | 5 |
| OaSealApplyController | 用印申请（BPM 审批） | 8 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/seal/create | POST | 创建印章 | oa:seal:create |
| /oa/seal-apply/seal-page | GET | 获得可申请的印章分页 | oa:seal-apply:create 或 oa:seal-apply:query |
| /oa/seal-apply/create | POST | 创建用印申请 | oa:seal-apply:create |
| /oa/seal-apply/submit | PUT | 提交用印审批 | oa:seal-apply:create |

### 办公用品 (supply) — 17 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaSupplyItemController | 办公用品台账/入库 | 7 |
| OaSupplyApplyController | 用品领用申请（BPM 审批） | 7 |
| OaSupplyIssueController | 领用发放/归还 | 3 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/supply-item/stock-in | PUT | 办公用品入库 | oa:supply-item:stock-in |
| /oa/supply-apply/submit | PUT | 提交领用申请 | oa:supply-apply:create |
| /oa/supply-issue/issue | PUT | 发放用品 | oa:supply-issue:issue |
| /oa/supply-issue/return | PUT | 确认归还用品 | oa:supply-issue:return |

### OA 任务 (task) — 10 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaTaskController | 任务下发/接收/反馈/统计 | 10 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/task/create | POST | 创建任务 | oa:task:create |
| /oa/task/feedback | POST | 创建任务反馈 | 已认证 |
| /oa/task/get-status-count | GET | 获得我的任务状态统计 | 已认证 |
| /oa/task/get-completed-ranking | GET | 获得任务完成排行 | 已认证 |

### 出差管理 (travel) — 15 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaTravelApplyController | 出差申请（BPM 审批） | 8 |
| OaTravelReimbursementController | 出差报销（BPM 审批，关联已通过出差单） | 7 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/travel-apply/create | POST | 创建出差申请 | oa:travel-apply:save |
| /oa/travel-apply/approved-list | GET | 获得本人可关联的已通过出差申请 | 已认证 |
| /oa/travel-reimbursement/create | POST | 创建出差报销 | oa:travel-reimbursement:save |
| /oa/travel-reimbursement/submit | POST | 提交出差报销审批 | oa:travel-reimbursement:save |

### 车辆管理 (vehicle) — 20 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaVehicleController | 车辆档案 | 5 |
| OaVehicleApplyController | 用车申请（BPM 审批） | 8 |
| OaVehicleReturnController | 还车申请（BPM 审批） | 7 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/vehicle/create | POST | 创建车辆档案 | oa:vehicle:create |
| /oa/vehicle-apply/vehicle-page | GET | 获得用车申请可选的车辆分页 | oa:vehicle-apply:create |
| /oa/vehicle-apply/create | POST | 创建用车申请 | oa:vehicle-apply:create |
| /oa/vehicle-return/create | POST | 创建还车申请 | oa:vehicle-return:create |

### OA 工作汇报 (workreport) — 8 端点

| Controller | 说明 | 端点数 |
|-----------|------|-------|
| OaWorkReportController | 工作汇报提交与统计 | 8 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /oa/work-report/create | POST | 创建工作汇报 | oa:work-report:create |
| /oa/work-report/submit | PUT | 提交工作汇报 | oa:work-report:update |
| /oa/work-report/get | GET | 汇报详情 | oa:work-report:query 或 oa:work-report:statistics |
| /oa/work-report/statistics | GET | 获得工作汇报统计 | oa:work-report:statistics |

## 数据模型

> 全部 48 张表，DO 均继承 `BaseDO`（creator/createTime/updater/updateTime/deleted），本模块不使用 `TenantBaseDO`（无 tenantId 字段）。

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| oa_announcement | OA 公告主表 | BaseDO | type, priority, title, content, url, top |
| oa_announcement_receiver | 公告接收人及已读记录 | BaseDO | announcementId, receiverUserId, readStatus |
| oa_attendance | 考勤打卡记录 | BaseDO | userId, type, status, attendanceTime, attendanceIp, remark |
| oa_contact | 外部联系人 | BaseDO | categoryId, name, pinyin, sex, mobile, email, address |
| oa_contact_category | 外部联系人分类（个人维度） | BaseDO | userId, name, sort |
| oa_contact_share | 联系人共享记录 | BaseDO | contactId, userId, categoryId, handleStatus |
| oa_discussion | 讨论主题（含投票配置） | BaseDO | userId, type, title, content, fileUrls, visitCount, voteMultiple |
| oa_discussion_like | 讨论点赞记录 | BaseDO | discussionId, replyId, userId |
| oa_discussion_reply | 讨论回复（支持楼中楼） | BaseDO | discussionId, userId, parentId, replyUserId, content |
| oa_vote_option | 投票选项 | BaseDO | discussionId, title, color, sort |
| oa_vote_record | 投票记录 | BaseDO | discussionId, optionId, userId |
| oa_file_favorite | 云盘收藏 | BaseDO | nodeId, userId |
| oa_file_node | 云盘文件/目录节点（树形，含回收站） | BaseDO | parentId, type, name, extension, category, size, url |
| oa_file_permission | 云盘共享权限（可继承、可过期） | BaseDO | nodeId, subjectType, subjectId, level, inherit, expireTime |
| oa_leave_apply | 请假申请 | BaseDO | title, urgency, type, startTime, endTime, days, reason |
| oa_mail_account | 用户邮箱账号 | BaseDO | providerId, mail, username, password, defaultStatus, status |
| oa_mail_folder | 邮箱文件夹（本地索引，含 uidValidity） | BaseDO | accountId, name, type, uidValidity, syncTime, available |
| oa_mail_message | 邮件（本地索引） | BaseDO | accountId, folderId, uidValidity, uid, subject, content, replyTos |
| oa_mail_provider | 邮箱服务商配置（IMAP/SMTP 地址） | BaseDO | name, imap, smtp, status |
| oa_meeting_room | 会议室 | BaseDO | name, location, type, managerUserId, status, picUrl, seatCount |
| oa_meeting_room_booking | 会议室预定单 | BaseDO | no, roomId, title, startTime, endTime, moderatorUserId, attendeeUserIds |
| oa_note | 笔记 | BaseDO | categoryId, type, priority, title, content, favorite, fileUrls |
| oa_note_category | 笔记目录（个人维度） | BaseDO | userId, name, sort |
| oa_note_receiver | 笔记共享接收人 | BaseDO | noteId, userId |
| oa_official_doc_receive | 收文单 | BaseDO | no, sendId, receiveType, title, documentNo, secrecyLevel, urgencyLevel |
| oa_official_doc_send | 发文单 | BaseDO | no, templateId, title, noPrefix, year, sequence, documentNo |
| oa_official_doc_template | 公文套红模板 | BaseDO | name, authorityName, fontSize, noPrefix, sealPicUrl, separatorType, status |
| oa_overtime_apply | 加班申请 | BaseDO | title, urgency, type, startTime, endTime, days, reason |
| oa_plan | 工作计划 | BaseDO | type, status, title, label, content, summary, comment |
| oa_regular_apply | 转正申请 | BaseDO | title, urgency, startTime, endTime, days, experience, understanding |
| oa_reimbursement | 费用报销单 | BaseDO | title, urgency, reason, witnessUserId, customerName, paymentMethod, invoiceCount |
| oa_resign_apply | 离职申请 | BaseDO | title, urgency, reason, handoverUserId, unfinishedWork, hasPendingReimbursement, suggestion |
| oa_schedule | 日程 | BaseDO | type, priority, title, description, startTime, endTime, remind |
| oa_schedule_participant | 日程参与人及已读 | BaseDO | scheduleId, userId, readStatus, readTime |
| oa_seal | 印章台账 | BaseDO | deptId, no, name, type, category, keeperUserId, keeperDeptId |
| oa_seal_apply | 用印申请 | BaseDO | no, userId, deptId, sealId, sealNo, sealName, sealType |
| oa_supply_apply | 用品领用申请 | BaseDO | no, deptId, applyTime, useType, pickupMethod, reason, status |
| oa_supply_apply_item | 领用申请明细 | BaseDO | applyId, itemId, itemName, model, unit, manageType, applyQuantity |
| oa_supply_item | 办公用品台账 | BaseDO | deptId, name, no, category, manageType, model, unit |
| oa_task | 任务 | BaseDO | type, status, title, description, comment, startTime, endTime |
| oa_task_log | 任务状态变更日志 | BaseDO | taskId, userId, status, content |
| oa_task_receiver | 任务接收人 | BaseDO | taskId, userId, status |
| oa_travel_apply | 出差申请 | BaseDO | no, deptId, reason, startTime, endTime, days, companion |
| oa_travel_reimbursement | 出差报销单 | BaseDO | no, deptId, travelApplyId, reason, startTime, endTime, days |
| oa_vehicle | 车辆档案 | BaseDO | no, name, deptId, type, category, brandModel, seatCount |
| oa_vehicle_apply | 用车申请 | BaseDO | no, vehicleId, vehicleNo, userId, deptId, startTime, endTime |
| oa_vehicle_return | 还车申请 | BaseDO | no, applyId, vehicleId, userId, deptId, actualStartTime, startLocation |
| oa_work_report | 工作汇报 | BaseDO | no, type, status, deptId, startTime, endTime, title |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|---------|------|
| 客户端封装（防腐层） | OaMailMessageClient / OaMailMessageClientImpl | 将 JavaMail IMAP/SMTP 协议细节（连接、UID 同步、附件、发送）与业务 Service 隔离，业务层只面向本地索引模型 |
| 统一流程生命周期模板 | 14 个审批域 Service（OaLeaveApplyServiceImpl、OaReimbursementServiceImpl 等） | 以约定俗成的 create/update→submit→cancel 状态机 + `BpmModelConstants` 流程 key 统一接入 `BpmProcessInstanceApi`，保证审批单据行为一致 |
| 常量集中管理 | enums/BpmModelConstants、MessageTemplateConstants、DictTypeConstants | 流程 key、站内信模板、字典类型统一维护，避免魔法值散落 |

## 依赖关系

- **上游**（本模块依赖）:
  - 业务模块: yudao-module-system、yudao-module-infra、yudao-module-bpm
  - Framework starter: yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-job（Quartz）、yudao-spring-boot-starter-test（test）
  - 第三方: spring-boot-starter-mail（JavaMail IMAP/SMTP）、jsoup、pinyin4j
- **下游**（依赖本模块）: 无。本模块未提供 `module/oa/api` 跨模块 API 包，仓库内也没有其他模块依赖 yudao-module-oa。

## 对外暴露的 API

本模块未提供跨模块 API 包（不存在 `cn.iocoder.yudao.module.oa.api`），仅通过 admin REST 接口对外服务，故省略本节明细。

## 定时任务

| Job | 说明 |
|-----|------|
| OaScheduleReminderJob | 日程提醒：按 `yudao.oa.schedule.remind-before-hours` 提前向参与人发送站内信 |
| OaMeetingRoomBookingReminderJob | 会议开始提醒与过期未开始预定自动取消 |

## 详细文档

- [api-announcement.md](api-announcement.md) - OA 公告
- [api-attendance.md](api-attendance.md) - OA 考勤
- [api-contact.md](api-contact.md) - OA 通讯录
- [api-discussion.md](api-discussion.md) - OA 讨论区
- [api-file.md](api-file.md) - 企业云盘
- [api-leave.md](api-leave.md) - 请假申请
- [api-mail.md](api-mail.md) - 企业邮箱
- [api-meetingroom.md](api-meetingroom.md) - 会议室管理
- [api-note.md](api-note.md) - OA 笔记
- [api-officialdoc.md](api-officialdoc.md) - 公文管理
- [api-overtime.md](api-overtime.md) - 加班申请
- [api-plan.md](api-plan.md) - OA 工作计划
- [api-regular.md](api-regular.md) - 转正申请
- [api-reimbursement.md](api-reimbursement.md) - 费用报销
- [api-resign.md](api-resign.md) - 离职申请
- [api-schedule.md](api-schedule.md) - OA 日程
- [api-seal.md](api-seal.md) - 印章管理
- [api-supply.md](api-supply.md) - 办公用品
- [api-task.md](api-task.md) - OA 任务
- [api-travel.md](api-travel.md) - 出差管理
- [api-vehicle.md](api-vehicle.md) - 车辆管理
- [api-workreport.md](api-workreport.md) - OA 工作汇报
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
