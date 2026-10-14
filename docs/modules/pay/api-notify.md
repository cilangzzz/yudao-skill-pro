# 回调通知接口 (PayNotifyController)

> 提供支付渠道支付/退款/转账结果的统一回调入口，以及回调通知任务（`pay_notify_task`）与回调日志的管理后台查询能力。收到渠道回调后，支付系统会生成通知任务并按 15s/15s/30s/180s/30min/30min/30min/1h 的频率（共 9 次）不断 HTTP 回调业务系统的 `notifyUrl`，直到业务系统返回成功。

## 接口路径前缀

/pay/notify  (Controller: PayNotifyController)

## 1. 渠道回调（接收支付渠道异步通知）

三个端点供微信、支付宝等支付渠道服务器调用，均标注 `@PermitAll`（匿名可访问）+ `@TenantIgnore`（忽略租户），返回值为纯文本 `String`（成功时固定返回 `success`），**不使用 CommonResult 包装**。

### 1.1 统一【支付】回调

- **路径**: POST /pay/notify/order/{channelId}
- **权限**: @PermitAll（匿名访问，@TenantIgnore 忽略租户）
- **说明**: 接收支付渠道的支付结果异步通知，解析后更新支付单状态并触发对业务系统的支付成功通知。

**请求参数**: 无 ReqVO，参数由支付渠道回调报文决定

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| channelId | Long | 是 | @PathVariable | 渠道编号（路径参数） |
| params | Map&lt;String, String&gt; | 否 | @RequestParam | 回调 URL 查询参数（格式由具体渠道 SDK 定义） |
| body | String | 否 | @RequestBody | 回调请求体原文（格式由具体渠道 SDK 定义） |
| headers | Map&lt;String, String&gt; | 否 | @RequestHeader | 回调请求头 |

**响应**: String（固定返回 `success` 表示处理成功）

**业务逻辑**:
1. 根据路径参数 channelId 获取对应渠道的支付客户端 PayClient，找不到则记录错误日志并抛出 CHANNEL_NOT_FOUND 异常。
2. 调用 `payClient.parseOrderNotify(params, body, headers)` 将渠道回调报文解析为统一的 PayOrderRespDTO。
3. 调用 `orderService.notifyOrder(channelId, notify)` 处理支付结果：校验并更新支付单/拓展单状态，创建支付回调通知任务（notifyTask）异步通知业务系统。
4. 处理成功后向渠道返回 `success` 字符串（非 success 响应会导致渠道重试回调）。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |

### 1.2 统一【退款】回调

- **路径**: POST /pay/notify/refund/{channelId}
- **权限**: @PermitAll（匿名访问，@TenantIgnore 忽略租户）
- **说明**: 接收支付渠道的退款结果异步通知，解析后更新退款单状态并触发对业务系统的退款成功通知。

**请求参数**: 无 ReqVO，参数由支付渠道回调报文决定

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| channelId | Long | 是 | @PathVariable | 渠道编号（路径参数） |
| params | Map&lt;String, String&gt; | 否 | @RequestParam | 回调 URL 查询参数（格式由具体渠道 SDK 定义） |
| body | String | 否 | @RequestBody | 回调请求体原文（格式由具体渠道 SDK 定义） |
| headers | Map&lt;String, String&gt; | 否 | @RequestHeader | 回调请求头 |

**响应**: String（固定返回 `success` 表示处理成功）

**业务逻辑**:
1. 根据路径参数 channelId 获取对应渠道的支付客户端 PayClient，找不到则记录错误日志并抛出 CHANNEL_NOT_FOUND 异常。
2. 调用 `payClient.parseRefundNotify(params, body, headers)` 将渠道回调报文解析为统一的 PayRefundRespDTO。
3. 调用 `refundService.notifyRefund(channelId, notify)` 处理退款结果：校验并更新退款单状态，创建退款回调通知任务异步通知业务系统。
4. 处理成功后向渠道返回 `success` 字符串。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |

### 1.3 统一【转账】回调

- **路径**: POST /pay/notify/transfer/{channelId}
- **权限**: @PermitAll（匿名访问，@TenantIgnore 忽略租户）
- **说明**: 接收支付渠道的转账结果异步通知，解析后更新转账单状态并触发对业务系统的转账结果通知。

**请求参数**: 无 ReqVO，参数由支付渠道回调报文决定

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| channelId | Long | 是 | @PathVariable | 渠道编号（路径参数） |
| params | Map&lt;String, String&gt; | 否 | @RequestParam | 回调 URL 查询参数（格式由具体渠道 SDK 定义） |
| body | String | 否 | @RequestBody | 回调请求体原文（格式由具体渠道 SDK 定义） |
| headers | Map&lt;String, String&gt; | 否 | @RequestHeader | 回调请求头 |

**响应**: String（固定返回 `success` 表示处理成功）

**业务逻辑**:
1. 根据路径参数 channelId 获取对应渠道的支付客户端 PayClient，找不到则记录错误日志并抛出 CHANNEL_NOT_FOUND 异常。
2. 调用 `payClient.parseTransferNotify(params, body, headers)` 将渠道回调报文解析为统一的 PayTransferRespDTO。
3. 调用 `payTransferService.notifyTransfer(channelId, notify)` 处理转账结果：校验转账单状态（不处于待转账/转账中会报错）并更新状态，创建转账回调通知任务异步通知业务系统。
4. 处理成功后向渠道返回 `success` 字符串。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |
| 1_007_009_006 | 通知转账结果失败，原因：转账单不处于待转账 |
| 1_007_009_007 | 通知转账结果失败，原因：转账单不处于待转账或转账中 |

## 2. 回调通知任务查询

