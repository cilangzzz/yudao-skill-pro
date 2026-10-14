# OTA 升级接口 (IotOtaFirmwareController / IotOtaTaskController / IotOtaTaskRecordController)

> IoT 模块的 OTA 升级：管理固件（上传 URL、自动计算文件 MD5 签名）、创建升级任务（按全部/指定设备圈定范围并批量生成升级记录）、跟踪设备升级记录的状态与进度，并支持任务/记录的取消。

## 接口路径前缀

- `/iot/ota/firmware`  (Controller: IotOtaFirmwareController)
- `/iot/ota/task`  (Controller: IotOtaTaskController)
- `/iot/ota/task/record`  (Controller: IotOtaTaskRecordController)

## 1. OTA 固件管理（IotOtaFirmwareController）

### 1.1 创建 OTA 固件

- **路径**: POST /iot/ota/firmware/create
- **权限**: iot:ota-firmware:create
- **说明**: 新增一个 OTA 固件，同一产品下版本号不可重复，创建时自动下载文件计算大小与 MD5 签名。

**请求参数 (IotOtaFirmwareCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| name | String | 是 | @NotEmpty | 固件名称 |
| description | String | 否 | | 固件描述 |
| version | String | 是 | @NotEmpty | 版本号 |
| productId | Long | 是 | @NotNull | 产品编号 |
| fileUrl | String | 是 | @NotEmpty、@URL | 固件文件 URL |

**响应**: CommonResult\<Long\>（新固件的编号）

**业务逻辑**: 1. 按 productId + version 查询固件，已存在则抛产品版本号重复错误；2. 校验产品存在；3. 转换为 IotOtaFirmwareDO，通过 HttpUtil 下载 fileUrl 文件字节，计算文件大小 fileSize，并用 MD5 算法计算签名写入 fileDigestAlgorithm/fileDigestValue（下载或计算失败则抛出运行时异常）；4. 插入数据库；5. 返回新固件编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_008_000 | 固件信息不存在 |
| 1_050_008_001 | 产品版本号重复 |

### 1.2 更新 OTA 固件

- **路径**: PUT /iot/ota/firmware/update
- **权限**: iot:ota-firmware:update
- **说明**: 修改固件名称与描述（不支持改版本号和文件）。

**请求参数 (IotOtaFirmwareUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @NotNull | 固件编号 |
| name | String | 否 | | 固件名称 |
| description | String | 否 | | 固件描述 |

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 校验固件存在，不存在抛固件不存在错误；2. 转换为 IotOtaFirmwareDO 按 id 更新。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_008_000 | 固件信息不存在 |

### 1.3 删除 OTA 固件

- **路径**: DELETE /iot/ota/firmware/delete
- **权限**: iot:ota-firmware:delete
- **说明**: 按编号删除固件，存在进行中升级任务时不允许删除。

**请求参数**: 无（Query 参数 id：固件编号，Long，必填）

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 校验固件存在；2. 统计该固件下状态为进行中（IN_PROGRESS）的升级任务数量，大于 0 则抛删除失败错误；3. 按编号删除。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_008_000 | 固件信息不存在 |
| 1_050_008_002 | 删除 OTA 固件失败，原因：存在进行中的升级任务 |

### 1.4 获得 OTA 固件

- **路径**: GET /iot/ota/firmware/get
- **权限**: iot:ota-firmware:query
- **说明**: 按编号获取固件详情，附带产品名称。

**请求参数**: 无（Query 参数 id：固件编号，Long，必填）

**响应**: CommonResult\<IotOtaFirmwareRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 固件编号 |
| name | String | 固件名称 |
| description | String | 固件描述 |
| version | String | 版本号 |
| productId | Long | 产品编号 |
| productName | String | 产品名称（根据 productId 查询产品补充） |
| fileUrl | String | 固件文件 URL |
| fileSize | Long | 固件文件大小 |
| fileDigestAlgorithm | String | 固件文件签名算法（MD5） |
| fileDigestValue | String | 固件文件签名结果 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**: 1. 按编号查询固件，不存在返回 null；2. 根据 productId 查询产品，将产品名称填充到响应 VO 中返回。

### 1.5 获得 OTA 固件分页

- **路径**: GET /iot/ota/firmware/page
- **权限**: iot:ota-firmware:query
- **说明**: 分页查询固件列表，支持名称、产品、创建时间过滤。

**请求参数 (IotOtaFirmwarePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| pageNo | Integer | 否 | | 页码（继承 PageParam） |
| pageSize | Integer | 否 | | 每页条数（继承 PageParam） |
| name | String | 否 | | 固件名称（模糊匹配） |
| productId | String | 否 | | 产品标识 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<IotOtaFirmwareRespVO\>\>（字段同 1.4 响应，分页查询不填充 productName）

**业务逻辑**: 1. 按查询条件分页查询固件；2. 转换为 IotOtaFirmwareRespVO 分页返回。

## 2. OTA 升级任务管理（IotOtaTaskController）

### 2.1 创建 OTA 升级任务

- **路径**: POST /iot/ota/task/create
- **权限**: iot:ota-task:create
- **说明**: 针对某个固件创建升级任务，圈定全部或指定设备，并为每台设备批量生成升级记录。

**请求参数 (IotOtaTaskCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| name | String | 是 | @NotEmpty | 任务名称 |
| description | String | 否 | | 任务描述 |
| firmwareId | Long | 是 | @NotNull | 固件编号 |
| deviceScope | Integer | 是 | @NotNull、@InEnum(IotOtaTaskDeviceScopeEnum) | 升级范围（1 全部设备 / 2 指定设备） |
| deviceIds | List\<Long\> | 否 | | 选中的设备编号数组（指定设备时必传） |

**响应**: CommonResult\<Long\>（新任务的编号）

**业务逻辑**: 1. 校验固件存在；2. 校验同一固件下任务名称不重复；3. 校验设备范围：指定设备(SELECT)时校验设备存在且属于固件对应产品（否则按设备不存在处理）、设备不能已是该固件版本、设备不能处于升级中；全部设备(ALL)时取该产品下全部设备，移除已是该固件版本和升级中的设备，若无可升级设备则报错；4. 插入任务记录，状态置为进行中（IN_PROGRESS），记录设备总数 deviceTotalCount，成功数 deviceSuccessCount 初始为 0；5. 为每台设备批量生成升级记录（状态待推送 PENDING、进度 0，记录来源固件 fromFirmwareId）；6. 返回新任务编号。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_008_000 | 固件信息不存在 |
| 1_050_003_000 | 设备不存在（设备不属于该产品时抛出） |
| 1_050_008_100 | 升级任务不存在 |
| 1_050_008_101 | 创建 OTA 任务失败，原因：任务名称重复 |
| 1_050_008_102 | 创建 OTA 任务失败，原因：设备({})已经是该固件版本 |
| 1_050_008_102 | 创建 OTA 任务失败，原因：设备({})已经在升级中...（源码中与上一条错误码数值相同） |
| 1_050_008_103 | 创建 OTA 任务失败，原因：没有可升级的设备 |

### 2.2 取消 OTA 升级任务

- **路径**: POST /iot/ota/task/cancel
- **权限**: iot:ota-task:cancel
- **说明**: 取消进行中的升级任务，并同步取消其下所有进行中的升级记录。

**请求参数**: 无（Query 参数 id：升级任务编号，Long，必填）

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 校验任务存在，不存在抛任务不存在错误；2. 校验任务状态为进行中，否则抛取消失败错误；3. 更新任务状态为已取消（CANCELED）；4. 查询该任务下处于进行中状态（待推送/已推送/升级中）的记录，批量更新为已取消，描述写为「因任务取消」。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_008_100 | 升级任务不存在 |
| 1_050_008_104 | 取消 OTA 任务失败，原因：任务状态不是进行中 |

### 2.3 获得 OTA 升级任务分页

- **路径**: GET /iot/ota/task/page
- **权限**: iot:ota-task:query
- **说明**: 分页查询升级任务列表。

**请求参数 (IotOtaTaskPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| pageNo | Integer | 否 | | 页码（继承 PageParam） |
| pageSize | Integer | 否 | | 每页条数（继承 PageParam） |
| name | String | 否 | | 任务名称（模糊匹配） |
| firmwareId | Long | 否 | | 固件编号 |

**响应**: CommonResult\<PageResult\<IotOtaTaskRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 任务编号 |
| name | String | 任务名称 |
| description | String | 任务描述 |
| firmwareId | Long | 固件编号 |
| status | Integer | 任务状态（10 进行中 / 20 已结束 / 30 已取消） |
| deviceScope | Integer | 升级范围（1 全部设备 / 2 指定设备） |
| deviceTotalCount | Integer | 设备总共数量 |
| deviceSuccessCount | Integer | 设备成功数量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按查询条件分页查询任务；2. 转换为 IotOtaTaskRespVO 分页返回。

### 2.4 获得 OTA 升级任务

- **路径**: GET /iot/ota/task/get
- **权限**: iot:ota-task:query
- **说明**: 按编号获取升级任务详情。

**请求参数**: 无（Query 参数 id：升级任务编号，Long，必填）

**响应**: CommonResult\<IotOtaTaskRespVO\>（字段同 2.3）

**业务逻辑**: 1. 按编号查询任务并转换为响应 VO 返回。

## 3. OTA 升级记录管理（IotOtaTaskRecordController）

### 3.1 获得 OTA 升级记录状态统计

- **路径**: GET /iot/ota/task/record/get-status-statistics
- **权限**: iot:ota-task-record:query
- **说明**: 按固件或任务统计各升级状态的设备数量，返回 Map（状态 -> 数量）。

**请求参数**: 无（Query 参数 firmwareId：固件编号，Long，可选；taskId：升级任务编号，Long，可选）

**响应**: CommonResult\<Map\<Integer, Long\>\>（key 为升级记录状态：0 待推送 / 10 已推送 / 20 升级中 / 30 升级成功 / 40 升级失败 / 50 已取消，value 为设备数量，全状态初始化为 0）

**业务逻辑**: 1. 按状态枚举初始化所有状态的计数为 0；2. 按 firmwareId、taskId 查询升级记录；3. 按设备分组后，每台设备按优先级（成功 > 待推送/已推送/升级中 > 失败 > 取消）归入第一个命中的状态，避免一台设备被重复统计；4. 返回状态统计 Map。

### 3.2 获得 OTA 升级记录分页

- **路径**: GET /iot/ota/task/record/page
- **权限**: iot:ota-task-record:query
- **说明**: 分页查询升级记录，附带设备名称与来源固件版本。

**请求参数 (IotOtaTaskRecordPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| pageNo | Integer | 否 | | 页码（继承 PageParam） |
| pageSize | Integer | 否 | | 每页条数（继承 PageParam） |
| taskId | Long | 否 | | 升级任务编号 |
| status | Integer | 否 | @InEnum(IotOtaTaskRecordStatusEnum) | 升级记录状态 |

**响应**: CommonResult\<PageResult\<IotOtaTaskRecordRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| firmwareId | Long | 固件编号（目标固件） |
| taskId | Long | 任务编号 |
| deviceId | Long | 设备编号 |
| deviceName | String | 设备名称（根据 deviceId 查询设备补充） |
| fromFirmwareId | Long | 来源的固件编号（升级前固件） |
| fromFirmwareVersion | String | 来源固件版本（根据 fromFirmwareId 查询固件补充） |
| status | Integer | 升级状态（0 待推送 / 10 已推送 / 20 升级中 / 30 升级成功 / 40 升级失败 / 50 已取消） |
| progress | Integer | 升级进度，百分比 |
| description | String | 升级进度描述 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**: 1. 按查询条件分页查询升级记录，空结果直接返回空分页；2. 批量查询记录中来源固件（fromFirmwareId）对应的固件 Map 和设备（deviceId）对应的设备 Map；3. 将来源固件版本、设备名称填充到各响应 VO 中返回。

### 3.3 获得 OTA 升级记录

- **路径**: GET /iot/ota/task/record/get
- **权限**: iot:ota-task-record:query
- **说明**: 按编号获取单条升级记录详情。

**请求参数**: 无（Query 参数 id：升级记录编号，Long，必填）

**响应**: CommonResult\<IotOtaTaskRecordRespVO\>（字段同 3.2，不填充 deviceName/fromFirmwareVersion）

**业务逻辑**: 1. 按编号查询记录并转换为响应 VO 返回。

### 3.4 取消 OTA 升级记录

- **路径**: PUT /iot/ota/task/record/cancel
- **权限**: iot:ota-task-record:cancel
- **说明**: 取消单台设备的升级记录，任务下记录全部结束时同步结束任务。

**请求参数**: 无（Query 参数 id：升级记录编号，Long，必填）

**响应**: CommonResult\<Boolean\>（true 表示成功）

**业务逻辑**: 1. 校验记录存在，不存在抛记录不存在错误；2. 以记录 id + 进行中状态为条件更新为已取消（CANCELED），描述写为「单条记录取消」，更新行数为 0 时抛取消失败（状态不是进行中）错误；3. 检查该任务下是否还有进行中的记录，没有则调用 updateOtaTaskStatusEnd 将任务状态更新为已结束（END）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_008_200 | 升级记录不存在 |
| 1_050_008_201 | 取消 OTA 升级记录失败，原因：记录状态不是进行中 |
