# 注意事项与已知坑点

> 使用 erp 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 erp 表在 DB 层默认参与租户隔离，新建表必须带 tenant_id 列

**问题**: 给 erp 模块新增业务表（DO 继承 BaseDO）后，运行期 SQL 直接报 `Unknown column 'tenant_id'`；或误以为"DO 没有 tenantId 字段 = 无租户隔离"而写出跨租户统计逻辑。

**原因**: `yudao-spring-boot-starter-biz-tenant` 的 `TenantDatabaseInterceptor#computeIgnoreTable` 对所有 MyBatis-Plus 注册过的表生效：只有标注 `@TenantIgnore` 的实体才跳过租户改写，其余（含仅继承 BaseDO 的实体）一律由 `TenantLineInnerInterceptor` 自动追加 `tenant_id = ?` 条件、INSERT 自动填充租户号。erp 模块 33 个 DO 全部继承 BaseDO 且模块内无一处 `@TenantIgnore`，即 erp 全部表在 DB 层按租户过滤，DO 不映射 tenantId 字段只是不读写该列。

**解决**:

```java
// 新建 erp 表时，DDL 必须包含 tenant_id 列（建议联合索引前缀）
// 确认无需租户隔离的表，显式在 DO 上标注：
@TenantIgnore
@TableName("erp_xxx_global")
public class ErpXxxGlobalDO extends BaseDO { ... }
```

### 1.2 statistics 域 XML 手写租户条件：${} 拼接 + 无上下文时过滤被跳过

**问题**: 统计接口（`ErpPurchaseStatisticsMapper.xml` / `ErpSaleStatisticsMapper.xml`）在异步线程、定时任务等无租户上下文的场景下租户过滤整体缺失；且租户号经 `${}` 字符串拼接，不走预编译。

**原因**: `getPurchasePrice` 等语句手写了

```xml
<if test="@cn.iocoder.yudao.framework.tenant.core.context.TenantContextHolder@getTenantId() != null">
    AND tenant_id = ${@cn.iocoder.yudao.framework.tenant.core.context.TenantContextHolder@getTenantId()}
</if>
```

`${}` 是纯文本替换（不走 `#{}` 参数绑定）；`getTenantId()` 为 null 时 `<if>` 直接跳过，过滤条件消失。

**解决**: 在 Service 层将 `TenantContextHolder.getTenantId()` 作为方法参数传入，XML 改用 `#{}` 占位符；异步/定时任务中调用统计前用 `TenantUtils.execute(tenantId, ...)` 设置上下文，避免依赖 OGNL 静态调用。

## 2. Redis 相关

### 2.1 单号生成依赖 Redis INCR，存在跳号、重复与 key 永不过期风险

**问题**: 单据号（`CGDD`/`XSCK`/`QTRK` 等前缀）出现跳号；Redis 数据丢失后理论上可生成重复单号，被 `selectByNo` 兜底拦截时用户看到"生成单号失败，请重新提交"。

**原因**: `ErpNoRedisDAO#generate` 中 `increment(key)` 与 `expire(key, 1天)` 是两条独立命令，中途宕机则 key 永不过期；计数器在 Redis，DB 事务回滚不会回滚 INCR（跳号）；Redis 未持久化重启后计数回退，依赖各 Service 创建单据后的 `selectByNo` 唯一性校验兜底（抛 `PURCHASE_ORDER_NO_EXISTS` 等）。

**解决**: 跳号业务无害可接受；Redis 必须开启持久化；increment 与 expire 可用 Lua 脚本保证原子。若业务要求严格连续单号，改为数据库号段表 + 行锁方案，勿用 Redis 自增。

## 3. 事务与并发相关

### 3.1 库存变更"查-校-改"竞态：台账结存 totalCount 失真 + 首插重复行

**问题**: 并发审核出入库时，`erp_stock_record.total_count`（变动后结存）与真实库存不一致；同产品同仓库首次入库并发时可能产生两条 `erp_stock` 行，之后 `selectOne` 抛 `TooManyResultsException`。

**原因**: `ErpStockServiceImpl#updateStockCountIncrement` 先 `selectByProductIdAndWarehouseId` 读旧值、在 Java 内存校验 `stock.getCount().add(count) < 0`，再执行 `ErpStockMapper#updateCountIncrement`（带 `count >= abs` 条件的原子 UPDATE，不足时 updateCount=0 抛 `STOCK_COUNT_NEGATIVE2`）——扣减本身有 DB 条件兜底，但方法返回的"最新库存"是 `stock.getCount().add(count)`（旧读数 + 变更数，代码注释自认"此时不好去查询最新库存"），并发下经 `ErpStockRecordServiceImpl#createStockRecord` 写入台账的结存失真；`stock == null` 分支直接 insert，若 `erp_stock` 无 `(product_id, warehouse_id)` 唯一索引则并发首插重复。

