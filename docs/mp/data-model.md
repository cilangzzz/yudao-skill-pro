# 数据模型详情

> mp 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

mp 模块共 **8 张表**，全部位于 `yudao-module-mp` 单模块内（包根 `cn.iocoder.yudao.module.mp`），围绕「公众号账号」这一核心实体展开：账号（mp_account）为聚合根，粉丝、标签、菜单、消息、自动回复、模板消息、素材均通过 `accountId` 关联账号，并冗余 `appId` 便于跨表查询与微信调用。

> 注意：草稿（/mp/draft）、发布（/mp/free-publish）、数据统计（/mp/statistics）三个功能域**不落库**，实时调用微信接口，响应直接使用 SDK 类型（WxMpDraftItem / WxMpFreePublishItem / WxDataCube*），因此没有对应的表和 DO。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，实现 Serializable + TransPojo）
│   ├── creator     String          创建者（SysUser 的 id，INSERT 自动填充）
│   ├── createTime  LocalDateTime   创建时间（INSERT 自动填充）
│   ├── updater     String          更新者（SysUser 的 id，INSERT_UPDATE 自动填充）
│   ├── updateTime  LocalDateTime   最后更新时间（INSERT_UPDATE 自动填充）
│   └── deleted     Boolean         是否删除（@TableLogic 逻辑删除）
│
└── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO（多租户基类，位于 yudao-spring-boot-starter-biz-tenant）
        └── tenantId    Long    租户编号
```

本模块 8 个 DO 的继承关系：

```
BaseDO
├── MpMaterialDO            mp_material   素材
├── MpMenuDO                mp_menu       菜单
├── MpAutoReplyDO           mp_auto_reply 自动回复
├── MpMessageDO             mp_message    消息
├── MpMessageTemplateDO     mp_message_template 模板消息
├── MpTagDO                 mp_tag        标签
├── MpUserDO                mp_user       粉丝
└── TenantBaseDO
    └── MpAccountDO         mp_account    公众号账号
