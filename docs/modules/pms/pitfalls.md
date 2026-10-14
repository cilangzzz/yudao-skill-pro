# 注意事项与已知坑点

> 使用 pms 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 全部表参与租户隔离，但 DO 不含 tenantId 字段，定时任务必须加 @TenantJob

**问题**: 新增业务表或定时任务后，Job 执行报租户相关异常，或误以为"DO 没有 tenantId 字段 = 不做租户隔离"而写出跨租户查询。

**原因**: pms 模块 33 个 DO 全部继承 `BaseDO`（如 `PmsWorkItemDO extends BaseDO`），但建表脚本 `yudao-module-pms/src/test/resources/sql/create_tables.sql` 中每张表都带 `tenant_id bigint NOT NULL DEFAULT 0`。租户过滤由 `TenantLineInnerInterceptor` 在 SQL 层自动追加，与 DO 是否映射该列无关；模块内唯一的例外是分享令牌接口上的 `@TenantIgnore`。定时任务侧，`PmsKnowledgeRecycleCleanJob` 的 `execute` 标注了 `@TenantJob`，会逐租户执行清理；漏加该注解时任务运行在无租户上下文环境，SQL 拼出 `tenant_id = null` 导致查不到数据或直接报错。

**解决**:

```java
// 1. 新建 pms 表的 DDL 必须包含 tenant_id 列，DO 继承 BaseDO 即可，不需要 TenantBaseDO
// 2. 新增 Job 必须标注 @TenantJob，让框架逐租户执行
@Override
@TenantJob
public String execute(String param) { ... }
```

### 1.2 分享令牌接口是 @PermitAll + @TenantIgnore 的匿名入口，重新开启分享会更换令牌

**问题**: 匿名访问 `/pms/kb/document-share/get-by-token` 报错；或分享链接"突然失效"；或误以为该接口有租户/登录态校验。

**原因**: `PmsKnowledgeDocumentShareController#getDocumentByToken` 同时标注 `@PermitAll` 和 `@TenantIgnore`：无登录用户、无租户上下文，SQL 不追加租户条件。`PmsKnowledgeDocumentShareServiceImpl#getDocumentByShareToken` 只校验分享记录处于 ENABLE 状态且文档为 NORMAL 状态，边界完全依赖 token 本身（`create_tables.sql` 中 `pms_knowledge_document_share.token` 有 UNIQUE 约束，token 为 `IdUtil.fastSimpleUUID()`）。另外 `openShare` 对已存在但被关闭的分享执行 `updateToReopen` 时会调用 `generateShareToken()` 生成**新**令牌，旧链接立即失效。

**解决**: 新增匿名接口时必须成对加上 `@PermitAll` + `@TenantIgnore`（否则租户插件在无上下文时拼出无效条件），并像 `getDocumentByShareToken` 一样仅依赖唯一 token + 状态机做访问控制；FILE 类型文档走 `fileApi.presignGetUrl` 预签名，注意预签名有效期与分享开关状态不同步的问题。业务上需要告知用户：关闭后再次开启分享，旧分享链接全部作废。

## 2. 事务相关

### 2.1 Excel 导入"逐行失败继续"与外层 @Transactional 冲突，触发 UnexpectedRollbackException

**问题**: 工作项 Excel 导入时，某行失败后后续行仍显示"成功"，但最终接口报 500（`UnexpectedRollbackException`），**全部**导入数据（含已"成功"的行）被回滚。

**原因**: `PmsWorkItemServiceImpl#importWorkItemList` 标注了 `@Transactional(rollbackFor = Exception.class)`（注释写"异常则回滚所有导入"），但循环体内 `catch (Exception ex)` 把每行异常吞掉继续导入。其中 `createWorkItem(...)` 是 this 自调用（不经过代理，抛异常不会标记 rollback-only），而步骤 3.3 的 `workItemWorkLogService.createWorkItemWorkLog(...)` 是跨 Bean 代理调用且该方法自带 `@Transactional`——它一旦抛异常（如工时字段超长导致 insert 失败），事务同步器会把共享事务标记为 rollback-only；外层 catch 继续循环、返回 `successCount/failureReasons`，最后提交时 Spring 抛 `UnexpectedRollbackException`。

**解决**: 二选一：去掉外层 `@Transactional`，让每行经代理调用各自独立提交（失败行只影响自己，与部分成功语义匹配）；或保留全量回滚语义，但去掉逐行 catch，任一行失败立即抛出、返回全部失败。不要维持现状这种"看似部分成功、实际整体回滚"的组合。

### 2.2 站内信在事务提交前发送：可能产生"幽灵通知"，且依赖预置消息模板

