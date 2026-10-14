# 项目管理系统模块 (pms)

> yudao PMS 模块：以「项目 → 迭代 → 工作项」为核心研发协作链路，配套看板、工时登记、工作台，并内置一套多成员协作的知识库（文库）系统，覆盖项目/知识两级成员权限模型。

## 模块概述

- **模块路径**: yudao-module-pms
- **业务定位**: 提供项目全生命周期管理（创建、归档、回收站、模板化初始化）、迭代规划与进度统计、需求/任务/缺陷三类工作项的看板流转与工时登记，以及支持文件夹/文档树、协作权限、评论点赞分享、回收站的团队知识库。权限模型为「成员级别 + 数据行级校验」，几乎所有操作都在 Service 层按当前登录用户做可读/可写/管理员校验。
- **技术栈**: Spring Boot 2.7.18（JDK8，`javax.*` 命名空间）/ MyBatis-Plus / Swagger v3 (springdoc GroupedOpenApi 分组 `pms`) / Quartz（回收站清理 Job）/ Lombok

## 设计原则

| 原则 | 说明 |
|-----|------|
| 两级业务域 | `pm`（项目/迭代/工作项/工作台）与 `kb`（知识库）两个子域，URL 前缀分别为 `/pms/pm/*` 与 `/pms/kb/*`，数据模型互不耦合 |
| 成员级别权限 | 项目成员与知识库成员均以 level 字段区分「拥有者/管理员/可编辑/只读」，超级管理员通过 `PermissionApi.hasAnyRoles(SUPER_ADMIN)` 放行 |
| 软删除 + 回收站双态 | 项目、工作项、知识库/文件夹/文档均走「回收站 → 彻底删除」两段式生命周期，知识库另有独立回收站记录表与到期清理 Job |
| VO 拼接内聚 | Controller 内私有 `buildXxxRespVO` 方法统一批量查询关联数据（用户、状态、迭代、标签）后拼接展示字段，避免 N+1 |
| 枚举驱动文案 | 工作项动态、错误信息等通过枚举常量 + `format(...)` 生成，站点消息复用 `MessageTemplateConstants` 站内信模板 |
| 状态可配置 | 工作项状态/看板列按「项目 + 工作项类型」维度由用户自定义维护，语义状态（statusType）与流转状态分离 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|--------|------|----------|
| 项目管理 | 项目增删改查、星标收藏、个人分组、归档/回收站、成员与权限级别、公告、项目模板一键初始化 | PmsProjectDO、PmsProjectMemberDO、PmsProjectGroupDO、PmsProjectTemplateDO、PmsProjectAnnouncementDO |
| 项目迭代 | 迭代创建/开始/完成/删除、进度统计、迭代概览（近期动态） | PmsIterationDO |
| 工作项管理 | 需求/任务/缺陷工作项的创建、状态流转、看板排序、参与人、标签、评论、动态、工时登记与项目工时报表、Excel 导入导出、归档/回收站 | PmsWorkItemDO、PmsWorkItemStatusDO、PmsWorkItemBoardDO、PmsWorkItemLabelDO、PmsWorkItemCommentDO、PmsWorkItemActivityDO、PmsWorkItemWorkLogDO |
| 工作台 | 聚合「我负责的工作项」「我负责的迭代」与未完成事项数量 | PmsWorkItemDO、PmsIterationDO |
| 知识库与分组 | 知识库创建/删除/退出、成员（用户/部门）管理、个人分组、知识库模板 | PmsKnowledgeLibraryDO、PmsKnowledgeLibraryMemberDO、PmsKnowledgeGroupDO、PmsKnowledgeLibraryTemplateDO |
| 知识库内容 | 文件夹/富文本文档/上传文件三类内容的树形组织、移动、MySQL 全局搜索、文档标签、内容级协作权限 | PmsKnowledgeFolderDO、PmsKnowledgeDocumentDO、PmsKnowledgeDocumentLabelDO、PmsKnowledgeContentPermissionDO |
| 知识库互动 | 文档评论（两级回复）、点赞、内部分享与令牌公开分享、关注收藏、最近浏览 | PmsKnowledgeDocumentCommentDO、PmsKnowledgeDocumentLikeDO、PmsKnowledgeDocumentShareDO、PmsKnowledgeFavoriteDO、PmsKnowledgeViewRecordDO |
| 知识库回收站 | 已删除知识库/内容的列表、预览、恢复、彻底删除，30 天到期自动清理 | PmsKnowledgeRecycleRecordDO |

