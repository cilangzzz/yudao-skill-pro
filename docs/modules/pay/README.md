# 支付模块 (pay)

> 提供统一支付网关能力：聚合支付宝、微信、钱包、模拟等多种支付渠道，覆盖应用/渠道管理、支付订单、退款、转账、回调通知、用户钱包全链路。

## 模块概述

- **模块路径**: yudao-module-pay
- **业务定位**: 作为平台的支付中台，向其他业务模块（如 mall 交易）提供创建支付单、发起退款、发起转账、操作钱包余额等标准化 API。内部通过渠道客户端（PayClient）抽象屏蔽支付宝/微信等三方 SDK 差异，并通过定时任务保证订单状态最终一致、回调通知可靠送达。
- **技术栈**: Spring Boot 3.x / MyBatis-Plus / Swagger v3（springdoc）/ Redis / 支付宝 SDK（alipay-sdk-java 4.40.607.ALL）/ 微信支付 SDK（weixin-java-pay）/ XXL-Job 定时任务 / Excel 导出

## 设计原则

| 原则 | 说明 |
|------|------|
| 渠道客户端抽象 | 所有支付渠道实现统一 `PayClient` 接口，`PayClientFactory` 按 channelId 创建并缓存客户端，新增渠道只需增加实现类 |
| 商户与支付分离 | 业务方只依赖 `api/` 包下的 PayOrderApi 等接口，通过 `merchantOrderId` 关联，支付细节完全收敛在 pay 模块内 |
| 状态机驱动 | 支付单/退款单/转账单均有明确状态枚举（待支付/成功/退款/关闭等），状态流转全部在 Service 层校验 |
| 可靠回调通知 | 支付结果通过 `PayNotifyTask` 异步通知业务方，失败自动重试（PayNotifyJob），每次尝试记录 `PayNotifyLog` |
| 定时任务兜底 | 订单过期（PayOrderExpireJob）、支付/退款/转账状态同步（PayOrderSyncJob 等）由 XXL-Job 定时补偿，保证最终一致 |
| 多租户隔离 | `pay_channel`、`pay_notify_task` 继承 TenantBaseDO 按租户隔离；三方回调入口使用 `@TenantIgnore` + 请求头解析租户 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|--------|------|----------|
| 支付应用 (app) | 维护支付应用（appKey、异步通知地址），一个应用可配置多个支付渠道 | PayAppDO |
| 支付渠道 (channel) | 配置应用下的支付渠道（微信/支付宝各类端、钱包、模拟），费率与渠道参数 JSON 存储 | PayChannelDO |
| 支付订单 (order) | 统一支付单创建、提交渠道支付、状态同步、过期处理、Excel 导出；交易拓展单保存渠道交互明细 | PayOrderDO、PayOrderExtensionDO |
| 退款订单 (refund) | 基于支付单发起部分/全额退款，同步退款状态，Excel 导出 | PayRefundDO |
| 转账单 (transfer) | 创建转账单（提现等场景），同步转账状态，Excel 导出 | PayTransferDO |
| 回调通知 (notify) | 接收渠道支付/退款/转账回调（PermitAll），维护通知任务与重试日志 | PayNotifyTaskDO、PayNotifyLogDO |
| 用户钱包 (wallet) | 会员钱包余额、冻结金额、余额明细、充值及充值套餐管理 | PayWalletDO、PayWalletTransactionDO、PayWalletRechargeDO、PayWalletRechargePackageDO |
| 示例订单 (demo) | 演示支付、退款、转账完整接入流程的示例代码（示例订单 + 示例提现单） | PayDemoOrderDO、PayDemoWithdrawDO |

## API 接口索引

### 支付应用信息 (PayAppController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/app/create | POST | 创建支付应用信息 | pay:app:create |
| /pay/app/update | PUT | 更新支付应用信息 | pay:app:update |
| /pay/app/update-status | PUT | 更新支付应用状态 | pay:app:update |
| /pay/app/delete | DELETE | 删除支付应用信息 | pay:app:delete |
| /pay/app/get | GET | 获得支付应用信息 | pay:app:query |
| /pay/app/page | GET | 获得支付应用信息分页 | pay:app:query |
| /pay/app/list | GET | 获得应用列表 | pay:merchant:query |

