# CRM 模块 (crm)

> 客户关系管理（Customer Relationship Management）模块，覆盖「线索 → 客户 → 联系人 → 商机 → 合同 → 回款」的完整销售闭环，配套公海回收、数据权限、跟进记录、业绩目标与多维统计分析能力。

## 模块概述

- **模块路径**: `yudao-module-crm`（单模块布局，无子模块拆分）
- **业务定位**: 面向销售团队的全流程 CRM 系统。以客户为核心资产，支持线索转化、商机推进（阶段管理）、合同签约（对接 BPM 审批流）、回款跟踪；通过「公海池」实现客户资源回收再分配，通过 `crm_permission` 表实现行级数据权限（只读/读写），并提供销售漏斗、排行榜、客户画像等多维统计。
- **技术栈**: Spring Boot 2.7.18 / MyBatis-Plus / springdoc（Swagger v3）/ EasyExcel（导入导出）/ mzt-biz-log（操作日志注解）/ BPM 流程对接（yudao-module-bpm API）/ 租户能力（yudao-spring-boot-starter-biz-tenant）

## 设计原则

| 原则 | 说明 |
|------|------|
| 行级数据权限 | 所有业务数据通过 `CrmPermissionDO`（bizType + bizId + userId + level）控制，`@CrmPermission` 注解 + `CrmPermissionAspect` 切面在 Service 层统一校验（本人/只读/读写） |
| 客户公海机制 | 无负责人的客户进入公海，支持领取/分配/自动回收（`CrmCustomerAutoPutPoolJob`），回收规则由 `crm_customer_pool_config` 配置 |
| 审批流解耦 | 合同、回款的审批通过 `BpmProcessInstanceApi` 发起 BPM 流程，审批结果经 `BpmProcessInstanceStatusEventListener` 子类回调更新 `auditStatus` |
| 跟进状态统一 | 客户/线索/联系人统一维护 `followUpStatus`、`contactLastTime`、`contactNextTime`，跟进记录（`crm_follow_up_record`）按 bizType + bizId 关联任意业务对象 |
| 通用域枚举 | `CrmBizTypeEnum` 定义所有业务对象类型（客户/线索/商机/合同/回款等），供数据权限、跟进、操作日志、负责人变更记录复用 |
| 数据锁定保护 | 客户锁定（`lockStatus`）后不可放入公海；合同被回款引用、商机被合同引用、回款被计划引用时禁止删除 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|--------|------|----------|
| 客户管理 | 客户 CRUD、成交状态、锁定、转移、导入导出、公海领取/分配/回收、公海与限制配置 | CrmCustomerDO、CrmCustomerPoolConfigDO、CrmCustomerLimitConfigDO |
| 线索管理 | 线索 CRUD、转化为客户（transform）、转移、待跟进数量统计 | CrmClueDO |
| 联系人管理 | 客户联系人 CRUD、联系人-商机关联/解绑、转移 | CrmContactDO、CrmContactBusinessDO |
| 商机管理 | 商机 CRUD、阶段推进（状态组/状态两级配置）、结束状态、转移 | CrmBusinessDO、CrmBusinessStatusDO、CrmBusinessStatusTypeDO、CrmBusinessProductDO |
| 合同管理 | 合同 CRUD、提交 BPM 审批、到期提醒、审批状态回调、合同配置 | CrmContractDO、CrmContractProductDO、CrmContractConfigDO |
| 回款管理 | 回款 CRUD、提交审批、回款计划（期数/提醒）、审批状态回调 | CrmReceivableDO、CrmReceivablePlanDO |
| 产品管理 | CRM 产品与产品分类（树形）维护，供商机/合同关联计算金额 | CrmProductDO、CrmProductCategoryDO |
| 跟进记录 | 按 bizType + bizId 记录跟进内容/图片/附件/下次联系时间，同步回写业务表 | CrmFollowUpRecordDO |
| 数据权限 | 业务数据的团队成员授权（只读/读写）、退出团队、负责人变更记录 | CrmPermissionDO、CrmOwnerRecordDO |
| 操作日志 | 基于 mzt-biz-log 记录客户/联系人/商机/合同等变更，分页查询走 system 模块 OperateLogApi | —（查询转发 system 模块） |
| 业绩目标 | 按员工/部门（objectType）按年设定合同、回款月度目标 | CrmPerformanceConfigDO |
| 数据统计 | 客户总量/跟进/公海/成交周期、销售漏斗、员工业绩、业绩目标完成度、客户画像、产品销售、排行榜 8 类统计 | —（只读聚合查询） |

