# 数据报表模块 (report)

> 基于积木报表（JimuReport）与积木仪表盘（JimuBI）提供数据可视化报表与大屏设计能力，并内置 GoView 大屏项目管理与数据集查询 API。

## 模块概述

- **模块路径**: yudao-module-report（单模块布局，非多子模块）
- **业务定位**: 提供数据可视化报表能力，包括打印设计、报表设计、图形设计、大屏设计等。报表与仪表盘设计器整体由积木报表（jimureport-spring-boot-starter）与积木仪表盘（jimubi-spring-boot-starter）官方组件提供，本模块只做"薄壳集成"——负责将 yudao 的登录认证、租户、权限体系桥接给积木组件，并自带一套 GoView 大屏项目管理与数据集查询接口。
- **技术栈**: Spring Boot 2.7.18 / MyBatis-Plus / 积木报表 jimureport-spring-boot-starter 2.3.4 / 积木仪表盘 jimubi-spring-boot-starter 2.3.2 / MapStruct / JdbcTemplate

## 设计原则

| 原则 | 说明 |
|-----|------|
| 薄壳集成 | 报表/大屏设计器的前后端能力整体委托给积木官方 starter，模块自身不实现设计器逻辑，只保留集成桥接与少量自研 API |
| Token 桥接 | 实现 JimuReport 的 `JmReportTokenServiceI`，把积木前端传递的 `X-Access-Token` 换为 yudao 的 `Authorization: Bearer` 头，复用 yudao OAuth2 Token 校验体系 |
| 安全豁免 + 内部认证 | `/jmreport/**`、`/drag/**`、`/jimubi/**` 在 Spring Security 层 `permitAll`，认证改由 `JmReportTokenServiceImpl.verifyToken` 完成，权限由 `getRoles`/`getPermissions` 映射（yudao 超管映射为积木 admin 及全部 drag 权限指令） |
| 租户透传 | 积木报表前端请求不携带 `tenant-id` Header，通过 `getTenantId()` 从 LoginUser 补齐租户上下文；token 校验期间临时忽略租户以便查询 accessToken |
| 多数据库适配 | DO 使用 `@KeySequence` 兼容 Oracle、PostgreSQL、Kingbase、DB2、H2 的主键自增 |
| 数据直查 | GoView 数据集查询直接基于 `JdbcTemplate` 执行 SQL，返回 `dimensions`（列名元数据）+ `source`（明细行 Map 列表）的通用图表结构 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-----|------|---------|
| GoView 项目管理 | GoView 大屏项目的创建、更新、删除、查询与"我的项目"分页（按 creator 过滤） | GoViewProjectDO |
| GoView 数据查询 | 为大屏图表提供 SQL 数据集查询（JdbcTemplate 直查）与 HTTP 数据集查询示例接口 | 无（直连 JdbcTemplate） |
| 积木报表集成 | 打印设计、报表设计、图形设计等报表能力，Token/角色/租户/权限桥接 | 无（表由 starter 自建） |
| 积木仪表盘集成 | JimuBI 大屏/仪表盘设计能力，字典与日志扩展服务（按需启用） | 无（表由 starter 自建） |

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

### 积木报表 / 积木仪表盘 (starter 提供，非本仓库代码)

报表与仪表盘的全部端点由 `jimureport-spring-boot-starter`（`/jmreport/**`）与 `jimubi-spring-boot-starter`（`/drag/**`、`/jimubi/**`）提供，代码不在本仓库中，不计入模块端点数。本模块通过以下桥接类完成集成：

| 桥接类 | 作用 |
|-------|------|
| JmReportTokenServiceImpl | 实现 JimuReport `JmReportTokenServiceI`：verifyToken 校验、getUsername 用户编号、getRoles 超管映射 jimu admin、getPermissions 映射 drag 权限指令、getTenantId 租户透传、customApiHeader 解决 API 数据集 Token 传递 |
| JmOnlDragExternalServiceImpl | 实现 JimuBI `IOnlDragExternalService`：字典、分类树、用户/部门字典与日志查询（当前为默认空实现，按需扩展） |
| SecurityConfiguration | 对 `/jmreport/**`、`/drag/**`、`/jimubi/**` 放行 Spring Security 过滤 |
| JmReportConfiguration | `@ComponentScan("org.jeecg.modules.jmreport")` 扫描积木包并注册上述 Bean |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| report_go_view_project | GoView 项目表，每个大屏图表对应一个项目 | BaseDO | name（项目名称）、pic_url（预览图 URL）、content（报表内容，JSON 字符串）、status（发布状态，复用 CommonStatusEnum：0 已发布/1 未发布）、remark（备注） |

> 说明：模块仅自建 1 张表。积木报表/仪表盘运行所需的 `jimu_*`、`onl_drag_*` 等表由官方 starter 维护，不属于本模块 DO。

## 设计模式

| 模式 | 应用位置 | 用途 |
|-----|---------|------|
| 适配器模式 | JmReportTokenServiceImpl（实现 `JmReportTokenServiceI`）、JmOnlDragExternalServiceImpl（实现 `IOnlDragExternalService`） | 将积木报表/仪表盘的外部扩展点适配到 yudao 的 OAuth2 认证、权限（PermissionCommonApi/PermissionApi）与租户上下文体系 |

## 依赖关系

- **上游**（本模块依赖）:
  - Framework starter: yudao-spring-boot-starter-web、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-biz-tenant、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-test
  - 业务模块: yudao-module-system（PermissionApi 超管角色判断；另通过 framework 的 OAuth2TokenCommonApi、PermissionCommonApi 完成 token 校验与权限查询）
  - 第三方: jimureport-spring-boot-starter 2.3.4（积木报表）、jimubi-spring-boot-starter 2.3.2（积木仪表盘）
- **下游**（依赖本模块）: 无。模块在根 `pom.xml` 的 `<modules>` 与 `yudao-server/pom.xml` 的依赖中默认被注释，未随 yudao-server 启用；启用需手动取消两处注释。

## 详细文档

- [api-goview-project.md](api-goview-project.md) - GoView 项目管理
- [api-goview-data.md](api-goview-data.md) - GoView 数据查询
- [api-jmreport.md](api-jmreport.md) - 积木报表集成
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
