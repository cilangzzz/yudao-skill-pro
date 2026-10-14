# GoView 项目管理接口 (GoViewProjectController)

> 提供 GoView 大屏项目的增删改查管理，每个大屏图表对应一个项目；项目创建后初始为「未发布」，通过更新接口保存报表内容（JSON）并发布。

## 接口路径前缀

/report/go-view/project  (Controller: GoViewProjectController)

> 注意：GoView 数据查询相关接口由 GoViewDataController 提供（前缀 /report/go-view/data），不属于本文档范围。

## 1. 项目管理

### 1.1 创建项目

- **路径**: POST /report/go-view/project/create
- **权限**: report:go-view-project:create
- **说明**: 创建一个新的 GoView 大屏项目，返回项目编号

**请求参数 (GoViewProjectCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotEmpty | 项目名称 |

**响应**: CommonResult&lt;Long&gt;（新创建项目的编号 id）

**业务逻辑**:
1. 通过 GoViewProjectConvert 将请求 VO 转换为 GoViewProjectDO
2. 强制设置项目状态为「未发布」（CommonStatusEnum.DISABLE），忽略请求中的其他状态
3. 插入数据表 report_go_view_project
4. 返回数据库自增生成的项目编号 id

### 1.2 更新项目

- **路径**: PUT /report/go-view/project/update
- **权限**: report:go-view-project:update
- **说明**: 更新项目信息，可修改名称、发布状态、报表内容、预览图片与备注（GoView 编辑器保存大屏即调用此接口）

**请求参数 (GoViewProjectUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 项目编号 |
| name | String | 否 | 无 | 项目名称 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 发布状态（0-开启/1-禁用，映射发布与未发布） |
| content | String | 否 | 无 | 报表内容（JSON 格式配置字符串） |
| picUrl | String | 否 | 无 | 预览图片 URL |
| remark | String | 否 | 无 | 项目备注 |

**响应**: CommonResult&lt;Boolean&gt;（更新成功返回 true）

**业务逻辑**:
1. 校验编号对应的项目是否存在，不存在则抛出错误码 GO_VIEW_PROJECT_NOT_EXISTS（1_003_000_000）
2. 通过 GoViewProjectConvert 将请求 VO 转换为 GoViewProjectDO
3. 调用 updateById 按编号更新项目记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_003_000_000 | GoView 项目不存在 |

### 1.3 删除项目

- **路径**: DELETE /report/go-view/project/delete
- **权限**: report:go-view-project:delete
- **说明**: 按编号删除指定的大屏项目

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 项目编号 |

**响应**: CommonResult&lt;Boolean&gt;（删除成功返回 true）

**业务逻辑**:
1. 校验编号对应的项目是否存在，不存在则抛出错误码 GO_VIEW_PROJECT_NOT_EXISTS（1_003_000_000）
2. 调用 deleteById 按编号删除项目（BaseDO 逻辑删除）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_003_000_000 | GoView 项目不存在 |

### 1.4 获得项目

- **路径**: GET /report/go-view/project/get
- **权限**: report:go-view-project:query
- **说明**: 按编号获取大屏项目详情（含报表内容 JSON）

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 项目编号 |

**响应**: CommonResult&lt;GoViewProjectRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 项目编号 |
| name | String | 项目名称 |
| status | Integer | 发布状态 |
| content | String | 报表内容（JSON 格式） |
| picUrl | String | 预览图片 URL |
| remark | String | 项目备注 |
| creator | String | 创建人编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 selectById 按编号查询 GoViewProjectDO
2. 通过 GoViewProjectConvert 将 DO 转换为 GoViewProjectRespVO 返回

### 1.5 获得我的项目分页

- **路径**: GET /report/go-view/project/my-page
- **权限**: report:go-view-project:query
- **说明**: 分页查询当前登录用户自己创建的大屏项目列表（GoView「我的项目」列表页）

**请求参数 (PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10；传 -1 时不分页（PAGE_SIZE_NONE） |

**响应**: CommonResult&lt;PageResult&lt;GoViewProjectRespVO&gt;&gt;，其中 GoViewProjectRespVO 字段见 1.4

**业务逻辑**:
1. 通过 SecurityFrameworkUtils.getLoginUserId() 获取当前登录用户编号
2. 调用 Mapper 分页查询，按 creator = 当前登录用户 过滤
3. 结果按编号 id 倒序排列（最新创建的项目在前）
4. 通过 GoViewProjectConvert.convertPage 将分页 DO 转换为分页 RespVO 返回
