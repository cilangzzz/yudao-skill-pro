# 转正申请接口 (OaRegularApplyController)

> 员工试用期/实习期转正申请的草稿维护、BPM 审批流提交与本人申请查询，审批状态由流程实例驱动。

## 接口路径前缀

/oa/regular-apply  (Controller: OaRegularApplyController)

## 1. 草稿管理

### 1.1 创建转正申请草稿

- **路径**: POST /oa/regular-apply/create
- **权限**: oa:regular-apply:create
- **说明**: 创建一条未提交（未开始）的转正申请草稿，返回申请编号。

**请求参数 (OaRegularApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | — | 申请编号（新增时忽略，Service 强制置空） |
| title | String | 是 | @NotBlank、@Size(max=255) | 标题 |
| urgency | Integer | 是 | @NotNull、@InDict(APPLY_URGENCY) | 紧急程度，字典 APPLY_URGENCY |
| startTime | LocalDateTime | 是 | @NotNull | 试用开始时间（int64 时间戳） |
| endTime | LocalDateTime | 是 | @NotNull | 试用结束时间（int64 时间戳），不能早于开始时间（@AssertTrue isTimeRangeValid） |
| experience | String | 是 | @NotBlank、@Size(max=255) | 试用期心得 |
| understanding | String | 是 | @NotBlank、@Size(max=255) | 岗位职责理解 |
| growth | String | 是 | @NotBlank、@Size(max=255) | 试用期成长 |
| deficiency | String | 是 | @NotBlank、@Size(max=255) | 目前不足 |
| improvement | String | 是 | @NotBlank、@Size(max=255) | 工作改进 |
| suggestion | String | 是 | @NotBlank、@Size(max=255) | 产品意见建议 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的转正申请编号。

**业务逻辑**:
1. 将请求 VO 转换为 OaRegularApplyDO，按 startTime 与 endTime 计算试用天数（LocalDateTimeUtils.getDaysBetweenCeiling，向上取整）。
2. 强制置空 id，并将审批状态设置为 BpmProcessInstanceStatusEnum.NOT_START（未开始，即草稿）。
3. 插入 oa_regular_apply 表并返回生成的申请编号。

### 1.2 更新转正申请草稿

- **路径**: PUT /oa/regular-apply/update
- **权限**: oa:regular-apply:create
- **说明**: 修改本人尚处于"未开始"状态的转正申请草稿内容。

**请求参数 (OaRegularApplySaveReqVO)**: 字段同 [1.1](#11-创建转正申请草稿)，其中 id 必填（用于定位更新的记录）。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验申请可修改：申请必须存在（否则抛申请不存在）、creator 必须为当前登录用户（否则抛无权操作）、状态必须为 NOT_START 草稿（否则抛状态不允许操作）。
2. 将请求 VO 转换为 DO，并根据新的 startTime/endTime 重新计算试用天数。
3. 按申请编号 updateById 更新记录。

## 2. 提交审批

### 2.1 提交转正申请

- **路径**: POST /oa/regular-apply/submit
- **权限**: oa:regular-apply:create
- **说明**: 将本人草稿置为审批中，并基于 BPM 流程定义 `oa_regular_apply` 发起流程实例。

**请求参数 (OaRegularApplySubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 申请编号 |
| startUserSelectAssignees | Map&lt;String, List&lt;Long&gt;&gt; | 否 | — | 发起人自选审批人（节点 Key → 审批人编号列表） |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验申请可提交：申请存在、归属本人、状态为 NOT_START 草稿。
2. 将申请状态更新为 BpmProcessInstanceStatusEnum.RUNNING（审批中）。
3. 调用 BpmProcessInstanceApi.createProcessInstance 发起流程实例：流程定义 Key 为 BpmModelConstants.REGULAR_APPLY（`oa_regular_apply`），businessKey 为申请编号，流程变量携带 days（试用天数），并传入发起人自选审批人 startUserSelectAssignees。
4. 将返回的流程实例编号 processInstanceId 回写绑定到转正申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

## 3. 查询

### 3.1 获得本人转正申请分页

- **路径**: GET /oa/regular-apply/page
- **权限**: oa:regular-apply:query
- **说明**: 分页查询当前登录用户本人发起的转正申请，支持标题模糊、审批状态过滤。

**请求参数 (OaRegularApplyPageReqVO)**: 继承 PageParam（pageNo、pageSize）。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| title | String | 否 | — | 标题，模糊匹配 |
| status | Integer | 否 | — | 审批状态（BpmProcessInstanceStatusEnum） |

**响应**: CommonResult&lt;PageResult&lt;OaRegularApplyRespVO&gt;&gt;

响应字段 (OaRegularApplyRespVO):

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| title | String | 标题 |
| urgency | Integer | 紧急程度（字典 APPLY_URGENCY） |
| startTime | LocalDateTime | 试用开始时间 |
| endTime | LocalDateTime | 试用结束时间 |
| days | Integer | 试用天数（按起止时间计算） |
| experience | String | 试用期心得 |
| understanding | String | 岗位职责理解 |
| growth | String | 试用期成长 |
| deficiency | String | 目前不足 |
| improvement | String | 工作改进 |
| suggestion | String | 产品意见建议 |
| status | Integer | 审批状态（BpmProcessInstanceStatusEnum） |
| processInstanceId | String | BPM 流程实例编号 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人昵称 |
| createTime | LocalDateTime | 申请时间 |

**业务逻辑**:
1. 按 creator = 当前登录用户过滤，拼接 title 模糊、status 精确条件，按 createTime、id 倒序分页查询。
2. 批量查询申请人用户信息（AdminUserApi.getUserMap）。
3. 转换为 RespVO 并拼接申请人昵称 creatorName。

### 3.2 获得转正申请详情

- **路径**: GET /oa/regular-apply/get
- **权限**: oa:regular-apply:query
- **说明**: 按编号查询单条转正申请详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | — | 申请编号 |

**响应**: CommonResult&lt;OaRegularApplyRespVO&gt;，字段同 [3.1](#31-获得本人转正申请分页)。

**业务逻辑**:
1. 按编号查询转正申请记录（selectById）。
2. 转换为 RespVO 并通过 AdminUserApi 查询拼接申请人昵称 creatorName；申请不存在时返回 null。

## 错误码汇总（流程申请段 1-054-280-000）

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |
