# 工厂模式

> **2026-10 增补**：适用时机、判定清单、JDK/Spring 经典示例、Map 注册表变体、与相关模式辨析
>
> **重要修正**：SmsClientFactoryImpl 实际位于 `yudao-module-system/.../framework/sms/`，而非 `yudao-module-infra`

## 模式定义

- **ID**：`factory-pattern`
- **名称**：工厂模式
- **分类**：创建型模式
- **描述**：把「实例化哪个具体类」的决策从调用方剥离，封装进独立创建逻辑（工厂类或工厂方法），调用方只依赖抽象产品接口

## 结构

### 参与者

| 角色 | 名称 | 说明 |
|------|------|------|
| 抽象工厂接口 | Factory | 声明创建产品对象抽象方法 |
| 具体工厂 | ConcreteFactory | 实现抽象工厂接口，创建具体产品 |
| 抽象产品 | Product | 定义产品共同接口 |
| 具体产品 | ConcreteProduct | 实现抽象产品接口的具体类 |

## 何时使用

### 信号 1：坏味道 —— 同一类里出现一长串 if-else / switch

- **解释**：这是最典型信号。收敛到工厂后，新增类型只改一处（注册表工厂甚至零改动）。判据是分支出现在两个以上位置、或单处分支已超过 5 个 case
- **项目案例**：`yudao-pay` 的 `PayClientFactoryImpl` 用「枚举→Class 注册表 + ReflectUtil.newInstance 反射」替代一长串 switch：`PayChannelEnum` 按渠道编码（wx_pub / wx_native / alipay_qr 等 14 种）路由到对应 PayClient，构造器注册、创建处零分支

### 信号 2：业务代码 import 了一堆具体实现类

- **解释**：依赖具体类意味着换实现、加实现都要动调用方；工厂让调用方只依赖抽象产品接口，具体类名从此只出现在工厂（或 Spring 配置）里
- **项目案例**：pay 模块内 `PayOrderServiceImpl` / `PayRefundServiceImpl` / `PayTransferServiceImpl` 只经 `PayChannelService#getPayClient` 获取 PayClient 抽象，从不 import `WxPayClient` / `AlipayQrPayClient` 等具体实现 —— 它们全部收敛在 `PayClientFactoryImpl` 的 clientClass 注册表一处

### 信号 3：实例化前后需要做一堆准备

- **解释**：构造器只该做简单字段赋值（Effective Java 建议）；需要缓存复用、读取配置、init 回调时，工厂方法是承载这些逻辑的正确位置 —— JDK 的 `Calendar#getInstance` 就是按 Locale 决定返回哪种实现
- **项目案例**：`yudao-module-system` 的 `SmsClientFactoryImpl`（注意：在 system 模块而非 infra）：`createOrUpdateSmsClient` 创建后调 `client.init()`，`channelIdClients` / `channelCodeClients` 双 Map 缓存，配置变更时对旧实例 refresh 而非重建

### 信号 4：实例化哪个类要等运行时才知道

- **解释**：具体类型由数据（而非编译期代码）决定时，不可能硬编码 new；必须有一个按 key 路由的创建环节，工厂 + 注册表是标准答案
- **项目案例**：`pay_channel` 表存渠道配置，`PayChannelServiceImpl#getPayClient` 读出 channel 后以 `channel.getCode()` / `channel.getConfig()` 调 `PayClientFactory#createOrUpdatePayClient` 动态创建客户端

### 信号 5：写的是框架 / 通用模块，要让第三方扩展

- **解释**：产品类型不可预知时 switch 工厂无法穷举；靠「注册 / 自动发现」把扩展点开放出去，新实现接入不需要改任何既有代码
- **项目案例**：两个层次 —— `yudao-ai` 的 `AiModelFactoryImpl` 按配置在 18 个 AI 平台间构建 ChatModel（运行时按键路由）；`yudao-bpm` 的 `BpmActivityBehaviorFactory` 继承 Flowable 的 `DefaultActivityBehaviorFactory` 覆写 `createUserTaskActivityBehavior`，是「框架把创建决策开放给子类」的更纯粹扩展点实例

### 信号 6：需要一次创建一组配套对象，且变体之间必须匹配

