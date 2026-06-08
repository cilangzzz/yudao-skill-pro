# 数据模型详情

> 模块路径：`yudao-module-mes`

---

## 1. 实体继承体系

所有 DO 实体类继承 `BaseDO`，统一包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键编号 |
| creator | String | 创建者 |
| createTime | LocalDateTime | 创建时间 |
| updater | String | 更新者 |
| updateTime | LocalDateTime | 更新时间 |
| deleted | Boolean | 是否删除（逻辑删除） |

> 部分表使用 `@KeySequence` 注解兼容 Oracle/PostgreSQL 主键生成。

---

## 2. 主数据域（MD）- 17 张表

### 2.1 mes_md_item（物料表）

**实体类**：`MesItemDO`
**继承**：`BaseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 物料编号 |
| name | String | 物料名称 |
| item_type_id | Long | 物料分类编号 |
| code | String | 物料编码 |
| spec | String | 规格型号 |
| unit_of_measure | String | 计量单位 |
| default_warehouse_id | Long | 默认仓库编号 |
| default_location_id | Long | 默认库位编号 |
| min_stock | BigDecimal | 最小库存 |
| max_stock | BigDecimal | 最大库存 |
| safety_stock | BigDecimal | 安全库存 |
| shelf_life | Integer | 保质期（天） |
| batch_size | BigDecimal | 批量大小 |
| default_vendor_id | Long | 默认供应商编号 |
| purchase_price | BigDecimal | 采购单价 |
| sale_price | BigDecimal | 销售单价 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 2.2 mes_md_item_type（物料分类表）

**实体类**：`MesItemTypeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 分类编号 |
| parent_id | Long | 父分类编号 |
| name | String | 分类名称 |
| sort | Integer | 排序 |
| status | Integer | 状态 |

### 2.3 mes_md_item_batch_config（物料批次配置表）

**实体类**：`MesItemBatchConfigDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 配置编号 |
| item_id | Long | 物料编号 |
| batch_rule | String | 批次生成规则 |
| auto_generate | Boolean | 是否自动生成批次 |

### 2.4 mes_md_product_bom（产品 BOM 表）

**实体类**：`MesProductBomDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | BOM 编号 |
| name | String | BOM 名称 |
| item_id | Long | 产品物料编号 |
| version | String | BOM 版本 |
| status | Integer | 状态 |
| remark | String | 备注 |

> BOM 子表通过 `mes_md_product_bom` 的子表关联（具体子表结构参见代码）。

### 2.5 mes_md_product_sip（产品 SIP 表）

**实体类**：`MesProductSipDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | SIP 编号 |
| name | String | SIP 名称 |
| item_id | Long | 产品物料编号 |
| version | String | 版本 |
| status | Integer | 状态 |
| content | String | SIP 内容（富文本） |

### 2.6 mes_md_product_sop（产品 SOP 表）

**实体类**：`MesProductSopDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | SOP 编号 |
| name | String | SOP 名称 |
| item_id | Long | 产品物料编号 |
| version | String | 版本 |
| status | Integer | 状态 |
| content | String | SOP 内容（富文本） |

### 2.7 mes_md_client（客户表）

**实体类**：`MesClientDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 客户编号 |
| name | String | 客户名称 |
| code | String | 客户编码 |
| contact | String | 联系人 |
| phone | String | 联系电话 |
| address | String | 地址 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 2.8 mes_md_vendor（供应商表）

**实体类**：`MesVendorDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 供应商编号 |
| name | String | 供应商名称 |
| code | String | 供应商编码 |
| contact | String | 联系人 |
| phone | String | 联系电话 |
| address | String | 地址 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 2.9 mes_md_unit_measure（计量单位表）

**实体类**：`MesUnitMeasureDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 单位编号 |
| name | String | 单位名称 |
| code | String | 单位编码 |
| status | Integer | 状态 |

### 2.10 mes_md_workshop（车间表）

**实体类**：`MesWorkshopDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 车间编号 |
| name | String | 车间名称 |
| code | String | 车间编码 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 2.11 mes_md_workstation（工位表）

**实体类**：`MesWorkstationDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 工位编号 |
| name | String | 工位名称 |
| code | String | 工位编码 |
| workshop_id | Long | 所属车间编号 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 2.12 mes_md_workstation_machine（工位机器关联表）

**实体类**：`MesWorkstationMachineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| workstation_id | Long | 工位编号 |
| machinery_id | Long | 设备编号 |

### 2.13 mes_md_workstation_tool（工位工具关联表）

**实体类**：`MesWorkstationToolDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| workstation_id | Long | 工位编号 |
| tool_id | Long | 工具编号 |

### 2.14 mes_md_workstation_worker（工位工人关联表）

**实体类**：`MesWorkstationWorkerDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| workstation_id | Long | 工位编号 |
| user_id | Long | 操作工人用户编号 |

### 2.15 mes_md_auto_code_rule（自动编码规则表）

