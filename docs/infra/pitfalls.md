# 注意事项与已知坑点

> 使用 infra 模块时的常见问题、易踩坑点和最佳实践。

> 版本提示：当前仓库为 JDK8 分支（revision `2026.09-jdk8-SNAPSHOT`，Spring Boot 2.7.18），代码使用 `javax.servlet` / `javax.annotation` 而非 `jakarta`，阅读源码与二次开发时注意与 Spring Boot 3.x 版本区分。

infra 模块的特殊性：它既是「平台基础设施」（配置、文件、定时任务、日志、代码生成），又被几乎所有业务模块依赖（`FileApi` 被 system/ai/mp/oa/pms/fms 消费，`ConfigApi` 被 system 消费，`WebSocketSenderApi` 被 system/im/promotion 消费）。因此 infra 出问题的影响面是全局的。

## 1. 多租户相关

### 1.1 infra 绝大多数表是全局表，租户隔离只覆盖日志与 demo 表

**问题**: 误以为 infra 所有数据都按租户隔离。实际上参数配置、文件、文件配置、数据源、代码生成、定时任务等都是全站共享的，租户 A 的管理员可以看到（并修改）影响所有租户的全局数据。

**原因**: 除 `ApiAccessLogDO` / `ApiErrorLogDO` 与 demo 域 DO 外，其余 DO 均标注了 `@TenantIgnore`（全局表，SQL 不追加 `tenant_id` 条件），包括 `ConfigDO`、`FileDO`、`FileContentDO`、`FileConfigDO`、`DataSourceConfigDO`、`JobDO`、`JobLogDO`、`CodegenTableDO`、`CodegenColumnDO`。这些表继承的也只是 `BaseDO`（无 `tenantId` 字段），租户拦截器按 `@TenantIgnore` 注解放行。

**解决**:
- 给角色分配 `infra:config:*`、`infra:file-config:*`、`infra:data-source-config:*`、`infra:job:*` 等权限时要极其谨慎——这些是「平台级」能力，只应授予平台运营方（租户 1）的管理员，不要下放给租户管理员。
- 自定义清理逻辑操作这些全局表时必须加 `@TenantIgnore`（参考 `ErrorLogCleanJob.execute`），否则 Quartz 线程无租户上下文，租户拦截器可能拼出异常 SQL 或漏删数据。
- 日志表（`infra_api_access_log` / `infra_api_error_log`）和 demo 表**是**租户隔离的，查询日志会自动带 `tenant_id` 过滤，跨租户排查问题时需注意。

### 1.2 定时任务与异步链路中的租户上下文丢失

**问题**: 自己写的 `JobHandler` 在 Quartz 线程里执行时，查询租户隔离表查不到数据，或插入时报租户相关错误；通过 `ApiErrorLogCommonApi` 异步记错误日志时偶发插入失败。

**原因**: `JobHandlerInvoker`（yudao-spring-boot-starter-job）调用 `JobHandler.execute(String)` 时不会设置租户上下文，Quartz 线程中 `TenantContextHolder.getTenantId()` 为 null。租户隔离表（如日志表）的 INSERT 会被租户拦截器处理，无租户上下文时直接失败。

**解决**:
- 需要逐租户执行的业务 Job，在 `execute` 方法上加框架的 `@TenantJob` 注解（`TenantJobAspect` 会取全量租户并 `TenantUtils.execute(tenantId, ...)` 并行执行）。注意 `TenantJobAspect` 的注释：Job 必须幂等，因为某租户失败重试时其他租户会重复执行。
- 全局清理类 Job 则加 `@TenantIgnore`（参考 `AccessLogCleanJob` / `ErrorLogCleanJob` / `JobLogCleanJob`）。
- infra 自身在 `ApiErrorLogServiceImpl.createApiErrorLog` 做了兜底：`TenantContextHolder.getTenantId() == null` 时用 `TenantUtils.executeIgnore` 忽略租户插入，避免记录日志本身失败；同时整个方法 catch 住异常只打日志——错误日志记录是 best-effort 语义，不要依赖它抛错。

### 1.3 文件内容下载接口是匿名可访问的

**问题**: `GET /infra/file/{configId}/get/**` 不需要登录 token 即可访问，且不受租户隔离。上传到私有存储的文件，若拿到路径也能通过该接口读取。

