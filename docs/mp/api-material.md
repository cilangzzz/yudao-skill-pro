# 素材管理 API

> 对应 Controller：`MpMaterialController` | 路径前缀：`/mp/material`

## 功能说明

管理公众号素材，支持临时素材和永久素材的上传、下载、删除。素材文件自动下载并存储到本地文件服务。

## 数据模型

### MpMaterialDO

继承 `BaseDO`。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| media_id | String | 微信素材 ID |
| type | String | 文件类型（image/voice/video/thumb） |
| permanent | Boolean | 是否永久素材 |
| url | String | 文件服务器 URL |
| name | String | 文件名称 |
| mp_url | String | 公众号文件 URL（永久素材） |
| title | String | 视频素材标题 |
| introduction | String | 视频素材描述 |

### 索引

- `idx_account_id` - 账号 ID 索引
- `idx_media_id` - 媒体 ID 索引

## 核心服务

### MpMaterialService

| 方法 | 说明 |
|------|------|
| 上传临时素材 | 上传临时素材到微信，有效期 3 天 |
| 上传永久素材 | 上传永久素材到微信 |
| 下载素材 | 从微信下载素材并存储到本地文件服务 |
| 删除素材 | 删除微信素材 |
| 分页查询 | 查询素材列表 |

## 素材处理流程

### 上传流程

1. 接收文件上传请求
2. 调用微信 API 上传素材
3. 保存素材记录到数据库

### 下载流程（消息中的媒体文件）

1. 收到粉丝发送的媒体消息
2. 调用微信 API 下载媒体文件
3. 存储到本地文件服务（yudao-module-infra）
4. 保存素材记录

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- 依赖 `yudao-module-infra` 的文件服务存储素材文件
- `mp_message` 中的 `media_id` 关联素材

## 设计要点

- 临时素材有效期 3 天，永久素材长期有效
- 素材文件自动下载到本地，避免依赖微信 CDN
- `media_id` 作为微信侧唯一标识，`url` 作为本地文件服务地址
- 支持 image、voice、video、thumb 四种素材类型
