# 员工管理接口 (HrmEmployeeController)

> HRM 员工管理域，覆盖员工档案全生命周期：建档（单个/批量/导入）、字段显隐配置、确认入职、转正、调岗、晋升、降级、转全职、离职与再入职，以及联系人、合同、异动记录、离职信息、工资卡、材料附件、个人备忘和教育/工作/培训经历、证书等子资源维护。

## 接口路径前缀

- /hrm/employee (Controller: HrmEmployeeController)
- /hrm/employee/config (Controller: HrmEmployeeFieldConfigController)
- /hrm/employee/contact (Controller: HrmEmployeeContactController)
- /hrm/employee/contract (Controller: HrmEmployeeContractController)
- /hrm/employee/change-record (Controller: HrmEmployeeChangeRecordController)
- /hrm/employee/quit-info (Controller: HrmEmployeeQuitInfoController)
- /hrm/employee/salary-card (Controller: HrmEmployeeSalaryCardController)
- /hrm/employee/file (Controller: HrmEmployeeFileController)
- /hrm/employee/personal-note (Controller: HrmEmployeePersonalNoteController)
- /hrm/employee/education-experience (Controller: HrmEmployeeEducationExperienceController)
- /hrm/employee/work-experience (Controller: HrmEmployeeWorkExperienceController)
- /hrm/employee/training-experience (Controller: HrmEmployeeTrainingExperienceController)
- /hrm/employee/certificate (Controller: HrmEmployeeCertificateController)

---

## 1. 员工档案管理（HrmEmployeeController）

### 1.1 创建员工档案

- **路径**: POST /hrm/employee/create
- **权限**: hrm:employee:create
- **说明**: 新建员工档案，自动计算试用期、转正时间、员工状态、年龄与司龄。

