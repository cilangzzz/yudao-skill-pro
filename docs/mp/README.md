# 微信公众号模块 (mp)

> 基于.weixin-java-mp SDK 封装的微信公众号管理模块，提供多公众号账号、菜单、粉丝、标签、消息、自动回复、素材、草稿与发布、模板消息、数据统计等一站式运营能力。

## 模块概述

- **模块路径**: `yudao-module-mp`（单模块布局，非多子模块）
- **业务定位**: 管理企业在微信公众平台的一个或多个公众号。通过 `MpServiceFactory` 按 appId 维护 `WxMpService` 实例与消息路由，管理员在后台即可完成账号接入、菜单配置、粉丝管理、素材上传、图文草稿编辑与发布、客服消息与模板消息发送、运营数据查看；同时对外暴露 `/mp/open/{appId}` 回调端点接收微信服务器推送。
- **技术栈**: Spring Boot 2.7.18 / MyBatis-Plus / Swagger v3 (springdoc) / weixin-java-mp 4.8.x（wx-java-mp-spring-boot-starter）/ Redis（access token 存储、本地缓存刷新）/ 多租户 (biz-tenant)

## 设计原则

| 原则 | 说明 |
|-----|------|
| 多账号工厂管理 | `MpServiceFactory` 按 appId / 账号 id 维护 `WxMpService` 与 `WxMpMessageRouter` 映射，账号增删改后整体重建缓存，Controller 均通过工厂获取对应账号的 SDK 服务 |
| 本地缓存 + 定时刷新 | `MpAccountServiceImpl` 通过 `@PostConstruct` 加载账号缓存、`@Scheduled` 每 60 秒检测更新并联动刷新 `MpServiceFactory`，回调场景零 DB 查询 |
| 消息路由策略化 | 微信回调消息经 `WxMpMessageRouter` 规则路由到 10 个 `WxMpMessageHandler` 策略实现（关注/取关/菜单点击/扫码/位置/客服会话等） |
| 回调与租户解耦 | `/mp/open` 回调端点标注 `@TenantIgnore`，先经 appId 定位账号，再用 `TenantUtils.execute` + `MpContextHolder`（ThreadLocal）恢复租户上下文 |
| 数据落库 + 冗余字段 | 消息、粉丝、素材等均落库留痕；业务表普遍冗余 `appId` 字段，便于按账号直查 |
| 管理端与回调端分离 | `controller/admin` 供后台运营（权限控制），`MpOpenController` 供微信服务器回调（签名校验，免登录） |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 公众号账号 | 账号 CRUD、生成带参二维码、清空 API 配额、精简列表（前端切换账号用） | MpAccountDO |
| 公众号菜单 | 按账号保存/删除/查询自定义菜单，支持点击推事件、跳转链接、小程序、回复消息等多种按钮类型 | MpMenuDO |
| 公众号粉丝 | 粉丝分页/详情/备注修改，从微信同步粉丝与标签数据 | MpUserDO |
| 公众号标签 | 标签 CRUD、同步微信标签及粉丝计数 | MpTagDO |
| 消息与客服 | 接收并落库微信推送消息，客服消息发送，消息分页查询 | MpMessageDO |
| 自动回复 | 关注回复/消息回复/关键字回复三类规则的 CRUD | MpAutoReplyDO |
| 素材管理 | 临时/永久素材上传、图文内图片上传、素材删除与分页 | MpMaterialDO |
| 图文草稿 | 微信草稿箱的分页、创建、更新、删除（数据实时读微信，不落库） | 无本地实体（WxMpDraftItem） |
| 发布能力 | 已发布图文的分页查询、草稿发布、发布记录删除 | 无本地实体（WxMpFreePublishItem） |
| 模板消息 | 模板同步（从微信拉取）、删除、按粉丝发送模板消息 | MpMessageTemplateDO |
| 数据统计 | 粉丝增减/累计、消息发送概况、接口分析四类数据报表 | 无本地实体（WxDataCube*） |
| 微信回调 | `GET /mp/open/{appId}` 验证服务器签名；`POST /mp/open/{appId}` 接收明文/AES 加密消息并路由处理 | MpAccountDO（缓存） |

## API 接口索引

### 公众号账号 (MpAccountController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/account/create | POST | 创建公众号账号 | mp:account:create |
| /mp/account/update | PUT | 更新公众号账号 | mp:account:update |
| /mp/account/delete | DELETE | 删除公众号账号 | mp:account:delete |
| /mp/account/get | GET | 获得公众号账号 | mp:account:query |
| /mp/account/page | GET | 获得公众号账号分页 | mp:account:query |
| /mp/account/list-all-simple | GET | 获取公众号账号精简信息列表 | mp:account:query |
| /mp/account/generate-qr-code | PUT | 生成公众号二维码 | mp:account:qr-code |
| /mp/account/clear-quota | PUT | 清空公众号 API 配额 | mp:account:clear-quota |

