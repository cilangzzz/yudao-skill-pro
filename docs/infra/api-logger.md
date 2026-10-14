# API 日志接口 (ApiAccessLogController / ApiErrorLogController)

> 记录系统所有 API 的访问日志与错误日志（由框架过滤器/全局异常处理器自动写入），管理端提供日志的分页查询、详情查看、Excel 导出以及错误日志的处理状态更新。

## 接口路径前缀

- `/infra/api-access-log` (Controller: ApiAccessLogController) — API 访问日志
- `/infra/api-error-log` (Controller: ApiErrorLogController) — API 错误日志

日志数据来源：框架层通过 `@ApiAccessLog` 注解/Aop 过滤器产生访问日志，全局异常处理器捕获未处理异常产生错误日志，经 RPC 调用 `createApiAccessLog` / `createApiErrorLog` 落库（写入时对 `requestParams`/`resultMsg` 按最大长度截断，租户上下文缺失时忽略租户插入），管理端不做新增/删除操作。

## 1. API 访问日志（ApiAccessLogController）

### 1.1 获得 API 访问日志

- **路径**: GET `/infra/api-access-log/get`
- **权限**: `infra:api-access-log:query`
- **说明**: 根据编号查询单条 API 访问日志详情

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 日志编号 |

**响应**: `CommonResult<ApiAccessLogRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 日志主键 |
| traceId | String | 链路追踪编号 |
| userId | Long | 用户编号 |
| userType | Integer | 用户类型（参见 UserTypeEnum 枚举） |
| applicationName | String | 应用名 |
| requestMethod | String | 请求方法名 |
| requestUrl | String | 请求地址 |
| requestParams | String | 请求参数 |
| responseBody | String | 响应结果 |
| userIp | String | 用户 IP |
| userAgent | String | 浏览器 UA |
| operateModule | String | 操作模块 |
| operateName | String | 操作名 |
| operateType | Integer | 操作分类（字典 infra_operate_type） |
| beginTime | LocalDateTime | 开始请求时间 |
| endTime | LocalDateTime | 结束请求时间 |
| duration | Integer | 执行时长（毫秒） |
| resultCode | Integer | 结果码 |
| resultMsg | String | 结果提示 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 `ApiAccessLogService.getApiAccessLog(id)`，由 Mapper `selectById` 按主键查询。
2. 通过 `BeanUtils.toBean` 将 `ApiAccessLogDO` 转换为 `ApiAccessLogRespVO` 返回。

### 1.2 获得 API 访问日志分页

- **路径**: GET `/infra/api-access-log/page`
- **权限**: `infra:api-access-log:query`
- **说明**: 分页查询 API 访问日志，支持多条件筛选

**请求参数 (ApiAccessLogPageReqVO)**，继承 `PageParam`（pageNo 默认 1、pageSize 默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码，从 1 开始 |
| pageSize | Integer | 否 | 分页参数 | 每页条数 |
| userId | Long | 否 | 无 | 用户编号 |
| userType | Integer | 否 | 无 | 用户类型 |
| applicationName | String | 否 | 无 | 应用名 |
| requestUrl | String | 否 | 无 | 请求地址，模糊匹配 |
| beginTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 开始时间区间 |
| duration | Integer | 否 | 无 | 执行时长，大于等于，单位：毫秒 |
| resultCode | Integer | 否 | 无 | 结果码 |

**响应**: `CommonResult<PageResult<ApiAccessLogRespVO>>`，列表项字段同 1.1 响应表。

**业务逻辑**:
1. 直接调用 Mapper `selectPage(pageReqVO)`，按分页请求 VO 中的条件拼接查询。
2. `PageResult<ApiAccessLogDO>` 经 `BeanUtils.toBean` 转换为 `PageResult<ApiAccessLogRespVO>` 返回。

### 1.3 导出 API 访问日志 Excel

- **路径**: GET `/infra/api-access-log/export-excel`
- **权限**: `infra:api-access-log:export`
- **说明**: 按与分页相同的筛选条件导出全量访问日志 Excel（文件名「API 访问日志.xls」），并通过 `@ApiAccessLog(operateType = EXPORT)` 记录本次导出操作日志

**请求参数 (ApiAccessLogPageReqVO)**: 同 1.2 请求参数表（pageSize 由服务端强制覆盖，筛选条件生效）。

**响应**: 二进制文件流（Excel 下载），非 CommonResult。

**业务逻辑**:
1. 将 `exportReqVO.pageSize` 置为 `PageParam.PAGE_SIZE_NONE`，即不分页查询全量数据。
2. 复用 `getApiAccessLogPage` 按筛选条件查询列表。
3. 通过 `ExcelUtils.write` 按 `ApiAccessLogRespVO` 的 `@ExcelProperty` 注解写出 Excel 文件到响应流。

## 2. API 错误日志（ApiErrorLogController）

### 2.1 更新 API 错误日志的状态

- **路径**: PUT `/infra/api-error-log/update-status`
- **权限**: `infra:api-error-log:update-status`
- **说明**: 对错误日志进行标记处理（已处理 / 已忽略），仅允许处理「未处理」状态的记录

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 错误日志编号 |
| processStatus | Integer | 是 | @RequestParam(required) | 处理状态：1 已处理、2 已忽略 |

**响应**: `CommonResult<Boolean>`，固定返回 `true`。

**业务逻辑**:
1. 按 id 调用 Mapper `selectById` 查询错误日志。
2. 记录不存在时抛出 `API_ERROR_LOG_NOT_FOUND`（1_001_002_000）。
3. 记录的 `processStatus` 不是初始状态 `INIT(0)`（未处理）时，抛出 `API_ERROR_LOG_PROCESSED`（1_001_002_001），即已处理/已忽略的日志不允许再次更新。
4. 校验通过后按 id 更新 `processStatus`（目标状态）、`processUserId`（当前登录用户 `getLoginUserId()`）、`processTime`（当前时间）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_002_000 | API 错误日志不存在 |
| 1_001_002_001 | API 错误日志已处理 |

### 2.2 获得 API 错误日志

- **路径**: GET `/infra/api-error-log/get`
- **权限**: `infra:api-error-log:query`
- **说明**: 根据编号查询单条 API 错误日志详情

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 错误日志编号 |

**响应**: `CommonResult<ApiErrorLogRespVO>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| traceId | String | 链路追踪编号 |
| userId | Long | 用户编号 |
| userType | Integer | 用户类型 |
| applicationName | String | 应用名 |
| requestMethod | String | 请求方法名 |
| requestUrl | String | 请求地址 |
| requestParams | String | 请求参数 |
| userIp | String | 用户 IP |
| userAgent | String | 浏览器 UA |
| exceptionTime | LocalDateTime | 异常发生时间 |
| exceptionName | String | 异常名 |
| exceptionMessage | String | 异常导致的消息 |
| exceptionRootCauseMessage | String | 异常导致的根消息 |
| exceptionStackTrace | String | 异常的栈轨迹 |
| exceptionClassName | String | 异常发生的类全名 |
| exceptionFileName | String | 异常发生的类文件 |
| exceptionMethodName | String | 异常发生的方法名 |
| exceptionLineNumber | Integer | 异常发生的方法所在行 |
| processStatus | Integer | 处理状态（0 未处理 / 1 已处理 / 2 已忽略，字典 api_error_log_process_status） |
| processTime | LocalDateTime | 处理时间 |
| processUserId | Integer | 处理用户编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 `ApiErrorLogService.getApiErrorLog(id)`，由 Mapper `selectById` 按主键查询。
2. 通过 `BeanUtils.toBean` 将 `ApiErrorLogDO` 转换为 `ApiErrorLogRespVO` 返回。

