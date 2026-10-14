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

错误码前缀：`1_003_000_000`

| 错误码 | 消息 | 常量名 |
|-------|------|--------|
| 1_003_000_000 | GoView 项目不存在 | GO_VIEW_PROJECT_NOT_EXISTS |

使用方式：

```java
if (goViewProjectMapper.selectById(id) == null) {
    throw exception(GO_VIEW_PROJECT_NOT_EXISTS);
}
```

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE)`

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

### 最佳实践

- 数据查询时考虑性能，大数据量场景建议使用 ClickHouse 等列式数据库
- 报表内容使用 JSON 格式存储，前端负责解析渲染
- 项目创建时默认状态为未发布（status=1），需手动发布
- 使用 creator 字段实现数据隔离，用户只能看到自己创建的项目
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
| spring-boot-starter-jdbc | Spring Boot 管理 | JdbcTemplate 数据源查询 |
| mapstruct | 管理在父 POM | 对象转换 |

模块无消息队列依赖；Framework starter 依赖（web/security/mybatis/biz-tenant/excel/test）见 [README](README.md) 的依赖关系一节。

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
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/enums/ErrorCodeConstants.java | 错误码定义 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/mysql/goview/GoViewProjectMapper.java | 项目数据访问 Mapper |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/convert/goview/GoViewProjectConvert.java | 对象转换器（MapStruct） |

## 领域模型

聚合根与值对象：

| 对象 | 类型 | 说明 |
|------|------|------|
| GoViewProject | 聚合根 | 大屏报表项目，包含项目配置、发布状态、报表内容等；对应实体 GoViewProjectDO，关联值对象 GoViewDataRespVO |
| GoViewDataRespVO | 值对象 | 数据响应结构，包含维度（dimensions）和数据明细（source） |
| GoViewProjectCreateReqVO | 值对象 | 项目创建请求参数 |
| GoViewProjectUpdateReqVO | 值对象 | 项目更新请求参数 |

领域服务：

| 服务 | 类型 | 说明 |
|------|------|------|
| GoViewProjectService | 领域服务 | 管理大屏项目的创建、更新、删除、查询 |
| GoViewDataService | 领域服务 | 提供数据查询能力，支持 SQL/HTTP 等数据源 |

## 设计与架构补充

### 分层架构

| 层 | 职责 | 组件 |
|----|------|------|
| controller | HTTP 接口层，提供 REST API | GoViewProjectController（大屏项目管理接口）、GoViewDataController（数据查询接口，SQL/HTTP） |
| service | 业务逻辑层 | GoViewProjectService/GoViewProjectServiceImpl（项目管理业务逻辑）、GoViewDataService/GoViewDataServiceImpl（数据查询业务逻辑） |
| dal | 数据访问层 | GoViewProjectMapper（项目数据访问）、GoViewProjectDO（项目实体） |
| convert | 对象转换层 | GoViewProjectConvert（DO/VO 对象转换，MapStruct） |
| framework | 框架集成层 | JmReportConfiguration、JmReportTokenServiceImpl、JmOnlDragExternalServiceImpl、SecurityConfiguration（各桥接类职责详见 [README](README.md)） |

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

### 数据表明细

`report_go_view_project`（GoView 大屏项目表）完整字段，实体 GoViewProjectDO 继承 BaseDO（含 id、creator、create_time、updater、update_time、deleted 基础字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID，自增 |
| name | VARCHAR(255) | 项目名称 |
| pic_url | VARCHAR(1024) | 预览图片URL |
| content | LONGTEXT | 报表内容，JSON格式配置 |
| status | TINYINT | 发布状态：0-已发布，1-未发布 |
| remark | VARCHAR(255) | 项目备注 |
| creator | VARCHAR(64) | 创建人 |
| create_time | DATETIME | 创建时间 |
| updater | VARCHAR(64) | 更新人 |
| update_time | DATETIME | 更新时间 |
| deleted | BIT | 是否删除 |

索引：

| 索引名 | 字段 |
|--------|------|
| idx_creator | creator |

表关系（ER）：

| 来源表 | 关联表 | 关系 | 外键 | 说明 |
|--------|--------|------|------|------|
| report_go_view_project | system_users | N:1 | creator | 项目创建人关联用户表 |
