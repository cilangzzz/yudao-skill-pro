# 微信公众号代码模式与扩展指南 (mp)

> 本文档移植自模块 Skill 知识库（skill-mp.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

管理端 Controller 统一遵循以下注解组合：

- `@Tag(name = "管理后台 - XXX")`：Swagger v3 接口分组
- `@RestController`
- `@RequestMapping("/mp/xxx")`
- `@Validated`
- `@PreAuthorize("@ss.hasPermission('mp:xxx:action')")`：权限校验

示例（MpMessageTemplateController）：

```java
@Tag(name = "管理后台 - 公众号模版消息")
@RestController
@RequestMapping("/mp/message-template")
@Validated
public class MpMessageTemplateController {
    @Resource
    private MpMessageTemplateService messageTemplateService;

    @PostMapping("/send")
    @Operation(summary = "给粉丝发送模版消息")
    @PreAuthorize("@ss.hasPermission('mp:message-template:send')")
    public CommonResult<Boolean> sendMessageTemplate(@Valid @RequestBody MpMessageTemplateSendReqVO sendReqVO) {
        messageTemplateService.sendMessageTempalte(sendReqVO);
        return success(true);
    }
}
```

### Service 层规范

- **接口**：定义业务方法，参数使用 VO 或 BO 对象。
- **实现**：实现类注入 `MpServiceFactory` 获取 `WxMpService`，处理微信 API 调用。

示例（MpMessageTemplateServiceImpl）：

```java
@Service
@Validated
@Slf4j
public class MpMessageTemplateServiceImpl implements MpMessageTemplateService {

    @Resource
    @Lazy // 延迟加载，解决循环依赖
    private MpServiceFactory mpServiceFactory;

    @Override
    public void sendMessageTempalte(MpMessageTemplateSendReqVO sendReqVO) {
        // 1. 获得关联信息
        MpUserDO user = mpUserService.getRequiredUser(sendReqVO.getUserId());
        MpMessageTemplateDO template = validateMsgTemplateExists(sendReqVO.getId());

        // 2. 构建模板消息并发送
        WxMpTemplateMessage templateMessage = buildTemplateMessage(template, user, sendReqVO);
        try {
            mpServiceFactory.getRequiredMpService(template.getAppId())
                    .getTemplateMsgService().sendTemplateMsg(templateMessage);
        } catch (WxErrorException e) {
            throw exception(MESSAGE_TEMPLATE_SEND_FAIL, e.getError().getErrorMsg());
        }
    }
}
```

### 消息处理器规范（Handler）

实现 `WxMpMessageHandler` 接口，通过 `@Component` 注册为 Spring Bean。

示例（SubscribeHandler）：

```java
@Component
@Slf4j
public class SubscribeHandler implements WxMpMessageHandler {

    @Resource
    private MpUserService mpUserService;
    @Resource
    private MpAutoReplyService mpAutoReplyService;

    @Override
    public WxMpXmlOutMessage handle(WxMpXmlMessage wxMessage, Map<String, Object> context,
                                    WxMpService weixinService, WxSessionManager sessionManager) {
        // 1. 获取粉丝信息
        WxMpUser wxMpUser = weixinService.getUserService().userInfo(wxMessage.getFromUser());

        // 2. 保存粉丝信息
        mpUserService.saveUser(MpContextHolder.getAppId(), wxMpUser);

        // 3. 回复关注欢迎语
        return mpAutoReplyService.replyForSubscribe(MpContextHolder.getAppId(), wxMessage);
    }
}
```

### 数据访问规范（DAL）

Mapper 继承 `BaseMapperX`，使用 `LambdaQueryWrapperX` 构建查询条件。

示例（MpMessageMapper）：

```java
@Mapper
public interface MpMessageMapper extends BaseMapperX<MpMessageDO> {

    default PageResult<MpMessageDO> selectPage(MpMessagePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<MpMessageDO>()
                .eqIfPresent(MpMessageDO::getAccountId, reqVO.getAccountId())
                .eqIfPresent(MpMessageDO::getUserId, reqVO.getUserId())
                .orderByDesc(MpMessageDO::getId));
    }
}
```

### 异常处理

