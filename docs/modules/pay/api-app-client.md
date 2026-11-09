# 用户 APP 端接口 (AppPay*Controller)

> pay 模块面向 C 端用户（会员）的一组 `app` 控制器，统一挂在 `/app-api` 前缀下（`@RequestMapping` 的路径与 admin 端同名，但由 `WebProperties` 按包路径 `**.controller.app.**` 映射到 `/app-api`，与 `/admin-api` 互不冲突）。所有接口均需登录态（未标注 `@PermitAll` / `@PreAuthorize`），并以当前登录用户 `userId + userType` 作为数据边界。

## 接口路径前缀

| Controller | 相对路径 | 完整前缀 |
|-----------|---------|---------|
| AppPayChannelController | /pay/channel | /app-api/pay/channel |
| AppPayOrderController | /pay/order | /app-api/pay/order |
| AppPayTransferController | /pay/transfer | /app-api/pay/transfer |
| AppPayWalletController | /pay/wallet | /app-api/pay/wallet |
| AppPayWalletRechargeController | /pay/wallet-recharge | /app-api/pay/wallet-recharge |
| AppPayWalletRechargePackageController | /pay/wallet-recharge-package | /app-api/pay/wallet-recharge-package |
| AppPayWalletTransactionController | /pay/wallet-transaction | /app-api/pay/wallet-transaction |

> 说明：api-*.md 中其它文档描述的是 admin 端（`/admin-api/pay/...`）。两端同名路径（如 `/pay/wallet/get`、`/pay/order/get`）因前缀不同不会冲突。

---

## 1. 支付渠道（AppPayChannelController）

### 1.1 获得指定应用的开启的支付渠道编码列表

- **路径**: GET /app-api/pay/channel/get-enable-code-list
- **权限**: 已认证
- **说明**: 查询指定支付应用下已开启的渠道编码，供前端渲染可选的支付方式。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| appId | Long | 是 | @RequestParam(required = true) | 支付应用编号 |

**响应**: CommonResult&lt;Set&lt;String&gt;&gt; —— 渠道编码集合（如 `wx_lite`、`alipay_pc`）

**业务逻辑**: 调用 `PayChannelService#getEnableChannelList(appId)` 获取开启的渠道，转换为 `PayChannelDO::getCode` 集合返回。

---

## 2. 支付订单（AppPayOrderController）

### 2.1 获得支付订单

- **路径**: GET /app-api/pay/order/get
- **权限**: 已认证（只能查询当前登录用户的订单，非本人订单返回 null）
- **说明**: 按编号或支付单号查询支付订单，可选同步渠道状态。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | @RequestParam(required = false) | 支付订单编号 |
| no | String | 否 | @RequestParam(required = false) | 支付订单号（优先按 no 查询） |
| sync | Boolean | 否 | @RequestParam(required = false) | 是否向渠道同步支付状态，仅在订单待支付时生效 |

**响应**: CommonResult&lt;PayOrderRespVO&gt;（字段见 [api-order.md](api-order.md) 1.1；订单不存在或不属于当前用户时 data 为 null）

**业务逻辑**:
1. `no` 非空时先按 no 查询；未命中且 `id` 非空时再按 id 查询；
2. 订单为空直接返回 success(null)；
3. **越权校验** `isLoginUserOrder`：订单 `userId`/`userType` 非空时必须与当前登录用户一致（早期未存 userId/userType 的订单忽略该校验，见 issue 1303），不一致返回 success(null)；
4. `sync=true` 且订单为待支付时调用 `syncOrderQuietly` 同步，再重新查询返回。

### 2.2 提交支付订单

- **路径**: POST /app-api/pay/order/submit
- **权限**: 已认证（只能提交当前登录用户的订单）
- **说明**: 对指定支付单发起渠道支付（统一下单）。

