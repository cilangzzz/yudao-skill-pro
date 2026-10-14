# 联系人管理接口 (CrmContactController)

> CRM 联系人管理：联系人的增删改查、分页导出、负责人转移，以及联系人与商机之间的关联/取关。查询均基于 CRM 数据权限（`@CrmPermission`）过滤可见范围。

## 接口路径前缀

- `/crm/contact`  (Controller: `CrmContactController`)
- Service: `CrmContactServiceImpl`（联系人本体）、`CrmContactBusinessServiceImpl`（联系人与商机关联）

---

## 1. 联系人 CRUD 与查询

### 1.1 创建联系人

- **路径**: POST /crm/contact/create
- **权限**: crm:contact:create
- **说明**: 创建一条联系人记录，同时创建 OWNER 级数据权限；若携带 `businessId` 则自动关联商机。

**请求参数 (CrmContactSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | | 主键，创建时传 null |
| name | String | 是 | @NotNull | 姓名 |
| customerId | Long | 是 | @NotNull | 客户编号 |
| contactNextTime | LocalDateTime | 否 | | 下次联系时间（yyyy-MM-dd 格式） |
| ownerUserId | Long | 是 | @NotNull | 负责人用户编号 |
| mobile | String | 否 | @Mobile | 手机号 |
| telephone | String | 否 | @Telephone | 电话 |
| qq | Long | 否 | | QQ |
| wechat | String | 否 | | 微信 |
| email | String | 否 | @Email | 电子邮箱 |
| areaId | Integer | 否 | | 地区编号 |
| detailAddress | String | 否 | | 地址 |
| sex | Integer | 否 | | 性别（字典 USER_SEX） |
| master | Boolean | 否 | | 是否关键决策人 |
| post | String | 否 | | 职位 |
| parentId | Long | 否 | | 直属上级联系人编号 |
| remark | String | 否 | | 备注 |
| businessId | Long | 否 | | 关联商机 ID，用于在【商机】详情页「新建联系人」时自动关联 |

**响应**: CommonResult&lt;Long&gt;，返回新建联系人编号。

**业务逻辑**:
1. 强制置空 `id`，校验关联数据：客户存在（`validateCustomer`）、负责人用户存在、直属上级联系人存在、关联商机存在。
2. VO 转换为 `CrmContactDO` 并插入联系人表。
3. 调用 `CrmPermissionService.createPermission` 为当前登录用户创建该联系人的 OWNER 级数据权限。
4. 若请求携带 `businessId`，调用 `CrmContactBusinessService.createContactBusinessList` 建立联系人与商机的关联。
5. 通过 `@LogRecord` 记录操作日志上下文，返回联系人编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_006_000 | 客户不存在 |
| 1_020_003_000 | 联系人不存在（直属上级不存在） |
| 1_020_002_000 | 商机不存在 |

### 1.2 更新联系人

- **路径**: PUT /crm/contact/update
- **权限**: crm:contact:update（Service 层 `@CrmPermission` 要求对联系人有 WRITE 权限）
- **说明**: 更新联系人基础信息，请求体与创建相同（`CrmContactSaveReqVO`，见 1.1，此时 `id` 必填）。

**请求参数 (CrmContactSaveReqVO)**: 同 1.1，`id` 为必填主键。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验联系人存在（不存在抛 CONTACT_NOT_EXISTS），并保留旧数据用于日志比对。
2. 校验关联数据：客户、负责人、直属上级、关联商机均存在（同创建）。
3. VO 转换为 `CrmContactDO` 后按 id 更新。
4. 将旧负责人回填到请求 VO，避免操作日志误报"删除负责人"，随后记录变更差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_003_000 | 联系人不存在 |
| 1_020_006_000 | 客户不存在 |
| 1_020_002_000 | 商机不存在 |

### 1.3 删除联系人

- **路径**: DELETE /crm/contact/delete
- **权限**: crm:contact:delete（Service 层 `@CrmPermission` 要求 OWNER 权限）
- **说明**: 删除指定联系人，并级联清理商机关联与数据权限。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 联系人编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验联系人存在。
2. 检查该联系人是否被合同引用（`getContractCountByContactId`），引用数大于 0 则抛异常拒绝删除。
3. 删除联系人记录。
4. 删除该联系人的所有商机关联记录。
5. 删除该联系人的数据权限记录，并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_003_000 | 联系人不存在 |
| 1_020_003_002 | 联系人已关联合同，不能删除 |

### 1.4 获得联系人详情

- **路径**: GET /crm/contact/get
- **权限**: crm:contact:query（Service 层 `@CrmPermission` 要求 READ 权限）
- **说明**: 获取单个联系人详情，附带客户名、负责人名/部门、直属上级名等关联信息。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 联系人编号 |

**响应**: CommonResult&lt;CrmContactRespVO&gt;（字段见 1.7，联系人不存在时返回 null）。

**业务逻辑**:
1. 按 id 查询 `CrmContactDO`（`@CrmPermission` 校验 READ 数据权限）。
2. 复用 `buildContactDetailList` 组装关联信息（见 1.7 业务逻辑），返回单条 VO。

### 1.5 获得联系人的精简列表

- **路径**: GET /crm/contact/simple-all-list
- **权限**: crm:contact:query
- **说明**: 获取当前用户可见联系人的精简列表（下拉选择用），只返回 id、name、customerId。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;CrmContactRespVO&gt;&gt;，仅填充 id、name、customerId 三个字段。

**业务逻辑**:
1. 以 `PAGE_SIZE_NONE`（不分页）构建查询条件，调用 `contactMapper.selectPage(reqVO, userId)`，通过 `CrmPermissionUtils.appendPermissionCondition` 拼接数据权限过滤，返回当前用户可见的全部联系人。

### 1.6 获得联系人列表（基于指定客户）

- **路径**: GET /crm/contact/list-by-customer
- **权限**: crm:contact:query（Service 层 `@CrmPermission` 要求对该客户有 READ 权限）
- **说明**: 获取指定客户下全部联系人的精简列表，只返回 id、name、customerId。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| customerId | Long | 是 | @RequestParam | 客户编号 |

**响应**: CommonResult&lt;List&lt;CrmContactRespVO&gt;&gt;，仅填充 id、name、customerId 三个字段。

**业务逻辑**:
1. `@CrmPermission` 校验当前用户对该客户的 READ 权限。
2. 按 `customerId` 查询该客户下全部联系人并转换为精简 VO 列表。

### 1.7 获得联系人分页

- **路径**: GET /crm/contact/page
- **权限**: crm:contact:query
- **说明**: 按数据权限与查询条件分页获取联系人，返回完整关联信息。

**请求参数 (CrmContactPageReqVO)**（继承 PageParam 的 pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | | 页码，PageParam 默认值 |
| pageSize | Integer | 否 | | 每页条数，PageParam 默认值 |
| name | String | 否 | | 姓名，模糊匹配 |
| customerId | Long | 否 | | 客户编号 |
| mobile | String | 否 | | 手机号，精确匹配 |
| telephone | String | 否 | | 电话，精确匹配 |
| email | String | 否 | | 电子邮箱，精确匹配 |
| qq | Long | 否 | | QQ，精确匹配 |
| wechat | String | 否 | | 微信，精确匹配 |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum.class) | 场景类型（1 我负责的 / 2 我参与的等），null 表示全部 |
| businessId | Long | 否 | | 商机编号 |

