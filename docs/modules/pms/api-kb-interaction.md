# 知识库互动接口 (PmsKnowledgeDocumentCommentController / PmsKnowledgeDocumentLikeController / PmsKnowledgeDocumentShareController / PmsKnowledgeFavoriteController / PmsKnowledgeViewRecordController)

> 提供 PMS 知识库的互动能力：文档评论（两级回复）、文档点赞、内部分享与令牌公开分享、知识对象关注（收藏）、最近浏览记录。所有写操作与查询都由 Service 层按当前登录用户校验「知识库成员 / 内容协作权限」的可读或可写权限。

## 接口路径前缀

- /pms/kb/document-comment  (Controller: PmsKnowledgeDocumentCommentController)
- /pms/kb/document-like  (Controller: PmsKnowledgeDocumentLikeController)
- /pms/kb/document-share  (Controller: PmsKnowledgeDocumentShareController)
- /pms/kb/favorite  (Controller: PmsKnowledgeFavoriteController)
- /pms/kb/view-record  (Controller: PmsKnowledgeViewRecordController)

> 本域还包含两个无端点的支撑 Service：`PmsKnowledgeInteractionTargetService`（统一的知识对象可读校验与展示字段组装）与 `PmsKnowledgeFolderReadService`（文件夹可读校验），被点赞、关注、浏览记录共同复用。

## 1. 文档评论（PmsKnowledgeDocumentCommentController，/pms/kb/document-comment）

### 1.1 创建知识库文档评论

- **路径**: POST /pms/kb/document-comment/create
- **权限**: pms:kb:library:query
- **说明**: 在富文本文档下发表评论或回复他人评论，评论人取当前登录用户。

