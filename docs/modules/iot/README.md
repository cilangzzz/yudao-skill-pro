# IoT 物联网模块 (iot)

> 提供设备接入、产品/物模型管理、消息上下行、OTA 升级、规则引擎与告警的一站式物联网平台，采用 biz/core/gateway 三子模块 + MySQL/TDengine 双存储架构。

## 模块概述

- **模块路径**: yudao-module-iot（多子模块布局）
  - `yudao-module-iot-biz`: 管理后台业务（Controller/Service/DAL），打包进 yudao-server
  - `yudao-module-iot-core`: biz 与 gateway 共享的消息总线、DTO、协议枚举
  - `yudao-module-iot-gateway`: 设备接入网关（独立 Spring Boot 进程），负责编解码与协议接入
- **业务定位**: 面向管理后台的 IoT 平台能力，覆盖产品与物模型（TSL）定义、设备全生命周期管理、设备消息上下行与日志存储、Modbus 采集配置、OTA 固件升级、场景联动/数据流转规则引擎、告警配置与记录、以及设备/消息数据统计。
- **技术栈**: Spring Boot 2.7.18（JDK8 分支，javax.* 风格）/ MyBatis-Plus / Swagger v3（springdoc）/ TDengine（taos-jdbcdriver 3.9.2，设备消息与属性时序存储）/ Redis（最新属性、serverId 缓存）/ Vert.x 4.5.26（网关 MQTT/TCP/UDP/WebSocket）/ Eclipse Californium 3.14.0（CoAP）/ j2mod 3.4.0（Modbus）/ Eclipse Paho MQTT / RocketMQ、Kafka、RabbitMQ（消息总线可选实现，optional 依赖）

## 设计原则

| 原则 | 说明 |
|-----|------|
| 三子模块分层 | biz（管理业务）与 gateway（协议网关）通过 core 提供的消息总线 + HTTP API 通信，可独立部署、互不耦合 |
| 双存储引擎 | MySQL 存业务数据；TDengine 存设备消息日志超级表 `iot_device_message` 与按产品（productKey）建属性超级表；Redis 缓存设备最新属性与网关 serverId |
| 消息总线驱动 | 设备消息经 core 的 messagebus（spring-event / redis stream / rocketmq / kafka / rabbitmq 可选）在 gateway 与 biz 间流转，上下行统一为 `IotDeviceMessage` |
| 物模型驱动 | TSL 定义属性/服务/事件，设备消息 method（Alink 风格如 `thing.property.post`）与物模型 identifier 对齐，属性表结构由物模型同步生成 |
| 多协议插件化网关 | 网关以 `IotProtocol` 接口 + `IotProtocolManager` 管理多协议实例（MQTT/EMQX/CoAP/HTTP/TCP/UDP/WebSocket/Modbus），按配置启停 |
| 规则引擎策略化 | 场景联动的触发器/条件/动作均为策略接口，由 MatcherManager/Action 注册分发，便于扩展新类型 |
| 多租户与权限 | 核心表（device/product/modbus/scene_rule）继承 TenantBaseDO 支持租户隔离，admin 接口以 `iot:xxx:yyy` 权限标识鉴权 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 产品管理 | 产品与产品分类 CRUD、ProductKey/动态注册、发布状态、属性表同步到 TDengine | IotProductDO、IotProductCategoryDO |
| 物模型 | 产品 TSL 属性/服务/事件定义，TSL 整体导出 | IotThingModelDO |
| 设备管理 | 设备 CRUD、Excel 导入导出、网关子设备拓扑绑定、设备分组、位置地图、连接信息 | IotDeviceDO、IotDeviceGroupDO |
| 设备通信 | 设备消息上下行/消息对分页/模拟发送，属性最新值与历史查询（TDengine） | IotDeviceMessageDO、IotDevicePropertyDO |
| Modbus 接入 | 设备 Modbus 连接配置（Client/Server 模式）与寄存器点位配置 | IotDeviceModbusConfigDO、IotDeviceModbusPointDO |
| OTA 升级 | 固件管理、升级任务（全量/指定设备）、升级记录与进度 | IotOtaFirmwareDO、IotOtaTaskDO、IotOtaTaskRecordDO |
| 规则引擎 | 场景联动（触发器/条件/动作）、数据流转规则与数据目的（9 种类型） | IotSceneRuleDO、IotDataRuleDO、IotDataSinkDO |
| 告警管理 | 告警配置（短信/邮件/站内信通知）、告警记录查询与处理 | IotAlertConfigDO、IotAlertRecordDO |
| 数据统计 | 产品/分类/设备/消息全局汇总、今日新增、设备状态分布、消息按日统计 | IotDeviceMessageDO |

