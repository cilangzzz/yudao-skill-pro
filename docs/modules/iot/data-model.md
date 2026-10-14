# 数据模型详情

> iot 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

iot 模块采用 **biz/core/gateway 三子模块 + MySQL/TDengine 双存储**架构：

- **MySQL**：存储业务配置数据（产品、设备、物模型、OTA、规则、告警），DO 位于 `yudao-module-iot-biz` 的 `dal/dataobject` 下，Mapper 位于 `dal/mysql` 下；
- **TDengine**：存储时序数据（设备消息日志、设备属性历史值），DO 无 `@TableName`，Mapper 位于 `dal/tdengine` 下，超级表由应用启动时自动创建（`TDengineTableInitRunner`）；
- **Redis**：存储设备属性的"最新值"缓存（`IotDevicePropertyDO`），由 `DevicePropertyRedisDAO` 读写。

## 1. 实体继承体系

```
BaseDO（通用审计字段：creator 创建者、createTime 创建时间、updater 更新者、updateTime 更新时间、deleted 逻辑删除）
│
├── TenantBaseDO（多租户扩展：+ tenantId 租户编号）
│   ├── IotDeviceDO                 （iot_device               设备）
│   ├── IotProductDO                （iot_product              产品）
│   ├── IotDeviceModbusConfigDO     （iot_device_modbus_config 设备 Modbus 连接配置）
│   ├── IotDeviceModbusPointDO      （iot_device_modbus_point  设备 Modbus 点位配置）
│   └── IotSceneRuleDO              （iot_scene_rule           场景联动规则）
│
├── IotDeviceGroupDO                （iot_device_group         设备分组）
├── IotProductCategoryDO            （iot_product_category     产品分类）
├── IotThingModelDO                 （iot_thing_model          产品物模型功能）
├── IotAlertConfigDO                （iot_alert_config         告警配置）
├── IotAlertRecordDO                （iot_alert_record         告警记录）
├── IotDataRuleDO                   （iot_data_rule            数据流转规则）
├── IotDataSinkDO                   （iot_data_sink            数据流转目的）
├── IotOtaFirmwareDO                （iot_ota_firmware         OTA 固件）
├── IotOtaTaskDO                    （iot_ota_task             OTA 升级任务）
└── IotOtaTaskRecordDO              （iot_ota_task_record      OTA 升级任务记录）

不继承基类（非 MySQL 存储，无审计字段）：
├── IotDeviceMessageDO              （TDengine 超级表 device_message，自带 tenantId 字段）
└── IotDevicePropertyDO             （Redis Hash iot:device_property:{deviceId}，属性最新值）
```

**使用规则**：

- **TenantBaseDO**：业务数据归属租户、需要多租户隔离的表使用，目前仅 5 张：`iot_device`、`iot_product`、`iot_device_modbus_config`、`iot_device_modbus_point`、`iot_scene_rule`；
- **BaseDO**：平台级/全局共享的配置数据（产品分类、设备分组、物模型、OTA、规则引擎、告警等）使用，仅含审计与逻辑删除字段；
- **无基类**：TDengine / Redis 存储的 DO 不继承 MyBatis-Plus 基类，租户字段（`tenantId`）在 `IotDeviceMessageDO` 中以普通列形式冗余存储，`IotDevicePropertyDO` 则完全由设备维度 Key 隔离。

> 说明：仓库内未包含 iot 模块表的物理建表 DDL（`sql/` 目录仅有字典数据），下文"索引"均指**从 Mapper/Service 代码推断的逻辑唯一约束与高频查询路径**，不代表物理索引。

## 2. 核心 DO 实体

### 2.1 产品聚合（产品 / 分类 / 物模型）

