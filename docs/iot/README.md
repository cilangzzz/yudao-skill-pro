# IoT 物联网平台模块 (iot)

> IoT 模块是整个系统的设备接入和管理中心，提供设备管理、产品管理、协议适配、规则引擎、OTA 升级、数据处理等完整的物联网平台能力。

## 模块概述

- **模块路径**: yudao-module-iot
- **业务定位**: 物联网平台核心模块，负责设备接入、设备管理、数据采集、规则引擎和 OTA 升级
- **核心职责**: 设备注册与认证、产品与物模型定义、多协议适配、场景联动、固件升级、设备消息处理

## 核心功能点

| 功能 | 说明 | 关键实体 |
|-----|------|---------|
| 设备管理 | 设备注册、认证、状态管理、分组管理、动态注册 | IotDeviceDO, IotDeviceGroupDO |
| 产品管理 | 产品定义、分类管理、协议与序列化配置 | IotProductDO, IotProductCategoryDO |
| 物模型管理 | 定义设备属性、事件、服务，实现标准化数据交互 | IotThingModelDO |
| 协议适配 | 支持 MQTT、CoAP、HTTP、TCP、UDP、WebSocket、Modbus、EMQX 等协议 | IotProtocol 接口实现 |
| 规则引擎 | 场景联动触发器-条件-动作模型，数据流转目的地配置 | IotSceneRuleDO, IotDataSinkDO |
| 告警管理 | 告警配置、告警记录、多用户通知 | IotAlertConfigDO, IotAlertRecordDO |
| OTA 升级 | 固件管理、升级任务、升级记录、分批升级 | IotOtaFirmwareDO, IotOtaTaskDO |
| 设备消息 | 设备上行/下行消息处理、消息记录存储（TDengine） | IotDeviceMessageDO |
| 设备属性 | 设备属性实时存储（Redis）、属性上报与查询 | IotDevicePropertyDO |

## 模块分层架构

```
yudao-module-iot
├── yudao-module-iot-core       # 核心层：公共模型、枚举、工具类、MQ 消息定义
├── yudao-module-iot-gateway    # 网关层：协议实现、上下行消息处理
└── yudao-module-iot-biz        # 业务层：设备/产品/规则/OTA 等核心业务逻辑
```

