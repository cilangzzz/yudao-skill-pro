# 仓库管理接口 (controller/admin/wm)

> MES 仓库管理（wm）域：仓库/库区/库位三级库位体系、到货/发货通知单、采购/领料/生产/销售/外协/杂项/退货等全部出入库单据（主表-行-明细三段式，明细行锁定来源库存）、库存台账与库存事务流水（mes_wm_transaction）、批次/SN 码、条码配置与条码清单、装箱单、转移单、盘点（方案/方案参数/任务/任务行/结果）。所有库存数量变动统一经 MesWmMaterialStockService#updateMaterialStockQuantity 更新台账并写入事务流水。
>
> 本域共 **55 个控制器、359 个端点**，端点清单由 Controller 源码逐一提取（路径、HTTP 方法、权限标识、请求/响应 VO 与源码一致）。
>
> - 通用约定：标准 CRUD 端点集合 `POST create` / `PUT update` / `DELETE delete` / `GET get` / `GET page` / `GET export-excel`（导出返回 Excel 文件流，方法返回 void）；
> - 权限标识统一为 `mes:{域-功能}:{操作}`；个别下拉/模板端点（如 `simple-list`、`get-import-template`）仅要求登录，无独立 `@PreAuthorize`，表中记为「已认证（仅登录）」；
> - 请求/响应 VO 字段结构与状态枚举取值详见 [data-model.md](data-model.md)，业务逻辑与代码模式见 [code-patterns.md](code-patterns.md)、模块概览见 [README.md](README.md)。

## 控制器索引

| Controller | 路径前缀 | 说明 | 端点数 |
|------------|----------|------|--------|
| MesWmArrivalNoticeController | `/mes/wm/arrival-notice` | MES 到货通知单 | 7 |
| MesWmArrivalNoticeLineController | `/mes/wm/arrival-notice-line` | MES 到货通知单行 | 5 |
| MesWmBarcodeConfigController | `/mes/wm/barcode-config` | MES 条码配置 | 5 |
| MesWmBarcodeController | `/mes/wm/barcode` | MES 条码清单 | 8 |
| MesWmBatchController | `/mes/wm/batch` | MES 批次管理 | 4 |
| MesWmItemConsumeLineController | `/mes/wm/item-consume-line` | MES 物料消耗记录行 | 1 |
| MesWmItemReceiptController | `/mes/wm/item-receipt` | MES 采购入库单 | 10 |
| MesWmItemReceiptDetailController | `/mes/wm/item-receipt-detail` | MES 采购入库明细 | 5 |
| MesWmItemReceiptLineController | `/mes/wm/item-receipt-line` | MES 采购入库单行 | 5 |
| MesWmMaterialStockController | `/mes/wm/material-stock` | MES 库存台账 | 4 |
| MesWmMiscIssueController | `/mes/wm/misc-issue` | MES 杂项出库单 | 9 |
| MesWmMiscIssueLineController | `/mes/wm/misc-issue-line` | MES 杂项出库单行 | 5 |
| MesWmMiscReceiptController | `/mes/wm/misc-receipt` | MES 杂项入库单 | 9 |
| MesWmMiscReceiptLineController | `/mes/wm/misc-receipt-line` | MES 杂项入库单行 | 6 |
| MesWmOutsourceIssueController | `/mes/wm/outsource-issue` | MES 外协发料单 | 11 |
| MesWmOutsourceIssueDetailController | `/mes/wm/outsource-issue-detail` | MES 外协发料单明细 | 5 |
| MesWmOutsourceIssueLineController | `/mes/wm/outsource-issue-line` | MES 外协发料单行 | 6 |
| MesWmOutsourceReceiptController | `/mes/wm/outsource-receipt` | MES 外协入库单 | 10 |
| MesWmOutsourceReceiptDetailController | `/mes/wm/outsource-receipt-detail` | MES 外协入库明细 | 5 |
| MesWmOutsourceReceiptLineController | `/mes/wm/outsource-receipt-line` | MES 外协入库单行 | 5 |
| MesWmPackageController | `/mes/wm/package` | MES 装箱单 | 8 |
| MesWmPackageLineController | `/mes/wm/package-line` | MES 装箱明细 | 5 |
| MesWmProductIssueController | `/mes/wm/product-issue` | MES 领料出库单 | 11 |
| MesWmProductIssueDetailController | `/mes/wm/product-issue-detail` | MES 领料出库明细 | 5 |
| MesWmProductIssueLineController | `/mes/wm/product-issue-line` | MES 领料出库单行 | 6 |
| MesWmProductProduceLineController | `/mes/wm/product-produce-line` | MES 生产入库单行 | 1 |
| MesWmProductReceiptController | `/mes/wm/product-receipt` | MES 产品收货单 | 11 |
| MesWmProductReceiptDetailController | `/mes/wm/product-receipt-detail` | MES 产品收货单明细 | 5 |
| MesWmProductReceiptLineController | `/mes/wm/product-receipt-line` | MES 产品收货单行 | 5 |
| MesWmProductSalesController | `/mes/wm/product-sales` | MES 销售出库单 | 12 |
| MesWmProductSalesDetailController | `/mes/wm/product-sales-detail` | MES 销售出库明细 | 5 |
| MesWmProductSalesLineController | `/mes/wm/product-sales-line` | MES 销售出库单行 | 5 |
| MesWmReturnIssueController | `/mes/wm/return-issue` | MES 生产退料单 | 10 |
| MesWmReturnIssueDetailController | `/mes/wm/return-issue-detail` | MES 生产退料明细 | 5 |
| MesWmReturnIssueLineController | `/mes/wm/return-issue-line` | MES 生产退料单行 | 6 |
| MesWmReturnSalesController | `/mes/wm/return-sales` | MES 销售退货单 | 11 |
| MesWmReturnSalesDetailController | `/mes/wm/return-sales-detail` | MES 销售退货明细 | 5 |
| MesWmReturnSalesLineController | `/mes/wm/return-sales-line` | MES 销售退货单行 | 6 |
| MesWmReturnVendorController | `/mes/wm/return-vendor` | MES 供应商退货单 | 11 |
| MesWmReturnVendorDetailController | `/mes/wm/return-vendor-detail` | MES 供应商退货明细 | 5 |
| MesWmReturnVendorLineController | `/mes/wm/return-vendor-line` | MES 供应商退货单行 | 6 |
| MesWmSalesNoticeController | `/mes/wm/sales-notice` | MES 发货通知单 | 7 |
| MesWmSalesNoticeLineController | `/mes/wm/sales-notice-line` | MES 发货通知单行 | 5 |
| MesWmSnController | `/mes/wm/sn` | MES SN 码 | 6 |
| MesWmStockTakingPlanController | `/mes/wm/stocktaking-plan` | MES 盘点方案 | 7 |
| MesWmStockTakingPlanParamController | `/mes/wm/stocktaking-plan-param` | MES 盘点方案参数 | 5 |
| MesWmStockTakingTaskController | `/mes/wm/stocktaking-task` | MES 盘点任务 | 9 |
| MesWmStockTakingTaskLineController | `/mes/wm/stocktaking-task-line` | MES 盘点任务行 | 6 |
| MesWmStockTakingTaskResultController | `/mes/wm/stocktaking-task-result` | MES 盘点结果 | 5 |
| MesWmTransferController | `/mes/wm/transfer` | MES 转移单 | 11 |
| MesWmTransferDetailController | `/mes/wm/transfer-detail` | MES 调拨明细 | 5 |
| MesWmTransferLineController | `/mes/wm/transfer-line` | MES 转移单行 | 5 |
| MesWmWarehouseAreaController | `/mes/wm/warehouse-area` | MES 库位 | 6 |
| MesWmWarehouseController | `/mes/wm/warehouse` | MES 仓库 | 6 |
| MesWmWarehouseLocationController | `/mes/wm/warehouse-location` | MES 库区 | 7 |


