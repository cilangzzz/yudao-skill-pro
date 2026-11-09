# AI 大模型代码模式与扩展指南 (ai)

> 本文档移植自模块 Skill 知识库（skill-ai.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

- 注解组合：`@Tag(name = "管理后台 - XXX")`、`@RestController`、`@RequestMapping("/ai/xxx")`、`@Operation(summary = "xxx")`
- 流式接口：`produces = MediaType.TEXT_EVENT_STREAM_VALUE`，返回 `Flux<CommonResult<T>>`
- 通过 `getLoginUserId()` 获取当前登录用户并传入 Service，Controller 不持有业务状态

```java
@Tag(name = "管理后台 - 聊天消息")
@RestController
@RequestMapping("/ai/chat/message")
public class AiChatMessageController {

    @Resource
    private AiChatMessageService chatMessageService;

    @Operation(summary = "发送消息（流式）")
    @PostMapping(value = "/send-stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<CommonResult<AiChatMessageSendRespVO>> sendChatMessageStream(
            @Valid @RequestBody AiChatMessageSendReqVO sendReqVO) {
        return chatMessageService.sendChatMessageStream(sendReqVO, getLoginUserId());
    }
}
```

### Service 层规范

- 接口模式：定义接口 + Impl 实现类，接口用于解耦
- 实现模式：`@Service` 注解，使用 `@Resource` 注入依赖
- 流式生成的标准流程：获取对话与模型配置 → 构建消息上下文 → 调用 ChatModel 流式生成 → 保存消息记录

```java
public interface AiChatMessageService {
    // 同步发送消息
    AiChatMessageSendRespVO sendMessage(AiChatMessageSendReqVO sendReqVO, Long userId);
    // 流式发送消息
    Flux<CommonResult<AiChatMessageSendRespVO>> sendChatMessageStream(
        AiChatMessageSendReqVO sendReqVO, Long userId);
}

@Service
public class AiChatMessageServiceImpl implements AiChatMessageService {
    @Resource
    private AiModelService modelService;

    @Override
    public Flux<CommonResult<AiChatMessageSendRespVO>> sendChatMessageStream(
            AiChatMessageSendReqVO sendReqVO, Long userId) {
        // 1. 获取对话和模型配置
        // 2. 构建消息上下文
        // 3. 调用 ChatModel 流式生成
        // 4. 保存消息记录
    }
}
```

### 数据访问层（DAL）规范

- Mapper 继承 `BaseMapperX`，使用 `LambdaQueryWrapper` 构建查询
- 通用查询封装为接口上的 `default` 方法，供 Service 复用

```java
@Mapper
public interface AiChatMessageMapper extends BaseMapperX<AiChatMessageDO> {

    default List<AiChatMessageDO> selectListByConversationId(Long conversationId) {
        return selectList(new LambdaQueryWrapper<AiChatMessageDO>()
                .eq(AiChatMessageDO::getConversationId, conversationId)
                .orderByAsc(AiChatMessageDO::getId));
    }
}
```

### AI 模型调用规范

业务层统一通过 `AiModelService` 获取 Spring AI 模型实例，不直接依赖具体平台 SDK。

**ChatModel（对话）**：

```java
// 获取 ChatModel
ChatModel chatModel = modelService.getChatModel(modelId);

// 获取 ChatModel（带思考档位参数）
ChatModel chatModel = modelService.getChatModel(modelId, reasoningOptions);

// 同步调用
ChatResponse response = chatModel.call(new Prompt(messages));

// 流式调用
Flux<ChatResponse> stream = chatModel.stream(new Prompt(messages));
```

**思考（Reasoning）档位**：

模型的思考档位保存在 `ai_model.reasoning_config`（`AiModelDO.ReasoningConfig`：档位列表 + 默认档位）。发送消息时按「平台一致 → 生效档位 → 平台路由 → 参数深拷贝」的顺序解析（见 `AiChatMessageServiceImpl#resolveReasoningOptions`）：

