# 数据模型文档

> 模块路径：`yudao-module-mall`

---

## 1. 实体继承体系

所有 DO 实体类继承 `BaseDO`，统一包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键编号 |
| creator | String | 创建者 |
| createTime | LocalDateTime | 创建时间 |
| updater | String | 更新者 |
| updateTime | LocalDateTime | 更新时间 |
| deleted | Boolean | 是否删除（逻辑删除） |

> 如果实体支持多租户，继承 `TenantBaseDO`，额外包含 `tenantId` 字段。

---

## 2. 商品模块数据表

### 2.1 product_spu（商品 SPU 表）

**实体类**：`ProductSpuDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 商品 SPU 编号 |
| name | String | 商品名称 |
| keyword | String | 关键字 |
| introduction | String | 商品简介 |
| description | String | 商品详情 |
| category_id | Long | 分类编号 |
| brand_id | Long | 品牌编号 |
| pic_url | String | 商品封面图 |
| slider_pic_urls | List\<String\> | 轮播图 |
| status | Integer | 商品状态：-1 回收站 0 下架 1 上架 |
| spec_type | Boolean | 规格类型：false 单规格 true 多规格 |
| price | Integer | 最低价格（分） |
| market_price | Integer | 市场价（分） |
| cost_price | Integer | 成本价（分） |
| stock | Integer | 库存总量 |
| sales_count | Integer | 销量 |
| delivery_types | List\<Integer\> | 配送方式 |
| delivery_template_id | Long | 运费模板编号 |

### 2.2 product_sku（商品 SKU 表）

**实体类**：`ProductSkuDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | SKU 编号 |
| spu_id | Long | SPU 编号 |
| properties | List\<Property\> | 属性数组（JSON 存储） |
| price | Integer | 商品价格（分） |
| market_price | Integer | 市场价（分） |
| cost_price | Integer | 成本价（分） |
| bar_code | String | 商品条码 |
| pic_url | String | 图片地址 |
| stock | Integer | 库存 |
| weight | Double | 重量（kg） |
| volume | Double | 体积（m^3） |
| first_brokerage_price | Integer | 一级分销佣金 |
| second_brokerage_price | Integer | 二级分销佣金 |

> **Property 值对象**：`{ "propertyId": Long, "valueId": Long, "propertyName": String, "valueName": String }`

### 2.3 product_category（商品分类表）

**实体类**：`ProductCategoryDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分类编号 |
| parent_id | Long | 父分类编号 |
| name | String | 分类名称 |
| pic_url | String | 分类图片 |
| sort | Integer | 排序 |
| status | Integer | 状态：0 启用 1 禁用 |

### 2.4 product_brand（商品品牌表）

**实体类**：`ProductBrandDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 品牌编号 |
| name | String | 品牌名称 |
| pic_url | String | 品牌图片 |
| sort | Integer | 排序 |
| status | Integer | 状态 |

---

## 3. 交易模块数据表

### 3.1 trade_order（交易订单表）

**实体类**：`TradeOrderDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 订单编号 |
| no | String | 订单流水号 |
| type | Integer | 订单类型 |
| terminal | Integer | 订单来源终端 |
| user_id | Long | 用户编号 |
| status | Integer | 订单状态 |
| product_count | Integer | 商品数量 |
| total_price | Integer | 商品原价（分） |
| discount_price | Integer | 优惠金额（分） |
| delivery_price | Integer | 运费金额（分） |
| pay_price | Integer | 应付金额（分） |
| pay_order_id | Long | 支付订单编号 |
| pay_status | Boolean | 是否已支付 |
| pay_time | LocalDateTime | 付款时间 |
| delivery_type | Integer | 配送方式 |
| logistics_id | Long | 物流公司编号 |
| logistics_no | String | 物流单号 |
| receiver_name | String | 收件人名称 |
| receiver_mobile | String | 收件人手机 |
| receiver_detail_address | String | 收件人详细地址 |
| refund_status | Integer | 售后状态 |
| coupon_id | Long | 优惠券编号 |
| coupon_price | Integer | 优惠券减免金额 |

### 3.2 trade_order_item（交易订单项表）

**实体类**：`TradeOrderItemDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 订单项编号 |
| order_id | Long | 订单编号 |
| user_id | Long | 用户编号 |
| spu_id | Long | SPU 编号 |
| sku_id | Long | SKU 编号 |
| spu_name | String | 商品名称 |
| sku_name | String | SKU 名称 |
| price | Integer | 商品原价（分） |
| count | Integer | 购买数量 |
| pay_price | Integer | 子订单实付金额 |
| after_sale_status | Integer | 售后状态 |

### 3.3 trade_after_sale（售后订单表）

