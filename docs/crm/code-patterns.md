# CRM 客户关系代码模式与扩展指南 (crm)

> 本文档移植自模块 Skill 知识库（skill-crm.yaml），提供该模块的代码模式、扩展指南与关键文件索引。模块概述、API 清单、数据表与设计原则见 [README.md](README.md)。

## 代码模式

### Controller 层

Controller 遵循统一的注解规范：

- `@Tag(name = "管理后台 - CRM xxx")` — Swagger 分组
- `@RestController`
- `@RequestMapping("/crm/xxx")`
- `@Validated`
- `@PreAuthorize("@ss.hasPermission('crm:xxx:action')")` — 功能权限校验
- `@Operation(summary = "xxx")` — 接口说明
- `@Parameter(name = "id", description = "编号", required = true)` — 参数说明

```java
@Tag(name = "管理后台 - CRM 客户")
@RestController
@RequestMapping("/crm/customer")
@Validated
public class CrmCustomerController {

    @PostMapping("/create")
    @Operation(summary = "创建客户")
    @PreAuthorize("@ss.hasPermission('crm:customer:create')")
    public CommonResult<Long> createCustomer(@Valid @RequestBody CrmCustomerSaveReqVO createReqVO) {
        return success(customerService.createCustomer(createReqVO, getLoginUserId()));
    }

    @PutMapping("/update")
    @Operation(summary = "更新客户")
    @PreAuthorize("@ss.hasPermission('crm:customer:update')")
    public CommonResult<Boolean> updateCustomer(@Valid @RequestBody CrmCustomerSaveReqVO updateReqVO) {
        customerService.updateCustomer(updateReqVO);
        return success(true);
    }

    @GetMapping("/page")
    @Operation(summary = "获得客户分页")
    @PreAuthorize("@ss.hasPermission('crm:customer:query')")
    public CommonResult<PageResult<CrmCustomerRespVO>> getCustomerPage(@Valid CrmCustomerPageReqVO pageVO) {
        PageResult<CrmCustomerDO> pageResult = customerService.getCustomerPage(pageVO, getLoginUserId());
        return success(new PageResult<>(buildCustomerDetailList(pageResult.getList()), pageResult.getTotal()));
    }
}
```

### Service 层

接口定义业务方法，使用 `@Valid` 注解校验参数。实现类的统一模式：

- `@Service` 注解标记服务类
- `@Validated` 启用方法参数校验
- `@Transactional(rollbackFor = Exception.class)` 声明事务
- `@LogRecord` 记录操作日志
- `@CrmPermission` 声明数据权限要求

```java
@Service
@Validated
public class CrmCustomerServiceImpl implements CrmCustomerService {

    @Override
    @Transactional(rollbackFor = Exception.class)
    @LogRecord(type = CRM_CUSTOMER_TYPE, subType = CRM_CUSTOMER_CREATE_SUB_TYPE,
               bizNo = "{{#customer.id}}", success = CRM_CUSTOMER_CREATE_SUCCESS)
    public Long createCustomer(CrmCustomerSaveReqVO createReqVO, Long userId) {
        // 1. 校验拥有客户是否到达上限
        validateCustomerExceedOwnerLimit(createReqVO.getOwnerUserId(), 1);

        // 2. 插入客户
        CrmCustomerDO customer = initCustomer(createReqVO, userId);
        customerMapper.insert(customer);

        // 3. 创建数据权限
        permissionService.createPermission(new CrmPermissionCreateReqBO()
            .setBizType(CrmBizTypeEnum.CRM_CUSTOMER.getType())
            .setBizId(customer.getId())
            .setUserId(userId)
            .setLevel(CrmPermissionLevelEnum.OWNER.getLevel()));

        // 4. 记录操作日志上下文
        LogRecordContext.putVariable("customer", customer);
        return customer.getId();
    }

    @Override
    @CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#id",
                   level = CrmPermissionLevelEnum.READ)
    public CrmCustomerDO getCustomer(Long id) {
        return customerMapper.selectById(id);
    }
}
```

### DAL 层

Mapper 的统一模式：

- 继承 `BaseMapperX<T>` 获得通用 CRUD 方法
- 使用 `@Mapper` 注解标记
- 复杂查询使用 `LambdaQueryWrapperX`

```java
@Mapper
public interface CrmCustomerMapper extends BaseMapperX<CrmCustomerDO> {

    default PageResult<CrmCustomerDO> selectPage(CrmCustomerPageReqVO pageReqVO, Long userId) {
        return selectPage(pageReqVO, new LambdaQueryWrapperX<CrmCustomerDO>()
            .likeIfPresent(CrmCustomerDO::getName, pageReqVO.getName())
            .eqIfPresent(CrmCustomerDO::getOwnerUserId, pageReqVO.getOwnerUserId())
            .orderByDesc(CrmCustomerDO::getId));
    }
}
```

### 数据权限控制

