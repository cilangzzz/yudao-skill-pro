# MES 制造执行代码模式与扩展指南 (mes)

> 本文档移植自模块 Skill 知识库（skill-mes.yaml），提供该模块的代码模式、扩展指南与关键文件索引。模块总体架构、API 索引与数据模型见 [README.md](README.md)。

## 代码模式

### Controller 层规范

Controller 统一使用以下注解组合：

- `@Tag(name = '管理后台 - MES xxx')` — Swagger 文档标签
- `@RestController` — REST 控制器
- `@RequestMapping('/mes/xxx')` — 请求路径前缀（框架统一附加 `/admin-api` 网关前缀）
- `@Validated` — 参数校验
- `@PreAuthorize('@ss.hasPermission('mes:xxx:action')')` — 权限控制

完整示例（以物料产品为例）：

```java
@Tag(name = "管理后台 - MES 物料产品")
@RestController
@RequestMapping("/mes/md/item")
@Validated
public class MesMdItemController {

    @Resource
    private MesMdItemService itemService;

    @PostMapping("/create")
    @Operation(summary = "创建物料产品")
    @PreAuthorize("@ss.hasPermission('mes:md-item:create')")
    public CommonResult<Long> createItem(@Valid @RequestBody MesMdItemSaveReqVO createReqVO) {
        return success(itemService.createItem(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新物料产品")
    @PreAuthorize("@ss.hasPermission('mes:md-item:update')")
    public CommonResult<Boolean> updateItem(@Valid @RequestBody MesMdItemSaveReqVO updateReqVO) {
        itemService.updateItem(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除物料产品")
    @PreAuthorize("@ss.hasPermission('mes:md-item:delete')")
    public CommonResult<Boolean> deleteItem(@RequestParam("id") Long id) {
        itemService.deleteItem(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得物料产品")
    @PreAuthorize("@ss.hasPermission('mes:md-item:query')")
    public CommonResult<MesMdItemRespVO> getItem(@RequestParam("id") Long id) {
        MesMdItemDO item = itemService.getItem(id);
        return success(buildItemVO(item));
    }

    @GetMapping("/page")
    @Operation(summary = "获得物料产品分页")
    @PreAuthorize("@ss.hasPermission('mes:md-item:query')")
    public CommonResult<PageResult<MesMdItemRespVO>> getItemPage(@Valid MesMdItemPageReqVO pageReqVO) {
        PageResult<MesMdItemDO> pageResult = itemService.getItemPage(pageReqVO);
        return success(new PageResult<>(buildItemVOList(pageResult.getList()), pageResult.getTotal()));
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

状态机流转示例（以生产工单确认为例，变更前校验前置状态）：

```java
// MesProWorkOrderServiceImpl#confirmWorkOrder
@Override
@Transactional(rollbackFor = Exception.class)
public void confirmWorkOrder(Long id) {
    // 1.1 校验存在
    MesProWorkOrderDO workOrder = validateWorkOrderExists(id);
    // 1.2 只有草稿状态才能确认
    if (ObjUtil.notEqual(workOrder.getStatus(), MesProWorkOrderStatusEnum.PREPARE.getStatus())) {
        throw exception(PRO_WORK_ORDER_NOT_PREPARE);
    }
    // 2. 更新状态为已确认
    workOrderMapper.updateById(new MesProWorkOrderDO().setId(id)
            .setStatus(MesProWorkOrderStatusEnum.CONFIRMED.getStatus()));
}
```

状态取值集中在 `enums/{域}/` 下的枚举类（`MesProWorkOrderStatusEnum`：0-草稿、1-已确认、2-已完成、3-已取消），流转规则以「校验前置状态 + 抛业务错误码」的形式写在 Service 中。

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

具体示例（物料产品分页查询）：

```java
public interface MesMdItemMapper extends BaseMapperX<MesMdItemDO> {
    default PageResult<MesMdItemDO> selectPage(MesMdItemPageReqVO reqVO, Collection<Long> itemTypeIds) {
        return selectPage(reqVO, new LambdaQueryWrapperX<MesMdItemDO>()
                .likeIfPresent(MesMdItemDO::getCode, reqVO.getCode())
                .likeIfPresent(MesMdItemDO::getName, reqVO.getName())
                .inIfPresent(MesMdItemDO::getItemTypeId, itemTypeIds)
                .eqIfPresent(MesMdItemDO::getStatus, reqVO.getStatus())
                .betweenIfPresent(MesMdItemDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(MesMdItemDO::getId));
    }
}
```

### 多数据库 SQL 兼容（MySQL / PostgreSQL / Oracle / SQL Server）

MES 的 SQL 需同时运行在 MySQL、PostgreSQL、Oracle、SQL Server 等数据库上。新增/修改 SQL 时**禁止硬编码 MySQL 专有函数**，统一使用框架提供的方言工具（`SqlDialectUtils`）、`BaseMapperX` 与 MyBatis-Plus 标准 API；具体踩坑与失败场景见 [pitfalls.md](pitfalls.md)。

#### 1. 按日聚合：SqlDialectUtils.formatDate

XML 中通过 OGNL 静态方法调用注入日期格式化片段，框架按**执行时路由到的数据源**自动输出对应方言：

```xml
<!-- MesHomeStatisticsMapper.xml#selectDailyFeedbackTrend -->
SELECT ${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@formatDate('feedback_time')} AS statDate,
       COALESCE(SUM(feedback_quantity), 0)    AS quantity,
       COALESCE(SUM(qualified_quantity), 0)   AS qualifiedQuantity,
       COALESCE(SUM(unqualified_quantity), 0) AS unqualifiedQuantity
FROM mes_pro_feedback
WHERE deleted = 0
  AND feedback_time >= #{beginTime}
GROUP BY ${@cn.iocoder.yudao.framework.mybatis.core.util.SqlDialectUtils@formatDate('feedback_time')}
ORDER BY statDate
```

| 方言 | `formatDate('feedback_time')` 输出 |
|------|-----------------------------------|
| MySQL / 其他默认 | `DATE_FORMAT(feedback_time, '%Y-%m-%d')` |
| PostgreSQL / Oracle | `TO_CHAR(feedback_time, 'YYYY-MM-DD')` |
| SQL Server | `CONVERT(varchar(10), feedback_time, 23)` |

约束：
- 列名必须是**代码中写死的常量**，`formatDate` 内部经 `MyBatisUtils.isSafeColumnName` 白名单校验，非法列名抛 `IllegalArgumentException`；业务值仍必须用 `#{}` 绑定，禁止把用户输入拼到列名位置。
- `GROUP BY` 必须复用与 `SELECT` 相同的 `formatDate` 表达式，`ORDER BY` 才能引用输出别名 `statDate`。
- 空值聚合统一用标准 `COALESCE(...)`，不要再用 MySQL 专有的 `IFNULL`。
- 返回 `Map` 的查询依赖 `CaseInsensitiveResultMap` 才能做到列别名大小写不敏感匹配（如 `row.get("statDate")`）。

#### 2. 限量取首条：BaseMapperX.selectFirstOne

```java
// MesWmBatchMapper#selectFirst：按 ID 升序取第一条
query.orderByAsc(MesWmBatchDO::getId);
return selectFirstOne(query);
```

`selectFirstOne(query)` / `selectListLimitN(query, n)` 走 MyBatis-Plus 分页插件，按方言生成 `LIMIT` / `ROWNUM` / `OFFSET FETCH`，且**不执行 COUNT**。不要再对同一个 `queryWrapper` 追加 `last("LIMIT 1")`；SQL Server 的分页语句要求必须有 `ORDER BY`，因此排序条件不可省略。

#### 3. 数值累加：LambdaUpdateWrapper#setIncrBy

```java
// MesProTaskMapper#updateProducedQuantity / MesProWorkOrderMapper#updateProducedQuantity
update(null, new LambdaUpdateWrapper<MesProTaskDO>()
        .eq(MesProTaskDO::getId, id)
        .setIncrBy(MesProTaskDO::getProducedQuantity, incrProducedQuantity)
        .setIncrBy(MesProTaskDO::getQualifyQuantity, incrQualifyQuantity)
        .setIncrBy(MesProTaskDO::getUnqualifyQuantity, incrUnqualifyQuantity));
```

生成的 SQL 为标准的 `produced_quantity = produced_quantity + ?`，不再拼接 `setSql("... IFNULL(produced_quantity, 0) + n")`。**注意**：`setIncrBy` 不再做 NULL 兜底，累加正确性依赖列本身为 `NOT NULL DEFAULT 0`（单测建表已同步，见 [pitfalls.md](pitfalls.md)）。

#### 4. 条件与类型写法对照

| 场景 | 错误/旧写法 | 正确/新写法 | 原因 |
|------|------------|------------|------|
| bit(1) 布尔列比较 | `l.iqc_check_flag = 1` | `<bind name="trueValue" value="true"/>` + `l.iqc_check_flag = #{trueValue}` | PostgreSQL 等库不接受 bit 与数字直接比较 |
| tinyint(1) 列比较 | 绑定 Boolean | `sl.oqc_check_flag = 1` 保持数值 | OQC 的 `oqc_check_flag` 是 tinyint(1)，按数值比较 |
| UNION 无值列 | `NULL AS workOrderId` | `CASE WHEN 1 = 0 THEN <本分支 bigint 列> END AS workOrderId` | 避免 UNION 按首分支推断类型导致 bigint 转换异常 |
| 模糊查询 | `LIKE CONCAT('%', #{code}, '%')` | `<bind name="codeLike" value="'%' + code + '%'"/>` + `LIKE #{codeLike}` | 兼容不支持 CONCAT 的数据库 |

对应实现见 `MesQcPendingInspectMapper.xml`：IQC/RQC 分支使用 `#{trueValue}` 绑定 Boolean，OQC 分支保留 `= 1`，6 个 UNION 分支的 `workOrderId/workstationId/taskId/clientId/vendorId` 均以带类型 NULL 占位。

#### 5. 方言识别与失败语义

`SqlDialectUtils` 的方言按**执行时路由到的数据源实例**识别并缓存（事务内复用事务连接，非事务按数据源缓存）；读取元数据失败或数据源不可用会抛 `IllegalStateException("获取数据库方言失败")`。新增涉及日期、JSON、行数限制的 SQL 片段时，应复用 `SqlDialectUtils` 而不要硬编码 MySQL 函数。

### VO Assembly 模式

查询接口批量获取关联实体后组装 VO，避免 N+1 查询（示例取自 `MesProWorkOrderController#buildWorkOrderRespVOList`）：

```java
// 1. 批量获取关联数据
Map<Long, MesMdItemDO> itemMap = itemService.getItemMap(
        convertSet(list, MesProWorkOrderDO::getProductId));
Map<Long, MesMdClientDO> clientMap = clientService.getClientMap(
        convertSet(list, MesProWorkOrderDO::getClientId));

// 2. 拼接 VO（关联缺失时保持 null，不抛错）
return BeanUtils.toBean(list, MesProWorkOrderRespVO.class, vo -> {
    MapUtils.findAndThen(itemMap, vo.getProductId(), item ->
            vo.setProductName(item.getName()).setProductCode(item.getCode()));
    MapUtils.findAndThen(clientMap, vo.getClientId(), client ->
            vo.setClientName(client.getName()).setClientCode(client.getCode()));
});
```

### 异常处理

- 错误码段号：`1_040_000_000`（mes 模块），统一在 `enums/ErrorCodeConstants.java` 中定义，格式为 `1-040-{子域段}-{序号}`。
- 抛错：`throw exception(ErrorCodeConstants.XXX)`；新增错误码时在同一子域段内分配未被占用的序号，不要跨子域复用。

| 子域 | 段号 | 代表错误码 |
|------|------|-----------|
| 主数据 (md) | `1-040-10x-xxx`（物料分类 100、计量单位 101、物料 102、客户 103、供应商 104、车间/工作站 105/106、BOM/SOP/SIP 107-109、编码规则 110） | `MD_ITEM_NOT_EXISTS` = 1_040_102_000 |
| 排班日历 (cal) | `1-040-2xx-xxx`（计划班次 200、班组 201、排班计划 202、假期 203） | `CAL_TEAM_CODE_DUPLICATE` = 1_040_201_001 |
| 设备管理 (dv) | `1-040-3xx-xxx`（设备类型 300、设备台账 301、点检方案 302、维修 303、项目 304、保养 305、点检记录 306） | `DV_MACHINERY_NOT_EXISTS` = 1_040_301_000 |
| 工装工具 (tm) | `1-040-4xx-xxx`（工具类型 400、工具台账 401） | `TM_TOOL_NOT_EXISTS` = 1_040_401_000 |
| 生产管理 (pro) | `1-040-5xx-xxx`（工序 500、工艺路线 501 等） | 见 `ErrorCodeConstants` |
| 质量管理 (qc) | `1-040-6xx-xxx` | 见 `ErrorCodeConstants` |
| 仓库管理 (wm) | `1-040-7xx-xxx`（批次管理 717 等） | `WM_BATCH_NOT_EXISTS` = 1_040_717_014 |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ErrorCode)`

## 扩展指南

### 新增物料属性

1. **修改数据库表**：在 `mes_md_item` 表中添加新字段
2. **更新 DO 实体**：在 `MesMdItemDO` 中添加对应属性
3. **更新 VO**：在 `MesMdItemSaveReqVO` 和 `MesMdItemRespVO` 中添加字段
4. **更新 Controller**：确保新字段在创建/更新/查询接口中正确处理

### 新增出入库类型

1. **创建出入库表**：参考 `mes_wm_misc_issue` 创建新的出入库主子表
2. **创建 DO 实体**：创建 `XxxDO` 继承 `BaseDO`
3. **创建 Mapper/Service/Controller**：遵循标准 CRUD 模式创建各层代码
4. **集成库存更新**：在 Service 中调用 `MesWmTransactionService#createTransaction`（内部转调 `MesWmMaterialStockService#updateMaterialStockQuantity` 更新台账并写 `mes_wm_transaction` 流水）
5. **添加权限配置**：在系统权限中添加 `mes:xxx:create/update/delete/query` 权限

