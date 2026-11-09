# 设备管理接口 (controller/admin/dv)

> MES 设备管理（dv）域：设备类型与设备台账（含 Excel 导入导出）、点检保养项目、点检保养方案（绑定设备与项目）、点检记录及其明细、保养记录及其明细、维修工单及其行。方案按周期类型生成待办并联动设备状态，维修/保养完成后自动恢复设备状态为正常。
>
> 本域共 **12 个控制器、79 个端点**，端点清单由 Controller 源码逐一提取（路径、HTTP 方法、权限标识、请求/响应 VO 与源码一致）。
>
> - 通用约定：标准 CRUD 端点集合 `POST create` / `PUT update` / `DELETE delete` / `GET get` / `GET page` / `GET export-excel`（导出返回 Excel 文件流，方法返回 void）；
> - 权限标识统一为 `mes:{域-功能}:{操作}`；个别下拉/模板端点（如 `simple-list`、`get-import-template`）仅要求登录，无独立 `@PreAuthorize`，表中记为「已认证（仅登录）」；
> - 请求/响应 VO 字段结构与状态枚举取值详见 [data-model.md](data-model.md)，业务逻辑与代码模式见 [code-patterns.md](code-patterns.md)、模块概览见 [README.md](README.md)。

## 控制器索引

| Controller | 路径前缀 | 说明 | 端点数 |
|------------|----------|------|--------|
| MesDvCheckPlanController | `/mes/dv/check-plan` | MES 点检保养方案 | 8 |
| MesDvCheckPlanMachineryController | `/mes/dv/check-plan-machinery` | MES 点检保养方案设备 | 3 |
| MesDvCheckPlanSubjectController | `/mes/dv/check-plan-subject` | MES 点检保养方案项目 | 3 |
| MesDvCheckRecordController | `/mes/dv/check-record` | MES 设备点检记录 | 7 |
| MesDvCheckRecordLineController | `/mes/dv/check-record-line` | MES 设备点检记录明细 | 6 |
| MesDvMachineryController | `/mes/dv/machinery` | MES 设备台账 | 9 |
| MesDvMachineryTypeController | `/mes/dv/machinery-type` | MES 设备类型 | 6 |
| MesDvMaintenRecordController | `/mes/dv/mainten-record` | MES 设备保养记录 | 7 |
| MesDvMaintenRecordLineController | `/mes/dv/mainten-record-line` | MES 设备保养记录明细 | 7 |
| MesDvRepairController | `/mes/dv/repair` | MES 维修工单 | 9 |
| MesDvRepairLineController | `/mes/dv/repair-line` | MES 维修工单行 | 7 |
| MesDvSubjectController | `/mes/dv/subject` | MES 点检保养项目 | 7 |


## 1. MesDvCheckPlanController（管理后台 - MES 点检保养方案，前缀 `/mes/dv/check-plan`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/check-plan/create` | 创建点检保养方案 | `mes:dv-check-plan:create` | MesDvCheckPlanSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/check-plan/update` | 更新点检保养方案 | `mes:dv-check-plan:update` | MesDvCheckPlanSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/dv/check-plan/enable` | 启用点检保养方案 | `mes:dv-check-plan:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/dv/check-plan/disable` | 停用点检保养方案 | `mes:dv-check-plan:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| DELETE | `/mes/dv/check-plan/delete` | 删除点检保养方案 | `mes:dv-check-plan:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/check-plan/get` | 获得点检保养方案 | `mes:dv-check-plan:query` | Query 参数 id（Long） | CommonResult<MesDvCheckPlanRespVO> |
| GET | `/mes/dv/check-plan/page` | 获得点检保养方案分页 | `mes:dv-check-plan:query` | MesDvCheckPlanPageReqVO | CommonResult<PageResult<MesDvCheckPlanRespVO>> |
| GET | `/mes/dv/check-plan/export-excel` | 导出点检保养方案 Excel | `mes:dv-check-plan:export` | MesDvCheckPlanPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 2. MesDvCheckPlanMachineryController（管理后台 - MES 点检保养方案设备，前缀 `/mes/dv/check-plan-machinery`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/check-plan-machinery/create` | 创建方案设备关联 | `mes:dv-check-plan:update` | MesDvCheckPlanMachinerySaveReqVO | CommonResult<Long> |
| DELETE | `/mes/dv/check-plan-machinery/delete` | 删除方案设备关联 | `mes:dv-check-plan:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/check-plan-machinery/list-by-plan` | 获得指定方案的设备列表 | `mes:dv-check-plan:query` | Query 参数 planId（Long） | CommonResult<List<MesDvCheckPlanMachineryRespVO>> |

## 3. MesDvCheckPlanSubjectController（管理后台 - MES 点检保养方案项目，前缀 `/mes/dv/check-plan-subject`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/check-plan-subject/create` | 创建方案项目关联 | `mes:dv-check-plan:update` | MesDvCheckPlanSubjectSaveReqVO | CommonResult<Long> |
| DELETE | `/mes/dv/check-plan-subject/delete` | 删除方案项目关联 | `mes:dv-check-plan:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/check-plan-subject/list-by-plan` | 获得指定方案的项目列表 | `mes:dv-check-plan:query` | Query 参数 planId（Long） | CommonResult<List<MesDvCheckPlanSubjectRespVO>> |

