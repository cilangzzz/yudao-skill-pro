# AI1 知识库接口 (Ai1KnowledgeBaseController / Ai1KnowledgeDocumentController)

> 管理 AI1 知识库的基础信息（嵌入 Provider / 模型、分片参数）与知识文档（粘贴文本 + `.txt`/`.md` 上传），提供文档向量化（字符级分片 → OpenAI 兼容嵌入 → 写入 Milvus）与向量检索测试能力。向量存储细节全部收口在 harness 层的 `Ai1RagTool`，对话链路中 Agent 绑定的知识库经 Spring AI `QuestionAnswerAdvisor` 自动注入召回上下文。

## 领域概述

- **存储模型**：知识库表 `ai1_knowledge_base` 配置嵌入 Provider/模型与分片参数（`chunkSize`/`chunkOverlap`/`topK`），一个知识库对应一个 Milvus 集合，集合名为 `{collectionPrefix}{知识库编号}`（`collectionPrefix` 默认 `knowledge_base_`，即默认 `knowledge_base_{id}`，由 `yudao.ai1.milvus.*` 配置）。不同知识库可能使用不同嵌入模型（向量维度不同），无法共用集合；按知识库隔离也便于整体删除与迁移。
- **文档模型**：文档表 `ai1_knowledge_document` 以纯文本存储 `content`（MEDIUMTEXT，上限 16777215 字符），手动触发向量化；`status` 由 `Ai1KnowledgeDocumentStatusEnum` 驱动状态机：0=UNPROCESSED 未处理、1=VECTORIZED 已向量化、2=FAILED 失败。
- **租户隔离约定**：Milvus 集合名全局唯一、无租户前缀，租户隔离依赖调用约定——必须先在当前租户下查出知识库 DO（走租户隔离的 DB 查询），再传入 `Ai1RagTool`，保证不会越权读写其他租户的集合。本域所有入口（检索、向量化、删除清理）均遵守该约定。

## 接口路径前缀

- `/ai1/knowledge` (Controller: Ai1KnowledgeBaseController)
- `/ai1/knowledge/document` (Controller: Ai1KnowledgeDocumentController)

## 1. 知识库管理（Ai1KnowledgeBaseController）

### 1.1 创建知识库

- **路径**: POST /ai1/knowledge/create
- **权限**: ai1:knowledge:create
- **说明**: 新建知识库，并绑定嵌入 Provider 与嵌入模型。

