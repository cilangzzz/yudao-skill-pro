# 即时通讯模块 (im)

> 站内即时通讯后端：单聊 / 群聊 / 频道三大会话形态，消息收发、撤回、已读、回执全链路，配套好友关系、加群审批、表情包、LiveKit 实时音视频通话、敏感词过滤与运营数据看板。

## 模块概述

- **模块路径**: yudao-module-im
- **业务定位**: 提供面向管理后台（Web 客户端）的即时通讯能力，覆盖三类会话（私聊 PRIVATE / 群聊 GROUP / 频道 CHANNEL）的消息收发、撤回、已读与回执，以及好友关系与申请审批、群组生命周期管理（邀请、踢人、禁言、转让、置顶、封禁）、表情包体系、实时音视频通话（LiveKit 信令 + Webhook 兜底）、敏感词拦截和运营侧的消息审计与数据看板。客户端采用「HTTP 增量拉取（/pull 游标）+ WebSocket 实时推送（notification）」双通道同步消息，保证离线补偿与实时可达。
- **技术栈**: Spring Boot（版本由父工程 yudao-dependencies 统一管理，本模块代码使用 `javax.*` 命名空间）/ MyBatis-Plus / Redis / houbb sensitive-word（Trie 树敏感词匹配）/ pinyin4j（拼音检索引擎）/ LiveKit（自研 HTTP + JWT 的 Twirp 客户端，无官方 SDK 依赖）/ 复用 infra 模块 WebSocketSenderApi 做 WebSocket 推送 / 复用 quartz 框架的 JobHandler（由 yudao-server 运行时提供）

## 设计原则

| 原则 | 说明 |
|---|---|
| HTTP 拉取 + WebSocket 推送双通道 | 每个会话域都提供 `/pull` 增量游标接口（重连 / 离线补偿）；实时事件统一经 infra 的 WebSocketSenderApi 推送，且延迟到事务提交后异步发送，避免客户端收到通知时数据库变更尚未可见 |
| 消息内容 JSON 多态 | 消息表 `content` 字段存 JSON，按 `ImContentTypeEnum`（101-105 直接复用 OpenIM 段位）映射 12 种内容结构类（文本 / 图片 / 语音 / 视频 / 文件 / 合并转发 / 名片 / 表情 / 素材 / 引用 / 撤回 / 位置） |
| 用户侧与管理侧分离 | `controller/admin` 业务域包面向登录用户（仅认证、无权限点），`controller/admin/manager` 面向运营后台（`im:manager:{域}:{操作}` 权限点），两侧复用同一套 Service |
| 会话内权限内聚在 Service 层 | 群操作（禁言、转让、置顶、踢人、审批）由 Service 校验群主 / 管理员角色并推送对应事件通知；管理后台只额外提供封禁 / 解散等全局干预能力 |
| 可靠性多层兜底 | RTC 通话采用「Webhook 回调 + 僵尸通话清理 Job + 振铃超时 Job」三层兜底；消息撤回有时限、发送前敏感词拦截、群消息有回执与已读人数统计 |
| 多租户兼容 | DO 继承 `BaseDO`（表无 tenant_id 字段），但运行在租户上下文中：RTC Job 用 `@TenantJob` 遍历租户执行，敏感词词库按租户用 Guava LoadingCache 缓存，LiveKit Webhook 用 `@TenantIgnore` + `@PermitAll` 放行 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|---|---|---|
| 好友关系 | 好友列表 / 增量拉取、单向软删除、备注与免打扰、置顶、拉黑与解除；好友申请的发起 / 同意 / 拒绝及 WebSocket 通知 | ImFriendDO、ImFriendRequestDO |
| 群聊 | 群创建 / 解散 / 信息维护、邀请与审批进群、踢人、群管理员增撤、群主转让、消息置顶、全群与成员禁言、封禁 | ImGroupDO、ImGroupMemberDO、ImGroupRequestDO |
| 单聊 / 群聊消息 | 消息发送（clientMessageId 幂等）、增量拉取、已读与回执、撤回（有时限）、@ 全体（atUserIds 含 -1 特殊值）、历史查询 | ImPrivateMessageDO、ImGroupMessageDO |
| 频道与频道消息 | 频道 / 素材（图文卡片）管理、运营侧立即推送频道消息、客户端按 minId 游标增量拉取与已读 | ImChannelDO、ImChannelMaterialDO、ImChannelMessageDO |
| 会话已读位点 | 按用户 + 会话维度记录已读消息 id，支持增量拉取（重连 / 离线补偿） | ImConversationReadDO |
| 表情包 | 官方表情包及表情项管理、用户个人表情上传 / 删除 | ImFacePackDO、ImFacePackItemDO、ImFaceUserItemDO |
| 实时通话 (RTC) | 私聊 / 群聊音视频通话信令（创建、邀请、加入、接听、拒绝、取消、离开）、LiveKit Webhook 兜底、振铃超时与僵尸通话清理 Job、通话记录审计 | ImRtcCallDO、ImRtcParticipantDO |
| 敏感词过滤 | 敏感词 CRUD + 批量删除，词库按租户缓存，消息发送前 Trie 匹配拦截 | ImSensitiveWordDO |
| 运营数据看板 | 数据概览、消息趋势（私聊 / 群聊双线）、用户趋势、内容类型分布、群规模分布、TOP 发送者 | ImPrivateMessageDO、ImGroupMessageDO |
| WebSocket 通知 | 40+ 种通知 DTO（好友 / 群 / 消息 / RTC 四族），事务提交后异步推送 | ImNotificationWebSocketDTO |

