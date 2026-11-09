# 质量管理接口 (controller/admin/qc)

> MES 质量管理（qc）域：质检方案（检测种类/指标项/产品关联）与质检指标、IQC/IPQC/OQC/RQC 四类检验单及其行、待检任务聚合分页（/mes/qc/pending-inspect/page，六路 UNION 聚合到货通知单/外协入库单/生产入库行/销售出库行/生产退料行/销售退货行的待检数据）、检验结果与明细、缺陷类型与质检缺陷记录。检验结果触发对应的出入库与质量状态联动。
>
> 本域共 **16 个控制器、76 个端点**，端点清单由 Controller 源码逐一提取（路径、HTTP 方法、权限标识、请求/响应 VO 与源码一致）。
>
> - 通用约定：标准 CRUD 端点集合 `POST create` / `PUT update` / `DELETE delete` / `GET get` / `GET page` / `GET export-excel`（导出返回 Excel 文件流，方法返回 void）；
> - 权限标识统一为 `mes:{域-功能}:{操作}`；个别下拉/模板端点（如 `simple-list`、`get-import-template`）仅要求登录，无独立 `@PreAuthorize`，表中记为「已认证（仅登录）」；
> - 请求/响应 VO 字段结构与状态枚举取值详见 [data-model.md](data-model.md)，业务逻辑与代码模式见 [code-patterns.md](code-patterns.md)、模块概览见 [README.md](README.md)。

## 控制器索引

| Controller | 路径前缀 | 说明 | 端点数 |
|------------|----------|------|--------|
| MesQcDefectController | `/mes/qc/defect` | MES 缺陷类型 | 7 |
| MesQcDefectRecordController | `/mes/qc/defect-record` | MES 质检缺陷记录 | 5 |
| MesQcIndicatorController | `/mes/qc/indicator` | MES 质检指标 | 6 |
| MesQcIndicatorResultController | `/mes/qc/indicator-result` | MES 检验结果 | 5 |
| MesQcIpqcController | `/mes/qc/ipqc` | MES 过程检验单（IPQC） | 7 |
| MesQcIpqcLineController | `/mes/qc/ipqc/line` | MES 过程检验单行 | 2 |
| MesQcIqcController | `/mes/qc/iqc` | MES 来料检验单（IQC） | 7 |
| MesQcIqcLineController | `/mes/qc/iqc/line` | MES 来料检验单行 | 2 |
| MesQcOqcController | `/mes/qc/oqc` | MES 出货检验单（OQC） | 7 |
| MesQcOqcLineController | `/mes/qc/oqc/line` | MES 出货检验单行 | 2 |
| MesQcPendingInspectController | `/mes/qc/pending-inspect` | MES 待检任务 | 1 |
| MesQcRqcController | `/mes/qc/rqc` | MES 退货检验单（RQC） | 7 |
| MesQcRqcLineController | `/mes/qc/rqc/line` | MES 退货检验单行 | 2 |
| MesQcTemplateController | `/mes/qc/template` | MES 质检方案 | 6 |
| MesQcTemplateIndicatorController | `/mes/qc/template/indicator` | MES 质检方案-检测指标项 | 5 |
| MesQcTemplateItemController | `/mes/qc/template/item` | MES 质检方案-产品关联 | 5 |


