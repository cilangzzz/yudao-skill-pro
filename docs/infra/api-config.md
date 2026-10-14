# 参数配置接口 (ConfigController)

> 提供系统参数配置（键值对形式）的管理能力，包括参数的增删改查、按 key 取值以及 Excel 导出；参数分为系统内置与用户自定义两种类型。

## 接口路径前缀

/infra/config  (Controller: ConfigController)

## 1. 参数配置管理（增删改）

### 1.1 创建参数配置

- **路径**: POST /infra/config/create
- **权限**: infra:config:create
- **说明**: 新增一条用户自定义参数配置，key 全局唯一。

**请求参数 (ConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 参数配置序号，创建时不传 |
| category | String | 是 | @NotEmpty、@Size(max=50) | 参数分组，如 biz |
| name | String | 是 | @NotBlank、@Size(max=100) | 参数名称 |
| key | String | 是 | @NotBlank、@Size(max=100) | 参数键名，如 yunai.db.username |
| value | String | 是 | @NotBlank、@Size(max=500) | 参数键值 |
| visible | Boolean | 是 | @NotNull | 是否可见 |
| remark | String | 否 | 无 | 备注 |

**响应**: CommonResult&lt;Long&gt;（新创建的参数配置编号）

**业务逻辑**:
1. 校验参数 key 的唯一性（数据库中已存在同 key 配置则抛出异常）。
2. 将请求 VO 转换为 ConfigDO。
3. 强制设置参数类型为自定义配置（ConfigTypeEnum.CUSTOM = 2），不允许通过接口创建系统内置参数。
4. 插入数据库并返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_000_002 | 参数配置 key 重复 |

### 1.2 修改参数配置

- **路径**: PUT /infra/config/update
- **权限**: infra:config:update
- **说明**: 按 id 修改参数配置内容，key 不可与其他配置重复。

**请求参数 (ConfigSaveReqVO)**: 同 [1.1 创建参数配置](#11-创建参数配置)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验待修改的参数配置是否存在。
2. 校验参数 key 的唯一性（排除自身 id）。
3. 将请求 VO 转换为 ConfigDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_000_001 | 参数配置不存在 |
| 1_001_000_002 | 参数配置 key 重复 |

### 1.3 删除参数配置

- **路径**: DELETE /infra/config/delete
- **权限**: infra:config:delete
- **说明**: 删除单条参数配置，系统内置类型不允许删除。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 参数配置编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验参数配置是否存在，并查询出记录。
2. 若参数类型为系统内置（ConfigTypeEnum.SYSTEM = 1），抛出异常禁止删除。
3. 按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_000_001 | 参数配置不存在 |
| 1_001_000_003 | 不能删除类型为系统内置的参数配置 |

### 1.4 批量删除参数配置

- **路径**: DELETE /infra/config/delete-list
- **权限**: infra:config:delete
- **说明**: 按编号列表批量删除参数配置，任一为系统内置类型则整体失败。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 参数配置编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 批量查询参数配置记录。
2. 遍历校验，只要存在任一系统内置类型（ConfigTypeEnum.SYSTEM）的配置即抛出异常。
3. 按 ids 批量删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_000_003 | 不能删除类型为系统内置的参数配置 |

## 2. 参数配置查询

### 2.1 获得参数配置

- **路径**: GET /infra/config/get
- **权限**: infra:config:query
- **说明**: 按编号获取单条参数配置详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 参数配置编号 |

**响应**: CommonResult&lt;ConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 参数配置序号 |
| category | String | 参数分类 |
| name | String | 参数名称 |
| key | String | 参数键名 |
| value | String | 参数键值 |
| type | Integer | 参数类型，参见 SysConfigTypeEnum 枚举（1=系统配置，2=自定义配置） |
| visible | Boolean | 是否可见 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询参数配置记录。
2. 通过 ConfigConvert 转换为 ConfigRespVO 返回。

### 2.2 根据参数键名查询参数值

- **路径**: GET /infra/config/get-value-by-key
- **权限**: 已认证（无 @PreAuthorize 权限注解，登录即可访问）
- **说明**: 按参数键名获取参数键值；不可见的配置不允许返回给前端。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| key | String | 是 | 无（@RequestParam） | 参数键名，如 yunai.biz.username |

**响应**: CommonResult&lt;String&gt;（参数键值）

**业务逻辑**:
1. 按参数键名查询配置记录。
2. 记录不存在时直接返回 null（不抛异常）。
3. 配置的 visible 为 false（不可见）时，抛出异常拒绝返回。
4. 校验通过后返回参数键值。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_000_004 | 获取参数配置失败，原因：不允许获取不可见配置 |

### 2.3 获取参数配置分页

- **路径**: GET /infra/config/page
- **权限**: infra:config:query
- **说明**: 按条件分页查询参数配置列表。

**请求参数 (ConfigPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam，默认 1） | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam，默认 10） | 每页条数 |
| name | String | 否 | 无 | 参数名称，模糊匹配 |
| key | String | 否 | 无 | 参数键名，模糊匹配 |
| type | Integer | 否 | 无 | 参数类型，参见 SysConfigTypeEnum 枚举 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ConfigRespVO&gt;&gt;（PageResult.list 为 ConfigRespVO 数组，字段同 [2.1 获得参数配置](#21-获得参数配置)）

**业务逻辑**:
1. 按名称模糊、键名模糊、参数类型、创建时间区间等条件分页查询。
2. 通过 ConfigConvert 将分页结果转换为 ConfigRespVO 返回。

## 3. 数据导出

### 3.1 导出参数配置

- **路径**: GET /infra/config/export-excel
- **权限**: infra:config:export
- **说明**: 按查询条件导出全部参数配置为 Excel 文件（操作类型记录为导出）。

**请求参数 (ConfigPageReqVO)**: 同 [2.3 获取参数配置分页](#23-获取参数配置分页)（导出时服务端强制 pageSize 为 -1 即不分页，查询全部数据）。

**响应**: 无 CommonResult 包装，直接输出 Excel 文件流（文件名「参数配置.xls」，导出列来自 ConfigRespVO 上的 @ExcelProperty 注解）。

**业务逻辑**:
1. 将请求的 pageSize 设置为 PageParam.PAGE_SIZE_NONE（-1），即不分页。
2. 按条件查询全部参数配置列表。
3. 通过 ConfigConvert 转换为 ConfigRespVO 列表。
4. 通过 ExcelUtils 写出 Excel 文件流返回前端。

## 附录：本域错误码汇总

infra 模块错误码使用 1-001-000-000 段，参数配置相关错误码如下：

| 错误码 | 说明 |
|-------|------|
| 1_001_000_001 | 参数配置不存在 |
| 1_001_000_002 | 参数配置 key 重复 |
| 1_001_000_003 | 不能删除类型为系统内置的参数配置 |
| 1_001_000_004 | 获取参数配置失败，原因：不允许获取不可见配置 |
