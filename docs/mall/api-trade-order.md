# 交易订单接口 (TradeOrderController)

> 管理后台对交易订单的查询（分页/统计/详情/物流轨迹）与操作（发货、备注、调价、改地址、自提核销）入口。

## 接口路径前缀

/trade/order  (Controller: TradeOrderController)

## 1. 订单查询

### 1.1 获得交易订单分页

- **路径**: GET /trade/order/page
- **权限**: trade:order:query
- **说明**: 按条件分页查询交易订单，附带订单项、下单用户与推广人信息。

**请求参数 (TradeOrderPageReqVO)**（继承 PageParam: pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| no | String | 否 | - | 订单号 |
| userId | Long | 否 | - | 用户编号 |
| userNickname | String | 否 | - | 用户昵称（按昵称模糊匹配会员后过滤） |
| userMobile | String | 否 | @Mobile | 用户手机号 |
| deliveryType | Integer | 否 | - | 配送方式 |
| logisticsId | Long | 否 | - | 发货物流公司编号 |
| pickUpStoreIds | List&lt;Long&gt; | 否 | - | 自提门店编号列表 |
| pickUpVerifyCode | String | 否 | - | 自提核销码 |
| type | Integer | 否 | - | 订单类型 |
| status | Integer | 否 | @InEnum(TradeOrderStatusEnum) | 订单状态 |
| payChannelCode | String | 否 | - | 支付渠道 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间范围 |
| terminal | Integer | 否 | @InEnum(TerminalEnum) | 订单来源终端 |

**响应**: CommonResult&lt;PageResult&lt;TradeOrderPageItemRespVO&gt;&gt;

TradeOrderPageItemRespVO 继承 TradeOrderBaseVO（公共字段见 1.3 节附表），额外字段：

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| receiverAreaName | String | 收件人地区名字 |
| items | List&lt;Item&gt; | 订单项列表（Item 继承 TradeOrderItemBaseVO，含 properties 属性列表） |
| user | MemberUserRespVO | 下单用户信息 |
| brokerageUser | MemberUserRespVO | 推广人信息 |

**业务逻辑**: 1. 按用户昵称/手机号查询会员，构建 userIds 过滤条件（查不到用户则直接返回空页）。2. 分页查询订单列表。3. 汇总订单的下单用户与推广人编号，批量查询会员信息。4. 根据订单编号集合查询全部订单项。5. 通过 TradeOrderConvert 组装为分页项 VO 返回。

### 1.2 获得交易订单统计

- **路径**: GET /trade/order/summary
- **权限**: trade:order:query
- **说明**: 按与分页相同的筛选条件，统计订单数量、订单金额、退款单数与退款金额。

**请求参数 (TradeOrderPageReqVO)**: 同 1.1 节分页请求参数。

**响应**: CommonResult&lt;TradeOrderSummaryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| orderCount | Long | 订单数量（未退款订单） |
| orderPayPrice | Long | 订单金额（实付总额，单位分） |
| afterSaleCount | Long | 退款单数（部分/全部退款订单） |
| afterSalePrice | Long | 退款金额 |

**业务逻辑**: 1. 按用户昵称/手机号构建 userIds 过滤条件（查不到用户则返回全 0 统计）。2. 调用 Mapper 按售后退款状态（refundStatus）分组统计数量与金额。3. 未退款（NONE）的分组计入订单数量/金额，部分退款与全部退款的分组累加计入退款单数/退款金额。

### 1.3 获得交易订单详情

- **路径**: GET /trade/order/get-detail
- **权限**: trade:order:query
- **说明**: 查询单个订单的完整详情，含订单项、操作日志、下单用户与推广人。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | - | 订单编号 |

**响应**: CommonResult&lt;TradeOrderDetailRespVO&gt;（订单不存在时返回 null）

