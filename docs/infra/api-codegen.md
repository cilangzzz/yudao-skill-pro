# 代码生成接口 (CodegenController)

> 提供代码生成器能力：从数据源导入表结构到 codegen 表定义，编辑表/字段的生成配置，并基于 Velocity 模板引擎预览、下载生成的 CRUD 代码。

## 接口路径前缀

/infra/codegen  (Controller: CodegenController)

## 1. 数据库表查询

### 1.1 获得数据库自带的表定义列表

- **路径**: GET /infra/codegen/db/table/list
- **权限**: infra:codegen:query
- **说明**: 获取指定数据源下的数据库表列表（支持表名/描述模糊匹配），会过滤掉已经导入 Codegen 的表。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| dataSourceConfigId | Long | 是 | @RequestParam 必填 | 数据源配置的编号 |
| name | String | 否 | - | 表名，模糊匹配 |
| comment | String | 否 | - | 描述，模糊匹配 |

**响应**: CommonResult&lt;List&lt;DatabaseTableRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| name | String | 表名称 |
| comment | String | 表描述 |

**业务逻辑**:
1. 调用 DatabaseTableService 获取指定数据源下、按 name/comment 模糊过滤的表结构列表（TableInfo）。
2. 查询 Codegen 中该数据源下已导入的表名集合。
3. 从结果中移除已导入的表，转换为 DatabaseTableRespVO 返回。

## 2. 表定义管理

### 2.1 获得表定义列表

- **路径**: GET /infra/codegen/table/list
- **权限**: infra:codegen:query
- **说明**: 获取指定数据源下已导入 Codegen 的全部表定义列表。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| dataSourceConfigId | Long | 是 | @RequestParam 必填 | 数据源配置的编号 |

**响应**: CommonResult&lt;List&lt;CodegenTableRespVO&gt;&gt;

**业务逻辑**:
1. 按 dataSourceConfigId 查询 codegen_table 表定义列表。
2. BeanUtils 转换为 CodegenTableRespVO 返回。

### 2.2 获得表定义分页

- **路径**: GET /infra/codegen/table/page
- **权限**: infra:codegen:query
- **说明**: 分页获取已导入的表定义，支持表名、描述、类名模糊查询及创建时间范围过滤。

**请求参数 (CodegenTablePageReqVO)**: 继承 PageParam

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| tableName | String | 否 | - | 表名称，模糊匹配 |
| tableComment | String | 否 | - | 表描述，模糊匹配 |
| className | String | 否 | - | 实体类名，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult&lt;PageResult&lt;CodegenTableRespVO&gt;&gt;，CodegenTableRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| scene | Integer | 生成场景，参见 CodegenSceneEnum 枚举 |
| tableName | String | 表名称 |
| tableComment | String | 表描述 |
| remark | String | 备注 |
| moduleName | String | 模块名 |
| businessName | String | 业务名 |
| className | String | 类名称 |
| classComment | String | 类描述 |
| author | String | 作者 |
| templateType | Integer | 模板类型，参见 CodegenTemplateTypeEnum 枚举 |
| frontType | Integer | 前端类型，参见 CodegenFrontTypeEnum 枚举 |
| parentMenuId | Long | 父菜单编号 |
| masterTableId | Long | 主表的编号（主子表场景） |
| subJoinColumnId | Long | 子表关联主表的字段编号 |
| subJoinMany | Boolean | 主表与子表是否一对多 |
| treeParentColumnId | Long | 树表的父字段编号 |
| treeNameColumnId | Long | 树表的名字字段编号 |
| dataSourceConfigId | Integer | 主键编号（数据源配置编号） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 按分页查询条件（表名/描述/类名模糊 + 创建时间范围）查询 codegen_table 分页结果。
2. BeanUtils 转换为 PageResult&lt;CodegenTableRespVO&gt; 返回。

### 2.3 获得表和字段的明细

- **路径**: GET /infra/codegen/detail
- **权限**: infra:codegen:query
- **说明**: 获取指定表的表定义与字段定义明细。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| tableId | Long | 是 | @RequestParam 必填 | 表编号 |

