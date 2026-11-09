# 主数据管理接口 (controller/admin/md)

> MES 主数据（md）域：物料/物料分类/物料批次属性配置、产品 BOM/SIP/SOP、客户、供应商、计量单位、编码规则（含规则组成与生成记录）、车间、工作站及其设备/工装/人力资源。主数据由其他业务域 Service/Controller 直接注入 md 域 Service 批量拼接 VO 回显（如工单列表回填产品/客户/供应商/单位名称），物料与设备支持 Excel 批量导入导出，业务编码由 md/autocode 策略模式 + Redis 流水号生成。
>
> 本域共 **17 个控制器、95 个端点**，端点清单由 Controller 源码逐一提取（路径、HTTP 方法、权限标识、请求/响应 VO 与源码一致）。
>
> - 通用约定：标准 CRUD 端点集合 `POST create` / `PUT update` / `DELETE delete` / `GET get` / `GET page` / `GET export-excel`（导出返回 Excel 文件流，方法返回 void）；
> - 权限标识统一为 `mes:{域-功能}:{操作}`；个别下拉/模板端点（如 `simple-list`、`get-import-template`）仅要求登录，无独立 `@PreAuthorize`，表中记为「已认证（仅登录）」；
> - 请求/响应 VO 字段结构与状态枚举取值详见 [data-model.md](data-model.md)，业务逻辑与代码模式见 [code-patterns.md](code-patterns.md)、模块概览见 [README.md](README.md)。

## 控制器索引

| Controller | 路径前缀 | 说明 | 端点数 |
|------------|----------|------|--------|
| MesMdAutoCodePartController | `/mes/md/auto-code-part` | MES 编码规则组成 | 5 |
| MesMdAutoCodeRecordController | `/mes/md/auto-code-record` | MES 编码生成记录 | 1 |
| MesMdAutoCodeRuleController | `/mes/md/auto-code-rule` | MES 编码规则 | 7 |
| MesMdClientController | `/mes/md-client` | MES 客户 | 8 |
| MesMdItemBatchConfigController | `/mes/md/item-batch-config` | MES 物料批次属性配置 | 2 |
| MesMdItemController | `/mes/md/item` | MES 物料产品 | 9 |
| MesMdItemTypeController | `/mes/md/item-type` | MES 物料产品分类 | 6 |
| MesMdProductBomController | `/mes/md/product-bom` | MES 产品BOM | 6 |
| MesMdProductSipController | `/mes/md/product-sip` | MES 产品SIP | 6 |
| MesMdProductSopController | `/mes/md/product-sop` | MES 产品SOP | 6 |
| MesMdUnitMeasureController | `/mes/md/unit-measure` | MES 计量单位 | 7 |
| MesMdVendorController | `/mes/md-vendor` | MES 供应商 | 8 |
| MesMdWorkshopController | `/mes/md-workshop` | MES 车间 | 7 |
| MesMdWorkstationController | `/mes/md-workstation` | MES 工作站 | 6 |
| MesMdWorkstationMachineController | `/mes/md-workstation-machine` | MES 设备资源 | 3 |
| MesMdWorkstationToolController | `/mes/md-workstation-tool` | MES 工装夹具资源 | 4 |
| MesMdWorkstationWorkerController | `/mes/md-workstation-worker` | MES 人力资源 | 4 |


## 1. MesMdAutoCodePartController（管理后台 - MES 编码规则组成，前缀 `/mes/md/auto-code-part`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/auto-code-part/create` | 创建规则组成 | `mes:auto-code-rule:update` | MesMdAutoCodePartSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/auto-code-part/update` | 更新规则组成 | `mes:auto-code-rule:update` | MesMdAutoCodePartSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/auto-code-part/delete` | 删除规则组成 | `mes:auto-code-rule:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/auto-code-part/get` | 获得规则组成 | `mes:auto-code-rule:query` | Query 参数 id（Long） | CommonResult<MesMdAutoCodePartRespVO> |
| GET | `/mes/md/auto-code-part/list-by-rule-id` | 根据规则 ID 获得规则组成列表 | `mes:auto-code-rule:query` | Query 参数 ruleId（Long） | CommonResult<List<MesMdAutoCodePartRespVO>> |

## 2. MesMdAutoCodeRecordController（管理后台 - MES 编码生成记录，前缀 `/mes/md/auto-code-record`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/auto-code-record/generate` | 生成编码 | `mes:auto-code-rule:query` | MesMdAutoCodeGenerateReqVO | CommonResult<String> |

