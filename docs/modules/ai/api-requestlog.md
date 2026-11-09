# AI 请求日志接口 (AiRequestLogController)

> AI 请求日志用于记录每一次业务生成尝试（聊天回复、写作、思维导图）的模型调用情况：调用平台、模型、耗时、状态（成功/失败/取消）、错误信息与 Token 用量。日志由业务 Service 在调用模型前后自动写入，本域仅提供后台查询与统计接口。

## 接口路径前缀

/ai/request-log  (Controller: AiRequestLogController)

> 三个接口均为管理端接口，统一需要 `ai:request-log:query` 权限。仓库 SQL 中暂无对应的菜单/按钮数据，使用前需按菜单权限流程补充菜单（详见 [pitfalls.md](pitfalls.md)）。

---

## 1. 获得单条请求日志

- **路径**: GET /ai/request-log/get
- **权限**: ai:request-log:query
- **说明**: 按编号查询单条 AI 请求日志，并补齐用户昵称。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 请求日志编号 |

**响应**: CommonResult\<AiRequestLogRespVO\>（记录不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| requestId | String | 请求编号（服务端在调用模型前生成的本地 UUID，与厂商响应 id 不同） |
| userId | Long | 用户编号 |
| userNickname | String | 用户昵称（通过 AdminUserApi 补齐；用户不存在时为空，前端可退化为展示 userId） |
| bizType | Integer | 业务类型，枚举 `AiRequestLogBizTypeEnum`：1 聊天、2 写作、3 思维导图 |
| bizId | Long | 业务编号（聊天为 assistant 消息 id、写作为 ai_write.id、思维导图为 ai_mind_map.id） |
| platform | String | 平台（调用时快照） |
| modelId | Long | 模型编号（调用时快照） |
| model | String | 模型标识（调用时快照，冗余 `AiModelDO.model`） |
| status | Integer | 状态，枚举 `AiRequestLogStatusEnum`：20 成功、30 失败、40 取消 |
| errorMessage | String | 错误信息（失败时记录异常 message，为空时记录异常类名） |
| beginTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| duration | Long | 耗时（毫秒，endTime - beginTime） |
| inputTokens | Long | 输入 Token 数，未知为空 |
| outputTokens | Long | 输出 Token 数，未知为空 |
| totalTokens | Long | 合计 Token 数，输入、输出都已知时才有值，否则为空 |
| responseMetadata | Map\<String, Object\> | 响应元数据 JSON 快照（含 id、model、usage、rateLimit、generations 等） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询日志，不存在直接返回 null；2. 通过 `AdminUserApi.getUserMap` 批量补齐 `userNickname`；3. 转换为 RespVO 返回。

---

## 2. 获得请求日志分页

- **路径**: GET /ai/request-log/page
- **权限**: ai:request-log:query
- **说明**: 按条件分页查询请求日志，按 id 倒序返回。

**请求参数 (AiRequestLogPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo / pageSize | Integer | 否 | 继承 PageParam（默认 1 / 10） | 分页参数 |
| requestId | String | 否 | - | 请求编号（精确匹配） |
| userId | Long | 否 | - | 用户编号 |
| bizType | Integer | 否 | @InEnum(AiRequestLogBizTypeEnum) | 业务类型：1 聊天、2 写作、3 思维导图 |
| platform | String | 否 | - | 平台（精确匹配） |
| modelId | Long | 否 | - | 模型编号 |
| model | String | 否 | - | 模型标识（模糊匹配） |
| status | Integer | 否 | @InEnum(AiRequestLogStatusEnum) | 状态：20 成功、30 失败、40 取消 |
| beginTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 开始时间区间 |

**响应**: CommonResult\<PageResult\<AiRequestLogRespVO\>\>（列表项字段同第 1 节）

**业务逻辑**: 1. 按上述条件（`eqIfPresent`/`likeIfPresent`/`betweenIfPresent`）构造查询；2. 按 `id` 倒序分页；3. 批量补齐用户昵称后返回。

---

## 3. 获得请求日志统计

- **路径**: GET /ai/request-log/statistics
- **权限**: ai:request-log:query
- **说明**: 统计全部匹配筛选条件的请求日志，不受分页参数影响。

**请求参数 (AiRequestLogPageReqVO)**: 筛选条件与第 2 节完全一致（pageNo/pageSize 不参与统计）。

**响应**: CommonResult\<AiRequestLogStatisticsRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| requestCount | Long | 请求总数 |
| successCount | Long | 成功数（status=20） |
| failCount | Long | 失败数（status=30） |
| cancelCount | Long | 取消数（status=40） |
| inputTokens | Long | 已知输入 Token 合计；没有任何已知值时为空 |
| outputTokens | Long | 已知输出 Token 合计；没有任何已知值时为空 |
| totalTokens | Long | 完整用量记录的合计 Token（仅输入、输出、合计都已知的记录参与）；没有完整用量记录时为空 |
| knownUsageCount | Long | 完整用量条数（input_tokens、output_tokens、total_tokens 均非空） |
| unknownUsageCount | Long | 用量不完整或未知条数 = requestCount - knownUsageCount |

**业务逻辑**: 1. 用与分页相同的筛选条件构造聚合 SQL（COUNT、按状态分类的 SUM、SUM 输入/输出、仅完整用量记录参与合计 Token 的 SUM）；2. 计数无记录时为 0，`SUM` 无已知值时为 null；3. 计算 `unknownUsageCount` 后返回。

---

## 4. 日志的写入时机与数据来源

> 本域没有写接口，日志由业务侧通过 `AiRequestLogService` 写入。

| 业务类型 | 触发接口 | 写入内容 |
|---------|---------|---------|
| 聊天（1） | `/ai/chat/message/send`、`/ai/chat/message/send-stream` | 每个 assistant 消息对应一次尝试；同步接口在 call 前后记录 SUCCESS/FAIL，流式在结束回调记录 SUCCESS/FAIL(异常)/CANCEL(取消) |
| 写作（2） | `/ai/write/generate-stream` | 每条 `ai_write` 记录对应一次尝试，流式结束回调记录 SUCCESS/FAIL/CANCEL |
| 思维导图（3） | `/ai/mind-map/generate-stream` | 每条 `ai_mind_map` 记录对应一次尝试，流式结束回调记录 SUCCESS/FAIL/CANCEL |

关键行为：

1. **独立事务写入**：`AiRequestLogServiceImpl#createRequestLog` 使用 `Propagation.REQUIRES_NEW`，业务事务回滚后日志仍保留，便于排查失败调用。
2. **租户隔离执行**：日志插入时按请求开始时捕获的 `tenantId` 执行 `TenantUtils.execute(tenantId, ...)`；Flux 异步回调中不再使用 `executeIgnore`。
3. **用量快照**：Token 用量来自 `AiUsageUtils.extractUsage`，未知返回 null、不做估算；流式用量按请求日志的最新整体快照（非逐块累加），合计 Token 仅输入、输出都已知时计算。
4. **元数据快照**：`responseMetadata` 由 `AiUsageUtils.extractResponseMetadata` 生成，流式按 generation 的 index 合并、错误信息去重追加。

**错误码**: 本域接口本身不抛业务异常（仅分页参数校验），无专属错误码。
