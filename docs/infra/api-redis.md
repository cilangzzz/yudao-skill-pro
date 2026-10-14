# Redis 监控接口 (RedisController)

> 提供 Redis 服务器的实时运行状态监控，一次性返回 INFO 统计信息、key 数量以及各命令的调用与 CPU 消耗统计，用于管理后台的 Redis 监控页面。

## 接口路径前缀
/infra/redis  (Controller: RedisController)

## 1. 监控信息

### 1.1 获得 Redis 监控信息
- **路径**: GET /infra/redis/get-monitor-info
- **权限**: infra:redis:get-monitor-info
- **说明**: 获得 Redis 监控信息，包含 info 全量统计、key 数量和命令调用统计。

**请求参数**: 无

**响应**: CommonResult<RedisMonitorRespVO>

| 字段 | 类型 | 说明 |
|-----|------|-----|
| info | Properties | Redis info 指令结果，具体字段查看 Redis 官方文档 |
| dbSize | Long | Redis key 数量 |
| commandStats | List&lt;CommandStat&gt; | CommandStat 数组 |

CommandStat（Redis 命令统计结果，RedisMonitorRespVO 内嵌类）：

| 字段 | 类型 | 说明 |
|-----|------|-----|
| command | String | Redis 命令名，如 get |
| calls | Long | 调用次数 |
| usec | Long | 消耗 CPU 秒数 |

**业务逻辑**:
1. 该域没有独立 Service 层，逻辑直接在 RedisController 中基于 StringRedisTemplate 实现。
2. 通过 `RedisServerCommands::info` 执行 Redis INFO 指令，获得服务器全量统计信息（Properties）。
3. 通过 `RedisServerCommands::dbSize` 获得当前 Redis 中的 key 总数量。
4. 通过 `connection.serverCommands().info("commandstats")` 获得各命令调用统计的原始信息（Properties）。
5. 调用 RedisConvert#build 拼装结果：初始化 RedisMonitorRespVO，写入 info 与 dbSize。
6. 遍历 commandStats 的每一项：key 去除 `cmdstat_` 前缀得到命令名 command；从 value 中解析 `calls=` 与 `,` 之间的数值得到调用次数 calls；解析 `usec=` 与 `,` 之间的数值得到 CPU 消耗 usec。
7. 将全部 CommandStat 组装进响应 VO 并返回。
