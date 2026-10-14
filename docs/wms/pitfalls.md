# 注意事项与已知坑点

> 使用 wms 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 DO 只继承 BaseDO，但表在 DB 层仍参与租户隔离，自建表必须带 tenant_id 列

**问题**: wms 全部 16 个 DO（如 `WmsInventoryDO`、`WmsReceiptOrderDO`）都只继承 `BaseDO`，DO 上没有任何 `tenantId` 字段，也没有 `@TenantIgnore` 注解。开发者容易误以为"wms 未启用多租户"，建表时漏掉 `tenant_id` 列，结果运行期所有 SQL 报 `Unknown column 'tenant_id'`。

**原因**: 租户改写不看 DO 继承谁，而看 `TenantDatabaseInterceptor#computeIgnoreTable`（yudao-spring-boot-starter-biz-tenant）：只有继承 `TenantBaseDO`、或标注 `@TenantIgnore` 的实体才被识别/忽略；其余仅继承 `BaseDO` 的实体一律返回"不忽略"，`TenantLineInnerInterceptor` 会对该表的所有 SQL（含 XML 手写 SQL）自动追加 `tenant_id = ?`，INSERT 时自动补 `tenant_id` 值。模块唯一在仓库内的 DDL（`yudao-module-wms/src/test/resources/sql/create_tables.sql`，H2 语法）也证实所有 wms 表都带 `tenant_id bigint NOT NULL DEFAULT '0'`。

**解决**:

```sql
-- 新建 wms 业务表时，DDL 必须包含 tenant_id 列（DO 里不用映射，INSERT 由拦截器自动填充）
"tenant_id" bigint NOT NULL DEFAULT '0'
```

```java
// 确实需要跨租户共享的表，在 DO 上显式标注：
@TenantIgnore
@TableName("wms_xxx_global")
public class WmsXxxGlobalDO extends BaseDO { ... }
```

## 2. 事务与并发相关

### 2.1 库存并发安全依赖"FOR UPDATE + 唯一索引"双保险，建表缺唯一索引会静默分裂库存

**问题**: 库存行 `(sku_id, warehouse_id)` 的并发首次创建依赖唯一索引兜底。如果自建的 `wms_inventory` 表没有这个唯一索引，两个并发单据同时给同一 SKU + 仓库首次建库存行时会插入两条重复行，之后 `findInventory` 只随机取一条，库存被分裂，且不报任何错。

**原因**: `WmsInventoryServiceImpl#createMissingInventoryList` 的设计是：INSERT 撞唯一索引抛 `DuplicateKeyException` 后回查 `selectBySkuIdAndWarehouseId` 拿回已存在的行；变更前再统一用 `WmsInventoryMapper#selectListByIdsForUpdate`（`.last("FOR UPDATE")`）按 ID 批量加悲观锁。测试 DDL 中对应约束为 `CONSTRAINT "uk_sku_id_warehouse_id" UNIQUE ("sku_id", "warehouse_id")`。但该 DDL 仅存在于测试资源中，生产建表语句不在仓库内，需自行保证。

**解决**: 生产建表必须带上唯一索引；并发首次建行撞锁的一方若回查仍拿不到行，代码会原样抛出 `DuplicateKeyException`（事务回滚），调用方按"重试即可"处理。

```sql
CONSTRAINT "uk_sku_id_warehouse_id" UNIQUE ("sku_id", "warehouse_id")
```

### 2.2 "完成单据"是同一事务内的 CAS 状态更新 + 库存写入，任一步失败整体回滚

**问题**: 对完成/作废动作的失败排查容易找错方向：例如出库单完成时库存不足抛 `INVENTORY_QUANTITY_NOT_ENOUGH`，会发现单据状态"没变成已完成"——这不是状态更新丢了，而是整个事务回滚了。

**原因**: 以 `WmsReceiptOrderServiceImpl#completeReceiptOrder` 为例：方法带 `@Transactional(rollbackFor = Exception.class)`，先用 `receiptOrderMapper.updateByIdAndStatus(id, PREPARE, FINISHED)` 做状态 CAS（`WmsReceiptOrderMapper#updateByIdAndStatus` 带 `status = PREPARE` 条件，并发重复完成时后者更新行数为 0 直接抛 `RECEIPT_ORDER_STATUS_NOT_PREPARE`），再调 `inventoryService.changeInventory` 写库存与流水。库存行上的 `FOR UPDATE` 锁会一直持有到外层事务提交。

