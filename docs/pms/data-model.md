# 数据模型详情

> pms 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。全模块共 33 张表，位于 `pms_` 前缀下，按 `pm`（项目管理）与 `kb`（知识库）两个业务域组织，互不外键耦合。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO
│   ├── creator      String          创建者（system_users.id，INSERT 填充）
│   ├── createTime   LocalDateTime   创建时间（INSERT 填充）
│   ├── updater      String          更新者（INSERT_UPDATE 填充）
│   ├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 填充）
│   └── deleted      Boolean         逻辑删除标记（@TableLogic）
│
├── pm 域（9 个 DO，全部直接继承 BaseDO）
│   ├── PmsProjectDO / PmsProjectTemplateDO / PmsProjectMemberDO
│   ├── PmsProjectGroupDO / PmsProjectGroupRelationDO
│   ├── PmsProjectFavoriteDO / PmsProjectAnnouncementDO
│   └── PmsIterationDO + pm/workitem 下 9 个 PmsWorkItem*DO
│
└── kb 域（16 个 DO，全部直接继承 BaseDO）
    ├── kb/library：PmsKnowledgeLibraryDO / LibraryMemberDO / LibraryTemplateDO / GroupDO / GroupRelationDO
    ├── kb/content：PmsKnowledgeFolderDO / DocumentDO / DocumentLabelDO / ContentPermissionDO / ContentPermissionMemberDO
    ├── kb/interaction：PmsKnowledgeDocumentCommentDO / LikeDO / ShareDO / FavoriteDO / ViewRecordDO
    └── kb/recycle：PmsKnowledgeRecycleRecordDO

cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO（BaseDO + tenantId）
└── pms 模块【未使用】
```

### 使用规则

| 规则 | 说明 |
|-----|------|
| 一律继承 BaseDO | 全部 33 个 DO 均直接继承 `BaseDO`，没有一个继承 `TenantBaseDO` |
| tenant_id 由插件处理 | 所有表物理列均含 `tenant_id bigint NOT NULL DEFAULT 0`，但 DO 不声明 `tenantId` 字段；INSERT 自动补列、SELECT 自动拼接过滤均由 MyBatis-Plus 租户插件（TenantLineInnerInterceptor）在 SQL 层完成 |
| 定时任务显式带租户 | 知识库回收站清理 Job 遍历租户执行，方法上标注 `@TenantJob` |
| 逻辑删除统一 @TableLogic | `deleted = bit`，查询自动追加 `deleted = 0`；项目/工作项/知识库内容另有 archiveTime、recycleTime 等回收站软状态字段与 deleted 并存 |
| 主键策略 @TableId + @KeySequence | 每个 DO 均标注 `@TableId`（自增/雪花由框架决定），并配置 `@KeySequence("pms_xxx_seq")` 以兼容 Oracle/PostgreSQL 等序列型数据库 |
| JSON 类型字段 | 复杂字段用 `@TableField(typeHandler = JacksonTypeHandler.class)` + `autoResultMap = true` 存 varchar/text；仅文档标签 `labelIds` 用框架的 `LongListTypeHandler`（逗号分隔存储） |
| 字段表约定 | 下文各 DO 字段表仅列出 `id` 与业务字段；所有表均额外携带 BaseDO 公共列 `creator/create_time/updater/update_time/deleted` 与租户列 `tenant_id`，不再重复罗列 |
| 索引信息来源 | 取自单测建表脚本 `yudao-module-pms/src/test/resources/sql/create_tables.sql`（H2 方言），生产库以实际 DDL 为准；未列出索引的表仅含主键索引，业务唯一性（如成员不可重复）由 Service 层校验保证 |

## 2. 核心 DO 实体

### 2.1 项目聚合（pm/project）

#### PmsProjectDO (pms_project)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 项目编号 |
| name | String | name | 项目名称 |
| status | Integer | status | 项目状态：1 进行中、2 已归档、3 回收站（PmsProjectStatusEnum） |
| type | Integer | type | 项目类型：1 通用项目、2 敏捷开发项目（PmsProjectTypeEnum） |
| level | Integer | level | 项目优先级：1 最高 ~ 5 最低（PmsProjectLevelEnum） |
| description | String | description | 项目描述 |
| openStatus | Boolean | open_status | 是否公开 |
| icon | String | icon | 项目图标 |
| sort | Integer | sort | 显示顺序 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 截止时间 |
| archiveTime | LocalDateTime | archive_time | 归档时间 |
| recycleTime | LocalDateTime | recycle_time | 移入回收站时间 |
| accessTime | LocalDateTime | access_time | 最近访问时间 |

**继承**: BaseDO
**索引**: 仅主键索引
全模块的聚合根：成员、迭代、工作项、公告、分组关系等均以 `project_id` 挂靠；status 与 lifecycle 类字段共同支撑「进行中 → 归档/回收站 → 恢复」的项目生命周期。

#### PmsProjectTemplateDO (pms_project_template)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 模板编号 |
| name | String | name | 模板名称 |
| description | String | description | 模板描述 |
| projectType | Integer | project_type | 项目类型（PmsProjectTypeEnum） |
| status | Integer | status | 模板状态（CommonStatusEnum：0 开启、1 禁用） |
| sort | Integer | sort | 显示顺序 |
| itemTypes | List\<Integer\> | item_types | 启用的工作项类型列表，JSON 存储（PmsWorkItemTypeEnum） |
| statuses | List\<StatusTemplate\> | statuses | 工作项状态模板列表，JSON 存储 |
| boards | List\<BoardTemplate\> | boards | 看板列模板列表，JSON 存储 |

**继承**: BaseDO
**索引**: 仅主键索引
模板只保存新建项目时使用的默认协作配置，项目创建后会生成自己的运行配置（独立的状态/看板表数据）。JSON 内嵌结构：

- `StatusTemplate`：code（模板内稳定编码）、name、workItemType、statusType（PmsWorkItemStatusTypeEnum）、defaultStatus（是否初始状态）、sort、boardCode（所属看板列编码）
- `BoardTemplate`：code、name、workItemType、sort、statusCodes（看板列关联的状态编码列表）

#### PmsProjectMemberDO (pms_project_member)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| userId | Long | user_id | 后台用户编号，关联 system 模块 AdminUserDO |
| level | Integer | level | 成员权限级别：1 项目拥有者、2 项目管理员、3 编辑、4 只读（PmsProjectMemberLevelEnum） |

**继承**: BaseDO
**索引**: 仅主键索引（project_id + user_id 唯一性由 Service 层校验）
项目级数据权限的载体，Service 层按 level 做「可读/可写/管理员」行级校验。

#### PmsProjectGroupDO (pms_project_group)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分组编号 |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO（分组归属人） |
| name | String | name | 分组名称 |
| sort | Integer | sort | 显示顺序 |
| type | Integer | type | 分组类型：1 全部项目、2 未分组、3 自定义分组（PmsProjectGroupTypeEnum） |

**继承**: BaseDO
**索引**: 仅主键索引
个人维护的项目视图分组，不影响其他成员看到的分组。

#### PmsProjectGroupRelationDO (pms_project_group_relation)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO |
| groupId | Long | group_id | 项目分组编号，关联 PmsProjectGroupDO |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 仅主键索引
「用户 × 分组 × 项目」三元关系表，实现项目在个人分组内的归类与排序。

#### PmsProjectFavoriteDO (pms_project_favorite)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 收藏编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| userId | Long | user_id | 收藏人用户编号，关联 AdminUserDO |

**继承**: BaseDO
**索引**: 仅主键索引
项目星标收藏，用户首页「我的项目」排序依据之一。

#### PmsProjectAnnouncementDO (pms_project_announcement)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 公告编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| content | String | content | 公告内容（text） |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储（varchar(5000)） |

**继承**: BaseDO
**索引**: 仅主键索引

### 2.2 迭代聚合（pm/iteration）

#### PmsIterationDO (pms_iteration)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 迭代编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| name | String | name | 迭代名称 |
| ownerUserId | Long | owner_user_id | 负责人用户编号，关联 AdminUserDO（工作台「我负责的迭代」查询条件） |
| status | Integer | status | 迭代状态：1 未开始、2 进行中、3 已完成（PmsIterationStatusEnum） |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| finishTime | LocalDateTime | finish_time | 完成时间 |
| target | String | target | 迭代目标 |
| description | String | description | 迭代描述 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 仅主键索引
迭代进度（已完成/总工作项数）由 Service 层按 work_item 表实时统计，不在本表冗余存储。

### 2.3 工作项聚合（pm/workitem）

#### PmsWorkItemDO (pms_work_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 工作项编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| type | Integer | type | 工作项类型：2 需求、3 任务、4 缺陷（PmsWorkItemTypeEnum） |
| serialNumber | Integer | serial_number | 项目内工作项序号（展示为编号后缀） |
| name | String | name | 工作项标题 |
| description | String | description | 工作项描述（text） |
| priority | Integer | priority | 优先级：0 无、1 低、2 中、3 高（PmsWorkItemPriorityEnum） |
| assigneeUserId | Long | assignee_user_id | 负责人用户编号，关联 AdminUserDO（指派时发站内信） |
| statusId | Long | status_id | 看板状态编号，关联 PmsWorkItemStatusDO |
| status | Integer | status | 语义状态：1 未开始、2 进行中、3 已完成（PmsWorkItemStatusTypeEnum），冗余自 statusId 便于统计 |
| lifecycleStatus | Integer | lifecycle_status | 生命周期状态：1 正常、2 已归档、3 回收站（PmsWorkItemLifecycleStatusEnum） |
| archiveTime | LocalDateTime | archive_time | 归档时间 |
| recycleTime | LocalDateTime | recycle_time | 移入回收站时间 |
| iterationId | Long | iteration_id | 所属迭代编号，关联 PmsIterationDO；NULL 表示待规划（Backlog） |
| parentId | Long | parent_id | 父工作项编号，自关联本表 id |
| relatedRequirementId | Long | related_requirement_id | 关联需求编号，自关联本表 id（缺陷挂需求） |
| defectType | Integer | defect_type | 缺陷类型：1 功能、2 界面、3 易用性、4 安全、5 性能、6 代码（PmsWorkItemDefectTypeEnum） |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 截止时间 |
| estimatedHours | Integer | estimated_hours | 预估工时，单位小时 |
| progress | Integer | progress | 完成进度，0-100 |
| fileUrls | List\<String\> | file_urls | 附件地址列表，JSON 存储（varchar(5000)） |
| labelIds | List\<Long\> | label_ids | 标签编号列表，JSON 存储，关联 PmsWorkItemLabelDO |
| sort | Integer | sort | 看板内显示顺序 |

**继承**: BaseDO
**索引**: 仅主键索引
模块业务核心表：看板流转（statusId/status）、迭代规划（iterationId）、父子层级（parentId）、缺陷-需求关联（relatedRequirementId）都汇聚于此；动态、评论、参与人、工时、个人排序均以 `work_item_id` 挂靠。

#### PmsWorkItemStatusDO (pms_work_item_status)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 状态编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| workItemType | Integer | work_item_type | 工作项类型（PmsWorkItemTypeEnum） |
| name | String | name | 状态名称 |
| statusType | Integer | status_type | 语义状态：1 未开始、2 进行中、3 已完成（PmsWorkItemStatusTypeEnum） |
| description | String | description | 状态描述 |
| boardName | String | board_name | 所属看板列名称，为空时不在看板展示 |
| systemCode | String | system_code | 系统状态编码，仅默认状态使用，用于保证并发初始化幂等 |
| defaultStatus | Boolean | default_status | 是否初始状态（新工作项的默认落点） |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 仅主键索引
按「项目 + 工作项类型」维度由用户自定义维护；状态可配置（本表）与流转语义（statusType）分离，是 PmsWorkItemDO.statusId 的字典表。

#### PmsWorkItemBoardDO (pms_work_item_board)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 看板列编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| workItemType | Integer | work_item_type | 工作项类型（PmsWorkItemTypeEnum） |
| name | String | name | 看板列名称 |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: 仅主键索引
与 PmsWorkItemStatusDO.boardName（列名冗余）配合呈现看板；看板列与状态的映射更新由 `/pms/pm/work-item-status/update-board-config` 完成。无独立 Controller，Service 由工作项配置端点内部调用。

#### PmsWorkItemMemberDO (pms_work_item_member)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO（冗余，便于按项目查询） |
| workItemId | Long | work_item_id | 工作项编号，关联 PmsWorkItemDO |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO |

**继承**: BaseDO
**索引**: 仅主键索引
工作项参与人（协作人）关联表。

#### PmsWorkItemLabelDO (pms_work_item_label)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 标签编号 |
| name | String | name | 标签名称 |
| color | String | color | 标签颜色（varchar(20)） |

**继承**: BaseDO
**索引**: 仅主键索引
项目内共用标签池；与工作项的关联通过 PmsWorkItemDO.labelIds JSON 列表维护（非外键关联表）。

#### PmsWorkItemCommentDO (pms_work_item_comment)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 评论编号 |
| workItemId | Long | work_item_id | 工作项编号，关联 PmsWorkItemDO |
| userId | Long | user_id | 评论人用户编号，关联 AdminUserDO |
| mainId | Long | main_id | 主评论编号，0 表示主评论（常量 MAIN_ID_ROOT），否则指向根评论 id |
| replyUserId | Long | reply_user_id | 回复对象用户编号，关联 AdminUserDO |
| content | String | content | 评论内容（varchar(2000)） |

**继承**: BaseDO
**索引**: 仅主键索引
两级评论结构：mainId = 0 为主评论，mainId = 根评论 id 为楼中楼回复。

#### PmsWorkItemActivityDO (pms_work_item_activity)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 动态编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO（冗余，支撑项目级动态流） |
| workItemId | Long | work_item_id | 工作项编号，关联 PmsWorkItemDO |
| operatorUserId | Long | operator_user_id | 操作人用户编号，关联 AdminUserDO |
| content | String | content | 动态内容（varchar(500)），文案由 PmsWorkItemActivityContentEnum 的 format() 生成 |

**继承**: BaseDO
**索引**: 仅主键索引
只追加不修改的操作流水表，记录创建、字段变更、状态流转、迭代规划、归档/回收/恢复、评论与工时等事件。

#### PmsWorkItemUserSortDO (pms_work_item_user_sort)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO |
| workItemId | Long | work_item_id | 工作项编号，关联 PmsWorkItemDO |
| userId | Long | user_id | 用户编号，关联 AdminUserDO |
| sort | Integer | sort | 显示顺序（个人视角） |

**继承**: BaseDO
**索引**: 仅主键索引
保存每个用户对看板/列表的个人拖拽排序，与公共 sort 字段隔离。无独立 Controller，由工作项排序端点内部调用。

#### PmsWorkItemWorkLogDO (pms_work_item_work_log)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 工时记录编号 |
| projectId | Long | project_id | 项目编号，关联 PmsProjectDO（冗余，支撑项目工时报表） |
| workItemId | Long | work_item_id | 工作项编号，关联 PmsWorkItemDO |
| actualHours | Integer | actual_hours | 实际投入工时，单位小时 |
| remainingHours | Integer | remaining_hours | 本次登记后的剩余工时，单位小时 |
| description | String | description | 工时说明（varchar(500)） |

**继承**: BaseDO
**索引**: 仅主键索引
登记流水；汇总由 Service 按 work_item_id 聚合计算，登记/更新动作同时写入动态表。

### 2.4 知识库聚合（kb）

#### PmsKnowledgeLibraryDO (pms_knowledge_library)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 知识库编号 |
| name | String | name | 知识库名称 |
| description | String | description | 知识库简介 |
| openStatus | Boolean | open_status | 是否公开（对知识库可访问人公开内容） |
| coverUrl | String | cover_url | 知识库封面 |
| status | Integer | status | 知识库状态：-1 回收站、0 草稿、1 正常、2 模板（PmsKnowledgeDocumentStatusEnum） |
| deleteUserId | Long | delete_user_id | 删除人用户编号，关联 AdminUserDO（移入回收站时记录） |
| deleteTime | LocalDateTime | delete_time | 删除时间 |

**继承**: BaseDO
**索引**: 仅主键索引
kb 域聚合根；成员、文件夹、文档、协作权限、分组关系、收藏、浏览、回收站记录均以 `library_id` 挂靠。

#### PmsKnowledgeLibraryMemberDO (pms_knowledge_library_member)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 成员编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO；与 deptId 二选一 |
| deptId | Long | dept_id | 部门编号，关联 system 模块 DeptDO（部门整体授权） |
| level | Integer | level | 成员等级：1 创建人、2 管理员、3 成员（PmsKnowledgeLibraryMemberLevelEnum） |

**继承**: BaseDO
**索引**: 仅主键索引
支持「用户 + 部门」两种成员粒度；退出知识库即删除本人成员记录。

#### PmsKnowledgeLibraryTemplateDO (pms_knowledge_library_template)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 模板编号 |
| name | String | name | 模板名称 |
| description | String | description | 模板简介 |
| coverUrl | String | cover_url | 模板封面地址 |
| status | Integer | status | 模板状态（CommonStatusEnum：0 开启、1 禁用） |
| sort | Integer | sort | 显示顺序 |
| documents | List\<Document\> | documents | 模板文档列表，JSON 存储（text，最大 varchar(1000000)） |

**继承**: BaseDO
**索引**: 仅主键索引
模板只保存新建知识库时使用的默认文档（内嵌结构 `Document`：title、content），创建后生成独立的文档记录。`/pms/kb/library-template/simple-list` 端点仅要求登录、无 @PreAuthorize。

#### PmsKnowledgeGroupDO (pms_knowledge_group)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 知识库分组编号 |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO（分组归属人） |
| name | String | name | 分组名称 |
| sort | Integer | sort | 显示顺序 |
| type | Integer | type | 分组类型：1 全部知识库、2 未分组、3 自定义分组（PmsKnowledgeGroupTypeEnum） |

**继承**: BaseDO
**索引**: idx_tenant_user_type（tenant_id, user_id, type）、idx_tenant_user_sort（tenant_id, user_id, sort）——按归属人取分组并排序
个人知识库分组，语义同项目分组。

#### PmsKnowledgeGroupRelationDO (pms_knowledge_group_relation)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO |
| groupId | Long | group_id | 知识库分组编号，关联 PmsKnowledgeGroupDO |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| sort | Integer | sort | 显示顺序 |

**继承**: BaseDO
**索引**: idx_tenant_user_group_library（tenant_id, user_id, group_id, library_id）、idx_tenant_user_library（tenant_id, user_id, library_id）、idx_tenant_library（tenant_id, library_id）——支撑「按分组取库」「库是否已分组」「删库清关系」三类查询

#### PmsKnowledgeFolderDO (pms_knowledge_folder)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 文件夹编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| permissionId | Long | permission_id | 内容协作权限编号，关联 PmsKnowledgeContentPermissionDO |
| parentId | Long | parent_id | 父文件夹编号，0 表示根目录（常量 PARENT_ID_ROOT），自关联本表 id |
| title | String | title | 文件夹标题 |
| status | Integer | status | 文件夹状态：-1 回收站、0 草稿、1 正常、2 模板（PmsKnowledgeDocumentStatusEnum） |
| deleteUserId | Long | delete_user_id | 删除人用户编号，关联 AdminUserDO |
| deleteTime | LocalDateTime | delete_time | 删除时间 |

**继承**: BaseDO
**索引**: 仅主键索引
与文档共同组成目录树；每个文件夹创建时同步生成一条内容协作权限记录（permissionId）。

#### PmsKnowledgeDocumentDO (pms_knowledge_document)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 文档编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| permissionId | Long | permission_id | 内容协作权限编号，关联 PmsKnowledgeContentPermissionDO |
| folderId | Long | folder_id | 文件夹编号，0 表示不在文件夹中（常量 FOLDER_ID_ROOT），关联 PmsKnowledgeFolderDO |
| parentId | Long | parent_id | 父文档编号，0 表示根文档（常量 PARENT_ID_ROOT），自关联本表 id |
| title | String | title | 文档标题 |
| content | String | content | 文档内容或文件地址（富文本存 HTML，文件类型存 URL；text） |
| type | Integer | type | 文档类型：3 富文本、4 文件（PmsKnowledgeDocumentTypeEnum） |
| fileType | String | file_type | 文件类型（扩展名，仅文件型文档） |
| fileSize | Long | file_size | 文件大小，单位字节 |
| status | Integer | status | 文档状态：-1 回收站、0 草稿、1 正常、2 模板（PmsKnowledgeDocumentStatusEnum） |
| labelIds | List\<Long\> | label_ids | 标签编号列表，LongListTypeHandler 逗号分隔存储，关联 PmsKnowledgeDocumentLabelDO |
| deleteUserId | Long | delete_user_id | 删除人用户编号，关联 AdminUserDO |
| deleteTime | LocalDateTime | delete_time | 删除时间 |

**继承**: BaseDO
**索引**: 仅主键索引
kb 域核心内容表：树形文档（parentId）+ 文件夹归类（folderId）+ 全局搜索（MySQL LIKE，由 Service 实现）；评论、点赞、分享均以 `document_id` 挂靠。

#### PmsKnowledgeContentPermissionDO (pms_knowledge_content_permission)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 内容协作权限编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| openStatus | Boolean | open_status | 是否对知识库可访问人公开 |
| openLevel | Integer | open_level | 公开协作等级：1 管理员、2 可编辑、3 仅预览、4 可下载、5 可上传下载（PmsKnowledgeContentLevelEnum） |

**继承**: BaseDO
**索引**: 仅主键索引
内容级（文件夹/文档粒度）权限配置，与 library 级成员权限叠加校验。

#### PmsKnowledgeContentPermissionMemberDO (pms_knowledge_content_permission_member)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 协作者编号 |
| permissionId | Long | permission_id | 内容协作权限编号，关联 PmsKnowledgeContentPermissionDO |
| userId | Long | user_id | 后台用户编号，关联 AdminUserDO；与 deptId 二选一 |
| deptId | Long | dept_id | 部门编号，关联 DeptDO（部门整体授权） |
| level | Integer | level | 协作等级：1 管理员、2 可编辑、3 仅预览、4 可下载、5 可上传下载（PmsKnowledgeContentLevelEnum） |

**继承**: BaseDO
**索引**: 仅主键索引
指定协作者（用户/部门）的内容权限明细。

#### PmsKnowledgeDocumentLabelDO (pms_knowledge_document_label)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 文档标签编号 |
| name | String | name | 标签名称（varchar(255)） |
| color | String | color | 标签颜色（varchar(20)） |

**继承**: BaseDO
**索引**: 仅主键索引
与文档的关联通过 PmsKnowledgeDocumentDO.labelIds 逗号分隔列维护。

#### PmsKnowledgeDocumentCommentDO (pms_knowledge_document_comment)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 评论编号 |
| documentId | Long | document_id | 文档编号，关联 PmsKnowledgeDocumentDO |
| userId | Long | user_id | 评论人用户编号，关联 AdminUserDO |
| mainId | Long | main_id | 主评论编号，0 表示主评论（常量 MAIN_ID_ROOT），否则指向根评论 id |
| replyUserId | Long | reply_user_id | 回复对象用户编号，关联 AdminUserDO |
| content | String | content | 评论内容（varchar(2000)） |

**继承**: BaseDO
**索引**: 仅主键索引
结构与工作项评论一致的两级评论。

#### PmsKnowledgeDocumentLikeDO (pms_knowledge_document_like)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 点赞编号 |
| documentId | Long | document_id | 文档编号，关联 PmsKnowledgeDocumentDO |
| userId | Long | user_id | 点赞人用户编号，关联 AdminUserDO |

**继承**: BaseDO
**索引**: idx_tenant_document_create_time（tenant_id, document_id, create_time，按文档统计点赞）、idx_tenant_user_document（tenant_id, user_id, document_id，判断是否已点赞/取消）

#### PmsKnowledgeDocumentShareDO (pms_knowledge_document_share)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分享编号 |
| documentId | Long | document_id | 文档编号，关联 PmsKnowledgeDocumentDO |
| shareUserIds | List\<Long\> | share_user_ids | 内部分享成员用户编号列表，JSON 存储（varchar(5000)），关联 AdminUserDO |
| token | String | token | 外部查看令牌（varchar(64)），唯一 |
| status | Integer | status | 分享状态（CommonStatusEnum：0 开启、1 关闭） |
| closeUserId | Long | close_user_id | 关闭人用户编号，关联 AdminUserDO |
| closeTime | LocalDateTime | close_time | 关闭时间 |

**继承**: BaseDO
**索引**: 唯一索引 uk_token（token）——令牌直链访问；idx_tenant_document（tenant_id, document_id）——按文档查分享
令牌访问端点 `/pms/kb/document-share/get-by-token` 为 @PermitAll + @TenantIgnore（公开链接场景），配合 token 唯一索引实现免登录查看。

#### PmsKnowledgeFavoriteDO (pms_knowledge_favorite)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 收藏编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO（冗余，支撑库内收藏筛选） |
| type | Integer | type | 收藏对象类型：1 知识库、2 文件夹、3 文档、4 文件（PmsKnowledgeObjectTypeEnum） |
| entityId | Long | entity_id | 收藏对象编号，按 type 多态关联知识库/文件夹/文档 |
| userId | Long | user_id | 收藏人用户编号，关联 AdminUserDO |

**继承**: BaseDO
**索引**: idx_tenant_user_create_time_id（tenant_id, user_id, create_time, id）、idx_tenant_user_library_create_time_id、idx_tenant_user_type_entity（tenant_id, user_id, type, entity_id，判重）、idx_tenant_library、idx_tenant_type_entity（tenant_id, type, entity_id，按对象统计）
「关注」功能多态关联表（type + entityId），覆盖关注分页、判重与对象统计三类查询。

#### PmsKnowledgeViewRecordDO (pms_knowledge_view_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 浏览记录编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| type | Integer | type | 浏览对象类型：1 知识库、2 文件夹、3 文档、4 文件（PmsKnowledgeObjectTypeEnum） |
| entityId | Long | entity_id | 浏览对象编号，按 type 多态关联文件夹或文档 |
| userId | Long | user_id | 浏览人用户编号，关联 AdminUserDO |

**继承**: BaseDO
**索引**: idx_tenant_user_create_time_id、idx_tenant_user_type_entity、idx_tenant_library_create_time_id、idx_tenant_type_entity —— 支撑「最近浏览列表」按用户倒序与对象维度查询

#### PmsKnowledgeRecycleRecordDO (pms_knowledge_recycle_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 回收站记录编号 |
| libraryId | Long | library_id | 知识库编号，关联 PmsKnowledgeLibraryDO |
| type | Integer | type | 回收对象类型：1 知识库、2 文件夹、3 文档、4 文件（PmsKnowledgeObjectTypeEnum） |
| entityId | Long | entity_id | 回收对象编号，按 type 多态关联知识库/文件夹/文档 |
| name | String | name | 回收对象名称（快照，原对象删除后仍可展示） |
| deleteUserId | Long | delete_user_id | 删除人用户编号，关联 AdminUserDO |
| deleteTime | LocalDateTime | delete_time | 删除时间（30 天到期清理依据） |

**继承**: BaseDO
**索引**: idx_tenant_type_entity（tenant_id, type, entity_id，恢复/彻底删除定位对象）、idx_tenant_delete_time_id（tenant_id, delete_time, id，到期 Job 扫描）、idx_tenant_library_delete_time、idx_tenant_delete_user_type（tenant_id, delete_user_id, type，按删除人筛选）
知识库回收站独立于 BaseDO.deleted 之外的「两段式删除」记录表；清理 Job 标注 @TenantJob 按 30 天到期执行彻底删除。

## 3. 实体关系

### pm 域（项目 → 迭代 → 工作项）

```
pms_project (聚合根)
├─1:N─ pms_project_member      (project_id → project.id；user_id → system AdminUserDO)
├─1:N─ pms_project_favorite    (project_id；user_id → AdminUserDO)
├─1:N─ pms_project_announcement(project_id)
├─1:N─ pms_iteration           (project_id；owner_user_id → AdminUserDO)
│        └─1:N─ pms_work_item  (iteration_id，NULL=待规划)
├─1:N─ pms_work_item           (project_id)
│        ├─N:1─ pms_work_item_status (status_id；project_id + work_item_type 维度配置)
│        ├─N:1─ pms_work_item_board  (project_id + work_item_type 维度配置，经 board_name 弱关联)
│        ├─自关联─ parent_id / related_requirement_id → work_item.id
│        ├─JSON逻辑关联─ label_ids → pms_work_item_label.id
│        ├─1:N─ pms_work_item_member   (work_item_id；user_id → AdminUserDO)
│        ├─1:N─ pms_work_item_comment  (work_item_id；main_id 自关联，0=主评论)
│        ├─1:N─ pms_work_item_activity (work_item_id；operator_user_id → AdminUserDO)
│        ├─1:N─ pms_work_item_user_sort(work_item_id；user_id → AdminUserDO)
│        └─1:N─ pms_work_item_work_log (work_item_id)
└─经 pms_project_group_relation (user_id + group_id + project_id)
          └─N:1─ pms_project_group (user_id 归属)

