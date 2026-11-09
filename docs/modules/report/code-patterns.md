# 报表代码模式与扩展指南 (report)

> 本文档移植自模块 Skill 知识库（skill-report.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

标准注解组合：

- `@Tag(name = "管理后台 - XXX")`
- `@RestController`
- `@RequestMapping("/report/xxx")`
- `@Validated`
- `@PreAuthorize("@ss.hasPermission(...)")`

示例（GoViewProjectController）：

```java
@Tag(name = "管理后台 - GoView 项目")
@RestController
@RequestMapping("/report/go-view/project")
@Validated
public class GoViewProjectController {

    @Resource
    private GoViewProjectService goViewProjectService;

    @PostMapping("/create")
    @Operation(summary = "创建项目")
    @PreAuthorize("@ss.hasPermission('report:go-view-project:create')")
    public CommonResult<Long> createProject(@Valid @RequestBody GoViewProjectCreateReqVO createReqVO) {
        return success(goViewProjectService.createProject(createReqVO));
    }
}
```

### Service 层规范

- 接口模式：定义接口 + 使用 `@Service` 注解的实现类
- 实现模式：使用 `@Validated` 注解支持参数校验，依赖注入使用 `@Resource`

```java
public interface GoViewProjectService {

    Long createProject(@Valid GoViewProjectCreateReqVO createReqVO);
    void updateProject(@Valid GoViewProjectUpdateReqVO updateReqVO);
    void deleteProject(Long id);
    GoViewProjectDO getProject(Long id);
    PageResult<GoViewProjectDO> getMyProjectPage(PageParam pageReqVO, Long userId);
}

@Service
@Validated
public class GoViewProjectServiceImpl implements GoViewProjectService {

    @Resource
    private GoViewProjectMapper goViewProjectMapper;

    @Override
    public Long createProject(GoViewProjectCreateReqVO createReqVO) {
        GoViewProjectDO goViewProject = GoViewProjectConvert.INSTANCE.convert(createReqVO)
                .setStatus(CommonStatusEnum.DISABLE.getStatus());
        goViewProjectMapper.insert(goViewProject);
        return goViewProject.getId();
    }
}
```

### 框架能力：平台共享数据租户编号（`TenantUtils.GLOBAL_TENANT_ID`）

框架在 `TenantUtils` 新增常量 `GLOBAL_TENANT_ID = 0L`，表示「平台共享数据」的租户编号——它是有明确含义的租户 0，区别于「未设置租户上下文」时的 `null`。UReport2 的报表定义缓存与文件元数据按「当前租户优先、无租户上下文时归入平台」读写：

```java
// UReport2ReportDefinitionCache / UReport2FileServiceImpl
private static Long getTenantId() {
    return ObjUtil.defaultIfNull(TenantContextHolder.getTenantId(), TenantUtils.GLOBAL_TENANT_ID);
}
```

适用场景与注意：
- 需要把数据归档到「所有租户共享」的空间、或读取平台级模板/定义时，用 `GLOBAL_TENANT_ID` 作为租户条件，不要自己写魔法值 `0L`
- 不要把「租户上下文未设置」（`TenantContextHolder.getTenantId() == null`）与「平台共享」（租户 0）混为一谈：落库前先按 `defaultIfNull` 归一化，查询平台数据时按 `tenant_id = GLOBAL_TENANT_ID` 精确过滤
- 写平台级共享数据若表受租户插件管控，需配合 `TenantUtils.executeIgnore(...)` 并显式 `setTenantId(GLOBAL_TENANT_ID)`，避免租户拦截器按当前租户改写（同 hrm 工资条模板的做法）

### DAL 层规范

Mapper 继承 `BaseMapperX<DO>`，使用 default 方法实现自定义查询：

```java
@Mapper
public interface GoViewProjectMapper extends BaseMapperX<GoViewProjectDO> {

    default PageResult<GoViewProjectDO> selectPage(PageParam reqVO, Long userId) {
        return selectPage(reqVO, new LambdaQueryWrapperX<GoViewProjectDO>()
                .eq(GoViewProjectDO::getCreator, userId)
                .orderByDesc(GoViewProjectDO::getId));
    }
}
```

