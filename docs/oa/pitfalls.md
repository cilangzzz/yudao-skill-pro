# 注意事项与已知坑点

> 使用 oa 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 oa_* 表未声明忽略租户，开启多租户后 SQL 会被拼上 tenant_id

**问题**: 在 `yudao.tenant.enable: true`（yudao-server 默认配置）的部署下，访问 OA 模块接口可能直接报 `Unknown column 'tenant_id'` 之类的 SQL 错误。

**原因**: 本模块 48 张表对应的 DO（如 `OaLeaveApplyDO`、`OaAttendanceDO`）全部继承 `BaseDO`，既没有 tenantId 字段，也没有类级 `@TenantIgnore` 注解。而框架的 `TenantDatabaseInterceptor#computeIgnoreTable`（yudao-spring-boot-starter-biz-tenant）只对 `TenantBaseDO` 子类或标注 `@TenantIgnore` 的实体返回"忽略"，其余注册过的表一律追加 `tenant_id = ?` 条件。

**解决**: 二选一：给 OA 全部 DO 类补类级 `@TenantIgnore`（参考 infra 模块 `DataSourceConfigDO` 的写法），或在 `yudao.tenant.ignore-tables` 配置中登记全部 oa_* 表名。新增 OA 表时务必同步处理，否则一上线就报错。

### 1.2 定时任务依赖 @TenantJob 提供租户上下文

**问题**: 仿写 OA 的 Quartz Job 时漏掉 `@TenantJob`，日程/会议提醒会发送失败或查不到跨模块数据。

**原因**: `OaScheduleReminderJob` 与 `OaMeetingRoomBookingReminderJob` 都标注了 `@TenantJob`，按租户逐个执行。虽然 OA 表本身不参与租户过滤，但 Job 内部调用的 `NotifyMessageSendApi`（日程/会议提醒站内信模板）、`AdminUserApi` 等走的是 system 模块的租户隔离表，必须持有租户上下文才能执行。

**解决**: 新增 Job 必须保留 `@TenantJob` 注解；提醒模板编码（`MessageTemplateConstants.SCHEDULE_REMINDER`、`MEETING_ROOM_BOOKING_REMINDER`）需要在对应租户的站内信模板中预置，否则发送环节报错。

## 2. 单号生成相关

### 2.1 Redis 单号自增与过期非原子，Redis 丢数据会导致当天单号重复

**问题**: 创建单据偶发抛 `OFFICIAL_DOC_SEND_NO_DUPLICATE`、`VEHICLE_APPLY_NO_DUPLICATE` 等"单号已存在"错误。

**原因**: `OaNoRedisDAO#generate` 先 `opsForValue().increment` 再 `expire`，两步非原子；key 形如 `FW + yyyyMMdd + 6位序号` 按天分片。Redis 未开持久化、主从切换或误 flush 后计数清零，当天再次生成的单号会与已入库单号冲突，目前只靠 `selectByNo` 查重兜底报错。

**解决**: 生产环境 Redis 开启持久化；各单据表的 `no` 列建唯一索引作为最终防线；创建失败后重试即可（increment 不会回退，重试会拿到下一个号）。

## 3. 事务与并发相关

### 3.1 BPM 审批回调在 BPM 事务内同步执行，回调抛异常会拖垮审批操作

**问题**: 审批通过/撤销时报错回滚，Flowable 流程已推进但业务单据状态未更新（或反之）。

**原因**: OA 的 14 个监听器（`OaLeaveApplyStatusListener`、`OaVehicleApplyStatusListener` 等）继承 `BpmProcessInstanceStatusEventListener`，是普通同步 `ApplicationListener`；BPM 侧 `BpmProcessInstanceEventPublisher` 通过 `ApplicationEventPublisher` 同线程发布事件，监听器与审批操作共用同一个事务。回调内任何异常（包括 `Long.valueOf(event.getBusinessKey())` 转换失败、`OFFICIAL_DOC_PROCESS_MISMATCH`）都会让整个审批事务回滚。

**解决**: 监听器 `onEvent` 里只做状态回写；非预期数据 log 后 return，参考 `OaMeetingRoomBookingServiceImpl#updateMeetingRoomBookingStatus` 对非 RUNNING 状态直接 return 的幂等写法，不要在回调里抛业务异常。

### 3.2 草稿不占用时段，提交时查重无锁，并发提交可双占会议室/车辆

**问题**: 两个请求同时提交同一时段的会议室预定或用车申请，都能成功，形成双占。

