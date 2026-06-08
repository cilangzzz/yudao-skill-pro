# 客户管理 API

## 概述

客户是 CRM 系统的核心聚合根，关联商机、联系人、合同、回款等所有业务对象。客户管理包含客户 CRUD、负责人转移、公海池机制（自动回收与领取）、客户限制配置等功能。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmCustomerController | `/crm/customer` | 客户管理接口 |
| CrmCustomerPoolConfigController | `/crm/customer-pool-config` | 公海池配置接口 |
| CrmCustomerLimitConfigController | `/crm/customer-limit-config` | 客户限制配置接口 |

## 接口列表

### 客户 CRUD

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建客户 | POST | `/crm/customer/create` | `crm:customer:create` | 创建客户并分配负责人权限 |
| 更新客户 | PUT | `/crm/customer/update` | `crm:customer:update` | 需要 WRITE 权限 |
| 删除客户 | DELETE | `/crm/customer/delete` | `crm:customer:delete` | 需要 OWNER 权限 |
| 获取客户详情 | GET | `/crm/customer/get` | `crm:customer:query` | 需要 READ 权限 |
| 客户分页查询 | GET | `/crm/customer/page` | `crm:customer:query` | 支持名称、负责人等条件过滤 |
| 客户列表查询 | GET | `/crm/customer/list` | -- | 轻量级列表，用于下拉选择 |
| 客户导入 | POST | `/crm/customer/import` | `crm:customer:import` | Excel 批量导入 |
| 客户导出 | GET | `/crm/customer/export` | `crm:customer:export` | Excel 导出 |

### 客户转移

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 转移客户 | PUT | `/crm/customer/transfer` | `crm:customer:update` | 支持同时转移联系人、商机、合同 |

### 公海池操作

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 放入公海 | PUT | `/crm/customer/put-pool` | `crm:customer:update` | 将客户放入公海池 |
| 领取客户 | PUT | `/crm/customer/take-pool` | `crm:customer:update` | 从公海池领取客户 |
| 分配客户 | PUT | `/crm/customer/distribute-pool` | `crm:customer:update` | 管理员分配公海客户 |

### 公海池配置

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 获取公海池配置 | GET | `/crm/customer-pool-config/get` | `crm:customer:config:query` | 查询公海池规则 |
| 更新公海池配置 | PUT | `/crm/customer-pool-config/update` | `crm:customer:config:update` | 设置自动回收天数、提醒等 |

### 客户限制配置

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 获取限制配置 | GET | `/crm/customer-limit-config/get` | `crm:customer:config:query` | 查询拥有上限/锁定上限 |
| 更新限制配置 | PUT | `/crm/customer-limit-config/update` | `crm:customer:config:update` | 设置客户数量限制 |

## 核心数据模型

### CrmCustomerDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 客户名称 |
| follow_up_status | TINYINT | 跟进状态 |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_last_content | VARCHAR | 最后跟进内容 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| owner_time | DATETIME | 成为负责人时间 |
| lock_status | TINYINT | 锁定状态 |
| deal_status | TINYINT | 成交状态 |
| mobile | VARCHAR | 手机号 |
| telephone | VARCHAR | 电话 |
| qq | VARCHAR | QQ |
| wechat | VARCHAR | 微信 |
| email | VARCHAR | 邮箱 |
| area_id | INT | 地区ID |
| detail_address | VARCHAR | 详细地址 |
| industry_id | INT | 所属行业 |
| level | INT | 客户等级 |
| source | INT | 客户来源 |
| remark | VARCHAR | 备注 |

### 索引

| 索引名 | 列 |
|--------|-----|
| idx_owner_user_id | owner_user_id |
| idx_name | name |

## 业务规则

1. **创建客户时**：自动校验负责人是否达到拥有客户上限；自动创建 OWNER 级别数据权限
2. **公海池机制**：配置未跟进天数和未成交天数，到期自动回收；支持提前提醒
3. **客户转移**：支持选择是否同时转移联系人、商机、合同的负责人
4. **数据权限**：查询需要 READ，更新需要 WRITE，删除/转移需要 OWNER

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/customer/CrmCustomerService.java` | 客户服务接口 |
| `service/customer/CrmCustomerServiceImpl.java` | 客户服务实现 |
| `controller/admin/customer/CrmCustomerController.java` | 客户控制器 |
| `dal/dataobject/customer/CrmCustomerDO.java` | 客户实体类 |
| `dal/dataobject/customer/CrmCustomerPoolConfigDO.java` | 公海池配置实体 |
| `dal/dataobject/customer/CrmCustomerLimitConfigDO.java` | 客户限制配置实体 |
