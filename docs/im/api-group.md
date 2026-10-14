# 群聊接口 (ImGroupController / ImGroupMemberController / ImGroupRequestController / ImGroupManagerController / ImGroupMemberManagerController / ImGroupRequestManagerController)

> 提供群聊全生命周期能力：建群、群信息维护、成员邀请/踢出/角色管理、禁言、消息置顶、加群申请审批，以及平台管理端的群分页查询、封禁/解封、强制解散与申请审计。

## 接口路径前缀

- `/im/group`  (Controller: ImGroupController) —— 登录用户端群操作
- `/im/group-member`  (Controller: ImGroupMemberController) —— 登录用户端群成员操作
- `/im/group-request`  (Controller: ImGroupRequestController) —— 登录用户端加群申请
- `/im/manager/group`  (Controller: ImGroupManagerController) —— 平台管理端群管理
- `/im/manager/group/member`  (Controller: ImGroupMemberManagerController) —— 平台管理端群成员管理
- `/im/manager/group-request`  (Controller: ImGroupRequestManagerController) —— 平台管理端加群申请审计

用户端三个控制器（`/im/group`、`/im/group-member`、`/im/group-request`）的所有端点均无 `@PreAuthorize` 注解，权限由业务逻辑内的"群主 / 管理员 / 有效成员"校验控制，仅需登录（已认证）。管理端三个控制器的端点均需对应权限标识。

## 1. 群操作（ImGroupController，登录用户端）

### 1.1 创建群

- **路径**: POST /im/group/create
- **权限**: 已认证
- **说明**: 创建新群，创建者自动成为群主（OWNER），可同时邀请初始成员。

