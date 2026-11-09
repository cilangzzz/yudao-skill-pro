# IM 即时通讯代码模式与扩展指南 (im)

> 本文档移植自模块 Skill 知识库（skill-im.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层

用户端与管理端常用注解规范：

- `@Tag(name = "xxx")` - Swagger 文档标签
- `@RestController` - REST 控制器
- `@RequestMapping("/im/xxx")` - 请求路径前缀（管理端为 `/im/manager/xxx`）
- `@Validated` - 参数校验
- `@PreAuthorize("@ss.hasPermission('im:manager:{域}:{操作}')")` - 权限控制（仅管理端 Controller 的方法上使用；用户端 Controller 不标注，靠登录态 + Service 业务校验）

示例（用户端好友管理 Controller，通过登录态鉴权，无 RBAC 权限点）：

```java
@Tag(name = "管理后台 - IM 好友")
@RestController
@RequestMapping("/im/friend")
@Validated
public class ImFriendController {
    @Resource
    private ImFriendService friendService;

    @GetMapping("/list")
    @Operation(summary = "获得当前登录用户的好友列表")
    public CommonResult<List<ImFriendRespVO>> getMyFriendList() {
        List<ImFriendDO> friends = friendService.getFriendList(getLoginUserId());
        return success(buildFriendRespVOList(friends)); // 组装昵称 / 头像等展示字段
    }
}
```

> `getLoginUserId()` 来自 `cn.iocoder.yudao.framework.web.core.util.WebFrameworkUtils`（静态导入），不是旧版的 `LoginContextHolder`。服务接口统一带 `Im` 前缀（`ImFriendService`、`ImFriendDO`），不存在无前缀的 `FriendService`。

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
public class ImPrivateMessageServiceImpl implements ImPrivateMessageService {
    @Resource
    private ImPrivateMessageMapper privateMessageMapper;
    @Resource
    private ImWebSocketService webSocketService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ImPrivateMessageDO sendPrivateMessage(Long senderId, ImPrivateMessageSendReqVO reqVO) {
        // 1. 好友关系校验（friendService.validateFriend）
        // 2. clientMessageId 幂等：已存在则直接回查返回
        // 3. 消息内容校验（ImMessageUtils）+ 文本敏感词过滤
        // 4. 保存消息（唯一键冲突时回查已有记录）
        ImPrivateMessageDO message = ...;
        privateMessageMapper.insert(message);
        // 5. 推送：交给 ImWebSocketService，内部在事务提交后异步发送
        webSocketService.sendNotificationAsync(...);
        return message;
    }
}
```

> 实际实现统一由 `ImWebSocketServiceImpl#executeAfterTransaction` 封装「事务内注册 afterCommit、无事务则同步执行、经 `getSelf()` 代理走 `@Async`」，业务代码不要自己注册 `TransactionSynchronization`（详见 pitfalls 3.1）。

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
public interface ImPrivateMessageMapper extends BaseMapperX<ImPrivateMessageDO> {
    default PageResult<ImPrivateMessageDO> selectPage(ImPrivateMessageManagerPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ImPrivateMessageDO>()
                .eqIfPresent(ImPrivateMessageDO::getSenderId, reqVO.getSenderId())
                .eqIfPresent(ImPrivateMessageDO::getReceiverId, reqVO.getReceiverId())
                .eqIfPresent(ImPrivateMessageDO::getType, reqVO.getType())
                .betweenIfPresent(ImPrivateMessageDO::getSendTime, reqVO.getSendTime())
                .orderByDesc(ImPrivateMessageDO::getId));
    }
}
```

> 真实实现里同时传入 senderId + receiverId 时会额外加「双向」条件（A→B 或 B→A），用于查看两人的完整会话；管理端分页 VO 是 `ImPrivateMessageManagerPageReqVO`（继承 `PageParam`），不是无前缀的 `PrivateMessagePageReqVO`。

### DAL 多数据库兼容约定

im 模块已适配 MySQL / PostgreSQL / Oracle / SQL Server。相关能力来自框架（`SqlDialectUtils`、`BaseMapperX#selectListLimitN`、`BaseMapperX#selectOneForUpdate`），不是 im 自研；二次开发沿用以下写法即可保持跨库一致。