**原因**: 草稿阶段刻意不校验时段占用（`OaVehicleApplyServiceImpl#createVehicleApply` 注释"草稿不占用预约时段"）；`submitVehicleApply` / `submitMeetingRoomBooking` 提交时才用 `selectCountByVehicleIdAndTimeOverlap`、`selectListByRoomIdAndTimeOverlap` 检查冲突，普通 SELECT 不加锁，两个并发事务都能通过检查后各自占用。

**解决**: 提交事务内先对资源行加 `FOR UPDATE`（参考 `OaFileNodeServiceImpl#lockFileNode` 的 `selectByIdForUpdate` 做法）再查冲突，或依赖数据库层排他约束；前端做提交按钮防重。

### 3.3 邮箱账号行锁依赖调用方事务，且锁内执行慢速 IMAP 网络 IO

**问题**: 在无事务方法里调用 `lockMailAccount` 以为已串行化，实际锁立即释放；或多个同步请求长时间互相阻塞。

**原因**: `OaMailAccountServiceImpl#lockMailAccount` 自身没有 `@Transactional`，仅靠 `selectByIdForUpdate`（`OaMailAccountMapper` 中 `last("FOR UPDATE")`）加行锁，调用方无事务时按自动提交执行、锁即刻失效。而 `OaMailMessageServiceImpl#syncMailMessageList` 在 `@Transactional` 内全程持锁抓取远端邮件（单文件夹上限 `MAX_MESSAGES = 100000`、每批 100 条），邮箱慢时数据库事务和行锁都被长时间持有。

**解决**: 邮件的读详情/同步/写操作入口必须保持 `@Transactional`（现有 `OaMailMessageServiceImpl` 各方法已满足），新增入口照抄该模式；`lockMailAccount` 之后应像 `getMailMessage` 一样在锁内重查索引（`selectByIdForUpdate`），避免使用已失效的旧数据。

### 3.4 自调用事务与循环依赖：getSelf() 与 @Lazy 不能随手删

**问题**: 重构后会议提醒不再逐条独立提交（一条失败全部回滚），或应用启动报循环依赖。

**原因**: `OaMeetingRoomBookingServiceImpl#sendMeetingRoomBookingReminders` 通过私有 `getSelf()`（`SpringUtil.getBean(getClass())`）取 Spring 代理后再调 `sendMeetingRoomBookingReminder`，保证"单条会议提醒一个事务、失败不影响其他会议"；另外模块内多处用 `@Lazy` 解循环依赖（`OaLeaveApplyServiceImpl` 注入 `OaAttendanceService`、`OaFileNodeServiceImpl` 注入 `OaFilePermissionService`/`OaFileFavoriteService`、`OaMeetingRoomBookingServiceImpl` 注入 `OaMeetingRoomService`），代码里都有"延迟加载，避免循环依赖"注释。

**解决**: 同类内部直接 `this.xxx()` 调用 `@Transactional` 方法会因代理失效导致事务不生效，必须走 `getSelf()` 式代理调用；`@Lazy` 注入点不可随意删除，新增服务间相互引用时优先评估是否真的需要双向调用。

## 4. 状态机相关

### 4.1 审批结果回写以 RUNNING 为闸门，还车回写用 CAS 防并发

**问题**: BPM 事件重复投递导致状态被覆盖，或多个还车单并发提交时回写错乱。

**原因**: `OaVehicleApplyServiceImpl#updateVehicleApplyStatus`、`OaMeetingRoomBookingServiceImpl#updateMeetingRoomBookingStatus` 等回调先判断 `status != RUNNING` 就 return，保证审批结果只写一次；还车流程在 `updateVehicleApplyReturnStatus` 里使用 `updateReturnStatusByIdAndReturnStatus`（按原状态做条件更新，`updateCount == 0` 抛 `VEHICLE_RETURN_STATUS_INVALID`），防止多个还车草稿同时提交成功。

**解决**: 新增审批域时（`BpmModelConstants` 已定义 14 个流程 key）必须复刻这两个模式：回调用 RUNNING 闸门幂等、并发回写用条件更新 CAS。取消单据依赖事件回写释放时段（`cancelVehicleApply` 注释"事件回写后释放预约"），不要在 cancel 方法里手工改状态，避免与监听器重复处理。

### 4.2 默认配置下"正常"下班打卡状态不可达

**问题**: 员工 17:00 后无法打卡（报 `ATTENDANCE_CLOCK_TIME_INVALID`），17:00 前的下班打卡全部记为"早退"，下班的 NORMAL 状态永远不会出现。

