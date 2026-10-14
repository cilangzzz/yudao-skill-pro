# 排班日历接口 (MesCalCalendarController、MesCalHolidayController、MesCalPlanController、MesCalPlanShiftController、MesCalPlanTeamController、MesCalTeamController、MesCalTeamMemberController、MesCalTeamShiftController)

> 提供 MES 排班管理全流程：排班计划（草稿/确认）与计划班次、计划班组分配，班组与班组成员维护，确认后自动生成逐日班组排班记录，并对外提供排班日历查询与假期（节假日）设置。

## 接口路径前缀

- `/mes/cal/calendar` (Controller: MesCalCalendarController) — 排班日历查询
- `/mes/cal/holiday` (Controller: MesCalHolidayController) — 假期设置
- `/mes/cal/plan` (Controller: MesCalPlanController) — 排班计划
- `/mes/cal/plan-shift` (Controller: MesCalPlanShiftController) — 计划班次
- `/mes/cal/plan-team` (Controller: MesCalPlanTeamController) — 计划班组关联
- `/mes/cal/team` (Controller: MesCalTeamController) — 班组
- `/mes/cal/team-member` (Controller: MesCalTeamMemberController) — 班组成员
- `/mes/cal/team-shift` (Controller: MesCalTeamShiftController) — 班组排班

**枚举约定**：

- 轮班方式 shiftType（MesCalShiftTypeEnum）：1-单白班（1 个班次/需 1 个班组）、2-两班倒（白班 08:00-20:00 / 夜班 20:00-08:00）、3-三班倒（白班 08:00-16:00 / 中班 16:00-00:00 / 夜班 00:00-08:00）
- 倒班方式 shiftMethod（MesCalShiftMethodEnum）：1-按季度、2-按月、3-按周、4-按天（需填倒班天数）
- 计划状态 status（MesCalPlanStatusEnum）：0-草稿、1-已确认（已确认不允许修改/删除）
- 假期类型 type（MesCalHolidayTypeEnum，字典 mes_cal_holiday_type）：1-工作日、2-节假日
- 日期参数格式均为 `yyyy-MM-dd HH:mm:ss`

---

## 1. 排班日历查询（MesCalCalendarController）

### 1.1 查询排班日历

- **路径**: GET /mes/cal/calendar/list
- **权限**: mes:cal-team-shift:query
- **说明**: 按查询类型（按班组分类/按班组/按个人）获取日期范围内的排班记录，按天聚合并过滤节假日，用于日历展示。

