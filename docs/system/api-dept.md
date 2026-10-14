# 部门与岗位接口 (DeptController / PostController)

> 提供管理后台部门（树形组织架构）与岗位的维护能力：增删改查、精简下拉列表、岗位分页与 Excel 导出，供用户管理、数据权限等模块复用部门/岗位校验逻辑。

## 接口路径前缀

- `/system/dept` (Controller: DeptController)
- `/system/post` (Controller: PostController)

---

## 1. 部门管理（DeptController）

### 1.1 创建部门

- **路径**: POST /system/dept/create
- **权限**: system:dept:create
- **说明**: 创建一个部门，支持指定父部门形成树形结构

**请求参数 (DeptSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 部门编号（创建时忽略） |
| name | String | 是 | @NotBlank、@Size(max = 30) | 部门名称 |
| parentId | Long | 否 | - | 父部门 ID，为空时自动设为根部门 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| leaderUserId | Long | 否 | - | 负责人的用户编号 |
| phone | String | 否 | @Size(max = 11) | 联系电话 |
| email | String | 否 | @Email、@Size(max = 50) | 邮箱 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum.class) | 状态（0 开启 / 1 禁用） |

**响应**: CommonResult&lt;Long&gt;，data 为新部门编号

**业务逻辑**:
1. parentId 为空时自动设置为根部门 ID（DeptDO.PARENT_ID_ROOT）
2. 校验父部门的有效性（父部门不存在时报错）
3. 校验同一父部门下部门名称的唯一性
4. VO 转 DeptDO 后插入，返回新部门编号
5. 清空部门子列表 Redis 缓存（DEPT_CHILDREN_ID_LIST，allEntries 全清）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_004_000 | 已经存在该名字的部门 |
| 1_002_004_001 | 父级部门不存在 |
| 1_002_004_004 | 不能设置自己为父部门 |

### 1.2 更新部门

- **路径**: PUT /system/dept/update
- **权限**: system:dept:update
- **说明**: 修改部门信息，含父部门调整（防环路校验）

**请求参数 (DeptSaveReqVO)**: 同 1.1（id 必传用于定位记录）

**响应**: CommonResult&lt;Boolean&gt;，data 恒为 true

**业务逻辑**:
1. parentId 为空时自动设置为根部门 ID
2. 校验当前部门存在
3. 校验父部门有效性：不能设置自己为父部门、父部门必须存在、父部门不能是自己的子孙部门（沿父链递归校验，避免形成环路）
4. 校验同一父部门下部门名称的唯一性（排除自身）
5. 更新部门记录
6. 清空部门子列表 Redis 缓存（DEPT_CHILDREN_ID_LIST）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_004_000 | 已经存在该名字的部门 |
| 1_002_004_001 | 父级部门不存在 |
| 1_002_004_002 | 当前部门不存在 |
| 1_002_004_004 | 不能设置自己为父部门 |
| 1_002_004_007 | 不能设置自己的子部门为父部门 |

### 1.3 删除部门

- **路径**: DELETE /system/dept/delete
- **权限**: system:dept:delete
- **说明**: 删除单个部门，存在子部门时禁止删除

**请求参数**: 无（Query 参数 `id`：部门编号，必填）

**响应**: CommonResult&lt;Boolean&gt;，data 恒为 true

**业务逻辑**:
1. 校验部门存在
2. 校验该部门下不存在子部门（selectCountByParentId > 0 时报错）
3. 删除部门记录
4. 清空部门子列表 Redis 缓存（DEPT_CHILDREN_ID_LIST）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_004_002 | 当前部门不存在 |
| 1_002_004_003 | 存在子部门，无法删除 |

### 1.4 批量删除部门

- **路径**: DELETE /system/dept/delete-list
- **权限**: system:dept:delete
- **说明**: 按 ID 集合批量删除部门

**请求参数**: 无（Query 参数 `ids`：部门编号列表，必填）

