# 踩坑与最佳实践

> 模块路径：`yudao-module-mes`

---

## 1. 工单状态机

### 踩坑：状态流转不严格

**问题**：未校验前置状态，导致工单状态跳变（如从"草稿"直接变为"已完工"）。

**正确做法**：状态变更前必须校验当前状态是否合法。

```java
// 错误：直接更新状态
workOrderMapper.updateStatus(orderId, newStatus);

// 正确：校验前置状态
MesWorkOrderDO order = workOrderMapper.selectById(orderId);
if (!MesWorkOrderStatusEnum.canTransit(order.getStatus(), newStatus)) {
    throw exception(WORK_ORDER_STATUS_TRANSIT_FAIL);
}
workOrderMapper.updateStatus(orderId, newStatus);
```

### 踩坑：并发状态变更

**问题**：两个请求同时变更同一工单状态，导致状态覆盖。

**正确做法**：使用 CAS 方式更新。

```sql
UPDATE mes_pro_work_order SET status = #{newStatus}
WHERE id = #{orderId} AND status = #{oldStatus}
```

---

## 2. 生产任务与甘特图

### 踩坑：任务时间重叠

**问题**：同一设备/工位分配了时间重叠的任务，导致排产冲突。

**正确做法**：更新任务时间时校验设备/工位的时间段是否冲突。

```java
// 校验同设备同时间段是否有其他任务
List<MesTaskDO> conflicts = taskMapper.selectList(
    new LambdaQueryWrapper<MesTaskDO>()
        .eq(MesTaskDO::getMachineryId, task.getMachineryId())
        .ne(MesTaskDO::getId, task.getId())
        .le(MesTaskDO::getPlanStartTime, task.getPlanEndTime())
        .ge(MesTaskDO::getPlanEndTime, task.getPlanStartTime())
);
if (!conflicts.isEmpty()) {
    throw exception(TASK_TIME_CONFLICT);
}
```

### 踩坑：甘特图拖拽后数据不一致

**问题**：前端拖拽调整任务时间后，未同步更新关联的工序计划。

**正确做法**：拖拽更新任务时间后，检查是否需要级联更新后续工序。

---

## 3. 流转卡管理

### 踩坑：流转卡工序顺序混乱

**问题**：流转卡跳过中间工序直接完成，导致生产过程不可追溯。

**正确做法**：流转卡工序必须按顺序执行，每个工序完成后才能进入下一个。

```java
// 校验当前工序是否是下一个待执行工序
MesCardProcessDO currentProcess = cardProcessMapper.selectOne(
    new LambdaQueryWrapper<MesCardProcessDO>()
        .eq(MesCardProcessDO::getCardId, cardId)
        .eq(MesCardProcessDO::getStatus, CardProcessStatusEnum.IN_PROGRESS)
);
if (currentProcess == null) {
    throw exception(CARD_NO_ACTIVE_PROCESS);
}
```

---

## 4. 报工审批流程

### 踩坑：报工数量超过任务计划数量

**问题**：多次报工累计数量超过任务计划数量，导致超产。

**正确做法**：报工时校验累计报工数量不超过计划数量。

```java
// 查询该任务已报工的累计数量
BigDecimal totalFeedback = feedbackMapper.selectTotalQuantity(taskId);
if (totalFeedback.add(feedbackQuantity).compareTo(task.getPlanQuantity()) > 0) {
    throw exception(FEEDBACK_QUANTITY_EXCEED);
}
```

### 踩坑：驳回后重新提交状态处理

**问题**：报工被驳回后重新提交，未正确重置状态。

**正确做法**：驳回状态只能重新提交（回到待审批），不能直接通过。

---

## 5. 来料检验（IQC）

### 踩坑：IQC 检验与入库顺序

**问题**：未完成 IQC 检验就办理入库，导致不合格品进入库存。

**正确做法**：入库前必须检查 IQC 检验结果。

```java
// 采购入库前校验
MesQcIqcDO iqc = iqcMapper.selectByArrivalNoticeId(arrivalNoticeId);
if (iqc == null || !QcResultEnum.QUALIFIED.equals(iqc.getResult())) {
    throw exception(IQC_NOT_QUALIFIED);
}
```

