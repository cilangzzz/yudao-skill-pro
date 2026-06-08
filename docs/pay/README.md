# Pay 模块文档

> 支付中台模块 (`yudao-module-pay`)，为整个系统提供统一的支付能力支持。

## 模块概述

Pay 模块是系统的支付中台，通过策略模式和工厂模式对多渠道支付进行统一封装，对外暴露一致的支付、退款、转账、钱包接口。

**核心定位**：屏蔽各支付渠道（微信、支付宝、钱包、模拟支付）的差异，为业务模块提供标准化支付接入能力。

**支持的支付渠道**：

| 渠道 | 编码 | 支持方式 |
|------|------|----------|
| 微信支付 | `wx_pub`, `wx_app`, `wx_lite`, `wx_native`, `wx_h5`, `wx_mpay` | JSAPI / 小程序 / App / Native / H5 / 付款码 |
| 支付宝 | `alipay_pc`, `alipay_wap`, `alipay_app`, `alipay_qr`, `alipay_bar` | PC / WAP / App / 扫码 / 条码 |
| 钱包支付 | `wallet` | 用户余额消费 |
| 模拟支付 | `mock` | 开发测试 |

## 核心功能

| 功能域 | 说明 | 详细文档 |
|--------|------|----------|
| 支付订单 | 订单创建、提交支付、异步回调、状态同步 | [api-order.md](./api-order.md) |
| 退款 | 全额/部分退款、退款回调、状态同步 | [api-refund.md](./api-refund.md) |
| 钱包 | 余额充值、消费、提现、冻结 | [api-wallet.md](./api-wallet.md) |
| 转账 | 企业付款到零钱、转账到银行卡 | [api-transfer.md](./api-transfer.md) |
| 渠道与应用 | 支付应用管理、渠道配置、客户端工厂 | [api-channel.md](./api-channel.md) |
| 异步通知 | 回调处理、通知重试、任务管理 | [api-notify.md](./api-notify.md) |

## API 索引

### 模块间 API（供其他模块调用）

| API 接口 | 方法 | 消费方 |
|----------|------|--------|
| `PayOrderApi` | `createOrder`, `getOrder` | 订单模块、会员模块 |
| `PayRefundApi` | `createRefund`, `getRefund` | 订单模块 |
| `PayWalletApi` | `addBalance`, `getWallet` | 会员模块、订单模块 |
| `PayTransferApi` | - | 内部使用 |

### HTTP 接口（管理后台）

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| `PayOrderController` | `/pay/order` | 支付订单管理 |
| `PayRefundController` | `/pay/refund` | 退款管理 |
| `PayChannelController` | `/pay/channel` | 渠道配置管理 |
| `PayAppController` | `/pay/app` | 应用管理 |
| `PayNotifyController` | `/pay/notify` | 通知回调（各渠道异步回调入口） |

## 数据模型

共 9 张核心表，详见 [data-model.md](./data-model.md)。

| 表名 | 说明 | 继承 |
|------|------|------|
| `pay_app` | 支付应用表 | `TenantBaseDO` |
| `pay_channel` | 支付渠道表 | `TenantBaseDO` |
| `pay_order` | 支付订单表 | `BaseDO` |
| `pay_order_extension` | 支付订单扩展表 | `BaseDO` |
| `pay_refund` | 退款订单表 | `BaseDO` |
| `pay_wallet` | 钱包表 | `BaseDO` |
| `pay_wallet_transaction` | 钱包交易表 | `BaseDO` |
| `pay_transfer` | 转账表 | `BaseDO` |
| `pay_notify_task` | 通知任务表 | `BaseDO` |

## 设计模式

### 策略模式 + 模板方法 + 工厂模式

```
PayClient (接口)
  |
  +-- AbstractPayClient<T extends PayClientConfig> (模板方法基类)
        |
        +-- AbstractAlipayPayClient (支付宝公共逻辑)
        |     +-- AlipayPcPayClient
        |     +-- AlipayWapPayClient
        |     +-- AlipayAppPayClient
        |     +-- ...
        |
        +-- AbstractWxPayClient (微信公共逻辑)
        |     +-- WxPubPayClient
        |     +-- WxAppPayClient
        |     +-- WxLitePayClient
        |     +-- ...
        |
        +-- WalletPayClient (钱包支付)
        +-- MockPayClient (模拟支付)

PayClientFactory (工厂)
  - 根据渠道编码创建对应 PayClient
  - 缓存已创建的客户端实例
  - 支持配置热刷新
```

**关键设计决策**：

- `AbstractPayClient.unifiedOrder()` 是模板方法，定义统一流程：参数校验 -> 子类实现 -> 异常处理
- `PayClientFactoryImpl` 通过 `Map<String, Class<?>>` 注册渠道与客户端类的映射，反射创建实例
- 新增渠道只需：创建客户端类 -> 注册到工厂，无需修改现有代码（开闭原则）

## 架构分层

```
api/          -> 模块间接口 (PayOrderApi, PayRefundApi, PayWalletApi)
controller/   -> HTTP 接口层
service/      -> 业务逻辑层 (PayOrderServiceImpl, PayRefundServiceImpl, ...)
framework/    -> 支付客户端抽象层 (PayClient, AbstractPayClient, PayClientFactory)
dal/          -> 数据访问层 (Mapper)
enums/        -> 枚举定义
convert/      -> 对象转换器
```

## 定时任务

| Job | 说明 |
|-----|------|
| `PayOrderSyncJob` | 定时同步待支付订单状态（主动查询渠道） |
| `PayOrderExpireJob` | 定时关闭过期订单 |
| `PayNotifyJob` | 异步通知重试 |

## 依赖关系

### 内部模块依赖

| 模块 | API | 用途 |
|------|-----|------|
| `yudao-module-system` | `TenantApi` | 获取租户信息 |
| `yudao-module-member` | `MemberUserApi` | 获取用户信息（钱包支付） |

### 外部依赖

| 库 | 版本 | 用途 |
|----|------|------|
| `alipay-sdk-java` | 4.x | 支付宝支付 SDK |
| `weixin-java-pay` | 4.x | 微信支付 SDK（WxJava） |
| `hutool-all` | 5.x | Java 工具库 |
| `mybatis-plus` | 3.x | ORM 框架 |

## 错误码

错误码前缀：`1-007-XXX-XXX`

| 错误码 | 说明 |
|--------|------|
| `1_007_000_000` | App 不存在 |
| `1_007_001_000` | 支付渠道的配置不存在 |
| `1_007_002_000` | 支付订单不存在 |
| `1_007_002_003` | 支付订单已经过期 |
| `1_007_006_000` | 退款金额超过订单可退款金额 |

## 扩展指南

### 新增支付渠道

1. 在 `PayChannelEnum` 添加渠道编码
2. 创建配置类实现 `PayClientConfig`
3. 创建客户端类继承 `AbstractPayClient<T>`
4. 在 `PayClientFactoryImpl` 注册映射
5. 编写单元测试

详见 YAML 中 `extension_guide.new_channel` 部分。

## 常见陷阱

详见 [pitfalls.md](./pitfalls.md)。

## 关键文件

| 文件 | 说明 |
|------|------|
| `PayClient.java` | 支付客户端接口 |
| `AbstractPayClient.java` | 模板方法基类 |
| `PayClientFactoryImpl.java` | 客户端工厂 |
| `PayOrderServiceImpl.java` | 订单核心业务逻辑 |
| `PayRefundServiceImpl.java` | 退款业务逻辑 |
| `PayChannelEnum.java` | 渠道枚举 |
| `ErrorCodeConstants.java` | 错误码定义 |
