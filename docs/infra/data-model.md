# 数据模型详情

## 实体继承体系

所有 DO 实体继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| creator | VARCHAR | 创建人 |
| createTime | DATETIME | 创建时间 |
| updater | VARCHAR | 更新人 |
| updateTime | DATETIME | 更新时间 |
| deleted | BIT | 是否删除（逻辑删除） |

> 大部分 infra 表使用 `@TenantIgnore` 注解，基础设施不参与租户隔离。

## 表关系总览

```
infra_file_config (文件配置)
    |
    | 1:N
    v
infra_file (文件记录)

infra_data_source_config (数据源配置)
    |
    | 1:N
    v
infra_codegen_table (代码生成表定义) --自关联--> infra_codegen_table (主子表关联)
    |
    | 1:N
    v
infra_codegen_column (代码生成列定义)

infra_job (定时任务)
    |
    | 1:N
    v
infra_job_log (任务执行日志)

infra_api_access_log (访问日志) -- 独立表
infra_api_error_log (异常日志) -- 独立表
infra_config (系统配置) -- 独立表
```

## 文件存储聚合

### infra_file_config（文件配置表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 配置编号 |
| name | VARCHAR | | 配置名称 |
| storage | TINYINT | | 存储器类型，枚举 FileStorageEnum |
| remark | VARCHAR | | 备注 |
| master | BIT | | 是否主配置 |
| config | JSON | | 存储配置，JSON 格式 |

**索引**: idx_master(master)

### infra_file（文件表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 文件编号 |
| config_id | BIGINT | FK -> infra_file_config.id | 配置编号 |
| name | VARCHAR | | 原文件名 |
| path | VARCHAR | | 文件路径 |
| url | VARCHAR | | 访问地址 |
| type | VARCHAR | | MIME 类型 |
| size | BIGINT | | 文件大小（字节） |

**索引**: idx_config_id(config_id)

### infra_file_content（文件内容表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 编号 |
| config_id | BIGINT | | 配置编号 |
| path | VARCHAR | | 文件路径 |
| content | LONGBLOB | | 文件内容 |

> 此表仅用于数据库存储方式，存储文件的二进制内容。

## 代码生成聚合

### infra_codegen_table（代码生成表定义）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 编号 |
| data_source_config_id | BIGINT | FK -> infra_data_source_config.id | 数据源编号 |
| scene | TINYINT | | 生成场景 |
| table_name | VARCHAR | | 表名称 |
| table_comment | VARCHAR | | 表描述 |
| remark | VARCHAR | | 备注 |
| module_name | VARCHAR | | 模块名 |
| business_name | VARCHAR | | 业务名 |
| class_name | VARCHAR | | 类名称 |
| class_comment | VARCHAR | | 类描述 |
| author | VARCHAR | | 作者 |
| template_type | TINYINT | | 模板类型 |
| front_type | TINYINT | | 前端类型 |
| parent_menu_id | BIGINT | | 父菜单编号 |
| master_table_id | BIGINT | FK -> infra_codegen_table.id | 主表编号（子表时使用） |
| sub_join_column_id | BIGINT | | 子表关联字段编号 |
| sub_join_many | BIT | | 是否一对多 |
| tree_parent_column_id | BIGINT | | 树表父字段编号 |
| tree_name_column_id | BIGINT | | 树表名称字段编号 |

### infra_codegen_column（代码生成列定义）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 编号 |
| table_id | BIGINT | FK -> infra_codegen_table.id | 表编号 |
| column_name | VARCHAR | | 字段名 |
| data_type | VARCHAR | | 数据库类型 |
| column_comment | VARCHAR | | 字段描述 |
| nullable | BIT | | 是否允许空 |
| primary_key | BIT | | 是否主键 |
| ordinal_position | INT | | 排序 |
| java_type | VARCHAR | | Java 类型 |
| java_field | VARCHAR | | Java 属性名 |
| dict_type | VARCHAR | | 字典类型 |
| example | VARCHAR | | 数据示例 |
| create_operation | BIT | | 是否 Create 操作字段 |
| update_operation | BIT | | 是否 Update 操作字段 |
| list_operation | BIT | | 是否 List 查询字段 |
| list_operation_condition | VARCHAR | | List 查询条件 |
| list_operation_result | BIT | | 是否 List 返回字段 |
| html_type | VARCHAR | | 显示类型 |

## 定时任务聚合

### infra_job（定时任务表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 任务编号 |
| name | VARCHAR | | 任务名称 |
| status | TINYINT | | 任务状态 |
| handler_name | VARCHAR | | 处理器名称 |
| handler_param | VARCHAR | | 处理器参数 |
| cron_expression | VARCHAR | | CRON 表达式 |
| retry_count | INT | | 重试次数 |
| retry_interval | INT | | 重试间隔（毫秒） |
| monitor_timeout | INT | | 监控超时时间（毫秒） |