## API 接口索引

> 全模块 28 个 Controller、145 个端点，均挂在 `controller/admin` 下（无 app 端接口）。下表按域汇总，完整明细见 `api-{key}.md`。

### 知识库内容管理（kb-content，/pms/kb/*）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsKnowledgeDocumentController | 知识库文档（富文本/文件）创建、更新、移动、详情、搜索 | 6 |
| PmsKnowledgeFolderController | 知识库文件夹增删改、移动、目录树 | 6 |
| PmsKnowledgeDocumentLabelController | 文档标签管理、按标签查文档分页 | 6 |
| PmsKnowledgeContentPermissionController | 知识内容协作权限查询与更新 | 2 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/kb/document/create | POST | 创建文档 | pms:kb:library:update |
| /pms/kb/document/get | GET | 获得文档详情 | pms:kb:library:query |
| /pms/kb/document/search-page | GET | 使用 MySQL 全局搜索文档 | pms:kb:library:query |
| /pms/kb/folder/tree | GET | 获得知识库目录树 | pms:kb:library:query |
| /pms/kb/document-label/document-page | GET | 获得指定标签的文档分页 | pms:kb:library:query |
| /pms/kb/content-permission/update | PUT | 更新知识内容协作权限 | pms:kb:library:update |

### 知识库互动（kb-interaction，/pms/kb/*）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsKnowledgeDocumentShareController | 文档分享（开启/关闭/成员/令牌访问） | 5 |
| PmsKnowledgeFavoriteController | 知识对象关注/取消、关注分页 | 4 |
| PmsKnowledgeDocumentCommentController | 文档评论创建/删除/列表 | 3 |
| PmsKnowledgeDocumentLikeController | 文档点赞/取消点赞 | 2 |
| PmsKnowledgeViewRecordController | 最近浏览列表 | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/kb/document-share/get-by-token | GET | 通过分享令牌获得文档 | @PermitAll（同时 @TenantIgnore） |
| /pms/kb/document-share/open | POST | 开启文档分享 | pms:kb:library:update |
| /pms/kb/document-comment/create | POST | 创建知识库文档评论 | pms:kb:library:query |
| /pms/kb/favorite/page | GET | 获得我的关注分页 | pms:kb:library:query |
| /pms/kb/view-record/recent-list | GET | 获得最近浏览列表 | pms:kb:library:query |

### 知识库与分组（kb-library，/pms/kb/*）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsKnowledgeGroupController | 个人知识库分组增删改、排序、移动 | 7 |
| PmsKnowledgeLibraryTemplateController | 知识库模板管理 | 6 |
| PmsKnowledgeLibraryController | 知识库创建/更新/删除/详情/分页 | 5 |
| PmsKnowledgeLibraryMemberController | 知识库成员列表/更新/退出 | 3 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/kb/library/create | POST | 创建知识库 | pms:kb:library:create |
| /pms/kb/library/page | GET | 获得知识库分页 | pms:kb:library:query |
| /pms/kb/library-member/exit | DELETE | 主动退出知识库 | pms:kb:library:query |
| /pms/kb/group/move | PUT | 移动知识库到个人分组 | pms:kb:library:update |
| /pms/kb/library-template/simple-list | GET | 获取知识库模板全列表 | 已认证（无 @PreAuthorize，仅启用模板） |

### 知识库回收站（kb-recycle，/pms/kb/recycle）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsKnowledgeRecycleController | 已删除知识库/内容查询、预览、恢复、彻底删除 | 6 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/kb/recycle/library-list | GET | 获得已删除知识库列表 | pms:kb:library:delete |
| /pms/kb/recycle/content-preview | GET | 预览知识库最近删除内容 | pms:kb:library:delete |
| /pms/kb/recycle/restore | PUT | 恢复回收站对象 | pms:kb:library:delete |
| /pms/kb/recycle/permanent-delete | DELETE | 彻底删除回收站对象 | pms:kb:library:delete |

