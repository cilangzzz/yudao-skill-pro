# 策略模式

> **2026-10 增补**：适用时机、判定清单、JDK/Spring 经典示例、6 种变体、与相关模式辨析
>
> **重要修正**：`SmsClient` 实际位于 `yudao-module-system/.../framework/sms/`，而非 `yudao-module-infra`

## 模式定义

- **ID**：`strategy-pattern`
- **名称**：策略模式
- **分类**：行为型模式
- **描述**：定义一族可互相替换的算法并各自封装，运行时按条件选择使用哪一个；Spring Boot 业务系统典型形态是「策略接口 + 多个 `@Component` 实现 + 构造器注入 `List` / `Map` 构建注册表」

## 结构

### 参与者

| 角色 | 名称 | 说明 |
|------|------|------|
| 策略接口 | Strategy | 定义所有支持算法公共接口；常含一个自报 key 的方法（如 `getStrategy()` / `supportChannel()`） |
| 具体策略 | ConcreteStrategy | 实现策略接口的具体算法 |
| 上下文 | Context | 维护对策略对象的引用；Spring 业务中常通过构造器注入 `List<Strategy>` 构建 Map 注册表 |

## 何时使用

### 信号 1：一个方法里出现长串 if/else 或 switch

- **解释**：把每个分支提为策略实现类后，主方法只剩「取策略→调用」两行，新增做法变成新增一个类（对扩展开放、对修改关闭）。这是 refactoring.guru 列出的核心适用条件之一之一之一 ——「your class has a massive conditional operator that switches between different variants of the same algorithm」
- **项目案例**：pay 模块 `PayClient`：14 个实现类（AlipayApp / Bar / Lite / Pc / Qr / Wap，WxApp / Bar / Lite / Native / Pub / Wap，Wallet、Mock），由 `PayClientFactoryImpl` 按 channelId 缓存实例；订单 / 退款 / 转账主流程零渠道分支

### 信号 2：多个类 90% 代码相同、只有一个方法体不同

- **解释**：GoF 原文适用条件之一：「许多相关的类仅仅是行为有异」。提取公共接口 + 抽象基类后，差异收敛到各实现类的唯一方法，公共代码上移到基类，修改公共逻辑不再需要同步改 N 个类
- **项目案例**：`AbstractPayClient`（pay 框架层 init / refresh 骨架 + `getConfig()` 等公共方法）与 `AbstractSmsClient`（system / framework / sms 抽象基类）；基类吃掉「SDK 初始化、配置解析、模板查询」等公共逻辑，差异收敛到各渠道子类的 `sendSms` / `unifiedOrder`

### 信号 3：需求方明确说「后面还要接新渠道 / 新模型 / 新存储引擎」

- **解释**：策略 + 注册表把「新增一种做法」的成本压到最低：实现接口、加 `@Component` 注解即完成注册，主流程零改动。这是策略相对 if/else 的核心收益；反之清单确定封顶，就先别抽
- **项目案例**：ai 模块 ChatModel：文心（`YiYanChatModel`）/ 智谱（`ZhiPuChatModel`）/ 豆包（`DouBaoChatModel`）/ 混元（`HunYuanChatModel`）/ 星火（`XingHuoChatModel`）/ Gemini 等 10 余个平台各有实现类，新增供应商仅需新增一个 `@Component`

### 信号 4：同一算法要按运行时外部输入切换，切换点散落在多处调用

- **解释**：把「选择逻辑」收敛到注册表一处（`Map.get(key)`），所有调用方只面向统一接口，不再各自维护分支；策略实现注册为单例缓存复用。这是 JDK `ThreadPoolExecutor` 拒绝策略体现的运行时可整体替换的策略形态
- **项目案例**：JDK `ThreadPoolExecutor` 持 `RejectedExecutionHandler` 字段并提供 `setRejectedExecutionHandler()`，默认 `AbortPolicy`（抛异常）可整体替换为 `CallerRunsPolicy`（调用方线程执行）或 `DiscardPolicy`（静默丢弃）；本项目内 PayClient 的 channelId 路由与该模式同构

### 信号 5：要对接多个第三方 SDK，内部代码只想面向一套自己定义稳定 API