**原因**: `FileController.getFileContent` 同时标注了 `@PermitAll` 和 `@TenantIgnore`（框架扫描 `@PermitAll` 自动放行）。这是有意设计：`<img>`、`<video>` 等标签引用文件 URL 时无法携带登录态。

**解决**:
- 敏感文件不要依赖「下载接口未暴露」的安全假设；私有桶（S3/OSS）场景应使用 `presignGetUrl` 生成的带签名 URL 限时访问。
- 确需鉴权的文件（如合同、账单），不要走该通用下载接口，业务模块自建带权限校验的下载端点。
- `configId` + `path` 即可定位文件，`path` 生成规则（`FileServiceImpl.generateUploadPath`，日期前缀 + 原文件名）是可预测的，注意不要让可预测路径成为遍历入口。

## 2. 缓存相关

### 2.1 文件配置客户端缓存只在本机失效，多实例部署会短暂不一致

**问题**: 修改/切换文件配置后，部分节点仍在用旧的存储配置（例如旧 OSS Bucket）上传文件，持续数秒到更久。

**原因**: `FileConfigServiceImpl` 用 Guava `LoadingCache`（`buildAsyncReloadingCache(Duration.ofSeconds(10))`）缓存 `FileClient`，底层 `FileClientFactoryImpl` 用 JVM 内 `ConcurrentHashMap` 保存客户端实例。`clearCache` 只操作本进程的 `clientCache`，没有 Redis 广播；其他实例要等缓存过期后的异步 reload 才会读到新配置。

**解决**:
- 单实例部署无感；多实例部署改完文件配置后，若要求立即生效，可滚动重启或接受最长约 10 秒（外加访问触发时机）的不一致窗口。
- 不要在 `FileClient` 之外再自己缓存 `FileConfigDO`，一律通过 `fileConfigService.getMasterFileClient()` / `getFileClient(id)` 取，让统一的失效逻辑生效。

### 2.2 切换主文件配置在事务内清缓存，且伴随一次全表 UPDATE

**问题**: 切换主配置后偶发「切换不生效」；且切换瞬间会对 `infra_file_config` 全表执行一次 UPDATE，表大时产生锁等待。

**原因**: `FileConfigServiceImpl.updateFileConfigMaster` 有两个点：一是 `fileConfigMapper.updateBatch(new FileConfigDO().setMaster(false))` 走 `BaseMapperX.updateBatch(T)` → `update(update, new QueryWrapper<>())`，是无 WHERE 的全表更新；二是 `clearCache(null, true)` 在 `@Transactional` 事务提交前执行，其他线程立刻 reload 时读到的还是旧数据（另一连接看不到未提交事务），旧客户端会被回填进缓存。

**解决**:
- 接受短暂的缓存陈旧窗口（约 10 秒内收敛），不要在切换后立即用 `getMasterFileClient` 做强一致断言。
- 若优化全表 UPDATE，可改为「先 UPDATE 非 master 的行（排除目标 id）」，并考虑用事务 `afterCommit` 回调时机清缓存。

## 3. 事务与状态机相关

### 3.1 文件存储操作与数据库记录不是原子的

**问题**: `createFile` 上传成功但 DB 插入失败时，存储器中留下无法通过管理界面管理的孤儿文件；`deleteFile` 删完物理文件后 DB 删除失败时，记录悬空（列表里还在，再删报错或文件 404）。

**原因**: `FileServiceImpl.createFile` 的顺序是 `client.upload(...)` → `fileMapper.insert(...)`，`deleteFile` 是 `client.delete(...)` → `fileMapper.deleteById(...)`，方法上都没有 `@Transactional`（物理存储操作本身也无法参与 DB 事务）。

**解决**:
- 理解这是「先外后内」的一致性取舍：宁可有孤儿文件，不能有 DB 记录但物理文件缺失（后者会导致下载 404）。
- 批量删除 `deleteFileList` 同理：逐个删物理文件成功后统一删记录，中间失败会留下部分删除状态，重试即可收敛。
- 运维侧可定期对账：用 `infra_file` 的 `path` + `configId` 反查存储器，清理孤儿对象。

### 3.2 定时任务的 Quartz 操作不会随 Spring 事务回滚，且受状态机约束

