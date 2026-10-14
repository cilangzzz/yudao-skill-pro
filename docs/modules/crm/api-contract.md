# 合同管理接口 (CrmContractController、CrmContractConfigController)

> 提供 CRM 合同的全生命周期管理：合同的创建/更新/删除、提交 BPM 审批、负责人转移、分页查询与 Excel 导出、待审核/到期提醒统计，以及合同到期提醒配置（是否开启提前提醒、提前天数）。

## 接口路径前缀

- `/crm/contract`  (Controller: CrmContractController)
- `/crm/contract-config`  (Controller: CrmContractConfigController)

说明：

- 合同实体的读操作（详情/分页）由 `@CrmPermission` 注解在 Service 层进行数据权限（读/写/负责人）校验；审批对接 BPM 流程 `crm-contract-audit`，审批结果由 `CrmContractStatusListener` 监听 `BpmProcessInstanceStatusEvent` 回写。
- 审批状态 `auditStatus` 取值（`CrmAuditStatusEnum`）：`0` 未提交（草稿）、`10` 审批中、`20` 审核通过、`30` 审核不通过、`40` 已取消。
- 场景类型 `sceneType` 取值（`CrmSceneTypeEnum`）：`1` 我负责的、`2` 我参与的、`3` 下属负责的。

---

## 1. 合同管理（CrmContractController）

### 1.1 创建合同

- **路径**: POST /crm/contract/create
- **权限**: crm:contract:create
- **说明**: 创建合同，生成合同序号，保存合同及关联产品，并为负责人创建 OWNER 级数据权限。

