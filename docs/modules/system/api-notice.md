# 通知公告接口 (NoticeController)

> 管理后台的通知公告（系统公告）维护，支持公告的创建、修改、删除、批量删除、分页查询、详情查询，以及通过 WebSocket 在线推送公告。

## 接口路径前缀

/system/notice  (Controller: NoticeController)

---

## 1. 通知公告管理

### 1.1 创建通知公告

- **路径**: POST /system/notice/create
- **权限**: system:notice:create
- **说明**: 新增一条通知公告，返回公告编号。

**请求参数 (NoticeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | | 岗位公告编号（创建时无需传入） |
| title | String | 是 | @NotBlank、@Size(max=50) | 公告标题，不能超过 50 个字符 |
| type | Integer | 是 | @NotNull | 公告类型 |
| content | String | 否 | | 公告内容 |
| status | Integer | 否 | | 状态，参见 CommonStatusEnum 枚举类 |

**响应**: `CommonResult<Long>` — 通知公告编号

**业务逻辑**: 1. 将 NoticeSaveReqVO 转换为 NoticeDO 实体。2. 调用 Mapper 插入数据库。3. 返回新记录的主键 id。

### 1.2 修改通知公告

- **路径**: PUT /system/notice/update
- **权限**: system:notice:update
- **说明**: 根据编号修改一条已有的通知公告。

**请求参数 (NoticeSaveReqVO)**: 与创建接口相同（见 1.1），其中 id 为更新必传的公告编号。

**响应**: `CommonResult<Boolean>` — 是否成功（true）

**业务逻辑**: 1. 校验 id 对应的通知公告是否存在，不存在则抛出 NOTICE_NOT_FOUND 错误。2. 将 NoticeSaveReqVO 转换为 NoticeDO 更新对象。3. 按 id 执行更新（updateById）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_008_001 | 当前通知公告不存在 |

### 1.3 删除通知公告

- **路径**: DELETE /system/notice/delete
- **权限**: system:notice:delete
- **说明**: 根据编号删除单条通知公告。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 公告编号 |

**响应**: `CommonResult<Boolean>` — 是否成功（true）

**业务逻辑**: 1. 校验 id 对应的通知公告是否存在，不存在则抛出 NOTICE_NOT_FOUND 错误。2. 按 id 删除该条公告记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_008_001 | 当前通知公告不存在 |

### 1.4 批量删除通知公告

- **路径**: DELETE /system/notice/delete-list
- **权限**: system:notice:delete
- **说明**: 根据编号列表批量删除通知公告。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | | 公告编号列表 |

**响应**: `CommonResult<Boolean>` — 是否成功（true）

**业务逻辑**: 1. 按编号列表批量删除公告记录（deleteByIds），不逐一校验存在性。

### 1.5 获取通知公告分页列表

- **路径**: GET /system/notice/page
- **权限**: system:notice:query
- **说明**: 分页查询通知公告列表，支持按标题模糊匹配与状态过滤。

**请求参数 (NoticePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，最大值 200，默认 10 |
| title | String | 否 | | 通知公告名称，模糊匹配 |
| status | Integer | 否 | | 展示状态，参见 CommonStatusEnum 枚举类 |

**响应**: `CommonResult<PageResult<NoticeRespVO>>`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 通知公告序号 |
| title | String | 公告标题 |
| type | Integer | 公告类型 |
| content | String | 公告内容 |
| status | Integer | 状态，参见 CommonStatusEnum 枚举类 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 根据分页与筛选条件调用 Mapper 执行分页查询（selectPage）。2. 将分页结果 NoticeDO 列表转换为 NoticeRespVO 返回。

### 1.6 获得通知公告详情

- **路径**: GET /system/notice/get
- **权限**: system:notice:query
- **说明**: 根据编号查询单条通知公告详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 公告编号 |

**响应**: `CommonResult<NoticeRespVO>`，字段同 1.5 响应表。

**业务逻辑**: 1. 按编号查询公告记录（selectById）。2. 将 NoticeDO 转换为 NoticeRespVO 返回。

### 1.7 推送通知公告

- **路径**: POST /system/notice/push
- **权限**: system:notice:update
- **说明**: 将指定公告推送给当前 WebSocket 在线的管理端用户（不保证离线用户收到）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | | 公告编号 |

**响应**: `CommonResult<Boolean>` — 是否成功（true）

**业务逻辑**: 1. 按编号查询公告，查询不到则通过 Assert 抛出「公告不能为空」异常。2. 通过 WebSocketSenderApi 以消息类型 `notice-push` 推送公告内容给在线的 ADMIN 类型用户。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_008_001 | 当前通知公告不存在（Service 层校验使用；push 端点运行时以 Assert.notEmpty 提示「公告不能为空」） |
