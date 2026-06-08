# 思维导图 API

> Controller: `AiMindMapController`
> 路径前缀：`/ai/mind-map`

## 业务概述

思维导图功能利用大模型根据用户输入的提示词自动生成结构化思维导图内容。

## Controller 接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 生成思维导图 | POST | `/ai/mind-map/generate` | 提交思维导图生成任务 |
| 创建 | POST | `/ai/mind-map/create` | 创建思维导图记录 |
| 更新 | PUT | `/ai/mind-map/update` | 更新思维导图记录 |
| 删除 | DELETE | `/ai/mind-map/delete` | 删除思维导图记录 |
| 获取详情 | GET | `/ai/mind-map/get` | 获取思维导图详情 |
| 分页查询 | GET | `/ai/mind-map/page` | 分页查询列表 |

## 数据表

### ai_mind_map

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| user_id | Long | 用户编号 |
| platform | String | 平台 |
| model_id | Long | 模型编号 |
| model | String | 模型 |
| prompt | String | 生成内容提示 |
| generated_content | String | 生成的内容 |
| error_message | String | 错误信息 |