```

**使用规则**：

- 仅 `MpAccountDO` 继承 `TenantBaseDO`：账号是租户维度接入的资产（每个租户可接入自己的公众号），随租户隔离；账号自身携带 `tenantId` 字段。
- 其余 7 个 DO 继承 `BaseDO`，**不带 tenantId**，跨租户共享存储，通过 `accountId` 区分数据归属。业务查询一律先经 `MpAccountService` 校验账号归属，再按 `accountId` 过滤。
- 多租户上下文的恢复：微信服务器回调（`/mp/{appId}/callback` 端点）没有登录态，Controller 使用 `@TenantIgnore` 跳过租户拦截，再通过 `TenantUtils.execute` 按 appId 反查账号所属租户、手动恢复租户上下文，保证下游 Service 正常走租户逻辑。

## 2. 核心 DO 实体

> 通用说明：所有 DO 均有 `@KeySequence("{表名}_seq")` 注解，用于 Oracle/PostgreSQL/Kingbase/DB2/H2 等数据库的主键序列，MySQL 下不生效。
> 索引说明：仓库 `sql/` 目录下的建表脚本**未包含 mp_ 开头的建表 DDL**（`sql/mysql/ruoyi-vue-pro.sql` 仅含 mp 相关字典数据），因此除代码中 `@TableId` 声明的主键外，其余唯一/普通索引无法从代码确认，下文仅标注主键与可从代码确证的约束，不做臆测。

### 2.1 账号聚合

#### MpAccountDO (mp_account)

公众号账号 DO，模块的聚合根，一个租户可接入多个公众号。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键 `@TableId` |
| name | String | name | 公众号名称 |
| account | String | account | 公众号账号（微信号） |
| appId | String | app_id | 公众号 appid，`MpServiceFactory` 按它缓存 WxMpService/WxMpMessageRouter |
| appSecret | String | app_secret | 公众号密钥 |
| token | String | token | 公众号 token（服务器验证） |
| aesKey | String | aes_key | 消息加解密密钥（EncodingAESKey） |
| qrCodeUrl | String | qr_code_url | 二维码图片 URL |
| remark | String | remark | 备注 |
| tenantId | Long | tenant_id | 租户编号（继承自 TenantBaseDO） |

**继承**: TenantBaseDO（BaseDO 的 creator/createTime/updater/updateTime/deleted 之外，额外带 tenantId）

**索引**: 主键 `id`。`appId` 是微信回调定位账号的唯一业务键（回调 URL 以 appId 为路径段，工厂按 appId 建缓存），业务上同一 appId 不应重复配置；仓库无 DDL，代码未声明唯一索引。

**周边机制**: `MpAccountServiceImpl` 通过 `@PostConstruct` 构建账号本地缓存，`@Scheduled` 每 60s 刷新一次，并联动 `MpServiceFactory` 重建 WxMpService/WxMpMessageRouter 缓存（access token 存 Redis）。

### 2.2 粉丝与标签聚合

#### MpUserDO (mp_user)

微信公众号粉丝 DO，粉丝关注/取关/消息互动时落库与更新。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号，主键 `@TableId` |
| openid | String | openid | 粉丝标识（单公众号内唯一） |
| unionId | String | union_id | 微信生态唯一标识 |
| subscribeStatus | Integer | subscribe_status | 关注状态，复用 `CommonStatusEnum`：1 开启-已关注、2 禁用-取消关注 |
| subscribeTime | LocalDateTime | subscribe_time | 关注时间 |
| unsubscribeTime | LocalDateTime | unsubscribe_time | 取消关注时间 |
| nickname | String | nickname | 昵称（2021-12-27 后公众号接口不再返回，仅网页登录可取） |
| headImageUrl | String | head_image_url | 头像地址（同上限制） |
| language | String | language | 语言 |
| country | String | country | 国家 |
| province | String | province | 省份 |
| city | String | city | 城市 |
| remark | String | remark | 备注（运营者在公众号平台为粉丝写的备注） |
| tagIds | List\<Long\> | tag_ids | 标签编号数组，`LongListTypeHandler` 存储为逗号分隔字符串。**注意：对应 `MpTagDO.tagId`（微信标签 id），而非 `MpTagDO` 主键 id** |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |

**继承**: BaseDO

**索引**: 主键 `id`。`openid` 在单个公众号内唯一，但仓库无 DDL，`(account_id, openid)` 的唯一索引无法从代码确证。

**易混淆点**: `tagIds` → `MpTagDO.tagId`，不是 `MpTagDO.id`。做标签-粉丝关联查询时必须用 tagId 对齐。

#### MpTagDO (mp_tag)

公众号标签 DO，与微信平台的用户标签一一对应。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，`@TableId(type = IdType.INPUT)`：不走 MP 的自动生成策略，插入时值由应用/数据库侧决定 |
| tagId | Long | tag_id | 公众号平台标签 id（来自 `WxUserTag.id`），**与主键 id 是两个独立字段** |
| name | String | name | 标签名（唯一性由微信平台保证，每个公众号最多 100 个） |
| count | Integer | count | 此标签下粉丝数，冗余自 `WxUserTag.count`，需管理员点击【同步】后更新 |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |

**继承**: BaseDO

**索引**: 主键 `id`。

**同步机制**（`MpTagServiceImpl#syncTag`）：以 `tagId` 与微信返回的 `WxUserTag.id` 对齐做合并——不存在的插入（`MpTagConvert.convert` 明确 `id` ignore、`wxTag.id → tagId`），已存在的更新 name/count，平台上已删除的本地删除。标签的增删改均先调微信接口成功后再写库。

### 2.3 消息聚合

#### MpMessageDO (mp_message)

