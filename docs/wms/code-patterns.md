# WMS 仓储管理代码模式与扩展指南 (wms)

> 本文档移植自模块 Skill 知识库（skill-wms.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

标准注解组合：

- `@Tag(name = "管理后台 - xxx")` - Swagger 文档标签
- `@RestController` - REST 控制器
- `@RequestMapping("/wms/xxx")` - 请求路径前缀
- `@Validated` - 参数校验
- `@PreAuthorize("@ss.hasPermission('wms:xxx:action')")` - 权限控制

示例（入库单 Controller，含「完成入库」动作接口）：

```java
@Tag(name = "管理后台 - 入库单")
@RestController
@RequestMapping("/wms/receipt-order")
@Validated
public class ReceiptOrderController {
    @Resource
    private ReceiptOrderService receiptOrderService;

    @PostMapping("/create")
    @Operation(summary = "创建入库单")
    @PreAuthorize("@ss.hasPermission('wms:receipt-order:create')")
    public CommonResult<Long> createReceiptOrder(@Valid @RequestBody ReceiptOrderSaveReqVO reqVO) {
        return success(receiptOrderService.createReceiptOrder(reqVO));
    }

    @PutMapping("/complete")
    @Operation(summary = "完成入库")
    @PreAuthorize("@ss.hasPermission('wms:receipt-order:update')")
    public CommonResult<Boolean> completeReceiptOrder(@RequestParam("id") Long id) {
        receiptOrderService.completeReceiptOrder(id);
        return success(true);
    }
}
```

### Service 层规范

接口模式：`XxxService` 接口定义业务方法，`XxxServiceImpl` 实现类。

实现模式骨架：

```java
@Service
@Validated
public class XxxServiceImpl implements XxxService {
    @Resource
    private XxxMapper xxxMapper;

    // 使用 static final 定义常量
    // 使用 @Transactional 注解控制事务
    // 使用 validateXxxExists 方法校验存在性
    // 使用 exception(ErrorCode) 抛出业务异常
}
```

示例（入库单完成逻辑：校验状态 → 按明细增加库存 → 更新单据状态）：

```java
@Service
public class ReceiptOrderServiceImpl implements ReceiptOrderService {
    @Resource
    private ReceiptOrderMapper receiptOrderMapper;
    @Resource
    private ReceiptOrderDetailMapper receiptOrderDetailMapper;
    @Resource
    private InventoryService inventoryService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void completeReceiptOrder(Long id) {
        // 1. 校验单据存在且状态为 PREPARE
        ReceiptOrderDO order = receiptOrderMapper.selectById(id);
        validateReceiptOrderCanComplete(order);

        // 2. 遍历明细行，增加库存
        List<ReceiptOrderDetailDO> details = receiptOrderDetailMapper.selectListByOrderId(id);
        for (ReceiptOrderDetailDO detail : details) {
            inventoryService.addStock(detail.getSkuId(), order.getWarehouseId(),
                detail.getQuantity(), detail.getPrice(),
                WmsOrderTypeConstants.RECEIPT_ORDER_TYPE, order.getId(), order.getNo());
        }

        // 3. 更新单据状态为 FINISHED
        receiptOrderMapper.updateById(new ReceiptOrderDO().setId(id)
            .setStatus(OrderStatusEnum.FINISHED.getStatus()));
    }
}
```

### 数据访问（DAL）规范

Mapper 继承 `BaseMapperX` 获得通用 CRUD 方法，自定义查询使用 `@Select` 注解或 XML，分页查询返回 `PageResult<XxxDO>`：

```java
public interface XxxMapper extends BaseMapperX<XxxDO> {
    // 继承 BaseMapperX 获得通用 CRUD 方法
    // 自定义查询方法使用 @Select 注解或 XML
    // 分页查询返回 PageResult<XxxDO>
}
```

示例（库存分页查询，条件为空时不拼接）：

```java
public interface InventoryMapper extends BaseMapperX<InventoryDO> {
    default PageResult<InventoryDO> selectPage(InventoryPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<InventoryDO>()
                .eqIfPresent(InventoryDO::getSkuId, reqVO.getSkuId())
                .eqIfPresent(InventoryDO::getWarehouseId, reqVO.getWarehouseId())
                .orderByDesc(InventoryDO::getId));
    }
}
```

### 库存并发安全模式

库存更新使用 `SELECT ... FOR UPDATE` 行锁 + `DuplicateKeyException` 捕获实现并发安全，并在同一事务内写入库存变动历史：

