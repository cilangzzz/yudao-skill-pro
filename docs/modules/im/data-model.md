# 数据模型详情

> im 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。共 17 张数据表（17 个 `@TableName` DO），消息正文以 JSON 多态存于 `content` 字段，对应 `dal/dataobject/message/content` 下 12 个内容结构类（非数据表）。

## 1. 实体继承体系

im 模块全部 17 个 DO 直接继承 `BaseDO`，无一使用 `TenantBaseDO`：

```
BaseDO（cn.iocoder.yudao.framework.mybatis.core.dataobject，抽象基类）
├── creator      String          创建者（SysUser 的 id，String 预留扩展；INSERT 自动填充）
├── createTime   LocalDateTime   创建时间（INSERT 自动填充）
├── updater      String          更新者（UPDATE 自动填充）
├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 自动填充）
└── deleted      Boolean         逻辑删除标记（@TableLogic，查询自动过滤已删行）
    │
    ├── TenantBaseDO（cn.iocoder.yudao.framework.tenant.core.db，抽象基类）
    │   └── tenantId   Long        多租户编号（DO 层显式映射租户字段）
    │
    └── im 模块 17 个 DO（dal/dataobject 下按业务域分包）
        ├── channel/       ImChannelDO、ImChannelMaterialDO
        ├── conversation/  ImConversationReadDO
        ├── face/          ImFacePackDO、ImFacePackItemDO、ImFaceUserItemDO
        ├── friend/        ImFriendDO、ImFriendRequestDO
        ├── group/         ImGroupDO、ImGroupMemberDO、ImGroupRequestDO
        ├── message/       ImPrivateMessageDO、ImGroupMessageDO、ImChannelMessageDO
        ├── rtc/           ImRtcCallDO、ImRtcParticipantDO
        └── sensitiveword/ ImSensitiveWordDO
```

**使用规则**：

| 基类 | 适用场景 | im 模块现状 |
|---|---|---|
| BaseDO | 通用业务表，无 DO 层租户字段映射需求 | **全部 17 个 DO 使用**。多租户隔离由 MyBatis Plus 租户插件在 SQL 层自动完成（`yudao-server` 配置 `tenant.enable=true`、`ignore-tables` 为空，租户插件对所有 im 表自动拼接 `tenant_id` 过滤条件与插入值；模块单测建表脚本中每张表都有 `tenant_id bigint NOT NULL DEFAULT 0` 物理列） |
| TenantBaseDO | 需要在 DO/VO 层显式读写 tenantId 字段的表 | 未使用 |

其余约定：所有表的 DO 均标注 `@KeySequence("im_xxx_seq")`（仅 Oracle / PostgreSQL / 达梦等序列数据库使用，MySQL 忽略）；主键统一为 `id bigint`（`@TableId`）；全库无物理外键，跨表关联均为逻辑关联。索引信息来自模块单测建表脚本 `yudao-module-im/src/test/resources/sql/create_tables.sql`（主 SQL dump `sql/mysql/ruoyi-vue-pro.sql` 尚未合入 im 建表语句，仅含 im 相关字典数据）。

## 2. 核心 DO 实体

### 2.1 好友聚合

#### ImFriendDO (im_friend)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 用户编号，关联 system 模块 AdminUserDO 的 id |
| friendUserId | Long | friend_user_id | 好友用户编号，关联 AdminUserDO 的 id |
| silent | Boolean | silent | 是否免打扰（屏蔽来自该好友的通知） |
| displayName | String | display_name | 好友展示备注（仅自己可见） |
| addSource | Integer | add_source | 添加来源，枚举 `ImFriendAddSourceEnum`（1 搜索 / 2 群聊 / 3 扫码 / 4 名片） |
| pinned | Boolean | pinned | 是否置顶联系人（单边，影响联系人 / 会话排序） |
| blocked | Boolean | blocked | 是否拉黑（单边屏蔽对方私聊消息；必须先是好友） |
| status | Integer | status | 好友状态，枚举 `CommonStatusEnum`（ENABLE 正常 / DISABLE 已删除），字典 `im_friend_status` |
| addTime | LocalDateTime | add_time | 添加好友时间 |
| deleteTime | LocalDateTime | delete_time | 删除好友时间（不为 null 表示已删除） |

