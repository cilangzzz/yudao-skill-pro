# 数据模型

## 实体继承体系

- `MpAccountDO` 继承 `TenantBaseDO`，支持多租户隔离
- 其他实体继承 `BaseDO`

## 核心数据表

### mp_account（公众号账号表）

聚合根，管理公众号配置信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| name | String | 公众号名称 |
| account | String | 公众号账号 |
| app_id | String | 公众号 AppId |
| app_secret | String | 公众号密钥 |
| token | String | 公众号 Token |
| aes_key | String | 消息加解密密钥 |
| qr_code_url | String | 二维码图片 URL |
| remark | String | 备注 |

索引：`uk_app_id(app_id)`

### mp_user（公众号粉丝表）

聚合根，关联粉丝标签和消息记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| openid | String | 粉丝标识 OpenId |
| union_id | String | 微信生态唯一标识 |
| subscribe_status | Integer | 关注状态（1 已关注 / 2 取消关注） |
| subscribe_time | LocalDateTime | 关注时间 |
| unsubscribe_time | LocalDateTime | 取消关注时间 |
| nickname | String | 昵称 |
| head_image_url | String | 头像地址 |
| language | String | 语言 |
| country | String | 国家 |
| province | String | 省份 |
| city | String | 城市 |
| remark | String | 备注 |
| tag_ids | List\<Long\> | 标签 ID 数组 |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId（冗余） |

索引：`idx_account_id(account_id)`、`uk_appid_openid(app_id, openid)`

### mp_message（公众号消息表）

聚合根，包含自动回复配置和消息模板。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| msg_id | Long | 微信消息 ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| user_id | Long | 粉丝编号 |
| openid | String | 粉丝 OpenId |
| type | String | 消息类型（text/image/voice/video 等） |
| send_from | Integer | 消息来源（1 粉丝发给公众号 / 2 公众号发给粉丝） |
| content | String | 文本消息内容 |
| media_id | String | 媒体文件 ID |
| media_url | String | 媒体文件 URL |
| recognition | String | 语音识别文本 |
| format | String | 语音格式 |
| title | String | 标题 |
| description | String | 描述 |
| thumb_media_id | String | 缩略图媒体 ID |
| thumb_media_url | String | 缩略图 URL |
| url | String | 链接地址 |
| location_x | Double | 地理位置纬度 |
| location_y | Double | 地理位置经度 |
| scale | Double | 地图缩放级别 |
| label | String | 地理位置信息 |
| articles | List\<Article\> | 图文消息数组（JSON） |
| music_url | String | 音乐链接 |
| hq_music_url | String | 高质量音乐链接 |
| event | String | 事件类型 |
| event_key | String | 事件 Key 值 |

索引：`idx_account_id(account_id)`、`idx_user_id(user_id)`

### mp_material（公众号素材表）

聚合根，管理临时素材和永久素材。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| media_id | String | 微信素材 ID |
| type | String | 文件类型（image/voice/video/thumb） |
| permanent | Boolean | 是否永久素材 |
| url | String | 文件服务器 URL |
| name | String | 文件名称 |
| mp_url | String | 公众号文件 URL（永久素材） |
| title | String | 视频素材标题 |
| introduction | String | 视频素材描述 |

索引：`idx_account_id(account_id)`、`idx_media_id(media_id)`

### mp_menu（公众号菜单表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| name | String | 菜单名称 |
| menu_key | String | 菜单标识 |
| parent_id | Long | 父菜单 ID |
| type | String | 按钮类型（click/view/miniprogram 等） |
| url | String | 网页链接 |
| mini_program_app_id | String | 小程序 AppId |
| mini_program_page_path | String | 小程序页面路径 |
| article_id | String | 跳转图文媒体 ID |
| reply_message_type | String | 回复消息类型 |
| reply_content | String | 回复文本内容 |
| reply_media_id | String | 回复媒体 ID |
| reply_media_url | String | 回复媒体 URL |
| reply_articles | List\<Article\> | 回复图文消息（JSON） |

索引：`idx_account_id(account_id)`

### mp_auto_reply（公众号自动回复表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| type | Integer | 回复类型（1 关注回复 / 2 消息回复 / 3 关键词回复） |
| request_keyword | String | 请求关键词 |
| request_match | Integer | 关键词匹配模式（1 完全匹配 / 2 半匹配） |
| request_message_type | String | 请求消息类型 |
| response_message_type | String | 响应消息类型 |
| response_content | String | 响应文本内容 |
| response_media_id | String | 响应媒体 ID |
| response_media_url | String | 响应媒体 URL |
| response_articles | List\<Article\> | 响应图文消息（JSON） |

索引：`idx_account_id(account_id)`

### mp_message_template（公众号模板消息表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| template_id | String | 模板 ID |
| title | String | 模板标题 |
| content | String | 模板内容 |
| example | String | 模板示例 |
| primary_industry | String | 一级行业 |
| deputy_industry | String | 二级行业 |

索引：`idx_account_id(account_id)`、`idx_template_id(template_id)`

### mp_tag（公众号标签表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| tag_id | Long | 微信标签 ID |
| name | String | 标签名称 |
| count | Integer | 标签下粉丝数 |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |

索引：`idx_account_id(account_id)`

## ER 关系

```
mp_account (1) <-- (N) mp_user
mp_account (1) <-- (N) mp_message
mp_account (1) <-- (N) mp_material
mp_account (1) <-- (N) mp_menu
mp_account (1) <-- (N) mp_auto_reply
mp_account (1) <-- (N) mp_message_template
mp_account (1) <-- (N) mp_tag
mp_user    (1) <-- (N) mp_message
```

所有子表通过 `account_id` 外键关联 `mp_account`。`mp_message` 同时通过 `user_id` 关联 `mp_user`。

## 值对象

| 值对象 | 说明 |
|--------|------|
| `MpMessageDO.Article` | 图文消息，包含标题、描述、图片链接、跳转链接 |

## 枚举定义

| 枚举 | 说明 |
|------|------|
| `MpAutoReplyTypeEnum` | 自动回复类型：关注回复(1)、消息回复(2)、关键词回复(3) |
| `MpAutoReplyMatchEnum` | 关键词匹配模式：完全匹配(1)、半匹配(2) |
| `MpMessageSendFromEnum` | 消息发送方向：粉丝发给公众号(1)、公众号发给粉丝(2) |
