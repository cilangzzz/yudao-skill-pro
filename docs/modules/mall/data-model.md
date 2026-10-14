# 数据模型详情

> mall 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

mall 为多子模块布局：`yudao-module-product`（商品）、`yudao-module-promotion`（营销）、`yudao-module-trade`（交易）、`yudao-module-statistics`（统计）四个业务子模块 + `yudao-module-trade-api`（纯 API 包，无 DO）。Java 包根分别为 `cn.iocoder.yudao.module.{product|promotion|trade|statistics}`，共 49 个数据表。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO（抽象基类，实现 Serializable / TransPojo）
│   creator      String          创建者（用户编号，INSERT 时自动填充）
│   createTime   LocalDateTime   创建时间（INSERT 时自动填充）
│   updater      String          更新者（用户编号，INSERT_UPDATE 时自动填充）
│   updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 时自动填充）
│   deleted      Boolean         是否删除（@TableLogic 逻辑删除）
│
└── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO（多租户扩展基类）
        tenantId  Long            多租户编号
```

**使用规则**：

- mall 模块全部 49 个 DO 均**直接继承 `BaseDO`**，未使用 `TenantBaseDO`，即 mall 的表未启用租户隔离（商城数据全局共享，靠会员 userId 区分归属）。
- `BaseDO` 的 5 个通用字段由 MyBatis-Plus 字段自动填充 + `@TableLogic` 提供，各表 DDL 中均需包含 `creator/create_time/updater/update_time/deleted` 列。
- 绝大多数含 JSON 字段的表在 `@TableName` 上声明了 `autoResultMap = true`，配合 `JacksonTypeHandler` / `LongListTypeHandler` / `IntegerListTypeHandler` / `StringListTypeHandler` 做集合字段映射。
- 各表主键均为 `id BIGINT` 自增（`@TableId`），并通过 `@KeySequence("xxx_seq")` 兼容 Oracle/PostgreSQL 等数据库的序列自增。

## 2. 核心 DO 实体

> 仓库内不含 mall 模块的建表 DDL 文件，以下索引信息仅包含代码可直接确认的部分（主键、业务唯一语义），未在代码中声明的唯一索引不做推测。所有表主键均为 `id` 自增，下文不再重复。

### 2.1 商品中心聚合（product 子模块）

#### ProductSpuDO（product_spu）

商品 SPU（标准产品单元），商品中心的核心聚合根，被全部营销活动、交易订单、统计数据引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 商品 SPU 编号，主键自增 |
| name | String | name | 商品名称 |
| keyword | String | keyword | 关键字（搜索） |
| introduction | String | introduction | 商品简介 |
| description | String | description | 商品详情（富文本） |
| categoryId | Long | category_id | 商品分类编号，关联 ProductCategoryDO.id |
| brandId | Long | brand_id | 商品品牌编号，关联 ProductBrandDO.id |
| picUrl | String | pic_url | 商品封面图 |
| sliderPicUrls | List&lt;String&gt; | slider_pic_urls | 商品轮播图（JSON，JacksonTypeHandler） |
| sort | Integer | sort | 排序 |
| status | Integer | status | 商品状态，枚举 ProductSpuStatusEnum |
| specType | Boolean | spec_type | 规格类型：false 单规格 / true 多规格 |
| price | Integer | price | 商品价格（分），取最低价 SKU 的 price |
| marketPrice | Integer | market_price | 市场价（分），取最低价 SKU 的 marketPrice |
| costPrice | Integer | cost_price | 成本价（分），取最低价 SKU 的 costPrice |
| stock | Integer | stock | 库存，为各 SKU stock 求和 |
| deliveryTypes | List&lt;Integer&gt; | delivery_types | 配送方式数组（JSON，IntegerListTypeHandler），对应 DeliveryTypeEnum |
| deliveryTemplateId | Long | delivery_template_id | 运费模板编号，关联 DeliveryExpressTemplateDO.id |
| giveIntegral | Integer | give_integral | 赠送积分 |
| subCommissionType | Boolean | sub_commission_type | 分销类型：false 默认 / true 自行设置 |
| salesCount | Integer | sales_count | 商品销量 |
| virtualSalesCount | Integer | virtual_sales_count | 虚拟销量 |
| browseCount | Integer | browse_count | 浏览量 |

**继承**: BaseDO
**索引**: 主键 id；代码中未声明其他唯一索引（categoryId、brandId、deliveryTemplateId 为逻辑外键）。

#### ProductSkuDO（product_sku）

商品 SKU（库存量单元），SPU 的子实体，承载价格、库存、规格组合与分销佣金。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | SKU 编号，主键自增 |
| spuId | Long | spu_id | SPU 编号，关联 ProductSpuDO.id |
| properties | List&lt;Property&gt; | properties | 规格属性数组（JSON，JacksonTypeHandler），内嵌 propertyId/propertyName/valueId/valueName |
| price | Integer | price | 商品价格（分） |
| marketPrice | Integer | market_price | 市场价（分） |
| costPrice | Integer | cost_price | 成本价（分） |
| barCode | String | bar_code | 商品条码 |
| picUrl | String | pic_url | 图片地址 |
| stock | Integer | stock | 库存 |
| weight | Double | weight | 商品重量（kg） |
| volume | Double | volume | 商品体积（m³） |
| firstBrokeragePrice | Integer | first_brokerage_price | 一级分销佣金（分） |
| secondBrokeragePrice | Integer | second_brokerage_price | 二级分销佣金（分） |
| salesCount | Integer | sales_count | 商品销量 |

**继承**: BaseDO
**索引**: 主键 id；spu_id 为从属查询列（逻辑外键）。内嵌类 `Property` 冗余属性名/属性值名，属性改名时需同步更新。

#### ProductCategoryDO（product_category）

商品分类，两层树形结构（常量 `CATEGORY_LEVEL = 2` 限定层级）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分类编号，主键自增 |
| parentId | Long | parent_id | 父分类编号，根分类为 0（PARENT_ID_NULL） |
| name | String | name | 分类名称 |
| picUrl | String | pic_url | 移动端分类图（建议 180×180） |
| sort | Integer | sort | 分类排序 |
| status | Integer | status | 开启状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；parent_id 支撑树形查询。

#### ProductBrandDO（product_brand）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 品牌编号，主键自增 |
| name | String | name | 品牌名称 |
| picUrl | String | pic_url | 品牌图片 |
| sort | Integer | sort | 品牌排序 |
| description | String | description | 品牌描述 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id。

#### ProductPropertyDO（product_property）

商品属性项（如"颜色"），单规格 SPU 使用 id=0 的默认属性（`ID_DEFAULT`）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键自增 |
| name | String | name | 属性名称 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id。

#### ProductPropertyValueDO（product_property_value）

商品属性值（如"红色"），从属于属性项。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 主键自增 |
| propertyId | Long | property_id | 属性项编号，关联 ProductPropertyDO.id |
| name | String | name | 属性值名称 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；property_id 为从属查询列。

#### ProductCommentDO（product_comment）

商品评论，同时冗余订单、SKU、用户信息，减少关联查询。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 评论编号，主键自增 |
| userId | Long | user_id | 评价人用户编号，关联 MemberUserDO.id |
| userNickname | String | user_nickname | 评价人名称（匿名时为"匿名用户"） |
| userAvatar | String | user_avatar | 评价人头像 |
| anonymous | Boolean | anonymous | 是否匿名 |
| orderId | Long | order_id | 交易订单编号，关联 TradeOrderDO.id |
| orderItemId | Long | order_item_id | 交易订单项编号，关联 TradeOrderItemDO.id |
| spuId | Long | spu_id | 商品 SPU 编号，关联 ProductSpuDO.id |
| spuName | String | spu_name | 商品 SPU 名称（冗余） |
| skuId | Long | sku_id | 商品 SKU 编号，关联 ProductSkuDO.id |
| skuPicUrl | String | sku_pic_url | SKU 图片地址（冗余） |
| skuProperties | List&lt;ProductSkuDO.Property&gt; | sku_properties | SKU 规格属性数组（JSON 冗余） |
| visible | Boolean | visible | 是否可见（商家可隐藏） |
| scores | Integer | scores | 评分星级（1-5） |
| descriptionScores | Integer | description_scores | 描述星级（1-5） |
| benefitScores | Integer | benefit_scores | 服务星级（1-5） |
| content | String | content | 评论内容 |
| picUrls | List&lt;String&gt; | pic_urls | 评论图片地址数组（JSON） |
| replyStatus | Boolean | reply_status | 商家是否回复 |
| replyUserId | Long | reply_user_id | 回复管理员编号，关联 AdminUserDO.id |
| replyContent | String | reply_content | 商家回复内容 |
| replyTime | LocalDateTime | reply_time | 商家回复时间 |

**继承**: BaseDO
**索引**: 主键 id；spu_id（商品维度评论列表）、user_id（我的评价）为核心查询列。

#### ProductFavoriteDO（product_favorite）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| spuId | Long | spu_id | 商品 SPU 编号，关联 ProductSpuDO.id |

**继承**: BaseDO
**索引**: 主键 id；user_id + spu_id 组合在业务上唯一（Mapper 提供 `selectByUserIdAndSpuId` 单条查询，收藏防重复）。

#### ProductBrowseHistoryDO（product_browse_history）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 记录编号，主键自增 |
| spuId | Long | spu_id | 商品 SPU 编号 |
| userId | Long | user_id | 用户编号 |
| userDeleted | Boolean | user_deleted | 用户侧是否删除（业务删除标记，区别于逻辑删除） |

**继承**: BaseDO
**索引**: 主键 id；user_id、spu_id 为核心查询列。

### 2.2 交易订单聚合（trade 子模块）

#### TradeOrderDO（trade_order）

交易订单主表，商城交易域的聚合根，字段按「基本信息 / 价格支付 / 收件物流 / 售后 / 营销」分组，并直接冗余各类营销活动编号。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 订单编号，主键自增 |
| no | String | no | 订单流水号 |
| type | Integer | type | 订单类型，枚举 TradeOrderTypeEnum |
| terminal | Integer | terminal | 订单来源终端，枚举 TerminalEnum |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| userIp | String | user_ip | 用户 IP |
| userRemark | String | user_remark | 用户备注 |
| status | Integer | status | 订单状态，枚举 TradeOrderStatusEnum |
| productCount | Integer | product_count | 购买的商品数量 |
| finishTime | LocalDateTime | finish_time | 订单完成时间 |
| cancelTime | LocalDateTime | cancel_time | 订单取消时间 |
| cancelType | Integer | cancel_type | 取消类型，枚举 TradeOrderCancelTypeEnum |
| remark | String | remark | 商家备注 |
| commentStatus | Boolean | comment_status | 是否评价 |
| brokerageUserId | Long | brokerage_user_id | 推广人编号，关联 BrokerageUserDO.id |
| payOrderId | Long | pay_order_id | 支付订单编号，对接 pay 模块 PayOrderDO.id |
| payStatus | Boolean | pay_status | 是否已支付 |
| payTime | LocalDateTime | pay_time | 付款时间 |
| payChannelCode | String | pay_channel_code | 支付渠道，对应 PayChannelEnum |
| totalPrice | Integer | total_price | 商品原价（分），各订单项 price×count 求和 |
| discountPrice | Integer | discount_price | 优惠金额（分） |
| deliveryPrice | Integer | delivery_price | 运费金额（分） |
| adjustPrice | Integer | adjust_price | 订单调价（分），正加负减 |
| payPrice | Integer | pay_price | 应付金额（分）= totalPrice − couponPrice − pointPrice − discountPrice + deliveryPrice + adjustPrice − vipPrice |
| deliveryType | Integer | delivery_type | 配送方式，枚举 DeliveryTypeEnum |
| logisticsId | Long | logistics_id | 发货物流公司编号，关联 DeliveryExpressDO.id；无需发货时为 0 |
| logisticsNo | String | logistics_no | 发货物流单号；无需发货时为空串 |
| deliveryTime | LocalDateTime | delivery_time | 发货时间 |
| receiveTime | LocalDateTime | receive_time | 收货时间 |
| receiverName | String | receiver_name | 收件人名称 |
| receiverMobile | String | receiver_mobile | 收件人手机 |
| receiverAreaId | Integer | receiver_area_id | 收件人地区编号 |
| receiverDetailAddress | String | receiver_detail_address | 收件人详细地址 |
| pickUpStoreId | Long | pick_up_store_id | 自提门店编号，关联 DeliveryPickUpStoreDO.id |
| pickUpVerifyCode | String | pick_up_verify_code | 自提核销码 |
| refundStatus | Integer | refund_status | 售后状态，枚举 TradeOrderRefundStatusEnum |
| refundPrice | Integer | refund_price | 退款金额（分），实际收入 = payPrice − refundPrice |
| couponId | Long | coupon_id | 优惠券编号，关联 CouponDO.id |
| couponPrice | Integer | coupon_price | 优惠券减免金额（分） |
| usePoint | Integer | use_point | 使用的积分 |
| pointPrice | Integer | point_price | 积分抵扣金额（分） |
| givePoint | Integer | give_point | 赠送的积分 |
| refundPoint | Integer | refund_point | 退还的使用积分 |
| vipPrice | Integer | vip_price | VIP 减免金额（分） |
| giveCouponTemplateCounts | Map&lt;Long,Integer&gt; | give_coupon_template_counts | 赠送的优惠券（模板编号→数量，JSON） |
| giveCouponIds | List&lt;Long&gt; | give_coupon_ids | 赠送的优惠券编号数组（JSON，用于取消/售后时扣减） |
| seckillActivityId | Long | seckill_activity_id | 秒杀活动编号，关联 SeckillActivityDO.id |
| bargainActivityId | Long | bargain_activity_id | 砍价活动编号，关联 BargainActivityDO.id |
| bargainRecordId | Long | bargain_record_id | 砍价记录编号，关联 BargainRecordDO.id |
| combinationActivityId | Long | combination_activity_id | 拼团活动编号，关联 CombinationActivityDO.id |
| combinationHeadId | Long | combination_head_id | 拼团团长编号，关联 CombinationRecordDO.headId |
| combinationRecordId | Long | combination_record_id | 拼团记录编号，关联 CombinationRecordDO.id |
| pointActivityId | Long | point_activity_id | 积分商城活动编号，关联 PointActivityDO.id |

**继承**: BaseDO
**索引**: 主键 id；user_id（我的订单）、status + 状态流转列为核心查询列；各营销活动编号列为活动→订单的回溯查询列。

#### TradeOrderItemDO（trade_order_item）

交易订单项（订单明细），一个订单包含多个订单项，大量冗余商品快照字段。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| orderId | Long | order_id | 订单编号，关联 TradeOrderDO.id |
| cartId | Long | cart_id | 购物车项编号，关联 CartDO.id |
| spuId | Long | spu_id | 商品 SPU 编号 |
| spuName | String | spu_name | 商品 SPU 名称（冗余快照） |
| skuId | Long | sku_id | 商品 SKU 编号，关联 ProductSkuDO.id |
| properties | List&lt;Property&gt; | properties | 规格属性数组（JSON 快照，结构同 ProductSkuDO.Property） |
| picUrl | String | pic_url | 商品图片（快照） |
| count | Integer | count | 购买数量 |
| commentStatus | Boolean | comment_status | 是否评价 |
| price | Integer | price | 商品原价（单，分），对应下单时 ProductSkuDO.price |
| discountPrice | Integer | discount_price | 优惠金额（总，分） |
| deliveryPrice | Integer | delivery_price | 运费金额（总，分） |
| adjustPrice | Integer | adjust_price | 订单调价（总，分） |
| payPrice | Integer | pay_price | 应付金额（总，分） |
| couponPrice | Integer | coupon_price | 优惠券减免金额（分） |
| pointPrice | Integer | point_price | 积分抵扣金额（分） |
| usePoint | Integer | use_point | 使用的积分 |
| givePoint | Integer | give_point | 赠送的积分 |
| vipPrice | Integer | vip_price | VIP 减免金额（分） |
| afterSaleId | Long | after_sale_id | 售后单编号，关联 AfterSaleDO.id |
| afterSaleStatus | Integer | after_sale_status | 售后状态，枚举 TradeOrderItemAfterSaleStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；order_id（订单→订单项）、sku_id/spu_id（商品销量回溯）为核心查询列。

#### TradeOrderLogDO（trade_order_log）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 操作用户编号（AdminUserDO 或 MemberUserDO 的 id；系统操作时为 0） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum（系统操作为 0） |
| orderId | Long | order_id | 订单编号，关联 TradeOrderDO.id |
| beforeStatus | Integer | before_status | 操作前状态 |
| afterStatus | Integer | after_status | 操作后状态 |
| operateType | Integer | operate_type | 操作类型，枚举 TradeOrderOperateTypeEnum |
| content | String | content | 订单日志信息 |

**继承**: BaseDO
**索引**: 主键 id；order_id 为核心查询列（订单操作轨迹）。

#### CartDO（trade_cart）

购物车项，仅 App 端使用（无 admin Controller）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，自增 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| spuId | Long | spu_id | 商品 SPU 编号，关联 ProductSpuDO.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 ProductSkuDO.id |
| count | Integer | count | 商品购买数量 |
| selected | Boolean | selected | 是否选中 |

**继承**: BaseDO
**索引**: 主键 id；user_id + sku_id 定位唯一购物车项。

#### AfterSaleDO（trade_after_sale）

售后订单，处理交易订单的退款/退货流程。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 售后编号，主键自增 |
| no | String | no | 售后单号 |
| status | Integer | status | 退款状态，枚举 AfterSaleStatusEnum |
| way | Integer | way | 售后方式，枚举 AfterSaleWayEnum（仅退款/退货退款） |
| type | Integer | type | 售后类型，枚举 AfterSaleTypeEnum |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| applyReason | String | apply_reason | 申请原因 |
| applyDescription | String | apply_description | 补充描述 |
| applyPicUrls | List&lt;String&gt; | apply_pic_urls | 补充凭证图片（JSON 数组） |
| orderId | Long | order_id | 交易订单编号，关联 TradeOrderDO.id |
| orderNo | String | order_no | 订单流水号（冗余） |
| orderItemId | Long | order_item_id | 交易订单项编号，关联 TradeOrderItemDO.id |
| spuId | Long | spu_id | 商品 SPU 编号（冗余订单项） |
| spuName | String | spu_name | 商品 SPU 名称（冗余订单项） |
| skuId | Long | sku_id | 商品 SKU 编号（冗余订单项） |
| properties | List&lt;TradeOrderItemDO.Property&gt; | properties | 规格属性数组（JSON 快照） |
| picUrl | String | pic_url | 商品图片（冗余订单项） |
| count | Integer | count | 退货商品数量 |
| auditTime | LocalDateTime | audit_time | 审批时间 |
| auditUserId | Long | audit_user_id | 审批人，关联 AdminUserDO.id |
| auditReason | String | audit_reason | 审批备注（仅审批不通过填写） |
| refundPrice | Integer | refund_price | 退款金额（分） |
| payRefundId | Long | pay_refund_id | 支付退款编号，对接 pay 模块 PayRefundDO.id |
| refundTime | LocalDateTime | refund_time | 退款时间 |
| logisticsId | Long | logistics_id | 退货物流公司编号 |
| logisticsNo | String | logistics_no | 退货物流单号 |
| deliveryTime | LocalDateTime | delivery_time | 退货时间 |
| receiveTime | LocalDateTime | receive_time | 收货时间 |
| receiveReason | String | receive_reason | 收货备注（仅拒绝收货填写） |

**继承**: BaseDO
**索引**: 主键 id；order_id / order_item_id、user_id 为核心查询列。

#### AfterSaleLogDO（trade_after_sale_log）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 操作用户编号（AdminUserDO 或 MemberUserDO） |
| userType | Integer | user_type | 用户类型，枚举 UserTypeEnum |
| afterSaleId | Long | after_sale_id | 售后编号，关联 AfterSaleDO.id |
| beforeStatus | Integer | before_status | 操作前状态 |
| afterStatus | Integer | after_status | 操作后状态 |
| operateType | Integer | operate_type | 操作类型，枚举 AfterSaleOperateTypeEnum |
| content | String | content | 操作明细 |

**继承**: BaseDO
**索引**: 主键 id；after_sale_id 为核心查询列（售后操作轨迹）。

#### DeliveryExpressDO（trade_delivery_express）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| code | String | code | 快递公司编码 |
| name | String | name | 快递公司名称 |
| logo | String | logo | 快递公司 logo |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；code 业务上唯一（对接三方物流的编码）。

#### DeliveryExpressTemplateDO（trade_delivery_express_template）

快递运费模板主表，被 ProductSpuDO.deliveryTemplateId 引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 模板名称 |
| chargeMode | Integer | charge_mode | 配送计费方式，枚举 DeliveryExpressChargeModeEnum（按件/按重/按体积） |
| sort | Integer | sort | 排序 |

**继承**: BaseDO
**索引**: 主键 id。

#### DeliveryExpressTemplateChargeDO（trade_delivery_express_template_charge）

运费模板计费配置，一个模板按区域配置多条计费规则。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| templateId | Long | template_id | 配送模板编号，关联 DeliveryExpressTemplateDO.id |
| areaIds | List&lt;Integer&gt; | area_ids | 配送区域编号列表（JSON，IntegerListTypeHandler） |
| chargeMode | Integer | charge_mode | 配送计费方式（冗余模板） |
| startCount | Double | start_count | 首件数量（件数/重量/体积） |
| startPrice | Integer | start_price | 起步价（分） |
| extraCount | Double | extra_count | 续件数量 |
| extraPrice | Integer | extra_price | 续件额外价（分） |

**继承**: BaseDO
**索引**: 主键 id；template_id 为从属查询列。

#### DeliveryExpressTemplateFreeDO（trade_delivery_express_template_free）

运费模板包邮配置。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| templateId | Long | template_id | 配送模板编号，关联 DeliveryExpressTemplateDO.id |
| areaIds | List&lt;Integer&gt; | area_ids | 包邮区域编号列表（JSON） |
| freePrice | Integer | free_price | 包邮金额（分），订单总金额 ≥ 该值免运费 |
| freeCount | Integer | free_count | 包邮件数，订单总件数 ≥ 该值免运费 |

**继承**: BaseDO
**索引**: 主键 id；template_id 为从属查询列。

#### DeliveryPickUpStoreDO（trade_delivery_pick_up_store）

自提门店，被 TradeOrderDO.pickUpStoreId 引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 门店名称 |
| introduction | String | introduction | 门店简介 |
| phone | String | phone | 门店手机 |
| areaId | Integer | area_id | 区域编号 |
| detailAddress | String | detail_address | 门店详细地址 |
| logo | String | logo | 门店 logo |
| openingTime | LocalTime | opening_time | 营业开始时间 |
| closingTime | LocalTime | closing_time | 营业结束时间 |
| latitude | Double | latitude | 纬度 |
| longitude | Double | longitude | 经度 |
| verifyUserIds | List&lt;Long&gt; | verify_user_ids | 核销员工编号数组（JSON，关联 AdminUserDO.id） |
| status | Integer | status | 门店状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id。

#### BrokerageUserDO（trade_brokerage_user）

分销用户，主键直接复用会员用户编号，与 MemberUserDO 一对一。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 用户编号，即 MemberUserDO.id（主键，非自增语义） |
| bindUserId | Long | bind_user_id | 推广员编号，关联 MemberUserDO.id（上级） |
| bindUserTime | LocalDateTime | bind_user_time | 推广员绑定时间 |
| brokerageEnabled | Boolean | brokerage_enabled | 是否有分销资格 |
| brokerageTime | LocalDateTime | brokerage_time | 成为分销员时间 |
| brokeragePrice | Integer | brokerage_price | 可用佣金（分） |
| frozenPrice | Integer | frozen_price | 冻结佣金（分） |

**继承**: BaseDO
**索引**: 主键 id（即会员编号）；bind_user_id 支撑下级推广员列表查询。

#### BrokerageRecordDO（trade_brokerage_record）

佣金记录，记录每一笔佣金的产生与结算。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id（获得佣金的分销员） |
| bizId | String | biz_id | 业务编号（如订单号） |
| bizType | Integer | biz_type | 业务类型，枚举 BrokerageRecordBizTypeEnum |
| title | String | title | 标题 |
| description | String | description | 说明 |
| price | Integer | price | 佣金金额（分） |
| totalPrice | Integer | total_price | 当前总佣金（分，快照） |
| status | Integer | status | 状态，枚举 BrokerageRecordStatusEnum（待结算/已结算/已取消） |
| frozenDays | Integer | frozen_days | 冻结时间（天） |
| unfreezeTime | LocalDateTime | unfreeze_time | 解冻时间 |
| sourceUserLevel | Integer | source_user_level | 来源用户等级（被推广人与 userId 的推广层级，1/2 级） |
| sourceUserId | Long | source_user_id | 来源用户编号，关联 MemberUserDO.id（被推广用户） |

**继承**: BaseDO
**索引**: 主键 id；user_id（我的佣金）、biz_id + biz_type（业务回溯）为核心查询列。

#### BrokerageWithdrawDO（trade_brokerage_withdraw）

佣金提现单，审核通过后对接 pay 模块转账。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| price | Integer | price | 提现金额（分） |
| feePrice | Integer | fee_price | 提现手续费（分） |
| totalPrice | Integer | total_price | 当前总佣金（分，快照） |
| type | Integer | type | 提现类型，枚举 BrokerageWithdrawTypeEnum（银行/微信/支付宝等） |
| userName | String | user_name | 提现姓名（银行开户人/微信真名/支付宝真名） |
| userAccount | String | user_account | 提现账号（银行账号/微信 openid/支付宝账号） |
| qrCodeUrl | String | qr_code_url | 收款码 |
| bankName | String | bank_name | 银行名称 |
| bankAddress | String | bank_address | 开户地址 |
| status | Integer | status | 状态，枚举 BrokerageWithdrawStatusEnum（审核中/通过/驳回） |
| auditReason | String | audit_reason | 审核驳回原因 |
| auditTime | LocalDateTime | audit_time | 审核时间 |
| remark | String | remark | 备注 |
| payTransferId | Long | pay_transfer_id | 转账单编号，关联 pay 模块 PayTransferRespDTO.id |
| transferChannelCode | String | transfer_channel_code | 转账渠道，枚举 PayChannelEnum |
| transferTime | LocalDateTime | transfer_time | 转账成功时间 |
| transferErrorMsg | String | transfer_error_msg | 转账错误提示 |

**继承**: BaseDO
**索引**: 主键 id；user_id 为核心查询列。

#### TradeConfigDO（trade_config）

交易中心配置（单行配置表），承载售后理由、配送开关、分销规则等全局配置。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 自增主键 |
| afterSaleRefundReasons | List&lt;String&gt; | after_sale_refund_reasons | 售后退款理由（JSON 数组） |
| afterSaleReturnReasons | List&lt;String&gt; | after_sale_return_reasons | 售后退货理由（JSON 数组） |
| deliveryExpressFreeEnabled | Boolean | delivery_express_free_enabled | 是否启用全场包邮 |
| deliveryExpressFreePrice | Integer | delivery_express_free_price | 全场包邮最小金额（分） |
| deliveryPickUpEnabled | Boolean | delivery_pick_up_enabled | 是否开启自提 |
| brokerageEnabled | Boolean | brokerage_enabled | 是否启用分佣 |
| brokerageEnabledCondition | Integer | brokerage_enabled_condition | 分佣模式，枚举 BrokerageEnabledConditionEnum |
| brokerageBindMode | Integer | brokerage_bind_mode | 分销关系绑定模式，枚举 BrokerageBindModeEnum |
| brokeragePosterUrls | List&lt;String&gt; | brokerage_poster_urls | 分销海报图地址数组（JSON） |
| brokerageFirstPercent | Integer | brokerage_first_percent | 一级返佣比例 |
| brokerageSecondPercent | Integer | brokerage_second_percent | 二级返佣比例 |
| brokerageWithdrawMinPrice | Integer | brokerage_withdraw_min_price | 用户提现最低金额（分） |
| brokerageWithdrawFeePercent | Integer | brokerage_withdraw_fee_percent | 提现手续费百分比 |
| brokerageFrozenDays | Integer | brokerage_frozen_days | 佣金冻结时间（天） |
| brokerageWithdrawTypes | List&lt;Integer&gt; | brokerage_withdraw_types | 提现方式数组（JSON，枚举 BrokerageWithdrawTypeEnum） |

**继承**: BaseDO
**索引**: 主键 id。

### 2.3 营销促销聚合（promotion 子模块）

#### CouponTemplateDO（promotion_coupon_template）

优惠券模板，用户领取时生成 CouponDO。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 模板编号，主键自增 |
| name | String | name | 优惠券名 |
| description | String | description | 优惠券说明 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| totalCount | Integer | total_count | 发放数量（-1 不限制） |
| takeLimitCount | Integer | take_limit_count | 每人限领个数（-1 不限制） |
| takeType | Integer | take_type | 领取方式，枚举 CouponTakeTypeEnum（直接领取/指定发放/新人券） |
| usePrice | Integer | use_price | 满多少金额可用（分，0 不限制） |
| productScope | Integer | product_scope | 商品范围，枚举 PromotionProductScopeEnum（全部/指定分类/指定商品） |
| productScopeValues | List&lt;Long&gt; | product_scope_values | 商品范围编号数组（JSON，LongListTypeHandler） |
| validityType | Integer | validity_type | 生效日期类型，枚举 CouponTemplateValidityTypeEnum（固定日期/领取后 N 天） |
| validStartTime | LocalDateTime | valid_start_time | 固定日期 - 生效开始时间 |
| validEndTime | LocalDateTime | valid_end_time | 固定日期 - 生效结束时间 |
| fixedStartTerm | Integer | fixed_start_term | 领取后第 N 天开始生效 |
| fixedEndTerm | Integer | fixed_end_term | 领取后第 N 天结束生效 |
| discountType | Integer | discount_type | 折扣类型，枚举 PromotionDiscountTypeEnum（满减/折扣） |
| discountPercent | Integer | discount_percent | 折扣百分比（80 表示 8 折） |
| discountPrice | Integer | discount_price | 优惠金额（分），discountType=PRICE 时生效 |
| discountLimitPrice | Integer | discount_limit_price | 折扣上限（分），discountType=PERCENT 时生效 |
| takeCount | Integer | take_count | 已领取数量 |
| useCount | Integer | use_count | 已使用次数 |

**继承**: BaseDO
**索引**: 主键 id。

#### CouponDO（promotion_coupon）

用户持有的优惠券，冗余模板的使用规则与优惠信息。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 优惠券编号，主键自增 |
| templateId | Long | template_id | 优惠券模板编号，关联 CouponTemplateDO.id |
| name | String | name | 优惠券名（冗余模板） |
| status | Integer | status | 状态，枚举 CouponStatusEnum（未使用/已使用/已过期/已作废） |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| takeType | Integer | take_type | 领取类型，枚举 CouponTakeTypeEnum |
| usePrice | Integer | use_price | 满多少金额可用（分，冗余模板） |
| validStartTime | LocalDateTime | valid_start_time | 生效开始时间 |
| validEndTime | LocalDateTime | valid_end_time | 生效结束时间 |
| productScope | Integer | product_scope | 商品范围，枚举 PromotionProductScopeEnum（冗余模板） |
| productScopeValues | List&lt;Long&gt; | product_scope_values | 商品范围编号数组（JSON，冗余模板） |
| discountType | Integer | discount_type | 折扣类型（冗余模板） |
| discountPercent | Integer | discount_percent | 折扣百分比（冗余模板） |
| discountPrice | Integer | discount_price | 优惠金额（分，冗余模板） |
| discountLimitPrice | Integer | discount_limit_price | 折扣上限（分，冗余模板） |
| useOrderId | Long | use_order_id | 使用订单号（关联 TradeOrderDO.id） |
| useTime | LocalDateTime | use_time | 使用时间 |

**继承**: BaseDO
**索引**: 主键 id；user_id + status（我的优惠券）、template_id（领取统计）为核心查询列。

#### SeckillConfigDO（promotion_seckill_config）

秒杀时段配置（如 10:00-12:00 场次）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| name | String | name | 秒杀时段名称 |
| startTime | String | start_time | 开始时间点 |
| endTime | String | end_time | 结束时间点 |
| sliderPicUrls | List&lt;String&gt; | slider_pic_urls | 秒杀轮播图（JSON 数组） |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id。

#### SeckillActivityDO（promotion_seckill_activity）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 秒杀活动编号，主键自增 |
| spuId | Long | spu_id | 秒杀活动商品 SPU 编号，关联 ProductSpuDO.id |
| name | String | name | 秒杀活动名称 |
| status | Integer | status | 活动状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |
| startTime | LocalDateTime | start_time | 活动开始时间 |
| endTime | LocalDateTime | end_time | 活动结束时间 |
| sort | Integer | sort | 排序 |
| configIds | List&lt;Long&gt; | config_ids | 秒杀时段编号数组（JSON，关联 SeckillConfigDO.id） |
| totalLimitCount | Integer | total_limit_count | 总限购数量 |
| singleLimitCount | Integer | single_limit_count | 单次限购数量 |
| stock | Integer | stock | 秒杀剩余库存（秒杀时扣减） |
| totalStock | Integer | total_stock | 秒杀总库存 |

**继承**: BaseDO
**索引**: 主键 id；spu_id 为关联查询列。

#### SeckillProductDO（promotion_seckill_product）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| activityId | Long | activity_id | 秒杀活动编号，关联 SeckillActivityDO.id |
| configIds | List&lt;Long&gt; | config_ids | 秒杀时段编号数组（JSON，关联 SeckillConfigDO.id） |
| spuId | Long | spu_id | 商品 SPU 编号 |
| skuId | Long | sku_id | 商品 SKU 编号 |
| seckillPrice | Integer | seckill_price | 秒杀金额（分） |
| stock | Integer | stock | 秒杀库存 |
| activityStatus | Integer | activity_status | 秒杀商品状态，枚举 CommonStatusEnum（冗余活动） |
| activityStartTime | LocalDateTime | activity_start_time | 活动开始时间（冗余） |
| activityEndTime | LocalDateTime | activity_end_time | 活动结束时间（冗余） |

**继承**: BaseDO
**索引**: 主键 id；activity_id、sku_id 为核心查询列（秒杀下单按 SKU 定位）。

#### CombinationActivityDO（promotion_combination_activity）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 活动编号，主键自增 |
| name | String | name | 拼团名称 |
| spuId | Long | spu_id | 商品 SPU 编号，关联 ProductSpuDO.id |
| totalLimitCount | Integer | total_limit_count | 总限购数量 |
| singleLimitCount | Integer | single_limit_count | 单次限购数量 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| userSize | Integer | user_size | 几人团 |
| virtualGroup | Boolean | virtual_group | 是否虚拟成团 |
| status | Integer | status | 活动状态，枚举 CommonStatusEnum |
| limitDuration | Integer | limit_duration | 限制时长（小时），开团后成团有效期 |

**继承**: BaseDO
**索引**: 主键 id。

#### CombinationProductDO（promotion_combination_product）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| activityId | Long | activity_id | 拼团活动编号，关联 CombinationActivityDO.id |
| spuId | Long | spu_id | 商品 SPU 编号 |
| skuId | Long | sku_id | 商品 SKU 编号 |
| combinationPrice | Integer | combination_price | 拼团价格（分） |
| activityStatus | Integer | activity_status | 拼团商品状态（冗余活动） |
| activityStartTime | LocalDateTime | activity_start_time | 活动开始时间（冗余） |
| activityEndTime | LocalDateTime | activity_end_time | 活动结束时间（冗余） |

**继承**: BaseDO
**索引**: 主键 id；activity_id、sku_id 为核心查询列。

#### CombinationRecordDO（promotion_combination_record）

拼团记录，用户参与拼团时创建；团长记录与参团人记录通过 headId 关联。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| activityId | Long | activity_id | 拼团活动编号，关联 CombinationActivityDO.id |
| combinationPrice | Integer | combination_price | 拼团商品单价（分，冗余 CombinationProductDO） |
| spuId | Long | spu_id | SPU 编号 |
| spuName | String | spu_name | 商品名字（快照） |
| picUrl | String | pic_url | 商品图片（快照） |
| skuId | Long | sku_id | SKU 编号 |
| count | Integer | count | 购买数量 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id |
| nickname | String | nickname | 用户昵称（快照） |
| avatar | String | avatar | 用户头像（快照） |
| headId | Long | head_id | 团长编号，关联 CombinationRecordDO.id；团长本人为 0（HEAD_ID_GROUP） |
| status | Integer | status | 开团状态，枚举 CombinationRecordStatusEnum |
| orderId | Long | order_id | 订单编号，关联 TradeOrderDO.id |
| userSize | Integer | user_size | 开团需要人数（冗余活动） |
| userCount | Integer | user_count | 已加入拼团人数 |
| virtualGroup | Boolean | virtual_group | 是否虚拟成团（过期未成团且活动允许时由 Job 置 true） |
| expireTime | LocalDateTime | expire_time | 过期时间 = startTime + 活动限制时长 |
| startTime | LocalDateTime | start_time | 开始时间（订单付款后） |
| endTime | LocalDateTime | end_time | 结束时间（成团/失败时间） |

**继承**: BaseDO
**索引**: 主键 id；head_id + status（团成员列表）、user_id + activity_id（我参与的拼团）为核心查询列。

#### BargainActivityDO（promotion_bargain_activity）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 活动编号，主键自增 |
| name | String | name | 砍价活动名称 |
| startTime | LocalDateTime | start_time | 活动开始时间 |
| endTime | LocalDateTime | end_time | 活动结束时间 |
| status | Integer | status | 活动状态，枚举 CommonStatusEnum |
| spuId | Long | spu_id | 商品 SPU 编号 |
| skuId | Long | sku_id | 商品 SKU 编号 |
| bargainFirstPrice | Integer | bargain_first_price | 砍价起始价格（分） |
| bargainMinPrice | Integer | bargain_min_price | 砍价底价（分） |
| stock | Integer | stock | 砍价剩余库存（砍价时扣减） |
| totalStock | Integer | total_stock | 砍价总库存 |
| helpMaxCount | Integer | help_max_count | 砍价人数（助力达到该人数即成功） |
| bargainCount | Integer | bargain_count | 单用户帮砍次数上限 |
| totalLimitCount | Integer | total_limit_count | 总限购数量 |
| randomMinPrice | Integer | random_min_price | 单次砍价最小金额（分） |
| randomMaxPrice | Integer | random_max_price | 单次砍价最大金额（分） |

**继承**: BaseDO
**索引**: 主键 id；spu_id/sku_id 为关联查询列。

#### BargainRecordDO（promotion_bargain_record）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 用户编号，关联 MemberUserDO.id（发起砍价的用户） |
| activityId | Long | activity_id | 砍价活动编号，关联 BargainActivityDO.id |
| spuId | Long | spu_id | 商品 SPU 编号 |
| skuId | Long | sku_id | 商品 SKU 编号 |
| bargainFirstPrice | Integer | bargain_first_price | 砍价起始价格（分） |
| bargainPrice | Integer | bargain_price | 当前砍到价格（分） |
| status | Integer | status | 砍价状态，枚举 BargainRecordStatusEnum（成功条件：砍到底价或助力人数达标） |
| endTime | LocalDateTime | end_time | 结束时间 |
| orderId | Long | order_id | 订单编号（砍价成功后下单） |

**继承**: BaseDO
**索引**: 主键 id；user_id + activity_id（我的砍价）、status 为核心查询列。

#### BargainHelpDO（promotion_bargain_help）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| activityId | Long | activity_id | 砍价活动编号，关联 BargainActivityDO.id |
| recordId | Long | record_id | 砍价记录编号，关联 BargainRecordDO.id |
| userId | Long | user_id | 助力用户编号，关联 MemberUserDO.id |
| reducePrice | Integer | reduce_price | 本次减少价格（分） |

**继承**: BaseDO
**索引**: 主键 id；record_id（助力列表）、activity_id + user_id（帮砍次数校验）为核心查询列。

#### DiscountActivityDO（promotion_discount_activity）

限时折扣活动，一个商品在指定时间段内只能属于一个活动。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 活动编号，主键自增 |
| name | String | name | 活动标题 |
| status | Integer | status | 状态，枚举 CommonStatusEnum（活动关闭后不允许再次开启） |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id。

#### DiscountProductDO（promotion_discount_product）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| activityId | Long | activity_id | 限时折扣活动编号，关联 DiscountActivityDO.id |
| spuId | Long | spu_id | 商品 SPU 编号，关联 ProductSpuDO.id |
| skuId | Long | sku_id | 商品 SKU 编号，关联 ProductSkuDO.id |
| discountType | Integer | discount_type | 折扣类型，枚举 PromotionDiscountTypeEnum |
| discountPercent | Integer | discount_percent | 折扣百分比（80 表示 8 折） |
| discountPrice | Integer | discount_price | 优惠金额（分），discountType=PRICE 时生效 |
| activityName | String | activity_name | 活动标题（冗余） |
| activityStatus | Integer | activity_status | 活动状态（冗余） |
| activityStartTime | LocalDateTime | activity_start_time | 活动开始时间（冗余） |
| activityEndTime | LocalDateTime | activity_end_time | 活动结束时间（冗余） |

**继承**: BaseDO
**索引**: 主键 id；activity_id、sku_id（价格计算时按 SKU 匹配）为核心查询列。

#### RewardActivityDO（promotion_reward_activity）

满减送活动，优惠规则以 JSON 数组内嵌。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 活动编号，主键自增 |
| name | String | name | 活动标题 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| remark | String | remark | 备注 |
| conditionType | Integer | condition_type | 条件类型，枚举 PromotionConditionTypeEnum（满金额/满件） |
| productScope | Integer | product_scope | 商品范围，枚举 PromotionProductScopeEnum |
| productScopeValues | List&lt;Long&gt; | product_scope_values | 商品 SPU 编号数组（JSON，LongListTypeHandler） |
| rules | List&lt;Rule&gt; | rules | 优惠规则数组（JSON，JacksonTypeHandler），内嵌 limit/discountPrice/freeDelivery/point/giveCouponTemplateCounts |

**继承**: BaseDO
**索引**: 主键 id。内嵌类 `Rule`：limit 优惠门槛（满 N 元/件）、discountPrice 优惠金额、freeDelivery 是否包邮、point 赠送积分、giveCouponTemplateCounts 赠送优惠券（模板编号→数量）。

#### PointActivityDO（promotion_point_activity）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 活动编号，主键自增 |
| spuId | Long | spu_id | 活动商品 SPU 编号，关联 ProductSpuDO.id |
| status | Integer | status | 活动状态，枚举 CommonStatusEnum |
| remark | String | remark | 备注 |
| sort | Integer | sort | 排序 |
| stock | Integer | stock | 活动剩余库存（兑换时扣减） |
| totalStock | Integer | total_stock | 活动总库存 |

**继承**: BaseDO
**索引**: 主键 id。

#### PointProductDO（promotion_point_product）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| activityId | Long | activity_id | 积分商城活动编号，关联 PointActivityDO.id |
| spuId | Long | spu_id | 商品 SPU 编号 |
| skuId | Long | sku_id | 商品 SKU 编号 |
| count | Integer | count | 可兑换次数 |
| point | Integer | point | 所需兑换积分 |
| price | Integer | price | 所需兑换金额（分，积分 + 金额混合兑换） |
| stock | Integer | stock | 积分商城商品库存 |
| activityStatus | Integer | activity_status | 商品状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；activity_id、sku_id 为核心查询列。

#### DiyTemplateDO（promotion_diy_template）

装修模板，一个模板包含多个装修页面；全局仅一个 `used = true` 的启用模板。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 模板编号，主键自增 |
| name | String | name | 模板名称 |
| used | Boolean | used | 是否使用（全局有且仅有一个启用） |
| usedTime | LocalDateTime | used_time | 使用时间 |
| remark | String | remark | 备注 |
| previewPicUrls | List&lt;String&gt; | preview_pic_urls | 预览图（JSON，StringListTypeHandler） |
| property | String | property | uni-app 底部导航属性（JSON 字符串） |

**继承**: BaseDO
**索引**: 主键 id；used 为启用模板定位列。

#### DiyPageDO（promotion_diy_page）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 页面编号，主键自增 |
| templateId | Long | template_id | 装修模板编号，关联 DiyTemplateDO.id |
| name | String | name | 页面名称（如首页、我的） |
| remark | String | remark | 备注 |
| previewPicUrls | List&lt;String&gt; | preview_pic_urls | 预览图（JSON，StringListTypeHandler） |
| property | String | property | 页面属性（JSON 字符串，装修组件配置） |

**继承**: BaseDO
**索引**: 主键 id；template_id 为从属查询列。

#### ArticleDO（promotion_article）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 文章编号，主键自增 |
| categoryId | Long | category_id | 分类编号，关联 ArticleCategoryDO.id |
| spuId | Long | spu_id | 关联商品编号，关联 ProductSpuDO.id（文章导购） |
| title | String | title | 文章标题 |
| author | String | author | 文章作者 |
| picUrl | String | pic_url | 文章封面图片地址 |
| introduction | String | introduction | 文章简介 |
| browseCount | Integer | browse_count | 浏览次数 |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| recommendHot | Boolean | recommend_hot | 是否热门（小程序） |
| recommendBanner | Boolean | recommend_banner | 是否轮播图（小程序） |
| content | String | content | 文章内容（富文本） |

**继承**: BaseDO
**索引**: 主键 id；category_id 为从属查询列。

#### ArticleCategoryDO（promotion_article_category）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分类编号，主键自增 |
| name | String | name | 分类名称 |
| picUrl | String | pic_url | 图标地址 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| sort | Integer | sort | 排序 |

**继承**: BaseDO
**索引**: 主键 id。

#### BannerDO（promotion_banner）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| title | String | title | 标题 |
| url | String | url | 跳转链接 |
| picUrl | String | pic_url | 图片链接 |
| sort | Integer | sort | 排序 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |
| position | Integer | position | 定位，枚举 BannerPositionEnum（首页/商品分类页等展示位） |
| memo | String | memo | 备注 |
| browseCount | Integer | browse_count | 点击次数 |

**继承**: BaseDO
**索引**: 主键 id；position + status 为 App 端展示位查询列。

#### KeFuConversationDO（promotion_kefu_conversation）

客服会话，一个会员用户一个会话。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| userId | Long | user_id | 会话所属用户，关联 MemberUserDO.id |
| lastMessageTime | LocalDateTime | last_message_time | 最后聊天时间 |
| lastMessageContent | String | last_message_content | 最后聊天内容 |
| lastMessageContentType | Integer | last_message_content_type | 最后消息类型，枚举 KeFuMessageContentTypeEnum |
| adminPinned | Boolean | admin_pinned | 管理端置顶 |
| userDeleted | Boolean | user_deleted | 用户侧是否可见（删除标记） |
| adminDeleted | Boolean | admin_deleted | 管理员侧是否可见（删除标记） |
| adminUnreadMessageCount | Integer | admin_unread_message_count | 管理员未读消息数（用户发消息 +1，查看后扣减） |

**继承**: BaseDO
**索引**: 主键 id；user_id 业务上定位唯一会话。

#### KeFuMessageDO（promotion_kefu_message）

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| conversationId | Long | conversation_id | 会话编号，关联 KeFuConversationDO.id |
| senderId | Long | sender_id | 发送人编号（用户编号） |
| senderType | Integer | sender_type | 发送人类型，枚举 UserTypeEnum（会员/管理员） |
| receiverId | Long | receiver_id | 接收人编号 |
| receiverType | Integer | receiver_type | 接收人类型，枚举 UserTypeEnum |
| contentType | Integer | content_type | 消息类型，枚举 KeFuMessageContentTypeEnum（文本/图片/视频/商品等） |
| content | String | content | 消息内容 |
| readStatus | Boolean | read_status | 是否已读 |

**继承**: BaseDO
**索引**: 主键 id；conversation_id（会话消息列表）为核心查询列。

### 2.4 数据统计聚合（statistics 子模块）

#### TradeStatisticsDO（trade_statistics）

交易统计，以天为维度汇总全量交易数据（Job 每日统计）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| time | LocalDateTime | time | 统计日期（天维度） |
| orderCreateCount | Integer | order_create_count | 创建订单数 |
| orderPayCount | Integer | order_pay_count | 支付订单商品数 |
| orderPayPrice | Integer | order_pay_price | 总支付金额（分） |
| afterSaleCount | Integer | after_sale_count | 退款订单数 |
| afterSaleRefundPrice | Integer | after_sale_refund_price | 总退款金额（分） |
| brokerageSettlementPrice | Integer | brokerage_settlement_price | 佣金金额（已结算，分） |
| walletPayPrice | Integer | wallet_pay_price | 总支付金额（余额支付，分） |
| rechargePayCount | Integer | recharge_pay_count | 充值订单数（从 PayWalletRechargeDO 计算） |
| rechargePayPrice | Integer | recharge_pay_price | 充值金额（分） |
| rechargeRefundCount | Integer | recharge_refund_count | 充值退款订单数 |
| rechargeRefundPrice | Integer | recharge_refund_price | 充值退款金额（分） |

**继承**: BaseDO
**索引**: 主键 id；time 为统计区间查询列（Mapper 提供 `selectByTimeBetween`）。

#### ProductStatisticsDO（product_statistics）

商品统计，以天 + SPU 为维度汇总商品行为数据（Job 每日统计）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，主键自增 |
| time | LocalDate | time | 统计日期（天维度） |
| spuId | Long | spu_id | 商品 SPU 编号，关联 ProductSpuDO.id |
| browseCount | Integer | browse_count | 浏览量 |
| browseUserCount | Integer | browse_user_count | 访客量 |
| favoriteCount | Integer | favorite_count | 收藏数量 |
| cartCount | Integer | cart_count | 加购数量 |
| orderCount | Integer | order_count | 下单件数 |
| orderPayCount | Integer | order_pay_count | 支付件数 |
| orderPayPrice | Integer | order_pay_price | 支付金额（分） |
| afterSaleCount | Integer | after_sale_count | 退款件数 |
| afterSaleRefundPrice | Integer | after_sale_refund_price | 退款金额（分） |
| browseConvertPercent | Integer | browse_convert_percent | 访客支付转化率（百分比） |

**继承**: BaseDO
**索引**: 主键 id；time + spu_id 为统计维度查询列。

## 3. 实体关系

### 3.1 商品中心（product）

```
ProductCategoryDO(自关联 parentId 树) ──1:N── ProductSpuDO ──1:N── ProductSkuDO
                                              │    ▲                │
