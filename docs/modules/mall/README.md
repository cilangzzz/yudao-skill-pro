# 商城模块 (mall)

> 覆盖「商品 — 交易 — 营销 — 统计」完整电商闭环的多子模块业务集群，是 yudao 中体量最大、子模块间协作最复杂的业务域。

## 模块概述

- **模块路径**: `yudao-module-mall`（聚合父工程，下辖 5 个子模块）
  - `yudao-module-product`：商品中心（SPU/SKU、分类、品牌、属性、评价、收藏、浏览记录）
  - `yudao-module-promotion`：营销中心（优惠劵、秒杀、拼团、砍价、限时折扣、满减送、积分商城、装修、文章、Banner、客服）
  - `yudao-module-trade`：交易中心（订单、售后、配送、分销、交易配置、购物车）
  - `yudao-module-statistics`：统计中心（交易/商品/会员/支付统计）
  - `yudao-module-trade-api`：纯 API 骨架包（仅 `TradeOrderApi` + DTO + 错误码，无业务实现）
- **业务定位**: 提供电商后台的完整能力：商品发布与管理、订单履约与售后、各类促销活动的配置与核销、经营数据统计；Admin 端（`controller/admin`）供商家后台使用，App 端（`controller/app`）供 C 端商城使用。
- **技术栈**: Spring Boot 2.7.18（仓库为 `2026.09-jdk8-SNAPSHOT` jdk8 分支）/ MyBatis-Plus 3.5.17 / Redisson 4.7.0（trade 子模块） / yudao framework starters（web、security、mybatis、excel、biz-tenant、biz-ip、redis）

## 设计原则

| 原则 | 说明 |
|-----|------|
| 多子模块拆分 | 商品/营销/交易/统计各自独立 Maven 子模块，按业务域隔离代码与表，避免单模块膨胀 |
| trade-api 解循环依赖 | promotion 与 trade 相互依赖（拼团/砍价要取消订单，订单要计算活动优惠），故抽出纯接口的 `yudao-module-trade-api` 切断循环 |
| 价格计算责任链 | 下单价格由 `TradePriceCalculator` 责任链按 `@Order` 顺序计算（优惠劵、限时折扣、满减、秒杀、拼团、砍价、积分等 10 个 Calculator 依次叠加） |
| 订单处理策略模式 | 订单创建/支付后的扩展动作用 `TradeOrderHandler` 策略分发，每种活动类型一个 Handler（共 9 个），新增活动类型无需改动订单主干 |
| Admin/App 双端分离 | 每个业务域分设 `controller/admin` 与 `controller/app`，VO 独立、权限独立，互不复用 |
| 跨模块仅依赖 Api 包 | 对 system/member/pay/infra 的调用全部走 `XxxApi` 接口 + DTO（如 `MemberUserApi`、`PayOrderApi`），不直接依赖对方实现类 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 商品管理 | SPU/SKU 发布、上下架、分类与品牌维护、属性（规格）管理、Excel 导出 | ProductSpuDO、ProductSkuDO、ProductCategoryDO、ProductBrandDO、ProductPropertyDO |
| 商品互动 | 商品评价（含商家回复/隐藏）、收藏、浏览记录 | ProductCommentDO、ProductFavoriteDO、ProductBrowseHistoryDO |
| 优惠劵 | 劵模板（满减/折扣/包邮）发放，劵的领取、使用、回收 | CouponTemplateDO、CouponDO |
| 促销活动 | 秒杀（时段+活动）、拼团、砍价（助力）、限时折扣、满减送、积分商城六类活动及记录 | SeckillActivityDO、CombinationRecordDO、BargainRecordDO、DiscountActivityDO、RewardActivityDO、PointActivityDO |
| 店铺装修 | DIY 模板与页面，JSON 装修属性驱动 C 端首页/商品页 | DiyTemplateDO、DiyPageDO |
| 内容运营 | 文章/文章分类、Banner 轮播位 | ArticleDO、BannerDO |
| 客服 | 会话管理、消息收发（WebSocket 推送）、置顶、已读 | KeFuConversationDO、KeFuMessageDO |
| 交易订单 | 下单（含价格责任链计算）、支付回调、发货、核销、确认收货、自动取消/收货/评价 Job | TradeOrderDO、TradeOrderItemDO、TradeOrderLogDO、CartDO |
| 售后 | 仅退款/退货退款流程、售后日志、退款支付回调 | AfterSaleDO、AfterSaleLogDO |
| 配送 | 快递公司、运费模板（计费/包邮明细）、自提门店与店员绑定 | DeliveryExpressDO、DeliveryExpressTemplateDO、DeliveryPickUpStoreDO |
| 分销 | 推广员绑定、佣金分成（一二级）、佣金冻结/解冻、提现审核 | BrokerageUserDO、BrokerageRecordDO、BrokerageWithdrawDO |
| 交易配置 | 售后原因、分销规则、免邮门槛等全局交易配置 | TradeConfigDO |
| 数据统计 | 交易状况、商品排行、会员分析、支付汇总；定时 Job 落库统计表 | TradeStatisticsDO、ProductStatisticsDO |

