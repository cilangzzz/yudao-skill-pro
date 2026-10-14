# 支付代码模式与扩展指南 (pay)

> 本文档移植自模块 Skill 知识库（skill-pay.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

常用注解：

- `@RestController`
- `@RequestMapping`
- `@PreAuthorize('@ss.hasPermission')`
- `@Operation(summary = ...)`

示例（支付提交接口使用 `@PermitAll` 允许匿名访问）：

```java
@RestController
@RequestMapping("/pay/order")
@Tag(name = "管理后台 - 支付订单")
public class PayOrderController {
    @PostMapping("/submit")
    @Operation(summary = "提交支付订单")
    @PermitAll  // 支付提交允许匿名访问
    public CommonResult<PayOrderSubmitRespVO> submitOrder(
            @RequestBody @Valid PayOrderSubmitReqVO reqVO,
            HttpServletRequest request) {
        return success(orderService.submitOrder(reqVO, getClientIP(request)));
    }
}
```

### Service 层规范

- 接口定义业务方法，使用 `@Valid` 注解校验参数
- 实现类使用 `@Service` 和 `@Validated` 注解，事务使用 `@Transactional`

示例（订单创建：先校验 App，再按商户订单号幂等查询，最后落库）：

```java
@Service
@Validated
@Slf4j
public class PayOrderServiceImpl implements PayOrderService {

    @Override
    public Long createOrder(PayOrderCreateReqDTO reqDTO) {
        // 1. 校验 App
        PayAppDO app = appService.validPayApp(reqDTO.getAppKey());

        // 2. 查询是否已存在
        PayOrderDO order = orderMapper.selectByAppIdAndMerchantOrderId(
                app.getId(), reqDTO.getMerchantOrderId());
        if (order != null) {
            return order.getId();
        }

        // 3. 创建订单
        order = PayOrderConvert.INSTANCE.convert(reqDTO)
                .setAppId(app.getId())
                .setStatus(PayOrderStatusEnum.WAITING.getStatus());
        orderMapper.insert(order);
        return order.getId();
    }
}
```

### 数据访问层（DAL）规范

Mapper 继承 `BaseMapperX`，使用 MyBatis-Plus 的 LambdaQueryWrapper：

```java
@Mapper
public interface PayOrderMapper extends BaseMapperX<PayOrderDO> {

    default PayOrderDO selectByAppIdAndMerchantOrderId(Long appId, String merchantOrderId) {
        return selectOne(PayOrderDO::getAppId, appId,
                         PayOrderDO::getMerchantOrderId, merchantOrderId);
    }

    default int updateByIdAndStatus(Long id, Integer status, PayOrderDO updateObj) {
        return update(updateObj, new LambdaUpdateWrapper<PayOrderDO>()
                .eq(PayOrderDO::getId, id)
                .eq(PayOrderDO::getStatus, status));
    }
}
```

> `updateByIdAndStatus` 这种「按 id + 期望状态更新」的写法是状态机并发安全的乐观锁基础，详见下文[最佳实践](#最佳实践)。

### 异常处理

错误码前缀：`1-007-XXX-XXX`。典型错误码示例：

| 错误码 | 说明 |
|--------|------|
| 1_007_000_000 | App 不存在 |
| 1_007_001_000 | 支付渠道的配置不存在 |
| 1_007_002_000 | 支付订单不存在 |
| 1_007_002_003 | 支付订单已经过期 |
| 1_007_006_000 | 退款金额超过订单可退款金额 |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE, args...)`

### 支付客户端（PayClient）使用示例

统一下单：

```java
// 1. 获取支付客户端
PayClient client = channelService.getPayClient(channelId);

// 2. 构建统一下单请求
PayOrderUnifiedReqDTO reqDTO = new PayOrderUnifiedReqDTO()
        .setOutTradeNo(orderExtension.getNo())
        .setSubject(order.getSubject())
        .setPrice(order.getPrice())
        .setExpireTime(order.getExpireTime())
        .setNotifyUrl(notifyUrl);

// 3. 调用支付渠道
PayOrderRespDTO respDTO = client.unifiedOrder(reqDTO);
```

统一退款：

```java
// 1. 获取支付客户端
PayClient client = channelService.getPayClient(channelId);

// 2. 构建退款请求
PayRefundUnifiedReqDTO reqDTO = new PayRefundUnifiedReqDTO()
        .setOutTradeNo(order.getNo())
        .setOutRefundNo(refund.getNo())
        .setRefundPrice(refund.getRefundPrice())
        .setReason(refund.getReason());

