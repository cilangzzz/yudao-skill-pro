# 基础设施模块 (infra)

> infra 模块是整个系统的"基础设施层"，提供文件存储、代码生成、定时任务、API日志、系统配置、数据源管理等跨业务模块的通用能力支撑。

## 模块概述

- **模块路径**: yudao-module-infra
- **业务定位**: 作为底层基础设施模块，不直接面向终端用户业务，而是为其他业务模块提供技术能力支撑
- **核心职责**: 文件存储服务、代码生成器、定时任务管理、API日志审计、系统配置管理、数据源管理

## 核心功能点

| 功能 | 说明 | 关键实体 |
|-----|------|---------|
| 文件存储服务 | 统一的文件上传、下载、管理能力，支持多存储渠道（本地/S3/OSS/FTP等） | FileDO, FileConfigDO, FileContentDO |
| 代码生成器 | 基于数据库表结构自动生成 CRUD 代码，支持多前端框架（Vue2/Vue3/Vben/UniApp） | CodegenTableDO, CodegenColumnDO |
| 定时任务管理 | 基于 Quartz 的任务调度管理，支持动态配置、重试和监控 | JobDO, JobLogDO |
| API日志审计 | 记录 API 访问日志和异常日志，支持链路追踪和问题分析 | ApiAccessLogDO, ApiErrorLogDO |
| 系统配置管理 | 键值对形式的系统参数配置，支持分类和可见性控制 | ConfigDO |
| 数据源管理 | 多数据源配置和管理，支持代码生成器连接不同数据库 | DataSourceConfigDO |

## API 接口索引

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| `/infra/file/upload` | POST | 上传文件 | - |
| `/infra/file/list` | GET | 文件列表 | infra:file:query |
| `/infra/file/delete` | DELETE | 删除文件 | infra:file:delete |
| `/infra/file-config/list` | GET | 文件配置列表 | infra:file-config:query |
| `/infra/file-config/create` | POST | 创建文件配置 | infra:file-config:create |
| `/infra/config/list` | GET | 配置列表 | infra:config:query |
| `/infra/config/create` | POST | 创建配置 | infra:config:create |
| `/infra/config/update` | PUT | 更新配置 | infra:config:update |
| `/infra/config/delete` | DELETE | 删除配置 | infra:config:delete |
| `/infra/job/list` | GET | 任务列表 | infra:job:query |
| `/infra/job/create` | POST | 创建任务 | infra:job:create |
| `/infra/job/update` | PUT | 更新任务 | infra:job:update |
| `/infra/job/delete` | DELETE | 删除任务 | infra:job:delete |
| `/infra/job/update-status` | PUT | 更新任务状态 | infra:job:update |
| `/infra/job-log/list` | GET | 任务日志列表 | infra:job-log:query |
| `/infra/api-access-log/list` | GET | 访问日志列表 | infra:api-access-log:query |
| `/infra/api-access-log/export` | GET | 导出访问日志 | infra:api-access-log:export |
| `/infra/api-error-log/list` | GET | 异常日志列表 | infra:api-error-log:query |
| `/infra/api-error-log/update-status` | PUT | 更新异常处理状态 | infra:api-error-log:update |
| `/infra/api-error-log/export` | GET | 导出异常日志 | infra:api-error-log:export |
| `/infra/codegen/table/list` | GET | 代码生成表列表 | infra:codegen:query |
| `/infra/codegen/table/create` | POST | 导入表结构 | infra:codegen:create |
| `/infra/codegen/table/update` | PUT | 更新表配置 | infra:codegen:update |
| `/infra/codegen/table/preview` | GET | 预览生成代码 | infra:codegen:query |
| `/infra/codegen/table/download` | GET | 下载生成代码 | infra:codegen:download |
| `/infra/db/list` | GET | 数据源列表 | infra:db:query |
| `/infra/db/create` | POST | 创建数据源 | infra:db:create |
| `/infra/redis/get-info` | GET | Redis 监控信息 | infra:redis:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| infra_file_config | 文件配置表 | BaseDO | name, storage, master, config(JSON) |
| infra_file | 文件表 | BaseDO | config_id, name, path, url, type, size |
| infra_file_content | 文件内容表（数据库存储） | BaseDO | config_id, path, content(LONGBLOB) |
| infra_codegen_table | 代码生成表定义 | BaseDO | table_name, module_name, business_name, template_type, front_type |
| infra_codegen_column | 代码生成列定义 | BaseDO | table_id, column_name, java_type, java_field, dict_type |
| infra_job | 定时任务表 | BaseDO | name, status, handler_name, cron_expression, retry_count |
| infra_job_log | 定时任务日志表 | BaseDO | job_id, handler_name, begin_time, end_time, duration, status |
| infra_api_access_log | API访问日志表 | BaseDO | trace_id, user_id, request_url, duration, result_code |
| infra_api_error_log | API异常日志表 | BaseDO | trace_id, exception_name, exception_message, process_status |
| infra_config | 参数配置表 | BaseDO | category, name, config_key, value, type |
| infra_data_source_config | 数据源配置表 | BaseDO | name, url, username, password(加密) |

## 设计模式

- **策略模式 + 工厂模式**: 文件存储采用策略模式，通过 FileClientFactory 创建不同的 FileClient 实现，支持本地、S3、FTP、SFTP、数据库等多种存储方式
- **模板方法模式**: AbstractFileClient 抽象类定义文件客户端的通用流程，子类实现具体的 doInit() 初始化逻辑
- **Builder 模式**: CodegenBuilder 负责构建代码生成的表和列定义对象，CodegenEngine 负责执行代码生成
- **模板引擎模式**: 代码生成使用 Velocity 模板引擎，支持自定义模板扩展
- **缓存模式**: FileClient 使用 Guava LoadingCache 实现 10 秒异步刷新，避免频繁查询数据库
- **多态配置**: FileClientConfig 使用 Jackson @JsonTypeInfo 实现多态序列化，配置类与存储类型一一对应

## 依赖关系

### 内部依赖

| 模块 | 用途 |
|-----|------|
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |
| yudao-framework-quartz | Quartz 封装、JobHandler、SchedulerManager |
| yudao-framework-tenant | 租户支持、@TenantIgnore |

### 外部依赖

| 库 | 用途 |
|---|------|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| Quartz | 定时任务调度框架 |
| Velocity | 模板引擎，用于代码生成 |
| Hutool | Java 工具类库 |
| Guava | Google 工具库，使用 Cache、Table 等 |
| MinIO/S3 SDK | 对象存储客户端 |
| Swagger/OpenAPI | API 文档注解 |

## 模块间通信

| 接口 | 方法 | 说明 | 调用方 |
|-----|------|------|-------|
| FileApi | createFile() | 其他模块调用上传文件，返回文件 URL | yudao-module-system（用户头像）、yudao-module-member（会员头像） |
| FileApi | presignGetUrl() | 获取文件预签名访问地址 | 所有模块 |
| ConfigApi | getConfigValueByKey() | 其他模块获取系统配置值 | 所有模块 |
| WebSocketSenderApi | send() | 发送 WebSocket 消息 | 需要推送的模块 |

## 详细文档

- [api-file.md](api-file.md) - 文件管理接口
- [api-config.md](api-config.md) - 配置管理接口
- [api-job.md](api-job.md) - 定时任务接口
- [api-log.md](api-log.md) - 日志管理接口
- [api-codegen.md](api-codegen.md) - 代码生成接口
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项