- **解释**：策略接口充当防腐层（Anti-Corruption Layer, ACL）：SDK 的参数构造、签名、字段映射、错误码翻译等差异被各自实现类吸收，升级 SDK 或更换供应商只影响一个实现类，业务代码永远面向自己的接口
- **项目案例**：`PayClient` 隔离 wxjava / alipay SDK、`SmsClient` 隔离阿里云 / 腾讯云 / 华为云 / 七牛云 SDK；`FileClient` 隔离本地磁盘 / 数据库 / FTP / SFTP / S3（兼容 OSS / COS / 七牛）—— 三处都是同一形态的 ACL

### 信号 6：算法变体自身有依赖和状态

- **解释**：需要依赖注入、生命周期管理和按 key 缓存实例时，策略必须是 Spring 管理 bean；同时要设计好配置变更的生效机制（否则就会出现「配置改了但内存里的旧实例还在跑」这类经典踩坑）
- **项目案例**：`PayClientFactoryImpl` 用 `ConcurrentMap<Long, AbstractPayClient<?>>` 按 channelId 缓存客户端，配置变更时 `createOrUpdatePayClient` 走 `AbstractPayClient.refresh(config)` 的 equals 比对热更新（详见 `docs/pay/pitfalls.md` 的「配置热更新」踩坑点）

### 信号 7：单元测试需要把某个外部调用替换成桩

- **解释**：面向策略接口编码后，测试可以注入 Mock 实现或本地模拟渠道，主流程测试不再依赖真实第三方网络。依赖具体实现类的代码做不到这一点，是策略模式常被低估的收益
- **项目案例**：`BpmTaskCandidateInvoker` 构造时把 `List<BpmTaskCandidateStrategy>` 注入并建 Map，测试时可注入一个返回固定 userId 集合的假策略来覆盖流程分支，Flowable 引擎 / 部门 API 都可被绕开

### 信号 8：同一抽象下「选择逻辑」开始膨胀 —— 嵌套 switch

- **解释**：嵌套 switch 是注册表键设计不当的信号，而不是「继续叠分支」理由。把多个维度合成一个键对象，或用两级注册表（工厂先按渠道选 client，client 内部再按支付方式细分），保持每层只有一维选择
- **项目案例**：`PayClient` 先按渠道编码确定（14 个实现），渠道内的支付方式（App / 扫码 / H5 / Lite / Wap / Bar / PC / Native）由各自 client 实现内部区分 —— 例如 `AlipayQrPayClient` 专做扫码、`AlipayAppPayClient` 专做 App 唤起，避免一个类里写满嵌套 switch

## 何时不该使用

### 反模式 1：分支只有 2-3 个、每段逻辑一眼可见、且没有增长预期

- **理由**：为两个分支引入接口 + 两个实现类 + 注册表是纯粹的过度设计：多出几个文件、调用链多一层跳转，读者要在文件间反复横跳才能看懂一段三元运算符能表达事。条件分支数量少时并不是坏味道，YAGNI 优先
- **替代方案**：保留 if/else 或 switch；等第 4 个真实分支出现时再重构

### 反模式 2：每个分支只有一两行、无状态、无依赖的纯函数差异

- **理由**：不需要接口 + 类的完整结构：`Map<枚举, 函数>` 一行注册一行取用，类数量零增长，还能直接用方法引用。策略类的价值在于承载依赖与状态，纯函数场景它是累赘。JDK `Comparator` 本身就是 `@FunctionalInterface`，`Collections.sort` / `Stream.sorted` 配合 `comparing()` / `thenCompare()` 链式 lambda 即是事实范本
- **替代方案**：`Map<PayChannelEnum, Function<OrderBO, String>>` 注册表，或枚举常量体内实现抽象方法（Baeldung《A Guide to Java Enums》§7.2 的枚举策略写法）

### 反模式 3：差异只是参数取值不同，不是算法结构不同

- **理由**：「支付宝和微信的手续费率不同」是配置不是策略 —— 抽策略接口只会得到一堆除了常量全相同类。让策略接口保持「行为差异」的纯度，数据差异交给配置；参数差异让位给 `@Value` / `@ConfigurationProperties`
- **替代方案**：配置化：数据库配置表、`@ConfigurationProperties`、枚举属性字段

### 反模式 4：行为切换由对象内部状态驱动、状态会自主流转