**请求参数 (PmsKnowledgeDocumentCommentSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @NotNull | 文档编号 |
| mainId | Long | 否 | - | 主评论编号（不传或 0 表示主评论；回复时传主评论编号） |
| replyUserId | Long | 否 | - | 回复对象用户编号 |
| content | String | 是 | @NotBlank、@Size(max = 2000) | 评论内容，不超过 2000 字符 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的评论编号。

**业务逻辑**:
1. 校验文档可评论：通过 documentService.getDocument(documentId, userId) 校验当前用户可读该文档，且文档类型必须是富文本（PmsKnowledgeDocumentTypeEnum.RICH_TEXT），否则抛出「只有富文本文档支持评论」。
2. 规范回复关系：mainId 为空时置为根标记 0；mainId 非 0 时校验主评论存在，且主评论必须属于同一文档且自身是主评论，否则抛出「回复的评论与文档不匹配」。
3. 将请求 VO 转换为 PmsKnowledgeDocumentCommentDO，设置评论人 userId 与规范后的 mainId，插入评论表并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_080 | 知识库文档评论不存在 |
| 1_053_130_081 | 回复的评论与文档不匹配 |
| 1_053_130_083 | 只有富文本文档支持评论 |
| 1_053_130_071 | 无权访问该知识内容（文档不可读时由内容权限校验抛出） |

### 1.2 删除知识库文档评论

- **路径**: DELETE /pms/kb/document-comment/delete
- **权限**: pms:kb:library:query
- **说明**: 删除自己的评论；删除主评论时级联删除其全部回复。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 评论编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验评论存在，不存在抛出「知识库文档评论不存在」。
2. 校验评论所属文档仍可评论（文档可读且类型为富文本）。
3. 校验评论属于当前登录用户，否则抛出「只能删除自己的评论」。
4. 事务内：若被删的是主评论（mainId = 0），先按 mainId 删除其全部回复，再删除主评论本身。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_080 | 知识库文档评论不存在 |
| 1_053_130_082 | 只能删除自己的评论 |
| 1_053_130_083 | 只有富文本文档支持评论 |
| 1_053_130_071 | 无权访问该知识内容（文档不可读时由内容权限校验抛出） |

### 1.3 获得知识库文档评论列表

- **路径**: GET /pms/kb/document-comment/list
- **权限**: pms:kb:library:query
- **说明**: 获得指定文档的全部评论，主评论携带 children 回复树，并批量填充评论人/回复人昵称。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @RequestParam(required) | 文档编号 |

**响应**: CommonResult&lt;List&lt;PmsKnowledgeDocumentCommentRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 评论编号 |
| documentId | Long | 文档编号 |
| userId | Long | 评论人用户编号 |
| userName | String | 评论人昵称（批量查询 AdminUserApi 填充） |
| mainId | Long | 主评论编号（0 表示主评论） |
| replyUserId | Long | 回复对象用户编号 |
| replyUserName | String | 回复对象昵称 |
| content | String | 评论内容 |
| createTime | LocalDateTime | 创建时间 |
| children | List&lt;PmsKnowledgeDocumentCommentRespVO&gt; | 该主评论下的回复列表（主评论才填充） |

**业务逻辑**:
1. 校验文档可评论（当前用户可读且类型为富文本）。
2. 查询该文档下全部评论与回复。
3. 批量查询评论人与回复对象用户信息（AdminUserApi.getUserMap），填充 userName / replyUserName 昵称。
4. 按主评论组织两级结构：mainId = 0 的评论作为根节点，其余回复按 mainId 挂到对应主评论的 children 列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_083 | 只有富文本文档支持评论 |
| 1_053_130_071 | 无权访问该知识内容（文档不可读时由内容权限校验抛出） |

## 2. 文档点赞（PmsKnowledgeDocumentLikeController，/pms/kb/document-like）

### 2.1 点赞文档

- **路径**: POST /pms/kb/document-like/create
- **权限**: pms:kb:library:query
- **说明**: 当前登录用户对指定文档点赞，重复请求幂等。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @RequestParam(required) | 文档编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 通过 interactionTargetService.validateTargetReadable(DOCUMENT, documentId, userId) 校验文档可读（同时校验文档类型与 DOCUMENT 匹配）。
2. 查询当前用户对该文档的点赞关系，已存在则直接返回（幂等）。
3. 不存在时插入 PmsKnowledgeDocumentLikeDO（documentId + userId）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_050 | 知识对象不存在或类型不匹配 |
| 1_053_130_071 | 无权访问该知识内容（文档不可读时由内容权限校验抛出） |

### 2.2 取消点赞文档

- **路径**: DELETE /pms/kb/document-like/delete
- **权限**: pms:kb:library:query
- **说明**: 取消当前登录用户对指定文档的点赞，重复请求幂等。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @RequestParam(required) | 文档编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档可读（同 2.1）。
2. 查询当前用户对该文档的点赞关系，存在则删除，不存在则不做任何处理（幂等）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_050 | 知识对象不存在或类型不匹配 |
| 1_053_130_071 | 无权访问该知识内容（文档不可读时由内容权限校验抛出） |

## 3. 文档分享（PmsKnowledgeDocumentShareController，/pms/kb/document-share）

### 3.1 开启文档分享

- **路径**: POST /pms/kb/document-share/open
- **权限**: pms:kb:library:update
- **说明**: 开启文档分享（内部成员 + 外部令牌），重新开启时生成新的外部令牌，并给内部分享成员发送站内信。

**请求参数 (PmsKnowledgeDocumentShareSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @NotNull | 文档编号 |
| shareUserIds | List&lt;Long&gt; | 否 | 元素 @NotNull | 内部分享成员用户编号列表（自动去重） |

**响应**: CommonResult&lt;PmsKnowledgeDocumentShareRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分享编号 |
| documentId | Long | 文档编号 |
| shareUserIds | List&lt;Long&gt; | 内部分享成员用户编号列表 |
| token | String | 外部查看令牌（fastSimpleUUID） |
| status | Integer | 分享状态（1 开启 / 0 关闭） |
| createTime | LocalDateTime | 创建时间 |
| closeUserId | Long | 关闭人用户编号（重新开启时清空） |
| closeTime | LocalDateTime | 关闭时间（重新开启时清空） |

**业务逻辑**:
1. 校验文档存在且状态正常（非回收/删除态），否则抛出「知识库文档不存在」。
2. 校验当前用户对该文档内容有编辑权限（validateContentPermissionWritable）。
3. 校验文档尚未开启分享：已有开启状态的分享记录则抛出「该文档已开启分享」。
4. 规范分享成员列表（LinkedHashSet 去重），并调用 AdminUserApi.validateUserList 校验用户存在且未禁用。
5. 无分享记录则新建，已有记录则通过 updateToReopen 重新开启；统一生成新的外部令牌、置为开启状态并清空关闭人/关闭时间。
6. 给全部分享成员发送站内信（模板 pms_knowledge_document_shared，参数含文档标题与分享路由 /pms/kb/document/share/{token}）；通知失败仅记录日志，不阻断分享主流程。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_060 | 该文档已开启分享 |
| 1_053_130_072 | 无权编辑该知识内容（内容编辑权限校验失败） |

### 3.2 更新文档内部分享成员

- **路径**: PUT /pms/kb/document-share/update-member-list
- **权限**: pms:kb:library:update
- **说明**: 全量更新文档的内部分享成员列表，仅对本次新增成员发送站内信。

**请求参数 (PmsKnowledgeDocumentShareUpdateMemberListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @NotNull | 文档编号 |
| shareUserIds | List&lt;Long&gt; | 否 | 元素 @NotNull | 内部分享成员用户编号列表（自动去重） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档存在且状态正常。
2. 校验当前用户对该文档内容有编辑权限。
3. 校验文档已开启分享，否则抛出「文档分享不存在或已失效」。
4. 规范并校验分享成员列表（去重 + 用户有效性）。
5. 按 share.id 全量更新内部分享成员列表。
6. 计算本次新增成员（新列表减去旧列表），仅给新增成员发送分享站内信，发送失败不阻断主流程。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_061 | 文档分享不存在或已失效 |
| 1_053_130_072 | 无权编辑该知识内容（内容编辑权限校验失败） |

### 3.3 关闭文档分享

- **路径**: PUT /pms/kb/document-share/close
- **权限**: pms:kb:library:update
- **说明**: 关闭文档分享，记录关闭人与关闭时间；外部令牌随之失效。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @RequestParam(required) | 文档编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验文档存在且状态正常。
2. 校验当前用户对该文档内容有编辑权限。
3. 校验文档已开启分享，否则抛出「文档分享不存在或已失效」。
4. 更新分享记录：状态置为关闭（DISABLE），记录 closeUserId 为当前用户、closeTime 为当前时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_061 | 文档分享不存在或已失效 |
| 1_053_130_072 | 无权编辑该知识内容（内容编辑权限校验失败） |

### 3.4 获得文档分享配置

- **路径**: GET /pms/kb/document-share/get
- **权限**: pms:kb:library:query
- **说明**: 获得文档当前仍处于开启状态的分享配置；未开启时返回 null 数据。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentId | Long | 是 | @RequestParam(required) | 文档编号 |

**响应**: CommonResult&lt;PmsKnowledgeDocumentShareRespVO&gt; —— 字段同 3.1；文档未开启分享时 data 为 null。

**业务逻辑**:
1. 校验文档存在且状态正常。
2. 校验当前用户对该文档内容有读取权限（validateContentPermissionReadable）。
3. 查询该文档的分享记录，仅当状态为开启时返回，否则返回 null。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_009 | 知识库文档不存在 |
| 1_053_130_071 | 无权访问该知识内容（内容读取权限校验失败） |

### 3.5 通过分享令牌获得文档

- **路径**: GET /pms/kb/document-share/get-by-token
- **权限**: @PermitAll（同时 @TenantIgnore，免登录免租户，供外部分享页访问）
- **说明**: 凭外部分享令牌获得文档内容；文件型文档不返回原始内容，改发文件临时预览地址。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| token | String | 是 | @NotBlank | 分享令牌 |

**响应**: CommonResult&lt;PmsKnowledgeDocumentSharePublicRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文档编号 |
| title | String | 文档标题 |
| content | String | 文档内容或文件地址（文件型文档返回 null） |
| previewUrl | String | 文件临时预览地址（仅文件型文档，经 FileApi.presignGetUrl 预签名） |
| type | Integer | 文档类型 |
| fileType | String | 文件类型（如 pdf） |
| updateTime | LocalDateTime | 文档更新时间 |

**业务逻辑**:
1. 按令牌查询分享记录，令牌不存在或分享已关闭则抛出「文档分享不存在或已失效」。
2. 查询分享对应的文档，文档不存在或状态非正常同样抛出「文档分享不存在或已失效」。
3. 富文本文档直接返回内容；文件型文档（PmsKnowledgeDocumentTypeEnum.FILE）将 content 置空，并通过 FileApi 生成预签名临时预览地址 previewUrl。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_061 | 文档分享不存在或已失效（令牌无效、分享已关闭、文档不存在或非正常状态） |

## 4. 知识关注（PmsKnowledgeFavoriteController，/pms/kb/favorite）

> 关注对象类型取值（PmsKnowledgeObjectTypeEnum）：1 知识库、2 文件夹、3 文档、4 文件。

### 4.1 关注知识对象

- **路径**: POST /pms/kb/favorite/create
- **权限**: pms:kb:library:query
- **说明**: 当前登录用户关注一个知识库/文件夹/文档/文件对象，重复关注报错。

**请求参数 (PmsKnowledgeFavoriteSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @NotNull、@InEnum(PmsKnowledgeObjectTypeEnum) | 对象类型（1 知识库 / 2 文件夹 / 3 文档 / 4 文件） |
| entityId | Long | 是 | @NotNull | 对象编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 通过 interactionTargetService.validateTargetReadable 校验关注对象可读：知识库走成员可读校验，文件夹走文件夹可读校验，文档/文件走文档可读校验并校验类型匹配；校验通过返回对象所属知识库编号。
2. 校验当前用户未关注过该对象，已关注抛出「该知识对象已关注」。
3. 插入关注记录（libraryId 取自第 1 步，userId 取当前登录用户）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_050 | 知识对象不存在或类型不匹配 |
| 1_053_130_051 | 该知识对象已关注 |
| 1_053_130_000 | 知识库不存在（对象为知识库且不存在时） |
| 1_053_130_001 | 无权访问该知识库（对象为知识库且不可读时） |
| 1_053_130_071 | 无权访问该知识内容（文件夹/文档对象不可读时） |

### 4.2 取消关注知识对象

- **路径**: DELETE /pms/kb/favorite/delete
- **权限**: pms:kb:library:query
- **说明**: 取消当前登录用户对指定对象的关注，未关注时静默处理。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @RequestParam(required)、@InEnum(PmsKnowledgeObjectTypeEnum) | 对象类型 |
| entityId | Long | 是 | @RequestParam(required) | 对象编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 按「当前用户 + 对象类型 + 对象编号」查询关注关系。
2. 存在则删除该关注记录，不存在则不做任何处理（幂等）。

### 4.3 获得我的关注分页

- **路径**: GET /pms/kb/favorite/page
- **权限**: pms:kb:library:query
- **说明**: 分页返回当前用户全部关注对象，自动过滤已无权限或已删除的对象并填充展示字段。

**请求参数 (PmsKnowledgeFavoritePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | -（PageParam 默认值 1） | 页码 |
| pageSize | Integer | 否 | -（PageParam 默认值 10） | 每页条数 |
| type | Integer | 否 | @InEnum(PmsKnowledgeObjectTypeEnum) | 对象类型筛选 |

**响应**: CommonResult&lt;PageResult&lt;PmsKnowledgeInteractionItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 关注记录编号 |
| type | Integer | 对象类型 |
| entityId | Long | 对象编号 |
| libraryId | Long | 知识库编号 |
| libraryName | String | 知识库名称 |
| name | String | 对象名称（知识库名/文件夹标题/文档标题） |
| description | String | 知识库简介（仅知识库对象） |
| folderId | Long | 文件夹编号（文件夹/文档对象） |
| documentId | Long | 文档编号（文档/文件对象） |
| fileType | String | 文件类型 |
| fileSize | Long | 文件大小，单位字节 |
| targetUpdateTime | LocalDateTime | 对象更新时间 |
| createTime | LocalDateTime | 关注时间 |

**业务逻辑**:
1. 查询当前用户的全部关注记录，并批量判定每个对象的可读性（getReadableItemList：批量查询知识库/文件夹/文档，计算可读知识库集合与可读内容权限集合，过滤掉知识库非正常、对象已删除/已回收、无内容读取权限的记录）。
2. 可读对象为空时直接返回空分页。
3. 将关注记录分页查询交给数据库处理（按 type 筛选、按创建时间排序、pageNo/pageSize 分页，限定在可读对象编号集合内）。
4. 按页用第 1 步批量解析好的展示对象拼装 PageResult 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_050 | 知识对象不存在或类型不匹配（type 非法时） |

### 4.4 获得知识库内我的关注列表

- **路径**: GET /pms/kb/favorite/list
- **权限**: pms:kb:library:query
- **说明**: 返回指定知识库内当前用户的全部关注对象（仅可读对象），不分页。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| libraryId | Long | 是 | @RequestParam(required) | 知识库编号 |

**响应**: CommonResult&lt;List&lt;PmsKnowledgeInteractionItemRespVO&gt;&gt; —— 字段同 4.3。

**业务逻辑**:
1. 查询指定知识库内当前用户的全部关注记录。
2. 复用统一的对象可读校验与展示字段组装（同 4.3 第 1 步），返回可读对象列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_050 | 知识对象不存在或类型不匹配 |

## 5. 最近浏览（PmsKnowledgeViewRecordController，/pms/kb/view-record）

### 5.1 获得最近浏览列表

- **路径**: GET /pms/kb/view-record/recent-list
- **权限**: pms:kb:library:query
- **说明**: 获得当前用户今天、昨天及此前 30 天的最近浏览对象，按时间分组去重；浏览记录由文档/文件夹读取链路自动写入（createViewRecord：首次浏览插入，重复浏览更新归属与最后访问时间）。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| libraryId | Long | 否 | @RequestParam(required = false) | 知识库编号；不传时查询全部可读知识库 |

**响应**: CommonResult&lt;PmsKnowledgeRecentListRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| todayItems | List&lt;PmsKnowledgeInteractionItemRespVO&gt; | 今天浏览列表（字段同 4.3 的 PmsKnowledgeInteractionItemRespVO，createTime 为浏览时间） |
| yesterdayItems | List&lt;PmsKnowledgeInteractionItemRespVO&gt; | 昨天浏览列表 |
| recent30DayItems | List&lt;PmsKnowledgeInteractionItemRespVO&gt; | 更早 30 天浏览列表 |

**业务逻辑**:
1. 指定 libraryId 时，先校验当前用户对该知识库的可读权限。
2. 查询当前用户自当天零点回溯 31 天（今天 + 昨天 + 30 天历史）以来的全部浏览记录；指定 libraryId 时过滤掉其他知识库的记录。
3. 通过 interactionTargetService.getReadableItemList 批量过滤出仍可读的对象（对象已删除/回收、知识库非正常、无内容读取权限的记录被剔除），并填充名称等展示字段。
4. 按浏览时间分组到今天 / 昨天 / 更早 30 天三个列表；同一分组内按「对象类型 + 对象编号」去重，仅保留最近一次访问。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_130_000 | 知识库不存在（指定 libraryId 且不存在时） |
| 1_053_130_001 | 无权访问该知识库（指定 libraryId 且不可读时） |
| 1_053_130_050 | 知识对象不存在或类型不匹配（浏览记录对象类型非法时） |