## 1. MesQcDefectController（管理后台 - MES 缺陷类型，前缀 `/mes/qc/defect`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/defect/create` | 创建缺陷类型 | `mes:qc-defect:create` | MesQcDefectSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/defect/update` | 更新缺陷类型 | `mes:qc-defect:update` | MesQcDefectSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/defect/delete` | 删除缺陷类型 | `mes:qc-defect:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/defect/get` | 获得缺陷类型 | `mes:qc-defect:query` | Query 参数 id（Long） | CommonResult<MesQcDefectRespVO> |
| GET | `/mes/qc/defect/page` | 获得缺陷类型分页 | `mes:qc-defect:query` | MesQcDefectPageReqVO | CommonResult<PageResult<MesQcDefectRespVO>> |
| GET | `/mes/qc/defect/simple-list` | 获得缺陷类型精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesQcDefectRespVO>> |
| GET | `/mes/qc/defect/export-excel` | 导出缺陷类型 Excel | `mes:qc-defect:export` | MesQcDefectPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 2. MesQcDefectRecordController（管理后台 - MES 质检缺陷记录，前缀 `/mes/qc/defect-record`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/defect-record/create` | 创建质检缺陷记录 | `mes:qc-defect:create` | MesQcDefectRecordSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/defect-record/update` | 更新质检缺陷记录 | `mes:qc-defect:update` | MesQcDefectRecordSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/defect-record/delete` | 删除质检缺陷记录 | `mes:qc-defect:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/defect-record/get` | 获得质检缺陷记录 | `mes:qc-defect:query` | Query 参数 id（Long） | CommonResult<MesQcDefectRecordRespVO> |
| GET | `/mes/qc/defect-record/page` | 获得质检缺陷记录分页 | `mes:qc-defect:query` | MesQcDefectRecordPageReqVO | CommonResult<PageResult<MesQcDefectRecordRespVO>> |

## 3. MesQcIndicatorController（管理后台 - MES 质检指标，前缀 `/mes/qc/indicator`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/indicator/create` | 创建质检指标 | `mes:qc-indicator:create` | MesQcIndicatorSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/indicator/update` | 更新质检指标 | `mes:qc-indicator:update` | MesQcIndicatorSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/indicator/delete` | 删除质检指标 | `mes:qc-indicator:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/indicator/get` | 获得质检指标 | `mes:qc-indicator:query` | Query 参数 id（Long） | CommonResult<MesQcIndicatorRespVO> |
| GET | `/mes/qc/indicator/page` | 获得质检指标分页 | `mes:qc-indicator:query` | MesQcIndicatorPageReqVO | CommonResult<PageResult<MesQcIndicatorRespVO>> |
| GET | `/mes/qc/indicator/export-excel` | 导出质检指标 Excel | `mes:qc-indicator:export` | MesQcIndicatorPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 4. MesQcIndicatorResultController（管理后台 - MES 检验结果，前缀 `/mes/qc/indicator-result`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/indicator-result/create` | 创建检验结果 | `mes:qc-iqc:create` | MesQcIndicatorResultSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/indicator-result/update` | 更新检验结果 | `mes:qc-iqc:update` | MesQcIndicatorResultSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/indicator-result/delete` | 删除检验结果 | `mes:qc-iqc:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/indicator-result/get-detail` | 获得检验结果明细（含检测项模板） | `mes:qc-iqc:query` | Query 参数 id（Long）, Query 参数 qcId（Long）, Query 参数 qcType（Integer） | CommonResult<MesQcIndicatorResultRespVO> |
| GET | `/mes/qc/indicator-result/page` | 获得检验结果分页 | `mes:qc-iqc:query` | MesQcIndicatorResultPageReqVO | CommonResult<PageResult<MesQcIndicatorResultRespVO>> |

## 5. MesQcIpqcController（管理后台 - MES 过程检验单（IPQC），前缀 `/mes/qc/ipqc`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/ipqc/create` | 创建过程检验单 | `mes:qc-ipqc:create` | MesQcIpqcSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/ipqc/update` | 更新过程检验单 | `mes:qc-ipqc:update` | MesQcIpqcSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/qc/ipqc/finish` | 完成过程检验单 | `mes:qc-ipqc:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| DELETE | `/mes/qc/ipqc/delete` | 删除过程检验单 | `mes:qc-ipqc:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/ipqc/get` | 获得过程检验单 | `mes:qc-ipqc:query` | Query 参数 id（Long） | CommonResult<MesQcIpqcRespVO> |
| GET | `/mes/qc/ipqc/page` | 获得过程检验单分页 | `mes:qc-ipqc:query` | MesQcIpqcPageReqVO | CommonResult<PageResult<MesQcIpqcRespVO>> |
| GET | `/mes/qc/ipqc/export-excel` | 导出过程检验单 Excel | `mes:qc-ipqc:export` | MesQcIpqcPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 6. MesQcIpqcLineController（管理后台 - MES 过程检验单行，前缀 `/mes/qc/ipqc/line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/qc/ipqc/line/get` | 获得过程检验单行 | `mes:qc-ipqc:query` | Query 参数 id（Long） | CommonResult<MesQcIpqcLineRespVO> |
| GET | `/mes/qc/ipqc/line/page` | 获得过程检验单行分页 | `mes:qc-ipqc:query` | MesQcIpqcLinePageReqVO | CommonResult<PageResult<MesQcIpqcLineRespVO>> |

## 7. MesQcIqcController（管理后台 - MES 来料检验单（IQC），前缀 `/mes/qc/iqc`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/iqc/create` | 创建来料检验单 | `mes:qc-iqc:create` | MesQcIqcSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/iqc/update` | 更新来料检验单 | `mes:qc-iqc:update` | MesQcIqcSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/qc/iqc/finish` | 完成来料检验单 | `mes:qc-iqc:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| DELETE | `/mes/qc/iqc/delete` | 删除来料检验单 | `mes:qc-iqc:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/iqc/get` | 获得来料检验单 | `mes:qc-iqc:query` | Query 参数 id（Long） | CommonResult<MesQcIqcRespVO> |
| GET | `/mes/qc/iqc/page` | 获得来料检验单分页 | `mes:qc-iqc:query` | MesQcIqcPageReqVO | CommonResult<PageResult<MesQcIqcRespVO>> |
| GET | `/mes/qc/iqc/export-excel` | 导出来料检验单 Excel | `mes:qc-iqc:export` | MesQcIqcPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 8. MesQcIqcLineController（管理后台 - MES 来料检验单行，前缀 `/mes/qc/iqc/line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/qc/iqc/line/get` | 获得来料检验单行 | `mes:qc-iqc:query` | Query 参数 id（Long） | CommonResult<MesQcIqcLineRespVO> |
| GET | `/mes/qc/iqc/line/page` | 获得来料检验单行分页 | `mes:qc-iqc:query` | MesQcIqcLinePageReqVO | CommonResult<PageResult<MesQcIqcLineRespVO>> |

## 9. MesQcOqcController（管理后台 - MES 出货检验单（OQC），前缀 `/mes/qc/oqc`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/oqc/create` | 创建出货检验单 | `mes:qc-oqc:create` | MesQcOqcSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/oqc/update` | 更新出货检验单 | `mes:qc-oqc:update` | MesQcOqcSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/qc/oqc/finish` | 完成出货检验单 | `mes:qc-oqc:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| DELETE | `/mes/qc/oqc/delete` | 删除出货检验单 | `mes:qc-oqc:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/oqc/get` | 获得出货检验单 | `mes:qc-oqc:query` | Query 参数 id（Long） | CommonResult<MesQcOqcRespVO> |
| GET | `/mes/qc/oqc/page` | 获得出货检验单分页 | `mes:qc-oqc:query` | MesQcOqcPageReqVO | CommonResult<PageResult<MesQcOqcRespVO>> |
| GET | `/mes/qc/oqc/export-excel` | 导出出货检验单 Excel | `mes:qc-oqc:export` | MesQcOqcPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 10. MesQcOqcLineController（管理后台 - MES 出货检验单行，前缀 `/mes/qc/oqc/line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/qc/oqc/line/get` | 获得出货检验单行 | `mes:qc-oqc:query` | Query 参数 id（Long） | CommonResult<MesQcOqcLineRespVO> |
| GET | `/mes/qc/oqc/line/page` | 获得出货检验单行分页 | `mes:qc-oqc:query` | MesQcOqcLinePageReqVO | CommonResult<PageResult<MesQcOqcLineRespVO>> |

## 11. MesQcPendingInspectController（管理后台 - MES 待检任务，前缀 `/mes/qc/pending-inspect`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/qc/pending-inspect/page` | 获得待检任务分页 | `mes:qc-pending-inspect:query` | MesQcPendingInspectPageReqVO | CommonResult<PageResult<MesQcPendingInspectRespVO>> |

