# 考勤管理接口 (HrmAttendanceGroupController / HrmAttendanceClockController / HrmAttendanceLeaveController / HrmAttendanceHolidayController / HrmAttendanceStatisticsController)

> HRM 考勤域管理端接口：考勤组（班次/打卡点/WiFi/扣款规则配置与员工匹配）、打卡记录（补录与导出）、请假记录（查询与导出，创建/取消走员工自助门户对接 BPM 审批）、考勤节假日维护，以及每日明细、月度汇总、月度打卡概况等考勤统计。

## 接口路径前缀

- /hrm/attendance/group  (Controller: HrmAttendanceGroupController)
- /hrm/attendance/clock  (Controller: HrmAttendanceClockController)
- /hrm/attendance/leave  (Controller: HrmAttendanceLeaveController)
- /hrm/attendance/holiday  (Controller: HrmAttendanceHolidayController)
- /hrm/attendance/statistics  (Controller: HrmAttendanceStatisticsController)

---

## 1. 考勤组管理（/hrm/attendance/group）

### 1.1 创建考勤组

- **路径**: POST /hrm/attendance/group/create
- **权限**: hrm:attendance:group:create
- **说明**: 创建考勤组，配置班次、特殊日期、打卡地点、WiFi 与扣款规则，并接管部门/员工适用范围。

**请求参数 (HrmAttendanceGroupSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 考勤组编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=50) | 考勤组名称 |
| openWifiCard | Boolean | 是 | @NotNull | 是否启用 WiFi 打卡 |
| openPointCard | Boolean | 是 | @NotNull | 是否启用定位打卡 |
| rest | Boolean | 是 | @NotNull | 是否法定节假日休息 |
| specialDates | List\<SpecialDate\> | 是 | @NotNull、@Valid | 特殊日期设置数组 |
| deptIds | List\<Long\> | 是 | @NotNull（元素 @NotNull） | 适用部门编号数组 |
| employeeIds | List\<Long\> | 是 | @NotNull（元素 @NotNull） | 适用员工编号数组 |
| shifts | List\<Shift\> | 是 | @NotEmpty、@Valid | 班次配置 |
| points | List\<Point\> | 是 | @NotNull、@Valid | 打卡地点 |
| wifis | List\<Wifi\> | 是 | @NotNull、@Valid | 打卡 WiFi |
| deductRule | DeductRule | 是 | @NotNull、@Valid | 扣款规则 |

嵌套对象 **SpecialDate**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| type | Integer | 是 | @NotNull、@InEnum(HrmAttendanceHolidayTypeEnum) | 日期类型：1 上班（补班）、2 休息 |
| date | LocalDateTime | 是 | @NotNull | 特殊日期 |

嵌套对象 **Shift**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| weeks | List\<Integer\> | 是 | @NotEmpty（元素 @NotNull、@Min(1)、@Max(7)） | 工作日数组（周一至周日 1~7），不同班次不可重复 |
| startTime | LocalTime | 是 | @NotNull（HH:mm） | 上班时间 |
| endTime | LocalTime | 是 | @NotNull（HH:mm） | 下班时间 |
| clockInStartTime | LocalTime | 是 | @NotNull（HH:mm） | 上班打卡开始时间 |
| clockInEndTime | LocalTime | 是 | @NotNull（HH:mm） | 上班打卡结束时间 |
| clockOutStartTime | LocalTime | 是 | @NotNull（HH:mm） | 下班打卡开始时间 |
| clockOutEndTime | LocalTime | 是 | @NotNull（HH:mm） | 下班打卡结束时间 |
| restStartTime | LocalTime | 是 | @NotNull（HH:mm） | 休息开始时间 |
| restEndTime | LocalTime | 是 | @NotNull（HH:mm） | 休息结束时间 |
| excludeRestTime | Boolean | 是 | @NotNull | 休息时间是否不计入工作时长 |

嵌套对象 **Point**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 是 | @NotBlank、@Size(max=50) | 地点名称 |
| address | String | 是 | @NotBlank、@Size(max=255) | 定位地址 |
| latitude | BigDecimal | 是 | @NotNull、@DecimalMin(-90)、@DecimalMax(90) | 纬度 |
| longitude | BigDecimal | 是 | @NotNull、@DecimalMin(-180)、@DecimalMax(180) | 经度 |
| radius | Integer | 是 | @NotNull、@Positive | 有效打卡半径（米），仅允许 100~1000（间隔 100）或 2000、3000 |

嵌套对象 **Wifi**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ssid | String | 是 | @NotBlank、@Size(max=50) | WiFi 名称 |
| mac | String | 是 | @NotBlank、@Pattern（MAC 地址格式） | MAC 地址 |

