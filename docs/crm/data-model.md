# 数据模型详情

> crm 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。共 21 张表，全部以 `crm_` 前缀命名，围绕「线索 → 客户 → 联系人 → 商机 → 合同 → 回款」销售主线展开，配套跟进记录、行级数据权限（crm_permission）、负责人变更记录与业绩目标；租户隔离不在 DO 层声明，由 biz-tenant 组件在 SQL 层统一处理。

---

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO          （框架通用基类）
├── creator        String          创建者（用户编号，字符串预留扩展性，INSERT 时自动填充）
├── createTime     LocalDateTime   创建时间（INSERT 时自动填充）
├── updater        String          更新者（INSERT/UPDATE 时自动填充）
├── updateTime     LocalDateTime   最后更新时间（INSERT/UPDATE 时自动填充）
└── deleted        Boolean         逻辑删除标记（@TableLogic，查询自动过滤）
    │
    └── crm 模块全部 21 个 DO（直接继承 BaseDO，模块内不使用 TenantBaseDO）
        ├── 销售主线
        │   ├── CrmClueDO                线索（crm_clue）
        │   ├── CrmCustomerDO            客户（crm_customer）
        │   ├── CrmContactDO             联系人（crm_contact）
        │   ├── CrmBusinessDO            商机（crm_business）
        │   ├── CrmContractDO            合同（crm_contract）
        │   ├── CrmReceivableDO          回款（crm_receivable）
        │   └── CrmReceivablePlanDO      回款计划（crm_receivable_plan）
        ├── 产品
        │   ├── CrmProductDO             产品（crm_product）
        │   └── CrmProductCategoryDO     产品分类（crm_product_category）
        ├── 业务关联表
        │   ├── CrmContactBusinessDO     联系人 ↔ 商机关联（crm_contact_business）
        │   ├── CrmBusinessProductDO     商机 ↔ 产品关联（crm_business_product）
        │   └── CrmContractProductDO     合同 ↔ 产品关联（crm_contract_product）
        ├── 商机状态配置
        │   ├── CrmBusinessStatusTypeDO  商机状态组（crm_business_status_type）
        │   └── CrmBusinessStatusDO      商机状态（crm_business_status）
        └── 公共支撑
            ├── CrmFollowUpRecordDO      跟进记录（crm_follow_up_record）
            ├── CrmPermissionDO          行级数据权限（crm_permission）
            ├── CrmOwnerRecordDO         负责人变更记录（crm_owner_record）
            ├── CrmCustomerPoolConfigDO  公海规则（crm_customer_pool_config）
            ├── CrmCustomerLimitConfigDO 客户数上限规则（crm_customer_limit_config）
            ├── CrmContractConfigDO      合同到期提醒配置（crm_contract_config）
            └── CrmPerformanceConfigDO   业绩目标（crm_performance_config）
