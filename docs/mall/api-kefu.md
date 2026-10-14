# 客服（会话/消息）接口 (KeFuConversationController / KeFuMessageController)

> 商城客服系统的管理端接口：管理员查看会员会话列表、置顶/删除会话、发送客服消息、查询历史消息并标记已读；消息实时推送通过 WebSocket 完成。

## 接口路径前缀

- /promotion/kefu-conversation  (Controller: KeFuConversationController)
- /promotion/kefu-message  (Controller: KeFuMessageController)

## 1. 客服会话（KeFuConversationController）

### 1.1 获得客服会话

- **路径**: GET /promotion/kefu-conversation/get
- **权限**: promotion:kefu-conversation:query
- **说明**: 根据编号获得单个客服会话详情，并拼接会话所属会员的头像与昵称；会话不存在时返回 null。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 会话编号 |

**响应**: CommonResult&lt;KeFuConversationRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| userId | Long | 会话所属用户（会员）编号 |
| userAvatar | String | 会话所属用户头像（来自 member 模块拼接） |
| userNickname | String | 会话所属用户昵称（来自 member 模块拼接） |
| lastMessageTime | LocalDateTime | 最后聊天时间 |
| lastMessageContent | String | 最后聊天内容 |
| lastMessageContentType | Integer | 最后发送的消息类型（1 文本/2 图片/3 语音/4 视频/5 系统/10 商品/11 订单） |
| adminPinned | Boolean | 管理端是否置顶 |
| userDeleted | Boolean | 用户端是否已删除（不可见） |
| adminDeleted | Boolean | 管理端是否已删除（不可见） |
| adminUnreadMessageCount | Integer | 管理员未读消息数 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询会话，不存在时直接返回 null。 2. DO 转换为 KeFuConversationRespVO。 3. 通过 MemberUserApi 查询会话所属会员，拼接 userAvatar、userNickname。

### 1.2 置顶/取消置顶客服会话

- **路径**: PUT /promotion/kefu-conversation/update-conversation-pinned
- **权限**: promotion:kefu-conversation:update
- **说明**: 管理员置顶或取消置顶指定会话（仅更新管理端的置顶标记）。

