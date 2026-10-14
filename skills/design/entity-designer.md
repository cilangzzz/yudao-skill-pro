# 实体类设计 Skill

> 根据数据库表结构生成符合 yudao-vue-pro 规范的实体类（DO）

## 元信息

- **ID**：`design-entity`
- **名称**：实体类设计 Skill
- **版本**：`1.0.0`
- **分类**：`design`
- **描述**：根据数据库表结构自动生成符合 yudao 项目规范的实体类（DO），支持多租户、审计字段、JSON 字段等特性
- **创建日期**：`2026-03-31`
- **更新日期**：`2026-03-31`

## 触发条件

### 命令

- `/entity-design`
- `/design-entity`
- `/entity-generator`

### 关键词

- 生成实体类
- 创建 DO
- 生成 DO 实体
- 实体类设计
- 数据对象

### 事件

| 事件名 | 条件 |
|--------|------|
| `db_design_completed` | 数据库表结构设计完成 |
| `sql_created` | 建表 SQL 文件创建完成 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 | 示例 |
|--------|------|------|--------|------|------|
| `module_code` | string | 是 | — | 模块编码（如 `mes`、`erp`、`crm`、`system`） | `mes`、`erp`、`crm`、`system`、`pay` |
| `table_name` | string | 是 | — | 表名（含前缀，如 `mes_work_order`） | `mes_work_order`、`erp_product`、`system_user` |
| `table_comment` | string | 是 | — | 表注释/描述 | — |
| `business_fields` | array | 是 | — | 业务字段列表（不含通用字段） | 见下方 schema |
| `tenant_type` | string | 否 | `multi` | 租户类型：`single`/`multi`/`ignore` | `single`、`multi`、`ignore` |
| `entity_name` | string | 否 | `auto` | 实体类名称（默认根据表名自动生成） | — |
| `feature` | string | 否 | `auto` | 功能子目录名（默认根据实体名推断） | — |

### `business_fields` schema

| 字段 | 说明 |
|------|------|
| `name` | 字段名 |
| `type` | 数据类型 |
| `required` | 是否必填 |
| `comment` | 字段注释 |
| `enum_ref` | 枚举引用（可选） |
| `json_field` | 是否 JSON 字段（可选） |
| `java_type` | JSON 字段的 Java 类型（可选，如 `Set<Long>`） |

## 设计理念

- **业务定位**：实体类（DO）是数据库表与业务逻辑之间的桥梁，将关系型数据映射为对象
- **设计原则**：
  - 继承体系：多租户继承 `TenantBaseDO`，单租户继承 `BaseDO`
  - 审计字段：由基类提供，业务实体不重复定义
  - 字段注释：使用 JavaDoc 格式，不使用 Swagger 注解
  - JSON 字段：使用 `JacksonTypeHandler` 处理复杂类型
  - 命名规范：实体类以 `DO` 结尾，与表名保持映射关系
  - 枚举引用：在注释中说明枚举类，字段使用 `Integer` 类型

### 继承体系

| 基类 | 包路径 | 字段 | 使用场景 |
|------|--------|------|----------|
| `BaseDO` | `cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO` | `createTime`、`updateTime`、`creator`、`updater`、`deleted` | 单租户业务表（`deleted` 字段为 `Boolean` 类型） |
| `TenantBaseDO` | `cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO` | 继承 `BaseDO`，额外 `tenantId` | 多租户业务表（绝大多数场景） |

#### 特殊注解 `@TenantIgnore`

- **包路径**：`cn.iocoder.yudao.framework.tenant.core.aop.TenantIgnore`
- **使用场景**：租户表、套餐表等需要忽略多租户过滤的实体

## 命名转换规则

### 表名 → 实体类名

- **规则**：
  - 去除表前缀（如 `mes_`、`erp_`、`system_`、`crm_`、`bpm_`、`pay_`）
  - `snake_case` 转 `PascalCase`
  - 添加 `DO` 后缀
  - 特殊表名特殊处理
