# 工装工具接口 (MesTmToolController / MesTmToolTypeController)

> MES 工具管理（tm）域：工具类型维护 + 工具台账管理，含保养周期维护、条码自动生成与批次引用校验。

## 接口路径前缀

- `/mes/tm/tool` (Controller: MesTmToolController) — 工具台账
- `/mes/tm/tool-type` (Controller: MesTmToolTypeController) — 工具类型

---

## 1. 工具台账（MesTmToolController，前缀 /mes/tm/tool）

### 1.1 创建工具

- **路径**: POST /mes/tm/tool/create
- **权限**: mes:tm-tool:create
- **说明**: 新增一条工具台账记录，并自动生成对应条码。

**请求参数 (MesTmToolSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | - | - | 编号（新增时忽略） |
| code | String | 是 | @NotEmpty / @Size(max=64) | 工具编码 |
| name | String | 是 | @NotEmpty / @Size(max=255) | 工具名称 |
| brand | String | 否 | @Size(max=255) | 品牌 |
| specification | String | 否 | @Size(max=255) | 型号规格 |
| toolTypeId | Long | 是 | @NotNull | 工具类型编号 |
| quantity | Integer | 是 | @NotNull | 数量 |
| availableQuantity | Integer | 是 | @NotNull | 可用数量 |
| maintenType | Integer | 否 | - | 保养维护类型（1 定期维护 / 2 按使用次数维护） |
| nextMaintenPeriod | Integer | 否 | - | 下次保养周期（次数） |
| nextMaintenDate | LocalDateTime | 否 | - | 下次保养日期 |
| status | Integer | 是 | @NotNull | 状态（字典 MES_TM_TOOL_STATUS） |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Long&gt; — 新建工具编号

**业务逻辑**:
1. 校验工具类型存在、工具编码唯一。
2. 转换为 MesTmToolDO 并插入数据库。
3. 调用条码服务按 TOOL 业务类型自动生成条码（关联工具编号、编码、名称）。
4. 返回新工具编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 工具类型不存在 |
| 1_040_401_001 | 工具编码已存在 |

### 1.2 更新工具

- **路径**: PUT /mes/tm/tool/update
- **权限**: mes:tm-tool:update
- **说明**: 更新工具台账信息，按保养类型互斥清理保养字段。

**请求参数 (MesTmToolSaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验工具存在。
2. 校验工具类型存在、工具编码唯一（排除自身）。
3. 保养类型互斥清理：定期维护（1）清空 nextMaintenPeriod；按使用次数维护（2）清空 nextMaintenDate。
4. 更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_401_000 | 工具不存在 |
| 1_040_400_000 | 工具类型不存在 |
| 1_040_401_001 | 工具编码已存在 |

### 1.3 删除工具

- **路径**: DELETE /mes/tm/tool/delete?id={id}
- **权限**: mes:tm-tool:delete
- **说明**: 删除工具，已被批次引用时禁止删除。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验工具存在。
2. 校验工具未被批次引用（引用计数大于 0 则抛错）。
3. 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_401_000 | 工具不存在 |
| 1_040_401_002 | 该工具已被批次引用，无法删除 |

### 1.4 获得工具详情

- **路径**: GET /mes/tm/tool/get?id={id}
- **权限**: mes:tm-tool:query
- **说明**: 查询单个工具详情，并拼接工具类型名称。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;MesTmToolRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 工具编码 |
| name | String | 工具名称 |
| brand | String | 品牌 |
| specification | String | 型号规格 |
| toolTypeId | Long | 工具类型编号 |
| toolTypeName | String | 工具类型名称（后端拼接） |
| quantity | Integer | 数量 |
| availableQuantity | Integer | 可用数量 |
| maintenType | Integer | 保养维护类型（字典 MES_TM_MAINTEN_TYPE） |
| nextMaintenPeriod | Integer | 下次保养周期（次数） |
| nextMaintenDate | LocalDateTime | 下次保养日期 |
| status | Integer | 状态（字典 MES_TM_TOOL_STATUS） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询工具并转换为 RespVO。
2. 若 toolTypeId 非空，查询工具类型并将名称写入 toolTypeName。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_401_000 | 工具不存在（编号无效时返回 null，不抛错） |

### 1.5 获得工具分页

- **路径**: GET /mes/tm/tool/page
- **权限**: mes:tm-tool:query
- **说明**: 分页查询工具台账，结果拼接工具类型名称。

**请求参数 (MesTmToolPageReqVO，继承分页参数 pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| code | String | 否 | - | 工具编码 |
| name | String | 否 | - | 工具名称 |
| toolTypeId | Long | 否 | - | 工具类型编号 |
| brand | String | 否 | - | 品牌 |
| specification | String | 否 | - | 型号规格 |
| status | Integer | 否 | - | 状态 |

**响应**: CommonResult&lt;PageResult&lt;MesTmToolRespVO&gt;&gt;，list 元素字段同 1.4。

**业务逻辑**:
1. 按条件分页查询工具。
2. 批量获取涉及的工具类型 Map。
3. 逐条拼接 toolTypeName 后返回。

### 1.6 导出工具 Excel

- **路径**: GET /mes/tm/tool/export-excel
- **权限**: mes:tm-tool:export
- **说明**: 按查询条件导出全部工具台账 Excel（文件名「工具台账.xls」）。

**请求参数 (MesTmToolPageReqVO)**: 同 1.5（pageSize 固定为全量）

**响应**: 文件流（Excel 下载），列定义同 MesTmToolRespVO 的 @ExcelProperty。

**业务逻辑**:
1. 将 pageSize 置为不分页，按条件查询全量数据。
2. 批量拼接工具类型名称。
3. 通过 ExcelUtils 输出「工具台账.xls」。

### 1.7 获得工具精简列表

- **路径**: GET /mes/tm/tool/simple-list
- **权限**: mes:tm-tool:query
- **说明**: 查询全部工具，用于下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MesTmToolRespVO&gt;&gt;，字段同 1.4（toolTypeName 不拼接）。

**业务逻辑**:
1. 查询全部工具列表。
2. 直接转换为 RespVO 列表返回（不拼接类型名称）。

---

## 2. 工具类型（MesTmToolTypeController，前缀 /mes/tm/tool-type）

### 2.1 创建工具类型

- **路径**: POST /mes/tm/tool-type/create
- **权限**: mes:tm-tool-type:create
- **说明**: 新增工具类型，编码与名称均需唯一。

**请求参数 (MesTmToolTypeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | - | - | 编号（新增时忽略） |
| code | String | 是 | @NotEmpty / @Size(max=64) | 类型编码 |
| name | String | 是 | @NotEmpty / @Size(max=255) | 类型名称 |
| codeFlag | Boolean | 是 | @NotNull | 是否编码管理 |
| maintenType | Integer | 否 | - | 保养维护类型（1 定期维护 / 2 按使用次数维护） |
| maintenPeriod | Integer | 否 | - | 保养周期 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Long&gt; — 新建类型编号

**业务逻辑**:
1. 校验类型编码唯一。
2. 校验类型名称唯一。
3. 转换为 MesTmToolTypeDO 并插入，返回编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_001 | 工具类型编码已存在 |
| 1_040_400_002 | 工具类型名称已存在 |

### 2.2 更新工具类型

- **路径**: PUT /mes/tm/tool-type/update
- **权限**: mes:tm-tool-type:update
- **说明**: 更新工具类型信息。

**请求参数 (MesTmToolTypeSaveReqVO)**: 同 2.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验工具类型存在。
2. 校验类型编码唯一（排除自身）。
3. 校验类型名称唯一（排除自身）。
4. 更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 工具类型不存在 |
| 1_040_400_001 | 工具类型编码已存在 |
| 1_040_400_002 | 工具类型名称已存在 |

### 2.3 删除工具类型

- **路径**: DELETE /mes/tm/tool-type/delete?id={id}
- **权限**: mes:tm-tool-type:delete
- **说明**: 删除工具类型，被工具或工作站工装资源引用时禁止删除。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;Boolean&gt; — 是否成功

**业务逻辑**:
1. 校验工具类型存在。
2. 校验该类型下不存在工具（存在则抛错）。
3. 校验该类型未被工作站工装资源引用（存在则抛错）。
4. 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 工具类型不存在 |
| 1_040_400_003 | 该工具类型下存在工具，无法删除 |
| 1_040_400_004 | 该工具类型已被工作站工装资源引用，无法删除 |

### 2.4 获得工具类型详情

- **路径**: GET /mes/tm/tool-type/get?id={id}
- **权限**: mes:tm-tool-type:query
- **说明**: 查询单个工具类型详情。

**请求参数**: 无（Query 参数 id：编号，必填）

**响应**: CommonResult&lt;MesTmToolTypeRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 类型编码 |
| name | String | 类型名称 |
| codeFlag | Boolean | 是否编码管理 |
| maintenType | Integer | 保养维护类型（字典 MES_TM_MAINTEN_TYPE） |
| maintenPeriod | Integer | 保养周期 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询工具类型并转换为 RespVO 返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_400_000 | 工具类型不存在（编号无效时返回 null，不抛错） |

### 2.5 获得工具类型分页

- **路径**: GET /mes/tm/tool-type/page
- **权限**: mes:tm-tool-type:query
- **说明**: 分页查询工具类型。

**请求参数 (MesTmToolTypePageReqVO，继承分页参数 pageNo/pageSize)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| code | String | 否 | - | 类型编码 |
| name | String | 否 | - | 类型名称 |
| maintenType | Integer | 否 | - | 保养维护类型 |

**响应**: CommonResult&lt;PageResult&lt;MesTmToolTypeRespVO&gt;&gt;，list 元素字段同 2.4。

**业务逻辑**:
1. 按条件分页查询工具类型并转换为 RespVO 分页结果。

### 2.6 获得工具类型精简列表

- **路径**: GET /mes/tm/tool-type/simple-list
- **权限**: 已认证（无 @PreAuthorize，仅要求登录，用于前端下拉选项）
- **说明**: 查询全部工具类型，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MesTmToolTypeRespVO&gt;&gt;，字段同 2.4。

**业务逻辑**:
1. 查询全部工具类型列表。
2. 转换为 RespVO 列表返回。

### 2.7 导出工具类型 Excel

- **路径**: GET /mes/tm/tool-type/export-excel
- **权限**: mes:tm-tool-type:export
- **说明**: 按查询条件导出全部工具类型 Excel（文件名「工具类型.xls」）。

**请求参数 (MesTmToolTypePageReqVO)**: 同 2.5（pageSize 固定为全量）

**响应**: 文件流（Excel 下载），列定义同 MesTmToolTypeRespVO 的 @ExcelProperty。

**业务逻辑**:
1. 将 pageSize 置为不分页，按条件查询全量数据。
2. 转换为 RespVO 列表。
3. 通过 ExcelUtils 输出「工具类型.xls」。
