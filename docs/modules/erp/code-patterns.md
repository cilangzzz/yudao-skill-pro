# ERP 进销存代码模式与扩展指南 (erp)

> 本文档移植自模块 Skill 知识库（skill-erp.yaml），提供该模块的代码模式、扩展指南与关键文件索引。模块总体功能、API 接口索引与数据模型详见 [README.md](README.md)。

## 代码模式

以下模式覆盖 Controller / Service / DAL 三层的编码规范与异常、响应约定，示例均取自采购、库存等核心域的标准实现。

### Controller 层

标准注解组合：

- `@Tag(name = "管理后台 - ERP XXX")`：Swagger 接口文档标签
- `@RestController`：RESTful 控制器
- `@RequestMapping("/erp/xxx")`：请求路径前缀
- `@PreAuthorize("@ss.hasPermission('erp:xxx:create')")`：权限控制，权限标识统一为 `erp:{功能}:{操作}`
- `@Validated`：参数校验

以采购订单控制器为例，包含创建、更新状态（审核/反审核）、分页查询三类典型接口：

```java
@Tag(name = "管理后台 - ERP 采购订单")
@RestController
@RequestMapping("/erp/purchase-order")
@Validated
public class ErpPurchaseOrderController {

    @PostMapping("/create")
    @Operation(summary = "创建采购订单")
    @PreAuthorize("@ss.hasPermission('erp:purchase-order:create')")
    public CommonResult<Long> createPurchaseOrder(@Valid @RequestBody ErpPurchaseOrderSaveReqVO createReqVO) {
        return success(purchaseOrderService.createPurchaseOrder(createReqVO));
    }

    @PutMapping("/update-status")
    @Operation(summary = "更新采购订单的状态")
    @PreAuthorize("@ss.hasPermission('erp:purchase-order:update-status')")
    public CommonResult<Boolean> updatePurchaseOrderStatus(@RequestParam("id") Long id,
                                                           @RequestParam("status") Integer status) {
        purchaseOrderService.updatePurchaseOrderStatus(id, status);
        return success(true);
    }

    @GetMapping("/page")
    @Operation(summary = "获得采购订单分页")
    @PreAuthorize("@ss.hasPermission('erp:purchase-order:query')")
    public CommonResult<PageResult<ErpPurchaseOrderRespVO>> getPurchaseOrderPage(@Valid ErpPurchaseOrderPageReqVO pageReqVO) {
        PageResult<ErpPurchaseOrderDO> pageResult = purchaseOrderService.getPurchaseOrderPage(pageReqVO);
        return success(buildPurchaseOrderVOPageResult(pageResult));
    }
}
```

分页接口的固定套路：Service 返回 `PageResult<DO>` 后，Controller 批量查询关联数据（供应商、客户、明细等）并组装为 RespVO，避免 N+1 查询。

### Service 层

Service 接口按功能分组定义：基础 CRUD、状态更新、关联数量回写、存在性校验、明细项查询。

```java
public interface ErpPurchaseOrderService {
    // 基础CRUD
    Long createPurchaseOrder(ErpPurchaseOrderSaveReqVO createReqVO);
    void updatePurchaseOrder(ErpPurchaseOrderSaveReqVO updateReqVO);
    void deletePurchaseOrder(List<Long> ids);
    ErpPurchaseOrderDO getPurchaseOrder(Long id);
    PageResult<ErpPurchaseOrderDO> getPurchaseOrderPage(ErpPurchaseOrderPageReqVO pageReqVO);

    // 状态更新
    void updatePurchaseOrderStatus(Long id, Integer status);

    // 关联更新
    void updatePurchaseOrderInCount(Long id, Map<Long, BigDecimal> inCountMap);
    void updatePurchaseOrderReturnCount(Long orderId, Map<Long, BigDecimal> returnCountMap);

    // 校验方法
    ErpPurchaseOrderDO validatePurchaseOrder(Long id);

    // 订单项查询
    List<ErpPurchaseOrderItemDO> getPurchaseOrderItemListByOrderId(Long orderId);
}
```

实现类固定注入主表 Mapper、子表 Mapper 与 `ErpNoRedisDAO`，创建单据遵循「校验业务数据 → 生成单据号 → 计算合计价格 → 主子表同事务保存」的流程：

