# 生产管理接口 (controller/admin/pro)

> MES 生产管理（pro）域：生产工单（确认/完成/取消状态机）与工单 BOM、生产任务与投料、生产报工（提交/审批）、流转卡与流转卡工序记录、生产工序与工序内容、工艺路线及其工序/产品/产品 BOM 关联、安灯呼叫配置与记录、上下工记录。工单/任务/报工/流转卡等核心实体均以「校验前置状态 + 抛业务错误码」的状态机方式流转。
>
> 本域共 **16 个控制器、107 个端点**，端点清单由 Controller 源码逐一提取（路径、HTTP 方法、权限标识、请求/响应 VO 与源码一致）。
>
> - 通用约定：标准 CRUD 端点集合 `POST create` / `PUT update` / `DELETE delete` / `GET get` / `GET page` / `GET export-excel`（导出返回 Excel 文件流，方法返回 void）；
> - 权限标识统一为 `mes:{域-功能}:{操作}`；个别下拉/模板端点（如 `simple-list`、`get-import-template`）仅要求登录，无独立 `@PreAuthorize`，表中记为「已认证（仅登录）」；
> - 请求/响应 VO 字段结构与状态枚举取值详见 [data-model.md](data-model.md)，业务逻辑与代码模式见 [code-patterns.md](code-patterns.md)、模块概览见 [README.md](README.md)。

## 控制器索引

| Controller | 路径前缀 | 说明 | 端点数 |
|------------|----------|------|--------|
| MesProAndonConfigController | `/mes/pro/andon-config` | MES 安灯呼叫配置 | 6 |
| MesProAndonRecordController | `/mes/pro/andon-record` | MES 安灯呼叫记录 | 6 |
| MesProCardController | `/mes/pro/card` | MES 生产流转卡 | 9 |
| MesProCardProcessController | `/mes/pro/card-process` | MES 流转卡工序记录 | 5 |
| MesProFeedbackController | `/mes/pro/feedback` | MES 生产报工 | 9 |
| MesProProcessContentController | `/mes/pro/process-content` | MES 生产工序内容 | 5 |
| MesProProcessController | `/mes/pro/process` | MES 生产工序 | 7 |
| MesProRouteController | `/mes/pro/route` | MES 工艺路线 | 8 |
| MesProRouteProcessController | `/mes/pro/route-process` | MES 工艺路线工序 | 7 |
| MesProRouteProductBomController | `/mes/pro/route-product-bom` | MES 工艺路线产品 BOM | 5 |
| MesProRouteProductController | `/mes/pro/route-product` | MES 工艺路线产品 | 5 |
| MesProTaskController | `/mes/pro/task` | MES 生产任务 | 7 |
| MesProTaskIssueController | `/mes/pro/task-issue` | MES 生产任务投料 | 6 |
| MesProWorkOrderBomController | `/mes/pro/work-order-bom` | MES 生产工单 BOM | 7 |
| MesProWorkOrderController | `/mes/pro/work-order` | MES 生产工单 | 9 |
| MesProWorkRecordController | `/mes/pro/workrecord` | MES 工作记录 | 6 |


## 1. MesProAndonConfigController（管理后台 - MES 安灯呼叫配置，前缀 `/mes/pro/andon-config`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/andon-config/create` | 创建安灯呼叫配置 | `mes:pro-andon-config:create` | MesProAndonConfigSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/andon-config/update` | 更新安灯呼叫配置 | `mes:pro-andon-config:update` | MesProAndonConfigSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/andon-config/delete` | 删除安灯呼叫配置 | `mes:pro-andon-config:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/andon-config/get` | 获得安灯呼叫配置 | `mes:pro-andon-config:query` | Query 参数 id（Long） | CommonResult<MesProAndonConfigRespVO> |
| GET | `/mes/pro/andon-config/page` | 获得安灯呼叫配置分页 | `mes:pro-andon-config:query` | MesProAndonConfigPageReqVO | CommonResult<PageResult<MesProAndonConfigRespVO>> |
| GET | `/mes/pro/andon-config/list` | 获得安灯呼叫配置列表 | `mes:pro-andon-config:query` | — | CommonResult<List<MesProAndonConfigRespVO>> |