- **解释**：这是抽象工厂（Abstract Factory）的专属信号：工厂接口声明多个 createXxx 方法，每个具体工厂产出同风格的一族产品，从结构上杜绝错配；单产品线用抽象工厂纯属过度设计
- **项目案例**：本仓库暂无严格抽象工厂实例；最接近的是 `yudao-ai` 的 `AiModelFactoryImpl`（同一工厂声明 `getOrCreateChatModel` / `getOrCreateImageModel` / `getOrCreateEmbeddingModel` / `getOrCreateVectorStore` 多条产品线），但未强制变体成套替换约束，引用时请如实说明

### 信号 7：调用方还需要复用实例

- **解释**：工厂是创建唯一出口，所有实例都经过同一处代码，横切能力（缓存、计数、装饰）改一处即可全局生效
- **项目案例**：`PayClientFactoryImpl` 的 `clients` 按 channelId 缓存：`createOrUpdatePayClient` 对已存在实例只做 `client.refresh(config)` 而不重建，保证同一渠道编号全局唯一客户端句柄；`AiModelFactoryImpl` 用 hutool `Singleton.get` 按 cacheKey 达到同样效果

### 信号 8：单元测试想要替换创建过程

- **解释**：业务类通过工厂取对象，测试时换一个返回 mock 的工厂或 Supplier 即可；工厂是接缝（seam）
- **项目案例**：`PayChannelServiceTest` 直接 mock `payClientFactory.createOrUpdatePayClient(...)` 返回测试替身，使渠道服务测试不依赖真实支付宝 / 微信 SDK

## 何时不该使用

### 反模式 1：只有一个实现类，且近期需求清单里没有第二个实现迹象

- **理由**：工厂只是给直接 new 套了一层壳：多一个类、多一次跳转，却没有换回任何扩展点，属于典型过度设计
- **替代方案**：直接 new 或构造器注入，把工厂决策推迟到真正出现第二个实现的那天（YAGNI）

### 反模式 2：想要的是「不用每次写 new 的便捷创建」

- **理由**：这不需要工厂类 —— 静态工厂方法（`List.of()` / `Optional.ofNullable()`）更轻，还能起更有意义的名字、返回接口类型、控制实例数量
- **替代方案**：静态工厂方法（Static Factory Method, Effective Java Item 1）

### 反模式 3：变化维度是「同一个抽象的行为」而不是「创建哪个类」

- **理由**：工厂解决类型选择问题；如果对象已创建好、只是执行逻辑不同，再套一层工厂会得到「工厂返回对象行为各异」的模糊设计
- **替代方案**：策略模式（配合 Spring 注入 `Map<String, XxxStrategy>` 按名路由）

### 反模式 4：产品类型会持续膨胀，switch-case 工厂每加一个渠道就要改一次工厂代码

- **理由**：手写分支工厂违反开闭原则，且容易漏 case 导致运行时才暴露
- **替代方案**：Map 注册表（枚举 key→Supplier / Class）或让 Spring 自动收集 `List<接口>` / `Map<String, 接口>`；yudao 的 `PayClientFactoryImpl` / `FileClientFactoryImpl` 已演进为「枚举→Class 注册表 + 反射」

### 反模式 5：对象是 Spring 管理单例 Bean，创建与装配过程容器已经完成

- **理由**：手写工厂等于重复造 IoC 轮子，还要自己处理依赖注入和生命周期；BeanFactory 本身就是一个通用工厂
- **替代方案**：构造注入 + 注入 `Map<String, BeanType>`（Spring 按 Bean 名自动装配）或 `ObjectProvider`

### 反模式 6：纠结点是一个对象的多个字段怎么组装（可选参数多、构造器爆炸）

- **理由**：这是「组装问题」不是「类型选择问题」，为它建抽象工厂 + 产品族接口的成本远超收益
- **替代方案**：建造者模式（Builder）或带默认值的静态工厂方法重载

## 动手前自检清单

