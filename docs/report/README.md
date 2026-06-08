# Report 模块文档

> 模块路径：`yudao-module-report`
> 技能版本：1.0.0 | 创建日期：2026-03-18

## 1. 模块概述

report 模块是企业级应用的**可视化报表解决方案**，与业务模块解耦，提供独立的数据展示能力。核心集成两大报表引擎：

- **积木报表（JimuReport）**：提供打印设计、报表设计、图形设计、大屏设计能力
- **GoView 大屏设计器**：提供可视化大屏报表设计，支持 SQL 和 HTTP 数据源

## 2. 核心功能

| 功能域 | 能力 | 说明 |
|--------|------|------|
| GoView 项目管理 | CRUD、分页查询 | 大屏项目的全生命周期管理，支持按用户隔离 |
| GoView 数据查询 | SQL 查询、HTTP 查询 | 多策略数据源查询，返回统一 dimensions/source 结构 |
| 积木报表集成 | 报表设计、打印、图形 | 通过 JimuReport Starter 集成，支持 Token 认证适配 |
| 积木仪表盘 | 大屏设计器 | 通过 JimuBI Starter 集成，扩展拖拽式仪表盘 |

## 3. API 索引

本模块 API 按业务域拆分为三份文档：

| 业务域 | 文档 | 路径前缀 | 说明 |
|--------|------|----------|------|
| GoView 项目管理 | [api-goview-project.md](./api-goview-project.md) | `/report/go-view/project` | 大屏项目的增删改查 |
| GoView 数据查询 | [api-goview-data.md](./api-goview-data.md) | `/report/go-view/data` | SQL/HTTP 数据源查询 |
| 积木报表集成 | [api-jmreport.md](./api-jmreport.md) | 由 JimuReport 框架托管 | Token 认证、权限校验等扩展点 |

## 4. 数据模型

详细数据模型参见 [data-model.md](./data-model.md)。

### 核心实体

| 实体 | 表名 | 说明 |
|------|------|------|
| `GoViewProjectDO` | `report_go_view_project` | GoView 大屏项目，继承 `BaseDO` |

### 实体继承体系

```
BaseDO
  ├── id          (BIGINT, 主键)
  ├── creator     (VARCHAR(64), 创建人)
  ├── create_time (DATETIME)
  ├── updater     (VARCHAR(64), 更新人)
  ├── update_time (DATETIME)
  └── deleted     (BIT, 逻辑删除)
```

### 表关系

| 关系 | 外键 | 说明 |
|------|------|------|
| `report_go_view_project` -> `system_users` | `creator` | N:1，项目创建人关联用户表 |

## 5. 设计模式

| 模式 | 位置 | 用途 |
|------|------|------|
| **适配器模式** | `JmReportTokenServiceImpl` | 将 yudao OAuth2 认证体系适配到积木报表 `JmReportTokenServiceI` 接口 |
| **策略模式** | `GoViewDataController` | 支持多种数据查询策略：`getDataBySQL`、`getDataByHttp` |
| **转换器模式** | `GoViewProjectConvert` | 使用 MapStruct 实现 DO 与 VO 之间的转换 |
| **单一职责** | 整体架构 | GoViewProject 负责项目管理，GoViewData 负责数据查询 |
| **依赖倒置** | Service 层 | Service 依赖接口而非实现，便于测试和扩展 |

## 6. 架构分层

```
controller/admin/     -- HTTP 接口层（REST API）
  ├── GoViewProjectController   -- 大屏项目管理接口
  └── GoViewDataController      -- 数据查询接口（SQL/HTTP）

service/              -- 业务逻辑层
  ├── GoViewProjectService      -- 项目管理
  └── GoViewDataService         -- 数据查询

dal/                  -- 数据访问层
  ├── mysql/GoViewProjectMapper -- MyBatis-Plus Mapper
  └── dataobject/GoViewProjectDO -- 实体类

convert/              -- 对象转换层（MapStruct）

framework/            -- 框架集成层
  ├── JmReportConfiguration           -- 积木报表配置
  ├── JmReportTokenServiceImpl        -- Token 认证适配
  ├── JmOnlDragExternalServiceImpl    -- 积木仪表盘扩展
  └── SecurityConfiguration           -- 安全配置
```

## 7. 依赖关系

### 内部模块依赖

| 模块 | API | 用途 |
|------|-----|------|
| `system` | `OAuth2TokenCommonApi` | 积木报表 Token 验证 |
| `system` | `PermissionCommonApi` | 积木报表权限校验 |

### 外部依赖

| 依赖 | 用途 |
|------|------|
| `jimureport-spring-boot-starter` | 积木报表核心，提供报表设计器 |
| `jimubi-spring-boot-starter` | 积木仪表盘/大屏设计器 |
| `spring-boot-starter-jdbc` | JdbcTemplate 数据源查询 |
| `mapstruct` | DO/VO 对象转换 |

## 8. 关键文件清单

| 文件 | 用途 |
|------|------|
| `dal/dataobject/goview/GoViewProjectDO.java` | GoView 项目实体类 |
| `dal/mysql/goview/GoViewProjectMapper.java` | 项目数据访问 Mapper |
| `service/goview/GoViewProjectService.java` | 项目管理服务接口 |
| `service/goview/GoViewDataServiceImpl.java` | 数据查询服务实现（核心 SQL 查询逻辑） |
| `controller/admin/goview/GoViewProjectController.java` | 项目管理 HTTP 接口 |
| `controller/admin/goview/GoViewDataController.java` | 数据查询 HTTP 接口 |
| `convert/goview/GoViewProjectConvert.java` | MapStruct 对象转换器 |
| `framework/jmreport/config/JmReportConfiguration.java` | 积木报表配置类 |
| `framework/jmreport/core/service/JmReportTokenServiceImpl.java` | 积木报表 Token 认证适配器 |
| `enums/ErrorCodeConstants.java` | 错误码定义 |

## 9. 详细文档

- [GoView 项目管理 API](./api-goview-project.md)
- [GoView 数据查询 API](./api-goview-data.md)
- [积木报表集成](./api-jmreport.md)
- [数据模型](./data-model.md)
- [踩坑与注意事项](./pitfalls.md)
