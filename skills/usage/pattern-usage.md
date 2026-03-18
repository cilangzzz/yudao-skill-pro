# 设计模式应用场景提示词指南

> 本文档提供设计模式应用的标准化提示词模板，帮助开发者快速选择和应用合适的设计模式。

---

## 目录

1. [设计模式选择指南](#1-设计模式选择指南)
2. [工厂模式应用提示词](#2-工厂模式应用提示词)
3. [策略模式应用提示词](#3-策略模式应用提示词)
4. [模板方法模式应用提示词](#4-模板方法模式应用提示词)
5. [实际案例分析](#5-实际案例分析)
6. [模式组合使用](#6-模式组合使用)

---

## 1. 设计模式选择指南

### 1.1 场景-模式映射表

| 场景描述 | 推荐模式 | 项目案例 |
|---------|---------|---------|
| 需要根据配置动态创建不同类型的客户端 | 工厂模式 + 策略模式 | 支付渠道、短信渠道、文件存储 |
| 需要统一处理流程，但具体实现不同 | 模板方法模式 | 支付下单流程、短信发送流程 |
| 需要动态切换算法或行为 | 策略模式 | AI模型切换、支付方式切换 |
| 需要隔离第三方SDK差异 | 策略模式 + 工厂模式 | 支付SDK、AI模型SDK |
| 需要支持扩展新的产品类型 | 工厂模式 | 新增支付渠道、新增存储类型 |
| 需要管理多个同类对象实例 | 工厂模式（带缓存） | PayClientFactory缓存客户端 |

### 1.2 选择决策树

```
需要解决的问题是什么？
|
+-- 创建对象
|   |
|   +-- 创建逻辑复杂，需要封装 --> 工厂模式
|   +-- 需要根据类型动态创建 --> 工厂模式
|   +-- 需要缓存和复用实例 --> 工厂模式（带缓存）
|
+-- 行为变化
|   |
|   +-- 需要动态切换算法 --> 策略模式
|   +-- 有多种可互换的实现 --> 策略模式
|   +-- 需要统一流程框架 --> 模板方法模式
|
+-- 组合场景
    |
    +-- 创建 + 行为变化 --> 工厂模式 + 策略模式
    +-- 统一流程 + 具体实现不同 --> 工厂模式 + 模板方法模式
    +-- 完整的多渠道系统 --> 工厂 + 策略 + 模板方法
```

### 1.3 模式特性对比

| 特性 | 工厂模式 | 策略模式 | 模板方法模式 |
|-----|---------|---------|-------------|
| 类型 | 创建型 | 行为型 | 行为型 |
| 主要目的 | 封装对象创建 | 封装可互换算法 | 定义算法骨架 |
| 开闭原则 | 支持 | 支持 | 支持 |
| 扩展方式 | 新增工厂方法 | 新增策略类 | 新增子类 |
| 客户端感知 | 不感知具体类 | 需选择策略 | 不感知实现细节 |
| 适用场景 | 多类型创建 | 算法切换 | 流程标准化 |

---

## 2. 工厂模式应用提示词

### 2.1 标准提示词模板

```markdown
## 任务：使用工厂模式设计 [系统名称]

### 业务背景
[描述业务场景，例如：需要支持多种支付渠道，包括微信支付、支付宝、银联等]

### 设计要求

1. 创建抽象产品接口
   - 定义 [产品名称] 接口
   - 包含以下核心方法：
     - [方法1]：[功能描述]
     - [方法2]：[功能描述]

2. 创建具体产品实现
   - 为每种类型创建实现类
   - 实现类命名规范：[类型][产品]Impl（如 AlipayPayClient）

3. 创建工厂类
   - 工厂命名：[产品]Factory（如 PayClientFactory）
   - 提供创建方法：create[产品](配置参数)
   - 考虑是否需要缓存实例

4. 注册机制
   - 使用 Map 存储类型与实现类的映射
   - 支持动态注册新类型

### 参考实现
参考项目中 PayClientFactory 的实现模式。
```

### 2.2 工厂模式提示词示例：多渠道短信系统

```markdown
## 任务：使用工厂模式设计短信客户端工厂

### 业务背景
系统需要支持多种短信渠道：阿里云短信、腾讯云短信、华为云短信、七牛云短信。
不同渠道有不同的SDK和配置，但对外需要提供统一的发送接口。

### 设计要求

#### Step 1: 创建短信客户端接口

```java
public interface SmsClient {
    Long getId();
    void init();
    SmsSendResultDTO sendSms(SmsSendMessageDTO message);
    SmsTemplateRespDTO getTemplate(String templateId);
}
```

#### Step 2: 创建配置接口

```java
public interface SmsClientConfig {
    void validate();
}
```

#### Step 3: 创建抽象基类（可选，结合模板方法）

```java
public abstract class AbstractSmsClient implements SmsClient {
    protected Long id;
    protected SmsClientConfig config;

    public AbstractSmsClient(Long id, SmsClientConfig config) {
        this.id = id;
        this.config = config;
    }

    @Override
    public final void init() {
        doInit();
    }

    protected abstract void doInit();
}
```

#### Step 4: 创建具体实现

```java
// 阿里云短信客户端
public class AliyunSmsClient extends AbstractSmsClient {
    private IAcsClient client;

    @Override
    protected void doInit() {
        AliyunSmsClientConfig config = (AliyunSmsClientConfig) this.config;
        // 初始化阿里云SDK
    }

    @Override
    public SmsSendResultDTO sendSms(SmsSendMessageDTO message) {
        // 调用阿里云API
    }
}

// 腾讯云短信客户端
public class TencentSmsClient extends AbstractSmsClient {
    // 实现类似...
}
```

#### Step 5: 创建工厂类

```java
@Component
public class SmsClientFactoryImpl implements SmsClientFactory {

    // 缓存已创建的客户端
    private final ConcurrentMap<Long, AbstractSmsClient> channelIdClients = new ConcurrentHashMap<>();

    // 类型与客户端类映射
    private static final Map<Integer, Class<? extends AbstractSmsClient>> CLIENT_CLASS_MAP = Map.of(
        SmsChannelEnum.ALIYUN.getCode(), AliyunSmsClient.class,
        SmsChannelEnum.TENCENT.getCode(), TencentSmsClient.class,
        SmsChannelEnum.HUAWEI.getCode(), HuaweiSmsClient.class,
        SmsChannelEnum.QINIU.getCode(), QiniuSmsClient.class
    );

    @Override
    public SmsClient createOrUpdateSmsClient(SmsChannelProperties properties) {
        AbstractSmsClient client = channelIdClients.get(properties.getId());
        if (client == null) {
            client = createSmsClient(properties);
            client.init();
            channelIdClients.put(client.getId(), client);
        } else {
            client.refresh(properties);
        }
        return client;
    }

    private AbstractSmsClient createSmsClient(SmsChannelProperties properties) {
        Class<? extends AbstractSmsClient> clientClass = CLIENT_CLASS_MAP.get(properties.getCode());
        return ReflectUtil.newInstance(clientClass, properties.getId(), properties.getConfig());
    }

    @Override
    public SmsClient getSmsClient(Long channelId) {
        return channelIdClients.get(channelId);
    }
}
```

### 预期产出
1. SmsClient 接口定义
2. AbstractSmsClient 抽象类
3. 4个具体实现类（Aliyun/Tencent/Huawei/Qiniu）
4. SmsClientFactory 工厂类
5. 各渠道配置类
```

### 2.3 扩展指南提示词

```markdown
## 任务：在现有工厂中新增产品类型

### 背景
需要在 [现有系统] 中新增支持 [新类型]。

### 扩展步骤

1. **创建配置类**
   - 实现 [Config接口]
   - 定义新类型特有的配置字段

2. **创建实现类**
   - 继承 [抽象基类]
   - 实现所有抽象方法

3. **注册到工厂**
   - 在枚举中添加新类型
   - 在工厂映射中添加对应关系

4. **添加测试**
   - 编写单元测试验证功能

### 遵循原则
- 开闭原则：扩展开放，修改关闭
- 新增类型不应修改已有实现类
- 只需在工厂中添加映射关系
```

---

## 3. 策略模式应用提示词

### 3.1 标准提示词模板

```markdown
## 任务：使用策略模式设计 [功能名称]

### 业务背景
[描述需要支持多种算法/行为的场景]

### 设计要求

1. 定义策略接口
   - 命名：[行为名称]Strategy 或直接作为核心接口
   - 包含所有策略共有的方法

2. 实现具体策略
   - 每种算法/行为一个实现类
   - 实现类命名：[类型][行为名称]Strategy

3. 上下文使用
   - 通过接口引用调用策略
   - 可在运行时切换策略

4. 策略选择
   - 结合工厂模式创建策略实例
   - 根据配置/参数选择策略

### 参考实现
参考项目中 PayClient 接口的多渠道实现。
```

### 3.2 策略模式提示词示例：多AI模型适配

```markdown
## 任务：使用策略模式设计AI模型适配层

### 业务背景
系统需要支持多种AI模型：OpenAI、Claude、百度文心一言、智谱AI、阿里通义千问等。
不同模型的API调用方式、参数格式不同，但对外需要提供统一的聊天、图像生成接口。

### 设计要求

#### Step 1: 定义AI模型策略接口

```java
// Spring AI 已经提供了统一接口，我们基于此进行适配
public interface AiModelFactory {

    // 获取聊天模型
    ChatModel getOrCreateChatModel(AiModelDO model);

    // 获取图像模型
    ImageModel getOrCreateImageModel(AiModelDO model);

    // 获取向量模型
    EmbeddingModel getOrCreateEmbeddingModel(AiModelDO model);
}
```

#### Step 2: 实现具体策略（各平台适配）

```java
@Service
public class AiModelFactoryImpl implements AiModelFactory {

    // 使用缓存避免重复创建
    private static final SingletonCache<ChatModel> CHAT_MODEL_CACHE = new SingletonCache<>();

    @Override
    public ChatModel getOrCreateChatModel(AiModelDO model) {
        String cacheKey = buildCacheKey(model);
        return CHAT_MODEL_CACHE.get(cacheKey, () -> doCreateChatModel(model));
    }

    private ChatModel doCreateChatModel(AiModelDO model) {
        AiPlatformEnum platform = AiPlatformEnum.valueOf(model.getPlatform());
        String apiKey = getApiKey(model.getKeyId());
        String url = model.getUrl();

        // 策略选择：根据平台类型创建不同的模型实例
        return switch (platform) {
            case OPENAI -> buildOpenAIChatModel(apiKey, url);
            case ANTHROPIC -> buildAnthropicChatModel(apiKey, url);
            case YI_YAN -> buildYiYanChatModel(apiKey, url);
            case ZHI_PU -> buildZhiPuChatModel(apiKey, url);
            case TONG_YI -> buildTongYiChatModel(apiKey, url);
            case DEEP_SEEK -> buildDeepSeekChatModel(apiKey, url);
            case OLLAMA -> buildOllamaChatModel(url);
            default -> throw new IllegalArgumentException("Unknown platform: " + platform);
        };
    }

    // 各平台具体创建方法
    private ChatModel buildOpenAIChatModel(String apiKey, String url) {
        OpenAiApi api = OpenAiApi.builder()
            .apiKey(apiKey)
            .baseUrl(url)
            .build();
        return OpenAIChatModel.builder()
            .openAiApi(api)
            .toolCallingManager(getToolCallingManager())
            .build();
    }

    private ChatModel buildZhiPuChatModel(String apiKey, String url) {
        ZhiPuApi api = new ZhiPuApi(apiKey);
        return new ZhiPuChatModel(api);
    }

    // 其他平台实现...
}
```

#### Step 3: 定义平台枚举

```java
@Getter
@AllArgsConstructor
public enum AiPlatformEnum {

    // 国际平台
    OPENAI("OpenAI", "OpenAI"),
    ANTHROPIC("Anthropic", "Anthropic Claude"),
    GEMINI("Gemini", "Google Gemini"),

    // 国内平台
    YI_YAN("YiYan", "百度文心一言"),
    ZHI_PU("ZhiPu", "智谱AI"),
    TONG_YI("TongYi", "阿里通义千问"),
    DEEP_SEEK("DeepSeek", "DeepSeek"),
    MINI_MAX("MiniMax", "MiniMax"),

    // 本地部署
    OLLAMA("Ollama", "Ollama 本地模型");

    private final String platform;
    private final String name;
}
```

#### Step 4: 服务层使用策略

```java
@Service
public class AiChatMessageServiceImpl implements AiChatMessageService {

    @Resource
    private AiModelFactory aiModelFactory;
    @Resource
    private AiModelService modelService;

    @Override
    public Flux<CommonResult<AiChatMessageSendRespVO>> sendChatMessageStream(
            AiChatMessageSendReqVO sendReqVO, Long userId) {

        // 1. 获取模型配置
        AiModelDO model = modelService.getRequiredAiModel(sendReqVO.getModelId());

        // 2. 通过工厂获取对应的策略实例（ChatModel）
        ChatModel chatModel = aiModelFactory.getOrCreateChatModel(model);

        // 3. 构建消息上下文
        List<Message> messages = buildMessages(sendReqVO);

        // 4. 调用策略（统一接口，内部实现不同）
        return chatModel.stream(new Prompt(messages))
            .map(response -> buildResponse(response));
    }
}
```

### 设计优势
1. 统一接口：所有AI平台通过ChatModel统一调用
2. 易于扩展：新增平台只需添加枚举和创建方法
3. 缓存优化：使用Singleton缓存避免重复创建连接
4. 配置驱动：通过数据库配置切换模型

### 预期产出
1. AiPlatformEnum 枚举定义
2. AiModelFactory 接口
3. AiModelFactoryImpl 实现类
4. 各平台ChatModel构建方法
```

### 3.3 策略模式扩展提示词

```markdown
## 任务：在策略模式中新增策略

### 背景
需要在现有 [策略系统] 中新增 [新策略类型]。

### 扩展步骤

1. **确认策略接口方法**
   - 查看现有接口定义
   - 确定需要实现的方法列表

2. **创建具体策略类**
   - 实现策略接口
   - 处理特定于新策略的逻辑

3. **更新工厂/上下文**
   - 在枚举中添加新类型
   - 在工厂中添加创建分支

4. **测试验证**
   - 编写单元测试
   - 验证与现有策略的兼容性

### 注意事项
- 保持接口一致性
- 处理策略特有的异常
- 考虑配置参数的差异
```

---

## 4. 模板方法模式应用提示词

### 4.1 标准提示词模板

```markdown
## 任务：使用模板方法模式设计 [流程名称]

### 业务背景
[描述需要统一流程但实现细节不同的场景]

### 设计要求

1. 创建抽象类
   - 定义模板方法（final修饰）
   - 定义抽象方法（由子类实现）
   - 可定义钩子方法（可选实现）

2. 模板方法流程
   - 步骤1：参数校验
   - 步骤2：调用子类实现
   - 步骤3：结果处理
   - 步骤4：异常处理

3. 具体实现类
   - 继承抽象类
   - 实现所有抽象方法

### 参考实现
参考项目中 AbstractPayClient 的实现模式。
```

### 4.2 模板方法模式提示词示例：支付客户端抽象

```markdown
## 任务：使用模板方法模式设计支付客户端基类

### 业务背景
系统支持多种支付渠道（微信、支付宝、钱包、模拟支付），每种渠道的下单流程相似：
参数校验 -> 调用第三方API -> 解析响应 -> 处理异常
但具体实现细节不同。

### 设计要求

#### Step 1: 创建抽象基类

```java
@Slf4j
public abstract class AbstractPayClient<Config extends PayClientConfig> implements PayClient<Config> {

    protected Long channelId;
    protected String channelCode;
    protected Config config;

    public AbstractPayClient(Long channelId, String channelCode, Config config) {
        this.channelId = channelId;
        this.channelCode = channelCode;
        this.config = config;
    }

    // ==================== 模板方法 ====================

    /**
     * 统一下单 - 模板方法
     * 定义固定的执行流程，子类不能修改
     */
    @Override
    public final PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
        // 1. 参数校验
        ValidationUtils.validate(reqDTO);

        // 2. 执行下单
        try {
            return doUnifiedOrder(reqDTO);
        } catch (Throwable ex) {
            // 3. 统一异常处理
            log.error("[unifiedOrder] 渠道[{}]下单异常", channelCode, ex);
            throw buildPayException(ex);
        }
    }

    /**
     * 统一退款 - 模板方法
     */
    @Override
    public final PayRefundRespDTO unifiedRefund(PayRefundUnifiedReqDTO reqDTO) {
        ValidationUtils.validate(reqDTO);
        try {
            return doUnifiedRefund(reqDTO);
        } catch (Throwable ex) {
            log.error("[unifiedRefund] 渠道[{}]退款异常", channelCode, ex);
            throw buildPayException(ex);
        }
    }

    // ==================== 抽象方法（子类必须实现） ====================

    /**
     * 执行下单 - 由子类实现具体调用第三方API的逻辑
     */
    protected abstract PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) throws Throwable;

    /**
     * 执行退款 - 由子类实现具体调用第三方API的逻辑
     */
    protected abstract PayRefundRespDTO doUnifiedRefund(PayRefundUnifiedReqDTO reqDTO) throws Throwable;

    /**
     * 初始化客户端 - 由子类实现SDK初始化
     */
    protected abstract void doInit();

    /**
     * 解析支付回调
     */
    protected abstract PayOrderRespDTO doParseOrderNotify(PayNotifyDataDTO notifyData) throws Throwable;

    // ==================== 钩子方法（子类可选实现） ====================

    /**
     * 刷新配置 - 默认实现，子类可覆盖
     */
    public void refresh(Config config) {
        this.config = config;
        doInit();
    }

    // ==================== 工具方法 ====================

    protected PayException buildPayException(Throwable ex) {
        if (ex instanceof PayException) {
            return (PayException) ex;
        }
        return new PayException(ex.getMessage(), ex);
    }
}
```

#### Step 2: 创建具体实现

```java
// 支付宝支付客户端
public class AlipayQrPayClient extends AbstractPayClient<AlipayPayClientConfig> {

    private AlipayClient client;

    public AlipayQrPayClient(Long channelId, AlipayPayClientConfig config) {
        super(channelId, PayChannelEnum.ALIPAY_QR.getCode(), config);
    }

    @Override
    protected void doInit() {
        AlipayPayClientConfig config = this.config;
        // 初始化支付宝SDK
        this.client = new DefaultAlipayClient(
            config.getServerUrl(),
            config.getAppId(),
            config.getPrivateKey(),
            config.getFormat(),
            config.getCharset(),
            config.getAlipayPublicKey(),
            config.getSignType()
        );
    }

    @Override
    protected PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) throws Throwable {
        // 1. 构建支付宝请求
        AlipayTradePrecreateRequest request = new AlipayTradePrecreateRequest();
        request.setBizContent(buildBizContent(reqDTO));
        request.setNotifyUrl(reqDTO.getNotifyUrl());

        // 2. 调用支付宝API
        AlipayTradePrecreateResponse response = client.execute(request);

        // 3. 解析响应
        if (response.isSuccess()) {
            return PayOrderRespDTO.builder()
                .channelOrderNo(response.getOutTradeNo())
                .qrCode(response.getQrCode())
                .build();
        } else {
            throw new PayException(response.getSubMsg());
        }
    }

    @Override
    protected PayRefundRespDTO doUnifiedRefund(PayRefundUnifiedReqDTO reqDTO) throws Throwable {
        // 实现退款逻辑...
    }

    @Override
    protected PayOrderRespDTO doParseOrderNotify(PayNotifyDataDTO notifyData) throws Throwable {
        // 解析回调...
    }
}

// 微信支付客户端
public class WxNativePayClient extends AbstractPayClient<WxPayClientConfig> {

    private WxPayService wxPayService;

    public WxNativePayClient(Long channelId, WxPayClientConfig config) {
        super(channelId, PayChannelEnum.WX_NATIVE.getCode(), config);
    }

    @Override
    protected void doInit() {
        WxPayClientConfig config = this.config;
        // 初始化微信支付SDK
        WxPayConfig wxConfig = new WxPayConfig();
        wxConfig.setAppId(config.getAppId());
        wxConfig.setMchId(config.getMchId());
        wxConfig.setPrivateKeyPath(config.getPrivateKeyPath());
        // ...

        this.wxPayService = new WxPayService();
        this.wxPayService.setConfig(wxConfig);
    }

    @Override
    protected PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) throws Throwable {
        // 使用WxJava SDK调用微信支付
        WxPayNativeOrderResult result = wxPayService.createOrder(
            buildWxOrderRequest(reqDTO)
        );
        return PayOrderRespDTO.builder()
            .qrCode(result.getCodeUrl())
            .build();
    }

    // 其他方法实现...
}
```

### 模板方法优势

1. **流程标准化**：所有渠道遵循统一的处理流程
2. **代码复用**：参数校验、异常处理等公共逻辑在基类实现
3. **易于维护**：修改公共逻辑只需修改基类
4. **扩展性强**：新增渠道只需继承基类实现抽象方法

### 预期产出
1. AbstractPayClient 抽象基类
2. 各渠道具体实现类
3. 统一的异常处理机制
```

### 4.3 模板方法扩展提示词

```markdown
## 任务：在模板方法模式中新增实现

### 背景
需要在现有 [模板类] 的基础上新增 [新实现类型]。

### 扩展步骤

1. **创建具体实现类**
   - 继承抽象基类
   - 实现所有抽象方法

2. **初始化处理**
   - 在 doInit() 中初始化第三方SDK
   - 配置必要的认证信息

3. **实现核心方法**
   - doUnifiedXxx()：调用第三方API
   - doParseXxxNotify()：解析回调数据

4. **注册到工厂**
   - 在工厂中添加创建逻辑
   - 在枚举中添加类型定义

### 代码模板

```java
public class XxxPayClient extends AbstractPayClient<XxxPayClientConfig> {

    private XxxSdkClient client;  // 第三方SDK客户端

    public XxxPayClient(Long channelId, XxxPayClientConfig config) {
        super(channelId, PayChannelEnum.XXX.getCode(), config);
    }

    @Override
    protected void doInit() {
        // 初始化SDK客户端
        this.client = new XxxSdkClient.Builder()
            .appId(config.getAppId())
            .apiKey(config.getApiKey())
            .build();
    }

    @Override
    protected PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) throws Throwable {
        // 调用第三方API
        XxxOrderRequest request = buildRequest(reqDTO);
        XxxOrderResponse response = client.createOrder(request);

        // 转换响应
        return PayOrderRespDTO.builder()
            .channelOrderNo(response.getOrderId())
            .build();
    }

    // 实现其他抽象方法...
}
```
```

---

## 5. 实际案例分析

### 5.1 案例一：多渠道支付系统

#### 业务场景
系统需要支持微信支付、支付宝、钱包支付、模拟支付等多种支付渠道，每种渠道有不同的：
- SDK接入方式
- 配置参数
- API调用方式
- 响应解析方式

#### 设计方案

**模式组合**：工厂模式 + 策略模式 + 模板方法模式

```
┌─────────────────────────────────────────────────────────────┐
│                      PayClientFactory                        │
│                    (工厂模式 - 创建客户端)                    │
│                                                              │
│  getPayClient(channelId) ──> 缓存中获取或创建客户端实例       │
└──────────────────────┬──────────────────────────────────────┘
                       │ 创建
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   AbstractPayClient                          │
│              (模板方法模式 - 统一流程骨架)                    │
│                                                              │
│  unifiedOrder() {                                            │
│      validate();      // 参数校验                            │
│      doUnifiedOrder(); // 调用子类实现                        │
│      handleException(); // 异常处理                          │
│  }                                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ 继承
          ┌────────────┼────────────┬────────────┐
          ▼            ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ AlipayClient │ │  WxPayClient │ │WalletClient  │ │ MockClient   │
│  (支付宝)    │ │   (微信)     │ │   (钱包)     │ │   (模拟)     │
│              │ │              │ │              │ │              │
│ 策略模式实现 │ │ 策略模式实现 │ │ 策略模式实现 │ │ 策略模式实现 │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

#### 关键代码

```java
// 策略接口（PayClient）- 定义统一行为
public interface PayClient<Config extends PayClientConfig> {
    Long getId();
    PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO);
    PayRefundRespDTO unifiedRefund(PayRefundUnifiedReqDTO reqDTO);
    PayTransferRespDTO unifiedTransfer(PayTransferUnifiedReqDTO reqDTO);
}

