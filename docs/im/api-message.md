# 单聊/群聊消息与会话接口 (ImGroupMessageController / ImPrivateMessageController / ImConversationReadController / ImGroupMessageManagerController / ImPrivateMessageManagerController)

> 提供 IM 群聊与私聊消息的发送、增量拉取、已读回执、撤回、历史查询，会话读位置的离线补偿拉取，以及管理后台的消息审计分页与详情。

## 接口路径前缀

| 前缀 | Controller | 说明 |
|------|-----------|------|
| /im/message/group | ImGroupMessageController | 群聊消息（用户端） |
| /im/message/private | ImPrivateMessageController | 私聊消息（用户端） |
| /im/conversation-read | ImConversationReadController | 会话读位置 |
| /im/manager/message/group | ImGroupMessageManagerController | 群聊消息管理（管理后台） |
| /im/manager/message/private | ImPrivateMessageManagerController | 私聊消息管理（管理后台） |

消息类型 type 取值参见 `ImContentTypeEnum`：用户聊天消息（normal）为 101 文本 / 102 图片 / 103 语音 / 104 视频 / 105 文件 / 107 合并转发 / 108 名片 / 115 表情；消息状态 status 参见 `ImMessageStatusEnum`（0 正常 / 撤回）；回执状态 receiptStatus 参见 `ImMessageReceiptStatusEnum`（无需回执 / 待回执 / 回执完成）。用户端接口均要求登录（已认证），按 `getLoginUserId()` 取当前用户；管理端接口需 `im:manager:message:query` 权限。

## 1. 群聊消息（Controller: ImGroupMessageController，前缀 /im/message/group）

### 1.1 发送群聊消息
- **路径**: POST /im/message/group/send
- **权限**: 已认证（发送人为当前登录用户）
- **说明**: 校验后保存一条群聊消息，固化可见成员快照，并通过 WebSocket 异步广播