**实体类**：`MesAutoCodeRuleDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 规则编号 |
| name | String | 规则名称 |
| code | String | 规则编码 |
| biz_type | String | 业务类型 |
| separator | String | 分隔符 |
| reset_type | Integer | 重置类型（不重置/按天/按月/按年） |
| status | Integer | 状态 |

### 2.16 mes_md_auto_code_part（编码规则零件表）

**实体类**：`MesAutoCodePartDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 零件编号 |
| rule_id | Long | 规则编号 |
| type | Integer | 零件类型（日期/固定字符/输入字符/序列号） |
| value | String | 值（格式或固定值） |
| sort | Integer | 排序 |
| length | Integer | 序列号长度（补零） |

### 2.17 mes_md_auto_code_record（编码记录表）

**实体类**：`MesAutoCodeRecordDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| rule_id | Long | 规则编号 |
| biz_date | String | 业务日期（用于按日期重置序列号） |
| current_value | Integer | 当前序列号值 |

---

## 3. 生产域（PRO）- 17 张表

### 3.1 mes_pro_work_order（生产工单表）

**实体类**：`MesWorkOrderDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 工单编号 |
| no | String | 工单号 |
| item_id | Long | 产品物料编号 |
| bom_id | Long | BOM 编号 |
| route_id | Long | 工艺路线编号 |
| quantity | BigDecimal | 计划数量 |
| completed_quantity | BigDecimal | 已完成数量 |
| start_date | LocalDate | 计划开始日期 |
| end_date | LocalDate | 计划结束日期 |
| priority | Integer | 优先级 |
| status | Integer | 状态（0草稿/1已确认/2已完工/3已取消） |
| source_code | String | 来源单号 |
| remark | String | 备注 |

### 3.2 mes_pro_work_order_bom（工单 BOM 表）

**实体类**：`MesWorkOrderBomDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| work_order_id | Long | 工单编号 |
| item_id | Long | 子物料编号 |
| quantity | BigDecimal | 用量 |
| loss_rate | BigDecimal | 损耗率 |

### 3.3 mes_pro_task（生产任务表）

**实体类**：`MesTaskDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 任务编号 |
| work_order_id | Long | 工单编号 |
| route_process_id | Long | 工序编号 |
| workstation_id | Long | 工位编号 |
| machinery_id | Long | 设备编号 |
| user_id | Long | 操作员编号 |
| plan_start_time | LocalDateTime | 计划开始时间 |
| plan_end_time | LocalDateTime | 计划结束时间 |
| actual_start_time | LocalDateTime | 实际开始时间 |
| actual_end_time | LocalDateTime | 实际结束时间 |
| plan_quantity | BigDecimal | 计划数量 |
| actual_quantity | BigDecimal | 实际数量 |
| status | Integer | 状态 |
| sort | Integer | 排序 |

### 3.4 mes_pro_task_issue（任务领料表）

**实体类**：`MesTaskIssueDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| task_id | Long | 任务编号 |
| item_id | Long | 物料编号 |
| plan_quantity | BigDecimal | 计划领料数量 |
| actual_quantity | BigDecimal | 实际领料数量 |

### 3.5 mes_pro_route（工艺路线表）

**实体类**：`MesRouteDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 路线编号 |
| name | String | 路线名称 |
| code | String | 路线编码 |
| item_id | Long | 产品物料编号 |
| version | String | 版本 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 3.6 mes_pro_route_process（工艺路线工序表）

**实体类**：`MesRouteProcessDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| route_id | Long | 工艺路线编号 |
| process_id | Long | 工序编号 |
| sort | Integer | 工序序号 |
| workstation_id | Long | 默认工位编号 |
| standard_time | BigDecimal | 标准工时（分钟） |
| remark | String | 备注 |

### 3.7 mes_pro_route_product（工艺路线产品关联表）

**实体类**：`MesRouteProductDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| route_id | Long | 工艺路线编号 |
| item_id | Long | 产品物料编号 |

### 3.8 mes_pro_route_product_bom（工艺路线产品 BOM 关联表）

**实体类**：`MesRouteProductBomDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| route_id | Long | 工艺路线编号 |
| item_id | Long | 产品物料编号 |
| bom_id | Long | BOM 编号 |

### 3.9 mes_pro_process（工序表）

**实体类**：`MesProcessDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 工序编号 |
| name | String | 工序名称 |
| code | String | 工序编码 |
| workstation_id | Long | 默认工位编号 |
| standard_time | BigDecimal | 标准工时（分钟） |
| status | Integer | 状态 |
| remark | String | 备注 |

### 3.10 mes_pro_process_content（工序内容表）

**实体类**：`MesProcessContentDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| process_id | Long | 工序编号 |
| name | String | 内容名称 |
| type | Integer | 内容类型 |
| content | String | 内容详情 |
| sort | Integer | 排序 |

### 3.11 mes_pro_card（流转卡表）

**实体类**：`MesCardDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 流转卡编号 |
| no | String | 流转卡号 |
| work_order_id | Long | 工单编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 数量 |
| status | Integer | 状态（0草稿/1进行中/2已完成/3已取消） |
| remark | String | 备注 |

### 3.12 mes_pro_card_process（流转卡工序表）

