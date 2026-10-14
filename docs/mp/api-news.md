# 图文草稿与发布接口 (MpDraftController / MpFreePublishController)

> 管理公众号图文草稿箱（查询/创建/更新/删除草稿）与发布能力（发布草稿、查询已发布图文、删除发布记录），数据实时读写微信公众平台接口，本地素材表仅用于封面图地址回填。

## 接口路径前缀

- `/mp/draft` (Controller: MpDraftController)
- `/mp/free-publish` (Controller: MpFreePublishController)

> 说明：草稿与发布接口不经过本地数据库持久化图文内容，而是直接调用微信 `WxMpService`（通过 `MpServiceFactory` 按账号获取实例）；封面图 `thumbUrl` 从本地素材表 `mp_material`（`MpMaterialService.getMaterialListByMediaId`）回填，解决公众号图片链接无法在后台展示的问题。请求/响应中的 `WxMpAddDraft`、`WxMpDraftArticles`、`WxMpDraftItem`、`WxMpFreePublishItem` 等均为 weixin-java-mp SDK bean，非项目自定义 VO。

## 1. 草稿管理（MpDraftController）

### 1.1 获得草稿分页

- **路径**: GET /mp/draft/page
- **权限**: mp:draft:query
- **说明**: 分页查询指定公众号草稿箱中的图文草稿，并回填封面图地址。

**请求参数 (MpDraftPageReqVO)**（继承 PageParam）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |

**响应**: CommonResult&lt;PageResult&lt;WxMpDraftItem&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| mediaId | String | 草稿素材的编号 |
| content | WxMpDraftInfo | 草稿内容，含 newsItem 列表（List&lt;WxMpDraftArticles&gt;） |
| content.newsItem[].title | String | 图文标题 |
| content.newsItem[].author | String | 作者 |
| content.newsItem[].digest | String | 摘要 |
| content.newsItem[].content | String | 图文内容（HTML） |
| content.newsItem[].contentSourceUrl | String | 原文链接（点击"阅读原文"到达） |
| content.newsItem[].thumbMediaId | String | 封面图的素材 media_id |
| content.newsItem[].showCoverPic | Integer | 是否显示封面（0/1） |
| content.newsItem[].needOpenComment | Integer | 是否允许评论（0/1） |
| content.newsItem[].onlyFansCanComment | Integer | 是否仅粉丝可评论（0/1） |
| content.newsItem[].url | String | 图文链接地址 |
| content.newsItem[].thumbUrl | String | 封面图地址（由本地素材表回填） |
| updateTime | Long | 更新时间（时间戳） |

**业务逻辑**:
1. 根据请求的 accountId 通过 `MpServiceFactory.getRequiredMpService` 获取对应公众号的 `WxMpService` 实例（找不到时断言失败）。
2. 调用微信草稿箱接口 `listDraft`，分页参数由 `PageUtils.getStart(reqVO)` 换算为 offset；微信调用失败抛出 `DRAFT_LIST_FAIL` 并附带微信错误信息。
3. 收集返回草稿中每条图文的 thumbMediaId，调用 `MpMaterialService.getMaterialListByMediaId` 批量查询本地素材记录。
4. 将本地素材的 url 回填到各图文的 thumbUrl 字段。
5. 组装 `PageResult` 返回（total 为微信端草稿总数）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_007_000 | 获得草稿列表失败，原因：{} |

### 1.2 创建草稿

- **路径**: POST /mp/draft/create
- **权限**: mp:draft:create
- **说明**: 将图文草稿提交到微信草稿箱，返回新草稿的 mediaId。

**请求参数**: 无 VO；Query 参数 accountId（Long，必填，公众号账号编号）+ Body 为 `WxMpAddDraft`（JSON）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| articles | List&lt;WxMpDraftArticles&gt; | 是 | 无 | 图文列表，元素字段见 1.3 |

**响应**: CommonResult&lt;String&gt;，返回新建草稿的 mediaId。

**业务逻辑**:
1. 根据 accountId 获取对应公众号的 `WxMpService` 实例。
2. 调用 `addDraft(draft)` 将草稿提交到微信草稿箱。
3. 返回微信生成的草稿 mediaId；微信调用失败抛出 `DRAFT_CREATE_FAIL` 并附带微信错误信息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_007_001 | 创建草稿失败，原因：{} |

### 1.3 更新草稿

- **路径**: PUT /mp/draft/update
- **权限**: mp:draft:update
- **说明**: 按 index 逐条更新草稿箱中指定草稿的图文文章。

**请求参数**: 无 VO；Query 参数 accountId（Long，必填，公众号账号编号）、mediaId（String，必填，草稿素材编号）+ Body 为 `List<WxMpDraftArticles>`（JSON 数组）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| title | String | 是 | 无 | 图文标题 |
| author | String | 否 | 无 | 作者 |
| digest | String | 否 | 无 | 图文摘要，单图文时默认取 title |
| content | String | 是 | 无 | 图文内容，支持 HTML 标签（不超过 1 万字符） |
| contentSourceUrl | String | 否 | 无 | 原文链接，需 ICP 备案 |
| thumbMediaId | String | 是 | 无 | 封面图的素材 media_id |
| showCoverPic | Integer | 否 | 无 | 是否显示封面（0/1） |
| needOpenComment | Integer | 否 | 无 | 是否允许评论（0/1） |
| onlyFansCanComment | Integer | 否 | 无 | 是否仅粉丝可评论（0/1） |
| url | String | 否 | 无 | 图文链接地址（响应时微信返回） |
| thumbUrl | String | 否 | 无 | 封面图地址（查询时由后台回填） |