```

**使用规则**：

| 场景 | 基类 | crm 模块实例 |
|-----|------|-------------|
| 模块内全部业务表 | `BaseDO` | 21 个 DO 全部直接继承，无例外 |
| 多租户表 | —（不使用 `TenantBaseDO`） | crm 各表不声明 `tenantId` 字段，租户隔离由 `yudao-spring-boot-starter-biz-tenant` 的租户拦截器在 SQL 层自动拼接 `tenant_id` 条件实现（建表 DDL 中仍需包含 `tenant_id` 列） |
| 数据归属控制 | —（不用基类表达） | 不靠基类区分归属，而是 `owner_user_id`（负责人）+ `crm_permission` 行级权限表双轨控制 |

通用约定：

- 主键统一为 `id`（`@TableId`，BIGINT 自增），并逐一声明 `@KeySequence("crm_xxx_seq")`，供 Oracle、PostgreSQL、Kingbase、DB2、H2 等数据库用序列模拟主键自增；MySQL 下不生效（直接走自增列）。
- 跟进记录、数据权限、负责人变更（以及操作日志查询）共用 `CrmBizTypeEnum` 表达业务对象类型：1 线索、2 客户、3 联系人、4 商机、5 合同、6 产品、7 回款、8 回款计划。
- 金额字段（价格/总额）除 `CrmContractDO.totalPrice` 的源码注释写作「单位：分」外，其余均注释为「单位：元」，类型为 `BigDecimal`。

---

## 2. 核心 DO 实体

按业务聚合分为七组。21 个 DO 全部详细展开。

> 索引说明：仓库内未包含 crm 的建表 DDL（`sql/mysql/ruoyi-vue-pro.sql` 不含 crm 表），下文「索引」仅描述主键与 DO/Service 层体现的高频查询键，不虚构数据库唯一/普通索引。

### 2.1 线索与客户聚合

线索（clue）是未确认的销售前潜在客户，转化后（`transformStatus = true`）落为正式客户（customer）并回写 `customerId`；两者字段高度同构（联系方式、地区、行业/等级/来源字典一致）。

#### CrmClueDO (crm_clue)

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| name | String | name | 线索名称 |
| followUpStatus | Boolean | follow_up_status | 跟进状态 |
| contactLastTime | LocalDateTime | contact_last_time | 最后跟进时间 |
| contactLastContent | String | contact_last_content | 最后跟进内容 |
| contactNextTime | LocalDateTime | contact_next_time | 下次联系时间 |
| ownerUserId | Long | owner_user_id | 负责人用户编号，关联 AdminUserDO#getId() |
| transformStatus | Boolean | transform_status | 转化状态（true 表示已转换为客户，会更新 customerId） |
| customerId | Long | customer_id | 客户编号，关联 CrmCustomerDO#getId() |
| mobile | String | mobile | 手机号 |
| telephone | String | telephone | 电话 |
| qq | String | qq | QQ |
| wechat | String | wechat | 微信 |
| email | String | email | 邮箱 |
| areaId | Integer | area_id | 所在地，关联框架 `Area#getId()`（地区库） |
| detailAddress | String | detail_address | 详细地址 |
| industryId | Integer | industry_id | 所属行业，字典 `crm_customer_industry` |
| level | Integer | level | 客户等级，字典 `crm_customer_level` |
| source | Integer | source | 客户来源，字典 `crm_customer_source` |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；源码未声明其余索引，高频查询为按 owner_user_id（负责人的线索分页/公海列表）

#### CrmCustomerDO (crm_customer)

客户主数据表，模块的核心聚合根：联系人、商机、合同、回款全部挂接在客户上，同时被公海回收、客户数上限规则约束。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| name | String | name | 客户名称 |
| followUpStatus | Boolean | follow_up_status | 跟进状态 |
| contactLastTime | LocalDateTime | contact_last_time | 最后跟进时间 |
| contactLastContent | String | contact_last_content | 最后跟进内容 |
| contactNextTime | LocalDateTime | contact_next_time | 下次联系时间 |
| ownerUserId | Long | owner_user_id | 负责人的用户编号，关联 AdminUserDO#getId() |
| ownerTime | LocalDateTime | owner_time | 成为负责人的时间 |
| lockStatus | Boolean | lock_status | 锁定状态（锁定后不允许领取/放入公海） |
| dealStatus | Boolean | deal_status | 成交状态（是否已有成交合同） |
| mobile | String | mobile | 手机 |
| telephone | String | telephone | 电话 |
| qq | String | qq | QQ |
| wechat | String | wechat | 微信 |
| email | String | email | 邮箱 |
| areaId | Integer | area_id | 所在地，关联框架 `Area#getId()` |
| detailAddress | String | detail_address | 详细地址 |
| industryId | Integer | industry_id | 所属行业，字典 `crm_customer_industry` |
| level | Integer | level | 客户等级，字典 `crm_customer_level` |
| source | Integer | source | 客户来源，字典 `crm_customer_source` |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；源码未声明其余索引，高频查询为按 owner_user_id（拥有客户）、lock_status/deal_status（公海回收扫描未跟进/未成交客户）

#### CrmCustomerPoolConfigDO (crm_customer_pool_config)

客户公海规则配置（全局单行），定义客户何时被自动放入公海及提前提醒。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| enabled | Boolean | enabled | 是否启用客户公海 |
| contactExpireDays | Integer | contact_expire_days | 未跟进放入公海天数（FieldStrategy.ALWAYS，支持更新为 null） |
| dealExpireDays | Integer | deal_expire_days | 未成交放入公海天数（FieldStrategy.ALWAYS） |
| notifyEnabled | Boolean | notify_enabled | 是否开启提前提醒（FieldStrategy.ALWAYS） |
| notifyDays | Integer | notify_days | 提前提醒天数（FieldStrategy.ALWAYS） |

