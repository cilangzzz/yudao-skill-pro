# 制造执行系统模块 (mes)

> mes 模块是整个系统的"制造执行层"，提供主数据管理、排班日历、设备管理、工具管理、生产管理、质量控制、仓库管理等面向离散制造和流程制造的核心能力支撑。

## 模块概述

- **模块路径**: yudao-module-mes
- **业务定位**: 作为制造执行系统（MES），连接 ERP 计划层与车间执行层，实现生产过程的数字化管理
- **核心职责**: 主数据管理、生产排程、工艺路线、工单管理、质量检验、设备维保、仓库出入库、条码追溯

## 核心功能点

| 功能 | 说明 | 关键实体 |
|-----|------|---------|
| 主数据管理 | 物料、BOM、工艺路线、SOP/SIP、客户/供应商、车间/工位、自动编码规则 | ItemDO, ProductBomDO, RouteDO, WorkshopDO, WorkstationDO |
| 生产管理 | 工单管理（草稿->确认->完工/取消）、工序任务、流转卡、报工反馈、安灯呼叫 | WorkOrderDO, TaskDO, CardDO, FeedbackDO, AndonRecordDO |
| 质量管理 | 检验模板、检验指标、缺陷管理、来料检验(IQC)、过程检验(IPQC)、出货检验(OQC)、退货检验(RQC) | QcTemplateDO, QcIqcDO, QcIpqcDO, QcOqcDO, QcRqcDO |
| 设备管理 | 设备台账、设备类型、点检计划、点检记录、保养记录、维修管理 | MachineryDO, CheckPlanDO, CheckRecordDO, MaintenRecordDO, RepairDO |
| 工具管理 | 工具台账、工具类型 | ToolDO, ToolTypeDO |
| 仓库管理 | 仓库/库区/库位、物料库存、批次、条码/SN、到货通知、各类出入库、调拨、盘点、包装 | WarehouseDO, MaterialStockDO, BatchDO, BarcodeDO, TransferDO, StockTakingPlanDO |
| 排班日历 | 日历管理、节假日、排班计划、班组管理 | CalPlanDO, CalTeamDO, CalHolidayDO |
| 首页看板 | 订单汇总、工单状态、生产趋势统计 | - |

## API 接口索引

详细 API 文档按业务域拆分，参见以下文件：

| 业务域 | 文档 | 说明 |
|--------|------|------|
| 首页看板 | [api-home.md](api-home.md) | 订单汇总、工单状态、生产趋势 |
| 排班日历 | [api-calendar.md](api-calendar.md) | 日历、节假日、排班计划、班组管理 |
| 主数据 | [api-master-data.md](api-master-data.md) | 物料、BOM、SOP/SIP、客户/供应商、车间/工位、自动编码 |
| 生产管理 | [api-production.md](api-production.md) | 工单、任务、工艺路线、工序、流转卡、报工、安灯 |
| 质量管理 | [api-quality.md](api-quality.md) | 检验模板、指标、缺陷、IQC/IPQC/OQC/RQC |
| 设备管理 | [api-device.md](api-device.md) | 设备台账、点检计划/记录、保养记录、维修管理 |
| 工具管理 | [api-tool.md](api-tool.md) | 工具台账、工具类型 |
| 仓库管理 | [api-warehouse.md](api-warehouse.md) | 仓库、库存、批次、条码、出入库、调拨、盘点 |

### HTTP 接口分层

接口统一使用管理后台路径前缀：

- **管理后台（admin）**: 路径前缀 `/admin-api/mes/`

### 权限标识规范

所有接口遵循 `mes:功能:操作` 格式，例如：
- `mes:item:create` - 创建物料
- `mes:work-order:update` - 更新工单
- `mes:qc:iqc:query` - 查询来料检验

## 数据模型

详见 [data-model.md](data-model.md)，包含约 100 张数据表，按 8 个业务域组织：

```
MD (主数据) ──17 张表──> 物料/BOM/工艺/车间/工位/自动编码
PRO (生产)  ──17 张表──> 工单/任务/工艺路线/工序/流转卡/报工/安灯
QC (质量)   ──17 张表──> 检验模板/指标/缺陷/IQC/IPQC/OQC/RQC
DV (设备)   ──12 张表──> 设备台账/点检/保养/维修
TM (工具)   ── 2 张表──> 工具/工具类型
WM (仓库)   ──40+张表──> 仓库/库存/批次/条码/出入库/调拨/盘点
CAL (日历)  ── 7 张表──> 日历/节假日/排班/班组
```

## 设计模式

| 模式 | 位置 | 说明 |
|------|------|------|
| 策略模式 | AutoCodeRuleDO + AutoCodePartDO | 自动编码规则支持日期、固定字符、输入字符、序列号等零件组合 |
| 状态机模式 | WorkOrderDO, CardDO, FeedbackDO, RepairDO, TransferDO | 工单/流转卡/报工/维修/调拨的状态流转管理 |
| VO Assembly 模式 | 各 Controller 的 get/page 接口 | 批量获取关联实体后组装 VO，避免 N+1 查询 |
| 标准 CRUD 模式 | 全部 Controller/Service/Mapper | 统一的增删改查 + @PreAuthorize 权限控制 |
| 甘特图支持 | TaskDO, TaskController | 生产任务支持甘特图展示和拖拽调整 |
| Oracle/PG 兼容 | @KeySequence 注解 | 主键生成兼容 Oracle 和 PostgreSQL |
| 批量关联查询 | MesBizTypeConstants | 集中管理业务类型常量，用于批量查询关联数据 |

## 依赖关系

### 内部依赖

| 模块 | API | 用途 |
|-----|-----|------|
| yudao-module-system | AdminUserApi | 获取用户信息（工位操作员、报工人等） |
| yudao-module-system | RoleApi | 角色权限校验 |

### 外部依赖

| 库 | 用途 |
|---|------|
| MyBatis-Plus | ORM 框架，提供 CRUD 封装，BaseMapperX |
| Swagger/OpenAPI | API 文档注解 |
| MapStruct | VO/DO 对象映射转换 |
| Hutool | Java 工具类库 |

## 错误码范围

| 域 | 错误码前缀 | 说明 |
|----|-----------|------|
| 主数据 | 待确认 | 物料、BOM、工艺等不存在 |
| 生产 | 待确认 | 工单、任务、流转卡等不存在 |
| 质量 | 待确认 | 检验单、模板等不存在 |
| 设备 | 待确认 | 设备、点检计划等不存在 |
| 仓库 | 待确认 | 仓库、库存、批次等不存在 |

> 具体错误码定义参见 `ErrorCodeConstants.java`

## 详细文档

- [api-home.md](api-home.md) - 首页看板接口
- [api-calendar.md](api-calendar.md) - 排班日历接口
- [api-master-data.md](api-master-data.md) - 主数据管理接口
- [api-production.md](api-production.md) - 生产管理接口
- [api-quality.md](api-quality.md) - 质量管理接口
- [api-device.md](api-device.md) - 设备管理接口
- [api-tool.md](api-tool.md) - 工具管理接口
- [api-warehouse.md](api-warehouse.md) - 仓库管理接口
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项