**响应**: CommonResult&lt;PageResult&lt;CrmContactRespVO&gt;&gt;

CrmContactRespVO 字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 主键 |
| name | String | 联系人姓名 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| contactLastTime | LocalDateTime | 最后跟进时间 |
| contactLastContent | String | 最后跟进内容 |
| contactNextTime | LocalDateTime | 下次联系时间 |
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人名字 |
| ownerUserDeptName | String | 负责人部门 |
| mobile | String | 手机号 |
| telephone | String | 电话 |
| email | String | 电子邮箱 |
| qq | Long | QQ |
| wechat | String | 微信 |
| areaId | Integer | 地区编号 |
| areaName | String | 地区名（AreaUtils 格式化） |
| detailAddress | String | 地址 |
| sex | Integer | 性别（字典 USER_SEX） |
| master | Boolean | 是否关键决策人 |
| post | String | 职位 |
| parentId | Long | 直属上级编号 |
| parentName | String | 直属上级名 |
| remark | String | 备注 |
| creator | String | 创建人编号 |
| creatorName | String | 创建人名字 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. `selectPage` 先通过 `CrmPermissionUtils.appendPermissionCondition` 拼接数据权限条件（联系人 id 关联权限表 + 场景类型过滤）。
2. 拼接自身查询条件（name 模糊、mobile/telephone/email/qq/wechat 精确），按 id 倒序分页查询。
3. 批量查询关联数据：客户 Map、创建人/负责人用户 Map 及其部门 Map、直属上级联系人 Map。
4. 转换为 `CrmContactRespVO`：格式化地区名（`AreaUtils.format`）、填充客户名、创建人名、负责人名与部门名、直属上级名。

