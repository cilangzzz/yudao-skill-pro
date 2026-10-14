# 财务管理接口 (ErpAccountController / ErpFinancePaymentController / ErpFinanceReceiptController)

> ERP 财务管理域，提供结算账户维护、采购付款单与销售收款单的管理（含审核状态流转、收付款项明细及其对采购/销售单据收付款金额的回写）。

## 接口路径前缀

- `/erp/account`（Controller: ErpAccountController）
- `/erp/finance-payment`（Controller: ErpFinancePaymentController）
- `/erp/finance-receipt`（Controller: ErpFinanceReceiptController）

---

## 1. 结算账户（ErpAccountController）

### 1.1 创建结算账户

- **路径**: POST /erp/account/create
- **权限**: erp:account:create
- **说明**: 新增一个结算账户。

**请求参数 (ErpAccountSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 结算账户编号（新增时不传） |
| name | String | 是 | @NotEmpty | 账户名称 |
| no | String | 否 | | 账户编码 |
| remark | String | 否 | | 备注 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 开启状态 |
| sort | Integer | 是 | @NotNull | 排序 |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的结算账户编号 |

**业务逻辑**:
1. 将请求 VO 转换为 ErpAccountDO。
2. 插入数据库。
3. 返回新记录编号。

### 1.2 更新结算账户

- **路径**: PUT /erp/account/update
- **权限**: erp:account:update
- **说明**: 修改已存在的结算账户。

**请求参数 (ErpAccountSaveReqVO)**: 同 1.1，其中 id 必传。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验结算账户存在，不存在抛 ACCOUNT_NOT_EXISTS。
2. 将请求 VO 转换为 ErpAccountDO 后按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_600_000 | 结算账户不存在 |

### 1.3 更新结算账户默认状态

- **路径**: PUT /erp/account/update-default-status
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 设置/取消默认结算账户，全局仅允许一个默认账户。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 结算账户编号 |
| defaultStatus | Boolean | 是 | | 是否默认 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验结算账户存在。
2. 若设置为默认，查询当前的默认账户并将其 defaultStatus 置为 false（保证唯一默认）。
3. 更新目标账户的默认状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_600_000 | 结算账户不存在 |

### 1.4 删除结算账户

- **路径**: DELETE /erp/account/delete
- **权限**: erp:account:delete
- **说明**: 删除指定结算账户。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 结算账户编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验结算账户存在，不存在抛 ACCOUNT_NOT_EXISTS。
2. 按 id 删除。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_600_000 | 结算账户不存在 |

### 1.5 获得结算账户

- **路径**: GET /erp/account/get
- **权限**: erp:account:query
- **说明**: 按编号查询单个结算账户详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 结算账户编号 |

**响应**: CommonResult&lt;ErpAccountRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 结算账户编号 |
| name | String | 账户名称 |
| no | String | 账户编码 |
| remark | String | 备注 |
| status | Integer | 开启状态 |
| sort | Integer | 排序 |
| defaultStatus | Boolean | 是否默认 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按编号查询，转换为 RespVO 返回。

### 1.6 获得结算账户精简列表

- **路径**: GET /erp/account/simple-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 只包含开启状态的结算账户，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ErpAccountRespVO&gt;&gt;，仅填充以下字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 结算账户编号 |
| name | String | 账户名称 |
| defaultStatus | Boolean | 是否默认 |

**业务逻辑**:
1. 查询状态为开启（CommonStatusEnum.ENABLE）的账户列表。
2. 转换为仅含 id/name/defaultStatus 的精简 RespVO 列表返回。

### 1.7 获得结算账户分页

- **路径**: GET /erp/account/page
- **权限**: erp:account:query
- **说明**: 分页查询结算账户。

**请求参数 (ErpAccountPageReqVO)**: 继承 PageParam（pageNo/pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码 |
| pageSize | Integer | 否 | | 每页条数 |
| no | String | 否 | | 账户编码 |
| name | String | 否 | | 账户名称 |
| remark | String | 否 | | 备注 |

**响应**: CommonResult&lt;PageResult&lt;ErpAccountRespVO&gt;&gt;，列表结构同 1.5。

**业务逻辑**: 1. 按条件分页查询并转换为 RespVO。

### 1.8 导出结算账户 Excel

- **路径**: GET /erp/account/export-excel
- **权限**: erp:account:export
- **说明**: 按分页条件导出全部结算账户 Excel（文件名"结算账户.xls"）。

**请求参数 (ErpAccountPageReqVO)**: 同 1.7（内部强制 pageSize 为不分页）。

**响应**: 二进制文件流（Excel），无 CommonResult 包装。

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 查询全部符合条件的账户。
3. 通过 ExcelUtils 写出 Excel 文件。

---

## 2. 付款单（ErpFinancePaymentController）

付款单针对供应商的采购入库（bizType=11）/采购退货（bizType=12）单据登记付款，单据状态采用审核流：10 未审核（PROCESS）、20 已审核（APPROVE）。

### 2.1 创建付款单

- **路径**: POST /erp/finance-payment/create
- **权限**: erp:finance-payment:create
- **说明**: 创建付款单并回写采购单据的已付款金额。

**请求参数 (ErpFinancePaymentSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（创建时不传） |
| paymentTime | LocalDateTime | 是 | @NotNull | 付款时间 |
| financeUserId | Long | 否 | | 财务人员编号 |
| supplierId | Long | 是 | @NotNull | 供应商编号 |
| accountId | Long | 是 | @NotNull | 付款账户编号 |
| discountPrice | BigDecimal | 是 | @NotNull | 优惠金额，单位：元 |
| remark | String | 否 | | 备注 |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 付款项列表 |

items（ErpFinancePaymentSaveReqVO.Item）：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 付款项编号 |
| bizType | Integer | 是 | @NotNull | 业务类型：11 采购入库、12 采购退货 |
| bizId | Long | 是 | @NotNull | 业务编号 |
| paidPrice | BigDecimal | 是 | @NotNull | 已付金额，单位：分 |
| paymentPrice | BigDecimal | 是 | @NotNull | 本次付款，单位：分 |
| remark | String | 否 | | 备注 |

**响应**: CommonResult&lt;Long&gt;，data 为新付款单编号。

**业务逻辑**:
1. 校验付款项有效性：按 bizType 校验对应采购入库单（11）或采购退货单（12）存在且供应商一致，并回填应付金额 totalPrice（退货取负数）与业务单号 bizNo。
2. 校验供应商存在。
3. 结算账户编号非空时校验账户存在且启用。
4. 财务人员编号非空时校验用户存在。
5. 通过 ErpNoRedisDAO 生成付款单号并校验唯一性，重复则抛 FINANCE_PAYMENT_NO_EXISTS。
6. 插入付款单：单号取生成值、状态置为未审核（PROCESS 10），合计金额 = Σ付款项本次付款，实际付款金额 = 合计金额 − 优惠金额。
7. 批量插入付款项。
8. 按业务单汇总付款金额，更新采购入库单的已付款金额 / 采购退货单的退款金额。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_601_004 | 生成付款单号失败，请重新提交 |
| 1_030_600_000 | 结算账户不存在（账户校验） |
| 1_030_600_001 | 结算账户({})未启用（账户校验） |
| 1_030_100_000 | 供应商不存在（供应商校验） |

### 2.2 更新付款单

- **路径**: PUT /erp/finance-payment/update
- **权限**: erp:finance-payment:update
- **说明**: 修改未审核状态的付款单。

**请求参数 (ErpFinancePaymentSaveReqVO)**: 同 2.1，其中 id 必传。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验付款单存在；已审核（APPROVE 20）则抛 FINANCE_PAYMENT_UPDATE_FAIL_APPROVE。
2. 校验供应商存在。
3. 结算账户编号非空时校验账户存在且启用。
4. 财务人员编号非空时校验用户存在。
5. 校验付款项有效性（同创建逻辑，回填金额与业务单号）。
6. 更新付款单并重新计算合计金额、实际付款金额。
7. 对比新老付款项列表差异，批量执行新增、修改、删除。
8. 按业务单重新汇总付款金额，更新采购入库单 / 采购退货单的付款金额。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_601_000 | 付款单不存在 |
| 1_030_601_005 | 付款单({})已审核，无法修改 |
| 1_030_600_000 | 结算账户不存在（账户校验） |
| 1_030_600_001 | 结算账户({})未启用（账户校验） |
| 1_030_100_000 | 供应商不存在（供应商校验） |

### 2.3 更新付款单的状态

- **路径**: PUT /erp/finance-payment/update-status
- **权限**: erp:finance-payment:update-status
- **说明**: 付款单审核 / 反审核。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 付款单编号 |
| status | Integer | 是 | | 目标状态：10 未审核、20 已审核 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验付款单存在。
2. 校验状态：目标状态与当前状态相同，抛 FINANCE_PAYMENT_APPROVE_FAIL（审核）或 FINANCE_PAYMENT_PROCESS_FAIL（反审核）。
3. 通过 updateByIdAndStatus 带条件（原状态）更新状态，更新数为 0 时抛同样异常。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_601_000 | 付款单不存在 |
| 1_030_601_003 | 审核失败，只有未审核的付款单才能审核 |
| 1_030_601_002 | 反审核失败，只有已审核的付款单才能反审核 |

### 2.4 删除付款单

- **路径**: DELETE /erp/finance-payment/delete
- **权限**: erp:finance-payment:delete
- **说明**: 批量删除未审核的付款单及其付款项。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 批量查询付款单，列表为空直接返回。
2. 逐一校验：任一付款单已审核（APPROVE 20）抛 FINANCE_PAYMENT_DELETE_FAIL_APPROVE。
3. 遍历删除付款单及对应付款项。
4. 按被删付款项的业务单重新汇总付款金额，回写采购入库单 / 采购退货单。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_601_001 | 付款单({})已审核，无法删除 |

### 2.5 获得付款单

- **路径**: GET /erp/finance-payment/get
- **权限**: erp:finance-payment:query
- **说明**: 查询付款单详情（含付款项列表）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 付款单编号 |

**响应**: CommonResult&lt;ErpFinancePaymentRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 付款单号 |
| status | Integer | 付款状态（10 未审核、20 已审核） |
| paymentTime | LocalDateTime | 付款时间 |
| financeUserId | Long | 财务人员编号 |
| financeUserName | String | 财务人员名称 |
| supplierId | Long | 供应商编号 |
| supplierName | String | 供应商名称 |
| accountId | Long | 付款账户编号 |
| accountName | String | 付款账户名称 |
| totalPrice | BigDecimal | 合计价格，单位：元 |
| discountPrice | BigDecimal | 优惠金额，单位：元 |
| paymentPrice | BigDecimal | 实际价格，单位：元 |
| remark | String | 备注 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称 |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 付款项列表 |

items（ErpFinancePaymentRespVO.Item）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 付款项编号 |
| bizType | Integer | 业务类型：11 采购入库、12 采购退货 |
| bizId | Long | 业务编号 |
| bizNo | String | 业务单号 |
| totalPrice | BigDecimal | 应付金额 |
| paidPrice | BigDecimal | 已付金额 |
| paymentPrice | BigDecimal | 本次付款 |
| remark | String | 备注 |

**业务逻辑**:
1. 查询付款单，不存在返回 null。
2. 查询该付款单下的付款项列表。
3. 组装 RespVO（含 items）返回。

### 2.6 获得付款单分页

- **路径**: GET /erp/finance-payment/page
- **权限**: erp:finance-payment:query
- **说明**: 分页查询付款单，并拼装关联信息。

**请求参数 (ErpFinancePaymentPageReqVO)**: 继承 PageParam（pageNo/pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码 |
| pageSize | Integer | 否 | | 每页条数 |
| no | String | 否 | | 付款单编号 |
| paymentTime | LocalDateTime[] | 否 | | 付款时间区间（yyyy-MM-dd HH:mm:ss） |
| supplierId | Long | 否 | | 供应商编号 |
| creator | String | 否 | | 创建者 |
| financeUserId | String | 否 | | 财务人员编号 |
| accountId | Long | 否 | | 结算账户编号 |
| status | Integer | 否 | | 付款状态 |
| remark | String | 否 | | 备注 |
| bizNo | String | 否 | | 业务编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpFinancePaymentRespVO&gt;&gt;，结构同 2.5。

**业务逻辑**:
1. 分页查询付款单。
2. 批量查询付款项并按付款单分组。
3. 批量查询供应商、结算账户、管理员（创建人 + 财务人员）信息。
4. 拼装列表：填充 items、供应商名称、账户名称、创建人名称、财务人员名称。

### 2.7 导出付款单 Excel

- **路径**: GET /erp/finance-payment/export-excel
- **权限**: erp:finance-payment:export
- **说明**: 按分页条件导出付款单 Excel（文件名"付款单.xls"）。

**请求参数 (ErpFinancePaymentPageReqVO)**: 同 2.6（内部强制 pageSize 为不分页）。

**响应**: 二进制文件流（Excel），无 CommonResult 包装。

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 查询全部符合条件的付款单并按 2.6 逻辑拼装。
3. 通过 ExcelUtils 写出 Excel 文件。

---

## 3. 收款单（ErpFinanceReceiptController）

收款单针对客户的销售出库（bizType=21）/销售退货（bizType=22）单据登记收款，单据状态采用审核流：10 未审核（PROCESS）、20 已审核（APPROVE）。接口结构与付款单对称，差异仅在关联方（客户）与业务单据方向。

### 3.1 创建收款单

- **路径**: POST /erp/finance-receipt/create
- **权限**: erp:finance-receipt:create
- **说明**: 创建收款单并回写销售单据的已收款金额。

**请求参数 (ErpFinanceReceiptSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（创建时不传） |
| receiptTime | LocalDateTime | 是 | @NotNull | 收款时间 |
| financeUserId | Long | 否 | | 财务人员编号 |
| customerId | Long | 是 | @NotNull | 客户编号 |
| accountId | Long | 是 | @NotNull | 收款账户编号 |
| discountPrice | BigDecimal | 是 | @NotNull | 优惠金额，单位：元 |
| remark | String | 否 | | 备注 |
| items | List&lt;Item&gt; | 是 | @NotEmpty、@Valid | 收款项列表 |

items（ErpFinanceReceiptSaveReqVO.Item）：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 收款项编号 |
| bizType | Integer | 是 | @NotNull | 业务类型：21 销售出库、22 销售退货 |
| bizId | Long | 是 | @NotNull | 业务编号 |
| receiptedPrice | BigDecimal | 是 | @NotNull | 已收金额，单位：分 |
| receiptPrice | BigDecimal | 是 | @NotNull | 本次收款，单位：分 |
| remark | String | 否 | | 备注 |

**响应**: CommonResult&lt;Long&gt;，data 为新收款单编号。

**业务逻辑**:
1. 校验收款项有效性：按 bizType 校验对应销售出库单（21）或销售退货单（22）存在且客户一致，并回填应收金额 totalPrice（退货取负数）与业务单号 bizNo。
2. 校验客户存在。
3. 结算账户编号非空时校验账户存在且启用。
4. 财务人员编号非空时校验用户存在。
5. 通过 ErpNoRedisDAO 生成收款单号并校验唯一性，重复则抛 FINANCE_RECEIPT_NO_EXISTS。
6. 插入收款单：单号取生成值、状态置为未审核（PROCESS 10），合计金额 = Σ收款项本次收款，实际收款金额 = 合计金额 − 优惠金额。
7. 批量插入收款项。
8. 按业务单汇总收款金额，更新销售出库单的已收款金额 / 销售退货单的退款金额。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_602_004 | 生成收款单号失败，请重新提交 |
| 1_030_600_000 | 结算账户不存在（账户校验） |
| 1_030_600_001 | 结算账户({})未启用（账户校验） |
| 1_020_200_000 | 客户不存在（客户校验） |

### 3.2 更新收款单

- **路径**: PUT /erp/finance-receipt/update
- **权限**: erp:finance-receipt:update
- **说明**: 修改未审核状态的收款单。

**请求参数 (ErpFinanceReceiptSaveReqVO)**: 同 3.1，其中 id 必传。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验收款单存在；已审核（APPROVE 20）则抛 FINANCE_RECEIPT_UPDATE_FAIL_APPROVE。
2. 校验客户存在。
3. 结算账户编号非空时校验账户存在且启用。
4. 财务人员编号非空时校验用户存在。
5. 校验收款项有效性（同创建逻辑，回填金额与业务单号）。
6. 更新收款单并重新计算合计金额、实际收款金额。
7. 对比新老收款项列表差异，批量执行新增、修改、删除。
8. 按业务单重新汇总收款金额，更新销售出库单 / 销售退货单的收款金额。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_602_000 | 收款单不存在 |
| 1_030_602_005 | 收款单({})已审核，无法修改 |
| 1_030_600_000 | 结算账户不存在（账户校验） |
| 1_030_600_001 | 结算账户({})未启用（账户校验） |
| 1_020_200_000 | 客户不存在（客户校验） |

### 3.3 更新收款单的状态

- **路径**: PUT /erp/finance-receipt/update-status
- **权限**: erp:finance-receipt:update-status
- **说明**: 收款单审核 / 反审核。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 收款单编号 |
| status | Integer | 是 | | 目标状态：10 未审核、20 已审核 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验收款单存在。
2. 校验状态：目标状态与当前状态相同，抛 FINANCE_RECEIPT_APPROVE_FAIL（审核）或 FINANCE_RECEIPT_PROCESS_FAIL（反审核）。
3. 通过 updateByIdAndStatus 带条件（原状态）更新状态，更新数为 0 时抛同样异常。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_602_000 | 收款单不存在 |
| 1_030_602_003 | 审核失败，只有未审核的收款单才能审核 |
| 1_030_602_002 | 反审核失败，只有已审核的收款单才能反审核 |

### 3.4 删除收款单

- **路径**: DELETE /erp/finance-receipt/delete
- **权限**: erp:finance-receipt:delete
- **说明**: 批量删除未审核的收款单及其收款项。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | | 编号数组 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 批量查询收款单，列表为空直接返回。
2. 逐一校验：任一收款单已审核（APPROVE 20）抛 FINANCE_RECEIPT_DELETE_FAIL_APPROVE。
3. 遍历删除收款单及对应收款项。
4. 按被删收款项的业务单重新汇总收款金额，回写销售出库单 / 销售退货单。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_030_602_001 | 收款单({})已审核，无法删除 |

### 3.5 获得收款单

- **路径**: GET /erp/finance-receipt/get
- **权限**: erp:finance-receipt:query
- **说明**: 查询收款单详情（含收款项列表）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 收款单编号 |

**响应**: CommonResult&lt;ErpFinanceReceiptRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| no | String | 收款单号 |
| status | Integer | 收款状态（10 未审核、20 已审核） |
| receiptTime | LocalDateTime | 收款时间 |
| financeUserId | Long | 财务人员编号 |
| financeUserName | String | 财务人员名称 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| accountId | Long | 收款账户编号 |
| accountName | String | 收款账户名称 |
| totalPrice | BigDecimal | 合计价格，单位：元 |
| discountPrice | BigDecimal | 优惠金额，单位：元 |
| receiptPrice | BigDecimal | 实际价格，单位：元 |
| remark | String | 备注 |
| creator | String | 创建人 |
| creatorName | String | 创建人名称 |
| createTime | LocalDateTime | 创建时间 |
| items | List&lt;Item&gt; | 收款项列表 |

items（ErpFinanceReceiptRespVO.Item）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 收款项编号 |
| bizType | Integer | 业务类型：21 销售出库、22 销售退货 |
| bizId | Long | 业务编号 |
| bizNo | String | 业务单号 |
| totalPrice | BigDecimal | 应收金额 |
| receiptedPrice | BigDecimal | 已收金额 |
| receiptPrice | BigDecimal | 本次收款 |
| remark | String | 备注 |

**业务逻辑**:
1. 查询收款单，不存在返回 null。
2. 查询该收款单下的收款项列表。
3. 组装 RespVO（含 items）返回。

### 3.6 获得收款单分页

- **路径**: GET /erp/finance-receipt/page
- **权限**: erp:finance-receipt:query
- **说明**: 分页查询收款单，并拼装关联信息。

**请求参数 (ErpFinanceReceiptPageReqVO)**: 继承 PageParam（pageNo/pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码 |
| pageSize | Integer | 否 | | 每页条数 |
| no | String | 否 | | 收款单编号 |
| receiptTime | LocalDateTime[] | 否 | | 收款时间区间（yyyy-MM-dd HH:mm:ss） |
| customerId | Long | 否 | | 客户编号 |
| creator | String | 否 | | 创建者 |
| financeUserId | String | 否 | | 财务人员编号 |
| accountId | Long | 否 | | 收款账户编号 |
| status | Integer | 否 | | 收款状态 |
| remark | String | 否 | | 备注 |
| bizNo | String | 否 | | 业务编号 |

**响应**: CommonResult&lt;PageResult&lt;ErpFinanceReceiptRespVO&gt;&gt;，结构同 3.5。

**业务逻辑**:
1. 分页查询收款单。
2. 批量查询收款项并按收款单分组。
3. 批量查询客户、结算账户、管理员（创建人 + 财务人员）信息。
4. 拼装列表：填充 items、客户名称、账户名称、创建人名称、财务人员名称。

### 3.7 导出收款单 Excel

- **路径**: GET /erp/finance-receipt/export-excel
- **权限**: erp:finance-receipt:export
- **说明**: 按分页条件导出收款单 Excel（文件名"收款单.xls"）。

**请求参数 (ErpFinanceReceiptPageReqVO)**: 同 3.6（内部强制 pageSize 为不分页）。

**响应**: 二进制文件流（Excel），无 CommonResult 包装。

**业务逻辑**:
1. 将 pageSize 置为 PAGE_SIZE_NONE（不分页）。
2. 查询全部符合条件的收款单并按 3.6 逻辑拼装。
3. 通过 ExcelUtils 写出 Excel 文件。
