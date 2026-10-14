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
| 1_011_000_017 | 交易订单发货失败，订单不是【待发货】状态 | trade |
| 1_013_004_000 | 优惠劵模板不存在 | promotion |
| 1_013_008_006 | 秒杀失败，原因：秒杀库存不足 | promotion |

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
| yudao-module-member | MemberUserApi | 获取会员信息，用于订单关联用户 |
| yudao-module-pay | PayOrderApi | 创建支付订单，处理支付回调 |
| yudao-module-system | AreaApi | 获取地区信息，用于收货地址 |

### 外部依赖（第三方库）

| 依赖 | 版本 | 用途 |
|-----|------|------|
| MyBatis-Plus | 3.x | ORM 框架，简化数据库操作 |
| MapStruct | 1.x | 对象映射，VO 与 DO 转换 |
| Spring Validation | 2.x | 参数校验 |
| Swagger/OpenAPI | 3.x | API 文档生成 |
| Redis | 6.x | 缓存、分布式锁、库存扣减 |

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

- ProductSkuDO.Property（SKU属性值对象）
- TradeOrderDO.Address（收货地址值对象）
- DeliveryExpressTemplateCharge（运费模板计费规则）

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
| 模板方法模式 | BaseDO、TenantBaseDO | 数据实体基类，统一处理创建时间、更新时间、删除标记等 |
| 工厂模式 | ProductSpuConvert、TradeOrderConvert | MapStruct 转换器，VO 与 DO 之间的对象转换 |
| 观察者模式 | TradeOrderLogService | 订单操作日志记录，订单状态变更时自动记录日志 |

### 模块间消息通信

| Topic | 用途 |
|-------|------|
| order.paid | 订单支付成功消息，触发积分发放、优惠券赠送等 |
| order.delivered | 订单发货消息，通知用户 |

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