- [ ] 现在有几个实现？明确的需求清单里是否会出现第二个实现？（判断依据来自需求而非「将来也许」；只有一个就先直接 new，出现第二个时再重构成本很低）
- [ ] 变化维度是「创建哪个类」还是「同一个对象怎么做事」？前者用工厂，后者用策略模式；如果两个维度都在变，工厂 + 策略组合（工厂管创建与缓存，策略管行为）
- [ ] 具体实现类的类名是否已经泄漏到调用方（import 进 Controller / Service）？泄漏点越多、分布越广，工厂的收敛收益越大
- [ ] 产品类型是有限封闭（能用枚举穷举、加类型必须改代码）还是开放扩展（运行时配置、第三方注册）？封闭且少用枚举 switch 简单工厂，开放多用 Map 注册表
- [ ] 是否需要一次创建一组配套对象且变体之间必须匹配？是才上抽象工厂；只有一条产品线时抽象工厂是纯开销
- [ ] 创建过程是否昂贵或需复用（建连、初始化 SDK、读配置）？需要缓存 / 热刷新的话，工厂方法是放置 `ConcurrentMap` 缓存与 refresh 逻辑的正确位置

## 权威框架经典示例

### JDK 17 (java.base)

- **位置**：`java.util.Calendar` 静态方法 `getInstance()` / `getInstance(TimeZone, Locale)`
- **描述**：静态工厂方法（简单工厂）：根据 TimeZone / Locale 决定返回 `GregorianCalendar`、`JapaneseImperialCalendar`、`BuddhistCalendar` 等具体子类；调用方只依赖抽象 Calendar；同时是「构造器私有化 + 工厂方法」的标准写法（`protected` 构造器不对外）

### JDK (java.xml)

- **位置**：`javax.xml.parsers.DocumentBuilderFactory.newInstance()` / `newDefaultInstance()`，抽象方法 `newDocumentBuilder()`
- **描述**：抽象工厂 + 工厂方法：`protected` 构造器防止直接实例化；`newInstance()` 按「系统属性 → jaxp.properties → ServiceLoader → 平台默认」四步顺序返回厂商具体工厂（如 Xerces 的 `DocumentBuilderFactoryImpl`），抽象方法 `newDocumentBuilder()` 再产出具体解析器 DocumentBuilder；应用代码与 XML 解析器实现完全解耦

### Spring Framework (spring-aop, spring-beans)

- **位置**：`org.springframework.aop.framework.ProxyFactoryBean`，实现 `org.springframework.beans.factory.FactoryBean`（`getObject` / `getObjectType` / `isSingleton`）
- **描述**：FactoryBean 模式旗舰实现：容器 `getBean("x")` 返回的不是 ProxyFactoryBean 本身，而是其 `getObject()` 产出的 AOP 代理对象；内部由 `DefaultAopProxyFactory` 决策 JDK 动态代理还是 CGLIB；Spring Data 的 `JpaRepositoryFactoryBean` 也基于同一机制；取工厂本身需在 bean 名前加 `&` 前缀

### Spring Framework (spring-beans)

- **位置**：`org.springframework.beans.factory.BeanFactory` 接口（getBean 系列），默认实现 `DefaultListableBeanFactory`
- **描述**：IoC 容器本身就是一个超级工厂：按名称 / 类型 / 构造参数创建并装配全部 Bean，管理单例缓存与生命周期；官方「Container Extension Points」一章把 FactoryBean、BeanFactoryPostProcessor、BeanPostProcessor 列为标准扩展点；启示：手写工厂前先确认容器原生能力（注入 List / Map、ObjectProvider）是否已覆盖需求

### SLF4J 2.x

- **位置**：`org.slf4j.LoggerFactory.getLogger(String)` / `getLogger(Class)` / `getILoggerFactory()`，底层抽象 `org.slf4j.ILoggerFactory`
- **描述**：静态工厂门面：`LoggerFactory` 内部委托 classpath 上的 SLF4JServiceProvider（经 ServiceLoader 加载，2.0.9 起可用 `slf4j.provider` 系统属性显式指定）提供 ILoggerFactory 实例，按实际绑定（Logback / reload4j / log4j2 / NOP 兜底）返回 Logger 适配器；调用方与日志实现零耦合 ——「门面 + 可插拔工厂」的教科书组合

### MyBatis 3.5+