| 场景 | 正确写法 | 不要使用 | 说明 |
|---|---|---|---|
| Wrapper 查询限制条数 | `selectListLimitN(wrapper, n)` | `.last("LIMIT " + n)` | 由 MyBatis-Plus 分页插件按执行数据源生成 `LIMIT` / `FETCH FIRST` / `OFFSET ... FETCH`，不执行 COUNT；`n == 0` 直接返回空列表，`n < 0` 抛 `IllegalArgumentException`；SQL Server 分页要求 wrapper 已设置 `orderBy` |
| 锁定读 | `selectOneForUpdate(...)`；群记录封装为 `ImGroupMapper#selectByIdForUpdate` | `.last("FOR UPDATE")` | 必须在外层 `@Transactional` 中调用，否则行锁随 auto-commit 立即释放；Wrapper 不能使用 `last` / `groupBy` / `having` / 自定义参数别名 |
| 手写 `@Select` 日期分桶 | `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@date('col')}` | `DATE(col)` | `SELECT` 与 `GROUP BY` 复用同一片段；MySQL 输出 `DATE(col)`，其它方言输出 `TO_CHAR` / `CONVERT` 等日期文本 |
| 手写 `@Select` 行数限制 | `${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@limitParam('limit', true)}` | `LIMIT #{limit}` | `ordered=true` 表示语句已有 `ORDER BY`（SQL Server 的 `OFFSET ... FETCH` 必须跟在 `ORDER BY` 之后） |
| 统计列别名 | `statDate`、`sizeRange` 等业务名 | `date`、`range` 等保留字 | 部分数据库不接受保留字作列别名；对外响应字段名可另行映射（如群规模接口仍返回 `range`） |

示例（游标拉取的限量统一走分页插件）：

```java
default List<ImPrivateMessageDO> selectListByMinId(Long userId, Long minId,
                                                   LocalDateTime minSendTime, Integer size) {
    LambdaQueryWrapperX<ImPrivateMessageDO> wrapper = new LambdaQueryWrapperX<>();
    wrapper.and(w -> w.eq(ImPrivateMessageDO::getSenderId, userId)
                    .or()
                    .eq(ImPrivateMessageDO::getReceiverId, userId))
            .gt(ImPrivateMessageDO::getId, minId)
            .gt(ImPrivateMessageDO::getSendTime, minSendTime)
            .orderByAsc(ImPrivateMessageDO::getId);
    return selectListLimitN(wrapper, size); // 不要追加 .last("LIMIT " + size)
}
```

示例（数据看板的手写统计 SQL，日期分桶与行数限制均走方言工具）：

```java
@Select("SELECT ${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@date('create_time')} AS statDate, " +
        "COUNT(*) AS count FROM system_users " +
        "WHERE deleted = 0 AND create_time >= #{beginTime} AND create_time < #{endTime} " +
        "GROUP BY ${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@date('create_time')}")
List<Map<String, Object>> selectNewUserDailyCount(@Param("beginTime") LocalDateTime beginTime,
                                                  @Param("endTime") LocalDateTime endTime);
```

Wrapper 条件优先使用 `LambdaQueryWrapperX` 的方法引用（如 `eq(ImPrivateMessageDO::getSenderId, ...)`）而不是字符串列名，编译期即可校验字段；`selectListLimitN` 走查询而非内存截断，也不要在其外层再叠加 `last("LIMIT ...")`。

### 异常处理

错误码前缀：`1_040_XXX_XXX`（[yudao-module-im/.../ErrorCodeConstants.java](../../../yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/enums/ErrorCodeConstants.java)），按子域分段：