**请求参数 (ImGroupCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotBlank、@Size(max=64) | 群名称 |
| memberUserIds | List\<Long\> | 否 | 无 | 初始成员用户编号列表（不含创建者自己） |
| joinApproval | Boolean | 否 | 无 | 进群是否需群主 / 管理员审批；不传默认 false 自由进群 |

**响应**: CommonResult\<ImGroupRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 群名称 |
| ownerUserId | Long | 群主用户编号 |
| avatar | String | 群头像 |
| notice | String | 群公告 |
| banned | Boolean | 是否封禁 |
| mutedAll | Boolean | 是否全群禁言 |
| joinApproval | Boolean | 进群是否需群主 / 管理员审批 |
| bannedTime | LocalDateTime | 封禁时间 |
| status | Integer | 群状态（CommonStatusEnum：0 正常 / 1 停用） |
| dissolvedTime | LocalDateTime | 解散时间 |
| createTime | LocalDateTime | 创建时间 |
| joinStatus | Integer | 当前登录用户在该群的成员状态：在群 / 已退群（CommonStatusEnum） |
| groupRemark | String | 当前登录用户对该群的备注 |
| silent | Boolean | 当前登录用户是否免打扰 |
| pinnedMessages | List\<ImGroupMessageRespVO\> | 群置顶消息列表，按 pin 顺序；非该群有效成员时为空 |

**业务逻辑**:
1. 处理初始成员列表（去重并排除创建者自己）。
2. 校验初始成员都是创建者的好友，否则抛出"不是您的好友"错误（含昵称列表）。
3. 校验群人数上限：创建者 + 初始成员数不得超过配置的 maxMember。
4. 插入群记录（ownerUserId=创建者，status=正常），创建者以 OWNER 角色入群，初始成员批量入群（addSource=INVITE、inviter=创建者）。
5. 向全员（含创建者，用于多端同步）推送 GROUP_CREATE 通知。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_500_006 | '{}' 不是您的好友，邀请失败 |
| 1_040_500_005 | 群聊人数不能超过 {} 人 |

### 1.2 更新群

- **路径**: PUT /im/group/update
- **权限**: 已认证（仅群主）
- **说明**: 更新群名称 / 头像 / 公告 / 进群审批开关，仅群主可操作。

**请求参数 (ImGroupUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| name | String | 否 | @Size(max=64)、@AssertTrue 非空串 | 群名称 |
| avatar | String | 否 | @Size(max=512)、@AssertTrue 非空串 | 群头像 |
| notice | String | 否 | @Size(max=2048) | 群公告（允许空串，表示清空公告） |
| joinApproval | Boolean | 否 | 无 | 进群是否需群主 / 管理员审批 |

**响应**: CommonResult\<ImGroupRespVO\>（字段同 1.1）

**业务逻辑**:
1. 校验群存在，并校验操作人是群主，否则抛"仅群主可执行该操作"。
2. 按非空字段更新群记录（仅含变更字段），并清除群缓存。
3. 查询活跃成员（只查一次复用），按变更字段分别推送通知：名称变更推 GROUP_NAME、公告变更推 GROUP_NOTICE、头像 / 审批开关变更推 GROUP_INFO_UPDATE。
4. 返回合并后的新群信息（请求 VO 非空字段覆盖老群信息）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_400_003 | 仅群主可执行该操作 |

### 1.3 解散群

- **路径**: DELETE /im/group/dissolve
- **权限**: 已认证（仅群主）
- **说明**: 群主解散群聊，群状态置为已解散并移除全部成员。

**请求参数**: 无（Query 参数 id=群编号，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在且未解散。
2. 校验当前用户是群主。
3. 先向全员广播 GROUP_DISSOLVE 通知（在成员移除前发送，保证能查到全员）。
4. 更新群状态为已解散并记录解散时间，然后移除全部群成员（置 DISABLE + 退群时间）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_002 | 群已解散 |
| 1_040_400_003 | 仅群主可执行该操作 |

### 1.4 获得群

- **路径**: GET /im/group/get
- **权限**: 已认证
- **说明**: 按编号获得群详情，附带登录用户的成员状态与置顶消息回填。

**请求参数**: 无（Query 参数 id=群编号，必填）

**响应**: CommonResult\<ImGroupRespVO\>（字段同 1.1）

**业务逻辑**:
1. 按编号查询群（走 Redis 缓存）。
2. 批量转换 VO：仅当登录用户是该群有效成员（status=ENABLE）时回填 pinnedMessages 置顶消息内容，避免非成员 / 已退群用户越权获取。
3. 标记登录用户在该群的 joinStatus（在群 / 已退群），并回填该成员的 groupRemark / silent 个人字段。

### 1.5 获得当前登录用户的群列表

- **路径**: GET /im/group/list
- **权限**: 已认证
- **说明**: 获得当前登录用户曾经加入的所有群（含已退群 / 已解散 / 已封禁的群，供前端展示历史消息）。

**请求参数**: 无

**响应**: CommonResult\<List\<ImGroupRespVO\>\>（字段同 1.1）

**业务逻辑**:
1. 查询当前用户的所有群成员记录（含已退群记录）。
2. 按群编号批量查询群信息（不按 status / banned 过滤，已解散 / 封禁的群也返回）。
3. 批量转换 VO：仅对当前用户仍是有效成员的群回填 pinnedMessages；逐群标记 joinStatus 并回填 groupRemark / silent。

### 1.6 邀请用户加入群

- **路径**: POST /im/group/invite
- **权限**: 已认证（需为群有效成员）
- **说明**: 邀请用户加入群；群开启审批且邀请人是普通成员时转为加群申请。

**请求参数 (ImGroupMemberInviteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| groupId | Long | 是 | @NotNull | 群编号 |
| memberUserIds | List\<Long\> | 是 | @NotEmpty | 被邀请的用户编号列表 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在、操作者是群有效成员；入参去重并排除已在群中的用户，全部已在群则直接返回。
2. 校验被邀请人都是当前用户的好友。
3. 校验群人数上限（活跃成员数 + 邀请数 ≤ maxMember）。
4. 情况一：群开启审批且邀请人是普通成员，则落 group_request 邀请申请，等群主 / 管理员处理，直接返回。
5. 情况二：未开审批或群主 / 管理员邀请，批量添加群成员（addSource=INVITE、inviterUserId=操作人）。
6. 向全员（活跃成员 + 新成员）推送 GROUP_MEMBER_INVITE 通知。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_500_001 | 您已不在该群中 |
| 1_040_500_006 | '{}' 不是您的好友，邀请失败 |
| 1_040_500_005 | 群聊人数不能超过 {} 人 |

### 1.7 退出群

- **路径**: DELETE /im/group/quit
- **权限**: 已认证（群主不可退群）
- **说明**: 当前登录用户退出指定群。

**请求参数**: 无（Query 参数 groupId=群编号，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在且未解散。
2. 校验当前用户不是群主（群主需先转让群主或解散群聊）。
3. 校验当前用户是该群有效成员。
4. 先广播 GROUP_MEMBER_QUIT 通知，再移除群成员（置 DISABLE + 退群时间）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_002 | 群已解散 |
| 1_040_500_003 | 群主不能退出群聊，请先转让群主或解散群聊 |
| 1_040_500_001 | 您已不在该群中 |

### 1.8 移除群成员

- **路径**: DELETE /im/group/kicking
- **权限**: 已认证（群主 / 管理员）
- **说明**: 将指定成员移出群聊，带三档权限校验。

**请求参数 (ImGroupMemberRemoveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| groupId | Long | 是 | @NotNull | 群编号 |
| memberUserIds | List\<Long\> | 是 | @NotEmpty | 被移除的用户编号列表 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在 + 操作者是群主或管理员。
2. 校验不能移除自己。
3. 仅保留仍有效（ENABLE）的目标成员，已退群 / 不存在的直接跳过；全部无效则直接返回。
4. 三档权限校验：群主不可被移出；管理员不能移出其他管理员。
5. 先广播 GROUP_MEMBER_KICK 通知（在成员移除前发送），再批量移除目标成员（保留退群前已读位置）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_004 | 仅群主或管理员可执行该操作 |
| 1_040_500_004 | 不能将自己移出群聊 |
| 1_040_500_010 | 群主无法被移出群聊 |
| 1_040_500_011 | 管理员无法移出其他管理员，请先由群主撤销其管理员身份 |

### 1.9 添加群管理员

- **路径**: PUT /im/group/add-admin
- **权限**: 已认证（仅群主）
- **说明**: 将指定成员设为群管理员，受管理员数量上限约束。

**请求参数 (ImGroupAdminAddReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| userIds | List\<Long\> | 是 | @NotEmpty | 目标用户编号列表 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 仅群主可操作（校验群存在 + 操作人是群主）。
2. 校验目标都是当前群的有效成员且非群主。
3. 幂等过滤：跳过已是管理员的用户，全部已是管理员则直接返回。
4. 校验管理员数量上限（现有管理员数 + 变更数 ≤ adminMaxCount）。
5. 批量更新目标角色为 ADMIN；更新行数不符时抛"目标用户已不在该群中"。
6. 推送 GROUP_ADMIN_ADD 通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_400_003 | 仅群主可执行该操作 |
| 1_040_500_007 | 目标用户已不在该群中 |
| 1_040_500_008 | 群主无法被设为或撤销管理员 |
| 1_040_500_009 | 群管理员数量不能超过 {} 人 |

### 1.10 撤销群管理员

- **路径**: PUT /im/group/remove-admin
- **权限**: 已认证（仅群主）
- **说明**: 将指定管理员撤销为普通成员。

**请求参数 (ImGroupAdminRemoveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| userIds | List\<Long\> | 是 | @NotEmpty | 目标用户编号列表 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 仅群主可操作（校验群存在 + 操作人是群主）。
2. 校验目标都是当前群的有效成员且非群主。
3. 幂等过滤：跳过已是普通成员的用户。
4. 批量更新目标角色为普通成员（NORMAL）。
5. 推送 GROUP_ADMIN_REMOVE 通知给全员。

**错误码**: 同 1.9。

### 1.11 转让群主

- **路径**: PUT /im/group/transfer-owner
- **权限**: 已认证（仅老群主）
- **说明**: 将群主转让给群内其他有效成员。

**请求参数 (ImGroupTransferOwnerReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| newOwnerUserId | Long | 是 | @NotNull | 新群主用户编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 仅老群主可执行（校验群存在 + 操作人是群主）。
2. 校验不能转让给自己。
3. 校验新群主必须是群的有效成员。
4. 更新成员角色：新群主置为 OWNER，老群主降为普通成员（NORMAL）；更新行数不符时抛错。
5. 更新群的 ownerUserId 字段。
6. 推送 GROUP_OWNER_TRANSFER 通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_400_003 | 仅群主可执行该操作 |
| 1_040_400_005 | 不能将群主转让给自己 |
| 1_040_500_001 | 您已不在该群中 |

### 1.12 置顶群消息

- **路径**: PUT /im/group/pin-message
- **权限**: 已认证（群主 / 管理员）
- **说明**: 将群内一条普通消息置顶，受置顶数量上限约束。

**请求参数 (ImGroupMessagePinReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| messageId | Long | 是 | @NotNull | 消息编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验操作人是群主 / 管理员（锁定群记录并返回群信息）。
2. 校验消息存在、属于该群、是普通聊天消息（不允许置顶群事件 / 撤回事件）且未被撤回。
3. 定向消息（receiverUserIds 非空）不允许置顶，避免置顶广播泄露仅部分人可见的内容。
4. 幂等校验（已置顶抛错）+ 数量上限校验（≤ pinMaxCount），随后追加到群记录的 pinnedMessageIds。
5. 推送 GROUP_MESSAGE_PIN 通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_004 | 仅群主或管理员可执行该操作 |
| 1_040_400_006 | 群置顶消息数量不能超过 {} 条 |
| 1_040_400_007 | 该消息已置顶 |
| 1_040_400_009 | 定向消息不支持置顶 |
| 1_040_300_009 | 消息不属于该群 |

### 1.13 取消置顶群消息

- **路径**: PUT /im/group/unpin-message
- **权限**: 已认证（群主 / 管理员）
- **说明**: 取消一条已置顶的群消息。

**请求参数 (ImGroupMessagePinReqVO)**: 字段同 1.12。

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验操作人是群主 / 管理员（锁定群记录并返回群信息）。
2. 幂等校验：消息必须在 pinnedMessageIds 中，否则抛"该消息未置顶"。
3. 从 pinnedMessageIds 移除并更新群记录。
4. 推送 GROUP_MESSAGE_UNPIN 通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_004 | 仅群主或管理员可执行该操作 |
| 1_040_400_008 | 该消息未置顶 |

### 1.14 全群禁言 / 取消

- **路径**: PUT /im/group/mute-all
- **权限**: 已认证（群主 / 管理员）
- **说明**: 设置或取消全群禁言。

**请求参数 (ImGroupMuteAllReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| mutedAll | Boolean | 是 | @NotNull | 是否全群禁言 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验操作人是群主 / 管理员。
2. 更新群的 mutedAll 字段。
3. 按开关值广播 GROUP_MUTED 或 GROUP_CANCEL_MUTED 通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_400_004 | 仅群主或管理员可执行该操作 |

### 1.15 禁言成员

- **路径**: PUT /im/group/mute-member
- **权限**: 已认证（群主 / 管理员，三档分层校验）
- **说明**: 禁言指定成员，支持时长禁言与永久禁言。

**请求参数 (ImGroupMuteMemberReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| userId | Long | 是 | @NotNull | 被禁言的用户编号 |
| mutedSeconds | Integer | 是 | @NotNull、@Min(0) | 禁言时长（秒），0 表示永久禁言 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验不能禁言自己。
2. 校验群存在且未封禁，操作人和目标都在群中。
3. 三档分层权限校验：普通成员不能禁言任何人；群主不可被禁言；管理员不能禁言其他管理员。
4. 更新目标的 muteEndTime：时长 0 置为永久禁言时间戳，否则为当前时间 + 禁言秒数。
5. 广播 GROUP_MEMBER_MUTED 通知给全员（含禁言到期时间）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_400_004 | 仅群主或管理员可执行该操作 |
| 1_040_500_001 | 您已不在该群中 |
| 1_040_500_014 | 不能禁言自己 |
| 1_040_500_015 | 群主无法被禁言 |
| 1_040_500_016 | 管理员无法禁言其他管理员 |

### 1.16 取消成员禁言

- **路径**: PUT /im/group/cancel-mute-member
- **权限**: 已认证（群主 / 管理员，三档分层校验）
- **说明**: 取消指定成员的禁言。

**请求参数 (ImGroupCancelMuteMemberReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| userId | Long | 是 | @NotNull | 被取消禁言的用户编号 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在且未封禁，操作人和目标都在群中。
2. 三档分层权限校验（同 1.15）。
3. 清空目标的 muteEndTime。
4. 广播 GROUP_MEMBER_CANCEL_MUTED 通知给全员。

**错误码**: 同 1.15。

## 2. 群成员（ImGroupMemberController，登录用户端）

### 2.1 更新群成员

- **路径**: PUT /im/group-member/update
- **权限**: 已认证（仅操作自己的成员记录）
- **说明**: 更新自己的群内昵称、群备注、免打扰设置。

**请求参数 (ImGroupMemberUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| groupId | Long | 是 | @NotNull | 群编号 |
| displayUserName | String | 否 | 无 | 群内昵称（空串视为清空昵称） |
| groupRemark | String | 否 | 无 | 群备注 |
| silent | Boolean | 否 | 无 | 是否免打扰 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验当前用户是该群的有效成员。
2. 按成员记录 id 更新群成员信息。
3. displayUserName 是公开字段且变更时，推送 GROUP_MEMBER_NICKNAME_UPDATE 在线同步给全员。
4. silent / groupRemark 是个人字段且变更时，仅推送给本人做多端同步（GROUP_MEMBER_SETTING_UPDATE）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_500_001 | 您已不在该群中 |

### 2.2 获得群成员

- **路径**: GET /im/group-member/get
- **权限**: 已认证（需为该群有效成员）
- **说明**: 按编号或 groupId + userId 查询单个群成员。

**请求参数**: 无（Query 参数三选一模式：id=成员记录编号；或 groupId + userId 组合查询）

**响应**: CommonResult\<ImGroupMemberRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| groupId | Long | 群编号 |
| userId | Long | 用户编号 |
| displayUserName | String | 组内显示名 |
| groupRemark | String | 群备注（非本人查询时置空） |
| silent | Boolean | 是否免打扰（非本人查询时置空） |
| status | Integer | 成员状态（CommonStatusEnum） |
| role | Integer | 成员角色（ImGroupMemberRoleEnum：1=群主 2=管理员 3=普通成员） |
| joinTime | LocalDateTime | 入群时间 |
| quitTime | LocalDateTime | 退群时间 |
| muteEndTime | LocalDateTime | 禁言到期时间 |
| createTime | LocalDateTime | 创建时间 |
| nickname | String | 用户昵称（聚合自 AdminUser） |
| avatar | String | 用户头像（聚合自 AdminUser） |

**业务逻辑**:
1. 参数校验：传 id 则按编号查；传 groupId + userId 则组合查；否则抛 IllegalArgumentException。
2. 查无记录返回 null；否则校验当前登录用户是该成员所在群的有效成员。
3. 转换 VO 并聚合 AdminUser 的昵称 / 头像。
4. 非本人查看时置空私人字段（groupRemark / silent）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_500_001 | 您已不在该群中 |

### 2.3 获得指定群的成员列表

- **路径**: GET /im/group-member/list
- **权限**: 已认证（需为该群有效成员）
- **说明**: 按群全量拉取成员列表（含已退群成员），作为前端本地成员缓存的完整基线。

**请求参数**: 无（Query 参数 groupId=群编号，必填）

**响应**: CommonResult\<List\<ImGroupMemberRespVO\>\>（字段同 2.2）

**业务逻辑**:
1. 查询群全部成员（含 DISABLE 已退群成员，不按时间过滤；保留已退群成员供前端展示历史消息时的昵称 / 头像）。
2. 校验当前登录用户是该群的有效成员，非成员不可查看。
3. 批量聚合 AdminUser 昵称 / 头像（避免 N+1），非本人置空私人字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_500_001 | 您已不在该群中 |

## 3. 加群申请（ImGroupRequestController，登录用户端）

### 3.1 申请加群

- **路径**: POST /im/group-request/apply
- **权限**: 已认证
- **说明**: 申请加入群；群未开审批时直接入群，开启审批时落申请记录并通知群主 / 管理员。

**请求参数 (ImGroupRequestApplyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| groupId | Long | 是 | @NotNull | 群编号 |
| applyContent | String | 否 | @Size(max=255) | 申请理由 |
| addSource | Integer | 否 | @InEnum(ImGroupAddSourceEnum) | 加入来源（1=搜索 2=邀请 3=扫码 4=分享链接） |

**响应**: CommonResult\<Long\>（申请记录编号；未开审批直接入群时返回 null）

**业务逻辑**:
1. 校验群存在且未封禁 / 未解散，并校验申请人未在群中。
2. 情况一：群未开启审批，校验人数上限后直接入群（addSource 取前端入口、inviterUserId=null），推 1510 GROUP_MEMBER_ENTER 全员广播，不落申请记录，返回 null。
3. 情况二：群开启审批，创建主动申请记录；已有旧申请则覆盖申请内容并重置为未处理（唯一键并发冲突时回查复用）。
4. 向群主 + 全部管理员定向推送 1503 GROUP_REQUEST_RECEIVED 通知（多端同步，payload 携带申请方昵称 / 头像）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_510_004 | 您已在该群中，无需重复申请 |
| 1_040_500_005 | 群聊人数不能超过 {} 人 |

### 3.2 同意加群申请

- **路径**: PUT /im/group-request/agree
- **权限**: 已认证（群主 / 管理员）
- **说明**: 同意一条未处理的加群 / 邀请申请，申请人入群。

**请求参数**: 无（Query 参数 id=申请编号，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验申请存在 + 未处理 + 操作人是该群群主 / 管理员。
2. 复核群当前状态（封禁 / 解散的群不放人），并复核申请人未已在群中（幂等，避免重复广播入群事件）。
3. 校验人数上限（群已满抛错，让操作人改选拒绝）。
4. 乐观锁推进申请状态为"已同意"（记录处理人 / 处理时间），乐观锁失败抛"加群申请已处理"。
5. 写群成员（addSource / inviterUserId 沿用申请记录上的来源信息）。
6. 向申请人 + 群主 + 全部管理员定向推送 1505 GROUP_REQUEST_APPROVED 通知；同时按来源推群事件：主动申请推 1510 自由进群，被邀请推 1509 成员加入。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_510_001 | 加群申请不存在 |
| 1_040_510_002 | 加群申请已处理 |
| 1_040_510_003 | 仅群主或管理员可处理加群申请 |
| 1_040_510_004 | 您已在该群中，无需重复申请 |
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_500_001 | 您已不在该群中 |
| 1_040_500_005 | 群聊人数不能超过 {} 人 |

### 3.3 拒绝加群申请

- **路径**: PUT /im/group-request/refuse
- **权限**: 已认证（群主 / 管理员）
- **说明**: 拒绝一条未处理的加群 / 邀请申请，可选填处理理由。

**请求参数**: 无（Query 参数 id=申请编号，必填；handleContent=处理理由，可选，@Size(max=255)）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验申请存在 + 未处理 + 操作人是该群群主 / 管理员。
2. 乐观锁推进申请状态为"已拒绝"（记录处理理由 / 处理人 / 处理时间），乐观锁失败抛"加群申请已处理"。
3. 向申请人 + 群主 + 全部管理员定向推送 1506 GROUP_REQUEST_REJECTED 通知（payload 携带处理理由）。

**错误码**: 同 3.2（不含人数上限相关）。

### 3.4 查询我管理的群的未处理申请列表

- **路径**: GET /im/group-request/unhandled-list
- **权限**: 已认证
- **说明**: 查询「我管理的所有群」下的未处理加群申请（不分页），前端据此派生横幅红点 + Drawer 列表。

**请求参数**: 无

**响应**: CommonResult\<List\<ImGroupRequestRespVO\>\>（字段见 3.7）

**业务逻辑**:
1. 查询当前用户的全部群成员记录，筛选出其担任群主 / 管理员的群集合；为空直接返回空列表。
2. 一次性拉取这些群下所有未处理（handleResult=未处理）的申请。
3. 批量聚合申请人 / 邀请人的昵称头像与群名称 / 群头像后返回。

### 3.5 增量拉取加群申请

- **路径**: GET /im/group-request/pull
- **权限**: 已认证
- **说明**: 按游标增量拉取「我管理的群」下的加群申请，用于重连 / 离线补偿。

**请求参数**: 无（Query 参数：lastUpdateTime=上次拉取的最新更新时间毫秒时间戳，可选；lastId=上次拉取的最后一条记录 id，可选；limit=单次拉取条数，必填，@Min(1) @Max(200)）

**响应**: CommonResult\<List\<ImGroupRequestRespVO\>\>（字段见 3.7）

**业务逻辑**:
1. 查询当前用户担任群主 / 管理员的所有群集合；为空直接返回空列表。
2. 按 (lastUpdateTime, lastId) 游标增量拉取这些群下的申请。
3. 批量聚合申请人 / 邀请人昵称头像与群信息后返回。

### 3.6 查询指定群下的全部加群申请

- **路径**: GET /im/group-request/list-by-group
- **权限**: 已认证（群主 / 管理员）
- **说明**: 查询指定群下的全部加群申请（含已处理），按 id 倒序。

**请求参数**: 无（Query 参数 groupId=群编号，必填，@NotNull）

**响应**: CommonResult\<List\<ImGroupRequestRespVO\>\>（字段见 3.7）

**业务逻辑**:
1. 校验群存在 + 当前用户是该群有效成员且为群主 / 管理员，否则抛"仅群主或管理员可处理加群申请"。
2. 拉取该群下全部申请（含已处理），按 id 倒序，前端首条卡片化展示。
3. 批量聚合用户 / 群信息后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_001 | 群已被封禁 |
| 1_040_400_002 | 群已解散 |
| 1_040_500_001 | 您已不在该群中 |
| 1_040_510_003 | 仅群主或管理员可处理加群申请 |

### 3.7 按 id 单查申请记录

- **路径**: GET /im/group-request/get
- **权限**: 已认证（带越权过滤）
- **说明**: 按编号单查申请记录，WebSocket 通知到达后使用。

**请求参数**: 无（Query 参数 id=申请记录编号，必填）

**响应**: CommonResult\<ImGroupRequestRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 申请编号 |
| groupId | Long | 群编号 |
| userId | Long | 申请人 / 被邀请人用户编号 |
| inviterUserId | Long | 邀请人用户编号；NULL 表示用户主动申请 |
| handleResult | Integer | 处理结果（ImGroupRequestHandleResultEnum） |
| applyContent | String | 申请理由 |
| handleContent | String | 处理理由（拒绝时可选填） |
| handleUserId | Long | 处理人用户编号 |
| addSource | Integer | 加入来源（ImGroupAddSourceEnum） |
| handleTime | LocalDateTime | 处理时间 |
| createTime | LocalDateTime | 申请创建时间 |
| updateTime | LocalDateTime | 申请更新时间；增量拉取游标 |
| userNickname | String | 申请人 / 被邀请人昵称（聚合自 AdminUser） |
| userAvatar | String | 申请人 / 被邀请人头像（聚合自 AdminUser） |
| inviterNickname | String | 邀请人昵称（聚合自 AdminUser） |
| inviterAvatar | String | 邀请人头像（聚合自 AdminUser） |
| groupName | String | 群名称（聚合自 ImGroup） |
| groupAvatar | String | 群头像（聚合自 ImGroup） |

**业务逻辑**:
1. 按编号查询申请记录，查无返回 null。
2. 越权过滤：仅申请人 / 邀请人 / 该群群主 / 管理员可见，其余一律返回 null。
3. 聚合申请人 / 邀请人昵称头像与群名称 / 群头像后返回。

## 4. 群聊管理（ImGroupManagerController，平台管理端）

### 4.1 获得群分页

- **路径**: GET /im/manager/group/page
- **权限**: im:manager:group:query
- **说明**: 分页查询全平台群聊，附带群主昵称与活跃成员数。

**请求参数 (ImGroupManagerPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| name | String | 否 | 无 | 群名称，模糊匹配 |
| ownerUserId | Long | 否 | 无 | 群主用户编号 |
| status | Integer | 否 | 无 | 群状态（0 正常 / 1 已解散） |
| banned | Boolean | 否 | 无 | 是否封禁 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<ImGroupManagerRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 群编号 |
| name | String | 群名称 |
| avatar | String | 群头像 |
| notice | String | 群公告 |
| ownerUserId | Long | 群主用户编号 |
| ownerNickname | String | 群主昵称（聚合自 AdminUser） |
| memberCount | Integer | 群成员数量（活跃成员数） |
| status | Integer | 群状态（CommonStatusEnum） |
| dissolvedTime | LocalDateTime | 解散时间 |
| banned | Boolean | 是否封禁 |
| mutedAll | Boolean | 是否全群禁言 |
| bannedReason | String | 封禁原因 |
| bannedTime | LocalDateTime | 封禁时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按条件分页查询群。
2. 批量查询群主用户信息（昵称）与各群活跃成员数。
3. 转换 VO，填充群主昵称与群成员数量。

### 4.2 获得群详情

- **路径**: GET /im/manager/group/get
- **权限**: im:manager:group:query
- **说明**: 按编号获得群详情（不含成员数回填）。

**请求参数**: 无（Query 参数 id=群编号，必填）

**响应**: CommonResult\<ImGroupManagerRespVO\>（字段同 4.1）

**业务逻辑**:
1. 按编号查询群并转换为管理端 VO。

### 4.3 封禁群

- **路径**: PUT /im/manager/group/ban
- **权限**: im:manager:group:ban
- **说明**: 封禁指定群，需填写封禁原因。

**请求参数 (ImGroupManagerBanReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 群编号 |
| reason | String | 是 | @NotBlank、@Size(max=200) | 封禁原因 |

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在且未解散。
2. 幂等：已封禁直接返回，避免重复广播封禁通知。
3. 更新封禁状态（banned=true、封禁原因、封禁时间）。
4. 广播群封禁通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_002 | 群已解散 |

### 4.4 解封群

- **路径**: PUT /im/manager/group/unban
- **权限**: im:manager:group:ban
- **说明**: 解除指定群的封禁状态。

**请求参数**: 无（Query 参数 id=群编号，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在。
2. 更新 banned=false（保留 bannedReason / bannedTime 作为历史记录）。
3. 广播群解封通知给全员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |

### 4.5 解散群（管理端）

- **路径**: DELETE /im/manager/group/dissolve
- **权限**: im:manager:group:dissolve
- **说明**: 平台管理员强制解散指定群。

**请求参数**: 无（Query 参数 id=群编号，必填）

**响应**: CommonResult\<Boolean\>

**业务逻辑**:
1. 校验群存在且未解散。
2. 先广播 GROUP_DISSOLVE 通知，再更新群状态为已解散并记录解散时间，最后移除全部群成员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 群不存在 |
| 1_040_400_002 | 群已解散 |

## 5. 群成员管理（ImGroupMemberManagerController，平台管理端）

### 5.1 获得群成员列表

- **路径**: GET /im/manager/group/member/list
- **权限**: im:manager:group:query
- **说明**: 平台管理端按群查询全部成员（含已退群成员，由前端按需过滤）。

**请求参数**: 无（Query 参数 groupId=群编号，必填）

**响应**: CommonResult\<List\<ImGroupMemberManagerRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| nickname | String | 用户昵称（聚合自 AdminUser） |
| avatar | String | 用户头像（聚合自 AdminUser） |
| displayUserName | String | 组内显示名 |
| groupRemark | String | 群备注 |
| silent | Boolean | 是否免打扰 |
| status | Integer | 成员状态（CommonStatusEnum） |
| role | Integer | 成员角色（1=群主 2=管理员 3=普通成员） |
| joinTime | LocalDateTime | 入群时间 |
| quitTime | LocalDateTime | 退群时间 |
| muteEndTime | LocalDateTime | 禁言到期时间 |

**业务逻辑**:
1. 查询群全部成员（含已退群），为空直接返回空列表。
2. 批量查询用户信息并填充昵称 / 头像。

## 6. 加群申请管理（ImGroupRequestManagerController，平台管理端）

### 6.1 获得加群申请分页

- **路径**: GET /im/manager/group-request/page
- **权限**: im:manager:group-request:query
- **说明**: 分页审计全平台加群申请，附带申请人 / 邀请人 / 处理人昵称与群名称。

**请求参数 (ImGroupRequestManagerPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 继承 PageParam | 页码 |
| pageSize | Integer | 否 | 继承 PageParam | 每页条数 |
| groupId | Long | 否 | 无 | 群编号 |
| userId | Long | 否 | 无 | 申请人 / 被邀请人用户编号 |
| inviterUserId | Long | 否 | 无 | 邀请人用户编号 |
| handleResult | Integer | 否 | 无 | 处理结果（ImGroupRequestHandleResultEnum） |
| addSource | Integer | 否 | 无 | 加入来源（ImGroupAddSourceEnum） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<ImGroupRequestManagerRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| groupId | Long | 群编号 |
| groupName | String | 群名称（聚合自 ImGroup） |
| userId | Long | 申请人 / 被邀请人用户编号 |
| userNickname | String | 申请人 / 被邀请人昵称（聚合自 AdminUser） |
| inviterUserId | Long | 邀请人用户编号；NULL 表示用户主动申请 |
| inviterNickname | String | 邀请人昵称（聚合自 AdminUser） |
| applyContent | String | 申请理由 |
| addSource | Integer | 加入来源（ImGroupAddSourceEnum） |
| handleResult | Integer | 处理结果（ImGroupRequestHandleResultEnum） |
| handleUserId | Long | 处理人用户编号 |
| handleNickname | String | 处理人昵称（聚合自 AdminUser） |
| handleContent | String | 处理理由 |
| handleTime | LocalDateTime | 处理时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按条件分页查询加群申请。
2. 批量聚合申请人 / 邀请人 / 处理人用户昵称。
3. 批量聚合群信息（取群名）并填充后返回。