### 项目管理（pm-project，/pms/pm/*）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsProjectController | 项目增删改查、概况、星标、归档/回收站/恢复 | 10 |
| PmsProjectGroupController | 个人项目分组增删改、排序、移动项目 | 6 |
| PmsProjectAnnouncementController | 项目公告增删改查 | 5 |
| PmsProjectTemplateController | 项目模板管理 | 5 |
| PmsProjectMemberController | 项目成员列表/保存/移除/退出 | 4 |
| PmsProjectFavoriteController | 项目收藏/取消收藏 | 2 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/pm/project/create | POST | 创建项目 | pms:pm:project:create |
| /pms/pm/project/get | GET | 获得项目详情 | pms:pm:project:query |
| /pms/pm/project/overview | GET | 获得项目概况 | pms:pm:project:query |
| /pms/pm/project/archive | PUT | 归档项目 | pms:pm:project:update |
| /pms/pm/project-member/update-list | PUT | 保存项目成员及其权限级别 | pms:pm:project-member:update |
| /pms/pm/project-group/move-project | PUT | 移动项目到个人分组 | pms:pm:project-group:update |
| /pms/pm/project-favorite/create | POST | 收藏项目 | pms:pm:project:query |

### 项目迭代（pm-iteration，/pms/pm/iteration）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsIterationController | 迭代创建/更新/开始/完成/删除/详情/分页/概览 | 8 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/pm/iteration/start | PUT | 开始项目迭代 | pms:pm:iteration:update |
| /pms/pm/iteration/complete | PUT | 完成项目迭代 | pms:pm:iteration:update |
| /pms/pm/iteration/page | GET | 获得项目迭代分页（含进度） | pms:pm:iteration:query |
| /pms/pm/iteration/overview | GET | 获得迭代概览统计 | pms:pm:iteration:query |

### 工作项管理（pm-workitem，/pms/pm/work-item*）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsWorkItemController | 工作项全生命周期：创建/更新/流转/排序/看板/导入导出/归档回收 | 17 |
| PmsWorkItemStatusController | 工作项状态与看板列配置 | 9 |
| PmsWorkItemWorkLogController | 工时登记、汇总、项目工时报表 | 5 |
| PmsWorkItemCommentController | 工作项评论（两级回复） | 4 |
| PmsWorkItemLabelController | 工作项标签管理 | 4 |
| PmsWorkItemActivityController | 工作项动态列表 | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/pm/work-item/create | POST | 创建工作项 | pms:pm:work-item:create |
| /pms/pm/work-item/update-status | PUT | 更新工作项状态 | pms:pm:work-item:update |
| /pms/pm/work-item/board | GET | 获得工作项看板 | pms:pm:work-item:query |
| /pms/pm/work-item/import | POST | 导入工作项（Excel） | pms:pm:work-item:import |
| /pms/pm/work-item/export-excel | GET | 导出工作项 | pms:pm:work-item:export |
| /pms/pm/work-item-status/update-board-config | PUT | 更新工作项看板列和状态映射 | pms:pm:work-item:update |
| /pms/pm/work-item-work-log/project-report | GET | 获得项目工时报表 | pms:pm:work-item:query |

### 工作台（pm-workbench，/pms/pm/workbench）

| Controller | 说明 | 端点数 |
|-----------|------|--------|
| PmsWorkbenchController | 我负责的工作项/迭代分页与未完成事项数量 | 3 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|----------|
| /pms/pm/workbench/work-item-page | GET | 获得我负责的工作项分页 | pms:pm:work-item:query |
| /pms/pm/workbench/iteration-page | GET | 获得我负责的迭代分页 | pms:pm:iteration:query |
| /pms/pm/workbench/count | GET | 获得我的未完成事项数量 | pms:pm:work-item:query 或 pms:pm:iteration:query（hasAnyPermissions） |

## 数据模型

