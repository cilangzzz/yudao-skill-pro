# 主数据管理 API 文档

> 模块路径：`yudao-module-mes`

---

## 1. 物料管理（Item）

**Controller**: `MesItemController`
**路径前缀**: `/admin-api/mes/item`
**权限前缀**: `mes:item:*`

### 1.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建物料 | `mes:item:create` |
| PUT | `/update` | 更新物料 | `mes:item:update` |
| DELETE | `/delete` | 删除物料 | `mes:item:delete` |
| GET | `/get` | 获取物料详情 | `mes:item:query` |
| GET | `/page` | 物料分页查询 | `mes:item:query` |
| GET | `/list-all` | 获取所有物料（下拉选择用） | `mes:item:query` |
| GET | `/export` | 导出物料 | `mes:item:export` |

### 1.2 请求/响应 VO

**MesItemSaveReqVO**（创建/更新请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 物料名称 |
| itemTypeId | Long | 是 | 物料分类编号 |
| code | String | 是 | 物料编码 |
| spec | String | 否 | 规格型号 |
| unitOfMeasure | String | 是 | 计量单位 |
| defaultWarehouseId | Long | 否 | 默认仓库编号 |
| defaultLocationId | Long | 否 | 默认库位编号 |
| minStock | BigDecimal | 否 | 最小库存 |
| maxStock | BigDecimal | 否 | 最大库存 |
| safetyStock | BigDecimal | 否 | 安全库存 |
| shelfLife | Integer | 否 | 保质期（天） |
| batchSize | BigDecimal | 否 | 批量大小 |
| defaultVendorId | Long | 否 | 默认供应商编号 |
| purchasePrice | BigDecimal | 否 | 采购单价 |
| salePrice | BigDecimal | 否 | 销售单价 |
| status | Integer | 是 | 状态 |
| remark | String | 否 | 备注 |

**MesItemPageReqVO**（分页查询请求）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 否 | 物料名称（模糊查询） |
| code | String | 否 | 物料编码（模糊查询） |
| itemTypeId | Long | 否 | 物料分类编号 |
| status | Integer | 否 | 状态 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页条数 |

---

## 2. 物料分类（ItemType）

**Controller**: `MesItemTypeController`
**路径前缀**: `/admin-api/mes/item-type`
**权限前缀**: `mes:item-type:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建物料分类 | `mes:item-type:create` |
| PUT | `/update` | 更新物料分类 | `mes:item-type:update` |
| DELETE | `/delete` | 删除物料分类 | `mes:item-type:delete` |
| GET | `/get` | 获取分类详情 | `mes:item-type:query` |
| GET | `/list` | 获取分类列表（树形） | `mes:item-type:query` |

---

## 3. 批次配置（BatchConfig）

**Controller**: `MesBatchConfigController`
**路径前缀**: `/admin-api/mes/batch-config`
**权限前缀**: `mes:batch-config:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建批次配置 | `mes:batch-config:create` |
| PUT | `/update` | 更新批次配置 | `mes:batch-config:update` |
| DELETE | `/delete` | 删除批次配置 | `mes:batch-config:delete` |
| GET | `/get` | 获取配置详情 | `mes:batch-config:query` |
| GET | `/page` | 分页查询 | `mes:batch-config:query` |

---

## 4. 产品 BOM（ProductBom）

**Controller**: `MesProductBomController`
**路径前缀**: `/admin-api/mes/bom`
**权限前缀**: `mes:bom:*`

### 4.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建 BOM | `mes:bom:create` |
| PUT | `/update` | 更新 BOM | `mes:bom:update` |
| DELETE | `/delete` | 删除 BOM | `mes:bom:delete` |
| GET | `/get` | 获取 BOM 详情（含子表） | `mes:bom:query` |
| GET | `/page` | BOM 分页查询 | `mes:bom:query` |

### 4.2 BOM 结构

BOM（物料清单）定义产品由哪些子物料组成及其用量关系：
- **主表**: 产品信息（成品物料、BOM 版本）
- **子表**: BOM 行项（子物料、用量、损耗率）

---

## 5. 产品 SOP（ProductSop）

**Controller**: `MesProductSopController`
**路径前缀**: `/admin-api/mes/sop`
**权限前缀**: `mes:sop:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建 SOP | `mes:sop:create` |
| PUT | `/update` | 更新 SOP | `mes:sop:update` |
| DELETE | `/delete` | 删除 SOP | `mes:sop:delete` |
| GET | `/get` | 获取 SOP 详情 | `mes:sop:query` |
| GET | `/page` | SOP 分页查询 | `mes:sop:query` |

> SOP（Standard Operating Procedure）标准作业指导书，定义产品的标准生产操作步骤。

---

## 6. 产品 SIP（ProductSip）

**Controller**: `MesProductSipController`
**路径前缀**: `/admin-api/mes/sip`
**权限前缀**: `mes:sip:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建 SIP | `mes:sip:create` |
| PUT | `/update` | 更新 SIP | `mes:sip:update` |
| DELETE | `/delete` | 删除 SIP | `mes:sip:delete` |
| GET | `/get` | 获取 SIP 详情 | `mes:sip:query` |
| GET | `/page` | SIP 分页查询 | `mes:sip:query` |

> SIP（Standard Inspection Procedure）标准检验程序，定义产品的标准检验步骤和判定标准。

---

## 7. 客户管理（Client）