- **解释**：refactoring.guru：State 可视为 Strategy 的扩展 —— 都靠组合委托改变行为，但 Strategy 的各实现互相独立、由外部一次选定；State 的各状态类可互相感知并主动驱动 context 切换流转。硬用策略实现状态机会把「流转」逻辑漏得到处都是
- **替代方案**：状态模式（简单状态机直接用状态字段 + 枚举方法即可，不必上类）

### 反模式 5：只想固定算法骨架、替换个别步骤

- **解释**：策略要求替换「整个算法」；若 80% 流程固定只有一两个钩子变化，抽成策略接口会让每个实现类重复抄写固定流程。Template Method 基于继承、作用于类层级（编译期固定）；Strategy 基于组合、作用于对象层级（运行时可换）。注意二者可叠加 —— `AbstractPayClient` 的 init / refresh 骨架是模板方法，各渠道 unifiedOrder 的差异是策略
- **替代方案**：模板方法（抽象基类固定骨架 + 受保护钩子方法）

### 反模式 6：策略方法需要十几个参数或一个巨型上下文对象才能工作

- **解释**：这是切分不当的信号：说明各「策略」并不在做同一件事，强行统一签名只会制造假抽象，接口沦为参数口袋。先拆分接口或换领域参数对象，再考虑策略；仍需要顺序尝试多个处理步骤时改用责任链
- **替代方案**：重新设计接口粒度（拆分接口、引入领域参数对象），或多阶段流程改用责任链

## 动手前自检清单

- [ ] 这些分支真的是「同一件事的不同做法」吗？能否写出让所有实现都自然满足统一方法签名？如果必须硬凑参数或空实现，先别抽策略
- [ ] 有没有具体业务证据表明清单会增长（排期中已确认「下季度接云片短信 / 银联支付」），还是只是「将来可能」？前者抽策略，后者保留 if/else
- [ ] 每个算法变体需要注入哪些依赖（SDK client、Redis、配置）、持有哪些状态？如果都不需要，Map+lambda 或枚举实现就够了，不必为此建类
- [ ] 策略如何被选中：调用方显式传入、注册表按 key 查找、还是 Spring 按 bean 名称 / 类型注入？key 查不到时抛什么错误码、由谁兜底？—— 本项目 `docs/pay/pitfalls.md` 记录过 `PayClientFactoryImpl.getPayClient` 查不到仅打 error 日志返回 null 的踩坑，新代码务必显式抛错
- [ ] 策略实现应是无状态单例（`@Component` 即可），还是按配置实例化并缓存（如 `PayClientFactoryImpl` 按 channelId 缓存 + refresh 热更新）？策略里能放可变字段吗？缓存的 equals 键（如 `PayClientConfig`）需不需要 `@Data` equals 实现？
- [ ] 选择逻辑收敛在哪一层？能否保证业务代码中除注册表构建处外，不再出现任何按渠道 / 类型的 if/else？若仍残留 switch，说明键设计维度错了（可能需要拆成两级注册表或换成键对象）

## 权威框架经典示例

### JDK (java.util)

- **位置**：`java.util.Comparator`（配合 `Collections.sort` / `Arrays.sort` / `List.sort` / `Stream.sorted` 使用）
- **描述**：JDK 排序框架的策略：`Collections.sort` / `Arrays.sort` / `List.sort` / `Stream.sorted` 骨架固定，「如何比较两个元素」作为 `Comparator` 实例由调用方传入，同一份排序代码配合不同比较器产生不同排序结果。Java 8 起 `Comparator` 是 `@FunctionalInterface`，lambda 与 `comparing()` / `thenComparing()` 组合子即轻量策略。refactoring.guru 将其列为 Java 核心库中的策略实例

### JDK (java.util.concurrent)

- **位置**：`java.util.concurrent.ThreadPoolExecutor` 内部接口 `RejectedExecutionHandler` 及四个静态嵌套实现 `AbortPolicy` / `CallerRunsPolicy` / `DiscardPolicy` / `DiscardOldestPolicy`
- **描述**：线程池队列满时的「拒绝策略」：`ThreadPoolExecutor` 持有 `RejectedExecutionHandler` 字段，可通过 `setRejectedExecutionHandler()` 在运行时整体替换；内置策略覆盖抛异常（默认 `AbortPolicy`，适合支付类关键任务）/ 调用者线程执行（`CallerRunsPolicy`）/ 静默丢弃（`DiscardPolicy`）/ 丢弃最旧任务（`DiscardOldestPolicy`），业务也可自定义（如将被拒任务写入 Redis 重试队列）。是「可热插拔策略」变体的教科书实现