mp 模块错误码前缀为 `1-006-XXX-XXX`，典型错误码：

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_003_000 | 粉丝不存在 |
| 1_006_005_000 | 发送消息失败，原因：{} |
| 1_006_009_000 | 自动回复不存在 |
| 1_006_010_004 | 发送模版消息失败，原因：{} |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE, args...)`

## 扩展指南

### 新增消息类型处理器

1. **创建 Handler 类**：在 `service/handler/` 目录下创建新的处理器类，实现 `WxMpMessageHandler` 接口。
2. **注册到消息路由**：在 `DefaultMpServiceFactory.buildMpMessageRouter()` 中添加路由规则。

```java
// 示例：添加新消息类型处理
router.rule().async(false)
        .msgType(WxConsts.XmlMsgType.XXX)
        .handler(newHandler).end();
```

3. **实现业务逻辑**：在 `handle()` 方法中实现消息处理逻辑，返回 `WxMpXmlOutMessage` 响应。

### 新增自动回复类型

1. **扩展枚举**：在 `MpAutoReplyTypeEnum` 中添加新的类型。
2. **创建自动回复配置**：通过 `MpAutoReplyController` 创建自动回复规则。
3. **实现回复逻辑**：在 `MpAutoReplyServiceImpl` 中实现对应的回复逻辑。

### 最佳实践

| 实践 | 说明 | 示例 |
|-----|------|------|
| 多账号管理 | 使用 `MpServiceFactory` 获取指定账号的 `WxMpService`，避免账号混淆 | `WxMpService mpService = mpServiceFactory.getRequiredMpService(accountId);` |
| 消息上下文 | 使用 `MpContextHolder` 在处理链中传递 appId 上下文 | `String appId = MpContextHolder.getAppId();` |
| 异步处理 | 消息接收使用异步处理，避免阻塞微信回调响应 | `router.rule().handler(messageReceiveHandler).next(); // next() 表示继续执行后续规则` |
| 素材下载 | 收到粉丝发送的媒体消息时，自动下载并存储到本地文件服务 | `mpMaterialService.downloadMaterialUrl(accountId, mediaId, type);` |
| 错误处理 | 捕获 `WxErrorException` 并转换为业务异常 | 见下方代码 |

```java
try {
    wxMpService.someOperation();
} catch (WxErrorException e) {
    throw exception(ERROR_CODE, e.getError().getErrorMsg());
}
```

## 模块依赖

### 内部依赖（其他业务模块）

| 模块 | 用途 |
|-----|------|
| yudao-module-system | 依赖用户体系、权限验证 |
| yudao-module-infra | 依赖文件服务存储素材（FileApi 上传素材文件） |

### 外部依赖（第三方库 / framework starter）

| 依赖 | 版本 | 用途 |
|-----|------|------|
| wx-java-mp-spring-boot-starter | 继承自父 POM | 微信公众号 Java SDK，提供 WxMpService 等核心 API |
| yudao-spring-boot-starter-mybatis | 继承自父 POM | MyBatis-Plus 封装，提供 BaseMapperX 等 |
| yudao-spring-boot-starter-redis | 继承自父 POM | Redis 封装，用于 WxMpService 配置存储（access token） |
| yudao-spring-boot-starter-biz-tenant | 继承自父 POM | 多租户支持 |

> 注意：本模块未使用消息队列，模块间通信不涉及 MQ。

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/framework/mp/core/MpServiceFactory.java | WxMpService 工厂接口，管理多公众号实例 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/framework/mp/core/DefaultMpServiceFactory.java | 默认工厂实现，构建 WxMpService 和 WxMpMessageRouter |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/controller/admin/open/MpOpenController.java | 微信回调入口，处理签名校验和消息路由 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/service/handler/user/SubscribeHandler.java | 关注事件处理器，保存粉丝信息并回复欢迎语 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/service/handler/message/MessageAutoReplyHandler.java | 自动回复处理器，处理关键词和消息类型回复 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/service/message/MpMessageServiceImpl.java | 消息服务实现，处理消息接收和发送 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/service/message/MpMessageTemplateServiceImpl.java | 模板消息服务实现，同步和发送模板消息 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/dal/dataobject/account/MpAccountDO.java | 公众号账号实体，支持多租户 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/dal/dataobject/message/MpMessageDO.java | 消息实体，包含多种消息类型字段 |
| yudao-module-mp/src/main/java/cn/iocoder/yudao/module/mp/enums/ErrorCodeConstants.java | 错误码定义 |