### 新增检验类型

1. **创建检验单表**：参考 `mes_qc_iqc` 创建新的检验主子表
2. **创建 DO/VO/Service/Controller**：遵循标准 CRUD + 主子表模式
3. **集成检验模板**：关联 `MesQcTemplateDO` 的检验项和指标
4. **集成缺陷管理**：检验不合格时关联 `MesQcDefectRecordDO`
5. **联动仓库操作**：检验结果触发对应的出入库操作

### 最佳实践

| 实践 | 说明 |
|------|------|
| 状态机校验 | 状态变更前先校验前置状态，非法流转直接抛业务错误码（如 `MesProWorkOrderServiceImpl#confirmWorkOrder`）；更新为普通 `updateById`，并发安全依赖事务与行锁，未使用乐观锁 |
| VO Assembly | 查询接口批量获取关联实体后组装 VO，避免 N+1 查询 |
| 库存乐观锁 | 出库时 `MesWmMaterialStockMapper#updateQuantity` 追加 `quantity >= |变更量|` 条件（`checkFlag=true` 且为负数变更时），防止库存变为负数；影响行数为 0 时抛 `WM_MATERIAL_STOCK_INSUFFICIENT` |
| 自动编码防重 | 流水号分段由 `MesMdAutoCodeRedisDAO` 在 Redis 内原子自增，保证并发生成不重复；模块内无 `SELECT FOR UPDATE` 写法 |
| 检验与入库联动 | IQC 合格后才能办理采购入库，不合格走供应商退货 |
| 设备状态联动 | 维修/保养完成后自动恢复设备状态为正常 |
| 事务范围控制 | 只包含写操作，查询移到事务外，避免长事务和锁竞争 |
| 方言化 SQL | 日期格式化、行数限制、空值聚合统一走 `SqlDialectUtils` / `BaseMapperX` / `COALESCE`，禁止硬编码 `DATE_FORMAT`、`IFNULL`、`LIMIT` |
| 布尔列按类型比较 | `bit(1)` 列绑定 Boolean（`#{trueValue}`），`tinyint(1)` 列才与数值 `1` 比较 |
| UNION 列类型一致 | 多分支 UNION 中表示"无值"的列必须用 `CASE WHEN 1 = 0 THEN <本分支同类型列> END` 产生带类型 NULL |

