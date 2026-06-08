# AI 模块数据模型

> 所有实体继承 `BaseDO`，包含字段：`id`、`creator`、`createTime`、`updater`、`updateTime`、`deleted`

## ER 关系总览

```
ai_api_key (API 密钥)
  └── ai_model (模型配置)          N:1 via key_id

ai_model
  └── ai_chat_role (聊天角色)      N:1 via model_id

ai_chat_role
  └── ai_chat_conversation (对话)  N:1 via role_id

ai_chat_conversation (聚合根)
  └── ai_chat_message (消息)       1:N via conversation_id

ai_knowledge (聚合根)
  └── ai_knowledge_document (文档) 1:N via knowledge_id
        └── ai_knowledge_segment   1:N via document_id
```

## 模型配置域

### ai_api_key - AI API 密钥表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| name | String | Y | 名称 |
| api_key | String | Y | 密钥 |
| platform | String | Y | 平台（枚举 AiPlatformEnum） |
| url | String | N | API 地址 |
| status | Integer | Y | 状态 |

### ai_model - AI 模型配置表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| key_id | Long | Y | API 密钥编号（FK -> ai_api_key.id） |
| name | String | Y | 模型名称 |
| model | String | Y | 模型标识 |
| platform | String | Y | 平台 |
| type | Integer | Y | 类型：1对话 2图片 3语音 4视频 5向量 6重排序 |
| sort | Integer | N | 排序值 |
| status | Integer | Y | 状态 |
| temperature | Double | N | 温度参数 |
| max_tokens | Integer | N | 最大 Token 数 |
| max_contexts | Integer | N | 最大上下文数 |

### ai_chat_role - AI 聊天角色表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| name | String | Y | 角色名称 |
| avatar | String | N | 角色头像 |
| category | String | N | 角色分类 |
| description | String | N | 角色描述 |
| system_message | String | N | 角色设定（系统提示词） |
| user_id | Long | N | 用户编号 |
| model_id | Long | N | 模型编号（FK -> ai_model.id） |
| knowledge_ids | List<Long> | N | 知识库编号列表 |
| tool_ids | List<Long> | N | 工具编号列表 |
| mcp_client_names | List<String> | N | MCP Client 名字列表 |
| public_status | Boolean | N | 是否公开 |
| sort | Integer | N | 排序值 |
| status | Integer | Y | 状态 |

### ai_tool - AI 工具表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| name | String | Y | 工具名称（Bean 名字） |
| description | String | N | 工具描述 |
| status | Integer | Y | 状态 |

## 聊天对话域

### ai_chat_conversation - AI 聊天对话表（聚合根）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| user_id | Long | Y | 用户编号 |
| title | String | N | 对话标题 |
| pinned | Boolean | N | 是否置顶 |
| pinned_time | LocalDateTime | N | 置顶时间 |
| role_id | Long | N | 角色编号（FK -> ai_chat_role.id） |
| model_id | Long | N | 模型编号（FK -> ai_model.id） |
| model | String | N | 模型标识 |
| system_message | String | N | 角色设定 |
| temperature | Double | N | 温度参数 |
| max_tokens | Integer | N | 最大 Token 数 |
| max_contexts | Integer | N | 最大上下文数 |

### ai_chat_message - AI 聊天消息表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| conversation_id | Long | Y | 对话编号（FK -> ai_chat_conversation.id） |
| reply_id | Long | N | 回复消息编号 |
| type | String | Y | 消息类型（USER / ASSISTANT / SYSTEM） |
| user_id | Long | N | 用户编号 |
| role_id | Long | N | 角色编号 |
| model | String | N | 模型标识 |
| model_id | Long | N | 模型编号 |
| content | String | N | 聊天内容 |
| reasoning_content | String | N | 推理内容 |
| use_context | Boolean | N | 是否携带上下文 |
| segment_ids | List<Long> | N | 知识库段落编号数组 |
| web_search_pages | List<WebPage> | N | 联网搜索网页内容 |
| attachment_urls | List<String> | N | 附件 URL 数组 |

## 图像生成域

