# RTC 通话接口

## 概述

RTC（实时通信）是 IM 模块的音视频通话功能，集成 LiveKit 开源框架，支持一对一和多人音视频通话。

### 业务定位

- 基于 LiveKit 实现 WebRTC 音视频通话
- 支持音频通话和视频通话两种媒体类型
- 支持一对一通话和群组通话两种会话类型
- 提供完整的通话生命周期管理：创建、邀请、加入、接听、拒绝、取消、离开

### 核心实体

| 实体 | 说明 |
|-----|------|
| RtcCallDO | 通话会话，包含房间 UUID、会话类型、媒体类型、发起者、状态、时间戳 |
| RtcParticipantDO | 通话参与者，包含角色、状态（INVITING/JOINED/LEFT/REJECTED/NO_ANSWER） |

## RTC 通话接口

### 1. 创建通话

- **路径**: `POST /im/rtc/create`
- **说明**: 创建 RTC 通话会话
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| conversationType | Integer | 是 | 会话类型（私聊/群聊） |
| mediaType | Integer | 是 | 媒体类型（音频/视频） |
| inviteeIds | List<Long> | 是 | 被邀请用户 ID 列表 |

- **响应**: `CommonResult<RtcCallDO>` - 通话会话信息
- **实现逻辑**:
  1. 生成唯一的房间 UUID
  2. 创建 `im_rtc_call` 记录
  3. 为发起者创建 JOINED 状态的参与者记录
  4. 为被邀请者创建 INVITING 状态的参与者记录
  5. 向被邀请者推送通话邀请通知

### 2. 邀请参与者

- **路径**: `POST /im/rtc/invite`
- **说明**: 向通话中追加邀请新参与者
- **权限**: 需要用户登录（通话参与者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| callId | Long | 是 | 通话 ID |
| inviteeIds | List<Long> | 是 | 被邀请用户 ID 列表 |

- **响应**: `CommonResult<Boolean>`

### 3. 加入通话

- **路径**: `POST /im/rtc/join`
- **说明**: 被邀请者加入通话
- **权限**: 需要用户登录（被邀请者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| callId | Long | 是 | 通话 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验通话存在且进行中
  2. 校验当前用户在参与者列表中且状态为 INVITING
  3. 更新参与者状态为 JOINED
  4. 生成 LiveKit 访问 Token

### 4. 接听通话

- **路径**: `POST /im/rtc/accept`
- **说明**: 被邀请者接听通话（一对一场景）
- **权限**: 需要用户登录（被邀请者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| callId | Long | 是 | 通话 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 更新参与者状态为 JOINED
  2. 更新通话状态为已接听
  3. 记录接听时间

### 5. 拒绝通话

- **路径**: `POST /im/rtc/reject`
- **说明**: 被邀请者拒绝通话
- **权限**: 需要用户登录（被邀请者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| callId | Long | 是 | 通话 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 更新参与者状态为 REJECTED
  2. 如果是一对一通话，更新通话状态为已结束

### 6. 取消通话

- **路径**: `POST /im/rtc/cancel`
- **说明**: 发起者取消通话（在未接听前）
- **权限**: 需要用户登录（通话发起者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| callId | Long | 是 | 通话 ID |

- **响应**: `CommonResult<Boolean>`

### 7. 离开通话

- **路径**: `POST /im/rtc/leave`
- **说明**: 参与者主动离开通话
- **权限**: 需要用户登录（通话参与者）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| callId | Long | 是 | 通话 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 更新参与者状态为 LEFT
  2. 如果所有参与者都已离开，更新通话状态为已结束

## LiveKit Webhook 接口

### 8. LiveKit Webhook 回调

- **路径**: `POST /im/livekit/webhook`
- **说明**: 接收 LiveKit 服务端的事件回调
- **权限**: `@PermitAll` + `@TenantIgnore`（无需登录，通过 JWT 签名验证）
- **请求参数**: LiveKit Webhook 事件 payload
- **响应**: `CommonResult<Boolean>`
- **安全机制**:
  1. 使用 LiveKit API Secret 对请求体进行 SHA256 签名验证
  2. 验证 JWT Token 的有效性
  3. 防止伪造的 Webhook 请求
- **处理事件**:
  - `room_started`: 房间开始
  - `room_finished`: 房间结束
  - `participant_joined`: 参与者加入
  - `participant_left`: 参与者离开
  - `track_published`: 轨道发布
  - `track_unpublished`: 轨道取消发布

## 关键实现

- **RtcService**: RTC 通话核心服务，管理通话生命周期
- **LiveKitService**: LiveKit 集成服务，管理房间和 Token 生成
- **LiveKit Webhook 安全**: 使用 `@PermitAll` + `@TenantIgnore` 标记，通过 JWT + SHA256 签名验证请求合法性
- **Token 生成**: 为每个参与者生成 LiveKit 访问 Token，包含房间权限和用户身份信息
- **超时处理**: 未接听的通话在超时后自动标记为 NO_ANSWER 状态

## 通话状态流转

```
创建 -> 进行中 -> 已结束
              |
              +-> 已取消（发起者取消）
              |
              +-> 未接听（超时无应答）
```

## 参与者状态流转

```
INVITING -> JOINED -> LEFT
         -> REJECTED
         -> NO_ANSWER（超时）
```
