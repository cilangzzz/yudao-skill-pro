# 数据源配置接口 (DataSourceConfigController)

> 管理多数据源配置（infra_data_source_config），供代码生成器等组件连接业务库之外的多个数据库使用；接口读写均内置 master 主数据源（id=0，来自 application 配置的 primary 数据源）的展示，新增/修改时会实时校验 JDBC 连通性。

## 接口路径前缀

/infra/data-source-config  (Controller: DataSourceConfigController)

## 1. 数据源配置管理

### 1.1 创建数据源配置

- **路径**: POST /infra/data-source-config/create
- **权限**: infra:data-source-config:create
- **说明**: 新增一条数据源配置，创建前先验证数据库连接可用。

**请求参数 (DataSourceConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 主键编号，创建时不传 |
| name | String | 是 | @NotNull | 数据源名称，如 test |
| url | String | 是 | @NotNull | 数据源连接，如 jdbc:mysql://127.0.0.1:3306/ruoyi-vue-pro |
| username | String | 是 | @NotNull | 用户名 |
| password | String | 是 | @NotNull | 密码 |

**响应**: CommonResult&lt;Long&gt;（新创建的数据源配置编号）

**业务逻辑**:
1. 将请求 VO 转换为 DataSourceConfigDO。
2. 调用 JdbcUtils.isConnectionOK(url, username, password) 验证数据库连接可用，连接失败则抛出异常。
3. 插入 infra_data_source_config 表并返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_007_001 | 数据源配置不正确，无法进行连接 |

### 1.2 更新数据源配置

- **路径**: PUT /infra/data-source-config/update
- **权限**: infra:data-source-config:update
- **说明**: 按 id 修改数据源配置，修改前校验存在性并重新验证连接。

**请求参数 (DataSourceConfigSaveReqVO)**: 同 [1.1 创建数据源配置](#11-创建数据源配置)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验数据源配置是否存在，不存在则抛出异常。
2. 将请求 VO 转换为 DataSourceConfigDO。
3. 再次验证数据库连接可用，失败则抛出异常。
4. 按 id 更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_007_000 | 数据源配置不存在 |
| 1_001_007_001 | 数据源配置不正确，无法进行连接 |

### 1.3 删除数据源配置

- **路径**: DELETE /infra/data-source-config/delete
- **权限**: infra:data-source-config:delete
- **说明**: 删除单条数据源配置。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 数据源配置编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验数据源配置是否存在，不存在则抛出异常。
2. 按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_007_000 | 数据源配置不存在 |

### 1.4 批量删除数据源配置

- **路径**: DELETE /infra/data-source-config/delete-list
- **权限**: infra:data-source-config:delete
- **说明**: 按编号列表批量删除数据源配置。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 数据源配置编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 列表批量删除记录（不逐条校验存在性）。

### 1.5 获得数据源配置

- **路径**: GET /infra/data-source-config/get
- **权限**: infra:data-source-config:query
- **说明**: 按编号查询单条数据源配置；id 为 0 时返回 master 主数据源。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 数据源配置编号，0 表示 master 主数据源 |

**响应**: CommonResult&lt;DataSourceConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键编号 |
| name | String | 数据源名称 |
| url | String | 数据源连接 |
| username | String | 用户名 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 若 id 等于 0（DataSourceConfigDO.ID_MASTER），从 DynamicDataSourceProperties 读取 primary 数据源配置，构造 master 数据源信息返回。
2. 否则按 id 从数据库查询记录并转换为 RespVO 返回（密码字段不对外返回）。

**错误码**: 无（查询不存在时返回 null 数据）

### 1.6 获得数据源配置列表

- **路径**: GET /infra/data-source-config/list
- **权限**: infra:data-source-config:query
- **说明**: 查询全部数据源配置，列表头部固定附带 master 主数据源。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DataSourceConfigRespVO&gt;&gt;（字段同 [1.5 获得数据源配置](#15-获得数据源配置)）

**业务逻辑**:
1. 查询 infra_data_source_config 全表记录。
2. 从 DynamicDataSourceProperties 读取 primary 数据源构造 master 配置（id=0），插入结果列表头部。
3. 批量转换为 RespVO 返回。

## 补充说明

- **master 主数据源**: id 固定为 0，来源于 application 配置文件中 dynamic-datasource 的 primary 数据源，仅支持查询展示，不支持增删改。
- **密码加密存储**: DataSourceConfigDO 的 password 字段使用 EncryptTypeHandler 加密存储，且该表通过 @TenantIgnore 忽略租户隔离。
- **内部服务 DatabaseTableService**: 本域还包含 DatabaseTableServiceImpl（getTableList / getTable），无 HTTP 端点，供代码生成器（CodegenServiceImpl）使用：基于数据源配置通过 MyBatis-Plus Generator 解析目标库的表结构，解析时忽略视图、排除 ACT_/QRTZ_/FLW_ 等工作流与定时任务前缀表、Oracle 系统表及含 $ 的系统表，并按表名排序。
