# 数据模型详情

> pay 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

## 1. 实体继承体系

pay 模块共 14 个 DO，其中 12 个继承 `BaseDO`，2 个（渠道、通知任务）继承 `TenantBaseDO` 支持多租户隔离。

```text
BaseDO（cn.iocoder.yudao.framework.mybatis.core.dataobject）
├── creator      String          创建者（SysUser 的 id，INSERT 时自动填充）
├── createTime   LocalDateTime   创建时间（INSERT 时自动填充）
├── updater      String          更新者（INSERT_UPDATE 时自动填充）
├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 时自动填充）
└── deleted      Boolean         逻辑删除标记（@TableLogic）
    │
    ├── TenantBaseDO（cn.iocoder.yudao.framework.tenant.core.db）
    │   └── tenantId   Long   多租户编号（TenantLineHandler 自动注入过滤）
    │       ├── PayChannelDO      （pay_channel       支付渠道）
    │       └── PayNotifyTaskDO   （pay_notify_task   支付通知任务）
    │
    ├── PayAppDO                 （pay_app                    支付应用）
    ├── PayOrderDO               （pay_order                  支付订单）
    ├── PayOrderExtensionDO      （pay_order_extension        支付订单拓展）
    ├── PayRefundDO              （pay_refund                 支付退款单）
    ├── PayTransferDO            （pay_transfer               转账单）
    ├── PayNotifyLogDO           （pay_notify_log             支付通知日志）
    ├── PayWalletDO              （pay_wallet                 会员钱包）
    ├── PayWalletRechargeDO      （pay_wallet_recharge        钱包充值单）
    ├── PayWalletRechargePackageDO（pay_wallet_recharge_package 钱包充值套餐）
    ├── PayWalletTransactionDO   （pay_wallet_transaction     钱包流水）
    ├── PayDemoOrderDO           （pay_demo_order             示例订单）
    └── PayDemoWithdrawDO        （pay_demo_withdraw          示例提现单）
```

**使用规则**：

| 场景 | 基类 | 模块内对应 DO |
|-----|------|--------------|
| 支付渠道配置、跨租户回调通知任务 | `TenantBaseDO` | PayChannelDO、PayNotifyTaskDO（渠道密钥与通知必须按租户隔离，避免 A 租户拿到 B 租户的商户号发起支付） |
| 交易单据（订单/退款/转账）、钱包账务、示例业务 | `BaseDO` | 其余 12 个 DO（交易记录属平台级数据，金额流水不随租户自动过滤，由业务层 appId 隔离） |

> 金额字段单位统一为「分」（Integer/Long），费率为「百分比」（Double），数据库不使用 decimal，避免四舍五入误差。

## 2. 核心 DO 实体

### 2.1 应用与渠道聚合

#### PayAppDO (pay_app)

支付应用。一个商户（外部业务系统）接入 pay 模块时创建一个应用，承载三类回调地址。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 应用编号，数据库自增（@TableId） |
| appKey | String | app_key | 应用标识 |
| name | String | name | 应用名 |
| status | Integer | status | 状态，枚举 CommonStatusEnum（0 开启 / 1 禁用） |
| remark | String | remark | 备注 |
| orderNotifyUrl | String | order_notify_url | 支付结果的回调地址 |
| refundNotifyUrl | String | refund_notify_url | 退款结果的回调地址 |
| transferNotifyUrl | String | transfer_notify_url | 转账结果的回调地址 |

**继承**: BaseDO
**索引**: 主键 id。查询以 id 为主（PayAppMapper.selectPage / selectListByStatus）。

#### PayChannelDO (pay_channel)

支付渠道。一个应用（PayAppDO : PayChannelDO = 1 : n）下可配置多个支付渠道（微信 JSAPI、支付宝 PC 等）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 渠道编号，数据库自增 |
| code | String | code | 渠道编码，枚举 PayChannelEnum（wx_pub / wx_lite / alipay_pc 等 14 种） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| feeRate | Double | fee_rate | 渠道费率，单位：百分比 |
| remark | String | remark | 备注 |
| appId | Long | app_id | 应用编号，关联 PayAppDO#id |
| config | PayClientConfig | config | 支付渠道配置（密钥/证书/商户号），JSON 存储于 varchar(10240)，通过 PayClientConfigTypeHandler 序列化（autoResultMap = true），兼容老版本 @class 包路径反序列化为 AlipayPayClientConfig / WxPayClientConfig / NonePayClientConfig |