## API 接口索引

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/device/create` | POST | 创建设备 | iot:device:create |
| `/iot/device/update` | PUT | 更新设备 | iot:device:update |
| `/iot/device/delete` | DELETE | 删除设备 | iot:device:delete |
| `/iot/device/page` | GET | 设备分页查询 | iot:device:query |
| `/iot/device/get` | GET | 获取设备详情 | iot:device:query |
| `/iot/product/create` | POST | 创建产品 | iot:product:create |
| `/iot/product/update` | PUT | 更新产品 | iot:product:update |
| `/iot/product/delete` | DELETE | 删除产品 | iot:product:delete |
| `/iot/product/page` | GET | 产品分页查询 | iot:product:query |
| `/iot/thing-model/create` | POST | 创建物模型功能 | iot:thing-model:create |
| `/iot/thing-model/update` | PUT | 更新物模型功能 | iot:thing-model:update |
| `/iot/thing-model/delete` | DELETE | 删除物模型功能 | iot:thing-model:delete |
| `/iot/thing-model/list` | GET | 物模型功能列表 | iot:thing-model:query |
| `/iot/scene-rule/create` | POST | 创建场景联动规则 | iot:scene-rule:create |
| `/iot/scene-rule/update` | PUT | 更新场景联动规则 | iot:scene-rule:update |
| `/iot/scene-rule/delete` | DELETE | 删除场景联动规则 | iot:scene-rule:delete |
| `/iot/scene-rule/page` | GET | 场景联动规则分页 | iot:scene-rule:query |
| `/iot/ota/firmware/create` | POST | 创建固件 | iot:ota-firmware:create |
| `/iot/ota/firmware/page` | GET | 固件分页查询 | iot:ota-firmware:query |
| `/iot/ota/task/create` | POST | 创建升级任务 | iot:ota-task:create |
| `/iot/ota/task/page` | GET | 升级任务分页查询 | iot:ota-task:query |
| `/iot/alert/config/create` | POST | 创建告警配置 | iot:alert-config:create |
| `/iot/alert/config/page` | GET | 告警配置分页查询 | iot:alert-config:query |
| `/iot/data-sink/create` | POST | 创建数据流转目的地 | iot:data-sink:create |
| `/iot/data-sink/page` | GET | 数据流转目的地分页 | iot:data-sink:query |

> 详细接口文档按业务域拆分，见下方"详细文档"章节。

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| iot_device | 设备表 | TenantBaseDO | device_name, product_id, product_key, state, device_secret |
| iot_device_group | 设备分组表 | BaseDO | name, status, description |
| iot_device_message | 设备消息表（TDengine） | BaseDO | device_id, product_key, method, payload |
| iot_product | 产品表 | TenantBaseDO | name, product_key, product_secret, device_type, protocol_type |
| iot_product_category | 产品分类表 | TenantBaseDO | name, parent_id, sort |
| iot_thing_model | 物模型功能表 | BaseDO | product_id, identifier, type, property(JSON), event(JSON), service(JSON) |
| iot_scene_rule | 场景联动规则表 | TenantBaseDO | name, status, triggers(JSON), actions(JSON) |
| iot_data_sink | 数据流转目的地表 | TenantBaseDO | name, type, config(JSON) |
| iot_alert_config | 告警配置表 | BaseDO | name, level, status, scene_rule_ids, receive_user_ids |
| iot_ota_firmware | OTA 固件表 | BaseDO | name, version, product_id, file_url, file_size |
| iot_ota_task | OTA 升级任务表 | TenantBaseDO | name, firmware_id, product_id, status |
| iot_ota_task_record | OTA 升级记录表 | BaseDO | task_id, device_id, status |

> 完整字段定义见 [data-model.md](data-model.md)。

## 设计模式

| 模式 | 位置 | 用途 |
|-----|------|------|
| 策略模式 / 适配器模式 | `IotProtocol.java` | 定义协议接口，不同协议实现统一接口，支持灵活扩展新协议 |
| 模板方法模式 | `AbstractIotProtocolDownstreamSubscriber.java` | 抽象下行消息订阅者，子类实现具体的消息处理逻辑 |
| 观察者模式 | `service/rule/scene/` | 场景规则引擎，设备状态变化触发规则执行 |
| 责任链模式 | `service/rule/scene/matcher/` | 规则匹配器链，依次判断触发条件、执行条件是否满足 |
| 工厂模式 | `IotMessageSerializerManager.java` | 消息序列化器工厂，根据序列化类型获取对应的序列化器 |

## 依赖关系

### 内部依赖

| 模块 | API | 用途 |
|-----|-----|------|
| yudao-module-system | AdminUserApi | 获取告警接收用户信息 |

### 外部依赖

| 库 | 版本 | 用途 |
|---|------|------|
| vertx-mqtt | 4.x | MQTT 服务器实现 |
| californium | 3.x | CoAP 服务器实现 |
| jmodbus | 1.x | Modbus 协议实现 |
| netty | 4.x | TCP/UDP/WebSocket 网络框架 |
| tdengine-jdbc | 3.x | TDengine 时序数据库驱动 |

## 模块间通信

| 接口 | 方法 | 说明 | 调用方 |
|-----|------|------|-------|
| IotDeviceCommonApi | authDevice() | 设备认证 | gateway 网关层 |
| IotDeviceCommonApi | getDevice() | 获取设备信息 | gateway 网关层 |
| IotDeviceCommonApi | registerDevice() | 设备动态注册 | gateway 网关层 |
| IotDeviceCommonApi | registerSubDevices() | 子设备动态注册 | gateway 网关层 |
| IotDeviceCommonApi | getModbusDeviceConfigList() | 获取 Modbus 设备配置 | gateway 网关层 |
| IotMessageBus | device:message:upstream | 设备上行消息 | gateway -> biz |
| IotMessageBus | device:message:downstream | 设备下行消息 | biz -> gateway |

## 详细文档

- [api-device.md](api-device.md) - 设备管理接口
- [api-product.md](api-product.md) - 产品管理接口
- [api-thingmodel.md](api-thingmodel.md) - 物模型管理接口
- [api-rule.md](api-rule.md) - 规则引擎与数据流转接口
- [api-ota.md](api-ota.md) - OTA 升级管理接口
- [api-alert.md](api-alert.md) - 告警管理接口
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与常见问题