**继承**: BaseDO
**索引**: 全局单行配置表，无业务索引

#### CrmCustomerLimitConfigDO (crm_customer_limit_config)

客户数上限规则，按「适用人群（用户/部门）」限定可拥有/可锁定的客户数量上限。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| type | Integer | type | 规则类型，枚举 CrmCustomerLimitConfigTypeEnum（1 拥有客户数限制、2 锁定客户数限制） |
| userIds | List&lt;Long&gt; | user_ids | 规则适用人群，`LongListTypeHandler` 逗号分隔存储，`autoResultMap = true` |
| deptIds | List&lt;Long&gt; | dept_ids | 规则适用部门，`LongListTypeHandler` 逗号分隔存储 |
| maxCount | Integer | max_count | 数量上限 |
| dealCountEnabled | Boolean | deal_count_enabled | 成交客户是否占有拥有客户数（仅当 type = 1 时使用） |

**继承**: BaseDO
**索引**: 主键 id；无其余索引声明，读取路径为全量加载后按 userIds/deptIds 匹配

### 2.2 联系人聚合

#### CrmContactDO (crm_contact)

联系人表，归属于客户，可独立负责商机与合同签约；支持公司内部上下级关系（parentId 自关联）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 主键（@TableId） |
| name | String | name | 联系人姓名 |
| customerId | Long | customer_id | 客户编号，关联 CrmCustomerDO#getId() |
| contactLastTime | LocalDateTime | contact_last_time | 最后跟进时间 |
| contactLastContent | String | contact_last_content | 最后跟进内容 |
| contactNextTime | LocalDateTime | contact_next_time | 下次联系时间 |
| ownerUserId | Long | owner_user_id | 负责人用户编号，关联 AdminUserDO#getId() |
| mobile | String | mobile | 手机号 |
| telephone | String | telephone | 电话 |
| email | String | email | 电子邮箱 |
| qq | Long | qq | QQ（注意：客户/线索表为 String，本表为 Long） |
| wechat | String | wechat | 微信 |
| areaId | Integer | area_id | 所在地，关联框架 `Area#getId()` |
| detailAddress | String | detail_address | 详细地址 |
| sex | Integer | sex | 性别，枚举 SexEnum（system 模块） |
| master | Boolean | master | 是否关键决策人 |
| post | String | post | 职位 |
| parentId | Long | parent_id | 直属上级，关联 CrmContactDO#id（自关联） |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；源码未声明其余索引，高频查询为按 customer_id（客户的联系人列表）、owner_user_id（我负责的联系人）

#### CrmContactBusinessDO (crm_contact_business)

联系人与商机的关联表（多对多中间表）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 主键（@TableId） |
| contactId | Long | contact_id | 联系人编号，关联 CrmContactDO#getId() |
| businessId | Long | business_id | 商机编号，关联 CrmBusinessDO#getId() |

**继承**: BaseDO
**索引**: 主键 id；查询键为 contact_id / business_id（双向查关联）

### 2.3 商机聚合

#### CrmBusinessDO (crm_business)

商机表，客户到合同的中间环节；通过状态组/状态两级配置推进，支持产品明细与整单折扣。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| name | String | name | 商机名称 |
| customerId | Long | customer_id | 客户编号，关联 CrmCustomerDO#getId() |
| followUpStatus | Boolean | follow_up_status | 跟进状态 |
| contactLastTime | LocalDateTime | contact_last_time | 最后跟进时间 |
| contactNextTime | LocalDateTime | contact_next_time | 下次联系时间 |
| ownerUserId | Long | owner_user_id | 负责人的用户编号，关联 AdminUserDO#getId() |
| statusTypeId | Long | status_type_id | 商机状态组编号，关联 CrmBusinessStatusTypeDO#getId() |
| statusId | Long | status_id | 商机状态编号，关联 CrmBusinessStatusDO#getId() |
| endStatus | Integer | end_status | 结束状态，枚举 CrmBusinessEndStatusEnum（1 赢单、2 输单、3 无效） |
| endRemark | String | end_remark | 结束时的备注 |
| dealTime | LocalDateTime | deal_time | 预计成交日期 |
| totalProductPrice | BigDecimal | total_product_price | 产品总金额，单位：元（= ∑ crm_business_product.total_price） |
| discountPercent | BigDecimal | discount_percent | 整单折扣，百分比 |
| totalPrice | BigDecimal | total_price | 商机总金额，单位：元 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；源码未声明其余索引，高频查询为按 customer_id（客户的商机）、owner_user_id、status_type_id/status_id（状态推进）

