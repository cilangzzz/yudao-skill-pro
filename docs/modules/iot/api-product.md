# 产品管理接口 (IotProductController / IotProductCategoryController)

> IoT 平台的产品与产品分类管理：产品是设备的模板，定义设备类型、联网方式、协议类型、序列化类型等；创建产品时自动生成 ProductSecret，发布产品时同步生成时序库（TDengine / IoTDB）的超级表数据模型。产品还可配置 JS 数据解析脚本（decode/encode），并在保存前在线调试。

## 接口路径前缀

- `/iot/product` (Controller: IotProductController)
- `/iot/product-category` (Controller: IotProductCategoryController)

## 1. 产品管理（IotProductController）

### 1.1 创建产品

- **路径**: POST /iot/product/create
- **权限**: iot:product:create
- **说明**: 创建产品，自动生成 ProductSecret，初始状态为「开发中」。

**请求参数 (IotProductSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | | 产品编号（新增时不传） |
| name | String | 是 | @NotEmpty | 产品名称 |
| productKey | String | 否 | | 产品 Key |
| categoryId | Long | 是 | @NotNull | 产品分类编号 |
| icon | String | 否 | | 产品图标 |
| picUrl | String | 否 | | 产品图片 |
| description | String | 否 | | 产品描述 |
| deviceType | Integer | 是 | @NotNull、@InEnum(IotProductDeviceTypeEnum) | 设备类型 |
| netType | Integer | 否 | @InEnum(IotNetTypeEnum) | 联网方式 |
| protocolType | String | 是 | @NotEmpty、@InEnum(IotProtocolTypeEnum) | 协议类型 |
| serializeType | String | 是 | @NotEmpty、@InEnum(IotSerializeTypeEnum) | 序列化类型 |
| registerEnabled | Boolean | 是 | @NotNull | 是否开启动态注册 |

**响应**: CommonResult&lt;Long&gt; — 产品编号

**业务逻辑**:
1. 校验 ProductKey 唯一性，已存在则抛出 PRODUCT_KEY_EXISTS 错误。
2. 请求 VO 转换为 IotProductDO，强制设置状态为「开发中」（UNPUBLISHED），并生成随机 ProductSecret（fastSimpleUUID）。
3. 插入数据库，返回产品编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_001 | 产品标识已经存在 |

### 1.2 更新产品

- **路径**: PUT /iot/product/update
- **权限**: iot:product:update
- **说明**: 更新产品基本信息，不允许修改 ProductKey。

**请求参数 (IotProductSaveReqVO)**: 同 1.1，其中 id 必传（产品编号）。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 将请求 VO 中的 productKey 置空，保证不更新产品标识。
2. 校验产品是否存在，不存在抛出 PRODUCT_NOT_EXISTS。
3. 更新数据库，并清除该产品的 Redis 缓存（@CacheEvict PRODUCT）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |

### 1.3 更新产品状态

- **路径**: PUT /iot/product/update-status
- **权限**: iot:product:update
- **说明**: 发布/取消发布产品；发布时同步创建时序库（TDengine / IoTDB）的产品超级表数据模型。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 产品编号 |
| status | Integer | 是 | | 状态（0 开发中 / 1 已发布） |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验产品是否存在，不存在抛出 PRODUCT_NOT_EXISTS。
2. 若目标状态为「已发布」（PUBLISHED），调用 devicePropertyDataService.defineDevicePropertyData 创建产品的超级表数据模型。
3. 更新产品状态（@DSTransactional 事务），并清除该产品的 Redis 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |

### 1.4 删除产品

- **路径**: DELETE /iot/product/delete
- **权限**: iot:product:delete
- **说明**: 删除产品，已发布或存在设备的产品不允许删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 产品编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验产品是否存在，不存在抛出 PRODUCT_NOT_EXISTS。
2. 校验产品状态，若为「已发布」则抛出 PRODUCT_STATUS_NOT_DELETE。
3. 校验产品下是否存在设备（deviceService.getDeviceCountByProductId），存在则抛出 PRODUCT_DELETE_FAIL_HAS_DEVICE。
4. 删除产品，并清除该产品的 Redis 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |
| 1_050_001_002 | 产品是发布状态，不允许删除 |
| 1_050_001_004 | 产品下存在设备，不允许删除 |

### 1.5 获得产品详情

- **路径**: GET /iot/product/get
- **权限**: iot:product:query
- **说明**: 按编号获得产品详情，并拼接产品分类名称。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 产品编号 |

**响应**: CommonResult&lt;IotProductRespVO&gt;（产品不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| productKey | String | 产品标识 |
| productSecret | String | 产品密钥 |
| registerEnabled | Boolean | 是否开启动态注册 |
| categoryId | Long | 产品分类编号 |
| categoryName | String | 产品分类名称（拼接字段） |
| icon | String | 产品图标 |
| picUrl | String | 产品图片 |
| description | String | 产品描述 |
| status | Integer | 产品状态（0 开发中 / 1 已发布） |
| deviceType | Integer | 设备类型 |
| netType | Integer | 联网方式 |
| protocolType | String | 协议类型 |
| serializeType | String | 序列化类型 |
| scriptContent | String | 数据解析脚本（JS ES5） |
| scriptEnabled | Boolean | 是否启用数据解析脚本 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询产品，不存在直接返回 null。
2. 查询产品所属分类，将 categoryName 拼接到响应 VO。

### 1.6 通过 ProductKey 获得产品详情

- **路径**: GET /iot/product/get-by-key
- **权限**: iot:product:query
- **说明**: 按 ProductKey 获得产品详情，并拼接产品分类名称。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| productKey | String | 是 | | 产品 Key |

**响应**: CommonResult&lt;IotProductRespVO&gt; — 字段同 1.5（产品不存在时 data 为 null）

**业务逻辑**:
1. 按 ProductKey 查询产品，不存在直接返回 null。
2. 查询产品所属分类，将 categoryName 拼接到响应 VO。

### 1.7 获得产品分页

- **路径**: GET /iot/product/page
- **权限**: iot:product:query
- **说明**: 分页查询产品列表，并批量拼接产品分类名称。

**请求参数 (IotProductPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam 默认字段） |
| pageSize | Integer | 否 | | 每页条数（PageParam 默认字段） |
| name | String | 否 | | 产品名称（模糊匹配） |
| productKey | String | 否 | | 产品标识 |

**响应**: CommonResult&lt;PageResult&lt;IotProductRespVO&gt;&gt; — 列表项字段同 1.5

**业务逻辑**:
1. 按条件分页查询产品。
2. 批量查询本页产品涉及的分类，构建分类 Map。
3. 逐条拼接 categoryName 后返回。

### 1.8 导出产品 Excel

- **路径**: GET /iot/product/export-excel
- **权限**: iot:product:export
- **说明**: 按分页查询条件导出全部产品 Excel 文件（产品.xls）。

**请求参数 (IotProductPageReqVO)**: 同 1.7（pageSize 在服务端强制为不分页）。

**响应**: Excel 文件流（导出列：产品编号、产品名称、产品标识、产品分类、产品图标、产品图片、产品描述、产品状态、设备类型、联网方式、协议类型、序列化类型、创建时间；状态类字段经字典转换）。

**业务逻辑**:
1. 将请求的 pageSize 置为 PAGE_SIZE_NONE（不分页，导出全部）。
2. 复用分页查询逻辑（含分类名称拼接）。
3. 通过 ExcelUtils 写出「产品.xls」文件流；操作日志记录为导出（@ApiAccessLog EXPORT）。

### 1.9 同步产品属性表结构到时序库

- **路径**: POST /iot/product/sync-property-table
- **权限**: iot:product:update
- **说明**: 手动同步指定产品的物模型属性表结构到时序库（TDengine / IoTDB）的超级表。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 产品编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验产品是否存在，不存在抛出 PRODUCT_NOT_EXISTS。
2. 调用 devicePropertyDataService.defineDevicePropertyData 同步该产品的时序库表结构。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |

### 1.10 获取产品精简信息列表

- **路径**: GET /iot/product/simple-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 获取产品精简列表，主要用于前端下拉选项，可按设备类型过滤。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceType | Integer | 否 | | 设备类型，不传则返回全部 |

**响应**: CommonResult&lt;List&lt;IotProductRespVO&gt;&gt; — 仅填充部分字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 产品编号 |
| name | String | 产品名称 |
| status | Integer | 产品状态 |
| deviceType | Integer | 设备类型 |
| productKey | String | 产品标识 |

**业务逻辑**:
1. 按设备类型（可为空）查询产品列表。
2. 仅转换出 id、name、status、deviceType、productKey 五个字段返回。

### 1.11 更新产品数据解析脚本

- **路径**: PUT /iot/product/update-script
- **权限**: iot:product:update
- **说明**: 部分更新产品的 JS 数据解析脚本与启用开关；只修改本次提交的字段，保存即生效。脚本内容只做语法编译校验，不执行。

**请求参数 (IotProductScriptUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 产品编号 |
| scriptContent | String | 否 | UTF-8 ≤ 32KB | 数据解析脚本（JS ES5）；空字符串表示清空，仅在停用时允许 |
| scriptEnabled | Boolean | 否 | - | 是否启用数据解析脚本 |

> 校验约束：scriptContent 与 scriptEnabled 至少提交一个。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验产品存在，不存在抛出 PRODUCT_NOT_EXISTS。
2. 若提交了 scriptContent：校验 UTF-8 字节数不超过 32KB；非空时在调试线程池上只编译（限时 2000ms）做语法检查，不执行用户代码，编译失败/超时/繁忙分别抛对应错误。
3. 计算生效值：未提交的 scriptContent / scriptEnabled 取数据库当前值；若最终为启用且脚本内容为空，抛 PRODUCT_SCRIPT_EMPTY。
4. 部分更新数据库（null 字段跳过），并清除该产品的 Redis 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |
| 1_050_009_000 | 数据解析脚本不能超过 32KB |
| 1_050_009_001 | 数据解析脚本语法错误 |
| 1_050_009_002 | 启用数据解析脚本时，脚本内容不能为空 |
| 1_050_009_003 | 脚本调试繁忙或已熔断，请稍后再试 |

### 1.12 调试产品数据解析脚本

- **路径**: POST /iot/product/debug-script
- **权限**: iot:product:update
- **说明**: 执行当前编辑的脚本内容做 decode/encode 调试；不保存、不发消息、不改属性。使用与网关相同的运行时、输出校验与执行预算，请求线程同步等待，最长 2000ms。

**请求参数 (IotProductScriptDebugReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 产品编号 |
| scriptContent | String | 是 | @NotEmpty、UTF-8 ≤ 32KB | 数据解析脚本（JS ES5） |
| direction | String | 是 | @NotEmpty、@Pattern(decode\|encode) | 方向：decode 上行解码 / encode 下行编码 |
| inputHex | String | decode 时必填 | 偶数位 HEX（允许空格）、≤ 4096 字节 | 上行原始字节的 HEX |
| message | Map&lt;String, Object&gt; | encode 时必填 | - | 下行指令：{method, requestId?, params?}，仅支持 thing.property.set / thing.service.invoke |

**响应**: CommonResult&lt;IotProductScriptDebugRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| success | Boolean | 是否成功 |
| durationMs | Long | 执行耗时（毫秒） |
| message | Map&lt;String, Object&gt; | decode：解析出的消息；为空表示没有业务消息（只记录原始消息） |
| standard | Boolean | encode：是否走标准 JSON 下发 |
| outputHex | String | encode：下行字节的 HEX |
| error | ErrorInfo | 失败信息（type：ERROR、TIMEOUT、REJECTED、OUTPUT_INVALID、ENCODE_EMPTY；message；line） |

**业务逻辑**:
1. 校验产品存在；校验脚本长度不超过 32KB。
2. 构建与网关结构一致的上下文：decode 校验 HEX 与长度，设备名固定为 `debug-device`；encode 只允许 thing.property.set / thing.service.invoke。
3. 按方向执行脚本（截止时间 2000ms），并按网关同一套规则校验输出：decode 未定义或返回 null 表示无业务消息；encode 的字节按产品协议规则校验（Modbus 必须是合法请求 PDU），未生成下行数据返回 ENCODE_EMPTY。
4. 返回执行结果与错误信息（错误行号可选）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_001_000 | 产品不存在 |
| 1_050_009_000 | 数据解析脚本不能超过 32KB |
| 1_050_009_003 | 脚本调试繁忙或已熔断，请稍后再试 |
| 400 | 上行数据不是偶数位 HEX / 超过 4096 字节；下行指令为空或不是属性设置/服务调用 |

## 2. 产品分类管理（IotProductCategoryController）

### 2.1 创建产品分类

- **路径**: POST /iot/product-category/create
- **权限**: iot:product-category:create
- **说明**: 创建产品分类。

**请求参数 (IotProductCategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | | 分类 ID（新增时不传） |
| name | String | 是 | @NotEmpty | 分类名字 |
| sort | Integer | 否 | | 分类排序 |
| status | Integer | 是 | @NotNull | 分类状态（CommonStatusEnum） |
| description | String | 否 | | 分类描述 |

**响应**: CommonResult&lt;Long&gt; — 分类编号

**业务逻辑**:
1. 请求 VO 转换为 IotProductCategoryDO。
2. 插入数据库，返回分类编号。

### 2.2 更新产品分类

- **路径**: PUT /iot/product-category/update
- **权限**: iot:product-category:update
- **说明**: 更新产品分类。

**请求参数 (IotProductCategorySaveReqVO)**: 同 2.1，其中 id 必传。

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验分类是否存在，不存在抛出 PRODUCT_CATEGORY_NOT_EXISTS。
2. 更新数据库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_004_000 | 产品分类不存在 |

### 2.3 删除产品分类

- **路径**: DELETE /iot/product-category/delete
- **权限**: iot:product-category:delete
- **说明**: 删除产品分类。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 分类编号 |

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验分类是否存在，不存在抛出 PRODUCT_CATEGORY_NOT_EXISTS。
2. 删除数据库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_004_000 | 产品分类不存在 |

### 2.4 获得产品分类详情

- **路径**: GET /iot/product-category/get
- **权限**: iot:product-category:query
- **说明**: 按编号获得产品分类详情。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 分类编号 |

**响应**: CommonResult&lt;IotProductCategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分类 ID |
| name | String | 分类名字 |
| sort | Integer | 分类排序 |
| status | Integer | 分类状态 |
| description | String | 分类描述 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询分类并转换为响应 VO 返回。

### 2.5 获得产品分类分页

- **路径**: GET /iot/product-category/page
- **权限**: iot:product-category:query
- **说明**: 分页查询产品分类。

**请求参数 (IotProductCategoryPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | | 页码（PageParam 默认字段） |
| pageSize | Integer | 否 | | 每页条数（PageParam 默认字段） |
| name | String | 否 | | 分类名字 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;IotProductCategoryRespVO&gt;&gt; — 列表项字段同 2.4

**业务逻辑**:
1. 按条件分页查询分类并转换为响应 VO。

### 2.6 获得所有产品分类精简列表

- **路径**: GET /iot/product-category/simple-list
- **权限**: iot:product-category:query
- **说明**: 获取全部启用状态的产品分类，用于下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;IotProductCategoryRespVO&gt;&gt; — 仅填充部分字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分类 ID |
| name | String | 分类名字 |

**业务逻辑**:
1. 查询状态为「开启」（ENABLE）的全部分类。
2. 仅转换出 id、name 两个字段返回。