公众号消息 DO，统一存储粉丝发给公众号、公众号发给粉丝的所有类型消息（普通消息 + 事件推送）。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，`@TableId` |
| msgId | Long | msg_id | 微信公众号消息 id |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |
| userId | Long | user_id | 公众号粉丝编号，关联 `MpUserDO.id` |
| openid | String | openid | 冗余 `MpUserDO.openid` |
| type | String | type | 消息类型，枚举 `WxConsts.XmlMsgType`（text/image/voice/video/shortvideo/news/music/location/link/event，对应字典 `mp_message_type`） |
| sendFrom | Integer | send_from | 消息来源，枚举 `MpMessageSendFromEnum`：1 粉丝发给公众号、2 公众号发给粉丝 |
| content | String | content | 消息内容（TEXT） |
| mediaId | String | media_id | 媒体文件编号（IMAGE/VOICE/VIDEO） |
| mediaUrl | String | media_url | 媒体文件 URL |
| recognition | String | recognition | 语音识别后文本（VOICE） |
| format | String | format | 语音格式，如 amr、speex（VOICE） |
| title | String | title | 标题（VIDEO/MUSIC/LINK） |
| description | String | description | 描述（VIDEO/MUSIC） |
| thumbMediaId | String | thumb_media_id | 缩略图媒体 id（MUSIC/VIDEO） |
| thumbMediaUrl | String | thumb_media_url | 缩略图媒体 URL |
| url | String | url | 点击图文消息跳转链接（LINK） |
| locationX | Double | location_x | 地理位置纬度（LOCATION） |
| locationY | Double | location_y | 地理位置经度（LOCATION） |
| scale | Double | scale | 地图缩放大小（LOCATION） |
| label | String | label | 详细地址（LOCATION） |
| articles | List\<Article\> | articles | 图文消息数组（NEWS），`JacksonTypeHandler` 存 JSON，表需 `autoResultMap = true` |
| musicUrl | String | music_url | 音乐链接（MUSIC） |
| hqMusicUrl | String | hq_music_url | 高质量音乐链接，WIFI 环境优先（MUSIC） |
| event | String | event | 事件类型，枚举 `WxConsts.EventType`（事件推送） |
| eventKey | String | event_key | 事件 Key：SCAN 时为 `qrscene_` 前缀 + 二维码参数值；CLICK 时与自定义菜单 KEY 对应 |

**继承**: BaseDO

**索引**: 主键 `id`。无 DDL 可确证其他索引；按 `(account_id, openid)` 查会话、按 `(account_id, user_id, send_from)` 分页是主要查询路径。

**内嵌类**: `MpMessageDO.Article`（实现 Serializable）——图文消息条目：`title` 标题、`description` 描述、`picUrl` 图片链接（大图 360*200 / 小图 200*200）、`url` 跳转链接，均 `@NotEmpty`（`NewsBuilder` 分组校验）。该类被 `MpMenuDO.replyArticles`、`MpAutoReplyDO.responseArticles` 复用，是模块内的公共 JSON 结构。

#### MpAutoReplyDO (mp_auto_reply)

公众号消息自动回复 DO，配置「关注时回复 / 收到消息回复 / 关键词回复」三类规则。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，`@TableId` |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |
| type | Integer | type | 回复类型，枚举 `MpAutoReplyTypeEnum`：1 关注时回复、2 收到消息回复、3 关键词回复 |
| requestKeyword | String | request_keyword | 请求的关键字（type = KEYWORD 时使用） |
| requestMatch | Integer | request_match | 关键字匹配模式，枚举 `MpAutoReplyMatchEnum`：1 完全匹配、2 半匹配（字典 `mp_auto_reply_request_match`） |
| requestMessageType | String | request_message_type | 请求的消息类型（type = MESSAGE 时使用），取 `WxConsts.XmlMsgType` 的 text/image/voice/video/shortvideo/location/link |
| responseMessageType | String | response_message_type | 回复的消息类型：TEXT/IMAGE/VOICE/VIDEO/NEWS |
| responseContent | String | response_content | 回复的消息内容（TEXT） |
| responseMediaId | String | response_media_id | 回复的媒体 id（IMAGE/VOICE/VIDEO） |
| responseMediaUrl | String | response_media_url | 回复的媒体 URL |
| responseTitle | String | response_title | 回复的标题（VIDEO） |
| responseDescription | String | response_description | 回复的描述（VIDEO） |
| responseThumbMediaId | String | response_thumb_media_id | 回复的缩略图媒体 id（MUSIC/VIDEO） |
| responseThumbMediaUrl | String | response_thumb_media_url | 回复的缩略图媒体 URL |
| responseArticles | List\<MpMessageDO.Article\> | response_articles | 回复的图文消息（NEWS），`JacksonTypeHandler` 存 JSON，`autoResultMap = true` |
| responseMusicUrl | String | response_music_url | 回复的音乐链接（MUSIC） |
| responseHqMusicUrl | String | response_hq_music_url | 回复的高质量音乐链接（MUSIC） |

**继承**: BaseDO

**索引**: 主键 `id`。无 DDL 可确证其他索引；按 `(account_id, type, request_keyword/request_message_type)` 匹配是自动回复路由的核心查询。

**生效链路**: 微信回调 → `MessageReceiveHandler` / `MessageAutoReplyHandler`（WxMpMessageRouter 路由的 10 个 Handler 之一）→ 按 type 匹配规则 → 拼装响应消息回复粉丝。