**继承**: TenantBaseDO（多租户，含 tenant_id 列）
**索引**: 主键 id。按 app_id 查询渠道列表（PayChannelMapper.selectListByAppId），即应用-渠道一对多的查询路径。

### 2.2 支付订单聚合

#### PayOrderDO (pay_order)

支付订单，模块的核心单据。业务系统调用 PayOrderApi 创建，成功后回写渠道信息。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 订单编号，数据库自增 |
| appId | Long | app_id | 应用编号，关联 PayAppDO#id |
| channelId | Long | channel_id | 渠道编号，关联 PayChannelDO#id |
| channelCode | String | channel_code | 渠道编码，枚举 PayChannelEnum |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型（UserTypeEnum：会员/管理员） |
| merchantOrderId | String | merchant_order_id | 商户订单编号，业务系统侧单号，需保证每个 PayAppDO 内唯一 |
| subject | String | subject | 商品标题 |
| body | String | body | 商品描述信息 |
| notifyUrl | String | notify_url | 异步通知地址 |
| price | Long | price | 支付金额，单位：分 |
| channelFeeRate | Double | channel_fee_rate | 渠道手续费率，单位：百分比，冗余 PayChannelDO#feeRate |
| channelFeePrice | Long | channel_fee_price | 渠道手续金额，单位：分 |
| status | Integer | status | 支付状态，枚举 PayOrderStatusEnum（0 待支付 / 1 成功 / 2 已退款 / 3 已关闭） |
| userIp | String | user_ip | 用户 IP |
| expireTime | LocalDateTime | expire_time | 订单失效时间（PayOrderExpireJob 按该字段扫描关单） |
| successTime | LocalDateTime | success_time | 订单支付成功时间 |
| extensionId | Long | extension_id | 支付成功的订单拓展单编号，关联 PayOrderExtensionDO#id |
| no | String | no | 支付成功的外部订单号，冗余 PayOrderExtensionDO#no（渠道 out_trade_no） |
| refundPrice | Long | refund_price | 退款总金额，单位：分（可多次部分退款累加） |
| channelUserId | String | channel_user_id | 渠道用户编号（微信 openid、支付宝 buyerOpenId） |
| channelOrderNo | String | channel_order_no | 渠道订单号（微信/支付宝侧交易号） |

**继承**: BaseDO
**索引**: 主键 id；`no` 单条查询（selectByNo）与 `(app_id, merchant_order_id)` 组合查询（selectByAppIdAndMerchantOrderId，防重复下单的唯一性校验依据）；过期任务按 status + expire_time 扫描。

#### PayOrderExtensionDO (pay_order_extension)

支付订单拓展单。每次调用支付渠道发起支付都会生成一条记录（同一订单可多次尝试支付，产生多条拓展单）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 订单拓展编号，数据库自增 |
| no | String | no | 外部订单号，按规则生成（如 P202110132239124200055），对应微信 out_trade_no / 支付宝 out_trade_no |
| orderId | Long | order_id | 订单号，关联 PayOrderDO#id |
| channelId | Long | channel_id | 渠道编号，关联 PayChannelDO#id |
| channelCode | String | channel_code | 渠道编码，枚举 PayChannelEnum |
| userIp | String | user_ip | 用户 IP |
| status | Integer | status | 支付状态，枚举 PayOrderStatusEnum（0 等待 / 1 成功 / 2 失败 / 3 关闭） |
| channelExtras | Map&lt;String, String&gt; | channel_extras | 支付渠道的额外参数，JSON TypeHandler（JacksonTypeHandler，autoResultMap = true）存储 |
| channelErrorCode | String | channel_error_code | 调用渠道的错误码 |
| channelErrorMsg | String | channel_error_msg | 调用渠道报错时的错误信息 |
| channelNotifyData | String | channel_notify_data | 支付渠道的同步/异步通知原始内容，对应 PayOrderRespDTO#rawData |

**继承**: BaseDO
**索引**: 主键 id；`no` 单条查询（selectByNo），渠道异步回调按 no 反查拓展单。orderId 为从属关系查询入口。

### 2.3 退款聚合

#### PayRefundDO (pay_refund)