```java
@Service
@Validated
public class ErpPurchaseOrderServiceImpl implements ErpPurchaseOrderService {

    @Resource
    private ErpPurchaseOrderMapper purchaseOrderMapper;
    @Resource
    private ErpPurchaseOrderItemMapper purchaseOrderItemMapper;
    @Resource
    private ErpNoRedisDAO noRedisDAO;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long createPurchaseOrder(ErpPurchaseOrderSaveReqVO createReqVO) {
        // 1. 校验业务数据
        List<ErpPurchaseOrderItemDO> items = validatePurchaseOrderItems(createReqVO.getItems());
        supplierService.validateSupplier(createReqVO.getSupplierId());

        // 2. 生成单据号
        String no = noRedisDAO.generate(ErpNoRedisDAO.PURCHASE_ORDER_NO_PREFIX);

        // 3. 计算价格
        ErpPurchaseOrderDO order = BeanUtils.toBean(createReqVO, ErpPurchaseOrderDO.class);
        order.setNo(no).setStatus(ErpAuditStatus.PROCESS.getStatus());
        calculateTotalPrice(order, items);

        // 4. 保存主表和子表
        purchaseOrderMapper.insert(order);
        items.forEach(item -> item.setOrderId(order.getId()));
        purchaseOrderItemMapper.insertBatch(items);

        return order.getId();
    }
}
```

审核/反审核的标准流程（以采购入库为例）：校验存在 → 校验前置状态 → 处理库存联动 → 更新状态。审核通过时按明细逐条创建库存记录，反审核时作废对应库存记录：

```java
// 采购入库审核流程
@Override
@Transactional(rollbackFor = Exception.class)
public void updatePurchaseInStatus(Long id, Integer status) {
    boolean approve = ErpAuditStatus.APPROVE.getStatus().equals(status);
    // 1. 校验存在
    ErpPurchaseInDO purchaseIn = validatePurchaseInExists(id);
    // 2. 校验状态
    if (purchaseIn.getStatus().equals(status)) {
        throw exception(approve ? PURCHASE_IN_APPROVE_FAIL : PURCHASE_IN_PROCESS_FAIL);
    }

    // 3. 更新库存
    if (approve) {
        List<ErpPurchaseInItemDO> items = purchaseInItemMapper.selectListByInId(id);
        items.forEach(item -> {
                // 创建库存记录
                ErpStockRecordCreateReqBO reqBO = new ErpStockRecordCreateReqBO();
                reqBO.setProductId(item.getProductId());
                reqBO.setWarehouseId(purchaseIn.getWarehouseId());
                reqBO.setCount(item.getCount());
                reqBO.setBizType(ErpStockRecordBizTypeEnum.PURCHASE_IN.getType());
                reqBO.setBizId(id);
                reqBO.setBizItemId(item.getId());
                reqBO.setBizNo(purchaseIn.getNo());
                // 更新库存
                stockRecordService.createStockRecord(reqBO);
            });
    } else {
        // 反审核，扣减库存
        stockRecordService.deleteStockRecord(id, ErpStockRecordBizTypeEnum.PURCHASE_IN_CANCEL.getType());
    }

    // 4. 更新状态
    purchaseInMapper.updateById(new ErpPurchaseInDO().setId(id).setStatus(status));
}
```

### DAL 层

Mapper 继承 `BaseMapperX<DO>`，用 `default` 方法封装常用查询：按单号查询、条件分页（`xxIfPresent` 系列方法在条件为空时自动跳过拼接）、带状态条件的更新（配合状态机做乐观并发控制）：

```java
@Mapper
public interface ErpPurchaseOrderMapper extends BaseMapperX<ErpPurchaseOrderDO> {

    default ErpPurchaseOrderDO selectByNo(String no) {
        return selectOne(ErpPurchaseOrderDO::getNo, no);
    }

    default PageResult<ErpPurchaseOrderDO> selectPage(ErpPurchaseOrderPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ErpPurchaseOrderDO>()
                .likeIfPresent(ErpPurchaseOrderDO::getNo, reqVO.getNo())
                .eqIfPresent(ErpPurchaseOrderDO::getStatus, reqVO.getStatus())
                .eqIfPresent(ErpPurchaseOrderDO::getSupplierId, reqVO.getSupplierId())
                .betweenIfPresent(ErpPurchaseOrderDO::getOrderTime, reqVO.getOrderTime())
                .orderByDesc(ErpPurchaseOrderDO::getId));
    }

    default int updateByIdAndStatus(Long id, Integer status, ErpPurchaseOrderDO update) {
        return update(update, new LambdaQueryWrapperX<ErpPurchaseOrderDO>()
                .eq(ErpPurchaseOrderDO::getId, id)
                .eq(ErpPurchaseOrderDO::getStatus, status));
    }
}
```

