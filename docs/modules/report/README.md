# 数据报表模块 (report)

> 基于积木报表（JimuReport）与积木仪表盘（JimuBI）提供数据可视化报表与大屏设计能力，内置 GoView 大屏项目管理与数据集查询 API，并集成 UReport2 提供中国式报表的设计、预览与导出。

## 模块概述

- **模块路径**: yudao-module-report（单模块布局，非多子模块）
- **业务定位**: 提供数据可视化报表能力，包括打印设计、报表设计、图形设计、大屏设计等。报表与仪表盘设计器整体由积木报表（jimureport-spring-boot-starter）与积木仪表盘（jimubi-spring-boot-starter）官方组件提供，本模块只做"薄壳集成"——负责将 yudao 的登录认证、租户、权限体系桥接给积木组件，并自带一套 GoView 大屏项目管理与数据集查询接口。此外，模块集成 UReport2（中国式报表），模板以 XML 存于 `report_ureport_file` 表并按租户隔离，通过自定义 `ReportProvider`（`db:` 前缀）实现数据库存储与多实例缓存一致性，并由自建 `UReport2SecurityFilter` 补齐 `/ureport/**` 的登录、租户与权限校验。
- **技术栈**: Spring Boot 2.7.18 / MyBatis-Plus / 积木报表 jimureport-spring-boot-starter 2.3.4 / 积木仪表盘 jimubi-spring-boot-starter 2.3.2 / UReport2 ureport2-spring-boot-starter 2.0.1（cn.iocoder 的 JDK8 适配分支）/ Redis / MapStruct / JdbcTemplate

## 设计原则

| 原则 | 说明 |
|-----|------|
| 薄壳集成 | 报表/大屏设计器的前后端能力整体委托给积木官方 starter，模块自身不实现设计器逻辑，只保留集成桥接与少量自研 API |
| Token 桥接 | 实现 JimuReport 的 `JmReportTokenServiceI`，把积木前端传递的 `X-Access-Token` 换为 yudao 的 `Authorization: Bearer` 头，复用 yudao OAuth2 Token 校验体系 |
| 安全豁免 + 内部认证 | `/jmreport/**`、`/drag/**`、`/jimubi/**` 在 Spring Security 层 `permitAll`，认证改由 `JmReportTokenServiceImpl.verifyToken` 完成，权限由 `getRoles`/`getPermissions` 映射（yudao 超管映射为积木 admin 及全部 drag、jmreport 权限指令） |
| 租户透传 | 积木报表前端请求不携带 `tenant-id` Header，通过 `getTenantId()` 从 LoginUser 补齐租户上下文；token 校验期间临时忽略租户以便查询 accessToken |
| 数据库存储模板 | UReport2 通过自定义 `ReportProvider`（前缀 `db:`）从 `report_ureport_file` 表读写 XML 模板，取代 UReport2 默认的文件存储；模板按租户隔离 |
| 多实例缓存一致性 | 解析后的模板定义仅缓存在本地（key = 租户编号:规范化模板名），Redis 只保存随机版本号；保存/删除先落库（无外层事务、自动提交）再刷新版本号，各实例版本号不一致即重新加载解析 |
| 过滤器补齐安全 | `/ureport/**` 不属于 `/admin-api`，`TenantSecurityWebFilter` 不处理，由自建 `UReport2SecurityFilter` 补齐登录校验（必须为 ADMIN 用户）、租户上下文注入与越权比对、租户合法性校验与权限分级 |
| 多数据库适配 | DO 使用 `@KeySequence` 兼容 Oracle、PostgreSQL、Kingbase、DB2、H2 的主键自增 |
| 数据直查 | GoView 数据集查询直接基于 `JdbcTemplate` 执行 SQL，返回 `dimensions`（列名元数据）+ `source`（明细行 Map 列表）的通用图表结构 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-----|------|---------|
| GoView 项目管理 | GoView 大屏项目的创建、更新、删除、查询与"我的项目"分页（按 creator 过滤） | GoViewProjectDO |
| GoView 数据查询 | 为大屏图表提供 SQL 数据集查询（JdbcTemplate 直查）与 HTTP 数据集查询示例接口 | 无（直连 JdbcTemplate） |
| 积木报表集成 | 打印设计、报表设计、图形设计等报表能力，Token/角色/租户/权限桥接 | 无（表由 starter 自建） |
| 积木仪表盘集成 | JimuBI 大屏/仪表盘设计能力，字典与日志扩展服务（按需启用） | 无（表由 starter 自建） |
| UReport2 中国式报表集成 | 模板以 XML 存于数据库（按租户隔离），支持设计、预览、打印与 Excel/PDF/Word 导出；多实例模板缓存通过 Redis 版本号保持一致；`/ureport/**` 由自建过滤器完成登录、租户与设计/查看权限分级校验；管理后台仅提供模板列表与删除 | UReport2FileDO |

