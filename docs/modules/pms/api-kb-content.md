# 知识库内容管理接口 (PmsKnowledgeDocumentController / PmsKnowledgeFolderController / PmsKnowledgeDocumentLabelController / PmsKnowledgeContentPermissionController)

> 提供 PMS 知识库的内容管理能力：文档与文件夹的创建、更新、移动、回收站删除、目录树查询、全局搜索，文档标签维护，以及知识内容（文件夹/文档）的协作权限管理。

## 接口路径前缀

- /pms/kb/document  (Controller: PmsKnowledgeDocumentController)
- /pms/kb/folder  (Controller: PmsKnowledgeFolderController)
- /pms/kb/document-label  (Controller: PmsKnowledgeDocumentLabelController)
- /pms/kb/content-permission  (Controller: PmsKnowledgeContentPermissionController)

## 1. 知识库文档（/pms/kb/document）

### 1.1 创建文档

- **路径**: POST /pms/kb/document/create
- **权限**: pms:kb:library:update
- **说明**: 在指定知识库的文件夹或父文档下创建一篇富文本或文件型文档，并继承所在位置的协作权限。

**请求参数 (PmsKnowledgeDocumentCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| libraryId | Long | 是 | @NotNull | 知识库编号 |
| folderId | Long | 是 | @NotNull | 文件夹编号（0 表示知识库根目录；与父文档同时指定时文件夹优先） |
| parentId | Long | 是 | @NotNull | 父文档编号（0 表示无父文档） |
| title | String | 是 | @NotBlank、@Size(max = 255) | 文档标题 |
| type | Integer | 是 | @NotNull、@InEnum(PmsKnowledgeDocumentTypeEnum) | 文档类型（3 富文本 / 4 文件） |
| content | String | 否 | - | 文档内容或文件地址 |
| fileType | String | 否 | @Size(max = 50) | 文件类型（如 pdf） |
| fileSize | Long | 否 | @Min(0)、@Max(104857600) | 文件大小，单位字节，最大 100 MB |

**响应**: CommonResult&lt;Long&gt; —— 新创建的文档编号。

**业务逻辑**:
1. 校验当前用户对该知识库有读取权限（validateLibraryReadable）。
2. 规范并校验目录位置（normalizeAndValidateDocumentPlacement）：文件夹优先于父文档，放入文件夹时校验文件夹属于该知识库、处于正常状态且可编辑，返回文件夹的权限编号；指定父文档时校验父文档存在、属于目标知识库、状态正常且可编辑，返回父文档的权限编号；两者均为根节点时规范到知识库根目录并校验知识库编辑权限。
3. 若未继承到权限编号（位于知识库根目录），创建一条默认的内容协作权限（公开、仅预览，创建人拥有管理权限）。
4. 组装文档记录：设置权限编号、文档类型与正常状态（NORMAL），插入文档表，返回文档编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_002 | 无权编辑该知识库 |
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_010 | 父文档与知识库不匹配 |
| 1_053_130_011 | 文档文件夹与知识库不匹配 |
| 1_053_130_014 | 文档类型无效 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_072 | 无权编辑该知识内容 |

### 1.2 更新文档内容

- **路径**: PUT /pms/kb/document/update
- **权限**: pms:kb:library:update
- **说明**: 更新文档标题、正文/文件地址、标签等字段；目录位置不可通过该接口修改。

**请求参数 (PmsKnowledgeDocumentUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文档编号 |
| title | String | 否 | @Size(max = 255) | 文档标题 |
| content | String | 否 | - | 文档内容或文件地址 |
| labelIds | List&lt;Long&gt; | 否 | - | 标签编号列表；传空集合表示清空标签 |
| fileType | String | 否 | @Size(max = 50) | 文件类型 |
| fileSize | Long | 否 | @Min(0)、@Max(104857600) | 文件大小，单位字节 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档存在且不在回收站（否则抛 1_053_130_009）。
2. 校验所属知识库可读。
3. 校验当前用户对该文档内容有编辑权限（协作等级可编辑）。
4. 校验标签编号列表中的标签均存在。
5. 更新文档记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_072 | 无权编辑该知识内容 |
| 1_053_130_030 | 知识库文档标签不存在 |

### 1.3 将文档移入回收站

- **路径**: DELETE /pms/kb/document/delete
- **权限**: pms:kb:library:delete
- **说明**: 将文档及其全部子文档移入知识库回收站（软删除）。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 文档编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档存在且不在回收站。
2. 校验所属知识库可读。
3. 校验当前用户对该文档内容有删除权限（协作等级可删除）。
4. 获得该文档及其全部子文档列表（逐层递归，visited 集合防御环形数据）。
5. 将文档与全部子文档移入回收站（recycleService.recycleDocument）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_073 | 无权删除该知识内容 |

### 1.4 移动文档

- **路径**: PUT /pms/kb/document/move
- **权限**: pms:kb:library:update
- **说明**: 将文档移动到其他文件夹、父文档或知识库，移动时整棵子文档树同步迁移；跨知识库移动会复制协作权限。

**请求参数 (PmsKnowledgeDocumentMoveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文档编号 |
| targetLibraryId | Long | 是 | @NotNull | 目标知识库编号 |
| targetFolderId | Long | 是 | @NotNull | 目标文件夹编号（0 表示根目录） |
| targetParentId | Long | 是 | @NotNull | 目标父文档编号（0 表示无父文档） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验源文档存在且不在回收站。
2. 校验移动目标只能选择一种容器：目标文件夹与目标父文档必须有一个为根节点（0），否则抛错。
3. 校验源知识库和目标知识库均可读。
4. 移动会改变目录结构，校验当前用户对源文档内容有管理权限。
5. 规范并校验目标位置（同创建逻辑，但按管理权限校验），并禁止移动到自身或其子文档下。
6. 获得文档子树；跨知识库移动时批量复制子树的全部协作权限到目标知识库（cloneContentPermissions），保持原权限与新权限的映射关系。
7. 批量更新文档位置：全部子文档同步所属知识库与权限编号，仅源文档更新文件夹/父文档编号。
8. 跨知识库移动时同步更新关注与最近浏览记录的知识库归属，并删除不再被引用的旧协作权限。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_010 | 父文档与知识库不匹配 |
| 1_053_130_011 | 文档文件夹与知识库不匹配 |
| 1_053_130_012 | 文档不能移动到自身或其子文档中 |
| 1_053_130_015 | 文档移动目标只能选择文件夹或父文档之一 |
| 1_053_130_070 | 知识内容协作权限不存在 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_072 | 无权编辑该知识内容 |

### 1.5 获得文档详情

- **路径**: GET /pms/kb/document/get
- **权限**: pms:kb:library:query
- **说明**: 获得文档详情，并拼接当前用户协作等级、下载权限、关注/点赞状态、点赞用户列表；可选择记录本次浏览。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 文档编号 |
| view | Boolean | 否 | @RequestParam(defaultValue = "false") | 是否记录本次浏览 |

**响应**: CommonResult&lt;PmsKnowledgeDocumentRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文档编号 |
| libraryId | Long | 知识库编号 |
| permissionId | Long | 协作权限编号 |
| currentUserLevel | Integer | 当前用户协作等级（1 管理员 / 2 可编辑 / 3 仅预览 / 4 可下载 / 5 可上传下载） |
| downloadStatus | Boolean | 当前用户是否可下载 |
| libraryName | String | 知识库名称 |
| folderId | Long | 文件夹编号 |
| parentId | Long | 父文档编号 |
| title | String | 文档标题 |
| contentSummary | String | 正文摘要（搜索分页时返回） |
| content | String | 文档内容或文件地址（文件型文档无下载权限时置空） |
| previewUrl | String | 文件预览地址（下载权限不足时仍可用于在线预览） |
| type | Integer | 文档类型（3 富文本 / 4 文件） |
| fileType | String | 文件类型 |
| fileSize | Long | 文件大小，单位字节 |
| status | Integer | 文档状态 |
| labelIds | List&lt;Long&gt; | 标签编号列表 |
| creatorUserId | Long | 创建人用户编号 |
| creatorUserName | String | 创建人姓名 |
| favoriteStatus | Boolean | 当前用户是否已关注 |
| likeStatus | Boolean | 当前用户是否已点赞 |
| likeUsers | List&lt;LikeUser&gt; | 点赞用户列表（含 id/nickname/avatar） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 校验文档存在且不在回收站。
2. 校验所属知识库可读、当前用户对该文档内容有读取权限。
3. view=true 时创建浏览记录（记录知识库、对象类型、对象编号与用户）。
4. 拼接 VO：查询当前用户内容协作等级，计算可下载状态（非仅预览即可下载），设置文件预览地址与关注状态。
5. 文件型文档且不可下载时，将实际文件地址 content 置空以隐藏真实地址。
6. 一次查询文档的全部点赞记录与相关用户信息，拼接创建人姓名、点赞状态与点赞用户列表（昵称、头像）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_071 | 无权访问该知识内容 |

### 1.6 全局搜索文档（分页）

- **路径**: GET /pms/kb/document/search-page
- **权限**: pms:kb:library:query
- **说明**: 使用 MySQL 对标题和正文进行模糊搜索，仅返回当前用户可读知识库中可读的文档，正文以摘要形式返回。

**请求参数 (PmsKnowledgeDocumentSearchPageReqVO，继承 PageParam 分页参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| keyword | String | 否 | - | 搜索关键字 |
| libraryId | Long | 否 | - | 知识库编号 |
| creatorUserId | Long | 否 | - | 创建人用户编号 |
| updateTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 更新时间范围 |

**响应**: CommonResult&lt;PageResult&lt;PmsKnowledgeDocumentRespVO&gt;&gt; —— 字段同 1.5，其中 content 恒为空、contentSummary 为去除 HTML 标签后的 120 字摘要，另含 libraryName。

**业务逻辑**:
1. 查询当前用户可读的知识库编号列表；若为空，或指定 libraryId 不可读，返回空分页。
2. 批量计算当前用户在这些知识库下可读的内容权限编号集合；为空则返回空分页。
3. 按关键字、知识库、创建人、更新时间范围等条件，对非回收站状态的文档执行 MySQL 模糊分页查询。
4. 拼接返回 VO：清空正文、生成正文摘要，批量拼接知识库名称与创建人姓名。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_070 | 知识内容协作权限不存在 |

## 2. 知识库文件夹（/pms/kb/folder）

### 2.1 创建文件夹

- **路径**: POST /pms/kb/folder/create
- **权限**: pms:kb:library:update
- **说明**: 在知识库根目录或指定父文件夹下创建文件夹，并继承父级协作权限。

**请求参数 (PmsKnowledgeFolderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 文件夹编号（创建时不传） |
| libraryId | Long | 是 | @NotNull | 知识库编号 |
| parentId | Long | 是 | @NotNull | 父文件夹编号（0 表示根目录） |
| title | String | 是 | @NotBlank、@Size(max = 255) | 文件夹标题 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的文件夹编号。

**业务逻辑**:
1. 校验当前用户对该知识库有读取权限。
2. 校验父文件夹存在：parentId 为空或 0 时视为根目录；否则父文件夹必须存在、属于该知识库且处于正常状态。
3. 根目录下创建时校验知识库编辑权限，并新建一条默认内容协作权限（公开、仅预览）；子目录下创建时校验父文件夹内容可编辑，并继承父文件夹的权限编号。
4. 组装文件夹记录（设置权限编号与正常状态）并插入，返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_002 | 无权编辑该知识库 |
| 1_053_130_007 | 父文件夹与知识库不匹配 |
| 1_053_130_072 | 无权编辑该知识内容 |

### 2.2 更新文件夹

- **路径**: PUT /pms/kb/folder/update
- **权限**: pms:kb:library:update
- **说明**: 修改文件夹标题；目录位置（所属知识库、父文件夹）不可通过该接口修改，需走移动接口。

**请求参数 (PmsKnowledgeFolderSaveReqVO)**: 同 2.1，其中 id 为必传的文件夹编号。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文件夹存在且不在回收站。
2. 校验所属知识库可读。
3. 校验当前用户对该文件夹内容有编辑权限。
4. 校验请求中的 libraryId 与文件夹实际所属知识库一致，否则抛错。
5. 仅更新文件夹标题（强制置空 libraryId 与 parentId，避免改动目录位置）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_006 | 知识库文件夹不存在 |
| 1_053_130_007 | 父文件夹与知识库不匹配 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_072 | 无权编辑该知识内容 |

### 2.3 将文件夹移入回收站

- **路径**: DELETE /pms/kb/folder/delete
- **权限**: pms:kb:library:delete
- **说明**: 将文件夹及其全部子文件夹、其中的文档一并移入回收站（软删除）。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 文件夹编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文件夹存在且不在回收站。
2. 校验所属知识库可读。
3. 校验当前用户对该文件夹内容有删除权限。
4. 获得该文件夹及其全部子文件夹（逐层递归，visited 集合防御环形数据），并查询这些文件夹包含的全部文档（含子文档）。
5. 将文件夹子树与文档移入回收站（recycleService.recycleFolder）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_006 | 知识库文件夹不存在 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_073 | 无权删除该知识内容 |

### 2.4 移动文件夹

- **路径**: PUT /pms/kb/folder/move
- **权限**: pms:kb:library:update
- **说明**: 将文件夹移动到其他父文件夹或知识库，移动时整个子文件夹树及其中文档同步迁移；跨知识库移动会复制协作权限。

**请求参数 (PmsKnowledgeFolderMoveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文件夹编号 |
| targetLibraryId | Long | 是 | @NotNull | 目标知识库编号 |
| targetParentId | Long | 是 | @NotNull | 目标父文件夹编号（0 表示根目录） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验源文件夹存在且不在回收站；校验源知识库和目标知识库均可读。
2. 移动会改变目录结构，校验当前用户对源文件夹内容有管理权限。
3. 校验目标父文件夹存在（根目录时校验目标知识库管理权限；子目录时校验目标文件夹管理权限）。
4. 校验目标父文件夹不在自身及其子文件夹中（防止移动到自身子树）。
5. 收集子文件夹树及其中文档的全部源协作权限；跨知识库移动时批量复制权限到目标知识库。
6. 批量更新子文件夹：全部同步所属知识库与权限编号，仅源文件夹更新父文件夹编号；文档同步执行移动（moveDocumentList）。
7. 跨知识库移动时同步更新关注与最近浏览记录的知识库归属，并删除不再被引用的旧协作权限。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_006 | 知识库文件夹不存在 |
| 1_053_130_007 | 父文件夹与知识库不匹配 |
| 1_053_130_008 | 文件夹不能移动到自身或其子文件夹中 |
| 1_053_130_070 | 知识内容协作权限不存在 |
| 1_053_130_071 | 无权访问该知识内容 |
| 1_053_130_072 | 无权编辑该知识内容 |

### 2.5 获得文件夹详情

- **路径**: GET /pms/kb/folder/get
- **权限**: pms:kb:library:query
- **说明**: 获得文件夹详情，并拼接子文件夹数量、直属文档数量、当前用户协作等级与关注状态；可选择记录本次浏览。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 文件夹编号 |
| view | Boolean | 否 | @RequestParam(defaultValue = "false") | 是否记录本次浏览 |

**响应**: CommonResult&lt;PmsKnowledgeFolderRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文件夹编号 |
| libraryId | Long | 知识库编号 |
| permissionId | Long | 协作权限编号 |
| currentUserLevel | Integer | 当前用户协作等级 |
| parentId | Long | 父文件夹编号 |
| title | String | 文件夹标题 |
| childFolderCount | Integer | 直属子文件夹数量 |
| documentCount | Integer | 直属文档数量 |
| status | Integer | 状态 |
| favoriteStatus | Boolean | 当前用户是否已关注 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 校验文件夹存在且不在回收站；校验所属知识库可读、当前用户对该文件夹内容有读取权限。
2. view=true 时创建浏览记录（对象类型为文件夹）。
3. 查询该知识库下当前用户可读的全部文件夹和文档，统计该文件夹的直属子文件夹数量与直属文档数量。
4. 拼接当前用户协作等级与关注状态返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_006 | 知识库文件夹不存在 |
| 1_053_130_071 | 无权访问该知识内容 |

### 2.6 获得知识库目录树

- **路径**: GET /pms/kb/folder/tree
- **权限**: pms:kb:library:query
- **说明**: 一次性返回指定知识库下当前用户可见的文件夹与文档目录树（含子文档嵌套），并附当前用户的编辑/管理状态。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| libraryId | Long | 是 | @RequestParam(required) | 知识库编号 |

**响应**: CommonResult&lt;PmsKnowledgeTreeRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| libraryId | Long | 知识库编号 |
| writeStatus | Boolean | 当前用户是否可编辑该知识库 |
| manageStatus | Boolean | 当前用户是否可管理该知识库目录结构 |
| folders | List&lt;FolderNode&gt; | 根文件夹列表 |
| folders[].id | Long | 文件夹编号 |
| folders[].permissionId | Long | 协作权限编号 |
| folders[].currentUserLevel | Integer | 当前用户协作等级 |
| folders[].parentId | Long | 父文件夹编号 |
| folders[].title | String | 文件夹标题 |
| folders[].children | List&lt;FolderNode&gt; | 子文件夹列表（递归嵌套） |
| folders[].documents | List&lt;DocumentNode&gt; | 文件夹下的文档列表 |
| documents | List&lt;DocumentNode&gt; | 根文档列表 |
| documents[].id | Long | 文档编号 |
| documents[].permissionId | Long | 协作权限编号 |
| documents[].currentUserLevel | Integer | 当前用户协作等级 |
| documents[].parentId | Long | 父文档编号 |
| documents[].title | String | 文档标题 |
| documents[].type | Integer | 文档类型 |
| documents[].fileType | String | 文件类型 |
| documents[].children | List&lt;DocumentNode&gt; | 子文档列表（递归嵌套） |

**业务逻辑**:
1. 查询该知识库下当前用户可读的全部文件夹（按内容权限过滤）。
2. 查询该知识库下当前用户可读的全部正常文档：先按内容权限过滤，再按父文档可见性裁剪——父文档不可见时整条子文档分支均不可见（从根文档逐层 BFS 标记可见集合）。
3. 批量判断当前用户是否可编辑（isLibraryWritable）、可管理目录结构（isLibraryAdmin）。
4. 批量计算全部节点权限编号对应的当前用户协作等级。
5. 组装文档树：子文档挂到父文档节点，无父文档时挂到所属文件夹节点，均无时挂到根文档列表。
6. 组装文件夹树：按父文件夹逐级挂载，最终返回根文件夹列表与根文档列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_070 | 知识内容协作权限不存在 |
| 1_053_130_071 | 无权访问该知识内容 |

## 3. 文档标签（/pms/kb/document-label）

### 3.1 创建文档标签

- **路径**: POST /pms/kb/document-label/create
- **权限**: pms:kb:library:update
- **说明**: 创建一条知识库文档标签（名称 + 颜色），名称与颜色会去除首尾空白。

**请求参数 (PmsKnowledgeDocumentLabelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 文档标签编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max = 255) | 标签名称 |
| color | String | 是 | @NotBlank、@Size(max = 20) | 标签颜色（如 #409EFF） |

**响应**: CommonResult&lt;Long&gt; —— 新创建的标签编号。

**业务逻辑**:
1. 将请求 VO 转换为 DO，名称与颜色 trim 后插入标签表。
2. 返回新标签编号。

**错误码**: 该端点无专属错误码。

### 3.2 修改文档标签

- **路径**: PUT /pms/kb/document-label/update
- **权限**: pms:kb:library:update
- **说明**: 修改文档标签的名称与颜色。

**请求参数 (PmsKnowledgeDocumentLabelSaveReqVO)**: 同 3.1，其中 id 为必传的标签编号。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档标签存在（否则抛 1_053_130_030）。
2. 名称与颜色 trim 后更新标签记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_030 | 知识库文档标签不存在 |

### 3.3 删除文档标签

- **路径**: DELETE /pms/kb/document-label/delete
- **权限**: pms:kb:library:delete
- **说明**: 删除指定文档标签（物理删除）。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 文档标签编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档标签存在。
2. 删除标签记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_030 | 知识库文档标签不存在 |

### 3.4 获得文档标签详情

- **路径**: GET /pms/kb/document-label/get
- **权限**: pms:kb:library:query
- **说明**: 获得指定文档标签的详情。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 文档标签编号 |

**响应**: CommonResult&lt;PmsKnowledgeDocumentLabelRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文档标签编号 |
| name | String | 标签名称 |
| color | String | 标签颜色 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询标签并转换为 RespVO 返回（不存在时返回 null 数据）。

### 3.5 获得文档标签列表

- **路径**: GET /pms/kb/document-label/list
- **权限**: pms:kb:library:query
- **说明**: 获得全部文档标签列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;PmsKnowledgeDocumentLabelRespVO&gt;&gt; —— 字段同 3.4。

**业务逻辑**: 1. 查询全部标签记录并批量转换为 RespVO 列表返回。

### 3.6 获得指定标签的文档分页

- **路径**: GET /pms/kb/document-label/document-page
- **权限**: pms:kb:library:query
- **说明**: 按标签分页查询文档，仅返回当前用户可读知识库中可读的非回收站文档。

**请求参数 (PmsKnowledgeDocumentLabelPageReqVO，继承 PageParam 分页参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| labelId | Long | 是 | @NotNull | 文档标签编号 |

**响应**: CommonResult&lt;PageResult&lt;PmsKnowledgeDocumentRespVO&gt;&gt; —— 字段同 1.5（content 恒为空，另含 libraryName、creatorUserName；无 contentSummary/点赞等互动字段）。

**业务逻辑**:
1. 校验文档标签存在。
2. 查询当前用户可读的知识库编号列表；为空则返回空分页。
3. 批量计算当前用户在这些知识库下可读的内容权限编号集合；为空则返回空分页。
4. 按标签、可读知识库与可读权限对非回收站状态文档分页查询。
5. 拼接返回 VO：清空正文，批量拼接知识库名称与创建人姓名。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_030 | 知识库文档标签不存在 |

## 4. 知识内容协作权限（/pms/kb/content-permission）

### 4.1 获得知识内容协作权限

- **路径**: GET /pms/kb/content-permission/get
- **权限**: pms:kb:library:query
- **说明**: 获得文件夹/文档对应的协作权限配置，含公开等级、协作者列表（用户昵称、部门名称）及当前用户协作等级。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 协作权限编号 |

**响应**: CommonResult&lt;PmsKnowledgeContentPermissionRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 协作权限编号 |
| libraryId | Long | 知识库编号 |
| openStatus | Boolean | 是否公开 |
| openLevel | Integer | 公开协作等级 |
| creatorUserId | Long | 创建人用户编号 |
| currentUserLevel | Integer | 当前用户协作等级 |
| members | List&lt;Member&gt; | 协作者列表 |
| members[].id | Long | 协作者编号 |
| members[].userId | Long | 用户编号 |
| members[].userName | String | 用户昵称 |
| members[].deptId | Long | 部门编号 |
| members[].deptName | String | 部门名称 |
| members[].level | Integer | 协作等级 |

**业务逻辑**:
1. 校验协作权限存在（否则抛 1_053_130_070）。
2. 校验当前用户可读取该权限所属知识库。
3. 校验当前用户对该内容有读取权限，并计算当前用户协作等级。
4. 查询协作者列表，批量拼接用户昵称与部门名称后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_070 | 知识内容协作权限不存在 |
| 1_053_130_071 | 无权访问该知识内容 |

### 4.2 更新知识内容协作权限

- **路径**: PUT /pms/kb/content-permission/update
- **权限**: pms:kb:library:update
- **说明**: 更新内容的公开状态、公开协作等级，并整体重建协作者列表；内容创建人始终保留管理权限。

**请求参数 (PmsKnowledgeContentPermissionUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 协作权限编号 |
| openStatus | Boolean | 是 | @NotNull | 是否公开 |
| openLevel | Integer | 是 | @NotNull、@InEnum(PmsKnowledgeContentLevelEnum) | 公开协作等级 |
| members | List&lt;Member&gt; | 是 | @Valid、@NotNull | 协作者列表 |
| members[].userId | Long | 否 | 与 deptId 二选一 | 用户编号 |
| members[].deptId | Long | 否 | 与 userId 二选一 | 部门编号 |
| members[].level | Integer | 是 | @NotNull、@InEnum(PmsKnowledgeContentLevelEnum) | 协作等级 |

校验规则：Member 内置 @AssertTrue 校验——协作者必须且只能选择用户或部门其一。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验协作权限存在、当前用户可访问其知识库。
2. 校验当前用户对该内容拥有管理权限（协作等级为管理员）。
3. 校验协作者唯一：用户编号与部门编号去重后的数量之和必须等于协作者总数，否则抛错。
4. 校验协作者不能包含内容创建人（创建人固定拥有管理权限）。
5. 校验用户协作者、部门协作者均真实存在（调用 AdminUserApi / DeptApi）。
6. 私有知识库额外校验：用户与部门协作者必须均为该知识库成员。
7. 更新公开状态与公开协作等级，删除原有协作者后重建：以内容创建人（管理权限）为首，插入请求中的全部协作者。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_001 | 无权访问该知识库 |
| 1_053_130_070 | 知识内容协作权限不存在 |
| 1_053_130_072 | 无权编辑该知识内容 |
| 1_053_130_074 | 知识内容协作者数据无效 |