### 公众号菜单 (MpMenuController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/menu/save | POST | 保存公众号菜单 | mp:menu:save |
| /mp/menu/delete | DELETE | 删除公众号菜单 | mp:menu:delete |
| /mp/menu/list | GET | 获得公众号菜单列表 | mp:menu:query |

### 公众号粉丝 (MpUserController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/user/page | GET | 获得公众号粉丝分页 | mp:user:query |
| /mp/user/get | GET | 获得公众号粉丝 | mp:user:query |
| /mp/user/update | PUT | 更新公众号粉丝 | mp:user:update |
| /mp/user/sync | POST | 同步公众号粉丝 | mp:user:sync |

### 公众号标签 (MpTagController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/tag/create | POST | 创建公众号标签 | mp:tag:create |
| /mp/tag/update | PUT | 更新公众号标签 | mp:tag:update |
| /mp/tag/delete | DELETE | 删除公众号标签 | mp:tag:delete |
| /mp/tag/get | GET | 获取公众号标签详情 | mp:tag:query |
| /mp/tag/page | GET | 获取公众号标签分页 | mp:tag:query |
| /mp/tag/list-all-simple | GET | 获取公众号标签精简信息列表 | mp:account:query（源码如此，疑似应为 mp:tag:query） |
| /mp/tag/sync | POST | 同步公众号标签 | mp:tag:sync |

### 消息与客服 (MpMessageController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/message/page | GET | 获得公众号消息分页 | mp:message:query |
| /mp/message/send | POST | 给粉丝发送（客服）消息 | mp:message:send |

### 自动回复 (MpAutoReplyController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/auto-reply/page | GET | 获得公众号自动回复分页 | mp:auto-reply:query |
| /mp/auto-reply/get | GET | 获得公众号自动回复 | mp:auto-reply:query |
| /mp/auto-reply/create | POST | 创建公众号自动回复 | mp:auto-reply:create |
| /mp/auto-reply/update | PUT | 更新公众号自动回复 | mp:auto-reply:update |
| /mp/auto-reply/delete | DELETE | 删除公众号自动回复 | mp:auto-reply:delete |

### 模板消息 (MpMessageTemplateController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/message-template/delete | DELETE | 删除模版消息 | mp:message-template:delete |
| /mp/message-template/get | GET | 获得模版消息 | mp:message-template:query |
| /mp/message-template/list | GET | 获得模版消息列表 | mp:message-template:query |
| /mp/message-template/sync | POST | 同步公众号模板 | mp:message-template:sync |
| /mp/message-template/send | POST | 给粉丝发送模版消息 | mp:message-template:send |

### 素材管理 (MpMaterialController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/material/upload-temporary | POST | 上传临时素材 | mp:material:upload-temporary |
| /mp/material/upload-permanent | POST | 上传永久素材 | mp:material:upload-permanent |
| /mp/material/delete-permanent | DELETE | 删除素材 | mp:material:delete |
| /mp/material/upload-news-image | POST | 上传图文内容中的图片 | mp:material:upload-news-image |
| /mp/material/page | GET | 获得素材分页 | mp:material:query |

### 图文草稿 (MpDraftController)

草稿数据实时读自微信草稿箱，不落本地库；返回 SDK 原生 `WxMpDraftItem` 结构。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/draft/page | GET | 获得草稿分页 | mp:draft:query |
| /mp/draft/create | POST | 创建草稿 | mp:draft:create |
| /mp/draft/update | PUT | 更新草稿 | mp:draft:update |
| /mp/draft/delete | DELETE | 删除草稿 | mp:draft:delete |

### 发布能力 (MpFreePublishController)

已发布图文数据实时读自微信，不落本地库；返回 SDK 原生 `WxMpFreePublishItem` 结构。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/free-publish/page | GET | 获得已发布的图文分页 | mp:free-publish:query |
| /mp/free-publish/submit | POST | 发布草稿 | mp:free-publish:submit |
| /mp/free-publish/delete | DELETE | 删除发布记录 | mp:free-publish:delete |

### 微信回调 (MpOpenController)