#### IotProductDO (iot_product)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 产品 ID，主键自增 |
| name | String | name | 产品名称 |
| productKey | String | product_key | 产品标识，全局唯一 |
| productSecret | String | product_secret | 产品密钥，用于一型一密动态注册 |
| registerEnabled | Boolean | register_enabled | 是否开启动态注册 |
| categoryId | Long | category_id | 产品分类编号，关联 IotProductCategoryDO |
| icon | String | icon | 产品图标 |
| picUrl | String | pic_url | 产品图片 |
| description | String | description | 产品描述 |
| status | Integer | status | 产品状态，枚举 IotProductStatusEnum |
| deviceType | Integer | device_type | 设备类型，枚举 IotProductDeviceTypeEnum（网关/网关子设备/直连） |
| netType | Integer | net_type | 联网方式，枚举 IotNetTypeEnum |
| protocolType | String | protocol_type | 协议类型，枚举 core 的 IotProtocolTypeEnum |
| serializeType | String | serialize_type | 序列化类型，枚举 core 的 IotSerializeTypeEnum |

**继承**: TenantBaseDO
**索引**: `product_key` 逻辑唯一（`IotProductMapper#selectByProductKey` 按忽略大小写 selectOne 校验）；高频查询列：`name`、`product_key`、`status`、`device_type`。

#### IotProductCategoryDO (iot_product_category)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 分类 ID，主键自增 |
| name | String | name | 分类名字 |
| sort | Integer | sort | 分类排序 |
| status | Integer | status | 分类状态，枚举 CommonStatusEnum |
| description | String | description | 分类描述 |

**继承**: BaseDO
**索引**: 无逻辑唯一约束，普通业务表。

#### IotThingModelDO (iot_thing_model)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 物模型功能编号，主键自增 |
| identifier | String | identifier | 功能标识符，产品内唯一 |
| name | String | name | 功能名称 |
| description | String | description | 功能描述 |
| productId | Long | product_id | 产品编号，关联 IotProductDO |
| productKey | String | product_key | 产品标识，冗余 IotProductDO.productKey |
| type | Integer | type | 功能类型，枚举 IotThingModelTypeEnum（1 属性 / 2 服务 / 3 事件） |
| property | ThingModelProperty | property | 属性定义，JSON 存储（JacksonTypeHandler） |
| event | ThingModelEvent | event | 事件定义，JSON 存储 |
| service | ThingModelService | service | 服务定义，JSON 存储 |

**继承**: BaseDO
**索引**: `(product_id, identifier)` 逻辑唯一（一个产品的每个属性/事件/服务对应一条记录，标识符重复由 Service 校验）；每个产品与物模型是"一对多"关系。

### 2.2 设备聚合（设备 / 分组 / Modbus 配置）

#### IotDeviceDO (iot_device)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 设备 ID，主键自增；特殊值 `DEVICE_ID_ALL = 0L` 表示"全部设备" |
| deviceName | String | device_name | 设备名称，在产品内唯一，用于标识设备 |
| nickname | String | nickname | 设备备注名称 |
| serialNumber | String | serial_number | 设备序列号 |
| picUrl | String | pic_url | 设备图片 |
| groupIds | Set\<Long\> | group_ids | 设备分组编号集合，关联 IotDeviceGroupDO，LongSetTypeHandler 存储，分组过滤使用 FIND_IN_SET |
| productId | Long | product_id | 产品编号，关联 IotProductDO |
| productKey | String | product_key | 产品标识，冗余 IotProductDO.productKey |
| deviceType | Integer | device_type | 设备类型，冗余 IotProductDO.deviceType |
| gatewayId | Long | gateway_id | 网关设备编号，自关联 IotDeviceDO.id，子设备需关联所属网关 |
| state | Integer | state | 设备状态，枚举 IotDeviceStateEnum（0 未激活 / 1 在线 / 2 离线） |
| onlineTime | LocalDateTime | online_time | 最后上线时间 |
| offlineTime | LocalDateTime | offline_time | 最后离线时间 |
| activeTime | LocalDateTime | active_time | 设备激活时间 |
| firmwareId | Long | firmware_id | 当前固件编号，关联 IotOtaFirmwareDO |
| deviceSecret | String | device_secret | 设备密钥，用于设备认证 |
| latitude | BigDecimal | latitude | 设备位置的纬度 |
| longitude | BigDecimal | longitude | 设备位置的经度 |
| config | String | config | 设备配置，JSON 格式，可下发给设备自定义配置 |

**继承**: TenantBaseDO
**索引**: `(product_key, device_name)` 逻辑唯一（`IotDeviceMapper#selectByProductKeyAndDeviceName` 查询单条）；`serial_number` 逻辑唯一（`selectBySerialNumber` selectOne）；高频查询列：`product_id`、`gateway_id`、`state`、`device_type`、`group_ids`（FIND_IN_SET）。

