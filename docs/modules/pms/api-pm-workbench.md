# 工作台接口 (PmsWorkbenchController)

> 提供 PMS 个人工作台能力：分页展示当前登录用户在活跃项目中「我负责」的未完成工作项与未完成迭代，并汇总需求数、任务数、缺陷数、迭代数四项待办数量。本域为纯查询域，未定义专属错误码；当用户未参与任何活跃项目或指定项目不在其活跃项目范围内时，接口直接返回空结果（不抛错）。

## 接口路径前缀

- /pms/pm/workbench  (Controller: PmsWorkbenchController)

## 1. 工作台查询（PmsWorkbenchController，/pms/pm/workbench）

### 1.1 获得我负责的工作项分页

- **路径**: GET /pms/pm/workbench/work-item-page
- **权限**: pms:pm:work-item:query
- **说明**: 分页返回当前登录用户在活跃项目中负责的未完成工作项，并拼接项目、状态、负责人/创建人姓名及当前用户的编辑权限标记。

**请求参数 (PmsWorkbenchPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承自 PageParam，默认 1） | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承自 PageParam，默认 10） | 每页条数，最大 200；传 -1 可不分页 |
| projectId | Long | 否 | - | 项目编号 |
| type | Integer | 否 | @InEnum(PmsWorkItemTypeEnum) | 工作项类型 |
| name | String | 否 | - | 名称，模糊匹配 |
| status | Integer | 否 | - | 语义状态（工作项为语义状态，迭代为迭代状态） |
| priority | Integer | 否 | @InEnum(PmsWorkItemPriorityEnum) | 优先级 |
| iterationId | Long | 否 | - | 迭代编号 |
| endTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 截止时间范围（区间查询） |

**响应**: CommonResult&lt;PageResult&lt;PmsWorkbenchWorkItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 工作项编号 |
| projectId | Long | 项目编号 |
| projectName | String | 项目名称 |
| projectType | Integer | 项目类型 |
| type | Integer | 工作项类型 |
| serialNumber | Integer | 工作项序号 |
| name | String | 工作项名称 |
| priority | Integer | 优先级 |
| assigneeUserId | Long | 负责人用户编号 |
| assigneeUserName | String | 负责人姓名 |
| creatorUserId | Long | 创建人用户编号（由 creator 字符串解析） |
| creatorUserName | String | 创建人姓名 |
| statusId | Long | 状态编号 |
| statusName | String | 状态名称 |
| status | Integer | 语义状态 |
| progress | Integer | 进度 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| writeStatus | Boolean | 是否可编辑（超级管理员或为项目可写成员时为 true） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 取当前登录用户编号，通过 projectMemberService 获得其参与的活跃项目编号列表；若列表为空，或指定了 projectId 但不在活跃项目范围内，直接返回空分页。
2. 调用 workItemService.getAssignedWorkItemPage，按查询条件分页查询当前用户在这些项目中负责的未完成工作项。
3. 批量查询工作项关联的项目 Map 与状态 Map；同时查询当前用户可写（可编辑）的项目编号集合，并通过 PermissionApi 判断其是否拥有 SUPER_ADMIN 超级管理员角色。
4. 批量查询负责人与创建人（creator 字符串解析为用户编号）的用户信息 Map，并建立工作项编号到创建人编号的映射。
5. 将工作项列表转换为响应 VO：拼接项目名称/类型、状态名称、负责人姓名、创建人编号/姓名，并计算 writeStatus（超级管理员或项目在可写集合中）。
6. 组装 PageResult 返回。

### 1.2 获得我负责的迭代分页

- **路径**: GET /pms/pm/workbench/iteration-page
- **权限**: pms:pm:iteration:query
- **说明**: 分页返回当前登录用户参与的活跃项目中、其负责的未完成迭代，并拼接项目名称与项目类型。

**请求参数 (PmsWorkbenchPageReqVO，继承 PageParam)**: 同 1.1 的请求参数表（projectId/type/name/status/priority/iterationId/endTime 对迭代查询的含义：status 为迭代状态，type/priority/iterationId/endTime 等条件由迭代查询按需使用）。

**响应**: CommonResult&lt;PageResult&lt;PmsWorkbenchIterationRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 迭代编号 |
| projectId | Long | 项目编号 |
| projectName | String | 项目名称 |
| projectType | Integer | 项目类型 |
| name | String | 迭代名称 |
| status | Integer | 迭代状态 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| target | String | 迭代目标 |

**业务逻辑**:
1. 获得当前登录用户参与的活跃项目编号列表；若为空，或指定 projectId 不在范围内，直接返回空分页。
2. 调用 iterationService.getUncompletedIterationPage，按查询条件分页查询这些项目中的未完成迭代。
3. 批量查询迭代关联的项目 Map。
4. 将迭代列表转换为响应 VO，并拼接项目名称与项目类型，组装 PageResult 返回。

### 1.3 获得我的未完成事项数量

- **路径**: GET /pms/pm/workbench/count
- **权限**: pms:pm:work-item:query 或 pms:pm:iteration:query（@PreAuthorize hasAnyPermissions）
- **说明**: 统计当前登录用户在活跃项目中的待办数量：需求数、任务数、缺陷数、未完成迭代数。
- **备注**: 该端点的入参未标注 @Valid，分页参数校验注解在此不生效，仅作为查询条件使用。

**请求参数 (PmsWorkbenchPageReqVO，继承 PageParam)**: 字段同 1.1 的请求参数表。

**响应**: CommonResult&lt;PmsWorkbenchCountRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| requirementCount | Integer | 需求数量（未完成需求工作项数） |
| taskCount | Integer | 任务数量（未完成任务工作项数） |
| defectCount | Integer | 缺陷数量（未完成缺陷工作项数） |
| iterationCount | Integer | 迭代数量（未完成迭代数） |

**业务逻辑**:
1. 获得当前登录用户参与的活跃项目编号列表；若为空，或指定 projectId 不在范围内，直接返回四项计数全为 0 的响应。
2. 调用 workItemService.getAssignedWorkItemTypeCountMap，按工作项类型统计当前用户在这些项目中负责的未完成工作项数量，得到「类型 → 数量」Map。
3. 调用 iterationService.getUncompletedIterationCount 统计未完成迭代数量。
4. 从类型计数 Map 中按 PmsWorkItemTypeEnum 取出 REQUIREMENT（需求）、TASK（任务）、DEFECT（缺陷）三类数量（缺失时取 0），连同迭代数量组装响应 VO 返回。
