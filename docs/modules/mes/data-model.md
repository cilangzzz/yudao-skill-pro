# MES 数据模型详情 (mes)

> `mes` 模块的核心数据模型，全部实体位于 `dal/dataobject` 包下，按业务域（md/cal/dv/pro/qc/tm/wm）组织。
> 字段表仅列出 `id` 与业务字段，所有表均额外携带 BaseDO 公共列 `creator/create_time/updater/update_time/deleted`。

## 1. 实体继承体系与公共约定

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO
│   ├── creator      String          创建者（system_users.id，INSERT 填充）
│   ├── createTime   LocalDateTime   创建时间（INSERT 填充）
│   ├── updater      String          更新者（INSERT_UPDATE 填充）
│   ├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 填充）
│   └── deleted      Boolean         逻辑删除标记（@TableLogic）
│
├── 主数据管理 (md) 域                 17 个 DO
├── 排班日历 (cal) 域                 7 个 DO
├── 设备管理 (dv) 域                  12 个 DO
├── 生产管理 (pro) 域                 17 个 DO
├── 质量管理 (qc) 域                  16 个 DO
├── 工装工具 (tm) 域                  2 个 DO
├── 仓库管理 (wm) 域                  62 个 DO
│
└── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO（BaseDO + tenantId）
    └── mes 模块【未使用】
```

| 规则 | 说明 |
|------|------|
| 一律继承 BaseDO | 全部 133 个 DO 均直接继承 `BaseDO`，无一继承 `TenantBaseDO`，模块未启用租户隔离 |
| 主键策略 | 每个 DO 标注 `@TableId`（自增），并配置 `@KeySequence("mes_xxx_seq")` 以兼容 Oracle/PostgreSQL 等序列型数据库 |
| 逻辑删除 | 统一 `deleted` 布尔列，`@TableLogic` 自动追加 `deleted = 0` 过滤条件 |
| 列名映射 | 未使用 `@TableField` 指定列名，一律按 MyBatis-Plus 驼峰转下划线规则映射 |
| 集合类型字段 | 仅 `mes_qc_template.types` 使用 `@TableField(typeHandler = IntegerListTypeHandler.class)`，以逗号分隔存储 `List<Integer>` |
| 枚举/字典引用 | 状态、类型等字段在 javadoc 中以「字典 `DictTypeConstants#XXX`」「枚举 `XXXEnum`」标注取值来源 |
| 字段表约定 | 下文各 DO 字段表仅列出 `id` 与业务字段，BaseDO 公共列不再重复罗列 |
| 索引信息来源 | 业务表未在代码中声明索引；单测建表脚本 `yudao-module-mes/src/test/resources/sql/create_tables.sql` 仅覆盖部分表（34 张），生产库以实际 DDL 为准 |

## 2. 各业务域 DO 实体

### 2.1 主数据管理 (md)

#### MesMdAutoCodePartDO (mes_md_auto_code_part)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分段 ID |
| ruleId | Long | rule_id | 规则 ID 关联 MesMdAutoCodeRuleDO |
| sort | Integer | sort | 分段序号 |
| type | Integer | type | 分段类型 字典 MES_MD_AUTO_CODE_PART_TYPE 枚举 MesMdAutoCodePartTypeEnum |
| length | Integer | length | 分段长度 |
| dateFormat | String | date_format | 日期格式 例如：yyyyMMdd、yyyyMM、HHmmss |
| fixCharacter | String | fix_character | 固定字符 |
| serialStartNo | Integer | serial_start_no | 流水号起始值 |
| serialStep | Integer | serial_step | 流水号步长 |
| cycleFlag | Boolean | cycle_flag | 流水号是否循环 |
| cycleMethod | Integer | cycle_method | 循环方式 字典 MES_MD_AUTO_CODE_CYCLE_METHOD 枚举 MesMdAutoCodeCycleMethodEnum |
| remark | String | remark | 备注 |

**说明**: MES 编码规则组成

**继承**: BaseDO　**主键序列**: mes_md_auto_code_part_seq　**关联实体**: MesMdAutoCodeRuleDO

#### MesMdAutoCodeRecordDO (mes_md_auto_code_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 记录 ID |
| ruleId | Long | rule_id | 规则 ID 关联 MesMdAutoCodeRuleDO |
| result | String | result | 生成的编码 |
| serialNo | Long | serial_no | 生成的流水号 当规则组成中包含流水号分段（SERIAL_NUMBER）时记录，方便追溯和调试 |
| inputChar | String | input_char | 传入的参数 |

**说明**: MES 编码生成记录

**继承**: BaseDO　**主键序列**: mes_md_auto_code_record_seq　**关联实体**: MesMdAutoCodeRuleDO

#### MesMdAutoCodeRuleDO (mes_md_auto_code_rule)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 规则 ID |
| code | String | code | 规则编码 |
| name | String | name | 规则名称 |
| description | String | description | 描述 |
| maxLength | Integer | max_length | 最大长度 |
| padded | Boolean | padded | 是否补齐 |
| paddedChar | String | padded_char | 补齐字符 |
| paddedMethod | Integer | padded_method | 补齐方式 字典 MES_MD_AUTO_CODE_PADDED_METHOD 枚举 MesMdAutoCodePaddedMethodEnum |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 编码规则

**继承**: BaseDO　**主键序列**: mes_md_auto_code_rule_seq

#### MesMdClientDO (mes_md_client)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 客户编号 |
| code | String | code | 客户编码 |
| name | String | name | 客户名称 |
| nickname | String | nickname | 客户简称 |
| englishName | String | english_name | 客户英文名称 |
| description | String | description | 客户简介 |
| logo | String | logo | 客户LOGO地址 |
| type | Integer | type | 客户类型 字典 MES_CLIENT_TYPE |
| address | String | address | 客户地址 |
| website | String | website | 客户官网地址 |
| email | String | email | 客户邮箱地址 |
| telephone | String | telephone | 客户电话 |
| contact1Name | String | contact1_name | 联系人1 |
| contact1Telephone | String | contact1_telephone | 联系人1-电话 |
| contact1Email | String | contact1_email | 联系人1-邮箱 |
| contact2Name | String | contact2_name | 联系人2 |
| contact2Telephone | String | contact2_telephone | 联系人2-电话 |
| contact2Email | String | contact2_email | 联系人2-邮箱 |
| creditCode | String | credit_code | 统一社会信用代码 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 客户

**继承**: BaseDO　**主键序列**: mes_md_client_seq

#### MesMdItemBatchConfigDO (mes_md_item_batch_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| produceDateFlag | Boolean | produce_date_flag | 批次属性-生产日期 |
| expireDateFlag | Boolean | expire_date_flag | 批次属性-有效期 |
| receiptDateFlag | Boolean | receipt_date_flag | 批次属性-入库日期 |
| vendorFlag | Boolean | vendor_flag | 批次属性-供应商 |
| clientFlag | Boolean | client_flag | 批次属性-客户 |
| salesOrderCodeFlag | Boolean | sales_order_code_flag | 批次属性-销售订单编号 |
| purchaseOrderCodeFlag | Boolean | purchase_order_code_flag | 批次属性-采购订单编号 |
| workOrderFlag | Boolean | work_order_flag | 批次属性-生产工单 |
| taskFlag | Boolean | task_flag | 批次属性-生产任务 |
| workstationFlag | Boolean | workstation_flag | 批次属性-工作站 |
| toolFlag | Boolean | tool_flag | 批次属性-工具 |
| moldFlag | Boolean | mold_flag | 批次属性-模具 |
| lotNumberFlag | Boolean | lot_number_flag | 批次属性-生产批号 |
| qualityStatusFlag | Boolean | quality_status_flag | 批次属性-质量状态 |

**说明**: MES 物料批次属性配置

**继承**: BaseDO　**主键序列**: mes_md_item_batch_config_seq　**关联实体**: MesMdItemDO

#### MesMdItemDO (mes_md_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 物料编号 |
| code | String | code | 物料编码 |
| name | String | name | 物料名称 |
| specification | String | specification | 规格型号 |
| unitMeasureId | Long | unit_measure_id | 计量单位编号 关联 MesMdUnitMeasureDO |
| itemTypeId | Long | item_type_id | 物料分类编号 关联 MesMdItemTypeDO |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| safeStockFlag | Boolean | safe_stock_flag | 是否启用安全库存 |
| minStock | BigDecimal | min_stock | 最低库存量 |
| maxStock | BigDecimal | max_stock | 最高库存量 |
| highValue | Boolean | high_value | 是否高值物料 |
| batchFlag | Boolean | batch_flag | 是否启用批次管理 |
| remark | String | remark | 备注 |

**说明**: MES 物料产品

**继承**: BaseDO　**主键序列**: mes_md_item_seq　**关联实体**: MesMdUnitMeasureDO、MesMdItemTypeDO

#### MesMdItemTypeDO (mes_md_item_type)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 分类编号 |
| code | String | code | 分类编码 |
| name | String | name | 分类名称 |
| parentId | Long | parent_id | 父分类编号 |
| itemOrProduct | String | item_or_product | 物料/产品标识 字典 MES_MD_ITEM_OR_PRODUCT 枚举 MesMdItemTypeEnum |
| sort | Integer | sort | 显示排序 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 物料产品分类

**继承**: BaseDO　**主键序列**: mes_md_item_type_seq

#### MesMdProductBomDO (mes_md_product_bom)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | BOM编号 |
| itemId | Long | item_id | 物料产品编号 关联 MesMdItemDO |
| bomItemId | Long | bom_item_id | BOM物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 物料使用比例 |
| status | Integer | status | 是否启用 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 产品 BOM

**继承**: BaseDO　**主键序列**: mes_md_product_bom_seq　**关联实体**: MesMdItemDO

#### MesMdProductSipDO (mes_md_product_sip)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| itemId | Long | item_id | 物料产品编号 关联 MesMdItemDO |
| sort | Integer | sort | 排列顺序 |
| processId | Long | process_id | 工序编号 |
| title | String | title | 标题 |
| description | String | description | 详细描述 |
| url | String | url | 图片地址 |
| remark | String | remark | 备注 |

**说明**: MES 产品SIP

**继承**: BaseDO　**主键序列**: mes_md_product_sip_seq　**关联实体**: MesMdItemDO

#### MesMdProductSopDO (mes_md_product_sop)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| itemId | Long | item_id | 物料产品编号 关联 MesMdItemDO |
| sort | Integer | sort | 排列顺序 |
| processId | Long | process_id | 工序编号 |
| title | String | title | 标题 |
| description | String | description | 详细描述 |
| url | String | url | 图片地址 |
| remark | String | remark | 备注 |

**说明**: MES 产品SOP

**继承**: BaseDO　**主键序列**: mes_md_product_sop_seq　**关联实体**: MesMdItemDO

#### MesMdUnitMeasureDO (mes_md_unit_measure)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 单位编号 |
| code | String | code | 单位编码 |
| name | String | name | 单位名称 |
| primaryFlag | Boolean | primary_flag | 是否主单位 |
| primaryId | Long | primary_id | 主单位编号 关联 MesMdUnitMeasureDO |
| changeRate | BigDecimal | change_rate | 与主单位换算比例 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 计量单位

**继承**: BaseDO　**主键序列**: mes_md_unit_measure_seq　**关联实体**: MesMdUnitMeasureDO

#### MesMdVendorDO (mes_md_vendor)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 供应商编号 |
| code | String | code | 供应商编码 |
| name | String | name | 供应商名称 |
| nickname | String | nickname | 供应商简称 |
| englishName | String | english_name | 供应商英文名称 |
| description | String | description | 供应商简介 |
| logo | String | logo | 供应商LOGO地址 |
| level | String | level | 供应商等级 字典 MES_VENDOR_LEVEL |
| score | Integer | score | 供应商评分 |
| address | String | address | 供应商地址 |
| website | String | website | 供应商官网地址 |
| email | String | email | 供应商邮箱地址 |
| telephone | String | telephone | 供应商电话 |
| contact1Name | String | contact1_name | 联系人1 |
| contact1Telephone | String | contact1_telephone | 联系人1-电话 |
| contact1Email | String | contact1_email | 联系人1-邮箱 |
| contact2Name | String | contact2_name | 联系人2 |
| contact2Telephone | String | contact2_telephone | 联系人2-电话 |
| contact2Email | String | contact2_email | 联系人2-邮箱 |
| creditCode | String | credit_code | 统一社会信用代码 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 供应商

**继承**: BaseDO　**主键序列**: mes_md_vendor_seq

#### MesMdWorkshopDO (mes_md_workshop)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 车间编码 |
| name | String | name | 车间名称 |
| area | BigDecimal | area | 面积（平方米） |
| chargeUserId | Long | charge_user_id | 负责人用户编号 关联 AdminUserDO 的 id |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 车间

**继承**: BaseDO　**主键序列**: mes_md_workshop_seq　**关联实体**: AdminUserDO

#### MesMdWorkstationDO (mes_md_workstation)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 工作站编码 |
| name | String | name | 工作站名称 |
| address | String | address | 工作站地点 |
| workshopId | Long | workshop_id | 所在车间编号 关联 MesMdWorkshopDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| warehouseId | Long | warehouse_id | 线边库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 工作站

**继承**: BaseDO　**主键序列**: mes_md_workstation_seq　**关联实体**: MesMdWorkshopDO、MesProProcessDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesMdWorkstationMachineDO (mes_md_workstation_machine)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| machineryId | Long | machinery_id | 设备编号 等 dv 模块，关联设备表 |
| quantity | Integer | quantity | 数量 |
| remark | String | remark | 备注 |

**说明**: MES 设备资源

**继承**: BaseDO　**主键序列**: mes_md_workstation_machine_seq　**关联实体**: MesMdWorkstationDO

#### MesMdWorkstationToolDO (mes_md_workstation_tool)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| toolTypeId | Long | tool_type_id | 工具类型编号 等 tm 模块，关联工具类型表 |
| quantity | Integer | quantity | 数量 |
| remark | String | remark | 备注 |

**说明**: MES 工装夹具资源

**继承**: BaseDO　**主键序列**: mes_md_workstation_tool_seq　**关联实体**: MesMdWorkstationDO

#### MesMdWorkstationWorkerDO (mes_md_workstation_worker)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| postId | Long | post_id | 岗位编号 关联 system_post 的 id |
| quantity | Integer | quantity | 数量 |
| remark | String | remark | 备注 |

**说明**: MES 人力资源

**继承**: BaseDO　**主键序列**: mes_md_workstation_worker_seq　**关联实体**: MesMdWorkstationDO

### 2.2 排班日历 (cal)

#### MesCalHolidayDO (mes_cal_holiday)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| day | LocalDateTime | day | 日期 |
| type | Integer | type | 日期类型 字典 MES_CAL_HOLIDAY_TYPE |
| remark | String | remark | 备注 |

**说明**: MES 假期设置

**继承**: BaseDO　**主键序列**: mes_cal_holiday_seq

#### MesCalPlanDO (mes_cal_plan)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 计划编号 |
| code | String | code | 计划编码 |
| name | String | name | 计划名称 |
| calendarType | Integer | calendar_type | 班组类型 |
| startDate | LocalDateTime | start_date | 开始日期 |
| endDate | LocalDateTime | end_date | 结束日期 |
| shiftType | Integer | shift_type | 轮班方式 字典 MES_CAL_SHIFT_TYPE 枚举 MesCalShiftTypeEnum |
| shiftMethod | Integer | shift_method | 倒班方式 字典 MES_CAL_SHIFT_METHOD 枚举 MesCalShiftMethodEnum |
| shiftCount | Integer | shift_count | 倒班天数 |
| status | Integer | status | 状态 字典 MES_CAL_PLAN_STATUS 枚举 MesCalPlanStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 排班计划

**继承**: BaseDO　**主键序列**: mes_cal_plan_seq

#### MesCalPlanShiftDO (mes_cal_plan_shift)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 班次编号 |
| planId | Long | plan_id | 排班计划编号 关联 MesCalPlanDO |
| sort | Integer | sort | 显示顺序 |
| name | String | name | 班次名称 |
| startTime | String | start_time | 开始时间（HH:mm 格式） |
| endTime | String | end_time | 结束时间（HH:mm 格式） |
| remark | String | remark | 备注 |

