# 即时通讯模块 (im)

> im 模块是系统的"即时通讯层"，提供私聊、群聊、消息收发、消息撤回、已读回执、RTC 实时通话、表情系统、频道广播等全链路即时通讯能力。

## 模块概述

- **模块路径**: yudao-module-im
- **业务定位**: 面向终端用户的即时通讯模块，支持单聊、群聊、频道广播及 RTC 音视频通话
- **核心职责**: 好友关系管理、群组管理、消息收发与存储、已读回执、消息撤回、表情包管理、RTC 通话、敏感词过滤

## 核心功能点

| 功能 | 说明 | 关键实体 |
|-----|------|---------|
| 好友关系管理 | 双向好友关系（每对好友 2 行记录），支持拉黑、免打扰、置顶、备注名 | FriendDO, FriendRequestDO |
| 群组管理 | 创建/解散群组，群主/管理员/普通成员三级角色，支持禁言、审批入群 | GroupDO, GroupMemberDO, GroupRequestDO |
| 私聊消息 | 一对一聊天，支持多种消息类型（文本/图片/语音/视频/文件等），clientMessageId 幂等发送 | PrivateMessageDO |
| 群聊消息 | 群组聊天，支持 @提醒、已读回执统计、消息置顶 | GroupMessageDO |
| 频道广播 | 单向广播频道，管理员发布素材推送给指定用户 | ChannelDO, ChannelMessageDO, ChannelMaterialDO |
| 消息撤回 | 发送者可撤回已发消息，需在时间窗口内 | PrivateMessageDO, GroupMessageDO |
| 已读回执 | 私聊/群聊已读状态跟踪，Redis 存储每个用户在每个群的最大已读消息 ID | PrivateMessageDO, GroupMessageDO |
| RTC 实时通话 | 音视频通话管理，集成 LiveKit，支持呼叫/接听/拒绝/取消/挂断 | RtcCallDO, RtcParticipantDO |
| 表情系统 | 系统表情包 + 用户私人表情，支持表情包的启用/禁用 | FacePackDO, FacePackItemDO, FaceUserItemDO |
| 敏感词过滤 | 基于 Trie 树的敏感词检测和替换 | SensitiveWordDO |

## API 接口索引

| 接口域 | 路径前缀 | 说明 | 权限 |
|-------|---------|------|------|
| 好友管理 | `/im/friend` | 好友列表、删除、更新、拉黑/取消拉黑 | 无需 RBAC（用户端） |
| 好友请求 | `/im/friend-request` | 申请、同意、拒绝好友请求 | 无需 RBAC（用户端） |
| 群组管理 | `/im/group` | 创建/解散群组、邀请/退出/踢人、管理员、禁言、置顶消息 | 无需 RBAC（用户端） |
| 群成员管理 | `/im/group-member` | 群成员列表、更新成员信息 | 无需 RBAC（用户端） |
| 群组请求 | `/im/group-request` | 申请入群、邀请入群、审批流程 | 无需 RBAC（用户端） |
| 私聊消息 | `/im/message/private` | 发送、拉取、已读、撤回、消息列表 | 无需 RBAC（用户端） |
| 群聊消息 | `/im/message/group` | 发送、拉取、已读、撤回、消息列表 | 无需 RBAC（用户端） |
| 频道消息 | `/im/message/channel` | 频道消息拉取、列表 | 无需 RBAC（用户端） |
| 频道素材 | `/im/channel/material` | 获取频道素材 | 无需 RBAC（用户端） |
| 表情管理 | `/im/face-pack`, `/im/face-user-item` | 系统表情包列表、用户私人表情管理 | 无需 RBAC（用户端） |
| RTC 通话 | `/im/rtc`, `/im/livekit` | 创建通话、邀请、加入、接听、拒绝、取消、离开、LiveKit Webhook | 无需 RBAC（用户端） |
| 管理后台 | `/im/manager/*` | 频道/表情/好友/群组/消息/RTC/敏感词管理 + 统计面板 | im:xxx:xxx（RBAC） |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| im_channel | 频道表 | BaseDO | code, name, avatar, sort, status |
| im_channel_material | 频道素材表 | BaseDO | title, coverUrl, summary, content, url |
| im_channel_message | 频道消息表 | BaseDO | materialId, receiverUserIds, sendTime |
| im_face_pack | 表情包表 | BaseDO | name, icon, sort, status |
| im_face_pack_item | 表情项表 | BaseDO | packId, url, name, width, height |
| im_face_user_item | 用户表情表 | BaseDO | userId, url, name, width, height |
| im_friend | 好友关系表 | BaseDO | userId, friendId, silent, pinned, blocked, displayName |
| im_friend_request | 好友请求表 | BaseDO | userId, friendId, applyContent, handleResult |
| im_group | 群组表 | BaseDO | name, ownerId, avatar, notice, joinApproval, banned, mutedAll |
| im_group_member | 群成员表 | BaseDO | groupId, userId, role, muteEndTime, addSource |
| im_group_request | 群组请求表 | BaseDO | groupId, userId, type, handleResult |
| im_private_message | 私聊消息表 | BaseDO | clientMessageId, senderId, receiverId, type, content, status |
| im_group_message | 群聊消息表 | BaseDO | clientMessageId, senderId, groupId, atUserIds, receiptStatus, readCount |
| im_rtc_call | RTC 通话表 | BaseDO | roomId, conversationType, mediaType, inviterUid, status |
| im_rtc_participant | RTC 参与者表 | BaseDO | callId, userId, role, status |
| im_sensitive_word | 敏感词表 | BaseDO | word, status |

