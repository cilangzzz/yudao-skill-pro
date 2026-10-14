# AI 音乐接口 (AiMusicController)

> 基于 Suno 平台的 AI 音乐生成与管理，提供【我的】音乐分页/详情/重命名/删除、音乐生成（描述模式/歌词模式），以及管理端音乐分页/详情/发布状态更新/删除。

## 接口路径前缀

/ai/music  (Controller: AiMusicController)

## 1. 通用数据结构

### 1.1 AiMusicPageReqVO（分页请求）

继承 `PageParam`（含 `pageNo` 页码、`pageSize` 每页条数）。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 否 | - | 用户编号 |
| title | String | 否 | - | 音乐名称 |
| status | Integer | 否 | @InEnum(AiMusicStatusEnum) | 音乐状态（10 进行中、20 已完成、30 已失败） |
| generateMode | Integer | 否 | @InEnum(AiMusicGenerateModeEnum) | 生成模式（1 描述模式、2 歌词模式） |
| publicStatus | Boolean | 否 | - | 是否发布 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

### 1.2 AiMusicRespVO（音乐响应）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| title | String | 音乐名称 |
| lyric | String | 歌词 |
| imageUrl | String | 图片地址 |
| audioUrl | String | 音频地址 |
| videoUrl | String | 视频地址 |
| status | Integer | 音乐状态（10 进行中、20 已完成、30 已失败） |
| gptDescriptionPrompt | String | 描述词 |
| prompt | String | 提示词 |
| platform | String | 模型平台（如 Suno） |
| model | String | 模型（如 chirp-v3.5） |
| generateMode | Integer | 生成模式（1 描述模式、2 歌词模式） |
| tags | List&lt;String&gt; | 音乐风格标签 |
| duration | Double | 音乐时长 |
| publicStatus | Boolean | 是否发布 |
| taskId | String | 任务编号（Suno 任务 ID） |
| errorMessage | String | 错误信息 |
| createTime | LocalDateTime | 创建时间 |

## 2. 【我的】音乐（用户端）

> 以下接口均无 @PreAuthorize 注解，仅需登录（已认证），按当前登录用户校验归属。

### 2.1 获得【我的】音乐分页

- **路径**: GET /ai/music/my-page
- **权限**: 已认证
- **说明**: 分页查询【我的】音乐列表

