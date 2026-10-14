# AI 绘画（含 Midjourney）接口 (AiImageController)

> 提供 AI 绘画能力：通用平台（OpenAI / SiliconFlow / StableDiffusion / 通义万相）文生图、Midjourney 绘图（imagine/action/回调通知），以及绘画记录的查询、发布、删除与管理。

## 接口路径前缀

/ai/image  (Controller: AiImageController)

> 该域仅有一个控制器，内部按「我的绘画（用户端）」「Midjourney 专属」「绘画管理（管理端）」三组划分。除管理端 4 个接口有 `@PreAuthorize` 权限标识、midjourney/notify 为 `@PermitAll` 回调外，其余接口仅需登录（已认证）。

---

## 1. 我的绘画（用户端）

### 1.1 获取【我的】绘图分页

- **路径**: GET /ai/image/my-page
- **权限**: 已认证（仅登录，按当前登录用户过滤）
- **说明**: 分页返回当前登录用户自己的绘画记录。

**请求参数 (AiImagePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Long | 是 | @NotNull、@Min(1) | 页码，从 1 开始 |
| pageSize | Long | 是 | @NotNull、@Min(1)、@Max(100) | 每页条数 |
| userId | Long | 否 | - | 用户编号（管理端分页用，本接口按登录用户覆盖） |
| platform | String | 否 | - | 平台，如 OpenAI |
| prompt | String | 否 | - | 提示词（模糊匹配） |
| status | Integer | 否 | - | 绘画状态 |
| publicStatus | Boolean | 否 | - | 是否发布 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult<PageResult<AiImageRespVO>>

**业务逻辑**: 1. 以当前登录用户 id + 分页条件调用 Mapper 的 selectPageMy 查询。 2. DO 转换为 AiImageRespVO 分页返回。

### 1.2 获取公开的绘图分页

- **路径**: GET /ai/image/public-page
- **权限**: 已认证（仅登录）
- **说明**: 分页返回已发布（publicStatus=true）的公开绘画，供画廊展示。

**请求参数 (AiImagePublicPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Long | 是 | @NotNull、@Min(1) | 页码 |
| pageSize | Long | 是 | @NotNull、@Min(1)、@Max(100) | 每页条数 |
| prompt | String | 否 | - | 提示词（模糊匹配） |

**响应**: CommonResult<PageResult<AiImageRespVO>>

**业务逻辑**: 1. 按分页参数查询绘画分页（条件已限定公开数据）。 2. DO 转换为 AiImageRespVO 返回。

### 1.3 获取【我的】绘图记录

- **路径**: GET /ai/image/get-my
- **权限**: 已认证（仅登录）
- **说明**: 按编号获取单条绘画详情，仅当记录属于当前登录用户时返回，否则返回 null。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 绘画编号 |

**响应**: CommonResult<AiImageRespVO>，字段见 [AiImageRespVO 字段](#响应字段-aiimagerespvo)

**业务逻辑**: 1. 按编号查询绘画记录。 2. 记录不存在或 userId 不等于当前登录用户时返回 null（不抛异常）。 3. 否则转换为 AiImageRespVO 返回。

### 1.4 获取【我的】绘图记录列表

- **路径**: GET /ai/image/my-list-by-ids
- **权限**: 已认证（仅登录）
- **说明**: 按编号数组批量获取绘画记录，过滤掉不属于当前登录用户的记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List\<Long\> | 是 | @RequestParam | 绘画编号数组，如 1024,2048 |

**响应**: CommonResult<List<AiImageRespVO>>，元素字段见 [AiImageRespVO 字段](#响应字段-aiimagerespvo)

**业务逻辑**: 1. 编号数组为空时返回空列表。 2. 按编号集合批量查询。 3. 移除 userId 与当前登录用户不相等的记录。 4. 转换为 AiImageRespVO 列表返回。

### 1.5 生成图片

- **路径**: POST /ai/image/draw
- **权限**: 已认证（仅登录）
- **说明**: 通用平台文生图，先落库返回绘画编号，前端凭编号轮询结果。

**请求参数 (AiImageDrawReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| modelId | Long | 是 | @NotNull | 模型编号 |
| prompt | String | 是 | @NotEmpty、@Size(max=1200) | 提示词，最大 1200 字 |
| height | Integer | 是 | @NotNull | 图片高度（dall-e-2：256/512/1024；dall-e-3：1024、1792x1024、1024x1792） |
| width | Integer | 是 | @NotNull | 图片宽度 |
| options | Map\<String, String\> | 否 | - | 各平台拓展参数（OpenAI 的 style；StabilityAI 的 seed/scale/steps/sampler/stylePreset/clipGuidancePreset 等） |

**响应**: CommonResult\<Long\>（绘画记录编号，用于轮询）

**业务逻辑**: 1. 校验模型存在且可用（modelService.validateModel）。 2. 将请求转换为 AiImageDO 落库：记录 userId、platform、modelId、model，publicStatus=false，status=进行中。 3. 通过 AOP 代理异步执行 executeDrawImage：按平台构建 ImageOptions（OpenAI/SiliconFlow/StableDiffusion/通义万相，不支持的平台抛出异常）。 4. 调用 ImageModel.call 生成图片，若结果为空抛出异常。 5. 优先解码 b64Json，否则按 URL 下载图片字节，上传文件服务获得 picUrl。 6. 更新记录状态为成功、picUrl、完成时间；异常时更新为失败并记录 errorMessage 与完成时间。 7. 返回绘画记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_001_000 | 模型不存在! |
| 1_040_001_001 | 模型({})已禁用! |

### 1.6 删除【我的】绘画记录

- **路径**: DELETE /ai/image/delete-my
- **权限**: 已认证（仅登录）
- **说明**: 删除当前登录用户自己的绘画记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 绘画编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验绘画记录存在，不存在抛 IMAGE_NOT_EXISTS。 2. 记录的 userId 与当前登录用户不一致时同样抛 IMAGE_NOT_EXISTS（防止越权）。 3. 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_005_000 | 图片不存在! |

---

## 2. Midjourney 专属

### 2.1 【Midjourney】生成图片

- **路径**: POST /ai/image/midjourney/imagine
- **权限**: 已认证（仅登录）
- **说明**: 提交 Midjourney imagine 任务，落库后向 Midjourney Proxy 提交，返回绘画编号供轮询。

**请求参数 (AiMidjourneyImagineReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| prompt | String | 是 | @NotEmpty | 提示词，如「中国神龙」 |
| modelId | Long | 是 | @NotNull | 模型编号（平台须为 Midjourney） |
| width | Integer | 是 | @NotNull | 图片宽度 |
| height | Integer | 是 | @NotNull | 图片高度 |
| version | String | 是 | @NotEmpty | 版本号，如 6.0 |
| referImageUrl | String | 否 | - | 参考图 URL |

**响应**: CommonResult\<Long\>（绘画记录编号）

**业务逻辑**: 1. 校验模型存在且可用，并断言平台为 Midjourney（否则报「平台不匹配」）；获取 MidjourneyApi。 2. 落库：userId、publicStatus=false、status=进行中、platform=MIDJOURNEY、modelId、model。 3. referImageUrl 非空时下载图片并转 base64 作为参考图，组装 ImagineRequest（含 width/height/version/model 的 state）调用 midjourneyApi.imagine 提交任务。 4. 提交失败（code 不在成功码中）时抛 IMAGE_MIDJOURNEY_SUBMIT_FAIL，quota_not_enough 场景提示「账户余额不足」。 5. 提交成功则回写 taskId 与请求参数 options。 6. 返回绘画编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_001_000 | 模型不存在! |
| 1_040_001_001 | 模型({})已禁用! |
| 1_040_005_001 | Midjourney 提交失败!原因：{} |

### 2.2 【Midjourney】通知图片进展

- **路径**: POST /ai/image/midjourney/notify
- **权限**: @PermitAll（由 Midjourney Proxy 回调，免登录），同时标注 @TenantIgnore 忽略租户；必须为 POST 方法
- **说明**: Midjourney Proxy 回调接口，按 taskId 更新对应绘画记录的状态与图片。

**请求参数 (MidjourneyApi.Notify)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | String | 是 | @NotEmpty（继承父接口校验） | 任务编号（对应绘画记录 taskId） |
| action | String | 是 | - | 动作，如 IMAGINE、UPSCALE 等 |
| status | String | 是 | - | 任务状态（NOT_START/SUBMITTED/IN_PROGRESS/FAILURE/SUCCESS） |
| prompt | String | 否 | - | 原始提示词 |
| promptEn | String | 否 | - | 英文提示词 |
| description | String | 否 | - | 任务描述 |
| state | String | 否 | - | 提交时的 state 参数 |
| submitTime | Long | 否 | - | 提交时间（时间戳） |
| startTime | Long | 否 | - | 开始时间（时间戳） |
| finishTime | Long | 否 | - | 结束时间（时间戳） |
| imageUrl | String | 否 | - | 生成图片 URL |
| progress | String | 否 | - | 任务进度，如 100% |
| failReason | String | 否 | - | 失败原因 |
| buttons | List\<Button\> | 否 | - | 可用操作按钮（customId/emoji/label/type/style） |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 按 notify.id（taskId）查询绘画记录，不存在仅打 warn 日志返回（不报错）。 2. 转换状态：SUCCESS → 绘画成功并记录完成时间；FAILURE → 绘画失败，其余状态不变。 3. imageUrl 非空时下载图片上传文件服务获得 picUrl，上传失败则降级使用原始 URL 并打 warn。 4. 更新记录：status、picUrl、buttons、errorMessage（失败原因）、finishTime。

### 2.3 【Midjourney】Action 操作（二次生成图片）

- **路径**: POST /ai/image/midjourney/action
- **权限**: 已认证（仅登录）
- **说明**: 对已有 Midjourney 图片执行按钮操作（放大、缩小、U1、U2 等），生成一条新的绘画记录。

**请求参数 (AiMidjourneyActionReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 图片（绘画记录）编号 |
| customId | String | 是 | @NotEmpty | 操作按钮编号，如 MJ::JOB::variation::4::06aa3e66-... |

**响应**: CommonResult\<Long\>（新生成的绘画记录编号）

**业务逻辑**: 1. 校验绘画记录存在且属于当前登录用户（否则抛 IMAGE_NOT_EXISTS）；获取 MidjourneyApi。 2. 在记录的 buttons 中查找 customId 匹配的按钮，不存在抛 IMAGE_CUSTOM_ID_NOT_EXISTS。 3. 调用 midjourneyApi.action 提交任务，提交失败抛 IMAGE_MIDJOURNEY_SUBMIT_FAIL（quota_not_enough 提示「账户余额不足」）。 4. 新增一条绘画记录：沿用原记录的 userId/prompt/model/width/height/options，publicStatus=false、status=进行中、taskId 为新任务编号。 5. 返回新记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_005_000 | 图片不存在! |
| 1_040_005_001 | Midjourney 提交失败!原因：{} |
| 1_040_005_002 | Midjourney 按钮 customId 不存在! {} |

---

## 3. 绘画管理（管理端）

### 3.1 获得绘画分页

- **路径**: GET /ai/image/page
- **权限**: ai:image:query
- **说明**: 管理端分页查询全部用户的绘画记录。

**请求参数 (AiImagePageReqVO，继承 PageParam)**: 同 [1.1](#11-获取我的绘图分页)（userId/platform/prompt/status/publicStatus/createTime + pageNo/pageSize）

**响应**: CommonResult<PageResult<AiImageRespVO>>，字段见 [AiImageRespVO 字段](#响应字段-aiimagerespvo)

**业务逻辑**: 1. 按分页条件查询绘画分页（不限用户）。 2. DO 转换为 AiImageRespVO 返回。

### 3.2 获得绘画

- **路径**: GET /ai/image/get
- **权限**: ai:image:query
- **说明**: 管理端按编号获取绘画详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 绘画编号 |

**响应**: CommonResult<AiImageRespVO>，字段见 [AiImageRespVO 字段](#响应字段-aiimagerespvo)

**业务逻辑**: 1. 按编号查询绘画记录。 2. 转换为 AiImageRespVO 返回。

### 3.3 更新绘画

- **路径**: PUT /ai/image/update
- **权限**: ai:image:update
- **说明**: 管理端更新绘画，主要用于修改发布（公开）状态。

**请求参数 (AiImageUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 编号 |
| publicStatus | Boolean | 否 | - | 是否发布 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验绘画记录存在，不存在抛 IMAGE_NOT_EXISTS。 2. 更新记录（当前仅发布状态字段）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_005_000 | 图片不存在! |

### 3.4 删除绘画

- **路径**: DELETE /ai/image/delete
- **权限**: ai:image:delete
- **说明**: 管理端删除任意绘画记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 绘画编号 |

**响应**: CommonResult\<Boolean\>（true）

**业务逻辑**: 1. 校验绘画记录存在，不存在抛 IMAGE_NOT_EXISTS。 2. 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_005_000 | 图片不存在! |

---

## 响应字段 (AiImageRespVO)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| platform | String | 平台（参见 AiPlatformEnum，如 OpenAI） |
| model | String | 模型标识 |
| prompt | String | 提示词 |
| width | Integer | 图片宽度 |
| height | Integer | 图片高度 |
| status | Integer | 绘画状态（10 进行中 / 20 已完成 / 30 已失败，参见 AiImageStatusEnum） |
| publicStatus | Boolean | 是否发布 |
| picUrl | String | 图片地址 |
| errorMessage | String | 绘画错误信息 |
| options | Map\<String, String\> | 绘制参数 |
| buttons | List\<MidjourneyApi.Button\> | MJ 按钮（customId/emoji/label/type/style） |
| finishTime | LocalDateTime | 完成时间 |
| createTime | LocalDateTime | 创建时间 |

## 错误码汇总（绘画 1-040-005-000 段）

| 错误码 | 说明 |
|-------|------|
| 1_040_005_000 | 图片不存在! |
| 1_040_005_001 | Midjourney 提交失败!原因：{} |
| 1_040_005_002 | Midjourney 按钮 customId 不存在! {} |

> 相关：绘画依赖模型校验，可能抛出模型域错误码 1_040_001_000（模型不存在!）、1_040_001_001（模型({})已禁用!）。