**请求参数 (Ai1KnowledgeBaseSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号（创建时不传） |
| name | String | 是 | @NotEmpty、@Size(max=100) | 名称 |
| description | String | 否 | @Size(max=500) | 描述 |
| embeddingProviderId | Long | 是 | @NotNull | 向量化 Provider 编号 |
| embeddingModelId | Long | 是 | @NotNull | 向量化模型编号 |
| chunkSize | Integer | 是 | @NotNull、@Min(100) | 分片大小，单位：字符 |
| chunkOverlap | Integer | 是 | @NotNull、@Min(0) | 分片重叠，单位：字符 |
| topK | Integer | 是 | @NotNull、@Min(1) | 检索数量 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态 |

> VO 上另有 `@AssertTrue` 级校验 `isChunkOverlapValid`：分片重叠必须小于分片大小（`chunkOverlap < chunkSize`）。

**响应**: CommonResult&lt;Long&gt;（新建知识库的编号）

**业务逻辑**:
1. 调用 `Ai1KnowledgeBaseServiceImpl#validateEmbeddingModel` 校验嵌入模型：先经 `Ai1ModelService#getModelRespBO` 校验 Provider / 模型存在且开启、模型归属该 Provider，再用 `Ai1ModelTypeEnum#isEmbedding` 校验为嵌入模型。
2. `BeanUtils.toBean` 转 `Ai1KnowledgeBaseDO` 插入 `ai1_knowledge_base` 表。
3. 返回自增编号 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_000_000 | 供应商不存在 |
| 1_041_000_001 | 供应商({}) 已禁用 |
| 1_041_001_000 | 模型不存在 |
| 1_041_001_001 | 模型({}) 已禁用 |
| 1_041_001_004 | 模型不属于该供应商 |
| 1_041_001_006 | 所选模型不是嵌入模型 |

### 1.2 更新知识库

- **路径**: PUT /ai1/knowledge/update
- **权限**: ai1:knowledge:update
- **说明**: 更新知识库基础信息；嵌入模型变更时失效向量存储缓存，使后续按新模型重建。

**请求参数 (Ai1KnowledgeBaseSaveReqVO)**: 同 1.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验知识库存在（`validateKnowledgeBaseExists`，不存在抛 KNOWLEDGE_BASE_NOT_EXISTS）。
2. 校验嵌入模型（同 1.1）。
3. `knowledgeBaseMapper.updateById` 更新记录。
4. 若 `embeddingProviderId` 或 `embeddingModelId` 变更，调用 `Ai1RagTool#evict(id)` 失效该知识库的向量存储缓存，使后续请求按新嵌入模型重建向量存储。注意：evict 只作用于当前节点；多节点部署下，其他节点依赖缓存中记录的 `EmbeddingModel` 实例引用不一致而自然重建。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_002_000 | 知识库不存在 |
| 1_041_001_006 | 所选模型不是嵌入模型（及 1.1 中模型校验相关错误码） |

### 1.3 删除知识库

- **路径**: DELETE /ai1/knowledge/delete
- **权限**: ai1:knowledge:delete
- **说明**: 删除知识库，连带删除其下文档与 Milvus 向量集合。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 知识库编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 委托 `deleteKnowledgeBaseListByIds(Collections.singletonList(id))`，完整链路见 3.4（事务内校验 + 删库删文档，事务提交后删除向量集合）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_002_000 | 知识库不存在 |
| 1_041_002_003 | 知识库已被 Agent 使用，禁止删除 |

### 1.4 批量删除知识库

- **路径**: DELETE /ai1/knowledge/delete-list
- **权限**: ai1:knowledge:delete
- **说明**: 批量删除知识库，连带删除文档与向量集合。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam | 知识库编号列表，逗号分隔（如 1,2,3） |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 同 1.3（走 `deleteKnowledgeBaseListByIds(List<Long> ids)` 批量版本：校验存在与 Agent 绑定 → 删库删文档 → 事务提交后逐个 `dropCollection`）。

**错误码**: 同 1.3。

### 1.5 获得知识库

- **路径**: GET /ai1/knowledge/get
- **权限**: ai1:knowledge:query
- **说明**: 按编号获得知识库详情，拼接 Provider / 模型名称。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 知识库编号 |

**响应**: CommonResult&lt;Ai1KnowledgeBaseRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名称 |
| description | String | 描述 |
| embeddingProviderId | Long | 向量化 Provider 编号 |
| embeddingProviderName | String | 向量化 Provider 名称（拼接） |
| embeddingModelId | Long | 向量化模型编号 |
| embeddingModelName | String | 向量化模型名称（拼接） |
| chunkSize | Integer | 分片大小，单位：字符 |
| chunkOverlap | Integer | 分片重叠，单位：字符 |
| topK | Integer | 检索数量 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. `knowledgeBaseService.getKnowledgeBase(id)` 查询记录。
2. 由私有 `buildKnowledgeBaseRespVOList` 拼接关联名称：`providerService.getProviderMap` / `modelService.getModelMap` 补 `embeddingProviderName`、`embeddingModelName`（`MapUtils.findAndThen`）。

### 1.6 获得知识库分页

- **路径**: GET /ai1/knowledge/page
- **权限**: ai1:knowledge:query
- **说明**: 按名称、状态分页查询知识库，拼接 Provider / 模型名称。

**请求参数 (Ai1KnowledgeBasePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull（继承 PageParam） | 每页条数 |
| name | String | 否 | 无 | 名称，模糊匹配 |
| status | Integer | 否 | 无 | 状态 |

**响应**: CommonResult&lt;PageResult&lt;Ai1KnowledgeBaseRespVO&gt;&gt;（字段同 1.5）

**业务逻辑**:
1. `Ai1KnowledgeBaseMapper#selectPage`：`name` likeIfPresent 模糊、`status` eqIfPresent、`orderByAsc(id)`。
2. 分页结果同样经 `buildKnowledgeBaseRespVOList` 拼接 Provider / 模型名称。

### 1.7 获得知识库精简列表

- **路径**: GET /ai1/knowledge/simple-list
- **权限**: 已认证（未加 @PreAuthorize）
- **说明**: 只包含开启状态的知识库，用于 Agent 绑定知识库的下拉选择。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;Ai1KnowledgeBaseRespVO&gt;&gt;（仅填充 id、name 两个字段）

**业务逻辑**:
1. `getKnowledgeBaseListByStatus(CommonStatusEnum.ENABLE.getStatus())` 查询全部启用知识库。
2. `convertList` 只回填 id + name 两个字段返回。

### 1.8 知识库检索测试

- **路径**: GET /ai1/knowledge/search
- **权限**: ai1:knowledge:search
- **说明**: 在指定知识库内做向量相似度检索，用于检索效果测试（与对话 RAG 共用同一 `Ai1RagTool#search` 通道）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 知识库编号 |
| query | String | 是 | @RequestParam、@NotEmpty | 查询文本 |
| topK | Integer | 否 | 无 | 检索数量，为空时使用知识库配置 |

**响应**: CommonResult&lt;List&lt;Ai1KnowledgeSearchRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| text | String | 命中分片文本 |
| documentId | Long | 文档编号 |
| documentName | String | 文档名称（Controller 拼接） |
| chunkIndex | Integer | 分片序号 |
| score | Double | 相似度得分（空值默认 0） |

**业务逻辑**:
1. `Ai1KnowledgeBaseServiceImpl#searchKnowledgeBase` 先 `validateKnowledgeBaseExists` —— 走租户隔离的 DB 查询确认知识库属于当前租户，作为租户隔离屏障（防止跨租户访问向量集合）。
2. 委托 `Ai1RagTool#search` 相似度检索，完整链路见 3.3。
3. 异常处理：`ServiceException`（如模型被禁用、所选模型不是嵌入模型）原样抛出；其余异常包装为 KNOWLEDGE_BASE_SEARCH_FAIL（消息格式化原始异常内容）。
4. Controller 层 `buildKnowledgeSearchRespVOList` 按 documentId 批量查询文档 Map（`knowledgeDocumentService.getKnowledgeDocumentMap`），为每条结果补充 documentName。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_002_000 | 知识库不存在 |
| 1_041_002_002 | 向量检索失败：{} |
| 1_041_001_006 | 所选模型不是嵌入模型（模型禁用等场景，见 1.1） |

## 2. 知识文档管理（Ai1KnowledgeDocumentController）

### 2.1 创建文档（粘贴文本）

- **路径**: POST /ai1/knowledge/document/create
- **权限**: ai1:knowledge-document:create
- **说明**: 以粘贴的纯文本内容创建文档，初始为未处理状态，需手动向量化。

**请求参数 (Ai1KnowledgeDocumentSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号（创建时不传） |
| knowledgeBaseId | Long | 是 | @NotNull | 知识库编号（修改时不允许变更） |
| name | String | 是 | @NotEmpty、@Size(max=255) | 文档名称 |
| content | String | 是 | @NotEmpty、@Size(max=16777215) | 文档内容（对应 DB MEDIUMTEXT 上限） |

**响应**: CommonResult&lt;Long&gt;（文档编号）

**业务逻辑**:
1. `knowledgeBaseService.validateKnowledgeBaseExists` 校验知识库存在。
2. 插入 `ai1_knowledge_document`：初始 `chunkCount=0`、`status=UNPROCESSED`（`Ai1KnowledgeDocumentStatusEnum`），需手动向量化。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_002_000 | 知识库不存在 |

### 2.2 上传文档

- **路径**: POST /ai1/knowledge/document/upload
- **权限**: ai1:knowledge-document:create
- **说明**: 上传 `.txt` / `.md` 文本文件，读取内容后入库（同样需手动向量化）。

**请求参数**: 无（form-data）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| knowledgeBaseId | Long | 是 | @RequestParam | 知识库编号 |
| file | MultipartFile | 是 | @RequestParam | 文本文件（仅 .txt / .md） |

**响应**: CommonResult&lt;Long&gt;（文档编号）

**业务逻辑** (`uploadKnowledgeDocument`):
1. 校验文件名后缀在 `UPLOAD_FILE_SUFFIXES`（`.txt`、`.md`）内，否则抛 KNOWLEDGE_DOCUMENT_FILE_TYPE_INVALID。
2. `IoUtil.readUtf8` 按 UTF-8 读取文件内容，失败抛 KNOWLEDGE_DOCUMENT_FILE_READ_FAIL。注意：GBK 等编码的文件会得到乱码内容但不报错，随后被正常入库。
3. 内容为空抛 KNOWLEDGE_DOCUMENT_FILE_EMPTY。
4. 组装 `Ai1KnowledgeDocumentSaveReqVO`（name 取上传文件名）复用 `createKnowledgeDocument` 入库。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_003_002 | 仅支持 .txt / .md 文本文件 |
| 1_041_003_003 | 文件内容为空 |
| 1_041_003_004 | 文件读取失败：{} |
| 1_041_002_000 | 知识库不存在（复用创建逻辑） |

### 2.3 更新文档

- **路径**: PUT /ai1/knowledge/document/update
- **权限**: ai1:knowledge-document:update
- **说明**: 更新文档名称与内容；归属知识库不可变更，内容变更后需重新向量化。

**请求参数 (Ai1KnowledgeDocumentSaveReqVO)**: 同 2.1（id 必传；`knowledgeBaseId` 校验必填但更新时被忽略）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑** (`updateKnowledgeDocument`):
1. `validateKnowledgeDocumentExists` 校验文档存在。
2. 更新对象只含 id、name、content —— 不含 `knowledgeBaseId`，归属知识库不可变更。
3. `ObjUtil.notEqual` 比较内容，变更时置 `chunkCount=0` + `status=UNPROCESSED`（需重新向量化），并按文档所属知识库调用 `Ai1RagTool#deleteByDocumentIds` 清理旧向量（该清理失败仅 log.warn，不影响 DB 更新，最终一致性依赖下次向量化时"先删后写"）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_003_000 | 文档不存在 |

### 2.4 删除文档

- **路径**: DELETE /ai1/knowledge/document/delete
- **权限**: ai1:knowledge-document:delete
- **说明**: 删除文档记录，并按所属知识库清理向量。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 文档编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 委托 `deleteKnowledgeDocumentListByIds(singletonList(id))`：逐个校验存在 → `deleteByIds` 删记录 → `convertMultiMap` 按知识库分组 → 逐知识库调用 `Ai1RagTool#deleteByDocumentIds` 清理向量（失败仅 log.warn）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_003_000 | 文档不存在 |

### 2.5 批量删除文档

- **路径**: DELETE /ai1/knowledge/document/delete-list
- **权限**: ai1:knowledge-document:delete
- **说明**: 批量删除文档，按知识库分组清理向量。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam | 文档编号列表，逗号分隔（如 1,2,3） |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: 同 2.4 的批量版本（`deleteKnowledgeDocumentListByIds(List<Long> ids)`：校验存在并收集文档 → 批量删 DB → 按知识库分组调 `Ai1RagTool#deleteByDocumentIds`）。

**错误码**: 同 2.4。

### 2.6 获得文档

- **路径**: GET /ai1/knowledge/document/get
- **权限**: ai1:knowledge-document:query
- **说明**: 按编号获取文档详情，包含完整内容（编辑时由此接口加载）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 文档编号 |

**响应**: CommonResult&lt;Ai1KnowledgeDocumentRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文档编号 |
| knowledgeBaseId | Long | 知识库编号 |
| name | String | 文档名称 |
| content | String | 文档内容（分页列表不返回） |
| contentLength | Integer | 内容长度，单位：字符 |
| chunkCount | Integer | 分片数量 |
| status | Integer | 向量化状态（0 未处理 / 1 已向量化 / 2 失败） |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. `getKnowledgeDocument(id)` 查询记录。
2. `BeanUtils.toBean` 转换后，用 `StrUtil.length` 计算并回填 `contentLength`。

### 2.7 获得文档分页

- **路径**: GET /ai1/knowledge/document/page
- **权限**: ai1:knowledge-document:query
- **说明**: 按知识库分页查询文档，不返回文档内容（避免大字段传输）。

**请求参数 (Ai1KnowledgeDocumentPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull（继承 PageParam） | 每页条数 |
| knowledgeBaseId | Long | 是 | @NotNull | 知识库编号 |
| name | String | 否 | 无 | 名称，模糊匹配 |
| status | Integer | 否 | 无 | 向量化状态（0/1/2） |

**响应**: CommonResult&lt;PageResult&lt;Ai1KnowledgeDocumentRespVO&gt;&gt;（字段同 2.6，content 置 null）

**业务逻辑**:
1. `Ai1KnowledgeDocumentMapper#selectPage`：`knowledgeBaseId` 必填 eq、`name` likeIfPresent、`status` eqIfPresent、`orderByAsc(id)`。
2. 分页结果把 `content` 置 null，仅保留 `contentLength`，避免大字段传输。

### 2.8 文档向量化

- **路径**: POST /ai1/knowledge/document/vectorize
- **权限**: ai1:knowledge-document:vectorize
- **说明**: 对单个文档执行分片 → 嵌入 → 写入 Milvus，返回分片数量。同步阻塞调用（HTTP 请求线程内完成嵌入 API 调用与向量写入）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 文档编号 |

**响应**: CommonResult&lt;Integer&gt;（分片数量）

**业务逻辑** (`vectorizeKnowledgeDocument(id)`):
1. 校验文档存在（KNOWLEDGE_DOCUMENT_NOT_EXISTS），并经 `knowledgeBaseService.validateKnowledgeBaseExists` 校验所属知识库存在。
2. 文档内容为空抛 KNOWLEDGE_DOCUMENT_CONTENT_EMPTY。
3. 调用 `Ai1RagTool#vectorize`（完整链路见 3.1）：分片 → 嵌入 → 先清旧向量再写 Milvus，返回分片数。
4. 成功回写 `chunkCount` + `status=VECTORIZED`；任何异常回写 `status=FAILED`，`ServiceException` 透传、其余异常包装为 KNOWLEDGE_DOCUMENT_VECTORIZE_FAIL 后抛出。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_003_000 | 文档不存在 |
| 1_041_002_000 | 知识库不存在 |
| 1_041_003_001 | 文档内容为空，无法向量化 |
| 1_041_003_005 | 向量化失败：{} |
| 1_041_001_006 | 所选模型不是嵌入模型（向量存储构建时校验） |

### 2.9 知识库批量向量化

- **路径**: POST /ai1/knowledge/document/vectorize-all
- **权限**: ai1:knowledge-document:vectorize
- **说明**: 对知识库下全部文档逐个向量化，返回成功 / 失败数量。逐文档串行执行，嵌入服务限速时接口耗时线性增长。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| knowledgeBaseId | Long | 是 | @RequestParam | 知识库编号 |

**响应**: CommonResult&lt;Ai1KnowledgeDocumentVectorizeRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| successCount | Integer | 成功数量 |
| failureCount | Integer | 失败数量 |

**业务逻辑** (`vectorizeKnowledgeDocumentListByKnowledgeBaseId`):
1. 校验知识库存在，且其下有文档（否则抛 KNOWLEDGE_BASE_DOCUMENT_EMPTY）。
2. 预检嵌入模型类型：`modelService.getModelRespBO` + `Ai1ModelTypeEnum.isEmbedding`，非嵌入模型直接抛 MODEL_TYPE_NOT_EMBEDDING —— 避免逐篇失败把整库文档刷成 FAILED 状态。
3. for 循环逐个向量化：跳过空内容文档；单个失败 catch（log.warn）不中断，继续下一篇。
4. 返回 `Ai1KnowledgeDocumentVectorizeRespVO(successCount, failureCount)`。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_041_002_000 | 知识库不存在 |
| 1_041_002_001 | 知识库下暂无文档 |
| 1_041_001_006 | 所选模型不是嵌入模型 |

## 3. 与 Harness（Ai1RagTool）的协作链路

`Ai1RagTool` 收口了向量库建集合、分片、嵌入、写入、检索、清理全部细节，被 `Ai1KnowledgeBaseServiceImpl`、`Ai1KnowledgeDocumentServiceImpl` 与会话编排（`Ai1SessionStreamTool`）三方复用。调用方只传当前租户下查出的 `Ai1KnowledgeBaseDO`，由工具类保证租户隔离。

### 3.1 文档向量化链路

1. `Ai1KnowledgeDocumentServiceImpl#vectorizeKnowledgeDocument(id)` 校验文档与所属知识库存在后，进入私有重载 `vectorizeKnowledgeDocument(knowledgeBase, document)`。
2. `Ai1RagTool#vectorize(knowledgeBase, documentId, content)`：
   - **分片**：`split(content, chunkSize, chunkOverlap)` 字符级滑动窗口分片；overlap 被钳制在 `[0, chunkSize-1]`（VO 层虽有 `@AssertTrue` 校验 `chunkOverlap < chunkSize`，工具层不信任入参自保），保证分片循环每轮必定前进。
   - **向量存储**：`getOrCreateVectorStore(knowledgeBase)`，见 3.2。
   - **清旧写新**：`vectorStore.delete(documentId eq)` 先清理该文档旧向量（支持重复向量化），再为每个分片构造 Spring AI `Document(text, metadata{documentId, chunkIndex})`，`vectorStore.add` 批量写入。
3. 返回分片数 → Service 回写 `chunkCount` + `status=VECTORIZED`；任何异常回写 `status=FAILED` 并抛 ServiceException。

### 3.2 向量存储的构建与缓存

1. **解析嵌入模型**：`modelService.getModelRespBO(providerId, modelId)` 校验 Provider / 模型存在且开启、归属正确，`Ai1ModelTypeEnum.isEmbedding` 校验类型 → `llmModelFactory.getOrCreateEmbeddingModel(model)` 构建兼容 OpenAI 协议的 `EmbeddingModel` 实例。
2. **缓存命中判断**：Guava 缓存 `Cache<Long, CachedVectorStore>`（maximumSize=128）命中、且缓存记录的 `EmbeddingModel` 实例与当前相同（`==` 实例比较）时直接复用。模型配置变更后 `Ai1LlmModelFactory` 重建实例，缓存随之自动失效重建；`evict(id)` 仅作为本节点主动失效的补充手段。
3. **构建**：未命中时按知识库锁（`ConcurrentHashMap#computeIfAbsent` 取锁对象 + synchronized 双重检查）串行构建 `MilvusVectorStore`：database 取 `yudao.ai1.milvus.database`、collectionName 为 `{collectionPrefix}{id}`、`MetricType.COSINE` + `IndexType.FLAT` + `initializeSchema(true)`。手动构建的实例不触发 Spring 生命周期回调，必须显式调用 `afterPropertiesSet()` 完成建集合、建索引、加载，否则首次写入/检索报集合不存在；初始化失败包装为 IllegalStateException。

### 3.3 检索测试链路

1. Service 先在当前租户下查出知识库 DO（租户隔离屏障）。
2. `getOrCreateVectorStore` → `MilvusVectorStore.similaritySearch(SearchRequest)`：topK 取入参 topK（大于 0 时）→ 知识库 `topK` 配置 → `yudao.ai1.milvus.default-top-k`（默认 5）。
3. 从向量元数据还原 `documentId` / `chunkIndex`，`score` 空值默认 0。
4. Controller 层按 documentId 批量补 documentName 后返回。

### 3.4 知识库删除链路（事务 + 事务提交后补偿）

1. `@Transactional(rollbackFor = Exception.class)` 事务内：
   - 逐个 `validateKnowledgeBaseExists` 校验存在；
   - `agentService.getAgentCountByKnowledgeBaseIds(ids) > 0` 时抛 KNOWLEDGE_BASE_USED_BY_AGENT（Agent 表的 `knowledgeBaseIds` 为逗号分隔字符串存储（LongListTypeHandler 映射 varchar，如 1,2,3），删除防护经 Ai1AgentMapper#selectCountByKnowledgeBaseIds 用 MyBatisUtils#findInSet 生成 FIND_IN_SET 条件，按编号逐个精确匹配计数）；
   - `knowledgeBaseMapper.deleteByIds(ids)` 删知识库 + `knowledgeDocumentService.deleteKnowledgeDocumentListByKnowledgeBaseIds(ids)` 删除其下文档（仅删 DB，不逐条清向量）。
2. `TransactionSynchronizationManager.registerSynchronization` 注册 `afterCommit` 回调：事务提交后逐个 `ragTool.dropCollection` —— 先 evict 本节点缓存，再用全局单例 Milvus 客户端按 database + collectionName `dropCollection`，失败仅 log.warn。
3. 原因：Milvus 是外部资源无法参与 DB 事务回滚，故放在事务提交后执行；若提交后应用崩溃或 Milvus 不可用，会遗留孤儿向量集合（需人工清理）。

### 3.5 对话 RAG 注入（跨域：会话域）

Agent 会话发消息时（`Ai1SessionStreamTool.generate`，经 Redis Stream 任务队列 + SSE 的异步链路，详见 api-session.md）：

1. 按 `agent.knowledgeBaseIds`（逗号分隔字符串存储）调用 `knowledgeBaseService.getKnowledgeBaseList(ids)` 在当前租户下查出知识库 DO，过滤 `CommonStatusEnum` 禁用库。
2. 对每个可用库调用 `ragTool.buildAdvisor(knowledgeBase)`：`getOrCreateVectorStore` + `QuestionAnswerAdvisor.builder(vectorStore).searchRequest(topK=知识库配置或 default-top-k).build()`；单库装配失败降级跳过，并在思考流写入「知识库降级」提示。
3. Advisor 随 ChatClient 流式请求发出，在请求前自动用用户问题检索向量库，把命中分片注入 prompt。

## 附：本域错误码汇总（Ai1ErrorCodeConstants，1-041 段）

**知识库段 1-041-002-000**

| 错误码 | 常量 | 说明 |
|-------|------|------|
| 1_041_002_000 | KNOWLEDGE_BASE_NOT_EXISTS | 知识库不存在 |
| 1_041_002_001 | KNOWLEDGE_BASE_DOCUMENT_EMPTY | 知识库下暂无文档 |
| 1_041_002_002 | KNOWLEDGE_BASE_SEARCH_FAIL | 向量检索失败：{} |
| 1_041_002_003 | KNOWLEDGE_BASE_USED_BY_AGENT | 知识库已被 Agent 使用，禁止删除 |

**知识文档段 1-041-003-000**

| 错误码 | 常量 | 说明 |
|-------|------|------|
| 1_041_003_000 | KNOWLEDGE_DOCUMENT_NOT_EXISTS | 文档不存在 |
| 1_041_003_001 | KNOWLEDGE_DOCUMENT_CONTENT_EMPTY | 文档内容为空，无法向量化 |
| 1_041_003_002 | KNOWLEDGE_DOCUMENT_FILE_TYPE_INVALID | 仅支持 .txt / .md 文本文件 |
| 1_041_003_003 | KNOWLEDGE_DOCUMENT_FILE_EMPTY | 文件内容为空 |
| 1_041_003_004 | KNOWLEDGE_DOCUMENT_FILE_READ_FAIL | 文件读取失败：{} |
| 1_041_003_005 | KNOWLEDGE_DOCUMENT_VECTORIZE_FAIL | 向量化失败：{} |

**跨域引用（模型段 1-041-001-000）**

| 错误码 | 常量 | 说明 | 触发场景 |
|-------|------|------|---------|
| 1_041_001_006 | MODEL_TYPE_NOT_EMBEDDING | 所选模型不是嵌入模型 | 创建/更新知识库、批量向量化预检、向量存储构建 |
| 1_041_001_008 | MODEL_USED_BY_KNOWLEDGE_BASE | 模型已被知识库使用，禁止删除 | 模型删除防护（模型域反向校验本域） |
| 1_041_001_010 | MODEL_TYPE_USED_BY_KNOWLEDGE_BASE | 模型已被知识库使用，禁止修改类型 | 模型改类型防护（模型域反向校验本域） |

## 相关文档

- [README.md](README.md) — ai1 模块总览与文档索引
- [api-model.md](api-model.md) — 供应商与模型域（嵌入模型配置，模型删除 / 改类型对本域的反向防护）
- [api-agent.md](api-agent.md) — Agent 域（绑定知识库下拉、知识库删除防护的来源）
- [api-session.md](api-session.md) — 会话域（对话 RAG 注入完整链路）
- [data-model.md](data-model.md) — `ai1_knowledge_base` / `ai1_knowledge_document` 表结构与 ER 关系
- [code-patterns.md](code-patterns.md) — 知识库三层 CRUD、Harness 工具收口、缓存 + 实例身份失效等代码模式
- [pitfalls.md](pitfalls.md) — 孤儿向量集合、UTF-8 编码乱码、向量存储缓存跨节点失效等踩坑点
