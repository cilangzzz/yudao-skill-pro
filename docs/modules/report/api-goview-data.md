# GoView 数据查询接口 (GoViewDataController)

> 为 GoView 大屏提供数据源查询能力，支持通过 SQL 直接查询项目数据源，并提供 HTTP 查询示例接口。

## 接口路径前缀

/report/go-view/data  (Controller: GoViewDataController)

## 1. 数据查询（GoViewDataController）

### 1.1 使用 SQL 查询数据

- **路径**: 任意 HTTP 方法（`@RequestMapping` 未限定，常用 POST） /report/go-view/data/get-by-sql
- **权限**: report:go-view-data:get-by-sql
- **说明**: 接收前端传入的 SQL 语句，在项目配置的默认数据源上执行查询，返回数据维度（列名）与数据明细列表，供 GoView 大屏图表渲染。

**请求参数 (GoViewDataGetBySqlReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| sql | String | 是 | @NotEmpty | SQL 语句，如 `SELECT * FROM user` |

**响应**: CommonResult<GoViewDataRespVO>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| dimensions | List&lt;String&gt; | 数据维度，即查询结果的全部列名 |
| source | List&lt;Map&lt;String, Object&gt;&gt; | 数据明细列表，每行为「列名 -&gt; 值」的 Map |

**业务逻辑** (GoViewDataServiceImpl):
1. 通过 `jdbcTemplate.queryForRowSet(sql)` 在项目配置的默认数据源上执行传入的 SQL，获得 `SqlRowSet` 结果集
2. 通过 `SqlRowSetMetaData` 解析结果集元数据，取全部列名数组作为数据维度 `dimensions`
3. 逐行遍历结果集，将每一行的各列以「列名 -&gt; 值」写入 Map，追加到 `source` 明细列表（使用 LinkedList，避免数据量不确定时的扩容复制开销）
4. 返回组装好的 GoViewDataRespVO

> 补充说明（来自 Service 实现）：默认使用 jdbcTemplate 查询项目配置的数据源；如需查询其它数据源，可新建对应数据源的 jdbcTemplate 来实现。默认数据源为 MySQL 关系型数据源，数据量较大时查询可能较慢，可考虑后续改用 ClickHouse 等分析型数据库。

### 1.2 使用 HTTP 查询数据

- **路径**: 任意 HTTP 方法（`@RequestMapping` 未限定，常用 POST） /report/go-view/data/get-by-http
- **权限**: report:go-view-data:get-by-http
- **说明**: 示例接口，返回固定维度加随机生成的模拟数据，演示 GoView 大屏数据源的对接格式；实际使用时应为每个查询编写真实的业务接口。

**请求参数**: 无固定 ReqVO —— 接口按需可选接收 query 参数 `params`（Map&lt;String, String&gt;，required = false）与请求体 `body`（String，required = false），两者仅作为示例占位，接口逻辑并不使用其内容。

**响应**: CommonResult<GoViewDataRespVO>

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| dimensions | List&lt;String&gt; | 固定为 `["日期", "PV", "UV"]`（PV 为每天访问次数，UV 为每天访问人数） |
| source | List&lt;Map&lt;String, Object&gt;&gt; | 12 条明细数据，覆盖 2021-01 至 2021-12 月份，PV 随机取值 1000~10000、UV 随机取值 100~1000 |

**业务逻辑** (Controller 内直接实现):
1. 新建 GoViewDataRespVO 响应对象
2. 设置数据维度 `dimensions` 为 `["日期", "PV", "UV"]`
3. 循环生成 12 个月份（2021-01 ~ 2021-12）的明细，随机生成 PV（1000~10000）与 UV（100~1000），以「日期/PV/UV」键值 Map 形式追加到 `source` 明细列表
4. 返回组装好的模拟数据结果
