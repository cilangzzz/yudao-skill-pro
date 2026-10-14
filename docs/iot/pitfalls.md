# 注意事项与已知坑点

> 使用 iot 模块时的常见问题、易踩坑点和最佳实践。

iot 模块为多子模块布局：`yudao-module-iot-biz`（管理端业务，打包进 yudao-server）、`yudao-module-iot-core`（biz 与 gateway 共享的消息总线/DTO）、`yudao-module-iot-gateway`（设备接入网关，独立 Spring Boot 进程）。属性数据与消息日志存 TDengine（超级表 + 按产品建子表），业务数据存 MySQL，两类存储的事务与租户行为差异是多数坑点的根源。

## 1. 多租户相关

### 1.1 「忽略租户」注解有两处硬约定：跨租户缓存与 TDengine Mapper

**问题**: 新增查询方法时漏写 `@TenantIgnore`，设备/产品相关查询在网关或 MQ 链路下查不到数据（返回 null 或空列表）；反之，给普通管理端查询误加 `@TenantIgnore` 会造成跨租户数据泄露。给新的 TDengine Mapper 忘加 `@InterceptorIgnore` 则直接启动或执行报错。

**原因**:
- 设备、产品、物模型是 `TenantBaseDO` 表，但缓存被刻意设计为**跨租户共享**：`IotDeviceServiceImpl#getDeviceFromCache`（两个重载）、`IotProductServiceImpl#getProductFromCache`、`IotThingModelServiceImpl#getThingModelListByProductIdFromCache` 都是 `@Cacheable` + `@TenantIgnore` 组合，RedisKeyConstants 中对应 key 注释明确写了「使用 Spring Cache 操作（忽略租户）」。跨租户安全依赖「productKey + deviceName / productId 全局唯一」这一前提，而不是缓存 key 隔离。
- TDengine 的 SQL（`IotDevicePropertyMapper`、`IotDeviceMessageMapper`）必须加 `@InterceptorIgnore(tenantLine = "true")`，源码注释写明原因：「JSqlParser 对 TDengine 的 SQL 解析会报错」。少了它租户拦截器会尝试改写 TDengine SQL 直接失败。

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

### 3.1 产品发布跨 MySQL 与 TDengine，@DSTransactional 无法回滚 TDengine DDL

**问题**: 产品发布（或手动同步表结构）时 TDengine 超级表结构变更失败，MySQL 里产品状态却可能已变成「已发布」；或反过来，发布成功但 TDengine 里缺少某属性列，设备上报该属性被丢弃。

**原因**: `IotProductServiceImpl#updateProductStatus` 标注的是 dynamic-datasource 的 `@DSTransactional`（非 Spring `@Transactional`），方法内先 `devicePropertyDataService.defineDevicePropertyData(id)` 建/改 TDengine 超级表，再更新 MySQL 产品状态。TDengine 的 `CREATE/ALTER TABLE` 是 DDL，没有事务回滚能力，`@DSTransactional` 只能提供有限的多数据源一致性。设备消息超级表则由 `TDengineTableInitRunner`（ApplicationRunner）在启动时通过 `defineDeviceMessageStable()` 创建。

**解决**: 发布失败后用「产品详情 → 同步表结构」（`IotProductService#syncProductPropertyTable`）重新执行 `defineDevicePropertyData`；对一致性要求高的场景，先同步表结构成功后再更新产品状态，失败时中断发布。

### 3.2 设备导入是「部分成功」语义，且旧设备匹配只按 deviceName

**问题**: Excel 批量导入设备时，部分行失败是正常的（记录在 `failureDeviceNames`），但有两个意外：① 某行抛出非 `ServiceException` 的异常（如 NPE）时，**整批已成功的导入全部回滚**，前端却拿到的是逐行结果；② Excel 里 deviceName 与**其他产品**下已有设备同名时，不会新建，而是错误地更新了那个产品下的设备（或报「设备标识已经存在」）。

**原因**: `IotDeviceServiceImpl#importDevice` 标注 `@Transactional(rollbackFor = Exception.class)`，循环内 `catch (ServiceException)` 继续处理下一行（此时不会回滚，之前已插入的设备随事务提交），其他异常则整体回滚。而存在性判断用的是 `deviceMapper.selectByDeviceName(importDevice.getDeviceName())`——`IotDeviceMapper#selectByDeviceName` 只按 deviceName 查询、不带 productKey；设备名唯一性约束实际是「同一 productKey 下唯一」（`validateCreateDeviceParam` 用的是 `selectByProductKeyAndDeviceName`），跨产品同名合法。