**实体类**：`MesCardProcessDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| card_id | Long | 流转卡编号 |
| process_id | Long | 工序编号 |
| sort | Integer | 工序序号 |
| actual_time | BigDecimal | 实际用时 |
| actual_quantity | BigDecimal | 实际数量 |
| status | Integer | 状态 |

### 3.13 mes_pro_feedback（报工反馈表）

**实体类**：`MesFeedbackDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 报工编号 |
| work_order_id | Long | 工单编号 |
| task_id | Long | 任务编号 |
| process_id | Long | 工序编号 |
| user_id | Long | 报工人编号 |
| quantity | BigDecimal | 报工数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| start_time | LocalDateTime | 开始时间 |
| end_time | LocalDateTime | 结束时间 |
| status | Integer | 状态（0草稿/1待审批/2已通过/3已驳回） |
| remark | String | 备注 |

### 3.14 mes_pro_work_record（报工记录表）

**实体类**：`MesWorkRecordDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| work_order_id | Long | 工单编号 |
| task_id | Long | 任务编号 |
| process_id | Long | 工序编号 |
| user_id | Long | 操作员编号 |
| quantity | BigDecimal | 数量 |
| start_time | LocalDateTime | 开始时间 |
| end_time | LocalDateTime | 结束时间 |
| duration | Integer | 用时（分钟） |

### 3.15 mes_pro_work_record_log（报工日志表）

**实体类**：`MesWorkRecordLogDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 日志编号 |
| work_record_id | Long | 报工记录编号 |
| type | Integer | 日志类型 |
| content | String | 日志内容 |
| user_id | Long | 操作人编号 |

### 3.16 mes_pro_andon_config（安灯配置表）

**实体类**：`MesAndonConfigDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 配置编号 |
| name | String | 配置名称 |
| type | Integer | 安灯类型 |
| workshop_id | Long | 车间编号 |
| status | Integer | 状态 |

### 3.17 mes_pro_andon_record（安灯记录表）

**实体类**：`MesAndonRecordDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| config_id | Long | 配置编号 |
| workstation_id | Long | 工位编号 |
| user_id | Long | 发起人编号 |
| type | Integer | 安灯类型 |
| description | String | 问题描述 |
| status | Integer | 状态 |
| handler_id | Long | 处理人编号 |
| handle_time | LocalDateTime | 处理时间 |
| handle_result | String | 处理结果 |

---

## 4. 质量域（QC）- 17 张表

### 4.1 mes_qc_template（检验模板表）

**实体类**：`MesQcTemplateDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 模板编号 |
| name | String | 模板名称 |
| type | Integer | 检验类型（IQC/IPQC/OQC/RQC） |
| item_id | Long | 适用物料编号 |
| status | Integer | 状态 |

### 4.2 mes_qc_template_item（检验模板检验项表）

**实体类**：`MesQcTemplateItemDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| template_id | Long | 模板编号 |
| name | String | 检验项名称 |
| sort | Integer | 排序 |

### 4.3 mes_qc_template_indicator（检验模板指标表）

**实体类**：`MesQcTemplateIndicatorDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| template_item_id | Long | 检验项编号 |
| indicator_id | Long | 指标编号 |
| upper_limit | BigDecimal | 上限值 |
| lower_limit | BigDecimal | 下限值 |
| standard_value | BigDecimal | 标准值 |

### 4.4 mes_qc_indicator（检验指标表）

**实体类**：`MesQcIndicatorDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 指标编号 |
| name | String | 指标名称 |
| code | String | 指标编码 |
| unit | String | 计量单位 |
| type | Integer | 指标类型（定量/定性） |
| status | Integer | 状态 |

### 4.5 mes_qc_indicator_result（指标结果表）

**实体类**：`MesQcIndicatorResultDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 结果编号 |
| qc_type | Integer | 检验类型 |
| qc_id | Long | 检验单编号 |
| indicator_id | Long | 指标编号 |
| result_value | BigDecimal | 结果值 |
| is_qualified | Boolean | 是否合格 |

### 4.6 mes_qc_indicator_result_detail（指标结果明细表）

**实体类**：`MesQcIndicatorResultDetailDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 明细编号 |
| result_id | Long | 结果编号 |
| measure_value | BigDecimal | 测量值 |
| sort | Integer | 测量次序 |

### 4.7 mes_qc_defect（缺陷类型表）

**实体类**：`MesQcDefectDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 缺陷编号 |
| name | String | 缺陷名称 |
| code | String | 缺陷编码 |
| level | Integer | 缺陷等级 |
| status | Integer | 状态 |

### 4.8 mes_qc_defect_record（缺陷记录表）

**实体类**：`MesQcDefectRecordDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| defect_id | Long | 缺陷类型编号 |
| qc_type | Integer | 检验类型 |
| qc_id | Long | 检验单编号 |
| quantity | Integer | 缺陷数量 |
| description | String | 描述 |

### 4.9 mes_qc_iqc（来料检验单表）

