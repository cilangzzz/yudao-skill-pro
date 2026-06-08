# 模型配置 API

> Controller: `AiModelController` / (`AiApiKeyController`)
> 路径前缀：`/ai/model` / `/ai/api-key`

## 业务概述

模型配置管理 AI 平台的 API 密钥和模型参数。是所有 AI 能力的基础设施层，聊天、图像、知识库等功能都依赖此处配置的模型。

## 架构关系

```
AiApiKeyDO (API 密钥)
  └── AiModelDO (模型配置) N:1 via key_id
        └── AiChatRoleDO (聊天角色) N:1 via model_id
```

## Controller 接口

### AiModelController（/ai/model）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建模型 | POST | `/ai/model/create` | 创建模型配置 |
| 更新模型 | PUT | `/ai/model/update` | 更新模型配置 |
| 删除模型 | DELETE | `/ai/model/delete` | 删除模型配置 |
| 获取详情 | GET | `/ai/model/get` | 获取模型详情 |
| 分页查询 | GET | `/ai/model/page` | 分页查询模型列表 |

### API 密钥管理（/ai/api-key）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建密钥 | POST | `/ai/api-key/create` | 创建 API 密钥 |
| 更新密钥 | PUT | `/ai/api-key/update` | 更新 API 密钥 |
| 删除密钥 | DELETE | `/ai/api-key/delete` | 删除 API 密钥 |
| 获取详情 | GET | `/ai/api-key/get` | 获取密钥详情 |
| 分页查询 | GET | `/ai/api-key/page` | 分页查询密钥列表 |

## Service 接口

### AiModelService

```java
public interface AiModelService {
    // 获取 ChatModel 实例
    ChatModel getChatModel(Long modelId);
    // 获取 ImageModel 实例
    ImageModel getImageModel(Long modelId);
    // 获取 EmbeddingModel / VectorStore
    VectorStore getOrCreateVectorStore(Long modelId, List<String> metadataFields);
}
```

## 模型工厂

```java
// 工厂接口
public interface AiModelFactory {
    ChatModel getOrCreateChatModel(AiPlatformEnum platform, String apiKey, String url);
    ImageModel getOrCreateImageModel(AiPlatformEnum platform, String apiKey, String url);
    EmbeddingModel getOrCreateEmbeddingModel(AiPlatformEnum platform, String apiKey, String url);
}
```

创建策略：根据 `AiPlatformEnum` 枚举值分发到不同的构建方法，使用 Hutool `Singleton.get()` 缓存实例。

## 数据表

### ai_api_key

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| name | String | 名称 |
| api_key | String | 密钥 |
| platform | String | 平台（AiPlatformEnum） |
| url | String | API 地址 |
| status | Integer | 状态 |

### ai_model

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| key_id | Long | API 密钥编号 |
| name | String | 模型名称 |
| model | String | 模型标识 |
| platform | String | 平台 |
| type | Integer | 类型：1对话 2图片 3语音 4视频 5向量 6重排序 |
| sort | Integer | 排序值 |
| status | Integer | 状态 |
| temperature | Double | 温度参数 |
| max_tokens | Integer | 最大 Token 数 |
| max_contexts | Integer | 最大上下文数 |

## 支持平台

通过 `AiPlatformEnum` 枚举定义，支持 20+ AI 服务商，包括但不限于：OpenAI、Anthropic、Ollama、智谱 AI、DeepSeek、MiniMax 等。

## 错误码

| 错误码 | 说明 |
|--------|------|
| `1_040_000_000` | API 密钥不存在 |
| `1_040_001_000` | 模型不存在 |
