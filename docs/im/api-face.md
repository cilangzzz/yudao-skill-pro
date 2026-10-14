# 表情包接口 (ImFacePackController / ImFaceUserItemController / ImFacePackManagerController / ImFacePackItemManagerController / ImFaceUserItemManagerController)

> IM 表情包域：管理后台维护表情包与表情素材（manager 系列控制器），用户端拉取启用表情包、维护个人收藏表情（face 系列控制器），管理员可查看/删除任意用户的表情。

## 接口路径前缀

- `/im/face-pack`  (Controller: ImFacePackController) —— 用户端：启用表情包列表
- `/im/face-user-item`  (Controller: ImFaceUserItemController) —— 用户端：个人表情管理
- `/im/manager/face-pack`  (Controller: ImFacePackManagerController) —— 管理后台：表情包管理
- `/im/manager/face-pack-item`  (Controller: ImFacePackItemManagerController) —— 管理后台：表情包项（表情）管理
- `/im/manager/face-user-item`  (Controller: ImFaceUserItemManagerController) —— 管理后台：用户表情管理

---

## 1. 用户端 - 表情包列表

### 1.1 获得启用的表情包列表（含表情）

- **路径**: GET /im/face-pack/list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 拉取所有启用状态的表情包及其下启用表情，用于聊天面板表情选择器

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ImFacePackUserRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 表情包编号 |
| name | String | 表情包名称 |
| icon | String | 表情包图标 URL |
| items | List&lt;Item&gt; | 表情列表 |

Item 子结构（ImFacePackUserRespVO.Item）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 表情编号 |
| url | String | 表情图 URL |
| name | String | 表情名 |
| width | Integer | 渲染宽度（像素） |
| height | Integer | 渲染高度（像素） |

**业务逻辑**: 1. 查询所有启用（status = 0）的表情包，按 sort 排序；2. 查询这些包下所有启用的表情项，按 packId 分组；3. 组装 VO：pack 字段映射后逐包塞入 items 列表；4. 无启用表情包时直接返回空列表

---

## 2. 用户端 - 个人表情

### 2.1 获得我的个人表情列表

- **路径**: GET /im/face-user-item/list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 查询当前登录用户收藏的全部个人表情

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ImFaceUserItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| url | String | 表情图 URL |
| name | String | 表情名 |
| width | Integer | 渲染宽度（像素） |
| height | Integer | 渲染高度（像素） |

**业务逻辑**: 1. 以当前登录用户 userId 为条件查询其全部个人表情（selectListByUserId）；2. 转换为 ImFaceUserItemRespVO 返回

### 2.2 添加个人表情

- **路径**: POST /im/face-user-item/create
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 将一张表情图添加为当前用户的个人表情

