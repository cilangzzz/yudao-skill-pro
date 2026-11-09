# 商城代码模式与扩展指南 (mall)

> 本文档移植自模块 Skill 知识库（skill-mall.yaml），提供该模块的代码模式、扩展指南与关键文件索引。模块概况、API 清单与数据表详见 [README.md](README.md)。

## 代码模式

以下模式以商品（product）、交易（trade）子模块的典型实现为范本，适用于 mall 各子模块的日常开发。

### Controller 层规范

Controller 类统一使用以下注解组合：

- `@RestController`
- `@RequestMapping`
- `@Tag(name = "模块名称")`（Swagger 接口分组）
- `@Operation(summary = "接口描述")`
- `@PreAuthorize("@ss.hasPermission('权限标识')")`

示例（商品 SPU 管理接口）：

```java
@Tag(name = "管理后台 - 商品 SPU")
@RestController
@RequestMapping("/product/spu")
@Validated
public class ProductSpuController {

    @Resource
    private ProductSpuService productSpuService;

    @PostMapping("/create")
    @Operation(summary = "创建商品 SPU")
    @PreAuthorize("@ss.hasPermission('product:spu:create')")
    public CommonResult<Long> createProductSpu(@Valid @RequestBody ProductSpuSaveReqVO createReqVO) {
        return success(productSpuService.createSpu(createReqVO));
    }

    @GetMapping("/page")
    @Operation(summary = "获得商品 SPU 分页")
    @PreAuthorize("@ss.hasPermission('product:spu:query')")
    public CommonResult<PageResult<ProductSpuRespVO>> getSpuPage(@Valid ProductSpuPageReqVO pageVO) {
        PageResult<ProductSpuDO> pageResult = productSpuService.getSpuPage(pageVO);
        return success(BeanUtils.toBean(pageResult, ProductSpuRespVO.class));
    }
}
```

请求参数中的枚举字段统一用 `@InEnum` 做入参校验，非法值在参数校验阶段直接返回 HTTP 400，不要进入 Service 后再手工判断。例如 `ProductSpuSaveReqVO.deliveryTypes` 标注 `@InEnum(value = DeliveryTypeEnum.class, message = "配送方式不正确")`，取值被限定为 1 快递发货 / 2 用户自提。跨子模块共享的枚举放在 `yudao-module-trade-api`（product 因此新增对 trade-api 的依赖），但 trade-api 的定位是纯 API 骨架包，禁止在其中引入任何实现类依赖。

### Service 层规范

接口定义模式：

```java
public interface ProductSpuService {
    Long createSpu(@Valid ProductSpuSaveReqVO createReqVO);
    void updateSpu(@Valid ProductSpuSaveReqVO updateReqVO);
    void deleteSpu(Long id);
    ProductSpuDO getSpu(Long id);
    PageResult<ProductSpuDO> getSpuPage(ProductSpuPageReqVO pageReqVO);
}
```

实现类模式：

```java
@Service
@Validated
public class ProductSpuServiceImpl implements ProductSpuService {

    @Resource
    private ProductSpuMapper productSpuMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long createSpu(ProductSpuSaveReqVO createReqVO) {
        // 1. 校验分类、品牌
        validateCategory(createReqVO.getCategoryId());
        brandService.validateProductBrand(createReqVO.getBrandId());
        // 2. 校验 SKU
        productSkuService.validateSkuList(skuSaveReqList, createReqVO.getSpecType());
        // 3. 插入 SPU
        ProductSpuDO spu = BeanUtils.toBean(createReqVO, ProductSpuDO.class);
        productSpuMapper.insert(spu);
        // 4. 插入 SKU
        productSkuService.createSkuList(spu.getId(), skuSaveReqList);
        return spu.getId();
    }
}
```

示例：商品创建流程