库存增量更新是本模块最关键的 DAL 模式——通过 `count = count + 变动量` 的原子 SQL 更新库存，不允许负库存时附加 `count >= 扣减量` 的条件过滤实现乐观锁：

```java
// 库存增量更新 - 使用乐观锁避免并发问题
@Mapper
public interface ErpStockMapper extends BaseMapperX<ErpStockDO> {

    default int updateCountIncrement(Long id, BigDecimal count, Boolean negativeEnable) {
        // 如果不允许负库存，需要检查库存是否充足
        if (!negativeEnable) {
            return update(null, new LambdaUpdateWrapper<ErpStockDO>()
                    .setSql("count = count + " + count)
                    .eq(ErpStockDO::getId, id)
                    .ge(count.compareTo(BigDecimal.ZERO) < 0, ErpStockDO::getCount, count.abs()));
        }
        return update(null, new LambdaUpdateWrapper<ErpStockDO>()
                .setSql("count = count + " + count)
                .eq(ErpStockDO::getId, id));
    }
}
```

### 异常处理

错误码前缀：`1-030-xxx-xxx`，统一定义在 `ErrorCodeConstants` 中。典型错误码：

| 错误码 | 说明 | 常量 |
|-----|------|------|
| 1_030_101_000 | 采购订单不存在 | PURCHASE_ORDER_NOT_EXISTS |
| 1_030_101_001 | 采购订单({})已审核，无法删除 | PURCHASE_ORDER_DELETE_FAIL_APPROVE |
| 1_030_101_003 | 审核失败，只有未审核的采购订单才能审核 | PURCHASE_ORDER_APPROVE_FAIL |
| 1_030_404_000 | 操作失败，产品({})所在仓库({})的库存：{}，小于变更数量：{} | STOCK_COUNT_NEGATIVE |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE, args...)`

## 扩展指南

### 新增业务单据类型

1. **创建 DO 实体类**：在 `dal/dataobject/{domain}/` 下创建主表 DO 和子表 DO，继承 `BaseDO`，使用 `@TableName`、`@KeySequence` 注解，定义字段并使用 `@TableId` 标注主键。
2. **创建 Mapper 接口**：在 `dal/mysql/{domain}/` 下创建 Mapper 接口，继承 `BaseMapperX<DO>`，添加自定义查询方法，实现分页查询、按 ID 查询等方法。
3. **创建 Service 层**：在 `service/{domain}/` 下创建 Service 接口和实现类，实现 CRUD、状态更新、业务校验等方法，使用 `@Transactional` 注解保证事务。
4. **创建 Controller 层**：在 `controller/admin/{domain}/` 下创建 Controller，添加 `@Tag`、`@RestController`、`@PreAuthorize` 注解，实现创建、更新、删除、查询、导出等接口。
5. **创建 VO 类**：在 `controller/admin/{domain}/vo/` 下创建：
   - `SaveReqVO`：创建/更新请求 VO
   - `PageReqVO`：分页查询请求 VO
   - `RespVO`：响应 VO
6. **添加单据号前缀**：在 `ErpNoRedisDAO` 中添加单据号前缀常量，格式：X + X + XX（如：CGDD，采购订单）。
7. **添加错误码**：在 `ErrorCodeConstants` 中添加错误码，格式：`1_030_xxx_xxx`。

### 新增库存业务类型

1. **添加业务类型枚举**：在 `ErpStockRecordBizTypeEnum` 中添加新类型，正反向类型需成对定义（正向入库为正数、反向作废为负数，数值段错开）：

```java
NEW_TYPE(90, "新业务类型"),
NEW_TYPE_CANCEL(91, "新业务类型（作废）")
```

2. **创建业务单据**：参考采购入库/销售出库创建对应的业务单据。
3. **在业务审核时创建库存记录**：审核通过时调用 `stockRecordService.createStockRecord()`，反审核时调用 `stockRecordService.deleteStockRecord()`。

### 最佳实践

- **单据状态管理**：所有业务单据使用 `ErpAuditStatus` 枚举管理状态——`PROCESS(10)` 未审核/审核中、`APPROVE(20)` 已审核；状态变更需要校验前置状态和关联数据。
- **主子表更新**：使用 `diffList` 方法对比新旧数据，分别处理新增、修改、删除的子表记录；批量操作使用 `insertBatch`、`updateBatch`、`deleteByIds`。
- **库存操作**：使用 `updateCountIncrement` 增量更新库存，通过乐观锁避免并发问题；每次库存变动都创建 `stock_record` 记录。
- **单据号生成**：使用 `ErpNoRedisDAO.generate()` 生成唯一单据号，格式：前缀 + yyyyMMdd + 6 位自增序号，基于 Redis 保证分布式唯一性。
- **数据关联查询**：分页查询时批量查询关联数据，使用 `convertMap`、`convertMultiMap` 构建映射，避免 N+1 查询问题。

## 模块依赖

内部依赖（仅依赖 yudao-module-system，经 `AdminUserApi` 查询用户昵称用于单据操作人/审核人展示）与 framework starter、下游依赖的完整说明见 [README.md](README.md) 的「依赖关系」一节。第三方依赖：

| 依赖 | 版本 | 用途 |
|-----|------|------|
| MyBatis-Plus | 3.x | ORM 框架，简化数据库操作 |
| Hutool | 5.x | Java 工具类库，日期、集合等工具 |
| Spring Redis | 2.x | Redis 操作，支撑分布式单据号生成 |

## 关键文件

| 分类 | 文件路径 | 说明 |
|-----|---------|------|
| 枚举与常量 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/enums/ErpAuditStatus.java` | 审核状态枚举，定义单据状态流转 |
| 枚举与常量 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/enums/ErrorCodeConstants.java` | 错误码常量，定义所有业务异常 |
| 枚举与常量 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/enums/stock/ErpStockRecordBizTypeEnum.java` | 库存记录业务类型枚举 |
| 核心服务 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/service/purchase/ErpPurchaseOrderServiceImpl.java` | 采购订单服务实现，展示标准业务流程 |
| 核心服务 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/service/stock/ErpStockServiceImpl.java` | 库存服务实现，展示库存增量更新 |
| 核心服务 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/service/stock/ErpStockRecordServiceImpl.java` | 库存记录服务，管理库存变动明细 |
| 数据访问 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/dal/redis/no/ErpNoRedisDAO.java` | 单据号生成器，分布式唯一 ID |
| 数据访问 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/dal/dataobject/purchase/ErpPurchaseOrderDO.java` | 采购订单 DO，展示主表设计 |
| 数据访问 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/dal/dataobject/stock/ErpStockDO.java` | 库存 DO，展示库存表设计 |
| 数据访问 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/dal/dataobject/stock/ErpStockRecordDO.java` | 库存记录 DO，展示库存明细设计 |
| 业务对象 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/service/stock/bo/ErpStockRecordCreateReqBO.java` | 库存记录创建请求 BO，展示值对象设计 |
| 控制器 | `yudao-module-erp/src/main/java/cn/iocoder/yudao/module/erp/controller/admin/purchase/ErpPurchaseOrderController.java` | 采购订单控制器，展示标准 Controller 设计 |