## 2. MesProAndonRecordController（管理后台 - MES 安灯呼叫记录，前缀 `/mes/pro/andon-record`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/andon-record/create` | 创建安灯呼叫记录 | `mes:pro-andon-record:create` | MesProAndonRecordCreateReqVO | CommonResult<Long> |
| DELETE | `/mes/pro/andon-record/delete` | 删除安灯呼叫记录 | `mes:pro-andon-record:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/andon-record/update` | 更新安灯呼叫记录 | `mes:pro-andon-record:update` | MesProAndonRecordUpdateReqVO | CommonResult<Boolean> |
| GET | `/mes/pro/andon-record/get` | 获得安灯呼叫记录 | `mes:pro-andon-record:query` | Query 参数 id（Long） | CommonResult<MesProAndonRecordRespVO> |
| GET | `/mes/pro/andon-record/page` | 获得安灯呼叫记录分页 | `mes:pro-andon-record:query` | MesProAndonRecordPageReqVO | CommonResult<PageResult<MesProAndonRecordRespVO>> |
| GET | `/mes/pro/andon-record/export-excel` | 导出安灯呼叫记录 Excel | `mes:pro-andon-record:export` | MesProAndonRecordPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 3. MesProCardController（管理后台 - MES 生产流转卡，前缀 `/mes/pro/card`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/card/create` | 创建生产流转卡 | `mes:pro-card:create` | MesProCardSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/card/update` | 更新生产流转卡 | `mes:pro-card:update` | MesProCardSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/card/delete` | 删除生产流转卡 | `mes:pro-card:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/card/submit` | 提交生产流转卡 | `mes:pro-card:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/card/finish` | 完成生产流转卡 | `mes:pro-card:finish` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/card/cancel` | 取消生产流转卡 | `mes:pro-card:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/card/get` | 获得生产流转卡 | `mes:pro-card:query` | Query 参数 id（Long） | CommonResult<MesProCardRespVO> |
| GET | `/mes/pro/card/page` | 获得生产流转卡分页 | `mes:pro-card:query` | MesProCardPageReqVO | CommonResult<PageResult<MesProCardRespVO>> |
| GET | `/mes/pro/card/export-excel` | 导出生产流转卡 Excel | `mes:pro-card:export` | MesProCardPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 4. MesProCardProcessController（管理后台 - MES 流转卡工序记录，前缀 `/mes/pro/card-process`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/card-process/create` | 创建流转卡工序记录 | `mes:pro-card:create` | MesProCardProcessSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/card-process/update` | 更新流转卡工序记录 | `mes:pro-card:update` | MesProCardProcessSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/card-process/delete` | 删除流转卡工序记录 | `mes:pro-card:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/card-process/get` | 获得流转卡工序记录 | `mes:pro-card:query` | Query 参数 id（Long） | CommonResult<MesProCardProcessRespVO> |
| GET | `/mes/pro/card-process/page` | 获得流转卡工序记录分页 | `mes:pro-card:query` | MesProCardProcessPageReqVO | CommonResult<PageResult<MesProCardProcessRespVO>> |

## 5. MesProFeedbackController（管理后台 - MES 生产报工，前缀 `/mes/pro/feedback`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/feedback/create` | 创建生产报工 | `mes:pro-feedback:create` | MesProFeedbackSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/feedback/update` | 更新生产报工 | `mes:pro-feedback:update` | MesProFeedbackSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/feedback/delete` | 删除生产报工 | `mes:pro-feedback:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/feedback/get` | 获得生产报工 | `mes:pro-feedback:query` | Query 参数 id（Long） | CommonResult<MesProFeedbackRespVO> |
| GET | `/mes/pro/feedback/page` | 获得生产报工分页 | `mes:pro-feedback:query` | MesProFeedbackPageReqVO | CommonResult<PageResult<MesProFeedbackRespVO>> |
| GET | `/mes/pro/feedback/export-excel` | 导出生产报工 Excel | `mes:pro-feedback:export` | MesProFeedbackPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/pro/feedback/submit` | 提交报工 | `mes:pro-feedback:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/feedback/reject` | 驳回报工 | `mes:pro-feedback:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/feedback/approve` | 审批报工 | `mes:pro-feedback:approve` | Query 参数 id（Long） | CommonResult<Boolean> |

## 6. MesProProcessContentController（管理后台 - MES 生产工序内容，前缀 `/mes/pro/process-content`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/process-content/create` | 创建生产工序内容 | `mes:pro-process:update` | MesProProcessContentSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/process-content/update` | 更新生产工序内容 | `mes:pro-process:update` | MesProProcessContentSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/process-content/delete` | 删除生产工序内容 | `mes:pro-process:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/process-content/get` | 获得生产工序内容 | `mes:pro-process:query` | Query 参数 id（Long） | CommonResult<MesProProcessContentRespVO> |
| GET | `/mes/pro/process-content/list-by-process` | 获得生产工序内容列表（按工序编号） | `mes:pro-process:query` | Query 参数 processId（Long） | CommonResult<List<MesProProcessContentRespVO>> |

