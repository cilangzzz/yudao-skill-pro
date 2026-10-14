# 商机管理接口 (CrmBusinessController)

> CRM 商机域接口：商机的创建/更新/状态流转/转移/分页查询/导出，以及商机状态组（阶段）的维护。商机关联客户、联系人、产品与状态组，并基于 CRM 数据权限（@CrmPermission）控制读写。

## 接口路径前缀

- `/crm/business` (Controller: CrmBusinessController)
- `/crm/business-status` (Controller: CrmBusinessStatusController)

---

## 1. 商机管理（CrmBusinessController）

### 1.1 创建商机

- **路径**: POST /crm/business/create
- **权限**: crm:business:create
- **说明**: 创建商机，支持关联产品列表与联系人，创建后默认写入状态组的第一个状态，并为负责人初始化数据权限。

**请求参数 (CrmBusinessSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 主键（创建时忽略） |
| name | String | 是 | @NotNull | 商机名称 |
| customerId | Long | 是 | @NotNull | 客户编号 |
| contactNextTime | LocalDateTime | 否 | 无 | 下次联系时间 |
| ownerUserId | Long | 是 | @NotNull | 负责人用户编号 |
| statusTypeId | Long | 是 | @NotNull | 商机状态组编号 |
| dealTime | LocalDateTime | 否 | 无 | 预计成交日期 |
| discountPercent | BigDecimal | 是 | @NotNull | 整单折扣（百分比） |
| remark | String | 否 | 无 | 备注 |
| contactId | Long | 否 | 无 | 联系人编号（在联系人详情页新建商机时关联两者） |
| products | List&lt;BusinessProduct&gt; | 否 | 无 | 产品列表 |
| products[].productId | Long | 是 | @NotNull | 产品编号 |
| products[].productPrice | BigDecimal | 是 | @NotNull | 产品单价 |
| products[].businessPrice | BigDecimal | 是 | @NotNull | 商机价格 |
| products[].count | Integer | 是 | @NotNull | 产品数量 |

**响应**: CommonResult&lt;Long&gt;（商机编号）

**业务逻辑**: 1. 校验产品项有效性（产品必须存在），并将每项的商机价格乘以数量计算单项总价 totalPrice。 2. 校验关联字段：状态组存在、客户存在、联系人存在且必须属于同一客户（否则报错）、负责人用户存在。 3. 插入商机：statusId 默认取状态组下第一个状态，按产品项汇总 totalProductPrice，再按整单折扣计算 totalPrice。 4. 批量插入商机关联商品（CrmBusinessProductDO）。 5. 为负责人创建 OWNER 级别的 CRM 数据权限。 6. 若传了 contactId，建立联系人与商机的关联记录。 7. 记录操作日志上下文（@LogRecord）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_004 | 商机关联的联系人不属于该客户 |
| 1_020_006_000 | 客户不存在 |
| 1_020_003_000 | 联系人不存在 |
| 1_020_008_000 | 产品不存在 |
| 1_020_010_000 | 商机状态组不存在 |

### 1.2 更新商机

- **路径**: PUT /crm/business/update
- **权限**: crm:business:update
- **说明**: 更新商机基本信息与产品列表，不允许更新负责人与状态组；需具备商机 WRITE 级数据权限。

**请求参数 (CrmBusinessSaveReqVO)**: 同 1.1（id 必传用于定位商机）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 强制将 ownerUserId、statusTypeId 置空（不允许通过更新接口修改）。 2. 校验商机存在（需 WRITE 数据权限）。 3. 校验产品项有效性与关联字段（客户/联系人/状态组等）。 4. 更新商机主记录，并重新计算产品总金额与商机总金额。 5. 对商机关联商品做 diff 更新（新增/更新/删除）。 6. 记录操作日志（含新旧数据 diff）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |
| 1_020_002_004 | 商机关联的联系人不属于该客户 |
| 1_020_006_000 | 客户不存在 |
| 1_020_003_000 | 联系人不存在 |
| 1_020_008_000 | 产品不存在 |

### 1.3 更新商机状态

- **路径**: PUT /crm/business/update-status
- **权限**: crm:business:update
- **说明**: 推进商机的阶段状态（statusId）或设置结束状态（endStatus，赢单/输单/无效）。

**请求参数 (CrmBusinessUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 商机编号 |
| statusId | Long | 否 | @AssertTrue(isStatusValid)：statusId 与 endStatus 不能同时为空 | 目标状态编号 |
| endStatus | Integer | 否 | @InEnum(CrmBusinessEndStatusEnum.class) | 结束状态 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验商机存在（需 WRITE 数据权限）。 2. 校验商机未结束（endStatus 已有值则报错）。 3. 若传 statusId，校验该状态属于商机当前的状态组。 4. 校验状态确有变更（与当前状态/结束状态相同则报错）。 5. 更新商机的 statusId / endStatus。 6. 记录操作日志（旧状态名、新状态名）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |
| 1_020_002_002 | 更新商机状态失败，原因：已经是结束状态 |
| 1_020_002_003 | 更新商机状态失败，原因：已经是该状态 |
| 1_020_010_003 | 商机状态不存在 |

### 1.4 删除商机

- **路径**: DELETE /crm/business/delete
- **权限**: crm:business:delete
- **说明**: 删除商机，要求 OWNER 级数据权限；已关联合同的商机不可删除。

**请求参数**: 无（Query 参数：id - 商机编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验商机存在（需 OWNER 数据权限）。 2. 校验商机是否关联合同，有合同则禁止删除。 3. 删除商机记录。 4. 删除该商机的 CRM 数据权限。 5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |
| 1_020_002_001 | 商机已关联合同，不能删除 |

### 1.5 获得商机详情

- **路径**: GET /crm/business/get
- **权限**: crm:business:query
- **说明**: 按编号获得商机详情（含关联产品项）。

**请求参数**: 无（Query 参数：id - 商机编号，必填）

**响应**: CommonResult&lt;CrmBusinessRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 商机名称 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| followUpStatus | Boolean | 跟进状态 |
| contactLastTime | LocalDateTime | 最后跟进时间 |
| contactNextTime | LocalDateTime | 下次联系时间 |
| ownerUserId | Long | 负责人的用户编号 |
| ownerUserName | String | 负责人名字 |
| ownerUserDeptName | String | 负责人部门 |
| statusTypeId | Long | 商机状态组编号 |
| statusTypeName | String | 商机状态组名字 |
| statusId | Long | 商机状态编号 |
| statusName | String | 状态名称 |
| endStatus | Integer | 结束状态 |
| endRemark | String | 结束时的备注 |
| dealTime | LocalDateTime | 预计成交日期 |
| totalProductPrice | BigDecimal | 产品总金额 |
| discountPercent | BigDecimal | 整单折扣 |
| totalPrice | BigDecimal | 商机总金额 |
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
| products[].businessPrice | BigDecimal | 商机价格 |
| products[].count | BigDecimal | 产品数量 |
| products[].totalPrice | BigDecimal | 总计价格 |

**业务逻辑**: 1. 按 id 查询商机（需 READ 数据权限）。 2. 拼接客户名称、创建人/负责人昵称与负责人部门名称。 3. 拼接商机状态组名称与状态名称（结合 endStatus 计算）。 4. 查询商机关联产品项，并拼接产品名称、条码、单位。

### 1.6 获得商机的精简列表

- **路径**: GET /crm/business/simple-all-list
- **权限**: crm:business:query
- **说明**: 不分页获得当前用户可见的全部商机，仅返回 id、name、customerId，用于下拉选择。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;CrmBusinessRespVO&gt;&gt;（仅 id/name/customerId 有值）

**业务逻辑**: 1. 构造 pageSize=PAGE_SIZE_NONE 的分页请求。 2. 按当前登录用户的数据权限查询商机全量列表。 3. 转换为仅含 id/name/customerId 的精简 VO。

### 1.7 获得商机列表（基于指定客户）

- **路径**: GET /crm/business/list-by-customer
- **权限**: crm:business:query
- **说明**: 获得指定客户下的商机精简列表（仅 id、name、customerId），需具备该客户 READ 数据权限。

**请求参数**: 无（Query 参数：customerId - 客户编号，必填）

**响应**: CommonResult&lt;List&lt;CrmBusinessRespVO&gt;&gt;（仅 id/name/customerId 有值）

**业务逻辑**: 1. 校验当前用户对该客户具备 READ 数据权限。 2. 按客户编号查询商机列表。 3. 转换为精简 VO。

### 1.8 获得商机列表（基于指定联系人）

- **路径**: GET /crm/business/list-by-contact
- **权限**: crm:business:query
- **说明**: 获得与指定联系人关联的商机列表（详情级字段），需具备该联系人 READ 数据权限。

**请求参数**: 无（Query 参数：contactId - 联系人编号，必填）

**响应**: CommonResult&lt;List&lt;CrmBusinessRespVO&gt;&gt;（同 1.5 字段，无 products）

**业务逻辑**: 1. 校验当前用户对该联系人具备 READ 数据权限。 2. 查询联系人-商机关联表得到商机编号集合，无关联则返回空。 3. 按编号查询商机列表。 4. 拼接客户名称、创建人/负责人、状态组与状态名称。

### 1.9 获得商机分页

- **路径**: GET /crm/business/page
- **权限**: crm:business:query
- **说明**: 分页获得当前用户可见（结合场景类型）的商机列表。

**请求参数 (CrmBusinessPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | 无 | 页码（PageParam） |
| pageSize | Integer | 否 | 无 | 每页条数（PageParam） |
| name | String | 否 | 无 | 商机名称（模糊） |
| customerId | Long | 否 | 无 | 客户编号 |
| contactId | Long | 否 | 无 | 联系人编号 |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum.class) | 场景类型（我负责的/我参与的/下属的等，null 表示全部） |

**响应**: CommonResult&lt;PageResult&lt;CrmBusinessRespVO&gt;&gt;（列表字段同 1.5，无 products）

**业务逻辑**: 1. 按查询条件与当前登录用户进行数据权限过滤分页查询。 2. 批量拼接客户名称、创建人/负责人昵称与部门名称。 3. 拼接商机状态组名称与状态名称。

### 1.10 获得商机分页（基于指定客户）

- **路径**: GET /crm/business/page-by-customer
- **权限**: 仅登录（无 @PreAuthorize，Service 层校验客户 READ 数据权限）
- **说明**: 在客户详情页分页展示该客户下的商机，customerId 必填。

**请求参数 (CrmBusinessPageReqVO)**: 同 1.9（其中 customerId 必填，为空时直接报“客户不存在”）

**响应**: CommonResult&lt;PageResult&lt;CrmBusinessRespVO&gt;&gt;（列表字段同 1.5，无 products）

**业务逻辑**: 1. customerId 为空时抛出客户不存在异常。 2. 校验当前用户对该客户具备 READ 数据权限。 3. 按客户编号分页查询商机。 4. 拼接客户/负责人/状态等展示字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_006_000 | 客户不存在 |

### 1.11 获得联系人的商机分页

- **路径**: GET /crm/business/page-by-contact
- **权限**: crm:business:query
- **说明**: 在联系人详情页分页展示与该联系人关联的商机，需具备该联系人 READ 数据权限。

**请求参数 (CrmBusinessPageReqVO)**: 同 1.9（其中 contactId 用于定位联系人）

**响应**: CommonResult&lt;PageResult&lt;CrmBusinessRespVO&gt;&gt;（列表字段同 1.5，无 products）

**业务逻辑**: 1. 校验当前用户对该联系人具备 READ 数据权限。 2. 查询联系人-商机关联表得到商机编号集合，无关联则返回空分页。 3. 按商机编号集合分页查询。 4. 拼接客户/负责人/状态等展示字段。

### 1.12 导出商机 Excel

- **路径**: GET /crm/business/export-excel
- **权限**: crm:business:export
- **说明**: 按分页条件全量导出商机 Excel（文件名“商机.xls”），记录导出操作日志。

**请求参数 (CrmBusinessPageReqVO)**: 同 1.9

**响应**: 无（直接以文件流写出 Excel，列定义取自 CrmBusinessRespVO 的 @ExcelProperty）

**业务逻辑**: 1. 将 pageSize 置为 PAGE_SIZE_NONE（不分页）。 2. 按当前用户数据权限查询全部符合条件的商机。 3. 拼接展示字段后通过 ExcelUtils 写出响应流。

### 1.13 商机转移

- **路径**: PUT /crm/business/transfer
- **权限**: crm:business:update
- **说明**: 将商机负责人转移给新负责人，原负责人可按权限级别留在团队或被移除，需 OWNER 级数据权限。

**请求参数 (CrmBusinessTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 商机编号 |
| newOwnerUserId | Long | 是 | @NotNull | 新负责人的用户编号 |
| oldOwnerPermissionLevel | Integer | 否 | 无 | 老负责人加入团队后的权限级别（CrmPermissionLevelEnum，null 表示移除） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验商机存在（需 OWNER 数据权限）。 2. 执行数据权限转移（新负责人成为 OWNER，老负责人按 oldOwnerPermissionLevel 调整）。 3. 更新商机的负责人字段。 4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |
| 1_020_007_001 | 操作失败，原因：没有权限 |
| 1_020_007_003 | 操作失败，原因：转移对象已经是该负责人 |

---

## 2. 商机状态管理（CrmBusinessStatusController）

### 2.1 创建商机状态组

- **路径**: POST /crm/business-status/create
- **权限**: crm:business-status:create
- **说明**: 创建商机状态组及其内部阶段状态列表。

**请求参数 (CrmBusinessStatusSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | 无 | 主键（创建时忽略） |
| name | String | 是 | @NotEmpty | 状态组名称 |
| deptIds | List&lt;Long&gt; | 否 | 无 | 使用的部门编号 |
| statuses | List&lt;Status&gt; | 是 | @NotEmpty + @Valid | 商机状态集合 |
| statuses[].id | Long | 否 | 无 | 状态编号 |
| statuses[].name | String | 是 | @NotEmpty | 状态名 |
| statuses[].percent | BigDecimal | 是 | @NotNull | 赢单率 |
| statuses[].sort | Integer | 否 | 无 | 排序（服务端按顺序自动生成） |

**响应**: CommonResult&lt;Long&gt;（状态组编号）

**业务逻辑**: 1. 校验状态组名称唯一。 2. 按列表顺序为各状态设置 sort（0,1,2...）。 3. 插入状态组（CrmBusinessStatusTypeDO）。 4. 批量插入状态（CrmBusinessStatusDO，关联 typeId）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_010_001 | 商机状态组的名称已存在 |

### 2.2 更新商机状态组

- **路径**: PUT /crm/business-status/update
- **权限**: crm:business-status:update
- **说明**: 更新商机状态组；已被商机使用的状态组不允许更新。

**请求参数 (CrmBusinessStatusSaveReqVO)**: 同 2.1（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验状态组存在。 2. 校验状态组名称唯一。 3. 按列表顺序重设状态 sort。 4. 校验该状态组未被任何商机使用，已使用则报错。 5. 更新状态组。 6. 对组内状态做 diff 更新（新增/更新/删除）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_010_000 | 商机状态组不存在 |
| 1_020_010_001 | 商机状态组的名称已存在 |
| 1_020_010_002 | 已经被使用的商机状态组，无法进行更新 |

### 2.3 删除商机状态组

- **路径**: DELETE /crm/business-status/delete
- **权限**: crm:business-status:delete
- **说明**: 删除商机状态组及其下所有状态；已被商机使用的状态组不允许删除。

**请求参数**: 无（Query 参数：id - 状态组编号，必填）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验状态组存在。 2. 校验该状态组未被任何商机使用，已使用则报错。 3. 删除状态组。 4. 按 typeId 删除组下全部状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_010_000 | 商机状态组不存在 |
| 1_020_010_002 | 已经被使用的商机状态组，无法进行删除（源码中与“更新失败”共用同一错误码） |

### 2.4 获得商机状态组详情

- **路径**: GET /crm/business-status/get
- **权限**: crm:business-status:query
- **说明**: 获得状态组详情，含组内全部状态（按 sort 升序）。

**请求参数**: 无（Query 参数：id - 状态组编号，必填）

**响应**: CommonResult&lt;CrmBusinessStatusRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 状态组编号 |
| name | String | 状态组名字 |
| deptIds | List&lt;Long&gt; | 使用的部门编号 |
| deptNames | List&lt;String&gt; | 使用的部门名称（仅分页接口填充） |
| creator | String | 创建人（分页接口填充为昵称） |
| createTime | LocalDateTime | 创建时间 |
| statuses | List&lt;Status&gt; | 状态集合 |
| statuses[].id | Long | 状态编号 |
| statuses[].name | String | 状态名 |
| statuses[].percent | BigDecimal | 赢单率 |
| statuses[].sort | Integer | 排序 |

**业务逻辑**: 1. 按 id 查询状态组，不存在返回 null。 2. 查询该组下全部状态。 3. 组装状态组 VO 与 statuses 列表。

### 2.5 获得商机状态组分页

- **路径**: GET /crm/business-status/page
- **权限**: crm:business-status:query
- **说明**: 分页获得商机状态组列表，拼接创建人昵称与部门名称。

**请求参数 (PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | 无 | 页码 |
| pageSize | Integer | 否 | 无 | 每页条数 |

**响应**: CommonResult&lt;PageResult&lt;CrmBusinessStatusRespVO&gt;&gt;（字段同 2.4，creator 为创建人昵称、deptNames 为部门名称列表）

**业务逻辑**: 1. 分页查询状态组。 2. 批量查询创建人昵称。 3. 批量查询 deptIds 对应的部门名称。 4. 拼接后返回分页结果。

### 2.6 获得商机状态组精简列表

- **路径**: GET /crm/business-status/type-simple-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 获得全部商机状态组精简列表，按当前登录用户所属部门过滤（deptIds 非空且不含用户部门的状态组被剔除），用于下拉选择。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;CrmBusinessStatusRespVO&gt;&gt;（不含 statuses）

**业务逻辑**: 1. 查询全部状态组列表。 2. 获取当前登录用户所属部门。 3. 剔除 deptIds 非空且不包含用户部门的状态组。 4. 转换为精简 VO 返回。

### 2.7 获得商机状态精简列表

- **路径**: GET /crm/business-status/status-simple-list
- **权限**: 仅登录（无 @PreAuthorize）
- **说明**: 获得指定状态组下的状态列表（按 sort 升序），用于下拉选择。

**请求参数**: 无（Query 参数：typeId - 商机状态组编号，必填）

**响应**: CommonResult&lt;List&lt;CrmBusinessStatusRespVO.Status&gt;&gt;（字段：id/name/percent/sort）

**业务逻辑**: 1. 按状态组编号查询状态列表。 2. 按 sort 升序排序。 3. 转换为精简 Status VO 返回。
