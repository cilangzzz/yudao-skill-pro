# AI 聊天对话与消息接口 (AiChatConversationController / AiChatMessageController)

> 提供 AI 聊天场景的对话管理（创建/更新/删除【我的】对话、管理员对话分页管理）与消息收发（段式/流式发送、知识库召回、联网搜索、附件解析与图片多模态、思考档位选择、Token 用量回传）能力。

## 接口路径前缀

- `/ai/chat/conversation` (Controller: AiChatConversationController)
- `/ai/chat/message` (Controller: AiChatMessageController)

---

## 1. 聊天对话【我的】（AiChatConversationController，仅登录用户，无需权限标识）

### 1.1 创建【我的】聊天对话

- **路径**: POST /ai/chat/conversation/create-my
- **权限**: 已认证（登录用户操作自己的数据）
- **说明**: 按聊天角色或默认模型创建一条属于当前登录用户的聊天对话。

**请求参数 (AiChatConversationCreateMyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| roleId | Long | 否 | - | 聊天角色编号 |
| knowledgeId | Long | 否 | - | 知识库编号 |

**响应**: CommonResult\<Long\>（新对话编号）

**业务逻辑**: 1. 若传了 roleId，校验聊天角色存在；角色绑定了模型则校验该模型，否则取系统的默认聊天模型。2. 校验模型 temperature/maxTokens/maxContexts 配置完整且为 CHAT 类型，否则抛 CHAT_CONVERSATION_MODEL_ERROR。3. 若传了 knowledgeId，校验知识库存在。4. 创建对话：绑定当前用户、pinned=false、模型及其温度/Token/上下文参数；有角色时标题、systemMessage 取自角色，否则使用默认标题。5. 插入并返回对话编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_003_001 | 操作失败，该聊天模型的配置不完整 |
| 1_040_002_000 | 聊天角色不存在（角色校验） |
| 1_040_001_000 | 模型不存在!（模型校验） |
| 1_040_009_000 | 知识库不存在!（知识库校验） |

### 1.2 更新【我的】聊天对话

- **路径**: PUT /ai/chat/conversation/update-my
- **权限**: 已认证
- **说明**: 更新当前用户的对话标题、置顶、模型、知识库、角色设定及模型参数。

**请求参数 (AiChatConversationUpdateMyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 对话编号 |
| title | String | 否 | - | 对话标题 |
| pinned | Boolean | 否 | - | 是否置顶 |
| modelId | Long | 否 | - | 模型编号 |
| knowledgeId | Long | 否 | - | 知识库编号 |
| systemMessage | String | 否 | - | 角色设定 |
| temperature | Double | 否 | - | 温度参数 |
| maxTokens | Integer | 否 | - | 单条回复的最大 Token 数量 |
| maxContexts | Integer | 否 | - | 上下文的最大 Message 数量 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验对话存在，且 userId 属于当前登录用户，否则抛 CHAT_CONVERSATION_NOT_EXISTS。2. 修改了 modelId 时校验模型存在。3. 修改了 knowledgeId 时校验知识库存在。4. 置顶时记录 pinnedTime 为当前时间；改模型时同步更新 model 标志字段。5. 执行更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_003_000 | 对话不存在! |
| 1_040_001_000 | 模型不存在!（模型校验） |
| 1_040_009_000 | 知识库不存在!（知识库校验） |

### 1.3 获得【我的】聊天对话列表

- **路径**: GET /ai/chat/conversation/my-list
- **权限**: 已认证
- **说明**: 获得当前登录用户的全部聊天对话列表。

**请求参数**: 无

**响应**: CommonResult\<List\<AiChatConversationRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 对话编号 |
| userId | Long | 用户编号 |
| title | String | 对话标题 |
| pinned | Boolean | 是否置顶 |
| roleId | Long | 角色编号（@Trans 自动翻译出 roleName/roleAvatar） |
| modelId | Long | 模型编号（@Trans 自动翻译出 modelName 与 modelReasoningConfig） |
| model | String | 模型标志 |
| modelName | String | 模型名字 |
| modelReasoningConfig | ReasoningConfig | 关联模型的思考配置（`levels` + `defaultLevel`），为空表示模型未配置思考；用于前端渲染思考档位选择 |
| systemMessage | String | 角色设定 |
| temperature | Double | 温度参数 |
| maxTokens | Integer | 单条回复的最大 Token 数量 |
| maxContexts | Integer | 上下文的最大 Message 数量 |
| createTime | LocalDateTime | 创建时间 |
| roleAvatar | String | 角色头像（关联翻译） |
| roleName | String | 角色名字（关联翻译） |
| messageCount | Integer | 消息数量（仅【对话管理】加载） |

**业务逻辑**: 1. 按当前登录用户查询其全部对话列表并返回。

### 1.4 获得【我的】聊天对话

- **路径**: GET /ai/chat/conversation/get-my
- **权限**: 已认证
- **说明**: 按 id 获得对话详情，仅当对话属于当前用户时返回。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 对话编号 |

**响应**: CommonResult\<AiChatConversationRespVO\>（字段同 1.3）

**业务逻辑**: 1. 按 id 查询对话。2. 若对话存在但 userId 不等于当前登录用户，则视为不存在返回 null。

### 1.5 删除聊天对话

- **路径**: DELETE /ai/chat/conversation/delete-my
- **权限**: 已认证
- **说明**: 删除当前用户自己的指定对话。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 对话编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验对话存在且属于当前用户，否则抛 CHAT_CONVERSATION_NOT_EXISTS。2. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_003_000 | 对话不存在! |

### 1.6 删除未置顶的聊天对话

- **路径**: DELETE /ai/chat/conversation/delete-by-unpinned
- **权限**: 已认证
- **说明**: 一键清空当前用户所有未置顶的对话。

**请求参数**: 无

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 查询当前用户 pinned=false 的对话列表。2. 列表为空直接返回。3. 批量删除这些对话。

## 2. 聊天对话管理（AiChatConversationController，需管理员权限）

### 2.1 获得对话分页

- **路径**: GET /ai/chat/conversation/page
- **权限**: ai:chat-conversation:query
- **说明**: 分页查询全部用户的对话，用于【对话管理】菜单，附带消息数量。

**请求参数 (AiChatConversationPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 否 | - | 用户编号 |
| title | String | 否 | - | 对话标题（模糊查询） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| pageNo | Integer | 否 | PageParam | 页码 |
| pageSize | Integer | 否 | PageParam | 每页条数 |

**响应**: CommonResult\<PageResult\<AiChatConversationRespVO\>\>（字段同 1.3，含 messageCount）

**业务逻辑**: 1. 按条件分页查询对话。2. 结果为空返回空分页。3. 按对话编号批量统计各对话的消息数量。4. 组装 messageCount 后返回。

### 2.2 获得对话

- **路径**: GET /ai/chat/conversation/get
- **权限**: ai:chat-conversation:query
- **说明**: 管理端按 id 获得对话详情，附带消息数量。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 对话编号 |

**响应**: CommonResult\<AiChatConversationRespVO\>（字段同 1.3，含 messageCount）

**业务逻辑**: 1. 按 id 查询对话并转 RespVO。2. 统计该对话的消息数量填充 messageCount。

### 2.3 管理员删除对话

- **路径**: DELETE /ai/chat/conversation/delete-by-admin
- **权限**: ai:chat-conversation:delete
- **说明**: 管理员删除任意用户的对话。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 对话编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验对话存在，否则抛 CHAT_CONVERSATION_NOT_EXISTS。2. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_003_000 | 对话不存在! |

## 3. 聊天消息发送与查看（AiChatMessageController，仅登录用户）

### 3.1 发送消息（段式）

- **路径**: POST /ai/chat/message/send
- **权限**: 已认证
- **说明**: 一次性返回 AI 回复（响应较慢），支持知识库召回、联网搜索、附件。

**请求参数 (AiChatMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 是 | @NotNull | 聊天对话编号 |
| content | String | 是 | @NotEmpty | 聊天内容 |
| useContext | Boolean | 否 | - | 是否携带上下文 |
| useSearch | Boolean | 否 | - | 是否联网搜索 |
| attachmentUrls | List\<String\> | 否 | - | 附件 URL 数组 |
| reasoningLevel | String | 否 | - | 本次思考档位；为空表示使用模型默认档位，模型未配置档位时必须为空（否则报 MODEL_REASONING_NOT_CONFIGURED） |

**响应**: CommonResult\<AiChatMessageSendRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| send | Message | 发送消息（用户消息） |
| receive | Message | 接收消息（AI 回复） |
| Message.id | Long | 编号 |
| Message.type | String | 消息类型（user/assistant/system） |
| Message.content | String | 聊天内容 |
| Message.reasoningContent | String | 推理内容（思维链） |
| Message.segmentIds | List\<Long\> | 知识库段落编号数组 |
| Message.segments | List\<KnowledgeSegment\> | 知识库段落数组（id/content/documentId/documentName） |
| Message.webSearchPages | List\<WebPage\> | 联网搜索的网页内容数组 |
| Message.createTime | LocalDateTime | 创建时间 |
| Message.inputTokens | Long | 输入 Token 数（未知为空） |
| Message.outputTokens | Long | 输出 Token 数（未知为空） |
| Message.totalTokens | Long | 合计 Token 数（输入、输出都已知时才有值） |

**业务逻辑**: 1. 校验对话存在且属于当前用户（事务内）。2. 加载对话历史消息，校验对话模型，解析本次思考参数（已配置思考时校验模型平台、ApiKey 平台一致、档位存在与平台路由；未配置时请求带档位直接报错），再按 `modelId + 思考参数` 获得 ChatModel。3. 若对话绑定了角色且角色配置了知识库，逐个知识库做段落向量召回；useSearch=true 且开启联网搜索时执行网络搜索（取前 10 条）。4. 构建 Prompt：system 角色设定 + 上下文历史消息（按 maxContexts 取最近 n 组 user+assistant，需 useContext=true）+ 当前用户消息 + 知识库参考（Reference 模板）+ 联网搜索参考（WebSearch 模板）+ 附件内容（模型 `input_modalities` 含 image 的图片以 `Media` 与文本放入同一条 UserMessage；其余图片转 Base64、其他读取文本走 Attachment 模板），并按平台构建 ChatOptions（含角色配置的工具 ToolCallback、MCP 工具与思考参数）。**Prompt 在插入消息前构建**，图片读取失败会抛 CHAT_MESSAGE_IMAGE_READ_FAIL 且不留下任何消息。5. 插入 user 类型消息，并插入 assistant 占位消息（记录召回段落编号、联网结果、`requestId`）。6. 同步调用模型获取回复；调用异常时仍记录 FAIL 请求日志并抛出。7. 将 content/reasoningContent 与 Token 用量更新到 assistant 消息，并记录 SUCCESS 请求日志。8. 组装知识库段落（含文档名）与搜索网页，返回 send/receive 消息（含用量）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_003_000 | 对话不存在! |
| 1_040_001_000 | 模型不存在!（模型校验） |
| 1_040_001_004 | 该模型未配置思考档位，请刷新页面后重试 |
| 1_040_001_005 | 该模型不支持思考档位({})，请刷新页面后重试 |
| 1_040_001_006 | 平台({})暂不支持思考配置 |
| 1_040_001_007 | 模型平台({})与 API 密钥平台({})不一致，无法使用思考配置 |
| 1_040_001_009 | 思考配置不正确：{} |
| 1_040_004_002 | 读取图片附件({})失败，请重新上传后重试 |

### 3.2 发送消息（流式）

- **路径**: POST /ai/chat/message/send-stream（produces: text/event-stream）
- **权限**: 已认证
- **说明**: 以 SSE 流式返回 AI 回复（响应较快），前置处理与段式一致。

**请求参数 (AiChatMessageSendReqVO)**: 同 3.1

**响应**: Flux\<CommonResult\<AiChatMessageSendRespVO\>\>（每帧结构同 3.1，content/reasoningContent 为增量片段；首帧附带知识库 segments 与联网搜索 webSearchPages；每帧的 receive 消息带 inputTokens/outputTokens/totalTokens，取请求日志的最新用量快照）

**业务逻辑**: 1. 校验对话归属与模型（同段式）。2. 知识库召回与联网搜索（同段式）。3. **思考校验失败**（模型未配置档位却传入档位、档位不存在、平台不支持、平台与 ApiKey 不一致）时直接返回一个错误帧，不调用模型、不落消息。4. 插入 user 消息与 assistant 占位消息（带 `requestId`）。5. 构建 Prompt 并调用 StreamingChatModel 得到 Flux\<ChatResponse\>；**图片读取失败时返回错误帧且不落消息**。6. 流式 map：用 CAS 保证知识库段落/搜索网页仅首次计算缓存；逐帧累积 content 与 reasoningContent，并把最新用量快照随帧下发。7. doOnComplete：按请求开始时捕获的 tenantId 回写 assistant 消息与用量，并记录 SUCCESS 请求日志。8. doOnError/doOnCancel：分别记录 FAIL/CANCEL 请求日志；有部分内容则回写保留，无内容则删除 assistant 占位消息。9. onErrorResume：流异常时返回 CHAT_STREAM_ERROR 错误帧。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_003_000 | 对话不存在! |
| 1_040_004_001 | 对话生成异常! |
| 1_040_004_002 | 读取图片附件({})失败，请重新上传后重试（以错误帧返回） |
| 1_040_001_004 | 该模型未配置思考档位，请刷新页面后重试（以错误帧返回） |
| 1_040_001_005 | 该模型不支持思考档位({})，请刷新页面后重试（以错误帧返回） |
| 1_040_001_006 | 平台({})暂不支持思考配置（以错误帧返回） |
| 1_040_001_007 | 模型平台({})与 API 密钥平台({})不一致，无法使用思考配置（以错误帧返回） |
| 1_040_001_009 | 思考配置不正确：{}（以错误帧返回） |

### 3.3 获得指定对话的消息列表

- **路径**: GET /ai/chat/message/list-by-conversation-id
- **权限**: 已认证
- **说明**: 获得当前用户指定对话下的全部消息，并拼接知识库段落信息。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 是 | @RequestParam | 对话编号 |

**响应**: CommonResult\<List\<AiChatMessageRespVO\>\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| conversationId | Long | 对话编号 |
| replyId | Long | 回复消息编号 |
| type | String | 消息类型（user/assistant/system） |
| userId | Long | 用户编号 |
| roleId | Long | 角色编号 |
| model | String | 模型标志 |
| modelId | Long | 模型编号 |
| content | String | 聊天内容 |
| reasoningContent | String | 推理内容 |
| useContext | Boolean | 是否携带上下文 |
| segmentIds | List\<Long\> | 知识库段落编号数组 |
| segments | List\<KnowledgeSegment\> | 知识库段落数组（id/content/documentId/documentName） |
| webSearchPages | List\<WebPage\> | 联网搜索的网页内容数组 |
| attachmentUrls | List\<String\> | 附件 URL 数组 |
| createTime | LocalDateTime | 创建时间 |
| requestId | String | 请求编号（本地 UUID，关联 ai_request_log.request_id；仅 assistant 消息有值） |
| inputTokens | Long | 输入 Token 数（未知为空） |
| outputTokens | Long | 输出 Token 数（未知为空） |
| totalTokens | Long | 合计 Token 数（输入、输出都已知时才有值） |
| roleName | String | 角色名字（仅【对话管理】加载） |

**业务逻辑**: 1. 查询对话，若不存在或不属于当前用户则返回空列表。2. 查询该对话全部消息，为空返回空列表。3. 批量查询消息引用的知识库段落及对应文档。4. 为每条消息的 segments 填充段落内容、文档编号与文档名称。

### 3.4 删除消息

- **路径**: DELETE /ai/chat/message/delete
- **权限**: 已认证
- **说明**: 删除当前用户自己的指定消息。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 消息编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验消息存在且属于当前用户，否则抛 CHAT_MESSAGE_NOT_EXIST。2. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_004_000 | 消息不存在! |

### 3.5 删除指定对话的消息

- **路径**: DELETE /ai/chat/message/delete-by-conversation-id
- **权限**: 已认证
- **说明**: 清空当前用户指定对话下的全部消息。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 是 | @RequestParam | 对话编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 查询该对话全部消息，为空或首条消息不属于当前用户则抛 CHAT_MESSAGE_NOT_EXIST。2. 批量删除这些消息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_004_000 | 消息不存在! |

## 4. 聊天消息管理（AiChatMessageController，需管理员权限）

### 4.1 获得消息分页

- **路径**: GET /ai/chat/message/page
- **权限**: ai:chat-message:query
- **说明**: 分页查询全部消息，用于【对话管理】菜单，附带角色名字。

**请求参数 (AiChatMessagePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| conversationId | Long | 否 | - | 对话编号 |
| userId | Long | 否 | - | 用户编号 |
| content | String | 否 | - | 消息内容（模糊查询） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| pageNo | Integer | 否 | PageParam | 页码 |
| pageSize | Integer | 否 | PageParam | 每页条数 |

**响应**: CommonResult\<PageResult\<AiChatMessageRespVO\>\>（字段同 3.3，含 roleName）

**业务逻辑**: 1. 按条件分页查询消息。2. 结果为空返回空分页。3. 批量查询消息关联的聊天角色，为每条消息填充 roleName。

### 4.2 获得消息

- **路径**: GET /ai/chat/message/get
- **权限**: ai:chat-message:query
- **说明**: 管理端按 id 获得消息详情，附带角色名字。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 消息编号 |

**响应**: CommonResult\<AiChatMessageRespVO\>（字段同 3.3，含 roleName）

**业务逻辑**: 1. 按 id 查询消息并转 RespVO。2. 若消息绑定了 roleId，查询角色并填充 roleName。

### 4.3 管理员删除消息

- **路径**: DELETE /ai/chat/message/delete-by-admin
- **权限**: ai:chat-message:delete
- **说明**: 管理员删除任意用户的消息。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 消息编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验消息存在，否则抛 CHAT_MESSAGE_NOT_EXIST。2. 执行删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_004_000 | 消息不存在! |