### 支付渠道 (PayChannelController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/channel/create | POST | 创建支付渠道 | pay:channel:create |
| /pay/channel/update | PUT | 更新支付渠道 | pay:channel:update |
| /pay/channel/delete | DELETE | 删除支付渠道 | pay:channel:delete |
| /pay/channel/get | GET | 获得支付渠道（支持 id 或 appId+code 查询） | pay:channel:query |
| /pay/channel/list | GET | 获得指定应用的支付渠道列表 | pay:channel:query |
| /pay/channel/get-enable-code-list | GET | 获得指定应用的开启的支付渠道编码列表 | 已认证 |

### 支付订单 (PayOrderController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/order/get | GET | 获得支付订单（可同步刷新状态） | pay:order:query |
| /pay/order/get-detail | GET | 获得支付订单详情（含交易拓展单） | pay:order:query |
| /pay/order/submit | POST | 提交支付订单 | 已认证 |
| /pay/order/page | GET | 获得支付订单分页 | pay:order:query |
| /pay/order/export-excel | GET | 导出支付订单 Excel | pay:order:export |

### 退款订单 (PayRefundController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/refund/get | GET | 获得退款订单 | pay:refund:query |
| /pay/refund/page | GET | 获得退款订单分页 | pay:refund:query |
| /pay/refund/export-excel | GET | 导出退款订单 Excel | pay:refund:export |

### 转账单 (PayTransferController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/transfer/get | GET | 获得转账订单 | pay:transfer:query |
| /pay/transfer/page | GET | 获得转账订单分页 | pay:transfer:query |
| /pay/transfer/export-excel | GET | 导出转账订单 Excel | pay:transfer:export |

### 回调通知 (PayNotifyController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/notify/order/{channelId} | POST | 支付渠道的统一【支付】回调 | @PermitAll（三方渠道回调） |
| /pay/notify/refund/{channelId} | POST | 支付渠道的统一【退款】回调 | @PermitAll（三方渠道回调） |
| /pay/notify/transfer/{channelId} | POST | 支付渠道的统一【转账】回调 | @PermitAll（三方渠道回调） |
| /pay/notify/get-detail | GET | 获得回调通知的明细 | pay:notify:query |
| /pay/notify/page | GET | 获得回调通知分页 | pay:notify:query |

### 用户钱包 (PayWalletController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/wallet/get | GET | 获得用户钱包明细 | pay:wallet:query |
| /pay/wallet/page | GET | 获得会员钱包分页 | pay:wallet:query |
| /pay/wallet/update-balance | PUT | 更新会员用户余额 | pay:wallet:update-balance |

### 钱包充值 (PayWalletRechargeController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/wallet-recharge/update-paid | POST | 更新钱包充值为已充值（内部回调） | @PermitAll（内部校验） |
| /pay/wallet-recharge/refund | POST | 发起钱包充值退款 | 已认证 |
| /pay/wallet-recharge/update-refunded | POST | 更新钱包充值为已退款（内部回调） | @PermitAll（内部校验） |

### 钱包充值套餐 (PayWalletRechargePackageController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/wallet-recharge-package/create | POST | 创建钱包充值套餐 | pay:wallet-recharge-package:create |
| /pay/wallet-recharge-package/update | PUT | 更新钱包充值套餐 | pay:wallet-recharge-package:update |
| /pay/wallet-recharge-package/delete | DELETE | 删除钱包充值套餐 | pay:wallet-recharge-package:delete |
| /pay/wallet-recharge-package/get | GET | 获得钱包充值套餐 | pay:wallet-recharge-package:query |
| /pay/wallet-recharge-package/page | GET | 获得钱包充值套餐分页 | pay:wallet-recharge-package:query |

### 钱包余额明细 (PayWalletTransactionController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/wallet-transaction/page | GET | 获得钱包流水分页 | pay:wallet:query |

### 示例订单 (PayDemoOrderController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/demo-order/create | POST | 创建示例订单 | 已认证 |
| /pay/demo-order/page | GET | 获得示例订单分页 | 已认证 |
| /pay/demo-order/update-paid | POST | 更新示例订单为已支付（内部回调） | @PermitAll（内部校验） |
| /pay/demo-order/refund | PUT | 发起示例订单的退款 | 已认证 |
| /pay/demo-order/update-refunded | POST | 更新示例订单为已退款（内部回调） | @PermitAll（内部校验） |