**解决**: 导入前确认 Excel 内设备名跨产品无重名；期望「失败行不影响成功行」时，不要依赖该方法处理会抛非 ServiceException 异常的脏数据。若要修代码，应把导入的存在性判断改为按 `productKey + deviceName` 查询。

## 4. TDengine 相关

### 4.1 属性列类型变更按「先删列再加列」执行，历史数据丢失；查询兜底依赖异常文本

**问题**: 修改物模型属性的数据类型（或把 text 长度改小）后，该属性的历史曲线全部变空；另外设备消息/历史属性页面在某些环境下「看起来没数据」其实是查询异常被吞了。

**原因**: `IotDevicePropertyMapper#alterProductPropertySTable`（default 方法）对类型变更的字段执行 `alterProductPropertySTableDropField` + `alterProductPropertySTableAddField`——TDengine 不支持直接改列类型，删列即删历史；注释明确「TDengine 长度修改时，只允许变长」，长度缩小也会被当成类型变更走删加流程。同时，`IotDeviceMessageServiceImpl#getDeviceMessagePage`、`IotDevicePropertyServiceImpl#getHistoryDevicePropertyList`、`defineDevicePropertyData` 都靠 `exception.getMessage().contains("Table does not exist")` 判断表不存在并返回空，TDengine 未启动/超级表未初始化时页面静默为空，不报错。

**解决**: 物模型属性的数据类型在产品发布前定好，发布后尽量不改类型（新增属性、加长 text 是安全的）；改了类型要接受历史数据清零。排查「无数据」问题时先确认 TDengine 可用、`TDengineTableInitRunner` 启动日志正常，再查业务，不要被空页面误导。

## 5. 消息总线与异步

### 5.1 本地消息总线同步分发且仅适用单机；RocketMQ 链路无顺序保障，下行依赖 Redis serverId

**问题**: 单机 local 模式下，设备消息处理慢会拖住发布方线程（如网关接入线程）；集群/大流量场景切 RocketMQ 后，设备上下线状态偶发「后发先至」，最终状态与实际相反。向 HTTP 等短连接设备下发消息时报「设备未连接网关」（`DEVICE_DOWNSTREAM_FAILED_SERVER_ID_NULL`）。

**原因**: `IotLocalMessageBus#post` 用 `applicationContext.publishEvent` 同步分发（类注释：「仅适用于单机场景！！！」），订阅者（`IotDeviceMessageSubscriber` 等 3 个）在发布线程内依次执行。`IotRocketMQMessageBus#post` 源码留有 `// TODO @芋艿：需要 orderly！`，消费用 `MessageListenerConcurrently` 并发消费，STATE_UPDATE 等状态消息可能乱序；下行消息路由靠 `IotDevicePropertyServiceImpl#getDeviceServerId` 读 Redis（`iot:device_server_id`），设备未上报过 serverId 或 Redis 数据丢失时抛 `DEVICE_DOWNSTREAM_FAILED_SERVER_ID_NULL`（`IotDeviceMessageServiceImpl#sendDeviceMessage`）。下行 PUSH/PULL 模型也仅有 TODO 注释（「下行消息需要区分 PUSH 和 PULL 模型」），短连接设备目前无拉取通道。

**解决**: 生产集群环境必须配置 RocketMQ 消息总线；对设备状态强一致的场景，消费端以消息时间戳或设备实际心跳做兜底判断（`IotDeviceOfflineCheckJob` 按 `iot:device_report_times` ZSet 判定离线）。下行失败先检查该设备是否有上行记录（serverId 是否已写入 Redis）。

### 5.2 @Async 写消息日志失败被静默吞掉

**问题**: 设备消息日志（TDengine `iot_device_message`）偶发缺条，接口无任何报错，只能翻日志发现。

**原因**: `IotDeviceMessageServiceImpl#createDeviceLogAsync` 是 `@Async` 方法，内部 try/catch 后仅 `log.error`（源码注释：「@Async 方法的异常默认会被 handler 吞掉，这里显式记录便于排查」）。注意它是**包私有**方法，靠 `getSelf()` 调用才走代理异步执行；若改成直接 `this.createDeviceLogAsync(...)` 会退化为同步执行且注解失效。同理 `IotDevicePropertyServiceImpl#updateDeviceReportTimeAsync` 也是 `@Async`（只写 Redis，失败影响较小）。另一个隐患：`@Async` 线程不继承 `TenantContextHolder`，这两个方法恰好只按 deviceId 操作 TDengine/Redis 才安全，新加的 @Async 方法若查 MySQL 租户表会踩 1.2 的坑。

