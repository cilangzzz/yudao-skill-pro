# 加班申请接口 (OaOvertimeApplyController)

> OA 加班申请：支持创建/修改加班草稿、提交至 BPM 流程审批（流程定义 key 为 `oa_overtime_apply`）、查询本人加班申请分页与详情；审批结果由 BPM 状态监听器（OaOvertimeApplyStatusListener）回调回写。

## 接口路径前缀

/oa/overtime-apply  (Controller: OaOvertimeApplyController)

## 1. 草稿管理

### 1.1 创建加班申请草稿

- **路径**: POST /oa/overtime-apply/create
- **权限**: oa:overtime-apply:create
- **说明**: 新建一条加班申请草稿，服务端按开始/结束时间计算加班天数，状态置为「未开始」。

**请求参数 (OaOvertimeApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | — | 申请编号（创建时传空） |
| title | String | 是 | @NotBlank、@Size(max=255) | 标题 |
| urgency | Integer | 是 | @NotNull、@InDict(APPLY_URGENCY) | 紧急程度（字典 APPLY_URGENCY） |
| type | Integer | 是 | @NotNull、@InDict(OVERTIME_TYPE) | 加班类型（字典 OVERTIME_TYPE） |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间 |
| endTime | LocalDateTime | 是 | @NotNull（@AssertTrue 校验结束时间不能早于开始时间） | 结束时间 |
| reason | String | 是 | @NotBlank、@Size(max=5000) | 申请原因 |

**响应**: CommonResult<Long>（新创建的申请编号）

**业务逻辑**:
1. 将请求 VO 转换为 OaOvertimeApplyDO，通过 LocalDateTimeUtils.getDaysBetween(startTime, endTime, 1) 计算加班天数（保留 1 位小数、四舍五入）。
2. 清空 id，设置审批状态为「未开始」（BpmProcessInstanceStatusEnum.NOT_START），插入数据库保存草稿。
3. 返回新记录编号。

### 1.2 更新加班申请草稿

- **路径**: PUT /oa/overtime-apply/update
- **权限**: oa:overtime-apply:create
- **说明**: 修改本人未提交的加班申请草稿（复用创建权限）。

**请求参数 (OaOvertimeApplySaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 校验申请可修改：申请必须存在（APPLY_NOT_EXISTS）、属于当前登录用户（APPLY_ACCESS_DENIED）、且状态为未提交草稿 NOT_START（APPLY_STATUS_INVALID）。
2. 将请求 VO 转换为 DO，并按新的开始/结束时间重新计算加班天数。
3. updateById 更新申请内容。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

## 2. 提交审批

### 2.1 提交加班申请

- **路径**: POST /oa/overtime-apply/submit
- **权限**: oa:overtime-apply:create
- **说明**: 将本人未提交的加班申请草稿提交至 BPM 流程审批，支持发起人自选审批人。

**请求参数 (OaOvertimeApplySubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 申请编号 |
| startUserSelectAssignees | Map&lt;String, List&lt;Long&gt;&gt; | 否 | — | 发起人自选审批人（节点 Key → 用户编号列表） |

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 校验申请可提交：存在（APPLY_NOT_EXISTS）、本人归属（APPLY_ACCESS_DENIED）、状态为 NOT_START 草稿（APPLY_STATUS_INVALID）。
2. 将申请状态更新为「审批中」（BpmProcessInstanceStatusEnum.RUNNING）。
3. 以 `days`（加班天数）作为流程变量，调用 BpmProcessInstanceApi 创建流程实例：流程定义 key 为 `oa_overtime_apply`，businessKey 为申请编号，携带发起人自选审批人。
4. 将返回的流程实例编号 processInstanceId 回写绑定到申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

## 3. 查询

### 3.1 获得本人加班申请分页

- **路径**: GET /oa/overtime-apply/page
- **权限**: oa:overtime-apply:query
- **说明**: 分页查询当前登录用户本人的加班申请，按创建时间倒序，并拼接申请人昵称。

**请求参数 (OaOvertimeApplyPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | — | 页码（继承自 PageParam） |
| pageSize | Integer | 否 | — | 每页条数（继承自 PageParam） |
| title | String | 否 | — | 标题（模糊匹配） |
| status | Integer | 否 | — | 审批状态（等值匹配） |

**响应**: CommonResult&lt;PageResult&lt;OaOvertimeApplyRespVO&gt;&gt;，字段见 3.2 响应表。

**业务逻辑**:
1. 按 creator = 当前登录用户过滤，仅查询本人申请。
2. 拼接查询条件：title 模糊匹配（可选）、status 等值匹配（可选）。
3. 按 createTime、id 倒序分页返回。
4. 批量查询申请人信息（adminUserApi.getUserMap），将申请人昵称拼接到 creatorName 字段。

### 3.2 获得加班申请详情

- **路径**: GET /oa/overtime-apply/get
- **权限**: oa:overtime-apply:query
- **说明**: 按编号查询加班申请详情，并拼接申请人昵称。

**请求参数**: 无（Query 参数 id）

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 申请编号 |

**响应**: CommonResult&lt;OaOvertimeApplyRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| title | String | 标题 |
| urgency | Integer | 紧急程度 |
| type | Integer | 加班类型 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| days | BigDecimal | 天数（服务端计算，1 位小数） |
| reason | String | 申请原因 |
| status | Integer | 审批状态 |
| processInstanceId | String | 流程实例编号 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人昵称 |
| createTime | LocalDateTime | 申请时间 |

**业务逻辑**:
1. 按编号 selectById 查询申请记录（不存在时返回 null）。
2. 转换为 RespVO 并查询申请人昵称拼接到 creatorName。

## 4. 流程回调（非 admin 端点）

Service 提供 `updateOvertimeApplyStatus(id, status)`，由 BPM 状态监听器 OaOvertimeApplyStatusListener（监听流程定义 `oa_overtime_apply`）在审批流程结束时回调：校验申请存在（APPLY_NOT_EXISTS）后，将审批状态回写到申请记录。该能力不通过 Controller 暴露。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
