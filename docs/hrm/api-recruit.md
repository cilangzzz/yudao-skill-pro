# 招聘管理接口 (HrmRecruitPostController / HrmRecruitPostTypeController / HrmRecruitChannelController / HrmRecruitCandidateController / HrmRecruitInterviewController / HrmRecruitConfigController)

> HRM 招聘域接口：覆盖招聘职位、职位类型、招聘渠道、候选人全生命周期（状态流转 / 淘汰 / 转员工）、面试安排与结果登记、招聘配置（淘汰原因）。

## 接口路径前缀

- /hrm/recruit/post (Controller: HrmRecruitPostController)
- /hrm/recruit/post-type (Controller: HrmRecruitPostTypeController)
- /hrm/recruit/channel (Controller: HrmRecruitChannelController)
- /hrm/recruit/candidate (Controller: HrmRecruitCandidateController)
- /hrm/recruit/interview (Controller: HrmRecruitInterviewController)
- /hrm/recruit/config (Controller: HrmRecruitConfigController)

## 1. 招聘职位（/hrm/recruit/post）

### 1.1 创建招聘职位

- **路径**: POST /hrm/recruit/post/create
- **权限**: hrm:recruit:post:create
- **说明**: 新建招聘职位，初始状态固定为「招聘中」。

**请求参数 (HrmRecruitPostSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 招聘职位编号 |
| postName | String | 是 | @NotBlank、@Size(max=255) | 职位名称 |
| deptId | Long | 否 | | 部门编号（用人部门） |
| jobNature | Integer | 是 | @NotNull | 工作性质 |
| areaId | Integer | 否 | | 工作城市地区编号 |
| recruitNum | Integer | 否 | @Min(0) | 招聘人数 |
| reason | String | 否 | @Size(max=255) | 招聘原因 |
| workTime | Integer | 否 | | 工作经验 |
| educationRequire | Integer | 否 | | 学历要求 |
| minSalary | BigDecimal | 否 | @Digits(integer=8, fraction=2) | 最低薪资 |
| maxSalary | BigDecimal | 否 | @Digits(integer=8, fraction=2) | 最高薪资 |
| salaryUnit | Integer | 否 | | 薪资单位 |
| minAge | Integer | 否 | | 最小年龄 |
| maxAge | Integer | 否 | | 最大年龄 |
| latestEntryTime | LocalDateTime | 否 | | 最迟到岗时间 |
| ownerEmployeeId | Long | 否 | | 负责人员工编号 |
| interviewEmployeeIds | List&lt;Long&gt; | 否 | | 面试官员工编号数组 |
| description | String | 否 | @Size(max=4000) | 职位描述 |
| emergencyLevel | Integer | 否 | | 紧急程度 |
| postTypeId | Long | 否 | | 职位类型编号 |

> 类级 @AssertTrue 交叉校验：① 薪资范围不正确 —— 薪资单位为「面议」或任一薪资为面议值时，minSalary/maxSalary/salaryUnit 必须同时为面议值；否则薪资不能为负且 minSalary ≤ maxSalary。② 年龄范围不正确 —— 任一年龄为「不限」值时必须同时为不限值；否则年龄不能为负且 minAge ≤ maxAge。

**响应**: CommonResult&lt;Long&gt;（招聘职位编号）

**业务逻辑**: 1. 校验职位类型存在、部门存在（deptId 非空时）、招聘负责人与面试官均为在职员工。 2. 插入招聘职位，状态统一置为「招聘中」，后续通过状态接口停止招聘。 3. 记录操作日志上下文（@LogRecord 招聘职位创建日志）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_000 | 招聘职位不存在 |
| 1_050_200_004 | 招聘职位类型不存在 |

### 1.2 更新招聘职位

- **路径**: PUT /hrm/recruit/post/update
- **权限**: hrm:recruit:post:update
- **说明**: 按编号修改招聘职位信息。

**请求参数 (HrmRecruitPostSaveReqVO)**: 同 1.1（id 必填用于定位记录）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验招聘职位存在。 2. 校验职位类型、部门、负责人与面试官关联有效。 3. 更新招聘职位。 4. 记录新旧对象 Diff 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_000 | 招聘职位不存在 |
| 1_050_200_004 | 招聘职位类型不存在 |

### 1.3 更新招聘职位状态

- **路径**: PUT /hrm/recruit/post/update-status
- **权限**: hrm:recruit:post:update
- **说明**: 启用招聘 / 停止招聘，停止时必须填写停止原因。

**请求参数 (HrmRecruitPostStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 招聘职位编号 |
| status | Integer | 是 | @NotNull、@InEnum(HrmRecruitPostStatusEnum) | 职位状态（0 停止招聘 / 1 招聘中） |
| stopReason | String | 否 | @Size(max=255)、@AssertTrue（停止招聘时不能为空） | 停止原因 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验招聘职位存在。 2. 更新职位状态：目标为「停止招聘」时写入停止原因，否则清空停止原因。 3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_000 | 招聘职位不存在 |

### 1.4 获得招聘职位

- **路径**: GET /hrm/recruit/post/get
- **权限**: hrm:recruit:post:query
- **说明**: 按编号获得招聘职位详情（含关联信息拼接）。

**请求参数**: Query 参数 id（Long，招聘职位编号，必填）。

**响应**: CommonResult&lt;HrmRecruitPostRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 招聘职位编号 |
| postName | String | 职位名称 |
| deptId | Long | 部门编号 |
| deptName | String | 用人部门名称 |
| jobNature | Integer | 工作性质 |
| areaId | Integer | 工作城市地区编号 |
| areaName | String | 工作城市地区名称 |
| recruitNum | Integer | 招聘人数 |
| reason | String | 招聘原因 |
| workTime | Integer | 工作经验 |
| educationRequire | Integer | 学历要求 |
| minSalary | BigDecimal | 最低薪资 |
| maxSalary | BigDecimal | 最高薪资 |
| salaryUnit | Integer | 薪资单位 |
| minAge | Integer | 最小年龄 |
| maxAge | Integer | 最大年龄 |
| latestEntryTime | LocalDateTime | 最迟到岗时间 |
| ownerEmployeeId | Long | 招聘负责人员工编号 |
| ownerEmployeeName | String | 招聘负责人姓名 |
| interviewEmployeeIds | List&lt;Long&gt; | 面试官员工编号数组 |
| interviewEmployeeNames | List&lt;String&gt; | 面试官姓名数组 |
| description | String | 职位描述 |
| emergencyLevel | Integer | 紧急程度 |
| postTypeId | Long | 职位类型编号 |
| postTypeName | String | 职位类型名称 |
| status | Integer | 职位状态 |
| stopReason | String | 停止原因 |
| hasEntryNum | Long | 已入职人数 |
| recruitSchedule | BigDecimal | 招聘进度百分比 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 查询职位记录。 2. 拼接负责人 / 面试官员工姓名、部门名称、职位类型名称、地区名称。 3. 统计已入职候选人数，并按 `已入职人数 / 招聘人数 × 100`（保留 2 位小数）计算招聘进度。

### 1.5 获得招聘职位分页

- **路径**: GET /hrm/recruit/post/page
- **权限**: hrm:recruit:post:query
- **说明**: 分页查询招聘职位，响应结构同 1.4。

**请求参数 (HrmRecruitPostPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |
| postName | String | 否 | | 职位名称，模糊匹配 |
| jobNature | Integer | 否 | | 工作性质 |
| areaId | Integer | 否 | | 工作城市地区编号 |
| deptId | Long | 否 | | 部门编号 |
| ownerEmployeeId | Long | 否 | | 招聘负责人员工编号 |
| postTypeId | Long | 否 | | 职位类型编号 |
| status | Integer | 否 | | 职位状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间范围 |

**响应**: CommonResult&lt;PageResult&lt;HrmRecruitPostRespVO&gt;&gt;（响应字段同 1.4）。

**业务逻辑**: 1. 按条件分页查询职位。 2. 批量拼接员工、部门、职位类型信息及已入职人数、招聘进度。

### 1.6 获得招聘职位精简列表

- **路径**: GET /hrm/recruit/post/simple-list
- **权限**: hrm:recruit:post:query
- **说明**: 获得招聘中的职位下拉精简列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmRecruitPostRespVO&gt;&gt;（仅返回 id、postName、status 三个字段）。

**业务逻辑**: 1. 查询状态为「招聘中」的全部职位。 2. 仅映射 id / postName / status 返回。

### 1.7 获得招聘职位状态数量

- **路径**: GET /hrm/recruit/post/status-count
- **权限**: hrm:recruit:post:query
- **说明**: 按职位状态分组统计数量（用于状态 Tab）。

**请求参数 (HrmRecruitPostPageReqVO)**: 同 1.5（作为统计过滤条件）。

**响应**: CommonResult&lt;List&lt;HrmRecruitStatusCountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 职位状态 |
| count | Long | 数量 |

**业务逻辑**: 1. 按分页条件对职位按状态分组计数。 2. 遍历全部职位状态枚举，缺失状态补 0 返回。

## 2. 招聘职位类型（/hrm/recruit/post-type）

### 2.1 获得招聘职位类型列表

- **路径**: GET /hrm/recruit/post-type/list
- **权限**: hrm:recruit:post:query
- **说明**: 获得职位类型全量（或按状态过滤）列表。

**请求参数**: Query 参数 status（Integer，可选，状态过滤）。

**响应**: CommonResult&lt;List&lt;HrmRecruitPostTypeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 职位类型编号 |
| name | String | 类型名称 |
| parentId | Long | 父类型编号 |
| sort | Integer | 排序 |
| status | Integer | 状态（common_status） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按状态（可为空）查询职位类型列表并直接转换返回。

## 3. 招聘渠道（/hrm/recruit/channel）

### 3.1 创建招聘渠道

- **路径**: POST /hrm/recruit/channel/create
- **权限**: hrm:recruit:channel:create
- **说明**: 新建自定义招聘渠道，初始为启用状态。

**请求参数 (HrmRecruitChannelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 招聘渠道编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 渠道名称 |
| sort | Integer | 是 | @NotNull、@Min(0) | 显示顺序 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Long&gt;（招聘渠道编号）

**业务逻辑**: 1. 插入招聘渠道，systemFlag 置为 false（非系统内置）、状态置为启用。 2. 记录操作日志。

### 3.2 更新招聘渠道

- **路径**: PUT /hrm/recruit/channel/update
- **权限**: hrm:recruit:channel:update
- **说明**: 修改招聘渠道；系统内置渠道不允许修改名称。

**请求参数 (HrmRecruitChannelSaveReqVO)**: 同 3.1（id 必填用于定位记录）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验渠道存在；若为系统内置渠道且修改了名称则拒绝（仅允许调整排序和备注）。 2. 更新招聘渠道。 3. 记录新旧对象 Diff 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_003 | 招聘渠道不存在 |
| 1_050_200_005 | 系统内置招聘渠道不允许修改名称 |

### 3.3 更新招聘渠道状态

- **路径**: PUT /hrm/recruit/channel/update-status
- **权限**: hrm:recruit:channel:update
- **说明**: 启用 / 停用招聘渠道。

**请求参数 (HrmRecruitChannelStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 招聘渠道编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 停用） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验渠道存在。 2. 仅更新渠道状态字段。 3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_003 | 招聘渠道不存在 |

### 3.4 删除招聘渠道

- **路径**: DELETE /hrm/recruit/channel/delete
- **权限**: hrm:recruit:channel:delete
- **说明**: 删除渠道前须指定承接渠道，迁移其下员工与候选人引用。

**请求参数 (HrmRecruitChannelDeleteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 待删除招聘渠道编号 |
| transferChannelId | Long | 是 | @NotNull | 承接招聘渠道编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验待删除渠道存在且非系统内置；承接渠道不能是待删除渠道自身。 2. 校验承接渠道存在且为启用状态。 3. 事务内将员工档案、候选人的渠道引用迁移到承接渠道，再删除原渠道。 4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_003 | 招聘渠道不存在 |
| 1_050_200_006 | 系统内置招聘渠道不允许删除 |
| 1_050_200_007 | 承接招聘渠道不能是待删除渠道 |
| 1_050_200_008 | 承接招聘渠道已停用 |

### 3.5 获得招聘渠道

- **路径**: GET /hrm/recruit/channel/get
- **权限**: hrm:recruit:channel:query
- **说明**: 按编号获得招聘渠道详情。

**请求参数**: Query 参数 id（Long，招聘渠道编号，必填）。

**响应**: CommonResult&lt;HrmRecruitChannelRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 招聘渠道编号 |
| systemFlag | Boolean | 是否系统内置 |
| status | Integer | 状态 |
| name | String | 渠道名称 |
| sort | Integer | 显示顺序 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询渠道并转换为 RespVO 返回。

### 3.6 获得招聘渠道分页

- **路径**: GET /hrm/recruit/channel/page
- **权限**: hrm:recruit:channel:query
- **说明**: 分页查询招聘渠道。

**请求参数 (HrmRecruitChannelPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |
| name | String | 否 | | 渠道名称，模糊匹配 |
| status | Integer | 否 | | 状态 |

**响应**: CommonResult&lt;PageResult&lt;HrmRecruitChannelRespVO&gt;&gt;（响应字段同 3.5）。

**业务逻辑**: 1. 按名称模糊、状态条件分页查询渠道。

### 3.7 获得招聘渠道精简列表

- **路径**: GET /hrm/recruit/channel/simple-list
- **权限**: 已认证（无 @PreAuthorize，供招聘职位、候选人等表单下拉使用）
- **说明**: 获得启用状态的招聘渠道下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmRecruitChannelRespVO&gt;&gt;（仅返回 id、name、status 三个字段）。

**业务逻辑**: 1. 查询状态为启用的全部渠道。 2. 仅映射 id / name / status 返回。

## 4. 招聘候选人（/hrm/recruit/candidate）

> 候选人状态枚举：1 新候选人、2 初选通过、3 安排面试、4 面试通过、5 已发 offer、6 待入职、7 已淘汰、8 已入职。

### 4.1 创建招聘候选人

- **路径**: POST /hrm/recruit/candidate/create
- **权限**: hrm:recruit:candidate:create
- **说明**: 新建候选人，初始状态由后端统一设置为「新候选人」。

**请求参数 (HrmRecruitCandidateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 候选人编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 候选人姓名 |
| mobile | String | 是 | @NotBlank、@Size(max=18)、@Pattern(手机号正则) | 手机号码 |
| sex | Integer | 是 | @NotNull | 性别 |
| age | Integer | 否 | @Min(0)、@Max(99) | 年龄 |
| email | String | 否 | @Email、@Size(max=255) | 邮箱 |
| postId | Long | 是 | @NotNull | 应聘职位编号 |
| workTime | Integer | 否 | @Min(0)、@Max(60) | 工作年限 |
| education | Integer | 是 | @NotNull | 学历 |
| graduateSchool | String | 否 | @Size(max=255) | 毕业院校 |
| latestWorkPlace | String | 否 | @Size(max=255) | 最近工作单位 |
| channelId | Long | 否 | | 招聘渠道编号 |
| remark | String | 否 | @Size(max=255) | 备注 |
| resumeUrls | List&lt;String&gt; | 否 | @Size(max=5)，元素 @Size(max=512) | 简历附件地址数组 |

**响应**: CommonResult&lt;Long&gt;（候选人编号）

**业务逻辑**: 1. 校验招聘职位存在；渠道编号非空时校验渠道存在。 2. 插入候选人，状态置为「新候选人」、面试轮次置 0、记录状态更新时间。 3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_000 | 招聘职位不存在 |
| 1_050_200_003 | 招聘渠道不存在 |

### 4.2 更新招聘候选人

- **路径**: PUT /hrm/recruit/candidate/update
- **权限**: hrm:recruit:candidate:update
- **说明**: 按编号修改候选人基本信息。

**请求参数 (HrmRecruitCandidateSaveReqVO)**: 同 4.1（id 必填用于定位记录）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验候选人存在、应聘职位存在；渠道编号非空时校验渠道存在。 2. 更新候选人（updateForEdit）。 3. 记录新旧对象 Diff 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_000 | 招聘职位不存在 |
| 1_050_200_003 | 招聘渠道不存在 |

### 4.3 更新招聘候选人状态

- **路径**: PUT /hrm/recruit/candidate/update-status
- **权限**: hrm:recruit:candidate:update
- **说明**: 通用状态流转接口；面试中、待入职、已入职等聚合状态必须走专用接口，不允许在此直接跳转。

**请求参数 (HrmRecruitCandidateUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 候选人编号 |
| status | Integer | 是 | @NotNull、@InEnum(HrmRecruitCandidateStatusEnum) | 候选人状态 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 行锁校验候选人存在；状态未变化时直接返回。 2. 校验状态流转规则：新候选人 → 初选通过 / 面试通过；初选通过 → 新候选人 / 面试通过；面试通过 → 已发 offer / 新候选人 / 初选通过；已淘汰 → 仅可恢复为新候选人。 3. 更新候选人状态与状态更新时间。 4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_011 | 候选人当前状态不允许流转到【{}】 |

### 4.4 更新招聘候选人应聘职位

- **路径**: PUT /hrm/recruit/candidate/update-post
- **权限**: hrm:recruit:candidate:update
- **说明**: 调整候选人的应聘职位。

**请求参数 (HrmRecruitCandidateUpdatePostReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 候选人编号 |
| postId | Long | 是 | @NotNull | 职位编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验候选人存在、目标职位存在。 2. 仅更新候选人 postId 字段。 3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_000 | 招聘职位不存在 |

### 4.5 更新招聘候选人渠道

- **路径**: PUT /hrm/recruit/candidate/update-channel
- **权限**: hrm:recruit:candidate:update
- **说明**: 调整候选人的招聘渠道。

**请求参数 (HrmRecruitCandidateUpdateChannelReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 候选人编号 |
| channelId | Long | 是 | @NotNull | 招聘渠道编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验候选人存在、目标渠道存在。 2. 仅更新候选人 channelId 字段。 3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_003 | 招聘渠道不存在 |

### 4.6 淘汰招聘候选人

- **路径**: PUT /hrm/recruit/candidate/eliminate
- **权限**: hrm:recruit:candidate:update
- **说明**: 淘汰候选人并记录淘汰原因；面试中候选人会同步结束当前面试，已生成的员工档案会被删除。

**请求参数 (HrmRecruitCandidateUpdateEliminateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 候选人编号 |
| eliminate | String | 是 | @NotBlank、@Size(max=255) | 淘汰原因 |
| remark | String | 否 | @Size(max=255) | 备注 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 行锁校验候选人存在，且状态在允许淘汰集合内（新候选人 / 初选通过 / 安排面试 / 面试通过 / 已发 offer / 待入职）。 2. 若处于「安排面试」状态，将当前面试记录置为「面试未通过」，评价写淘汰原因，避免状态矛盾。 3. 若候选人已生成员工档案，删除该员工档案。 4. 更新候选人为「已淘汰」，记录淘汰原因、备注与状态更新时间。 5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_018 | 候选人当前状态不允许淘汰 |
| 1_050_200_013 | 候选人当前状态不允许安排或修改面试 |

### 4.7 候选人转员工档案

- **路径**: POST /hrm/recruit/candidate/convert-employee
- **权限**: hrm:recruit:candidate:update
- **说明**: 将面试通过 / 已发 offer 的候选人转为员工档案，返回新员工编号。

**请求参数 (HrmRecruitCandidateEntryReqVO，继承 HrmEmployeeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| candidateId | Long | 是 | @AssertTrue（不能为空） | 关联招聘候选人编号 |
| （其余字段） | - | 见员工档案 VO | | 继承 HrmEmployeeSaveReqVO 的员工建档字段（姓名、手机、入职状态、部门、岗位、入职时间 entryTime 等） |

**响应**: CommonResult&lt;Long&gt;（新员工档案编号）

**业务逻辑**: 1. 行锁校验候选人存在，状态须为「面试通过」或「已发 offer」；已生成过员工档案则报错；校验其应聘职位存在。 2. 以入参（继承员工保存 VO）创建员工档案，清空 id、绑定 candidateId，招聘渠道取候选人渠道。 3. 按员工入职状态更新候选人：员工为「在职」则候选人不进入待入职直接置「已入职」，否则置「待入职」，同时记录入职时间与状态更新时间。 4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_017 | 候选人当前状态不允许转为员工 |
| 1_050_100_005 | 招聘候选人已转为员工档案 |
| 1_050_200_000 | 招聘职位不存在 |

### 4.8 删除招聘候选人

- **路径**: DELETE /hrm/recruit/candidate/delete
- **权限**: hrm:recruit:candidate:delete
- **说明**: 删除候选人及其面试记录；已生成员工档案的候选人不可删除。

**请求参数**: Query 参数 id（Long，候选人编号，必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 行锁校验候选人存在，状态必须是 新候选人 / 初选通过 / 安排面试 / 面试通过 / 已淘汰 之一；已生成员工档案则报错。 2. 事务内先删除候选人的全部面试记录，再删除候选人。 3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_016 | 候选人当前状态不允许删除 |
| 1_050_200_012 | 候选人已生成员工档案，不能删除 |

### 4.9 获得招聘候选人

- **路径**: GET /hrm/recruit/candidate/get
- **权限**: hrm:recruit:candidate:query
- **说明**: 获得候选人详情（含职位 / 渠道 / 面试 / 员工关联信息拼接）。

**请求参数**: Query 参数 id（Long，候选人编号，必填）。

**响应**: CommonResult&lt;HrmRecruitCandidateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 候选人编号 |
| name | String | 候选人姓名 |
| mobile | String | 手机号码 |
| sex | Integer | 性别 |
| age | Integer | 年龄 |
| email | String | 邮箱 |
| postId | Long | 应聘职位编号 |
| postName | String | 应聘职位名称 |
| postStatus | Integer | 应聘职位状态 |
| deptId | Long | 用人部门编号 |
| deptName | String | 用人部门名称 |
| ownerEmployeeId | Long | 招聘负责人员工编号 |
| ownerEmployeeName | String | 招聘负责人姓名 |
| stageNumber | Integer | 面试轮次 |
| workTime | Integer | 工作年限 |
| education | Integer | 学历 |
| graduateSchool | String | 毕业院校 |
| latestWorkPlace | String | 最近工作单位 |
| channelId | Long | 招聘渠道编号 |
| channelName | String | 招聘渠道名称 |
| remark | String | 备注 |
| status | Integer | 候选人状态 |
| eliminate | String | 淘汰原因 |
| statusUpdateTime | LocalDateTime | 状态更新时间 |
| entryTime | LocalDateTime | 入职时间 |
| resumeUrls | List&lt;String&gt; | 简历附件地址数组 |
| interviewId | Long | 当前面试编号 |
| interviewType | Integer | 面试方式 |
| interviewEmployeeId | Long | 主面试官员工编号 |
| interviewEmployeeName | String | 主面试官姓名 |
| otherInterviewEmployeeIds | List&lt;Long&gt; | 其他面试官员工编号数组 |
| otherInterviewEmployeeNames | List&lt;String&gt; | 其他面试官姓名数组 |
| interviewTime | LocalDateTime | 面试时间 |
| interviewAddress | String | 面试地址 |
| interviewResult | Integer | 面试结果 |
| employeeId | Long | 转入的员工编号 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**: 1. 查询候选人并批量拼接职位、部门、招聘负责人、渠道信息。 2. 查询候选人最近一场面试：仅面试相关状态展示面试方式、面试官、时间、地址、结果，其余状态轮次展示为 0。 3. 拼接已转员工编号与创建人昵称。

### 4.10 获得招聘候选人分页

- **路径**: GET /hrm/recruit/candidate/page
- **权限**: hrm:recruit:candidate:query
- **说明**: 多条件分页查询候选人，响应结构同 4.9。

**请求参数 (HrmRecruitCandidatePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |
| search | String | 否 | | 姓名、手机号码或邮箱，模糊匹配 |
| postId | Long | 否 | | 职位编号 |
| ownerEmployeeId | Long | 否 | | 招聘负责人员工编号 |
| sex | Integer | 否 | | 性别 |
| minAge | Integer | 否 | | 最小年龄 |
| maxAge | Integer | 否 | | 最大年龄 |
| minWorkTime | Integer | 否 | | 最小工作年限 |
| maxWorkTime | Integer | 否 | | 最大工作年限 |
| education | Integer | 否 | | 学历 |
| graduateSchool | String | 否 | | 毕业院校，模糊匹配 |
| latestWorkPlace | String | 否 | | 最近工作单位，模糊匹配 |
| channelId | Long | 否 | | 渠道编号 |
| interviewEmployeeId | Long | 否 | | 面试官员工编号 |
| interviewTime | LocalDateTime[] | 否 | @DateTimeFormat | 面试时间范围 |
| creator | Long | 否 | | 创建人用户编号 |
| status | Integer | 否 | @InEnum(HrmRecruitCandidateStatusEnum) | 候选人状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间范围 |

**响应**: CommonResult&lt;PageResult&lt;HrmRecruitCandidateRespVO&gt;&gt;（响应字段同 4.9）。

**业务逻辑**: 1. 按条件分页查询候选人。 2. 批量拼接职位 / 部门 / 渠道 / 最新面试 / 员工 / 创建人信息。

### 4.11 获得待清理候选人编号

- **路径**: GET /hrm/recruit/candidate/clean-ids
- **权限**: hrm:recruit:candidate:delete
- **说明**: 查询在指定状态下停留超过 N 天的候选人编号，用于批量清理。

**请求参数 (HrmRecruitCandidateCleanReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| statuses | List&lt;Integer&gt; | 是 | @NotEmpty，元素 @NotNull、@InEnum(HrmRecruitCandidateStatusEnum) | 候选人状态数组 |
| days | Integer | 是 | @NotNull、@Positive | 状态持续天数 |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt;（候选人编号列表）

**业务逻辑**: 1. 以「当前时间 - days」为截止时间，查询状态命中且状态更新时间早于该时间的候选人。 2. 返回其编号列表。

### 4.12 获得候选人状态数量

- **路径**: GET /hrm/recruit/candidate/status-count
- **权限**: hrm:recruit:candidate:query
- **说明**: 按候选人状态分组统计数量（用于状态 Tab）。

**请求参数 (HrmRecruitCandidatePageReqVO)**: 同 4.10（作为统计过滤条件）。

**响应**: CommonResult&lt;List&lt;HrmRecruitStatusCountRespVO&gt;&gt;（响应字段同 1.7：status、count）。

**业务逻辑**: 1. 按分页条件对候选人按状态分组计数。 2. 遍历全部候选人状态枚举，缺失状态补 0 返回。

## 5. 招聘面试（/hrm/recruit/interview）

> 面试结果枚举：1 面试未完成、2 面试通过、3 面试未通过、4 面试取消。

### 5.1 创建招聘面试

- **路径**: POST /hrm/recruit/interview/create
- **权限**: hrm:recruit:interview:create
- **说明**: 为候选人安排面试；候选人停留在当前轮次时复用最近一场记录重新安排，否则进入下一轮。

**请求参数 (HrmRecruitInterviewSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 面试编号 |
| candidateId | Long | 是 | @NotNull | 候选人编号 |
| type | Integer | 是 | @NotNull | 面试方式 |
| stageNumber | Integer | 否 | | 面试轮次（后端自动计算，入参忽略） |
| interviewEmployeeId | Long | 是 | @NotNull | 主面试官员工编号 |
| otherInterviewEmployeeIds | List&lt;Long&gt; | 否 | | 其他面试官员工编号数组 |
| interviewTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat | 面试时间 |
| address | String | 否 | @Size(max=255) | 面试地址 |
| remark | String | 否 | @Size(max=255) | 备注 |

**响应**: CommonResult&lt;Long&gt;（面试编号）

**业务逻辑**: 1. 行锁校验候选人存在且状态允许安排面试（新候选人 / 初选通过 / 安排面试 / 面试通过）；校验主面试官与其他面试官（去重并排除主面试官）均为在职员工。 2. 若候选人处于「安排面试」状态且最近一场面试结果为未完成 / 已取消则复用该记录重新安排（保持原轮次、结果置未完成），否则新插入记录（轮次 = 最近轮次 + 1，首轮为 1，结果置未完成）。 3. 更新候选人状态为「安排面试」及面试轮次、状态更新时间。 4. 向绑定了后台账号的面试官发送面试安排站内信（候选人姓名、轮次、时间）。 5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_013 | 候选人当前状态不允许安排或修改面试 |
| 1_050_200_014 | 只能操作候选人当前轮次的面试 |

### 5.2 更新招聘面试

- **路径**: PUT /hrm/recruit/interview/update
- **权限**: hrm:recruit:interview:update
- **说明**: 修改候选人当前轮次的面试安排；已完成的面试不允许修改。

**请求参数 (HrmRecruitInterviewSaveReqVO)**: 同 5.1（id 必填用于定位记录）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验面试记录存在、候选人行锁存在、该面试为候选人当前轮次、面试官有效。 2. 面试结果非未完成 / 已取消（即已完成）时拒绝修改。 3. 更新面试安排（保持候选人与轮次），结果重置为未完成；原为「已取消」时恢复候选人的面试状态与轮次。 4. 通知面试官。 5. 记录新旧对象 Diff 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_002 | 招聘面试不存在 |
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_014 | 只能操作候选人当前轮次的面试 |
| 1_050_200_009 | 已完成的招聘面试不允许修改安排 |
| 1_050_200_013 | 候选人当前状态不允许安排或修改面试 |

### 5.3 更新招聘面试结果

- **路径**: PUT /hrm/recruit/interview/update-result
- **权限**: hrm:recruit:interview:update
- **说明**: 对当前未完成面试登记通过 / 未通过 / 取消结果，并联动候选人状态。

**请求参数 (HrmRecruitInterviewResultReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 面试编号 |
| result | Integer | 是 | @NotNull、@AssertTrue（必须是通过 / 未通过 / 取消） | 面试结果 |
| evaluate | String | 否 | @Size(max=255) | 评价（取消时忽略） |
| cancelReason | String | 否 | @Size(max=255)、取消时必填 | 取消原因 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验面试记录、候选人存在（行锁），且该面试为候选人当前轮次。 2. 仅未完成面试允许登记结果，且结果不能是「未完成」；结果为「取消」时必须填写取消原因。 3. 更新面试结果：取消时仅保留取消原因，否则保留评价。 4. 联动候选人状态：通过 → 「面试通过」；未通过 → 「已淘汰」；取消 → 仅刷新候选人状态更新时间。 5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_002 | 招聘面试不存在 |
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_014 | 只能操作候选人当前轮次的面试 |
| 1_050_200_015 | 当前面试状态或面试结果不允许提交 |
| 1_050_200_010 | 取消面试时必须填写取消原因 |

### 5.4 删除招聘面试

- **路径**: DELETE /hrm/recruit/interview/delete
- **权限**: hrm:recruit:interview:delete
- **说明**: 删除面试记录；删除当前轮次面试后按剩余最近一场修复候选人状态。

**请求参数**: Query 参数 id（Long，面试编号，必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验面试记录与候选人（行锁）存在；若为候选人最近一场面试，须校验候选人处于「安排面试」状态且轮次匹配。 2. 删除面试记录。 3. 若删除的是当前面试：无剩余面试时候选人恢复「新候选人」、轮次 0；有剩余时按最近一场结果（未完成 → 安排面试，通过 → 面试通过，未通过 → 已淘汰）修复候选人状态与轮次。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_200_002 | 招聘面试不存在 |
| 1_050_200_001 | 招聘候选人不存在 |
| 1_050_200_014 | 只能操作候选人当前轮次的面试 |

### 5.5 获得招聘面试

- **路径**: GET /hrm/recruit/interview/get
- **权限**: hrm:recruit:interview:query
- **说明**: 按编号获得面试详情（含面试官姓名）。

**请求参数**: Query 参数 id（Long，面试编号，必填）。

**响应**: CommonResult&lt;HrmRecruitInterviewRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 面试编号 |
| candidateId | Long | 候选人编号 |
| type | Integer | 面试方式 |
| stageNumber | Integer | 面试轮次 |
| interviewEmployeeId | Long | 主面试官员工编号 |
| interviewEmployeeName | String | 主面试官姓名 |
| otherInterviewEmployeeIds | List&lt;Long&gt; | 其他面试官员工编号数组 |
| otherInterviewEmployeeNames | List&lt;String&gt; | 其他面试官姓名数组 |
| interviewTime | LocalDateTime | 面试时间 |
| address | String | 面试地址 |
| remark | String | 备注 |
| result | Integer | 面试结果 |
| evaluate | String | 评价 |
| cancelReason | String | 取消原因 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 查询面试记录。 2. 拼接主面试官与其他面试官姓名。

### 5.6 获得候选人的招聘面试列表

- **路径**: GET /hrm/recruit/interview/list-by-candidate
- **权限**: hrm:recruit:interview:query
- **说明**: 获得某候选人全部面试记录（按轮次展示）。

**请求参数**: Query 参数 candidateId（Long，候选人编号，必填）。

**响应**: CommonResult&lt;List&lt;HrmRecruitInterviewRespVO&gt;&gt;（响应字段同 5.5）。

**业务逻辑**: 1. 按候选人编号查询其全部面试记录。 2. 批量拼接主面试官与其他面试官姓名。

## 6. 招聘设置（/hrm/recruit/config）

### 6.1 保存招聘淘汰原因

- **路径**: POST /hrm/recruit/config/eliminate-reason/save
- **权限**: hrm:recruit:config:update
- **说明**: 全量替换招聘淘汰原因字典（去重、去空白）。

**请求参数 (HrmRecruitEliminateReasonSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| reasons | List&lt;String&gt; | 是 | @NotNull，元素 @NotBlank | 淘汰原因列表 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 对原因列表去除首尾空白、过滤空白项并去重。 2. 以 RECRUIT_ELIMINATE 配置类型全量替换 HRM 配置中的淘汰原因值。 3. 记录新旧配置 Diff 操作日志。

### 6.2 获得招聘淘汰原因列表

- **路径**: GET /hrm/recruit/config/eliminate-reason/list
- **权限**: hrm:recruit:config:query 或 hrm:recruit:candidate:update
- **说明**: 获得配置的招聘淘汰原因列表（候选人淘汰表单下拉用）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;String&gt;&gt;（淘汰原因字符串列表）

**业务逻辑**: 1. 读取 RECRUIT_ELIMINATE 配置类型的配置值列表返回。