微信服务器直连回调端点，无登录态，通过微信签名校验鉴权；响应为 XML 明文（`@TenantIgnore` 免租户解析）。

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/open/{appId} | GET | 校验签名（接入验证，回显 echostr） | 免登录（微信签名校验） |
| /mp/open/{appId} | POST | 处理消息（接收微信推送，明文/AES 加密两种模式） | 免登录（微信签名校验） |

### 数据统计 (MpStatisticsController)

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /mp/statistics/user-summary | GET | 获得粉丝增减数据 | mp:statistics:query |
| /mp/statistics/user-cumulate | GET | 获得粉丝累计数据 | mp:statistics:query |
| /mp/statistics/upstream-message | GET | 获取消息发送概况数据 | mp:statistics:query |
| /mp/statistics/interface-summary | GET | 获取接口分析数据 | mp:statistics:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|---------|---------|
| mp_account | 公众号账号 | TenantBaseDO | appId、appSecret、token、aesKey、qrCodeUrl、name、account |
| mp_menu | 公众号菜单 | BaseDO | accountId、appId、menuKey、parentId、type、url、replyMessageType、replyArticles(JSON) |
| mp_user | 公众号粉丝 | BaseDO | openid、unionId、subscribeStatus、subscribeTime、nickname、tagIds(List)、accountId |
| mp_tag | 公众号标签 | BaseDO | tagId、name、count(粉丝数冗余)、accountId、appId（id 为 INPUT 主键，存微信 tagId） |
| mp_message | 公众号消息 | BaseDO | msgId、openid、userId、type、sendFrom、content、mediaId、event、eventKey、articles(JSON) |
| mp_auto_reply | 公众号自动回复 | BaseDO | accountId、type、requestKeyword、requestMatch、requestMessageType、responseMessageType、responseArticles(JSON) |
| mp_message_template | 公众号模板消息 | BaseDO | templateId、title、content、example、primaryIndustry、deputyIndustry |
| mp_material | 公众号素材 | BaseDO | mediaId、type、permanent、url、mpUrl、name、title、introduction、accountId |

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 工厂模式 | `framework/mp/core/MpServiceFactory` + `DefaultMpServiceFactory` | 按公众号 appId（或账号 id）创建并缓存 `WxMpService` / `WxMpMessageRouter`，多账号隔离 SDK 实例（access token 存 Redis） |
| 策略模式 + 责任链路由 | `service/handler/**` 下 10 个 `WxMpMessageHandler` 实现（MessageReceiveHandler、MessageAutoReplyHandler、MenuHandler、SubscribeHandler、UnsubscribeHandler、LocationHandler、ScanHandler、KfSessionHandler、StoreCheckNotifyHandler、NullHandler），由 `WxMpMessageRouter` 按消息类型/事件规则分发 | 微信回调消息的差异化处理：关注/取关更新粉丝、菜单点击回复、扫码记录、自动回复兜底等 |
| ThreadLocal 上下文 | `framework/mp/core/context/MpContextHolder` | Handler 层无法直接拿到 appId 参数，通过上下文透传当前请求所属公众号 |
| 本地缓存刷新 | `MpAccountServiceImpl#initLocalCache` + `@Scheduled` 定时比对 updateTime | 账号列表内存缓存，变更后联动 `MpServiceFactory.init()` 重建 SDK 实例 |

## 依赖关系

- **上游**（本模块依赖）:
  - 业务模块: `yudao-module-system`（POM 依赖）、`yudao-module-infra`（`FileApi` 上传素材到文件服务）
  - framework starter: `yudao-spring-boot-starter-biz-tenant`、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-redis`、`yudao-spring-boot-starter-mq`、`yudao-spring-boot-starter-excel`
  - 三方 SDK: `wx-java-mp-spring-boot-starter`（weixin-java-mp 4.8.x，微信公众号开发 SDK）
- **下游**（依赖本模块）: 无其他业务模块依赖 mp，仅 `yudao-server` 启动器聚合引入

## 对外暴露的 API

无（`cn.iocoder.yudao.module.mp.api` 包不存在，本模块不提供跨模块 Api 接口；能力均通过 admin Controller 与微信回调端点对外）。

## 详细文档

- [api-account.md](api-account.md) - 公众号账号
- [api-material.md](api-material.md) - 素材管理
- [api-menu.md](api-menu.md) - 公众号菜单
- [api-message.md](api-message.md) - 消息、自动回复与模板消息
- [api-news.md](api-news.md) - 图文草稿与发布
- [api-open.md](api-open.md) - 微信回调
- [api-statistics.md](api-statistics.md) - 数据统计
- [api-tag.md](api-tag.md) - 公众号标签
- [api-user.md](api-user.md) - 公众号粉丝
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
