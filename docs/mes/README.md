# 制造执行系统模块 (mes)

> 面向离散制造的制造执行系统（MES），打通 主数据 → 排班 → 设备/工装 → 生产执行 → 质量检验 → 仓储物流 的全链路业务闭环。

## 模块概述

- **模块路径**: `yudao-module-mes`
- **业务定位**: 提供制造企业车间级执行管理能力：以物料/BOM/工作站等主数据为基础，围绕生产工单驱动任务派工、报工、流转卡与安灯呼叫；通过 IQC/IPQC/OQC/RQC 四类检验单管控质量；以"主表-行-明细"单据体系管理采购/领料/生产/销售/外协/杂项/退货等全部出入库场景，并用库存事务流水保证库存台账可追溯。
- **技术栈**: Spring Boot 2.7.18（JDK8 分支，`javax.*` 命名空间）、MyBatis-Plus 3.5.17、Redis（编码流水号并发控制）、EasyExcel（批量导入导出）、Spring Security（方法级 `@PreAuthorize`）、springdoc-openapi（Swagger 分组）。单 jar 模块，无子模块。

## 设计原则

| 原则 | 说明 |
|------|------|
| 主数据一体化共享 | `md` 域为全模块提供物料、BOM、客户、供应商、计量单位、车间/工作站等基础数据，其他域 Service/Controller 直接注入 md 域 Service 批量拼接 VO（如工单列表回填产品/客户/供应商/单位名称） |
| 单据"主表-行-明细"三段式 | wm 出入库单据统一采用 主表（单据头）+ Line（单据行）+ Detail（库存明细，锁定来源库存）三层 DO 结构 |
| 库存事务流水驱动 | 所有库存数量变动统一经 `MesWmMaterialStockService#updateMaterialStockQuantity` 更新台账，并写入 `mes_wm_transaction` 事务流水（type/bizType/bizId），保证任意库存变动可追溯 |
| 状态与业务类型中央注册 | `MesOrderStatusConstants`（单据状态）与 `MesBizTypeConstants`（业务类型编号分段）集中管理，各域枚举引用常量，避免硬编码与编号冲突 |
| 编码生成策略化 | `md/autocode` 按分段类型（固定字符/日期/输入字符/流水号）以策略模式生成业务编码，Redis（`MesMdAutoCodeRedisDAO`）保证流水号并发安全 |
| 权限按"域-功能:操作"命名 | 统一 `@PreAuthorize("@ss.hasPermission('mes:{域-功能}:{操作}')")`；`simple-list`、`get-import-template` 等下拉/模板端点仅要求登录，不设单独权限 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|--------|------|----------|
| 主数据管理 (md) | 物料/分类/批次属性配置、产品 BOM/SIP/SOP、客户、供应商、计量单位、编码规则（含生成记录）、车间/工作站及其人力/设备/工装资源 | `MesMdItemDO`、`MesMdProductBomDO`、`MesMdAutoCodeRuleDO`、`MesMdWorkstationDO` |
| 排班日历 (cal) | 班组/班成员/班组排班、排班计划（计划班次/计划班组）、假期设置、排班日历聚合查询 | `MesCalTeamDO`、`MesCalPlanDO`、`MesCalTeamShiftDO` |
| 设备管理 (dv) | 设备类型/设备台账、点检保养项目/方案（绑定设备与项目）、点检记录、保养记录、维修工单 | `MesDvMachineryDO`、`MesDvCheckPlanDO`、`MesDvRepairDO` |
| 工装工具 (tm) | 工具类型（含编码规则开关）、工具台账（寿命/状态） | `MesTmToolDO`、`MesTmToolTypeDO` |
| 生产管理 (pro) | 生产工单（确认/完成/取消）与工单 BOM、生产任务与投料、生产报工、流转卡与工序记录、工序/工艺路线（产品/BOM 关联）、安灯呼叫配置与记录、上下工记录 | `MesProWorkOrderDO`、`MesProTaskDO`、`MesProFeedbackDO`、`MesProCardDO`、`MesProWorkRecordDO` |
| 质量管理 (qc) | 质检方案（指标项/产品关联）与质检指标、IQC/IPQC/OQC/RQC 四类检验单、待检任务聚合查询、检验结果与明细、缺陷类型/缺陷记录 | `MesQcIqcDO`、`MesQcIpqcDO`、`MesQcOqcDO`、`MesQcRqcDO`、`MesQcTemplateDO` |
| 仓库管理 (wm) | 仓库/库区/库位、到货/发货通知、采购/领料/生产/销售/外协/杂项/退货等出入库单、库存台账、批次/SN 码、条码配置与清单、装箱单、转移单、盘点（方案/任务/结果）、库存事务流水 | `MesWmMaterialStockDO`、`MesWmTransactionDO`、`MesWmBatchDO`、`MesWmItemReceiptDO` |
| 首页统计 (home) | 首页汇总统计、工单状态分布、生产趋势（无独立实体，聚合查询） | — |

