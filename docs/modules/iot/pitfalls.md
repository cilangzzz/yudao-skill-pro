# 注意事项与已知坑点

> 使用 iot 模块时的常见问题、易踩坑点和最佳实践。

iot 模块为多子模块布局：`yudao-module-iot-biz`（管理端业务，打包进 yudao-server）、`yudao-module-iot-core`（biz 与 gateway 共享的消息总线/DTO）、`yudao-module-iot-gateway`（设备接入网关，独立 Spring Boot 进程）。业务数据存 MySQL；属性数据与消息日志存时序库，由 `yudao.iot.storage.type` 二选一（默认 `tdengine`，或 `iotdb`），两类存储的事务与租户行为差异是多数坑点的根源。

## 1. 多租户相关

### 1.1 「忽略租户」注解有两处硬约定：跨租户缓存与 TDengine Mapper

**问题**: 新增查询方法时漏写 `@TenantIgnore`，设备/产品相关查询在网关或 MQ 链路下查不到数据（返回 null 或空列表）；反之，给普通管理端查询误加 `@TenantIgnore` 会造成跨租户数据泄露。给新的 TDengine Mapper 忘加 `@InterceptorIgnore` 则直接启动或执行报错。

**原因**:
- 设备、产品、物模型是 `TenantBaseDO` 表，但缓存被刻意设计为**跨租户共享**：`IotDeviceServiceImpl#getDeviceFromCache`（两个重载）、`IotProductServiceImpl#getProductFromCache`、`IotThingModelServiceImpl#getThingModelListByProductIdFromCache` 都是 `@Cacheable` + `@TenantIgnore` 组合，RedisKeyConstants 中对应 key 注释明确写了「使用 Spring Cache 操作（忽略租户）」。跨租户安全依赖「productKey + deviceName / productId 全局唯一」这一前提，而不是缓存 key 隔离。
- TDengine 的 SQL（`IotDevicePropertyMapper`、`IotDeviceMessageMapper`）必须加 `@InterceptorIgnore(tenantLine = "true")`，源码注释写明原因：「JSqlParser 对 TDengine 的 SQL 解析会报错」。少了它租户拦截器会尝试改写 TDengine SQL 直接失败。IoTDB 实现（`dal/iotdb` 下的 DAO）走独立 JDBC 会话，不经过 MyBatis 租户拦截器，无需该注解。

**解决**:
- 写 iot 查询前先确认调用链：来自网关进程 RPC（`IoTDeviceApiImpl`）或 MQ 消费的方法，应走带 `@TenantIgnore` 的缓存方法获取设备，再用 `device.getTenantId()` 显式恢复租户；管理端列表/详情保持走 `deviceMapper.selectById` 等租户过滤查询。
- 新建 TDengine Mapper 模板：

```java
@Mapper
@TDengineDS
@InterceptorIgnore(tenantLine = "true") // 避免 SQL 解析，因为 JSqlParser 对 TDengine 的 SQL 解析会报错
public interface XxxTdengineMapper { ... }
```

### 1.2 MQ 消费与网关 RPC 链路的租户上下文需要手工补齐

**问题**: 在 MQ 消费者或定时任务里新加业务逻辑时，一执行带租户过滤的 MySQL 查询就查不到数据（`TenantContextHolder` 为空），或抛租户相关异常；而同样代码放在 Controller 链路里正常。

**原因**: HTTP 请求的租户上下文由 Web 过滤器注入，MQ/Job/RPC 链路没有。iot 模块的补齐方式不统一，容易漏：
- `IotDeviceMessageSubscriber#onMessage` 与 `IotDataRuleMessageSubscriber#onMessage` 显式 `TenantUtils.execute(message.getTenantId(), ...)`；
- `IotSceneRuleMessageSubscriber#onMessage` **不设置**租户，依赖 `IotSceneRuleServiceImpl#executeSceneRuleByDevice` 内部先通过 `@TenantIgnore` 缓存取设备，再 `TenantUtils.execute(device.getTenantId(), ...)`；
- 设备动态注册 `IotDeviceServiceImpl#registerDevice` 用 `TenantUtils.execute(product.getTenantId(), ...)` 包住建设备逻辑。

