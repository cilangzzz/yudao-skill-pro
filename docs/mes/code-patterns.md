# MES 制造执行代码模式与扩展指南 (mes)

> 本文档移植自模块 Skill 知识库（skill-mes.yaml），提供该模块的代码模式、扩展指南与关键文件索引。模块总体架构、API 索引与数据模型见 [README.md](README.md)。

## 代码模式

### Controller 层规范

Controller 统一使用以下注解组合：

- `@Tag(name = '管理后台 - xxx')` — Swagger 文档标签
- `@RestController` — REST 控制器
- `@RequestMapping('/admin-api/mes/xxx')` — 请求路径前缀
- `@Validated` — 参数校验
- `@PreAuthorize('@ss.hasPermission('mes:xxx:action')')` — 权限控制

完整示例（以物料管理为例）：

```java
@Tag(name = "管理后台 - 物料管理")
@RestController
@RequestMapping("/admin-api/mes/item")
@Validated
public class MesItemController {
    @Resource
    private MesItemService itemService;

    @PostMapping("/create")
    @Operation(summary = "创建物料")
    @PreAuthorize("@ss.hasPermission('mes:item:create')")
    public CommonResult<Long> create(@Valid @RequestBody MesItemSaveReqVO reqVO) {
        return success(itemService.create(reqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新物料")
    @PreAuthorize("@ss.hasPermission('mes:item:update')")
    public CommonResult<Boolean> update(@Valid @RequestBody MesItemSaveReqVO reqVO) {
        itemService.update(reqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除物料")
    @PreAuthorize("@ss.hasPermission('mes:item:delete')")
    public CommonResult<Boolean> delete(@RequestParam("id") Long id) {
        itemService.delete(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获取物料详情")
    @PreAuthorize("@ss.hasPermission('mes:item:query')")
    public CommonResult<MesItemRespVO> get(@RequestParam("id") Long id) {
        return success(itemService.get(id));
    }

    @GetMapping("/page")
    @Operation(summary = "物料分页查询")
    @PreAuthorize("@ss.hasPermission('mes:item:query')")
    public CommonResult<PageResult<MesItemRespVO>> page(@Valid MesItemPageReqVO reqVO) {
        return success(itemService.page(reqVO));
    }
}
```

### Service 层规范

接口与实现分离：`XxxService` 接口定义业务方法，`XxxServiceImpl` 实现类。

实现类骨架：

```java
@Service
@Validated
public class XxxServiceImpl implements XxxService {
    @Resource
    private XxxMapper xxxMapper;

    // 使用 static final 定义常量
    // 使用 @Transactional 注解控制事务
    // 使用 validateXxxExists 方法校验存在性
    // 使用 exception(ErrorCode) 抛出业务异常
}
```

状态机流转示例（以工单状态变更为例，变更前校验前置状态并以 CAS 方式更新）：

```java
@Override
@Transactional(rollbackFor = Exception.class)
public void updateStatus(Long id, Integer status) {
  MesWorkOrderDO order = validateWorkOrderExists(id);
  // 校验状态流转
  if (!MesWorkOrderStatusEnum.canTransit(order.getStatus(), status)) {
    throw exception(WORK_ORDER_STATUS_TRANSIT_FAIL);
  }
  // CAS 更新
  workOrderMapper.updateStatus(id, order.getStatus(), status);
}
```

### 数据访问层（DAL）规范

Mapper 统一继承 `BaseMapperX`，用 `LambdaQueryWrapperX` 的 `xxxIfPresent` 系列方法实现条件拼接（条件为空自动忽略）：

```java
public interface XxxMapper extends BaseMapperX<XxxDO> {
    default PageResult<XxxDO> selectPage(XxxPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<XxxDO>()
                .likeIfPresent(XxxDO::getName, reqVO.getName())
                .eqIfPresent(XxxDO::getStatus, reqVO.getStatus())
                .orderByDesc(XxxDO::getId));
    }
}
```

具体示例（物料分页查询）：

```java
public interface MesItemMapper extends BaseMapperX<MesItemDO> {
    default PageResult<MesItemDO> selectPage(MesItemPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<MesItemDO>()
                .likeIfPresent(MesItemDO::getName, reqVO.getName())
                .likeIfPresent(MesItemDO::getCode, reqVO.getCode())
                .eqIfPresent(MesItemDO::getItemTypeId, reqVO.getItemTypeId())
                .eqIfPresent(MesItemDO::getStatus, reqVO.getStatus())
                .orderByDesc(MesItemDO::getId));
    }
}
```

### VO Assembly 模式

查询接口批量获取关联实体后组装 VO，避免 N+1 查询：

