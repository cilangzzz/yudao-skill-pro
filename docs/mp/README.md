# 微信公众号模块 (yudao-module-mp)

> 模块路径：`yudao-module-mp` | 错误码前缀：`1-006-XXX-XXX`

## 模块概述

微信公众号管理模块，提供完整的公众号运营能力。支持多公众号账号管理、粉丝管理、消息管理、素材管理、菜单管理、自动回复、模板消息推送及数据统计等功能，是企业与微信用户交互的关键渠道。

## 核心功能

| 功能域 | 说明 | 核心类 | 详细文档 |
|--------|------|--------|----------|
| 账号管理 | 多公众号账号接入、配置、缓存 | `MpAccountService` | [api-account.md](api-account.md) |
| 粉丝管理 | 粉丝同步、标签分组、用户画像 | `MpUserService` | [api-user.md](api-user.md) |
| 消息管理 | 消息接收、客服消息、消息记录 | `MpMessageService` | [api-message.md](api-message.md) |
| 模板消息 | 模板同步、模板消息发送 | `MpMessageTemplateService` | [api-message.md](api-message.md) |
| 素材管理 | 临时/永久素材上传、下载、管理 | `MpMaterialService` | [api-material.md](api-material.md) |
| 菜单管理 | 自定义菜单创建、同步、响应 | `MpMenuService` | [api-menu.md](api-menu.md) |
| 自动回复 | 关注回复、关键词回复、消息回复 | `MpAutoReplyService` | [api-auto-reply.md](api-auto-reply.md) |
| 标签管理 | 粉丝标签创建、同步、分组 | `MpTagService` | [api-tag.md](api-tag.md) |
| 数据统计 | 用户分析、消息分析 | `MpStatisticsService` | [api-statistics.md](api-statistics.md) |
| 草稿管理 | 草稿创建与管理 | `MpDraftController` | [api-draft.md](api-draft.md) |
| 发布能力 | 内容发布管理 | `MpFreePublishController` | [api-publish.md](api-publish.md) |

## API 索引

### 管理后台接口

| Controller | 路径前缀 | 说明 |
|-----------|----------|------|
| `MpAccountController` | `/mp/account` | 公众号账号管理 |
| `MpUserController` | `/mp/user` | 粉丝管理 |
| `MpMessageController` | `/mp/message` | 消息管理 |
| `MpMessageTemplateController` | `/mp/message-template` | 模板消息管理 |
| `MpAutoReplyController` | `/mp/auto-reply` | 自动回复管理 |
| `MpMaterialController` | `/mp/material` | 素材管理 |
| `MpMenuController` | `/mp/menu` | 菜单管理 |
| `MpTagController` | `/mp/tag` | 标签管理 |
| `MpStatisticsController` | `/mp/statistics` | 数据统计 |
| `MpDraftController` | `/mp/draft` | 草稿管理 |
| `MpFreePublishController` | `/mp/free-publish` | 发布管理 |

### 微信回调接口

| Controller | 路径 | 说明 |
|-----------|------|------|
| `MpOpenController` | `/mp/open` | 微信回调入口（签名校验、消息处理） |

## 数据模型

详见 [data-model.md](data-model.md)。

**核心数据表：**

- `mp_account` - 公众号账号表（聚合根）
- `mp_user` - 公众号粉丝表（聚合根）
- `mp_message` - 公众号消息表（聚合根）
- `mp_material` - 公众号素材表（聚合根）
- `mp_menu` - 公众号菜单表
- `mp_auto_reply` - 公众号自动回复表
- `mp_message_template` - 公众号模板消息表
- `mp_tag` - 公众号标签表

## 设计模式

| 模式 | 位置 | 用途 |
|------|------|------|
| Factory Pattern | `MpServiceFactory` / `DefaultMpServiceFactory` | 管理多公众号 WxMpService 实例 |
| Chain of Responsibility | `DefaultMpServiceFactory.buildMpMessageRouter()` | WxMpMessageRouter 消息处理链 |
| Strategy Pattern | `service/handler/*` | 不同消息/事件由不同 Handler 处理 |
| Template Method | `MpOpenController.handleMessage()` | 统一回调流程：签名校验 -> 消息解析 -> 路由 -> 响应 |
| Convert Pattern | `convert/*` | MapStruct VO/DO/微信对象转换 |

## 架构分层

```
controller/         -> HTTP 接口层（管理后台 + 微信回调）
service/            -> 业务逻辑层
  handler/          -> 微信消息事件处理器
dal/                -> 数据访问层（MyBatis-Plus Mapper）
framework/mp/       -> 微信公众号框架核心（MpServiceFactory 等）
convert/            -> 对象转换器（MapStruct）
enums/              -> 枚举定义
```

## 依赖关系

### 内部依赖

| 模块 | 用途 |
|------|------|
| `yudao-module-system` | 用户体系、权限验证 |
| `yudao-module-infra` | 文件服务存储素材 |

### 外部依赖

| 依赖 | 用途 |
|------|------|
| `wx-java-mp-spring-boot-starter` | 微信公众号 Java SDK |
| `yudao-spring-boot-starter-mybatis` | MyBatis-Plus 封装 |
| `yudao-spring-boot-starter-redis` | Redis 封装，WxMpService 配置存储 |
| `yudao-spring-boot-starter-biz-tenant` | 多租户支持 |

## 关键文件

| 文件 | 用途 |
|------|------|
| `framework/mp/core/MpServiceFactory.java` | WxMpService 工厂接口 |
| `framework/mp/core/DefaultMpServiceFactory.java` | 默认工厂实现，构建 WxMpService 和 WxMpMessageRouter |
| `controller/admin/open/MpOpenController.java` | 微信回调入口 |
| `service/handler/user/SubscribeHandler.java` | 关注事件处理器 |
| `service/handler/message/MessageAutoReplyHandler.java` | 自动回复处理器 |
| `enums/ErrorCodeConstants.java` | 错误码定义 |

## 扩展指南

### 新增消息类型处理器

1. 在 `service/handler/` 下创建处理器类，实现 `WxMpMessageHandler` 接口
2. 在 `DefaultMpServiceFactory.buildMpMessageRouter()` 中添加路由规则
3. 在 `handle()` 方法中实现业务逻辑

### 新增自动回复类型

1. 在 `MpAutoReplyTypeEnum` 中添加新类型
2. 通过 `MpAutoReplyController` 创建自动回复规则
3. 在 `MpAutoReplyServiceImpl` 中实现回复逻辑

## 最佳实践

- **多账号管理**：使用 `MpServiceFactory.getRequiredMpService(appId)` 获取指定账号服务
- **消息上下文**：使用 `MpContextHolder.getAppId()` 在处理链中传递 appId
- **异步处理**：消息接收使用异步处理，避免阻塞微信回调响应
- **素材下载**：收到媒体消息时自动下载并存储到本地文件服务
- **错误处理**：捕获 `WxErrorException` 并转换为业务异常

## 常见陷阱

详见 [pitfalls.md](pitfalls.md)。
