# 消息管理 API

> 对应 Controller：`MpMessageController`、`MpMessageTemplateController` | 路径前缀：`/mp/message`、`/mp/message-template`

## 功能说明

处理公众号消息的接收与发送，包括客服消息、模板消息、消息记录查询等。

## 数据模型

### MpMessageDO

继承 `BaseDO`。

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

### MpMessageDO.Article（值对象）

图文消息，包含标题、描述、图片链接、跳转链接。

### MpMessageTemplateDO

继承 `BaseDO`。

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

## 核心服务

### MpMessageService

| 方法 | 说明 |
|------|------|
| 接收消息 | 处理微信回调消息，保存到数据库 |
| 发送客服消息 | 向指定粉丝发送客服消息 |
| 分页查询 | 按条件查询消息记录 |

### MpMessageTemplateService

| 方法 | 说明 |
|------|------|
| 同步模板 | 从微信 API 同步模板列表 |
| 发送模板消息 | 向粉丝发送模板消息 |
| 分页查询 | 查询模板列表 |

## 消息处理流程

```
微信回调 -> MpOpenController.handleMessage()
         -> 签名校验
         -> WxMpMessageRouter 路由
         -> Handler 处理（SubscribeHandler / MessageAutoReplyHandler 等）
         -> 保存消息记录
         -> 返回响应
```

## 枚举定义

| 枚举 | 说明 |
|------|------|
| `MpMessageSendFromEnum` | 消息发送方向：1 粉丝发给公众号、2 公众号发给粉丝 |

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- 通过 `user_id` 关联 `mp_user`
- 模板消息通过 `MpMessageTemplateDO` 管理模板配置

## 设计要点

- 消息类型通过 `type` 字段区分（text/image/voice/video/event 等）
- 图文消息使用 JSON 存储 `articles` 数组
- 消息接收使用异步处理，避免阻塞微信回调响应
- 模板消息发送失败时抛出业务异常
