# 公众号账号管理 API

> 对应 Controller：`MpAccountController` | 路径前缀：`/mp/account`

## 功能说明

管理公众号账号的增删改查，包括 AppId、AppSecret、Token、AES Key 等配置信息。每个账号对应一个微信公众号，支持多账号并行管理。

## 数据模型

### MpAccountDO

继承 `TenantBaseDO`，支持多租户隔离。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| name | String | 公众号名称 |
| account | String | 公众号账号 |
| app_id | String | 公众号 AppId（唯一索引） |
| app_secret | String | 公众号密钥 |
| token | String | 公众号 Token |
| aes_key | String | 消息加解密密钥 |
| qr_code_url | String | 二维码图片 URL |
| remark | String | 备注 |

### 索引

- `uk_app_id` - AppId 唯一索引

## 核心服务

### MpAccountService

| 方法 | 说明 |
|------|------|
| 创建账号 | 保存公众号配置信息 |
| 更新账号 | 修改公众号配置 |
| 删除账号 | 删除公众号及其关联数据 |
| 获取账号 | 根据 ID 或 AppId 获取账号信息 |
| 分页查询 | 按条件分页查询账号列表 |

## 与其他模块的关系

- `mp_user`、`mp_message`、`mp_material`、`mp_menu`、`mp_auto_reply`、`mp_message_template`、`mp_tag` 均通过 `account_id` 关联到账号
- `MpServiceFactory` 根据 `app_id` 创建和缓存 `WxMpService` 实例

## 设计要点

- 账号使用 `TenantBaseDO` 支持多租户数据隔离
- AppId 作为唯一索引，保证同一租户下不重复
- 账号配置变更后需刷新 `MpServiceFactory` 中的缓存实例
