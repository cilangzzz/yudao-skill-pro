# 跟进记录 API

## 概述

跟进记录用于记录销售人员与客户的沟通历史，支持关联多种业务类型（客户、商机、合同等），支持文字、图片、附件等多种内容形式。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmFollowUpRecordController | `/crm/follow-up-record` | 跟进记录管理接口 |
| CrmOperateLogController | `/crm/operate-log` | 操作日志查询接口 |

## 接口列表

### 跟进记录

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建跟进记录 | POST | `/crm/follow-up-record/create` | `crm:followup:create` | 记录跟进内容 |
| 删除跟进记录 | DELETE | `/crm/follow-up-record/delete` | `crm:followup:delete` | 删除跟进记录 |
| 获取跟进记录详情 | GET | `/crm/follow-up-record/get` | `crm:followup:query` | 查询详情 |
| 跟进记录列表 | GET | `/crm/follow-up-record/list` | `crm:followup:query` | 按业务类型和业务ID查询 |

### 操作日志

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 操作日志列表 | GET | `/crm/operate-log/list` | `crm:operate-log:query` | 查询业务操作日志 |

## 核心数据模型

### CrmFollowUpRecordDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| biz_type | INT | 业务类型（对应 CrmBizTypeEnum） |
| biz_id | BIGINT | 业务ID（关联具体记录） |
| type | INT | 跟进类型 |
| content | VARCHAR | 跟进内容 |
| next_time | DATETIME | 下次联系时间 |
| pic_urls | VARCHAR | 图片URL列表 |
| file_urls | VARCHAR | 附件URL列表 |
| business_ids | VARCHAR | 关联商机ID列表 |
| contact_ids | VARCHAR | 关联联系人ID列表 |

## 业务规则

1. **多业务关联**：跟进记录通过 biz_type 和 biz_id 关联任意业务类型（客户、商机、合同等）
2. **关联商机和联系人**：创建跟进记录时可同时关联多个商机（business_ids）和联系人（contact_ids）
3. **下次联系时间**：记录下次联系时间，用于提醒销售人员及时跟进
4. **自动更新跟进状态**：创建跟进记录后，自动更新对应业务记录的 contact_last_time、contact_last_content、contact_next_time 等字段
5. **操作日志**：通过 @LogRecord 注解自动记录关键业务操作日志，可在操作日志接口查询

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/followup/CrmFollowUpRecordService.java` | 跟进记录服务接口 |
| `controller/admin/followup/CrmFollowUpRecordController.java` | 跟进记录控制器 |
| `controller/admin/followup/CrmOperateLogController.java` | 操作日志控制器 |
| `dal/dataobject/followup/CrmFollowUpRecordDO.java` | 跟进记录实体类 |