**实体类**：`MesQcIqcDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 检验单编号 |
| no | String | 检验单号 |
| arrival_notice_id | Long | 到货通知编号 |
| vendor_id | Long | 供应商编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| unqualified_quantity | BigDecimal | 不合格数量 |
| result | Integer | 判定结果 |
| inspector_id | Long | 检验员编号 |
| inspect_date | LocalDate | 检验日期 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 4.10 mes_qc_iqc_line（来料检验行表）

**实体类**：`MesQcIqcLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| iqc_id | Long | 检验单编号 |
| item_id | Long | 物料编号 |
| batch_id | Long | 批次编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |

### 4.11 mes_qc_ipqc（过程检验单表）

**实体类**：`MesQcIpqcDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 检验单编号 |
| no | String | 检验单号 |
| work_order_id | Long | 工单编号 |
| process_id | Long | 工序编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |
| inspector_id | Long | 检验员编号 |
| inspect_date | LocalDate | 检验日期 |
| status | Integer | 状态 |

### 4.12 mes_qc_ipqc_line（过程检验行表）

**实体类**：`MesQcIpqcLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| ipqc_id | Long | 检验单编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |

### 4.13 mes_qc_oqc（出货检验单表）

**实体类**：`MesQcOqcDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 检验单编号 |
| no | String | 检验单号 |
| client_id | Long | 客户编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |
| inspector_id | Long | 检验员编号 |
| inspect_date | LocalDate | 检验日期 |
| status | Integer | 状态 |

### 4.14 mes_qc_oqc_line（出货检验行表）

**实体类**：`MesQcOqcLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| oqc_id | Long | 检验单编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |

### 4.15 mes_qc_rqc（退货检验单表）

**实体类**：`MesQcRqcDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 检验单编号 |
| no | String | 检验单号 |
| source_type | Integer | 退货来源类型 |
| source_id | Long | 来源单号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |
| inspector_id | Long | 检验员编号 |
| inspect_date | LocalDate | 检验日期 |
| status | Integer | 状态 |

### 4.16 mes_qc_rqc_line（退货检验行表）

**实体类**：`MesQcRqcLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| rqc_id | Long | 检验单编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 检验数量 |
| qualified_quantity | BigDecimal | 合格数量 |
| result | Integer | 判定结果 |

---

## 5. 设备域（DV）- 12 张表

### 5.1 mes_dv_machinery（设备台账表）

**实体类**：`MesMachineryDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 设备编号 |
| name | String | 设备名称 |
| code | String | 设备编码 |
| machinery_type_id | Long | 设备类型编号 |
| specification | String | 规格型号 |
| workshop_id | Long | 所属车间编号 |
| workstation_id | Long | 所属工位编号 |
| purchase_date | LocalDate | 购置日期 |
| warranty_date | LocalDate | 保修到期日期 |
| status | Integer | 状态（0正常/1维修中/2保养中/3停用） |
| remark | String | 备注 |

### 5.2 mes_dv_machinery_type（设备类型表）

**实体类**：`MesMachineryTypeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 类型编号 |
| parent_id | Long | 父类型编号 |
| name | String | 类型名称 |
| status | Integer | 状态 |

### 5.3 mes_dv_check_plan（点检计划表）

**实体类**：`MesCheckPlanDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 计划编号 |
| name | String | 计划名称 |
| frequency | Integer | 检查频率 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 5.4 mes_dv_check_plan_machinery（点检计划设备关联表）

**实体类**：`MesCheckPlanMachineryDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| plan_id | Long | 计划编号 |
| machinery_id | Long | 设备编号 |

### 5.5 mes_dv_check_plan_subject（点检计划检查项关联表）

**实体类**：`MesCheckPlanSubjectDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| plan_id | Long | 计划编号 |
| subject_id | Long | 检查项目编号 |

### 5.6 mes_dv_check_record（点检记录表）

**实体类**：`MesCheckRecordDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| plan_id | Long | 计划编号 |
| machinery_id | Long | 设备编号 |
| check_date | LocalDate | 点检日期 |
| user_id | Long | 点检人编号 |
| result | Integer | 整体结果 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 5.7 mes_dv_check_record_line（点检记录行表）

**实体类**：`MesCheckRecordLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| record_id | Long | 记录编号 |
| subject_id | Long | 检查项目编号 |
| actual_value | String | 实际值 |
| is_qualified | Boolean | 是否合格 |

### 5.8 mes_dv_mainten_record（保养记录表）

**实体类**：`MesMaintenRecordDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录编号 |
| machinery_id | Long | 设备编号 |
| maintenance_date | LocalDate | 保养日期 |
| user_id | Long | 保养人编号 |
| type | Integer | 保养类型 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 5.9 mes_dv_mainten_record_line（保养记录行表）

**实体类**：`MesMaintenRecordLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| record_id | Long | 记录编号 |
| content | String | 保养内容 |
| material | String | 使用材料 |
| duration | Integer | 用时（分钟） |

### 5.10 mes_dv_repair（维修单表）

**实体类**：`MesRepairDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 维修单编号 |
| no | String | 维修单号 |
| machinery_id | Long | 设备编号 |
| fault_description | String | 故障描述 |
| user_id | Long | 维修人编号 |
| status | Integer | 状态（0草稿/1待确认/2维修中/3已完成） |
| remark | String | 备注 |