数据权限注解模板：`@CrmPermission(bizType = CrmBizTypeEnum.XXX, bizId = '#id', level = CrmPermissionLevelEnum.XXX)`。级别编码与 `CrmPermissionLevelEnum` 源码一致：

| 级别 | 编码 | 说明 |
|------|------|------|
| OWNER | 1 | 负责人权限，拥有所有操作权限，可以删除、转移 |
| READ | 2 | 只读权限，只能查看数据 |
| WRITE | 3 | 读写权限，可以编辑数据但不能删除 |

不同操作对应的权限级别示例：

```java
// 查询需要 READ 权限
@CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#id", level = CrmPermissionLevelEnum.READ)
public CrmCustomerDO getCustomer(Long id)

// 更新需要 WRITE 权限
@CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#updateReqVO.id", level = CrmPermissionLevelEnum.WRITE)
public void updateCustomer(CrmCustomerSaveReqVO updateReqVO)

// 删除需要 OWNER 权限
@CrmPermission(bizType = CrmBizTypeEnum.CRM_CUSTOMER, bizId = "#id", level = CrmPermissionLevelEnum.OWNER)
public void deleteCustomer(Long id)
```

### 异常处理

错误码前缀为 `1-020-xxx-xxx`，典型错误码：

| 错误码 | 提示信息 | 常量名 |
|--------|----------|--------|
| 1_020_006_000 | 客户不存在 | CUSTOMER_NOT_EXISTS |
| 1_020_002_000 | 商机不存在 | BUSINESS_NOT_EXISTS |
| 1_020_007_001 | {}操作失败，原因：没有权限 | CRM_PERMISSION_DENIED |

```java
// 抛出业务异常
throw exception(CUSTOMER_NOT_EXISTS);
throw exception(CUSTOMER_OWNER_EXISTS, customer.getName());
```

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`CommonResult.error(errorCode)`

## 扩展指南

### 新增 CRM 业务功能

1. **创建 DO 实体类**：在 dal/dataobject 包下创建实体类，继承 BaseDO，添加 @TableName 注解
2. **创建 Mapper 接口**：在 dal/mysql 包下创建 Mapper 接口，继承 BaseMapperX
3. **创建 Service 接口和实现类**：在 service 包下创建接口和实现类，添加 @CrmPermission 注解控制数据权限
4. **创建 Controller 和 VO**：在 controller 包下创建 Controller 和 VO 类，添加权限注解和 Swagger 注解
5. **添加业务类型枚举**：在 CrmBizTypeEnum 中添加新的业务类型，确保权限系统正确识别
6. **添加错误码**：在 ErrorCodeConstants 中添加相关错误码

### 自定义商机阶段

1. **创建商机状态组**：通过 CrmBusinessStatusService.createBusinessStatusType() 创建新的状态组
2. **添加状态阶段**：为状态组添加多个状态，设置赢单率和排序
3. **关联部门**：设置状态组适用的部门列表
4. **使用状态组**：创建商机时选择对应的状态组

### 新增客户类型/行业

1. **修改字典数据**：在 CRM_CUSTOMER_INDUSTRY 字典中添加新的行业类型
2. **前端适配**：前端页面会自动读取字典数据显示下拉选项

### 最佳实践

| 实践 | 说明 |
|------|------|
| 数据权限校验 | 所有涉及数据操作的方法都必须添加 @CrmPermission 注解，确保数据安全 |
| 操作日志记录 | 关键业务操作（创建、更新、删除、转移）使用 @LogRecord 记录操作日志 |
| 事务管理 | 涉及多表操作的方法添加 @Transactional 注解，确保数据一致性 |
| 参数校验 | VO 类使用 @Valid 注解进行参数校验，Service 层使用 @Validated |
| 公海池机制 | 客户放入公海时，需要同时更新联系人的负责人为空 |
| 客户转移 | 客户转移时，可选择同时转移联系人、商机、合同 |

## 模块依赖

### 内部依赖

| 模块 | API | 用途 |
|------|-----|------|
| yudao-module-system | AdminUserApi | 获取用户信息、校验用户存在性 |
| yudao-module-system | DeptApi | 获取部门信息，用于商机状态组关联 |
| yudao-module-bpm | 流程审批 | 合同、回款的审批流程管理 |

### 外部依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| MyBatis-Plus | 3.x | ORM 框架，提供 CRUD 操作 |
| Spring Security | 5.x | 权限校验 |
| Swagger/OpenAPI | 3.x | API 文档生成 |
| EasyExcel | 3.x | Excel 导入导出 |
| LogRecord | mzt-biz-log | 操作日志记录 |

## 关键文件