### JDK (java.time, Java 8+)

- **位置**：`java.time.temporal.TemporalAdjuster`（配套工具类 `java.time.temporal.TemporalAdjusters`）
- **描述**：Javadoc 原文「Strategy for adjusting a temporal object」：「如何调整日期」的算法被外置为可传参的策略对象，通过 `temporal.with(adjuster)` 应用；`TemporalAdjusters` 提供标准实现（`nextOrSame(DayOfWeek)`、`lastDayOfMonth` 等），业务可自定义 lambda 策略（如「跳过周末取下一个工作日」）。`@FunctionalInterface`，配合方法引用使用

### Spring Framework (spring-beans)

- **位置**：`org.springframework.beans.factory.support.InstantiationStrategy` —— 实现 `SimpleInstantiationStrategy` / `CglibSubclassingInstantiationStrategy`
- **描述**：Spring 容器创建 bean 实例的策略接口：`AbstractAutowireCapableBeanFactory` 持有该策略，「用反射构造还是 CGLIB 生成子类」这一算法选择被封装在策略内部，容器主流程不感知。`CglibSubclassingInstantiationStrategy` 的 Javadoc 自述为「Default object instantiation strategy for use in BeanFactories」

### Spring Framework (spring-core)

- **位置**：`org.springframework.core.io.ResourceLoader` —— 实现 `DefaultResourceLoader` / `FileSystemResourceLoader` / `ClassRelativeResourceLoader` / `ServletContextResourceLoader` 等
- **描述**：Javadoc 原文「Strategy interface for loading resources (for example, class path or file system resources)」：「把 location 字符串解析为 Resource 句柄」的算法可整体替换 —— `classpath:` / `file:` / URL 前缀识别封装在 `DefaultResourceLoader` 内，ServletContext 场景换用 `ServletContextResourceLoader`，ApplicationContext 自身也继承该策略接口

### Spring Security (spring-security-crypto)

- **位置**：`org.springframework.security.crypto.password.PasswordEncoder` —— 中心实现 `DelegatingPasswordEncoder` 按 `{id}` 前缀分发到 `BCryptPasswordEncoder` / `Pbkdf2PasswordEncoder` / `SCryptPasswordEncoder` / `NoOpPasswordEncoder`
- **描述**：以 key 分发策略的官方示范：存库密码串自带 `{bcrypt}`、`{noop}`、`{pbkdf2}`、`{scrypt}` 前缀，`DelegatingPasswordEncoder` 解析前缀后路由到对应编码器 —— 相当于一个以 id 为 key 的策略注册表，同时兼容历史编码并支持新密码渐进升级算法（`PasswordEncoderFactories.createDelegatingPasswordEncoder()` 默认编码为 bcrypt）

## 最小可读示例

### 支付渠道下单：策略接口 + Spring 注入注册表（无需手写工厂）

**场景**：电商订单按用户选择支付渠道（支付宝扫码 / 微信 Native）发起下单：各渠道 SDK 调用、参数构造差异封装在各自策略类中，下单主流程只面对统一接口；新增银联支付只需新增一个 `@Component` 实现类，存量代码零改动。本项目 bpm 模块 `BpmTaskCandidateInvoker` + `BpmTaskCandidateStrategy` 即此形态，pay 模块的 `PayClient` + `PayClientFactoryImpl` 是其「按配置实例化并缓存」的重量级变体