```java
// 1. 解析本次生效的档位与思考参数
//    注意：模型未配置思考时，只有「请求显式带了档位」才会抛 MODEL_REASONING_NOT_CONFIGURED；
//          未带档位时不报错，直接返回 null（保持平台原有行为）
Map<String, Object> reasoningOptions = AiReasoningUtils.getReasoningOptions(
        model, AiReasoningUtils.resolveReasoningLevel(model, sendReqVO.getReasoningLevel()));

// 2. 带着思考参数取客户端（不同档位对应不同客户端实例，缓存键含思考参数哈希）
ChatModel chatModel = modelService.getChatModel(model.getId(), reasoningOptions);
```

思考参数的落地方式由平台决定（`AiReasoningUtils.ReasoningRoute`）：HTTP 路由复用 DeepSeek 客户端，通过 `AiRequestBodyPatcher` 在 HTTP 层做 RFC 7396 合并补丁；OPENAI 路由 `reasoning_effort` 写强类型字段、其余键进 `extraBody`；TONG_YI 路由映射到 `enable_thinking` / `thinking_budget`。

**Token 用量与请求日志**：

```java
// 1. 生成请求编号（本地 UUID，非厂商返回 id）
String requestId = IdUtil.fastUUID();
// 2. 构建请求日志快照（bizType / bizId / 平台 / 模型 / 租户快照）
AiRequestLogCreateReqDTO requestLog = requestLogService.buildCreateReqDTO(
        requestId, userId, AiRequestLogBizTypeEnum.CHAT, bizId, model);
// 3. 流式过程中用 chunk 更新用量快照（取最新整份快照，不累加）
requestLogService.setCreateReqDTO(requestLog, chunk);
// 4. 结束时记录日志（独立事务，主事务回滚也不丢）
requestLogService.createRequestLog(requestLog);
```

Token 用量由 `AiUsageUtils` 从厂商返回的 usage 中提取，未知为 null（不做估算），`totalTokens` 仅在 input、output 都已知时才有值。

**ImageModel（绘画）**：

```java
// 获取 ImageModel
ImageModel imageModel = modelService.getImageModel(modelId);

// 生成图片
ImageResponse response = imageModel.call(new ImagePrompt(prompt, options));
```

**EmbeddingModel（向量化）与 VectorStore（向量库）**：

```java
// 获取向量库（当前默认 SimpleVectorStore；切换 Qdrant / Redis / Milvus 需改 AiModelServiceImpl#getOrCreateVectorStore）
// 返回类型是 VectorStore，不是 EmbeddingModel
VectorStore vectorStore = modelService.getOrCreateVectorStore(modelId, metadataFields);

// 写入文档（知识库段落向量化），向量 id 由 VectorStore 生成并回写 ai_knowledge_segment.vector_id
vectorStore.add(List.of(document));
```

### 异常处理

错误码前缀为 `1-040-XXX-XXX`，典型错误码示例：

| 错误码 | 说明 |
|-------|------|
| 1_040_000_000 | API 密钥不存在 |
| 1_040_001_000 | 模型不存在 |
| 1_040_001_004 | 该模型未配置思考档位 |
| 1_040_001_005 | 该模型不支持思考档位 |
| 1_040_001_006 | 平台暂不支持思考配置 |
| 1_040_001_007 | 模型平台与 API 密钥平台不一致，无法使用思考配置 |
| 1_040_001_009 | 思考配置不正确 |
| 1_040_003_000 | 对话不存在 |
| 1_040_004_001 | 对话生成异常 |
| 1_040_004_002 | 读取图片附件失败 |
| 1_040_006_000 | 音乐不存在 |
| 1_040_009_000 | 知识库不存在 |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`CommonResult.error(ErrorCode)`

## 扩展指南

### 新增 AI 平台提供商

1. 在 `AiPlatformEnum` 中添加新平台枚举值：

