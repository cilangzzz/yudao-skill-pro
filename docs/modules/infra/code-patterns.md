# 基础设施代码模式与扩展指南 (infra)

> 本文档移植自模块 Skill 知识库（skill-infra.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

标准注解组合：

- `@Tag(name = "管理后台 - xxx")` — Swagger 文档标签
- `@RestController` — REST 控制器
- `@RequestMapping("/infra/xxx")` — 请求路径前缀
- `@Validated` — 参数校验
- `@PreAuthorize("@ss.hasPermission('infra:xxx:action')")` — 权限控制

示例（FileController，文件上传）：

```java
@Tag(name = "管理后台 - 文件存储")
@RestController
@RequestMapping("/infra/file")
@Validated
public class FileController {
    @Resource
    private FileService fileService;

    @PostMapping("/upload")
    @Operation(summary = "上传文件")
    public CommonResult<String> uploadFile(@Valid FileUploadReqVO uploadReqVO) throws Exception {
        MultipartFile file = uploadReqVO.getFile();
        byte[] content = IoUtil.readBytes(file.getInputStream());
        return success(fileService.createFile(content, file.getOriginalFilename(),
                uploadReqVO.getDirectory(), file.getContentType()));
    }
}
```

### Service 层规范

- 接口模式：`XxxService` 接口定义业务方法，`XxxServiceImpl` 实现类
- 实现模式：

```java
@Service
@Validated
public class XxxServiceImpl implements XxxService {
    @Resource
    private XxxMapper xxxMapper;

    // 使用 static final 定义常量
    // 使用 @Transactional 注解控制事务
    // 使用 validateXxxExists 方法校验存在性
    // 使用 exception(ErrorCode) 抛出业务异常
}
```

示例（FileServiceImpl，文件上传的核心流程：处理参数 → 生成路径 → 上传存储 → 落库）：

```java
@Service
public class FileServiceImpl implements FileService {
    @Resource
    private FileConfigService fileConfigService;
    @Resource
    private FileMapper fileMapper;

    @Override
    public String createFile(byte[] content, String name, String directory, String type) {
        // 1. 处理参数
        // 2. 生成上传路径
        String path = generateUploadPath(name, directory);
        // 3. 上传到文件存储器
        FileClient client = fileConfigService.getMasterFileClient();
        String url = client.upload(content, path, type);
        // 4. 保存到数据库
        fileMapper.insert(new FileDO()...);
        return url;
    }
}
```

### DAL 层规范

Mapper 继承 `BaseMapperX<XxxDO>`：

```java
public interface XxxMapper extends BaseMapperX<XxxDO> {
    // 继承 BaseMapperX 获得通用 CRUD 方法
    // 自定义查询方法使用 @Select 注解或 XML
    // 分页查询返回 PageResult<XxxDO>
}
```

示例（FileMapper，使用 `LambdaQueryWrapperX` 的条件拼接与分页）：

```java
public interface FileMapper extends BaseMapperX<FileDO> {
    default PageResult<FileDO> selectPage(FilePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<FileDO>()
                .likeIfPresent(FileDO::getPath, reqVO.getPath())
                .likeIfPresent(FileDO::getName, reqVO.getName())
                .betweenIfPresent(FileDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(FileDO::getId));
    }
}
```

### 异常处理

错误码前缀：`1_001_XXX_XXX`（即 1-001-xxx-xxx 段）。

| 错误码 | 消息 |
|--------|------|
| 1_001_000_001 | 参数配置不存在 |
| 1_001_001_000 | 定时任务不存在 |
| 1_001_003_001 | 文件不存在 |
| 1_001_004_002 | 表定义已经存在 |
| 1_001_006_000 | 文件配置不存在 |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ErrorCode)`

## 扩展指南

### 新增文件存储类型

1. **创建配置类**：在 `framework/file/core/client/` 下创建 `XxxFileClientConfig` 实现 `FileClientConfig`

```java
@Data
public class XxxFileClientConfig implements FileClientConfig {
    private String endpoint;
    private String accessKey;
    private String secretKey;
}
```

2. **创建客户端类**：创建 `XxxFileClient` 继承 `AbstractFileClient<XxxFileClientConfig>`

```java
public class XxxFileClient extends AbstractFileClient<XxxFileClientConfig> {
    public XxxFileClient(Long id, XxxFileClientConfig config) {
        super(id, config);
    }