**问题**: 创建/删除/暂停任务时抛异常，`infra_job` 表回滚了，但 Quartz 调度器里的任务状态没回滚，两边状态对不上；修改暂停状态的任务直接报错。

**原因**: `JobServiceImpl` 的 `createJob` / `updateJob` / `updateJobStatus` / `deleteJob` 都标了 `@Transactional(rollbackFor = Exception.class)`，但其中调用的 `schedulerManager.addJob / pauseJob / resumeJob / deleteJob` 操作的是 Quartz 自己的 `QRTZ_` 表（独立连接），不在 Spring 事务管理范围内。同时代码内建了状态机：`updateJob` 要求任务必须处于 NORMAL 状态才能修改（否则抛 `JOB_UPDATE_ONLY_NORMAL_STATUS`，因为暂停状态下改 Quartz Job 会导致任务恢复执行）；`updateJobStatus` 只允许 NORMAL/STOP 两个目标状态，且相同状态抛 `JOB_CHANGE_STATUS_EQUALS`。

**解决**:
- 修改任务前先确认状态为「开启」，需要改暂停任务时先恢复再改。
- 状态不一致时可用 `JobServiceImpl.syncJob`（以 `infra_job` 表为准，先删后建重建全部 Quartz 任务）修复，它天然向 DB 配置收敛。
- handlerName 通过 `SpringUtil.getBean(handlerName)` 校验，必须是实现 `JobHandler` 的 Spring Bean（错误码 `JOB_HANDLER_BEAN_NOT_EXISTS` / `JOB_HANDLER_BEAN_TYPE_ERROR` 提示了首字母小写命名约定）。

## 4. 错误码与接口权限

### 4.1 错误码 1_001_004_002 被重复定义

**问题**: 前端按 code 区分「表定义已经存在」和「导入的字段不存在」时无法区分，二者返回同一个 code。

**原因**: `ErrorCodeConstants` 中 `CODEGEN_TABLE_EXISTS = 1_001_004_002` 与 `CODEGEN_IMPORT_COLUMNS_NULL = 1_001_004_002` 撞号（中间还跳过了 1_001_004_003）。

**解决**:
- 修改该文件时新增错误码务必全文件查重（历史上已撞过一次）；infra 段为 `1_001_000_000` 起，其中 demo 域固定占用 `1_001_201_000` 段，新增业务错误码从 `1_001_007_000`（数据源）之后顺延，避开 demo 段。

### 4.2 按参数键查值接口只校验登录，靠 visible 字段兜底

**问题**: `GET /infra/config/get-value-by-key` 没有 `@PreAuthorize`，任何登录用户都能按 key 查参数值；把敏感信息（如三方密钥）存进参数配置可能被普通用户读取。

**原因**: `ConfigController.getConfigKey` 设计上供前端业务读取参数，仅要求登录；防泄露机制是 `ConfigDO.visible` 字段——`visible = false` 时抛 `CONFIG_GET_VALUE_ERROR_IF_VISIBLE`（1_001_000_004）。

**解决**:
- 敏感配置项必须把「是否可见」设为 false，前端一律不通过该接口获取；敏感配置改走后端读取（`ConfigService.getConfigByKey`）。
- 该接口对不存在的 key 返回 `success(null)` 而不是报错，前端需处理空值。
- 注意 `deleteConfig` / `deleteConfigList` 会拦截 `ConfigTypeEnum.SYSTEM` 类型（`CONFIG_CAN_NOT_DELETE_SYSTEM_TYPE`），内置参数不可删，只能改值。

## 5. 文件相关

### 5.1 后端上传与前端直传的文件类型校验强度不同

**问题**: 走后端 `/infra/file/upload` 传伪造类型的文件会被拒；走 `/infra/file/presigned-url` + `/infra/file/create`（前端直传 OSS）时，恶意内容有机会绕过类型检查。

**原因**: `FileServiceImpl.createFile(byte[]...)` 不信任客户端传入的 type，用 `FileTypeUtils.getMineType(content, name)` 基于内容重新嗅探，再校验 `ALLOWED_FILE_TYPES` 白名单，图片还要求扩展名类型与内容类型一致；而 `presignPutUrl` / `createFile(FileCreateReqVO)` 拿不到文件内容，只能按文件名校验 MIME（`validateFileType(name)`）。