**实体类**：`AfterSaleDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 售后编号 |
| no | String | 售后流水号 |
| order_id | Long | 订单编号 |
| order_item_id | Long | 订单项编号 |
| user_id | Long | 用户编号 |
| type | Integer | 售后类型：0 退款 1 退货退款 |
| way | Integer | 退款方式 |
| status | Integer | 售后状态 |
| refund_price | Integer | 退款金额 |
| apply_reason | String | 申请原因 |

---

## 4. 促销模块数据表

### 4.1 promotion_coupon_template（优惠券模板表）

**实体类**：`CouponTemplateDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 模板编号 |
| name | String | 优惠券名称 |
| status | Integer | 状态 |
| total_count | Integer | 发放数量 |
| take_limit_count | Integer | 每人限领数量 |
| take_type | Integer | 领取方式 |
| product_scope | Integer | 商品范围 |
| discount_type | Integer | 折扣类型 |

### 4.2 promotion_coupon（优惠券表）

**实体类**：`CouponDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 优惠券编号 |
| template_id | Long | 模板编号 |
| user_id | Long | 用户编号 |
| status | Integer | 状态：1 未使用 2 已使用 3 已过期 |

### 4.3 promotion_seckill_activity（秒杀活动表）

**实体类**：`SeckillActivityDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 活动编号 |
| name | String | 活动名称 |
| spu_id | Long | SPU 编号 |
| status | Integer | 活动状态 |
| start_time | LocalDateTime | 开始时间 |
| end_time | LocalDateTime | 结束时间 |
| total_limit_count | Integer | 总限购数量 |
| single_limit_count | Integer | 单次限购数量 |

### 4.4 promotion_combination_activity（拼团活动表）

**实体类**：`CombinationActivityDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 活动编号 |
| name | String | 活动名称 |
| spu_id | Long | SPU 编号 |
| status | Integer | 活动状态 |
| user_size | Integer | 成团人数 |
| limit_duration | Integer | 拼团时长（小时） |

### 4.5 promotion_bargain_activity（砍价活动表）

**实体类**：`BargainActivityDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 活动编号 |
| name | String | 活动名称 |
| spu_id | Long | SPU 编号 |
| status | Integer | 活动状态 |
| bargain_first_price | Integer | 砍价起始价格 |
| bargain_min_price | Integer | 砍价最低价格 |

---

## 5. 表关系（ER 关系）

### 5.1 商品域

```
product_spu ──1:N──> product_sku           (spu_id)
product_spu ──N:1──> product_category      (category_id)
product_spu ──N:1──> product_brand         (brand_id)
```

| 关系 | 外键 | 说明 |
|------|------|------|
| product_spu -> product_sku | `spu_id` | 一个 SPU 对应多个 SKU |
| product_spu -> product_category | `category_id` | 多个 SPU 属于一个分类 |
| product_spu -> product_brand | `brand_id` | 多个 SPU 属于一个品牌 |

### 5.2 交易域

```
trade_order ──1:N──> trade_order_item      (order_id)
trade_order_item ──N:1──> product_sku      (sku_id)
trade_order ──1:N──> trade_after_sale      (order_id)
```

| 关系 | 外键 | 说明 |
|------|------|------|
| trade_order -> trade_order_item | `order_id` | 一个订单包含多个订单项 |
| trade_order_item -> product_sku | `sku_id` | 订单项关联 SKU |
| trade_order -> trade_after_sale | `order_id` | 一个订单可能有多个售后单 |

### 5.3 促销域

```
promotion_coupon_template ──1:N──> promotion_coupon  (template_id)
promotion_seckill_activity ──N:1──> product_spu      (spu_id)
promotion_combination_activity ──N:1──> product_spu  (spu_id)
promotion_bargain_activity ──N:1──> product_spu      (spu_id)
```

| 关系 | 外键 | 说明 |
|------|------|------|
| coupon_template -> coupon | `template_id` | 一个模板发放多张优惠券 |
| seckill_activity -> product_spu | `spu_id` | 秒杀活动关联商品 |
| combination_activity -> product_spu | `spu_id` | 拼团活动关联商品 |
| bargain_activity -> product_spu | `spu_id` | 砍价活动关联商品 |

---

## 6. 数据访问规范

### 6.1 Mapper 基类

所有 Mapper 继承 `BaseMapperX<T>`，提供增强查询能力：

```java
@Mapper
public interface ProductSpuMapper extends BaseMapperX<ProductSpuDO> {

    default PageResult<ProductSpuDO> selectPage(ProductSpuPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductSpuDO>()
                .likeIfPresent(ProductSpuDO::getName, reqVO.getName())
                .eqIfPresent(ProductSpuDO::getCategoryId, reqVO.getCategoryId())
                .eqIfPresent(ProductSpuDO::getStatus, reqVO.getStatus())
                .orderByDesc(ProductSpuDO::getSort));
    }
}
```

### 6.2 关键设计决策

- **价格使用整数（分）**：所有金额字段使用 Integer 类型，单位为分，避免浮点精度问题
- **逻辑删除**：所有表使用 `deleted` 字段进行逻辑删除
- **JSON 存储**：SKU 的 properties 字段使用 JSON 格式存储属性数组
- **金额快照**：订单项保存下单时的快照价格，不受商品价格后续变更影响
