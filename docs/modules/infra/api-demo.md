# 代码生成示例接口 (Demo01ContactController / Demo02CategoryController / Demo03Student*Controller)

> infra 模块的代码生成器示例域：包含单表示例（示例联系人）、树表示例（示例分类）以及同一主子表结构的三种代码生成模式示例（学生 + 课程/班级子表），用于展示 yudao 代码生成器产出的标准 CRUD 代码形态。

## 接口路径前缀

- /infra/demo01-contact  (Controller: Demo01ContactController)
- /infra/demo02-category  (Controller: Demo02CategoryController)
- /infra/demo03-student-erp  (Controller: Demo03StudentErpController)
- /infra/demo03-student-inner  (Controller: Demo03StudentInnerController)
- /infra/demo03-student-normal  (Controller: Demo03StudentNormalController)

## 1. 示例联系人（单表示例，Demo01ContactController）

### 1.1 创建示例联系人

- **路径**: POST /infra/demo01-contact/create
- **权限**: infra:demo01-contact:create
- **说明**: 新增一条示例联系人记录。

**请求参数 (Demo01ContactSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| name | String | 是 | @NotEmpty | 名字 |
| sex | Integer | 是 | @NotNull | 性别（字典 system_user_sex） |
| birthday | LocalDateTime | 是 | @NotNull | 出生年 |
| description | String | 是 | @NotEmpty | 简介 |
| avatar | String | 否 | 无 | 头像 |

**响应**: CommonResult&lt;Long&gt;（新创建的联系人编号）

**业务逻辑**:
1. 将请求 VO 转换为 Demo01ContactDO。
2. 插入数据库。
3. 返回新记录编号。

### 1.2 更新示例联系人

- **路径**: PUT /infra/demo01-contact/update
- **权限**: infra:demo01-contact:update
- **说明**: 按编号修改示例联系人。

**请求参数 (Demo01ContactSaveReqVO)**: 同 [1.1 创建示例联系人](#11-创建示例联系人)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验示例联系人是否存在，不存在则抛出异常。
2. 将请求 VO 转换为 DO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_000 | 示例联系人不存在 |

### 1.3 删除示例联系人

- **路径**: DELETE /infra/demo01-contact/delete
- **权限**: infra:demo01-contact:delete
- **说明**: 删除单条示例联系人。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验示例联系人是否存在。
2. 按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_000 | 示例联系人不存在 |

### 1.4 批量删除示例联系人

- **路径**: DELETE /infra/demo01-contact/delete-list
- **权限**: infra:demo01-contact:delete
- **说明**: 按编号列表批量删除示例联系人。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 批量查询记录，若查询结果为空或数量与 ids 不一致则抛出异常。
2. 按 ids 批量删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_000 | 示例联系人不存在 |

### 1.5 获得示例联系人

- **路径**: GET /infra/demo01-contact/get
- **权限**: infra:demo01-contact:query
- **说明**: 按编号查询单条示例联系人详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo01ContactRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名字 |
| sex | Integer | 性别（字典 system_user_sex，导出 Excel 时自动转换） |
| birthday | LocalDateTime | 出生年 |
| description | String | 简介 |
| avatar | String | 头像 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 DO。
2. 通过 BeanUtils 转换为 RespVO 返回（记录不存在时返回 null 数据）。

### 1.6 获得示例联系人分页

- **路径**: GET /infra/demo01-contact/page
- **权限**: infra:demo01-contact:query
- **说明**: 分页查询示例联系人列表。

**请求参数 (Demo01ContactPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | 无 | 名字，模糊匹配 |
| sex | Integer | 否 | 无 | 性别 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;Demo01ContactRespVO&gt;&gt;，list 内元素字段同 [1.5 获得示例联系人](#15-获得示例联系人) 响应表。

**业务逻辑**:
1. 调用 Mapper 按条件分页查询。
2. 将 PageResult&lt;DO&gt; 转换为 PageResult&lt;RespVO&gt; 返回。

### 1.7 导出示例联系人 Excel

- **路径**: GET /infra/demo01-contact/export-excel
- **权限**: infra:demo01-contact:export
- **说明**: 按查询条件导出全量示例联系人 Excel（文件名 示例联系人.xls），并记录导出操作日志。

**请求参数 (Demo01ContactPageReqVO)**: 同 [1.6 获得示例联系人分页](#16-获得示例联系人分页) 请求参数表。

**响应**: 无 CommonResult 包装，直接以 Excel 文件流输出。

**业务逻辑**:
1. 将分页参数的 pageSize 置为 PAGE_SIZE_NONE（-1），实现不分页查询全量数据。
2. 按条件查询全量 DO 列表并转换为 RespVO 列表。
3. 通过 ExcelUtils 写出 Excel 文件（性别列通过 DictConvert 按字典 system_user_sex 转换）。

## 2. 示例分类（树表示例，Demo02CategoryController）

### 2.1 创建示例分类

- **路径**: POST /infra/demo02-category/create
- **权限**: infra:demo02-category:create
- **说明**: 在指定父级下新增一条示例分类。

**请求参数 (Demo02CategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| name | String | 是 | @NotEmpty | 名字 |
| parentId | Long | 是 | @NotNull | 父级编号（0 表示根节点） |

**响应**: CommonResult&lt;Long&gt;（新创建的分类编号）

**业务逻辑**:
1. 校验父级编号的有效性：parentId 为空或为根（0）时直接通过；不能设置自己为父分类；父分类必须存在（新增场景无需环路校验）。
2. 校验同一父级下名字的唯一性，重复则抛出异常。
3. 将请求 VO 转换为 Demo02CategoryDO 并插入数据库。
4. 返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_003 | 父级示例分类不存在 |
| 1_001_201_004 | 不能设置自己为父示例分类 |
| 1_001_201_005 | 已经存在该名字的示例分类 |

### 2.2 更新示例分类

- **路径**: PUT /infra/demo02-category/update
- **权限**: infra:demo02-category:update
- **说明**: 按编号修改示例分类，含父级有效性（防环路）与同级名字唯一性校验。

**请求参数 (Demo02CategorySaveReqVO)**: 同 [2.1 创建示例分类](#21-创建示例分类)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验示例分类是否存在。
2. 校验父级编号的有效性：不能设置自己为父分类；父分类必须存在；并沿父链逐级向上递归遍历，若发现父链中出现自身 id 则判定会形成环路，抛出异常。
3. 校验同一父级下名字的唯一性（排除自身 id）。
4. 将请求 VO 转换为 DO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_001 | 示例分类不存在 |
| 1_001_201_003 | 父级示例分类不存在 |
| 1_001_201_004 | 不能设置自己为父示例分类 |
| 1_001_201_005 | 已经存在该名字的示例分类 |
| 1_001_201_006 | 不能设置自己的子示例分类为父示例分类 |

### 2.3 删除示例分类

- **路径**: DELETE /infra/demo02-category/delete
- **权限**: infra:demo02-category:delete
- **说明**: 删除单条示例分类，存在子分类时不允许删除。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验示例分类是否存在。
2. 统计以该 id 为父级的子分类数量，大于 0 则抛出异常，禁止删除。
3. 按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_001 | 示例分类不存在 |
| 1_001_201_002 | 存在存在子示例分类，无法删除 |

### 2.4 获得示例分类

- **路径**: GET /infra/demo02-category/get
- **权限**: infra:demo02-category:query
- **说明**: 按编号查询单条示例分类详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo02CategoryRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名字 |
| parentId | Long | 父级编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 DO。
2. 转换为 RespVO 返回（记录不存在时返回 null 数据）。

### 2.5 获得示例分类列表

- **路径**: GET /infra/demo02-category/list
- **权限**: infra:demo02-category:query
- **说明**: 按条件查询全量示例分类列表（不分页），用于树形展示。

**请求参数 (Demo02CategoryListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | 无 | 名字，模糊匹配 |
| parentId | Long | 否 | 无 | 父级编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;List&lt;Demo02CategoryRespVO&gt;&gt;，元素字段同 [2.4 获得示例分类](#24-获得示例分类) 响应表。

**业务逻辑**:
1. 调用 Mapper 按条件查询列表。
2. 转换为 RespVO 列表返回。

### 2.6 导出示例分类 Excel

- **路径**: GET /infra/demo02-category/export-excel
- **权限**: infra:demo02-category:export
- **说明**: 按查询条件导出示例分类 Excel（文件名 示例分类.xls），并记录导出操作日志。

**请求参数 (Demo02CategoryListReqVO)**: 同 [2.5 获得示例分类列表](#25-获得示例分类列表) 请求参数表。

**响应**: 无 CommonResult 包装，直接以 Excel 文件流输出。

**业务逻辑**:
1. 按条件查询全量 DO 列表。
2. 转换为 RespVO 列表。
3. 通过 ExcelUtils 写出 Excel 文件。

## 3. 学生 - ERP 模式（主子表示例，Demo03StudentErpController）

> 主表为学生，子表为学生课程（一对多）与学生班级（一对一）。ERP 模式下子表拥有独立完整的 CRUD 接口，由前端按学生编号逐个维护子表数据。三个 demo03 控制器共用权限标识 infra:demo03-student:* 与 Demo03StudentDO 主表。

### 3.1 创建学生

- **路径**: POST /infra/demo03-student-erp/create
- **权限**: infra:demo03-student:create
- **说明**: 新增一条学生记录（ERP 模式下仅处理主表，不处理子表）。

**请求参数 (Demo03StudentErpSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| name | String | 是 | @NotEmpty | 名字 |
| sex | Integer | 是 | @NotNull | 性别（字典 system_user_sex） |
| birthday | LocalDateTime | 是 | @NotNull | 出生日期 |
| description | String | 是 | @NotEmpty | 简介 |

**响应**: CommonResult&lt;Long&gt;（新创建的学生编号）

**业务逻辑**:
1. 将请求 VO 转换为 Demo03StudentDO。
2. 插入数据库。
3. 返回新记录编号。

### 3.2 更新学生

- **路径**: PUT /infra/demo03-student-erp/update
- **权限**: infra:demo03-student:update
- **说明**: 按编号修改学生主表信息。

**请求参数 (Demo03StudentErpSaveReqVO)**: 同 [3.1 创建学生](#31-创建学生)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验学生是否存在。
2. 将请求 VO 转换为 DO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 3.3 删除学生

- **路径**: DELETE /infra/demo03-student-erp/delete
- **权限**: infra:demo03-student:delete
- **说明**: 删除学生及其全部子表数据（课程、班级）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验学生是否存在。
2. 删除主表记录。
3. 按学生编号删除课程子表数据。
4. 按学生编号删除班级子表数据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 3.4 批量删除学生

- **路径**: DELETE /infra/demo03-student-erp/delete-list
- **权限**: infra:demo03-student:delete
- **说明**: 按编号列表批量删除学生及其全部子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 批量查询学生，结果为空或数量与 ids 不一致则抛出异常。
2. 批量删除主表记录。
3. 按学生编号列表批量删除课程子表数据。
4. 按学生编号列表批量删除班级子表数据。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 3.5 获得学生

- **路径**: GET /infra/demo03-student-erp/get
- **权限**: infra:demo03-student:query
- **说明**: 按编号查询单条学生详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo03StudentErpRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名字 |
| sex | Integer | 性别（字典 system_user_sex，导出 Excel 时自动转换） |
| birthday | LocalDateTime | 出生日期 |
| description | String | 简介 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 DO。
2. 转换为 RespVO 返回（记录不存在时返回 null 数据）。

### 3.6 获得学生分页

- **路径**: GET /infra/demo03-student-erp/page
- **权限**: infra:demo03-student:query
- **说明**: 分页查询学生列表。

**请求参数 (Demo03StudentErpPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | 无 | 名字，模糊匹配 |
| sex | Integer | 否 | 无 | 性别 |
| description | String | 否 | 无 | 简介，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;Demo03StudentErpRespVO&gt;&gt;，list 内元素字段同 [3.5 获得学生](#35-获得学生) 响应表。

**业务逻辑**:
1. 调用 Mapper 按条件分页查询。
2. 转换为 PageResult&lt;RespVO&gt; 返回。

### 3.7 导出学生 Excel

- **路径**: GET /infra/demo03-student-erp/export-excel
- **权限**: infra:demo03-student:export
- **说明**: 按查询条件导出全量学生 Excel（文件名 学生.xls），并记录导出操作日志。

**请求参数 (Demo03StudentErpPageReqVO)**: 同 [3.6 获得学生分页](#36-获得学生分页) 请求参数表。

**响应**: 无 CommonResult 包装，直接以 Excel 文件流输出。

**业务逻辑**:
1. 将分页参数的 pageSize 置为 PAGE_SIZE_NONE（-1），不分页查询全量数据。
2. 转换为 RespVO 列表。
3. 通过 ExcelUtils 写出 Excel 文件。

### 3.8 获得学生课程分页（子表）

- **路径**: GET /infra/demo03-student-erp/demo03-course/page
- **权限**: infra:demo03-student:query
- **说明**: 按学生编号分页查询其课程子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| studentId | Long | 是 | 无（@RequestParam） | 学生编号 |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码（PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（PageParam，默认 10） |

**响应**: CommonResult&lt;PageResult&lt;Demo03CourseDO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| studentId | Long | 学生编号 |
| name | String | 名字 |
| score | Integer | 分数 |
| creator / createTime / updater / updateTime / deleted | - | 继承自 BaseDO 的通用字段 |

**业务逻辑**:
1. 按学生编号分页查询课程子表。
2. 直接返回 DO 分页结果（子表接口未做 VO 转换）。

### 3.9 创建学生课程（子表）

- **路径**: POST /infra/demo03-student-erp/demo03-course/create
- **权限**: infra:demo03-student:create
- **说明**: 为指定学生新增一条课程记录，请求体直接使用 Demo03CourseDO。

**请求参数 (Demo03CourseDO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| studentId | Long | 是 | 无 | 学生编号 |
| name | String | 是 | 无 | 课程名字 |
| score | Integer | 是 | 无 | 分数 |

**响应**: CommonResult&lt;Long&gt;（新创建的课程编号）

**业务逻辑**:
1. 插入课程子表记录。
2. 返回新记录编号。

### 3.10 更新学生课程（子表）

- **路径**: PUT /infra/demo03-student-erp/demo03-course/update
- **权限**: infra:demo03-student:update
- **说明**: 按编号修改课程记录。

**请求参数 (Demo03CourseDO)**: 同 [3.9 创建学生课程](#39-创建学生课程) 请求参数表，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验课程是否存在，不存在则抛出异常。
2. 调用 clean() 重置 DO 的基础字段后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_008 | 学生课程不存在 |

### 3.11 删除学生课程（子表）

- **路径**: DELETE /infra/demo03-student-erp/demo03-course/delete
- **权限**: infra:demo03-student:delete
- **说明**: 删除单条课程记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 id 直接删除课程记录。

### 3.12 批量删除学生课程（子表）

- **路径**: DELETE /infra/demo03-student-erp/demo03-course/delete-list
- **权限**: infra:demo03-student:delete
- **说明**: 按编号列表批量删除课程记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 直接批量删除课程记录。

### 3.13 获得学生课程（子表）

- **路径**: GET /infra/demo03-student-erp/demo03-course/get
- **权限**: infra:demo03-student:query
- **说明**: 按编号查询单条课程记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo03CourseDO&gt;，字段同 [3.8 获得学生课程分页](#38-获得学生课程分页子表) 响应表。

**业务逻辑**:
1. 按 id 查询并返回课程 DO。

### 3.14 获得学生班级分页（子表）

- **路径**: GET /infra/demo03-student-erp/demo03-grade/page
- **权限**: infra:demo03-student:query
- **说明**: 按学生编号分页查询其班级子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| studentId | Long | 是 | 无（@RequestParam） | 学生编号 |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码（PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（PageParam，默认 10） |

**响应**: CommonResult&lt;PageResult&lt;Demo03GradeDO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| studentId | Long | 学生编号 |
| name | String | 名字 |
| teacher | String | 班主任 |
| creator / createTime / updater / updateTime / deleted | - | 继承自 BaseDO 的通用字段 |

**业务逻辑**:
1. 按学生编号分页查询班级子表。
2. 直接返回 DO 分页结果。

### 3.15 创建学生班级（子表）

- **路径**: POST /infra/demo03-student-erp/demo03-grade/create
- **权限**: infra:demo03-student:create
- **说明**: 为指定学生新增班级记录，一个学生仅允许存在一条班级数据。

**请求参数 (Demo03GradeDO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| studentId | Long | 是 | 无 | 学生编号 |
| name | String | 是 | 无 | 班级名字 |
| teacher | String | 是 | 无 | 班主任 |

**响应**: CommonResult&lt;Long&gt;（新创建的班级编号）

**业务逻辑**:
1. 按学生编号查询已有班级，若已存在则抛出异常（一对一约束）。
2. 插入班级子表记录。
3. 返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_010 | 学生班级已存在 |

### 3.16 更新学生班级（子表）

- **路径**: PUT /infra/demo03-student-erp/demo03-grade/update
- **权限**: infra:demo03-student:update
- **说明**: 按编号修改班级记录。

**请求参数 (Demo03GradeDO)**: 同 [3.15 创建学生班级](#315-创建学生班级子表) 请求参数表，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验班级是否存在，不存在则抛出异常。
2. 调用 clean() 重置 DO 的基础字段后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_009 | 学生班级不存在 |

### 3.17 删除学生班级（子表）

- **路径**: DELETE /infra/demo03-student-erp/demo03-grade/delete
- **权限**: infra:demo03-student:delete
- **说明**: 删除单条班级记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 id 直接删除班级记录。

### 3.18 批量删除学生班级（子表）

- **路径**: DELETE /infra/demo03-student-erp/demo03-grade/delete-list
- **权限**: infra:demo03-student:delete
- **说明**: 按编号列表批量删除班级记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 直接批量删除班级记录。

### 3.19 获得学生班级（子表）

- **路径**: GET /infra/demo03-student-erp/demo03-grade/get
- **权限**: infra:demo03-student:query
- **说明**: 按编号查询单条班级记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo03GradeDO&gt;，字段同 [3.14 获得学生班级分页](#314-获得学生班级分页子表) 响应表。

**业务逻辑**:
1. 按 id 查询并返回班级 DO。

## 4. 学生 - Inner 模式（主子表示例，Demo03StudentInnerController）

> Inner（内嵌）模式下，子表数据随主表一起提交保存：SaveReqVO 内嵌课程列表与班级对象；查询时通过独立接口按学生编号获取子表数据。

### 4.1 创建学生

- **路径**: POST /infra/demo03-student-inner/create
- **权限**: infra:demo03-student:create
- **说明**: 新增学生，并一次性保存内嵌的课程列表与班级数据。

**请求参数 (Demo03StudentInnerSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| name | String | 是 | @NotEmpty | 名字 |
| sex | Integer | 是 | @NotNull | 性别（字典 system_user_sex） |
| birthday | LocalDateTime | 是 | @NotNull | 出生日期 |
| description | String | 是 | @NotEmpty | 简介 |
| demo03Courses | List&lt;Demo03CourseDO&gt; | 否 | 无 | 学生课程列表，元素字段：id/studentId/name/score |
| demo03Grade | Demo03GradeDO | 否 | 无 | 学生班级，字段：id/studentId/name/teacher |

**响应**: CommonResult&lt;Long&gt;（新创建的学生编号）

**业务逻辑**:
1. 将请求 VO 转换为 Demo03StudentDO，插入主表。
2. 为课程列表逐条设置学生编号后批量插入课程子表。
3. 若班级对象不为空，设置学生编号后插入班级子表。
4. 返回学生编号。以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 4.2 更新学生

- **路径**: PUT /infra/demo03-student-inner/update
- **权限**: infra:demo03-student:update
- **说明**: 更新学生主表，并对子表做增量 diff 更新。

**请求参数 (Demo03StudentInnerSaveReqVO)**: 同 [4.1 创建学生](#41-创建学生)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验学生是否存在。
2. 更新主表记录。
3. 课程子表增量更新：以 id 相同作为匹配条件，计算数据库旧列表与提交新列表的差异，分三段处理——批量插入新增记录、批量更新存在记录、批量删除被移除记录。
4. 班级子表：若提交的班级对象不为空，设置学生编号后执行 insertOrUpdate。
5. 以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 4.3 删除学生

- **路径**: DELETE /infra/demo03-student-inner/delete
- **权限**: infra:demo03-student:delete
- **说明**: 删除学生及其全部子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验学生是否存在。
2. 删除主表记录。
3. 按学生编号删除课程子表数据。
4. 按学生编号删除班级子表数据。
5. 以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 4.4 批量删除学生

- **路径**: DELETE /infra/demo03-student-inner/delete-list
- **权限**: infra:demo03-student:delete
- **说明**: 按编号列表批量删除学生及其全部子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 批量查询学生，结果为空或数量与 ids 不一致则抛出异常。
2. 批量删除主表记录。
3. 按学生编号列表批量删除课程子表数据。
4. 按学生编号列表批量删除班级子表数据。
5. 以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 4.5 获得学生

- **路径**: GET /infra/demo03-student-inner/get
- **权限**: infra:demo03-student:query
- **说明**: 按编号查询单条学生详情（仅主表）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo03StudentInnerRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名字 |
| sex | Integer | 性别（字典 system_user_sex，导出 Excel 时自动转换） |
| birthday | LocalDateTime | 出生日期 |
| description | String | 简介 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 DO。
2. 转换为 RespVO 返回（记录不存在时返回 null 数据）。

### 4.6 获得学生分页

- **路径**: GET /infra/demo03-student-inner/page
- **权限**: infra:demo03-student:query
- **说明**: 分页查询学生列表。

**请求参数 (Demo03StudentInnerPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | 无 | 名字，模糊匹配 |
| sex | Integer | 否 | 无 | 性别 |
| description | String | 否 | 无 | 简介，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;Demo03StudentInnerRespVO&gt;&gt;，list 内元素字段同 [4.5 获得学生](#45-获得学生) 响应表。

**业务逻辑**:
1. 调用 Mapper 按条件分页查询。
2. 转换为 PageResult&lt;RespVO&gt; 返回。

### 4.7 导出学生 Excel

- **路径**: GET /infra/demo03-student-inner/export-excel
- **权限**: infra:demo03-student:export
- **说明**: 按查询条件导出全量学生 Excel（文件名 学生.xls），并记录导出操作日志。

**请求参数 (Demo03StudentInnerPageReqVO)**: 同 [4.6 获得学生分页](#46-获得学生分页) 请求参数表。

**响应**: 无 CommonResult 包装，直接以 Excel 文件流输出。

**业务逻辑**:
1. 将分页参数的 pageSize 置为 PAGE_SIZE_NONE（-1），不分页查询全量数据。
2. 转换为 RespVO 列表。
3. 通过 ExcelUtils 写出 Excel 文件。

### 4.8 获得学生课程列表（子表）

- **路径**: GET /infra/demo03-student-inner/demo03-course/list-by-student-id
- **权限**: infra:demo03-student:query
- **说明**: 按学生编号查询其全部课程子表数据（不分页）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| studentId | Long | 是 | 无（@RequestParam） | 学生编号 |

**响应**: CommonResult&lt;List&lt;Demo03CourseDO&gt;&gt;，元素字段同 [3.8 获得学生课程分页](#38-获得学生课程分页子表) 响应表。

**业务逻辑**:
1. 按学生编号查询课程列表并直接返回 DO 列表。

### 4.9 获得学生班级（子表）

- **路径**: GET /infra/demo03-student-inner/demo03-grade/get-by-student-id
- **权限**: infra:demo03-student:query
- **说明**: 按学生编号查询其班级子表数据（一对一）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| studentId | Long | 是 | 无（@RequestParam） | 学生编号 |

**响应**: CommonResult&lt;Demo03GradeDO&gt;，字段同 [3.14 获得学生班级分页](#314-获得学生班级分页子表) 响应表。

**业务逻辑**:
1. 按学生编号查询班级记录并直接返回 DO。

## 5. 学生 - Normal 模式（主子表示例，Demo03StudentNormalController）

> Normal（标准）模式的后端接口结构与 Inner 模式完全一致（控制器、Service、Mapper 均为独立一套，业务逻辑相同），差异体现在代码生成器产出的前端页面组织方式。路径前缀为 /infra/demo03-student-normal。

### 5.1 创建学生

- **路径**: POST /infra/demo03-student-normal/create
- **权限**: infra:demo03-student:create
- **说明**: 新增学生，并一次性保存课程列表与班级数据。

**请求参数 (Demo03StudentNormalSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号，创建时不传 |
| name | String | 是 | @NotEmpty | 名字 |
| sex | Integer | 是 | @NotNull | 性别（字典 system_user_sex） |
| birthday | LocalDateTime | 是 | @NotNull | 出生日期 |
| description | String | 是 | @NotEmpty | 简介 |
| demo03Courses | List&lt;Demo03CourseDO&gt; | 否 | 无 | 学生课程列表，元素字段：id/studentId/name/score |
| demo03Grade | Demo03GradeDO | 否 | 无 | 学生班级，字段：id/studentId/name/teacher |

**响应**: CommonResult&lt;Long&gt;（新创建的学生编号）

**业务逻辑**:
1. 将请求 VO 转换为 Demo03StudentDO，插入主表。
2. 为课程列表逐条设置学生编号后批量插入课程子表。
3. 若班级对象不为空，设置学生编号后插入班级子表。
4. 返回学生编号。以上步骤在同一事务内执行。

### 5.2 更新学生

- **路径**: PUT /infra/demo03-student-normal/update
- **权限**: infra:demo03-student:update
- **说明**: 更新学生主表，并对子表做增量 diff 更新。

**请求参数 (Demo03StudentNormalSaveReqVO)**: 同 [5.1 创建学生](#51-创建学生)，修改时 id 必传。

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验学生是否存在。
2. 更新主表记录。
3. 课程子表增量更新：以 id 相同作为匹配条件计算新旧列表差异，批量插入新增记录、批量更新存在记录、批量删除被移除记录。
4. 班级子表：若提交的班级对象不为空，设置学生编号后执行 insertOrUpdate。
5. 以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 5.3 删除学生

- **路径**: DELETE /infra/demo03-student-normal/delete
- **权限**: infra:demo03-student:delete
- **说明**: 删除学生及其全部子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 校验学生是否存在。
2. 删除主表记录。
3. 按学生编号删除课程子表数据。
4. 按学生编号删除班级子表数据。
5. 以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 5.4 批量删除学生

- **路径**: DELETE /infra/demo03-student-normal/delete-list
- **权限**: infra:demo03-student:delete
- **说明**: 按编号列表批量删除学生及其全部子表数据。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | 无（@RequestParam） | 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 按 ids 批量查询学生，结果为空或数量与 ids 不一致则抛出异常。
2. 批量删除主表记录。
3. 按学生编号列表批量删除课程子表数据。
4. 按学生编号列表批量删除班级子表数据。
5. 以上步骤在同一事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_007 | 学生不存在 |

### 5.5 获得学生

- **路径**: GET /infra/demo03-student-normal/get
- **权限**: infra:demo03-student:query
- **说明**: 按编号查询单条学生详情（仅主表）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | 无（@RequestParam） | 编号 |

**响应**: CommonResult&lt;Demo03StudentNormalRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名字 |
| sex | Integer | 性别（字典 system_user_sex，导出 Excel 时自动转换） |
| birthday | LocalDateTime | 出生日期 |
| description | String | 简介 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 DO。
2. 转换为 RespVO 返回（记录不存在时返回 null 数据）。

### 5.6 获得学生分页

- **路径**: GET /infra/demo03-student-normal/page
- **权限**: infra:demo03-student:query
- **说明**: 分页查询学生列表。

**请求参数 (Demo03StudentNormalPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10） |
| name | String | 否 | 无 | 名字，模糊匹配 |
| sex | Integer | 否 | 无 | 性别 |
| description | String | 否 | 无 | 简介，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;Demo03StudentNormalRespVO&gt;&gt;，list 内元素字段同 [5.5 获得学生](#55-获得学生) 响应表。

**业务逻辑**:
1. 调用 Mapper 按条件分页查询。
2. 转换为 PageResult&lt;RespVO&gt; 返回。

### 5.7 导出学生 Excel

- **路径**: GET /infra/demo03-student-normal/export-excel
- **权限**: infra:demo03-student:export
- **说明**: 按查询条件导出全量学生 Excel（文件名 学生.xls），并记录导出操作日志。

**请求参数 (Demo03StudentNormalPageReqVO)**: 同 [5.6 获得学生分页](#56-获得学生分页) 请求参数表。

**响应**: 无 CommonResult 包装，直接以 Excel 文件流输出。

**业务逻辑**:
1. 将分页参数的 pageSize 置为 PAGE_SIZE_NONE（-1），不分页查询全量数据。
2. 转换为 RespVO 列表。
3. 通过 ExcelUtils 写出 Excel 文件。

### 5.8 获得学生课程列表（子表）

- **路径**: GET /infra/demo03-student-normal/demo03-course/list-by-student-id
- **权限**: infra:demo03-student:query
- **说明**: 按学生编号查询其全部课程子表数据（不分页）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| studentId | Long | 是 | 无（@RequestParam） | 学生编号 |

**响应**: CommonResult&lt;List&lt;Demo03CourseDO&gt;&gt;，元素字段同 [3.8 获得学生课程分页](#38-获得学生课程分页子表) 响应表。

**业务逻辑**:
1. 按学生编号查询课程列表并直接返回 DO 列表。

### 5.9 获得学生班级（子表）

- **路径**: GET /infra/demo03-student-normal/demo03-grade/get-by-student-id
- **权限**: infra:demo03-student:query
- **说明**: 按学生编号查询其班级子表数据（一对一）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| studentId | Long | 是 | 无（@RequestParam） | 学生编号 |

**响应**: CommonResult&lt;Demo03GradeDO&gt;，字段同 [3.14 获得学生班级分页](#314-获得学生班级分页子表) 响应表。

**业务逻辑**:
1. 按学生编号查询班级记录并直接返回 DO。

## 6. 三种主子表生成模式对比

| 模式 | 路径前缀 | 子表保存方式 | 子表查询接口 |
|-----|---------|------------|------------|
| ERP 模式 | /infra/demo03-student-erp | 前端调用子表独立 CRUD 接口（create/update/delete）逐条维护 | 子表独立 page / get 接口 |
| Inner 内嵌模式 | /infra/demo03-student-inner | 子表数据内嵌在主表 SaveReqVO 中，随主表一次事务保存（课程 diff 增量更新、班级 insertOrUpdate） | list-by-student-id / get-by-student-id |
| Normal 标准模式 | /infra/demo03-student-normal | 与 Inner 模式后端逻辑一致，前端页面组织方式不同 | list-by-student-id / get-by-student-id |

**本域错误码汇总（1_001_201_000 段）**:

| 错误码 | 说明 |
|-------|------|
| 1_001_201_000 | 示例联系人不存在 |
| 1_001_201_001 | 示例分类不存在 |
| 1_001_201_002 | 存在存在子示例分类，无法删除 |
| 1_001_201_003 | 父级示例分类不存在 |
| 1_001_201_004 | 不能设置自己为父示例分类 |
| 1_001_201_005 | 已经存在该名字的示例分类 |
| 1_001_201_006 | 不能设置自己的子示例分类为父示例分类 |
| 1_001_201_007 | 学生不存在 |
| 1_001_201_008 | 学生课程不存在 |
| 1_001_201_009 | 学生班级不存在 |
| 1_001_201_010 | 学生班级已存在 |
