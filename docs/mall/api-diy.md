# 装修模板与页面接口 (DiyTemplateController / DiyPageController)

> 商城 DIY 装修域：管理店铺装修模板（含"使用中"唯一启用机制）与装修页面（首页/我的等），页面属性以 JSON 形式存储供前端装修组件渲染。

## 接口路径前缀

- /promotion/diy-template  (Controller: DiyTemplateController)
- /promotion/diy-page  (Controller: DiyPageController)

## 1. 装修模板（DiyTemplateController）

### 1.1 创建装修模板

- **路径**: POST /promotion/diy-template/create
- **权限**: promotion:diy-template:create
- **说明**: 创建装修模板，并自动创建"首页""我的"两个默认页面。

**请求参数 (DiyTemplateCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotEmpty | 模板名称 |
| remark | String | 否 | - | 备注 |
| previewPicUrls | List\<String\> | 否 | - | 预览图列表 |

**响应**: CommonResult\<Long\>，返回新模板编号。

**业务逻辑**:
1. 校验模板名称唯一（名称已存在时抛出 DIY_TEMPLATE_NAME_USED）。
2. 转换为 DO 插入数据库，property 属性初始化为 "{}"。
3. 事务内调用 DiyPageService 创建两个默认装修页面："首页"、"我的"，备注为"模板【xxx】自动创建"。
4. 返回新模板编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_017_001 | 装修模板名称({})已经被使用 |

### 1.2 更新装修模板

- **路径**: PUT /promotion/diy-template/update
- **权限**: promotion:diy-template:update
- **说明**: 更新装修模板基本信息（名称/备注/预览图）。

**请求参数 (DiyTemplateUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 装修模板编号 |
| name | String | 是 | @NotEmpty | 模板名称 |
| remark | String | 否 | - | 备注 |
| previewPicUrls | List\<String\> | 否 | - | 预览图列表 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验模板存在（不存在抛出 DIY_TEMPLATE_NOT_EXISTS）。
2. 校验模板名称唯一（排除自身 id）。
3. 按 id 更新模板记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_017_000 | 装修模板不存在 |
| 1_013_017_001 | 装修模板名称({})已经被使用 |

### 1.3 使用装修模板

- **路径**: PUT /promotion/diy-template/use
- **权限**: promotion:diy-template:use
- **说明**: 启用指定装修模板，全局只允许一个模板处于"使用中"状态。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修模板编号 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验模板存在（不存在抛出 DIY_TEMPLATE_NOT_EXISTS）。
2. 查询当前"使用中"（used = true）的模板；若就是目标模板则直接返回（状态未变化）。
3. 事务内将原使用中模板置为未使用（used = false，清空使用时间）。
4. 将目标模板置为已使用，并记录使用时间 usedTime 为当前时间。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_017_000 | 装修模板不存在 |

### 1.4 删除装修模板

- **路径**: DELETE /promotion/diy-template/delete
- **权限**: promotion:diy-template:delete
- **说明**: 删除装修模板，使用中的模板不允许删除。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修模板编号 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验模板存在（不存在抛出 DIY_TEMPLATE_NOT_EXISTS）。
2. 校验模板未处于使用中（used = true 时抛出 DIY_TEMPLATE_USED_CANNOT_DELETE）。
3. 按 id 删除模板记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_017_000 | 装修模板不存在 |
| 1_013_017_002 | 不能删除正在使用的装修模板 |

### 1.5 获得装修模板

- **路径**: GET /promotion/diy-template/get
- **权限**: promotion:diy-template:query
- **说明**: 按编号获得装修模板详情。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修模板编号 |

**响应**: CommonResult\<DiyTemplateRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 装修模板编号 |
| name | String | 模板名称 |
| remark | String | 备注 |
| previewPicUrls | List\<String\> | 预览图列表 |
| createTime | LocalDateTime | 创建时间 |
| used | Boolean | 是否使用中 |
| usedTime | LocalDateTime | 使用时间 |

### 1.6 获得装修模板分页

- **路径**: GET /promotion/diy-template/page
- **权限**: promotion:diy-template:query
- **说明**: 分页查询装修模板列表。

**请求参数 (DiyTemplatePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | - | 模板名称（模糊查询） |
| used | Boolean | 否 | - | 是否使用 |
| usedTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 使用时间区间 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<DiyTemplateRespVO\>\>，列表项字段同 1.5 的 DiyTemplateRespVO。

### 1.7 获得装修模板属性

- **路径**: GET /promotion/diy-template/get-property
- **权限**: promotion:diy-template:query
- **说明**: 获得模板详情及其属性 JSON 与模板下的全部装修页面，供装修编辑器加载。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修模板编号 |

**响应**: CommonResult\<DiyTemplatePropertyRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 装修模板编号 |
| name | String | 模板名称 |
| remark | String | 备注 |
| previewPicUrls | List\<String\> | 预览图列表 |
| property | String | 模板属性，JSON 格式 |
| pages | List\<DiyPagePropertyRespVO\> | 模板下的装修页面列表（字段同 2.7 的 DiyPagePropertyRespVO） |

**业务逻辑**:
1. 按编号查询模板。
2. 查询该模板下的全部装修页面（按 templateId 查询 DiyPage 列表）。
3. 组装为 DiyTemplatePropertyRespVO 返回（含模板属性 JSON 与页面列表）。

### 1.8 更新装修模板属性

- **路径**: PUT /promotion/diy-template/update-property
- **权限**: promotion:diy-template:update
- **说明**: 更新装修模板的属性 JSON（装修编辑器保存）。

**请求参数 (DiyTemplatePropertyUpdateRequestVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 装修模板编号 |
| property | String | 是 | @NotBlank | 模板属性，JSON 格式 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验模板存在（不存在抛出 DIY_TEMPLATE_NOT_EXISTS）。
2. 按 id 更新模板的 property 属性 JSON。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_017_000 | 装修模板不存在 |

## 2. 装修页面（DiyPageController）

### 2.1 创建装修页面

- **路径**: POST /promotion/diy-page/create
- **权限**: promotion:diy-page:create
- **说明**: 创建装修页面（可归属于某模板，也可为独立页面）。

**请求参数 (DiyPageCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| templateId | Long | 否 | - | 装修模板编号（为空表示独立页面） |
| name | String | 是 | @NotNull | 页面名称 |
| remark | String | 否 | - | 备注 |
| previewPicUrls | List\<String\> | 否 | - | 预览图列表 |

**响应**: CommonResult\<Long\>，返回新页面编号。

**业务逻辑**:
1. 校验名称唯一：仅对独立页面（templateId 为空）校验，在同属"无模板"的页面中名称不可重复，重复抛出 DIY_PAGE_NAME_USED；归属于模板的页面不校验名称唯一。
2. 转换为 DO 插入数据库，property 属性初始化为 "{}"。
3. 返回新页面编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_018_001 | 装修页面名称({})已经被使用 |

### 2.2 更新装修页面

- **路径**: PUT /promotion/diy-page/update
- **权限**: promotion:diy-page:update
- **说明**: 更新装修页面基本信息（名称/备注/预览图/所属模板）。

**请求参数 (DiyPageUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 装修页面编号 |
| templateId | Long | 否 | - | 装修模板编号（为空表示独立页面） |
| name | String | 是 | @NotNull | 页面名称 |
| remark | String | 否 | - | 备注 |
| previewPicUrls | List\<String\> | 否 | - | 预览图列表 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验页面存在（不存在抛出 DIY_PAGE_NOT_EXISTS）。
2. 校验名称唯一（仅独立页面参与校验，排除自身 id）。
3. 按 id 更新页面记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_018_000 | 装修页面不存在 |
| 1_013_018_001 | 装修页面名称({})已经被使用 |

### 2.3 删除装修页面

- **路径**: DELETE /promotion/diy-page/delete
- **权限**: promotion:diy-page:delete
- **说明**: 删除装修页面。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修页面编号 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验页面存在（不存在抛出 DIY_PAGE_NOT_EXISTS）。
2. 按 id 删除页面记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_018_000 | 装修页面不存在 |

### 2.4 获得装修页面

- **路径**: GET /promotion/diy-page/get
- **权限**: promotion:diy-page:query
- **说明**: 按编号获得装修页面详情。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修页面编号 |

**响应**: CommonResult\<DiyPageRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 装修页面编号 |
| templateId | Long | 装修模板编号（为空表示独立页面） |
| name | String | 页面名称 |
| remark | String | 备注 |
| previewPicUrls | List\<String\> | 预览图列表 |
| createTime | LocalDateTime | 创建时间 |

### 2.5 获得装修页面列表

- **路径**: GET /promotion/diy-page/list
- **权限**: promotion:diy-page:query
- **说明**: 按编号集合批量获得装修页面列表。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Collection\<Long\> | 是 | @RequestParam | 页面编号列表，逗号分隔，如 1024,2048 |

**响应**: CommonResult\<List\<DiyPageRespVO\>\>，列表项字段同 2.4 的 DiyPageRespVO。

**业务逻辑**:
1. ids 为空时直接返回空列表。
2. 否则按编号集合批量查询页面记录并返回。

### 2.6 获得装修页面分页

- **路径**: GET /promotion/diy-page/page
- **权限**: promotion:diy-page:query
- **说明**: 分页查询装修页面列表。

**请求参数 (DiyPagePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | - | 页面名称（模糊查询） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<DiyPageRespVO\>\>，列表项字段同 2.4 的 DiyPageRespVO。

### 2.7 获得装修页面属性

- **路径**: GET /promotion/diy-page/get-property
- **权限**: promotion:diy-page:query
- **说明**: 获得装修页面的属性 JSON，供装修编辑器加载。

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 装修页面编号 |

**响应**: CommonResult\<DiyPagePropertyRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 装修页面编号 |
| templateId | Long | 装修模板编号（为空表示独立页面） |
| name | String | 页面名称 |
| remark | String | 备注 |
| previewPicUrls | List\<String\> | 预览图列表 |
| property | String | 页面属性，JSON 格式 |

**业务逻辑**:
1. 按编号查询页面并转换为 DiyPagePropertyRespVO（含属性 JSON）。

### 2.8 更新装修页面属性

- **路径**: PUT /promotion/diy-page/update-property
- **权限**: promotion:diy-page:update
- **说明**: 更新装修页面的属性 JSON（装修编辑器保存）。

**请求参数 (DiyPagePropertyUpdateRequestVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 装修页面编号 |
| property | String | 是 | @NotBlank | 页面属性，JSON 格式 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验页面存在（不存在抛出 DIY_PAGE_NOT_EXISTS）。
2. 按 id 更新页面的 property 属性 JSON。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_018_000 | 装修页面不存在 |