// 模板方法（AbstractPayClient）- 定义流程骨架
public abstract class AbstractPayClient<Config extends PayClientConfig> implements PayClient<Config> {
    @Override
    public final PayOrderRespDTO unifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
        ValidationUtils.validate(reqDTO);
        try {
            return doUnifiedOrder(reqDTO);  // 子类实现
        } catch (Throwable ex) {
            throw buildPayException(ex);
        }
    }
    protected abstract PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) throws Throwable;
}

// 工厂（PayClientFactory）- 创建和管理客户端
@Component
public class PayClientFactoryImpl implements PayClientFactory {
    private final ConcurrentMap<Long, PayClient<?>> clients = new ConcurrentHashMap<>();

    private static final Map<String, Class<? extends PayClient>> CLIENT_CLASS_MAP = Map.of(
        "wx_pub", WxPubPayClient.class,
        "wx_native", WxNativePayClient.class,
        "alipay_wap", AlipayWapPayClient.class,
        "alipay_qr", AlipayQrPayClient.class,
        "wallet", WalletPayClient.class,
        "mock", MockPayClient.class
    );

    @Override
    public PayClient getPayClient(Long channelId) {
        return clients.computeIfAbsent(channelId, this::createPayClient);
    }
}
```

#### 扩展指南：新增银联支付

```markdown
## 任务：新增银联支付渠道