```java
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

// ===== 策略接口：统一所有支付渠道的「下单」算法签名 =====
public interface PayChannelHandler {
    PayChannelEnum supportChannel();          // 注册表键：本策略负责的渠道
    String createOrder(PayOrderBO order);     // 返回支付凭证/跳转参数
}

// ===== 具体策略：每个渠道一个 @Component，SDK 差异全部封装在实现内 =====
@Component
public class AlipayQrHandler implements PayChannelHandler {
    public PayChannelEnum supportChannel() { return PayChannelEnum.ALIPAY_QR; }
    public String createOrder(PayOrderBO order) {
        return alipaySdk.precreate(order.orderNo(), order.amount());
    }
}

@Component
public class WechatNativeHandler implements PayChannelHandler {
    public PayChannelEnum supportChannel() { return PayChannelEnum.WECHAT_NATIVE; }
    public String createOrder(PayOrderBO order) {
        return wxPayService.createNativeV3(order.orderNo(), order.amount());
    }
}

// ===== 上下文：Spring 注入全部策略构建注册表，主流程零渠道分支 =====
@Service
public class PayOrderService {
    private final Map<PayChannelEnum, PayChannelHandler> handlerMap;

    public PayOrderService(List<PayChannelHandler> handlers) {   // Spring 自动收集容器内全部实现
        this.handlerMap = handlers.stream()
                .collect(Collectors.toMap(PayChannelHandler::supportChannel, Function.identity()));
    }

    public String createOrder(PayChannelEnum channel, PayOrderBO order) {
        PayChannelHandler handler = handlerMap.get(channel);
        if (handler == null) {
            throw new IllegalArgumentException("不支持的支付渠道: " + channel);
        }
        return handler.createOrder(order);
    }
}

// 配套定义：record PayOrderBO(String orderNo, int amount) {}
//            enum PayChannelEnum { ALIPAY_QR, WECHAT_NATIVE }
// 新增银联渠道 = 仅新增 UnionPayHandler implements PayChannelHandler 并标注 @Component
```

**关键点**：

- 策略接口只含两个职责：声明自己负责的 key（`supportChannel`）+ 执行算法（`createOrder`）；key 由实现类自声明，注册过程对实现类零侵入
- 构造器注入 `List<PayChannelHandler>`，Spring 会自动收集容器内全部实现 bean —— 注册表由框架构建，新增渠道 = 新增一个类，主流程零 if/else、零改动
- 上下文（`PayOrderService`）是唯一感知所有策略存在的地方；key 查不到时显式抛异常，不静默返回 null（`docs/pay/pitfalls.md` 明确记录过 `PayClientFactoryImpl.getPayClient` 查不到仅打 error 日志返回 null 导致的踩坑）
- 策略实现默认无状态单例（`@Component` singleton）；若渠道需要按配置初始化的 SDK client，参考 `PayClientFactoryImpl`：按 channelId 缓存实例 + 配置变更时 refresh 热更新
- 若某渠道实现只有一两行，可降级为 `Map<PayChannelEnum, Function<PayOrderBO, String>>` + lambda / 方法引用，不必为此建类
- 单元测试时向 `PayOrderService` 注入一个假 `PayChannelHandler` 即可覆盖主流程，无需 mock 整个第三方 SDK

## 项目中的应用

### pay · PayClient 接口

- **目的**：屏蔽 14 种支付渠道 SDK 差异，订单 / 退款 / 转账业务只面向统一接口
- **代码路径**：`yudao-module-pay/src/main/java/cn/iocoder/yudao/module/pay/framework/pay/core/client/PayClient.java`
- **策略**：
  - AlipayApp / Bar / Lite / Pc / Qr / Wap（6 个）
  - WxApp / Bar / Lite / Native / Pub / Wap（6 个）
  - WalletPayClient、MockPayClient

```java
public interface PayClient<Config> {
    Long getId();
    Config getConfig();
    PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO);
    PayRefundRespDTO unifiedRefund(PayRefundUnifiedReqDTO reqDTO);
    // ... 另有 parseOrderNotify、getOrder、parseRefundNotify、getRefund、
    //     unifiedTransfer、getTransfer、parseTransferNotify 等方法
}
// 具体策略 14 个，由 PayClientFactoryImpl 按 PayChannelEnum 枚举维护 clientClass 注册表、
// 按 channelId(Long) 缓存运行时实例，配置变更走 AbstractPayClient.refresh(config) 热更新
// 注意：getPayClient 查不到仅打 error 日志返回 null 是项目内已知踩坑点（docs/pay/pitfalls.md）
```

### system · SmsClient 接口

- **目的**：屏蔽阿里云 / 腾讯云 / 华为云 / 七牛 / 钉钉调试等短信平台 SDK 差异
- **代码路径**：`yudao-module-system/src/main/java/cn/iocoder/yudao/module/system/framework/sms/core/client/SmsClient.java`
- **策略**：
  - AliyunSmsClient、TencentSmsClient、HuaweiSmsClient、QiniuSmsClient、DebugDingTalkSmsClient