## API 接口索引

> 端点总数 167（> 120），按域分节给出控制器级摘要与代表性端点；完整端点清单见各 `api-{key}.md`。

### 客户管理域（26 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmCustomerController | 客户管理（/crm/customer） | 19 | POST /crm/customer/create；PUT /crm/customer/receive（领取公海客户，`crm:customer:receive`）；PUT /crm/customer/put-pool（放入公海，`crm:customer:update`）；GET /crm/customer/put-pool-remind-page（待进公海分页）；POST /crm/customer/import（导入，`crm:customer:import`）；GET /crm/customer/simple-list（已认证，内部按数据权限过滤） |
| CrmCustomerLimitConfigController | 客户拥有量限制配置（/crm/customer-limit-config） | 5 | POST /crm/customer-limit-config/create（`crm:customer-limit-config:create`）；GET /page |
| CrmCustomerPoolConfigController | 客户公海规则配置（/crm/customer-pool-config） | 2 | GET /crm/customer-pool-config/get（`crm:customer-pool-config:query`）；PUT /save |

### 线索管理域（9 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmClueController | 线索管理（/crm/clue） | 9 | POST /crm/clue/create（`crm:clue:create`）；PUT /crm/clue/transform（线索转化为客户，`crm:clue:update`）；PUT /crm/clue/transfer（转移）；GET /follow-count（待跟进数量） |

### 联系人管理域（15 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmContactController | 联系人管理（/crm/contact） | 15 | POST /crm/contact/create（`crm:contact:create`）；POST /crm/contact/create-business-list（关联商机，`crm:contact:create-business`）；DELETE /crm/contact/delete-business-list2；GET /page-by-business（已认证） |

### 商机管理域（20 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmBusinessController | 商机管理（/crm/business） | 13 | POST /crm/business/create（`crm:business:create`）；PUT /crm/business/update-status（推进阶段，`crm:business:update`）；GET /page-by-customer（已认证）；PUT /transfer |
| CrmBusinessStatusController | 商机状态组配置（/crm/business-status） | 7 | POST /create（`crm:business-status:create`）；GET /status-simple-list（已认证，按状态组取阶段） |

### 合同管理域（15 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmContractController | 合同管理（/crm/contract） | 13 | POST /crm/contract/create（`crm:contract:create`）；PUT /crm/contract/submit（提交 BPM 审批，`crm:contract:update`）；GET /audit-count（待审核数量）；GET /remind-count（到期提醒数量） |
| CrmContractConfigController | 合同到期提醒配置（/crm/contract-config） | 2 | GET /get（`crm:contract-config:query`）；PUT /save |

### 回款管理域（18 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmReceivableController | 回款管理（/crm/receivable） | 9 | POST /crm/receivable/create（`crm:receivable:create`）；PUT /submit（提交审批）；GET /audit-count |
| CrmReceivablePlanController | 回款计划管理（/crm/receivable-plan） | 9 | POST /crm/receivable-plan/create（`crm:receivable-plan:create`）；GET /remind-count（待回款提醒数量）；GET /simple-list（`crm:receivable-plan:query`） |

### 产品管理域（12 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmProductController | 产品管理（/crm/product） | 7 | POST /crm/product/create（`crm:product:create`）；GET /simple-list（已认证，仅上架产品） |
| CrmProductCategoryController | 产品分类管理（/crm/product-category，树形） | 5 | POST /create（`crm:product-category:create`）；GET /list |

### 跟进记录域（4 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmFollowUpRecordController | 跟进记录（/crm/follow-up-record） | 4 | POST /crm/follow-up-record/create；GET /page（均仅登录校验，数据权限由 Service 层过滤） |