支付退款单。一个支付订单（PayOrderDO : PayRefundDO = 1 : n）可多次部分退款，每次退款一条记录。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 退款单编号，数据库自增（@TableId） |
| no | String | no | 外部退款号，按规则生成，对应微信 out_refund_no / 支付宝 out_request_no |
| appId | Long | app_id | 应用编号，关联 PayAppDO#id |
| channelId | Long | channel_id | 渠道编号，关联 PayChannelDO#id |
| channelCode | String | channel_code | 渠道编码，枚举 PayChannelEnum |
| orderId | Long | order_id | 订单编号，关联 PayOrderDO#id |
| orderNo | String | order_no | 支付订单号，冗余 PayOrderDO#no |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型 |
| merchantOrderId | String | merchant_order_id | 商户订单编号 |
| merchantRefundId | String | merchant_refund_id | 商户退款订单号，需保证每个 PayAppDO 内唯一 |
| notifyUrl | String | notify_url | 异步通知地址 |
| status | Integer | status | 退款状态，枚举 PayRefundStatusEnum（0 生成 / 1 成功 / 2 失败 / 3 关闭） |
| payPrice | Long | pay_price | 支付金额，单位：分 |
| refundPrice | Long | refund_price | 退款金额，单位：分 |
| reason | String | reason | 退款原因 |
| userIp | String | user_ip | 用户 IP |
| channelOrderNo | String | channel_order_no | 渠道订单号，冗余 PayOrderDO#channelOrderNo |
| channelRefundNo | String | channel_refund_no | 渠道退款单号（微信 refund_id；支付宝无对应字段） |
| successTime | LocalDateTime | success_time | 退款成功时间 |
| channelErrorCode | String | channel_error_code | 调用渠道的错误码 |
| channelErrorMsg | String | channel_error_msg | 调用渠道的错误提示 |
| channelNotifyData | String | channel_notify_data | 支付渠道的同步/异步通知原始内容，对应 PayRefundRespDTO#rawData |

**继承**: BaseDO
**索引**: 主键 id；`no` 单条查询（selectByNo，渠道退款回调按 no 反查退款单）；退款分页按 appId / orderId / merchantRefundId 等条件组合查询。

### 2.4 转账聚合

#### PayTransferDO (pay_transfer)

转账单。业务系统（如示例提现、佣金提现）通过 PayTransferApi 发起，向收款人账户转账。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增（@TableId） |
| no | String | no | 转账单号，按规则生成 |
| appId | Long | app_id | 应用编号，关联 PayAppDO#id |
| channelId | Long | channel_id | 转账渠道编号，关联 PayChannelDO#id |
| channelCode | String | channel_code | 转账渠道编码，枚举 PayChannelEnum |
| userId | Long | user_id | 用户编号 |
| userType | Integer | user_type | 用户类型 |
| merchantTransferId | String | merchant_transfer_id | 商户转账单编号，需保证每个 PayAppDO 内唯一 |
| subject | String | subject | 转账标题 |
| price | Long | price | 转账金额，单位：分 |
| userAccount | String | user_account | 收款人账号 |
| userName | String | user_name | 收款人姓名 |
| status | Integer | status | 转账状态，枚举 PayTransferStatusEnum（0 等待 / 1 成功 / 2 失败，含待收款中间态） |
| successTime | LocalDateTime | success_time | 转账成功时间 |
| notifyUrl | String | notify_url | 异步通知地址 |
| userIp | String | user_ip | 用户 IP |
| channelExtras | Map&lt;String, String&gt; | channel_extras | 渠道的额外参数，JacksonTypeHandler JSON 存储（autoResultMap = true） |
| channelTransferNo | String | channel_transfer_no | 渠道转账单号 |
| channelErrorCode | String | channel_error_code | 调用渠道的错误码 |
| channelErrorMsg | String | channel_error_msg | 调用渠道的错误提示 |
| channelNotifyData | String | channel_notify_data | 渠道的同步/异步通知原始内容 |
| channelPackageInfo | String | channel_package_info | 渠道 package 信息，仅微信转账使用（JSAPI 调起用户确认收款场景） |

**继承**: BaseDO
**索引**: 主键 id；`no` 单条查询（selectByNo）；`(app_id, merchant_transfer_id)` 组合查询（selectByAppIdAndMerchantOrderId，防重复发起转账）。

### 2.5 回调通知聚合

#### PayNotifyTaskDO (pay_notify_task)