## 领域模型

### 聚合根

| 聚合根 | 说明 | 关联实体 |
|-------|------|---------|
| MpAccount | 公众号账号聚合根，管理公众号配置信息 | MpMenu、MpTag、MpStatistics |
| MpUser | 公众号粉丝聚合根，关联粉丝标签和消息记录 | MpTag |
| MpMessage | 消息聚合根，包含自动回复配置和消息模板 | MpAutoReply、MpMessageTemplate |
| MpMaterial | 素材聚合根，管理临时素材和永久素材 | - |

### 值对象

| 值对象 | 说明 |
|-------|------|
| MpMessageDO.Article | 图文消息值对象，包含标题、描述、图片链接、跳转链接 |
| MpAutoReplyTypeEnum | 自动回复类型枚举：关注回复、消息回复、关键词回复 |
| MpAutoReplyMatchEnum | 关键词匹配模式枚举：完全匹配、半匹配 |
| MpMessageSendFromEnum | 消息发送方向枚举：粉丝发给公众号、公众号发给粉丝 |

## 设计与架构补充

以下为 README 及各 api 文档未覆盖部分的补充。

### 分层架构

| 层 | 职责 | 核心组件 |
|---|------|---------|
| controller | HTTP 接口层，提供管理后台和微信回调接口 | MpAccountController、MpUserController、MpMessageController、MpMessageTemplateController、MpAutoReplyController、MpMaterialController、MpMenuController、MpTagController、MpOpenController（微信回调入口：签名校验、消息处理）、MpStatisticsController、MpDraftController、MpFreePublishController |
| service | 业务逻辑层 | MpAccountService、MpUserService、MpMessageService、MpMaterialService、MpMenuService、MpAutoReplyService、MpMessageTemplateService、MpTagService、MpStatisticsService |
| handler | 微信消息事件处理器 | SubscribeHandler（关注）、UnsubscribeHandler（取消关注）、MenuHandler（菜单点击）、MessageReceiveHandler（消息接收）、MessageAutoReplyHandler（自动回复）、LocationHandler（地理位置）、ScanHandler（扫码）、KfSessionHandler（客服会话） |
| dal | 数据访问层 | MpAccountMapper、MpUserMapper、MpMessageMapper、MpMaterialMapper、MpMenuMapper、MpAutoReplyMapper、MpMessageTemplateMapper、MpTagMapper |
| framework/mp | 微信公众号框架核心 | MpServiceFactory（WxMpService 工厂接口）、DefaultMpServiceFactory（默认工厂实现，管理多账号 WxMpService）、MpContextHolder（公众号上下文持有者） |

### 设计模式补充

