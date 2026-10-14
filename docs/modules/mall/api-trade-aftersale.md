# 售后订单接口 (AfterSaleController)

> 管理后台对交易售后单的查询与处理：分页/详情查询、审批（同意/拒绝）、退货收货（确认收货/拒绝收货）、退款发起，以及接收支付模块退款结果回调。

## 接口路径前缀
/trade/after-sale  (Controller: AfterSaleController)

## 通用数据结构

### AfterSaleBaseVO（分页与详情响应的公共字段）

AfterSaleRespPageItemVO 与 AfterSaleDetailRespVO 均继承 AfterSaleBaseVO：

| 字段 | 类型 | 说明 |
|-----|------|------|
| no | String | 售后流水号 |
| status | Integer | 售后状态（见下方状态枚举） |
| type | Integer | 售后类型：10 售中退款 / 20 售后退款 |
| way | Integer | 售后方式：10 仅退款 / 20 退货退款 |
| userId | Long | 用户编号 |
| applyReason | String | 申请原因 |
| applyDescription | String | 补充描述 |
| applyPicUrls | List&lt;String&gt; | 补充凭证图片 |
| orderId | Long | 订单编号 |
| orderNo | String | 订单流水号 |
| orderItemId | Long | 订单项编号 |
| spuId | Long | 商品 SPU 编号 |
| spuName | String | 商品 SPU 名称 |
| skuId | Long | 商品 SKU 编号 |
| picUrl | String | 商品图片 |
| count | Integer | 购买数量 |
| auditTime | LocalDateTime | 审批时间 |
| auditUserId | Long | 审批人（管理员用户编号） |
| auditReason | String | 审批备注 |
| refundPrice | Integer | 退款金额，单位：分 |
| payRefundId | Long | 支付退款编号 |
| refundTime | LocalDateTime | 退款时间 |
| logisticsId | Long | 退货物流公司编号 |
| logisticsNo | String | 退货物流单号 |
| deliveryTime | LocalDateTime | 退货时间 |
| receiveTime | LocalDateTime | 收货时间 |
| receiveReason | String | 收货备注 |

### 售后状态枚举（AfterSaleStatusEnum）

| 值 | 名称 | 触发动作 |
|----|------|---------|
| 10 | 申请中 | 会员申请退款 |
| 20 | 卖家通过 | 商家同意退款（待买家退货） |
| 30 | 待卖家收货 | 会员填写退货物流信息 |
| 40 | 等待平台退款 | 商家收货 |
| 50 | 完成 | 商家确认退款 / 退款成功 |
| 61 | 买家取消售后 | 会员取消退款 |
| 62 | 卖家拒绝 | 商家拒绝退款申请 |
| 63 | 卖家拒绝收货 | 商家拒绝收货，不同意退款 |

## 1. 售后查询

### 1.1 获得售后订单分页
- **路径**: GET /trade/after-sale/page
- **权限**: trade:after-sale:query
- **说明**: 分页查询售后订单，并拼接每条记录对应的会员用户信息

**请求参数 (AfterSalePageReqVO)**: 继承 PageParam

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull | 页码，从 1 开始，默认 1（继承 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Max(200) | 每页条数，最大 200，默认 10（继承 PageParam） |
| userId | Long | 否 | - | 用户编号 |
| no | String | 否 | - | 售后流水号 |
| status | Integer | 否 | @InEnum(AfterSaleStatusEnum) | 售后状态 |
| type | Integer | 否 | @InEnum(AfterSaleTypeEnum) | 售后类型 |
| way | Integer | 否 | @InEnum(AfterSaleWayEnum) | 售后方式 |
| orderNo | String | 否 | - | 订单编号（流水号） |
| spuName | String | 否 | - | 商品 SPU 名称 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;AfterSaleRespPageItemVO&gt;&gt;

AfterSaleRespPageItemVO 继承 AfterSaleBaseVO（公共字段见「通用数据结构」），额外字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 售后编号 |
| createTime | LocalDateTime | 创建时间 |
| properties | List&lt;ProductPropertyValueDetailRespVO&gt; | 商品属性数组（propertyId/propertyName/valueId/valueName） |
| user | MemberUserRespVO | 用户信息（id 用户编号、nickname 用户昵称、avatar 用户头像） |

**业务逻辑**:
1. 调用 `AfterSaleService.getAfterSalePage`，由 `AfterSaleMapper.selectPage` 按 AfterSalePageReqVO 条件分页查询售后单。
2. 分页结果为空时直接返回空的 PageResult。
3. 收集结果中的 `userId` 集合，通过 `MemberUserApi.getUserMap` 批量查询会员用户信息。
4. 通过 `AfterSaleConvert.convertPage` 将售后单与会员信息拼接为 AfterSaleRespPageItemVO 分页结果返回。

### 1.2 获得售后订单详情
- **路径**: GET /trade/after-sale/get-detail
- **权限**: trade:after-sale:query
- **说明**: 查询售后单详情，拼接关联订单、订单项、会员用户及售后操作日志

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 售后编号 |