### 步骤

1. **创建配置类**
```java
@Data
public class UnionPayClientConfig implements PayClientConfig {
    private String merchantId;      // 商户号
    private String apiKey;          // API密钥
    private String certPath;        // 证书路径
    private String certPassword;    // 证书密码
}
```

2. **创建客户端类**
```java
public class UnionPayQrPayClient extends AbstractPayClient<UnionPayClientConfig> {
    @Override
    protected void doInit() {
        // 初始化银联SDK
    }
    @Override
    protected PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) throws Throwable {
        // 调用银联下单API
    }
    // 实现其他方法...
}
```

3. **注册到工厂**
```java
CLIENT_CLASS_MAP.put("union_pay_qr", UnionPayQrPayClient.class);
```

4. **添加枚举**
```java
UNION_PAY_QR("union_pay_qr", "银联扫码支付");
```
```

---

### 5.2 案例二：多存储类型文件系统

#### 业务场景
系统需要支持多种文件存储方式：本地存储、S3（MinIO/OSS/COS）、FTP、SFTP、数据库存储。不同存储方式的：
- 配置参数不同
- 上传/下载/删除实现不同
- 访问URL生成方式不同

#### 设计方案

**模式组合**：策略模式 + 工厂模式 + 模板方法模式

```
┌─────────────────────────────────────────────────────────────┐
│                    FileClientFactory                         │
│                    (工厂模式 - 创建客户端)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   AbstractFileClient                         │
│              (模板方法模式 - 统一流程)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┬────────────┬───────────┐
          ▼            ▼            ▼            ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ ┌─────────────┐