## 7. MesProProcessController（管理后台 - MES 生产工序，前缀 `/mes/pro/process`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/process/create` | 创建生产工序 | `mes:pro-process:create` | MesProProcessSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/process/update` | 更新生产工序 | `mes:pro-process:update` | MesProProcessSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/process/delete` | 删除生产工序 | `mes:pro-process:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/process/get` | 获得生产工序 | `mes:pro-process:query` | Query 参数 id（Long） | CommonResult<MesProProcessRespVO> |
| GET | `/mes/pro/process/page` | 获得生产工序分页 | `mes:pro-process:query` | MesProProcessPageReqVO | CommonResult<PageResult<MesProProcessRespVO>> |
| GET | `/mes/pro/process/simple-list` | 获得生产工序精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesProProcessRespVO>> |
| GET | `/mes/pro/process/export-excel` | 导出生产工序 Excel | `mes:pro-process:export` | MesProProcessPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 8. MesProRouteController（管理后台 - MES 工艺路线，前缀 `/mes/pro/route`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/route/create` | 创建工艺路线 | `mes:pro-route:create` | MesProRouteSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/route/update` | 更新工艺路线 | `mes:pro-route:update` | MesProRouteSaveReqVO | CommonResult<Boolean> |
| PUT | `/mes/pro/route/update-status` | 更新工艺路线状态 | `mes:pro-route:update` | Query 参数 id（Long）, Query 参数 status（Integer） | CommonResult<Boolean> |
| DELETE | `/mes/pro/route/delete` | 删除工艺路线 | `mes:pro-route:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/route/get` | 获得工艺路线 | `mes:pro-route:query` | Query 参数 id（Long） | CommonResult<MesProRouteRespVO> |
| GET | `/mes/pro/route/page` | 获得工艺路线分页 | `mes:pro-route:query` | MesProRoutePageReqVO | CommonResult<PageResult<MesProRouteRespVO>> |
| GET | `/mes/pro/route/simple-list` | 获得工艺路线精简列表 | `已认证（仅登录）` | — | CommonResult<List<MesProRouteRespVO>> |
| GET | `/mes/pro/route/export-excel` | 导出工艺路线 Excel | `mes:pro-route:export` | MesProRoutePageReqVO, HttpServletResponse | Excel 文件流（void） |

## 9. MesProRouteProcessController（管理后台 - MES 工艺路线工序，前缀 `/mes/pro/route-process`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/route-process/create` | 创建工艺路线工序 | `mes:pro-route:update` | MesProRouteProcessSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/route-process/update` | 更新工艺路线工序 | `mes:pro-route:update` | MesProRouteProcessSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/route-process/delete` | 删除工艺路线工序 | `mes:pro-route:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/route-process/get` | 获得工艺路线工序 | `mes:pro-route:query` | Query 参数 id（Long） | CommonResult<MesProRouteProcessRespVO> |
| GET | `/mes/pro/route-process/list-by-product` | 按产品获得工序列表 | `mes:pro-route:query` | Query 参数 productId（Long） | CommonResult<List<MesProRouteProcessRespVO>> |
| GET | `/mes/pro/route-process/list-by-route` | 按工艺路线获得工序列表 | `mes:pro-route:query` | Query 参数 routeId（Long） | CommonResult<List<MesProRouteProcessRespVO>> |
| GET | `/mes/pro/route-process/get-by-route-and-process` | 按工艺路线+工序获得工序配置 | `mes:pro-route:query` | Query 参数 routeId（Long）, Query 参数 processId（Long） | CommonResult<MesProRouteProcessRespVO> |