**继承**: BaseDO
**索引**: 唯一索引 `uk_user_friend (user_id, friend_user_id, tenant_id)` —— 好友关系单向一行，A-B 互为好友存 2 条记录（userId=A,friendUserId=B 与 userId=B,friendUserId=A），该约束防止重复添加

#### ImFriendRequestDO (im_friend_request)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| fromUserId | Long | from_user_id | 发起方用户编号，关联 AdminUserDO 的 id |
| toUserId | Long | to_user_id | 接收方用户编号，关联 AdminUserDO 的 id |
| applyContent | String | apply_content | 申请理由（发起方填写） |
| displayName | String | display_name | 发起方对接收方的备注（同意后写入发起方侧 ImFriendDO.displayName） |
| addSource | Integer | add_source | 添加来源，枚举 `ImFriendAddSourceEnum`（同意后双向写入 ImFriendDO.addSource） |
| handleResult | Integer | handle_result | 处理结果，枚举 `ImFriendRequestHandleResultEnum`（0 未处理 / 1 同意 / 2 拒绝） |
| handleContent | String | handle_content | 处理理由（接收方拒绝时可选填） |
| handleTime | LocalDateTime | handle_time | 处理时间 |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_friend_request (from_user_id, to_user_id, tenant_id)` —— 同一对用户的申请只保留一条记录，配合「申请 - 审批」状态机（apply 落库 UNHANDLED → agree/refuse 更新处理字段）

### 2.2 群聊聚合

#### ImGroupDO (im_group)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| name | String | name | 群名称 |
| ownerUserId | Long | owner_user_id | 群主用户编号，关联 AdminUserDO 的 id（转让群主时切换） |
| avatar | String | avatar | 群头像 |
| notice | String | notice | 群公告 |
| joinApproval | Boolean | join_approval | 进群是否需群主 / 管理员审批（false 自由进群；true 时「申请」「邀请」均需审批） |
| banned | Boolean | banned | 是否封禁（运营侧管理动作） |
| bannedReason | String | banned_reason | 封禁原因 |
| bannedTime | LocalDateTime | banned_time | 封禁时间 |
| status | Integer | status | 群状态，枚举 `CommonStatusEnum`（ENABLE 正常 / DISABLE 已解散），字典 `im_group_status` |
| dissolvedTime | LocalDateTime | dissolved_time | 解散时间 |
| mutedAll | Boolean | muted_all | 是否全群禁言 |
| pinnedMessageIds | List\<Long\> | pinned_message_ids | 群置顶消息编号列表，`LongListTypeHandler` 以逗号分隔存储；操作人 / 置顶时间从对应 PIN 事件的消息记录反查 |

**继承**: BaseDO
**索引**: 仅主键。`@TableName(value = "im_group", autoResultMap = true)`（pinnedMessageIds 的 TypeHandler 需要）

#### ImGroupMemberDO (im_group_member)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| groupId | Long | group_id | 群编号，关联 ImGroupDO.id |
| userId | Long | user_id | 用户编号，关联 AdminUserDO 的 id |
| displayUserName | String | display_user_name | 组内显示名（成员自己改，广播 1516 事件） |
| groupRemark | String | group_remark | 群备注（个人对群的备注） |
| silent | Boolean | silent | 是否免打扰 |
| status | Integer | status | 成员状态，枚举 `CommonStatusEnum` |
| role | Integer | role | 成员角色，枚举 `ImGroupMemberRoleEnum`（1 群主 / 2 管理员 / 3 普通成员），字典 `im_group_member_role` |
| joinTime | LocalDateTime | join_time | 入群时间 |
| addSource | Integer | add_source | 加入来源，枚举 `ImGroupAddSourceEnum`（1 搜索 / 2 邀请 / 3 扫码 / 4 分享链接），字典 `im_group_add_source`；审批通过时从 ImGroupRequestDO 同步 |
| inviterUserId | Long | inviter_user_id | 邀请人用户编号（用户主动申请进群时为 NULL） |
| quitTime | LocalDateTime | quit_time | 退群时间 |
| muteEndTime | LocalDateTime | mute_end_time | 禁言到期时间（null 未禁言；非 null 且在未来表示禁言中；永久禁言写入类常量 `PERMANENT_MUTE_END_TIME` = 9999-12-31 23:59:59） |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_group_member (group_id, user_id, tenant_id)` —— 同群同用户仅一行，退群走逻辑删除 / quitTime，再次进群复用或新建记录

