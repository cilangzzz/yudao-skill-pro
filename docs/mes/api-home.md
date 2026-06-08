# 首页看板 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 首页统计（Home）

**Controller**: `MesHomeController`
**路径前缀**: `/admin-api/mes/home`
**权限前缀**: `mes:home:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/order-summary` | 订单汇总统计 | `mes:home:query` |
| GET | `/work-order-status` | 工单状态统计 | `mes:home:query` |
| GET | `/production-trend` | 生产趋势统计 | `mes:home:query` |

### 1.2 订单汇总统计

**接口**: `GET /admin-api/mes/home/order-summary`

返回订单相关的汇总数据：

| 字段 | 类型 | 说明 |
|------|------|------|
| totalOrders | Integer | 总订单数 |
| pendingOrders | Integer | 待处理订单数 |
| inProgressOrders | Integer | 进行中订单数 |
| completedOrders | Integer | 已完成订单数 |
| todayOrders | Integer | 今日新增订单数 |

### 1.3 工单状态统计

**接口**: `GET /admin-api/mes/home/work-order-status`

返回工单各状态的数量统计：

| 字段 | 类型 | 说明 |
|------|------|------|
| draft | Integer | 草稿数量 |
| confirmed | Integer | 已确认数量 |
| finished | Integer | 已完工数量 |
| cancelled | Integer | 已取消数量 |
| overdue | Integer | 超期未完工数量 |

### 1.4 生产趋势统计

**接口**: `GET /admin-api/mes/home/production-trend`

返回近 N 天的生产趋势数据：

| 字段 | 类型 | 说明 |
|------|------|------|
| dates | List\<String\> | 日期列表 |
| planQuantities | List\<BigDecimal\> | 计划产量 |
| actualQuantities | List\<BigDecimal\> | 实际产量 |
| completionRates | List\<BigDecimal\> | 完成率 |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | Integer | 否 | 统计天数，默认 7 天 |

---

## 核心设计要点

### 数据聚合

首页统计数据通过聚合查询实现：
- 订单汇总：从 `mes_pro_work_order` 表按状态分组统计
- 工单状态：从 `mes_pro_work_order` 表按状态聚合
- 生产趋势：从 `mes_pro_work_record` 表按日期聚合

### 性能优化

- 首页统计数据建议使用缓存（Redis），设置合理的过期时间
- 生产趋势数据按天聚合，避免实时查询大表
- 可考虑使用定时任务预计算统计数据

### 权限控制

首页看板数据需要 `mes:home:query` 权限，通常授权给生产管理人员和车间主管。