#### IotDeviceGroupDO (iot_device_group)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 分组 ID，主键自增 |
| name | String | name | 分组名字 |
| status | Integer | status | 分组状态，枚举 CommonStatusEnum |
| description | String | description | 分组描述 |

**继承**: BaseDO
**索引**: 无逻辑唯一约束；设备与分组通过 `iot_device.group_ids` JSON 集合隐式关联，无中间表。

#### IotDeviceModbusConfigDO (iot_device_modbus_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键，自增 |
| productId | Long | product_id | 产品编号，关联 IotProductDO |
| deviceId | Long | device_id | 设备编号，关联 IotDeviceDO |
| ip | String | ip | Modbus 服务器 IP 地址 |
| port | Integer | port | Modbus 服务器端口 |
| slaveId | Integer | slave_id | 从站地址 |
| timeout | Integer | timeout | 连接超时时间，单位：毫秒 |
| retryInterval | Integer | retry_interval | 重试间隔，单位：毫秒 |
| mode | Integer | mode | 模式，枚举 IotModbusModeEnum |
| frameFormat | Integer | frame_format | 数据帧格式，枚举 IotModbusFrameFormatEnum |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: TenantBaseDO
**索引**: `device_id` 逻辑一对一（每台设备的 Modbus 连接配置）。

#### IotDeviceModbusPointDO (iot_device_modbus_point)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 主键，自增 |
| deviceId | Long | device_id | 设备编号，关联 IotDeviceDO |
| thingModelId | Long | thing_model_id | 物模型属性编号，关联 IotThingModelDO |
| identifier | String | identifier | 属性标识符，冗余 IotThingModelDO.identifier |
| name | String | name | 属性名称，冗余 IotThingModelDO.name |
| functionCode | Integer | function_code | Modbus 功能码，取值 FC01-04（读线圈/离散输入/保持寄存器/输入寄存器） |
| registerAddress | Integer | register_address | 寄存器起始地址 |
| registerCount | Integer | register_count | 寄存器数量 |
| byteOrder | String | byte_order | 字节序，枚举 IotModbusByteOrderEnum |
| rawDataType | String | raw_data_type | 原始数据类型，枚举 IotModbusRawDataTypeEnum |
| scale | BigDecimal | scale | 缩放因子 |
| pollInterval | Integer | poll_interval | 轮询间隔，单位：毫秒 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: TenantBaseDO
**索引**: `(device_id, thing_model_id)` 逻辑唯一（设备 + 物模型属性对应一个采集点位）。

### 2.3 设备消息与属性（TDengine / Redis 存储）

#### IotDeviceMessageDO (TDengine 超级表 device_message)

设备消息日志，存储在 TDengine：超级表 `device_message`，按设备自动建子表 `device_message_{deviceId}`，`device_id` 为 TAG。应用启动时由 `TDengineTableInitRunner` 调用 `defineDeviceMessageStable()` 创建（`CREATE STABLE IF NOT EXISTS`）。

| 字段 | 类型 | TDengine 列 | 说明 |
|-----|------|------------|------|
| ts | Long | ts TIMESTAMP | 存储时间戳（主时间轴） |
| id | String | id NCHAR(50) | 消息编号 |
| reportTime | Long | report_time TIMESTAMP | 上报时间戳 |
| deviceId | Long | device_id BIGINT（TAG） | 设备编号，关联 IotDeviceDO，子表维度 |
| tenantId | Long | tenant_id BIGINT | 租户编号 |
| serverId | String | server_id NCHAR(50) | 服务编号，该消息由哪个 server 发送 |
| upstream | Boolean | upstream BOOL | 是否上行消息，由 IotDeviceMessageUtils 计算，便于统计上下行数量 |
| reply | Boolean | reply BOOL | 是否回复消息，由 IotDeviceMessageUtils 计算，便于统计请求/回复数量 |
| identifier | String | identifier NCHAR(100) | 标识符，对应 IotThingModelDO.identifier，仅事件上报、服务调用时有值 |
| requestId | String | request_id NCHAR(50) | 请求编号，设备生成，对应 Alink 协议 id / 华为云 request_id |
| method | String | method NCHAR(100) | 请求方法，枚举 IotDeviceMessageMethodEnum，如 thing.property.post |
| params | Object | params VARCHAR(8192) | 请求参数（属性上报 properties、事件上报 params） |
| data | Object | data VARCHAR(8192) | 响应结果 |
| code | Integer | code INT | 响应错误码 |
| msg | String | msg NCHAR(256) | 响应提示 |

