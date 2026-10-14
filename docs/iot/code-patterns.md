# IoT 物联网代码模式与扩展指南 (iot)

> 本文档移植自模块 Skill 知识库（skill-iot.yaml），提供该模块的代码模式、扩展指南与关键文件索引。模块总体概述、API 索引与依赖关系见 [README.md](README.md)。

## 代码模式

### Controller 层规范

管理后台 Controller 使用 Swagger v3（`@Tag` / `@Operation`）+ Spring Security 权限注解（`@PreAuthorize`），权限标识遵循 `iot:{功能}:{操作}` 格式，典型注解组合：

- `@Tag(name = "管理后台 - IoT 设备")`
- `@RestController`
- `@RequestMapping("/iot/device")`
- `@PreAuthorize("@ss.hasPermission('iot:device:create')")`

示例（`IotDeviceController`）：

```java
@Tag(name = "管理后台 - IoT 设备")
@RestController
@RequestMapping("/iot/device")
@Validated
public class IotDeviceController {
    @Resource
    private IotDeviceService deviceService;

    @PostMapping("/create")
    @Operation(summary = "创建设备")
    @PreAuthorize("@ss.hasPermission('iot:device:create')")
    public CommonResult<Long> createDevice(@Valid @RequestBody IotDeviceSaveReqVO createReqVO) {
        return success(deviceService.createDevice(createReqVO));
    }

    @GetMapping("/page")
    @Operation(summary = "获得设备分页")
    @PreAuthorize("@ss.hasPermission('iot:device:query')")
    public CommonResult<PageResult<IotDeviceRespVO>> getDevicePage(@Valid IotDevicePageReqVO pageReqVO) {
        PageResult<IotDeviceDO> pageResult = deviceService.getDevicePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, IotDeviceRespVO.class));
    }
}
```

### Service 层规范

Service 接口按「CRUD 操作 / 业务操作 / 缓存操作」三段组织方法，设备服务同时面向管理后台（VO）与网关进程（DTO）提供能力：

```java
public interface IotDeviceService {
    // CRUD 操作
    Long createDevice(@Valid IotDeviceSaveReqVO createReqVO);
    void updateDevice(@Valid IotDeviceSaveReqVO updateReqVO);
    void deleteDevice(Long id);
    IotDeviceDO getDevice(Long id);
    PageResult<IotDeviceDO> getDevicePage(IotDevicePageReqVO pageReqVO);

    // 业务操作
    boolean authDevice(@Valid IotDeviceAuthReqDTO authReqDTO);
    void updateDeviceState(Long id, Integer state);
    IotDeviceRegisterRespDTO registerDevice(@Valid IotDeviceRegisterReqDTO reqDTO);

    // 缓存操作
    IotDeviceDO getDeviceFromCache(Long id);
    IotDeviceDO getDeviceFromCache(String productKey, String deviceName);
}
```

实现类的写法要点：`@Service + @Validated`，写操作加 `@Transactional(rollbackFor = Exception.class)`，方法内按「校验 → 生成业务数据 → 落库」的编号步骤组织。创建设备时校验产品存在、生成设备密钥，并从产品冗余 `productKey`、`deviceType` 到设备记录：

```java
@Service
@Validated
public class IotDeviceServiceImpl implements IotDeviceService {
    @Resource
    private IotDeviceMapper deviceMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long createDevice(IotDeviceSaveReqVO createReqVO) {
        // 1. 校验产品存在
        IotProductDO product = productService.validateProductExists(createReqVO.getProductId());
        // 2. 生成设备密钥
        String deviceSecret = generateDeviceSecret();
        // 3. 插入设备
        IotDeviceDO device = BeanUtils.toBean(createReqVO, IotDeviceDO.class)
                .setProductKey(product.getProductKey())
                .setDeviceType(product.getDeviceType())
                .setDeviceSecret(deviceSecret)
                .setState(IotDeviceStateEnum.INACTIVE.getState());
        deviceMapper.insert(device);
        return device.getId();
    }
}
```

设备认证示例：优先从缓存取设备（网关高频调用），依次校验设备存在性与密钥，认证通过后更新设备状态为在线：

```java
// 设备认证示例
@Override
public boolean authDevice(IotDeviceAuthReqDTO authReqDTO) {
    // 1. 获取设备信息
    IotDeviceDO device = getDeviceFromCache(authReqDTO.getProductKey(), authReqDTO.getDeviceName());
    if (device == null) {
        return false;
    }
    // 2. 校验设备密钥
    if (!StrUtil.equals(device.getDeviceSecret(), authReqDTO.getDeviceSecret())) {
        return false;
    }
    // 3. 更新设备状态为在线
    updateDeviceState(device, IotDeviceStateEnum.ONLINE.getState());
    return true;
}
```