ProductBrandDO ──────────────1:N──────────────┘    │                │ properties(JSON)
                                                   │                ▼
ProductPropertyDO ──1:N── ProductPropertyValueDO   └────（SKU 规格组合冗余属性项/属性值 id 与名称）

ProductSpuDO ──1:N── ProductCommentDO（冗余 order/orderItem/sku 快照）
ProductSpuDO ──1:N── ProductFavoriteDO / ProductBrowseHistoryDO（均携带 userId，归属 MemberUserDO）
```

- SPU 上的 price/marketPrice/costPrice/stock 为 SKU 字段的汇总冗余；SKU.properties JSON 冗余属性项/属性值名称，属性改名时需同步。
- ProductCommentDO 同时引用 product 与 trade 两个子模块的实体（orderId/orderItemId → TradeOrderDO/TradeOrderItemDO）。

### 3.2 交易订单（trade）

```
TradeOrderDO ──1:N── TradeOrderItemDO ──N:1── ProductSkuDO（快照 spuName/picUrl/properties/price）
     │  │                │
     │  │                └──1:N── AfterSaleDO ──1:N── AfterSaleLogDO
     │  └──1:N── TradeOrderLogDO（状态流转轨迹，userId 区分会员/管理员/系统）
     │
     ├── N:1 ── CouponDO（couponId）；CouponDO.useOrderId 反向记录核销订单
     ├── N:1 ── DeliveryExpressDO（logisticsId）/ DeliveryPickUpStoreDO（pickUpStoreId）
     ├── N:1 ── BrokerageUserDO（brokerageUserId 推广人）
     └── 营销活动列：seckillActivityId / bargainActivityId(+bargainRecordId) /
         combinationActivityId(+combinationHeadId+combinationRecordId) / pointActivityId

