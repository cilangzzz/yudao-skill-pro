# 工作项管理接口 (PmsWorkItemController)

> PMS 工作项域接口，覆盖工作项的创建/更新/生命周期（归档、回收站、删除）、分页与看板查询、Excel 导入导出，以及工作项状态与看板列配置、标签、评论、动态、工时记录等子资源。

## 接口路径前缀

- /pms/pm/work-item  (Controller: PmsWorkItemController)
- /pms/pm/work-item-status  (Controller: PmsWorkItemStatusController)
- /pms/pm/work-item-label  (Controller: PmsWorkItemLabelController)
- /pms/pm/work-item-comment  (Controller: PmsWorkItemCommentController)
- /pms/pm/work-item-activity  (Controller: PmsWorkItemActivityController)
- /pms/pm/work-item-work-log  (Controller: PmsWorkItemWorkLogController)

通用枚举取值：

- 工作项类型 type：2 需求、3 任务、4 缺陷
- 优先级 priority：0 无、1 低、2 中、3 高
- 语义状态 status：1 未开始、2 进行中、3 已完成
- 生命周期状态 lifecycleStatus：1 正常、2 已归档、3 回收站

## 1. 工作项（PmsWorkItemController）

### 1.1 创建工作项

- **路径**: POST /pms/pm/work-item/create
- **权限**: pms:pm:work-item:create
- **说明**: 在项目中创建工作项，生命周期初始状态与看板顺序由后端控制，可同时创建子工作项并登记初始工时。

**请求参数 (PmsWorkItemSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 工作项编号（创建时忽略） |
| projectId | Long | 是 | @NotNull | 项目编号 |
| type | Integer | 是 | @NotNull、@InEnum(PmsWorkItemTypeEnum) | 工作项类型（2 需求、3 任务、4 缺陷） |
| name | String | 是 | @NotBlank、@Size(max=100) | 工作项标题 |
| description | String | 否 | @Size(max=5000) | 工作项描述 |
| priority | Integer | 是 | @NotNull、@InEnum(PmsWorkItemPriorityEnum) | 优先级（0 无、1 低、2 中、3 高） |
| assigneeUserId | Long | 否 | - | 负责人用户编号 |
| memberUserIds | List&lt;Long&gt; | 否 | - | 参与人用户编号列表，为空时默认为当前登录用户 |
| iterationId | Long | 否 | - | 所属迭代编号，仅敏捷开发项目可用 |
| parentId | Long | 否 | - | 父工作项编号 |
| relatedRequirementId | Long | 否 | - | 关联需求编号 |
| defectType | Integer | 否 | @InEnum(PmsWorkItemDefectTypeEnum) | 缺陷类型，仅缺陷工作项可填 |
| startTime | LocalDateTime | 否 | @AssertTrue 校验早于截止时间 | 开始时间 |
| endTime | LocalDateTime | 否 | - | 截止时间 |
| estimatedHours | Integer | 否 | @Min(0) | 预估工时，单位：小时 |
| progress | Integer | 是 | @NotNull、@Min(0)、@Max(100) | 完成进度 |
| fileUrls | List&lt;String&gt; | 否 | - | 附件地址列表 |
| labelIds | List&lt;Long&gt; | 否 | - | 标签编号列表 |
| childWorkItemNames | List&lt;String&gt; | 否 | 元素 @NotBlank、@Size(max=100) | 创建时同时新增的子工作项标题列表 |
| actualHours | Integer | 否 | @Min(1) | 创建时登记的实际投入工时，单位：小时 |
| remainingHours | Integer | 否 | @Min(0)；@AssertTrue 要求填写时必须同时填写 actualHours | 创建时登记的剩余工时，单位：小时 |

**响应**: CommonResult&lt;Long&gt;（工作项编号）

**业务逻辑**:
1. 校验项目可编辑、项目处于进行中、工作项类型可用（通用项目仅支持任务）。
2. 校验迭代/父工作项/关联需求/缺陷类型等关联关系，以及参与人必须是项目成员、标签编号有效。
3. 取项目默认状态为初始状态，按项目内最大序号 +1 生成 serialNumber，插入工作项（lifecycleStatus=正常）。
4. 保存参与人关系，记录"创建了工作项"动态；childWorkItemNames 非空时递归创建子工作项并沿用父项状态与排序。
5. actualHours 非空时同步创建一条工时记录；向负责人发送指派站内信（负责人为空或等于操作人则跳过，通知失败仅记录日志不阻断业务）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_001 | 当前项目不支持该工作项类型 |
| 1_053_120_005 | 所属迭代与工作项项目不匹配 |
| 1_053_120_006 | 父工作项与当前工作项不匹配 |
| 1_053_120_007 | 关联需求与当前工作项不匹配 |
| 1_053_120_008 | 只有缺陷工作项可以设置缺陷类型 |
| 1_053_120_017 | 工作项标签数据无效 |

### 1.2 更新工作项

- **路径**: PUT /pms/pm/work-item/update
- **权限**: pms:pm:work-item:update
- **说明**: 全量更新工作项业务字段，类型与生命周期状态不允许表单修改，参与人关系全量重建。

**请求参数 (PmsWorkItemSaveReqVO)**: 同 1.1（id 必传，作为待更新工作项编号）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且处于正常生命周期，项目可编辑且处于进行中。
2. 校验关联关系（迭代/父项/关联需求/缺陷类型）、参与人必须是项目成员、标签有效。
3. 更新业务字段（projectId、type 置空不更新），名称去首尾空格。
4. 删除并重建参与人关系，按字段差异记录更新动态（名称、描述、优先级、负责人、参与人、迭代、父项、关联需求、缺陷类型、起止时间、预估工时、进度、标签、附件）。
5. 负责人发生变化时向新负责人发送指派站内信。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_005 | 所属迭代与工作项项目不匹配 |
| 1_053_120_006 | 父工作项与当前工作项不匹配 |
| 1_053_120_007 | 关联需求与当前工作项不匹配 |
| 1_053_120_008 | 只有缺陷工作项可以设置缺陷类型 |
| 1_053_120_017 | 工作项标签数据无效 |

### 1.3 更新工作项名称

- **路径**: PUT /pms/pm/work-item/update-name
- **权限**: pms:pm:work-item:update
- **说明**: 仅更新工作项标题（行内编辑场景）。

**请求参数 (PmsWorkItemNameUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 工作项编号 |
| name | String | 是 | @NotBlank、@Size(max=100) | 工作项标题 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 通过 getWritableWorkItem 校验工作项存在、生命周期正常、项目可编辑且处于进行中。
2. 更新工作项名称（去首尾空格），记录"修改了标题：旧名称 → 新名称"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 1.4 更新工作项状态

- **路径**: PUT /pms/pm/work-item/update-status
- **权限**: pms:pm:work-item:update
- **说明**: 拖拽看板时更新工作项的看板状态。

**请求参数 (PmsWorkItemStatusUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 工作项编号 |
| statusId | Long | 是 | @NotNull | 目标看板状态编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且生命周期正常，项目可编辑且处于进行中。
2. 校验目标状态属于当前项目和工作项类型。
3. 更新工作项的 statusId、语义状态 status，并将 sort 置为该状态列内最大顺序 +1。
4. 记录"修改了状态：旧状态名 → 新状态名"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_120_003 | 工作项状态与项目或类型不匹配 |

### 1.5 更新工作项所属迭代

- **路径**: PUT /pms/pm/work-item/update-iteration
- **权限**: pms:pm:work-item:update
- **说明**: 将工作项移入/移出迭代，iterationId 为空表示移回待规划区（Backlog）。

**请求参数 (PmsWorkItemIterationUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 工作项编号 |
| iterationId | Long | 否 | - | 迭代编号；为空表示移回待规划 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且生命周期正常，项目可编辑且处于进行中。
2. 校验项目为敏捷开发类型（否则报迭代不匹配）；iterationId 非空时校验迭代属于同一项目。
3. 更新工作项 iterationId，迭代发生变化时记录"修改了所属迭代"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_005 | 所属迭代与工作项项目不匹配 |

### 1.6 更新看板列内工作项顺序

- **路径**: PUT /pms/pm/work-item/update-sort
- **权限**: pms:pm:work-item:update
- **说明**: 按前端给定的顺序重排同一看板列内的工作项。

**请求参数 (PmsWorkItemSortReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| statusId | Long | 是 | @NotNull | 看板状态编号 |
| workItemIds | List&lt;Long&gt; | 是 | @NotEmpty，元素 @NotNull | 工作项编号列表，顺序即看板显示顺序 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验目标状态存在、所属项目可编辑且处于进行中。
2. 校验列表内编号无重复，且恰好包含目标状态下的全部工作项（不多不少）。
3. 逐项校验工作项属于目标项目、类型与状态一致。
4. 按请求顺序（编号升序加锁更新）批量写入 sort = 位置序号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_009 | 工作项看板排序数据无效 |

### 1.7 更新待规划或迭代内工作项顺序

- **路径**: PUT /pms/pm/work-item/update-planning-sort
- **权限**: pms:pm:work-item:update
- **说明**: 重排待规划区（Backlog）或迭代内一级工作项的显示顺序。

**请求参数 (PmsWorkItemPlanningSortReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| iterationId | Long | 否 | - | 迭代编号；为空时表示 Backlog |
| workItemIds | List&lt;Long&gt; | 是 | @NotEmpty，元素 @NotNull | 工作项编号列表，顺序即显示顺序 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验项目可编辑且处于进行中；iterationId 非空时校验迭代属于当前项目。
2. 校验列表无重复，且恰好包含目标区域（待规划区/迭代）内的全部一级工作项。
3. iterationId 为空（Backlog）时，按当前用户保存个人排序（工作项用户排序表）。
4. 迭代内排序为项目成员共享，按请求顺序批量写入 sort。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_115_000 | 项目迭代不存在 |
| 1_053_120_009 | 工作项看板排序数据无效 |

### 1.8 归档工作项

- **路径**: PUT /pms/pm/work-item/archive
- **权限**: pms:pm:work-item:update
- **说明**: 将正常状态的工作项标记为已归档。

**请求参数**: 无（Query 参数 id：工作项编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且生命周期正常，项目可编辑且处于进行中。
2. 更新 lifecycleStatus 为已归档并记录归档时间。
3. 记录"归档了工作项"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 1.9 将工作项移入回收站

- **路径**: PUT /pms/pm/work-item/recycle
- **权限**: pms:pm:work-item:update
- **说明**: 软删除工作项到回收站。

**请求参数**: 无（Query 参数 id：工作项编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且不在回收站（已在回收站则报生命周期错误）。
2. 校验项目可编辑且处于进行中。
3. 更新 lifecycleStatus 为回收站并记录回收时间，记录"移入回收站"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 1.10 恢复工作项

- **路径**: PUT /pms/pm/work-item/restore
- **权限**: pms:pm:work-item:update
- **说明**: 将已归档或回收站中的工作项恢复为正常状态。

**请求参数**: 无（Query 参数 id：工作项编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且当前已归档或位于回收站（正常状态则报生命周期错误）。
2. 校验项目可编辑且处于进行中。
3. 更新 lifecycleStatus 为正常并清空归档/回收时间，记录"恢复了工作项"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 1.11 彻底删除回收站中的工作项

- **路径**: DELETE /pms/pm/work-item/delete
- **权限**: pms:pm:work-item:delete
- **说明**: 仅回收站中的工作项可以物理删除，同时清理全部关联数据。

**请求参数**: 无（Query 参数 id：工作项编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工作项存在且位于回收站（否则报删除状态错误）。
2. 校验项目可编辑且处于进行中。
3. 解除子工作项的 parentId、需求类型工作项的 relatedRequirementId 引用。
4. 删除参与人、个人排序、评论、工时、动态等关联记录。
5. 删除工作项主记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_022 | 只有回收站中的工作项才能彻底删除 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 1.12 获得工作项详情

- **路径**: GET /pms/pm/work-item/get
- **权限**: pms:pm:work-item:query
- **说明**: 获得工作项详情，拼接状态、迭代、关联需求、负责人、参与人、标签展示字段。

**请求参数**: 无（Query 参数 id：工作项编号，必填）

**响应**: CommonResult&lt;PmsWorkItemRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 工作项编号 |
| projectId | Long | 项目编号 |
| type | Integer | 工作项类型（2 需求、3 任务、4 缺陷） |
| serialNumber | Integer | 项目内工作项序号 |
| name | String | 工作项标题 |
| description | String | 工作项描述 |
| priority | Integer | 优先级（0 无、1 低、2 中、3 高） |
| assigneeUserId | Long | 负责人用户编号 |
| assigneeUserName | String | 负责人姓名 |
| memberUserIds | List&lt;Long&gt; | 参与人用户编号列表 |
| memberUserNames | List&lt;String&gt; | 参与人姓名列表 |
| statusId | Long | 看板状态编号 |
| statusName | String | 看板状态名称 |
| status | Integer | 语义状态（1 未开始、2 进行中、3 已完成） |
| lifecycleStatus | Integer | 生命周期状态（1 正常、2 已归档、3 回收站） |
| archiveTime | LocalDateTime | 归档时间 |
| recycleTime | LocalDateTime | 移入回收站时间 |
| iterationId | Long | 所属迭代编号 |
| iterationName | String | 所属迭代名称 |
| parentId | Long | 父工作项编号 |
| relatedRequirementId | Long | 关联需求编号 |
| relatedRequirementName | String | 关联需求标题 |
| defectType | Integer | 缺陷类型 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 截止时间 |
| estimatedHours | Integer | 预估工时 |
| progress | Integer | 完成进度 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| labelIds | List&lt;Long&gt; | 标签编号列表 |
| labels | List&lt;PmsWorkItemLabelRespVO&gt; | 标签列表（含 id/name/color） |
| sort | Integer | 看板内显示顺序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验工作项存在。
2. 校验当前用户可读项目（必须是项目成员）。
3. 批量查询状态、迭代、关联需求、参与人、标签和用户信息并拼接进 RespVO。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 1.13 获得工作项分页

- **路径**: GET /pms/pm/work-item/page
- **权限**: pms:pm:work-item:query
- **说明**: 按多条件分页查询工作项；待规划视图按当前用户个人顺序内存分页。

**请求参数 (PmsWorkItemPageReqVO，继承 PageParam: pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| type | Integer | 否 | @InEnum(PmsWorkItemTypeEnum) | 工作项类型 |
| types | List&lt;Integer&gt; | 否 | - | 工作项类型列表 |
| name | String | 否 | - | 工作项标题（模糊） |
| status | Integer | 否 | @InEnum(PmsWorkItemStatusTypeEnum) | 语义状态 |
| statuses | List&lt;Integer&gt; | 否 | - | 语义状态列表 |
| priority | Integer | 否 | @InEnum(PmsWorkItemPriorityEnum) | 优先级 |
| priorities | List&lt;Integer&gt; | 否 | - | 优先级列表 |
| lifecycleStatus | Integer | 否 | @InEnum(PmsWorkItemLifecycleStatusEnum) | 生命周期状态（1 正常、2 已归档、3 回收站） |
| statusId | Long | 否 | - | 看板状态编号 |
| iterationId | Long | 否 | - | 迭代编号 |
| iterationIds | List&lt;Long&gt; | 否 | - | 迭代编号列表 |
| excludedIterationIds | List&lt;Long&gt; | 否 | - | 排除的迭代编号列表 |
| parentId | Long | 否 | - | 父工作项编号 |
| labelIds | List&lt;Long&gt; | 否 | - | 标签编号列表 |
| unplannedOnly | Boolean | 否 | - | 是否只查询未规划工作项 |
| planningOnly | Boolean | 否 | - | 是否用于待规划视图；true 时只查一级工作项并按规划顺序返回 |
| rootOnly | Boolean | 否 | - | 是否只查询一级工作项 |
| assigneeUserId | Long | 否 | - | 负责人用户编号 |
| assigneeUserIds | List&lt;Long&gt; | 否 | - | 负责人用户编号列表 |

**响应**: CommonResult&lt;PageResult&lt;PmsWorkItemRespVO&gt;&gt;，元素字段同 1.12。

**业务逻辑**:
1. 校验当前用户可读项目；type/types 指定时校验类型可用。
2. planningOnly 与 unplannedOnly 同时为 true 时，查出全部待规划工作项后按当前用户个人排序内存排序再分页。
3. 其余场景直接走 SQL 分页查询，并批量拼接展示字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |
| 1_053_120_001 | 当前项目不支持该工作项类型 |

### 1.14 导出工作项

- **路径**: GET /pms/pm/work-item/export-excel
- **权限**: pms:pm:work-item:export
- **说明**: 按分页查询条件导出全部工作项 Excel。

**请求参数 (PmsWorkItemPageReqVO)**: 同 1.13（pageSize 强制置为不分页）。

**响应**: Excel 文件流（工作项.xlsx，列：编号、类型、标题、描述、优先级、负责人、状态、所属迭代、开始时间、截止时间、预估工时、完成进度）

**业务逻辑**:
1. 将 pageSize 置为不分页，校验项目可读后查询全部符合条件的工作项。
2. 拼接展示字段后通过 ExcelUtils 写出响应。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |

### 1.15 下载工作项导入模板

- **路径**: GET /pms/pm/work-item/get-import-template
- **权限**: pms:pm:work-item:import
- **说明**: 下载 Excel 导入模板，内含一条示例数据。

**请求参数**: 无

**响应**: Excel 文件流（工作项导入模板.xlsx）

**业务逻辑**:
1. 构造一条示例数据（标题"登录页面开发"、优先级"中"、开始时间为当前时间、截止时间为 3 天后、预估工时 16）。
2. 通过 ExcelUtils 写出模板文件。

### 1.16 导入工作项

- **路径**: POST /pms/pm/work-item/import
- **权限**: pms:pm:work-item:import
- **说明**: 按模板 Excel 批量导入工作项，逐行校验，失败行记录原因，成功行单独入库。

**请求参数**（multipart/form-data）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | - | 项目编号 |
| type | Integer | 是 | - | 工作项类型（需求、任务、缺陷） |
| file | MultipartFile | 是 | - | Excel 文件，列定义见 PmsWorkItemImportExcelVO |

Excel 列（PmsWorkItemImportExcelVO）：事项标题 name、描述 description、处理人用户编号 assigneeUserId、状态 statusName（按名称匹配项目内状态，空则用默认状态）、优先级 priority（字典标签）、开始时间 startTime、截止时间 endTime、标签 labels（名称列表，逗号/顿号/斜杠分隔）、进度 progress（0-100）、预估工时 estimatedHours、实际投入时长 actualHours（@Min(1)）、剩余工时 remainingHours（@Min(0)，填写时必须同时填写实际投入时长）、缺陷类型 defectType（字典标签，仅缺陷工作项可用）。

**响应**: CommonResult&lt;PmsWorkItemImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| successCount | Integer | 导入成功数量 |
| failureReasons | Map&lt;Integer, String&gt; | 导入失败行号（Excel 行号，数据从第 2 行开始）及原因 |

**业务逻辑**:
1. 校验项目可编辑且处于进行中、工作项类型可用。
2. 查询项目内该类型的状态名称映射和全局标签名称映射。
3. 逐行解析：补齐默认值（优先级"无"、进度 0、预估工时 0），解析状态名/标签名为编号，JSR-303 校验导入行与构造的保存 VO。
4. 调用创建逻辑入库，指定状态时更新状态，有实际工时时同步登记工时记录。
5. 单行失败不回滚整体，记录行号与原因并继续；返回成功数量和失败原因。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_001 | 当前项目不支持该工作项类型 |
| 1_053_120_017 | 工作项标签数据无效 |

### 1.17 获得工作项看板

- **路径**: GET /pms/pm/work-item/board
- **权限**: pms:pm:work-item:query
- **说明**: 按看板列组织工作项，用于看板视图渲染；未分配看板列的状态不展示。

**请求参数 (PmsWorkItemBoardReqVO，继承 PmsWorkItemPageReqVO)**: 同 1.13，其中 type 必填（@NotNull）。

**响应**: CommonResult&lt;List&lt;PmsWorkItemBoardRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 看板列编号 |
| name | String | 看板列名称 |
| statuses | List&lt;PmsWorkItemStatusRespVO&gt; | 映射到当前列的状态列表 |
| items | List&lt;PmsWorkItemRespVO&gt; | 工作项列表，元素字段同 1.12 |

**业务逻辑**:
1. 校验当前用户可读项目。
2. 查询项目该类型的全部状态和看板列，查询符合条件的一级工作项并按 statusId 分组。
3. 按看板列顺序组装列数据：列内聚合 boardName 匹配的状态及其工作项，空看板状态（boardName 为空）不参与展示。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |

## 2. 工作项状态（PmsWorkItemStatusController）

### 2.1 创建工作项状态

- **路径**: POST /pms/pm/work-item-status/create
- **权限**: pms:pm:work-item:update
- **说明**: 为项目某工作项类型追加自定义状态，初始不归属任何看板列。

**请求参数 (PmsWorkItemStatusCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| workItemType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemTypeEnum) | 工作项类型 |
| name | String | 是 | @NotBlank、@Size(max=50) | 状态名称 |
| statusType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemStatusTypeEnum) | 语义状态（1 未开始、2 进行中、3 已完成） |
| description | String | 否 | @Size(max=255) | 状态描述 |

**响应**: CommonResult&lt;Long&gt;（状态编号）

**业务逻辑**:
1. 校验项目可编辑且处于进行中、工作项类型可用。
2. 校验该项目类型下已有状态列表非空、状态名称在同项目同类型内唯一。
3. 追加自定义状态：boardName 置空、defaultStatus=false、sort = 末位 +1。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_001 | 当前项目不支持该工作项类型 |
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_120_010 | 工作项状态名称已存在 |

### 2.2 更新工作项状态

- **路径**: PUT /pms/pm/work-item-status/update
- **权限**: pms:pm:work-item:update
- **说明**: 更新状态名称、语义状态和描述，并同步该状态下全部工作项的语义状态。

**请求参数 (PmsWorkItemStatusConfigUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 状态编号 |
| name | String | 是 | @NotBlank、@Size(max=50) | 状态名称 |
| statusType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemStatusTypeEnum) | 语义状态 |
| description | String | 否 | @Size(max=255) | 状态描述 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验状态存在、所属项目可编辑且处于进行中。
2. 校验状态名称在同项目同类型内唯一。
3. 更新状态（保留原 boardName），并按新语义状态批量刷新该状态下所有工作项的 status 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_010 | 工作项状态名称已存在 |

### 2.3 更新工作项初始状态

- **路径**: PUT /pms/pm/work-item-status/update-default
- **权限**: pms:pm:work-item:update
- **说明**: 将指定状态设为该项目工作项类型的初始状态（新建工作项落到的默认状态）。

**请求参数**: 无（Query 参数 id：状态编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验状态存在、所属项目可编辑且处于进行中。
2. 切换当前项目和工作项类型下的初始状态：原默认状态取消，目标状态置为默认。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 2.4 更新工作项状态顺序

- **路径**: PUT /pms/pm/work-item-status/update-sort
- **权限**: pms:pm:work-item:update
- **说明**: 重排某项目某工作项类型下的状态显示顺序。

**请求参数 (PmsWorkItemStatusSortReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| statusIds | List&lt;Long&gt; | 是 | @NotEmpty，元素 @NotNull | 状态编号列表，顺序即显示顺序 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验列表内状态全部存在且无缺失（列表必须包含该项目该类型的全部状态）。
2. 校验首个状态所属项目可编辑且处于进行中。
3. 按状态编号稳定加锁，批量写入 sort = 请求位置序号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_013 | 工作项状态排序数据无效 |

### 2.5 更新工作项看板列和状态映射

- **路径**: PUT /pms/pm/work-item-status/update-board-config
- **权限**: pms:pm:work-item:update
- **说明**: 全量保存看板列及其与状态的映射关系。

**请求参数 (PmsWorkItemBoardConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| workItemType | Integer | 是 | @NotNull、@InEnum(PmsWorkItemTypeEnum) | 工作项类型 |
| boards | List&lt;Board&gt; | 是 | @Valid、@NotNull | 看板列列表 |
| boards[].id | Long | 否 | - | 看板列编号（已有列传入，新增列不传） |
| boards[].name | String | 是 | @NotBlank、@Size(max=50) | 看板列名称 |
| boards[].statusIds | List&lt;Long&gt; | 是 | @NotNull | 关联状态编号列表，可为空列表 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验项目可编辑、处于进行中、工作项类型可用。
2. 校验看板列名称、状态编号各自不重复，且状态全部属于当前项目和工作项类型。
3. 校验请求中的已有列编号属于当前项目该类型，diff 对比新旧看板列后仅增删改实际变化的列。
4. 先清除当前类型全部状态的 boardName，再按请求批量写入新映射。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_001 | 当前项目不支持该工作项类型 |
| 1_053_120_013 | 工作项状态排序数据无效 |

### 2.6 删除工作项状态并迁移工作项

- **路径**: DELETE /pms/pm/work-item-status/delete
- **权限**: pms:pm:work-item:update
- **说明**: 删除状态；该状态下仍有工作项时必须指定迁移目标状态。

**请求参数 (PmsWorkItemStatusDeleteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 待删除状态编号 |
| transferStatusId | Long | 条件必填 | - | 工作项迁入状态编号；待删除状态存在工作项时必填 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验待删除状态存在、所属项目可编辑且处于进行中；初始状态（defaultStatus）不允许删除。
2. 该状态下存在工作项或传入了迁移状态时，校验迁移目标与源状态同项目同类型且不等于源状态，将工作项批量迁移到目标状态并同步语义状态。
3. 删除状态记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_011 | 工作项初始状态不能删除 |
| 1_053_120_012 | 工作项状态迁移目标无效 |
| 1_053_120_003 | 工作项状态与项目或类型不匹配 |

### 2.7 获得工作项状态详情

- **路径**: GET /pms/pm/work-item-status/get
- **权限**: pms:pm:work-item:query
- **说明**: 获得单个工作项状态详情。

**请求参数**: 无（Query 参数 id：状态编号，必填）

**响应**: CommonResult&lt;PmsWorkItemStatusRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 状态编号 |
| projectId | Long | 项目编号 |
| workItemType | Integer | 工作项类型 |
| name | String | 状态名称 |
| statusType | Integer | 语义状态（1 未开始、2 进行中、3 已完成） |
| description | String | 状态描述 |
| boardName | String | 所属看板列名称 |
| defaultStatus | Boolean | 是否初始状态 |
| sort | Integer | 显示顺序 |

**业务逻辑**:
1. 校验状态存在。
2. 校验当前用户可读状态所属项目。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_002 | 工作项状态不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 2.8 获得工作项看板状态列表

- **路径**: GET /pms/pm/work-item-status/list
- **权限**: pms:pm:work-item:query
- **说明**: 获得项目某工作项类型下的全部看板状态。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | - | 项目编号 |
| type | Integer | 是 | - | 工作项类型 |

**响应**: CommonResult&lt;List&lt;PmsWorkItemStatusRespVO&gt;&gt;，元素字段同 2.7。

**业务逻辑**:
1. 校验当前用户可读项目。
2. 查询该项目该类型已保存的状态列表（读取接口不做数据初始化）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |

### 2.9 获得工作项看板列和状态映射

- **路径**: GET /pms/pm/work-item-status/get-board-config
- **权限**: pms:pm:work-item:query
- **说明**: 获得看板列配置视图：每列关联的状态编号，以及未放入看板的状态。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | - | 项目编号 |
| type | Integer | 是 | - | 工作项类型 |

**响应**: CommonResult&lt;PmsWorkItemBoardConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| boards | List&lt;Board&gt; | 看板列列表 |
| boards[].id | Long | 看板列编号 |
| boards[].name | String | 看板列名称 |
| boards[].statusIds | List&lt;Long&gt; | 关联状态编号列表 |
| unassignedStatusIds | List&lt;Long&gt; | 未放入看板的状态编号列表 |

**业务逻辑**:
1. 校验项目可读，查询该项目该类型的状态列表和看板列列表。
2. 按状态的 boardName 聚合状态编号，按看板列顺序组装响应并保留空列。
3. 未分配到任何看板列的状态编号收集进 unassignedStatusIds。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |

## 3. 工作项标签（PmsWorkItemLabelController）

### 3.1 创建工作项标签

- **路径**: POST /pms/pm/work-item-label/create
- **权限**: pms:pm:work-item:update
- **说明**: 创建全局工作项标签（标签为租户级，不绑定项目）。

**请求参数 (PmsWorkItemLabelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 标签编号（创建时忽略） |
| name | String | 是 | @NotBlank、@Size(max=50) | 标签名称 |
| color | String | 是 | @NotBlank、@Size(max=20) | 标签颜色，如 #409EFF |

**响应**: CommonResult&lt;Long&gt;（标签编号）

**业务逻辑**:
1. 名称和颜色去首尾空格后插入标签记录。

### 3.2 修改工作项标签

- **路径**: PUT /pms/pm/work-item-label/update
- **权限**: pms:pm:work-item:update
- **说明**: 更新标签名称和颜色。

**请求参数 (PmsWorkItemLabelSaveReqVO)**: 同 3.1（id 必传）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验标签存在。
2. 名称和颜色去首尾空格后更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_016 | 工作项标签不存在 |

### 3.3 删除工作项标签

- **路径**: DELETE /pms/pm/work-item-label/delete
- **权限**: pms:pm:work-item:update
- **说明**: 删除标签；工作项中残留的标签编号在展示时自动忽略。

**请求参数**: 无（Query 参数 id：标签编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验标签存在。
2. 删除标签记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_016 | 工作项标签不存在 |

### 3.4 获得工作项标签列表

- **路径**: GET /pms/pm/work-item-label/list
- **权限**: pms:pm:work-item:query
- **说明**: 按名称（可选，模糊）查询标签列表。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 标签名称，模糊匹配 |

**响应**: CommonResult&lt;List&lt;PmsWorkItemLabelRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 标签编号 |
| name | String | 标签名称 |
| color | String | 标签颜色 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按名称条件查询标签列表并转换为 RespVO。

## 4. 工作项评论（PmsWorkItemCommentController）

### 4.1 创建工作项评论

- **路径**: POST /pms/pm/work-item-comment/create
- **权限**: pms:pm:work-item:update
- **说明**: 对工作项发表评论或回复主评论。

**请求参数 (PmsWorkItemCommentSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 评论编号（创建时忽略） |
| workItemId | Long | 是 | @NotNull | 工作项编号 |
| mainId | Long | 否 | - | 主评论编号，回复时传入 |
| replyUserId | Long | 否 | - | 回复对象用户编号 |
| content | String | 是 | @NotBlank、@Size(max=2000) | 评论内容 |

**响应**: CommonResult&lt;Long&gt;（评论编号）

**业务逻辑**:
1. 校验工作项存在、生命周期正常、项目可编辑且处于进行中。
2. mainId 非空（回复）时校验主评论存在、属于同一工作项且本身是主评论，否则报回复无效。
3. 创建评论（记录评论人 userId 和 mainId，根评论 mainId=0），记录"发表了评论"/"回复了评论"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |
| 1_053_120_018 | 工作项评论不存在 |
| 1_053_120_019 | 回复的评论与工作项不匹配 |

### 4.2 修改工作项评论

- **路径**: PUT /pms/pm/work-item-comment/update
- **权限**: pms:pm:work-item:update
- **说明**: 修改自己发表的评论内容。

**请求参数 (PmsWorkItemCommentSaveReqVO)**: 同 4.1（id 必传，作为待更新评论编号）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验评论存在。
2. 校验评论所属工作项可编辑。
3. 校验当前用户是评论创建人，否则报无权操作。
4. 更新评论内容，记录"修改了评论"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_018 | 工作项评论不存在 |
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_120_020 | 只能修改或删除自己的评论 |

### 4.3 删除工作项评论

- **路径**: DELETE /pms/pm/work-item-comment/delete
- **权限**: pms:pm:work-item:update
- **说明**: 删除自己的评论；删除主评论时同步删除全部回复。

**请求参数**: 无（Query 参数 id：评论编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验评论存在。
2. 校验评论所属工作项可编辑，且当前用户是评论创建人。
3. 主评论（mainId=0）删除时先按 mainId 删除其全部回复，再删除主评论本身，记录"删除了评论"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_018 | 工作项评论不存在 |
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_120_020 | 只能修改或删除自己的评论 |

### 4.4 获得工作项评论列表

- **路径**: GET /pms/pm/work-item-comment/list
- **权限**: pms:pm:work-item:query
- **说明**: 获得工作项评论列表，主评论携带 children 回复树。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| workItemId | Long | 是 | - | 工作项编号 |

**响应**: CommonResult&lt;List&lt;PmsWorkItemCommentRespVO&gt;&gt;（仅返回主评论，回复嵌套在 children 中）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 评论编号 |
| workItemId | Long | 工作项编号 |
| userId | Long | 评论人用户编号 |
| userName | String | 评论人姓名 |
| mainId | Long | 主评论编号 |
| replyUserId | Long | 回复对象用户编号 |
| replyUserName | String | 回复对象姓名 |
| content | String | 评论内容 |
| children | List&lt;PmsWorkItemCommentRespVO&gt; | 回复列表 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验工作项可访问（项目可读）。
2. 查询工作项全部评论和回复，批量查询评论人与回复对象用户信息。
3. 按主评论（mainId=0）组织回复树并拼接评论人/回复对象姓名。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_100_001 | 无权访问该项目 |

## 5. 工作项动态（PmsWorkItemActivityController）

### 5.1 获得工作项动态列表

- **路径**: GET /pms/pm/work-item-activity/list
- **权限**: pms:pm:work-item:query
- **说明**: 获得工作项操作动态（创建、更新、状态变更、评论、工时等），按时间倒序展示。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| workItemId | Long | 是 | - | 工作项编号 |

**响应**: CommonResult&lt;List&lt;PmsWorkItemActivityRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 动态编号 |
| workItemId | Long | 工作项编号 |
| operatorUserId | Long | 操作人用户编号 |
| operatorUserName | String | 操作人姓名 |
| operatorUserAvatar | String | 操作人头像 |
| content | String | 动态内容 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验工作项存在且当前用户可读项目。
2. 查询工作项全部动态记录。
3. 批量查询操作人用户信息，拼接操作人姓名和头像。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_100_001 | 无权访问该项目 |

## 6. 工作项工时（PmsWorkItemWorkLogController）

### 6.1 创建工作项工时记录

- **路径**: POST /pms/pm/work-item-work-log/create
- **权限**: pms:pm:work-item:update
- **说明**: 登记工作项的实际投入工时。

**请求参数 (PmsWorkItemWorkLogSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 工时记录编号（创建时忽略） |
| workItemId | Long | 是 | @NotNull | 工作项编号 |
| actualHours | Integer | 是 | @NotNull、@Min(1) | 实际投入工时，单位：小时 |
| remainingHours | Integer | 否 | @Min(0) | 本次登记后的剩余工时，单位：小时 |
| description | String | 否 | @Size(max=500) | 工时说明 |

**响应**: CommonResult&lt;Long&gt;（工时记录编号）

**业务逻辑**:
1. 校验工作项存在、生命周期正常、项目可编辑且处于进行中。
2. 创建工时记录（冗余 projectId，说明去首尾空格）。
3. 记录"登记了工时"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 6.2 更新工作项工时记录

- **路径**: PUT /pms/pm/work-item-work-log/update
- **权限**: pms:pm:work-item:update
- **说明**: 更新工时记录的投入工时、剩余工时和说明。

**请求参数 (PmsWorkItemWorkLogSaveReqVO)**: 同 6.1（id 必传，作为待更新工时记录编号）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验工时记录存在。
2. 校验请求的 workItemId 与记录原有 workItemId 一致，否则报工时与工作项不匹配。
3. 校验工作项可编辑。
4. 更新投入工时、剩余工时和说明，记录"修改了工时"动态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_014 | 工作项工时记录不存在 |
| 1_053_120_015 | 工时记录与工作项不匹配 |
| 1_053_120_000 | 工作项不存在 |
| 1_053_120_021 | 工作项当前生命周期状态不支持该操作 |
| 1_053_100_004 | 当前项目状态不允许执行该操作 |

### 6.3 获得工作项工时记录

- **路径**: GET /pms/pm/work-item-work-log/get
- **权限**: pms:pm:work-item:query
- **说明**: 获得单条工时记录详情，拼接登记人与工作项名称。

**请求参数**: 无（Query 参数 id：工时记录编号，必填）

**响应**: CommonResult&lt;PmsWorkItemWorkLogRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 工时记录编号 |
| workItemId | Long | 工作项编号 |
| workItemName | String | 工作项标题 |
| actualHours | Integer | 实际投入工时，单位：小时 |
| remainingHours | Integer | 本次登记后的剩余工时，单位：小时 |
| description | String | 工时说明 |
| creatorUserId | Long | 登记人用户编号 |
| creatorUserName | String | 登记人姓名 |
| createTime | LocalDateTime | 登记时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 校验工时记录存在。
2. 校验所属工作项可查看（项目可读）。
3. 解析 creator 为登记人用户编号，批量拼接登记人姓名与工作项标题。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_014 | 工作项工时记录不存在 |
| 1_053_120_000 | 工作项不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 6.4 获得工作项工时汇总

- **路径**: GET /pms/pm/work-item-work-log/summary
- **权限**: pms:pm:work-item:query
- **说明**: 汇总工作项的预估、已登记、剩余工时及全部登记记录。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| workItemId | Long | 是 | - | 工作项编号 |

**响应**: CommonResult&lt;PmsWorkItemWorkLogSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| estimatedHours | Integer | 预估工时，单位：小时 |
| actualHours | Integer | 已登记工时（全部记录求和），单位：小时 |
| remainingHours | Integer | 剩余工时，取最新一条登记记录；无记录时为 null，可由预估工时减已登记工时兜底 |
| records | List&lt;PmsWorkItemWorkLogRespVO&gt; | 工时记录列表，元素字段同 6.3 |

**业务逻辑**:
1. 校验工作项可查看。
2. 查询工作项全部工时记录，累加得到已登记工时。
3. 剩余工时取最新一条登记记录的 remainingHours；无登记记录时回退为预估工时，仍无则按 预估-已登记 计算（不小于 0）。
4. 转换记录列表并拼接登记人与工作项名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_120_000 | 工作项不存在 |
| 1_053_100_001 | 无权访问该项目 |

### 6.5 获得项目工时报表

- **路径**: GET /pms/pm/work-item-work-log/project-report
- **权限**: pms:pm:work-item:query
- **说明**: 按迭代分组的项目工时报表，含每个工作项的每日工时分布和连续日期轴。

**请求参数 (PmsProjectWorkLogReportReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| projectId | Long | 是 | @NotNull | 项目编号 |
| createTime | LocalDateTime[] | 是 | @NotNull、@Size(min=2, max=2)、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 工时登记时间范围 [开始, 结束] |
| iterationName | String | 否 | - | 迭代名称，模糊过滤（含"未规划事项"） |

**响应**: CommonResult&lt;PmsProjectWorkLogReportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| dates | List&lt;String&gt; | 报表日期列表（起止日期间连续每天一个，yyyy-MM-dd） |
| totalHours | Integer | 总工时 |
| groups | List&lt;Group&gt; | 迭代分组 |
| groups[].iterationId | Long | 迭代编号，未规划事项为空 |
| groups[].iterationName | String | 迭代名称（未规划事项显示"未规划事项"） |
| groups[].totalHours | Integer | 分组总工时 |
| groups[].items | List&lt;Item&gt; | 工作项列表，按序号排序 |
| groups[].items[].workItemId | Long | 工作项编号 |
| groups[].items[].serialNumber | Integer | 项目内工作项序号 |
| groups[].items[].name | String | 工作项标题 |
| groups[].items[].type | Integer | 工作项类型 |
| groups[].items[].totalHours | Integer | 工作项总工时 |
| groups[].items[].dailyHours | Map&lt;String, Integer&gt; | 每日工时，键为日期，值为小时数 |

**业务逻辑**:
1. 校验项目可读，校验时间范围（结束时间早于开始时间则报工时数据无效）。
2. 查询时间范围内的项目工时及关联工作项，迭代名称非空时按迭代名称（不区分大小写包含）过滤工作项和工时。
3. 按迭代（未规划归入一组）和工作项分组，逐项按登记日期汇总每日工时和总工时，工作项按序号排序。
4. 分组按迭代名称排序，未规划事项排最后。
5. 生成起止日期间的连续日期轴，累计总工时返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_053_100_001 | 无权访问该项目 |
| 1_053_120_015 | 工时记录与工作项不匹配 |