**解决**: 新写消费者/Job 时，明确采用「先从忽略租户的缓存取 device/product，再 `TenantUtils.execute(tenantId, ...)`」的模式（参考 `executeSceneRuleByDevice`）；定时任务用 `@TenantJob`（如 `IotOtaUpgradeJob`、`IotDeviceOfflineCheckJob`）。不要假设上下文已存在。

## 2. 缓存相关

### 2.1 Spring Cache 注解自调用失效，项目统一用 getSelf() 规避

**问题**: 直接在 Service 内部 `this.xxx()` 调用带 `@Cacheable`/`@CacheEvict` 的方法，缓存完全不生效（不读、不清），且无任何报错，表现为「改了数据但界面/网关读到旧值」。

**原因**: Spring Cache 基于 AOP 代理，内部调用不走代理。iot 模块大量使用该注解（`RedisKeyConstants` 中 DEVICE / PRODUCT / THING_MODEL_LIST / SCENE_RULE_LIST / DATA_RULE_LIST / DATA_SINK 六组缓存），因此 `IotDeviceServiceImpl#deleteDeviceCache`、`IotThingModelServiceImpl#deleteThingModelListCache`、`IotSceneRuleServiceImpl#getMatchedSceneRuleListByMessage`、`IotDeviceMessageServiceImpl` 都通过 `getSelf()`（`SpringUtil.getBean(getClass())`）绕过：

```java
private void deleteDeviceCache(IotDeviceDO device) {
    // 保证 Spring AOP 触发
    getSelf().deleteDeviceCache0(device);
}

@Caching(evict = {
    @CacheEvict(value = RedisKeyConstants.DEVICE, key = "#device.id"),
    @CacheEvict(value = RedisKeyConstants.DEVICE, key = "#device.productKey + '_' + #device.deviceName")
})
public void deleteDeviceCache0(IotDeviceDO device) { }
```

**解决**: 在 iot Service 内部调用任何带缓存注解的方法（包括新写的），一律走 `getSelf().xxx()` 或注入自身接口；代码评审时重点检查 `deleteDeviceCache0`、`deleteThingModelListCache0` 这类空方法是否被直接 `this` 调用。

### 2.2 事务提交前清缓存，存在脏缓存回填窗口

**问题**: 批量改设备分组、绑定/解绑网关后偶发读到旧设备数据，且旧值会**一直留在 Redis 里**（直到下次写操作），不是一次性的读到旧值。

**原因**: `IotDeviceServiceImpl#updateDeviceGroup`、`#bindDeviceGateway`、`#unbindDeviceGateway` 都是 `@Transactional`，但 `deleteDeviceCache(devices)` 在事务**提交前**执行：清缓存 → 另一线程从 DB 读到未提交前旧数据并回填缓存 → 事务提交。DB 已是新值、缓存却是旧值。`IotThingModelServiceImpl` 的写方法（`@Transactional` 内调 `deleteThingModelListCache`）同理。

**解决**: 把缓存清理挪到事务提交后执行（`TransactionSynchronization.afterCommit`），或采用「先更新 DB → 清缓存 → 延迟再清一次」的双重删除；至少要意识到该窗口的存在，排查这类不一致时先看是否处于事务方法内。

## 3. 事务相关

### 3.1 产品发布跨 MySQL 与时序库，@DSTransactional 无法回滚时序库 DDL

**问题**: 产品发布（或手动同步表结构）时时序库表结构变更失败，MySQL 里产品状态却可能已变成「已发布」；或反过来，发布成功但时序库里缺少某属性列，设备上报该属性被丢弃。

**原因**: `IotProductServiceImpl#updateProductStatus` 标注的是 dynamic-datasource 的 `@DSTransactional`（非 Spring `@Transactional`），方法内先 `devicePropertyDataService.defineDevicePropertyData(id)` 建/改时序表，再更新 MySQL 产品状态。无论 TDengine 还是 IoTDB，`CREATE/ALTER TABLE` 都是 DDL，没有事务回滚能力，`@DSTransactional` 只能提供有限的多数据源一致性。设备消息表则由 `IotStorageInitRunner`（ApplicationRunner）在启动时调用对应 DAO 的 `initialize()` 创建（TDengine 为超级表 `device_message`，IoTDB 为全局表 `device_message`）。