#### MpMessageTemplateDO (mp_message_template)

公众号模板消息 DO，缓存微信「模板消息」的模板元数据，供发送时引用。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，`@TableId` |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |
| templateId | String | template_id | 公众号模板 ID（微信平台生成） |
| title | String | title | 标题 |
| content | String | content | 模板内容（含 `{{xxx.DATA}}` 占位符） |
| example | String | example | 模板示例 |
| primaryIndustry | String | primary_industry | 模板所属行业的一级行业 |
| deputyIndustry | String | deputy_industry | 模板所属行业的二级行业 |

**继承**: BaseDO

**索引**: 主键 `id`。无 DDL 可确证其他索引；`templateId` 为微信平台唯一键，发送模板消息时以它定位。

### 2.4 菜单聚合

#### MpMenuDO (mp_menu)

公众号自定义菜单 DO，采用 `parentId` 树形结构（一级菜单 + 二级菜单），同时保存点击菜单后的回复消息配置。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，`@TableId`；常量 `ID_ROOT = 0L` 表示顶级菜单的 parentId 约定值 |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |
| name | String | name | 菜单名称 |
| menuKey | String | menu_key | 菜单标识（自定义 KEY，CLICK/SCAN 事件回传） |
| parentId | Long | parent_id | 父菜单编号，0 为顶级 |
| type | String | type | 按钮类型，枚举 `WxConsts.MenuButtonType`（view/click/scancode_waitmsg/miniprogram 等） |
| url | String | url | 网页链接，不超过 1024 字节（VIEW、MINIPROGRAM） |
| miniProgramAppId | String | mini_program_app_id | 小程序的 appId（MINIPROGRAM） |
| miniProgramPagePath | String | mini_program_page_path | 小程序的页面路径（MINIPROGRAM） |
| articleId | String | article_id | 跳转图文的媒体编号 |
| replyMessageType | String | reply_message_type | 消息类型（type 为 CLICK、SCANCODE_WAITMSG 时），取 `WxConsts.XmlMsgType` 的 TEXT/IMAGE/VOICE/VIDEO/NEWS/MUSIC |
| replyContent | String | reply_content | 回复的消息内容（TEXT） |
| replyMediaId | String | reply_media_id | 回复的媒体 id（IMAGE/VOICE/VIDEO） |
| replyMediaUrl | String | reply_media_url | 回复的媒体 URL |
| replyTitle | String | reply_title | 回复的标题（VIDEO） |
| replyDescription | String | reply_description | 回复的描述（VIDEO） |
| replyThumbMediaId | String | reply_thumb_media_id | 回复的缩略图媒体 id（MUSIC/VIDEO） |
| replyThumbMediaUrl | String | reply_thumb_media_url | 回复的缩略图媒体 URL |
| replyArticles | List\<MpMessageDO.Article\> | reply_articles | 回复的图文消息数组（NEWS），`JacksonTypeHandler` 存 JSON，`autoResultMap = true` |
| replyMusicUrl | String | reply_music_url | 回复的音乐链接（MUSIC） |
| replyHqMusicUrl | String | reply_hq_music_url | 回复的高质量音乐链接（MUSIC） |

**继承**: BaseDO

**索引**: 主键 `id`。无 DDL 可确证其他索引；按 `(account_id, parent_id)` 构建菜单树、按 `(account_id, menu_key)` 定位点击菜单是主要查询路径。

**生效机制**: 菜单保存后通过 `WxMpService.getMenuService().menuCreate/menuDelete` 同步到微信平台；粉丝点击 CLICK 菜单时微信回调事件由 `MenuHandler` 处理，按 menuKey 找到本表记录并发送配置的回复消息。

### 2.5 素材聚合

#### MpMaterialDO (mp_material)

公众号素材 DO，管理微信临时/永久素材（图片、语音、视频、缩略图），上传文件实体存 infra 文件服务。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 主键，`@TableId` |
| accountId | Long | account_id | 公众号账号编号，关联 `MpAccountDO.id` |
| appId | String | app_id | 冗余 `MpAccountDO.appId` |
| mediaId | String | media_id | 公众号素材 id（微信平台返回） |
| type | String | type | 文件类型，枚举 `WxConsts.MediaFileType`（image/voice/video/thumb/news 等） |
| permanent | Boolean | permanent | 是否永久：true 永久素材、false 临时素材 |
| url | String | url | 文件服务器的 URL（本系统 infra 文件服务地址） |
| name | String | name | 名字。永久素材非空；临时素材可能为空（粉丝主动发的图片/语音为空，主动发给粉丝的非空） |
| mpUrl | String | mp_url | 公众号文件 URL，仅永久素材使用 |
| title | String | title | 视频素材的标题，仅永久素材使用 |
| introduction | String | introduction | 视频素材的描述，仅永久素材使用 |