**问题**: 工作项指派/知识文档分享的通知发出后，主业务却因后续异常回滚了，接收人看到一条指向不存在对象的站内信；或通知始终发不出去但接口正常返回。

**原因**: `PmsWorkItemServiceImpl#sendWorkItemAssignedNotify` 与 `PmsKnowledgeDocumentShareServiceImpl#sendKnowledgeDocumentSharedNotify` 都在 `@Transactional` 方法内部（commit 之前）调用 `notifyMessageSendApi.sendSingleMessageToAdmin`，事务回滚不会撤回已发送的通知；同时通知 RPC 拉长了事务持锁时间。两处均 `catch (RuntimeException)` 仅打 warn 日志——这是刻意设计（通知失败不阻断主业务），代价是模板缺失时通知**静默丢失**。模板编码见 `MessageTemplateConstants`：`pms_work_item_assigned`、`pms_knowledge_document_shared`，参数含 `projectName/serialNumber/workItemName/route` 与 `documentTitle/route`。

**解决**: 部署前必须在 system 模块预置这两个站内信模板，否则指派/分享通知永远只有 warn 日志；对一致性要求更高的场景，可改为事务提交后发送（`TransactionSynchronization.afterCommit`）或 MQ 异步化。

### 2.3 工作项编辑依赖 updateForEdit 强制置空字段，改用 updateById 会丢"清空"语义

**问题**: 新增可空字段后直接用 `updateById` 实现编辑，前端把字段清空后提交，数据库里旧值未被清掉。

**原因**: MyBatis-Plus 的 `updateById` 默认跳过 null 字段。`PmsWorkItemMapper#updateForEdit` 因此用 `LambdaUpdateWrapper` 对 `description、assigneeUserId、iterationId、parentId、relatedRequirementId、defectType、startTime、endTime、estimatedHours、fileUrls、labelIds` 共 11 个字段逐一执行 `.set(字段 == null, 字段, null)` 显式置空。同类的保护还有 `PmsProjectServiceImpl#updateProject`：`BeanUtils.toBean(...).setType(null)` 后 `updateById`——利用 null 被跳过的特性保证项目类型不可修改。

**解决**: 编辑工作项的清空语义必须走 `updateForEdit`，新增可空字段时记得同步在该方法里补一行 `.set(...)`；反之，想"字段不可改"就可以模仿 `updateProject` 把 VO 字段置 null 后走 `updateById`。

## 3. 并发相关

### 3.1 序列号/看板 sort 的 max+1 读取与状态初始化，都依赖建表脚本中并不存在的唯一索引

**问题**: 并发创建工作项时 `serialNumber` 重复、并发拖拽看板时 `sort` 重复；并发创建项目时出现重复的"未开始/进行中/已完成"状态行。

**原因**: 三处并发防御都隐式依赖数据库唯一索引，而 `yudao-module-pms/src/test/resources/sql/create_tables.sql` 里除主键外只有 `pms_knowledge_document_share.token` 一处 UNIQUE：
1. `PmsWorkItemMapper#selectMaxSerialNumberByProjectId` / `#selectMaxSortByStatusId` 是"查 max 后在 Java 里 +1"的模式，`pms_work_item` 无 `(project_id, serial_number)` 唯一约束，并发下产生重复编号；
2. `PmsWorkItemStatusServiceImpl#initMissingSystemWorkItemStatuses`（创建项目时调用）按 `systemCode` 补插默认状态并 `catch (DuplicateKeyException ignored)` 容忍并发重复初始化，但 `pms_work_item_status` 只有主键——唯一索引缺失时该 catch 是死代码，并发下会插入重复系统状态；
3. `PmsWorkItemStatusServiceImpl#updateWorkItemStatusSort` 注释里的"按状态编号稳定加锁"实际只是 `Collections.sort(statusIds)` 后 `updateBatch`，用于降低死锁概率，并非真正加锁。

**解决**: 生产库为 `pms_work_item (project_id, serial_number)` 与 `pms_work_item_status (project_id, work_item_type, name)` 补唯一索引，让 `DuplicateKeyException` 兜底真正生效；对严格连续的编号需求改为事务内 `SELECT ... FOR UPDATE` 项目行再取 max。普通排序重复影响有限，现有查询已带 `orderByAsc(id)` 稳定次序兜底。

### 3.2 项目/知识库成员列表采用"删除-重建"，并发编辑互相覆盖

**问题**: 两个管理员同时编辑项目或知识库成员，后保存者覆盖前者的全部调整；成员刚被移除却又出现在列表里。