**请求参数 (CrmContractSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 否 | 无 | 合同编号（创建时不传，更新时必传） |
| name | String | 是 | @NotNull | 合同名称 |
| customerId | Long | 是 | @NotNull | 客户编号 |
| businessId | Long | 否 | 无 | 商机编号 |
| ownerUserId | Long | 是 | @NotNull | 负责人的用户编号 |
| orderDate | LocalDateTime | 是 | @NotNull | 下单日期 |
| startTime | LocalDateTime | 否 | 无 | 开始时间 |
| endTime | LocalDateTime | 否 | 无 | 结束时间 |
| discountPercent | BigDecimal | 是 | @NotNull | 整单折扣 |
| totalPrice | BigDecimal | 否 | @DecimalMin("0") | 合同金额（无产品明细时以传入值为准，不再重算） |
| signContactId | Long | 否 | 无 | 客户签约人编号（联系人） |
| signUserId | Long | 否 | 无 | 公司签约人（用户编号） |
| remark | String | 否 | 无 | 备注 |
| products | List&lt;Product&gt; | 否 | 无 | 产品列表 |
| products[].productId | Long | 是 | @NotNull | 产品编号 |
| products[].productPrice | BigDecimal | 是 | @NotNull | 产品单价 |
| products[].contractPrice | BigDecimal | 是 | @NotNull | 合同价格 |
| products[].count | Integer | 是 | @NotNull | 产品数量 |

**响应**: CommonResult&lt;Long&gt;（合同编号）

**业务逻辑**:
1. 校验产品项有效性：产品必须存在，并计算每个产品项总价（合同价格 × 数量）。
2. 校验关联字段：客户、负责人存在；若传商机、客户签约人、公司签约人则分别校验存在。
3. 通过 `CrmNoRedisDAO` 生成合同序号（前缀 CONTRACT），若序号重复则抛出 `CONTRACT_NO_EXISTS`。
4. 插入合同：计算产品总金额；有产品明细时合同金额 = 产品总额 - 折扣额（按整单折扣重算），无产品明细时保留传入的合同金额。
5. 批量插入合同关联产品（`CrmContractProductDO`）。
6. 创建数据权限：负责人拥有 OWNER 级别权限（`crmPermissionService.createPermission`）。
7. 记录操作日志（`@LogRecord`）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_000_004 | 生成合同序列号重复，请重试 |

### 1.2 更新合同

- **路径**: PUT /crm/contract/update
- **权限**: crm:contract:update（Service 层另校验合同 WRITE 数据权限）
- **说明**: 更新合同基本信息及关联产品，仅草稿/审批中状态可编辑，负责人不可通过本接口修改。

**请求参数 (CrmContractSaveReqVO)**: 同 1.1（`id` 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验合同编号非空、合同存在。
2. 校验状态：仅草稿（0）、审批中（10）可编辑，否则抛出 `CONTRACT_UPDATE_FAIL_NOT_DRAFT`；`ownerUserId` 强制置空不允许更新。
3. 校验产品项有效性并计算每项总价。
4. 校验关联字段（客户/负责人/商机/签约人）存在。
5. 更新合同并重算产品总金额与合同金额。
6. 差量更新合同关联产品：新增、更新、删除（按 id 对比）。
7. 记录操作日志（新旧对象 diff 对比）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_000_000 | 合同不存在 |
| 1_020_000_001 | 合同更新失败，原因：合同不是草稿状态 |

### 1.3 删除合同

- **路径**: DELETE /crm/contract/delete
- **权限**: crm:contract:delete（Service 层另校验合同 OWNER 数据权限）
- **说明**: 删除合同，被回款引用的合同不允许删除。

**请求参数**: 无（Query 参数 `id`：Long，必填，合同编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验合同存在。
2. 校验未被回款引用：若该合同下存在回款记录，抛出 `CONTRACT_DELETE_FAIL`。
3. 删除合同记录。
4. 删除该合同的数据权限记录。
5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_000_000 | 合同不存在 |
| 1_020_000_005 | 删除合同失败，原因：有被回款所使用 |

### 1.4 获得合同详情

- **路径**: GET /crm/contract/get
- **权限**: crm:contract:query（Service 层另校验合同 READ 数据权限）
- **说明**: 获得合同详情，拼接客户/商机/签约人/负责人等关联信息及产品明细。

**请求参数**: 无（Query 参数 `id`：Long，必填，合同编号）

**响应**: CommonResult&lt;CrmContractRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 合同编号 |
| name | String | 合同名称 |
| no | String | 合同序号 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| businessId | Long | 商机编号 |
| businessName | String | 商机名称 |
| contactLastTime | LocalDateTime | 最后跟进时间 |
| ownerUserId | Long | 负责人的用户编号 |
| ownerUserName | String | 负责人名字 |
| ownerUserDeptName | String | 负责人部门 |
| processInstanceId | String | 工作流编号（BPM 流程实例） |
| auditStatus | Integer | 审批状态（0/10/20/30/40） |
| orderDate | LocalDateTime | 下单日期 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| totalProductPrice | BigDecimal | 产品总金额 |
| discountPercent | BigDecimal | 整单折扣 |
| totalPrice | BigDecimal | 合同金额 |
| totalReceivablePrice | BigDecimal | 已回款金额 |
| signContactId | Long | 客户签约人编号 |
| signContactName | String | 客户签约人 |
| signUserId | Long | 公司签约人编号 |
| signUserName | String | 公司签约人 |
| remark | String | 备注 |
| creator | String | 创建人 |
| creatorName | String | 创建人名字 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |
| products | List&lt;Product&gt; | 产品列表 |
| products[].id | Long | 编号 |
| products[].productId | Long | 产品编号 |
| products[].productName | String | 产品名称 |
| products[].productNo | String | 产品条码 |
| products[].productUnit | int | 产品单位 |
| products[].productPrice | BigDecimal | 产品单价 |
| products[].contractPrice | BigDecimal | 合同价格 |
| products[].count | BigDecimal | 产品数量 |
| products[].totalPrice | BigDecimal | 总计价格 |

**业务逻辑**:
1. 按编号查询合同（Service 层校验 READ 数据权限）。
2. 拼接客户名称、创建人/负责人（含负责人部门）、公司签约人、客户签约人、商机名称。
3. 统计并拼接该合同的已回款金额（无记录则为 0）。
4. 查询合同产品明细，拼接产品名称、产品条码、产品单位。

### 1.5 获得合同分页

- **路径**: GET /crm/contract/page
- **权限**: crm:contract:query
- **说明**: 按条件分页查询当前用户可见（我负责的/我参与的/下属负责的）的合同列表。

**请求参数 (CrmContractPageReqVO)**（继承 PageParam：`pageNo` 页码、`pageSize` 每页条数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| no | String | 否 | 无 | 合同序号 |
| name | String | 否 | 无 | 合同名称 |
| customerId | Long | 否 | 无 | 客户编号 |
| businessId | Long | 否 | 无 | 商机编号 |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum) | 场景类型：1 我负责的、2 我参与的、3 下属负责的（null 全部） |
| auditStatus | Integer | 否 | @InEnum(CrmAuditStatusEnum) | 审批状态：0 未提交、10 审批中、20 审核通过、30 审核不通过、40 已取消 |
| expiryType | Integer | 否 | 无 | 过期类型：1 即将过期、2 已过期（null 全部） |

