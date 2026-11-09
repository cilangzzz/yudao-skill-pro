# MES 已知坑点与注意事项 (mes)

> 本文档汇总 `mes` 模块的已知坑点，重点覆盖多数据库（MySQL / PostgreSQL / Oracle / SQL Server）SQL 兼容约定与失败场景。代码模式见 [code-patterns.md](code-patterns.md)，数据模型见 [data-model.md](data-model.md)。

## 1. 多数据库 SQL 兼容

### 1.1 `setIncrBy` 不再对 NULL 兜底，累加依赖列 `NOT NULL DEFAULT 0`

- **变更**：生产任务与生产工单的产量累加，由 MySQL 专用写法 `setSql("produced_quantity = IFNULL(produced_quantity, 0) + n")` 改为 MyBatis-Plus `LambdaUpdateWrapper#setIncrBy`，生成标准 SQL `col = col + ?`。
- **源码**：`MesProTaskMapper#updateProducedQuantity`（`dal/mysql/pro/task/MesProTaskMapper.java:63-67`）、`MesProWorkOrderMapper#updateProducedQuantity`（`dal/mysql/pro/workorder/MesProWorkOrderMapper.java:39-41`）。
- **风险**：新写法不做 NULL 兜底。若线上库该列仍允许 NULL 且存在 NULL 历史数据，`NULL + n` 结果仍为 NULL——**不会报错，但产量不增长**。
- **契约**：单测建表已把 `produced_quantity` / `qualify_quantity` / `unqualify_quantity` 改为 `NOT NULL DEFAULT 0`（`src/test/resources/sql/create_tables.sql:759-761`），`mes_pro_work_order.quantity_produced` 同理（同文件 `:793`）。
- **行动项**：切换到 PostgreSQL / Oracle / SQL Server 等多库环境前，先核对线上表结构是否同样为 `NOT NULL DEFAULT 0`，并对历史 NULL 数据做 `UPDATE ... SET col = 0 WHERE col IS NULL`。

### 1.2 `SqlDialectUtils.formatDate` 的列名走白名单，业务值必须用 `#{}`

- **用法**：在 XML 中以 OGNL 静态方法形式注入 SQL 片段：`${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@formatDate('feedback_time')}`。
- **源码**：`SqlDialectUtils.formatDate`（`yudao-spring-boot-starter-mybatis/.../SqlDialectUtils.java:148-170`），列名校验 `checkColumn`（同文件 `:967`）内部调用 `MyBatisUtils.isSafeColumnName`。
- **坑点**：`formatDate` 使用 `${}` 直接拼进 SQL，列名必须是代码中写死的常量并通过白名单校验，否则抛 `IllegalArgumentException("Invalid column name: ...")`。**绝不能**把用户输入或请求参数放到列名位置；业务值仍必须用 `#{}` 绑定。
- **方言输出**：MySQL `DATE_FORMAT(col, '%Y-%m-%d')`；PostgreSQL / Oracle `TO_CHAR(col, 'YYYY-MM-DD')`；SQL Server `CONVERT(varchar(10), col, 23)`。

### 1.3 方言按执行数据源识别并缓存，识别失败会抛异常

- **源码**：`SqlDialectUtils.getDialect()`（`SqlDialectUtils.java:809-844`）。事务内复用事务连接识别方言，非事务按路由后的数据源实例缓存。
- **坑点**：读取元数据失败或数据源不可用会抛 `IllegalStateException("获取数据库方言失败")`；新增涉及日期 / JSON / 行数限制的 SQL 片段时，**不要硬编码 MySQL 函数**，统一复用 `SqlDialectUtils` 与 `BaseMapperX`。

### 1.4 按日聚合必须复用 `GROUP BY` 表达式，返回 Map 依赖大小写不敏感结果集

- **源码**：`MesHomeStatisticsMapper.xml#selectDailyFeedbackTrend`（`src/main/resources/mapper/home/MesHomeStatisticsMapper.xml:55-67`）。
- **坑点**：
  - `GROUP BY` 必须复用与 `SELECT` 相同的 `formatDate('feedback_time')` 表达式，`ORDER BY` 才能引用输出别名 `statDate`。
  - 查询 `resultType` 为 `CaseInsensitiveResultMap`，`MesHomeStatisticsServiceImpl` 用 `row.get("statDate")` 取值（`service/home/MesHomeStatisticsServiceImpl.java:124`）；若换成普通 Map，列别名大小写不匹配会导致取不到值。
  - 空值聚合统一用标准 `COALESCE(...)`，已不再使用 MySQL 专有的 `IFNULL`。

### 1.5 布尔列类型不统一：`bit(1)` 绑定 Boolean，`tinyint(1)` 用数值 1

