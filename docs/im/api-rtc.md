# 实时通话接口 (ImRtcCallController / ImRtcLiveKitController / ImRtcCallManagerController)

> IM 实时音视频通话（基于 LiveKit）：用户端通话信令（创建/邀请/加入/接听/拒绝/取消/离开/超时兜底/活跃通话查询）、LiveKit Webhook 事件回调兜底清理、管理后台通话记录查询。

## 接口路径前缀

- `/im/rtc` (Controller: ImRtcCallController) —— 用户端通话信令，仅登录即可调用
- `/im/livekit` (Controller: ImRtcLiveKitController) —— LiveKit 厂商 Webhook 回调入口，`@PermitAll` + 请求签名校验
- `/im/manager/rtc` (Controller: ImRtcCallManagerController) —— 管理后台通话记录查询

存储模型：DB 单一存储（`im_rtc_call` 主表 + `im_rtc_participant` 明细表）；并发幂等通过 Redis 分布式锁 + 条件 UPDATE 保证；媒体协商完全交给 LiveKit，后端只做会话状态机、Token 签发、来电信令推送、通话历史落消息流。

关键枚举：

| 枚举 | 取值 |
|-----|------|
| 通话状态 ImRtcCallStatusEnum | 10=创建 CREATED、20=进行中 RUNNING、30=已结束 ENDED |
| 参与者状态 ImRtcParticipantStatusEnum | 10=邀请中 INVITING、20=已加入 JOINED、30=已拒绝 REJECTED、40=未应答 NO_ANSWER、50=已离开 LEFT |
| 媒体类型 ImRtcCallMediaTypeEnum | 1=语音、2=视频 |
| 结束原因 ImRtcCallEndReasonEnum | 1=通话结束 HANGUP、2=已拒绝 REJECT、3=已取消 CANCEL、4=无人接听 NO_ANSWER、5=对方正忙 BUSY、9=通话异常 ERROR |
| 会话类型 ImConversationTypeEnum | 私聊 / 群聊（通话仅支持这两种） |
| 参与角色 ImRtcParticipantRoleEnum | 主叫 INVITER / 被邀请人 INVITEE / 主动加入者 JOINER |

## 1. 通话信令（ImRtcCallController）

无独立权限标识，所有端点仅要求登录（已认证），身份从登录态取当前 userId。

通话主表状态机：CREATED → RUNNING → ENDED；CREATED 直接到 ENDED 表示无人接听 / 主叫取消。

### 1.1 创建通话

- **路径**: POST /im/rtc/create
- **权限**: 已认证
- **说明**: 创建新通话；按 conversationType 区分私聊 / 群聊，私聊走好友校验 + 好友对锁，群聊走群成员校验 + 群锁，忙线时不报错而是立即结束通话（reason=BUSY）