**响应**: CommonResult&lt;PageResult&lt;CrmContractRespVO&gt;&gt;，列表项字段同 1.4 的 CrmContractRespVO（分页项不返回产品明细）。

**业务逻辑**:
1. 若 `expiryType` 为「即将过期」（1），读取合同到期提醒配置；配置不存在或未开启提醒则直接返回空分页。
2. 按查询条件 + 当前登录用户的数据权限范围执行分页查询。
3. 批量拼接关联信息：客户名称、创建人/负责人（含部门）、客户签约人、公司签约人、商机名称、已回款金额。

### 1.6 获得合同分页（基于指定客户）

- **路径**: GET /crm/contract/page-by-customer
- **权限**: 已认证（Service 层通过 `@CrmPermission` 校验客户的 READ 数据权限）
- **说明**: 查询指定客户下的合同分页，用于客户详情页等场景。

**请求参数 (CrmContractPageReqVO)**: 同 1.5，其中 `customerId` 必传（服务端 Assert 校验非空）

**响应**: CommonResult&lt;PageResult&lt;CrmContractRespVO&gt;&gt;（字段同 1.4）

**业务逻辑**:
1. 校验 `customerId` 非空。
2. 校验当前用户对该客户的 READ 数据权限。
3. 按客户条件分页查询合同，并拼接关联信息（同 1.5 第 3 步）。

### 1.7 获得合同分页（基于指定商机）

- **路径**: GET /crm/contract/page-by-business
- **权限**: 已认证（Service 层通过 `@CrmPermission` 校验商机的 READ 数据权限）
- **说明**: 查询指定商机下的合同分页。

**请求参数 (CrmContractPageReqVO)**: 同 1.5，其中 `businessId` 必传（服务端 Assert 校验非空）

**响应**: CommonResult&lt;PageResult&lt;CrmContractRespVO&gt;&gt;（字段同 1.4）

**业务逻辑**:
1. 校验 `businessId` 非空。
2. 校验当前用户对该商机的 READ 数据权限。
3. 按商机条件分页查询合同，并拼接关联信息（同 1.5 第 3 步）。

### 1.8 导出合同 Excel

- **路径**: GET /crm/contract/export-excel
- **权限**: crm:contract:export
- **说明**: 按分页条件导出合同列表为 Excel 文件（`合同.xls`），并记录导出操作日志。

**请求参数 (CrmContractPageReqVO)**: 同 1.5

**响应**: 无 CommonResult，直接向 `HttpServletResponse` 输出 Excel 文件流（导出列为 CrmContractRespVO 上 `@ExcelProperty` 标注的字段）。

**业务逻辑**:
1. 按 1.5 相同的条件 + 数据权限查询合同分页。
2. 转换为 CrmContractRespVO 列表，通过 `ExcelUtils.write` 输出文件。
3. 记录 EXPORT 类型访问日志（`@ApiAccessLog(operateType = EXPORT)`）。

### 1.9 合同转移

- **路径**: PUT /crm/contract/transfer
- **权限**: crm:contract:update（Service 层另校验合同 OWNER 数据权限）
- **说明**: 将合同负责人转移给新负责人，老负责人可保留团队权限。

