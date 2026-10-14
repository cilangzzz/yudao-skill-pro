# 企业邮箱接口 (OaMailAccountController / OaMailFolderController / OaMailMessageController / OaMailProviderController)

> 提供企业邮箱的服务配置管理、个人邮箱账号绑定、文件夹与邮件索引同步、邮件读写及写信发送能力；本地仅保存邮件索引与正文缓存，收发与同步通过 IMAP/SMTP 直连远端邮箱，远端写操作按账号加锁串行执行，失败后通过再次同步恢复索引。

## 接口路径前缀

- /oa/mail-account (Controller: OaMailAccountController)
- /oa/mail-folder (Controller: OaMailFolderController)
- /oa/mail-message (Controller: OaMailMessageController)
- /oa/mail-provider (Controller: OaMailProviderController)

## 1. 邮箱服务配置管理（OaMailProviderController）

管理员维护企业邮箱的 IMAP/SMTP 连接配置，供邮箱账号绑定引用。

### 1.1 获得邮箱服务配置列表

- **路径**: GET /oa/mail-provider/list
- **权限**: oa:mail-provider:query
- **说明**: 按状态过滤查询邮箱服务配置，status 未传时查询全部状态

**请求参数**: 无（Query 参数 `status` 可选，Integer，0 启用 / 1 停用）

**响应**: CommonResult&lt;List&lt;OaMailProviderRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| name | String | 名称 |
| imap | ConnectionConfig | IMAP 连接配置 |
| smtp | ConnectionConfig | SMTP 连接配置 |
| status | Integer | 状态 |

**业务逻辑**: 1. 按状态条件查询配置列表（status 为空查全部）。 2. BeanUtils 转换为 RespVO 返回。

### 1.2 获得邮箱服务配置精简列表

- **路径**: GET /oa/mail-provider/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 供前端下拉选择，仅返回启用中的配置

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;OaMailProviderRespVO&gt;&gt;（仅填充 id、name、status 三个字段）

**业务逻辑**: 1. 查询启用状态（CommonStatusEnum.ENABLE）的配置。 2. 转换为仅含 id/name/status 的精简 VO 返回。

### 1.3 获得邮箱服务配置

- **路径**: GET /oa/mail-provider/get
- **权限**: oa:mail-provider:query
- **说明**: 按编号查询单个服务配置

**请求参数**: 无（Query 参数 `id` 必填，Long，服务配置编号）

**响应**: CommonResult&lt;OaMailProviderRespVO&gt;，字段同 1.1

**业务逻辑**: 1. 按编号查询配置，不存在时抛 MAIL_PROVIDER_NOT_EXISTS。 2. 转换为 RespVO 返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |

### 1.4 创建邮箱服务配置

- **路径**: POST /oa/mail-provider/create
- **权限**: oa:mail-provider:create
- **说明**: 新增 IMAP/SMTP 连接配置