**响应**: CommonResult&lt;Boolean&gt;，data 恒为 true

**业务逻辑**:
1. 逐个校验每个待删部门下不存在子部门（任一存在子部门即整体报错）
2. 按 ID 集合批量删除部门
3. 清空部门子列表 Redis 缓存（DEPT_CHILDREN_ID_LIST）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_004_003 | 存在子部门，无法删除 |

### 1.5 获取部门列表

- **路径**: GET /system/dept/list
- **权限**: system:dept:query
- **说明**: 按名称/状态条件查询部门全列表（非分页）

**请求参数 (DeptListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | - | 部门名称，模糊匹配 |
| status | Integer | 否 | - | 展示状态，参见 CommonStatusEnum 枚举 |

**响应**: CommonResult&lt;List&lt;DeptRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 部门编号 |
| name | String | 部门名称 |
| parentId | Long | 父部门 ID |
| sort | Integer | 显示顺序 |
| leaderUserId | Long | 负责人的用户编号 |
| phone | String | 联系电话 |
| email | String | 邮箱 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 name（模糊匹配）与 status 条件查询部门列表
2. 按 sort 字段升序排序后返回

### 1.6 获取部门精简信息列表

- **路径**: GET /system/dept/list-all-simple（别名 GET /system/dept/simple-list）
- **权限**: 已认证（未加 @PreAuthorize）
- **说明**: 只包含开启状态的部门，主要用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DeptSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 部门编号 |
| name | String | 部门名称 |
| parentId | Long | 父部门 ID |

**业务逻辑**:
1. 服务端固定构造 status = 开启（CommonStatusEnum.ENABLE）的查询条件
2. 查询部门列表并按 sort 升序排序
3. 转换为 DeptSimpleRespVO（仅含 id/name/parentId）返回

### 1.7 获得部门信息

- **路径**: GET /system/dept/get
- **权限**: system:dept:query
- **说明**: 按编号查询单个部门详情

**请求参数**: 无（Query 参数 `id`：部门编号，必填）

**响应**: CommonResult&lt;DeptRespVO&gt;，字段同 1.5

**业务逻辑**:
1. 按 ID 查询部门记录（不存在时 data 为空）
2. 转换为 DeptRespVO 返回

> 域内另有 `validateDeptList(ids)` 校验方法（错误码 1_002_004_002 当前部门不存在、1_002_004_006 部门({})不处于开启状态，不允许选择），供用户管理等其他模块校验部门有效性时调用，不在本控制器暴露端点。

---

## 2. 岗位管理（PostController）

### 2.1 创建岗位

- **路径**: POST /system/post/create
- **权限**: system:post:create
- **说明**: 创建一个岗位

**请求参数 (PostSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 岗位编号（创建时忽略） |
| name | String | 是 | @NotBlank、@Size(max = 50) | 岗位名称 |
| code | String | 是 | @NotBlank、@Size(max = 64) | 岗位编码 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| status | Integer | 否 | @InEnum(CommonStatusEnum.class) | 状态（0 开启 / 1 禁用） |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;，data 为新岗位编号

**业务逻辑**:
1. 校验岗位名称的唯一性（同名校验）
2. 校验岗位编码的唯一性
3. VO 转 PostDO 后插入，返回新岗位编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_005_002 | 已经存在该名字的岗位 |
| 1_002_005_003 | 已经存在该标识的岗位 |

### 2.2 修改岗位

- **路径**: PUT /system/post/update
- **权限**: system:post:update
- **说明**: 修改岗位信息

**请求参数 (PostSaveReqVO)**: 同 2.1（id 必传用于定位记录）

**响应**: CommonResult&lt;Boolean&gt;，data 恒为 true

**业务逻辑**:
1. 校验当前岗位存在
2. 校验岗位名称的唯一性（排除自身）
3. 校验岗位编码的唯一性（排除自身）
4. 更新岗位记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_005_000 | 当前岗位不存在 |
| 1_002_005_002 | 已经存在该名字的岗位 |
| 1_002_005_003 | 已经存在该标识的岗位 |

### 2.3 删除岗位

- **路径**: DELETE /system/post/delete
- **权限**: system:post:delete
- **说明**: 删除单个岗位

**请求参数**: 无（Query 参数 `id`：岗位编号，必填）

**响应**: CommonResult&lt;Boolean&gt;，data 恒为 true

**业务逻辑**:
1. 校验岗位存在
2. 删除岗位记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_005_000 | 当前岗位不存在 |

### 2.4 批量删除岗位

- **路径**: DELETE /system/post/delete-list
- **权限**: system:post:delete
- **说明**: 按 ID 集合批量删除岗位

**请求参数**: 无（Query 参数 `ids`：岗位编号列表，必填）

**响应**: CommonResult&lt;Boolean&gt;，data 恒为 true

**业务逻辑**:
1. 按 ID 集合直接批量删除岗位（未做存在性校验）

### 2.5 获得岗位信息

- **路径**: GET /system/post/get
- **权限**: system:post:query
- **说明**: 按编号查询单个岗位详情

**请求参数**: 无（Query 参数 `id`：岗位编号，必填）

**响应**: CommonResult&lt;PostRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 岗位序号 |
| name | String | 岗位名称 |
| code | String | 岗位编码 |
| sort | Integer | 显示顺序 |
| status | Integer | 状态（CommonStatusEnum） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 ID 查询岗位记录（不存在时 data 为空）
2. 转换为 PostRespVO 返回

### 2.6 获取岗位全列表

- **路径**: GET /system/post/list-all-simple（别名 GET /system/post/simple-list）
- **权限**: 已认证（未加 @PreAuthorize）
- **说明**: 只包含开启状态的岗位，主要用于前端下拉选项

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;PostSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 岗位序号 |
| name | String | 岗位名称 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）的全部岗位（不限制 ID 集合）
2. 按 sort 字段升序排序
3. 转换为 PostSimpleRespVO（仅含 id/name）返回

### 2.7 获得岗位分页列表

- **路径**: GET /system/post/page
- **权限**: system:post:query
- **说明**: 按编码/名称/状态条件分页查询岗位

**请求参数 (PostPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，最大 200 |
| code | String | 否 | - | 岗位编码，模糊匹配 |
| name | String | 否 | - | 岗位名称，模糊匹配 |
| status | Integer | 否 | - | 展示状态，参见 CommonStatusEnum 枚举 |

**响应**: CommonResult&lt;PageResult&lt;PostRespVO&gt;&gt;，list 内字段同 2.5

**业务逻辑**:
1. 按 code/name（模糊匹配）与 status 条件分页查询岗位列表

### 2.8 岗位数据导出

- **路径**: GET /system/post/export-excel
- **权限**: system:post:export（操作日志类型为 EXPORT）
- **说明**: 按查询条件导出岗位 Excel 文件

**请求参数 (PostPageReqVO)**: 同 2.7（导出时服务端强制不分页查全量）

**响应**: 无 CommonResult 包装，直接输出 Excel 文件流（文件名「岗位数据.xls」，列定义见 PostRespVO 上的 @ExcelProperty 注解，状态列经 DictConvert 字典转换）

**业务逻辑**:
1. 将分页参数 pageSize 置为 -1（PageParam.PAGE_SIZE_NONE，不分页）
2. 按 PostPageReqVO 条件查询全量岗位列表
3. 转换为 PostRespVO 列表后通过 ExcelUtils 写出到响应流

> 域内另有 `validatePostList(ids)` 校验方法（错误码 1_002_005_000 当前岗位不存在、1_002_005_001 岗位({})不处于开启状态，不允许选择），供用户管理等其他模块校验岗位有效性时调用，不在本控制器暴露端点。
