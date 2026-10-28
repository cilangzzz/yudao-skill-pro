# AI1 首页统计接口 (Ai1HomeController)

> 提供 AI1 模块管理后台工作台首页的三类只读统计数据：资源总量（Agent / SKILL / MCP / 模型数量）、近 N 天每日消息趋势、近 N 天各 Agent 消息排行。该域没有独立 DO 与专属表，由 `Ai1HomeMapper` 用原生 `@Select` SQL 直接聚合各业务表，结果直接映射到响应 VO。

## 接口路径前缀

/ai1/home  (Controller: Ai1HomeController)

## 1. 资源总量统计

### 1.1 获得总量统计

- **路径**: GET /ai1/home/summary
- **权限**: ai1:home:query
- **说明**: 获得 Agent、SKILL、MCP、模型四类资源的总量统计（仪表盘统计卡片数据）

**请求参数**: 无

**响应**: CommonResult\<Ai1HomeSummaryRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| agentCount | Long | Agent 数量 |
| skillCount | Long | SKILL 数量 |
| mcpCount | Long | MCP 数量 |
| modelCount | Long | 模型数量 |

**业务逻辑**:
1. Controller 无请求参数，直接委托 `Ai1HomeService#getSummary()`，`Ai1HomeServiceImpl` 直通 `Ai1HomeMapper#selectSummary()`。
2. Mapper 用一条 `@Select` SQL 内 4 个标量子查询分别 `COUNT(1)` `ai1_agent`、`ai1_skill`、`ai1_mcp`、`ai1_model` 四张表，一次 DB 往返拿齐 4 个总量；每个子查询手写 `deleted = FALSE`（原生 SQL 不走 MyBatis-Plus 的逻辑删除自动拼接）。
3. 聚合列别名 `agentCount` / `skillCount` / `mcpCount` / `modelCount` 与 `Ai1HomeSummaryRespVO` 字段同名，MyBatis 按别名直接完成映射，无需中间转换层。
4. 无事务、无缓存、无错误码分支；租户隔离依赖 `TenantLineInnerInterceptor` 对 SQL 的自动改写（相关 DO 均继承 `TenantBaseDO`，SQL 未手写 tenant_id 条件）。

## 2. 消息统计

### 2.1 获得按日消息统计

- **路径**: GET /ai1/home/message-summary-by-date
- **权限**: ai1:home:query
- **说明**: 近 days 个自然日（含今天）每日消息数量，没有消息的日期补 0，按日期升序（消息趋势折线图数据）

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| days | Integer | 否 | @RequestParam(defaultValue="30")、@Min(1)、@Max(30) | 天数，1 ~ 30，默认 30 |

**响应**: CommonResult\<List\<Ai1HomeMessageSummaryByDateRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| date | String | 日期，格式 yyyy-MM-dd |
| count | Long | 当日消息数量 |

**业务逻辑**:
1. `Ai1HomeController` 类级 `@Validated` 配合方法参数上的 `@Min(1)` / `@Max(30)` 完成 days 校验（校验只在 Controller 层，Service 层不设防）。
2. 时间区间计算：`endTime = getDayEndTime(now)`（`LocalTime.MAX`，即当日 23:59:59.999999999），`beginTime = getDayBeginTime(endTime.minusDays(days - 1L))`，形成含今天在内、共 days 个自然日的闭区间。
3. 调用 `Ai1HomeMapper#selectMessageSummaryListByCreateTimeBetweenGroupByDate(beginTime, endTime)`：`SELECT CAST(create_time AS DATE) AS date, COUNT(1) AS count FROM ai1_session_message WHERE create_time BETWEEN #{beginTime} AND #{endTime} AND deleted = FALSE GROUP BY CAST(create_time AS DATE) ORDER BY date`。注释明确用 `CAST(create_time AS DATE)` 而非 `DATE(create_time)`，以兼容 MySQL 与 H2（单测 `BaseDbUnitTest` 跑 H2 内存库）；仅返回有消息的日期。
4. `Ai1HomeServiceImpl#getMessageSummaryByDate` 先用 `CollectionUtils.convertMap` 把查询结果转成「日期 -> 数量」Map，再 for 循环 days 次，用 `LocalDateTimeUtil.format(beginTime.plusDays(i), DatePattern.NORM_DATE_FORMATTER)` 生成连续日期，`countMap.getOrDefault(date, 0L)` 为没有消息的日期补 0。最终返回列表长度恒等于 days、按日期升序，保证前端折线图 X 轴连续不断点。
5. 统计口径：不区分消息角色（user / assistant）与状态（生成中 / 完成 / 失败），失败消息与「生成中」占位消息同样计入；调整口径需改 Mapper 的 SQL，而非枚举判断。

### 2.2 获得按 Agent 消息统计

- **路径**: GET /ai1/home/message-summary-by-agent
- **权限**: ai1:home:query
- **说明**: 近 days 个自然日（含今天）各 Agent 的消息数量，按数量倒序（消息排行数据）

