# 会议室管理接口 (OaMeetingRoomController / OaMeetingRoomBookingController)

> 会议室管理：管理员维护会议室基础配置（负责人、设备、可预定范围、是否需审批）；用户以"草稿 → 提交（免审批直接通过 / 走 BPM 审批）→ 使用 → 完成"的流程预定会议室，支持时段冲突校验、取消、日程查询与开始前站内信提醒。

## 接口路径前缀

/oa/meeting-room  (Controller: OaMeetingRoomController)

/oa/meeting-room-booking  (Controller: OaMeetingRoomBookingController)

## 1. 会议室管理（OaMeetingRoomController）

### 1.1 创建会议室

- **路径**: POST /oa/meeting-room/create
- **权限**: oa:meeting-room:create
- **说明**: 创建会议室，校验负责人、设备字典与指定可预定成员。

**请求参数 (OaMeetingRoomSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（新增不传） |
| name | String | 是 | @NotBlank、@Size(max=100) | 会议室名称 |
| location | String | 是 | @NotBlank、@Size(max=255) | 位置 |
| type | Integer | 是 | @NotNull、@InEnum(OaMeetingRoomTypeEnum) | 会议室类型：1 内部会议室、2 外部会议室、3 培训室、4 多功能厅 |
| managerUserId | Long | 是 | @NotNull | 负责人用户编号 |
| status | Integer | 是 | @NotNull、@InEnum(OaMeetingRoomStatusEnum) | 可用状态：0 正常、1 维修中、2 不可用 |
| picUrl | String | 否 | @Size(max=1024) | 会议室图片 |
| seatCount | Integer | 否 | @Min(1) | 坐席数 |
| equipments | List&lt;Integer&gt; | 是 | @NotNull、元素 @NotNull | 设备列表（字典 MEETING_ROOM_EQUIPMENT） |
| allowBooking | Boolean | 是 | @NotNull | 允许预定 |
| needApproval | Boolean | 是 | @NotNull | 预定需审批 |
| bookingScope | Integer | 是 | @NotNull、@InEnum(OaMeetingRoomBookingScopeEnum) | 可预定范围：0 全部成员、1 指定成员 |
| bookingUserIds | List&lt;Long&gt; | 是 | @NotNull、元素 @NotNull | 可预定成员用户编号列表 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| remark | String | 否 | @Size(max=200) | 备注 |
| fileUrls | List&lt;String&gt; | 是 | @NotNull、元素 @NotBlank | 附件地址列表 |

**响应**: CommonResult&lt;Long&gt; —— 会议室编号。

**业务逻辑**:
1. 校验负责人用户有效。
2. 设备列表非空时，逐项校验 MEETING_ROOM_EQUIPMENT 字典值有效。
3. 可预定范围为"指定成员"时，校验可预定成员列表非空（否则报错），并校验成员用户全部有效。
4. 请求 VO 转换为 DO 并插入，返回会议室编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_002 | 指定成员不能为空 |

### 1.2 更新会议室

- **路径**: PUT /oa/meeting-room/update
- **权限**: oa:meeting-room:update
- **说明**: 更新会议室配置，校验逻辑与创建一致。

**请求参数 (OaMeetingRoomSaveReqVO)**: 同 [1.1 创建会议室](#11-创建会议室)，其中 `id` 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验会议室存在。
2. 校验负责人、设备字典与指定可预定成员（同创建）。
3. 按 id 更新会议室。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_002 | 指定成员不能为空 |

### 1.3 删除会议室

- **路径**: DELETE /oa/meeting-room/delete
- **权限**: oa:meeting-room:delete
- **说明**: 删除会议室，存在有效预约时禁止删除。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 会议室编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验会议室存在。
2. 校验该会议室没有仍有效的预约（结束时间晚于当前时间的预约），存在则报错。
3. 删除会议室。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_009 | 会议室存在有效预约，不能删除 |

### 1.4 获得会议室详情

- **路径**: GET /oa/meeting-room/get
- **权限**: oa:meeting-room:query
- **说明**: 获得会议室详情，附带负责人姓名与联系方式。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 会议室编号 |

**响应**: CommonResult&lt;OaMeetingRoomRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 会议室名称 |
| location | String | 位置 |
| type | Integer | 会议室类型 |
| managerUserId | Long | 负责人用户编号 |
| status | Integer | 可用状态 |
| picUrl | String | 会议室图片 |
| seatCount | Integer | 坐席数 |
| equipments | List&lt;Integer&gt; | 设备列表 |
| allowBooking | Boolean | 允许预定 |
| needApproval | Boolean | 预定需审批 |
| bookingScope | Integer | 可预定范围 |
| bookingUserIds | List&lt;Long&gt; | 可预定成员用户编号列表 |
| sort | Integer | 显示顺序 |
| remark | String | 备注 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| managerName | String | 负责人姓名 |
| managerPhone | String | 负责人联系方式 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验会议室存在。
2. 转换为 RespVO，查询负责人用户，拼接 managerName（昵称）与 managerPhone（手机号）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_000 | 会议室不存在 |

### 1.5 获得会议室分页

- **路径**: GET /oa/meeting-room/page
- **权限**: oa:meeting-room:query
- **说明**: 分页返回全部会议室，支持按名称、位置、类型、状态、负责人姓名筛选，附带负责人姓名与联系方式。

**请求参数 (OaMeetingRoomPageReqVO)**（继承 PageParam：pageNo、pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 会议室名称，模糊匹配 |
| location | String | 否 | - | 位置 |
| type | Integer | 否 | - | 会议室类型 |
| status | Integer | 否 | - | 可用状态 |
| managerName | String | 否 | - | 负责人姓名，按用户昵称模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;OaMeetingRoomRespVO&gt;&gt; —— 字段同 [1.4 获得会议室详情](#14-获得会议室详情)。

**业务逻辑**:
1. 传入 managerName 时，按昵称模糊查询匹配用户的 id 列表；无匹配用户时直接返回空分页。
2. 按 `OaMeetingRoomPageReqVO`（不限用户）分页查询会议室。
3. 批量查询负责人用户，拼接每条记录的 managerName 与 managerPhone。

### 1.6 获得可预定会议室分页

- **路径**: GET /oa/meeting-room/bookable-page
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 面向预定场景的分页，仅返回当前登录用户可预定的会议室（可预定范围为全部成员，或指定成员包含本人），响应只保留展示所需字段。

**请求参数 (OaMeetingRoomPageReqVO)**: 同 [1.5 获得会议室分页](#15-获得会议室分页)。

**响应**: CommonResult&lt;PageResult&lt;OaMeetingRoomRespVO&gt;&gt; —— 仅填充 id、name、location、type、status、seatCount、managerName 字段。

**业务逻辑**:
1. 传入 managerName 时按昵称模糊匹配用户，无匹配直接返回空分页。
2. 以当前登录用户 id 过滤，查询其可预定的会议室分页。
3. 响应仅保留 id、name、location、type、status、seatCount、managerName 字段。

## 2. 会议室预定（OaMeetingRoomBookingController）

### 2.1 创建会议室预定草稿

- **路径**: POST /oa/meeting-room-booking/create
- **权限**: oa:meeting-room-booking:create
- **说明**: 创建预定草稿，自动生成单号，初始状态为"未开始（草稿）"。

**请求参数 (OaMeetingRoomBookingSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 预定编号（草稿更新时必传） |
| roomId | Long | 是 | @NotNull | 会议室编号 |
| title | String | 是 | @NotBlank、@Size(max=200) | 会议主题 |
| startTime | LocalDateTime | 是 | @NotNull | 会议开始时间 |
| endTime | LocalDateTime | 是 | @NotNull | 会议结束时间 |
| moderatorUserId | Long | 是 | @NotNull | 主持人用户编号 |
| attendeeUserIds | List&lt;Long&gt; | 是 | @NotNull、元素 @NotNull | 参会人用户编号列表 |
| reminderType | Integer | 是 | @NotNull、@InEnum(OaMeetingRoomReminderTypeEnum) | 会议提醒：1 不提醒、2 提前 5 分钟、3 提前 10 分钟、4 提前 15 分钟、5 提前 30 分钟 |
| description | String | 否 | @Size(max=500) | 会议说明 |
| remark | String | 否 | @Size(max=500) | 申请备注 |
| fileUrls | List&lt;String&gt; | 是 | @NotNull、元素 @NotBlank | 附件地址列表 |

**响应**: CommonResult&lt;Long&gt; —— 预定编号。

**业务逻辑**:
1. 校验会议室存在、开始时间早于结束时间、主持人与参会人用户有效。
2. 校验申请人（当前登录用户）有效并取得其所属部门。
3. 通过 Redis 生成预定单号（前缀 MEETING_ROOM_BOOKING_NO_PREFIX），若单号已存在则报错。
4. 创建草稿：写入单号、reminded=false、申请人部门，审批状态置为未开始、使用状态置为待使用。
5. 插入预定记录并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_006 | 会议时间不正确 |
| 1_054_250_010 | 会议室预定单号已存在 |

### 2.2 更新会议室预定草稿

- **路径**: PUT /oa/meeting-room-booking/update
- **权限**: oa:meeting-room-booking:update
- **说明**: 更新本人未提交的预定草稿。

**请求参数 (OaMeetingRoomBookingSaveReqVO)**: 同 [2.1 创建会议室预定草稿](#21-创建会议室预定草稿)，其中 `id` 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验预定存在。
2. 校验预定归属（creator 为当前登录用户），否则报无权操作。
3. 校验审批状态仍为未开始（草稿），否则报状态不允许。
4. 校验会议室、时间与主持人和参会人有效（同创建）。
5. 按 id 更新草稿。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_003 | 会议室预定不存在 |
| 1_054_250_004 | 无权操作该会议室预定 |
| 1_054_250_005 | 当前预定状态不允许该操作 |
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_006 | 会议时间不正确 |

### 2.3 删除会议室预定草稿

- **路径**: DELETE /oa/meeting-room-booking/delete
- **权限**: oa:meeting-room-booking:delete
- **说明**: 删除本人未提交的预定草稿。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 预定编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验预定存在且归属当前登录用户。
2. 校验审批状态仍为未开始（草稿）。
3. 删除草稿记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_003 | 会议室预定不存在 |
| 1_054_250_004 | 无权操作该会议室预定 |
| 1_054_250_005 | 当前预定状态不允许该操作 |

### 2.4 获得会议室预定详情

- **路径**: GET /oa/meeting-room-booking/get
- **权限**: oa:meeting-room-booking:query
- **说明**: 获得预定详情，附带会议室、主持人、申请人、参会人、部门等展示字段。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 预定编号 |

**响应**: CommonResult&lt;OaMeetingRoomBookingRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 预定编号 |
| roomId | Long | 会议室编号 |
| title | String | 会议主题 |
| startTime | LocalDateTime | 会议开始时间 |
| endTime | LocalDateTime | 会议结束时间 |
| moderatorUserId | Long | 主持人用户编号 |
| attendeeUserIds | List&lt;Long&gt; | 参会人用户编号列表 |
| reminderType | Integer | 会议提醒 |
| description | String | 会议说明 |
| remark | String | 申请备注 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| no | String | 申请单号 |
| roomName | String | 会议室名称 |
| roomLocation | String | 位置 |
| roomType | Integer | 会议室类型 |
| moderatorName | String | 主持人姓名 |
| attendeeNames | List&lt;String&gt; | 参会人姓名列表 |
| creatorName | String | 申请人 |
| deptId | Long | 申请部门编号 |
| deptName | String | 部门名称 |
| status | Integer | 审批状态：-1 未开始（草稿）、1 审批中、2 审批通过、3 审批不通过、4 已取消 |
| useStatus | Integer | 使用状态：0 待使用、1 使用中、2 已完成、3 已取消 |
| needApproval | Boolean | 提交时是否需要审批 |
| processInstanceId | String | 流程实例编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询预定记录（不存在时返回空）。
2. 批量查询主持人、申请人（creator）与参会人用户，拼接 moderatorName、creatorName 与 attendeeNames（用户缺失时回退为用户编号字符串）。
3. 批量查询会议室，拼接 roomName、roomLocation、roomType；查询申请部门，拼接 deptName。

### 2.5 获得本人的会议室预定分页

- **路径**: GET /oa/meeting-room-booking/page
- **权限**: oa:meeting-room-booking:query
- **说明**: 分页返回当前登录用户（creator）的预定列表，支持单号、会议室名称、主题、主持人姓名、部门、状态、时间等筛选。

**请求参数 (OaMeetingRoomBookingPageReqVO)**（继承 PageParam：pageNo、pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| no | String | 否 | - | 单据编号 |
| roomName | String | 否 | - | 会议室名称 |
| title | String | 否 | - | 会议主题 |
| moderatorName | String | 否 | - | 主持人姓名 |
| deptId | Long | 否 | - | 申请部门编号 |
| status | Integer | 否 | - | 审批状态 |
| useStatus | Integer | 否 | - | 使用状态 |
| startTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 会议开始时间范围 |
| endTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 会议结束时间范围 |
| creator | String | 否 | - | 创建人编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult&lt;PageResult&lt;OaMeetingRoomBookingRespVO&gt;&gt; —— 字段同 [2.4 获得会议室预定详情](#24-获得会议室预定详情)。

**业务逻辑**:
1. 传入 roomName 时按名称查询会议室 id 列表，无匹配直接返回空分页。
2. 传入 moderatorName 时按昵称查询主持人用户 id 列表，无匹配直接返回空分页。
3. 以当前登录用户为 creator 分页查询本人预定，并拼接展示字段（同详情）。

### 2.6 提交会议室预定

- **路径**: PUT /oa/meeting-room-booking/submit
- **权限**: oa:meeting-room-booking:create
- **说明**: 提交草稿进入审批：免审批的会议室直接置为审批通过；需审批的发起 BPM 流程。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 预定编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验预定与所约会议室存在。
2. 校验预定归属本人且仍为草稿状态，阻止重复提交。
3. 校验会议室可预定：allowBooking 为 true、可用状态正常，且指定成员范围时当前用户在可预定成员列表内。
4. 重新校验时间与人员有效，且开始时间必须晚于当前时间。
5. 检查该会议室在预定时段内（左闭右开区间，相邻会议不冲突）无其他有效预约，存在冲突则报错。
6. 按会议室 needApproval 更新审批状态：免审批直接置为审批通过；需审批则置为审批中，发起 BPM 审批流程（流程 key 为 MEETING_ROOM_BOOKING）并回写流程实例编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_003 | 会议室预定不存在 |
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_004 | 无权操作该会议室预定 |
| 1_054_250_005 | 当前预定状态不允许该操作 |
| 1_054_250_001 | 会议室当前不可预定 |
| 1_054_250_006 | 会议时间不正确 |
| 1_054_250_007 | 会议室在该时段已被预定 |

### 2.7 取消会议室预定

- **路径**: PUT /oa/meeting-room-booking/cancel
- **权限**: oa:meeting-room-booking:update
- **说明**: 申请人取消本人的预定：审批中取消 BPM 流程；已通过且待使用时仅取消使用状态。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 预定编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验预定存在且归属当前登录用户。
2. 审批状态为审批中时，取消对应 BPM 流程实例（理由"申请人取消会议室预定"），结束。
3. 审批通过且使用状态为待使用时，使用状态置为已取消，保留审批结果，结束。
4. 其余状态不允许取消，报状态错误。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_003 | 会议室预定不存在 |
| 1_054_250_004 | 无权操作该会议室预定 |
| 1_054_250_005 | 当前预定状态不允许该操作 |

### 2.8 开始使用会议室预定

- **路径**: PUT /oa/meeting-room-booking/start
- **权限**: oa:meeting-room-booking:update
- **说明**: 会议开始后由申请人或主持人将预定置为使用中。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 预定编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验预定存在，且操作人为申请人（creator）或主持人。
2. 校验审批通过、使用状态为待使用，且当前时间处于 [开始时间, 结束时间) 区间内。
3. 开始前再次校验会议室仍可用（allowBooking 且状态正常），避免审批期间被停用或维修。
4. 使用状态置为使用中。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_003 | 会议室预定不存在 |
| 1_054_250_004 | 无权操作该会议室预定 |
| 1_054_250_005 | 当前预定状态不允许该操作 |
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_001 | 会议室当前不可预定 |

### 2.9 完成使用会议室预定

- **路径**: PUT /oa/meeting-room-booking/finish
- **权限**: oa:meeting-room-booking:update
- **说明**: 由申请人或主持人将使用中的预定置为已完成。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 预定编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验预定存在，且操作人为申请人（creator）或主持人。
2. 校验审批通过且使用状态为使用中，否则报状态错误。
3. 使用状态置为已完成。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_003 | 会议室预定不存在 |
| 1_054_250_004 | 无权操作该会议室预定 |
| 1_054_250_005 | 当前预定状态不允许该操作 |

### 2.10 获得会议室日程

- **路径**: GET /oa/meeting-room-booking/schedule
- **权限**: oa:meeting-room:query 或 oa:meeting-room-booking:query（@PreAuthorize hasAnyPermissions）
- **说明**: 查询指定会议室在某时间段内占用（相交）的全部预约，用于日历展示。

**请求参数 (OaMeetingRoomBookingScheduleReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| roomId | Long | 是 | @NotNull | 会议室编号 |
| startTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 查询开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 查询结束时间 |

**响应**: CommonResult&lt;List&lt;OaMeetingRoomBookingRespVO&gt;&gt; —— 字段同 [2.4 获得会议室预定详情](#24-获得会议室预定详情)。

**业务逻辑**:
1. 校验会议室存在。
2. 校验查询区间开始时间早于结束时间。
3. 查询与该区间相交的预约列表，并拼接会议室、人员、部门等展示字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_250_000 | 会议室不存在 |
| 1_054_250_006 | 会议时间不正确 |
