# 字典管理接口 (DictTypeController / DictDataController)

> 提供系统中字典类型与字典数据的全生命周期管理（创建、修改、删除、分页查询、下拉精简列表、Excel 导出），字典数据按所属字典类型组织，供全局下拉选项与状态枚举翻译使用。

## 接口路径前缀

- `/system/dict-type`  (Controller: DictTypeController) — 字典类型管理
- `/system/dict-data`  (Controller: DictDataController) — 字典数据管理

---

## 1. 字典类型（DictTypeController，前缀 /system/dict-type）

### 1.1 创建字典类型

- **路径**: POST /system/dict-type/create
- **权限**: system:dict:create
- **说明**: 新增一个字典类型，名称与类型（type）均要求全局唯一。

**请求参数 (DictTypeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 字典类型编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=100) | 字典名称，如「性别」 |
| type | String | 是 | @NotNull、@Size(max=100) | 字典类型，如 `sys_common_sex` |
| status | Integer | 是 | @NotNull | 状态，参见 CommonStatusEnum 枚举 |
| remark | String | 否 | — | 备注 |

**响应**: CommonResult&lt;Long&gt; — 新创建的字典类型编号。

**业务逻辑**:
1. 校验字典类型名字的唯一性（重名抛 DICT_TYPE_NAME_DUPLICATE）。
2. 校验字典类型 type 的唯一性（type 为空时跳过校验，重复抛 DICT_TYPE_TYPE_DUPLICATE）。
3. 将请求 VO 转换为 DictTypeDO，并将 deletedTime 置为空值占位（避免唯一索引出现 null 值）。
4. 插入数据库并返回新记录 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_006_003 | 已经存在该名字的字典类型 |
| 1_002_006_004 | 已经存在该类型的字典类型 |

### 1.2 修改字典类型

- **路径**: PUT /system/dict-type/update
- **权限**: system:dict:update
- **说明**: 按 id 修改字典类型，同样校验名称与 type 的唯一性。

**请求参数 (DictTypeSaveReqVO)**: 同 1.1，其中 id 必传（用于定位待更新记录）。

**响应**: CommonResult&lt;Boolean&gt; — 固定返回 true。

**业务逻辑**:
1. 校验待修改的字典类型是否存在（不存在抛 DICT_TYPE_NOT_EXISTS）。
2. 校验字典类型名字的唯一性（排除自身 id）。
3. 校验字典类型 type 的唯一性（排除自身 id）。
4. 转换为 DictTypeDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_006_001 | 当前字典类型不存在 |
| 1_002_006_003 | 已经存在该名字的字典类型 |
| 1_002_006_004 | 已经存在该类型的字典类型 |

### 1.3 删除字典类型

- **路径**: DELETE /system/dict-type/delete
- **权限**: system:dict:delete
- **说明**: 按 id 逻辑删除单个字典类型，删除前校验其下无字典数据。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 字典类型编号 |

**响应**: CommonResult&lt;Boolean&gt; — 固定返回 true。

**业务逻辑**:
1. 校验字典类型是否存在，并取回该记录（不存在抛 DICT_TYPE_NOT_EXISTS）。
2. 统计该类型下字典数据数量，大于 0 则抛 DICT_TYPE_HAS_CHILDREN，拒绝删除。
3. 执行逻辑删除（updateToDelete，记录删除时间）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_006_001 | 当前字典类型不存在 |
| 1_002_006_005 | 无法删除，该字典类型还有字典数据 |

### 1.4 批量删除字典类型

- **路径**: DELETE /system/dict-type/delete-list
- **权限**: system:dict:delete
- **说明**: 按 id 列表批量逻辑删除字典类型，逐个校验其下无字典数据。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam(required) | 字典类型编号列表 |

**响应**: CommonResult&lt;Boolean&gt; — 固定返回 true。

**业务逻辑**:
1. 按 ids 批量查询字典类型记录。
2. 逐个统计各类型下字典数据数量，任一大于 0 则抛 DICT_TYPE_HAS_CHILDREN。
3. 使用同一删除时间批量逻辑删除全部记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_006_005 | 无法删除，该字典类型还有字典数据 |

### 1.5 获得字典类型的分页列表

- **路径**: GET /system/dict-type/page
- **权限**: system:dict:query
- **说明**: 按条件分页查询字典类型列表。

