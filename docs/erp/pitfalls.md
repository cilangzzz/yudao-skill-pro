# ERP 模块踩坑与注意事项

## 1. 单据状态管理

### 1.1 审核状态不可逆操作

**问题**: 已审核的单据直接修改或删除会导致数据不一致。

**规则**: 所有业务单据遵循 `PROCESS(10)` -> `APPROVE(20)` 状态流转。已审核单据必须先反审核才能修改/删除。

**正确做法**:
```java
// 删除前检查状态
if (ErpAuditStatus.APPROVE.getStatus().equals(order.getStatus())) {
    throw exception(PURCHASE_ORDER_DELETE_FAIL_APPROVE);
}
```

**常见错误**:
- 直接删除不检查状态
- 反审核时不检查关联单据

### 1.2 反审核时的关联检查

**问题**: 反审核采购订单时，如果存在已审核的入库单或退货单，会导致数据不一致。

**正确做法**: 反审核前检查是否存在关联的已审核入库/退货单。

---

## 2. 库存操作

### 2.1 库存并发问题

**问题**: 多个请求同时修改同一产品在同一仓库的库存，可能导致库存数量不准确。

**解决方案**: 使用 `ErpStockMapper.updateCountIncrement()` 增量更新，通过 SQL 级别的 `count = count + ?` 避免并发问题。

```java
// 错误做法：先查后改
ErpStockDO stock = stockMapper.selectByProductAndWarehouse(productId, warehouseId);
stock.setCount(stock.getCount().add(count)); // 并发时不安全
stockMapper.updateById(stock);

// 正确做法：增量更新
stockMapper.updateCountIncrement(stockId, count, negativeEnable);
```

### 2.2 负库存控制

**问题**: 出库时库存不足，是否允许负库存。

**解决方案**: `updateCountIncrement` 方法的 `negativeEnable` 参数控制：
- `true`: 允许负库存，直接更新
- `false`: 不允许负库存，更新时检查 `count >= abs(changeCount)`

```java
// 不允许负库存时的 SQL
UPDATE erp_stock SET count = count + #{count}
WHERE id = #{id} AND count >= #{abs(count)}
```

### 2.3 库存记录追溯

**问题**: 库存变动后无法追溯原因。

**解决方案**: 每次库存变动都创建 `ErpStockRecordDO` 记录，包含：
- 业务类型 (biz_type): 区分采购入库、销售出库等
- 业务编号 (biz_id): 关联业务单据
- 业务项编号 (biz_item_id): 关联业务单据明细
- 业务单号 (biz_no): 便于查询

---

## 3. 主子表操作

### 3.1 差量更新

**问题**: 更新订单时，直接删除所有子表再重新插入，会导致子表ID变化，影响关联数据。

**解决方案**: 使用 `diffList` 方法对比新旧数据，分别处理新增、修改、删除的子表记录。

```java
// 正确做法：差量更新
List<ErpPurchaseOrderItemDO> newItems = BeanUtils.toBean(updateReqVO.getItems(), ErpPurchaseOrderItemDO.class);
List<ErpPurchaseOrderItemDO> oldItems = purchaseOrderItemMapper.selectListByOrderId(orderId);
diffList(newItems, oldItems,
    // 新增的项
    insertItems -> purchaseOrderItemMapper.insertBatch(insertItems),
    // 修改的项
    updateItems -> purchaseOrderItemMapper.updateBatch(updateItems),
    // 删除的项
    deleteItems -> purchaseOrderItemMapper.deleteByIds(convertList(deleteItems, ErpPurchaseOrderItemDO::getId))
);
```

### 3.2 子表关联更新

**问题**: 采购入库/退货审核后，需要更新采购订单的已入库/已退货数量。

**解决方案**: 使用 Map 传递每个订单项的变更数量，批量更新。

```java
// 更新采购订单的已入库数量
Map<Long, BigDecimal> inCountMap = new HashMap<>();
items.forEach(item -> inCountMap.put(item.getOrderItemId(), item.getCount()));
purchaseOrderService.updatePurchaseOrderInCount(orderId, inCountMap);
```

---

## 4. 单据号生成

### 4.1 Redis 单据号生成

**问题**: 分布式环境下，单据号可能重复。

**解决方案**: 使用 `ErpNoRedisDAO.generate()` 基于 Redis 生成，格式：`前缀 + yyyyMMdd + 6位自增序号`。

```java
String no = noRedisDAO.generate(ErpNoRedisDAO.PURCHASE_ORDER_NO_PREFIX);
// 生成结果：CGDD20260318000001
```

### 4.2 单据号前缀规范