### 数据访问层（DAL）规范

Mapper 继承 `BaseMapperX`，分页查询用 `LambdaQueryWrapperX` 的 `xxxIfPresent` 系列方法拼接动态条件，固定按 `id` 倒序：

```java
@Mapper
public interface IotDeviceMapper extends BaseMapperX<IotDeviceDO> {
    default PageResult<IotDeviceDO> selectPage(IotDevicePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<IotDeviceDO>()
                .likeIfPresent(IotDeviceDO::getDeviceName, reqVO.getDeviceName())
                .eqIfPresent(IotDeviceDO::getProductId, reqVO.getProductId())
                .eqIfPresent(IotDeviceDO::getState, reqVO.getState())
                .orderByDesc(IotDeviceDO::getId));
    }
}
```

设备属性读写走 Redis DAO（属性最新值缓存），按 `productKey + deviceName + identifier` 组装 key 后写入属性值与更新时间：

```java
// 设备属性存储在 Redis 中
@Resource
private DevicePropertyRedisDAO devicePropertyRedisDAO;

public void updateDeviceProperty(String productKey, String deviceName, String identifier, Object value) {
    String key = formatDevicePropertyKey(productKey, deviceName, identifier);
    IotDevicePropertyDO property = IotDevicePropertyDO.builder()
            .value(value)
            .updateTime(LocalDateTime.now())
            .build();
    devicePropertyRedisDAO.set(key, property);
}
```

### 协议扩展模式

网关所有协议实现统一实现 `IotProtocol` 接口，接口定义协议实例 ID、服务器 ID、协议类型与生命周期：

```java
public interface IotProtocol {
    String getId();                    // 协议实例 ID
    String getServerId();              // 服务器 ID（消息追踪）
    IotProtocolTypeEnum getType();     // 协议类型
    void start();                      // 启动协议服务
    void stop();                       // 停止协议服务
    boolean isRunning();               // 检查运行状态
}
```

MQTT 协议实现示例：`start()` 中创建并监听服务器、置运行标记、启动下行消息订阅者；连接建立时先做设备认证，认证失败拒绝连接，成功后挂载消息处理器并接受连接：

```java
// MQTT 协议实现示例
public class IotMqttProtocol implements IotProtocol {
    private MqttServer mqttServer;
    private IotMqttConnectionManager connectionManager;

    @Override
    public void start() {
        // 1. 创建 MQTT 服务器
        mqttServer = MqttServer.create(vertx, options);
        mqttServer.endpointHandler(this::handleEndpoint);

        // 2. 启动服务器
        mqttServer.listen();
        running = true;

        // 3. 启动下行消息订阅者
        downstreamSubscriber.start();
    }

    private void handleEndpoint(MqttEndpoint endpoint) {
        // 1. 处理认证
        if (!authHandler.handleAuthenticationRequest(endpoint)) {
            endpoint.reject(MqttConnectReturnCode.CONNECTION_REFUSED_BAD_USER_NAME_OR_PASSWORD);
            return;
        }
        // 2. 设置消息处理器
        endpoint.publishHandler(message -> processMessage(endpoint, message));
        // 3. 接受连接
        endpoint.accept(false);
    }
}
```

### 异常处理与错误码

IoT 模块错误码使用 `1-011` 前缀，常用错误码：

| 错误码 | 说明 |
|-------|------|
| 1-011-000-000 | 设备不存在 |
| 1-011-000-001 | 设备认证失败 |
| 1-011-000-002 | 设备已存在 |
| 1-011-001-000 | 产品不存在 |
| 1-011-002-000 | 物模型不存在 |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`CommonResult.error(ErrorCodeConstants.DEVICE_NOT_EXISTS)`

## 扩展指南

### 新增协议类型

1. **添加协议类型枚举** — 文件：`yudao-module-iot-core/src/main/java/cn/iocoder/yudao/module/iot/core/enums/IotProtocolTypeEnum.java`
   在枚举中添加新的协议类型，如 `GOPHER("gopher")`。
2. **创建协议配置类** — 文件：`yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/{protocol}/Iot{Protocol}Config.java`
   定义协议特有的配置参数，如端口、超时时间、SSL 配置等。