**响应**: CommonResult&lt;CodegenDetailRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| table | CodegenTableRespVO | 表定义（字段同 2.2） |
| columns | List&lt;CodegenColumnRespVO&gt; | 字段定义列表 |

CodegenColumnRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| tableId | Long | 表编号 |
| columnName | String | 字段名 |
| dataType | String | 字段类型 |
| columnComment | String | 字段描述 |
| nullable | Boolean | 是否允许为空 |
| primaryKey | Boolean | 是否主键 |
| ordinalPosition | Integer | 排序 |
| javaType | String | Java 属性类型 |
| javaField | String | Java 属性名 |
| dictType | String | 字典类型 |
| example | String | 数据示例 |
| createOperation | Boolean | 是否为 Create 创建操作的字段 |
| updateOperation | Boolean | 是否为 Update 更新操作的字段 |
| listOperation | Boolean | 是否为 List 查询操作的字段 |
| listOperationCondition | String | List 查询条件类型，参见 CodegenColumnListConditionEnum 枚举（如 LIKE） |
| listOperationResult | Boolean | 是否为 List 查询操作的返回字段 |
| htmlType | String | 显示类型（如 input） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 tableId 查询表定义 CodegenTableDO。
2. 查询该表下全部字段定义 CodegenColumnDO 列表。
3. 通过 CodegenConvert 拼装为 CodegenDetailRespVO（table + columns）返回。

### 2.4 基于数据库的表结构，创建代码生成器的表和字段定义

- **路径**: POST /infra/codegen/create-list
- **权限**: infra:codegen:create
- **说明**: 从指定数据源批量导入表结构，生成 Codegen 的表和字段定义。

