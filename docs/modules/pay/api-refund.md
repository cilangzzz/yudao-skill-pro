# 退款订单接口 (PayRefundController)

> 提供管理后台对支付退款单的查询、分页与 Excel 导出能力；退款单的创建（发起退款）由业务侧通过 `PayRefundApi` 触发，退款结果由渠道回调异步更新。

## 接口路径前缀

/pay/refund  (Controller: PayRefundController)

## 1. 退款订单查询与导出

### 1.1 获得退款订单

- **路径**: GET /pay/refund/get
- **权限**: pay:refund:query
- **说明**: 按编号获得退款单详情，并拼接应用名称、支付订单商品标题等信息。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| id | Long | 是 | @RequestParam(required = true) | 退款单编号 |

**响应**: CommonResult&lt;PayRefundDetailsRespVO&gt;

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 支付退款编号 |
| no | String | 外部退款号（退款单号） |
| appId | Long | 应用编号 |
| appName | String | 应用名称 |
| channelId | Long | 渠道编号 |
| channelCode | String | 渠道编码 |
| orderId | Long | 支付订单编号 |
| merchantOrderId | String | 商户订单编号 |
| merchantRefundId | String | 商户退款订单号 |
| notifyUrl | String | 异步通知地址 |
| status | Integer | 退款状态（0-未退款/等待 1-成功 2-失败，见 PayRefundStatusEnum） |
| payPrice | Long | 支付金额（单位分） |
| refundPrice | Long | 退款金额（单位分） |
| reason | String | 退款原因 |
| userIp | String | 用户 IP |
| channelOrderNo | String | 渠道订单号 |
| channelRefundNo | String | 渠道退款单号 |
| successTime | LocalDateTime | 退款成功时间 |
| channelErrorCode | String | 调用渠道的错误码 |
| channelErrorMsg | String | 调用渠道的错误提示 |
| channelNotifyData | String | 支付渠道的额外参数 |
| order.subject | String | 支付订单商品标题（嵌套 Order 对象） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**: 1. 按 id 查询退款单 PayRefundDO，不存在则返回空对象 PayRefundDetailsRespVO；2. 根据退款单的 appId 查询支付应用 PayAppDO；3. 通过 PayRefundConvert 将退款单与应用信息拼接为 PayRefundDetailsRespVO（含应用名称、订单商品标题）返回。

### 1.2 获得退款订单分页

- **路径**: GET /pay/refund/page
- **权限**: pay:refund:query
- **说明**: 分页查询退款单列表，并批量拼接应用名称。

**请求参数 (PayRefundPageReqVO)**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| appId | Long | 否 | 无 | 应用编号 |
| channelCode | String | 否 | 无 | 渠道编码 |
| merchantOrderId | String | 否 | 无 | 商户支付单号 |
| merchantRefundId | String | 否 | 无 | 商户退款单号 |
| channelOrderNo | String | 否 | 无 | 渠道支付单号 |
| channelRefundNo | String | 否 | 无 | 渠道退款单号 |
| status | Integer | 否 | 无 | 退款状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围（起止区间） |
| pageNo | Integer | 是 | @NotNull + @Min(1)（继承 PageParam） | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull + @Min(1) + @Max(200)（继承 PageParam） | 每页条数，默认 10 |

**响应**: CommonResult&lt;PageResult&lt;PayRefundPageItemRespVO&gt;&gt;，列表项字段如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 支付退款编号 |
| no | String | 外部退款号（退款单号） |
| appId | Long | 应用编号 |
| appName | String | 应用名称 |
| channelId | Long | 渠道编号 |
| channelCode | String | 渠道编码 |
| orderId | Long | 支付订单编号 |
| merchantOrderId | String | 商户订单编号 |
| merchantRefundId | String | 商户退款订单号 |
| notifyUrl | String | 异步通知地址 |
| status | Integer | 退款状态 |
| payPrice | Long | 支付金额（单位分） |
| refundPrice | Long | 退款金额（单位分） |
| reason | String | 退款原因 |
| userIp | String | 用户 IP |
| channelOrderNo | String | 渠道订单号 |
| channelRefundNo | String | 渠道退款单号 |
| successTime | LocalDateTime | 退款成功时间 |
| channelErrorCode | String | 调用渠道的错误码 |
| channelErrorMsg | String | 调用渠道的错误提示 |
| channelNotifyData | String | 支付渠道的额外参数 |
| createTime | LocalDateTime | 创建时间 |

（字段继承自 PayRefundBaseVO）

**业务逻辑**: 1. 按 PayRefundPageReqVO 条件分页查询退款单；2. 结果为空时直接返回仅含 total 的空分页；3. 收集分页结果中的 appId 集合，批量查询应用得到 appMap；4. 通过 PayRefundConvert.convertPage 将退款单与应用信息拼接为 PayRefundPageItemRespVO 分页返回。

### 1.3 导出退款订单 Excel