#### CrmBusinessProductDO (crm_business_product)

商机产品关联表，CrmBusinessDO : CrmBusinessProductDO = 1 : N，商机金额由明细汇总。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 主键（@TableId） |
| businessId | Long | business_id | 商机编号，关联 CrmBusinessDO#getId() |
| productId | Long | product_id | 产品编号，关联 CrmProductDO#getId() |
| productPrice | BigDecimal | product_price | 产品单价，单位：元（冗余 CrmProductDO#getPrice()） |
| businessPrice | BigDecimal | business_price | 商机价格（成交价），单位：元 |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总计价格，单位：元（= business_price × count） |

**继承**: BaseDO
**索引**: 主键 id；查询键为 business_id

#### CrmBusinessStatusTypeDO (crm_business_status_type)

商机状态组配置表，按部门划分可用的商机推进阶段集合。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 主键（@TableId） |
| name | String | name | 状态类型名 |
| deptIds | List&lt;Long&gt; | dept_ids | 使用的部门编号，`LongListTypeHandler` 逗号分隔存储，`autoResultMap = true` |

**继承**: BaseDO
**索引**: 主键 id；无其余索引声明

#### CrmBusinessStatusDO (crm_business_status)

商机状态配置表，隶属某个状态组，定义阶段名称与赢单率。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 主键（@TableId） |
| typeId | Long | type_id | 状态类型编号，关联 CrmBusinessStatusTypeDO#getId() |
| name | String | name | 状态名 |
| percent | Integer | percent | 赢单率，百分比 |
| sort | Integer | sort | 排序 |

**继承**: BaseDO
**索引**: 主键 id；查询键为 type_id（状态组下的状态列表）

### 2.4 合同聚合

#### CrmContractDO (crm_contract)

合同表，销售闭环的成交节点，接 BPM 工作流审批；可关联商机（非必须），金额由产品明细汇总。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 合同编号（主键，@TableId） |
| name | String | name | 合同名称 |
| no | String | no | 合同编号（业务编号） |
| customerId | Long | customer_id | 客户编号，关联 CrmCustomerDO#getId() |
| businessId | Long | business_id | 商机编号（非必须），关联 CrmBusinessDO#getId() |
| contactLastTime | LocalDateTime | contact_last_time | 最后跟进时间 |
| ownerUserId | Long | owner_user_id | 负责人的用户编号，关联 AdminUserDO#getId() |
| processInstanceId | String | process_instance_id | 工作流编号，关联 BPM ProcessInstance 的 id |
| auditStatus | Integer | audit_status | 审批状态，枚举 CrmAuditStatusEnum（0 未提交、10 审批中、20 审核通过、30 审核不通过、40 已取消） |
| orderDate | LocalDateTime | order_date | 下单日期 |
| startTime | LocalDateTime | start_time | 开始时间 |
| endTime | LocalDateTime | end_time | 结束时间（配合 crm_contract_config 做到期提醒） |
| totalProductPrice | BigDecimal | total_product_price | 产品总金额，单位：元（= ∑ crm_contract_product.total_price） |
| discountPercent | BigDecimal | discount_percent | 整单折扣 |
| totalPrice | BigDecimal | total_price | 合同总金额（源码注释标注单位为「分」，模块内其余金额字段均为「元」，以源码为准） |
| signContactId | Long | sign_contact_id | 客户签约人（非必须），关联 CrmContactDO#getId() |
| signUserId | Long | sign_user_id | 公司签约人（非必须），关联 AdminUserDO#getId() |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；源码未声明其余索引，高频查询为按 customer_id / business_id / owner_user_id、audit_status（待审批列表）