## 模块依赖

> 模块对 framework starter 及 system 模块 API（`AdminUserApi`、`DictDataApi`、`PostApi`、`RoleApi`）的完整依赖清单见 [README.md](README.md) 的"依赖关系"一节，此处不再重复；下表为 Skill 知识库中登记的依赖明细。

| 类别 | 依赖 | 用途 |
|------|------|------|
| 内部模块 | yudao-module-system / AdminUserApi | 获取用户信息（工位操作员、报工人等） |
| 内部模块 | yudao-module-system / RoleApi | 角色权限校验 |
| 内部模块 | yudao-module-system / PostApi | 工作站人力资源岗位信息回显 |
| 内部模块 | yudao-module-system / DictDataApi | 质检指标字典值回显 |
| 外部库 | MyBatis-Plus | ORM 框架，提供 CRUD 封装，BaseMapperX |
| 外部库 | Swagger/OpenAPI | API 文档注解 |
| 外部库 | Hutool | Java 工具类库（CollUtil、StrUtil、ObjUtil 等） |
| 外部库 | Spring Data Redis | 编码流水号自增（MesMdAutoCodeRedisDAO） |

## 关键文件

路径相对于仓库根目录，核心业务逻辑集中在 `service` 层：

| 文件路径 | 说明 |
|---------|------|
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/md/item/MesMdItemService.java | 物料产品服务接口 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/workorder/MesProWorkOrderService.java | 生产工单服务接口，核心状态机（确认/完成/取消） |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/task/MesProTaskService.java | 生产任务服务，含甘特图数据查询 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/card/MesProCardService.java | 流转卡服务，工序执行跟踪 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/pro/feedback/MesProFeedbackService.java | 报工反馈服务，提交/审批报工 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/qc/iqc/MesQcIqcService.java | 来料检验服务 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/dv/machinery/MesDvMachineryService.java | 设备台账服务 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/dv/repair/MesDvRepairService.java | 维修工单服务，状态机 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/wm/materialstock/MesWmMaterialStockService.java | 库存台账服务，出入库核心 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/wm/transaction/MesWmTransactionService.java | 库存事务流水服务，统一写 `mes_wm_transaction` |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/wm/transfer/MesWmTransferService.java | 转移（调拨）服务，双向库存更新 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/md/autocode/MesMdAutoCodeRecordService.java | 自动编码服务入口（`generateAutoCode`），策略模式 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/service/cal/plan/MesCalPlanService.java | 排班计划服务 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/enums/MesBizTypeConstants.java | 业务类型常量定义 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/enums/MesOrderStatusConstants.java | 单据状态常量定义 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/enums/ErrorCodeConstants.java | 错误码常量定义 |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/dal/redis/md/autocode/MesMdAutoCodeRedisDAO.java | 编码流水号 Redis 自增（并发安全） |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/dal/mysql/home/MesHomeStatisticsMapper.java | 首页统计 Mapper（按日聚合返回 `statDate`） |
| yudao-module-mes/src/main/resources/mapper/home/MesHomeStatisticsMapper.xml | 首页统计 SQL（`SqlDialectUtils.formatDate` + `COALESCE` 方言化聚合） |
| yudao-module-mes/src/main/resources/mapper/qc/pendinginspect/MesQcPendingInspectMapper.xml | 待检任务 6 分支 UNION 查询（bit(1) 绑定 Boolean、带类型 NULL） |
| yudao-module-mes/src/main/java/cn/iocoder/yudao/module/mes/dal/mysql/wm/batch/MesWmBatchMapper.java | 批次 FIFO 查询（`selectFirstOne` + `orderByAsc(id)`） |

