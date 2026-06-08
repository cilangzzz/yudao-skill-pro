# Mall 模块文档

## 1. 模块概述

Mall 是 ruoyi-vue-pro 项目的电商核心模块（`yudao-module-mall`），提供完整的电商解决方案。
按 DDD 领域划分为四个子模块：

| 子模块 | 路径 | 定位 |
|--------|------|------|
| product | `yudao-module-product` | 商品管理：SPU/SKU 模型、分类、品牌、属性规格 |
| trade | `yudao-module-trade` | 交易订单：购物车、订单、售后 |
| promotion | `yudao-module-promotion` | 促销活动：优惠券、秒杀、拼团、砍价 |
| statistics | `yudao-module-statistics` | 数据统计：交易统计、商品统计、会员统计 |

> trade-api 为独立模块，提供跨模块调用接口。

---

## 2. 核心功能点

### 2.1 商品管理（product）

| 功能 | 说明 | 核心 Service |
|------|------|-------------|
| SPU 管理 | 商品标准化单元，管理名称、分类、品牌、轮播图、详情等 | `ProductSpuService` |
| SKU 管理 | 库存单位，支持单规格/多规格，管理价格、库存、条码、重量体积 | `ProductSkuService` |
| 分类管理 | 支持父子层级，启用/禁用状态 | `ProductCategoryService` |
| 品牌管理 | 品牌图片、排序、状态 | `ProductBrandService` |
| 属性规格 | 商品属性与规格值管理 | `ProductPropertyService` |
| 运费模板 | 按重量/体积/件数计费 | `DeliveryExpressTemplateService` |

### 2.2 交易订单（trade）

| 功能 | 说明 | 核心 Service |
|------|------|-------------|
| 购物车 | 用户端商品加购、数量修改、删除 | `CartService` |
| 订单创建 | 合并购物车下单，计算价格，扣减库存，使用优惠券 | `TradeOrderUpdateService` |
| 订单查询 | 管理后台/用户端分页查询，按状态筛选 | `TradeOrderQueryService` |
| 订单状态机 | 待付款 -> 待发货 -> 待收货 -> 已完成 / 已取消 | `TradeOrderUpdateService` |
| 售后退款 | 退款、退货退款，状态流转 | `AfterSaleService` |
| 价格计算 | 商品价格 + 运费 - 优惠券 - 满减等 | `TradePriceService` |
| 物流管理 | 物流公司、物流轨迹查询 | `DeliveryExpressService` |

### 2.3 促销活动（promotion）

| 功能 | 说明 | 核心 Service |
|------|------|-------------|
| 优惠券 | 模板创建、发放、领取、使用、过期 | `CouponService` / `CouponTemplateService` |
| 秒杀 | 活动创建、时间段管理、限购、库存扣减 | `SeckillActivityService` |
| 拼团 | 成团人数、拼团时长、参团记录 | `CombinationActivityService` |
| 砍价 | 起始价/最低价、砍价记录 | `BargainActivityService` |
| 满减送 | 满足条件自动减免或赠送 | `RewardActivityService` |
| 积分商城 | 积分兑换商品 | `PointActivityService` |

### 2.4 数据统计（statistics）

| 功能 | 说明 | 核心 Service |
|------|------|-------------|
| 交易统计 | 订单量、销售额、客单价等 | `TradeStatisticsService` |
| 商品统计 | 商品销量排行、库存预警 | `ProductStatisticsService` |

---

## 3. API 索引

详细 API 文档按业务域拆分，参见以下文件：

| 业务域 | 文档 | 说明 |
|--------|------|------|
| 商品 | [api-product.md](./api-product.md) | SPU/SKU/分类/品牌/属性管理接口 |
| 订单 | [api-order.md](./api-order.md) | 订单/购物车/售后/物流接口 |
| 促销 | [api-promotion.md](./api-promotion.md) | 优惠券/秒杀/拼团/砍价接口 |
| 统计 | [api-statistics.md](./api-statistics.md) | 交易/商品统计接口 |

### 3.1 HTTP 接口分层

接口分为两类：

- **管理后台（admin）**：路径前缀 `/admin-api/product/`、`/admin-api/trade/`、`/admin-api/promotion/`
- **用户端（app）**：路径前缀 `/app-api/product/`、`/app-api/trade/`、`/app-api/promotion/`

### 3.2 跨模块 RPC API

