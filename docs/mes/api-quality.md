# 质量管理 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 检验模板（QcTemplate）

**Controller**: `MesQcTemplateController`
**路径前缀**: `/admin-api/mes/qc/template`
**权限前缀**: `mes:qc:template:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建检验模板 | `mes:qc:template:create` |
| PUT | `/update` | 更新检验模板 | `mes:qc:template:update` |
| DELETE | `/delete` | 删除检验模板 | `mes:qc:template:delete` |
| GET | `/get` | 获取模板详情（含检验项/指标） | `mes:qc:template:query` |
| GET | `/page` | 模板分页查询 | `mes:qc:template:query` |
| GET | `/list-all` | 获取所有模板 | `mes:qc:template:query` |

### 1.2 模板结构

检验模板由三层结构组成：

| 层级 | 表 | 说明 |
|------|---|------|
| 模板主表 | `mes_qc_template` | 模板名称、类型、适用物料 |
| 检验项 | `mes_qc_template_item` | 模板下的检验项目列表 |
| 检验指标 | `mes_qc_template_indicator` | 每个检验项的判定指标（上限/下限/标准值） |

---

## 2. 检验指标（QcIndicator）

**Controller**: `MesQcIndicatorController`
**路径前缀**: `/admin-api/mes/qc/indicator`
**权限前缀**: `mes:qc:indicator:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建检验指标 | `mes:qc:indicator:create` |
| PUT | `/update` | 更新检验指标 | `mes:qc:indicator:update` |
| DELETE | `/delete` | 删除检验指标 | `mes:qc:indicator:delete` |
| GET | `/get` | 获取指标详情 | `mes:qc:indicator:query` |
| GET | `/page` | 指标分页查询 | `mes:qc:indicator:query` |
| GET | `/list-all` | 获取所有指标 | `mes:qc:indicator:query` |

### 检验指标结果

检验完成后，每个指标产生结果记录：
- `mes_qc_indicator_result` - 指标结果主表（关联检验单）
- `mes_qc_indicator_result_detail` - 指标结果明细（多次测量值）

---

## 3. 缺陷管理（QcDefect）

**Controller**: `MesQcDefectController`
**路径前缀**: `/admin-api/mes/qc/defect`
**权限前缀**: `mes:qc:defect:*`

### 3.1 缺陷定义

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建缺陷类型 | `mes:qc:defect:create` |
| PUT | `/update` | 更新缺陷类型 | `mes:qc:defect:update` |
| DELETE | `/delete` | 删除缺陷类型 | `mes:qc:defect:delete` |
| GET | `/get` | 获取缺陷详情 | `mes:qc:defect:query` |
| GET | `/page` | 缺陷分页查询 | `mes:qc:defect:query` |
| GET | `/list-all` | 获取所有缺陷类型 | `mes:qc:defect:query` |

### 3.2 缺陷记录

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/record/create` | 记录缺陷 | `mes:qc:defect:create` |
| GET | `/record/page` | 缺陷记录分页查询 | `mes:qc:defect:query` |

---

## 4. 来料检验（IQC）

**Controller**: `MesQcIqcController`
**路径前缀**: `/admin-api/mes/qc/iqc`
**权限前缀**: `mes:qc:iqc:*`

### 4.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建来料检验单 | `mes:qc:iqc:create` |
| PUT | `/update` | 更新检验单 | `mes:qc:iqc:update` |
| DELETE | `/delete` | 删除检验单 | `mes:qc:iqc:delete` |
| GET | `/get` | 获取检验单详情（含检验行） | `mes:qc:iqc:query` |
| GET | `/page` | 检验单分页查询 | `mes:qc:iqc:query` |

### 4.2 IQC 结构

来料检验用于对供应商来料进行质量检验：

| 层级 | 表 | 说明 |
|------|---|------|
| 检验单主表 | `mes_qc_iqc` | 供应商、到货单号、检验日期、判定结果 |
| 检验行 | `mes_qc_iqc_line` | 每个物料的检验明细（合格数/不合格数） |

### 4.3 IQC 业务流程

```
1. 仓库到货 -> 创建到货通知 (ArrivalNotice)
2. 质检员创建 IQC 检验单，关联到货通知
3. 逐项检验物料，记录检验指标结果
4. 判定合格/不合格，记录缺陷
5. 合格物料办理入库 (ItemReceipt)
6. 不合格物料办理退货 (ReturnVendor)
```

---

## 5. 过程检验（IPQC）

**Controller**: `MesQcIpqcController`
**路径前缀**: `/admin-api/mes/qc/ipqc`
**权限前缀**: `mes:qc:ipqc:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建过程检验单 | `mes:qc:ipqc:create` |
| PUT | `/update` | 更新检验单 | `mes:qc:ipqc:update` |
| DELETE | `/delete` | 删除检验单 | `mes:qc:ipqc:delete` |
| GET | `/get` | 获取检验单详情（含检验行） | `mes:qc:ipqc:query` |
| GET | `/page` | 检验单分页查询 | `mes:qc:ipqc:query` |