**解决**: 理解"状态流转 + 库存变更 + 流水写入"是原子的；对库存不足等业务失败，修复数据后重新完成即可，单据始终停留在草稿态，不会出现"状态已完成但库存没动"的中间态。

### 2.3 盘库单完成时校验"账面快照"，期间库存一动就报 CHECK_ORDER_INVENTORY_CHANGED

**问题**: 盘库单（`WmsCheckOrderServiceImpl#completeCheckOrder`）创建后，只要对应库存行发生过任何出入库变动，完成时就会报 `1_060_203_007 盘库单库存已变化，请重新加载库存后再完成`，且新建库存行的场景撞上并发插入也会转成同一个错误。

**原因**: `WmsInventoryServiceImpl#getOrCreateCheckInventory` 逐条 `selectByIdForUpdate` 锁行后做三重比对：库存行存在、skuId/warehouseId 一致、当前 `quantity` 与盘库明细快照的账面数量 `quantity` 相等，任一不满足抛 `CHECK_ORDER_INVENTORY_CHANGED`；`createCheckInventory` 对 `inventoryId == null`（全新库存行）的插入在 `DuplicateKeyException` 时也抛同一错误。另外，账面数量与实盘数量相等（零盈亏）的明细会直接 `continue`：不更新库存、也不生成库存流水。

**解决**: 完成失败后重新加载盘库单（明细的账面数量/库存 ID 会刷新）再完成；不要试图绕过该校验，它防止的是把过期快照覆盖到最新库存上。统计盘亏盘盈时注意零盈亏明细没有流水记录。

## 3. 状态机相关

### 3.1 三值状态机：只有草稿可改/删/完成/作废，已完成是终态、没有红冲接口

**问题**: 单据状态只有 `WmsOrderStatusEnum` 的 `PREPARE(0)/FINISHED(4)/CANCELED(5)` 三值。已完成单据不能改、不能删、不能作废，也没有"反完成/红冲"接口——出库多发、入库多收后无法把原单退回草稿。

**原因**: 四类单据的 `update*/delete*/complete*/cancel*` 全部先走 `validateXxxOrderPrepare`（仅 `PREPARE` 放行），删除走 `validateXxxOrderExists` + 状态属于 `PREPARE/CANCELED` 的判断（对应 `*_ORDER_STATUS_NOT_DELETABLE`）；状态流转靠 `updateByIdAndStatus` 的 CAS 保证。库存模块 `WmsInventoryService` 只提供 `changeInventory/checkInventory` 两个正向入口，没有反向冲销。

**解决**: 已完成单据的错误只能用"再建一张反向单据"修正（多发库存建入库单、多收建出库单，或用盘库单校正）；设计对接逻辑时不要假设可以撤销已完成单据。

## 4. 单据类型与校验相关

### 4.1 单据"大类枚举"与"细分类型常量"是两套编号体系，库存流水存大类、单据 type 存细分类

**问题**: 查询/统计时混用两套类型值会导致查不到数据：`WmsOrderTypeEnum` 是 1 入库/2 出库/3 移库/4 盘库；而入库单、出库单自身的 `type` 字段存的是细分类——`WmsOrderTypeConstants` 定义的 100-103（生产/采购/退货/归还入库）、200-202（退货/销售/生产出库）。

**原因**: `wms_inventory_history.orderType` 只写大类（`buildInventoryHistory` 取 `WmsInventoryChangeReqDTO.orderType`，来源是 `WmsOrderTypeEnum`）；单据 `type` 字段经 VO 上的 `@InEnum(WmsReceiptOrderTypeEnum.class)` / `@InEnum(WmsShipmentOrderTypeEnum.class)` 校验，值域是细分类型。字典也分两套：`wms_order_type` 用大类，`wms_receipt_order_type` / `wms_shipment_order_type` 用细分值（见 `DictTypeConstants`）。

**解决**: 按单据类型过滤流水用 1-4，按入库/出库业务类型过滤单据用 100+ / 200+；新增细分类时在 `WmsOrderTypeConstants` 集中编号（注释明确分段：入库 [100,200)、出库 [200,300)），避免与其它段冲突。

### 4.2 入库单必须是供应商、出库单必须是客户，但 merchantId 可空、企业类型改了不回头校验

**问题**: 三个容易踩的边界：① 入库/出库单的 `merchantId` 传 `null` 也能创建成功；② 往来企业的类型（`WmsMerchantTypeEnum`：1 客户/2 供应商/3 客户+供应商）创建单据后被随意修改，`updateMerchant` 不会回头校验该企业名下已有单据；③ 类型选错时错误信息只说"必须是供应商/客户"，不含企业名。