### 踩坑：部分合格的入库处理

**问题**：IQC 检验部分合格、部分不合格时，入库数量处理不当。

**正确做法**：
1. 合格数量办理采购入库（ItemReceipt）
2. 不合格数量办理供应商退货（ReturnVendor）
3. 两个操作需要在同一事务中完成

---

## 6. 库存管理

### 踩坑：出库时库存不足

**问题**：并发出库导致库存变为负数。

**正确做法**：使用乐观锁扣减库存。

```sql
UPDATE mes_wm_material_stock
SET quantity = quantity - #{outQuantity}
WHERE id = #{stockId}
  AND quantity >= #{outQuantity}
```

### 踩坑：调拨单双向库存更新

**问题**：调拨操作只扣减了源库位库存，未增加目标库位库存。

**正确做法**：调拨必须同时更新两个库位的库存。

```java
@Transactional(rollbackFor = Exception.class)
public void executeTransfer(MesTransferDO transfer) {
    // 1. 扣减源库位库存
    materialStockService.deductStock(
        transfer.getFromWarehouseId(), transfer.getFromLocationId(),
        transfer.getItemId(), transfer.getQuantity()
    );
    // 2. 增加目标库位库存
    materialStockService.addStock(
        transfer.getToWarehouseId(), transfer.getToLocationId(),
        transfer.getItemId(), transfer.getQuantity()
    );
    // 3. 更新调拨单状态
    transferMapper.updateStatus(transfer.getId(), TransferStatusEnum.COMPLETED);
}
```

### 踩坑：盘点差异处理

**问题**：盘点结果直接覆盖库存，未经过审批流程。

**正确做法**：盘点差异需要审批后才能调整库存，避免误操作。

---

## 7. 设备状态联动

### 踩坑：维修完成后设备状态未恢复

**问题**：维修单完成后，设备状态仍为"维修中"，影响生产排产。

**正确做法**：维修单状态变更时联动更新设备状态。

```java
// 完成维修时
repairMapper.updateStatus(repairId, RepairStatusEnum.FINISHED);
machineryMapper.updateStatus(repair.getMachineryId(), MachineryStatusEnum.NORMAL);
```

### 踩坑：设备维修期间仍被分配任务

**问题**：设备状态为"维修中"时，仍被分配生产任务。

**正确做法**：分配任务时校验设备状态。

```java
MesMachineryDO machinery = machineryMapper.selectById(machineryId);
if (!MachineryStatusEnum.NORMAL.equals(machinery.getStatus())) {
    throw exception(MACHINERY_NOT_AVAILABLE);
}
```

---

## 8. 自动编码生成

### 踩坑：序列号并发重复

**问题**：多个请求同时生成编码，序列号重复。

**正确做法**：使用数据库行锁保证序列号唯一。

```java
@Transactional(rollbackFor = Exception.class)
public String generateCode(Long ruleId) {
    // 1. 查询并锁定记录（SELECT FOR UPDATE）
    MesAutoCodeRecordDO record = autoCodeRecordMapper.selectByRuleIdForUpdate(ruleId);
    // 2. 递增序列号
    record.setCurrentValue(record.getCurrentValue() + 1);
    autoCodeRecordMapper.updateById(record);
    // 3. 根据规则组装编码
    return buildCode(ruleId, record);
}
```

### 踩坑：按日期重置序列号

**问题**：跨天后序列号未重置，导致编码不符合预期。

**正确做法**：每次生成时检查当前日期，如果日期变化则重置序列号。

---

## 9. 工艺路线与 BOM

### 踩坑：工艺路线和 BOM 不匹配

**问题**：工单关联的工艺路线和 BOM 对应的产品不一致。

**正确做法**：创建工单时校验工艺路线和 BOM 是否属于同一产品。

```java
if (!route.getItemId().equals(bom.getItemId())) {
    throw exception(ROUTE_BOM_MISMATCH);
}
```

### 踩坑：BOM 子物料用量计算