- **示例**：

| 表名 | 实体类名 |
|------|----------|
| `mes_work_order` | `WorkOrderDO` |
| `erp_product` | `ProductDO` |
| `system_users` | `AdminUserDO` |
| `system_role` | `RoleDO` |
| `crm_customer` | `CustomerDO` |

### 字段名 → 属性名

- **规则**：`snake_case` 转 `camelCase`，保持与数据库字段映射
- **示例**：

| 列名 | 属性名 |
|------|--------|
| `work_order_no` | `workOrderNo` |
| `create_time` | `createTime` |
| `tenant_id` | `tenantId` |

### 特殊表名映射

| 表名 | 类名 |
|------|------|
| `system_users` | `AdminUserDO` |
| `system_menu` | `MenuDO` |
| `system_tenant` | `TenantDO` |
| `system_dict_data` | `DictDataDO` |
| `system_dict_type` | `DictTypeDO` |

### 表前缀映射（模块编码）

| 前缀 | 模块 |
|------|------|
| `sys` | `system` |
| `mes` | `mes` |
| `erp` | `erp` |
| `crm` | `crm` |
| `bpm` | `bpm` |
| `pay` | `pay` |
| `member` | `member` |
| `infra` | `infra` |

## 类型映射规则

### MySQL → Java

| MySQL 类型 | Java 类型 | 备注 | 引入 |
|-----------|-----------|------|------|
| `BIGINT` | `Long` | 主键、外键、数量类字段 | — |
| `INT` / `INTEGER` | `Integer` | 状态、排序、计数类字段 | — |
| `TINYINT` | `Integer` | 枚举字段、开关字段 | — |
| `SMALLINT` | `Integer` | 小范围数值 | — |
| `DECIMAL(p,s)` | `BigDecimal` | 金额、精确数值 | `java.math.BigDecimal` |
| `FLOAT` / `DOUBLE` | `Double` | 浮点数 | — |
| `VARCHAR` / `CHAR` | `String` | 字符串 | — |
| `TEXT` / `LONGTEXT` | `String` | 大文本 | — |
| `DATETIME` / `TIMESTAMP` | `LocalDateTime` | 日期时间 | `java.time.LocalDateTime` |
| `DATE` | `LocalDate` | 日期 | `java.time.LocalDate` |
| `TIME` | `LocalTime` | 时间 | `java.time.LocalTime` |
| `BIT(1)` / `BOOLEAN` | `Boolean` | 布尔值 | — |
| `BLOB` / `LONGBLOB` | `byte[]` | 二进制数据 | — |
| `JSON` | 复杂类型（`JacksonTypeHandler`） | JSON 数据，需特殊处理 | — |

### JSON 字段类型映射

| 模式 | Java 类型 | 引入 |
|------|-----------|------|
| ID 数组 | `Set<Long>` | `java.util.Set` |
| 字符串数组 | `List<String>` | `java.util.List` |
| 键值对对象 | `Map<String, Object>` | `java.util.Map` |

## 注解规范

### 类级别注解

#### 必选注解

| 注解 | 格式 | 引入 | 备注 |
|------|------|------|------|
| `@TableName` | `@TableName(value = "{table_name}", autoResultMap = true)` | `com.baomidou.mybatisplus.annotation.TableName` | `autoResultMap = true` 用于支持 TypeHandler |
| `@KeySequence` | `@KeySequence("{table_name}_seq")` | `com.baomidou.mybatisplus.annotation.KeySequence` | Oracle/PostgreSQL 主键自增，MySQL 可省略但建议保留 |
| `@Data` | — | `lombok.Data` | Lombok getter/setter |
| `@EqualsAndHashCode` | `@EqualsAndHashCode(callSuper = true)` | `lombok.EqualsAndHashCode` | 必须 `callSuper = true` 以包含基类字段 |

