# 数据模型详情

> infra 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。infra 模块提供平台级基础设施运维能力（参数配置、文件存储、定时任务、API 日志）与研发效率工具（代码生成器、多数据源管理），共 16 张数据表。
>
> 说明：当前仓库为 JDK8 分支（revision 2026.09-jdk8-SNAPSHOT，Spring Boot 2.7.18），文档中的类型与注解均以实际代码为准。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类）
│   creator       String          创建者（用户编号，INSERT 时自动填充）
│   createTime    LocalDateTime   创建时间（INSERT 时自动填充）
│   updater       String          更新者（INSERT/UPDATE 时自动填充）
│   updateTime    LocalDateTime   最后更新时间（INSERT/UPDATE 时自动填充）
│   deleted       Boolean         逻辑删除标记（@TableLogic）
│
├── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO（多租户基类）
│   │   tenantId   Long            多租户编号（由租户拦截器自动填充与过滤）
│   │
│   └──（infra 模块暂无 DO 直接继承该基类）
│
└── infra 模块 16 个 DO 全部直接继承 BaseDO，按租户策略分为两类：

    【全局表，@TenantIgnore 标注（9 个）】
    CodegenTableDO / CodegenColumnDO        代码生成器（研发工具，租户无关）
    ConfigDO / DataSourceConfigDO            平台级参数与数据源配置
    FileConfigDO / FileDO / FileContentDO    文件存储（配置与文件元数据/内容）
    JobDO / JobLogDO                         Quartz 定时任务（Quartz 表本身无租户概念）

    【租户表，未标注 @TenantIgnore（7 个）】
    ApiAccessLogDO / ApiErrorLogDO           API 访问/异常日志（按租户隔离记录）
    Demo01ContactDO / Demo02CategoryDO /     代码生成器示例表
    Demo03StudentDO / Demo03CourseDO / Demo03GradeDO