**请求参数 (ImFaceUserItemSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| url | String | 是 | @NotBlank、@Size(max=512) | 表情图 URL |
| name | String | 否 | @Size(max=64) | 表情名 |
| width | Integer | 是 | @NotNull、@Min(1)、@Max(2048) | 渲染宽度（像素） |
| height | Integer | 是 | @NotNull、@Min(1)、@Max(2048) | 渲染高度（像素） |

**响应**: CommonResult&lt;Long&gt;（新个人表情编号）

**业务逻辑**: 1. 按当前登录用户 + URL 查重，已存在则报错（防止重复收藏）；2. 从配置 `yudao.im.face.user-item-max-count`（默认 200）读取个人表情数量上限，若已达上限则报错；3. 组装 DO（userId 取当前登录用户）入库，捕获唯一键冲突 DuplicateKeyException 转为「重复收藏」错误；4. 返回新表情编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_013 | 该表情已添加到个人表情 |
| 1_040_800_014 | 个人表情数量不能超过 {} 个 |

### 2.3 删除个人表情

- **路径**: DELETE /im/face-user-item/delete
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 删除当前用户的一条个人表情（仅能删除自己的）

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 个人表情编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. 校验表情记录存在，不存在报错；2. 校验归属：记录 userId 与当前登录用户不一致则报错（防止 A 用户传 B 用户的表情 id 删别人的）；3. 删除该记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_010 | 个人表情不存在 |
| 1_040_800_011 | 不能操作他人的表情 |

---

## 3. 管理后台 - 表情包管理

### 3.1 新增表情包

- **路径**: POST /im/manager/face-pack/create
- **权限**: im:manager:face-pack:create
- **说明**: 新增一个表情包

**请求参数 (ImFacePackSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 修改时必填 | - | 编号（新增不传） |
| name | String | 是 | @NotBlank、@Size(max=64) | 表情包名称 |
| icon | String | 否 | @Size(max=512) | 表情包图标 URL |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |

**响应**: CommonResult&lt;Long&gt;（新表情包编号）

**业务逻辑**: 1. 将 VO 转换为 DO 直接插入表情包表；2. 返回新记录编号

### 3.2 修改表情包

- **路径**: PUT /im/manager/face-pack/update
- **权限**: im:manager:face-pack:update
- **说明**: 修改已有表情包的基本信息 / 状态

**请求参数 (ImFacePackSaveReqVO)**: 同 3.1（id 为修改目标编号，必传）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. 校验表情包存在，不存在报错；2. VO 转 DO 后按 id 更新

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_000 | 表情包不存在 |

### 3.3 删除表情包

- **路径**: DELETE /im/manager/face-pack/delete
- **权限**: im:manager:face-pack:delete
- **说明**: 删除单个表情包（包下还有表情时拒绝）

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 表情包编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. 校验表情包存在，不存在报错；2. 校验表情包下表情数量为 0，否则报错（防止误删表情包导致历史 face 消息无法回查归属）；3. 删除该表情包

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_000 | 表情包不存在 |
| 1_040_800_001 | 表情包下还有表情，无法删除 |

### 3.4 批量删除表情包

- **路径**: DELETE /im/manager/face-pack/delete-list
- **权限**: im:manager:face-pack:delete
- **说明**: 批量删除表情包，任一包下有表情则整批拒绝

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @Size(max=100)（批量删除最多 100 条） | 表情包编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. ids 为空集合直接返回；2. 统计这些包下表情总数，大于 0 则整批拒绝删除（避免「只删一半」的中间态）；3. 批量删除

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_001 | 表情包下还有表情，无法删除 |

### 3.5 获得表情包分页

- **路径**: GET /im/manager/face-pack/page
- **权限**: im:manager:face-pack:query
- **说明**: 分页查询表情包列表

**请求参数 (ImFacePackPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数 |
| name | String | 否 | - | 表情包名称，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ImFacePackRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 表情包名称 |
| icon | String | 表情包图标 URL |
| sort | Integer | 排序 |
| status | Integer | 状态（0 启用 / 1 禁用） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 name 模糊、status、createTime 区间条件分页查询表情包列表

### 3.6 获得表情包详情

- **路径**: GET /im/manager/face-pack/get
- **权限**: im:manager:face-pack:query
- **说明**: 按编号查询单个表情包详情

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 表情包编号 |

**响应**: CommonResult&lt;ImFacePackRespVO&gt;（字段同 3.5 响应表）

**业务逻辑**: 1. 按编号查询表情包记录；2. 转换为 ImFacePackRespVO 返回

---

## 4. 管理后台 - 表情包项（表情）管理

### 4.1 新增表情

- **路径**: POST /im/manager/face-pack-item/create
- **权限**: im:manager:face-pack-item:create
- **说明**: 向指定表情包内新增一个表情

**请求参数 (ImFacePackItemSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 修改时必填 | - | 编号（新增不传） |
| packId | Long | 是 | @NotNull | 所属表情包编号 |
| url | String | 是 | @NotBlank、@Size(max=512) | 表情图 URL |
| name | String | 否 | @Size(max=64) | 表情名 |
| width | Integer | 是 | @NotNull、@Min(1)、@Max(2048) | 渲染宽度（像素） |
| height | Integer | 是 | @NotNull、@Min(1)、@Max(2048) | 渲染高度（像素） |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |

**响应**: CommonResult&lt;Long&gt;（新表情编号）

**业务逻辑**: 1. 校验所属表情包存在，不存在报错；2. VO 转 DO 入库；3. 返回新表情编号

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_000 | 表情包不存在 |

### 4.2 修改表情

- **路径**: PUT /im/manager/face-pack-item/update
- **权限**: im:manager:face-pack-item:update
- **说明**: 修改已有表情的内容 / 归属包 / 状态

**请求参数 (ImFacePackItemSaveReqVO)**: 同 4.1（id 为修改目标编号，必传）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. 校验表情存在，不存在报错；2. 校验所属表情包存在，不存在报错；3. VO 转 DO 后按 id 更新

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_000 | 表情包不存在 |
| 1_040_800_002 | 表情不存在 |

### 4.3 删除表情

- **路径**: DELETE /im/manager/face-pack-item/delete
- **权限**: im:manager:face-pack-item:delete
- **说明**: 删除单个表情

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 表情编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. 校验表情存在，不存在报错；2. 删除该记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_002 | 表情不存在 |

### 4.4 批量删除表情

- **路径**: DELETE /im/manager/face-pack-item/delete-list
- **权限**: im:manager:face-pack-item:delete
- **说明**: 批量删除表情

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @Size(max=100)（批量删除最多 100 条） | 表情编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. ids 为空集合直接返回；2. 批量删除（未做逐条存在性校验）

### 4.5 获得表情分页

- **路径**: GET /im/manager/face-pack-item/page
- **权限**: im:manager:face-pack-item:query
- **说明**: 分页查询表情项列表

**请求参数 (ImFacePackItemPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数 |
| packId | Long | 否 | - | 所属表情包编号 |
| name | String | 否 | - | 表情名，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |

**响应**: CommonResult&lt;PageResult&lt;ImFacePackItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| packId | Long | 所属表情包编号 |
| url | String | 表情图 URL |
| name | String | 表情名 |
| width | Integer | 渲染宽度（像素） |
| height | Integer | 渲染高度（像素） |
| sort | Integer | 排序 |
| status | Integer | 状态（0 启用 / 1 禁用） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 packId、name 模糊、status 条件分页查询表情项列表

### 4.6 获得表情详情

- **路径**: GET /im/manager/face-pack-item/get
- **权限**: im:manager:face-pack-item:query
- **说明**: 按编号查询单个表情详情

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 表情编号 |

**响应**: CommonResult&lt;ImFacePackItemRespVO&gt;（字段同 4.5 响应表）

**业务逻辑**: 1. 按编号查询表情记录；2. 转换为 ImFacePackItemRespVO 返回

---

## 5. 管理后台 - 用户表情管理

### 5.1 获得用户表情分页

- **路径**: GET /im/manager/face-user-item/page
- **权限**: im:manager:face-user-item:query
- **说明**: 分页查询全部用户上传的个人表情，并回填用户昵称

**请求参数 (ImFaceUserItemManagerPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数 |
| userId | Long | 否 | - | 所属用户编号 |
| name | String | 否 | - | 表情名，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 添加时间区间 |

**响应**: CommonResult&lt;PageResult&lt;ImFaceUserItemManagerRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| userId | Long | 所属用户编号 |
| userNickname | String | 所属用户昵称 |
| url | String | 表情图 URL |
| name | String | 表情名 |
| width | Integer | 渲染宽度（像素） |
| height | Integer | 渲染高度（像素） |
| createTime | LocalDateTime | 添加时间 |

**业务逻辑**: 1. 按 userId、name 模糊、createTime 区间条件分页查询用户表情列表；2. 收集结果中的 userId 集合，通过 AdminUserApi 批量查询 system 用户；3. 逐条组装 VO 并回填 userNickname 昵称（用户不存在时留空），返回分页结果

### 5.2 删除用户表情

- **路径**: DELETE /im/manager/face-user-item/delete
- **权限**: im:manager:face-user-item:delete
- **说明**: 管理员删除任意用户的一条个人表情（无归属限制）

**请求参数**: 查询参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 用户表情编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 1. 校验表情记录存在，不存在报错；2. 删除该记录

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_800_010 | 个人表情不存在 |