## API 接口索引

> Admin 端共 **41 个 Controller、217 个端点**，超过 120，按域分节给出控制器级摘要；另有 `controller/app` 下 32 个 App 端 Controller（约 99 个端点）不在本文档范围内。端点明细见各 `api-{key}.md`。

### 商品中心（product 子模块，41 端点）

| Controller | 说明 | 端点数 | 明细 |
|-----------|------|-------|------|
| ProductSpuController | 商品 SPU（含上下架、导出） | 10 | [api-spu.md](api-spu.md) |
| ProductBrandController | 商品品牌 | 7 | [api-brand.md](api-brand.md) |
| ProductPropertyController | 商品属性项 | 6 | [api-property.md](api-property.md) |
| ProductPropertyValueController | 商品属性值 | 6 | [api-property.md](api-property.md) |
| ProductCategoryController | 商品分类 | 5 | [api-category.md](api-category.md) |
| ProductCommentController | 商品评价（回复/隐藏/自评） | 5 | [api-comment.md](api-comment.md) |
| ProductFavoriteController | 商品收藏 | 1 | [api-favorite.md](api-favorite.md) |
| ProductBrowseHistoryController | 商品浏览记录 | 1 | [api-history.md](api-history.md) |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /product/spu/create | POST | 创建商品 SPU | product:spu:create |
| /product/spu/update-status | PUT | 更新商品 SPU Status | product:spu:update |
| /product/spu/get-detail | GET | 获得商品 SPU 明细 | product:spu:query |
| /product/spu/get-count | GET | 获得 SPU 分页 tab count | product:spu:query |
| /product/spu/export-excel | GET | 导出商品 | product:spu:export |
| /product/property/simple-list | GET | 获得属性项精简列表 | 已认证 |
| /product/comment/reply | PUT | 商家回复 | product:comment:update |

### 营销中心（promotion 子模块，101 端点）

| Controller | 说明 | 端点数 | 明细 |
|-----------|------|-------|------|
| DiyPageController | 装修页面 | 8 | [api-diy.md](api-diy.md) |
| DiyTemplateController | 装修模板 | 8 | [api-diy.md](api-diy.md) |
| SeckillConfigController | 秒杀时段 | 8 | [api-seckill.md](api-seckill.md) |
| SeckillActivityController | 秒杀活动 | 7 | [api-seckill.md](api-seckill.md) |
| CombinationActivityController | 拼团活动 | 7 | [api-combination.md](api-combination.md) |
| CouponTemplateController | 优惠劵模板 | 7 | [api-coupon.md](api-coupon.md) |
| PointActivityController | 积分商城活动 | 7 | [api-point.md](api-point.md) |
| ArticleCategoryController | 文章分类 | 6 | [api-article.md](api-article.md) |
| ArticleController | 文章管理 | 5 | [api-article.md](api-article.md) |
| BannerController | Banner 管理 | 5 | [api-banner.md](api-banner.md) |
| BargainActivityController | 砍价活动 | 6 | [api-bargain.md](api-bargain.md) |
| DiscountActivityController | 限时折扣活动 | 6 | [api-discount.md](api-discount.md) |
| RewardActivityController | 满减送活动 | 6 | [api-reward.md](api-reward.md) |
| CouponController | 优惠劵（发放/回收） | 4 | [api-coupon.md](api-coupon.md) |
| KeFuConversationController | 客服会话 | 4 | [api-kefu.md](api-kefu.md) |
| KeFuMessageController | 客服消息 | 3 | [api-kefu.md](api-kefu.md) |
| CombinationRecordController | 拼团记录 | 2 | [api-combination.md](api-combination.md) |
| BargainHelpController | 砍价助力 | 1 | [api-bargain.md](api-bargain.md) |
| BargainRecordController | 砍价记录 | 1 | [api-bargain.md](api-bargain.md) |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /promotion/seckill-activity/close | PUT | 关闭秒杀活动 | promotion:seckill-activity:close |
| /promotion/combination-activity/create | POST | 创建拼团活动 | promotion:combination-activity:create |
| /promotion/coupon/send | POST | 发送优惠劵 | promotion:coupon:send |
| /promotion/coupon/delete | DELETE | 回收优惠劵 | promotion:coupon:delete |
| /promotion/bargain-activity/close | PUT | 关闭砍价活动 | promotion:bargain-activity:close |
| /promotion/discount-activity/page | GET | 获得限时折扣活动分页 | promotion:discount-activity:query |
| /promotion/reward-activity/page | GET | 获得满减送活动分页 | promotion:reward-activity:query |
| /promotion/point-activity/list-by-ids | GET | 基于活动编号数组获得积分商城活动 | 已认证 |
| /promotion/diy-template/use | PUT | 使用装修模板 | promotion:diy-template:use |
| /promotion/kefu-message/send | POST | 发送客服消息 | promotion:kefu-message:send |

