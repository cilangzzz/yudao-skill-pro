# AI 模块常见陷阱

## 1. 模型实例未缓存导致连接泄漏

**问题**：每次调用 AI 接口都重新创建 ChatModel / ImageModel 实例，导致连接池耗尽或内存泄漏。

**正确做法**：使用 Hutool `Singleton.get()` 缓存模型实例，`AiModelFactoryImpl` 已内置此机制。不要绕过工厂直接创建模型。

```java
// 错误：直接 new
ChatModel model = new MyChatModel(apiKey, url);

// 正确：通过工厂获取（内部已缓存）
ChatModel model = modelService.getChatModel(modelId);
```

## 2. 流式接口未正确处理 SSE

**问题**：流式接口返回类型不是 `Flux`，或未设置 `produces = MediaType.TEXT_EVENT_STREAM_VALUE`，导致客户端无法接收流式数据。

**正确做法**：

```java
@PostMapping(value = "/send-stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<CommonResult<AiChatMessageSendRespVO>> sendChatMessageStream(
        @Valid @RequestBody AiChatMessageSendReqVO sendReqVO) {
    return chatMessageService.sendChatMessageStream(sendReqVO, getLoginUserId());
}
```

## 3. 知识库向量存储选型不当

**问题**：生产环境使用 `SimpleVectorStore`（内存存储），重启后向量数据丢失。

**正确做法**：
- 开发/测试：`SimpleVectorStore`
- 生产环境：`Milvus` 或 `Qdrant`
- 轻量级场景：`Redis`

## 4. 知识库分片 Token 数设置不合理

**问题**：`segment_max_tokens` 设置过大导致检索精度下降，设置过小导致上下文断裂。

**建议**：
- 一般文档：512-1024 tokens
- QA 格式文档：按问答对自然分片
- 代码文档：按函数/类分片

## 5. 对话上下文超出模型限制

**问题**：历史消息过多导致 Token 超出模型 `max_tokens` 或 `max_contexts` 限制，请求失败。

**正确做法**：在构建消息上下文时，根据 `max_contexts` 参数截取最近的 N 条消息，而非传递全部历史。

## 6. AI 调用异常未捕获

**问题**：AI 平台调用可能因网络、配额、内容审核等原因抛出异常，未捕获会导致接口直接报 500。

**正确做法**：捕获 AI 调用异常，记录到 `errorMessage` 字段，返回友好的错误信息。

## 7. Midjourney 异步任务状态未轮询

**问题**：Midjourney 图像生成是异步的，提交任务后不查询状态，用户看不到结果。

**正确做法**：通过 `task_id` 定时轮询任务状态，更新 `status`、`pic_url`、`finish_time` 等字段。

## 8. 新增平台未在工厂中注册

**问题**：在 `AiPlatformEnum` 添加了新平台枚举值，但未在 `AiModelFactoryImpl` 的 switch 分支中添加对应的构建方法，运行时抛出异常。

**正确做法**：新增平台必须同步完成以下步骤：
1. `AiPlatformEnum` 添加枚举值
2. `AiModelFactoryImpl` 添加模型创建方法
3. `YudaoAiProperties` 添加配置属性
4. `AiAutoConfiguration` 添加自动配置 Bean

## 9. 附件 URL 未做校验

**问题**：`ChatMessage.attachmentUrls` 传入无效或恶意 URL，导致模型调用失败或安全风险。

**正确做法**：对附件 URL 做格式校验和白名单过滤。

## 10. 错误码前缀冲突

**问题**：AI 模块错误码前缀为 `1-040-XXX-XXX`，新增错误码时与其他模块冲突。

**正确做法**：严格遵循 `1_040_xxx_xxx` 前缀，参考已有错误码命名：
- `1_040_000_000` - API 密钥不存在
- `1_040_001_000` - 模型不存在
- `1_040_003_000` - 对话不存在
- `1_040_004_001` - 对话生成异常
- `1_040_009_000` - 知识库不存在