## API 接口索引

模块端点总数 **766**（127 个 Controller），超过单页容量，按业务域分节给出控制器级摘要；完整端点清单见各 `api-{域}.md` 文档。

> 权限说明：下表"端点数"为方法级映射注解数；除标注外，各域端点遵循 `create/update/delete/get/page/export-excel` 标准 CRUD 集合，另有 `simple-list`、`get-import-template`（仅登录）与 `import`（导入权限）等扩展端点。

### 主数据管理（17 个控制器，95 个端点） → 详情见 [api-master-data.md](api-master-data.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesMdItemController | 物料产品（含状态启停、导入导出） | 9 |
| MesMdItemTypeController | 物料产品分类 | 6 |
| MesMdItemBatchConfigController | 物料批次属性配置 | 2 |
| MesMdProductBomController | 产品 BOM | 6 |
| MesMdProductSipController | 产品 SIP（检验标准作业） | 6 |
| MesMdProductSopController | 产品 SOP（标准作业） | 6 |
| MesMdClientController | 客户 | 8 |
| MesMdVendorController | 供应商 | 8 |
| MesMdUnitMeasureController | 计量单位 | 7 |
| MesMdAutoCodeRuleController | 编码规则 | 7 |
| MesMdAutoCodePartController | 编码规则组成 | 5 |
| MesMdAutoCodeRecordController | 编码生成记录 | 1 |
| MesMdWorkshopController | 车间 | 7 |
| MesMdWorkstationController | 工作站 | 6 |
| MesMdWorkstationMachineController | 工作站设备资源 | 3 |
| MesMdWorkstationToolController | 工作站工装夹具资源 | 4 |
| MesMdWorkstationWorkerController | 工作站人力资源 | 4 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/md/item/create | POST | 创建物料产品 | mes:md-item:create |
| /mes/md/item/update-status | PUT | 更新物料产品状态 | mes:md-item:update |
| /mes/md/item/import | POST | 导入物料 | mes:md-item:import |
| /mes/md/item/get-import-template | GET | 获得物料导入模板 | 已认证（仅登录） |

### 排班日历（8 个控制器，33 个端点） → 详情见 [api-calendar.md](api-calendar.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesCalCalendarController | 排班日历聚合查询 | 1 |
| MesCalHolidayController | 假期设置 | 3 |
| MesCalPlanController | 排班计划 | 7 |
| MesCalPlanShiftController | 计划班次 | 6 |
| MesCalPlanTeamController | 计划班组关联 | 3 |
| MesCalTeamController | 班组 | 7 |
| MesCalTeamMemberController | 班组成员 | 5 |
| MesCalTeamShiftController | 班组排班 | 1 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/cal/calendar/list | GET | 查询排班日历 | mes:cal-team-shift:query |
| /mes/cal/team-shift/list | GET | 获得班组排班列表 | mes:cal-team-shift:query |
| /mes/cal/plan/create | POST | 创建排班计划 | mes:cal-plan:create |