TradeOrderDetailRespVO 继承 TradeOrderBaseVO，额外字段：

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| items | List&lt;Item&gt; | 订单项列表（Item 继承 TradeOrderItemBaseVO，含 properties 属性列表） |
| user | MemberUserRespVO | 下单用户信息 |
| brokerageUser | MemberUserRespVO | 推广用户信息 |
| logs | List&lt;OrderLog&gt; | 操作日志列表 |
| receiverAreaName | String | 收件人地区名字 |

TradeOrderDetailRespVO.OrderLog:

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| content | String | 操作详情（如"订单发货"） |
| createTime | LocalDateTime | 创建时间 |
| userType | Integer | 用户类型 |

**请求参数附表 — TradeOrderBaseVO 公共字段**（1.1/1.3 响应共用）:

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| id | Long | 订单编号 |
| no | String | 订单流水号 |
| createTime | LocalDateTime | 下单时间 |
| type | Integer | 订单类型 |
| terminal | Integer | 订单来源 |
| userId | Long | 用户编号 |
| userIp | String | 用户 IP |
| userRemark | String | 用户备注 |
| status | Integer | 订单状态 |
| productCount | Integer | 购买的商品数量 |
| finishTime | LocalDateTime | 订单完成时间 |
| cancelTime | LocalDateTime | 订单取消时间 |
| cancelType | Integer | 取消类型 |
| remark | String | 商家备注 |
| payOrderId | Long | 支付订单编号 |
| payStatus | Boolean | 是否已支付 |
| payTime | LocalDateTime | 付款时间 |
| payChannelCode | String | 支付渠道 |
| totalPrice | Integer | 商品原价（总） |
| discountPrice | Integer | 订单优惠（总） |
| deliveryPrice | Integer | 运费金额 |
| adjustPrice | Integer | 订单调价（总） |
| payPrice | Integer | 应付金额（总） |
| deliveryType | Integer | 配送方式 |
| pickUpStoreId | Long | 自提门店 |
| pickUpVerifyCode | Long | 自提核销码 |
| deliveryTemplateId | Long | 配送模板编号 |
| logisticsId | Long | 发货物流公司编号 |
| logisticsNo | String | 发货物流单号 |
| deliveryTime | LocalDateTime | 发货时间 |
| receiveTime | LocalDateTime | 收货时间 |
| receiverName | String | 收件人名称 |
| receiverMobile | String | 收件人手机 |
| receiverAreaId | Integer | 收件人地区编号 |
| receiverDetailAddress | String | 收件人详细地址 |
| afterSaleStatus | Integer | 售后状态 |
| refundPrice | Integer | 退款金额 |
| couponId | Long | 优惠劵编号 |
| couponPrice | Integer | 优惠劵减免金额 |
| pointPrice | Integer | 积分抵扣的金额 |
| vipPrice | Integer | VIP 减免金额 |
| brokerageUserId | Long | 推广人编号 |

TradeOrderItemBaseVO（订单项公共字段）:

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| id | Long | 订单项编号 |
| userId | Long | 用户编号 |
| orderId | Long | 订单编号 |
| spuId | Long | 商品 SPU 编号 |
| spuName | String | 商品 SPU 名称 |
| skuId | Long | 商品 SKU 编号 |
| picUrl | String | 商品图片 |
| count | Integer | 购买数量 |
| price | Integer | 商品原价（单） |
| discountPrice | Integer | 商品优惠（总） |
| payPrice | Integer | 商品实付金额（总） |
| orderPartPrice | Integer | 子订单分摊金额（总） |
| orderDividePrice | Integer | 分摊后子订单实付金额（总） |
| afterSaleStatus | Integer | 售后状态 |

**业务逻辑**: 1. 按编号查询订单，不存在返回 null。2. 查询该订单的全部订单项。3. 查询下单用户信息，推广人编号非空时再查询推广人信息。4. 查询该订单的操作日志列表（TradeOrderLogService）。5. 组装为 TradeOrderDetailRespVO 返回。

