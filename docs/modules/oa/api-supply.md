# 办公用品接口 (OaSupplyItemController / OaSupplyApplyController / OaSupplyIssueController)

> 提供办公用品档案与库存管理（创建/更新/删除/入库/分页查询）、员工用品领用申请（草稿、提交发起 BPM 审批、取消、详情分页）以及审批通过后的发放与归还处理。

## 接口路径前缀

- /oa/supply-item  (Controller: OaSupplyItemController) —— 办公用品档案与库存
- /oa/supply-apply  (Controller: OaSupplyApplyController) —— 用品领用申请
- /oa/supply-issue  (Controller: OaSupplyIssueController) —— 领用发放与归还

## 1. 办公用品管理（OaSupplyItemController）

### 1.1 创建办公用品

- **路径**: POST /oa/supply-item/create
- **权限**: oa:supply-item:create
- **说明**: 新增一条办公用品档案，校验物品编码唯一与所属部门合法。

**请求参数 (OaSupplyItemSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号（创建时不传） |
| deptId | Long | 是 | @NotNull | 所属部门编号 |
| name | String | 是 | @NotBlank、@Size(max = 128) | 物品名称 |
| no | String | 否 | @Size(max = 64) | 物品编码，需唯一 |
| category | Integer | 是 | @NotNull、@InEnum(OaSupplyCategoryEnum) | 类别（1 文具类、2 打印耗材、3 生活用品、4 电脑办公、5 办公设备、6 财务用品、7 电器） |
| manageType | Integer | 是 | @NotNull、@InEnum(OaSupplyManageTypeEnum) | 管理类型（1 消耗品、2 借用品、3 资产品） |
| model | String | 否 | @Size(max = 128) | 规格型号 |
| unit | String | 否 | @Size(max = 32) | 计量单位 |
| referencePrice | BigDecimal | 否 | @DecimalMin(0)、@Digits(integer = 16, fraction = 2) | 参考单价 |
| stockQuantity | Integer | 是 | @NotNull、@Min(0) | 库存数量 |
| minStockQuantity | Integer | 是 | @NotNull、@Min(0) | 最低库存 |
| picUrl | String | 否 | @Size(max = 2048) | 物品图片 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启、1 禁用） |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| remark | String | 否 | @Size(max = 500) | 备注 |

**响应**: CommonResult\<Long\>，返回新建办公用品编号。

**业务逻辑**:
1. 校验物品编码唯一：编码非空时按 no 查询，已存在其他记录则抛 `SUPPLY_ITEM_NO_DUPLICATE`。
2. 调用 DeptApi 校验所属部门合法性。
3. 转换为 OaSupplyItemDO 插入数据库，返回新物品编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_001 | 用品编号已存在 |

### 1.2 更新办公用品

- **路径**: PUT /oa/supply-item/update
- **权限**: oa:supply-item:update
- **说明**: 修改办公用品档案，编码仍需保持唯一。

**请求参数 (OaSupplyItemSaveReqVO)**: 与「创建办公用品」相同（`id` 此时必传用于定位记录）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验物品存在，否则抛 `SUPPLY_ITEM_NOT_EXISTS`。
2. 校验物品编码唯一（排除自身记录）。
3. 调用 DeptApi 校验所属部门合法性。
4. 按 id 更新物品记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_000 | 办公用品不存在 |
| 1_054_200_001 | 用品编号已存在 |

### 1.3 删除办公用品

- **路径**: DELETE /oa/supply-item/delete?id={id}
- **权限**: oa:supply-item:delete
- **说明**: 删除办公用品，存在未归还或待发放明细时禁止删除。

**请求参数**: 无（Query 参数 `id`：办公用品编号，必填）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验物品存在，否则抛 `SUPPLY_ITEM_NOT_EXISTS`。
2. 查询该物品未归还的明细数量（借用品管理类型），大于 0 时抛 `SUPPLY_ITEM_NOT_RETURNED`。
3. 查询该物品待发放的明细数量，大于 0 时抛 `SUPPLY_ITEM_PENDING_ISSUE`。
4. 校验通过后删除物品记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_000 | 办公用品不存在 |
| 1_054_200_002 | 物品尚有未归还数量，不能删除 |
| 1_054_200_004 | 物品尚有待发放明细，不能删除 |

### 1.4 获得办公用品

- **路径**: GET /oa/supply-item/get?id={id}
- **权限**: oa:supply-item:query
- **说明**: 按编号查询单个办公用品详情。

**请求参数**: 无（Query 参数 `id`：办公用品编号，必填）。

**响应**: CommonResult\<OaSupplyItemRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| deptId | Long | 所属部门编号 |
| deptName | String | 所属部门（分页接口拼接） |
| name | String | 物品名称 |
| no | String | 物品编码 |
| category | Integer | 类别 |
| manageType | Integer | 管理类型 |
| model | String | 规格型号 |
| unit | String | 计量单位 |
| referencePrice | BigDecimal | 参考单价 |
| stockQuantity | Integer | 库存数量 |
| minStockQuantity | Integer | 最低库存 |
| picUrl | String | 物品图片 |
| status | Integer | 状态 |
| sort | Integer | 显示顺序 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间（时间戳毫秒） |

**业务逻辑**:
1. 按 id 查询物品并转换为 RespVO 返回。

### 1.5 获得办公用品分页

- **路径**: GET /oa/supply-item/page
- **权限**: oa:supply-item:query
- **说明**: 按条件分页查询办公用品，并拼接所属部门名称。

**请求参数 (OaSupplyItemPageReqVO)**: 继承 PageParam（pageNo/pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | 无 | 物品名称，模糊匹配 |
| no | String | 否 | 无 | 物品编码 |
| category | Integer | 否 | 无 | 类别 |
| manageType | Integer | 否 | 无 | 管理类型 |
| status | Integer | 否 | 无 | 状态 |

**响应**: CommonResult\<PageResult\<OaSupplyItemRespVO\>\>，字段同「获得办公用品」，额外拼接 deptName。

**业务逻辑**:
1. 按名称/编码/类别/管理类型/状态条件分页查询物品。
2. 批量查询物品所属部门，为列表逐条拼接部门名称 deptName。

### 1.6 获得可领用的办公用品分页

- **路径**: GET /oa/supply-item/select-page
- **权限**: 已认证（仅登录，无独立权限标识）
- **说明**: 供领用申请选择物品使用，仅返回启用状态的办公用品。

**请求参数 (OaSupplyItemPageReqVO)**: 与「获得办公用品分页」相同。

**响应**: CommonResult\<PageResult\<OaSupplyItemRespVO\>\>

**业务逻辑**:
1. 强制将查询条件 status 置为「开启」（CommonStatusEnum.ENABLE）。
2. 复用分页查询返回启用状态的物品分页（不拼接部门名称）。

### 1.7 办公用品入库

- **路径**: PUT /oa/supply-item/stock-in
- **权限**: oa:supply-item:stock-in
- **说明**: 对指定办公用品执行入库，原子增加库存数量。

**请求参数 (OaSupplyItemStockInReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 办公用品编号 |
| quantity | Integer | 是 | @NotNull、@Min(1) | 入库数量 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验物品存在，否则抛 `SUPPLY_ITEM_NOT_EXISTS`。
2. 调用 updateSupplyItemStockQuantity 以正数原子增加库存数量（底层 UPDATE 扣减失败会抛 `SUPPLY_STOCK_INSUFFICIENT`，入库为正向增加不会触发）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_000 | 办公用品不存在 |
| 1_054_200_003 | 用品库存不足（库存原子增减共享校验） |

## 2. 用品领用申请（OaSupplyApplyController）

### 2.1 创建用品领用申请

- **路径**: POST /oa/supply-apply/create
- **权限**: oa:supply-apply:create
- **说明**: 创建一条状态为「未开始」的领用申请草稿，自动生成申请单号并保存领用明细。

**请求参数 (OaSupplyApplySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 编号（创建时不传） |
| applyTime | LocalDateTime | 是 | @NotNull | 领用日期（时间戳毫秒） |
| useType | Integer | 是 | @NotNull、@InEnum(OaSupplyUseTypeEnum) | 使用类型（1 领用、2 借用） |
| pickupMethod | Integer | 是 | @NotNull、@Min(1) | 领取方式 |
| reason | String | 是 | @NotBlank、@Size(max = 500) | 申请事由 |
| fileUrls | List\<String\> | 否 | @Size(max = 10)，元素 @NotBlank | 附件地址列表，最多 10 个 |
| remark | String | 否 | @Size(max = 500) | 备注 |
| items | List\<Item\> | 是 | @NotEmpty、@Valid，元素 @NotNull | 领用明细 |

**Item 子对象**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| itemId | Long | 是 | @NotNull | 办公用品编号 |
| applyQuantity | Integer | 是 | @NotNull、@Min(1) | 领用数量 |

**响应**: CommonResult\<Long\>，返回新建申请编号。

**业务逻辑**:
1. 将明细转换为 DO，校验领用物品：itemId 不重复、物品均存在且为启用状态，否则抛 `SUPPLY_APPLY_ITEM_INVALID`。
2. 调用 AdminUserApi 校验申请人并获取其所属部门，作为申请部门 deptId。
3. 通过 OaNoRedisDAO 按前缀 `YP` 生成申请单号，若与已有单号重复抛 `SUPPLY_APPLY_NO_DUPLICATE`。
4. 保存申请草稿：状态置为 BPM「未开始」（NOT_START），创建人由公共审计字段填写。
5. 逐条保存领用明细：冗余物品名称/规格型号/计量单位/管理类型，已发放与已归还数量置 0，明细状态为「申请中」（APPLYING）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_008 | 用品已停用或重复 |
| 1_054_200_009 | 用品申请单号已存在 |

### 2.2 更新用品领用申请

- **路径**: PUT /oa/supply-apply/update
- **权限**: oa:supply-apply:update
- **说明**: 修改本人尚未提交（或被驳回/取消）的领用申请草稿，明细整体重建。

**请求参数 (OaSupplyApplySaveReqVO)**: 与「创建用品领用申请」相同（`id` 此时必传）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验申请存在（`SUPPLY_APPLY_NOT_EXISTS`）且归属当前登录用户（`SUPPLY_APPLY_ACCESS_DENIED`）。
2. 校验状态可编辑：仅「未开始/已驳回/已取消」允许，否则抛 `SUPPLY_APPLY_STATUS_INVALID`。
3. 校验新的领用明细物品有效且不重复。
4. 按 id 更新申请内容。
5. 删除原明细后按新明细重新保存（冗余字段与初始状态同创建逻辑）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_005 | 用品申请不存在 |
| 1_054_200_006 | 无权操作该用品申请 |
| 1_054_200_007 | 当前申请状态不允许该操作 |
| 1_054_200_008 | 用品已停用或重复 |

### 2.3 删除用品领用申请

- **路径**: DELETE /oa/supply-apply/delete?id={id}
- **权限**: oa:supply-apply:delete
- **说明**: 删除本人可编辑状态的申请及其明细。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验申请存在且归属当前登录用户。
2. 校验状态可编辑（未开始/已驳回/已取消）。
3. 先删除领用明细，再删除申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_005 | 用品申请不存在 |
| 1_054_200_006 | 无权操作该用品申请 |
| 1_054_200_007 | 当前申请状态不允许该操作 |

### 2.4 提交用品领用申请

- **路径**: PUT /oa/supply-apply/submit?id={id}
- **权限**: oa:supply-apply:create
- **说明**: 将本人可编辑状态的申请提交审批，发起 BPM `oa_supply_apply` 流程并绑定流程实例编号。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验申请存在、归属当前登录用户、状态可编辑（未开始/已驳回/已取消）。
2. 重新校验明细中领用物品仍然有效且启用（提交阶段不扣减库存）。
3. 通过 updateStatusAndClearProcessInstanceId 将状态由「未开始」乐观更新为「审批中」（RUNNING），更新数为 0 时抛 `SUPPLY_APPLY_STATUS_INVALID`。
4. 调用 BpmProcessInstanceApi 以流程定义 Key `oa_supply_apply`（BpmModelConstants.SUPPLY_APPLY）发起审批流程。
5. 将返回的流程实例编号回写到申请记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_005 | 用品申请不存在 |
| 1_054_200_006 | 无权操作该用品申请 |
| 1_054_200_007 | 当前申请状态不允许该操作 |
| 1_054_200_008 | 用品已停用或重复 |

### 2.5 取消用品领用申请

- **路径**: PUT /oa/supply-apply/cancel?id={id}
- **权限**: oa:supply-apply:update
- **说明**: 申请人取消审批中的申请，由 BPM 取消流程实例，审批结果经监听器回写。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）。

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验申请存在且归属当前登录用户。
2. 校验申请状态为「审批中」（RUNNING），否则抛 `SUPPLY_APPLY_STATUS_INVALID`。
3. 调用 BPM 以发起人身份取消流程实例（取消理由「申请人取消用品申请」），最终状态由流程监听器回调 updateSupplyApplyStatus 写回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_005 | 用品申请不存在 |
| 1_054_200_006 | 无权操作该用品申请 |
| 1_054_200_007 | 当前申请状态不允许该操作 |

### 2.6 获得用品领用申请

- **路径**: GET /oa/supply-apply/get?id={id}
- **权限**: oa:supply-apply:query
- **说明**: 查询申请详情，含领用明细列表与申请人/部门展示字段。

**请求参数**: 无（Query 参数 `id`：申请编号，必填）。

**响应**: CommonResult\<OaSupplyApplyRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| applyTime | LocalDateTime | 领用日期（时间戳毫秒） |
| useType | Integer | 使用类型（1 领用、2 借用） |
| pickupMethod | Integer | 领取方式 |
| reason | String | 申请事由 |
| fileUrls | List\<String\> | 附件地址列表 |
| remark | String | 备注 |
| no | String | 申请单号 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人昵称（拼接） |
| deptId | Long | 申请部门编号 |
| deptName | String | 申请部门名称（拼接） |
| status | Integer | 单据状态（BPM 流程实例状态，-1 未开始等） |
| processInstanceId | String | 流程实例编号 |
| createTime | LocalDateTime | 创建时间（时间戳毫秒） |
| items | List\<OaSupplyIssueRespVO\> | 领用明细列表（结构见 3.1 响应） |

**业务逻辑**:
1. 按 id 查询申请记录。
2. 查询该申请的全部领用明细并转换为 OaSupplyIssueRespVO 列表填入 items。
3. 批量查询申请人昵称与申请部门名称拼接展示字段。

### 2.7 获得本人的用品领用申请分页

- **路径**: GET /oa/supply-apply/page
- **权限**: oa:supply-apply:query
- **说明**: 分页查询当前登录用户本人创建的领用申请。

**请求参数 (OaSupplyApplyPageReqVO)**: 继承 PageParam（pageNo/pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| no | String | 否 | 无 | 申请单号 |
| status | Integer | 否 | 无 | 单据状态（BPM 流程实例状态） |
| deptId | Long | 否 | 无 | 申请部门编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<OaSupplyApplyRespVO\>\>，字段同「获得用品领用申请」（分页项不含 items 明细）。

**业务逻辑**:
1. 按申请人限定为当前登录用户，按单号/状态/部门/创建时间区间过滤分页查询。
2. 批量查询申请人昵称与部门名称，逐条拼接 creatorName、deptName。

## 3. 领用发放（OaSupplyIssueController）

### 3.1 获得领用发放分页

- **路径**: GET /oa/supply-issue/page
- **权限**: oa:supply-issue:query
- **说明**: 面向行政管理的领用明细分页，支持按申请人昵称筛选，拼接申请与发放展示字段。

**请求参数 (OaSupplyIssuePageReqVO)**: 继承 PageParam（pageNo/pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| itemName | String | 否 | 无 | 物品名称，模糊匹配 |
| creatorName | String | 否 | 无 | 申请人昵称 |
| manageType | Integer | 否 | 无 | 管理类型（1 消耗品、2 借用品、3 资产品） |
| useType | Integer | 否 | 无 | 使用类型（1 领用、2 借用） |
| status | Integer | 否 | 无 | 明细状态（-1 申请中、0 待发放、1 已领用、2 待归还、3 已归还） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 申请时间区间 |

**响应**: CommonResult\<PageResult\<OaSupplyIssueRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 明细编号 |
| applyId | Long | 申请编号 |
| itemId | Long | 用品编号 |
| itemName | String | 物品名称 |
| model | String | 规格型号 |
| unit | String | 计量单位 |
| manageType | Integer | 管理类型 |
| applyQuantity | Integer | 申请数量 |
| issuedQuantity | Integer | 实发数量 |
| returnedQuantity | Integer | 已归还数量 |
| status | Integer | 明细状态 |
| issueUserId | Long | 发放人编号 |
| issueUserName | String | 发放人昵称（拼接） |
| issueTime | LocalDateTime | 发放时间 |
| issueRemark | String | 发放备注 |
| returnRemark | String | 归还备注 |
| no | String | 申请单号（拼接） |
| creatorName | String | 申请人昵称（拼接） |
| deptName | String | 申请部门名称（拼接） |
| useType | Integer | 使用类型（拼接） |
| createTime | LocalDateTime | 申请时间（拼接） |

**业务逻辑**:
1. 若传入 creatorName，按昵称查询匹配的用户列表，无匹配时直接返回空分页。
2. 以匹配到的申请人编号集合为过滤条件，分页查询领用明细。
3. 批量查询关联申请、申请人/发放人用户、部门，拼接单号、使用类型、申请人、部门、发放人等展示字段。

### 3.2 发放用品

- **路径**: PUT /oa/supply-issue/issue
- **权限**: oa:supply-issue:issue
- **说明**: 对审批通过申请中的待发放明细执行发放，并扣减物品库存。

**请求参数 (OaSupplyIssueReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 明细编号 |
| issuedQuantity | Integer | 是 | @NotNull、@Min(1) | 实发数量 |
| issueRemark | String | 否 | @Size(max = 500) | 发放备注 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验发放明细存在（否则 `SUPPLY_ISSUE_NOT_EXISTS`）且状态为「待发放」（PENDING），否则抛 `SUPPLY_APPLY_STATUS_INVALID`。
2. 校验所属申请存在（否则 `SUPPLY_APPLY_NOT_EXISTS`）且审批状态为「通过」（APPROVE）。
3. 以乐观锁（比对原状态）更新明细：写入实发数量、发放备注、发放人与发放时间；借用品状态转「待归还」（RETURN_PENDING），其他用品转「已领用」（RECEIVED），更新失败抛 `SUPPLY_APPLY_STATUS_INVALID`。
4. 调用 updateSupplyItemStockQuantity 按实发数量负向扣减库存，库存不足抛 `SUPPLY_STOCK_INSUFFICIENT` 并随事务整体回滚。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_011 | 用品发放或归还记录不存在 |
| 1_054_200_005 | 用品申请不存在 |
| 1_054_200_007 | 当前申请状态不允许该操作 |
| 1_054_200_003 | 用品库存不足 |

### 3.3 确认归还用品

- **路径**: PUT /oa/supply-issue/return
- **权限**: oa:supply-issue:return
- **说明**: 对待归还的借用品明细执行归还，支持分次归还，累计归还完自动结束并补回库存。

**请求参数 (OaSupplyReturnReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 明细编号 |
| quantity | Integer | 是 | @NotNull、@Min(1) | 本次归还数量 |
| returnRemark | String | 否 | @Size(max = 500) | 归还备注 |

**响应**: CommonResult\<Boolean\>，固定返回 true。

**业务逻辑**:
1. 校验发放明细存在（否则 `SUPPLY_ISSUE_NOT_EXISTS`）且状态为「待归还」（RETURN_PENDING），否则抛 `SUPPLY_APPLY_STATUS_INVALID`。
2. 校验累计归还数量（已归还 + 本次）不超过实发数量，超出抛 `SUPPLY_APPLY_QTY_INVALID`。
3. 以乐观锁（比对原已归还数量）更新：累计归还数量与归还备注；全部归还完状态转「已归还」（RETURNED），否则保持「待归还」，更新失败抛 `SUPPLY_APPLY_STATUS_INVALID`。
4. 将本次归还数量正向补回物品库存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_200_011 | 用品发放或归还记录不存在 |
| 1_054_200_007 | 当前申请状态不允许该操作 |
| 1_054_200_010 | 操作数量超过申请或待归还数量 |
| 1_054_200_003 | 用品库存不足（库存原子增减共享校验） |