│LocalFileClient│ │ S3FileClient │ │FtpFileClient│ │SftpFileClient│ │DBFileClient │
│   (本地)     │ │  (S3/OSS)    │ │    (FTP)    │ │    (SFTP)   │ │  (数据库)   │
└──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ └─────────────┘
```

#### 关键代码

```java
// 策略接口
public interface FileClient {
    Long getId();
    void upload(byte[] content, String path, String type);
    byte[] getContent(String path);
    void delete(String path);
    String getPresignedUrl(String path, int timeout);
}

// 模板方法
public abstract class AbstractFileClient<Config extends FileClientConfig> implements FileClient {
    protected Long id;
    protected Config config;

    public AbstractFileClient(Long id, Config config) {
        this.id = id;
        this.config = config;
    }

    public final void init() {
        doInit();
    }

    protected abstract void doInit();
}

// 枚举定义类型与类映射
@Getter
@AllArgsConstructor
public enum FileStorageEnum {
    LOCAL(10, LocalFileClientConfig.class, LocalFileClient.class),
    S3(20, S3FileClientConfig.class, S3FileClient.class),
    FTP(30, FtpFileClientConfig.class, FtpFileClient.class),
    SFTP(40, SftpFileClientConfig.class, SftpFileClient.class),
    DATABASE(50, NoneFileClientConfig.class, DBFileClient.class);

