# 素材管理接口 (MpMaterialController)

> 管理公众号（含临时/永久）素材的上传、删除与分页查询，文件同时上传至微信服务器与本地文件服务，并在数据库留存记录。

## 接口路径前缀

/mp/material  (Controller: MpMaterialController)

## 1. 素材上传

### 1.1 上传临时素材

- **路径**: POST /mp/material/upload-temporary
- **权限**: mp:material:upload-temporary
- **说明**: 上传临时素材（image/voice/video/thumb 等）到微信，有效期为 3 天，同时保存到文件服务与数据库。

**请求参数 (MpMaterialUploadTemporaryReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| type | String | 是 | @NotEmpty | 文件类型，参见 WxConsts.MediaFileType 枚举，如 image |
| file | MultipartFile | 是 | @NotNull | 文件附件 |

**响应**: CommonResult<MpMaterialUploadRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| mediaId | String | 素材的 media_id |
| url | String | 素材的 URL（文件服务地址） |

**业务逻辑**:
1. 通过 MpServiceFactory 根据 accountId 获取对应公众号的 WxMpService 实例。
2. 将上传的文件写入服务器临时目录。
3. 调用微信 API（mediaUpload）上传临时素材，media_id 优先取 mediaId，否则取 thumbMediaId。
4. 将文件内容上传到本地文件服务（FileApi），以「mediaId.文件类型」作为存储路径，得到 URL。
5. 微信上传失败（WxErrorException）时抛出 MATERIAL_UPLOAD_FAIL 异常，并在 finally 中删除临时文件。
6. 查询公众号账号信息，将 mediaId、类型、URL、账号、文件名写入数据库，permanent 置为 false。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_004_001 | 上传素材失败，原因：{} |

### 1.2 上传永久素材

- **路径**: POST /mp/material/upload-permanent
- **权限**: mp:material:upload-permanent
- **说明**: 上传永久素材到微信（长期有效），同时保存到文件服务与数据库。

**请求参数 (MpMaterialUploadPermanentReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| type | String | 是 | @NotEmpty | 文件类型，参见 WxConsts.MediaFileType 枚举，如 image |
| file | MultipartFile | 是 | @NotNull | 文件附件 |
| name | String | 否 | - | 素材名字，为空时使用文件名 |
| title | String | 条件 | @AssertTrue（type 为 video 时必填） | 视频素材的标题 |
| introduction | String | 条件 | @AssertTrue（type 为 video 时必填） | 视频素材的描述 |

**响应**: CommonResult<MpMaterialUploadRespVO>

| 字段 | 类型 | 说明 |
|-----|------|------|
| mediaId | String | 素材的 media_id |
| url | String | 素材的 URL（文件服务地址） |

**业务逻辑**:
1. 通过 MpServiceFactory 根据 accountId 获取对应公众号的 WxMpService 实例。
2. 素材名字 name 为空时默认取上传文件名，随后将文件写入服务器临时目录。
3. 调用微信 API（materialFileUpload）上传永久素材，视频类型需携带 title 与 introduction。
4. 将文件内容上传到本地文件服务，得到 URL。
5. 微信上传失败（WxErrorException）时抛出 MATERIAL_UPLOAD_FAIL 异常，并在 finally 中删除临时文件。
6. 查询公众号账号信息，将 mediaId、类型、URL、名字、标题、描述及微信返回的文件 URL（mpUrl）写入数据库，permanent 置为 true。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_004_001 | 上传素材失败，原因：{} |

### 1.3 上传图文内容中的图片

- **路径**: POST /mp/material/upload-news-image
- **权限**: mp:material:upload-news-image
- **说明**: 上传图文消息正文中的图片，返回微信侧图片 URL，不产生素材记录。

**请求参数 (MpMaterialUploadNewsImageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| file | MultipartFile | 是 | @NotNull | 文件附件 |

**响应**: CommonResult&lt;String&gt;（图片在微信服务器上的 URL）

**业务逻辑**:
1. 通过 MpServiceFactory 根据 accountId 获取对应公众号的 WxMpService 实例。
2. 将上传的文件写入服务器临时目录。
3. 调用微信 API（mediaImgUpload）上传图片，返回微信侧的 URL。
4. 微信上传失败（WxErrorException）时抛出 MATERIAL_IMAGE_UPLOAD_FAIL 异常，并在 finally 中删除临时文件。
5. 不写入数据库（区别于临时/永久素材）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_004_002 | 上传图片失败，原因：{} |

## 2. 素材删除

### 2.1 删除素材

- **路径**: DELETE /mp/material/delete-permanent
- **权限**: mp:material:delete
- **说明**: 删除永久素材（同时删除微信侧与数据库记录）；临时素材无需微信删除，仅删数据库记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required = true) | 素材编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

**业务逻辑**:
1. 根据编号查询素材记录，不存在时抛出 MATERIAL_NOT_EXISTS 异常。
2. 永久素材（permanent = true）：根据素材所属 appId 获取 WxMpService，调用微信 API（materialDelete）删除微信侧素材，失败时抛出 MATERIAL_DELETE_FAIL。
3. 临时素材不调用微信删除（3 天后自动失效）。
4. 删除数据库中的素材记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_004_000 | 素材不存在 |
| 1_006_004_003 | 删除素材失败，原因：{} |

## 3. 素材查询

### 3.1 获得素材分页

- **路径**: GET /mp/material/page
- **权限**: mp:material:query
- **说明**: 分页查询素材列表，按公众号账号过滤，可按是否永久、文件类型筛选。

**请求参数 (MpMaterialPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数，最大值为 200 |
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| permanent | Boolean | 否 | - | 是否永久：true - 永久；false - 临时 |
| type | String | 否 | - | 文件类型，参见 WxConsts.MediaFileType 枚举，如 image |

**响应**: CommonResult&lt;PageResult&lt;MpMaterialRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 |
| accountId | Long | 公众号账号的编号 |
| appId | String | 公众号账号的 appId |
| mediaId | String | 素材的 media_id |
| type | String | 文件类型，参见 WxConsts.MediaFileType 枚举 |
| permanent | Boolean | 是否永久：true - 永久；false - 临时 |
| url | String | 素材的 URL（文件服务地址） |
| name | String | 名字 |
| mpUrl | String | 公众号文件 URL，只有【永久素材】使用 |
| title | String | 视频素材的标题，只有【永久素材】使用 |
| introduction | String | 视频素材的描述，只有【永久素材】使用 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 accountId 精确匹配查询素材分页。
2. permanent、type 条件存在时才参与过滤（eqIfPresent）。
3. 按编号倒序（id DESC）返回分页结果，DO 经 MpMaterialConvert 转换为 RespVO。

## 附注

- Service 另有内部方法 `downloadMaterialUrl`（无对应 admin 端点）：优先从数据库按 accountId + mediaId 查询已下载素材直接返回 URL；未命中则调用微信 mediaDownload 下载媒体文件（最多重试 3 次，媒体文件在微信后台仅保存 3 天），上传到文件服务后以临时素材（permanent = false）落库，供消息收发等场景复用。
- 错误码使用 mp 模块「公众号素材」段 1-006-004-000。