### 示例提现订单 (PayDemoWithdrawController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /pay/demo-withdraw/create | POST | 创建示例提现单 | 已认证 |
| /pay/demo-withdraw/transfer | POST | 提现单转账 | 已认证 |
| /pay/demo-withdraw/page | GET | 获得示例提现单分页 | 已认证 |
| /pay/demo-withdraw/update-transferred | POST | 更新示例提现单的转账状态（内部回调） | @PermitAll（内部校验） |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| pay_app | 支付应用信息 | BaseDO | app_key、name、status、order_notify_url、refund_notify_url、transfer_notify_url |
| pay_channel | 支付渠道配置 | TenantBaseDO | code（渠道编码）、status、fee_rate、app_id、config（渠道参数 JSON） |
| pay_order | 支付订单 | BaseDO | app_id、channel_code、merchant_order_id、price、status、no、extension_id、success_time、refund_price |
| pay_order_extension | 支付交易拓展单（渠道交互明细） | BaseDO | no、order_id、channel_code、channel_extras（JSON）、channel_notify_data、status |
| pay_refund | 退款订单 | BaseDO | no、order_id、merchant_refund_id、pay_price、refund_price、status、channel_refund_no |
| pay_transfer | 转账单 | BaseDO | no、merchant_transfer_id、price、user_account、user_name、status、channel_transfer_no |
| pay_notify_task | 支付通知任务 | TenantBaseDO | app_id、type（通知类型）、data_id、merchant_order_id、status、notify_times、max_notify_times、next_notify_time |
| pay_notify_log | 支付通知日志 | BaseDO | task_id、notify_times、response、status |
| pay_wallet | 用户钱包 | BaseDO | user_id、user_type、balance、freeze_price、total_expense、total_recharge |
| pay_wallet_recharge | 钱包充值记录 | BaseDO | wallet_id、total_price、pay_price、bonus_price、pay_order_id、pay_status、refund_status |
| pay_wallet_recharge_package | 钱包充值套餐 | BaseDO | name、pay_price、bonus_price、status |
| pay_wallet_transaction | 钱包流水明细 | BaseDO | no、wallet_id、biz_type、biz_id、title、price、balance |
| pay_demo_order | 示例订单（演示支付/退款接入） | BaseDO | user_id、spu_id、price、pay_status、pay_order_id、pay_refund_id |
| pay_demo_withdraw | 示例提现单（演示转账接入） | BaseDO | subject、price、user_account、type、status、pay_transfer_id |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|----------|------|
| 工厂模式 | `framework/pay/core/client/impl/PayClientFactoryImpl` | 按渠道编号创建并缓存 PayClient 实例，屏蔽客户端初始化细节 |
| 模板方法模式 | `framework/pay/core/client/impl/AbstractPayClient` | 定义客户端 init/execute 骨架（doInit、doUnifiedOrder 等），子类实现渠道细节 |
| 策略模式 | WxAppPayClient、AlipayPcPayClient、WalletPayClient、MockPayClient 等 14 个 PayClient 实现 | 同一支付动作在不同渠道下有不同的 SDK 调用实现，按渠道编码切换 |

## 依赖关系

- **上游**（本模块依赖）:
  - Framework starters: yudao-spring-boot-starter-biz-tenant、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-job、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-test
  - 业务模块: yudao-module-system（SocialClientApi：微信小程序发货信息录入、订阅消息发送）
  - 三方 SDK: alipay-sdk-java、weixin-java-pay
- **下游**（依赖本模块）:
  - yudao-module-mall（yudao-module-trade：支付/退款/转账/钱包 API 的主要消费方）

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|---------|------|--------|
| PayOrderApi | 创建/查询支付订单、同步支付状态 | yudao-module-mall (trade) |
| PayRefundApi | 创建支付退款 | yudao-module-mall (trade) |
| PayTransferApi | 创建转账单（提现） | yudao-module-mall (trade) |
| PayWalletApi | 查询/增减钱包余额、冻结/解冻 | yudao-module-mall (trade) |

> 另有 5 个内部定时任务：PayNotifyJob（回调重试）、PayOrderExpireJob（订单过期）、PayOrderSyncJob / PayRefundSyncJob / PayTransferSyncJob（状态同步）。

## 详细文档

- [api-app.md](api-app.md) - 支付应用
- [api-channel.md](api-channel.md) - 支付渠道
- [api-order.md](api-order.md) - 支付订单
- [api-refund.md](api-refund.md) - 退款订单
- [api-transfer.md](api-transfer.md) - 转账单
- [api-notify.md](api-notify.md) - 回调通知
- [api-wallet.md](api-wallet.md) - 用户钱包
- [api-demo.md](api-demo.md) - 示例订单
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