```java
MY_PLATFORM("MyPlatform", "我的平台"),
```

2. 在 `AiModelFactoryImpl` 中添加模型创建方法（`AiModelFactory#getOrCreateChatModel` 现为四参：`platform`、`apiKey`、`url`、`reasoningOptions`）：

```java
// 在 getOrCreateChatModel 方法的 switch 中添加（思考参数按平台路由处理，见下方说明）
case MY_PLATFORM:
    return buildMyPlatformChatModel(apiKey, url, reasoningOptions);

// 新增构建方法
private static ChatModel buildMyPlatformChatModel(String apiKey, String url,
                                                  Map<String, Object> reasoningOptions) {
    // 参考 Spring AI 对应平台的 AutoConfiguration 实现
    MyPlatformApi api = MyPlatformApi.builder()
        .apiKey(apiKey)
        .baseUrl(url)
        .build();
    return MyPlatformChatModel.builder()
        .myPlatformApi(api)
        .toolCallingManager(getToolCallingManager())
        .build();
}

// 若平台需要支持思考档位：先在 AiReasoningUtils#getReasoningRoute 归属路由；
// HTTP 路由用 AiRequestBodyPatcher.configure(builder, patcher) 给 DeepSeekApi.Builder 装上补丁，
// 缓存键需带上 reasoningOptions 的规范化哈希（AiReasoningUtils#hashReasoningOptions）
```

3. 如需自定义模型类，在 `framework/ai/core/model/` 下创建：

```java
// 参考 BaiChuanChatModel、GeminiChatModel 等
```

4. 在 `YudaoAiProperties` 中添加平台配置属性：

```java
@Data
public static class MyPlatform {
    private String apiKey;
    private String baseUrl;
}
```

5. 在 `AiAutoConfiguration` 中添加自动配置：

```java
@Bean
@ConditionalOnProperty(prefix = "yudao.ai.my-platform", name = "api-key")
public ChatModel myPlatformChatModel(YudaoAiProperties properties) {
    return buildMyPlatformChatModel(properties.getMyPlatform());
}
```

### 新增 AI 能力类型

1. 在 `AiModelTypeEnum` 中添加新类型：

```java
MY_CAPABILITY(7, "新能力"),
```

2. 创建对应的 DO 实体类：

```java
@TableName("ai_my_capability")
@Data
public class AiMyCapabilityDO extends BaseDO {
    private Long id;
    private Long userId;
    private String prompt;
    private String result;
    // ...
}
```

3. 创建 Controller、Service、Mapper：

```java
// Controller
@Tag(name = "管理后台 - 新能力")
@RestController
@RequestMapping("/ai/my-capability")
public class AiMyCapabilityController { ... }

// Service
public interface AiMyCapabilityService { ... }

// Mapper
public interface AiMyCapabilityMapper extends BaseMapperX<AiMyCapabilityDO> { ... }
```

4. 在 `AiModelFactory` 中添加对应的模型获取方法：

```java
MyCapabilityModel getOrCreateMyCapabilityModel(AiPlatformEnum platform,
    String apiKey, String url);
```

### 最佳实践

