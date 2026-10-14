# 示例订单接口 (PayDemoOrderController / PayDemoWithdrawController)

> 演示支付中心三大能力的示例业务：示例订单（demo-order）演示「支付 + 退款」全流程，示例提现单（demo-withdraw）演示「转账」全流程，可作为业务模块接入支付模块的参考实现。

## 接口路径前缀

- /pay/demo-order  (Controller: PayDemoOrderController) —— 示例订单，演示支付、退款功能
- /pay/demo-withdraw  (Controller: PayDemoWithdrawController) —— 示例提现单，演示转账功能

---

## 1. 示例订单（PayDemoOrderController）

### 1.1 创建示例订单
- **路径**: POST /pay/demo-order/create
- **权限**: 已认证（无 @PreAuthorize，使用当前登录用户编号下单）
- **说明**: 根据商品编号创建示例订单，并调用支付模块创建对应支付单。

**请求参数 (PayDemoOrderCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| spuId | Long | 是 | @NotNull | 商品编号 |

**响应**: CommonResult&lt;Long&gt; —— 示例订单编号

**业务逻辑**:
1. 从内置商品 Map（spuNames）按 spuId 获取商品名与价格，商品不存在直接断言失败（演示环境仅支持 1~5 五个内置商品：华为手机、小米电视、苹果手表、华硕笔记本、蔚来汽车）。
2. 插入示例订单（userId、spuId、spuName、price，payStatus=false，refundPrice=0）。
3. 调用 PayOrderApi.createOrder 创建支付单（appKey=demo，用户类型 ADMIN，商户订单号 = 示例订单 id，支付过期时间为 2 小时后）。
4. 将返回的支付单编号 payOrderId 更新回示例订单，返回订单编号。

### 1.2 获得示例订单分页
- **路径**: GET /pay/demo-order/page
- **权限**: 已认证
- **说明**: 分页获得示例订单列表。

**请求参数**: 通用分页参数 PageParam（pageNo 默认 1、pageSize 默认 10），无域专属查询条件

**响应**: CommonResult&lt;PageResult&lt;PayDemoOrderRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 订单编号 |
| userId | Long | 用户编号 |
| spuId | Long | 商品编号 |
| spuName | String | 商品名称 |
| price | Integer | 价格，单位：分 |
| payStatus | Boolean | 是否已支付 |
| payOrderId | Long | 支付订单编号 |
| payTime | LocalDateTime | 订单支付时间 |
| payChannelCode | String | 支付渠道 |
| payRefundId | Long | 支付退款编号 |
| refundPrice | Integer | 退款金额，单位：分 |
| refundTime | LocalDateTime | 退款时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 PageParam 直接分页查询示例订单表（无额外过滤条件），DO 转为 RespVO 返回。

### 1.3 更新示例订单为已支付（支付结果回调）
- **路径**: POST /pay/demo-order/update-paid
- **权限**: @PermitAll（无需登录，安全性由 PayDemoOrderService 内部校验保证；由支付模块定时任务 PayNotifyJob 回调）
- **说明**: 支付单支付成功后，支付模块回调本接口，将示例订单标记为已支付。

**请求参数 (PayOrderNotifyReqDTO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantOrderId | String | 是 | @NotEmpty | 商户订单号（即示例订单编号） |
| payOrderId | Long | 是 | @NotNull | 支付订单编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验示例订单存在，不存在则记录错误日志并抛出 DEMO_ORDER_NOT_FOUND。
2. 若订单已支付：支付单编号相同视为重复回调，直接返回；不同则抛出 DEMO_ORDER_UPDATE_PAID_FAIL_PAY_ORDER_ID_ERROR。
3. 校验支付单合法性（validatePayOrderPaid）：支付单必须存在（否则 PAY_ORDER_NOT_FOUND）、状态为支付成功、支付金额与订单金额一致、商户订单号与示例订单 id 一致（二次匹配校验）。
4. 通过 updateByIdAndPayed 携带「未支付」状态条件，乐观更新为已支付（记录支付时间、支付渠道）；更新数为 0 则抛出 DEMO_ORDER_UPDATE_PAID_STATUS_NOT_UNPAID（并发保护）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_900_000 | 示例订单不存在 |
| 1_007_900_001 | 示例订单更新支付状态失败，订单不是【未支付】状态 |
| 1_007_900_002 | 示例订单更新支付状态失败，支付单编号不匹配 |
| 1_007_900_003 | 示例订单更新支付状态失败，支付单状态不是【支付成功】状态 |
| 1_007_900_004 | 示例订单更新支付状态失败，支付单金额不匹配 |
| 1_007_002_000 | 支付订单不存在 |

### 1.4 发起示例订单退款
- **路径**: PUT /pay/demo-order/refund?id={id}
- **权限**: 已认证
- **说明**: 对已支付的示例订单发起全额退款，调用支付模块创建退款单。

**请求参数**: 无（Query 参数 id：示例订单编号，必填）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验订单可退款（validateDemoOrderCanRefund）：订单存在、已支付、且未发起过退款（payRefundId 为空）。
2. 生成商户退款编号：订单 id + "-refund"（演示环境无独立售后维权表，直接以订单 id 拼接）。
3. 调用 PayRefundApi.createRefund 创建退款单（appKey=demo，用户类型 ADMIN，全额退款，退款原因"想退钱"）。
4. 将退款单编号 payRefundId 与退款金额（= 订单金额）更新回示例订单。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_900_000 | 示例订单不存在 |
| 1_007_900_005 | 发起退款失败，示例订单未支付 |
| 1_007_900_006 | 发起退款失败，示例订单已退款 |

### 1.5 更新示例订单为已退款（退款结果回调）
- **路径**: POST /pay/demo-order/update-refunded
- **权限**: @PermitAll（无需登录，安全性由 Service 内部校验保证；由支付模块定时任务 PayNotifyJob 回调）
- **说明**: 退款单退款成功后，支付模块回调本接口，更新示例订单的退款时间。

**请求参数 (PayRefundNotifyReqDTO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantOrderId | String | 是 | @NotEmpty | 商户订单号（即示例订单编号） |
| merchantRefundId | String | 是 | @NotEmpty | 商户退款编号（订单 id + "-refund"） |
| payRefundId | Long | 是 | @NotNull | 支付退款编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验示例订单存在，否则抛出 DEMO_ORDER_NOT_FOUND。
2. 校验订单记录的退款单编号与回调 payRefundId 一致，否则抛出 DEMO_ORDER_REFUND_FAIL_REFUND_ORDER_ID_ERROR。
3. 校验退款单合法性（validateDemoOrderCanRefunded）：退款单存在、状态为退款成功、退款金额与订单金额一致、商户退款编号等于 订单 id + "-refund"（二次匹配校验）。
4. 将示例订单的退款时间 refundTime 更新为退款单成功时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_900_000 | 示例订单不存在 |
| 1_007_900_007 | 发起退款失败，退款订单不存在 |
| 1_007_900_008 | 发起退款失败，退款订单未退款成功 |
| 1_007_900_009 | 发起退款失败，退款单编号不匹配 |
| 1_007_900_010 | 发起退款失败，退款单金额不匹配 |

---

## 2. 示例提现单（PayDemoWithdrawController）

### 2.1 创建示例提现单
- **路径**: POST /pay/demo-withdraw/create
- **权限**: 已认证
- **说明**: 创建一笔等待提现的示例提现单。

**请求参数 (PayDemoWithdrawCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| subject | String | 是 | @NotEmpty | 提现标题 |
| price | Integer | 是 | @NotNull、@Min(1) | 提现金额，单位：分，必须大于零 |
| userAccount | String | 是 | @NotBlank | 收款人账号 |
| userName | String | 支付宝时必填 | @AssertTrue(isUserNameValid) | 收款人姓名（提现方式为支付宝时必须填写） |
| type | Integer | 是 | @NotNull、@InEnum(PayDemoWithdrawTypeEnum) | 提现方式：1 支付宝、2 微信、3 钱包 |

**响应**: CommonResult&lt;Long&gt; —— 示例提现单编号

**业务逻辑**:
1. VO 转 PayDemoWithdrawDO，并按提现方式映射转账渠道：支付宝 → alipay_pc、微信 → wx_lite、钱包 → wallet。
2. 初始化状态为「等待提现」（0）后插入数据库，返回提现单编号。

### 2.2 提现单转账
- **路径**: POST /pay/demo-withdraw/transfer?id={id}
- **权限**: 已认证
- **说明**: 对等待提现（或转账失败）的提现单发起转账，调用支付模块创建转账单。

**请求参数**: 无（Query 参数 id：提现单编号，必填）

**响应**: CommonResult&lt;Long&gt; —— 支付转账单编号

**业务逻辑**:
1. 校验提现单可转账（validateDemoWithdrawCanTransfer）：提现单存在，且状态为「等待提现」或「提现关闭」，否则抛出 DEMO_WITHDRAW_NOT_FOUND / DEMO_WITHDRAW_TRANSFER_FAIL_STATUS_NOT_WAITING_OR_CLOSED。
2. 特殊处理：若为转账失败（提现关闭）状态，先通过带状态条件的更新将其重置为「等待提现」并清空失败原因，更新数为 0 则抛出状态不匹配错误码。
3. 组装 PayTransferCreateReqDTO 创建转账单（appKey=demo，用户类型 ADMIN，商户转账单号 = 提现单 id，携带收款人账号/姓名）；若为微信渠道，额外写入微信转账用途扩展参数（buildWeiXinChannelExtra1000："测试活动"、"测试奖励"）。
4. 通过带状态条件的更新将转账单编号 payTransferId 写回提现单，返回转账单编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_901_000 | 示例提现单不存在 |
| 1_007_901_008 | 发起转账失败，原因：示例提现单状态不是【等待提现】或【提现关闭】 |

### 2.3 获得示例提现单分页
- **路径**: GET /pay/demo-withdraw/page
- **权限**: 已认证
- **说明**: 分页获得示例提现单列表。

**请求参数**: 通用分页参数 PageParam（pageNo 默认 1、pageSize 默认 10），无域专属查询条件

**响应**: CommonResult&lt;PageResult&lt;PayDemoWithdrawRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 提现单编号 |
| subject | String | 提现标题 |
| price | Integer | 提现金额，单位：分 |
| userName | String | 收款人姓名 |
| userAccount | String | 收款人账号 |
| type | Integer | 提现类型：1 支付宝、2 微信、3 钱包 |
| status | Integer | 提现状态：0 等待提现、10 提现成功、20 提现关闭 |
| payTransferId | Long | 转账单编号 |
| transferChannelCode | String | 转账渠道 |
| transferTime | LocalDateTime | 转账成功时间 |
| transferErrorMsg | String | 转账失败原因 |

**业务逻辑**:
1. 按 PageParam 直接分页查询示例提现单表（无额外过滤条件），DO 转为 RespVO 返回。

### 2.4 更新示例提现单的转账状态（转账结果回调）
- **路径**: POST /pay/demo-withdraw/update-transferred
- **权限**: @PermitAll（无需登录，安全性由 Service 内部校验保证；由支付模块转账服务回调）
- **说明**: 转账单转账成功或失败后，支付模块回调本接口，更新提现单状态。

**请求参数 (PayTransferNotifyReqDTO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantTransferId | String | 是 | @NotEmpty | 商户转账单号（即提现单编号） |
| payTransferId | Long | 是 | @NotNull | 支付转账单编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验提现单存在，不存在则记录错误日志并抛出 DEMO_WITHDRAW_NOT_FOUND。
2. 若提现单已结束（提现成功或提现关闭）：转账单编号相同视为重复回调，直接返回；不同则抛出 DEMO_WITHDRAW_UPDATE_STATUS_FAIL_PAY_TRANSFER_ID_ERROR。
3. 校验转账单合法性（validateDemoTransferStatusCanUpdate）：转账单存在（否则 PAY_TRANSFER_NOT_FOUND）、状态为转账成功或转账失败、转账金额与提现金额一致、商户转账单号与提现单 id 一致（二次匹配校验）、转账渠道与提现单渠道一致。
4. 按转账单结果通过带状态条件的更新：转账成功 → 提现状态更新为「提现成功」（10），转账失败 → 「提现关闭」（20），同时记录转账时间与渠道失败原因。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_901_000 | 示例提现单不存在 |
| 1_007_901_001 | 更新示例提现单状态失败，支付转账单编号不匹配 |
| 1_007_901_002 | 更新示例提现单状态失败，支付转账单状态不是【转账成功】或【转账失败】状态 |
| 1_007_901_003 | 更新示例提现单状态失败，支付转账单金额不匹配 |
| 1_007_901_004 | 更新示例提现单状态失败，支付转账单商户订单号不匹配 |
| 1_007_901_005 | 更新示例提现单状态失败，支付转账单渠道不匹配 |
| 1_007_009_001 | 转账单不存在 |