#### 可选注解

| 注解 | 引入 | 备注 |
|------|------|------|
| `@Builder` | `lombok.Builder` | 构建器模式 |
| `@NoArgsConstructor` | `lombok.NoArgsConstructor` | 无参构造（与 Builder 配合） |
| `@AllArgsConstructor` | `lombok.AllArgsConstructor` | 全参构造（与 Builder 配合） |
| `@TenantIgnore` | `cn.iocoder.yudao.framework.tenant.core.aop.TenantIgnore` | 忽略多租户过滤（仅用于租户表等特殊场景） |

### 字段级别注解

#### 主键

| 注解 | 引入 | 备注 |
|------|------|------|
| `@TableId` | `com.baomidou.mybatisplus.annotation.TableId` | 主键字段，默认使用雪花算法 |

#### JSON 字段

- **注解**：`@TableField(typeHandler = JacksonTypeHandler.class)`
- **引入**：`com.baomidou.mybatisplus.annotation.TableField`
- **Handler 引入**：`com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler`
- **备注**：JSON 类型字段，需要 `@TableName` 包含 `autoResultMap = true`

## 代码模板

### 多租户实体模板（最常用）

- **描述**：多租户业务表实体类
- **基类**：`TenantBaseDO`

```java
package cn.iocoder.yudao.module.{module}.dal.dataobject.{feature};

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;
{additional_imports}

/**
 * {table_comment} DO
 *
 * @author {author}
 */
@TableName(value = "{table_name}", autoResultMap = true)
@KeySequence("{table_name}_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class {EntityName}DO extends TenantBaseDO {

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    {business_fields}

}
```

### 单租户实体模板

- **描述**：单租户业务表实体类
- **基类**：`BaseDO`

```java
package cn.iocoder.yudao.module.{module}.dal.dataobject.{feature};

import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;
{additional_imports}

/**
 * {table_comment} DO
 *
 * @author {author}
 */
@TableName(value = "{table_name}", autoResultMap = true)
@KeySequence("{table_name}_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class {EntityName}DO extends BaseDO {

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    {business_fields}

}
```

### 忽略多租户实体模板

- **描述**：需要忽略多租户过滤的实体类（如租户表、套餐表）
- **基类**：`BaseDO`
- **额外注解**：`@TenantIgnore`

```java
package cn.iocoder.yudao.module.{module}.dal.dataobject.{feature};

import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import cn.iocoder.yudao.framework.tenant.core.aop.TenantIgnore;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;
{additional_imports}

/**
 * {table_comment} DO
 *
 * @author {author}
 */
@TenantIgnore
@TableName(value = "{table_name}", autoResultMap = true)
@KeySequence("{table_name}_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class {EntityName}DO extends BaseDO {

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    {business_fields}

}
```

### 业务字段模板

#### 普通字段

```java
/**
 * {字段注释}
{enum_reference}
 */
private {JavaType} {fieldName};
```

#### JSON 字段

```java
/**
 * {字段注释}
 */
@TableField(typeHandler = JacksonTypeHandler.class)
private {JavaType} {fieldName};
```

## 输出规范

### 文件输出位置

- **路径模式**：`yudao-module-{module}/src/main/java/cn/iocoder/yudao/module/{module}/dal/dataobject/{feature}/{EntityName}DO.java`
- **示例**：`yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/dal/dataobject/workorder/WorkOrderDO.java`

### 导入语句规范

#### 基础导入

```java
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.KeySequence;
import lombok.Data;
import lombok.EqualsAndHashCode;
```

#### 多租户导入

```java
import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
```

#### 单租户导入

```java
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
```

#### JSON Handler 导入

```java
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
```

#### Builder 导入

```java
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
```

### 产物清单

| 名称 | 类型 | 路径 |
|------|------|------|
| 实体类文件 | code | `dal/dataobject/{feature}/{EntityName}DO.java` |