**说明**: MES 计划班次

**继承**: BaseDO　**主键序列**: mes_cal_plan_shift_seq　**关联实体**: MesCalPlanDO

#### MesCalPlanTeamDO (mes_cal_plan_team)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 排班计划编号 关联 MesCalPlanDO |
| teamId | Long | team_id | 班组编号 关联 MesCalTeamDO |
| remark | String | remark | 备注 |

**说明**: MES 计划班组关联

**继承**: BaseDO　**主键序列**: mes_cal_plan_team_seq　**关联实体**: MesCalPlanDO、MesCalTeamDO

#### MesCalTeamDO (mes_cal_team)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 班组编号 |
| code | String | code | 班组编码 |
| name | String | name | 班组名称 |
| calendarType | Integer | calendar_type | 班组类型 |
| remark | String | remark | 备注 |

**说明**: MES 班组

**继承**: BaseDO　**主键序列**: mes_cal_team_seq

#### MesCalTeamMemberDO (mes_cal_team_member)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 班组成员编号 |
| teamId | Long | team_id | 班组编号 关联 MesCalTeamDO |
| userId | Long | user_id | 用户编号 关联 system_users 表 |
| remark | String | remark | 备注 |

**说明**: MES 班组成员

**继承**: BaseDO　**主键序列**: mes_cal_team_member_seq　**关联实体**: MesCalTeamDO

#### MesCalTeamShiftDO (mes_cal_team_shift)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 排班计划编号 关联 MesCalPlanDO |
| teamId | Long | team_id | 班组编号 关联 MesCalTeamDO |
| shiftId | Long | shift_id | 班次编号 关联 MesCalPlanShiftDO |
| day | LocalDateTime | day | 日期 |
| sort | Integer | sort | 排序 |
| remark | String | remark | 备注 |

**说明**: MES 班组排班

**继承**: BaseDO　**主键序列**: mes_cal_team_shift_seq　**关联实体**: MesCalPlanDO、MesCalTeamDO、MesCalPlanShiftDO

### 2.3 设备管理 (dv)

#### MesDvCheckPlanDO (mes_dv_check_plan)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 方案编码 |
| name | String | name | 方案名称 |
| type | Integer | type | 方案类型 字典 MES_DV_SUBJECT_TYPE |
| startDate | LocalDateTime | start_date | 开始日期 |
| endDate | LocalDateTime | end_date | 结束日期 |
| cycleType | Integer | cycle_type | 周期类型 字典 MES_DV_CYCLE_TYPE |
| cycleCount | Integer | cycle_count | 周期数量 |
| status | Integer | status | 状态 字典 MES_DV_CHECK_PLAN_STATUS 枚举 MesDvCheckPlanStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 点检保养方案

**继承**: BaseDO　**主键序列**: mes_dv_check_plan_seq

#### MesDvCheckPlanMachineryDO (mes_dv_check_plan_machinery)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 方案编号 关联 MesDvCheckPlanDO |
| machineryId | Long | machinery_id | 设备编号 关联 MesDvMachineryDO |
| remark | String | remark | 备注 |

**说明**: MES 点检保养方案设备

**继承**: BaseDO　**主键序列**: mes_dv_check_plan_machinery_seq　**关联实体**: MesDvCheckPlanDO、MesDvMachineryDO

#### MesDvCheckPlanSubjectDO (mes_dv_check_plan_subject)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 方案编号 关联 MesDvCheckPlanDO |
| subjectId | Long | subject_id | 项目编号 关联 MesDvSubjectDO |
| remark | String | remark | 备注 |

**说明**: MES 点检保养方案项目

**继承**: BaseDO　**主键序列**: mes_dv_check_plan_subject_seq　**关联实体**: MesDvCheckPlanDO、MesDvSubjectDO

#### MesDvCheckRecordDO (mes_dv_check_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 点检计划编号 关联 MesDvCheckPlanDO |
| machineryId | Long | machinery_id | 设备编号 关联 MesDvMachineryDO |
| checkTime | LocalDateTime | check_time | 点检时间 |
| userId | Long | user_id | 点检人编号 关联 AdminUserDO#getId() |
| status | Integer | status | 状态 字典 MES_DV_CHECK_RECORD_STATUS 枚举 MesDvCheckRecordStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 设备点检记录

**继承**: BaseDO　**主键序列**: mes_dv_check_record_seq　**关联实体**: MesDvCheckPlanDO、MesDvMachineryDO、AdminUserDO