```java
@Service
public class InventoryServiceImpl implements InventoryService {
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void addStock(Long skuId, Long warehouseId, BigDecimal quantity,
                        BigDecimal price, Integer sourceOrderType,
                        Long sourceOrderId, String sourceOrderNo) {
        // 1. 查询库存记录（带行锁）
        InventoryDO inventory = inventoryMapper.selectBySkuIdAndWarehouseIdForUpdate(skuId, warehouseId);

        BigDecimal beforeQuantity;
        if (inventory == null) {
            // 2. 首次入库，尝试插入（懒初始化）
            try {
                inventory = new InventoryDO().setSkuId(skuId)
                    .setWarehouseId(warehouseId).setQuantity(quantity).setPrice(price);
                inventoryMapper.insert(inventory);
                beforeQuantity = BigDecimal.ZERO;
            } catch (DuplicateKeyException e) {
                // 3. 并发插入冲突，重新查询
                inventory = inventoryMapper.selectBySkuIdAndWarehouseIdForUpdate(skuId, warehouseId);
                beforeQuantity = inventory.getQuantity();
                inventory.setQuantity(beforeQuantity.add(quantity));
                inventoryMapper.updateById(inventory);
            }
        } else {
            // 4. 已有记录，直接更新
            beforeQuantity = inventory.getQuantity();
            inventory.setQuantity(beforeQuantity.add(quantity));
            inventoryMapper.updateById(inventory);
        }

        // 5. 记录库存变动历史
        inventoryHistoryService.createHistory(skuId, warehouseId,
            beforeQuantity, inventory.getQuantity(), quantity, price,
            sourceOrderType, sourceOrderId, sourceOrderNo);
    }
}
```

### 异常处理

wms 模块错误码需遵循项目统一的错误码分配规则。典型业务异常消息：