**继承**: 无（不继承 BaseDO，TDengine 存储）
**索引**: 主时间轴 `ts`；TAG `device_id` 决定子表路由；查询按子表 `device_message_{deviceId}` 过滤 `method` / `upstream` / `reply` / `identifier`，统计查询走超级表（TIMETRUNCATE 按小时分组）。

#### IotDevicePropertyDO (Redis Hash iot:device_property:{deviceId})

设备属性"最新值"，存储在 Redis Hash：Key 为 `iot:device_property:{deviceId}`（RedisKeyConstants.DEVICE_PROPERTY），Hash field 为属性 identifier，value 为该 DO 的 JSON。属性"历史值"存 TDengine。

| 字段 | 类型 | 存储位置 | 说明 |
|-----|------|---------|------|
| value | Object | Hash value JSON 内 | 属性值（最新） |
| updateTime | LocalDateTime | Hash value JSON 内 | 更新时间 |

**继承**: 无（Redis DO）
**索引**: 按 Key `iot:device_property:{deviceId}` 整体读写（Hash 结构）。

**TDengine 属性超级表（随物模型动态变更）**：超级表 `product_property_{productId}`（按产品维度建表），TAG 为 `device_id BIGINT`；固定列 `ts TIMESTAMP`、`report_time TIMESTAMP`，其余列为该产品物模型全部属性（identifier 作为列名，类型由 ThingModelProperty 推断）。子表为 `device_property_{deviceId}`。物模型变更时由 `IotDevicePropertyMapper#alterProductPropertySTable` 自动 `ALTER STABLE` 增加/删除/修改列。注意：建表维度是 `productId`（而非 productKey）。

### 2.4 OTA 聚合（固件 / 任务 / 记录）

#### IotOtaFirmwareDO (iot_ota_firmware)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 固件编号，主键自增 |
| name | String | name | 固件名称 |
| description | String | description | 固件描述 |
| version | String | version | 版本号 |
| productId | Long | product_id | 产品编号，关联 IotProductDO |
| fileUrl | String | file_url | 固件文件 URL |
| fileSize | Long | file_size | 固件文件大小 |
| fileDigestAlgorithm | String | file_digest_algorithm | 固件文件签名算法，枚举 DigestAlgorithm，目前只使用 MD5 |
| fileDigestValue | String | file_digest_value | 固件文件签名结果 |

**继承**: BaseDO
**索引**: 高频查询列：`product_id`。

#### IotOtaTaskDO (iot_ota_task)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 任务编号，主键自增 |
| name | String | name | 任务名称 |
| description | String | description | 任务描述 |
| firmwareId | Long | firmware_id | 固件编号，关联 IotOtaFirmwareDO |
| status | Integer | status | 任务状态，枚举 IotOtaTaskStatusEnum |
| deviceScope | Integer | device_scope | 设备升级范围，枚举 IotOtaTaskDeviceScopeEnum |
| deviceTotalCount | Integer | device_total_count | 设备总数数量 |
| deviceSuccessCount | Integer | device_success_count | 设备成功数量 |

**继承**: BaseDO
**索引**: 高频查询列：`firmware_id`、`status`。

#### IotOtaTaskRecordDO (iot_ota_task_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 升级记录编号，主键自增 |
| firmwareId | Long | firmware_id | 目标固件编号，关联 IotOtaFirmwareDO |
| taskId | Long | task_id | 任务编号，关联 IotOtaTaskDO |
| deviceId | Long | device_id | 设备编号，关联 IotDeviceDO |
| fromFirmwareId | Long | from_firmware_id | 来源固件编号，关联 IotDeviceDO.firmwareId |
| status | Integer | status | 升级状态，枚举 IotOtaTaskRecordStatusEnum |
| progress | Integer | progress | 升级进度，百分比 |
| description | String | description | 升级进度描述，只记录最后一次描述，历史看设备消息日志 |