**请求参数 (AiMusicPageReqVO)**: 字段见 [1.1](#11-aimusicpagereqvo分页请求)

**响应**: CommonResult&lt;PageResult&lt;AiMusicRespVO&gt;&gt;，字段见 [1.2](#12-aimusicrespvo音乐响应)

**业务逻辑**:
1. 以当前登录用户 ID 调用 `musicMapper.selectPageByMy` 分页查询。
2. 查询条件：`publicStatus=true` 时只查公开（已发布）音乐；`publicStatus=false` 时只查当前用户的私有音乐；未指定时二者均不加过滤。
3. 结果按 id 升序排列，转换为一页 AiMusicRespVO 返回。

### 2.2 音乐生成

- **路径**: POST /ai/music/generate
- **权限**: 已认证
- **说明**: 调用 Suno 生成音乐，支持描述模式与歌词模式

**请求参数 (AiSunoGenerateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| platform | String | 是 | @NotBlank | 平台（参见 AiPlatformEnum，如 Suno） |
| generateMode | Integer | 是 | @NotNull | 生成模式（1 描述模式、2 歌词模式） |
| prompt | String | 否 | - | 歌词提示：描述模式为描述词；歌词模式为歌词内容 |
| makeInstrumental | Boolean | 否 | - | 是否纯音乐（仅描述模式使用） |
| model | String | 是 | @NotEmpty | 模型（如 chirp-v3.5） |
| tags | List&lt;String&gt; | 否 | - | 音乐风格（仅歌词模式使用，逗号拼接传给 Suno） |
| title | String | 否 | - | 音乐/歌曲名称（仅歌词模式使用） |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt;（生成的音乐记录编号数组）

| 字段 | 类型 | 说明 |
|-----|------|------|
| - | List&lt;Long&gt; | 新插入音乐记录的编号列表 |

**业务逻辑**:
1. 通过 `modelService.getSunoApi()` 获取 Suno API 客户端（整个方法带事务 @Transactional）。
2. 描述模式（generateMode=1）：构造 `MusicGenerateRequest(prompt, model, makeInstrumental)` 调用 `sunoApi.generate`。
3. 歌词模式（generateMode=2）：构造 `MusicGenerateRequest(prompt, model, tags 逗号拼接, title)` 调用 `sunoApi.customGenerate`。
4. 其它模式抛出 `IllegalArgumentException("未知生成模式")`；Suno 返回为空时直接返回空列表。
5. 将 Suno 返回的 MusicData 转换为 AiMusicDO：status 按 `complete→20(已完成)`、`error→30(已失败)`、其余 `→10(进行中)` 映射，并填充 taskId、model、描述词、标题、时长、歌词、风格标签、错误信息等。
6. 状态为已完成（20）时，将音频/视频/图片地址通过 `HttpUtil.downloadBytes` 下载并经 `fileApi.createFile` 上传到内部文件服务器（失败则保留原 URL）。
7. 设置 userId（当前登录用户）、platform、generateMode 后批量插入 `ai_music` 表，返回记录编号列表。

### 2.3 删除【我的】音乐记录

- **路径**: DELETE /ai/music/delete-my
- **权限**: 已认证
- **说明**: 删除当前用户自己的音乐记录

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 音乐编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验音乐记录存在，不存在抛 MUSIC_NOT_EXISTS。
2. 校验记录的 userId 与当前登录用户一致，不一致抛 IMAGE_NOT_EXISTS（源码此处复用了绘画域错误码）。
3. 校验通过后按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_006_000 | 音乐不存在! |
| 1_040_005_000 | 图片不存在!（delete-my 校验非本人时抛出，源码复用绘画域错误码） |

### 2.4 获取【我的】音乐

- **路径**: GET /ai/music/get-my
- **权限**: 已认证
- **说明**: 获取当前用户自己的单条音乐详情

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 音乐编号 |

**响应**: CommonResult&lt;AiMusicRespVO&gt;，字段见 [1.2](#12-aimusicrespvo音乐响应)（记录不存在或非本人时返回 null）

**业务逻辑**:
1. 按编号查询音乐记录。
2. 记录不存在或记录的 userId 与当前登录用户不一致时，返回 null（不抛异常）。
3. 校验通过则转换为 AiMusicRespVO 返回。

### 2.5 修改【我的】音乐（目前只支持修改标题）

- **路径**: POST /ai/music/update-my
- **权限**: 已认证
- **说明**: 修改当前用户自己的音乐标题

**请求参数 (AiMusicUpdateMyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 音乐编号 |
| title | String | 否 | - | 音乐名称 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验音乐记录存在，不存在抛 MUSIC_NOT_EXISTS。
2. 校验记录的 userId 与当前登录用户一致，不一致同样抛 MUSIC_NOT_EXISTS。
3. 校验通过后仅更新标题（title）字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_006_000 | 音乐不存在! |

## 3. 音乐管理（管理端）

### 3.1 获得音乐分页

- **路径**: GET /ai/music/page
- **权限**: ai:music:query
- **说明**: 管理端按条件分页查询全部音乐

**请求参数 (AiMusicPageReqVO)**: 字段见 [1.1](#11-aimusicpagereqvo分页请求)

**响应**: CommonResult&lt;PageResult&lt;AiMusicRespVO&gt;&gt;，字段见 [1.2](#12-aimusicrespvo音乐响应)

**业务逻辑**:
1. 调用 `musicMapper.selectPage` 分页查询，条件全部为"有值才过滤"（eqIfPresent/betweenIfPresent）：userId、title、status、generateMode、publicStatus、createTime 区间。
2. 结果按 id 降序排列，转换为 AiMusicRespVO 分页返回。

### 3.2 获得音乐

- **路径**: GET /ai/music/get
- **权限**: ai:music:query
- **说明**: 管理端查询单条音乐详情

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 编号 |

**响应**: CommonResult&lt;AiMusicRespVO&gt;，字段见 [1.2](#12-aimusicrespvo音乐响应)

**业务逻辑**:
1. 按编号调用 `musicMapper.selectById` 查询记录。
2. 转换为 AiMusicRespVO 返回。

### 3.3 删除音乐

- **路径**: DELETE /ai/music/delete
- **权限**: ai:music:delete
- **说明**: 管理端删除音乐记录

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验音乐记录存在，不存在抛 MUSIC_NOT_EXISTS。
2. 校验通过后按 id 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_006_000 | 音乐不存在! |

### 3.4 更新音乐

- **路径**: PUT /ai/music/update
- **权限**: ai:music:update
- **说明**: 管理端更新音乐（目前仅支持发布状态）

**请求参数 (AiMusicUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 音乐编号 |
| publicStatus | Boolean | 否 | - | 是否发布 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验音乐记录存在，不存在抛 MUSIC_NOT_EXISTS。
2. 按编号仅更新发布状态（publicStatus）字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_006_000 | 音乐不存在! |

## 附注

- Service 层另有 `syncMusic()` 方法（无 admin 端点，供定时任务调用）：查询所有"进行中"（10）的任务，按 36 个一批调用 `sunoApi.getMusicList` 同步 Suno 任务状态，并将已完成音乐的三类文件转存到内部文件服务器。
- 音乐域错误码前缀为 1-040-006-XXX，当前仅 `MUSIC_NOT_EXISTS`（1_040_006_000）一个。