## API 接口索引

> 模块共 30 个 Controller、127 个端点（超过 120），此处按业务域分节给出控制器摘要与代表性端点，完整端点清单见各 `api-{key}.md`。

### 频道与素材 (19 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImChannelManagerController | 频道管理（运营侧：增删改查 + 精简列表） | 6 |
| ImChannelMaterialManagerController | 频道素材管理（运营侧：图文卡片增删改查 + 精简列表） | 6 |
| ImChannelMessageManagerController | 频道消息管理（运营侧：立即推送 / 删除 / 分页 / 详情） | 4 |
| ImChannelMessageController | 频道消息（客户端：离线增量拉取 / 已读） | 2 |
| ImChannelMaterialController | 频道素材详情（客户端：图文卡片渲染） | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/manager/channel/create | POST | 新增频道 | im:manager:channel:create |
| /im/manager/channel-message/send | POST | 立即推送频道消息 | im:manager:channel-message:send |
| /im/channel/message/pull | GET | 拉取频道消息（离线增量），按 minId 游标分页 | 已认证 |
| /im/channel/material/get | GET | 获取素材详情，用于客户端点击图文卡片渲染详情页 | 已认证 |

### 表情包 (18 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImFacePackManagerController | 表情包管理（运营侧 CRUD + 批量删除） | 6 |
| ImFacePackItemManagerController | 表情项管理（运营侧 CRUD + 批量删除） | 6 |
| ImFaceUserItemController | 个人表情（客户端：列表 / 添加 / 删除） | 3 |
| ImFaceUserItemManagerController | 用户表情管理（运营侧：分页 / 删除） | 2 |
| ImFacePackController | 启用中的表情包列表（含表情项，客户端） | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/manager/face-pack/delete-list | DELETE | 批量删除表情包 | im:manager:face-pack:delete |
| /im/manager/face-user-item/page | GET | 获得用户表情分页 | im:manager:face-user-item:query |
| /im/face-user-item/create | POST | 添加个人表情 | 已认证 |
| /im/face-pack/list | GET | 获得启用的表情包列表（含表情） | 已认证 |

### 好友与申请 (15 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImFriendController | 好友（列表 / 增量 / 详情 / 删除 / 备注 / 拉黑 / 解除拉黑） | 7 |
| ImFriendRequestController | 好友申请（发起 / 同意 / 拒绝 / 游标列表 / 增量 / 单查） | 6 |
| ImFriendManagerController | 好友关系分页（运营侧） | 1 |
| ImFriendRequestManagerController | 好友申请分页（运营侧） | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/friend/block | PUT | 拉黑好友（必须先是好友；单边屏蔽对方私聊消息） | 已认证 |
| /im/friend-request/apply | POST | 发起好友申请 | 已认证 |
| /im/friend-request/list | GET | 查询「我相关」的好友申请列表（游标分页） | 已认证 |
| /im/manager/friend/page | GET | 获得好友关系分页 | im:manager:friend:query |