## 领域模型

README 的「数据模型」以表为单位列出全部实体；本节从 DDD 视角补充聚合根与实体的组织关系。

### 聚合根与实体

| 聚合根 | 类型 | 包含实体 | 说明 |
|-----|------|---------|------|
| 采购订单 (ErpPurchaseOrderDO) | 聚合根 | 采购订单项 (ErpPurchaseOrderItemDO)、供应商 (ErpSupplierDO) | 采购域核心聚合，管理采购订单及其明细项 |
| 采购入库 (ErpPurchaseInDO) | 聚合根 | 采购入库项 (ErpPurchaseInItemDO) | 关联采购订单，记录采购入库明细 |
| 采购退货 (ErpPurchaseReturnDO) | 聚合根 | 采购退货项 (ErpPurchaseReturnItemDO) | 关联采购订单，记录采购退货明细 |
| 销售订单 (ErpSaleOrderDO) | 聚合根 | 销售订单项 (ErpSaleOrderItemDO)、客户 (ErpCustomerDO) | 销售域核心聚合，管理销售订单及其明细项 |
| 销售出库 (ErpSaleOutDO) | 聚合根 | 销售出库项 (ErpSaleOutItemDO) | 关联销售订单，记录销售出库明细 |
| 销售退货 (ErpSaleReturnDO) | 聚合根 | 销售退货项 (ErpSaleReturnItemDO) | 关联销售订单，记录销售退货明细 |
| 库存 (ErpStockDO) | 聚合根 | 仓库 (ErpWarehouseDO)、产品 (ErpProductDO) | 库存域核心，记录产品在各仓库的实时库存 |
| 库存记录 (ErpStockRecordDO) | 实体 | — | 记录所有库存变动明细，支持追溯 |
| 付款单 (ErpFinancePaymentDO) | 聚合根 | 付款单项 (ErpFinancePaymentItemDO)、结算账户 (ErpAccountDO) | 财务域付款管理 |
| 收款单 (ErpFinanceReceiptDO) | 聚合根 | 收款单项 (ErpFinanceReceiptItemDO)、结算账户 (ErpAccountDO) | 财务域收款管理 |