#### ImGroupRequestDO (im_group_request)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| groupId | Long | group_id | 群编号，关联 ImGroupDO.id |
| userId | Long | user_id | 申请人 / 被邀请人用户编号，关联 AdminUserDO 的 id |
| inviterUserId | Long | inviter_user_id | 邀请人用户编号（NULL 表示用户主动申请；非 NULL 表示成员邀请待群主 / 管理员审批） |
| applyContent | String | apply_content | 申请理由 |
| addSource | Integer | add_source | 加入来源，枚举 `ImGroupAddSourceEnum`（同意时同步写入 ImGroupMemberDO.addSource） |
| handleResult | Integer | handle_result | 处理结果，枚举 `ImGroupRequestHandleResultEnum`（0 未处理 / 1 同意 / 2 拒绝），与好友申请枚举平行 |
| handleUserId | Long | handle_user_id | 处理人用户编号（群主或管理员） |
| handleContent | String | handle_content | 处理理由（拒绝时可选填） |
| handleTime | LocalDateTime | handle_time | 处理时间 |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_group_request (group_id, user_id, tenant_id)` —— 同群同申请人一行，支撑「申请 - 审批」状态机

### 2.3 消息聚合

#### ImPrivateMessageDO (im_private_message)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键），客户端游标拉取 /pull 的递增位点 |
| clientMessageId | String | client_message_id | 客户端消息编号，用于发送幂等 |
| senderId | Long | sender_id | 发送人编号，关联 AdminUserDO 的 id |
| receiverId | Long | receiver_id | 接收人编号，关联 AdminUserDO 的 id |
| type | Integer | type | 消息类型，枚举 `ImContentTypeEnum`（见 2.3.4） |
| content | String | content | 消息内容，JSON 格式，对应 content 包下的 TextMessage / ImageMessage 等结构（见 2.3.5） |
| status | Integer | status | 消息状态，枚举 `ImMessageStatusEnum`（-1 发送中仅客户端 / 0 正常 / 2 已撤回） |
| receiptStatus | Integer | receipt_status | 回执状态，枚举 `ImMessageReceiptStatusEnum`（0 不需要 / 1 待完成 / 2 已完成） |
| sendTime | LocalDateTime | send_time | 发送时间 |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_private_message_sender_client (sender_id, client_message_id, tenant_id)` —— 同一发送人的 clientMessageId 幂等去重，防止重试造成消息重复