### 1.8 获得联系人分页（基于指定客户）

- **路径**: GET /crm/contact/page-by-customer
- **权限**: 已认证（仅登录；Service 层 `@CrmPermission` 要求对该客户有 READ 权限）
- **说明**: 在指定客户的联系人范围内分页查询，请求与响应结构同 1.7。

**请求参数 (CrmContactPageReqVO)**: 同 1.7，其中 `customerId` 必填（Controller 用 `Assert.notNull` 校验，缺失时抛异常提示"客户编号不能为空"）。

**响应**: CommonResult&lt;PageResult&lt;CrmContactRespVO&gt;&gt;，字段见 1.7。

**业务逻辑**:
1. 校验 `customerId` 不为空。
2. `@CrmPermission` 校验当前用户对该客户的 READ 权限。
3. 按 customerId + name/mobile/telephone/email/qq/wechat 条件分页查询（不受数据权限表过滤），组装关联信息后返回（同 1.7 第 3-4 步）。

### 1.9 获得联系人分页（基于指定商机）

- **路径**: GET /crm/contact/page-by-business
- **权限**: 已认证（仅登录；Service 层 `@CrmPermission` 要求对该商机有 READ 权限）
- **说明**: 查询与指定商机关联的联系人分页，请求与响应结构同 1.7。

**请求参数 (CrmContactPageReqVO)**: 同 1.7，其中 `businessId` 必填（Controller 用 `Assert.notNull` 校验，缺失时抛异常提示"商机编号不能为空"）。

**响应**: CommonResult&lt;PageResult&lt;CrmContactRespVO&gt;&gt;，字段见 1.7。

**业务逻辑**:
1. 校验 `businessId` 不为空。
2. `@CrmPermission` 校验当前用户对该商机的 READ 权限。
3. 查询商机-联系人关联表（`getContactBusinessListByBusinessId`），无关联记录时直接返回空分页。
4. 以关联的联系人 id 集合 `in` 查询 + name/mobile 等条件过滤，分页返回并组装关联信息（同 1.7 第 3-4 步）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |

### 1.10 导出联系人 Excel

- **路径**: GET /crm/contact/export-excel
- **权限**: crm:contact:export（`@ApiAccessLog(operateType = EXPORT)` 记录导出日志）
- **说明**: 按分页查询条件导出联系人 Excel 文件（联系人.xls）。

**请求参数 (CrmContactPageReqVO)**: 同 1.7（pageNo/pageSize 由后端强制覆盖，导出全部数据）。

**响应**: 无 JSON 响应，直接以流写出 Excel 文件（"联系人.xls"，sheet 名"数据"，按 `CrmContactRespVO` 的 `@ExcelProperty` 注解列输出）。

**业务逻辑**:
1. 将 `pageNo` 置为 `PAGE_SIZE_NONE`，查询当前用户数据权限下符合条件的全部联系人。
2. 复用 `buildContactDetailList` 组装关联信息（客户名、负责人、直属上级等）。
3. `ExcelUtils.write` 将 VO 列表写出到 HttpServletResponse。

---

## 2. 联系人转移

### 2.1 联系人转移

- **路径**: PUT /crm/contact/transfer
- **权限**: crm:contact:update（Service 层 `@CrmPermission` 要求 OWNER 权限）
- **说明**: 将联系人负责人转移给新用户，可为老负责人保留团队权限级别。

