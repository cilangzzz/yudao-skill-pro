# 基础设施模块 (infra)

> 提供平台级基础设施运维能力（参数配置、文件存储、定时任务、API 日志、Redis 监控）与研发效率工具（代码生成器、数据源管理），是所有业务模块的公共底座。

## 模块概述

- **模块路径**: `yudao-module-infra`（单模块布局，无子模块）
- **业务定位**: 一方面承载基础设施的运维与管理，支撑上层通用与核心业务，例如参数配置、文件存储、定时任务、API 访问/错误日志；另一方面提供研发工具提升效率与质量，例如代码生成器、数据库表结构浏览、多数据源配置。
- **技术栈**: Spring Boot 2.7.18（JDK8 分支，`javax.*` 命名空间）/ MyBatis-Plus + mybatis-plus-generator（解析表结构）/ Quartz（定时任务）/ Velocity（代码生成模板）/ AWS S3 SDK（S3 文件存储）/ commons-net + jsch（FTP/SFTP）/ Spring Boot Admin（监控）/ Redis

## 设计原则

| 原则 | 说明 |
|------|------|
| 全局数据 | 绝大多数 infra 表标注 `@TenantIgnore`，跨租户共享（代码生成、参数、数据源、文件配置、任务等），DO 均继承 `BaseDO` 而非 `TenantBaseDO` |
| 存储器可插拔 | 文件客户端抽象为 `FileClient` 接口，DB/本地/FTP/SFTP/S3 五种实现经工厂按配置创建，支持 Master 主配置热切换 |
| 模板驱动生成 | 代码生成器以数据库真实表结构为输入，经 `CodegenBuilder` 构建、`CodegenEngine` 用 Velocity 渲染，覆盖后端 + Vue 前端 + SQL |
| DB 与调度器双写 | 定时任务同时维护 `infra_job` 表与 Quartz Scheduler，提供 `sync` 接口全量对齐两者 |
| 日志双轨 + 自动清理 | API 访问日志与错误日志分离，通过 `traceId` 串联排错；内置 `AccessLogCleanJob`、`ErrorLogCleanJob`、`JobLogCleanJob` 定期清理 |
| 能力单向输出 | 对外仅通过 `api` 包（`FileApi`/`ConfigApi`/`WebSocketSenderApi`）暴露能力，自身不反向依赖任何业务模块 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|--------|------|----------|
| 代码生成 | 导入数据库表结构 → 编辑表/字段定义 → 预览/下载生成代码（后端、前端、SQL），支持单表/树表/主子表模板 | CodegenTableDO、CodegenColumnDO |
| 参数配置 | 系统参数的键值管理，支持系统内置/自定义类型、可见性控制、按 key 查询 | ConfigDO |
| 数据源配置 | 多数据源连接配置（密码加密存储），供代码生成器读取任意库的表结构 | DataSourceConfigDO |
| 代码生成示例 | 生成器的标准产物示例：单表（demo01）、树表（demo02）、主子表（demo03 的 normal/inner/erp 三种关联方式） | Demo01ContactDO、Demo02CategoryDO、Demo03StudentDO 等 |
| 文件服务 | 文件上传/下载/预签名上传，存储配置管理（DB/本地/FTP/SFTP/S3），文件内容可落库 | FileDO、FileConfigDO、FileContentDO |
| 定时任务 | Quartz 任务管理（创建/启停/触发/同步）、执行日志查询与导出 | JobDO、JobLogDO |
| API 日志 | API 访问日志与错误日志的查询、错误处理状态流转、Excel 导出 | ApiAccessLogDO、ApiErrorLogDO |
| Redis 监控 | 读取 Redis INFO 统计与命令统计，返回监控视图数据 | 无（直连 RedisTemplate） |

## API 接口索引

### 代码生成器 (CodegenController)

前缀：`/infra/codegen`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/codegen/db/table/list | GET | 获得数据库自带的表定义列表（过滤已导入的表） | infra:codegen:query |
| /infra/codegen/table/list | GET | 获得表定义列表 | infra:codegen:query |
| /infra/codegen/table/page | GET | 获得表定义分页 | infra:codegen:query |
| /infra/codegen/detail | GET | 获得表和字段的明细 | infra:codegen:query |
| /infra/codegen/create-list | POST | 基于数据库表结构，创建代码生成的表和字段定义 | infra:codegen:create |
| /infra/codegen/update | PUT | 更新表和字段定义 | infra:codegen:update |
| /infra/codegen/sync-from-db | PUT | 基于数据库表结构，同步表和字段定义 | infra:codegen:update |
| /infra/codegen/delete | DELETE | 删除表和字段定义 | infra:codegen:delete |
| /infra/codegen/delete-list | DELETE | 批量删除表和字段定义 | infra:codegen:delete |
| /infra/codegen/preview | GET | 预览生成代码 | infra:codegen:preview |
| /infra/codegen/download | GET | 下载生成代码（zip） | infra:codegen:download |