### 异常处理

错误码段：`1_003_000_000`（GoView 域）、`1_003_001_000`（UReport2 域）

| 错误码 | 消息 | 常量名 |
|-------|------|--------|
| 1_003_000_000 | GoView 项目不存在 | GO_VIEW_PROJECT_NOT_EXISTS |
| 1_003_001_000 | UReport2 报表模板不存在 | UREPORT2_FILE_NOT_EXISTS |

使用方式：

```java
if (goViewProjectMapper.selectById(id) == null) {
    throw exception(GO_VIEW_PROJECT_NOT_EXISTS);
}
// UReport2 模板
if (file == null) {
    throw exception(UREPORT2_FILE_NOT_EXISTS);
}
```

> 新增错误码时按子域顺延：GoView 域继续使用 `1_003_000_xxx`，UReport2 域使用 `1_003_001_xxx`；注意避开 system 的 `1_002` 段与 member 的 `1_004` 段。

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE)`

### 权限标识

业务代码中动态校验的权限标识集中定义于 `enums/PermissionConstants`，与菜单配置保持一致；接口上的 `@PreAuthorize` 仍直接书写权限标识字符串。

| 常量 | 权限标识 | 说明 |
|-----|---------|------|
| UREPORT2_QUERY | report:ureport:query | 查看：查看报表列表，预览、打印、导出已保存的报表 |
| UREPORT2_DESIGN | report:ureport:design | 设计：新建、设计、保存、删除报表，配置数据源；包含查看权限的全部功能 |

> `UReport2SecurityFilter` 使用上述常量做动态权限校验；`UReport2FileController` 的接口仍直接书写 `report:ureport:query`、`report:ureport:design` 字符串。GoView 相关权限（`report:go-view-project:*`、`report:go-view-data:*`）只在接口注解中使用，未收敛到常量类。

## 扩展指南

### 新增报表功能

1. 在 dal/dataobject 下创建 DO 实体类，继承 BaseDO
2. 在 dal/mysql 下创建 Mapper 接口，继承 BaseMapperX
3. 在 controller/admin/vo 下创建请求/响应 VO
4. 在 convert 下创建 Convert 接口（使用 MapStruct）
5. 在 service 下创建 Service 接口和实现类
6. 在 controller/admin 下创建 Controller
7. 在 enums/ErrorCodeConstants 添加错误码

### 新增数据源类型

GoView 数据集查询目前支持 SQL 与 HTTP 两种数据源，新增其他数据源类型的步骤：

1. 在 GoViewDataController 中新增查询方法，如 getDataByElasticsearch
2. 在 GoViewDataService 接口中定义新方法
3. 在 GoViewDataServiceImpl 中实现查询逻辑
4. 创建对应的请求 VO（如 GoViewDataGetByEsReqVO）
5. 添加权限注解 `@PreAuthorize("@ss.hasPermission(...)")`

示例（新增 Elasticsearch 数据源查询）：

```java
@RequestMapping("/get-by-es")
@Operation(summary = "使用 Elasticsearch 查询数据")
@PreAuthorize("@ss.hasPermission('report:go-view-data:get-by-es')")
public CommonResult<GoViewDataRespVO> getDataByEs(@Valid @RequestBody GoViewDataGetByEsReqVO reqVO) {
    return success(goViewDataService.getDataByEs(reqVO));
}
```

### 扩展 UReport2 模板存储与缓存

UReport2 通过自定义 `ReportProvider` 把模板读写落到数据库，通过 `ReportDefinitionCache` 在多实例间保持一致。扩展时注意以下约定：

1. **模板名称先规范化**：所有以名称为身份的地方（数据库读写、本地缓存、Redis 版本号）都先调用 `UReport2FileNameUtils#normalize`（去掉尾部 ASCII 空格，与 MySQL PAD SPACE 比较规则一致）。
2. **先落库再发布版本号**：`UReport2FileServiceImpl#saveFile`/`deleteFile` 无外层事务（自动提交），先写数据库，再通过 `UReport2FileVersionRedisDAO#refresh` 发布随机版本号；数据库与 Redis 不在同一事务，需容忍发布失败时各实例短暂使用旧缓存。
3. **本地缓存 key = tenantId + ":" + 规范化模板名**：`UReport2ReportDefinitionCache#buildKey`，避免不同租户同名模板互相覆盖；Redis 只保存版本号，不序列化 `ReportDefinition` 对象图。
4. **不要给 `UReport2DatabaseReportProvider` 增加 getter**：设计器会把 Provider 序列化成 JSON 加载存储列表。
5. **`reportDefinitionCache` 可能不存在**：`UReport2FileServiceImpl` 使用 `@Autowired(required = false)`，`ureport.enabled=false` 时无该 Bean，扩展代码不要假设它一定存在。
6. **新增 UReport2 请求 Action 时同步白名单**：若该 Action 应允许查看权限访问，必须加入 `UReport2SecurityFilter#QUERY_ACTIONS`，否则只持 `report:ureport:query` 的用户会 403。

