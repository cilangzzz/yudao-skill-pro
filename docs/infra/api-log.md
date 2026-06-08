# 日志管理接口

## 概述

API 日志审计模块记录系统中所有 API 的访问日志和异常日志，支持链路追踪和问题分析。

### 业务定位

- 记录 API 访问日志（请求参数、响应结果、执行时长等）
- 记录 API 异常日志（异常类型、堆栈信息、处理状态等）
- 通过 traceId 关联访问日志和错误日志，便于问题排查

### 核心实体

| 实体 | 说明 |
|-----|------|
| ApiAccessLogDO | API 访问日志，记录正常请求的完整信息 |
| ApiErrorLogDO | API 异常日志，记录异常请求的详细信息和处理状态 |

## 数据模型

### infra_api_access_log（API 访问日志表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 编号，主键 |
| trace_id | VARCHAR | 链路追踪编号 |
| user_id | BIGINT | 用户编号 |
| user_type | TINYINT | 用户类型 |
| application_name | VARCHAR | 应用名 |
| request_method | VARCHAR | 请求方法 |
| request_url | VARCHAR | 请求地址 |
| request_params | VARCHAR | 请求参数 |
| response_body | VARCHAR | 响应结果 |
| user_ip | VARCHAR | 用户 IP |
| user_agent | VARCHAR | 浏览器 UA |
| operate_module | VARCHAR | 操作模块 |
| operate_name | VARCHAR | 操作名 |
| operate_type | TINYINT | 操作分类 |
| begin_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| duration | INT | 执行时长（毫秒） |
| result_code | INT | 结果码 |
| result_msg | VARCHAR | 结果提示 |

### infra_api_error_log（API 异常日志表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 编号，主键 |
| user_id | BIGINT | 用户编号 |
| trace_id | VARCHAR | 链路追踪编号 |
| user_type | TINYINT | 用户类型 |
| application_name | VARCHAR | 应用名 |
| request_method | VARCHAR | 请求方法 |
| request_url | VARCHAR | 请求地址 |
| request_params | VARCHAR | 请求参数 |
| user_ip | VARCHAR | 用户 IP |
| user_agent | VARCHAR | 浏览器 UA |
| exception_time | DATETIME | 异常时间 |
| exception_name | VARCHAR | 异常名 |
| exception_message | VARCHAR | 异常消息 |
| exception_root_cause_message | VARCHAR | 异常根消息 |
| exception_stack_trace | VARCHAR | 异常栈轨迹 |
| exception_class_name | VARCHAR | 异常类名 |
| exception_file_name | VARCHAR | 异常文件名 |
| exception_method_name | VARCHAR | 异常方法名 |
| exception_line_number | INT | 异常行号 |
| process_status | TINYINT | 处理状态 |
| process_time | DATETIME | 处理时间 |
| process_user_id | BIGINT | 处理用户编号 |

## 访问日志接口

### 1. 访问日志列表

- **路径**: `GET /infra/api-access-log/list`
- **说明**: 分页查询 API 访问日志
- **权限**: `infra:api-access-log:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| userId | Long | 否 | 用户编号 |
| userType | Integer | 否 | 用户类型 |
| requestUrl | String | 否 | 请求地址（模糊匹配） |
| operateModule | String | 否 | 操作模块 |
| operateName | String | 否 | 操作名 |
| operateType | Integer | 否 | 操作分类 |
| resultCode | Integer | 否 | 结果码 |
| beginTime | Date[] | 否 | 请求时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ApiAccessLogDO>>`

### 2. 导出访问日志

- **路径**: `GET /infra/api-access-log/export`
- **说明**: 导出访问日志为 Excel 文件
- **权限**: `infra:api-access-log:export`

## 异常日志接口

### 3. 异常日志列表

- **路径**: `GET /infra/api-error-log/list`
- **说明**: 分页查询 API 异常日志
- **权限**: `infra:api-error-log:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| userId | Long | 否 | 用户编号 |
| processStatus | Integer | 否 | 处理状态 |
| exceptionTime | Date[] | 否 | 异常时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ApiErrorLogDO>>`

### 4. 更新异常处理状态

- **路径**: `PUT /infra/api-error-log/update-status`
- **说明**: 更新异常日志的处理状态
- **权限**: `infra:api-error-log:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 日志编号 |
| processStatus | Integer | 是 | 处理状态 |

### 5. 导出异常日志

- **路径**: `GET /infra/api-error-log/export`
- **说明**: 导出异常日志为 Excel 文件
- **权限**: `infra:api-error-log:export`

## 关键实现

- **ApiAccessLogService**: 访问日志服务
- **ApiErrorLogService**: 异常日志服务
- 日志记录通过 AOP 拦截器自动采集，无需业务代码手动记录

## 最佳实践

- **链路追踪**: 通过 traceId 关联 API 访问日志和错误日志，便于问题排查
- **异常处理**: 异常日志支持 process_status 标记处理状态，便于跟踪异常处理进度
- **性能分析**: 通过 duration 字段分析 API 响应时间，识别慢接口
