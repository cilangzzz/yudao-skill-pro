# CRM 模块常见陷阱与注意事项

## 1. 数据权限相关

### 1.1 忘记添加 @CrmPermission 注解

**问题**：新增 Service 方法时忘记添加 `@CrmPermission` 注解，导致任意有接口访问权限的用户都能操作任意数据。

**正确做法**：
```java
// 查询需要 READ 权限
@CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#id", level = CrmPermissionLevelEnum.READ)
public CrmCustomerDO getCustomer(Long id)

// 更新需要 WRITE 权限
@CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#updateReqVO.id", level = CrmPermissionLevelEnum.WRITE)
public void updateCustomer(CrmCustomerSaveReqVO updateReqVO)

// 删除需要 OWNER 权限
@CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#id", level = CrmPermissionLevelEnum.OWNER)
public void deleteCustomer(Long id)
```

**规则**：所有涉及数据操作的方法都必须添加 `@CrmPermission` 注解。

### 1.2 新增业务类型忘记注册

**问题**：新增 CRM 业务实体时，忘记在 `CrmBizTypeEnum` 中添加对应的业务类型枚举，导致权限系统无法识别。

**正确做法**：在 `CrmBizTypeEnum` 中添加新的枚举值，并确保 `CrmPermissionAspect` 能正确处理该类型。

---

## 2. 客户公海池相关

### 2.1 公海回收时未清理关联数据

**问题**：客户放入公海时，未同步清理联系人、商机、合同的负责人信息，导致原负责人仍能看到数据。

**正确做法**：客户放入公海时，需要：
1. 清空客户的 owner_user_id
2. 清空关联联系人的 owner_user_id
3. 根据业务需求决定是否清空商机、合同的负责人

### 2.2 领取客户时未检查限制

**问题**：从公海领取客户时，未检查用户是否达到拥有客户上限。

**正确做法**：领取前调用 `validateCustomerExceedOwnerLimit()` 校验限制配置。

### 2.3 公海池配置未生效

**问题**：修改公海池配置后，未触发定时任务重新计算，导致配置不生效。

**注意**：公海池的自动回收依赖定时任务，配置修改后需要等待下次任务执行。

---

## 3. 客户转移相关

### 3.1 转移时权限未同步更新

**问题**：转移客户负责人时，未正确更新权限表，导致新负责人无权限或旧负责人仍保留高权限。

**正确做法**：转移时需要：
1. 将原负责人的 OWNER 权限降为 WRITE（或删除）
2. 为新负责人创建 OWNER 权限
3. 根据选择同步转移联系人、商机、合同的权限

### 3.2 转移时未更新 owner_time

**问题**：转移负责人后，未更新 `owner_time` 字段，影响公海池的到期计算。

---

## 4. 商机管理相关

### 4.1 状态组与部门关联

**问题**：创建商机时选择了不属于自己部门的状态组，导致销售漏斗统计异常。

**注意**：状态组通过 `dept_ids` 关联适用部门，创建商机时应只展示本部门可用的状态组。

### 4.2 赢单/输单操作时机

**问题**：在非最终阶段执行赢单/输单操作，导致数据不一致。

**正确做法**：赢单/输单操作应只在状态组的最后一个阶段执行，前端需要做相应限制。

### 4.3 商机产品金额计算

**问题**：更新商机产品后，未重新计算 `total_product_price` 和 `total_price`。

**正确做法**：每次更新商机产品后，需要重新汇总计算产品总金额，并应用折扣。

---

## 5. 合同与回款相关

### 5.1 审批状态同步

**问题**：合同/回款的审批状态通过 Listener 异步更新，在审批完成的瞬间查询可能获取到旧状态。

**注意**：`CrmContractStatusListener` 和 `CrmReceivableStatusListener` 监听 BPM 审批结果，存在短暂的延迟。

### 5.2 回款计划与实际回款关联

**问题**：创建实际回款时未关联回款计划（plan_id），导致回款计划状态无法更新。

**正确做法**：创建回款时，如果对应有回款计划，应设置 `plan_id` 并更新回款计划的 `receivable_id`。

### 5.3 合同删除时未清理关联

**问题**：删除合同时，未清理关联的回款计划和回款记录。

---

## 6. 事务管理相关

### 6.1 AOP 代理导致事务失效

**问题**：在 Service 实现类内部调用 `@Transactional` 方法时，由于 Spring AOP 代理机制，事务不生效。

**正确做法**：使用 `getSelf()` 方法获取代理对象再调用：
```java
// 通过 getSelf() 获取代理对象，确保事务生效
self().createCustomer(createReqVO, userId);
```

### 6.2 批量操作未加事务

**问题**：批量创建权限、批量更新等操作未添加 `@Transactional`，部分失败时数据不一致。

**正确做法**：涉及多表操作的方法统一添加 `@Transactional(rollbackFor = Exception.class)`。

---

## 7. 操作日志相关

### 7.1 LogRecordContext 变量未设置

**问题**：使用 `@LogRecord` 注解但未在方法中设置 `LogRecordContext` 变量，导致日志内容为空。

**正确做法**：
```java
@LogRecord(type = CRM_CUSTOMER_TYPE, subType = CRM_CUSTOMER_CREATE_SUB_TYPE,
           bizNo = "{{#customer.id}}", success = CRM_CUSTOMER_CREATE_SUCCESS)
public Long createCustomer(CrmCustomerSaveReqVO createReqVO, Long userId) {
    // ... 业务逻辑 ...
    // 必须设置变量供日志模板使用
    LogRecordContext.putVariable("customer", customer);
    return customer.getId();
}
```

---

## 8. 错误码相关

### 8.1 错误码格式

CRM 模块错误码前缀为 `1-020-xxx-xxx`，格式为 `1_020_xxx_xxx`。

**常用错误码**：

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 1_020_006_000 | CUSTOMER_NOT_EXISTS | 客户不存在 |
| 1_020_002_000 | BUSINESS_NOT_EXISTS | 商机不存在 |
| 1_020_007_001 | CRM_PERMISSION_DENIED | 没有权限 |

**正确做法**：使用 `throw exception(XXX)` 抛出业务异常，不要直接 new 异常。

---

## 9. 性能相关

### 8.1 权限查询 N+1 问题

**问题**：分页查询时，对每条记录都查询一次权限表，产生 N+1 查询。

**正确做法**：批量查询权限数据，或在 Mapper 层通过 JOIN 查询一次性获取。

### 8.2 统计查询未加索引

**问题**：统计接口按时间范围查询时，如果表数据量大且未在时间字段上加索引，查询缓慢。

**注意**：确保 `create_time`、`contact_last_time` 等常用查询字段有索引支撑。