### 最佳实践

- 数据查询时考虑性能，大数据量场景建议使用 ClickHouse 等列式数据库
- 报表内容使用 JSON 格式存储，前端负责解析渲染
- 项目创建时默认状态为未发布（status=1），需手动发布
- 「我的项目」列表按 `creator` 过滤；但详情、更新、删除接口只校验存在性、未校验归属，存在水平越权（见 [pitfalls.md](pitfalls.md) 2.2）
- 积木报表集成时需注意 Token 传递，通过 customApiHeader 方法处理

## 模块依赖

内部依赖（其他模块）：

| 模块 | API | 用途 |
|------|-----|------|
| system | OAuth2TokenCommonApi | 积木报表 Token 验证 |
| system | PermissionCommonApi | 积木报表权限校验 |

外部依赖（第三方库）：

| 依赖 | 版本 | 用途 |
|------|------|------|
| jimureport-spring-boot-starter | 管理在父 POM | 积木报表核心依赖，提供报表设计器 |
| jimubi-spring-boot-starter | 管理在父 POM | 积木仪表盘/大屏设计器 |
| ureport2-spring-boot-starter（cn.iocoder.ureport2） | 2.0.1（yudao-dependencies 管理） | UReport2 中国式报表设计器、预览、导出；JDK8 适配分支 |
| yudao-spring-boot-starter-redis | 框架管理 | UReport2 模板版本号缓存（StringRedisTemplate） |
| spring-boot-starter-jdbc | Spring Boot 管理 | JdbcTemplate 数据源查询 |
| mapstruct | 管理在父 POM | 对象转换 |