支付通知任务。支付/退款/转账结果产生后，pay 模块持续回调业务系统，直至成功（最多 1+8=9 次，间隔 15s/15s/30s/3min/30min/30min/30min/1h）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增（@TableId） |
| appId | Long | app_id | 应用编号，关联 PayAppDO#id |
| type | Integer | type | 通知类型，枚举 PayNotifyTypeEnum（1 支付订单 / 2 退款订单 / 3 转账单） |
| dataId | Long | data_id | 数据编号，按 type 多态关联：ORDER → PayOrderDO#id、REFUND → PayRefundDO#id、TRANSFER → PayTransferDO#id |
| merchantOrderId | String | merchant_order_id | 商户订单编号 |
| merchantRefundId | String | merchant_refund_id | 商户退款编号（type=REFUND 时有值） |
| merchantTransferId | String | merchant_transfer_id | 商户转账编号（type=TRANSFER 时有值） |
| status | Integer | status | 通知状态，枚举 PayNotifyStatusEnum（等待/成功/失败/请求成功但处理失败等） |
| nextNotifyTime | LocalDateTime | next_notify_time | 下一次通知时间（PayNotifyJob 按该字段扫描到期任务） |
| lastExecuteTime | LocalDateTime | last_execute_time | 最后一次执行时间 |
| notifyTimes | Integer | notify_times | 当前通知次数，对应日志表 notify_times |
| maxNotifyTimes | Integer | max_notify_times | 最大可通知次数 |
| notifyUrl | String | notify_url | 通知地址（取自 PayAppDO 的 orderNotifyUrl/refundNotifyUrl/transferNotifyUrl） |

**继承**: TenantBaseDO（多租户，含 tenant_id 列）
**索引**: 主键 id；通知任务调度按 status + next_notify_time 扫描（PayNotifyJob），按 appId/dataId 定位任务。

#### PayNotifyLogDO (pay_notify_log)

商户通知日志。每次向业务系统发起通知都记录一条，便于排查回调失败原因。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 日志编号，自增 |
| taskId | Long | task_id | 通知任务编号，关联 PayNotifyTaskDO#id |
| notifyTimes | Integer | notify_times | 第几次被通知，对应 PayNotifyTaskDO#notifyTimes |
| response | String | response | HTTP 响应结果（业务系统返回体） |
| status | Integer | status | 支付通知状态，枚举 PayNotifyStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；按 task_id 查询某任务的全部通知历史（PayNotifyLogMapper.selectListByTaskId）。

### 2.6 用户钱包聚合

#### PayWalletDO (pay_wallet)

会员钱包。按 (userId, userType) 一人一钱包，余额账务的汇总账户。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增（@TableId） |
| userId | Long | user_id | 用户 id，关联 MemberUserDO / AdminUserDO 的 id |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum（预留多商户转账） |
| balance | Integer | balance | 余额，单位：分 |
| freezePrice | Integer | freeze_price | 冻结金额，单位：分 |
| totalExpense | Integer | total_expense | 累计支出，单位：分 |
| totalRecharge | Integer | total_recharge | 累计充值，单位：分 |

**继承**: BaseDO
**索引**: 主键 id；(user_id, user_type) 单条查询（selectByUserIdAndType），即钱包的唯一业务定位键；支付下单时 PayOrderController#submit 对当前用户自动注入该钱包。

#### PayWalletRechargeDO (pay_wallet_recharge)

会员钱包充值单。充值走标准支付订单（PayOrderDO），支持「充 100 送 20」类赠送，可整单退款。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增（@TableId） |
| walletId | Long | wallet_id | 钱包编号，关联 PayWalletDO#id |
| totalPrice | Integer | total_price | 用户实际到账余额（实付 + 赠送，如充 100 送 20 则为 120） |
| payPrice | Integer | pay_price | 实际支付金额 |
| bonusPrice | Integer | bonus_price | 钱包赠送金额 |
| packageId | Long | package_id | 充值套餐编号，关联 PayWalletRechargePackageDO#id |
| payStatus | Boolean | pay_status | 是否已支付（true 已支付 / false 未支付） |
| payOrderId | Long | pay_order_id | 支付订单编号，关联 PayOrderDO#id |
| payChannelCode | String | pay_channel_code | 支付成功的支付渠道，冗余 PayOrderDO#channelCode |
| payTime | LocalDateTime | pay_time | 订单支付时间 |
| payRefundId | Long | pay_refund_id | 支付退款单编号，关联 PayRefundDO#id |
| refundTotalPrice | Integer | refund_total_price | 退款金额（包含赠送金额） |
| refundPayPrice | Integer | refund_pay_price | 退款支付金额 |
| refundBonusPrice | Integer | refund_bonus_price | 退款钱包赠送金额 |
| refundTime | LocalDateTime | refund_time | 退款时间 |
| refundStatus | Integer | refund_status | 退款状态，枚举 PayRefundStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；按 walletId 查询充值记录分页，payOrderId 用于支付成功回调（updatePaid）定位充值单。

