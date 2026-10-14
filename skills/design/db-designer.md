# 数据库设计 Skill

> 根据业务需求生成符合项目规范的数据库表结构

## 元信息

- **ID**：`db-designer`
- **名称**：数据库设计 Skill
- **版本**：`1.1.0`
- **分类**：`design`
- **描述**：根据业务需求自动生成符合项目规范的数据库设计，包括表结构、索引、ER 图等
- **创建日期**：`2026-03-31`
- **更新日期**：`2026-10-14`

## 触发条件

### 命令

- `/db-design`
- `/db-designer`

### 关键词

- 设计数据库
- 生成表结构
- 创建数据模型
- 建表
- DDL

### 事件

| 事件名 | 条件 |
|--------|------|
| `prd_approved` | PRD 文档审核通过 |
| `architecture_defined` | 系统架构设计完成 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 | 示例 |
|--------|------|------|--------|------|------|
| `module_code` | string | 是 | — | 模块编码（如 `mes`、`erp`、`crm`、`bpm` 等） | `mes`、`erp`、`crm`、`bpm`、`pay`、`za` |
| `table_name` | string | 是 | — | 表名（不含前缀） | `work_order`、`product`、`customer`、`penalty` |
| `business_fields` | array | 是 | — | 业务字段列表 | — |
| `indexes` | array | 否 | `[]` | 额外索引定义 | — |
| `create_date` | string | 否 | `today` | 创建日期（用于文件命名） | — |

## 设计理念

- **业务定位**：数据库设计是业务建模的核心环节，将业务需求转化为可存储的数据结构
- **设计原则**：
  - 多租户隔离：所有业务表包含 `tenant_id` 字段，索引必须包含 `tenant_id`
  - 审计追踪：标准化审计字段，支持数据变更追踪
  - 逻辑删除：使用 `deleted` 字段实现软删除，避免数据物理删除
  - 索引优化：根据查询场景设计索引，遵循最左匹配原则
  - 命名规范：统一的表名、字段名、索引名命名规则

## 目录结构规范

- **基础路径**：`sql`
- **详细规范**：`sql/README.md`（SQL 文件管理规范，目录与文件命名以此为准）
- **布局**：

```text
sql/
├── {发版日期}/          # 已指定发版日期，如 2026_10_20/，发版后只读归档
├── {模块名}/            # 未定发版日期且归属单一模块或业务域，如 mes/、za/
├── {当前日期}/          # 未定发版日期且跨模块/通用，如 2026_10_14/
├── master/              # 既有全量基线（多数据库版本），保持不变
└── mysql/ 等数据库目录   # 源项目各数据库全量脚本，保持不变
```

- **规则**：
  - 新增 SQL 一律放入发版日期 / 模块名 / 当前日期三类目录，不再写入 `master/` 或各数据库目录
  - 分类由文件名中的操作段决定（见 `file_naming`），不再使用 `table/create` 等子目录分类

## 文件命名规范

- **统一格式**：连字符分段，段内下划线，详见 `sql/README.md`
- **格式**：`{YYYY_MM_DD}-{表名}-{操作}[-{两位序号}][-{数据库标识}].sql`

### 建表文件

- **示例**：
  - `2026_10_14-mes_work_order-create_table.sql`
  - `2026_10_14-crm_customer-create_table-postgresql.sql`
- **规则**：
  - 日期使用实际编写日期（`YYYY_MM_DD`）
  - 表名使用小写字母和下划线
  - 方言变体仅在语句不兼容时创建，数据库标识取值与 `sql/` 既有方言目录一致（`postgresql`、`oracle`、`dm` 等）

### 表结构更新（新增/修改/删除字段、索引等）

- **示例**：
  - `2026_10_15-mes_work_order-add_priority_column.sql`
  - `2026_10_15-crm_customer-modify_name_column.sql`
  - `2026_10_15-mes_work_order-add_index-01.sql`
  - `2026_10_15-mes_work_order-add_index-02.sql`
- **规则**：
  - 操作段使用具体操作描述（`add_column`、`modify_column`、`drop_index` 等）
  - 同一表同一天多次变更无法用补充说明区分时，同批文件统一追加两位序号（`-01`、`-02`）
  - 已发版目录只读，变更一律新增文件

### 序列文件命名（Oracle/PostgreSQL）

- **示例**：
  - `2026_10_14-mes_work_order-create_seq.sql`
- **规则**：
  - 与建表使用相同日期
  - 序列名通常为 `表名_seq`