## 10. MesProRouteProductBomController（管理后台 - MES 工艺路线产品 BOM，前缀 `/mes/pro/route-product-bom`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/route-product-bom/create` | 创建工艺路线产品 BOM | `mes:pro-route:update` | MesProRouteProductBomSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/route-product-bom/update` | 更新工艺路线产品 BOM | `mes:pro-route:update` | MesProRouteProductBomSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/route-product-bom/delete` | 删除工艺路线产品 BOM | `mes:pro-route:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/route-product-bom/get` | 获得工艺路线产品 BOM | `mes:pro-route:query` | Query 参数 id（Long） | CommonResult<MesProRouteProductBomRespVO> |
| GET | `/mes/pro/route-product-bom/list` | 查询工艺路线产品 BOM 列表 | `mes:pro-route:query` | Query 参数 routeId（Long）, Query 参数 processId（Long）, Query 参数 productId（Long） | CommonResult<List<MesProRouteProductBomRespVO>> |

## 11. MesProRouteProductController（管理后台 - MES 工艺路线产品，前缀 `/mes/pro/route-product`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/route-product/create` | 创建工艺路线产品 | `mes:pro-route:update` | MesProRouteProductSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/route-product/update` | 更新工艺路线产品 | `mes:pro-route:update` | MesProRouteProductSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/route-product/delete` | 删除工艺路线产品 | `mes:pro-route:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/route-product/get` | 获得工艺路线产品 | `mes:pro-route:query` | Query 参数 id（Long） | CommonResult<MesProRouteProductRespVO> |
| GET | `/mes/pro/route-product/list-by-route` | 按工艺路线获得产品列表 | `mes:pro-route:query` | Query 参数 routeId（Long） | CommonResult<List<MesProRouteProductRespVO>> |

## 12. MesProTaskController（管理后台 - MES 生产任务，前缀 `/mes/pro/task`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/task/create` | 创建生产任务 | `mes:pro-task:create` | MesProTaskSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/task/update` | 更新生产任务 | `mes:pro-task:update` | MesProTaskSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/task/delete` | 删除生产任务 | `mes:pro-task:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/task/get` | 获得生产任务 | `mes:pro-task:query` | Query 参数 id（Long） | CommonResult<MesProTaskRespVO> |
| GET | `/mes/pro/task/page` | 获得生产任务分页 | `mes:pro-task:query` | MesProTaskPageReqVO | CommonResult<PageResult<MesProTaskRespVO>> |
| GET | `/mes/pro/task/gantt-list` | 获得甘特图任务列表 | `mes:pro-task:query` | MesProWorkOrderPageReqVO | CommonResult<List<GanttDataRespVO>> |
| GET | `/mes/pro/task/export-excel` | 导出生产任务 Excel | `mes:pro-task:export` | MesProTaskPageReqVO, HttpServletResponse | Excel 文件流（void） |

## 13. MesProTaskIssueController（管理后台 - MES 生产任务投料，前缀 `/mes/pro/task-issue`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/task-issue/create` | 创建生产任务投料 | `mes:pro-task-issue:create` | MesProTaskIssueSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/task-issue/update` | 更新生产任务投料 | `mes:pro-task-issue:update` | MesProTaskIssueSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/task-issue/delete` | 删除生产任务投料 | `mes:pro-task-issue:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/task-issue/get` | 获得生产任务投料 | `mes:pro-task-issue:query` | Query 参数 id（Long） | CommonResult<MesProTaskIssueRespVO> |
| GET | `/mes/pro/task-issue/page` | 获得生产任务投料分页 | `mes:pro-task-issue:query` | MesProTaskIssuePageReqVO | CommonResult<PageResult<MesProTaskIssueRespVO>> |
| GET | `/mes/pro/task-issue/list-by-task` | 根据任务获得投料列表 | `mes:pro-task-issue:query` | Query 参数 taskId（Long） | CommonResult<List<MesProTaskIssueRespVO>> |