**继承**: BaseDO
**索引**: 高频查询列：`task_id`、`device_id`、`firmware_id`、`status`；`(task_id, device_id)` 逻辑唯一（一个任务内每台设备一条记录）。

### 2.5 规则引擎聚合（场景联动 / 数据流转）

#### IotSceneRuleDO (iot_scene_rule)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 场景联动编号，主键自增 |
| name | String | name | 场景联动名称 |
| description | String | description | 场景联动描述 |
| status | Integer | status | 场景联动状态，枚举 CommonStatusEnum |
| lastTriggerTime | LocalDateTime | last_trigger_time | 最后触发时间 |
| triggers | List\<Trigger\> | triggers | 场景定义配置，JSON 存储（JacksonTypeHandler） |
| actions | List\<Action\> | actions | 场景动作配置，JSON 存储 |

**继承**: TenantBaseDO
**索引**: 无逻辑唯一约束；规则列表整表加载进 Redis 缓存（`iot:scene_rule_list`）供匹配器使用。

**内嵌结构（JSON）**：

- `Trigger`（触发器）：`type` 触发类型（IotSceneRuleTriggerTypeEnum：设备上下线 / 属性上报 / 事件上报 / 服务调用 / 定时 TIMER）、`productId`、`deviceId`（0 表示全部设备）、`identifier` 物模型标识符、`operator` 操作符（IotSceneRuleConditionOperatorEnum）、`value` 参数（多值逗号分隔）、`cronExpression` 定时 CRON 表达式、`conditionGroups` 触发条件分组（`List<List<TriggerCondition>>`，分组间"或"、组内"且"）；
- `TriggerCondition`（触发条件）：`type` 条件类型（IotSceneRuleConditionTypeEnum：设备状态 / 设备属性 / 当前时间）、`productId`、`deviceId`、`identifier`、`operator`、`param`；
- `Action`（动作）：`type` 执行类型（IotSceneRuleActionTypeEnum：设备属性设置 / 服务调用 / 告警触发 / 告警恢复）、`productId`、`deviceId`、`identifier`、`params` 请求参数、`alertConfigId` 关联告警配置。

配套策略辅助包：`service/rule/scene/matcher`（5 个 TriggerMatcher + 3 个 ConditionMatcher + MatcherManager）、`service/rule/scene/action`（4 个 SceneRuleAction 实现）、`service/rule/scene/timer`（定时触发处理）。

#### IotDataRuleDO (iot_data_rule)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 数据流转规则编号，主键自增 |
| name | String | name | 数据流转规则名称 |
| description | String | description | 数据流转规则描述 |
| status | Integer | status | 数据流转规则状态，枚举 CommonStatusEnum |
| sourceConfigs | List\<SourceConfig\> | source_configs | 数据源配置数组，JSON 存储 |
| sinkIds | List\<Long\> | sink_ids | 数据目的编号数组，关联 IotDataSinkDO，LongListTypeHandler 存储 |

**继承**: BaseDO
**索引**: 无逻辑唯一约束；监听 SourceConfig 数据源，转发到若干 IotDataSinkDO 数据目的（多对多，经 sinkIds）。

**内嵌结构 `SourceConfig`（JSON）**：`method` 消息方法（IotDeviceMessageMethodEnum 上行部分，必填）、`productId` 产品编号、`deviceId` 设备编号（0 表示全部设备）、`identifier` 物模型标识符。

#### IotDataSinkDO (iot_data_sink)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 数据流转目的编号，主键自增 |
| name | String | name | 数据流转目的名称 |
| description | String | description | 数据流转目的描述 |
| status | Integer | status | 数据流转目的状态，枚举 CommonStatusEnum |
| type | Integer | type | 数据流转目的类型，枚举 IotDataSinkTypeEnum（1 HTTP / 2 TCP / 3 WebSocket / 10 MQTT / 20 Database / 21 Redis / 30 RocketMQ / 31 RabbitMQ / 32 Kafka） |
| config | IotAbstractDataSinkConfig | config | 数据流转目的配置，JSON 存储，@JsonTypeInfo 多态反序列化（type 字符串对应 IotDataSinkTypeEnum 数值，共 9 个子类） |