| 子段 | 子域 | 说明 |
|------|------|------|
| `1_040_300_XXX` | 消息 | 消息不存在、撤回、敏感词、私聊已读等 |
| `1_040_400_XXX` | 群 | 群不存在、已封禁、已解散、群主/管理员权限 |
| `1_040_500_XXX` | 群成员 | 入退群、禁言、踢人、群管理员 |
| `1_040_510_XXX` | 加群申请 | 申请不存在、已处理、非审批人 |
| `1_040_600_XXX` | 好友 | 不是好友、不能加自己、黑名单 |
| `1_040_610_XXX` | 好友申请 | 申请不存在、已是好友 |
| `1_040_700_XXX` | 敏感词 | 敏感词不存在/重复 |
| `1_040_800_XXX` | 表情包 | 表情包/个人表情相关 |
| `1_040_810_XXX` | 频道 | 频道编码/素材/消息 |
| `1_040_900_XXX` | 实时通话 | RTC 会话、忙碌、邀请人校验 |

### 统一响应

- 成功响应：`CommonResult.success(data)`
- 失败响应：`throw exception(ErrorCode)` 抛出业务异常，由全局异常处理器统一封装

## 扩展指南

### 新增消息类型

1. **定义消息类型枚举**：在 `ImContentTypeEnum`（`enums/ImContentTypeEnum.java`）中添加新的消息类型编号，保持与 OpenIM 协议段位兼容，并明确两个标志：`persistent`（是否入 `im_xxx_message` 表，决定离线 pull 能否拉到）与 `normal`（是否算普通用户聊天消息，发送入口的 `@AssertTrue` 只放行 normal 类型）。
2. **定义消息内容类**：在 `dal/dataobject/message/content` 下创建 `XxxMessage` 类（命名是 `Message` 后缀，不是 DTO），定义该类型 content JSON 的结构；同时在 `ImMessageUtils#validateUserMessageContent` 中补充该类型的字段校验。

   ```java
   @Data
   public class VideoMessage {
       private String url;
       private String coverUrl;
       private Integer duration;
       private Integer width;
       private Integer height;
       private Long size;
       private QuoteMessage quote; // 引用消息，可选
   }
   ```

3. **实现消息渲染**：在客户端实现该消息类型的渲染逻辑。
4. **敏感词处理**：只有文本类内容需要敏感词过滤；发送入口对 `ImContentTypeEnum.TEXT` 调用 `ImSensitiveWordService#validateText`。

### 新增管理后台接口

1. **创建 Manager Controller**：在 `controller/admin/manager/` 下创建新的 Controller 类。

   ```java
   @Tag(name = "管理后台 - IM XXX")
   @RestController
   @RequestMapping("/im/manager/xxx")
   @Validated
   public class ImXxxManagerController {

       @PostMapping("/create")
       @Operation(summary = "新增 XXX")
       @PreAuthorize("@ss.hasPermission('im:manager:xxx:create')")
       public CommonResult<Long> createXxx(@Valid @RequestBody ImXxxSaveReqVO reqVO) {
           return success(xxxService.createXxx(reqVO));
       }
       // 其余 CRUD 方法同样在「方法上」标注 im:manager:xxx:{query|update|delete}
   }
   ```

2. **定义权限标识**：在权限系统中注册 `im:manager:xxx:query` / `im:manager:xxx:create` / `im:manager:xxx:update` / `im:manager:xxx:delete` 权限（权限点格式是 `im:manager:{域}:{操作}`，不是 `im:xxx:query`）。
3. **实现 Service 方法**：在对应的 Service 中实现管理端的业务逻辑。
4. **添加数据权限**：根据需要添加数据权限控制。

### 最佳实践