    private final Integer storage;
    private final Class<? extends FileClientConfig> configClass;
    private final Class<? extends FileClient> clientClass;
}
```

---

### 5.3 案例三：多AI模型适配

#### 业务场景
系统需要支持多种AI平台：OpenAI、Claude、文心一言、智谱AI、通义千问、DeepSeek、Ollama本地部署等。不同平台：
- API格式不同
- 认证方式不同
- 响应结构不同

#### 设计方案

**模式组合**：工厂模式 + 策略模式

```
┌─────────────────────────────────────────────────────────────┐
│                    AiModelFactory                            │
│                 (工厂模式 - 创建模型实例)                     │
│                                                              │
│  getOrCreateChatModel(model) -> 缓存获取或创建               │
└──────────────────────┬──────────────────────────────────────┘
                       │ switch by platform
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      ChatModel                               │
│              (Spring AI 统一接口 - 策略模式)                  │
│                                                              │
│  call(Prompt) -> ChatResponse                               │
│  stream(Prompt) -> Flux<ChatResponse>                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ 实现
     ┌─────────────────┼─────────────────┬─────────────────┐
     ▼                 ▼                 ▼                 ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│OpenAIChat   │ │ZhiPuChat    │ │DeepSeekChat │ │OllamaChat   │
│   Model     │ │   Model     │ │   Model     │ │   Model     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### 关键代码

