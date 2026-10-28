# 数据模型详情

> ai1 模块的核心数据模型，包括 DO、Mapper 及其之间的关系。

## 1. 实体继承体系

ai1 模块全部 11 个 DO 位于 `cn.iocoder.yudao.module.ai1.dal.dataobject` 下，按业务域分为 agent / knowledge / mcp / memory / model / session / skill 七个包，**全部直接继承框架的 TenantBaseDO（多租户基类），无一只用 BaseDO**：

```text
Serializable + TransPojo（Easy-Trans 数据翻译接口）
│
└── BaseDO（yudao-spring-boot-starter-mybatis，cn.iocoder.yudao.framework.mybatis.core.dataobject）
    ├── creator      String          创建者，SysUser 的 userId（INSERT 自动填充）
    ├── createTime   LocalDateTime   创建时间（INSERT 自动填充）
    ├── updater      String          更新者（INSERT_UPDATE 自动填充）
    ├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 自动填充）
    ├── deleted      Boolean         逻辑删除标记（@TableLogic，查询自动过滤已删除数据）
    │
    └── TenantBaseDO（yudao-spring-boot-starter-biz-tenant，cn.iocoder.yudao.framework.tenant.core.db）
        ├── tenantId  Long            多租户编号
        │
        ├── Ai1AgentDO               （ai1_agent，@TableName(autoResultMap = true)）
        ├── Ai1ProviderDO            （ai1_provider，@TableName(autoResultMap = true)）
        ├── Ai1ModelDO               （ai1_model）
        ├── Ai1KnowledgeBaseDO       （ai1_knowledge_base）
        ├── Ai1KnowledgeDocumentDO   （ai1_knowledge_document）
        ├── Ai1SessionDO             （ai1_session）
        ├── Ai1SessionMessageDO      （ai1_session_message）
        ├── Ai1MemoryDO              （ai1_memory）
        ├── Ai1McpDO                 （ai1_mcp，@TableName(autoResultMap = true)）
        ├── Ai1SkillDO               （ai1_skill）
        └── Ai1SkillFileDO           （ai1_skill_file）
```

使用规则：

- ai1 模块所有 DO 均继承 TenantBaseDO，11 张业务表 100% 带 `tenant_id` 字段，全部走多租户隔离（与旧 ai 模块全部继承 BaseDO、平台级共享的设计相反）。
- 配置类数据（Provider / Model / MCP / SKILL）与用户数据（Agent / 知识库 / 会话 / 记忆）均在租户内隔离；用户归属类数据（会话、记忆）另通过 `userId` 字段关联到管理后台用户。
- BaseDO 的四个审计字段由 MyBatis-Plus 的 `MetaObjectHandler` 自动填充，业务代码不要手工赋值；`deleted` 走逻辑删除，统计 SQL（如 `Ai1HomeMapper`）中显式使用 `deleted = FALSE` 过滤。
- 所有 DO 均标注 `@KeySequence`（如 `ai1_agent_seq`），供 Oracle / PostgreSQL / Kingbase / DB2 / H2 主键自增使用，MySQL 不受影响。
- Redis 侧的任务队列 / 结果流 KEY 不带 tenantId，由任务字段 tenantId 或调用前按租户、用户校验归属来还原上下文（见「其他持久化结构」一节）。

## 2. 核心 DO 实体

> 索引说明（本节通用）：仓库 `sql/` 目录没有任何 ai1 模块的建表语句，模块自身也没有 `src/main/resources` 目录与 Mapper XML，下文表结构与列名由 DO 源码（MyBatis-Plus 驼峰转下划线映射）反推。DO 代码中只显式声明了主键 `@TableId`（非 MySQL 数据库通过 `@KeySequence` 走对应序列，如 `ai1_agent_seq`），因此「索引」一栏仅列出代码中可确认的约束，不编造数据库二级索引。

### 2.1 模型配置聚合（模型接入的基石）

#### Ai1ProviderDO (ai1_provider)

