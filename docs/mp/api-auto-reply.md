# 自动回复 API

> 对应 Controller：`MpAutoReplyController` | 路径前缀：`/mp/auto-reply`

## 功能说明

管理公众号自动回复规则，支持关注回复、消息回复、关键词回复三种类型。当粉丝发送消息或关注公众号时，系统自动匹配规则并回复。

## 数据模型

### MpAutoReplyDO

继承 `BaseDO`。

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

### 索引

- `idx_account_id` - 账号 ID 索引

## 核心服务

### MpAutoReplyService

| 方法 | 说明 |
|------|------|
| 创建规则 | 创建自动回复规则 |
| 更新规则 | 修改自动回复规则 |
| 删除规则 | 删除自动回复规则 |
| replyForSubscribe | 处理关注回复 |
| replyForMessage | 处理消息回复（关键词匹配 + 默认回复） |

## 回复类型

| 类型 | 枚举值 | 说明 |
|------|--------|------|
| 关注回复 | `MpAutoReplyTypeEnum.SUBSCRIBE (1)` | 粉丝关注公众号时触发 |
| 消息回复 | `MpAutoReplyTypeEnum.MESSAGE (2)` | 粉丝发送消息时触发（无关键词匹配时的默认回复） |
| 关键词回复 | `MpAutoReplyTypeEnum.KEYWORD (3)` | 粉丝发送的消息匹配关键词时触发 |

## 匹配模式

| 模式 | 枚举值 | 说明 |
|------|--------|------|
| 完全匹配 | `MpAutoReplyMatchEnum.FULL (1)` | 消息内容与关键词完全一致 |
| 半匹配 | `MpAutoReplyMatchEnum.HALF (2)` | 消息内容包含关键词 |

## 处理流程

```
粉丝发送消息 -> MessageAutoReplyHandler.handle()
             -> 查询关键词回复规则
             -> 匹配成功：返回关键词回复
             -> 匹配失败：查询消息回复规则（默认回复）
             -> 返回响应
```

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- 关注回复由 `SubscribeHandler` 触发
- 消息回复由 `MessageAutoReplyHandler` 触发
- 回复内容可引用素材（`response_media_id`）

## 设计要点

- 每个公众号可配置多条关键词回复规则
- 关键词匹配优先级：完全匹配 > 半匹配
- 无关键词匹配时回退到消息回复（默认回复）
- 回复类型支持文本、图文、媒体等多种形式
