# AI 知识库接口 (AiKnowledgeController / AiKnowledgeDocumentController / AiKnowledgeSegmentController)

> 管理 AI 知识库的基础信息、知识库文档（URL 抓取 + Tika 解析）与文档切片（段落），并提供基于向量库（Embedding + Rerank）的段落检索能力。

## 接口路径前缀

- `/ai/knowledge` (Controller: AiKnowledgeController)
- `/ai/knowledge/document` (Controller: AiKnowledgeDocumentController)
- `/ai/knowledge/segment` (Controller: AiKnowledgeSegmentController)

## 1. 知识库管理（AiKnowledgeController）

### 1.1 获取知识库分页

- **路径**: GET /ai/knowledge/page
- **权限**: ai:knowledge:query
- **说明**: 按名称、状态、创建时间等条件分页查询知识库。

**请求参数 (AiKnowledgePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull（继承 PageParam） | 每页条数 |
| name | String | 否 | 无 | 知识库名称 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 是否启用 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围 |

**响应**: CommonResult&lt;PageResult&lt;AiKnowledgeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 知识库名称 |
| description | String | 知识库描述 |
| embeddingModelId | Long | 向量模型编号 |
| embeddingModel | String | 向量模型标识 |
| topK | Integer | topK |
| similarityThreshold | Double | 相似度阈值 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 `AiKnowledgeMapper.selectPage` 按条件分页查询知识库记录。
2. 将 PageResult&lt;AiKnowledgeDO&gt; 转换为 PageResult&lt;AiKnowledgeRespVO&gt; 返回。

### 1.2 获得知识库

- **路径**: GET /ai/knowledge/get
- **权限**: ai:knowledge:query
- **说明**: 按编号获得知识库详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 知识库编号 |

**响应**: CommonResult&lt;AiKnowledgeRespVO&gt;（字段同 1.1）

**业务逻辑**:
1. 按 ID 查询知识库记录。
2. 转换为 AiKnowledgeRespVO 返回（不存在时返回 null 数据）。

### 1.3 创建知识库

- **路径**: POST /ai/knowledge/create
- **权限**: ai:knowledge:create
- **说明**: 新建知识库，并绑定向量模型。

**请求参数 (AiKnowledgeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号（创建时不传） |
| name | String | 是 | @NotBlank | 知识库名称 |
| description | String | 否 | 无 | 知识库描述 |
| embeddingModelId | Long | 是 | @NotNull | 向量模型编号 |
| topK | Integer | 是 | @NotNull | topK |
| similarityThreshold | Double | 是 | @NotNull | 相似性阈值 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 是否启用 |

**响应**: CommonResult&lt;Long&gt;（知识库编号）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新建知识库的编号 |

**业务逻辑**:
1. 调用 `AiModelService.validateModel` 校验向量模型配置是否存在。
2. 将请求 VO 转换为 AiKnowledgeDO，并写入模型标识 `embeddingModel`。
3. 插入知识库记录，返回新编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在!（模型校验失败等场景） |

### 1.4 更新知识库

- **路径**: PUT /ai/knowledge/update
- **权限**: ai:knowledge:update
- **说明**: 更新知识库基础信息；向量模型变化时触发全量重建索引。

**请求参数 (AiKnowledgeSaveReqVO)**: 同 1.3（id 必传）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验知识库存在（不存在抛 KNOWLEDGE_NOT_EXISTS）。
2. 校验向量模型配置。
3. 更新知识库记录（含 embeddingModel 标识）。
4. 若 embeddingModelId 发生变化，调用 `knowledgeSegmentService.reindexByKnowledgeIdAsync` 异步重建该知识库全部段落的向量索引。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在! |

### 1.5 删除知识库

- **路径**: DELETE /ai/knowledge/delete
- **权限**: ai:knowledge:delete
- **说明**: 删除知识库及其下所有文档与段落（事务内）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 知识库编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验知识库存在。
2. 级联删除该知识库下所有文档及对应段落（`deleteKnowledgeDocumentByKnowledgeId`，含向量清理）。
3. 最后删除知识库记录本身（保证相关配置在删除过程中仍可被找到），整个操作在事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在! |

### 1.6 获得知识库的精简列表

- **路径**: GET /ai/knowledge/simple-list
- **权限**: 已认证（未加 @PreAuthorize）
- **说明**: 获取全部启用状态知识库的下拉精简列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;AiKnowledgeRespVO&gt;&gt;（仅填充 id、name 字段）

**业务逻辑**:
1. 查询状态为启用（CommonStatusEnum.ENABLE）的知识库列表。
2. 转换为仅含 id、name 的精简 RespVO 列表返回。

## 2. 知识库文档（AiKnowledgeDocumentController）

### 2.1 获取文档分页

- **路径**: GET /ai/knowledge/document/page
- **权限**: ai:knowledge:query
- **说明**: 按知识库编号、文档名称分页查询文档。

**请求参数 (AiKnowledgeDocumentPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull（继承 PageParam） | 每页条数 |
| knowledgeId | Long | 否 | 无 | 知识库编号 |
| name | String | 否 | 无 | 文档名称 |

**响应**: CommonResult&lt;PageResult&lt;AiKnowledgeDocumentRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 文档编号 |
| knowledgeId | Long | 知识库编号 |
| name | String | 文档名称 |
| url | String | 文档 URL |
| content | String | 文档内容 |
| contentLength | Integer | 文档内容长度 |
| tokens | Integer | 文档 Token 数量 |
| segmentMaxTokens | Integer | 分片最大 Token 数 |
| retrievalCount | Integer | 召回次数 |
| status | Integer | 文档状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 调用 `AiKnowledgeDocumentMapper.selectPage` 按条件分页查询。
2. 转换为 PageResult&lt;AiKnowledgeDocumentRespVO&gt; 返回。

### 2.2 获取文档详情

- **路径**: GET /ai/knowledge/document/get
- **权限**: ai:knowledge:query
- **说明**: 按编号获取文档详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 文档编号 |

**响应**: CommonResult&lt;AiKnowledgeDocumentRespVO&gt;（字段同 2.1）

**业务逻辑**:
1. 按 ID 查询文档记录。
2. 转换为 AiKnowledgeDocumentRespVO 返回。

### 2.3 新建文档（单个）

- **路径**: POST /ai/knowledge/document/create
- **权限**: ai:knowledge:create
- **说明**: 从 URL 下载并解析文档，入库后异步切片向量化。

**请求参数 (AiKnowledgeDocumentCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| knowledgeId | Long | 是 | @NotNull | 知识库编号 |
| name | String | 是 | @NotBlank | 文档名称 |
| url | String | 否 | @URL | 文档 URL |
| segmentMaxTokens | Integer | 是 | @NotNull | 分段的最大 Token 数 |

**响应**: CommonResult&lt;Long&gt;（文档编号）

**业务逻辑**:
1. 校验知识库存在（KNOWLEDGE_NOT_EXISTS）。
2. 调用 `readUrl`：下载 URL 字节流（失败抛 KNOWLEDGE_DOCUMENT_FILE_DOWNLOAD_FAIL，内容为空抛 KNOWLEDGE_DOCUMENT_FILE_EMPTY），用 Spring AI TikaDocumentReader 解析文本（解析结果为空抛 KNOWLEDGE_DOCUMENT_FILE_READ_FAIL）。
3. 估算 Token 数，插入文档记录（默认启用状态）。
4. 调用 `createKnowledgeSegmentBySplitContentAsync` 异步切片并向量化。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在! |
| 1_040_009_102 | 文档内容为空! |
| 1_040_009_102 | 文件下载失败!（与文档内容为空共用同一码值，见源码） |
| 1_040_009_102 | 文档加载失败!（与文档内容为空共用同一码值，见源码） |

### 2.4 新建文档（多个）

- **路径**: POST /ai/knowledge/document/create-list
- **权限**: ai:knowledge:create
- **说明**: 批量从 URL 创建文档，统一设置 segmentMaxTokens 并异步切片。

**请求参数 (AiKnowledgeDocumentCreateListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| knowledgeId | Long | 是 | @NotNull | 知识库编号 |
| segmentMaxTokens | Integer | 是 | @NotNull | 分段的最大 Token 数（对所有文档生效） |
| list | List&lt;Document&gt; | 是 | @NotEmpty | 文档列表 |
| list[].name | String | 是 | @NotBlank | 文档名称 |
| list[].url | String | 否 | @URL | 文档 URL |

**响应**: CommonResult&lt;List&lt;Long&gt;&gt;（文档编号列表）

**业务逻辑**:
1. 校验知识库存在。
2. 逐个下载并解析所有 URL 的文档内容。
3. 批量插入文档记录（统一 knowledgeId、segmentMaxTokens、启用状态，逐篇估算 Token）。
4. 对每个文档异步执行切片向量化。
5. 返回新建文档编号列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在! |
| 1_040_009_102 | 文档内容为空! |
| 1_040_009_102 | 文件下载失败! |
| 1_040_009_102 | 文档加载失败! |

### 2.5 更新文档

- **路径**: PUT /ai/knowledge/document/update
- **权限**: ai:knowledge:update
- **说明**: 更新文档名称/分片大小；分片大小变化时重建切片。

**请求参数 (AiKnowledgeDocumentUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文档编号 |
| name | String | 否 | 无 | 文档名称 |
| segmentMaxTokens | Integer | 否 | 无 | 分片最大 Token 数 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验文档存在（KNOWLEDGE_DOCUMENT_NOT_EXISTS）。
2. 更新文档记录。
3. 若文档处于启用状态且 segmentMaxTokens 非空且有变化：先删除该文档的全部旧切片，再异步按新分片大小重新切片并向量化。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_101 | 文档不存在! |

### 2.6 更新文档状态

- **路径**: PUT /ai/knowledge/document/update-status
- **权限**: ai:knowledge:update
- **说明**: 启用/禁用文档，并同步增删向量库中的切片。

**请求参数 (AiKnowledgeDocumentUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 文档编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验文档存在。
2. 更新文档状态。
3. 启用：基于文档原内容异步重新切片并向量化；禁用：删除该文档在向量库中的全部切片记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_101 | 文档不存在! |

### 2.7 删除文档

- **路径**: DELETE /ai/knowledge/document/delete
- **权限**: ai:knowledge:delete
- **说明**: 删除文档及其全部切片（事务内）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 文档编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验文档存在。
2. 删除文档记录。
3. 级联删除该文档对应的全部段落（含向量清理），整个操作在事务内执行。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_101 | 文档不存在! |

## 3. 知识库段落/检索（AiKnowledgeSegmentController）

### 3.1 获取段落详情

- **路径**: GET /ai/knowledge/segment/get
- **权限**: ai:knowledge:query
- **说明**: 按编号获取切片段落详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 段落编号 |

**响应**: CommonResult&lt;AiKnowledgeSegmentRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| documentId | Long | 文档编号 |
| knowledgeId | Long | 知识库编号 |
| vectorId | String | 向量库编号 |
| content | String | 切片内容 |
| contentLength | Integer | 切片内容长度 |
| tokens | Integer | Token 数量 |
| retrievalCount | Integer | 召回次数 |
| status | Integer | 文档状态 |
| createTime | Long | 创建时间 |

**业务逻辑**:
1. 按 ID 查询段落记录。
2. 转换为 AiKnowledgeSegmentRespVO 返回。

### 3.2 获取段落分页

- **路径**: GET /ai/knowledge/segment/page
- **权限**: ai:knowledge:query
- **说明**: 按文档编号、内容关键字、状态分页查询段落。

**请求参数 (AiKnowledgeSegmentPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull（继承 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull（继承 PageParam） | 每页条数 |
| documentId | Long | 否 | 无 | 文档编号 |
| content | String | 否 | 无 | 分段内容关键字 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 分段状态 |

**响应**: CommonResult&lt;PageResult&lt;AiKnowledgeSegmentRespVO&gt;&gt;（字段同 3.1）

**业务逻辑**:
1. 调用 `AiKnowledgeSegmentMapper.selectPage` 按条件分页查询。
2. 转换为 PageResult&lt;AiKnowledgeSegmentRespVO&gt; 返回。

### 3.3 创建段落

- **路径**: POST /ai/knowledge/segment/create
- **权限**: ai:knowledge:create
- **说明**: 手工新增切片段落，校验 Token 上限后向量化入库。

**请求参数 (AiKnowledgeSegmentSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号（创建时不传） |
| documentId | Long | 否 | 无 | 知识库文档编号 |
| content | String | 是 | @NotEmpty | 切片内容 |

**响应**: CommonResult&lt;Long&gt;（段落编号）

**业务逻辑**:
1. 校验文档存在（KNOWLEDGE_DOCUMENT_NOT_EXISTS），并获取所属知识库信息（KNOWLEDGE_NOT_EXISTS）。
2. 估算内容 Token 数，若超过文档的 segmentMaxTokens 则抛错。
3. 插入段落记录（默认启用、vectorId 置空、召回次数 0）。
4. 将段落写入向量库（元数据携带 knowledgeId/documentId/segmentId），并回写 vectorId。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_101 | 文档不存在! |
| 1_040_009_202 | 段落不存在! |
| 1_040_009_203 | 内容 Token 数为 {}，超过最大限制 {} |

### 3.4 更新段落内容

- **路径**: PUT /ai/knowledge/segment/update
- **权限**: ai:knowledge:update
- **说明**: 修改切片内容并重新向量化。

**请求参数 (AiKnowledgeSegmentSaveReqVO)**: 同 3.3（id 必传）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验段落存在（KNOWLEDGE_SEGMENT_NOT_EXISTS）。
2. 从向量库删除该段落旧向量，并将 vectorId 置空。
3. 更新段落记录（新内容、长度、Token 数）。
4. 若原状态为启用，则将新内容重新写入向量库并回写 vectorId。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_202 | 段落不存在! |

### 3.5 启禁用段落内容

- **路径**: PUT /ai/knowledge/segment/update-status
- **权限**: ai:knowledge:update
- **说明**: 启用段落时写入向量库，禁用时从向量库移除。

**请求参数 (AiKnowledgeSegmentUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 段落编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 是否启用 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验段落存在。
2. 获取所属知识库对应的 VectorStore 实例。
3. 更新段落状态。
4. 启用：以段落内容构建 Document 写入向量库；禁用：从向量库删除该向量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在! |
| 1_040_009_202 | 段落不存在! |

### 3.6 删除段落

- **路径**: DELETE /ai/knowledge/segment/delete
- **权限**: ai:knowledge:delete
- **说明**: 删除段落记录并同步删除向量。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 段落编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验段落存在。
2. 获取知识库对应 VectorStore，删除该段落的向量（先置空 vectorId 再删除）。
3. 删除段落记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_202 | 段落不存在! |

### 3.7 切片内容（预览）

- **路径**: GET /ai/knowledge/segment/split
- **权限**: ai:knowledge:query
- **说明**: 按 URL 拉取文档并按策略试切分，返回切片预览结果（不入库）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| url | String | 是 | @RequestParam、@URL | 文档 URL |
| segmentMaxTokens | Integer | 是 | @RequestParam | 分段的最大 Token 数 |

**响应**: CommonResult&lt;List&lt;AiKnowledgeSegmentRespVO&gt;&gt;（仅填充 content、contentLength、tokens 等内容字段）

**业务逻辑**:
1. 调用 `readUrl` 下载并用 Tika 解析 URL 文档内容。
2. 自动检测切片策略：Markdown QA 格式（.md 且二级标题数 >= 2 且标题行占比 > 10%）优先，其余 Markdown 文档及默认情况使用语义切分（SEMANTIC），空内容回退 TOKEN 切分。
3. 按策略与 segmentMaxTokens 执行切分（MarkdownQaSplitter / SemanticTextSplitter / TokenTextSplitter）。
4. 过滤空切片，转换为段落 VO 列表返回（不写入数据库与向量库）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_102 | 文档内容为空! |
| 1_040_009_102 | 文件下载失败! |
| 1_040_009_102 | 文档加载失败! |

### 3.8 获取文档处理列表

- **路径**: GET /ai/knowledge/segment/get-process-list
- **权限**: ai:knowledge:query
- **说明**: 统计文档的切片总数与已向量化切片数，用于展示处理进度。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| documentIds | List&lt;Long&gt; | 是 | @RequestParam | 文档编号列表，逗号分隔（如 1,2,3） |

**响应**: CommonResult&lt;List&lt;AiKnowledgeSegmentProcessRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| documentId | Long | 文档编号 |
| count | Long | 总段落数量 |
| embeddingCount | Long | 已向量化段落数量 |

**业务逻辑**:
1. documentIds 为空时直接返回空列表。
2. 调用 `selectProcessList` 按文档分组统计总段落数与已向量化（vectorId 非空）段落数。

### 3.9 搜索段落内容

- **路径**: GET /ai/knowledge/segment/search
- **权限**: ai:knowledge:query
- **说明**: 基于向量检索（可选 Rerank 重排序）在指定知识库内召回相关段落。

**请求参数 (AiKnowledgeSegmentSearchReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| knowledgeId | Long | 是 | @NotNull | 知识库编号 |
| content | String | 是 | @NotEmpty | 检索内容 |
| topK | Integer | 否 | 无 | 最大返回数量（缺省取知识库配置） |
| similarityThreshold | Double | 否 | 无 | 相似度阈值（缺省取知识库配置） |

**响应**: CommonResult&lt;List&lt;AiKnowledgeSegmentSearchRespVO&gt;&gt;（AiKnowledgeSegmentRespVO 全部字段 + 以下扩展字段）

| 字段 | 类型 | 说明 |
|-----|------|------|
| documentName | String | 文档名称 |
| score | Double | 相似度分数（降序排列） |

**业务逻辑**:
1. 校验知识库存在（KNOWLEDGE_NOT_EXISTS）。
2. 向量检索：按 knowledgeId 过滤，topK/相似度阈值缺省时取知识库配置；若启用了 RerankModel，则召回量扩大 4 倍且放开相似度阈值，先粗召回再 Rerank 取 topN 并按阈值过滤。
3. 按 vectorId 召回对应段落记录，并批量累加这些段落的召回次数（retrievalCount）。
4. 将段落与检索得分组装为结果，按相似度分数降序排序。
5. Controller 层批量查询文档 Map，为每条结果补充文档名称 documentName；检索结果为空时直接返回空列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_009_000 | 知识库不存在! |