### 5.11 mes_dv_repair_line（维修行表）

**实体类**：`MesRepairLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| repair_id | Long | 维修单编号 |
| content | String | 维修内容 |
| material | String | 更换配件 |
| duration | Integer | 用时（分钟） |

### 5.12 mes_dv_subject（检查项目表）

**实体类**：`MesSubjectDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 项目编号 |
| name | String | 项目名称 |
| code | String | 项目编码 |
| type | Integer | 检查类型 |
| standard | String | 检查标准 |
| status | Integer | 状态 |

---

## 6. 工具域（TM）- 2 张表

### 6.1 mes_tm_tool（工具台账表）

**实体类**：`MesToolDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 工具编号 |
| name | String | 工具名称 |
| code | String | 工具编码 |
| tool_type_id | Long | 工具类型编号 |
| spec | String | 规格型号 |
| workshop_id | Long | 所属车间编号 |
| workstation_id | Long | 所属工位编号 |
| status | Integer | 状态（0正常/1使用中/2维修中/3报废） |
| remark | String | 备注 |

### 6.2 mes_tm_tool_type（工具类型表）

**实体类**：`MesToolTypeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 类型编号 |
| parent_id | Long | 父类型编号 |
| name | String | 类型名称 |
| status | Integer | 状态 |

---

## 7. 仓库域（WM）- 40+ 张表

### 7.1 mes_wm_warehouse（仓库表）

**实体类**：`MesWarehouseDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 仓库编号 |
| name | String | 仓库名称 |
| code | String | 仓库编码 |
| type | Integer | 仓库类型 |
| address | String | 地址 |
| status | Integer | 状态 |

### 7.2 mes_wm_warehouse_area（库区表）

**实体类**：`MesWarehouseAreaDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 库区编号 |
| warehouse_id | Long | 仓库编号 |
| name | String | 库区名称 |
| code | String | 库区编码 |
| status | Integer | 状态 |

### 7.3 mes_wm_warehouse_location（库位表）

**实体类**：`MesWarehouseLocationDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 库位编号 |
| area_id | Long | 库区编号 |
| name | String | 库位名称 |
| code | String | 库位编码 |
| status | Integer | 状态 |

### 7.4 mes_wm_material_stock（物料库存表）

**实体类**：`MesMaterialStockDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 库存编号 |
| item_id | Long | 物料编号 |
| warehouse_id | Long | 仓库编号 |
| location_id | Long | 库位编号 |
| batch_id | Long | 批次编号 |
| quantity | BigDecimal | 库存数量 |
| locked_quantity | BigDecimal | 锁定数量 |

### 7.5 mes_wm_batch（批次表）

**实体类**：`MesBatchDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 批次编号 |
| no | String | 批次号 |
| item_id | Long | 物料编号 |
| production_date | LocalDate | 生产日期 |
| expiry_date | LocalDate | 过期日期 |
| status | Integer | 状态 |

### 7.6 mes_wm_barcode（条码表）

**实体类**：`MesBarcodeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 条码编号 |
| code | String | 条码内容 |
| item_id | Long | 物料编号 |
| batch_id | Long | 批次编号 |
| type | Integer | 条码类型 |
| status | Integer | 状态 |

### 7.7 mes_wm_barcode_config（条码配置表）

**实体类**：`MesBarcodeConfigDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 配置编号 |
| name | String | 配置名称 |
| type | Integer | 条码类型 |
| rule | String | 生成规则 |
| status | Integer | 状态 |

### 7.8 mes_wm_sn（SN 序列号表）

**实体类**：`MesSnDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| sn | String | 序列号 |
| item_id | Long | 物料编号 |
| batch_id | Long | 批次编号 |
| status | Integer | 状态 |

### 7.9 mes_wm_transaction（库存事务表）

**实体类**：`MesTransactionDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 事务编号 |
| type | Integer | 事务类型（入库/出库/调拨） |
| item_id | Long | 物料编号 |
| warehouse_id | Long | 仓库编号 |
| quantity | BigDecimal | 数量 |
| source_type | Integer | 来源类型 |
| source_id | Long | 来源单号 |

### 7.10 mes_wm_arrival_notice（到货通知表）

**实体类**：`MesArrivalNoticeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 通知编号 |
| no | String | 通知单号 |
| vendor_id | Long | 供应商编号 |
| arrival_date | LocalDate | 到货日期 |
| status | Integer | 状态 |

### 7.11 mes_wm_arrival_notice_line（到货通知行表）

**实体类**：`MesArrivalNoticeLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| notice_id | Long | 通知编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 数量 |
| batch_no | String | 批次号 |

### 7.12 mes_wm_item_receipt（采购入库表）

**实体类**：`MesItemReceiptDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 入库单编号 |
| no | String | 入库单号 |
| vendor_id | Long | 供应商编号 |
| warehouse_id | Long | 仓库编号 |
| receipt_date | LocalDate | 入库日期 |
| status | Integer | 状态 |

### 7.13 mes_wm_item_receipt_line（采购入库行表）