## 领域模型

模块按聚合组织核心领域对象，各聚合根通过子实体外键关联维护边界：

| 聚合 | 聚合根 | 包含实体 | 说明 |
|------|--------|----------|------|
| 物料聚合 | MesMdItemDO | MesMdItemTypeDO、MesMdItemBatchConfigDO、MesMdProductBomDO、MesMdProductSipDO、MesMdProductSopDO | MesMdItemDO 是物料聚合根，分类树 + 批次属性/BOM/SIP/SOP 扩展 |
| 工艺路线聚合 | MesProRouteDO | MesProRouteProcessDO、MesProRouteProductDO、MesProRouteProductBomDO | 工艺路线 → 工序 → 适用产品 → 产品 BOM |
| 工单聚合 | MesProWorkOrderDO | MesProWorkOrderBomDO、MesProTaskDO、MesProFeedbackDO、MesProCardDO | 工单 → BOM/任务/报工/流转卡级联 |
| 任务聚合 | MesProTaskDO | MesProTaskIssueDO | 生产任务 → 投料 |
| 流转卡聚合 | MesProCardDO | MesProCardProcessDO | 流转卡跟踪各工序执行情况 |
| 检验单聚合 | MesQcIqcDO / MesQcIpqcDO / MesQcOqcDO / MesQcRqcDO | 各 `*LineDO`、MesQcIndicatorResultDO、MesQcIndicatorResultDetailDO | 四大检验单各自为聚合根，主子表结构 |
| 设备聚合 | MesDvMachineryDO | MesDvMachineryTypeDO、MesDvCheckPlanDO、MesDvCheckRecordDO、MesDvMaintenRecordDO、MesDvRepairDO | 设备台账关联点检、保养、维修 |
| 仓库聚合 | MesWmWarehouseDO | MesWmWarehouseLocationDO、MesWmWarehouseAreaDO | 仓库 → 库区 → 库位三级结构 |
| 库存聚合 | MesWmMaterialStockDO | MesWmBatchDO、MesWmBarcodeDO、MesWmSnDO、MesWmTransactionDO | 库存台账按物料/仓库/库位/批次维度管理，变动写事务流水 |
| 排班聚合 | MesCalPlanDO | MesCalPlanShiftDO、MesCalPlanTeamDO、MesCalTeamDO、MesCalTeamMemberDO、MesCalTeamShiftDO | 排班计划 → 计划班次/计划班组 → 班组 → 班组成员/班组排班 |
| 自动编码聚合 | MesMdAutoCodeRuleDO | MesMdAutoCodePartDO、MesMdAutoCodeRecordDO | 编码规则由分段定义，生成记录留痕 |
| 工作站聚合 | MesMdWorkstationDO | MesMdWorkstationMachineDO、MesMdWorkstationToolDO、MesMdWorkstationWorkerDO | 工作站 → 设备/工装/人员资源 |

