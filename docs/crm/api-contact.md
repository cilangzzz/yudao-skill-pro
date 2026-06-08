# 联系人管理 API

## 概述

联系人是客户的关键联系人信息，一个客户可以有多个联系人。联系人支持关联多个商机（多对多关系），并可通过 parent_id 维护上下级关系。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmContactController | `/crm/contact` | 联系人管理接口 |

## 接口列表

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建联系人 | POST | `/crm/contact/create` | `crm:contact:create` | 创建联系人并分配权限 |
| 更新联系人 | PUT | `/crm/contact/update` | `crm:contact:update` | 需要 WRITE 权限 |
| 删除联系人 | DELETE | `/crm/contact/delete` | `crm:contact:delete` | 需要 OWNER 权限 |
| 获取联系人详情 | GET | `/crm/contact/get` | `crm:contact:query` | 需要 READ 权限 |
| 联系人分页查询 | GET | `/crm/contact/page` | `crm:contact:query` | 按客户、姓名等条件过滤 |
| 联系人列表查询 | GET | `/crm/contact/list` | `crm:contact:query` | 轻量级列表 |

## 核心数据模型

### CrmContactDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 联系人姓名 |
| customer_id | BIGINT | 客户ID |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_last_content | VARCHAR | 最后跟进内容 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| mobile | VARCHAR | 手机号 |
| telephone | VARCHAR | 电话 |
| email | VARCHAR | 邮箱 |
| qq | BIGINT | QQ |
| wechat | VARCHAR | 微信 |
| area_id | INT | 地区ID |
| detail_address | VARCHAR | 详细地址 |
| sex | INT | 性别 |
| master | TINYINT | 是否关键决策人 |
| post | VARCHAR | 职位 |
| parent_id | BIGINT | 直属上级ID |
| remark | VARCHAR | 备注 |

### CrmContactBusinessDO（联系人商机关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| contact_id | BIGINT | 联系人ID |
| business_id | BIGINT | 商机ID |

## 业务规则

1. **关联客户**：联系人必须关联一个客户（customer_id 为必填）
2. **多对多商机**：通过 crm_contact_business 关联表实现联系人与商机的多对多关系
3. **上下级关系**：通过 parent_id 维护联系人之间的上下级关系
4. **关键决策人**：master 字段标识是否为关键决策人
5. **客户公海回收**：客户放入公海时，联系人负责人会被清空

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/contact/CrmContactService.java` | 联系人服务接口 |
| `controller/admin/contact/CrmContactController.java` | 联系人控制器 |
| `dal/dataobject/contact/CrmContactDO.java` | 联系人实体类 |
| `dal/dataobject/contact/CrmContactBusinessDO.java` | 联系人商机关联实体 |
