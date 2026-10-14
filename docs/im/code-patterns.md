# IM 即时通讯代码模式与扩展指南 (im)

> 本文档移植自模块 Skill 知识库（skill-im.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层

用户端与用户端常用注解规范：

- `@Tag(name = "xxx")` - Swagger 文档标签
- `@RestController` - REST 控制器
- `@RequestMapping("/im/xxx")` - 请求路径前缀
- `@Validated` - 参数校验
- `@PreAuthorize("@ss.hasPermission('im:xxx:action')")` - 权限控制（仅管理端 Controller 使用）

示例（用户端好友管理 Controller，通过登录态鉴权，无 RBAC 权限点）：

```java
@Tag(name = "用户端 - 好友管理")
@RestController
@RequestMapping("/im/friend")
@Validated
public class ImFriendController {
    @Resource
    private FriendService friendService;

    @GetMapping("/list")
    @Operation(summary = "获取好友列表")
    public CommonResult<List<FriendDO>> getFriendList() {
        return success(friendService.getFriendList(LoginContextHolder.getLoginUserId()));
    }
}
```

### Service 层

接口与实现约定：`XxxService` 接口定义业务方法，`XxxServiceImpl` 实现类。

实现类骨架约定：

```java
@Service
@Validated
public class XxxServiceImpl implements XxxService {
    @Resource
    private XxxMapper xxxMapper;

    // 使用 static final 定义常量
    // 使用 @Transactional 注解控制事务
    // 使用 validateXxxExists 方法校验存在性
    // 使用 exception(ErrorCode) 抛出业务异常
}
```

示例（私聊消息发送，展示「校验 → 幂等 → 敏感词过滤 → 保存 → 事务提交后异步推送」的完整流程）：

```java
@Service
public class PrivateMessageServiceImpl implements PrivateMessageService {
    @Resource
    private ImPrivateMessageMapper privateMessageMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PrivateMessageDO sendPrivateMessage(PrivateMessageSendReqDTO reqDTO) {
        // 1. 校验接收者存在
        // 2. 检查 clientMessageId 幂等
        // 3. 敏感词过滤
        // 4. 保存消息
        PrivateMessageDO message = ...;
        privateMessageMapper.insert(message);
        // 5. 事务提交后异步推送
        TransactionSynchronizationManager.registerSynchronization(
            new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    // 推送消息给接收者
                }
            });
        return message;
    }
}
```

### DAL 层

Mapper 约定：

```java
public interface XxxMapper extends BaseMapperX<XxxDO> {
    // 继承 BaseMapperX 获得通用 CRUD 方法
    // 自定义查询方法使用 @Select 注解或 XML
    // 分页查询返回 PageResult<XxxDO>
}
```

示例（私聊消息分页查询，使用 `LambdaQueryWrapperX` 的条件判空短路）：

```java
public interface ImPrivateMessageMapper extends BaseMapperX<PrivateMessageDO> {
    default PageResult<PrivateMessageDO> selectPage(PrivateMessagePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<PrivateMessageDO>()
                .eqIfPresent(PrivateMessageDO::getSenderId, reqVO.getSenderId())
                .eqIfPresent(PrivateMessageDO::getReceiverId, reqVO.getReceiverId())
                .betweenIfPresent(PrivateMessageDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(PrivateMessageDO::getId));
    }
}
```

### 异常处理

- 错误码前缀：`1_009_XXX_XXX`
- 典型错误场景包括：好友已存在、不是好友关系、群组不存在、不是群成员、已被禁言、消息已撤回、撤回超时、通话不存在

### 统一响应

- 成功响应：`CommonResult.success(data)`
- 失败响应：`throw exception(ErrorCode)` 抛出业务异常，由全局异常处理器统一封装

## 扩展指南

### 新增消息类型

1. **定义消息类型枚举**：在 `MessageTypeEnum` 中添加新的消息类型编号，保持与 OpenIM 协议兼容。
2. **定义消息内容 DTO**：创建 `XxxContentDTO` 类定义该消息类型的 content JSON 结构。

   ```java
   @Data
   public class VideoContentDTO {
       private String url;
       private Integer duration;
       private Integer width;
       private Integer height;
       private String thumbUrl;
   }
   ```

3. **实现消息渲染**：在客户端实现该消息类型的渲染逻辑。
4. **敏感词处理**：如果消息类型包含文本内容，需要在发送时进行敏感词过滤。

### 新增管理后台接口

1. **创建 Manager Controller**：在 `controller/admin/manager/` 下创建新的 Controller 类。

   ```java
   @Tag(name = "管理后台 - XXX 管理")
   @RestController
   @RequestMapping("/im/manager/xxx")
   @Validated
   @PreAuthorize("@ss.hasPermission('im:xxx:query')")
   public class ImXxxManagerController {
       // 注入 Service
       // 定义 CRUD 接口
   }
   ```

2. **定义权限标识**：在权限系统中注册 `im:xxx:query` / `im:xxx:create` / `im:xxx:update` / `im:xxx:delete` 权限。
3. **实现 Service 方法**：在对应的 Service 中实现管理端的业务逻辑。
4. **添加数据权限**：根据需要添加数据权限控制。

### 最佳实践