**请求参数 (MesCalCalendarListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| startDay | LocalDateTime | 是 | @NotNull | 开始日期 |
| endDay | LocalDateTime | 是 | @NotNull | 结束日期 |
| queryType | String | 是 | @NotEmpty | 查询类型：TYPE-按分类，TEAM-按班组，USER-按个人 |
| calendarType | Integer | 否 | - | 班组类型（queryType=TYPE 时使用） |
| teamId | Long | 否 | - | 班组编号（queryType=TEAM 时使用） |
| userId | Long | 否 | - | 用户编号（queryType=USER 时使用） |

**响应**: CommonResult&lt;List&lt;MesCalCalendarRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| day | LocalDateTime | 日期（当天 00:00:00） |
| shiftType | Integer | 轮班方式（取该天第一条排班记录关联排班计划的 shiftType） |
| teamShifts | List&lt;TeamShiftItem> | 班组排班列表（按 sort 升序） |
| teamShifts[].teamId | Long | 班组编号 |
| teamShifts[].teamName | String | 班组名称 |
| teamShifts[].shiftId | Long | 班次编号 |
| teamShifts[].shiftName | String | 班次名称 |
| teamShifts[].sort | Integer | 排序 |

**业务逻辑**:
1. 根据 queryType 获取班组排班记录：TYPE 时先查出该班组类型的所有班组，再按班组集合 + 日期范围 IN 查询；TEAM 时按班组编号 + 日期范围查询；USER 时先查用户所属班组（一个用户只属于一个班组），再查该班组在日期范围内的排班记录。
2. 无排班记录时直接返回空列表。
3. 按日期范围查询假期，构建节假日日期集合（仅 type=2 节假日，格式 yyyy-MM-dd）。
4. 批量查询关联数据：班组 Map、计划班次 Map、排班计划 Map。
5. 排班记录按 day 分组，过滤掉节假日所在的日期。
6. 每天记录按 sort 升序排序，取第一条记录关联排班计划的轮班方式作为该天 shiftType。
7. 构建每天的班组排班项（班组名称、班次名称）并返回日历列表。

---

## 2. 假期设置（MesCalHolidayController）

### 2.1 保存假期设置

- **路径**: POST /mes/cal/holiday/save
- **权限**: mes:cal-holiday:create
- **说明**: 保存假期设置，如果该日期已存在记录则更新（Upsert）。

**请求参数 (MesCalHolidaySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（更新时由后端按日期匹配，无需传入） |
| day | LocalDateTime | 是 | @NotNull | 日期 |
| type | Integer | 是 | @NotNull | 日期类型：1-工作日、2-节假日 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 假期设置编号 |

**业务逻辑**:
1. 按日期查询是否已存在假期记录。
2. 已存在则将请求参数转换为 DO 并沿用已有 id 更新，返回已有记录 id。
3. 不存在则插入新记录，返回新记录 id。

### 2.2 根据日期获得假期设置

- **路径**: GET /mes/cal/holiday/get-by-day
- **权限**: mes:cal-holiday:query
- **说明**: 根据日期获得单条假期设置，不存在时 data 为 null。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| day | LocalDateTime | 是 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 日期 |

**响应**: CommonResult&lt;MesCalHolidayRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| day | LocalDateTime | 日期 |
| type | Integer | 日期类型：1-工作日、2-节假日 |
| remark | String | 备注 |

**业务逻辑**: 1. 按日期查询假期记录；2. 转换为 MesCalHolidayRespVO 返回。

### 2.3 获得假期设置列表

- **路径**: GET /mes/cal/holiday/list
- **权限**: mes:cal-holiday:query
- **说明**: 获得假期设置列表，支持可选日期范围过滤，不传则返回全量数据。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| startDay | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 开始日期 |
| endDay | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 结束日期 |

**响应**: CommonResult&lt;List&lt;MesCalHolidayRespVO>>（字段同 2.2）

**业务逻辑**: 1. 按可选日期范围查询假期列表；2. 转换为 RespVO 列表返回。

---

## 3. 排班计划（MesCalPlanController）

### 3.1 创建排班计划

- **路径**: POST /mes/cal/plan/create
- **权限**: mes:cal-plan:create
- **说明**: 创建排班计划，状态默认草稿，并按轮班方式自动生成默认班次。

**请求参数 (MesCalPlanSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 计划编号（创建时忽略） |
| code | String | 是 | @NotEmpty | 计划编码 |
| name | String | 是 | @NotEmpty | 计划名称 |
| calendarType | Integer | 是 | @NotNull | 班组类型 |
| startDate | LocalDateTime | 是 | @NotNull | 开始日期 |
| endDate | LocalDateTime | 是 | @NotNull | 结束日期 |
| shiftType | Integer | 是 | @NotNull | 轮班方式：1-单白班、2-两班倒、3-三班倒 |
| shiftMethod | Integer | 否 | - | 倒班方式：1-按季度、2-按月、3-按周、4-按天 |
| shiftCount | Integer | 否 | - | 倒班天数（shiftMethod=4 按天时必填） |
| status | Integer | 否 | - | 状态（创建时固定为草稿） |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 计划编号 |

**业务逻辑**:
1. 校验计划编码唯一（重复抛 CAL_PLAN_CODE_DUPLICATE）。
2. 插入计划，状态固定为草稿（PREPARE）。
3. 若轮班方式非空，按 MesCalShiftTypeEnum 枚举配置自动生成默认班次（单白班 1 个：白班 08:00-18:00；两班倒 2 个；三班倒 3 个），含名称、时间段与排序。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_000 | 排班计划不存在 |
| 1_040_202_001 | 排班计划编码已存在 |

### 3.2 更新排班计划

- **路径**: PUT /mes/cal/plan/update
- **权限**: mes:cal-plan:update
- **说明**: 更新排班计划（仅草稿状态可更新），状态字段与倒班字段做联动清理。

**请求参数 (MesCalPlanSaveReqVO)**: 同 3.1（id 必传）。

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验计划存在。
2. 校验计划未确认，已确认抛 CAL_PLAN_NOT_PREPARE。
3. 校验计划编码唯一（排除自身）。
4. 置空 status，不允许通过更新修改状态，状态变更走专用确认接口。
5. 倒班字段联动清理：轮班方式为单白班时清空 shiftMethod；单白班、或倒班方式为空/非按天时清空 shiftCount。
6. 通过 updateWithShiftFieldCleanup 更新计划，并在 SQL 层将对应字段清理为 NULL。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_000 | 排班计划不存在 |
| 1_040_202_001 | 排班计划编码已存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |

### 3.3 确认排班计划

- **路径**: PUT /mes/cal/plan/confirm
- **权限**: mes:cal-plan:update
- **说明**: 确认草稿排班计划，并按计划日期范围逐日生成班组排班记录。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 计划编号 |

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验计划存在且状态为草稿（否则抛 CAL_PLAN_NOT_PREPARE）。
2. 校验分配的班组数量是否满足轮班方式所需班组数（单白班 1 个、两班倒 2 个、三班倒 3 个），不足抛 CAL_PLAN_TEAM_COUNT_NOT_MATCH。
3. 更新计划状态为已确认（CONFIRMED）。
4. 查询计划的班次列表与班组列表，校验数量满足班型要求。
5. 按计划开始/结束日期逐日遍历：单白班不倒班；其余按倒班方式（按季度/月/周/天）计算轮转序号 shiftIndex。
6. 按班型（两班倒/三班倒）根据 shiftIndex 轮转分配各班组的班次，生成逐日排班记录并批量插入。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_000 | 排班计划不存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |
| 1_040_202_003 | 确认排班计划时，分配的班组数量与轮班方式不匹配 |
| 1_040_201_201 | 班组数量不满足轮班方式要求 |
| 1_040_201_202 | 班次数量不满足轮班方式要求 |
| 1_040_201_203 | 按天倒班必须填写合法的倒班天数 |
| 1_040_201_204 | 不支持的倒班方式：{} |

### 3.4 删除排班计划

- **路径**: DELETE /mes/cal/plan/delete
- **权限**: mes:cal-plan:delete
- **说明**: 删除草稿状态的排班计划，级联删除其班次与班组关联。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 计划编号 |

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验计划存在且状态为草稿（否则抛 CAL_PLAN_NOT_PREPARE）。
2. 级联删除该计划下全部计划班次。
3. 级联删除该计划下全部计划班组关联。
4. 删除排班计划。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_000 | 排班计划不存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |

### 3.5 获得排班计划

- **路径**: GET /mes/cal/plan/get
- **权限**: mes:cal-plan:query
- **说明**: 根据编号获得排班计划详情。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 计划编号 |

**响应**: CommonResult&lt;MesCalPlanRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 计划编号 |
| code | String | 计划编码 |
| name | String | 计划名称 |
| calendarType | Integer | 班组类型 |
| startDate | LocalDateTime | 开始日期 |
| endDate | LocalDateTime | 结束日期 |
| shiftType | Integer | 轮班方式 |
| shiftMethod | Integer | 倒班方式 |
| shiftCount | Integer | 倒班天数 |
| status | Integer | 状态：0-草稿、1-已确认 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询计划；2. 转换为 RespVO 返回。

### 3.6 获得排班计划分页

- **路径**: GET /mes/cal/plan/page
- **权限**: mes:cal-plan:query
- **说明**: 分页查询排班计划。

**请求参数 (MesCalPlanPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam 默认 1） |
| pageSize | Integer | 否 | - | 每页条数（PageParam 默认 10） |
| code | String | 否 | - | 计划编码 |
| name | String | 否 | - | 计划名称 |
| shiftType | Integer | 否 | - | 轮班方式 |
| status | Integer | 否 | - | 状态 |
| calendarType | Integer | 否 | - | 班组类型 |
| startDate | LocalDateTime[] | 否 | @DateTimeFormat | 开始日期区间 |
| endDate | LocalDateTime[] | 否 | @DateTimeFormat | 结束日期区间 |

**响应**: CommonResult&lt;PageResult&lt;MesCalPlanRespVO>>（list 字段结构同 3.5）

**业务逻辑**: 1. 按条件分页查询计划；2. 转换为 RespVO 分页返回。

### 3.7 导出排班计划 Excel

- **路径**: GET /mes/cal/plan/export-excel
- **权限**: mes:cal-plan:export
- **说明**: 按分页条件导出排班计划 Excel（文件名 排班计划.xls），不分页导出全量。

**请求参数 (MesCalPlanPageReqVO)**: 同 3.6（pageSize 强制设为不分页）。

**响应**: Excel 文件流（列结构同 MesCalPlanRespVO 的 @ExcelProperty 标注）。

**业务逻辑**: 1. 将分页参数置为不分页；2. 查询计划全量列表；3. 通过 ExcelUtils 写出 Excel。

---

## 4. 计划班次（MesCalPlanShiftController）

### 4.1 创建计划班次

- **路径**: POST /mes/cal/plan-shift/create
- **权限**: mes:cal-plan:update
- **说明**: 为草稿排班计划新增班次，班次数量受轮班方式上限约束。

**请求参数 (MesCalPlanShiftSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 班次编号（创建时忽略） |
| planId | Long | 是 | @NotNull | 排班计划编号 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| name | String | 是 | @NotEmpty | 班次名称 |
| startTime | String | 是 | @NotEmpty | 开始时间（如 08:00） |
| endTime | String | 是 | @NotEmpty | 结束时间（如 17:00） |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long>（班次编号）

**业务逻辑**:
1. 校验所属排班计划存在且状态为草稿。
2. 校验该计划已有班次数量未达到轮班方式的班次上限（单白班 1、两班倒 2、三班倒 3）。
3. 插入计划班次。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |
| 1_040_200_001 | 班次数量已达到轮班方式的上限 |

### 4.2 更新计划班次

- **路径**: PUT /mes/cal/plan-shift/update
- **权限**: mes:cal-plan:update
- **说明**: 更新计划班次（仅所属计划为草稿时允许）。

**请求参数 (MesCalPlanShiftSaveReqVO)**: 同 4.1（id 必传）。

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验班次存在。
2. 校验所属排班计划状态为草稿。
3. 更新班次。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_200_000 | 计划班次不存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |

### 4.3 删除计划班次

- **路径**: DELETE /mes/cal/plan-shift/delete
- **权限**: mes:cal-plan:update
- **说明**: 删除计划班次（仅所属计划为草稿时允许）。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 班次编号 |

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验班次存在。
2. 校验所属排班计划状态为草稿。
3. 删除班次。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_200_000 | 计划班次不存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |

### 4.4 获得计划班次

- **路径**: GET /mes/cal/plan-shift/get
- **权限**: mes:cal-plan:query
- **说明**: 根据编号获得计划班次详情。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 班次编号 |

**响应**: CommonResult&lt;MesCalPlanShiftRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 班次编号 |
| planId | Long | 排班计划编号 |
| sort | Integer | 显示顺序 |
| name | String | 班次名称 |
| startTime | String | 开始时间 |
| endTime | String | 结束时间 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询班次；2. 转换为 RespVO 返回。

### 4.5 获得计划班次分页

- **路径**: GET /mes/cal/plan-shift/page
- **权限**: mes:cal-plan:query
- **说明**: 分页查询计划班次。

**请求参数 (MesCalPlanShiftPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| planId | Long | 否 | - | 排班计划编号 |
| name | String | 否 | - | 班次名称 |

**响应**: CommonResult&lt;PageResult&lt;MesCalPlanShiftRespVO>>（list 字段结构同 4.4）

**业务逻辑**: 1. 按条件分页查询班次；2. 转换为 RespVO 分页返回。

### 4.6 获得指定排班计划的班次列表

- **路径**: GET /mes/cal/plan-shift/list-by-plan
- **权限**: mes:cal-plan:query
- **说明**: 获得指定排班计划下的全部班次列表。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| planId | Long | 是 | - | 排班计划编号 |

**响应**: CommonResult&lt;List&lt;MesCalPlanShiftRespVO>>（字段结构同 4.4）

**业务逻辑**: 1. 按计划编号查询班次列表；2. 转换为 RespVO 列表返回。

---

## 5. 计划班组关联（MesCalPlanTeamController）

### 5.1 创建计划班组关联

- **路径**: POST /mes/cal/plan-team/create
- **权限**: mes:cal-plan:update
- **说明**: 将班组分配到草稿排班计划，同一班组不可重复分配。

**请求参数 (MesCalPlanTeamSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时忽略） |
| planId | Long | 是 | @NotNull | 排班计划编号 |
| teamId | Long | 是 | @NotNull | 班组编号 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long>（关联编号）

**业务逻辑**:
1. 校验排班计划存在且状态为草稿。
2. 校验班组存在。
3. 校验该班组未重复分配到该计划（重复抛 CAL_PLAN_TEAM_DUPLICATE）。
4. 插入计划班组关联。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |
| 1_040_201_000 | 班组不存在 |
| 1_040_202_101 | 该班组已分配到此计划 |

### 5.2 删除计划班组关联

- **路径**: DELETE /mes/cal/plan-team/delete
- **权限**: mes:cal-plan:update
- **说明**: 删除计划班组关联（仅所属计划为草稿时允许）。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 关联编号 |

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验关联记录存在。
2. 校验所属排班计划状态为草稿。
3. 删除关联记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_202_100 | 计划班组关联不存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |

### 5.3 获得指定排班计划的班组列表

- **路径**: GET /mes/cal/plan-team/list-by-plan
- **权限**: mes:cal-plan:query
- **说明**: 获得指定排班计划已分配的班组列表，并拼装班组编码/名称。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| planId | Long | 是 | - | 排班计划编号 |

**响应**: CommonResult&lt;List&lt;MesCalPlanTeamRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 关联编号 |
| planId | Long | 排班计划编号 |
| teamId | Long | 班组编号 |
| teamCode | String | 班组编码（关联班组后拼装） |
| teamName | String | 班组名称（关联班组后拼装） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按计划编号查询计划班组关联列表。
2. 批量查询关联的班组 Map，拼装班组编码与名称。
3. 转换为 RespVO 列表返回。

---

## 6. 班组（MesCalTeamController）

### 6.1 创建班组

- **路径**: POST /mes/cal/team/create
- **权限**: mes:cal-team:create
- **说明**: 创建排班班组，编码唯一。

**请求参数 (MesCalTeamSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 班组编号（创建时忽略） |
| code | String | 是 | @NotEmpty | 班组编码 |
| name | String | 是 | @NotEmpty | 班组名称 |
| calendarType | Integer | 是 | @NotNull | 班组类型 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long>（班组编号）

**业务逻辑**:
1. 校验班组编码唯一（重复抛 CAL_TEAM_CODE_DUPLICATE）。
2. 插入班组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_201_001 | 班组编码已存在 |

### 6.2 更新班组

- **路径**: PUT /mes/cal/team/update
- **权限**: mes:cal-team:update
- **说明**: 更新班组信息，编码唯一。

**请求参数 (MesCalTeamSaveReqVO)**: 同 6.1（id 必传）。

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验班组存在。
2. 校验班组编码唯一（排除自身）。
3. 更新班组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_201_000 | 班组不存在 |
| 1_040_201_001 | 班组编码已存在 |

### 6.3 删除班组

- **路径**: DELETE /mes/cal/team/delete
- **权限**: mes:cal-team:delete
- **说明**: 删除班组，级联删除其成员与排班记录。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 班组编号 |

**响应**: CommonResult&lt;Boolean>

**业务逻辑**:
1. 校验班组存在。
2. 级联删除该班组下全部班组成员。
3. 级联删除该班组全部班组排班记录。
4. 删除班组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_201_000 | 班组不存在 |

### 6.4 获得班组

- **路径**: GET /mes/cal/team/get
- **权限**: mes:cal-team:query
- **说明**: 根据编号获得班组详情。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 班组编号 |

**响应**: CommonResult&lt;MesCalTeamRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 班组编号 |
| code | String | 班组编码 |
| name | String | 班组名称 |
| calendarType | Integer | 班组类型 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询班组；2. 转换为 RespVO 返回。

### 6.5 获得班组分页

- **路径**: GET /mes/cal/team/page
- **权限**: mes:cal-team:query
- **说明**: 分页查询班组。

**请求参数 (MesCalTeamPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| code | String | 否 | - | 班组编码 |
| name | String | 否 | - | 班组名称 |
| calendarType | Integer | 否 | - | 班组类型 |

**响应**: CommonResult&lt;PageResult&lt;MesCalTeamRespVO>>（list 字段结构同 6.4）

**业务逻辑**: 1. 按条件分页查询班组；2. 转换为 RespVO 分页返回。

### 6.6 获得班组列表

- **路径**: GET /mes/cal/team/list
- **权限**: mes:cal-team:query
- **说明**: 获得全部班组列表（下拉选择等场景使用）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MesCalTeamRespVO>>（字段结构同 6.4）

**业务逻辑**: 1. 查询全部班组；2. 转换为 RespVO 列表返回。

### 6.7 导出班组 Excel

- **路径**: GET /mes/cal/team/export-excel
- **权限**: mes:cal-team:export
- **说明**: 按分页条件导出班组 Excel（文件名 班组.xls），不分页导出全量。

**请求参数 (MesCalTeamPageReqVO)**: 同 6.5（pageSize 强制设为不分页）。

**响应**: Excel 文件流（列结构同 MesCalTeamRespVO 的 @ExcelProperty 标注）。

**业务逻辑**: 1. 将分页参数置为不分页；2. 查询班组全量列表；3. 通过 ExcelUtils 写出 Excel。

---

## 7. 班组成员（MesCalTeamMemberController）

### 7.1 创建班组成员

- **路径**: POST /mes/cal/team-member/create
- **权限**: mes:cal-team:create
- **说明**: 将用户加入班组，一个用户只能属于一个班组。

**请求参数 (MesCalTeamMemberSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 成员编号（创建时忽略） |
| teamId | Long | 是 | @NotNull | 班组编号 |
| userId | Long | 是 | @NotNull | 用户编号 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long>（成员编号）

**业务逻辑**:
1. 校验班组存在。
2. 通过 AdminUserApi 校验用户存在。
3. 校验该用户未分配到其他班组（重复抛 CAL_TEAM_MEMBER_USER_DUPLICATE）。
4. 插入班组成员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_201_000 | 班组不存在 |
| 1_040_201_102 | 用户不存在 |
| 1_040_201_101 | 该用户已分配到其他班组 |

### 7.2 删除班组成员

- **路径**: DELETE /mes/cal/team-member/delete
- **权限**: mes:cal-team:delete
- **说明**: 删除班组成员。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 成员编号 |

**响应**: CommonResult&lt;Boolean>

**业务逻辑**: 1. 校验成员存在；2. 删除成员。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_201_100 | 班组成员不存在 |

### 7.3 获得班组成员

- **路径**: GET /mes/cal/team-member/get
- **权限**: mes:cal-team:query
- **说明**: 根据编号获得班组成员详情（不含用户信息拼装）。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 成员编号 |

**响应**: CommonResult&lt;MesCalTeamMemberRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 成员编号 |
| teamId | Long | 班组编号 |
| userId | Long | 用户编号 |
| nickname | String | 用户昵称（列表接口拼装，get 接口为空） |
| telephone | String | 电话（列表接口拼装，get 接口为空） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询成员；2. 转换为 RespVO 返回。

### 7.4 获得班组成员分页

- **路径**: GET /mes/cal/team-member/page
- **权限**: mes:cal-team:query
- **说明**: 分页查询指定班组的成员。

**请求参数 (MesCalTeamMemberPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码 |
| pageSize | Integer | 否 | - | 每页条数 |
| teamId | Long | 是 | @NotNull | 班组编号 |

**响应**: CommonResult&lt;PageResult&lt;MesCalTeamMemberRespVO>>（list 字段结构同 7.3）

**业务逻辑**: 1. 按班组编号分页查询成员；2. 转换为 RespVO 分页返回。

### 7.5 获得班组成员列表

- **路径**: GET /mes/cal/team-member/list-by-team
- **权限**: mes:cal-team:query
- **说明**: 获得班组成员列表，支持单个 teamId 或多个 teamIds，并拼装用户昵称与电话。

**请求参数**: Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| teamId | Long | 否 | - | 班组编号（与 teamIds 至少传一个） |
| teamIds | Collection&lt;Long> | 否 | - | 班组编号集合（优先使用） |

**响应**: CommonResult&lt;List&lt;MesCalTeamMemberRespVO>>（字段结构同 7.3，nickname/telephone 均已拼装）

**业务逻辑**:
1. teamIds 非空时按班组编号集合查询；否则 teamId 非空时按单个班组查询；否则返回空列表。
2. 通过 AdminUserApi 批量查询成员对应的系统用户。
3. 拼装用户昵称（nickname）与电话（telephone）后返回。

---

## 8. 班组排班（MesCalTeamShiftController）

### 8.1 获得班组排班列表

- **路径**: GET /mes/cal/team-shift/list
- **权限**: mes:cal-team-shift:query
- **说明**: 按班组/计划/日期范围查询班组排班记录，并拼装班组名称与班次名称。

**请求参数 (MesCalTeamShiftListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| teamId | Long | 否 | - | 班组编号 |
| teamIds | Collection&lt;Long> | 否 | - | 班组编号集合 |
| planId | Long | 否 | - | 排班计划编号 |
| startDay | LocalDateTime | 否 | @DateTimeFormat | 开始日期 |
| endDay | LocalDateTime | 否 | @DateTimeFormat | 结束日期 |

**响应**: CommonResult&lt;List&lt;MesCalTeamShiftRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 排班记录编号 |
| planId | Long | 排班计划编号 |
| teamId | Long | 班组编号 |
| teamName | String | 班组名称（拼装） |
| shiftId | Long | 班次编号 |
| shiftName | String | 班次名称（拼装） |
| day | LocalDateTime | 排班日期 |
| sort | Integer | 排序 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按班组/计划/日期范围条件查询班组排班记录，为空时直接返回空列表。
2. 批量查询关联的班组 Map 与计划班次 Map。
3. 拼装班组名称与班次名称后返回。

---

## 附：排班日历域错误码汇总

| 错误码 | 说明 |
|-------|------|
| 1_040_200_000 | 计划班次不存在 |
| 1_040_200_001 | 班次数量已达到轮班方式的上限 |
| 1_040_201_000 | 班组不存在 |
| 1_040_201_001 | 班组编码已存在 |
| 1_040_201_100 | 班组成员不存在 |
| 1_040_201_101 | 该用户已分配到其他班组 |
| 1_040_201_102 | 用户不存在 |
| 1_040_201_200 | 班组排班记录不存在 |
| 1_040_201_201 | 班组数量不满足轮班方式要求 |
| 1_040_201_202 | 班次数量不满足轮班方式要求 |
| 1_040_201_203 | 按天倒班必须填写合法的倒班天数 |
| 1_040_201_204 | 不支持的倒班方式：{} |
| 1_040_202_000 | 排班计划不存在 |
| 1_040_202_001 | 排班计划编码已存在 |
| 1_040_202_002 | 排班计划已确认，不允许修改或删除 |
| 1_040_202_003 | 确认排班计划时，分配的班组数量与轮班方式不匹配 |
| 1_040_202_100 | 计划班组关联不存在 |
| 1_040_202_101 | 该班组已分配到此计划 |
| 1_040_203_000 | 假期设置不存在 |
