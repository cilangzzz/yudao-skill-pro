# 消息收发接口

## 概述

消息收发是 IM 模块的核心功能，涵盖私聊消息、群聊消息和频道广播消息三种场景，支持多种消息类型、幂等发送、消息撤回、已读回执等能力。

### 业务定位

- 私聊消息：一对一聊天，支持发送者和接收者双向拉取
- 群聊消息：群组聊天，支持 @提醒、已读统计
- 频道消息：单向广播，管理员发布推送给指定用户
- 消息类型兼容 OpenIM 协议编号体系

### 核心实体

| 实体 | 说明 |
|-----|------|
| PrivateMessageDO | 私聊消息，包含 clientMessageId（幂等）、senderId、receiverId、type、content（JSON）、status |
| GroupMessageDO | 群聊消息，包含 clientMessageId、senderId、groupId、atUserIds、receiptStatus、readCount |
| ChannelMessageDO | 频道广播消息，包含 materialId、receiverUserIds、sendTime |

## 私聊消息接口

### 1. 发送私聊消息

- **路径**: `POST /im/message/private/send`
- **说明**: 发送私聊消息
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| clientMessageId | String | 是 | 客户端消息 ID（用于幂等去重） |
| receiverId | Long | 是 | 接收者用户 ID |
| type | Integer | 是 | 消息类型（文本/图片/语音/视频/文件等） |
| content | String | 是 | 消息内容（JSON 格式） |

- **响应**: `CommonResult<PrivateMessageDO>` - 发送的消息记录
- **实现逻辑**:
  1. 校验接收者存在
  2. 检查 `clientMessageId` 是否已存在（幂等校验）
  3. 敏感词过滤处理
  4. 保存消息到 `im_private_message` 表
  5. 事务提交后异步推送给接收者（afterCommit 回调）

### 2. 拉取私聊消息

- **路径**: `GET /im/message/private/pull`
- **说明**: 拉取与指定用户的聊天消息（增量拉取）
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| userId | Long | 是 | 对方用户 ID |
| maxMessageId | Long | 否 | 最大消息 ID（拉取此 ID 之后的消息） |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<List<PrivateMessageDO>>` - 消息列表

### 3. 标记私聊已读

- **路径**: `PUT /im/message/private/read`
- **说明**: 标记与指定用户的消息为已读
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| userId | Long | 是 | 对方用户 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**: 更新 Redis 中当前用户与对方会话的最大已读消息 ID

### 4. 获取最大已读消息 ID

- **路径**: `GET /im/message/private/max-read-message-id`
- **说明**: 获取与指定用户会话中当前用户已读的最大消息 ID
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| userId | Long | 是 | 对方用户 ID |

- **响应**: `CommonResult<Long>` - 最大已读消息 ID

### 5. 撤回私聊消息

- **路径**: `DELETE /im/message/private/recall`
- **说明**: 撤回已发送的私聊消息
- **权限**: 需要用户登录（消息发送者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| messageId | Long | 是 | 消息 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验消息存在且当前用户是发送者
  2. 校验消息在撤回时间窗口内
  3. 更新消息状态为"已撤回"
  4. 事务提交后异步通知对方

### 6. 获取私聊消息列表

- **路径**: `GET /im/message/private/list`
- **说明**: 分页查询私聊消息列表（管理端）
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| senderId | Long | 否 | 发送者 ID |
| receiverId | Long | 否 | 接收者 ID |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<PrivateMessageDO>>`

## 群聊消息接口

### 7. 发送群聊消息

- **路径**: `POST /im/message/group/send`
- **说明**: 在群组中发送消息
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| clientMessageId | String | 是 | 客户端消息 ID（幂等） |
| groupId | Long | 是 | 群组 ID |
| type | Integer | 是 | 消息类型 |
| content | String | 是 | 消息内容（JSON） |
| atUserIds | List<Long> | 否 | @的用户 ID 列表 |

- **响应**: `CommonResult<GroupMessageDO>` - 发送的消息记录
- **实现逻辑**:
  1. 校验群组存在且未被封禁
  2. 校验发送者是群成员
  3. 校验是否被禁言（全员禁言或个人禁言）
  4. 检查 `clientMessageId` 幂等
  5. 敏感词过滤
  6. 保存消息到 `im_group_message` 表
  7. 事务提交后异步推送给群成员

### 8. 拉取群聊消息

- **路径**: `GET /im/message/group/pull`
- **说明**: 拉取群组的聊天消息（增量拉取）
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |
| maxMessageId | Long | 否 | 最大消息 ID |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<List<GroupMessageDO>>`

### 9. 标记群聊已读

- **路径**: `PUT /im/message/group/read`
- **说明**: 标记群组消息为已读
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |

- **响应**: `CommonResult<Boolean>`

### 10. 获取群聊最大已读消息 ID

- **路径**: `GET /im/message/group/max-read-message-id`
- **说明**: 获取当前用户在指定群组中已读的最大消息 ID
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |

- **响应**: `CommonResult<Long>`

### 11. 撤回群聊消息

- **路径**: `DELETE /im/message/group/recall`
- **说明**: 撤回已发送的群聊消息
- **权限**: 需要用户登录（消息发送者或群主/管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| messageId | Long | 是 | 消息 ID |

- **响应**: `CommonResult<Boolean>`

### 12. 获取群聊消息列表

- **路径**: `GET /im/message/group/list`
- **说明**: 分页查询群聊消息列表
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 否 | 群组 ID |
| senderId | Long | 否 | 发送者 ID |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<GroupMessageDO>>`

## 频道消息接口

### 13. 发送频道消息

- **路径**: `POST /im/message/channel/send`
- **说明**: 向频道发送广播消息
- **权限**: 需要用户登录（频道管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| channelId | Long | 是 | 频道 ID |
| materialId | Long | 是 | 关联素材 ID |
| receiverUserIds | List<Long> | 否 | 接收用户 ID 列表（为空则广播全部） |

- **响应**: `CommonResult<ChannelMessageDO>`

### 14. 拉取频道消息

- **路径**: `GET /im/message/channel/pull`
- **说明**: 拉取频道的广播消息
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| channelId | Long | 是 | 频道 ID |
| maxMessageId | Long | 否 | 最大消息 ID |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<List<ChannelMessageDO>>`

### 15. 获取频道消息列表

- **路径**: `GET /im/message/channel/list`
- **说明**: 分页查询频道消息列表
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| channelId | Long | 否 | 频道 ID |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ChannelMessageDO>>`

## 关键实现

- **PrivateMessageService**: 私聊消息服务，管理消息的发送、拉取、已读、撤回
- **GroupMessageService**: 群聊消息服务，管理群消息的发送、拉取、已读、撤回
- **ChannelMessageService**: 频道消息服务，管理广播消息的发送和拉取
- **幂等发送**: 通过 `clientMessageId` 字段在数据库层面去重，避免网络重试导致重复消息
- **事务感知推送**: 使用 `TransactionSynchronizationManager.registerSynchronization(afterCommit)` 确保事务提交后再推送
- **Redis 已读游标**: 使用 Redis 存储 `im:read:cursor:{userId}:{targetId}` 格式的已读游标，避免频繁更新数据库
- **敏感词过滤**: 发送消息前通过 `sensitive-word` 库进行敏感词检测和替换
