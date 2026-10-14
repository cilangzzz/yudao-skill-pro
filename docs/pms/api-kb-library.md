# 知识库与分组接口 (PmsKnowledgeLibraryController)

> PMS 知识库「库级」管理域：知识库的创建/更新/删除/查询、成员（用户/部门）管理、个人知识库分组，以及用于一键初始化文档的知识库模板。所有操作在 Service 层按当前登录用户做可读/可写/管理员/创建人校验，超级管理员（SUPER_ADMIN 角色）放行。

## 接口路径前缀

- /pms/kb/library  (Controller: PmsKnowledgeLibraryController)
- /pms/kb/library-member  (Controller: PmsKnowledgeLibraryMemberController)
- /pms/kb/group  (Controller: PmsKnowledgeGroupController)
- /pms/kb/library-template  (Controller: PmsKnowledgeLibraryTemplateController)

**通用枚举**：
- 成员等级 `level`（PmsKnowledgeLibraryMemberLevelEnum）：`1` 创建人、`2` 管理员、`3` 成员
- 分组类型 `type`（PmsKnowledgeGroupTypeEnum）：`1` 全部知识库（系统分组）、`2` 未分组（系统分组）、`3` 自定义分组

---

## 1. 知识库管理（PmsKnowledgeLibraryController）

### 1.1 创建知识库

- **路径**: POST /pms/kb/library/create
- **权限**: pms:kb:library:create
- **说明**: 创建知识库，同时加入创建人与初始成员，可选用模板初始化文档

**请求参数 (PmsKnowledgeLibrarySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 知识库编号（创建时无需） |
| name | String | 是 | @NotBlank、@Size(max=50) | 知识库名称 |
| description | String | 否 | @Size(max=300) | 知识库简介 |
| openStatus | Boolean | 是 | @NotNull | 是否公开 |
| coverUrl | String | 否 | @Size(max=255) | 知识库封面 |
| adminUserIds | List&lt;Long&gt; | 否 | - | 创建时的初始管理员用户编号列表 |
| memberUserIds | List&lt;Long&gt; | 否 | - | 创建时的初始普通成员用户编号列表 |
| templateId | Long | 否 | @Positive | 模板编号，仅创建时有效 |

**响应**: CommonResult&lt;Long&gt; —— 知识库编号

**业务逻辑**:
1. 将请求转换为 DO 并设置状态为 NORMAL，插入知识库记录。
2. 创建初始成员：创建人以 CREATOR 级别加入，adminUserIds 以 ADMIN 级别、memberUserIds 以 MEMBER 级别加入；校验初始成员不能为空/重复/包含创建人，并校验用户账号存在。
3. 若指定 templateId，使用该模板在知识库根目录批量创建富文本文档。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_005 | 知识库成员数据无效 |
| 1_053_130_084 | 知识库模板不存在 |
| 1_053_130_085 | 知识库模板配置无效 |

### 1.2 更新知识库

- **路径**: PUT /pms/kb/library/update
- **权限**: pms:kb:library:update
- **说明**: 更新知识库基本信息，管理员维护；公开库转私有限创建人

**请求参数 (PmsKnowledgeLibrarySaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前用户是知识库管理员（创建人/管理员等级，超级管理员放行）。
2. 若知识库当前为公开且请求要转为私有，校验当前用户是知识库创建人（超级管理员放行）。
3. 更新知识库基本信息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_003 | 只有知识库管理员可以执行该操作 |

### 1.3 删除知识库

- **路径**: DELETE /pms/kb/library/delete
- **权限**: pms:kb:library:delete
- **说明**: 删除知识库（创建人操作），知识库及内容移入回收站

**请求参数**: Query 参数 `id`（Long，必填，知识库编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前用户是知识库创建人（超级管理员放行）。
2. 将知识库及其全部内容（成员、分组关系、文件夹、文档等）移入回收站。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_003 | 只有知识库管理员可以执行该操作（创建人校验不通过时抛出） |

### 1.4 获得知识库详情

- **路径**: GET /pms/kb/library/get
- **权限**: pms:kb:library:query
- **说明**: 获得知识库详情，含成员数、内容统计与当前用户权限标识

**请求参数**: Query 参数 `id`（Long，必填，知识库编号）

**响应**: CommonResult&lt;PmsKnowledgeLibraryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 知识库编号 |
| name | String | 知识库名称 |
| description | String | 知识库简介 |
| openStatus | Boolean | 是否公开 |
| coverUrl | String | 知识库封面 |
| creatorUserId | Long | 创建人用户编号 |
| creatorUserName | String | 创建人姓名 |
| memberCount | Integer | 成员数量 |
| documentCount | Long | 文档数量（富文本文档） |
| fileCount | Long | 文件数量 |
| writeStatus | Boolean | 当前用户是否可以编辑内容 |
| adminStatus | Boolean | 当前用户是否为知识库管理员 |
| exitStatus | Boolean | 当前用户是否可以主动退出知识库 |
| favoriteStatus | Boolean | 当前用户是否已关注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验知识库存在且当前用户可读（公开库或成员，超级管理员放行；私有非成员抛无权访问）。
2. 批量查询知识库成员、文档类型统计、创建人昵称、当前用户部门、是否超级管理员、收藏状态。
3. 计算权限标识：writeStatus=超管或任意成员；adminStatus=超管或创建人/管理员等级成员；exitStatus=当前用户为直接成员且非创建人；favoriteStatus=已收藏。
4. 按文档类型统计富文本数量与文件数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_001 | 无权访问该知识库 |

### 1.5 获得知识库分页

- **路径**: GET /pms/kb/library/page
- **权限**: pms:kb:library:query
- **说明**: 分页获得当前用户可见的知识库，可按个人分组过滤

**请求参数 (PmsKnowledgeLibraryPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承 PageParam） |
| name | String | 否 | - | 知识库名称 |
| groupId | Long | 否 | - | 个人知识库分组编号 |

**响应**: CommonResult&lt;PageResult&lt;PmsKnowledgeLibraryRespVO&gt;&gt;，元素字段同 1.4

**业务逻辑**:
1. 查询当前用户参与（用户或部门成员）且未删除/未进入回收站的知识库编号。
2. 若指定 groupId，将可读知识库按个人分组过滤（全部知识库不过滤、未分组取未建立关系者、自定义分组取有关系者），过滤结果为空直接返回空页。
3. 超级管理员查询全部知识库，普通用户仅查询公开或已加入的知识库。
4. 分页查询 NORMAL 状态知识库，并按 1.4 相同逻辑拼接成员数、文档/文件数、权限标识、收藏状态与创建人姓名。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_020 | 知识库分组不存在（groupId 校验失败时） |

---

## 2. 知识库成员（PmsKnowledgeLibraryMemberController）

### 2.1 获得知识库成员列表

- **路径**: GET /pms/kb/library-member/list
- **权限**: pms:kb:library:query
- **说明**: 获得知识库全部成员（用户与部门成员），拼接昵称、头像与部门信息

**请求参数**: Query 参数 `libraryId`（Long，必填，知识库编号）

**响应**: CommonResult&lt;List&lt;PmsKnowledgeLibraryMemberRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 成员编号 |
| userId | Long | 用户编号 |
| nickname | String | 用户姓名 |
| avatar | String | 用户头像 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| parentDeptId | Long | 父部门编号 |
| parentDeptName | String | 父部门名称 |
| level | Integer | 成员等级（1 创建人/2 管理员/3 成员） |

**业务逻辑**:
1. 校验知识库可读（存在、非回收站、公开或成员）。
2. 查询知识库全部成员记录（用户成员 + 部门成员）。
3. 批量拼接用户昵称、头像与部门名称、父部门名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_001 | 无权访问该知识库 |

### 2.2 更新知识库成员

- **路径**: PUT /pms/kb/library-member/update-list
- **权限**: pms:kb:library:update
- **说明**: 管理员全量重建知识库管理员与普通成员，保留创建人

**请求参数 (PmsKnowledgeLibraryUpdateMemberListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| libraryId | Long | 是 | @NotNull | 知识库编号 |
| members | List&lt;Member&gt; | 是 | @NotNull、@Valid | 成员列表（全量提交） |
| members[].userId | Long | 否 | 与 deptId 二选一（@AssertTrue） | 用户编号 |
| members[].deptId | Long | 否 | 与 userId 二选一（@AssertTrue） | 部门编号 |
| members[].level | Integer | 是 | @NotNull、@InEnum(PmsKnowledgeLibraryMemberLevelEnum) | 成员等级（1/2/3） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前用户是知识库管理员。
2. 校验成员不重复（userId/deptId 数量与列表一致）、不包含知识库创建人、不能伪造创建人等级。
3. 校验用户成员、部门成员真实存在。
4. 删除原有管理员与普通成员（保留创建人），批量插入新成员。
5. 对比新旧成员，删除已移出成员在知识库内的内容级协作权限。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_003 | 只有知识库管理员可以执行该操作 |
| 1_053_130_005 | 知识库成员数据无效 |

### 2.3 主动退出知识库

- **路径**: DELETE /pms/kb/library-member/exit
- **权限**: pms:kb:library:query
- **说明**: 当前用户主动退出知识库，创建人不可退出

**请求参数**: Query 参数 `libraryId`（Long，必填，知识库编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验知识库可访问。
2. 校验当前账号是该知识库的直接成员（用户维度，不含部门继承），否则抛错。
3. 校验创建人不能主动退出。
4. 删除成员记录，并清理当前账号在知识库内的内容级协作权限。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_004 | 知识库创建人不能移出知识库 |
| 1_053_130_086 | 当前账号不是该知识库的直接成员 |

---

## 3. 知识库分组（PmsKnowledgeGroupController）

### 3.1 创建知识库分组

- **路径**: POST /pms/kb/group/create
- **权限**: pms:kb:library:create
- **说明**: 创建个人自定义分组，排序追加到现有分组末尾

**请求参数 (PmsKnowledgeGroupSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 知识库分组编号（创建时无需） |
| name | String | 是 | @NotBlank、@Size(max=100) | 分组名称 |

**响应**: CommonResult&lt;Long&gt; —— 分组编号

**业务逻辑**:
1. 校验同一用户下分组名称唯一。
2. 查询当前用户最后一个分组的 sort，新分组 sort 取其 +1（最小为 2，排在两个系统分组之后）。
3. 插入 CUSTOM（自定义）类型分组并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_021 | 知识库分组名称已存在 |

### 3.2 修改知识库分组

- **路径**: PUT /pms/kb/group/update
- **权限**: pms:kb:library:update
- **说明**: 修改自定义分组名称，系统分组不允许修改

**请求参数 (PmsKnowledgeGroupSaveReqVO)**: 同 3.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验分组存在且属于当前用户。
2. 校验分组为自定义分组（系统分组不允许修改）。
3. 校验分组名称唯一。
4. 仅更新分组名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_020 | 知识库分组不存在 |
| 1_053_130_021 | 知识库分组名称已存在 |
| 1_053_130_022 | 默认知识库分组不允许修改 |

### 3.3 修改知识库分组排序

- **路径**: PUT /pms/kb/group/update-sort
- **权限**: pms:kb:library:update
- **说明**: 按提交列表批量更新分组显示顺序

**请求参数 (PmsKnowledgeGroupSortReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 分组排序项列表 |
| items[].id | Long | 是 | @NotNull | 知识库分组编号 |
| items[].sort | Integer | 是 | @NotNull、@Min(0) | 显示顺序 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验排序列表中的分组全部属于当前用户（数量一致，否则抛分组不存在）。
2. 批量更新全部分组的显示顺序。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_020 | 知识库分组不存在 |
| 1_053_130_024 | 知识库分组排序列表存在重复分组 |

### 3.4 删除知识库分组

- **路径**: DELETE /pms/kb/group/delete
- **权限**: pms:kb:library:delete
- **说明**: 删除自定义分组及其分组关系，系统分组不允许删除

**请求参数**: Query 参数 `id`（Long，必填，知识库分组编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验分组存在且属于当前用户。
2. 校验分组为自定义分组（系统分组不允许删除）。
3. 删除该用户该分组的全部知识库分组关系，再删除分组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_020 | 知识库分组不存在 |
| 1_053_130_023 | 默认知识库分组不允许删除 |

### 3.5 获得知识库分组列表

- **路径**: GET /pms/kb/group/list
- **权限**: pms:kb:library:query
- **说明**: 获得当前用户全部分组（含系统分组），并统计各分组知识库数量

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;PmsKnowledgeGroupRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 知识库分组编号 |
| name | String | 分组名称 |
| sort | Integer | 显示顺序 |
| type | Integer | 分组类型（1 全部/2 未分组/3 自定义） |
| libraryCount | Integer | 分组内知识库数量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 查询当前用户的知识库分组列表。
2. 缺失时补齐「全部知识库」（sort=0）和「未分组」（sort=1）两个系统分组。
3. 统计各分组知识库数量：仅统计当前用户可读的知识库；「全部」= 可读总数，「未分组」= 可读总数 - 已分组数，自定义分组按关系表统计。

**错误码**: 无专属错误码

### 3.6 获得知识库分组

- **路径**: GET /pms/kb/group/get
- **权限**: pms:kb:library:query
- **说明**: 获得指定个人分组详情（不含数量统计）

**请求参数**: Query 参数 `id`（Long，必填，知识库分组编号）

**响应**: CommonResult&lt;PmsKnowledgeGroupRespVO&gt;，字段同 3.5（libraryCount 为 null）

**业务逻辑**:
1. 校验分组存在且属于当前用户，返回分组详情。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_020 | 知识库分组不存在 |

### 3.7 移动知识库到个人分组

- **路径**: PUT /pms/kb/group/move
- **权限**: pms:kb:library:update
- **说明**: 将知识库加入/移出个人分组（可收藏公开知识库）

**请求参数 (PmsKnowledgeLibraryMoveGroupReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| libraryId | Long | 是 | @NotNull | 知识库编号 |
| groupId | Long | 否 | - | 目标分组编号；为空表示移出分组 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前用户可读取该知识库（个人分组允许收藏公开知识库）。
2. groupId 为空或目标分组为「未分组」时，删除该用户该知识库已有的个人分组关系（移出分组）。
3. 目标分组为「全部知识库」时抛默认分组不允许修改错误。
4. 无分组关系则新增（sort=0），已有则更新为目标分组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在 |
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_020 | 知识库分组不存在 |
| 1_053_130_022 | 默认知识库分组不允许修改 |

---

## 4. 知识库模板（PmsKnowledgeLibraryTemplateController）

### 4.1 创建知识库模板

- **路径**: POST /pms/kb/library-template/create
- **权限**: pms:kb:library-template:create
- **说明**: 创建知识库模板，模板内含一组初始富文本文档配置

**请求参数 (PmsKnowledgeLibraryTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 模板编号（创建时无需） |
| name | String | 是 | @NotBlank、@Size(max=100) | 模板名称 |
| description | String | 否 | @Size(max=500) | 模板简介 |
| coverUrl | String | 否 | @Size(max=255) | 模板封面地址 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 模板状态（0 开启/1 禁用） |
| sort | Integer | 是 | @NotNull、@PositiveOrZero | 显示顺序 |
| documents | List&lt;Document&gt; | 是 | @NotEmpty、@Valid | 模板文档列表 |
| documents[].title | String | 是 | @NotBlank、@Size(max=255) | 文档标题 |
| documents[].content | String | 是 | @NotBlank | 文档内容 |

**响应**: CommonResult&lt;Long&gt; —— 模板编号

**业务逻辑**:
1. 校验模板名称唯一。
2. 校验文档配置有效：文档列表不能为空、每篇文档标题与内容非空、标题不重复。
3. 插入模板（文档列表以 JSON 存储），返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_085 | 知识库模板配置无效 |
| 1_053_130_087 | 知识库模板名称已存在 |

### 4.2 更新知识库模板

- **路径**: PUT /pms/kb/library-template/update
- **权限**: pms:kb:library-template:update
- **说明**: 更新知识库模板基本信息与文档配置

**请求参数 (PmsKnowledgeLibraryTemplateSaveReqVO)**: 同 4.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验模板存在。
2. 校验模板名称唯一（排除自身）。
3. 校验文档配置有效（非空、标题内容完整、标题不重复）。
4. 更新模板及文档列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_084 | 知识库模板不存在 |
| 1_053_130_085 | 知识库模板配置无效 |
| 1_053_130_087 | 知识库模板名称已存在 |

### 4.3 删除知识库模板

- **路径**: DELETE /pms/kb/library-template/delete
- **权限**: pms:kb:library-template:delete
- **说明**: 删除指定模板

**请求参数**: Query 参数 `id`（Long，必填，模板编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验模板存在。
2. 删除模板。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_084 | 知识库模板不存在 |

### 4.4 获得知识库模板

- **路径**: GET /pms/kb/library-template/get
- **权限**: pms:kb:library-template:query
- **说明**: 获得模板详情（含文档列表）

**请求参数**: Query 参数 `id`（Long，必填，模板编号）

**响应**: CommonResult&lt;PmsKnowledgeLibraryTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模板编号 |
| name | String | 模板名称 |
| description | String | 模板简介 |
| coverUrl | String | 模板封面地址 |
| status | Integer | 模板状态（0 开启/1 禁用） |
| sort | Integer | 显示顺序 |
| documents | List&lt;Document&gt; | 模板文档列表（title、content） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验模板存在，返回模板详情。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_084 | 知识库模板不存在 |

### 4.5 获取知识库模板全列表

- **路径**: GET /pms/kb/library-template/simple-list
- **权限**: 已认证（无 @PreAuthorize，仅登录即可访问）
- **说明**: 返回全部启用状态模板，仅含模板选择所需基本字段与文档标题

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;PmsKnowledgeLibraryTemplateRespVO&gt;&gt;（精简：id、name、coverUrl、description、documents（仅 title））

**业务逻辑**:
1. 查询全部启用状态（ENABLE）的模板。
2. 仅返回编号、名称、封面、简介及每篇文档的标题。

### 4.6 获得知识库模板分页

- **路径**: GET /pms/kb/library-template/page
- **权限**: pms:kb:library-template:query
- **说明**: 分页获得模板列表，支持名称模糊与状态过滤

**请求参数 (PmsKnowledgeLibraryTemplatePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承 PageParam） |
| name | String | 否 | - | 模板名称，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 模板状态 |

**响应**: CommonResult&lt;PageResult&lt;PmsKnowledgeLibraryTemplateRespVO&gt;&gt;，元素字段同 4.4

**业务逻辑**:
1. 按名称模糊匹配、状态条件分页查询模板。

**错误码**: 无专属错误码