AI1 供应商：模型提供方（OpenAI 兼容端点），维护接口地址 baseUrl 与 API 密钥 apiKey。`headers` 支持自定义请求头，value 可含 `{session}` 占位符在请求时替换为会话编号。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 名称 |
| baseUrl | String | base_url | 接口地址（OpenAI 兼容端点） |
| apiKey | String | api_key | API 密钥 |
| headers | Map\<String, String\> | headers | 请求 Header，`JacksonTypeHandler` 存 JSON 对象，格式 `{"X-Session":"{session}"}`；value 可包含 `{session}` 占位符，请求时替换为会话编号 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum`（0 开启、1 关闭） |
| remark | String | remark | 备注 |

**继承**: TenantBaseDO
**索引**: 主键 id；代码与仓库 SQL 均未声明其他索引

#### Ai1ModelDO (ai1_model)

AI1 模型定义：挂在某个供应商（providerId）之下，是 Agent 对话 / 知识库向量化所使用的模型元数据，类型分对话（0）与嵌入（1）两种。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| providerId | Long | provider_id | 供应商编号，关联 `Ai1ProviderDO.id` |
| name | String | name | 展示名称 |
| model | String | model | 模型标识，例如说 `gpt-4o`、`deepseek-chat` |
| type | Integer | type | 类型，枚举 `Ai1ModelTypeEnum`：0 对话、1 嵌入 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

### 2.2 Agent 聚合（智能体编排的核心）

#### Ai1AgentDO (ai1_agent)

AI1 Agent（智能体）：名称 / 介绍 + 对话模型（providerId + modelId）+ 系统指令 + 知识库 / MCP / SKILL 三组逻辑多对多引用 + 长期记忆开关。`status` 开启后才可在「Agent 会话」中使用。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 名称 |
| introduction | String | introduction | 介绍 |
| providerId | Long | provider_id | 模型所属 Provider 编号，关联 `Ai1ProviderDO.id` |
| modelId | Long | model_id | 对话模型编号，关联 `Ai1ModelDO.id` |
| systemPrompt | String | system_prompt | 系统指令 |
| knowledgeBaseIds | List\<Long\> | knowledge_base_ids | 知识库编号集合，`LongListTypeHandler` 存逗号分隔字符串，逻辑关联 `Ai1KnowledgeBaseDO.id`；Mapper 用 FIND_IN_SET 查询 |
| mcpIds | List\<Long\> | mcp_ids | MCP 编号集合，`LongListTypeHandler` 存逗号分隔字符串，逻辑关联 `Ai1McpDO.id` |
| skillIds | List\<Long\> | skill_ids | SKILL 编号集合，`LongListTypeHandler` 存逗号分隔字符串，逻辑关联 `Ai1SkillDO.id` |
| memoryEnabled | Boolean | memory_enabled | 是否开启长期记忆；开启后对话时注入记忆，并由 Job 归档已完成的消息 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum`；开启后才可在「Agent 会话」中使用 |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

### 2.3 知识库聚合（RAG）

#### Ai1KnowledgeBaseDO (ai1_knowledge_base)

AI1 知识库：分片参数（chunkSize / chunkOverlap）+ 检索参数（topK）+ 嵌入模型配置（embeddingProviderId + embeddingModelId）。向量本身存储在 Milvus 集合 `{collectionPrefix}{id}`（`yudao.ai1.milvus.collection-prefix`，默认 `knowledge_base_{id}`），按知识库隔离，不落 MySQL。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增；同时是 Milvus 集合名后缀） |
| name | String | name | 名称 |
| description | String | description | 描述 |
| embeddingProviderId | Long | embedding_provider_id | 向量化 Provider 编号，关联 `Ai1ProviderDO.id` |
| embeddingModelId | Long | embedding_model_id | 向量化模型编号，关联 `Ai1ModelDO.id`（嵌入类型） |
| chunkSize | Integer | chunk_size | 分片大小，单位：字符 |
| chunkOverlap | Integer | chunk_overlap | 分片重叠，单位：字符 |
| topK | Integer | top_k | 检索数量 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

#### Ai1KnowledgeDocumentDO (ai1_knowledge_document)

AI1 知识库-文档：文档原文 content 直接存 MySQL，向量化状态由 `Ai1KnowledgeDocumentStatusEnum` 标记（0 未处理、1 已向量化、2 失败），分片向量落在对应知识库的 Milvus 集合中。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| knowledgeBaseId | Long | knowledge_base_id | 知识库编号，关联 `Ai1KnowledgeBaseDO.id` |
| name | String | name | 名称 |
| content | String | content | 内容（文档原文） |
| chunkCount | Integer | chunk_count | 分片数量 |
| status | Integer | status | 向量化状态，枚举 `Ai1KnowledgeDocumentStatusEnum`：0 未处理、1 已向量化、2 失败 |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