- **位置**：`org.apache.ibatis.session.SqlSessionFactory`（`openSession` 系列），由 `SqlSessionFactoryBuilder` 构建、`DefaultSqlSessionFactory` 实现
- **描述**：框架级工厂（常与建造者组合）：`SqlSessionFactoryBuilder` 读配置构建出单例 SqlSessionFactory，`openSession()` 每次按 ExecutorType / autoCommit / 事务级别组合产出配置好的 SqlSession；连接、事务、Executor 的装配细节全部封装

## 最小可读示例

### Spring Boot 通知渠道工厂（Map 注册表工厂，新增渠道零改动）

**场景**：站内消息中心需要支持短信 / 邮件 / 小程序订阅消息等多种发送渠道，渠道编码存在数据库配置中，业务代码按编码取发送器；后续还会陆续接入新渠道

```java
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.stereotype.Component;

/** 抽象产品：通知渠道发送器 */
public interface NotifySender {
    String channel();  // 自报路由键，供工厂注册
    void send(Long userId, String content);
}

/** 具体产品：短信渠道 */
@Component
public class SmsNotifySender implements NotifySender {
    @Override public String channel() { return "sms"; }
    @Override public void send(Long userId, String content) { /* 调短信网关 */ }
}

/** 具体产品：邮件渠道 */
@Component
public class MailNotifySender implements NotifySender {
    @Override public String channel() { return "mail"; }
    @Override public void send(Long userId, String content) { /* 调邮件服务 */ }
}

/** 工厂：Spring 自动收集所有 NotifySender 实现，构建不可变注册表 */
@Component
public class NotifySenderFactory {
    private final Map<String, NotifySender> senderMap;

    public NotifySenderFactory(List<NotifySender> senders) {
        this.senderMap = senders.stream().collect(Collectors.toUnmodifiableMap(
                NotifySender::channel, Function.identity()));
    }

    /** 按渠道编码路由，未知渠道立即失败 */
    public NotifySender getSender(String channel) {
        NotifySender sender = senderMap.get(channel);
        if (sender == null) {
            throw new IllegalArgumentException("未知通知渠道: " + channel);
        }
        return sender;
    }
}

// 调用方：notifySenderFactory.getSender("sms").send(userId, "验证码 6688");
```

**关键点**：

- 实现类通过 `channel()` 自报路由键，工厂用 Spring 注入的 `List<NotifySender>` 自动构建 Map 注册表 —— 新增渠道只需加一个 `@Component`，工厂与所有调用方零改动
- 工厂对外只暴露 `NotifySender` 接口，调用方不 import 任何具体实现类，创建决策完全收口在工厂
- 查不到渠道时抛出带渠道名的 `IllegalArgumentException` 立即失败，而不是返回 null 把错误推迟到 NPE
- 若创建过程昂贵（如短信渠道要初始化厂商 SDK），把 Map 换成 ConcurrentMap 缓存并在工厂里做配置热刷新 —— 这正是 yudao `SmsClientFactoryImpl`（`channelIdClients` / `channelCodeClients` 双缓存 + `createOrUpdateSmsClient` 走 refresh 复用）的做法
- 工厂管「造哪个对象」，`NotifySender` 各实现管「怎么发」—— 与策略模式天然分工，不要在工厂里混入发送业务逻辑

## 项目中的应用

### pay · PayClientFactoryImpl

- **目的**：创建支付渠道客户端（14 种），按 channelId 缓存实例，支持配置热刷新
- **代码路径**：`yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/impl/PayClientFactoryImpl.java`

```java
private final Map<PayChannelEnum, Class<? extends PayClient<?>>> clientClass = new ConcurrentHashMap<>();

@Override
@SuppressWarnings("unchecked")
public <Config extends PayClientConfig> PayClient createOrUpdatePayClient(Long channelId, String channelCode, Config config) {
    AbstractPayClient<Config> client = (AbstractPayClient<Config>) clients.get(channelId);
    if (client == null) {
        client = this.createPayClient(channelId, channelCode, config);
        client.init();
        clients.put(client.getId(), client);
    } else {
        client.refresh(config);
    }
    return client;
}
```

### system · SmsClientFactoryImpl

- **目的**：创建短信渠道客户端（阿里云 / 腾讯云 / 华为云 / 七牛 / 钉钉调试），双 Map 缓存 + refresh
- **代码路径**：`yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/framework/sms/core/client/impl/SmsClientFactoryImpl.java`

