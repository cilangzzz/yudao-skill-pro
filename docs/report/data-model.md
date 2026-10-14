# 数据模型详情

> report 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。

report 模块是数据可视化模块，基于积木报表（JimuReport）与积木仪表盘（JimuBI）提供报表与大屏设计能力，并内置 GoView 大屏项目管理与数据集查询 API。模块自身的持久化层非常轻量：**仅 1 个 DO（`GoViewProjectDO`，对应 1 张表 `report_go_view_project`）**，积木报表/仪表盘所需的 `jimu_*`、`onl_drag_*` 等表均由第三方 starter（`jimureport-spring-boot-starter`，版本锁定 2.3.4）自动建表并维护，不在本仓库 DO 层管理。

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO        ← 框架通用基类（yudao-spring-boot-starter-mybatis）
│   ├── creator      String          创建者，存 SysUser 用户编号（String 类型预留扩展性，INSERT 自动填充）
│   ├── createTime   LocalDateTime   创建时间（INSERT 自动填充）
│   ├── updater      String          更新者，存 SysUser 用户编号（INSERT_UPDATE 自动填充）
│   ├── updateTime   LocalDateTime   最后更新时间（INSERT_UPDATE 自动填充）
│   └── deleted      Boolean         是否删除（@TableLogic 逻辑删除，查询自动拼接 deleted = 0）
│
└── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO       ← 多租户基类（yudao-spring-boot-starter-biz-tenant）
        └── tenantId  Long            多租户编号（配合租户插件自动拼接租户过滤条件）

cn.iocoder.yudao.module.report.dal.dataobject.goview.GoViewProjectDO
        └── 继承 BaseDO（不继承 TenantBaseDO）
