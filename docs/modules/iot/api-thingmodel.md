# 产品物模型接口 (IotThingModelController)

> 管理产品的物模型功能定义（属性 / 服务 / 事件），并提供 TSL（物模型语言）聚合查询，供设备接入与数据存储使用。

## 接口路径前缀

/iot/thing-model  (Controller: IotThingModelController)

## 1. 物模型管理（增删改查）

### 1.1 创建产品物模型

- **路径**: POST /iot/thing-model/create
- **权限**: iot:thing-model:create
- **说明**: 为指定产品新增一条物模型功能定义（属性、服务或事件）。

**请求参数 (IotThingModelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| productId | Long | 是 | @NotNull | 产品 ID |
| productKey | String | 是 | @NotEmpty | 产品标识（ProductKey） |
| identifier | String | 是 | @NotEmpty | 功能标识（同一产品下唯一，不能为系统保留字） |
| name | String | 是 | @NotEmpty | 功能名称（同一产品下唯一） |
| description | String | 否 | - | 功能描述 |
| type | Integer | 是 | @NotNull、@InEnum(IotThingModelTypeEnum) | 功能类型：1 属性、2 服务、3 事件 |
| property | ThingModelProperty | 否 | @Valid | 属性定义，type=1 时使用 |
| service | ThingModelService | 否 | @Valid | 服务定义，type=2 时使用 |
| event | ThingModelEvent | 否 | @Valid | 事件定义，type=3 时使用 |

**ThingModelProperty 字段**（dataSpecs 与 dataSpecsList 必须传入且只能传入一个）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| identifier | String | 是 | @NotEmpty、@Pattern（字母开头，仅字母/数字/下划线，长度 ≤ 32） | 属性标识符 |
| name | String | 是 | @NotEmpty | 属性名称 |
| accessMode | String | 是 | @NotEmpty、@InEnum(IotThingModelAccessModeEnum) | 云端可对该属性进行的操作类型（读 / 读写） |
| required | Boolean | 否 | - | 是否标准品类的必选属性 |
| dataType | String | 是 | @NotEmpty、@InEnum(IotDataSpecsDataTypeEnum) | 参数值的数据类型（int/float/double/enum/bool/text/date/array/struct 等） |
| dataSpecs | ThingModelDataSpecs | 否 | - | 非列表型（int、float、double、text、date、array）的数据规范 |
| dataSpecsList | List&lt;ThingModelDataSpecs&gt; | 否 | - | 列表型（enum、bool、struct）的数据规范 |

**ThingModelService 字段**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| identifier | String | 是 | @NotEmpty、@Pattern（字母开头，仅字母/数字/下划线，长度 ≤ 32） | 服务标识符 |
| name | String | 是 | @NotEmpty | 服务名称 |
| required | Boolean | 否 | - | 是否标准品类的必选服务 |
| callType | String | 是 | @NotEmpty、@InEnum(IotThingModelServiceCallTypeEnum) | 调用类型（同步 / 异步等） |
| inputParams | List&lt;ThingModelParam&gt; | 否 | @Valid | 服务的输入参数 |
| outputParams | List&lt;ThingModelParam&gt; | 否 | @Valid | 服务的输出参数 |
| method | String | 否 | - | 标识设备需要执行的具体操作 |

**ThingModelEvent 字段**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| identifier | String | 是 | @NotEmpty、@Pattern（字母开头，仅字母/数字/下划线，长度 ≤ 32） | 事件标识符 |
| name | String | 是 | @NotEmpty | 事件名称 |
| required | Boolean | 否 | - | 是否标准品类的必选事件 |
| type | String | 是 | @NotEmpty、@InEnum(IotThingModelServiceEventTypeEnum) | 事件类型（info/alert/error 等） |
| outputParams | List&lt;ThingModelParam&gt; | 否 | @Valid | 事件的输出参数 |
| method | String | 否 | - | 标识设备需要执行的具体操作 |

**响应**: CommonResult&lt;Long&gt; —— 新增物模型的编号 id

**业务逻辑**:
1. 校验功能标识符在同一产品下唯一；创建时标识符不能使用系统保留字（set、get、post、property、event、time、value），否则报 THING_MODEL_IDENTIFIER_INVALID。
2. 校验功能名称在同一产品下唯一，重复则报 THING_MODEL_NAME_EXISTS。
3. 校验产品存在（否则 PRODUCT_NOT_EXISTS），且产品不能处于“已发布”状态，发布状态下不允许新增功能。
4. 通过 IotThingModelConvert 将 ReqVO 转换为 IotThingModelDO 并插入数据库。
5. 删除该产品在 Redis 中的物模型列表缓存（THING_MODEL_LIST），保证缓存一致性。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_001_000 | 产品不存在 |
| 1_050_001_003 | 产品状是发布状态，不允许操作物模型 |
| 1_050_002_002 | 存在重复的功能标识符。 |
| 1_050_002_003 | 存在重复的功能名称。 |
| 1_050_002_003 | 产品物模型标识无效（源码中该错误码与“存在重复的功能名称”同值） |

### 1.2 更新产品物模型

- **路径**: PUT /iot/thing-model/update
- **权限**: iot:thing-model:update
- **说明**: 更新指定物模型功能定义，并同步关联的 Modbus 点位冗余字段。

**请求参数 (IotThingModelSaveReqVO)**: 同 1.1（id 必传用于定位记录）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验物模型功能是否存在，不存在则报 THING_MODEL_NOT_EXISTS。
2. 校验功能标识符在同一产品下唯一（排除自身记录）。
3. 校验产品存在且不能处于“已发布”状态，发布状态下不允许操作功能。
4. 更新数据库记录。
5. 同步更新关联 Modbus 点位中的冗余字段（identifier、name），保持点位与物模型一致。
6. 删除该产品的物模型列表缓存（THING_MODEL_LIST）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_001_000 | 产品不存在 |
| 1_050_001_003 | 产品状是发布状态，不允许操作物模型 |
| 1_050_002_000 | 产品物模型不存在 |
| 1_050_002_002 | 存在重复的功能标识符。 |

### 1.3 删除产品物模型

- **路径**: DELETE /iot/thing-model/delete
- **权限**: iot:thing-model:delete
- **说明**: 按 id 删除物模型功能定义。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @RequestParam(required = true) | 物模型编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验物模型功能是否存在，不存在则报 THING_MODEL_NOT_EXISTS。
2. 校验所属产品不能处于“已发布”状态，发布状态下不允许删除功能。
3. 删除数据库记录。
4. 删除该产品的物模型列表缓存（THING_MODEL_LIST）。

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_050_001_003 | 产品状是发布状态，不允许操作物模型 |
| 1_050_002_000 | 产品物模型不存在 |

### 1.4 获得产品物模型

- **路径**: GET /iot/thing-model/get
- **权限**: iot:thing-model:query
- **说明**: 按编号查询单条物模型功能定义详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @RequestParam(required = true) | 物模型编号 |

**响应**: CommonResult&lt;IotThingModelRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| productId | Long | 产品编号 |
| productKey | String | 产品标识（ProductKey） |
| identifier | String | 功能标识 |
| name | String | 功能名称 |
| description | String | 功能描述 |
| type | Integer | 功能类型：1 属性、2 服务、3 事件 |
| property | ThingModelProperty | 属性定义（结构同 1.1） |
| event | ThingModelEvent | 事件定义（结构同 1.1） |
| service | ThingModelService | 服务定义（结构同 1.1） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 IotThingModelDO，记录不存在时返回 null。
2. 通过 BeanUtils 将 DO 转换为 IotThingModelRespVO 返回；该查询无额外校验与缓存逻辑，直接读库。

## 2. 物模型查询（TSL / 列表 / 分页）

### 2.1 获得产品物模型 TSL

- **路径**: GET /iot/thing-model/get-tsl
- **权限**: iot:thing-model:query
- **说明**: 按产品聚合查询完整 TSL，将物模型定义拆分为属性、服务、事件三组返回。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| productId | Long | 是 | @RequestParam(required = true) | 产品 ID |

**响应**: CommonResult&lt;IotThingModelTSLRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| productId | Long | 产品编号 |
| productKey | String | 产品标识（ProductKey） |
| properties | List&lt;ThingModelProperty&gt; | 属性列表（结构同 1.1 的 ThingModelProperty） |
| services | List&lt;ThingModelService&gt; | 服务列表（结构同 1.1 的 ThingModelService） |
| events | List&lt;ThingModelEvent&gt; | 事件列表（结构同 1.1 的 ThingModelEvent） |

**业务逻辑**:
1. 查询产品信息，产品不存在时直接返回 null（不抛异常）。
2. 以产品 id、productKey 初始化 IotThingModelTSLRespVO。
3. 查询该产品下全部物模型定义列表。
4. 按功能类型 type 过滤：type=1（属性）取出 property、type=2（服务）取出 service、type=3（事件）取出 event，分别填充 properties、services、events。

### 2.2 获得产品物模型列表

- **路径**: GET /iot/thing-model/list
- **权限**: iot:thing-model:query
- **说明**: 按条件查询某产品下的物模型定义列表（不分页）。

**请求参数 (IotThingModelListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| productId | Long | 是 | @NotNull | 产品编号（精确匹配） |
| identifier | String | 否 | - | 功能标识（精确匹配，条件成立才拼接） |
| name | String | 否 | - | 功能名称（模糊匹配，条件成立才拼接） |
| type | Integer | 否 | @InEnum(IotThingModelTypeEnum) | 功能类型（精确匹配，条件成立才拼接） |

**响应**: CommonResult&lt;List&lt;IotThingModelRespVO&gt;&gt; —— 字段结构同 1.4

**业务逻辑**:
1. 按 productId（必填）、identifier（精确）、name（模糊）、type（精确）条件拼接查询。
2. 按 id 倒序返回列表，并通过 BeanUtils 转换为 RespVO 列表。

### 2.3 获得产品物模型分页

- **路径**: GET /iot/thing-model/page
- **权限**: iot:thing-model:query
- **说明**: 分页查询某产品下的物模型功能定义。

**请求参数 (IotThingModelPageReqVO)**（继承 PageParam）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| pageNo | Integer | 否 | -（PageParam 默认值 1） | 页码 |
| pageSize | Integer | 否 | -（PageParam 默认值 10） | 每页条数 |
| productId | Long | 是 | @NotNull | 产品编号（精确匹配） |
| identifier | String | 否 | - | 功能标识（精确匹配，条件成立才拼接） |
| name | String | 否 | - | 功能名称（模糊匹配，条件成立才拼接） |
| type | Integer | 否 | @InEnum(IotThingModelTypeEnum) | 功能类型（精确匹配，条件成立才拼接） |

**响应**: CommonResult&lt;PageResult&lt;IotThingModelRespVO&gt;&gt; —— list 内字段结构同 1.4

**业务逻辑**:
1. 按 productId（必填）、identifier（精确）、name（模糊）、type（精确）条件分页查询。
2. 按 id 倒序排列，返回 PageResult 并通过 BeanUtils 转换为 RespVO 分页结果。

## 附：域相关错误码汇总（1-050-002 段）

| 错误码 | 说明 |
|--------|------|
| 1_050_002_000 | 产品物模型不存在 |
| 1_050_002_001 | ProductKey 对应的产品物模型已存在（已定义，当前物模型流程未使用） |
| 1_050_002_002 | 存在重复的功能标识符。 |
| 1_050_002_003 | 存在重复的功能名称。 |
| 1_050_002_003 | 产品物模型标识无效（源码中该错误码与上一条同值） |

> 关联错误码：1_050_001_000（产品不存在）、1_050_001_003（产品状是发布状态，不允许操作物模型），在创建/更新/删除时校验产品状态抛出。
