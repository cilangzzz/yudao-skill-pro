# 代码生成接口

## 概述

代码生成器基于数据库表结构自动生成 CRUD 代码，支持多前端框架，大幅提升开发效率。

### 业务定位

- 从数据库导入表结构，生成完整的前后端 CRUD 代码
- 支持单表、主子表、树表等多种生成场景
- 支持 Vue2、Vue3、Vben、UniApp 等多前端框架
- 使用 Velocity 模板引擎，支持自定义模板扩展

### 核心实体

| 实体 | 说明 |
|-----|------|
| CodegenTableDO | 代码生成表定义，存储表的元信息和生成配置 |
| CodegenColumnDO | 代码生成列定义，存储字段的元信息和前端配置 |
| DataSourceConfigDO | 数据源配置，支持连接不同数据库 |

## 数据模型

### infra_codegen_table（代码生成表定义）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 编号，主键 |
| data_source_config_id | BIGINT | 数据源编号 |
| scene | TINYINT | 生成场景（单表/主子表/树表） |
| table_name | VARCHAR | 表名称 |
| table_comment | VARCHAR | 表描述 |
| remark | VARCHAR | 备注 |
| module_name | VARCHAR | 模块名 |
| business_name | VARCHAR | 业务名 |
| class_name | VARCHAR | 类名称 |
| class_comment | VARCHAR | 类描述 |
| author | VARCHAR | 作者 |
| template_type | TINYINT | 模板类型 |
| front_type | TINYINT | 前端类型 |
| parent_menu_id | BIGINT | 父菜单编号 |
| master_table_id | BIGINT | 主表编号（子表时使用） |
| sub_join_column_id | BIGINT | 子表关联字段编号 |
| sub_join_many | BIT | 是否一对多 |
| tree_parent_column_id | BIGINT | 树表父字段编号 |
| tree_name_column_id | BIGINT | 树表名称字段编号 |

### infra_codegen_column（代码生成列定义）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 编号，主键 |
| table_id | BIGINT | 表编号，关联 CodegenTableDO |
| column_name | VARCHAR | 字段名 |
| data_type | VARCHAR | 数据库类型 |
| column_comment | VARCHAR | 字段描述 |
| nullable | BIT | 是否允许空 |
| primary_key | BIT | 是否主键 |
| ordinal_position | INT | 排序 |
| java_type | VARCHAR | Java 类型 |
| java_field | VARCHAR | Java 属性名 |
| dict_type | VARCHAR | 字典类型 |
| example | VARCHAR | 数据示例 |
| create_operation | BIT | 是否 Create 操作字段 |
| update_operation | BIT | 是否 Update 操作字段 |
| list_operation | BIT | 是否 List 查询字段 |
| list_operation_condition | VARCHAR | List 查询条件 |
| list_operation_result | BIT | 是否 List 返回字段 |
| html_type | VARCHAR | 显示类型 |

### infra_data_source_config（数据源配置表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 主键编号，0 表示 Master 数据源 |
| name | VARCHAR | 连接名 |
| url | VARCHAR | 数据源连接 |
| username | VARCHAR | 用户名 |
| password | VARCHAR | 密码（加密存储） |

## 表接口

### 1. 代码生成表列表

- **路径**: `GET /infra/codegen/table/list`
- **说明**: 分页查询代码生成表定义
- **权限**: `infra:codegen:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| tableName | String | 否 | 表名称（模糊匹配） |
| tableComment | String | 否 | 表描述（模糊匹配） |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<CodegenTableDO>>`

### 2. 导入表结构

- **路径**: `POST /infra/codegen/table/create`
- **说明**: 从数据库导入表结构，自动生成代码生成定义
- **权限**: `infra:codegen:create`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| dataSourceConfigId | Long | 否 | 数据源编号（默认主数据源） |
| tableName | String | 是 | 表名称 |
| scene | Integer | 是 | 生成场景 |

### 3. 更新表配置

- **路径**: `PUT /infra/codegen/table/update`
- **说明**: 更新代码生成表的配置信息
- **权限**: `infra:codegen:update`

### 4. 删除表定义

- **路径**: `DELETE /infra/codegen/table/delete`
- **说明**: 删除代码生成表定义及其列定义
- **权限**: `infra:codegen:delete`

### 5. 同步表结构

- **路径**: `PUT /infra/codegen/table/sync`
- **说明**: 从数据库同步表结构变更，更新列定义
- **权限**: `infra:codegen:update`

### 6. 预览生成代码

- **路径**: `GET /infra/codegen/table/preview`
- **说明**: 预览生成的代码内容
- **权限**: `infra:codegen:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 表编号 |

- **响应**: `CommonResult<Map<String, String>>` - 文件路径到代码内容的映射

### 7. 下载生成代码

- **路径**: `GET /infra/codegen/table/download`
- **说明**: 下载生成的代码压缩包
- **权限**: `infra:codegen:download`

## 列接口

### 8. 列定义列表

- **路径**: `GET /infra/codegen/column/list`
- **说明**: 查询指定表的列定义列表
- **权限**: `infra:codegen:query`

### 9. 更新列配置

- **路径**: `PUT /infra/codegen/column/update`
- **说明**: 更新列的前端配置（字典类型、HTML类型、查询条件等）
- **权限**: `infra:codegen:update`

## 数据源接口

### 10. 数据源列表

- **路径**: `GET /infra/db/list`
- **说明**: 查询数据源配置列表
- **权限**: `infra:db:query`

### 11. 创建数据源

- **路径**: `POST /infra/db/create`
- **说明**: 创建新的数据源配置
- **权限**: `infra:db:create`

### 12. 测试数据源连接

- **路径**: `POST /infra/db/test`
- **说明**: 测试数据源连接是否正常
- **权限**: `infra:db:create`

## 关键实现

- **CodegenService**: 代码生成服务接口
- **CodegenServiceImpl**: 服务实现类
- **CodegenBuilder**: 构建器，从数据库表结构构建 CodegenTableDO 和 CodegenColumnDO
- **CodegenEngine**: 生成引擎，使用 Velocity 模板渲染代码
- **DataSourceConfigService**: 数据源配置服务

## 生成场景

| 场景 | 枚举值 | 说明 |
|-----|-------|------|
| 单表 | 0 | 基础 CRUD 生成 |
| 主子表 | 1 | 主表关联子表，支持一对多 |
| 树表 | 2 | 树形结构表，支持父级字段 |

## 前端类型

| 类型 | 枚举值 | 说明 |
|-----|-------|------|
| Vue2 | 0 | Vue2 + Element UI |
| Vue3 | 1 | Vue3 + Element Plus |
| Vben | 2 | Vben Admin |
| UniApp | 3 | UniApp 小程序 |

## 最佳实践

- **表结构同步**: 使用 syncCodegenFromDB() 同步数据库表结构变更，保持代码生成定义与数据库一致
- **模板自定义**: 在 resources/codegen/ 下创建 .vm 模板文件，通过 CodegenEngine 注册自定义模板
- **数据源管理**: 通过 DataSourceConfigDO 管理多数据源，支持代码生成器连接不同数据库

## 错误码

| 错误码 | 说明 |
|-------|------|
| 1_001_004_002 | 表定义已经存在 |