| 前缀 | 说明 | 示例 |
|------|------|------|
| CGDD | 采购订单 | CGDD20260318000001 |
| XSDD | 销售订单 | XSDD20260318000001 |
| QTRK | 其它入库 | QTRK20260318000001 |
| QCKD | 其它出库 | QCKD20260318000001 |
| QCDB | 库存调拨 | QCDB20260318000001 |
| QCPD | 库存盘点 | QCPD20260318000001 |
| FKD | 付款单 | FKD20260318000001 |
| SKD | 收款单 | SKD20260318000001 |

---

## 5. 数据关联查询

### 5.1 N+1 查询问题

**问题**: 分页查询订单时，如果逐条查询关联数据（如供应商名称），会产生 N+1 查询。

**解决方案**: 使用 `convertMap` 或 `convertMultiMap` 批量查询关联数据，构建映射后批量设置。

```java
// 错误做法：N+1 查询
orders.forEach(order -> {
    ErpSupplierDO supplier = supplierService.getSupplier(order.getSupplierId());
    order.setSupplierName(supplier.getName());
});

// 正确做法：批量查询
Map<Long, ErpSupplierDO> supplierMap = supplierService.getSupplierMap(
    convertSet(orders, ErpPurchaseOrderDO::getSupplierId));
orders.forEach(order -> {
    ErpSupplierDO supplier = supplierMap.get(order.getSupplierId());
    if (supplier != null) {
        order.setSupplierName(supplier.getName());
    }
});
```

### 5.2 关联数据缺失处理

**问题**: 关联数据（如供应商、产品）被删除后，查询订单时可能出现空指针。

**解决方案**: 查询关联数据后，检查是否为 null，提供默认值。

---

## 6. 事务管理

### 6.1 事务范围

**问题**: 审核操作涉及多个表更新，如果部分更新失败，需要回滚。

**解决方案**: 在 Service 实现类的方法上添加 `@Transactional(rollbackFor = Exception.class)`。

```java
@Override
@Transactional(rollbackFor = Exception.class)
public void updatePurchaseInStatus(Long id, Integer status) {
    // 1. 更新入库单状态
    // 2. 更新库存
    // 3. 更新采购订单已入库数量
    // 如果任何一步失败，全部回滚
}
```

### 6.2 事务嵌套

**问题**: 在事务中调用其他 Service 的方法，可能导致事务嵌套。

**解决方案**: 确保事务边界清晰，避免不必要的嵌套事务。

---

## 7. 权限控制

### 7.1 权限标识规范

**问题**: 权限标识不规范导致权限配置混乱。

**规范**: 权限标识格式：`erp:{模块}:{操作}`

```
erp:purchase-order:create
erp:purchase-order:update
erp:purchase-order:delete
erp:purchase-order:query
erp:purchase-order:update-status
```

### 7.2 状态更新权限

**问题**: 状态更新（审核/反审核）使用单独的权限标识。

**规范**: 使用 `update-status` 作为操作类型。

---

## 8. 错误码管理

### 8.1 错误码格式

**规范**: 错误码格式：`1_030_xxx_xxx`

- `1`: 系统标识
- `030`: ERP 模块标识
- `xxx`: 业务域标识（100=采购，200=销售，300=财务，400=库存）
- `xxx`: 具体错误编号

### 8.2 常见错误码

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_030_101_000 | PURCHASE_ORDER_NOT_EXISTS | 采购订单不存在 |
| 1_030_101_001 | PURCHASE_ORDER_DELETE_FAIL_APPROVE | 采购订单已审核，无法删除 |
| 1_030_101_003 | PURCHASE_ORDER_APPROVE_FAIL | 审核失败，只有未审核的采购订单才能审核 |
| 1_030_404_000 | STOCK_COUNT_NEGATIVE | 操作失败，产品所在仓库的库存不足 |

---

## 9. 扩展指南

### 9.1 新增业务单据类型

1. 创建 DO 实体类（主表 + 子表）
2. 创建 Mapper 接口
3. 创建 Service 接口和实现类
4. 创建 Controller
5. 创建 VO 类（SaveReqVO、PageReqVO、RespVO）
6. 在 `ErpNoRedisDAO` 中添加单据号前缀
7. 在 `ErrorCodeConstants` 中添加错误码

### 9.2 新增库存业务类型

1. 在 `ErpStockRecordBizTypeEnum` 中添加新类型
2. 创建对应的业务单据
3. 在业务审核时调用 `stockRecordService.createStockRecord()`
4. 在反审核时调用 `stockRecordService.deleteStockRecord()`