### 数据权限域（5 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmPermissionController | 团队数据权限（/crm/permission） | 5 | POST /crm/permission/create（添加团队成员）；DELETE /delete-self（退出团队）；GET /list?bizType=&bizId=（均仅登录校验） |

### 操作日志域（1 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmOperateLogController | CRM 操作日志（/crm/operate-log） | 1 | GET /crm/operate-log/page（已认证，内部转发 system 模块 OperateLogApi） |

### 业绩目标域（5 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmPerformanceConfigController | 业绩目标设置（/crm/performance-config） | 5 | POST /crm/performance-config/create（`crm:performance-config:create`）；GET /page |

### 数据统计域（37 端点）

| Controller | 说明 | 端点数 | 代表性端点 |
|-----------|------|--------|-----------|
| CrmStatisticsCustomerController | 客户统计（/crm/statistics-customer） | 12 | GET /get-customer-summary-by-date、/get-customer-deal-cycle-by-area（`crm:statistics-customer:query`） |
| CrmStatisticsFunnelController | 销售漏斗（/crm/statistics-funnel） | 6 | GET /get-funnel-summary、/get-business-inversion-rate-summary-by-date（`crm:statistics-funnel:query`） |
| CrmStatisticsPerformanceController | 员工业绩统计（/crm/statistics-performance） | 4 | GET /get-contract-count-performance、/get-contract-summary（`crm:statistics-performance:query`） |
| CrmStatisticsPerformanceTargetController | 业绩目标完成度统计（/crm/statistics-performance-target） | 1 | GET /get-performance-target-summary（`crm:statistics-performance-target:query`） |
| CrmStatisticsPortraitController | 客户画像（/crm/statistics-portrait） | 4 | GET /get-customer-area-summary、/get-customer-source-summary（`crm:statistics-portrait:query`） |
| CrmStatisticsProductController | 产品统计（/crm/statistics-product） | 2 | GET /get-product-sales-list（`crm:statistics-product:query`） |
| CrmStatisticsRankController | 排行榜（/crm/statistics-rank） | 8 | GET /get-contract-price-rank、/get-follow-count-rank（`crm:statistics-rank:query`） |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|------|------|----------|----------|
| crm_customer | 客户 | BaseDO | name、ownerUserId、lockStatus、dealStatus、followUpStatus、contactNextTime、industryId、level、source、areaId、mobile |
| crm_customer_pool_config | 客户公海规则配置 | BaseDO | enabled、contactExpireDays、dealExpireDays、notifyEnabled、notifyDays |
| crm_customer_limit_config | 客户拥有量限制配置 | BaseDO | type、userIds、deptIds、maxCount、dealCountEnabled |
| crm_clue | 线索 | BaseDO | name、ownerUserId、transformStatus、customerId（转化后回写）、followUpStatus、mobile、industryId、level、source |
| crm_contact | 联系人 | BaseDO | name、customerId、ownerUserId、mobile、master（是否主联系人）、parentId、email、areaId |
| crm_contact_business | 联系人-商机关联表 | BaseDO | contactId、businessId |
| crm_business | 商机 | BaseDO | name、customerId、ownerUserId、statusTypeId、statusId、endStatus、totalProductPrice、discountPercent、totalPrice、dealTime |
| crm_business_product | 商机-产品明细 | BaseDO | businessId、productId、productPrice、businessPrice、count、totalPrice |
| crm_business_status_type | 商机状态组 | BaseDO | name、deptIds（适用部门） |
| crm_business_status | 商机状态（阶段） | BaseDO | typeId、name、percent（赢单率）、sort |
| crm_contract | 合同 | BaseDO | name、no（序列号）、customerId、businessId、ownerUserId、processInstanceId、auditStatus、orderDate、startTime/endTime、totalPrice、signContactId、signUserId |
| crm_contract_product | 合同-产品明细 | BaseDO | contractId、productId、productPrice、contractPrice、count、totalPrice |
| crm_contract_config | 合同到期提醒配置 | BaseDO | notifyEnabled、notifyDays |
| crm_receivable | 回款 | BaseDO | no、planId、customerId、contractId、ownerUserId、returnTime、returnType、price、processInstanceId、auditStatus |
| crm_receivable_plan | 回款计划 | BaseDO | period（期数）、customerId、contractId、ownerUserId、returnTime、returnType、price、receivableId、remindDays、remindTime |
| crm_product | CRM 产品 | BaseDO | name、no、unit、price、status、categoryId、ownerUserId |
| crm_product_category | 产品分类（树形） | BaseDO | name、parentId |
| crm_follow_up_record | 跟进记录 | BaseDO | bizType、bizId、type、content、nextTime、picUrls、fileUrls、businessIds、contactIds |
| crm_permission | 数据权限（团队成员） | BaseDO | bizType、bizId、userId、level（1 负责人/2 读写/3 只读） |
| crm_owner_record | 负责人变更记录 | BaseDO | bizType、bizId、preOwnerUserId、postOwnerUserId |
| crm_performance_config | 业绩目标 | BaseDO | bizType、objectType、objectId、year、yearTargetPrice、januaryTargetPrice ~ decemberTargetPrice（12 个月度字段） |

