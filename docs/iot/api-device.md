# 设备管理接口 (IotDeviceController)

> IoT 设备全生命周期管理：设备 CRUD、网关拓扑绑定、分组管理、Modbus 连接与点位配置、设备属性（最新值/历史值）、设备消息查询与模拟发送。

## 接口路径前缀

- /iot/device (Controller: IotDeviceController)
- /iot/device-group (Controller: IotDeviceGroupController)
- /iot/device-modbus-config (Controller: IotDeviceModbusConfigController)
- /iot/device-modbus-point (Controller: IotDeviceModbusPointController)
- /iot/device/property (Controller: IotDevicePropertyController)
- /iot/device/message (Controller: IotDeviceMessageController)

---

## 1. 设备管理（IotDeviceController）

### 1.1 创建设备
- **路径**: POST /iot/device/create
- **权限**: iot:device:create
- **说明**: 在指定产品下创建设备，自动生成设备密钥并初始化为未激活状态。

**请求参数 (IotDeviceSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 设备编号（新增时不传） |
| deviceName | String | 是(业务校验) | - | 设备名称，同一产品下唯一 |
| nickname | String | 否 | - | 备注名称 |
| serialNumber | String | 否 | - | 设备序列号，全局唯一 |
| picUrl | String | 否 | - | 设备图片 |
| groupIds | Set&lt;Long&gt; | 否 | - | 设备分组编号数组 |
| productId | Long | 是(业务校验) | - | 产品编号 |
| gatewayId | Long | 否 | - | 网关设备 ID（网关子设备时需校验） |
| config | String | 否 | - | 设备配置（JSON） |
| latitude | BigDecimal | 否 | @DecimalMin(-90)/@DecimalMax(90) | 设备位置纬度 |
| longitude | BigDecimal | 否 | @DecimalMin(-180)/@DecimalMax(180) | 设备位置经度 |

**响应**: CommonResult&lt;Long&gt; — 设备编号

| 字段 | 类型 | 说明 |
|------|------|------|
| data | Long | 新建设备的编号 |

**业务逻辑**:
1. 校验产品存在，不存在抛 PRODUCT_NOT_EXISTS。
2. 统一校验：设备名称在同一产品（productKey + deviceName，跨租户）下唯一；网关子设备类型时校验 gatewayId 指向的设备存在且为网关类型。
3. 校验设备分组存在。
4. 校验设备序列号全局唯一。
5. 初始化设备（productKey/deviceType 取自产品、生成 deviceSecret、状态默认未激活）并插入数据库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |
| 1_050_003_000 | 设备不存在 |
| 1_050_003_001 | 设备名称在同一产品下必须唯一 |
| 1_050_003_004 | 网关设备不存在 |
| 1_050_003_005 | 设备不是网关设备 |
| 1_050_003_008 | 设备序列号已存在，序列号必须全局唯一 |
| 1_050_005_000 | 设备分组不存在 |

### 1.2 更新设备
- **路径**: PUT /iot/device/update
- **权限**: iot:device:update
- **说明**: 更新设备基础信息，deviceName 与 productId 不允许更新。

**请求参数 (IotDeviceSaveReqVO)**: 同 1.1（id 必传；deviceName/productId 服务端强制置空）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 将 deviceName、productId 置空（不允许更新）。
2. 校验设备存在。
3. 网关子设备类型时校验 gatewayId 指向的设备存在且为网关类型。
4. 校验分组存在、序列号全局唯一（排除自身）。
5. 更新数据库并清空设备相关 Redis 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_003_004 | 网关设备不存在 |
| 1_050_003_005 | 设备不是网关设备 |
| 1_050_003_008 | 设备序列号已存在，序列号必须全局唯一 |
| 1_050_005_000 | 设备分组不存在 |

### 1.3 绑定子设备到网关
- **路径**: PUT /iot/device/bind-gateway
- **权限**: iot:device:update
- **说明**: 将一批子设备批量绑定到指定网关设备，并下发拓扑变更通知。

**请求参数 (IotDeviceBindGatewayReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| subIds | Set&lt;Long&gt; | 是 | @NotEmpty | 子设备编号列表 |
| gatewayId | Long | 是 | @NotNull | 网关设备编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验网关设备存在且设备类型为网关。
2. 逐个校验子设备：类型必须为网关子设备，且未绑定到其他网关。
3. 批量更新子设备的 gatewayId。
4. 清空设备缓存。
5. 向网关下发拓扑变更通知（topo/change，status=创建），通知失败仅记录日志不影响绑定结果。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_003_004 | 网关设备不存在 |
| 1_050_003_005 | 设备不是网关设备 |
| 1_050_003_009 | 设备不是网关子设备类型，无法绑定到网关 |
| 1_050_003_010 | 设备已绑定到其他网关，请先解绑 |

### 1.4 解绑子设备与网关
- **路径**: PUT /iot/device/unbind-gateway
- **权限**: iot:device:update
- **说明**: 将一批子设备从指定网关解绑（gatewayId 置空），并下发拓扑变更通知。

**请求参数 (IotDeviceUnbindGatewayReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| subIds | Set&lt;Long&gt; | 是 | @NotEmpty | 子设备编号列表 |
| gatewayId | Long | 是 | @NotNull | 网关设备编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 查询子设备列表，过滤掉 gatewayId 与传入网关不一致的设备。
2. 批量将这些设备的 gatewayId 更新为 null。
3. 清空设备缓存。
4. 向网关下发拓扑变更通知（topo/change，status=删除）。

### 1.5 获取网关的子设备列表
- **路径**: GET /iot/device/sub-device-list
- **权限**: iot:device:query
- **说明**: 按 gatewayId 查询其下全部子设备，并补充产品名称。

**请求参数**: 无（Query 参数 gatewayId：网关设备编号，必填）

**响应**: CommonResult&lt;List&lt;IotDeviceRespVO&gt;&gt; — 字段同 1.11 响应表，且附带 productName（产品名称）

**业务逻辑**:
1. 按 gatewayId 查询子设备列表，为空直接返回空集合。
2. 查询全部产品建立映射，为每个子设备补充 productName 后返回。

### 1.6 获取未绑定网关的子设备分页
- **路径**: GET /iot/device/unbound-sub-device-page
- **权限**: iot:device:query
- **说明**: 分页查询 gatewayId 为空的网关子设备（用于绑定网关时的候选列表）。

**请求参数 (IotDevicePageReqVO)**: 同 1.11 请求参数表

**响应**: CommonResult&lt;PageResult&lt;IotDeviceRespVO&gt;&gt; — 字段同 1.11，且附带 productName

**业务逻辑**:
1. 分页查询未绑定网关的子设备。
2. 查询全部产品建立映射，为结果补充 productName 后返回。

### 1.7 更新设备分组
- **路径**: PUT /iot/device/update-group
- **权限**: iot:device:update
- **说明**: 批量将多个设备设置到指定分组集合（覆盖原有分组）。

**请求参数 (IotDeviceUpdateGroupReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Set&lt;Long&gt; | 是 | @NotEmpty | 设备编号列表 |
| groupIds | Set&lt;Long&gt; | 是 | @NotEmpty | 分组编号列表 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 查询并校验设备存在（为空直接返回）。
2. 校验分组存在。
3. 批量更新设备的 groupIds 字段。
4. 清空设备缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_005_000 | 设备分组不存在 |

### 1.8 删除单个设备
- **路径**: DELETE /iot/device/delete
- **权限**: iot:device:delete
- **说明**: 删除单个设备，网关设备存在子设备时禁止删除。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验设备存在。
2. 若为网关设备且其下存在已绑定的子设备，抛 DEVICE_GATEWAY_HAS_SUB 拒绝删除。
3. 删除设备并清空缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_003_002 | 网关设备存在已绑定的子设备，不允许删除 |

### 1.9 删除多个设备
- **路径**: DELETE /iot/device/delete-list
- **权限**: iot:device:delete
- **说明**: 批量删除设备，逐个校验网关子设备约束，事务回滚。

**请求参数**: 无（Query 参数 ids：编号数组，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 查询设备列表（为空直接返回）。
2. 逐个检查：网关设备存在已绑定子设备时抛 DEVICE_GATEWAY_HAS_SUB。
3. 事务内批量删除设备并清空缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_003_002 | 网关设备存在已绑定的子设备，不允许删除 |

### 1.10 获得设备
- **路径**: GET /iot/device/get
- **权限**: iot:device:query
- **说明**: 按编号获取设备详情。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;IotDeviceRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 设备编号 |
| deviceName | String | 设备名称 |
| nickname | String | 设备备注名称 |
| serialNumber | String | 设备序列号 |
| picUrl | String | 设备图片 |
| groupIds | Set&lt;Long&gt; | 设备分组编号数组 |
| productId | Long | 产品编号 |
| productName | String | 产品名称（仅部分接口返回） |
| productKey | String | 产品标识 |
| deviceType | Integer | 设备类型 |
| gatewayId | Long | 网关设备 ID |
| state | Integer | 设备状态（字典 DEVICE_STATE） |
| onlineTime | LocalDateTime | 最后上线时间 |
| offlineTime | LocalDateTime | 最后离线时间 |
| activeTime | LocalDateTime | 设备激活时间 |
| deviceSecret | String | 设备密钥 |
| config | String | 设备配置（JSON） |
| latitude | BigDecimal | 设备位置纬度 |
| longitude | BigDecimal | 设备位置经度 |
| createTime | LocalDateTime | 创建时间 |

### 1.11 获得设备分页
- **路径**: GET /iot/device/page
- **权限**: iot:device:query
- **说明**: 按条件分页查询设备。

**请求参数 (IotDevicePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| deviceName | String | 否 | - | 设备名称（模糊） |
| nickname | String | 否 | - | 备注名称（模糊） |
| productId | Long | 否 | - | 产品编号 |
| deviceType | Integer | 否 | @InEnum(IotProductDeviceTypeEnum) | 设备类型 |
| status | Integer | 否 | @InEnum(IotDeviceStateEnum) | 设备状态 |
| groupId | Long | 否 | - | 设备分组编号 |
| gatewayId | Long | 否 | - | 网关设备 ID |

**响应**: CommonResult&lt;PageResult&lt;IotDeviceRespVO&gt;&gt; — 字段同 1.10

### 1.12 导出设备 Excel
- **路径**: GET /iot/device/export-excel
- **权限**: iot:device:export
- **说明**: 按分页条件导出全部设备数据为 Excel 文件。

**请求参数 (IotDevicePageReqVO)**: 同 1.11

**响应**: Excel 文件流（设备.xls，导出 IotDeviceRespVO 中标注 @ExcelProperty 的字段）

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（不分页导出全部）。
2. 复用分页查询逻辑获取数据。
3. 通过 ExcelUtils 写出 Excel 响应。

### 1.13 获得设备数量
- **路径**: GET /iot/device/count
- **权限**: iot:device:query
- **说明**: 统计指定产品下的设备数量。

**请求参数**: 无（Query 参数 productId：产品编号，必填）

**响应**: CommonResult&lt;Long&gt; — 设备数量

### 1.14 获取设备的精简信息列表
- **路径**: GET /iot/device/simple-list
- **权限**: 已认证（仅登录，用于前端下拉选项）
- **说明**: 按设备类型/产品编号条件查询设备精简列表。

**请求参数**: 无（Query 参数 deviceType：设备类型，可选；productId：产品编号，可选）

**响应**: CommonResult&lt;List&lt;IotDeviceRespVO&gt;&gt; — 仅返回 id、deviceName、productId、state 字段

**业务逻辑**:
1. 按 deviceType、productId 条件查询设备列表。
2. 仅转换出 id、deviceName、productId、state 四个字段返回。

### 1.15 获取设备位置列表
- **路径**: GET /iot/device/location-list
- **权限**: iot:device:query
- **说明**: 获取有经纬度信息的设备列表，用于地图展示。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;IotDeviceRespVO&gt;&gt; — 字段同 1.10，且附带 productName

**业务逻辑**:
1. 查询有位置信息（经纬度非空）的设备列表。
2. 查询全部产品建立映射，补充 productName 后返回。

### 1.16 导入设备
- **路径**: POST /iot/device/import
- **权限**: iot:device:import
- **说明**: 通过 Excel 批量导入设备，支持已存在时选择更新。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| file | MultipartFile | 是 | - | Excel 文件（IotDeviceImportExcelVO） |
| updateSupport | Boolean | 否 | - | 已存在设备时是否支持更新，默认 false |

Excel 行 (IotDeviceImportExcelVO):

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceName | String | 是 | @NotEmpty | 设备名称 |
| parentDeviceName | String | 否 | - | 父设备（网关）名称 |
| productKey | String | 是 | @NotEmpty | 产品标识 |
| groupNames | String | 否 | - | 设备分组名（逗号分隔） |

**响应**: CommonResult&lt;IotDeviceImportRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| createDeviceNames | List&lt;String&gt; | 创建成功的设备名称数组 |
| updateDeviceNames | List&lt;String&gt; | 更新成功的设备名称数组 |
| failureDeviceNames | Map&lt;String, String&gt; | 导入失败的设备集合（key 为设备名称，value 为失败原因） |

**业务逻辑**:
1. 导入数据为空时抛 DEVICE_IMPORT_LIST_IS_EMPTY。
2. 事务内逐行处理：先做字段校验（失败记入 failureDeviceNames）。
3. 按 productKey 校验产品存在；填写了父设备名称时校验其存在且为网关类型。
4. 按分组名称（逗号分隔）逐个校验分组存在并收集 groupId。
5. 设备不存在则调用创建逻辑；已存在且 updateSupport=false 抛 DEVICE_KEY_EXISTS，否则执行更新。
6. 单行失败捕获 ServiceException 记入 failureDeviceNames，不影响其他行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_006 | 导入设备数据不能为空 |
| 1_050_003_003 | 设备标识已经存在（已存在且不允许更新） |
| 1_050_003_004 | 网关设备不存在 |
| 1_050_003_005 | 设备不是网关设备 |
| 1_050_003_008 | 设备序列号已存在，序列号必须全局唯一 |
| 1_050_001_000 | 产品不存在 |
| 1_050_005_000 | 设备分组不存在 |

### 1.17 获得导入设备模板
- **路径**: GET /iot/device/get-import-template
- **权限**: 已认证（仅登录）
- **说明**: 下载设备导入 Excel 模板（内置两行示例数据）。

**请求参数**: 无

**响应**: Excel 文件流（设备导入模板.xls）

### 1.18 获得设备连接信息
- **路径**: GET /iot/device/get-auth-info
- **权限**: iot:device:auth-info
- **说明**: 获取设备连接（MQTT 认证）所需的 clientId/username/password。

**请求参数**: 无（Query 参数 id：设备编号，必填）

**响应**: CommonResult&lt;IotDeviceAuthInfoRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| clientId | String | 客户端 ID（格式 productKey.deviceName） |
| username | String | 用户名（格式 deviceName&productKey） |
| password | String | 密码（基于 deviceSecret 计算的哈希） |

**业务逻辑**:
1. 校验设备存在。
2. 通过 IotDeviceAuthUtils 基于 productKey、deviceName、deviceSecret 生成认证三元组并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |

### 1.19 通过产品标识和设备名称列表获取设备
- **路径**: GET /iot/device/list-by-product-key-and-names
- **权限**: iot:device:query
- **说明**: 按 productKey + 设备名称集合精确查询设备列表。

**请求参数 (IotDeviceByProductKeyAndNamesReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| productKey | String | 是 | @NotBlank | 产品标识 |
| deviceNames | List&lt;String&gt; | 是 | @NotEmpty | 设备名称列表 |

**响应**: CommonResult&lt;List&lt;IotDeviceRespVO&gt;&gt; — 字段同 1.10

**业务逻辑**:
1. productKey 为空或 deviceNames 为空时返回空列表。
2. 按 productKey + deviceNames 条件查询设备列表返回。

---

## 2. 设备分组（IotDeviceGroupController）

### 2.1 创建设备分组
- **路径**: POST /iot/device-group/create
- **权限**: iot:device-group:create
- **说明**: 创建设备分组。

**请求参数 (IotDeviceGroupSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 分组 ID（新增时不传） |
| name | String | 是 | @NotEmpty | 分组名字 |
| status | Integer | 是 | @NotNull | 分组状态（0 开启 / 1 禁用） |
| description | String | 否 | - | 分组描述 |

**响应**: CommonResult&lt;Long&gt; — 分组编号

**业务逻辑**:
1. VO 转换为 DO 后插入数据库，返回分组 ID。

### 2.2 更新设备分组
- **路径**: PUT /iot/device-group/update
- **权限**: iot:device-group:update
- **说明**: 更新设备分组信息。

**请求参数 (IotDeviceGroupSaveReqVO)**: 同 2.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验分组存在。
2. 更新数据库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_005_000 | 设备分组不存在 |

### 2.3 删除设备分组
- **路径**: DELETE /iot/device-group/delete
- **权限**: iot:device-group:delete
- **说明**: 删除设备分组，分组下存在设备时禁止删除。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验分组存在。
2. 统计分组下设备数量，大于 0 时抛 DEVICE_GROUP_DELETE_FAIL_DEVICE_EXISTS。
3. 删除分组。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_005_000 | 设备分组不存在 |
| 1_050_005_001 | 设备分组下存在设备，不允许删除 |

### 2.4 获得设备分组
- **路径**: GET /iot/device-group/get
- **权限**: iot:device-group:query
- **说明**: 按编号获取分组详情。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;IotDeviceGroupRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分组 ID |
| name | String | 分组名字 |
| status | Integer | 分组状态 |
| description | String | 分组描述 |
| createTime | LocalDateTime | 创建时间 |
| deviceCount | Long | 设备数量（仅分页接口填充） |

### 2.5 获得设备分组分页
- **路径**: GET /iot/device-group/page
- **权限**: iot:device-group:query
- **说明**: 按条件分页查询分组，并统计每组的设备数量。

**请求参数 (IotDeviceGroupPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| name | String | 否 | - | 分组名字（模糊） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult&lt;PageResult&lt;IotDeviceGroupRespVO&gt;&gt; — 字段同 2.4（deviceCount 为每组实际设备数）

**业务逻辑**:
1. 分页查询分组列表。
2. 对每个分组调用设备统计接口填充 deviceCount。

### 2.6 获取设备分组的精简信息列表
- **路径**: GET /iot/device-group/simple-list
- **权限**: 已认证（仅登录，用于前端下拉选项）
- **说明**: 获取所有开启状态的分组精简列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;IotDeviceGroupRespVO&gt;&gt; — 仅返回 id、name 字段

**业务逻辑**:
1. 查询状态为开启（ENABLE）的分组列表。
2. 仅转换出 id、name 字段返回。

---

## 3. 设备 Modbus 连接配置（IotDeviceModbusConfigController）

### 3.1 保存设备 Modbus 连接配置
- **路径**: POST /iot/device-modbus-config/save
- **权限**: iot:device:update
- **说明**: 按设备维度保存（新增或更新）Modbus 连接配置，并根据产品协议类型做条件校验。

**请求参数 (IotDeviceModbusConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceId | Long | 是 | @NotNull | 设备编号 |
| ip | String | 条件必填 | Client 模式必填（业务校验） | Modbus 服务器 IP 地址 |
| port | Integer | 条件必填 | Client 模式必填（业务校验） | Modbus 端口 |
| slaveId | Integer | 是 | @NotNull | 从站地址 |
| timeout | Integer | 条件必填 | Client 模式必填（业务校验） | 连接超时时间（毫秒） |
| retryInterval | Integer | 条件必填 | Client 模式必填（业务校验） | 重试间隔（毫秒） |
| mode | Integer | 条件必填 | @InEnum(IotModbusModeEnum)；Server 模式必填 | 工作模式 |
| frameFormat | Integer | 条件必填 | @InEnum(IotModbusFrameFormatEnum)；Server 模式必填 | 数据帧格式 |
| status | Integer | 是 | @NotNull | 状态 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验设备存在。
2. 查询设备所属产品，根据产品 protocolType 条件校验：MODBUS_TCP_CLIENT 模式下 ip/port/timeout/retryInterval 必填；MODBUS_TCP_SERVER 模式下 mode/frameFormat 必填。
3. 按设备编号查询已有配置：不存在则插入，存在则更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_006_002 | Client 模式下，IP 地址不能为空 |
| 1_050_006_003 | Client 模式下，端口不能为空 |
| 1_050_006_004 | Client 模式下，连接超时时间不能为空 |
| 1_050_006_005 | Client 模式下，重试间隔不能为空 |
| 1_050_006_006 | Server 模式下，工作模式不能为空 |
| 1_050_006_007 | Server 模式下，数据帧格式不能为空 |

### 3.2 获得设备 Modbus 连接配置
- **路径**: GET /iot/device-modbus-config/get
- **权限**: iot:device:query
- **说明**: 按主键 id 或设备编号查询 Modbus 连接配置。

**请求参数**: 无（Query 参数 id：编号，可选；deviceId：设备编号，可选，二者传其一）

**响应**: CommonResult&lt;IotDeviceModbusConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键 |
| deviceId | Long | 设备编号 |
| deviceName | String | 设备名称 |
| ip | String | Modbus 服务器 IP 地址 |
| port | Integer | Modbus 端口 |
| slaveId | Integer | 从站地址 |
| timeout | Integer | 连接超时时间（毫秒） |
| retryInterval | Integer | 重试间隔（毫秒） |
| mode | Integer | 工作模式 |
| frameFormat | Integer | 数据帧格式 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. id 非空按 id 查询；否则 deviceId 非空按 deviceId 查询。
2. 转换为 RespVO 返回（无配置时各字段为 null）。

---

## 4. 设备 Modbus 点位配置（IotDeviceModbusPointController）

### 4.1 创建设备 Modbus 点位配置
- **路径**: POST /iot/device-modbus-point/create
- **权限**: iot:device:update
- **说明**: 为设备创建一个 Modbus 点位（物模型属性与寄存器的映射）。

**请求参数 (IotDeviceModbusPointSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 主键（新增时不传） |
| deviceId | Long | 是 | @NotNull | 设备编号 |
| thingModelId | Long | 是 | @NotNull | 物模型属性编号 |
| functionCode | Integer | 是 | @NotNull | Modbus 功能码 |
| registerAddress | Integer | 是 | @NotNull | 寄存器起始地址 |
| registerCount | Integer | 否 | - | 寄存器数量 |
| byteOrder | String | 是 | @NotEmpty | 字节序（如 AB） |
| rawDataType | String | 是 | @NotEmpty | 原始数据类型（如 INT16） |
| scale | BigDecimal | 否 | - | 缩放因子 |
| pollInterval | Integer | 否 | - | 轮询间隔（毫秒） |
| status | Integer | 是 | @NotNull | 状态 |

**响应**: CommonResult&lt;Long&gt; — 点位编号

**业务逻辑**:
1. 校验设备存在。
2. 校验物模型属性存在。
3. 校验同一设备下该 identifier 的点位唯一。
4. 插入点位（identifier/name 取自物模型属性）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_002_000 | 产品物模型不存在 |
| 1_050_007_001 | 设备 Modbus 点位配置已存在 |

### 4.2 更新设备 Modbus 点位配置
- **路径**: PUT /iot/device-modbus-point/update
- **权限**: iot:device:update
- **说明**: 更新 Modbus 点位配置。

**请求参数 (IotDeviceModbusPointSaveReqVO)**: 同 4.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验点位存在。
2. 校验设备存在、物模型属性存在。
3. 校验同一设备下 identifier 唯一（排除自身）。
4. 更新点位（identifier/name 同步取自物模型属性）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_007_000 | 设备 Modbus 点位配置不存在 |
| 1_050_003_000 | 设备不存在 |
| 1_050_002_000 | 产品物模型不存在 |
| 1_050_007_001 | 设备 Modbus 点位配置已存在 |

### 4.3 删除设备 Modbus 点位配置
- **路径**: DELETE /iot/device-modbus-point/delete
- **权限**: iot:device:update
- **说明**: 删除指定 Modbus 点位配置。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验点位存在。
2. 删除点位。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_007_000 | 设备 Modbus 点位配置不存在 |

### 4.4 获得设备 Modbus 点位配置
- **路径**: GET /iot/device-modbus-point/get
- **权限**: iot:device:query
- **说明**: 按编号获取点位配置详情。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;IotDeviceModbusPointRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键 |
| deviceId | Long | 设备编号 |
| thingModelId | Long | 物模型属性编号 |
| identifier | String | 属性标识符（来自物模型） |
| name | String | 属性名称（来自物模型） |
| functionCode | Integer | Modbus 功能码 |
| registerAddress | Integer | 寄存器起始地址 |
| registerCount | Integer | 寄存器数量 |
| byteOrder | String | 字节序 |
| rawDataType | String | 原始数据类型 |
| scale | BigDecimal | 缩放因子 |
| pollInterval | Integer | 轮询间隔（毫秒） |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

### 4.5 获得设备 Modbus 点位配置分页
- **路径**: GET /iot/device-modbus-point/page
- **权限**: iot:device:query
- **说明**: 按条件分页查询点位配置。

**请求参数 (IotDeviceModbusPointPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| deviceId | Long | 否 | - | 设备编号 |
| identifier | String | 否 | - | 属性标识符 |
| name | String | 否 | - | 属性名称 |
| functionCode | Integer | 否 | - | Modbus 功能码 |
| status | Integer | 否 | - | 状态 |

**响应**: CommonResult&lt;PageResult&lt;IotDeviceModbusPointRespVO&gt;&gt; — 字段同 4.4

---

## 5. 设备属性（IotDevicePropertyController）

### 5.1 获取设备属性最新属性
- **路径**: GET /iot/device/property/get-latest
- **权限**: iot:device:property-query
- **说明**: 获取设备全部物模型属性的最新值（来自 Redis 缓存）。

**请求参数**: 无（Query 参数 deviceId：设备编号，必填）

**响应**: CommonResult&lt;List&lt;IotDevicePropertyDetailRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| identifier | String | 属性标识符 |
| value | Object | 属性值（无上报时为 null） |
| updateTime | Long | 更新时间（毫秒时间戳，无上报时为 null） |
| name | String | 属性名称（来自物模型） |
| dataType | String | 数据类型（来自物模型） |
| dataSpecs | ThingModelDataSpecs | 数据定义 |
| dataSpecsList | List&lt;ThingModelDataSpecs&gt; | 数据定义列表 |

**业务逻辑**:
1. 校验设备存在。
2. 从 Redis 获取设备各属性的最新值。
3. 按 productId 查询属性类型（PROPERTY）的物模型列表。
4. 遍历物模型，拼接属性定义与最新值（无上报记录的属性 value/updateTime 为空）返回。

### 5.2 获取设备属性历史数据列表
- **路径**: GET /iot/device/property/history-list
- **权限**: iot:device:property-query
- **说明**: 从 TDengine 查询指定属性的历史数据列表。

**请求参数 (IotDevicePropertyHistoryListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceId | Long | 是 | @NotNull | 设备编号 |
| identifier | String | 是 | @NotEmpty | 属性标识符 |
| times | LocalDateTime[] | 否 | @Size(min=2, max=2)、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 时间范围 |

**响应**: CommonResult&lt;List&lt;IotDevicePropertyRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| identifier | String | 属性标识符 |
| value | Object | 属性值 |
| updateTime | Long | 更新时间（毫秒时间戳） |

**业务逻辑**:
1. 从 TDengine 按设备分表查询指定属性在时间范围内的历史数据。
2. 若对应表不存在（Table does not exist），返回空列表。

---

## 6. 设备消息（IotDeviceMessageController）

### 6.1 获得设备消息分页
- **路径**: GET /iot/device/message/page
- **权限**: iot:device:message-query
- **说明**: 从 TDengine 分页查询设备上下行消息日志。

**请求参数 (IotDeviceMessagePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| deviceId | Long | 是 | @NotNull | 设备编号 |
| method | String | 否 | @InEnum(IotDeviceMessageMethodEnum) | 消息类型（方法） |
| upstream | Boolean | 否 | - | 是否上行 |
| reply | Boolean | 否 | - | 是否回复 |
| identifier | String | 否 | - | 标识符 |
| times | LocalDateTime[] | 否 | @Size(min=2, max=2)、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 时间范围 |

**响应**: CommonResult&lt;PageResult&lt;IotDeviceMessageRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 消息编号 |
| reportTime | LocalDateTime | 上报时间 |
| ts | LocalDateTime | 记录时间戳 |
| deviceId | Long | 设备编号 |
| serverId | String | 服务（网关节点）编号 |
| upstream | Boolean | 是否上行消息 |
| reply | Boolean | 是否回复消息 |
| identifier | String | 标识符 |
| requestId | String | 请求编号 |
| method | String | 请求方法（如 thing.property.post） |
| params | Object | 请求参数 |
| data | Object | 响应结果 |
| code | Integer | 响应错误码 |
| msg | String | 响应提示 |

**业务逻辑**:
1. 从 TDengine 超级表按条件分页查询消息。
2. 表不存在（Table does not exist）时返回空分页。

### 6.2 获得设备消息对分页
- **路径**: GET /iot/device/message/pair-page
- **权限**: iot:device:message-query
- **说明**: 将请求消息与其回复消息按 requestId 配对后分页返回。

**请求参数 (IotDeviceMessagePageReqVO)**: 同 6.1

**响应**: CommonResult&lt;PageResult&lt;IotDeviceMessageRespPairVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| request | IotDeviceMessageRespVO | 请求消息（字段同 6.1） |
| reply | IotDeviceMessageRespVO | 响应消息（通过 requestId 配对，可能为 null） |

**业务逻辑**:
1. 强制 reply=false 查询请求消息分页，为空直接返回空分页。
2. 提取本页所有 requestId，批量查询该设备对应的 reply 消息并建立映射。
3. 逐条将请求消息与回复消息组装为消息对返回（total 取请求消息总数）。

### 6.3 发送消息
- **路径**: POST /iot/device/message/send
- **权限**: iot:device:message-send
- **说明**: 向设备发送消息（可用于设备模拟，如属性上报、事件上报、状态变更）。

**请求参数 (IotDeviceMessageSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| method | String | 是 | @NotEmpty、@InEnum(IotDeviceMessageMethodEnum) | 请求方法 |
| params | Object | 否 | - | 请求参数（如属性上报的 properties） |
| deviceId | Long | 是 | @NotNull | 设备编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验设备存在。
2. 补充消息字段：生成 messageId、reportTime、绑定 deviceId/tenantId，requestId 缺省取 messageId。
3. 上行消息：直接发送到 MQ（由消费者处理并记录日志）。
4. 下行消息：需要 serverId 路由（从 Redis 获取设备当前连接的网关节点），不存在时抛 DEVICE_DOWNSTREAM_FAILED_SERVER_ID_NULL；存在则发送到对应网关，并异步记录消息日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_003_007 | 下行设备消息失败，原因：设备未连接网关 |
