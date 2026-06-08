# 线索管理 API

## 概述

线索是潜在客户信息的载体，记录尚未正式建立客户关系的销售机会。线索可以转化为正式客户，转化后自动创建客户记录。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmClueController | `/crm/clue` | 线索管理接口 |

## 接口列表

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建线索 | POST | `/crm/clue/create` | `crm:clue:create` | 录入潜在客户信息 |
| 更新线索 | PUT | `/crm/clue/update` | `crm:clue:update` | 编辑线索信息 |
| 删除线索 | DELETE | `/crm/clue/delete` | `crm:clue:delete` | 删除线索 |
| 获取线索详情 | GET | `/crm/clue/get` | `crm:clue:query` | 查询线索详情 |
| 线索分页查询 | GET | `/crm/clue/page` | `crm:clue:query` | 分页查询线索列表 |
| 线索转化 | POST | `/crm/clue/transform` | `crm:clue:update` | 将线索转化为正式客户 |

## 核心数据模型

### CrmClueDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 线索名称 |
| follow_up_status | TINYINT | 跟进状态 |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_last_content | VARCHAR | 最后跟进内容 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| transform_status | TINYINT | 转化状态 |
| customer_id | BIGINT | 转化后的客户ID |
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

## 业务规则

1. **线索转化**：转化时自动创建客户记录，建立线索与客户的关联关系（customer_id）
2. **转化后不可逆**：已转化的线索不能再次转化
3. **负责人机制**：线索同样有负责人字段，转化后负责人默认继承为客户的负责人

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/clue/CrmClueService.java` | 线索服务接口 |
| `controller/admin/clue/CrmClueController.java` | 线索控制器 |
| `dal/dataobject/clue/CrmClueDO.java` | 线索实体类 |