## API 接口索引

### GoView 项目 (GoViewProjectController)

前缀：`/report/go-view/project`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /report/go-view/project/create | POST | 创建项目 | report:go-view-project:create |
| /report/go-view/project/update | PUT | 更新项目 | report:go-view-project:update |
| /report/go-view/project/delete | DELETE | 删除 GoView 项目 | report:go-view-project:delete |
| /report/go-view/project/get | GET | 获得项目 | report:go-view-project:query |
| /report/go-view/project/my-page | GET | 获得我的项目分页（按当前登录用户 creator 过滤） | report:go-view-project:query |

### GoView 数据 (GoViewDataController)

前缀：`/report/go-view/data`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /report/go-view/data/get-by-sql | 任意（@RequestMapping 未限定方法） | 使用 SQL 查询数据，返回 dimensions + source 结构 | report:go-view-data:get-by-sql |
| /report/go-view/data/get-by-http | 任意（@RequestMapping 未限定方法） | 使用 HTTP 查询数据（仅为示例接口，返回随机 PV/UV 数据，实际应为每个查询单独写接口） | report:go-view-data:get-by-http |

### UReport2 报表模板 (UReport2FileController)

前缀：`/report/ureport2/file`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /report/ureport2/file/page | GET | 获得 UReport2 报表模板分页（按 name 模糊匹配、id 倒序，不返回 content） | report:ureport:query 或 report:ureport:design |
| /report/ureport2/file/delete | DELETE | 按编号逻辑删除模板，并发布新版本号使各实例缓存失效 | report:ureport:design |

### UReport2 设计器 / 预览 / 导出 (UReportServlet，由 ureport2-spring-boot-starter 提供)