**原因**: `PmsProjectMemberServiceImpl#updateProjectMemberList` 先 `deleteByProjectIdAndUserIds` 再 `insertBatch`；`PmsKnowledgeLibraryMemberServiceImpl#updateLibraryMemberList` 先 `deleteByLibraryIdAndLevels(ADMIN, MEMBER)` 再 `insertBatch`，且重建后还要级联清理内容协作权限（`contentPermissionService.deleteContentPermissionMembersByLibraryId`）。全程在一个事务内但无版本号/行锁，读到的 oldMembers 快照在并发下过期。另有隐含规则：项目成员请求中包含创建人会抛 `PROJECT_MEMBER_CREATOR_CANNOT_REMOVE`，伪造 OWNER/CREATOR 级别分别抛 `PROJECT_MEMBER_OWNER_LEVEL_CANNOT_ASSIGN` / `KNOWLEDGE_LIBRARY_MEMBERS_INVALID`。

**解决**: 成员管理入口做前端互斥或后端按 `updateTime` 乐观校验；理解"创建人不在请求中、级别不可指定"的约定，避免前端把创建人带回请求导致保存失败。

## 4. 权限模型相关

### 4.1 内容权限批量校验"一票否决"，且库管理员/公开级别会短路成员匹配

**问题**: 批量接口整页报 `KNOWLEDGE_CONTENT_PERMISSION_NOT_EXISTS`；或发现非知识库成员竟能读写公开库的内容；或排查权限时发现配置的协作者"不生效"。

**原因**: `PmsKnowledgeContentPermissionServiceImpl#getCurrentUserContentPermissionLevelMap` 要求传入的 permissionIds 全部存在且都属于同一 `libraryId`，否则整体抛异常——复用它做批量过滤时，一个脏 ID 会拖垮整批数据。级别解析顺序为：库管理员（`isLibraryAdmin`，含部门继承的管理员）直接得 `MANAGE`；其次 `openStatus=true` 的公开权限对**所有人**（包括仅"可读公开库"的非成员）按 `openLevel` 生效；再次按用户、部门显式协作权限匹配；都未命中则为 null（`KNOWLEDGE_CONTENT_ACCESS_DENIED`）。用户/部门成员匹配依赖 `adminUserApi.getUser(userId)` 取部门号，鉴权链路里有隐藏 RPC，循环单条校验时是 N+1。

**解决**: 批量过滤优先用 `getReadableContentPermissionIdSet`（不存在即跳过而非抛错）；给内容配置"可编辑/可管理"的公开级别前确认公开库语义；单条循环校验改为批量 map 查询。成员身份判断沿用 `PmsKnowledgeLibraryMemberServiceImpl#getLibraryMember` 的"用户 → 部门"两级回退，排查权限问题时先确认用户部门是否被加进了库。

### 4.2 @PreAuthorize 权限标识大量复用，授权粒度粗于接口粒度

**问题**: 给角色勾选了某功能权限后，用户能访问一批"看起来无关"的接口；或以为某接口有权限控制，实际仅需登录。

**原因**: kb 域内容与互动端点（文档增删改、评论、点赞、收藏、分享、回收站等）不单独建权限，统一复用 `pms:kb:library:*`（如分享开关用 `pms:kb:library:update`、查询用 `pms:kb:library:query`）；pm 域工作项/状态/标签/评论/工时统一复用 `pms:pm:work-item:*`；模板域独立为 `pms:kb:library-template:*`，但 `/pms/kb/library-template/simple-list` 未加 `@PreAuthorize`，登录即可访问。接口级细粒度实际由 Service 层的成员级别校验（`validateProjectWritable`、`validateLibraryAdmin`、`validateContentPermissionWritable` 等）完成。

**解决**: 权限申报与菜单配置时按"kb:library / kb:library-template / pm:work-item"三组理解，不要期望按 Controller 拆分授权；新增接口时保持现有复用惯例，业务级访问控制写进 Service 校验而不是依赖 `@PreAuthorize`；模板 simple-list 这类下拉数据接口如需收紧，显式加 `@PreAuthorize`。

## 5. 状态机与数据一致性

### 5.1 工作项/项目生命周期状态机：仅 ACTIVE 可写，彻底删除仅限回收站

**问题**: 对已归档/已回收的工作项或项目执行更新、拖拽状态、删除时报 `WORK_ITEM_LIFECYCLE_STATUS_INVALID` / `PROJECT_STATUS_INVALID`；或新增写操作漏校验生命周期，改动"看不见的数据"。