> 全部 33 张表位于 `pms_` 前缀下，均含 `tenant_id`（租户隔离由 MyBatis-Plus 租户插件处理），公共字段 creator/create_time/updater/update_time/deleted 继承自 BaseDO。

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| pms_project | 项目 | BaseDO | name, status, type, level, open_status, icon, start_time, end_time, archive_time, recycle_time, access_time |
| pms_project_template | 项目模板（默认协作配置） | BaseDO | name, project_type, status, sort, item_types, statuses, boards（JSON） |
| pms_project_member | 项目成员 | BaseDO | project_id, user_id, level |
| pms_project_group | 个人项目分组 | BaseDO | user_id, name, sort, type |
| pms_project_group_relation | 项目分组关系 | BaseDO | user_id, group_id, project_id, sort |
| pms_project_favorite | 项目收藏 | BaseDO | project_id, user_id |
| pms_project_announcement | 项目公告 | BaseDO | project_id, content, file_urls |
| pms_iteration | 项目迭代 | BaseDO | project_id, name, owner_user_id, status, start_time, end_time, finish_time, target, sort |
| pms_work_item | 工作项 | BaseDO | project_id, type, serial_number, name, priority, assignee_user_id, status_id, lifecycle_status, iteration_id, parent_id, related_requirement_id, defect_type, estimated_hours, progress, label_ids, file_urls |
| pms_work_item_status | 工作项状态（按项目+类型配置） | BaseDO | project_id, work_item_type, name, status_type, board_name, system_code, default_status, sort |
| pms_work_item_board | 工作项看板列 | BaseDO | project_id, work_item_type, name, sort |
| pms_work_item_member | 工作项参与人 | BaseDO | project_id, work_item_id, user_id |
| pms_work_item_user_sort | 工作项个人排序 | BaseDO | project_id, work_item_id, user_id, sort |
| pms_work_item_work_log | 工作项工时记录 | BaseDO | project_id, work_item_id, actual_hours, remaining_hours, description |
| pms_work_item_label | 工作项标签 | BaseDO | name, color |
| pms_work_item_comment | 工作项评论 | BaseDO | work_item_id, user_id, main_id, reply_user_id, content |
| pms_work_item_activity | 工作项动态 | BaseDO | project_id, work_item_id, operator_user_id, content |
| pms_knowledge_library | 知识库 | BaseDO | name, description, open_status, cover_url, status, delete_user_id, delete_time |
| pms_knowledge_library_member | 知识库成员 | BaseDO | library_id, user_id, dept_id, level |
| pms_knowledge_library_template | 知识库模板（默认文档） | BaseDO | name, description, cover_url, status, sort, documents（JSON） |
| pms_knowledge_group | 个人知识库分组 | BaseDO | user_id, name, sort, type |
| pms_knowledge_group_relation | 知识库分组关系 | BaseDO | user_id, group_id, library_id, sort |
| pms_knowledge_folder | 知识库文件夹 | BaseDO | library_id, permission_id, parent_id, title, status, delete_user_id |
| pms_knowledge_document | 知识库文档（富文本/文件） | BaseDO | library_id, permission_id, folder_id, parent_id, title, content, type, file_type, file_size, status, label_ids |
| pms_knowledge_document_label | 文档标签 | BaseDO | name, color |
| pms_knowledge_content_permission | 知识内容协作权限 | BaseDO | library_id, open_status, open_level |
| pms_knowledge_content_permission_member | 知识内容协作者 | BaseDO | permission_id, user_id, dept_id, level |
| pms_knowledge_document_comment | 文档评论 | BaseDO | document_id, user_id, main_id, reply_user_id, content |
| pms_knowledge_document_like | 文档点赞 | BaseDO | document_id, user_id |
| pms_knowledge_document_share | 文档分享 | BaseDO | document_id, share_user_ids, token, status, close_user_id, close_time |
| pms_knowledge_favorite | 知识关注 | BaseDO | library_id, type, entity_id, user_id |
| pms_knowledge_view_record | 知识最近浏览记录 | BaseDO | library_id, type, entity_id, user_id |
| pms_knowledge_recycle_record | 知识库回收站记录 | BaseDO | library_id, type, entity_id, name, delete_user_id, delete_time |

## 依赖关系

- **上游**（本模块依赖）:
  - framework: `yudao-spring-boot-starter-web`、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-job`（test: `yudao-spring-boot-starter-test`）
  - 业务模块: `yudao-module-system`（AdminUserApi、PermissionApi、DeptApi、NotifyMessageSendApi）、`yudao-module-infra`（FileApi 文件预签名）
- **下游**（依赖本模块）: 无业务模块依赖 pms；仅 `yudao-server` 聚合打包，`yudao-spring-boot-starter-web` 的 BannerApplicationRunner 检测其类路径提示启用状态

## 详细文档

- [api-kb-content.md](api-kb-content.md) - 知识库内容管理
- [api-kb-interaction.md](api-kb-interaction.md) - 知识库互动
- [api-kb-library.md](api-kb-library.md) - 知识库与分组
- [api-kb-recycle.md](api-kb-recycle.md) - 知识库回收站
- [api-pm-project.md](api-pm-project.md) - 项目管理
- [api-pm-iteration.md](api-pm-iteration.md) - 项目迭代
- [api-pm-workitem.md](api-pm-workitem.md) - 工作项管理
- [api-pm-workbench.md](api-pm-workbench.md) - 工作台
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