对应的领域服务清单：

| 领域服务 | 说明 |
|---------|------|
| MesMdItemService | 物料产品服务，提供物料的增删改查 |
| MesMdProductBomService | BOM 管理服务，管理产品物料清单 |
| MesProRouteService | 工艺路线服务，管理生产工序流程 |
| MesProWorkOrderService | 生产工单服务，工单状态机流转 |
| MesProTaskService | 生产任务服务，支持甘特图排产 |
| MesProCardService | 流转卡服务，跟踪生产工序执行 |
| MesProFeedbackService | 报工反馈服务，提交/审批报工 |
| MesQcIqcService / MesQcIpqcService / MesQcOqcService / MesQcRqcService | 四大检验服务，管理来料/过程/出货/退货检验 |
| MesDvMachineryService | 设备台账服务，设备档案维护 |
| MesDvRepairService | 维修管理服务，维修单状态流转 |
| MesWmWarehouseService | 仓库管理服务，仓库/库区/库位层级管理 |
| MesWmMaterialStockService | 库存台账服务，出入库、调拨、盘点 |
| MesWmTransactionService | 库存事务流水服务，统一登记数量变动 |
| MesMdAutoCodeRecordService | 自动编码服务，根据规则生成业务单号 |
| MesCalPlanService | 排班计划服务，工厂日历和班组排班 |