**请求参数 (KeFuConversationUpdatePinnedReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 会话编号 |
| adminPinned | Boolean | 是 | @NotNull | 是否管理端置顶 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**: 1. 校验会话存在（KEFU_CONVERSATION_NOT_EXISTS）。 2. 更新会话的 adminPinned 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_019_000 | 客服会话不存在 |

### 1.3 删除客服会话

- **路径**: DELETE /promotion/kefu-conversation/delete
- **权限**: promotion:kefu-conversation:delete
- **说明**: 管理端删除会话；逻辑删除（仅置 adminDeleted=true，管理端不可见，数据不物理删除），会员端仍可继续使用。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 会话编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**: 1. 校验会话存在（KEFU_CONVERSATION_NOT_EXISTS）。 2. 将会话的 adminDeleted 更新为 true（注释说明：不真删，只是管理员端看不到）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_019_000 | 客服会话不存在 |

### 1.4 获得客服会话列表

- **路径**: GET /promotion/kefu-conversation/list
- **权限**: promotion:kefu-conversation:query
- **说明**: 获得管理端可见的全部客服会话列表（过滤 adminDeleted=true 的会话），并批量拼接会员头像与昵称。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;KeFuConversationRespVO&gt;&gt;，字段同 1.1。

**业务逻辑**: 1. 查询会话列表：过滤 adminDeleted=false，按 createTime 倒序。 2. DO 列表转换为 KeFuConversationRespVO 列表。 3. 按会话中的 userId 批量调用 MemberUserApi.getUserMap，逐条拼接 userAvatar、userNickname。

## 2. 客服消息（KeFuMessageController）

### 2.1 发送客服消息

- **路径**: POST /promotion/kefu-message/send
- **权限**: promotion:kefu-message:send
- **说明**: 管理员（客服）向指定会话发送消息，接收人固定为会话所属会员；消息保存后通过 WebSocket 异步通知会员端与所有管理端。

**请求参数 (KeFuMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 是 | @NotNull | 会话编号 |
| contentType | Integer | 是 | @NotNull | 消息类型（1 文本/2 图片/3 语音/4 视频/5 系统/10 商品/11 订单） |
| content | String | 是 | @NotEmpty | 消息内容 |
| senderId | Long | 否 | hidden，后端设置 | 发送人编号（前端无需传递，取当前登录管理员） |
| senderType | Integer | 否 | hidden，后端设置 | 发送人类型（前端无需传递，固定为 ADMIN） |

**响应**: CommonResult&lt;Long&gt;（消息编号）

**业务逻辑**: 1. Controller 将 senderId 设为当前登录用户、senderType 设为 ADMIN。 2. 校验会话存在（KEFU_CONVERSATION_NOT_EXISTS）。 3. 校验接收人存在（按会话 userId 校验会员用户）。 4. 保存消息 DO，接收人设置为会话所属会员（receiverId/receiverType=MEMBER）。 5. 事务内更新会话冗余字段：最后消息时间/内容/类型；同时若会员发送过消息会增加管理员未读数、若管理员此前删除过该会话则恢复（adminDeleted 置回 false）。 6. 异步 WebSocket 推送：向会话会员发送 KEFU_MESSAGE_TYPE 消息（附管理员头像），并向所有管理员广播同一消息用于刷新对话列表。 7. 返回新消息编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_019_000 | 客服会话不存在 |

### 2.2 更新客服消息已读状态

- **路径**: PUT /promotion/kefu-message/update-read-status
- **权限**: promotion:kefu-message:update
- **说明**: 将指定会话中对方发来的未读消息批量标记为已读，并将管理员未读计数归零；通过 WebSocket 通知双方刷新已读状态。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 是 | @RequestParam 必传 | 会话编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**: 1. 校验会话存在（KEFU_CONVERSATION_NOT_EXISTS）。 2. 会员端调用时会校验 userId 与会话归属一致，管理端（本接口）直接以当前登录管理员身份处理。 3. 查询会话内 senderType 不等于当前用户类型且 readStatus=false 的未读消息（管理员视角即会员发来的未读消息），为空则直接返回。 4. 批量更新这批消息的 readStatus=true（注释说明：多个客服场景下，一人点击已读则全部已读）。 5. 将会话的 adminUnreadMessageCount 归零。 6. 异步 WebSocket 推送 KEFU_MESSAGE_ADMIN_READ：通知发消息的会员刷新消息状态，并通知所有管理员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_019_000 | 客服会话不存在 |

### 2.3 获得客服消息列表

- **路径**: GET /promotion/kefu-message/list
- **权限**: promotion:kefu-message:query
- **说明**: 分批拉取指定会话的历史消息（按发送时间倒序取最新 limit 条），并拼接管理员发送者的头像；首次查询不带 createTime 取最新消息，翻历史时传入上一批最早消息的发送时间。

**请求参数 (KeFuMessageListReqVO)**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 是 | @NotNull | 会话编号 |
| createTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发送时间（查询该时间之前的历史消息） |
| limit | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每次查询条数，默认 10（Schema 描述写"最大值为 100"，实际校验上限为 200） |

**响应**: CommonResult&lt;List&lt;KeFuMessageRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 消息编号 |
| conversationId | Long | 会话编号 |
| senderId | Long | 发送人编号 |
| senderAvatar | String | 发送人头像（管理员发送的消息拼接 admin 用户头像） |
| senderType | Integer | 发送人类型（ADMIN/MEMBER） |
| receiverId | Long | 接收人编号 |
| receiverType | Integer | 接收人类型 |
| contentType | Integer | 消息类型（1 文本/2 图片/3 语音/4 视频/5 系统/10 商品/11 订单） |
| content | String | 消息内容 |
| readStatus | Boolean | 是否已读 |
| createTime | LocalDateTime | 创建时间（发送时间） |

**业务逻辑**: 1. 按条件查询消息：conversationId 精确匹配、createTime 小于匹配（如传）、按 createTime 倒序、最多返回 limit 条。 2. DO 列表转换为 KeFuMessageRespVO 列表。 3. 过滤出 senderType=ADMIN 的消息，按 senderId 批量调用 AdminUserApi.getUserMap，拼接 senderAvatar（会员发送的消息头像由前端/会员端处理）。

## 3. 域内错误码汇总（promotion 模块 ErrorCodeConstants）

| 错误码 | 说明 |
|-------|------|
| 1_013_019_000 | 客服会话不存在 |
| 1_013_020_000 | 客服消息不存在 |

> 补充说明：客服域的消息实时推送依赖 infra 的 WebSocketSenderApi，消息类型常量为 KEFU_MESSAGE_TYPE（新消息）、KEFU_MESSAGE_ADMIN_READ（管理员已读）；App 端对应的会话自动创建（getOrCreateConversation）与消息分页接口在 AppKeFuController 中，不在本文档范围。
