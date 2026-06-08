# 数据统计 API

## 概述

CRM 数据统计模块提供多维度的销售数据分析能力，包括客户统计、销售漏斗分析、业绩统计、客户画像和排行榜功能。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmStatisticsCustomerController | `/crm/statistics/customer` | 客户统计接口 |
| CrmStatisticsFunnelController | `/crm/statistics/funnel` | 销售漏斗统计接口 |
| CrmStatisticsPerformanceController | `/crm/statistics/performance` | 业绩统计接口 |
| CrmStatisticsPortraitController | `/crm/statistics/portrait` | 客户画像统计接口 |
| CrmStatisticsRankController | `/crm/statistics/rank` | 排行榜统计接口 |

## 接口列表

### 客户统计

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 客户数量统计 | GET | `/crm/statistics/customer/count` | 按时间维度统计新增客户数 |
| 客户来源分布 | GET | `/crm/statistics/customer/source` | 按来源维度统计客户分布 |
| 客户行业分布 | GET | `/crm/statistics/customer/industry` | 按行业维度统计客户分布 |
| 客户等级分布 | GET | `/crm/statistics/customer/level` | 按等级维度统计客户分布 |

### 销售漏斗

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 漏斗数据 | GET | `/crm/statistics/funnel/summary` | 按商机状态统计销售漏斗 |
| 漏斗转化率 | GET | `/crm/statistics/funnel/conversion` | 各阶段转化率分析 |

### 业绩统计

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 合同金额统计 | GET | `/crm/statistics/performance/contract` | 按时间维度统计合同金额 |
| 回款金额统计 | GET | `/crm/statistics/performance/receivable` | 按时间维度统计回款金额 |
| 业绩目标完成率 | GET | `/crm/statistics/performance/target` | 业绩目标完成情况 |

### 客户画像

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 客户画像 | GET | `/crm/statistics/portrait/summary` | 客户多维度画像数据 |

### 排行榜

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 销售排行榜 | GET | `/crm/statistics/rank/sales` | 按合同/回款金额排名 |
| 客户排行榜 | GET | `/crm/statistics/rank/customer` | 按客户数量排名 |
| 商机排行榜 | GET | `/crm/statistics/rank/business` | 按商机金额排名 |

## 业务规则

1. **数据范围**：统计数据基于当前用户的权限范围，只能看到有权限的数据
2. **时间维度**：支持按日、周、月、季、年等维度统计
3. **销售漏斗**：基于商机状态组（CrmBusinessStatusTypeDO）和状态（CrmBusinessStatusDO）的赢单率计算

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/statistics/CrmStatisticsCustomerService.java` | 客户统计服务 |
| `service/statistics/CrmStatisticsFunnelService.java` | 漏斗统计服务 |
| `service/statistics/CrmStatisticsPerformanceService.java` | 业绩统计服务 |
| `service/statistics/CrmStatisticsPortraitService.java` | 客户画像服务 |
| `service/statistics/CrmStatisticsRankService.java` | 排行榜服务 |
| `controller/admin/statistics/CrmStatisticsCustomerController.java` | 客户统计控制器 |
| `controller/admin/statistics/CrmStatisticsFunnelController.java` | 漏斗统计控制器 |
| `controller/admin/statistics/CrmStatisticsPerformanceController.java` | 业绩统计控制器 |
| `controller/admin/statistics/CrmStatisticsPortraitController.java` | 客户画像控制器 |
| `controller/admin/statistics/CrmStatisticsRankController.java` | 排行榜控制器 |