3. **实现协议接口** — 文件：`yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/{protocol}/Iot{Protocol}Protocol.java`
   实现 `IotProtocol` 接口：
   - `start()`：启动协议服务，创建服务器/客户端
   - `stop()`：停止协议服务，释放资源
   - `handleUpstream()`：处理上行消息
   - `handleDownstream()`：处理下行消息
4. **实现上行消息处理器** — 文件：`yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/{protocol}/handler/upstream/Iot{Protocol}UpstreamHandler.java`
   处理设备上报的消息，解析后发送到消息总线。
5. **实现下行消息订阅者** — 文件：`yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/{protocol}/handler/downstream/Iot{Protocol}DownstreamSubscriber.java`
   订阅下行消息，下发给设备。
6. **注册协议到管理器** — 文件：`yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/IotProtocolManager.java`
   在配置中添加新协议的实例化逻辑。

### 新增设备类型

1. **添加设备类型枚举** — 文件：`yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/enums/product/IotProductDeviceTypeEnum.java`
   在枚举中添加新的设备类型。
2. **定义物模型** — 操作入口：管理后台配置
   为新产品定义物模型（属性、事件、服务）。
3. **配置协议** — 操作入口：产品管理页面
   设置产品使用的协议类型和序列化方式。

### 新增场景联动动作类型

1. **添加动作类型枚举** — 文件：`yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/enums/rule/IotSceneRuleActionTypeEnum.java`
   添加新的动作类型枚举值。
2. **实现动作执行器** — 文件：`yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/service/rule/scene/action/Iot{Action}SceneRuleAction.java`
   实现 `IotSceneRuleAction` 接口，定义动作执行逻辑。
3. **注册动作执行器** — 在 Spring 容器中注册为 Bean，自动被规则引擎发现和调用。

### 最佳实践

- 设备密钥安全性：设备密钥应使用强随机数生成，避免硬编码或简单规则
- 协议扩展：新协议应继承 `AbstractIotProtocolDownstreamSubscriber`，复用下行消息处理逻辑
- 消息存储：设备消息使用 TDengine 时序数据库存储，支持高效查询和聚合
- 设备缓存：频繁访问的设备信息使用 Redis 缓存，减少数据库压力
- 规则引擎：场景规则应设置合理的触发条件，避免频繁触发导致性能问题
- OTA 升级：大规模升级应分批进行，避免网络拥塞和服务器压力
- 租户隔离：所有设备操作都应考虑租户隔离，防止越权访问

## 模块依赖

内部依赖（其他业务模块）：

| 模块 | API | 用途 |
|-----|-----|------|
| yudao-module-system | AdminUserApi | 获取告警接收用户信息 |

外部依赖（第三方库）：

| 依赖 | 版本 | 用途 |
|-----|------|------|
| vertx-mqtt | 4.x | MQTT 服务器实现 |
| californium | 3.x | CoAP 服务器实现 |
| jmodbus | 1.x | Modbus 协议实现 |
| netty | 4.x | TCP/UDP/WebSocket 网络框架 |
| tdengine-jdbc | 3.x | TDengine 时序数据库驱动 |

> 完整依赖关系（framework starter、消息总线可选实现、下游 yudao-server / yudao-module-iot-gateway 的关系）见 [README.md](README.md) 的「依赖关系」一节。

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-iot/yudao-module-iot-core/src/main/java/cn/iocoder/yudao/module/iot/core/enums/IotProtocolTypeEnum.java | 协议类型枚举定义 |
| yudao-module-iot/yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/IotProtocol.java | 协议接口定义，所有协议必须实现此接口 |
| yudao-module-iot/yudao-module-iot-gateway/src/main/java/cn/iocoder/yudao/module/iot/gateway/protocol/mqtt/IotMqttProtocol.java | MQTT 协议实现，最常用的设备接入协议 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/service/device/IotDeviceService.java | 设备管理服务接口 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/service/device/message/IotDeviceMessageService.java | 设备消息服务接口 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/service/rule/scene/IotSceneRuleService.java | 场景联动规则服务 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/dal/dataobject/device/IotDeviceDO.java | 设备实体类定义 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/dal/dataobject/product/IotProductDO.java | 产品实体类定义 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/dal/dataobject/thingmodel/IotThingModelDO.java | 物模型实体类定义 |
| yudao-module-iot/yudao-module-iot-biz/src/main/java/cn/iocoder/yudao/module/iot/controller/admin/device/IotDeviceController.java | 设备管理 Controller |
| yudao-module-iot/yudao-module-iot-core/src/main/java/cn/iocoder/yudao/module/iot/core/biz/IotDeviceCommonApi.java | 设备通用 API 接口 |

