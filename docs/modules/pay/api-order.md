# 支付订单接口 (PayOrderController)

> 管理后台支付订单域：提供支付订单的查询、详情、分页、Excel 导出，以及向支付渠道发起支付（提交订单）能力。

## 接口路径前缀

- `/pay/order`  (Controller: PayOrderController)

## 1. 订单查询

### 1.1 获得支付订单

- **路径**: GET /pay/order/get
- **权限**: pay:order:query
- **说明**: 按编号查询单个支付订单；可选 `sync=true` 在订单待支付时主动向渠道同步最新支付状态。

**请求参数**（Query 参数，无 VO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 支付订单编号 |
| sync | Boolean | 否 | - | 是否向渠道同步支付状态，仅在订单待支付时生效 |

**响应**: CommonResult<PayOrderRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 支付订单编号 |
| createTime | LocalDateTime | 创建时间 |
| appId | Long | 应用编号 |
| channelId | Long | 渠道编号 |
| channelCode | String | 渠道编码 |
| merchantOrderId | String | 商户订单编号 |
| subject | String | 商品标题 |
| body | String | 商品描述 |
| notifyUrl | String | 异步通知地址 |
| price | Long | 支付金额，单位：分 |
| channelFeeRate | Double | 渠道手续费，单位：百分比 |
| channelFeePrice | Integer | 渠道手续金额，单位：分 |
| status | Integer | 支付状态（0 待支付 / 1 成功 / 2 失败关闭 / 3 已退款，见 PayOrderStatusEnum） |
| userIp | String | 用户 IP |
| expireTime | LocalDateTime | 订单失效时间 |
| successTime | LocalDateTime | 订单支付成功时间 |
| extensionId | Long | 支付成功的订单拓展单编号 |
| no | String | 支付订单号 |
| refundPrice | Long | 退款总金额，单位：分 |
| channelUserId | String | 渠道用户编号 |
| channelOrderNo | String | 渠道订单号 |

**业务逻辑**:
1. 按 id 查询支付订单 PayOrderDO。
2. 若 `sync=true` 且订单状态为待支付，调用 syncOrderQuietly 同步支付状态。
3. 同步时查询该订单所有待支付的支付拓展单，通过对应渠道 PayClient 主动查询渠道侧订单状态。
4. 渠道返回支付成功或已关闭时触发 notifyOrder 更新本地订单/拓展单状态；渠道返回"订单不存在"（关闭）时不做变更，优先以渠道回调为准，避免误关订单。
5. 同步后重新查询订单并返回（状态可能已变化）。

### 1.2 获得支付订单详情

- **路径**: GET /pay/order/get-detail
- **权限**: pay:order:query
- **说明**: 查询支付订单详情，额外拼接应用名称与支付拓展单信息。

**请求参数**（Query 参数，无 VO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 支付订单编号 |

**响应**: CommonResult<PayOrderDetailsRespVO>（订单不存在时返回 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 支付订单编号 |
| appName | String | 应用名称 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |
| extension.no | String | 支付订单号（拓展单号） |
| extension.channelNotifyData | String | 渠道异步通知的原始内容 |
| （其余字段） | - | 同 PayOrderBaseVO：appId、channelId、channelCode、merchantOrderId、subject、body、notifyUrl、price、channelFeeRate、channelFeePrice、status、userIp、expireTime、successTime、extensionId、no、refundPrice、channelUserId、channelOrderNo |

**业务逻辑**:
1. 按 id 查询支付订单，不存在直接返回 null。
2. 按订单的 appId 查询支付应用 PayAppDO。
3. 按订单的 extensionId 查询支付拓展单 PayOrderExtensionDO。
4. 通过 PayOrderConvert 将订单、拓展单（no、channelNotifyData）与应用名称拼接为详情 VO 返回。

### 1.3 获得支付订单分页

- **路径**: GET /pay/order/page
- **权限**: pay:order:query
- **说明**: 按条件分页查询支付订单，并拼接应用名称。