### 初始数据文件命名

- **示例**：
  - `2026_10_14-system_dict_data-insert_data.sql`
  - `2026_10_14-system_menu-insert_menu_data.sql`
- **规则**：
  - 单表初始数据按统一格式命名
  - 模块级全量初始化脚本（`bpm.sql`、`quartz.sql` 等）属于 `master/` 基线，不按此命名

## 表命名规范

### 表名前缀

| 前缀 | 用途 | 示例 |
|------|------|------|
| `sys_` | 系统核心表 | `sys_user`、`sys_role`、`sys_menu`、`sys_dict_data` |
| `mes_` | 制造执行系统表 | `mes_work_order`、`mes_product`、`mes_workshop` |
| `erp_` | 企业资源计划表 | `erp_purchase`、`erp_sale`、`erp_inventory` |
| `crm_` | 客户关系管理表 | `crm_customer`、`crm_contract`、`crm_clue` |
| `bpm_` | 工作流表 | `bpm_process_definition`、`bpm_process_instance` |
| `pay_` | 支付模块表 | `pay_order`、`pay_refund`、`pay_channel` |
| `member_` | 会员模块表 | `member_user`、`member_level`、`member_address` |
| `infra_` | 基础设施表 | `infra_file`、`infra_config` |
| `za_` | 治安业务表 | `za_case`、`za_penalty`、`za_mediation` |
| `xz_` | 行政业务表 | `xz_license`、`xz_penalty`、`xzreview` |
| `jz_` | 建筑业务表 | `jz_project`、`jz_company`、`jz_permit` |
| `ye_` | 育儿业务表 | `ye_org`、`ye_child`、`ye_check` |
| `wb_` | 网吧业务表 | `wb_place`、`wb_inspection`、`wb_violation` |

### 表名规则

- 使用小写字母，单词间用下划线分隔
- 使用名词，表示实体或关系
- 避免使用 MySQL 保留字
- 长度不超过 64 个字符
- 关联表命名：`主表_关联表_rel`，如 `mes_work_order_label_rel`

### 字段命名规则

- 使用小写字母和下划线
- 布尔类型使用 `is_` 前缀，如 `is_deleted`、`is_enabled`
- 时间类型使用 `_time` 或 `_date` 后缀
- 外键使用 `关联表_id` 格式，如 `user_id`、`dept_id`
- 主键统一命名为 `id`

## 必需字段规范

### 字段定义

| 字段名 | 类型 | 约束 | 默认值 | 注释 | 位置 |
|--------|------|------|--------|------|------|
| `id` | BIGINT | NOT NULL AUTO_INCREMENT PRIMARY KEY | — | 主键 ID | 1 |
| `tenant_id` | BIGINT | NOT NULL | `0` | 租户编号 | 2（所有业务表必须包含，位于 id 之后） |
| `creator` | VARCHAR(64) | — | `''` | 创建者 | — |
| `create_time` | DATETIME | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 | — |
| `updater` | VARCHAR(64) | — | `''` | 更新者 | — |
| `update_time` | DATETIME | NOT NULL | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | 更新时间 | — |
| `deleted` | BIT(1) | NOT NULL | `b'0'` | 是否删除 | — |

### 可选备注字段

- **字段名**：`remark`
- **类型**：`VARCHAR(500)`
- **默认值**：`NULL`
- **注释**：备注
- **位置**：在审计字段之前

## 索引设计规范

### 索引命名规则

| 类型 | 命名 |
|------|------|
| 主键 | `PRIMARY KEY (`id`)` |
| 唯一索引 | `uk_{字段名}` 或 `uk_{字段1_字段2}` |
| 普通索引 | `idx_{字段名}` 或 `idx_{字段1_字段2}` |

### 索引设计原则

- 所有索引必须包含 `tenant_id` 作为第一列
- 唯一索引必须包含 `deleted` 字段（软删除场景）
- 外键字段必须建立索引
- 经常用于查询条件的字段建立索引
- 唯一约束字段建立唯一索引
- 组合索引注意字段顺序（最左匹配）
- 避免过多索引，影响写入性能

### 索引模板

#### 唯一索引（带租户）

- **模式**：`UNIQUE KEY `uk_tenant_{col}` (`tenant_id`, `{col}`, `deleted`)`
- **示例**：`UNIQUE KEY `uk_tenant_order` (`tenant_id`, `order_no`, `deleted`)`