## API 接口索引

### 告警管理 (IotAlertConfigController / IotAlertRecordController)

IotAlertConfigController — `@RequestMapping("/iot/alert-config")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/alert-config/create | POST | 创建告警配置 | iot:alert-config:create |
| /iot/alert-config/update | PUT | 更新告警配置 | iot:alert-config:update |
| /iot/alert-config/delete | DELETE | 删除告警配置 | iot:alert-config:delete |
| /iot/alert-config/get | GET | 获得告警配置 | iot:alert-config:query |
| /iot/alert-config/page | GET | 获得告警配置分页 | iot:alert-config:query |
| /iot/alert-config/simple-list | GET | 获得告警配置简单列表（仅开启项，下拉用） | iot:alert-config:query |

IotAlertRecordController — `@RequestMapping("/iot/alert-record")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/alert-record/get | GET | 获得告警记录 | iot:alert-record:query |
| /iot/alert-record/page | GET | 获得告警记录分页 | iot:alert-record:query |
| /iot/alert-record/process | PUT | 处理告警记录 | iot:alert-record:process |

### 设备管理 (IotDeviceController)

`@RequestMapping("/iot/device")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/device/create | POST | 创建设备 | iot:device:create |
| /iot/device/update | PUT | 更新设备 | iot:device:update |
| /iot/device/bind-gateway | PUT | 绑定子设备到网关 | iot:device:update |
| /iot/device/unbind-gateway | PUT | 解绑子设备与网关 | iot:device:update |
| /iot/device/sub-device-list | GET | 获取网关的子设备列表 | iot:device:query |
| /iot/device/unbound-sub-device-page | GET | 获取未绑定网关的子设备分页 | iot:device:query |
| /iot/device/update-group | PUT | 更新设备分组 | iot:device:update |
| /iot/device/delete | DELETE | 删除单个设备 | iot:device:delete |
| /iot/device/delete-list | DELETE | 删除多个设备 | iot:device:delete |
| /iot/device/get | GET | 获得设备 | iot:device:query |
| /iot/device/page | GET | 获得设备分页 | iot:device:query |
| /iot/device/export-excel | GET | 导出设备 Excel | iot:device:export |
| /iot/device/count | GET | 获得设备数量 | iot:device:query |
| /iot/device/simple-list | GET | 获取设备的精简信息列表（下拉用） | 已认证 |
| /iot/device/location-list | GET | 获取设备位置列表（地图展示） | iot:device:query |
| /iot/device/import | POST | 导入设备 | iot:device:import |
| /iot/device/get-import-template | GET | 获得导入设备模板 | 已认证 |
| /iot/device/get-auth-info | GET | 获得设备连接信息 | iot:device:auth-info |
| /iot/device/list-by-product-key-and-names | GET | 通过产品标识和设备名称列表获取设备 | iot:device:query |

### 设备分组 (IotDeviceGroupController)

`@RequestMapping("/iot/device-group")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/device-group/create | POST | 创建设备分组 | iot:device-group:create |
| /iot/device-group/update | PUT | 更新设备分组 | iot:device-group:update |
| /iot/device-group/delete | DELETE | 删除设备分组 | iot:device-group:delete |
| /iot/device-group/get | GET | 获得设备分组 | iot:device-group:query |
| /iot/device-group/page | GET | 获得设备分组分页 | iot:device-group:query |
| /iot/device-group/simple-list | GET | 获取设备分组的精简信息列表（下拉用） | 已认证 |

