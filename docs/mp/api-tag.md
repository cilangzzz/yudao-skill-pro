# 标签管理 API

> 对应 Controller：`MpTagController` | 路径前缀：`/mp/tag`

## 功能说明

管理公众号粉丝标签，支持标签的创建、修改、删除、同步。标签用于粉丝分组管理，支持按标签群发消息。

## 数据模型

### MpTagDO

继承 `BaseDO`。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| tag_id | Long | 微信标签 ID |
| name | String | 标签名称 |
| count | Integer | 标签下粉丝数 |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |

### 索引

- `idx_account_id` - 账号 ID 索引

## 核心服务

### MpTagService

| 方法 | 说明 |
|------|------|
| 创建标签 | 创建粉丝标签 |
| 更新标签 | 修改标签名称 |
| 删除标签 | 删除标签 |
| 同步标签 | 从微信 API 同步标签列表 |
| 查询标签列表 | 查询当前公众号所有标签 |

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- `MpUserDO.tag_ids` 关联标签，表示粉丝所属标签

## 设计要点

- `tag_id` 为微信侧标签 ID，本地 `id` 为数据库主键
- 标签下粉丝数通过 `count` 字段缓存，避免实时查询
- 标签同步时与微信 API 保持一致
