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
public class WmsReceiptOrderController {
    @Resource
    private WmsReceiptOrderService receiptOrderService;

    @PostMapping("/create")
    @Operation(summary = "创建入库单")
    @PreAuthorize("@ss.hasPermission('wms:receipt-order:create')")
    public CommonResult<Long> createReceiptOrder(@Valid @RequestBody WmsReceiptOrderSaveReqVO reqVO) {
        return success(receiptOrderService.createReceiptOrder(reqVO));
    }

    @PutMapping("/complete")
    @Operation(summary = "完成入库")
    @PreAuthorize("@ss.hasPermission('wms:receipt-order:complete')")
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

示例（入库单完成逻辑：校验状态 → CAS 更新单据状态 → 按明细写入库存）：

```java
@Service
public class WmsReceiptOrderServiceImpl implements WmsReceiptOrderService {
    @Resource
    private WmsReceiptOrderMapper receiptOrderMapper;
    @Resource
    private WmsReceiptOrderDetailService receiptOrderDetailService;
    @Resource
    private WmsInventoryService inventoryService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void completeReceiptOrder(Long id) {
        // 1. 校验单据存在，且状态为 PREPARE
        WmsReceiptOrderDO order = validateReceiptOrderPrepare(id);
        List<WmsReceiptOrderDetailDO> details =
                receiptOrderDetailService.validateReceiptOrderDetailListExists(id);

        // 2. 状态 CAS 更新为 FINISHED（并发重复完成时更新行数为 0，抛 RECEIPT_ORDER_STATUS_NOT_PREPARE）
        if (receiptOrderMapper.updateByIdAndStatus(id, WmsOrderStatusEnum.PREPARE.getStatus(),
                new WmsReceiptOrderDO().setStatus(WmsOrderStatusEnum.FINISHED.getStatus())) == 0) {
            throw exception(RECEIPT_ORDER_STATUS_NOT_PREPARE);
        }

        // 3. 按明细写入库存（统一入口 changeInventory，内部加行锁并写库存流水）
        List<WmsInventoryChangeReqDTO.Item> items = convertList(details,
                detail -> BeanUtils.toBean(detail, WmsInventoryChangeReqDTO.Item.class));
        inventoryService.changeInventory(new WmsInventoryChangeReqDTO()
                .setOrderId(order.getId()).setOrderNo(order.getNo())
                .setOrderType(WmsOrderTypeEnum.RECEIPT.getType()).setItems(items));
    }
}
```

### 数据访问（DAL）规范

Mapper 继承 `BaseMapperX` 获得通用 CRUD 方法；自定义查询使用 `default` 方法 + `LambdaQueryWrapperX / MPJLambdaWrapperX`（条件为空不拼接），跨方言的复杂统计 SQL 使用 XML（如 `WmsHomeStatisticsMapper.xml`），分页查询返回 `PageResult<XxxDO>`：

```java
public interface XxxMapper extends BaseMapperX<XxxDO> {
    // 继承 BaseMapperX 获得通用 CRUD 方法
    // 自定义查询方法使用 default 方法 + LambdaQueryWrapperX / MPJLambdaWrapperX
    // 分页查询返回 PageResult<XxxDO>
}
```

示例（库存分页查询，MPJ 联表 + 条件为空时不拼接）：

```java
public interface WmsInventoryMapper extends BaseMapperX<WmsInventoryDO> {
    default PageResult<WmsInventoryDO> selectPage(WmsInventoryPageReqVO reqVO) {
        MPJLambdaWrapperX<WmsInventoryDO> query = new MPJLambdaWrapperX<WmsInventoryDO>()
                .selectAll(WmsInventoryDO.class)
                .innerJoin(WmsItemSkuDO.class, WmsItemSkuDO::getId, WmsInventoryDO::getSkuId)
                .innerJoin(WmsItemDO.class, WmsItemDO::getId, WmsItemSkuDO::getItemId)
                .likeIfPresent(WmsItemDO::getCode, reqVO.getItemCode())
                .likeIfPresent(WmsItemDO::getName, reqVO.getItemName())
                .eqIfPresent(WmsInventoryDO::getSkuId, reqVO.getSkuId())
                .eqIfPresent(WmsInventoryDO::getWarehouseId, reqVO.getWarehouseId());
        // 按统计维度决定排序（warehouse / item，未知维度抛 IllegalArgumentException）
        appendDimensionOrder(query, reqVO.getType());
        return selectJoinPage(reqVO, WmsInventoryDO.class, query);
    }
}
```

### 框架能力：统计 SQL 方言适配（`SqlDialectUtils`）

首页/统计类手写 XML SQL 中的 MySQL 专有语法改用框架 `SqlDialectUtils` 生成方言片段（`WmsHomeStatisticsMapper.xml`）：日期格式化用 `${@...SqlDialectUtils@formatDate('create_time')}` 替换 `DATE_FORMAT`，行数限制用 `${@...SqlDialectUtils@limitParam('limit', true)}` 替换 `LIMIT`。它按当前执行时路由到的数据源动态判定方言并按数据源实例缓存，MySQL 下输出与原 SQL 等价，PostgreSQL / Oracle / SQL Server 2012+ 输出对应写法。注意 `limitParam` 的参数名必须是 Mapper 方法里真实存在的 `@Param`；统计结果 `Map` 的 key 依赖 SQL 别名（如 `statDate`），改片段时保持别名一致。详见 pitfalls 6.1。

### 库存并发安全模式

库存更新使用框架行锁（`BaseMapperX#selectOneForUpdate / selectListForUpdate`，内部按当前方言生成锁定语义）+ `DuplicateKeyException` 捕获实现并发安全，并在同一事务内写入库存变动历史。`WmsInventoryMapper#selectByIdForUpdate / selectListByIdsForUpdate` 即对这两个框架方法的封装（不再自行拼接 `.last("FOR UPDATE")`）：

```java
@Service
public class WmsInventoryServiceImpl implements WmsInventoryService {
    @Resource
    private WmsInventoryMapper inventoryMapper;
    @Resource
    private WmsInventoryHistoryService inventoryHistoryService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changeInventory(WmsInventoryChangeReqDTO reqDTO) {
        // 1. 补齐缺失的库存行：insert 撞唯一索引时回查已有行
        List<WmsInventoryDO> inventories = getOrCreateInventoryList(reqDTO.getItems());
        // 2. 按库存 ID 批量加行锁（委托 BaseMapperX#selectListForUpdate，按方言生成锁定语义）
        inventories = inventoryMapper.selectListByIdsForUpdate(
                convertSet(inventories, WmsInventoryDO::getId));

        // 3. 加锁后计算前后数量、校验库存充足，再批量更新库存
        //    beforeQuantity/afterQuantity 同时用于写入库存流水
        ...
        inventoryMapper.updateBatch(...);

        // 4. 同一事务内写入库存变动历史
        inventoryHistoryService.createInventoryHistoryList(histories);
    }
}
```

> 注意：`selectByIdForUpdate` / `selectListByIdsForUpdate` 必须在 `@Transactional` 方法内调用，否则锁随语句结束释放；不要自行拼接 `.last("FOR UPDATE")`。框架内部按方言生成锁定语义（标准数据库为 `FOR UPDATE`，SQL Server 不支持 `FOR UPDATE`/`LIMIT`，由 `ForUpdateInnerInterceptor` 改写），自行拼接会绕过这套适配。

### 异常处理

wms 模块错误码需遵循项目统一的错误码分配规则。典型业务异常消息：

- 商品不存在
- 仓库不存在
- 往来企业不存在
- 商品规格不存在
- 库存不足
- 单据状态不是草稿，不能操作
- 删除失败！品牌已被商品使用！
- 删除失败！请先删除该分类下的子分类！

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ErrorCode)`

## 扩展指南

### 新增仓储单据类型

1. **分配订单类型常量**：在 `WmsOrderTypeConstants` 中分配新的类型范围

```java
// 示例：新增调拨单，沿用分段注释，类型值落在 [500, 600) 区间；每个子类型一个常量
// ========== 调拨单类型 [500, 600) ==========