### IPQC 结构

| 层级 | 表 | 说明 |
|------|---|------|
| 检验单主表 | `mes_qc_ipqc` | 工单、工序、检验日期、判定结果 |
| 检验行 | `mes_qc_ipqc_line` | 检验明细 |

> IPQC（In-Process Quality Control）过程检验，在生产过程中对在制品进行质量检验。

---

## 6. 出货检验（OQC）

**Controller**: `MesQcOqcController`
**路径前缀**: `/admin-api/mes/qc/oqc`
**权限前缀**: `mes:qc:oqc:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建出货检验单 | `mes:qc:oqc:create` |
| PUT | `/update` | 更新检验单 | `mes:qc:oqc:update` |
| DELETE | `/delete` | 删除检验单 | `mes:qc:oqc:delete` |
| GET | `/get` | 获取检验单详情（含检验行） | `mes:qc:oqc:query` |
| GET | `/page` | 检验单分页查询 | `mes:qc:oqc:query` |

### OQC 结构

| 层级 | 表 | 说明 |
|------|---|------|
| 检验单主表 | `mes_qc_oqc` | 客户、出货单号、检验日期、判定结果 |
| 检验行 | `mes_qc_oqc_line` | 检验明细 |

> OQC（Outgoing Quality Control）出货检验，产品出库发货前的最终质量检验。

---

## 7. 退货检验（RQC）

**Controller**: `MesQcRqcController`
**路径前缀**: `/admin-api/mes/qc/rqc`
**权限前缀**: `mes:qc:rqc:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建退货检验单 | `mes:qc:rqc:create` |
| PUT | `/update` | 更新检验单 | `mes:qc:rqc:update` |
| DELETE | `/delete` | 删除检验单 | `mes:qc:rqc:delete` |
| GET | `/get` | 获取检验单详情（含检验行） | `mes:qc:rqc:query` |
| GET | `/page` | 检验单分页查询 | `mes:qc:rqc:query` |

### RQC 结构

| 层级 | 表 | 说明 |
|------|---|------|
| 检验单主表 | `mes_qc_rqc` | 退货来源、检验日期、判定结果 |
| 检验行 | `mes_qc_rqc_line` | 检验明细 |

> RQC（Return Quality Control）退货检验，客户退货或生产退回物料的质量检验。

---

## 8. 待检物料查询

**Controller**: `MesPendingInspectController`
**路径前缀**: `/admin-api/mes/qc/pending-inspect`
**权限前缀**: `mes:qc:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/page` | 待检物料分页查询 | `mes:qc:query` |

> 查询所有待检验的物料，包括到货待检（IQC）、生产待检（IPQC）、出货待检（OQC）等。

---

## 核心设计要点

### 检验单通用结构

所有检验单（IQC/IPQC/OQC/RQC）遵循相同的主子表结构：
- **主表**: 检验单基本信息（来源单号、检验日期、判定结果、检验员）
- **子表（检验行）**: 每个物料/批次的检验明细（合格数、不合格数、检验指标结果）

### 检验指标结果

检验过程中记录每个指标的实际测量值：
- `qc_indicator_result` - 指标结果主记录，关联检验单和指标
- `qc_indicator_result_detail` - 多次测量的详细值
- 系统自动根据指标上下限判定合格/不合格

### 缺陷关联

检验发现的不合格品关联缺陷记录：
- 缺陷类型定义（缺陷代码、名称、等级）
- 缺陷记录关联检验单和具体检验行
- 统计缺陷发生频率用于质量分析

### 与仓库联动

检验结果影响仓库操作：
- IQC 合格 -> 触发采购入库（ItemReceipt）
- IQC 不合格 -> 触发退货（ReturnVendor）
- OQC 合格 -> 允许出货（ProductIssue）
- RQC 结果 -> 决定退回入库或报废
