# 用户钱包接口 (PayWalletController / PayWalletRechargeController / PayWalletRechargePackageController / PayWalletTransactionController)

> 提供管理后台对会员钱包的查询与余额调整、钱包充值订单的支付/退款回调处理、充值套餐管理，以及钱包流水（余额明细）分页查询。

## 接口路径前缀

- `/pay/wallet`（Controller: PayWalletController，用户钱包）
- `/pay/wallet-recharge`（Controller: PayWalletRechargeController，钱包充值）
- `/pay/wallet-recharge-package`（Controller: PayWalletRechargePackageController，钱包充值套餐）
- `/pay/wallet-transaction`（Controller: PayWalletTransactionController，钱包余额明细）

---

## 1. 用户钱包（PayWalletController）

### 1.1 获得用户钱包明细

- **路径**: GET /pay/wallet/get
- **权限**: pay:wallet:query
- **说明**: 按用户编号查询会员钱包，钱包不存在时自动创建（初始余额为 0）

**请求参数 (PayWalletUserReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 用户编号 |

**响应**: CommonResult&lt;PayWalletRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 钱包编号 |
| userId | Long | 用户编号 |
| userType | Integer | 用户类型 |
| balance | Integer | 余额，单位分 |
| totalExpense | Integer | 累计支出，单位分 |
| totalRecharge | Integer | 累计充值，单位分 |
| freezePrice | Integer | 冻结金额，单位分 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 `getOrCreateWallet(userId, MEMBER)`：先按 userId + userType 查询钱包；
2. 钱包不存在时，通过 Redis 分布式锁（PayWalletLockRedisDAO，超时 120 秒）+ 双重检查创建钱包，初始 balance / totalExpense / totalRecharge 均为 0；
3. 将 PayWalletDO 转换为 PayWalletRespVO 返回。

### 1.2 获得会员钱包分页

- **路径**: GET /pay/wallet/page
- **权限**: pay:wallet:query
- **说明**: 按条件分页查询会员钱包列表

**请求参数 (PayWalletPageReqVO)**（继承 PageParam，含 pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| userId | Long | 否 | - | 用户编号 |
| userType | Integer | 否 | @InEnum(UserTypeEnum) | 用户类型 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;PayWalletRespVO&gt;&gt;，元素字段同 1.1 的 PayWalletRespVO。

**业务逻辑**:
1. 调用 `PayWalletService#getWalletPage`，由 PayWalletMapper 按 userId / userType / createTime 条件分页查询；
2. 转换为 PayWalletRespVO 分页结果返回。

### 1.3 更新会员用户余额

- **路径**: PUT /pay/wallet/update-balance
- **权限**: pay:wallet:update-balance
- **说明**: 管理员手工调整会员钱包余额（正数增加、负数减少），并生成「更新余额」类型流水

**请求参数 (PayWalletUpdateBalanceReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 用户编号 |
| balance | Integer | 是 | @NotNull | 变动余额，正数为增加，负数为减少，单位分 |

**响应**: CommonResult&lt;Boolean&gt;（操作是否成功）

**业务逻辑**:
1. 调用 `getOrCreateWallet` 获取用户钱包，不存在时记录错误日志并抛出 WALLET_NOT_FOUND；
2. 调用 `addWalletBalance(walletId, userId, UPDATE_BALANCE, balance)`；
3. `addWalletBalance` 先获取钱包（不存在抛 WALLET_NOT_FOUND），再通过 Redis 分布式锁加锁更新，避免并发更新导致余额变化不连贯；
4. 按 UPDATE_BALANCE 业务类型执行 `updateWhenAdd` 直接增减钱包余额；
5. 生成钱包流水（bizType = 5「更新余额」，price 为变动金额，balance 为变动后余额）并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_007_000 | 用户钱包不存在 |
| 1_007_007_001 | 钱包余额不足 |

---

## 2. 钱包充值（PayWalletRechargeController）

### 2.1 更新钱包充值为已充值

- **路径**: POST /pay/wallet-recharge/update-paid
- **权限**: @PermitAll（无需登录，由 pay 支付模块回调，见 PayNotifyJob，内部自行校验）
- **说明**: 支付成功回调入口，将钱包充值记录置为已支付并增加钱包余额

**请求参数 (PayOrderNotifyReqDTO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantOrderId | String | 是 | @NotEmpty | 商户订单号（即钱包充值记录编号） |
| payOrderId | Long | 是 | @NotNull | 支付订单编号 |

**响应**: CommonResult&lt;Boolean&gt;（处理是否成功）

**业务逻辑**:
1. 校验充值记录存在，不存在抛 WALLET_RECHARGE_NOT_FOUND；
2. 幂等校验：若已支付且支付单号相同，直接返回；若已支付但支付单号不同，抛 WALLET_RECHARGE_UPDATE_PAID_PAY_ORDER_ID_ERROR；
3. `validatePayOrderPaid` 校验支付单：存在（PAY_ORDER_NOT_FOUND）、状态为支付成功（WALLET_RECHARGE_UPDATE_PAID_PAY_ORDER_STATUS_NOT_SUCCESS）、金额与充值支付金额一致（WALLET_RECHARGE_UPDATE_PAID_PAY_PRICE_NOT_MATCH）、商户订单号匹配（WALLET_RECHARGE_UPDATE_PAID_PAY_ORDER_ID_ERROR）；
4. 通过 `updateByIdAndPaid`（条件 payStatus = false 乐观更新）将充值记录置为已支付，记录支付时间与支付渠道，更新失败抛 WALLET_RECHARGE_UPDATE_PAID_STATUS_NOT_UNPAID；
5. 调用 `addWalletBalance(RECHARGE)` 增加钱包余额（金额为 支付金额 + 赠送金额），并生成「充值」类型流水；
6. 异步发送微信小程序订阅消息（充值成功通知）；若支付渠道为微信小程序，还会调用 system 模块接口上传虚拟物品发货信息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_000 | 钱包充值记录不存在 |
| 1_007_008_001 | 钱包充值更新支付状态失败，钱包充值记录不是【未支付】状态 |
| 1_007_008_002 | 钱包充值更新支付状态失败，支付单编号不匹配 |
| 1_007_008_003 | 钱包充值更新支付状态失败，支付单状态不是【支付成功】状态 |
| 1_007_008_004 | 钱包充值更新支付状态失败，支付单金额不匹配 |
| 1_007_002_000 | 支付订单不存在 |

### 2.2 发起钱包充值退款

- **路径**: POST /pay/wallet-recharge/refund
- **权限**: 已认证（无 @PreAuthorize 注解，仅要求登录）
- **说明**: 对已支付的钱包充值记录发起退款，先冻结余额再创建支付退款单

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 钱包充值记录编号 |

**响应**: CommonResult&lt;Boolean&gt;（发起是否成功）

**业务逻辑**:
1. 查询充值记录，不存在抛 WALLET_RECHARGE_NOT_FOUND；
2. `validateWalletRechargeCanRefund` 校验：未支付抛 WALLET_RECHARGE_REFUND_FAIL_NOT_PAID；已存在退款单号抛 WALLET_RECHARGE_REFUND_FAIL_REFUNDED；钱包余额小于充值总额（支付 + 赠送）抛 WALLET_RECHARGE_REFUND_BALANCE_NOT_ENOUGH；
3. 调用 `freezePrice` 冻结退款金额（冻结失败即余额不足，抛 WALLET_BALANCE_NOT_ENOUGH）；
4. 调用 `payRefundApi.createRefund` 创建支付退款单（商户退款单号为 `{充值id}-refund`，退款金额为充值的支付金额 payPrice，即赠送金额随支付金额一并退回）；
5. 更新充值记录的退款单号 payRefundId，并将退款状态置为 WAITING（待退款）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_000 | 钱包充值记录不存在 |
| 1_007_008_005 | 钱包发起退款失败，钱包充值订单未支付 |
| 1_007_008_006 | 钱包发起退款失败，钱包充值订单已退款 |
| 1_007_008_007 | 钱包发起退款失败，钱包余额不足 |
| 1_007_007_001 | 钱包余额不足（冻结金额时） |

### 2.3 更新钱包充值为已退款

- **路径**: POST /pay/wallet-recharge/update-refunded
- **权限**: @PermitAll（无需登录，由 pay 支付模块回调，见 PayNotifyJob，内部自行校验）
- **说明**: 退款结果回调入口，按退款成功/失败分别处理钱包余额与充值记录退款状态

**请求参数 (PayRefundNotifyReqDTO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantOrderId | String | 是 | @NotEmpty | 商户订单号（即钱包充值记录编号） |
| merchantRefundId | String | 是 | @NotEmpty | 商户退款编号（即 `{充值id}-refund`） |
| payRefundId | Long | 是 | @NotNull | 支付退款单编号 |

**响应**: CommonResult&lt;Boolean&gt;（处理是否成功）

**业务逻辑**:
1. 查询充值记录，不存在抛 WALLET_RECHARGE_NOT_FOUND；
2. `validateWalletRechargeCanRefunded` 校验：退款单编号与充值记录不匹配抛 WALLET_RECHARGE_REFUND_FAIL_REFUND_ORDER_ID_ERROR；支付退款单不存在抛 WALLET_RECHARGE_REFUND_FAIL_REFUND_NOT_FOUND；退款金额与充值支付金额不一致抛 WALLET_RECHARGE_REFUND_FAIL_REFUND_PRICE_NOT_MATCH；商户退款单号不匹配再次抛 WALLET_RECHARGE_REFUND_FAIL_REFUND_ORDER_ID_ERROR；
3. 退款成功：调用 `reduceWalletBalance(RECHARGE_REFUND)` 扣减钱包（仅扣减冻结金额 freezePrice，balance 在冻结时已扣、保持不变），并更新充值记录的退款状态为 SUCCESS、退款时间、退款总额 / 退款支付金额 / 退款赠送金额；
4. 退款失败：调用 `unfreezePrice` 解冻余额（解冻失败抛 WALLET_FREEZE_PRICE_NOT_ENOUGH），退款状态置为 FAILURE；
5. 通过 `updateByIdAndRefunded`（条件退款状态为 WAITING）将上述退款字段更新到充值记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_000 | 钱包充值记录不存在 |
| 1_007_008_008 | 钱包退款更新失败，钱包退款单编号不匹配 |
| 1_007_008_009 | 钱包退款更新失败，退款订单不存在 |
| 1_007_008_010 | 钱包退款更新失败，退款单金额不匹配 |
| 1_007_007_004 | 钱包冻结余额不足 |

---

## 3. 钱包充值套餐（PayWalletRechargePackageController）

### 3.1 创建钱包充值套餐

- **路径**: POST /pay/wallet-recharge-package/create
- **权限**: pay:wallet-recharge-package:create
- **说明**: 新增一个钱包充值套餐（支付金额 + 赠送金额）

**请求参数 (WalletRechargePackageCreateReqVO)**（继承 WalletRechargePackageBaseVO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 套餐名 |
| payPrice | Integer | 是 | @NotNull | 支付金额，单位分 |
| bonusPrice | Integer | 是 | @NotNull | 赠送金额，单位分 |
| status | Byte | 是 | @NotNull | 状态（CommonStatusEnum：0 开启 / 1 禁用） |

**响应**: CommonResult&lt;Long&gt;（新套餐编号）

**业务逻辑**:
1. `validateRechargePackageNameUnique` 校验套餐名唯一，按名称查询已存在则抛 WALLET_RECHARGE_PACKAGE_NAME_EXISTS；
2. 转换为 PayWalletRechargePackageDO 插入数据库；
3. 返回新套餐编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_013 | 钱包充值套餐名称已存在 |

### 3.2 更新钱包充值套餐

- **路径**: PUT /pay/wallet-recharge-package/update
- **权限**: pay:wallet-recharge-package:update
- **说明**: 修改指定编号的钱包充值套餐

**请求参数 (WalletRechargePackageUpdateReqVO)**（继承 WalletRechargePackageBaseVO）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 套餐编号 |
| name | String | 是 | @NotNull | 套餐名 |
| payPrice | Integer | 是 | @NotNull | 支付金额，单位分 |
| bonusPrice | Integer | 是 | @NotNull | 赠送金额，单位分 |
| status | Byte | 是 | @NotNull | 状态（0 开启 / 1 禁用） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验套餐存在，不存在抛 WALLET_RECHARGE_PACKAGE_NOT_FOUND；
2. 校验套餐名唯一（排除自身编号），重复抛 WALLET_RECHARGE_PACKAGE_NAME_EXISTS；
3. 转换后按编号更新套餐记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_011 | 钱包充值套餐不存在 |
| 1_007_008_013 | 钱包充值套餐名称已存在 |

### 3.3 删除钱包充值套餐

- **路径**: DELETE /pay/wallet-recharge-package/delete
- **权限**: pay:wallet-recharge-package:delete
- **说明**: 删除指定编号的钱包充值套餐

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 套餐编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验套餐存在，不存在抛 WALLET_RECHARGE_PACKAGE_NOT_FOUND；
2. 按编号删除套餐记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_008_011 | 钱包充值套餐不存在 |

### 3.4 获得钱包充值套餐

- **路径**: GET /pay/wallet-recharge-package/get
- **权限**: pay:wallet-recharge-package:query
- **说明**: 查询单个钱包充值套餐详情

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 套餐编号 |

**响应**: CommonResult&lt;WalletRechargePackageRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 套餐编号 |
| name | String | 套餐名 |
| payPrice | Integer | 支付金额，单位分 |
| bonusPrice | Integer | 赠送金额，单位分 |
| status | Byte | 状态（0 开启 / 1 禁用） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询套餐记录；
2. 转换为 WalletRechargePackageRespVO 返回（不存在时返回 null 数据）。

### 3.5 获得钱包充值套餐分页

- **路径**: GET /pay/wallet-recharge-package/page
- **权限**: pay:wallet-recharge-package:query
- **说明**: 按条件分页查询钱包充值套餐

**请求参数 (WalletRechargePackagePageReqVO)**（继承 PageParam，含 pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| name | String | 否 | - | 套餐名（模糊查询） |
| status | Integer | 否 | - | 状态（0 开启 / 1 禁用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;WalletRechargePackageRespVO&gt;&gt;，元素字段同 3.4。

**业务逻辑**:
1. 由 PayWalletRechargePackageMapper 按 name / status / createTime 条件分页查询；
2. 转换为 WalletRechargePackageRespVO 分页结果返回。

---

## 4. 钱包余额明细（PayWalletTransactionController）

### 4.1 获得钱包流水分页

- **路径**: GET /pay/wallet-transaction/page
- **权限**: pay:wallet:query
- **说明**: 管理端分页查询会员钱包流水（余额变动明细）

**请求参数 (PayWalletTransactionPageReqVO)**（继承 PageParam，含 pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| walletId | Long | 否 | - | 钱包编号 |
| userId | Long | 否 | - | 用户编号 |
| userType | Integer | 否 | @InEnum(UserTypeEnum) | 用户类型 |

**响应**: CommonResult&lt;PageResult&lt;PayWalletTransactionRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 流水编号 |
| walletId | Long | 钱包编号 |
| bizType | Integer | 业务分类（1 充值 / 2 充值退款 / 3 支付 / 4 支付退款 / 5 更新余额 / 6 转账） |
| price | Long | 交易金额，单位分（收入为正、支出为负） |
| title | String | 流水标题 |
| balance | Long | 交易后的余额，单位分 |
| createTime | LocalDateTime | 交易时间 |

**业务逻辑**:
1. 当 walletId 为空且 userId、userType 均非空时，调用 `getOrCreateWallet` 查询（必要时创建）该用户钱包，并将其编号回填到查询条件；
2. 由 PayWalletTransactionMapper 按 walletId 分页查询流水记录；
3. 转换为 PayWalletTransactionRespVO 分页结果返回。
