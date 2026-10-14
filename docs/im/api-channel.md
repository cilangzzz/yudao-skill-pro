# 频道与素材接口 (ImChannelManagerController / ImChannelMaterialManagerController / ImChannelMessageManagerController / ImChannelMaterialController / ImChannelMessageController)

> 提供 IM 频道的后台管理（频道、频道图文素材、频道推送消息的增删改查）与用户端的素材详情渲染、离线消息增量拉取、已读回执上报能力。

## 接口路径前缀

- /im/manager/channel  (Controller: ImChannelManagerController) —— 管理后台·频道
- /im/manager/channel-material  (Controller: ImChannelMaterialManagerController) —— 管理后台·频道素材
- /im/manager/channel-message  (Controller: ImChannelMessageManagerController) —— 管理后台·频道消息
- /im/channel/material  (Controller: ImChannelMaterialController) —— 用户端·频道素材
- /im/channel/message  (Controller: ImChannelMessageController) —— 用户端·频道消息

---

## 1. 频道管理（管理后台）

### 1.1 新增频道
- **路径**: POST /im/manager/channel/create
- **权限**: im:manager:channel:create
- **说明**: 新建一个推送频道，频道业务码全局唯一。

**请求参数 (ImChannelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否（新增时不传） | - | 编号（修改时必填） |
| code | String | 是 | @NotBlank、@Size(max=64)、@Pattern(^[a-z][a-z0-9_]*$) | 频道业务码，唯一；只能由小写字母/数字/下划线组成且以字母开头 |
| name | String | 是 | @NotBlank、@Size(max=64) | 频道名称 |
| avatar | String | 否 | @Size(max=512) | 频道头像 |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum：0 启用 / 1 禁用） |

**响应**: CommonResult&lt;Long&gt; —— 新频道的编号

**业务逻辑**: 1. 校验频道业务码 code 唯一（已存在同名 code 则报错）；2. VO 转 DO 插入频道表；3. 返回新频道编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_001 | 频道编码 '{}' 已存在 |

### 1.2 修改频道
- **路径**: PUT /im/manager/channel/update
- **权限**: im:manager:channel:update
- **说明**: 按编号修改频道基础信息。

**请求参数 (ImChannelSaveReqVO)**: 同 1.1（id 修改时必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**: 1. 校验频道存在（不存在则报错）；2. 校验 code 唯一（排除自身）；3. VO 转 DO 按编号更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_000 | 频道不存在 |
| 1_040_810_001 | 频道编码 '{}' 已存在 |

### 1.3 删除频道
- **路径**: DELETE /im/manager/channel/delete
- **权限**: im:manager:channel:delete
- **说明**: 删除频道；频道下仍有素材时禁止删除。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**: 1. 校验频道存在；2. 统计该频道下素材数量，大于 0 则拒绝删除（防止误删频道导致历史素材/消息回查不到归属）；3. 按编号删除频道。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_000 | 频道不存在 |
| 1_040_810_002 | 频道下还有素材，无法删除 |

### 1.4 获得频道分页
- **路径**: GET /im/manager/channel/page
- **权限**: im:manager:channel:query
- **说明**: 分页查询频道列表，支持 code 模糊、name 模糊、status 精确过滤，按 sort 升序、id 倒序。

**请求参数 (ImChannelPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | （继承 PageParam） | 页码 |
| pageSize | Integer | 是 | （继承 PageParam） | 每页条数 |
| code | String | 否 | - | 频道业务码（模糊匹配） |
| name | String | 否 | - | 频道名称（模糊匹配） |
| status | Integer | 否 | - | 状态（0 启用 / 1 禁用） |

**响应**: CommonResult&lt;PageResult&lt;ImChannelRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 频道业务码 |
| name | String | 频道名称 |
| avatar | String | 频道头像 |
| sort | Integer | 排序 |
| status | Integer | 状态（0 启用 / 1 禁用） |
| createTime | LocalDateTime | 创建时间 |

### 1.5 获得频道详情
- **路径**: GET /im/manager/channel/get
- **权限**: im:manager:channel:query
- **说明**: 按编号查询单个频道详情。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;ImChannelRespVO&gt;（字段同 1.4）

### 1.6 获得启用的频道精简列表
- **路径**: GET /im/manager/channel/simple-list
- **权限**: 已认证（无独立权限标识）
- **说明**: 查询全部启用状态的频道，按 sort 升序；前端表单选择频道时调用。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ImChannelRespVO&gt;&gt;（字段同 1.4）

---

## 2. 素材管理（管理后台）

### 2.1 新增素材
- **路径**: POST /im/manager/channel-material/create
- **权限**: im:manager:channel-material:create
- **说明**: 在指定频道下新建图文/外链素材。

**请求参数 (ImChannelMaterialSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否（新增时不传） | - | 编号（修改时必填） |
| channelId | Long | 是 | @NotNull | 所属频道编号 |
| type | Integer | 是 | @NotNull | 内容类型（ImChannelMaterialTypeEnum：1 站内富文本 / 2 外链） |
| title | String | 是 | @NotBlank、@Size(max=128) | 标题 |
| coverUrl | String | 否 | @Size(max=512) | 封面图 |
| summary | String | 否 | @Size(max=255) | 摘要 |
| content | String | 否 | - | 正文；富文本 HTML |
| url | String | 否 | @Size(max=512) | 跳转链接；为空表示走客户端内置详情页 |

**响应**: CommonResult&lt;Long&gt; —— 新素材的编号

**业务逻辑**: 1. 校验所属频道存在（不存在则报错）；2. VO 转 DO 插入素材表；3. 返回新素材编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_000 | 频道不存在 |

### 2.2 修改素材
- **路径**: PUT /im/manager/channel-material/update
- **权限**: im:manager:channel-material:update
- **说明**: 按编号修改素材内容。

**请求参数 (ImChannelMaterialSaveReqVO)**: 同 2.1（id 修改时必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**: 1. 校验素材存在；2. 校验所属频道存在；3. VO 转 DO 按编号更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_010 | 素材不存在 |
| 1_040_810_000 | 频道不存在 |

### 2.3 删除素材
- **路径**: DELETE /im/manager/channel-material/delete
- **权限**: im:manager:channel-material:delete
- **说明**: 删除素材；已被推送过的素材禁止删除。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**: 1. 校验素材存在；2. 统计频道消息表中引用该素材的数量，大于 0 则拒绝删除（防止删除素材导致历史 channel_message 反查不到内容）；3. 按编号删除素材。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_010 | 素材不存在 |
| 1_040_810_011 | 素材已被推送过，无法删除 |

### 2.4 获得素材分页
- **路径**: GET /im/manager/channel-material/page
- **权限**: im:manager:channel-material:query
- **说明**: 分页查询素材列表，支持频道、内容类型、标题模糊、创建时间区间过滤，按 id 倒序；结果回填频道名。

**请求参数 (ImChannelMaterialPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | （继承 PageParam） | 页码 |
| pageSize | Integer | 是 | （继承 PageParam） | 每页条数 |
| channelId | Long | 否 | - | 频道编号 |
| type | Integer | 否 | - | 内容类型（1 站内富文本 / 2 外链） |
| title | String | 否 | - | 标题（模糊匹配） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ImChannelMaterialRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| channelId | Long | 频道编号 |
| channelName | String | 频道名称（关联查询填充） |
| type | Integer | 内容类型（1 站内富文本 / 2 外链） |
| title | String | 标题 |
| coverUrl | String | 封面图 |
| summary | String | 摘要 |
| content | String | 正文；富文本 HTML |
| url | String | 跳转链接 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按条件分页查询素材；2. 批量查询本页素材所属的频道；3. 将频道名回填到 channelName 字段返回。

### 2.5 获得素材详情
- **路径**: GET /im/manager/channel-material/get
- **权限**: im:manager:channel-material:query
- **说明**: 按编号查询单个素材详情（含富文本正文）。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;ImChannelMaterialRespVO&gt;（字段同 2.4）

### 2.6 获得指定频道下的素材精简列表
- **路径**: GET /im/manager/channel-material/simple-list
- **权限**: 已认证（无独立权限标识）
- **说明**: 查询指定频道下的全部素材，按 id 倒序；用于推送弹窗的素材下拉。

**请求参数**: 无（Query 参数 channelId：频道编号，必填）

**响应**: CommonResult&lt;List&lt;ImChannelMaterialRespVO&gt;&gt;（字段同 2.4）

---

## 3. 频道消息（管理后台）

### 3.1 立即推送频道消息
- **路径**: POST /im/manager/channel-message/send
- **权限**: im:manager:channel-message:send
- **说明**: 将指定素材作为一条频道消息立即推送给全员或指定用户。

**请求参数 (ImChannelMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| materialId | Long | 是 | @NotNull | 素材编号 |
| receiverUserIds | List&lt;Long&gt; | 否 | - | 接收人编号列表；为空表示全员 |

**响应**: CommonResult&lt;Long&gt; —— 新频道消息的编号

**业务逻辑**: 1. 校验素材存在；2. 由素材组装 payload JSON 快照（不含富文本正文），落库一行频道消息：channelId 取自素材所属频道、type 为素材消息类型、content 为 payload JSON、sendTime 为当前时间；3. 事务内提交后异步推 WebSocket：receiverUserIds 非空时按用户点对点推送，为空时全员广播。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_010 | 素材不存在 |

### 3.2 删除频道消息
- **路径**: DELETE /im/manager/channel-message/delete
- **权限**: im:manager:channel-message:delete
- **说明**: 按编号删除一条频道消息记录。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**: 1. 校验频道消息存在；2. 按编号删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_020 | 频道消息不存在 |

### 3.3 获得频道消息分页
- **路径**: GET /im/manager/channel-message/page
- **权限**: im:manager:channel-message:query
- **说明**: 分页查询频道消息，支持频道、素材、发送时间区间过滤，按 id 倒序；结果回填频道名与素材标题/封面。

**请求参数 (ImChannelMessagePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | （继承 PageParam） | 页码 |
| pageSize | Integer | 是 | （继承 PageParam） | 每页条数 |
| channelId | Long | 否 | - | 频道编号 |
| materialId | Long | 否 | - | 素材编号 |
| sendTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发送时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ImChannelMessageRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| channelId | Long | 频道编号 |
| channelName | String | 频道名称（关联查询填充） |
| materialId | Long | 素材编号 |
| materialTitle | String | 素材标题（关联查询填充） |
| materialCoverUrl | String | 素材封面 URL（关联查询填充） |
| type | Integer | 消息类型（ImContentTypeEnum，推送消息为素材类型） |
| content | String | 消息内容；payload JSON 快照 |
| receiverUserIds | List&lt;Long&gt; | 接收人编号列表；为空表示全员 |
| sendTime | LocalDateTime | 发送时间 |

**业务逻辑**: 1. 按条件分页查询频道消息；2. 批量查询本页消息关联的频道与素材；3. 回填 channelName、materialTitle、materialCoverUrl 后返回。

### 3.4 获得频道消息详情
- **路径**: GET /im/manager/channel-message/get
- **权限**: im:manager:channel-message:query
- **说明**: 按编号查询单条频道消息详情，同样回填频道名与素材标题/封面。

**请求参数**: 无（Query 参数 id：消息编号，必填）

**响应**: CommonResult&lt;ImChannelMessageRespVO&gt;（字段同 3.3）

---

## 4. 用户端接口

### 4.1 获取素材详情
- **路径**: GET /im/channel/material/get
- **权限**: 已认证（用户端登录态）
- **说明**: 按编号获取素材详情，用于客户端点击图文卡片渲染详情页。

**请求参数**: 无（Query 参数 id：素材编号，必填）

**响应**: CommonResult&lt;ImChannelMaterialRespVO&gt;（字段同 2.4）

**业务逻辑**: 1. 校验素材存在（不存在则报错）；2. DO 转 VO 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_810_010 | 素材不存在 |

### 4.2 拉取频道消息（离线增量）
- **路径**: GET /im/channel/message/pull
- **权限**: 已认证（用户端登录态）
- **说明**: 按消息 id 游标增量拉取当前用户应收的频道消息，并按已读游标标记回执状态。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| minId | Long | 否 | @PositiveOrZero | 游标；返回 id 大于该值的消息，默认 0 |
| size | Integer | 否 | @Min(1)、@Max(200) | 单次条数，默认 100，一次最多 200 条 |

**响应**: CommonResult&lt;List&lt;ImChannelMessagePullRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 消息编号 |
| channelId | Long | 频道编号 |
| materialId | Long | 素材编号 |
| type | Integer | 消息类型（ImContentTypeEnum） |
| content | String | 消息内容；payload JSON 快照 |
| receiptStatus | Integer | 当前用户回执/已读态（ImMessageReceiptStatusEnum：2 已读 DONE / 1 未读 PENDING） |
| sendTime | LocalDateTime | 发送时间 |

**业务逻辑**: 1. 按当前登录用户 + minId 游标查询消息（命中条件：id 大于游标，且接收人为空表示全员，或定向接收列表包含当前用户），按 id 升序、限制条数；2. 批量查询当前用户在各频道的已读游标（已读最大消息 id）；3. 逐条比对游标，已读最大 id ≥ 消息 id 记为 DONE，否则 PENDING，转换 VO 返回。

### 4.3 标记频道消息已读
- **路径**: PUT /im/channel/message/read
- **权限**: 已认证（用户端登录态）
- **说明**: 上报当前用户在某频道的已读位置，并异步给自己多端同步 READ 事件。

**请求参数**: 无（Query 参数：channelId 频道编号必填、messageId 已读到的消息编号必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**: 1. 校验消息真实存在且属于该频道，不存在或不属于则直接返回（避免伪造 messageId 污染读位置）；2. 定向消息校验对当前用户可见（receiverUserIds 为空表示全员可见，否则需包含当前用户）；3. 更新会话已读位置，读位置未前进则直接返回不推送；4. 异步通过 WebSocket 向自己推送 READ 事件做多端同步（频道无发送方回执概念，不广播）。

---

## 错误码汇总（频道域 1-040-810-000 段）

| 错误码 | 说明 |
|-------|------|
| 1_040_810_000 | 频道不存在 |
| 1_040_810_001 | 频道编码 '{}' 已存在 |
| 1_040_810_002 | 频道下还有素材，无法删除 |
| 1_040_810_010 | 素材不存在 |
| 1_040_810_011 | 素材已被推送过，无法删除 |
| 1_040_810_020 | 频道消息不存在 |
