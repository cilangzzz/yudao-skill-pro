# 工作流 API

> Controller: `AiWorkflowController`
> 路径前缀：`/ai/workflow`

## 业务概述

工作流提供可视化 AI 工作流编排能力，通过 JSON 图形数据定义工作流节点和连接关系。

## Controller 接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建工作流 | POST | `/ai/workflow/create` | 创建工作流 |
| 更新工作流 | PUT | `/ai/workflow/update` | 更新工作流 |
| 删除工作流 | DELETE | `/ai/workflow/delete` | 删除工作流 |
| 获取详情 | GET | `/ai/workflow/get` | 获取工作流详情 |
| 分页查询 | GET | `/ai/workflow/page` | 分页查询列表 |

## 数据表

### ai_workflow

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| name | String | 工作流名称 |
| code | String | 工作流标识 |
| graph | String | 工作流模型 JSON 数据 |
| remark | String | 备注 |
| status | Integer | 状态 |