```java
// 工厂实现
@Service
public class AiModelFactoryImpl implements AiModelFactory {

    @Override
    public ChatModel getOrCreateChatModel(AiModelDO model) {
        String cacheKey = buildCacheKey(model);
        return Singleton.get(cacheKey, () -> doCreateChatModel(model));
    }

    private ChatModel doCreateChatModel(AiModelDO model) {
        AiPlatformEnum platform = AiPlatformEnum.valueOf(model.getPlatform());

        return switch (platform) {
            case OPENAI -> buildOpenAIChatModel(model);
            case ANTHROPIC -> buildAnthropicChatModel(model);
            case ZHI_PU -> buildZhiPuChatModel(model);
            case DEEP_SEEK -> buildDeepSeekChatModel(model);
            case OLLAMA -> buildOllamaChatModel(model);
            // ... 其他平台
        };
    }
}
```

---

## 6. 模式组合使用

### 6.1 三种模式的协作关系

```
┌────────────────────────────────────────────────────────────────┐
│                        业务场景                                 │
│              "需要支持多种XXX，统一调用方式"                     │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      工厂模式                                   │
│                                                                 │
│  职责：创建具体实例                                              │
│  - 根据类型/配置创建对应的实现类实例                              │
│  - 缓存已创建的实例                                              │
│  - 支持配置热刷新                                                │
│                                                                 │
│  产出：Product 接口的实现类实例                                   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      策略模式                                   │
│                                                                 │
│  职责：定义统一行为接口                                          │
│  - 定义所有实现类共有的方法                                      │
│  - 不同实现类提供不同的算法/行为                                  │
│  - 运行时可切换                                                  │
│                                                                 │
│  产出：Product 接口定义                                          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    模板方法模式                                 │
│                                                                 │
│  职责：定义统一流程骨架                                          │
│  - 定义模板方法（final）控制执行流程                              │
│  - 定义抽象方法由子类实现                                        │
│  - 复用公共逻辑（校验、异常处理、日志）                           │
│                                                                 │
│  产出：AbstractProduct 抽象类                                    │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 组合使用提示词模板

```markdown
## 任务：使用设计模式组合设计 [系统名称]