### infra_job_log（定时任务日志表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 日志编号 |
| job_id | BIGINT | FK -> infra_job.id | 任务编号 |
| handler_name | VARCHAR | | 处理器名称 |
| handler_param | VARCHAR | | 处理器参数 |
| execute_index | INT | | 第几次执行 |
| begin_time | DATETIME | | 开始时间 |
| end_time | DATETIME | | 结束时间 |
| duration | INT | | 执行时长（毫秒） |
| status | TINYINT | | 执行状态 |
| result | VARCHAR | | 执行结果 |

## API 日志聚合

### infra_api_access_log（API 访问日志表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 编号 |
| trace_id | VARCHAR | | 链路追踪编号 |
| user_id | BIGINT | | 用户编号 |
| user_type | TINYINT | | 用户类型 |
| application_name | VARCHAR | | 应用名 |
| request_method | VARCHAR | | 请求方法 |
| request_url | VARCHAR | | 请求地址 |
| request_params | VARCHAR | | 请求参数 |
| response_body | VARCHAR | | 响应结果 |
| user_ip | VARCHAR | | 用户 IP |
| user_agent | VARCHAR | | 浏览器 UA |
| operate_module | VARCHAR | | 操作模块 |
| operate_name | VARCHAR | | 操作名 |
| operate_type | TINYINT | | 操作分类 |
| begin_time | DATETIME | | 开始时间 |
| end_time | DATETIME | | 结束时间 |
| duration | INT | | 执行时长（毫秒） |
| result_code | INT | | 结果码 |
| result_msg | VARCHAR | | 结果提示 |

### infra_api_error_log（API 异常日志表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 编号 |
| user_id | BIGINT | | 用户编号 |
| trace_id | VARCHAR | | 链路追踪编号 |
| user_type | TINYINT | | 用户类型 |
| application_name | VARCHAR | | 应用名 |
| request_method | VARCHAR | | 请求方法 |
| request_url | VARCHAR | | 请求地址 |
| request_params | VARCHAR | | 请求参数 |
| user_ip | VARCHAR | | 用户 IP |
| user_agent | VARCHAR | | 浏览器 UA |
| exception_time | DATETIME | | 异常时间 |
| exception_name | VARCHAR | | 异常名 |
| exception_message | VARCHAR | | 异常消息 |
| exception_root_cause_message | VARCHAR | | 异常根消息 |
| exception_stack_trace | VARCHAR | | 异常栈轨迹 |
| exception_class_name | VARCHAR | | 异常类名 |
| exception_file_name | VARCHAR | | 异常文件名 |
| exception_method_name | VARCHAR | | 异常方法名 |
| exception_line_number | INT | | 异常行号 |
| process_status | TINYINT | | 处理状态 |
| process_time | DATETIME | | 处理时间 |
| process_user_id | BIGINT | | 处理用户编号 |

## 独立实体

### infra_config（参数配置表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 参数主键 |
| category | VARCHAR | | 参数分类 |
| name | VARCHAR | | 参数名称 |
| config_key | VARCHAR | | 参数键名 |
| value | VARCHAR | | 参数键值 |
| type | TINYINT | | 参数类型 |
| visible | BIT | | 是否可见 |
| remark | VARCHAR | | 备注 |

### infra_data_source_config（数据源配置表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|-----|------|
| id | BIGINT | PK | 主键编号，0 表示 Master 数据源 |
| name | VARCHAR | | 连接名 |
| url | VARCHAR | | 数据源连接 |
| username | VARCHAR | | 用户名 |
| password | VARCHAR | | 密码（加密存储） |

## ER 关系定义

| 关系 | 类型 | 外键 | 说明 |
|-----|------|------|------|
| infra_file -> infra_file_config | N:1 | config_id | 文件属于某个存储配置 |
| infra_codegen_column -> infra_codegen_table | N:1 | table_id | 列定义属于某个表定义 |
| infra_job_log -> infra_job | N:1 | job_id | 日志属于某个任务 |
| infra_codegen_table -> infra_codegen_table | N:1 | master_table_id | 主子表自关联 |
| infra_codegen_table -> infra_data_source_config | N:1 | data_source_config_id | 表定义关联数据源 |

## Mapper 规范

所有 Mapper 继承 `BaseMapperX<T>`，获得通用 CRUD 方法：

```java
public interface FileMapper extends BaseMapperX<FileDO> {
    default PageResult<FileDO> selectPage(FilePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<FileDO>()
                .likeIfPresent(FileDO::getPath, reqVO.getPath())
                .likeIfPresent(FileDO::getName, reqVO.getName())
                .betweenIfPresent(FileDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(FileDO::getId));
    }
}
```
