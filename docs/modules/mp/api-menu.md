# 公众号菜单接口 (MpMenuController)

> 管理微信公众号的自定义菜单：保存（同步到微信 + 落库）、删除（同步到微信 + 清库）、查询账号下的菜单列表。

## 接口路径前缀

/mp/menu  (Controller: MpMenuController)

## 1. 公众号菜单管理

### 1.1 保存公众号菜单

- **路径**: POST /mp/menu/save
- **权限**: mp:menu:save
- **说明**: 整体保存指定公众号账号的自定义菜单（先调用微信接口创建菜单，再全量替换数据库中的菜单记录）。

**请求参数 (MpMenuSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| menus | List&lt;Menu&gt; | 是 | @NotEmpty、@Valid（级联校验） | 菜单数组 |

**Menu 结构（继承 MpMenuBaseVO，一级/二级菜单通用）**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 菜单名称 |
| menuKey | String | 否 | - | 菜单标识（CLICK 等点击事件回复时使用） |
| parentId | Long | 否 | - | 父菜单编号（落库时由服务端生成，顶级为 0） |
| type | String | 否 | - | 按钮类型，枚举 WxConsts.MenuButtonType（click/view/miniprogram/scancode_waitmsg/view_limited 等），按类型分组校验 |
| url | String | 否 | @NotEmpty(ViewButtonGroup、MiniProgramButtonGroup)、@URL | 网页链接 |
| miniProgramAppId | String | 否 | @NotEmpty(MiniProgramButtonGroup) | 小程序的 appId |
| miniProgramPagePath | String | 否 | @NotEmpty(MiniProgramButtonGroup) | 小程序的页面路径 |
| articleId | String | 否 | @NotEmpty(ViewLimitedButtonGroup) | 跳转图文的媒体编号 |
| replyMessageType | String | 否 | @NotEmpty(ClickButtonGroup、ScanCodeWaitMsgButtonGroup) | 回复的消息类型，枚举 TEXT、IMAGE、VOICE、VIDEO、NEWS、MUSIC |
| replyContent | String | 否 | @NotEmpty(TextMessageGroup) | 回复的消息内容 |
| replyMediaId | String | 否 | @NotEmpty(ImageMessageGroup、VoiceMessageGroup、VideoMessageGroup) | 回复的媒体 id |
| replyMediaUrl | String | 否 | @NotEmpty(ImageMessageGroup、VoiceMessageGroup、VideoMessageGroup) | 回复的媒体 URL |
| replyThumbMediaId | String | 否 | @NotEmpty(MusicMessageGroup) | 缩略图的媒体 id |
| replyThumbMediaUrl | String | 否 | @NotEmpty(MusicMessageGroup) | 缩略图的媒体 URL |
| replyTitle | String | 否 | @NotEmpty(VideoMessageGroup) | 回复的标题 |
| replyDescription | String | 否 | @NotEmpty(VideoMessageGroup) | 回复的描述 |
| replyArticles | List&lt;MpMessageDO.Article&gt; | 否 | @NotNull(NewsMessageGroup、ViewLimitedButtonGroup)、@Valid | 回复的图文消息数组 |
| replyMusicUrl | String | 否 | @NotEmpty(MusicMessageGroup)、@URL(MusicMessageGroup) | 回复的音乐链接 |
| replyHqMusicUrl | String | 否 | @NotEmpty(MusicMessageGroup)、@URL(MusicMessageGroup) | 高质量音乐链接（WIFI 环境优先播放） |
| children | List&lt;Menu&gt; | 否 | -（递归校验子菜单） | 子菜单数组 |

> 注：消息类字段的必填校验通过 MpUtils 定义的分组接口（TextMessageGroup/ImageMessageGroup 等）按按钮类型动态生效，由 MpUtils#validateButton 逐个按钮递归执行。

**响应**: CommonResult&lt;Boolean&gt;（保存成功返回 true）

**业务逻辑**:
1. 根据accountId 获取公众号账号（不存在则报错），并通过 MpServiceFactory 获取该账号对应的 WxMpService 实例。
2. 递归遍历所有菜单（含子菜单），按按钮类型分组校验格式（如 view 必填 url、click 必须有合法的回复消息等）。
3. 将菜单转换为微信 WxMenu 结构，调用微信接口 menuCreate 同步创建公众号菜单；微信返回错误则抛出 MENU_SAVE_FAIL。
4. 同步成功后，删除数据库中该账号的原有全部菜单记录。
5. 逐个插入一级菜单（parentId 置为根 0，冗余 accountId/appId），再依次插入其子菜单（parentId 置为父菜单 id）；整个保存在事务中执行，失败回滚。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_008_000 | 创建菜单失败，原因：{} |
| 1_006_000_000 | 公众号账号不存在 |

### 1.2 删除公众号菜单

- **路径**: DELETE /mp/menu/delete
- **权限**: mp:menu:delete
- **说明**: 删除指定公众号账号在微信端配置的全部自定义菜单，并清空本地菜单记录。

**请求参数**: 无（Query 参数 accountId：公众号账号的编号，Long，必填）

**响应**: CommonResult&lt;Boolean&gt;（删除成功返回 true）

**业务逻辑**:
1. 通过 MpServiceFactory 获取指定账号对应的 WxMpService 实例。
2. 调用微信接口 menuDelete 删除公众号上的全部菜单；微信返回错误则抛出 MENU_DELETE_FAIL。
3. 删除数据库中该账号的全部菜单记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_008_001 | 删除菜单失败，原因：{} |

### 1.3 获得公众号菜单列表

- **路径**: GET /mp/menu/list
- **权限**: mp:menu:query
- **说明**: 查询指定公众号账号下的全部菜单（含一级、二级），用于前端渲染菜单配置界面。

**请求参数**: 无（Query 参数 accountId：公众号账号的编号，Long，必填）

**响应**: CommonResult&lt;List&lt;MpMenuRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 |
| accountId | Long | 公众号账号的编号 |
| appId | String | 公众号 appId |
| createTime | LocalDateTime | 创建时间 |
| name | String | 菜单名称 |
| menuKey | String | 菜单标识 |
| parentId | Long | 父菜单编号（顶级为 0） |
| type | String | 按钮类型，枚举 WxConsts.MenuButtonType |
| url | String | 网页链接 |
| miniProgramAppId | String | 小程序的 appId |
| miniProgramPagePath | String | 小程序的页面路径 |
| articleId | String | 跳转图文的媒体编号 |
| replyMessageType | String | 回复的消息类型（TEXT/IMAGE/VOICE/VIDEO/NEWS/MUSIC） |
| replyContent | String | 回复的消息内容 |
| replyMediaId | String | 回复的媒体 id |
| replyMediaUrl | String | 回复的媒体 URL |
| replyThumbMediaId | String | 缩略图的媒体 id |
| replyThumbMediaUrl | String | 缩略图的媒体 URL |
| replyTitle | String | 回复的标题 |
| replyDescription | String | 回复的描述 |
| replyArticles | List&lt;MpMessageDO.Article&gt; | 回复的图文消息数组 |
| replyMusicUrl | String | 回复的音乐链接 |
| replyHqMusicUrl | String | 高质量音乐链接 |

**业务逻辑**:
1. 调用 Mapper 的 selectListByAccountId 查询该账号下的全部菜单记录。
2. 通过 MpMenuConvert 转换为 MpMenuRespVO 列表返回（父子关系由前端按 parentId 组装）。

## 补充说明

- 菜单按账号（accountId）维度全量管理：保存即整体替换，删除即清空该账号全部菜单。
- Service 层还提供内部方法 reply(appId, key, openid)：粉丝点击 click/scancode_waitmsg 类型菜单按钮时，按 appId + menuKey 查找菜单，并将配置的回复消息通过 MpMessageService 发出；该方法不暴露为 admin 端点，由微信消息回调处理链路调用。