**请求参数 (CrmContactTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 联系人编号 |
| newOwnerUserId | Long | 是 | @NotNull | 新负责人的用户编号 |
| oldOwnerPermissionLevel | Integer | 否 | | 老负责人加入团队后的权限级别，关联 CrmPermissionLevelEnum；为 null 表示移除 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验联系人存在。
2. 调用 `CrmPermissionService.transferPermission` 转移数据权限（新负责人设为 OWNER，按参数为老负责人保留或移除团队权限）。
3. 更新联系人的 `ownerUserId` 为新负责人。
4. 记录转移操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_003_000 | 联系人不存在 |

---

## 3. 联系人与商机关联

### 3.1 创建联系人与商机的关联（联系人维度）

- **路径**: POST /crm/contact/create-business-list
- **权限**: crm:contact:create-business（Service 层 `@CrmPermission` 要求对该联系人有 WRITE 权限）
- **说明**: 指定一个联系人，批量关联多个商机。

**请求参数 (CrmContactBusinessReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| contactId | Long | 是 | @NotNull | 联系人编号 |
| businessIds | List&lt;Long&gt; | 是 | @NotEmpty | 商机编号数组 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验联系人存在（不存在抛 CONTACT_NOT_EXISTS）。
2. 遍历 `businessIds`，逐个校验商机存在。
3. 对每个 (contactId, businessId) 组合做关联判重，已存在的跳过。
4. 将未关联的组合批量插入 `CrmContactBusinessDO` 关联表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_003_000 | 联系人不存在 |
| 1_020_002_000 | 商机不存在 |

### 3.2 创建联系人与商机的关联（商机维度）

- **路径**: POST /crm/contact/create-business-list2
- **权限**: crm:contact:create-business（Service 层 `@CrmPermission` 要求对该商机有 WRITE 权限）
- **说明**: 指定一个商机，批量关联多个联系人（【商机】详情页操作）。

**请求参数 (CrmContactBusiness2ReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| businessId | Long | 是 | @NotNull | 商机编号 |
| contactIds | List&lt;Long&gt; | 是 | @NotEmpty | 联系人编号数组 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验商机存在（不存在抛 BUSINESS_NOT_EXISTS）。
2. 遍历 `contactIds`，逐个校验联系人存在。
3. 对每个 (contactId, businessId) 组合做关联判重，已存在的跳过。
4. 将未关联的组合批量插入关联表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |
| 1_020_003_000 | 联系人不存在 |

### 3.3 删除联系人与商机的关联（联系人维度）

- **路径**: DELETE /crm/contact/delete-business-list
- **权限**: crm:contact:delete-business（Service 层 `@CrmPermission` 要求对该联系人有 WRITE 权限）
- **说明**: 指定一个联系人，批量取消与多个商机的关联。

**请求参数 (CrmContactBusinessReqVO)**: 同 3.1（contactId + businessIds）。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验联系人存在。
2. 按 contactId + businessIds 直接删除关联表中的对应记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_003_000 | 联系人不存在 |

### 3.4 删除联系人与商机的关联（商机维度）

- **路径**: DELETE /crm/contact/delete-business-list2
- **权限**: crm:contact:delete-business（Service 层 `@CrmPermission` 要求对该商机有 WRITE 权限）
- **说明**: 指定一个商机，批量取消与多个联系人的关联。

**请求参数 (CrmContactBusiness2ReqVO)**: 同 3.2（businessId + contactIds）。

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验商机存在。
2. 按 businessId + contactIds 直接删除关联表中的对应记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_002_000 | 商机不存在 |

---

## 附：联系人域错误码汇总（1_020_003_XXX）

| 错误码 | 说明 |
|-------|------|
| 1_020_003_000 | 联系人不存在 |
| 1_020_003_002 | 联系人已关联合同，不能删除 |
| 1_020_003_003 | 更新联系人负责人失败 |

> 关联域错误码：创建/更新时校验客户（1_020_006_000 客户不存在）、商机（1_020_002_000 商机不存在）。