public static final int TRANSFER_NORMAL = 500; // 普通调拨：WmsTransferOrderDO（示例，需新建）
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

### 扩展商品属性

1. **添加字段到 wms_item 或 wms_item_sku**：根据属性粒度决定添加到商品表还是 SKU 表
2. **更新 DO 类**：在对应的 DO 类中添加字段
3. **更新 VO 类**：在 SaveReqVO 和 RespVO 中添加字段
4. **更新 Controller 和 Service**：确保新字段在 CRUD 流程中正确处理
5. **更新 Excel 导出模板**：在导出 VO 中添加 `@ExcelProperty` 注解

### 最佳实践

- **库存更新必须使用行锁**：库存变更与盘库完成统一通过 `WmsInventoryMapper#selectByIdForUpdate / selectListByIdsForUpdate`（委托框架 `BaseMapperX#selectOneForUpdate / selectListForUpdate`）加行锁，且必须在事务内调用，避免并发更新丢失
- **单据完成操作使用事务**：单据完成涉及状态更新、库存变更、历史记录，必须在同一事务中完成
- **VO 组装使用批量查询**：通过 `AdminUserApi.getUserMap()` 等批量查询避免 N+1 问题
- **单据操作前校验状态**：完成、作废、更新操作前必须校验单据状态为 PREPARE；删除允许 PREPARE/CANCELED（对应 `*_ORDER_STATUS_NOT_DELETABLE`）
- **订单类型常量分段管理**：新单据类型必须在 `WmsOrderTypeConstants` 中分配范围，避免类型冲突
- **SKU 作为库存单位**：库存以 SKU + 仓库维度管理，商品级别不跟踪库存
- **分类树一次性加载**：分类查询建议一次性加载所有数据到内存后构建树，避免递归查询数据库
- **Excel 导出注意数据量**：导出统一用 `ExcelUtils.write(response, 文件名, 表名, XxxRespVO.class, list)`；导出前会把分页大小置为 `PAGE_SIZE_NONE` 一次性查出全部数据再写入内存，数据量大时需自行分片导出，避免内存溢出

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
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/inventory/WmsInventoryServiceImpl.java | 库存服务实现，核心库存变更逻辑（并发安全） |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/inventory/WmsInventoryHistoryServiceImpl.java | 库存历史服务，记录每笔库存变动 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/order/receipt/WmsReceiptOrderServiceImpl.java | 入库单服务实现，完成入库触发库存增加 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/order/shipment/WmsShipmentOrderServiceImpl.java | 出库单服务实现，完成出库触发库存减少 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/order/movement/WmsMovementOrderServiceImpl.java | 移库单服务实现，完成移库触发双向库存变更 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/order/check/WmsCheckOrderServiceImpl.java | 盘点单服务实现，完成盘点触发库存调整 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/service/md/item/WmsItemServiceImpl.java | 商品服务实现，包含 SKU 嵌入管理 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/dal/mysql/inventory/WmsInventoryMapper.java | 库存 Mapper，含 selectByIdForUpdate / selectListByIdsForUpdate（委托框架锁定读） |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/enums/order/WmsOrderTypeConstants.java | 订单子类型常量，按业务域分段定义各单据 type 取值 |
| yudao-module-wms/src/main/java/cn/iocoder/yudao/module/wms/enums/ErrorCodeConstants.java | 错误码常量定义 |