## 1. MesWmArrivalNoticeController（管理后台 - MES 到货通知单，前缀 `/mes/wm/arrival-notice`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/arrival-notice/create` | 创建到货通知单 | `mes:wm-arrival-notice:create` | MesWmArrivalNoticeSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/arrival-notice/update` | 修改到货通知单 | `mes:wm-arrival-notice:update` | MesWmArrivalNoticeSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/arrival-notice/delete` | 删除到货通知单 | `mes:wm-arrival-notice:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/arrival-notice/get` | 获得到货通知单 | `mes:wm-arrival-notice:query` | Query 参数 id（Long） | CommonResult<MesWmArrivalNoticeRespVO> |
| GET | `/mes/wm/arrival-notice/page` | 获得到货通知单分页 | `mes:wm-arrival-notice:query` | MesWmArrivalNoticePageReqVO | CommonResult<PageResult<MesWmArrivalNoticeRespVO>> |
| GET | `/mes/wm/arrival-notice/export-excel` | 导出到货通知单 Excel | `mes:wm-arrival-notice:export` | MesWmArrivalNoticePageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/arrival-notice/submit` | 提交到货通知单 | `mes:wm-arrival-notice:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 2. MesWmArrivalNoticeLineController（管理后台 - MES 到货通知单行，前缀 `/mes/wm/arrival-notice-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/arrival-notice-line/create` | 创建到货通知单行 | `mes:wm-arrival-notice:create` | MesWmArrivalNoticeLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/arrival-notice-line/update` | 修改到货通知单行 | `mes:wm-arrival-notice:update` | MesWmArrivalNoticeLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/arrival-notice-line/delete` | 删除到货通知单行 | `mes:wm-arrival-notice:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/arrival-notice-line/get` | 获得到货通知单行 | `mes:wm-arrival-notice:query` | Query 参数 id（Long） | CommonResult<MesWmArrivalNoticeLineRespVO> |
| GET | `/mes/wm/arrival-notice-line/page` | 获得到货通知单行分页 | `mes:wm-arrival-notice:query` | MesWmArrivalNoticeLinePageReqVO | CommonResult<PageResult<MesWmArrivalNoticeLineRespVO>> |

## 3. MesWmBarcodeConfigController（管理后台 - MES 条码配置，前缀 `/mes/wm/barcode-config`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/barcode-config/create` | 创建条码配置 | `mes:wm-barcode-config:create` | MesWmBarcodeConfigSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/barcode-config/update` | 更新条码配置 | `mes:wm-barcode-config:update` | MesWmBarcodeConfigSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/barcode-config/delete` | 删除条码配置 | `mes:wm-barcode-config:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/barcode-config/get` | 获得条码配置 | `mes:wm-barcode-config:query` | Query 参数 id（Long） | CommonResult<MesWmBarcodeConfigRespVO> |
| GET | `/mes/wm/barcode-config/page` | 获得条码配置分页 | `mes:wm-barcode-config:query` | MesWmBarcodeConfigPageReqVO | CommonResult<PageResult<MesWmBarcodeConfigRespVO>> |