**响应**: CommonResult&lt;AfterSaleDetailRespVO&gt;

AfterSaleDetailRespVO 继承 AfterSaleBaseVO（公共字段见「通用数据结构」），额外字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 售后编号 |
| order | TradeOrderBaseVO | 订单基本信息（编号、流水号、下单时间、状态、金额、收货信息等） |
| orderItem | OrderItem | 订单项信息，继承 TradeOrderItemBaseVO（SPU/SKU 编号、名称、图片、数量、价格、售后状态），额外含 properties 商品属性数组 |
| user | MemberUserRespVO | 用户信息（id/nickname/avatar） |
| logs | List&lt;AfterSaleLogRespVO&gt; | 售后日志列表：id、userId、userType、afterSaleId、beforeStatus（操作前状态）、afterStatus（操作后状态）、content 操作明细、createTime |

**业务逻辑**:
1. 按 id 调用 `AfterSaleService.getAfterSale` 查询售后单，不存在时返回 null。
2. 通过 `TradeOrderQueryService.getOrder` 查询售后单关联的交易订单。
3. 通过 `TradeOrderQueryService.getOrderItem` 查询售后单关联的订单项。
4. 通过 `MemberUserApi.getUser` 查询申请售后的会员用户信息。
5. 通过 `AfterSaleLogService.getAfterSaleLogList` 查询该售后单的全部操作日志。
6. 通过 `AfterSaleConvert.convert` 将五者拼接为 AfterSaleDetailRespVO 返回。

## 2. 售后审批

### 2.1 同意售后
- **路径**: PUT /trade/after-sale/agree
- **权限**: trade:after-sale:agree
- **说明**: 商家同意售后申请，按售后方式流转到不同状态

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 售后编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验售后单存在（否则抛 AFTER_SALE_NOT_FOUND），且状态为【申请中】10（否则抛 AFTER_SALE_AUDIT_FAIL_STATUS_NOT_APPLY）。
2. 按售后方式分流：仅退款（way=10）→ 状态改为【等待平台退款】40；退货退款（way=20）→ 状态改为【卖家通过】20，等买家退货。
3. 通过 `updateByIdAndStatus`（旧状态乐观锁）更新售后单状态，同时记录 auditUserId（当前登录管理员）与 auditTime；更新失败（并发冲突）抛 AFTER_SALE_UPDATE_STATUS_FAIL。
4. 通过 @AfterSaleLog 切面记录售后日志（操作类型 ADMIN_AGREE_APPLY，记录前后状态）。

### 2.2 拒绝售后
- **路径**: PUT /trade/after-sale/disagree
- **权限**: trade:after-sale:disagree
- **说明**: 商家拒绝售后申请，售后单终止并回滚订单项售后状态

**请求参数 (AfterSaleDisagreeReqVO)**: Body JSON

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 售后编号 |
| auditReason | String | 是 | @NotEmpty | 审批备注 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验售后单存在且状态为【申请中】10（错误码同 2.1）。
2. 更新售后单状态为【卖家拒绝】62，记录 auditUserId、auditTime 与 auditReason（审批备注）。
3. 记录售后日志（操作类型 ADMIN_DISAGREE_APPLY）。
4. 调用 `TradeOrderUpdateService.updateOrderItemWhenAfterSaleCancel` 将关联订单项的售后状态恢复为【未申请】。

## 3. 退货收货

### 3.1 确认收货
- **路径**: PUT /trade/after-sale/receive
- **权限**: trade:after-sale:receive
- **说明**: 商家确认收到买家退回的货物，售后进入待退款状态

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 售后编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验售后单存在（AFTER_SALE_NOT_FOUND），且状态为【待卖家收货】30（否则抛 AFTER_SALE_CONFIRM_FAIL_STATUS_NOT_BUYER_DELIVERY）。
2. 更新售后单状态为【等待平台退款】40，记录 receiveTime。
3. 记录售后日志（操作类型 ADMIN_AGREE_RECEIVE）。

### 3.2 拒绝收货
- **路径**: PUT /trade/after-sale/refuse
- **权限**: trade:after-sale:receive
- **说明**: 商家拒收买家退回的货物，售后单终止并回滚订单项售后状态

**请求参数 (AfterSaleRefuseReqVO)**: 该方法未标注 @RequestBody，参数按 Query/Form 方式绑定；且未加 @Valid，注解校验不生效

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是（代码意图） | @NotNull（未生效） | 售后编号 |
| refuseMemo | String | 是（代码意图） | @NotNull（未生效） | 收货备注 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验售后单存在（AFTER_SALE_NOT_FOUND），且状态为【待卖家收货】30（AFTER_SALE_CONFIRM_FAIL_STATUS_NOT_BUYER_DELIVERY）。
2. 更新售后单状态为【卖家拒绝收货】63，记录 receiveTime 与 receiveReason（取自 refuseMemo）。
3. 记录售后日志（操作类型 ADMIN_DISAGREE_RECEIVE，日志内容附拒绝原因）。
4. 调用 `TradeOrderUpdateService.updateOrderItemWhenAfterSaleCancel` 将关联订单项的售后状态恢复为【未申请】。