```java
// 查询时批量获取关联数据，避免 N+1
PageResult<MesWorkOrderDO> pageResult = workOrderMapper.selectPage(reqVO);
Set<Long> itemIds = pageResult.getList().stream()
    .map(MesWorkOrderDO::getItemId).collect(Collectors.toSet());
Map<Long, MesItemDO> itemMap = itemService.getItemMap(itemIds);

// 组装 VO
return new PageResult<>(pageResult.getList().stream().map(order -> {
    MesWorkOrderRespVO vo = BeanUtils.toBean(order, MesWorkOrderRespVO.class);
    MesItemDO item = itemMap.get(order.getItemId());
    if (item != null) {
        vo.setItemName(item.getName());
    }
    return vo;
}).collect(Collectors.toList()), pageResult.getTotal());
```

### 异常处理

- 错误码前缀：`1-xxx-xxx-xxx`
- 具体错误码前缀需查阅 `ErrorCodeConstants.java` 确认

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ErrorCode)`

## 扩展指南

### 新增物料属性

1. **修改数据库表**：在 `mes_md_item` 表中添加新字段
2. **更新 DO 实体**：在 `MesItemDO` 中添加对应属性
3. **更新 VO**：在 `MesItemSaveReqVO` 和 `MesItemRespVO` 中添加字段
4. **更新 Controller**：确保新字段在创建/更新/查询接口中正确处理

### 新增出入库类型

1. **创建出入库表**：参考 `mes_wm_misc_issue` 创建新的出入库主子表
2. **创建 DO 实体**：创建 `XxxDO` 继承 `BaseDO`
3. **创建 Mapper/Service/Controller**：遵循标准 CRUD 模式创建各层代码
4. **集成库存更新**：在 Service 中调用 `MaterialStockService` 更新库存
5. **添加权限配置**：在系统权限中添加 `mes:xxx:create/update/delete/query` 权限

### 新增检验类型

1. **创建检验单表**：参考 `mes_qc_iqc` 创建新的检验主子表
2. **创建 DO/VO/Service/Controller**：遵循标准 CRUD + 主子表模式
3. **集成检验模板**：关联 `QcTemplateDO` 的检验项和指标
4. **集成缺陷管理**：检验不合格时关联 `QcDefectRecordDO`
5. **联动仓库操作**：检验结果触发对应的出入库操作

### 最佳实践

| 实践 | 说明 |
|------|------|
| 状态机校验 | 所有状态变更前校验前置状态，使用 CAS 方式更新防止并发覆盖 |
| VO Assembly | 查询接口批量获取关联实体后组装 VO，避免 N+1 查询 |
| 库存乐观锁 | 出库操作使用 `quantity >= #{outQuantity}` 条件防止库存变为负数 |
| 自动编码防重 | 使用 SELECT FOR UPDATE 锁定编码记录，防止并发生成重复编码 |
| 检验与入库联动 | IQC 合格后才能办理采购入库，不合格走供应商退货 |
| 设备状态联动 | 维修/保养完成后自动恢复设备状态为正常 |
| 事务范围控制 | 只包含写操作，查询移到事务外，避免长事务和锁竞争 |

## 模块依赖

> 模块对 framework starter 及 system 模块 API（`AdminUserApi`、`DictDataApi`、`PostApi`、`RoleApi`）的完整依赖清单见 [README.md](README.md) 的"依赖关系"一节，此处不再重复；下表为 Skill 知识库中登记的依赖明细。

| 类别 | 依赖 | 用途 |
|------|------|------|
| 内部模块 | yudao-module-system / AdminUserApi | 获取用户信息（工位操作员、报工人等） |
| 内部模块 | yudao-module-system / RoleApi | 角色权限校验 |
| 外部库 | MyBatis-Plus | ORM 框架，提供 CRUD 封装，BaseMapperX |
| 外部库 | Swagger/OpenAPI | API 文档注解 |
| 外部库 | MapStruct | VO/DO 对象映射转换 |
| 外部库 | Hutool | Java 工具类库 |

## 关键文件

路径相对于仓库根目录，核心业务逻辑集中在 `service` 层：

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/md/ItemService.java | 物料管理服务接口 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/WorkOrderService.java | 工单管理服务接口，核心状态机 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/TaskService.java | 生产任务服务，甘特图支持 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/CardService.java | 流转卡服务，工序执行跟踪 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/FeedbackService.java | 报工反馈服务，审批流程 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/qc/QcIqcService.java | 来料检验服务 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/dv/MachineryService.java | 设备管理服务 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/dv/RepairService.java | 维修管理服务，状态机 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/wm/MaterialStockService.java | 库存管理服务，出入库核心 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/wm/TransferService.java | 调拨服务，双向库存更新 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/md/AutoCodeService.java | 自动编码服务，策略模式 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/cal/CalPlanService.java | 排班计划服务 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/enums/MesBizTypeConstants.java | 业务类型常量定义 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/enums/ErrorCodeConstants.java | 错误码常量定义 |

## 领域模型

模块按聚合组织核心领域对象，各聚合根通过子实体外键关联维护边界：