### 群聊 (33 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImGroupController | 群（创建 / 解散 / 邀请 / 退群 / 踢人 / 管理员增撤 / 转让群主 / 消息置顶 / 禁言） | 16 |
| ImGroupRequestController | 加群申请（申请 / 同意 / 拒绝 / 未处理列表 / 增量 / 按群查询 / 单查） | 7 |
| ImGroupMemberController | 群成员（更新 / 查询 / 按群全量列表） | 3 |
| ImGroupManagerController | 群管理（运营侧：分页 / 详情 / 封禁 / 解封 / 解散） | 5 |
| ImGroupMemberManagerController | 群成员列表（含已退群成员） | 1 |
| ImGroupRequestManagerController | 加群申请分页（运营侧） | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/group/create | POST | 创建群 | 已认证 |
| /im/group/transfer-owner | PUT | 转让群主 | 已认证 |
| /im/group/mute-member | PUT | 禁言成员 | 已认证 |
| /im/group-request/unhandled-list | GET | 「我管理的所有群」未处理加群申请（前端红点横幅） | 已认证 |
| /im/manager/group/ban | PUT | 封禁群 | im:manager:group:ban |

### 单聊 / 群聊消息与会话 (17 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImGroupMessageController | 群聊消息（发送 / 增量 / 已读 / 撤回 / 已读用户列表 / 历史） | 6 |
| ImPrivateMessageController | 私聊消息（发送 / 增量 / 已读 / 对方已读位点 / 撤回 / 历史） | 6 |
| ImConversationReadController | 会话读位置（增量拉取，重连 / 离线补偿） | 1 |
| ImGroupMessageManagerController | 群聊消息分页 / 详情（运营侧审计） | 2 |
| ImPrivateMessageManagerController | 私聊消息分页 / 详情（运营侧审计） | 2 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/message/group/send | POST | 发送群聊消息 | 已认证 |
| /im/message/group/recall | DELETE | 撤回群聊消息 | 已认证 |
| /im/message/private/max-read-message-id | GET | 查询对方已读到我发的最大消息 id | 已认证 |
| /im/manager/message/group/page | GET | 获得群聊消息分页 | im:manager:message:query |

### 实时通话 (13 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImRtcCallController | 通话信令（创建 / 邀请 / 加入 / 接听 / 拒绝 / 取消 / 离开 / 振铃超时检查 / 进行中查询） | 9 |
| ImRtcCallManagerController | 通话记录（运营侧：分页 / 详情 / 参与者列表） | 3 |
| ImRtcLiveKitController | LiveKit Webhook 回调（成员离开 / 房间结束业务态兜底清理） | 1 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/rtc/create | POST | 创建新通话，按 conversationType 区分私聊 / 群聊 | 已认证 |
| /im/rtc/get-active-call | GET | 查询进行中的通话，用于群聊顶部「N 人正在通话」胶囊条 | 已认证 |
| /im/livekit/webhook | POST | LiveKit Webhook 回调 | @PermitAll（另加 @TenantIgnore） |
| /im/manager/rtc/participant-list | GET | 获得通话参与者列表 | im:manager:rtc:query |

### 敏感词与数据看板 (12 端点)

| Controller | 说明 | 端点数 |
|---|---|---|
| ImSensitiveWordManagerController | 敏感词管理（CRUD / 批量删除 / 分页 / 详情） | 6 |
| ImStatisticsManagerController | 数据看板（概览 / 消息趋势 / 用户趋势 / 内容类型分布 / 群规模分布 / TOP 发送者） | 6 |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---|---|---|---|
| /im/manager/sensitive-word/delete-list | DELETE | 批量删除敏感词 | im:manager:sensitive-word:delete |
| /im/manager/statistics/overview | GET | 获得数据概览 | im:manager:statistics:query |
| /im/manager/statistics/top-senders | GET | 获得消息 TOP 发送者（最近 30 天） | im:manager:statistics:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|---|---|---|---|
| im_friend | 好友关系（单向记录） | BaseDO | user_id, friend_user_id, silent, display_name, add_source, pinned, blocked, status, add_time, delete_time |
| im_friend_request | 好友申请 | BaseDO | from_user_id, to_user_id, apply_content, display_name, add_source, handle_result, handle_content, handle_time |
| im_group | 群 | BaseDO | name, owner_user_id, avatar, notice, join_approval, banned, banned_reason, muted_all, pinned_message_ids(JSON), status, dissolved_time |
| im_group_member | 群成员 | BaseDO | group_id, user_id, display_user_name, group_remark, role, silent, status, join_time, add_source, inviter_user_id, quit_time, mute_end_time |
| im_group_request | 加群申请 | BaseDO | group_id, user_id, inviter_user_id, apply_content, add_source, handle_result, handle_user_id, handle_content, handle_time |
| im_private_message | 私聊消息 | BaseDO | client_message_id, sender_id, receiver_id, type, content(JSON), status, receipt_status, send_time |
| im_group_message | 群聊消息 | BaseDO | client_message_id, sender_id, group_id, type, content(JSON), status, receiver_user_ids(JSON), at_user_ids(JSON), receipt_status, read_count, send_time |
| im_channel | 频道（广播 / 公众号） | BaseDO | code, name, avatar, sort, status |
| im_channel_material | 频道素材（图文卡片） | BaseDO | channel_id, type, title, cover_url, summary, content, url |
| im_channel_message | 频道消息 | BaseDO | channel_id, material_id, type, content(JSON), receiver_user_ids(JSON), send_time |
| im_conversation_read | 会话读位置 | BaseDO | user_id, conversation_type, target_id, message_id, read_time |
| im_face_pack | 表情包 | BaseDO | name, icon, sort, status |
| im_face_pack_item | 表情包项 | BaseDO | pack_id, url, name, width, height, sort, status |
| im_face_user_item | 用户个人表情 | BaseDO | user_id, url, name, width, height, sort |
| im_rtc_call | 通话记录 | BaseDO | room, conversation_type, media_type, inviter_user_id, group_id, status, end_reason, start_time, accept_time, end_time |
| im_rtc_participant | 通话参与者 | BaseDO | call_id, room, user_id, role, status, invite_time, accept_time, leave_time |
| im_sensitive_word | 敏感词 | BaseDO | word, status |