### 1.4 获得交易订单的物流轨迹

- **路径**: GET /trade/order/get-express-track-list
- **权限**: trade:order:query
- **说明**: 查询已发货订单的快递物流轨迹，结果按「快递公司编码 + 单号 + 手机号」缓存。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | - | 交易订单编号 |

**响应**: CommonResult&lt;List&lt;ExpressTrackRespDTO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| time | LocalDateTime | 轨迹发生时间 |
| content | String | 快递状态描述 |

**业务逻辑**: 1. 按编号查询订单，不存在抛 ORDER_NOT_FOUND。2. 订单无物流公司编号（logisticsId 为空）时返回空列表。3. 查询物流公司，不存在抛 EXPRESS_NOT_EXISTS。4. 通过 ExpressClientFactory 获取默认快递客户端，按快递公司编码、物流单号、收件人手机号查询轨迹，结果写入 Redis 缓存（ EXPRESS_TRACK，减少付费查询次数）。

### 1.5 查询核销码对应的订单

- **路径**: GET /trade/order/get-by-pick-up-verify-code
- **权限**: trade:order:query
- **说明**: 门店核销前，按自提核销码查询待核销订单，用于核销界面预览。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| pickUpVerifyCode | String | 是 | - | 自提核销码 |

**响应**: CommonResult&lt;TradeOrderDetailRespVO&gt;（仅订单基础字段，无订单项/日志等附加信息）

**业务逻辑**: 1. 按自提核销码查询订单（selectOneByPickUpVerifyCode）。2. 转换为详情 VO 返回（不组装订单项与用户信息）。

## 2. 订单操作

### 2.1 订单发货

- **路径**: PUT /trade/order/delivery
- **权限**: trade:order:update
- **说明**: 对待发货的快递订单执行发货，记录物流公司/单号并通知用户。