```java
private AbstractSmsClient createSmsClient(SmsChannelProperties properties) {
    SmsChannelEnum channelEnum = SmsChannelEnum.getByCode(properties.getCode());
    Assert.notNull(channelEnum, String.format("渠道类型(%s) 为空", channelEnum));
    switch (channelEnum) {
        case ALIYUN: return new AliyunSmsClient(properties);
        case DEBUG_DING_TALK: return new DebugDingTalkSmsClient(properties);
        case TENCENT: return new TencentSmsClient(properties);
        case HUAWEI: return new HuaweiSmsClient(properties);
        case QINIU: return new QiniuSmsClient(properties);
    }
    log.error("[createSmsClient][配置({}) 找不到合适的客户端实现]", properties);
    throw new IllegalArgumentException(String.format("配置(%s) 找不到合适的客户端实现", properties));
}
```

### infra · FileClientFactoryImpl

- **目的**：根据 `FileStorageEnum` 反射实例化本地 / DB / S3 / 七牛等存储客户端，按 configId 缓存
- **代码路径**：`yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/framework/file/core/client/FileClientFactoryImpl.java`

```java
private final ConcurrentMap<Long, AbstractFileClient<?>> clients = new ConcurrentHashMap<>();

@SuppressWarnings("unchecked")
private <Config extends FileClientConfig> AbstractFileClient<Config> createFileClient(
        LongId configId, Integer storage, Config config) {
    FileStorageEnum storageEnum = FileStorageEnum.getByStorage(storage);
    Assert.notNull(storageEnum, String.format("文件配置(%s) 为空", storageEnum));
    return (AbstractFileClient<Config>) ReflectUtil.newInstance(storageEnum.getClientClass(), configId, config);
}
```

### ai · AiModelFactoryImpl

- **目的**：按 AI 平台枚举创建并缓存 Spring AI 的 ChatModel / ImageModel / EmbeddingModel / VectorStore（ChatModel 分支覆盖 18 个平台）
- **代码路径**：`yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/model/AiModelFactoryImpl.java`

```java
@Override
public ChatModel getOrCreateChatModel(AiPlatformEnum platform, String rawApiKey, String rawUrl) {
    final String apiKey = resolveSpringPlaceholders(rawApiKey);
    final String url = resolveSpringPlaceholders(rawUrl);
    String cacheKey = buildClientCacheKey(ChatModel.class, platform, apiKey, url);
    return Singleton.get(cacheKey, (Func0<ChatModel>) () -> {
        switch (platform) {
            case TONG_YI: return buildTongYiChatModel(apiKey);
            // ... YI_YAN / DEEP_SEEK / DOU_BAO 等 13 个平台分支
            case OPENAI: return buildOpenAiChatModel(apiKey, url);
            case OLLAMA: return buildOllamaChatModel(url);
            default: throw new IllegalArgumentException(StrUtil.format("未知平台({})", platform));
        }
    });
}
```

### mall (trade) · ExpressClientFactoryImpl

- **目的**：按快递查询服务商枚举（快递鸟 / 快递100 / 无提供商）惰性创建并缓存
- **代码路径**：`yudao-module-mall/yudao-module-trade/src/main/java/cn/iocoder/yudao/module/trade/framework/delivery/core/client/impl/ExpressClientFactoryImpl.java`

```java
private final Map<ExpressClientEnum, ExpressClient> clientMap = new ConcurrentHashMap<>(8);

private ExpressClient createExpressClient(ExpressClientEnum queryProviderEnum,
                                           TradeExpressProperties tradeExpressProperties) {
    switch (queryProviderEnum) {
        case NOT_PROVIDE: return new NoProvideExpressClient();
        case KD_NIAO: return new KdNiaoExpressClient(restTemplate, tradeExpressProperties.getKdNiao());
        case KD_100: return new Kd100ExpressClient(restTemplate, tradeExpressProperties.getKd100());
    }
    return null;  // 注：此兜底返回 null 风格与 SmsClientFactoryImpl 抛异常风格不同，后者更值得推广
}
```

### system · AuthRequestFactory

- **目的**：把 52 个内置三方 OAuth2 平台 + 用户自定义扩展的 AuthRequest 创建集中到一处
- **代码路径**：`yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/framework/justauth/core/AuthRequestFactory.java`

