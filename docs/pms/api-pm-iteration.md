# 项目迭代接口 (PmsIterationController)

> PMS 项目迭代管理：迭代的创建/更新/开始/完成/删除，以及迭代详情、分页与概览统计（状态/类型/趋势/燃尽/动态）。

## 接口路径前缀

/pms/pm/iteration  (Controller: PmsIterationController)

迭代状态取值（`PmsIterationStatusEnum`）：`1` 未开始（PLANNED）、`2` 进行中（ACTIVE）、`3` 已完成（COMPLETED）。

## 1. 迭代写操作

### 1.1 创建项目迭代

- **路径**: POST /pms/pm/iteration/create
- **权限**: pms:pm:iteration:create
- **说明**: 在指定项目下创建一个"未开始"状态的迭代，自动追加显示顺序。

**请求参数 (PmsIterationSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 迭代编号（创建时不传） |
| projectId | Long | 是 | @NotNull | 项目编号 |
| name | String | 是 | @NotBlank、@Size(max=100) | 迭代名称 |
| ownerUserId | Long | 否 | - | 负责人用户编号（必须为项目成员） |
| startTime | LocalDateTime | 否 | - | 开始时间 |
| endTime | LocalDateTime | 否 | - | 结束时间 |
| target | String | 否 | @Size(max=255) | 迭代目标 |
| description | String | 否 | - | 迭代描述 |

类级校验：`@AssertTrue isTimeRangeValid` —— 开始、结束时间需同时填写或不填，且结束时间必须晚于开始时间。

**响应**: CommonResult&lt;Long&gt; —— 迭代编号

**业务逻辑**:
1. 校验当前用户对项目有编辑权限（`validateProjectWritable`），且项目处于进行中状态（否则报 `PROJECT_STATUS_INVALID`）。
2. 若指定负责人，校验其是该项目成员（`validateProjectMemberExists`）。
3. 查询该项目下当前最大 `sort` 值，新迭代 `sort = maxSort + 1`（无迭代时为 1）。
4. 转换为 `PmsIterationDO` 插入，状态固定为未开始（PLANNED）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作（项目非进行中） |
| 1_053_100_005 | 当前项目角色无编辑权限 |
| 1_053_105_000 | 项目成员不存在（负责人不是项目成员） |

### 1.2 更新项目迭代

- **路径**: PUT /pms/pm/iteration/update
- **权限**: pms:pm:iteration:update
- **说明**: 更新迭代基本信息，不允许变更所属项目。

**请求参数 (PmsIterationSaveReqVO)**: 同 1.1（`id` 必传，其余字段同表；时间范围类级校验同上）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验迭代存在（否则报 `ITERATION_NOT_EXISTS`）。
2. 校验当前用户对迭代所属项目有编辑权限，且项目处于进行中状态。
3. 若指定负责人，校验其是该项目成员。
4. 更新迭代，并将 `projectId` 置空，避免修改所属项目。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_005 | 当前项目角色无编辑权限 |
| 1_053_105_000 | 项目成员不存在（负责人不是项目成员） |

### 1.3 开始项目迭代

- **路径**: PUT /pms/pm/iteration/start
- **权限**: pms:pm:iteration:update
- **说明**: 将"未开始"的迭代置为"进行中"，同时确定迭代周期。

**请求参数 (PmsIterationStartReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 迭代编号 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间 |
| endTime | LocalDateTime | 是 | @NotNull | 结束时间 |

类级校验：`@AssertTrue isTimeRangeValid` —— 结束时间必须晚于开始时间。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验迭代存在。
2. 校验当前用户对项目有编辑权限，且项目处于进行中状态。
3. 校验迭代当前状态为未开始（PLANNED），否则抛出 `ITERATION_STATUS_INVALID`。
4. 保存迭代周期并将状态更新为进行中（ACTIVE），`projectId` 置空。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_115_002 | 当前迭代状态不允许执行该操作（非未开始状态） |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_005 | 当前项目角色无编辑权限 |

### 1.4 完成项目迭代

- **路径**: PUT /pms/pm/iteration/complete
- **权限**: pms:pm:iteration:update
- **说明**: 将"进行中"的迭代置为"已完成"，记录完成时间。

**请求参数**: 无（Query 参数 `id`：迭代编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验迭代存在。
2. 校验当前用户对项目有编辑权限，且项目处于进行中状态。
3. 校验迭代当前状态为进行中（ACTIVE），否则抛出 `ITERATION_STATUS_INVALID`。
4. 将状态更新为已完成（COMPLETED），并写入 `finishTime` 为当前时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_115_002 | 当前迭代状态不允许执行该操作（非进行中状态） |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_005 | 当前项目角色无编辑权限 |

### 1.5 删除项目迭代

- **路径**: DELETE /pms/pm/iteration/delete
- **权限**: pms:pm:iteration:delete
- **说明**: 删除迭代，并解除迭代下工作项的所属迭代关系。

**请求参数**: 无（Query 参数 `id`：迭代编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验迭代存在。
2. 校验当前用户对项目有编辑权限，且项目处于进行中状态。
3. 事务内先调用 `clearWorkItemIterationId` 解除该迭代下所有工作项的迭代归属。
4. 再删除迭代记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_100_005 | 当前项目角色无编辑权限 |

## 2. 迭代查询

### 2.1 获得项目迭代详情

- **路径**: GET /pms/pm/iteration/get
- **权限**: pms:pm:iteration:query
- **说明**: 获得迭代详情，拼接负责人姓名。

**请求参数**: 无（Query 参数 `id`：迭代编号，必填）

**响应**: CommonResult&lt;PmsIterationRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 迭代编号 |
| projectId | Long | 项目编号 |
| name | String | 迭代名称 |
| ownerUserId | Long | 负责人用户编号 |
| status | Integer | 迭代状态（1 未开始/2 进行中/3 已完成） |
| ownerUserName | String | 负责人姓名（来自 system 模块用户昵称） |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| target | String | 迭代目标 |
| description | String | 迭代描述 |
| finishTime | LocalDateTime | 完成时间 |
| sort | Integer | 显示顺序 |
| progress | Integer | 完成进度百分比（详情接口不填充，分页接口填充） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验迭代存在。
2. 校验当前用户对迭代所属项目有读取权限（公开项目可查看，私有项目需为项目成员或超管）。
3. 转换为 `PmsIterationRespVO`，批量查询 system 用户并拼接负责人姓名 `ownerUserName`。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 2.2 获得项目迭代分页

- **路径**: GET /pms/pm/iteration/page
- **权限**: pms:pm:iteration:query
- **说明**: 按项目分页查询迭代列表，附带每个迭代的完成进度。

**请求参数 (PmsIterationPageReqVO)**（继承 PageParam：`pageNo` 页码默认 1、`pageSize` 每页条数默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| name | String | 否 | - | 迭代名称（模糊匹配） |
| status | Integer | 否 | @InEnum(PmsIterationStatusEnum) | 迭代状态（1/2/3） |
| pageNo | Integer | 否 | - | 页码，从 1 开始 |
| pageSize | Integer | 否 | - | 每页条数 |

**响应**: CommonResult&lt;PageResult&lt;PmsIterationRespVO&gt;&gt;，字段同 2.1（`progress` 均已填充）

**业务逻辑**:
1. 校验当前用户对项目有读取权限。
2. 按条件查询迭代分页（项目 + 名称 + 状态过滤）。
3. 批量查询负责人并拼接 `ownerUserName`。
4. 批量聚合每个迭代下正常工作项的状态数量，计算完成进度：`已完成数 * 100 / 总数`（无工作项时为 0），填充到 `progress` 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |

### 2.3 获得迭代概览统计

- **路径**: GET /pms/pm/iteration/overview
- **权限**: pms:pm:iteration:query
- **说明**: 获得迭代下工作项的状态/类型统计、状态趋势、燃尽图与最近动态。

**请求参数**: 无（Query 参数 `id`：迭代编号，必填）

**响应**: CommonResult&lt;PmsIterationOverviewRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalCount | Integer | 工作项总数 |
| pendingCount | Integer | 未开始工作项数量 |
| processingCount | Integer | 进行中工作项数量 |
| completedCount | Integer | 已完成工作项数量 |
| progress | Integer | 完成进度百分比（已完成 * 100 / 总数） |
| typeCountMap | Map&lt;Integer, Integer&gt; | 工作项类型 → 数量统计 |
| typeStatusCountMap | Map&lt;Integer, Map&lt;Integer, Integer&gt;&gt; | 工作项类型 → 状态 → 数量统计 |
| statusTrends | List&lt;TrendItem&gt; | 最近 14 天状态趋势 |
| burnDowns | List&lt;BurnDownItem&gt; | 燃尽图数据 |
| recentActivities | List&lt;ActivityItem&gt; | 最近动态列表（最多 50 条） |

TrendItem：`date`（日期）、`pendingCount` / `processingCount` / `completedCount`（当日各状态数量）。
BurnDownItem：`date`（日期）、`idealRemaining`（理想剩余工时，小时）、`actualRemaining`（实际剩余工时，小时）。
ActivityItem：`id`（动态编号）、`workItemId`（工作项编号）、`workItemSerialNumber`（工作项序号）、`workItemName`（工作项名称）、`operatorUserId`（操作人编号）、`operatorUserName`（操作人昵称，Controller 拼接）、`content`（动态内容）、`createTime`（创建时间）。

**业务逻辑**:
1. 校验迭代存在且用户对项目有读取权限。
2. 查询迭代关联的未删除工作项列表。
3. 按状态统计未开始/进行中/已完成数量，按类型和"类型+状态"两个维度统计数量，并计算完成进度百分比。
4. 构建最近 14 天的每日状态趋势：按工作项 `updateTime` 的日期统计当日处于各状态的数量。
5. 构建燃尽图数据：未配置完整迭代周期（开始或结束时间为空）时返回空列表；否则汇总工作项预估总工时与工时登记记录的每日实际投入，逐日计算理想剩余工时（按周期线性递减）与实际剩余工时。
6. 构建最近动态：查询工作项动态（按工作项 ID 集合，限 50 条），拼接工作项序号与名称；Controller 再批量查询 system 用户填充操作人昵称 `operatorUserName`。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_100_001 | 无权访问该项目 |