### 设备管理（12 个控制器，79 个端点） → 详情见 [api-device.md](api-device.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesDvMachineryController | 设备台账（含导入导出） | 9 |
| MesDvMachineryTypeController | 设备类型 | 6 |
| MesDvSubjectController | 点检保养项目 | 7 |
| MesDvCheckPlanController | 点检保养方案 | 8 |
| MesDvCheckPlanMachineryController | 方案-设备关联 | 3 |
| MesDvCheckPlanSubjectController | 方案-项目关联 | 3 |
| MesDvCheckRecordController | 设备点检记录 | 7 |
| MesDvCheckRecordLineController | 点检记录明细 | 6 |
| MesDvMaintenRecordController | 设备保养记录 | 7 |
| MesDvMaintenRecordLineController | 保养记录明细 | 7 |
| MesDvRepairController | 维修工单 | 9 |
| MesDvRepairLineController | 维修工单行 | 7 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/dv/machinery/create | POST | 创建设备 | mes:dv-machinery:create |
| /mes/dv/machinery/import | POST | 导入设备 | mes:dv-machinery:import |
| /mes/dv/machinery/simple-list | GET | 获得设备精简列表 | mes:dv-machinery:query |

### 工装工具（2 个控制器，14 个端点） → 详情见 [api-tool.md](api-tool.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesTmToolController | 工具台账 | 7 |
| MesTmToolTypeController | 工具类型 | 7 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/tm/tool/create | POST | 创建工具 | mes:tm-tool:create |
| /mes/tm/tool/simple-list | GET | 获得工具精简列表 | mes:tm-tool:query |

### 生产管理（16 个控制器，107 个端点） → 详情见 [api-production.md](api-production.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesProWorkOrderController | 生产工单（确认/完成/取消） | 9 |
| MesProWorkOrderBomController | 生产工单 BOM | 7 |
| MesProTaskController | 生产任务 | 7 |
| MesProTaskIssueController | 生产任务投料 | 6 |
| MesProFeedbackController | 生产报工 | 9 |
| MesProCardController | 生产流转卡 | 9 |
| MesProCardProcessController | 流转卡工序记录 | 5 |
| MesProProcessController | 生产工序 | 7 |
| MesProProcessContentController | 生产工序内容 | 5 |
| MesProRouteController | 工艺路线 | 8 |
| MesProRouteProcessController | 工艺路线工序 | 7 |
| MesProRouteProductController | 工艺路线产品 | 5 |
| MesProRouteProductBomController | 工艺路线产品 BOM | 5 |
| MesProAndonConfigController | 安灯呼叫配置 | 6 |
| MesProAndonRecordController | 安灯呼叫记录 | 6 |
| MesProWorkRecordController | 工作记录（上下工） | 6 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/pro/work-order/create | POST | 创建生产工单 | mes:pro-work-order:create |
| /mes/pro/work-order/confirm | PUT | 确认工单 | mes:pro-work-order:update |
| /mes/pro/work-order/finish | PUT | 完成工单 | mes:pro-work-order:update |
| /mes/pro/work-order/cancel | PUT | 取消工单 | mes:pro-work-order:update |

### 质量管理（16 个控制器，76 个端点） → 详情见 [api-quality.md](api-quality.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesQcIqcController | 来料检验单（IQC） | 7 |
| MesQcIqcLineController | 来料检验单行 | 2 |
| MesQcIpqcController | 过程检验单（IPQC） | 7 |
| MesQcIpqcLineController | 过程检验单行 | 2 |
| MesQcOqcController | 出货检验单（OQC） | 7 |
| MesQcOqcLineController | 出货检验单行 | 2 |
| MesQcRqcController | 退货检验单（RQC） | 7 |
| MesQcRqcLineController | 退货检验单行 | 2 |
| MesQcPendingInspectController | 待检任务聚合分页 | 1 |
| MesQcTemplateController | 质检方案 | 6 |
| MesQcTemplateIndicatorController | 质检方案-检测指标项 | 5 |
| MesQcTemplateItemController | 质检方案-产品关联 | 5 |
| MesQcIndicatorController | 质检指标 | 6 |
| MesQcIndicatorResultController | 检验结果 | 5 |
| MesQcDefectController | 缺陷类型 | 7 |
| MesQcDefectRecordController | 质检缺陷记录 | 5 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/qc/iqc/create | POST | 创建来料检验单 | mes:qc-iqc:create |
| /mes/qc/iqc/finish | PUT | 完成来料检验单 | mes:qc-iqc:finish |
| /mes/qc/pending-inspect/page | GET | 获得待检任务分页 | mes:qc-pending-inspect:query |

