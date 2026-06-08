# yudao-skill-pro

> 基于 yudao-vue-pro 的 AI 辅助开发知识库，通过 Skill 文档体系实现标准化代码生成。

## 🎯 项目特色

本分支在芋道源码基础上，构建了一套完整的 **AI Skill 开发规范体系**，让 AI 能够：

- 理解项目架构和代码规范
- 自动生成符合项目标准的 CRUD 代码
- 遵循设计模式和最佳实践
- 支持多模块业务场景

## 🆚 与上游仓库的区别

本仓库基于 [YunaiV/ruoyi-vue-pro](https://github.com/YunaiV/ruoyi-vue-pro) 同步代码，在其基础上新增了完整的 AI Skill 知识库体系。上游代码保持原样，以下为本仓库独有的内容：

| 新增内容 | 路径 | 说明 |
|---------|------|------|
| **Claude Code 配置** | `.claude/` | Claude Code 工作流配置 |
| **项目开发规范** | `CLAUDE.md` | 模块索引、命名规范、分层架构、错误码速查 |
| **模块功能文档** | `docs/` | 15 个模块的完整文档（API、数据模型、踩坑点），共 131 个文件 |
| **设计规范** | `skills/design/` | 数据库、实体类、API 接口、CRUD 代码生成 4 套规范 |
| **模块 Skill** | `skills/modules/` | 15 个业务模块的结构化 Skill YAML（架构、表结构、代码模式、扩展指南） |
| **设计模式** | `skills/patterns/` | 工厂、策略、模板方法 3 种设计模式实现指南 |
| **使用样例** | `skills/usage/` | 实体类实现、扩展模块、新增模块、改造模块等场景的提示词模板 |

> 同步方式：定期从 upstream/master 拉取最新代码合并，自定义文件始终保留。

## 📁 Skill 体系结构

```
skills/
├── design/                    # 设计规范
│   ├── db-designer.yaml      # 数据库设计规范
│   ├── entity-designer.yaml  # 实体类设计规范
│   ├── api-designer.yaml     # API 接口设计规范
│   └── crud-designer.yaml    # CRUD 代码生成规范
├── modules/                   # 模块 Skill
│   ├── system/               # 系统管理模块
│   ├── infra/                # 基础设施模块
│   ├── pay/                  # 支付模块
│   ├── member/               # 会员模块
│   ├── mall/                 # 商城模块
│   ├── crm/                  # CRM 模块
│   ├── erp/                  # ERP 模块
│   ├── bpm/                  # 工作流模块
│   ├── ai/                   # AI 模块
│   ├── iot/                  # 物联网模块
│   ├── mp/                   # 微信公众号模块
│   ├── report/               # 报表模块
│   ├── im/                   # 即时通讯模块
│   ├── mes/                  # 制造执行模块
│   └── wms/                  # 仓储管理模块
├── patterns/                  # 设计模式
│   ├── factory-pattern.yaml
│   ├── strategy-pattern.yaml
│   └── template-method-pattern.yaml
└── usage/                     # 使用样例
    ├── entity-implementation.md
    ├── extend-module.md
    ├── new-module.md
    └── ...
```

## 🚀 核心能力

### 1. 设计规范体系

| 规范 | 说明 |
|-----|------|
| 数据库设计 | 建表 SQL、字段命名、索引设计规范 |
| 实体类设计 | 继承体系、注解规范、命名转换规则 |
| API 接口设计 | Controller 注解、请求响应格式标准 |
| CRUD 代码生成 | 各层代码模板、命名规范 |

### 2. 模块化 Skill

每个业务模块都有对应的 Skill 文档，包含：
- 模块架构说明
- 核心实体关系
- 业务流程定义
- 代码生成规则

### 3. 设计模式支持

内置常用设计模式的实现指南：
- 工厂模式 - 根据条件创建不同类型的对象
- 策略模式 - 多种算法或策略间切换
- 模板方法模式 - 定义算法骨架，子类实现细节

### 4. 自动引用机制

使用样例文档通过 YAML front matter 声明依赖的规范文件，AI 自动加载相关规范：

```yaml
references:
  design:
    - skills/design/db-designer.yaml
    - skills/design/entity-designer.yaml
  module_guide:
    mapping:
      system: skills/modules/system/skill-system.yaml
```

## 📖 使用场景

| 场景 | 说明 | 文档 |
|-----|------|------|
| 实体类实现 | 从 SQL 到完整 CRUD 功能 | [usage/entity-implementation.md](skills/usage/entity-implementation.md) |
| 扩展模块 | 在现有模块添加新功能 | [usage/extend-module.md](skills/usage/extend-module.md) |
| 新增模块 | 创建全新业务模块 | [usage/new-module.md](skills/usage/new-module.md) |
| 改造模块 | 修改现有功能或重构 | [usage/refactor-module.md](skills/usage/refactor-module.md) |
| 设计模式 | 工厂/策略/模板方法模式 | [usage/pattern-usage.md](skills/usage/pattern-usage.md) |

## 🛠️ 技术栈

- **后端**: Spring Boot 2.7.18 / MyBatis Plus / MySQL / Redis
- **前端**: Vue 3 + Element Plus / Vben(ant-design-vue)
- **工作流**: Flowable
- **AI**: Spring AI

## 📝 命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 数据库表 | 小写下划线 | `mes_process` |
| DO 类 | `XxxDO` | `MesProcessDO` |
| Mapper | `XxxMapper` | `MesProcessMapper` |
| Service | `XxxService` | `MesProcessService` |
| Controller | `XxxController` | `MesProcessController` |
| VO | `XxxSaveReqVO` / `XxxRespVO` | `MesProcessSaveReqVO` |

## 📊 项目状态

- ✅ 15 个模块 Skill 已完成
- ✅ 4 个设计规范已定义
- ✅ 3 个设计模式已文档化
- ✅ 使用样例和自动引用机制已就绪

## 🔗 相关链接

- [芋道源码](https://github.com/YunaiV/ruoyi-vue-pro) - 原始项目
- [开发文档](https://doc.iocoder.cn/) - 芋道官方文档

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。