**请求参数 (AppPayOrderSubmitReqVO，继承 PayOrderSubmitReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 支付单编号 |
| channelCode | String | 是 | @NotEmpty | 支付渠道编码 |
| channelExtras | Map&lt;String, String&gt; | 否 | - | 渠道额外参数（如微信公众号需 openid） |
| displayMode | String | 否 | - | 展示模式（见 PayDisplayModeEnum，不传则用渠道默认） |
| returnUrl | String | 否 | @URL | 支付完成后的回跳地址 |

**响应**: CommonResult&lt;AppPayOrderSubmitRespVO&gt;（继承 PayOrderSubmitRespVO）

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | Integer | 支付状态（见 PayOrderStatusEnum） |
| displayMode | String | 展示模式 |
| displayContent | String | 展示内容（如支付链接/二维码内容） |

**业务逻辑**:
1. 按 id 查询订单并做越权校验，订单不存在或不属于当前用户抛 `PAY_ORDER_NOT_FOUND`；
2. `channelCode = wallet` 时，服务端调用 `getOrCreateWallet` 注入当前用户钱包编号到 `channelExtras`（`WalletPayClient.WALLET_ID_KEY`），不信任前端传入；
3. 调用 `PayOrderService#submitOrder(reqVO, getClientIP())` 发起渠道支付并返回结果。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_002_000 | 支付订单不存在 |
| 1_007_002_004 | 发起支付报错（渠道返回错误码/提示） |

---

## 3. 转账单（AppPayTransferController）

### 3.1 同步转账单

- **路径**: GET /app-api/pay/transfer/sync
- **权限**: 已认证
- **说明**: 主动向渠道查询转账结果并回调本地状态，用于缓解微信转账异步回调延迟。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 转账单编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 按 id 查询转账单，不存在抛 `PAY_TRANSFER_NOT_FOUND`；
2. 获取渠道 PayClient 并调用 `getTransfer(no)` 查询渠道侧转账结果；
3. 调用 `notifyTransfer(channelId, resp)` 按租户处理转账结果（更新转账单状态、回调业务方）；
4. 同步过程中的异常内部 catch 并记录日志，不向上抛出。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_009_001 | 转账单不存在 |

---

## 4. 钱包（AppPayWalletController）

### 4.1 获取钱包

- **路径**: GET /app-api/pay/wallet/get
- **权限**: 已认证
- **说明**: 获取当前会员钱包，不存在时自动创建（初始余额 0）。

**请求参数**: 无（使用当前登录用户）

**响应**: CommonResult&lt;AppPayWalletRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| balance | Integer | 钱包余额，单位分 |
| totalExpense | Integer | 累计支出，单位分（正值） |
| totalRecharge | Integer | 累计充值，单位分 |

**业务逻辑**: 调用 `getOrCreateWallet(getLoginUserId(), MEMBER)` 获取/创建钱包后转换为 AppPayWalletRespVO。

---

## 5. 钱包充值（AppPayWalletRechargeController）

### 5.1 创建钱包充值记录（发起充值）

- **路径**: POST /app-api/pay/wallet-recharge/create
- **权限**: 已认证
- **说明**: 创建充值单并向钱包支付应用创建对应支付单。

**请求参数 (AppPayWalletRechargeCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| payPrice | Integer | 否 | @Min(1) | 自定义支付金额，单位分 |
| packageId | Long | 否 | - | 充值套餐编号（与 payPrice 二选一） |

> 类上 `@AssertTrue(isValidPayPriceAndPackageId)` 校验 `payPrice` 与 `packageId` 不能同时为空；选了套餐时以套餐的 payPrice / bonusPrice 为准。

**响应**: CommonResult&lt;AppPayWalletRechargeCreateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 钱包充值记录编号 |
| payOrderId | Long | 对应支付订单编号 |

**业务逻辑**:
1. 若传 packageId，校验套餐（不存在抛 `WALLET_RECHARGE_PACKAGE_NOT_FOUND`），取套餐的 payPrice / bonusPrice；否则用 reqVO.payPrice，bonusPrice=0；
2. 插入充值记录（payStatus=false）；
3. 通过 `PayOrderApi#createOrder`（appKey = `yudao.pay.wallet-pay-app-key`，默认 wallet）创建支付单，商户订单号 = 充值记录 id，金额 = payPrice，过期时间 2 小时；
4. 回写 payOrderId 到充值记录并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_011 | 钱包充值套餐不存在 |

### 5.2 获得钱包充值记录分页

- **路径**: GET /app-api/pay/wallet-recharge/page
- **权限**: 已认证
- **说明**: 分页查询当前会员**已支付**的钱包充值记录，并拼接对应的支付订单渠道信息。

**请求参数**: 通用分页参数 PageParam（pageNo 默认 1、pageSize 默认 10）

**响应**: CommonResult&lt;PageResult&lt;AppPayWalletRechargeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 充值记录编号 |
| totalPrice | Integer | 用户实际到账余额（支付 + 赠送），单位分 |
| payPrice | Integer | 实际支付金额，单位分 |
| bonusPrice | Integer | 赠送金额，单位分 |
| payChannelCode | String | 支付渠道编码 |
| payChannelName | String | 支付渠道名 |
| payOrderId | Long | 支付订单编号 |
| payOrderChannelOrderNo | String | 支付订单渠道单号（PayOrderDO#channelOrderNo） |
| payTime | LocalDateTime | 支付时间 |
| refundStatus | Integer | 退款状态（见 PayRefundStatusEnum） |

**业务逻辑**:
1. 调用 `getWalletRechargePackagePage(userId, MEMBER, pageReqVO, true)`（`payStatus=true` 仅查已支付）；
2. 空结果返回空分页；
3. 批量查询分页内 `payOrderId` 对应的支付订单，拼接渠道信息后转换返回。

---

## 6. 钱包充值套餐（AppPayWalletRechargePackageController）

### 6.1 获得钱包充值套餐列表

- **路径**: GET /app-api/pay/wallet-recharge-package/list
- **权限**: 已认证
- **说明**: 获取所有已开启（status=0）的充值套餐，按支付金额升序。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;AppPayWalletPackageRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 套餐编号 |
| name | String | 套餐名 |
| payPrice | Integer | 支付金额，单位分 |
| bonusPrice | Integer | 赠送金额，单位分 |

**业务逻辑**: 查询 status=ENABLE 的套餐，按 `payPrice` 升序排序后转换为 VO 返回。

---

## 7. 钱包余额明细（AppPayWalletTransactionController）

### 7.1 获得钱包流水分页

- **路径**: GET /app-api/pay/wallet-transaction/page
- **权限**: 已认证
- **说明**: 分页查询当前会员的钱包流水。

**请求参数 (AppPayWalletTransactionPageReqVO)**（继承 PageParam）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| type | Integer | 否 | - | 类型：1 收入 / 2 支出 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;AppPayWalletTransactionRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| bizType | Integer | 业务分类（见 PayWalletBizTypeEnum） |
| price | Long | 交易金额，单位分（收入为正、支出为负） |
| title | String | 流水标题 |
| createTime | LocalDateTime | 交易时间 |

**业务逻辑**: 调用 `getWalletTransactionPage(getLoginUserId(), MEMBER, pageReqVO)` 分页查询当前用户钱包流水并转换为 VO。

### 7.2 获得钱包流水统计

- **路径**: GET /app-api/pay/wallet-transaction/get-summary
- **权限**: 已认证
- **说明**: 统计当前会员钱包在指定时间段内的累计收入与累计支出。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| createTime | LocalDateTime[] | 是 | @RequestParam(required = true) + @DateTimeFormat | 统计时间段（起止） |

**响应**: CommonResult&lt;AppPayWalletTransactionSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalExpense | Integer | 累计支出，单位分，**正值**（支出流水 price 为负，按 `SUM(-price)` 汇总） |
| totalIncome | Integer | 累计收入，单位分，正值（按 `SUM(price)` 汇总） |

> 与 api-wallet.md 4.2 为同一端点的详细说明，统计口径见 [pitfalls.md](pitfalls.md) 6.3。