| 聚合 | 聚合根 | 包含实体 | 说明 |
|------|--------|----------|------|
| 物料聚合 | ItemDO | ItemDO, ItemBatchConfigDO | ItemDO 是物料聚合根，BatchConfigDO 定义物料的批次生成规则 |
| BOM 聚合 | ProductBomDO | ProductBomDO, Bom 子表 | ProductBomDO 是 BOM 聚合根，定义产品由哪些子物料组成及用量 |
| 工艺路线聚合 | RouteDO | RouteDO, RouteProcessDO, RouteProductDO | RouteDO 是工艺路线聚合根，包含工序列表和适用产品 |
| 工单聚合 | WorkOrderDO | WorkOrderDO, WorkOrderBomDO | WorkOrderDO 是工单聚合根，关联 BOM 和工艺路线 |
| 任务聚合 | TaskDO | TaskDO, TaskIssueDO | TaskDO 是生产任务聚合根，关联工序、工位、设备、操作员 |
| 流转卡聚合 | CardDO | CardDO, CardProcessDO | CardDO 是流转卡聚合根，跟踪各工序的执行情况 |
| 检验单聚合 | QcIqcDO / QcIpqcDO / QcOqcDO / QcRqcDO | 四大检验单 + 检验行 | 四大检验单各自为聚合根，主子表结构 |
| 设备聚合 | MachineryDO | MachineryDO, CheckPlanDO, CheckRecordDO, MaintenRecordDO, RepairDO | MachineryDO 是设备聚合根，关联点检、保养、维修 |
| 仓库聚合 | WarehouseDO | WarehouseDO, WarehouseAreaDO, WarehouseLocationDO | WarehouseDO 是仓库聚合根，包含库区和库位的层级结构 |
| 库存聚合 | MaterialStockDO | MaterialStockDO, BatchDO, BarcodeDO, SnDO | MaterialStockDO 是库存聚合根，按物料/仓库/库位/批次维度管理 |
| 排班聚合 | CalPlanDO | CalPlanDO, CalPlanShiftDO, CalPlanTeamDO, CalTeamDO | CalPlanDO 是排班计划聚合根，关联班次和班组 |
| 自动编码聚合 | AutoCodeRuleDO | AutoCodeRuleDO, AutoCodePartDO, AutoCodeRecordDO | AutoCodeRuleDO 是编码规则聚合根，由零件组合定义编码格式 |

对应的领域服务清单：

| 领域服务 | 说明 |
|---------|------|
| ItemService | 物料管理服务，提供物料的增删改查 |
| ProductBomService | BOM 管理服务，管理产品物料清单 |
| RouteService | 工艺路线服务，管理生产工序流程 |
| WorkOrderService | 工单管理服务，工单状态机流转 |
| TaskService | 生产任务服务，支持甘特图排产 |
| CardService | 流转卡服务，跟踪生产工序执行 |
| FeedbackService | 报工反馈服务，提交/审批报工 |
| QcIqcService / QcIpqcService / QcOqcService / QcRqcService | 四大检验服务，管理来料/过程/出货/退货检验 |
| MachineryService | 设备管理服务，设备台账维护 |
| RepairService | 维修管理服务，维修单状态流转 |
| WarehouseService | 仓库管理服务，仓库/库区/库位层级管理 |
| MaterialStockService | 库存管理服务，出入库、调拨、盘点 |
| AutoCodeService | 自动编码服务，根据规则生成业务单号 |
| CalPlanService | 排班计划服务，工厂日历和班组排班 |

## 设计与架构补充

以下为 Skill 知识库中登记、但 [README.md](README.md) 现有"设计原则"/"设计模式"章节未覆盖的架构要点。

### 补充设计原则

| 原则 | 说明 |
|------|------|
| 状态机模式 | 工单/流转卡/报工/维修/调拨/排班计划等核心实体使用状态机管理状态流转，变更前校验前置状态，使用 CAS 防止并发覆盖（CAS 更新模式：`WHERE status = #{oldStatus}`，应用于状态变更与库存扣减场景） |
| VO Assembly 模式 | 查询接口批量获取关联实体后组装 VO，避免 N+1 查询，提升查询性能（应用位置：controller 层的 get/page 接口） |
| 主子表结构 | BOM、检验单、出入库单、维修单等使用主子表结构，主表记录基本信息，子表记录明细，子表通过外键关联主表 |
| Oracle/PG 兼容 | 使用 `@KeySequence` 注解兼容 Oracle 和 PostgreSQL 的主键生成方式 |
| 跨模块 API 集成 | 通过 AdminUserApi、RoleApi 等接口与 system 模块集成，不直接依赖实现类 |

### 实体基类与枚举组织

- 所有 DO 继承 `BaseDO`，统一包含 `id, creator, createTime, updater, updateTime, deleted` 审计字段；部分表使用 `@KeySequence` 注解兼容 Oracle/PostgreSQL 主键生成。
- 状态枚举集中在 `enums` 包：`WorkOrderStatusEnum`、`CardStatusEnum`、`FeedbackStatusEnum`、`RepairStatusEnum` 等，配合状态机使用。
- `ErrorCodeConstants` 集中定义模块错误码常量；`MesBizTypeConstants` 集中管理业务类型常量（已在 README 设计原则中说明）。
