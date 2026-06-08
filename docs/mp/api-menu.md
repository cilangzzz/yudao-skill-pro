# 菜单管理 API

> 对应 Controller：`MpMenuController` | 路径前缀：`/mp/menu`

## 功能说明

管理公众号自定义菜单，支持多级菜单、菜单点击事件响应。菜单类型包括 click（推事件）、view（跳转 URL）、miniprogram（小程序）等。

## 数据模型

### MpMenuDO

继承 `BaseDO`。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| name | String | 菜单名称 |
| menu_key | String | 菜单标识 |
| parent_id | Long | 父菜单 ID |
| type | String | 按钮类型（click/view/miniprogram 等） |
| url | String | 网页链接 |
| mini_program_app_id | String | 小程序 AppId |
| mini_program_page_path | String | 小程序页面路径 |
| article_id | String | 跳转图文媒体 ID |
| reply_message_type | String | 回复消息类型 |
| reply_content | String | 回复文本内容 |
| reply_media_id | String | 回复媒体 ID |
| reply_media_url | String | 回复媒体 URL |
| reply_articles | List\<Article\> | 回复图文消息（JSON） |

## 核心服务

### MpMenuService

| 方法 | 说明 |
|------|------|
| 创建菜单 | 创建菜单项 |
| 更新菜单 | 修改菜单项 |
| 删除菜单 | 删除菜单项 |
| 同步到微信 | 将本地菜单同步到微信服务器 |
| 获取菜单 | 查询菜单树结构 |

## 菜单类型

| 类型 | 说明 |
|------|------|
| click | 推事件，用户点击后微信推送事件到回调 URL |
| view | 跳转 URL，用户点击后跳转到指定网页 |
| miniprogram | 小程序，用户点击后跳转到小程序页面 |
| article_id | 跳转图文消息 |

## 事件处理

### MenuHandler（菜单点击事件）

1. 接收微信推送的菜单点击事件
2. 根据 `menu_key` 查找菜单配置
3. 执行对应的回复逻辑（文本/图文/媒体）

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- 菜单点击事件通过 `MenuHandler` 处理
- `article_id` 关联图文素材

## 设计要点

- 菜单支持树形结构，通过 `parent_id` 实现多级菜单
- 菜单同步到微信时，将本地树结构转换为微信 API 格式
- 菜单点击事件可配置回复内容（文本/图文/媒体）
