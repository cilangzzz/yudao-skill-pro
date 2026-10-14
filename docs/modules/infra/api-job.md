# 定时任务接口 (JobController)

> 基于 Quartz 的定时任务管理与执行日志查询，支持任务的创建/修改/启停/手动触发/Quartz 同步，以及任务执行日志的分页查询与导出。

## 接口路径前缀

- `/infra/job` (Controller: JobController) —— 定时任务管理
- `/infra/job-log` (Controller: JobLogController) —— 定时任务日志

## 1. 定时任务管理（JobController）

### 1.1 创建定时任务

- **路径**: POST `/infra/job/create`
- **权限**: `infra:job:create`
- **说明**: 新增定时任务，校验 CRON 与处理器后写入数据库并注册到 Quartz 调度器。

**请求参数 (JobSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 任务编号（创建时可不传） |
| name | String | 是 | @NotEmpty | 任务名称 |
| handlerName | String | 是 | @NotEmpty | 处理器的名字（Spring Bean 名） |
| handlerParam | String | 否 | - | 处理器的参数 |
| cronExpression | String | 是 | @NotEmpty | CRON 表达式 |
| retryCount | Integer | 是 | @NotNull | 重试次数 |
| retryInterval | Integer | 是 | @NotNull | 重试间隔（毫秒） |
| monitorTimeout | Integer | 否 | - | 监控超时时间 |

**响应**: `CommonResult<Long>` —— 任务编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新建任务的编号 |

**业务逻辑**:
1. 校验 CRON 表达式合法性（CronUtils.isValid），非法抛 JOB_CRON_EXPRESSION_VALID。
2. 校验 handlerName 唯一性，已存在同名处理器则抛 JOB_HANDLER_EXISTS。
3. 校验 JobHandler Bean 存在（SpringUtil.getBean），Bean 不存在抛 JOB_HANDLER_BEAN_NOT_EXISTS，类型未实现 JobHandler 接口抛 JOB_HANDLER_BEAN_TYPE_ERROR。
4. 插入 JobDO，状态置为 INIT，monitorTimeout 为空时补 0。
5. 调用 SchedulerManager.addJob 将任务注册到 Quartz（含重试次数与重试间隔）。
6. 更新 JobDO 状态为 NORMAL，返回任务编号（整体 @Transactional 事务）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |
| 1_001_001_001 | 定时任务的处理器已经存在 |
| 1_001_001_005 | CRON 表达式不正确 |
| 1_001_001_006 | 定时任务的处理器 Bean 不存在，注意 Bean 默认首字母小写 |
| 1_001_001_007 | 定时任务的处理器 Bean 类型不正确，未实现 JobHandler 接口 |

### 1.2 更新定时任务

- **路径**: PUT `/infra/job/update`
- **权限**: `infra:job:update`
- **说明**: 修改任务配置（名称/处理器/CRON/重试等），仅开启状态的任务允许修改，并同步更新 Quartz。

**请求参数 (JobSaveReqVO)**: 同 1.1（更新时 id 必传）

**响应**: `CommonResult<Boolean>` —— 是否成功

**业务逻辑**:
1. 校验 CRON 表达式合法性。
2. 校验任务存在（不存在抛 JOB_NOT_EXISTS）。
3. 校验任务状态为开启（NORMAL），暂停状态不允许修改，抛 JOB_UPDATE_ONLY_NORMAL_STATUS。
4. 校验 JobHandler Bean 存在且实现 JobHandler 接口。
5. 更新 JobDO（monitorTimeout 为空时补 0）。
6. 调用 SchedulerManager.updateJob 更新 Quartz 中的处理器参数、CRON、重试配置。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |
| 1_001_001_004 | 只有开启状态的任务，才可以修改 |
| 1_001_001_005 | CRON 表达式不正确 |
| 1_001_001_006 | 定时任务的处理器 Bean 不存在，注意 Bean 默认首字母小写 |
| 1_001_001_007 | 定时任务的处理器 Bean 类型不正确，未实现 JobHandler 接口 |

### 1.3 更新定时任务的状态

- **路径**: PUT `/infra/job/update-status`
- **权限**: `infra:job:update`
- **说明**: 开启/暂停任务，同步 resume/pause Quartz Job。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 任务编号 |
| status | Integer | 是 | - | 目标状态（1 开启 / 2 暂停，参见 JobStatusEnum） |

**响应**: `CommonResult<Boolean>` —— 是否成功

**业务逻辑**:
1. 校验 status 只能为 NORMAL 或 STOP，否则抛 JOB_CHANGE_STATUS_INVALID。
2. 校验任务存在。
3. 校验任务不处于目标状态，已处于该状态抛 JOB_CHANGE_STATUS_EQUALS。
4. 更新 JobDO 的 status 字段。
5. 状态为开启时调用 SchedulerManager.resumeJob，否则 pauseJob 暂停 Quartz 任务。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |
| 1_001_001_002 | 只允许修改为开启或者关闭状态 |
| 1_001_001_003 | 定时任务已经处于该状态，无需修改 |

### 1.4 删除定时任务

- **路径**: DELETE `/infra/job/delete`
- **权限**: `infra:job:delete`
- **说明**: 删除单个任务（逻辑删除数据库记录并从 Quartz 移除）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 任务编号 |

**响应**: `CommonResult<Boolean>` —— 是否成功

**业务逻辑**:
1. 校验任务存在（不存在抛 JOB_NOT_EXISTS）。
2. 删除数据库 JobDO 记录。
3. 调用 SchedulerManager.deleteJob 从 Quartz 中删除该任务。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |

### 1.5 批量删除定时任务

- **路径**: DELETE `/infra/job/delete-list`
- **权限**: `infra:job:delete`
- **说明**: 按编号列表批量删除任务并逐一从 Quartz 移除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List\<Long\> | 是 | - | 任务编号列表 |

**响应**: `CommonResult<Boolean>` —— 是否成功

**业务逻辑**:
1. 查询 ids 对应的 JobDO 列表。
2. 批量删除数据库记录（deleteByIds）。
3. 遍历删除的任务，逐个调用 SchedulerManager.deleteJob 从 Quartz 移除。

### 1.6 触发定时任务

- **路径**: PUT `/infra/job/trigger`
- **权限**: `infra:job:trigger`
- **说明**: 手动立即执行一次任务，不改变 CRON 调度计划。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 任务编号 |

**响应**: `CommonResult<Boolean>` —— 是否成功

**业务逻辑**:
1. 校验任务存在。
2. 调用 SchedulerManager.triggerJob 按 jobId、handlerName、handlerParam 立即触发一次 Quartz Job。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |

### 1.7 同步定时任务

- **路径**: POST `/infra/job/sync`
- **权限**: `infra:job:create`
- **说明**: 将数据库中的任务配置全量同步到 Quartz 调度器（用于集群/重启后修复）。

**请求参数**: 无

**响应**: `CommonResult<Boolean>` —— 是否成功

**业务逻辑**:
1. 查询数据库中全部 JobDO 任务列表。
2. 遍历每个任务：先调用 SchedulerManager.deleteJob 删除 Quartz 旧任务，再 addJob 重建（含 handlerParam、CRON、重试配置）。
3. 若任务状态为暂停（STOP），追加调用 pauseJob 保持暂停。
4. 记录同步完成日志。

### 1.8 获得定时任务

- **路径**: GET `/infra/job/get`
- **权限**: `infra:job:query`
- **说明**: 按编号查询任务详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 任务编号 |

**响应**: `CommonResult<JobRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 任务编号 |
| name | String | 任务名称 |
| status | Integer | 任务状态（参见 JobStatusEnum） |
| handlerName | String | 处理器的名字 |
| handlerParam | String | 处理器的参数 |
| cronExpression | String | CRON 表达式 |
| retryCount | Integer | 重试次数 |
| retryInterval | Integer | 重试间隔 |
| monitorTimeout | Integer | 监控超时时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 JobDO 并转换为 JobRespVO 返回。

### 1.9 获得定时任务分页

- **路径**: GET `/infra/job/page`
- **权限**: `infra:job:query`
- **说明**: 分页查询定时任务列表。

**请求参数 (JobPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull @Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull @Min(1) @Max(200) | 每页条数，默认 10 |
| name | String | 否 | - | 任务名称，模糊匹配 |
| status | Integer | 否 | - | 任务状态，参见 JobStatusEnum |
| handlerName | String | 否 | - | 处理器的名字，模糊匹配 |

**响应**: `CommonResult<PageResult<JobRespVO>>`，列表项字段同 1.8。

**业务逻辑**: 1. 按条件分页查询 JobDO（name/handlerName 模糊、status 精确）并转换为 JobRespVO 分页结果。

### 1.10 导出定时任务 Excel

- **路径**: GET `/infra/job/export-excel`
- **权限**: `infra:job:export`
- **说明**: 按分页条件查询全部任务并导出为 Excel 文件（文件名「定时任务.xls」）。

**请求参数 (JobPageReqVO)**: 同 1.9（导出时 pageSize 置为 -1 不分页）

**响应**: Excel 文件流（列定义见 JobRespVO 的 @ExcelProperty 注解：任务编号、任务名称、任务状态、处理器的名字、处理器的参数、CRON 表达式、重试次数、重试间隔、监控超时时间、创建时间）。

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（-1）查询全部数据。
2. 复用 getJobPage 查询并转换为 JobRespVO 列表。
3. 通过 ExcelUtils.write 输出 Excel 到响应流；记录操作类型为导出（@ApiAccessLog EXPORT）。

### 1.11 获得定时任务的下 n 次执行时间

- **路径**: GET `/infra/job/get_next_times`
- **权限**: `infra:job:query`
- **说明**: 根据任务的 CRON 表达式计算未来 n 次执行时间。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 任务编号 |
| count | Integer | 否 | - | 数量，默认 5 |

**响应**: `CommonResult<List<LocalDateTime>>` —— 未来执行时间列表

**业务逻辑**:
1. 按 id 查询任务，任务不存在时返回空列表。
2. 使用 CronUtils.getNextTimes 按任务的 cronExpression 计算下 n 次执行时间并返回。

## 2. 定时任务日志（JobLogController）

### 2.1 获得定时任务日志

- **路径**: GET `/infra/job-log/get`
- **权限**: `infra:job:query`
- **说明**: 按编号查询任务执行日志详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 日志编号 |

**响应**: `CommonResult<JobLogRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 日志编号 |
| jobId | Long | 任务编号 |
| handlerName | String | 处理器的名字 |
| handlerParam | String | 处理器的参数 |
| executeIndex | Integer | 第几次执行 |
| beginTime | LocalDateTime | 开始执行时间 |
| endTime | LocalDateTime | 结束执行时间 |
| duration | Integer | 执行时长（毫秒） |
| status | Integer | 任务状态（参见 JobLogStatusEnum：RUNNING/SUCCESS/FAILURE） |
| result | String | 结果数据 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询 JobLogDO 并转换为 JobLogRespVO 返回。

### 2.2 获得定时任务日志分页

- **路径**: GET `/infra/job-log/page`
- **权限**: `infra:job:query`
- **说明**: 分页查询任务执行日志。

**请求参数 (JobLogPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull @Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull @Min(1) @Max(200) | 每页条数，默认 10 |
| jobId | Long | 否 | - | 任务编号 |
| handlerName | String | 否 | - | 处理器的名字，模糊匹配 |
| beginTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 开始执行时间 |
| endTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 结束执行时间 |
| status | Integer | 否 | - | 任务状态，参见 JobLogStatusEnum |

**响应**: `CommonResult<PageResult<JobLogRespVO>>`，列表项字段同 2.1。

**业务逻辑**: 1. 按条件分页查询 JobLogDO（jobId/status 精确、handlerName 模糊、beginTime/endTime 范围）并转换为 JobLogRespVO 分页结果。

### 2.3 导出定时任务日志 Excel

- **路径**: GET `/infra/job-log/export-excel`
- **权限**: `infra:job:export`
- **说明**: 按分页条件查询全部日志并导出为 Excel 文件（文件名「任务日志.xls」）。

**请求参数 (JobLogPageReqVO)**: 同 2.2（导出时 pageSize 置为 -1 不分页）

**响应**: Excel 文件流（列定义见 JobLogRespVO 的 @ExcelProperty 注解：日志编号、任务编号、处理器的名字、处理器的参数、第几次执行、开始执行时间、结束执行时间、执行时长、任务状态、结果数据、创建时间）。

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（-1）查询全部数据。
2. 复用 getJobLogPage 查询并转换为 JobLogRespVO 列表。
3. 通过 ExcelUtils.write 输出 Excel 到响应流；记录操作类型为导出（@ApiAccessLog EXPORT）。

## 附：错误码汇总（定时任务 1_001_001_XXX）

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |
| 1_001_001_001 | 定时任务的处理器已经存在 |
| 1_001_001_002 | 只允许修改为开启或者关闭状态 |
| 1_001_001_003 | 定时任务已经处于该状态，无需修改 |
| 1_001_001_004 | 只有开启状态的任务，才可以修改 |
| 1_001_001_005 | CRON 表达式不正确 |
| 1_001_001_006 | 定时任务的处理器 Bean 不存在，注意 Bean 默认首字母小写 |
| 1_001_001_007 | 定时任务的处理器 Bean 类型不正确，未实现 JobHandler 接口 |

> 备注：日志的新增（createJobLog）与结果回写（updateJobLogResultAsync，@Async 异步更新状态为 SUCCESS/FAILURE）由 Quartz Job 执行链路内部调用，不暴露 admin 端点；日志清理（cleanJobLog，按 exceedDay 循环分批删除过期记录）亦为内部方法，供定时任务自身调度调用。