**解决**: `erp_stock` 必须建 `(product_id, warehouse_id)` 唯一索引，insert 冲突时捕获异常重查；台账结存改为 UPDATE 成功后同事务回读 `count`（`SELECT count FROM erp_stock WHERE id = #{id}`），不要用内存计算值。

### 3.2 默认仓库/默认账户切换非原子，并发下出现双默认或无默认

**问题**: 两个管理员同时把不同仓库/结算账户设为默认，最终可能两个都是默认或都不是。

**原因**: `ErpWarehouseServiceImpl#updateWarehouseDefaultStatus` 与 `ErpAccountServiceImpl#updateAccountDefaultStatus` 都是先 `selectByDefaultStatus()` 查出旧默认、逐条关闭、再设置新默认的"读-写"序列；`selectByDefaultStatus` 只返回一行（只关一个旧默认），且 **`ErpAccountServiceImpl#updateAccountDefaultStatus` 连 `@Transactional` 都没有**，两条 UPDATE 各自提交，中途失败留下中间状态。

**解决**: 至少给 account 版补上 `@Transactional(rollbackFor = Exception.class)`；更稳妥用单条 SQL 原子切换：

```java
// UPDATE erp_warehouse SET default_status = (id = #{id}) WHERE deleted = 0
warehouseMapper.updateDefaultStatusAtomically(id);
```

## 4. 数据一致性相关

### 4.1 产品删除校验不完整：漏掉库存/其它出入库/调拨/盘点，删后异常分支 NPE

**问题**: 只做过"其它入库/其它出库/调拨/盘点"的产品可以被删除，`erp_stock`、`erp_stock_record` 及这些单据明细悬空；后续相关操作在抛业务异常时先抛 `NullPointerException`（500），掩盖真实错误。

**原因**: `ErpProductServiceImpl#deleteProduct` 只校验采购订单/采购入库/采购退货/销售订单/销售出库/销售退货六类明细引用，未校验 `erp_stock_in_item`、`erp_stock_out_item`、`erp_stock_move_item`、`erp_stock_check_item`、`erp_stock`、`erp_stock_record`；而 `ErpStockServiceImpl#updateStockCountIncrement` 的库存不足提示 `productService.getProduct(productId).getName()`、`ErpPurchaseOrderServiceImpl#updatePurchaseOrderInCount` 的超量提示同理，产品被逻辑删除后 `selectById` 返回 null 直接 `.getName()` NPE。

**解决**: `deleteProduct` 补齐对库存域六张表的 `selectCount` 校验（参照已有的采购/销售域写法）；错误消息拼接处改为判空或统一走 `validProductList`。

### 4.2 仓库/客户/供应商/结算账户删除无任何引用校验

**问题**: 有库存、有单据的仓库，有销售订单的客户，有采购订单的供应商，有付款单的结算账户，都能直接删除，单据展示与统计悬空。

**原因**: `ErpWarehouseServiceImpl#deleteWarehouse`、`ErpCustomerServiceImpl#deleteCustomer`、`ErpSupplierServiceImpl#deleteSupplier`、`ErpAccountServiceImpl#deleteAccount` 全部只做 `validateXxxExists` 后直接 `deleteById`，无任何引用检查（对比 `deleteProduct` 至少校验了六类单据）。

**解决**: 参照 `ErpProductServiceImpl#deleteProduct` 模式，删除前逐域 `selectCount` 校验引用；仓库至少校验 `erp_stock` 与未完成单据，账户至少校验付款/收款单引用。

## 5. 状态机与操作日志相关

### 5.1 全模块无操作日志，审核状态机仅两态，变更不可追溯

**问题**: 单据的创建、审核/反审核、删除全无操作日志，库存变动的"谁在什么时候审的"无法追溯；审核状态只有"未审核(10)/已审核(20)"两态。

**原因**: `enums/LogRecordConstants` 是**空接口**（未定义任何常量），全模块 grep 不到一处 `@LogRecord`，10+ 个 ServiceImpl（`ErpPurchaseOrderServiceImpl`、`ErpStockInServiceImpl`、`ErpStockCheckServiceImpl`、`ErpFinancePaymentServiceImpl` 等）顶部均留有 `// TODO 芋艿：记录操作日志`；`ErpAuditStatus` 类上 TODO 注明未来接入工作流补充"待提交/审核不通过"等状态。各单据审核入口统一用 `updateByIdAndStatus(id, oldStatus, ...)` 乐观锁做并发防护（这点是对的），但状态流转之外没有审计。