**解决**: 发布失败后用「产品详情 → 同步表结构」（`IotProductService#syncProductPropertyTable`）重新执行 `defineDevicePropertyData`；对一致性要求高的场景，先同步表结构成功后再更新产品状态，失败时中断发布。

### 3.2 设备导入是「部分成功」语义，且旧设备匹配只按 deviceName

**问题**: Excel 批量导入设备时，部分行失败是正常的（记录在 `failureDeviceNames`），但有两个意外：① 某行抛出非 `ServiceException` 的异常（如 NPE）时，**整批已成功的导入全部回滚**，前端却拿到的是逐行结果；② Excel 里 deviceName 与**其他产品**下已有设备同名时，不会新建，而是错误地更新了那个产品下的设备（或报「设备标识已经存在」）。

**原因**: `IotDeviceServiceImpl#importDevice` 标注 `@Transactional(rollbackFor = Exception.class)`，循环内 `catch (ServiceException)` 继续处理下一行（此时不会回滚，之前已插入的设备随事务提交），其他异常则整体回滚。而存在性判断用的是 `deviceMapper.selectByDeviceName(importDevice.getDeviceName())`——`IotDeviceMapper#selectByDeviceName` 只按 deviceName 查询、不带 productKey；设备名唯一性约束实际是「同一 productKey 下唯一」（`validateCreateDeviceParam` 用的是 `selectByProductKeyAndDeviceName`），跨产品同名合法。

**解决**: 导入前确认 Excel 内设备名跨产品无重名；期望「失败行不影响成功行」时，不要依赖该方法处理会抛非 ServiceException 异常的脏数据。若要修代码，应把导入的存在性判断改为按 `productKey + deviceName` 查询。

### 3.3 设备状态消息必须在事务外处理，规则执行与状态变更同一事务

**问题**: 在已有事务（如业务方法内同步发布设备状态消息）里触发状态更新，会抛 `IllegalStateException("状态消息不能在已有事务中处理")`；或者状态已更新、规则刚执行失败时，状态没有回滚，出现「设备在线但联动没触发」。多网关节点场景下，旧节点迟到的离线消息还可能把刚连到新节点的设备误判为离线。

**原因**: `IotDeviceMessageServiceImpl#processStateUpdateMessage` 显式检查 `TransactionSynchronizationManager.isActualTransactionActive()`，因为 Local 消息总线在发布线程同步消费，若加入外层事务，`handleStateUpdateMessage` 返回时事务并未提交，后续「网关离线联动子设备」就失去前提。状态事务内先按事件时间（`reportTime`，截断到秒）与上下线时间水位做**条件 UPDATE**（重复/迟到的状态直接返回 false），状态真的变化后，才在同一事务内执行场景联动与数据流转；规则执行后还会检查 `isRollbackOnly()`，避免回滚被静默吞掉。旧节点离线通过 `isStaleServerOffline` 比较 Redis 中的当前 serverId 过滤（EMQX 除外）。

**解决**: 不要在事务方法内发布 `STATE_UPDATE` 消息；状态处理一律走 `deviceMessageService.sendDeviceMessage(...)` 等入口，让消息总线在事务外触发。规则动作应尽量幂等、少抛异常；排查「状态变了但规则没跑」时，先看状态条件更新是否返回 false（重复/迟到消息），再看规则是否把事务标记为 rollback-only。

## 4. 时序存储相关（TDengine / IoTDB）

### 4.1 属性列类型变更按「先删列再加列」执行，历史数据丢失；查询兜底依赖异常文本

**问题**: 修改物模型属性的数据类型（或把 text 长度改小）后，该属性的历史曲线全部变空；另外设备消息/历史属性页面在某些环境下「看起来没数据」其实是查询异常被吞了。

**原因**: `IotDevicePropertyMapper#alterProductPropertySTable`（default 方法）对类型变更的字段执行 `alterProductPropertySTableDropField` + `alterProductPropertySTableAddField`——TDengine 不支持直接改列类型，删列即删历史；注释明确「TDengine 长度修改时，只允许变长」，长度缩小也会被当成类型变更走删加流程。同时，`IotDeviceMessageServiceImpl#getDeviceMessagePage`、`IotDevicePropertyServiceImpl#getHistoryDevicePropertyList`、`defineDevicePropertyData` 都靠 `exception.getMessage().contains("Table does not exist")` 判断表不存在并返回空，TDengine 未启动/超级表未初始化时页面静默为空，不报错。