### 2.4 会话聚合（Agent 对话的载体）

#### Ai1SessionDO (ai1_session)

AI1 会话：管理后台登录用户与 Agent 的一次会话。仅 4 个业务字段，标题默认 `TITLE_DEFAULT = "新会话"`，首条消息发送后自动替换为提问内容，超出 `TITLE_MAX_LENGTH = 50` 截断。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| agentId | Long | agent_id | Agent 编号，关联 `Ai1AgentDO.id` |
| userId | Long | user_id | 用户编号，关联 system 模块 AdminUserDO.id |
| title | String | title | 标题；默认 `TITLE_DEFAULT = "新会话"`，首条提问后替换并按 `TITLE_MAX_LENGTH = 50` 截断 |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

#### Ai1SessionMessageDO (ai1_session_message)

AI1 会话消息：用户 / 助手两类角色（role 为字符串）。助手消息先以 GENERATING 状态占位（编号同时作为 Redis 结果流标识，用于断线续传），生成结束回填 reasoning / content 与终态。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增）；助手消息的编号同时作为 Redis 结果流标识 `ai1:session:result:{messageId}` |
| sessionId | Long | session_id | 会话编号，关联 `Ai1SessionDO.id` |
| role | String | role | 角色，枚举 `Ai1SessionMessageRoleEnum`（字符串 `"user"` 用户、`"assistant"` 助手） |
| reasoning | String | reasoning | 思考过程，即推理模型的 reasoning_content |
| content | String | content | 内容（人工终止 / 生成失败时追加「本条回复已被人工终止 / 生成失败」提示） |
| status | Integer | status | 生成状态，枚举 `Ai1SessionMessageStatusEnum`：0 生成中（占位可续传）、1 完成、2 失败 |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

### 2.5 长期记忆聚合

#### Ai1MemoryDO (ai1_memory)

AI1 长期记忆：每个用户在每个 Agent 下一条未删除的记忆，由归档 Job 根据已完成的消息增量生成；删除为逻辑删除以保留历史便于追溯，之后的归档会根据历史消息生成新记录。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| agentId | Long | agent_id | Agent 编号，关联 `Ai1AgentDO.id` |
| userId | Long | user_id | 用户编号，关联 system 模块 AdminUserDO.id |
| content | String | content | 记忆正文，Markdown 格式，按维度分节 |
| lastMessageId | Long | last_message_id | 已归档的最后一条消息编号，即增量归档的水位线，关联 `Ai1SessionMessageDO.id` |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引。「每 (agentId, userId) 一条未删除记录」为业务约定（`Ai1MemoryDO` 类注释明示），代码未声明唯一索引（`Ai1MemoryMapper#selectByAgentIdAndUserId` 注释明示），极端并发下可能重复，用 selectFirstOne 取第一条兜底

### 2.6 扩展能力聚合（MCP / SKILL）

#### Ai1McpDO (ai1_mcp)

AI1 MCP 服务：外部 MCP Server 的连接配置，传输方式分远程 http（Streamable HTTP）与本地 stdio 进程两种。`transport` 列为准，保存时同步写回 config JSON 的 transport 字段；切换为本地时 url 置空（由 `Ai1McpMapper#updateForSave` 主动 set null）。`@TableName(autoResultMap = true)`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 名称 |
| transport | String | transport | 传输方式，枚举 `Ai1McpTransportEnum`（`"http"` 远程 Streamable HTTP、`"stdio"` 本地进程）；以该列为准，保存时同步写回 config 的 transport 字段 |
| url | String | url | 服务地址，远程必填、本地为空；切换为本地时由 `Ai1McpMapper#updateForSave` 主动置空 |
| headers | Map\<String, String\> | headers | 请求头，`JacksonTypeHandler` 存 JSON 对象，例如 `{"Authorization":"Bearer xxx"}` |
| config | String | config | 完整 MCP 配置，JSON 字符串；远程 `{transport, url, headers}`，本地 `{transport, command, args, env, cwd}` |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |
| remark | String | remark | 备注 |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

#### Ai1SkillDO (ai1_skill)