**原因**: `WmsReceiptOrderServiceImpl#validateReceiptOrderSaveData` 中 `if (reqVO.getMerchantId() != null)` 才调 `merchantService.validateSupplierMerchantExists`（放行 `SUPPLIER/CUSTOMER_SUPPLIER`，否则 `MERCHANT_NOT_SUPPLIER`）；出库单对应 `validateCustomerMerchantExists`。而 `WmsMerchantServiceImpl#updateMerchant` 的 `validateMerchantSaveData` 只校验 code/name 唯一，不涉及 type 与历史单据的一致性。

**解决**: 需要强制往来方的业务请在自己的一层补非空校验；修改企业类型前先人工确认名下入库/出库单（`getReceiptOrderCountByMerchantId` / `getShipmentOrderCountByMerchantId`）的影响。

## 5. 主数据维护相关

### 5.1 SKU 没有独立写接口，增删改全靠商品接口全量提交，被库存/单据引用的 SKU 删不掉

**问题**: 想单独新增/修改/删除 SKU 时找不到接口——`WmsItemSkuController` 只有一个 `GET /page`（复用 `wms:item:query` 权限）。通过 `WmsItemController` 更新商品时，提交的 `skus` 数组是全量语义：不在数组里的旧 SKU 会被删除，若该 SKU 已有库存或出现在任何单据明细中，整个更新直接失败。

**原因**: SKU 的写路径全部在 `WmsItemServiceImpl`（createItem/updateItem/deleteItem 调 `itemSkuService.createItemSkuList/updateItemSkuList/deleteItemSkuListByItemId`）。`WmsItemSkuServiceImpl#updateItemSkuList` 用 `diffList` 对比新旧列表，删除部分先过 `validateItemSkuUnused`：逐一检查 4 类单据明细 count（`getReceiptOrderDetailCountBySkuId` 等，命中抛 `ITEM_SKU_HAS_ORDER`）和库存 count（`getInventoryCountBySkuId`，命中抛 `ITEM_SKU_HAS_INVENTORY`）。新增 SKU 的 id 会被强制置 null 由数据库自增分配。

**解决**: 维护 SKU 一律走商品保存接口并提交完整 `skus` 数组；想"停用"而不是删除被引用的 SKU，只能修改名称/价格字段，把它从数组里去掉会触发删除校验。

### 5.2 删除保护靠逐项 count 校验实现，双向依赖全靠 @Lazy 解环，扩展时沿用该模式

**问题**: 给 wms 新增单据类型或新增 Service 互相引用时容易踩两个坑：① 仓库/往来企业/商品分类的删除保护是"写死的清单"，新增一种引用了仓库的单据后，忘记在删除校验里补一项，就会出现"仓库已被引用却还能删"；② 主数据 Service 与单据/库存 Service 互相注入（如仓库删除要统计 4 类单据、SKU 删除要统计 4 类明细），直接 `@Resource` 互注会启动失败。

**原因**: `WmsWarehouseServiceImpl#validateWarehouseUnused` 逐一调用 `inventoryService` + 4 个单据 Service 的 count 方法（`WAREHOUSE_HAS_INVENTORY` / `WAREHOUSE_HAS_ORDER`）；`WmsItemCategoryServiceImpl#validateParentCategory` 用 `Short.MAX_VALUE` 上限的循环递归校验分类环路（`ITEM_CATEGORY_PARENT_IS_CHILD`）。这些反向引用全部通过 `@Lazy` 注入解环：`WmsItemServiceImpl`（categoryService/brandService）、`WmsItemSkuServiceImpl`（inventoryService + 4 个明细 Service）、`WmsWarehouseServiceImpl`（5 个）、`WmsMerchantServiceImpl`（2 个）。

**解决**: 新增引用仓库/企业/SKU 的表时，同步在对应 `validateXxxUnused` 里补 count 校验；新增 Service 间双向引用时用 `@Resource + @Lazy`（Spring Boot 2.6+ 默认禁止循环依赖，本项目为 2.7.x 线）。

## 6. 查询与统计相关

### 6.1 首页统计是 MySQL 方言手写 SQL，逻辑删除要手动写 deleted = 0

**问题**: `WmsHomeStatisticsMapper.xml` 的 5 条统计语句是手写 SQL，直接照搬到 Oracle/PostgreSQL/SQL Server 等方言会报错（`DATE_FORMAT(order_time, '%Y-%m-%d')`、`IFNULL`、`LIMIT #{limit}` 均为 MySQL 语法）；另外自己新增统计语句时漏写 `deleted = 0` 会把已删除数据统计进去——MyBatis-Plus 的逻辑删除只对 BaseMapper 生成的 SQL 自动生效，不会改写 XML 手写 SQL。

