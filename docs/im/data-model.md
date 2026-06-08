# 数据模型详情

## 实体继承体系

所有 DO 实体继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| creator | VARCHAR | 创建人 |
| createTime | DATETIME | 创建时间 |
| updater | VARCHAR | 更新人 |
| updateTime | DATETIME | 更新时间 |
| deleted | BIT | 是否删除（逻辑删除） |

## 表关系总览

```
im_channel (频道)
    |
    | 1:N
    v
im_channel_material (频道素材)        im_channel_message (频道消息) --> im_channel_material (materialId)
    |
    | 1:N
    v
im_face_pack (表情包)
    |
    | 1:N
    v
im_face_pack_item (表情项)

im_face_user_item (用户表情) -- 独立表，按 userId 关联用户

im_friend (好友关系) -- 双向，每对好友 2 行记录
im_friend_request (好友请求) -- 独立表

im_group (群组)
    |
    | 1:N                 1:N                  1:N
    v                     v                    v
im_group_member        im_group_request      im_group_message
(群成员)              (入群请求)            (群聊消息)

im_private_message (私聊消息) -- 独立表，通过 senderId/receiverId 关联用户

im_rtc_call (RTC 通话)
    |
    | 1:N
    v
im_rtc_participant (RTC 参与者)

im_sensitive_word (敏感词) -- 独立表
```

## 频道聚合

### im_channel（频道表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 频道编号 |
| code | VARCHAR | UNIQUE | 频道编码 |
| name | VARCHAR | | 频道名称 |
| avatar | VARCHAR | | 频道头像 URL |
| sort | INT | | 排序值 |
| status | TINYINT | | 频道状态（启用/禁用） |

**索引**: uk_code(code)

### im_channel_material（频道素材表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 素材编号 |
| title | VARCHAR | | 素材标题 |
| cover_url | VARCHAR | | 封面图片 URL |
| summary | VARCHAR | | 内容摘要 |
| content | TEXT | | 内容 HTML |
| url | VARCHAR | | 原文链接 |

### im_channel_message（频道消息表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 消息编号 |
| channel_id | BIGINT | FK -> im_channel.id | 频道编号 |
| material_id | BIGINT | FK -> im_channel_material.id | 关联素材编号 |
| receiver_user_ids | VARCHAR | | 接收用户 ID 列表（JSON 数组） |
| send_time | DATETIME | | 发送时间 |

**索引**: idx_channel_id(channel_id)

## 表情聚合

### im_face_pack（表情包表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 表情包编号 |
| name | VARCHAR | | 表情包名称 |
| icon | VARCHAR | | 表情包图标 URL |
| sort | INT | | 排序值 |
| status | TINYINT | | 启用状态 |

### im_face_pack_item（表情项表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 表情项编号 |
| pack_id | BIGINT | FK -> im_face_pack.id | 所属表情包编号 |
| url | VARCHAR | | 表情图片 URL |
| name | VARCHAR | | 表情名称 |
| width | INT | | 图片宽度 |
| height | INT | | 图片高度 |

**索引**: idx_pack_id(pack_id)

### im_face_user_item（用户表情表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 表情编号 |
| user_id | BIGINT | | 用户编号 |
| url | VARCHAR | | 表情图片 URL |
| name | VARCHAR | | 表情名称 |
| width | INT | | 图片宽度 |
| height | INT | | 图片高度 |

**索引**: idx_user_id(user_id)

## 好友聚合

### im_friend（好友关系表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 关系编号 |
| user_id | BIGINT | | 用户编号 |
| friend_id | BIGINT | | 好友用户编号 |
| silent | BIT | | 是否免打扰 |
| pinned | BIT | | 是否置顶 |
| blocked | BIT | | 是否拉黑 |
| display_name | VARCHAR | | 好友备注名 |

**索引**: uk_user_friend(user_id, friend_id) - 联合唯一索引

> 每对好友关系存储 2 行记录：A->B 和 B->A，各自拥有独立的 silent/pinned/blocked/display_name 属性。

### im_friend_request（好友请求表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 请求编号 |
| user_id | BIGINT | | 申请人用户编号 |
| friend_id | BIGINT | | 目标用户编号 |
| apply_content | VARCHAR | | 申请附言 |
| display_name | VARCHAR | | 对好友的备注名 |
| add_source | TINYINT | | 添加来源（搜索/扫码/群聊等） |
| handle_result | TINYINT | | 处理结果（未处理/同意/拒绝） |
| handle_time | DATETIME | | 处理时间 |
| handle_user_id | BIGINT | | 处理人用户编号 |

**索引**: idx_user_id(user_id), idx_friend_id(friend_id)

## 群组聚合

### im_group（群组表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 群组编号 |
| name | VARCHAR | | 群组名称 |
| owner_id | BIGINT | | 群主用户编号 |
| avatar | VARCHAR | | 群组头像 URL |
| notice | VARCHAR | | 群公告 |
| join_approval | BIT | | 是否开启入群审批 |
| banned | BIT | | 是否被封禁 |
| muted_all | BIT | | 是否全员禁言 |
| pinned_message_ids | VARCHAR | | 置顶消息 ID 列表（JSON 数组） |

**索引**: idx_owner_id(owner_id)

