# 写作助手 API

> Controller: `AiWriteController`
> 路径前缀：`/ai/write`

## 业务概述

写作助手利用大模型实现 AI 辅助写作，支持多种写作类型、格式、语气和语言的配置。

## Controller 接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| AI 写作 | POST | `/ai/write/generate` | 提交写作任务 |
| 创建 | POST | `/ai/write/create` | 创建写作记录 |
| 更新 | PUT | `/ai/write/update` | 更新写作记录 |
| 删除 | DELETE | `/ai/write/delete` | 删除写作记录 |
| 获取详情 | GET | `/ai/write/get` | 获取写作详情 |
| 分页查询 | GET | `/ai/write/page` | 分页查询写作列表 |

## Service 接口

```java
// AiWriteService - 写作生成与 CRUD
```

## 数据表

### ai_write

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| user_id | Long | 用户编号 |
| type | Integer | 写作类型 |
| platform | String | 平台 |
| model_id | Long | 模型编号 |
| model | String | 模型 |
| prompt | String | 生成内容提示 |
| generated_content | String | 生成的内容 |
| original_content | String | 原文 |
| length | Integer | 长度提示词 |
| format | Integer | 格式提示词 |
| tone | Integer | 语气提示词 |
| language | Integer | 语言提示词 |
| error_message | String | 错误信息 |
