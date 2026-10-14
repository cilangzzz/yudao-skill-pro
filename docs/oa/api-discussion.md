# OA 讨论区接口 (OaDiscussionController / OaDiscussionLikeController / OaDiscussionReplyController / OaDiscussionVoteController)

> 提供企业内 OA 讨论区的完整能力：讨论（公告/讨论/投票三种类型）发布与管理、回复（楼中楼）、点赞（讨论与主回复）、投票参与，以及各维度的统计数据拼接。

## 接口路径前缀

- `/oa/discussion`（Controller: OaDiscussionController，讨论管理）
- `/oa/discussion-like`（Controller: OaDiscussionLikeController，讨论点赞）
- `/oa/discussion-reply`（Controller: OaDiscussionReplyController，讨论回复）
- `/oa/discussion-vote`（Controller: OaDiscussionVoteController，讨论投票）

讨论类型枚举（OaDiscussionTypeEnum）：`1` 公告、`2` 讨论、`3` 投票。

---

## 1. 讨论管理（OaDiscussionController）

### 1.1 创建讨论

- **路径**: POST /oa/discussion/create
- **权限**: oa:discussion:create
- **说明**: 创建一条公告/讨论/投票，投票类型时同时创建投票选项。

**请求参数 (OaDiscussionSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 讨论编号，新增时不传 |
| type | Integer | 是 | @NotNull、@InEnum(OaDiscussionTypeEnum) | 讨论类型：1 公告、2 讨论、3 投票 |
| title | String | 是 | @NotBlank、@Size(max = 255) | 标题 |
| content | String | 否 | - | 内容 |
| fileUrls | List\<String\> | 否 | 元素 @NotBlank、@Size(max = 512) | 附件地址列表 |
| voteMultiple | Boolean | 见下 | @AssertTrue 类级校验 | 投票是否允许多选 |
| voteStartTime | LocalDateTime | 见下 | @AssertTrue 类级校验 | 投票开始时间 |
| voteEndTime | LocalDateTime | 见下 | @AssertTrue 类级校验 | 投票结束时间 |
| voteOptions | List\<OaVoteOptionSaveReqVO\> | 见下 | @Valid，元素 @NotNull | 投票选项列表 |

类级 @AssertTrue 校验：当 type 为投票（3）时，voteMultiple、voteStartTime、voteEndTime 必填，voteEndTime 必须晚于 voteStartTime，且至少需要 2 个投票选项。

OaVoteOptionSaveReqVO 字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| title | String | 是 | @NotBlank、@Size(max = 200) | 选项标题 |
| color | String | 否 | @Size(max = 20) | 选项颜色，如 #409EFF |
| sort | Integer | 是 | @NotNull | 显示顺序 |

**响应**: CommonResult\<Long\>，讨论编号。

**业务逻辑**:
1. 将请求 VO 转为 OaDiscussionDO，设置发布人为当前登录用户、访问次数为 0。
2. 非投票类型时清空投票配置字段（voteMultiple/voteStartTime/voteEndTime），新增时不保存。
3. 插入讨论记录。
4. 调用投票服务批量新增投票选项（选项列表为空时跳过），选项关联讨论编号。

### 1.2 更新讨论

- **路径**: PUT /oa/discussion/update
- **权限**: oa:discussion:update
- **说明**: 更新本人发布的讨论；发布后不允许修改类型及已有投票的基础配置。

**请求参数 (OaDiscussionSaveReqVO)**: 同 1.1，其中 id 必传（用于定位更新记录）。

**响应**: CommonResult\<Boolean\>，更新成功。

**业务逻辑**:
1. 校验讨论存在，且属于当前登录用户（否则抛 DISCUSSION_NOT_EXISTS / DISCUSSION_ACCESS_DENIED）。
2. 投票类型讨论校验：新的投票结束时间不能为空，且必须晚于原投票开始时间，否则抛 DISCUSSION_VOTE_INVALID。
3. 更新讨论，userId 与 type 置空（不允许修改发布人和类型）。
4. 投票类型讨论的 voteMultiple 与 voteStartTime 置空（不允许修改已有投票的基础配置）；非投票类型清空投票配置字段（修改时不覆盖原字段）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |
| 1_054_150_001 | 只能修改或删除自己发布的讨论 |
| 1_054_150_004 | 投票配置无效 |

### 1.3 删除讨论

- **路径**: DELETE /oa/discussion/delete
- **权限**: oa:discussion:delete
- **说明**: 删除本人发布的讨论（超级管理员可删除任意讨论），并级联清理回复、点赞、投票数据。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 讨论编号 |

**响应**: CommonResult\<Boolean\>，删除成功。

**业务逻辑**:
1. 校验讨论存在，且当前用户是发布人或超级管理员。
2. 删除讨论下全部回复及回复点赞。
3. 删除讨论点赞记录。
4. 删除投票记录及投票选项。
5. 删除讨论本身。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |
| 1_054_150_001 | 只能修改或删除自己发布的讨论 |

### 1.4 获得讨论详情

- **路径**: GET /oa/discussion/get
- **权限**: oa:discussion:query
- **说明**: 获得讨论详情，可按需记录本次访问（访问次数 +1）。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 讨论编号 |
| visit | Boolean | 否 | 默认 false | 是否记录本次访问 |

**响应**: CommonResult\<OaDiscussionRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 讨论编号 |
| userId | Long | 发布人用户编号 |
| userName | String | 发布人用户昵称 |
| type | Integer | 讨论类型：1 公告、2 讨论、3 投票 |
| title | String | 标题 |
| content | String | 内容 |
| fileUrls | List\<String\> | 附件地址列表 |
| visitCount | Integer | 访问次数 |
| replyCount | Integer | 回复数 |
| likeCount | Integer | 点赞数 |
| liked | Boolean | 当前用户是否已点赞 |
| likeUserNames | List\<String\> | 点赞人用户昵称列表 |
| voteMultiple | Boolean | 投票是否允许多选 |
| voteStartTime | LocalDateTime | 投票开始时间 |
| voteEndTime | LocalDateTime | 投票结束时间 |
| voteOptions | List\<OaVoteOptionRespVO\> | 投票选项列表，结构见 4.1 节末尾 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验讨论存在。
2. visit 为 true 时，访问次数 +1 持久化，并在返回值中同步 +1。
3. 拼接展示字段：发布人昵称、回复数、点赞数、当前用户是否已点赞、点赞人昵称列表、投票选项列表（各选项的投票数、当前用户是否已选、投票人昵称列表）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |

### 1.5 获得讨论分页

- **路径**: GET /oa/discussion/page
- **权限**: oa:discussion:query
- **说明**: 分页查询全部讨论，并批量拼接统计与展示字段。

**请求参数 (OaDiscussionPageReqVO，继承 SortablePageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码，默认 1 |
| pageSize | Integer | 否 | 分页参数 | 每页条数，默认 10 |
| sortingFields | List | 否 | - | 排序字段，缺省时后端指定默认排序 |
| title | String | 否 | - | 标题，模糊匹配 |
| type | Integer | 否 | @InEnum(OaDiscussionTypeEnum) | 讨论类型 |
| userId | Long | 否 | - | 发布人用户编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult\<PageResult\<OaDiscussionRespVO\>\>，元素结构同 1.4。

**业务逻辑**:
1. 未指定排序时，默认按 type 升序、updateTime 降序排序。
2. 按条件分页查询讨论。
3. 批量查询各讨论的回复、点赞、投票选项与投票记录，避免逐条查询数据库。
4. 批量查询发布人、点赞人、投票人的用户昵称。
5. 拼接每条讨论的回复数、点赞数、是否已赞、点赞人昵称列表、投票选项统计。

### 1.6 获得管理范围内的讨论分页

- **路径**: GET /oa/discussion/manage-page
- **权限**: oa:discussion:query
- **说明**: "我的讨论"管理分页，普通用户只能管理本人发布的讨论。

**请求参数**: 同 1.5（OaDiscussionPageReqVO）。

**响应**: CommonResult\<PageResult\<OaDiscussionRespVO\>\>，元素结构同 1.4。

**业务逻辑**:
1. 判断当前用户是否具有超级管理员角色；非超级管理员时强制将查询条件 userId 覆盖为当前登录用户（不接受请求指定的其他发布人）。
2. 复用讨论分页查询（超级管理员保留按发布人筛选的能力）。

---

## 2. 讨论点赞（OaDiscussionLikeController）

### 2.1 点赞讨论或主回复

- **路径**: POST /oa/discussion-like/create
- **权限**: 已认证（无 @PreAuthorize 权限标识）
- **说明**: 对讨论或主回复点赞，重复点赞幂等处理。

**请求参数 (OaDiscussionLikeReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| discussionId | Long | 二选一 | @AssertTrue 类级校验 | 讨论编号，与回复编号必须且只能填写一个 |
| replyId | Long | 二选一 | @AssertTrue 类级校验 | 回复编号，与讨论编号必须且只能填写一个 |

**响应**: CommonResult\<Boolean\>，点赞成功。

**业务逻辑**:
1. 校验点赞对象存在：discussionId 非空时校验讨论存在；否则校验回复存在，且必须是主回复（parentId = 0），楼内子回复不允许点赞，否则抛 DISCUSSION_LIKE_TARGET_INVALID。
2. 查询当前用户对该目标的点赞记录，已点赞时直接返回（幂等，避免重试重复新增）。
3. 新增点赞记录（讨论编号/回复编号 + 用户编号）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |
| 1_054_150_002 | 讨论回复不存在 |
| 1_054_150_009 | 只能点赞讨论或主回复 |

### 2.2 取消点赞讨论或主回复

- **路径**: DELETE /oa/discussion-like/delete
- **权限**: 已认证（无 @PreAuthorize 权限标识）
- **说明**: 取消当前用户对讨论或主回复的点赞。

**请求参数 (OaDiscussionLikeReqVO)**: 同 2.1（通过 query 参数绑定）。

**响应**: CommonResult\<Boolean\>，取消成功。

**业务逻辑**:
1. 查询当前用户对该目标的点赞记录，不存在时直接返回。
2. 删除该条点赞记录。

---

## 3. 讨论回复（OaDiscussionReplyController）

### 3.1 创建讨论回复

- **路径**: POST /oa/discussion-reply/create
- **权限**: 已认证（无 @PreAuthorize 权限标识）
- **说明**: 在讨论下发布根回复或楼内子回复。

**请求参数 (OaDiscussionReplyCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| discussionId | Long | 是 | @NotNull | 讨论编号 |
| parentId | Long | 否 | - | 父回复编号，空或 0 表示根回复 |
| content | String | 是 | @NotBlank、@AssertTrue | 回复内容；楼内评论（parentId 非空且非 0）不能超过 255 个字符 |

**响应**: CommonResult\<Long\>，回复编号。

**业务逻辑**:
1. 校验讨论存在。
2. parentId 为空时视为根回复（parentId = 0）。
3. 有父回复时校验父回复存在，且属于当前讨论（否则抛 DISCUSSION_REPLY_NOT_EXISTS），被回复人取父回复的发布人。
4. 新增回复记录（发布人为当前登录用户）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |
| 1_054_150_002 | 讨论回复不存在 |

### 3.2 删除讨论回复

- **路径**: DELETE /oa/discussion-reply/delete
- **权限**: 已认证（无 @PreAuthorize 权限标识）
- **说明**: 删除回复及其全部子回复，仅讨论发布人或超级管理员可操作。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 回复编号 |

**响应**: CommonResult\<Boolean\>，删除成功。

**业务逻辑**:
1. 校验回复存在、所属讨论存在。
2. 校验当前用户是讨论发布人或超级管理员（注意：不是回复发布人），否则抛 DISCUSSION_REPLY_ACCESS_DENIED。
3. 基于讨论下的全部回复，通过 BFS 收集当前回复及其全部子回复编号（每个回复最多入队一次，避免脏数据形成循环关联）。
4. 删除这些回复的点赞记录。
5. 批量删除当前回复及其全部子回复。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |
| 1_054_150_002 | 讨论回复不存在 |
| 1_054_150_003 | 只有讨论发布人或超级管理员可以删除回复 |

### 3.3 获得讨论回复分页

- **路径**: GET /oa/discussion-reply/page
- **权限**: oa:discussion:query
- **说明**: 按楼层（主回复）分页，子回复挂载在所属楼层的 children 下。

**请求参数 (OaDiscussionReplyPageReqVO，继承 SortablePageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码，默认 1 |
| pageSize | Integer | 否 | 分页参数 | 每页条数，默认 10 |
| sortingFields | List | 否 | - | 排序字段，缺省时按创建时间升序 |
| discussionId | Long | 是 | @NotNull | 讨论编号 |
| userId | Long | 否 | - | 回复人用户编号 |

**响应**: CommonResult\<PageResult\<OaDiscussionReplyRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 回复编号 |
| discussionId | Long | 讨论编号 |
| userId | Long | 回复人用户编号 |
| userName | String | 回复人用户昵称 |
| parentId | Long | 父回复编号，0 表示根回复 |
| replyUserId | Long | 被回复人用户编号 |
| replyUserName | String | 被回复人用户昵称 |
| content | String | 回复内容 |
| likeCount | Integer | 点赞数 |
| liked | Boolean | 当前用户是否已点赞 |
| likeUserNames | List\<String\> | 点赞人用户昵称列表 |
| createTime | LocalDateTime | 创建时间 |
| children | List\<OaDiscussionReplyRespVO\> | 楼层内的子回复（递归结构） |

**业务逻辑**:
1. 校验讨论存在。
2. 仅对主回复分页（子回复随所属楼层展示），未指定排序时按创建时间升序。
3. 批量查询当前页楼层内的全部子回复（后代）。
4. 批量拼接回复人/被回复人昵称，以及主回复的点赞数、是否已赞、点赞人昵称列表。
5. 按 parentId 父子关系将子回复组织进各楼层的 children，返回主回复分页。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |

---

## 4. 讨论投票（OaDiscussionVoteController）

### 4.1 参与讨论投票

- **路径**: POST /oa/discussion-vote/create
- **权限**: 已认证（无 @PreAuthorize 权限标识）
- **说明**: 对投票类型讨论提交选项；单选一次性提交，多选可分次追加。

**请求参数 (OaDiscussionVoteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| discussionId | Long | 是 | @NotNull | 讨论编号 |
| optionIds | List\<Long\> | 是 | @NotEmpty，元素 @NotNull | 投票选项编号列表 |

**响应**: CommonResult\<Boolean\>，投票成功。

**业务逻辑**:
1. 校验讨论存在。
2. 校验讨论类型为投票，否则抛 DISCUSSION_VOTE_INVALID。
3. 校验当前时间在投票开始与结束时间之间，否则抛 DISCUSSION_VOTE_EXPIRED。
4. 校验选项数量：单选投票（voteMultiple = false）只能选择一个选项，否则抛 DISCUSSION_VOTE_INVALID。
5. 校验全部选项属于当前讨论，否则抛 DISCUSSION_VOTE_OPTION_NOT_EXISTS。
6. 校验重复投票：单选只能提交一次；多选可分次追加，但同一选项不能重复提交，否则抛 DISCUSSION_VOTE_DUPLICATE。
7. 批量新增投票记录（讨论编号 + 选项编号 + 用户编号）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_150_000 | 讨论不存在 |
| 1_054_150_004 | 投票配置无效 |
| 1_054_150_005 | 投票未开始或已结束 |
| 1_054_150_006 | 已经参与过该投票 |
| 1_054_150_007 | 投票选项不存在 |

投票选项响应结构（OaVoteOptionRespVO，用于 1.4/1.5 的 voteOptions 字段）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 投票选项编号 |
| title | String | 选项标题 |
| color | String | 选项颜色 |
| sort | Integer | 显示顺序 |
| voteCount | Integer | 投票数 |
| voted | Boolean | 当前用户是否已选择 |
| voterUserNames | List\<String\> | 投票人用户昵称列表 |