    @Override
    protected void doInit() {
        // 初始化客户端
    }

    @Override
    public String upload(byte[] content, String path, String type) {
        // 实现上传逻辑
    }

    @Override
    public void delete(String path) {
        // 实现删除逻辑
    }

    @Override
    public byte[] getContent(String path) {
        // 实现获取内容逻辑
    }
}
```

3. **注册枚举**：在 `FileStorageEnum` 中添加新存储类型

```java
XXX(30, XxxFileClientConfig.class, XxxFileClient.class);
```

4. **测试验证**：编写单元测试验证功能正确性

### 自定义代码生成模板

1. **创建模板文件**：在 `resources/codegen/` 下创建 `.vm` 模板文件
2. **注册模板路径**：在 `CodegenEngine` 的 `SERVER_TEMPLATES` 或 `FRONT_TEMPLATES` 中添加映射

```java
.put(javaTemplatePath("custom/template"), javaModuleImplMainFilePath("custom/${table.className}Custom"))
```

3. **添加模板变量**：在 `initBindingMap()` 方法中添加模板需要的全局变量
4. **测试生成结果**：使用预览接口验证生成代码

### 最佳实践

- **文件上传路径规范**：使用 `generateUploadPath()` 方法生成唯一路径，包含日期前缀和时间戳后缀，避免文件名冲突
- **文件配置缓存**：使用 Guava LoadingCache 缓存 FileClient，避免频繁查询数据库，支持异步刷新
- **代码生成同步**：使用 `syncCodegenFromDB()` 同步数据库表结构变更，保持代码生成定义与数据库一致
- **定时任务幂等**：`JobHandler.execute()` 应实现幂等性，避免重复执行产生副作用
- **错误日志追踪**：通过 `traceId` 关联 API 访问日志和错误日志，便于问题排查

## 模块依赖

内部依赖（框架组件）：

| 模块 | 用途 |
|------|------|
| yudao-framework-common | 通用工具类、CommonResult、PageResult 等 |
| yudao-framework-mybatis | MyBatis-Plus 封装、BaseMapperX、BaseDO |
| yudao-framework-quartz | Quartz 封装、JobHandler、SchedulerManager |
| yudao-framework-tenant | 租户支持、@TenantIgnore |

外部依赖（第三方库）：

| 依赖 | 用途 |
|------|------|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装 |
| Quartz | 定时任务调度框架 |
| Velocity | 模板引擎，用于代码生成 |
| Hutool | Java 工具类库 |
| Guava | Google 工具库，使用 Cache、Table 等 |
| MinIO/S3 SDK | 对象存储客户端 |
| Swagger/OpenAPI | API 文档注解 |

> 本模块不依赖任何业务模块；完整的 framework starter 清单与下游依赖模块列表见 [README](README.md) 的「依赖关系」一节，模块间依赖图见 [docs/README.md](../README.md)。

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/service/file/FileServiceImpl.java | 文件服务实现，核心上传下载逻辑 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/service/file/FileConfigServiceImpl.java | 文件配置服务，FileClient 缓存管理 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/framework/file/core/client/FileClient.java | 文件客户端接口定义 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/framework/file/core/client/AbstractFileClient.java | 文件客户端抽象类，模板方法模式 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/framework/file/core/enums/FileStorageEnum.java | 文件存储类型枚举，配置类与客户端类映射 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/service/codegen/CodegenServiceImpl.java | 代码生成服务实现 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/service/codegen/inner/CodegenEngine.java | 代码生成引擎，模板渲染核心 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/service/codegen/inner/CodegenBuilder.java | 代码生成对象构建器 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/service/job/JobServiceImpl.java | 定时任务服务实现，Quartz 集成 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/api/file/FileApi.java | 文件 API 接口，供其他模块调用 |
| yudao-module-infra/src/main/java/cn/iocoder/yudao/module/infra/enums/ErrorCodeConstants.java | 错误码常量定义 |

## 领域模型

聚合根：

| 聚合 | 包含实体 | 说明 |
|------|----------|------|
| 文件存储聚合 | FileDO、FileConfigDO、FileContentDO | FileConfigDO 是配置聚合根，FileDO 是文件记录，FileContentDO 是数据库存储的文件内容 |
| 代码生成聚合 | CodegenTableDO、CodegenColumnDO | CodegenTableDO 是表定义聚合根，CodegenColumnDO 是列定义，两者是一对多关系 |
| 定时任务聚合 | JobDO、JobLogDO | JobDO 是任务定义聚合根，JobLogDO 是执行日志，两者是一对多关系 |
| API 日志聚合 | ApiAccessLogDO、ApiErrorLogDO | 独立的日志实体，无关联关系 |

值对象：

| 对象 | 说明 |
|------|------|
| FileClientConfig | 文件客户端配置接口，有多种实现（LocalFileClientConfig、S3FileClientConfig 等） |
| FileStorageEnum | 文件存储类型枚举，定义存储类型与配置类、客户端类的映射关系 |

> 领域服务（FileService、FileConfigService、CodegenService、JobService、ConfigService）的职责划分见 [README](README.md) 的「核心功能点」。

## 设计与架构补充

### 分层架构

| 层 | 职责 | 组件 |
|----|------|------|
| api | 模块间 API 接口，供其他模块调用 | FileApi（文件上传）、ConfigApi（配置获取）、WebSocketSenderApi（WebSocket 消息发送） |
| controller | HTTP 接口层，提供 RESTful API | admin/codegen、admin/file、admin/job、admin/logger、admin/config、admin/db、admin/redis、admin/demo（代码生成示例 Demo01/Demo02/Demo03）、app/file（App 端文件上传） |
| service | 业务逻辑层 | codegen（CodegenService、CodegenBuilder、CodegenEngine）、file（FileService、FileConfigService）、job（JobService、JobLogService）、logger（ApiAccessLogService、ApiErrorLogService）、config（ConfigService）、db（DataSourceConfigService、DatabaseTableService） |
| dal | 数据访问层 | dataobject（DO 实体类定义）、mysql（MyBatis Mapper 接口） |
| framework | 框架层，模块内部基础设施 | file/core/client（文件客户端抽象和实现）、file/core/enums（文件存储枚举）、codegen/config（代码生成配置） |

> controller/service 各接口明细见 [README](README.md) 的「API 接口索引」；本表补充 README 未展开的 framework 层结构与 App 端接口（app/file）。

### 设计原则补充

[README](README.md) 的「设计原则」「设计模式」已覆盖策略 + 工厂模式、模板方法模式、模板驱动生成、租户隔离忽略等，此处补充其余两点：

| 原则 | 说明 |
|------|------|
| 多态配置 | FileClientConfig 使用 Jackson `@JsonTypeInfo` 实现多态序列化，配置类与存储类型一一对应，`infra_file_config.config` 字段以 JSON 反序列化为具体配置实现 |
| 缓存优化 | FileClient 使用 Guava LoadingCache 实现 10 秒异步刷新，避免频繁查询数据库（应用位置：FileConfigServiceImpl） |

### 表关系（ER）

| 来源表 | 关联表 | 关系 | 外键 | 说明 |
|--------|--------|------|------|------|
| infra_file | infra_file_config | N:1 | config_id | 文件记录关联存储配置 |
| infra_codegen_column | infra_codegen_table | N:1 | table_id | 列定义关联表定义 |
| infra_job_log | infra_job | N:1 | job_id | 任务日志关联任务定义 |
| infra_codegen_table | infra_codegen_table | N:1 | master_table_id | 主子表关联 |
| infra_codegen_table | infra_data_source_config | N:1 | data_source_config_id | 代码生成表定义关联数据源配置 |
