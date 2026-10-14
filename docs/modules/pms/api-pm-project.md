# 项目管理接口 (PmsProjectController / PmsProjectMemberController / PmsProjectGroupController / PmsProjectFavoriteController / PmsProjectAnnouncementController / PmsProjectTemplateController)

> 覆盖 PMS 项目全生命周期：项目的增删改查、归档/回收站、概况统计、星标收藏、成员与权限级别、个人分组、项目公告，以及用于一键初始化项目的项目模板维护。

## 接口路径前缀

| 前缀 | Controller | 说明 |
|------|-----------|------|
| /pms/pm/project | PmsProjectController | 项目主体（创建/更新/详情/分页/概况/归档/回收站） |
| /pms/pm/project-member | PmsProjectMemberController | 项目成员与权限级别 |
| /pms/pm/project-group | PmsProjectGroupController | 个人项目分组 |
| /pms/pm/project-favorite | PmsProjectFavoriteController | 项目星标收藏 |
| /pms/pm/project-announcement | PmsProjectAnnouncementController | 项目公告 |
| /pms/pm/project-template | PmsProjectTemplateController | 项目模板 |

通用说明：

- 项目状态 `status` 参见 `PmsProjectStatusEnum`：1 进行中 / 2 已归档 / 3 回收站。
- 成员权限级别 `level` 参见 `PmsProjectMemberLevelEnum`：1 拥有者（OWNER）/ 2 管理员（ADMIN）/ 3 编辑（WRITE）/ 4 只读（READ）；OWNER+ADMIN 可管理项目，OWNER+ADMIN+WRITE 可编辑业务数据，超级管理员全部放行。
- 项目内几乎所有接口都在 Service 层按当前登录用户做「可读（公开项目或成员）/ 可写 / 管理员」数据行级校验。

---

## 1. 项目管理（Controller: PmsProjectController，前缀 /pms/pm/project）

### 1.1 创建项目
- **路径**: POST /pms/pm/project/create
- **权限**: pms:pm:project:create
- **说明**: 创建一个进行中的项目，创建人自动成为项目拥有者，并初始化成员与工作项看板状态

**请求参数 (PmsProjectSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 否 | — | 项目编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=31) | 项目名称 |
| type | Integer | 是 | @NotNull、@InEnum(PmsProjectTypeEnum.class) | 项目类型：1 通用项目 / 2 敏捷开发项目 |
| level | Integer | 是 | @NotNull、@InEnum(PmsProjectLevelEnum.class) | 项目优先级：1 最高 ~ 5 最低 |
| description | String | 否 | @Size(max=500) | 项目描述 |
| openStatus | Boolean | 是 | @NotNull | 是否公开（公开项目非成员可查看） |
| icon | String | 是 | @NotBlank | 项目图标，如 ep:folder |
| startTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@AssertTrue 联动校验 | 开始时间 |
| endTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 截止时间（@AssertTrue：开始、截止需同时填写且开始早于截止） |
| memberUserIds | List\<Long\> | 否 | — | 初始成员编号列表 |

**响应**: CommonResult\<Long\> — 项目编号

**业务逻辑**: 1. 创建项目，状态固定为进行中（ACTIVE），sort=0 并记录访问时间。 2. 校验初始成员账号存在，创建人写入为 OWNER 级别成员，其余初始成员默认 WRITE 级别，批量插入。 3. 按项目类型初始化该项目支持的工作项看板状态。

### 1.2 更新项目
- **路径**: PUT /pms/pm/project/update
- **权限**: pms:pm:project:update
- **说明**: 更新项目基本信息，项目类型不允许修改