> UReport2 额外依赖 `yudao-spring-boot-starter-biz-tenant` 的 `TenantBaseDO` 与租户插件，以及 Spring Security 过滤器链（`UReport2SecurityFilter` 在 `TENANT_SECURITY_FILTER` 顺序执行，晚于 token 认证）。模块无消息队列依赖。

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/dataobject/goview/GoViewProjectDO.java | GoView 项目实体类，对应 report_go_view_project 表 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/service/goview/GoViewProjectService.java | 项目管理服务接口 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/service/goview/GoViewDataServiceImpl.java | 数据查询服务实现，核心 SQL 查询逻辑 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/controller/admin/goview/GoViewProjectController.java | 项目管理 HTTP 接口 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/controller/admin/goview/GoViewDataController.java | 数据查询 HTTP 接口 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/jmreport/config/JmReportConfiguration.java | 积木报表配置类 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/jmreport/core/service/JmReportTokenServiceImpl.java | 积木报表 Token 认证适配器 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/enums/ErrorCodeConstants.java | 错误码定义（GoView + UReport2） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/enums/PermissionConstants.java | 权限标识常量（report:ureport:query/design） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/mysql/goview/GoViewProjectMapper.java | 项目数据访问 Mapper |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/convert/goview/GoViewProjectConvert.java | 对象转换器（MapStruct） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/controller/admin/ureport2/UReport2FileController.java | UReport2 模板列表/删除接口 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/service/ureport2/UReport2FileServiceImpl.java | UReport2 模板保存/删除与版本号发布 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/dataobject/ureport2/UReport2FileDO.java | UReport2 模板实体（TenantBaseDO） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/mysql/ureport2/UReport2FileMapper.java | UReport2 模板 Mapper（查询不含 content） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/redis/ureport2/UReport2FileVersionRedisDAO.java | UReport2 模板版本号 Redis DAO |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/config/UReport2Configuration.java | UReport2 配置类与 ureport.enabled 开关 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/provider/UReport2DatabaseReportProvider.java | 数据库 ReportProvider（db: 前缀） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/cache/UReport2ReportDefinitionCache.java | 多实例模板缓存 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/web/UReport2SecurityFilter.java | /ureport/** 登录、租户、权限分级校验 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/util/UReport2FileNameUtils.java | 模板名称规范化 |

## 领域模型

聚合根与值对象：

| 对象 | 类型 | 说明 |
|------|------|------|
| GoViewProject | 聚合根 | 大屏报表项目，包含项目配置、发布状态、报表内容等；对应实体 GoViewProjectDO，关联值对象 GoViewDataRespVO |
| GoViewDataRespVO | 值对象 | 数据响应结构，包含维度（dimensions）和数据明细（source） |
| GoViewProjectCreateReqVO | 值对象 | 项目创建请求参数 |
| GoViewProjectUpdateReqVO | 值对象 | 项目更新请求参数 |
| UReport2File | 聚合根 | UReport2 中国式报表模板，按租户隔离；对应实体 UReport2FileDO，模板 XML 存于 content |
| UReport2FilePageReqVO | 值对象 | UReport2 模板分页请求参数 |
| UReport2FileSaveReqVO | 值对象 | UReport2 模板保存参数（供 Provider 调用，非管理后台接口入参） |
| UReport2FileRespVO | 值对象 | UReport2 模板列表响应（不含 content） |

领域服务：

| 服务 | 类型 | 说明 |
|------|------|------|
| GoViewProjectService | 领域服务 | 管理大屏项目的创建、更新、删除、查询 |
| GoViewDataService | 领域服务 | 提供数据查询能力，支持 SQL/HTTP 等数据源 |
| UReport2FileService | 领域服务 | UReport2 模板保存、删除、查询与版本号发布 |
| UReport2ReportDefinitionCache | 领域服务（框架） | 本地模板缓存 + Redis 版本号比对，实现多实例一致性 |
| UReport2SecurityFilter | 领域服务（框架） | `/ureport/**` 登录、租户、权限分级校验 |

## 设计与架构补充

### 分层架构

| 层 | 职责 | 组件 |
|----|------|------|
| controller | HTTP 接口层，提供 REST API | GoViewProjectController（大屏项目管理接口）、GoViewDataController（数据查询接口，SQL/HTTP）、UReport2FileController（UReport2 模板列表/删除） |
| service | 业务逻辑层 | GoViewProjectService/GoViewProjectServiceImpl（项目管理业务逻辑）、GoViewDataService/GoViewDataServiceImpl（数据查询业务逻辑）、UReport2FileService/UReport2FileServiceImpl（UReport2 模板与版本号） |
| dal | 数据访问层 | GoViewProjectMapper（项目数据访问）、GoViewProjectDO（项目实体）、UReport2FileMapper（模板数据访问）、UReport2FileDO（模板实体）、UReport2FileVersionRedisDAO（版本号 Redis） |
| convert | 对象转换层 | GoViewProjectConvert（DO/VO 对象转换，MapStruct）；UReport2 直接使用 `BeanUtils.toBean` |
| framework | 框架集成层 | JmReportConfiguration、JmReportTokenServiceImpl、JmOnlDragExternalServiceImpl、UReport2Configuration、UReport2DatabaseReportProvider、UReport2ReportDefinitionCache、UReport2SecurityFilter、UReport2SessionRequestWrapper、UReport2ErrorLogRequestWrapper、SecurityConfiguration（各桥接类职责详见 [README](README.md) 与 [api-ureport2.md](api-ureport2.md)） |

### 设计原则与设计模式补充

[README](README.md) 已记录适配器模式（JmReportTokenServiceImpl / JmOnlDragExternalServiceImpl）与薄壳集成、Token 桥接等原则，此处补充其余部分：

| 原则/模式 | 说明 |
|-----------|------|
| 单一职责原则 | GoViewProject 负责 project 管理，GoViewData 负责数据查询 |
| 开放封闭原则 | 通过 JmReportTokenServiceI 接口扩展积木报表认证机制 |
| 依赖倒置原则 | Service 层依赖接口而非实现，便于测试和扩展 |
| 策略模式 | 支持多种数据源查询策略（SQL、HTTP），可扩展新数据源 |
| 数据源抽象 | 默认使用 JdbcTemplate，支持切换至 ClickHouse 等大数据引擎 |
| 策略模式（查询入口） | 应用位置：GoViewDataController，支持 getDataBySQL、getDataByHttp 多种数据查询策略 |
| 转换器模式 | 应用位置：GoViewProjectConvert，使用 MapStruct 实现 DO 与 VO 之间的转换 |
| 适配器模式（UReport2） | 应用位置：UReport2DatabaseReportProvider，实现 UReport2 的 `ReportProvider`，把模板读写适配到数据库 |
| 缓存一致性模式 | 应用位置：UReport2ReportDefinitionCache，本地缓存模板定义 + Redis 版本号比对，实现多实例缓存失效 |
| 请求包装器模式 | 应用位置：UReport2SessionRequestWrapper（稳定 Session 编号）、UReport2ErrorLogRequestWrapper（异常日志脱敏） |
| 过滤器模式 | 应用位置：UReport2SecurityFilter，补齐 `/ureport/**` 的登录、租户、权限校验 |

### 数据表明细

`report_go_view_project`（GoView 大屏项目表）完整字段，实体 GoViewProjectDO 继承 BaseDO（含 id、creator、create_time、updater、update_time、deleted 基础字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID，自增 |
| name | VARCHAR(255) | 项目名称 |
| pic_url | VARCHAR(1024) | 预览图片URL |
| content | TEXT | 报表内容，JSON格式配置（历史 optional/go-view.sql 定义为 text；H2 测试脚本为 varchar） |
| status | TINYINT | 发布状态：0-已发布，1-未发布 |
| remark | VARCHAR(255) | 项目备注 |
| creator | VARCHAR(64) | 创建人 |
| create_time | DATETIME | 创建时间 |
| updater | VARCHAR(64) | 更新人 |
| update_time | DATETIME | 更新时间 |
| deleted | BIT(1) | 是否删除 |
| tenant_id | BIGINT | 租户编号（DO 中无此字段，租户插件自动补值与过滤；建表必须包含，见 pitfalls 1.1） |

索引：

| 索引名 | 字段 |
|--------|------|
| PRIMARY KEY | id |

> 除主键外无其它索引。该表建表语句不在当前仓库 `sql/` 中（历史 `sql/mysql/optional/go-view.sql` 已删除），历史脚本与 H2 测试脚本均只声明主键；`creator` 未单独建索引。

表关系（ER）：

| 来源表 | 关联表 | 关系 | 外键 | 说明 |
|--------|--------|------|------|------|
| report_go_view_project | system_users | N:1 | creator | 项目创建人关联用户表 |
| report_ureport_file | system_tenant | N:1 | tenant_id | UReport2 模板按租户隔离（逻辑关联） |

`report_ureport_file`（UReport2 报表模板表）完整字段，实体 UReport2FileDO 继承 TenantBaseDO（含 BaseDO 的审计字段与 tenant_id）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID，自增 |
| name | VARCHAR(128) | 模板名称，不含存储前缀，如 demo.ureport.xml |
| content | VARCHAR | UReport2 XML 模板内容，可能含数据源账号密码（测试 DDL 为 varchar NOT NULL，正式库可酌情改为 LONGTEXT） |
| creator | VARCHAR(64) | 创建人 |
| create_time | DATETIME | 创建时间 |
| updater | VARCHAR(64) | 更新人 |
| update_time | DATETIME | 更新时间 |
| deleted | BIT | 是否删除（逻辑删除，删除后可重建同名模板） |
| tenant_id | BIGINT | 租户编号，NOT NULL DEFAULT 0 |

索引：仅主键 `id`，无唯一索引（同名模板的并发新增没有数据库兜底）。