#### 普通索引（带租户）

- **模式**：`KEY `idx_tenant_{col}` (`tenant_id`, `{col}`)`
- **示例**：`KEY `idx_tenant_status` (`tenant_id`, `status`)`

#### 外键索引

- **模式**：`KEY `idx_tenant_{fk}` (`tenant_id`, `{fk}`)`
- **示例**：`KEY `idx_tenant_line` (`tenant_id`, `line_id`)`

## 建表模板

```sql
-- ============================================
-- 文件名：{filename}
-- 说明：{table_comment}
-- 作者：{author}
-- 日期：{date}
-- 关联需求：{需求号，如有}
-- 回滚说明：{回滚语句或备份方式，破坏性操作必填}
-- ============================================

CREATE TABLE `{table_name}` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户编号',
    -- 业务字段
    {business_columns}
    -- 通用字段
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` BIT(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
    PRIMARY KEY (`id`),
    {indexes}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='{table_comment}';
```

### 字段类型推荐

| 类型 | MySQL 类型 |
|------|-----------|
| 短字符串 | `VARCHAR(64)` |
| 中字符串 | `VARCHAR(255)` |
| 长字符串 | `VARCHAR(500)` |
| 大文本 | `TEXT` |
| 整数 | `INT` |
| 长整数 | `BIGINT` |
| 金额 | `DECIMAL(18,2)` |
| 数量 | `DECIMAL(10,4)` |
| 布尔 | `TINYINT` |
| 日期时间 | `DATETIME` |
| 日期 | `DATE` |
| 状态 | `TINYINT` |

## 更新脚本规范

- **命名**：`{YYYY_MM_DD}-{表名}-{操作}[-{两位序号}][-{数据库标识}].sql`，详见 `sql/README.md`

### 字段操作模板

#### 新增字段

```sql
-- 新增字段
ALTER TABLE `{tablecolumn}` ADD COLUMN `{column}` {type} COMMENT '{comment}';
-- 示例
ALTER TABLE `mes_work_order` ADD COLUMN `priority` TINYINT DEFAULT 0 COMMENT '优先级';
```

#### 修改字段

```sql
-- 修改字段类型
ALTER TABLE `{add_column}` MODIFY COLUMN `{column}` {new_type} COMMENT '{comment}';
-- 示例
ALTER TABLE `crm_customer` MODIFY COLUMN `remark` VARCHAR(500) COMMENT '客户备注';
```

#### 删除字段

```sql
-- 删除字段（确保无业务依赖）
ALTER TABLE `{add_column}` DROP COLUMN `{column}`;
```

#### 新增索引

```sql
-- 添加普通索引
ALTER TABLE `{add_index}` ADD INDEX `idx_tenant_{col}` (`tenant_id`, `{col}`);
-- 添加唯一索引
ALTER TABLE `{add_index}` ADD UNIQUE INDEX `uk_tenant_{col}` (`tenant_id`, `{col}`, `deleted`);
```

### 文件头部模板

```sql
-- ============================================
-- 文件名：{文件名}
-- 说明：{变更目的}
-- 作者：{姓名}
-- 日期：{YYYY-MM-DD}
-- 关联需求：{需求号，如有}
-- 回滚说明：{回滚语句或备份方式，破坏性操作必填}
-- ============================================
```

### 注释规范

- 文件头部说明更新目的
- 每个变更语句添加注释
- 危险操作（删除字段、删除数据）添加警告注释

## 数据初始化规范

### INSERT 语句格式

```sql
-- 插入菜单数据
INSERT INTO `sys_menu` (`id`, `name`, `permission`, `type`, `sort`, `parent_id`, `path`, `icon`, `component`, `status`)
VALUES
(1001, '工序管理', '', 2, 1, 0, 'process', 'ep:document', 'mes/process/index', 0),
(1002, '工序查询', 'mes:process:query', 3, 1, 1001, '', '', '', 0);
```

### 字典数据

```sql
-- 字典类型
INSERT INTO `sys_dict_type` (`name`, `type`, `status`, `remark`)
VALUES ('工单状态', 'mes_work_order_status', 0, '生产工单流转状态');

-- 字典数据
INSERT INTO `sys_dict_data` (`sort`, `label`, `value`, `dict_type`, `status`)
VALUES
(1, '待下发', '0', 'mes_work_order_status', 0),
(2, '已下发', '1', 'mes_work_order_status', 0),
(3, '生产中', '2', 'mes_work_order_status', 0),
(4, '已完成', '3', 'mes_work_order_status', 0),
(5, '已关闭', '4', 'mes_work_order_status', 0);
```

## 编写规范

### SQL 格式

- 关键字使用大写：`SELECT`、`FROM`、`WHERE`、`JOIN`、`ORDER BY`
- 表名、字段名使用小写和反引号
- 每个字段占一行，逗号放在行尾
- 复杂查询使用缩进和换行提高可读性

### 注释规范

#### 文件头

```sql
-- ============================================
-- 文件名：{文件名}
-- 说明：{功能描述}
-- 作者：{作者}
-- 日期：{YYYY-MM-DD}
-- 关联需求：{需求号，如有}
-- 回滚说明：{回滚语句或备份方式，破坏性操作必填}
-- ============================================
```

- `CREATE TABLE` 语句必须包含 `COMMENT`
- 每个字段必须包含 `COMMENT`
- 复杂索引添加注释说明用途

### 事务处理

- 多条关联语句使用事务包裹
- DDL 语句（部分数据库）自动提交注意顺序
- 大数据量操作分批执行

## 版本管理

### 原则

- 建表后表结构变更新增脚本文件，不修改原文件
- 每个变更独立文件便于追踪和回滚
- 日期前缀确保文件顺序和变更时间线
- 版本升级时按日期顺序执行所有脚本
- 文件目录与命名遵循 `sql/README.md`：已发版目录只读，变更一律新增文件

### 变更记录

```sql
-- 变更记录：
-- 2025-08-09：创建表
-- 2025-11-11：新增 priority 字段
-- 2026-01-07：新增 category 字段，添加索引
```

## 执行流程

### 阶段 1：需求分析

- **描述**：解析业务需求，提取实体和关系
- **步骤**：
  - 识别核心业务实体
  - 分析实体间关系（一对多、多对多）
  - 确定实体属性列表
  - 确定表名前缀（模块编码）

### 阶段 2：实体设计

- **描述**：设计实体属性和字段
- **步骤**：
  - 设计业务属性字段
  - 添加系统必需字段（审计字段）
  - 定义主键策略（BIGINT AUTO_INCREMENT）
  - 设置外键关系

### 阶段 3：多租户设计

- **描述**：添加租户隔离字段和索引
- **步骤**：
  - 添加 `tenant_id` 字段（第二位置）
  - 确保所有索引包含 `tenant_id`
  - 唯一索引包含 `deleted` 字段

### 阶段 4：索引设计

- **描述**：根据查询场景设计索引
- **步骤**：
  - 分析查询场景（列表、详情、关联、搜索）
  - 设计主键索引
  - 设计唯一索引（业务唯一键）
  - 设计普通索引（查询优化）
  - 设计外键索引

### 阶段 5：文件生成

- **描述**：生成符合规范 SQL 文件
- **步骤**：
  - 确定文件命名（日期前缀）
  - 生成文件头部注释
  - 生成 `CREATE TABLE` 语句
  - 生成索引定义
  - 添加表注释

## 质量检查清单

### 建表前

- 确认表名符合命名规范
- 确认包含所有必需字段
- 确认字段类型和长度合理
- 确认添加了必要索引
- 确认添加了表注释和字段注释
- 确认文件命名符合规范

### 建表后

- 测试建表脚本可正常执行
- 确认所有索引包含 `tenant_id`
- 确认唯一索引包含 `deleted`
- 确认外键字段有索引
- 检查索引是否生效
- 更新相关文档

### 更新前

- 确认变更的必要性
- 评估对现有数据的影响
- 准备回滚方案
- 选择低峰期执行

## 快速参考

### 表前缀速查

| 前缀 | 说明 |
|------|------|
| `sys_` | 系统表 |
| `mes_` | 制造执行系统表 |
| `erp_` | 企业资源计划表 |
| `crm_` | 客户关系管理表 |
| `bpm_` | 工作流表 |
| `pay_` | 支付表 |
| `member_` | 会员表 |
| `infra_` | 基础设施表 |
| `za_` | 治安业务表 |
| `xz_` | 行政业务表 |
| `jz_` | 建筑业务表 |
| `ye_` | 育儿业务表 |
| `wb_` | 网吧业务表 |

### 文件操作

| 操作 | 说明 |
|------|------|
| `create_table` | 建表脚本 |
| `add_column` | 新增字段 |
| `modify_column` | 修改字段 |
| `drop_column` | 删除字段 |
| `add_index` | 新增索引 |
| `insert_data` | 初始数据 |
| `create_seq` | 序列脚本 |
| `-postgresql` 后缀 | PostgreSQL 数据库版本（Kingbase 等兼容库可直接执行，专用变体用 `-kingbase`） |

### 通用字段

| 字段 | 说明 |
|------|------|
| `id` | 主键 ID（BIGINT） |
| `tenant_id` | 租户编号（BIGINT） |
| `creator` | 创建者（VARCHAR(64)） |
| `create_time` | 创建时间（DATETIME） |
| `updater` | 更新者（VARCHAR(64)） |
| `update_time` | 更新时间（DATETIME） |
| `deleted` | 逻辑删除（BIT(1)） |
| `remark` | 备注（VARCHAR(500)） |

## 示例

### 生产工单表

#### 输入

```yaml
module_code: "mes"
table_name: "work_order"
table_comment: "生产工单表"
business_fields:
  - name: "order_no"
    type: "VARCHAR(64)"
    required: true
    comment: "工单编号"
    unique: true
  - name: "product_id"
    type: "BIGINT"
    required: true
    comment: "产品ID"
  - name: "status"
    type: "TINYINT"
    required: true
    default: "0"
    comment: "状态:0-待下发,1-已下发,2-生产中,3-已完成,4-已关闭"
```

#### 输出文件名

`2026_03_25-mes_work_order-create_table.sql`

#### 输出 SQL

```sql
-- ============================================
-- 文件名：2026_03_25-mes_work_order-create_table.sql
-- 说明：生产工单表
-- 作者：AI Assistant
-- 日期：2026-03-25
-- 关联需求：无
-- 回滚说明：无
-- ============================================

CREATE TABLE `mes_work_order` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户ID',
    `order_no` VARCHAR(64) NOT NULL COMMENT '工单编号(WO+年月日+4位流水)',
    `erp_order_no` VARCHAR(64) DEFAULT NULL COMMENT 'ERP订单编号',
    `product_id` BIGINT NOT NULL COMMENT '产品ID',
    `product_code` VARCHAR(64) NOT NULL COMMENT '产品编码',
    `product_name` VARCHAR(255) NOT NULL COMMENT '产品名称',
    `plan_qty` INT NOT NULL COMMENT '计划数量',
    `actual_qty` INT NOT NULL DEFAULT 0 COMMENT '实际数量',
    `routing_id` BIGINT NOT NULL COMMENT '工艺路线ID',
    `routing_name` VARCHAR(255) DEFAULT NULL COMMENT '工艺路线名称',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态:0-待下发,1-已下发,2-生产中,3-已完成,4-已关闭',
    `priority` INT NOT NULL DEFAULT 5 COMMENT '优先级(1-10)',
    `plan_start_time` DATETIME NOT NULL COMMENT '计划开始时间',
    `plan_end_time` DATETIME NOT NULL COMMENT '计划结束时间',
    `actual_start_time` DATETIME DEFAULT NULL COMMENT '实际开始时间',
    `actual_end_time` DATETIME DEFAULT NULL COMMENT '实际结束时间',
    `workshop_id` BIGINT DEFAULT NULL COMMENT '车间ID',
    `workshop_name` VARCHAR(100) DEFAULT NULL COMMENT '车间名称',
    `line_id` BIGINT NOT NULL COMMENT '产线ID',
    `line_name` VARCHAR(100) DEFAULT NULL COMMENT '产线名称',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` BIT(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_order` (`tenant_id`, `order_no`, `deleted`),
    KEY `idx_tenant_status` (`tenant_id`, `status`),
    KEY `idx_tenant_line` (`tenant_id`, `line_id`),
    KEY `idx_tenant_time` (`tenant_id`, `plan_start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产工单表';
```

## 错误处理

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| `DB001` | 表名不符合命名规范 | 检查表名前缀和格式 |
| `DB002` | 缺少必需字段 | 确保包含 `id`、`tenant_id`、审计字段 |
| `DB003` | 索引缺少 `tenant_id` | 所有索引必须包含 `tenant_id` 作为第一列 |
| `DB004` | 文件命名不符合规范 | 使用 `{YYYY_MM_DD}-{表名}-{操作}[-{两位序号}][-{数据库标识}].sql` 格式，详见 `sql/README.md` |
| `DB005` | 唯一索引缺少 `deleted` | 唯一索引必须包含 `deleted` 字段 |
