# 规则引擎接口 (IotDataRuleController / IotDataSinkController / IotSceneRuleController)

> IoT 规则引擎域：管理数据流转目的（Data Sink）、数据流转规则（Data Rule）与场景联动（Scene Rule），实现设备消息按规则转发到多种数据目的、以及按触发器/条件自动执行联动动作。

## 接口路径前缀

- `/iot/data-rule` (Controller: IotDataRuleController) —— 数据流转规则
- `/iot/data-sink` (Controller: IotDataSinkController) —— 数据流转目的
- `/iot/scene-rule` (Controller: IotSceneRuleController) —— 场景联动

---

## 1. 数据流转规则（IotDataRuleController）

数据流转规则监听设备上行消息（数据源配置 sourceConfigs），并转发到一个或多个数据目的（sinkIds）。

### 1.1 创建数据流转规则

- **路径**: POST /iot/data-rule/create
- **权限**: iot:data-rule:create
- **说明**: 新增一条数据流转规则

**请求参数 (IotDataRuleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| id | Long | 否 | - | 数据流转规则编号（新增不传，修改必传） |
| name | String | 是 | @NotEmpty | 数据流转规则名称 |
| description | String | 否 | - | 数据流转规则描述 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 规则状态（1 开启、0 禁用） |
| sourceConfigs | List\<SourceConfig\> | 是 | @NotEmpty | 数据源配置数组 |
| sinkIds | List\<Long\> | 是 | @NotEmpty | 数据目的编号数组，关联 IotDataSinkDO |

**SourceConfig 结构 (IotDataRuleDO.SourceConfig)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| method | String | 是 | @NotEmpty | 消息方法，取 IotDeviceMessageMethodEnum 中的上行（upstream）部分 |
| productId | Long | 否 | - | 产品编号，关联 IotProductDO |
| deviceId | Long | 是 | @NotEmpty | 设备编号，关联 IotDeviceDO；为 DEVICE_ID_ALL（-1）时表示全部设备 |
| identifier | String | 否 | - | 标识符；物模型时对应 IotThingModelDO.identifier |

**响应**: CommonResult\<Long\> —— 新建的规则编号

**业务逻辑**:
1. 校验规则名称唯一（按 name 查询，重名抛出 DATA_RULE_NAME_EXISTS）
2. 校验数据源配置：产品存在（否则 PRODUCT_NOT_EXISTS）、设备存在（排除 DEVICE_ID_ALL 的项，否则 DEVICE_NOT_EXISTS）、物模型标识符存在（按 productId + identifiers 校验，否则 THING_MODEL_NOT_EXISTS）
3. 校验数据目的存在（validateDataSinksExist，否则 DATA_SINK_NOT_EXISTS）
4. VO 转 IotDataRuleDO 插入 iot_data_rule 表，返回规则编号
5. 通过 @CacheEvict 清除 Redis 中 DATA_RULE_LIST 规则列表缓存

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_010_000 | 数据流转规则不存在 |
| 1_050_010_001 | 数据流转规则名称已存在 |
| 1_050_011_000 | 数据桥梁不存在 |
| 1_050_001_000 | 产品不存在（数据源校验） |
| 1_050_003_000 | 设备不存在（数据源校验） |
| 1_050_002_000 | 产品物模型不存在（数据源校验） |

### 1.2 更新数据流转规则

- **路径**: PUT /iot/data-rule/update
- **权限**: iot:data-rule:update
- **说明**: 修改一条数据流转规则

**请求参数 (IotDataRuleSaveReqVO)**: 与 1.1 相同，此时 id 必传

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验规则存在（否则 DATA_RULE_NOT_EXISTS）
2. 校验规则名称唯一（排除自身 id，否则 DATA_RULE_NAME_EXISTS）
3. 校验数据源配置与数据目的（同创建逻辑）
4. VO 转 IotDataRuleDO 按 id 更新
5. 清除 DATA_RULE_LIST 缓存

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_010_000 | 数据流转规则不存在 |
| 1_050_010_001 | 数据流转规则名称已存在 |
| 1_050_011_000 | 数据桥梁不存在 |
| 1_050_001_000 | 产品不存在（数据源校验） |
| 1_050_003_000 | 设备不存在（数据源校验） |
| 1_050_002_000 | 产品物模型不存在（数据源校验） |

### 1.3 删除数据流转规则

- **路径**: DELETE /iot/data-rule/delete
- **权限**: iot:data-rule:delete
- **说明**: 删除一条数据流转规则

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验规则存在（否则 DATA_RULE_NOT_EXISTS）
2. 按 id 删除记录
3. 清除 DATA_RULE_LIST 缓存

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_010_000 | 数据流转规则不存在 |

### 1.4 获得数据流转规则

- **路径**: GET /iot/data-rule/get
- **权限**: iot:data-rule:query
- **说明**: 按编号查询单条数据流转规则

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult\<IotDataRuleRespVO\>

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 数据流转规则编号 |
| name | String | 数据流转规则名称 |
| description | String | 数据流转规则描述 |
| status | Integer | 规则状态（1 开启、0 禁用） |
| sourceConfigs | List\<SourceConfig\> | 数据源配置数组（结构见 1.1） |
| sinkIds | List\<Long\> | 数据目的编号数组 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 iot_data_rule 记录并转换为 RespVO 返回

### 1.5 获得数据流转规则分页

- **路径**: GET /iot/data-rule/page
- **权限**: iot:data-rule:query
- **说明**: 分页查询数据流转规则

**请求参数 (IotDataRulePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | - | 数据流转规则名称（模糊匹配） |
| status | Integer | 否 | - | 数据流转规则状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<IotDataRuleRespVO\>\>，列表项字段同 1.4

**业务逻辑**:
1. 按名称/状态/创建时间区间条件分页查询

---

## 2. 数据流转目的（IotDataSinkController）

数据目的（Data Sink）定义数据流转的目标端点及其连接配置，类型覆盖 HTTP、TCP、WebSocket、MQTT、数据库、Redis 及各类消息队列。

### 2.1 创建数据目的

- **路径**: POST /iot/data-sink/create
- **权限**: iot:data-sink:create
- **说明**: 新增一个数据流转目的

**请求参数 (IotDataSinkSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| id | Long | 否 | - | 数据目的编号（新增不传，修改必传） |
| name | String | 是 | @NotEmpty | 数据目的名称 |
| description | String | 否 | - | 数据目的描述 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 数据目的状态（1 开启、0 禁用） |
| type | Integer | 是 | @NotNull、@InEnum(IotDataSinkTypeEnum) | 数据目的类型：1 HTTP、2 TCP、3 WebSocket、10 MQTT、20 Database、21 Redis、30 RocketMQ、31 RabbitMQ、32 Kafka |
| config | IotAbstractDataSinkConfig | 是 | @NotNull | 数据目的配置（多态对象，见下方说明） |

**config 多态说明**: `IotAbstractDataSinkConfig` 含 `type`（String）字段，Jackson 按 `type` 属性反序列化为对应子类：1→IotDataSinkHttpConfig、2→IotDataSinkTcpConfig、3→IotDataSinkWebSocketConfig、10→IotDataSinkMqttConfig、20→IotDataSinkDatabaseConfig、21→IotDataSinkRedisConfig、30→IotDataSinkRocketMQConfig、31→IotDataSinkRabbitMQConfig、32→IotDataSinkKafkaConfig。

**响应**: CommonResult\<Long\> —— 新建的数据目的编号

**业务逻辑**:
1. 校验数据目的名称唯一（按 name 查询，重名抛出 DATA_SINK_NAME_EXISTS）
2. VO 转 IotDataSinkDO 插入，返回编号

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_011_002 | 数据流转目的名称已存在 |

### 2.2 更新数据目的

- **路径**: PUT /iot/data-sink/update
- **权限**: iot:data-sink:update
- **说明**: 修改一个数据流转目的

**请求参数 (IotDataSinkSaveReqVO)**: 与 2.1 相同，此时 id 必传

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验数据目的存在（否则 DATA_SINK_NOT_EXISTS）
2. 校验名称唯一（排除自身 id，否则 DATA_SINK_NAME_EXISTS）
3. VO 转 IotDataSinkDO 按 id 更新

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_011_000 | 数据桥梁不存在 |
| 1_050_011_002 | 数据流转目的名称已存在 |

### 2.3 删除数据目的

- **路径**: DELETE /iot/data-sink/delete
- **权限**: iot:data-sink:delete
- **说明**: 删除一个数据流转目的

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验数据目的存在（否则 DATA_SINK_NOT_EXISTS）
2. 校验是否被数据流转规则引用：按 sinkId 查询引用它的数据流转规则，非空则抛出 DATA_SINK_DELETE_FAIL_USED_BY_RULE
3. 校验通过后按 id 删除

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_011_000 | 数据桥梁不存在 |
| 1_050_011_001 | 数据流转目的正在被数据流转规则使用，无法删除 |

### 2.4 获得数据目的

- **路径**: GET /iot/data-sink/get
- **权限**: iot:data-sink:query
- **说明**: 按编号查询单个数据目的

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult\<IotDataSinkRespVO\>

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 数据目的编号 |
| name | String | 数据目的名称 |
| description | String | 数据目的描述 |
| status | Integer | 数据目的状态（1 开启、0 禁用） |
| type | Integer | 数据目的类型（枚举同 2.1） |
| config | IotAbstractDataSinkConfig | 数据目的配置（多态对象，见 2.1） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询记录并转换为 RespVO 返回

### 2.5 获得数据目的分页

- **路径**: GET /iot/data-sink/page
- **权限**: iot:data-sink:query
- **说明**: 分页查询数据目的

**请求参数 (IotDataSinkPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam） |
| name | String | 否 | - | 数据目的名称（模糊匹配） |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 数据目的状态 |
| type | Integer | 否 | @InEnum(IotDataSinkTypeEnum) | 数据目的类型 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<IotDataSinkRespVO\>\>，列表项字段同 2.4

**业务逻辑**:
1. 按名称/状态/类型/创建时间区间条件分页查询

### 2.6 获取数据目的精简信息列表

- **路径**: GET /iot/data-sink/simple-list
- **权限**: 已认证（无 @PreAuthorize，用于前端下拉选项）
- **说明**: 获取所有启用状态数据目的的精简列表

**请求参数**: 无

**响应**: CommonResult\<List\<IotDataSinkRespVO\>\>，仅填充以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 数据目的编号 |
| name | String | 数据目的名称 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）的数据目的列表
2. 只转换 id、name 两个字段返回

---

## 3. 场景联动（IotSceneRuleController）

场景联动由触发器（Triggers）+ 条件组（conditionGroups）+ 执行器（Actions）组成，可由设备消息或定时（CRON）触发。

### 3.1 创建场景联动

- **路径**: POST /iot/scene-rule/create
- **权限**: iot:scene-rule:create
- **说明**: 新增一个场景联动

**请求参数 (IotSceneRuleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| id | Long | 否 | - | 场景编号（新增不传，修改必传） |
| name | String | 是 | @NotEmpty | 场景名称 |
| description | String | 否 | - | 场景描述 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 场景状态（1 开启、0 禁用） |
| triggers | List\<Trigger\> | 是 | @NotEmpty | 触发器数组 |
| actions | List\<Action\> | 是 | @NotEmpty | 执行器数组 |

**Trigger 结构 (IotSceneRuleDO.Trigger)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| type | Integer | 是 | - | 触发类型：1 设备上下线（DEVICE_STATE_UPDATE）、2 属性上报（DEVICE_PROPERTY_POST）、3 事件上报（DEVICE_EVENT_POST）、4 服务调用（DEVICE_SERVICE_INVOKE）、100 定时（TIMER） |
| productId | Long | 否 | - | 产品编号，关联 IotProductDO；定时触发器无需 |
| deviceId | Long | 否 | - | 设备编号，关联 IotDeviceDO；DEVICE_ID_ALL（-1）表示全部设备；定时触发器无需 |
| identifier | String | 否 | - | 物模型标识符，对应 IotThingModelDO.identifier |
| operator | String | 否 | - | 操作符，枚举 IotSceneRuleConditionOperatorEnum（=、in、not in、between、not between、like、date_time_>、date_time_<、date_time_between、time_>、time_<、time_between） |
| value | String | 否 | - | 参数（属性值/在线状态）；多个值用 "," 分隔（如 in、between） |
| cronExpression | String | 否 | - | CRON 表达式（定时触发器必填） |
| conditionGroups | List\<List\<TriggerCondition\>\> | 否 | - | 触发条件分组：组与组之间"或"、组内条件之间"且" |

**TriggerCondition 结构 (IotSceneRuleDO.TriggerCondition)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| type | Integer | 是 | - | 条件类型：1 设备状态（DEVICE_STATE）、2 设备属性（DEVICE_PROPERTY）、100 当前时间（CURRENT_TIME） |
| productId | Long | 否 | - | 产品编号 |
| deviceId | Long | 否 | - | 设备编号 |
| identifier | String | 否 | - | 标识符（属性） |
| operator | String | 否 | - | 操作符，枚举同 Trigger.operator |
| param | String | 否 | - | 参数；多个值用 "," 分隔 |

**Action 结构 (IotSceneRuleDO.Action)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| type | Integer | 是 | - | 执行类型：1 设备属性设置（DEVICE_PROPERTY_SET）、2 设备服务调用（DEVICE_SERVICE_INVOKE）、100 告警触发（ALERT_TRIGGER）、101 告警恢复（ALERT_RECOVER） |
| productId | Long | 否 | - | 产品编号 |
| deviceId | Long | 否 | - | 设备编号 |
| identifier | String | 否 | - | 标识符（服务），对应 IotThingModelDO.identifier |
| params | String | 否 | - | 请求参数，对应 IotDeviceMessage.params；属性设置/服务调用时必填 |
| alertConfigId | Long | 否 | - | 告警配置编号，关联 IotAlertConfigDO；告警恢复时必填（告警触发由告警配置反向关联） |

**响应**: CommonResult\<Long\> —— 新建的场景编号

**业务逻辑**:
1. VO 转 IotSceneRuleDO 插入 iot_scene_rule 表
2. 调用 timerHandler.registerTimerTriggers 注册场景中的定时（TIMER）触发器
3. 清除 SCENE_RULE_LIST 缓存

### 3.2 更新场景联动

- **路径**: PUT /iot/scene-rule/update
- **权限**: iot:scene-rule:update
- **说明**: 修改一个场景联动

**请求参数 (IotSceneRuleSaveReqVO)**: 与 3.1 相同，此时 id 必传

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验场景存在（否则 RULE_SCENE_NOT_EXISTS）
2. VO 转 IotSceneRuleDO 按 id 更新
3. 调用 timerHandler.updateTimerTriggers 同步更新定时触发器
4. 清除 SCENE_RULE_LIST 缓存

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_012_000 | 场景联动不存在 |

### 3.3 更新场景联动状态

- **路径**: PUT /iot/scene-rule/update-status
- **权限**: iot:scene-rule:update
- **说明**: 启用或禁用一个场景联动

**请求参数 (IotSceneRuleUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| id | Long | 是 | @NotNull | 场景联动编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 目标状态（1 开启、0 禁用） |

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验场景存在（否则 RULE_SCENE_NOT_EXISTS）
2. 按 id 仅更新 status 字段
3. 启用时：查询完整场景信息并注册定时触发器；禁用时：调用 timerHandler.pauseTimerTriggers 暂停定时触发器
4. 清除 SCENE_RULE_LIST 缓存

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_012_000 | 场景联动不存在 |

### 3.4 删除场景联动

- **路径**: DELETE /iot/scene-rule/delete
- **权限**: iot:scene-rule:delete
- **说明**: 删除一个场景联动

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验场景存在（否则 RULE_SCENE_NOT_EXISTS）
2. 按 id 删除记录
3. 调用 timerHandler.unregisterTimerTriggers 注销对应的定时触发器
4. 清除 SCENE_RULE_LIST 缓存

**错误码**:

| 错误码 | 说明 |
|---|---|
| 1_050_012_000 | 场景联动不存在 |

### 3.5 获得场景联动

- **路径**: GET /iot/scene-rule/get
- **权限**: iot:scene-rule:query
- **说明**: 按编号查询单个场景联动

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult\<IotSceneRuleRespVO\>

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 场景编号 |
| name | String | 场景名称 |
| description | String | 场景描述 |
| status | Integer | 场景状态（1 开启、0 禁用） |
| triggers | List\<Trigger\> | 触发器数组（结构见 3.1） |
| actions | List\<Action\> | 执行器数组（结构见 3.1） |
| lastTriggerTime | LocalDateTime | 最后触发时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询记录并转换为 RespVO 返回

### 3.6 获得场景联动分页

- **路径**: GET /iot/scene-rule/page
- **权限**: iot:scene-rule:query
- **说明**: 分页查询场景联动

**请求参数 (IotSceneRulePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam） |
| name | String | 否 | - | 场景名称（模糊匹配） |
| description | String | 否 | - | 场景描述 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 场景状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<IotSceneRuleRespVO\>\>，列表项字段同 3.5

**业务逻辑**:
1. 按名称/描述/状态/创建时间区间条件分页查询

### 3.7 获取场景联动精简信息列表

- **路径**: GET /iot/scene-rule/simple-list
- **权限**: 已认证（无 @PreAuthorize，用于前端下拉选项）
- **说明**: 获取所有启用状态场景联动的精简列表

**请求参数**: 无

**响应**: CommonResult\<List\<IotSceneRuleRespVO\>\>，仅填充以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 场景编号 |
| name | String | 场景名称 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）的场景联动列表
2. 只转换 id、name 两个字段返回

---

## 附：运行时执行机制（非 admin 端点）

以下为规则引擎在设备消息到达时的内部执行链路，供理解上述管理接口的配置如何生效：

**数据流转规则执行（IotDataRuleServiceImpl.executeDataRule）**:
1. 属性上报（PROPERTY_POST）消息：提取 params 中全部属性标识符，逐个匹配规则（含未填 identifier 的"任意属性"规则），按规则 id 去重；其他消息（事件/服务调用/状态）：按单一 identifier 匹配
2. 规则匹配走 Redis 缓存（DATA_RULE_LIST，key 为 deviceId + method + identifier）：查询所有开启规则后在内存中按 deviceId（含 DEVICE_ID_ALL）、method、identifier 过滤
3. 命中规则后跨规则去重 sinkIds（同一消息下多条规则命中同一数据目的只推送一次）
4. 对每个 sinkId 从缓存（DATA_SINK）取配置，数据目的不存在或已禁用则跳过
5. 按 sink.type 路由到对应的 IotDataRuleAction 实现执行推送

**场景联动执行（IotSceneRuleServiceImpl）**:
- 设备消息触发（executeSceneRuleByDevice）：通过设备缓存获取租户上下文 → 按产品/设备匹配启用中的场景（缓存）→ 逐个触发器调用 IotSceneRuleMatcherManager 匹配 + 评估条件组（组间"或"、组内"且"）→ 执行匹配到的 IotSceneRuleAction 动作 → 更新 lastTriggerTime
- 定时触发（executeSceneRuleByTimer）：校验场景存在、启用且含 TIMER 触发器 → 评估条件组（无条件组直接执行）→ 在场景租户上下文中执行动作

**错误码段说明**: 本域错误码位于 1-050-010 / 1-050-011 / 1-050-012 段；`yudao-module-iot-gateway` 的 ErrorCodeConstants（1-051-000-000 段）属于设备认证（DEVICE_AUTH_FAIL、DEVICE_TOKEN_EXPIRED）与设备信息（DEVICE_NOT_EXISTS），与本域接口无直接关联。