#### ImGroupMessageDO (im_group_message)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键），游标拉取位点 |
| clientMessageId | String | client_message_id | 客户端消息编号，用于发送幂等 |
| senderId | Long | sender_id | 发送人编号，关联 AdminUserDO 的 id |
| groupId | Long | group_id | 群编号，关联 ImGroupDO.id |
| type | Integer | type | 消息类型，枚举 `ImContentTypeEnum` |
| content | String | content | 消息内容，JSON 格式（见 2.3.5） |
| status | Integer | status | 消息状态，枚举 `ImMessageStatusEnum` |
| receiverUserIds | List\<Long\> | receiver_user_ids | 定向接收用户编号列表，`LongListTypeHandler` 逗号分隔（为空表示全员可见）；关联 AdminUserDO 的 id |
| atUserIds | List\<Long\> | at_user_ids | @ 目标用户编号列表，`LongListTypeHandler` 逗号分隔（@ 全体时含 -1 特殊值） |
| receiptStatus | Integer | receipt_status | 回执状态，枚举 `ImMessageReceiptStatusEnum` |
| readCount | Integer | （非表字段） | `@TableField(exist = false)`：离线拉取等场景下回算的已读人数，不落库 |
| sendTime | LocalDateTime | send_time | 发送时间 |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_group_message_sender_client (sender_id, client_message_id, tenant_id)` —— 发送幂等。`@TableName(value = "im_group_message", autoResultMap = true)`（receiverUserIds / atUserIds 的 TypeHandler 需要）

#### ImChannelMessageDO (im_channel_message)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| channelId | Long | channel_id | 频道编号，关联 ImChannelDO.id；冗余自 ImChannelMaterialDO.channelId，便于按频道检索 |
| materialId | Long | material_id | 关联素材编号，关联 ImChannelMaterialDO.id |
| type | Integer | type | 消息类型，枚举 `ImContentTypeEnum`（频道推送固定 MATERIAL(125)） |
| content | String | content | 推送时 payload 的 JSON 快照（title / coverUrl / summary / url），不含富文本正文（正文按需走 /get-content 接口，避免压爆 WebSocket 通道） |
| receiverUserIds | List\<Long\> | receiver_user_ids | 接收人编号列表，`LongListTypeHandler` 逗号分隔（为空表示全员） |
| sendTime | LocalDateTime | send_time | 发送时间（一次推送 1 行） |

**继承**: BaseDO
**索引**: 仅主键。`@TableName(value = "im_channel_message", autoResultMap = true)`（receiverUserIds 的 TypeHandler 需要）

#### 2.3.4 消息类型枚举 ImContentTypeEnum

消息表 `type` 字段与 WebSocket 通知 `contentType` 共用该枚举，编号复用 OpenIM 段位；`persistent` 决定是否落消息表（离线可拉），`normal` 决定是否计入未读数：

| 段位 | 编号 | 枚举 | 入库 | 说明 |
|---|---|---|---|---|
| 聊天消息 | 101-105 | TEXT / IMAGE / VOICE / VIDEO / FILE | 是 | 直接复用 OpenIM 段位 |
| 聊天消息 | 107 / 108 / 115 | MERGE / CARD / FACE | 是 | 合并转发 / 名片 / 表情贴图 |
| 频道扩展 | 125 | MATERIAL | 是 | 频道素材图文卡片（OpenIM 125 起未占用） |
| 好友通知 | 1201-1210 | FRIEND_REQUEST_APPROVED 等 | 仅 1204 FRIEND_ADD 入库 | 其余仅 WebSocket 推送 |
| 群事件 | 1501-1533 | GROUP_CREATE、GROUP_MUTED 等 | 大多入库 | 群生命周期 / 成员 / 禁言 / 置顶事件 |
| RTC 信令 | 1601-1603 | RTC_CALL / PARTICIPANT_CONNECTED / DISCONNECTED | 否 | 不入库，仅推参与方 |
| RTC 历史 | 1610 / 1611 | RTC_CALL_START / RTC_CALL_END | 是 | 两段式配对，入私聊 / 群聊消息表渲染通话 tip |
| 信号类 | 2101 | RECALL | 是 | 撤回提示 |
| 信号类 | 2200 / 2201 | RECEIPT / READ | 否 | 回执 / 已读，已读走 Redis 游标 + im_conversation_read |

#### 2.3.5 消息内容 JSON 结构（content 包，非数据表）

12 个内容结构类以 JSON 存于三张消息表的 `content` 字段，无 `DO` 后缀、不对应任何表：

| 结构类 | 对应类型 | 关键字段 |
|---|---|---|
| TextMessage | TEXT(101) | content 文本；可选 quote 引用 |
| ImageMessage | IMAGE(102) | url / thumbnailUrl / width / height / size；可选 quote |
| AudioMessage | VOICE(103) | url / duration（秒）/ size；可选 quote |
| VideoMessage | VIDEO(104) | url / coverUrl / duration / width / height / size；可选 quote |
| FileMessage | FILE(105) | url / name / size / type（扩展名）；可选 quote |
| MergeMessage | MERGE(107) | title + messages 内嵌完整消息快照（含发送人昵称 / 头像快照，原消息撤回不影响已转发内容） |
| CardMessage | CARD(108) | targetType（PRIVATE 用户名片 / GROUP 群名片）/ targetId / name / avatar / memberCount；可选 quote |
| FaceMessage | FACE(115) | url / width / height / name（Unicode emoji 仍走 TEXT）；可选 quote |
| MaterialMessage | MATERIAL(125) | materialId / channelId / type / title / coverUrl / summary / url，频道图文卡片 |
| QuoteMessage | （嵌套结构） | messageId / senderId / type / content；服务端反查原消息重算覆盖客户端写入，防伪造；复制时 removeQuote 防嵌套 |
| RecallMessage | RECALL(2101) | messageId（被撤回的原消息编号） |
| LocationMessage | （预留） | description / longitude / latitude；`ImContentTypeEnum` 暂未注册对应段位，预留结构 |

### 2.4 会话已读

#### ImConversationReadDO (im_conversation_read)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 用户编号，关联 AdminUserDO 的 id |
| conversationType | Integer | conversation_type | 会话类型，枚举 `ImConversationTypeEnum`（1 私聊 / 2 群聊 / 3 频道） |
| targetId | Long | target_id | 目标编号：私聊 → AdminUserDO.id；群聊 → ImGroupDO.id；频道 → ImChannelDO.id |
| messageId | Long | message_id | 最大已读消息编号，按会话类型关联 ImPrivateMessageDO / ImGroupMessageDO / ImChannelMessageDO 的 id |
| readTime | LocalDateTime | read_time | 最近已读时间 |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_conversation_read_user_target (user_id, conversation_type, target_id, tenant_id)` —— 「用户 + 会话」一行，是三类会话读位置的唯一权威，支持增量拉取（重连 / 离线补偿）