| 实践 | 说明 |
|---|---|
| clientMessageId 幂等发送 | 客户端生成 UUID 作为 clientMessageId，服务端通过唯一索引保证幂等，避免网络重试导致重复消息 |
| 事务感知异步推送 | 使用 afterCommit 回调确保事务提交后再推送消息，避免接收方读到未提交数据 |
| Redis 已读游标 | 使用 Redis 存储已读游标，避免频繁更新数据库，提高已读状态查询性能 |
| 双向好友独立属性 | 每对好友的 2 行记录拥有独立属性，更新时只修改当前用户方向的记录 |
| 群组角色权限校验 | 通过 GroupMemberDO.role 字段判断操作权限，注意权限边界（管理员不可踢管理员） |
| LiveKit Webhook 安全 | 使用 JWT + SHA256 签名验证 Webhook 请求，不要在未验证签名的情况下处理事件 |
| 敏感词过滤时机 | 敏感词过滤在消息发送时执行，过滤后直接存储，已发送消息不受后续词库更新影响 |
| 消息增量拉取 | 使用 maxMessageId 作为游标进行增量拉取，避免使用 offset 分页的性能问题 |

## 模块依赖

### 内部依赖（其他模块 / 框架）

| 依赖 | 用途 |
|---|---|
| yudao-module-system | AdminUserApi - 查询用户信息、校验用户存在性 |
| yudao-module-infra | 文件存储（头像、图片、文件消息等） |
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |
| yudao-framework-redis | Redis 操作封装，用于已读游标存储 |
| yudao-framework-tenant | 租户支持 |

### 外部依赖（第三方库 / 服务）

| 依赖 | 用途 |
|---|---|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| sensitive-word | 基于 Trie 树的敏感词过滤库 |
| pinyin4j | 汉字转拼音，用于敏感词拼音匹配 |
| LiveKit | 开源实时音视频通信框架，RTC 能力支撑 |
| Swagger/OpenAPI | API 文档注解 |

> 模块间依赖的完整说明（含 WebSocket 推送通道、用户资料变更事件、下游依赖情况）见 [README.md](README.md) 的「依赖关系」章节。

## 关键文件

| 文件路径 | 说明 |
|---|---|
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/friend/ImFriendController.java | 好友管理用户端 Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/group/ImGroupController.java | 群组管理用户端 Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/message/ImPrivateMessageController.java | 私聊消息用户端 Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/message/ImGroupMessageController.java | 群聊消息用户端 Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/rtc/ImRtcController.java | RTC 通话用户端 Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/livekit/ImLivekitController.java | LiveKit Webhook Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/friend/FriendService.java | 好友关系服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/group/GroupService.java | 群组核心服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/message/PrivateMessageService.java | 私聊消息服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/message/GroupMessageService.java | 群聊消息服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/rtc/RtcService.java | RTC 通话服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/sensitive/SensitiveWordService.java | 敏感词服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/dataobject/group/GroupDO.java | 群组实体类 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/dataobject/message/PrivateMessageDO.java | 私聊消息实体类 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/dataobject/rtc/RtcCallDO.java | RTC 通话实体类 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/enums/ErrorCodeConstants.java | 错误码常量定义 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/framework/config/ImProperties.java | IM 模块配置属性类 |

## 设计与架构补充

以下为现有文档（README.md）未覆盖、但阅读与扩展代码时需要的补充内容。

### 配置驱动

模块配置统一在 `yudao.im.*` 命名空间下管理，配置属性类为 `ImProperties`（位于 `framework/config/`），新增可配置项时应统一收敛到该类，避免散落在各 Service 中。

### 模块间 API 调用

| API | 方法 | 用途 |
|---|---|---|
| AdminUserApi | getUser() | 查询用户基本信息，用于好友信息、群成员信息展示 |
| AdminUserApi | getUsers() | 批量查询用户信息，用于消息列表中展示发送者信息 |
| FileApi | createFile() | 上传文件（头像、图片消息、文件消息） |

消费的提供方：yudao-module-system（AdminUserApi）、yudao-module-infra（FileApi）。模块未使用 MQ 通信。

### Service 层服务清单

| 业务域 | 服务 |
|---|---|
| friend | FriendService（好友关系增删改查、拉黑/取消拉黑）、FriendRequestService（好友申请/同意/拒绝流程） |
| group | GroupService（群组生命周期）、GroupMemberService（成员加入/退出/角色变更）、GroupRequestService（入群申请与审批） |
| message | PrivateMessageService（私聊消息发送、拉取、已读、撤回）、GroupMessageService（群聊消息发送、拉取、已读、撤回）、ChannelMessageService（频道广播消息发送与拉取） |
| channel | ChannelService（频道 CRUD 与状态）、ChannelMaterialService（素材创建、编辑、查询） |
| face | FacePackService（表情包 CRUD 与状态）、FaceUserItemService（用户私人表情） |
| rtc | RtcService（RTC 通话生命周期）、LiveKitService（LiveKit 房间与 Token 生成） |
| sensitive | SensitiveWordService（敏感词库 CRUD） |

### 值对象

| 值对象 | 说明 |
|---|---|
| ImProperties | IM 模块配置属性，`yudao.im.*` 命名空间下的配置项 |
| GroupMemberRoleEnum | 群成员角色枚举：OWNER / ADMIN / NORMAL |
| MessageTypeEnum | 消息类型枚举，兼容 OpenIM 协议编号 |

### 表间关系

除主键外，各表通过以下外键形成 N:1 关系（详细字段见 [README.md](README.md) 的「数据模型」章节）：

| 子表 | 父表 | 外键 |
|---|---|---|
| im_channel_message | im_channel | channel_id |
| im_channel_message | im_channel_material | material_id |
| im_face_pack_item | im_face_pack | pack_id |
| im_group_member | im_group | group_id |
| im_group_request | im_group | group_id |
| im_group_message | im_group | group_id |
| im_rtc_participant | im_rtc_call | call_id |

### LiveKit Webhook 签名验证

LiveKit Webhook 接口除 `@PermitAll` + `@TenantIgnore` 放行注解外，还使用 JWT + SHA256 签名验证请求合法性；处理事件前必须先完成签名校验，防止伪造回调触发业务态清理逻辑。