### 设备 Modbus 配置 (IotDeviceModbusConfigController / IotDeviceModbusPointController)

IotDeviceModbusConfigController — `@RequestMapping("/iot/device-modbus-config")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/device-modbus-config/save | POST | 保存设备 Modbus 连接配置 | iot:device:update |
| /iot/device-modbus-config/get | GET | 获得设备 Modbus 连接配置（按 id 或 deviceId） | iot:device:query |

IotDeviceModbusPointController — `@RequestMapping("/iot/device-modbus-point")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/device-modbus-point/create | POST | 创建设备 Modbus 点位配置 | iot:device:update |
| /iot/device-modbus-point/update | PUT | 更新设备 Modbus 点位配置 | iot:device:update |
| /iot/device-modbus-point/delete | DELETE | 删除设备 Modbus 点位配置 | iot:device:update |
| /iot/device-modbus-point/get | GET | 获得设备 Modbus 点位配置 | iot:device:query |
| /iot/device-modbus-point/page | GET | 获得设备 Modbus 点位配置分页 | iot:device:query |

### 设备属性 (IotDevicePropertyController)

`@RequestMapping("/iot/device/property")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/device/property/get-latest | GET | 获取设备属性最新属性 | iot:device:property-query |
| /iot/device/property/history-list | GET | 获取设备属性历史数据列表 | iot:device:property-query |

### 设备消息 (IotDeviceMessageController)

`@RequestMapping("/iot/device/message")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/device/message/page | GET | 获得设备消息分页 | iot:device:message-query |
| /iot/device/message/pair-page | GET | 获得设备消息对分页（请求-回复配对） | iot:device:message-query |
| /iot/device/message/send | POST | 发送消息（可用于设备模拟） | iot:device:message-send |

### OTA 升级 (IotOtaFirmwareController / IotOtaTaskController / IotOtaTaskRecordController)

IotOtaFirmwareController — `@RequestMapping("/iot/ota/firmware")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/ota/firmware/create | POST | 创建 OTA 固件 | iot:ota-firmware:create |
| /iot/ota/firmware/update | PUT | 更新 OTA 固件 | iot:ota-firmware:update |
| /iot/ota/firmware/delete | DELETE | 删除 OTA 固件 | iot:ota-firmware:delete |
| /iot/ota/firmware/get | GET | 获得 OTA 固件 | iot:ota-firmware:query |
| /iot/ota/firmware/page | GET | 获得 OTA 固件分页 | iot:ota-firmware:query |

IotOtaTaskController — `@RequestMapping("/iot/ota/task")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/ota/task/create | POST | 创建 OTA 升级任务 | iot:ota-task:create |
| /iot/ota/task/cancel | POST | 取消 OTA 升级任务 | iot:ota-task:cancel |
| /iot/ota/task/page | GET | 获得 OTA 升级任务分页 | iot:ota-task:query |
| /iot/ota/task/get | GET | 获得 OTA 升级任务 | iot:ota-task:query |

IotOtaTaskRecordController — `@RequestMapping("/iot/ota/task/record")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/ota/task/record/get-status-statistics | GET | 获得 OTA 升级记录状态统计 | iot:ota-task-record:query |
| /iot/ota/task/record/page | GET | 获得 OTA 升级记录分页 | iot:ota-task-record:query |
| /iot/ota/task/record/get | GET | 获得 OTA 升级记录 | iot:ota-task-record:query |
| /iot/ota/task/record/cancel | PUT | 取消 OTA 升级记录 | iot:ota-task-record:cancel |

### 产品管理 (IotProductController / IotProductCategoryController)

IotProductController — `@RequestMapping("/iot/product")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/product/create | POST | 创建产品 | iot:product:create |
| /iot/product/update | PUT | 更新产品 | iot:product:update |
| /iot/product/update-status | PUT | 更新产品状态 | iot:product:update |
| /iot/product/delete | DELETE | 删除产品 | iot:product:delete |
| /iot/product/get | GET | 获得产品 | iot:product:query |
| /iot/product/get-by-key | GET | 通过 ProductKey 获得产品 | iot:product:query |
| /iot/product/page | GET | 获得产品分页 | iot:product:query |
| /iot/product/export-excel | GET | 导出产品 Excel | iot:product:export |
| /iot/product/sync-property-table | POST | 同步产品属性表结构到 TDengine | iot:product:update |
| /iot/product/simple-list | GET | 获取产品的精简信息列表（下拉用） | 已认证 |