## 4. MesDvCheckRecordController（管理后台 - MES 设备点检记录，前缀 `/mes/dv/check-record`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/check-record/create` | 创建设备点检记录 | `mes:dv-check-record:create` | MesDvCheckRecordSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/check-record/update` | 更新设备点检记录 | `mes:dv-check-record:update` | MesDvCheckRecordSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/dv/check-record/submit` | 提交设备点检记录（草稿→已完成） | `mes:dv-check-record:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| DELETE | `/mes/dv/check-record/delete` | 删除设备点检记录 | `mes:dv-check-record:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/check-record/get` | 获得设备点检记录 | `mes:dv-check-record:query` | Query 参数 id（Long） | CommonResult<MesDvCheckRecordRespVO> |
| GET | `/mes/dv/check-record/page` | 获得设备点检记录分页 | `mes:dv-check-record:query` | MesDvCheckRecordPageReqVO | CommonResult<PageResult<MesDvCheckRecordRespVO>> |
| GET | `/mes/dv/check-record/export-excel` | 导出设备点检记录 Excel | `mes:dv-check-record:export` | MesDvCheckRecordPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 5. MesDvCheckRecordLineController（管理后台 - MES 设备点检记录明细，前缀 `/mes/dv/check-record-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/check-record-line/create` | 创建设备点检记录明细 | `mes:dv-check-record:create` | MesDvCheckRecordLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/check-record-line/update` | 更新设备点检记录明细 | `mes:dv-check-record:update` | MesDvCheckRecordLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/check-record-line/delete` | 删除设备点检记录明细 | `mes:dv-check-record:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/check-record-line/get` | 获得设备点检记录明细 | `mes:dv-check-record:query` | Query 参数 id（Long） | CommonResult<MesDvCheckRecordLineRespVO> |
| GET | `/mes/dv/check-record-line/page` | 获得设备点检记录明细分页 | `mes:dv-check-record:query` | MesDvCheckRecordLinePageReqVO | CommonResult<PageResult<MesDvCheckRecordLineRespVO>> |
| GET | `/mes/dv/check-record-line/list-by-record-id` | 获得指定点检记录的明细列表 | `mes:dv-check-record:query` | Query 参数 recordId（Long） | CommonResult<List<MesDvCheckRecordLineRespVO>> |