### 交易中心（trade 子模块，56 端点）

| Controller | 说明 | 端点数 | 明细 |
|-----------|------|-------|------|
| DeliveryPickUpStoreController | 自提门店（含店员绑定） | 8 | [api-trade-delivery.md](api-trade-delivery.md) |
| AfterSaleController | 售后订单（审核/退款/支付回调） | 8 | [api-trade-aftersale.md](api-trade-aftersale.md) |
| DeliveryExpressController | 快递公司 | 7 | [api-trade-delivery.md](api-trade-delivery.md) |
| DeliveryExpressTemplateController | 快递运费模板 | 7 | [api-trade-delivery.md](api-trade-delivery.md) |
| BrokerageUserController | 分销用户 | 6 | [api-trade-brokerage.md](api-trade-brokerage.md) |
| TradeOrderController | 交易订单（发货/核销/调价/改址） | 11 | [api-trade-order.md](api-trade-order.md) |
| BrokerageWithdrawController | 佣金提现（审核/转账回调） | 5 | [api-trade-brokerage.md](api-trade-brokerage.md) |
| BrokerageRecordController | 佣金记录 | 2 | [api-trade-brokerage.md](api-trade-brokerage.md) |
| TradeConfigController | 交易中心配置 | 2 | [api-trade-config.md](api-trade-config.md) |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /trade/order/page | GET | 获得交易订单分页 | trade:order:query |
| /trade/order/get-detail | GET | 获得交易订单详情 | trade:order:query |
| /trade/order/delivery | PUT | 订单发货 | trade:order:update |
| /trade/order/pick-up-by-verify-code | PUT | 订单核销 | trade:order:pick-up |
| /trade/order/update-address | PUT | 修改订单收货地址 | trade:order:update |
| /trade/after-sale/agree | PUT | 同意售后 | trade:after-sale:agree |
| /trade/after-sale/refund | PUT | 确认退款 | trade:after-sale:refund |
| /trade/after-sale/update-refunded | POST | 更新售后为已退款（pay-module 回调） | @PermitAll |
| /trade/brokerage-withdraw/approve | PUT | 佣金提现通过申请 | trade:brokerage-withdraw:audit |
| /trade/brokerage-withdraw/update-transferred | POST | 更新提现转账结果（pay-module 回调） | @PermitAll |
| /trade/delivery/pick-up-store/bind | POST | 绑定自提店员 | trade:delivery:pick-up-store:create |
| /trade/config/save | PUT | 更新交易中心配置 | trade:config:save |

### 统计中心（statistics 子模块，19 端点）

| Controller | 说明 | 端点数 | 明细 |
|-----------|------|-------|------|
| TradeStatisticsController | 交易统计（概况/趋势/对比/导出） | 7 | [api-statistics-trade.md](api-statistics-trade.md) |
| MemberStatisticsController | 会员统计（概览/地域/性别/终端） | 7 | [api-statistics-member.md](api-statistics-member.md) |
| ProductStatisticsController | 商品统计（分析/明细/排行/导出） | 4 | [api-statistics-product.md](api-statistics-product.md) |
| PayStatisticsController | 支付统计（充值金额汇总） | 1 | [api-statistics-pay.md](api-statistics-pay.md) |