### 2.5 频道聚合

#### ImChannelDO (im_channel)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键），前端会话 targetId 使用 |
| code | String | code | 频道业务码（API / 字典外露；DO 注释与建表注释标注唯一，测试 DDL 未建唯一约束） |
| name | String | name | 频道名称 |
| avatar | String | avatar | 频道头像 |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum`（0 启用 / 1 停用） |

**继承**: BaseDO
**索引**: 仅主键。频道是运营单向推送主体，C 端用户不能向频道发消息

#### ImChannelMaterialDO (im_channel_material)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| channelId | Long | channel_id | 频道编号，关联 ImChannelDO.id |
| type | Integer | type | 内容类型，枚举 `ImChannelMaterialTypeEnum`（1 站内富文本 / 2 外链） |
| title | String | title | 标题 |
| coverUrl | String | cover_url | 封面图 |
| summary | String | summary | 摘要 |
| content | String | content | 富文本 HTML，仅 `type=CONTENT` 使用；仅在素材详情接口按需返回 |
| url | String | url | 跳转链接，仅 `type=LINK` 使用（为空时点击在客户端内置详情页拉 content） |

**继承**: BaseDO
**索引**: 仅主键。一条素材 1:N 关联多次频道推送（ImChannelMessageDO.materialId）

### 2.6 表情包聚合

#### ImFacePackDO (im_face_pack)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| name | String | name | 表情包名称 |
| icon | String | icon | 表情包图标（面板底部 tab 栏显示） |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 仅主键。运营配置的系统表情包元数据

#### ImFacePackItemDO (im_face_pack_item)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| packId | Long | pack_id | 所属表情包编号，关联 ImFacePackDO.id |
| url | String | url | 表情图 URL |
| name | String | name | 表情名（可选，如「狗头」「捂脸」） |
| width | Integer | width | 渲染宽度（像素） |
| height | Integer | height | 渲染高度（像素） |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: BaseDO
**索引**: 仅主键。系统表情包内的单张表情图

#### ImFaceUserItemDO (im_face_user_item)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 所属用户编号，关联 AdminUserDO 的 id |
| url | String | url | 表情图 URL |
| name | String | name | 表情名（可选，用户私有表情通常不带名字，留作「重命名」交互） |
| width | Integer | width | 渲染宽度（像素） |
| height | Integer | height | 渲染高度（像素） |
| sort | Integer | sort | 排序 |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_face_user_item_user_url_deleted (user_id, url, deleted)` —— 同一用户不重复收藏同一张图（注意该表唯一键含 `deleted` 而非 `tenant_id`，删除后可重新添加）

### 2.7 实时通话（RTC）聚合

