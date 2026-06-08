# 促销域 API 文档

> 模块路径：`yudao-module-mall/yudao-module-promotion`

---

## 1. 优惠券模板管理（admin）

**Controller**: `CouponTemplateController`
**路径前缀**: `/admin-api/promotion/coupon-template`
**权限前缀**: `promotion:coupon-template:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建优惠券模板 | `promotion:coupon-template:create` |
| PUT | `/update` | 更新优惠券模板 | `promotion:coupon-template:update` |
| DELETE | `/delete` | 删除优惠券模板 | `promotion:coupon-template:delete` |
| GET | `/get` | 获取模板详情 | `promotion:coupon-template:query` |
| GET | `/page` | 模板分页查询 | `promotion:coupon-template:query` |
| PUT | `/update-status` | 更新模板状态 | `promotion:coupon-template:update` |

### 1.2 请求/响应 VO

**CouponTemplateSaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 优惠券名称 |
| totalCount | Integer | 是 | 发放数量 |
| takeLimitCount | Integer | 是 | 每人限领数量 |
| takeType | Integer | 是 | 领取方式 |
| productScope | Integer | 是 | 商品范围：0 全部 1 指定商品 |
| productScopeValues | List\<Long\> | 否 | 指定商品 SPU 编号列表 |
| discountType | Integer | 是 | 折扣类型：0 满减 1 折扣 2 立减 |
| discountPercent | Integer | 否 | 折扣百分比（discountType=1 时） |
| discountPrice | Integer | 否 | 优惠金额（分） |
| usePrice | Integer | 否 | 最低消费金额（分） |
| validityType | Integer | 是 | 有效期类型：0 固定日期 1 领取后 N 天 |
| validStartTime | LocalDateTime | 否 | 固定开始时间 |
| validEndTime | LocalDateTime | 否 | 固定结束时间 |
| fixedStartTerm | Integer | 否 | 领取后 N 天开始 |
| fixedEndTerm | Integer | 否 | 领取后 N 天结束 |

---

## 2. 优惠券管理（admin）

**Controller**: `CouponController`
**路径前缀**: `/admin-api/promotion/coupon`
**权限前缀**: `promotion:coupon:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 手动发放优惠券 | `promotion:coupon:create` |
| GET | `/page` | 优惠券分页查询 | `promotion:coupon:query` |
| GET | `/get` | 获取优惠券详情 | `promotion:coupon:query` |

---

## 3. 用户端优惠券（app）

**Controller**: `AppCouponController`
**路径前缀**: `/app-api/promotion/coupon`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/take` | 领取优惠券 |
| GET | `/list` | 我的优惠券列表 |
| GET | `/list-by-template` | 可领取的优惠券模板列表 |
| GET | `/available` | 下单时可用优惠券列表 |

**CouponStatusEnum**:

| 值 | 状态 |
|----|------|
| 1 | 未使用 |
| 2 | 已使用 |
| 3 | 已过期 |

---

## 4. 秒杀活动管理（admin）

**Controller**: `SeckillActivityController`
**路径前缀**: `/admin-api/promotion/seckill-activity`
**权限前缀**: `promotion:seckill-activity:*`

### 4.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建秒杀活动 | `promotion:seckill-activity:create` |
| PUT | `/update` | 更新秒杀活动 | `promotion:seckill-activity:update` |
| DELETE | `/delete` | 删除秒杀活动 | `promotion:seckill-activity:delete` |
| GET | `/get` | 获取活动详情 | `promotion:seckill-activity:query` |
| GET | `/page` | 活动分页查询 | `promotion:seckill-activity:query` |
| PUT | `/update-status` | 更新活动状态 | `promotion:seckill-activity:update` |

### 4.2 请求/响应 VO

**SeckillActivitySaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 活动名称 |
| spuId | Long | 是 | SPU 编号 |
| startTime | LocalDateTime | 是 | 开始时间 |
| endTime | LocalDateTime | 是 | 结束时间 |
| totalLimitCount | Integer | 是 | 总限购数量 |
| singleLimitCount | Integer | 是 | 单次限购数量 |
| seckillPrice | Integer | 是 | 秒杀价格（分） |
| seckillStock | Integer | 是 | 秒杀库存 |

---

## 5. 用户端秒杀（app）

**Controller**: `AppSeckillActivityController`
**路径前缀**: `/app-api/promotion/seckill-activity`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/list` | 秒杀活动列表 |
| GET | `/get` | 活动详情 |
| POST | `/order` | 秒杀下单 |