> 消息正文 `content` 字段存 JSON，对应 `dal/dataobject/message/content` 下 12 种内容结构类（TextMessage / ImageMessage / VoiceMessage / VideoMessage / FileMessage / LocationMessage / CardMessage / FaceMessage / MaterialMessage / MergeMessage / QuoteMessage / RecallMessage），编号见 `ImContentTypeEnum`。

## 设计模式

| 模式 | 应用位置 | 用途 |
|---|---|---|
| 静态工厂方法 | service/message/dto 的 ImGroupMessageSendDTO、ImPrivateMessageSendDTO；service/websocket/notification 下各通知 DTO | 按 ImContentTypeEnum 快捷构造群事件 / 私聊事件 / WebSocket 通知载荷 |
| 事件驱动（Spring 事务事件 + @Async） | mq/consumer/friend/AdminUserProfileUpdateConsumer | 监听 system 模块的 AdminUserProfileUpdateMessage，事务提交后异步向「资料被改的人」的所有好友推送 FRIEND_INFO_UPDATED 通知 |
| 适配器（厂商绑定层） | framework/rtc/core/LiveKitClient（由 ImRtcConfiguration 注册为 Bean） | 自研 LiveKit Twirp HTTP 客户端：JWT Token 签发（join / admin）+ DeleteRoom / ListParticipants Server API + identity 拼接解析，隔离厂商 SDK |
| 本地缓存（Guava LoadingCache） | service/sensitiveword/ImSensitiveWordServiceImpl | 敏感词词库按租户缓存、异步刷新，消息发送前用 houbb sensitive-word Trie 匹配拦截 |
| 通知 DTO 继承族 | service/websocket/notification/{friend,group,rtc}（BaseFriendNotification / BaseGroupNotification 等） | 40+ 种 WebSocket 通知载荷按族分类封装，配合 ImNotificationWebSocketDTO 统一信封 |

## 依赖关系

- **上游**（本模块依赖）:
  - 业务模块: yudao-module-system（AdminUserApi 用户信息校验与映射；AdminUserProfileUpdateMessage 用户资料变更事件）、yudao-module-infra（WebSocketSenderApi WebSocket 推送通道）
  - framework starter: yudao-common、yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-excel
  - 三方库: com.github.houbb:sensitive-word（敏感词匹配）、com.belerweb:pinyin4j（拼音引擎）；外部服务 LiveKit（HTTP/Twirp，无 SDK 依赖）
- **下游**（依赖本模块）: 无（叶子业务模块，其他业务模块未依赖它）

## 对外暴露的 API

无。`api/` 包仅含 package-info.java，未定义跨模块 Api 接口；对本模块的使用只通过 HTTP 接口与 WebSocket 通知协议。

## 详细文档

- [api-channel.md](api-channel.md) - 频道与素材
- [api-face.md](api-face.md) - 表情包
- [api-friend.md](api-friend.md) - 好友与申请
- [api-group.md](api-group.md) - 群聊
- [api-message.md](api-message.md) - 单聊 / 群聊消息与会话
- [api-manager.md](api-manager.md) - 运营管理与数据看板
- [api-rtc.md](api-rtc.md) - 实时通话
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