// 3. 调用退款接口
PayRefundRespDTO respDTO = client.unifiedRefund(reqDTO);
```

## 扩展指南

### 新增支付渠道（如添加银联支付）

#### 步骤 1：创建支付渠道枚举

文件：`PayChannelEnum.java`。添加新的渠道编码，如 `UNION_PAY("union_pay", "银联支付")`。

#### 步骤 2：创建配置类

文件：`UnionPayClientConfig.java`。实现 `PayClientConfig` 接口，定义银联支付所需的配置字段：

```java
@Data
public class UnionPayClientConfig implements PayClientConfig {
    private String merchantId;      // 商户号
    private String apiKey;          // API密钥
    private String certPath;        // 证书路径
    // ...
}
```

#### 步骤 3：创建抽象客户端类（可选）

文件：`AbstractUnionPayClient.java`。如果有多种支付方式（如扫码、APP），可以创建抽象类：

```java
public abstract class AbstractUnionPayClient
    extends AbstractPayClient<UnionPayClientConfig> {
    // 实现公共逻辑
}
```

#### 步骤 4：创建具体客户端实现类

文件：`UnionPayQrPayClient.java`。继承 `AbstractPayClient` 或抽象类，实现具体支付逻辑：

```java
public class UnionPayQrPayClient extends AbstractPayClient<UnionPayClientConfig> {

    public UnionPayQrPayClient(Long channelId, UnionPayClientConfig config) {
        super(channelId, PayChannelEnum.UNION_PAY.getCode(), config);
    }

    @Override
    protected void doInit() {
        // 初始化银联SDK
    }