**解决**: 物模型属性的数据类型在产品发布前定好，发布后尽量不改类型（新增属性、加长 text 是安全的）；改了类型要接受历史数据清零。排查「无数据」问题时先确认 TDengine 可用、`IotStorageInitRunner` 启动日志正常，再查业务，不要被空页面误导。

### 4.2 IoTDB：物理类型变更同样 DROP + ADD，DDL 不参与事务；表结构不兼容时应用直接启动失败

**问题**: 切换到 `yudao.iot.storage.type=iotdb` 后：修改属性物理类型，历史数据同样丢失；初始化中途失败，重启后可能缺表/缺列；升级版本后应用启动直接抛 `IllegalStateException`，提示 `device_message` 结构不兼容。

**原因**: `IotDevicePropertyIoTDBDAO#defineProductPropertyTable` 对物理类型变化的列执行 `dropColumn` + `addColumn`（IoTDB 不支持改列类型），旧列数据不保留；INT/ENUM/BOOL 都映射为 INT32，这三者之间变化不会改表。IoTDB 的 DDL 不参与事务、无法回滚，但 ADD/DROP 均为幂等语句，再次定义即可收敛。另外 `IotDeviceMessageIoTDBDAO#initialize` 会校验消息表结构（`device_id` 必须是唯一 TAG，其它列为类型一致的 FIELD），不兼容时**直接抛异常终止启动**，不会自动修改或删除表；`IotDevicePropertyIoTDBDAO#initialize` 只校验前提条件，产品属性表在发布/手动同步时创建。

**解决**: 切换时序库前先确认 `iotdb` 连接可用；属性物理类型（如 BOOLEAN → TEXT）发布后不要随意修改，改了要接受历史清零。启动报 `device_message` 结构不兼容时，按提示导出需要保留的数据后删表重建（或更换数据库），应用不会自动处理。不要同时保留 TDengine 的旧数据并期望自动迁移，切换存储类型不会搬迁历史数据。

## 5. 消息总线与异步

### 5.1 本地消息总线同步分发且仅适用单机；RocketMQ 链路无顺序保障，下行依赖 Redis serverId

**问题**: 单机 local 模式下，设备消息处理慢会拖住发布方线程（如网关接入线程）；集群/大流量场景切 RocketMQ 后，设备上下线状态偶发「后发先至」，最终状态与实际相反。向 HTTP 等短连接设备下发消息时报「设备未连接网关」（`DEVICE_DOWNSTREAM_FAILED_SERVER_ID_NULL`）。

**原因**: `IotLocalMessageBus#post` 用 `applicationContext.publishEvent` 同步分发（类注释：「仅适用于单机场景！！！」），订阅者（`IotDeviceMessageSubscriber` 等 3 个）在发布线程内依次执行。`IotRocketMQMessageBus#post` 源码留有 `// TODO @芋艿：需要 orderly！`，消费用 `MessageListenerConcurrently` 并发消费，STATE_UPDATE 等状态消息可能乱序；下行消息路由靠 `IotDevicePropertyServiceImpl#getDeviceServerId` 读 Redis（`iot:device_server_id`），设备未上报过 serverId 或 Redis 数据丢失时抛 `DEVICE_DOWNSTREAM_FAILED_SERVER_ID_NULL`（`IotDeviceMessageServiceImpl#sendDeviceMessage`）。下行 PUSH/PULL 模型也仅有 TODO 注释（「下行消息需要区分 PUSH 和 PULL 模型」），短连接设备目前无拉取通道。

**解决**: 生产集群环境必须配置 RocketMQ 消息总线；对设备状态强一致的场景，消费端以消息时间戳或设备实际心跳做兜底判断（`IotDeviceOfflineCheckJob` 以 `iot:device_report_times` 的活跃时间 + 超时判定活跃型设备，连接型设备还要校验所在网关的存活标记 `iot:gateway_server:{serverId}`）。下行失败先检查该设备是否有上行记录（serverId 是否已写入 Redis）。**不要在事务内发布状态消息**：Local 总线同步消费，`processStateUpdateMessage` 会直接拒绝已有事务（见 3.3）。