AI1 SKILL：技能定义（名称 / 描述 / 版本 / 状态）。`name` 同时作为物化目录名（租户内唯一，仅支持字母、数字、中划线），物化时把 ai1_skill_file 文件树写入本地技能目录（`yudao.ai1.skill.root`，默认 `~/yudao-ai1/skills`）。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| name | String | name | 名称；同时作为物化目录名，租户内唯一（业务约定），仅支持字母、数字、中划线 |
| description | String | description | 描述 |
| version | String | version | 版本 |
| status | Integer | status | 状态，枚举 `CommonStatusEnum` |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引。`name` 的租户内唯一性由服务层校验（`Ai1SkillMapper#selectByName` + Service 层校验）保证，属应用层逻辑唯一约束，代码未声明唯一索引

#### Ai1SkillFileDO (ai1_skill_file)

AI1 SKILL 内容文件：以 parentId 组织为文件树（目录 + 文件两种节点），物化时按树结构写入本地技能目录。固定节点（SKILL.md、scripts/、reference/）`locked = true`，不可删除、改名、移动。类常量 `PARENT_ID_ROOT = 0L`（根级）、`NAME_SKILL = "SKILL.md"`。

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|---------|------|
| id | Long | id | 编号（主键，自增） |
| skillId | Long | skill_id | SKILL 编号，关联 `Ai1SkillDO.id` |
| parentId | Long | parent_id | 父目录编号，自关联本表 `id`；根级为 `PARENT_ID_ROOT = 0` |
| name | String | name | 文件或目录名称（SKILL 入口文件固定为 `NAME_SKILL = "SKILL.md"`） |
| type | Integer | type | 类型，枚举 `Ai1SkillFileTypeEnum`：0 目录、1 文件 |
| fileType | String | file_type | 文件类型，即扩展名；目录为空 |
| content | String | content | 文件内容；目录为空 |
| locked | Boolean | locked | 是否固定；固定节点（SKILL.md、scripts/、reference/）不可删除、改名、移动 |
| sort | Integer | sort | 排序（`Ai1SkillFileMapper.selectListBySkillId` 按 type → sort → id 升序返回） |

**继承**: TenantBaseDO
**索引**: 主键 id；无其他已声明索引

## 3. 实体关系

核心外键 / 从属关系（均为逻辑外键，靠业务代码维护，未建数据库外键约束）：

```text
ai1_provider ──1:N(providerId)──> ai1_model
    │  providerId（Agent 对话供应商 / 知识库嵌入供应商 共用）
    │  modelId（Agent 对话模型 / 知识库嵌入模型 共用）
    ├──> ai1_agent (providerId, modelId)
    └──> ai1_knowledge_base (embeddingProviderId, embeddingModelId)
              │ 1:N(knowledgeBaseId)
              ▼
         ai1_knowledge_document ──分片向量──> Milvus 集合 knowledge_base_{知识库编号}（不落 MySQL）

ai1_agent ──1:N(agentId)──> ai1_session ──1:N(sessionId)──> ai1_session_message
    │                          (userId ⇢ system AdminUserDO)        ▲
    │                                                                │ 水位线 lastMessageId
    └──1:N(agentId)──> ai1_memory (agentId, userId, lastMessageId)

逻辑多对多（varchar 逗号分隔存储，无中间表）：
ai1_agent.knowledge_base_ids ⇢ ai1_knowledge_base.id（Mapper 用 FIND_IN_SET 查询引用计数）
ai1_agent.mcp_ids           ⇢ ai1_mcp.id
ai1_agent.skill_ids         ⇢ ai1_skill.id

ai1_skill ──1:N(skillId)──> ai1_skill_file ──parentId 表内自关联──> 目录树（根级 parent_id = 0）
```

关系要点：