- 模型实例缓存：使用 `Singleton.get()` 缓存，避免重复创建连接
- 流式响应优先：聊天推荐使用流式接口，用户体验更好
- 错误处理：捕获 AI 调用异常，记录 `errorMessage` 字段
- 向量存储选择：当前 `AiModelServiceImpl#getOrCreateVectorStore` 硬编码 `SimpleVectorStore`（本地文件持久化），Qdrant / Redis / Milvus 的构建方法已存在但被注释；生产环境需放开注释切换，并在 `application.yaml` 配置对应连接
- 知识库分片：根据文档特点选择分片策略（语义分片、Markdown QA 分片）
- 多模态支持：模型 `input_modalities` 包含 `image` 时，图片附件以 `Media`（`ByteArrayResource`）与文本放入同一条 `UserMessage`；为空（历史数据）视为仅 text，图片退化为 Base64 文本。详见 [pitfalls 第 8 节](pitfalls.md)
- 平台默认模型：各平台 `XxxChatModel.MODEL_DEFAULT` 是内置默认模型标识（当前 MiniMax=`MiniMax-M3.1-Flash`、月之暗面=`kimi-k3.1-pro`、智谱=`glm-5.3-flash`、小米 MiMo=`mimo-v2.6-flash`），`application.yaml` 中的示例值可能滞后，以代码常量为准
- 复用客户端的新平台：小米 MiMo 直接复用 DeepSeek 客户端（OpenAI 兼容协议，`https://api.xiaomimimo.com/v1/chat/completions`），Bean 受 `yudao.ai.mimo.enable` 开关控制，默认关闭；新增同类平台可参考 `MiMoChatModel` 的写法

## 模块依赖

内部依赖仅 `yudao-module-system`（通过 `AdminUserApi` 获取用户信息），与 [README](README.md) 依赖关系一节的描述一致。模块特有的外部依赖明细如下：

| 依赖 | 版本 | 用途 |
|-----|------|-----|
| spring-ai-bom | 1.1.8 | Spring AI 依赖版本统一管理（BOM） |
| spring-ai-starter-model-openai | 1.1.8 | OpenAI 模型集成（多个平台复用其 OpenAI 兼容协议） |
| spring-ai-starter-model-azure-openai | 1.1.8 | Azure OpenAI 模型集成 |
| spring-ai-starter-model-anthropic | 1.1.8 | Anthropic Claude 模型集成 |
| spring-ai-starter-model-deepseek | 1.1.8 | DeepSeek 模型集成（HTTP 思考路由复用该客户端） |
| spring-ai-starter-model-ollama | 1.1.8 | Ollama 本地模型集成 |
| spring-ai-starter-model-stability-ai | 1.1.8 | StableDiffusion 绘画模型集成 |
| spring-ai-alibaba-starter-dashscope | 1.1.2.2 | 通义千问（DASHSCOPE）模型集成，并提供 Rerank 模型 |
| spring-ai-starter-vector-store-qdrant | 1.1.8 | Qdrant 向量数据库集成（构建代码存在，当前默认未启用） |
| spring-ai-starter-vector-store-redis | 1.1.8 | Redis 向量存储集成（构建代码存在，当前默认未启用） |
| spring-ai-starter-vector-store-milvus | 1.1.8 | Milvus 向量数据库集成（构建代码存在，当前默认未启用） |
| spring-ai-tika-document-reader | 1.1.8 | Tika 文档解析（知识库文档下载解析） |
| spring-ai-starter-mcp-server-webmvc | 1.1.8 | MCP Server（仅支持 WebMVC，WebFlux 版会导致 SSE 失效） |
| spring-ai-starter-mcp-client | 1.1.8 | MCP Client（连接外部 MCP Server） |
| tinyflow-java-core | 1.2.6 | TinyFlow 工作流引擎（AI 工作流执行） |

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/model/AiModelFactory.java` | AI 模型工厂接口，定义统一的模型创建方法 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/model/AiModelFactoryImpl.java` | AI 模型工厂实现，包含各平台模型创建逻辑 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/enums/model/AiPlatformEnum.java` | AI 平台枚举，定义支持的 22 个 AI 服务商 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/enums/model/AiModelTypeEnum.java` | AI 模型类型枚举 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/enums/model/AiModelInputModalityEnum.java` | 模型输入模态枚举（text / image / video） |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/util/AiReasoningUtils.java` | 思考档位工具：平台路由、保存校验、档位解析、参数规范化与哈希 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/util/AiUsageUtils.java` | Token 用量提取与响应元数据快照 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/util/AiChatUtils.java` | 聊天工具类（原 `AiUtils`）：构建 ChatOptions、解析响应内容 / 推理内容、多模态判断 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/reasoning/AiRequestBodyPatcher.java` | 思考参数 HTTP 层请求体改写（RFC 7396 JSON Merge Patch） |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/model/AiModelService.java` | 模型配置服务，管理 API Key、模型配置 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/requestlog/AiRequestLogService.java` | AI 请求日志服务（独立事务写入、用量统计） |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/chat/AiChatMessageService.java` | 聊天消息服务，核心业务逻辑 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/knowledge/AiKnowledgeService.java` | 知识库服务 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/controller/admin/chat/AiChatMessageController.java` | 聊天消息 Controller，提供 HTTP 接口 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/controller/admin/requestlog/AiRequestLogController.java` | AI 请求日志 Controller（查询 / 分页 / 统计） |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/config/AiAutoConfiguration.java` | AI 自动配置类 |

