# 商机管理 API

## 概述

商机代表销售机会，是销售漏斗的核心对象。商机通过状态组（StatusType）和状态（Status）实现可配置的销售漏斗阶段管理，支持赢单/输单/无效三种结束状态。商机可以关联多个产品。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmBusinessController | `/crm/business` | 商机管理接口 |
| CrmBusinessStatusController | `/crm/business-status` | 商机状态组与状态管理接口 |

## 接口列表

### 商机 CRUD

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建商机 | POST | `/crm/business/create` | `crm:business:create` | 创建商机并分配权限 |
| 更新商机 | PUT | `/crm/business/update` | `crm:business:update` | 需要 WRITE 权限 |
| 删除商机 | DELETE | `/crm/business/delete` | `crm:business:delete` | 需要 OWNER 权限 |
| 获取商机详情 | GET | `/crm/business/get` | `crm:business:query` | 需要 READ 权限 |
| 商机分页查询 | GET | `/crm/business/page` | `crm:business:query` | 按客户、状态等条件过滤 |

### 商机状态操作

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 更新商机状态 | PUT | `/crm/business/update-status` | `crm:business:update` | 切换销售漏斗阶段 |
| 商机赢单 | PUT | `/crm/business/win` | `crm:business:update` | 标记为赢单 |
| 商机输单 | PUT | `/crm/business/lose` | `crm:business:update` | 标记为输单 |

### 商机状态组配置

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建状态组 | POST | `/crm/business-status/create-type` | `crm:business:status:create` | 创建新的销售漏斗阶段组 |
| 更新状态组 | PUT | `/crm/business-status/update-type` | `crm:business:status:update` | 编辑状态组 |
| 删除状态组 | DELETE | `/crm/business-status/delete-type` | `crm:business:status:delete` | 删除状态组 |
| 获取状态组详情 | GET | `/crm/business-status/get-type` | `crm:business:status:query` | 查询状态组及其状态列表 |
| 状态组列表 | GET | `/crm/business-status/list-type` | `crm:business:status:query` | 查询所有状态组 |
| 创建状态 | POST | `/crm/business-status/create` | `crm:business:status:create` | 为状态组添加阶段 |
| 更新状态 | PUT | `/crm/business-status/update` | `crm:business:status:update` | 编辑阶段（名称、赢单率） |
| 删除状态 | DELETE | `/crm/business-status/delete` | `crm:business:status:delete` | 删除阶段 |

## 核心数据模型

### CrmBusinessDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 商机名称 |
| customer_id | BIGINT | 客户ID |
| follow_up_status | TINYINT | 跟进状态 |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| status_type_id | BIGINT | 商机状态组ID |
| status_id | BIGINT | 商机状态ID |
| end_status | INT | 结束状态（赢单/输单/无效） |
| end_remark | VARCHAR | 结束备注 |
| deal_time | DATETIME | 预计成交日期 |
| total_product_price | DECIMAL | 产品总金额 |
| discount_percent | DECIMAL | 整单折扣 |
| total_price | DECIMAL | 商机总金额 |
| remark | VARCHAR | 备注 |

### CrmBusinessStatusTypeDO（商机状态组）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 状态组名称 |
| dept_ids | VARCHAR | 使用的部门ID列表 |

### CrmBusinessStatusDO（商机状态）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| type_id | BIGINT | 状态组ID |
| name | VARCHAR | 状态名称 |
| percent | INT | 赢单率百分比 |
| sort | INT | 排序 |

### CrmBusinessProductDO（商机产品关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| business_id | BIGINT | 商机ID |
| product_id | BIGINT | 产品ID |
| count | DECIMAL | 数量 |
| price | DECIMAL | 单价 |

## 业务规则

1. **销售漏斗**：商机通过 status_type_id 关联状态组，status_id 关联具体阶段，每个阶段有赢单率
2. **状态组按部门**：状态组通过 dept_ids 关联适用部门，不同部门可使用不同的销售漏斗
3. **结束状态**：商机只能在最终阶段执行赢单/输单操作
4. **商机产品**：商机可以关联多个产品，记录数量和单价，自动计算总金额
5. **整单折扣**：支持设置整单折扣百分比

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/business/CrmBusinessService.java` | 商机服务接口 |
| `controller/admin/business/CrmBusinessController.java` | 商机控制器 |
| `controller/admin/business/CrmBusinessStatusController.java` | 状态组控制器 |
| `dal/dataobject/business/CrmBusinessDO.java` | 商机实体类 |
| `dal/dataobject/business/CrmBusinessStatusTypeDO.java` | 状态组实体 |
| `dal/dataobject/business/CrmBusinessStatusDO.java` | 状态实体 |
| `dal/dataobject/business/CrmBusinessProductDO.java` | 商机产品关联实体 |
