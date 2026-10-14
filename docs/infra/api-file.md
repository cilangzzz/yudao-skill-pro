# 文件服务接口 (FileController + FileConfigController)

> 提供 infra 模块的文件上传/下载/管理与文件存储配置管理能力：文件支持后端上传与前端直传（预签名）两种模式，存储配置支持 DB/本地/FTP/SFTP/S3 等多种存储器并支持 Master 主配置切换。

## 接口路径前缀

- /infra/file  (Controller: FileController) —— 文件记录与文件内容
- /infra/file-config  (Controller: FileConfigController) —— 文件存储配置

---

## 1. 文件管理（FileController）

### 1.1 上传文件（后端上传模式）

- **路径**: POST /infra/file/upload
- **权限**: 已认证（未配置 @PreAuthorize）
- **说明**: 模式一：后端接收 multipart 文件并上传到 Master 存储器，返回文件访问 URL。

**请求参数 (FileUploadReqVO)**（form-data）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| file | MultipartFile | 是 | @NotNull | 文件附件（binary） |
| directory | String | 否 | @AssertTrue（isDirectoryValid） | 文件目录，如 XXX/YYY；禁止绝对路径、目录穿越等 |

**响应**: CommonResult&lt;String&gt; —— 文件访问 URL（如 `https://www.iocoder.cn/yudao.jpg`）

**业务逻辑**:
1. Controller 读取 MultipartFile 的字节内容，以原文件名、directory、contentType 调用 Service。
2. `FilePathUtils.validateFileName` 校验文件名合法性，禁止携带目录路径（非法抛 FILE_PATH_INVALID）。
3. 校验文件内容非空（FILE_IS_EMPTY）；通过文件内容探测真实 MIME 类型（不信任客户端传入的 type），校验其在 ALLOWED_FILE_TYPES 白名单内；图片类型还要求与文件名后缀推断的类型一致，否则抛 FILE_TYPE_NOT_ALLOWED。
4. 文件名为空时以内容 SHA-256 作为文件名；文件名无后缀时按 MIME 类型补充后缀。
5. `generateUploadPath` 生成唯一存储路径：校验 path/directory 合法性，默认启用日期前缀（yyyyMMdd 分目录），时间戳后缀默认关闭（可静态开关调整）。
6. 获取 Master 文件配置对应的 FileClient（无则断言失败），上传内容并得到访问 URL。
7. 将 configId、name、path、url、type、size 插入 infra_file 表，返回 URL。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_002 | 文件为空 |
| 1_001_003_003 | 文件路径不正确 |
| 1_001_003_004 | 不支持的文件类型 |

### 1.2 获取文件预签名地址（前端直传模式）

- **路径**: GET /infra/file/presigned-url
- **权限**: 已认证（未配置 @PreAuthorize）
- **说明**: 模式二：前端直传七牛、阿里云 OSS 等 S3 协议存储器，先获取预签名上传地址与访问地址。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 是 | @RequestParam required | 文件名称 |
| directory | String | 否 | 无 | 文件目录 |

**响应**: CommonResult&lt;FilePresignedUrlRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| configId | Long | 配置编号 |
| uploadUrl | String | 文件上传 URL（预签名，含签名参数） |
| url | String | 文件访问 URL（前端上传完成后用它访问） |
| path | String | 文件路径（前端上传完成后调用 /create 登记） |

**业务逻辑**:
1. `generateUploadPath` 生成唯一存储路径（同 1.1 的路径生成规则）。
2. 前端直传无法读取文件内容，仅按文件名推断 MIME 类型并校验白名单，不合法抛 FILE_TYPE_NOT_ALLOWED。
3. 获取 Master FileClient，调用 presignPutUrl 生成预签名上传 URL，presignGetUrl 生成预签名访问 URL。
4. 返回 configId、path、uploadUrl、url。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_003 | 文件路径不正确 |
| 1_001_003_004 | 不支持的文件类型 |

### 1.3 创建文件（前端直传登记）

- **路径**: POST /infra/file/create
- **权限**: 已认证（未配置 @PreAuthorize）
- **说明**: 配合 presigned-url 接口，前端直传完成后登记文件记录。

**请求参数 (FileCreateReqVO)**（JSON body）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| configId | Long | 是 | @NotNull | 文件配置编号 |
| path | String | 是 | @NotNull | 文件路径（存储路径） |
| name | String | 是 | @NotNull | 原文件名 |
| url | String | 是 | @NotNull | 文件 URL |
| type | String | 否 | 无 | 文件 MIME 类型 |
| size | Long | 否 | 无（Schema 标记 REQUIRED） | 文件大小 |

**响应**: CommonResult&lt;Long&gt; —— 文件编号

**业务逻辑**:
1. `validatePath` 校验存储路径合法性（禁止绝对路径/目录穿越），`validateFileName` 校验并规范化原文件名。
2. 分别按原文件名与存储路径推断 MIME 类型并校验白名单，二者不一致时抛 FILE_TYPE_NOT_ALLOWED（前端直传不校验文件内容）。
3. 处理 URL：移除 URL 中的查询参数（如私有桶的签名参数），保证 URL 唯一性。
4. VO 转换为 FileDO 插入数据库，返回文件编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_003 | 文件路径不正确 |
| 1_001_003_004 | 不支持的文件类型 |