- **ai1_provider → ai1_model**：供应商与模型的 1:N 关系（`Ai1ModelMapper.selectListByProviderId` / `selectByProviderIdAndModel`）；供应商是 OpenAI 兼容端点的接入配置，模型只是其下的元数据。
- **ai1_model → ai1_agent / ai1_knowledge_base**：Agent 用对话类型模型（modelId），知识库用嵌入类型模型（embeddingModelId，type = 1 嵌入）；删除前由 `Ai1AgentMapper.selectCountByModelIds`、`Ai1KnowledgeBaseMapper.selectCountByEmbeddingModelIds` 做引用计数校验。
- **ai1_knowledge_base → ai1_knowledge_document**：知识库三级结构中的两级（文档原文在 MySQL，分片向量在 Milvus）；删除知识库时由 `Ai1KnowledgeDocumentMapper.deleteByKnowledgeBaseIds` 级联（逻辑）删除文档。
- **ai1_knowledge_document → 外部向量库 Milvus**：文档分片向量存于集合 `{collectionPrefix}{知识库编号}`（默认 `knowledge_base_{id}`），按知识库隔离，向量数据不落本模块数据库。
- **ai1_agent 对 knowledge / mcp / skill 的引用**：通过 `LongListTypeHandler` 存逗号分隔 varchar（如 `"1,2,3"`）实现逻辑多对多，没有中间表；`knowledge_base_ids` 的引用计数用 `MyBatisUtils.findInSet`（FIND_IN_SET）查询。
- **ai1_agent → ai1_session → ai1_session_message**：Agent 下的用户会话（`Ai1SessionMapper.selectListByAgentIdAndUserId` / `selectListByAgentIds`），会话下的消息；删除会话时由 `Ai1SessionMessageMapper.deleteBySessionIds` 级联（逻辑）删除消息。
- **ai1_session_message → ai1_memory**：`lastMessageId` 作为长期记忆的增量归档水位线（`Ai1SessionMessageMapper.selectListBySessionIdsAndStatusAndIdBetween` 拉取水位线之后的已完成消息）；每 (agentId, userId) 一条未删除记忆（`Ai1MemoryMapper.selectByAgentIdAndUserId`）。
- **ai1_skill → ai1_skill_file**：SKILL 的内容文件树；删除 SKILL 时由 `Ai1SkillFileMapper.deleteBySkillIds` 级联（逻辑）删除文件树。文件表内 `parentId` 自关联组织目录树，根级 `parent_id = 0`。
- **删除保护（引用计数）**：`Ai1AgentMapper.selectCountByModelIds / selectCountByKnowledgeBaseIds / selectCountBySkillIds`、`Ai1ModelMapper.selectCountByProviderIds`、`Ai1KnowledgeBaseMapper.selectCountByEmbeddingModelIds`——删除 Provider / Model / 知识库 / SKILL 前校验被 Agent 引用情况。
- **跨模块**：`ai1_session.user_id`、`ai1_memory.user_id` 弱关联 system 模块 AdminUserDO.id，仅存编号不做外键。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|------|-----|------|
| ai1_provider | Ai1ProviderDO | AI1 供应商（OpenAI 兼容端点的接口地址、密钥与自定义 Header） |
| ai1_model | Ai1ModelDO | AI1 模型（挂在供应商下的模型元数据，分对话 / 嵌入两种类型） |
| ai1_agent | Ai1AgentDO | AI1 Agent（模型 + 系统指令 + 知识库/MCP/SKILL 组合 + 长期记忆开关） |
| ai1_knowledge_base | Ai1KnowledgeBaseDO | AI1 知识库（分片 / 检索参数 + 嵌入模型配置，向量在 Milvus） |
| ai1_knowledge_document | Ai1KnowledgeDocumentDO | AI1 知识库-文档（原文存 MySQL，标记向量化状态） |
| ai1_session | Ai1SessionDO | AI1 会话（用户与 Agent 的一次会话，含自动标题） |
| ai1_session_message | Ai1SessionMessageDO | AI1 会话消息（问答两类角色，助手消息编号即 Redis 结果流标识） |
| ai1_memory | Ai1MemoryDO | AI1 长期记忆（按 Agent + 用户归档的 Markdown 记忆，含水位线） |
| ai1_mcp | Ai1McpDO | AI1 MCP 服务（远程 http / 本地 stdio 两种传输的连接配置） |
| ai1_skill | Ai1SkillDO | AI1 SKILL（技能定义，name 兼作物化目录名） |
| ai1_skill_file | Ai1SkillFileDO | AI1 SKILL 内容文件（parentId 目录树，物化到本地技能目录） |

> 补充：`Ai1HomeMapper`（`dal/mysql/home`）是唯一无 DO 对应表的 Mapper，用 `@Select` 聚合统计 ai1_agent / ai1_skill / ai1_mcp / ai1_model 四表 count、ai1_session_message 按天与按 Agent（INNER JOIN ai1_session，已删除会话不计入）统计；`CAST(create_time AS DATE)` 兼容 MySQL 与 H2。