```java
public interface SmsClient {
    Long getId();
    SmsSendRespDTO sendSms(Long logId, String mobile, String apiTemplateId,
                           List<KeyValue<String, Object>> templateParams) throws Throwable;
    List<SmsReceiveRespDTO> parseSmsReceiveStatus(String text) throws Throwable;
    SmsTemplateRespDTO getSmsTemplate(String apiTemplateId) throws Throwable;
}
// 注意：该接口实际位于 system 模块的 framework/sms 目录（而非 infra）
```

### infra · FileClient 接口

- **目的**：屏蔽本地磁盘 / 数据库 / FTP / SFTP / S3 等文件存储介质的差异
- **代码路径**：`yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/framework/file/core/client/FileClient.java`
- **策略**：
  - LocalFileClient、DBFileClient、FtpFileClient、SftpFileClient、S3FileClient（兼容 OSS / COS / 七牛等）

```java
public interface FileClient {
    Long getId();
    String upload(byte[] content, String path, String type) throws Exception;
    void delete(String path) throws Exception;
    byte[] getContent(String path) throws Exception;
    // presignPutUrl / presignGetUrl 是 default 方法，仅 S3FileClient 选择性重写
}
```

### ai · ChatModel 接口（Spring AI 提供）

- **目的**：在 10 余个大模型间按配置切换；豆包是「组合复用」的典型实现（委托给 OpenAI 兼容协议的 openAiChatModel）
- **代码路径**：`yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/model/doubao/DouBaoChatModel.java`
- **策略**：
  - DouBaoChatModel、ZhiPuChatModel、YiYanChatModel、HunYuanChatModel、XingHuoChatModel、GeminiChatModel 等 10 余个

```java
@RequiredArgsConstructor
public class DouBaoChatModel implements ChatModel {
    // 兼容 OpenAI 接口，进行复用
    private final ChatModel openAiChatModel;
    @Override public ChatResponse call(Prompt prompt) { return openAiChatModel.call(prompt); }
    @Override public Flux<ChatResponse> stream(Prompt prompt) { return openAiChatModel.stream(prompt); }
}
// 由 AiModelFactoryImpl 按平台创建并缓存；同模块下另有 midjourney / suno 等图像 / 音乐模型（非 ChatModel）
```

### bpm · BpmTaskCandidateStrategy

- **目的**：把「流程审批人如何计算」抽象为一族可替换策略；16 个具体策略 + 1 个抽象基类（按角色 / 部门 / 自选 / 表达式等）
- **代码路径**：`yudao-module-bpm/src/main/java/cn/iocoder/yudao/module/bpm/framework/flowable/core/candidate/BpmTaskCandidateStrategy.java`
- **策略**：
  - BpmTaskCandidateRoleStrategy、BpmTaskCandidateDeptMemberStrategy、BpmTaskCandidateStartUserSelectStrategy、BpmTaskCandidateExpressionStrategy 等 16 个具体策略 + 1 个抽象基类

```java
public interface BpmTaskCandidateStrategy {
    BpmTaskCandidateStrategyEnum getStrategy();
    void validateParam(String param);
    default boolean isParamRequired() { return true; }
    default Set<Long> calculateUsers(String param) { throw new UnsupportedOperation("该分配方法未实现，请检查！"); }
    // calculateUsersByTask / calculateUsersByActivity 是带默认实现的扩展点
}
// 由 BpmTaskCandidateInvoker 构造时把 List<BpmTaskCandidateStrategy> 注入并按 getStrategy() 枚举建 Map，重复 key 触发 Assert 断言
```

### mall (trade) · TradePriceCalculator

- **目的**：把购物车价格计算拆成一族可排序策略；10 个具体计算器按 `@Order` 声明叠加顺序
- **代码路径**：`yudao-module-mall/yudao-module-trade/src/main/java/cn/iocoder/yudao/module/trade/service/price/calculator/TradePriceCalculator.java`
- **策略**：
  - TradeSeckillActivityPriceCalculator 秒杀、TradeDiscountActivityPriceCalculator 会员折扣、TradeRewardActivityPriceCalculator 满减送、TradeCouponPriceCalculator 优惠券、TradePointUsePriceCalculator 积分抵扣、TradeDeliveryPriceCalculator 运费、TradePointGiveCalculator 赠送积分 等 10 个