#### ImRtcCallDO (im_rtc_call)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| room | String | room | 业务通话编号（UUID，同时作为 LiveKit 房间名；DO 注释标注唯一，测试 DDL 未建唯一约束） |
| conversationType | Integer | conversation_type | 会话类型，枚举 `ImConversationTypeEnum`（私聊 / 群聊） |
| mediaType | Integer | media_type | 媒体类型，枚举 `ImRtcCallMediaTypeEnum`（1 语音 / 2 视频） |
| inviterUserId | Long | inviter_user_id | 发起人用户编号，关联 AdminUserDO 的 id |
| groupId | Long | group_id | 群编号，关联 ImGroupDO.id（私聊为 NULL） |
| status | Integer | status | 通话状态，枚举 `ImRtcCallStatusEnum`（10 创建 / 20 进行中 / 30 已结束），状态机 CREATED → RUNNING → ENDED，CREATED 直达 ENDED 表示无人接听 / 主叫取消 |
| endReason | Integer | end_reason | 结束原因，枚举 `ImRtcCallEndReasonEnum`（1 挂断 / 2 已拒绝 / 3 已取消 / 4 无人接听 / 5 对方正忙 / 9 异常）；未结束时为 NULL |
| startTime | LocalDateTime | start_time | 发起时间 |
| acceptTime | LocalDateTime | accept_time | 接通时间（首个非发起人加入时写入；未接通保持 NULL） |
| endTime | LocalDateTime | end_time | 通话结束时间 |

**继承**: BaseDO
**索引**: 仅主键。一通通话一行（房间级 / 主表），与明细表通过 room + callId 关联；僵尸通话清理 Job 按该表扫描 ACTIVE 状态兜底

#### ImRtcParticipantDO (im_rtc_participant)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| callId | Long | call_id | 通话编号，关联 ImRtcCallDO.id |
| room | String | room | 业务通话编号，关联 ImRtcCallDO.room（冗余，便于按房间操作） |
| userId | Long | user_id | 参与者用户编号，关联 AdminUserDO 的 id |
| role | Integer | role | 参与角色，枚举 `ImRtcParticipantRoleEnum`（1 发起人 / 2 被邀请者 / 3 主动加入者——群聊旁观者点胶囊条加入） |
| status | Integer | status | 参与状态，枚举 `ImRtcParticipantStatusEnum`（10 邀请中 / 20 已加入 / 30 已拒绝 / 40 未应答 / 50 已离开）；终态闭合：通话 ENDED 时必属 {LEFT / REJECTED / NO_ANSWER} |
| inviteTime | LocalDateTime | invite_time | 被邀请时间（发起人取通话 startTime） |
| acceptTime | LocalDateTime | accept_time | 接听时间（未接听 NULL） |
| leaveTime | LocalDateTime | leave_time | 离开时间（未加入 NULL） |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_rtc_participant_room_user (room, user_id, tenant_id)` —— 同一通话每个参与者一行（用户级 / 明细表）

### 2.8 敏感词

#### ImSensitiveWordDO (im_sensitive_word)

| 字段 | 类型 | 数据库列 | 说明 |
|---|---|---|---|
| id | Long | id | 编号（主键） |
| word | String | word | 敏感词 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum`（0 启用 / 1 停用） |

**继承**: BaseDO
**索引**: 唯一索引 `uk_im_sensitive_word (word, tenant_id)` —— 词库按租户隔离（Service 层用 Guava LoadingCache 按租户缓存，消息发送前 Trie 匹配拦截）

## 3. 实体关系

全库无物理外键，跨表与跨模块引用均为逻辑关联；用户维度统一引用 system 模块的 `AdminUserDO`（system_users 表）。

```
system_users（AdminUserDO，system 模块）
    ▲ 逻辑引用：userId / friendUserId / senderId / receiverId / ownerUserId /
      inviterUserId / atUserIds / receiverUserIds ...
    │
    ├─ ImFriendRequestDO (fromUserId → toUserId)
    │        │ 审批同意后落 2 条记录（双向）
    │        ▼
    ├─ ImFriendDO (userId + friendUserId；单边属性 silent / pinned / blocked)
    │
    ├─ ImGroupDO (ownerUserId)
    │        │ 1
    │        ├──< N ImGroupMemberDO (groupId + userId，uk 群内唯一；role / muteEndTime)
    │        ├──< N ImGroupRequestDO (groupId + userId；inviterUserId NULL=主动申请)
    │        └──< N ImGroupMessageDO (groupId；receiverUserIds / atUserIds 定向)
    │                 ▲ pinnedMessageIds（im_group JSON 数组）反向指向置顶消息 id
    │
    ├─ ImPrivateMessageDO (senderId → receiverId)
    │
    ├─ ImChannelDO 1 ──< N ImChannelMaterialDO (channelId)
    │        └───────< N ImChannelMessageDO (channelId 冗余 + materialId → 素材)
    │
    ├─ ImConversationReadDO (userId + conversationType + targetId 多态定位：
    │        PRIVATE → system_users.id；GROUP → im_group.id；CHANNEL → im_channel.id；
    │        messageId → 对应会话类型消息表的 id)
    │
    └─ ImRtcCallDO (inviterUserId；groupId 私聊为 NULL)
             │ 1
             └──< N ImRtcParticipantDO (callId + room 双关联；userId)

ImFacePackDO 1 ──< N ImFacePackItemDO (packId)          系统表情包 → 表情项
ImFaceUserItemDO (userId)                                用户个人表情，独立于系统表情包
ImSensitiveWordDO（独立配置表，发送前 Trie 匹配，无外键关联）
```

