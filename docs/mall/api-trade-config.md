# 交易中心配置接口 (TradeConfigController)

> 管理交易中心的售后理由、配送（全场包邮/自提）与分销（分佣、返佣比例、提现）等全局配置，配置全局单条记录存储于 `trade_config` 表。

## 接口路径前缀

/trade/config  (Controller: TradeConfigController)

## 1. 交易中心配置

### 1.1 更新交易中心配置

- **路径**: PUT /trade/config/save
- **权限**: trade:config:save
- **说明**: 保存（新增或更新）交易中心全局配置，采用"存在即更新、不存在即插入"的 upsert 语义。

**请求参数 (TradeConfigSaveReqVO)**: 继承 TradeConfigBaseVO，字段如下

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| afterSaleRefundReasons | List&lt;String&gt; | 是 | @NotEmpty | 售后的退款理由 |
| afterSaleReturnReasons | List&lt;String&gt; | 是 | @NotEmpty | 售后的退货理由 |
| deliveryExpressFreeEnabled | Boolean | 是 | @NotNull | 是否启用全场包邮 |
| deliveryExpressFreePrice | Integer | 是 | @NotNull、@PositiveOrZero | 全场包邮的最小金额，单位：分 |
| deliveryPickUpEnabled | Boolean | 是 | @NotNull | 是否开启自提 |
| brokerageEnabled | Boolean | 是 | @NotNull | 是否启用分佣 |
| brokerageEnabledCondition | Integer | 是 | @NotNull、@InEnum(BrokerageEnabledConditionEnum) | 分佣模式：1 人人分销、2 指定分销 |
| brokerageBindMode | Integer | 是 | @NotNull、@InEnum(BrokerageBindModeEnum) | 分销关系绑定模式：1 首次绑定、2 注册绑定、3 覆盖绑定 |
| brokeragePosterUrls | List&lt;String&gt; | 否 | 无 | 分销海报图地址数组 |
| brokerageFirstPercent | Integer | 是 | @NotNull、@Range(0-100) | 一级返佣比例 |
| brokerageSecondPercent | Integer | 是 | @NotNull、@Range(0-100) | 二级返佣比例 |
| brokerageWithdrawMinPrice | Integer | 是 | @NotNull、@PositiveOrZero | 用户提现最低金额，单位：分 |
| brokerageWithdrawFeePercent | Integer | 是 | @NotNull、@PositiveOrZero | 用户提现手续费百分比（1% 传 1） |
| brokerageFrozenDays | Integer | 是 | @NotNull、@PositiveOrZero | 佣金冻结时间(天) |
| brokerageWithdrawTypes | List&lt;Integer&gt; | 是 | @NotEmpty、@InEnum(BrokerageWithdrawTypeEnum) | 提现方式：1 钱包、2 银行卡、3 微信收款码、4 支付宝收款码、5 微信零钱、6 支付宝余额 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 保存成功返回 true |

**业务逻辑**:
1. 调用 `getTradeConfig()` 查询当前配置（查全表取第一条记录）。
2. 若配置存在，则将 SaveReqVO 转换为 TradeConfigDO 并回填已有记录的 id，执行 `updateById` 更新。
3. 若配置不存在，则将 SaveReqVO 转换为 TradeConfigDO，执行 `insert` 新增。

### 1.2 获得交易中心配置

- **路径**: GET /trade/config/get
- **权限**: trade:config:query
- **说明**: 获取交易中心全局配置，并附带服务端配置文件中的腾讯地图 KEY。

**请求参数**: 无

**响应**: CommonResult&lt;TradeConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 自增主键 |
| tencentLbsKey | String | 腾讯地图 KEY（来自配置项 `yudao.tencent-lbs-key`，非数据库字段） |
| afterSaleRefundReasons | List&lt;String&gt; | 售后的退款理由 |
| afterSaleReturnReasons | List&lt;String&gt; | 售后的退货理由 |
| deliveryExpressFreeEnabled | Boolean | 是否启用全场包邮 |
| deliveryExpressFreePrice | Integer | 全场包邮的最小金额，单位：分 |
| deliveryPickUpEnabled | Boolean | 是否开启自提 |
| brokerageEnabled | Boolean | 是否启用分佣 |
| brokerageEnabledCondition | Integer | 分佣模式：1 人人分销、2 指定分销 |
| brokerageBindMode | Integer | 分销关系绑定模式：1 首次绑定、2 注册绑定、3 覆盖绑定 |
| brokeragePosterUrls | List&lt;String&gt; | 分销海报图地址数组 |
| brokerageFirstPercent | Integer | 一级返佣比例 |
| brokerageSecondPercent | Integer | 二级返佣比例 |
| brokerageWithdrawMinPrice | Integer | 用户提现最低金额，单位：分 |
| brokerageWithdrawFeePercent | Integer | 用户提现手续费百分比 |
| brokerageFrozenDays | Integer | 佣金冻结时间(天) |
| brokerageWithdrawTypes | List&lt;Integer&gt; | 提现方式：1 钱包、2 银行卡、3 微信收款码、4 支付宝收款码、5 微信零钱、6 支付宝余额 |

（除 id、tencentLbsKey 外的字段均继承自 TradeConfigBaseVO）

**业务逻辑**:
1. 调用 `getTradeConfig()`：通过 `tradeConfigMapper.selectList()` 查询全部配置记录，取第一条返回（全局仅一条配置）。
2. 通过 `TradeConfigConvert` 将 TradeConfigDO 转换为 TradeConfigRespVO。
3. 若配置非空，将 `@Value("${yudao.tencent-lbs-key}")` 注入的腾讯地图 KEY 设置到响应 VO 中。