```java
public interface TradePriceCalculator {
    int ORDER_DISCOUNT_ACTIVITY = 10;
    int ORDER_REWARD_ACTIVITY = 20;
    int ORDER_COUPON = 30;
    int ORDER_POINT_USE = 40;
    int ORDER_DELIVERY = 50;
    int ORDER_POINT_GIVE = 999;
    void calculate(TradePriceCalculateReqBO param, TradePriceCalculateRespBO result);
}
// 由 TradePriceCalculatorHelper 依次链式调用；新增营销类型只需新增一个实现
```

### yudao-framework · DataPermissionRule

- **目的**：将「数据权限的 SQL 过滤条件如何生成」抽象为策略；`DeptDataPermissionRule` 基于部门 / 用户生成 dept_id / user_id 过滤表达式
- **代码路径**：`yudao-framework/yudao-spring-boot-starter-biz-data-permission/src/main/java/cn/iocoder/yudao/framework/datapermission/core/rule/DataPermissionRule.java`
- **策略**：
  - dept/DeptDataPermissionRule（基于部门 / 用户生成 dept_id、user_id 过滤表达式）

```java
public interface DataPermissionRule {
    Set<String> getTableNames();
    Expression getExpression(String tableName, Alias tableAlias);
}
// 由 DataPermissionRuleFactoryImpl 按 @DataPermission 注解选择生效规则；
// DataPermissionRuleHandler 通过 MyBatis 拦截器重写 SQL 的 WHERE 条件
```

## 变体

### 经典类策略（接口 + 实现类 + Spring 注入注册表）

- **描述**：策略接口 + 多个 `@Component` 实现 + 构造注入 List / Map 注册表；结构完整，可承载依赖注入、配置与复杂状态；Spring 业务系统事实标准形态
- **适用**：每个算法变体有独立依赖（Redis、SDK client、渠道配置）或逻辑超过几行；需要独立单测、多人协作分工实现时。本项目 bpm `BpmTaskCandidateInvoker` + `BpmTaskCandidateStrategy` 严格符合此形态；ai ChatModel 也属此形态（由 `AiModelFactoryImpl` 按平台创建并缓存）

### 函数式策略（@FunctionalInterface + lambda / 方法引用）

- **描述**：接口只有一个抽象方法时直接用 lambda 传参，或 `Map<Enum, Function>` 一行注册一行取用，省去实现类
- **适用**：策略是无状态纯函数、变体短小（1-5 行）且不太可能长出依赖；局部性、临时性的算法选择。JDK `Comparator` 即此形态

### 枚举策略（枚举常量体内实现抽象方法）

- **描述**：enum 中每个常量重写抽象方法（Baeldung《A Guide to Java Enums》§7.2 演示的 PizzaDeliveryStrategy 写法），枚举常量天然是 key，实例线程安全且天生单例，switch 穷尽性可被编译器检查
- **适用**：算法集合固定封闭、基本不会在运行时由外部新增；不需要 Spring 生命周期管理

### 工厂缓存的重量级策略（策略 + 工厂 + 实例缓存）

- **描述**：策略实例不进 Spring 容器，由工厂按 key 创建并缓存：`PayClientFactoryImpl` 用 `ConcurrentMap<Long, AbstractPayClient<?>>` 缓存，配置变更时经 `AbstractPayClient.refresh(config)` 热更新（详见 `docs/pay/pitfalls.md` 关于 refresh.equals 实现的踩坑点）
- **适用**：策略实例创建成本高（SDK 握手、连接池）、需按数据库配置动态实例化与热更新、同一 key 的实例须跨请求复用

### 可热插拔策略（Context 持有 setter，运行时整体替换）

- **描述**：经典 GoF 形态：Context 提供 `setStrategy()`，行为在运行期整体替换。JDK `ThreadPoolExecutor.setRejectedHandlerHandler()` 即此类变体；本项目 `docs/pay/pitfalls.md` 提到的「已删渠道的实例仍在进程内可解析回调」也是该形态的典型踩坑 —— 热更新不彻底导致旧实例残留
- **适用**：需按运维开关 / 全局配置切换整套行为（线程池拒绝策略、限流算法），切换点全局唯一、不随单次请求变化

### 分发型策略（Delegating：按数据自带标记路由）

