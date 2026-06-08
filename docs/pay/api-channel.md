# 渠道与应用管理 API 详解

> 业务域：支付应用管理、支付渠道配置、支付客户端工厂。

## 核心领域模型

**实体**：`PayApp`

- 支付应用是业务系统接入支付能力的入口
- 每个应用配置独立的回调地址（订单回调、退款回调）
- 支持多租户（继承 `TenantBaseDO`）

**实体**：`PayChannel`

- 支付渠道配置，关联到具体的支付客户端
- 每个渠道有独立的配置（`PayClientConfig` JSON）
- 支持多租户（继承 `TenantBaseDO`）
- 通过 `app_id` 关联到 `PayApp`，一个应用可有多个渠道

**值对象**：`PayClientConfig`

- 不同渠道有不同的配置实现：
  - `AlipayPayClientConfig`：支付宝配置（appId、privateKey、alipayPublicKey 等）
  - `WxPayClientConfig`：微信配置（appId、mchId、apiKey、certPath 等）

## HTTP 接口

### PayAppController

路径前缀：`/pay/app`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建应用 | POST | `/create` | 创建支付应用 |
| 更新应用 | PUT | `/update` | 更新应用配置 |
| 删除应用 | DELETE | `/delete` | 删除支付应用 |
| 查询应用 | GET | `/get` | 查询应用详情 |
| 分页查询 | GET | `/page` | 分页查询应用列表 |

### PayChannelController

路径前缀：`/pay/channel`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建渠道 | POST | `/create` | 创建支付渠道 |
| 更新渠道 | PUT | `/update` | 更新渠道配置 |
| 删除渠道 | DELETE | `/delete` | 删除支付渠道 |
| 查询渠道 | GET | `/get` | 查询渠道详情 |
| 分页查询 | GET | `/page` | 分页查询渠道列表 |

## 数据表

### pay_app

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 应用编号（主键） |
| `name` | `String` | 应用名称 |
| `status` | `Integer` | 开启状态 |
| `order_notify_url` | `String` | 订单回调地址 |
| `refund_notify_url` | `String` | 退款回调地址 |

### pay_channel

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Long` | 渠道编号（主键） |
| `code` | `String` | 渠道编码（如 `wx_pub`, `alipay_wap`） |
| `status` | `Integer` | 开启状态 |
| `fee_rate` | `Double` | 渠道费率 |
| `app_id` | `Long` | 应用编号（关联 pay_app） |
| `config` | `PayClientConfig` | 支付配置（JSON 存储） |

**关系**：`pay_app` 1:N `pay_channel`，通过 `app_id` 关联。

## 支付客户端工厂

### PayClientFactory

```java
public interface PayClientFactory {
    PayClient getPayClient(Long channelId);
    void refresh(Long channelId);  // 刷新指定渠道的客户端配置
}
```

### PayClientFactoryImpl 实现

**核心机制**：

1. **注册映射**：在构造函数中注册渠道编码与客户端类的映射关系
   ```java
   clientClass.put(WX_PUB, WxPubPayClient.class);
   clientClass.put(ALIPAY_WAP, AlipayWapPayClient.class);
   // ...
   ```

2. **创建客户端**：根据 `channelId` 查询 `PayChannelDO`，获取配置，反射创建客户端实例
   ```java
   ReflectUtil.newInstance(payClientClass, channelId, config);
   ```

3. **缓存机制**：已创建的客户端实例缓存，避免重复创建

4. **配置热刷新**：调用 `refresh(channelId)` 清除缓存，下次获取时重新创建

### PayClient 接口

```java
public interface PayClient {
    // 统一下单
    PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO);
    // 统一退款
    PayRefundRespDTO unifiedRefund(PayRefundUnifiedReqDTO reqDTO);
    // 统一转账
    PayTransferRespDTO unifiedTransfer(PayTransferUnifiedReqDTO reqDTO);
    // 解析支付回调
    PayOrderNotifyRespDTO parseOrderNotify(PayNotifyDataDTO notifyData);
    // 解析退款回调
    PayRefundNotifyRespDTO parseRefundNotify(PayNotifyDataDTO notifyData);
    // 查询订单
    PayOrderRespDTO getOrder(String outTradeNo);
    // 关闭订单
    void closeOrder(String outTradeNo);
}
```

### AbstractPayClient 模板方法

```java
public abstract class AbstractPayClient<T extends PayClientConfig> implements PayClient {
    protected Long channelId;
    protected String channelCode;
    protected T config;

    // 模板方法：统一下单
    public final PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
        ValidationUtils.validate(reqDTO);   // 1. 参数校验
        try {
            return doUnifiedOrder(reqDTO);   // 2. 子类实现
        } catch (Throwable ex) {
            throw buildPayException(ex);     // 3. 统一异常处理
        }
    }

    // 子类必须实现的抽象方法
    protected abstract PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO);
    protected abstract PayRefundRespDTO doUnifiedRefund(PayRefundUnifiedReqDTO reqDTO);
    protected abstract PayOrderRespDTO doGetOrder(String outTradeNo);
    protected abstract void doCloseOrder(String outTradeNo);
    protected abstract void doInit();
    // ...
}
```

## 渠道枚举

### PayChannelEnum

| 编码 | 名称 | 说明 |
|------|------|------|
| `wx_pub` | 微信公众号支付 | JSAPI 支付 |
| `wx_app` | 微信 App 支付 | App 内支付 |
| `wx_lite` | 微信小程序支付 | 小程序内支付 |
| `wx_native` | 微信 Native 支付 | 扫码支付 |
| `wx_h5` | 微信 H5 支付 | H5 页面支付 |
| `wx_mpay` | 微信付款码 | 商户扫用户付款码 |
| `alipay_pc` | 支付宝 PC 支付 | 电脑网站支付 |
| `alipay_wap` | 支付宝 WAP 支付 | 手机网站支付 |
| `alipay_app` | 支付宝 App 支付 | App 内支付 |
| `alipay_qr` | 支付宝扫码支付 | 用户扫商户二维码 |
| `alipay_bar` | 支付宝条码支付 | 商户扫用户条码 |
| `wallet` | 钱包支付 | 用户余额消费 |
| `mock` | 模拟支付 | 开发测试用 |

## 新增支付渠道步骤

1. 在 `PayChannelEnum` 添加渠道编码
2. 创建配置类实现 `PayClientConfig`
3. 创建客户端类继承 `AbstractPayClient<T>`
4. 在 `PayClientFactoryImpl` 注册映射
5. 编写单元测试

## 关键设计要点

1. **多租户**：`PayApp` 和 `PayChannel` 继承 `TenantBaseDO`，不同租户的应用和渠道隔离。

2. **配置热刷新**：修改渠道配置后，调用 `PayClientFactory.refresh(channelId)` 即可生效，无需重启。

3. **错误码**：`1_007_000_000`（App 不存在）、`1_007_001_000`（支付渠道配置不存在）。
