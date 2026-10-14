# OA 工作汇报接口 (OaWorkReportController)

> 提供员工日报/周报/月报的草稿管理与提交、个人汇报分页查询，以及面向管理者的下属汇报完成度统计。

## 接口路径前缀

/oa/work-report  (Controller: OaWorkReportController)

汇报类型（`type`）：1 日报、2 周报、3 月报（`OaWorkReportTypeEnum`）；汇报状态（`status`）：1 草稿、2 已提交（`OaWorkReportStatusEnum`）。

## 1. 我的汇报

### 1.1 创建工作汇报草稿

- **路径**: POST /oa/work-report/create
- **权限**: oa:work-report:create
- **说明**: 创建一份属于当前登录用户的工作汇报草稿，自动生成汇报单号与默认标题。

**请求参数 (OaWorkReportSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | — | 汇报编号（创建时不传） |
| type | Integer | 是 | @NotNull、@InEnum(OaWorkReportTypeEnum) | 汇报类型（1 日报、2 周报、3 月报） |
| title | String | 否 | @Size(max = 255) | 汇报标题，为空时自动生成“{周期} 工作{日报/周报/月报}” |
| startTime | LocalDateTime | 是 | @NotNull | 周期开始时间 |
| endTime | LocalDateTime | 是 | @NotNull | 周期结束时间 |
| summary | String | 否 | @Size(max = 5000) | 工作总结 |
| plan | String | 否 | @Size(max = 5000) | 工作计划补充说明 |
| problem | String | 否 | @Size(max = 5000) | 问题与协调事项 |
| workItems | List\<WorkItem\> | 否 | @Valid、@Size(max = 100)、元素 @NotNull | 已完成工作项 |
| workItems[].content | String | 是 | @NotBlank、@Size(max = 1000) | 工作内容 |
| workItems[].progress | Integer | 是 | @NotNull、@Min(0)、@Max(100) | 完成进度（百分比） |
| planItems | List\<PlanItem\> | 否 | @Valid、@Size(max = 100)、元素 @NotNull | 工作计划项 |
| planItems[].content | String | 是 | @NotBlank、@Size(max = 1000) | 计划内容 |
| fileUrls | List\<String\> | 否 | @Size(max = 10)、元素 @NotBlank、@Size(max = 1024) | 附件地址列表 |
| remark | String | 否 | @Size(max = 1000) | 备注 |

类级校验（@AssertTrue）：周期结束时间不能早于开始时间；工作总结、计划说明、工作项、计划项至少填写其一（“请填写工作总结、计划说明或工作明细”）。

**响应**: CommonResult\<Long\> — 汇报编号。

**业务逻辑**:
1. 调用 `adminUserApi.validateUser` 校验汇报人（当前登录用户）信息。
2. 通过 `OaNoRedisDAO` 按前缀 `WORK_REPORT_NO_PREFIX` 生成汇报单号，并查询数据库校验唯一性，重复则抛出“工作汇报单号已存在”。
3. 组装 DO：写入单号，标题为空时按“周期 + 汇报类型名称”生成默认标题（如“2026-09-14 工作日报”），状态置为草稿，部门取汇报人所在部门。
4. 插入数据库并返回汇报编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_240_005 | 工作汇报单号已存在 |

### 1.2 更新工作汇报草稿

- **路径**: PUT /oa/work-report/update
- **权限**: oa:work-report:update
- **说明**: 修改本人草稿状态的汇报内容，请求体同 1.1 的 OaWorkReportSaveReqVO（id 必传）。

**请求参数 (OaWorkReportSaveReqVO)**: 同 1.1，其中 `id` 为必传的汇报编号。

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作汇报存在且属于当前用户（creator 与登录用户不一致时抛出“无权访问该工作汇报”）。
2. 校验汇报处于草稿状态，否则抛出“当前工作汇报状态不允许该操作”。
3. 更新汇报内容；标题为空时按周期与类型重新生成默认标题。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_240_000 | 工作汇报不存在 |
| 1_054_240_001 | 无权访问该工作汇报 |
| 1_054_240_002 | 当前工作汇报状态不允许该操作 |

### 1.3 删除工作汇报草稿

- **路径**: DELETE /oa/work-report/delete
- **权限**: oa:work-report:delete
- **说明**: 删除本人草稿状态的汇报。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | — | 汇报编号 |

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作汇报存在且属于当前用户。
2. 校验汇报处于草稿状态。
3. 删除该汇报记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_240_000 | 工作汇报不存在 |
| 1_054_240_001 | 无权访问该工作汇报 |
| 1_054_240_002 | 当前工作汇报状态不允许该操作 |

### 1.4 提交工作汇报

- **路径**: PUT /oa/work-report/submit
- **权限**: oa:work-report:update
- **说明**: 将本人草稿汇报提交，提交后进入统计与上级可见范围。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | — | 汇报编号 |

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作汇报存在且属于当前用户。
2. 校验汇报处于草稿状态。
3. 将状态更新为已提交。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_240_000 | 工作汇报不存在 |
| 1_054_240_001 | 无权访问该工作汇报 |
| 1_054_240_002 | 当前工作汇报状态不允许该操作 |

### 1.5 取消提交工作汇报

- **路径**: PUT /oa/work-report/cancel
- **权限**: oa:work-report:update
- **说明**: 将本人已提交的汇报撤回为草稿。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | — | 汇报编号 |

**响应**: CommonResult\<Boolean\> — 是否成功。

**业务逻辑**:
1. 校验工作汇报存在且属于当前用户。
2. 校验汇报处于已提交状态（与提交相反，此处要求 SUBMITTED）。
3. 将状态回退为草稿。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_240_000 | 工作汇报不存在 |
| 1_054_240_001 | 无权访问该工作汇报 |
| 1_054_240_002 | 当前工作汇报状态不允许该操作 |

### 1.6 获得工作汇报详情

- **路径**: GET /oa/work-report/get
- **权限**: oa:work-report:query 或 oa:work-report:statistics（hasAnyPermissions）
- **说明**: 查询单条汇报详情；本人可直接查看，非本人仅限管理范围内已提交的汇报。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | — | 汇报编号 |

**响应**: CommonResult\<OaWorkReportRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 汇报编号 |
| no | String | 汇报单号 |
| type | Integer | 汇报类型（1 日报、2 周报、3 月报） |
| status | Integer | 汇报状态（1 草稿、2 已提交） |
| title | String | 汇报标题 |
| periodKey | String | 汇报周期标识（按类型格式化 startTime：日期 / 自然年周次 / 月份） |
| startTime | LocalDateTime | 周期开始时间 |
| endTime | LocalDateTime | 周期结束时间 |
| summary | String | 工作总结 |
| plan | String | 工作计划补充说明 |
| problem | String | 问题与协调事项 |
| workItems | List\<OaWorkReportDO.WorkItem\> | 已完成工作项（content 工作内容、progress 完成进度） |
| planItems | List\<OaWorkReportDO.PlanItem\> | 工作计划项（content 计划内容） |
| fileUrls | List\<String\> | 附件地址列表 |
| remark | String | 备注 |
| userId | Long | 汇报人用户编号 |
| userName | String | 汇报人昵称 |
| deptId | Long | 汇报人部门编号 |
| deptName | String | 汇报人部门名称 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 校验工作汇报存在，不存在则抛出“工作汇报不存在”。
2. 若汇报创建人是当前用户，直接返回。
3. 非本人时进行管理范围校验：需同时满足当前用户具备 `oa:work-report:statistics` 权限、汇报处于已提交状态、汇报创建人在当前用户的管理范围（下属用户列表）内，否则抛出“无权访问该工作汇报”（员工草稿不公开）。
4. 拼接响应 VO：按创建人批量查询用户昵称、按部门编号批量查询部门名称，并计算周期标识 periodKey。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_240_000 | 工作汇报不存在 |
| 1_054_240_001 | 无权访问该工作汇报 |

### 1.7 获得我的工作汇报分页

- **路径**: GET /oa/work-report/page
- **权限**: oa:work-report:query
- **说明**: 分页查询当前用户本人的汇报列表，支持类型、状态、单号、部门、时间范围等条件。

**请求参数 (OaWorkReportPageReqVO)**: 继承 PageParam（pageNo 页码、pageSize 每页条数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| type | Integer | 否 | @InEnum(OaWorkReportTypeEnum) | 汇报类型 |
| status | Integer | 否 | @InEnum(OaWorkReportStatusEnum) | 汇报状态 |
| no | String | 否 | — | 汇报单号（模糊匹配） |
| deptId | Long | 否 | — | 部门编号 |
| periodTime | LocalDateTime[] | 否 | — | 汇报开始时间范围（startTime 区间） |
| startTime | LocalDateTime | 否 | — | 开始日期（按整天过滤 startTime） |
| endTime | LocalDateTime | 否 | — | 结束日期（按整天过滤 endTime） |
| createTime | LocalDateTime[] | 否 | — | 创建时间范围 |

**响应**: CommonResult\<PageResult\<OaWorkReportRespVO\>\> — 列表项字段同 1.6。

**业务逻辑**:
1. 按 `creator = 当前用户` 固定过滤，仅查询本人汇报。
2. 叠加单号模糊、部门、汇报开始时间范围（periodTime / startTime 按天 / endTime 按天）、类型、状态、创建时间范围等可选条件。
3. 按 startTime 倒序、id 倒序分页返回。
4. 拼接响应 VO：批量补全汇报人昵称、部门名称及周期标识 periodKey。

### 1.8 获得工作汇报统计

- **路径**: GET /oa/work-report/statistics
- **权限**: oa:work-report:statistics
- **说明**: 统计当前用户管理范围内员工的日报/周报/月报应填、已填、未填情况及汇报明细。

**请求参数 (OaWorkReportStatisticsReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| type | Integer | 是 | @NotNull、@InEnum(OaWorkReportTypeEnum) | 汇报类型 |
| startTime | LocalDateTime | 是 | @NotNull | 统计开始时间 |
| endTime | LocalDateTime | 是 | @NotNull | 统计结束时间 |
| queryStartTime | LocalDateTime | 是 | @NotNull | 完整周期查询开始时间（避免从周中/月中开始漏掉汇报） |
| queryEndTime | LocalDateTime | 是 | @NotNull | 完整周期查询结束时间 |
| deptId | Long | 否 | — | 部门编号（含子部门），不传则不限部门 |

类级校验（@AssertTrue）：统计结束时间不能早于开始时间。

**响应**: CommonResult\<OaWorkReportStatisticsRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| userCount | Integer | 统计人数 |
| expectedCount | Integer | 应填数量（合计） |
| submittedCount | Integer | 已填数量（合计） |
| missingCount | Integer | 未填数量（合计） |
| users | List\<UserStatistics\> | 员工统计列表 |
| users[].userId | Long | 员工用户编号 |
| users[].userName | String | 员工昵称 |
| users[].deptId | Long | 部门编号 |
| users[].deptName | String | 部门名称 |
| users[].expectedCount | Integer | 员工应填数量 |
| users[].submittedCount | Integer | 员工已填数量 |
| users[].missingCount | Integer | 员工未填数量 |
| users[].submittedReports | List\<Report\> | 已提交汇报明细 |
| users[].submittedReports[].id | Long | 汇报编号 |
| users[].submittedReports[].no | String | 汇报单号 |
| users[].submittedReports[].title | String | 汇报标题 |
| users[].submittedReports[].status | Integer | 汇报状态 |
| users[].submittedReports[].startTime | LocalDateTime | 开始时间 |
| users[].submittedReports[].createTime | LocalDateTime | 创建时间 |
| users[].submittedReports[].periodKey | String | 汇报周期 |
| users[].missingPeriodKeys | List\<String\> | 未填周期标识列表 |

**业务逻辑**:
1. 按所选日期范围与汇报类型生成应填周期列表：日报排除周六周日，周报按自然年周次、月报按月份去重；起止时间统一到当日零点后判断顺序。
2. 查询统计员工范围：先取当前用户管理范围（下属）员工，再保留启用状态员工；若指定部门则限定在该部门及其子部门内，最后按用户编号稳定排序。
3. 按完整自然周期（queryStartTime ~ queryEndTime）批量查询范围内员工已提交的对应类型汇报。
4. 逐员工按周期标识去重统计已填数量，计算未填周期；转换已提交汇报明细（同一周期多份汇报均保留展示）。
5. 汇总整体统计：统计人数、应填总数、已填总数及未填总数（不足 0 时取 0）。

**错误码**: 该端点业务逻辑本身不抛出域错误码（统计范围外员工直接被过滤，不返回错误）。

## 域错误码汇总（1_054_240_XXX）

| 错误码 | 说明 |
|-------|------|
| 1_054_240_000 | 工作汇报不存在 |
| 1_054_240_001 | 无权访问该工作汇报 |
| 1_054_240_002 | 当前工作汇报状态不允许该操作 |
| 1_054_240_005 | 工作汇报单号已存在 |