**请求参数 (TradeOrderDeliveryReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @NotNull | 订单编号 |
| logisticsId | Long | 是 | @NotNull | 发货物流公司编号（传 LOGISTICS_ID_NULL 表示无需发货） |
| logisticsNo | String | 否 | - | 发货物流单号 |

**响应**: CommonResult&lt;Boolean&gt;（操作结果）

**业务逻辑**: 1. 校验订单存在且未退款（validateOrderDeliverable），并执行 TradeOrderHandler 前置处理；订单不是待发货状态则抛 ORDER_DELIVERY_FAIL_STATUS_NOT_UNDELIVERED（更新失败时）。2. 校验配送方式必须为快递（EXPRESS），否则抛 ORDER_DELIVERY_FAIL_DELIVERY_TYPE_NOT_EXPRESS。3. 快递发货时校验物流公司存在并记录物流编号/单号；无需发货时置 logisticsId=0、单号为空。4. 更新订单状态为【已发货】并记录发货时间（CAS 更新，状态不匹配则抛错），记录订单日志。5. 发送站内信与微信小程序订阅消息（订单编号、状态、发货时间、快递单号、收货地址）。6. 执行 TradeOrderHandler 发货后置处理（如分销佣金冻结等）。

### 2.2 订单备注

- **路径**: PUT /trade/order/update-remark
- **权限**: trade:order:update
- **说明**: 商家为订单添加/修改备注。

**请求参数 (TradeOrderRemarkReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @NotNull | 订单编号 |
| remark | String | 是 | @NotEmpty | 商家备注 |

**响应**: CommonResult&lt;Boolean&gt;（操作结果）

**业务逻辑**: 1. 校验订单存在（不存在抛 ORDER_NOT_FOUND）。2. 更新订单的商家备注字段。

### 2.3 订单调价

- **路径**: PUT /trade/order/update-price
- **权限**: trade:order:update
- **说明**: 商家对未支付订单调价，调整金额按订单项分摊并同步支付单。

**请求参数 (TradeOrderUpdatePriceReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @NotNull | 订单编号 |
| adjustPrice | Integer | 是 | @NotNull | 订单调价，单位分；正数加价、负数减价 |

**响应**: CommonResult&lt;Boolean&gt;（操作结果）

**业务逻辑**: 1. 校验订单存在；已支付则抛 ORDER_UPDATE_PRICE_FAIL_PAID；已调过价（adjustPrice > 0）则抛 ORDER_UPDATE_PRICE_FAIL_ALREADY。2. 计算新支付价格（payPrice + adjustPrice），小于等于 0 抛 ORDER_UPDATE_PRICE_FAIL_PRICE_ERROR。3. 更新订单的 adjustPrice（累加）与 payPrice。4. 查询订单项，用 TradePriceCalculatorHelper.dividePrice2 将调价金额按金额占比分摊到各订单项，批量更新每项的 adjustPrice 与 payPrice。5. 调用 payOrderApi.updatePayOrderPrice 同步修改支付订单金额。6. 记录订单日志（旧支付价、调整额、新支付价）。

**错误码**:

| 错误码 | 说明 |
|-----|-----|
| 1_011_000_011 | 交易订单不存在 |
| 1_011_000_026 | 支付订单调价失败，原因：支付订单已付款,不能调价 |
| 1_011_000_027 | 支付订单调价失败，原因：已经修改过价格 |
| 1_011_000_028 | 支付订单调价失败，原因：调整后支付价格不能小于 0.01 元 |

### 2.4 修改订单收货地址

- **路径**: PUT /trade/order/update-address
- **权限**: trade:order:update
- **说明**: 仅待发货（未支付/已支付未发货）状态订单允许修改收货地址。

**请求参数 (TradeOrderUpdateAddressReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @NotNull | 订单编号 |
| receiverName | String | 是 | @NotEmpty | 收件人名称 |
| receiverMobile | String | 是 | @NotEmpty | 收件人手机 |
| receiverAreaId | Integer | 是 | @NotNull | 收件人地区编号 |
| receiverDetailAddress | String | 是 | @NotEmpty | 收件人详细地址 |

**响应**: CommonResult&lt;Boolean&gt;（操作结果）

**业务逻辑**: 1. 校验订单存在。2. 校验订单状态为待发货（isUndelivered），否则抛 ORDER_UPDATE_ADDRESS_FAIL_STATUS_NOT_DELIVERED。3. 更新订单收件人信息。4. 记录订单日志。

## 3. 订单核销（自提）

### 3.1 订单核销（按订单编号）

- **路径**: PUT /trade/order/pick-up-by-id
- **权限**: trade:order:pick-up
- **说明**: 门店核销员按订单编号核销自提订单，订单直接完成收货。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | - | 交易订单编号 |

**响应**: CommonResult&lt;Boolean&gt;（操作结果）

### 3.2 订单核销（按核销码）

- **路径**: PUT /trade/order/pick-up-by-verify-code
- **权限**: trade:order:pick-up
- **说明**: 门店核销员扫描/输入自提核销码核销订单。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| pickUpVerifyCode | String | 是 | - | 自提核销码 |

**响应**: CommonResult&lt;Boolean&gt;（操作结果）

### 3.1/3.2 共用业务逻辑（pickUpOrder）: 1. 按编号或核销码查询订单，不存在抛 ORDER_NOT_FOUND。2. 校验配送方式为【用户自提】（PICK_UP），否则抛 ORDER_RECEIVE_FAIL_DELIVERY_TYPE_NOT_PICK_UP。3. 校验订单状态为待发货（待核销），否则抛 ORDER_PICK_UP_FAIL_STATUS_NOT_UNDELIVERED。4. 拼团订单（type 为拼团）需查询拼团记录，拼团未成功抛 ORDER_PICK_UP_FAIL_COMBINATION_NOT_SUCCESS。5. 查询订单的自提门店，门店不存在或当前登录用户不在门店核销员列表（verifyUserIds）中，抛 ORDER_PICK_UP_FAIL_NOT_VERIFY_USER。6. 执行收货：CAS 更新订单状态为【已完成】并记录收货时间（失败抛 ORDER_RECEIVE_FAIL_STATUS_NOT_DELIVERED），记录订单日志，执行 TradeOrderHandler 收货后置处理。

**错误码**（3.1/3.2 共用）:

| 错误码 | 说明 |
|-----|-----|
| 1_011_000_011 | 交易订单不存在 |
| 1_011_000_030 | 交易订单自提失败，收货方式不是【用户自提】 |
| 1_011_000_036 | 交易订单自提失败，原因：你没有核销该门店订单的权限 |
| 1_011_000_037 | 交易订单自提失败，原因：商品拼团记录不是【成功】状态 |
| 1_011_000_039 | 交易订单自提失败，订单不是【待核销】状态 |
| 1_011_000_018 | 交易订单收货失败，订单不是【待收货】状态 |

## 域级错误码汇总（trade/order 相关，前缀 1_011_000_XXX）

| 错误码 | 说明 |
|-----|-----|
| 1_011_000_010 | 交易订单项不存在 |
| 1_011_000_011 | 交易订单不存在 |
| 1_011_000_012 | 交易订单项更新售后状态失败，请重试 |
| 1_011_000_013 | 交易订单更新支付状态失败，订单不是【未支付】状态 |
| 1_011_000_014 | 交易订单更新支付状态失败，支付单编号不匹配 |
| 1_011_000_015 | 交易订单更新支付状态失败，支付单状态不是【支付成功】状态 |
| 1_011_000_016 | 交易订单更新支付状态失败，支付单金额不匹配 |
| 1_011_000_017 | 交易订单发货失败，订单不是【待发货】状态 |
| 1_011_000_018 | 交易订单收货失败，订单不是【待收货】状态 |
| 1_011_000_019 | 创建交易订单项的评价失败，订单不是【已完成】状态 |
| 1_011_000_020 | 创建交易订单项的评价失败，订单已评价 |
| 1_011_000_021 | 交易订单发货失败，订单已退款或部分退款 |
| 1_011_000_022 | 交易订单发货失败，拼团未成功 |
| 1_011_000_023 | 交易订单发货失败，砍价未成功 |
| 1_011_000_024 | 交易订单发货失败，发货类型不是快递 |
| 1_011_000_025 | 交易订单取消失败，订单不是【待支付】状态 |
| 1_011_000_026 | 支付订单调价失败，原因：支付订单已付款,不能调价 |
| 1_011_000_027 | 支付订单调价失败，原因：已经修改过价格 |
| 1_011_000_028 | 支付订单调价失败，原因：调整后支付价格不能小于 0.01 元 |
| 1_011_000_029 | 交易订单删除失败，订单不是【已取消】状态 |
| 1_011_000_030 | 交易订单自提失败，收货方式不是【用户自提】 |
| 1_011_000_031 | 交易订单修改收货地址失败，原因：订单不是【待发货】状态 |
| 1_011_000_032 | 交易订单创建失败，原因：存在未付款订单 |
| 1_011_000_033 | 交易订单取消支付失败，原因：订单不是【{}】状态 |
| 1_011_000_034 | 交易订单更新支付订单退款状态失败，原因：退款单不存在 |
| 1_011_000_035 | 交易订单更新支付订单退款状态失败，原因：退款单状态不是【退款成功】 |
| 1_011_000_036 | 交易订单自提失败，原因：你没有核销该门店订单的权限 |
| 1_011_000_037 | 交易订单自提失败，原因：商品拼团记录不是【成功】状态 |
| 1_011_000_038 | 交易订单创建失败，原因：用户积分不足 |
| 1_011_000_039 | 交易订单自提失败，订单不是【待核销】状态 |
| 1_011_004_000 | 快递公司不存在（物流轨迹查询相关） |