## 3. MesMdAutoCodeRuleController（管理后台 - MES 编码规则，前缀 `/mes/md/auto-code-rule`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/auto-code-rule/create` | 创建编码规则 | `mes:auto-code-rule:create` | MesMdAutoCodeRuleSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/auto-code-rule/update` | 更新编码规则 | `mes:auto-code-rule:update` | MesMdAutoCodeRuleSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/auto-code-rule/delete` | 删除编码规则 | `mes:auto-code-rule:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/auto-code-rule/get` | 获得编码规则 | `mes:auto-code-rule:query` | Query 参数 id（Long） | CommonResult<MesMdAutoCodeRuleRespVO> |
| GET | `/mes/md/auto-code-rule/page` | 获得编码规则分页 | `mes:auto-code-rule:query` | MesMdAutoCodeRulePageReqVO | CommonResult<PageResult<MesMdAutoCodeRuleRespVO>> |
| GET | `/mes/md/auto-code-rule/simple-list` | 获得编码规则精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesMdAutoCodeRuleRespVO>> |
| GET | `/mes/md/auto-code-rule/export-excel` | 导出编码规则 Excel | `mes:auto-code-rule:export` | MesMdAutoCodeRulePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 4. MesMdClientController（管理后台 - MES 客户，前缀 `/mes/md-client`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-client/create` | 创建客户 | `mes:md-client:create` | MesMdClientSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md-client/update` | 更新客户 | `mes:md-client:update` | MesMdClientSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md-client/delete` | 删除客户 | `mes:md-client:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-client/get` | 获得客户 | `mes:md-client:query` | Query 参数 id（Long） | CommonResult<MesMdClientRespVO> |
| GET | `/mes/md-client/page` | 获得客户分页 | `mes:md-client:query` | MesMdClientPageReqVO | CommonResult<PageResult<MesMdClientRespVO>> |
| GET | `/mes/md-client/export-excel` | 导出客户 Excel | `mes:md-client:export` | MesMdClientPageReqVO, HttpServletResponse | Excel 文件流（void） |
| GET | `/mes/md-client/get-import-template` | 获得客户导入模板 | `已认证（仅登录）` | HttpServletResponse | Excel 文件流（void） |
| POST | `/mes/md-client/import` | 导入客户 | `mes:md-client:import` | Query 参数 file（MultipartFile）, Query 参数 updateSupport（Boolean） | CommonResult<MesMdClientImportRespVO> |

## 5. MesMdItemBatchConfigController（管理后台 - MES 物料批次属性配置，前缀 `/mes/md/item-batch-config`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/md/item-batch-config/get-by-item-id` | 根据物料编号获取批次属性配置 | `mes:md-item:query` | Query 参数 itemId（Long） | CommonResult<MesMdItemBatchConfigRespVO> |
| POST | `/mes/md/item-batch-config/save` | 保存批次属性配置（新增或更新） | `mes:md-item:update` | MesMdItemBatchConfigSaveReqVO | CommonResult<Long> |

## 6. MesMdItemController（管理后台 - MES 物料产品，前缀 `/mes/md/item`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/item/create` | 创建物料产品 | `mes:md-item:create` | MesMdItemSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/item/update` | 更新物料产品 | `mes:md-item:update` | MesMdItemSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/md/item/update-status` | 更新物料产品状态 | `mes:md-item:update` | Query 参数 id（Long）, Query 参数 status（Integer） | CommonResult<Boolean> |
| DELETE | `/mes/md/item/delete` | 删除物料产品 | `mes:md-item:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/item/get` | 获得物料产品 | `mes:md-item:query` | Query 参数 id（Long） | CommonResult<MesMdItemRespVO> |
| GET | `/mes/md/item/page` | 获得物料产品分页 | `mes:md-item:query` | MesMdItemPageReqVO | CommonResult<PageResult<MesMdItemRespVO>> |
| GET | `/mes/md/item/export-excel` | 导出物料产品 Excel | `mes:md-item:export` | MesMdItemPageReqVO, HttpServletResponse | Excel 文件流（void） |
| GET | `/mes/md/item/get-import-template` | 获得物料导入模板 | `已认证（仅登录）` | HttpServletResponse | Excel 文件流（void） |
| POST | `/mes/md/item/import` | 导入物料 | `mes:md-item:import` | Query 参数 file（MultipartFile）, Query 参数 updateSupport（Boolean） | CommonResult<MesMdItemImportRespVO> |

## 7. MesMdItemTypeController（管理后台 - MES 物料产品分类，前缀 `/mes/md/item-type`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/item-type/create` | 创建物料产品分类 | `mes:md-item-type:create` | MesMdItemTypeSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/item-type/update` | 更新物料产品分类 | `mes:md-item-type:update` | MesMdItemTypeSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/item-type/delete` | 删除物料产品分类 | `mes:md-item-type:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/item-type/get` | 获得物料产品分类 | `mes:md-item-type:query` | Query 参数 id（Long） | CommonResult<MesMdItemTypeRespVO> |
| GET | `/mes/md/item-type/list` | 获得物料产品分类列表 | `mes:md-item-type:query` | MesMdItemTypeListReqVO | CommonResult<List<MesMdItemTypeRespVO>> |
| GET | `/mes/md/item-type/simple-list` | 获得物料产品分类精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesMdItemTypeRespVO>> |