## 设计模式

- **双层 Controller 模式**: 用户端 Controller（无 RBAC，通过登录态鉴权）+ Manager 端 Controller（RBAC 权限控制），分离普通用户操作和管理后台操作
- **双向好友模型**: 每对好友在 `im_friend` 表中存储 2 行记录（A->B 和 B->A），各自拥有独立的 silent/pinned/blocked/displayName 属性
- **幂等消息发送**: 通过 `clientMessageId` 字段实现客户端消息去重，避免网络重试导致重复消息
- **事务感知异步推送**: 消息推送使用 `afterCommit` 回调，确保数据库事务提交后再推送，避免读到未提交数据
- **Redis 已读游标**: 使用 Redis 存储每个用户在每个会话中的最大已读消息 ID，避免频繁更新数据库
- **LiveKit Webhook 安全**: LiveKit Webhook 接口使用 JWT + SHA256 签名验证，同时标记 `@PermitAll` + `@TenantIgnore`
- **Trie 树敏感词过滤**: 使用 sensitive-word 库实现基于 Trie 树的高效敏感词检测和替换
- **OpenIM 兼容消息类型**: 消息类型编号兼容 OpenIM 协议，便于与 OpenIM 生态对接
- **配置驱动**: 模块配置统一在 `yudao.im.*` 命名空间下，通过 `ImProperties` 类管理

## 依赖关系

### 内部依赖

| 模块 | 用途 |
|-----|------|
| yudao-module-system | AdminUserApi - 查询用户信息、校验用户存在性 |
| yudao-module-infra | 文件存储（头像、图片、文件消息等） |
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |
| yudao-framework-redis | Redis 操作封装，用于已读游标存储 |
| yudao-framework-tenant | 租户支持 |

### 外部依赖

| 库 | 用途 |
|---|------|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| sensitive-word | 基于 Trie 树的敏感词过滤库 |
| pinyin4j | 汉字转拼音，用于敏感词拼音匹配 |
| LiveKit | 开源实时音视频通信框架，RTC 能力支撑 |
| Swagger/OpenAPI | API 文档注解 |

## 模块间通信

| 接口 | 方法 | 说明 | 调用方 |
|-----|------|------|-------|
| AdminUserApi | getUser() | 查询用户基本信息 | im 模块内部（好友信息、群成员信息展示） |
| AdminUserApi | getUsers() | 批量查询用户信息 | im 模块内部（消息列表中展示发送者信息） |
| FileApi | createFile() | 上传文件（头像、图片消息、文件消息） | im 模块内部 |

## 详细文档

- [api-friend.md](api-friend.md) - 好友与好友请求接口
- [api-group.md](api-group.md) - 群组与群成员接口
- [api-message.md](api-message.md) - 消息收发接口
- [api-channel.md](api-channel.md) - 频道与素材接口
- [api-face.md](api-face.md) - 表情系统接口
- [api-rtc.md](api-rtc.md) - RTC 通话接口
- [api-manager.md](api-manager.md) - 管理后台接口
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项
