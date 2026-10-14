# 好友与申请接口 (ImFriendController / ImFriendRequestController / ImFriendManagerController / ImFriendRequestManagerController)

> 提供 IM 好友关系的查询与维护（列表/详情/备注/免打扰/置顶/拉黑/删除）、好友申请的全生命周期（发起/同意/拒绝/列表/增量拉取），以及管理后台的好友关系与申请分页查询。

## 接口路径前缀

- /im/friend  (Controller: ImFriendController)
- /im/friend-request  (Controller: ImFriendRequestController)
- /im/manager/friend  (Controller: ImFriendManagerController)
- /im/manager/friend-request  (Controller: ImFriendRequestManagerController)

---

## 1. 好友关系（ImFriendController，/im/friend）

> 面向当前登录用户的好友关系接口，所有操作均以登录用户为「我方」视角，单边生效。好友关系为双向记录（im_friend 每人各一条），状态判断要求双方记录均为 ENABLE。

### 1.1 获得当前登录用户的好友列表

- **路径**: GET /im/friend/list
- **权限**: 已认证
- **说明**: 返回当前登录用户的全部好友关系列表，并聚合好友昵称/头像及拼音（供前端字母分桶与拼音搜索）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ImFriendRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 关系记录编号 |
| friendUserId | Long | 好友的用户编号 |
| silent | Boolean | 是否免打扰 |
| displayName | String | 好友展示备注（仅自己可见） |
| displayNamePinyin | String | 好友展示备注的拼音（小写无空格，服务端计算） |
| addSource | Integer | 添加来源（1=搜索 2=群聊 3=扫码 4=名片） |
| pinned | Boolean | 是否置顶联系人 |
| blocked | Boolean | 是否拉黑（仅自己可见） |
| status | Integer | 好友状态（CommonStatusEnum：0=开启 1=禁用） |
| addTime | LocalDateTime | 添加好友时间 |
| deleteTime | LocalDateTime | 删除好友时间 |
| updateTime | LocalDateTime | 最近更新时间（增量拉取游标用） |
| nickname | String | 好友昵称（实时聚合自 AdminUser） |
| nicknamePinyin | String | 好友昵称的拼音（小写无空格，服务端计算） |
| avatar | String | 好友头像（实时聚合自 AdminUser） |

**业务逻辑**:
1. 以当前登录用户编号为 userId，调用 Mapper 查询其好友关系列表。
2. 批量调用 AdminUserApi 聚合好友的昵称/头像，避免 N+1 查询。
3. DO 转 ImFriendRespVO，并计算 displayName / nickname 的小写拼音填充 displayNamePinyin / nicknamePinyin。

### 1.2 增量拉取当前用户的好友关系（重连 / 离线补偿）

- **路径**: GET /im/friend/pull
- **权限**: 已认证
- **说明**: 按 (updateTime, id) 游标增量拉取当前用户的好友关系变更，用于重连或离线补偿场景。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| lastUpdateTime | Long | 否 | - | 上次拉取到的最新更新时间（毫秒时间戳）；首次拉取不传 |
| lastId | Long | 否 | - | 上次拉取到的最后一条记录 id；首次拉取不传 |
| limit | Integer | 是 | @Min(1)、@Max(200) | 单次拉取条数 |

**响应**: CommonResult&lt;List&lt;ImFriendRespVO&gt;&gt;，字段同 1.1 的 ImFriendRespVO。

**业务逻辑**:
1. 以当前登录用户为视角，按 (lastUpdateTime, lastId) 游标 + limit 限制调用 Mapper 增量查询好友关系。
2. 复用与 1.1 相同的 VO 组装逻辑（聚合昵称/头像 + 拼音）后返回。

### 1.3 获得好友详情

- **路径**: GET /im/friend/get
- **权限**: 已认证
- **说明**: 按好友用户编号单查当前用户视角的一条好友关系。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| friendUserId | Long | 是 | @RequestParam 默认必填 | 好友的用户编号 |