| 实践 | 说明 |
|---|---|
| clientMessageId 幂等发送 | 客户端生成 UUID 作为 clientMessageId，服务端通过唯一索引保证幂等，避免网络重试导致重复消息 |
| 事务感知异步推送 | 使用 afterCommit 回调确保事务提交后再推送消息，避免接收方读到未提交数据 |
| 已读位点持久化 | 已读游标存在 DB 表 `im_conversation_read`（user_id + conversation_type + target_id 唯一），用「只增不减」的条件 UPDATE（`updateReadMessageIdToLarger`）保证并发下不回退；不要另建 Redis 已读游标（模块 Redis 只用于好友/群成员状态缓存与 RTC 锁） |
| 双向好友独立属性 | 每对好友的 2 行记录拥有独立属性，更新时只修改当前用户方向的记录 |
| 群组角色权限校验 | 通过 ImGroupMemberDO.role 字段判断操作权限，注意权限边界（管理员不可踢管理员） |
| LiveKit Webhook 安全 | 使用 JWT + SHA256 签名验证 Webhook 请求，不要在未验证签名的情况下处理事件 |
| 敏感词过滤时机 | 敏感词过滤在消息发送时执行，过滤后直接存储，已发送消息不受后续词库更新影响 |
| 消息增量拉取 | 用消息 id 游标代替 offset 分页：在线增量 `pull` 传 `minId`（取 id 更大、且受时间窗口限制的消息），历史回看传 `maxId`（取 id 更小的消息），避免 offset 深分页的性能问题 |
| 多数据库兼容 | 限量查询走 `selectListLimitN`、锁定读走 `selectOneForUpdate`、手写 SQL 的日期/限量走 `SqlDialectUtils`，不要硬编码 `LIMIT` / `FOR UPDATE` / `DATE()`，以免破坏 MySQL / PostgreSQL / Oracle / SQL Server 的跨库能力 |

## 模块依赖

### 内部依赖（其他模块 / 框架）

| 依赖 | 用途 |
|---|---|
| yudao-module-system | AdminUserApi - 查询用户信息、校验用户存在性；消费 AdminUserProfileUpdateMessage 用户资料变更事件 |
| yudao-module-infra | WebSocketSenderApi - WebSocket 推送通道（本模块未使用 FileApi，文件/图片 URL 由客户端直传后随消息内容提交） |
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |
| yudao-framework-redis | Redis 操作封装：好友状态 / 群 / 群成员 id 缓存、RTC 通话分布式锁 |
| yudao-framework-tenant | 租户支持（`@TenantJob` 逐租户执行 Job、`@TenantIgnore` 放行 Webhook） |

### 外部依赖（第三方库 / 服务）

| 依赖 | 用途 |
|---|---|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| sensitive-word | 基于 Trie 树的敏感词过滤库 |
| pinyin4j | 汉字转拼音（经 `StrUtils.toPinyin`），用于好友列表返回 `displayNamePinyin` / `nicknamePinyin`，供客户端首字母排序与检索；不用于敏感词匹配 |
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
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/rtc/ImRtcCallController.java | RTC 通话用户端 Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/controller/admin/rtc/ImRtcLiveKitController.java | LiveKit Webhook Controller |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/friend/ImFriendService.java | 好友关系服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/group/ImGroupService.java | 群组核心服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/message/ImPrivateMessageService.java | 私聊消息服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/message/ImGroupMessageService.java | 群聊消息服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/rtc/ImRtcCallService.java | RTC 通话服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/service/sensitiveword/ImSensitiveWordService.java | 敏感词服务接口 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/dataobject/group/ImGroupDO.java | 群组实体类 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/mysql/group/ImGroupMapper.java | 群 Mapper，含 `selectByIdForUpdate` 锁定读 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/mysql/statistics/ImStatisticsManagerMapper.java | 数据看板统计 SQL，含 `SqlDialectUtils` 多数据库写法 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/dataobject/message/ImPrivateMessageDO.java | 私聊消息实体类 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/dal/dataobject/rtc/ImRtcCallDO.java | RTC 通话实体类 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/enums/ErrorCodeConstants.java | 错误码常量定义 |
| yudao-module-im/src/main/java/cn/iocoder/yudao/module/im/framework/config/ImProperties.java | IM 模块配置属性类 |