## 8. MesMdProductBomController（管理后台 - MES 产品BOM，前缀 `/mes/md/product-bom`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/product-bom/create` | 创建产品BOM | `mes:md-item:create` | MesMdProductBomSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/product-bom/update` | 更新产品BOM | `mes:md-item:update` | MesMdProductBomSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/product-bom/delete` | 删除产品BOM | `mes:md-item:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/product-bom/get` | 获得产品BOM | `mes:md-item:query` | Query 参数 id（Long） | CommonResult<MesMdProductBomRespVO> |
| GET | `/mes/md/product-bom/page` | 获得产品BOM分页 | `mes:md-item:query` | MesMdProductBomPageReqVO | CommonResult<PageResult<MesMdProductBomRespVO>> |
| GET | `/mes/md/product-bom/list-by-item-id` | 根据物料产品编号获得产品BOM列表 | `mes:md-item:query` | Query 参数 itemId（Long） | CommonResult<List<MesMdProductBomRespVO>> |

## 9. MesMdProductSipController（管理后台 - MES 产品SIP，前缀 `/mes/md/product-sip`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/product-sip/create` | 创建产品SIP | `mes:md-item:create` | MesMdProductSipSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/product-sip/update` | 更新产品SIP | `mes:md-item:update` | MesMdProductSipSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/product-sip/delete` | 删除产品SIP | `mes:md-item:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/product-sip/get` | 获得产品SIP | `mes:md-item:query` | Query 参数 id（Long） | CommonResult<MesMdProductSipRespVO> |
| GET | `/mes/md/product-sip/page` | 获得产品SIP分页 | `mes:md-item:query` | MesMdProductSipPageReqVO | CommonResult<PageResult<MesMdProductSipRespVO>> |
| GET | `/mes/md/product-sip/list-by-item-id` | 根据物料产品编号，获得产品SIP列表 | `mes:md-item:query` | Query 参数 itemId（Long） | CommonResult<List<MesMdProductSipRespVO>> |

## 10. MesMdProductSopController（管理后台 - MES 产品SOP，前缀 `/mes/md/product-sop`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/product-sop/create` | 创建产品SOP | `mes:md-item:create` | MesMdProductSopSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/product-sop/update` | 更新产品SOP | `mes:md-item:update` | MesMdProductSopSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/product-sop/delete` | 删除产品SOP | `mes:md-item:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/product-sop/get` | 获得产品SOP | `mes:md-item:query` | Query 参数 id（Long） | CommonResult<MesMdProductSopRespVO> |
| GET | `/mes/md/product-sop/page` | 获得产品SOP分页 | `mes:md-item:query` | MesMdProductSopPageReqVO | CommonResult<PageResult<MesMdProductSopRespVO>> |
| GET | `/mes/md/product-sop/list-by-item-id` | 根据物料产品编号，获得产品SOP列表 | `mes:md-item:query` | Query 参数 itemId（Long） | CommonResult<List<MesMdProductSopRespVO>> |