### 5.2 @Async 写消息日志失败被静默吞掉

**问题**: 设备消息日志（时序库 `device_message`）偶发缺条，接口无任何报错，只能翻日志发现。

**原因**: `IotDeviceMessageServiceImpl#createDeviceLogAsync` 是 `@Async` 方法，内部 try/catch 后仅 `log.error`（源码注释：「@Async 方法的异常默认会被 handler 吞掉，这里显式记录便于排查」）。注意它是**包私有**方法，靠 `getSelf()` 调用才走代理异步执行；若改成直接 `this.createDeviceLogAsync(...)` 会退化为同步执行且注解失效。同理 `IotDevicePropertyServiceImpl#updateDeviceReportTimeAsync` 也是 `@Async`（只写 Redis，失败影响较小）。另一个隐患：`@Async` 线程不继承 `TenantContextHolder`，这两个方法恰好只按 deviceId 操作 TDengine/Redis 才安全，新加的 @Async 方法若查 MySQL 租户表会踩 1.2 的坑。

**解决**: 排查消息日志缺失时直接搜 `[createDeviceLogAsync]` 错误日志；TDengine 不可用时消息日志会持续丢失但不影响主流程。新写 @Async 方法须自带 try/catch + 显式日志，且不要在里面依赖租户上下文。

## 6. 并发与状态机

### 6.1 OTA 升级：创建任务无并发防护，多条进行中记录时固定取第一条

**问题**: 对同一设备并发创建两个升级任务都能成功，设备出现两条「进行中」记录；此后设备上报升级进度可能记到**另一个任务**的记录上，任务统计（成功/失败数）失真。

**原因**: `IotOtaTaskServiceImpl#createOtaTask` 只校验固件存在、同一固件下任务名不重复、设备范围（`validateOtaTaskDeviceScope`），**没有校验设备是否已在其它进行中任务里**，事务内插入任务后直接为设备批量创建升级记录，因此同一设备可以同时出现在多个进行中任务中。`IotOtaTaskRecordServiceImpl#updateOtaRecordProgress` 按设备查询 `IN_PROCESS_STATUSES` 的记录，`records.size() > 1` 只 `log.warn`，然后 `CollUtil.getFirst(records)` 取第一条更新，进度可能记到另一个任务的记录上。另外 `IotOtaUpgradeJob` 源码自注两个 TODO：逐条查询存在 N+1、离线设备直接跳过推送（「当前逻辑跳过了离线的设备，但未充分利用 MQTT 的离线消息能力」），设备离线期间的 PENDING 记录只能等下次在线后被推送。

**解决**: 创建任务时在业务上避免同一设备重复纳入进行中任务；若开放 API，建议增加「设备维度进行中唯一」校验（数据库唯一索引或分布式锁）。发现某设备有多条进行中记录时，以 `updateOtaRecordProgress` 的 warn 日志定位并手工取消多余记录。

### 6.2 从缓存获取设备后未判空的 NPE 风险；场景触发器匹配存在「首个不匹配即返回」

**问题**: 网关子设备注册 RPC 传入的网关设备已被删除时，抛 NullPointerException；配置了多个触发器的场景规则，只有第一个触发器参与设备匹配，排查「规则不触发」时容易被误导。

**原因**: `IotDeviceServiceImpl#registerSubDevices` 通过 `getSelf().getDeviceFromCache(gatewayProductKey, gatewayDeviceName)` 取网关设备后，直接 `TenantUtils.execute(gatewayDevice.getTenantId(), ...)`，判空发生在更内层的 `registerSubDevices0`，已经来不及；`getDeviceFromCache` 带 `unless = "#result == null"`，设备不存在时返回 null。`IotSceneRuleServiceImpl#executeSceneRuleByDevice` 目前已补判空（`device == null` 时 warn 并 return），但 `getSceneRuleListByProductIdAndDeviceIdFromCache` 的 for 循环内直接 `return`：首个 trigger 产品/设备不匹配就返回 false，多触发器场景下后续触发器不会参与匹配。

**解决**: 调用 `getDeviceFromCache` 后统一先判空（或改用 `validateDeviceExistsFromCache`）；`registerSubDevices` 应在取 `tenantId` 前判空。复现 NPE 时先确认设备是否刚被删除、MQ 是否有积压；排查「规则不触发」时注意多触发器的早退逻辑。