**实体类**：`MesItemReceiptLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| receipt_id | Long | 入库单编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 数量 |

### 7.14 mes_wm_item_receipt_detail（采购入库详情表）

**实体类**：`MesItemReceiptDetailDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| line_id | Long | 入库行编号 |
| batch_id | Long | 批次编号 |
| location_id | Long | 库位编号 |
| barcode | String | 条码 |
| quantity | BigDecimal | 数量 |

### 7.15 mes_wm_product_receipt（产品入库表）

**实体类**：`MesProductReceiptDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 入库单编号 |
| no | String | 入库单号 |
| work_order_id | Long | 工单编号 |
| warehouse_id | Long | 仓库编号 |
| receipt_date | LocalDate | 入库日期 |
| status | Integer | 状态 |

### 7.16 mes_wm_product_issue（生产领料表）

**实体类**：`MesProductIssueDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 领料单编号 |
| no | String | 领料单号 |
| work_order_id | Long | 工单编号 |
| warehouse_id | Long | 仓库编号 |
| issue_date | LocalDate | 领料日期 |
| status | Integer | 状态 |

### 7.17 mes_wm_return_issue（生产退料表）

**实体类**：`MesReturnIssueDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 退料单编号 |
| no | String | 退料单号 |
| work_order_id | Long | 工单编号 |
| warehouse_id | Long | 仓库编号 |
| return_date | LocalDate | 退料日期 |
| status | Integer | 状态 |

### 7.18 mes_wm_misc_issue（其他出库表）

**实体类**：`MesMiscIssueDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 出库单编号 |
| no | String | 出库单号 |
| warehouse_id | Long | 仓库编号 |
| issue_date | LocalDate | 出库日期 |
| type | Integer | 出库类型 |
| status | Integer | 状态 |

### 7.19 mes_wm_misc_receipt（其他入库表）

**实体类**：`MesMiscReceiptDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 入库单编号 |
| no | String | 入库单号 |
| warehouse_id | Long | 仓库编号 |
| receipt_date | LocalDate | 入库日期 |
| type | Integer | 入库类型 |
| status | Integer | 状态 |

### 7.20 mes_wm_product_sales（销售出库表）

**实体类**：`MesProductSalesDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 出库单编号 |
| no | String | 出库单号 |
| client_id | Long | 客户编号 |
| warehouse_id | Long | 仓库编号 |
| sales_date | LocalDate | 出库日期 |
| status | Integer | 状态 |

### 7.21 mes_wm_return_sales（销售退货表）

**实体类**：`MesReturnSalesDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 退货单编号 |
| no | String | 退货单号 |
| client_id | Long | 客户编号 |
| warehouse_id | Long | 仓库编号 |
| return_date | LocalDate | 退货日期 |
| status | Integer | 状态 |

### 7.22 mes_wm_outsource_issue（委外发料表）

**实体类**：`MesOutsourceIssueDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 发料单编号 |
| no | String | 发料单号 |
| vendor_id | Long | 委外供应商编号 |
| warehouse_id | Long | 仓库编号 |
| issue_date | LocalDate | 发料日期 |
| status | Integer | 状态 |

### 7.23 mes_wm_outsource_receipt（委外收料表）

**实体类**：`MesOutsourceReceiptDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 收料单编号 |
| no | String | 收料单号 |
| vendor_id | Long | 委外供应商编号 |
| warehouse_id | Long | 仓库编号 |
| receipt_date | LocalDate | 收料日期 |
| status | Integer | 状态 |

### 7.24 mes_wm_return_vendor（供应商退货表）

**实体类**：`MesReturnVendorDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 退货单编号 |
| no | String | 退货单号 |
| vendor_id | Long | 供应商编号 |
| warehouse_id | Long | 仓库编号 |
| return_date | LocalDate | 退货日期 |
| status | Integer | 状态 |

### 7.25 mes_wm_transfer（库存调拨表）

**实体类**：`MesTransferDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 调拨单编号 |
| no | String | 调拨单号 |
| from_warehouse_id | Long | 源仓库编号 |
| from_location_id | Long | 源库位编号 |
| to_warehouse_id | Long | 目标仓库编号 |
| to_location_id | Long | 目标库位编号 |
| transfer_date | LocalDate | 调拨日期 |
| status | Integer | 状态（0草稿/1待确认/2已完成） |

### 7.26 mes_wm_package（包装表）

**实体类**：`MesPackageDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 包装单编号 |
| no | String | 包装单号 |
| client_id | Long | 客户编号 |
| status | Integer | 状态 |

### 7.27 mes_wm_package_line（包装行表）

**实体类**：`MesPackageLineDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| package_id | Long | 包装单编号 |
| item_id | Long | 物料编号 |
| quantity | BigDecimal | 数量 |
| box_no | String | 箱号 |

### 7.28 mes_wm_stock_taking_plan（盘点计划表）

**实体类**：`MesStockTakingPlanDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 计划编号 |
| name | String | 计划名称 |
| warehouse_id | Long | 盘点仓库编号 |
| type | Integer | 盘点类型 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 7.29 mes_wm_stock_taking_task（盘点任务表）