**请求参数 (ImGroupMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| clientMessageId | String | 是 | @NotEmpty | 客户端消息编号（幂等键） |
| groupId | Long | 是 | @NotNull | 群编号 |
| type | Integer | 是 | @NotNull、@InEnum(ImContentTypeEnum.class)、@AssertTrue（仅允许 normal 用户消息） | 消息类型 |
| content | String | 是 | @NotEmpty | 消息内容，JSON 格式 |
| atUserIds | List\<Long\> | 否 | | @目标用户编号列表 |
| receipt | Boolean | 否 | | 是否需要回执 |

**响应**: CommonResult\<ImGroupMessageRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 消息编号 |
| clientMessageId | String | 客户端消息编号 |
| senderId | Long | 发送人编号 |
| groupId | Long | 群编号 |
| type | Integer | 消息类型 |
| content | String | 消息内容 |
| status | Integer | 消息状态 |
| sendTime | LocalDateTime | 发送时间 |
| atUserIds | List\<Long\> | @目标用户编号列表 |
| receiverUserIds | List\<Long\> | 定向接收用户编号列表（可见快照） |
| receiptStatus | Integer | 回执状态 |
| readCount | Integer | 已读人数（回执消息、且发送人为当前用户时有值） |

**业务逻辑**:
1. 幂等校验：按 senderId + clientMessageId 查重，命中直接返回已存在消息
2. 消息内容校验：type 须为 normal 用户消息，content JSON 按类型校验（文本、图片/语音/视频/文件 url、名片、合并转发等），非法抛 MESSAGE_CONTENT_INVALID
3. 校验群存在（未封禁、未解散）且发送人仍在群中；禁言校验：全群禁言仅群主/管理员豁免，成员禁言期内禁止发送
4. 文本消息走敏感词过滤（MESSAGE_SENSITIVE_WORD_BLOCKED）
5. 固化发送当时可见成员快照 receiver_user_ids（无定向列表即全员广播，发送者始终纳入）；引用 quote 消息规范化：原消息须存在、未撤回、同群、对发送人可见，且新消息可见集合必须为原消息可见集合的子集（防定向消息内容随引用广播泄漏）
6. 构建并保存消息（status=NORMAL；回执状态由群已读开关与 receipt 决定，开关关闭强制 NO_RECEIPT）；唯一键冲突（并发重发）时回查已存在消息返回
7. WebSocket 异步推送群消息通知给快照内可见成员（含发送方多端同步）

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_004 | 消息包含敏感词，无法发送 |
| 1_040_300_008 | 引用的消息不可用 |
| 1_040_300_013 | 消息内容格式不正确 |
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_500_001 | 您已不在该群中 |
| 1_040_500_012 | 群已全局禁言，仅群主和管理员可发送消息 |
| 1_040_500_013 | 您已被禁言，解除时间：{} |

### 1.2 拉取群聊消息（增量）
- **路径**: GET /im/message/group/pull
- **权限**: 已认证
- **说明**: 离线 / 断线重连场景按 minId 增量拉取本人可见的群聊消息

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| minId | Long | 是 | | 最小消息 id（从该 id 之后拉取） |
| size | Integer | 是 | @Min(1) | 拉取数量（超过配置 maxPullSize 报错） |

**响应**: CommonResult\<List\<ImGroupMessageRespVO\>\>（字段同 1.1 响应表）

**业务逻辑**:
1. 校验 size 不超过配置 maxPullSize（MESSAGE_PULL_SIZE_EXCEEDED）
2. 计算拉取时间窗 minSendTime：超过 groupPullMaxDays 天的老消息不再通过离线通道推送
3. 候选群 = 用户曾经加入的所有群（含已退群）；无候选群直接返回空列表
4. SQL 按 receiver_user_ids 快照过滤当前用户可见性，结果按 id 升序返回
5. 补齐本人发送的回执消息已读人数 readCount：应读分母 = 快照 ∩ 当前有效成员 - 发送者，按各成员群已读位置统计（群已读开关关闭时不补）

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_005 | 单次拉取消息数量不能超过 {} 条 |

### 1.3 标记群聊消息已读
- **路径**: PUT /im/message/group/read
- **权限**: 已认证
- **说明**: 上报群会话已读位置，触发已读回执刷新

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| groupId | Long | 是 | | 群编号 |
| messageId | Long | 是 | | 已读到的消息编号 |

**响应**: CommonResult\<Boolean\>（固定返回 true）

**业务逻辑**:
1. 群聊已读全局开关校验（关闭报 MESSAGE_GROUP_READ_DISABLED）
2. 校验消息存在、归属于该群、且对当前用户可见（按快照），否则报 MESSAGE_NOT_IN_GROUP
3. 取旧读位置，更新会话读位置（CAS 单调递增）；读位置未前进则直接返回
4. 异步发送 READ 事件给自己的其他终端（多端同步），并刷新 (旧位置, 新位置] 区间内待回执消息：统计已读人数、全部已读标记回执 DONE、向消息发送方推送 RECEIPT 事件

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_009 | 消息不属于该群 |
| 1_040_300_011 | 群聊已读功能已关闭 |

### 1.4 撤回群聊消息
- **路径**: DELETE /im/message/group/recall
- **权限**: 已认证
- **说明**: 撤回一条群聊消息，普通成员限本人消息且受时间窗限制

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 是 | | 消息编号 |

**响应**: CommonResult\<ImGroupMessageRespVO\>（字段同 1.1 响应表，返回撤回事件消息）

**业务逻辑**:
1. 校验消息存在（MESSAGE_NOT_EXISTS）
2. 校验撤回人仍在群中，并取其角色用于权限判断
3. 普通成员只能撤回自己发送的消息；群主/管理员可撤回他人违规消息，否则报 MESSAGE_RECALL_DENIED
4. 不能重复撤回（MESSAGE_ALREADY_RECALLED）
5. 撤回时间窗仅约束撤回自己的消息（recallTimeoutMinutes），群主/管理员治理他人消息不受时间限制，超时报 MESSAGE_RECALL_TIMEOUT
6. 更新原消息状态为 RECALL
7. 以原消息可见快照为接收范围发送 RECALL 类型撤回事件消息并 WebSocket 推送

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_000 | 消息不存在 |
| 1_040_300_002 | 只能撤回自己发送的消息 |
| 1_040_300_003 | 消息已撤回 |
| 1_040_300_007 | 超过 {} 分钟的消息无法撤回 |
| 1_040_500_001 | 您已不在该群中 |

### 1.5 获取群消息已读用户列表
- **路径**: GET /im/message/group/get-read-user-ids
- **权限**: 已认证
- **说明**: 查询一条群消息（须为本人发送）的已读用户编号列表

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| groupId | Long | 是 | | 群编号 |
| messageId | Long | 是 | | 消息编号 |

**响应**: CommonResult\<List\<Long\>\>（已读用户编号列表）

**业务逻辑**:
1. 群聊已读全局开关校验（关闭报 MESSAGE_GROUP_READ_DISABLED）
2. 校验当前用户在群中（GROUP_MEMBER_NOT_IN_GROUP）
3. 校验消息归属该群且对调用者可见（按快照），不满足返回空列表
4. 仅消息发送方关心已读人数，非发送方查询直接返回空列表
5. 取当前有效成员与全员已读位置，计算该消息可见成员集合（快照 ∩ 有效成员，排除发送者）
6. 返回可见范围内已读位置 >= messageId 的用户编号列表

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_011 | 群聊已读功能已关闭 |
| 1_040_500_001 | 您已不在该群中 |

### 1.6 查询群聊历史消息
- **路径**: GET /im/message/group/list
- **权限**: 已认证
- **说明**: 进入会话时按 maxId 游标向前翻页拉取群聊历史消息

**请求参数 (ImGroupMessageListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| groupId | Long | 是 | @NotNull | 群编号 |
| maxId | Long | 否 | | 起始消息编号，从该 id 往前拉取（不含），为空则从最新消息开始 |
| limit | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 拉取数量 |

**响应**: CommonResult\<List\<ImGroupMessageRespVO\>\>（字段同 1.1 响应表）

**业务逻辑**:
1. 校验用户曾经在群（当前在群或已退群，与 pull 的退群窗口口径一致），否则报 GROUP_MEMBER_NOT_IN_GROUP
2. SQL 按 receiver_user_ids 快照过滤当前用户可见，从 maxId 往前拉取 limit 条历史消息

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_500_001 | 您已不在该群中 |

## 2. 私聊消息（Controller: ImPrivateMessageController，前缀 /im/message/private）

### 2.1 发送私聊消息
- **路径**: POST /im/message/private/send
- **权限**: 已认证（发送人为当前登录用户）
- **说明**: 校验好友关系后保存一条私聊消息并双向 WebSocket 推送

**请求参数 (ImPrivateMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| clientMessageId | String | 是 | @NotEmpty | 客户端消息编号（幂等键） |
| receiverId | Long | 是 | @NotNull | 接收人编号 |
| type | Integer | 是 | @NotNull、@InEnum(ImContentTypeEnum.class)、@AssertTrue（仅允许 normal 用户消息） | 消息类型 |
| content | String | 是 | @NotEmpty | 消息内容，JSON 格式 |
| receipt | Boolean | 否 | | 是否需要回执（不传按 true） |

**响应**: CommonResult\<ImPrivateMessageRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 消息编号 |
| clientMessageId | String | 客户端消息编号 |
| senderId | Long | 发送人编号 |
| receiverId | Long | 接收人编号 |
| type | Integer | 消息类型 |
| content | String | 消息内容 |
| status | Integer | 消息状态 |
| receiptStatus | Integer | 回执状态 |
| sendTime | LocalDateTime | 发送时间 |

**业务逻辑**:
1. 幂等校验：按 senderId + clientMessageId 查重，命中直接返回已存在消息
2. 消息内容校验：type 须为 normal 用户消息，content JSON 按类型校验，非法抛 MESSAGE_CONTENT_INVALID
3. 好友校验：非好友报 FRIEND_NOT_FRIEND，被对方拉黑报 FRIEND_BLOCKED_BY_PEER
4. 文本消息走敏感词过滤（MESSAGE_SENSITIVE_WORD_BLOCKED）
5. 引用 quote 消息规范化：原消息须存在、未撤回、与本次发送同会话（双向判断），否则报 MESSAGE_QUOTE_INVALID
6. 构建并保存消息（receipt 默认 true；私聊已读开关关闭时强制 NO_RECEIPT）；唯一键冲突（并发重发）时回查已存在消息返回
7. WebSocket 异步推送：接收方 + 发送方多端同步

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_004 | 消息包含敏感词，无法发送 |
| 1_040_300_008 | 引用的消息不可用 |
| 1_040_300_013 | 消息内容格式不正确 |
| 1_040_600_001 | 对方不是您的好友 |
| 1_040_600_004 | 您已被对方拉入黑名单，无法发送消息 |

### 2.2 拉取私聊消息（增量）
- **路径**: GET /im/message/private/pull
- **权限**: 已认证
- **说明**: 离线 / 断线重连场景按 minId 增量拉取与本人相关的私聊消息

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| minId | Long | 是 | | 最小消息 id（从该 id 之后拉取） |
| size | Integer | 是 | @Min(1) | 拉取数量（超过配置 maxPullSize 报错） |

**响应**: CommonResult\<List\<ImPrivateMessageRespVO\>\>（字段同 2.1 响应表）

**业务逻辑**:
1. 校验 size 不超过配置 maxPullSize（MESSAGE_PULL_SIZE_EXCEEDED）
2. 计算拉取时间窗 minSendTime：超过 privatePullMaxDays 天的老消息不再通过离线通道推送
3. 按 minId + minSendTime 拉取与本人相关（发送或接收）的消息，避免 minId 恰好被发出后才拉取导致漏消息

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_005 | 单次拉取消息数量不能超过 {} 条 |

### 2.3 标记私聊消息已读
- **路径**: PUT /im/message/private/read
- **权限**: 已认证
- **说明**: 上报私聊会话已读位置，完成对方消息回执并双向推送事件

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| receiverId | Long | 是 | | 接收方用户编号（对方） |
| messageId | Long | 是 | | 已读位置（含），通常是会话内最大消息编号 |

**响应**: CommonResult\<Boolean\>（固定返回 true）

**业务逻辑**:
1. 私聊已读全局开关校验（关闭报 MESSAGE_PRIVATE_READ_DISABLED）
2. 回执置 DONE：把 (receiverId → userId) 方向上 id <= messageId、待回执（PENDING）的消息标记为已完成，只翻 PENDING 行避免覆盖 NO_RECEIPT / 已 DONE
3. 同步写会话读位置（唯一权威，CAS 单调递增）；读位置未前进则结束
4. 异步发送 READ 事件给自己的其他终端（多端同步）、RECEIPT 事件给对方

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_010 | 私聊已读功能已关闭 |

### 2.4 查询对方已读到我发的最大消息 id
- **路径**: GET /im/message/private/max-read-message-id
- **权限**: 已认证
- **说明**: 多端 / 离线场景下的已读位置补齐，进入会话或断线重连后调用

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| peerId | Long | 是 | | 对方用户编号 |

**响应**: CommonResult\<Long\>（对方已读到的最大消息编号）

**业务逻辑**:
1. 私聊已读全局开关校验（关闭报 MESSAGE_PRIVATE_READ_DISABLED）
2. 查询对方在「与当前用户的会话」中的读位置，即对方把当前用户发的消息读到了哪

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_010 | 私聊已读功能已关闭 |

### 2.5 撤回私聊消息
- **路径**: DELETE /im/message/private/recall
- **权限**: 已认证
- **说明**: 撤回一条本人发送的私聊消息

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 是 | | 消息编号 |

**响应**: CommonResult\<ImPrivateMessageRespVO\>（字段同 2.1 响应表，返回撤回事件消息）

**业务逻辑**:
1. 校验消息存在（MESSAGE_NOT_EXISTS）
2. 只能撤回自己发送的消息，否则报 MESSAGE_RECALL_DENIED
3. 不能重复撤回（MESSAGE_ALREADY_RECALLED）
4. 校验撤回时间窗 recallTimeoutMinutes，超时报 MESSAGE_RECALL_TIMEOUT
5. 更新原消息状态为 RECALL
6. 向原接收人发送 RECALL 类型撤回事件消息并 WebSocket 推送

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_040_300_000 | 消息不存在 |
| 1_040_300_002 | 只能撤回自己发送的消息 |
| 1_040_300_003 | 消息已撤回 |
| 1_040_300_007 | 超过 {} 分钟的消息无法撤回 |

### 2.6 查询私聊历史消息
- **路径**: GET /im/message/private/list
- **权限**: 已认证
- **说明**: 进入会话时按 maxId 游标向前翻页拉取与对方的私聊历史消息

**请求参数 (ImPrivateMessageListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| receiverId | Long | 是 | @NotNull | 接收人编号（对方） |
| maxId | Long | 否 | | 起始消息编号，从该 id 往前拉取（不含），为空则从最新消息开始 |
| limit | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 拉取数量 |

**响应**: CommonResult\<List\<ImPrivateMessageRespVO\>\>（字段同 2.1 响应表）

**业务逻辑**:
1. SQL 过滤与当前用户和对方相关的会话消息，从 maxId 往前拉取 limit 条历史消息

## 3. 会话读位置（Controller: ImConversationReadController，前缀 /im/conversation-read）

### 3.1 增量拉取当前用户的会话读位置
- **路径**: GET /im/conversation-read/pull
- **权限**: 已认证
- **说明**: 重连 / 离线补偿场景，按更新时间游标增量拉取当前用户在所有会话的已读位置

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| lastUpdateTime | Long | 否 | | 上次拉取到的最新更新时间（毫秒时间戳）；首次拉取不传 |
| lastId | Long | 否 | | 上次拉取到的最后一条记录 id；首次拉取不传 |
| limit | Integer | 是 | @Min(1)、@Max(200) | 单次拉取条数 |

**响应**: CommonResult\<List\<ImConversationReadRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 读位置编号 |
| conversationType | Integer | 会话类型（参见 ImConversationTypeEnum 枚举） |
| targetId | Long | 目标编号（群编号或对方用户编号） |
| messageId | Long | 最大已读消息编号 |
| updateTime | LocalDateTime | 最近更新时间（增量拉取游标用） |

**业务逻辑**:
1. 按 userId + lastUpdateTime + lastId 游标查询当前用户的会话读位置列表（上限 limit 条），用于多端同步重放已读状态

## 4. 群聊消息管理（Controller: ImGroupMessageManagerController，前缀 /im/manager/message/group）

### 4.1 获得群聊消息分页
- **路径**: GET /im/manager/message/group/page
- **权限**: im:manager:message:query
- **说明**: 管理后台按条件分页查询群聊消息，附带回填群名称与用户昵称

**请求参数 (ImGroupMessageManagerPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数 |
| groupId | Long | 否 | | 群编号 |
| senderId | Long | 否 | | 发送人编号 |
| type | Integer | 否 | | 消息类型（参见 ImContentTypeEnum 枚举） |
| content | String | 否 | | 消息内容（模糊匹配） |
| status | Integer | 否 | | 消息状态（参见 ImMessageStatusEnum 枚举） |
| sendTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发送时间范围 |

**响应**: CommonResult\<PageResult\<ImGroupMessageManagerRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 消息编号 |
| clientMessageId | String | 客户端消息编号 |
| groupId | Long | 群编号 |
| groupName | String | 群名称（回填） |
| senderId | Long | 发送人编号 |
| senderNickname | String | 发送人昵称（回填） |
| type | Integer | 消息类型 |
| content | String | 消息内容（JSON 格式） |
| status | Integer | 消息状态 |
| atUserIds | List\<Long\> | @ 目标用户编号列表（-1 表示 @所有人） |
| atUserNicknames | List\<String\> | @ 目标用户昵称列表（-1 位置为 null，前端展示「@所有人」） |
| receiptStatus | Integer | 回执状态 |
| sendTime | LocalDateTime | 发送时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 groupId / senderId / type / content / status / sendTime 条件分页查询群聊消息
2. 批量查询群名称、发送人昵称、@ 用户昵称（-1 表示 @所有人，跳过查询，由前端判断渲染）
3. 转换为 VO 并回填 groupName、senderNickname、atUserNicknames（-1 位置留 null）

### 4.2 获得群聊消息详情
- **路径**: GET /im/manager/message/group/get
- **权限**: im:manager:message:query
- **说明**: 按编号查询一条群聊消息详情

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 是 | | 消息编号 |

**响应**: CommonResult\<ImGroupMessageManagerRespVO\>（字段同 4.1 响应表，昵称类字段不回填）

**业务逻辑**:
1. 按消息编号查询群聊消息并转换为 VO 返回

## 5. 私聊消息管理（Controller: ImPrivateMessageManagerController，前缀 /im/manager/message/private）

### 5.1 获得私聊消息分页
- **路径**: GET /im/manager/message/private/page
- **权限**: im:manager:message:query
- **说明**: 管理后台按条件分页查询私聊消息，附带回填双方昵称

**请求参数 (ImPrivateMessageManagerPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数 |
| senderId | Long | 否 | | 发送人编号 |
| receiverId | Long | 否 | | 接收人编号 |
| type | Integer | 否 | | 消息类型（参见 ImContentTypeEnum 枚举） |
| content | String | 否 | | 消息内容（模糊匹配） |
| status | Integer | 否 | | 消息状态（参见 ImMessageStatusEnum 枚举） |
| sendTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发送时间范围 |

**响应**: CommonResult\<PageResult\<ImPrivateMessageManagerRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 消息编号 |
| clientMessageId | String | 客户端消息编号 |
| senderId | Long | 发送人编号 |
| senderNickname | String | 发送人昵称（回填） |
| receiverId | Long | 接收人编号 |
| receiverNickname | String | 接收人昵称（回填） |
| type | Integer | 消息类型 |
| content | String | 消息内容（JSON 格式） |
| status | Integer | 消息状态 |
| receiptStatus | Integer | 回执状态 |
| sendTime | LocalDateTime | 发送时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 senderId / receiverId / type / content / status / sendTime 条件分页查询私聊消息
2. 一次性批量查询发送人 + 接收人昵称
3. 转换为 VO 并回填 senderNickname、receiverNickname

### 5.2 获得私聊消息详情
- **路径**: GET /im/manager/message/private/get
- **权限**: im:manager:message:query
- **说明**: 按编号查询一条私聊消息详情

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| id | Long | 是 | | 消息编号 |

**响应**: CommonResult\<ImPrivateMessageManagerRespVO\>（字段同 5.1 响应表，昵称类字段不回填）

**业务逻辑**:
1. 按消息编号查询私聊消息并转换为 VO 返回