**响应**: CommonResult&lt;ImFriendRespVO&gt;，字段同 1.1 的 ImFriendRespVO（记录不存在时 data 为 null）。

**业务逻辑**:
1. 按 (当前登录用户, friendUserId) 查询单条好友关系记录。
2. 记录存在时复用列表 VO 组装逻辑返回，不存在时返回 null。

### 1.4 删除好友（单向软删除）

- **路径**: DELETE /im/friend/delete
- **权限**: 已认证
- **说明**: 仅删除「我方」视角的好友关系（状态置 DISABLE），对方不感知；可选级联清理本端会话数据。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| friendUserId | Long | 是 | @NotNull | 好友的用户编号 |
| clear | Boolean | 否 | - | 是否级联清理本端相关数据（如私聊会话），透传给前端多端 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 单边软删：仅将当前用户视角的关系记录状态置 DISABLE 并记录删除时间；对方视角记录不动（记录不存在或已禁用时直接结束）。
2. 通过私聊消息通道发送 FRIEND_DELETE 通知（persistent=false 不入库），仅推送当前用户的多端，对方完全不感知。
3. clear=false 时前端渲染「你已删除好友」的瞬时会话气泡；clear=true 时前端直接清理会话、跳过气泡。
4. 通过 @Caching 注解双向失效 FRIEND_STATE 好友状态缓存。

### 1.5 更新好友单边属性（备注 / 免打扰 / 联系人置顶）

- **路径**: PUT /im/friend/update
- **权限**: 已认证
- **说明**: 更新仅自己可见的好友属性，未传字段表示不修改。