## 执行流程

### 阶段 1：表结构解析

- **描述**：解析数据库表结构，提取元数据
- **步骤**：
  - 识别表名、表前缀、表注释
  - 提取业务字段列表（排除通用字段：`id`、`tenant_id`、`creator`、`create_time`、`updater`、`update_time`、`deleted`）
  - 识别主键、索引信息
  - 识别 JSON 字段、枚举字段

### 阶段 2：命名转换

- **描述**：将数据库命名转换为 Java 命名
- **步骤**：
  - 表名 → 实体类名（去除前缀 + PascalCase + DO 后缀）
  - 字段名 → 属性名（camelCase）
  - 处理特殊表名映射

### 阶段 3：类型映射

- **描述**：将 MySQL 类型映射为 Java 类型
- **步骤**：
  - 标准类型映射（BIGINT → Long 等）
  - JSON 字段识别和处理
  - 枚举字段处理（Integer + 注释引用）

### 阶段 4：继承选择

- **描述**：确定实体类继承的基类
- **步骤**：
  - 判断租户类型（multi/single/ignore）
  - 选择对应基类（TenantBaseDO/BaseDO）
  - 判断是否需要 `@TenantIgnore`

### 阶段 5：代码生成

- **描述**：生成实体类代码
- **步骤**：
  - 生成类注释和注解
  - 生成主键字段
  - 生成业务字段（含 JavaDoc 注释）
  - 生成导入语句（按规范分组排序）
  - 格式化代码

### 阶段 6：质量检查

- **描述**：验证生成的实体类
- **步骤**：
  - 检查注解完整性
  - 检查字段注释格式
  - 检查继承正确性
  - 检查命名规范

## 质量检查清单

### 生成前

- 确认表名符合命名规范
- 确认业务字段列表完整
- 确认租户类型选择正确
- 确认字段类型映射正确

### 生成后

- 实体类名称以 `DO` 结尾
- `@TableName` 注解包含 `autoResultMap = true`
- `@EqualsAndHashCode` 包含 `callSuper = true`
- 继承正确基类
- 主键字段使用 `@TableId` 注解
- 所有字段使用 JavaDoc 注释格式
- JSON 字段使用 `JacksonTypeHandler`
- 枚举字段注释包含枚举引用
- 不包含 Swagger `@Schema` 注解
- 不重复定义审计字段（已在基类中）

## 示例

### 多租户实体示例

#### 输入

```yaml
module_code: "mes"
table_name: "mes_work_order"
table_comment: "生产工单"
tenant_type: "multi"
business_fields:
  - name: "order_no"
    type: "VARCHAR(64)"
    comment: "工单编号"
    unique: true
  - name: "product_id"
    type: "BIGINT"
    comment: "产品ID"
  - name: "status"
    type: "TINYINT"
    comment: "状态"
    enum_ref: "WorkOrderStatusEnum"
  - name: "plan_qty"
    type: "INT"
    comment: "计划数量"
```

#### 输出类名

`WorkOrderDO`

#### 输出文件

`yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/dal/dataobject/workorder/WorkOrderDO.java`

#### 输出代码

```java
package cn.iocoder.yudao.module.mes.dal.dataobject.workorder;

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import cn.iocoder.yudao.module.mes.enums.WorkOrderStatusEnum;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

/**
 * 生产工单 DO
 *
 * @author yudao
 */
@TableName(value = "mes_work_order", autoResultMap = true)
@KeySequence("mes_work_order_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WorkOrderDO extends TenantBaseDO {

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    /**
     * 工单编号
     */
    private String orderNo;

    /**
     * 产品ID
     */
    private Long productId;

    /**
     * 状态
     *
     * 枚举 {@link WorkOrderStatusEnum}
     */
    private Integer status;

    /**
     * 计划数量
     */
    private Integer planQty;

}
```

### JSON 字段实体示例