- **描述**：注册表 key 不由调用方显式指定，而从数据本身解析：Spring Security `DelegatingPasswordEncoder` 从存库密码串的 `{bcrypt}` / `{noop}` 前缀解析目标编码器，`PasswordEncoderFactories.createDelegatingPasswordEncoder()` 默认编码为 bcrypt
- **适用**：处理的存量数据混有多种「算法版本」且算法标识随数据一起存储（密码串、序列化头、报文版本号），需要向前兼容旧数据

## 与相关模式辨析

### 状态模式（State）

结构同构、意图不同。refactoring.guru：State 可视为 Strategy 的扩展 —— 都靠组合委托改变行为，但 Strategy 的各实现互相独立、由外部一次选定；State 的各状态类可互相感知并主动驱动 context 切换流转。订单状态机选 State，支付渠道选择选 Strategy

### 命令模式（Command）

都可用于把动作参数化进对象，但意图不同：Command 把任意请求封装成对象以支持排队、撤销、日志、远程执行；Strategy 只描述「同一件事的不同做法」并在同一 context 内互换。需要 undo / 队列 / 审计选 Command，需要换算法选 Strategy

### 模板方法（Template Method）

refactoring.guru：模板方法基于继承、作用于类层级（编译期固定），通过子类改写算法的个别步骤；Strategy 基于组合、作用于对象层级（运行时可换），整体替换算法。骨架固定只换个别步骤用模板方法，整个算法要换用策略；二者可叠加 —— 本项目 `AbstractPayClient` 的 init / refresh 骨架是模板方法，各渠道 unifiedOrder 的差异是策略

### 工厂模式（Factory）

黄金搭档而非竞争：工厂负责「按 key 找到 / 创建策略实例」（可加缓存、热更新），策略负责「实例自身的算法」。本项目 `PayClient`（策略）+ `PayClientFactoryImpl`（工厂缓存）成对出现；用 Spring 注入 List / Map 构建注册表时，简单场景可省略手写工厂（`BpmTaskCandidateInvoker` 即省略了独立工厂类）

### 责任链（Chain of Responsibility）

责任链是「每个 handler 都有机会处理，处理不了传给下一个」（顺序尝试、可能多个都处理），策略是「按 key 精确选中一个」（互斥选择）。风控规则逐条过滤用责任链，渠道选择用策略。注意：`TradePriceCalculator` 看似责任链（Helper 依次链式调用），实则每个 calculator 是被链式调用的「独立计算步骤」，不是「试到能处理为止」—— 区别在于 calculator 之间是叠加关系而非备选关系

### Map 注册表 / switch 分支

策略的退化形态，也是它的首要替代品：分支少、变体无状态时 Map+lambda 或 switch 更直白；当变体需要依赖注入、独立状态、独立单测时才升级为完整策略结构

## 优点

- 算法可自由切换
- 避免使用多重条件判断
- 易于扩展新策略
- 符合开闭原则

## 缺点

- 客户端需要了解所有策略（通过 Map 注册表可大幅缓解：调用方只依赖策略接口）
- 策略过多时类数量增加（注册表工厂比 switch 工厂更易管理大规模清单）

## 扩展指南

### 如何新增策略

1. **创建策略实现类**：实现策略接口；若用 Map 注册表工厂还需声明自己的 key（如 `supportChannel()` / `getStrategy()`）
2. **定义配置类**：如果需要配置参数
3. **注册到工厂或上下文**：在工厂中添加创建分支（重量级策略）；或直接加 `@Component` 即可（轻量 Map 注册表）
4. **添加枚举**：如果需要类型枚举

**示例：新增短信渠道（轻量 Map 注册表工厂）**

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

- <https://refactoring.guru/design-patterns/strategy>
- <https://docs.oracle.com/javase/8/docs/api/java/time/temporal/TemporalAdjuster.html>
- <https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/core/io/ResourceLoader.html>
- <https://docs.spring.io/spring-framework/docs/3.2.2.RELEASE_to_4.0.0.M1/Spring%20Framework%204.0.0.M1/org/springframework/beans/factory/support/CglibSubclassingInstantiationStrategy.html>
- <https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html>
- <https://www.baeldung.com/java-rejectedexecutionhandler>
- <https://www.baeldung.com/java-enums>
- 本项目 `docs/pay/pitfalls.md`（`PayClientFactoryImpl.getPayClient` 返回 null 与 refresh 热更新踩坑点）