| 文件路径 | 说明 |
|----------|------|
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/dal/dataobject/customer/CrmCustomerDO.java | 客户实体类，CRM 核心聚合根 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/dal/dataobject/business/CrmBusinessDO.java | 商机实体类，销售漏斗核心 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/dal/dataobject/permission/CrmPermissionDO.java | 数据权限实体，权限控制核心 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/service/customer/CrmCustomerService.java | 客户服务接口，定义客户核心业务方法 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/service/customer/CrmCustomerServiceImpl.java | 客户服务实现，包含公海池、转移等复杂业务逻辑 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/service/permission/CrmPermissionService.java | 数据权限服务接口 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/controller/admin/customer/CrmCustomerController.java | 客户控制器，HTTP 接口入口 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/enums/common/CrmBizTypeEnum.java | 业务类型枚举，权限控制的基础 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/enums/permission/CrmPermissionLevelEnum.java | 权限级别枚举 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/enums/ErrorCodeConstants.java | 错误码常量定义 |
| yudao-module-crm/src/main/java/cn/iocoder/yudao/module/crm/framework/permission/core/annotations/CrmPermission.java | 数据权限注解定义 |

## 领域模型

### 聚合根

| 聚合根 | 说明 | 关联实体 |
|--------|------|----------|
| 客户（Customer） | CRM 系统的核心聚合根，关联商机、联系人、合同、回款等所有业务对象 | CrmBusinessDO（商机）、CrmContactDO（联系人）、CrmContractDO（合同）、CrmReceivableDO（回款）、CrmReceivablePlanDO（回款计划）、CrmFollowUpRecordDO（跟进记录） |
| 线索（Clue） | 潜在客户信息，可转化为正式客户 | — |
| 产品（Product） | 产品信息管理，被商机和合同引用 | CrmProductCategoryDO（产品分类） |

### 值对象

| 值对象 | 说明 |
|--------|------|
| CrmPermissionDO | 数据权限值对象，关联业务类型与权限级别 |
| CrmBusinessStatusDO | 商机状态值对象，属于商机状态组 |
| CrmBusinessStatusTypeDO | 商机状态组配置 |
| CrmCustomerPoolConfigDO | 客户公海池配置 |
| CrmCustomerLimitConfigDO | 客户限制配置（拥有上限、锁定上限） |

### 领域服务

| 领域服务 | 职责 |
|----------|------|
| CrmCustomerService | 客户管理领域服务，处理客户创建、转移、公海等核心业务 |
| CrmBusinessService | 商机管理领域服务，处理商机创建、状态变更等业务 |
| CrmPermissionService | 数据权限领域服务，处理权限创建、转移、校验等业务 |
| CrmContractService | 合同管理领域服务，处理合同签订、审批等业务 |
| CrmReceivableService | 回款管理领域服务，处理回款录入、审批等业务 |

## 设计与架构补充

以下内容为现有文档之外的补充，避免与 [README.md](README.md) 重复。

### 分层结构

模块采用严格的 Controller -> Service -> DAL 三层架构，`api` 包仅有 package-info（未对外暴露跨模块 API）。Service 层按业务域划分子包：

| 子包 | 职责 |
|------|------|
| service/customer/ | 客户相关服务 |
| service/clue/ | 线索相关服务 |
| service/contact/ | 联系人相关服务 |
| service/business/ | 商机相关服务 |
| service/contract/ | 合同相关服务 |
| service/receivable/ | 回款相关服务 |
| service/product/ | 产品相关服务 |
| service/permission/ | 权限相关服务 |
| service/followup/ | 跟进记录服务 |
| service/statistics/ | 统计服务 |

### 设计模式补充

除 README「设计模式」一节所列内容外，本模块还有以下模式应用：

| 模式 | 应用位置 | 用途 |
|------|----------|------|
| 策略模式 | CrmBizTypeEnum 业务类型枚举 | 统一处理不同业务类型的权限校验逻辑 |
| 模板方法 | 各 Service 实现类的校验方法 | 统一的业务校验流程 |
| Builder 模式 | 所有 DO 实体类使用 @Builder | 简化复杂对象的构建 |
| 代理模式 | CrmCustomerServiceImpl.getSelf() | 解决 AOP 事务代理问题（内部调用需穿透代理） |

### 表关系（ER）

| 主表 | 关联表 | 关系 | 外键 | 说明 |
|------|--------|------|------|------|
| crm_customer | crm_business | 1:N | customer_id | 一个客户可以有多个商机 |
| crm_customer | crm_contact | 1:N | customer_id | 一个客户可以有多个联系人 |
| crm_customer | crm_contract | 1:N | customer_id | 一个客户可以签订多个合同 |
| crm_customer | crm_receivable | 1:N | customer_id | 一个客户可以有多个回款 |
| crm_business | crm_contract | 1:N | business_id | 一个商机可以签订多个合同 |
| crm_contract | crm_receivable | 1:N | contract_id | 一个合同可以有多个回款 |
| crm_contract | crm_receivable_plan | 1:N | contract_id | 一个合同可以有多个回款计划 |
| crm_receivable_plan | crm_receivable | 1:1 | receivable_id | 一个回款计划对应一个实际回款 |
| crm_business_status_type | crm_business_status | 1:N | type_id | 一个状态组包含多个状态 |
| crm_product_category | crm_product | 1:N | category_id | 一个分类下有多个产品 |
| crm_clue | crm_customer | N:1 | customer_id | 线索转化为客户 |