**请求参数 (CrmContractTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @NotNull | 合同编号 |
| newOwnerUserId | Long | 是 | @NotNull | 新负责人的用户编号 |
| oldOwnerPermissionLevel | Integer | 否 | @InEnum(CrmPermissionLevelEnum) | 老负责人加入团队后的权限级别 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验合同存在（需 OWNER 数据权限）。
2. 转移数据权限：调用 `crmPermissionService.transferPermission`，新负责人成为 OWNER，老负责人按 `oldOwnerPermissionLevel` 加入团队。
3. 更新合同的负责人为新负责人。
4. 记录转移操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_000_000 | 合同不存在 |

### 1.10 提交合同审批

- **路径**: PUT /crm/contract/submit
- **权限**: crm:contract:update
- **说明**: 将草稿状态的合同提交 BPM 审批流程（流程 Key：`crm-contract-audit`）。

**请求参数**: 无（Query 参数 `id`：Long，必填，合同编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验合同存在，且审批状态必须为未提交（草稿 0），否则抛出 `CONTRACT_SUBMIT_FAIL_NOT_DRAFT`。
2. 调用 `bpmProcessInstanceApi.createProcessInstance` 创建 BPM 流程实例（流程定义 Key 为 `crm-contract-audit`，businessKey 为合同编号）。
3. 更新合同的 `processInstanceId`，并将审批状态置为审批中（10）。
4. 审批结果由 `CrmContractStatusListener` 监听 BPM 流程实例状态事件后回调 `updateContractAuditStatus`：仅审批中（10）的合同可回写结果（否则抛 `CONTRACT_UPDATE_AUDIT_STATUS_FAIL_NOT_PROCESS`），并将 BPM 结果转换为合同审批状态（通过/不通过）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_000_000 | 合同不存在 |
| 1_020_000_002 | 合同提交审核失败，原因：合同没处在未提交状态 |
| 1_020_000_003 | 更新合同审核状态失败，原因：合同不是审核中状态 |

### 1.11 获得待审核合同数量

- **路径**: GET /crm/contract/audit-count
- **权限**: crm:contract:query
- **说明**: 统计当前用户待审核（审批中）的合同数量，用于首页待办提醒。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;（待审核合同数量）

**业务逻辑**:
1. 按当前登录用户统计其名下审批中的合同数量。

### 1.12 获得即将到期（提醒）的合同数量

- **路径**: GET /crm/contract/remind-count
- **权限**: crm:contract:query
- **说明**: 按合同配置的提前提醒天数，统计当前用户即将到期的合同数量。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;（即将到期合同数量）

**业务逻辑**:
1. 读取合同到期提醒配置；配置不存在或未开启提醒（`notifyEnabled` 为 false）时直接返回 0。
2. 按配置的提前提醒天数统计当前用户即将到期的合同数量。

### 1.13 获得合同精简列表

- **路径**: GET /crm/contract/simple-list
- **权限**: crm:contract:query
- **说明**: 获得指定客户下的合同精简列表（不分页），主要用于前端下拉选项。

**请求参数**: 无（Query 参数 `customerId`：Long，必填，客户编号）

**响应**: CommonResult&lt;List&lt;CrmContractRespVO&gt;&gt;，仅返回精简字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 合同编号 |
| name | String | 合同名称 |
| auditStatus | Integer | 审批状态 |
| totalPrice | BigDecimal | 合同金额 |
| totalReceivablePrice | BigDecimal | 已回款金额 |

**业务逻辑**:
1. 以 `customerId` 构造分页查询（`pageSize` 设为不分页），基于客户维度查询合同。
2. 结果为空则直接返回空列表。
3. 统计各合同的已回款金额（无记录则为 0）。
4. 组装仅含 id、name、auditStatus、totalPrice、totalReceivablePrice 的精简 VO 列表返回。

---

## 2. 合同配置（CrmContractConfigController）

### 2.1 获取合同配置

- **路径**: GET /crm/contract-config/get
- **权限**: crm:contract-config:query
- **说明**: 获取合同到期提醒配置（单条全局配置）。

**请求参数**: 无

**响应**: CommonResult&lt;CrmContractConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| notifyEnabled | Boolean | 是否开启提前提醒 |
| notifyDays | Integer | 提前提醒天数 |

**业务逻辑**:
1. 查询配置表中的单条配置记录并转换为 RespVO 返回（不存在时返回 null 数据）。

### 2.2 更新合同配置

- **路径**: PUT /crm/contract-config/save
- **权限**: crm:contract-config:update
- **说明**: 保存合同到期提醒配置，存在则更新、不存在则插入。

**请求参数 (CrmContractConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| notifyEnabled | Boolean | 否 | 无 | 是否开启提前提醒 |
| notifyDays | Integer | 条件必填 | @AssertTrue（开启提醒时不能为空） | 提前提醒天数 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 查询数据库中的现有配置。
2. 配置存在则按 id 更新；不存在则插入新配置。
3. 记录操作日志（区分「更新」与「新建」两种情况）。