**请求参数 (ImRtcCallCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| conversationType | Integer | 是 | @NotNull、@InEnum(ImConversationTypeEnum)、@AssertTrue 仅支持私聊/群聊 | 会话类型 |
| mediaType | Integer | 是 | @NotNull、@InEnum(ImRtcCallMediaTypeEnum) | 媒体类型（1 语音 / 2 视频） |
| groupId | Long | 群聊必填 | 无 | 群编号；群聊场景必填 |
| inviteeIds | Set&lt;Long&gt; | 是 | 元素 @NotNull | 被邀请的用户编号集合；私聊必传 1 个对端，群聊必传至少 1 人 |

**响应**: CommonResult&lt;ImRtcCallRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| room | String | 业务通话编号 |
| livekitUrl | String | LiveKit Server WebSocket 地址；前端 connect 用 |
| token | String | LiveKit 接入 Token；仅非 ENDED 场景才签发，ENDED 时为 null（前端据此展示「通话已结束」） |
| conversationType | Integer | 会话类型 |
| mediaType | Integer | 媒体类型 |
| status | Integer | 通话状态 |
| endReason | Integer | 结束原因；仅 status=ENDED 时有值 |
| inviterId | Long | 发起人编号 |
| groupId | Long | 群编号；群通话才有 |
| inviteeIds | Set&lt;Long&gt; | 被邀请人编号集合（INVITING 状态） |
| joinedUserIds | Set&lt;Long&gt; | 已加入房间的成员编号集合（JOINED 状态） |

**业务逻辑**:
1. 校验通话功能已开启（配置开关）。
2. 校验入参：私聊必须恰好 1 个对端且不能呼叫自己，并校验双方为好友；群聊必须指定群编号、被邀请池非空，并校验发起人是群成员。
3. 按场景加 Redis 分布式锁（私聊按好友对、群聊按群编号）串行化，避免并发各开一通的竞态。
4. 锁内查重：群通话同群已有活跃通话则抛错（引导走 invite / join）；私聊双方已在同一通话视为数据异常抛错；随后检测发起人（私聊还检测对端）忙线状态。
5. 创建通话实体：room 用 UUID，INSERT 主表（status=CREATED），批量 INSERT 参与表（发起人即时 JOINED，被邀请人 INVITING）。
6. 忙线时立即 endSession(BUSY) 结束通话并落记录（群聊向全群推送完整 START + END）。
7. 推送 WebSocket 通知：RTC_CALL(INVITE) 给每个被邀请人（内含按被邀请人签发的 LiveKit token）；并向消息流写入 RTC_CALL_START（群聊全群广播、私聊定向给被叫），作为会话列表「[语音通话]」预览依据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_002 | 对方正在通话中 |
| 1_040_900_003 | 您正在通话中 |
| 1_040_900_005 | 不能呼叫自己 |
| 1_040_900_006 | 私聊通话必须指定对方 |
| 1_040_900_007 | 群聊通话必须指定群编号 |
| 1_040_900_009 | 该群已有进行中通话，请通过胶囊条加入 |
| 1_040_900_010 | 群通话邀请人数超过最大值 |
| 1_040_900_011 | 群通话必须选择被邀请人 |

### 1.2 通话中追加邀请

- **路径**: POST /im/rtc/invite
- **权限**: 已认证
- **说明**: 通话中追加邀请新成员；仅群通话可用

**请求参数 (ImRtcCallInviteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| room | String | 是 | @NotBlank | 业务通话编号 |
| inviteeIds | Set&lt;Long&gt; | 是 | @NotEmpty、元素 @NotNull | 新邀请的用户编号集合 |

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 校验通话功能已开启、通话存在且活跃（不存在 / 已结束抛错）。
2. 校验通话是群聊类型，私聊不支持追加邀请。
3. 校验操作者是房内 JOINED 状态的参与者。
4. 加群锁后执行追加：校验被邀请人都是该群活跃成员。
5. 排除已在通话池中的用户，剩余为新邀请；无可新增则直接返回；校验人数不超过 groupMaxParticipants 上限。
6. 批量 INSERT 新参与者（INVITING 状态），并推送 RTC_CALL(INVITE) WebSocket 通知给每个新被邀请人。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_004 | 您不在该通话中 |
| 1_040_900_007 | 群聊通话必须指定群编号 |
| 1_040_900_010 | 群通话邀请人数超过最大值 |

### 1.3 加入群通话

- **路径**: POST /im/rtc/join
- **权限**: 已认证
- **说明**: 加入已有群通话；用于胶囊条「加入」按钮

**请求参数**: Query 参数 `room`（String，必填，业务通话编号）

**响应**: CommonResult&lt;ImRtcCallRespVO&gt;（字段同 1.1，含按当前用户签发的 token）

**业务逻辑**:
1. 校验通话功能已开启、通话存在且活跃。
2. 仅群通话支持「旁观者加入」，私聊抛错。
3. 校验当前用户是该群有效成员，防止仅凭 room 就拿到 LiveKit token 越权入会。
4. 校验当前用户没有其它活跃通话（忙线抛错）。
5. 参与表写入：已有参与记录切回 JOINED（写 acceptTime）；无记录则以 JOINER 角色 INSERT，唯一键冲突时回查复用并发写入的记录。
6. 主表状态推进：首次有非发起人加入时 CREATED → RUNNING（条件 UPDATE 保幂等，多人并发只有一人成功）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_003 | 您正在通话中 |
| 1_040_900_007 | 群聊通话必须指定群编号 |

### 1.4 接听通话

- **路径**: POST /im/rtc/accept
- **权限**: 已认证
- **说明**: 被叫接听通话

**请求参数**: Query 参数 `room`（String，必填，业务通话编号）

**响应**: CommonResult&lt;ImRtcCallRespVO&gt;（字段同 1.1，含按当前用户签发的 token）

**业务逻辑**:
1. 校验通话功能已开启、通话存在且活跃。
2. 校验本人是该通话的参与者。
3. 已 JOINED 直接幂等返回；否则校验当前用户不在其它活跃通话中。
4. 仅 INVITING → JOINED：条件 UPDATE 写 acceptTime，其它状态拒绝；更新影响 0 行（并发已变更）抛错。
5. 主表状态推进：首次有非发起人接通时 CREATED → RUNNING（条件 UPDATE 保幂等）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_003 | 您正在通话中 |
| 1_040_900_004 | 您不在该通话中 |

### 1.5 拒绝通话

- **路径**: POST /im/rtc/reject
- **权限**: 已认证
- **说明**: 被叫拒绝通话

**请求参数**: Query 参数 `room`（String，必填，业务通话编号）

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 校验通话功能已开启、通话存在且活跃、本人是该通话参与者。
2. 仅 INVITING 状态可拒绝；INVITING → REJECTED 条件 UPDATE（写 leaveTime），并发已变更则忽略。
3. 群通话：推 RTC_CALL(REJECT) WebSocket 通知给通话受众，再触发关房判定（全员拒接 / 只剩主叫一人时收敛关房）。
4. 私聊：直接 endSession(REJECT)，推 RTC_CALL_END 入消息流，两端 UI 收敛。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_004 | 您不在该通话中 |

### 1.6 取消邀请

- **路径**: POST /im/rtc/cancel
- **权限**: 已认证
- **说明**: 主叫接通前取消通话

**请求参数**: Query 参数 `room`（String，必填，业务通话编号）

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 校验通话功能已开启、通话存在且活跃。
2. 仅主叫（通话发起人）可取消，其它人抛错。
3. 仅 CREATED 状态可取消（已进入 RUNNING 应走 leave），否则抛错。
4. endSession(CANCEL)：主表条件 UPDATE 推到 ENDED、残留 INVITING 批量改 NO_ANSWER、残留 JOINED 改 LEFT。
5. 推 RTC_CALL_END WebSocket / 消息流通知（endReason=CANCEL），并兜底删除 LiveKit 房间强制断开残留客户端。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_004 | 您不在该通话中 |

### 1.7 离开通话

- **路径**: POST /im/rtc/leave
- **权限**: 已认证
- **说明**: 接通后挂断 / 离开通话

**请求参数**: Query 参数 `room`（String，必填，业务通话编号）

**响应**: CommonResult&lt;Boolean&gt;（成功返回 true）

**业务逻辑**:
1. 校验通话功能已开启、通话存在且活跃、本人是该通话参与者。
2. 当前状态 → LEFT：条件 UPDATE（写 leaveTime）防并发反复改；影响 0 行直接返回。
3. 群通话已入会（JOINED）参与者离开时，推 RTC_PARTICIPANT_DISCONNECTED 通知（私聊推双方、群聊广播全群）。
4. 触发关房判定：私聊任一方离开必关；群通话仅「无人在房（JOINED=0）」或「只剩 1 人且无响铃（JOINED=1 且 INVITING=0）」时关。
5. 关房时 endSession 按 call.status 自动推结束原因：CREATED（没人接通过）= CANCEL，RUNNING = HANGUP；并兜底删除 LiveKit 房间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_004 | 您不在该通话中 |

### 1.8 振铃超时检查

- **路径**: POST /im/rtc/no-answer-call-check
- **权限**: 已认证
- **说明**: 前端 RUNNING 端 timer 兜底；触发后端立即扫描该 room 的振铃超时（接口静默，不暴露错误）

**请求参数**: Query 参数 `room`（String，必填，业务通话编号）

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 鉴权：仅该 room 的参与者可触发；非参与者静默返回，不暴露错误。
2. 超时阈值取后端配置 inviteTimeoutMinutes（避免前后端配置不一致），查询该 room 内邀请时间早于阈值的 INVITING 参与者。
3. 逐个 CAS 把 INVITING → NO_ANSWER（写 leaveTime）；并发已变更（刚接 / 拒 / 整体结束）则跳过。
4. 群通话：推 RTC_CALL(NO_ANSWER) WebSocket 通知让前端 banner 移除该人，并级联关房判定；私聊：被叫超时即整通结束，走 endSession(NO_ANSWER) 推 RTC_CALL_END。

**错误码**: 无（接口静默，失败不抛错）

### 1.9 查询群活跃通话

- **路径**: GET /im/rtc/get-active-call
- **权限**: 已认证
- **说明**: 查询当前进行中的通话；用于群聊顶部「N 人正在通话」胶囊条

**请求参数**: Query 参数 `groupId`（Long，必填，群编号）

**响应**: CommonResult&lt;ImRtcGroupCallRespVO&gt;（无活跃通话时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| room | String | 业务通话编号 |
| groupId | Long | 群编号 |
| mediaType | Integer | 媒体类型 |
| inviterId | Long | 发起人编号 |
| joinedUserIds | Set&lt;Long&gt; | 已加入房间的用户编号集合 |
| inviteeIds | Set&lt;Long&gt; | 被邀请池；用于胶囊条展开时显示待加入头像 |

**业务逻辑**:
1. 校验通话功能已开启。
2. 鉴权：仅群活跃成员能查（走单行 SQL，不依赖成员列表缓存）。
3. 查询该群最近的活跃通话（CREATED / RUNNING），拼装不含 token 的展示用响应 VO。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |

## 2. LiveKit Webhook 回调（ImRtcLiveKitController）

### 2.1 LiveKit Webhook 回调

- **路径**: POST /im/livekit/webhook
- **权限**: @PermitAll（不走登录鉴权）；另加 @TenantIgnore 忽略租户。安全由请求签名（Authorization 头 JWT + body sha256）保证，伪造请求被签名校验直接拒绝
- **说明**: 接收 LiveKit 成员加入 / 离开 / 房间结束等事件，做业务态兜底清理

**请求参数**: 原始 JSON body（String），由 LiveKit 服务端推送；事件载荷含 event 类型、room 名称、participant identity 等

**响应**: CommonResult&lt;Boolean&gt;（是否处理成功；伪造 / 非法事件返回 false）

**业务逻辑**:
1. 校验请求签名（Authorization 头对 rawBody 做 sha256 校验）；失败记 warn 日志并返回 false，但不报错，避免给攻击者反馈。
2. 解析事件载荷；非法 / 空 event 直接忽略。
3. 交给 Service 按事件类型分发处理（幂等由条件 UPDATE 保证）：
   - participant_joined：通话活跃且能从 identity 解析出 userId 时，转推 1602 RTC_PARTICIPANT_CONNECTED 通知（DB 接通态由 accept 接口写入，此处仅转推）。
   - participant_left：兜底把 JOINED → LEFT（正常 leave 接口已清理过的，条件 UPDATE 自动幂等跳过），推 1603 RTC_PARTICIPANT_DISCONNECTED 通知，并触发关房判定。
   - room_finished：兜底把通话主表推到 ENDED，endSession(HANGUP) 完成清理与通知。
   - 其它事件忽略（track_published 等业务态由 LiveKit 客户端事件驱动，后端不重复推）。
4. 处理异常仅记 error 日志，不向 LiveKit 返回失败。

**错误码**: 无（内部异常均吞掉记日志）

## 3. 通话记录管理（ImRtcCallManagerController）

### 3.1 通话记录分页

- **路径**: GET /im/manager/rtc/page
- **权限**: im:manager:rtc:query
- **说明**: 分页查询通话记录，附带发起人昵称与群名称

**请求参数 (ImRtcCallManagerPageReqVO，继承 PageParam 分页参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | PageParam | 页码 |
| pageSize | Integer | 否 | PageParam | 每页条数 |
| inviterUserId | Long | 否 | 无 | 发起人用户编号 |
| conversationType | Integer | 否 | 无 | 会话类型 |
| mediaType | Integer | 否 | 无 | 媒体类型 |
| status | Integer | 否 | 无 | 通话状态 |
| endReason | Integer | 否 | 无 | 结束原因 |
| startTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发起时间范围 |

**响应**: CommonResult&lt;PageResult&lt;ImRtcCallManagerRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| room | String | 业务通话编号 |
| conversationType | Integer | 会话类型 |
| mediaType | Integer | 媒体类型 |
| inviterUserId | Long | 发起人用户编号 |
| inviterNickname | String | 发起人昵称 |
| groupId | Long | 群编号；私聊为空 |
| groupName | String | 群名称；私聊为空 |
| status | Integer | 通话状态 |
| endReason | Integer | 结束原因 |
| startTime | LocalDateTime | 发起时间 |
| acceptTime | LocalDateTime | 接通时间；未接通为空 |
| endTime | LocalDateTime | 结束时间；未结束为空 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按查询条件分页查询通话主表。
2. 批量查询发起人用户信息与群信息，拼装 inviterNickname / groupName。

### 3.2 通话记录详情

- **路径**: GET /im/manager/rtc/get
- **权限**: im:manager:rtc:query
- **说明**: 按编号查询单条通话记录详情

**请求参数**: Query 参数 `id`（Long，必填，通话编号）

**响应**: CommonResult&lt;ImRtcCallManagerRespVO&gt;（字段同 3.1；不存在时 data 为 null）

**业务逻辑**:
1. 按编号查询通话主表，不存在返回 null。
2. 拼装发起人昵称与群名称后返回。

### 3.3 通话参与者列表

- **路径**: GET /im/manager/rtc/participant-list
- **权限**: im:manager:rtc:query
- **说明**: 按通话编号查询参与者明细列表

**请求参数**: Query 参数 `id`（Long，必填，通话编号）

**响应**: CommonResult&lt;List&lt;ImRtcParticipantManagerRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| callId | Long | 通话编号 |
| userId | Long | 参与者用户编号 |
| userNickname | String | 参与者昵称 |
| role | Integer | 参与角色（主叫 / 被邀请人 / 主动加入者） |
| status | Integer | 参与状态（邀请中 / 已加入 / 已拒绝 / 未应答 / 已离开） |
| inviteTime | LocalDateTime | 被邀请时间 |
| acceptTime | LocalDateTime | 接听时间；未接听为空 |
| leaveTime | LocalDateTime | 离开时间；未加入为空 |

**业务逻辑**:
1. 按通话编号查询参与者明细列表，为空返回空集合。
2. 批量查询参与者用户信息，拼装 userNickname 后返回。

## 附：实时通话域错误码汇总（1-040-900-000 段）

| 错误码 | 说明 |
|-------|------|
| 1_040_900_000 | 通话功能未开启 |
| 1_040_900_001 | 通话已结束 |
| 1_040_900_002 | 对方正在通话中 |
| 1_040_900_003 | 您正在通话中 |
| 1_040_900_004 | 您不在该通话中 |
| 1_040_900_005 | 不能呼叫自己 |
| 1_040_900_006 | 私聊通话必须指定对方 |
| 1_040_900_007 | 群聊通话必须指定群编号 |
| 1_040_900_008 | 通话发起繁忙，请稍后再试 |
| 1_040_900_009 | 该群已有进行中通话，请通过胶囊条加入 |
| 1_040_900_010 | 群通话邀请人数超过最大值 |
| 1_040_900_011 | 群通话必须选择被邀请人 |
