# 公众号标签接口 (MpTagController)

> 管理微信公众号的用户标签，支持标签的创建、修改、删除、查询，以及从微信平台同步标签到本地数据库。

## 接口路径前缀

/mp/tag  (Controller: MpTagController)

## 1. 标签基础管理

### 1.1 创建公众号标签

- **路径**: POST /mp/tag/create
- **权限**: mp:tag:create
- **说明**: 在指定公众号账号下创建用户标签，先调用微信平台接口创建，再落库保存。

**请求参数 (MpTagCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| name | String | 是 | @NotEmpty | 标签名（继承自 MpTagBaseVO） |

**响应**: CommonResult&lt;Long&gt;，返回新建标签的数据库编号（id）。

**业务逻辑**:
1. 调用 MpAccountService#getRequiredAccount 校验公众号账号存在，不存在则抛出账号不存在异常。
2. 通过 MpServiceFactory 获取该账号对应的 WxMpService，调用微信平台 tagCreate 接口创建标签；标签名的唯一性交给公众号平台保证。
3. 微信接口调用失败（WxErrorException）时，抛出「创建标签失败」异常，并携带微信返回的错误信息。
4. 将微信返回的 WxUserTag 与账号信息转换为 MpTagDO，插入本地数据库，返回数据库主键 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_002_001 | 创建标签失败，原因：{} |

### 1.2 更新公众号标签

- **路径**: PUT /mp/tag/update
- **权限**: mp:tag:update
- **说明**: 修改标签名称，先调用微信平台接口更新，再更新本地数据库记录。

**请求参数 (MpTagUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 标签编号 |
| name | String | 是 | @NotEmpty | 标签名（继承自 MpTagBaseVO） |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验标签在本地数据库中存在，不存在则抛出「标签不存在」异常。
2. 根据标签关联的 accountId 获取 WxMpService，调用微信平台 tagUpdate 接口，按微信侧 tagId 更新标签名；标签名的唯一性交给公众号平台保证。
3. 微信接口调用失败时，抛出「更新标签失败」异常，并携带微信返回的错误信息。
4. 按本地记录 id 更新数据库中的标签名。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_002_000 | 标签不存在 |
| 1_006_002_002 | 更新标签失败，原因：{} |

### 1.3 删除公众号标签

- **路径**: DELETE /mp/tag/delete
- **权限**: mp:tag:delete
- **说明**: 删除指定标签，先调用微信平台接口删除，再删除本地数据库记录。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 标签编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验标签在本地数据库中存在，不存在则抛出「标签不存在」异常。
2. 根据标签关联的 accountId 获取 WxMpService，调用微信平台 tagDelete 接口，按微信侧 tagId 删除标签。
3. 微信接口调用失败时，抛出「删除标签失败」异常，并携带微信返回的错误信息。
4. 删除本地数据库中的标签记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_002_000 | 标签不存在 |
| 1_006_002_003 | 删除标签失败，原因：{} |

### 1.4 获取公众号标签详情

- **路径**: GET /mp/tag/get
- **权限**: mp:tag:query
- **说明**: 按编号查询单个标签的详细信息。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必传 | 标签编号 |

**响应**: CommonResult&lt;MpTagRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 标签名 |
| count | Integer | 此标签下粉丝数量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按主键 id 从数据库查询 MpTagDO。
2. 通过 MpTagConvert 转换为 MpTagRespVO 返回；记录不存在时返回 null 数据。

### 1.5 获取公众号标签分页

- **路径**: GET /mp/tag/page
- **权限**: mp:tag:query
- **说明**: 分页查询标签列表，支持按公众号账号与标签名过滤。

**请求参数 (MpTagPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | PageParam 默认值 1 | 页码 |
| pageSize | Integer | 是 | PageParam 默认值 10 | 每页条数 |
| accountId | Long | 是 | @NotEmpty | 公众号账号的编号 |
| name | String | 否 | - | 标签名，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;MpTagRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 标签名 |
| count | Integer | 此标签下粉丝数量 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按分页参数（accountId、name 模糊匹配）查询数据库，返回分页结果。
2. 通过 MpTagConvert 将 MpTagDO 分页结果转换为 MpTagRespVO 分页结果。

## 2. 精简列表与同步

### 2.1 获取标签精简信息列表

- **路径**: GET /mp/tag/list-all-simple
- **权限**: mp:account:query
- **说明**: 查询全部标签的精简信息（id、tagId、name），常用于下拉选择场景。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MpTagSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| tagId | Long | 公众号的标签编号 |
| name | String | 标签名称 |

**业务逻辑**:
1. 查询数据库中全部标签列表（不区分公众号账号）。
2. 通过 MpTagConvert 转换为 MpTagSimpleRespVO 列表返回。

### 2.2 同步公众号标签

- **路径**: POST /mp/tag/sync
- **权限**: mp:tag:sync
- **说明**: 从微信平台拉取指定账号的最新标签列表，与本地数据库进行合并（新增、更新、删除）。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountId | Long | 是 | @RequestParam 必传 | 公众号账号的编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 调用 MpAccountService#getRequiredAccount 校验公众号账号存在，不存在则抛出账号不存在异常（整个方法在事务中执行）。
2. 通过 MpServiceFactory 获取该账号对应的 WxMpService，调用微信平台 tagGet 接口获取最新标签列表；失败时抛出「获得标签失败」异常。
3. 将本地该账号下的标签按微信侧 tagId 建立映射，遍历微信标签列表逐一合并。
4. 微信存在而本地不存在的标签，转换为 MpTagDO 新增入库。
5. 两边都存在的标签，更新本地的标签名与粉丝数量（count）。
6. 遍历结束后本地仍残留（微信侧已不存在）的标签，批量删除（标签总数不超过 100 个，故直接 for 循环处理）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_002_004 | 获得标签失败，原因：{} |
