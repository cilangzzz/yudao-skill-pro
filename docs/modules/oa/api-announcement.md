# OA 公告接口 (OaAnnouncementController)

> OA 公告管理：发布人向下属发布/更新/删除公告，接收人查看、已读、移除收到的公告并逐级转发，公告分为"我发布的"与"我收到的"两个视角。

## 接口路径前缀

/oa/announcement  (Controller: OaAnnouncementController)

## 1. 我发布的

### 1.1 创建公告

- **路径**: POST /oa/announcement/create
- **权限**: oa:announcement:create
- **说明**: 创建公告，自动将当前发布人负责部门及其子部门下的用户（下属）作为公告接收人。

**请求参数 (OaAnnouncementSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 公告编号（新增时不传） |
| type | Integer | 是 | @NotNull、@InEnum(OaAnnouncementTypeEnum) | 公告类型：1 公告、2 通知、3 投票 |
| priority | Integer | 是 | @NotNull、@InEnum(OaPriorityEnum) | 优先级：1 一般、2 重要、3 紧急 |
| title | String | 是 | @NotBlank、@Size(max=255) | 公告标题 |
| content | String | 否 | - | 公告内容 |
| url | String | 否 | @Size(max=512) | 相关链接 |
| top | Boolean | 是 | @NotNull | 是否置顶 |

**响应**: CommonResult&lt;Long&gt; —— 公告编号。

**业务逻辑**:
1. 查询发布人（当前登录用户）负责部门及其子部门下的用户列表，作为公告接收人。
2. 将请求 VO 转换为 DO，插入公告表。
3. 批量新增公告接收关系（每个接收人初始未读），接收人在公告列表查看，不额外发送站内信。
4. 返回新公告的编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_001 | 无权操作该公告 |

### 1.2 更新公告

- **路径**: PUT /oa/announcement/update
- **权限**: oa:announcement:update
- **说明**: 更新自己发布的公告，仅允许发布人本人操作。

**请求参数 (OaAnnouncementSaveReqVO)**: 同 [1.1 创建公告](#11-创建公告)，其中 `id` 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验公告存在且 creator 为当前登录用户（否则抛出无权操作错误）。
2. 将请求 VO 转换为 DO，按 id 更新公告。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_001 | 无权操作该公告 |

### 1.3 删除发布的公告

- **路径**: DELETE /oa/announcement/delete
- **权限**: oa:announcement:delete
- **说明**: 删除自己发布的公告，同时删除全部接收关系。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 公告编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验公告存在且 creator 为当前登录用户。
2. 删除该公告的全部接收关系。
3. 删除公告本身。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_001 | 无权操作该公告 |

### 1.4 获得我发布的公告分页

- **路径**: GET /oa/announcement/published-page
- **权限**: oa:announcement:query
- **说明**: 分页返回当前登录用户发布的公告，附带发布人/接收人信息和当前用户视角的转发状态。

**请求参数 (OaAnnouncementPageReqVO)**（继承 PageParam：pageNo、pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| title | String | 否 | - | 公告标题，模糊匹配 |
| type | Integer | 否 | @InEnum(OaAnnouncementTypeEnum) | 公告类型：1 公告、2 通知、3 投票 |
| priority | Integer | 否 | @InEnum(OaPriorityEnum) | 优先级：1 一般、2 重要、3 紧急 |
| readStatus | Boolean | 否 | - | 是否已读 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发布时间范围 |

**响应**: CommonResult&lt;PageResult&lt;OaAnnouncementRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 公告编号 |
| publisherUserId | Long | 发布人用户编号 |
| publisherUserName | String | 发布人用户昵称 |
| publisherDeptId | Long | 发布人部门编号 |
| publisherDeptName | String | 发布人部门名称 |
| type | Integer | 公告类型 |
| priority | Integer | 优先级 |
| title | String | 公告标题 |
| content | String | 公告内容 |
| url | String | 相关链接 |
| top | Boolean | 是否置顶 |
| receiverUserIds | List&lt;Long&gt; | 接收人用户编号列表 |
| receiverUserNames | List&lt;String&gt; | 接收人用户昵称列表 |
| readStatus | Boolean | 当前接收人是否已读（当前用户非接收人时为空） |
| forwarded | Boolean | 当前接收人是否已转发给下属 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按查询条件分页查询当前登录用户（作为 creator）发布的公告。
2. 批量查询公告的接收关系、发布人用户、接收人用户及发布人部门信息，并查询当前登录用户的下属用户集合。
3. 拼接响应：填充发布人昵称/部门、接收人编号与昵称列表；若当前用户是接收人则填充其已读状态。
4. 判断任一接收人是否属于当前登录用户的下属，设置 forwarded 转发标记。

## 2. 我收到的

### 2.1 删除接收的公告

- **路径**: DELETE /oa/announcement/delete-received
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 接收人从"我收到的"列表中移除公告，仅删除本人的接收关系，不影响公告及其他接收人。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 公告编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验公告存在。
2. 校验当前用户是该公告的接收人。
3. 校验接收关系为已读，未读时不允许移除（抛出"请先阅读公告"错误）。
4. 物理删除当前用户这条接收关系记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_002 | 当前用户不是该公告的接收人 |
| 1_054_180_004 | 请先阅读公告，再移除收到的公告 |

### 2.2 获得接收的公告分页

- **路径**: GET /oa/announcement/received-page
- **权限**: oa:announcement:query
- **说明**: 分页返回当前登录用户作为接收人收到的公告，附带已读状态与转发状态。

**请求参数 (OaAnnouncementPageReqVO)**: 同 [1.4 获得我发布的公告分页](#14-获得我发布的公告分页)。

**响应**: CommonResult&lt;PageResult&lt;OaAnnouncementRespVO&gt;&gt;，字段同 [1.4](#14-获得我发布的公告分页)。

**业务逻辑**:
1. 按查询条件联查接收关系，分页查询当前登录用户作为接收人的公告。
2. 批量查询接收关系、发布人、接收人及部门信息，并查询当前登录用户的下属用户集合。
3. 拼接响应：填充发布人昵称/部门、接收人编号与昵称列表、当前用户（接收人）的已读状态。
4. 判断任一接收人是否属于当前登录用户的下属，设置 forwarded 转发标记。

### 2.3 标记公告为已读

- **路径**: PUT /oa/announcement/update-read-status
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 当前接收人将收到的公告标记为已读。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 公告编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验公告存在。
2. 校验当前用户是该公告的接收人。
3. 若接收关系已是已读状态，直接返回（幂等处理）。
4. 更新该接收关系记录的 readStatus 为 true。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_002 | 当前用户不是该公告的接收人 |

### 2.4 转发公告给下属

- **路径**: POST /oa/announcement/forward
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 当前接收人将收到的公告转发给自己的下属，返回本次新增的接收人数量。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 公告编号 |

**响应**: CommonResult&lt;Integer&gt; —— 新增接收人数量（无下属时为 0）。

**业务逻辑**:
1. 对公告按 id 加行锁（selectByIdForUpdate），串行化同一公告的并发转发；公告不存在则报错。
2. 校验当前用户是该公告的接收人。
3. 查询当前用户的下属列表，为空则直接返回 0。
4. 查询公告已有接收人，若任一下属已在接收人中，抛出"公告已转发，请勿重复转发"（与列表 forwarded 状态保持一致）。
5. 批量新增下属的公告接收关系（初始未读），返回新增数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_002 | 当前用户不是该公告的接收人 |
| 1_054_180_003 | 公告已转发，请勿重复转发 |

## 3. 公共详情

### 3.1 获得公告详情

- **路径**: GET /oa/announcement/get
- **权限**: oa:announcement:query
- **说明**: 获得公告详情，仅发布人或接收人可访问，响应中附带当前用户视角的已读/转发状态。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 公告编号 |

**响应**: CommonResult&lt;OaAnnouncementRespVO&gt;，字段同 [1.4 获得我发布的公告分页](#14-获得我发布的公告分页)。

**业务逻辑**:
1. 校验公告存在。
2. 校验访问权限：当前用户须是公告发布人（creator）或该公告的接收人，否则抛出"无权操作该公告"。
3. 按与分页相同的拼接逻辑填充发布人、接收人信息及当前用户的已读状态、转发标记。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_180_000 | 公告不存在 |
| 1_054_180_001 | 无权操作该公告 |
