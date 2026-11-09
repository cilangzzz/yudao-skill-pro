# AI 模型管理（密钥/模型/角色/工具）接口 (AiApiKeyController / AiModelController / AiChatRoleController / AiToolController)

> 管理 AI 平台的底层配置：API 密钥、模型、聊天角色（含【我的】角色）与 AI 工具（Function Calling），供对话、绘图、音乐、知识库等上层功能引用。

## 接口路径前缀

- `/ai/api-key` (Controller: AiApiKeyController) — API 密钥管理
- `/ai/model` (Controller: AiModelController) — AI 模型管理
- `/ai/chat-role` (Controller: AiChatRoleController) — 聊天角色管理
- `/ai/tool` (Controller: AiToolController) — AI 工具管理

---

## 1. API 密钥（AiApiKeyController）

### 1.1 创建 API 密钥

- **路径**: POST /ai/api-key/create
- **权限**: ai:api-key:create
- **说明**: 新增一条平台 API 密钥配置

**请求参数 (AiApiKeySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 新增时否 | - | 编号 |
| name | String | 是 | @NotEmpty | 名称，如「文心一言」 |
| apiKey | String | 是 | @NotEmpty | 密钥 |
| platform | String | 是 | @NotEmpty | 平台，如「OpenAI」 |
| url | String | 否 | - | 自定义 API 地址 |
| status | Integer | 是 | @NotNull | 状态（0 开启 / 1 关闭，CommonStatusEnum） |

**响应**: CommonResult&lt;Long&gt; — 密钥编号

**业务逻辑**: 1. 将请求 VO 转换为 AiApiKeyDO；2. 直接插入数据库（不做平台合法性校验）；3. 返回新记录编号。

### 1.2 更新 API 密钥

- **路径**: PUT /ai/api-key/update
- **权限**: ai:api-key:update
- **说明**: 按编号更新密钥配置

**请求参数 (AiApiKeySaveReqVO)**: 同 1.1，其中 id 必传

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验密钥是否存在，不存在抛 API_KEY_NOT_EXISTS；2. VO 转 AiApiKeyDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_000_000 | API 密钥不存在 |

### 1.3 删除 API 密钥

- **路径**: DELETE /ai/api-key/delete
- **权限**: ai:api-key:delete
- **说明**: 按编号删除密钥

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验密钥存在；2. 按 id 物理删除（BaseDO 逻辑删除）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_000_000 | API 密钥不存在 |

### 1.4 获得 API 密钥

- **路径**: GET /ai/api-key/get
- **权限**: ai:api-key:query
- **说明**: 按编号查询单个密钥

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;AiApiKeyRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名称 |
| apiKey | String | 密钥 |
| platform | String | 平台 |
| url | String | 自定义 API 地址 |
| status | Integer | 状态 |

**业务逻辑**: 1. 按 id selectById 查询；2. BeanUtils 转 RespVO 返回（不存在时返回 null）。

### 1.5 获得 API 密钥分页

- **路径**: GET /ai/api-key/page
- **权限**: ai:api-key:query
- **说明**: 分页查询密钥列表

**请求参数 (AiApiKeyPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承自 PageParam，默认 1） | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承自 PageParam，默认 10） | 每页条数 |
| name | String | 否 | - | 名称，模糊匹配 |
| platform | String | 否 | - | 平台，精确匹配 |
| status | Integer | 否 | - | 状态 |

**响应**: CommonResult&lt;PageResult&lt;AiApiKeyRespVO&gt;&gt; — 列表项字段同 1.4

**业务逻辑**: 1. 按名称 LIKE、平台/状态等值条件构造查询；2. 按 id 倒序分页返回。

### 1.6 获得 API 密钥精简列表

- **路径**: GET /ai/api-key/simple-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 获取全部密钥的下拉精简列表（供模型配置选择密钥）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;AiModelRespVO&gt;&gt;（仅填充 id、name 两个字段）

**业务逻辑**: 1. 查询全部密钥列表（不过滤状态）；2. 转换为 AiModelRespVO，仅设置 id 与 name。

---

## 2. AI 模型（AiModelController）

### 2.1 创建模型

- **路径**: POST /ai/model/create
- **权限**: ai:model:create
- **说明**: 新增一个模型配置，绑定某个 API 密钥

**请求参数 (AiModelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 新增时否 | - | 编号 |
| keyId | Long | 是 | @NotNull | API 密钥编号 |
| name | String | 是 | @NotEmpty | 模型名字 |
| model | String | 是 | @NotEmpty | 模型标识，如 gpt-3.5-turbo-0125 |
| platform | String | 是 | @NotEmpty、@InEnum(AiPlatformEnum) | 模型平台 |
| type | Integer | 是 | @NotNull、@InEnum(AiModelTypeEnum) | 模型类型（1 对话 / 2 图片 / 3 语音 / 4 视频 / 5 向量 / 6 重排序） |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 关闭） |
| temperature | Double | 否 | - | 温度参数 |
| maxTokens | Integer | 否 | - | 单条回复的最大 Token 数量 |
| maxContexts | Integer | 否 | - | 上下文的最大 Message 数量 |
| inputModalities | List\<String\> | 否 | @InEnum(AiModelInputModalityEnum) | 输入模态数组，取值 text / image / video；仅对话模型（type=1）使用，为空视为仅支持 text |
| reasoningConfig | ReasoningConfig | 否 | - | 思考配置（`levels` + `defaultLevel`）；null 或 `levels` 为 [] 表示不配置思考（更新时清空） |

**思考配置 (ReasoningConfig) 与思考档位 (ReasoningLevel)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| levels | List\<ReasoningLevel\> | 是 | @NotNull、@Valid（元素 @NotNull、档位值不能重复） | 档位数组，从低到高；`[]` 表示清空思考配置 |
| defaultLevel | String | 否 | @AssertTrue（必须在 levels 中；levels 为空时不能传） | 默认档位 |
| ReasoningLevel.level | String | 是 | @NotNull、@Pattern(`^[a-z0-9_-]{1,32}$`) | 档位值，`off` 表示关闭思考 |
| ReasoningLevel.options | Map\<String, Object\> | 是 | @NotNull、@AssertTrue（任意层级不允许 null） | 该档位的思考参数（JSON 对象） |

**响应**: CommonResult&lt;Long&gt; — 模型编号

**业务逻辑**: 1. AiPlatformEnum.validatePlatform 校验平台合法；2. apiKeyService.validateApiKey 校验密钥存在且未禁用（否则抛 MODEL_NOT_EXISTS 相关联的 API_KEY_NOT_EXISTS / API_KEY_DISABLE）；3. VO 转 AiModelDO；4. 校验思考配置（仅配置了思考时才校验）：模型类型必须为 CHAT、模型平台必须与 API 密钥平台一致、平台必须支持思考路由、每档 options 的顶层键需符合该路由规则（HTTP 路由禁止 model/messages/stream/stream_options/tools/tool_choice；OPENAI 路由禁止与强类型字段同名且 reasoning_effort 必须是非空字符串；通义只认 enable_thinking 布尔值与 thinking_budget 正整数）；5. 未配置思考（null 或 levels 为空）时把 reasoningConfig 归一为 null 后插入；6. 返回模型编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_000_000 | API 密钥不存在 |
| 1_040_000_001 | API 密钥已禁用！ |
| 1_040_001_007 | 模型平台({})与 API 密钥平台({})不一致，无法使用思考配置 |
| 1_040_001_006 | 平台({})暂不支持思考配置 |
| 1_040_001_009 | 思考配置不正确：{} |

### 2.2 更新模型

- **路径**: PUT /ai/model/update
- **权限**: ai:model:update
- **说明**: 按编号更新模型配置

**请求参数 (AiModelSaveReqVO)**: 同 2.1，其中 id 必传

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验模型存在（MODEL_NOT_EXISTS）；2. 校验平台合法；3. 校验密钥存在且未禁用；4. 思考配置校验同 2.1；5. 未配置思考时把 reasoningConfig 归一为 null，并通过 `AiChatMapper#updateForSave` 以一条 UPDATE 显式把该列置空（否则 MyBatis-Plus 的 null 字段不会出现在 UPDATE 语句中，旧的思考配置会残留）；6. 按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_001_000 | 模型不存在! |
| 1_040_000_000 | API 密钥不存在 |
| 1_040_000_001 | API 密钥已禁用！ |
| 1_040_001_007 | 模型平台({})与 API 密钥平台({})不一致，无法使用思考配置 |
| 1_040_001_006 | 平台({})暂不支持思考配置 |
| 1_040_001_009 | 思考配置不正确：{} |

### 2.3 删除模型

- **路径**: DELETE /ai/model/delete
- **权限**: ai:model:delete
- **说明**: 按编号删除模型

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验模型存在；2. 按 id 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_001_000 | 模型不存在! |

### 2.4 获得模型

- **路径**: GET /ai/model/get
- **权限**: ai:model:query
- **说明**: 按编号查询单个模型

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;AiModelRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| keyId | Long | API 密钥编号 |
| name | String | 模型名字 |
| model | String | 模型标识 |
| platform | String | 模型平台 |
| type | Integer | 模型类型 |
| sort | Integer | 排序 |
| status | Integer | 状态 |
| temperature | Double | 温度参数 |
| maxTokens | Integer | 单条回复的最大 Token 数量 |
| maxContexts | Integer | 上下文的最大 Message 数量 |
| inputModalities | List\<String\> | 输入模态数组（text / image / video），为空视为仅支持 text |
| reasoningConfig | ReasoningConfig | 思考配置（`levels` + `defaultLevel`），为空表示未配置思考 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询；2. 转 RespVO 返回（不存在时返回 null）。

### 2.5 获得模型分页

- **路径**: GET /ai/model/page
- **权限**: ai:model:query
- **说明**: 分页查询模型列表

**请求参数 (AiModelPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo / pageSize | Integer | 是 | 同 PageParam（见 1.5） | 分页参数 |
| name | String | 否 | - | 模型名字，模糊匹配 |
| model | String | 否 | - | 模型标识 |
| platform | String | 否 | - | 模型平台 |

**响应**: CommonResult&lt;PageResult&lt;AiModelRespVO&gt;&gt; — 列表项字段同 2.4

**业务逻辑**: 1. 按名称/标识/平台条件构造查询；2. 分页返回。

### 2.6 获得模型精简列表

- **路径**: GET /ai/model/simple-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 获取指定类型（可选平台）下启用模型的精简列表

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| type | Integer | 是 | - | 模型类型 |
| platform | String | 否 | - | 平台，如 midjourney |

**响应**: CommonResult&lt;List&lt;AiModelRespVO&gt;&gt;（仅填充 id、name、model、platform、inputModalities 五个字段；不返回 reasoningConfig）

**业务逻辑**: 1. 按状态=开启、类型、平台（可选）查询模型列表；2. 转精简 RespVO 返回（含 inputModalities，供前端判断模型是否支持图片输入）。

---

## 3. 聊天角色（AiChatRoleController）

> 分为【我的】角色（面向登录用户，无权限点）与角色管理（面向管理员，需 ai:chat-role:* 权限）两组。RespVO 实现了 trans 接口，modelId 会自动翻译出 modelName / model 字段。

### 3.1 获得【我的】聊天角色分页

- **路径**: GET /ai/chat-role/my-page
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 当前用户可见的角色分页（公开角色 + 本人私有角色）

**请求参数 (AiChatRolePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo / pageSize | Integer | 是 | 同 PageParam（见 1.5） | 分页参数 |
| name | String | 否 | - | 角色名称，模糊匹配 |
| category | String | 否 | - | 角色类别，精确匹配 |
| publicStatus | Boolean | 否 | - | 是否公开：true 查公开角色；false 查本人私有且启用的角色；不传查全部（含公开与本人角色） |

**响应**: CommonResult&lt;PageResult&lt;AiChatRoleRespVO&gt;&gt; — 字段见 3.10

**业务逻辑**: 1. 以当前登录用户 id 调用 selectPageByMy；2. 名称 LIKE、类别等值过滤，按 sort 升序；3. publicStatus=true 时仅查公开角色，=false 时追加 userId=当前用户 且 status=启用 条件。

### 3.2 获得【我的】聊天角色

- **路径**: GET /ai/chat-role/get-my
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 按编号获取角色详情，仅当角色属于当前用户时返回

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;AiChatRoleRespVO&gt;（非本人角色时 data 为 null）

**业务逻辑**: 1. 查询角色；2. 角色 userId 与当前登录用户不一致时返回 null；3. 否则转 RespVO 返回。

### 3.3 创建【我的】聊天角色

- **路径**: POST /ai/chat-role/create-my
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 用户自建聊天角色，强制归属本人、状态开启且不公开

**请求参数 (AiChatRoleSaveMyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 角色编号（创建时不传） |
| name | String | 是 | @NotEmpty | 角色名称 |
| avatar | String | 是 | @NotEmpty、@URL | 角色头像，URL 格式 |
| description | String | 是 | @NotEmpty | 角色描述 |
| systemMessage | String | 是 | @NotEmpty | 角色设定（System 提示词） |
| knowledgeIds | List&lt;Long&gt; | 否 | - | 引用的知识库编号列表 |
| toolIds | List&lt;Long&gt; | 否 | - | 引用的工具编号列表 |
| mcpClientNames | List&lt;String&gt; | 否 | - | 引用的 MCP Client 名字列表 |

**响应**: CommonResult&lt;Long&gt; — 角色编号

**业务逻辑**: 1. 逐个校验 knowledgeIds 对应知识库存在（KNOWLEDGE_NOT_EXISTS）；2. 逐个校验 toolIds 对应工具存在（TOOL_NOT_EXISTS）；3. 转 DO 并强制设置 userId=当前用户、status=开启、publicStatus=false；4. 插入并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在 |
| 1_040_010_000 | 工具不存在 |

### 3.4 更新【我的】聊天角色

- **路径**: PUT /ai/chat-role/update-my
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 更新本人创建的聊天角色

**请求参数 (AiChatRoleSaveMyReqVO)**: 同 3.3，其中 id 必传

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验角色存在；2. 角色 userId 与当前用户不一致时抛 CHAT_ROLE_NOT_EXISTS；3. 校验知识库、工具存在；4. 转 DO 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_002_000 | 聊天角色不存在 |
| 1_040_009_000 | 知识库不存在 |
| 1_040_010_000 | 工具不存在 |

### 3.5 删除【我的】聊天角色

- **路径**: DELETE /ai/chat-role/delete-my
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 删除本人创建的聊天角色

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验角色存在；2. 校验归属当前用户，否则抛 CHAT_ROLE_NOT_EXISTS；3. 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_002_000 | 聊天角色不存在 |

### 3.6 获得聊天角色的分类列表

- **路径**: GET /ai/chat-role/category-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 获取启用角色的类别去重列表，用于前端分类筛选

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;String&gt;&gt;

**业务逻辑**: 1. 按 status=启用 分组查询 category 字段；2. 过滤空白类别后返回。

### 3.7 创建聊天角色（管理）

- **路径**: POST /ai/chat-role/create
- **权限**: ai:chat-role:create
- **说明**: 管理员创建聊天角色（可配置公开状态、绑定模型/知识库/工具）

**请求参数 (AiChatRoleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 角色编号（创建时不传） |
| modelId | Long | 否 | - | 模型编号 |
| name | String | 是 | @NotEmpty | 角色名称 |
| avatar | String | 是 | @NotEmpty、@URL | 角色头像 |
| category | String | 是 | @NotEmpty | 角色类别 |
| sort | Integer | 是 | @NotNull | 角色排序 |
| description | String | 是 | @NotEmpty | 角色描述 |
| systemMessage | String | 是 | @NotEmpty | 角色设定 |
| knowledgeIds | List&lt;Long&gt; | 否 | - | 引用的知识库编号列表 |
| toolIds | List&lt;Long&gt; | 否 | - | 引用的工具编号列表 |
| mcpClientNames | List&lt;String&gt; | 否 | - | 引用的 MCP Client 名字列表 |
| publicStatus | Boolean | 是 | @NotNull | 是否公开 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 关闭） |

**响应**: CommonResult&lt;Long&gt; — 角色编号

**业务逻辑**: 1. 校验知识库存在；2. 校验工具存在；3. 转 AiChatRoleDO 插入（userId 不设置，即系统级角色）；4. 返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在 |
| 1_040_010_000 | 工具不存在 |

### 3.8 更新聊天角色（管理）

- **路径**: PUT /ai/chat-role/update
- **权限**: ai:chat-role:update
- **说明**: 管理员更新聊天角色

**请求参数 (AiChatRoleSaveReqVO)**: 同 3.7，其中 id 必传

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验角色存在；2. 校验知识库存在；3. 校验工具存在；4. 转 DO 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_002_000 | 聊天角色不存在 |
| 1_040_009_000 | 知识库不存在 |
| 1_040_010_000 | 工具不存在 |

### 3.9 删除聊天角色（管理）

- **路径**: DELETE /ai/chat-role/delete
- **权限**: ai:chat-role:delete
- **说明**: 管理员删除聊天角色

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验角色存在；2. 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_002_000 | 聊天角色不存在 |

### 3.10 获得聊天角色（管理）

- **路径**: GET /ai/chat-role/get
- **权限**: ai:chat-role:query
- **说明**: 按编号获取角色详情（含模型名称翻译）

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;AiChatRoleRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 角色编号 |
| userId | Long | 用户编号（【我的】角色归属） |
| modelId | Long | 模型编号 |
| modelName | String | 模型名字（@Trans 根据 modelId 自动翻译） |
| model | String | 模型标识（@Trans 自动翻译） |
| name | String | 角色名称 |
| avatar | String | 角色头像 |
| category | String | 角色类别 |
| sort | Integer | 角色排序 |
| description | String | 角色描述 |
| systemMessage | String | 角色设定 |
| knowledgeIds | List&lt;Long&gt; | 引用的知识库编号列表 |
| toolIds | List&lt;Long&gt; | 引用的工具编号列表 |
| mcpClientNames | List&lt;String&gt; | 引用的 MCP Client 名字列表 |
| publicStatus | Boolean | 是否公开 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询角色；2. 转 RespVO 返回（modelId 经 @TransMethodResult 翻译出 modelName / model）。

### 3.11 获得聊天角色分页（管理）

- **路径**: GET /ai/chat-role/page
- **权限**: ai:chat-role:query
- **说明**: 管理端分页查询全部角色

**请求参数 (AiChatRolePageReqVO)**: 同 3.1

**响应**: CommonResult&lt;PageResult&lt;AiChatRoleRespVO&gt;&gt; — 字段见 3.10

**业务逻辑**: 1. 按名称 LIKE、类别/公开状态等值过滤；2. 按 sort 升序分页返回。

---

## 4. AI 工具（AiToolController）

> 工具即 Spring AI Function Calling 的工具配置：数据库仅保存名称/描述/状态，工具名必须能通过 ToolCallbackResolver 解析到容器中的 ToolCallback Bean。

### 4.1 创建工具

- **路径**: POST /ai/tool/create
- **权限**: ai:tool:create
- **说明**: 登记一个 AI 工具（名称必须对应 Spring 容器中的工具 Bean）

**请求参数 (AiToolSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 工具编号（创建时不传） |
| name | String | 是 | @NotEmpty | 工具名称（须为容器中的 ToolCallback Bean 名） |
| description | String | 否 | - | 工具描述 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态 |

**响应**: CommonResult&lt;Long&gt; — 工具编号

**业务逻辑**: 1. 通过 ToolCallbackResolver.resolve(name) 校验工具名能解析到 Bean，否则抛 TOOL_NAME_NOT_EXISTS；2. 转 AiToolDO 插入；3. 返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_010_001 | 工具({})找不到 Bean |

### 4.2 更新工具

- **路径**: PUT /ai/tool/update
- **权限**: ai:tool:update
- **说明**: 按编号更新工具

**请求参数 (AiToolSaveReqVO)**: 同 4.1，其中 id 必传

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验工具存在（TOOL_NOT_EXISTS）；2. 校验工具名能解析到 Bean；3. 转 DO 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_010_000 | 工具不存在 |
| 1_040_010_001 | 工具({})找不到 Bean |

### 4.3 删除工具

- **路径**: DELETE /ai/tool/delete
- **权限**: ai:tool:delete
- **说明**: 按编号删除工具

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; — 固定 true

**业务逻辑**: 1. 校验工具存在；2. 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_010_000 | 工具不存在 |

### 4.4 获得工具

- **路径**: GET /ai/tool/get
- **权限**: ai:tool:query
- **说明**: 按编号查询单个工具

**请求参数**: 无（Query 参数 id：Long，必填，编号）

**响应**: CommonResult&lt;AiToolRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 工具编号 |
| name | String | 工具名称 |
| description | String | 工具描述 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询；2. 转 RespVO 返回（不存在时返回 null）。

### 4.5 获得工具分页

- **路径**: GET /ai/tool/page
- **权限**: ai:tool:query
- **说明**: 分页查询工具列表

**请求参数 (AiToolPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo / pageSize | Integer | 是 | 同 PageParam（见 1.5） | 分页参数 |
| name | String | 否 | - | 工具名称 |
| description | String | 否 | - | 工具描述 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;AiToolRespVO&gt;&gt; — 列表项字段同 4.4

**业务逻辑**: 1. 按名称/描述/状态/创建时间区间构造查询；2. 分页返回。

### 4.6 获得工具精简列表

- **路径**: GET /ai/tool/simple-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 获取全部启用工具的精简列表（供角色配置引用）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;AiToolRespVO&gt;&gt;（仅填充 id、name 两个字段）

**业务逻辑**: 1. 按 status=开启查询工具列表；2. 转精简 RespVO 返回。

---

## 附：本域错误码汇总（ErrorCodeConstants，1-040 段）

| 错误码 | 说明 | 所属 |
|-------|------|------|
| 1_040_000_000 | API 密钥不存在 | API 密钥 |
| 1_040_000_001 | API 密钥已禁用！ | API 密钥 |
| 1_040_000_002 | AI 配置({})无法解析，请检查环境变量或配置项 | API 密钥 |
| 1_040_001_000 | 模型不存在! | 模型 |
| 1_040_001_001 | 模型({})已禁用! | 模型 |
| 1_040_001_002 | 操作失败，找不到默认模型 | 模型 |
| 1_040_001_003 | 操作失败，该模型的模型类型不正确 | 模型 |
| 1_040_001_004 | 该模型未配置思考档位，请刷新页面后重试 | 模型（发送时校验） |
| 1_040_001_005 | 该模型不支持思考档位({})，请刷新页面后重试 | 模型（发送时校验） |
| 1_040_001_006 | 平台({})暂不支持思考配置 | 模型（保存/发送时校验） |
| 1_040_001_007 | 模型平台({})与 API 密钥平台({})不一致，无法使用思考配置 | 模型（保存/发送时校验） |
| 1_040_001_009 | 思考配置不正确：{} | 模型（保存/发送时校验） |
| 1_040_002_000 | 聊天角色不存在 | 聊天角色 |
| 1_040_001_001 | 聊天角色({})已禁用!（源码中与模型禁用共用同一编号） | 聊天角色 |
| 1_040_009_000 | 知识库不存在 | 聊天角色（引用校验） |
| 1_040_010_000 | 工具不存在 | 工具 / 聊天角色（引用校验） |
| 1_040_010_001 | 工具({})找不到 Bean | 工具 |
