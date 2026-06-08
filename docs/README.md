# 芋道源码模块文档索引

> 基于 `author-build-project-docs` 工作流的 phase-5-business 规范生成，每个模块由独立子 agent 分析 `skills/modules/*/skill-*.yaml` 提取。

## 文档结构

每个模块文档包含：
- **README.md** — 模块概述、核心功能点、API 索引、数据模型概览、设计模式、依赖关系
- **api-{domain}.md** — 按业务域拆分的 API 详情（接口路径、参数、返回值、业务逻辑）
- **data-model.md** — 完整数据模型（表结构、字段定义、ER 关系）
- **pitfalls.md** — 已知踩坑点和注意事项

## 模块索引

| 模块 | 说明 | 核心功能 | API 域数 | 文件数 | 文档路径 |
|-----|------|---------|---------|--------|---------|
| **system** | 系统管理 | 用户、角色、权限、部门、租户、字典 | 5 | 8 | [docs/system/](system/README.md) |
| **infra** | 基础设施 | 文件、配置、定时任务、日志、代码生成 | 5 | 8 | [docs/infra/](infra/README.md) |
| **pay** | 支付 | 订单、退款、钱包、转账、渠道、通知 | 6 | 9 | [docs/pay/](pay/README.md) |
| **member** | 会员 | 用户、等级、积分、签到、地址、标签 | 7 | 10 | [docs/member/](member/README.md) |
| **mall** | 商城 | 商品(SPU/SKU)、订单、促销、统计 | 4 | 7 | [docs/mall/](mall/README.md) |
| **crm** | CRM | 客户、线索、商机、合同、回款、统计 | 10 | 13 | [docs/crm/](crm/README.md) |
| **erp** | ERP | 采购、销售、库存、财务、产品 | 5 | 8 | [docs/erp/](erp/README.md) |
| **bpm** | 工作流 | 模型、流程定义、实例、任务、表单 | 7 | 8 | [docs/bpm/](bpm/README.md) |
| **ai** | AI | 对话、图像、模型、知识库、音乐、写作 | 8 | 11 | [docs/ai/](ai/README.md) |
| **iot** | 物联网 | 设备、产品、物模型、规则、OTA、告警 | 6 | 9 | [docs/iot/](iot/README.md) |
| **mp** | 公众号 | 账号、用户、消息、素材、菜单、自动回复 | 10 | 13 | [docs/mp/](mp/README.md) |
| **report** | 报表 | GoView 项目、数据查询、积木报表 | 3 | 6 | [docs/report/](report/README.md) |

**合计: 12 个模块 / 100 个文档文件**

## 模块依赖关系

```
system (系统管理) ← 几乎所有模块都依赖
  │
  ├── infra (基础设施) ← 所有模块
  │
  ├── pay (支付) ← mall, member
  │   └── 依赖: system (用户), infra (文件)
  │
  ├── member (会员) ← mall, crm
  │   └── 依赖: system (用户), pay (钱包)
  │
  ├── mall (商城)
  │   └── 依赖: system, member, pay, product
  │
  ├── crm (CRM)
  │   └── 依赖: system (用户/部门)
  │
  ├── erp (ERP)
  │   └── 依赖: system (用户/部门)
  │
  ├── bpm (工作流)
  │   └── 依赖: system (用户/角色), Flowable 引擎
  │
  ├── ai (AI)
  │   └── 依赖: system (用户), Spring AI
  │
  ├── iot (物联网)
  │   └── 依赖: system (租户)
  │
  ├── mp (公众号)
  │   └── 依赖: system (用户), WxJava SDK
  │
  └── report (报表)
      └── 依赖: system (用户), infra (数据源)
```

## 数据模型统计

| 模块 | 表数量 | 关键表 |
|-----|--------|--------|
| system | 18 | admin_user, system_role, system_menu, system_dept, system_tenant |
| infra | 11 | infra_file, infra_config, infra_job, infra_api_access_log |
| pay | 9 | pay_order, pay_refund, pay_wallet, pay_channel |
| member | 11 | member_user, member_level, member_point |
| mall | 12 | product_spu, product_sku, trade_order, promotion_coupon |
| crm | 20 | crm_customer, crm_contract, crm_business, crm_clue |
| erp | 25 | erp_purchase_order, erp_sale_order, erp_stock, erp_finance |
| bpm | 16 | bpm_model, bpm_process_definition, bpm_task (8 自建 + 8 Flowable) |
| ai | 14 | ai_model, ai_chat_message, ai_image, ai_knowledge |
| iot | 12 | iot_device, iot_product, iot_thing_model |
| mp | 8 | mp_account, mp_user, mp_message, mp_menu |
| report | 1 | report_go_view_project |

## 生成方式

每个模块由独立子 agent 并行分析，遵循 `F:\work\flow\software-dev-ai-workflow\0.0-通用skill\author-build-project-docs` 的 phase-5-business 规范：
1. 读取 `skills/modules/{module}/skill-{module}.yaml` Skill 文档
2. 提取模块概述、功能点、API、数据模型、设计模式
3. 生成 README.md（索引）+ api-{domain}.md（详情）+ data-model.md + pitfalls.md