代表性端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /statistics/trade/summary | GET | 获得交易统计 | statistics:trade:query |
| /statistics/trade/order-count-trend | GET | 获得订单量趋势统计 | statistics:trade:query |
| /statistics/trade/export-excel | GET | 导出交易状况明细 Excel | statistics:trade:export |
| /statistics/product/rank-page | GET | 商品统计排行榜分页 | statistics:product:query |
| /statistics/member/analyse | GET | 获得会员分析数据 | statistics:member:query |
| /statistics/pay/summary | GET | 获取充值金额 | 已认证 |

## 数据模型

> 共 49 张表；所有 DO 均继承 `BaseDO`（mall 未启用 TenantBaseDO 租户隔离），仅标注 `@TableName(autoResultMap = true)` 的表含 JSON/复杂类型字段。

### product 子模块（9 张）

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| product_spu | 商品 SPU | BaseDO | name、category_id、brand_id、spec_type、price、stock、delivery_types、sub_commission_type、status |
| product_sku | 商品 SKU | BaseDO | spu_id、properties、price、market_price、cost_price、stock、weight |
| product_category | 商品分类 | BaseDO | parent_id、name、pic_url、sort、status |
| product_brand | 商品品牌 | BaseDO | name、pic_url、status |
| product_property | 商品属性项 | BaseDO | name、status |
| product_property_value | 商品属性值 | BaseDO | property_id、name、status |
| product_comment | 商品评价 | BaseDO | user_id、order_item_id、spu_id、scores、content、pic_urls、visible、reply |
| product_favorite | 商品收藏 | BaseDO | user_id、spu_id |
| product_browse_history | 商品浏览记录 | BaseDO | user_id、spu_id |

### promotion 子模块（23 张）

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| promotion_coupon_template | 优惠劵模板 | BaseDO | name、discount_type、discount_percent、discount_price、use_price、validity_type、total_count、take_count、product_scope |
| promotion_coupon | 优惠劵 | BaseDO | template_id、user_id、status、use_order_id、valid_end_time |
| promotion_seckill_config | 秒杀时段配置 | BaseDO | name、start_time、end_time、status |
| promotion_seckill_activity | 秒杀活动 | BaseDO | config_id、spu_id、start_time、end_time、total_limit_count |
| promotion_seckill_product | 秒杀活动商品 | BaseDO | activity_id、spu_id、sku_id、seckill_price、stock |
| promotion_combination_activity | 拼团活动 | BaseDO | spu_id、team_count、team_duration、total_limit_count |
| promotion_combination_product | 拼团活动商品 | BaseDO | activity_id、spu_id、sku_id、combination_price |
| promotion_combination_record | 拼团记录 | BaseDO | activity_id、user_id、head_id、user_count、status、order_id |
| promotion_bargain_activity | 砍价活动 | BaseDO | spu_id、sku_id、random_min_price、random_max_price、help_max_count |
| promotion_bargain_record | 砍价记录 | BaseDO | activity_id、user_id、bargaining_price、status、order_id |
| promotion_bargain_help | 砍价助力 | BaseDO | record_id、user_id、reduction_price |
| promotion_discount_activity | 限时折扣活动 | BaseDO | name、start_time、end_time、status |
| promotion_discount_product | 限时折扣商品 | BaseDO | activity_id、spu_id、sku_id、discount_price |
| promotion_reward_activity | 满减送活动 | BaseDO | name、condition_type、rules、start_time、end_time |
| promotion_point_activity | 积分商城活动 | BaseDO | spu_id、point、stock、total_stock、start_time、end_time |
| promotion_point_product | 积分商城活动商品 | BaseDO | activity_id、spu_id、sku_id、point、price、stock |
| promotion_diy_template | 装修模板 | BaseDO | name、property、used |
| promotion_diy_page | 装修页面 | BaseDO | name、property、status |
| promotion_article | 文章 | BaseDO | category_id、title、author、pic_url、spu_id |
| promotion_article_category | 文章分类 | BaseDO | name、status |
| promotion_banner | 轮播图 | BaseDO | title、pic_url、position、status |
| promotion_kefu_conversation | 客服会话 | BaseDO | user_id、last_message_time、last_message_content、admin_pinned、admin_unread_message_count |
| promotion_kefu_message | 客服消息 | BaseDO | conversation_id、sender_user_id、sender_admin_id、content、read_status |