```

**使用规则**：

- `BaseDO`：通用审计字段基类，适用于无多租户隔离诉求的表。report 模块唯一的 `GoViewProjectDO` 即继承它 —— 大屏项目按**创建人**隔离（`creator` 字段实现"我的项目"过滤），而非按租户隔离，因此表中没有 `tenant_id` 列。
- `TenantBaseDO`：需要租户隔离的表使用，新增 `tenantId` 字段并由租户插件自动过滤。**report 模块当前没有任何 DO 使用该基类**；若后续需要将大屏项目纳入租户体系，可让 `GoViewProjectDO` 改继承 `TenantBaseDO` 并补 `tenant_id` 列。
- `BaseDO` 同时实现 `TransPojo`（Easy-Trans 简单翻译模式），并提供 `clean()` 方法在落库前清空前端可能传入的审计字段。

## 2. 核心 DO 实体

### 2.1 GoView 大屏项目聚合

模块内唯一的业务聚合：一个大屏可视化项目对应一条 `GoViewProjectDO` 记录，大屏的全部图表配置以 JSON 字符串整体存放在 `content` 字段中（无子表拆分）。

#### GoViewProjectDO (report_go_view_project)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|------|
| id | Long | id | 编号，数据库自增主键（`@TableId`） |
| name | String | name | 项目名称 |
| picUrl | String | pic_url | 预览图片 URL（大屏缩略图） |
| content | String | content | 报表内容，GoView 大屏 JSON 配置，使用字符串整体存储 |
| status | Integer | status | 发布状态，复用框架 `CommonStatusEnum`：0 - 已发布、1 - 未发布 |
| remark | String | remark | 项目备注 |
| creator | String | creator | 创建者（继承自 BaseDO），存 SysUser 用户编号，"我的项目"过滤依据 |
| createTime | LocalDateTime | create_time | 创建时间（继承自 BaseDO，自动填充） |
| updater | String | updater | 更新者（继承自 BaseDO，自动填充） |
| updateTime | LocalDateTime | update_time | 最后更新时间（继承自 BaseDO，自动填充） |
| deleted | Boolean | deleted | 逻辑删除标记（继承自 BaseDO，`@TableLogic`） |

**继承**: `BaseDO`（未继承 `TenantBaseDO`，无 `tenant_id` 列，非多租户表）

**索引**:

- 主键：`id`（自增）。
- 无其他唯一索引或普通索引（仓库内仅有 H2 测试建表脚本 `yudao-module-report/src/test/resources/sql/create_tables.sql`，其中仅声明 `PRIMARY KEY ("id")`）。
- "我的项目"过滤通过 `creator` 字段等值查询实现（`GoViewProjectMapper` 按当前登录用户编号筛选），未单独建索引，数据量大时可视情况补 `creator` 普通索引。
- 类上标注 `@KeySequence("report_go_view_project_seq")`，仅用于 Oracle、PostgreSQL、Kingbase、DB2、H2 等数据库的序列主键自增，MySQL 下不生效；`@TableName(autoResultMap = true)` 开启自动结果映射以支持 TypeHandler。

### 2.2 VO 数据传输对象

模块 VO 全部位于 `controller/admin/goview/vo/` 下，分 project（项目管理）与 data（数据查询）两组，通过 `GoViewProjectConvert`（MapStruct）与 DO 互转：

| VO | 层级 | 字段 | 说明 |
|----|------|------|------|
| GoViewProjectCreateReqVO | 请求 | name（必填） | 创建大屏项目，仅传名称 |
| GoViewProjectUpdateReqVO | 请求 | id（必填）、name、status、content、picUrl、remark | 更新项目；`status` 用 `@InEnum(CommonStatusEnum.class)` 校验取值 |
| GoViewProjectRespVO | 响应 | id、name、status、content、picUrl、remark、creator、createTime | 项目详情/列表响应，额外返回 creator 与 createTime |
| GoViewDataGetBySqlReqVO | 请求 | sql（必填） | 按原生 SQL 查询图表数据源 |
| GoViewDataRespVO | 响应 | dimensions（List\<String\>）、source（List\<Map\<String, Object\>\>） | GoView 图表数据格式：维度列表 + 明细行 |

> 注意：`GoViewDataController` 的两个端点使用 `@RequestMapping` 未限定 HTTP 方法（任意方法均可访问），且直接执行前端传入的 SQL；`GoViewProjectUpdateReqVO` 中 `name` 未加 `@NotEmpty`，与 CreateReqVO 的校验强度不一致，使用时需留意。

## 3. 实体关系

report 模块内部为**单表单聚合**结构，无表间外键；与外部模块和第三方表均为逻辑关联：

```
                ┌──────────────────────────────┐
                │  BaseDO（框架基类，5 个审计字段）│
                └──────────────┬───────────────┘
                               │ 继承
                ┌──────────────▼───────────────┐
                │        GoViewProjectDO       │
                │    report_go_view_project    │
                │  （大屏项目，content 存 JSON）  │
                └──┬───────────────────────┬───┘
     creator 逻辑关联│                       │ JSON 配置渲染
        （非外键）    │                       │
        ┌───────────▼────────┐    ┌──────────▼──────────────────┐
        │ system_users 用户表 │    │ GoView 前端大屏（Vue 组件）   │
        │（yudao-module-system）│  └─────────────────────────────┘
        └────────────────────┘

  第三方表（jimureport-spring-boot-starter 自建自管，本仓库无 DO）：
  ┌─────────────────────┐        ┌─────────────────────┐
  │ jimu_*（积木报表）    │        │ onl_drag_*（积木仪表盘）│
  └──────────┬──────────┘        └──────────┬──────────┘
             │ starter 内部读写               │ 通过 IOnlDragExternalService
             │                              │ 桥接（JmOnlDragExternalServiceImpl）
             └──────────────┬───────────────┘
                            │ HTTP 端点 /jmreport/**、/drag/**、/jimubi/**
                ┌───────────▼────────────┐
                │ JmReportTokenServiceImpl │← token 校验（OAuth2TokenCommonApi）
                │ / SecurityConfiguration  │← permitAll 放行
                └────────────────────────┘
```

关系说明：

- **GoViewProjectDO → system_users（逻辑关联）**：`creator` 字段存创建人用户编号，用于"我的项目"过滤，无数据库外键约束；用户鉴权与权限校验依赖上游 `yudao-module-system` 的 `PermissionApi` 及 framework common biz 的 `OAuth2TokenCommonApi`/`PermissionCommonApi`。
- **GoViewProjectDO ↔ jimu_*/onl_drag_*（集成关系，非数据关系）**：积木报表/仪表盘的自建表由 starter 维护，与 `report_go_view_project` 之间无外键、无关联查询。本模块通过 `JmReportTokenServiceImpl`（为积木端点提供登录态）、`JmOnlDragExternalServiceImpl`（为积木仪表盘提供字典/日志桥接，当前均为默认实现）接入。
- **GoView 数据查询无落库**：`GoViewDataController` 的 SQL 查询端点直接执行 SQL 返回 `GoViewDataRespVO`，不产生新的持久化数据。

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|------|----|------|
| report_go_view_project | GoViewProjectDO | GoView 大屏项目表，一个大屏项目一条记录，JSON 配置整体存于 content 字段 |

> 附注：积木报表/仪表盘由 starter 自建自管的 `jimu_*`（报表）、`onl_drag_*`（仪表盘拖拽设计）等表，表结构定义在第三方 jar 内，不属于本模块 DO 层管理范围，故不计入上表。