嵌套对象 **DeductRule**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| lateMethod | Integer | 是 | @NotNull、@InEnum(HrmAttendanceLateEarlyDeductMethodEnum) | 迟到扣款方式：1 每月固定、2 按分钟、3 按次数 |
| lateDeductMoney | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@Digits(8,2) | 迟到扣款金额 |
| earlyMethod | Integer | 是 | @NotNull、@InEnum(HrmAttendanceLateEarlyDeductMethodEnum) | 早退扣款方式：1 每月固定、2 按分钟、3 按次数 |
| earlyDeductMoney | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@Digits(8,2) | 早退扣款金额 |
| absenteeismMethod | Integer | 是 | @NotNull、@InEnum(HrmAttendanceAbsenteeismDeductMethodEnum) | 旷工扣款方式：1 按旷工天数 |
| absenteeismDeductMoney | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@Digits(8,2) | 旷工扣款金额 |
| misscardMethod | Integer | 是 | @NotNull、@InEnum(HrmAttendanceMisscardDeductMethodEnum) | 缺卡扣款方式：1 按缺卡次数 |
| misscardDeductMoney | BigDecimal | 是 | @NotNull、@DecimalMin(0)、@Digits(8,2) | 缺卡扣款金额 |

类级校验（@AssertTrue）：不同班次不能配置重复工作日；班次上下班、打卡窗口或休息时间配置合法（打卡窗口须覆盖对应应打卡时间，休息时间须落在班次范围内）；特殊日期不能重复；至少选择一个适用部门或员工；至少启用定位打卡或 WiFi 打卡之一；启用定位打卡时打卡地点不能为空；启用 WiFi 打卡时打卡 WiFi 不能为空。

**响应**: CommonResult\<Long\> — 考勤组编号

**业务逻辑**:
1. 校验考勤组名称唯一（同一名称不允许重复）。
2. 校验适用部门存在（DeptApi.validateDeptList）、适用员工存在。
3. 转换为 DO 插入考勤组，特殊日期统一取当日 0 点，`defaultStatus` 固定为 false。
4. 接管考勤组适用范围：部门范围扩展到全部子部门并关联其下员工，从其它考勤组的部门/员工范围中移除冲突范围，保证同一部门或员工只归属一个考勤组。
5. 记录操作日志（@LogRecord）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_007 | 考勤名称已存在 |

### 1.2 修改考勤组

- **路径**: PUT /hrm/attendance/group/update
- **权限**: hrm:attendance:group:update
- **说明**: 修改考勤组基础配置并重新接管适用范围。

**请求参数 (HrmAttendanceGroupSaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验考勤组存在。
2. 校验考勤组名称唯一（排除自身）。
3. 校验适用部门、员工存在。
4. 更新考勤组，特殊日期统一取当日 0 点。
5. 接管考勤组适用范围（同 1.1 第 4 步）。
6. 记录操作日志（含修改前后差量对比）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_002 | 考勤组不存在 |
| 1_050_300_007 | 考勤名称已存在 |

### 1.3 删除考勤组

- **路径**: DELETE /hrm/attendance/group/delete?id={id}
- **权限**: hrm:attendance:group:delete
- **说明**: 删除考勤组，默认考勤组不允许删除。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 考勤组编号 |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验考勤组存在，且不是默认考勤组（defaultStatus=true 时拒绝删除）。
2. 删除考勤组。
3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_002 | 考勤组不存在 |
| 1_050_300_008 | 默认考勤配置不能删除 |

### 1.4 获得考勤组

- **路径**: GET /hrm/attendance/group/get?id={id}
- **权限**: hrm:attendance:group:query
- **说明**: 获得考勤组详情，拼接适用部门名称与员工名称。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 考勤组编号 |

**响应**: CommonResult\<HrmAttendanceGroupRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 考勤组编号 |
| name | String | 名称 |
| openWifiCard | Boolean | 是否启用 WiFi 打卡 |
| openPointCard | Boolean | 是否启用定位打卡 |
| rest | Boolean | 是否法定节假日休息 |
| defaultStatus | Boolean | 是否默认配置 |
| specialDates | List\<SpecialDate\> | 特殊日期设置（type + date） |
| deptIds | List\<Long\> | 部门范围 |
| deptNames | List\<String\> | 适用部门名称（与 deptIds 顺序对应） |
| employeeIds | List\<Long\> | 员工范围 |
| employeeNames | List\<String\> | 适用员工名称（与 employeeIds 顺序对应） |
| shifts | List\<Shift\> | 班次配置（结构同 1.1 的 Shift） |
| points | List\<Point\> | 打卡地点（结构同 1.1 的 Point） |
| wifis | List\<Wifi\> | 打卡 WiFi（结构同 1.1 的 Wifi） |
| deductRule | DeductRule | 扣款规则（结构同 1.1 的 DeductRule） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询考勤组。
2. 批量查询部门名称（DeptApi）与员工名称，拼入 deptNames / employeeNames。

### 1.5 获得员工所在考勤组

- **路径**: GET /hrm/attendance/group/my?employeeId={employeeId}
- **权限**: hrm:attendance:group:query
- **说明**: 匹配员工当前归属的考勤组，返回详情（含部门/员工名称）。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| employeeId | Long | 是 | @Parameter(required=true) | 员工编号 |

**响应**: CommonResult\<HrmAttendanceGroupRespVO\> — 结构同 1.4；员工未匹配到考勤组时返回 null

**业务逻辑**:
1. 校验员工存在，不存在时返回 null。
2. 按顺序匹配员工考勤组：优先匹配考勤组显式配置的员工，其次按员工当前部门到上级部门的层级顺序匹配部门范围，最后回退到默认考勤组。
3. 拼接部门名称与员工名称。

### 1.6 获得考勤组分页

- **路径**: GET /hrm/attendance/group/page
- **权限**: hrm:attendance:group:query
- **说明**: 分页查询考勤组，拼接部门/员工名称。

**请求参数 (HrmAttendanceGroupPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 考勤组名称，模糊匹配 |
| defaultStatus | Boolean | 否 | - | 是否默认考勤组 |

**响应**: CommonResult\<PageResult\<HrmAttendanceGroupRespVO\>\> — list 元素结构同 1.4，另含 total 总条数

**业务逻辑**:
1. 按名称、是否默认组条件分页查询。
2. 批量拼接部门名称与员工名称。

### 1.7 获得考勤组精简列表

- **路径**: GET /hrm/attendance/group/simple-list
- **权限**: hrm:attendance:group:query
- **说明**: 获得全部考勤组精简列表（下拉选择器用）。

**请求参数**: 无

**响应**: CommonResult\<List\<HrmAttendanceGroupRespVO\>\> — 仅填充 id、name 两个字段

**业务逻辑**:
1. 查询全部考勤组，按默认组优先、编号升序排序。
2. 转换为仅含 id、name 的精简 RespVO 列表。

---

## 2. 打卡记录管理（/hrm/attendance/clock）

### 2.1 创建打卡记录（管理员补录）

- **路径**: POST /hrm/attendance/clock/create
- **权限**: hrm:attendance:clock:create
- **说明**: 管理员手工补录打卡记录，来源固定为手工录入，状态由后端计算。

**请求参数 (HrmAttendanceClockSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 打卡记录编号（创建时不传） |
| employeeId | Long | 是 | @NotNull | 打卡员工编号 |
| clockTime | LocalDateTime | 是 | @NotNull | 实际打卡时间 |
| type | Integer | 是 | @NotNull、@InEnum(HrmAttendanceClockTypeEnum) | 打卡类型：1 上班打卡、2 下班打卡 |
| attendanceTime | LocalDateTime | 是 | @NotNull | 应打卡时间（班次上/下班时间） |
| address | String | 否 | @Size(max=255) | 打卡地址 |
| longitude | BigDecimal | 否 | @DecimalMin(-180)、@DecimalMax(180) | 经度 |
| latitude | BigDecimal | 否 | @DecimalMin(-90)、@DecimalMax(90) | 纬度 |
| ssid | String | 否 | @Size(max=50) | WiFi 名称 |
| mac | String | 否 | @Size(max=50) | WiFi MAC 地址 |
| remark | String | 否 | @Size(max=255) | 备注（如手工补卡原因） |

**响应**: CommonResult\<Long\> — 打卡记录编号

**业务逻辑**:
1. 校验员工存在。
2. 校验补录时间合法：应打卡时间必须等于员工当日班次（按应打卡日期或前一日期归属跨日班次）的上班或下班时间，且实际打卡时间必须落在对应的上班/下班打卡窗口闭区间内；休息日或班次时间不完整不允许补录。
3. 创建打卡记录，来源固定为手工录入（MANUAL）、打卡阶段为第一段。
4. 打卡状态由后端计算：上班打卡晚于应打卡时间为迟到，下班打卡早于应打卡时间为早退，否则正常。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_033 | 应打卡时间或实际打卡时间不在员工班次窗口内 |

### 2.2 修改打卡记录

- **路径**: PUT /hrm/attendance/clock/update
- **权限**: hrm:attendance:clock:update
- **说明**: 修改手工录入的打卡记录并重算状态，非手工录入的记录（如手机端打卡）禁止修改。

**请求参数 (HrmAttendanceClockSaveReqVO)**: 同 2.1（id 必传）

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验打卡记录存在，且来源为手工录入（MANUAL），否则拒绝修改。
2. 校验员工存在。
3. 校验应打卡/实际打卡时间位于员工班次窗口内（同 2.1 第 2 步）。
4. 更新打卡记录，来源保持手工录入，并按打卡时间与应打卡时间重新计算状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_003 | 打卡记录不存在 |
| 1_050_300_028 | 只有手工录入的打卡记录可以修改或删除 |
| 1_050_300_033 | 应打卡时间或实际打卡时间不在员工班次窗口内 |

### 2.3 删除打卡记录

- **路径**: DELETE /hrm/attendance/clock/delete?id={id}
- **权限**: hrm:attendance:clock:delete
- **说明**: 删除单条手工录入的打卡记录。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 打卡记录编号 |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验打卡记录存在且来源为手工录入。
2. 删除打卡记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_003 | 打卡记录不存在 |
| 1_050_300_028 | 只有手工录入的打卡记录可以修改或删除 |

### 2.4 批量删除打卡记录

- **路径**: DELETE /hrm/attendance/clock/delete-list?ids={ids}
- **权限**: hrm:attendance:clock:delete
- **说明**: 批量删除手工录入的打卡记录，任一记录不满足条件则整体失败（事务回滚）。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List\<Long\> | 是 | @NotEmpty | 打卡记录编号列表（逗号分隔） |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验编号列表非空，且全部记录存在（数量不一致即报错），避免批量删除部分成功。
2. 逐条校验均为手工录入的打卡记录。
3. 事务内批量删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_003 | 打卡记录不存在 |
| 1_050_300_028 | 只有手工录入的打卡记录可以修改或删除 |

### 2.5 获得打卡记录

- **路径**: GET /hrm/attendance/clock/get?id={id}
- **权限**: hrm:attendance:clock:query
- **说明**: 获得打卡记录详情，拼接员工与部门信息。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 打卡记录编号 |

**响应**: CommonResult\<HrmAttendanceClockRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 打卡记录编号 |
| employeeId | Long | 打卡员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号（来自员工档案） |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| clockTime | LocalDateTime | 实际打卡时间 |
| type | Integer | 打卡类型（字典 hrm_attendance_clock_type：1 上班、2 下班） |
| attendanceTime | LocalDateTime | 应打卡时间 |
| sourceType | Integer | 打卡来源（字典 hrm_attendance_clock_source：1 手机端、2 手工录入） |
| status | Integer | 打卡状态（字典 hrm_attendance_clock_status：0 正常、1 迟到、2 早退、3 缺卡） |
| stage | Integer | 打卡阶段（1 第一段） |
| address | String | 打卡地址 |
| longitude | BigDecimal | 经度 |
| latitude | BigDecimal | 纬度 |
| ssid | String | WiFi 名称 |
| mac | String | WiFi MAC 地址 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询打卡记录，不存在返回 null。
2. 批量查询员工信息（姓名、工号、部门编号、岗位）与部门名称并拼接。

### 2.6 获得员工实际班次和允许打卡时间

- **路径**: GET /hrm/attendance/clock/get-shift
- **权限**: hrm:attendance:clock:create 或 hrm:attendance:clock:update（hasAnyPermissions）
- **说明**: 解析员工指定考勤时间的实际班次，并换算为具体的可打卡时间窗口。

**请求参数 (HrmAttendanceClockShiftReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| attendanceTime | LocalDateTime | 是 | @NotNull（yyyy-MM-dd HH:mm:ss） | 考勤时间 |

**响应**: CommonResult\<HrmAttendanceClockShiftRespVO\>；班次缺失或窗口解析失败时返回 null

| 字段 | 类型 | 说明 |
|-----|------|------|
| startTime | LocalDateTime | 上班时间（已换算为具体日期时间） |
| endTime | LocalDateTime | 下班时间（跨日班次为次日时间） |
| clockInStartTime | LocalDateTime | 上班打卡开始时间 |
| clockInEndTime | LocalDateTime | 上班打卡结束时间 |
| clockOutStartTime | LocalDateTime | 下班打卡开始时间 |
| clockOutEndTime | LocalDateTime | 下班打卡结束时间 |

**业务逻辑**:
1. 匹配员工所在考勤组，并结合特殊日期、法定节假日、每周班次解析考勤日实际班次（特殊日期优先于法定节假日，法定节假日优先于每周班次）。
2. 将班次的上/下班时分换算为考勤日对应的实际日期时间范围（支持跨日班次）。
3. 以上/下班应打卡时间为锚点，分别解析可能跨日的上班打卡窗口和下班打卡窗口。
4. 班次时间或打卡窗口不完整时返回 null。

### 2.7 获得打卡记录分页

- **路径**: GET /hrm/attendance/clock/page
- **权限**: hrm:attendance:clock:query
- **说明**: 按员工、部门、打卡类型/状态/来源、时间范围等条件分页查询打卡记录。

**请求参数 (HrmAttendanceClockPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| search | String | 否 | - | 员工姓名或工号，模糊匹配 |
| employeeId | Long | 否 | - | 员工编号 |
| deptIds | List\<Long\> | 否 | - | 部门编号数组 |
| type | Integer | 否 | @InEnum(HrmAttendanceClockTypeEnum) | 打卡类型：1 上班、2 下班 |
| status | Integer | 否 | @InEnum(HrmAttendanceClockStatusEnum) | 打卡状态：0 正常、1 迟到、2 早退、3 缺卡 |
| sourceTypes | List\<Integer\> | 否 | @InEnum(HrmAttendanceClockSourceEnum) | 来源类型数组：1 手机端、2 手工录入 |
| address | String | 否 | - | 打卡地点，模糊匹配 |
| attendanceTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 应打卡（上班）日期范围 |
| clockTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 实际打卡时间范围 |

**响应**: CommonResult\<PageResult\<HrmAttendanceClockRespVO\>\> — list 元素结构同 2.5，另含 total 总条数

**业务逻辑**:
1. 传入 search、deptIds 或 employeeId 时，先按姓名/工号关键词与部门解析匹配的员工编号集合。
2. 员工集合为空时直接返回空页。
3. 按条件分页查询打卡记录。
4. 批量拼接员工信息与部门名称。

### 2.8 导出打卡记录

- **路径**: GET /hrm/attendance/clock/export-excel
- **权限**: hrm:attendance:clock:export
- **说明**: 按分页相同条件导出全部打卡记录 Excel（不分页）。

**请求参数 (HrmAttendanceClockPageReqVO)**: 同 2.7（pageSize 强制置为不分页）

**响应**: Excel 文件流 — 文件名「打卡记录.xls」，列：记录编号、员工编号、员工姓名、工号、部门、岗位、打卡类型、应打卡时间、打卡时间、打卡状态、来源、地点、备注

**业务逻辑**:
1. 按查询条件解析员工编号集合并查询全部记录（不分页）。
2. 拼接员工与部门信息。
3. 通过 ExcelUtils 写出 Excel，并记录导出操作日志（@ApiAccessLog EXPORT）。

---

## 3. 请假管理（/hrm/attendance/leave）

> 请假的创建与取消由员工自助门户发起（对接 BPM 审批流程 hrm_attendance_leave），管理端仅提供查询与导出。

### 3.1 获得请假

- **路径**: GET /hrm/attendance/leave/get?id={id}
- **权限**: hrm:attendance:leave:query 或 bpm:process-instance:query 或 bpm:task:query（hasAnyPermissions，BPM 审批详情场景复用）
- **说明**: 获得请假记录详情，拼接员工与部门信息。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 请假记录编号 |

**响应**: CommonResult\<HrmAttendanceLeaveRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 请假记录编号 |
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号（来自员工档案） |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| type | String | 请假类型（字典 hrm_attendance_leave_type，如事假、病假） |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| day | BigDecimal | 请假天数 |
| reason | String | 请假事由 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| approvalStatus | Integer | 审批状态（BPM 流程实例状态：审批中/通过/不通过/已取消） |
| processInstanceId | String | BPM 流程实例编号 |
| approvalTime | LocalDateTime | 审批时间 |
| approvalReason | String | 审批意见 |

**业务逻辑**:
1. 按编号查询请假记录。
2. 批量查询员工信息（姓名、工号、部门编号、岗位）与部门名称并拼接。

### 3.2 获得请假分页

- **路径**: GET /hrm/attendance/leave/page
- **权限**: hrm:attendance:leave:query
- **说明**: 按员工、部门、请假类型、审批状态、时间范围分页查询请假记录。

**请求参数 (HrmAttendanceLeavePageReqVO，继承 SortablePageParam，支持排序)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo / pageSize | Integer | 否 | - | 分页参数 |
| employeeId | Long | 否 | - | 员工编号 |
| deptIds | List\<Long\> | 否 | - | 部门编号数组 |
| employeeKeyword | String | 否 | - | 员工姓名或工号，模糊匹配 |
| types | List\<String\> | 否 | - | 请假类型数组（如事假、病假） |
| startTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 请假开始时间范围 |
| approvalStatus | Integer | 否 | - | 审批状态 |

**响应**: CommonResult\<PageResult\<HrmAttendanceLeaveRespVO\>\> — list 元素结构同 3.1，另含 total 总条数

**业务逻辑**:
1. 传入 employeeId、deptIds 或 employeeKeyword 时，先解析匹配的员工编号集合。
2. 员工集合为空时直接返回空页。
3. 按条件分页查询请假记录。
4. 批量拼接员工信息与部门名称。

### 3.3 导出请假

- **路径**: GET /hrm/attendance/leave/export-excel
- **权限**: hrm:attendance:leave:export
- **说明**: 按分页相同条件导出全部请假记录 Excel（不分页）。

**请求参数 (HrmAttendanceLeavePageReqVO)**: 同 3.2（pageSize 强制置为不分页）

**响应**: Excel 文件流 — 文件名「请假记录.xls」，列：记录编号、员工编号、员工姓名、工号、部门、岗位、请假类型、开始时间、结束时间、请假天数、请假事由、备注、创建时间

**业务逻辑**:
1. 按查询条件解析员工编号集合并查询全部请假记录（不分页）。
2. 拼接员工与部门信息。
3. 通过 ExcelUtils 写出 Excel，并记录导出操作日志（@ApiAccessLog EXPORT）。

---

## 4. 考勤节假日管理（/hrm/attendance/holiday）

### 4.1 创建考勤节假日

- **路径**: POST /hrm/attendance/holiday/create
- **权限**: hrm:attendance:holiday:create
- **说明**: 配置法定节假日/补班日，同一天仅允许一条配置。

**请求参数 (HrmAttendanceHolidaySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 节假日编号（创建时不传） |
| date | LocalDateTime | 是 | @NotNull | 节假日日期（统一取当日 0 点存储） |
| type | Integer | 是 | @NotNull、@InEnum(HrmAttendanceHolidayTypeEnum) | 节假日类型：1 上班（补班）、2 休息 |

**响应**: CommonResult\<Long\> — 节假日编号

**业务逻辑**:
1. 日期取当日 0 点，校验同日期未配置过节假日。
2. 插入节假日配置。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_029 | 该日期已配置为考勤节假日 |

### 4.2 修改考勤节假日

- **路径**: PUT /hrm/attendance/holiday/update
- **权限**: hrm:attendance:holiday:update
- **说明**: 修改节假日日期或类型。

**请求参数 (HrmAttendanceHolidaySaveReqVO)**: 同 4.1（id 必传）

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验节假日配置存在。
2. 日期取当日 0 点，校验同日期未配置过（排除自身）。
3. 更新节假日配置。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_006 | 考勤节假日不存在 |
| 1_050_300_029 | 该日期已配置为考勤节假日 |

### 4.3 删除考勤节假日

- **路径**: DELETE /hrm/attendance/holiday/delete?id={id}
- **权限**: hrm:attendance:holiday:delete
- **说明**: 删除节假日配置。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 考勤节假日编号 |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验节假日配置存在。
2. 删除节假日配置。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_300_006 | 考勤节假日不存在 |

### 4.4 获得考勤节假日

- **路径**: GET /hrm/attendance/holiday/get?id={id}
- **权限**: hrm:attendance:holiday:query
- **说明**: 获得节假日配置详情。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @Parameter(required=true) | 考勤节假日编号 |

**响应**: CommonResult\<HrmAttendanceHolidayRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| date | LocalDateTime | 节假日日期 |
| type | Integer | 考勤假期类型：1 上班、2 休息 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询节假日配置并转换为 RespVO（不存在时返回 null）。

### 4.5 检查日期是否为考勤节假日

- **路径**: GET /hrm/attendance/holiday/check?day={day}
- **权限**: hrm:attendance:holiday:query
- **说明**: 查询指定日期是否配置了节假日，用于考勤日历展示。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| day | LocalDateTime | 是 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 待检查日期 |

**响应**: CommonResult\<HrmAttendanceHolidayRespVO\> — 结构同 4.4；未配置时返回 null

**业务逻辑**:
1. 将日期归一为当日 0 点后查询节假日配置。

### 4.6 获得考勤节假日分页

- **路径**: GET /hrm/attendance/holiday/page
- **权限**: hrm:attendance:holiday:query
- **说明**: 按日期范围、类型分页查询节假日配置。

**请求参数 (HrmAttendanceHolidayPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo / pageSize | Integer | 否 | - | 分页参数 |
| date | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 日期范围 |
| type | Integer | 否 | @InEnum(HrmAttendanceHolidayTypeEnum) | 节假日类型：1 上班、2 休息 |

**响应**: CommonResult\<PageResult\<HrmAttendanceHolidayRespVO\>\> — list 元素结构同 4.4，另含 total 总条数

**业务逻辑**:
1. 按日期范围与类型分页查询节假日配置。

---

## 5. 考勤统计（/hrm/attendance/statistics）

> 统计接口为实时计算：按员工匹配考勤组，结合特殊日期/法定节假日/每周班次解析每日排班，再基于打卡记录与已通过（APPROVE）的请假记录逐日计算考勤结果。

### 5.1 查询员工每日打卡明细

- **路径**: GET /hrm/attendance/statistics/daily-detail
- **权限**: hrm:attendance:clock:query
- **说明**: 查询员工指定考勤日的排班、打卡、迟到/早退/缺卡/旷工/请假明细及考勤结果。

**请求参数 (HrmAttendanceDailyDetailReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| attendanceTime | LocalDateTime | 是 | @NotNull（yyyy-MM-dd HH:mm:ss） | 考勤日期 |

**响应**: CommonResult\<HrmAttendanceDailyDetailRespVO\>；员工不存在时返回 null

| 字段 | 类型 | 说明 |
|-----|------|------|
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| attendanceTime | LocalDateTime | 考勤日期（当日 0 点） |
| shiftName | String | 班次（格式「上班时间-下班时间」） |
| scheduled | Boolean | 是否排班工作日 |
| requiredClockCount | Integer | 应打卡次数（工作日 2，休息日 0） |
| scheduledMinutes | Integer | 排班分钟数（扣除休息时间） |
| misscardCount | Integer | 缺卡次数 |
| absenteeism | Boolean | 是否旷工 |
| absenteeismMinutes | Integer | 旷工分钟数 |
| absenteeismDays | BigDecimal | 旷工天数 |
| leaveStatus | Boolean | 是否请假 |
| leaveMinutes | Integer | 请假分钟数 |
| leaveDays | BigDecimal | 请假天数 |
| attendanceResult | String | 考勤结果（正常/休息/未排班/未到日期/请假/请假 N 天/旷工/旷工 N 天/缺卡 N 次/迟到 N 分钟/早退 N 分钟/待打卡，多个以「 / 」拼接） |
| clockCount | Integer | 实际打卡次数（按去重打卡类型计） |
| lateCount | Integer | 迟到次数 |
| lateMinutes | Integer | 迟到分钟 |
| earlyCount | Integer | 早退次数 |
| earlyMinutes | Integer | 早退分钟 |
| clockList | List\<HrmAttendanceClockRespVO\> | 打卡记录列表（按打卡时间升序） |

**业务逻辑**:
1. 查询员工，不存在返回 null。
2. 查询员工考勤组及前一日至当日两天的实际班次，用于识别跨日班次的业务日期归属。
3. 查询日期前后的打卡记录，并按应打卡时间与班次匹配归集到正确的业务日。
4. 查询覆盖当前班次时间范围（无班次时为当日全天）的有效请假记录（审批通过）。
5. 计算单日明细：排班分钟扣除休息时间；下班打卡窗口结束且全天无卡时未请假时长计为旷工；打卡窗口结束未打卡且该时段未请假计为缺卡；迟到/早退分钟扣除休息与请假覆盖范围；请假分钟/天数按请假覆盖的工作范围折算。
6. 拼接考勤结果文案与打卡记录列表。

### 5.2 查询员工月度考勤汇总

- **路径**: GET /hrm/attendance/statistics/month-record-page
- **权限**: hrm:attendance:statistics:query
- **说明**: 分页查询员工指定月份的考勤汇总（出勤、迟到、早退、缺卡、旷工、请假及扣款金额）。

**请求参数 (HrmAttendanceMonthRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo / pageSize | Integer | 否 | - | 分页参数 |
| search | String | 否 | - | 员工姓名或工号，模糊匹配 |
| employeeId | Long | 否 | - | 员工编号 |
| deptIds | List\<Long\> | 否 | - | 部门编号数组 |
| year | Integer | 是 | @NotNull | 年份 |
| month | Integer | 是 | @NotNull、@Min(1)、@Max(12) | 月份 |
| fullAttendance | Boolean | 否 | - | 是否全勤（筛选条件） |

**响应**: CommonResult\<PageResult\<HrmAttendanceMonthRecordRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| attendanceGroupName | String | 考勤组名称 |
| entryTime | LocalDateTime | 入职时间 |
| employeeStatus | Integer | 员工状态 |
| workCity | String | 工作城市 |
| year | Integer | 年份 |
| month | Integer | 月份 |
| attendDays | Integer | 应出勤天数（已结算的排班工作日数） |
| actualDays | BigDecimal | 实际出勤天数（应出勤 - 请假 - 旷工，最小 0） |
| lateMinute | Integer | 迟到时长（分钟） |
| lateCount | Integer | 迟到次数 |
| earlyMinute | Integer | 早退时长（分钟） |
| earlyCount | Integer | 早退次数 |
| misscardCount | Integer | 缺卡次数 |
| absenteeismDays | BigDecimal | 旷工天数 |
| absenteeismMinutes | Integer | 旷工时长（分钟） |
| leaveDays | BigDecimal | 请假天数 |
| leaveMinutes | Integer | 请假时长（分钟） |
| lateDeductAmount | BigDecimal | 迟到扣款（按考勤组扣款规则：每月固定/按分钟/按次数） |
| earlyDeductAmount | BigDecimal | 早退扣款 |
| misscardDeductAmount | BigDecimal | 缺卡扣款（按次数） |
| absenteeismDeductAmount | BigDecimal | 旷工扣款（按天数） |
| attendanceDeductAmount | BigDecimal | 考勤扣款合计 |
| fullAttendance | Boolean | 是否全勤（有应出勤且无迟到/早退/缺卡/请假/旷工） |

**业务逻辑**:
1. 未筛选全勤时：分页查询当月在职员工，逐人计算月度汇总后按分页返回。
2. 筛选全勤时：计算全部符合条件的员工月度汇总，按 fullAttendance 过滤后内存分页。
3. 月度汇总计算：批量查询当月打卡（含跨日归属）、员工考勤组与每日班次（特殊日期 > 法定节假日 > 每周班次）、有效请假记录。
4. 仅统计已结算（超过下班打卡截止时间）的排班工作日，逐日计算迟到/早退/缺卡/旷工/请假后汇总。
5. 按员工所属考勤组的扣款规则计算各类扣款金额（无考勤组或无规则时为 0）。
6. 拼接部门名称。

### 5.3 查询员工月度打卡概况

- **路径**: GET /hrm/attendance/statistics/month-daily-page
- **权限**: hrm:attendance:clock:query
- **说明**: 分页查询员工指定月份每日打卡概况（考勤表表格视图），每日展示打卡项或考勤结果。

**请求参数 (HrmAttendanceMonthRecordPageReqVO)**: 同 5.2（fullAttendance 条件不生效）

**响应**: CommonResult\<PageResult\<HrmAttendanceMonthDailyOverviewRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| year | Integer | 年份 |
| month | Integer | 月份 |
| dailyClockMap | Map\<LocalDate, HrmAttendanceDailyOverviewRespVO\> | 每日打卡概况，Key 为日期 |

其中每日概况 **HrmAttendanceDailyOverviewRespVO**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| clocks | List\<HrmAttendanceClockRespVO\> | 当日打卡记录（按打卡时间升序） |
| attendanceResult | String | 当日考勤结果 |
| overviews | List\<OverviewItem\> | 概况展示项：无打卡时仅含考勤结果文本；有打卡时每条为「打卡类型（去“打卡”后缀）+ 打卡时间 + 打卡状态」 |

**业务逻辑**:
1. 分页查询当月在职员工。
2. 逐人复用每日明细计算逻辑，构建日期到打卡概况的映射。
3. 每日打卡记录按打卡时间升序，转换为概况展示项（打卡类型取字典标签并去掉「打卡」后缀）。
4. 拼接部门名称。

### 5.4 导出员工月度考勤汇总

- **路径**: GET /hrm/attendance/statistics/month-record-export-excel
- **权限**: hrm:attendance:statistics:export
- **说明**: 按相同条件导出员工月度考勤汇总 Excel（不分页）。

**请求参数 (HrmAttendanceMonthRecordPageReqVO)**: 同 5.2（pageSize 强制置为不分页）

**响应**: Excel 文件流 — 文件名「员工月度考勤汇总.xls」，列：员工编号、员工姓名、工号、部门、岗位、年份、月份、应出勤天数、实际出勤天数、迟到时长（分钟）、迟到次数、早退时长（分钟）、早退次数、缺卡次数、旷工天数、旷工时长（分钟）、请假天数、请假时长（分钟）、迟到扣款、早退扣款、缺卡扣款、旷工扣款、考勤扣款合计

**业务逻辑**:
1. 查询符合条件的全部员工并计算月度汇总（按需过滤全勤）。
2. 拼接部门名称。
3. 通过 ExcelUtils 写出 Excel，并记录导出操作日志（@ApiAccessLog EXPORT）。

### 5.5 导出员工月度打卡概况

- **路径**: GET /hrm/attendance/statistics/month-daily-export-excel
- **权限**: hrm:attendance:clock:export
- **说明**: 导出员工月度打卡概况 Excel，动态列：每日一列展示当日打卡概况或考勤结果。

**请求参数 (HrmAttendanceMonthRecordPageReqVO)**: 同 5.2（pageSize 强制置为不分页）

**响应**: Excel 文件流 — 文件名「员工月度打卡概况.xls」，表头：员工编号、员工姓名、工号、部门、岗位 + 当月每日一列（列名为日期），单元格为该日概况（多项以「；」拼接）

**业务逻辑**:
1. 查询符合条件的全部员工并计算月度打卡概况。
2. 拼接部门名称，并将每日概况转换为展示项。
3. 按当月天数生成动态表头与数据行（无打卡的日期展示考勤结果文本），写出 Excel 并记录导出操作日志。

### 5.6 查询员工月度考勤详情

- **路径**: GET /hrm/attendance/statistics/month-detail?employeeId={employeeId}&year={year}&month={month}
- **权限**: hrm:attendance:statistics:query
- **说明**: 查询单个员工指定月份的完整考勤详情：月度汇总 + 每日明细 + 请假记录。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| employeeId | Long | 是 | @Parameter(required=true) | 员工编号 |
| year | Integer | 是 | @Parameter(required=true) | 年份 |
| month | Integer | 是 | @Parameter(required=true) | 月份 |

**响应**: CommonResult\<HrmAttendanceMonthDetailRespVO\>；员工不存在时返回 null

| 字段 | 类型 | 说明 |
|-----|------|------|
| summary | HrmAttendanceMonthRecordRespVO | 月度汇总（结构同 5.2） |
| dailyDetails | List\<HrmAttendanceDailyDetailRespVO\> | 每日打卡明细（结构同 5.1，覆盖当月每天） |
| leaves | List\<HrmAttendanceLeaveRespVO\> | 与当月时间范围重叠的请假记录（结构同 3.1） |

**业务逻辑**:
1. 查询员工，不存在返回 null。
2. 批量获取员工当月的打卡记录、考勤组班次（特殊日期/节假日/每周班次解析）与审批通过的请假记录。
3. summary：构建当月考勤汇总（含扣款与全勤判断）。
4. dailyDetails：逐日构建考勤明细（含休息日）。
5. leaves：筛选与当月时间范围重叠的请假记录并拼接员工信息。
