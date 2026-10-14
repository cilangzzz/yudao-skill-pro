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
| **使用指南总览** | 不确定选哪个场景 | [skills/usage/index.md](skills/usage/index.md) | 场景分类目录、使用流程图、FAQ |
| **实体类实现** | 从 SQL 到完整 CRUD 功能 | [skills/usage/entity-implementation.md](skills/usage/entity-implementation.md) | 建表 → DO → Mapper → Service → Controller 全流程 |
| **扩展模块** | 在现有模块添加新功能 | [skills/usage/extend-module.md](skills/usage/extend-module.md) | 渠道/策略/业务实体三种扩展模式 |
| **新增模块** | 创建全新业务模块 | [skills/usage/new-module.md](skills/usage/new-module.md) | 需求分析 → 架构 → 数据库 → 代码 → 测试 |
| **菜单权限配置** | 为新功能/新模块添加后台管理菜单与按钮 | [skills/usage/menu-permission.md](skills/usage/menu-permission.md) | 父菜单逐级查找 → 序列插入菜单/按钮 → 权限标识规范 |
| **改造模块** | 修改现有功能或重构 | [skills/usage/refactor-module.md](skills/usage/refactor-module.md) | 分析框架 + 风险评估 + 回滚策略 |
| **设计模式** | 工厂/策略/模板方法模式 | [skills/usage/pattern-usage.md](skills/usage/pattern-usage.md) | 多渠道系统设计模式组合指南 |
| **快速上手** | Skill 文档快速使用 | [skills/usage/quick-start.md](skills/usage/quick-start.md) | 提示词模板 + 代码片段速查 |
| **数据库操作** | 解析 yaml 凭证 + 委托 badseal/ssh-skill 执行 SQL + 自检 | [skills/db-ops/SKILL.md](skills/db-ops/SKILL.md) | 自动检测 ssh-skill / DB 类型，dry-run + 写操作事务，prod 需 YES-DESTRUCTIVE token |

---

## 模块功能文档（docs/）

19 个模块的详细功能文档（核心 15 个 + 补充 4 个：fms/oa/hrm/pms），由 `author-build-project-docs` 工作流生成。

> 总索引: [docs/README.md](docs/README.md) — 含模块依赖关系、数据模型统计

### 通用结构

每个模块目录下包含以下文档（api-{domain}.md 按业务域拆分，数量因模块而异；code-patterns.md 仅 15 个核心模块有；pitfalls.md 暂缺 system/mes；data-model.md 暂缺 mes）：

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
| system | [docs/modules/system/](docs/modules/system/README.md) | 用户、角色、权限、部门、租户 |
| infra | [docs/modules/infra/](docs/modules/infra/README.md) | 文件、配置、定时任务、日志、代码生成 |
| pay | [docs/modules/pay/](docs/modules/pay/README.md) | 订单、退款、钱包、转账、渠道、通知 |
| member | [docs/modules/member/](docs/modules/member/README.md) | 用户、等级、积分、签到、地址、标签 |
| mall | [docs/modules/mall/](docs/modules/mall/README.md) | 商品(SPU/SKU)、订单、促销、统计 |
| crm | [docs/modules/crm/](docs/modules/crm/README.md) | 客户、线索、商机、合同、回款、统计 |
| erp | [docs/modules/erp/](docs/modules/erp/README.md) | 采购、销售、库存、财务、产品 |
| bpm | [docs/modules/bpm/](docs/modules/bpm/README.md) | 模型、流程定义、实例、任务、表单 |
| ai | [docs/modules/ai/](docs/modules/ai/README.md) | 对话、图像、模型、知识库、音乐、写作 |
| iot | [docs/modules/iot/](docs/modules/iot/README.md) | 设备、产品、物模型、规则、OTA、告警 |
| mp | [docs/modules/mp/](docs/modules/mp/README.md) | 账号、用户、消息、素材、菜单、自动回复 |
| report | [docs/modules/report/](docs/modules/report/README.md) | GoView 项目、数据查询、积木报表 |
| im | [docs/modules/im/](docs/modules/im/README.md) | 单聊、群聊、消息收发、撤回、已读、RTC 通话、表情、频道 |
| mes | [docs/modules/mes/](docs/modules/mes/README.md) | 主数据、排班、设备、工装、生产、质检、仓库 |
| wms | [docs/modules/wms/](docs/modules/wms/README.md) | 仓库、物料、库存、入库、出库、调拨、盘点 |
| **fms**（补充） | [docs/modules/fms/](docs/modules/fms/README.md) | 账套、凭证、账簿、三大报表与期末结账 |
| **oa**（补充） | [docs/modules/oa/](docs/modules/oa/README.md) | 个人/企业协同、行政管理与人事财务审批 |
| **hrm**（补充） | [docs/modules/hrm/](docs/modules/hrm/README.md) | 员工档案、招聘、考勤、薪资、社保、绩效 |
| **pms**（补充） | [docs/modules/pms/](docs/modules/pms/README.md) | 项目/迭代/工作项、看板、工时与团队知识库 |