**原因**: 统计结果以 `Map<String, Object>` 返回，key 依赖 SQL 别名（`date`/`orderType`/`count`），`WmsHomeStatisticsServiceImpl#buildInventoryItemRankList` 甚至做了 `id`/`itemId` 双读兜底；单据枚举值通过 OGNL 内联（`${@cn.iocoder.yudao.module.wms.enums.order.WmsOrderTypeEnum@RECEIPT.type}`）。还有统计口径问题：移库单按 `source_warehouse_id = ? OR target_warehouse_id = ?` 计数，同一单在两个仓库的过滤结果里各计一次，跨仓库汇总时会重复。租户条件不用手写，由多租户拦截器自动追加（见 1.1）。

**解决**: 切换数据库方言时优先改写这 5 条 XML；新增手写统计 SQL 时记得带 `deleted = 0`、注意别名字符串与 `MapUtil.getInt(row, "orderType")` 的 key 一致；跨仓库汇总趋势数据时对移库单做去重口径说明。

## 7. 错误码与异常相关

### 7.1 错误码 1_060 段独占但有编号空洞；库存内部不一致抛的是 IllegalStateException（500）

**问题**: ① `ErrorCodeConstants` 段内有空洞（仓库 `1_060_100_003` 未用、入库单 `1_060_200_004/006` 未用），新错误码按分段续号时不要误以为连续；② 库存变更中有一类错误不走错误码体系——`WmsInventoryServiceImpl#changeInventoryList` 里"库存行不存在"抛的是 `IllegalStateException`，前端会收到 500 而非业务错误码。

**原因**: wms 独占 `1-060-000-000` 段（已全仓 grep 确认无其它模块使用）：仓库 1_060_100_x、商品分类 1_060_102_x、品牌 1_060_103_x、商品 1_060_104_x、往来企业 1_060_105_x、入库 1_060_200_x、出库 1_060_201_x、移库 1_060_202_x、盘库 1_060_203_x、库存 1_060_300_x。`IllegalStateException` 是内部不变式兜底（加锁回查后行仍缺失），设计上按"不可能发生"处理。另外 `INVENTORY_QUANTITY_NOT_ENOUGH` 的消息里拼的是 `warehouseId` 原始 ID 而非仓库名，排查时需自行换算。

**解决**: 新增错误码沿用 `1_060_{域}_{序号}` 分段；遇到"库存行不存在"的 500 优先排查是否绕过 `WmsInventoryService` 直接操作了 `wms_inventory` 表或数据库缺唯一索引（见 2.1）。

## 8. 部署与集成相关

### 8.1 yudao-server 默认不引 wms 模块，初始化 SQL 不含业务表 DDL，启用需手工两步

**问题**: 编译/启动后发现没有任何 wms 接口——`yudao-server/pom.xml` 中 wms 依赖默认被注释（"WMS 仓库管理模块。默认注释，保证编译速度"）；而执行 `sql/mysql/ruoyi-vue-pro.sql` 初始化后菜单、字典都有了，业务表却一张都不存在——该文件只有 wms 相关的 `system_menu` INSERT（权限标识如 `wms:warehouse:query`）和 `system_dict_data/system_dict_type` INSERT（`wms_order_status` 等 5 个字典），没有任何 `CREATE TABLE wms_*`。

**原因**: wms 是可选模块，依赖按需开启；建表语句不随初始化 SQL 发布，仓库内唯一的 DDL 参考是测试资源 `yudao-module-wms/src/test/resources/sql/create_tables.sql`（H2 语法，含 `tenant_id` 列与 `uk_sku_id_warehouse_id` 唯一索引，转成 MySQL 需自行调整）。Swagger 分组依赖模块内的 `WmsWebConfiguration#wmsGroupedOpenApi`（`buildGroupedOpenApi("wms")`），模块未引入时自然没有 wms 分组。

**解决**: 启用步骤：① 打开 `yudao-server/pom.xml` 中 wms 依赖注释并重新编译；② 按测试 DDL 在目标库建齐 16 张 wms 业务表（务必带 `tenant_id` 和库存唯一索引，见 1.1/2.1）。集成注意：模块是纯 admin API（无 `controller/app`），不提供 `api` 包对外暴露跨模块接口，上游仅依赖 `yudao-module-system` 的 `AdminUserApi`；二次开发的权限标识按 `wms:{功能}:{操作}` 与菜单 INSERT 保持一致。