## 12. MesQcRqcController（管理后台 - MES 退货检验单（RQC），前缀 `/mes/qc/rqc`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/rqc/create` | 创建退货检验单 | `mes:qc-rqc:create` | MesQcRqcSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/rqc/update` | 更新退货检验单 | `mes:qc-rqc:update` | MesQcRqcSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/qc/rqc/finish` | 完成退货检验单 | `mes:qc-rqc:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| DELETE | `/mes/qc/rqc/delete` | 删除退货检验单 | `mes:qc-rqc:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/rqc/get` | 获得退货检验单 | `mes:qc-rqc:query` | Query 参数 id（Long） | CommonResult<MesQcRqcRespVO> |
| GET | `/mes/qc/rqc/page` | 获得退货检验单分页 | `mes:qc-rqc:query` | MesQcRqcPageReqVO | CommonResult<PageResult<MesQcRqcRespVO>> |
| GET | `/mes/qc/rqc/export-excel` | 导出退货检验单 Excel | `mes:qc-rqc:export` | MesQcRqcPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 13. MesQcRqcLineController（管理后台 - MES 退货检验单行，前缀 `/mes/qc/rqc/line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/qc/rqc/line/get` | 获得退货检验单行 | `mes:qc-rqc:query` | Query 参数 id（Long） | CommonResult<MesQcRqcLineRespVO> |
| GET | `/mes/qc/rqc/line/page` | 获得退货检验单行分页 | `mes:qc-rqc:query` | MesQcRqcLinePageReqVO | CommonResult<PageResult<MesQcRqcLineRespVO>> |