```java
public AuthRequest get(String source) {
    if (StrUtil.isBlank(source)) throw new AuthException(AuthResponseStatus.NO_AUTH_SOURCE);
    AuthRequest authRequest = getDefaultRequest(source);
    if (authRequest == null) authRequest = getExtendRequest(properties.getExtend().getEnumClass(), source);
    if (authRequest == null) throw new AuthException(AuthResponseStatus.UNSUPPORTED);
    return authRequest;
}
// 先查内置枚举映射、再回退用户自定义扩展（反射实例化），体现「内置封闭集合 + 开放扩展兜底」的工厂结构
```

### bpm · BpmActivityBehaviorFactory

- **目的**：继承并覆写 Flowable 的 `DefaultActivityBehaviorFactory`，把用户任务 / 多实例节点 Behavior 替换为带候选人分配逻辑的 Bpm 自定义实现（典型工厂方法扩展点）
- **代码路径**：`yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/framework/flowable/core/behavior/BpmActivityBehaviorFactory.java`

```java
public class BpmActivityBehaviorFactory extends DefaultActivityBehaviorFactory {

    private BpmTaskCandidateInvoker taskCandidateInvoker;

    @Override
    public UserTaskActivityBehavior createUserTaskActivityBehavior(UserTask userTask) {
        return new BpmUserTaskActivityBehavior(userTask).setTaskCandidateInvoker(taskCandidateInvoker);
    }
}
```

## 变体

### 简单工厂 / 静态工厂方法（Simple Factory / Static Factory Method）

- **描述**：一个类持有一段 if-else / switch 创建逻辑，或直接用静态方法按参数返回不同实现（`Calendar#getInstance`、`List#of`）；静态工厂方法是 Effective Java Item 1 的第一选型
- **适用**：产品类型少且稳定（2-5 个）、创建逻辑只有几行、调用方就在同模块内；yudao 的 `SmsClientFactoryImpl`（5 渠道 switch）即此形态

### 工厂方法（Factory Method）

- **描述**：父类 / 接口中定义抽象创建方法，由子类决定实例化哪个具体产品；Spring `FactoryBean#getObject`、Flowable 的 `ActivityBehaviorFactory`（被 yudao `BpmActivityBehaviorFactory` 继承覆写）都是此形态
- **适用**：编写框架或模板基类时把「造什么」交给子类定制；产品创建依赖子类持有的上下文；refactoring.guru 强调它也适合复用昂贵资源（池化）的场景

### 抽象工厂（Abstract Factory）

- **描述**：一个工厂接口声明多个 createXxx 方法，每个具体工厂产出一族配套产品，从结构上保证变体之间不混配
- **适用**：产品存在多个维度且必须成套替换（如某支付渠道需同时提供下单 / 退款 / 对账三个配套客户端）；只有一条产品线时纯属多付一层接口的税 —— yudao 仓库内没有严格的抽象工厂实例，`AiModelFactoryImpl` 是近似形态

### Map 注册表工厂（Registry Factory）

- **描述**：key→Supplier / Class 的 Map，或利用 Spring 注入 `List<接口>` / `Map<String,接口>` 自动收集全部实现，运行时按键路由；实现类「自报 key」（如 `channel()`）避免集中维护映射，新增实现零改动
- **适用**：类型会持续膨胀的渠道类系统 —— Spring Boot 业务开发首选变体；yudao 的 `PayClientFactoryImpl`（枚举→Class 注册表 + 反射）与 `FileClientFactoryImpl`（枚举携带 ClientClass + 反射）即此风格

### 缓存 / 池化工厂（Caching Factory）

- **描述**：工厂方法内部用 `ConcurrentMap` 缓存已创建实例，支持配置 refresh 后复用而非重建；本质是把「实例化策略」（新建 / 池化 / 缓存）封装进工厂
- **适用**：对象创建昂贵（建连、加载厂商 SDK）、需要热更新配置而不重建实例、或需保证同一 channelId / configId 全局唯一实例；yudao 的 `PayClientFactoryImpl`、`SmsClientFactoryImpl`、`FileClientFactoryImpl` 三者结构完全一致（缓存 + createOrUpdate + refresh），可直接作为模板

## 与相关模式的辨析