## 6. MesDvMachineryController（管理后台 - MES 设备台账，前缀 `/mes/dv/machinery`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/machinery/create` | 创建设备 | `mes:dv-machinery:create` | MesDvMachinerySaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/machinery/update` | 更新设备 | `mes:dv-machinery:update` | MesDvMachinerySaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/machinery/delete` | 删除设备 | `mes:dv-machinery:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/machinery/get` | 获得设备 | `mes:dv-machinery:query` | Query 参数 id（Long） | CommonResult<MesDvMachineryRespVO> |
| GET | `/mes/dv/machinery/page` | 获得设备分页 | `mes:dv-machinery:query` | MesDvMachineryPageReqVO | CommonResult<PageResult<MesDvMachineryRespVO>> |
| GET | `/mes/dv/machinery/export-excel` | 导出设备 Excel | `mes:dv-machinery:export` | MesDvMachineryPageReqVO, HttpServletResponse | Excel 文件流（void） |
| GET | `/mes/dv/machinery/simple-list` | 获得设备精简列表 | `mes:dv-machinery:query` | — | CommonResult<List<MesDvMachineryRespVO>> |
| GET | `/mes/dv/machinery/get-import-template` | 获得设备导入模板 | `已认证（仅登录）` | HttpServletResponse | Excel 文件流（void） |
| POST | `/mes/dv/machinery/import` | 导入设备 | `mes:dv-machinery:import` | Query 参数 file（MultipartFile）, Query 参数 updateSupport（Boolean） | CommonResult<MesDvMachineryImportRespVO> |

## 7. MesDvMachineryTypeController（管理后台 - MES 设备类型，前缀 `/mes/dv/machinery-type`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/machinery-type/create` | 创建设备类型 | `mes:dv-machinery-type:create` | MesDvMachineryTypeSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/machinery-type/update` | 更新设备类型 | `mes:dv-machinery-type:update` | MesDvMachineryTypeSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/machinery-type/delete` | 删除设备类型 | `mes:dv-machinery-type:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/machinery-type/get` | 获得设备类型 | `mes:dv-machinery-type:query` | Query 参数 id（Long） | CommonResult<MesDvMachineryTypeRespVO> |
| GET | `/mes/dv/machinery-type/list` | 获得设备类型列表 | `mes:dv-machinery-type:query` | MesDvMachineryTypeListReqVO | CommonResult<List<MesDvMachineryTypeRespVO>> |
| GET | `/mes/dv/machinery-type/simple-list` | 获得设备类型精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesDvMachineryTypeRespVO>> |

## 8. MesDvMaintenRecordController（管理后台 - MES 设备保养记录，前缀 `/mes/dv/mainten-record`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/mainten-record/create` | 创建设备保养记录 | `mes:dv-mainten-record:create` | MesDvMaintenRecordSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/mainten-record/update` | 更新设备保养记录 | `mes:dv-mainten-record:update` | MesDvMaintenRecordSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/mainten-record/delete` | 删除设备保养记录 | `mes:dv-mainten-record:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/mainten-record/get` | 获得设备保养记录 | `mes:dv-mainten-record:query` | Query 参数 id（Long） | CommonResult<MesDvMaintenRecordRespVO> |
| GET | `/mes/dv/mainten-record/page` | 获得设备保养记录分页 | `mes:dv-mainten-record:query` | MesDvMaintenRecordPageReqVO | CommonResult<PageResult<MesDvMaintenRecordRespVO>> |
| GET | `/mes/dv/mainten-record/export-excel` | 导出设备保养记录 Excel | `mes:dv-mainten-record:export` | MesDvMaintenRecordPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/dv/mainten-record/submit` | 提交设备保养记录（草稿→已提交） | `mes:dv-mainten-record:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 9. MesDvMaintenRecordLineController（管理后台 - MES 设备保养记录明细，前缀 `/mes/dv/mainten-record-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/mainten-record-line/create` | 创建设备保养记录明细 | `mes:dv-mainten-record:create` | MesDvMaintenRecordLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/mainten-record-line/update` | 更新设备保养记录明细 | `mes:dv-mainten-record:update` | MesDvMaintenRecordLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/mainten-record-line/delete` | 删除设备保养记录明细 | `mes:dv-mainten-record:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/mainten-record-line/get` | 获得设备保养记录明细 | `mes:dv-mainten-record:query` | Query 参数 id（Long） | CommonResult<MesDvMaintenRecordLineRespVO> |
| GET | `/mes/dv/mainten-record-line/page` | 获得设备保养记录明细分页 | `mes:dv-mainten-record:query` | MesDvMaintenRecordLinePageReqVO | CommonResult<PageResult<MesDvMaintenRecordLineRespVO>> |
| GET | `/mes/dv/mainten-record-line/list-by-record-id` | 获得指定保养记录的明细列表 | `mes:dv-mainten-record:query` | Query 参数 recordId（Long） | CommonResult<List<MesDvMaintenRecordLineRespVO>> |
| GET | `/mes/dv/mainten-record-line/export-excel` | 导出设备保养记录明细 Excel | `mes:dv-mainten-record:export` | MesDvMaintenRecordLinePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 10. MesDvRepairController（管理后台 - MES 维修工单，前缀 `/mes/dv/repair`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/repair/create` | 创建维修工单 | `mes:dv-repair:create` | MesDvRepairSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/repair/update` | 更新维修工单 | `mes:dv-repair:update` | MesDvRepairSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/repair/delete` | 删除维修工单 | `mes:dv-repair:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/repair/get` | 获得维修工单 | `mes:dv-repair:query` | Query 参数 id（Long） | CommonResult<MesDvRepairRespVO> |
| GET | `/mes/dv/repair/page` | 获得维修工单分页 | `mes:dv-repair:query` | MesDvRepairPageReqVO | CommonResult<PageResult<MesDvRepairRespVO>> |
| GET | `/mes/dv/repair/export-excel` | 导出维修工单 Excel | `mes:dv-repair:export` | MesDvRepairPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/dv/repair/submit` | 提交维修工单（草稿→维修中） | `mes:dv-repair:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/dv/repair/confirm` | 确认维修完成（维修中→待验收） | `mes:dv-repair:update` | cn.iocoder.yudao.module.mes.controller.admin.dv.repair.vo.MesDvRepairConfirmReqVO | CommonResult<Boolean> |
| PUT | `/mes/dv/repair/finish` | 完成验收（待验收→已确认） | `mes:dv-repair:update` | Query 参数 id（Long）, Query 参数 result（Integer） | CommonResult<Boolean> |