### 仓库管理（55 个控制器，359 个端点） → 详情见 [api-warehouse.md](api-warehouse.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesWmWarehouseController | 仓库 | 6 |
| MesWmWarehouseLocationController | 库区 | 7 |
| MesWmWarehouseAreaController | 库位 | 6 |
| MesWmMaterialStockController | 库存台账 | 4 |
| MesWmBatchController | 批次管理 | 4 |
| MesWmSnController | SN 码 | 6 |
| MesWmBarcodeController | 条码清单 | 8 |
| MesWmBarcodeConfigController | 条码配置 | 5 |
| MesWmArrivalNoticeController | 到货通知单 | 7 |
| MesWmArrivalNoticeLineController | 到货通知单行 | 5 |
| MesWmItemReceiptController | 采购入库单 | 10 |
| MesWmItemReceiptLineController | 采购入库单行 | 5 |
| MesWmItemReceiptDetailController | 采购入库明细 | 5 |
| MesWmProductIssueController | 领料出库单 | 11 |
| MesWmProductIssueLineController | 领料出库单行 | 6 |
| MesWmProductIssueDetailController | 领料出库明细 | 5 |
| MesWmReturnIssueController | 生产退料单 | 10 |
| MesWmReturnIssueLineController | 生产退料单行 | 6 |
| MesWmReturnIssueDetailController | 生产退料明细 | 5 |
| MesWmProductProduceLineController | 生产入库单行 | 1 |
| MesWmProductReceiptController | 产品收货（入库）单 | 11 |
| MesWmProductReceiptLineController | 产品收货单行 | 5 |
| MesWmProductReceiptDetailController | 产品收货单明细 | 5 |
| MesWmProductSalesController | 销售出库单 | 12 |
| MesWmProductSalesLineController | 销售出库单行 | 5 |
| MesWmProductSalesDetailController | 销售出库明细 | 5 |
| MesWmSalesNoticeController | 发货通知单 | 7 |
| MesWmSalesNoticeLineController | 发货通知单行 | 5 |
| MesWmReturnSalesController | 销售退货单 | 11 |
| MesWmReturnSalesLineController | 销售退货单行 | 6 |
| MesWmReturnSalesDetailController | 销售退货明细 | 5 |
| MesWmOutsourceIssueController | 外协发料单 | 11 |
| MesWmOutsourceIssueLineController | 外协发料单行 | 6 |
| MesWmOutsourceIssueDetailController | 外协发料单明细 | 5 |
| MesWmOutsourceReceiptController | 外协入库单 | 10 |
| MesWmOutsourceReceiptLineController | 外协入库单行 | 5 |
| MesWmOutsourceReceiptDetailController | 外协入库明细 | 5 |
| MesWmReturnVendorController | 供应商退货单 | 11 |
| MesWmReturnVendorLineController | 供应商退货单行 | 6 |
| MesWmReturnVendorDetailController | 供应商退货明细 | 5 |
| MesWmMiscReceiptController | 杂项入库单 | 9 |
| MesWmMiscReceiptLineController | 杂项入库单行 | 6 |
| MesWmMiscIssueController | 杂项出库单 | 9 |
| MesWmMiscIssueLineController | 杂项出库单行 | 5 |
| MesWmTransferController | 转移单 | 11 |
| MesWmTransferLineController | 转移单行 | 5 |
| MesWmTransferDetailController | 调拨明细 | 5 |
| MesWmStockTakingPlanController | 盘点方案 | 7 |
| MesWmStockTakingPlanParamController | 盘点方案参数 | 5 |
| MesWmStockTakingTaskController | 盘点任务 | 9 |
| MesWmStockTakingTaskLineController | 盘点任务行 | 6 |
| MesWmStockTakingTaskResultController | 盘点结果 | 5 |
| MesWmPackageController | 装箱单 | 8 |
| MesWmPackageLineController | 装箱明细 | 5 |
| MesWmItemConsumeLineController | 物料消耗记录行（借用了报工查询权限） | 1 |

代表端点：

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/wm/material-stock/page | GET | 获得库存台账分页 | mes:wm-material-stock:query |
| /mes/wm/material-stock/export-excel | GET | 导出库存台账 Excel | mes:wm-material-stock:export |
| /mes/wm/warehouse/simple-list | GET | 获得仓库精简列表 | 已认证（仅登录） |