---

## 自动引用机制

使用样例（[使用样例总览](skills/usage/index.md)）文档头部以 YAML front matter 声明该场景需引用的规范，AI 读取时自动加载：

| 字段 | 作用 |
|-----|------|
| `design` | 设计规范文件列表（`path` + 引用 `reason`） |
| `module_guide` | `{prompt, mapping}` —— 模块名 → `docs/{module}/code-patterns.md` 映射 |
| `patterns` | 设计模式文件列表（`path` + 引用 `reason`） |
| `usage_hint` | 顶层提示语句，引导用户在提示词中指定模块名 |

**使用方式**: 在提示词中指定模块名（如「目标模块：pay」），AI 加载对应模块文档。完整示例见 [skills/usage/extend-module.md](skills/usage/extend-module.md) 头部。

---

## 设计规范索引

| 规范 | 路径 | 说明 |
|-----|------|------|
| 数据库设计 | [skills/design/db-designer.md](skills/design/db-designer.md) | 建表 SQL、字段命名、索引设计 |
| 实体类设计 | [skills/design/entity-designer.md](skills/design/entity-designer.md) | 继承体系、注解规范、命名转换 |
| API 接口设计 | [skills/design/api-designer.md](skills/design/api-designer.md) | Controller 注解、请求响应格式 |
| CRUD 代码生成 | [skills/design/crud-designer.md](skills/design/crud-designer.md) | 各层代码模板、命名规范 |
| SQL 文件管理 | [sql/README.md](sql/README.md) | SQL 目录组织（发版日期 / 模块 / 日期）与文件命名规范 |

---

## 设计模式索引

| 模式 | 路径 | 适用场景 |
|-----|------|---------|
| 模式选择指南 | [skills/design/patterns/index.md](skills/design/patterns/index.md) | 不确定用哪种模式时的选择与组合方案 |
| 工厂模式 | [skills/design/patterns/factory-pattern.md](skills/design/patterns/factory-pattern.md) | 根据条件创建不同类型的对象 |
| 策略模式 | [skills/design/patterns/strategy-pattern.md](skills/design/patterns/strategy-pattern.md) | 多种算法或策略间切换 |
| 模板方法模式 | [skills/design/patterns/template-method-pattern.md](skills/design/patterns/template-method-pattern.md) | 定义算法骨架，子类实现细节 |

---

## 规范速查索引

命名、错误码、权限标识、包路径等速查内容不在本文件维护，按粒度查两级出处，避免双处更新不一致：

| 粒度 | 出处 | 覆盖内容 |
|-----|------|---------|
| 通用规范 | [skills/design/crud-designer.md](skills/design/crud-designer.md)（`naming_standards`、`error_code`）· [skills/usage/entity-implementation.md](skills/usage/entity-implementation.md)「快速参考」 | 命名规范、权限标识格式、错误码格式与模块段号、各层目录树（前者机器可读，后者人类可读） |
| 模块实例 | [docs/README.md](docs/README.md) 派发的各模块 `docs/{module}/code-patterns.md`「异常处理」等章节 | 模块专属错误码前缀与清单、各层组件实例（章节标题因模块而异） |
