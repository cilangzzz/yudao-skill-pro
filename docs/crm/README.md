# CRM 客户关系管理模块

## 模块概述

CRM（Customer Relationship Management）模块是客户关系管理系统的核心，解决企业销售过程中的客户管理、商机跟进、合同签订、回款管理等全流程业务问题。模块路径：`yudao-module-crm`。

### 核心业务场景

1. **线索管理**：潜在客户信息的录入与转化
2. **客户管理**：客户信息维护、公海池机制、客户分配与转移
3. **联系人管理**：客户关键联系人信息管理
4. **商机管理**：销售机会的全生命周期管理（销售漏斗）
5. **合同管理**：合同签订与审批流程
6. **回款管理**：回款计划与实际回款跟踪
7. **产品管理**：产品信息与分类管理
8. **数据统计**：销售漏斗、业绩排名等统计分析

---

## 核心功能点

| 业务域 | 功能点 | Controller | 权限标识 |
|--------|--------|------------|----------|
| 客户管理 | 客户 CRUD、转移、公海池回收/领取 | CrmCustomerController | `crm:customer:*` |
| 客户配置 | 公海池配置、客户限制配置 | CrmCustomerPoolConfigController / CrmCustomerLimitConfigController | `crm:customer:config:*` |
| 线索管理 | 线索 CRUD、线索转化 | CrmClueController | `crm:clue:*` |
| 联系人管理 | 联系人 CRUD | CrmContactController | `crm:contact:*` |
| 商机管理 | 商机 CRUD、状态变更、赢单/输单 | CrmBusinessController | `crm:business:*` |
| 商机配置 | 商机状态组与状态管理 | CrmBusinessStatusController | `crm:business:status:*` |
| 合同管理 | 合同 CRUD、审批 | CrmContractController | `crm:contract:*` |
| 合同配置 | 合同押金配置 | CrmContractConfigController | `crm:contract:config:*` |
| 回款管理 | 回款 CRUD、审批 | CrmReceivableController | `crm:receivable:*` |
| 回款计划 | 回款计划 CRUD | CrmReceivablePlanController | `crm:receivable:plan:*` |
| 产品管理 | 产品 CRUD | CrmProductController | `crm:product:*` |
| 产品分类 | 分类 CRUD | CrmProductCategoryController | `crm:product:category:*` |
| 数据权限 | 权限查询、转移、共享 | CrmPermissionController | `crm:permission:*` |
| 跟进记录 | 跟进记录 CRUD | CrmFollowUpRecordController | `crm:followup:*` |
| 操作日志 | 日志查询 | CrmOperateLogController | `crm:operate-log:*` |
| 客户统计 | 客户相关数据统计 | CrmStatisticsCustomerController | `crm:statistics:*` |
| 漏斗统计 | 销售漏斗分析 | CrmStatisticsFunnelController | `crm:statistics:*` |
| 业绩统计 | 销售业绩分析 | CrmStatisticsPerformanceController | `crm:statistics:*` |
| 客户画像 | 客户画像分析 | CrmStatisticsPortraitController | `crm:statistics:*` |
| 排行榜 | 销售排行 | CrmStatisticsRankController | `crm:statistics:*` |

---

## API 索引

| 文档 | 业务域 | 说明 |
|------|--------|------|
| [api-customer.md](api-customer.md) | 客户管理 | 客户 CRUD、转移、公海池、限制配置 |
| [api-clue.md](api-clue.md) | 线索管理 | 线索 CRUD、转化 |
| [api-contact.md](api-contact.md) | 联系人管理 | 联系人 CRUD |
| [api-business.md](api-business.md) | 商机管理 | 商机 CRUD、状态组与状态配置 |
| [api-contract.md](api-contract.md) | 合同管理 | 合同 CRUD、审批、配置 |
| [api-receivable.md](api-receivable.md) | 回款管理 | 回款 CRUD、回款计划 |
| [api-product.md](api-product.md) | 产品管理 | 产品 CRUD、产品分类 |
| [api-permission.md](api-permission.md) | 数据权限 | 权限查询、转移、共享 |
| [api-followup.md](api-followup.md) | 跟进记录 | 跟进记录 CRUD |
| [api-statistics.md](api-statistics.md) | 数据统计 | 客户统计、漏斗、业绩、画像、排行榜 |

---

## 数据模型

详细数据模型请参阅 [data-model.md](data-model.md)。

### 核心聚合根

| 聚合根 | 关联实体 | 说明 |
|--------|----------|------|
| **客户（CrmCustomerDO）** | 商机、联系人、合同、回款、回款计划、跟进记录 | CRM 系统核心聚合根 |
| **线索（CrmClue）** | -- | 潜在客户，可转化为正式客户 |
| **产品（CrmProductDO）** | 产品分类 | 产品信息管理，被商机和合同引用 |

---

## 设计模式

| 模式 | 位置 | 用途 |
|------|------|------|
| AOP 权限校验 | `@CrmPermission` + `CrmPermissionAspect` | 通过注解声明数据权限要求，AOP 自动校验 |
| 策略模式 | `CrmBizTypeEnum` | 统一处理不同业务类型的权限校验逻辑 |
| 观察者模式 | `CrmContractStatusListener` / `CrmReceivableStatusListener` | 监听 BPM 审批状态变更，更新业务状态 |
| Builder 模式 | 所有 DO 实体类 `@Builder` | 简化复杂对象的构建 |
| 代理模式 | `CrmCustomerServiceImpl.getSelf()` | 解决 AOP 事务代理问题 |

---

## 依赖关系

### 内部模块依赖

| 模块 | API | 用途 |
|------|-----|------|
| yudao-module-system | AdminUserApi | 获取用户信息、校验用户 |
| yudao-module-system | DeptApi | 获取部门信息 |
| yudao-module-bpm | 流程审批 | 合同、回款的审批流程 |

### 外部库依赖

| 库 | 版本 | 用途 |
|----|------|------|
| MyBatis-Plus | 3.x | ORM 框架 |
| Spring Security | 5.x | 权限校验 |
| Swagger/OpenAPI | 3.x | API 文档 |
| EasyExcel | 3.x | Excel 导入导出 |
| LogRecord | mzt-biz-log | 操作日志记录 |

---

## 关键文件清单

| 文件 | 说明 |
|------|------|
| `dal/dataobject/customer/CrmCustomerDO.java` | 客户实体类，核心聚合根 |
| `dal/dataobject/business/CrmBusinessDO.java` | 商机实体类，销售漏斗核心 |
| `dal/dataobject/permission/CrmPermissionDO.java` | 数据权限实体 |
| `service/customer/CrmCustomerService.java` | 客户服务接口 |
| `service/customer/CrmCustomerServiceImpl.java` | 客户服务实现（公海池、转移等） |
| `service/permission/CrmPermissionService.java` | 数据权限服务接口 |
| `controller/admin/customer/CrmCustomerController.java` | 客户控制器 |
| `enums/common/CrmBizTypeEnum.java` | 业务类型枚举 |
| `enums/permission/CrmPermissionLevelEnum.java` | 权限级别枚举 |
| `enums/ErrorCodeConstants.java` | 错误码常量 |
| `framework/permission/core/annotations/CrmPermission.java` | 数据权限注解 |

---

## 详细文档

- [数据模型](data-model.md) - 数据表设计、ER 关系
- [常见陷阱](pitfalls.md) - 开发中的注意事项与踩坑点