### ai_image - AI 绘画表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| user_id | Long | Y | 用户编号 |
| prompt | String | Y | 提示词 |
| platform | String | Y | 平台 |
| model_id | Long | N | 模型编号 |
| model | String | N | 模型标识 |
| width | Integer | N | 图片宽度 |
| height | Integer | N | 图片高度 |
| status | Integer | Y | 生成状态 |
| finish_time | LocalDateTime | N | 完成时间 |
| error_message | String | N | 错误信息 |
| pic_url | String | N | 图片地址 |
| public_status | Boolean | N | 是否公开 |
| options | Map<String,Object> | N | 绘制参数 |
| buttons | List<Button> | N | MJ 按钮 |
| task_id | String | N | 任务编号 |

## 知识库域

### ai_knowledge - AI 知识库表（聚合根）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| name | String | Y | 知识库名称 |
| description | String | N | 知识库描述 |
| embedding_model_id | Long | N | 向量模型编号 |
| embedding_model | String | N | 模型标识 |
| top_k | Integer | N | TopK |
| similarity_threshold | Double | N | 相似度阈值 |
| status | Integer | Y | 状态 |

### ai_knowledge_document - AI 知识库文档表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| knowledge_id | Long | Y | 知识库编号（FK -> ai_knowledge.id） |
| name | String | Y | 文档名称 |
| url | String | N | 文件 URL |
| content | String | N | 内容 |
| content_length | Integer | N | 文档长度 |
| tokens | Integer | N | Token 数量 |
| segment_max_tokens | Integer | N | 分片最大 Token 数 |
| retrieval_count | Integer | N | 召回次数 |
| status | Integer | Y | 状态 |

### ai_knowledge_segment - AI 知识库分段表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| knowledge_id | Long | Y | 知识库编号（FK -> ai_knowledge.id） |
| document_id | Long | Y | 文档编号（FK -> ai_knowledge_document.id） |
| content | String | N | 切片内容 |
| content_length | Integer | N | 内容长度 |
| vector_id | String | N | 向量库编号 |
| tokens | Integer | N | Token 数量 |
| retrieval_count | Integer | N | 召回次数 |
| status | Integer | Y | 状态 |

## 音乐生成域

### ai_music - AI 音乐表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| user_id | Long | Y | 用户编号 |
| title | String | N | 音乐名称 |
| lyric | String | N | 歌词 |
| image_url | String | N | 图片地址 |
| audio_url | String | N | 音频地址 |
| video_url | String | N | 视频地址 |
| status | Integer | Y | 音乐状态 |
| generate_mode | Integer | N | 生成模式 |
| description | String | N | 描述词 |
| platform | String | N | 平台 |
| model | String | N | 模型 |
| tags | List<String> | N | 音乐风格标签 |
| duration | Double | N | 音乐时长 |
| public_status | Boolean | N | 是否公开 |
| task_id | String | N | 任务编号 |
| error_message | String | N | 错误信息 |

## 写作域

### ai_write - AI 写作表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| user_id | Long | Y | 用户编号 |
| type | Integer | Y | 写作类型 |
| platform | String | N | 平台 |
| model_id | Long | N | 模型编号 |
| model | String | N | 模型 |
| prompt | String | N | 生成内容提示 |
| generated_content | String | N | 生成的内容 |
| original_content | String | N | 原文 |
| length | Integer | N | 长度提示词 |
| format | Integer | N | 格式提示词 |
| tone | Integer | N | 语气提示词 |
| language | Integer | N | 语言提示词 |
| error_message | String | N | 错误信息 |

## 思维导图域

### ai_mind_map - AI 思维导图表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| user_id | Long | Y | 用户编号 |
| platform | String | N | 平台 |
| model_id | Long | N | 模型编号 |
| model | String | N | 模型 |
| prompt | String | N | 生成内容提示 |
| generated_content | String | N | 生成的内容 |
| error_message | String | N | 错误信息 |

## 工作流域

### ai_workflow - AI 工作流表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | Y | 编号 |
| name | String | Y | 工作流名称 |
| code | String | Y | 工作流标识 |
| graph | String | N | 工作流模型 JSON 数据 |
| remark | String | N | 备注 |
| status | Integer | Y | 状态 |

## 关键值对象

### AiPlatformEnum - AI 平台枚举

定义支持的 20+ AI 服务商，包括 OpenAI、Anthropic、Ollama、智谱 AI、DeepSeek、MiniMax 等。在 `ai_api_key.platform` 和 `ai_model.platform` 字段中使用。

### AiModelTypeEnum - 模型类型枚举

| 值 | 说明 |
|----|------|
| 1 | 对话 |
| 2 | 图片 |
| 3 | 语音 |
| 4 | 视频 |
| 5 | 向量 |
| 6 | 重排序 |