### 业务场景
[描述业务需求，强调多类型支持、统一调用、流程标准化]

### 设计要求

#### 1. 策略层设计（定义行为）

**创建策略接口**
```java
public interface [Product] {
    // 核心业务方法
    Result doSomething(Request request);
}
```

#### 2. 模板层设计（定义流程）

**创建抽象基类**
```java
public abstract class Abstract[Product] implements [Product] {
    // 模板方法
    @Override
    public final Result doSomething(Request request) {
        // 1. 参数校验
        validate(request);
        // 2. 执行业务
        try {
            return doDoSomething(request);
        } catch (Exception e) {
            // 3. 异常处理
            return handleException(e);
        }
    }

    // 抽象方法
    protected abstract Result doDoSomething(Request request);
    protected abstract void doInit();
}
```

#### 3. 工厂层设计（创建实例）

**创建工厂接口和实现**
```java
public interface [Product]Factory {
    [Product] get[Product](Long id);
    [Product] create[Product](Config config);
}

@Component
public class [Product]FactoryImpl implements [Product]Factory {
    private final ConcurrentMap<Long, [Product]> cache = new ConcurrentHashMap<>();

    @Override
    public [Product] get[Product](Long id) {
        return cache.computeIfAbsent(id, this::create[Product]);
    }
}
```