**继承**: BaseDO
**索引**: 无逻辑唯一约束；`@KeySequence("iot_data_bridge_seq")` 为历史遗留命名（前身"数据桥梁"）。

### 2.6 告警聚合（告警配置 / 告警记录）

#### IotAlertConfigDO (iot_alert_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 配置编号，主键自增 |
| name | String | name | 配置名称 |
| description | String | description | 配置描述 |
| level | Integer | level | 告警级别，字典 iot_alert_level |
| status | Integer | status | 配置状态，枚举 CommonStatusEnum |
| sceneRuleIds | List\<Long\> | scene_rule_ids | 关联的场景联动规则编号数组，关联 IotSceneRuleDO，LongListTypeHandler 存储 |
| receiveUserIds | List\<Long\> | receive_user_ids | 接收的用户编号数组，关联 system 模块管理员用户，LongListTypeHandler 存储 |
| receiveTypes | List\<Integer\> | receive_types | 接收的类型数组，枚举 IotAlertReceiveTypeEnum（短信/邮件/站内信），IntegerListTypeHandler 存储 |
| smsTemplateCode | String | sms_template_code | 短信模板编号，关联 system SmsTemplateDO.code |
| mailTemplateCode | String | mail_template_code | 邮件模板编号，关联 system MailTemplateDO.code |
| notifyTemplateCode | String | notify_template_code | 站内信模板编号，关联 system NotifyTemplateDO.code |

**继承**: BaseDO
**索引**: 无逻辑唯一约束；与 IotSceneRuleDO 通过 `scene_rule_ids` 多对多关联，与告警动作（ALERT_TRIGGER / ALERT_RECOVER）双向引用。

#### IotAlertRecordDO (iot_alert_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|--------|------|
| id | Long | id | 记录编号，主键自增 |
| configId | Long | config_id | 告警配置编号，关联 IotAlertConfigDO |
| configName | String | config_name | 告警配置名称，冗余 IotAlertConfigDO.name |
| configLevel | Integer | config_level | 告警级别，冗余 IotAlertConfigDO.level，字典 iot_alert_level |
| sceneRuleId | Long | scene_rule_id | 触发的场景规则编号，关联 IotSceneRuleDO |
| productId | Long | product_id | 产品编号，关联 IotProductDO |
| deviceId | Long | device_id | 设备编号，关联 IotDeviceDO |
| deviceMessage | IotDeviceMessage | device_message | 触发的设备消息，JSON 存储（JacksonTypeHandler） |
| processStatus | Boolean | process_status | 是否已处理 |
| processRemark | String | process_remark | 处理结果（备注） |

**继承**: BaseDO
**索引**: 高频查询列：`config_id`、`device_id`、`product_id`、`process_status`；冗余 `config_name`、`config_level` 避免联表查询。

## 3. 实体关系

```
IotProductCategory 1 ──< n IotProduct 1 ──< n IotDevice >── n IotDeviceGroup
                          │  │  │              （group_ids JSON 集合，无中间表）
                          │  │  └──< n IotThingModel（1 产品 = n 属性/事件/服务记录）
                          │  │
                          │  ├──< n IotOtaFirmware 1 ──< n IotOtaTask 1 ──< n IotOtaTaskRecord >── 1 IotDevice
                          │  │        （record.fromFirmwareId 冗余设备原固件）
                          │  └── 1 IotDeviceModbusConfig（1 设备 1 份连接配置）
                          │         └── IotDeviceModbusPoint n >── 1 IotThingModel（点位绑定物模型属性）
                          │
IotDevice 1 ──< n TDengine device_message_{deviceId} 子表（消息日志，TAG device_id）
IotDevice 1 ── 1 Redis iot:device_property:{deviceId}（属性最新值）
IotProduct 1 ── 1 TDengine product_property_{productId} 超级表（属性历史值，动态列 = 物模型属性）
IotDevice 1 ── 1 IotDeviceModbusConfig；1 IotDevice ──< n IotDeviceModbusPoint

IotSceneRule（triggers/actions JSON 内引用 IotProduct / IotDevice / IotThingModel / IotAlertConfig）
IotDataRule n >── n IotDataSink（sink_ids JSON 数组）；SourceConfig 内引用 IotProduct / IotDevice / IotThingModel
IotAlertConfig n >── n IotSceneRule（scene_rule_ids）；receiveUserIds ──> system 管理员用户（跨模块）
IotAlertRecord n >── 1 IotAlertConfig；n >── 1 IotSceneRule；n >── 1 IotDevice；n >── 1 IotProduct
```