**请求参数 (ImFriendUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| friendUserId | Long | 是 | @NotNull | 好友的用户编号 |
| silent | Boolean | 否 | - | 是否免打扰；不传表示不修改 |
| displayName | String | 否 | @Size(max=16) | 好友展示备注（仅自己可见）；不传表示不修改，传空串表示清空 |
| pinned | Boolean | 否 | - | 是否置顶联系人；不传表示不修改 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验至少修改一个字段，三个可变字段全为 null 时直接结束。
2. 校验当前用户与目标存在启用状态的好友关系，否则抛出 FRIEND_NOT_FRIEND。
3. 按记录 id 更新备注/免打扰/置顶属性。
4. 推送 FRIEND_UPDATE 通知给当前用户的多端（所有单边属性变更合并为单条通知，避免多通知顺序竞争）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_040_600_001 | 对方不是您的好友 |

### 1.6 拉黑好友（必须先是好友；单边屏蔽对方私聊消息）

- **路径**: PUT /im/friend/block
- **权限**: 已认证
- **说明**: 将好友加入黑名单，单边生效；已拉黑时幂等返回。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| friendUserId | Long | 是 | @NotNull | 好友的用户编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验当前用户与目标存在启用状态的好友关系，否则抛出 FRIEND_NOT_FRIEND。
2. 已拉黑时直接返回（幂等）。
3. 单边更新 blocked=true。
4. 推送 FRIEND_BLOCK 通知给当前用户的多端，并双向失效 FRIEND_STATE 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_040_600_001 | 对方不是您的好友 |

### 1.7 移出黑名单

- **路径**: PUT /im/friend/unblock
- **权限**: 已认证
- **说明**: 将好友移出黑名单；未拉黑时直接报错。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| friendUserId | Long | 是 | @NotNull | 好友的用户编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验当前用户与目标存在启用状态的好友关系，否则抛出 FRIEND_NOT_FRIEND。
2. 未拉黑时抛出 FRIEND_NOT_BLOCKED。
3. 单边更新 blocked=false。
4. 推送 FRIEND_UNBLOCK 通知给当前用户的多端，并双向失效 FRIEND_STATE 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_040_600_001 | 对方不是您的好友 |
| 1_040_600_003 | 对方未在黑名单中 |

---

## 2. 好友申请（ImFriendRequestController，/im/friend-request）

> 面向当前登录用户的好友申请接口，覆盖发起、同意、拒绝与查询；同一 (发起方, 接收方) 仅保留一条申请记录，重复申请覆盖内容并重置为未处理。

### 2.1 发起好友申请

- **路径**: POST /im/friend-request/apply
- **权限**: 已认证
- **说明**: 向目标用户发起好友申请；存在单向好友关系时静默恢复，开启自动通过时事务提交后自动同意。

**请求参数 (ImFriendRequestApplyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| toUserId | Long | 是 | @NotNull | 接收方用户编号 |
| applyContent | String | 否 | @Size(max=255) | 申请理由 |
| displayName | String | 否 | @Size(max=16) | 对接收方的备注（仅自己可见，同意后写入我侧关系） |
| addSource | Integer | 否 | @InEnum(ImFriendAddSourceEnum) | 添加来源（1=搜索 2=群聊 3=扫码 4=名片） |

**响应**: CommonResult&lt;Long&gt;，申请记录编号；走单向好友静默恢复路径时返回 null（不产生申请）。

**业务逻辑**:
1. 校验不能添加自己为好友（FRIEND_ADD_SELF），并校验对方用户存在且启用。
2. 读取双向好友状态：已是好友抛 FRIEND_REQUEST_ALREADY_FRIEND，被对方拉黑抛 FRIEND_REQUEST_BLOCKED_BY_PEER。
3. 单向好友场景（我方记录已删、对方仍把我当好友）：对方已拉黑则抛 FRIEND_REQUEST_BLOCKED_BY_PEER；否则静默恢复我侧好友关系（silentReAddFriend，对方无感知）并返回 null。
4. 落库创建或重置申请：同一 (fromUserId, toUserId) 唯一，无旧记录则插入（唯一键冲突时回查复用并发写入的记录），有旧记录则覆盖申请内容并重置为未处理。
5. 推送 FRIEND_REQUEST_RECEIVED 通知给接收方多端，payload 携带申请方昵称/头像。
6. 若开启 im.friend.auto-accept 全局自动通过开关，注册 afterCommit 回调，在事务提交后自动执行同意流程（异常兜底记录日志，不阻断）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_040_600_002 | 不允许添加自己为好友 |
| 1_040_610_005 | 您已是 TA 的好友，无需重复添加 |
| 1_040_610_006 | 您已被对方拉入黑名单，无法添加为好友 |

### 2.2 同意好友申请

- **路径**: PUT /im/friend-request/agree
- **权限**: 已认证
- **说明**: 接收方同意好友申请，双方建立好友关系并发送「你们已成为好友」会话消息。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 申请编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验申请存在、未处理、操作人是接收方，否则分别抛出 FRIEND_REQUEST_NOT_EXISTS / FRIEND_REQUEST_NOT_TO_ME / FRIEND_REQUEST_HANDLED。
2. 以乐观锁（handleResult=UNHANDLED 条件更新）将申请置为 AGREED 并记录处理时间；更新影响行数为 0 时抛 FRIEND_REQUEST_HANDLED（并发兜底）。
3. 调用 becomeFriends 双向建立好友关系：发起方带申请中的备注/添加来源，接收方备注为空；内部 addFriend0 幂等处理「已启用跳过 / 禁用恢复 / 不存在插入」三种情况，并发送 FRIEND_ADD 私聊消息入库（双方拉历史均可见「你们已成为好友」会话气泡），并双向失效 FRIEND_STATE 缓存。
4. 推送 FRIEND_REQUEST_APPROVED 通知给发起方多端。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_040_610_001 | 好友申请不存在 |
| 1_040_610_002 | 好友申请已处理 |
| 1_040_610_003 | 不能处理别人的好友申请 |

### 2.3 拒绝好友申请

- **路径**: PUT /im/friend-request/refuse
- **权限**: 已认证
- **说明**: 接收方拒绝好友申请，可选填处理理由。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 申请编号 |
| handleContent | String | 否 | @Size(max=255) | 处理理由（最多 255 个字符） |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验申请存在、未处理、操作人是接收方（fail-fast，并发场景由乐观锁兜底）。
2. 以乐观锁将申请置为 REFUSED 并记录处理理由与处理时间；更新影响行数为 0 时抛 FRIEND_REQUEST_HANDLED。
3. 推送 FRIEND_REQUEST_REJECTED 通知给发起方多端，payload 携带处理理由。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_040_610_001 | 好友申请不存在 |
| 1_040_610_002 | 好友申请已处理 |
| 1_040_610_003 | 不能处理别人的好友申请 |

### 2.4 查询「我相关」的好友申请列表（游标分页：传 maxId 加载更多）

- **路径**: GET /im/friend-request/list
- **权限**: 已认证
- **说明**: 查询发起方或接收方为当前用户的申请记录，按 maxId 游标分页加载。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| maxId | Long | 否 | - | 当前列表最旧记录的 id；首页不传 |
| limit | Integer | 是 | @Min(1)、@Max(200) | 单次拉取条数 |

**响应**: CommonResult&lt;List&lt;ImFriendRequestRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 申请编号 |
| fromUserId | Long | 发起方用户编号 |
| toUserId | Long | 接收方用户编号 |
| handleResult | Integer | 处理结果（0=未处理 1=同意 2=拒绝） |
| applyContent | String | 申请理由 |
| handleContent | String | 处理理由（接收方拒绝时可选填） |
| addSource | Integer | 添加来源（1=搜索 2=群聊 3=扫码 4=名片） |
| handleTime | LocalDateTime | 处理时间 |
| createTime | LocalDateTime | 申请创建时间 |
| updateTime | LocalDateTime | 最近更新时间（增量拉取游标用） |
| fromNickname | String | 发起方昵称（实时聚合自 AdminUser） |
| fromAvatar | String | 发起方头像（实时聚合自 AdminUser） |
| toNickname | String | 接收方昵称（实时聚合自 AdminUser） |
| toAvatar | String | 接收方头像（实时聚合自 AdminUser） |

**业务逻辑**:
1. 传 maxId 时先按 id 查询该记录，记录不存在则返回空列表。
2. 以 maxId 记录的 updateTime + id 为游标，查询发起方或接收方为当前用户的申请列表。
3. 批量聚合发起方/接收方双方用户的昵称/头像后返回。

### 2.5 增量拉取「我相关」的好友申请（重连 / 离线补偿）

- **路径**: GET /im/friend-request/pull
- **权限**: 已认证
- **说明**: 按 (updateTime, id) 游标增量拉取与当前用户相关的申请变更。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| lastUpdateTime | Long | 否 | - | 上次拉取到的最新更新时间（毫秒时间戳）；首次拉取不传 |
| lastId | Long | 否 | - | 上次拉取到的最后一条记录 id；首次拉取不传 |
| limit | Integer | 是 | @Min(1)、@Max(200) | 单次拉取条数 |

**响应**: CommonResult&lt;List&lt;ImFriendRequestRespVO&gt;&gt;，字段同 2.4 的 ImFriendRequestRespVO。

**业务逻辑**:
1. 以当前登录用户为视角，按 (lastUpdateTime, lastId) 游标 + limit 限制调用 Mapper 增量查询相关申请。
2. 复用与 2.4 相同的 VO 组装逻辑（聚合双方昵称/头像）后返回。

### 2.6 按 id 单查「我相关」的申请记录

- **路径**: GET /im/friend-request/get
- **权限**: 已认证
- **说明**: WebSocket 通知到达后按 id 单查申请详情，带越权过滤。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @RequestParam 默认必填 | 申请记录编号 |

**响应**: CommonResult&lt;ImFriendRequestRespVO&gt;，字段同 2.4 的 ImFriendRequestRespVO（无权限或不存在时 data 为 null）。

**业务逻辑**:
1. 按 id 查询申请记录。
2. 越权过滤：发起方与接收方必有一方是当前用户，否则当不存在返回 null。
3. 记录通过校验时复用列表 VO 组装逻辑返回。

---

## 3. 好友管理（ImFriendManagerController，/im/manager/friend）

> 管理后台的好友关系查询接口，面向管理员，不区分视角地展示双向关系记录。

### 3.1 获得好友关系分页

- **路径**: GET /im/manager/friend/page
- **权限**: im:manager:friend:query
- **说明**: 按条件分页查询全站好友关系记录，聚合双方昵称。

**请求参数 (ImFriendManagerPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数 |
| userId | Long | 否 | - | 用户编号 |
| friendUserId | Long | 否 | - | 好友用户编号 |
| status | Integer | 否 | - | 好友状态（CommonStatusEnum：0=开启 1=禁用） |
| silent | Boolean | 否 | - | 是否免打扰 |
| addTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 添加好友时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ImFriendManagerRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| userNickname | String | 用户昵称（实时聚合自 AdminUser） |
| friendUserId | Long | 好友用户编号 |
| friendNickname | String | 好友昵称（实时聚合自 AdminUser） |
| displayName | String | 好友展示备注 |
| addSource | Integer | 添加来源（1=搜索 2=群聊 3=扫码 4=名片） |
| silent | Boolean | 是否免打扰 |
| pinned | Boolean | 是否置顶联系人 |
| blocked | Boolean | 是否拉黑 |
| status | Integer | 好友状态（CommonStatusEnum：0=开启 1=禁用） |
| addTime | LocalDateTime | 添加好友时间 |
| deleteTime | LocalDateTime | 删除好友时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按条件分页查询好友关系记录。
2. 结果为空时直接返回空分页（保留 total）。
3. 一次性批量查询记录中「用户 + 好友」两组用户编号的昵称，转换为 VO 并填充 userNickname / friendNickname。

---

## 4. 好友申请管理（ImFriendRequestManagerController，/im/manager/friend-request）

> 管理后台的好友申请查询接口，面向管理员展示全部申请记录。

### 4.1 获得好友申请分页

- **路径**: GET /im/manager/friend-request/page
- **权限**: im:manager:friend-request:query
- **说明**: 按条件分页查询全站好友申请记录，聚合双方昵称。

**请求参数 (ImFriendRequestManagerPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数 |
| fromUserId | Long | 否 | - | 发起方用户编号 |
| toUserId | Long | 否 | - | 接收方用户编号 |
| handleResult | Integer | 否 | - | 处理结果（0=未处理 1=同意 2=拒绝） |
| addSource | Integer | 否 | - | 添加来源（1=搜索 2=群聊 3=扫码 4=名片） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ImFriendRequestManagerRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| fromUserId | Long | 发起方用户编号 |
| fromNickname | String | 发起方昵称（实时聚合自 AdminUser） |
| toUserId | Long | 接收方用户编号 |
| toNickname | String | 接收方昵称（实时聚合自 AdminUser） |
| applyContent | String | 申请理由 |
| displayName | String | 发起方对接收方的备注 |
| addSource | Integer | 添加来源（1=搜索 2=群聊 3=扫码 4=名片） |
| handleResult | Integer | 处理结果（0=未处理 1=同意 2=拒绝） |
| handleContent | String | 处理理由 |
| handleTime | LocalDateTime | 处理时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按条件分页查询好友申请记录。
2. 结果为空时直接返回空分页（保留 total）。
3. 一次性批量查询记录中「发起方 + 接收方」两组用户编号的昵称，转换为 VO 并填充 fromNickname / toNickname。