#### PayWalletRechargePackageDO (pay_wallet_recharge_package)

会员钱包充值套餐。管理员配置「支付 X 元赠送 Y 元」的套餐，用户充值时选择。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增（@TableId） |
| name | String | name | 套餐名 |
| payPrice | Integer | pay_price | 支付金额，单位：分 |
| bonusPrice | Integer | bonus_price | 赠送金额，单位：分 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；管理端分页查询 + 状态过滤。

#### PayWalletTransactionDO (pay_wallet_transaction)

会员钱包流水。钱包每次余额变动（充值、支付、退款、套餐退回等）记录一条，含交易后余额快照，可完整重放账务。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增（@TableId） |
| no | String | no | 流水号 |
| walletId | Long | wallet_id | 钱包编号，关联 PayWalletDO#id |
| bizType | Integer | biz_type | 关联业务分类，枚举 PayWalletBizTypeEnum（1 交易 / 2 充值 / 3 支付 / 4 退款等） |
| bizId | String | biz_id | 关联业务编号（按 bizType 指向支付订单/充值单等，String 兼容不同单号） |
| title | String | title | 流水说明 |
| price | Integer | price | 交易金额，单位：分（正值余额增加，负值余额减少） |
| balance | Integer | balance | 交易后余额，单位：分 |

**继承**: BaseDO
**索引**: 主键 id；`no` 单条查询（selectByNo）；按 walletId 分页查询用户流水。

### 2.7 示例业务聚合（Demo）

#### PayDemoOrderDO (pay_demo_order)

示例订单。演示业务系统如何接入 pay 模块完成支付与退款（PayDemoOrderController + AppPayDemoOrderController）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 订单编号，自增（@TableId） |
| userId | Long | user_id | 用户编号 |
| spuId | Long | spu_id | 商品编号 |
| spuName | String | spu_name | 商品名称 |
| price | Integer | price | 价格，单位：分 |
| payStatus | Boolean | pay_status | 是否支付 |
| payOrderId | Long | pay_order_id | 支付订单编号，关联 PayOrderDO#id |
| payTime | LocalDateTime | pay_time | 付款时间 |
| payChannelCode | String | pay_channel_code | 支付渠道，枚举 PayChannelEnum |
| payRefundId | Long | pay_refund_id | 支付退款单号，关联 PayRefundDO#id |
| refundPrice | Integer | refund_price | 退款金额，单位：分 |
| refundTime | LocalDateTime | refund_time | 退款完成时间 |

**继承**: BaseDO
**索引**: 主键 id；按 payOrderId / payRefundId 接收 update-paid / update-refunded 内部回调更新状态。

#### PayDemoWithdrawDO (pay_demo_withdraw)

示例提现订单。演示业务系统如何通过 PayTransferApi 发起转账并接收结果。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 提现单编号，自增（@TableId） |
| subject | String | subject | 提现标题 |
| price | Integer | price | 提现金额，单位：分 |
| userAccount | String | user_account | 收款人账号 |
| userName | String | user_name | 收款人姓名 |
| type | Integer | type | 提现方式，枚举 PayDemoWithdrawTypeEnum（钱包余额 / 银行卡等） |
| status | Integer | status | 提现状态，枚举 PayDemoWithdrawStatusEnum |
| payTransferId | Long | pay_transfer_id | 转账单编号，关联 PayTransferDO#id |
| transferChannelCode | String | transfer_channel_code | 转账渠道，枚举 PayChannelEnum |
| transferTime | LocalDateTime | transfer_time | 转账成功时间 |
| transferErrorMsg | String | transfer_error_msg | 转账错误提示 |

