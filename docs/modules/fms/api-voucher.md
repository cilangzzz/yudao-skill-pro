# 凭证管理接口 (FmsVoucherController)

> 提供 FMS 财务模块凭证的创建、编辑、审核、整理（重编号）、移动、删除、查询、打印、导入导出与科目汇总等能力，是账簿与报表取数的数据源头。

## 接口路径前缀

/fms/voucher  (Controller: FmsVoucherController)

> 通用说明：所有端点均要求登录，并先校验账套访问权限（写操作校验 `validateAccountSetWritePermission`，查询校验 `validateAccountSetReadPermission`），失败时抛出 `ACCOUNT_SET_NOT_EXISTS`（1_052_100_000）或 `ACCOUNT_SET_ACCESS_DENIED`（1_052_100_002），下文各端点错误码不再重复列出。

## 1. 凭证写操作

### 1.1 创建凭证

- **路径**: POST /fms/voucher/create
- **权限**: fms:voucher:create
- **说明**: 新增一张凭证及其分录，凭证初始状态为待审核。

**请求参数 (FmsVoucherSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 凭证编号（创建时不传） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| voucherWordId | Long | 是 | @NotNull | 凭证字编号 |
| voucherNumber | Integer | 是 | @NotNull、@Min(1) | 凭证号 |
| voucherTime | LocalDateTime | 是 | @NotNull | 凭证日期 |
| attachmentCount | Integer | 是 | @NotNull、@Min(0) | 附单据张数 |
| entries | List&lt;FmsVoucherEntrySaveReqVO&gt; | 是 | @Valid、@Size(min = 2) | 凭证分录数组，至少两条 |

FmsVoucherEntrySaveReqVO 分录结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 凭证分录编号 |
| digest | String | 是 | @NotBlank、@Size(max = 500) | 摘要内容 |
| subjectId | Long | 是 | @NotNull | 科目编号 |
| quantity | BigDecimal | 否 | @DecimalMin(0)、@Digits(14,4) | 数量 |
| unitPrice | BigDecimal | 否 | @DecimalMin(0)、@Digits(12,6) | 单价 |
| debitAmount | BigDecimal | 否 | @Digits(16,2) | 借方金额 |
| creditAmount | BigDecimal | 否 | @Digits(16,2) | 贷方金额 |
| auxiliaries | List&lt;AuxiliaryItem&gt; | 否 | @Valid | 辅助核算项目数组 |
| auxiliaries[].typeId | Long | 是 | @NotNull | 辅助核算类别编号 |
| auxiliaries[].itemId | Long | 是 | @NotNull | 辅助核算项目编号 |

**响应**: CommonResult&lt;Long&gt;，凭证编号。

**业务逻辑**:
1. 校验账套写权限，并锁定账套以串行化同账套的凭证号写操作。
2. 校验凭证日期所在会计期间未结账、凭证字存在、凭证号在该会计期间内唯一（凭证日期归一化为当天 00:00）。
3. 校验并构造分录：至少两条有效分录；科目必须存在、已启用且为末级科目；每条分录借/贷金额只能填一项且不能为 0；校验数量核算规则；按科目配置校验辅助核算项目完整性并生成名称快照。
4. 校验凭证借贷平衡（借方合计 = 贷方合计），并补充分录辅助核算组合编号。
5. 插入凭证主表（汇总借/贷金额，total = 借方合计，状态为待审核），唯一键冲突时抛凭证号重复错误。
6. 逐条插入凭证分录，记录操作日志上下文，返回凭证编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |
| 1_052_103_002 | 该期间的凭证号已存在 |
| 1_052_103_003 | 凭证至少需要两条有效分录 |
| 1_052_103_004 | 凭证分录只能填写借方或贷方金额 |
| 1_052_103_005 | 凭证借贷金额不平衡 |
| 1_052_103_008 | 凭证分录使用了已停用科目 |
| 1_052_103_009 | 凭证分录不能使用非末级科目 |
| 1_052_103_010 | 凭证分录的辅助核算项目不完整 |
| 1_052_103_011 | 凭证分录的数量核算信息不正确 |
| 1_052_101_000 | 科目不存在 |

### 1.2 更新凭证

- **路径**: PUT /fms/voucher/update
- **权限**: fms:voucher:update
- **说明**: 编辑凭证头信息并整体重建分录。

**请求参数 (FmsVoucherSaveReqVO)**: 同 1.1，其中 id 必传（要更新的凭证编号）。

**响应**: CommonResult&lt;Boolean&gt;，固定 true。

**业务逻辑**:
1. 校验账套写权限并锁定账套。
2. 校验凭证存在且属于该账套、不是结账生成的凭证、未处于已审核状态。
3. 分别校验原凭证日期与新凭证日期所在会计期间均未结账。
4. 校验凭证字存在、凭证号在期间内唯一（排除自身）。
5. 校验并构造分录（校验规则同 1.1），汇总借贷金额。
6. 更新凭证主表（不更新附件），并按分录 id 差量更新分录：新增插入、已有修改、缺失删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_000 | 凭证不存在 |
| 1_052_103_001 | 凭证字不存在 |
| 1_052_103_002 | 该期间的凭证号已存在 |
| 1_052_103_003 | 凭证至少需要两条有效分录 |
| 1_052_103_004 | 凭证分录只能填写借方或贷方金额 |
| 1_052_103_005 | 凭证借贷金额不平衡 |
| 1_052_103_006 | 已审核凭证不能编辑或删除 |
| 1_052_103_008 | 凭证分录使用了已停用科目 |
| 1_052_103_009 | 凭证分录不能使用非末级科目 |
| 1_052_103_010 | 凭证分录的辅助核算项目不完整 |
| 1_052_103_011 | 凭证分录的数量核算信息不正确 |
| 1_052_103_029 | 结账生成凭证不能编辑、审核或删除 |
| 1_052_101_000 | 科目不存在 |

### 1.3 更新凭证附件

- **路径**: PUT /fms/voucher/update-attachments
- **权限**: fms:voucher:update
- **说明**: 整体覆盖凭证的附件地址数组。

**请求参数 (FmsVoucherAttachmentUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 凭证编号 |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| attachmentUrls | List&lt;String&gt; | 否 | @Size(max = 100) | 附件地址数组，最多 100 个 |

**响应**: CommonResult&lt;Boolean&gt;，固定 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验凭证存在且属于该账套、不是结账生成凭证、未审核。
3. 校验凭证所在会计期间未结账。
4. 将附件地址数组整体更新（入参为 null 时置为空数组）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_000 | 凭证不存在 |
| 1_052_103_006 | 已审核凭证不能编辑或删除 |
| 1_052_103_029 | 结账生成凭证不能编辑、审核或删除 |

### 1.4 删除凭证

- **路径**: DELETE /fms/voucher/delete-list
- **权限**: fms:voucher:delete
- **说明**: 批量删除凭证及其分录。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 凭证编号数组 |

**响应**: CommonResult&lt;Boolean&gt;，固定 true。

**业务逻辑**:
1. 校验账套写权限并锁定账套。
2. 批量校验凭证存在且属于该账套（数量不一致即抛凭证不存在）。
3. 校验所选凭证均不是结账生成凭证、均未审核。
4. 逐张校验凭证所在会计期间未结账。
5. 先删除凭证分录，再批量删除凭证。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_000 | 凭证不存在 |
| 1_052_103_006 | 已审核凭证不能编辑或删除 |
| 1_052_103_029 | 结账生成凭证不能编辑、审核或删除 |

### 1.5 审核或反审核凭证

- **路径**: PUT /fms/voucher/update-review-status
- **权限**: fms:voucher:review
- **说明**: 对一批凭证执行审核（待审核 → 已审核）或反审核（已审核 → 待审核）。

**请求参数 (FmsVoucherReviewReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 凭证编号数组 |
| status | Integer | 是 | @NotNull、@InEnum(FmsVoucherStatusEnum) | 目标审核状态：0 待审核（反审核）/ 1 已审核（审核） |

**响应**: CommonResult&lt;Boolean&gt;，固定 true。

**业务逻辑**:
1. 校验账套写权限。
2. 校验目标状态只能是待审核（0）或已审核（1），否则状态流转不正确。
3. 批量校验凭证存在且属于该账套，且不是结账生成凭证。
4. 逐张校验凭证所在会计期间未结账。
5. 校验状态流转方向：审核要求当前为待审核，反审核要求当前为已审核，否则抛状态流转错误。
6. 批量更新审核状态：审核时记录审核人为当前用户，反审核时清空审核人。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_000 | 凭证不存在 |
| 1_052_103_007 | 凭证状态流转不正确 |
| 1_052_103_029 | 结账生成凭证不能编辑、审核或删除 |

### 1.6 整理凭证

- **路径**: PUT /fms/voucher/tidy
- **权限**: fms:voucher:tidy
- **说明**: 对指定月份（可按凭证字过滤）的凭证从起始编号开始重新连续编号，消除断号或按日期重排。

**请求参数 (FmsVoucherTidyReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| month | String | 是 | @NotBlank、@Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 整理月份，格式 yyyy-MM |
| voucherWordId | Long | 否 | - | 凭证字编号，为空时整理全部凭证字 |
| startNumber | Integer | 是 | @NotNull、@Min(1) | 起始编号 |
| type | Integer | 是 | @NotNull、@InEnum(FmsVoucherTidyTypeEnum) | 整理方式：1 按凭证号顺次前移补齐断号 / 2 按凭证日期重新顺次编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定 true。

**业务逻辑**:
1. 校验账套写权限并锁定账套。
2. 解析整理月份，校验该会计期间未结账；指定凭证字时校验凭证字存在。
3. 按凭证字、起始编号和整理方式查询该月待整理凭证列表，为空时直接返回。
4. 按凭证字分组，对每组凭证从 startNumber 起按顺序分配新凭证号。
5. 先将待整理凭证批量写入临时负数凭证号（不占用正常凭证号，避免唯一键冲突），再批量写入最终凭证号完成重编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |

### 1.7 移动凭证

- **路径**: PUT /fms/voucher/move
- **权限**: fms:voucher:move
- **说明**: 将指定月份、凭证字下原凭证号的凭证移动到更小的目标凭证号，区间内其余凭证号顺延。

**请求参数 (FmsVoucherMoveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| month | String | 是 | @NotBlank、@Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 凭证月份，格式 yyyy-MM |
| voucherWordId | Long | 是 | @NotNull | 凭证字编号 |
| sourceNumber | Integer | 是 | @NotNull、@Min(1) | 原凭证号 |
| targetNumber | Integer | 是 | @NotNull、@Min(1) | 移动到的凭证号 |

**响应**: CommonResult&lt;Boolean&gt;，固定 true。

**业务逻辑**:
1. 校验账套写权限并锁定账套。
2. 解析凭证月份，校验该会计期间未结账、凭证字存在。
3. 校验目标凭证号必须小于原凭证号，否则抛移动范围错误。
4. 查询目标号与原号之间的凭证区间，定位原凭证号对应的凭证，不存在或不唯一时抛要移动的凭证不存在。
5. 先将区间内凭证批量写入临时负数凭证号，再将原凭证号写入目标号、区间内其余凭证号加 1 顺延，完成移动。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |
| 1_052_103_023 | 移动到的凭证号必须小于原凭证号 |
| 1_052_103_024 | 要移动的凭证不存在 |

## 2. 凭证查询

### 2.1 获得凭证详情

- **路径**: GET /fms/voucher/get
- **权限**: fms:voucher:query 或 fms:voucher:update（任一）
- **说明**: 获得单张凭证详情，含分录、凭证字名称、制单人/审核人昵称。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 凭证编号 |

**响应**: CommonResult&lt;FmsVoucherRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 凭证编号 |
| accountSetId | Long | 账套编号 |
| voucherWordId | Long | 凭证字编号 |
| voucherWordName | String | 凭证字名称 |
| voucherNumber | Integer | 凭证号 |
| voucherTime | LocalDateTime | 凭证日期 |
| attachmentUrls | List&lt;String&gt; | 附件地址数组 |
| attachmentCount | Integer | 附件数 |
| debitAmount | BigDecimal | 借方金额（合计） |
| creditAmount | BigDecimal | 贷方金额（合计） |
| total | BigDecimal | 合计金额 |
| status | Integer | 审核状态：0 待审核 / 1 已审核 / 2 已驳回 等 |
| closingGenerated | Boolean | 是否为结账生成凭证 |
| creatorUserId | Long | 制单人后台用户编号 |
| creatorUserName | String | 制单人名称 |
| reviewerUserId | Long | 审核人后台用户编号 |
| reviewerUserName | String | 审核人名称 |
| createTime | LocalDateTime | 创建时间 |
| entries | List&lt;Entry&gt; | 凭证分录数组 |

Entry 分录结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分录编号 |
| digest | String | 摘要内容 |
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| quantity | BigDecimal | 数量 |
| unitPrice | BigDecimal | 单价 |
| debitAmount | BigDecimal | 借方金额 |
| creditAmount | BigDecimal | 贷方金额 |
| sort | Integer | 显示顺序 |
| assistCombinationId | Long | 辅助核算组合编号 |
| auxiliaries | List&lt;AuxiliaryItem&gt; | 辅助核算项目数组 |

Entry.AuxiliaryItem 结构：

| 字段 | 类型 | 说明 |
|-----|------|------|
| type | Integer | 辅助核算类型 |
| typeId | Long | 辅助核算类别编号 |
| itemId | Long | 辅助核算项目编号 |
| name | String | 辅助核算项目名称 |

**业务逻辑**:
1. 校验账套读权限。
2. 校验凭证存在且属于该账套，否则抛凭证不存在。
3. 批量加载凭证字、分录、制单人/审核人用户信息与结账生成凭证集合。
4. 组装响应：填充分录、凭证字名称、制单人/审核人昵称、制单人编号及结账生成标识。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_000 | 凭证不存在 |

### 2.2 获得凭证分页

- **路径**: GET /fms/voucher/page
- **权限**: fms:voucher:query
- **说明**: 按多条件分页查询凭证，支持按摘要、科目、金额范围过滤分录后再筛选凭证。

**请求参数 (FmsVoucherPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam，默认 1） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam，默认 10） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 否 | @Size(max = 200) | 凭证编号数组 |
| voucherTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 凭证日期范围 |
| voucherWordId | Long | 否 | - | 凭证字编号 |
| voucherNumber | Integer | 否 | - | 凭证号 |
| digest | String | 否 | - | 摘要关键词 |
| subjectId | Long | 否 | - | 科目编号（含全部下级科目） |
| minAmount | BigDecimal | 否 | - | 最小金额 |
| maxAmount | BigDecimal | 否 | - | 最大金额 |
| creatorUserId | Long | 否 | - | 制单人后台用户编号 |
| status | Integer | 否 | @InEnum(FmsVoucherStatusEnum) | 审核状态 |

**响应**: CommonResult&lt;PageResult&lt;FmsVoucherRespVO&gt;&gt;，列表项结构同 2.1。

**业务逻辑**:
1. 校验账套读权限。
2. 当指定科目、摘要关键词或金额范围时，先按条件查询匹配的凭证分录获得凭证编号集合（科目条件会展开为该科目及全部下级科目）；无匹配分录时直接返回空分页。
3. 按条件分页查询凭证。
4. 批量拼接分录、凭证字名称、制单人/审核人昵称与结账生成标识后返回。

**错误码**: （除通用账套权限错误码外无专属错误码）

### 2.3 获得下一凭证号

- **路径**: GET /fms/voucher/next-number
- **权限**: fms:voucher:query、fms:voucher:create、fms:voucher:update（任一）
- **说明**: 计算指定账套、凭证字、会计期间下的下一个可用凭证号。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| voucherWordId | Long | 是 | @NotNull | 凭证字编号 |
| voucherTime | LocalDateTime | 是 | @NotNull、@DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 凭证日期 |

**响应**: CommonResult&lt;Integer&gt;，下一凭证号。

**业务逻辑**:
1. 校验账套读权限、凭证字存在。
2. 按凭证日期所属月份，查询该期间内该凭证字的最后一张凭证。
3. 存在最后一张凭证时返回其凭证号 + 1，否则返回 1。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |

## 3. 科目余额辅助查询

### 3.1 获得凭证科目余额列表

- **路径**: GET /fms/voucher/subject-balance-list
- **权限**: fms:voucher:query、fms:voucher:create、fms:voucher:update（任一）
- **说明**: 录入凭证时按会计期间查询科目期末余额树（供带入分录余额参考）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| month | String | 是 | @Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 会计期间，格式 yyyy-MM |

**响应**: CommonResult&lt;List&lt;FmsVoucherSubjectBalanceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| subjectId | Long | 科目编号 |
| balanceDirection | String | 余额方向，如 `借` |
| balance | BigDecimal | 余额 |

**业务逻辑**:
1. 调用账簿服务查询该账套、该期间（起止均为 month）的科目余额列表（树形含子级）。
2. 递归遍历科目余额树并展平为列表。
3. 每个节点生成一条响应：余额方向取期末余额方向，余额取期末借方金额与期末贷方金额之和（空值按 0 处理）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |

### 3.2 获得凭证辅助核算组合余额

- **路径**: GET /fms/voucher/auxiliary-balance
- **权限**: fms:voucher:query、fms:voucher:create、fms:voucher:update（任一）
- **说明**: 查询某科目在指定期间、指定辅助核算项目组合下的余额。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| month | String | 是 | @Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 会计期间，格式 yyyy-MM |
| subjectId | Long | 是 | @NotNull | 科目编号 |
| auxiliaryItemIds | List&lt;Long&gt; | 是 | @NotEmpty | 辅助核算项目编号数组 |

**响应**: CommonResult&lt;FmsVoucherSubjectBalanceRespVO&gt;，结构同 3.1。

**业务逻辑**:
1. 调用账簿服务计算该科目与辅助核算项目组合在该期间的带符号余额。
2. 根据带符号余额推断余额方向（借/贷）。
3. 返回科目编号、余额方向与余额绝对值。

**错误码**: （除通用账套权限错误码外无专属错误码）

## 4. 打印与导入导出

### 4.1 获得待打印凭证列表

- **路径**: GET /fms/voucher/print-list
- **权限**: fms:voucher:print
- **说明**: 按查询条件返回全部待打印凭证（不分页），供打印排版使用。

**请求参数 (FmsVoucherPageReqVO)**: 同 2.2（pageSize 由后端强制置为不分页，查询全部）。

**响应**: CommonResult&lt;List&lt;FmsVoucherRespVO&gt;&gt;，列表项结构同 2.1。

**业务逻辑**:
1. 校验账套读权限。
2. 将分页大小置为不分页，按条件查询全部符合条件的凭证。
3. 批量拼接分录、凭证字名称、制单人/审核人昵称与结账生成标识后返回。

**错误码**: （除通用账套权限错误码外无专属错误码）

### 4.2 导出凭证

- **路径**: GET /fms/voucher/export-excel
- **权限**: fms:voucher:export
- **说明**: 按查询条件导出凭证 Excel（凭证列表.xls），每条分录一行。

**请求参数 (FmsVoucherPageReqVO)**: 同 2.2（pageSize 由后端强制置为不分页，导出全部）。

**响应**: Excel 文件流（FmsVoucherExportRespVO）

| 字段 | 类型 | 说明 |
|-----|------|------|
| voucherTime | LocalDateTime | 凭证日期（yyyy-MM-dd） |
| voucherWordName | String | 凭证字 |
| voucherNumber | Integer | 凭证号 |
| digest | String | 摘要 |
| subjectCode | String | 科目代码 |
| subjectName | String | 科目名称（含辅助核算项目名称拼接） |
| debitAmount | BigDecimal | 借方金额 |
| creditAmount | BigDecimal | 贷方金额 |
| attachmentCount | Integer | 附件数 |
| creatorUserName | String | 制单人 |
| reviewerUserName | String | 审核人 |

**业务逻辑**:
1. 校验账套读权限，分页大小置为不分页后查询全部符合条件的凭证。
2. 拼接凭证响应（分录、凭证字名称、制单人/审核人昵称）。
3. 将每张凭证按分录展开为导出行，科目有辅助核算时在科目名称后追加 ` / 项目名、项目名`。
4. 通过 Excel 工具写入响应并记录导出操作日志。

**错误码**: （除通用账套权限错误码外无专属错误码）

### 4.3 获得凭证导入模板

- **路径**: GET /fms/voucher/get-import-template
- **权限**: fms:voucher:import
- **说明**: 下载含账套基础数据（凭证字、科目、辅助核算）的凭证导入 Excel 模板。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: Excel 文件流（凭证导入模板.xlsx）。

**业务逻辑**:
1. 校验账套读权限。
2. 加载该账套的凭证字列表、科目列表、辅助核算类别列表与辅助核算项目列表。
3. 以模板数据生成 xlsx 附件写入响应，并记录导出操作日志。

**错误码**: （除通用账套权限错误码外无专属错误码）

### 4.4 导入凭证

- **路径**: POST /fms/voucher/import
- **权限**: fms:voucher:import
- **说明**: 上传按模板填写的 Excel 批量导入凭证，失败行生成错误数据文件。

**请求参数 (form-data 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| file | MultipartFile | 是 | - | Excel 文件（模板见 4.3） |

**响应**: CommonResult&lt;FmsVoucherImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalRowCount | Integer | 总分录数 |
| successRowCount | Integer | 成功分录数 |
| failureRowCount | Integer | 失败分录数 |
| totalVoucherCount | Integer | 总凭证数 |
| successVoucherCount | Integer | 成功凭证数 |
| failureVoucherCount | Integer | 失败凭证数 |
| errorFileUrl | String | 错误数据文件地址（无错误行时为空） |

**业务逻辑**:
1. 校验账套读权限并加载导入模板依赖（凭证字、科目、辅助核算类别与项目），解析上传的 Excel 为行数据，解析失败抛导入模板格式不正确。
2. 逐行校验：字段格式、凭证字存在、科目编码存在且启用且为末级、借/贷金额只能填一项且不为 0、数量核算规则（数量 × 单价 = 金额）、按科目配置校验辅助核算项目编码。
3. 按「凭证日期 + 凭证字 + 凭证号」对行分组，组级校验：至少两条分录、至少一条摘要、借贷平衡、所在会计期间未结账、期间内凭证号未被占用。
4. 校验组间业务键（会计期间 + 凭证字 + 凭证号）不重复。
5. 无错误的凭证组整体落库（凭证状态为待审核，分录快照科目与辅助核算信息），失败组汇总为错误行。
6. 存在错误行时生成错误数据 Excel 并上传文件服务器，返回统计结果与错误文件地址。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_025 | 请选择要导入的凭证文件 |
| 1_052_103_027 | 凭证导入模板格式不正确 |

## 5. 凭证汇总

### 5.1 获得凭证汇总

- **路径**: GET /fms/voucher/statistics/list
- **权限**: fms:voucher:statistics:query
- **说明**: 按会计期间区间与科目级次汇总各科目的借/贷发生额。

**请求参数 (FmsVoucherStatisticsReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| startMonth | String | 是 | @NotNull、@Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 开始会计期间，格式 yyyy-MM |
| endMonth | String | 是 | @NotNull、@Pattern(\\d{4}-(0[1-9]\|1[0-2])) | 结束会计期间，格式 yyyy-MM |
| voucherWordId | Long | 否 | - | 凭证字编号 |
| minVoucherNumber | Integer | 否 | @Min(1) | 最小凭证号 |
| maxVoucherNumber | Integer | 否 | @Min(1) | 最大凭证号 |
| minLevel | Integer | 否 | @Min(1)、@Max(10) | 最小科目级次 |
| maxLevel | Integer | 否 | @Min(1)、@Max(10) | 最大科目级次 |

**响应**: CommonResult&lt;List&lt;FmsVoucherStatisticsRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| level | Integer | 科目级次 |
| debitAmount | BigDecimal | 借方金额（含下级汇总） |
| creditAmount | BigDecimal | 贷方金额（含下级汇总） |

**业务逻辑**:
1. 校验账套读权限。
2. 校验开始会计期间不晚于结束会计期间。
3. 校验科目级次范围（min ≤ max）与凭证号范围（min ≤ max），否则抛汇总查询范围错误；未传级次时默认 1。
4. 指定凭证字时校验凭证字存在。
5. 查询期间区间内（按凭证号、凭证字过滤）各科目直接的借/贷发生额，无数据时返回空列表。
6. 加载全部科目并构建父子关系，对级次在范围内的科目通过广度优先遍历汇总自身及全部下级科目的发生额。
7. 仅返回有发生额的科目列表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |
| 1_052_103_022 | 凭证汇总查询范围不正确 |
| 1_052_104_000 | 开始会计期间不能晚于结束会计期间 |

### 5.2 导出凭证汇总

- **路径**: GET /fms/voucher/statistics/export-excel
- **权限**: fms:voucher:statistics:export
- **说明**: 按 5.1 相同的查询与汇总逻辑导出凭证汇总 Excel（凭证汇总表.xls）。

**请求参数 (FmsVoucherStatisticsReqVO)**: 同 5.1。

**响应**: Excel 文件流（FmsVoucherStatisticsRespVO，含科目编码、科目名称、借方金额、贷方金额列）。

**业务逻辑**:
1. 执行与 5.1 相同的权限、参数校验与科目发生额汇总逻辑。
2. 将汇总结果通过 Excel 工具写入响应，并记录导出操作日志。

**错误码**: 同 5.1。
