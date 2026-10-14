# 费用报销接口 (OaReimbursementController)

> 提供费用报销单的草稿创建与修改、提交 BPM 审批流程、本人报销单分页与详情查询能力，明细金额与票据数自动汇总。

## 接口路径前缀

/oa/reimbursement  (Controller: OaReimbursementController)

## 1. 草稿管理

### 1.1 创建费用报销草稿

- **路径**: POST /oa/reimbursement/create
- **权限**: oa:reimbursement:create
- **说明**: 校验证明人后保存报销单草稿，自动汇总报销总金额与票据总数，初始状态为未启动（NOT_START）。

**请求参数 (OaReimbursementSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 申请编号（新增时不传） |
| title | String | 是 | @NotBlank、@Size(max=255) | 标题 |
| urgency | Integer | 是 | @NotNull、@InDict(APPLY_URGENCY) | 紧急程度 |
| witnessUserId | Long | 是 | @NotNull | 证明人用户编号 |
| customerName | String | 是 | @NotBlank、@Size(max=255) | 相关客户 |
| paymentMethod | Integer | 是 | @NotNull、@InDict(REIMBURSEMENT_PAYMENT_METHOD) | 报销方式 |
| fileUrls | List\<String\> | 否 | @Size(max=5)，元素 @NotBlank、@Size(max=1024) | 附件地址列表，最多 5 个 |
| reason | String | 是 | @NotBlank、@Size(max=5000) | 申请原因 |
| items | List\<Item\> | 是 | @NotEmpty、@Valid | 报销明细列表 |

**报销明细 (OaReimbursementSaveReqVO.Item)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| expenseTime | LocalDateTime | 是 | @NotNull | 费用发生时间 |
| expenseType | Integer | 是 | @NotNull、@InDict(EXPENSE_TYPE) | 费用类型 |
| description | String | 是 | @NotBlank | 费用说明 |
| invoiceCount | Integer | 是 | @NotNull、@Min(0) | 票据张数 |
| price | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@Digits(integer=16, fraction=2) | 报销金额 |

**响应**: CommonResult\<Long\>（报销申请编号）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新建报销单的编号 |

**业务逻辑**:
1. 调用 AdminUserApi 校验证明人用户存在。
2. 转换申请内容及报销明细，汇总明细金额求和为 totalPrice、票据张数求和为 invoiceCount。
3. 审批状态置为未启动（BpmProcessInstanceStatusEnum.NOT_START），插入数据库并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |

### 1.2 更新费用报销草稿

- **路径**: PUT /oa/reimbursement/update
- **权限**: oa:reimbursement:create
- **说明**: 仅允许本人修改未提交的草稿，修改后重新汇总金额与票据数。

**请求参数 (OaReimbursementSaveReqVO)**: 与「创建费用报销草稿」相同（id 必传以定位记录）。

**响应**: CommonResult\<Boolean\>（true 表示更新成功）

**业务逻辑**:
1. 校验申请可修改：申请必须存在、归属当前登录用户、状态为未提交草稿（NOT_START），否则分别抛出申请不存在/无权操作/状态不允许错误。
2. 校验证明人用户存在。
3. 转换申请内容及明细并重新汇总 totalPrice、invoiceCount，按 id 更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

## 2. 提交审批

### 2.1 提交费用报销

- **路径**: POST /oa/reimbursement/submit
- **权限**: oa:reimbursement:create
- **说明**: 将本人的未提交草稿送入 BPM 审批流程，可由发起人自选审批人。

**请求参数 (OaReimbursementSubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 申请编号 |
| startUserSelectAssignees | Map\<String, List\<Long\>\> | 否 | - | 发起人自选审批人（节点 Key -> 用户编号列表） |

**响应**: CommonResult\<Boolean\>（true 表示提交成功）

**业务逻辑**:
1. 校验申请可提交：申请存在、归属当前用户、状态为未提交草稿。
2. 将申请状态更新为审批中（BpmProcessInstanceStatusEnum.RUNNING）。
3. 以流程定义 Key（BpmModelConstants.REIMBURSEMENT）、业务 Key（申请编号）发起流程实例，流程变量携带 totalPrice（报销总金额），并传入发起人自选审批人。
4. 将返回的流程实例编号 processInstanceId 回写到报销单记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

## 3. 查询

### 3.1 获得本人费用报销分页

- **路径**: GET /oa/reimbursement/page
- **权限**: oa:reimbursement:query
- **说明**: 分页返回当前登录用户本人创建的费用报销单，支持标题模糊、审批状态过滤，并拼接申请人昵称。

**请求参数 (OaReimbursementPageReqVO)**（继承 PageParam：pageNo、pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | PageParam 默认校验 | 页码，从 1 开始 |
| pageSize | Integer | 否 | PageParam 默认校验 | 每页条数 |
| title | String | 否 | - | 标题（模糊匹配） |
| status | Integer | 否 | - | 审批状态（如 -1） |

**响应**: CommonResult\<PageResult\<OaReimbursementRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| title | String | 标题 |
| urgency | Integer | 紧急程度 |
| reason | String | 申请原因 |
| witnessUserId | Long | 证明人用户编号 |
| customerName | String | 相关客户 |
| paymentMethod | Integer | 报销方式 |
| invoiceCount | Integer | 票据总数（明细汇总） |
| totalPrice | BigDecimal | 报销总金额（明细汇总） |
| status | Integer | 审批状态 |
| processInstanceId | String | 流程实例编号 |
| items | List\<OaReimbursementDO.Item\> | 报销明细（字段同创建接口明细：expenseTime、expenseType、description、invoiceCount、price） |
| fileUrls | List\<String\> | 附件地址列表 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人昵称（批量查询用户信息拼接） |
| createTime | LocalDateTime | 申请时间 |

**业务逻辑**:
1. 以当前登录用户编号为条件分页查询报销单（仅本人数据），附加 title、status 过滤条件。
2. 批量查询申请人用户信息，将昵称拼接到 creatorName 字段返回。

**错误码**: 无（查询接口）

### 3.2 获得费用报销详情

- **路径**: GET /oa/reimbursement/get
- **权限**: oa:reimbursement:query
- **说明**: 按编号查询单条报销单详情，包含明细与附件，拼接申请人昵称。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 申请编号 |

**响应**: CommonResult\<OaReimbursementRespVO\>（字段同分页接口单条记录；记录不存在时返回 null）

**业务逻辑**:
1. 按编号查询报销单记录。
2. 转换为响应 VO，并查询申请人用户信息拼接 creatorName 后返回。

**错误码**: 无（不存在时返回 null 而非抛错）