关系要点：

- **好友关系双向两行**：A-B 互为好友存 2 条 ImFriendDO（userId 互换），silent / pinned / blocked 均为单边属性；申请表唯一键保证同一对用户仅一条申请，同意后 displayName / addSource 同步写入 ImFriendDO。
- **群三表状态机衔接**：ImGroupRequestDO 审批同意时，把 addSource / inviterUserId 同步写入 ImGroupMemberDO；群主转让只改 ImGroupDO.ownerUserId 与成员 role；置顶消息 id 以 JSON 数组存 im_group.pinned_message_ids。
- **三类消息表结构同源**：均为 clientMessageId 幂等 + type（ImContentTypeEnum）+ content(JSON)，私聊按 receiverId 定向、群聊可按 receiverUserIds 定向、频道按 receiverUserIds 定向（为空全员）。
- **RTC 主明细双关联**：ImRtcParticipantDO 同时持有 callId（数字主键）与 room（UUID / LiveKit 房间名），Webhook 兜底清理时按 room 直接定位。
- **读位置多态**：im_conversation_read 用 (conversationType, targetId) 多态引用三类会话，messageId 指向对应消息表，替代每会话一张读位置的方案。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|---|---|---|
| im_friend | ImFriendDO | 好友关系（双向两行、单边免打扰 / 置顶 / 拉黑） |
| im_friend_request | ImFriendRequestDO | 好友申请记录（申请 - 审批状态机） |
| im_group | ImGroupDO | 群信息（群主、审批开关、封禁、全群禁言、置顶消息列表） |
| im_group_member | ImGroupMemberDO | 群成员（角色、入群来源、禁言到期时间） |
| im_group_request | ImGroupRequestDO | 加群申请记录（主动申请 / 邀请待审批） |
| im_private_message | ImPrivateMessageDO | 私聊消息（content JSON 多态、发送幂等、回执状态） |
| im_group_message | ImGroupMessageDO | 群聊消息（content JSON 多态、定向接收、@ 列表、回执） |
| im_channel_message | ImChannelMessageDO | 频道消息（一次推送一行、payload JSON 快照） |
| im_conversation_read | ImConversationReadDO | 会话读位置（三类会话统一的已读位点） |
| im_channel | ImChannelDO | 频道（运营单向推送主体） |
| im_channel_material | ImChannelMaterialDO | 频道素材（图文卡片 / 外链，可反复推送） |
| im_face_pack | ImFacePackDO | 表情包（运营配置的系统表情包元数据） |
| im_face_pack_item | ImFacePackItemDO | 表情包项（系统表情包内单张表情图） |
| im_face_user_item | ImFaceUserItemDO | 用户个人表情（对照微信「我的表情」） |
| im_rtc_call | ImRtcCallDO | 通话记录主表（房间级，LiveKit 房间名 room） |
| im_rtc_participant | ImRtcParticipantDO | 通话参与者明细表（用户级，角色与状态机） |
| im_sensitive_word | ImSensitiveWordDO | 敏感词（按租户缓存，发送前拦截） |

> 消息正文 `content` 字段存 JSON，对应 `dal/dataobject/message/content` 下 12 个内容结构类（TextMessage / ImageMessage / AudioMessage / VideoMessage / FileMessage / LocationMessage / CardMessage / FaceMessage / MaterialMessage / MergeMessage / QuoteMessage / RecallMessage），类型编号见 `ImContentTypeEnum`；它们不是数据表，不计入上表。
