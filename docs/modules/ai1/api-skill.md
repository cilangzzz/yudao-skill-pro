# AI1 SKILL 技能接口 (Ai1SkillController / Ai1SkillFileController)

> 管理 AI1 模块的「技能 SKILL」：一种 Claude Agent Skills 风格的提示词能力包。以「管理信息表 `ai1_skill` + 内容文件树表 `ai1_skill_file`」存储，约定根级 `SKILL.md` 为技能入口、`scripts/` 存可执行脚本、`reference/` 存参考文档，提供 SKILL 管理信息的 CRUD 与文件树级的创建/重命名/移动/改内容/删除（含固定节点保护）。Agent 对话生成时由 harness 层的 `Ai1SkillToolFactory` 把绑定的开启状态 SKILL 物化（落盘）到本地沙箱目录，并注册 spring-ai-agent-utils 的 `SkillsTool` 与 Shell/FileSystem 等执行类工具供模型调用。

## 接口路径前缀

- /ai1/skill  (Controller: Ai1SkillController)
- /ai1/skill/file  (Controller: Ai1SkillFileController)

## 1. 通用数据结构

### 1.1 Ai1SkillSaveReqVO（SKILL 新增/修改请求）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 修改时必填 | - | 编号 |
| name | String | 是 | @NotEmpty、@Size(max=100)、@Pattern(regexp="^[A-Za-z0-9-]+$") | 名称，同时作为物化目录名，仅支持字母、数字、中划线 |
| description | String | 否 | @Size(max=500) | 描述 |
| version | String | 是 | @NotEmpty、@Size(max=20) | 版本（如 1.0） |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启、1 关闭） |

### 1.2 Ai1SkillPageReqVO（SKILL 分页请求）

继承 `PageParam`（含 `pageNo` 页码、`pageSize` 每页条数）。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | - | 名称，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态（0 开启、1 关闭） |

### 1.3 Ai1SkillRespVO（SKILL 响应）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名称（同时作为物化目录名） |
| description | String | 描述 |
| version | String | 版本 |
| status | Integer | 状态（0 开启、1 关闭） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间（兼作物化变更指纹） |

> `/ai1/skill/simple-list` 复用该 VO，但只填充 id、name、description 三个字段。

### 1.4 Ai1SkillFileRespVO（内容文件响应）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| skillId | Long | 所属 SKILL 编号 |
| parentId | Long | 父目录编号，0 为根级 |
| name | String | 文件或目录名称（如 SKILL.md） |
| type | Integer | 类型（`Ai1SkillFileTypeEnum`：0 目录、1 文件） |
| fileType | String | 文件类型，即扩展名（小写）；目录为空 |
| content | String | 文件内容；文件树列表接口不返回（置 null），编辑时通过获取接口加载 |
| locked | Boolean | 是否固定：固定节点（SKILL.md、scripts/、reference/）不可删除、改名、移动 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

### 1.5 文件域请求 VO 一览

**Ai1SkillFileCreateReqVO（创建目录或文件）**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| skillId | Long | 是 | @NotNull | SKILL 编号 |
| parentId | Long | 是 | @NotNull | 父目录编号，0 为根级 |
| name | String | 是 | @NotEmpty | 名称（服务层再做格式与同级唯一校验） |
| type | Integer | 是 | @NotNull、@InEnum(Ai1SkillFileTypeEnum) | 类型（0 目录、1 文件） |

**Ai1SkillFileRenameReqVO（重命名）**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 编号 |
| name | String | 是 | @NotEmpty | 新名称 |

**Ai1SkillFileMoveReqVO（移动）**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 编号 |
| parentId | Long | 是 | @NotNull | 目标父目录编号，0 为根级 |

**Ai1SkillFileContentReqVO（保存内容）**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 编号 |
| content | String | 是 | @NotNull、@Size(max=16_777_215) | 文件内容，允许为空字符串；上限对应 MySQL MEDIUMTEXT 容量（16MB-1） |

## 2. SKILL 管理（Ai1SkillController）

### 2.1 创建 SKILL