### 首页统计（1 个控制器，3 个端点） → 详情见 [api-home.md](api-home.md)

| Controller | 说明 | 端点数 |
|------------|------|--------|
| MesHomeStatisticsController | 首页汇总/工单状态分布/生产趋势 | 3 |

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|----------|----------|------|----------|
| /mes/home-statistics/summary | GET | 获得首页汇总统计 | mes:home:query |
| /mes/home-statistics/work-order-status | GET | 获得工单状态分布 | mes:home:query |
| /mes/home-statistics/production-trend | GET | 获得生产趋势（days 参数 1-90） | mes:home:query |

## 数据模型

共 **133** 张表，全部继承 `BaseDO`（未使用 `TenantBaseDO`，模块未启用租户隔离）。按域分组列出：

### 排班日历 (cal)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_cal_holiday | 假期设置 | BaseDO | id, day, type, remark |
| mes_cal_plan | 排班计划 | BaseDO | id, code, name, calendarType |
| mes_cal_plan_shift | 计划班次 | BaseDO | id, planId, sort, name |
| mes_cal_plan_team | 计划班组关联 | BaseDO | id, planId, teamId |
| mes_cal_team | 班组 | BaseDO | id, code, name, calendarType |
| mes_cal_team_member | 班组成员 | BaseDO | id, teamId, userId |
| mes_cal_team_shift | 班组排班 | BaseDO | id, planId, teamId, shiftId |

### 设备管理 (dv)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_dv_machinery | 设备台账 | BaseDO | id, code, name, brand |
| mes_dv_machinery_type | 设备类型 | BaseDO | id, code, name, parentId |
| mes_dv_subject | 点检保养项目 | BaseDO | id, code, name, type |
| mes_dv_check_plan | 点检保养方案 | BaseDO | id, code, name, type |
| mes_dv_check_plan_machinery | 方案-设备关联 | BaseDO | id, planId, machineryId |
| mes_dv_check_plan_subject | 方案-项目关联 | BaseDO | id, planId, subjectId |
| mes_dv_check_record | 设备点检记录 | BaseDO | id, planId, machineryId, checkTime |
| mes_dv_check_record_line | 点检记录明细 | BaseDO | id, recordId, subjectId, checkStatus |
| mes_dv_mainten_record | 设备保养记录 | BaseDO | id, planId, machineryId, maintenTime |
| mes_dv_mainten_record_line | 保养记录明细 | BaseDO | id, recordId, subjectId, status |
| mes_dv_repair | 维修工单 | BaseDO | id, code, name, machineryId |
| mes_dv_repair_line | 维修工单行 | BaseDO | id, repairId, subjectId, malfunction |

### 主数据 (md)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_md_item | 物料产品 | BaseDO | id, code, name, specification |
| mes_md_item_type | 物料产品分类 | BaseDO | id, code, name, parentId |
| mes_md_item_batch_config | 物料批次属性配置 | BaseDO | id, itemId, produceDateFlag, expireDateFlag |
| mes_md_product_bom | 产品 BOM | BaseDO | id, itemId, bomItemId, quantity |
| mes_md_product_sip | 产品 SIP | BaseDO | id, itemId, sort, processId |
| mes_md_product_sop | 产品 SOP | BaseDO | id, itemId, sort, processId |
| mes_md_client | 客户 | BaseDO | id, code, name, nickname |
| mes_md_vendor | 供应商 | BaseDO | id, code, name, nickname |
| mes_md_unit_measure | 计量单位 | BaseDO | id, code, name, primaryFlag |
| mes_md_auto_code_rule | 编码规则 | BaseDO | id, code, name, description |
| mes_md_auto_code_part | 编码规则组成 | BaseDO | id, ruleId, sort, type |
| mes_md_auto_code_record | 编码生成记录 | BaseDO | id, ruleId, result, serialNo |
| mes_md_workshop | 车间 | BaseDO | id, code, name, area |
| mes_md_workstation | 工作站 | BaseDO | id, code, name, address |
| mes_md_workstation_machine | 工作站设备资源 | BaseDO | id, workstationId, machineryId, quantity |
| mes_md_workstation_tool | 工作站工装夹具资源 | BaseDO | id, workstationId, toolTypeId, quantity |
| mes_md_workstation_worker | 工作站人力资源 | BaseDO | id, workstationId, postId, quantity |

