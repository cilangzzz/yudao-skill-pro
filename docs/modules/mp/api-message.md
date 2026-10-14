# 消息、自动回复与模板消息接口 (MpMessageController / MpAutoReplyController / MpMessageTemplateController)

> 管理后台对微信公众号消息的查询与客服消息发送、自动回复规则的维护，以及模板消息的同步与推送。

## 接口路径前缀

- /mp/message (Controller: MpMessageController)
- /mp/auto-reply (Controller: MpAutoReplyController)
- /mp/message-template (Controller: MpMessageTemplateController)

---

## 1. 公众号消息（粉丝消息，MpMessageController）

### 1.1 获得公众号消息分页

- **路径**: GET /mp/message/page
- **权限**: mp:message:query
- **说明**: 分页查询公众号收到/发出的消息记录，可按消息类型、粉丝等条件过滤。

**请求参数 (MpMessagePageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| type | String | 否 | - | 消息类型，参见 WxConsts.XmlMsgType 枚举（如 text） |
| openid | String | 否 | - | 公众号粉丝标识 |
| userId | String | 否 | - | 公众号粉丝 UserId |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;MpMessageRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| msgId | Long | 微信公众号消息 id |
| accountId | Long | 公众号账号的编号 |
| appId | String | 公众号账号的 appid |
| userId | Long | 公众号粉丝编号 |
| openid | String | 公众号粉丝标志 |
| type | String | 消息类型，参见 WxConsts.XmlMsgType 枚举 |
| sendFrom | Integer | 消息来源，参见 MpMessageSendFromEnum 枚举（用户发给公众号 / 公众号发给用户） |
| content | String | 消息内容（text 类型才有值） |
| mediaId | String | 媒体素材编号（image、voice、video 类型才有值） |
| mediaUrl | String | 媒体文件 URL（image、voice、video 类型才有值） |
| recognition | String | 语音识别后文本（voice 类型才有值） |
| format | String | 语音格式（voice 类型才有值） |
| title | String | 标题（video、music、link 类型才有值） |
| description | String | 描述（video、music 类型才有值） |
| thumbMediaId | String | 缩略图媒体 id（video、music 类型才有值） |
| thumbMediaUrl | String | 缩略图媒体 URL（video、music 类型才有值） |
| url | String | 点击图文消息跳转链接（link 类型才有值） |
| locationX | Double | 地理位置纬度（location 类型才有值） |
| locationY | Double | 地理位置经度（location 类型才有值） |
| scale | Double | 地图缩放大小（location 类型才有值） |
| label | String | 详细地址（location 类型才有值） |
| articles | List&lt;MpMessageDO.Article&gt; | 图文消息数组（NEWS 类型才有值） |
| musicUrl | String | 音乐链接（music 类型才有值） |
| hqMusicUrl | String | 高质量音乐链接（music 类型才有值） |
| event | String | 事件类型，参见 WxConsts.EventType 枚举 |
| eventKey | String | 事件 Key |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 accountId 必填条件及其他可选条件构造查询。2. MpMessageMapper.selectPage 分页查询消息表。3. 转换为 MpMessageRespVO 分页返回。

### 1.2 给粉丝发送消息（客服消息）

- **路径**: POST /mp/message/send
- **权限**: mp:message:send
- **说明**: 管理后台以客服消息形式给指定粉丝发送文本/图片/语音/视频/图文/音乐消息。

**请求参数 (MpMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 公众号粉丝的编号 |
| type | String | 是 | @NotEmpty | 消息类型 TEXT/IMAGE/VOICE/VIDEO/NEWS |
| content | String | 条件必填 | @NotEmpty(TextMessageGroup) | 消息内容（type 为 TEXT 时校验） |
| mediaId | String | 条件必填 | @NotEmpty(Image/Voice/VideoMessageGroup) | 媒体 ID（type 为 IMAGE/VOICE/VIDEO 时校验） |
| title | String | 条件必填 | @NotEmpty(VideoMessageGroup) | 标题（type 为 VIDEO 时校验） |
| description | String | 条件必填 | @NotEmpty(VideoMessageGroup) | 描述（type 为 VIDEO 时校验） |
| thumbMediaId | String | 条件必填 | @NotEmpty(MusicMessageGroup) | 缩略图的媒体 id（type 为 MUSIC 时校验） |
| articles | List&lt;MpMessageDO.Article&gt; | 条件必填 | @Valid、@NotNull(NewsMessageGroup) | 图文消息（type 为 NEWS 时校验） |
| musicUrl | String | 否 | - | 音乐链接（type 为 MUSIC 时） |
| hqMusicUrl | String | 否 | - | 高质量音乐链接（type 为 MUSIC 时） |

**响应**: CommonResult&lt;MpMessageRespVO&gt;（字段同 1.1 响应表）

**业务逻辑**: 1. 按 type 调用 MpUtils.validateMessage 按对应消息分组校验消息格式。2. 校验粉丝（getRequiredUser）与所属公众号账号（getRequiredAccount）存在。3. 转换为 WxMpKefuMessage，通过 MpServiceFactory 取得对应 appId 的 WxMpService 发送客服消息；微信返回错误时抛 MESSAGE_SEND_FAIL。4. 转换并记录 MpMessageDO，sendFrom = MP_TO_USER。5. downloadMessageMedia：若含 mediaId/thumbMediaId，下载媒体文件并上传到文件服务，回填 mediaUrl/thumbMediaUrl。6. 插入消息记录并返回。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_005_000 | 发送消息失败，原因：{} |

---

## 2. 公众号自动回复（MpAutoReplyController）

### 2.1 获得公众号自动回复分页

- **路径**: GET /mp/auto-reply/page
- **权限**: mp:auto-reply:query
- **说明**: 分页查询自动回复规则（复用 MpMessagePageReqVO 作为分页查询参数）。

**请求参数 (MpMessagePageReqVO)**: 继承 PageParam（pageNo、pageSize），字段同 1.1（accountId 必填，type/openid/userId/createTime 可选）。

**响应**: CommonResult&lt;PageResult&lt;MpAutoReplyRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 |
| accountId | Long | 公众号账号的编号 |
| appId | String | 公众号 appId |
| type | Integer | 回复类型：1 关注时回复 / 2 收到消息回复 / 3 关键词回复（MpAutoReplyTypeEnum） |
| requestKeyword | String | 请求的关键字（type 为 KEYWORD 时有值） |
| requestMatch | Integer | 请求的匹配方式（type 为 KEYWORD 时有值） |
| requestMessageType | String | 请求的消息类型（type 为 MESSAGE 时有值） |
| responseMessageType | String | 回复的消息类型：TEXT、IMAGE、VOICE、VIDEO、NEWS、MUSIC |
| responseContent | String | 回复的消息内容 |
| responseMediaId | String | 回复的媒体 id |
| responseMediaUrl | String | 回复的媒体 URL |
| responseThumbMediaId | String | 缩略图的媒体 id |
| responseThumbMediaUrl | String | 缩略图的媒体 URL |
| responseTitle | String | 回复的标题 |
| responseDescription | String | 回复的描述 |
| responseArticles | List&lt;MpMessageDO.Article&gt; | 回复的图文消息 |
| responseMusicUrl | String | 回复的音乐链接 |
| responseHqMusicUrl | String | 回复的高质量音乐链接 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. MpAutoReplyMapper.selectPage 按 accountId 等条件分页查询自动回复表。2. 转换为 MpAutoReplyRespVO 分页返回。

### 2.2 获得公众号自动回复

- **路径**: GET /mp/auto-reply/get
- **权限**: mp:auto-reply:query
- **说明**: 按编号查询单条自动回复详情。请求参数：id（Long，必填，编号）。响应字段同 2.1。

**业务逻辑**: 1. MpAutoReplyMapper.selectById 查询。2. 转换为 MpAutoReplyRespVO 返回。

### 2.3 创建公众号自动回复

- **路径**: POST /mp/auto-reply/create
- **权限**: mp:auto-reply:create
- **说明**: 新建关注时回复 / 收到消息回复 / 关键词回复规则。

**请求参数 (MpAutoReplyCreateReqVO)**: 继承 MpAutoReplyBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| type | Integer | 是 | @NotNull | 回复类型：1 关注时回复 / 2 收到消息回复 / 3 关键词回复 |
| requestKeyword | String | 条件必填 | @AssertTrue（type=KEYWORD 时不能为空） | 请求的关键字 |
| requestMatch | Integer | 条件必填 | @AssertTrue（type=KEYWORD 时不能为空） | 请求的匹配方式 |
| requestMessageType | String | 条件必填 | @AssertTrue（type=MESSAGE 时不能为空） | 请求的消息类型 |
| responseMessageType | String | 是 | @NotEmpty | 回复的消息类型：TEXT、IMAGE、VOICE、VIDEO、NEWS、MUSIC |
| responseContent | String | 条件必填 | @NotEmpty(TextMessageGroup) | 回复的消息内容 |
| responseMediaId | String | 条件必填 | @NotEmpty(Image/Voice/VideoMessageGroup) | 回复的媒体 id |
| responseMediaUrl | String | 条件必填 | @NotEmpty(Image/Voice/VideoMessageGroup) | 回复的媒体 URL |
| responseThumbMediaId | String | 条件必填 | @NotEmpty(MusicMessageGroup) | 缩略图的媒体 id |
| responseThumbMediaUrl | String | 条件必填 | @NotEmpty(MusicMessageGroup) | 缩略图的媒体 URL |
| responseTitle | String | 条件必填 | @NotEmpty(VideoMessageGroup) | 回复的标题 |
| responseDescription | String | 条件必填 | @NotEmpty(VideoMessageGroup) | 回复的描述 |
| responseArticles | List&lt;MpMessageDO.Article&gt; | 条件必填 | @NotNull、@Valid(NewsMessageGroup/ViewLimitedButtonGroup) | 回复的图文消息 |
| responseMusicUrl | String | 条件必填 | @NotEmpty、@URL(MusicMessageGroup) | 回复的音乐链接 |
| responseHqMusicUrl | String | 条件必填 | @NotEmpty、@URL(MusicMessageGroup) | 高质量音乐链接 |

**响应**: CommonResult&lt;Long&gt;（自动回复编号）

**业务逻辑**: 1. 按 responseMessageType 调用 MpUtils.validateMessage 按消息分组校验回复内容格式。2. validateAutoReplyConflict 冲突校验：type=SUBSCRIBE 时该账号不允许已存在关注回复；type=MESSAGE 时同一账号同一请求消息类型不允许重复；type=KEYWORD 时同一账号同一关键词不允许重复，冲突则分别抛对应错误码。3. mpAccountService.getRequiredAccount 校验公众号账号存在并取 appId。4. 转换为 MpAutoReplyDO 并设置 appId 后插入。5. 返回新记录 id。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_009_001 | 操作失败，原因：已存在关注时的回复 |
| 1_006_009_002 | 操作失败，原因：已存在该消息类型的回复 |
| 1_006_009_003 | 操作失败，原因：已关在该关键字的回复 |

### 2.4 更新公众号自动回复

- **路径**: PUT /mp/auto-reply/update
- **权限**: mp:auto-reply:update
- **说明**: 修改自动回复规则（不可修改所属账号）。

**请求参数 (MpAutoReplyUpdateReqVO)**: 继承 MpAutoReplyBaseVO（字段同 2.3，accountId 替换为下述 id）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 主键 |

（其余继承字段及校验同 2.3 请求参数表）

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. 按 responseMessageType 分组校验回复内容格式。2. validateAutoReplyExists 校验自动回复存在。3. validateAutoReplyConflict 按原记录的 accountId 做同 2.3 的冲突校验（排除自身 id）。4. 转换为更新对象并将 accountId、appId 置空（避免前端传递更新这两个字段）。5. updateById 更新记录。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_009_000 | 自动回复不存在 |
| 1_006_009_001 | 操作失败，原因：已存在关注时的回复 |
| 1_006_009_002 | 操作失败，原因：已存在该消息类型的回复 |
| 1_006_009_003 | 操作失败，原因：已关在该关键字的回复 |

### 2.5 删除公众号自动回复

- **路径**: DELETE /mp/auto-reply/delete
- **权限**: mp:auto-reply:delete
- **说明**: 删除指定自动回复规则。请求参数：id（Long，必填，编号）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. validateAutoReplyExists 校验自动回复存在，不存在抛 AUTO_REPLY_NOT_EXISTS。2. deleteById 删除记录。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_009_000 | 自动回复不存在 |

---

## 3. 公众号模版消息（MpMessageTemplateController）

### 3.1 获得模版消息

- **路径**: GET /mp/message-template/get
- **权限**: mp:message-template:query
- **说明**: 按编号查询单条模板消息详情。请求参数：id（Long，必填，编号）。

**响应**: CommonResult&lt;MpMessageTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模版主键 |
| accountId | Long | 公众号账号的编号 |
| appId | String | appId |
| templateId | String | 公众号模板 ID |
| title | String | 标题 |
| content | String | 模板内容 |
| example | String | 模板示例 |
| primaryIndustry | String | 模板所属行业的一级行业 |
| deputyIndustry | String | 模板所属行业的二级行业 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. messageTemplateMapper.selectById 查询。2. BeanUtils 转换为 MpMessageTemplateRespVO 返回。

### 3.2 获得模版消息列表

- **路径**: GET /mp/message-template/list
- **权限**: mp:message-template:query
- **说明**: 按公众号账号查询其全部模板消息（非分页）。

**请求参数 (MpMessageTemplateListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |

**响应**: CommonResult&lt;List&lt;MpMessageTemplateRespVO&gt;&gt;（字段同 3.1 响应表）

**业务逻辑**: 1. messageTemplateMapper.selectList 按 accountId 条件查询列表。2. BeanUtils 批量转换为 MpMessageTemplateRespVO 返回。

### 3.3 同步公众号模板

- **路径**: POST /mp/message-template/sync
- **权限**: mp:message-template:sync
- **说明**: 从微信平台拉取该账号的私有模板列表，全量合并到本地数据库。请求参数：accountId（Long，必填，公众号账号的编号）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. mpAccountService.getRequiredAccount 校验公众号账号存在。2. 通过 MpServiceFactory 取得 WxMpService 调用 getAllPrivateTemplate 拉取最新模板列表，微信返回错误时抛 MESSAGE_TEMPLATE_SYNC_FAIL。3. 以 templateId 为键将本地该 appId 下已有模板转为 Map。4. 遍历微信模板：本地不存在则插入新记录；已存在则按 id 更新标题、内容、示例、行业信息。5. 本地剩余（微信已删除）的模板批量删除（事务方法，异常整体回滚）。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_010_003 | 同步模版消息失败，原因：{} |

### 3.4 给粉丝发送模版消息

- **路径**: POST /mp/message-template/send
- **权限**: mp:message-template:send
- **说明**: 用指定模板给粉丝推送模板消息（不落库，微信会主动推送事件）。

**请求参数 (MpMessageTemplateSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 模版主键 |
| userId | Long | 是 | @NotNull | 公众号粉丝的编号 |
| url | String | 否 | - | 模板跳转链接 |
| miniprogram | String | 否 | - | 跳转小程序时填写（JSON 字符串） |
| data | Map&lt;String, String&gt; | 否 | - | 模板内容（key-value 数据） |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. mpUserService.getRequiredUser 校验粉丝存在。2. validateMsgTemplateExists 校验模板存在。3. buildTemplateMessage 构造 WxMpTemplateMessage：templateId + 粉丝 openid，可选设置跳转链接 url、解析 miniprogram JSON 为小程序跳转、将 data 转为 WxMpTemplateData 列表。4. 通过 MpServiceFactory 取得模板所属 appId 的 WxMpService 发送模板消息，微信返回错误时抛 MESSAGE_TEMPLATE_SEND_FAIL。5. 不记录 MpMessageDO，因为微信会主动推送模板消息送达事件。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_010_000 | 模版消息不存在 |
| 1_006_003_000 | 粉丝不存在 |
| 1_006_010_004 | 发送模版消息失败，原因：{} |

### 3.5 删除模版消息

- **路径**: DELETE /mp/message-template/delete
- **权限**: mp:message-template:delete
- **说明**: 删除微信平台的私有模板并同步删除本地记录。请求参数：id（Long，必填，编号）。

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**: 1. validateMsgTemplateExists 校验模板存在。2. 通过 MpServiceFactory 取得对应 appId 的 WxMpService 调用 delPrivateTemplate 删除微信平台模板，微信返回错误时抛 MESSAGE_TEMPLATE_DELETE_FAIL。3. deleteById 删除本地数据库记录。

**错误码**: 

| 错误码 | 说明 |
|-------|------|
| 1_006_010_000 | 模版消息不存在 |
| 1_006_010_002 | 删除模版消息失败，原因：{} |

---

## 附：本域错误码汇总（1_006_005 / 1_006_009 / 1_006_010 段）

| 错误码 | 说明 |
|-------|------|
| 1_006_005_000 | 发送消息失败，原因：{} |
| 1_006_009_000 | 自动回复不存在 |
| 1_006_009_001 | 操作失败，原因：已存在关注时的回复 |
| 1_006_009_002 | 操作失败，原因：已存在该消息类型的回复 |
| 1_006_009_003 | 操作失败，原因：已关在该关键字的回复 |
| 1_006_010_000 | 模版消息不存在 |
| 1_006_010_002 | 删除模版消息失败，原因：{} |
| 1_006_010_003 | 同步模版消息失败，原因：{} |
| 1_006_010_004 | 发送模版消息失败，原因：{} |

> 说明：粉丝消息的接收（receiveMessage）与被动回复（replyForMessage / replyForSubscribe）由公众号回调 Handler 触发，不走 admin 端点，故不在本文档端点列表内。