## 7. 错误码相关

### 7.1 错误码重复定义与 biz/gateway 双段编码

**问题**: 前端/调用方按错误码做分支处理时行为错乱：提示语与实际原因对不上。两处已知重复：
- `1_050_002_003` 同时是 `THING_MODEL_NAME_EXISTS`（「存在重复的功能名称。」）和 `THING_MODEL_IDENTIFIER_INVALID`（「产品物模型标识无效」）；
- `1_050_008_102` 同时是 `OTA_TASK_CREATE_FAIL_DEVICE_FIRMWARE_EXISTS`（设备已是该固件版本）和 `OTA_TASK_CREATE_FAIL_DEVICE_OTA_IN_PROCESS`（设备升级中）。

**原因**: `yudao-module-iot-biz` 的 `enums/ErrorCodeConstants.java` 中上述常量字面量重复（同 int 值不同消息）。iot 的错误码分两段：biz 用 `1_050_000_000` 段，`yudao-module-iot-gateway` 独立进程用 `1_051_000_000` 段，且存在同名不同码的情况（biz `DEVICE_NOT_EXISTS` = 1_050_003_000，gateway `DEVICE_NOT_EXISTS` = 1_051_002_001）。gateway 的注释段还标着「设备认证 1_050_001_000」，与实际 1_051 段不一致，按注释对码会出错。

**解决**: 新增错误码前先在 biz 与 gateway 两个 `ErrorCodeConstants` 里搜索确认不重复；跨进程判断设备类错误时不要假设码值相同，按各进程实际常量对齐；使用 `1_050_002_003` / `1_050_008_102` 做自动化判断的代码应改为按异常消息或重构后的错误码区分。

## 8. 设备影子

### 8.1 影子「查得到」不代表「已启用」；读接口允许 60 秒旧值

**问题**: 设备影子开关是停用状态，管理端 `GET /iot/device/shadow/get` 仍能正常返回影子；刚更新期望状态后，另一个请求短时间内可能读到旧值；对停用设备调用 `update-desired` 却报「设备影子未启用」；调用 reset 后查询记录还在。

**原因**: `IotDeviceShadowServiceImpl#getOrCreateShadow` 先读 Redis（`iot:device_shadow:{deviceId}`，TTL 60s，源码注释「仅用于展示，允许在缓存过期前读到旧影子」），未命中才读 DB；DB 无记录时**懒创建**，默认 `status=ENABLE`。只有 `updateDesiredState` 会读 DB 校验开关，停用时抛 `DEVICE_SHADOW_NOT_ENABLED`（1_050_007_100）；`get` 不会因停用而报错。`resetShadow`/`resetDeviceShadow0` 清空 desired、reported、metadata 并把 version 归 0，**不删除记录**。

**解决**: 不要用 `get` 是否成功判断影子是否启用，开关状态以 `status` 字段为准；写操作后缓存会被主动删除，读到的旧值只可能出现在缓存未被清理的窗口（最多 60s），排障时先看 Redis key。reset 是「清空状态、版本归零」，不是删除；需要彻底移除请删设备（`deleteByDeviceId`）。

### 8.2 设备上报的 version=-1 是「清空」语义；属性数上限 128，乐观锁冲突重试 3 次

**问题**: 设备想清空影子却上报 `version=-1`，结果被当作版本不匹配；期望状态一次提交超过 128 个属性报 `DEVICE_SHADOW_PROPERTY_COUNT_EXCEEDED`；并发更新偶发 `DEVICE_SHADOW_VERSION_CONFLICT`。

**原因**: `handleReportedUpdate` 先判断 `Objects.equals(reqDTO.getVersion(), -1L)`，为 -1 时直接清空影子并回复 version=0，不读取 state；否则按 `expectVersion` 合并 reported。desired/reported **各自**上限 128（`MAX_PROPERTY_COUNT`），合并后超限抛 1_050_007_102。`updateDeviceShadowState` 采用「读最新 → 合并 → 按 version 条件更新」的乐观锁，冲突后重试，最多 3 次（`OPTIMISTIC_LOCK_RETRY`），仍失败抛 1_050_007_101。管理端 `update-desired` 的 `expectVersion` 传 null（不校验版本），设备上报则按携带版本校验。