### 生产管理 (pro)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_pro_work_order | 生产工单 | BaseDO | id, code, name, type |
| mes_pro_work_order_bom | 生产工单 BOM | BaseDO | id, workOrderId, itemId, quantity |
| mes_pro_task | 生产任务 | BaseDO | id, code, name, workOrderId |
| mes_pro_task_issue | 生产任务投料 | BaseDO | id, taskId, workOrderId, workstationId |
| mes_pro_feedback | 生产报工 | BaseDO | id, code, type, channel |
| mes_pro_card | 生产流转卡 | BaseDO | id, code, workOrderId, itemId |
| mes_pro_card_process | 流转卡工序记录 | BaseDO | id, cardId, sort, processId |
| mes_pro_process | 生产工序 | BaseDO | id, code, name, attention |
| mes_pro_process_content | 生产工序内容 | BaseDO | id, processId, sort, content |
| mes_pro_route | 工艺路线 | BaseDO | id, code, name, description |
| mes_pro_route_process | 工艺路线工序 | BaseDO | id, routeId, processId, sort |
| mes_pro_route_product | 工艺路线产品 | BaseDO | id, routeId, itemId, quantity |
| mes_pro_route_product_bom | 工艺路线产品 BOM | BaseDO | id, routeId, processId, productId |
| mes_pro_andon_config | 安灯呼叫配置 | BaseDO | id, reason, level, handlerRoleId |
| mes_pro_andon_record | 安灯呼叫记录 | BaseDO | id, configId, workstationId, userId |
| mes_pro_work_record | 用户工作站绑定关系（当前快照） | BaseDO | id, userId, workstationId, type |
| mes_pro_work_record_log | 上下工记录流水 | BaseDO | id, userId, workstationId, type |

### 质量管理 (qc)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_qc_template | 质检方案 | BaseDO | id, code, name, status |
| mes_qc_template_indicator | 质检方案-检测指标项 | BaseDO | id, templateId, indicatorId, checkMethod |
| mes_qc_template_item | 质检方案-产品关联 | BaseDO | id, templateId, itemId, quantityCheck |
| mes_qc_indicator | 质检指标 | BaseDO | id, code, name, type |
| mes_qc_iqc | 来料检验单（IQC） | BaseDO | id, code, name, templateId |
| mes_qc_iqc_line | 来料检验单行 | BaseDO | id, iqcId, indicatorId, tool |
| mes_qc_ipqc | 过程检验单（IPQC） | BaseDO | id, code, name, type |
| mes_qc_ipqc_line | 过程检验单行 | BaseDO | id, ipqcId, indicatorId, tool |
| mes_qc_oqc | 出货检验单（OQC） | BaseDO | id, code, name, templateId |
| mes_qc_oqc_line | 出货检验单行 | BaseDO | id, oqcId, indicatorId, tool |
| mes_qc_rqc | 退货检验单（RQC） | BaseDO | id, code, name, templateId |
| mes_qc_rqc_line | 退货检验行 | BaseDO | id, rqcId, indicatorId, tool |
| mes_qc_indicator_result | 检验结果记录 | BaseDO | id, code, qcId, qcType |
| mes_qc_indicator_result_detail | 检验结果明细记录 | BaseDO | id, resultId, indicatorId, value |
| mes_qc_defect | 缺陷类型 | BaseDO | id, code, name, type |
| mes_qc_defect_record | 质检缺陷记录 | BaseDO | id, qcType, qcId, lineId |

### 工装工具 (tm)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_tm_tool | 工具台账 | BaseDO | id, code, name, brand |
| mes_tm_tool_type | 工具类型 | BaseDO | id, code, name, codeFlag |