## 领域模型

聚合根与聚合：

| 聚合 | 聚合根/实体 | 说明 |
|------|------------|------|
| 商品聚合 | WmsItemDO、WmsItemSkuDO、WmsItemBrandDO、WmsItemCategoryDO | WmsItemDO 是商品聚合根，WmsItemSkuDO 是商品的多规格 SKU，WmsItemBrandDO 和 WmsItemCategoryDO 是商品的品牌和分类维度 |
| 商户聚合 | WmsMerchantDO | 商户聚合根，管理客户和供应商信息 |
| 仓库聚合 | WmsWarehouseDO | 仓库聚合根，管理仓库基本信息 |
| 库存聚合 | WmsInventoryDO、WmsInventoryHistoryDO | WmsInventoryDO 以 SKU + 仓库为唯一维度管理库存余额，WmsInventoryHistoryDO 记录每笔库存变动 |
| 入库单聚合 | WmsReceiptOrderDO、WmsReceiptOrderDetailDO | WmsReceiptOrderDO 是入库单聚合根，WmsReceiptOrderDetailDO 是入库明细行，一对多关系 |
| 出库单聚合 | WmsShipmentOrderDO、WmsShipmentOrderDetailDO | WmsShipmentOrderDO 是出库单聚合根，WmsShipmentOrderDetailDO 是出库明细行，一对多关系 |
| 移库单聚合 | WmsMovementOrderDO、WmsMovementOrderDetailDO | WmsMovementOrderDO 是移库单聚合根，WmsMovementOrderDetailDO 是移库明细行，一对多关系 |
| 盘点单聚合 | WmsCheckOrderDO、WmsCheckOrderDetailDO | WmsCheckOrderDO 是盘点单聚合根，WmsCheckOrderDetailDO 是盘点明细行，一对多关系 |

值对象：

| 对象 | 说明 |
|------|------|
| WmsOrderTypeConstants | 订单类型常量，按业务域分段定义各单据子类型编号，用于单据 `type` 字段取值 |
| WmsOrderStatusEnum | 单据状态枚举：PREPARE(0), FINISHED(4), CANCELED(5) |

领域服务：

| 服务 | 说明 |
|------|------|
| WmsItemService | 商品管理服务，提供商品及 SKU 的 CRUD 操作 |
| WmsItemBrandService | 品牌管理服务 |
| WmsItemCategoryService | 分类管理服务，支持树形结构操作 |
| WmsMerchantService | 商户管理服务 |
| WmsWarehouseService | 仓库管理服务 |
| WmsInventoryService | 库存管理服务，提供库存查询和变更方法 |
| WmsInventoryHistoryService | 库存历史服务，记录每笔库存变动 |
| WmsReceiptOrderService | 入库单管理服务 |
| WmsShipmentOrderService | 出库单管理服务 |
| WmsMovementOrderService | 移库单管理服务 |
| WmsCheckOrderService | 盘点单管理服务 |