**解决**: 接入 `yudao-spring-boot-starter-biz-operatelog`，为 `createXxx`/`updateXxxStatus`/`deleteXxx` 补 `@LogRecord` 注解并填充 `LogRecordConstants`；扩展 `ErpAuditStatus` 前同步字典 `erp_audit_status` 与前端状态映射。

## 6. 错误码相关

### 6.1 多组错误码互相冲突/错段，前端按 code 分支会错乱

**问题**: 同一错误码对应多个不同含义，日志排障与前端按 code 的特殊处理（如提示语、跳转）被误导。

**原因**: `enums/ErrorCodeConstants` 中：

- `SUPPLIER_NOT_EXISTS` 与 `SUPPLIER_NOT_ENABLE` 同为 `1_030_100_000`；
- `STOCK_MOVE_*` 六个错误码整段复用 `STOCK_OUT_*` 的 `1_030_402_000~005`；
- `PRODUCT_CATEGORY_EXITS_PRODUCT`（`1_030_502_002`）与 `PRODUCT_UNIT_EXITS_PRODUCT`（`1_030_502_002`）完全相同；
- 客户/销售段注释声明 `1_030-2xx`，实际全部使用 `1_020-2xx`。

**解决**: 按段重新规划并迁移（新码 + 兼容旧码映射）；至少先把三组完全重复的错开；建议在 CI 中加错误码段唯一性校验脚本。

## 7. 接口与命名相关

### 7.1 Swagger @Tag 复制粘贴错误：盘点单接口显示为"库存调拨单"

**问题**: Swagger 文档中"库存盘点"全部接口显示为"管理后台 - ERP 库存调拨单"，与 `ErpStockMoveController`（真正的调拨单，`/erp/stock-move`）完全同名；结算账户精简列表的方法名叫 `getWarehouseSimpleList`。

**原因**: `ErpStockCheckController` 类级 `@Tag(name = "管理后台 - ERP 库存调拨单")` 是从调拨单复制后未改（实际路径 `/erp/stock-check` 是盘点单）；`ErpAccountController` 的 `/simple-list` 方法名复制自仓库模块。

**解决**: 修正 `@Tag` 为"ERP 库存盘点单"，方法改名 `getAccountSimpleList`；联调时以 `@RequestMapping` 路径为准，勿按 `@Tag` 名称区分控制器。

## 8. 参数校验与异常相关

### 8.1 付款/收款单校验用 hutool Assert，业务错误抛成 IllegalArgumentException（500）

**问题**: 付款单里选择与供应商不匹配的采购入库单时，前端收到 500 系统异常而非"供应商必须相同"的可读提示；传错 bizType 时同理。

**原因**: `ErpFinancePaymentServiceImpl#validateFinancePaymentItems` 使用 `Assert.equals(purchaseIn.getSupplierId(), supplierId, "供应商必须相同")`，hutool `Assert` 抛的是 `IllegalArgumentException` 而非 `ServiceException`；同文件及 `updatePurchasePrice` 中 `throw new IllegalArgumentException("业务类型不正确：" + item.getBizType())` 同样绕过了业务异常体系。

**解决**: 统一改用 `ServiceExceptionUtil.exception(ErrorCode)`，为"供应商不一致""业务类型非法"新增错误码；不要用 hutool Assert 做对外接口的业务校验。

### 8.2 采购入库单 accountId 可空却强制校验，报"结算账户不存在"误导

**问题**: 采购入库单不填结算账户时保存直接报"结算账户不存在"，与采购订单、付款单（账户均可空）行为不一致。

**原因**: `ErpPurchaseInSaveReqVO.accountId` 无 `@NotNull`（VO 层允许为空），但 `ErpPurchaseInServiceImpl#createPurchaseIn` / `updatePurchaseIn` 无条件调用 `accountService.validateAccount(createReqVO.getAccountId())`，`ErpAccountServiceImpl#validateAccount` 对 null 查不到即抛 `ACCOUNT_NOT_EXISTS`；对比 `ErpPurchaseOrderServiceImpl`、`ErpFinancePaymentServiceImpl` 均有 `if (accountId != null)` 判空。

**解决**: 二选一对齐：VO 加 `@NotNull` 明确必填；或与订单/付款单一致加 null 判断（账户可空）。