**请求参数 (CodegenCreateListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| dataSourceConfigId | Long | 是 | @NotNull | 数据源配置的编号 |
| tableNames | List&lt;String&gt; | 是 | @NotNull | 表名数组 |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt;（导入成功的表定义编号数组）

**业务逻辑**:
1. 遍历表名数组，逐个表执行导入（事务内）。
2. 从数据源获取表的 TableInfo 结构；校验表存在（CODEGEN_IMPORT_TABLE_NULL）、表注释非空、字段非空、每个字段注释非空。
3. 校验同数据源下该表名未被导入过，否则抛出"表定义已经存在"。
4. 通过 CodegenBuilder 将 TableInfo 构建为 CodegenTableDO（类名驼峰转换、模块/业务名推断等），设置数据源编号、默认生成场景为管理后台、前端类型取 CodegenProperties 配置、作者为当前登录用户昵称，插入 codegen_table。
5. 通过 CodegenBuilder 构建字段列表 CodegenColumnDO（按字段名后缀推断查询条件与显示类型，如 name→LIKE、time/date→BETWEEN、status/sex→RADIO、image/file→上传控件、content/description→富文本等）；若无主键则将第一个字段视为主键，批量插入 codegen_column。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_004_001 | 导入的表不存在 |
| 1_001_004_002 | 表定义已经存在 |
| 1_001_004_002 | 导入的字段不存在 |
| 1_001_004_008 | 数据库的表注释未填写 |
| 1_001_004_009 | 数据库的表字段({})注释未填写 |

### 2.5 更新数据库的表和字段定义

- **路径**: PUT /infra/codegen/update
- **权限**: infra:codegen:update
- **说明**: 修改指定表定义及其字段定义（编辑生成配置）。

**请求参数 (CodegenUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| table | CodegenTableSaveReqVO | 是 | @Valid @NotNull | 表定义 |
| columns | List&lt;CodegenColumnSaveReqVO&gt; | 是 | @Valid @NotNull | 字段定义列表 |

CodegenTableSaveReqVO 字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 修改时必填 | - | 编号 |
| scene | Integer | 是 | @NotNull | 生成场景，参见 CodegenSceneEnum 枚举 |
| tableName | String | 是 | @NotNull | 表名称 |
| tableComment | String | 是 | @NotNull | 表描述 |
| remark | String | 否 | - | 备注 |
| moduleName | String | 是 | @NotNull | 模块名 |
| businessName | String | 是 | @NotNull | 业务名 |
| className | String | 是 | @NotNull | 类名称 |
| classComment | String | 是 | @NotNull | 类描述 |
| author | String | 是 | @NotNull | 作者 |
| templateType | Integer | 是 | @NotNull | 模板类型，参见 CodegenTemplateTypeEnum 枚举 |
| frontType | Integer | 是 | @NotNull | 前端类型，参见 CodegenFrontTypeEnum 枚举 |
| parentMenuId | Long | 条件必填 | @AssertTrue | 父菜单编号；生成场景为管理后台时必须设置 |
| masterTableId | Long | 条件必填 | @AssertTrue | 主表的编号；模板类型为主子表的子表时必须与关联字段、一对多标识齐全 |
| subJoinColumnId | Long | 条件必填 | @AssertTrue | 子表关联主表的字段编号 |
| subJoinMany | Boolean | 条件必填 | @AssertTrue | 主表与子表是否一对多 |
| treeParentColumnId | Long | 条件必填 | @AssertTrue | 树表的父字段编号；模板类型为树表时必须与名字字段齐全 |
| treeNameColumnId | Long | 条件必填 | @AssertTrue | 树表的名字字段编号 |

CodegenColumnSaveReqVO 字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号 |
| tableId | Long | 是 | @NotNull | 表编号 |
| columnName | String | 是 | @NotNull | 字段名 |
| dataType | String | 是 | @NotNull | 字段类型 |
| columnComment | String | 是 | @NotNull | 字段描述 |
| nullable | Boolean | 是 | @NotNull | 是否允许为空 |
| primaryKey | Boolean | 是 | @NotNull | 是否主键 |
| ordinalPosition | Integer | 是 | @NotNull | 排序 |
| javaType | String | 是 | @NotNull | Java 属性类型 |
| javaField | String | 是 | @NotNull | Java 属性名 |
| dictType | String | 否 | - | 字典类型 |
| example | String | 否 | - | 数据示例 |
| createOperation | Boolean | 是 | @NotNull | 是否为 Create 创建操作的字段 |
| updateOperation | Boolean | 是 | @NotNull | 是否为 Update 更新操作的字段 |
| listOperation | Boolean | 是 | @NotNull | 是否为 List 查询操作的字段 |
| listOperationCondition | String | 是 | @NotNull | List 查询条件类型，参见 CodegenColumnListConditionEnum 枚举 |
| listOperationResult | Boolean | 是 | @NotNull | 是否为 List 查询操作的返回字段 |
| htmlType | String | 是 | @NotNull | 显示类型 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 校验表定义存在，否则抛出"表定义不存在"。
2. 若模板类型为【主子表的子表】，校验关联的主表存在（CODEGEN_MASTER_TABLE_NOT_EXISTS）。
3. 若模板类型为【主子表的子表】，校验子表关联字段（subJoinColumnId）在字段列表中存在（CODEGEN_SUB_COLUMN_NOT_EXISTS）。
4. 更新 codegen_table 表定义记录。
5. 逐条更新 codegen_column 字段定义记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_004_004 | 表定义不存在 |
| 1_001_004_010 | 主表(id={})定义不存在，请检查 |
| 1_001_004_011 | 子表的字段(id={})不存在，请检查 |

### 2.6 基于数据库的表结构，同步数据库的表和字段定义

- **路径**: PUT /infra/codegen/sync-from-db
- **权限**: infra:codegen:update
- **说明**: 以数据库最新表结构为准，同步指定表已导入的字段定义（新增/删除字段）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| tableId | Long | 是 | @RequestParam 必填 | 表编号 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 校验表定义存在，否则抛出"表定义不存在"。
2. 从原数据源重新读取该表的最新 TableInfo 结构。
3. 校验表注释非空、字段非空、字段注释非空。
4. 将数据库字段与已导入字段逐个对比（JDBC 类型、是否可空、是否主键、注释、字段位置），计算需要【修改】（删除后重建）的字段名集合。
5. 计算【删除】的字段：数据库中已不存在、或属于需重建的字段。
6. 若既无新增字段也无删除字段，抛出"同步失败，不存在改变"。
7. 通过 CodegenBuilder 构建并批量插入新增/重建的字段，删除失效字段记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_004_001 | 导入的表不存在 |
| 1_001_004_004 | 表定义不存在 |
| 1_001_004_007 | 同步失败，不存在改变 |
| 1_001_004_008 | 数据库的表注释未填写 |
| 1_001_004_009 | 数据库的表字段({})注释未填写 |

### 2.7 删除数据库的表和字段定义

- **路径**: DELETE /infra/codegen/delete
- **权限**: infra:codegen:delete
- **说明**: 删除指定表的表定义及其全部字段定义。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| tableId | Long | 是 | @RequestParam 必填 | 表编号 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 校验表定义存在，否则抛出"表定义不存在"。
2. 删除 codegen_table 表定义记录。
3. 删除该表下全部 codegen_column 字段定义记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_004_004 | 表定义不存在 |

### 2.8 批量删除数据库的表和字段定义

- **路径**: DELETE /infra/codegen/delete-list
- **权限**: infra:codegen:delete
- **说明**: 批量删除多个表的表定义及对应字段定义。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| tableIds | List&lt;Long&gt; | 是 | @RequestParam 必填 | 表编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（true）

**业务逻辑**:
1. 按 tableIds 批量删除 codegen_table 表定义记录。
2. 批量删除这些表下的 codegen_column 字段定义记录。

## 3. 代码生成

### 3.1 预览生成代码

- **路径**: GET /infra/codegen/preview
- **权限**: infra:codegen:preview
- **说明**: 基于表和字段的生成配置，渲染模板并返回每个生成文件的路径与代码内容。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| tableId | Long | 是 | @RequestParam 必填 | 表编号 |

**响应**: CommonResult&lt;List&lt;CodegenPreviewRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| filePath | String | 文件路径 |
| code | String | 生成的代码内容 |

**业务逻辑**:
1. 校验表定义存在，否则抛出"表定义不存在"；校验字段列表非空，否则抛出"字段义不存在"。
2. 若模板类型为【主子表的主表】，查询其全部子表；无子表则抛出"主表生成代码失败，原因：它没有子表"。
3. 逐个校验每个子表的关联字段（subJoinColumnId）存在，否则抛出"子表的字段(id={})不存在"。
4. 根据数据源 URL 解析数据库类型 DbType。
5. 调用 CodegenEngine 执行生成：基于 Velocity 模板引擎，使用后端模板（Controller/VO/Service/Mapper/DO/错误码等）与前端模板渲染，填充表、字段、主子表等上下文变量，输出 Map&lt;文件路径, 代码&gt;。
6. 转换为 CodegenPreviewRespVO 列表返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_004_004 | 表定义不存在 |
| 1_001_004_005 | 字段义不存在 |
| 1_001_004_011 | 子表的字段(id={})不存在，请检查 |
| 1_001_004_012 | 主表生成代码失败，原因：它没有子表 |
| 1_001_004_013 | 主子表规范化类名({})重复，请调整主表或子表类名 |
| 1_001_004_014 | 主子表属性名({})重复，请调整主表字段、子表类名或关联关系 |

### 3.2 下载生成代码

- **路径**: GET /infra/codegen/download
- **权限**: infra:codegen:download
- **说明**: 生成代码并打包为 zip 文件下载。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| tableId | Long | 是 | @RequestParam 必填 | 表编号 |

**响应**: 非 CommonResult 包装，直接输出 zip 附件（文件名 codegen.zip）

**业务逻辑**:
1. 调用 generationCodes 生成代码（逻辑同 3.1 的第 1-5 步，含表/字段/主子表校验）。
2. 将生成结果的文件路径与代码内容（UTF-8 流）通过 ZipUtil 打包为 zip 字节流。
3. 通过 writeAttachment 将 zip 以附件形式写回响应，文件名为 codegen.zip。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_004_004 | 表定义不存在 |
| 1_001_004_005 | 字段义不存在 |
| 1_001_004_011 | 子表的字段(id={})不存在，请检查 |
| 1_001_004_012 | 主表生成代码失败，原因：它没有子表 |
| 1_001_004_013 | 主子表规范化类名({})重复，请调整主表或子表类名 |
| 1_001_004_014 | 主子表属性名({})重复，请调整主表字段、子表类名或关联关系 |