#### 4. 具体实现

**为每种类型创建实现类**
```java
public class [Type][Product] extends Abstract[Product] {
    @Override
    protected void doInit() {
        // 初始化特定类型
    }

    @Override
    protected Result doDoSomething(Request request) {
        // 实现特定逻辑
    }
}
```

### 预期产出
1. [Product] 接口定义
2. Abstract[Product] 抽象类
3. [Product]Factory 工厂类
4. 多个具体实现类
5. 类型枚举定义
```

### 6.3 扩展新类型的标准流程

```markdown
## 任务：在组合模式系统中扩展新类型

### 扩展流程图

```
┌─────────────────┐
│ 1. 创建配置类    │  实现 Config 接口，定义新类型配置字段
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 创建实现类    │  继承抽象基类，实现所有抽象方法
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 添加枚举值    │  在类型枚举中添加新类型定义
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 注册到工厂    │  在工厂的映射Map中添加类型-类关系
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 编写测试      │  验证新类型功能正确性
└─────────────────┘
```

### 扩展代码模板

```java
// Step 1: 配置类
@Data
public class [NewType]Config implements Config {
    private String field1;
    private String field2;
    // ...
}

// Step 2: 实现类
public class [NewType][Product] extends Abstract[Product]<[NewType]Config> {

    public [NewType][Product](Long id, [NewType]Config config) {
        super(id, config);
    }

    @Override
    protected void doInit() {
        // 初始化逻辑
    }

    @Override
    protected Result doDoSomething(Request request) {
        // 业务逻辑
    }
}

// Step 3: 枚举
[NEW_TYPE](100, "[NewType]", "新类型描述");

// Step 4: 工厂注册
CLIENT_MAP.put(TypeEnum.NEW_TYPE, [NewType][Product].class);

// Step 5: 测试
@Test
void test[NewType]() {
    // ...
}
```
```

---

## 附录：项目中的设计模式文件索引

### 工厂模式实现位置

| 模块 | 工厂类 | 路径 |
|-----|-------|------|
| pay | PayClientFactoryImpl | yudao-module-pay/.../pay/core/client/impl/PayClientFactoryImpl.java |
| infra | FileClientFactory | yudao-module-infra/.../file/core/client/FileClientFactory.java |
| ai | AiModelFactoryImpl | yudao-module-ai/.../framework/ai/core/model/AiModelFactoryImpl.java |

### 策略模式实现位置

| 模块 | 策略接口 | 实现类 |
|-----|---------|--------|
| pay | PayClient | AlipayPayClient, WxPayClient, WalletPayClient, MockPayClient |
| infra | FileClient | LocalFileClient, S3FileClient, FtpFileClient, DBFileClient |
| ai | ChatModel (Spring AI) | OpenAIChatModel, ZhiPuChatModel, DeepSeekChatModel |

### 模板方法模式实现位置

| 模块 | 抽象类 | 路径 |
|-----|-------|------|
| pay | AbstractPayClient | yudao-module-pay/.../pay/core/client/impl/AbstractPayClient.java |
| infra | AbstractFileClient | yudao-module-infra/.../file/core/client/AbstractFileClient.java |

---

> 文档版本：1.0.0
> 更新日期：2026-03-18
> 维护者：Technical Writer Agent