## 5. 其他持久化结构

除 MySQL 表外，ai1 模块还使用 Redis（Redisson）、Milvus 与本地文件系统三类持久化结构。

### 5.1 Redis（dal/redis）

KEY 常量定义于 `Ai1RedisKeyConstants`，全部 Stream / Topic / Bucket 使用 Redisson 原生 `RStream` / `RTopic` / `RBucket` + StringCodec 纯字符串存储（项目 RedisTemplate 的 JSON 序列化会破坏 Stream 字段；也不用 Spring Data opsForStream，因 Redisson 适配层阻塞读取会抛 ClassCastException 且占满连接池）。KEY 不带 tenantId，租户上下文由任务字段或调用前校验归属还原。

| KEY / 格式 | 类型 | 说明 |
|-----------|------|------|
| ai1:session:tasks | Stream | 会话生成任务队列；XADD 字段：tenantId（可选，关闭多租户时不携带）、messageId、agentId、sessionId、content（均为 String）；消费组 `ai1-session-workers`，worker 从任务 tenantId 字段还原租户上下文（TenantUtils.execute）；队列最大长度 5000 条近似裁剪（TASK_STREAM_MAX_LENGTH）；所有租户共用一个队列 |
| ai1:session:task-lock:{messageId} | Redisson RLock | 会话生成任务执行锁，按助手消息编号隔离；不设置租期，由 Redisson 看门狗续期 |
| ai1:session:result:{messageId} | Stream | 会话结果流，按助手消息编号隔离，与 ai1_session_message 助手消息一一对应；XADD 字段：type（SSE 事件类型）、data（字符串原文；转发 SSE 时才统一 JSON 序列化，见 `Ai1SessionStreamTool#sendEvent`）；续传时携带 lastEventId 从断点重放、不重新生成；TTL 由 `yudao.ai1.session.stream.ttlSeconds` 控制（默认 3600s），终态事件续期一次完整 TTL；续传前已按租户、用户校验消息归属 |
| ai1:session:stop:{messageId} | String（值为 "1"） | 会话停止意图，覆盖排队中与其他节点执行中的任务；TTL 与结果流一致（stream.ttlSeconds） |
| ai1:session:stop | Pub/Sub Topic | 会话停止通知，消息内容为助手消息编号，用于即时唤醒执行节点（兜底另有 1s 间隔的停止意图轮询） |
| ai1:memory:archive-lock:{tenantId} | Redisson RLock | 长期记忆归档锁，按租户互斥；`Ai1MemoryLockRedisDAO#tryLockArchive` 不等待，其他节点归档中时直接跳过 |
| ai1:memory:snapshot-lock:{agentId}:{userId} | Redisson RLock | 长期记忆快照锁：消息落库事务与归档读取互斥，避免低编号消息晚提交后落在水位线之前；Agent 编号全局唯一，KEY 不带 tenantId；`Ai1MemoryLockRedisDAO#lockSnapshot` 阻塞获取 |

会话流的 Stream / 锁 / 停止意图读写实现在 `harness/session/Ai1SessionStreamTool`。

### 5.2 Milvus 向量集合

- 知识库的分片向量不落 MySQL，存于 Milvus 集合 `{collectionPrefix}{知识库编号}`（配置 `yudao.ai1.milvus.collection-prefix`，默认 `knowledge_base_`），按知识库隔离。
- MySQL 侧（ai1_knowledge_document）只存文档原文 content、分片数量 chunk_count 与向量化状态 status（0 未处理、1 已向量化、2 失败），与旧 ai 模块「segment 表存 vectorId 引用」的方式不同。

### 5.3 本地文件系统（SKILL 物化目录）

- SKILL 物化根目录由配置 `yudao.ai1.skill.root` 控制，默认 `~/yudao-ai1/skills`。
- 物化时把 `ai1_skill_file` 的文件树按 `parentId` 结构写入 `{root}/agent_{agentId}/{skill.name}/` 目录：物化以 Agent 为沙箱（`Ai1SkillToolFactory#buildAgentRoot`，Agent 删除时整目录清理），每个 SKILL 目录名取 `sanitize(skill.name)`；与 `YudaoAi1Properties.Skill` 注释「实际目录为 {root}/agent_{agentId}」保持一致。固定节点（SKILL.md、scripts/、reference/）不可删除、改名、移动。
