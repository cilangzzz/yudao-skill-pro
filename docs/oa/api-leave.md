# 请假申请接口 (OaLeaveApplyController)

> 提供个人请假申请的草稿创建/更新、提交发起 BPM 审批流程，以及本人申请的分页与详情查询；审批状态由 BPM 流程回调更新，审批通过后自动生成考勤明细。

## 接口路径前缀

/oa/leave-apply  (Controller: OaLeaveApplyController)

## 1. 草稿与提交

### 1.1 创建请假申请草稿

- **路径**: POST /oa/leave-apply/create
- **权限**: oa:leave-apply:create
- **说明**: 根据请假信息计算天数并校验单次天数上限后，保存一条状态为「未开始」的请假申请草稿。

**请求参数 (OaLeaveApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 申请编号（创建时不传，由后端生成） |
| title | String | 是 | @NotBlank、@Size(max = 255) | 标题，不能超过 255 个字符 |
| urgency | Integer | 是 | @NotNull、@InDict(APPLY_URGENCY) | 紧急程度，字典 `oa_apply_urgency` |
| type | Integer | 是 | @NotNull、@InDict(LEAVE_TYPE) | 请假类型，字典 `oa_leave_type`（1 年假、2 事假、3 病假、4 婚假、5 产假及哺乳假、6 陪产假、7 丧假） |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间（时间戳毫秒） |
| endTime | LocalDateTime | 是 | @NotNull | 结束时间（时间戳毫秒），不能早于开始时间（@AssertTrue isTimeRangeValid） |
| reason | String | 是 | @NotBlank、@Size(max = 5000) | 申请原因，不能超过 5000 个字符 |
| fileUrls | List\<String\> | 否 | @Size(max = 5)，元素 @NotBlank、@Size(max = 1024) | 附件地址列表，最多 5 个，单个地址不超过 1024 字符 |

**响应**: CommonResult\<Long\>，返回新建请假申请的编号。

**业务逻辑**:
1. 通过 `LocalDateTimeUtils.getDaysBetweenCeiling` 计算开始时间到结束时间的请假天数（向上取整）。
2. 调用 `validateLeaveApplyDays` 按 `OaLeaveTypeEnum` 校验单次请假天数是否超过该类型上限（事假 4 天、婚假 10 天、陪产假 10 天，其余类型不限；不校验年度累计额度），超限抛出 `LEAVE_APPLY_DAYS_EXCEEDED`。
3. 将 ReqVO 转换为 `OaLeaveApplyDO`，清空 id，状态置为 BPM 流程实例状态「未开始」（-1），写入计算出的天数。
4. 插入数据库保存草稿，返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_005 | 单次{}不能超过 {} 天（如：单次事假不能超过 4 天） |

### 1.2 更新请假申请草稿

- **路径**: PUT /oa/leave-apply/update
- **权限**: oa:leave-apply:create
- **说明**: 修改本人尚未提交的请假申请草稿（重算请假天数并校验）。

**请求参数 (OaLeaveApplySaveReqVO)**: 与「创建请假申请草稿」相同（`id` 此时为必传业务字段，无校验注解，用于定位要更新的记录）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 调用 `validateLeaveApplyEditable` 校验申请可修改：申请必须存在（否则 `APPLY_NOT_EXISTS`）、归属当前登录用户（否则 `APPLY_ACCESS_DENIED`）、状态为「未开始」草稿（否则 `APPLY_STATUS_INVALID`）。
2. 重新计算开始/结束时间区间的请假天数（向上取整）。
3. 按请假类型校验单次天数上限，超限抛出 `LEAVE_APPLY_DAYS_EXCEEDED`。
4. 转换为 DO（含新天数）后按 id 更新申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |
| 1_054_280_005 | 单次{}不能超过 {} 天 |

### 1.3 提交请假申请

- **路径**: POST /oa/leave-apply/submit
- **权限**: oa:leave-apply:create
- **说明**: 将本人「未开始」的请假草稿提交，发起 BPM 请假审批流程并绑定流程实例编号。

**请求参数 (OaLeaveApplySubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 申请编号 |
| startUserSelectAssignees | Map\<String, List\<Long\>\> | 否 | 无 | 发起人自选审批人：任务节点 Key → 候选人用户编号列表 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 调用 `validateLeaveApplyEditable` 校验申请可提交：存在、本人归属、状态为「未开始」草稿，并返回该申请。
2. 按草稿已有的请假类型和天数再次校验单次天数上限。
3. 将申请状态更新为「审批中」（BPM RUNNING = 1）。
4. 通过 `BpmProcessInstanceApi.createProcessInstance` 以流程定义 Key `BpmModelConstants.LEAVE_APPLY` 发起流程，业务 Key 为申请编号，流程变量携带 `days`（请假天数），并传入发起人自选审批人 `startUserSelectAssignees`。
5. 将返回的流程实例编号 `processInstanceId` 回写到请假申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |
| 1_054_280_005 | 单次{}不能超过 {} 天 |

## 2. 查询

### 2.1 获得本人请假申请分页

- **路径**: GET /oa/leave-apply/page
- **权限**: oa:leave-apply:query
- **说明**: 分页查询当前登录用户本人的请假申请，拼接申请人昵称。

**请求参数 (OaLeaveApplyPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull | 页码，从 1 开始（继承 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Max(200) | 每页条数，最大 200（继承 PageParam，默认 10） |
| title | String | 否 | 无 | 标题，模糊匹配 |
| status | Integer | 否 | 无 | 审批状态（-1 未开始、1 审批中、2 审批通过、3 审批不通过、4 已取消） |

**响应**: CommonResult\<PageResult\<OaLeaveApplyRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| title | String | 标题 |
| urgency | Integer | 紧急程度 |
| type | Integer | 请假类型（1 年假、2 事假、3 病假、4 婚假、5 产假及哺乳假、6 陪产假、7 丧假） |
| startTime | LocalDateTime | 开始时间（时间戳毫秒） |
| endTime | LocalDateTime | 结束时间（时间戳毫秒） |
| days | Integer | 请假天数（向上取整） |
| reason | String | 申请原因 |
| status | Integer | 审批状态（-1 未开始、1 审批中、2 审批通过、3 审批不通过、4 已取消） |
| processInstanceId | String | BPM 流程实例编号 |
| fileUrls | List\<String\> | 附件地址列表 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人昵称（根据 creator 批量查询系统用户拼接） |
| createTime | LocalDateTime | 申请时间（时间戳毫秒） |

**业务逻辑**:
1. 以当前登录用户编号作为 `creator` 条件执行分页查询，仅返回本人的申请。
2. 收集分页结果中的申请人编号集合，通过 `AdminUserApi.getUserMap` 批量查询用户。
3. 将 `OaLeaveApplyDO` 转换为 `OaLeaveApplyRespVO`，并回填申请人昵称 `creatorName`。
4. 组装 `PageResult` 返回列表与总数。

### 2.2 获得请假申请详情

- **路径**: GET /oa/leave-apply/get
- **权限**: oa:leave-apply:query
- **说明**: 按编号查询单条请假申请详情，拼接申请人昵称。

**请求参数**: 无（Query 参数）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 申请编号（@RequestParam） |

**响应**: CommonResult\<OaLeaveApplyRespVO\>，字段同「获得本人请假申请分页」的响应表。

**业务逻辑**:
1. 按 id 调用 `leaveApplyMapper.selectById` 查询申请记录，不存在时返回 null。
2. 复用分页接口的 VO 拼接逻辑：批量查询申请人用户信息。
3. 转换为 `OaLeaveApplyRespVO` 并回填申请人昵称后返回。

## 附：审批状态回调（内部接口说明）

`updateLeaveApplyStatus(id, status)` 由 BPM 流程监听器调用（非本 Controller 的 admin 端点）：校验申请存在后更新审批状态；当状态变更为「审批通过」时，调用 `OaAttendanceService.createApplyAttendance` 为申请人按请假开始时间生成「请假」类型考勤明细。

## 附：错误码汇总（流程申请段 1-054-280-000）

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |
| 1_054_280_005 | 单次{}不能超过 {} 天（按请假类型上限：事假 4 天、婚假 10 天、陪产假 10 天） |