### trade 子模块（15 张）

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| trade_order | 交易订单 | BaseDO | no、type、terminal、user_id、status、total_price、discount_price、delivery_price、adjust_price、pay_price、pay_order_id、delivery_type、receiver_area_id、pick_up_verify_code、refund_status |
| trade_order_item | 交易订单项 | BaseDO | order_id、spu_id、sku_id、price、count、use_point、after_sale_status |
| trade_order_log | 交易订单日志 | BaseDO | order_id、user_id、user_type、type、before_info、after_info |
| trade_cart | 购物车（仅 App 端） | BaseDO | user_id、spu_id、sku_id、count、selected |
| trade_after_sale | 售后订单 | BaseDO | no、order_id、order_item_id、way、type、refund_price、status |
| trade_after_sale_log | 售后日志 | BaseDO | after_sale_id、user_id、activity_type、content |
| trade_delivery_express | 快递公司 | BaseDO | code、name、sort、status |
| trade_delivery_express_template | 快递运费模板 | BaseDO | name、charge_mode、sort |
| trade_delivery_express_template_charge | 运费模板计费明细 | BaseDO | template_id、area_ids、start_count、start_price、extra_count、extra_price |
| trade_delivery_express_template_free | 运费模板包邮明细 | BaseDO | template_id、area_ids、free_count、free_price |
| trade_delivery_pick_up_store | 自提门店 | BaseDO | name、phone、latitude、longitude、status |
| trade_brokerage_user | 分销用户 | BaseDO | bind_user_id、brokerage_enabled、brokerage_price、frozen_price |
| trade_brokerage_record | 佣金记录 | BaseDO | user_id、biz_id、biz_type、price、total_price、frozen_days、source_user_id |
| trade_brokerage_withdraw | 佣金提现 | BaseDO | user_id、price、type、status、transfer_channel_code |
| trade_config | 交易配置 | BaseDO | after_sale_refund_reasons、delivery_pick_up_enabled、brokerage_enabled、brokerage_bind_mode、brokerage_first_percent、brokerage_withdraw_min_price |

### statistics 子模块（2 张）

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| trade_statistics | 交易统计（日汇总） | BaseDO | day、order_create_count、order_pay_count、pay_price、wallet_pay_price、after_sale_refund_price |
| product_statistics | 商品统计（日汇总） | BaseDO | day、spu_id、browse_count、order_count、pay_price |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|---------|------|
| 责任链 | `trade/service/price/calculator` 下 `TradePriceCalculator` 接口 + 10 个实现（TradeCouponPriceCalculator、TradeDiscountActivityPriceCalculator、TradeRewardActivityPriceCalculator、TradeSeckillActivityPriceCalculator、TradeCombinationActivityPriceCalculator、TradeBargainActivityPriceCalculator、TradePointUsePriceCalculator、TradePointGiveCalculator、TradeDeliveryPriceCalculator 等） | 下单价格计算按 `@Order` 顺序依次叠加各类优惠，`TradePriceServiceImpl` 汇总执行链 |
| 策略模式 | `trade/service/order/handler` 下 `TradeOrderHandler` 接口 + 9 个实现（TradeSeckillOrderHandler、TradeCombinationOrderHandler、TradeBargainOrderHandler、TradeCouponOrderHandler、TradePointOrderHandler、TradeMemberPointOrderHandler、TradeBrokerageOrderHandler、TradeProductSkuOrderHandler、TradeStatusSyncToWxaOrderHandler） | 订单创建与支付后的活动扩展逻辑按策略分发，`TradeOrderUpdateServiceImpl` 注入 `List<TradeOrderHandler>` 遍历调用 |
| 定时任务补偿 | 各子模块 `job/` 包（TradeOrderAutoCancelJob、TradeOrderAutoReceiveJob、TradeOrderAutoCommentJob、CouponExpireJob、CombinationRecordExpireJob、BrokerageRecordUnfreezeJob、ProductStatisticsJob、TradeStatisticsJob 等） | 订单超时关闭/自动收货、劵过期、拼团过期、佣金解冻、统计落库等异步补偿 |