**继承**: BaseDO
**索引**: 主键 id；按 payTransferId 接收 update-transferred 内部回调更新状态（autoResultMap = true）。

## 3. 实体关系

```text
PayAppDO (pay_app)
 │ 1
 ├─ n ── PayChannelDO (pay_channel)          appId → PayAppDO.id，config JSON 存渠道密钥
 │         │
 │         │（渠道被订单/退款/转账引用，channelId + channelCode 冗余渠道编码）
 │         ├─ n ── PayOrderDO.channelId
 │         ├─ n ── PayRefundDO.channelId
 │         ├─ n ── PayOrderExtensionDO.channelId
 │         └─ n ── PayTransferDO.channelId
 │
 ├─ n ── PayOrderDO (pay_order)              appId → PayAppDO.id
 │         │ 1
 │         ├─ n ── PayOrderExtensionDO       orderId → PayOrderDO.id（一次发起支付一条拓展单，
 │         │                                  支付成功后 PayOrderDO.extensionId/no 回写成功的那条）
 │         ├─ n ── PayRefundDO               orderId → PayOrderDO.id（多次部分退款，1 : n）
 │         │          └─ PayRefundDO.orderNo 冗余 PayOrderDO.no
 │         └─ 1 ── PayNotifyTaskDO           dataId 按 type 多态指向 PayOrderDO / PayRefundDO / PayTransferDO
 │                  │ 1
 │                  └─ n ── PayNotifyLogDO   taskId → PayNotifyTaskDO.id（每次回调一条日志）
 │
 ├─ n ── PayTransferDO (pay_transfer)        appId → PayAppDO.id
 │
 └─（回调地址）PayAppDO.orderNotifyUrl / refundNotifyUrl / transferNotifyUrl
              ↓ 被 PayNotifyTaskDO.notifyUrl 引用

PayWalletDO (pay_wallet)                     (userId, userType) 唯一定位
 │ 1
 ├─ n ── PayWalletRechargeDO                 walletId → PayWalletDO.id
 │         │         ├─ payOrderId  → PayOrderDO.id（充值走标准支付单）
 │         │         ├─ payRefundId → PayRefundDO.id（充值退款）
 │         │         └─ packageId   → PayWalletRechargePackageDO.id（充 X 送 Y 套餐）
 │
 └─ n ── PayWalletTransactionDO              walletId → PayWalletDO.id（bizType + bizId 指向
                                             支付订单 / 充值单等业务单据，price 正负记账）

PayDemoOrderDO (pay_demo_order)              payOrderId → PayOrderDO.id
                                             payRefundId → PayRefundDO.id
PayDemoWithdrawDO (pay_demo_withdraw)        payTransferId → PayTransferDO.id
```

关键多态关系：`PayNotifyTaskDO.dataId` 的含义由 `type` 决定（ORDER → 支付订单、REFUND → 退款单、TRANSFER → 转账单），配套的 `merchantOrderId` / `merchantRefundId` / `merchantTransferId` 三个商户侧单号字段也按 type 取值。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|----|------|
| pay_app | PayAppDO | 支付应用（商户接入载体，含三类回调地址） |
| pay_channel | PayChannelDO | 支付渠道（应用下多渠道配置，config JSON 密钥） |
| pay_order | PayOrderDO | 支付订单 |
| pay_order_extension | PayOrderExtensionDO | 支付订单拓展（每次发起支付一条，存渠道交互明细） |
| pay_refund | PayRefundDO | 支付退款单（一单多次部分退款） |
| pay_transfer | PayTransferDO | 转账单 |
| pay_notify_task | PayNotifyTaskDO | 支付通知任务（向业务系统重试回调） |
| pay_notify_log | PayNotifyLogDO | 支付通知日志（每次回调的 HTTP 响应记录） |
| pay_wallet | PayWalletDO | 会员钱包（余额/冻结/累计充值支出） |
| pay_wallet_recharge | PayWalletRechargeDO | 钱包充值单（含赠送金额与退款信息） |
| pay_wallet_recharge_package | PayWalletRechargePackageDO | 钱包充值套餐（充 X 送 Y） |
| pay_wallet_transaction | PayWalletTransactionDO | 钱包流水（含交易后余额快照） |
| pay_demo_order | PayDemoOrderDO | 示例订单（演示支付+退款接入） |
| pay_demo_withdraw | PayDemoWithdrawDO | 示例提现单（演示转账接入） |