**实体类**：`MesStockTakingTaskDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 任务编号 |
| plan_id | Long | 计划编号 |
| location_id | Long | 盘点库位编号 |
| user_id | Long | 盘点人编号 |
| status | Integer | 状态 |

### 7.30 mes_wm_stock_taking_task_result（盘点结果表）

**实体类**：`MesStockTakingTaskResultDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 结果编号 |
| task_id | Long | 任务编号 |
| item_id | Long | 物料编号 |
| batch_id | Long | 批次编号 |
| book_quantity | BigDecimal | 账面数量 |
| actual_quantity | BigDecimal | 实盘数量 |
| difference | BigDecimal | 差异 |

### 7.31 mes_wm_item_consume（物料消耗表）

**实体类**：`MesItemConsumeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| work_order_id | Long | 工单编号 |
| item_id | Long | 物料编号 |
| standard_quantity | BigDecimal | 标准用量（BOM） |
| actual_quantity | BigDecimal | 实际用量 |

### 7.32 mes_wm_product_produce（产品产出表）

**实体类**：`MesProductProduceDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| work_order_id | Long | 工单编号 |
| item_id | Long | 产品物料编号 |
| plan_quantity | BigDecimal | 计划产量 |
| actual_quantity | BigDecimal | 实际产量 |

### 7.33 mes_wm_sales_notice（销售通知表）

**实体类**：`MesSalesNoticeDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 通知编号 |
| no | String | 通知单号 |
| client_id | Long | 客户编号 |
| delivery_date | LocalDate | 交货日期 |
| status | Integer | 状态 |

---

## 8. 日历域（CAL）- 7 张表

### 8.1 mes_cal_holiday（节假日表）

**实体类**：`MesCalHolidayDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| name | String | 节假日名称 |
| date | LocalDate | 日期 |
| type | Integer | 类型（0法定假日/1调休工作日） |
| remark | String | 备注 |

### 8.2 mes_cal_plan（排班计划表）

**实体类**：`MesCalPlanDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 计划编号 |
| name | String | 计划名称 |
| start_date | LocalDate | 开始日期 |
| end_date | LocalDate | 结束日期 |
| status | Integer | 状态（0草稿/1待审批/2已生效/3已驳回） |
| remark | String | 备注 |

### 8.3 mes_cal_plan_shift（排班计划班次表）

**实体类**：`MesCalPlanShiftDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| plan_id | Long | 计划编号 |
| name | String | 班次名称 |
| start_time | LocalTime | 开始时间 |
| end_time | LocalTime | 结束时间 |
| is_next_day | Boolean | 是否跨天 |

### 8.4 mes_cal_plan_team（排班计划班组表）

**实体类**：`MesCalPlanTeamDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| plan_id | Long | 计划编号 |
| team_id | Long | 班组编号 |
| shift_id | Long | 班次编号 |
| work_date | LocalDate | 工作日期 |

### 8.5 mes_cal_team（班组表）

**实体类**：`MesCalTeamDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 班组编号 |
| name | String | 班组名称 |
| leader_id | Long | 班组长用户编号 |
| status | Integer | 状态 |
| remark | String | 备注 |

### 8.6 mes_cal_team_member（班组成员表）