IotProductCategoryController — `@RequestMapping("/iot/product-category")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/product-category/create | POST | 创建产品分类 | iot:product-category:create |
| /iot/product-category/update | PUT | 更新产品分类 | iot:product-category:update |
| /iot/product-category/delete | DELETE | 删除产品分类 | iot:product-category:delete |
| /iot/product-category/get | GET | 获得产品分类 | iot:product-category:query |
| /iot/product-category/page | GET | 获得产品分类分页 | iot:product-category:query |
| /iot/product-category/simple-list | GET | 获得所有产品分类列表 | iot:product-category:query |

### 规则引擎 (IotDataRuleController / IotDataSinkController / IotSceneRuleController)

IotDataRuleController — `@RequestMapping("/iot/data-rule")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/data-rule/create | POST | 创建数据流转规则 | iot:data-rule:create |
| /iot/data-rule/update | PUT | 更新数据流转规则 | iot:data-rule:update |
| /iot/data-rule/delete | DELETE | 删除数据流转规则 | iot:data-rule:delete |
| /iot/data-rule/get | GET | 获得数据流转规则 | iot:data-rule:query |
| /iot/data-rule/page | GET | 获得数据流转规则分页 | iot:data-rule:query |

IotDataSinkController — `@RequestMapping("/iot/data-sink")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/data-sink/create | POST | 创建数据目的 | iot:data-sink:create |
| /iot/data-sink/update | PUT | 更新数据目的 | iot:data-sink:update |
| /iot/data-sink/delete | DELETE | 删除数据目的 | iot:data-sink:delete |
| /iot/data-sink/get | GET | 获得数据目的 | iot:data-sink:query |
| /iot/data-sink/page | GET | 获得数据目的分页 | iot:data-sink:query |
| /iot/data-sink/simple-list | GET | 获取数据目的的精简信息列表（下拉用） | 已认证 |

IotSceneRuleController — `@RequestMapping("/iot/scene-rule")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/scene-rule/create | POST | 创建场景联动 | iot:scene-rule:create |
| /iot/scene-rule/update | PUT | 更新场景联动 | iot:scene-rule:update |
| /iot/scene-rule/update-status | PUT | 更新场景联动状态 | iot:scene-rule:update |
| /iot/scene-rule/delete | DELETE | 删除场景联动 | iot:scene-rule:delete |
| /iot/scene-rule/get | GET | 获得场景联动 | iot:scene-rule:query |
| /iot/scene-rule/page | GET | 获得场景联动分页 | iot:scene-rule:query |
| /iot/scene-rule/simple-list | GET | 获取场景联动的精简信息列表（下拉用） | 已认证 |

### 数据统计 (IotStatisticsController)