**原因**: `OaAttendanceServiceImpl#clockAttendance` 只允许 `(clockBeginTime, workEndTime)` 开区间内打卡（默认 5:00-17:00），而 `calculateAttendanceStatus` 对早于 `workEndTime` 的下班打卡一律返回 EARLY。两个判断共用 `workEndTime`，`OaAttendanceTypeEnum.CLOCK_OUT` 的 NORMAL 分支在数学上不可达（`OaAttendanceServiceImplTest` 断言的下班状态也是 EARLY）。

**解决**: 这是有意设计：下班卡仅作兜底记录。确需修正状态走管理员接口 `updateAttendance`（`validateAttendanceStatus` 允许 CLOCK_OUT 修正为 NORMAL/EARLY）；如需调整口径，修改 `yudao.oa.attendance.work-end-time` 配置前先想清楚它会同时改变打卡截止时间和早退判定线。

## 5. 邮箱集成相关

### 5.1 远端 IMAP/SMTP 操作不可回滚，失败码按"结果未确认"处理

**问题**: 发信/删信/存草稿失败后盲目重试，造成重复发信或本地索引与远端不一致。

**原因**: `OaMailMessageServiceImpl` 各写操作在 `@Transactional` 内先操作远端再改本地索引，事务只能回滚本地部分；代码用一组 `*_UNCONFIRMED` 错误码（`MAIL_SEND_UNCONFIRMED`、`MAIL_DELETE_UNCONFIRMED`、`MAIL_DRAFT_SAVE_UNCONFIRMED`、`MAIL_RESTORE_UNCONFIRMED`）表达"结果未知"。`sendMailMessage` 特意把"SMTP 发送成功"与"已发送副本/草稿清理"分成两段，第二段失败返回提示字符串而非异常，避免用户重发。

**解决**: 调用方收到 `*_UNCONFIRMED` 类错误时先执行 `syncMailMessageList` 重新同步再判断，禁止直接重发；草稿替换要求服务器支持 UIDPLUS 能力（`hasCapability` 检查，不支持则抛 `MAIL_DRAFT_REPLACE_UNSUPPORTED`），服务商能力差异属于常态，报错文案均引导用户回原邮箱客户端操作。

### 5.2 邮件索引以 uidValidity:uid 为快照键，UID 失效必须重新同步

**问题**: 对旧索引读详情/移动/删除时报 `MAIL_UID_EXPIRED` 或 `MAIL_MESSAGE_NOT_EXISTS`。

**原因**: 本地只存邮件索引（`OaMailMessageDO` 的 `uid` + `uidValidity` 字段），远端文件夹 UIDValidity 变化（文件夹重建、账号迁移）后旧 UID 全部失效。`OaMailMessageClientImpl#getMessage` 显式比较 `getUIDValidity() != index.getUidValidity()` 抛 `MAIL_UID_EXPIRED`；同步时 `getMessageList` 还用 `folder.getMessageCount() != count` 抛 `MAIL_SYNC_CHANGED`，保证整轮快照期间远端未变化。

**解决**: 出现这类错误码时引导用户重新同步：`syncFolder` 按 `uidValidity:uid` 对比完整快照，保留本地主键做增量更新，快照中缺失的索引删除；任何持久化逻辑都不要使用 IMAP sequence number，只允许 UID。

## 6. 权限相关

### 6.1 权限标识命名不统一，部分端点仅登录即可访问

**问题**: 按通用的 `:create`/`:update` 命名给角色配权限后，出差保存接口仍然 403；或误以为所有 OA 接口都有按钮级权限校验。

**原因**: travel/travel-reimbursement 的 create/update 使用自定义权限 `oa:travel-apply:save`（见 `OaTravelApplyController`），不是 `:create`/`:update`；`OaMailMessageController` 把 `@PreAuthorize("@ss.hasPermission('oa:mail-account:query')")` 标在类级，方法级不再重复标注；另有打卡 `/clock`、各 `my-page`/`received-page`、`share/handle-share`、`forward`、`feedback`、`simple-list` 等个人域端点没有 `@PreAuthorize`，登录即可访问。

**解决**: 配置角色菜单权限时以 Controller 注解为准，出差/差旅报销要单独授权 `:save`；个人域接口的数据隔离依赖 Service 层归属校验（如 `validateBookingOwner`、`validateAttendanceExists` 将越界记录与不存在记录统一返回 `*_NOT_EXISTS` 防泄露），新增此类接口不要漏写 owner 校验。