#### CrmContractProductDO (crm_contract_product)

合同产品关联表，CrmContractDO : CrmContractProductDO = 1 : N。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 主键（@TableId） |
| contractId | Long | contract_id | 合同编号，关联 CrmContractDO#getId() |
| productId | Long | product_id | 产品编号，关联 CrmProductDO#getId() |
| productPrice | BigDecimal | product_price | 产品单价，单位：元 |
| contractPrice | BigDecimal | contract_price | 合同价格（成交价），单位：元 |
| count | BigDecimal | count | 数量 |
| totalPrice | BigDecimal | total_price | 总计价格，单位：元（源码注释误写为 businessPrice × count，实际语义为 contract_price × count） |

**继承**: BaseDO
**索引**: 主键 id；查询键为 contract_id

#### CrmContractConfigDO (crm_contract_config)

合同到期提醒配置（全局单行）。源码无类注释，语义取自字段与 Service（合同提前提醒）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| notifyEnabled | Boolean | notify_enabled | 是否开启提前提醒（FieldStrategy.ALWAYS） |
| notifyDays | Integer | notify_days | 提前提醒天数（FieldStrategy.ALWAYS） |

**继承**: BaseDO
**索引**: 全局单行配置表，无业务索引

### 2.5 回款聚合

#### CrmReceivableDO (crm_receivable)

回款表，记录合同实际收到的一笔笔回款，接 BPM 工作流审批；可关联回款计划（非必须）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | ID（主键，@TableId） |
| no | String | no | 回款编号（业务编号） |
| planId | Long | plan_id | 回款计划编号（非必须），关联 CrmReceivablePlanDO#getId() |
| customerId | Long | customer_id | 客户编号，关联 CrmCustomerDO#getId() |
| contractId | Long | contract_id | 合同编号，关联 CrmContractDO#getId() |
| ownerUserId | Long | owner_user_id | 负责人编号，关联 AdminUserDO#getId() |
| returnTime | LocalDateTime | return_time | 回款日期 |
| returnType | Integer | return_type | 回款方式，枚举 CrmReceivableReturnTypeEnum（1 支票、2 现金、3 邮政汇款、4 电汇、5 网上转账、6 支付宝、7 微信支付、8 其它） |
| price | BigDecimal | price | 回款金额，单位：元（源码注释沿用「计划回款金额」） |
| remark | String | remark | 备注 |
| processInstanceId | String | process_instance_id | 工作流编号，关联 BPM ProcessInstance 的 id |
| auditStatus | Integer | audit_status | 审批状态，枚举 CrmAuditStatusEnum |

**继承**: BaseDO
**索引**: 主键 id；源码未声明其余索引，高频查询为按 contract_id / customer_id / owner_user_id

#### CrmReceivablePlanDO (crm_receivable_plan)

回款计划表，按期数拆分合同的应收款项；期数回款完成后回写 receivableId 关联到实际回款。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| period | Integer | period | 期数 |
| customerId | Long | customer_id | 客户编号，关联 CrmCustomerDO#getId() |
| contractId | Long | contract_id | 合同编号，关联 CrmContractDO#getId() |
| ownerUserId | Long | owner_user_id | 负责人编号，关联 AdminUserDO#getId() |
| returnTime | LocalDateTime | return_time | 计划回款日期 |
| returnType | Integer | return_type | 计划回款类型，枚举 CrmReceivableReturnTypeEnum |
| price | BigDecimal | price | 计划回款金额，单位：元 |
| receivableId | Long | receivable_id | 回款编号，关联 CrmReceivableDO#getId()（该期已完成回款时回写） |
| remindDays | Integer | remind_days | 提前几天提醒 |
| remindTime | LocalDateTime | remind_time | 提醒日期 |
| remark | String | remark | 备注 |

**继承**: BaseDO
**索引**: 主键 id；查询键为 contract_id / customer_id / owner_user_id

### 2.6 产品聚合

#### CrmProductDO (crm_product)