### 参数配置 (ConfigController)

前缀：`/infra/config`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/config/create | POST | 创建参数配置 | infra:config:create |
| /infra/config/update | PUT | 修改参数配置 | infra:config:update |
| /infra/config/delete | DELETE | 删除参数配置 | infra:config:delete |
| /infra/config/delete-list | DELETE | 批量删除参数配置 | infra:config:delete |
| /infra/config/get | GET | 获得参数配置 | infra:config:query |
| /infra/config/get-value-by-key | GET | 根据参数键名查询参数值（不可见配置拒绝返回） | 已认证 |
| /infra/config/page | GET | 获取参数配置分页 | infra:config:query |
| /infra/config/export-excel | GET | 导出参数配置 | infra:config:export |

### 数据源配置 (DataSourceConfigController)

前缀：`/infra/data-source-config`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/data-source-config/create | POST | 创建数据源配置 | infra:data-source-config:create |
| /infra/data-source-config/update | PUT | 更新数据源配置 | infra:data-source-config:update |
| /infra/data-source-config/delete | DELETE | 删除数据源配置 | infra:data-source-config:delete |
| /infra/data-source-config/delete-list | DELETE | 批量删除数据源配置 | infra:data-source-config:delete |
| /infra/data-source-config/get | GET | 获得数据源配置 | infra:data-source-config:query |
| /infra/data-source-config/list | GET | 获得数据源配置列表 | infra:data-source-config:query |

### 文件存储 (FileController)

