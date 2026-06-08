# 聊天对话 API

> Controller: `AiChatMessageController` / `AiChatConversationController`
> 路径前缀：`/ai/chat/message` / `/ai/chat/conversation`

## 业务概述

聊天对话是 AI 模块的核心功能，支持多模型切换、流式响应（SSE）、知识库增强（RAG）、联网搜索、多模态附件等能力。

## Controller 清单

### AiChatMessageController

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 同步发送 | POST | `/ai/chat/message/send` | 同步发送消息并返回完整回复 |
| 流式发送 | POST | `/ai/chat/message/send-stream` | SSE 流式返回消息（推荐） |
| 消息列表 | GET | `/ai/chat/message/list` | 获取对话历史消息 |
| 删除消息 | DELETE | `/ai/chat/message/delete` | 删除指定消息 |

### AiChatConversationController

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建对话 | POST | `/ai/chat/conversation/create` | 创建新对话 |
| 更新对话 | PUT | `/ai/chat/conversation/update` | 更新对话信息 |
| 删除对话 | DELETE | `/ai/chat/conversation/delete` | 删除对话 |
| 获取详情 | GET | `/ai/chat/conversation/get` | 获取对话详情 |
| 分页查询 | GET | `/ai/chat/conversation/page` | 分页查询对话列表 |
| 置顶对话 | PUT | `/ai/chat/conversation/pin` | 置顶/取消置顶 |

## Service 接口

### AiChatMessageService

```java
public interface AiChatMessageService {
    // 同步发送消息
    AiChatMessageSendRespVO sendMessage(AiChatMessageSendReqVO sendReqVO, Long userId);
    // 流式发送消息
    Flux<CommonResult<AiChatMessageSendRespVO>> sendChatMessageStream(
        AiChatMessageSendReqVO sendReqVO, Long userId);
}
```

### 核心流程

1. 获取对话配置（角色、模型、温度等）
2. 构建消息上下文（历史消息 + 系统提示）
3. 如果角色绑定了知识库，执行 RAG 检索
4. 如果开启联网搜索，执行 Web Search
5. 调用 ChatModel 生成回复（同步/流式）
6. 保存用户消息和 AI 回复到数据库

## 模型调用

```java
// 获取 ChatModel（通过模型配置 ID）
ChatModel chatModel = modelService.getChatModel(modelId);

// 同步调用
ChatResponse response = chatModel.call(new Prompt(messages));

// 流式调用
Flux<ChatResponse> stream = chatModel.stream(new Prompt(messages));
```

## 数据表

- `ai_chat_conversation` - 对话表，聚合根
- `ai_chat_message` - 消息表，归属对话

## 关联配置

- `ai_chat_role` - 角色配置（系统提示词、绑定模型、知识库、工具）
- `ai_model` - 模型配置（模型标识、温度、Token 限制）
- `ai_knowledge` - 知识库（RAG 增强）

## 错误码

| 错误码 | 说明 |
|--------|------|
| `1_040_003_000` | 对话不存在 |
| `1_040_004_001` | 对话生成异常 |