## 4. MesWmBarcodeController（管理后台 - MES 条码清单，前缀 `/mes/wm/barcode`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/barcode/create` | 创建条码 | `mes:wm-barcode:create` | MesWmBarcodeSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/barcode/update` | 更新条码 | `mes:wm-barcode:update` | MesWmBarcodeSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/barcode/delete` | 删除条码 | `mes:wm-barcode:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/barcode/get` | 获得条码 | `mes:wm-barcode:query` | Query 参数 id（Long） | CommonResult<MesWmBarcodeRespVO> |
| GET | `/mes/wm/barcode/page` | 获得条码分页 | `mes:wm-barcode:query` | MesWmBarcodePageReqVO | CommonResult<PageResult<MesWmBarcodeRespVO>> |
| GET | `/mes/wm/barcode/get-by-business` | 根据业务对象获取条码信息 | `mes:wm-barcode:query` | Query 参数 bizType（Integer）, Query 参数 bizId（Long） | CommonResult<MesWmBarcodeRespVO> |
| GET | `/mes/wm/barcode/generate-content` | 生成条码内容 | `mes:wm-barcode:query` | Query 参数 bizType（@NotNull(message）, Query 参数 bizCode（@NotBlank(message） | CommonResult<String> |
| GET | `/mes/wm/barcode/export-excel` | 导出条码清单 Excel | `mes:wm-barcode:export` | MesWmBarcodePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 5. MesWmBatchController（管理后台 - MES 批次管理，前缀 `/mes/wm/batch`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/wm/batch/get` | 获得批次详情 | `mes:wm-batch:query` | Query 参数 id（Long） | CommonResult<MesWmBatchRespVO> |
| GET | `/mes/wm/batch/page` | 获得批次分页 | `mes:wm-batch:query` | MesWmBatchPageReqVO | CommonResult<PageResult<MesWmBatchRespVO>> |
| GET | `/mes/wm/batch/forward-list` | 批次向前追溯 | `mes:wm-batch:query` | Query 参数 code（@Valid） | CommonResult<List<MesWmBatchRespVO>> |
| GET | `/mes/wm/batch/backward-list` | 批次向后追溯 | `mes:wm-batch:query` | Query 参数 code（@Valid） | CommonResult<List<MesWmBatchRespVO>> |

## 6. MesWmItemConsumeLineController（管理后台 - MES 物料消耗记录行，前缀 `/mes/wm/item-consume-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/wm/item-consume-line/page` | 根据报工编号分页获取消耗行列表 | `mes:pro-feedback:query` | MesWmItemConsumeLinePageReqVO | CommonResult<PageResult<MesWmItemConsumeLineRespVO>> |

## 7. MesWmItemReceiptController（管理后台 - MES 采购入库单，前缀 `/mes/wm/item-receipt`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/item-receipt/create` | 创建采购入库单 | `mes:wm-item-receipt:create` | MesWmItemReceiptSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/item-receipt/update` | 修改采购入库单 | `mes:wm-item-receipt:update` | MesWmItemReceiptSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/item-receipt/delete` | 删除采购入库单 | `mes:wm-item-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/item-receipt/get` | 获得采购入库单 | `mes:wm-item-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmItemReceiptRespVO> |
| GET | `/mes/wm/item-receipt/page` | 获得采购入库单分页 | `mes:wm-item-receipt:query` | MesWmItemReceiptPageReqVO | CommonResult<PageResult<MesWmItemReceiptRespVO>> |
| GET | `/mes/wm/item-receipt/export-excel` | 导出采购入库单 Excel | `mes:wm-item-receipt:export` | MesWmItemReceiptPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/item-receipt/submit` | 提交采购入库单 | `mes:wm-item-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/item-receipt/stock` | 执行上架 | `mes:wm-item-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/item-receipt/finish` | 执行入库 | `mes:wm-item-receipt:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/item-receipt/cancel` | 取消采购入库单 | `mes:wm-item-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 8. MesWmItemReceiptDetailController（管理后台 - MES 采购入库明细，前缀 `/mes/wm/item-receipt-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/item-receipt-detail/create` | 创建采购入库明细 | `mes:wm-item-receipt:create` | MesWmItemReceiptDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/item-receipt-detail/update` | 修改采购入库明细 | `mes:wm-item-receipt:update` | MesWmItemReceiptDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/item-receipt-detail/delete` | 删除采购入库明细 | `mes:wm-item-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/item-receipt-detail/get` | 获得采购入库明细 | `mes:wm-item-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmItemReceiptDetailRespVO> |
| GET | `/mes/wm/item-receipt-detail/list-by-line` | 获得采购入库明细列表（按行编号） | `mes:wm-item-receipt:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmItemReceiptDetailRespVO>> |

## 9. MesWmItemReceiptLineController（管理后台 - MES 采购入库单行，前缀 `/mes/wm/item-receipt-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/item-receipt-line/create` | 创建采购入库单行 | `mes:wm-item-receipt:create` | MesWmItemReceiptLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/item-receipt-line/update` | 修改采购入库单行 | `mes:wm-item-receipt:update` | MesWmItemReceiptLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/item-receipt-line/delete` | 删除采购入库单行 | `mes:wm-item-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/item-receipt-line/get` | 获得采购入库单行 | `mes:wm-item-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmItemReceiptLineRespVO> |
| GET | `/mes/wm/item-receipt-line/page` | 获得采购入库单行分页 | `mes:wm-item-receipt:query` | MesWmItemReceiptLinePageReqVO | CommonResult<PageResult<MesWmItemReceiptLineRespVO>> |

## 10. MesWmMaterialStockController（管理后台 - MES 库存台账，前缀 `/mes/wm/material-stock`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/wm/material-stock/get` | 获得库存记录 | `mes:wm-material-stock:query` | Query 参数 id（Long） | CommonResult<MesWmMaterialStockRespVO> |
| GET | `/mes/wm/material-stock/page` | 获得库存台账分页 | `mes:wm-material-stock:query` | MesWmMaterialStockPageReqVO | CommonResult<PageResult<MesWmMaterialStockRespVO>> |
| PUT | `/mes/wm/material-stock/update-frozen` | 更新库存冻结状态 | `mes:wm-material-stock:update` | MesWmMaterialStockFreezeReqVO | CommonResult<Boolean> |
| GET | `/mes/wm/material-stock/export-excel` | 导出库存台账 Excel | `mes:wm-material-stock:export` | MesWmMaterialStockPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 11. MesWmMiscIssueController（管理后台 - MES 杂项出库单，前缀 `/mes/wm/misc-issue`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/misc-issue/create` | 创建杂项出库单 | `mes:wm-misc-issue:create` | MesWmMiscIssueSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/misc-issue/update` | 修改杂项出库单 | `mes:wm-misc-issue:update` | MesWmMiscIssueSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/misc-issue/delete` | 删除杂项出库单 | `mes:wm-misc-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/misc-issue/get` | 获得杂项出库单 | `mes:wm-misc-issue:query` | Query 参数 id（Long） | CommonResult<MesWmMiscIssueRespVO> |
| GET | `/mes/wm/misc-issue/page` | 获得杂项出库单分页 | `mes:wm-misc-issue:query` | MesWmMiscIssuePageReqVO | CommonResult<PageResult<MesWmMiscIssueRespVO>> |
| GET | `/mes/wm/misc-issue/export-excel` | 导出杂项出库单 Excel | `mes:wm-misc-issue:export` | MesWmMiscIssuePageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/misc-issue/submit` | 提交杂项出库单 | `mes:wm-misc-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/misc-issue/finish` | 执行出库 | `mes:wm-misc-issue:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/misc-issue/cancel` | 取消杂项出库单 | `mes:wm-misc-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 12. MesWmMiscIssueLineController（管理后台 - MES 杂项出库单行，前缀 `/mes/wm/misc-issue-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/misc-issue-line/create` | 创建杂项出库单行 | `mes:wm-misc-issue:create` | MesWmMiscIssueLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/misc-issue-line/update` | 修改杂项出库单行 | `mes:wm-misc-issue:update` | MesWmMiscIssueLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/misc-issue-line/delete` | 删除杂项出库单行 | `mes:wm-misc-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/misc-issue-line/get` | 获得杂项出库单行 | `mes:wm-misc-issue:query` | Query 参数 id（Long） | CommonResult<MesWmMiscIssueLineRespVO> |
| GET | `/mes/wm/misc-issue-line/page` | 获得杂项出库单行分页 | `mes:wm-misc-issue:query` | MesWmMiscIssueLinePageReqVO | CommonResult<PageResult<MesWmMiscIssueLineRespVO>> |

## 13. MesWmMiscReceiptController（管理后台 - MES 杂项入库单，前缀 `/mes/wm/misc-receipt`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/misc-receipt/create` | 创建杂项入库单 | `mes:wm:misc-receipt:create` | MesWmMiscReceiptSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/misc-receipt/update` | 修改杂项入库单 | `mes:wm:misc-receipt:update` | MesWmMiscReceiptSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/misc-receipt/delete` | 删除杂项入库单 | `mes:wm:misc-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/misc-receipt/get` | 获得杂项入库单 | `mes:wm:misc-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmMiscReceiptRespVO> |
| GET | `/mes/wm/misc-receipt/page` | 获得杂项入库单分页 | `mes:wm:misc-receipt:query` | MesWmMiscReceiptPageReqVO | CommonResult<PageResult<MesWmMiscReceiptRespVO>> |
| PUT | `/mes/wm/misc-receipt/submit` | 提交审批 | `mes:wm:misc-receipt:submit` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/misc-receipt/finish` | 执行入库 | `mes:wm:misc-receipt:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/misc-receipt/cancel` | 取消杂项入库单 | `mes:wm:misc-receipt:cancel` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/misc-receipt/export-excel` | 导出杂项入库单 Excel | `mes:wm:misc-receipt:export` | MesWmMiscReceiptPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 14. MesWmMiscReceiptLineController（管理后台 - MES 杂项入库单行，前缀 `/mes/wm/misc-receipt-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/misc-receipt-line/create` | 创建杂项入库单行 | `mes:wm:misc-receipt:create` | MesWmMiscReceiptLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/misc-receipt-line/update` | 修改杂项入库单行 | `mes:wm:misc-receipt:update` | MesWmMiscReceiptLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/misc-receipt-line/delete` | 删除杂项入库单行 | `mes:wm:misc-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/misc-receipt-line/get` | 获得杂项入库单行 | `mes:wm:misc-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmMiscReceiptLineRespVO> |
| GET | `/mes/wm/misc-receipt-line/list-by-receipt-id` | 获得杂项入库单行列表 | `mes:wm:misc-receipt:query` | Query 参数 receiptId（Long） | CommonResult<List<MesWmMiscReceiptLineRespVO>> |
| GET | `/mes/wm/misc-receipt-line/page` | 获得杂项入库单行分页 | `mes:wm:misc-receipt:query` | MesWmMiscReceiptLinePageReqVO | CommonResult<PageResult<MesWmMiscReceiptLineRespVO>> |

## 15. MesWmOutsourceIssueController（管理后台 - MES 外协发料单，前缀 `/mes/wm/outsource-issue`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/outsource-issue/create` | 创建外协发料单 | `mes:wm-outsource-issue:create` | MesWmOutsourceIssueSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/outsource-issue/update` | 修改外协发料单 | `mes:wm-outsource-issue:update` | MesWmOutsourceIssueSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/outsource-issue/delete` | 删除外协发料单 | `mes:wm-outsource-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-issue/get` | 获得外协发料单 | `mes:wm-outsource-issue:query` | Query 参数 id（Long） | CommonResult<MesWmOutsourceIssueRespVO> |
| GET | `/mes/wm/outsource-issue/page` | 获得外协发料单分页 | `mes:wm-outsource-issue:query` | MesWmOutsourceIssuePageReqVO | CommonResult<PageResult<MesWmOutsourceIssueRespVO>> |
| GET | `/mes/wm/outsource-issue/export-excel` | 导出外协发料单 Excel | `mes:wm-outsource-issue:export` | MesWmOutsourceIssuePageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/outsource-issue/submit` | 提交到待拣货 | `mes:wm-outsource-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/outsource-issue/stock` | 执行拣货 | `mes:wm-outsource-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/outsource-issue/finish` | 完成外协发料出库 | `mes:wm-outsource-issue:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/outsource-issue/cancel` | 取消外协发料单 | `mes:wm-outsource-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-issue/check-quantity` | 校验外协发料单数量 | `mes:wm-outsource-issue:query` | Query 参数 id（Long） | CommonResult<Boolean> |

## 16. MesWmOutsourceIssueDetailController（管理后台 - MES 外协发料单明细，前缀 `/mes/wm/outsource-issue-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/outsource-issue-detail/create` | 创建外协发料单明细 | `mes:wm-outsource-issue:create` | MesWmOutsourceIssueDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/outsource-issue-detail/update` | 修改外协发料单明细 | `mes:wm-outsource-issue:update` | MesWmOutsourceIssueDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/outsource-issue-detail/delete` | 删除外协发料单明细 | `mes:wm-outsource-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-issue-detail/get` | 获得外协发料单明细 | `mes:wm-outsource-issue:query` | Query 参数 id（Long） | CommonResult<MesWmOutsourceIssueDetailRespVO> |
| GET | `/mes/wm/outsource-issue-detail/list-by-line` | 获得外协发料单明细列表（按行ID） | `mes:wm-outsource-issue:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmOutsourceIssueDetailRespVO>> |

## 17. MesWmOutsourceIssueLineController（管理后台 - MES 外协发料单行，前缀 `/mes/wm/outsource-issue-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/outsource-issue-line/create` | 创建外协发料单行 | `mes:wm-outsource-issue:create` | MesWmOutsourceIssueLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/outsource-issue-line/update` | 修改外协发料单行 | `mes:wm-outsource-issue:update` | MesWmOutsourceIssueLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/outsource-issue-line/delete` | 删除外协发料单行 | `mes:wm-outsource-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-issue-line/get` | 获得外协发料单行 | `mes:wm-outsource-issue:query` | Query 参数 id（Long） | CommonResult<MesWmOutsourceIssueLineRespVO> |
| GET | `/mes/wm/outsource-issue-line/page` | 获得外协发料单行分页 | `mes:wm-outsource-issue:query` | MesWmOutsourceIssueLinePageReqVO | CommonResult<PageResult<MesWmOutsourceIssueLineRespVO>> |
| GET | `/mes/wm/outsource-issue-line/list-by-issue-id` | 获得外协发料单行列表 | `mes:wm-outsource-issue:query` | Query 参数 issueId（Long） | CommonResult<List<MesWmOutsourceIssueLineRespVO>> |

## 18. MesWmOutsourceReceiptController（管理后台 - MES 外协入库单，前缀 `/mes/wm/outsource-receipt`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/outsource-receipt/create` | 创建外协入库单 | `mes:wm-outsource-receipt:create` | MesWmOutsourceReceiptSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/outsource-receipt/update` | 修改外协入库单 | `mes:wm-outsource-receipt:update` | MesWmOutsourceReceiptSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/outsource-receipt/delete` | 删除外协入库单 | `mes:wm-outsource-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-receipt/get` | 获得外协入库单 | `mes:wm-outsource-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmOutsourceReceiptRespVO> |
| GET | `/mes/wm/outsource-receipt/page` | 获得外协入库单分页 | `mes:wm-outsource-receipt:query` | MesWmOutsourceReceiptPageReqVO | CommonResult<PageResult<MesWmOutsourceReceiptRespVO>> |
| GET | `/mes/wm/outsource-receipt/export-excel` | 导出外协入库单 Excel | `mes:wm-outsource-receipt:export` | MesWmOutsourceReceiptPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/outsource-receipt/submit` | 提交外协入库单 | `mes:wm-outsource-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/outsource-receipt/stock` | 执行上架 | `mes:wm-outsource-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/outsource-receipt/finish` | 完成入库 | `mes:wm-outsource-receipt:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/outsource-receipt/cancel` | 取消外协入库单 | `mes:wm-outsource-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 19. MesWmOutsourceReceiptDetailController（管理后台 - MES 外协入库明细，前缀 `/mes/wm/outsource-receipt-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/outsource-receipt-detail/create` | 创建外协入库明细 | `mes:wm-outsource-receipt:create` | MesWmOutsourceReceiptDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/outsource-receipt-detail/update` | 修改外协入库明细 | `mes:wm-outsource-receipt:update` | MesWmOutsourceReceiptDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/outsource-receipt-detail/delete` | 删除外协入库明细 | `mes:wm-outsource-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-receipt-detail/get` | 获得外协入库明细 | `mes:wm-outsource-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmOutsourceReceiptDetailRespVO> |
| GET | `/mes/wm/outsource-receipt-detail/list-by-line` | 获得外协入库明细列表（按行编号） | `mes:wm-outsource-receipt:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmOutsourceReceiptDetailRespVO>> |

## 20. MesWmOutsourceReceiptLineController（管理后台 - MES 外协入库单行，前缀 `/mes/wm/outsource-receipt-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/outsource-receipt-line/create` | 创建外协入库单行 | `mes:wm-outsource-receipt:create` | MesWmOutsourceReceiptLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/outsource-receipt-line/update` | 修改外协入库单行 | `mes:wm-outsource-receipt:update` | MesWmOutsourceReceiptLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/outsource-receipt-line/delete` | 删除外协入库单行 | `mes:wm-outsource-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/outsource-receipt-line/get` | 获得外协入库单行 | `mes:wm-outsource-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmOutsourceReceiptLineRespVO> |
| GET | `/mes/wm/outsource-receipt-line/page` | 获得外协入库单行分页 | `mes:wm-outsource-receipt:query` | MesWmOutsourceReceiptLinePageReqVO | CommonResult<PageResult<MesWmOutsourceReceiptLineRespVO>> |

## 21. MesWmPackageController（管理后台 - MES 装箱单，前缀 `/mes/wm/package`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/package/create` | 创建装箱单 | `mes:wm-package:create` | MesWmPackageSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/package/update` | 修改装箱单 | `mes:wm-package:update` | MesWmPackageSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/package/delete` | 删除装箱单 | `mes:wm-package:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/package/get` | 获得装箱单 | `mes:wm-package:query` | Query 参数 id（Long） | CommonResult<MesWmPackageRespVO> |
| GET | `/mes/wm/package/page` | 获得装箱单分页 | `mes:wm-package:query` | MesWmPackagePageReqVO | CommonResult<PageResult<MesWmPackageRespVO>> |
| PUT | `/mes/wm/package/finish` | 完成装箱单 | `mes:wm-package:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/package/add-child-package` | 添加子箱 | `mes:wm-package:update` | Query 参数 parentId（Long）, Query 参数 childId（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/package/remove-child-package` | 移除子箱 | `mes:wm-package:update` | Query 参数 childId（Long） | CommonResult<Boolean> |

## 22. MesWmPackageLineController（管理后台 - MES 装箱明细，前缀 `/mes/wm/package-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/package-line/create` | 创建装箱明细 | `mes:wm-package:create` | MesWmPackageLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/package-line/update` | 修改装箱明细 | `mes:wm-package:update` | MesWmPackageLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/package-line/delete` | 删除装箱明细 | `mes:wm-package:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/package-line/get` | 获得装箱明细 | `mes:wm-package:query` | Query 参数 id（Long） | CommonResult<MesWmPackageLineRespVO> |
| GET | `/mes/wm/package-line/page` | 获得装箱明细分页 | `mes:wm-package:query` | MesWmPackageLinePageReqVO | CommonResult<PageResult<MesWmPackageLineRespVO>> |

## 23. MesWmProductIssueController（管理后台 - MES 领料出库单，前缀 `/mes/wm/product-issue`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-issue/create` | 创建领料出库单 | `mes:wm-product-issue:create` | MesWmProductIssueSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-issue/update` | 修改领料出库单 | `mes:wm-product-issue:update` | MesWmProductIssueSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-issue/delete` | 删除领料出库单 | `mes:wm-product-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-issue/get` | 获得领料出库单 | `mes:wm-product-issue:query` | Query 参数 id（Long） | CommonResult<MesWmProductIssueRespVO> |
| GET | `/mes/wm/product-issue/page` | 获得领料出库单分页 | `mes:wm-product-issue:query` | MesWmProductIssuePageReqVO | CommonResult<PageResult<MesWmProductIssueRespVO>> |
| GET | `/mes/wm/product-issue/export-excel` | 导出领料出库单 Excel | `mes:wm-product-issue:export` | MesWmProductIssuePageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/product-issue/finish` | 完成领料出库单 | `mes:wm-product-issue:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-issue/submit` | 提交领料出库单 | `mes:wm-product-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-issue/stock` | 执行拣货 | `mes:wm-product-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-issue/cancel` | 取消领料出库单 | `mes:wm-product-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-issue/check-quantity` | 校验领料出库单数量 | `mes:wm-product-issue:query` | Query 参数 id（Long） | CommonResult<Boolean> |

## 24. MesWmProductIssueDetailController（管理后台 - MES 领料出库明细，前缀 `/mes/wm/product-issue-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-issue-detail/create` | 创建领料出库明细 | `mes:wm-product-issue:create` | MesWmProductIssueDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-issue-detail/update` | 修改领料出库明细 | `mes:wm-product-issue:update` | MesWmProductIssueDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-issue-detail/delete` | 删除领料出库明细 | `mes:wm-product-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-issue-detail/get` | 获得领料出库明细 | `mes:wm-product-issue:query` | Query 参数 id（Long） | CommonResult<MesWmProductIssueDetailRespVO> |
| GET | `/mes/wm/product-issue-detail/list-by-line` | 获得领料出库明细列表（按行编号） | `mes:wm-product-issue:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmProductIssueDetailRespVO>> |

## 25. MesWmProductIssueLineController（管理后台 - MES 领料出库单行，前缀 `/mes/wm/product-issue-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-issue-line/create` | 创建领料出库单行 | `mes:wm-product-issue:create` | MesWmProductIssueLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-issue-line/update` | 修改领料出库单行 | `mes:wm-product-issue:update` | MesWmProductIssueLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-issue-line/delete` | 删除领料出库单行 | `mes:wm-product-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-issue-line/get` | 获得领料出库单行 | `mes:wm-product-issue:query` | Query 参数 id（Long） | CommonResult<MesWmProductIssueLineRespVO> |
| GET | `/mes/wm/product-issue-line/page` | 获得领料出库单行分页 | `mes:wm-product-issue:query` | MesWmProductIssueLinePageReqVO | CommonResult<PageResult<MesWmProductIssueLineRespVO>> |
| GET | `/mes/wm/product-issue-line/list-by-issue` | 获得领料出库单行列表（按领料单编号） | `mes:wm-product-issue:query` | Query 参数 issueId（Long） | CommonResult<List<MesWmProductIssueLineRespVO>> |

## 26. MesWmProductProduceLineController（管理后台 - MES 生产入库单行，前缀 `/mes/wm/product-produce-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/wm/product-produce-line/page` | 获得生产入库单行分页 | `mes:wm-product-produce:query` | MesWmProductProduceLinePageReqVO | CommonResult<PageResult<MesWmProductProduceLineRespVO>> |

## 27. MesWmProductReceiptController（管理后台 - MES 产品收货单，前缀 `/mes/wm/product-receipt`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-receipt/create` | 创建产品收货单 | `mes:wm-product-receipt:create` | MesWmProductReceiptSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-receipt/update` | 修改产品收货单 | `mes:wm-product-receipt:update` | MesWmProductReceiptSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-receipt/delete` | 删除产品收货单 | `mes:wm-product-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-receipt/get` | 获得产品收货单 | `mes:wm-product-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmProductReceiptRespVO> |
| GET | `/mes/wm/product-receipt/page` | 获得产品收货单分页 | `mes:wm-product-receipt:query` | MesWmProductReceiptPageReqVO | CommonResult<PageResult<MesWmProductReceiptRespVO>> |
| GET | `/mes/wm/product-receipt/export-excel` | 导出产品收货单 Excel | `mes:wm-product-receipt:export` | MesWmProductReceiptPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/product-receipt/submit` | 提交产品收货单 | `mes:wm-product-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-receipt/stock` | 执行上架 | `mes:wm-product-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-receipt/finish` | 执行入库 | `mes:wm-product-receipt:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-receipt/cancel` | 取消产品收货单 | `mes:wm-product-receipt:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-receipt/check-quantity` | 校验产品收货单明细数量 | `mes:wm-product-receipt:query` | Query 参数 id（Long） | CommonResult<Boolean> |

## 28. MesWmProductReceiptDetailController（管理后台 - MES 产品收货单明细，前缀 `/mes/wm/product-receipt-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-receipt-detail/create` | 创建产品收货单明细 | `mes:wm-product-receipt:create` | MesWmProductReceiptDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-receipt-detail/update` | 修改产品收货单明细 | `mes:wm-product-receipt:update` | MesWmProductReceiptDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-receipt-detail/delete` | 删除产品收货单明细 | `mes:wm-product-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-receipt-detail/get` | 获得产品收货单明细 | `mes:wm-product-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmProductReceiptDetailRespVO> |
| GET | `/mes/wm/product-receipt-detail/list-by-line` | 获得产品收货单明细列表（按行编号） | `mes:wm-product-receipt:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmProductReceiptDetailRespVO>> |

## 29. MesWmProductReceiptLineController（管理后台 - MES 产品收货单行，前缀 `/mes/wm/product-receipt-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-receipt-line/create` | 创建产品收货单行 | `mes:wm-product-receipt:create` | MesWmProductReceiptLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-receipt-line/update` | 修改产品收货单行 | `mes:wm-product-receipt:update` | MesWmProductReceiptLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-receipt-line/delete` | 删除产品收货单行 | `mes:wm-product-receipt:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-receipt-line/get` | 获得产品收货单行 | `mes:wm-product-receipt:query` | Query 参数 id（Long） | CommonResult<MesWmProductReceiptLineRespVO> |
| GET | `/mes/wm/product-receipt-line/page` | 获得产品收货单行分页 | `mes:wm-product-receipt:query` | MesWmProductReceiptLinePageReqVO | CommonResult<PageResult<MesWmProductReceiptLineRespVO>> |

## 30. MesWmProductSalesController（管理后台 - MES 销售出库单，前缀 `/mes/wm/product-sales`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-sales/create` | 创建销售出库单 | `mes:wm-product-sales:create` | MesWmProductSalesSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-sales/update` | 修改销售出库单 | `mes:wm-product-sales:update` | MesWmProductSalesSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-sales/delete` | 删除销售出库单 | `mes:wm-product-sales:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-sales/get` | 获得销售出库单 | `mes:wm-product-sales:query` | Query 参数 id（Long） | CommonResult<MesWmProductSalesRespVO> |
| GET | `/mes/wm/product-sales/page` | 获得销售出库单分页 | `mes:wm-product-sales:query` | MesWmProductSalesPageReqVO | CommonResult<PageResult<MesWmProductSalesRespVO>> |
| GET | `/mes/wm/product-sales/export-excel` | 导出销售出库单 Excel | `mes:wm-product-sales:export` | MesWmProductSalesPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/product-sales/submit` | 提交销售出库单 | `mes:wm-product-sales:submit` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-sales/check-quantity` | 校验销售出库单数量 | `mes:wm-product-sales:query` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-sales/stock` | 执行拣货 | `mes:wm-product-sales:stock` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-sales/shipping` | 填写运单 | `mes:wm-product-sales:shipping` | MesWmProductSalesShippingReqVO | CommonResult<Boolean> |
| PUT | `/mes/wm/product-sales/finish` | 执行出库 | `mes:wm-product-sales:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/product-sales/cancel` | 取消销售出库单 | `mes:wm-product-sales:cancel` | Query 参数 id（Long） | CommonResult<Boolean> |

## 31. MesWmProductSalesDetailController（管理后台 - MES 销售出库明细，前缀 `/mes/wm/product-sales-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-sales-detail/create` | 创建销售出库明细 | `mes:wm-product-sales:create` | MesWmProductSalesDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-sales-detail/update` | 修改销售出库明细 | `mes:wm-product-sales:update` | MesWmProductSalesDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-sales-detail/delete` | 删除销售出库明细 | `mes:wm-product-sales:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-sales-detail/get` | 获得销售出库明细 | `mes:wm-product-sales:query` | Query 参数 id（Long） | CommonResult<MesWmProductSalesDetailRespVO> |
| GET | `/mes/wm/product-sales-detail/list-by-line` | 获得销售出库明细列表（按行编号） | `mes:wm-product-sales:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmProductSalesDetailRespVO>> |

## 32. MesWmProductSalesLineController（管理后台 - MES 销售出库单行，前缀 `/mes/wm/product-sales-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/product-sales-line/create` | 创建销售出库单行 | `mes:wm-product-sales:create` | MesWmProductSalesLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/product-sales-line/update` | 修改销售出库单行 | `mes:wm-product-sales:update` | MesWmProductSalesLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/product-sales-line/delete` | 删除销售出库单行 | `mes:wm-product-sales:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/product-sales-line/get` | 获得销售出库单行 | `mes:wm-product-sales:query` | Query 参数 id（Long） | CommonResult<MesWmProductSalesLineRespVO> |
| GET | `/mes/wm/product-sales-line/page` | 获得销售出库单行分页 | `mes:wm-product-sales:query` | MesWmProductSalesLinePageReqVO | CommonResult<PageResult<MesWmProductSalesLineRespVO>> |

## 33. MesWmReturnIssueController（管理后台 - MES 生产退料单，前缀 `/mes/wm/return-issue`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-issue/create` | 创建生产退料单 | `mes:wm-return-issue:create` | MesWmReturnIssueSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-issue/update` | 修改生产退料单 | `mes:wm-return-issue:update` | MesWmReturnIssueSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-issue/delete` | 删除生产退料单 | `mes:wm-return-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-issue/get` | 获得生产退料单 | `mes:wm-return-issue:query` | Query 参数 id（Long） | CommonResult<MesWmReturnIssueRespVO> |
| GET | `/mes/wm/return-issue/page` | 获得生产退料单分页 | `mes:wm-return-issue:query` | MesWmReturnIssuePageReqVO | CommonResult<PageResult<MesWmReturnIssueRespVO>> |
| GET | `/mes/wm/return-issue/export-excel` | 导出生产退料单 Excel | `mes:wm-return-issue:export` | MesWmReturnIssuePageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/return-issue/finish` | 完成生产退料单 | `mes:wm-return-issue:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-issue/submit` | 提交生产退料单（草稿 → 待检验/待上架） | `mes:wm-return-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-issue/stock` | 入库上架 | `mes:wm-return-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-issue/cancel` | 取消生产退料单 | `mes:wm-return-issue:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 34. MesWmReturnIssueDetailController（管理后台 - MES 生产退料明细，前缀 `/mes/wm/return-issue-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-issue-detail/create` | 创建生产退料明细 | `mes:wm-return-issue:create` | MesWmReturnIssueDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-issue-detail/update` | 修改生产退料明细 | `mes:wm-return-issue:update` | MesWmReturnIssueDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-issue-detail/delete` | 删除生产退料明细 | `mes:wm-return-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-issue-detail/get` | 获得生产退料明细 | `mes:wm-return-issue:query` | Query 参数 id（Long） | CommonResult<MesWmReturnIssueDetailRespVO> |
| GET | `/mes/wm/return-issue-detail/list-by-line` | 获得生产退料明细列表（按行编号） | `mes:wm-return-issue:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmReturnIssueDetailRespVO>> |

## 35. MesWmReturnIssueLineController（管理后台 - MES 生产退料单行，前缀 `/mes/wm/return-issue-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-issue-line/create` | 创建生产退料单行 | `mes:wm-return-issue:create` | MesWmReturnIssueLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-issue-line/update` | 修改生产退料单行 | `mes:wm-return-issue:update` | MesWmReturnIssueLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-issue-line/delete` | 删除生产退料单行 | `mes:wm-return-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-issue-line/get` | 获得生产退料单行 | `mes:wm-return-issue:query` | Query 参数 id（Long） | CommonResult<MesWmReturnIssueLineRespVO> |
| GET | `/mes/wm/return-issue-line/page` | 获得生产退料单行分页 | `mes:wm-return-issue:query` | MesWmReturnIssueLinePageReqVO | CommonResult<PageResult<MesWmReturnIssueLineRespVO>> |
| GET | `/mes/wm/return-issue-line/list-by-issue` | 获得生产退料单行列表（按退料单编号） | `mes:wm-return-issue:query` | Query 参数 issueId（Long） | CommonResult<List<MesWmReturnIssueLineRespVO>> |

## 36. MesWmReturnSalesController（管理后台 - MES 销售退货单，前缀 `/mes/wm/return-sales`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-sales/create` | 创建销售退货单 | `mes:wm-return-sales:create` | MesWmReturnSalesSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-sales/update` | 修改销售退货单 | `mes:wm-return-sales:update` | MesWmReturnSalesSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-sales/delete` | 删除销售退货单 | `mes:wm-return-sales:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-sales/get` | 获得销售退货单 | `mes:wm-return-sales:query` | Query 参数 id（Long） | CommonResult<MesWmReturnSalesRespVO> |
| GET | `/mes/wm/return-sales/page` | 获得销售退货单分页 | `mes:wm-return-sales:query` | MesWmReturnSalesPageReqVO | CommonResult<PageResult<MesWmReturnSalesRespVO>> |
| GET | `/mes/wm/return-sales/export-excel` | 导出销售退货单 Excel | `mes:wm-return-sales:export` | MesWmReturnSalesPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/return-sales/submit` | 提交销售退货单 | `mes:wm-return-sales:submit` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-sales/finish` | 执行退货 | `mes:wm-return-sales:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-sales/stock` | 执行上架 | `mes:wm-return-sales:stock` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-sales/cancel` | 取消销售退货单 | `mes:wm-return-sales:cancel` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-sales/check-quantity` | 校验销售退货单数量 | `mes:wm-return-sales:query` | Query 参数 id（Long） | CommonResult<Boolean> |

## 37. MesWmReturnSalesDetailController（管理后台 - MES 销售退货明细，前缀 `/mes/wm/return-sales-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-sales-detail/create` | 创建销售退货明细 | `mes:wm-return-sales:create` | MesWmReturnSalesDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-sales-detail/update` | 修改销售退货明细 | `mes:wm-return-sales:update` | MesWmReturnSalesDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-sales-detail/delete` | 删除销售退货明细 | `mes:wm-return-sales:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-sales-detail/get` | 获得销售退货明细 | `mes:wm-return-sales:query` | Query 参数 id（Long） | CommonResult<MesWmReturnSalesDetailRespVO> |
| GET | `/mes/wm/return-sales-detail/list-by-line` | 获得销售退货明细列表（按行编号） | `mes:wm-return-sales:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmReturnSalesDetailRespVO>> |

## 38. MesWmReturnSalesLineController（管理后台 - MES 销售退货单行，前缀 `/mes/wm/return-sales-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-sales-line/create` | 创建销售退货单行 | `mes:wm-return-sales:create` | MesWmReturnSalesLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-sales-line/update` | 修改销售退货单行 | `mes:wm-return-sales:update` | MesWmReturnSalesLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-sales-line/delete` | 删除销售退货单行 | `mes:wm-return-sales:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-sales-line/get` | 获得销售退货单行 | `mes:wm-return-sales:query` | Query 参数 id（Long） | CommonResult<MesWmReturnSalesLineRespVO> |
| GET | `/mes/wm/return-sales-line/page` | 获得销售退货单行分页 | `mes:wm-return-sales:query` | MesWmReturnSalesLinePageReqVO | CommonResult<PageResult<MesWmReturnSalesLineRespVO>> |
| GET | `/mes/wm/return-sales-line/list-by-return-sales` | 获得销售退货单行列表（按退货单编号） | `mes:wm-return-sales:query` | Query 参数 returnId（Long） | CommonResult<List<MesWmReturnSalesLineRespVO>> |

## 39. MesWmReturnVendorController（管理后台 - MES 供应商退货单，前缀 `/mes/wm/return-vendor`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-vendor/create` | 创建供应商退货单 | `mes:wm-return-vendor:create` | MesWmReturnVendorSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-vendor/update` | 修改供应商退货单 | `mes:wm-return-vendor:update` | MesWmReturnVendorSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-vendor/delete` | 删除供应商退货单 | `mes:wm-return-vendor:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-vendor/get` | 获得供应商退货单 | `mes:wm-return-vendor:query` | Query 参数 id（Long） | CommonResult<MesWmReturnVendorRespVO> |
| GET | `/mes/wm/return-vendor/page` | 获得供应商退货单分页 | `mes:wm-return-vendor:query` | MesWmReturnVendorPageReqVO | CommonResult<PageResult<MesWmReturnVendorRespVO>> |
| GET | `/mes/wm/return-vendor/export-excel` | 导出供应商退货单 Excel | `mes:wm-return-vendor:export` | MesWmReturnVendorPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/return-vendor/submit` | 提交供应商退货单 | `mes:wm-return-vendor:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-vendor/stock` | 执行拣货 | `mes:wm-return-vendor:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-vendor/finish` | 完成供应商退货单 | `mes:wm-return-vendor:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/return-vendor/cancel` | 取消供应商退货单 | `mes:wm-return-vendor:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-vendor/check-quantity` | 校验供应商退货单数量 | `mes:wm-return-vendor:query` | Query 参数 id（Long） | CommonResult<Boolean> |

## 40. MesWmReturnVendorDetailController（管理后台 - MES 供应商退货明细，前缀 `/mes/wm/return-vendor-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-vendor-detail/create` | 创建供应商退货明细 | `mes:wm-return-vendor:create` | MesWmReturnVendorDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-vendor-detail/update` | 修改供应商退货明细 | `mes:wm-return-vendor:update` | MesWmReturnVendorDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-vendor-detail/delete` | 删除供应商退货明细 | `mes:wm-return-vendor:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-vendor-detail/get` | 获得供应商退货明细 | `mes:wm-return-vendor:query` | Query 参数 id（Long） | CommonResult<MesWmReturnVendorDetailRespVO> |
| GET | `/mes/wm/return-vendor-detail/list-by-line` | 获得供应商退货明细列表（按行编号） | `mes:wm-return-vendor:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmReturnVendorDetailRespVO>> |

## 41. MesWmReturnVendorLineController（管理后台 - MES 供应商退货单行，前缀 `/mes/wm/return-vendor-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/return-vendor-line/create` | 创建供应商退货单行 | `mes:wm-return-vendor:create` | MesWmReturnVendorLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/return-vendor-line/update` | 修改供应商退货单行 | `mes:wm-return-vendor:update` | MesWmReturnVendorLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/return-vendor-line/delete` | 删除供应商退货单行 | `mes:wm-return-vendor:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/return-vendor-line/get` | 获得供应商退货单行 | `mes:wm-return-vendor:query` | Query 参数 id（Long） | CommonResult<MesWmReturnVendorLineRespVO> |
| GET | `/mes/wm/return-vendor-line/page` | 获得供应商退货单行分页 | `mes:wm-return-vendor:query` | MesWmReturnVendorLinePageReqVO | CommonResult<PageResult<MesWmReturnVendorLineRespVO>> |
| GET | `/mes/wm/return-vendor-line/list-by-return-vendor` | 获得供应商退货单行列表（按退货单编号） | `mes:wm-return-vendor:query` | Query 参数 returnId（Long） | CommonResult<List<MesWmReturnVendorLineRespVO>> |

## 42. MesWmSalesNoticeController（管理后台 - MES 发货通知单，前缀 `/mes/wm/sales-notice`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/sales-notice/create` | 创建发货通知单 | `mes:wm-sales-notice:create` | MesWmSalesNoticeSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/sales-notice/update` | 修改发货通知单 | `mes:wm-sales-notice:update` | MesWmSalesNoticeSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/sales-notice/delete` | 删除发货通知单 | `mes:wm-sales-notice:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/sales-notice/get` | 获得发货通知单 | `mes:wm-sales-notice:query` | Query 参数 id（Long） | CommonResult<MesWmSalesNoticeRespVO> |
| GET | `/mes/wm/sales-notice/page` | 获得发货通知单分页 | `mes:wm-sales-notice:query` | MesWmSalesNoticePageReqVO | CommonResult<PageResult<MesWmSalesNoticeRespVO>> |
| GET | `/mes/wm/sales-notice/export-excel` | 导出发货通知单 Excel | `mes:wm-sales-notice:export` | MesWmSalesNoticePageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/sales-notice/submit` | 提交发货通知单 | `mes:wm-sales-notice:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 43. MesWmSalesNoticeLineController（管理后台 - MES 发货通知单行，前缀 `/mes/wm/sales-notice-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/sales-notice-line/create` | 创建发货通知单行 | `mes:wm-sales-notice:create` | MesWmSalesNoticeLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/sales-notice-line/update` | 修改发货通知单行 | `mes:wm-sales-notice:update` | MesWmSalesNoticeLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/sales-notice-line/delete` | 删除发货通知单行 | `mes:wm-sales-notice:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/sales-notice-line/get` | 获得发货通知单行 | `mes:wm-sales-notice:query` | Query 参数 id（Long） | CommonResult<MesWmSalesNoticeLineRespVO> |
| GET | `/mes/wm/sales-notice-line/page` | 获得发货通知单行分页 | `mes:wm-sales-notice:query` | MesWmSalesNoticeLinePageReqVO | CommonResult<PageResult<MesWmSalesNoticeLineRespVO>> |

## 44. MesWmSnController（管理后台 - MES SN 码，前缀 `/mes/wm/sn`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/sn/generate` | 生成 SN 码 | `mes:wm-sn:create` | MesWmSnGenerateReqVO | CommonResult<Boolean> |
| GET | `/mes/wm/sn/group-page` | 获得 SN 码分组分页 | `mes:wm-sn:query` | MesWmSnPageReqVO | CommonResult<PageResult<MesWmSnGroupRespVO>> |
| GET | `/mes/wm/sn/list-by-uuid` | 获得批次 SN 码明细列表 | `mes:wm-sn:query` | Query 参数 uuid（@NotBlank(message） | CommonResult<List<MesWmSnRespVO>> |
| DELETE | `/mes/wm/sn/delete-batch` | 批量删除 SN 码（按批次 UUID） | `mes:wm-sn:delete` | Query 参数 uuid（@NotBlank(message） | CommonResult<Boolean> |
| GET | `/mes/wm/sn/group-export-excel` | 导出 SN 码分组 Excel | `mes:wm-sn:export` | MesWmSnPageReqVO, HttpServletResponse | Excel 文件流（void） |
| GET | `/mes/wm/sn/export-excel` | 导出批次 SN 码明细 Excel | `mes:wm-sn:export` | Query 参数 uuid（String）, HttpServletResponse | Excel 文件流（void） |

## 45. MesWmStockTakingPlanController（管理后台 - MES 盘点方案，前缀 `/mes/wm/stocktaking-plan`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/stocktaking-plan/create` | 创建盘点方案 | `mes:wm-stock-taking-plan:create` | MesWmStockTakingPlanSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/stocktaking-plan/update` | 修改盘点方案 | `mes:wm-stock-taking-plan:update` | MesWmStockTakingPlanSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/wm/stocktaking-plan/update-status` | 更新盘点方案状态 | `mes:wm-stock-taking-plan:update` | Query 参数 id（Long）, Query 参数 status（Integer） | CommonResult<Boolean> |
| DELETE | `/mes/wm/stocktaking-plan/delete` | 删除盘点方案 | `mes:wm-stock-taking-plan:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/stocktaking-plan/get` | 获得盘点方案 | `mes:wm-stock-taking-plan:query` | Query 参数 id（Long） | CommonResult<MesWmStockTakingPlanRespVO> |
| GET | `/mes/wm/stocktaking-plan/page` | 获得盘点方案分页 | `mes:wm-stock-taking-plan:query` | MesWmStockTakingPlanPageReqVO | CommonResult<PageResult<MesWmStockTakingPlanRespVO>> |
| GET | `/mes/wm/stocktaking-plan/export-excel` | 导出盘点方案 Excel | `mes:wm-stock-taking-plan:export` | MesWmStockTakingPlanPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 46. MesWmStockTakingPlanParamController（管理后台 - MES 盘点方案参数，前缀 `/mes/wm/stocktaking-plan-param`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/stocktaking-plan-param/create` | 创建盘点方案参数 | `mes:wm-stock-taking-plan:update` | MesWmStockTakingPlanParamSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/stocktaking-plan-param/update` | 修改盘点方案参数 | `mes:wm-stock-taking-plan:update` | MesWmStockTakingPlanParamSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/stocktaking-plan-param/delete` | 删除盘点方案参数 | `mes:wm-stock-taking-plan:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/stocktaking-plan-param/get` | 获得盘点方案参数 | `mes:wm-stock-taking-plan:query` | Query 参数 id（Long） | CommonResult<MesWmStockTakingPlanParamRespVO> |
| GET | `/mes/wm/stocktaking-plan-param/page` | 获得盘点方案参数分页 | `mes:wm-stock-taking-plan:query` | MesWmStockTakingPlanParamPageReqVO | CommonResult<PageResult<MesWmStockTakingPlanParamRespVO>> |

## 47. MesWmStockTakingTaskController（管理后台 - MES 盘点任务，前缀 `/mes/wm/stocktaking-task`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/stocktaking-task/create` | 创建盘点任务 | `mes:wm-stock-taking-task:create` | MesWmStockTakingTaskSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/stocktaking-task/update` | 修改盘点任务 | `mes:wm-stock-taking-task:update` | MesWmStockTakingTaskSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/stocktaking-task/delete` | 删除盘点任务 | `mes:wm-stock-taking-task:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/stocktaking-task/submit` | 提交盘点任务 | `mes:wm-stock-taking-task:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/stocktaking-task/get` | 获得盘点任务 | `mes:wm-stock-taking-task:query` | Query 参数 id（Long） | CommonResult<MesWmStockTakingTaskRespVO> |
| GET | `/mes/wm/stocktaking-task/page` | 获得盘点任务分页 | `mes:wm-stock-taking-task:query` | MesWmStockTakingTaskPageReqVO | CommonResult<PageResult<MesWmStockTakingTaskRespVO>> |
| GET | `/mes/wm/stocktaking-task/export-excel` | 导出盘点任务 Excel | `mes:wm-stock-taking-task:export` | MesWmStockTakingTaskPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/stocktaking-task/finish` | 完成盘点任务 | `mes:wm-stock-taking-task:finish` | MesWmStockTakingTaskFinishReqVO | CommonResult<Boolean> |
| PUT | `/mes/wm/stocktaking-task/cancel` | 取消盘点任务 | `mes:wm-stock-taking-task:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 48. MesWmStockTakingTaskLineController（管理后台 - MES 盘点任务行，前缀 `/mes/wm/stocktaking-task-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/wm/stocktaking-task-line/get` | 获得盘点任务行 | `mes:wm-stock-taking-task:query` | Query 参数 id（Long） | CommonResult<MesWmStockTakingTaskLineRespVO> |
| GET | `/mes/wm/stocktaking-task-line/page` | 获得盘点任务行分页 | `mes:wm-stock-taking-task:query` | MesWmStockTakingTaskLinePageReqVO | CommonResult<PageResult<MesWmStockTakingTaskLineRespVO>> |
| POST | `/mes/wm/stocktaking-task-line/create` | 创建盘点任务行 | `mes:wm-stock-taking-task:update` | MesWmStockTakingTaskLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/stocktaking-task-line/update` | 更新盘点任务行 | `mes:wm-stock-taking-task:update` | MesWmStockTakingTaskLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/stocktaking-task-line/delete` | 删除盘点任务行 | `mes:wm-stock-taking-task:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/stocktaking-task-line/simple-list` | 获得盘点任务行精简列表 | `mes:wm-stock-taking-task:query` | Query 参数 taskId（Long） | CommonResult<List<MesWmStockTakingTaskLineRespVO>> |

## 49. MesWmStockTakingTaskResultController（管理后台 - MES 盘点结果，前缀 `/mes/wm/stocktaking-task-result`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/wm/stocktaking-task-result/get` | 获得盘点结果 | `mes:wm-stock-taking-task:query` | Query 参数 id（Long） | CommonResult<MesWmStockTakingTaskResultRespVO> |
| GET | `/mes/wm/stocktaking-task-result/page` | 获得盘点结果分页 | `mes:wm-stock-taking-task:query` | MesWmStockTakingTaskResultPageReqVO | CommonResult<PageResult<MesWmStockTakingTaskResultRespVO>> |
| POST | `/mes/wm/stocktaking-task-result/create` | 创建盘点结果 | `mes:wm-stock-taking-task:update` | MesWmStockTakingTaskResultSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/stocktaking-task-result/update` | 更新盘点结果 | `mes:wm-stock-taking-task:update` | MesWmStockTakingTaskResultSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/stocktaking-task-result/delete` | 删除盘点结果 | `mes:wm-stock-taking-task:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 50. MesWmTransferController（管理后台 - MES 转移单，前缀 `/mes/wm/transfer`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/transfer/create` | 创建转移单 | `mes:wm-transfer:create` | MesWmTransferSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/transfer/update` | 修改转移单 | `mes:wm-transfer:update` | MesWmTransferSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/transfer/delete` | 删除转移单 | `mes:wm-transfer:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/transfer/get` | 获得转移单 | `mes:wm-transfer:query` | Query 参数 id（Long） | CommonResult<MesWmTransferRespVO> |
| GET | `/mes/wm/transfer/page` | 获得转移单分页 | `mes:wm-transfer:query` | MesWmTransferPageReqVO | CommonResult<PageResult<MesWmTransferRespVO>> |
| GET | `/mes/wm/transfer/export-excel` | 导出转移单 Excel | `mes:wm-transfer:export` | MesWmTransferPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/wm/transfer/submit` | 提交转移单 | `mes:wm-transfer:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/transfer/confirm` | 确认转移单 | `mes:wm-transfer:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/transfer/stock` | 执行上架 | `mes:wm-transfer:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/transfer/finish` | 完成转移单 | `mes:wm-transfer:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/wm/transfer/cancel` | 取消转移单 | `mes:wm-transfer:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 51. MesWmTransferDetailController（管理后台 - MES 调拨明细，前缀 `/mes/wm/transfer-detail`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/transfer-detail/create` | 创建调拨明细 | `mes:wm-transfer:create` | MesWmTransferDetailSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/transfer-detail/update` | 修改调拨明细 | `mes:wm-transfer:update` | MesWmTransferDetailSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/transfer-detail/delete` | 删除调拨明细 | `mes:wm-transfer:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/transfer-detail/get` | 获得调拨明细 | `mes:wm-transfer:query` | Query 参数 id（Long） | CommonResult<MesWmTransferDetailRespVO> |
| GET | `/mes/wm/transfer-detail/list-by-line` | 获得调拨明细列表（按行编号） | `mes:wm-transfer:query` | Query 参数 lineId（Long） | CommonResult<List<MesWmTransferDetailRespVO>> |

## 52. MesWmTransferLineController（管理后台 - MES 转移单行，前缀 `/mes/wm/transfer-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/transfer-line/create` | 创建转移单行 | `mes:wm-transfer:create` | MesWmTransferLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/transfer-line/update` | 修改转移单行 | `mes:wm-transfer:update` | MesWmTransferLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/transfer-line/delete` | 删除转移单行 | `mes:wm-transfer:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/transfer-line/get` | 获得转移单行 | `mes:wm-transfer:query` | Query 参数 id（Long） | CommonResult<MesWmTransferLineRespVO> |
| GET | `/mes/wm/transfer-line/list` | 获得转移单行列表 | `mes:wm-transfer:query` | Query 参数 transferId（Long） | CommonResult<List<MesWmTransferLineRespVO>> |

## 53. MesWmWarehouseAreaController（管理后台 - MES 库位，前缀 `/mes/wm/warehouse-area`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/warehouse-area/create` | 创建库位 | `mes:wm-warehouse:create` | MesWmWarehouseAreaSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/warehouse-area/update` | 更新库位 | `mes:wm-warehouse:update` | MesWmWarehouseAreaSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/warehouse-area/delete` | 删除库位 | `mes:wm-warehouse:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/warehouse-area/get` | 获得库位 | `mes:wm-warehouse:query` | Query 参数 id（Long） | CommonResult<MesWmWarehouseAreaRespVO> |
| GET | `/mes/wm/warehouse-area/page` | 获得库位分页 | `mes:wm-warehouse:query` | MesWmWarehouseAreaPageReqVO | CommonResult<PageResult<MesWmWarehouseAreaRespVO>> |
| GET | `/mes/wm/warehouse-area/simple-list` | 获得库位精简列表 | `已认证（仅登录）` | (name =, Query 参数 locationId（description） | CommonResult<List<MesWmWarehouseAreaRespVO>> |

## 54. MesWmWarehouseController（管理后台 - MES 仓库，前缀 `/mes/wm/warehouse`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/warehouse/create` | 创建仓库 | `mes:wm-warehouse:create` | MesWmWarehouseSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/warehouse/update` | 更新仓库 | `mes:wm-warehouse:update` | MesWmWarehouseSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/warehouse/delete` | 删除仓库 | `mes:wm-warehouse:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/warehouse/get` | 获得仓库 | `mes:wm-warehouse:query` | Query 参数 id（Long） | CommonResult<MesWmWarehouseRespVO> |
| GET | `/mes/wm/warehouse/page` | 获得仓库分页 | `mes:wm-warehouse:query` | MesWmWarehousePageReqVO | CommonResult<PageResult<MesWmWarehouseRespVO>> |
| GET | `/mes/wm/warehouse/simple-list` | 获得仓库精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesWmWarehouseRespVO>> |

## 55. MesWmWarehouseLocationController（管理后台 - MES 库区，前缀 `/mes/wm/warehouse-location`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/wm/warehouse-location/create` | 创建库区 | `mes:wm-warehouse:create` | MesWmWarehouseLocationSaveReqVO | CommonResult<Long> |
| PUT | `/mes/wm/warehouse-location/update` | 更新库区 | `mes:wm-warehouse:update` | MesWmWarehouseLocationSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/wm/warehouse-location/delete` | 删除库区 | `mes:wm-warehouse:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/wm/warehouse-location/get` | 获得库区 | `mes:wm-warehouse:query` | Query 参数 id（Long） | CommonResult<MesWmWarehouseLocationRespVO> |
| GET | `/mes/wm/warehouse-location/page` | 获得库区分页 | `mes:wm-warehouse:query` | MesWmWarehouseLocationPageReqVO | CommonResult<PageResult<MesWmWarehouseLocationRespVO>> |
| GET | `/mes/wm/warehouse-location/simple-list` | 获得库区精简列表 | `已认证（仅登录）` | (name =, Query 参数 warehouseId（description） | CommonResult<List<MesWmWarehouseLocationRespVO>> |
| PUT | `/mes/wm/warehouse-location/update-by-location-id` | 批量设置库区下所有库位的混放规则 | `mes:wm-warehouse:update` | Query 参数 locationId（Long）, Query 参数 allowItemMixing（Boolean）, Query 参数 allowBatchMixing（Boolean） | CommonResult<Boolean> |