## 设计与架构补充

[README](README.md) 已记录单据驱动库存、单据状态机、并发安全、明细增量维护、只读统计分离等设计原则与三大设计模式，本节补充其余内容。

### 分层架构

| 层 | 职责 | 说明 |
|----|------|------|
| api | 模块间 API 接口，供其他模块 RPC 调用 | 当前无对外暴露的 API 组件 |
| controller | HTTP 接口层，提供 RESTful API | 覆盖主数据、库存（只读）、四大单据及明细、首页统计，接口明细见 [README](README.md) 的 API 接口索引 |
| service | 业务逻辑层 | item（商品/SKU）、item-brand、item-category、merchant、warehouse、inventory（库存 + 库存历史）及四大单据服务，见 [README](README.md) 的核心功能点 |
| dal | 数据访问层 | dataobject（DO 实体类定义）、mysql（MyBatis Mapper 接口） |
| enums | 枚举和常量定义 | WmsOrderTypeConstants（订单类型常量）、ErrorCodeConstants（错误码常量）、WmsOrderStatusEnum（单据状态枚举） |

### 设计原则与设计模式补充

| 原则/模式 | 说明 |
|-----------|------|
| 订单类型常量分段 | `WmsOrderTypeConstants` 按业务域分段定义单据子类型编号（入库 [100,200)、出库 [200,300)），用于单据 `type` 字段取值；库存流水的来源大类另由 `WmsOrderTypeEnum`（1 入库/2 出库/3 移库/4 盘库）表示 |
| SKU 作为库存单位 | 库存以 SKU + 仓库维度跟踪，不跟踪商品级别库存，支持多规格管理 |
| 字典集成 | 单据状态、子类型等使用系统字典管理 |
| 细粒度权限控制 | 权限标识格式 `wms:{entity}:{action}`，如 `wms:receipt-order:create` |
| 单据头/明细模式 | 应用位置：`service/order/{receipt,shipment,movement,check}/`。所有四大单据采用 Header + Detail 主子表结构，单据头存储汇总信息，明细行存储 SKU 级别数据 |
| VO 组装模式 | 应用位置：各 Controller 的私有 `buildXxxRespVO(List)` 方法。先批量查询关联实体（`getXxxMap` / `AdminUserApi.getUserMap`）到 Map，再用 `BeanUtils.toBean(list, XxxRespVO.class, vo -> ...)` 回填名称等字段，避免 N+1 查询 |

### 表关系（ER）

| 来源表 | 关联表 | 关系 | 外键 | 说明 |
|--------|--------|------|------|------|
| wms_item | wms_item_category | N:1 | category_id | 商品归属分类 |
| wms_item | wms_item_brand | N:1 | brand_id | 商品归属品牌 |
| wms_item_sku | wms_item | N:1 | item_id | SKU 归属商品 |
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
| wms_movement_order | wms_warehouse | N:1 | source_warehouse_id | 源仓库 |
| wms_movement_order | wms_warehouse | N:1 | target_warehouse_id | 目标仓库 |
| wms_movement_order_detail | wms_movement_order | N:1 | order_id | 移库明细归属单据 |
| wms_movement_order_detail | wms_item_sku | N:1 | sku_id | 移库明细关联 SKU |
| wms_check_order | wms_warehouse | N:1 | warehouse_id | 盘点单归属仓库 |
| wms_check_order_detail | wms_check_order | N:1 | order_id | 盘点明细归属单据 |
| wms_check_order_detail | wms_item_sku | N:1 | sku_id | 盘点明细关联 SKU |

### 唯一约束与关键索引

仓库内唯一的建表 DDL 是测试资源 `yudao-module-wms/src/test/resources/sql/create_tables.sql`（H2 语法），其中只有 `wms_inventory` 定义了一个唯一约束，其余表仅有主键：

| 表 | 约束/索引 | 类型 | 说明 |
|----|-----------|------|------|
| wms_inventory | uk_sku_id_warehouse_id (sku_id, warehouse_id) | 唯一 | 库存以 SKU + 仓库唯一，是并发懒初始化的兜底依据 |

代码中的编码/单号唯一性由 Service 层查询校验实现，**不依赖数据库唯一索引**：仓库/商品/分类/品牌/往来企业在保存前调 `validateXxxCodeUnique`（`selectByCode`），四类单据保存前调 `validateXxxOrderNoUnique`（`selectByNo`）。生产建表若需额外的查询加速索引，建议按实际查询补充：

- 各明细表 `order_id`、`wms_item_sku.item_id`、`wms_item.category_id` / `brand_id`、`wms_inventory.warehouse_id`：普通索引，加速外键/明细查询
- `wms_inventory_history (order_type, order_id)`：普通索引，支持按来源单据追溯流水（代码按该两列查询）