## 依赖关系

- **上游**（本模块依赖）:
  - framework starters：`yudao-spring-boot-starter-web`、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-excel`、`yudao-spring-boot-starter-biz-tenant`、`yudao-spring-boot-starter-biz-ip`（trade/statistics）、`yudao-spring-boot-starter-redis`（trade）
  - 业务模块 API：
    - `system`：AdminUserApi、NotifyMessageSendApi、SocialClientApi（微信小程序发货信息录入/确认收货/订阅消息）
    - `member`：MemberUserApi、MemberAddressApi、MemberConfigApi、MemberLevelApi、MemberPointApi
    - `pay`：PayOrderApi、PayRefundApi（支付/退款发起），并接收 pay 的 PayNotifyJob 回调（售后退款、佣金提现转账）
    - `infra`：WebSocketSenderApi（客服消息推送）
- **下游**（依赖本模块）:
  - 无其他业务模块依赖 mall 的 Api（仓库内 grep 未发现外部消费方）；`yudao-server` 聚合打包全部子模块
  - mall 内部依赖方向：promotion → product、trade-api；trade → product、promotion、trade-api；statistics → product、promotion、trade-api

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|---------|------|--------|
| `cn.iocoder.yudao.module.trade.api.order.TradeOrderApi`（位于 yudao-module-trade-api） | getOrderList(ids)、getOrder(id)、cancelPaidOrder(userId, orderId, cancelType) | promotion 子模块（CombinationRecordServiceImpl 拼团失败取消订单、AppBargainRecordController 砍价订单查询） |
| `cn.iocoder.yudao.module.product.api.*`（ProductSpuApi、ProductSkuApi、ProductCategoryApi、ProductCommentApi） | 商品/分类/SKU/评价查询与更新库存 | mall 内部（trade、promotion、statistics） |
| `cn.iocoder.yudao.module.promotion.api.*`（CouponApi、SeckillActivityApi、BargainActivityApi、DiscountActivityApi、RewardActivityApi、PointActivityApi 等 10 个） | 活动校验与库存扣减、优惠劵使用/回收 | mall 内部（trade 价格计算链与订单 Handler） |

## 详细文档

- [api-spu.md](api-spu.md) - 商品 SPU 管理
- [api-brand.md](api-brand.md) - 商品品牌
- [api-category.md](api-category.md) - 商品分类
- [api-property.md](api-property.md) - 商品属性（属性项/属性值）
- [api-comment.md](api-comment.md) - 商品评价
- [api-favorite.md](api-favorite.md) - 商品收藏
- [api-history.md](api-history.md) - 商品浏览记录
- [api-coupon.md](api-coupon.md) - 优惠劵（模板/发放/回收）
- [api-seckill.md](api-seckill.md) - 秒杀（时段/活动）
- [api-combination.md](api-combination.md) - 拼团（活动/记录）
- [api-bargain.md](api-bargain.md) - 砍价（活动/记录/助力）
- [api-discount.md](api-discount.md) - 限时折扣活动
- [api-reward.md](api-reward.md) - 满减送活动
- [api-point.md](api-point.md) - 积分商城活动
- [api-diy.md](api-diy.md) - 装修模板与页面
- [api-article.md](api-article.md) - 文章与文章分类
- [api-banner.md](api-banner.md) - Banner 管理
- [api-kefu.md](api-kefu.md) - 客服（会话/消息）
- [api-trade-order.md](api-trade-order.md) - 交易订单
- [api-trade-aftersale.md](api-trade-aftersale.md) - 售后订单
- [api-trade-delivery.md](api-trade-delivery.md) - 配送（快递公司/运费模板/自提门店）
- [api-trade-brokerage.md](api-trade-brokerage.md) - 分销（用户/佣金/提现）
- [api-trade-config.md](api-trade-config.md) - 交易配置
- [api-statistics-trade.md](api-statistics-trade.md) - 交易统计
- [api-statistics-product.md](api-statistics-product.md) - 商品统计
- [api-statistics-member.md](api-statistics-member.md) - 会员统计
- [api-statistics-pay.md](api-statistics-pay.md) - 支付统计
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
