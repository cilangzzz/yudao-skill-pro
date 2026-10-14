# 会员标签接口 (MemberTagController)

> 会员标签的管理接口，提供标签的创建、修改、删除、查询能力；标签用于对会员用户进行分类打标，删除标签前会校验标签下是否存在用户。

## 接口路径前缀

/member/tag  (Controller: MemberTagController)

## 1. 会员标签管理

### 1.1 创建会员标签

- **路径**: POST /member/tag/create
- **权限**: member:tag:create
- **说明**: 创建一个新的会员标签，要求标签名称唯一

**请求参数 (MemberTagCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 标签名称（继承自 MemberTagBaseVO） |

**响应**: CommonResult&lt;Long&gt;，data 为新创建的标签编号

**业务逻辑**:
1. 校验标签名称唯一：按名称查询已有标签，若已存在则抛出 TAG_NAME_EXISTS（名称为空时跳过校验，实际由 VO 的 @NotNull 保证非空）
2. 将 MemberTagCreateReqVO 转换为 MemberTagDO
3. 插入数据库
4. 返回新标签的编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_006_001 | 用户标签已经存在 |

### 1.2 更新会员标签

- **路径**: PUT /member/tag/update
- **权限**: member:tag:update
- **说明**: 更新指定会员标签的信息

**请求参数 (MemberTagUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 标签编号 |
| name | String | 是 | @NotNull | 标签名称（继承自 MemberTagBaseVO） |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true

**业务逻辑**:
1. 校验标签存在，不存在则抛出 TAG_NOT_EXISTS
2. 校验标签名称唯一：按名称查询已有标签，若重名且不属于当前 id，则抛出 TAG_NAME_EXISTS
3. 将 MemberTagUpdateReqVO 转换为 MemberTagDO，按 id 更新

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_006_000 | 用户标签不存在 |
| 1_004_006_001 | 用户标签已经存在 |

### 1.3 删除会员标签

- **路径**: DELETE /member/tag/delete
- **权限**: member:tag:delete
- **说明**: 删除指定会员标签，标签下存在用户时禁止删除

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 标签编号（@RequestParam） |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true

**业务逻辑**:
1. 校验标签存在，不存在则抛出 TAG_NOT_EXISTS
2. 校验标签下是否有用户：调用 MemberUserService.getUserCountByTagId 统计，若用户数大于 0 则抛出 TAG_HAS_USER
3. 按 id 删除标签

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_006_000 | 用户标签不存在 |
| 1_004_006_002 | 用户标签下存在用户，无法删除 |

### 1.4 获得会员标签

- **路径**: GET /member/tag/get
- **权限**: member:tag:query
- **说明**: 根据编号获得单个会员标签详情

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 标签编号（@RequestParam） |

**响应**: CommonResult&lt;MemberTagRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 标签编号 |
| name | String | 标签名称（继承自 MemberTagBaseVO） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 MemberTagDO
2. 通过 MemberTagConvert 转换为 MemberTagRespVO 返回

### 1.5 获取会员标签精简信息列表

- **路径**: GET /member/tag/list-all-simple
- **权限**: 已认证（无 @PreAuthorize 注解，登录即可访问）
- **说明**: 获取会员标签精简信息列表，主要用于前端下拉选项（接口描述称只包含开启状态的标签，实际实现返回全部标签）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MemberTagRespVO&gt;&gt;，字段同 1.4 的 MemberTagRespVO

**业务逻辑**:
1. 查询全部标签列表（memberTagMapper.selectList()）
2. 通过 MemberTagConvert 转换为 MemberTagRespVO 列表返回

### 1.6 获得会员标签列表

- **路径**: GET /member/tag/list
- **权限**: member:tag:query
- **说明**: 根据编号列表批量获得会员标签

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Collection&lt;Long&gt; | 是 | - | 标签编号列表，逗号分隔，如 1024,2048（@RequestParam） |

**响应**: CommonResult&lt;List&lt;MemberTagRespVO&gt;&gt;，字段同 1.4 的 MemberTagRespVO

**业务逻辑**:
1. ids 为空时直接返回空列表
2. 按 ids 批量查询标签（memberTagMapper.selectByIds）
3. 通过 MemberTagConvert 转换为 MemberTagRespVO 列表返回

### 1.7 获得会员标签分页

- **路径**: GET /member/tag/page
- **权限**: member:tag:query
- **说明**: 分页查询会员标签列表

**请求参数 (MemberTagPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 标签名称（模糊查询条件） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |
| pageNo | Integer | 是 | @NotNull @Min(1) | 页码，从 1 开始（继承自 PageParam） |
| pageSize | Integer | 是 | @NotNull @Min(1) @Max(200) | 每页条数，最大 200，-1 表示不分页（继承自 PageParam） |

**响应**: CommonResult&lt;PageResult&lt;MemberTagRespVO&gt;&gt;，list 元素字段同 1.4 的 MemberTagRespVO

**业务逻辑**:
1. 按分页条件（标签名称、创建时间范围）执行分页查询（memberTagMapper.selectPage）
2. 通过 MemberTagConvert 转换为 MemberTagRespVO 分页结果返回

## 域错误码汇总

会员标签域使用错误码前缀 1_004_006_XXX（ErrorCodeConstants 中「用户标签」段）：

| 错误码 | 说明 |
|-------|------|
| 1_004_006_000 | 用户标签不存在 |
| 1_004_006_001 | 用户标签已经存在 |
| 1_004_006_002 | 用户标签下存在用户，无法删除 |