## 11. MesMdUnitMeasureController（管理后台 - MES 计量单位，前缀 `/mes/md/unit-measure`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md/unit-measure/create` | 创建计量单位 | `mes:md-unit-measure:create` | MesMdUnitMeasureSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md/unit-measure/update` | 更新计量单位 | `mes:md-unit-measure:update` | MesMdUnitMeasureSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md/unit-measure/delete` | 删除计量单位 | `mes:md-unit-measure:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md/unit-measure/get` | 获得计量单位 | `mes:md-unit-measure:query` | Query 参数 id（Long） | CommonResult<MesMdUnitMeasureRespVO> |
| GET | `/mes/md/unit-measure/page` | 获得计量单位分页 | `mes:md-unit-measure:query` | MesMdUnitMeasurePageReqVO | CommonResult<PageResult<MesMdUnitMeasureRespVO>> |
| GET | `/mes/md/unit-measure/simple-list` | 获得计量单位精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesMdUnitMeasureRespVO>> |
| GET | `/mes/md/unit-measure/export-excel` | 导出计量单位 Excel | `mes:md-unit-measure:export` | MesMdUnitMeasurePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 12. MesMdVendorController（管理后台 - MES 供应商，前缀 `/mes/md-vendor`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-vendor/create` | 创建供应商 | `mes:md-vendor:create` | MesMdVendorSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md-vendor/update` | 更新供应商 | `mes:md-vendor:update` | MesMdVendorSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md-vendor/delete` | 删除供应商 | `mes:md-vendor:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-vendor/get` | 获得供应商 | `mes:md-vendor:query` | Query 参数 id（Long） | CommonResult<MesMdVendorRespVO> |
| GET | `/mes/md-vendor/page` | 获得供应商分页 | `mes:md-vendor:query` | MesMdVendorPageReqVO | CommonResult<PageResult<MesMdVendorRespVO>> |
| GET | `/mes/md-vendor/export-excel` | 导出供应商 Excel | `mes:md-vendor:export` | MesMdVendorPageReqVO, HttpServletResponse | Excel 文件流（void） |
| GET | `/mes/md-vendor/get-import-template` | 获得供应商导入模板 | `已认证（仅登录）` | HttpServletResponse | Excel 文件流（void） |
| POST | `/mes/md-vendor/import` | 导入供应商 | `mes:md-vendor:import` | Query 参数 file（MultipartFile）, Query 参数 updateSupport（Boolean） | CommonResult<MesMdVendorImportRespVO> |

## 13. MesMdWorkshopController（管理后台 - MES 车间，前缀 `/mes/md-workshop`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-workshop/create` | 创建车间 | `mes:md-workshop:create` | MesMdWorkshopSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md-workshop/update` | 更新车间 | `mes:md-workshop:update` | MesMdWorkshopSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md-workshop/delete` | 删除车间 | `mes:md-workshop:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-workshop/get` | 获得车间 | `mes:md-workshop:query` | Query 参数 id（Long） | CommonResult<MesMdWorkshopRespVO> |
| GET | `/mes/md-workshop/page` | 获得车间分页 | `mes:md-workshop:query` | MesMdWorkshopPageReqVO | CommonResult<PageResult<MesMdWorkshopRespVO>> |
| GET | `/mes/md-workshop/simple-list` | 获得车间精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesMdWorkshopRespVO>> |
| GET | `/mes/md-workshop/export-excel` | 导出车间 Excel | `mes:md-workshop:export` | MesMdWorkshopPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 14. MesMdWorkstationController（管理后台 - MES 工作站，前缀 `/mes/md-workstation`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-workstation/create` | 创建工作站 | `mes:md-workstation:create` | MesMdWorkstationSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md-workstation/update` | 更新工作站 | `mes:md-workstation:update` | MesMdWorkstationSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md-workstation/delete` | 删除工作站 | `mes:md-workstation:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-workstation/get` | 获得工作站 | `mes:md-workstation:query` | Query 参数 id（Long） | CommonResult<MesMdWorkstationRespVO> |
| GET | `/mes/md-workstation/page` | 获得工作站分页 | `mes:md-workstation:query` | MesMdWorkstationPageReqVO | CommonResult<PageResult<MesMdWorkstationRespVO>> |
| GET | `/mes/md-workstation/export-excel` | 导出工作站 Excel | `mes:md-workstation:export` | MesMdWorkstationPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 15. MesMdWorkstationMachineController（管理后台 - MES 设备资源，前缀 `/mes/md-workstation-machine`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-workstation-machine/create` | 创建设备资源 | `mes:md-workstation:update` | MesMdWorkstationMachineSaveReqVO | CommonResult<Long> |
| DELETE | `/mes/md-workstation-machine/delete` | 删除设备资源 | `mes:md-workstation:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-workstation-machine/list-by-workstation` | 获得设备资源列表 | `mes:md-workstation:query` | Query 参数 workstationId（Long） | CommonResult<List<MesMdWorkstationMachineRespVO>> |

## 16. MesMdWorkstationToolController（管理后台 - MES 工装夹具资源，前缀 `/mes/md-workstation-tool`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-workstation-tool/create` | 创建工装夹具资源 | `mes:md-workstation:update` | MesMdWorkstationToolSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md-workstation-tool/update` | 更新工装夹具资源 | `mes:md-workstation:update` | MesMdWorkstationToolSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md-workstation-tool/delete` | 删除工装夹具资源 | `mes:md-workstation:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-workstation-tool/list-by-workstation` | 获得工装夹具资源列表 | `mes:md-workstation:query` | Query 参数 workstationId（Long） | CommonResult<List<MesMdWorkstationToolRespVO>> |

## 17. MesMdWorkstationWorkerController（管理后台 - MES 人力资源，前缀 `/mes/md-workstation-worker`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/md-workstation-worker/create` | 创建人力资源 | `mes:md-workstation:update` | MesMdWorkstationWorkerSaveReqVO | CommonResult<Long> |
| PUT | `/mes/md-workstation-worker/update` | 更新人力资源 | `mes:md-workstation:update` | MesMdWorkstationWorkerSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/md-workstation-worker/delete` | 删除人力资源 | `mes:md-workstation:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/md-workstation-worker/list-by-workstation` | 获得人力资源列表 | `mes:md-workstation:query` | Query 参数 workstationId（Long） | CommonResult<List<MesMdWorkstationWorkerRespVO>> |