## 设计与架构补充

以下为 Skill 知识库中登记、但 [README.md](README.md) 现有"设计原则"/"设计模式"章节未覆盖的架构要点。

### 补充设计原则

| 原则 | 说明 |
|------|------|
| 状态机模式 | 工单/流转卡/报工/维修/调拨/排班计划等核心实体使用状态机管理状态流转，变更前校验前置状态（如 `MesProWorkOrderServiceImpl#confirmWorkOrder`）；状态更新为普通 `updateById`，未使用乐观锁/CAS，并发安全依赖事务与行锁；库存扣减为唯一例外，`MesWmMaterialStockMapper#updateQuantity` 在 `checkFlag=true` 且负数变更时追加 `quantity >= |变更量|` 条件防负库存 |
| VO Assembly 模式 | 查询接口批量获取关联实体后组装 VO，避免 N+1 查询，提升查询性能（应用位置：controller 层的 get/page 接口） |
| 主子表结构 | BOM、检验单、出入库单、维修单等使用主子表结构，主表记录基本信息，子表记录明细，子表通过外键关联主表 |
| Oracle/PG 兼容 | 使用 `@KeySequence` 注解兼容 Oracle 和 PostgreSQL 的主键生成方式 |
| 跨模块 API 集成 | 通过 AdminUserApi、RoleApi 等接口与 system 模块集成，不直接依赖实现类 |

### 实体基类与枚举组织

- 所有 DO 继承 `BaseDO`，统一包含 `id, creator, createTime, updater, updateTime, deleted` 审计字段；部分表使用 `@KeySequence` 注解兼容 Oracle/PostgreSQL 主键生成。
- 状态枚举集中在 `enums` 包：`WorkOrderStatusEnum`、`CardStatusEnum`、`FeedbackStatusEnum`、`RepairStatusEnum` 等，配合状态机使用。
- `ErrorCodeConstants` 集中定义模块错误码常量；`MesBizTypeConstants` 集中管理业务类型常量（已在 README 设计原则中说明）。