**请求参数 (DictTypePageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | PageParam 默认校验 | 页码，从 1 开始 |
| pageSize | Integer | 否 | PageParam 默认校验 | 每页条数 |
| name | String | 否 | — | 字典类型名称，模糊匹配 |
| type | String | 否 | @Size(max=100) | 字典类型，模糊匹配 |
| status | Integer | 否 | — | 展示状态，参见 CommonStatusEnum 枚举 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;DictTypeRespVO&gt;&gt;，分页内容字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 字典类型编号 |
| name | String | 字典名称 |
| type | String | 字典类型 |
| status | Integer | 状态，参见 CommonStatusEnum 枚举 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

### 1.6 查询字典类型详细

- **路径**: GET /system/dict-type/get
- **权限**: system:dict:query
- **说明**: 按编号查询单个字典类型详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 字典类型编号 |

**响应**: CommonResult&lt;DictTypeRespVO&gt;，字段同 1.5 响应表。

### 1.7 获得全部字典类型列表

- **路径**: GET /system/dict-type/list-all-simple（兼容别名 /system/dict-type/simple-list）
- **权限**: 无需权限认证（前端全局使用，仅要求已登录）
- **说明**: 获得全部字典类型（包括开启 + 禁用），主要用于前端的下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DictTypeSimpleRespVO&gt;&gt;，字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 字典类型编号 |
| name | String | 字典类型名称 |
| type | String | 字典类型 |

**业务逻辑**:
1. 查询全部字典类型列表（selectList，不做状态过滤）。
2. 转换为精简 VO 列表返回。

### 1.8 导出数据类型

- **路径**: GET /system/dict-type/export-excel
- **权限**: system:dict:query
- **说明**: 按分页查询条件导出全量字典类型 Excel（.xls），操作类型记为导出日志。

**请求参数 (DictTypePageReqVO)**: 同 1.5 请求参数（pageSize 由后端强制设为不分页常量）。

**响应**: 无 CommonResult 包装，直接输出 Excel 文件流（文件名「字典类型.xls」，按 DictTypeRespVO 注解映射列：字典主键、字典名称、字典类型、状态）。

**业务逻辑**:
1. 将导出请求的 pageSize 设置为 PAGE_SIZE_NONE（查询全部）。
2. 按条件查询字典类型分页并取全量列表。
3. 转换为 DictTypeRespVO 后通过 ExcelUtils 写出 Excel 响应流。

---

## 2. 字典数据（DictDataController，前缀 /system/dict-data）

### 2.1 新增字典数据

- **路径**: POST /system/dict-data/create
- **权限**: system:dict:create
- **说明**: 在指定字典类型下新增一条字典数据，同一类型下 value 唯一。

**请求参数 (DictDataSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | 字典数据编号（创建时不传） |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| label | String | 是 | @NotBlank、@Size(max=100) | 字典标签，如「男」 |
| value | String | 是 | @NotBlank、@Size(max=100) | 字典值，如 `iocoder` |
| dictType | String | 是 | @NotBlank、@Size(max=100) | 所属字典类型，如 `sys_common_sex` |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态，参见 CommonStatusEnum 枚举 |
| colorType | String | 否 | — | 颜色类型：default、primary、success、info、warning、danger |
| cssClass | String | 否 | — | css 样式 |
| remark | String | 否 | — | 备注 |

**响应**: CommonResult&lt;Long&gt; — 新创建的字典数据编号。

**业务逻辑**:
1. 校验所属字典类型有效：类型必须存在且处于开启状态（否则分别抛 DICT_TYPE_NOT_EXISTS / DICT_TYPE_NOT_ENABLE）。
2. 校验同一字典类型下字典值 value 的唯一性（重复抛 DICT_DATA_VALUE_DUPLICATE）。
3. 转换为 DictDataDO 插入数据库并返回新记录 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_006_001 | 当前字典类型不存在 |
| 1_002_006_002 | 字典类型不处于开启状态，不允许选择 |
| 1_002_007_003 | 已经存在该值的字典数据 |

### 2.2 修改字典数据

- **路径**: PUT /system/dict-data/update
- **权限**: system:dict:update
- **说明**: 按 id 修改字典数据，重新校验字典类型有效性与 value 唯一性。

**请求参数 (DictDataSaveReqVO)**: 同 2.1，其中 id 必传（用于定位待更新记录）。

**响应**: CommonResult&lt;Boolean&gt; — 固定返回 true。

**业务逻辑**:
1. 校验待修改的字典数据是否存在（不存在抛 DICT_DATA_NOT_EXISTS）。
2. 校验所属字典类型有效（存在且开启，否则抛 DICT_TYPE_NOT_EXISTS / DICT_TYPE_NOT_ENABLE）。
3. 校验同一字典类型下 value 的唯一性（排除自身 id）。
4. 转换为 DictDataDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_006_001 | 当前字典类型不存在 |
| 1_002_006_002 | 字典类型不处于开启状态，不允许选择 |
| 1_002_007_001 | 当前字典数据不存在 |
| 1_002_007_003 | 已经存在该值的字典数据 |

### 2.3 删除字典数据

- **路径**: DELETE /system/dict-data/delete
- **权限**: system:dict:delete
- **说明**: 按 id 删除单条字典数据。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 字典数据编号 |

**响应**: CommonResult&lt;Boolean&gt; — 固定返回 true。

**业务逻辑**:
1. 校验字典数据是否存在（不存在抛 DICT_DATA_NOT_EXISTS）。
2. 删除该条字典数据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_007_001 | 当前字典数据不存在 |

### 2.4 批量删除字典数据

- **路径**: DELETE /system/dict-data/delete-list
- **权限**: system:dict:delete
- **说明**: 按 id 列表批量删除字典数据。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam(required) | 字典数据编号列表 |

**响应**: CommonResult&lt;Boolean&gt; — 固定返回 true。

**业务逻辑**:
1. 按 ids 直接批量删除字典数据（Mapper deleteByIds）。

### 2.5 获得全部字典数据列表

- **路径**: GET /system/dict-data/list-all-simple（兼容别名 /system/dict-data/simple-list）
- **权限**: 无需权限认证（前端全局使用，仅要求已登录）
- **说明**: 获得全部开启状态的字典数据，一般用于管理后台将字典数据缓存到本地。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DictDataSimpleRespVO&gt;&gt;，字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| dictType | String | 字典类型 |
| value | String | 字典键值 |
| label | String | 字典标签 |
| colorType | String | 颜色类型：default、primary、success、info、warning、danger |
| cssClass | String | css 样式 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）且不限定字典类型的全部字典数据。
2. 按「字典类型 dictType + 显示顺序 sort」双关键字排序。
3. 转换为精简 VO 列表返回。

### 2.6 获得字典数据的分页

- **路径**: GET /system/dict-data/page
- **权限**: system:dict:query
- **说明**: 按条件分页查询字典数据列表。

**请求参数 (DictDataPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | PageParam 默认校验 | 页码，从 1 开始 |
| pageSize | Integer | 否 | PageParam 默认校验 | 每页条数 |
| label | String | 否 | @Size(max=100) | 字典标签 |
| dictType | String | 否 | @Size(max=100) | 字典类型，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 展示状态，参见 CommonStatusEnum 枚举 |

**响应**: CommonResult&lt;PageResult&lt;DictDataRespVO&gt;&gt;，分页内容字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 字典数据编号 |
| sort | Integer | 显示顺序 |
| label | String | 字典标签 |
| value | String | 字典值 |
| dictType | String | 字典类型 |
| status | Integer | 状态，参见 CommonStatusEnum 枚举 |
| colorType | String | 颜色类型：default、primary、success、info、warning、danger |
| cssClass | String | css 样式 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

### 2.7 查询字典数据详细

- **路径**: GET /system/dict-data/get
- **权限**: system:dict:query
- **说明**: 按编号查询单条字典数据详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 字典数据编号 |

**响应**: CommonResult&lt;DictDataRespVO&gt;，字段同 2.6 响应表。

### 2.8 导出字典数据

- **路径**: GET /system/dict-data/export-excel
- **权限**: system:dict:export
- **说明**: 按分页查询条件导出全量字典数据 Excel（.xls），操作类型记为导出日志。

**请求参数 (DictDataPageReqVO)**: 同 2.6 请求参数（pageSize 由后端强制设为不分页常量）。

**响应**: 无 CommonResult 包装，直接输出 Excel 文件流（文件名「字典数据.xls」，按 DictDataRespVO 注解映射列：字典编码、字典排序、字典标签、字典键值、字典类型、状态）。

**业务逻辑**:
1. 将导出请求的 pageSize 设置为 PAGE_SIZE_NONE（查询全部）。
2. 按条件查询字典数据分页并取全量列表。
3. 转换为 DictDataRespVO 后通过 ExcelUtils 写出 Excel 响应流。

---

## 附：本域相关错误码汇总（ErrorCodeConstants，前缀 1_002_006 / 1_002_007）

| 错误码 | 常量名 | 说明 |
|-------|--------|------|
| 1_002_006_001 | DICT_TYPE_NOT_EXISTS | 当前字典类型不存在 |
| 1_002_006_002 | DICT_TYPE_NOT_ENABLE | 字典类型不处于开启状态，不允许选择 |
| 1_002_006_003 | DICT_TYPE_NAME_DUPLICATE | 已经存在该名字的字典类型 |
| 1_002_006_004 | DICT_TYPE_TYPE_DUPLICATE | 已经存在该类型的字典类型 |
| 1_002_006_005 | DICT_TYPE_HAS_CHILDREN | 无法删除，该字典类型还有字典数据 |
| 1_002_007_001 | DICT_DATA_NOT_EXISTS | 当前字典数据不存在 |
| 1_002_007_002 | DICT_DATA_NOT_ENABLE | 字典数据({})不处于开启状态，不允许选择 |
| 1_002_007_003 | DICT_DATA_VALUE_DUPLICATE | 已经存在该值的字典数据 |