**继承**: BaseDO

**索引**: 主键 `id`。无 DDL 可确证其他索引；按 `(account_id, permanent, type)` 分页是素材列表的主要查询路径。

**外部依赖**: 文件本体通过 infra 模块的 `FileApi` 上传（`url` 字段指向 infra 文件服务），`mediaId`/`mpUrl` 由微信素材接口返回。

## 3. 实体关系

所有业务表以 `MpAccountDO`（mp_account）为中心呈星型从属关系，逻辑外键均为 `account_id → mp_account.id`，并冗余 `app_id` 字符串列便于直接按公众号检索与构建微信 SDK 调用上下文：

```
                                ┌─────────────────┐
                                │   mp_account    │  (TenantBaseDO, 带 tenantId)
                                │  公众号账号(聚合根) │
                                └───────┬─────────┘
                 id = account_id（各表同时冗余 app_id） │
        ┌──────────────┬──────────────┼──────────────┬──────────────┐
        │              │              │              │              │
  ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴──────┐  ┌────┴──────┐
  │  mp_user  │  │  mp_tag   │  │  mp_menu  │  │mp_material │  │ mp_message│
  │ 粉丝      │  │ 标签       │  │ 菜单(树形) │  │ 素材        │  │ 消息       │
  └─────┬─────┘  └─────┬─────┘  └───────────┘  └────────────┘  └─────┬─────┘
        │              ▲                                             │
        │  tag_ids []  │ tagId（微信标签id，非主键id）                    │ user_id
        └──────────────┘                                             ▼
                                                          mp_user.id（粉丝）
```

关键关系说明：

- **mp_user.tagIds → mp_tag.tagId**：粉丝的标签编号数组关联的是标签表的 `tag_id`（微信标签 id），**不是** mp_tag 的主键 `id`，两者数值不同，极易混淆；`tagIds` 以逗号分隔字符串落库（`LongListTypeHandler`），无中间关联表。
- **mp_message.user_id → mp_user.id**：消息归属粉丝，冗余 `openid`；配合 `send_from`（1 粉丝→公众号、2 公众号→粉丝）可还原完整会话。
- **mp_menu.parent_id → mp_menu.id**：自关联树形结构，顶级菜单 `parent_id = 0`（`ID_ROOT` 常量）；一个账号保存一份完整菜单树，同步到微信平台。
- **mp_message / mp_menu / mp_auto_reply 的图文 JSON 结构复用**：三者的 NEWS 消息体统一使用 `MpMessageDO.Article` 内嵌类，`JacksonTypeHandler` 以 JSON 列存储（对应表均需 `autoResultMap = true`）。
- **mp_tag ↔ 微信平台**：标签主数据在微信平台，本表为同步副本（增删改先调微信、成功后落库；`count` 需手动同步刷新）。
- **不落库的域**：草稿、发布、数据统计三个功能实时调用微信接口，响应直接使用 SDK 类型（WxMpDraftItem / WxMpFreePublishItem / WxDataCube*），不产生任何表数据。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|------|-----|------|
| mp_account | MpAccountDO | 公众号账号（唯一带 tenantId 的多租户表，聚合根） |
| mp_user | MpUserDO | 公众号粉丝（关注状态、地区、标签数组） |
| mp_tag | MpTagDO | 公众号标签（微信标签同步副本，tagId 为微信标签 id） |
| mp_menu | MpMenuDO | 公众号自定义菜单（树形 + 点击回复消息配置） |
| mp_message | MpMessageDO | 公众号消息（收发双向，含事件推送，内嵌 Article 图文结构） |
| mp_auto_reply | MpAutoReplyDO | 公众号自动回复（关注/消息/关键词三类规则） |
| mp_message_template | MpMessageTemplateDO | 公众号模板消息（模板元数据缓存） |
| mp_material | MpMaterialDO | 公众号素材（临时/永久，文件实体存 infra 文件服务） |