#### MesDvCheckRecordLineDO (mes_dv_check_record_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| recordId | Long | record_id | 点检记录编号 关联 MesDvCheckRecordDO |
| subjectId | Long | subject_id | 点检项目编号 关联 MesDvSubjectDO |
| checkStatus | Integer | check_status | 点检结果 字典 MES_DV_CHECK_RESULT 枚举 MesDvCheckResultEnum |
| checkResult | String | check_result | 异常描述 仅 {@link #checkStatus} 为异常时使用 |
| remark | String | remark | 备注 |

**说明**: MES 设备点检记录明细

**继承**: BaseDO　**主键序列**: mes_dv_check_record_line_seq　**关联实体**: MesDvCheckRecordDO、MesDvSubjectDO

#### MesDvMachineryDO (mes_dv_machinery)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 设备编码 |
| name | String | name | 设备名称 |
| brand | String | brand | 品牌 |
| specification | String | specification | 规格型号 |
| machineryTypeId | Long | machinery_type_id | 设备类型编号 关联 MesDvMachineryTypeDO |
| workshopId | Long | workshop_id | 所属车间编号 关联 MesMdWorkshopDO |
| status | Integer | status | 设备状态 字典 MES_DV_MACHINERY_STATUS 枚举 MesDvMachineryStatusEnum |
| lastMaintenTime | LocalDateTime | last_mainten_time | 最近保养时间 |
| lastCheckTime | LocalDateTime | last_check_time | 最近点检时间 |
| remark | String | remark | 备注 |

**说明**: MES 设备台账

**继承**: BaseDO　**主键序列**: mes_dv_machinery_seq　**关联实体**: MesDvMachineryTypeDO、MesMdWorkshopDO

#### MesDvMachineryTypeDO (mes_dv_machinery_type)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 类型编码 |
| name | String | name | 类型名称 |
| parentId | Long | parent_id | 父类型编号 关联 MesDvMachineryTypeDO |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| sort | Integer | sort | 显示排序 |
| remark | String | remark | 备注 |

**说明**: MES 设备类型

**继承**: BaseDO　**主键序列**: mes_dv_machinery_type_seq　**关联实体**: MesDvMachineryTypeDO

#### MesDvMaintenRecordDO (mes_dv_mainten_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 计划编号 关联 MesDvCheckPlanDO |
| machineryId | Long | machinery_id | 设备编号 关联 MesDvMachineryDO |
| maintenTime | LocalDateTime | mainten_time | 保养时间 |
| userId | Long | user_id | 用户编号 关联 AdminUserDO#getId() |
| status | Integer | status | 状态 字典 MES_MAINTEN_RECORD_STATUS 枚举 MesDvMaintenRecordStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 设备保养记录

**继承**: BaseDO　**主键序列**: mes_dv_mainten_record_seq　**关联实体**: MesDvCheckPlanDO、MesDvMachineryDO、AdminUserDO

#### MesDvMaintenRecordLineDO (mes_dv_mainten_record_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| recordId | Long | record_id | 保养记录编号 关联 MesDvMaintenRecordDO |
| subjectId | Long | subject_id | 项目编号 关联 MesDvSubjectDO |
| status | Integer | status | 保养结果 字典 MES_MAINTEN_STATUS 枚举 MesDvMaintenStatusEnum |
| result | String | result | 异常描述 |
| remark | String | remark | 备注 |

**说明**: MES 设备保养记录明细

**继承**: BaseDO　**主键序列**: mes_dv_mainten_record_line_seq　**关联实体**: MesDvMaintenRecordDO、MesDvSubjectDO

#### MesDvRepairDO (mes_dv_repair)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 维修工单编码 |
| name | String | name | 维修工单名称 |
| machineryId | Long | machinery_id | 设备编号 关联 MesDvMachineryDO |
| requireDate | LocalDateTime | require_date | 报修日期 |
| finishDate | LocalDateTime | finish_date | 维修完成日期 |
| confirmDate | LocalDateTime | confirm_date | 验收日期 |
| result | Integer | result | 维修结果 字典 MES_DV_REPAIR_RESULT 枚举 MesDvRepairResultEnum |
| acceptedUserId | Long | accepted_user_id | 维修人用户编号 关联 AdminUserDO#getId() |
| confirmUserId | Long | confirm_user_id | 验收人用户编号 关联 AdminUserDO#getId() |
| sourceDocType | Integer | source_doc_type | 来源单据类型 |
| sourceDocId | Long | source_doc_id | 来源单据编号 |
| sourceDocCode | String | source_doc_code | 来源单据编码 |
| status | Integer | status | 状态 字典 MES_DV_REPAIR_STATUS 枚举 MesDvRepairStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 维修工单

**继承**: BaseDO　**主键序列**: mes_dv_repair_seq　**关联实体**: MesDvMachineryDO、AdminUserDO

#### MesDvRepairLineDO (mes_dv_repair_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| repairId | Long | repair_id | 维修工单编号 关联 MesDvRepairDO |
| subjectId | Long | subject_id | 点检保养项目编号 关联 MesDvSubjectDO |
| malfunction | String | malfunction | 故障描述 |
| malfunctionUrl | String | malfunction_url | 故障图片 URL |
| description | String | description | 维修描述 |
| remark | String | remark | 备注 |

**说明**: MES 维修工单行

**继承**: BaseDO　**主键序列**: mes_dv_repair_line_seq　**关联实体**: MesDvRepairDO、MesDvSubjectDO

#### MesDvSubjectDO (mes_dv_subject)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 项目编码 |
| name | String | name | 项目名称 |
| type | Integer | type | 项目类型 字典类型 mes_dv_subject_type |
| content | String | content | 项目内容 |
| standard | String | standard | 标准 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 点检保养项目

**继承**: BaseDO　**主键序列**: mes_dv_subject_seq

### 2.4 生产管理 (pro)

#### MesProAndonConfigDO (mes_pro_andon_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| reason | String | reason | 呼叫原因 |
| level | Integer | level | 级别 字典 MES_PRO_ANDON_LEVEL 枚举 MesProAndonLevelEnum |
| handlerRoleId | Long | handler_role_id | 处置人角色编号 关联 system_role#id |
| handlerUserId | Long | handler_user_id | 处置人编号 关联 system_users#id |
| remark | String | remark | 备注 |

**说明**: MES 安灯呼叫配置

**继承**: BaseDO　**主键序列**: mes_pro_andon_config_seq

#### MesProAndonRecordDO (mes_pro_andon_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| configId | Long | config_id | 安灯配置编号 关联 MesProAndonConfigDO |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| userId | Long | user_id | 发起用户编号 关联 system_users#id |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| reason | String | reason | 呼叫原因（快照值，不随配置变更） |
| level | Integer | level | 级别（快照值） 字典 MES_PRO_ANDON_LEVEL 枚举 MesProAndonLevelEnum |
| status | Integer | status | 处置状态 字典 MES_PRO_ANDON_STATUS 枚举 MesProAndonStatusEnum |
| handleTime | LocalDateTime | handle_time | 处置时间 |
| handlerUserId | Long | handler_user_id | 处置人编号 关联 system_users#id |
| remark | String | remark | 备注 |

**说明**: MES 安灯呼叫记录

**继承**: BaseDO　**主键序列**: mes_pro_andon_record_seq　**关联实体**: MesProAndonConfigDO、MesMdWorkstationDO、MesProWorkOrderDO、MesProProcessDO

#### MesProCardDO (mes_pro_card)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 流转卡编码 |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| itemId | Long | item_id | 产品物料编号 关联 MesMdItemDO |
| batchCode | String | batch_code | 批次号 |
| transferedQuantity | BigDecimal | transfered_quantity | 流转数量 |
| status | Integer | status | 状态 字典 MES_PRO_WORK_ORDER_STATUS 枚举 MesProWorkOrderStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产流转卡

**继承**: BaseDO　**主键序列**: mes_pro_card_seq　**关联实体**: MesProWorkOrderDO、MesMdItemDO

#### MesProCardProcessDO (mes_pro_card_process)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| cardId | Long | card_id | 流转卡编号 关联 MesProCardDO |
| sort | Integer | sort | 序号 |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| inputTime | LocalDateTime | input_time | 进入工序时间 |
| outputTime | LocalDateTime | output_time | 出工序时间 |
| inputQuantity | BigDecimal | input_quantity | 投入数量 |
| outputQuantity | BigDecimal | output_quantity | 产出数量 |
| unqualifiedQuantity | BigDecimal | unqualified_quantity | 不合格品数量 |
| workstationId | Long | workstation_id | 工位编号 关联 MesMdWorkstationDO |
| userId | Long | user_id | 操作人编号 关联 AdminUserDO#getId() |
| ipqcId | Long | ipqc_id | 过程检验单编号 关联 mes_qc_ipqc 表，等 IPQC 模块迁移后再对接 |
| remark | String | remark | 备注 |

**说明**: MES 流转卡工序记录

**继承**: BaseDO　**主键序列**: mes_pro_card_process_seq　**关联实体**: MesProCardDO、MesProProcessDO、MesMdWorkstationDO、AdminUserDO

#### MesProFeedbackDO (mes_pro_feedback)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 报工单编号 |
| type | Integer | type | 报工类型 字典 MES_PRO_FEEDBACK_TYPE 枚举 MesProFeedbackTypeEnum |
| channel | String | channel | 报工途径 字典类型 mes_pro_feedback_channel |
| feedbackTime | LocalDateTime | feedback_time | 报工时间 |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| routeId | Long | route_id | 工艺路线编号 关联 MesProRouteDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| taskId | Long | task_id | 生产任务编号 |
| itemId | Long | item_id | 产品物料编号（冗余自任务） 关联 MesMdItemDO |
| expireDate | LocalDateTime | expire_date | 过期日期 |
| lotNumber | String | lot_number | 生产批号 预留字段，当前未启用 |
| scheduledQuantity | BigDecimal | scheduled_quantity | 排产数量 |
| feedbackQuantity | BigDecimal | feedback_quantity | 本次报工数量 |
| qualifiedQuantity | BigDecimal | qualified_quantity | 合格品数量 |
| unqualifiedQuantity | BigDecimal | unqualified_quantity | 不良品数量 |
| uncheckQuantity | BigDecimal | uncheck_quantity | 待检测数量 |
| laborScrapQuantity | BigDecimal | labor_scrap_quantity | 工废数量 |
| materialScrapQuantity | BigDecimal | material_scrap_quantity | 料废数量 |
| otherScrapQuantity | BigDecimal | other_scrap_quantity | 其他废品数量 |
| feedbackUserId | Long | feedback_user_id | 报工用户编号 关联 AdminUserDO#getId() |
| approveUserId | Long | approve_user_id | 审核用户编号 关联 AdminUserDO#getId() |
| status | Integer | status | 状态 字典 MES_PRO_FEEDBACK_STATUS 枚举 MesProFeedbackStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产报工

**继承**: BaseDO　**主键序列**: mes_pro_feedback_seq　**关联实体**: MesMdWorkstationDO、MesProRouteDO、MesProProcessDO、MesProWorkOrderDO、MesMdItemDO、AdminUserDO

#### MesProProcessContentDO (mes_pro_process_content)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| sort | Integer | sort | 顺序编号 |
| content | String | content | 步骤说明 |
| device | String | device | 辅助设备 |
| material | String | material | 辅助材料 |
| docUrl | String | doc_url | 材料文档 URL |
| remark | String | remark | 备注 |

**说明**: MES 生产工序内容

**继承**: BaseDO　**主键序列**: mes_pro_process_content_seq　**关联实体**: MesProProcessDO

#### MesProProcessDO (mes_pro_process)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 工序编码 |
| name | String | name | 工序名称 |
| attention | String | attention | 工艺要求 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产工序

**继承**: BaseDO　**主键序列**: mes_pro_process_seq

#### MesProRouteDO (mes_pro_route)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 工艺路线编码 |
| name | String | name | 工艺路线名称 |
| description | String | description | 工艺路线说明 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 工艺路线

**继承**: BaseDO　**主键序列**: mes_pro_route_seq

#### MesProRouteProcessDO (mes_pro_route_process)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| routeId | Long | route_id | 工艺路线编号 关联 MesProRouteDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| sort | Integer | sort | 序号 |
| nextProcessId | Long | next_process_id | 下一道工序编号 关联 MesProProcessDO |
| linkType | Integer | link_type | 与下一道工序关系 字典 MES_PRO_LINK_TYPE 枚举 MesProLinkTypeEnum |
| prepareTime | Integer | prepare_time | 准备时间（分钟） |
| waitTime | Integer | wait_time | 等待时间（分钟） |
| colorCode | String | color_code | 甘特图显示颜色 |
| keyFlag | Boolean | key_flag | 是否关键工序 |
| checkFlag | Boolean | check_flag | 是否质检工序 |
| remark | String | remark | 备注 |

**说明**: MES 工艺路线工序

**继承**: BaseDO　**主键序列**: mes_pro_route_process_seq　**关联实体**: MesProRouteDO、MesProProcessDO

#### MesProRouteProductBomDO (mes_pro_route_product_bom)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| routeId | Long | route_id | 工艺路线编号 关联 MesProRouteDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| productId | Long | product_id | 产品物料编号 关联 MesMdItemDO |
| itemId | Long | item_id | BOM 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 用料比例 |
| remark | String | remark | 备注 |

**说明**: MES 工艺路线产品 BOM

**继承**: BaseDO　**主键序列**: mes_pro_route_product_bom_seq　**关联实体**: MesProRouteDO、MesProProcessDO、MesMdItemDO

#### MesProRouteProductDO (mes_pro_route_product)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| routeId | Long | route_id | 工艺路线编号 关联 MesProRouteDO |
| itemId | Long | item_id | 产品物料编号 关联 MesMdItemDO |
| quantity | Integer | quantity | 生产数量 |
| productionTime | BigDecimal | production_time | 生产用时 |
| timeUnitType | String | time_unit_type | 时间单位 字典 MES_TIME_UNIT_TYPE 枚举 MesTimeUnitTypeEnum |
| remark | String | remark | 备注 |

**说明**: MES 工艺路线产品

**继承**: BaseDO　**主键序列**: mes_pro_route_product_seq　**关联实体**: MesProRouteDO、MesMdItemDO

#### MesProTaskDO (mes_pro_task)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 任务编码 |
| name | String | name | 任务名称 |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| routeId | Long | route_id | 工艺路线编号 关联 MesProRouteDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| itemId | Long | item_id | 产品物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 排产数量 |
| producedQuantity | BigDecimal | produced_quantity | 已生产数量 |
| qualifyQuantity | BigDecimal | qualify_quantity | 合格品数量 |
| unqualifyQuantity | BigDecimal | unqualify_quantity | 不良品数量 |
| changedQuantity | BigDecimal | changed_quantity | 调整数量 |
| clientId | Long | client_id | 客户编号 关联 MesMdClientDO |
| startTime | LocalDateTime | start_time | 开始生产时间 |
| duration | Integer | duration | 生产时长（工作日，1=8小时） |
| endTime | LocalDateTime | end_time | 结束生产时间 |
| colorCode | String | color_code | 甘特图显示颜色 |
| finishDate | LocalDateTime | finish_date | 完成日期 |
| cancelDate | LocalDateTime | cancel_date | 取消日期 |
| status | Integer | status | 任务状态 字典 MES_PRO_TASK_STATUS 枚举 MesProTaskStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产任务

**继承**: BaseDO　**主键序列**: mes_pro_task_seq　**关联实体**: MesProWorkOrderDO、MesMdWorkstationDO、MesProRouteDO、MesProProcessDO、MesMdItemDO、MesMdClientDO

#### MesProTaskIssueDO (mes_pro_task_issue)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| taskId | Long | task_id | 生产任务编号 关联 MesProTaskDO |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| sourceDocType | String | source_doc_type | 来源单据类型 |
| sourceDocId | Long | source_doc_id | 来源单据编号 |
| sourceLineId | Long | source_line_id | 来源单据行编号 |
| sourceDocCode | String | source_doc_code | 来源单据编码 |
| batchCode | String | batch_code | 投料批次 |
| itemId | Long | item_id | 产品物料编号 关联 MesMdItemDO |
| unitMeasureId | Long | unit_measure_id | 单位编号 关联 MesMdUnitMeasureDO |
| issuedQuantity | BigDecimal | issued_quantity | 总投料数量 |
| availableQuantity | BigDecimal | available_quantity | 当前可用数量 |
| usedQuantity | BigDecimal | used_quantity | 当前使用数量 |
| remark | String | remark | 备注 |

**说明**: MES 生产任务投料

**继承**: BaseDO　**主键序列**: mes_pro_task_issue_seq　**关联实体**: MesProTaskDO、MesProWorkOrderDO、MesMdWorkstationDO、MesMdItemDO、MesMdUnitMeasureDO

#### MesProWorkOrderBomDO (mes_pro_work_order_bom)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| itemId | Long | item_id | BOM 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 预计使用量 |
| remark | String | remark | 备注 |

**说明**: MES 生产工单 BOM

**继承**: BaseDO　**主键序列**: mes_pro_work_order_bom_seq　**关联实体**: MesProWorkOrderDO、MesMdItemDO

#### MesProWorkOrderDO (mes_pro_work_order)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 工单编码 |
| name | String | name | 工单名称 |
| type | Integer | type | 工单类型 字典 MES_PRO_WORK_ORDER_TYPE 枚举 MesProWorkOrderTypeEnum |
| orderSourceType | Integer | order_source_type | 来源类型 字典 MES_PRO_WORK_ORDER_SOURCE_TYPE 枚举 MesProWorkOrderSourceTypeEnum |
| orderSourceCode | String | order_source_code | 来源单据编号 |
| productId | Long | product_id | 产品编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 生产数量 |
| quantityProduced | BigDecimal | quantity_produced | 已生产数量 |
| quantityChanged | BigDecimal | quantity_changed | 调整数量 |
| quantityScheduled | BigDecimal | quantity_scheduled | 已排产数量 |
| clientId | Long | client_id | 客户编号 关联 MesMdClientDO |
| vendorId | Long | vendor_id | 供应商编号 关联 MesMdVendorDO |
| batchCode | String | batch_code | 批次号 |
| requestDate | LocalDateTime | request_date | 需求日期 |
| parentId | Long | parent_id | 父工单编号 关联 MesProWorkOrderDO |
| finishDate | LocalDateTime | finish_date | 完成时间 |
| cancelDate | LocalDateTime | cancel_date | 取消时间 |
| status | Integer | status | 工单状态 字典 MES_PRO_WORK_ORDER_STATUS 枚举 MesProWorkOrderStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产工单

**继承**: BaseDO　**主键序列**: mes_pro_work_order_seq　**关联实体**: MesMdItemDO、MesMdClientDO、MesMdVendorDO、MesProWorkOrderDO

#### MesProWorkRecordDO (mes_pro_work_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| userId | Long | user_id | 用户编号 关联 AdminUserDO#getId() |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| type | Integer | type | 当前状态 字典 MES_PRO_WORK_RECORD_TYPE 枚举 MesProWorkRecordTypeEnum |
| clockInTime | LocalDateTime | clock_in_time | 上工时间 |
| clockOutTime | LocalDateTime | clock_out_time | 下工时间 |
| remark | String | remark | 备注 |

**说明**: MES 用户工作站绑定关系（当前快照）

**继承**: BaseDO　**主键序列**: mes_pro_work_record_seq　**关联实体**: AdminUserDO、MesMdWorkstationDO

#### MesProWorkRecordLogDO (mes_pro_work_record_log)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| userId | Long | user_id | 用户编号 关联 AdminUserDO#getId() |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| type | Integer | type | 操作类型 字典 MES_PRO_WORK_RECORD_TYPE 枚举 MesProWorkRecordTypeEnum |
| remark | String | remark | 备注 |

**说明**: MES 上下工记录流水

**继承**: BaseDO　**主键序列**: mes_pro_work_record_log_seq　**关联实体**: AdminUserDO、MesMdWorkstationDO

### 2.5 质量管理 (qc)

#### MesQcDefectDO (mes_qc_defect)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 缺陷编码 |
| name | String | name | 缺陷描述 |
| type | Integer | type | 检测项类型 字典类型 MES_INDICATOR_TYPE |
| level | Integer | level | 缺陷等级 字典 MES_DEFECT_LEVEL 枚举 MesQcDefectLevelEnum |
| remark | String | remark | 备注 |

**说明**: MES 缺陷类型

**继承**: BaseDO　**主键序列**: mes_qc_defect_seq

#### MesQcDefectRecordDO (mes_qc_defect_record)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| qcType | Integer | qc_type | 检验类型 字典 MES_QC_TYPE 枚举 MesQcTypeEnum |
| qcId | Long | qc_id | 检验单 ID 关联 MesQcIqcDO 关联 MesQcIpqcDO |
| lineId | Long | line_id | 检验行 ID 关联 MesQcIqcLineDO 关联 MesQcIpqcLineDO |
| name | String | name | 缺陷描述 |
| level | Integer | level | 缺陷等级 字典 MES_DEFECT_LEVEL 枚举 MesQcDefectLevelEnum |
| quantity | Integer | quantity | 缺陷数量 |
| remark | String | remark | 备注 |

**说明**: MES 质检缺陷记录 通用缺陷记录表，通过 {@link #qcType} 区分检验类型（IQC、IPQC、OQC、RQC），多模块复用

**继承**: BaseDO　**主键序列**: mes_qc_defect_record_seq　**关联实体**: MesQcIqcDO、MesQcIpqcDO、MesQcIqcLineDO、MesQcIpqcLineDO

#### MesQcIndicatorDO (mes_qc_indicator)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 检测项编码 |
| name | String | name | 检测项名称 |
| type | Integer | type | 检测项类型 枚举 MES_INDICATOR_TYPE |
| tool | String | tool | 检测工具 |
| resultType | Integer | result_type | 结果值类型 字典 MES_QC_RESULT_TYPE 枚举 MesQcResultValueTypeEnum |
| resultSpecification | String | result_specification | 结果值属性 1. FILE 时：存 IMG/FILE 2. DICT 时：存字典类型名 |
| remark | String | remark | 备注 |

**说明**: MES 质检指标

**继承**: BaseDO　**主键序列**: mes_qc_indicator_seq

#### MesQcIndicatorResultDO (mes_qc_indicator_result)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 样品编号 |
| qcId | Long | qc_id | 关联质检单 ID（IQC/IPQC/OQC/RQC 的 id） 关联 IQC MesQcIqcDO 关联 IPQC MesQcIpqcDO 关联 OQC MesQcOqcDO 关联 RQC MesQcRqcDO |
| qcType | Integer | qc_type | 质检类型 字典 MES_QC_TYPE 枚举 MesQcTypeEnum |
| itemId | Long | item_id | 产品物料 ID 关联 MesMdItemDO |
| sn | String | sn | 物资 SN |
| remark | String | remark | 备注 |

**说明**: MES 检验结果记录

**继承**: BaseDO　**主键序列**: mes_qc_indicator_result_seq　**关联实体**: MesMdItemDO

#### MesQcIndicatorResultDetailDO (mes_qc_indicator_result_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| resultId | Long | result_id | 关联检验结果 ID 关联 MesQcIndicatorResultDO |
| indicatorId | Long | indicator_id | 检测指标 ID 关联 MesQcIndicatorDO |
| value | String | value | 检测值（统一存为字符串） |
| remark | String | remark | 备注 |

**说明**: MES 检验结果明细记录

**继承**: BaseDO　**主键序列**: mes_qc_indicator_result_detail_seq　**关联实体**: MesQcIndicatorResultDO、MesQcIndicatorDO

#### MesQcIpqcDO (mes_qc_ipqc)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 检验单编号 |
| name | String | name | 检验单名称 |
| type | Integer | type | IPQC 检验类型 字典 MES_IPQC_TYPE |
| templateId | Long | template_id | 检验模板 ID 关联 MesQcTemplateDO |
| sourceDocType | Integer | source_doc_type | 来源单据类型 字典 MES_QC_SOURCE_DOC_TYPE 枚举 MesQcSourceDocTypeEnum |
| sourceDocId | Long | source_doc_id | 来源单据 ID 关联：根据 {@link #sourceDocType} 不同： 1. PRO_FEEDBACK 时，关联 MesProFeedbackDO |
| sourceLineId | Long | source_line_id | 来源单据行 ID 关联：根据 {@link #sourceDocType} 不同： 1. PRO_FEEDBACK 时，关联 MesWmProductProduceLineDO |
| sourceDocCode | String | source_doc_code | 来源单据编号（冗余） |
| workOrderId | Long | work_order_id | 生产工单 ID 关联 MesProWorkOrderDO |
| taskId | Long | task_id | 生产任务 ID 关联 MesProTaskDO |
| workstationId | Long | workstation_id | 工位 ID 关联 MesMdWorkstationDO |
| processId | Long | process_id | 工序 ID 关联 MesProProcessDO |
| itemId | Long | item_id | 产品物料 ID 关联 MesMdItemDO |
| checkQuantity | BigDecimal | check_quantity | 检测数量 |
| qualifiedQuantity | BigDecimal | qualified_quantity | 合格品数量 |
| unqualifiedQuantity | BigDecimal | unqualified_quantity | 不合格品数量 |
| laborScrapQuantity | BigDecimal | labor_scrap_quantity | 工废数量 |
| materialScrapQuantity | BigDecimal | material_scrap_quantity | 料废数量 |
| otherScrapQuantity | BigDecimal | other_scrap_quantity | 其他废品数量 |
| criticalRate | BigDecimal | critical_rate | 致命缺陷率（%） |
| majorRate | BigDecimal | major_rate | 严重缺陷率（%） |
| minorRate | BigDecimal | minor_rate | 轻微缺陷率（%） |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| checkResult | Integer | check_result | 检测结果 字典 MES_QC_CHECK_RESULT 枚举 MesQcCheckResultEnum |
| inspectDate | LocalDateTime | inspect_date | 检测日期 |
| inspectorUserId | Long | inspector_user_id | 检测人员用户 ID 关联 AdminUserDO 的 id |
| status | Integer | status | 状态 字典 MES_ORDER_STATUS 枚举 MesQcStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 过程检验单（IPQC, In-Process Quality Control）

**继承**: BaseDO　**主键序列**: mes_qc_ipqc_seq　**关联实体**: MesQcTemplateDO、MesProFeedbackDO、MesWmProductProduceLineDO、MesProWorkOrderDO、MesProTaskDO、MesMdWorkstationDO、MesProProcessDO、MesMdItemDO、AdminUserDO

#### MesQcIpqcLineDO (mes_qc_ipqc_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| ipqcId | Long | ipqc_id | 过程检验单 ID 关联 MesQcIpqcDO |
| indicatorId | Long | indicator_id | 检测指标 ID 关联 MesQcIndicatorDO |
| tool | String | tool | 检测工具 冗余 MesQcIndicatorDO |
| checkMethod | String | check_method | 检测方法 |
| standardValue | BigDecimal | standard_value | 标准值 |
| unitMeasureId | Long | unit_measure_id | 计量单位 ID 关联 MesMdUnitMeasureDO |
| maxThreshold | BigDecimal | max_threshold | 误差上限 |
| minThreshold | BigDecimal | min_threshold | 误差下限 |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| remark | String | remark | 备注 |

**说明**: MES 过程检验单行

**继承**: BaseDO　**主键序列**: mes_qc_ipqc_line_seq　**关联实体**: MesQcIpqcDO、MesQcIndicatorDO、MesMdUnitMeasureDO

#### MesQcIqcDO (mes_qc_iqc)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 检验单编号 |
| name | String | name | 检验单名称 |
| templateId | Long | template_id | 检验模板 ID 关联 MesQcTemplateDO |
| sourceDocType | Integer | source_doc_type | 来源单据类型 字典 MES_QC_SOURCE_DOC_TYPE 枚举 MesQcSourceDocTypeEnum |
| sourceDocId | Long | source_doc_id | 来源单据 ID 关联：根据 {@link #sourceDocType} 不同： 1. ARRIVAL_NOTICE 时，关联 MesWmArrivalNoticeDO |
| sourceLineId | Long | source_line_id | 来源单据行 ID 关联：根据 {@link #sourceDocType} 不同： 1. ARRIVAL_NOTICE 时，关联 MesWmArrivalNoticeLineDO |
| sourceDocCode | String | source_doc_code | 来源单据编号（冗余） |
| vendorId | Long | vendor_id | 供应商 ID 关联 MesMdVendorDO |
| vendorBatch | String | vendor_batch | 供应商批次号 |
| itemId | Long | item_id | 产品物料 ID 关联 MesMdItemDO |
| receivedQuantity | BigDecimal | received_quantity | 本次接收数量 |
| checkQuantity | BigDecimal | check_quantity | 本次检测数量 |
| qualifiedQuantity | BigDecimal | qualified_quantity | 合格品数量 |
| unqualifiedQuantity | BigDecimal | unqualified_quantity | 不合格品数量 |
| criticalRate | BigDecimal | critical_rate | 致命缺陷率（%） |
| majorRate | BigDecimal | major_rate | 严重缺陷率（%） |
| minorRate | BigDecimal | minor_rate | 轻微缺陷率（%） |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| checkResult | Integer | check_result | 检测结果 字典 MES_QC_CHECK_RESULT 枚举 MesQcCheckResultEnum |
| receiveDate | LocalDateTime | receive_date | 来料日期 |
| inspectDate | LocalDateTime | inspect_date | 检测日期 |
| inspectorUserId | Long | inspector_user_id | 检测人员用户 ID 关联 AdminUserDO 的 id |
| status | Integer | status | 状态 字典 MES_ORDER_STATUS 枚举 MesQcStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 来料检验单（IQC, Incoming Quality Control）

**继承**: BaseDO　**主键序列**: mes_qc_iqc_seq　**关联实体**: MesQcTemplateDO、MesWmArrivalNoticeDO、MesWmArrivalNoticeLineDO、MesMdVendorDO、MesMdItemDO、AdminUserDO

#### MesQcIqcLineDO (mes_qc_iqc_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| iqcId | Long | iqc_id | 来料检验单 ID 关联 MesQcIqcDO |
| indicatorId | Long | indicator_id | 检测指标 ID 关联 MesQcIndicatorDO |
| tool | String | tool | 检测工具 冗余 MesQcIndicatorDO |
| checkMethod | String | check_method | 检测方法 |
| standardValue | BigDecimal | standard_value | 标准值 |
| unitMeasureId | Long | unit_measure_id | 计量单位 ID 关联 MesMdUnitMeasureDO |
| maxThreshold | BigDecimal | max_threshold | 误差上限 |
| minThreshold | BigDecimal | min_threshold | 误差下限 |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| remark | String | remark | 备注 |

**说明**: MES 来料检验单行

**继承**: BaseDO　**主键序列**: mes_qc_iqc_line_seq　**关联实体**: MesQcIqcDO、MesQcIndicatorDO、MesMdUnitMeasureDO

#### MesQcOqcDO (mes_qc_oqc)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 检验单编号 |
| name | String | name | 检验单名称 |
| templateId | Long | template_id | 检验模板 ID 关联 MesQcTemplateDO |
| sourceDocType | Integer | source_doc_type | 来源单据类型 字典 MES_QC_SOURCE_DOC_TYPE 枚举 MesQcSourceDocTypeEnum |
| sourceDocId | Long | source_doc_id | 来源单据 ID 关联：根据 {@link #sourceDocType} 不同： 1. PRODUCT_SALES 时，关联 MesWmProductSalesDO |
| sourceLineId | Long | source_line_id | 来源单据行 ID 关联：根据 {@link #sourceDocType} 不同： 1. PRODUCT_SALES 时，关联 MesWmProductSalesLineDO |
| sourceDocCode | String | source_doc_code | 来源单据编号（冗余） |
| clientId | Long | client_id | 客户 ID 关联 MesMdClientDO |
| batchCode | String | batch_code | 批次号 |
| itemId | Long | item_id | 产品物料 ID 关联 MesMdItemDO |
| minCheckQuantity | Integer | min_check_quantity | 最低检测数 |
| maxUnqualifiedQuantity | Integer | max_unqualified_quantity | 最大不合格数 |
| outQuantity | BigDecimal | out_quantity | 本次出货数量 |
| checkQuantity | BigDecimal | check_quantity | 本次检测数量 |
| qualifiedQuantity | BigDecimal | qualified_quantity | 合格品数量 |
| unqualifiedQuantity | BigDecimal | unqualified_quantity | 不合格品数量 |
| criticalRate | BigDecimal | critical_rate | 致命缺陷率（%） |
| majorRate | BigDecimal | major_rate | 严重缺陷率（%） |
| minorRate | BigDecimal | minor_rate | 轻微缺陷率（%） |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| checkResult | Integer | check_result | 检测结果 字典 MES_QC_CHECK_RESULT 枚举 MesQcCheckResultEnum |
| outDate | LocalDateTime | out_date | 出货日期 |
| inspectDate | LocalDateTime | inspect_date | 检测日期 |
| inspectorUserId | Long | inspector_user_id | 检测人员用户 ID 关联 AdminUserDO 的 id |
| status | Integer | status | 状态 字典 MES_ORDER_STATUS 枚举 MesQcStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 出货检验单（OQC, Outgoing Quality Control）

**继承**: BaseDO　**主键序列**: mes_qc_oqc_seq　**关联实体**: MesQcTemplateDO、MesWmProductSalesDO、MesWmProductSalesLineDO、MesMdClientDO、MesMdItemDO、AdminUserDO

#### MesQcOqcLineDO (mes_qc_oqc_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| oqcId | Long | oqc_id | 出货检验单 ID 关联 MesQcOqcDO |
| indicatorId | Long | indicator_id | 检测指标 ID 关联 MesQcIndicatorDO |
| tool | String | tool | 检测工具 冗余 MesQcIndicatorDO |
| checkMethod | String | check_method | 检测方法 |
| standardValue | BigDecimal | standard_value | 标准值 |
| unitMeasureId | Long | unit_measure_id | 计量单位 ID 关联 MesMdUnitMeasureDO |
| maxThreshold | BigDecimal | max_threshold | 误差上限 |
| minThreshold | BigDecimal | min_threshold | 误差下限 |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| remark | String | remark | 备注 |

**说明**: MES 出货检验单行

**继承**: BaseDO　**主键序列**: mes_qc_oqc_line_seq　**关联实体**: MesQcOqcDO、MesQcIndicatorDO、MesMdUnitMeasureDO

#### MesQcRqcDO (mes_qc_rqc)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 检验单编号 |
| name | String | name | 检验单名称 |
| templateId | Long | template_id | 检验模板 ID 关联 MesQcTemplateDO |
| sourceDocType | Integer | source_doc_type | 来源单据类型 关联 MesBizTypeConstants |
| sourceDocId | Long | source_doc_id | 来源单据 ID |
| sourceLineId | Long | source_line_id | 来源单据行 ID |
| sourceDocCode | String | source_doc_code | 来源单据编码（冗余） |
| type | Integer | type | 检验类型 字典 mes_rqc_type |
| itemId | Long | item_id | 产品物料 ID 关联 MesMdItemDO |
| batchCode | String | batch_code | 批次号 |
| checkQuantity | BigDecimal | check_quantity | 检测数量 |
| qualifiedQuantity | BigDecimal | qualified_quantity | 合格品数量 |
| unqualifiedQuantity | BigDecimal | unqualified_quantity | 不合格数量 |
| criticalRate | BigDecimal | critical_rate | 致命缺陷率（%） |
| majorRate | BigDecimal | major_rate | 严重缺陷率（%） |
| minorRate | BigDecimal | minor_rate | 轻微缺陷率（%） |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| checkResult | Integer | check_result | 检测结果 字典 MES_QC_CHECK_RESULT 枚举 MesQcCheckResultEnum |
| inspectDate | LocalDateTime | inspect_date | 检测日期 |
| inspectorUserId | Long | inspector_user_id | 检测人员用户 ID 关联 AdminUserDO 的 id |
| status | Integer | status | 状态 字典 MES_ORDER_STATUS 枚举 MesQcStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 退货检验单（RQC, Return Quality Control）

**继承**: BaseDO　**主键序列**: mes_qc_rqc_seq　**关联实体**: MesQcTemplateDO、MesMdItemDO、AdminUserDO

#### MesQcRqcLineDO (mes_qc_rqc_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| rqcId | Long | rqc_id | 退货检验单 ID 关联 MesQcRqcDO |
| indicatorId | Long | indicator_id | 检测指标 ID 关联 MesQcIndicatorDO |
| tool | String | tool | 检测工具 冗余 MesQcIndicatorDO |
| checkMethod | String | check_method | 检测方法 |
| standardValue | BigDecimal | standard_value | 标准值 |
| unitMeasureId | Long | unit_measure_id | 计量单位 ID 关联 MesMdUnitMeasureDO |
| maxThreshold | BigDecimal | max_threshold | 误差上限 |
| minThreshold | BigDecimal | min_threshold | 误差下限 |
| criticalQuantity | Integer | critical_quantity | 致命缺陷数量 |
| majorQuantity | Integer | major_quantity | 严重缺陷数量 |
| minorQuantity | Integer | minor_quantity | 轻微缺陷数量 |
| remark | String | remark | 备注 |

**说明**: MES 退货检验行

**继承**: BaseDO　**主键序列**: mes_qc_rqc_line_seq　**关联实体**: MesQcRqcDO、MesQcIndicatorDO、MesMdUnitMeasureDO

#### MesQcTemplateDO (mes_qc_template)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 方案编号 |
| name | String | name | 方案名称 |
| types | List<Integer> | types | 检测种类 字典 MES_QC_TYPE（IntegerListTypeHandler，逗号分隔存储） |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 质检方案

**继承**: BaseDO　**主键序列**: mes_qc_template_seq

#### MesQcTemplateIndicatorDO (mes_qc_template_indicator)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| templateId | Long | template_id | 质检方案编号 关联 MesQcTemplateDO |
| indicatorId | Long | indicator_id | 质检指标编号 关联 MesQcIndicatorDO |
| checkMethod | String | check_method | 检测方法 |
| standardValue | BigDecimal | standard_value | 标准值 |
| unitMeasureId | Long | unit_measure_id | 计量单位编号 关联 MesMdUnitMeasureDO |
| thresholdMax | BigDecimal | threshold_max | 误差上限 |
| thresholdMin | BigDecimal | threshold_min | 误差下限 |
| docUrl | String | doc_url | 说明图 URL |
| remark | String | remark | 备注 |

**说明**: MES 质检方案-检测指标项

**继承**: BaseDO　**主键序列**: mes_qc_template_indicator_seq　**关联实体**: MesQcTemplateDO、MesQcIndicatorDO、MesMdUnitMeasureDO

#### MesQcTemplateItemDO (mes_qc_template_item)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| templateId | Long | template_id | 质检方案编号 关联 MesQcTemplateDO |
| itemId | Long | item_id | 产品物料编号 关联 MesMdItemDO |
| quantityCheck | Integer | quantity_check | 最低检测数 |
| quantityUnqualified | Integer | quantity_unqualified | 最大不合格数（0=不启用） |
| criticalRate | BigDecimal | critical_rate | 最大致命缺陷率（%，0=不允许） |
| majorRate | BigDecimal | major_rate | 最大严重缺陷率（%，0=不允许） |
| minorRate | BigDecimal | minor_rate | 最大轻微缺陷率（%） |
| remark | String | remark | 备注 |

**说明**: MES 质检方案-产品关联

**继承**: BaseDO　**主键序列**: mes_qc_template_item_seq　**关联实体**: MesQcTemplateDO、MesMdItemDO

### 2.6 工装工具 (tm)

#### MesTmToolDO (mes_tm_tool)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 工具编码 |
| name | String | name | 工具名称 |
| brand | String | brand | 品牌 |
| specification | String | specification | 型号规格 |
| toolTypeId | Long | tool_type_id | 工具类型编号 关联 MesTmToolTypeDO |
| quantity | Integer | quantity | 数量 |
| availableQuantity | Integer | available_quantity | 可用数量 |
| maintenType | Integer | mainten_type | 保养维护类型 字典 MES_TM_MAINTEN_TYPE 枚举 MesTmMaintenTypeEnum |
| nextMaintenPeriod | Integer | next_mainten_period | 下次保养周期（次数） |
| nextMaintenDate | LocalDateTime | next_mainten_date | 下次保养日期 |
| status | Integer | status | 状态 字典 MES_TM_TOOL_STATUS 枚举 MesTmToolStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 工具台账

**继承**: BaseDO　**主键序列**: mes_tm_tool_seq　**关联实体**: MesTmToolTypeDO

#### MesTmToolTypeDO (mes_tm_tool_type)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 类型编码 |
| name | String | name | 类型名称 |
| codeFlag | Boolean | code_flag | 是否编码管理 |
| maintenType | Integer | mainten_type | 保养维护类型 字典 MES_TM_MAINTEN_TYPE 枚举 MesTmMaintenTypeEnum |
| maintenPeriod | Integer | mainten_period | 保养周期 |
| remark | String | remark | 备注 |

**说明**: MES 工具类型

**继承**: BaseDO　**主键序列**: mes_tm_tool_type_seq

### 2.7 仓库管理 (wm)

#### MesWmArrivalNoticeDO (mes_wm_arrival_notice)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 通知单编码 |
| name | String | name | 通知单名称 |
| purchaseOrderCode | String | purchase_order_code | 采购订单编号 |
| vendorId | Long | vendor_id | 供应商编号 关联 MesMdVendorDO |
| arrivalDate | LocalDateTime | arrival_date | 到货日期 |
| contactName | String | contact_name | 联系人 |
| contactTelephone | String | contact_telephone | 联系电话 |
| status | Integer | status | 状态 字典 MES_WM_ARRIVAL_NOTICE_STATUS 枚举 MesWmArrivalNoticeStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 到货通知单

**继承**: BaseDO　**主键序列**: mes_wm_arrival_notice_seq　**关联实体**: MesMdVendorDO

#### MesWmArrivalNoticeLineDO (mes_wm_arrival_notice_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| noticeId | Long | notice_id | 到货通知单编号 关联 MesWmArrivalNoticeDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| arrivalQuantity | BigDecimal | arrival_quantity | 到货数量 |
| qualifiedQuantity | BigDecimal | qualified_quantity | 合格数量 |
| iqcCheckFlag | Boolean | iqc_check_flag | 是否需要来料检验 |
| iqcId | Long | iqc_id | 来料检验单编号 关联 MesQcIqcDO |
| remark | String | remark | 备注 |

**说明**: MES 到货通知单行

**继承**: BaseDO　**主键序列**: mes_wm_arrival_notice_line_seq　**关联实体**: MesWmArrivalNoticeDO、MesMdItemDO、MesQcIqcDO

#### MesWmBarcodeConfigDO (mes_wm_barcode_config)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| format | Integer | format | 条码格式 字典 MES_BARCODE_FORMAT 枚举 BarcodeFormatEnum |
| bizType | Integer | biz_type | 业务类型 字典 MES_BARCODE_BIZ_TYPE 枚举 BarcodeBizTypeEnum |
| contentFormat | String | content_format | 内容格式模板（支持 {BUSINESSCODE} 占位符） |
| contentExample | String | content_example | 内容样例 |
| autoGenerateFlag | Boolean | auto_generate_flag | 是否自动生成 |
| defaultTemplate | String | default_template | 默认打印模板 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 条码配置

**继承**: BaseDO　**主键序列**: mes_wm_barcode_config_seq

#### MesWmBarcodeDO (mes_wm_barcode)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| configId | Long | config_id | 条码配置编号 关联 MesWmBarcodeConfigDO |
| format | Integer | format | 条码格式 字典 MES_BARCODE_FORMAT 枚举 BarcodeFormatEnum |
| bizType | Integer | biz_type | 业务类型 字典 MES_BARCODE_BIZ_TYPE 枚举 BarcodeBizTypeEnum |
| content | String | content | 条码内容（核心字段，前端根据此内容生成条码图片） |
| bizId | Long | biz_id | 业务编号 |
| bizCode | String | biz_code | 业务编码 |
| bizName | String | biz_name | 业务名称 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 条码清单

**继承**: BaseDO　**主键序列**: mes_wm_barcode_seq　**关联实体**: MesWmBarcodeConfigDO

#### MesWmBatchDO (mes_wm_batch)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 批次ID |
| code | String | code | 批次编码 |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| produceDate | LocalDateTime | produce_date | 生产日期 |
| expireDate | LocalDateTime | expire_date | 有效期 |
| receiptDate | LocalDateTime | receipt_date | 入库日期 |
| vendorId | Long | vendor_id | 供应商ID 关联 MesMdVendorDO |
| clientId | Long | client_id | 客户ID 关联 MesMdClientDO |
| salesOrderCode | String | sales_order_code | 销售订单编号 |
| purchaseOrderCode | String | purchase_order_code | 采购订单编号 |
| workOrderId | Long | work_order_id | 生产工单ID 关联 MesProWorkOrderDO |
| taskId | Long | task_id | 生产任务ID 关联 MesProTaskDO |
| workstationId | Long | workstation_id | 工作站ID 关联 MesMdWorkstationDO |
| toolId | Long | tool_id | 工具ID 关联 MesTmToolDO |
| moldId | Long | mold_id | 模具 ID |
| lotNumber | String | lot_number | 生产批号 |
| qualityStatus | Integer | quality_status | 质量状态 |
| remark | String | remark | 备注 |

**说明**: 批次管理

**继承**: BaseDO　**主键序列**: mes_wm_batch_seq　**关联实体**: MesMdItemDO、MesMdVendorDO、MesMdClientDO、MesProWorkOrderDO、MesProTaskDO、MesMdWorkstationDO、MesTmToolDO

#### MesWmItemConsumeDO (mes_wm_item_consume)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| taskId | Long | task_id | 生产任务编号 关联 MesProTaskDO |
| workstationId | Long | workstation_id | 工作站编号 关联 MesMdWorkstationDO |
| processId | Long | process_id | 工序编号 关联 MesProProcessDO |
| feedbackId | Long | feedback_id | 报工记录编号 关联 MesProFeedbackDO |
| consumeDate | LocalDateTime | consume_date | 消耗日期 |
| status | Integer | status | 状态 字典 MES_WM_ITEM_CONSUME_STATUS 枚举 MesWmItemConsumeStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 物料消耗记录

**继承**: BaseDO　**主键序列**: mes_wm_item_consume_seq　**关联实体**: MesProWorkOrderDO、MesProTaskDO、MesMdWorkstationDO、MesProProcessDO、MesProFeedbackDO

#### MesWmItemConsumeDetailDO (mes_wm_item_consume_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| consumeId | Long | consume_id | 消耗记录编号 关联 MesWmItemConsumeDO |
| lineId | Long | line_id | 消耗记录行编号 关联 MesWmItemConsumeLineDO |
| materialStockId | Long | material_stock_id | 库存台账编号 关联 MesWmMaterialStockDO 当线边库中无可用库存时为 null |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 消耗数量 |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 冗余 MesWmBatchDO |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 物料消耗记录明细 记录 line 级别的消耗按线边库 FIFO 分配到具体批次的明细。 一条 line 可能拆分为多条 detail（当一个批次库存不够，需要从下一个批次继续分配时）。

**继承**: BaseDO　**主键序列**: mes_wm_item_consume_detail_seq　**关联实体**: MesWmItemConsumeDO、MesWmItemConsumeLineDO、MesWmMaterialStockDO、MesMdItemDO、MesWmBatchDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmItemConsumeLineDO (mes_wm_item_consume_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| consumeId | Long | consume_id | 消耗记录编号 关联 MesWmItemConsumeDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 消耗数量 |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 冗余 MesWmBatchDO |
| remark | String | remark | 备注 |

**说明**: MES 物料消耗记录行

**继承**: BaseDO　**主键序列**: mes_wm_item_consume_line_seq　**关联实体**: MesWmItemConsumeDO、MesMdItemDO、MesWmBatchDO

#### MesWmItemReceiptDO (mes_wm_item_receipt)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 入库单编码 |
| name | String | name | 入库单名称 |
| iqcId | Long | iqc_id | 来料检验单编号 关联 MesQcIqcDO |
| noticeId | Long | notice_id | 到货通知单编号 关联 MesWmArrivalNoticeDO |
| purchaseOrderCode | String | purchase_order_code | 采购订单号 冗余自 MesWmArrivalNoticeDO，也可以手动填写 |
| vendorId | Long | vendor_id | 供应商编号 关联 MesMdVendorDO |
| receiptDate | LocalDateTime | receipt_date | 入库日期 |
| status | Integer | status | 状态 字典 MES_WM_ITEM_RECEIPT_STATUS 枚举 MesWmItemReceiptStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 采购入库单

**继承**: BaseDO　**主键序列**: mes_wm_item_receipt_seq　**关联实体**: MesQcIqcDO、MesWmArrivalNoticeDO、MesMdVendorDO

#### MesWmItemReceiptDetailDO (mes_wm_item_receipt_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| lineId | Long | line_id | 入库单行编号 关联 MesWmItemReceiptLineDO |
| receiptId | Long | receipt_id | 入库单编号 关联 MesWmItemReceiptDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 上架数量 |
| batchId | Long | batch_id | 批次编号 保留。待 mes_wm_batch 模块迁移后补充 @link 关联 |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 采购入库明细

**继承**: BaseDO　**主键序列**: mes_wm_item_receipt_detail_seq　**关联实体**: MesWmItemReceiptLineDO、MesWmItemReceiptDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmItemReceiptLineDO (mes_wm_item_receipt_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| receiptId | Long | receipt_id | 入库单编号 关联 MesWmItemReceiptDO |
| arrivalNoticeLineId | Long | arrival_notice_line_id | 到货通知单行编号 关联 MesWmArrivalNoticeLineDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| receivedQuantity | BigDecimal | received_quantity | 入库数量 |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次编码 关联 MesWmBatchDO |
| productionDate | LocalDateTime | production_date | 生产日期 |
| expireDate | LocalDateTime | expire_date | 有效期 |
| lotNumber | String | lot_number | 生产批号 |
| remark | String | remark | 备注 |

**说明**: MES 采购入库单行

**继承**: BaseDO　**主键序列**: mes_wm_item_receipt_line_seq　**关联实体**: MesWmItemReceiptDO、MesWmArrivalNoticeLineDO、MesMdItemDO、MesWmBatchDO

#### MesWmMaterialStockDO (mes_wm_material_stock)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| itemTypeId | Long | item_type_id | 物料分类编号 关联 MesMdItemTypeDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| vendorId | Long | vendor_id | 供应商编号 关联 MesMdVendorDO |
| quantity | BigDecimal | quantity | 在库数量 |
| receiptTime | LocalDateTime | receipt_time | 入库时间 |
| frozen | Boolean | frozen | 是否冻结 |

**说明**: MES 库存台账（仓库现有量）

**继承**: BaseDO　**主键序列**: mes_wm_material_stock_seq　**关联实体**: MesMdItemTypeDO、MesMdItemDO、MesWmBatchDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO、MesMdVendorDO

#### MesWmMiscIssueDO (mes_wm_misc_issue)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 出库单编号 |
| name | String | name | 出库单名称 |
| type | Integer | type | 杂项类型 字典 MES_WM_MISC_ISSUE_TYPE 枚举 MesWmMiscIssueTypeEnum |
| sourceDocType | String | source_doc_type | 来源单据类型 |
| sourceDocId | Long | source_doc_id | 来源单据 ID |
| sourceDocCode | String | source_doc_code | 来源单据编号 |
| issueDate | LocalDateTime | issue_date | 出库日期 |
| status | Integer | status | 状态 字典 MES_WM_MISC_ISSUE_STATUS 枚举 MesWmMiscIssueStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 杂项出库单

**继承**: BaseDO　**主键序列**: mes_wm_misc_issue_seq

#### MesWmMiscIssueDetailDO (mes_wm_misc_issue_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| issueId | Long | issue_id | 出库单ID 关联 MesWmMiscIssueDO |
| lineId | Long | line_id | 行ID 关联 MesWmMiscIssueLineDO |
| materialStockId | Long | material_stock_id | 库存记录ID 关联 MesWmMaterialStockDO |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 出库数量 |
| batchId | Long | batch_id | 批次ID |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 杂项出库明细

**继承**: BaseDO　**主键序列**: mes_wm_misc_issue_detail_seq　**关联实体**: MesWmMiscIssueDO、MesWmMiscIssueLineDO、MesWmMaterialStockDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmMiscIssueLineDO (mes_wm_misc_issue_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| issueId | Long | issue_id | 出库单编号 关联 MesWmMiscIssueDO |
| sourceDocLineId | Long | source_doc_line_id | 来源单据行ID |
| materialStockId | Long | material_stock_id | 库存记录ID |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 出库数量 |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 挂你兰 MesWmBatchDO |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 杂项出库单行

**继承**: BaseDO　**主键序列**: mes_wm_misc_issue_line_seq　**关联实体**: MesWmMiscIssueDO、MesMdItemDO、MesWmBatchDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmMiscReceiptDO (mes_wm_misc_receipt)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 入库单编码 |
| name | String | name | 入库单名称 |
| type | Integer | type | 杂项类型 字典 MES_WM_MISC_RECEIPT_TYPE |
| sourceDocType | String | source_doc_type | 来源单据类型 |
| sourceDocId | Long | source_doc_id | 来源单据 ID |
| sourceDocCode | String | source_doc_code | 来源单据编码 |
| receiptDate | LocalDateTime | receipt_date | 入库日期 |
| status | Integer | status | 状态 字典 MES_WM_MISC_RECEIPT_STATUS 枚举 MesWmMiscReceiptStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 杂项入库单

**继承**: BaseDO　**主键序列**: mes_wm_misc_receipt_seq

#### MesWmMiscReceiptDetailDO (mes_wm_misc_receipt_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| receiptId | Long | receipt_id | 入库单ID 关联 MesWmMiscReceiptDO |
| lineId | Long | line_id | 行ID 关联 MesWmMiscReceiptLineDO |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 入库数量 |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 杂项入库明细

**继承**: BaseDO　**主键序列**: mes_wm_misc_receipt_detail_seq　**关联实体**: MesWmMiscReceiptDO、MesWmMiscReceiptLineDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmMiscReceiptLineDO (mes_wm_misc_receipt_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| receiptId | Long | receipt_id | 入库单编号 关联 MesWmMiscReceiptDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 入库数量 |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 杂项入库单行

**继承**: BaseDO　**主键序列**: mes_wm_misc_receipt_line_seq　**关联实体**: MesWmMiscReceiptDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmOutsourceIssueDO (mes_wm_outsource_issue)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 发料单ID |
| code | String | code | 发料单编号 |
| name | String | name | 发料单名称 |
| vendorId | Long | vendor_id | 供应商ID 关联 MesMdVendorDO |
| workOrderId | Long | work_order_id | 生产工单ID 关联 MesProWorkOrderDO |
| issueDate | LocalDateTime | issue_date | 发料日期 |
| status | Integer | status | 单据状态 字典 MES_WM_OUTSOURCE_ISSUE_STATUS 枚举 MesWmOutsourceIssueStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 外协发料单

**继承**: BaseDO　**主键序列**: mes_wm_outsource_issue_seq　**关联实体**: MesMdVendorDO、MesProWorkOrderDO

#### MesWmOutsourceIssueDetailDO (mes_wm_outsource_issue_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 明细ID |
| lineId | Long | line_id | 行ID 关联 MesWmOutsourceIssueLineDO |
| issueId | Long | issue_id | 发料单ID 关联 MesWmOutsourceIssueDO |
| materialStockId | Long | material_stock_id | 库存ID 关联 MesWmMaterialStockDO |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 数量 |
| batchId | Long | batch_id | 批次ID |
| warehouseId | Long | warehouse_id | 仓库ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库位ID |
| areaId | Long | area_id | 库区ID |
| remark | String | remark | 备注 |

**说明**: MES 外协发料单明细

**继承**: BaseDO　**主键序列**: mes_wm_outsource_issue_detail_seq　**关联实体**: MesWmOutsourceIssueLineDO、MesWmOutsourceIssueDO、MesWmMaterialStockDO、MesMdItemDO、MesWmWarehouseDO

#### MesWmOutsourceIssueLineDO (mes_wm_outsource_issue_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 行ID |
| issueId | Long | issue_id | 发料单ID 关联 MesWmOutsourceIssueDO |
| materialStockId | Long | material_stock_id | 库存ID |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 发料数量 |
| batchId | Long | batch_id | 批次ID |
| remark | String | remark | 备注 |

**说明**: MES 外协发料单行

**继承**: BaseDO　**主键序列**: mes_wm_outsource_issue_line_seq　**关联实体**: MesWmOutsourceIssueDO、MesMdItemDO

#### MesWmOutsourceReceiptDO (mes_wm_outsource_receipt)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 入库单编码 |
| name | String | name | 入库单名称 |
| workOrderId | Long | work_order_id | 外协工单编号 关联 MesProWorkOrderDO |
| vendorId | Long | vendor_id | 供应商编号 关联 MesMdVendorDO |
| receiptDate | LocalDateTime | receipt_date | 入库日期 |
| status | Integer | status | 状态 字典 MES_WM_OUTSOURCE_RECEIPT_STATUS 枚举 MesWmOutsourceReceiptStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 外协入库单

**继承**: BaseDO　**主键序列**: mes_wm_outsource_receipt_seq　**关联实体**: MesProWorkOrderDO、MesMdVendorDO

#### MesWmOutsourceReceiptDetailDO (mes_wm_outsource_receipt_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| lineId | Long | line_id | 入库单行编号 关联 MesWmOutsourceReceiptLineDO |
| receiptId | Long | receipt_id | 入库单编号 关联 MesWmOutsourceReceiptDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 上架数量 |
| batchId | Long | batch_id | 批次编号 DONE @芋艿：保留。待 mes_wm_batch 模块迁移后补充 @link 关联（AI 未修复原因：标注为后续处理，需人工介入） |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 外协入库明细

**继承**: BaseDO　**主键序列**: mes_wm_outsource_receipt_detail_seq　**关联实体**: MesWmOutsourceReceiptLineDO、MesWmOutsourceReceiptDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmOutsourceReceiptLineDO (mes_wm_outsource_receipt_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| receiptId | Long | receipt_id | 入库单编号 关联 MesWmOutsourceReceiptDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 入库数量 |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| productionDate | LocalDateTime | production_date | 生产日期 |
| expireDate | LocalDateTime | expire_date | 有效期 |
| lotNumber | String | lot_number | 生产批号 |
| remark | String | remark | 备注 |
| iqcId | Long | iqc_id | 来料检验单编号 关联 MesQcIqcDO |
| iqcCheckFlag | Boolean | iqc_check_flag | 是否需要质检 |
| qualityStatus | Integer | quality_status | 质量状态 字典 MES_WM_QUALITY_STATUS 枚举 MesWmQualityStatusEnum |

**说明**: MES 外协入库单行

**继承**: BaseDO　**主键序列**: mes_wm_outsource_receipt_line_seq　**关联实体**: MesWmOutsourceReceiptDO、MesMdItemDO、MesWmBatchDO、MesQcIqcDO

#### MesWmPackageDO (mes_wm_package)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | — |
| code | String | code | 装箱单编号 |
| parentId | Long | parent_id | 父箱 ID |
| packageDate | LocalDateTime | package_date | 装箱日期 |
| salesOrderCode | String | sales_order_code | 销售订单编号 |
| invoiceCode | String | invoice_code | 发票编号 |
| clientId | Long | client_id | 客户 ID 关联 MesMdClientDO |
| length | BigDecimal | length | 箱长度 |
| width | BigDecimal | width | 箱宽度 |
| height | BigDecimal | height | 箱高度 |
| sizeUnitId | Long | size_unit_id | 尺寸单位 ID 关联 MesMdUnitMeasureDO |
| netWeight | BigDecimal | net_weight | 净重 |
| grossWeight | BigDecimal | gross_weight | 毛重 |
| weightUnitId | Long | weight_unit_id | 重量单位 ID 关联 MesMdUnitMeasureDO |
| inspectorUserId | Long | inspector_user_id | 检查员用户 ID 关联 AdminUserDO 的 id |
| status | Integer | status | 状态 字典 MES_WM_PACKAGE_STATUS 枚举 MesWmPackageStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 装箱单

**继承**: BaseDO　**主键序列**: mes_wm_package_seq　**关联实体**: MesMdClientDO、MesMdUnitMeasureDO、AdminUserDO

#### MesWmPackageLineDO (mes_wm_package_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | — |
| packageId | Long | package_id | 装箱单 ID 关联 MesWmPackageDO |
| materialStockId | Long | material_stock_id | 库存记录 ID |
| itemId | Long | item_id | 产品物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 装箱数量 |
| workOrderId | Long | work_order_id | 生产工单 ID 关联 MesProWorkOrderDO |
| expireDate | LocalDateTime | expire_date | 有效期 |
| remark | String | remark | 备注 |

**说明**: MES 装箱明细

**继承**: BaseDO　**主键序列**: mes_wm_package_line_seq　**关联实体**: MesWmPackageDO、MesMdItemDO、MesProWorkOrderDO

#### MesWmProductIssueDO (mes_wm_product_issue)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 领料单编号 |
| name | String | name | 领料单名称 |
| workstationId | Long | workstation_id | 工作站 ID 关联 MesMdWorkstationDO |
| workOrderId | Long | work_order_id | 生产工单 ID 关联 MesProWorkOrderDO |
| taskId | Long | task_id | 生产任务 ID 关联 MesProTaskDO |
| issueDate | LocalDateTime | issue_date | 领料日期 |
| requiredTime | LocalDateTime | required_time | 需求时间 |
| status | Integer | status | 状态 字典 MES_WM_PRODUCT_ISSUE_STATUS 枚举 MesWmProductIssueStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 领料出库单

**继承**: BaseDO　**主键序列**: mes_wm_product_issue_seq　**关联实体**: MesMdWorkstationDO、MesProWorkOrderDO、MesProTaskDO

#### MesWmProductIssueDetailDO (mes_wm_product_issue_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| issueId | Long | issue_id | 领料单ID 关联 MesWmProductIssueDO |
| lineId | Long | line_id | 行ID 关联 MesWmProductIssueLineDO |
| materialStockId | Long | material_stock_id | 库存记录ID 关联 MesWmMaterialStockDO |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 领料数量 |
| batchId | Long | batch_id | 批次ID |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 领料出库明细

**继承**: BaseDO　**主键序列**: mes_wm_product_issue_detail_seq　**关联实体**: MesWmProductIssueDO、MesWmProductIssueLineDO、MesWmMaterialStockDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmProductIssueLineDO (mes_wm_product_issue_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| issueId | Long | issue_id | 领料单 ID 关联 MesWmProductIssueDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 领料数量 |
| batchId | Long | batch_id | 批次 ID |
| remark | String | remark | 备注 |

**说明**: MES 领料出库单行

**继承**: BaseDO　**主键序列**: mes_wm_product_issue_line_seq　**关联实体**: MesWmProductIssueDO、MesMdItemDO

#### MesWmProductProduceDO (mes_wm_product_produce)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| workOrderId | Long | work_order_id | 生产工单 ID 关联 MesProWorkOrderDO |
| feedbackId | Long | feedback_id | 报工记录 ID 关联 MesProFeedbackDO |
| taskId | Long | task_id | 生产任务 ID 关联 MesProTaskDO |
| workstationId | Long | workstation_id | 工作站 ID 关联 MesMdWorkstationDO |
| processId | Long | process_id | 工序 ID 关联 MesProProcessDO |
| produceDate | LocalDateTime | produce_date | 生产日期 |
| status | Integer | status | 状态 字典 MES_WM_PRODUCT_PRODUCE_STATUS 枚举 MesWmProductProduceStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产入库单

**继承**: BaseDO　**主键序列**: mes_wm_product_produce_seq　**关联实体**: MesProWorkOrderDO、MesProFeedbackDO、MesProTaskDO、MesMdWorkstationDO、MesProProcessDO

#### MesWmProductProduceDetailDO (mes_wm_product_produce_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| produceId | Long | produce_id | 入库单 ID 关联 MesWmProductProduceDO |
| lineId | Long | line_id | 行 ID 关联 MesWmProductProduceLineDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 入库数量 |
| batchId | Long | batch_id | 批次 ID |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库 ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区 ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位 ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 生产入库明细

**继承**: BaseDO　**主键序列**: mes_wm_product_produce_detail_seq　**关联实体**: MesWmProductProduceDO、MesWmProductProduceLineDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmProductProduceLineDO (mes_wm_product_produce_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| produceId | Long | produce_id | 入库单 ID 关联 MesWmProductProduceDO |
| feedbackId | Long | feedback_id | 报工记录 ID 关联 MesProFeedbackDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 入库数量 |
| batchId | Long | batch_id | 批次 ID |
| batchCode | String | batch_code | 批次号 |
| expireDate | LocalDateTime | expire_date | 过期日期 |
| lotNumber | String | lot_number | 生产批号 |
| qualityStatus | Integer | quality_status | 质量状态 字典 MES_WM_QUALITY_STATUS 枚举 MesWmQualityStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产入库单行

**继承**: BaseDO　**主键序列**: mes_wm_product_produce_line_seq　**关联实体**: MesWmProductProduceDO、MesProFeedbackDO、MesMdItemDO

#### MesWmProductReceiptDO (mes_wm_product_receipt)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 收货单编码 |
| name | String | name | 收货单名称 |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |
| itemId | Long | item_id | 产品物料编号 关联 MesMdItemDO |
| receiptDate | LocalDateTime | receipt_date | 收货日期 |
| status | Integer | status | 状态 字典 MES_WM_PRODUCT_RECEIPT_STATUS 枚举 MesWmProductReceiptStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 产品收货（入库）单

**继承**: BaseDO　**主键序列**: mes_wm_product_receipt_seq　**关联实体**: MesProWorkOrderDO、MesMdItemDO

#### MesWmProductReceiptDetailDO (mes_wm_product_receipt_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| lineId | Long | line_id | 收货单行编号 关联 MesWmProductReceiptLineDO |
| receiptId | Long | receipt_id | 收货单编号 关联 MesWmProductReceiptDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 上架数量 |
| batchId | Long | batch_id | 批次编号 保留。待 mes_wm_batch 模块迁移后补充 @link 关联 |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 产品收货（入库）单明细

**继承**: BaseDO　**主键序列**: mes_wm_product_receipt_detail_seq　**关联实体**: MesWmProductReceiptLineDO、MesWmProductReceiptDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmProductReceiptLineDO (mes_wm_product_receipt_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| receiptId | Long | receipt_id | 收货单编号 关联 MesWmProductReceiptDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| materialStockId | Long | material_stock_id | 库存物资记录编号 关联 MesWmMaterialStockDO |
| quantity | BigDecimal | quantity | 收货数量 |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| remark | String | remark | 备注 |

**说明**: MES 产品收货（入库）单行

**继承**: BaseDO　**主键序列**: mes_wm_product_receipt_line_seq　**关联实体**: MesWmProductReceiptDO、MesMdItemDO、MesWmMaterialStockDO、MesWmBatchDO

#### MesWmProductSalesDO (mes_wm_product_sales)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 出库单号 |
| name | String | name | 出库单名称 |
| clientId | Long | client_id | 客户ID 关联 MesMdClientDO |
| salesOrderCode | String | sales_order_code | 销售订单号 |
| noticeId | Long | notice_id | 发货通知单 ID 关联 MesWmSalesNoticeDO |
| salesDate | LocalDateTime | sales_date | 出库日期 |
| contactName | String | contact_name | 联系人 |
| contactTelephone | String | contact_telephone | 联系电话 |
| contactAddress | String | contact_address | 收货地址 |
| carrier | String | carrier | 承运商 |
| shippingNumber | String | shipping_number | 运输单号 |
| status | Integer | status | 状态 字典 MES_WM_PRODUCT_SALES_STATUS 枚举 MesWmProductSalesStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 销售出库单

**继承**: BaseDO　**主键序列**: mes_wm_product_sales_seq　**关联实体**: MesMdClientDO、MesWmSalesNoticeDO

#### MesWmProductSalesDetailDO (mes_wm_product_sales_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| lineId | Long | line_id | 出库单行ID 关联 MesWmProductSalesLineDO |
| salesId | Long | sales_id | 出库单ID 关联 MesWmProductSalesDO |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 拣货数量 |
| materialStockId | Long | material_stock_id | 库存记录ID 关联 MesWmMaterialStockDO |
| batchId | Long | batch_id | 批次 ID 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| warehouseId | Long | warehouse_id | 仓库ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 销售出库明细

**继承**: BaseDO　**主键序列**: mes_wm_product_sales_detail_seq　**关联实体**: MesWmProductSalesLineDO、MesWmProductSalesDO、MesMdItemDO、MesWmMaterialStockDO、MesWmBatchDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmProductSalesLineDO (mes_wm_product_sales_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| salesId | Long | sales_id | 出库单ID 关联 MesWmProductSalesDO |
| noticeLineId | Long | notice_line_id | 发货通知单行ID 关联 MesWmSalesNoticeLineDO |
| itemId | Long | item_id | 物料ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 出库数量 |
| batchId | Long | batch_id | 批次 ID 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| materialStockId | Long | material_stock_id | 库存记录ID 关联 MesWmMaterialStockDO |
| oqcCheckFlag | Boolean | oqc_check_flag | 是否出厂检验 |
| oqcId | Long | oqc_id | 出厂检验单 ID 关联 MesQcOqcDO |
| qualityStatus | Integer | quality_status | 质量状态 字典 MES_WM_QUALITY_STATUS 枚举 MesWmQualityStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 销售出库单行

**继承**: BaseDO　**主键序列**: mes_wm_product_sales_line_seq　**关联实体**: MesWmProductSalesDO、MesWmSalesNoticeLineDO、MesMdItemDO、MesWmBatchDO、MesWmMaterialStockDO、MesQcOqcDO

#### MesWmReturnIssueDO (mes_wm_return_issue)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 退料单编号 |
| name | String | name | 退料单名称 |
| workOrderId | Long | work_order_id | 生产工单 ID 关联 MesProWorkOrderDO |
| workstationId | Long | workstation_id | 工作站 ID 关联 MesMdWorkstationDO |
| type | Integer | type | 退料类型 字典 MES_WM_RETURN_ISSUE_TYPE 枚举 MesWmReturnIssueTypeEnum |
| returnDate | LocalDateTime | return_date | 退料日期 |
| status | Integer | status | 状态 字典 MES_WM_RETURN_ISSUE_STATUS 枚举 MesWmReturnIssueStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产退料单

**继承**: BaseDO　**主键序列**: mes_wm_return_issue_seq　**关联实体**: MesProWorkOrderDO、MesMdWorkstationDO

#### MesWmReturnIssueDetailDO (mes_wm_return_issue_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| issueId | Long | issue_id | 退料单 ID 关联 MesWmReturnIssueDO |
| lineId | Long | line_id | 行 ID 关联 MesWmReturnIssueLineDO |
| materialStockId | Long | material_stock_id | 库存记录 ID 关联 MesWmMaterialStockDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 退料数量 |
| batchId | Long | batch_id | 批次 ID |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库 ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区 ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位 ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 生产退料明细

**继承**: BaseDO　**主键序列**: mes_wm_return_issue_detail_seq　**关联实体**: MesWmReturnIssueDO、MesWmReturnIssueLineDO、MesWmMaterialStockDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmReturnIssueLineDO (mes_wm_return_issue_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| issueId | Long | issue_id | 退料单 ID 关联 MesWmReturnIssueDO |
| materialStockId | Long | material_stock_id | 库存记录 ID 关联 MesWmMaterialStockDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 退料数量 |
| batchId | Long | batch_id | 批次 ID 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次编码 关联 MesWmBatchDO |
| rqcId | Long | rqc_id | 退货检验单 ID 关联 MesQcRqcDO |
| rqcCheckFlag | Boolean | rqc_check_flag | 是否需要质检 |
| qualityStatus | Integer | quality_status | 质量状态 字典 MES_WM_QUALITY_STATUS 枚举 MesWmQualityStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 生产退料单行

**继承**: BaseDO　**主键序列**: mes_wm_return_issue_line_seq　**关联实体**: MesWmReturnIssueDO、MesWmMaterialStockDO、MesMdItemDO、MesWmBatchDO、MesQcRqcDO

#### MesWmReturnSalesDO (mes_wm_return_sales)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 退货单编号 |
| name | String | name | 退货单名称 |
| salesOrderCode | String | sales_order_code | 销售订单编号 |
| clientId | Long | client_id | 客户 ID 关联 MesMdClientDO |
| returnDate | LocalDateTime | return_date | 退货日期 |
| returnReason | String | return_reason | 退货原因 |
| status | Integer | status | 状态 字典 MES_WM_RETURN_SALES_STATUS 枚举 MesWmReturnSalesStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 销售退货单

**继承**: BaseDO　**主键序列**: mes_wm_return_sales_seq　**关联实体**: MesMdClientDO

#### MesWmReturnSalesDetailDO (mes_wm_return_sales_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| returnId | Long | return_id | 退货单 ID 关联 MesWmReturnSalesDO |
| lineId | Long | line_id | 行 ID 关联 MesWmReturnSalesLineDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 数量 |
| batchId | Long | batch_id | 批次 ID |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库 ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区 ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位 ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 销售退货明细

**继承**: BaseDO　**主键序列**: mes_wm_return_sales_detail_seq　**关联实体**: MesWmReturnSalesDO、MesWmReturnSalesLineDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmReturnSalesLineDO (mes_wm_return_sales_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| returnId | Long | return_id | 退货单 ID 关联 MesWmReturnSalesDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 退货数量 |
| batchId | Long | batch_id | 批次 ID |
| batchCode | String | batch_code | 批次号 |
| rqcId | Long | rqc_id | 退货检验单 ID |
| rqcCheckFlag | Boolean | rqc_check_flag | 是否需要质检 |
| qualityStatus | Integer | quality_status | 质量状态 字典 MES_WM_QUALITY_STATUS 枚举 MesWmQualityStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 销售退货单行

**继承**: BaseDO　**主键序列**: mes_wm_return_sales_line_seq　**关联实体**: MesWmReturnSalesDO、MesMdItemDO

#### MesWmReturnVendorDO (mes_wm_return_vendor)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 退货单编号 |
| name | String | name | 退货单名称 |
| purchaseOrderCode | String | purchase_order_code | 采购订单编号 |
| vendorId | Long | vendor_id | 供应商 ID 关联 MesMdVendorDO |
| returnDate | LocalDateTime | return_date | 退货日期 |
| returnReason | String | return_reason | 退货原因 |
| transportCode | String | transport_code | 物流单号 |
| transportTelephone | String | transport_telephone | 物流联系电话 |
| status | Integer | status | 状态 字典 MES_WM_RETURN_VENDOR_STATUS 枚举 MesWmReturnVendorStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 供应商退货单

**继承**: BaseDO　**主键序列**: mes_wm_return_vendor_seq　**关联实体**: MesMdVendorDO

#### MesWmReturnVendorDetailDO (mes_wm_return_vendor_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| returnId | Long | return_id | 退货单 ID 关联 MesWmReturnVendorDO |
| lineId | Long | line_id | 行 ID 关联 MesWmReturnVendorLineDO |
| materialStockId | Long | material_stock_id | 库存记录 ID 关联 MesWmMaterialStockDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 退货数量 |
| batchId | Long | batch_id | 批次 ID |
| batchCode | String | batch_code | 批次号 |
| warehouseId | Long | warehouse_id | 仓库 ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区 ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位 ID 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 供应商退货明细

**继承**: BaseDO　**主键序列**: mes_wm_return_vendor_detail_seq　**关联实体**: MesWmReturnVendorDO、MesWmReturnVendorLineDO、MesWmMaterialStockDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmReturnVendorLineDO (mes_wm_return_vendor_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| returnId | Long | return_id | 退货单 ID 关联 MesWmReturnVendorDO |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 退货数量 |
| batchId | Long | batch_id | 批次 ID 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| remark | String | remark | 备注 |

**说明**: MES 供应商退货单行

**继承**: BaseDO　**主键序列**: mes_wm_return_vendor_line_seq　**关联实体**: MesWmReturnVendorDO、MesMdItemDO、MesWmBatchDO

#### MesWmSalesNoticeDO (mes_wm_sales_notice)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 通知单编码 |
| name | String | name | 通知单名称 |
| salesOrderCode | String | sales_order_code | 销售订单编号 |
| clientId | Long | client_id | 客户编号 关联 MesMdClientDO |
| salesDate | LocalDateTime | sales_date | 发货日期 |
| recipientName | String | recipient_name | 收货人 |
| recipientTelephone | String | recipient_telephone | 联系方式 |
| recipientAddress | String | recipient_address | 收货地址 |
| status | Integer | status | 状态 字典 MES_WM_SALES_NOTICE_STATUS 枚举 MesWmSalesNoticeStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 发货通知单

**继承**: BaseDO　**主键序列**: mes_wm_sales_notice_seq　**关联实体**: MesMdClientDO

#### MesWmSalesNoticeLineDO (mes_wm_sales_notice_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| noticeId | Long | notice_id | 发货通知单编号 关联 MesWmSalesNoticeDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| batchId | Long | batch_id | 批次编号 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| quantity | BigDecimal | quantity | 发货数量 |
| oqcCheckFlag | Boolean | oqc_check_flag | 是否检验 |
| remark | String | remark | 备注 |

**说明**: MES 发货通知单行

**继承**: BaseDO　**主键序列**: mes_wm_sales_notice_line_seq　**关联实体**: MesWmSalesNoticeDO、MesMdItemDO、MesWmBatchDO

#### MesWmSnDO (mes_wm_sn)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| uuid | String | uuid | 批次 UUID（用于标记同一批次生成的 SN 码） |
| code | String | code | SN 码（唯一） |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| batchCode | String | batch_code | 批次号 |
| workOrderId | Long | work_order_id | 生产工单编号 关联 MesProWorkOrderDO |

**说明**: MES SN 码

**继承**: BaseDO　**主键序列**: mes_wm_sn_seq　**关联实体**: MesMdItemDO、MesProWorkOrderDO

#### MesWmStockTakingPlanDO (mes_wm_stock_taking_plan)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 方案编码 |
| name | String | name | 方案名称 |
| type | Integer | type | 盘点类型 字典 MES_WM_STOCK_TAKING_TYPE 枚举 MesWmStockTakingTypeEnum |
| startTime | LocalDateTime | start_time | 计划开始时间 |
| endTime | LocalDateTime | end_time | 计划结束时间 |
| blindFlag | Boolean | blind_flag | 是否盲盘 |
| frozen | Boolean | frozen | 是否冻结库存 |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 盘点方案

**继承**: BaseDO　**主键序列**: mes_wm_stock_taking_plan_seq

#### MesWmStockTakingPlanParamDO (mes_wm_stock_taking_plan_param)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| planId | Long | plan_id | 盘点方案编号 关联 MesWmStockTakingPlanDO |
| type | Integer | type | 参数值类型 字典 MES_WM_STOCK_TAKING_PLAN_PARAM_TYPE 枚举 MesWmStockTakingPlanParamTypeEnum |
| valueId | Long | value_id | 参数值编号，例如仓库、库区、库位、物料、批次的主键 ID |
| valueCode | String | value_code | 参数值编码，例如仓库编码、库区编码、库位编码、物料编码、批次编码 |
| valueName | String | value_name | 参数值名称，例如仓库名称、库区名称、库位名称、物料名称、批次名称 |
| remark | String | remark | 备注 |

**说明**: MES 盘点方案参数

**继承**: BaseDO　**主键序列**: mes_wm_stock_taking_plan_param_seq　**关联实体**: MesWmStockTakingPlanDO

#### MesWmStockTakingTaskDO (mes_wm_stock_taking_task)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 任务编码 |
| name | String | name | 任务名称 |
| takingDate | LocalDateTime | taking_date | 盘点日期 |
| type | Integer | type | 盘点类型 字典 MES_WM_STOCK_TAKING_TYPE 枚举 MesWmStockTakingTypeEnum |
| userId | Long | user_id | 盘点人编号 关联 AdminUserDO 的 id 字段 |
| planId | Long | plan_id | 盘点计划编号 关联 MesWmStockTakingPlanDO |
| blindFlag | Boolean | blind_flag | 是否盲盘 |
| frozen | Boolean | frozen | 是否冻结库存 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间 |
| status | Integer | status | 任务状态 字典 MES_WM_STOCK_TAKING_TASK_STATUS 枚举 MesWmStockTakingTaskStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 盘点任务

**继承**: BaseDO　**主键序列**: mes_wm_stock_taking_task_seq　**关联实体**: AdminUserDO、MesWmStockTakingPlanDO

#### MesWmStockTakingTaskLineDO (mes_wm_stock_taking_task_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| taskId | Long | task_id | 盘点任务编号 关联 MesWmStockTakingTaskDO |
| materialStockId | Long | material_stock_id | 库存编号 |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| batchId | Long | batch_id | 批次编号 |
| batchCode | String | batch_code | 批次编码 |
| quantity | BigDecimal | quantity | 在库数量 |
| takingQuantity | BigDecimal | taking_quantity | 盘点数量 |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库位编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库区编号 关联 MesWmWarehouseAreaDO ()} |
| status | Integer | status | 盘点状态 字典 MES_WM_STOCK_TAKING_TASK_LINE_STATUS 枚举 MesWmStockTakingTaskLineStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 盘点任务行

**继承**: BaseDO　**主键序列**: mes_wm_stock_taking_task_line_seq　**关联实体**: MesWmStockTakingTaskDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmStockTakingTaskResultDO (mes_wm_stock_taking_task_result)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| taskId | Long | task_id | 盘点任务编号 关联 MesWmStockTakingTaskDO |
| lineId | Long | line_id | 盘点任务行编号 关联 MesWmStockTakingTaskLineDO |
| materialStockId | Long | material_stock_id | 库存编号 |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| batchId | Long | batch_id | 批次编号 |
| batchCode | String | batch_code | 批次编码 |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库位编号 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库区编号 关联 MesWmWarehouseAreaDO |
| quantity | BigDecimal | quantity | 在库数量 |
| takingQuantity | BigDecimal | taking_quantity | 盘点数量 |
| remark | String | remark | 备注 |

**说明**: MES 盘点结果

**继承**: BaseDO　**主键序列**: mes_wm_stock_taking_task_result_seq　**关联实体**: MesWmStockTakingTaskDO、MesWmStockTakingTaskLineDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmTransactionDO (mes_wm_transaction)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| type | Integer | type | 事务类型 字典 MES_WM_TRANSACTION_TYPE 枚举 MesWmTransactionTypeEnum |
| bizType | Integer | biz_type | 业务类型 对应 MesBizTypeConstants 中的常量 |
| bizId | Long | biz_id | 来源业务主单 ID |
| bizCode | String | biz_code | 来源业务单号 |
| bizLineId | Long | biz_line_id | 来源业务行 ID |
| materialStockId | Long | material_stock_id | 库存记录 ID 关联 MesWmMaterialStockDO |
| relatedTransactionId | Long | related_transaction_id | 关联的事务 ID 关联 {@link #getId()}，用于调拨等成对流水关联 |
| itemId | Long | item_id | 物料 ID 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 本次变动数量 正数=入库，负数=出库 |
| batchId | Long | batch_id | 批次 ID 关联 MesWmBatchDO |
| batchCode | String | batch_code | 批次号 关联 MesWmBatchDO |
| warehouseId | Long | warehouse_id | 仓库 ID 关联 MesWmWarehouseDO |
| locationId | Long | location_id | 库区 ID 关联 MesWmWarehouseLocationDO |
| areaId | Long | area_id | 库位 ID 关联 MesWmWarehouseAreaDO |
| transactionTime | LocalDateTime | transaction_time | 事务发生时间 |
| erpTime | LocalDateTime | erp_time | ERP 账期 |
| receiptTime | LocalDateTime | receipt_time | 入库时间 |

**说明**: MES 库存事务流水 记录每一笔库存增减事件，系统自动生成，只读查询，不允许人工维护。

**继承**: BaseDO　**主键序列**: mes_wm_transaction_seq　**关联实体**: MesWmMaterialStockDO、MesMdItemDO、MesWmBatchDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmTransferDO (mes_wm_transfer)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 转移单编号 |
| name | String | name | 转移单名称 |
| type | Integer | type | 转移单类型 字典 MES_WM_TRANSFER_TYPE 枚举 MesWmTransferTypeEnum |
| deliveryFlag | Boolean | delivery_flag | 是否配送 |
| recipientName | String | recipient_name | 收货人 |
| recipientTelephone | String | recipient_telephone | 联系方式 |
| destinationAddress | String | destination_address | 目的地 |
| carrier | String | carrier | 承运商 |
| shippingNumber | String | shipping_number | 运输单号 |
| confirmFlag | Boolean | confirm_flag | 是否已确认 |
| transferDate | LocalDateTime | transfer_date | 转移日期 |
| status | Integer | status | 状态 字典 MES_WM_TRANSFER_STATUS 枚举 MesWmTransferStatusEnum |
| remark | String | remark | 备注 |

**说明**: MES 转移单

**继承**: BaseDO　**主键序列**: mes_wm_transfer_seq

#### MesWmTransferDetailDO (mes_wm_transfer_detail)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| lineId | Long | line_id | 转移单行编号 关联 MesWmTransferLineDO |
| transferId | Long | transfer_id | 转移单编号 关联 MesWmTransferDO |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 上架数量 |
| batchId | Long | batch_id | 批次编号 |
| toWarehouseId | Long | to_warehouse_id | 移入仓库编号 关联 MesWmWarehouseDO |
| toLocationId | Long | to_location_id | 移入库区编号 关联 MesWmWarehouseLocationDO |
| toAreaId | Long | to_area_id | 移入库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 调拨明细

**继承**: BaseDO　**主键序列**: mes_wm_transfer_detail_seq　**关联实体**: MesWmTransferLineDO、MesWmTransferDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmTransferLineDO (mes_wm_transfer_line)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| transferId | Long | transfer_id | 转移单编号 关联 MesWmTransferDO |
| materialStockId | Long | material_stock_id | 库存记录编号 |
| itemId | Long | item_id | 物料编号 关联 MesMdItemDO |
| quantity | BigDecimal | quantity | 转移数量 |
| batchId | Long | batch_id | 批次编号 |
| fromWarehouseId | Long | from_warehouse_id | 移出仓库编号 关联 MesWmWarehouseDO |
| fromLocationId | Long | from_location_id | 移出库区编号 关联 MesWmWarehouseLocationDO |
| fromAreaId | Long | from_area_id | 移出库位编号 关联 MesWmWarehouseAreaDO |
| remark | String | remark | 备注 |

**说明**: MES 转移单行

**继承**: BaseDO　**主键序列**: mes_wm_transfer_line_seq　**关联实体**: MesWmTransferDO、MesMdItemDO、MesWmWarehouseDO、MesWmWarehouseLocationDO、MesWmWarehouseAreaDO

#### MesWmWarehouseAreaDO (mes_wm_warehouse_area)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 库位编码 |
| name | String | name | 库位名称 |
| locationId | Long | location_id | 库区编号 关联 MesWmWarehouseLocationDO |
| area | BigDecimal | area | 面积 |
| maxLoad | BigDecimal | max_load | 最大载重 |
| positionX | Integer | position_x | 位置 X |
| positionY | Integer | position_y | 位置 Y |
| positionZ | Integer | position_z | 位置 Z |
| status | Integer | status | 状态 枚举 CommonStatusEnum |
| frozen | Boolean | frozen | 是否冻结 |
| allowItemMixing | Boolean | allow_item_mixing | 是否允许物料混放 |
| allowBatchMixing | Boolean | allow_batch_mixing | 是否允许批次混放 |
| remark | String | remark | 备注 |

**说明**: MES 库位

**继承**: BaseDO　**主键序列**: mes_wm_warehouse_area_seq　**关联实体**: MesWmWarehouseLocationDO

#### MesWmWarehouseDO (mes_wm_warehouse)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 仓库编码 |
| name | String | name | 仓库名称 |
| address | String | address | 仓库地址 |
| area | BigDecimal | area | 面积 |
| chargeUserId | Long | charge_user_id | 负责人用户编号 关联 system_users 表的 id 字段 |
| frozen | Boolean | frozen | 是否冻结 |
| remark | String | remark | 备注 |

**说明**: MES 仓库

**继承**: BaseDO　**主键序列**: mes_wm_warehouse_seq

#### MesWmWarehouseLocationDO (mes_wm_warehouse_location)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号 |
| code | String | code | 库区编码 |
| name | String | name | 库区名称 |
| warehouseId | Long | warehouse_id | 仓库编号 关联 MesWmWarehouseDO |
| area | BigDecimal | area | 面积 |
| frozen | Boolean | frozen | 是否冻结 |
| remark | String | remark | 备注 |

**说明**: MES 库区

**继承**: BaseDO　**主键序列**: mes_wm_warehouse_location_seq　**关联实体**: MesWmWarehouseDO

## 3. 实体关系

MES 的关联以「主表-行-明细」三段式与「聚合根-子实体」外键方式组织，不建物理外键约束，由应用层保证一致性。

| 聚合 | 聚合根 | 包含实体 | 说明 |
|------|--------|----------|------|
| 主数据 | `MesMdItemDO` | `MesMdItemTypeDO`、`MesMdItemBatchConfigDO`、`MesMdProductBomDO`、`MesMdProductSipDO`、`MesMdProductSopDO` | 物料分类树 + 物料自身的批次属性/BOM/SIP/SOP 扩展 |
| 主数据 | `MesMdWorkstationDO` | `MesMdWorkshopDO`、`MesMdWorkstationMachineDO`、`MesMdWorkstationToolDO`、`MesMdWorkstationWorkerDO` | 车间 → 工作站 → 设备/工装/人员资源三级结构 |
| 主数据 | `MesMdAutoCodeRuleDO` | `MesMdAutoCodePartDO`、`MesMdAutoCodeRecordDO` | 编码规则由分段定义，按规则生成记录流水 |
| 生产 | `MesProWorkOrderDO` | `MesProWorkOrderBomDO`、`MesProTaskDO`、`MesProTaskIssueDO`、`MesProFeedbackDO`、`MesProCardDO`、`MesProCardProcessDO` | 工单 → BOM/任务/投料/报工/流转卡级联 |
| 生产 | `MesProRouteDO` | `MesProRouteProcessDO`、`MesProRouteProductDO`、`MesProRouteProductBomDO` | 工艺路线 → 工序 → 适用产品 → 产品 BOM |
| 生产 | `MesProProcessDO` | `MesProProcessContentDO` | 工序与工序内容（SIP/SOP 引用） |
| 生产 | `MesProAndonConfigDO` | `MesProAndonRecordDO` | 安灯呼叫配置与呼叫记录 |
| 生产 | `MesProWorkRecordDO` | `MesProWorkRecordLogDO` | 用户-工作站绑定快照与上下工流水 |
| 质量 | `MesQcTemplateDO` | `MesQcTemplateIndicatorDO`、`MesQcTemplateItemDO`、`MesQcIndicatorDO` | 质检方案 → 检测指标项 + 适用产品 |
| 质量 | `MesQcIqcDO` / `MesQcIpqcDO` / `MesQcOqcDO` / `MesQcRqcDO` | 各 `*LineDO`、`MesQcIndicatorResultDO`、`MesQcIndicatorResultDetailDO`、`MesQcDefectRecordDO` | 四类检验单主子表 + 检验结果 + 缺陷记录 |
| 设备 | `MesDvMachineryDO` | `MesDvMachineryTypeDO`、`MesDvCheckPlanDO`、`MesDvCheckRecordDO`、`MesDvMaintenRecordDO`、`MesDvRepairDO` | 设备台账 → 点检保养方案/记录、维修工单 |
| 仓库 | `MesWmWarehouseDO` | `MesWmWarehouseLocationDO`、`MesWmWarehouseAreaDO` | 仓库 → 库区 → 库位三级结构 |
| 仓库 | `MesWmMaterialStockDO` | `MesWmBatchDO`、`MesWmSnDO`、`MesWmBarcodeDO`、`MesWmTransactionDO` | 库存台账按物料/仓库/库位/批次维度，所有数量变动写事务流水 |
| 仓库 | 8 类出/入库单 | 各单 `*DO` + `*LineDO` + `*DetailDO` | 采购入库、领料出库、生产退料、生产入库、产品收货、销售出库、销售退货、外协发料/入库、供应商退货、杂项收/发、转移、盘点、装箱均为主表-行-明细三段式 |
| 排班 | `MesCalPlanDO` | `MesCalPlanShiftDO`、`MesCalPlanTeamDO`、`MesCalTeamDO`、`MesCalTeamMemberDO`、`MesCalTeamShiftDO` | 排班计划 → 计划班次/计划班组 → 班组 → 班组成员/班组排班 |
| 工装 | `MesTmToolDO` | `MesTmToolTypeDO` | 工具类型与工具台账 |

### 3.1 跨域外键映射

| 引用方字段 | 被引用实体 | 说明 |
|------|------|------|
| `MesProTaskDO.workOrderId` | `MesProWorkOrderDO` | 生产任务挂在工单下 |
| `MesProTaskDO.workstationId` | `MesMdWorkstationDO` | 任务派工到工作站 |
| `MesProTaskDO.routeId` / `processId` | `MesProRouteDO` / `MesProProcessDO` | 任务对应工艺路线与工序 |
| `MesProTaskDO.itemId` | `MesMdItemDO` | 任务生产的产品物料 |
| `MesWmMaterialStockDO.itemId` / `itemTypeId` | `MesMdItemDO` / `MesMdItemTypeDO` | 库存台账的物料维度 |
| `MesWmMaterialStockDO.batchId` / `batchCode` | `MesWmBatchDO` | 库存台账的批次维度（ID + 号冗余） |
| `MesWmMaterialStockDO.warehouseId` / `locationId` / `areaId` | `MesWmWarehouseDO` / `MesWmWarehouseLocationDO` / `MesWmWarehouseAreaDO` | 库存台账的三级库位维度 |
| `MesWmTransactionDO.bizId` | 多态 | 事务流水通过 `type`/`bizType` 指向 8 类出入库单据，`bizId` 为单据主键 |
| `MesQcIndicatorResultDO.qcId` | 四类检验单 | 检验结果通过 `qcType` 多态关联 IQC/IPQC/OQC/RQC 单据 |
| `MesQcDefectRecordDO.qcId` / `lineId` | 四类检验单 / 检验行 | 缺陷记录通过 `qcType` 多态关联 |
| `MesProFeedbackDO.workOrderId` / `taskId` | `MesProWorkOrderDO` / `MesProTaskDO` | 报工记录回溯工单与任务 |
| `MesProCardDO.workOrderId` | `MesProWorkOrderDO` | 流转卡跟随工单 |

## 4. 全部数据表清单

共 **133** 张表（133 个 DO，一一对应）。

| 表名 | DO | 说明 |
|-----|-----|------|
| mes_md_auto_code_part | MesMdAutoCodePartDO | MES 编码规则组成 |
| mes_md_auto_code_record | MesMdAutoCodeRecordDO | MES 编码生成记录 |
| mes_md_auto_code_rule | MesMdAutoCodeRuleDO | MES 编码规则 |
| mes_md_client | MesMdClientDO | MES 客户 |
| mes_md_item | MesMdItemDO | MES 物料产品 |
| mes_md_item_batch_config | MesMdItemBatchConfigDO | MES 物料批次属性配置 |
| mes_md_item_type | MesMdItemTypeDO | MES 物料产品分类 |
| mes_md_product_bom | MesMdProductBomDO | MES 产品 BOM |
| mes_md_product_sip | MesMdProductSipDO | MES 产品SIP |
| mes_md_product_sop | MesMdProductSopDO | MES 产品SOP |
| mes_md_unit_measure | MesMdUnitMeasureDO | MES 计量单位 |
| mes_md_vendor | MesMdVendorDO | MES 供应商 |
| mes_md_workshop | MesMdWorkshopDO | MES 车间 |
| mes_md_workstation | MesMdWorkstationDO | MES 工作站 |
| mes_md_workstation_machine | MesMdWorkstationMachineDO | MES 设备资源 |
| mes_md_workstation_tool | MesMdWorkstationToolDO | MES 工装夹具资源 |
| mes_md_workstation_worker | MesMdWorkstationWorkerDO | MES 人力资源 |
| mes_cal_holiday | MesCalHolidayDO | MES 假期设置 |
| mes_cal_plan | MesCalPlanDO | MES 排班计划 |
| mes_cal_plan_shift | MesCalPlanShiftDO | MES 计划班次 |
| mes_cal_plan_team | MesCalPlanTeamDO | MES 计划班组关联 |
| mes_cal_team | MesCalTeamDO | MES 班组 |
| mes_cal_team_member | MesCalTeamMemberDO | MES 班组成员 |
| mes_cal_team_shift | MesCalTeamShiftDO | MES 班组排班 |
| mes_dv_check_plan | MesDvCheckPlanDO | MES 点检保养方案 |
| mes_dv_check_plan_machinery | MesDvCheckPlanMachineryDO | MES 点检保养方案设备 |
| mes_dv_check_plan_subject | MesDvCheckPlanSubjectDO | MES 点检保养方案项目 |
| mes_dv_check_record | MesDvCheckRecordDO | MES 设备点检记录 |
| mes_dv_check_record_line | MesDvCheckRecordLineDO | MES 设备点检记录明细 |
| mes_dv_machinery | MesDvMachineryDO | MES 设备台账 |
| mes_dv_machinery_type | MesDvMachineryTypeDO | MES 设备类型 |
| mes_dv_mainten_record | MesDvMaintenRecordDO | MES 设备保养记录 |
| mes_dv_mainten_record_line | MesDvMaintenRecordLineDO | MES 设备保养记录明细 |
| mes_dv_repair | MesDvRepairDO | MES 维修工单 |
| mes_dv_repair_line | MesDvRepairLineDO | MES 维修工单行 |
| mes_dv_subject | MesDvSubjectDO | MES 点检保养项目 |
| mes_pro_andon_config | MesProAndonConfigDO | MES 安灯呼叫配置 |
| mes_pro_andon_record | MesProAndonRecordDO | MES 安灯呼叫记录 |
| mes_pro_card | MesProCardDO | MES 生产流转卡 |
| mes_pro_card_process | MesProCardProcessDO | MES 流转卡工序记录 |
| mes_pro_feedback | MesProFeedbackDO | MES 生产报工 |
| mes_pro_process | MesProProcessDO | MES 生产工序 |
| mes_pro_process_content | MesProProcessContentDO | MES 生产工序内容 |
| mes_pro_route | MesProRouteDO | MES 工艺路线 |
| mes_pro_route_process | MesProRouteProcessDO | MES 工艺路线工序 |
| mes_pro_route_product | MesProRouteProductDO | MES 工艺路线产品 |
| mes_pro_route_product_bom | MesProRouteProductBomDO | MES 工艺路线产品 BOM |
| mes_pro_task | MesProTaskDO | MES 生产任务 |
| mes_pro_task_issue | MesProTaskIssueDO | MES 生产任务投料 |
| mes_pro_work_order | MesProWorkOrderDO | MES 生产工单 |
| mes_pro_work_order_bom | MesProWorkOrderBomDO | MES 生产工单 BOM |
| mes_pro_work_record | MesProWorkRecordDO | MES 用户工作站绑定关系（当前快照） |
| mes_pro_work_record_log | MesProWorkRecordLogDO | MES 上下工记录流水 |
| mes_qc_template | MesQcTemplateDO | MES 质检方案 |
| mes_qc_defect | MesQcDefectDO | MES 缺陷类型 |
| mes_qc_defect_record | MesQcDefectRecordDO | MES 质检缺陷记录 通用缺陷记录表，通过 {@link #qcType} 区分检验类型（IQC、IPQC、OQC、RQC），多模块复用 |
| mes_qc_indicator | MesQcIndicatorDO | MES 质检指标 |
| mes_qc_indicator_result | MesQcIndicatorResultDO | MES 检验结果记录 |
| mes_qc_indicator_result_detail | MesQcIndicatorResultDetailDO | MES 检验结果明细记录 |
| mes_qc_ipqc | MesQcIpqcDO | MES 过程检验单（IPQC, In-Process Quality Control） |
| mes_qc_ipqc_line | MesQcIpqcLineDO | MES 过程检验单行 |
| mes_qc_iqc | MesQcIqcDO | MES 来料检验单（IQC, Incoming Quality Control） |
| mes_qc_iqc_line | MesQcIqcLineDO | MES 来料检验单行 |
| mes_qc_oqc | MesQcOqcDO | MES 出货检验单（OQC, Outgoing Quality Control） |
| mes_qc_oqc_line | MesQcOqcLineDO | MES 出货检验单行 |
| mes_qc_rqc | MesQcRqcDO | MES 退货检验单（RQC, Return Quality Control） |
| mes_qc_rqc_line | MesQcRqcLineDO | MES 退货检验行 |
| mes_qc_template_indicator | MesQcTemplateIndicatorDO | MES 质检方案-检测指标项 |
| mes_qc_template_item | MesQcTemplateItemDO | MES 质检方案-产品关联 |
| mes_tm_tool | MesTmToolDO | MES 工具台账 |
| mes_tm_tool_type | MesTmToolTypeDO | MES 工具类型 |
| mes_wm_arrival_notice | MesWmArrivalNoticeDO | MES 到货通知单 |
| mes_wm_arrival_notice_line | MesWmArrivalNoticeLineDO | MES 到货通知单行 |
| mes_wm_barcode | MesWmBarcodeDO | MES 条码清单 |
| mes_wm_barcode_config | MesWmBarcodeConfigDO | MES 条码配置 |
| mes_wm_batch | MesWmBatchDO | 批次管理 |
| mes_wm_item_consume | MesWmItemConsumeDO | MES 物料消耗记录 |
| mes_wm_item_consume_detail | MesWmItemConsumeDetailDO | MES 物料消耗记录明细 记录 line 级别的消耗按线边库 FIFO 分配到具体批次的明细。 一条 line 可能拆分为多条 detail（当一个批次库存不够，需要从下一个批次继续分配时）。 |
| mes_wm_item_consume_line | MesWmItemConsumeLineDO | MES 物料消耗记录行 |
| mes_wm_item_receipt | MesWmItemReceiptDO | MES 采购入库单 |
| mes_wm_item_receipt_detail | MesWmItemReceiptDetailDO | MES 采购入库明细 |
| mes_wm_item_receipt_line | MesWmItemReceiptLineDO | MES 采购入库单行 |
| mes_wm_material_stock | MesWmMaterialStockDO | MES 库存台账（仓库现有量） |
| mes_wm_misc_issue | MesWmMiscIssueDO | MES 杂项出库单 |
| mes_wm_misc_issue_detail | MesWmMiscIssueDetailDO | MES 杂项出库明细 |
| mes_wm_misc_issue_line | MesWmMiscIssueLineDO | MES 杂项出库单行 |
| mes_wm_misc_receipt | MesWmMiscReceiptDO | MES 杂项入库单 |
| mes_wm_misc_receipt_detail | MesWmMiscReceiptDetailDO | MES 杂项入库明细 |
| mes_wm_misc_receipt_line | MesWmMiscReceiptLineDO | MES 杂项入库单行 |
| mes_wm_outsource_issue | MesWmOutsourceIssueDO | MES 外协发料单 |
| mes_wm_outsource_issue_detail | MesWmOutsourceIssueDetailDO | MES 外协发料单明细 |
| mes_wm_outsource_issue_line | MesWmOutsourceIssueLineDO | MES 外协发料单行 |
| mes_wm_outsource_receipt | MesWmOutsourceReceiptDO | MES 外协入库单 |
| mes_wm_outsource_receipt_detail | MesWmOutsourceReceiptDetailDO | MES 外协入库明细 |
| mes_wm_outsource_receipt_line | MesWmOutsourceReceiptLineDO | MES 外协入库单行 |
| mes_wm_package | MesWmPackageDO | MES 装箱单 |
| mes_wm_package_line | MesWmPackageLineDO | MES 装箱明细 |
| mes_wm_product_issue | MesWmProductIssueDO | MES 领料出库单 |
| mes_wm_product_issue_detail | MesWmProductIssueDetailDO | MES 领料出库明细 |
| mes_wm_product_issue_line | MesWmProductIssueLineDO | MES 领料出库单行 |
| mes_wm_product_produce | MesWmProductProduceDO | MES 生产入库单 |
| mes_wm_product_produce_detail | MesWmProductProduceDetailDO | MES 生产入库明细 |
| mes_wm_product_produce_line | MesWmProductProduceLineDO | MES 生产入库单行 |
| mes_wm_product_receipt | MesWmProductReceiptDO | MES 产品收货（入库）单 |
| mes_wm_product_receipt_detail | MesWmProductReceiptDetailDO | MES 产品收货（入库）单明细 |
| mes_wm_product_receipt_line | MesWmProductReceiptLineDO | MES 产品收货（入库）单行 |
| mes_wm_product_sales | MesWmProductSalesDO | MES 销售出库单 |
| mes_wm_product_sales_detail | MesWmProductSalesDetailDO | MES 销售出库明细 |
| mes_wm_product_sales_line | MesWmProductSalesLineDO | MES 销售出库单行 |
| mes_wm_return_issue | MesWmReturnIssueDO | MES 生产退料单 |
| mes_wm_return_issue_detail | MesWmReturnIssueDetailDO | MES 生产退料明细 |
| mes_wm_return_issue_line | MesWmReturnIssueLineDO | MES 生产退料单行 |
| mes_wm_return_sales | MesWmReturnSalesDO | MES 销售退货单 |
| mes_wm_return_sales_detail | MesWmReturnSalesDetailDO | MES 销售退货明细 |
| mes_wm_return_sales_line | MesWmReturnSalesLineDO | MES 销售退货单行 |
| mes_wm_return_vendor | MesWmReturnVendorDO | MES 供应商退货单 |
| mes_wm_return_vendor_detail | MesWmReturnVendorDetailDO | MES 供应商退货明细 |
| mes_wm_return_vendor_line | MesWmReturnVendorLineDO | MES 供应商退货单行 |
| mes_wm_sales_notice | MesWmSalesNoticeDO | MES 发货通知单 |
| mes_wm_sales_notice_line | MesWmSalesNoticeLineDO | MES 发货通知单行 |
| mes_wm_sn | MesWmSnDO | MES SN 码 |
| mes_wm_stock_taking_plan | MesWmStockTakingPlanDO | MES 盘点方案 |
| mes_wm_stock_taking_plan_param | MesWmStockTakingPlanParamDO | MES 盘点方案参数 |
| mes_wm_stock_taking_task | MesWmStockTakingTaskDO | MES 盘点任务 |
| mes_wm_stock_taking_task_line | MesWmStockTakingTaskLineDO | MES 盘点任务行 |
| mes_wm_stock_taking_task_result | MesWmStockTakingTaskResultDO | MES 盘点结果 |
| mes_wm_transaction | MesWmTransactionDO | MES 库存事务流水 记录每一笔库存增减事件，系统自动生成，只读查询，不允许人工维护。 |
| mes_wm_transfer | MesWmTransferDO | MES 转移单 |
| mes_wm_transfer_detail | MesWmTransferDetailDO | MES 调拨明细 |
| mes_wm_transfer_line | MesWmTransferLineDO | MES 转移单行 |
| mes_wm_warehouse | MesWmWarehouseDO | MES 仓库 |
| mes_wm_warehouse_area | MesWmWarehouseAreaDO | MES 库位 |
| mes_wm_warehouse_location | MesWmWarehouseLocationDO | MES 库区 |