**解决**:
- 安全敏感场景优先走后端上传模式；必须直传时，在存储端（OSS 回源校验、CDN 防护）或业务侧做二次内容校验。
- 自定义允许的文件类型时修改 `FileServiceImpl.ALLOWED_FILE_TYPES` 常量，注意它是全模块共用的白名单，收紧/放开影响所有上传方（system、ai、mp、oa、pms、fms 均通过 `FileApi` 上传）。

### 5.2 文件配置被删除后，历史文件变成「死文件」，且错误以 500 而非业务错误呈现

**问题**: 删除某个文件配置后，原来通过它上传的文件既无法下载也无法删除，接口报 500 而非业务错误码。

**原因**: `FileClientFactoryImpl.getFileClient` 找不到客户端时只 `log.error` 并返回 null（不抛业务异常）；调用方 `FileServiceImpl` 用 `Assert.notNull(client, "客户端({}) 不能为空", ...)` 断言，抛出的是 `IllegalArgumentException` 而非 `ServiceException`，前端只能看到通用错误。`getFileContent` 走 `FileConfigServiceImpl.clientCache.load()` 时若配置已删除（`config == null`），同样拿不到客户端。

**解决**:
- 删除文件配置前，先确认该配置下没有存量文件（可按 `FileDO.configId` 查询）；`FILE_CONFIG_DELETE_FAIL_MASTER` 只拦主配置，不拦「有历史文件的非主配置」。
- 二次开发时不要把 `Assert.notNull` 当业务校验用，对外抛业务错误请用 `ServiceExceptionUtil.exception(ERROR_CODE)`。

## 6. 代码生成器相关

### 6.1 同步表结构会「删除重建」有变化的列，且导入/生成有多项硬性前置条件

**问题**: 在代码生成页面精心调整过字段的查询方式、UI 组件、字典类型后，执行「同步表结构」发现这些配置丢了；导入表时报「表注释未填写/字段注释未填写」；主子表生成时报类名或属性名重复。

**原因**:
- `CodegenServiceImpl.syncCodegen0` 的同步策略是：只新增不存在的字段；对「有变化」的字段（按 jdbcType / nullable / 是否主键 / 注释 / 位置序号比对，见 `primaryKeyPredicate`）执行先删后插，`CodegenColumnDO` 上的手工调整随删除一起丢失。特别注意：只要改了字段注释（`columnComment`），该列就会被判定为「修改」而被删除重建。
- `CodegenServiceImpl.validateTableInfo` 要求表注释和每个字段注释非空（这是生成 Swagger 注解的来源）。
- `CodegenEngine` 生成主子表时做符号归一化（`removePrefix(subTable.getClassName(), upperFirst(moduleName))`），主表与子表归一化后类名重复抛 `CODEGEN_MASTER_TABLE_NAME_DUPLICATE`（1_001_004_013），合并子表字段时属性名重复抛 `CODEGEN_MASTER_TABLE_FIELD_DUPLICATE`（1_001_004_014）；主表还必须已配置子表（`CODEGEN_MASTER_GENERATION_FAIL_NO_SUB_TABLE`）。
- `DatabaseTableServiceImpl.getTableList0` 默认排除 `ACT_` / `QRTZ_` / `FLW_` 前缀（工作流、Quartz）和含 `$` 的系统表，这些表在「导入表」列表里看不到。

**解决**:
- 建表 SQL 就写全 `COMMENT`，避免导入后再补；表结构变更后先记下页面手工调整项，同步后再补配，生成前用「预览」确认。
- 多子表场景给子表起不同业务名（如 `ErpStudent` / `InnerStudent`），或调整 `moduleName` 前缀，避免归一化后撞名。
- 无主键的表导入时框架取第一个字段当主键（`createCodegen0` 中 `columns.get(0).setPrimaryKey(true)`），业务表务必显式定义主键。
- demo 域（`Demo01Contact` 单表 / `Demo02Category` 树表 / `Demo03Student` 主子表 normal、inner、erp 三种风格）是代码生成器的标准产物示例，注意其表前缀是 `yudao_demo01_*` 而非 `infra_`，三个 Student Controller 权限统一为 `infra:demo03-student:*`，可作为新模块生成结果的对照参考。
