# 知识库 API

> Controller: `AiKnowledgeController`
> 路径前缀：`/ai/knowledge`

## 业务概述

知识库提供 RAG（检索增强生成）能力，支持文档上传、自动分片、向量存储、语义检索。聊天对话可通过绑定知识库实现上下文增强。

## 核心流程

1. 创建知识库，配置向量模型和检索参数
2. 上传文档，自动进行内容提取和分片
3. 分片内容通过 EmbeddingModel 生成向量，存入向量数据库
4. 聊天时对用户问题做语义检索，召回相关分片作为上下文

## Controller 接口

### 知识库管理（/ai/knowledge）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建知识库 | POST | `/ai/knowledge/create` | 创建知识库 |
| 更新知识库 | PUT | `/ai/knowledge/update` | 更新知识库配置 |
| 删除知识库 | DELETE | `/ai/knowledge/delete` | 删除知识库 |
| 获取详情 | GET | `/ai/knowledge/get` | 获取知识库详情 |
| 分页查询 | GET | `/ai/knowledge/page` | 分页查询知识库列表 |

### 文档管理（/ai/knowledge/document）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 上传文档 | POST | `/ai/knowledge/document/create` | 上传并处理文档 |
| 删除文档 | DELETE | `/ai/knowledge/document/delete` | 删除文档及其分片 |
| 获取详情 | GET | `/ai/knowledge/document/get` | 获取文档详情 |
| 分页查询 | GET | `/ai/knowledge/document/page` | 分页查询文档列表 |

### 分段管理（/ai/knowledge/segment）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 获取详情 | GET | `/ai/knowledge/segment/get` | 获取分段详情 |
| 分页查询 | GET | `/ai/knowledge/segment/page` | 分页查询分段列表 |

## Service 接口

### AiKnowledgeService

```java
public interface AiKnowledgeService {
    // 知识库 CRUD
    // 文档 CRUD
    // 分段检索
}
```

## 向量模型调用

```java
// 获取 EmbeddingModel
EmbeddingModel embeddingModel = modelService.getOrCreateVectorStore(modelId, metadataFields);

// 生成向量
EmbeddingResponse response = embeddingModel.embedForResponse(texts);
```

## 数据表

### ai_knowledge

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| name | String | 知识库名称 |
| description | String | 知识库描述 |
| embedding_model_id | Long | 向量模型编号 |
| embedding_model | String | 模型标识 |
| top_k | Integer | TopK |
| similarity_threshold | Double | 相似度阈值 |
| status | Integer | 状态 |

### ai_knowledge_document

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| knowledge_id | Long | 知识库编号 |
| name | String | 文档名称 |
| url | String | 文件 URL |
| content | String | 内容 |
| content_length | Integer | 文档长度 |
| tokens | Integer | Token 数量 |
| segment_max_tokens | Integer | 分片最大 Token 数 |
| retrieval_count | Integer | 召回次数 |
| status | Integer | 状态 |

### ai_knowledge_segment

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| knowledge_id | Long | 知识库编号 |
| document_id | Long | 文档编号 |
| content | String | 切片内容 |
| content_length | Integer | 内容长度 |
| vector_id | String | 向量库编号 |
| tokens | Integer | Token 数量 |
| retrieval_count | Integer | 召回次数 |
| status | Integer | 状态 |

## 表关系

```
ai_knowledge (聚合根)
  └── ai_knowledge_document  1:N via knowledge_id
        └── ai_knowledge_segment  1:N via document_id
```

## 向量存储选型

| 存储 | 适用场景 |
|------|----------|
| SimpleVectorStore | 测试/开发环境 |
| Milvus | 生产环境（推荐） |
| Qdrant | 生产环境 |
| Redis | 轻量级场景 |

## 错误码

| 错误码 | 说明 |
|--------|------|
| `1_040_009_000` | 知识库不存在 |