pms_project_template ──(仅 JSON 配置，创建项目时物化为 status/board 记录，无外键)
```

### kb 域（知识库 → 内容树 → 互动）

```
pms_knowledge_library (聚合根)
├─1:N─ pms_knowledge_library_member   (library_id；user_id → AdminUserDO / dept_id → DeptDO)
├─1:N─ pms_knowledge_group_relation   (library_id) ─N:1─ pms_knowledge_group (user_id 归属)
├─1:N─ pms_knowledge_folder           (library_id + permission_id)
│        └─自关联─ parent_id（0=根目录）
├─1:N─ pms_knowledge_document         (library_id + permission_id + folder_id)
│        ├─自关联─ parent_id（0=根文档）
│        ├─JSON逻辑关联─ label_ids → pms_knowledge_document_label.id
│        ├─1:N─ pms_knowledge_document_comment (document_id；main_id 自关联，0=主评论)
│        ├─1:N─ pms_knowledge_document_like    (document_id)
│        └─1:N─ pms_knowledge_document_share   (document_id；token 唯一；share_user_ids JSON)
├─1:N─ pms_knowledge_content_permission        (library_id)
│        └─1:N─ pms_knowledge_content_permission_member (permission_id；user_id/dept_id 二选一)
└─多态关联（type + entity_id：1=库 / 2=文件夹 / 3=文档 / 4=文件）
         ├─ pms_knowledge_favorite      (library_id + type + entity_id + user_id)
         ├─ pms_knowledge_view_record   (library_id + type + entity_id + user_id)
         └─ pms_knowledge_recycle_record(library_id + type + entity_id，name/delete_* 为快照)

