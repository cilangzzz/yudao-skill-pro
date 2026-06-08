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

12 个模块的详细功能文档，由 `author-build-project-docs` 工作流生成。

> 总索引: [docs/README.md](docs/README.md) — 含模块依赖关系、数据模型统计

| 模块 | 文档路径 | 功能点 | API 域数 | 表数量 |
|-----|---------|-------|---------|--------|
| system | [docs/system/](docs/system/README.md) | 用户、角色、权限、部门、租户 | 5 | 18 |
| infra | [docs/infra/](docs/infra/README.md) | 文件、配置、定时任务、日志、代码生成 | 5 | 11 |
| pay | [docs/pay/](docs/pay/README.md) | 订单、退款、钱包、转账、渠道、通知 | 6 | 9 |
| member | [docs/member/](docs/member/README.md) | 用户、等级、积分、签到、地址、标签 | 7 | 11 |
| mall | [docs/mall/](docs/mall/README.md) | 商品(SPU/SKU)、订单、促销、统计 | 4 | 12 |
| crm | [docs/crm/](docs/crm/README.md) | 客户、线索、商机、合同、回款、统计 | 10 | 20 |
| erp | [docs/erp/](docs/erp/README.md) | 采购、销售、库存、财务、产品 | 5 | 25 |
| bpm | [docs/bpm/](docs/bpm/README.md) | 模型、流程定义、实例、任务、表单 | 7 | 16 |
| ai | [docs/ai/](docs/ai/README.md) | 对话、图像、模型、知识库、音乐、写作 | 8 | 14 |
| iot | [docs/iot/](docs/iot/README.md) | 设备、产品、物模型、规则、OTA、告警 | 6 | 12 |
| mp | [docs/mp/](docs/mp/README.md) | 账号、用户、消息、素材、菜单、自动回复 | 10 | 8 |
| report | [docs/report/](docs/report/README.md) | GoView 项目、数据查询、积木报表 | 3 | 1 |

每个模块目录下包含：README.md（索引）+ api-{domain}.md（API 详情）+ data-model.md（数据模型）+ pitfalls.md（踩坑点）

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
      system: skills/modules/system/skill-system.yaml
      infra: skills/modules/infra/skill-infra.yaml
      # ... 更多模块见下方索引
```

**使用方式**: 在提示词中指定模块名，AI 自动加载对应规范和模块 skill。

---

## 模块 Skill 文档索引

| 模块 | 文档路径 | 核心功能 |
|-----|---------|---------|
| system | [skills/modules/system/skill-system.yaml](skills/modules/system/skill-system.yaml) | 用户、角色、权限、菜单、租户、字典 |
| infra | [skills/modules/infra/skill-infra.yaml](skills/modules/infra/skill-infra.yaml) | 文件、配置、任务、日志、代码生成 |
| pay | [skills/modules/pay/skill-pay.yaml](skills/modules/pay/skill-pay.yaml) | 支付、退款、钱包、转账 |
| member | [skills/modules/member/skill-member.yaml](skills/modules/member/skill-member.yaml) | 会员、积分、等级、签到 |
| mall | [skills/modules/mall/skill-mall.yaml](skills/modules/mall/skill-mall.yaml) | 商品、订单、促销、统计 |
| crm | [skills/modules/crm/skill-crm.yaml](skills/modules/crm/skill-crm.yaml) | 线索、客户、商机、合同、回款 |
| erp | [skills/modules/erp/skill-erp.yaml](skills/modules/erp/skill-erp.yaml) | 采购、销售、库存、财务 |
| bpm | [skills/modules/bpm/skill-bpm.yaml](skills/modules/bpm/skill-bpm.yaml) | 流程定义、流程实例、任务 |
| ai | [skills/modules/ai/skill-ai.yaml](skills/modules/ai/skill-ai.yaml) | AI 模型、对话、绘图 |
| iot | [skills/modules/iot/skill-iot.yaml](skills/modules/iot/skill-iot.yaml) | 设备、产品、物模型 |
| mp | [skills/modules/mp/skill-mp.yaml](skills/modules/mp/skill-mp.yaml) | 公众号、菜单、消息 |
| report | [skills/modules/report/skill-report.yaml](skills/modules/report/skill-report.yaml) | 报表、数据源、图表 |

---

## 设计规范索引

| 规范 | 路径 | 说明 |
|-----|------|------|
| 数据库设计 | [skills/design/db-designer.yaml](skills/design/db-designer.yaml) | 建表 SQL、字段命名、索引设计 |
| 实体类设计 | [skills/design/entity-designer.yaml](skills/design/entity-designer.yaml) | 继承体系、注解规范、命名转换 |
| API 接口设计 | [skills/design/api-designer.yaml](skills/design/api-designer.yaml) | Controller 注解、请求响应格式 |
| CRUD 代码生成 | [skills/design/crud-designer.yaml](skills/design/crud-designer.yaml) | 各层代码模板、命名规范 |

---

## 设计模式索引

| 模式 | 路径 | 适用场景 |
|-----|------|---------|
| 工厂模式 | [skills/patterns/factory-pattern.yaml](skills/patterns/factory-pattern.yaml) | 根据条件创建不同类型的对象 |
| 策略模式 | [skills/patterns/strategy-pattern.yaml](skills/patterns/strategy-pattern.yaml) | 多种算法或策略间切换 |
| 模板方法模式 | [skills/patterns/template-method-pattern.yaml](skills/patterns/template-method-pattern.yaml) | 定义算法骨架，子类实现细节 |

---

## 命名规范速查

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 数据库表 | 小写下划线 | `mes_process` |
| DO 类 | `XxxDO` | `MesProcessDO` |
| Mapper | `XxxMapper` | `MesProcessMapper` |
| Service 接口 | `XxxService` | `MesProcessService` |
| Service 实现 | `XxxServiceImpl` | `MesProcessServiceImpl` |
| Controller | `XxxController` | `MesProcessController` |
| 保存 VO | `XxxSaveReqVO` | `MesProcessSaveReqVO` |
| 分页 VO | `XxxPageReqVO` | `MesProcessPageReqVO` |
| 响应 VO | `XxxRespVO` | `MesProcessRespVO` |
| 权限标识 | `模块:功能:操作` | `mes:process:create` |

---

## 错误码前缀速查

| 模块 | 前缀 | 示例 |
|------|------|------|
| infra | `1_001_XXX_XXX` | 1_001_000_000 文件不存在 |
| system | `1_002_XXX_XXX` | 1_002_000_000 登录失败 |
| member | `1_004_XXX_XXX` | 1_004_001_000 用户不存在 |
| pay | `1_007_XXX_XXX` | 1_007_002_000 支付订单不存在 |
| product | `1_008_XXX_XXX` | 1_008_005_000 商品不存在 |
| trade | `1_011_XXX_XXX` | 1_011_000_011 订单不存在 |
| promotion | `1_013_XXX_XXX` | 1_013_004_000 优惠券模板不存在 |

---

## 分层架构路径

```
cn.iocoder.yudao.module.{模块}
├── controller/admin/{功能}/          # Controller + VO
├── service/{功能}/                   # Service 接口 + 实现
├── dal/dataobject/{功能}/            # DO 实体
├── dal/mysql/{功能}/                 # Mapper
└── enums/                            # 错误码 + 枚举
```