**请求参数 (PmsProjectSaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验项目存在。 2. 校验项目处于进行中状态。 3. 校验当前用户可以管理项目（OWNER/ADMIN 或超级管理员）。 4. 更新项目基本信息，更新时将 type 置 null，即不允许修改项目类型。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_002 | 只有项目管理员可以执行该操作 |

### 1.3 获得项目详情
- **路径**: GET /pms/pm/project/get
- **权限**: pms:pm:project:query
- **说明**: 获得项目详情，同时刷新最近访问时间，并拼接当前用户在项目中的角色状态

**请求参数**: Query 参数 id（Long，必填，项目编号）

**响应**: CommonResult\<PmsProjectRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 项目编号 |
| name | String | 项目名称 |
| status | Integer | 项目状态（1 进行中 / 2 已归档 / 3 回收站） |
| type | Integer | 项目类型 |
| level | Integer | 项目优先级 |
| description | String | 项目描述 |
| openStatus | Boolean | 是否公开 |
| icon | String | 项目图标 |
| startTime / endTime | LocalDateTime | 开始 / 截止时间 |
| archiveTime | LocalDateTime | 归档时间 |
| recycleTime | LocalDateTime | 移入回收站时间 |
| accessTime | LocalDateTime | 最近访问时间 |
| createTime | LocalDateTime | 创建时间 |
| creator | String | 创建人编号 |
| creatorName | String | 创建人姓名 |
| adminNames | List\<String\> | 项目管理员姓名列表 |
| memberCount | Integer | 项目成员数量 |
| pendingWorkItemCount | Long | 未开始工作项数量 |
| processingWorkItemCount | Long | 进行中工作项数量 |
| completedWorkItemCount | Long | 已完成工作项数量 |
| adminStatus | Boolean | 当前用户是否为项目管理员 |
| ownerStatus | Boolean | 当前用户是否拥有项目所有者权限 |
| memberStatus | Boolean | 当前用户是否为项目成员 |
| exitStatus | Boolean | 当前用户是否可以主动退出项目（是成员且非拥有者） |
| writeStatus | Boolean | 当前用户是否可以编辑项目业务数据 |
| favoriteStatus | Boolean | 当前用户是否已收藏 |

**业务逻辑**: 1. 校验项目可读（公开项目允许查看；私有项目仅项目成员或超级管理员）。 2. 更新并返回最近访问时间 accessTime。 3. Controller 批量拼接展示字段：创建人姓名、管理员姓名、成员数量、三类状态工作项数量，以及当前用户的 owner/admin/member/exit/write/favorite 状态（超级管理员直接获得 owner/admin/write 状态）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 1.4 获得项目分页
- **路径**: GET /pms/pm/project/page
- **权限**: pms:pm:project:query
- **说明**: 按列表场景分页查询项目，响应字段同 1.3 的 PmsProjectRespVO

**请求参数 (PmsProjectPageReqVO，继承 PageParam：pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| pageNo | Integer | 否 | — | 页码（PageParam 默认 1） |
| pageSize | Integer | 否 | — | 每页条数（PageParam 默认 10） |
| name | String | 否 | — | 项目名称，模糊匹配 |
| sceneType | Integer | 否 | @InEnum(PmsProjectSceneTypeEnum.class) | 列表场景：1 全部项目（默认）/ 2 我负责的 / 3 我参与的 |
| groupId | Long | 否 | — | 个人项目分组编号（我参与场景下按分组过滤） |
| status | Integer | 否 | @InEnum(PmsProjectStatusEnum.class) | 项目状态，默认 1 进行中 |
| sortType | Integer | 否 | @InEnum(PmsProjectSortTypeEnum.class) | 排序类型：1 按访问时间（默认）/ 2 按创建时间 |

**响应**: CommonResult\<PageResult\<PmsProjectRespVO\>\>

**业务逻辑**: 1. 按项目状态和列表场景确定可查询的项目范围：查询归档/回收站项目时仅限我管理的项目；场景为「全部项目」时查询我参与的项目并附带公开项目（超级管理员附带全部项目）；场景为「我负责的」时仅限我管理的项目；场景为「我参与的」且指定 groupId 时按个人分组过滤。 2. 范围为空且不包含公开项目时直接返回空分页。 3. 分页查询项目列表。 4. Controller 按同 1.3 的方式批量拼接展示字段。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_110_000 | 项目分组不存在（按 groupId 过滤时） |

### 1.5 获得星标项目列表
- **路径**: GET /pms/pm/project/favorite-list
- **权限**: pms:pm:project:query
- **说明**: 获得当前用户参与且已星标的进行中项目列表

**请求参数**: 无

**响应**: CommonResult\<List\<PmsProjectRespVO\>\>（字段同 1.3）

**业务逻辑**: 1. 查询当前用户星标的项目编号与参与的项目编号，取交集得到可读的星标项目。 2. 交集为空直接返回空列表。 3. 查询其中处于进行中状态的项目。 4. Controller 拼接展示字段后返回。

### 1.6 获得项目概况
- **路径**: GET /pms/pm/project/overview
- **权限**: pms:pm:project:query
- **说明**: 统计项目工作项状态/类型分布、近十四日完成趋势和分配给当前用户的待办

**请求参数**: Query 参数 projectId（Long，必填，项目编号）

**响应**: CommonResult\<PmsProjectOverviewRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| totalCount | Long | 工作项总数 |
| pendingCount | Long | 未开始工作项数量 |
| processingCount | Long | 进行中工作项数量 |
| completedCount | Long | 已完成工作项数量 |
| typeCountMap | Map\<Integer, Long\> | 按工作项类型统计 |
| completedTrends | List\<TrendPoint\> | 近十四日完成趋势，TrendPoint 含 date（日期字符串）、count（当日完成数量） |
| assignedWorkItems | List\<AssignedWorkItem\> | 分配给当前用户的未完成工作项，含 id、serialNumber（项目内序号）、type、name、status（语义状态）、endTime、progress（完成进度） |

**业务逻辑**: 1. 校验项目可访问。 2. 查询项目的全部工作项，统计总数、未开始/进行中/已完成数量及按类型的数量分布。 3. 以近 14 天日期为桶，统计每日完成（按工作项 updateTime 日期）数量，生成完成趋势。 4. 过滤分配给当前用户且未完成的工作项，按截止时间（空值靠后）和编号排序，最多返回 10 条。 5. 组装概况返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 1.7 归档项目
- **路径**: PUT /pms/pm/project/archive
- **权限**: pms:pm:project:update
- **说明**: 将进行中的项目归档，并清除个人分组与星标关系

**请求参数**: Query 参数 id（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验项目存在。 2. 校验项目处于进行中。 3. 校验当前用户可以管理项目。 4. 以「状态为进行中」为条件更新为已归档并记录归档时间，条件更新未命中时抛出状态错误。 5. 删除该项目的个人分组关系与星标关系。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_002 | 只有项目管理员可以执行该操作 |

### 1.8 将项目移入回收站
- **路径**: PUT /pms/pm/project/recycle
- **权限**: pms:pm:project:update
- **说明**: 将进行中的项目移入回收站，并清除个人分组与星标关系

**请求参数**: Query 参数 id（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验项目存在。 2. 校验项目处于进行中。 3. 校验当前用户可以管理项目。 4. 以「状态为进行中」为条件更新为回收站状态并记录回收时间，条件更新未命中时抛出状态错误。 5. 删除该项目的个人分组关系与星标关系。

**错误码**: 同 1.7

### 1.9 恢复项目
- **路径**: PUT /pms/pm/project/restore
- **权限**: pms:pm:project:update
- **说明**: 将已归档或回收站中的项目恢复为进行中

**请求参数**: Query 参数 id（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验项目存在。 2. 校验项目不处于进行中（仅已归档或回收站可恢复）。 3. 校验当前用户可以管理项目。 4. 恢复为进行中并清空归档/回收站等生命周期时间，条件更新未命中时抛出状态错误。

**错误码**: 同 1.7

### 1.10 彻底删除回收站项目
- **路径**: DELETE /pms/pm/project/delete
- **权限**: pms:pm:project:delete
- **说明**: 彻底删除回收站中的项目及其全部关联数据，仅项目拥有者可操作

**请求参数**: Query 参数 id（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验项目存在。 2. 校验项目位于回收站。 3. 校验当前用户拥有项目所有者权限（OWNER 或超级管理员）。 4. 事务中依次删除项目工时记录、工作项、迭代、成员、个人分组关系、星标关系、公告。 5. 最后删除项目本身。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_007 | 只有项目拥有者可以执行该操作 |

---

## 2. 项目成员（Controller: PmsProjectMemberController，前缀 /pms/pm/project-member）

### 2.1 获得项目成员列表
- **路径**: GET /pms/pm/project-member/list
- **权限**: pms:pm:project-member:query
- **说明**: 获得项目成员及其权限级别，并拼接用户昵称与头像

**请求参数**: Query 参数 projectId（Long，必填，项目编号）

**响应**: CommonResult\<List\<PmsProjectMemberRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| userId | Long | 后台用户编号 |
| nickname | String | 用户昵称 |
| avatar | String | 用户头像 |
| level | Integer | 成员权限级别（1 拥有者 / 2 管理员 / 3 编辑 / 4 只读） |
| creatorStatus | Boolean | 是否项目创建人 |

**业务逻辑**: 1. 校验当前用户可以访问项目。 2. 查询项目全部成员，标记是否为项目创建人（creatorStatus）。 3. Controller 批量查询用户信息，拼接昵称与头像。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 2.2 保存项目成员及其权限级别
- **路径**: PUT /pms/pm/project-member/update-list
- **权限**: pms:pm:project-member:update
- **说明**: 全量保存项目成员列表及其权限级别（先删后插）

**请求参数 (PmsProjectMemberSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| members | List\<Member\> | 是 | @NotEmpty、@Valid | 项目成员列表 |
| members[].userId | Long | 是 | @NotNull | 后台用户编号 |
| members[].level | Integer | 是 | @NotNull、@InEnum(PmsProjectMemberLevelEnum.class) | 成员权限级别（不能为拥有者级别） |

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验操作人可以管理项目（可读 + OWNER/ADMIN 或超管）。 2. 校验成员编号不重复。 3. 校验成员账号存在。 4. 校验创建人不能出现在成员列表（创建人不能被移出或修改级别），且不能分配拥有者（OWNER）级别。 5. 删除项目原成员记录后，按请求批量插入每名成员的权限级别。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |
| 1_053_100_002 | 只有项目管理员可以执行该操作 |
| 1_053_105_000 | 项目成员不存在（成员编号重复时复用） |
| 1_053_105_001 | 项目创建人不能移出项目 |
| 1_053_105_002 | 项目拥有者级别不能直接分配 |

### 2.3 移除项目成员
- **路径**: DELETE /pms/pm/project-member/delete
- **权限**: pms:pm:project-member:update
- **说明**: 项目管理员移除一名成员

**请求参数**: Query 参数 projectId（Long，必填，项目编号）、userId（Long，必填，后台用户编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验操作人可以管理项目。 2. 校验待移除成员存在。 3. 校验待移除成员不是项目创建人也不是拥有者级别。 4. 删除该成员记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |
| 1_053_100_002 | 只有项目管理员可以执行该操作 |
| 1_053_105_000 | 项目成员不存在 |
| 1_053_105_001 | 项目创建人不能移出项目 |

### 2.4 主动退出项目
- **路径**: DELETE /pms/pm/project-member/exit
- **权限**: pms:pm:project-member:query（仅登录 + 数据行级校验）
- **说明**: 当前登录用户主动退出项目

**请求参数**: Query 参数 projectId（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验项目可访问。 2. 校验当前账号是该项目的直接成员。 3. 校验当前用户不是拥有者（OWNER）级别，拥有者不能退出项目。 4. 删除当前用户的成员记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |
| 1_053_105_000 | 项目成员不存在 |
| 1_053_105_003 | 项目拥有者不能退出项目 |

---

## 3. 项目分组（Controller: PmsProjectGroupController，前缀 /pms/pm/project-group）

> 分组为「个人维度」数据：每个用户拥有「全部项目」「未分组」两个系统分组（type 1/2）与若干自定义分组（type 3）。

### 3.1 创建项目分组
- **路径**: POST /pms/pm/project-group/create
- **权限**: pms:pm:project-group:create
- **说明**: 创建一个自定义分组，排序追加到现有分组末尾

**请求参数 (PmsProjectGroupSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 否 | — | 项目分组编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=100) | 分组名称 |

**响应**: CommonResult\<Long\> — 分组编号

**业务逻辑**: 1. 校验当前用户的分组名称唯一。 2. 查询当前用户最后一个分组，新分组 sort 追加在其后（无分组时从 2 开始，0/1 保留给系统分组）。 3. 创建类型为自定义（CUSTOM）的分组记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_110_001 | 项目分组名称已存在 |

### 3.2 修改项目分组
- **路径**: PUT /pms/pm/project-group/update
- **权限**: pms:pm:project-group:update
- **说明**: 修改自定义分组名称

**请求参数 (PmsProjectGroupSaveReqVO)**: 同 3.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验分组存在且属于当前用户。 2. 校验分组为自定义分组，系统分组不允许修改。 3. 校验分组名称唯一（排除自身）。 4. 仅更新分组名称（userId/sort/type 置 null 不更新）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_110_000 | 项目分组不存在 |
| 1_053_110_001 | 项目分组名称已存在 |
| 1_053_110_002 | 默认项目分组不允许修改 |

### 3.3 修改项目分组排序
- **路径**: PUT /pms/pm/project-group/update-sort
- **权限**: pms:pm:project-group:update
- **说明**: 批量更新个人分组的显示顺序

**请求参数 (PmsProjectGroupSortReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| items | List\<Item\> | 是 | @Valid、@NotEmpty | 项目分组排序项 |
| items[].id | Long | 是 | @NotNull | 项目分组编号 |
| items[].sort | Integer | 是 | @NotNull、@Min(0) | 显示顺序 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验排序列表中的分组都属于当前用户（数量不一致时抛分组不存在）。 2. 批量更新全部分组的显示顺序。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_110_000 | 项目分组不存在 |

### 3.4 删除项目分组
- **路径**: DELETE /pms/pm/project-group/delete
- **权限**: pms:pm:project-group:delete
- **说明**: 删除自定义分组及其项目分组关系

**请求参数**: Query 参数 id（Long，必填，项目分组编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验分组存在且属于当前用户。 2. 校验分组为自定义分组，系统分组不允许删除。 3. 删除该分组下的项目分组关系。 4. 删除分组本身。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_110_000 | 项目分组不存在 |
| 1_053_110_003 | 默认项目分组不允许删除 |

### 3.5 获得项目分组列表
- **路径**: GET /pms/pm/project-group/list
- **权限**: pms:pm:project-group:query
- **说明**: 获得当前用户的分组列表（含系统分组）及各分组的项目数量

**请求参数**: 无

**响应**: CommonResult\<List\<PmsProjectGroupRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 项目分组编号 |
| name | String | 分组名称 |
| sort | Integer | 显示顺序 |
| type | Integer | 分组类型：1 全部项目 / 2 未分组 / 3 自定义分组 |
| createTime | LocalDateTime | 创建时间 |
| projectCount | Integer | 分组内进行中项目数量 |

**业务逻辑**: 1. 查询当前用户的全部项目分组。 2. 若缺少「全部项目」「未分组」两个系统分组则补建，并按 sort 稳定排序。 3. 查询当前用户参与的进行中项目编号列表。 4. 统计各分组项目数量：自定义分组按分组关系计数，「全部项目」为参与项目总数，「未分组」为参与项目总数减去已分组数量。

### 3.6 移动项目到个人分组
- **路径**: PUT /pms/pm/project-group/move-project
- **权限**: pms:pm:project-group:update
- **说明**: 将项目加入/移出/更换个人分组

**请求参数 (PmsProjectGroupMoveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| groupId | Long | 否 | — | 目标项目分组编号；不传表示移动到未分组 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验当前用户是项目成员。 2. groupId 为空时视为移出分组，删除已有的个人分组关系。 3. 校验目标分组存在且属于当前用户；移动到「未分组」等同于移出分组；「全部项目」不允许作为目标分组。 4. 无已有分组关系时插入新关系（sort=0），否则更新关系的 groupId。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目（非项目成员时） |
| 1_053_110_000 | 项目分组不存在 |
| 1_053_110_002 | 默认项目分组不允许修改（目标为「全部项目」时） |

---

## 4. 项目收藏（Controller: PmsProjectFavoriteController，前缀 /pms/pm/project-favorite）

### 4.1 收藏项目
- **路径**: POST /pms/pm/project-favorite/create
- **权限**: pms:pm:project:query
- **说明**: 当前用户星标收藏一个项目（幂等）

**请求参数**: Query 参数 projectId（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验当前用户是项目成员。 2. 已存在收藏关系时直接返回（幂等）。 3. 插入收藏关系记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目（非项目成员时） |

### 4.2 取消收藏项目
- **路径**: DELETE /pms/pm/project-favorite/delete
- **权限**: pms:pm:project:query
- **说明**: 当前用户取消星标收藏（幂等）

**请求参数**: Query 参数 projectId（Long，必填，项目编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验当前用户是项目成员。 2. 查询收藏关系，存在则删除，不存在则跳过（幂等）。

**错误码**: 同 4.1

---

## 5. 项目公告（Controller: PmsProjectAnnouncementController，前缀 /pms/pm/project-announcement）

> 公告的创建/修改/删除复用项目编辑权限 `pms:pm:project:update`，查询复用 `pms:pm:project:query`，并在 Service 层校验项目可读/可写。

### 5.1 创建项目公告
- **路径**: POST /pms/pm/project-announcement/create
- **权限**: pms:pm:project:update
- **说明**: 在项目下发布一条公告

**请求参数 (PmsProjectAnnouncementSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 否 | — | 公告编号（创建时不传） |
| projectId | Long | 是 | @NotNull | 项目编号 |
| content | String | 是 | @NotBlank、@Size(max=5000) | 公告内容 |
| fileUrls | List\<String\> | 否 | — | 附件地址列表 |

**响应**: CommonResult\<Long\> — 公告编号

**业务逻辑**: 1. 校验当前用户对项目有编辑权限（成员级别可编辑或超级管理员）。 2. 插入公告记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_000 | 项目不存在 |
| 1_053_100_005 | 当前项目角色无编辑权限 |

### 5.2 更新项目公告
- **路径**: PUT /pms/pm/project-announcement/update
- **权限**: pms:pm:project:update
- **说明**: 更新项目公告内容与附件

**请求参数 (PmsProjectAnnouncementSaveReqVO)**: 同 5.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验公告存在。 2. 校验公告属于请求中的项目（projectId 不一致时视为公告不存在）。 3. 校验当前用户对公告所属项目有编辑权限。 4. 更新公告。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_006 | 项目公告不存在 |
| 1_053_100_000 | 项目不存在 |
| 1_053_100_005 | 当前项目角色无编辑权限 |

### 5.3 删除项目公告
- **路径**: DELETE /pms/pm/project-announcement/delete
- **权限**: pms:pm:project:update
- **说明**: 删除一条项目公告

**请求参数**: Query 参数 id（Long，必填，公告编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验公告存在。 2. 校验当前用户对公告所属项目有编辑权限。 3. 删除公告。

**错误码**: 同 5.2

### 5.4 获得项目公告详情
- **路径**: GET /pms/pm/project-announcement/get
- **权限**: pms:pm:project:query
- **说明**: 获得单条公告详情，含创建者昵称

**请求参数**: Query 参数 id（Long，必填，公告编号）

**响应**: CommonResult\<PmsProjectAnnouncementRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 公告编号 |
| projectId | Long | 项目编号 |
| content | String | 公告内容 |
| fileUrls | List\<String\> | 附件地址列表 |
| creatorUserId | Long | 创建者用户编号 |
| creatorUserName | String | 创建者用户昵称 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**: 1. 校验公告存在。 2. 校验当前用户对公告所属项目可读。 3. Controller 拼接创建者用户编号与昵称。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_100_006 | 项目公告不存在 |
| 1_053_100_000 | 项目不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 5.5 获得项目公告列表
- **路径**: GET /pms/pm/project-announcement/list
- **权限**: pms:pm:project:query
- **说明**: 获得项目下全部公告，含创建者昵称

**请求参数**: Query 参数 projectId（Long，必填，项目编号）

**响应**: CommonResult\<List\<PmsProjectAnnouncementRespVO\>\>（字段同 5.4）

**业务逻辑**: 1. 校验当前用户对项目可读。 2. 查询项目的全部公告。 3. Controller 批量查询创建者用户并拼接创建者昵称。

**错误码**: 同 5.4

---

## 6. 项目模板（Controller: PmsProjectTemplateController，前缀 /pms/pm/project-template）

> 项目模板定义某项目类型下的工作项类型、状态与看板列配置，供创建项目时一键初始化。模板为全局数据（不做成员级校验），依赖功能权限控制。

### 6.1 创建项目模板
- **路径**: POST /pms/pm/project-template/create
- **权限**: pms:pm:project-template:create
- **说明**: 创建一个项目模板，校验状态与看板列配置的一致性

**请求参数 (PmsProjectTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 否 | — | 模板编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=100) | 模板名称 |
| description | String | 否 | @Size(max=500) | 模板描述 |
| projectType | Integer | 是 | @NotNull、@InEnum(PmsProjectTypeEnum.class) | 项目类型：1 通用项目 / 2 敏捷开发项目 |
| status | Integer | 是 | @NotNull | 模板状态 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| itemTypes | List\<Integer\> | 是 | @NotEmpty | 启用的工作项类型列表 |
| statuses | List\<StatusTemplate\> | 是 | @Valid、@NotEmpty | 工作项状态模板列表 |
| statuses[].code | String | 是 | @NotBlank、@Size(max=50) | 模板内稳定编码 |
| statuses[].name | String | 是 | @NotBlank、@Size(max=50) | 状态名称 |
| statuses[].workItemType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemTypeEnum.class) | 工作项类型 |
| statuses[].statusType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemStatusTypeEnum.class) | 语义状态（未开始/进行中/已完成） |
| statuses[].defaultStatus | Boolean | 是 | @NotNull | 是否为初始状态 |
| statuses[].sort | Integer | 是 | @NotNull | 状态显示顺序 |
| statuses[].boardCode | String | 是 | @NotBlank | 所属看板列编码 |
| boards | List\<BoardTemplate\> | 是 | @Valid、@NotEmpty | 看板列模板列表 |
| boards[].code | String | 是 | @NotBlank、@Size(max=50) | 模板内稳定编码 |
| boards[].name | String | 是 | @NotBlank、@Size(max=50) | 看板列名称 |
| boards[].workItemType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemTypeEnum.class) | 工作项类型 |
| boards[].sort | Integer | 是 | @NotNull | 看板列显示顺序 |
| boards[].statusCodes | List\<String\> | 是 | @NotEmpty | 关联的状态编码列表 |

**响应**: CommonResult\<Long\> — 模板编号

**业务逻辑**: 1. 校验同一项目类型下的模板名称唯一。 2. 校验模板配置一致性：工作项类型不重复且均为有效枚举值。 3. 校验状态编码唯一、状态的工作项类型均在启用列表内，且每种工作项类型必须且只能配置一个初始状态。 4. 校验看板列编码唯一、关联状态编码不重复、看板列类型在启用列表内，且看板列关联的状态必须是同类型、boardCode 与该看板列互相匹配、每个状态只归属一个看板列。 5. 顶层字段与嵌套状态/看板列分别转换后插入模板记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_112_001 | 同一项目类型下的模板名称已存在 |
| 1_053_112_002 | 项目模板配置无效：{}（携带具体原因） |

### 6.2 更新项目模板
- **路径**: PUT /pms/pm/project-template/update
- **权限**: pms:pm:project-template:update
- **说明**: 更新项目模板及其状态、看板列配置

**请求参数 (PmsProjectTemplateSaveReqVO)**: 同 6.1（id 必传）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验模板存在。 2. 校验同一项目类型下的模板名称唯一（排除自身）。 3. 校验模板配置一致性（同 6.1 的 2-4 步）。 4. 转换后整体更新模板记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_112_000 | 项目模板不存在 |
| 1_053_112_001 | 同一项目类型下的模板名称已存在 |
| 1_053_112_002 | 项目模板配置无效：{} |

### 6.3 删除项目模板
- **路径**: DELETE /pms/pm/project-template/delete
- **权限**: pms:pm:project-template:delete
- **说明**: 删除一个项目模板

**请求参数**: Query 参数 id（Long，必填，模板编号）

**响应**: CommonResult\<Boolean\>

**业务逻辑**: 1. 校验模板存在。 2. 删除模板记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_112_000 | 项目模板不存在 |

### 6.4 获得项目模板
- **路径**: GET /pms/pm/project-template/get
- **权限**: pms:pm:project-template:query
- **说明**: 获得单个项目模板详情（含状态、看板列配置）

**请求参数**: Query 参数 id（Long，必填，模板编号）

**响应**: CommonResult\<PmsProjectTemplateRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 模板编号 |
| name | String | 模板名称 |
| description | String | 模板描述 |
| projectType | Integer | 项目类型 |
| status | Integer | 模板状态 |
| sort | Integer | 显示顺序 |
| itemTypes | List\<Integer\> | 启用的工作项类型列表 |
| statuses | List\<StatusTemplate\> | 工作项状态模板列表（结构同 6.1 请求） |
| boards | List\<BoardTemplate\> | 看板列模板列表（结构同 6.1 请求） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 校验模板存在，不存在时抛出错误。 2. 转换为响应 VO 返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_053_112_000 | 项目模板不存在 |

### 6.5 获得项目模板分页
- **路径**: GET /pms/pm/project-template/page
- **权限**: pms:pm:project-template:query
- **说明**: 按名称、项目类型、状态分页查询项目模板

**请求参数 (PmsProjectTemplatePageReqVO，继承 PageParam：pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| pageNo | Integer | 否 | — | 页码（PageParam 默认 1） |
| pageSize | Integer | 否 | — | 每页条数（PageParam 默认 10） |
| name | String | 否 | — | 模板名称，模糊匹配 |
| projectType | Integer | 否 | @InEnum(PmsProjectTypeEnum.class) | 项目类型 |
| status | Integer | 否 | — | 模板状态 |

**响应**: CommonResult\<PageResult\<PmsProjectTemplateRespVO\>\>（字段同 6.4）

**业务逻辑**: 1. 按名称模糊、项目类型、状态条件分页查询模板。 2. 转换为响应 VO 分页返回。

**域相关错误码汇总（除上述已列外）**:

| 错误码 | 说明 |
|--------|------|
| 1_053_105_000 | 项目成员不存在 |
| 1_053_105_001 | 项目创建人不能移出项目 |
| 1_053_105_002 | 项目拥有者级别不能直接分配 |
| 1_053_105_003 | 项目拥有者不能退出项目 |
| 1_053_110_000 | 项目分组不存在 |
| 1_053_110_001 | 项目分组名称已存在 |
| 1_053_110_002 | 默认项目分组不允许修改 |
| 1_053_110_003 | 默认项目分组不允许删除 |