## 14. MesQcTemplateController（管理后台 - MES 质检方案，前缀 `/mes/qc/template`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/template/create` | 创建质检方案 | `mes:qc-template:create` | MesQcTemplateSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/template/update` | 更新质检方案 | `mes:qc-template:update` | MesQcTemplateSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/template/delete` | 删除质检方案 | `mes:qc-template:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/template/get` | 获得质检方案 | `mes:qc-template:query` | Query 参数 id（Long） | CommonResult<MesQcTemplateRespVO> |
| GET | `/mes/qc/template/page` | 获得质检方案分页 | `mes:qc-template:query` | MesQcTemplatePageReqVO | CommonResult<PageResult<MesQcTemplateRespVO>> |
| GET | `/mes/qc/template/export-excel` | 导出质检方案 Excel | `mes:qc-template:export` | MesQcTemplatePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 15. MesQcTemplateIndicatorController（管理后台 - MES 质检方案-检测指标项，前缀 `/mes/qc/template/indicator`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/template/indicator/create` | 创建质检方案-检测指标项 | `mes:qc-template:create` | MesQcTemplateIndicatorSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/template/indicator/update` | 更新质检方案-检测指标项 | `mes:qc-template:update` | MesQcTemplateIndicatorSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/template/indicator/delete` | 删除质检方案-检测指标项 | `mes:qc-template:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/template/indicator/get` | 获得质检方案-检测指标项 | `mes:qc-template:query` | Query 参数 id（Long） | CommonResult<MesQcTemplateIndicatorRespVO> |
| GET | `/mes/qc/template/indicator/page` | 获得质检方案-检测指标项分页 | `mes:qc-template:query` | MesQcTemplateIndicatorPageReqVO | CommonResult<PageResult<MesQcTemplateIndicatorRespVO>> |

## 16. MesQcTemplateItemController（管理后台 - MES 质检方案-产品关联，前缀 `/mes/qc/template/item`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/qc/template/item/create` | 创建质检方案-产品关联 | `mes:qc-template:create` | MesQcTemplateItemSaveReqVO | CommonResult<Long> |
| PUT | `/mes/qc/template/item/update` | 更新质检方案-产品关联 | `mes:qc-template:update` | MesQcTemplateItemSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/qc/template/item/delete` | 删除质检方案-产品关联 | `mes:qc-template:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/qc/template/item/get` | 获得质检方案-产品关联 | `mes:qc-template:query` | Query 参数 id（Long） | CommonResult<MesQcTemplateItemRespVO> |
| GET | `/mes/qc/template/item/page` | 获得质检方案-产品关联分页 | `mes:qc-template:query` | MesQcTemplateItemPageReqVO | CommonResult<PageResult<MesQcTemplateItemRespVO>> |
