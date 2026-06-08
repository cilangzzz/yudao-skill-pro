# 定时任务接口

## 概述

定时任务管理基于 Quartz 框架，提供任务调度的动态配置和监控能力。

### 业务定位

- 基于 Quartz 实现分布式定时任务调度
- 支持任务的动态创建、修改、暂停、恢复和删除
- 提供任务执行日志记录和监控

### 核心实体

| 实体 | 说明 |
|-----|------|
| JobDO | 定时任务定义，存储任务配置信息 |
| JobLogDO | 任务执行日志，记录每次执行的状态和结果 |

## 数据模型

### infra_job（定时任务表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 任务编号，主键 |
| name | VARCHAR | 任务名称 |
| status | TINYINT | 任务状态 |
| handler_name | VARCHAR | 处理器名称（JobHandler 实现类标识） |
| handler_param | VARCHAR | 处理器参数 |
| cron_expression | VARCHAR | CRON 表达式 |
| retry_count | INT | 重试次数 |
| retry_interval | INT | 重试间隔（毫秒） |
| monitor_timeout | INT | 监控超时时间（毫秒） |

### infra_job_log（定时任务日志表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 日志编号，主键 |
| job_id | BIGINT | 任务编号，关联 JobDO |
| handler_name | VARCHAR | 处理器名称 |
| handler_param | VARCHAR | 处理器参数 |
| execute_index | INT | 第几次执行 |
| begin_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| duration | INT | 执行时长（毫秒） |
| status | TINYINT | 执行状态 |
| result | VARCHAR | 执行结果 |

## 接口列表

### 1. 任务列表查询

- **路径**: `GET /infra/job/list`
- **说明**: 分页查询定时任务列表
- **权限**: `infra:job:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 任务名称（模糊匹配） |
| status | Integer | 否 | 任务状态 |
| handlerName | String | 否 | 处理器名称 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<JobDO>>`

### 2. 创建任务

- **路径**: `POST /infra/job/create`
- **说明**: 创建新的定时任务
- **权限**: `infra:job:create`
- **请求参数**: JobSaveReqVO（含 name, handlerName, handlerParam, cronExpression, retryCount, retryInterval 等）

### 3. 更新任务

- **路径**: `PUT /infra/job/update`
- **说明**: 更新定时任务配置
- **权限**: `infra:job:update`

### 4. 删除任务

- **路径**: `DELETE /infra/job/delete`
- **说明**: 删除定时任务
- **权限**: `infra:job:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 任务编号 |

### 5. 更新任务状态

- **路径**: `PUT /infra/job/update-status`
- **说明**: 更新任务状态（启用/暂停）
- **权限**: `infra:job:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 任务编号 |
| status | Integer | 是 | 目标状态 |

### 6. 手动执行任务

- **路径**: `PUT /infra/job/trigger`
- **说明**: 手动触发一次任务执行
- **权限**: `infra:job:update`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 任务编号 |

## 任务日志接口

### 7. 任务日志列表

- **路径**: `GET /infra/job-log/list`
- **说明**: 分页查询任务执行日志
- **权限**: `infra:job-log:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| jobId | Long | 否 | 任务编号 |
| status | Integer | 否 | 执行状态 |
| beginTime | Date[] | 否 | 执行时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

## 关键实现

- **JobService**: 定时任务服务接口，与 Quartz 集成管理任务调度
- **JobServiceImpl**: 服务实现类，封装 Quartz SchedulerManager 操作
- **JobLogService**: 任务日志服务，记录执行日志
- **JobHandler**: 任务处理器抽象接口，业务实现需继承此类

## 自定义 JobHandler

```java
@Component
@JobHandler("demoJobHandler")
public class DemoJobHandler extends JobHandler {
    @Override
    public String execute(String param) throws Exception {
        // 业务逻辑
        return JobHandler.SUCCESS;
    }
}
```

## 最佳实践

- **幂等性**: JobHandler.execute() 应实现幂等性，避免重复执行产生副作用
- **参数传递**: 通过 handlerParam 传递业务参数，支持 JSON 格式
- **重试机制**: 配置 retryCount 和 retryInterval 实现失败重试
- **监控超时**: 配置 monitorTimeout 实现任务执行超时告警

## 错误码

| 错误码 | 说明 |
|-------|------|
| 1_001_001_000 | 定时任务不存在 |