```

**使用规则**：

- **BaseDO**：所有 DO 的公共基类，提供审计字段（creator/createTime/updater/updateTime）与逻辑删除（deleted）。字段值由 MyBatis-Plus 的 `FieldFill` 机制自动填充，业务代码不应手工设置（DO 提供 `clean()` 方法清空，防止前端注入）。
- **TenantBaseDO**：显式带 `tenantId` 字段的业务实体使用，infra 模块当前没有直接使用方。
- **@TenantIgnore（标注在 DO 类上）**：`TenantDatabaseInterceptor` 通过 MyBatis-Plus TableInfo 读取该注解，将对应表视为全局表，SQL 不追加 `WHERE tenant_id = ?` 过滤。适用于平台级配置、代码生成、定时任务、文件等租户无关数据。
- **未标注 @TenantIgnore 的 BaseDO 子类**（如两个日志 DO 与 5 个 demo DO）：DO 中虽无 `tenantId` 字段，但表结构含 `tenant_id` 列，由租户拦截器（TenantLineInnerInterceptor）在 INSERT 时自动填充、SELECT 时自动过滤，实现租户隔离。

## 2. 核心 DO 实体

### 2.1 代码生成聚合（codegen）

代码生成器的元数据表，读取数据库表结构（经 `DatabaseTableService`）后落库，再由 CodegenBuilder/CodegenEngine 基于 Velocity 模板生成代码，支持单表/树表/主子表三种 `CodegenTemplateTypeEnum` 模板。

#### CodegenTableDO (infra_codegen_table)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键编号 |
| dataSourceConfigId | Long | data_source_config_id | 数据源编号，关联 DataSourceConfigDO.id |
| scene | Integer | scene | 生成场景，枚举 CodegenSceneEnum（管理后台 / 用户 App） |
| tableName | String | table_name | 表名称 |
| tableComment | String | table_comment | 表描述 |
| remark | String | remark | 备注 |
| moduleName | String | module_name | 模块名（一级目录，如 system、infra） |
| businessName | String | business_name | 业务名（二级目录，如 user、dict） |
| className | String | class_name | 类名称（首字母大写） |
| classComment | String | class_comment | 类描述 |
| author | String | author | 作者 |
| templateType | Integer | template_type | 模板类型，枚举 CodegenTemplateTypeEnum：1 单表 / 2 树表 / 10、11、12 主子表主表（普通、ERP、内嵌）/ 15 子表 |
| frontType | Integer | front_type | 前端代码类型，枚举 CodegenFrontTypeEnum |
| parentMenuId | Long | parent_menu_id | 父菜单编号，关联 system 模块 MenuDO.id |
| masterTableId | Long | master_table_id | 主子表场景的主表编号，关联 CodegenTableDO.id |
| subJoinColumnId | Long | sub_join_column_id | 子表关联主表的字段编号，关联 CodegenColumnDO.id |
| subJoinMany | Boolean | sub_join_many | 主表与子表是否一对多（true 一对多 / false 一对一） |
| treeParentColumnId | Long | tree_parent_column_id | 树表的父字段编号，关联 CodegenColumnDO.id |
| treeNameColumnId | Long | tree_name_column_id | 树表的名字字段编号（下拉框展示用），关联 CodegenColumnDO.id |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引（数据量小，按主键/全量查询）
**特性**: `@TenantIgnore` 全局表；`autoResultMap = true`；`@KeySequence("infra_codegen_table_seq")` 兼容 Oracle/PostgreSQL 等非自增数据库。

#### CodegenColumnDO (infra_codegen_column)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键编号 |
| tableId | Long | table_id | 表编号，关联 CodegenTableDO.id |
| columnName | String | column_name | 字段名（数据库列名） |
| dataType | String | data_type | 数据库字段类型（JDBC 类型） |
| columnComment | String | column_comment | 字段描述 |
| nullable | Boolean | nullable | 是否允许为空 |
| primaryKey | Boolean | primary_key | 是否主键 |
| ordinalPosition | Integer | ordinal_position | 字段排序 |
| javaType | String | java_type | Java 属性类型（如 String、Boolean） |
| javaField | String | java_field | Java 属性名 |
| dictType | String | dict_type | 字典类型，关联 system 模块 DictTypeDO.type |
| example | String | example | 数据示例（生成 Swagger @Schema example 用） |
| createOperation | Boolean | create_operation | 是否为 Create 操作的字段 |
| updateOperation | Boolean | update_operation | 是否为 Update 操作的字段 |
| listOperation | Boolean | list_operation | 是否为 List 查询条件字段 |
| listOperationCondition | String | list_operation_condition | 查询条件类型，枚举 CodegenColumnListConditionEnum（=、LIKE 等） |
| listOperationResult | Boolean | list_operation_result | 是否为 List 查询的返回字段 |
| htmlType | String | html_type | UI 显示类型，枚举 CodegenColumnHtmlTypeEnum（input、textarea、select 等） |

**继承**: BaseDO
**索引**: 主键 `id`；普通索引 `idx_table_id(table_id)` —— 按表编号加载一张表的全部字段定义。
**特性**: `@TenantIgnore` 全局表；一张代码生成表对应多条字段记录，是 CodegenEngine 生成 DO/VO/Mapper/Service/Controller 的字段级元数据来源。

### 2.2 参数配置与数据源（config / db）

#### ConfigDO (infra_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 参数主键 |
| category | String | category | 参数分类（分组） |
| name | String | name | 参数名称 |
| configKey | String | config_key | 参数键名（如 `system.user.init-password`），业务方经 ConfigApi 按键读取 |
| value | String | value | 参数键值 |
| type | Integer | type | 参数类型，枚举 ConfigTypeEnum：1 系统内置（不可删改）/ 2 自定义 |
| visible | Boolean | visible | 是否可见（false 为敏感参数，前端不可获取） |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 `id`；普通索引 `idx_config_key(config_key)` —— 支撑按 key 的 `getConfigValueByKey` 高频查询。
**特性**: `@TenantIgnore` 全局表；经 ConfigApi 供 system 等模块消费；本仓库中亦承载各业务模块（EAM/CMS 等）的业务编号生成规则配置。

#### DataSourceConfigDO (infra_data_source_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键编号；常量 ID_MASTER = 0 代表 Master 主数据源 |
| name | String | name | 连接名 |
| url | String | url | 数据源 JDBC 连接串 |
| username | String | username | 用户名 |
| password | String | password | 密码（@TableField(typeHandler = EncryptTypeHandler) 加密存储） |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: `@TenantIgnore` 全局表；`autoResultMap = true`；是动态多数据源（dynamic-datasource）与代码生成器"从任意库读表结构"的基础；密码经 EncryptTypeHandler 落库加密。

### 2.3 文件存储聚合（file）

文件客户端采用**策略 + 工厂模式**：FileClientFactory 按 storage 类型创建 5 种 FileClient（DB / Local / FTP / SFTP / S3），AbstractFileClient 为模板方法基类；`config` 字段以 JSON 多态存储各客户端的差异化配置。

#### FileConfigDO (infra_file_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 配置编号，数据库自增 |
| name | String | name | 配置名 |
| storage | Integer | storage | 存储器，枚举 FileStorageEnum：1 DB / 10 本地 / 11 FTP / 12 SFTP / 20 S3 |
| remark | String | remark | 备注 |
| master | Boolean | master | 是否主配置（默认上传走主配置，全局仅一条 master=true） |
| config | FileClientConfig | config | 客户端配置，JSON 多态存储（DBFileClientConfig / LocalFileClientConfig / FtpFileClientConfig / SftpFileClientConfig / S3FileClientConfig），由内部 FileClientConfigTypeHandler 反序列化（含老版本 @class 包路径兼容逻辑） |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: `@TenantIgnore` 全局表；`autoResultMap = true` 配合自定义 TypeHandler 完成多态 JSON 映射。

#### FileDO (infra_file)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 文件编号，数据库自增 |
| configId | Long | config_id | 配置编号，关联 FileConfigDO.id |
| name | String | name | 原文件名 |
| path | String | path | 文件路径（即存储文件名） |
| url | String | url | 访问地址 |
| type | String | type | 文件 MIME 类型（如 application/octet-stream） |
| size | Long | size | 文件大小（字节） |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: `@TenantIgnore` 全局表；每次上传记录一条；`FileController` 的 `/{configId}/get/**` 访问路径为 @PermitAll + @TenantIgnore（SecurityConfiguration 放行），upload/presigned-url/create 仅需登录；经 FileApi 供 system/ai/mp/oa/pms/fms 等模块消费。

#### FileContentDO (infra_file_content)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，数据库自增 |
| configId | Long | config_id | 配置编号，关联 FileConfigDO.id |
| path | String | path | 文件路径（即文件名），与 FileDO.path 对应 |
| content | byte[] | content | 文件二进制内容（mediumblob），仅 DB 存储器（DBFileClient）写入 |

**继承**: BaseDO
**索引**: 主键 `id`；联合普通索引 `idx_config_id_path(config_id, path)` —— DB 存储器按"配置 + 路径"读取文件内容。
**特性**: `@TenantIgnore` 全局表；当存储器为 DB 时，文件元数据在 infra_file、文件内容在 infra_file_content，两表通过 path 关联。

### 2.4 定时任务聚合（job）

基于 Quartz 的任务管理，JobDO 为任务定义（与 Quartz 触发器状态双向同步），JobLogDO 为每次执行的日志。

#### JobDO (infra_job)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 任务编号 |
| name | String | name | 任务名称 |
| status | Integer | status | 任务状态，枚举 JobStatusEnum：0 初始化 / 1 开启 / 2 暂停（与 Quartz 触发器状态集合映射） |
| handlerName | String | handler_name | 处理器名字（对应 JobHandler 的 Bean 名，如 payNotifyJob） |
| handlerParam | String | handler_param | 处理器参数 |
| cronExpression | String | cron_expression | CRON 执行表达式 |
| retryCount | Integer | retry_count | 重试次数（0 表示不重试） |
| retryInterval | Integer | retry_interval | 重试间隔（毫秒，0 表示无间隔） |
| monitorTimeout | Integer | monitor_timeout | 监控超时时间（毫秒，仅用于执行过长的告警，不取消任务；空/0 表示不监控） |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: `@TenantIgnore` 全局表；业务模块（pay/mall/iot/hrm/cms/oa/pms/eam 等）通过注册 JobHandler 在此表中登记定时任务。

#### JobLogDO (infra_job_log)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日志编号 |
| jobId | Long | job_id | 任务编号，关联 JobDO.id |
| handlerName | String | handler_name | 处理器名字（冗余 JobDO.handlerName） |
| handlerParam | String | handler_param | 处理器参数（冗余 JobDO.handlerParam） |
| executeIndex | Integer | execute_index | 第几次执行（>1 表示重试执行） |
| beginTime | LocalDateTime | begin_time | 开始执行时间 |
| endTime | LocalDateTime | end_time | 结束执行时间 |
| duration | Integer | duration | 执行时长（毫秒） |
| status | Integer | status | 执行状态，枚举 JobLogStatusEnum：0 运行中 / 1 成功 / 2 失败 |
| result | String | result | 结果数据（成功为 execute 返回值，失败为异常堆栈） |

**继承**: BaseDO
**索引**: 主键 `id`；普通索引 `idx_job_id(job_id)`（按任务查日志）、`idx_create_time(create_time)`（日志清理 Job 按时间清理）。
**特性**: `@TenantIgnore` 全局表；由 jobLogCleanJob 定期清理过期日志。

### 2.5 API 日志（logger）

由 framework 的 apilog 组件经 ApiAccessLogCommonApi / ApiErrorLogCommonApi 异步写入，infra 模块实现这两个 CommonApi 并提供管理端查询。两表均通过 traceId 串联访问日志、错误日志与链路追踪日志。两 DO 未标注 `@TenantIgnore`，表内 `tenant_id` 列由租户拦截器自动填充/过滤（DO 不显式映射该字段）。

#### ApiAccessLogDO (infra_api_access_log)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日志主键 |
| traceId | String | trace_id | 链路追踪编号（串联访问日志/错误日志/链路日志） |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum（管理员/会员） |
| applicationName | String | application_name | 应用名（读取 spring.application.name） |
| requestMethod | String | request_method | 请求方法名 |
| requestUrl | String | request_url | 请求地址 |
| requestParams | String | request_params | 请求参数（query + body），超长截断至 REQUEST_PARAMS_MAX_LENGTH = 8000 |
| responseBody | String | response_body | 响应结果 |
| userIp | String | user_ip | 用户 IP |
| userAgent | String | user_agent | 浏览器 UA |
| operateModule | String | operate_module | 操作模块（来自 @ApiAccessLog 注解） |
| operateName | String | operate_name | 操作名 |
| operateType | Integer | operate_type | 操作分类，枚举 OperateTypeEnum（CREATE/UPDATE/DELETE/GET 等） |
| beginTime | LocalDateTime | begin_time | 开始请求时间 |
| endTime | LocalDateTime | end_time | 结束请求时间 |
| duration | Integer | duration | 执行时长（毫秒） |
| resultCode | Integer | result_code | 结果码（CommonResult.code） |
| resultMsg | String | result_msg | 结果提示（CommonResult.msg），超长截断至 RESULT_MSG_MAX_LENGTH = 512 |

**继承**: BaseDO
**索引**: 主键 `id`；普通索引 `idx_create_time(create_time)` —— 支撑日志分页查询与 accessLogCleanJob 按时间清理。
**特性**: 租户表（表含 tenant_id，拦截器自动处理）；requestParams/responseBody 为 text 大字段。

#### ApiErrorLogDO (infra_api_error_log)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| userId | Long | user_id | 用户编号 |
| traceId | String | trace_id | 链路追踪编号 |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| applicationName | String | application_name | 应用名 |
| requestMethod | String | request_method | 请求方法名 |
| requestUrl | String | request_url | 请求地址 |
| requestParams | String | request_params | 请求参数，varchar(8000)，超长截断至 REQUEST_PARAMS_MAX_LENGTH = 8000 |
| userIp | String | user_ip | 用户 IP |
| userAgent | String | user_agent | 浏览器 UA |
| exceptionTime | LocalDateTime | exception_time | 异常发生时间 |
| exceptionName | String | exception_name | 异常名（Throwable 的类全名） |
| exceptionMessage | String | exception_message | 异常消息 |
| exceptionRootCauseMessage | String | exception_root_cause_message | 异常根因消息 |
| exceptionStackTrace | String | exception_stack_trace | 异常堆栈 |
| exceptionClassName | String | exception_class_name | 异常发生的类全名 |
| exceptionFileName | String | exception_file_name | 异常发生的类文件 |
| exceptionMethodName | String | exception_method_name | 异常发生的方法名 |
| exceptionLineNumber | Integer | exception_line_number | 异常发生的方法所在行 |
| processStatus | Integer | process_status | 处理状态，枚举 ApiErrorLogProcessStatusEnum：0 未处理 / 1 已处理 / 2 已忽略 |
| processTime | LocalDateTime | process_time | 处理时间 |
| processUserId | Long | process_user_id | 处理用户编号，关联 system 模块用户 |

**继承**: BaseDO
**索引**: 主键 `id`；普通索引 `idx_create_time(create_time)` —— 支撑分页查询与 errorLogCleanJob 按时间清理。
**特性**: 租户表（表含 tenant_id，拦截器自动处理）；"处理"动作（标记已处理/忽略）会更新 processStatus/processTime/processUserId。

### 2.6 代码生成示例（demo）

demo 域是代码生成器三种模板类型的标准产物示例，表前缀为 `yudao_`（非 `infra_`），全部继承 BaseDO、走租户隔离（表含 tenant_id，拦截器自动处理），错误码占用 1_001_201_000 段，权限统一为 `infra:demo03-student:*`。业务上无下游依赖，仅作生成效果演示与回归参照。

#### Demo01ContactDO (yudao_demo01_contact)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| name | String | name | 名字 |
| sex | Integer | sex | 性别（字典 system_user_sex） |
| birthday | LocalDateTime | birthday | 出生年 |
| description | String | description | 简介 |
| avatar | String | avatar | 头像（infra_file 的访问 URL） |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: 单表（增删改查）模板示例，演示富文本、字典、文件上传等常见字段。

#### Demo02CategoryDO (yudao_demo02_category)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| name | String | name | 名字 |
| parentId | Long | parent_id | 父级编号，关联本表 id；常量 PARENT_ID_ROOT = 0 表示根节点 |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: 树表（增删改查）模板示例，parentId 自关联构成树形结构。

#### Demo03StudentDO (yudao_demo03_student)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| name | String | name | 名字 |
| sex | Integer | sex | 性别（字典 system_user_sex） |
| birthday | LocalDateTime | birthday | 出生日期 |
| description | String | description | 简介 |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: 主子表模板的主表，关联两张子表演示普通/ERP/内嵌三种主子表风格。

#### Demo03CourseDO (yudao_demo03_course)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| studentId | Long | student_id | 学生编号，关联 Demo03StudentDO.id |
| name | String | name | 课程名字 |
| score | Integer | score | 分数 |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: 主子表模板的子表（独立 Tab 编辑风格，对应主表"普通模式"）。

#### Demo03GradeDO (yudao_demo03_grade)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| studentId | Long | student_id | 学生编号，关联 Demo03StudentDO.id |
| name | String | name | 班级名字 |
| teacher | String | teacher | 班主任 |

**继承**: BaseDO
**索引**: 主键 `id`；无二级索引
**特性**: 主子表模板的子表，演示 ERP 模式（类 Excel 联动编辑）与内嵌模式风格。

## 3. 实体关系

所有关联均为逻辑外键（无数据库 FOREIGN KEY 约束），通过字段冗余 + 应用层校验维护：

```
infra_data_source_config (1) ─────< infra_codegen_table (N)      data_source_config_id
                                        │  (1)
                                        └────────< infra_codegen_column (N)   table_id
                                        │
                                        ├─ masterTableId ────────> infra_codegen_table.id   （主子表：子表指回主表）
                                        ├─ subJoinColumnId ──────> infra_codegen_column.id  （子表关联主表的字段）
                                        ├─ treeParentColumnId ───> infra_codegen_column.id  （树表父字段）
                                        ├─ treeNameColumnId ─────> infra_codegen_column.id  （树表名字字段）
                                        └─ parentMenuId ─────────> system_menu.id           （跨模块：生成菜单挂载点）

infra_file_config (1) ─┬───────< infra_file (N)             config_id   文件元数据
                       └───────< infra_file_content (N)     config_id   DB 存储器的文件内容（path 与 infra_file.path 对应）

infra_job (1) ────────────────< infra_job_log (N)            job_id      任务执行日志

yudao_demo03_student (1) ─────< yudao_demo03_course (N)      student_id  主子表·普通模式
yudao_demo03_student (1) ─────< yudao_demo03_grade (N)       student_id  主子表·ERP/内嵌模式
yudao_demo02_category.parentId ──> yudao_demo02_category.id  树表自关联

infra_api_access_log ─┐
                      ├─ traceId 逻辑串联（无外键）；userId + userType 指向 system/ member 的用户
infra_api_error_log ──┘           processUserId ──> system 用户
```

**关系说明**：

- **codegen 三表链路** 是模块内最核心的聚合：DataSourceConfigDO 提供数据库连接 → CodegenTableDO 存表级配置 → CodegenColumnDO 存字段级配置；主子表/树表通过 masterTableId、subJoinColumnId、treeParentColumnId、treeNameColumnId 在 CodegenTable 内部自关联。
- **file 三表链路**：FileConfigDO 是配置中心，FileDO（元数据）与 FileContentDO（内容）都以 configId 指向它；FileDO 与 FileContentDO 通过相同的 path 对应同一条文件记录（仅 DB 存储器产生 FileContentDO 记录）。
- **job 两表链路**：JobLogDO 冗余了 handlerName/handlerParam，按 jobId 关联任务定义，用于执行历史回溯。
- **日志两表** 无模块内外键，以 traceId 跨日志类型串联排错；跨模块逻辑关联（parentMenuId → system_menu、dictType → system_dict_type、processUserId → system 用户）由应用层保证。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|----|------|
| infra_codegen_table | CodegenTableDO | 代码生成表定义（全局表） |
| infra_codegen_column | CodegenColumnDO | 代码生成表字段定义（全局表） |
| infra_config | ConfigDO | 参数配置表（全局表） |
| infra_data_source_config | DataSourceConfigDO | 数据源配置表（全局表，密码加密） |
| infra_file_config | FileConfigDO | 文件存储配置表（全局表，JSON 多态配置） |
| infra_file | FileDO | 文件表，上传记录元数据（全局表） |
| infra_file_content | FileContentDO | 文件内容表，DB 存储器专用（全局表） |
| infra_job | JobDO | 定时任务表（全局表） |
| infra_job_log | JobLogDO | 定时任务执行日志表（全局表） |
| infra_api_access_log | ApiAccessLogDO | API 访问日志表（租户表） |
| infra_api_error_log | ApiErrorLogDO | API 异常日志表（租户表） |
| yudao_demo01_contact | Demo01ContactDO | 示例联系人表，单表模板（租户表） |
| yudao_demo02_category | Demo02CategoryDO | 示例分类表，树表模板（租户表） |
| yudao_demo03_student | Demo03StudentDO | 学生表，主子表主表模板（租户表） |
| yudao_demo03_course | Demo03CourseDO | 学生课程表，主子表子表·普通模式（租户表） |
| yudao_demo03_grade | Demo03GradeDO | 学生班级表，主子表子表·ERP/内嵌模式（租户表） |