前缀：`/ureport/**`（代码不在本仓库，由 starter 的 `UReportServlet` 按 Action 分发；`UReport2SecurityFilter` 负责登录、租户与权限校验）

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /ureport/designer/**、/ureport/datasource/**、/ureport/import、/ureport/image 等 | 任意（按 Action 分发） | 报表设计、保存、删除、加载、脚本校验、数据源测试与 SQL 执行、导入等 | report:ureport:design |
| /ureport/preview/**、/ureport/excel(97)/**、/ureport/pdf/**、/ureport/word、/ureport/chart/storeData | 任意（按 Action 分发） | 已保存报表的预览、分页、打印与 Excel/PDF/Word 导出、图表图片回传；`_u` 参数必须以 `db:` 开头 | report:ureport:query（白名单内的 Action 才放行） |
| /ureport/res/ureport-asserts/** | GET | UReport2 设计器/预览页静态资源 | 无（permitAll，免登录） |

### 积木报表 / 积木仪表盘 (starter 提供，非本仓库代码)

报表与仪表盘的全部端点由 `jimureport-spring-boot-starter`（`/jmreport/**`）与 `jimubi-spring-boot-starter`（`/drag/**`、`/jimubi/**`）提供，代码不在本仓库中，不计入模块端点数。本模块通过以下桥接类完成集成：

| 桥接类 | 作用 |
|-------|------|
| JmReportTokenServiceImpl | 实现 JimuReport `JmReportTokenServiceI`：verifyToken 校验、getUsername 用户编号、getRoles 超管映射 jimu admin、getPermissions 映射 drag 权限指令、getTenantId 租户透传、customApiHeader 解决 API 数据集 Token 传递 |
| JmOnlDragExternalServiceImpl | 实现 JimuBI `IOnlDragExternalService`：字典、分类树、用户/部门字典与日志查询（当前为默认空实现，按需扩展） |
| SecurityConfiguration | 对 `/jmreport/**`、`/drag/**`、`/jimubi/**` 放行 Spring Security 过滤，并放行 `GET /ureport/res/ureport-asserts/**`（UReport2 静态资源） |
| JmReportConfiguration | `@ComponentScan("org.jeecg.modules.jmreport")` 扫描积木包并注册上述 Bean |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| report_go_view_project | GoView 项目表，每个大屏图表对应一个项目 | BaseDO | name（项目名称）、pic_url（预览图 URL）、content（报表内容，JSON 字符串）、status（发布状态，复用 CommonStatusEnum：0 已发布/1 未发布）、remark（备注） |
| report_ureport_file | UReport2 报表模板表，按租户隔离，存储 UReport2 的 XML 模板内容 | TenantBaseDO | name（模板名称，不含存储前缀，varchar(128)）、content（UReport2 XML 模板内容）、tenant_id（租户编号） |

> 说明：模块自建 2 张表，分别对应 GoViewProjectDO（BaseDO）与 UReport2FileDO（TenantBaseDO）。注意 `report_go_view_project` 虽只继承 BaseDO（DO 无 tenantId 字段），但租户插件仍会自动追加 `tenant_id` 条件，物理表必须含 `tenant_id` 列（见 [pitfalls.md](pitfalls.md) 1.1）。积木报表/仪表盘运行所需的 `jimu_*`、`onl_drag_*` 等表由官方 starter 维护，不属于本模块 DO。UReport2 另依赖 Redis 存储模板版本号（`report:ureport2_file_version:{tenantId}:{file}`）。

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 适配器模式 | JmReportTokenServiceImpl（实现 `JmReportTokenServiceI`）、JmOnlDragExternalServiceImpl（实现 `IOnlDragExternalService`） | 将积木报表/仪表盘的外部扩展点适配到 yudao 的 OAuth2 认证、权限（PermissionCommonApi）与租户上下文体系 |
| 适配器模式（UReport2） | UReport2DatabaseReportProvider（实现 `ReportProvider`） | 将 UReport2 的模板读写抽象适配到数据库存储（`report_ureport_file`），取代其默认文件存储 |
| 缓存一致性模式 | UReport2ReportDefinitionCache（实现 `ReportDefinitionCache`） | 本地缓存解析后的模板定义，Redis 只存版本号，通过版本号比对实现多实例缓存失效 |
| 请求包装器模式 | UReport2SessionRequestWrapper、UReport2ErrorLogRequestWrapper | 包装 HttpServletRequest，分别提供稳定 Session 编号与异常日志脱敏 |

## 依赖关系

- **上游**（本模块依赖）:
  - Framework starter: yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-biz-tenant、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-test
  - 业务模块: yudao-module-system（提供 `RoleCodeEnum` 超管角色编码；另通过 framework 的 OAuth2TokenCommonApi、PermissionCommonApi 完成 token 校验与权限查询）
  - 第三方: jimureport-spring-boot-starter 2.3.4（积木报表）、jimubi-spring-boot-starter 2.3.2（积木仪表盘）、ureport2-spring-boot-starter 2.0.1（UReport2，版本由 yudao-dependencies 管理）
  - 中间件: Redis（UReport2 模板版本号缓存；由 yudao-spring-boot-starter-redis 提供）
- **下游**（依赖本模块）: 无。模块在根 `pom.xml` 的 `<modules>` 与 `yudao-server/pom.xml` 的依赖中默认被注释，未随 yudao-server 启用；启用需手动取消两处注释。
- **运行期开关**: UReport2 由 `ureport.enabled` 控制（`@ConditionalOnProperty`，默认开启）；关闭后不注册模板缓存、ReportProvider 与 SecurityFilter，但 `UReport2FileService` 仍可保存与删除模板。

## 详细文档

- [api-goview-project.md](api-goview-project.md) - GoView 项目管理
- [api-goview-data.md](api-goview-data.md) - GoView 数据查询
- [api-jmreport.md](api-jmreport.md) - 积木报表集成
- [api-ureport2.md](api-ureport2.md) - UReport2 中国式报表集成
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