### 值对象

- `ErpStockRecordCreateReqBO`：库存记录创建请求 BO，封装库存变动所需的业务信息（产品、仓库、数量、业务类型与业务单据回链），是 8 类出入库单据统一记账的入参载体。

### 领域服务

| 领域服务 | 说明 |
|-----|------|
| ErpPurchaseOrderService | 采购订单领域服务，管理采购订单生命周期 |
| ErpSaleOrderService | 销售订单领域服务，管理销售订单生命周期 |
| ErpStockService | 库存领域服务，管理库存变动 |
| ErpStockRecordService | 库存记录领域服务，记录库存变动明细 |

## 设计与架构补充

以下为 README 未覆盖的设计原则与架构细节，已覆盖部分（业务定位、主子表、两态审核状态机、表结构等）不再重复。

### 分层结构

```
cn.iocoder.yudao.module.erp
├── controller/admin/    # HTTP 接口层：请求响应、参数校验、权限控制（各 Controller 见 README「API 接口索引」）
├── service/             # 业务逻辑层：领域服务、事务管理、业务规则校验，按域分包
│   ├── purchase/        # 采购域（订单、入库、退货、供应商）
│   ├── sale/            # 销售域（订单、出库、退货、客户）
│   ├── stock/           # 库存域（库存、仓库、入库、出库、调拨、盘点、记录）
│   ├── finance/         # 财务域（账户、付款、收款）
│   ├── product/         # 产品域（产品、分类、单位）
│   └── statistics/      # 统计服务（采购统计、销售统计）
└── dal/                 # 数据访问层
    ├── dataobject/      # DO 实体类（按业务域分包）
    ├── mysql/           # MyBatis Mapper 接口
    └── redis/           # Redis 操作（单据号生成 ErpNoRedisDAO）
```

### 设计原则补充

- **库存增量更新**：库存变动一律采用 `ErpStockMapper.updateCountIncrement` 增量更新（`count = count + 变动量` 的原子 SQL），不允许负库存时通过附加 `count >= 扣减量` 条件实现乐观锁，避免并发下的超扣（示例见上文 DAL 层）。
- **单据号生成器**：基于 Redis 的分布式单据号生成（`ErpNoRedisDAO`），格式为「前缀 + yyyyMMdd + 6 位自增序号」，保证分布式环境下单据号的唯一性与有序性。
- **审核权限控制与关联校验的落地方式**：已审核单据不可修改/删除，需反审核后才能操作；单据间的关联关系（如订单 → 入库 → 退货）在删除/反审核时通过查询下游单据是否存在进行校验，订单项上的 `inCount`/`outCount`/`returnCount` 累计字段用于数量联动控制。

### 单据号前缀一览

各业务单据的单号前缀（格式均为「前缀 + yyyyMMdd + 6 位序号」）：

| 单据 | 前缀 |
|-----|------|
| 采购订单 | CGDD |
| 销售订单 | XSDD |
| 其它入库单 | QTRK |
| 其它出库单 | QCKD |
| 库存调拨单 | QCDB |
| 库存盘点单 | QCPD |
| 付款单 | FKD |
| 收款单 | SKD |

采购入库/退货、销售出库/退货等其余单据的前缀以 `ErpNoRedisDAO` 中的常量定义为准。

### 模块间通信

- 不对外提供跨模块 API 接口，也不使用消息队列（无 MQ 生产/消费）。
- 对 system 模块仅通过 `AdminUserApi` 获取用户信息，用于显示单据操作人/审核人姓名。