除 README「设计模式」章节列出的工厂模式、策略模式 + 责任链路由、ThreadLocal 上下文、本地缓存刷新外，本模块还应用了以下模式：

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 转换器模式（Convert） | convert/* | MapStruct 转换器，VO / DO / 微信 SDK 对象之间转换 |
| 模板方法 | MpOpenController.handleMessage() | 统一的微信回调处理流程：签名校验 → 消息解析 → 路由处理 → 响应构建 |

### 设计原则补充

- **素材统一管理**：临时素材和永久素材统一抽象，收到粉丝发送的媒体消息时自动下载并存储到本地文件服务（内部方法 `downloadMaterialUrl`，详见 [api-material.md](api-material.md) 附注）。

### 数据模型补充

README「数据模型」章节给出各表概要，此处补充完整字段、索引与表间关系。

#### mp_account 公众号账号表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
| name | String | 公众号名称 |
| account | String | 公众号账号 |
| app_id | String | 公众号 AppId |
| app_secret | String | 公众号密钥 |
| token | String | 公众号 Token |
| aes_key | String | 消息加解密密钥 |
| qr_code_url | String | 二维码图片 URL |
| remark | String | 备注 |

索引：`uk_app_id`（app_id 唯一索引，保证 appId 全局不重复，否则微信回调无法识别归属账号）。

#### mp_user 公众号粉丝表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
| openid | String | 粉丝标识 OpenId |
| union_id | String | 微信生态唯一标识 |
| subscribe_status | Integer | 关注状态（1 已关注 / 2 取消关注） |
| subscribe_time | LocalDateTime | 关注时间 |
| unsubscribe_time | LocalDateTime | 取消关注时间 |
| nickname | String | 昵称 |
| head_image_url | String | 头像地址 |
| language | String | 语言 |
| country | String | 国家 |
| province | String | 省份 |
| city | String | 城市 |
| remark | String | 备注 |
| tag_ids | List&lt;Long&gt; | 标签 ID 数组 |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId（冗余） |

索引：`idx_account_id`（account_id）；`uk_appid_openid`（app_id + openid 联合唯一索引，保证同一公众号下粉丝不重复）。

#### mp_message 公众号消息表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
| msg_id | Long | 微信消息 ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| user_id | Long | 粉丝编号 |
| openid | String | 粉丝 OpenId |
| type | String | 消息类型（text/image/voice/video 等） |
| send_from | Integer | 消息来源（1 粉丝发给公众号 / 2 公众号发给粉丝） |
| content | String | 文本消息内容 |
| media_id | String | 媒体文件 ID |
| media_url | String | 媒体文件 URL |
| recognition | String | 语音识别文本 |
| format | String | 语音格式 |
| title | String | 标题 |
| description | String | 描述 |
| thumb_media_id | String | 缩略图媒体 ID |
| thumb_media_url | String | 缩略图 URL |
| url | String | 链接地址 |
| location_x | Double | 地理位置纬度 |
| location_y | Double | 地理位置经度 |
| scale | Double | 地图缩放级别 |
| label | String | 地理位置信息 |
| articles | List&lt;Article&gt; | 图文消息数组（JSON） |
| music_url | String | 音乐链接 |
| hq_music_url | String | 高质量音乐链接 |
| event | String | 事件类型 |
| event_key | String | 事件 Key 值 |

索引：`idx_account_id`（account_id）；`idx_user_id`（user_id）。

#### mp_material 公众号素材表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
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

索引：`idx_account_id`（account_id）；`idx_media_id`（media_id）。

#### mp_menu 公众号菜单表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
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
| reply_articles | List&lt;Article&gt; | 回复图文消息（JSON） |

索引：`idx_account_id`（account_id）。

#### mp_auto_reply 公众号自动回复表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| type | Integer | 回复类型（1 关注回复 / 2 消息回复 / 3 关键词回复） |
| request_keyword | String | 请求关键词 |
| request_match | Integer | 关键词匹配模式（1 完全匹配 / 2 半匹配） |
| request_message_type | String | 请求消息类型 |
| response_message_type | String | 响应消息类型 |
| response_content | String | 响应文本内容 |
| response_media_id | String | 响应媒体 ID |
| response_media_url | String | 响应媒体 URL |
| response_articles | List&lt;Article&gt; | 响应图文消息（JSON） |

索引：`idx_account_id`（account_id）。

#### mp_message_template 公众号模板消息表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |
| template_id | String | 模板 ID |
| title | String | 模板标题 |
| content | String | 模板内容 |
| example | String | 模板示例 |
| primary_industry | String | 一级行业 |
| deputy_industry | String | 二级行业 |

索引：`idx_account_id`（account_id）；`idx_template_id`（template_id）。

#### mp_tag 公众号标签表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 ID |
| tag_id | Long | 微信标签 ID |
| name | String | 标签名称 |
| count | Integer | 标签下粉丝数 |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId |

索引：`idx_account_id`（account_id）。

#### 表间关系

| 表 | 关联表 | 关系 | 外键 |
|---|-------|------|------|
| mp_user | mp_account | N:1 | account_id |
| mp_message | mp_account | N:1 | account_id |
| mp_message | mp_user | N:1 | user_id |
| mp_material | mp_account | N:1 | account_id |
| mp_menu | mp_account | N:1 | account_id |
| mp_auto_reply | mp_account | N:1 | account_id |
| mp_message_template | mp_account | N:1 | account_id |
| mp_tag | mp_account | N:1 | account_id |

除 mp_message 额外通过 user_id 关联 mp_user 外，其余业务表均通过 account_id 以 N:1 关联 mp_account。