**请求参数 (PayOrderPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| appId | Long | 否 | - | 应用编号 |
| channelCode | String | 否 | - | 渠道编码 |
| merchantOrderId | String | 否 | - | 商户订单编号 |
| channelOrderNo | String | 否 | - | 渠道订单号 |
| no | String | 否 | - | 支付单号 |
| status | Integer | 否 | - | 支付状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间（起止） |

**响应**: CommonResult<PageResult<PayOrderPageItemRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 支付订单编号 |
| createTime | LocalDateTime | 创建时间 |
| appName | String | 应用名称 |
| （其余字段） | - | 同 PayOrderBaseVO：appId、channelId、channelCode、merchantOrderId、subject、body、notifyUrl、price、channelFeeRate、channelFeePrice、status、userIp、expireTime、successTime、extensionId、no、refundPrice、channelUserId、channelOrderNo |

**业务逻辑**:
1. 按查询条件分页查询支付订单 PayOrderDO。
2. 结果为空时直接返回空分页（仅含 total）。
3. 批量查询分页结果涉及的应用 PayAppDO。
4. 通过 PayOrderConvert 拼接应用名称 appName 后返回。

## 2. 订单支付

### 2.1 提交支付订单

- **路径**: POST /pay/order/submit
- **权限**: 已认证（无 @PreAuthorize，仅要求登录，业务模块用户也可调用）
- **说明**: 对待支付的支付订单按指定渠道发起支付，返回渠道展示模式与展示内容（如支付二维码、跳转 URL）。

**请求参数 (PayOrderSubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 支付单编号 |
| channelCode | String | 是 | @NotEmpty | 支付渠道编码，如 wx_pub |
| channelExtras | Map\<String, String\> | 否 | - | 支付渠道的额外参数（如微信公众号需传 openid；钱包支付时由后端自动填充钱包编号） |
| displayMode | String | 否 | - | 展示模式（PayDisplayModeEnum），不传则用渠道默认方式 |
| returnUrl | String | 否 | @URL | 支付后的回跳地址 |

**响应**: CommonResult<PayOrderSubmitRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 支付状态（PayOrderStatusEnum） |
| displayMode | String | 展示模式（PayDisplayModeEnum） |
| displayContent | String | 展示内容（如二维码链接、跳转 URL、表单 HTML 等） |

**业务逻辑**:
1. 渠道为钱包支付（wallet）时，获取或创建当前登录用户的钱包，并将钱包编号写入 channelExtras 后再提交。
2. 校验订单可提交：订单存在（否则 PAY_ORDER_NOT_FOUND）、未支付成功、处于待支付、未超过失效时间。
3. 校验订单实际未支付：遍历该订单的支付拓展单，若拓展单已支付、或调用渠道查询发现已支付（回调延迟/数据不一致），抛 PAY_ORDER_EXTENSION_IS_PAID。
4. 校验支付应用与渠道有效（validPayApp / validPayChannel），并获取对应渠道 PayClient。
5. 生成支付单号 no（Redis 发号 + 订单号前缀），插入支付拓展单 PayOrderExtensionDO（WAITING 状态）。
6. 构造统一支付请求 PayOrderUnifiedReqDTO（outTradeNo 使用拓展单号 no，回调地址 = 配置的 orderNotifyUrl + 渠道编号），调用渠道 unifiedOrder 发起支付。
7. 若渠道直接返回支付结果（如付款码、免密支付）：立即走支付成功通知更新订单状态（并发回调冲突时 try-catch 忽略）；渠道返回错误码时抛 PAY_ORDER_SUBMIT_CHANNEL_ERROR 提示用户。
8. 读取最新订单状态，返回 status / displayMode / displayContent。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_000_000 | App 不存在 |
| 1_007_000_002 | App 已经被禁用 |
| 1_007_001_000 | 支付渠道的配置不存在 |
| 1_007_002_000 | 支付订单不存在 |
| 1_007_002_001 | 支付订单不处于待支付 |
| 1_007_002_002 | 订单已支付，请刷新页面 |
| 1_007_002_003 | 支付订单已经过期 |
| 1_007_002_004 | 发起支付报错，错误码：{}，错误提示：{} |
| 1_007_003_000 | 支付交易拓展单不存在 |
| 1_007_003_001 | 支付交易拓展单不处于待支付 |
| 1_007_003_002 | 订单已支付，请等待支付结果 |

## 3. 订单导出

### 3.1 导出支付订单 Excel

- **路径**: GET /pay/order/export-excel
- **权限**: pay:order:export
- **说明**: 按条件（与分页查询一致，不分页）导出支付订单 Excel 文件。

**请求参数 (PayOrderExportReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| appId | Long | 否 | - | 应用编号 |
| channelCode | String | 否 | - | 渠道编码 |
| merchantOrderId | String | 否 | - | 商户订单编号 |
| channelOrderNo | String | 否 | - | 渠道订单号 |
| no | String | 否 | - | 支付单号 |
| status | Integer | 否 | - | 支付状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间（起止） |

**响应**: Excel 文件流（`支付订单.xls`），Excel 列来自 PayOrderExcelVO：编号、创建时间、支付金额（分转元）、退款金额（分转元）、手续金额（分转元）、商户单号、支付单号、渠道单号、支付状态（字典）、渠道编号名称（字典）、订单支付成功时间、订单失效时间、应用名称、商品标题、商品描述。

**业务逻辑**:
1. 按查询条件（不分页）查询支付订单列表 PayOrderDO。
2. 列表为空时导出仅含表头的空 Excel。
3. 批量查询涉及的应用 PayAppDO，拼接应用名称 appName。
4. 通过 PayOrderConvert 转换为 PayOrderExcelVO 列表（金额经 MoneyConvert 转换、状态与渠道经字典转换）。
5. 通过 ExcelUtils 写出 `支付订单.xls` 文件流。
