# 车辆管理接口 (OaVehicleController / OaVehicleApplyController / OaVehicleReturnController)

> 提供 OA 车辆管理能力：车辆台账维护（增删改查）、用车申请（草稿 + BPM 审批 + 时段占用/冲突校验）以及还车申请（草稿 + BPM 审批 + 归还状态回写）。

## 接口路径前缀

- /oa/vehicle  (Controller: OaVehicleController)
- /oa/vehicle-apply  (Controller: OaVehicleApplyController)
- /oa/vehicle-return  (Controller: OaVehicleReturnController)

---

## 1. 车辆台账（OaVehicleController）

### 1.1 创建车辆

- **路径**: POST /oa/vehicle/create
- **权限**: oa:vehicle:create
- **说明**: 新增车辆台账记录，校验车牌号唯一与所属部门有效。

**请求参数 (OaVehicleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（新增时不用） |
| no | String | 是 | @NotBlank、@Size(max=32) | 车牌号 |
| name | String | 是 | @NotBlank、@Size(max=128) | 车辆名称 |
| deptId | Long | 否 | - | 所属部门编号 |
| type | String | 是 | @NotBlank、@Size(max=64) | 车型 |
| category | String | 否 | @Size(max=64) | 车辆分类 |
| brandModel | String | 否 | @Size(max=128) | 品牌型号 |
| seatCount | Integer | 是 | @NotNull、@DecimalMin("1") | 座位数 |
| barePrice | BigDecimal | 是 | @NotNull、@DecimalMin("0")、@Digits(integer=16, fraction=2) | 裸车价格（元） |
| compulsoryInsuranceExpireTime | LocalDateTime | 否 | - | 交强险到期时间 |
| commercialInsuranceExpireTime | LocalDateTime | 否 | - | 商业险到期时间 |
| inspectionExpireTime | LocalDateTime | 否 | - | 年检到期时间 |
| picUrl | String | 否 | @Size(max=2048) | 车辆照片 URL |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| status | Integer | 是 | @NotNull、@InEnum(OaVehicleStatusEnum) | 车辆状态（0 空闲 / 1 停用 / 2 使用中） |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的车辆编号

**业务逻辑**:
1. 校验车牌号在台账内唯一，重复抛 VEHICLE_NO_DUPLICATE。
2. 若填写所属部门，调用 DeptApi 校验部门有效。
3. VO 转换为 OaVehicleDO 后插入数据库，返回新记录 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_001 | 车牌号已存在 |

### 1.2 更新车辆

- **路径**: PUT /oa/vehicle/update
- **权限**: oa:vehicle:update
- **说明**: 修改车辆台账基础信息与状态。

**请求参数 (OaVehicleSaveReqVO)**: 与 1.1 相同，id 必传用于定位记录。

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验车辆存在，否则抛 VEHICLE_NOT_EXISTS。
2. 校验车牌号唯一（排除自身 id）。
3. 若填写所属部门，校验部门有效。
4. VO 转换为 OaVehicleDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |
| 1_054_220_001 | 车牌号已存在 |

### 1.3 删除车辆

- **路径**: DELETE /oa/vehicle/delete?id={id}
- **权限**: oa:vehicle:delete
- **说明**: 删除车辆台账，已被业务单据引用的车辆不允许删除。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 车辆编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验车辆存在，否则抛 VEHICLE_NOT_EXISTS。
2. 统计该车辆的用车申请数量，大于 0 抛 VEHICLE_IN_USE，禁止删除。
3. 按 id 删除车辆记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |
| 1_054_220_019 | 车辆已有业务单据引用，不能删除 |

### 1.4 获得车辆

- **路径**: GET /oa/vehicle/get?id={id}
- **权限**: oa:vehicle:query
- **说明**: 查询单辆车辆详情，拼接所属部门名称。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 车辆编号 |

**响应**: CommonResult&lt;OaVehicleRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 车牌号 |
| name | String | 车辆名称 |
| deptId | Long | 所属部门编号 |
| deptName | String | 所属部门名称（拼接 DeptApi） |
| type | String | 车型 |
| category | String | 车辆分类 |
| brandModel | String | 品牌型号 |
| seatCount | Integer | 座位数 |
| barePrice | BigDecimal | 裸车价格（元） |
| compulsoryInsuranceExpireTime | LocalDateTime | 交强险到期时间 |
| commercialInsuranceExpireTime | LocalDateTime | 商业险到期时间 |
| inspectionExpireTime | LocalDateTime | 年检到期时间 |
| picUrl | String | 车辆照片 URL |
| status | Integer | 车辆台账状态（0 空闲 / 1 停用 / 2 使用中） |
| sort | Integer | 显示顺序 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验车辆存在，否则抛 VEHICLE_NOT_EXISTS。
2. 转换为 RespVO 并通过 DeptApi 批量查询部门，拼接 deptName。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |

### 1.5 获得车辆分页

- **路径**: GET /oa/vehicle/page
- **权限**: oa:vehicle:query
- **说明**: 分页查询车辆台账，支持车牌号、部门、保险/年检到期时间区间等条件过滤。

**请求参数 (OaVehiclePageReqVO，继承 PageParam：pageNo、pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | PageParam 默认 1 | 页码 |
| pageSize | Integer | 否 | PageParam 默认 10 | 每页条数 |
| no | String | 否 | - | 车牌号 |
| name | String | 否 | - | 车辆名称 |
| deptId | Long | 否 | - | 所属部门编号 |
| category | String | 否 | - | 分类 |
| status | Integer | 否 | @InEnum(OaVehicleStatusEnum) | 状态（0/1/2） |
| type | String | 否 | - | 车型 |
| brandModel | String | 否 | - | 品牌型号 |
| compulsoryInsuranceExpireTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 交强险到期时间区间 |
| commercialInsuranceExpireTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 商业险到期时间区间 |
| inspectionExpireTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 年检到期时间区间 |

**响应**: CommonResult&lt;PageResult&lt;OaVehicleRespVO&gt;&gt;，字段与 1.4 相同（列表批量拼接 deptName）。

**业务逻辑**:
1. 按查询条件分页查询车辆台账。
2. 批量转换 RespVO 并通过 DeptApi 拼接所属部门名称。

---

## 2. 用车申请（OaVehicleApplyController）

### 2.1 获得用车申请可选的车辆分页

- **路径**: GET /oa/vehicle-apply/vehicle-page
- **权限**: oa:vehicle-apply:create
- **说明**: 发起用车申请时选择车辆的分页查询，直接复用车辆台账分页逻辑。

**请求参数 (OaVehiclePageReqVO)**: 与 1.5 的请求参数相同（继承 PageParam）。

**响应**: CommonResult&lt;PageResult&lt;OaVehicleRespVO&gt;&gt;，字段与 1.4 相同（此处不做 deptName 拼接）。

**业务逻辑**:
1. 直接调用 OaVehicleService 的车辆分页查询并转换为 RespVO 返回。

### 2.2 创建用车申请草稿

- **路径**: POST /oa/vehicle-apply/create
- **权限**: oa:vehicle-apply:create
- **说明**: 创建用车申请草稿，草稿阶段不占用车辆预约时段。

**请求参数 (OaVehicleApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（新增时不用） |
| vehicleId | Long | 是 | @NotNull | 车辆编号 |
| startTime | LocalDateTime | 是 | @NotNull | 预计出车时间 |
| endTime | LocalDateTime | 是 | @NotNull | 预计回车时间 |
| startLocation | String | 是 | @NotBlank、@Size(max=255) | 出车地点 |
| endLocation | String | 是 | @NotBlank、@Size(max=255) | 预计回车地点 |
| reason | String | 是 | @NotBlank、@Size(max=500) | 用车事由 |
| passenger | String | 否 | @Size(max=500) | 随行人 |
| remark | String | 否 | @Size(max=500) | 备注 |
| fileUrls | List&lt;String&gt; | 否 | @Size(max=5)，元素 @NotBlank、@Size(max=2048) | 附件地址列表 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的申请编号

**业务逻辑**:
1. 校验车辆存在，并校验预计回车时间晚于出车时间（左闭右开区间），否则抛 VEHICLE_APPLY_TIME_INVALID；草稿不占用预约时段。
2. 调用 AdminUserApi 校验申请人有效。
3. 通过 OaNoRedisDAO 生成用车申请单号（YC 前缀），并校验单号唯一。
4. 创建草稿：单号回填、清空入参 id、快照车牌号 vehicleNo、绑定当前用户与所在部门，状态置为未启动（NOT_START）、还车状态置为未生效（NOT_EFFECTIVE），插入数据库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |
| 1_054_220_006 | 出车时间必须早于回车时间 |
| 1_054_220_017 | 用车申请单号已存在 |

### 2.3 更新用车申请草稿

- **路径**: PUT /oa/vehicle-apply/update
- **权限**: oa:vehicle-apply:update
- **说明**: 编辑本人未提交的用车申请草稿，允许更换车辆。

**请求参数 (OaVehicleApplySaveReqVO)**: 与 2.2 相同，id 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验申请存在并属于当前用户，否则分别抛 VEHICLE_APPLY_NOT_EXISTS / VEHICLE_APPLY_NOT_OWNER。
2. 校验申请仍为草稿（未提交），否则抛 VEHICLE_APPLY_STATUS_INVALID。
3. 重新校验车辆存在与出车/回车时间合法性。
4. 按入参更新草稿，并同步刷新车辆车牌号快照 vehicleNo。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_004 | 只能操作本人的用车申请 |
| 1_054_220_005 | 用车申请状态不允许此操作 |
| 1_054_220_006 | 出车时间必须早于回车时间 |

### 2.4 删除用车申请草稿

- **路径**: DELETE /oa/vehicle-apply/delete?id={id}
- **权限**: oa:vehicle-apply:delete
- **说明**: 删除本人未提交的用车申请草稿；已提交记录保留审批历史，不允许删除。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 申请编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验申请存在并属于当前用户。
2. 校验申请仍为草稿状态，否则抛 VEHICLE_APPLY_STATUS_INVALID。
3. 按 id 删除草稿记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_004 | 只能操作本人的用车申请 |
| 1_054_220_005 | 用车申请状态不允许此操作 |

### 2.5 提交用车申请

- **路径**: PUT /oa/vehicle-apply/submit?id={id}
- **权限**: oa:vehicle-apply:create
- **说明**: 将草稿提交进入 BPM 审批流程，提交时校验车辆空闲与时段冲突，并占用预约时段。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 申请编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验申请存在、属于当前用户且仍为草稿状态。
2. 校验关联车辆存在，且车辆状态必须为空闲（IDLE），否则抛 VEHICLE_NOT_ENABLED。
3. 检查同一车辆在预计出车/回车时段内的冲突申请数（排除自身；审批中的申请同样占用时段），存在冲突抛 VEHICLE_APPLY_TIME_CONFLICT。
4. 保存提交时的车牌号快照，并将申请状态置为审批中（RUNNING）。
5. 调用 BpmProcessInstanceApi 以流程定义 VEHICLE_APPLY 发起审批，businessKey 为申请 id。
6. 将返回的流程实例编号 processInstanceId 回写到申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |
| 1_054_220_002 | 车辆非空闲状态，不能申请用车 |
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_004 | 只能操作本人的用车申请 |
| 1_054_220_005 | 用车申请状态不允许此操作 |
| 1_054_220_007 | 该时段车辆已被预约，请调整用车时间 |

### 2.6 撤销用车申请

- **路径**: PUT /oa/vehicle-apply/cancel?id={id}
- **权限**: oa:vehicle-apply:update
- **说明**: 取消审批中的用车申请，审批结果事件回写后释放预约时段。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 申请编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验申请存在并属于当前用户。
2. 校验申请状态为审批中（RUNNING），否则抛 VEHICLE_APPLY_STATUS_INVALID。
3. 调用 BpmProcessInstanceApi 按发起人取消流程实例（取消原因：申请人取消用车申请），流程结果事件回写后释放预约时段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_004 | 只能操作本人的用车申请 |
| 1_054_220_005 | 用车申请状态不允许此操作 |

### 2.7 获得用车申请详情

- **路径**: GET /oa/vehicle-apply/get?id={id}
- **权限**: oa:vehicle-apply:query
- **说明**: 查询单条用车申请详情，拼接申请人姓名与部门名称。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 申请编号 |

**响应**: CommonResult&lt;OaVehicleApplyRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 申请单号（如 YC202609140001） |
| vehicleId | Long | 车辆编号 |
| vehicleNo | String | 车牌号（提交时快照） |
| userId | Long | 申请人用户编号 |
| deptId | Long | 申请部门编号 |
| startTime | LocalDateTime | 预计出车时间 |
| endTime | LocalDateTime | 预计回车时间 |
| startLocation | String | 出车地点 |
| endLocation | String | 预计回车地点 |
| reason | String | 用车事由 |
| passenger | String | 随行人 |
| status | Integer | 审批状态（BPM 流程实例状态） |
| returnStatus | Integer | 还车状态（0 未生效 / 1 待还车 / 2 还车中 / 3 已还车） |
| processInstanceId | String | 流程实例编号 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| userName | String | 申请人姓名（拼接 AdminUserApi） |
| deptName | String | 申请部门（拼接 DeptApi） |

**业务逻辑**:
1. 按 id 查询用车申请。
2. 转换为 RespVO，批量查询申请人昵称与部门名称并拼接。

### 2.8 获得本人的用车申请分页

- **路径**: GET /oa/vehicle-apply/page
- **权限**: oa:vehicle-apply:query
- **说明**: 分页查询当前登录用户自己的用车申请列表。

**请求参数 (OaVehicleApplyPageReqVO，继承 PageParam：pageNo、pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | PageParam 默认 1 | 页码 |
| pageSize | Integer | 否 | PageParam 默认 10 | 每页条数 |
| no | String | 否 | - | 申请单号 |
| vehicleNo | String | 否 | - | 车牌号 |
| status | Integer | 否 | @InEnum(BpmProcessInstanceStatusEnum) | 审批状态 |
| returnStatus | Integer | 否 | @InEnum(OaVehicleReturnStatusEnum) | 还车状态（0/1/2/3） |
| deptId | Long | 否 | - | 申请部门编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;OaVehicleApplyRespVO&gt;&gt;，字段与 2.7 相同（列表批量拼接 userName、deptName）。

**业务逻辑**:
1. 以当前登录用户 id 为条件分页查询本人的用车申请。
2. 批量查询申请人、部门信息并拼接展示字段。

---

## 3. 还车申请（OaVehicleReturnController）

### 3.1 创建还车申请草稿

- **路径**: POST /oa/vehicle-return/create
- **权限**: oa:vehicle-return:create
- **说明**: 针对已审批通过且待还车的用车申请创建还车申请草稿，同一用车申请允许保存多个草稿。

**请求参数 (OaVehicleReturnSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（新增时不用） |
| applyId | Long | 是 | @NotNull | 用车申请编号 |
| actualStartTime | LocalDateTime | 是 | @NotNull | 实际出车时间 |
| startLocation | String | 是 | @NotBlank、@Size(max=255) | 实际出车地点 |
| reason | String | 是 | @NotBlank、@Size(max=500) | 用车事由 |
| passenger | String | 否 | @Size(max=500) | 随行人 |
| actualReturnTime | LocalDateTime | 是 | @NotNull、@PastOrPresent | 实际回车时间（不能晚于当前时间） |
| returnLocation | String | 是 | @NotBlank、@Size(max=255) | 实际回车地点 |
| remark | String | 否 | @Size(max=500) | 还车说明 |
| fileUrls | List&lt;String&gt; | 否 | @Size(max=5)，元素 @NotBlank、@Size(max=2048) | 附件地址列表 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的还车申请编号

**业务逻辑**:
1. 校验关联的用车申请存在。
2. 校验原用车申请属于当前用户，且状态为审批通过（APPROVE）且还车状态为待还车（PENDING_RETURN），否则分别抛 VEHICLE_RETURN_NOT_OWNER / VEHICLE_RETURN_STATUS_INVALID。
3. 校验实际回车时间：必须填写实际出车时间，且回车时间不早于出车时间、不晚于当前时间，否则抛 VEHICLE_RETURN_TIME_INVALID。
4. 通过 OaNoRedisDAO 生成还车申请单号（HC 前缀）并校验唯一。
5. 创建草稿：从原用车申请继承车辆编号与申请部门，绑定当前用户，状态置为未启动（NOT_START），插入数据库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_010 | 只能操作本人的还车申请 |
| 1_054_220_011 | 当前申请状态不允许还车操作 |
| 1_054_220_014 | 请填写实际出车时间，回车时间不能早于实际出车时间或晚于当前时间 |
| 1_054_220_018 | 还车申请单号已存在 |

### 3.2 更新还车申请草稿

- **路径**: PUT /oa/vehicle-return/update
- **权限**: oa:vehicle-return:update
- **说明**: 编辑本人未提交的还车申请草稿，允许重新选择关联的用车申请。

**请求参数 (OaVehicleReturnSaveReqVO)**: 与 3.1 相同，id 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验还车申请存在，否则抛 VEHICLE_RETURN_NOT_EXISTS。
2. 校验属于当前用户，且仍为草稿状态。
3. 校验本次选择的用车申请存在，并校验其归属与待还车状态。
4. 重新校验实际出车/回车时间合法性。
5. 按入参更新草稿，并根据新选的用车申请刷新车辆编号、用户与部门归属。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_009 | 还车申请不存在 |
| 1_054_220_010 | 只能操作本人的还车申请 |
| 1_054_220_011 | 当前申请状态不允许还车操作 |
| 1_054_220_014 | 请填写实际出车时间，回车时间不能早于实际出车时间或晚于当前时间 |

### 3.3 删除还车申请草稿

- **路径**: DELETE /oa/vehicle-return/delete?id={id}
- **权限**: oa:vehicle-return:delete
- **说明**: 删除本人未提交的还车申请草稿，原用车申请保持待还车状态。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 还车申请编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验还车申请存在。
2. 校验属于当前用户，且仍为草稿状态（已提交记录保留审批历史，不允许删除）。
3. 按 id 删除草稿记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_009 | 还车申请不存在 |
| 1_054_220_010 | 只能操作本人的还车申请 |
| 1_054_220_011 | 当前申请状态不允许还车操作 |

### 3.4 提交还车申请

- **路径**: PUT /oa/vehicle-return/submit?id={id}
- **权限**: oa:vehicle-return:create
- **说明**: 将还车申请草稿提交进入 BPM 审批流程，原用车申请同步切换为还车中。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 还车申请编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验还车申请存在、属于当前用户且仍为草稿状态。
2. 校验关联的原用车申请存在，且归属当前用户、状态为审批通过且还车状态为待还车。
3. 重新校验实际回车时间（不早于实际出车时间、不晚于当前时间）。
4. 原用车申请还车状态由待还车（PENDING_RETURN）按原状态 CAS 更新为还车中（RETURNING），期间车辆仍被占用；更新失败抛 VEHICLE_RETURN_STATUS_INVALID，防止多个还车草稿同时提交成功。
5. 将还车申请状态置为审批中（RUNNING）。
6. 调用 BpmProcessInstanceApi 以流程定义 VEHICLE_RETURN 发起审批，businessKey 为还车申请 id，并回写流程实例编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_009 | 还车申请不存在 |
| 1_054_220_010 | 只能操作本人的还车申请 |
| 1_054_220_011 | 当前申请状态不允许还车操作 |
| 1_054_220_014 | 请填写实际出车时间，回车时间不能早于实际出车时间或晚于当前时间 |

### 3.5 取消还车申请

- **路径**: PUT /oa/vehicle-return/cancel?id={id}
- **权限**: oa:vehicle-return:update
- **说明**: 取消审批中的还车申请，流程结果事件将原用车申请恢复为待还车。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 还车申请编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定 true

**业务逻辑**:
1. 校验还车申请存在并属于当前用户。
2. 校验还车申请状态为审批中（RUNNING），否则抛 VEHICLE_RETURN_STATUS_INVALID。
3. 调用 BpmProcessInstanceApi 按发起人取消流程实例（取消原因：申请人取消还车申请），审批结果事件将原用车申请恢复为待还车。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_220_009 | 还车申请不存在 |
| 1_054_220_010 | 只能操作本人的还车申请 |
| 1_054_220_011 | 当前申请状态不允许还车操作 |

### 3.6 获得还车申请详情

- **路径**: GET /oa/vehicle-return/get?id={id}
- **权限**: oa:vehicle-return:query
- **说明**: 查询单条还车申请详情，拼接申请人、部门及原用车申请信息。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam 必填 | 还车申请编号 |

**响应**: CommonResult&lt;OaVehicleReturnRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 还车申请单号（如 HC202609140001） |
| applyId | Long | 用车申请编号 |
| vehicleId | Long | 车辆编号 |
| userId | Long | 申请人用户编号 |
| deptId | Long | 申请部门编号 |
| actualStartTime | LocalDateTime | 实际出车时间 |
| startLocation | String | 实际出车地点 |
| reason | String | 用车事由 |
| passenger | String | 随行人 |
| actualReturnTime | LocalDateTime | 实际回车时间 |
| returnLocation | String | 实际回车地点 |
| status | Integer | 审批状态（BPM 流程实例状态） |
| processInstanceId | String | 流程实例编号 |
| remark | String | 还车说明 |
| createTime | LocalDateTime | 创建时间 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| userName | String | 申请人姓名（拼接 AdminUserApi） |
| deptName | String | 申请部门（拼接 DeptApi） |
| applyNo | String | 用车申请单号（拼接原用车申请） |
| vehicleNo | String | 车牌号（拼接原用车申请） |

**业务逻辑**:
1. 按 id 查询还车申请。
2. 转换为 RespVO，批量查询申请人昵称、部门名称，并根据 applyId 批量查询原用车申请，拼接 applyNo 与 vehicleNo。

### 3.7 获得本人还车申请分页

- **路径**: GET /oa/vehicle-return/page
- **权限**: oa:vehicle-return:query
- **说明**: 分页查询当前登录用户自己的还车申请列表。

**请求参数 (OaVehicleReturnPageReqVO，继承 PageParam：pageNo、pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | PageParam 默认 1 | 页码 |
| pageSize | Integer | 否 | PageParam 默认 10 | 每页条数 |
| no | String | 否 | - | 还车申请单号 |
| applyId | Long | 否 | - | 用车申请编号 |
| status | Integer | 否 | @InEnum(BpmProcessInstanceStatusEnum) | 审批状态 |
| vehicleNo | String | 否 | - | 车牌号 |
| applyNo | String | 否 | - | 用车申请单号 |
| deptId | Long | 否 | - | 申请部门编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;OaVehicleReturnRespVO&gt;&gt;，字段与 3.6 相同（列表批量拼接 userName、deptName、applyNo、vehicleNo）。

**业务逻辑**:
1. 以当前登录用户 id 为条件分页查询本人的还车申请。
2. 批量查询申请人、部门及原用车申请信息并拼接展示字段。

---

## 4. 车辆管理域错误码总表（1_054_220_XXX）

| 错误码 | 说明 |
|-------|------|
| 1_054_220_000 | 车辆不存在 |
| 1_054_220_001 | 车牌号已存在 |
| 1_054_220_002 | 车辆非空闲状态，不能申请用车 |
| 1_054_220_003 | 用车申请不存在 |
| 1_054_220_004 | 只能操作本人的用车申请 |
| 1_054_220_005 | 用车申请状态不允许此操作 |
| 1_054_220_006 | 出车时间必须早于回车时间 |
| 1_054_220_007 | 该时段车辆已被预约，请调整用车时间 |
| 1_054_220_009 | 还车申请不存在 |
| 1_054_220_010 | 只能操作本人的还车申请 |
| 1_054_220_011 | 当前申请状态不允许还车操作 |
| 1_054_220_014 | 请填写实际出车时间，回车时间不能早于实际出车时间或晚于当前时间 |
| 1_054_220_017 | 用车申请单号已存在 |
| 1_054_220_018 | 还车申请单号已存在 |
| 1_054_220_019 | 车辆已有业务单据引用，不能删除 |
