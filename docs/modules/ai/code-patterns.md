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

// 同步调用
ChatResponse response = chatModel.call(new Prompt(messages));

// 流式调用
Flux<ChatResponse> stream = chatModel.stream(new Prompt(messages));
```

**ImageModel（绘画）**：

```java
// 获取 ImageModel
ImageModel imageModel = modelService.getImageModel(modelId);

// 生成图片
ImageResponse response = imageModel.call(new ImagePrompt(prompt, options));
```

**EmbeddingModel（向量化）**：

```java
// 获取 EmbeddingModel
EmbeddingModel embeddingModel = modelService.getOrCreateVectorStore(modelId, metadataFields);

// 生成向量
EmbeddingResponse response = embeddingModel.embedForResponse(texts);
```

### 异常处理

错误码前缀为 `1-040-XXX-XXX`，典型错误码示例：

| 错误码 | 说明 |
|-------|------|
| 1_040_000_000 | API 密钥不存在 |
| 1_040_001_000 | 模型不存在 |
| 1_040_003_000 | 对话不存在 |
| 1_040_004_001 | 对话生成异常 |
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

2. 在 `AiModelFactoryImpl` 中添加模型创建方法：

```java
// 在 getOrCreateChatModel 方法的 switch 中添加
case MY_PLATFORM:
    return buildMyPlatformChatModel(apiKey, url);

// 新增构建方法
private static ChatModel buildMyPlatformChatModel(String apiKey, String url) {
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
- 向量存储选择：生产环境推荐 Milvus、Qdrant，测试可用 SimpleVectorStore
- 知识库分片：根据文档特点选择分片策略（语义分片、Markdown QA 分片）
- 多模态支持：`ChatMessage` 支持携带 `attachmentUrls` 实现多模态对话

## 模块依赖

内部依赖仅 `yudao-module-system`（通过 `AdminUserApi` 获取用户信息），与 [README](README.md) 依赖关系一节的描述一致。模块特有的外部依赖明细如下：

| 依赖 | 版本 | 用途 |
|-----|------|-----|
| spring-ai-core | 1.0.x | Spring AI 核心框架，提供统一的 AI 模型抽象 |
| spring-ai-openai | 1.0.x | OpenAI 模型集成 |
| spring-ai-anthropic | 1.0.x | Anthropic Claude 模型集成 |
| spring-ai-ollama | 1.0.x | Ollama 本地模型集成 |
| spring-ai-zhipuai | 1.0.x | 智谱 AI 模型集成 |
| spring-ai-deepseek | 1.0.x | DeepSeek 模型集成 |
| spring-ai-minimax | 1.0.x | MiniMax 模型集成 |
| spring-ai-milvus | 1.0.x | Milvus 向量数据库集成 |
| spring-ai-qdrant | 1.0.x | Qdrant 向量数据库集成 |
| spring-ai-redis | 1.0.x | Redis 向量存储集成 |
| hutool | 5.x | Singleton 缓存、工具类 |

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/model/AiModelFactory.java` | AI 模型工厂接口，定义统一的模型创建方法 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/framework/ai/core/model/AiModelFactoryImpl.java` | AI 模型工厂实现，包含各平台模型创建逻辑 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/enums/model/AiPlatformEnum.java` | AI 平台枚举，定义支持的 20+ AI 服务商 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/enums/model/AiModelTypeEnum.java` | AI 模型类型枚举 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/model/AiModelService.java` | 模型配置服务，管理 API Key、模型配置 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/chat/AiChatMessageService.java` | 聊天消息服务，核心业务逻辑 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/service/knowledge/AiKnowledgeService.java` | 知识库服务 |
| `yudao-module-ai/src/main/java/cn/iocoder/yudao/module/ai/controller/admin/chat/AiChatMessageController.java` | 聊天消息 Controller，提供 HTTP 接口 |
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

**service — 业务逻辑层**

- `chat/`: 聊天相关服务
- `image/`: 图像生成服务
- `knowledge/`: 知识库服务
- `model/`: 模型配置服务
- `music/`: 音乐生成服务
- `write/`: 写作服务
- `mindmap/`: 思维导图服务
- `workflow/`: 工作流服务

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