pms_knowledge_library_template ──(JSON documents，创建知识库时物化为 document 记录，无外键)
```

### 跨模块关联（无外键，逻辑关联）

| 本模块字段 | 上游模块 | 用途 |
|-----------|---------|------|
| 各表 user_id / owner_user_id / assignee_user_id / operator_user_id / delete_user_id / close_user_id / reply_user_id | system.AdminUserDO | 成员、负责人、操作人展示与校验（AdminUserApi） |
| pms_knowledge_library_member.dept_id、pms_knowledge_content_permission_member.dept_id | system.DeptDO | 部门整体授权（DeptApi） |
| 权限校验 | system.PermissionApi | 超级管理员放行 + 菜单权限 |
| 附件/封面/图标 file_urls、icon、cover_url | infra.FileApi | 文件预签名访问 |
| 指派/分享通知 | system.NotifyMessageSendApi | 站内信模板（MessageTemplateConstants） |

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|------|
| pms_project | PmsProjectDO | 项目（聚合根，含归档/回收站生命周期） |
| pms_project_template | PmsProjectTemplateDO | 项目模板（JSON 保存默认工作项类型/状态/看板列配置） |
| pms_project_member | PmsProjectMemberDO | 项目成员（含权限级别 1-4） |
| pms_project_group | PmsProjectGroupDO | 个人项目分组 |
| pms_project_group_relation | PmsProjectGroupRelationDO | 项目分组关系（用户×分组×项目） |
| pms_project_favorite | PmsProjectFavoriteDO | 项目收藏（星标） |
| pms_project_announcement | PmsProjectAnnouncementDO | 项目公告（含 JSON 附件列表） |
| pms_iteration | PmsIterationDO | 项目迭代 |
| pms_work_item | PmsWorkItemDO | 工作项（需求/任务/缺陷，业务核心表） |
| pms_work_item_status | PmsWorkItemStatusDO | 工作项状态（按项目+类型配置） |
| pms_work_item_board | PmsWorkItemBoardDO | 工作项看板列 |
| pms_work_item_member | PmsWorkItemMemberDO | 工作项参与人 |
| pms_work_item_label | PmsWorkItemLabelDO | 工作项标签 |
| pms_work_item_comment | PmsWorkItemCommentDO | 工作项评论（两级回复） |
| pms_work_item_activity | PmsWorkItemActivityDO | 工作项动态（操作流水） |
| pms_work_item_user_sort | PmsWorkItemUserSortDO | 工作项个人排序 |
| pms_work_item_work_log | PmsWorkItemWorkLogDO | 工作项工时记录 |
| pms_knowledge_library | PmsKnowledgeLibraryDO | 知识库（kb 域聚合根） |
| pms_knowledge_library_member | PmsKnowledgeLibraryMemberDO | 知识库成员（用户/部门 + 等级） |
| pms_knowledge_library_template | PmsKnowledgeLibraryTemplateDO | 知识库模板（JSON 默认文档） |
| pms_knowledge_group | PmsKnowledgeGroupDO | 个人知识库分组 |
| pms_knowledge_group_relation | PmsKnowledgeGroupRelationDO | 知识库分组关系 |
| pms_knowledge_folder | PmsKnowledgeFolderDO | 知识库文件夹（树形） |
| pms_knowledge_document | PmsKnowledgeDocumentDO | 知识库文档（富文本/文件，树形） |
| pms_knowledge_document_label | PmsKnowledgeDocumentLabelDO | 知识库文档标签 |
| pms_knowledge_content_permission | PmsKnowledgeContentPermissionDO | 知识内容协作权限（文件夹/文档粒度） |
| pms_knowledge_content_permission_member | PmsKnowledgeContentPermissionMemberDO | 知识内容协作者（用户/部门 + 等级） |
| pms_knowledge_document_comment | PmsKnowledgeDocumentCommentDO | 知识库文档评论（两级回复） |
| pms_knowledge_document_like | PmsKnowledgeDocumentLikeDO | 知识库文档点赞 |
| pms_knowledge_document_share | PmsKnowledgeDocumentShareDO | 知识库文档分享（内部成员 + 外部令牌） |
| pms_knowledge_favorite | PmsKnowledgeFavoriteDO | 知识收藏/关注（多态：库/文件夹/文档/文件） |
| pms_knowledge_view_record | PmsKnowledgeViewRecordDO | 知识最近浏览记录（多态） |
| pms_knowledge_recycle_record | PmsKnowledgeRecycleRecordDO | 知识库回收站记录（30 天到期清理） |