**原因**: 工作项生命周期 `ACTIVE → ARCHIVED / RECYCLED`：`PmsWorkItemServiceImpl` 中除查询外所有写方法都先 `validateActiveWorkItem` + `validateActiveProject`；`archiveWorkItem` 写 `archiveTime`、清 `recycleTime`，`recycleWorkItem` 保留 `archiveTime`、写 `recycleTime`，`restoreWorkItem` 两者清空，`deleteWorkItem` 仅允许 RECYCLED（`WORK_ITEM_DELETE_STATUS_INVALID`）且先解除子项与关联需求引用（`updateParentIdToNullByParentId` / `updateRelatedRequirementIdToNullByRelatedRequirementId`）再删关联数据。项目侧 `archiveProject/recycleProject` 用带 `WHERE status = ACTIVE` 条件的 `updateStatusAndArchiveTimeById/updateStatusAndRecycleTimeById` 做 CAS，`updateCount == 0` 即抛 `PROJECT_STATUS_INVALID`，并发下不会双重归档；`deleteProject` 仅回收站状态且要求 Owner 权限。迭代状态机为 `PLANNED → ACTIVE → COMPLETED`（`PmsIterationServiceImpl#startIteration/completeIteration` 单向，不可重启）。

**解决**: 新增工作项/项目写操作时复用 `getWritableWorkItem` 或成对调用 `validateActiveWorkItem` + `validateActiveProject`；状态迁移用条件 UPDATE + 受影响行数判断，不要先查后改。看板状态删除同样有状态机约束：默认状态受 `WORK_ITEM_STATUS_DEFAULT_CANNOT_DELETE` 保护，列内仍有工作项时必须提供同项目同类型的目标状态（否则 `WORK_ITEM_STATUS_TRANSFER_INVALID`），迁移由 `transferWorkItemStatus` 一条 UPDATE 完成。

### 5.2 回收站恢复：独立删除的子树受保护，父级已失效时重挂根目录

**问题**: 恢复整个知识库/文件夹后，部分内容"没有回来"；或恢复出来的文档/文件夹不在原来的位置；或彻底删除库后独立删除过的内容也没了。

**原因**: `PmsKnowledgeRecycleServiceImpl` 的设计是"只记录显式删除的根对象"（`recycleLibrary/recycleFolder/recycleDocument` 各自只 insert 一条记录，级联内容置 RECYCLED 状态）。恢复时 `restoreLibrary/restoreFolder/restoreDocument` 通过 `excludeProtectedFolders/excludeProtectedDocuments` 把仍被其他回收站记录保护的子树从恢复集合中剔除——所以"整库恢复"不会捎带恢复之前单独删除的子树，后者仍留在回收站等各自恢复。恢复根对象的父文件夹/父文档若不存在或仍处于 RECYCLED，则被重挂到 `PARENT_ID_ROOT` / `FOLDER_ID_ROOT`（目录结构与删除前不同）。`permanentDeleteLibrary` 则物理删除库内全部内容（包括独立删除子树），并连带清理收藏、点赞、浏览、分享、评论、内容权限、成员与分组关系。层级解析 `getFolderDescendantIds/getDocumentDescendantIds` 用已访问集合 + `Short.MAX_VALUE` 深度上限防环。

**解决**: 恢复操作按"谁的回收站记录谁负责"理解；需要完整还原时，先恢复库，再逐条恢复库内剩余回收站记录。彻底删除库前确认其中不存在还想保留的独立删除内容（先恢复再删，或接受全部丢失）。

### 5.3 统计口径：趋势/燃尽按 updateTime 近似还原，待规划分页在内存中完成

**问题**: 迭代概览的每日状态趋势、项目概况的完成趋势"不准"——批量导入、回收站恢复或集中编辑后某天数字异常；待规划区数据量大时接口变慢。

**原因**: `PmsIterationServiceImpl#buildStatusTrends` 与 `PmsProjectServiceImpl#getProjectOverview` 的完成趋势都用**当前** `status` + `updateTime.toLocalDate()` 反推每日数量，模块没有状态流转历史表，任何批量写操作都会集中改 `updateTime` 使趋势失真；燃尽图 `buildBurnDowns` 按工时记录的 `createTime` 聚合，未填工时的天数无法体现。另外 `PmsWorkItemServiceImpl#getWorkItemPage` 在 `planningOnly + unplannedOnly` 时走"全量查询 + `workItemUserSortService.sortWorkItemList` 内存排序 + `PageUtils.buildPageResult` 内存分页"（代码注释自认"难以在 SQL 中等价表达"）。

**解决**: 把趋势/燃尽视为参考值而非审计数据；业务要求精确时需另建状态流转流水。待规划区超大项目（数千根工作项）需要关注该接口的内存与耗时，必要时拆分"个人排序"与"分页"为两步查询。