```java
// 商品创建流程
@Transactional(rollbackFor = Exception.class)
public Long createSpu(ProductSpuSaveReqVO createReqVO) {
    // 1. 校验分类、品牌
    validateCategory(createReqVO.getCategoryId());
    brandService.validateProductBrand(createReqVO.getBrandId());
    // 2. 校验 SKU
    List<ProductSkuSaveReqVO> skuSaveReqList = createReqVO.getSkus();
    productSkuService.validateSkuList(skuSaveReqList, createReqVO.getSpecType());
    // 3. 初始化 SPU 信息
    ProductSpuDO spu = BeanUtils.toBean(createReqVO, ProductSpuDO.class);
    initSpuFromSkus(spu, skuSaveReqList);
    // 4. 插入 SPU
    productSpuMapper.insert(spu);
    // 5. 插入 SKU
    productSkuService.createSkuList(spu.getId(), skuSaveReqList);
    return spu.getId();
}
```

### 数据访问层（DAL）规范

Mapper 继承 `BaseMapperX`，分页查询使用 `LambdaQueryWrapperX` 按条件拼接：

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

查询示例：

```java
// 使用 MyBatis-Plus 查询
List<ProductSpuDO> list = productSpuMapper.selectList(
    new LambdaQueryWrapper<ProductSpuDO>()
        .eq(ProductSpuDO::getStatus, ProductSpuStatusEnum.ENABLE.getStatus())
        .orderByDesc(ProductSpuDO::getSort)
);
```

#### 取前 N 条 / 单条：使用 selectListLimitN / selectFirstOne

禁止再用 `.last("LIMIT n")` 追加行数限制（非 MySQL 数据库不可移植）。框架 `BaseMapperX` 提供：

```java
// 前 N 条：走 MyBatis-Plus 分页插件，按数据库生成 LIMIT / ROWNUM / OFFSET FETCH，不执行 COUNT
return selectListLimitN(new LambdaQueryWrapperX<XxxDO>()
        .eq(XxxDO::getStatus, status)
        .orderByAsc(XxxDO::getId), count);   // SQL Server 分页要求 ORDER BY，必须显式排序

// 单条：等价于 selectListLimitN(wrapper, 1) 取第一条
return selectFirstOne(new LambdaQueryWrapper<XxxDO>()
        .eq(XxxDO::getUserId, userId)
        .orderByDesc(XxxDO::getId));
```

约定：limit 为负数时直接抛 `IllegalArgumentException`（防负数被分页插件视为不分页而查全表），为 0 时直接返回空列表；`selectListLimitN` 保留 wrapper 的排序与 `select` 投影，但不再允许通过 `last` 追加行数限制。mall 中 `BargainActivityMapper`、`BargainRecordMapper`、`CombinationRecordMapper`、`CouponTemplateMapper`、`KeFuMessageMapper` 均已按此迁移，并为砍价相关查询补齐确定性 `ORDER BY id`。

#### 统计 XML 的方言与字面量

- 日期分组用 `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@castDate('create_time')}`（`LocalDate` 消费者）、`castDateText(...)`（字符串消费者）、`formatYearDashMonth(...)`（`yyyy-MM` 月份标签）；配合 `resultMap` 显式映射 `statDate → date`，不要直接写 `CAST(... AS DATE)` 或 `CONCAT(EXTRACT(...))`。
- 布尔值用 `<bind name="trueValue" value="true"/>` + `#{trueValue}` 绑定，不要写 `pay_status = TRUE`。
- 逻辑删除条件统一写 `deleted = 0`，不要写 `deleted = FALSE`。
- 以上约定不改变任何接口响应字段（`date` / `orderPayCount` / `orderPayPrice` / `count` 保持不变）。

### 异常处理

各子模块错误码前缀：

| 子模块 | 错误码前缀 |
|-------|-----------|
| product | 1-008-xxx-xxx |
| trade | 1-011-xxx-xxx |
| promotion | 1-013-xxx-xxx |

典型错误码示例：

| 错误码 | 错误信息 | 模块 |
|-------|---------|------|
| 1_008_005_000 | 商品 SPU 不存在 | product |
| 1_008_006_004 | 商品 SKU 库存不足 | product |
| 1_011_000_011 | 交易订单不存在 | trade |
| 1_011_000_014 | 交易订单更新支付状态失败，支付单编号不匹配（同时用于回调 payOrderId 与订单绑定单号不一致） | trade |
| 1_011_000_017 | 交易订单发货失败，订单不是【待发货】状态（实际白名单为【待发货】或【已发货】，其余未付款/已取消/已完成状态均抛此错误） | trade |
| 1_011_000_114 | 退款失败，退款单不匹配（同时用于回调 payRefundId 与售后单绑定单号不一致） | trade |
| 1_011_008_005 | 提现单更新转账状态失败，转账单不匹配（同时用于回调 payTransferId 与提现单绑定单号不一致） | trade |
| 1_013_004_000 | 优惠劵模板不存在 | promotion |
| 1_013_008_006 | 秒杀失败，原因：秒杀库存不足 | promotion |

