# 告警管理接口 (IotAlertConfigController / IotAlertRecordController)

> IoT 模块的告警管理：维护告警配置（关联场景联动规则、接收人、短信/邮件/站内信通知方式），并记录设备触发产生的告警记录及其处理状态。

## 接口路径前缀

- `/iot/alert-config`  (Controller: IotAlertConfigController)
- `/iot/alert-record`  (Controller: IotAlertRecordController)

## 1. 告警配置管理（IotAlertConfigController）

### 1.1 创建告警配置

- **路径**: POST /iot/alert-config/create
- **权限**: iot:alert-config:create
- **说明**: 新增一条告警配置，校验关联的场景联动规则、接收用户以及接收方式对应的通知模板。

**请求参数 (IotAlertConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 否 | | 配置编号（创建时不传） |
| name | String | 是 | @NotEmpty | 配置名称 |
| description | String | 否 | | 配置描述 |
| level | Integer | 是 | @NotNull | 告警级别 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 配置状态（1 开启 / 2 禁用） |
| sceneRuleIds | List\<Long\> | 是 | @NotEmpty | 关联的场景联动规则编号数组 |
| receiveUserIds | List\<Long\> | 是 | @NotEmpty | 接收的用户编号数组 |
| receiveTypes | List\<Integer\> | 是 | @NotEmpty | 接收的类型数组（1 短信 / 2 邮件 / 3 站内信） |
| smsTemplateCode | String | 否 | | 短信模板编号 |
| mailTemplateCode | String | 否 | | 邮件模板编号 |
| notifyTemplateCode | String | 否 | | 站内信模板编号 |

**响应**: CommonResult\<Long\>（新配置的编号）

**业务逻辑**: 1. 调用 IotSceneRuleService.validateSceneRuleList 校验关联的场景联动规则存在；2. 调用 AdminUserApi.validateUserList 校验接收用户存在；3. 校验接收方式对应模板：选了短信(1)必须有 smsTemplateCode，选了邮件(2)必须有 mailTemplateCode，选了站内信(3)必须有 notifyTemplateCode，缺失则抛对应错误码；4. 转换为 IotAlertConfigDO 插入数据库；5. 返回新配置编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_013_001 | 已选择短信接收方式，短信模板不能为空 |
| 1_050_013_002 | 已选择邮件接收方式，邮件模板不能为空 |
| 1_050_013_003 | 已选择站内信接收方式，站内信模板不能为空 |

### 1.2 更新告警配置

- **路径**: PUT /iot/alert-config/update
- **权限**: iot:alert-config:update
- **说明**: 修改已存在的告警配置，校验逻辑与创建一致。

**请求参数 (IotAlertConfigSaveReqVO)**: 与 1.1 相同，id 必传。

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 校验配置编号对应的配置存在，不存在抛 ALERT_CONFIG_NOT_EXISTS；2. 校验场景联动规则、接收用户存在；3. 校验接收方式对应模板编号（同创建）；4. 转换为 IotAlertConfigDO 按 id 更新。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_013_000 | IoT 告警配置不存在 |
| 1_050_013_001 | 已选择短信接收方式，短信模板不能为空 |
| 1_050_013_002 | 已选择邮件接收方式，邮件模板不能为空 |
| 1_050_013_003 | 已选择站内信接收方式，站内信模板不能为空 |

### 1.3 删除告警配置

- **路径**: DELETE /iot/alert-config/delete
- **权限**: iot:alert-config:delete
- **说明**: 按编号删除告警配置。

**请求参数**: 无（Query 参数 id：编号，Long，必填）

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 校验配置存在，不存在抛 ALERT_CONFIG_NOT_EXISTS；2. 按编号删除。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_013_000 | IoT 告警配置不存在 |

### 1.4 获得告警配置详情

- **路径**: GET /iot/alert-config/get
- **权限**: iot:alert-config:query
- **说明**: 按编号查询单条告警配置详情。

**请求参数**: 无（Query 参数 id：编号，Long，必填）

**响应**: CommonResult\<IotAlertConfigRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 配置编号 |
| name | String | 配置名称 |
| description | String | 配置描述 |
| level | Integer | 告警级别 |
| status | Integer | 配置状态 |
| sceneRuleIds | List\<Long\> | 关联的场景联动规则编号数组 |
| receiveUserIds | List\<Long\> | 接收的用户编号数组 |
| receiveUserNames | List\<String\> | 接收的用户名称数组 |
| receiveTypes | List\<Integer\> | 接收的类型数组（1 短信 / 2 邮件 / 3 站内信） |
| smsTemplateCode | String | 短信模板编号 |
| mailTemplateCode | String | 邮件模板编号 |
| notifyTemplateCode | String | 站内信模板编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询 IotAlertConfigDO；2. 转换为 RespVO 返回（该端点不填充 receiveUserNames）。

### 1.5 获得告警配置分页

- **路径**: GET /iot/alert-config/page
- **权限**: iot:alert-config:query
- **说明**: 分页查询告警配置，并批量翻译接收用户的昵称。

**请求参数 (IotAlertConfigPageReqVO，继承 PageParam: pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| name | String | 否 | | 配置名称（模糊匹配） |
| status | Integer | 否 | | 配置状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |

**响应**: CommonResult\<PageResult\<IotAlertConfigRespVO\>\>，列表项字段同 1.4。

**业务逻辑**: 1. 按条件分页查询 IotAlertConfigDO；2. 收集结果中所有配置的 receiveUserIds，调用 AdminUserApi.getUserMap 批量获取用户信息；3. 将用户昵称填充到每条记录的 receiveUserNames 字段后返回。

### 1.6 获得告警配置简单列表

- **路径**: GET /iot/alert-config/simple-list
- **权限**: iot:alert-config:query
- **说明**: 获取所有开启状态的告警配置精简列表，用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult\<List\<IotAlertConfigRespVO\>\>（仅填充 id、name 两个字段）

**业务逻辑**: 1. 查询状态为开启（CommonStatusEnum.ENABLE）的配置列表；2. 仅返回每条配置的 id、name。

## 2. 告警记录管理（IotAlertRecordController）

告警记录由场景联动规则触发时由系统内部创建（IotAlertRecordService.createAlertRecord），管理后台仅提供查询与处理能力。

### 2.1 获得告警记录详情

- **路径**: GET /iot/alert-record/get
- **权限**: iot:alert-record:query
- **说明**: 按编号查询单条告警记录。

**请求参数**: 无（Query 参数 id：编号，Long，必填）

**响应**: CommonResult\<IotAlertRecordRespVO\>

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| configId | Long | 告警配置编号 |
| configName | String | 告警名称（配置名称快照） |
| configLevel | Integer | 告警级别 |
| productId | Long | 产品编号 |
| deviceId | Long | 设备编号 |
| deviceMessage | IotDeviceMessage | 触发的设备消息 |
| processStatus | Boolean | 是否处理 |
| processRemark | String | 处理结果（备注） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询 IotAlertRecordDO；2. 转换为 RespVO 返回。

### 2.2 获得告警记录分页

- **路径**: GET /iot/alert-record/page
- **权限**: iot:alert-record:query
- **说明**: 按配置、级别、产品、设备、处理状态、时间等条件分页查询告警记录。

**请求参数 (IotAlertRecordPageReqVO，继承 PageParam: pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| configId | Long | 否 | | 告警配置编号 |
| configLevel | Integer | 否 | | 告警级别 |
| productId | Long | 否 | | 产品编号 |
| deviceId | String | 否 | | 设备编号 |
| processStatus | Boolean | 否 | | 是否处理 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |

**响应**: CommonResult\<PageResult\<IotAlertRecordRespVO\>\>，列表项字段同 2.1。

**业务逻辑**: 1. 按条件分页查询 IotAlertRecordDO；2. 转换为 RespVO 分页返回。

### 2.3 处理告警记录

- **路径**: PUT /iot/alert-record/process
- **权限**: iot:alert-record:process
- **说明**: 将单条告警记录标记为已处理并填写处理备注。

**请求参数 (IotAlertRecordProcessReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @NotNull | 记录编号 |
| processRemark | String | 是（Schema 标注必填，无校验注解） | | 处理结果（备注） |

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 将记录编号包装为单元素集合，调用 processAlertRecordList；2. 若集合为空直接返回；3. 批量更新记录，置 processStatus = true 并写入 processRemark。