- **源码**：`MesQcPendingInspectMapper.xml`。
- **区别**：
  - IQC / RQC 分支的 `iqc_check_flag` / `rqc_check_flag` 是 `bit(1)`，必须用 `<bind name="trueValue" value="true"/>` + `#{trueValue}` 绑定 Boolean（同文件 `:17`、`:37`、`:62`、`:137`、`:163`）。
  - OQC 分支的 `oqc_check_flag` 是 `tinyint(1)`，仍按数值 `1` 比较（同文件 `:111`）。
- **失败场景**：把 `bit(1)` 列与数字 `1` 直接比较，在 PostgreSQL 等数据库上会报类型不匹配错误。

### 1.6 多分支 UNION 的"无值"列必须用带类型 NULL

- **源码**：`MesQcPendingInspectMapper.xml` 6 个 UNION 分支。
- **写法**：不能写裸 `NULL AS workOrderId`，必须写 `CASE WHEN 1 = 0 THEN <本分支 bigint 列> END AS workOrderId`（示例见同文件 `:30-33`、`:55-58`、`:79-83`、`:104-107`、`:129-133`、`:155-158`）。
- **原因**：PostgreSQL / Oracle 等会按第一个分支推断列类型，裸 NULL 会让后续分支的 bigint 值出现类型转换异常；`CASE WHEN 1 = 0` 永不命中，但能让数据库推导出与该分支列一致的 bigint 类型。

### 1.7 `selectFirstOne` / `selectListLimitN` 不能再追加 `last("LIMIT 1")`

- **源码**：`BaseMapperX#selectFirstOne`（`BaseMapperX.java:368`）、`BaseMapperX#selectListLimitN`（同文件 `:384`）。内部走 MyBatis-Plus 分页插件，按方言生成 `LIMIT` / `ROWNUM` / `OFFSET FETCH`，且**不执行 COUNT**。
- **坑点**：
  - 不要再对同一个 `queryWrapper` 追加 `last("LIMIT 1")`，否则与分页插件生成的行数限制冲突。
  - SQL Server 的分页语句要求必须带 `ORDER BY`，扩展批次 FIFO 查询时需保留 `orderByAsc(id)`（`MesWmBatchMapper.java:134-136`）。

### 1.8 模糊查询用 `<bind>` 拼接，不要用 `CONCAT`

- **源码**：`MesQcPendingInspectMapper.xml:170-172`。
- **写法**：`<bind name="sourceDocCodeLike" value="'%' + sourceDocCode + '%'"/>` + `LIKE #{sourceDocCodeLike}`。
- **原因**：部分数据库不支持 `CONCAT` 或语义有差异（如 SQL Server 需 `+`），用 `<bind>` 在 MyBatis 侧拼接通配符最稳妥。

## 2. 数据模型与实体约定

| 约定 | 说明 |
|------|------|
| 全部继承 `BaseDO` | 133 个 DO 均直接继承 `BaseDO`，无 `TenantBaseDO`；模块未启用租户隔离 |
| 主键序列 | 每个 DO 配置 `@KeySequence("mes_xxx_seq")`，兼容 Oracle / PostgreSQL 等序列型数据库 |
| 逻辑删除 | 统一 `deleted` 布尔列，`@TableLogic` 自动追加 `deleted = 0` |
| 列名映射 | 未用 `@TableField` 指定列名，按驼峰转下划线映射；改动字段名会直接改变数据库列名 |
| 集合字段 | 仅 `mes_qc_template.types` 使用 `IntegerListTypeHandler`，以逗号分隔存储 `List<Integer>` |
| 单据结构 | 出入库单统一「主表-行-明细」三段式，明细行锁定来源库存，数量变动统一写 `mes_wm_transaction` 事务流水 |

## 3. 本次变更的对外契约影响

以下对外行为**均未变化**，相关 api 文档无需修改：

- 首页生产趋势 `GET /mes/home-statistics/production-trend`：内部聚合结果 Map 的日期键由 `date` 改为 `statDate`，但对外 VO 字段仍为 `date`（`MesHomeProductionTrendRespVO`，由 `MesHomeStatisticsServiceImpl.java:134` 设置），响应契约不变。
- 待检任务 `GET /mes/qc/pending-inspect/page`：仅改 SQL 写法（Boolean 绑定 / 带类型 NULL / `<bind>` 模糊），响应 VO 字段与权限标识 `mes:qc-pending-inspect:query` 不变。
- 排班计划班组列表 `GET /mes/cal/plan-team/list-by-plan`：内部改用 `MapUtils.findAndThen` 批量回填 `teamCode`/`teamName` 并增加空列表提前返回（`controller/admin/cal/plan/MesCalPlanTeamController.java:59-71`），对外行为不变——关联班组不存在时 `teamCode`/`teamName` 仍为 `null`。