- **路径**: POST /ai1/skill/create
- **权限**: ai1:skill:create
- **说明**: 创建 SKILL，自动播种固定文件 SKILL.md、scripts/、reference/

**请求参数 (Ai1SkillSaveReqVO)**: 字段见 [1.1](#11-ai1skillsavereqvoskill-新增修改请求)

**响应**: CommonResult&lt;Long&gt;（新 SKILL 编号）

**业务逻辑**（`Ai1SkillServiceImpl.createSkill`，@Transactional）:
1. 校验名称租户内唯一：`Ai1SkillMapper.selectByName` 查同名记录，已存在则抛 SKILL_NAME_DUPLICATE。
2. `BeanUtils.toBean` 转 `Ai1SkillDO` 后 `skillMapper.insert` 插入。
3. 调用 `Ai1SkillFileService.createDefaultSkillFileList(skill)` 播种三条固定节点（`locked=true`，parentId 均为根级 0）：
   - `SKILL.md`（sort=1，type=文件，fileType=md）：内容按 `SKILL_FILE_CONTENT_TEMPLATE` 生成，frontmatter 的 name/description 取自管理信息；其中 description 经 `toFrontmatterValue` 把换行压成空格保持单行，防止破坏 YAML 解析。
   - `scripts/`（sort=2，type=目录）
   - `reference/`（sort=3，type=目录）
4. 事务内完成，任一步失败整体回滚。

### 2.2 更新 SKILL

- **路径**: PUT /ai1/skill/update
- **权限**: ai1:skill:update
- **说明**: 更新 SKILL 的管理信息（名称/描述/版本/状态）

**请求参数 (Ai1SkillSaveReqVO)**: 字段见 [1.1](#11-ai1skillsavereqvoskill-新增修改请求)（id 必传）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`Ai1SkillServiceImpl.updateSkill`）:
1. 校验 SKILL 存在（不存在抛 SKILL_NOT_EXISTS）、名称租户内唯一（排除自身 id）。
2. `BeanUtils.toBean` 转 `Ai1SkillDO` 后 `skillMapper.updateById` 更新。
3. 注意：`SKILL.md` 内面向模型的 frontmatter name/description **不随此接口更新**，由文件编辑器（[3.6 保存内容](#36-保存-skill-文件内容)）独立维护，两套数据互相独立。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_005_000 | SKILL 不存在 |
| 1_041_005_002 | SKILL 名称({}) 已存在 |

### 2.3 删除 SKILL

- **路径**: DELETE /ai1/skill/delete
- **权限**: ai1:skill:delete
- **说明**: 删除 SKILL，级联删除内容文件

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | SKILL 编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`Ai1SkillServiceImpl.deleteSkill` → `deleteSkillListByIds`，@Transactional）:
1. 逐个校验 SKILL 存在，不存在抛 SKILL_NOT_EXISTS。
2. 校验未被 Agent 绑定：调 `Ai1AgentService.getAgentCountBySkillIds`（底层 `Ai1AgentMapper.selectCountBySkillIds` 用 `MyBatisUtils.findInSet` 对 `ai1_agent.skill_ids` 逗号分隔串做 FIND_IN_SET 匹配，因绑定列表经 `LongListTypeHandler` 存字符串无法用 IN），计数大于 0 抛 SKILL_USED_BY_AGENT。
3. 删除 SKILL（`skillMapper.deleteByIds`），并级联删除该 SKILL 的全部内容文件（`Ai1SkillFileMapper.deleteBySkillIds`），同事务完成。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_005_000 | SKILL 不存在 |
| 1_041_005_001 | SKILL 已被 Agent 使用，禁止删除 |

### 2.4 批量删除 SKILL

- **路径**: DELETE /ai1/skill/delete-list
- **权限**: ai1:skill:delete
- **说明**: 批量删除 SKILL，级联删除内容文件

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam | SKILL 编号列表 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 与 [2.3](#23-删除-skill) 完全一致（`deleteSkill` 即委托本方法的单元素版本）：逐个校验存在 → FIND_IN_SET 校验未被任一 Agent 绑定 → 删 SKILL 并级联删全部 `ai1_skill_file`，@Transactional。

**错误码**: 同 [2.3](#23-删除-skill)。

### 2.5 获得 SKILL

- **路径**: GET /ai1/skill/get
- **权限**: ai1:skill:query
- **说明**: 获得 SKILL 详情

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | SKILL 编号 |

**响应**: CommonResult&lt;Ai1SkillRespVO&gt;，字段见 [1.3](#13-ai1skillrespvoskill-响应)

**业务逻辑**: `skillService.getSkill(id)`（`selectById`）后 `BeanUtils.toBean` 转 Ai1SkillRespVO 返回；记录不存在时 data 为 null。

### 2.6 获得 SKILL 分页

- **路径**: GET /ai1/skill/page
- **权限**: ai1:skill:query
- **说明**: 获得 SKILL 分页

**请求参数 (Ai1SkillPageReqVO)**: 字段见 [1.2](#12-ai1skillpagereqvosskill-分页请求)

**响应**: CommonResult&lt;PageResult&lt;Ai1SkillRespVO&gt;&gt;，字段见 [1.3](#13-ai1skillrespvoskill-响应)

**业务逻辑**:
1. `Ai1SkillMapper.selectPage` 分页查询，条件均为"有值才过滤"：name like 模糊、status 等值。
2. 结果按 id 升序排列，转换为 Ai1SkillRespVO 分页返回。

### 2.7 获得 SKILL 精简列表

- **路径**: GET /ai1/skill/simple-list
- **权限**: 已认证（无 @PreAuthorize，仅需登录）
- **说明**: 获得 SKILL 精简列表，只含开启状态，供 Agent 绑定 SKILL 的下拉选择

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;Ai1SkillRespVO&gt;&gt;（每项仅 id、name、description 三个字段）

**业务逻辑**:
1. `skillService.getSkillListByStatus(CommonStatusEnum.ENABLE.getStatus())` 查询全部开启状态的 SKILL，按 id 升序。
2. `convertList` 只取 id、name、description 三个字段返回。
3. 安全提示：该接口与 `/get`、`/page` 的 ai1:skill:query 权限不同级，任何已认证用户可枚举本租户全部开启 SKILL 的名称与描述（与其他模块 simple-list 惯例一致）。

## 3. SKILL 内容文件（Ai1SkillFileController）

> 文件树以 `parentId` 邻接表存储在 `ai1_skill_file`，不做 DB 递归；树合法性（环防御、同级唯一、目录类型校验）全部在应用层保证。所有写操作成功后都会调 `Ai1SkillService.touchSkill` 刷新 SKILL 的 update_time，作为 harness 物化的失效指纹（见 [第 4 节](#4-与-harness-的协作skill-物化与工具注入)）。

### 3.1 获得 SKILL 文件列表

- **路径**: GET /ai1/skill/file/list
- **权限**: ai1:skill:query
- **说明**: 获得 SKILL 文件列表，平铺返回、不返回文件内容

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| skillId | Long | 是 | @RequestParam | SKILL 编号 |

**响应**: CommonResult&lt;List&lt;Ai1SkillFileRespVO&gt;&gt;，字段见 [1.4](#14-ai1skillfilerespvo内容文件响应)（content 置 null）

**业务逻辑**:
1. 先 `skillService.validateSkillExists(skillId)` 防止 SKILL 不存在（抛 SKILL_NOT_EXISTS）。
2. `Ai1SkillFileMapper.selectListBySkillId` 平铺返回该 SKILL 全部节点，排序为目录优先（type 升序）、再按 sort、id 升序。
3. `BeanUtils.toBean` 转 VO 后逐个 `setContent(null)` 减小响应体；前端编辑时按 [3.2](#32-获得-skill-文件含内容) 加载内容。

### 3.2 获得 SKILL 文件（含内容）

- **路径**: GET /ai1/skill/file/get
- **权限**: ai1:skill:query
- **说明**: 获得 SKILL 文件（含内容），编辑时加载

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 文件编号 |

**响应**: CommonResult&lt;Ai1SkillFileRespVO&gt;，字段见 [1.4](#14-ai1skillfilerespvo内容文件响应)（唯一返回 content 的接口）

**业务逻辑**: `skillFileService.getSkillFile(id)`（`selectById`）后转 VO 返回；记录不存在时 data 为 null。

### 3.3 创建 SKILL 目录或文件

- **路径**: POST /ai1/skill/file/create
- **权限**: ai1:skill:update
- **说明**: 在指定父目录下创建目录或文件

**请求参数 (Ai1SkillFileCreateReqVO)**: 字段见 [1.5](#15-文件域请求-vo-一览)

**响应**: CommonResult&lt;Long&gt;（新节点编号）

**业务逻辑**（`Ai1SkillFileServiceImpl.createSkillFile`，@Transactional）:
1. 校验 SKILL 存在（抛 SKILL_NOT_EXISTS）。
2. 校验名称格式 `validateSkillFileName`：去除首尾空白，非空且 ≤200 字符；禁止包含路径分隔符 `/`、`\` 与 ISO 控制字符；禁止为 `.` 或 `..`。不合法抛 SKILL_FILE_NAME_INVALID。
3. 校验父目录 `validateParentDirectory`：根级（parentId=0）直接通过；否则父节点必须存在（否则 SKILL_FILE_PARENT_NOT_EXISTS）、属于同一 SKILL 且为目录类型（否则 SKILL_FILE_PARENT_INVALID）。
4. 校验同级名称唯一 `validateSkillFileNameUnique`（按 skillId + parentId + name 查询），重复抛 SKILL_FILE_NAME_DUPLICATE。
5. 插入节点：sort 取同级 `maxSort + 1`（同级为空时为 1），locked 固定为 false；文件类型按扩展名 `parseFileType` 推断（小写，无扩展名默认 txt）；内容填充：md 文件写入默认模板 `MARKDOWN_FILE_CONTENT_TEMPLATE`（"# 新文档\n\n请在此编写内容（Markdown）。\n"），其他文件为空字符串；目录无 fileType/content。
6. 调 `skillService.touchSkill(skillId)` 刷新物化指纹，返回新节点编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_005_000 | SKILL 不存在 |
| 1_041_006_001 | 名称格式不合法（不能包含路径分隔符、控制字符，且不能为 . 或 ..） |
| 1_041_006_002 | 同级下已存在同名节点({}) |
| 1_041_006_003 | 父节点必须是同一 SKILL 下的目录 |
| 1_041_006_008 | 父目录不存在 |

### 3.4 重命名 SKILL 目录或文件

- **路径**: PUT /ai1/skill/file/rename
- **权限**: ai1:skill:update
- **说明**: 重命名 SKILL 目录或文件，固定节点禁止

**请求参数 (Ai1SkillFileRenameReqVO)**: 字段见 [1.5](#15-文件域请求-vo-一览)

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`Ai1SkillFileServiceImpl.renameSkillFile`，@Transactional）:
1. 校验节点存在（抛 SKILL_FILE_NOT_EXISTS）、非固定节点 `validateSkillFileNotLocked`（locked=true 抛 SKILL_FILE_LOCKED）。
2. 校验新名称格式（同 [3.3](#33-创建-skill-目录或文件) 第 2 步）与同级唯一（排除自身）。
3. 更新 name；若节点为文件，同步刷新 fileType 为新扩展名 `parseFileType(name)`（内容不变）。
4. 调 `skillService.touchSkill` 刷新物化指纹。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_006_000 | 文件或目录不存在 |
| 1_041_006_001 | 名称格式不合法 |
| 1_041_006_002 | 同级下已存在同名节点({}) |
| 1_041_006_004 | 固定文件或目录禁止重命名 |

### 3.5 移动 SKILL 目录或文件

- **路径**: PUT /ai1/skill/file/move
- **权限**: ai1:skill:update
- **说明**: 移动 SKILL 目录或文件，不能移入自身或其后代

**请求参数 (Ai1SkillFileMoveReqVO)**: 字段见 [1.5](#15-文件域请求-vo-一览)

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`Ai1SkillFileServiceImpl.moveSkillFile`，@Transactional）:
1. 校验节点存在、非固定节点（locked 抛 SKILL_FILE_LOCKED）。
2. 成环防御：目标 parentId 等于自身 id 抛 SKILL_FILE_MOVE_TO_SELF；`isDescendant` 沿目标节点的父链向上遍历（上限节点总数次，防御异常数据成环）发现自身时抛 SKILL_FILE_MOVE_TO_DESCENDANT。
3. 校验目标父目录：根级直接通过；否则必须存在、属于同一 SKILL 且为目录（SKILL_FILE_PARENT_NOT_EXISTS / SKILL_FILE_PARENT_INVALID）。
4. 校验目标目录下同名唯一（用节点当前 name），重复抛 SKILL_FILE_NAME_DUPLICATE。
5. 更新 parentId，调 `skillService.touchSkill` 刷新物化指纹。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_006_000 | 文件或目录不存在 |
| 1_041_006_002 | 同级下已存在同名节点({}) |
| 1_041_006_003 | 父节点必须是同一 SKILL 下的目录 |
| 1_041_006_004 | 固定文件或目录禁止移动 |
| 1_041_006_005 | 不能移入自身 |
| 1_041_006_007 | 不能移入自身的子目录 |
| 1_041_006_008 | 父目录不存在 |

### 3.6 保存 SKILL 文件内容

- **路径**: PUT /ai1/skill/file/update-content
- **权限**: ai1:skill:update
- **说明**: 保存 SKILL 文件内容，目录不支持

**请求参数 (Ai1SkillFileContentReqVO)**: 字段见 [1.5](#15-文件域请求-vo-一览)

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`Ai1SkillFileServiceImpl.updateSkillFileContent`，@Transactional）:
1. 校验节点存在（抛 SKILL_FILE_NOT_EXISTS），且必须为文件类型（`Ai1SkillFileTypeEnum.isFile`），目录抛 SKILL_FILE_NOT_FILE。
2. `updateById` 仅更新 content 字段；内容允许空字符串，@Size 上限 16_777_215 字符（MEDIUMTEXT 量级）。
3. 调 `skillService.touchSkill` 刷新物化指纹。`SKILL.md` 的 frontmatter（name/description）即通过本接口维护，与 [2.2](#22-更新-skill) 的管理字段互相独立。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_006_000 | 文件或目录不存在 |
| 1_041_006_006 | 目录不支持保存内容 |

### 3.7 删除 SKILL 目录或文件

- **路径**: DELETE /ai1/skill/file/delete
- **权限**: ai1:skill:delete
- **说明**: 删除 SKILL 目录或文件，目录递归删除后代

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 节点编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`Ai1SkillFileServiceImpl.deleteSkillFile`，@Transactional）:
1. 校验节点存在（抛 SKILL_FILE_NOT_EXISTS）、非固定节点（locked 抛 SKILL_FILE_LOCKED）。
2. 收集自身及全部后代：`selectListBySkillId` 取该 SKILL 全量节点，构建 parentId → childIds 映射，用 `ArrayDeque` 从自身 id 开始 BFS 逐层向下收集；循环上限 `Short.MAX_VALUE` 次，防御异常数据中的环导致死循环。
3. `deleteByIds` 批量逻辑删除，调 `skillService.touchSkill` 刷新物化指纹。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_006_000 | 文件或目录不存在 |
| 1_041_006_004 | 固定文件或目录禁止删除 |

## 4. 与 harness 的协作：SKILL 物化与工具注入

管理端只维护数据库中的文件树，Agent 对话真正使用 SKILL 依赖 harness 层的 `Ai1SkillToolFactory`（位于 `cn.iocoder.yudao.module.ai1.harness.skill`）。完整链路如下：

### 4.1 指纹与失效机制（touchSkill）

1. 每次内容文件写操作（create/rename/move/update-content/delete）结束后，`Ai1SkillFileServiceImpl` 都回调 `Ai1SkillServiceImpl.touchSkill(skillId)`。
2. `touchSkill` 执行 `skillMapper.updateById(new Ai1SkillDO().setId(id))`——不更新任何业务字段，完全依赖 MyBatis-Plus `MetaObjectHandler`（`DefaultDBFieldHandler`）自动填充 update_time。
3. `ai1_skill.update_time` 的变化即物化指纹的变化源：`Ai1SkillToolFactory.buildFingerprint` 按 id 排序把每个 SKILL 拼成「编号:更新时间」（分号分隔）。

### 4.2 物化流程（Ai1SkillToolFactory.sync）

Agent 发消息生成时（`Ai1SessionStreamTool` → `skillToolFactory.buildTools(agent, shellTracker)`）触发：

1. Agent 未绑定 SKILL（`skillIds` 为空）或绑定的 SKILL 全部查不到 → 返回 null，不提供任何工具（无技能工具也无执行工具）。
2. 计算指纹，与 `Guava Cache<agentId, SkillSnapshot>`（maximumSize=1000）中的快照比对；`isSnapshotValid` 同时校验内存指纹一致，且 `{root}/agent_{agentId}/.fingerprint` 标记文件存在且内容一致（防目录被外部清理），命中即复用。
3. 未命中则进入 `synchronized(syncLocks.computeIfAbsent(agentId))` 双重检查后整目录重建：`FileUtil.del` 清空 → mkdir → 按 id 升序遍历，仅物化 `CommonStatusEnum.isEnable` 的 SKILL（`materializeSkill`：查全树 → `resolveRelativePath` 沿 parentId 自底向上递归拼相对路径、每段 `sanitize` 净化防目录穿越 → 文件 `FileUtil.writeUtf8String` / 目录 `FileUtil.mkdir`）。
4. 含根级 `SKILL.md` 的目录加入 `skillDirectories`，写 `.fingerprint` 后构建 `SkillsTool.builder().addSkillsDirectories(...).build()`；缺 `SKILL.md` 的 SKILL 只物化文件不注册技能（log.warn），全部缺失时 skillsTool 为 null。
5. 构建工具集：`ShellTools`（bash，经 `Ai1SkillShellTracker` 执行）、`FileSystemTools`（Read/Write/Edit）、`GlobTool`、`GrepTool`、`ListDirectoryTool`，后四者的 allowedDirectory/workingDirectory 均限定在 Agent 物化根目录 `{yudao.ai1.skill.root}/agent_{agentId}`。
6. 物化异常时仅 log.warn 并返回旧缓存快照（可能为 null）——**静默降级**，对话继续但没有技能工具，用户侧无报错，需查服务端 warn 日志。

物化目录结构：

```text
${yudao.ai1.skill.root}/            # 默认 {user.home}/yudao-ai1/skills
└── agent_{agentId}/                # Agent 级沙箱（Agent 编号全局唯一，无需按租户分层）
    ├── .fingerprint                # 指纹标记，仅用于本地缓存校验
    └── {skillName}/                # 每个 SKILL 一个子目录（name 即目录名）
        ├── SKILL.md                # 技能入口（缺失则不注册为技能）
        ├── scripts/
        └── reference/
```

### 4.3 Shell 进程回收（Ai1SkillShellTracker）

`ShellTools` 可在服务器执行任意 bash 命令，模块通过装饰器 `Ai1SkillShellTracker`（包装 `LocalExecBackend`，实现 spring-ai-agent-utils 的 `ExecBackend`）追踪本次生成启动的全部后台进程：`start()` 登记 `ExecHandle` 并以"登记后双检 cancelled 立即 kill"堵住竞态窗口；`cancel()` 按"移出集合才认领"逐个 kill（幂等、可并发）。回收时机：生成正常结束（finally）、用户停止（独立 reaper 线程）、节点停机（`Ai1SessionStreamTool.stop()`）。

### 4.4 Agent 删除时的清理

`Ai1AgentServiceImpl.deleteAgentListByIds` 删除 Agent 后逐个调用 `skillToolFactory.evict(agentId)`：失效快照缓存 + `FileUtil.del` 删除本地沙箱目录（清理失败仅 log.warn 不回滚事务）。若此后事务回滚 Agent 仍在，下次对话会因指纹缓存失效自动重建，无功能损伤。

## 5. 错误码汇总

ai1 模块错误码统一使用 1-041-000-000 段（`Ai1ErrorCodeConstants`），skill 域占 005/006 两个子段（相邻 004 为 MCP、007 为 Agent）：

| 错误码 | 常量 | 说明 |
|-------|------|------|
| 1_041_005_000 | SKILL_NOT_EXISTS | SKILL 不存在 |
| 1_041_005_001 | SKILL_USED_BY_AGENT | SKILL 已被 Agent 使用，禁止删除 |
| 1_041_005_002 | SKILL_NAME_DUPLICATE | SKILL 名称({}) 已存在 |
| 1_041_006_000 | SKILL_FILE_NOT_EXISTS | 文件或目录不存在 |
| 1_041_006_001 | SKILL_FILE_NAME_INVALID | 名称格式不合法（不能包含路径分隔符、控制字符，且不能为 . 或 ..） |
| 1_041_006_002 | SKILL_FILE_NAME_DUPLICATE | 同级下已存在同名节点({}) |
| 1_041_006_003 | SKILL_FILE_PARENT_INVALID | 父节点必须是同一 SKILL 下的目录 |
| 1_041_006_004 | SKILL_FILE_LOCKED | 固定文件或目录禁止{操作} |
| 1_041_006_005 | SKILL_FILE_MOVE_TO_SELF | 不能移入自身 |
| 1_041_006_006 | SKILL_FILE_NOT_FILE | 目录不支持保存内容 |
| 1_041_006_007 | SKILL_FILE_MOVE_TO_DESCENDANT | 不能移入自身的子目录 |
| 1_041_006_008 | SKILL_FILE_PARENT_NOT_EXISTS | 父目录不存在 |

## 附注

- **两套独立数据**：`ai1_skill` 表的 name/description 与 `SKILL.md` frontmatter 是两套数据——创建时用管理信息初始化 frontmatter，之后 updateSkill 不回写 SKILL.md；SkillsTool 注册读取的是 SKILL.md frontmatter 而非表字段。
- **指纹覆盖范围**：指纹只含 `id:updateTime`，不校验文件内容；绕过 `Ai1SkillFileService` 直接改库（DBA 操作、其他模块直写 Mapper）不会触发 touchSkill，物化不会重建。所有文件写路径必须走 `Ai1SkillFileService` 并调用 touchSkill。
- **固定节点保护**：SKILL.md、scripts/、reference/ 三条 locked=true 节点在 rename/move/delete 三个入口统一拦截，保证任何技能都有入口文件与约定目录结构；SKILL.md 锁定仅指节点本身（不可删改名移），其内容仍可通过 update-content 编辑。
- **同名 frontmatter 冲突**：多个 SKILL 物化到同一 Agent 目录时按 id 升序固定顺序注册，frontmatter name 相同时由 agent-utils 的首次注册规则决定生效者（后注册者被忽略）。
- **占用校验性能**：Agent 绑定列表存逗号分隔字符串，`FIND_IN_SET` 校验无法走索引，Agent 表大时是删除 SKILL 的慢查询点；绑定关系为软引用，`skill_ids` 中可残留已删 SKILL 的编号（物化时查不到即跳过，不报错）。
- **content 容量**：VO 允许 16_777_215 字符，生产 MySQL 建表 content 列需用 mediumtext（测试 H2 脚本为 text，sql/ 目录目前没有 ai1 模块的生产 DDL）。
- **沙箱安全边界**：执行类工具仅有目录级限定（allowedDirectory/workingDirectory），ShellTools 可执行任意命令，多租户不可信部署需自行评估（源码注释明确提示）。

## 相关文档

- [api-home.md](api-home.md) - 首页统计接口（含 SKILL 数量统计）
- [data-model.md](data-model.md) - 数据模型详情（ai1_skill / ai1_skill_file 表结构与 ER 关系）
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南（工厂 + 指纹缓存、树结构环防御、路径净化等模式与扩展步骤）
- [pitfalls.md](pitfalls.md) - 已知踩坑点（touchSkill 依赖自动填充、物化静默降级、集群共享卷并发等）
