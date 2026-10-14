# CLAUDE.md - 芋道源码 Skills 开发规范

> 本文件为 Claude Code 工作流模式提供项目开发规范索引和使用指南。

---

## 项目概述

基于 yudao-vue-pro（芋道源码）项目的 AI 辅助开发知识库，通过 Skill 文档体系实现标准化代码生成。

**技术栈**: Spring Boot 3.x / MyBatis-Plus / Swagger v3 / Spring AI / Flowable

---

## Skills 使用场景索引

| 场景 | 适用情况 | 文档路径 | 一句话描述 |
|-----|---------|---------|-----------|
| **实体类实现** | 从 SQL 到完整 CRUD 功能 | [skills/usage/entity-implementation.md](skills/usage/entity-implementation.md) | 建表 → DO → Mapper → Service → Controller 全流程 |
| **扩展模块** | 在现有模块添加新功能 | [skills/usage/extend-module.md](skills/usage/extend-module.md) | 渠道/策略/业务实体三种扩展模式 |
| **新增模块** | 创建全新业务模块 | [skills/usage/new-module.md](skills/usage/new-module.md) | 需求分析 → 架构 → 数据库 → 代码 → 测试 |
| **改造模块** | 修改现有功能或重构 | [skills/usage/refactor-module.md](skills/usage/refactor-module.md) | 分析框架 + 风险评估 + 回滚策略 |
| **设计模式** | 工厂/策略/模板方法模式 | [skills/usage/pattern-usage.md](skills/usage/pattern-usage.md) | 多渠道系统设计模式组合指南 |
| **快速上手** | Skill 文档快速使用 | [skills/usage/quick-start.md](skills/usage/quick-start.md) | 提示词模板 + 代码片段速查 |

---

## 模块功能文档（docs/）

15 个模块的详细功能文档，由 `author-build-project-docs` 工作流生成。

> 总索引: [docs/README.md](docs/README.md) — 含模块依赖关系、数据模型统计

### 通用结构

每个模块目录下包含以下文档（api-{domain}.md 按业务域拆分，数量因模块而异）：

| 文件 | 说明 |
|-----|------|
| README.md | 模块索引：概述、核心功能点、API 索引、数据模型概览、设计模式、依赖关系 |
| api-{domain}.md | 按业务域拆分的 API 详情（接口路径、参数、返回值、业务逻辑） |
| data-model.md | 完整数据模型（表结构、字段定义、ER 关系） |
| code-patterns.md | 模块代码模式、技术规范与扩展指南 |
| pitfalls.md | 已知踩坑点和注意事项 |

### 模块列表

| 模块 | 文档路径 | 核心功能 |
|-----|---------|---------|
| system | [docs/system/](docs/system/README.md) | 用户、角色、权限、部门、租户 |
| infra | [docs/infra/](docs/infra/README.md) | 文件、配置、定时任务、日志、代码生成 |
| pay | [docs/pay/](docs/pay/README.md) | 订单、退款、钱包、转账、渠道、通知 |
| member | [docs/member/](docs/member/README.md) | 用户、等级、积分、签到、地址、标签 |
| mall | [docs/mall/](docs/mall/README.md) | 商品(SPU/SKU)、订单、促销、统计 |
| crm | [docs/crm/](docs/crm/README.md) | 客户、线索、商机、合同、回款、统计 |
| erp | [docs/erp/](docs/erp/README.md) | 采购、销售、库存、财务、产品 |
| bpm | [docs/bpm/](docs/bpm/README.md) | 模型、流程定义、实例、任务、表单 |
| ai | [docs/ai/](docs/ai/README.md) | 对话、图像、模型、知识库、音乐、写作 |
| iot | [docs/iot/](docs/iot/README.md) | 设备、产品、物模型、规则、OTA、告警 |
| mp | [docs/mp/](docs/mp/README.md) | 账号、用户、消息、素材、菜单、自动回复 |
| report | [docs/report/](docs/report/README.md) | GoView 项目、数据查询、积木报表 |
| im | [docs/im/](docs/im/README.md) | 单聊、群聊、消息收发、撤回、已读、RTC 通话、表情、频道 |
| mes | [docs/mes/](docs/mes/README.md) | 主数据、排班、设备、工装、生产、质检、仓库 |
| wms | [docs/wms/](docs/wms/README.md) | 仓库、物料、库存、入库、出库、调拨、盘点 |

---

## 自动引用机制

使用样例文档头部包含 YAML front matter，声明需要引用的规范文件：

```yaml
references:
  design:
    - skills/design/db-designer.yaml      # 数据库设计规范
    - skills/design/entity-designer.yaml   # 实体类设计规范
    - skills/design/api-designer.yaml      # API 接口设计规范
    - skills/design/crud-designer.yaml     # CRUD 代码生成规范
  module_guide:
    mapping:
      system: docs/system/code-patterns.md
      infra: docs/infra/code-patterns.md
      im: docs/im/code-patterns.md
      mes: docs/mes/code-patterns.md
      wms: docs/wms/code-patterns.md
      # ... 其余模块见上方「模块列表」，code-patterns 路径为 docs/{module}/code-patterns.md
```

**使用方式**: 在提示词中指定模块名，AI 自动加载对应规范和模块 skill。

---

## 设计规范索引

| 规范 | 路径 | 说明 |
|-----|------|------|
| 数据库设计 | [skills/design/db-designer.yaml](skills/design/db-designer.yaml) | 建表 SQL、字段命名、索引设计 |
| 实体类设计 | [skills/design/entity-designer.yaml](skills/design/entity-designer.yaml) | 继承体系、注解规范、命名转换 |
| API 接口设计 | [skills/design/api-designer.yaml](skills/design/api-designer.yaml) | Controller 注解、请求响应格式 |
| CRUD 代码生成 | [skills/design/crud-designer.yaml](skills/design/crud-designer.yaml) | 各层代码模板、命名规范 |
| SQL 文件管理 | [sql/README.md](sql/README.md) | SQL 目录组织（发版日期 / 模块 / 日期）与文件命名规范 |

---

## 设计模式索引

| 模式 | 路径 | 适用场景 |
|-----|------|---------|
| 工厂模式 | [skills/design/patterns/factory-pattern.yaml](skills/design/patterns/factory-pattern.yaml) | 根据条件创建不同类型的对象 |
| 策略模式 | [skills/design/patterns/strategy-pattern.yaml](skills/design/patterns/strategy-pattern.yaml) | 多种算法或策略间切换 |
| 模板方法模式 | [skills/design/patterns/template-method-pattern.yaml](skills/design/patterns/template-method-pattern.yaml) | 定义算法骨架，子类实现细节 |

---

## 规范速查索引

命名规范、错误码前缀、分层包路径等速查表已在规范文档中维护，此处仅保留索引，避免双处更新不一致：

| 速查项 | 权威出处 | 内容说明 |
|-------|---------|---------|
| 命名规范速查 | [skills/usage/entity-implementation.md](skills/usage/entity-implementation.md) · [skills/design/crud-designer.yaml](skills/design/crud-designer.yaml)（`naming_standards`） | 表/DO/Mapper/Service/Controller/VO 命名与权限标识格式 |
| 错误码前缀速查 | [skills/usage/quick-start.md](skills/usage/quick-start.md) §4.2 · [skills/design/crud-designer.yaml](skills/design/crud-designer.yaml)（`error_code.module_codes`） | 各模块错误码前缀与示例 |
| 分层架构路径 | [skills/usage/entity-implementation.md](skills/usage/entity-implementation.md) 包路径规范 | `cn.iocoder.yudao.module.{模块}` 各层目录树 |