## 11. MesDvRepairLineController（管理后台 - MES 维修工单行，前缀 `/mes/dv/repair-line`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/repair-line/create` | 创建维修工单行 | `mes:dv-repair:create` | MesDvRepairLineSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/repair-line/update` | 更新维修工单行 | `mes:dv-repair:update` | MesDvRepairLineSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/repair-line/delete` | 删除维修工单行 | `mes:dv-repair:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/repair-line/get` | 获得维修工单行 | `mes:dv-repair:query` | Query 参数 id（Long） | CommonResult<MesDvRepairLineRespVO> |
| GET | `/mes/dv/repair-line/page` | 获得维修工单行分页 | `mes:dv-repair:query` | MesDvRepairLinePageReqVO | CommonResult<PageResult<MesDvRepairLineRespVO>> |
| GET | `/mes/dv/repair-line/list-by-repair-id` | 获得指定维修工单的明细列表 | `mes:dv-repair:query` | Query 参数 repairId（Long） | CommonResult<List<MesDvRepairLineRespVO>> |
| GET | `/mes/dv/repair-line/export-excel` | 导出维修工单行 Excel | `mes:dv-repair:export` | MesDvRepairLinePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 12. MesDvSubjectController（管理后台 - MES 点检保养项目，前缀 `/mes/dv/subject`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/dv/subject/create` | 创建点检保养项目 | `mes:dv-subject:create` | MesDvSubjectSaveReqVO | CommonResult<Long> |
| PUT | `/mes/dv/subject/update` | 更新点检保养项目 | `mes:dv-subject:update` | MesDvSubjectSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/dv/subject/delete` | 删除点检保养项目 | `mes:dv-subject:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/dv/subject/get` | 获得点检保养项目 | `mes:dv-subject:query` | Query 参数 id（Long） | CommonResult<MesDvSubjectRespVO> |
| GET | `/mes/dv/subject/page` | 获得点检保养项目分页 | `mes:dv-subject:query` | MesDvSubjectPageReqVO | CommonResult<PageResult<MesDvSubjectRespVO>> |
| GET | `/mes/dv/subject/simple-list` | 获得点检保养项目精简列表 | `mes:dv-subject:query` | — | CommonResult<List<MesDvSubjectRespVO>> |
| GET | `/mes/dv/subject/export-excel` | 导出点检保养项目 Excel | `mes:dv-subject:export` | MesDvSubjectPageReqVO, HttpServletResponse | Excel 文件流（void） |