| API 接口 | 所在模块 | 用途 |
|----------|---------|------|
| `ProductSpuApi` | product | 查询商品信息、更新库存 |
| `ProductSkuApi` | product | 查询 SKU 信息、更新库存 |
| `TradeOrderApi` | trade | 查询订单信息 |
| `CouponApi` | promotion | 优惠券使用、回收 |
| `SeckillActivityApi` | promotion | 秒杀活动校验、库存扣减 |
| `CombinationRecordApi` | promotion | 拼团记录校验 |

---

## 4. 数据模型

详见 [data-model.md](./data-model.md)，核心实体关系：

```
ProductSpu (聚合根)
  |-- ProductSku (1:N)
  |-- ProductCategory (N:1)
  |-- ProductBrand (N:1)
  |-- ProductProperty (1:N)

TradeOrder (聚合根)
  |-- TradeOrderItem (1:N)
  |-- AfterSale (1:N)
  |-- Cart (用户维度)

CouponTemplate (聚合根)
  |-- Coupon (1:N)

CombinationActivity (聚合根)
  |-- CombinationProduct (1:N)
  |-- CombinationRecord (1:N)
```

---

## 5. 设计模式

| 模式 | 位置 | 说明 |
|------|------|------|
| 状态模式 | `TradeOrderStatusEnum`, `ProductSpuStatusEnum` | 订单/商品状态机管理 |
| 策略模式 | `TradePriceService` | 不同促销活动的价格计算策略 |
| 模板方法 | `BaseDO`, `TenantBaseDO` | 数据实体基类，统一处理公共字段 |
| 工厂模式 | `ProductSpuConvert`, `TradeOrderConvert` | MapStruct VO/DO 转换 |
| 观察者模式 | `TradeOrderLogService` | 订单状态变更自动记录日志 |

---

## 6. 依赖关系

### 6.1 内部模块依赖

| 依赖模块 | API | 用途 |
|----------|-----|------|
| yudao-module-member | `MemberUserApi` | 获取会员信息，订单关联用户 |
| yudao-module-pay | `PayOrderApi` | 创建支付订单，处理支付回调 |
| yudao-module-system | `AreaApi` | 获取地区信息，用于收货地址 |

### 6.2 消息队列

| Topic | 说明 |
|-------|------|
| `order.paid` | 订单支付成功，触发积分发放、优惠券赠送 |
| `order.delivered` | 订单发货，通知用户 |

### 6.3 外部依赖

| 库 | 版本 | 用途 |
|----|------|------|
| MyBatis-Plus | 3.x | ORM 框架 |
| MapStruct | 1.x | 对象映射 |
| Spring Validation | 2.x | 参数校验 |
| Swagger/OpenAPI | 3.x | API 文档 |
| Redis | 6.x | 缓存、分布式锁、库存扣减 |

---

## 7. 错误码范围

| 模块 | 错误码前缀 | 示例 |
|------|-----------|------|
| product | `1-008-xxx-xxx` | `1_008_005_000` = 商品 SPU 不存在 |
| trade | `1-011-xxx-xxx` | `1_011_000_011` = 交易订单不存在 |
| promotion | `1-013-xxx-xxx` | `1_013_004_000` = 优惠券模板不存在 |

---

## 8. 关键文件清单

| 模块 | 文件 | 说明 |
|------|------|------|
| product | `product/dal/dataobject/spu/ProductSpuDO.java` | 商品 SPU 实体类 |
| product | `product/dal/dataobject/sku/ProductSkuDO.java` | 商品 SKU 实体类 |
| product | `product/service/spu/ProductSpuService.java` | 商品 SPU 服务接口 |
| product | `product/controller/admin/spu/ProductSpuController.java` | 商品 SPU 管理接口 |
| trade | `trade/dal/dataobject/order/TradeOrderDO.java` | 交易订单实体类 |
| trade | `trade/service/order/TradeOrderUpdateService.java` | 订单更新服务 |
| trade | `trade/service/price/TradePriceService.java` | 价格计算服务 |
| trade | `trade/service/aftersale/AfterSaleService.java` | 售后服务 |
| promotion | `promotion/dal/dataobject/coupon/CouponTemplateDO.java` | 优惠券模板实体类 |
| promotion | `promotion/dal/dataobject/seckill/SeckillActivityDO.java` | 秒杀活动实体类 |
| promotion | `promotion/dal/dataobject/combination/CombinationActivityDO.java` | 拼团活动实体类 |
| statistics | `statistics/service/trade/TradeStatisticsService.java` | 交易统计服务 |
