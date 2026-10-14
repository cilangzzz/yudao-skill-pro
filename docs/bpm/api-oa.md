# OA 请假示例接口 (BpmOALeaveController)

> OA 请假申请是「自己存储业务数据 + 接入 BPM 工作流」的演示示例：请假单落库到 `bpm_oa_leave` 表，同时以流程定义 Key `oa_leave` 发起流程实例，通过流程实例状态事件监听器回写审批结果。

## 接口路径前缀

/bpm/oa/leave  (Controller: BpmOALeaveController)

## 1. 请假申请管理

### 1.1 创建请假申请

- **路径**: POST /bpm/oa/leave/create
- **权限**: bpm:oa-leave:create
- **说明**: 创建请假单并同步发起 `oa_leave` 流程实例，返回请假单编号。

**请求参数 (BpmOALeaveCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| startTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 请假的开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss)、@AssertTrue（结束时间需在开始时间之后） | 请假的结束时间 |
| type | Integer | 是 | 无 | 请假类型，参见 `bpm_oa_type` 字典/枚举 |
| reason | String | 是 | 无 | 原因 |
| startUserSelectAssignees | Map&lt;String, List&lt;Long&gt;&gt; | 否 | 无 | 发起人自选审批人 Map，key 为任务标识，value 为审批人用户编号列表 |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 请假单编号（即 `bpm_oa_leave` 表主键） |

**业务逻辑**:
1. 计算 `startTime` 到 `endTime` 的间隔天数 `day`（LocalDateTimeUtil.between().toDays()）。
2. 将请求 VO 转换为 `BpmOALeaveDO`，设置申请人 `userId`（当前登录用户）、请假天数 `day`、审批结果 `status` 为 `BpmTaskStatusEnum.RUNNING`（审批中），插入 `bpm_oa_leave` 表。
3. 以流程定义 Key `oa_leave` 发起 BPM 流程实例，流程变量传入 `day`，业务 Key（businessKey）设置为请假单编号，并透传发起人自选审批人 `startUserSelectAssignees`。
4. 在同一事务中，将返回的流程实例编号 `processInstanceId` 更新回请假单。
5. 返回请假单编号；整个创建过程使用 `@Transactional(rollbackFor = Exception.class)`，落库或发起流程任一失败均整体回滚。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_004_005 | 发起流程失败，你没有权限发起该流程 |
| 1_009_004_003 | 任务({})的候选人未配置 |
| 1_009_004_004 | 任务({})的候选人({})不存在 |
| 1_009_004_009 | 发起流程失败，表单字段（{}）为必填项，不能为空 |

### 1.2 获得请假申请

- **路径**: GET /bpm/oa/leave/get
- **权限**: bpm:oa-leave:query
- **说明**: 按编号查询单条请假申请详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 请假单编号 |

**响应**: CommonResult&lt;BpmOALeaveRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 请假表单主键 |
| type | Integer | 请假类型，参见 `bpm_oa_type` 枚举 |
| reason | String | 原因 |
| createTime | LocalDateTime | 申请时间 |
| startTime | LocalDateTime | 请假的开始时间 |
| endTime | LocalDateTime | 请假的结束时间 |
| processInstanceId | String | 对应的流程实例编号 |
| status | Integer | 审批结果，参见 `BpmProcessInstanceStatusEnum` 枚举 |

**业务逻辑**:
1. 调用 `leaveMapper.selectById(id)` 查询 `bpm_oa_leave` 记录。
2. 通过 `BeanUtils.toBean` 将 DO 转换为 `BpmOALeaveRespVO` 返回（记录不存在时返回 null 数据）。

### 1.3 获得请假申请分页

- **路径**: GET /bpm/oa/leave/page
- **权限**: bpm:oa-leave:query
- **说明**: 分页查询**当前登录用户**发起的请假申请列表。

**请求参数 (BpmOALeavePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 继承 PageParam（默认 1） | 页码 |
| pageSize | Integer | 否 | 继承 PageParam（默认 10） | 每页条数 |
| status | Integer | 否 | 无 | 审批结果，参见 `BpmProcessInstanceResultEnum` 枚举 |
| type | Integer | 否 | 无 | 请假类型，参见 `bpm_oa_type` |
| reason | String | 否 | 无 | 原因，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 申请时间区间（between 查询） |

**响应**: CommonResult&lt;PageResult&lt;BpmOALeaveRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | BpmOALeaveRespVO[] | 请假申请列表，字段同 1.2 的响应 |
| total | Long | 总条数 |

**业务逻辑**:
1. 以当前登录用户 `userId` 作为固定过滤条件（`eqIfPresent`），即只能查询自己发起的请假单。
2. 按 `status`（精确）、`type`（精确）、`reason`（模糊 like）、`createTime`（区间 between）条件动态拼接查询。
3. 按 `id` 倒序分页返回 `PageResult<BpmOALeaveDO>`，再转换为 `PageResult<BpmOALeaveRespVO>`。

## 附：流程结果回写机制（非 HTTP 端点）

`BpmOALeaveStatusListener` 继承 `BpmProcessInstanceStatusEventListener`，监听流程定义 Key 为 `oa_leave` 的流程实例状态事件：
1. 收到 `BpmProcessInstanceStatusEvent` 事件后，以事件的 `businessKey`（即请假单编号）解析出请假单 id。
2. 调用 `updateLeaveStatus(id, status)` 更新请假单审批结果，更新前校验请假单存在，不存在则抛出 `OA_LEAVE_NOT_EXISTS` 错误。

**错误码**（OA 流程模块 1_009_001_000 段）:

| 错误码 | 说明 |
|-------|------|
| 1_009_001_001 | 请假申请不存在 |