## 领域模型

### 聚合根

| 聚合根 | 包含实体 | 说明 |
|-------|---------|------|
| 设备聚合 | IotDeviceDO、IotDeviceGroupDO、IotDevicePropertyDO、IotDeviceMessageDO | 设备是 IoT 平台的核心实体，包含设备基本信息、状态、属性、消息等 |
| 产品聚合 | IotProductDO、IotProductCategoryDO、IotThingModelDO | 产品是设备的模板，定义物模型（属性、事件、服务）和协议配置 |
| 规则引擎聚合 | IotSceneRuleDO、IotDataRuleDO、IotDataSinkDO、IotAlertConfigDO、IotAlertRecordDO | 规则引擎处理设备数据流转、场景联动、告警触发 |
| OTA 升级聚合 | IotOtaFirmwareDO、IotOtaTaskDO、IotOtaTaskRecordDO | OTA 升级管理固件版本、升级任务和升级记录 |

### 值对象

| 值对象 | 说明 |
|-------|------|
| ThingModelProperty | 物模型属性定义，包含数据类型、单位、范围等 |
| ThingModelEvent | 物模型事件定义，包含事件类型、参数等 |
| ThingModelService | 物模型服务定义，包含输入输出参数 |
| IotDeviceIdentity | 设备身份标识，包含 productKey、deviceName |

### 领域服务

| 领域服务 | 说明 |
|---------|------|
| IotDeviceService | 设备管理服务，处理设备 CRUD、认证、状态更新 |
| IotDeviceMessageService | 设备消息服务，处理消息收发、记录存储 |
| IotSceneRuleService | 场景联动服务，执行场景联动逻辑 |
| IotProtocol | 协议接口，定义协议生命周期（启动、停止、运行状态） |

## 设计与架构补充

以下为模块 Skill 知识库中未被 README.md 覆盖的补充内容。

### 产品-设备模板模型

产品定义设备模板（物模型、协议类型、序列化方式等），设备继承产品配置（如 `productKey`、`deviceType` 在创建设备时从产品冗余写入），并支持一型一密动态注册（由 `iot_product.register_enabled` 控制开关，见上文 `registerDevice` 业务操作）。

### 补充的设计模式

README「设计模式」一节已覆盖策略、模板方法、观察者/发布订阅等模式，此处补充其余两类：

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 责任链模式 | yudao-module-iot-biz 的 `service/rule/scene/matcher/` | 规则匹配器链，依次判断触发条件、执行条件是否满足 |
| 工厂模式 | yudao-module-iot-gateway 的 `serialize/IotMessageSerializerManager` | 消息序列化器工厂，根据序列化类型获取对应的序列化器 |

### 分层组件细节

三子模块（biz/core/gateway）的职责划分见 README「模块概述」，各层内部组件补充如下：

- **gateway 网关层**：协议实现按 `protocol/{协议}` 包组织（MQTT/CoAP/HTTP/TCP/UDP/WebSocket/Modbus TCP 客户端与服务端/EMQX 桥接）；上行消息处理器统一放在 `handler/upstream`，下行消息处理器统一放在 `handler/downstream`。
- **core 核心层**：`enums`（协议类型、设备状态、消息方法等枚举）、`mq/message`（设备消息模型）、`biz/dto`（业务 DTO）、`topic`（Topic 定义和工具）。

### 内部消息总线

gateway 与 biz 之间通过内部消息总线 IotMessageBus 传递设备消息，使用两类主题：

- `device:message:upstream` — 设备上行消息
- `device:message:downstream` — 设备下行消息

### 表关系（ER 关系）

| 表 | 关联表 | 关系 | 外键 | 说明 |
|---|-------|------|------|------|
| iot_device | iot_product | N:1 | product_id | 设备属于某个产品 |
| iot_device | iot_device | N:1 | gateway_id | 子设备关联网关设备 |
| iot_product | iot_product_category | N:1 | category_id | 产品属于某个分类 |
| iot_thing_model | iot_product | N:1 | product_id | 物模型属于某个产品 |
| iot_ota_firmware | iot_product | N:1 | product_id | 固件属于某个产品 |
| iot_ota_task | iot_ota_firmware | N:1 | firmware_id | 升级任务使用某个固件 |