- 物料不存在
- 仓库不存在
- 商户不存在
- SKU 不存在
- 库存不足
- 单据状态不允许操作
- 品牌存在关联数据不允许删除
- 分类存在子分类不允许删除

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ErrorCode)`

## 扩展指南

### 新增仓储单据类型

1. **分配订单类型常量**：在 `WmsOrderTypeConstants` 中分配新的类型范围

```java
// 示例：新增调拨单，类型范围 [500, 600)
public static final int TRANSFER_ORDER_TYPE_BEGIN = 500;
public static final int TRANSFER_ORDER_TYPE_END = 600;
```

2. **创建单据头和明细表**：创建主子表，单据头包含 no、warehouse_id、status 等字段

```sql
CREATE TABLE wms_transfer_order (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  no VARCHAR(64) NOT NULL,
  warehouse_id BIGINT NOT NULL,
  status TINYINT NOT NULL DEFAULT 0,
  remark VARCHAR(512),
  -- BaseDO 字段
  creator VARCHAR(64), create_time DATETIME, updater VARCHAR(64),
  update_time DATETIME, deleted BIT DEFAULT 0,
  UNIQUE KEY uk_no (no)
);
```

3. **创建 DO、Mapper、Service、Controller**：按照既有模式创建完整的 CRUD 代码
4. **实现完成/取消逻辑**：在 Service 中实现单据完成时的库存变更逻辑
5. **添加权限配置**：在系统中配置权限标识 `wms:transfer-order:{action}`

### 扩展物料属性

1. **添加字段到 wms_item 或 wms_item_sku**：根据属性粒度决定添加到物料表还是 SKU 表
2. **更新 DO 类**：在对应的 DO 类中添加字段
3. **更新 VO 类**：在 SaveReqVO 和 RespVO 中添加字段
4. **更新 Controller 和 Service**：确保新字段在 CRUD 流程中正确处理
5. **更新 Excel 导出模板**：在导出 VO 中添加 `@ExcelProperty` 注解

### 最佳实践

- **库存更新必须使用行锁**：所有库存更新操作必须使用 `SELECT ... FOR UPDATE` 行锁，避免并发更新丢失
- **单据完成操作使用事务**：单据完成涉及状态更新、库存变更、历史记录，必须在同一事务中完成
- **VO 组装使用批量查询**：通过 `AdminUserApi.getUserMap()` 等批量查询避免 N+1 问题
- **单据操作前校验状态**：完成、取消、更新、删除操作前必须校验单据状态为 PREPARE
- **订单类型常量分段管理**：新单据类型必须在 `WmsOrderTypeConstants` 中分配范围，避免类型冲突
- **SKU 作为库存单位**：库存以 SKU + 仓库维度管理，物料级别不跟踪库存
- **分类树一次性加载**：分类查询建议一次性加载所有数据到内存后构建树，避免递归查询数据库
- **Excel 导出控制数据量**：大数据量导出使用 EasyExcel 流式写入，避免内存溢出

## 模块依赖

内部依赖（其他模块）：

| 模块 | 用途 |
|------|------|
| yudao-module-system | AdminUserApi - 批量获取用户信息用于 VO 组装 |
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |

外部依赖（第三方库）：

| 依赖 | 用途 |
|------|------|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| Hutool | Java 工具类库 |
| Swagger/OpenAPI | API 文档注解 |
| Apache POI / EasyExcel | Excel 导入导出 |

模块间通信仅依赖 system 模块的 `AdminUserApi`，无 MQ 依赖；framework starter 明细与下游依赖方（yudao-server）见 [README](README.md) 的「依赖关系」一节。

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/inventory/InventoryServiceImpl.java | 库存服务实现，核心库存变更逻辑（并发安全） |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/inventory/InventoryHistoryServiceImpl.java | 库存历史服务，记录每笔库存变动 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/receiptorder/ReceiptOrderServiceImpl.java | 入库单服务实现，完成入库触发库存增加 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/shipmentorder/ShipmentOrderServiceImpl.java | 出库单服务实现，完成出库触发库存减少 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/movementorder/MovementOrderServiceImpl.java | 移库单服务实现，完成移库触发双向库存变更 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/checkorder/CheckOrderServiceImpl.java | 盘点单服务实现，完成盘点触发库存调整 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/item/ItemServiceImpl.java | 物料服务实现，包含 SKU 嵌入管理 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/dal/mysql/inventory/InventoryMapper.java | 库存 Mapper，含 FOR UPDATE 查询方法 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/enums/WmsOrderTypeConstants.java | 订单类型常量，定义各单据类型范围 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/enums/ErrorCodeConstants.java | 错误码常量定义 |

## 领域模型

聚合根与聚合：

| 聚合 | 聚合根/实体 | 说明 |
|------|------------|------|
| 物料聚合 | ItemDO、ItemSkuDO、ItemBrandDO、ItemCategoryDO | ItemDO 是物料聚合根，ItemSkuDO 是物料的多规格 SKU，ItemBrandDO 和 ItemCategoryDO 是物料的品牌和分类维度 |
| 商户聚合 | MerchantDO | 商户聚合根，管理客户和供应商信息 |
| 仓库聚合 | WarehouseDO | 仓库聚合根，管理仓库基本信息 |
| 库存聚合 | InventoryDO、InventoryHistoryDO | InventoryDO 以 SKU + 仓库为唯一维度管理库存余额，InventoryHistoryDO 记录每笔库存变动 |
| 入库单聚合 | ReceiptOrderDO、ReceiptOrderDetailDO | ReceiptOrderDO 是入库单聚合根，ReceiptOrderDetailDO 是入库明细行，一对多关系 |
| 出库单聚合 | ShipmentOrderDO、ShipmentOrderDetailDO | ShipmentOrderDO 是出库单聚合根，ShipmentOrderDetailDO 是出库明细行，一对多关系 |
| 移库单聚合 | MovementOrderDO、MovementOrderDetailDO | MovementOrderDO 是移库单聚合根，MovementOrderDetailDO 是移库明细行，一对多关系 |
| 盘点单聚合 | CheckOrderDO、CheckOrderDetailDO | CheckOrderDO 是盘点单聚合根，CheckOrderDetailDO 是盘点明细行，一对多关系 |

值对象：

| 对象 | 说明 |
|------|------|
| WmsOrderTypeConstants | 订单类型常量，定义各单据类型范围，用于库存历史来源标识 |
| OrderStatusEnum | 单据状态枚举：PREPARE(0), FINISHED(4), CANCELED(5) |

领域服务：

| 服务 | 说明 |
|------|------|
| ItemService | 物料管理服务，提供物料及 SKU 的 CRUD 操作 |
| ItemBrandService | 品牌管理服务 |
| ItemCategoryService | 分类管理服务，支持树形结构操作 |
| MerchantService | 商户管理服务 |
| WarehouseService | 仓库管理服务 |
| InventoryService | 库存管理服务，提供库存查询和变更方法 |
| InventoryHistoryService | 库存历史服务，记录每笔库存变动 |
| ReceiptOrderService | 入库单管理服务 |
| ShipmentOrderService | 出库单管理服务 |
| MovementOrderService | 移库单管理服务 |
| CheckOrderService | 盘点单管理服务 |

## 设计与架构补充

[README](README.md) 已记录单据驱动库存、单据状态机、并发安全、明细整体维护、只读统计分离等设计原则与三大设计模式，本节补充其余内容。

### 分层架构

| 层 | 职责 | 说明 |
|----|------|------|
| api | 模块间 API 接口，供其他模块 RPC 调用 | 当前无对外暴露的 API 组件 |
| controller | HTTP 接口层，提供 RESTful API | 覆盖主数据、库存（只读）、四大单据及明细、首页统计，接口明细见 [README](README.md) 的 API 接口索引 |
| service | 业务逻辑层 | item（物料/SKU）、item-brand、item-category、merchant、warehouse、inventory（库存 + 库存历史）及四大单据服务，见 [README](README.md) 的核心功能点 |
| dal | 数据访问层 | dataobject（DO 实体类定义）、mysql（MyBatis Mapper 接口） |
| enums | 枚举和常量定义 | WmsOrderTypeConstants（订单类型常量）、ErrorCodeConstants（错误码常量）、OrderStatusEnum（单据状态枚举） |

### 设计原则与设计模式补充

| 原则/模式 | 说明 |
|-----------|------|
| 订单类型常量分段 | `WmsOrderTypeConstants` 定义订单类型范围：入库 [100,200)、出库 [200,300)，用于库存历史来源标识 |
| SKU 作为库存单位 | 库存以 SKU + 仓库维度跟踪，不跟踪物料级别库存，支持多规格管理 |
| 字典集成 | 单据状态、子类型等使用系统字典管理 |
| 细粒度权限控制 | 权限标识格式 `wms:{entity}:{action}`，如 `wms:receipt-order:create` |
| 单据头/明细模式 | 应用位置：`service/*-order/`。所有四大单据采用 Header + Detail 主子表结构，单据头存储汇总信息，明细行存储 SKU 级别数据 |
| VO 组装模式 | 应用位置：各 `XxxServiceImpl`。通过批量查询关联实体到 Map 中，再通过 `BeanUtils.toBean()` 丰富 VO 对象，避免 N+1 查询 |

### 表关系（ER）

| 来源表 | 关联表 | 关系 | 外键 | 说明 |
|--------|--------|------|------|------|
| wms_item | wms_item_category | N:1 | category_id | 物料归属分类 |
| wms_item | wms_item_brand | N:1 | brand_id | 物料归属品牌 |
| wms_item_sku | wms_item | N:1 | item_id | SKU 归属物料 |
| wms_inventory | wms_item_sku | N:1 | sku_id | 库存归属 SKU |
| wms_inventory | wms_warehouse | N:1 | warehouse_id | 库存归属仓库 |
| wms_inventory_history | wms_item_sku | N:1 | sku_id | 流水归属 SKU |
| wms_inventory_history | wms_warehouse | N:1 | warehouse_id | 流水归属仓库 |
| wms_receipt_order | wms_warehouse | N:1 | warehouse_id | 入库单归属仓库 |
| wms_receipt_order | wms_merchant | N:1 | merchant_id | 入库单关联商户 |
| wms_receipt_order_detail | wms_receipt_order | N:1 | order_id | 入库明细归属单据 |
| wms_receipt_order_detail | wms_item_sku | N:1 | sku_id | 入库明细关联 SKU |
| wms_shipment_order | wms_warehouse | N:1 | warehouse_id | 出库单归属仓库 |
| wms_shipment_order | wms_merchant | N:1 | merchant_id | 出库单关联商户 |
| wms_shipment_order_detail | wms_shipment_order | N:1 | order_id | 出库明细归属单据 |
| wms_shipment_order_detail | wms_item_sku | N:1 | sku_id | 出库明细关联 SKU |
| wms_movement_order | wms_warehouse | N:1 | from_warehouse_id | 源仓库 |
| wms_movement_order | wms_warehouse | N:1 | to_warehouse_id | 目标仓库 |
| wms_movement_order_detail | wms_movement_order | N:1 | order_id | 移库明细归属单据 |
| wms_movement_order_detail | wms_item_sku | N:1 | sku_id | 移库明细关联 SKU |
| wms_check_order | wms_warehouse | N:1 | warehouse_id | 盘点单归属仓库 |
| wms_check_order_detail | wms_check_order | N:1 | order_id | 盘点明细归属单据 |
| wms_check_order_detail | wms_item_sku | N:1 | sku_id | 盘点明细关联 SKU |

### 唯一约束与关键索引

| 表 | 索引 | 类型 | 说明 |
|----|------|------|------|
| wms_item | uk_code (code) | 唯一 | 物料编码唯一 |
| wms_warehouse | uk_code (code) | 唯一 | 仓库编码唯一 |
| wms_inventory | uk_sku_warehouse (sku_id, warehouse_id) | 唯一 | 库存以 SKU + 仓库唯一，是并发懒初始化的兜底依据 |
| 四大单据表（receipt/shipment/movement/check_order） | uk_no (no) | 唯一 | 单据号唯一 |
| wms_inventory_history | idx_source_order (source_order_type, source_order_id) | 普通 | 支持按来源单据追溯库存流水 |
| wms_item / wms_item_sku / 四大单据明细表 | idx_category_id、idx_brand_id、idx_item_id、idx_order_id 等 | 普通 | 外键查询加速 |
