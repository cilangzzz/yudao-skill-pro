# 数据权限 API

## 概述

CRM 模块采用独立的数据权限机制，通过 CrmPermissionDO 实现细粒度的数据访问控制。每个业务记录都有对应的权限记录，控制哪些用户可以访问以及访问级别。权限校验通过 `@CrmPermission` 注解配合 AOP 切面实现声明式控制。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmPermissionController | `/crm/permission` | 数据权限管理接口 |

## 权限级别

| 级别 | 代码 | 说明 |
|------|------|------|
| OWNER | 1 | 负责人权限，拥有所有操作权限，可以删除、转移 |
| READ | 2 | 只读权限，只能查看数据 |
| WRITE | 3 | 读写权限，可以编辑数据但不能删除 |

## 业务类型枚举（CrmBizTypeEnum）

权限系统通过业务类型枚举区分不同业务实体的权限控制：

| 枚举值 | 说明 |
|--------|------|
| CRM_CUSTOMER | 客户 |
| CRM_CLUE | 线索 |
| CRM_CONTACT | 联系人 |
| CRM_BUSINESS | 商机 |
| CRM_CONTRACT | 合同 |
| CRM_RECEIVABLE | 回款 |
| CRM_PRODUCT | 产品 |

## 接口列表

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 获取权限列表 | GET | `/crm/permission/list` | `crm:permission:query` | 查询某条记录的权限列表 |
| 转移权限 | PUT | `/crm/permission/transfer` | `crm:permission:update` | 将负责人权限转移给其他用户 |
| 共享权限 | POST | `/crm/permission/share` | `crm:permission:update` | 为其他用户添加只读/读写权限 |
| 删除权限 | DELETE | `/crm/permission/delete` | `crm:permission:delete` | 移除某用户的权限 |

## 核心数据模型

### CrmPermissionDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| biz_type | INT | 业务类型（对应 CrmBizTypeEnum） |
| biz_id | BIGINT | 业务ID（关联具体记录） |
| user_id | BIGINT | 用户ID |
| level | INT | 权限级别（对应 CrmPermissionLevelEnum） |

### 索引

| 索引名 | 列 | 说明 |
|--------|-----|------|
| idx_biz | biz_type, biz_id | 按业务查询权限 |
| idx_user | user_id | 按用户查询权限 |

## 使用方式

### 注解声明式权限校验

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

## 业务规则

1. **自动创建**：创建业务记录时自动为创建者创建 OWNER 级别权限
2. **权限转移**：转移负责人时，原负责人的 OWNER 权限降为 WRITE，新负责人获得 OWNER 权限
3. **权限共享**：可以为其他用户添加 READ 或 WRITE 级别权限
4. **公海池影响**：客户放入公海时，相关权限会被清理
5. **AOP 校验**：`CrmPermissionAspect` 拦截 `@CrmPermission` 注解方法，自动校验当前用户是否满足权限要求

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/permission/CrmPermissionService.java` | 权限服务接口 |
| `controller/admin/permission/CrmPermissionController.java` | 权限控制器 |
| `dal/dataobject/permission/CrmPermissionDO.java` | 权限实体类 |
| `enums/common/CrmBizTypeEnum.java` | 业务类型枚举 |
| `enums/permission/CrmPermissionLevelEnum.java` | 权限级别枚举 |
| `framework/permission/core/annotations/CrmPermission.java` | 权限注解定义 |
| `framework/permission/core/aspect/CrmPermissionAspect.java` | 权限 AOP 切面 |