CRM 产品表，被商机明细与合同明细引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| name | String | name | 产品名称 |
| no | String | no | 产品编码 |
| unit | int | unit | 单位，字典 `crm_product_unit`（注意为基本类型 int） |
| price | BigDecimal | price | 价格，单位：元（商机/合同明细冗余该值） |
| status | Integer | status | 状态，枚举 CrmProductStatusEnum（上架/下架） |
| categoryId | Long | category_id | 产品分类编号，关联 CrmProductCategoryDO#getId() |
| description | String | description | 产品描述 |
| ownerUserId | Long | owner_user_id | 负责人的用户编号，关联 AdminUserDO#getId() |

**继承**: BaseDO
**索引**: 主键 id；查询键为 category_id / status / owner_user_id

#### CrmProductCategoryDO (crm_product_category)

产品分类表，parentId 自关联成树，源码常量限定层级为 2 级（`CATEGORY_LEVEL = 2`，根分类 `parentId = 0`）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 分类编号（主键，@TableId） |
| name | String | name | 分类名称 |
| parentId | Long | parent_id | 父级编号，关联 CrmProductCategoryDO#getId()（0 表示根分类） |

**继承**: BaseDO
**索引**: 主键 id；查询键为 parent_id（子分类列表）

### 2.7 公共支撑（跟进 / 权限 / 变更 / 业绩）

#### CrmFollowUpRecordDO (crm_follow_up_record)

跟进记录表，通过 bizType + bizId 多态挂接线索/客户/联系人/商机等 8 类业务对象；同时反写目标对象的跟进状态与最后跟进时间。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| bizType | Integer | biz_type | 数据类型，枚举 CrmBizTypeEnum（1-8 对应线索/客户/联系人/商机/合同/产品/回款/回款计划） |
| bizId | Long | biz_id | 数据编号，关联 CrmBizTypeEnum 对应模块 DO 的 id 字段 |
| type | Integer | type | 跟进类型，字典 `crm_follow_up_type` |
| content | String | content | 跟进内容 |
| nextTime | LocalDateTime | next_time | 下次联系时间 |
| picUrls | List&lt;String&gt; | pic_urls | 图片，`StringListTypeHandler` 逗号分隔存储，`autoResultMap = true` |
| fileUrls | List&lt;String&gt; | file_urls | 附件，`StringListTypeHandler` 逗号分隔存储 |
| businessIds | List&lt;Long&gt; | business_ids | 关联的商机编号数组，`LongListTypeHandler` 逗号分隔存储，关联 CrmBusinessDO#getId() |
| contactIds | List&lt;Long&gt; | contact_ids | 关联的联系人编号数组，`LongListTypeHandler` 逗号分隔存储，关联 CrmContactDO#getId() |

**继承**: BaseDO
**索引**: 主键 id；查询键为 biz_type + biz_id（某条业务数据的跟进时间线）

#### CrmPermissionDO (crm_permission)

行级数据权限表，模块内所有业务数据的可见/可编辑控制中枢；数据隔离不依赖 SQL 拼接，而是 Service 层先查权限再过滤（无 @PreAuthorize 的端点即靠它控权）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| bizType | Integer | biz_type | 数据类型，枚举 CrmBizTypeEnum（1-8） |
| bizId | Long | biz_id | 数据编号，关联 CrmBizTypeEnum 对应模块 DO 的 id 字段 |
| userId | Long | user_id | 用户编号，关联 AdminUser#getId() |
| level | Integer | level | 权限级别，枚举 CrmPermissionLevelEnum（1 负责人、2 只读、3 读写） |

**继承**: BaseDO
**索引**: 主键 id；业务上 (biz_type, biz_id, user_id) 组合唯一定位一条权限（`selectByBizTypeAndBizIdByUserId` 单条返回），高频查询键为 biz_type + biz_id（团队成员列表）与 biz_type + user_id（我参与的的数据）。源码未声明其余数据库索引

#### CrmOwnerRecordDO (crm_owner_record)

负责人变更记录表，公海领取/分配、数据转移时记录负责人前后值，通过 bizType + bizId 多态关联业务对象。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| bizType | Integer | biz_type | CRM 业务类型，枚举 CrmBizTypeEnum |
| bizId | Long | biz_id | CRM 业务编号 |
| preOwnerUserId | Long | pre_owner_user_id | 变更前负责人 |
| postOwnerUserId | Long | post_owner_user_id | 变更后负责人 |