## 领域模型

### 聚合根

| 聚合根 | 包含实体 | 说明 |
|-------|---------|------|
| 聊天会话 | `AiChatMessageDO` | 用户发起的对话，包含多条消息 |
| 知识库 | `AiKnowledgeDocumentDO`、`AiKnowledgeSegmentDO` | 知识库包含多个文档，文档包含多个分段 |
| AI 模型配置 | `AiApiKeyDO` | 模型配置关联 API 密钥 |

### 值对象

| 值对象 | 说明 |
|-------|------|
| `AiPlatformEnum` | AI 平台枚举，定义支持的 AI 服务商 |
| `AiModelTypeEnum` | 模型类型枚举：对话、图像、语音、视频、向量、重排序 |

## 设计与架构补充

以下内容为 [README](README.md) 已有描述之外的架构细节。

### 分层架构

模块内部按四层组织，Service 层接口按领域划分（chat/image/knowledge/model/music/write/mindmap/workflow），职责单一：

**controller — HTTP 接口层**

- `AiChatMessageController`: 聊天消息接口
- `AiChatConversationController`: 对话管理接口
- `AiImageController`: 图像生成接口
- `AiKnowledgeController`: 知识库管理接口
- `AiModelController`: 模型配置接口
- `AiMusicController`: 音乐生成接口
- `AiWriteController`: 写作助手接口
- `AiMindMapController`: 思维导图接口
- `AiWorkflowController`: 工作流接口
- `AiRequestLogController`: AI 请求日志接口（查询 / 分页 / 统计）

**service — 业务逻辑层**

- `chat/`: 聊天相关服务
- `image/`: 图像生成服务
- `knowledge/`: 知识库服务
- `model/`: 模型配置服务
- `music/`: 音乐生成服务
- `write/`: 写作服务
- `mindmap/`: 思维导图服务
- `workflow/`: 工作流服务
- `requestlog/`: AI 请求日志服务（Token 用量统计、请求链路追踪）

**dal — 数据访问层**

- `dataobject/`: DO 实体类
- `mysql/`: MyBatis Mapper 接口

**framework/ai — AI 框架集成层**

- `core/model/`: 模型工厂和多平台适配
- `core/webserch/`: 联网搜索客户端
- `config/`: 自动配置类

### 补充设计模式

README「设计模式」一节已覆盖工厂模式与策略模式，此处补充：

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 模板方法 | `service/chat/AiChatMessageServiceImpl.java` | 聊天消息处理的统一流程（获取配置 → 构建上下文 → 模型生成 → 落库） |

### 表关系（ER）

| 主表 | 关系 | 从表 | 外键 |
|-----|------|-----|------|
| ai_chat_conversation | 1:N | ai_chat_message | conversation_id |
| ai_knowledge | 1:N | ai_knowledge_document | knowledge_id |
| ai_knowledge_document | 1:N | ai_knowledge_segment | document_id |
| ai_model | N:1 | ai_api_key | key_id |
| ai_chat_role | N:1 | ai_model | model_id |