## 设计与架构补充

以下为现有文档（README.md）未覆盖、但阅读与扩展代码时需要的补充内容。

### 配置驱动

模块配置统一在 `yudao.im.*` 命名空间下管理，配置属性类为 `ImProperties`（位于 `framework/config/`），新增可配置项时应统一收敛到该类，避免散落在各 Service 中。

### 模块间 API 调用

| API | 方法 | 用途 |
|---|---|---|
| AdminUserApi | `getUser(Long id)` | 查询单个用户基本信息（如邀请人 / 发起人昵称） |
| AdminUserApi | `getUserMap(Collection<Long> ids)` | 批量查询用户信息，用于好友 / 群成员 / 消息发送者展示（模块内最常用） |
| AdminUserApi | `validateUser(Long id)` | 校验用户存在性（如发起好友申请的目标用户） |
| WebSocketSenderApi | `send(...)` 系列（经 `ImWebSocketService` 封装） | WebSocket 实时推送通道 |

消费的提供方：yudao-module-system（AdminUserApi）、yudao-module-infra（WebSocketSenderApi）。模块**不使用 MQ 中间件**；`mq/consumer/friend/AdminUserProfileUpdateConsumer` 虽放在 mq 包下，实际是 Spring 事件监听器（`@TransactionalEventListener(AFTER_COMMIT) + @Async`），监听 system 模块的 `AdminUserProfileUpdateMessage` 并推送 FRIEND_INFO_UPDATED。本模块不调用 `FileApi`，文件 / 图片 URL 由客户端上传后随消息 content 提交。

### Service 层服务清单

| 业务域 | 服务 |
|---|---|
| friend | ImFriendService（好友关系增删改查、拉黑/取消拉黑）、ImFriendRequestService（好友申请/同意/拒绝流程） |
| group | ImGroupService（群组生命周期）、ImGroupMemberService（成员加入/退出/角色变更）、ImGroupRequestService（入群申请与审批） |
| message | ImPrivateMessageService（私聊消息发送、拉取、已读、撤回）、ImGroupMessageService（群聊消息发送、拉取、已读、撤回）、ImChannelMessageService（频道广播消息发送与拉取） |
| conversation | ImConversationReadService（会话已读位点：DB 表 + 只增不减 CAS 更新） |
| channel | ImChannelService（频道 CRUD 与状态）、ImChannelMaterialService（素材创建、编辑、查询） |
| face | ImFacePackService（表情包 CRUD 与状态）、ImFacePackItemService（表情包项）、ImFaceUserItemService（用户私人表情） |
| rtc | ImRtcCallService（RTC 通话生命周期与 LiveKit 交互；房间 / Token 能力由 `framework/rtc/core/LiveKitClient` 提供，无独立 LiveKitService） |
| sensitiveword | ImSensitiveWordService（敏感词库 CRUD 与 Trie 缓存） |
| statistics | ImStatisticsManagerService（运营数据看板聚合） |
| websocket | ImWebSocketService（通知封装与事务提交后异步推送） |

### 值对象

| 值对象 | 说明 |
|---|---|
| ImProperties | IM 模块配置属性，`yudao.im.*` 命名空间下的配置项 |
| ImConversationTypeEnum | 会话类型枚举：NONE(0) / PRIVATE(1) / GROUP(2) / CHANNEL(3) |
| ImGroupMemberRoleEnum | 群成员角色枚举：OWNER(1) / ADMIN(2) / NORMAL(3) |
| ImContentTypeEnum | 消息类型枚举，兼容 OpenIM 协议编号，带 persistent / normal 双标志 |
| ImMessageStatusEnum | 消息状态枚举：SENDING(-1) / NORMAL(0) / RECALL(2) |

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
