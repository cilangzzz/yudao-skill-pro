# 配置管理接口

## 概述

系统配置管理提供键值对形式的参数配置能力，支持分类管理和可见性控制。

### 业务定位

- 为整个系统提供统一的配置管理能力
- 支持通过 ConfigApi 供其他模块 RPC 调用获取配置值
- 配置项支持分类、类型标记和可见性控制

### 核心实体

| 实体 | 说明 |
|-----|------|
| ConfigDO | 参数配置实体，存储 key-value 配置对 |

## 数据模型

**表名**: `infra_config`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 参数主键 |
| category | VARCHAR | 参数分类 |
| name | VARCHAR | 参数名称 |
| config_key | VARCHAR | 参数键名 |
| value | VARCHAR | 参数键值 |
| type | TINYINT | 参数类型 |
| visible | BIT | 是否可见 |
| remark | VARCHAR | 备注 |

继承 BaseDO 字段：creator, createTime, updater, updateTime, deleted

## 接口列表

### 1. 配置列表查询

- **路径**: `GET /infra/config/list`
- **说明**: 分页查询参数配置列表
- **权限**: `infra:config:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 参数名称（模糊匹配） |
| configKey | String | 否 | 参数键名（模糊匹配） |
| type | Integer | 否 | 参数类型 |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ConfigDO>>`

### 2. 创建配置

- **路径**: `POST /infra/config/create`
- **说明**: 创建新的参数配置
- **权限**: `infra:config:create`
- **请求参数**: ConfigDO 对象

### 3. 更新配置

- **路径**: `PUT /infra/config/update`
- **说明**: 更新参数配置
- **权限**: `infra:config:update`
- **请求参数**: ConfigDO 对象

### 4. 删除配置

- **路径**: `DELETE /infra/config/delete`
- **说明**: 删除指定参数配置
- **权限**: `infra:config:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 参数主键 |

### 5. 获取配置值（按 key）

- **路径**: `GET /infra/config/get-valueByKey`
- **说明**: 根据 configKey 获取配置值
- **权限**: 无需特定权限

## 模块间调用

其他模块通过 `ConfigApi` 接口获取配置值：

```java
// 获取配置值示例
String value = configApi.getConfigValueByKey("sys.user.init-password");
```

- `ConfigApi.getConfigValueByKey(key)` - 根据 key 获取配置值

## 关键实现

- **ConfigService**: 配置管理服务接口
- **ConfigServiceImpl**: 服务实现类
- **ConfigMapper**: 数据访问层，继承 BaseMapperX

## 错误码

| 错误码 | 说明 |
|-------|------|
| 1_001_000_001 | 参数配置不存在 |