### 2.1 获得回调通知的明细

- **路径**: GET /pay/notify/get-detail
- **权限**: pay:notify:query
- **说明**: 获得指定回调通知任务的详情，包含任务信息与全部回调日志。

**请求参数**: 无 ReqVO，直接使用 Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 任务编号 |

**响应**: CommonResult&lt;PayNotifyTaskDetailRespVO&gt;（任务不存在时 data 为 null），字段继承 PayNotifyTaskRespVO 全部字段，另有：

| 字段 | 类型 | 说明 |
|------|-----|------|
| logs | List&lt;Log&gt; | 回调日志列表 |
| logs[].id | Long | 日志编号 |
| logs[].status | Byte | 通知状态 |
| logs[].notifyTimes | Byte | 当前通知次数 |
| logs[].response | String | HTTP 响应结果 |
| logs[].createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 根据 id 查询 PayNotifyTaskDO，任务不存在时直接返回 success(null)。
2. 根据 task.appId 查询支付应用 PayAppDO，获取应用名称 appName。
3. 根据 taskId 查询该任务的全部回调日志列表 PayNotifyLogDO（每次通知尝试一条记录）。
4. 将任务、应用名、日志列表组装为 PayNotifyTaskDetailRespVO 返回。

### 2.2 获得回调通知分页

- **路径**: GET /pay/notify/page
- **权限**: pay:notify:query
- **说明**: 分页获得回调通知任务列表，并拼接应用名称。

**请求参数 (PayNotifyTaskPageReqVO)**: 全部条件均为可选过滤项，继承 PageParam 的分页参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | @NotNull（PageParam 默认值 1） | 页码，从 1 开始 |
| pageSize | Integer | 否 | @NotNull（PageParam 默认值 10） | 每页条数 |
| appId | Long | 否 | 无 | 应用编号 |
| type | Integer | 否 | 无 | 通知类型（1 支付订单、2 退款、3 转账） |
| dataId | Long | 否 | 无 | 数据编号（按 type 关联支付单/退款单/转账单） |
| status | Integer | 否 | 无 | 通知状态（0 等待、10 成功、20 失败、21 请求成功但结果失败、22 请求失败） |
| merchantOrderId | String | 否 | 无 | 商户订单编号 |
| merchantRefundId | String | 否 | 无 | 商户退款编号 |
| merchantTransferId | String | 否 | 无 | 商户转账编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;PayNotifyTaskRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|-----|------|
| id | Long | 任务编号 |
| appId | Long | 应用编号 |
| appName | String | 应用名称（后端拼接） |
| type | Byte | 通知类型（1 支付订单、2 退款、3 转账） |
| dataId | Long | 数据编号（按 type 关联支付单/退款单/转账单编号） |
| merchantOrderId | String | 商户订单编号 |
| merchantRefundId | String | 商户退款编号 |
| merchantTransferId | String | 商户转账编号 |
| status | Byte | 通知状态（0 等待通知、10 通知成功、20 通知失败、21 请求成功但结果失败、22 请求失败） |
| nextNotifyTime | LocalDateTime | 下一次通知时间 |
| lastExecuteTime | LocalDateTime | 最后一次执行时间 |
| notifyTimes | Byte | 当前通知次数 |
| maxNotifyTimes | Byte | 最大可通知次数（固定 9 次） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 按分页与过滤条件查询回调通知任务分页数据。
2. 分页结果为空时直接返回空 PageResult。
3. 批量查询分页结果涉及的支付应用 Map，为每条记录拼接 appName。
4. 转换为 PayNotifyTaskRespVO 分页结果返回。

## 附：回调通知任务执行机制（PayNotifyServiceImpl）

任务的产生与执行不直接暴露 admin 端点，由渠道回调（见分组 1）与定时任务（PayNotifyJob 调用 `executeNotify()`）驱动：

1. **创建任务**（`createPayNotifyTask(type, dataId)`）：按通知类型（支付/退款/转账）查询对应业务单据，补充 appId、notifyUrl、商户单号等字段，插入 `pay_notify_task`（状态 WAITING、notifyTimes=0、maxNotifyTimes=9）。
2. **事务提交后异步通知**：通过 TransactionSynchronization 在事务 afterCommit 后调用 `executeNotifyAsync`，避免任务未入库就发起回调，且不阻塞当前事务。
3. **批量调度**（`executeNotify()`）：查询所有到达 nextNotifyTime 的待通知任务，提交到专用线程池并发执行，用 CountDownLatch 等待完成（总超时 120 秒，每秒打印一次剩余任务数）。
4. **加锁防并发**（`executeNotify(task)`）：以 Redis 分布式锁包裹，并通过比对 notifyTimes 与数据库值，避免同一任务被并发重复通知。
5. **发起 HTTP 回调**（`executeNotifyInvoke`）：按任务类型组装 PayOrderNotifyReqDTO / PayRefundNotifyReqDTO / PayTransferNotifyReqDTO 作为请求体，携带租户请求头，POST 到任务的 notifyUrl（超时 120 秒），将响应解析为 CommonResult。
6. **处理结果**（`processNotifyResult`）：回调返回 success 则任务置为 SUCCESS；失败时若已达最大次数（9 次）置为 FAILURE，否则按 NOTIFY_FREQUENCY（15s/15s/30s/180s/1800s/1800s/1800s/3600s）设置 nextNotifyTime 并置为 REQUEST_SUCCESS（响应失败）或 REQUEST_FAILURE（请求异常）状态等待重试。
7. **记录日志**：每次执行均插入一条 `pay_notify_log`，记录通知次数、状态与响应内容（异常时记录根因消息），可在 2.1 明细接口中查看。