**解决**: 排查消息日志缺失时直接搜 `[createDeviceLogAsync]` 错误日志；TDengine 不可用时消息日志会持续丢失但不影响主流程。新写 @Async 方法须自带 try/catch + 显式日志，且不要在里面依赖租户上下文。

## 6. 并发与状态机

### 6.1 OTA 升级：创建任务无并发防护，多条进行中记录时固定取第一条

**问题**: 对同一设备并发创建两个升级任务都能成功，设备出现两条「进行中」记录；此后设备上报升级进度可能记到**另一个任务**的记录上，任务统计（成功/失败数）失真。

**原因**: `IotOtaTaskServiceImpl#createOtaTask` 在事务内「查进行中记录 → 校验 → 插入」，是典型的 check-then-act，无锁、`iot_ota_task_record` 也无设备维度的唯一约束，并发下双重通过校验。而 `IotOtaTaskRecordServiceImpl#updateOtaRecordProgress` 处理进度时对 `records.size() > 1` 只 `log.warn`，然后 `CollUtil.getFirst(records)` 取第一条更新。另外 `IotOtaUpgradeJob` 源码自注两个 TODO：逐条查询存在 N+1、离线设备直接跳过推送（「当前逻辑跳过了离线的设备，但未充分利用 MQTT 的离线消息能力」），设备离线期间的 PENDING 记录只能等下次在线后被推送。

**解决**: 创建任务集中在管理端串行操作可规避；若开放 API，建议给进行中记录加「设备维度唯一」校验（数据库唯一索引或分布式锁）。发现某设备有多条进行中记录时，以 `updateOtaRecordProgress` 的 warn 日志定位并手工取消多余记录。

### 6.2 从缓存获取设备后未判空的 NPE 风险

**问题**: 设备删除后，MQ 里残留消息、网关侧子设备注册请求仍会到达，规则引擎/注册链路抛 NullPointerException，消息消费失败。

**原因**: 两个已存在的调用点没有判空，而 `getDeviceFromCache` 带 `unless = "#result == null"`，设备不存在时就是返回 null：
- `IotSceneRuleServiceImpl#executeSceneRuleByDevice`：`deviceService.getDeviceFromCache(message.getDeviceId())` 后直接 `device.getTenantId()`；
- `IotDeviceServiceImpl#registerSubDevices`：按 productKey + deviceName 取网关设备后直接 `gatewayDevice.getTenantId()`。

对比 `IotDeviceMessageSubscriber` 用的是 `validateDeviceExistsFromCache`（null 时抛 `DEVICE_NOT_EXISTS`），这两处是遗漏。另外规则触发器匹配方法 `getSceneRuleListByProductIdAndDeviceIdFromCache` 的 for 循环内 `return`（首个 trigger 不匹配即返回），多触发器场景下只有第一个触发器参与设备匹配，排查「规则不触发」时注意。

**解决**: 调用 `getDeviceFromCache` 后统一判空（或改用 `validateDeviceExistsFromCache`）；复现这类 NPE 时先确认设备是否刚被删除、MQ 是否有积压。

## 7. 错误码相关

### 7.1 错误码重复定义与 biz/gateway 双段编码

**问题**: 前端/调用方按错误码做分支处理时行为错乱：提示语与实际原因对不上。两处已知重复：
- `1_050_002_003` 同时是 `THING_MODEL_NAME_EXISTS`（「存在重复的功能名称。」）和 `THING_MODEL_IDENTIFIER_INVALID`（「产品物模型标识无效」）；
- `1_050_008_102` 同时是 `OTA_TASK_CREATE_FAIL_DEVICE_FIRMWARE_EXISTS`（设备已是该固件版本）和 `OTA_TASK_CREATE_FAIL_DEVICE_OTA_IN_PROCESS`（设备升级中）。

**原因**: `yudao-module-iot-biz` 的 `enums/ErrorCodeConstants.java` 中上述常量字面量重复（同 int 值不同消息）。iot 的错误码分两段：biz 用 `1_050_000_000` 段，`yudao-module-iot-gateway` 独立进程用 `1_051_000_000` 段，且存在同名不同码的情况（biz `DEVICE_NOT_EXISTS` = 1_050_003_000，gateway `DEVICE_NOT_EXISTS` = 1_051_002_001）。gateway 的注释段还标着「设备认证 1-050-001-000」，与实际 1_051 段不一致，按注释对码会出错。

**解决**: 新增错误码前先在 biz 与 gateway 两个 `ErrorCodeConstants` 里搜索确认不重复；跨进程判断设备类错误时不要假设码值相同，按各进程实际常量对齐；使用 `1_050_002_003` / `1_050_008_102` 做自动化判断的代码应改为按异常消息或重构后的错误码区分。