### im_group_member（群成员表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 成员编号 |
| group_id | BIGINT | FK -> im_group.id | 群组编号 |
| user_id | BIGINT | | 用户编号 |
| role | TINYINT | | 角色（OWNER/ADMIN/NORMAL） |
| nickname | VARCHAR | | 群内昵称 |
| mute_end_time | DATETIME | | 禁言结束时间 |
| add_source | TINYINT | | 加入来源 |
| inviter | BIGINT | | 邀请人用户编号 |

**索引**: uk_group_user(group_id, user_id) - 联合唯一索引

### im_group_request（群组请求表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 请求编号 |
| group_id | BIGINT | FK -> im_group.id | 群组编号 |
| user_id | BIGINT | | 申请人/被邀请人用户编号 |
| type | TINYINT | | 请求类型（用户申请/成员邀请） |
| apply_content | VARCHAR | | 申请附言 |
| handle_result | TINYINT | | 处理结果（未处理/同意/拒绝） |
| handle_time | DATETIME | | 处理时间 |
| handle_user_id | BIGINT | | 处理人用户编号 |

**索引**: idx_group_id(group_id), idx_user_id(user_id)

## 消息聚合

### im_private_message（私聊消息表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 消息编号 |
| client_message_id | VARCHAR | UNIQUE | 客户端消息 ID（幂等键） |
| sender_id | BIGINT | | 发送者用户编号 |
| receiver_id | BIGINT | | 接收者用户编号 |
| type | TINYINT | | 消息类型（文本/图片/语音/视频/文件等） |
| content | VARCHAR | | 消息内容（JSON 格式） |
| status | TINYINT | | 消息状态（正常/已撤回） |

**索引**: uk_client_message_id(client_message_id), idx_sender_id(sender_id), idx_receiver_id(receiver_id)

### im_group_message（群聊消息表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 消息编号 |
| client_message_id | VARCHAR | UNIQUE | 客户端消息 ID（幂等键） |
| sender_id | BIGINT | | 发送者用户编号 |
| group_id | BIGINT | FK -> im_group.id | 群组编号 |
| type | TINYINT | | 消息类型 |
| content | VARCHAR | | 消息内容（JSON 格式） |
| at_user_ids | VARCHAR | | @的用户 ID 列表（JSON 数组） |
| status | TINYINT | | 消息状态（正常/已撤回） |
| receipt_status | TINYINT | | 已读回执状态 |
| read_count | INT | | 已读人数 |

**索引**: uk_client_message_id(client_message_id), idx_group_id(group_id), idx_sender_id(sender_id)

## RTC 通话聚合

### im_rtc_call（RTC 通话表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 通话编号 |
| room_id | VARCHAR | UNIQUE | LiveKit 房间 UUID |
| conversation_type | TINYINT | | 会话类型（私聊/群聊） |
| media_type | TINYINT | | 媒体类型（音频/视频） |
| inviter_uid | BIGINT | | 发起者用户编号 |
| status | TINYINT | | 通话状态（进行中/已结束/已取消/未接听） |
| start_time | DATETIME | | 开始时间 |
| accept_time | DATETIME | | 接听时间 |
| end_time | DATETIME | | 结束时间 |

**索引**: uk_room_id(room_id), idx_inviter_uid(inviter_uid)

### im_rtc_participant（RTC 参与者表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 参与者编号 |
| call_id | BIGINT | FK -> im_rtc_call.id | 通话编号 |
| user_id | BIGINT | | 用户编号 |
| role | TINYINT | | 角色（发起者/参与者） |
| status | TINYINT | | 状态（INVITING/JOINED/LEFT/REJECTED/NO_ANSWER） |
| join_time | DATETIME | | 加入时间 |
| leave_time | DATETIME | | 离开时间 |

**索引**: idx_call_id(call_id), idx_user_id(user_id)

## 独立实体

### im_sensitive_word（敏感词表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 敏感词编号 |
| word | VARCHAR | UNIQUE | 敏感词内容 |
| status | TINYINT | | 启用状态 |

**索引**: uk_word(word)

## ER 关系定义

| 关系 | 类型 | 外键 | 说明 |
|-----|------|------|------|
| im_channel_material -> im_channel | N:1 | channel_id | 素材属于频道 |
| im_channel_message -> im_channel | N:1 | channel_id | 消息属于频道 |
| im_channel_message -> im_channel_material | N:1 | material_id | 消息关联素材 |
| im_face_pack_item -> im_face_pack | N:1 | pack_id | 表情项属于表情包 |
| im_group_member -> im_group | N:1 | group_id | 成员属于群组 |
| im_group_request -> im_group | N:1 | group_id | 请求属于群组 |
| im_group_message -> im_group | N:1 | group_id | 消息属于群组 |
| im_rtc_participant -> im_rtc_call | N:1 | call_id | 参与者属于通话 |

## Mapper 规范

所有 Mapper 继承 `BaseMapperX<T>`，获得通用 CRUD 方法：

```java
public interface ImPrivateMessageMapper extends BaseMapperX<PrivateMessageDO> {
    default PageResult<PrivateMessageDO> selectPage(PrivateMessagePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<PrivateMessageDO>()
                .eqIfPresent(PrivateMessageDO::getSenderId, reqVO.getSenderId())
                .eqIfPresent(PrivateMessageDO::getReceiverId, reqVO.getReceiverId())
                .betweenIfPresent(PrivateMessageDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(PrivateMessageDO::getId));
    }
}
```
