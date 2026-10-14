# 回款管理接口 (CrmReceivableController)

> CRM 回款与回款计划管理：回款记录合同实际收到的款项（支持 BPM 工作流审批），回款计划按期数拆分合同回款并支持到期提醒。

## 接口路径前缀

- `/crm/receivable` (Controller: CrmReceivableController)
- `/crm/receivable-plan` (Controller: CrmReceivablePlanController)

## 1. 回款（CrmReceivableController）

### 1.1 创建回款

- **路径**: POST /crm/receivable/create
- **权限**: crm:receivable:create
- **说明**: 创建一条回款记录，自动生成回款编号，并写入数据权限、回填回款计划。

**请求参数 (CrmReceivableSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（新增时不传） |
| ownerUserId | Long | 是 | @NotNull | 负责人编号 |
| customerId | Long | 否 | - | 客户编号（不通过前端传递，由 contractId 查询得出） |
| contractId | Long | 是 | @NotNull | 合同编号 |
| planId | Long | 否 | - | 回款计划编号 |
| returnType | Integer | 否 | @InEnum(CrmReceivableReturnTypeEnum) | 回款方式 |
| price | BigDecimal | 是 | @NotNull | 回款金额 |
| returnTime | LocalDateTime | 是 | @NotNull | 回款日期 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult<Long>（回款编号）

**业务逻辑**:
1. 校验可回款金额不超上限：统计该合同下已审核通过与审批中的回款金额之和，合同总价减去该和即为剩余可回款金额，超出则报错（更新时排除自身）。
2. 校验关联数据存在：负责人必须存在；合同必须存在且为审核通过状态（并回填 customerId）；回款计划必须存在且尚未关联回款。
3. 通过 Redis 生成回款编号（前缀 RECEIVABLE），若编号重复则抛出异常。
4. 插入回款记录，审批状态初始化为草稿（DRAFT）。
5. 创建数据权限，将负责人设置为 OWNER 级别。
6. 若指定了回款计划（planId），更新该计划的关联回款编号（receivableId）。
7. 记录操作日志上下文（回款信息、期数）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_004_005 | 生成回款序列号重复，请重试 |
| 1_020_004_006 | 创建回款失败，原因：合同不是审核通过状态 |
| 1_020_004_007 | 创建回款失败，原因：回款金额超出合同金额，目前剩余可退：{} 元 |
| 1_020_004_008 | 删除回款失败，原因：回款审批已通过 |
| 1_020_005_000 | 回款计划不存在 |
| 1_020_006_001 | 回款计划已经有对应的回款，不能使用 |

### 1.2 更新回款

- **路径**: PUT /crm/receivable/update
- **权限**: crm:receivable:update
- **说明**: 更新回款（负责人、客户、合同、回款计划均不允许修改），仅草稿/审批中状态可编辑。

**请求参数 (CrmReceivableSaveReqVO)**: 同 1.1（id 必传；负责人/客户/合同/计划字段被强制以库中原值覆盖，前端传入无效）

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 校验回款存在（RECEIVABLE_NOT_EXISTS）。
2. 屏蔽负责人、客户、合同、计划等不允许修改的字段，统一以库中原值回填。
3. 校验可回款金额不超上限（同创建，排除自身）。
4. 仅草稿（DRAFT）、审批中（PROCESS）状态可编辑，否则报错。
5. 更新回款记录，并记录操作日志上下文（旧对象用于差异对比）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_004_000 | 回款不存在 |
| 1_020_004_001 | 更新回款失败，原因：禁止编辑 |
| 1_020_004_007 | 创建回款失败，原因：回款金额超出合同金额，目前剩余可退：{} 元 |

### 1.3 删除回款

- **路径**: DELETE /crm/receivable/delete
- **权限**: crm:receivable:delete
- **说明**: 删除回款，被回款计划引用或已审批通过的不允许删除。

**请求参数**: 无（Query 参数：`id` - 编号，必填）

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 校验回款存在（需要 OWNER 级数据权限）。
2. 若回款关联了回款计划且计划仍存在，则不允许删除。
3. 若回款审批状态为已通过（APPROVE），则不允许删除。
4. 删除回款记录及对应的数据权限。
5. 记录操作日志上下文。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_004_000 | 回款不存在 |
| 1_020_004_002 | 删除回款失败，原因：被回款计划所使用，不允许删除 |
| 1_020_004_008 | 删除回款失败，原因：回款审批已通过 |

### 1.4 获得回款

- **路径**: GET /crm/receivable/get
- **权限**: crm:receivable:query
- **说明**: 根据编号获得回款详情（需要 READ 级数据权限），拼接客户、负责人、创建人、合同信息。

**请求参数**: 无（Query 参数：`id` - 编号，必填）

**响应**: CommonResult&lt;CrmReceivableRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 回款编号 |
| planId | Long | 回款计划编号 |
| returnType | Integer | 回款方式（字典 CRM_RECEIVABLE_RETURN_TYPE） |
| price | BigDecimal | 回款金额 |
| returnTime | LocalDateTime | 计划回款日期 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名字 |
| contractId | Long | 合同编号 |
| contract | CrmContractRespVO | 合同信息（详情接口拼接） |
| ownerUserId | Long | 负责人的用户编号 |
| ownerUserName | String | 负责人名字 |
| ownerUserDeptName | String | 负责人部门 |
| processInstanceId | String | 工作流编号 |
| auditStatus | Integer | 审批状态（字典 CRM_AUDIT_STATUS） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |
| creator | String | 创建人 |
| creatorName | String | 创建人名字 |

**业务逻辑**:
1. 查询回款记录（需要当前用户对该回款有 READ 级数据权限）。
2. 批量拼接客户名称、创建人/负责人昵称、负责人部门名称。
3. 拼接合同完整信息（CrmContractRespVO）。

### 1.5 获得回款分页

- **路径**: GET /crm/receivable/page
- **权限**: crm:receivable:query
- **说明**: 分页获得当前登录用户数据权限范围内的回款列表。

**请求参数 (CrmReceivablePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| no | String | 否 | - | 回款编号 |
| planId | Long | 否 | - | 回款计划编号 |
| customerId | Long | 否 | - | 客户编号 |
| contractId | Long | 否 | - | 合同编号 |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum) | 场景类型，为 null 时表示全部 |
| auditStatus | Integer | 否 | @InEnum(CrmAuditStatusEnum) | 审批状态 |

**响应**: CommonResult&lt;PageResult&lt;CrmReceivableRespVO&gt;&gt;（列表字段同 1.4）

**业务逻辑**:
1. 按查询条件分页查询回款，数据范围限定为当前登录用户有权限的数据。
2. 批量拼接客户名称、创建人/负责人昵称、负责人部门名称、合同信息后返回。

### 1.6 获得回款分页，基于指定客户

- **路径**: GET /crm/receivable/page-by-customer
- **权限**: 已认证（无 @PreAuthorize，校验客户 READ 级数据权限）
- **说明**: 基于指定客户分页查询回款，customerId 必传（断言校验）。

**请求参数 (CrmReceivablePageReqVO)**: 同 1.5，其中 `customerId` 必填（代码断言校验为空时抛出提示"客户编号不能为空"）

**响应**: CommonResult&lt;PageResult&lt;CrmReceivableRespVO&gt;&gt;（列表字段同 1.4）

**业务逻辑**:
1. 断言 customerId 不为空。
2. 需要当前用户对该客户有 READ 级数据权限，按客户维度分页查询回款。
3. 拼接客户、负责人、创建人、合同信息后返回。

### 1.7 导出回款 Excel

- **路径**: GET /crm/receivable/export-excel
- **权限**: crm:receivable:export
- **说明**: 按分页条件导出全部回款数据为 Excel 文件（回款.xls）。

**请求参数 (CrmReceivablePageReqVO)**: 同 1.5（pageSize 强制置为 PAGE_SIZE_NONE，即不分页导出全部）

**响应**: Excel 文件流（列同 CrmReceivableRespVO 的 @ExcelProperty 注解：编号、回款编号、回款计划编号、回款方式、回款金额、计划回款日期、客户名字、合同编号、负责人名字、负责人部门、工作流编号、审批状态、创建时间、更新时间、创建人名字等）

**业务逻辑**:
1. 将 pageSize 设置为 PAGE_SIZE_NONE，按条件查询数据权限内的全部回款。
2. 拼接客户、负责人、创建人、合同信息后通过 ExcelUtils 写出响应流，并记录导出操作日志。

### 1.8 提交回款审批

- **路径**: PUT /crm/receivable/submit
- **权限**: crm:receivable:update
- **说明**: 将草稿状态的回款提交 BPM 审批流程（流程标识 crm-receivable-audit）。

**请求参数**: 无（Query 参数：`id` - 回款编号，必填）

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 校验回款存在，且审批状态为草稿（DRAFT），否则报错。
2. 调用 BPM 创建流程实例（流程定义 Key 为 crm-receivable-audit，业务键为回款编号）。
3. 更新回款的流程实例编号（processInstanceId），并将审批状态更新为审批中（PROCESS）。
4. 记录操作日志（回款编号）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_004_000 | 回款不存在 |
| 1_020_004_003 | 回款提交审核失败，原因：回款没处在未提交状态 |

### 1.9 获得待审核回款数量

- **路径**: GET /crm/receivable/audit-count
- **权限**: crm:receivable:query
- **说明**: 获得当前登录用户待审核的回款数量（用于首页/角标提醒）。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;（待审核数量）

**业务逻辑**:
1. 按当前登录用户统计审批中的回款数量并返回。

### 1.10 审批结果回调（内部监听器，非 HTTP 端点）

- **路径**: 无（BPM 事件监听）
- **权限**: 不适用
- **说明**: CrmReceivableStatusListener 监听 BPM 流程实例状态事件（仅处理流程标识 crm-receivable-audit），回调更新回款审批状态：仅审批中（PROCESS）状态可更新，否则报错；按 BPM 结果映射为审批状态（通过/不通过等）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_004_000 | 回款不存在 |
| 1_020_004_004 | 更新回款审核状态失败，原因：回款不是审核中状态 |

## 2. 回款计划（CrmReceivablePlanController）

### 2.1 创建回款计划

- **路径**: POST /crm/receivable-plan/create
- **权限**: crm:receivable-plan:create
- **说明**: 为合同创建一条回款计划，期数自动递增，并按提醒天数计算提醒时间。

**请求参数 (CrmReceivablePlanSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（新增时不传） |
| customerId | Long | 否 | - | 客户编号（隐藏字段，由 contractId 查询得出） |
| contractId | Long | 是 | @NotNull | 合同编号 |
| ownerUserId | Long | 是 | @NotNull | 负责人编号 |
| returnTime | LocalDateTime | 是 | @NotNull | 计划回款日期 |
| returnType | Integer | 否 | - | 回款方式 |
| price | BigDecimal | 是 | @NotNull | 计划回款金额 |
| remindDays | Integer | 否 | - | 提前几天提醒 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult<Long>（回款计划编号）

**业务逻辑**:
1. 校验关联数据存在：负责人必须存在；合同必须存在（并回填 customerId）。
2. 查询该合同下最大期数的回款计划，新计划期数 = 最大期数 + 1（无计划则从 1 开始）。
3. 若计划回款日期与提醒天数均不为空，计算提醒时间 = 计划回款日期 - 提醒天数。
4. 插入回款计划记录。
5. 创建数据权限，将负责人设置为 OWNER 级别。
6. 记录操作日志上下文。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_004_006 | 创建回款失败，原因：合同不是审核通过状态（validateContract 校验合同） |
| 1_020_005_000 | 回款计划不存在 |

### 2.2 更新回款计划

- **路径**: PUT /crm/receivable-plan/update
- **权限**: crm:receivable-plan:update
- **说明**: 更新回款计划（客户、合同、负责人不允许修改），已关联回款的计划不允许编辑。

**请求参数 (CrmReceivablePlanSaveReqVO)**: 同 2.1（id 必传；客户/合同/负责人字段被强制以库中原值覆盖，前端传入无效）

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 屏蔽负责人、客户、合同等不允许修改的字段。
2. 校验关联数据存在（负责人、合同）与回款计划存在（需要 WRITE 级数据权限）。
3. 若该计划已关联回款（receivableId 不为空），则不允许编辑。
4. 若计划回款日期与提醒天数均不为空，重新计算提醒时间后更新计划。
5. 记录操作日志上下文（旧对象用于差异对比）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_005_000 | 回款计划不存在 |
| 1_020_006_000 | 更想回款计划失败，原因：已经有对应的还款 |

### 2.3 删除回款计划

- **路径**: DELETE /crm/receivable-plan/delete
- **权限**: crm:receivable-plan:delete
- **说明**: 删除回款计划（需要 OWNER 级数据权限）。

**请求参数**: 无（Query 参数：`id` - 编号，必填）

**响应**: CommonResult<Boolean>（是否成功）

**业务逻辑**:
1. 校验回款计划存在。
2. 删除回款计划记录。
3. 删除对应的数据权限。
4. 记录操作日志上下文。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_005_000 | 回款计划不存在 |

### 2.4 获得回款计划

- **路径**: GET /crm/receivable-plan/get
- **权限**: crm:receivable-plan:query
- **说明**: 根据编号获得回款计划详情（需要 READ 级数据权限），拼接客户、负责人、合同、回款信息。

**请求参数**: 无（Query 参数：`id` - 编号，必填）

**响应**: CommonResult&lt;CrmReceivablePlanRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| period | Integer | 期数 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名字 |
| contractId | Long | 合同编号 |
| contractNo | String | 合同编号（No） |
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人名字 |
| returnTime | LocalDateTime | 计划回款日期 |
| returnType | Integer | 计划回款方式 |
| price | BigDecimal | 计划回款金额 |
| receivableId | Long | 回款编号 |
| receivable | CrmReceivableRespVO | 回款信息 |
| remindDays | Integer | 提前几天提醒 |
| remindTime | LocalDateTime | 提醒日期 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |
| creator | String | 创建人 |
| creatorName | String | 创建人名字 |

**业务逻辑**:
1. 查询回款计划记录（需要当前用户对该计划有 READ 级数据权限）。
2. 批量拼接客户名称、负责人/创建人昵称、合同编号（contractNo）。
3. 拼接关联回款完整信息（CrmReceivableRespVO）。

### 2.5 获得回款计划分页

- **路径**: GET /crm/receivable-plan/page
- **权限**: crm:receivable-plan:query
- **说明**: 分页获得当前登录用户数据权限范围内的回款计划列表，支持按提醒类型（待回款/已逾期/已回款）过滤。

**请求参数 (CrmReceivablePlanPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam） |
| customerId | Long | 否 | - | 客户编号 |
| contractNo | String | 否 | - | 合同编号（No） |
| contractId | Long | 否 | - | 合同编号 |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum) | 场景类型，为 null 时表示全部 |
| remindType | Integer | 否 | - | 提醒类型：1 待回款 / 2 已逾期 / 3 已回款，为 null 时表示全部 |

**响应**: CommonResult&lt;PageResult&lt;CrmReceivablePlanRespVO&gt;&gt;（列表字段同 2.4）

**业务逻辑**:
1. 按查询条件分页查询回款计划，数据范围限定为当前登录用户有权限的数据。
2. 批量拼接客户名称、负责人/创建人昵称、合同编号、关联回款信息后返回。

### 2.6 获得回款计划分页，基于指定客户

- **路径**: GET /crm/receivable-plan/page-by-customer
- **权限**: 已认证（无 @PreAuthorize，校验客户 READ 级数据权限）
- **说明**: 基于指定客户分页查询回款计划，customerId 必传（断言校验）。

**请求参数 (CrmReceivablePlanPageReqVO)**: 同 2.5，其中 `customerId` 必填（代码断言校验为空时抛出提示"客户编号不能为空"）

**响应**: CommonResult&lt;PageResult&lt;CrmReceivablePlanRespVO&gt;&gt;（列表字段同 2.4）

**业务逻辑**:
1. 断言 customerId 不为空。
2. 需要当前用户对该客户有 READ 级数据权限，按客户维度分页查询回款计划。
3. 拼接客户、负责人、创建人、合同、回款信息后返回。

### 2.7 导出回款计划 Excel

- **路径**: GET /crm/receivable-plan/export-excel
- **权限**: crm:receivable-plan:export
- **说明**: 按分页条件导出全部回款计划数据为 Excel 文件（回款计划.xls）。

**请求参数 (CrmReceivablePlanPageReqVO)**: 同 2.5（pageSize 强制置为 PAGE_SIZE_NONE，即不分页导出全部）

**响应**: Excel 文件流（列同 CrmReceivablePlanRespVO 的 @ExcelProperty 注解：编号、期数、客户编号、客户名字、合同编号、负责人编号、负责人、计划回款日期、计划回款方式、计划回款金额、回款编号、提前几天提醒、提醒日期、备注、创建时间、更新时间、创建人、创建人名字等）

**业务逻辑**:
1. 将 pageSize 设置为 PAGE_SIZE_NONE，按条件查询数据权限内的全部回款计划。
2. 拼接客户、负责人、创建人、合同、回款信息后通过 ExcelUtils 写出响应流，并记录导出操作日志。

### 2.8 获得回款计划精简列表

- **路径**: GET /crm/receivable-plan/simple-list
- **权限**: crm:receivable-plan:query
- **说明**: 获得回款计划精简列表，主要用于前端的下拉选项（如创建回款时选择计划）。

**请求参数**: 无（Query 参数：`customerId` - 客户编号，必填；`contractId` - 合同编号，必填）

**响应**: CommonResult&lt;List&lt;CrmReceivablePlanRespVO&gt;&gt;（精简，仅以下字段）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| period | Integer | 期数 |
| receivableId | Long | 回款编号 |
| price | BigDecimal | 计划回款金额 |
| returnType | Integer | 计划回款方式 |

**业务逻辑**:
1. 以客户编号 + 合同编号构造分页查询条件（pageNo 置为 PAGE_SIZE_NONE，即全量查询）。
2. 需要当前用户对该客户有 READ 级数据权限，查询回款计划列表。
3. 仅映射 id、period、receivableId、price、returnType 五个字段返回。

### 2.9 获得待回款提醒数量

- **路径**: GET /crm/receivable-plan/remind-count
- **权限**: crm:receivable-plan:query
- **说明**: 获得当前登录用户待回款提醒的数量（用于首页/角标提醒）。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;（待回款提醒数量）

**业务逻辑**:
1. 按当前登录用户统计待回款提醒（待回款/已逾期）的回款计划数量并返回。
