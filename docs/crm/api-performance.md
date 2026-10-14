# 业绩目标接口 (CrmPerformanceConfigController)

> 提供 CRM 业绩目标设置的管理：按「部门/员工 + 年份 + 业务类型（销售/回款）」维度维护 12 个月的业绩目标金额，系统自动汇总年度目标金额。

## 接口路径前缀

/crm/performance-config  (Controller: CrmPerformanceConfigController)

**枚举约定**:

- 目标对象类型 objectType（CrmPerformanceConfigObjectTypeEnum）：`2` 部门、`3` 员工
- 目标类型 bizType（CrmPerformanceConfigBizTypeEnum）：`5` 销售目标（合同）、`7` 回款目标

## 1. 业绩目标设置管理

### 1.1 创建业绩目标

- **路径**: POST /crm/performance-config/create
- **权限**: crm:performance-config:create
- **说明**: 创建一条业绩目标配置，同一「目标对象 + 年份 + 业务类型」组合不允许重复，月份金额空值自动补 0 并计算年度目标。

**请求参数 (CrmPerformanceConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（创建时不传） |
| objectId | Long | 是 | @NotNull | 目标对象编号（部门或员工编号） |
| objectType | Integer | 是 | @NotNull、@InEnum(CrmPerformanceConfigObjectTypeEnum) | 目标对象类型：2 部门、3 员工 |
| year | Integer | 是 | @NotNull | 年份，如 2026 |
| januaryTargetPrice | BigDecimal | 否 | - | 一月目标金额 |
| februaryTargetPrice | BigDecimal | 否 | - | 二月目标金额 |
| marchTargetPrice | BigDecimal | 否 | - | 三月目标金额 |
| aprilTargetPrice | BigDecimal | 否 | - | 四月目标金额 |
| mayTargetPrice | BigDecimal | 否 | - | 五月目标金额 |
| juneTargetPrice | BigDecimal | 否 | - | 六月目标金额 |
| julyTargetPrice | BigDecimal | 否 | - | 七月目标金额 |
| augustTargetPrice | BigDecimal | 否 | - | 八月目标金额 |
| septemberTargetPrice | BigDecimal | 否 | - | 九月目标金额 |
| octoberTargetPrice | BigDecimal | 否 | - | 十月目标金额 |
| novemberTargetPrice | BigDecimal | 否 | - | 十一月目标金额 |
| decemberTargetPrice | BigDecimal | 否 | - | 十二月目标金额 |
| bizType | Integer | 是 | @NotNull、@InEnum(CrmPerformanceConfigBizTypeEnum) | 目标类型：5 销售目标、7 回款目标 |

**响应**: CommonResult&lt;Long&gt; —— 业绩目标编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的业绩目标配置编号 |

**业务逻辑**:
1. 校验目标对象：objectType 为部门（2）时调用 deptApi.validateDeptList 校验部门存在；为员工（3）时调用 adminUserApi.validateUserList 校验员工存在；其他类型抛出「目标对象类型不正确」。
2. 校验唯一：按 objectId + objectType + year + bizType 查询，已存在配置则抛出「该对象当前年份的业绩目标配置已存在」。
3. 将请求 VO 转换为 CrmPerformanceConfigDO。
4. 填充目标金额：12 个月目标金额空值置为 0，并累加 12 个月得到年度目标金额 yearTargetPrice。
5. 插入数据库，返回记录编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_011_001 | 该对象当前年份的业绩目标配置已存在 |
| 1_020_011_002 | 目标对象类型不正确 |

### 1.2 更新业绩目标

- **路径**: PUT /crm/performance-config/update
- **权限**: crm:performance-config:update
- **说明**: 更新指定业绩目标配置，同样进行目标对象校验与唯一性校验（排除自身），并重算年度目标金额。

**请求参数 (CrmPerformanceConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是（更新必传） | - | 编号 |
| objectId | Long | 是 | @NotNull | 目标对象编号（部门或员工编号） |
| objectType | Integer | 是 | @NotNull、@InEnum(CrmPerformanceConfigObjectTypeEnum) | 目标对象类型：2 部门、3 员工 |
| year | Integer | 是 | @NotNull | 年份，如 2026 |
| januaryTargetPrice ~ decemberTargetPrice | BigDecimal | 否 | - | 一月～十二月目标金额（共 12 个字段，命名分别为 january/february/march/april/may/june/july/august/september/october/november/december + TargetPrice） |
| bizType | Integer | 是 | @NotNull、@InEnum(CrmPerformanceConfigBizTypeEnum) | 目标类型：5 销售目标、7 回款目标 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 更新成功返回 true |

**业务逻辑**:
1. 校验存在：按 id 查询记录，不存在抛出「业绩目标配置不存在」。
2. 校验目标对象：部门/员工存在性校验，同创建逻辑，其他类型抛出「目标对象类型不正确」。
3. 校验唯一：按 objectId + objectType + year + bizType 查询，存在且非自身记录则抛出「该对象当前年份的业绩目标配置已存在」。
4. 将请求 VO 转换为 CrmPerformanceConfigDO，月份金额空值置 0 并重算年度目标金额。
5. 按主键更新数据库记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_011_000 | 业绩目标配置不存在 |
| 1_020_011_001 | 该对象当前年份的业绩目标配置已存在 |
| 1_020_011_002 | 目标对象类型不正确 |

### 1.3 删除业绩目标

- **路径**: DELETE /crm/performance-config/delete
- **权限**: crm:performance-config:delete
- **说明**: 删除指定业绩目标配置。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 编号 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**:
1. 校验存在：按 id 查询记录，不存在抛出「业绩目标配置不存在」。
2. 按主键删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_011_000 | 业绩目标配置不存在 |

### 1.4 获得业绩目标

- **路径**: GET /crm/performance-config/get
- **权限**: crm:performance-config:query
- **说明**: 按编号获取业绩目标配置详情，并拼接目标对象名称（部门名称或员工昵称）。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 编号 |

**响应**: CommonResult&lt;CrmPerformanceConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| objectId | Long | 目标对象编号 |
| objectName | String | 目标对象名称（部门名称或员工昵称，Controller 拼接） |
| objectType | Integer | 目标对象类型：2 部门、3 员工 |
| year | Integer | 年份 |
| januaryTargetPrice ~ decemberTargetPrice | BigDecimal | 一月～十二月目标金额（12 个字段） |
| bizType | Integer | 目标类型：5 销售目标、7 回款目标 |
| yearTargetPrice | BigDecimal | 年度目标金额（12 个月之和） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询记录，不存在抛出「业绩目标配置不存在」。
2. 将 DO 转换为 CrmPerformanceConfigRespVO。
3. 拼接目标对象名称：objectType 为部门时通过 deptApi.getDeptMap 取部门名称；为员工时通过 adminUserApi.getUserMap 取员工昵称，写入 objectName。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_011_000 | 业绩目标配置不存在 |

### 1.5 获得业绩目标分页

- **路径**: GET /crm/performance-config/page
- **权限**: crm:performance-config:query
- **说明**: 分页查询业绩目标配置，支持按目标对象、类型、年份、业务类型过滤，结果拼接目标对象名称。

**请求参数 (CrmPerformanceConfigPageReqVO)**（继承 PageParam：pageNo 页码默认 1、pageSize 每页条数默认 10）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，从 1 开始（PageParam 继承） |
| pageSize | Integer | 否 | - | 每页条数（PageParam 继承） |
| objectId | Long | 否 | - | 目标对象编号（精确匹配） |
| objectType | Integer | 否 | @InEnum(CrmPerformanceConfigObjectTypeEnum) | 目标对象类型：2 部门、3 员工 |
| year | Integer | 否 | - | 年份 |
| bizType | Integer | 否 | @InEnum(CrmPerformanceConfigBizTypeEnum) | 目标类型：5 销售目标、7 回款目标 |

**响应**: CommonResult&lt;PageResult&lt;CrmPerformanceConfigRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| total | Long | 总条数 |
| list[].id | Long | 编号 |
| list[].objectId | Long | 目标对象编号 |
| list[].objectName | String | 目标对象名称（部门名称或员工昵称，Controller 拼接） |
| list[].objectType | Integer | 目标对象类型：2 部门、3 员工 |
| list[].year | Integer | 年份 |
| list[].januaryTargetPrice ~ decemberTargetPrice | BigDecimal | 一月～十二月目标金额（12 个字段） |
| list[].bizType | Integer | 目标类型：5 销售目标、7 回款目标 |
| list[].yearTargetPrice | BigDecimal | 年度目标金额（12 个月之和） |
| list[].createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按条件分页查询：objectId/objectType/year/bizType 均为条件非空时才生效（eqIfPresent），排序为 year 倒序、objectType/objectId/bizType 升序。
2. 分页结果为空时直接返回空分页（仅含 total）。
3. 将分页结果批量转换为 CrmPerformanceConfigRespVO 列表。
4. 拼接目标对象名称：收集 objectType 为部门的 objectId 批量调用 deptApi.getDeptMap 取部门名称；objectType 为员工的批量调用 adminUserApi.getUserMap 取员工昵称，逐条写入 objectName。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_011_000 | 业绩目标配置不存在（内部查询时可能触发） |