**请求参数 (OaMailProviderSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | Long | 否 | - | 服务配置编号（创建时传空） |
| name | String | 是 | @NotBlank、@Size(max=255) | 名称 |
| imap | ConnectionConfig | 是 | @NotNull、@Valid | IMAP 连接配置 |
| smtp | ConnectionConfig | 是 | @NotNull、@Valid | SMTP 连接配置 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态 |

嵌套对象 ConnectionConfig：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| host | String | 是 | @NotBlank、@Size(max=253)、@AssertTrue（服务器域名/IP 格式，IPv6 或 IPv4 或域名，不含协议与端口） | 服务器域名 |
| port | Integer | 是 | @NotNull、@Min(1)、@Max(65535) | 服务器端口 |
| sslEnable | Boolean | 是 | @NotNull | 是否开启 SSL |
| starttlsEnable | Boolean | 是 | @NotNull、@AssertTrue（SSL 与 STARTTLS 不能同时开启） | 是否开启 STARTTLS |

**响应**: CommonResult&lt;Long&gt;（新配置编号）

**业务逻辑**: 1. 将 ReqVO 转换为 OaMailProviderDO 并清空 id。 2. 插入配置并返回编号。

### 1.5 更新邮箱服务配置

- **路径**: PUT /oa/mail-provider/update
- **权限**: oa:mail-provider:update
- **说明**: 修改服务配置的连接信息或状态

**请求参数 (OaMailProviderSaveReqVO)**: 同 1.4（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验配置存在（否则 MAIL_PROVIDER_NOT_EXISTS）。 2. 转换为 DO 并 updateById 更新。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |

### 1.6 删除邮箱服务配置

- **路径**: DELETE /oa/mail-provider/delete
- **权限**: oa:mail-provider:delete
- **说明**: 删除未被邮箱账号引用的服务配置

**请求参数**: 无（Query 参数 `id` 必填，Long，服务配置编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验配置存在。 2. 校验是否被邮箱账号引用（引用数大于 0 时抛 MAIL_PROVIDER_IN_USE）。 3. 删除配置。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |
| 1_054_190_002 | 邮箱服务配置已被账号引用 |

## 2. 邮箱账号管理（OaMailAccountController）

用户绑定本人邮箱账号（归属人以 creator 字段判定），支持设置默认发件账号与连接测试。

### 2.1 获得本人邮箱账号列表

- **路径**: GET /oa/mail-account/list
- **权限**: oa:mail-account:query
- **说明**: 查询当前登录用户绑定的邮箱账号，可按状态过滤

**请求参数**: 无（Query 参数 `status` 可选，Integer，未传时查询全部状态）

**响应**: CommonResult&lt;List&lt;OaMailAccountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 账号编号 |
| providerId | Long | 服务配置编号 |
| mail | String | 邮箱地址 |
| userName | String | 归属人姓名 |
| username | String | 登录用户名 |
| defaultStatus | Boolean | 是否默认发件账号 |
| status | Integer | 状态 |

**业务逻辑**: 1. 按当前登录用户（creator）与可选状态查询本人账号列表。 2. 转换为 RespVO 返回。

### 2.2 获得当前租户邮箱地址精简列表

- **路径**: GET /oa/mail-account/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 供全员选择器使用，只返回邮箱地址和姓名，不暴露登录名及连接配置

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;OaMailAccountRespVO&gt;&gt;（仅填充 mail、userName 字段）

**业务逻辑**: 1. 查询启用状态的邮箱账号，并批量获取归属人的用户昵称。 2. 转换为仅含 mail/userName 的精简 VO。 3. 补充 system 模块中已配置邮箱地址的启用用户（按邮箱地址忽略大小写去重后追加）。

### 2.3 获得本人邮箱账号

- **路径**: GET /oa/mail-account/get
- **权限**: oa:mail-account:query
- **说明**: 按编号查询本人邮箱账号，校验归属

**请求参数**: 无（Query 参数 `id` 必填，Long，邮箱账号编号）

**响应**: CommonResult&lt;OaMailAccountRespVO&gt;，字段同 2.1

**业务逻辑**: 1. validateMailAccount 按编号查询账号，不存在或 creator 不是当前用户时抛 MAIL_ACCOUNT_NOT_EXISTS。 2. 转换为 RespVO 返回。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |

### 2.4 绑定本人邮箱账号

- **路径**: POST /oa/mail-account/create
- **权限**: oa:mail-account:create
- **说明**: 为当前用户新增邮箱绑定（@ApiAccessLog(requestEnable=false)，避免日志记录密码）

**请求参数 (OaMailAccountSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| id | Long | 否 | - | 账号编号（创建时传空） |
| providerId | Long | 是 | @NotNull | 服务配置编号 |
| mail | String | 是 | @NotBlank、@Email、@Size(max=255) | 邮箱地址 |
| username | String | 是 | @NotBlank、@Size(max=255) | 登录用户名 |
| password | String | 创建时必填 | @Size(max=4096)、@ToString.Exclude | 密码或授权码，修改时留空表示不变 |
| defaultStatus | Boolean | 是 | @NotNull、@AssertTrue（默认账号必须启用） | 是否默认发件账号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态 |

**响应**: CommonResult&lt;Long&gt;（新账号编号）

**业务逻辑**: 1. 校验服务配置存在且启用。 2. 创建时密码/授权码为空则抛 MAIL_ACCOUNT_PASSWORD_REQUIRED。 3. 锁定本人全部账号（selectListByCreatorForUpdate），若请求设为默认则清除其它账号的默认标志。 4. 转换为 DO（清空 id）插入并返回编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |
| 1_054_190_001 | 邮箱服务配置未启用 |
| 1_054_190_005 | 请输入邮箱密码或授权码 |

### 2.5 更新本人邮箱账号

- **路径**: PUT /oa/mail-account/update
- **权限**: oa:mail-account:update
- **说明**: 修改本人账号的凭据、默认标志或状态（@ApiAccessLog(requestEnable=false)，避免日志记录密码）

**请求参数 (OaMailAccountSaveReqVO)**: 同 2.4（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 锁定本人全部账号并校验目标账号归属。 2. 绑定身份固定：providerId、mail、username 任一变化即抛 MAIL_ACCOUNT_IDENTITY_IMMUTABLE（换邮箱需新增绑定，避免旧邮件归到新账号）。 3. 校验服务配置存在且启用。 4. 若设为默认则清除其它账号默认标志。 5. 转换为 DO 更新，密码留空时置 null 表示不变。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |
| 1_054_190_001 | 邮箱服务配置未启用 |
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_033 | 邮箱绑定后不能修改地址、登录名或服务，请新增绑定 |

### 2.6 设置本人默认发件账号

- **路径**: PUT /oa/mail-account/update-default
- **权限**: oa:mail-account:update
- **说明**: 将本人某个启用中的账号设为默认发件账号

**请求参数**: 无（Query 参数 `id` 必填，Long，邮箱账号编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 锁定本人全部账号。 2. 校验目标账号归属。 3. 校验目标账号已启用（停用抛 MAIL_ACCOUNT_DISABLED）。 4. 校验其服务配置存在且启用。 5. 清除原默认账号，并将目标账号 defaultStatus 置为 true。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |
| 1_054_190_001 | 邮箱服务配置未启用 |
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_004 | 邮箱账号未启用 |

### 2.7 移除本人邮箱绑定

- **路径**: DELETE /oa/mail-account/delete
- **权限**: oa:mail-account:delete
- **说明**: 删除本地邮箱绑定，不影响远端邮箱

**请求参数**: 无（Query 参数 `id` 必填，Long，邮箱账号编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验账号归属（validateMailAccount）。 2. 仅删除本地绑定记录。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |

### 2.8 测试本人邮箱连接

- **路径**: POST /oa/mail-account/test-connection
- **权限**: oa:mail-account:query
- **说明**: 用保存的凭据分别测试 IMAP/SMTP 连接，不发送真实邮件

**请求参数**: 无（Query 参数 `id` 必填，Long，邮箱账号编号）

**响应**: CommonResult&lt;Map&lt;String, Boolean&gt;&gt;，形如 `{"imap": true, "smtp": true}`

**业务逻辑**: 1. 校验账号归属及启用状态。 2. 校验服务配置存在且启用。 3. 分别以 IMAP（验证登录）与 SMTP（不发送邮件）两种协议测试连接，返回各自的连通结果。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_000 | 邮箱服务配置不存在 |
| 1_054_190_001 | 邮箱服务配置未启用 |
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_004 | 邮箱账号未启用 |

## 3. 邮箱文件夹（OaMailFolderController）

文件夹由邮件同步时自动创建/更新，本控制器仅提供查询入口。

### 3.1 获得邮箱文件夹列表

- **路径**: GET /oa/mail-folder/list
- **权限**: oa:mail-account:query
- **说明**: 查询指定邮箱账号的文件夹（含未读数），供左侧目录树展示

**请求参数**: 无（Query 参数 `accountId` 必填，Long，邮箱账号编号）

**响应**: CommonResult&lt;List&lt;OaMailFolderRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| key | String | 目录查询标识（标准目录为 INBOX/SENT/DRAFTS/TRASH 等，自建目录为目录编号） |
| name | String | 显示名称 |
| unreadCount | Long | 未读数量 |

**业务逻辑**: 1. 校验账号归属。 2. 查询账号下全部目录，并统计各目录未读邮件数。 3. 标准目录统一中文展示并按标准顺序排序（收件箱、已发送、草稿箱、已删除在前），自建目录保留完整名称按名称排序；不可用目录跳过。 4. 收件箱之后追加"未读邮件"虚拟入口（key=UNREAD，未读数与收件箱一致）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |

## 4. 邮件消息（OaMailMessageController）

> 类级别声明 @PreAuthorize("@ss.hasPermission('oa:mail-account:query')")，以下全部端点默认要求该权限。

### 4.1 获得写信预填数据

- **路径**: GET /oa/mail-message/compose
- **权限**: oa:mail-account:query
- **说明**: 按写信方式（新邮件/编辑草稿/回复/回复全部/转发）返回写信表单预填数据

**请求参数**: 无（Query 参数 `id` 必填，Long，邮件编号；`mode` 必填，String，写信方式，@InEnum(OaMailComposeModeEnum)，取值 new/draft/reply/replyAll/forward）

**响应**: CommonResult&lt;OaMailMessageSaveReqVO&gt;（结构同 4.8 请求参数，attachments 字段用于回显原附件）

**业务逻辑**: 1. 校验原邮件索引归属及文件夹可用。 2. 编辑器正文用 Jsoup 移除 style 样式并按 relaxed Safelist 清洗（额外保留 details/summary 标签），避免样式泄漏和外链资源请求。 3. draft 模式：校验原邮件确在草稿箱（否则 MAIL_NOT_DRAFT），返回 draftId、收件人、抄送、主题、正文及原附件路径，mode 置回 new。 4. 转发模式主题加 "Fwd: " 前缀并携带原附件；回复模式主题无 "Re:" 前缀时补上。 5. 回复地址优先取 Reply-To，为空时用发件人；回复全部时并入原收件人与抄送，均排除本人邮箱并按地址忽略大小写去重；地址解析失败抛 MAIL_ADDRESS_INVALID。 6. 引用正文包裹 blockquote，原始发件人等邮件头以文本转义（Entities.escape）防止 HTML 注入。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_016 | 邮件地址格式不正确，请检查收件人和抄送人 |
| 1_054_190_017 | 邮件不是草稿 |

### 4.2 同步本人邮箱索引

- **路径**: POST /oa/mail-message/sync
- **权限**: oa:mail-account:query
- **说明**: 拉取远端邮箱全部文件夹及邮件索引，更新本地快照，返回同步邮件总数

**请求参数**: 无（Query 参数 `accountId` 必填，Long，邮箱账号编号）

**响应**: CommonResult&lt;Integer&gt;（本次同步的邮件索引总数）

**业务逻辑**: 1. 校验归属并锁定账号（lockMailAccount），避免多个同步请求覆盖更新结果。 2. 建立 IMAP 连接，获取远端全部文件夹映射（标准目录 + CUSTOM: 前缀的自建目录）。 3. 逐文件夹抓取完整邮件快照（单文件夹超过 100000 封抛 MAIL_SYNC_COUNT_EXCEEDED），按 uidValidity:uid 对比本地索引，执行新增/更新/删除，保留稳定的本地主键。 4. 远端不再存在的文件夹标记 available=false，保留旧索引但不再展示。 5. 全部抓取成功后才提交本地快照；连接或读取异常抛 MAIL_SYNC_FAILED（本地快照未更新）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_008 | 单文件夹超过 100000 封，请先缩小邮箱范围后同步 |
| 1_054_190_018 | 邮箱同步失败，本地快照未更新，请检查连接后重试 |

### 4.3 获得邮件索引分页

- **路径**: GET /oa/mail-message/page
- **权限**: oa:mail-account:query
- **说明**: 按文件夹分页查询本地邮件索引

**请求参数 (OaMailMessagePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| pageNo | Integer | 否 | PageParam 默认校验 | 页码 |
| pageSize | Integer | 否 | PageParam 默认校验 | 每页条数 |
| accountId | Long | 是 | @NotNull | 邮箱账号编号 |
| folderKey | String | 是 | @NotBlank、@AssertTrue（标准入口 INBOX/UNREAD/SENT/DRAFTS/TRASH 或数字目录编号） | 文件夹类型 |
| keyword | String | 否 | @Size(max=200) | 主题或发件人搜索关键字 |
| readStatus | Boolean | 否 | - | 是否已读 |
| hasAttach | Boolean | 否 | - | 是否有附件 |

**响应**: CommonResult&lt;PageResult&lt;OaMailMessageRespVO&gt;&gt;，字段同 4.4（详情接口的 content/attachments 仅缓存后返回）

**业务逻辑**: 1. 校验账号归属。 2. folderKey 为 UNREAD 虚拟入口时固定在收件箱内筛选，并强制 readStatus=false。 3. folderKey 为数字时按自定义目录编号查询，并校验目录归属当前账号且可用；否则按标准类型查找可用目录。 4. 目录不存在（尚未同步或不可用）时返回空分页。 5. 按条件查询邮件分页。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |

### 4.4 获得邮件详情

- **路径**: GET /oa/mail-message/get
- **权限**: oa:mail-account:query
- **说明**: 查看邮件详情，首次访问时从远端读取并缓存正文与附件目录

**请求参数**: 无（Query 参数 `id` 必填，Long，邮件编号）

**响应**: CommonResult&lt;OaMailMessageRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 邮件编号 |
| accountId | Long | 邮箱账号编号 |
| folderId | Long | 文件夹编号 |
| uid | Long | 远端邮件 UID |
| uidValidity | Long | 远端 UID 有效期 |
| subject | String | 邮件主题 |
| sender | String | 发件人 |
| recipients | List&lt;String&gt; | 收件人 |
| ccs | List&lt;String&gt; | 抄送人 |
| replyTos | List&lt;String&gt; | 回复地址 |
| receiveTime | LocalDateTime | 接收时间 |
| readStatus | Boolean | 是否已读 |
| hasAttach | Boolean | 是否有附件 |
| size | Integer | 邮件大小（字节） |
| content | String | 安全 HTML 正文 |
| attachments | List&lt;Attachment&gt; | 附件信息（part：MIME 部件路径；name：附件名称；size：附件大小字节） |

**业务逻辑**: 1. 校验索引归属和文件夹可用；与同步、草稿替换共用账号锁，锁内重查索引，避免使用已失效的旧索引。 2. 正文已缓存（含空正文）时直接返回本地索引。 3. 首次读取：以只读方式打开远端文件夹读取邮件详情，HTML 清洗后缓存正文、Reply-To、附件目录到本地索引，不修改远端状态；读取失败抛 MAIL_DETAIL_READ_FAILED。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_019 | 邮件详情读取失败，请先同步或使用原邮箱客户端 |

### 4.5 更新邮件已读状态

- **路径**: PUT /oa/mail-message/update-read
- **权限**: oa:mail-account:query
- **说明**: 同步设置远端邮件的已读/未读标志并更新本地索引

**请求参数**: 无（Query 参数 `id` 必填，Long，邮件编号；`readStatus` 必填，Boolean，是否已读）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验邮件索引归属及文件夹可用。 2. 锁定账号串行化写操作。 3. 以读写方式打开远端文件夹，setFlag(SEEN) 更新远端已读标志。 4. 远端成功后更新本地索引 readStatus；远端失败抛 MAIL_READ_STATUS_FAILED（提示同步确认远端状态）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_020 | 已读状态更新失败，请同步确认远端状态 |

### 4.6 删除邮件

- **路径**: DELETE /oa/mail-message/delete
- **权限**: oa:mail-account:query
- **说明**: 普通文件夹中的邮件移入已删除文件夹；已删除文件夹中的邮件单封彻底删除

**请求参数**: 无（Query 参数 `id` 必填，Long，邮件编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验归属、文件夹可用及远端 UID。 2. 锁定账号串行化写操作。 3. 普通文件夹：定位远端已删除文件夹（未识别到抛 MAIL_TRASH_NOT_EXISTS），MOVE 能力校验失败抛 MAIL_MOVE_UNSUPPORTED，将邮件移动到已删除。 4. 已删除文件夹中：要求 UIDPLUS 能力（否则抛 MAIL_PERMANENT_DELETE_UNSUPPORTED），仅对指定单封邮件打 DELETED 标记并 expunge，不做全文件夹清理。 5. 远端成功后删除本地索引；失败抛 MAIL_DELETE_UNCONFIRMED（提示先同步核实，勿重复操作）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_011 | 服务商不支持安全的单封彻底删除，请使用原邮箱客户端 |
| 1_054_190_012 | 未识别到已删除文件夹，请使用原邮箱客户端 |
| 1_054_190_013 | 服务商不支持安全移动，请使用原邮箱客户端操作 |
| 1_054_190_021 | 删除结果未确认，请先同步核实，勿重复操作 |

### 4.7 恢复邮件到收件箱

- **路径**: PUT /oa/mail-message/restore
- **权限**: oa:mail-account:query
- **说明**: 将已删除文件夹中的邮件移回收件箱

**请求参数**: 无（Query 参数 `id` 必填，Long，邮件编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验归属及文件夹可用；邮件不在已删除文件夹时抛 MAIL_NOT_TRASH。 2. 锁定账号。 3. 定位远端收件箱（不存在抛 MAIL_FOLDER_NOT_AVAILABLE）。 4. MOVE 能力校验后将邮件移回收件箱。 5. 删除旧 UID 索引，新索引由后续同步生成；失败抛 MAIL_RESTORE_UNCONFIRMED。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_013 | 服务商不支持安全移动，请使用原邮箱客户端操作 |
| 1_054_190_034 | 恢复结果未确认，请先同步核实 |
| 1_054_190_035 | 只能恢复已删除文件夹中的邮件 |

### 4.8 保存草稿

- **路径**: POST /oa/mail-message/save-draft（consumes=application/json 或 multipart/form-data 两种方式，multipart 方式额外上传 files 附件列表，data 部分为 ReqVO）
- **权限**: oa:mail-account:query
- **说明**: 以"先追加新草稿、再按 UID 安全清理旧草稿"的方式保存草稿到远端草稿箱，返回新草稿编号

**请求参数 (OaMailMessageSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| accountId | Long | 是 | @NotNull | 邮箱账号编号 |
| draftId | Long | 否 | - | 原草稿编号（编辑已有草稿时传） |
| recipients | List&lt;String&gt; | 否 | 元素 @NotBlank | 收件人 |
| ccs | List&lt;String&gt; | 否 | 元素 @NotBlank | 抄送人 |
| subject | String | 否 | @Size(max=65535) | 主题（服务端校验不能含换行） |
| content | String | 否 | @Size(max=500000) | 正文 HTML |
| sourceId | Long | 否 | - | 回复或转发的原邮件编号 |
| mode | String | 是 | @NotBlank、@InEnum(OaMailComposeModeEnum) | 写信方式 new/draft/reply/replyAll/forward |
| attachmentParts | List&lt;String&gt; | 否 | - | 保留的原邮件附件 MIME 路径；空列表表示移除全部原附件 |
| attachments | List&lt;Attachment&gt; | 否 | 只读，用于回显 | 原邮件附件 |
| files | List&lt;MultipartFile&gt; | multipart 方式 | - | 上传的附件文件 |

**响应**: CommonResult&lt;Long&gt;（新草稿编号）

**业务逻辑**: 1. 锁定账号并校验归属；指定 draftId 时校验其为当前账号草稿箱中的草稿（否则 MAIL_DRAFT_NOT_OWNED），不允许将普通邮件当作草稿覆盖。 2. 校验草稿箱目录存在（否则 MAIL_DRAFT_FOLDER_NOT_EXISTS），且服务商支持 UIDPLUS 能力（否则 MAIL_DRAFT_REPLACE_UNSUPPORTED）。 3. 构建新草稿邮件：正文清洗为安全 HTML、地址解析校验（含换行的地址抛 MAIL_ADDRESS_INVALID）、编辑草稿或转发时按 attachmentParts 保留原附件、上传文件作为独立 MIME 附件、标记 DRAFT 标志。 4. 将新草稿追加到远端草稿箱（appendUIDMessages），未返回 UID 时抛 MAIL_DRAFT_SAVE_UNCONFIRMED。 5. 新草稿成功追加后才按 UID 清理旧草稿。 6. 同步草稿索引并按 UID 定位新草稿（找不到抛 MAIL_DRAFT_INDEX_NOT_FOUND），返回其本地编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_014 | 请填写收件人 |
| 1_054_190_015 | 主题不能包含换行 |
| 1_054_190_016 | 邮件地址格式不正确，请检查收件人和抄送人 |
| 1_054_190_022 | 未识别到草稿箱，请先在原邮箱配置草稿文件夹 |
| 1_054_190_023 | 服务商不支持草稿安全替换，请使用原邮箱客户端 |
| 1_054_190_024 | 草稿保存结果未确认，请同步草稿箱后核实，勿重复保存 |
| 1_054_190_025 | 草稿已保存，请同步后查看 |
| 1_054_190_026 | 原邮件不属于当前邮箱 |
| 1_054_190_028 | 只能修改当前账号的草稿 |
| 1_054_190_029 | 原邮件或附件读取失败，未执行发送 |

### 4.9 发送邮件

- **路径**: POST /oa/mail-message/send（consumes=application/json 或 multipart/form-data，multipart 方式额外上传 files 附件列表）
- **权限**: oa:mail-account:query
- **说明**: 通过 SMTP 发送邮件并处理 IMAP 已发送副本与草稿清理，返回结果提示语

**请求参数 (OaMailMessageSaveReqVO)**: 同 4.8（发送时要求至少一个收件人，否则 MAIL_RECIPIENT_REQUIRED）

**响应**: CommonResult&lt;String&gt;（提示语，如"服务器已接收邮件，请同步查看已发送"）

**业务逻辑**: 1. 锁定账号并校验归属；指定 draftId 时校验草稿归属，指定 sourceId 时校验引用原邮件属于当前账号（否则 MAIL_SOURCE_NOT_OWNED）。 2. 构建待发邮件（回复时补充 In-Reply-To/References 线程标识，正文清洗，附件处理同 4.8），SMTP 发送仅执行一次；发送异常抛 MAIL_SEND_UNCONFIRMED（提示勿直接重发）。 3. SMTP 成功后 IMAP 副本处理分开反馈：未识别到已发送文件夹时返回提示，不影响发送结果。 4. 已发送文件夹按 Message-ID 检查（部分服务商自动保存副本），不存在时才追加副本。 5. 存在原草稿时删除远端草稿及本地索引。 6. 副本保存或草稿清理失败仅返回提示语，绝不让用户重复发信。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_014 | 请填写收件人 |
| 1_054_190_015 | 主题不能包含换行 |
| 1_054_190_016 | 邮件地址格式不正确，请检查收件人和抄送人 |
| 1_054_190_026 | 原邮件不属于当前邮箱 |
| 1_054_190_027 | 发送失败或结果未知，请先在原邮箱确认，勿直接重发 |
| 1_054_190_028 | 只能修改当前账号的草稿 |
| 1_054_190_029 | 原邮件或附件读取失败，未执行发送 |

### 4.10 下载本人邮件附件

- **路径**: GET /oa/mail-message/attachment
- **权限**: oa:mail-account:query
- **说明**: 从远端邮箱按 MIME 部件路径下载附件，直接输出文件流

**请求参数**: 无（Query 参数 `id` 必填，Long，邮件编号；`part` 必填，String，MIME 部件路径，如 "1.2"）

**响应**: 文件流（非 CommonResult，通过 ServletUtils.writeAttachment 写出）

**业务逻辑**: 1. 校验邮件归属、所属邮箱及文件夹可用。 2. 校验远端 UID 后以只读方式打开远端文件夹。 3. 按 part 路径定位附件并读取完整内容（文件夹关闭前读完），附件不存在抛 MAIL_ATTACHMENT_NOT_EXISTS。 4. 以附件原始文件名写出响应流；读取失败抛 MAIL_ATTACHMENT_READ_FAILED。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_054_190_003 | 邮箱账号不存在或无权访问 |
| 1_054_190_006 | 邮件不存在或已移动，请先同步 |
| 1_054_190_007 | 文件夹不可用，请先同步 |
| 1_054_190_031 | 邮件附件不存在 |
| 1_054_190_032 | 邮件附件读取失败，请同步邮件后重试 |