**继承**: BaseDO
**索引**: 主键 id；查询键为 biz_type + biz_id（某条数据的负责人变更历史）

#### CrmPerformanceConfigDO (crm_performance_config)

业绩目标表，按「对象（用户/部门）× 年份」配置年度与逐月目标金额，供业绩统计对比完成率。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键，@TableId） |
| bizType | Integer | biz_type | 目标类型，枚举 CrmPerformanceConfigBizTypeEnum |
| objectId | Long | object_id | 目标对象编号（用户或部门 id） |
| objectType | Integer | object_type | 目标对象类型，枚举 CrmPerformanceConfigObjectTypeEnum |
| year | Integer | year | 年份 |
| yearTargetPrice | BigDecimal | year_target_price | 年度目标金额 |
| januaryTargetPrice ~ decemberTargetPrice | BigDecimal | january_target_price ~ december_target_price | 一月 ~ 十二月目标金额（12 个月度列） |

**继承**: BaseDO
**索引**: 主键 id；业务上按 (object_type, object_id, year) 定位一条目标记录，源码未声明其余数据库索引

---

## 3. 实体关系

核心外键/从属关系（均为逻辑外键，无数据库级 FK 约束）：

```
crm_clue (线索)
   │ transform_status = true 时写入 customer_id，转入客户
   ▼
crm_customer (客户) ──────────────────────────────────────────────┐
   │ customerId            customerId              customerId     │ customerId
   ▼                       ▼                       ▼              │
crm_contact (联系人)   crm_business (商机)     crm_contract (合同) │
   │ contactId            │ businessId            │ contractId    │
   │        ┌─────────────┘                       │               │
   ▼        ▼                                     ▼               │
crm_contact_business               crm_contract_product           │
 (contact_id ↔ business_id)               │ productId             │
                                          ▼                       │
                                    crm_product ── categoryId ──► crm_product_category
                                                                    (parentId 自关联，限 2 级)

crm_business (商机)
   ├── statusTypeId ──► crm_business_status_type (状态组，dept_ids 限定适用部门)
   │                          ▲ typeId
   ├── statusId ────────── crm_business_status (状态，percent 赢单率，sort 排序)
   └── businessId ◄── crm_business_product ──► productId ──► crm_product

crm_contract (合同)
   ├── businessId ──► crm_business.id        （来源商机，非必须）
   ├── sign_contact_id ──► crm_contact.id    （客户签约人，非必须）
   ├── contractId ──► crm_receivable_plan (回款计划，period 期数)
   │                          │ receivableId（完成回款后回写）
   │                          ▼
   └── contractId ──► crm_receivable (回款，planId 关联计划，非必须)

多态关联（biz_type + biz_id，CrmBizTypeEnum：1 线索 2 客户 3 联系人 4 商机 5 合同 6 产品 7 回款 8 回款计划）：
   crm_permission         数据权限（+ user_id + level：1 负责人 / 2 只读 / 3 读写）
   crm_follow_up_record   跟进记录（+ type/content/pic_urls/file_urls + businessIds、contactIds 二次关联）
   crm_owner_record       负责人变更记录（+ pre_owner_user_id / post_owner_user_id）

独立配置表（不挂业务数据）：
   crm_customer_pool_config   公海规则（单行：未跟进/未成交天数 + 提前提醒）
   crm_customer_limit_config  客户数上限（user_ids/dept_ids 逗号分隔匹配，max_count）
   crm_contract_config        合同到期提醒（单行）
   crm_performance_config     业绩目标（object_type + object_id + year + 12 个月目标列）
```

**关系要点**：

