# 印章管理接口 (OaSealController / OaSealApplyController)

> 提供 OA 印章台账维护（创建、变更、停用、删除印章）与用印申请全流程（草稿、提交 BPM 审批、撤销、查询）能力。

## 接口路径前缀

- `/oa/seal` (Controller: OaSealController) — 印章台账管理
- `/oa/seal-apply` (Controller: OaSealApplyController) — 用印申请管理

## 1. 印章台账（OaSealController）

### 1.1 创建印章

- **路径**: POST /oa/seal/create
- **权限**: oa:seal:create
- **说明**: 新增印章台账记录，印章编号由系统按 `YZ` 前缀自动生成，不接受传入。

**请求参数 (OaSealSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（新增时不传） |
| deptId | Long | 是 | @NotNull | 所属部门编号（允许与保管部门不同） |
| name | String | 是 | @NotBlank、@Size(max = 128) | 印章名称 |
| type | Integer | 是 | @NotNull | 印章类型 |
| category | Integer | 否 | | 印章分类 |
| keeperUserId | Long | 是 | @NotNull | 保管人用户编号 |
| keeperDeptId | Long | 是 | @NotNull | 保管部门编号 |
| status | Integer | 是 | @NotNull、@InEnum(OaSealStatusEnum) | 印章台账状态（0 在库 / 1 停用 / 2 使用中） |
| purchaseTime | LocalDateTime | 否 | | 购买时间 |
| enableTime | LocalDateTime | 否 | | 启用时间 |
| disableTime | LocalDateTime | 否 | | 停用时间 |
| picUrl | String | 否 | @Size(max = 2048) | 印章照片地址 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| remark | String | 否 | @Size(max = 500) | 备注 |

**响应**: CommonResult&lt;Long&gt;，返回新创建的印章编号。

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 印章编号 |

**业务逻辑**:
1. 校验保管人用户有效（AdminUserApi.validateUser）。
2. 校验保管部门有效（DeptApi.validateDeptList）。
3. 校验所属部门有效，允许与保管部门不同。
4. 通过 OaNoRedisDAO 按 `YZ` 前缀生成印章编号，并校验编号唯一性（重复抛 SEAL_NO_DUPLICATE）。
5. 转换为 OaSealDO 插入数据库，状态及购买/启用/停用日期按表单保存，返回新记录 ID。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_001 | 印章编号已存在 |

### 1.2 更新印章

- **路径**: PUT /oa/seal/update
- **权限**: oa:seal:update
- **说明**: 修改印章台账信息（含保管人、保管部门、状态等），印章编号不可修改。

**请求参数 (OaSealSaveReqVO)**: 字段同 1.1，其中 id 为更新必传。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验印章存在（不存在抛 SEAL_NOT_EXISTS）。
2. 校验保管人用户有效。
3. 校验保管部门有效。
4. 校验所属部门有效，允许与保管部门不同。
5. 转换为 OaSealDO 按 ID 更新印章及保管信息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_000 | 印章不存在 |

### 1.3 删除印章

- **路径**: DELETE /oa/seal/delete
- **权限**: oa:seal:delete
- **说明**: 删除印章台账，已被用印申请等业务单据引用的印章不允许删除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 印章编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验印章存在（不存在抛 SEAL_NOT_EXISTS）。
2. 校验印章未被业务单据引用（按 sealId 统计用印申请数量，大于 0 抛 SEAL_IN_USE）。
3. 逻辑删除台账记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_000 | 印章不存在 |
| 1_054_210_002 | 印章已有业务单据引用，不能删除 |

### 1.4 获得印章

- **路径**: GET /oa/seal/get
- **权限**: oa:seal:query
- **说明**: 按编号获得印章详情，并拼接所属部门、保管人、保管部门名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 印章编号 |

**响应**: CommonResult&lt;OaSealRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| deptId | Long | 所属部门编号 |
| deptName | String | 所属部门名称（拼接） |
| no | String | 印章编号（业务编号，如 SEAL-001 风格） |
| name | String | 印章名称 |
| type | Integer | 印章类型 |
| category | Integer | 印章分类 |
| keeperUserId | Long | 保管人用户编号 |
| keeperDeptId | Long | 保管部门编号 |
| keeperName | String | 保管人昵称（拼接） |
| keeperDeptName | String | 保管部门名称（拼接） |
| status | Integer | 印章台账状态（0 在库 / 1 停用 / 2 使用中） |
| purchaseTime | LocalDateTime | 购买时间 |
| enableTime | LocalDateTime | 启用时间 |
| disableTime | LocalDateTime | 停用时间 |
| picUrl | String | 印章照片地址 |
| sort | Integer | 显示顺序 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询印章，不存在抛 SEAL_NOT_EXISTS。
2. 批量查询保管人用户与所属/保管部门信息。
3. 转换为 OaSealRespVO 并拼接 deptName、keeperName、keeperDeptName 展示字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_000 | 印章不存在 |

### 1.5 获得印章分页

- **路径**: GET /oa/seal/page
- **权限**: oa:seal:query
- **说明**: 分页查询印章台账，支持编号、名称、分类、类型、保管人、部门、状态及购买/启用/停用时间范围过滤；响应拼接部门与保管人名称。

**请求参数 (OaSealPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |
| no | String | 否 | | 印章业务编号 |
| name | String | 否 | | 印章名称 |
| category | Integer | 否 | | 分类 |
| type | Integer | 否 | | 类型 |
| keeperUserId | Long | 否 | | 保管人编号 |
| deptId | Long | 否 | | 所属部门编号 |
| status | Integer | 否 | | 台账状态 |
| purchaseTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 购买时间范围 |
| enableTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 启用时间范围 |
| disableTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 停用时间范围 |

**响应**: CommonResult&lt;PageResult&lt;OaSealRespVO&gt;&gt;，列表元素字段同 1.4 响应表。

**业务逻辑**:
1. 按 OaSealPageReqVO 条件分页查询印章（OaSealMapper.selectPage）。
2. 批量查询保管人用户与部门信息，拼接 deptName、keeperName、keeperDeptName 后返回。

## 2. 用印申请（OaSealApplyController）

### 2.1 获得可申请的印章分页

- **路径**: GET /oa/seal-apply/seal-page
- **权限**: oa:seal-apply:create 或 oa:seal-apply:query（hasAnyPermissions）
- **说明**: 供发起用印申请时选择印章，复用印章分页查询，但仅返回 id、no、name 三个精简字段。

**请求参数 (OaSealPageReqVO)**: 字段同 1.5 请求参数表。

**响应**: CommonResult&lt;PageResult&lt;OaSealRespVO&gt;&gt;，列表元素仅填充部分字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 印章编号 |
| no | String | 印章业务编号 |
| name | String | 印章名称 |

**业务逻辑**:
1. 调用印章服务 getSealPage 按 OaSealPageReqVO 条件分页查询。
2. 仅将每条记录的 id、no、name 转换为 OaSealRespVO 返回。

### 2.2 创建用印申请草稿

- **路径**: POST /oa/seal-apply/create
- **权限**: oa:seal-apply:create
- **说明**: 创建用印申请草稿，单号按 `YY` 前缀自动生成；草稿不占用预约时段。

**请求参数 (OaSealApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（新增时不传） |
| sealId | Long | 是 | @NotNull | 印章编号 |
| reason | String | 是 | @NotBlank、@Size(max = 500) | 用印事由 |
| type | Integer | 是 | @NotNull、@InEnum(OaSealApplyTypeEnum) | 用印类型（1 合同 / 2 协议 / 3 证明 / 4 授权 / 5 其他） |
| mode | Integer | 是 | @NotNull、@InEnum(OaSealUseModeEnum) | 用印方式（1 现场用印 / 2 外借） |
| documentTitle | String | 否 | @Size(max = 255) | 文件标题 |
| documentType | String | 否 | @Size(max = 64) | 文件类型 |
| documentCount | Integer | 是 | @NotNull、@Min(1) | 文件份数 |
| contractPrice | BigDecimal | 否 | @DecimalMin(0)、@Digits(integer=16, fraction=2) | 合同金额（type 为合同时使用） |
| contractParty | String | 否 | @Size(max = 255) | 合同对方 |
| expectedUseTime | LocalDateTime | 是 | @NotNull | 预计用印时间 |
| expectedReturnTime | LocalDateTime | 否 | | 预计归还时间（外借时使用） |
| actualReturnTime | LocalDateTime | 否 | | 实际归还时间 |
| urgent | Boolean | 是 | @NotNull | 是否紧急 |
| remark | String | 否 | @Size(max = 500) | 备注 |
| fileUrls | List&lt;String&gt; | 否 | @Size(max = 5)，元素 @NotBlank、@Size(max = 2048) | 附件地址列表 |

**响应**: CommonResult&lt;Long&gt;，返回新创建的申请编号。

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 用印申请编号 |

**业务逻辑**:
1. 校验申请的印章存在（草稿不占用预约时段）。
2. 校验申请人账号有效；申请人 userId 与所属部门 deptId 取自平台账号，不接受客户端指定。
3. 通过 OaNoRedisDAO 按 `YY` 前缀生成申请单号，并校验唯一性（重复抛 SEAL_APPLY_NO_DUPLICATE）。
4. 保存草稿并快照印章信息（sealNo、sealName、keeperUserId、sealType、keeperDeptId）。
5. 审批状态初始化为 NOT_START（未提交），用印状态初始化为待处理（PENDING）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_000 | 印章不存在 |
| 1_054_210_021 | 用印申请单号已存在 |

### 2.3 更新用印申请草稿

- **路径**: PUT /oa/seal-apply/update
- **权限**: oa:seal-apply:update
- **说明**: 修改尚未提交的用印申请草稿，仅允许本人操作；提交后不可修改。

**请求参数 (OaSealApplySaveReqVO)**: 字段同 2.2，其中 id 为更新必传。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验申请存在（SEAL_APPLY_NOT_EXISTS）且归属当前用户（SEAL_APPLY_NOT_OWNER）。
2. 校验申请仍为草稿状态（NOT_START），否则抛 SEAL_APPLY_STATUS_INVALID。
3. 重新校验申请内容对应的印章存在。
4. 按白名单字段更新，并重新快照印章信息（sealNo、sealName、keeperUserId、sealType、keeperDeptId）。
5. 用印类型非合同时清空 contractPrice、contractParty；用印方式非外借时清空 expectedReturnTime。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_000 | 印章不存在 |
| 1_054_210_013 | 用印申请不存在 |
| 1_054_210_014 | 只能操作本人的用印申请 |
| 1_054_210_015 | 用印申请状态不允许该操作 |

### 2.4 删除用印申请草稿

- **路径**: DELETE /oa/seal-apply/delete
- **权限**: oa:seal-apply:delete
- **说明**: 删除本人尚未提交的用印申请草稿，已提交申请保留审批记录不可删除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 申请编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验申请存在且归属当前用户。
2. 校验申请仍为草稿状态（已提交申请保留审批记录，抛 SEAL_APPLY_STATUS_INVALID）。
3. 逻辑删除草稿记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_013 | 用印申请不存在 |
| 1_054_210_014 | 只能操作本人的用印申请 |
| 1_054_210_015 | 用印申请状态不允许该操作 |

### 2.5 提交用印申请

- **路径**: PUT /oa/seal-apply/submit
- **权限**: oa:seal-apply:create
- **说明**: 将草稿提交发起 BPM 审批流程，外借申请校验借用时段冲突，返回流程实例编号。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 申请编号 |

**响应**: CommonResult&lt;String&gt;，返回 BPM 流程实例编号。

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | String | 流程实例编号（processInstanceId） |

**业务逻辑**:
1. 校验申请存在、归属当前用户、仍为草稿状态。
2. 校验关联印章存在。
3. 校验借用时段冲突：仅外借且预计用印/归还时间完整时检查，预计用印时间晚于归还时间抛 SEAL_APPLY_TIME_INVALID；与该印章其他「审批中或审批通过」的外借预约在闭区间上重叠时抛 SEAL_APPLY_TIME_CONFLICT。
4. 将审批状态更新为审批中（RUNNING），并重新快照印章信息。
5. 以流程定义 `oa_seal_apply`、业务键为申请编号发起 BPM 流程实例。
6. 将返回的流程实例编号回写到申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_000 | 印章不存在 |
| 1_054_210_013 | 用印申请不存在 |
| 1_054_210_014 | 只能操作本人的用印申请 |
| 1_054_210_015 | 用印申请状态不允许该操作 |
| 1_054_210_016 | 用印或归还时间不正确 |
| 1_054_210_017 | 该印章存在冲突预约或尚未归还 |

### 2.6 撤销用印申请

- **路径**: PUT /oa/seal-apply/cancel
- **权限**: oa:seal-apply:update
- **说明**: 撤销本人审批中的用印申请，通过 BPM 撤销流程实例，由审批事件回调释放预约。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 申请编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验申请存在（台账删除不影响历史申请撤销）。
2. 校验归属当前用户。
3. 校验审批状态为审批中（RUNNING），否则抛 SEAL_APPLY_STATUS_INVALID。
4. 以申请人身份撤销 BPM 流程实例，撤销原因为「申请人撤销用印申请」。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_210_013 | 用印申请不存在 |
| 1_054_210_014 | 只能操作本人的用印申请 |
| 1_054_210_015 | 用印申请状态不允许该操作 |

### 2.7 获得用印申请

- **路径**: GET /oa/seal-apply/get
- **权限**: oa:seal-apply:query
- **说明**: 按编号获得用印申请详情，并拼接申请人、申请部门、保管人、保管部门名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 申请编号 |

**响应**: CommonResult&lt;OaSealApplyRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 申请编号 |
| sealId | Long | 印章编号 |
| reason | String | 用印事由 |
| type | Integer | 用印类型（1 合同 / 2 协议 / 3 证明 / 4 授权 / 5 其他） |
| mode | Integer | 用印方式（1 现场用印 / 2 外借） |
| documentTitle | String | 文件标题 |
| documentType | String | 文件类型 |
| documentCount | Integer | 文件份数 |
| contractPrice | BigDecimal | 合同金额 |
| contractParty | String | 合同对方 |
| expectedUseTime | LocalDateTime | 预计用印时间 |
| expectedReturnTime | LocalDateTime | 预计归还时间 |
| urgent | Boolean | 是否紧急 |
| remark | String | 备注 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| no | String | 申请单号 |
| sealNo | String | 印章业务编号（快照） |
| sealName | String | 印章名称（快照） |
| sealType | Integer | 印章类型（快照） |
| keeperDeptId | Long | 保管部门编号（快照） |
| keeperDeptName | String | 保管部门名称（拼接） |
| userId | Long | 申请人编号 |
| deptId | Long | 申请部门编号 |
| userName | String | 申请人昵称（拼接） |
| deptName | String | 申请部门名称（拼接） |
| keeperUserId | Long | 保管人编号（快照） |
| keeperName | String | 保管人昵称（拼接） |
| status | Integer | 审批状态（BPM 流程状态） |
| useStatus | Integer | 用印状态（0 待处理 / 1 已完成 / 2 外借中 / 3 已归还 / 4 已逾期） |
| processInstanceId | String | 流程实例编号 |
| actualUseTime | LocalDateTime | 实际用印时间 |
| actualReturnTime | LocalDateTime | 实际归还时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询用印申请。
2. 批量查询申请人/保管人用户信息与申请/保管部门信息。
3. 转换为 OaSealApplyRespVO 并拼接 userName、deptName、keeperName、keeperDeptName 展示字段。

### 2.8 获得本人的用印申请分页

- **路径**: GET /oa/seal-apply/page
- **权限**: oa:seal-apply:query
- **说明**: 分页查询当前登录用户本人的用印申请，支持单号、印章、部门、时间范围、审批/用印状态等条件过滤；响应拼接用户与部门名称。

**请求参数 (OaSealApplyPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |
| no | String | 否 | | 申请单号 |
| sealId | Long | 否 | | 印章编号 |
| sealName | String | 否 | | 印章名称 |
| deptId | Long | 否 | | 申请部门编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |
| expectedUseTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 预计用印时间范围 |
| status | Integer | 否 | | 审批状态 |
| useStatus | Integer | 否 | | 用印状态 |
| type | Integer | 否 | | 用印类型 |
| mode | Integer | 否 | | 用印方式 |
| urgent | Boolean | 否 | | 是否紧急 |

**响应**: CommonResult&lt;PageResult&lt;OaSealApplyRespVO&gt;&gt;，列表元素字段同 2.7 响应表。

**业务逻辑**:
1. 以当前登录用户 userId 作为申请人条件，按 OaSealApplyPageReqVO 分页查询（OaSealApplyMapper.selectPage）。
2. 批量查询申请人/保管人用户信息与申请/保管部门信息。
3. 拼接 userName、deptName、keeperName、keeperDeptName 后返回。