**问题**：BOM 用量计算未考虑损耗率，导致领料不足。

**正确做法**：领料数量 = BOM 标准用量 * (1 + 损耗率) * 生产数量。

---

## 10. 检验模板与指标

### 踩坑：检验模板修改影响历史数据

**问题**：修改检验模板的指标上下限后，历史检验结果的判定标准不一致。

**正确做法**：检验模板修改后创建新版本，历史检验单关联旧版本模板。

### 踩坑：检验指标结果多次测量

**问题**：多次测量值的记录和判定逻辑不清晰。

**正确做法**：
1. 每次测量值记录到 `qc_indicator_result_detail`
2. 根据检验标准判定（取平均值/最大值/最小值）
3. 最终结果记录到 `qc_indicator_result`

---

## 11. 查询性能优化

### 踩坑：N+1 查询

**问题**：查询工单列表后逐个查询关联的物料、BOM 等信息。

**正确做法**：使用 VO Assembly 模式批量查询。

```java
// 1. 查询主表
List<MesWorkOrderDO> orders = workOrderMapper.selectPage(reqVO).getList();

// 2. 批量获取关联数据
Set<Long> itemIds = orders.stream().map(MesWorkOrderDO::getItemId).collect(Collectors.toSet());
Map<Long, MesItemDO> itemMap = itemService.getItemMap(itemIds);

// 3. 组装 VO
return orders.stream().map(order -> {
    MesWorkOrderRespVO vo = BeanUtils.toBean(order, MesWorkOrderRespVO.class);
    vo.setItemName(itemMap.get(order.getItemId())?.getName());
    return vo;
}).collect(Collectors.toList());
```

### 踩坑：大表分页查询缓慢

**问题**：仓库事务表（`mes_wm_transaction`）数据量大，分页查询缓慢。

**正确做法**：
- 必须按时间范围过滤，避免全表扫描
- 建议按月分表或归档历史数据
- 为常用查询字段添加组合索引

---

## 12. 事务管理

### 踩坑：跨域操作事务范围

**问题**：出入库操作涉及库存更新和事务记录，事务范围过大导致锁竞争。

**正确做法**：
- 将查询操作移到事务外
- 事务只包含写操作（更新库存、插入事务记录）
- 使用 `@Transactional(rollbackFor = Exception.class)` 显式指定回滚异常

### 踩坑：报工与库存联动

**问题**：产品入库操作在报工事务中失败，但报工已提交。

**正确做法**：报工和入库放在同一事务中，或使用消息队列最终一致性。

---

## 13. 错误码规范

### 踩坑：错误码不统一

**问题**：各域使用不同的错误码定义方式，难以维护。

**正确做法**：在 `ErrorCodeConstants.java` 中统一定义错误码。

```java
// 主数据域
ErrorCode ITEM_NOT_EXISTS = new ErrorCode(1_0XX_000_000, "物料不存在");
// 生产域
ErrorCode WORK_ORDER_NOT_EXISTS = new ErrorCode(1_0XX_000_000, "工单不存在");
// 质量域
ErrorCode IQC_NOT_EXISTS = new ErrorCode(1_0XX_000_000, "来料检验单不存在");
```

---

## 14. 最佳实践速查表

| 场景 | 建议 |
|------|------|
| 状态变更 | CAS 更新 + 状态机校验 |
| 库存扣减 | 乐观锁 `quantity >= #{outQuantity}` |
| 调拨操作 | 同一事务中扣减源库位 + 增加目标库位 |
| IQC 入库 | 先检验后入库，不合格走退货 |
| 编码生成 | SELECT FOR UPDATE 防止并发重复 |
| 报工校验 | 累计报工数不超过计划数 |
| 设备分配 | 校验设备状态为"正常" |
| VO 组装 | 批量查询 + Map 组装，避免 N+1 |
| 事务范围 | 只包含写操作，查询移到事务外 |
| 大表查询 | 必须按时间范围过滤 + 组合索引 |
| BOM 领料 | 标准用量 * (1 + 损耗率) * 生产数量 |
| 检验模板 | 修改创建新版本，不影响历史数据 |
