# 数据统计 API

> 对应 Controller：`MpStatisticsController` | 路径前缀：`/mp/statistics`

## 功能说明

获取公众号数据统计信息，包括用户分析、消息分析等运营数据。

## 核心服务

### MpStatisticsService

| 方法 | 说明 |
|------|------|
| 用户分析 | 获取用户增减数据、累计用户数据 |
| 消息分析 | 获取消息发送概况数据 |

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- 统计数据从微信 API 实时获取

## 设计要点

- 统计数据来自微信 API，本地不做持久化
- 查询时需指定日期范围
- 数据粒度为天