前缀：`/infra/file`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/file/upload | POST | 上传文件（模式一：后端上传） | 已认证 |
| /infra/file/presigned-url | GET | 获取文件预签名上传地址（模式二：前端直传 OSS） | 已认证 |
| /infra/file/create | POST | 创建文件记录（配合预签名接口） | 已认证 |
| /infra/file/get | GET | 获得文件 | infra:file:query |
| /infra/file/delete | DELETE | 删除文件 | infra:file:delete |
| /infra/file/delete-list | DELETE | 批量删除文件 | infra:file:delete |
| /infra/file/{configId}/get/** | GET | 下载文件（按存储配置 + 路径） | @PermitAll（另 @TenantIgnore，SecurityConfiguration 中放行） |
| /infra/file/page | GET | 获得文件分页 | infra:file:query |

### 文件配置 (FileConfigController)

前缀：`/infra/file-config`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/file-config/create | POST | 创建文件配置 | infra:file-config:create |
| /infra/file-config/update | PUT | 更新文件配置 | infra:file-config:update |
| /infra/file-config/update-master | PUT | 更新文件配置为 Master | infra:file-config:update |
| /infra/file-config/delete | DELETE | 删除文件配置（主配置禁止删除） | infra:file-config:delete |
| /infra/file-config/delete-list | DELETE | 批量删除文件配置 | infra:file-config:delete |
| /infra/file-config/get | GET | 获得文件配置 | infra:file-config:query |
| /infra/file-config/page | GET | 获得文件配置分页 | infra:file-config:query |
| /infra/file-config/test | GET | 测试文件配置是否正确 | infra:file-config:query |

### 定时任务 (JobController)

前缀：`/infra/job`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/job/create | POST | 创建定时任务 | infra:job:create |
| /infra/job/update | PUT | 更新定时任务 | infra:job:update |
| /infra/job/update-status | PUT | 更新定时任务的状态（开启/暂停） | infra:job:update |
| /infra/job/delete | DELETE | 删除定时任务 | infra:job:delete |
| /infra/job/delete-list | DELETE | 批量删除定时任务 | infra:job:delete |
| /infra/job/trigger | PUT | 触发定时任务（立即执行一次） | infra:job:trigger |
| /infra/job/sync | POST | 同步定时任务（数据库与 Quartz 集群对齐） | infra:job:create |
| /infra/job/get | GET | 获得定时任务 | infra:job:query |
| /infra/job/page | GET | 获得定时任务分页 | infra:job:query |
| /infra/job/export-excel | GET | 导出定时任务 Excel | infra:job:export |
| /infra/job/get_next_times | GET | 获得定时任务的下 n 次执行时间 | infra:job:query |

### 定时任务日志 (JobLogController)

前缀：`/infra/job-log`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/job-log/get | GET | 获得定时任务日志 | infra:job:query |
| /infra/job-log/page | GET | 获得定时任务日志分页 | infra:job:query |
| /infra/job-log/export-excel | GET | 导出定时任务日志 Excel | infra:job:export |

### API 访问日志 (ApiAccessLogController)

前缀：`/infra/api-access-log`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/api-access-log/get | GET | 获得 API 访问日志 | infra:api-access-log:query |
| /infra/api-access-log/page | GET | 获得 API 访问日志分页 | infra:api-access-log:query |
| /infra/api-access-log/export-excel | GET | 导出 API 访问日志 Excel | infra:api-access-log:export |

### API 错误日志 (ApiErrorLogController)

前缀：`/infra/api-error-log`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/api-error-log/update-status | PUT | 更新 API 错误日志的处理状态 | infra:api-error-log:update-status |
| /infra/api-error-log/get | GET | 获得 API 错误日志 | infra:api-error-log:query |
| /infra/api-error-log/page | GET | 获得 API 错误日志分页 | infra:api-error-log:query |
| /infra/api-error-log/export-excel | GET | 导出 API 错误日志 Excel | infra:api-error-log:export |

### Redis 监控 (RedisController)

前缀：`/infra/redis`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/redis/get-monitor-info | GET | 获得 Redis 监控信息（INFO 统计 + 命令统计） | infra:redis:get-monitor-info |

### 示例联系人（单表示例） (Demo01ContactController)

前缀：`/infra/demo01-contact`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/demo01-contact/create | POST | 创建示例联系人 | infra:demo01-contact:create |
| /infra/demo01-contact/update | PUT | 更新示例联系人 | infra:demo01-contact:update |
| /infra/demo01-contact/delete | DELETE | 删除示例联系人 | infra:demo01-contact:delete |
| /infra/demo01-contact/delete-list | DELETE | 批量删除示例联系人 | infra:demo01-contact:delete |
| /infra/demo01-contact/get | GET | 获得示例联系人 | infra:demo01-contact:query |
| /infra/demo01-contact/page | GET | 获得示例联系人分页 | infra:demo01-contact:query |
| /infra/demo01-contact/export-excel | GET | 导出示例联系人 Excel | infra:demo01-contact:export |

### 示例分类（树表示例） (Demo02CategoryController)

前缀：`/infra/demo02-category`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/demo02-category/create | POST | 创建示例分类 | infra:demo02-category:create |
| /infra/demo02-category/update | PUT | 更新示例分类 | infra:demo02-category:update |
| /infra/demo02-category/delete | DELETE | 删除示例分类 | infra:demo02-category:delete |
| /infra/demo02-category/get | GET | 获得示例分类 | infra:demo02-category:query |
| /infra/demo02-category/list | GET | 获得示例分类列表 | infra:demo02-category:query |
| /infra/demo02-category/export-excel | GET | 导出示例分类 Excel | infra:demo02-category:export |

### 示例学生（主子表示例 - ERP 风格） (Demo03StudentErpController)

前缀：`/infra/demo03-student-erp`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/demo03-student-erp/create | POST | 创建学生（含子表数据） | infra:demo03-student:create |
| /infra/demo03-student-erp/update | PUT | 更新学生 | infra:demo03-student:update |
| /infra/demo03-student-erp/delete | DELETE | 删除学生 | infra:demo03-student:delete |
| /infra/demo03-student-erp/delete-list | DELETE | 批量删除学生 | infra:demo03-student:delete |
| /infra/demo03-student-erp/get | GET | 获得学生 | infra:demo03-student:query |
| /infra/demo03-student-erp/page | GET | 获得学生分页 | infra:demo03-student:query |
| /infra/demo03-student-erp/export-excel | GET | 导出学生 Excel | infra:demo03-student:export |
| /infra/demo03-student-erp/demo03-course/page | GET | 获得学生课程分页（子表） | infra:demo03-student:query |
| /infra/demo03-student-erp/demo03-course/create | POST | 创建学生课程 | infra:demo03-student:create |
| /infra/demo03-student-erp/demo03-course/update | PUT | 更新学生课程 | infra:demo03-student:update |
| /infra/demo03-student-erp/demo03-course/delete | DELETE | 删除学生课程 | infra:demo03-student:delete |
| /infra/demo03-student-erp/demo03-course/delete-list | DELETE | 批量删除学生课程 | infra:demo03-student:delete |
| /infra/demo03-student-erp/demo03-course/get | GET | 获得学生课程 | infra:demo03-student:query |
| /infra/demo03-student-erp/demo03-grade/page | GET | 获得学生班级分页（子表） | infra:demo03-student:query |
| /infra/demo03-student-erp/demo03-grade/create | POST | 创建学生班级 | infra:demo03-student:create |
| /infra/demo03-student-erp/demo03-grade/update | PUT | 更新学生班级 | infra:demo03-student:update |
| /infra/demo03-student-erp/demo03-grade/delete | DELETE | 删除学生班级 | infra:demo03-student:delete |
| /infra/demo03-student-erp/demo03-grade/delete-list | DELETE | 批量删除学生班级 | infra:demo03-student:delete |
| /infra/demo03-student-erp/demo03-grade/get | GET | 获得学生班级 | infra:demo03-student:query |

### 示例学生（主子表示例 - 内嵌风格） (Demo03StudentInnerController)

前缀：`/infra/demo03-student-inner`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/demo03-student-inner/create | POST | 创建学生 | infra:demo03-student:create |
| /infra/demo03-student-inner/update | PUT | 更新学生 | infra:demo03-student:update |
| /infra/demo03-student-inner/delete | DELETE | 删除学生 | infra:demo03-student:delete |
| /infra/demo03-student-inner/delete-list | DELETE | 批量删除学生 | infra:demo03-student:delete |
| /infra/demo03-student-inner/get | GET | 获得学生 | infra:demo03-student:query |
| /infra/demo03-student-inner/page | GET | 获得学生分页 | infra:demo03-student:query |
| /infra/demo03-student-inner/export-excel | GET | 导出学生 Excel | infra:demo03-student:export |
| /infra/demo03-student-inner/demo03-course/list-by-student-id | GET | 获得学生课程列表（子表） | infra:demo03-student:query |
| /infra/demo03-student-inner/demo03-grade/get-by-student-id | GET | 获得学生班级（子表） | infra:demo03-student:query |

### 示例学生（主子表示例 - 常规风格） (Demo03StudentNormalController)

前缀：`/infra/demo03-student-normal`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /infra/demo03-student-normal/create | POST | 创建学生 | infra:demo03-student:create |
| /infra/demo03-student-normal/update | PUT | 更新学生 | infra:demo03-student:update |
| /infra/demo03-student-normal/delete | DELETE | 删除学生 | infra:demo03-student:delete |
| /infra/demo03-student-normal/delete-list | DELETE | 批量删除学生 | infra:demo03-student:delete |
| /infra/demo03-student-normal/get | GET | 获得学生 | infra:demo03-student:query |
| /infra/demo03-student-normal/page | GET | 获得学生分页 | infra:demo03-student:query |
| /infra/demo03-student-normal/export-excel | GET | 导出学生 Excel | infra:demo03-student:export |
| /infra/demo03-student-normal/demo03-course/list-by-student-id | GET | 获得学生课程列表（子表） | infra:demo03-student:query |
| /infra/demo03-student-normal/demo03-grade/get-by-student-id | GET | 获得学生班级（子表） | infra:demo03-student:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| infra_codegen_table | 代码生成的表定义 | BaseDO（@TenantIgnore） | data_source_config_id, table_name, table_comment, scene, template_type, front_type |
| infra_codegen_column | 代码生成的字段定义 | BaseDO（@TenantIgnore） | table_id, column_name, data_type, column_comment, html_type, query_condition |
| infra_config | 参数配置表 | BaseDO（@TenantIgnore） | category, name, config_key, value, type, visible |
| infra_data_source_config | 数据源配置 | BaseDO（@TenantIgnore） | name, url, username, password（EncryptTypeHandler 加密存储） |
| infra_file | 文件信息 | BaseDO | config_id, name, path, url, type, size |
| infra_file_config | 文件存储配置 | BaseDO | name, storage（FileStorageEnum）, master, config（FileClientConfig JSON，autoResultMap） |
| infra_file_content | 文件内容（DB 存储模式专用） | BaseDO | config_id, path, content（byte[]） |
| infra_job | 定时任务 | BaseDO | name, status, handler_name, handler_param, cron_expression, retry_count, retry_interval, monitor_timeout |
| infra_job_log | 定时任务执行日志 | BaseDO | job_id, handler_name, handler_param, execute_index, begin_time, duration, status, result |
| infra_api_access_log | API 访问日志 | BaseDO | trace_id, user_id, user_type, request_url, request_params, operate_module, operate_type, duration, result_code |
| infra_api_error_log | API 错误日志 | BaseDO | trace_id, user_id, request_url, exception_name, exception_stack_trace, process_status, process_user_id |
| yudao_demo01_contact | 示例联系人（单表代码生成示例） | BaseDO | name, sex, birthday, description |
| yudao_demo02_category | 示例分类（树表代码生成示例） | BaseDO | name, parent_id |
| yudao_demo03_student | 示例学生（主子表示例 - 主表） | BaseDO | name, sex, birthday, description |
| yudao_demo03_course | 学生课程（主子表示例 - 子表） | BaseDO | student_id, name, score |
| yudao_demo03_grade | 学生班级（主子表示例 - 子表） | BaseDO | student_id, name, teacher |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|----------|------|
| 策略模式 + 工厂模式 | `framework/file/core/client/`：`FileClient` 接口 + `DBFileClient`/`LocalFileClient`/`FtpFileClient`/`SftpFileClient`/`S3FileClient` 五种实现；`FileClientFactoryImpl` 按 `FileStorageEnum` 创建客户端 | 文件存储器可插拔，按配置切换 DB/本地/FTP/SFTP/S3 存储 |
| 模板方法模式 | `AbstractFileClient#init()` 为 final 模板方法，子类实现 `doInit()` 抽象方法 | 统一文件客户端的初始化流程与配置变更判断 |
| 模板引擎 + 构建器 | `service/codegen/inner/CodegenBuilder`（数据库表 → 代码生成定义）与 `CodegenEngine`（Velocity 渲染全部前后端模板，支持单表/树表/主子表 `CodegenTemplateTypeEnum`） | 代码生成管道：解析表结构、构建元数据、按模板类型渲染输出 |

## 依赖关系

- **上游**（本模块依赖）:
  - framework starters: `yudao-spring-boot-starter-biz-tenant`（多租户）、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-websocket`、`yudao-spring-boot-starter-mybatis`（+ `mybatis-plus-generator` 解析表结构）、`yudao-spring-boot-starter-redis`、`yudao-spring-boot-starter-job`（Quartz）、`yudao-spring-boot-starter-mq`、`yudao-spring-boot-starter-excel`、`yudao-spring-boot-starter-monitor`（+ spring-boot-admin-server）、`yudao-spring-boot-starter-test`（test）
  - 三方库: `velocity-engine-core`（代码生成模板）、`commons-net`（FTP）、`jsch`（SFTP）、`software.amazon.awssdk:s3`（S3/OSS/MinIO）、`tika-core`（文件类型识别）
  - 业务模块: 无（不依赖任何其他业务模块）

- **下游**（依赖本模块）:
  - pom 依赖 `yudao-module-infra`: `yudao-module-system`、`yudao-module-member`、`yudao-module-mall/yudao-module-promotion`、`yudao-module-crm`、`yudao-module-mp`、`yudao-module-im`、`yudao-module-ai`、`yudao-module-oa`、`yudao-module-pms`、`yudao-module-fms`、`yudao-server`

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|---------|------|--------|
| `api/file/FileApi` | createFile（byte[]/名称/目录/类型）、presignGetUrl | system、ai、mp、oa、pms、fms |
| `api/config/ConfigApi` | getConfigValueByKey | system |
| `api/websocket/WebSocketSenderApi` | send / sendObject（向用户、用户类型、Session 推送 WebSocket 消息） | system、im、mall/promotion |
| `ApiAccessLogCommonApi` / `ApiErrorLogCommonApi`（framework common-biz 接口，本模块实现于 `api/logger/`） | createApiAccessLog / createApiErrorLog | apilog 框架组件（API 日志自动记录链路） |

## 详细文档

- [api-codegen.md](api-codegen.md) - 代码生成
- [api-config.md](api-config.md) - 参数配置
- [api-db.md](api-db.md) - 数据源配置
- [api-demo.md](api-demo.md) - 代码生成示例
- [api-file.md](api-file.md) - 文件服务
- [api-job.md](api-job.md) - 定时任务
- [api-logger.md](api-logger.md) - API 日志
- [api-redis.md](api-redis.md) - Redis 监控
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