### 仓库管理 (wm)

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| mes_wm_warehouse | 仓库 | BaseDO | id, code, name, address |
| mes_wm_warehouse_location | 库区 | BaseDO | id, code, name, warehouseId |
| mes_wm_warehouse_area | 库位 | BaseDO | id, code, name, locationId |
| mes_wm_material_stock | 库存台账（仓库现有量） | BaseDO | id, itemTypeId, itemId, batchId |
| mes_wm_transaction | 库存事务流水 | BaseDO | id, type, bizType, bizId |
| mes_wm_batch | 批次 | BaseDO | id, code, itemId, produceDate |
| mes_wm_sn | SN 码 | BaseDO | id, uuid, code, itemId |
| mes_wm_barcode | 条码清单 | BaseDO | id, configId, format, bizType |
| mes_wm_barcode_config | 条码配置 | BaseDO | id, format, bizType, contentFormat |
| mes_wm_arrival_notice | 到货通知单 | BaseDO | id, code, name, purchaseOrderCode |
| mes_wm_arrival_notice_line | 到货通知单行 | BaseDO | id, noticeId, itemId, arrivalQuantity |
| mes_wm_item_receipt | 采购入库单 | BaseDO | id, code, name, iqcId |
| mes_wm_item_receipt_line | 采购入库单行 | BaseDO | id, receiptId, arrivalNoticeLineId, itemId |
| mes_wm_item_receipt_detail | 采购入库明细 | BaseDO | id, lineId, receiptId, itemId |
| mes_wm_product_issue | 领料出库单 | BaseDO | id, code, name, workstationId |
| mes_wm_product_issue_line | 领料出库单行 | BaseDO | id, issueId, itemId, quantity |
| mes_wm_product_issue_detail | 领料出库明细 | BaseDO | id, issueId, lineId, materialStockId |
| mes_wm_return_issue | 生产退料单 | BaseDO | id, code, name, workOrderId |
| mes_wm_return_issue_line | 生产退料单行 | BaseDO | id, issueId, materialStockId, itemId |
| mes_wm_return_issue_detail | 生产退料明细 | BaseDO | id, issueId, lineId, materialStockId |
| mes_wm_product_produce | 生产入库单 | BaseDO | id, workOrderId, feedbackId, taskId |
| mes_wm_product_produce_line | 生产入库单行 | BaseDO | id, produceId, feedbackId, itemId |
| mes_wm_product_produce_detail | 生产入库明细 | BaseDO | id, produceId, lineId, itemId |
| mes_wm_item_consume | 物料消耗记录 | BaseDO | id, workOrderId, taskId, workstationId |
| mes_wm_item_consume_line | 物料消耗记录行 | BaseDO | id, consumeId, itemId, quantity |
| mes_wm_item_consume_detail | 物料消耗记录明细 | BaseDO | id, consumeId, lineId, materialStockId |
| mes_wm_product_receipt | 产品收货（入库）单 | BaseDO | id, code, name, workOrderId |
| mes_wm_product_receipt_line | 产品收货（入库）单行 | BaseDO | id, receiptId, itemId, materialStockId |
| mes_wm_product_receipt_detail | 产品收货（入库）单明细 | BaseDO | id, lineId, receiptId, itemId |
| mes_wm_product_sales | 销售出库单 | BaseDO | id, code, name, clientId |
| mes_wm_product_sales_line | 销售出库单行 | BaseDO | id, salesId, noticeLineId, itemId |
| mes_wm_product_sales_detail | 销售出库明细 | BaseDO | id, lineId, salesId, itemId |
| mes_wm_sales_notice | 发货通知单 | BaseDO | id, code, name, salesOrderCode |
| mes_wm_sales_notice_line | 发货通知单行 | BaseDO | id, noticeId, itemId, batchId |
| mes_wm_return_sales | 销售退货单 | BaseDO | id, code, name, salesOrderCode |
| mes_wm_return_sales_line | 销售退货单行 | BaseDO | id, returnId, itemId, quantity |
| mes_wm_return_sales_detail | 销售退货明细 | BaseDO | id, returnId, lineId, itemId |
| mes_wm_outsource_issue | 外协发料单 | BaseDO | id, code, name, vendorId |
| mes_wm_outsource_issue_line | 外协发料单行 | BaseDO | id, issueId, materialStockId, itemId |
| mes_wm_outsource_issue_detail | 外协发料单明细 | BaseDO | id, lineId, issueId, materialStockId |
| mes_wm_outsource_receipt | 外协入库单 | BaseDO | id, code, name, workOrderId |
| mes_wm_outsource_receipt_line | 外协入库单行 | BaseDO | id, receiptId, itemId, quantity |
| mes_wm_outsource_receipt_detail | 外协入库明细 | BaseDO | id, lineId, receiptId, itemId |
| mes_wm_return_vendor | 供应商退货单 | BaseDO | id, code, name, purchaseOrderCode |
| mes_wm_return_vendor_line | 供应商退货单行 | BaseDO | id, returnId, itemId, quantity |
| mes_wm_return_vendor_detail | 供应商退货明细 | BaseDO | id, returnId, lineId, materialStockId |
| mes_wm_misc_receipt | 杂项入库单 | BaseDO | id, code, name, type |
| mes_wm_misc_receipt_line | 杂项入库单行 | BaseDO | id, receiptId, itemId, quantity |
| mes_wm_misc_receipt_detail | 杂项入库明细 | BaseDO | id, receiptId, lineId, itemId |
| mes_wm_misc_issue | 杂项出库单 | BaseDO | id, code, name, type |
| mes_wm_misc_issue_line | 杂项出库单行 | BaseDO | id, issueId, sourceDocLineId, materialStockId |
| mes_wm_misc_issue_detail | 杂项出库明细 | BaseDO | id, issueId, lineId, materialStockId |
| mes_wm_transfer | 转移单 | BaseDO | id, code, name, type |
| mes_wm_transfer_line | 转移单行 | BaseDO | id, transferId, materialStockId, itemId |
| mes_wm_transfer_detail | 调拨明细 | BaseDO | id, lineId, transferId, itemId |
| mes_wm_stock_taking_plan | 盘点方案 | BaseDO | id, code, name, type |
| mes_wm_stock_taking_plan_param | 盘点方案参数 | BaseDO | id, planId, type, valueId |
| mes_wm_stock_taking_task | 盘点任务 | BaseDO | id, code, name, takingDate |
| mes_wm_stock_taking_task_line | 盘点任务行 | BaseDO | id, taskId, materialStockId, itemId |
| mes_wm_stock_taking_task_result | 盘点结果 | BaseDO | id, taskId, lineId, materialStockId |
| mes_wm_package | 装箱单 | BaseDO | id, code, parentId, packageDate |
| mes_wm_package_line | 装箱明细 | BaseDO | id, packageId, materialStockId, itemId |

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|----------|------|
| 策略模式 | `service/md/autocode/strategy/`（`MesMdAutoCodePartStrategy` 接口 + `MesMdAutoCodeContext` 上下文 + 4 个实现：`FixedCharPart`/`DatePart`/`InputCharPart`/`SerialNumberPart`） | 编码规则按分段类型路由到对应策略生成分段内容，新增分段类型只需扩展实现类 |
| DAO（Redis 数据访问对象） | `dal/redis/md/autocode/MesMdAutoCodeRedisDAO` | 编码流水号在 Redis 中的自增与缓存，隔离并发场景下的持久层访问 |

## 依赖关系

- **上游**（本模块依赖）:
  - framework starter：`yudao-spring-boot-starter-web`、`yudao-spring-boot-starter-security`、`yudao-spring-boot-starter-mybatis`、`yudao-spring-boot-starter-redis`、`yudao-spring-boot-starter-excel`、`yudao-spring-boot-starter-test`
  - 业务模块：`yudao-module-system`（通过 API 调用 `AdminUserApi`、`DictDataApi`、`PostApi`、`RoleApi`，用于用户昵称/岗位/角色/字典回显）
- **下游**（依赖本模块）: `yudao-server`（服务聚合启动）；无其他业务模块依赖 mes

## 详细文档

- [api-master-data.md](api-master-data.md) - 主数据管理
- [api-calendar.md](api-calendar.md) - 排班日历
- [api-device.md](api-device.md) - 设备管理
- [api-tool.md](api-tool.md) - 工装工具
- [api-production.md](api-production.md) - 生产管理
- [api-quality.md](api-quality.md) - 质量管理
- [api-warehouse.md](api-warehouse.md) - 仓库管理
- [api-home.md](api-home.md) - 首页统计
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