### 1.4 获得文件

- **路径**: GET /infra/file/get
- **权限**: infra:file:query
- **说明**: 按编号获得文件记录详情（不返回文件内容）。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 文件编号 |

**响应**: CommonResult&lt;FileRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文件编号 |
| configId | Long | 配置编号 |
| path | String | 文件路径 |
| name | String | 原文件名 |
| url | String | 文件 URL |
| type | String | 文件 MIME 类型 |
| size | Long | 文件大小 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询文件记录，不存在抛 FILE_NOT_EXISTS。
2. 转换为 FileRespVO 返回（VO 不含 content 字段，避免内容过大）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_001 | 文件不存在 |

### 1.5 获得文件分页

- **路径**: GET /infra/file/page
- **权限**: infra:file:query
- **说明**: 分页获得文件记录列表。

**请求参数 (FilePageReqVO)**（继承 PageParam: pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| path | String | 否 | 无 | 文件路径，模糊匹配 |
| type | String | 否 | 无 | 文件类型，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;FileRespVO&gt;&gt; —— 列表项字段同 1.4 的 FileRespVO

**业务逻辑**:
1. FileMapper 按 path 模糊、type 模糊、createTime 区间条件分页查询。
2. 分页结果转换为 FileRespVO 返回。

### 1.6 下载文件