> 错误码语义复用提醒：1_011_000_017 / 1_011_000_114 / 1_011_008_005 本次未新增，而是扩展了触发场景（发货状态白名单、三类支付回调的单号双向核对）。扩展代码时不要按错误码文案字面推断，具体判定以 Service 中的白名单与单号比对逻辑为准。

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE, args)`，通过各模块 `ErrorCodeConstants` 中定义的错误码抛出业务异常

## 扩展指南

### 新增业务功能（以商品为例）

1. 创建 DO 实体类：在 dal/dataobject 目录下创建实体类，继承 BaseDO
2. 创建 Mapper 接口：在 dal/mysql 目录下创建 Mapper，继承 BaseMapperX
3. 创建 Service 接口和实现：在 service 目录下创建接口和实现类
4. 创建 VO 类：在 controller/vo 目录下创建请求和响应 VO
5. 创建 Controller：在 controller 目录下创建控制器
6. 创建错误码：在 enums/ErrorCodeConstants.java 中定义错误码
7. 编写单元测试：验证业务逻辑正确性

### 新增促销活动类型

1. 创建活动 DO 实体：如 XxxActivityDO，关联商品和规则
2. 创建 API 接口：提供活动校验、库存扣减等跨模块调用能力
3. 创建 Service 层：处理活动创建、状态流转、库存管理
4. 集成到订单流程：在 TradePriceService 中增加价格计算逻辑
5. 集成到下单流程：在 TradeOrderUpdateService 中处理活动商品下单
6. 创建管理后台接口：活动创建、编辑、上下架等
7. 创建用户端接口：活动列表、详情、参与等

### 最佳实践

- 商品状态管理：使用 ProductSpuStatusEnum 枚举，状态变更通过 updateSpuStatus 方法
- 订单状态流转：严格遵循状态机模式，状态变更记录日志
- 库存扣减：使用乐观锁或 Redis 原子操作，防止超卖
- 价格计算：统一使用分为单位，避免浮点精度问题
- 事务管理：涉及多表操作时使用 @Transactional 注解
- 异常处理：使用框架提供的 exception() 方法抛出业务异常
- API 设计：跨模块调用通过 API 接口，避免直接依赖实现类
- 并发控制：使用分布式锁处理秒杀、拼团等高并发场景

## 模块依赖

> 框架 starter 依赖、mall 内部子模块依赖方向及下游消费情况见 [README.md](README.md) 的「依赖关系」一节，此处补充 Skill 知识库记录的模块间 API 依赖与第三方库清单。

### 内部依赖（其他业务模块）

| 模块 | API | 用途 |
|-----|-----|------|
| yudao-module-member | MemberUserApi、MemberAddressApi、MemberConfigApi、MemberLevelApi、MemberPointApi | 会员信息、收货地址、会员积分配置（抵扣上限、赠送比例）、会员等级、积分变更 |
| yudao-module-pay | PayOrderApi、PayRefundApi、PayTransferApi、PayWalletApi | 创建支付单/退款单/转账单、查询钱包余额；同时接收 pay 的 `PayNotifyJob` 回调（售后退款、佣金提现转账） |
| yudao-module-system | AdminUserApi、NotifyMessageSendApi、SocialClientApi | 获取管理员用户信息、发送站内信、微信小程序发货信息录入/确认收货/订阅消息 |
| yudao-module-infra | WebSocketSenderApi | 客服消息的 WebSocket 推送 |
| yudao-module-trade-api（mall 内部） | DeliveryTypeEnum、TradeOrderStatusEnum 等 18 个共享枚举 + TradeOrderApi + ErrorCodeConstants | product 用 `DeliveryTypeEnum` 做 SPU 配送方式参数校验（product → trade-api）；promotion/trade/statistics 复用订单状态、售后、分销、配送、通知等枚举与错误码 |

### 外部依赖（第三方库）

| 依赖 | 版本 | 用途 |
|-----|------|------|
| MyBatis-Plus | 3.5.17 | ORM 框架，简化数据库操作 |
| MapStruct | 1.7.0.Beta2 | 对象映射，VO 与 DO 转换（各子模块的 `*Convert` 类共 35 个） |
| Spring Validation | javax.validation（JSR-303，Spring Boot 2.7 内置 Hibernate Validator） | 参数校验（`@NotNull`、`@InEnum` 等） |
| Swagger/OpenAPI | springdoc-openapi 1.8.0 | API 文档生成 |
| Redis / Redisson | Redisson 4.8.0（经 `yudao-spring-boot-starter-redis` 引入）；Redis 服务端版本未在仓库中固定 | 缓存（物流轨迹 `@Cacheable`）、分布式锁；**不用于库存扣减**——库存统一走数据库 CAS 条件更新，见 pitfalls.md 5.1 |

### 配置项（application.yaml）

mall 仅 trade 子模块提供自定义配置，product / promotion / statistics 子模块没有 `@ConfigurationProperties`，配置集中在 `yudao-server` 的 `application.yaml` 的 `yudao.trade` 节点下。

| 配置前缀 | 配置类 | 配置项 | 默认值 | 说明 |
|---------|-------|-------|-------|------|
| `yudao.trade.order` | `TradeOrderProperties`（`framework/order/config`，由 `TradeOrderConfig` 的 `@EnableConfigurationProperties` 注册） | `payAppKey` | `mall` | 支付应用标识，需在 pay 模块「支付管理 → 应用信息」中创建同名应用；下单与提现转账都用它 |
| | | `payExpireTime` | 无默认（`@NotNull` 必填） | 支付超时时间，yaml 示例 `2h`；用于计算支付单过期时间与自动取消订单的截止时间 |
| | | `receiveExpireTime` | 无默认（`@NotNull` 必填） | 收货超时时间，yaml 示例 `14d`；`TradeOrderAutoReceiveJob` 据此自动确认收货 |
| | | `commentExpireTime` | 无默认（`@NotNull` 必填） | 评论超时时间，yaml 示例 `7d`；`TradeOrderAutoCommentJob` 据此自动评价 |
| | | `statusSyncToWxaEnable` | 无默认（`@NotNull` 必填） | 是否同步订单状态到微信小程序，yaml 示例 `true`；注意当前 mall 源码中只有该配置项定义，未被任何代码读取 |
| `yudao.trade.express` | `TradeExpressProperties`（`framework/delivery/config`，`@Component` + `@ConfigurationProperties`，由 `ExpressClientConfig` 注入 `ExpressClientFactory`） | `client` | `not_provide` | 快递客户端：not_provide 未提供 / kd_niao 快递鸟 / kd_100 快递100（`ExpressClientEnum`）；`not_provide` 时工厂返回 `NoProvideExpressClient`（不真正查询快递轨迹） |
| | | `kdNiao.businessId` / `kdNiao.apiKey` / `kdNiao.requestType` | 无默认（`@NotEmpty` 必填） | 快递鸟用户 ID / API Key / 接口指令（1002 免费版仅支持申通、圆通；8001 付费版） |
| | | `kd100.customer` / `kd100.key` | 无默认（`@NotEmpty` 必填） | 快递 100 授权码 / 授权 key |

> 配置缺失会导致应用启动失败：`payExpireTime`、`receiveExpireTime`、`commentExpireTime`、`statusSyncToWxaEnable` 均标注 `@NotNull`，快递鸟 / 快递 100 的子配置标注 `@NotEmpty`（校验失败即启动报错）。

## 关键文件

### 商品模块（yudao-module-product）

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mall/yudao-module-product/src/main/java/cn/iocoder/yudao/module/product/dal/dataobject/spu/ProductSpuDO.java | 商品SPU实体类，电商核心领域模型 |
| yudao-module-mall/yudao-module-product/src/main/java/cn/iocoder/yudao/module/product/dal/dataobject/sku/ProductSkuDO.java | 商品SKU实体类，库存管理单元 |
| yudao-module-mall/yudao-module-product/src/main/java/cn/iocoder/yudao/module/product/service/spu/ProductSpuService.java | 商品SPU服务接口，定义商品CRUD操作 |
| yudao-module-mall/yudao-module-product/src/main/java/cn/iocoder/yudao/module/product/controller/admin/spu/ProductSpuController.java | 商品SPU管理接口，后台商品管理入口 |
| yudao-module-mall/yudao-module-product/src/main/java/cn/iocoder/yudao/module/product/enums/ErrorCodeConstants.java | 商品模块错误码定义 |

### 交易模块（yudao-module-trade / yudao-module-trade-api）

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mall/yudao-module-trade/src/main/java/cn/iocoder/yudao/module/trade/dal/dataobject/order/TradeOrderDO.java | 交易订单实体类，订单聚合根 |
| yudao-module-mall/yudao-module-trade/src/main/java/cn/iocoder/yudao/module/trade/service/order/TradeOrderUpdateService.java | 订单更新服务，订单创建和状态流转 |
| yudao-module-mall/yudao-module-trade/src/main/java/cn/iocoder/yudao/module/trade/service/price/TradePriceService.java | 价格计算服务，订单金额计算核心 |
| yudao-module-mall/yudao-module-trade/src/main/java/cn/iocoder/yudao/module/trade/service/aftersale/AfterSaleService.java | 售后服务，退款退货处理 |
| yudao-module-mall/yudao-module-trade-api/src/main/java/cn/iocoder/yudao/module/trade/enums/ErrorCodeConstants.java | 交易模块错误码定义 |

### 促销模块（yudao-module-promotion）

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mall/yudao-module-promotion/src/main/java/cn/iocoder/yudao/module/promotion/dal/dataobject/coupon/CouponTemplateDO.java | 优惠券模板实体类 |
| yudao-module-mall/yudao-module-promotion/src/main/java/cn/iocoder/yudao/module/promotion/dal/dataobject/seckill/SeckillActivityDO.java | 秒杀活动实体类 |
| yudao-module-mall/yudao-module-promotion/src/main/java/cn/iocoder/yudao/module/promotion/dal/dataobject/combination/CombinationActivityDO.java | 拼团活动实体类 |
| yudao-module-mall/yudao-module-promotion/src/main/java/cn/iocoder/yudao/module/promotion/enums/ErrorCodeConstants.java | 促销模块错误码定义 |

### 统计模块（yudao-module-statistics）

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mall/yudao-module-statistics/src/main/java/cn/iocoder/yudao/module/statistics/service/trade/TradeStatisticsService.java | 交易统计服务，订单数据汇总 |

## 领域模型

README 的「数据模型」一节给出了各子模块的数据表清单与关键字段，此处补充其上的聚合根与值对象划分。

### 聚合根

| 聚合根 | 关联实体 | 说明 |
|-------|---------|------|
| ProductSpu（商品SPU） | ProductSku（商品SKU）、ProductCategory（分类）、ProductBrand（品牌）、ProductProperty（属性） | 商品SPU作为聚合根，管理SKU、分类、品牌、属性等关联实体 |
| TradeOrder（交易订单） | TradeOrderItem（订单项）、AfterSale（售后单）、Cart（购物车） | 订单作为交易核心聚合根，管理订单项、售后、购物车等 |
| CouponTemplate（优惠券模板） | Coupon（优惠券） | 优惠券模板管理优惠券的发放和使用 |
| CombinationActivity（拼团活动） | CombinationProduct（拼团商品）、CombinationRecord（拼团记录） | 拼团活动管理拼团商品和拼团参与记录 |

### 值对象

- `ProductSkuDO.Property`（SKU 属性值对象，内嵌于 `product_sku.properties` JSON）
- `AppTradeOrderSettlementRespVO.Address`（订单结算响应中的收货地址 VO）
- 运费模板的计费/包邮规则并非值对象，而是独立实体：`DeliveryExpressTemplateChargeDO`（`trade_delivery_express_template_charge`）、`DeliveryExpressTemplateFreeDO`（`trade_delivery_express_template_free`）

## 设计与架构补充

以下为 Skill 知识库中未被 README 覆盖的设计与架构信息。

### 设计原则补充

在 README「设计原则」之外的两条原则：

- **SPU-SKU 模型**：标准电商商品模型，SPU 为商品标准化单元，SKU 为库存单位
- **订单状态机**：订单状态流转严格遵循状态机模式，确保状态变更可追溯

### 分层结构

各子模块内部的分层职责与代表组件：

| 层 | 职责 | 代表组件 |
|----|------|---------|
| api | 模块间API接口，提供RPC调用能力 | ProductSpuApi/ProductSkuApi（商品信息查询、库存更新）、TradeOrderApi（订单信息查询）、CouponApi（优惠券使用）、SeckillActivityApi/CombinationRecordApi（营销活动验证） |
| controller | HTTP接口，分为管理后台(admin)和用户端(app) | admin/spu/ProductSpuController（商品SPU管理）、admin/order/TradeOrderController（订单管理）、app/spu/AppProductSpuController（商品展示）、app/order/AppTradeOrderController（用户下单） |
| service | 业务逻辑层，核心业务处理 | ProductSpuService/ProductSkuService（商品业务）、TradeOrderUpdateService/TradeOrderQueryService（订单业务）、AfterSaleService（售后业务）、CartService（购物车业务）、CouponService（优惠券业务） |
| dal | 数据访问层，MyBatis-Plus Mapper | ProductSpuMapper/ProductSkuMapper（商品数据访问）、TradeOrderMapper/TradeOrderItemMapper（订单数据访问）、CouponMapper/CouponTemplateMapper（优惠券数据访问） |

### 设计模式补充

README「设计模式」已记录责任链（TradePriceCalculator 价格计算链）、策略（TradeOrderHandler 订单处理分发）与定时任务补偿三类模式，此处补充其余模式的应用：

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 状态模式 | TradeOrderStatusEnum、ProductSpuStatusEnum | 订单状态和商品状态的状态机管理，通过枚举定义状态流转 |
| 模板方法模式 | BaseDO | 数据实体基类，统一处理创建时间、更新时间、删除标记等（mall 全部 49 个 DO 均继承 BaseDO，未使用 TenantBaseDO） |
| 工厂模式 | ProductSpuConvert、TradeOrderConvert | MapStruct 转换器，VO 与 DO 之间的对象转换 |
| 观察者模式 | TradeOrderLogService | 订单操作日志记录，订单状态变更时自动记录日志 |

### 模块间消息通信

mall 未接入任何 MQ 中间件（RocketMQ / Kafka / RabbitMQ）；源码中不存在消息 Topic 与消息生产者。子模块之间以及与其他模块的协作全部是同步 API 调用（见上表「内部依赖」）：例如 trade 在下单/支付链路中直接调用 `ProductSkuApi` 扣减库存、调用 `CouponApi` 核销优惠劵；promotion 通过 `TradeOrderApi.cancelPaidOrder` 取消拼团失败订单。异步能力仅由 Spring `@Async`（如 `sendDeliveryOrderMessage`、`sendCombinationResultMessage`）与合作方回调（pay 模块的 `PayNotifyJob` 回调售后/提现接口）提供，不经过消息中间件。

> 唯一的例外：`promotion/mq/consumer/coupon/CouponTakeByRegisterConsumer` 虽位于 `mq/consumer` 包，但实际使用 Spring `@EventListener`（进程内事件）监听 member 模块发布的 `MemberUserCreateMessage`，在用户注册后 `@Async` 自动发放新人券——它是 Spring 应用事件监听器，不是 MQ 消费者。新增"注册发券"相关逻辑时改这里即可，不要引入真正的 MQ。

### 核心表关系（ER）

| 源表 | 目标表 | 关系 | 外键 | 说明 |
|-----|-------|------|------|------|
| product_spu | product_sku | 1:N | spu_id | 一个SPU对应多个SKU |
| product_spu | product_category | N:1 | category_id | 多个SPU属于一个分类 |
| product_spu | product_brand | N:1 | brand_id | 多个SPU属于一个品牌 |
| trade_order | trade_order_item | 1:N | order_id | 一个订单包含多个订单项 |
| trade_order_item | product_sku | N:1 | sku_id | 订单项关联SKU |
| trade_order | trade_after_sale | 1:N | order_id | 一个订单可能有多个售后单 |
| promotion_coupon_template | promotion_coupon | 1:N | template_id | 一个模板发放多张优惠券 |
