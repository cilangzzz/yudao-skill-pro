# 合同管理 API

## 概述

合同管理支持合同的创建、审批、查询等全流程操作。合同关联客户和商机，支持关联多个产品，并通过 BPM 模块实现审批流程。合同审批状态通过监听器（Listener）自动同步。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmContractController | `/crm/contract` | 合同管理接口 |
| CrmContractConfigController | `/crm/contract-config` | 合同配置接口 |

## 接口列表

### 合同 CRUD

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建合同 | POST | `/crm/contract/create` | `crm:contract:create` | 创建合同并发起审批 |
| 更新合同 | PUT | `/crm/contract/update` | `crm:contract:update` | 需要 WRITE 权限 |
| 删除合同 | DELETE | `/crm/contract/delete` | `crm:contract:delete` | 需要 OWNER 权限 |
| 获取合同详情 | GET | `/crm/contract/get` | `crm:contract:query` | 需要 READ 权限 |
| 合同分页查询 | GET | `/crm/contract/page` | `crm:contract:query` | 按客户、审批状态等过滤 |

### 合同配置

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 获取合同配置 | GET | `/crm/contract-config/get` | `crm:contract:config:query` | 查询押金等配置 |
| 更新合同配置 | PUT | `/crm/contract-config/update` | `crm:contract:config:update` | 设置押金开关和比例 |

## 核心数据模型

### CrmContractDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 合同名称 |
| no | VARCHAR | 合同编号 |
| customer_id | BIGINT | 客户ID |
| business_id | BIGINT | 商机ID |
| contact_last_time | DATETIME | 最后跟进时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| process_instance_id | VARCHAR | 工作流实例ID |
| audit_status | INT | 审批状态 |
| order_date | DATETIME | 下单日期 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| total_product_price | DECIMAL | 产品总金额 |
| discount_percent | DECIMAL | 整单折扣 |
| total_price | DECIMAL | 合同总金额 |
| sign_contact_id | BIGINT | 客户签约人ID |
| sign_user_id | BIGINT | 公司签约人ID |
| remark | VARCHAR | 备注 |

### CrmContractConfigDO（合同配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| deposit_enabled | TINYINT | 是否开启押金 |
| deposit_percent | DECIMAL | 押金比例 |

### CrmContractProductDO（合同产品关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| contract_id | BIGINT | 合同ID |
| product_id | BIGINT | 产品ID |
| count | DECIMAL | 数量 |
| price | DECIMAL | 单价 |

## 业务规则

1. **审批流程**：合同创建后通过 BPM 模块发起审批，process_instance_id 记录工作流实例
2. **审批状态同步**：通过 CrmContractStatusListener 监听 BPM 审批结果，自动更新 audit_status
3. **关联商机**：合同可关联商机（business_id），一个商机可对应多个合同
4. **合同产品**：通过 crm_contract_product 关联多个产品，记录数量和单价
5. **签约人**：区分客户签约人（sign_contact_id）和公司签约人（sign_user_id）
6. **押金配置**：可配置是否开启押金及押金比例

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/contract/CrmContractService.java` | 合同服务接口 |
| `controller/admin/contract/CrmContractController.java` | 合同控制器 |
| `controller/admin/contract/CrmContractConfigController.java` | 合同配置控制器 |
| `dal/dataobject/contract/CrmContractDO.java` | 合同实体类 |
| `dal/dataobject/contract/CrmContractConfigDO.java` | 合同配置实体 |
| `dal/dataobject/contract/CrmContractProductDO.java` | 合同产品关联实体 |
| `CrmContractStatusListener` | 审批状态监听器 |