- **路径**: GET /pay/refund/export-excel
- **权限**: pay:refund:export（操作日志类型为 EXPORT）
- **说明**: 按与分页相同的筛选条件查询全部退款单，导出为 Excel 文件。

**请求参数 (PayRefundExportReqVO)**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| appId | Long | 否 | 无 | 应用编号 |
| channelCode | String | 否 | 无 | 渠道编码 |
| merchantOrderId | String | 否 | 无 | 商户支付单号 |
| merchantRefundId | String | 否 | 无 | 商户退款单号 |
| channelOrderNo | String | 否 | 无 | 渠道支付单号 |
| channelRefundNo | String | 否 | 无 | 渠道退款单号 |
| status | Integer | 否 | 无 | 退款状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围（起止区间） |

（参数与 PayRefundPageReqVO 一致，但不含分页参数）

**响应**: 无 CommonResult 包装，直接向 HttpServletResponse 写出 Excel 文件（文件名「退款订单.xls」，sheet「数据」）。列结构（PayRefundExcelVO）：

| 列名 | 类型 | 说明 |
|---|---|---|
| 支付退款编号 | Long | id |
| 创建时间 | LocalDateTime | createTime |
| 支付金额 | Integer | payPrice，经 MoneyConvert 分转元 |
| 退款金额 | Integer | refundPrice，经 MoneyConvert 分转元 |
| 商户退款单号 | String | merchantRefundId |
| 退款单号 | String | no |
| 渠道退款单号 | String | channelRefundNo |
| 商户支付单号 | String | merchantOrderId |
| 渠道支付单号 | String | channelOrderNo |
| 退款状态 | Integer | status，经 DictConvert 按字典 pay_refund_status 转换 |
| 退款渠道 | String | channelCode，经 DictConvert 按字典 pay_channel_code 转换 |
| 成功时间 | LocalDateTime | successTime |
| 支付应用 | String | appName |
| 退款原因 | String | reason |

**业务逻辑**: 1. 按 PayRefundExportReqVO 条件查询全部满足条件的退款单列表；2. 收集列表中的 appId 集合，批量查询应用得到 appMap；3. 通过 PayRefundConvert.convertList 将退款单与应用信息拼接为 PayRefundExcelVO 列表（金额分转元、状态/渠道转字典标签）；4. 通过 ExcelUtils.write 将列表写出为「退款订单.xls」文件流返回。

## 2. 补充：退款单核心业务流程（非 admin 端点，来自 PayRefundServiceImpl）

退款单的管理端点均为只读查询；退款单的产生与状态流转在 Service 内部完成，流程如下：

1. **发起退款 createRefund**（由业务方通过 PayRefundApi 调用）：校验 App（validPayApp）→ 校验支付订单可退款（订单必须存在、状态为已支付或已退款、累计退款金额不超订单金额、无进行中的退款单）→ 校验支付渠道有效并获取 PayClient → 校验同一 merchantRefundId 的退款单不存在 → 生成退款单号（Redis 前缀序号）插入状态为「等待」的退款单 → 调用渠道 unifiedRefund 发起退款（渠道调用异常仅记录日志不抛出，结果由回调或轮询补偿获得）→ 处理渠道返回结果 notifyRefund。
2. **退款结果通知 notifyRefund**：校验渠道有效性后按渠道租户上下文更新退款单；成功则更新退款单为「成功」（记录成功时间、渠道退款单号、渠道通知原文），并更新支付订单已退款金额、插入退款通知任务（PayNotifyTypeEnum.REFUND）；失败则更新退款单为「失败」（记录渠道错误码/错误信息），同样插入退款通知任务。更新采用乐观锁（updateByIdAndStatus，仅允许从「等待」状态变更，重复通知幂等返回）。
3. **退款状态轮询补偿 syncRefund**：定时任务查询指定创建时间内仍处于「等待」状态的退款单，逐个通过渠道 PayClient.getRefund 查询渠道侧结果，并复用 notifyRefund 更新状态，返回同步成功的条数。

**错误码**: 该域相关错误码（pay 模块 1-007-000-000 段，主要在退款创建与回调流程中抛出）：

| 错误码 | 说明 |
|---|---|
| 1_007_000_000 | App 不存在 |
| 1_007_000_002 | App 已经被禁用 |
| 1_007_001_000 | 支付渠道的配置不存在 |
| 1_007_001_001 | 支付渠道已经禁用 |
| 1_007_002_000 | 支付订单不存在 |
| 1_007_002_005 | 支付订单退款失败，原因：状态不是已支付或已退款 |
| 1_007_006_000 | 退款金额超过订单可退款金额 |
| 1_007_006_002 | 已经有退款在处理中 |
| 1_007_006_003 | 已经存在退款单 |
| 1_007_006_004 | 支付退款单不存在 |
| 1_007_006_005 | 支付退款单不处于待退款 |