- **路径**: GET /infra/file/{configId}/get/**（path 为文件路径）
- **权限**: @PermitAll（匿名可访问，且标注 @TenantIgnore 忽略租户）
- **说明**: 从指定配置的存储器读取文件内容，以附件形式输出。

**请求参数**（Path）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| configId | Long | 是 | @PathVariable | 配置编号 |
| path | String | 是 | 无（URL 通配段） | 文件路径，取 /get/ 之后的部分 |

**响应**: 文件二进制流（attachment）；文件不存在时返回 HTTP 404。

**业务逻辑**:
1. 从请求 URI 截取 /get/ 之后的路径，为空抛出 IllegalArgumentException；对路径做 URL 解码，解决中文、%、+ 等特殊字符问题。
2. `validatePath` 校验路径合法性，按 configId 获取 FileClient（经 10 秒异步刷新的本地缓存）读取文件内容。
3. 内容为 null 时记录 warn 日志并返回 HTTP 404。
4. 按 configId + path 查询最新文件记录，取其原文件名（无记录则取路径末段）作为下载文件名，写出附件内容。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_003 | 文件路径不正确 |

### 1.7 删除文件

- **路径**: DELETE /infra/file/delete
- **权限**: infra:file:delete
- **说明**: 删除单个文件：同时删除存储器中的文件与数据库记录。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 文件编号 |

**响应**: CommonResult&lt;Boolean&gt; —— true

**业务逻辑**:
1. 校验文件存在，不存在抛 FILE_NOT_EXISTS。
2. 校验文件存储路径合法性，避免误删存储器中的其他文件。
3. 按文件记录的 configId 获取对应 FileClient，从存储器删除该路径文件。
4. 删除数据库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_001 | 文件不存在 |
| 1_001_003_003 | 文件路径不正确 |

### 1.8 批量删除文件

- **路径**: DELETE /infra/file/delete-list
- **权限**: infra:file:delete
- **说明**: 按编号列表批量删除文件。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam required | 文件编号列表 |

**响应**: CommonResult&lt;Boolean&gt; —— true

**业务逻辑**:
1. 按 ids 查询文件记录列表。
2. 逐个校验路径合法性，并按各记录的 configId 获取 FileClient，从存储器删除文件。
3. 批量删除数据库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_003_003 | 文件路径不正确 |

---

## 2. 文件配置管理（FileConfigController）

存储器 storage 取值参见 FileStorageEnum：DB=1、LOCAL=10（本地磁盘）、FTP=11、SFTP=12、S3=20（兼容七牛/阿里云/腾讯云等 S3 协议）。FileClient 通过 Guava LoadingCache 缓存（10 秒异步刷新），Master 配置使用固定缓存键 0。

### 2.1 创建文件配置

- **路径**: POST /infra/file-config/create
- **权限**: infra:file-config:create
- **说明**: 新增一个文件存储配置（默认非 Master）。

**请求参数 (FileConfigSaveReqVO)**（JSON body，创建与更新共用）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 编号（更新时必传） |
| name | String | 是 | @NotNull | 配置名，如 S3 - 阿里云 |
| storage | Integer | 是 | @NotNull | 存储器，参见 FileStorageEnum 枚举 |
| config | Map&lt;String, Object&gt; | 是 | @NotNull | 存储配置，动态参数以 Map 接收，按 storage 反序列化为对应 FileClientConfig 并做 JSR-303 校验 |
| remark | String | 否 | 无 | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 配置编号

**业务逻辑**:
1. 按 storage 从 FileStorageEnum 找到对应配置类，将 Map 先转 JSON 再反序列化为 FileClientConfig，并通过 Validator 校验参数合法性。
2. master 强制置为 false（新建配置默认非主配置）。
3. 插入数据库，返回配置编号。

### 2.2 更新文件配置

- **路径**: PUT /infra/file-config/update
- **权限**: infra:file-config:update
- **说明**: 修改文件配置（请求参数同 2.1 的 FileConfigSaveReqVO，id 必传）。

**响应**: CommonResult&lt;Boolean&gt; —— true

**业务逻辑**:
1. 校验配置存在，不存在抛 FILE_CONFIG_NOT_EXISTS。
2. 以数据库中已有记录的 storage 为准，反序列化并校验新的 config 参数。
3. 更新数据库记录。
4. 清空该配置的 FileClient 缓存；若其为 Master，同时清空 Master 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_006_000 | 文件配置不存在 |

### 2.3 更新文件配置为 Master

- **路径**: PUT /infra/file-config/update-master
- **权限**: infra:file-config:update
- **说明**: 将指定配置设为主配置（Master），此后文件上传默认使用它。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 配置编号 |

**响应**: CommonResult&lt;Boolean&gt; —— true

**业务逻辑**:
1. 校验配置存在，不存在抛 FILE_CONFIG_NOT_EXISTS。
2. 事务内先将所有配置批量更新为 master=false。
3. 再将指定配置更新为 master=true。
4. 清空 Master 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_006_000 | 文件配置不存在 |

### 2.4 获得文件配置

- **路径**: GET /infra/file-config/get
- **权限**: infra:file-config:query
- **说明**: 按编号获得文件配置详情。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 配置编号 |

**响应**: CommonResult&lt;FileConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 配置名 |
| storage | Integer | 存储器，参见 FileStorageEnum 枚举 |
| master | Boolean | 是否为主配置 |
| config | FileClientConfig | 存储配置（按存储器类型的配置对象） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 直接按 id 查询配置记录并转换为 FileConfigRespVO 返回（未校验存在性，不存在时返回 null 数据）。

### 2.5 获得文件配置分页

- **路径**: GET /infra/file-config/page
- **权限**: infra:file-config:query
- **说明**: 分页获得文件配置列表。

**请求参数 (FileConfigPageReqVO)**（继承 PageParam: pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | 无 | 配置名，模糊匹配 |
| storage | Integer | 否 | 无 | 存储器 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;FileConfigRespVO&gt;&gt; —— 列表项字段同 2.4 的 FileConfigRespVO

**业务逻辑**:
1. FileConfigMapper 按 name、storage、createTime 条件分页查询。
2. 分页结果转换为 FileConfigRespVO 返回。

### 2.6 测试文件配置是否正确

- **路径**: GET /infra/file-config/test
- **权限**: infra:file-config:query
- **说明**: 向该配置对应的存储器实际上传一个测试文件，验证配置正确性。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 配置编号 |

**响应**: CommonResult&lt;String&gt; —— 测试文件上传后的访问 URL

**业务逻辑**:
1. 校验配置存在，不存在抛 FILE_CONFIG_NOT_EXISTS。
2. 读取内置资源 file/erweima.jpg 作为测试文件内容。
3. 通过该配置对应的 FileClient（经缓存获取）将文件上传到 `public/{UUID}.jpg` 路径，返回上传后的 URL；上传失败即说明配置有误。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_006_000 | 文件配置不存在 |

### 2.7 删除文件配置

- **路径**: DELETE /infra/file-config/delete
- **权限**: infra:file-config:delete
- **说明**: 删除单个文件配置（Master 配置不允许删除）。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 配置编号 |

**响应**: CommonResult&lt;Boolean&gt; —— true

**业务逻辑**:
1. 校验配置存在，不存在抛 FILE_CONFIG_NOT_EXISTS。
2. 若该配置为 Master，抛 FILE_CONFIG_DELETE_FAIL_MASTER（删除会导致无法上传文件）。
3. 删除数据库记录，并清空该配置的 FileClient 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_006_000 | 文件配置不存在 |
| 1_001_006_001 | 该文件配置不允许删除，原因：它是主配置，删除会导致无法上传文件 |

### 2.8 批量删除文件配置

- **路径**: DELETE /infra/file-config/delete-list
- **权限**: infra:file-config:delete
- **说明**: 按编号列表批量删除文件配置（含 Master 时整体失败）。

**请求参数**（Query）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam required | 配置编号列表 |

**响应**: CommonResult&lt;Boolean&gt; —— true

**业务逻辑**:
1. 按 ids 查询配置列表，逐一校验，任一为 Master 则抛 FILE_CONFIG_DELETE_FAIL_MASTER。
2. 批量删除数据库记录。
3. 逐个清空对应配置的 FileClient 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_001_006_001 | 该文件配置不允许删除，原因：它是主配置，删除会导致无法上传文件 |