## 14. MesProWorkOrderBomController（管理后台 - MES 生产工单 BOM，前缀 `/mes/pro/work-order-bom`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/work-order-bom/create` | 创建工单 BOM | `mes:pro-work-order:update` | MesProWorkOrderBomSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/work-order-bom/update` | 更新工单 BOM | `mes:pro-work-order:update` | MesProWorkOrderBomSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/work-order-bom/delete` | 删除工单 BOM | `mes:pro-work-order:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/work-order-bom/get` | 获得工单 BOM | `mes:pro-work-order:query` | Query 参数 id（Long） | CommonResult<MesProWorkOrderBomRespVO> |
| GET | `/mes/pro/work-order-bom/page` | 获得工单 BOM 分页 | `mes:pro-work-order:query` | MesProWorkOrderBomPageReqVO | CommonResult<PageResult<MesProWorkOrderBomRespVO>> |
| GET | `/mes/pro/work-order-bom/list-by-work-order-id` | 获得工单 BOM 列表 | `mes:pro-work-order:query` | Query 参数 workOrderId（Long） | CommonResult<List<MesProWorkOrderBomRespVO>> |
| GET | `/mes/pro/work-order-bom/item-list-by-work-order-id` | 获得工单物料需求列表 | `mes:pro-work-order:query` | Query 参数 workOrderId（Long） | CommonResult<List<MesProWorkOrderItemRespVO>> |

## 15. MesProWorkOrderController（管理后台 - MES 生产工单，前缀 `/mes/pro/work-order`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| POST | `/mes/pro/work-order/create` | 创建生产工单 | `mes:pro-work-order:create` | MesProWorkOrderSaveReqVO | CommonResult<Long> |
| PUT | `/mes/pro/work-order/update` | 更新生产工单 | `mes:pro-work-order:update` | MesProWorkOrderSaveReqVO | CommonResult<Boolean> |
| DELETE | `/mes/pro/work-order/delete` | 删除生产工单 | `mes:pro-work-order:delete` | Query 参数 id（Long） | CommonResult<Boolean> |
| GET | `/mes/pro/work-order/get` | 获得生产工单 | `mes:pro-work-order:query` | Query 参数 id（Long） | CommonResult<MesProWorkOrderRespVO> |
| GET | `/mes/pro/work-order/page` | 获得生产工单分页 | `mes:pro-work-order:query` | MesProWorkOrderPageReqVO | CommonResult<PageResult<MesProWorkOrderRespVO>> |
| GET | `/mes/pro/work-order/export-excel` | 导出生产工单 Excel | `mes:pro-work-order:export` | MesProWorkOrderPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/pro/work-order/confirm` | 确认工单 | `mes:pro-work-order:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/work-order/finish` | 完成工单 | `mes:pro-work-order:update` | Query 参数 id（Long） | CommonResult<Boolean> |
| PUT | `/mes/pro/work-order/cancel` | 取消工单 | `mes:pro-work-order:update` | Query 参数 id（Long） | CommonResult<Boolean> |

## 16. MesProWorkRecordController（管理后台 - MES 工作记录，前缀 `/mes/pro/workrecord`）

| 方法 | 路径 | 说明 | 权限标识 | 请求参数 | 响应 |
|------|------|------|----------|----------|------|
| GET | `/mes/pro/workrecord/log/page` | 获得工作记录流水分页 | `mes:pro-workrecord:query` | MesProWorkRecordLogPageReqVO | CommonResult<PageResult<MesProWorkRecordLogRespVO>> |
| GET | `/mes/pro/workrecord/log/get` | 获得工作记录流水 | `mes:pro-workrecord:query` | Query 参数 id（Long） | CommonResult<MesProWorkRecordLogRespVO> |
| GET | `/mes/pro/workrecord/log/export-excel` | 导出工作记录 Excel | `mes:pro-workrecord:export` | MesProWorkRecordLogPageReqVO, HttpServletResponse | Excel 文件流（void） |
| PUT | `/mes/pro/workrecord/clock-in` | 上线（绑定工作站） | `mes:pro-workrecord:clock` | Query 参数 workstationId（Long） | CommonResult<Long> |
| PUT | `/mes/pro/workrecord/clock-out` | 下线（解绑工作站） | `mes:pro-workrecord:clock` | — | CommonResult<Long> |
| GET | `/mes/pro/workrecord/get-my` | 获取当前用户绑定的工作站状态 | `mes:pro-workrecord:query` | — | CommonResult<MesProWorkRecordRespVO> |