### 策略模式

最易混淆、也最常成对出现：工厂解决「用哪个实现」（创建维度），策略解决「实现怎么做事」（行为维度）。选型口诀 —— 按类型选对象用工厂，按行为换算法用策略。yudao 中 `PayClientFactory`（工厂，含 channelId 缓存）+ `PayClient`（策略，各渠道 unifiedOrder / unifiedRefund 行为，经 `AbstractPayClient` 骨架落地）是标准组合，二者缺一不可但不互相替代

### 建造者模式

同为创建型但问题不同：工厂在「多个可替换产品中选一个」，Builder 在「一个复杂对象的多个可选字段分步组装」。决策依据是参数的数量而非类型：参数多、有可选字段选 Builder（如 Spring AI 各 `XxxChatModel.builder()`）；类型多、可替换选工厂（如 `AiModelFactoryImpl` 按平台选 ChatModel）

### 模板方法模式

常组合使用：工厂创建出的产品往往是模板方法的抽象子类 —— `AbstractSmsClient` 定义 final `init()` / `refresh()` 骨架，具体渠道子类填空；工厂（`SmsClientFactory`）负责决定实例化哪个模板子类。模板方法管「骨架复用」，工厂管「子类选择」

### 依赖注入 / IoC 容器

Spring 容器本质是一个通用工厂（`BeanFactory#getBean`），能靠注入 `List<T>` / `Map<String,T>` 或 `ObjectProvider` 解决时优先用容器能力（simple_example 正是靠注入 `List<NotifySender>` 免去手工注册）；手写工厂只保留给容器管不了的动态创建、按键路由与实例缓存场景

### 单例模式

工厂常在内部持有缓存以提供事实上的按 key 单例（`SmsClientFactoryImpl` 用 ConcurrentMap 双 Map 保证每个 channelId / code 只有一个 client；`AiModelFactoryImpl` 借 hutool `Singleton.get` 按 cacheKey 保证唯一），但职责不同：单例管「实例有几个」，工厂管「创建哪个、怎么创建、何时复用」

### 原型模式 / 享元模式

工厂方法是承载这些实例化策略的天然入口：同一个工厂方法内部可以返回全新对象、池化对象或共享缓存对象（对象池、连接池），这正是工厂方法「资源密集对象复用」适用性的直接体现；`FileClientFactoryImpl` / `PayClientFactoryImpl` 的 clients 缓存即是享元式的「按 key 共享」

## 优点

- 解耦创建逻辑和使用逻辑
- 便于扩展新产品类型
- 可以缓存和复用对象实例
- 统一管理对象生命周期

## 缺点

- 增加了类的数量
- 需要维护工厂类的实现（注册表工厂相对 switch 工厂可大幅减少该负担）

## 扩展指南

### 如何新增产品类型

1. **创建具体产品类**：实现 Product 接口；若使用 Map 注册表工厂则同时在枚举携带 Class（如 `PayClientFactoryImpl`）
2. **修改工厂创建逻辑**：在工厂中添加新类型的创建分支；若使用 Map 注册表则只需新增枚举值，工厂零改动
3. **添加配置支持**：添加配置枚举或配置项

**示例：新增短信渠道（轻量 switch 简单工厂）**

```java
// 1. 创建实现类
public class XxxSmsClient extends AbstractSmsClient {
    @Override protected void doInit() { ... }
    @Override public SmsSendResultDTO sendSms(SmsSendMessageDTO message) { ... }
}
// 2. 添加渠道枚举
public enum SmsChannelEnum { XXX(10, "XXX短信"); }
// 3. switch 简单工厂：在 SmsClientFactoryImpl 的 switch 中加 case XXX: return new XxxSmsClient(properties);
//    Map 注册表工厂：枚举携带 Class 后无需改工厂代码
```

## 参考文献

- <https://refactoring.guru/design-patterns/factory-method>
- <https://refactoring.guru/design-patterns/abstract-factory>
- <https://www.baeldung.com/java-creational-design-patterns>
- <https://docs.spring.io/spring/reference/6.2/core/beans/factory-extension.html>
- <https://www.slf4j.org/api/org/slf4j/LoggerFactory.html>
- <https://mybatis.org/mybatis-3/getting-started.html>