`@RequestMapping("/iot/statistics")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/statistics/get-summary | GET | 获取全局的数据统计 | 已认证 |
| /iot/statistics/get-device-message-summary-by-date | GET | 获取设备消息的数据统计 | 已认证 |

### 产品物模型 (IotThingModelController)

`@RequestMapping("/iot/thing-model")`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /iot/thing-model/create | POST | 创建产品物模型 | iot:thing-model:create |
| /iot/thing-model/update | PUT | 更新产品物模型 | iot:thing-model:update |
| /iot/thing-model/delete | DELETE | 删除产品物模型 | iot:thing-model:delete |
| /iot/thing-model/get | GET | 获得产品物模型 | iot:thing-model:query |
| /iot/thing-model/get-tsl | GET | 获得产品物模型 TSL | iot:thing-model:query |
| /iot/thing-model/list | GET | 获得产品物模型列表 | iot:thing-model:query |
| /iot/thing-model/page | GET | 获得产品物模型分页 | iot:thing-model:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| iot_product | 产品 | TenantBaseDO | name、productKey、productSecret、registerEnabled、categoryId、deviceType、netType、protocolType、serializeType、status |
| iot_product_category | 产品分类 | BaseDO | name、sort、status、description |
| iot_thing_model | 产品物模型（TSL） | BaseDO | identifier、productId、productKey、type（1属性/2服务/3事件）、property/event/service（JSON，autoResultMap） |
| iot_device | 设备 | TenantBaseDO | deviceName、nickname、serialNumber、groupIds、productId、productKey、deviceType、gatewayId、state、deviceSecret、onlineTime、firmwareId、latitude/longitude、config |
| iot_device_group | 设备分组 | BaseDO | name、status、description |
| iot_device_modbus_config | 设备 Modbus 连接配置 | TenantBaseDO | deviceId、productId、ip、port、slaveId、mode、frameFormat、timeout、retryInterval、status |
| iot_device_modbus_point | 设备 Modbus 点位配置 | TenantBaseDO | deviceId、thingModelId、identifier、functionCode（FC01-04）、registerAddress、registerCount、byteOrder、rawDataType、scale、pollInterval |
| iot_ota_firmware | OTA 固件 | BaseDO | name、version、productId、fileUrl、fileSize、fileDigestAlgorithm、fileDigestValue |
| iot_ota_task | OTA 升级任务 | BaseDO | name、firmwareId、status、deviceScope、deviceTotalCount、deviceSuccessCount |
| iot_ota_task_record | OTA 升级记录 | BaseDO | firmwareId、taskId、deviceId、fromFirmwareId、status、progress、description |
| iot_data_rule | 数据流转规则 | BaseDO | name、status、sourceConfigs（JSON：method/productId/deviceId/identifier）、sinkIds |
| iot_data_sink | 数据流转目的 | BaseDO | name、type（IotDataSinkTypeEnum）、config（JSON 多态，IotAbstractDataSinkConfig 9 种子类） |
| iot_scene_rule | 场景联动 | TenantBaseDO | name、status、lastTriggerTime、triggers（JSON：type/productId/deviceId/identifier/operator/value/cronExpression/conditionGroups）、actions（JSON） |
| iot_alert_config | IoT 告警配置 | BaseDO | name、level、status、sceneRuleIds、receiveUserIds、receiveTypes、smsTemplateCode、mailTemplateCode、notifyTemplateCode |
| iot_alert_record | IoT 告警记录 | BaseDO | configId、configName、configLevel、sceneRuleId、productId、deviceId、deviceMessage（JSON）、processStatus、processRemark |
| iot_device_message（TDengine 超级表） | 设备消息日志 | 无（IotDeviceMessageDO，自管理主键） | id（消息编号）、deviceId、tenantId、serverId、upstream、reply、identifier、requestId、method、params、data、code、msg、reportTime、ts |
| iot_device_property（TDengine，按产品 productKey 建超级表+设备子表） | 设备属性最新值/历史 | 无（IotDevicePropertyDO 为值包装对象） | value、updateTime（历史表含时间戳与各属性列） |

说明：数据目的配置 9 种子类（Http/Tcp/WebSocket/Mqtt/Database/Redis/RocketMQ/RabbitMQ/Kafka）位于 `dal/dataobject/rule/config`，物模型 TSL 模型（ThingModelProperty/Service/Event 及 dataType 规格类）位于 `dal/dataobject/thingmodel/model`，均为 JSON 内嵌模型，不单独建表。

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 策略模式 | service/rule/scene/matcher/trigger（IotSceneRuleTriggerMatcher 5 个实现）+ matcher/condition（IotSceneRuleConditionMatcher 3 个实现）+ IotSceneRuleMatcherManager | 场景联动按触发类型（属性上报/事件上报/状态变更/服务调用/定时）与条件类型分发到对应匹配器 |
| 策略模式 | service/rule/scene/action（IotSceneRuleAction 4 个实现：设备服务调用、属性设置、告警触发、告警恢复） | 场景动作按动作类型策略化执行 |
| 策略模式（多态配置） | dal/dataobject/rule/config：IotAbstractDataSinkConfig 抽象类 + 9 个子类，@JsonTypeInfo 按 type 反序列化 | 数据流转目的同一字段 config 适配 HTTP/TCP/WebSocket/MQTT/DB/Redis/RocketMQ/RabbitMQ/Kafka |
| 插件化策略 | yudao-module-iot-gateway 的 protocol 包：IotProtocol 接口 + IotProtocolManager（SmartLifecycle），MQTT/EMQX/CoAP/HTTP/TCP/UDP/WebSocket/Modbus（Client/Server）实现 | 网关按配置启停多协议接入实例 |
| 模板方法 | gateway/protocol/AbstractIotProtocolDownstreamSubscriber | 各协议下行消息订阅者的公共流程骨架 |
| 观察者/发布订阅 | core messagebus + biz 的 mq 包：IotDeviceMessageProducer 发布，IotDeviceMessageSubscriber、IotDataRuleMessageSubscriber、IotSceneRuleMessageSubscriber 消费 | 设备消息驱动属性存储、规则引擎、场景联动 |

## 依赖关系

- **上游**（本模块依赖）
  - framework starter：yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-biz-tenant、yudao-spring-boot-starter-mq（经 core 引入）、yudao-spring-boot-starter-test
  - 中间件驱动：taos-jdbcdriver（TDengine）、rocketmq-spring-boot-starter、spring-kafka、spring-boot-starter-amqp（RabbitMQ，后三者 optional）、org.eclipse.paho.client.mqttv3、okhttp、vertx-web/vertx-mqtt、j2mod（Modbus）、californium-core（CoAP，后三者为 gateway）
  - 业务模块：yudao-module-system（AdminUserApi、SmsSendApi、MailSendApi、NotifyMessageSendApi）、yudao-module-iot-core
- **下游**（依赖本模块）
  - yudao-server：可选引入 yudao-module-iot-biz（yudao-server/pom.xml 中默认注释，启用后随主服务启动）
  - yudao-module-iot-gateway：依赖 core，通过 HTTP 调用 biz 暴露的 IotDeviceCommonApi 获取设备信息/鉴权/注册/Modbus 配置
  - 说明：gateway 与 biz 之间还通过 core 的消息总线（redis stream / rocketmq / kafka / rabbitmq / spring-event）异步传递设备消息

## 对外暴露的 API

biz 侧实现 `cn.iocoder.yudao.module.iot.core.biz.IotDeviceCommonApi`（实现类 `api/device/IoTDeviceApiImpl.java`，@Primary，@PermitAll 内部 HTTP 接口，供 gateway 进程调用）：

| API接口 | 方法 | 消费方 |
|--------|------|-------|
| IotDeviceCommonApi | authDevice（设备鉴权） | yudao-module-iot-gateway |
| IotDeviceCommonApi | getDevice（查询设备信息） | yudao-module-iot-gateway |
| IotDeviceCommonApi | registerDevice（设备动态注册） | yudao-module-iot-gateway |
| IotDeviceCommonApi | registerSubDevices（网关子设备批量注册） | yudao-module-iot-gateway |
| IotDeviceCommonApi | getModbusDeviceConfigList（获取 Modbus 设备配置与点位） | yudao-module-iot-gateway |

## 详细文档

- [api-alert.md](api-alert.md) - 告警管理（告警配置 + 告警记录）
- [api-device.md](api-device.md) - 设备管理（设备/分组/Modbus 配置/属性/消息）
- [api-ota.md](api-ota.md) - OTA 升级（固件/升级任务/升级记录）
- [api-product.md](api-product.md) - 产品管理（产品 + 产品分类）
- [api-rule.md](api-rule.md) - 规则引擎（场景联动/数据流转规则/数据目的）
- [api-statistics.md](api-statistics.md) - 数据统计
- [api-thingmodel.md](api-thingmodel.md) - 物模型（TSL 定义）
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