DeliveryExpressTemplateDO ──1:N── DeliveryExpressTemplateChargeDO / DeliveryExpressTemplateFreeDO
CartDO ──N:1── MemberUserDO + ProductSpuDO/ProductSkuDO（下单后由 TradeOrderItemDO.cartId 关联回溯）
BrokerageUserDO ──1:N── BrokerageRecordDO（bizId+bizType 指向订单）／ BrokerageWithdrawDO
TradeConfigDO（全局单行配置，无外键）
```

- 订单/订单项/售后单均大量冗余商品与用户快照字段，保证历史订单不受商品修改影响。
- 金额公式：`payPrice = totalPrice − couponPrice − pointPrice − discountPrice + deliveryPrice + adjustPrice − vipPrice`（订单与订单项各自成体系）。
- 售后单通过 payRefundId / 退款回调对接 pay 模块；AfterSaleController 的 `/update-refunded`、BrokerageWithdrawController 的 `/update-transferred` 为 `@PermitAll` 的 pay 回调端点。

### 3.3 营销促销（promotion）

```
CouponTemplateDO ──1:N── CouponDO ──N:1──（核销）TradeOrderDO
SeckillConfigDO（时段，configIds JSON 被 SeckillActivityDO / SeckillProductDO 引用）
SeckillActivityDO ──1:N── SeckillProductDO ──N:1── ProductSkuDO
CombinationActivityDO ──1:N── CombinationProductDO
CombinationActivityDO ──1:N── CombinationRecordDO ──自关联 headId── 团长记录（headId=0 为团长）
BargainActivityDO ──1:N── BargainRecordDO ──1:N── BargainHelpDO（助力明细）
DiscountActivityDO ──1:N── DiscountProductDO ──N:1── ProductSkuDO
RewardActivityDO（rules JSON 内嵌优惠门槛/赠券，giveCouponTemplateCounts 指向 CouponTemplateDO）
PointActivityDO ──1:N── PointProductDO ──N:1── ProductSkuDO
DiyTemplateDO ──1:N── DiyPageDO
ArticleCategoryDO ──1:N── ArticleDO ──N:1── ProductSpuDO（导购文章）
KeFuConversationDO ──1:N── KeFuMessageDO（sender/receiver 按 UserTypeEnum 区分会员与管理员）
```

- 活动商品表（SeckillProduct/CombinationProduct/DiscountProduct/PointProduct）统一采用「活动 + SPU + SKU + 活动价 + 冗余活动状态/时间」的结构，供交易价格计算链（TradePriceCalculator）按 SKU 匹配优惠。
- TradeOrderDO 直接持有各活动编号列，实现订单 → 活动来源回溯；trade-api 包即为此跨模块协作提供 API（避免 promotion 与 trade 循环依赖）。

### 3.4 数据统计（statistics）

```
TradeStatisticsDO（按天汇总 trade_order / trade_after_sale / trade_brokerage_record / 会员钱包充值数据）
ProductStatisticsDO（按天+spuId 汇总 product_spu 的浏览/收藏/加购/下单/支付/退款数据）
```

- 两张统计表均由 Job 定时任务写入，无物理外键，仅通过 time（+ spuId）与业务表对账。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|----|------|
| product_spu | ProductSpuDO | 商品 SPU 主表 |
| product_sku | ProductSkuDO | 商品 SKU（价格/库存/规格） |
| product_category | ProductCategoryDO | 商品分类（两级树） |
| product_brand | ProductBrandDO | 商品品牌 |
| product_property | ProductPropertyDO | 商品属性项 |
| product_property_value | ProductPropertyValueDO | 商品属性值 |
| product_comment | ProductCommentDO | 商品评论 |
| product_favorite | ProductFavoriteDO | 商品收藏 |
| product_browse_history | ProductBrowseHistoryDO | 商品浏览记录 |
| promotion_coupon_template | CouponTemplateDO | 优惠券模板 |
| promotion_coupon | CouponDO | 用户优惠券 |
| promotion_seckill_config | SeckillConfigDO | 秒杀时段配置 |
| promotion_seckill_activity | SeckillActivityDO | 秒杀活动 |
| promotion_seckill_product | SeckillProductDO | 秒杀活动商品 |
| promotion_combination_activity | CombinationActivityDO | 拼团活动 |
| promotion_combination_product | CombinationProductDO | 拼团活动商品 |
| promotion_combination_record | CombinationRecordDO | 拼团记录（团长/团员） |
| promotion_bargain_activity | BargainActivityDO | 砍价活动 |
| promotion_bargain_record | BargainRecordDO | 砍价记录 |
| promotion_bargain_help | BargainHelpDO | 砍价助力明细 |
| promotion_discount_activity | DiscountActivityDO | 限时折扣活动 |
| promotion_discount_product | DiscountProductDO | 限时折扣商品 |
| promotion_reward_activity | RewardActivityDO | 满减送活动 |
| promotion_point_activity | PointActivityDO | 积分商城活动 |
| promotion_point_product | PointProductDO | 积分商城商品 |
| promotion_diy_template | DiyTemplateDO | 商城装修模板 |
| promotion_diy_page | DiyPageDO | 商城装修页面 |
| promotion_article | ArticleDO | 文章管理 |
| promotion_article_category | ArticleCategoryDO | 文章分类 |
| promotion_banner | BannerDO | 广告 Banner |
| promotion_kefu_conversation | KeFuConversationDO | 客服会话 |
| promotion_kefu_message | KeFuMessageDO | 客服消息 |
| trade_order | TradeOrderDO | 交易订单主表 |
| trade_order_item | TradeOrderItemDO | 交易订单项 |
| trade_order_log | TradeOrderLogDO | 订单操作日志 |
| trade_cart | CartDO | 购物车 |
| trade_after_sale | AfterSaleDO | 售后订单 |
| trade_after_sale_log | AfterSaleLogDO | 售后操作日志 |
| trade_delivery_express | DeliveryExpressDO | 快递公司 |
| trade_delivery_express_template | DeliveryExpressTemplateDO | 快递运费模板 |
| trade_delivery_express_template_charge | DeliveryExpressTemplateChargeDO | 运费模板计费配置 |
| trade_delivery_express_template_free | DeliveryExpressTemplateFreeDO | 运费模板包邮配置 |
| trade_delivery_pick_up_store | DeliveryPickUpStoreDO | 自提门店 |
| trade_brokerage_user | BrokerageUserDO | 分销用户 |
| trade_brokerage_record | BrokerageRecordDO | 佣金记录 |
| trade_brokerage_withdraw | BrokerageWithdrawDO | 佣金提现 |
| trade_config | TradeConfigDO | 交易中心配置 |
| trade_statistics | TradeStatisticsDO | 交易统计（天维度） |
| product_statistics | ProductStatisticsDO | 商品统计（天+SPU 维度） |

> 备注：App 端另有 32 个 App*Controller（购物车、分销等约 99 个端点）共用上述数据表，不引入额外表；trade 子模块的 `controller/admin/base` 与 statistics 子模块的 `controller/admin/common` 目录仅含共享 VO，无对应数据表。