- `crm_customer` 是模块中心表：`crm_contact`、`crm_business`、`crm_contract`、`crm_receivable`、`crm_receivable_plan` 均带 `customer_id` 冗余关联（如 crm_receivable 同时挂 contract_id 与 customer_id，便于按客户聚合）。
- 销售主线：线索转化（`crm_clue.customer_id`）→ 客户下建联系人/商机 → 商机配产品明细（`crm_business_product`）→ 成交签合同（`crm_contract.business_id`）→ 合同拆回款计划（`crm_receivable_plan`）→ 落实际回款（`crm_receivable`，`receivable_plan.receivable_id` 回写）。
- 商机/合同与产品均为「主表 + 明细表」模式：明细行冗余 `product_price`（下单时单价快照），主表 `total_product_price` = ∑明细 `total_price`，再乘整单折扣 `discount_percent` 得 `total_price`。
- 负责人字段 `owner_user_id` 在客户/线索/联系人/商机/合同/回款/回款计划/产品上均存在，指向 system 模块 AdminUser；变更动作统一记录到 `crm_owner_record`，可见性则由 `crm_permission` 按 (biz_type, biz_id) 一组多行控制（1 负责人 + N 个只读/读写成员）。
- 公海回收不单独建表：`crm_customer_pool_config` 提供规则，规则触发时把 `crm_customer.owner_user_id` 置空并写 `crm_owner_record`；领取时受 `crm_customer_limit_config` 的数量上限约束（`lock_status` 锁定的客户不可转移）。
- 商机推进依赖两级配置：`crm_business_status_type`（状态组，dept_ids 指定哪些部门可用）→ `crm_business_status`（组内阶段，type_id 关联）；`crm_business.end_status` 用枚举表达终结态（赢单/输单/无效）。
- 审批对接 BPM：`crm_contract`、`crm_receivable` 通过 `process_instance_id`（字符串，BPM 流程实例 id）+ `audit_status` 枚举（0 未提交/10 审批中/20 审核通过/30 审核不通过/40 已取消）挂接工作流。
- 跨模块引用：system 模块（AdminUser 用户、Dept 部门、字典 `crm_customer_industry`/`crm_customer_level`/`crm_customer_source`/`crm_product_unit`/`crm_follow_up_type`）、bpm 模块（流程实例）、框架 ip 模块（`Area` 地区库）。操作日志无本地表，复用 system 模块 OperateLogApi。

---

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|-----|
| crm_clue | CrmClueDO | 线索（销售前潜在客户，转化后回写 customer_id） |
| crm_customer | CrmCustomerDO | 客户主数据（模块中心表，含跟进/成交/锁定状态） |
| crm_customer_limit_config | CrmCustomerLimitConfigDO | 客户数上限规则（拥有/锁定，按用户或部门生效） |
| crm_customer_pool_config | CrmCustomerPoolConfigDO | 客户公海规则（单行：放入公海天数 + 提前提醒） |
| crm_contact | CrmContactDO | 联系人（归属客户，parentId 支持上下级，master 标记关键决策人） |
| crm_contact_business | CrmContactBusinessDO | 联系人 ↔ 商机关联（多对多中间表） |
| crm_business | CrmBusinessDO | 商机（状态组/状态推进，整单折扣，结束状态） |
| crm_business_product | CrmBusinessProductDO | 商机产品明细（单价快照 + 数量 + 小计） |
| crm_business_status_type | CrmBusinessStatusTypeDO | 商机状态组配置（dept_ids 限定适用部门） |
| crm_business_status | CrmBusinessStatusDO | 商机状态配置（组内阶段 + 赢单率 + 排序） |
| crm_contract | CrmContractDO | 合同（接 BPM 审批，sign_contact/sign_user 双签约人） |
| crm_contract_product | CrmContractProductDO | 合同产品明细（单价快照 + 数量 + 小计） |
| crm_contract_config | CrmContractConfigDO | 合同到期提醒配置（单行） |
| crm_receivable | CrmReceivableDO | 回款（接 BPM 审批，可关联回款计划） |
| crm_receivable_plan | CrmReceivablePlanDO | 回款计划（期数拆分，完成回款后回写 receivable_id） |
| crm_product | CrmProductDO | CRM 产品（被商机/合同明细引用） |
| crm_product_category | CrmProductCategoryDO | 产品分类（parentId 自关联，限 2 级） |
| crm_follow_up_record | CrmFollowUpRecordDO | 跟进记录（bizType + bizId 多态挂接 8 类业务对象） |
| crm_permission | CrmPermissionDO | 行级数据权限（bizType + bizId + userId + level，模块控权中枢） |
| crm_owner_record | CrmOwnerRecordDO | 负责人变更记录（bizType + bizId 多态，记录前后负责人） |
| crm_performance_config | CrmPerformanceConfigDO | 业绩目标（对象 × 年份，年度 + 12 个月目标金额） |