**Controller**: `MesClientController`
**路径前缀**: `/admin-api/mes/client`
**权限前缀**: `mes:client:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建客户 | `mes:client:create` |
| PUT | `/update` | 更新客户 | `mes:client:update` |
| DELETE | `/delete` | 删除客户 | `mes:client:delete` |
| GET | `/get` | 获取客户详情 | `mes:client:query` |
| GET | `/page` | 客户分页查询 | `mes:client:query` |
| GET | `/list-all` | 获取所有客户（下拉选择用） | `mes:client:query` |

---

## 8. 供应商管理（Vendor）

**Controller**: `MesVendorController`
**路径前缀**: `/admin-api/mes/vendor`
**权限前缀**: `mes:vendor:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建供应商 | `mes:vendor:create` |
| PUT | `/update` | 更新供应商 | `mes:vendor:update` |
| DELETE | `/delete` | 删除供应商 | `mes:vendor:delete` |
| GET | `/get` | 获取供应商详情 | `mes:vendor:query` |
| GET | `/page` | 供应商分页查询 | `mes:vendor:query` |
| GET | `/list-all` | 获取所有供应商（下拉选择用） | `mes:vendor:query` |

---

## 9. 计量单位（UnitMeasure）

**Controller**: `MesUnitMeasureController`
**路径前缀**: `/admin-api/mes/unitmeasure`
**权限前缀**: `mes:unitmeasure:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建计量单位 | `mes:unitmeasure:create` |
| PUT | `/update` | 更新计量单位 | `mes:unitmeasure:update` |
| DELETE | `/delete` | 删除计量单位 | `mes:unitmeasure:delete` |
| GET | `/get` | 获取计量单位详情 | `mes:unitmeasure:query` |
| GET | `/page` | 分页查询 | `mes:unitmeasure:query` |
| GET | `/list-all` | 获取所有计量单位 | `mes:unitmeasure:query` |

---

## 10. 车间管理（Workshop）

**Controller**: `MesWorkshopController`
**路径前缀**: `/admin-api/mes/workshop`
**权限前缀**: `mes:workshop:*`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建车间 | `mes:workshop:create` |
| PUT | `/update` | 更新车间 | `mes:workshop:update` |
| DELETE | `/delete` | 删除车间 | `mes:workshop:delete` |
| GET | `/get` | 获取车间详情 | `mes:workshop:query` |
| GET | `/page` | 车间分页查询 | `mes:workshop:query` |
| GET | `/list-all` | 获取所有车间 | `mes:workshop:query` |

---

## 11. 工位管理（Workstation）

**Controller**: `MesWorkstationController`
**路径前缀**: `/admin-api/mes/workstation`
**权限前缀**: `mes:workstation:*`

### 11.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建工位 | `mes:workstation:create` |
| PUT | `/update` | 更新工位 | `mes:workstation:update` |
| DELETE | `/delete` | 删除工位 | `mes:workstation:delete` |
| GET | `/get` | 获取工位详情（含关联机器/工具/工人） | `mes:workstation:query` |
| GET | `/page` | 工位分页查询 | `mes:workstation:query` |
| GET | `/list-all` | 获取所有工位 | `mes:workstation:query` |

### 11.2 工位关联关系

工位可关联多种资源：
- **机器**: `mes_md_workstation_machine` - 工位绑定的设备
- **工具**: `mes_md_workstation_tool` - 工位绑定的工具
- **工人**: `mes_md_workstation_worker` - 工位分配的操作工人

---

## 12. 自动编码规则（AutoCode）

**Controller**: `MesAutoCodeRuleController`
**路径前缀**: `/admin-api/mes/auto-code`
**权限前缀**: `mes:auto-code:*`

### 12.1 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/create` | 创建编码规则 | `mes:auto-code:create` |
| PUT | `/update` | 更新编码规则 | `mes:auto-code:update` |
| DELETE | `/delete` | 删除编码规则 | `mes:auto-code:delete` |
| GET | `/get` | 获取编码规则详情（含零件定义） | `mes:auto-code:query` |
| GET | `/page` | 分页查询 | `mes:auto-code:query` |
| POST | `/generate` | 根据规则生成编码 | `mes:auto-code:query` |

### 12.2 编码规则结构

自动编码由多个"零件"组合而成：

| 零件类型 | 说明 | 示例 |
|---------|------|------|
| 日期 | 按日期格式生成 | yyyyMMdd -> 20260608 |
| 固定字符 | 固定字符串 | PROD -> PROD |
| 输入字符 | 用户输入的字符 | 车间代码 |
| 序列号 | 自增序号，支持补零 | 0001, 0002... |

### 12.3 设计说明

- `MesAutoCodeRuleDO` 定义编码规则主表
- `MesAutoCodePartDO` 定义规则的各个零件（顺序、类型、格式）
- `MesAutoCodeRecordDO` 记录已生成的编码（用于序列号去重）
- 采用策略模式，不同零件类型有不同的生成策略

---

## RPC API 跨模块接口

### 跨模块依赖

| API 接口 | 所在模块 | 用途 |
|----------|---------|------|
| `AdminUserApi` | system | 获取用户信息（工位操作员名称等） |
| `RoleApi` | system | 角色权限校验 |

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 待确认 | 物料不存在 |
| 待确认 | 物料分类不存在 |
| 待确认 | BOM 不存在 |
| 待确认 | 客户不存在 |
| 待确认 | 供应商不存在 |
| 待确认 | 车间不存在 |
| 待确认 | 工位不存在 |
| 待确认 | 编码规则不存在 |