**实体类**：`MesCalTeamMemberDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| team_id | Long | 班组编号 |
| user_id | Long | 成员用户编号 |

### 8.7 mes_cal_team_shift（班组班次表）

**实体类**：`MesCalTeamShiftDO`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| team_id | Long | 班组编号 |
| name | String | 班次名称 |
| start_time | LocalTime | 开始时间 |
| end_time | LocalTime | 结束时间 |
| is_next_day | Boolean | 是否跨天 |

---

## 9. 表关系（ER 关系）

### 9.1 主数据域

```
mes_md_item ──N:1──> mes_md_item_type          (item_type_id)
mes_md_item ──N:1──> mes_md_warehouse           (default_warehouse_id)
mes_md_item ──N:1──> mes_md_vendor              (default_vendor_id)
mes_md_workstation ──N:1──> mes_md_workshop     (workshop_id)
mes_md_workstation_machine ──N:1──> mes_md_workstation  (workstation_id)
mes_md_workstation_machine ──N:1──> mes_dv_machinery    (machinery_id)
mes_md_workstation_tool ──N:1──> mes_md_workstation     (workstation_id)
mes_md_workstation_tool ──N:1──> mes_tm_tool            (tool_id)
mes_md_workstation_worker ──N:1──> mes_md_workstation   (workstation_id)
mes_md_auto_code_part ──N:1──> mes_md_auto_code_rule    (rule_id)
mes_md_auto_code_record ──N:1──> mes_md_auto_code_rule  (rule_id)
```

### 9.2 生产域

```
mes_pro_work_order ──N:1──> mes_md_item              (item_id)
mes_pro_work_order ──N:1──> mes_md_product_bom       (bom_id)
mes_pro_work_order ──N:1──> mes_pro_route            (route_id)
mes_pro_work_order_bom ──N:1──> mes_pro_work_order   (work_order_id)
mes_pro_task ──N:1──> mes_pro_work_order              (work_order_id)
mes_pro_task ──N:1──> mes_pro_route_process           (route_process_id)
mes_pro_task ──N:1──> mes_md_workstation              (workstation_id)
mes_pro_task ──N:1──> mes_dv_machinery                (machinery_id)
mes_pro_task_issue ──N:1──> mes_pro_task              (task_id)
mes_pro_route_process ──N:1──> mes_pro_route          (route_id)
mes_pro_route_process ──N:1──> mes_pro_process        (process_id)
mes_pro_card ──N:1──> mes_pro_work_order               (work_order_id)
mes_pro_card_process ──N:1──> mes_pro_card            (card_id)
mes_pro_feedback ──N:1──> mes_pro_work_order           (work_order_id)
mes_pro_feedback ──N:1──> mes_pro_task                 (task_id)
mes_pro_andon_record ──N:1──> mes_pro_andon_config     (config_id)
```

### 9.3 质量域

```
mes_qc_template_item ──N:1──> mes_qc_template         (template_id)
mes_qc_template_indicator ──N:1──> mes_qc_template_item  (template_item_id)
mes_qc_iqc_line ──N:1──> mes_qc_iqc                    (iqc_id)
mes_qc_ipqc_line ──N:1──> mes_qc_ipqc                  (ipqc_id)
mes_qc_oqc_line ──N:1──> mes_qc_oqc                    (oqc_id)
mes_qc_rqc_line ──N:1──> mes_qc_rqc                    (rqc_id)
mes_qc_indicator_result ──N:1──> mes_qc_indicator       (indicator_id)
mes_qc_indicator_result_detail ──N:1──> mes_qc_indicator_result  (result_id)
mes_qc_defect_record ──N:1──> mes_qc_defect             (defect_id)
```

### 9.4 设备域

```
mes_dv_machinery ──N:1──> mes_dv_machinery_type         (machinery_type_id)
mes_dv_check_plan_machinery ──N:1──> mes_dv_check_plan   (plan_id)
mes_dv_check_plan_subject ──N:1──> mes_dv_check_plan     (plan_id)
mes_dv_check_record ──N:1──> mes_dv_check_plan           (plan_id)
mes_dv_check_record_line ──N:1──> mes_dv_check_record    (record_id)
mes_dv_mainten_record_line ──N:1──> mes_dv_mainten_record (record_id)
mes_dv_repair_line ──N:1──> mes_dv_repair                (repair_id)
```

### 9.5 仓库域

```
mes_wm_warehouse_area ──N:1──> mes_wm_warehouse          (warehouse_id)
mes_wm_warehouse_location ──N:1──> mes_wm_warehouse_area (area_id)
mes_wm_material_stock ──N:1──> mes_wm_warehouse           (warehouse_id)
mes_wm_material_stock ──N:1──> mes_md_item                (item_id)
mes_wm_material_stock ──N:1──> mes_wm_batch               (batch_id)
mes_wm_arrival_notice_line ──N:1──> mes_wm_arrival_notice (notice_id)
mes_wm_item_receipt_line ──N:1──> mes_wm_item_receipt     (receipt_id)
mes_wm_item_receipt_detail ──N:1──> mes_wm_item_receipt_line (line_id)
mes_wm_package_line ──N:1──> mes_wm_package               (package_id)
mes_wm_stock_taking_task ──N:1──> mes_wm_stock_taking_plan (plan_id)
mes_wm_stock_taking_task_result ──N:1──> mes_wm_stock_taking_task (task_id)
```

### 9.6 日历域

```
mes_cal_plan_shift ──N:1──> mes_cal_plan                 (plan_id)
mes_cal_plan_team ──N:1──> mes_cal_plan                  (plan_id)
mes_cal_plan_team ──N:1──> mes_cal_team                  (team_id)
mes_cal_team_member ──N:1──> mes_cal_team                (team_id)
mes_cal_team_shift ──N:1──> mes_cal_team                 (team_id)
```

---

## 10. 数据访问规范

### Mapper 基类

所有 Mapper 继承 `BaseMapperX<T>`，提供增强查询能力：

```java
@Mapper
public interface MesItemMapper extends BaseMapperX<MesItemDO> {

    default PageResult<MesItemDO> selectPage(MesItemPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<MesItemDO>()
                .likeIfPresent(MesItemDO::getName, reqVO.getName())
                .likeIfPresent(MesItemDO::getCode, reqVO.getCode())
                .eqIfPresent(MesItemDO::getItemTypeId, reqVO.getItemTypeId())
                .eqIfPresent(MesItemDO::getStatus, reqVO.getStatus())
                .orderByDesc(MesItemDO::getId));
    }
}
```

### 关键设计决策

- **金额/数量使用 BigDecimal**：所有金额和数量字段使用 BigDecimal 类型，保证精度
- **逻辑删除**：所有表使用 `deleted` 字段进行逻辑删除
- **Oracle/PG 兼容**：部分表使用 `@KeySequence` 注解兼容不同数据库的主键生成
- **状态枚举统一**：各实体的状态枚举值保持一致（0=初始态，1=进行中，2=完成，3=取消/驳回）
- **主子表结构**：BOM、检验单、出入库单等使用主子表结构，子表通过外键关联主表