核心关系说明：

1. **产品 → 设备**：一对多；设备冗余 `product_key`、`device_type`，避免查询产品表；
2. **产品 → 物模型**：一对多，每个属性/事件/服务一条记录；物模型同时驱动 TDengine 属性超级表的动态列；
3. **设备 → 网关**：自关联（`gateway_id`），网关子设备挂到网关设备下；
4. **OTA 链路**：固件 → 升级任务 → 升级记录（任务 1 → n 记录，记录 n → 1 设备），设备当前固件记录在 `iot_device.firmware_id`；
5. **规则引擎**：场景联动的触发器/条件/动作全部 JSON 化内嵌，运行时加载进 Redis 缓存由 Matcher 策略匹配；数据流转规则通过 `sink_ids` 关联多个数据目的；
6. **告警链路**：场景联动动作（ALERT_TRIGGER）触发告警 → 按 IotAlertConfigDO 配置（级别、接收人、接收渠道、模板）发送通知 → 落库 IotAlertRecordDO；
7. **跨模块引用**：告警接收人关联 `system_users`，短信/邮件/站内信模板关联 system 模块的 Template 表（按 code 关联）。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|------|
| iot_device | IotDeviceDO | IoT 设备（含网关/子设备、状态、位置、密钥） |
| iot_device_group | IotDeviceGroupDO | IoT 设备分组 |
| iot_device_modbus_config | IotDeviceModbusConfigDO | 设备 Modbus 连接配置（IP/端口/从站/模式） |
| iot_device_modbus_point | IotDeviceModbusPointDO | 设备 Modbus 点位配置（功能码/寄存器/字节序/轮询） |
| iot_product | IotProductDO | IoT 产品（协议、序列化、动态注册） |
| iot_product_category | IotProductCategoryDO | IoT 产品分类 |
| iot_thing_model | IotThingModelDO | 产品物模型功能（属性/事件/服务，JSON 定义） |
| iot_ota_firmware | IotOtaFirmwareDO | OTA 固件（文件、签名、版本） |
| iot_ota_task | IotOtaTaskDO | OTA 升级任务（范围、进度统计） |
| iot_ota_task_record | IotOtaTaskRecordDO | OTA 升级任务记录（单设备进度与状态） |
| iot_scene_rule | IotSceneRuleDO | 场景联动规则（触发器/条件/动作 JSON） |
| iot_data_rule | IotDataRuleDO | 数据流转规则（数据源 → 数据目的） |
| iot_data_sink | IotDataSinkDO | 数据流转目的（9 种类型，多态配置） |
| iot_alert_config | IotAlertConfigDO | 告警配置（级别、接收人、通知模板） |
| iot_alert_record | IotAlertRecordDO | 告警记录（触发消息快照、处理状态） |
| device_message（TDengine 超级表，子表 device_message_{deviceId}） | IotDeviceMessageDO | 设备消息日志（上下行、方法、参数、响应） |
| product_property_{productId}（TDengine 超级表，子表 device_property_{deviceId}） | （无独立 DO，动态列映射物模型属性） | 设备属性历史值（按产品建超级表，物模型变更自动 ALTER） |

补充：设备属性**最新值**不在任何数据库表中，存于 Redis Hash `iot:device_property:{deviceId}`（DO 为 IotDevicePropertyDO），由 `DevicePropertyRedisDAO` 维护；规则引擎运行态缓存存于 `iot:scene_rule_list`、`iot:data_rule_list`、`iot:data_sink`、`iot:thing_model_list`、`iot:device`、`iot:product` 等 Redis Key（见 RedisKeyConstants）。