#### 输入

```yaml
module_code: "system"
table_name: "system_role"
table_comment: "角色"
tenant_type: "multi"
business_fields:
  - name: "name"
    type: "VARCHAR(100)"
    comment: "角色名称"
  - name: "code"
    type: "VARCHAR(50)"
    comment: "角色标识"
  - name: "data_scope_dept_ids"
    type: "JSON"
    comment: "数据范围部门ID数组"
    json_field: true
    java_type: "Set<Long>"
```

#### 输出代码

```java
package cn.iocoder.yudao.module.system.dal.dataobject.permission;

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;

import java.util.Set;

/**
 * 角色 DO
 *
 * @author yudao
 */
@TableName(value = "system_role", autoResultMap = true)
@KeySequence("system_role_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RoleDO extends TenantBaseDO {

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    /**
     * 角色名称
     */
    private String name;

    /**
     * 角色标识
     */
    private String code;

    /**
     * 数据范围(指定部门数组)
     */
    @TableField(typeHandler = JacksonTypeHandler.class)
    private Set<Long> dataScopeDeptIds;

}
```

### 忽略租户实体示例

#### 输入

```yaml
module_code: "system"
table_name: "system_tenant"
table_comment: "租户"
tenant_type: "ignore"
business_fields:
  - name: "name"
    type: "VARCHAR(100)"
    comment: "租户名称"
  - name: "contact_name"
    type: "VARCHAR(50)"
    comment: "联系人"
  - name: "status"
    type: "TINYINT"
    comment: "状态"
    enum_ref: "CommonStatusEnum"
```

#### 输出代码

```java
package cn.iocoder.yudao.module.system.dal.dataobject.tenant;

import cn.iocoder.yudao.framework.common.enums.CommonStatusEnum;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import cn.iocoder.yudao.framework.tenant.core.aop.TenantIgnore;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

/**
 * 租户 DO
 *
 * @author yudao
 */
@TenantIgnore
@TableName(value = "system_tenant", autoResultMap = true)
@KeySequence("system_tenant_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TenantDO extends BaseDO {

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    /**
     * 租户名称
     */
    private String name;

    /**
     * 联系人
     */
    private String contactName;

    /**
     * 状态
     *
     * 枚举 {@link CommonStatusEnum}
     */
    private Integer status;

}
```

## 与其他 Skill 的关系

### 上游依赖

| Skill | 关系 | 描述 | 路径 |
|-------|------|------|------|
| `db-designer` | 依赖 | 依赖数据库表结构设计，从 SQL 解析表信息 | `skills/design/db-designer.md` |

### 下游输出

| Skill | 关系 | 描述 | 路径 |
|-------|------|------|------|
| `api-designer` | 输出 | 实体类作为 API 设计输入 | `skills/design/api-designer.md` |

### 协同

| 路径 | 关系 | 描述 |
|------|------|------|
| `skills/usage/entity-implementation.md` | 协同 | `entity-designer` 专注实体类设计规范，`entity-implementation` 提供完整实现流程（含 Mapper、Service 等） |

## 错误处理

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| `ENT001` | 表名不符合命名规范 | 检查表名前缀和格式，确保包含模块前缀（如 `mes_`、`erp_`） |
| `ENT002` | 缺少必需的表注释 | 提供 `table_comment` 参数 |
| `ENT003` | 字段类型无法映射 | 使用默认 `String` 类型，手动调整 |
| `ENT004` | JSON 字段缺少 `java_type` | 为 JSON 字段指定 `java_type`，如 `Set<Long>` |
| `ENT005` | 租户类型选择错误 | `multi` 使用 `TenantBaseDO`，`single` 使用 `BaseDO`，`ignore` 使用 `@TenantIgnore` |
| `ENT006` | 枚举字段缺少 `enum_ref` | 为枚举字段提供 `enum_ref` 参数，在注释中引用枚举类 |