**请求参数 (HrmEmployeeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 员工档案编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 员工姓名 |
| jobNumber | String | 否 | @Size(max=64)；在职员工必填（@AssertTrue） | 工号 |
| userId | Long | 否 | - | 系统用户编号 |
| mobile | String | 是 | @NotBlank、@Mobile | 手机号 |
| country | String | 否 | @Size(max=64) | 国家地区 |
| nation | String | 否 | @Size(max=64) | 民族 |
| idType | Integer | 否 | @InEnum(证件类型) | 证件类型 |
| idNumber | String | 否 | @Size(max=255)；身份证类型时格式校验（@AssertTrue） | 证件号码 |
| sex | Integer | 否 | - | 性别 |
| email | String | 否 | @Email、@Size(max=255) | 邮箱 |
| nativePlace | String | 否 | @Size(max=128) | 籍贯 |
| birthday | LocalDateTime | 否 | @PastOrPresent | 出生时间 |
| age | Integer | 否 | - | 年龄（服务端按生日计算） |
| address | String | 否 | @Size(max=255) | 户籍地址 |
| highestEducation | Integer | 否 | @InEnum(最高学历) | 最高学历 |
| deptId | Long | 否 | - | 部门编号 |
| leaderEmployeeId | Long | 否 | - | 直属上级员工编号（不能是本人或下属） |
| entryStatus | Integer | 是 | @NotNull、@InEnum(入职状态) | 入职状态：1 在职，2 待入职 |
| status | Integer | 否 | @InEnum(员工状态)；非正式员工必填 | 员工状态 |
| type | Integer | 是 | @NotNull、@InEnum(聘用形式) | 聘用形式：1 正式，2 非正式 |
| entryTime | LocalDateTime | 是 | @NotNull | 入职时间 |
| probation | Integer | 否 | @Min(0)、@Max(6)；正式员工必填 | 试用期（月），0 表示无试用期 |
| regularTime | LocalDateTime | 否 | - | 转正时间 |
| leaveTime | LocalDateTime | 否 | - | 离职时间 |
| postName | String | 否 | @Size(max=255) | 职位名称 |
| postLevel | String | 否 | @Size(max=255) | 岗位职级 |
| workCity | String | 否 | @Size(max=64) | 工作城市 |
| workAddress | String | 否 | @Size(max=255) | 工作地址 |
| workDetailAddress | String | 否 | @Size(max=255) | 工作详细地址 |
| channelId | Long | 否 | - | 招聘渠道编号 |
| companyAgeStartTime | LocalDateTime | 否 | 不能晚于入职时间（@AssertTrue） | 司龄开始时间 |
| companyAge | Integer | 否 | - | 司龄（年，服务端计算） |
| candidateId | Long | 否 | - | 关联招聘候选人编号 |
| remark | String | 否 | @Size(max=500) | 备注 |

> 类级 @AssertTrue 交叉校验：身份证号码格式、员工状态与聘用形式匹配（非正式员工只能是非正式状态）、在职员工工号必填、正式员工试用期必填、司龄起算时间不晚于入职时间。

**响应**: CommonResult&lt;Long&gt; — 员工档案编号

**业务逻辑**:
1. 按入职状态校验新建字段配置，未显示字段不允许提交值。
2. 综合校验：工号/后台用户/手机号唯一，后台用户存在，部门存在，直属上级链路无自引用和环路，招聘渠道与候选人存在。
3. 构建员工档案：身份证补充出生日期并计算年龄；正式员工按入职时间+试用期计算转正时间和员工状态；司龄开始时间缺省取入职时间并计算司龄。
4. 插入员工档案。
5. 事务提交后向已绑定后台账号的员工发送员工端开通通知。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_001 | 员工工号已存在 |
| 1_050_100_002 | 系统用户已绑定员工档案 |
| 1_050_100_003 | 手机号已绑定员工档案 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_034 | 员工字段【{}】当前未显示，不能提交 |

### 1.2 从未建档后台用户批量创建员工档案

- **路径**: POST /hrm/employee/create-list
- **权限**: hrm:employee:create
- **说明**: 选择尚未建档的后台用户，批量生成员工档案（单次最多 100 名）。

**请求参数**: List&lt;HrmEmployeeCreateFromUserReqVO&gt;（@NotEmpty、@Size(max=100)，元素级 @Valid）

HrmEmployeeCreateFromUserReqVO 字段:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 后台用户编号 |
| jobNumber | String | 是 | @NotBlank、@Size(max=64) | 工号 |
| mobile | String | 是 | @NotBlank、@Mobile | 员工手机号 |
| deptId | Long | 否 | - | 部门编号 |
| leaderEmployeeId | Long | 否 | - | 直属上级员工编号 |
| type | Integer | 是 | @NotNull、@InEnum(聘用形式) | 聘用形式 |
| status | Integer | 否 | @InEnum(员工状态)；非正式员工必填 | 员工状态 |
| entryTime | LocalDateTime | 是 | @NotNull | 入职时间 |
| probation | Integer | 否 | @Min(0)、@Max(6)；正式员工必填 | 试用期（月） |
| postName | String | 否 | @Size(max=255) | 职位名称 |
| postLevel | String | 否 | @Size(max=255) | 岗位职级 |
| workCity | String | 否 | @Size(max=64) | 工作城市 |
| workAddress | String | 否 | @Size(max=255) | 工作地点 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt; — 员工档案编号列表

**业务逻辑**:
1. 校验列表内后台用户编号不重复，并校验后台用户存在，一次性加载用户资料。
2. 逐个构建员工档案：回填用户昵称、邮箱、性别，入职状态固定为在职；校验字段配置、列表内工号/手机号唯一、Bean Validation 及唯一性校验。
3. 全部校验通过后批量插入员工档案。
4. 事务提交后发送员工端开通通知，并按员工档案逐条记录"从后台用户创建"操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_001 | 员工工号已存在 |
| 1_050_100_003 | 手机号已绑定员工档案 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_031 | 批量建档的后台用户不能重复 |
| 1_050_100_032 | 批量建档的后台用户不存在 |

### 1.3 获得已经建立员工档案的后台用户编号列表

- **路径**: GET /hrm/employee/bound-user-id-list
- **权限**: hrm:employee:create
- **说明**: 查询已绑定员工档案的后台用户编号集合，用于批量建档时排除已建档用户。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;Long&gt;&gt; — 已建档用户编号列表

**业务逻辑**:
1. 查询所有绑定了后台用户的员工记录。
2. 提取 userId 列表返回。

### 1.4 发送填写员工档案通知

- **路径**: POST /hrm/employee/send-profile-fill-message
- **权限**: hrm:employee:update
- **说明**: 向指定员工（绑定了后台账号的）发送填写档案的站内信通知。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @NotEmpty、@Size(max=100) | 员工编号数组 |

**响应**: CommonResult&lt;HrmEmployeeNotifyRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| successCount | Integer | 发送成功数量 |
| skippedCount | Integer | 无后台账号跳过数量 |
| failureCount | Integer | 发送失败数量 |

**业务逻辑**:
1. 去重校验员工编号并加载员工，数量不一致时报员工档案不存在。
2. 遍历员工：未绑定后台账号的跳过；已绑定的按消息模板发送站内信，失败不中断。
3. 统计成功/跳过/失败数量。
4. 对发送成功的员工逐条记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 1.5 更新员工档案

- **路径**: PUT /hrm/employee/update
- **权限**: hrm:employee:update
- **说明**: 更新员工基本信息，生命周期字段（入职状态、聘用形式、员工状态、试用期、转正/离职时间）保持不变。

**请求参数 (HrmEmployeeSaveReqVO)**: 同 1.1（id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在及关联数据（唯一性、用户、部门、上级、渠道、候选人）。
2. 构建更新对象，保留员工当前的入职状态、聘用形式、员工状态、试用期、转正/离职时间。
3. 更新员工档案，并记录新旧值差异的操作日志。

**错误码**: 同 1.1

### 1.6 删除员工档案

- **路径**: DELETE /hrm/employee/delete
- **权限**: hrm:employee:delete
- **说明**: 按 id 删除单个员工档案。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 员工档案编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工档案存在。
2. 删除员工档案并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 1.7 批量删除员工档案

- **路径**: DELETE /hrm/employee/delete-list
- **权限**: hrm:employee:delete
- **说明**: 按编号数组批量删除员工档案。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 员工档案编号数组 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 批量查询员工档案，为空直接返回。
2. 逐个删除员工档案（复用单个删除逻辑记录日志）。

### 1.8 获得员工档案

- **路径**: GET /hrm/employee/get
- **权限**: hrm:employee:query
- **说明**: 按 id 获取员工完整档案，聚合用户、部门、上级、渠道、工资卡和社保账号信息。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 员工档案编号 |

**响应**: CommonResult&lt;HrmEmployeeRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 员工档案编号 |
| name | String | 员工姓名 |
| jobNumber | String | 工号 |
| userId | Long | 系统用户编号 |
| userNickname | String | 后台用户昵称 |
| mobile | String | 手机号 |
| country | String | 国家地区 |
| nation | String | 民族 |
| idType | Integer | 证件类型 |
| idNumber | String | 证件号码 |
| sex | Integer | 性别 |
| email | String | 邮箱 |
| nativePlace | String | 籍贯 |
| birthday | LocalDateTime | 出生时间 |
| age | Integer | 年龄（按生日实时计算） |
| address | String | 户籍地址 |
| highestEducation | Integer | 最高学历 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| leaderEmployeeId | Long | 直属上级员工编号 |
| leaderEmployeeName | String | 直属上级员工姓名 |
| entryStatus | Integer | 入职状态 |
| status | Integer | 员工状态 |
| type | Integer | 聘用形式 |
| entryTime | LocalDateTime | 入职时间 |
| probation | Integer | 试用期（月） |
| regularTime | LocalDateTime | 转正时间 |
| leaveTime | LocalDateTime | 离职时间 |
| postName | String | 职位名称 |
| postLevel | String | 岗位职级 |
| workCity | String | 工作城市 |
| workAddress | String | 工作地址 |
| workDetailAddress | String | 工作详细地址 |
| channelId | Long | 招聘渠道编号 |
| channelName | String | 招聘渠道名称 |
| companyAgeStartTime | LocalDateTime | 司龄开始时间 |
| companyAge | Integer | 司龄（年，实时计算） |
| candidateId | Long | 关联招聘候选人编号 |
| salaryCardNumber | String | 银行卡号 |
| salaryCardAreaId | Integer | 开户地区编号 |
| salaryCardAreaName | String | 开户地区名称 |
| salaryCardBankName | String | 银行名称 |
| salaryCardBankBranchName | String | 开户支行名称 |
| socialSecurityNumber | String | 个人社保账号 |
| accumulationFundNumber | String | 个人公积金账号 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询员工档案。
2. 批量加载后台用户、部门、直属上级员工、招聘渠道、工资卡、员工社保信息并拼接进响应。
3. 根据生日和司龄起算时间实时计算年龄与司龄。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 1.9 确认员工入职

- **路径**: PUT /hrm/employee/confirm-entry
- **权限**: hrm:employee:update
- **说明**: 待入职员工补全资料后确认入职，入职时间不能晚于当前时间。

**请求参数 (HrmEmployeeConfirmEntryReqVO)**: 继承 HrmEmployeeSaveReqVO 全部字段，另加校验：入职时间不能晚于当前时间（@AssertTrue）。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在且入职状态为"待入职"。
2. 将入职状态置为在职，执行整体 Bean Validation 和新建字段配置校验。
3. 保存完整员工固定字段并确认入职（清空离职时间）。
4. 若员工关联招聘候选人，同步候选人入职状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_009 | 只有待入职员工可以确认入职 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_034 | 员工字段【{}】当前未显示，不能提交 |

### 1.10 办理离职员工再入职

- **路径**: POST /hrm/employee/rehire
- **权限**: hrm:employee:update
- **说明**: 已离职员工重新入职，创建再入职异动记录并清空原离职信息。

**请求参数 (HrmEmployeeRehireReqVO)**: 继承 HrmEmployeeSaveReqVO 全部字段，新增：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |

> 另加校验：入职时间不能晚于当前时间（@AssertTrue）。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在且入职状态为"已离职"。
2. 执行整体校验（字段配置、唯一性、部门/上级链路）。
3. 按聘用形式计算试用期、转正时间和员工状态；司龄开始时间缺省取入职时间并计算司龄。
4. 创建"再入职"异动记录，并删除原离职信息。
5. 更新员工档案：入职状态置在职、回填任职字段、清空离职时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_007 | 只有已离职员工可以办理再入职 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |

### 1.11 办理员工转正

- **路径**: POST /hrm/employee/regular
- **权限**: hrm:employee:update
- **说明**: 试用期员工办理转正，支持预约生效日期，可同时调整部门/岗位/职级/工作地点/直属上级。

**请求参数 (HrmEmployeeRegularReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| reason | Integer | 是 | @NotNull、@InEnum(异动原因) | 异动原因 |
| newDeptId | Long | 否 | - | 新部门编号；未填写表示不变 |
| newPostName | String | 否 | @Size(max=255) | 新岗位名称；未填写表示不变 |
| newPostLevel | String | 否 | @Size(max=255) | 新职级；未填写表示不变 |
| newWorkAddress | String | 否 | @Size(max=255) | 新工作地点；未填写表示不变 |
| newLeaderEmployeeId | Long | 否 | - | 新直属上级员工编号；未填写表示不变 |
| effectTime | LocalDateTime | 是 | @NotNull | 生效日期 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在、处于在职状态且员工状态为试用期。
2. 将未填写的任职字段补充为员工当前值，校验新部门和新直属上级。
3. 创建"转正"异动记录（生效时间取自然日开始）。
4. 更新员工的预约转正时间；若生效时间已到则立即应用转正（状态改为正式，并应用任职字段变更）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_025 | 员工当前状态不允许办理【{}】 |

### 1.12 办理员工调岗

- **路径**: POST /hrm/employee/transfer
- **权限**: hrm:employee:update
- **说明**: 在职员工办理调岗，支持预约生效日期。

**请求参数 (HrmEmployeeTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| reason | Integer | 是 | @NotNull、@InEnum(异动原因)；仅允许调岗晋升类原因（@AssertTrue） | 异动原因 |
| newDeptId | Long | 否 | - | 新部门编号 |
| newPostName | String | 否 | @Size(max=255) | 新岗位名称 |
| newPostLevel | String | 否 | @Size(max=255) | 新职级 |
| newWorkAddress | String | 否 | @Size(max=255) | 新工作地点 |
| newLeaderEmployeeId | Long | 否 | - | 新直属上级员工编号 |
| effectTime | LocalDateTime | 是 | @NotNull | 生效日期 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工处于在职状态，校验新部门和新直属上级链路。
2. 创建"调岗"异动记录（原部门/岗位/职级/工作地点/上级自动留档）。
3. 若生效时间已到则立即更新员工的部门、岗位、职级、工作地点和直属上级。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_025 | 员工当前状态不允许办理【{}】 |

### 1.13 办理员工晋升

- **路径**: POST /hrm/employee/promote
- **权限**: hrm:employee:update
- **说明**: 在职员工办理晋升，参数结构与校验逻辑同调岗，异动类型为晋升。

**请求参数 (HrmEmployeePromoteReqVO)**: 同 HrmEmployeeTransferReqVO（异动原因仅允许调岗晋升类原因）。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工处于在职状态，校验新部门和新直属上级链路。
2. 创建"晋升"异动记录。
3. 若生效时间已到则立即应用岗位变更。

**错误码**: 同 1.12

### 1.14 办理员工降级

- **路径**: POST /hrm/employee/demote
- **权限**: hrm:employee:update
- **说明**: 在职员工办理降级，异动原因仅允许降级类原因。

**请求参数 (HrmEmployeeDemoteReqVO)**: 同 HrmEmployeeTransferReqVO（@AssertTrue 校验异动原因属于降级类原因）。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工处于在职状态，校验新部门和新直属上级链路。
2. 创建"降级"异动记录。
3. 若生效时间已到则立即应用岗位变更。

**错误码**: 同 1.12

### 1.15 办理员工转为全职

- **路径**: POST /hrm/employee/convert-to-full-time
- **权限**: hrm:employee:update
- **说明**: 非全职员工转为全职，需指定新试用期（0-6 个月），支持预约生效。

**请求参数 (HrmEmployeeConvertToFullTimeReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| reason | Integer | 是 | @NotNull、@InEnum(异动原因) | 异动原因 |
| probation | Integer | 是 | @NotNull、@Min(0)、@Max(6) | 试用期（月），0 表示无试用期 |
| newDeptId | Long | 否 | - | 新部门编号；未填写表示不变 |
| newPostName | String | 否 | @Size(max=255) | 新岗位名称；未填写表示不变 |
| newPostLevel | String | 否 | @Size(max=255) | 新职级；未填写表示不变 |
| newWorkAddress | String | 否 | @Size(max=255) | 新工作地点；未填写表示不变 |
| newLeaderEmployeeId | Long | 否 | - | 新直属上级员工编号；未填写表示不变 |
| effectTime | LocalDateTime | 是 | @NotNull | 生效日期 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在、处于在职状态且当前员工状态允许转全职。
2. 将未填写的任职字段补充为员工当前值，校验新部门和新直属上级。
3. 创建"转全职"异动记录。
4. 若生效时间已到则立即应用：聘用形式改为正式，按新试用期计算员工状态和转正时间，并应用任职字段变更。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_025 | 员工当前状态不允许办理【{}】 |

### 1.16 办理员工离职

- **路径**: POST /hrm/employee/quit
- **权限**: hrm:employee:update
- **说明**: 为在职/待离职/已离职员工设置离职信息，支持预约离职日期。

**请求参数 (HrmEmployeeQuitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| planQuitTime | LocalDateTime | 是 | @NotNull | 计划离职时间 |
| applyQuitTime | LocalDateTime | 是 | @NotNull；不能晚于计划离职时间（@AssertTrue） | 申请离职时间 |
| salarySettlementTime | LocalDateTime | 是 | @NotNull；不能早于计划离职时间（@AssertTrue） | 薪资结算时间 |
| type | Integer | 是 | @NotNull、@InEnum(离职类型) | 离职类型 |
| reason | Integer | 否 | @InEnum(离职原因)；须与离职类型匹配（@AssertTrue），退休类型免填 | 离职原因 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工入职状态为在职/待离职/已离职；已离职员工补办时计划离职时间必须在当前时间之前。
2. 保存离职信息：退休类型清空离职原因，申请/结算时间取自然日开始，记录离职前员工状态。
3. 更新员工：计划离职时间已到或原已离职的置为"已离职"并按计划离职时间结算司龄，否则置为"待离职"，同时记录离职时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_010 | 只有在职或待离职员工可以设置离职 |
| 1_050_100_028 | 离职时间范围不合法 |

### 1.17 取消员工离职

- **路径**: PUT /hrm/employee/cancel-quit
- **权限**: hrm:employee:update
- **说明**: 撤销待离职员工的离职安排，恢复在职状态。

**请求参数 (HrmEmployeeCancelQuitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| reason | String | 是 | @NotBlank、@Size(max=500) | 取消原因 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工入职状态为"待离职"且存在离职信息。
2. 删除该员工的离职信息。
3. 恢复员工入职状态为在职并清空离职时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_011 | 只有待离职员工可以取消离职 |
| 1_050_100_023 | 员工离职信息不存在 |

### 1.18 获得员工档案分页

- **路径**: GET /hrm/employee/page
- **权限**: hrm:employee:query
- **说明**: 多条件分页查询员工档案，响应结构与 1.8 一致。

**请求参数 (HrmEmployeePageReqVO)**: 继承 SortablePageParam（含 pageNo/pageSize/sortingRule 排序参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 否 | - | 员工编号列表 |
| search | String | 否 | - | 姓名/工号/手机号模糊匹配 |
| name | String | 否 | - | 员工姓名，模糊匹配 |
| jobNumber | String | 否 | - | 工号，模糊匹配 |
| mobile | String | 否 | - | 手机号，模糊匹配 |
| deptId | Long | 否 | - | 部门编号 |
| deptIds | List&lt;Long&gt; | 否 | - | 部门编号数组 |
| leaderEmployeeId | Long | 否 | - | 直属上级员工编号 |
| sex | Integer | 否 | - | 性别 |
| entryTime | LocalDateTime[] | 否 | - | 入职时间范围 |
| postName | String | 否 | - | 职位名称，模糊匹配 |
| regularTime | LocalDateTime[] | 否 | - | 转正时间范围 |
| workAddress | String | 否 | - | 工作地点，模糊匹配 |
| channelId | Long | 否 | - | 招聘渠道编号 |
| type | Integer | 否 | @InEnum(聘用形式) | 聘用形式 |
| entryStatus | Integer | 否 | @InEnum(入职状态) | 入职状态 |
| status | Integer | 否 | @InEnum(员工状态) | 员工状态 |
| statusCategory | Integer | 否 | @InEnum(状态分类) | 员工状态分类（页签） |
| surveyType | Integer | 否 | @InEnum(人事概况筛选) | 首页人事概况筛选类型 |
| todoType | Integer | 否 | @InEnum(待办筛选) | 首页待办筛选类型 |

**响应**: CommonResult&lt;PageResult&lt;HrmEmployeeRespVO&gt;&gt; — RespVO 字段同 1.8

**业务逻辑**:
1. 按条件分页查询员工档案。
2. 批量加载用户/部门/上级/渠道/工资卡/社保信息并拼接，实时计算年龄和司龄。

### 1.19 获得员工列表

- **路径**: GET /hrm/employee/list
- **权限**: hrm:employee:query
- **说明**: 按编号列表查询员工完整档案，用于表单回显已选员工。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 员工编号列表 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeRespVO&gt;&gt; — RespVO 字段同 1.8

**业务逻辑**:
1. 按编号列表查询员工并做 VO 聚合拼接（同 1.8 逻辑）。

### 1.20 获得员工精简分页

- **路径**: GET /hrm/employee/simple-page
- **权限**: 已认证（仅登录，无权限标识）
- **说明**: 分页查询员工选择器所需字段，只返回非敏感信息。

**请求参数**: 同 HrmEmployeePageReqVO（见 1.18）

**响应**: CommonResult&lt;PageResult&lt;HrmEmployeeRespVO&gt;&gt;，仅返回精简字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 员工档案编号 |
| name | String | 员工姓名 |
| jobNumber | String | 工号 |
| mobile | String | 手机号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| leaderEmployeeId | Long | 直属上级员工编号 |
| leaderEmployeeName | String | 直属上级姓名 |
| postName | String | 职位名称 |
| postLevel | String | 岗位职级 |
| entryStatus | Integer | 入职状态 |
| status | Integer | 员工状态 |

**业务逻辑**:
1. 复用分页查询；加载部门与直属上级信息拼接名称。
2. 只填充员工选择器需要的精简字段，不加载工资卡、社保等敏感聚合。

### 1.21 获得员工精简列表

- **路径**: GET /hrm/employee/simple-list
- **权限**: 已认证（仅登录，无权限标识）
- **说明**: 按编号列表查询精简员工信息，用于员工选择器回显。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 员工编号列表 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeRespVO&gt;&gt; — 仅精简字段（同 1.20）

**业务逻辑**: 同 1.20。

### 1.22 导出员工档案

- **路径**: GET /hrm/employee/export-excel
- **权限**: hrm:employee:export
- **说明**: 按筛选条件导出员工档案 Excel（不含工资卡、社保等敏感聚合字段）。

**请求参数**: 同 HrmEmployeePageReqVO（见 1.18，pageSize 强制置为不分页）

**响应**: Excel 文件流（员工档案.xlsx），导出列包括员工编号、姓名、工号、手机号、部门、岗位、职级、直属上级、入职状态、员工状态、聘用形式、入职/转正/离职时间、工作城市/地点、绑定用户、招聘渠道等。

**业务逻辑**:
1. 将分页参数转为列表查询条件（不分页）。
2. 查询员工并拼接用户昵称、部门、直属上级、渠道等安全导出字段（不加载工资卡和社保）。
3. 通过 Excel 工具输出文件。

### 1.23 获得员工档案导入模板

- **路径**: GET /hrm/employee/get-import-template
- **权限**: hrm:employee:import
- **说明**: 下载员工档案 Excel 导入模板，内含一条示例数据。

**请求参数**: 无

**响应**: Excel 文件流（员工档案导入模板.xlsx），列包括员工姓名、工号、手机号、国家或地区、民族、证件类型、证件号码、性别、邮箱、籍贯、出生日期、户籍地址、最高学历、部门编号、直属上级工号、职位名称、岗位职级、入职状态、员工状态、聘用形式、入职时间、试用期（月）、转正时间、离职时间、工作城市、工作地点、工作详细地址、招聘渠道、司龄起算时间、绑定用户手机号、银行卡号、开户地区、银行名称、开户支行名称、是否首次参保、是否首次缴纳公积金、个人社保账号、个人公积金账号、社保起缴月份、参保方案名称、备注。

**业务逻辑**:
1. 构造一条完整的示例数据（含工资卡、社保示例值）。
2. 通过 Excel 工具输出模板文件。

### 1.24 导入员工档案

- **路径**: POST /hrm/employee/import
- **权限**: hrm:employee:import
- **说明**: 上传 Excel 批量导入员工档案，支持按工号或绑定用户判重，重复数据可跳过/覆盖/判失败。

**请求参数**: Multipart 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| file | MultipartFile | 是 | - | Excel 文件 |
| duplicateStrategy | Integer | 否 | 默认 3 | 重复员工处理策略：1 跳过，2 覆盖，3 判失败 |

**响应**: CommonResult&lt;HrmEmployeeImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| createJobNumbers | List&lt;String&gt; | 创建成功的员工标识（工号）数组 |
| updateJobNumbers | List&lt;String&gt; | 更新成功的员工标识数组 |
| skipJobNumbers | List&lt;String&gt; | 因重复而跳过的员工标识数组 |
| failureJobNumbers | Map&lt;String, String&gt; | 导入失败集合，key 为原始行号和员工标识，value 为失败原因 |

**业务逻辑**:
1. 读取 Excel 数据，校验数据非空、重复处理策略合法。
2. 逐行处理：将业务键解析为内部编号（直属上级工号→上级员工、绑定用户手机号→后台用户、参保方案名称→社保方案、招聘渠道名称→渠道），执行 Bean Validation 与工资卡/社保字段组校验，失败记录原因并继续。
3. 按工号或绑定用户编号匹配已有员工；已存在时按策略跳过、判失败或覆盖更新。
4. 在独立事务内保存员工档案及其工资卡、员工社保信息。
5. 汇总创建/更新/跳过/失败结果返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_001 | 员工工号已存在 |
| 1_050_100_002 | 系统用户已绑定员工档案 |
| 1_050_100_003 | 手机号已绑定员工档案 |
| 1_050_100_006 | 导入员工档案数据不能为空 |
| 1_050_100_014 | 直属上级不能是员工本人或下属 |
| 1_050_100_033 | 员工导入重复数据处理策略不合法 |
| 1_050_100_038 | 导入字段【{}】的值【{}】不存在 |
| 1_050_200_003 | 招聘渠道不存在 |

### 1.25 获得员工状态统计

- **路径**: GET /hrm/employee/status-count
- **权限**: hrm:employee:query
- **说明**: 按员工状态页签（在职、全职、待入职、待离职、已离职及各细分状态）统计数量，常与列表页签联动。

**请求参数**: 同 HrmEmployeePageReqVO（见 1.18，用于联动筛选）

**响应**: CommonResult&lt;List&lt;HrmEmployeeStatusCountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 状态页签 |
| count | Long | 数量 |

**业务逻辑**:
1. 按页签查询条件分组统计员工数量。
2. 在职人数包含"在职"和"待离职"，并继续按员工状态、是否全职细分；其余按待入职/待离职/已离职归集。

### 1.26 获得员工部门统计

- **路径**: GET /hrm/employee/dept-statistics
- **权限**: hrm:employee:query
- **说明**: 按部门统计在职员工人数及全职/非全职构成。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmEmployeeDeptStatisticsRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| deptId | Long | 部门编号 |
| activeCount | Long | 在职员工人数 |
| fullTimeCount | Long | 全职员工人数 |
| nonFullTimeCount | Long | 非全职员工人数 |

**业务逻辑**:
1. 查询各部门在职员工按聘用形式的数量分布。
2. 汇总计算部门在职总人数、全职人数和非全职人数。

## 2. 员工字段配置（HrmEmployeeFieldConfigController）

### 2.1 获得新建员工字段配置

- **路径**: GET /hrm/employee/config/create-field/list
- **权限**: hrm:employee:config:query 或 hrm:employee:create
- **说明**: 获取新建员工表单的字段显隐配置，按入职状态区分在职/待入职两套配置。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| entryStatus | Integer | 是 | 1 在职，2 待入职 | 入职状态 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeFieldConfigRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| name | String | 字段名称 |
| title | String | 字段标题 |
| groupName | String | 字段分组名称 |
| visible | Boolean | 是否显示 |
| editable | Boolean | 是否允许员工编辑 |
| visibleLocked | Boolean | 是否锁定显示（不可关闭） |
| editableLocked | Boolean | 是否锁定编辑 |

**业务逻辑**:
1. 根据入职状态定位对应配置类型（在职/待入职），非法值报错。
2. 读取系统配置中的字段配置 JSON，按新建字段枚举逐项输出；锁定显示字段强制使用默认值。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_024 | 员工字段配置【{}】不合法 |

### 2.2 保存新建员工字段配置

- **路径**: PUT /hrm/employee/config/create-field/save
- **权限**: hrm:employee:config:update
- **说明**: 保存指定入职状态下的新建员工字段显隐配置。

**请求参数 (HrmEmployeeCreateFieldConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| entryStatus | Integer | 是 | @NotNull、@InEnum、@Range(min=1,max=2) | 入职状态：1 在职，2 待入职 |
| fields | List&lt;HrmEmployeeFieldConfigSaveReqVO&gt; | 是 | @Valid、@NotEmpty | 字段配置列表 |

HrmEmployeeFieldConfigSaveReqVO 字段:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotBlank、@Size(max=40) | 字段名称 |
| visible | Boolean | 是 | @NotNull | 是否显示 |
| editable | Boolean | 否 | - | 是否允许员工编辑 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验字段名合法（属于新建字段枚举）且列表内不重复。
2. 锁定显示字段强制使用默认显隐值。
3. 将字段配置序列化为 JSON 后整体替换系统配置，并记录新旧配置差异的操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_024 | 员工字段配置【{}】不合法 |

### 2.3 获得员工档案字段配置

- **路径**: GET /hrm/employee/config/archive-field/list
- **权限**: hrm:employee:config:query
- **说明**: 获取员工档案详情页的字段显隐与员工端可编辑配置。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmEmployeeFieldConfigRespVO&gt;&gt; — 字段同 2.1

**业务逻辑**:
1. 读取档案字段配置，按档案字段枚举逐项输出显隐与可编辑值。
2. 不可见字段或编辑锁定字段强制不可编辑。

### 2.4 保存员工档案字段配置

- **路径**: PUT /hrm/employee/config/archive-field/save
- **权限**: hrm:employee:config:update
- **说明**: 保存员工档案字段的显示与员工端编辑配置。

**请求参数 (HrmEmployeeArchiveFieldConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| fields | List&lt;HrmEmployeeFieldConfigSaveReqVO&gt; | 是 | @Valid、@NotEmpty | 字段配置列表（字段结构同 2.2） |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验字段名合法（属于档案字段枚举）且列表内不重复。
2. 不可见字段或编辑锁定字段强制不可编辑。
3. 序列化后整体替换系统配置，并记录新旧配置差异的操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_024 | 员工字段配置【{}】不合法 |

## 3. 员工联系人（HrmEmployeeContactController）

### 3.1 获得员工联系人列表

- **路径**: GET /hrm/employee/contact/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询其全部紧急联系人/联系人。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeContactRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 联系人编号 |
| employeeId | Long | 员工编号 |
| name | String | 联系人名称 |
| relation | String | 关系 |
| phone | String | 联系人电话 |
| workUnit | String | 联系人工作单位 |
| postName | String | 联系人职务 |
| address | String | 联系人地址 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询联系人列表并转换为 VO。

### 3.2 创建员工联系人

- **路径**: POST /hrm/employee/contact/create
- **权限**: hrm:employee:update
- **说明**: 为员工新增一条联系人。

**请求参数 (HrmEmployeeContactSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 联系人编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| name | String | 是 | @NotBlank、@Size(max=64) | 联系人名称 |
| relation | String | 否 | @Size(max=64) | 关系 |
| phone | String | 否 | @Size(max=40) | 联系人电话 |
| workUnit | String | 否 | @Size(max=128) | 联系人工作单位 |
| postName | String | 否 | @Size(max=128) | 联系人职务 |
| address | String | 否 | @Size(max=255) | 联系人地址 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; — 联系人编号

**业务逻辑**:
1. 校验员工存在。
2. 插入联系人记录并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 3.3 更新员工联系人

- **路径**: PUT /hrm/employee/contact/update
- **权限**: hrm:employee:update
- **说明**: 更新员工联系人信息，不允许变更所属员工。

**请求参数**: 同 HrmEmployeeContactSaveReqVO（见 3.2，id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工和联系人存在，且联系人归属该员工。
2. 更新联系人（清空 employeeId 防止变更归属），记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_020 | 员工联系人不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |

### 3.4 删除员工联系人

- **路径**: DELETE /hrm/employee/contact/delete
- **权限**: hrm:employee:delete
- **说明**: 按编号删除员工联系人。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 联系人编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验联系人存在后删除，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_020 | 员工联系人不存在 |

## 4. 员工合同（HrmEmployeeContractController）

### 4.1 获得员工合同列表

- **路径**: GET /hrm/employee/contract/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询其全部劳动合同。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeContractRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 合同记录编号 |
| employeeId | Long | 员工编号 |
| no | String | 合同编号 |
| type | Integer | 合同类型 |
| startTime | LocalDateTime | 合同开始日期 |
| endTime | LocalDateTime | 合同结束日期 |
| term | Integer | 期限（年） |
| status | Integer | 合同状态 |
| signCompany | String | 签约公司 |
| signTime | LocalDateTime | 合同签订日期 |
| remark | String | 备注 |
| expireRemind | Boolean | 是否到期提醒 |
| fileUrls | List&lt;String&gt; | 附件地址数组 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询合同列表并转换为 VO。

### 4.2 创建员工合同

- **路径**: POST /hrm/employee/contract/create
- **权限**: hrm:employee:update
- **说明**: 为员工新增一条合同记录。

**请求参数 (HrmEmployeeContractSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 合同记录编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| no | String | 否 | @Size(max=128) | 合同编号 |
| type | Integer | 是 | @NotNull、@InEnum(合同类型) | 合同类型 |
| startTime | LocalDateTime | 是 | @NotNull | 合同开始日期 |
| endTime | LocalDateTime | 是 | @NotNull；不能早于开始日期（@AssertTrue） | 合同结束日期 |
| term | Integer | 否 | @Min(1)、@Max(10)；非固定期限合同外必填（@AssertTrue） | 期限（年） |
| status | Integer | 是 | @NotNull、@InEnum(合同状态) | 合同状态 |
| signCompany | String | 否 | @Size(max=255) | 签约公司 |
| signTime | LocalDateTime | 是 | @NotNull | 合同签订日期 |
| remark | String | 否 | @Size(max=500) | 备注 |
| expireRemind | Boolean | 否 | - | 是否到期提醒 |
| fileUrls | List&lt;String&gt; | 否 | - | 附件地址数组 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; — 合同记录编号

**业务逻辑**:
1. 校验员工存在。
2. 合同开始/结束/签订日期取自然日开始；无固定期限劳动合同清空期限字段。
3. 插入合同记录并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 4.3 更新员工合同

- **路径**: PUT /hrm/employee/contract/update
- **权限**: hrm:employee:update
- **说明**: 更新员工合同，不允许变更所属员工。

**请求参数**: 同 HrmEmployeeContractSaveReqVO（见 4.2，id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工和合同存在，且合同归属该员工。
2. 更新合同（清空 employeeId 防止变更归属），无固定期限合同清空期限，记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_021 | 员工合同不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |

### 4.4 删除员工合同

- **路径**: DELETE /hrm/employee/contract/delete
- **权限**: hrm:employee:delete
- **说明**: 按编号删除员工合同。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 合同记录编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验合同存在后删除，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_021 | 员工合同不存在 |

## 5. 员工异动记录（HrmEmployeeChangeRecordController）

### 5.1 获得员工异动记录列表

- **路径**: GET /hrm/employee/change-record/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询异动历史（转正、调岗、晋升、降级、转全职、再入职等），拼接新旧部门与上级名称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeChangeRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 异动编号 |
| employeeId | Long | 员工编号 |
| type | Integer | 变动类型 |
| reason | Integer | 异动原因 |
| oldDeptId | Long | 原部门编号 |
| oldDeptName | String | 原部门名称 |
| newDeptId | Long | 新部门编号 |
| newDeptName | String | 新部门名称 |
| oldPostName | String | 原岗位名称 |
| newPostName | String | 新岗位名称 |
| oldPostLevel | String | 原职级 |
| newPostLevel | String | 新职级 |
| oldWorkAddress | String | 原工作地点 |
| newWorkAddress | String | 新工作地点 |
| oldLeaderEmployeeId | Long | 原直属上级员工编号 |
| oldLeaderEmployeeName | String | 原直属上级员工姓名 |
| newLeaderEmployeeId | Long | 新直属上级员工编号 |
| newLeaderEmployeeName | String | 新直属上级员工姓名 |
| probation | Integer | 试用期（月） |
| effectTime | LocalDateTime | 生效日期 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按员工编号查询异动记录。
2. 批量加载新旧部门名称和新旧直属上级姓名并拼接。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

## 6. 员工离职信息（HrmEmployeeQuitInfoController）

### 6.1 获得员工离职信息

- **路径**: GET /hrm/employee/quit-info/get
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询其离职安排详情（无离职安排时返回 null）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;HrmEmployeeQuitInfoRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 离职信息编号 |
| employeeId | Long | 员工编号 |
| planQuitTime | LocalDateTime | 计划离职时间 |
| applyQuitTime | LocalDateTime | 申请离职时间 |
| salarySettlementTime | LocalDateTime | 薪资结算时间 |
| type | Integer | 离职类型 |
| reason | Integer | 离职原因 |
| remark | String | 备注 |
| oldEmployeeStatus | Integer | 离职前员工状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询离职信息并转换为 VO。

## 7. 员工工资卡（HrmEmployeeSalaryCardController）

### 7.1 获得员工工资卡

- **路径**: GET /hrm/employee/salary-card/get
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询工资卡，拼接开户地区名称（每人一张卡，无卡时返回 null）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;HrmEmployeeSalaryCardRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 工资卡编号 |
| employeeId | Long | 员工编号 |
| bankCardNumber | String | 银行卡号 |
| bankAreaId | Integer | 开户地区编号 |
| bankAreaName | String | 开户地区名称 |
| bankName | String | 银行名称 |
| bankBranchName | String | 开户支行名称 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询工资卡，将开户地区编号格式化为地区名称。

### 7.2 保存员工工资卡

- **路径**: PUT /hrm/employee/salary-card/save
- **权限**: hrm:employee:update
- **说明**: 新增或更新员工工资卡（每名员工一张卡），不允许变更所属员工。

**请求参数 (HrmEmployeeSalaryCardSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 工资卡编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| bankCardNumber | String | 是 | @NotBlank、@Size(max=64) | 银行卡号 |
| bankAreaId | Integer | 否 | - | 开户地区编号 |
| bankName | String | 否 | @Size(max=64) | 银行名称 |
| bankBranchName | String | 否 | @Size(max=128) | 开户支行名称 |

**响应**: CommonResult&lt;Long&gt; — 工资卡编号

**业务逻辑**:
1. 校验员工存在；按 id 或员工编号定位已有工资卡，校验归属（不能把别人的卡改到自己名下）。
2. 未传 id 且已有卡时复用原卡记录，执行 insertOrUpdate。
3. 记录银行卡号脱敏差异的操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |
| 1_050_500_008 | 员工工资卡不存在 |

### 7.3 删除员工工资卡

- **路径**: DELETE /hrm/employee/salary-card/delete
- **权限**: hrm:employee:update
- **说明**: 按员工编号删除其工资卡。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在且名下有工资卡。
2. 删除工资卡并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_500_008 | 员工工资卡不存在 |

## 8. 员工材料附件（HrmEmployeeFileController）

### 8.1 获得员工材料附件列表

- **路径**: GET /hrm/employee/file/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询全部材料附件（按类型分组的文件，如身份证、学历证明等）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeFileRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 附件编号 |
| employeeId | Long | 员工编号 |
| type | Integer | 附件类型 |
| url | String | 附件地址 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询全部材料附件并转换为 VO。

### 8.2 保存员工材料附件

- **路径**: PUT /hrm/employee/file/save
- **权限**: hrm:employee:update
- **说明**: 按附件类型整体保存员工附件，自动对比差异新增/删除。

**请求参数 (HrmEmployeeFileSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| type | Integer | 是 | @NotNull、@InEnum(附件类型) | 附件类型 |
| fileUrls | List&lt;String&gt; | 是 | @NotNull、@Size(max=20)，元素 @NotBlank、@Size(max=512) | 附件地址数组（同类最多 20 个） |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工存在。
2. 查询该员工该类型的已有附件，与请求 URL 集合做差异比对。
3. 新增请求中增加的附件，删除请求中移除的附件（含历史重复附件）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

## 9. 员工个人备忘（HrmEmployeePersonalNoteController）

### 9.1 创建员工个人备忘

- **路径**: POST /hrm/employee/personal-note/create
- **权限**: hrm:employee:personal-note:create
- **说明**: 当前登录用户给自己绑定员工档案创建一条带提醒时间的备忘。

**请求参数 (HrmEmployeePersonalNoteCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| content | String | 是 | @NotBlank、@Size(max=1024) | 备忘内容 |
| reminderTime | LocalDateTime | 是 | @NotNull | 提醒时间 |

**响应**: CommonResult&lt;Long&gt; — 备忘编号

**业务逻辑**:
1. 根据当前登录用户查找其绑定的员工档案（未建档报错）。
2. 校验员工存在后插入个人备忘。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 9.2 删除员工个人备忘

- **路径**: DELETE /hrm/employee/personal-note/delete
- **权限**: hrm:employee:personal-note:delete
- **说明**: 当前登录用户删除自己的个人备忘。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 员工个人备忘编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 根据当前登录用户查找其绑定的员工档案。
2. 校验备忘存在且属于当前员工，否则报备忘不存在。
3. 删除备忘。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_030 | 员工个人备忘不存在 |

## 10. 员工教育经历（HrmEmployeeEducationExperienceController）

### 10.1 获得员工教育经历列表

- **路径**: GET /hrm/employee/education-experience/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询教育经历。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeEducationExperienceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 教育经历编号 |
| employeeId | Long | 员工编号 |
| education | Integer | 学历 |
| graduateSchool | String | 毕业院校 |
| major | String | 专业 |
| admissionTime | LocalDateTime | 入学日期 |
| graduationTime | LocalDateTime | 毕业日期 |
| teachingMethods | Integer | 教学方式 |
| firstDegree | Boolean | 是否第一学历 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询教育经历列表并转换为 VO。

### 10.2 创建员工教育经历

- **路径**: POST /hrm/employee/education-experience/create
- **权限**: hrm:employee:update
- **说明**: 为员工新增一条教育经历。

**请求参数 (HrmEmployeeEducationExperienceSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 教育经历编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| education | Integer | 是 | @NotNull | 学历 |
| graduateSchool | String | 是 | @NotBlank、@Size(max=255) | 毕业院校 |
| major | String | 是 | @NotBlank、@Size(max=255) | 专业 |
| admissionTime | LocalDateTime | 否 | - | 入学日期 |
| graduationTime | LocalDateTime | 否 | 不能早于入学日期（@AssertTrue） | 毕业日期 |
| teachingMethods | Integer | 否 | - | 教学方式 |
| firstDegree | Boolean | 否 | - | 是否第一学历 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; — 教育经历编号

**业务逻辑**:
1. 校验员工存在。
2. 入学/毕业日期取自然日后插入教育经历，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 10.3 更新员工教育经历

- **路径**: PUT /hrm/employee/education-experience/update
- **权限**: hrm:employee:update
- **说明**: 更新教育经历，不允许变更所属员工。

**请求参数**: 同 HrmEmployeeEducationExperienceSaveReqVO（见 10.2，id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工和教育经历存在，且归属该员工。
2. 更新教育经历（清空 employeeId 防止变更归属），记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_016 | 员工教育经历不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |

### 10.4 删除员工教育经历

- **路径**: DELETE /hrm/employee/education-experience/delete
- **权限**: hrm:employee:delete
- **说明**: 按编号删除教育经历。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 教育经历编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验教育经历存在后删除，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_016 | 员工教育经历不存在 |

## 11. 员工工作经历（HrmEmployeeWorkExperienceController）

### 11.1 获得员工工作经历列表

- **路径**: GET /hrm/employee/work-experience/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询工作经历。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeWorkExperienceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 工作经历编号 |
| employeeId | Long | 员工编号 |
| workUnit | String | 工作单位 |
| postName | String | 职务 |
| startTime | LocalDateTime | 工作开始日期 |
| endTime | LocalDateTime | 工作结束日期 |
| reason | String | 离职原因 |
| witnessName | String | 证明人 |
| witnessPhone | String | 证明人手机号 |
| remark | String | 工作备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询工作经历列表并转换为 VO。

### 11.2 创建员工工作经历

- **路径**: POST /hrm/employee/work-experience/create
- **权限**: hrm:employee:update
- **说明**: 为员工新增一条工作经历。

**请求参数 (HrmEmployeeWorkExperienceSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 工作经历编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| workUnit | String | 是 | @NotBlank、@Size(max=255) | 工作单位 |
| postName | String | 是 | @NotBlank、@Size(max=255) | 职务 |
| startTime | LocalDateTime | 否 | - | 工作开始日期 |
| endTime | LocalDateTime | 否 | 不能早于开始日期（@AssertTrue） | 工作结束日期 |
| reason | String | 否 | @Size(max=1024) | 离职原因 |
| witnessName | String | 否 | @Size(max=255) | 证明人 |
| witnessPhone | String | 否 | @Size(max=32) | 证明人手机号 |
| remark | String | 否 | @Size(max=500) | 工作备注 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; — 工作经历编号

**业务逻辑**:
1. 校验员工存在。
2. 起止日期取自然日后插入工作经历，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 11.3 更新员工工作经历

- **路径**: PUT /hrm/employee/work-experience/update
- **权限**: hrm:employee:update
- **说明**: 更新工作经历，不允许变更所属员工。

**请求参数**: 同 HrmEmployeeWorkExperienceSaveReqVO（见 11.2，id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工和工作经历存在，且归属该员工。
2. 更新工作经历（清空 employeeId 防止变更归属），记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_017 | 员工工作经历不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |

### 11.4 删除员工工作经历

- **路径**: DELETE /hrm/employee/work-experience/delete
- **权限**: hrm:employee:delete
- **说明**: 按编号删除工作经历。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 工作经历编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验工作经历存在后删除，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_017 | 员工工作经历不存在 |

## 12. 员工培训经历（HrmEmployeeTrainingExperienceController）

### 12.1 获得员工培训经历列表

- **路径**: GET /hrm/employee/training-experience/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询培训经历。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeTrainingExperienceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 培训经历编号 |
| employeeId | Long | 员工编号 |
| course | String | 培训课程 |
| organizationName | String | 培训机构名称 |
| startTime | LocalDateTime | 培训开始日期 |
| endTime | LocalDateTime | 培训结束日期 |
| duration | String | 培训时长 |
| result | String | 培训成绩 |
| certificateName | String | 培训证书名称 |
| remark | String | 备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询培训经历列表并转换为 VO。

### 12.2 创建员工培训经历

- **路径**: POST /hrm/employee/training-experience/create
- **权限**: hrm:employee:update
- **说明**: 为员工新增一条培训经历。

**请求参数 (HrmEmployeeTrainingExperienceSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 培训经历编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| course | String | 是 | @NotBlank、@Size(max=128) | 培训课程 |
| organizationName | String | 否 | @Size(max=128) | 培训机构名称 |
| startTime | LocalDateTime | 否 | - | 培训开始日期 |
| endTime | LocalDateTime | 否 | 不能早于开始日期（@AssertTrue） | 培训结束日期 |
| duration | String | 否 | @Size(max=64) | 培训时长 |
| result | String | 否 | @Size(max=64) | 培训成绩 |
| certificateName | String | 否 | @Size(max=128) | 培训证书名称 |
| remark | String | 否 | @Size(max=500) | 备注 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; — 培训经历编号

**业务逻辑**:
1. 校验员工存在。
2. 起止日期取自然日后插入培训经历，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 12.3 更新员工培训经历

- **路径**: PUT /hrm/employee/training-experience/update
- **权限**: hrm:employee:update
- **说明**: 更新培训经历，不允许变更所属员工。

**请求参数**: 同 HrmEmployeeTrainingExperienceSaveReqVO（见 12.2，id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工和培训经历存在，且归属该员工。
2. 更新培训经历（清空 employeeId 防止变更归属），记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_018 | 员工培训经历不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |

### 12.4 删除员工培训经历

- **路径**: DELETE /hrm/employee/training-experience/delete
- **权限**: hrm:employee:delete
- **说明**: 按编号删除培训经历。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 培训经历编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验培训经历存在后删除，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_018 | 员工培训经历不存在 |

## 13. 员工证书（HrmEmployeeCertificateController）

### 13.1 获得员工证书列表

- **路径**: GET /hrm/employee/certificate/list
- **权限**: hrm:employee:query
- **说明**: 按员工编号查询证书。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | - | 员工编号 |

**响应**: CommonResult&lt;List&lt;HrmEmployeeCertificateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 证书记录编号 |
| employeeId | Long | 员工编号 |
| name | String | 证书名称 |
| level | String | 证书级别 |
| no | String | 证书编号 |
| startTime | LocalDateTime | 有效起始日期 |
| endTime | LocalDateTime | 有效结束日期 |
| issuingAuthority | String | 发证机构 |
| issuingTime | LocalDateTime | 发证日期 |
| remark | String | 备注 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按员工编号查询证书列表并转换为 VO。

### 13.2 创建员工证书

- **路径**: POST /hrm/employee/certificate/create
- **权限**: hrm:employee:update
- **说明**: 为员工新增一条证书。

**请求参数 (HrmEmployeeCertificateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 证书记录编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 证书名称 |
| level | String | 否 | @Size(max=255) | 证书级别 |
| no | String | 否 | @Size(max=255) | 证书编号 |
| startTime | LocalDateTime | 否 | - | 有效起始日期 |
| endTime | LocalDateTime | 否 | 不能早于开始日期（@AssertTrue） | 有效结束日期 |
| issuingAuthority | String | 否 | @Size(max=255) | 发证机构 |
| issuingTime | LocalDateTime | 否 | - | 发证日期 |
| remark | String | 否 | @Size(max=500) | 备注 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; — 证书记录编号

**业务逻辑**:
1. 校验员工存在。
2. 有效期和发证日期取自然日后插入证书，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |

### 13.3 更新员工证书

- **路径**: PUT /hrm/employee/certificate/update
- **权限**: hrm:employee:update
- **说明**: 更新证书，不允许变更所属员工。

**请求参数**: 同 HrmEmployeeCertificateSaveReqVO（见 13.2，id 必传用于定位）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验员工和证书存在，且归属该员工。
2. 更新证书（清空 employeeId 防止变更归属），记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_000 | 员工档案不存在 |
| 1_050_100_019 | 员工证书不存在 |
| 1_050_100_029 | 员工{}不属于指定员工 |

### 13.4 删除员工证书

- **路径**: DELETE /hrm/employee/certificate/delete
- **权限**: hrm:employee:delete
- **说明**: 按编号删除证书。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 证书记录编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验证书存在后删除，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_019 | 员工证书不存在 |
