# 出差管理接口 (OaTravelApplyController / OaTravelReimbursementController)

> 提供个人出差申请与出差报销的草稿创建/更新、提交发起 BPM 审批流程、撤回与删除，以及本人单据的分页与详情查询；审批状态由 BPM 流程事件回调更新，出差申请审批通过后自动生成出差考勤明细，报销审批通过后回写关联申请的报销状态。

## 接口路径前缀

/oa/travel-apply  (Controller: OaTravelApplyController)
/oa/travel-reimbursement  (Controller: OaTravelReimbursementController)

## 1. 出差申请 (OaTravelApplyController)

### 1.1 创建出差申请草稿

- **路径**: POST /oa/travel-apply/create
- **权限**: oa:travel-apply:save
- **说明**: 生成单据编号并计算出差天数后，保存一条状态为「未开始」的出差申请草稿。

**请求参数 (OaTravelApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，新建时不传 |
| reason | String | 是 | @NotBlank | 出差事由 |
| startTime | LocalDateTime | 是 | @NotNull | 开始日期（时间戳毫秒） |
| endTime | LocalDateTime | 是 | @NotNull | 结束日期（时间戳毫秒），不能早于开始日期（@AssertTrue isTimeRangeValid） |
| companion | String | 否 | 无 | 同行人（填写姓名文本，不关联用户编号） |
| estimatedPrice | BigDecimal | 否 | @DecimalMin("0") | 预计费用，单位：元，不能小于零 |
| remark | String | 否 | 无 | 备注 |
| items | List\<Item\> | 是 | @NotEmpty，元素 @NotNull + @Valid | 行程明细 |
| fileUrls | List\<String\> | 否 | 元素 @NotBlank | 附件地址列表 |

行程明细 Item:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| departureAreaId | Integer | 否 | 无 | 出发地区编号（关联区域 Area 编号） |
| arrivalAreaId | Integer | 否 | 无 | 到达地区编号（关联区域 Area 编号） |
| startTime | LocalDateTime | 否 | 无 | 行程开始日期（时间戳毫秒） |
| endTime | LocalDateTime | 否 | 无 | 行程结束日期（时间戳毫秒），不能早于开始日期（@AssertTrue isTimeRangeValid） |
| transportType | Integer | 否 | @InDict(TRANSPORT_TYPE) | 交通方式，字典 `oa_transport_type` |
| remark | String | 否 | 无 | 备注 |

**响应**: CommonResult\<Long\>，返回新建出差申请的编号。

**业务逻辑**:
1. 通过 `AdminUserApi.validateUser` 查询并校验申请人存在，取其所属部门。
2. 通过 `OaNoRedisDAO` 按 `CC` 前缀生成单据编号，若库中已存在同编号记录则抛出 `TRAVEL_NO_DUPLICATE`。
3. 通过 `LocalDateTimeUtils.getDaysBetweenCeiling` 按开始/结束日期计算出差天数（向上取整）。
4. 转换为 `OaTravelApplyDO`，写入单号、天数、申请人部门，状态置为 BPM 流程实例状态「未开始」（-1），报销状态置为 false。
5. 插入数据库保存草稿，返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_011 | 出差单据编号已存在 |

### 1.2 更新出差申请草稿

- **路径**: PUT /oa/travel-apply/update
- **权限**: oa:travel-apply:save
- **说明**: 修改本人尚未进入审批的出差申请草稿（重算出差天数）。

**请求参数 (OaTravelApplySaveReqVO)**: 与「创建出差申请草稿」相同（`id` 此时为必传业务字段，无校验注解，用于定位要更新的记录）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在，否则抛出 `TRAVEL_NOT_EXISTS`。
2. 校验单据归属当前登录用户（比对 creator），否则抛出 `TRAVEL_ACCESS_DENIED`。
3. 校验可编辑状态：仅「未开始」「审批不通过」「已取消」可编辑，否则抛出 `TRAVEL_STATUS_INVALID`。
4. 重新计算开始/结束日期区间的出差天数（向上取整）。
5. 转换为 DO（含新天数）后按 id 更新申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |

### 1.3 提交出差申请

- **路径**: POST /oa/travel-apply/submit
- **权限**: oa:travel-apply:save
- **说明**: 将本人可编辑状态的出差申请提交，发起 BPM 出差审批流程并绑定流程实例编号。

**请求参数 (OaTravelApplySubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 申请编号 |
| startUserSelectAssignees | Map\<String, List\<Long\>\> | 否 | 无 | 发起人自选审批人：任务节点 Key → 候选人用户编号列表 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在（`TRAVEL_NOT_EXISTS`）、归属当前登录用户（`TRAVEL_ACCESS_DENIED`）、状态可提交（仅「未开始」「审批不通过」「已取消」，否则 `TRAVEL_STATUS_INVALID`）。
2. 先将单据状态更新为「审批中」（RUNNING）并清空流程实例编号，兼容流程创建时的同步回调。
3. 以出差天数 `days` 为流程变量，按流程定义 Key `oa_travel_apply` 发起 BPM 流程实例，支持传入发起人自选审批人。
4. 将返回的流程实例编号回写绑定到单据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |

### 1.4 撤回出差申请

- **路径**: PUT /oa/travel-apply/cancel
- **权限**: oa:travel-apply:save
- **说明**: 撤回审批中的出差申请，通过 BPM 取消流程实例，由流程事件回写单据状态。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在，否则抛出 `TRAVEL_NOT_EXISTS`。
2. 校验单据归属当前登录用户，否则抛出 `TRAVEL_ACCESS_DENIED`。
3. 仅「审批中」（RUNNING）状态可撤回，否则抛出 `TRAVEL_STATUS_INVALID`。
4. 调用 `BpmProcessInstanceApi.cancelProcessInstanceByStartUser` 以申请人身份取消流程实例（取消原因：申请人撤回出差申请），单据状态由 BPM 事件回调更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |

### 1.5 删除出差申请

- **路径**: DELETE /oa/travel-apply/delete
- **权限**: oa:travel-apply:delete
- **说明**: 删除本人尚未进入审批的出差申请。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在，否则抛出 `TRAVEL_NOT_EXISTS`。
2. 校验单据归属当前登录用户，否则抛出 `TRAVEL_ACCESS_DENIED`。
3. 校验可删除状态：仅「未开始」「审批不通过」「已取消」可删除，否则抛出 `TRAVEL_STATUS_INVALID`。
4. 按 id 删除本人单据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |

### 1.6 获得出差申请详情

- **路径**: GET /oa/travel-apply/get
- **权限**: oa:travel-apply:query
- **说明**: 按编号查询单条出差申请，并拼接申请人姓名与部门名称。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）

**响应**: CommonResult\<OaTravelApplyRespVO\>，单据不存在时 data 为 null。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 单据编号（如 CC202609140001） |
| reason | String | 出差事由 |
| startTime | LocalDateTime | 开始日期 |
| endTime | LocalDateTime | 结束日期 |
| companion | String | 同行人 |
| estimatedPrice | BigDecimal | 预计费用，单位：元 |
| remark | String | 备注 |
| days | Integer | 出差天数 |
| status | Integer | 审批状态（BPM 流程实例状态枚举） |
| reimburseStatus | Boolean | 是否已报销 |
| processInstanceId | String | 流程实例编号 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人姓名（批量查询用户拼接） |
| deptId | Long | 申请部门编号 |
| deptName | String | 申请部门名称（批量查询部门拼接） |
| createTime | LocalDateTime | 创建时间 |
| items | List\<OaTravelApplyDO.Item\> | 行程明细（结构同「创建出差申请草稿」的 Item：departureAreaId/arrivalAreaId/startTime/endTime/transportType/remark） |
| fileUrls | List\<String\> | 附件地址列表 |

**业务逻辑**:
1. 按 id 查询出差申请记录。
2. 将记录转换为 `OaTravelApplyRespVO`。
3. 批量查询申请人用户信息与部门信息，拼接 `creatorName`（用户昵称）与 `deptName`（部门名称）。

### 1.7 获得本人出差申请分页

- **路径**: GET /oa/travel-apply/page
- **权限**: oa:travel-apply:query
- **说明**: 分页查询当前登录用户本人的出差申请，响应结构同详情并拼接申请人/部门展示信息。

**请求参数 (OaTravelApplyPageReqVO)**（继承 PageParam：pageNo 默认 1、pageSize 默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 无（PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 否 | 无（PageParam） | 每页条数 |
| no | String | 否 | 无 | 单据编号，模糊匹配 |
| status | Integer | 否 | 无 | 审批状态 |
| deptId | Long | 否 | 无 | 申请部门编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间（起止两个元素） |
| reimburseStatus | Boolean | 否 | 无 | 报销状态 |

**响应**: CommonResult\<PageResult\<OaTravelApplyRespVO\>\>，记录字段同「获得出差申请详情」。

**业务逻辑**:
1. 按当前登录用户（creator）与查询条件分页查询出差申请。
2. 批量查询申请人用户信息、部门信息，拼接 `creatorName` 与 `deptName`。
3. 返回分页结果（list + total）。

### 1.8 获得本人可关联的已通过出差申请

- **路径**: GET /oa/travel-apply/approved-list
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 查询当前登录用户审批状态为「审批通过」的出差申请列表，供创建/编辑报销单时选择关联。

**请求参数**: 无

**响应**: CommonResult\<List\<OaTravelApplyRespVO\>\>，记录字段同「获得出差申请详情」（此接口直接 Bean 转换，不拼接 creatorName/deptName）。

**业务逻辑**:
1. 按 creator 为当前登录用户、审批状态为「审批通过」（APPROVE）查询申请列表。
2. 转换为 `OaTravelApplyRespVO` 列表返回。

## 2. 出差报销 (OaTravelReimbursementController)

### 2.1 创建出差报销草稿

- **路径**: POST /oa/travel-reimbursement/create
- **权限**: oa:travel-reimbursement:save
- **说明**: 生成单据编号、计算天数与报销总金额后，保存一条状态为「未开始」的出差报销草稿，可选关联已通过的出差申请。

**请求参数 (OaTravelReimbursementSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，新建时不传 |
| reason | String | 是 | @NotBlank | 出差事由 |
| startTime | LocalDateTime | 是 | @NotNull | 开始日期（时间戳毫秒） |
| endTime | LocalDateTime | 是 | @NotNull | 结束日期（时间戳毫秒），不能早于开始日期（@AssertTrue isTimeRangeValid） |
| travelApplyId | Long | 否 | 无 | 关联出差申请编号（不关联时为空） |
| remark | String | 否 | 无 | 备注 |
| items | List\<Item\> | 是 | @NotEmpty，元素 @NotNull + @Valid | 费用明细 |
| fileUrls | List\<String\> | 是 | @NotEmpty，元素 @NotBlank | 附件地址列表（报销附件必传） |

费用明细 Item:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| expenseType | Integer | 否 | @InDict(EXPENSE_TYPE) | 费用类型，字典 `oa_expense_type` |
| expenseTime | LocalDateTime | 否 | 无 | 发生日期（时间戳毫秒） |
| departureCity | String | 否 | 无 | 出发地 |
| arrivalCity | String | 否 | 无 | 到达地 |
| price | BigDecimal | 是 | @NotNull、@DecimalMin("0") | 金额，单位：元，不能小于零 |
| description | String | 否 | 无 | 费用说明 |

**响应**: CommonResult\<Long\>，返回新建出差报销的编号。

**业务逻辑**:
1. 若传入 `travelApplyId`，调用 `validateApprovedTravelApply` 校验关联申请：存在、归属当前用户、审批已通过（否则 `TRAVEL_APPLY_NOT_APPROVED`）、未报销（否则 `TRAVEL_APPLY_ALREADY_REIMBURSED`）。
2. 通过 `AdminUserApi.validateUser` 校验申请人并取其所属部门。
3. 通过 `OaNoRedisDAO` 按 `CLBX` 前缀生成单据编号，若库中已存在同编号记录则抛出 `TRAVEL_NO_DUPLICATE`。
4. 计算出差天数（开始/结束日期区间向上取整），并汇总费用明细 `price` 合计为报销总金额（保留 2 位小数，四舍五入）。
5. 写入单号、申请人部门，状态置为「未开始」（-1），支付状态置为 false，插入数据库并返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在（关联申请不存在时） |
| 1_054_270_001 | 无权操作该出差单据（关联申请非本人时） |
| 1_054_270_009 | 所选出差申请尚未审批通过 |
| 1_054_270_010 | 所选出差申请已报销，不能重复报销 |
| 1_054_270_011 | 出差单据编号已存在 |

### 2.2 更新出差报销草稿

- **路径**: PUT /oa/travel-reimbursement/update
- **权限**: oa:travel-reimbursement:save
- **说明**: 修改本人尚未进入审批的报销草稿（重算天数与报销总金额，并重新校验关联申请）。

**请求参数 (OaTravelReimbursementSaveReqVO)**: 与「创建出差报销草稿」相同（`id` 此时为必传业务字段，无校验注解，用于定位要更新的记录）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在，否则抛出 `TRAVEL_NOT_EXISTS`。
2. 校验单据归属当前登录用户，否则抛出 `TRAVEL_ACCESS_DENIED`。
3. 校验可编辑状态：仅「未开始」「审批不通过」「已取消」可编辑，否则抛出 `TRAVEL_STATUS_INVALID`。
4. 若传入 `travelApplyId`，校验关联申请已通过且未报销。
5. 重算出差天数与报销总金额（明细 price 合计），按 id 更新报销记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |
| 1_054_270_009 | 所选出差申请尚未审批通过 |
| 1_054_270_010 | 所选出差申请已报销，不能重复报销 |

### 2.3 提交出差报销

- **路径**: POST /oa/travel-reimbursement/submit
- **权限**: oa:travel-reimbursement:save
- **说明**: 将本人可编辑状态的报销单提交，发起 BPM 出差报销审批流程并绑定流程实例编号。

**请求参数 (OaTravelReimbursementSubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 报销编号 |
| startUserSelectAssignees | Map\<String, List\<Long\>\> | 否 | 无 | 发起人自选审批人：任务节点 Key → 候选人用户编号列表 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在（`TRAVEL_NOT_EXISTS`）、归属当前登录用户（`TRAVEL_ACCESS_DENIED`）、状态可提交（仅「未开始」「审批不通过」「已取消」，否则 `TRAVEL_STATUS_INVALID`）。
2. 若单据关联了出差申请，再次校验该申请仍审批已通过且未报销（否则 `TRAVEL_APPLY_NOT_APPROVED` / `TRAVEL_APPLY_ALREADY_REIMBURSED`）。
3. 先将单据状态更新为「审批中」（RUNNING）并清空流程实例编号，兼容流程创建时的同步回调。
4. 以出差天数 `days` 为流程变量，按流程定义 Key `oa_travel_reimbursement` 发起 BPM 流程实例，支持发起人自选审批人。
5. 将返回的流程实例编号回写绑定到单据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |
| 1_054_270_009 | 所选出差申请尚未审批通过 |
| 1_054_270_010 | 所选出差申请已报销，不能重复报销 |

### 2.4 撤回出差报销

- **路径**: PUT /oa/travel-reimbursement/cancel
- **权限**: oa:travel-reimbursement:save
- **说明**: 撤回审批中的出差报销，通过 BPM 取消流程实例，由流程事件回写单据状态。

**请求参数**: 无（Query 参数 `id`：报销编号，必填）

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在，否则抛出 `TRAVEL_NOT_EXISTS`。
2. 校验单据归属当前登录用户，否则抛出 `TRAVEL_ACCESS_DENIED`。
3. 仅「审批中」（RUNNING）状态可撤回，否则抛出 `TRAVEL_STATUS_INVALID`。
4. 调用 `BpmProcessInstanceApi.cancelProcessInstanceByStartUser` 以申请人身份取消流程实例（取消原因：申请人撤回出差报销），单据状态由 BPM 事件回调更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |

### 2.5 删除出差报销

- **路径**: DELETE /oa/travel-reimbursement/delete
- **权限**: oa:travel-reimbursement:delete
- **说明**: 删除本人尚未进入审批的出差报销单。

**请求参数**: 无（Query 参数 `id`：报销编号，必填）

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验单据存在，否则抛出 `TRAVEL_NOT_EXISTS`。
2. 校验单据归属当前登录用户，否则抛出 `TRAVEL_ACCESS_DENIED`。
3. 校验可删除状态：仅「未开始」「审批不通过」「已取消」可删除，否则抛出 `TRAVEL_STATUS_INVALID`。
4. 按 id 删除本人报销单。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_270_000 | 出差单据不存在 |
| 1_054_270_001 | 无权操作该出差单据 |
| 1_054_270_002 | 当前单据状态不允许该操作 |

### 2.6 获得出差报销详情

- **路径**: GET /oa/travel-reimbursement/get
- **权限**: oa:travel-reimbursement:query
- **说明**: 按编号查询单条出差报销，并拼接申请人姓名、部门名称与关联出差申请单号。

**请求参数**: 无（Query 参数 `id`：报销编号，必填）

**响应**: CommonResult\<OaTravelReimbursementRespVO\>，单据不存在时 data 为 null。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 单据编号（如 CLBX202609140001） |
| reason | String | 出差事由 |
| startTime | LocalDateTime | 开始日期 |
| endTime | LocalDateTime | 结束日期 |
| travelApplyId | Long | 关联出差申请编号（未关联时为空） |
| remark | String | 备注 |
| days | Integer | 出差天数（按起止日期向上取整） |
| status | Integer | 审批状态（BPM 流程实例状态枚举） |
| payStatus | Boolean | 是否已支付 |
| totalPrice | BigDecimal | 报销总金额，单位：元（明细金额合计） |
| travelApplyNo | String | 关联出差申请单号（批量查询申请拼接） |
| processInstanceId | String | 流程实例编号 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人姓名（批量查询用户拼接） |
| deptId | Long | 申请部门编号 |
| deptName | String | 申请部门名称（批量查询部门拼接） |
| createTime | LocalDateTime | 创建时间 |
| items | List\<OaTravelReimbursementDO.Item\> | 费用明细（结构同「创建出差报销草稿」的 Item：expenseType/expenseTime/departureCity/arrivalCity/price/description） |
| fileUrls | List\<String\> | 附件地址列表 |

**业务逻辑**:
1. 按 id 查询出差报销记录。
2. 将记录转换为 `OaTravelReimbursementRespVO`。
3. 批量查询申请人用户信息、部门信息与关联的出差申请，拼接 `creatorName`、`deptName` 与 `travelApplyNo`（关联申请单号）。

### 2.7 获得本人出差报销分页

- **路径**: GET /oa/travel-reimbursement/page
- **权限**: oa:travel-reimbursement:query
- **说明**: 分页查询当前登录用户本人的出差报销，响应结构同详情并拼接申请人/部门/关联申请单号。

**请求参数 (OaTravelReimbursementPageReqVO)**（继承 PageParam：pageNo 默认 1、pageSize 默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 无（PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 否 | 无（PageParam） | 每页条数 |
| no | String | 否 | 无 | 单据编号，模糊匹配 |
| status | Integer | 否 | 无 | 审批状态 |
| deptId | Long | 否 | 无 | 申请部门编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间（起止两个元素） |
| payStatus | Boolean | 否 | 无 | 支付状态 |

**响应**: CommonResult\<PageResult\<OaTravelReimbursementRespVO\>\>，记录字段同「获得出差报销详情」。

**业务逻辑**:
1. 按当前登录用户（creator）与查询条件分页查询出差报销。
2. 批量查询申请人用户信息、部门信息与关联出差申请，拼接 `creatorName`、`deptName` 与 `travelApplyNo`。
3. 返回分页结果（list + total）。

## 补充说明

- **审批状态回写**: 出差申请与报销单的 `status` 均冗余 BPM 流程实例状态，由 BPM 流程事件回调更新（`updateTravelApplyStatus` / `updateTravelReimbursementStatus`，服务内部方法，无 HTTP 端点）。
- **出差申请审批通过**: 回调生成申请人对应起止日期的出差考勤明细（考勤类型 TRAVEL）。
- **报销审批通过**: 回调将关联出差申请的 `reimburseStatus` 标记为已报销（重复状态回调不重复触发），支付状态不由审批流程修改。
- **单据编号**: 出差申请前缀 `CC`、出差报销前缀 `CLBX`，由 Redis DAO 生成并校验唯一。