### 2.3 获得 API 错误日志分页

- **路径**: GET `/infra/api-error-log/page`
- **权限**: `infra:api-error-log:query`
- **说明**: 分页查询 API 错误日志，支持多条件筛选

**请求参数 (ApiErrorLogPageReqVO)**，继承 `PageParam`（pageNo 默认 1、pageSize 默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数 | 页码，从 1 开始 |
| pageSize | Integer | 否 | 分页参数 | 每页条数 |
| userId | Long | 否 | 无 | 用户编号 |
| userType | Integer | 否 | 无 | 用户类型 |
| applicationName | String | 否 | 无 | 应用名 |
| requestUrl | String | 否 | 无 | 请求地址 |
| exceptionTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 异常发生时间区间 |
| processStatus | Integer | 否 | 无 | 处理状态（0 未处理 / 1 已处理 / 2 已忽略） |

**响应**: `CommonResult<PageResult<ApiErrorLogRespVO>>`，列表项字段同 2.2 响应表。

**业务逻辑**:
1. 直接调用 Mapper `selectPage(pageReqVO)`，按分页请求 VO 中的条件拼接查询。
2. `PageResult<ApiErrorLogDO>` 经 `BeanUtils.toBean` 转换为 `PageResult<ApiErrorLogRespVO>` 返回。

### 2.4 导出 API 错误日志 Excel

- **路径**: GET `/infra/api-error-log/export-excel`
- **权限**: `infra:api-error-log:export`
- **说明**: 按与分页相同的筛选条件导出全量错误日志 Excel（文件名「API 错误日志.xls」），并通过 `@ApiAccessLog(operateType = EXPORT)` 记录本次导出操作日志

**请求参数 (ApiErrorLogPageReqVO)**: 同 2.3 请求参数表（pageSize 由服务端强制覆盖，筛选条件生效）。

**响应**: 二进制文件流（Excel 下载），非 CommonResult。

**业务逻辑**:
1. 将 `exportReqVO.pageSize` 置为 `PageParam.PAGE_SIZE_NONE`，即不分页查询全量数据。
2. 复用 `getApiErrorLogPage` 按筛选条件查询列表。
3. 通过 `ExcelUtils.write` 按 `ApiErrorLogRespVO` 的 `@ExcelProperty` 注解写出 Excel 文件到响应流。