> 所有 DO 均继承 `BaseDO`（creator/createTime/updater/updateTime/deleted），无单独租户字段；租户隔离由 biz-tenant 组件在 SQL 层统一处理。

## 设计模式

| 模式 | 应用位置 | 用途 |
|------|----------|------|
| AOP 切面 + 自定义注解 | `framework/permission/core`（@CrmPermission + CrmPermissionAspect） | Controller/Service 方法级数据权限校验（校验当前用户对该业务记录的读/写权限） |
| 模板方法（事件监听） | `service/contract/listener/CrmContractStatusListener`、`service/receivable/listener/CrmReceivableStatusListener` | 继承 BPM 的 `BpmProcessInstanceStatusEventListener`，只实现流程结束回调逻辑，回写合同/回款审批状态 |
| 策略模式 | `framework/operatelog/core` 下 16 个 ParseFunction（CrmCustomerParseFunction 等，实现 mzt-biz-log 的 IParseFunction） | 操作日志模板变量按业务类型解析（客户名、联系人、商机、区域、字典等） |
| 策略模式 | `framework/excel/core/AreaExcelColumnSelectFunction`（实现 ExcelColumnSelectFunction） | 客户导入模板中「所在区域」列的 Excel 下拉数据源 |
| 拦截器扩展 | `framework/web/config/CrmWebConfiguration` | 注册 CRM 专用 Web 能力 |

## 依赖关系

- **上游**（本模块依赖）:
  - 业务模块：`yudao-module-system`（AdminUserApi、DeptApi、PostApi、OperateLogApi）、`yudao-module-bpm`（BpmProcessInstanceApi + 流程状态事件监听）、`yudao-module-infra`（pom 依赖）
  - Framework starter：yudao-spring-boot-starter-web、security、mybatis、excel、biz-tenant、biz-ip、test
- **下游**（依赖本模块）: 无（`api` 包仅有 package-info，未对外提供跨模块 API；其他模块未引用 crm 包）

## 对外暴露的 API

> 无。crm 模块未定义 `api` 包下的跨模块接口，仅作为终端业务模块被 yudao-server 聚合启动。

## 详细文档

- [api-customer.md](api-customer.md) - 客户管理
- [api-clue.md](api-clue.md) - 线索管理
- [api-contact.md](api-contact.md) - 联系人管理
- [api-business.md](api-business.md) - 商机管理
- [api-contract.md](api-contract.md) - 合同管理
- [api-receivable.md](api-receivable.md) - 回款管理
- [api-product.md](api-product.md) - 产品管理
- [api-followup.md](api-followup.md) - 跟进记录
- [api-permission.md](api-permission.md) - 数据权限
- [api-operatelog.md](api-operatelog.md) - 操作日志
- [api-performance.md](api-performance.md) - 业绩目标
- [api-statistics.md](api-statistics.md) - 数据统计
- [data-model.md](data-model.md) - 数据模型详情
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