    @Override
    protected PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
        // 调用银联下单接口
    }

    @Override
    protected PayOrderRespDTO doParseOrderNotify(...) {
        // 解析银联回调
    }

    // 实现其他抽象方法...
}
```

#### 步骤 5：注册到工厂

文件：`PayClientFactoryImpl.java`。在构造函数中注册新的客户端：

```java
public PayClientFactoryImpl() {
    // ...
    clientClass.put(UNION_PAY, UnionPayQrPayClient.class);
}
```

#### 步骤 6：添加单元测试

文件：`UnionPayQrPayClientTest.java`。编写测试用例验证支付流程。

### 新增业务功能

按分层架构自下而上创建：

| 步骤 | 内容 | 说明 |
|------|------|------|
| 1 | 创建 DO 实体 | 在 `dal/dataobject` 下创建实体类 |
| 2 | 创建 Mapper | 在 `dal/mysql` 下创建 Mapper 接口 |
| 3 | 创建 Service 接口和实现 | 在 `service` 下创建服务层 |
| 4 | 创建 Controller | 在 `controller` 下创建 HTTP 接口 |
| 5 | 创建 API（如需模块间调用） | 在 `api` 下创建对外 API 接口 |

### 最佳实践

- 支付金额统一使用 Integer 类型，单位为分，避免浮点精度问题
- 订单状态变更使用乐观锁，通过 `updateByIdAndStatus` 方法保证并发安全
- 支付回调需要验签，使用渠道提供的验签方法
- 异步通知需要支持重试机制，使用 `PayNotifyTask` 记录通知状态
- 支付订单需要设置过期时间，定时任务关闭过期订单
- 退款金额累计不能超过支付金额，在 Service 层进行校验
- 客户端配置支持热刷新，通过 refresh 方法更新配置

## 模块依赖

### 内部依赖（其他模块）

| 模块 | 依赖 API | 用途 |
|------|----------|------|
| yudao-module-system | TenantApi | 获取租户信息 |
| yudao-module-member | MemberUserApi | 获取用户信息（钱包支付） |

### 外部依赖（第三方库）

| 依赖 | 版本 | 用途 |
|------|------|------|
| alipay-sdk-java | 4.x | 支付宝支付 SDK |
| weixin-java-pay | 4.x | 微信支付 SDK（WxJava） |
| hutool-all | 5.x | Java 工具库 |
| mybatis-plus | 3.x | ORM 框架 |

> Framework starter（security、mybatis、redis、job、excel、tenant 等）与下游消费方（mall/trade）的整体依赖关系，参见 [README.md](README.md) 的「依赖关系」章节。

## 关键文件

| 文件路径 | 说明 |
|----------|------|
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/PayClient.java | 支付客户端接口，定义统一的支付/退款/转账方法 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/impl/AbstractPayClient.java | 支付客户端抽象基类，实现模板方法模式 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/impl/PayClientFactoryImpl.java | 支付客户端工厂，管理客户端创建和缓存 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/impl/alipay/AbstractAlipayPayClient.java | 支付宝支付抽象类，实现支付宝统一的接口 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/impl/weixin/AbstractWxPayClient.java | 微信支付抽象类，实现微信统一的接口 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/service/order/PayOrderServiceImpl.java | 支付订单服务实现，核心业务逻辑 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/service/refund/PayRefundServiceImpl.java | 退款服务实现 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/dal/dataobject/order/PayOrderDO.java | 支付订单实体 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/enums/PayChannelEnum.java | 支付渠道枚举 |
| yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/enums/ErrorCodeConstants.java | 错误码定义 |

## 领域模型

### 聚合根

- **PayOrder（支付订单聚合根）**：管理订单生命周期，包含实体 PayOrderExtension（支付交易拓展单）。不变式约束：
  - 订单状态流转：WAITING -> SUCCESS/REFUND/CLOSED
  - 退款金额不能超过支付金额
- **PayRefund（退款单聚合根）**：管理退款流程。不变式约束：
  - 退款状态流转：WAITING -> SUCCESS/FAILURE
  - 一个支付订单可以有多个退款单
- **PayChannel（支付渠道，实体）**：支付渠道配置，关联支付客户端
- **PayApp（支付应用，实体）**：支付应用，业务系统的支付入口

### 值对象

- **PayClientConfig（支付客户端配置）**：不同渠道有不同的配置类型，现有实现包括 `AlipayPayClientConfig`、`WxPayClientConfig`

### 领域服务

| 领域服务 | 职责 |
|----------|------|
| PayOrderService | 支付订单领域服务，负责订单创建、提交、回调处理 |
| PayRefundService | 退款领域服务，负责退款发起、回调处理 |
| PayChannelService | 渠道管理服务，负责渠道配置和客户端获取 |
| PayNotifyService | 通知服务，负责异步通知的处理和重试 |

## 设计与架构补充

以下内容为 [README.md](README.md) 已有描述之外的补充，不重复其已覆盖的部分。

### 业务定位补充

支付中台为整个系统提供统一的支付能力支持，核心能力清单：

1. **多渠道支付**：支持微信支付（JSAPI/小程序/App/Native/H5/付款码）、支付宝（PC/WAP/App/扫码/条码）、钱包支付、模拟支付
2. **统一退款**：支持全额退款和部分退款，自动处理退款状态同步
3. **转账功能**：支持企业付款到零钱、转账到银行卡
4. **钱包系统**：用户余额充值、消费、提现
5. **异步通知**：统一处理各渠道的支付/退款回调

### 设计原则补充

除 README 已覆盖的渠道客户端抽象、工厂/模板方法/策略模式外，本模块还遵循：

- **依赖倒置**：Service 层依赖 PayClient 接口而非具体实现
- **单一职责**：每个 PayClient 只负责对应渠道的支付逻辑

### 分层架构

| 层 | 职责 | 主要组件 |
|----|------|----------|
| api | 模块间 API 接口，供其他模块调用 | PayOrderApi（支付订单 API）、PayRefundApi（退款 API）、PayTransferApi（转账 API）、PayWalletApi（钱包 API） |
| controller | HTTP 接口，暴露给前端调用 | PayOrderController（支付订单管理）、PayRefundController（退款管理）、PayChannelController（渠道配置管理）、PayAppController（应用管理）、PayNotifyController（通知回调） |
| service | 业务逻辑层，核心领域服务 | PayOrderServiceImpl（订单创建、提交、回调）、PayRefundServiceImpl（退款创建、回调）、PayChannelServiceImpl（渠道管理）、PayNotifyServiceImpl（通知处理） |
| framework/pay/core/client | 支付客户端抽象层，对接各支付渠道 SDK | PayClient（客户端接口）、AbstractPayClient（抽象基类）、PayClientFactory（客户端工厂） |
| dal | 数据访问层 | PayOrderMapper（订单数据访问）、PayRefundMapper（退款数据访问）、PayChannelMapper（渠道数据访问） |

### 设计模式实现要点

工厂模式（`PayClientFactoryImpl`）——注册渠道与客户端类的映射，并反射创建实例：

```java
// 注册渠道与客户端类的映射
clientClass.put(WX_PUB, WxPubPayClient.class);
clientClass.put(ALIPAY_WAP, AlipayWapPayClient.class);

// 反射创建客户端实例
ReflectUtil.newInstance(payClientClass, channelId, config);
```

模板方法模式（`AbstractPayClient`）——统一下单流程，封装参数校验、子类实现与统一异常处理：

```java
// 模板方法：统一下单
public final PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
    ValidationUtils.validate(reqDTO);  // 参数校验
    try {
        return doUnifiedOrder(reqDTO);   // 子类实现
    } catch (Throwable ex) {
        throw buildPayException(ex);     // 统一异常处理
    }
}
```

### 表关系（ER）

| 主表 | 从表 | 关系 | 外键 | 说明 |
|------|------|------|------|------|
| pay_app | pay_channel | 1:N | app_id | 一个应用可以有多个支付渠道 |
| pay_app | pay_order | 1:N | app_id | 一个应用可以有多个支付订单 |
| pay_order | pay_order_extension | 1:N | order_id | 一个订单可以有多个扩展单（多次支付尝试） |
| pay_order | pay_refund | 1:N | order_id | 一个订单可以有多个退款单 |
| pay_channel | pay_order | 1:N | channel_id | 一个渠道可以有多个订单 |