## 4. 退款

### 4.1 确认退款
- **路径**: PUT /trade/after-sale/refund
- **权限**: trade:after-sale:refund
- **说明**: 商家对【待退款】售后单发起支付退款，退款结果由支付回调更新

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 售后编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验售后单存在（AFTER_SALE_NOT_FOUND），且状态为【等待平台退款】40（否则抛 AFTER_SALE_REFUND_FAIL_STATUS_NOT_WAIT_REFUND）。
2. 特殊情况：退款金额为 0（如积分商城订单）时，直接将售后单状态更新为【完成】50 并记录 refundTime，不发起支付退款。
3. 否则调用 `createPayRefund`：通过 `PayRefundApi.createRefund` 创建支付退款单（退款原因为 `退款【spuName】`，用户类型 MEMBER），并将返回的 payRefundId 更新到售后单；售后单状态保持 40，等待支付模块回调。
4. 记录售后日志（操作类型 ADMIN_REFUND）。

### 4.2 更新售后订单为已退款
- **路径**: POST /trade/after-sale/update-refunded
- **权限**: @PermitAll（无需登录；由 pay-module 支付服务通过 PayNotifyJob 回调，安全由 AfterSaleService 内部校验实现）
- **说明**: 接收支付模块退款结果通知，更新售后单（或原支付订单）的退款状态

**请求参数 (PayRefundNotifyReqDTO)**: Body JSON

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantOrderId | String | 是 | @NotEmpty | 商户订单编号（此处为售后单编号或订单编号字符串） |
| merchantRefundId | String | 是 | @NotEmpty | 商户退款编号；以 `order-` 开头表示未支付订单的退款回调 |
| payRefundId | Long | 是 | @NotNull | 支付退款单编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 控制器分流：若 `merchantRefundId` 以 `order-` 开头，说明是「未支付订单退款」回调，解析出订单编号后转交 `TradeOrderUpdateService.updatePaidOrderRefunded` 处理后直接返回。
2. 否则为售后退款回调：按 id 查询售后单（AFTER_SALE_NOT_FOUND），校验状态为【等待平台退款】40（AFTER_SALE_REFUND_FAIL_STATUS_NOT_WAIT_REFUND）。
3. 校验支付退款单合法性：退款单存在（AFTER_SALE_REFUND_FAIL_REFUND_NOT_FOUND）；状态为成功或失败（AFTER_SALE_REFUND_FAIL_REFUND_NOT_SUCCESS_OR_FAILURE）；退款金额与售后单一致（AFTER_SALE_REFUND_FAIL_REFUND_PRICE_NOT_MATCH）；商户退款单号与售后单编号匹配（AFTER_SALE_REFUND_FAIL_REFUND_ORDER_ID_ERROR）。
4. 退款成功：售后单状态更新为【完成】50 并记录 refundTime，记录售后日志，调用 `TradeOrderUpdateService.updateOrderItemWhenAfterSaleSuccess` 将订单项售后状态更新为已完成（按退款金额）。
5. 退款失败：仅记录售后日志（操作类型 SYSTEM_REFUND_FAIL），售后单状态不变。

## 域错误码（After Sale 模块，前缀 1-011-000-100）

定义于 `yudao-module-trade-api` 的 `cn.iocoder.yudao.module.trade.enums.ErrorCodeConstants`：

| 错误码 | 说明 |
|-------|------|
| 1_011_000_100 | 售后单不存在 |
| 1_011_000_101 | 申请退款金额错误 |
| 1_011_000_102 | 订单已关闭，无法申请售后 |
| 1_011_000_103 | 订单未支付，无法申请售后 |
| 1_011_000_104 | 订单未发货，无法申请【退货退款】售后 |
| 1_011_000_105 | 订单项已申请售后，无法重复申请 |
| 1_011_000_106 | 审批失败，售后状态不处于审批中 |
| 1_011_000_107 | 操作售后单失败，请刷新后重试 |
| 1_011_000_108 | 退货失败，售后单状态不处于【待买家退货】 |
| 1_011_000_109 | 确认收货失败，售后单状态不处于【待确认收货】 |
| 1_011_000_110 | 退款失败，售后单状态不是【待退款】 |
| 1_011_000_111 | 退款失败，退款单不存在 |
| 1_011_000_112 | 退款失败，退款单未退款 |
| 1_011_000_113 | 退款失败，退款金额不匹配 |
| 1_011_000_114 | 退款失败，退款单不匹配 |
| 1_011_000_115 | 取消售后单失败，售后单状态不是【待审核】或【卖家同意】或【商家待收货】 |
| 1_011_000_116 | 订单拼团中，无法申请售后 |

其中 1_011_000_101 ~ 105、108、115、116 由 App 端售后创建/退货/取消操作触发（见 AppAfterSaleController），admin 端主要触发 1_011_000_100、106、107、109、110 ~ 114。4.2 端点的「未支付订单退款」分支还可能抛出 Order 模块错误码：1_011_000_034（退款单不存在）、1_011_000_035（退款单状态不是【退款成功】）。