**响应**: CommonResult&lt;Boolean&gt;，更新成功返回 true。

**业务逻辑**:
1. 根据 accountId 获取对应公众号的 `WxMpService` 实例。
2. 遍历请求体中的文章列表，按数组下标 i 构造 `WxMpUpdateDraft(mediaId, i, article)`，逐条调用 `updateDraft` 更新草稿中对应位置的文章。
3. 任一条更新失败抛出 `DRAFT_UPDATE_FAIL` 并附带微信错误信息；全部成功返回 true。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_007_002 | 更新草稿失败，原因：{} |

### 1.4 删除草稿

- **路径**: DELETE /mp/draft/delete
- **权限**: mp:draft:delete
- **说明**: 从微信草稿箱删除指定草稿。

**请求参数**: 无 VO；Query 参数:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | 无 | 公众号账号的编号 |
| mediaId | String | 是 | 无 | 草稿素材的编号 |

**响应**: CommonResult&lt;Boolean&gt;，删除成功返回 true。

**业务逻辑**:
1. 根据 accountId 获取对应公众号的 `WxMpService` 实例。
2. 调用 `delDraft(mediaId)` 从微信草稿箱删除草稿。
3. 微信调用失败抛出 `DRAFT_DELETE_FAIL` 并附带微信错误信息；成功返回 true。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_007_003 | 删除草稿失败，原因：{} |

## 2. 发布能力（MpFreePublishController）

### 2.1 获得已发布的图文分页

- **路径**: GET /mp/free-publish/page
- **权限**: mp:free-publish:query
- **说明**: 分页查询指定公众号已成功发布的图文列表，并回填封面图地址。

**请求参数 (MpFreePublishPageReqVO)**（继承 PageParam）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |

**响应**: CommonResult&lt;PageResult&lt;WxMpFreePublishItem&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| articleId | String | 发布记录（图文）的编号 |
| content | WxMpFreePublishInfo | 发布内容，含 newsItem 列表（List&lt;WxMpFreePublishArticles&gt;） |
| content.newsItem[].title | String | 图文标题 |
| content.newsItem[].author | String | 作者 |
| content.newsItem[].digest | String | 摘要 |
| content.newsItem[].content | String | 图文内容（HTML） |
| content.newsItem[].contentSourceUrl | String | 原文链接 |
| content.newsItem[].thumbMediaId | String | 封面图的素材 media_id |
| content.newsItem[].showCoverPic | Integer | 是否显示封面（0/1） |
| content.newsItem[].needOpenComment | Integer | 是否允许评论（0/1） |
| content.newsItem[].onlyFansCanComment | Integer | 是否仅粉丝可评论（0/1） |
| content.newsItem[].thumbUrl | String | 封面图地址（由本地素材表回填） |
| content.newsItem[].url | String | 图文链接地址 |
| content.newsItem[].isDeleted | Boolean | 该图文是否已被删除 |
| updateTime | String | 更新时间 |

**业务逻辑**:
1. 根据请求的 accountId 通过 `MpServiceFactory.getRequiredMpService` 获取对应公众号的 `WxMpService` 实例。
2. 调用微信发布能力接口 `getPublicationRecords` 获取已发布图文列表，分页参数由 `PageUtils.getStart(reqVO)` 换算；微信调用失败抛出 `FREE_PUBLISH_LIST_FAIL` 并附带微信错误信息。
3. 收集返回图文中的 thumbMediaId，调用 `MpMaterialService.getMaterialListByMediaId` 批量查询本地素材记录。
4. 将本地素材的 url 回填到各图文的 thumbUrl 字段。
5. 组装 `PageResult` 返回（total 为微信端发布记录总数）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_006_000 | 获得已成功发布列表失败，原因：{} |

### 2.2 发布草稿

- **路径**: POST /mp/free-publish/submit
- **权限**: mp:free-publish:submit
- **说明**: 将草稿箱中指定草稿提交发布，微信异步处理，返回 publishId。

**请求参数**: 无 VO；Query 参数:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | 无 | 公众号账号的编号 |
| mediaId | String | 是 | 无 | 要发布的草稿的 media_id |

**响应**: CommonResult&lt;String&gt;，返回发布任务 id（publishId）。

**业务逻辑**:
1. 根据 accountId 获取对应公众号的 `WxMpService` 实例。
2. 调用 `submit(mediaId)` 将指定草稿提交发布。
3. 返回微信生成的 publishId；微信调用失败抛出 `FREE_PUBLISH_SUBMIT_FAIL` 并附带微信错误信息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_006_001 | 提交发布失败，原因：{} |

### 2.3 删除发布记录

- **路径**: DELETE /mp/free-publish/delete
- **权限**: mp:free-publish:delete
- **说明**: 删除指定的已发布图文记录（从公众号后台与主页下线该图文）。

**请求参数**: 无 VO；Query 参数:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | 无 | 公众号账号的编号 |
| articleId | String | 是 | 无 | 发布记录的编号 |

**响应**: CommonResult&lt;Boolean&gt;，删除成功返回 true。

**业务逻辑**:
1. 根据 accountId 获取对应公众号的 `WxMpService` 实例。
2. 调用 `deletePushAllArticle(articleId)` 删除该发布记录。
3. 微信调用失败抛出 `FREE_PUBLISH_DELETE_FAIL` 并附带微信错误信息；成功返回 true。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_006_002 | 删除发布失败，原因：{} |