**解决**: 设备端清空影子用 `version=-1`；批量设置期望状态时分批，避免单次超过 128 个属性；出现版本冲突属于并发更新的正常结果，重试或重新读取最新影子即可，不要把它当成数据损坏。

## 9. 数据解析脚本

### 9.1 脚本不是安全沙箱；网关默认关闭，需同时打开两级开关

**问题**: 产品上已配置并启用了脚本，但网关收到设备报文仍按标准 JSON 解析；脚本里能访问到宿主对象/执行耗时操作；脚本保存后行为与调试结果不一致。

**原因**: 脚本由 Rhino 执行，`IotRhinoScriptExecutor` 只做时间预算（`execBudget` 默认 500ms）、指令上限（`maxInstructions` 默认 100 万）、截止时间（`deadline` 默认 2000ms）与超时熔断，**没有做类访问隔离，不是安全沙箱**。网关侧 `yudao.iot.gateway.script.enabled` **默认 false**，关闭时整体绕开脚本（不执行、不预热，raw 上行纯透传）；产品的 `scriptEnabled` 决定是否把脚本随设备信息下发给网关（管理后台详情接口始终返回 `scriptContent`），二者必须同时满足。`PUT /iot/product/update-script` **只编译不执行**（编译限时 2000ms），`POST /iot/product/debug-script` 使用固定 `debug-device` 上下文、请求线程同步等待最长 2000ms，调试通过不代表真实设备上下文（如真实 serverId、属性缓存）完全一致。

**解决**: 只运行可信人员编写的脚本；生产开启脚本需同时配置 `yudao.iot.gateway.script.enabled=true` 与产品 `scriptEnabled=true`。脚本 UTF-8 不超过 32KB，启用时内容不能为空；每设备最多排队 256 条下行脚本指令（`maxPendingCommandsPerDevice`），超出会丢弃并记日志，大量下行时应调大或限流。保存时的语法校验与网关执行共用 `IotScriptUtils` 的输出校验规则，但仍建议上线前用真实报文在测试设备验证。

## 10. 原始字节透传（raw）

### 10.1 raw.post 只能由网关产生；raw.push 需要额外权限且并非所有协议都支持

**问题**: 管理端调用 `/iot/device/message/send` 发送 `thing.raw.post` 被拒绝；有消息发送权限但透传下发仍报无权限；对 HTTP/CoAP 设备下发 raw 报「协议不支持透传下发」；Base64 字符串稍不规范就报载荷不合法。

**原因**: `validateRawMessage` 明确拒绝 `RAW_POST`（1_050_003_402，透传上报只能由网关创建）；`thing.raw.push` 在 `IotDeviceMessageController` 额外校验 `iot:device:message-raw-send`，不满足时抛全局 `FORBIDDEN`（403），仅有 `iot:device:message-send` 不够。HTTP、CoAP 无长连接，服务端直接抛 1_050_003_401。载荷必须是**标准 Base64（带 padding）**，解码后 1~4096 字节；Modbus 协议另按请求 PDU 校验（5~253 字节、功能码白名单、数量/byteCount 规则）。raw 消息不会自动回复。

**解决**: 透传上报只能由网关的 raw 入口产生；管理端模拟下发使用 `thing.raw.push` 并给操作人授予 `iot:device:message-raw-send`。下发前按产品协议校验字节，Modbus 必须是合法请求 PDU；HTTP/CoAP 设备改用标准物模型指令。排查「透传没反应」时先确认设备在线且有 serverId，再确认协议与字节格式。

## 11. 数据流转目的

### 11.1 Database 目的表名双重校验，create_time 使用外部库时间；HTTP 目的有 3s/5s 超时

**问题**: 数据目的配置了合法表名，运行一段时间后报「目标表名格式不正确」；Oracle/SQL Server 写入报 `NOW()` 语法错误；HTTP 目的偶发超时，同时设备状态更新也变慢。