**请求参数**: Query 参数（同 2.1）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| days | Integer | 否 | @RequestParam(defaultValue="30")、@Min(1)、@Max(30) | 天数，1 ~ 30，默认 30 |

**响应**: CommonResult\<List\<Ai1HomeMessageSummaryByAgentRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| agentId | Long | Agent 编号 |
| agentName | String | Agent 名称，Agent 已删除时为空 |
| count | Long | 消息数量 |

**业务逻辑**:
1. 时间区间计算同 2.1，`Ai1HomeServiceImpl#getMessageSummaryByAgent` 纯透传给 Mapper。
2. 调用 `Ai1HomeMapper#selectMessageSummaryListByCreateTimeBetweenGroupByAgentId(beginTime, endTime)`：`ai1_session_message m INNER JOIN ai1_session c ON m.session_id = c.id AND c.deleted = FALSE WHERE m.create_time BETWEEN ... AND m.deleted = FALSE GROUP BY c.agent_id ORDER BY count DESC, c.agent_id`。已删除会话（`c.deleted = TRUE`）下的消息不计入；SQL 只 INNER JOIN 会话表、不 JOIN `ai1_agent`，因此已删除 Agent 名下的未删除会话消息仍计入排行。
3. Controller 私有方法 `buildMessageSummaryByAgentRespVOList` 回填 Agent 名称：`convertSet(list, Ai1HomeMessageSummaryByAgentRespVO::getAgentId)` 取 agentId 集合 → `Ai1AgentService#getAgentMap(ids)`（接口 default 方法，`convertMap(getAgentList(ids), Ai1AgentDO::getId)`，逻辑删除自动过滤）→ 逐项 `MapUtils.findAndThen(agentMap, agentId, agent -> item.setAgentName(agent.getName()))` 回填名称。
4. Agent 已删除或不存在时，`findAndThen` 不命中，`agentName` 保持 null，该统计行仍返回——刻意不 JOIN `ai1_agent` 回填名称，否则已删除 Agent 的统计行会被 INNER JOIN 过滤掉而丢失消息计数；前端需容忍 `agentName` 为空的行。

## 3. 数据来源与实现要点

### 3.1 无 DO 的统计 Mapper

home 域在 `dal/dataobject` 下没有 home 包、不建实体表：`Ai1HomeMapper` 不继承 MyBatis-Plus `BaseMapperX`，纯 `@Select` 原生 SQL 聚合，结果按列别名直接映射到 `controller/admin/home/vo` 下的 Response VO。统计涉及的表如下：

| 表 | 说明 | home 域的使用方式 |
|-----|------|------------------|
| ai1_agent | Agent 表 | 标量子查询 COUNT；按 Agent 统计经 `Ai1AgentService#getAgentMap` 回填 name |
| ai1_skill | SKILL 表 | 标量子查询 COUNT |
| ai1_mcp | MCP 表 | 标量子查询 COUNT |
| ai1_model | 模型表 | 标量子查询 COUNT |
| ai1_session_message | 会话消息表 | 按 create_time 统计消息数量（不区分 role / status） |
| ai1_session | 会话表 | 按 Agent 统计时 INNER JOIN 过滤会话归属与 deleted |

### 3.2 原生 SQL 的逻辑删除与租户隔离

`Ai1HomeMapper` 三条 `@Select` 均手写 `deleted = FALSE`（含子查询与 JOIN 侧），漏写即引入脏数据，是复制此类 SQL 时最需核对的点。相关表对应的 DO（`Ai1AgentDO`、`Ai1SessionMessageDO` 等）均继承 `TenantBaseDO`，但 SQL 未写 tenant_id，租户隔离完全依赖 `TenantLineInnerInterceptor` 对 `@Select` 的自动改写；若统计逻辑被搬到无租户上下文的场景（定时 Job、异步线程）需自行评估。

### 3.3 实时聚合，无缓存

统计表数据由其他域写入（会话消息由 session 域流式生成），home 每次请求实时 COUNT，无 `@Cacheable`、无定时预聚合。多租户大消息量下按 `CAST(create_time AS DATE)` 分组可能触发临时表/filesort，数据量大时需再考虑缓存或预聚合，当前代码无此设计。

### 3.4 错误码

home 域三个接口均为只读统计，无异常分支，不使用 `Ai1ErrorCodeConstants` 中任何错误码（模块统一错误码段为 1-041-000-000，见 `enums/Ai1ErrorCodeConstants`）。参数校验失败（days 超出 1 ~ 30）由框架统一返回 400 参数错误。

## 相关文档

- [README.md](README.md) - ai1 模块文档索引
- [api-session.md](api-session.md) - 会话与消息（home 的消息趋势 / 排行统计直接聚合 ai1_session_message）
- [data-model.md](data-model.md) - 数据模型详情（ai1_agent / ai1_skill / ai1_mcp / ai1_model / ai1_session / ai1_session_message 表结构）
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南（无 DO 统计 Mapper、时序缺口补零、名称回填等模式，新增统计卡片步骤）
- [pitfalls.md](pitfalls.md) - 已知踩坑点（days 校验只在 Controller 层、统计口径、agentName 可为空等）