---

## 6. 拼团活动管理（admin）

**Controller**: `CombinationActivityController`
**路径前缀**: `/admin-api/promotion/combination-activity`
**权限前缀**: `promotion:combination-activity:*`

### 6.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建拼团活动 | `promotion:combination-activity:create` |
| PUT | `/update` | 更新拼团活动 | `promotion:combination-activity:update` |
| DELETE | `/delete` | 删除拼团活动 | `promotion:combination-activity:delete` |
| GET | `/get` | 获取活动详情 | `promotion:combination-activity:query` |
| GET | `/page` | 活动分页查询 | `promotion:combination-activity:query` |
| PUT | `/update-status` | 更新活动状态 | `promotion:combination-activity:update` |

### 6.2 请求/响应 VO

**CombinationActivitySaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 活动名称 |
| spuId | Long | 是 | SPU 编号 |
| userSize | Integer | 是 | 成团人数 |
| limitDuration | Integer | 是 | 拼团时长（小时） |
| combinationPrice | Integer | 是 | 拼团价格（分） |

---

## 7. 用户端拼团（app）

**Controller**: `AppCombinationActivityController`
**路径前缀**: `/app-api/promotion/combination-activity`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/list` | 拼团活动列表 |
| GET | `/get` | 活动详情 |
| POST | `/order` | 参团下单 |
| GET | `/record/list` | 拼团记录列表 |

**CombinationRecord 状态**:

| 值 | 状态 |
|----|------|
| 0 | 进行中 |
| 1 | 已成功（成团） |
| 2 | 已失败（超时未成团） |

---

## 8. 砍价活动管理（admin）

**Controller**: `BargainActivityController`
**路径前缀**: `/admin-api/promotion/bargain-activity`
**权限前缀**: `promotion:bargain-activity:*`

### 8.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建砍价活动 | `promotion:bargain-activity:create` |
| PUT | `/update` | 更新砍价活动 | `promotion:bargain-activity:update` |
| DELETE | `/delete` | 删除砍价活动 | `promotion:bargain-activity:delete` |
| GET | `/get` | 获取活动详情 | `promotion:bargain-activity:query` |
| GET | `/page` | 活动分页查询 | `promotion:bargain-activity:query` |
| PUT | `/update-status` | 更新活动状态 | `promotion:bargain-activity:update` |

### 8.2 请求/响应 VO

**BargainActivitySaveReqVO**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 活动名称 |
| spuId | Long | 是 | SPU 编号 |
| bargainFirstPrice | Integer | 是 | 砍价起始价格（分） |
| bargainMinPrice | Integer | 是 | 砍价最低价格（分） |

---

## 9. 用户端砍价（app）

**Controller**: `AppBargainActivityController`
**路径前缀**: `/app-api/promotion/bargain-activity`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/list` | 砍价活动列表 |
| GET | `/get` | 活动详情 |
| POST | `/start` | 发起砍价 |
| POST | `/help` | 帮好友砍价 |
| GET | `/record/get` | 砍价记录详情 |

---

## 10. RPC API 跨模块接口

### CouponApi

| 方法 | 说明 |
|------|------|
| `useCoupon(Long couponId, Long orderId)` | 使用优惠券 |
| `returnCoupon(Long couponId)` | 退回优惠券（订单取消时） |
| `validateCoupon(Long couponId, Long userId)` | 校验优惠券可用性 |

### SeckillActivityApi

| 方法 | 说明 |
|------|------|
| `validateSeckill(Long activityId, Long userId)` | 校验秒杀资格 |
| `deductSeckillStock(Long activityId, Integer count)` | 扣减秒杀库存 |
| `restoreSeckillStock(Long activityId, Integer count)` | 恢复秒杀库存 |

### CombinationRecordApi

| 方法 | 说明 |
|------|------|
| `validateRecord(Long recordId)` | 校验拼团记录 |

---

## 11. 错误码

| 错误码 | 说明 |
|--------|------|
| `1_013_004_000` | 优惠券模板不存在 |
| `1_013_008_006` | 秒杀失败，原因：秒杀库存不足 |