**原因**: `IotDataSinkDatabaseConfig.TABLE_NAME_REGEX` 要求字母/下划线开头，只允许字母、数字、下划线，可选 `schema.table`；保存时 `@Pattern` 校验，**执行时 `IotDatabaseDataRuleAction` 会再次校验**（防历史非法配置拼接 SQL）。固定写入列 `id、device_id、tenant_id、method、report_time、data、create_time`，`create_time` 按 JDBC `DatabaseMetaData#getDatabaseProductName` 选择：Oracle、Microsoft SQL Server 用 `CURRENT_TIMESTAMP`，其它用 `NOW()`。HTTP 目的使用私有 RestTemplate，连接超时 3s、读取超时 5s；数据流转在设备状态事务内执行，HTTP 慢会延长设备行锁与数据库连接的持有时间。

**解决**: 目标表名只用 `[A-Za-z_][A-Za-z0-9_]{0,127}`（可带一段 schema），不要使用引号、空格或保留字；目标表需预先建好且包含上述固定列。Oracle/SQL Server 场景不要依赖 `NOW()`。HTTP 目的指向响应快的内网服务，避免在状态消息链路上调用慢接口；超时是保护，不是可调优的吞吐参数。

## 12. 网关进程与设备保活

### 12.1 网关 `-exec.jar` 才能独立运行；合并部署不要重复启动协议实例

**问题**: 直接用 `yudao-module-iot-gateway` 的主 artifact 执行 `java -jar` 起不来（没有主清单）；biz 引入 gateway 合并部署后，又单独启动网关进程，出现端口冲突或同一设备被两个实例接入；网关宕机后设备长时间仍显示在线。

**原因**: gateway 的 `spring-boot-maven-plugin` 使用 `exec` classifier，主 artifact 保留为普通 jar 供 biz 依赖，只有 `-exec.jar` 是可执行 jar（见 `pom.xml` 注释「普通 jar 供 biz 引入，-exec.jar 独立运行」）。合并部署时 biz 选择性引入 gateway 依赖，消息总线需配为 local，二者共享同一进程；若再启动独立网关，会重复创建协议实例。保活方面，网关每 20 秒（`IotProtocolManager.ALIVE_INTERVAL_SECONDS`）调用 `IotDeviceCommonApi#keepAliveGatewayServers`，biz 写入 `iot:gateway_server:{serverId}`，TTL 120 秒；离线 Job 对连接型设备检查该标记，EMQX 设备豁免（连接由 EMQX 维护），Redis 读取失败时本轮跳过。子设备、产品不存在或协议未知按活跃型处理。

**解决**: 独立部署使用 `-exec.jar`；合并部署时只启动一个进程，并把消息总线配置为 local。网关停止/宕机后，存活标记最多 120 秒过期，下一次离线 Job 才会把连接型设备判离线，这是预期延迟；不要用网关进程的启动时间推断设备在线。

## 13. Modbus 点位

### 13.1 bitIndex 只适用于 FC03/04 + BOOLEAN + 单寄存器；轮询间隔有服务端与网关双重下限

**问题**: 给 INT16 点位配置 bitIndex 报错；把 bitIndex 清空后旧值仍在；把 pollInterval 设为 50ms 被校验拒绝；网关侧实际轮询仍明显慢于配置。

**原因**: `IotDeviceModbusPointSaveReqVO#bitIndex` 限 0~15，服务层 `validateBitIndex` 要求功能码必须是 `READ_HOLDING_REGISTERS`(03) 或 `READ_INPUT_REGISTERS`(04)、原始数据类型 `BOOLEAN`、`registerCount=1`，否则抛 1_050_007_002。更新时 `IotDeviceModbusPointMapper#updateForSave` 对 bitIndex 为空会**显式写 NULL** 以支持清空。`pollInterval` 服务端 `@Min(100)`；网关协议实例配置项 `yudao.iot.gateway.protocols[].modbus-tcp-server.min-request-interval`（`IotModbusTcpServerConfig`）默认 1000ms，约束同一设备的最小请求间隔（≤0 才不限制）。位点位的写操作是「先 FC03 读 1 个寄存器，再 FC06 写回」，只改目标位。

**解决**: 位点位只用于「单寄存器里取一位」的 BOOLEAN 量，整寄存器点位不要填 bitIndex；清空 bitIndex 提交 null 即可。轮询间隔不要低于 100ms，且要 ≥ 网关 `min-request-interval`，否则实际生效的是较大值。并发写同一寄存器不同位存在读改写竞争，尽量由单一入口写入。
