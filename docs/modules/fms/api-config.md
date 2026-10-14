# 基础配置接口 (FmsAccountSetController 等 13 个控制器)

> FMS 财务模块的基础配置域：账套的创建/初始化/成员授权，以及账套内会计科目、辅助核算、币别、凭证字、凭证模板、常用摘要、首页财务指标、财务参数和初始余额的维护，是凭证、账簿、结账、报表等业务的数据基础。

## 接口路径前缀

| 路径前缀 | Controller |
|---------|-----------|
| /fms/config/account-set | FmsAccountSetController |
| /fms/config/account-user | FmsAccountUserController |
| /fms/config/subject | FmsSubjectController |
| /fms/config/auxiliary-type | FmsAuxiliaryTypeController |
| /fms/config/auxiliary-item | FmsAuxiliaryItemController |
| /fms/config/currency | FmsCurrencyController |
| /fms/config/voucher-word | FmsVoucherWordController |
| /fms/config/voucher-template | FmsVoucherTemplateController |
| /fms/config/voucher-template-category | FmsVoucherTemplateCategoryController |
| /fms/config/digest | FmsDigestController |
| /fms/config/finance-indicator | FmsFinanceIndicatorController |
| /fms/config/finance-parameter | FmsFinanceParameterController |
| /fms/config/initial-balance | FmsInitialBalanceController |

> 说明：本域所有 Service 方法内部都会先做账套级权限校验（读操作校验成员可读级别，写操作校验成员可写级别，部分操作要求账套主管），对应错误码 `ACCOUNT_SET_ACCESS_DENIED` / `ACCOUNT_SET_NOT_EXISTS`，下文各端点不再重复展开。

## 1. 账套管理 (/fms/config/account-set)

### 1.1 创建账套

- **路径**: POST /fms/config/account-set/create
- **权限**: fms:config:account-set:create
- **说明**: 创建未初始化的账套，并将当前用户作为账套创建人（OWNER 级）加入账套。

**请求参数 (FmsAccountSetSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 账套编号（新增时置空） |
| companyCode | String | 是 | @NotBlank、@Size(max=64) | 公司编码 |
| companyName | String | 是 | @NotBlank、@Size(max=255) | 公司名称 |
| companyProfile | String | 否 | @Size(max=500) | 公司简介 |
| industry | String | 否 | @Size(max=255) | 所在行业 |
| location | String | 否 | @Size(max=255) | 所在地 |
| legalRepresentative | String | 否 | @Size(max=255) | 法人代表 |
| legalRepresentativeIdNumber | String | 否 | @Size(max=255) | 法人身份证号 |
| businessLicenseNumber | String | 否 | @Size(max=255) | 营业执照号 |
| organizationCode | String | 否 | @Size(max=255) | 组织机构代码 |
| remark | String | 否 | @Size(max=500) | 备注 |
| contactName | String | 否 | @Size(max=255) | 联系人 |
| officeTelephone | String | 否 | @Size(max=32) | 办公电话 |
| mobile | String | 否 | @Size(max=32) | 手机号码 |
| faxNumber | String | 否 | @Size(max=32) | 传真号码 |
| qqNumber | String | 否 | @Size(max=255) | QQ 号码 |
| email | String | 否 | @Email、@Size(max=255) | 邮箱 |
| otherContact | String | 否 | @Size(max=255) | 其他联系方式 |
| address | String | 否 | @Size(max=255) | 详细地址 |

**响应**: CommonResult&lt;Long&gt;（账套编号）

**业务逻辑**:
1. 校验公司编码在全局唯一（`ACCOUNT_SET_CODE_DUPLICATE`）。
2. 创建 `initialized = false` 的账套记录。
3. 调用账套用户服务将创建人写入 `fms_account_user`：第一个账套默认设为用户的默认账套，`founder = true`、级别为 OWNER。
4. 记录操作日志上下文并返回账套编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_001 | 账套编码已存在 |

### 1.2 更新账套

- **路径**: PUT /fms/config/account-set/update
- **权限**: fms:config:account-set:update
- **说明**: 更新账套的公司基本信息，要求账套主管（OWNER）权限。

**请求参数 (FmsAccountSetSaveReqVO)**: 同 1.1，其中 id 必填（更新目标）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套存在且当前用户为账套主管（OWNER 级）。
2. 校验公司编码唯一（排除自身）。
3. 更新账套基本信息。
4. 将修改前对象放入日志上下文，记录差异日志（@DiffLogField 字段）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_001 | 账套编码已存在 |

### 1.3 初始化账套

- **路径**: PUT /fms/config/account-set/initialize
- **权限**: fms:config:account-set:initialize
- **说明**: 对未初始化账套执行一键初始化，批量生成本位币、财务参数、凭证字、辅助核算类别、科目、结账模板/方案与首页指标。

**请求参数 (FmsAccountSetInitializeReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| currencyCode | String | 是 | @NotBlank、@InEnum(FmsCurrencyPresetEnum) | 本位币编码（预置币种） |
| startTime | LocalDateTime | 是 | @NotNull | 启用期间 |
| standard | Integer | 是 | @NotNull、@InEnum(FmsAccountingStandardEnum) | 会计制度 |
| level | Integer | 是 | @NotNull、@Min(1)、@Max(8) | 科目层级 |
| subjectCodeRule | String | 是 | @NotBlank、@Size(max=64) | 科目编码规则，如 `4-2-2-2` |
| ledgerBalanceMode | Integer | 是 | @NotNull、@InEnum(FmsLedgerBalanceModeEnum) | 账簿余额方向模式 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套成员写权限（未初始化账套由可维护成员完成初始化）；账套已初始化时抛出 `ACCOUNT_SET_ALREADY_INITIALIZED`。
2. 依次初始化基础数据：创建本位币（预置币别、`standard = true`）→ 创建财务参数（校验科目层级与编码规则匹配、各级长度 2~5 位）→ 批量创建预置凭证字 → 创建系统预置辅助核算类别 → 按标准科目模板转换编码后逐级创建账套科目 → 初始化结账模板 → 初始化默认结账方案 → 初始化预置首页财务指标。
3. 回写账套初始化信息：`initialized = true`、会计制度、启用期间（取所选月份的月初 0 点）、本位币编号。
4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_003 | 账套已完成初始化 |
| 1_052_100_006 | 科目编码规则不正确 |

### 1.4 获得账套

- **路径**: GET /fms/config/account-set/get
- **权限**: fms:config:account-set:query
- **说明**: 获得单个账套详情，并附带当前用户在该账套下的成员信息。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必填 | 账套编号 |

**响应**: CommonResult&lt;FmsAccountSetRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 账套编号 |
| companyCode | String | 公司编码 |
| companyName | String | 公司名称 |
| companyProfile | String | 公司简介 |
| industry | String | 所在行业 |
| location | String | 所在地 |
| legalRepresentative | String | 法人代表 |
| legalRepresentativeIdNumber | String | 法人身份证号 |
| businessLicenseNumber | String | 营业执照号 |
| organizationCode | String | 组织机构代码 |
| remark | String | 备注 |
| contactName | String | 联系人 |
| officeTelephone | String | 办公电话 |
| mobile | String | 手机号码 |
| faxNumber | String | 传真号码 |
| qqNumber | String | QQ 号码 |
| email | String | 邮箱 |
| otherContact | String | 其他联系方式 |
| address | String | 详细地址 |
| currencyId | Long | 币种编号 |
| startTime | LocalDateTime | 启用期间 |
| standard | Integer | 会计制度 |
| initialized | Boolean | 是否已初始化 |
| createTime | LocalDateTime | 创建时间 |
| defaultStatus | Boolean | 是否当前用户默认账套（来自账套用户） |
| founder | Boolean | 当前用户是否账套创建人（来自账套用户） |
| level | Integer | 当前用户的成员权限级别（来自账套用户） |

**业务逻辑**:
1. 校验账套存在且当前用户具备读权限。
2. 查询当前用户在该账套下的账套用户记录。
3. 拼接账套信息与成员信息（defaultStatus/founder/level）返回。

### 1.5 获得当前用户账套列表

- **路径**: GET /fms/config/account-set/list
- **权限**: fms:config:account-set:query
- **说明**: 获得当前登录用户有权访问的全部账套列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;FmsAccountSetRespVO&gt;&gt;（结构同 1.4）

**业务逻辑**:
1. 查询当前用户的全部账套用户记录。
2. 按 accountSetId 批量查询账套信息。
3. 逐条拼接账套信息与成员信息返回。

## 2. 账套用户管理 (/fms/config/account-user)

### 2.1 获得账套用户列表

- **路径**: GET /fms/config/account-user/list
- **权限**: fms:config:account-set:authorize
- **说明**: 获得账套的授权成员列表，附系统用户昵称、部门、联系方式等信息。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsAccountUserRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 后台用户编号 |
| nickname | String | 用户昵称（来自 system 用户） |
| deptName | String | 部门名称（来自 system 部门） |
| mobile | String | 手机号码 |
| email | String | 用户邮箱 |
| status | Integer | 用户状态 |
| defaultStatus | Boolean | 是否默认账套 |
| founder | Boolean | 是否账套创建人 |
| level | Integer | 成员权限级别 |

**业务逻辑**:
1. 校验当前用户对账套的读权限。
2. 查询账套全部成员记录。
3. 批量查询系统用户和部门信息，拼接昵称、手机号、邮箱、状态、部门名称后返回。

### 2.2 更新账套用户列表

- **路径**: PUT /fms/config/account-user/update
- **权限**: fms:config:account-set:authorize
- **说明**: 全量设置账套成员及权限级别（增、删、改），创建人（founder）不受影响。

**请求参数 (FmsAccountUserUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| members | List&lt;Member&gt; | 是 | @NotNull、@Size(max=100)、@Valid | 账套成员数组，单账套最多 100 名成员 |

Member 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 后台用户编号 |
| level | Integer | 是 | @NotNull、@InEnum(FmsAccountUserLevelEnum) | 成员权限级别 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前用户为账套主管；查询现有成员并分离 founder 集合。
2. 校验授权成员均为存在的后台用户。
3. 移出不再授权的成员（非 founder 且不在新列表中的记录）。
4. 更新已有成员的权限级别（仅级别变化时更新）。
5. 新增成员（`founder = false`、`defaultStatus = false`）。
6. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |

### 2.3 更新默认账套状态

- **路径**: PUT /fms/config/account-user/update-default-status
- **权限**: fms:config:account-set:query
- **说明**: 将指定账套设置为当前用户的默认账套。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验当前用户对目标账套的读权限（即用户属于该账套）。
2. 清除该用户原默认账套标记。
3. 将目标账套设置为默认账套。

## 3. 会计科目 (/fms/config/subject)

### 3.1 创建科目

- **路径**: POST /fms/config/subject/create
- **权限**: fms:config:subject:create
- **说明**: 在账套下新增会计科目，支持在上级科目已有业务数据时迁移历史数据。

**请求参数 (FmsSubjectSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 科目编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| code | String | 是 | @NotBlank、@Size(max=64) | 科目编码 |
| name | String | 是 | @NotBlank、@Size(max=255) | 科目名称 |
| parentId | Long | 是 | @NotNull | 上级科目编号（0 表示根） |
| type | Integer | 是 | @NotNull、@InEnum(FmsSubjectTypeEnum) | 科目类型 |
| category | Integer | 是 | @NotNull、@AssertTrue 校验与 type 匹配 | 科目类别 |
| balanceDirection | Integer | 是 | @NotNull、@InEnum(FmsDebitCreditDirectionEnum) | 余额方向 |
| auxiliaryTypeIds | List&lt;Long&gt; | 是 | @NotNull | 辅助核算类别编号数组 |
| currencyIds | List&lt;Long&gt; | 是 | @NotNull | 外币核算币别编号数组 |
| quantityAccounting | Boolean | 是 | @NotNull、@AssertTrue 校验启用时单位必填 | 是否启用数量核算 |
| quantityUnit | String | 否 | @Size(max=255) | 数量单位 |
| cash | Boolean | 是 | @NotNull | 是否现金及现金等价物 |
| migrateParentData | Boolean | 否 | - | 是否迁移上级科目历史数据 |
| auxiliaryMappings | List&lt;AuxiliaryMapping&gt; | 否 | 元素 @NotNull | 辅助核算历史数据迁移项目数组 |

AuxiliaryMapping 结构：typeId（辅助核算类别编号，@NotNull）、itemId（辅助核算项目编号，@NotNull）。

**响应**: CommonResult&lt;Long&gt;（科目编号）

**业务逻辑**:
1. 校验账套写权限；账套未初始化（无财务参数）时抛 `ACCOUNT_SET_NOT_INITIALIZED`。
2. 校验科目编码唯一、上级科目合法（同账套且类型/类别一致）、编码符合科目级次规则（长度等于前 N 级规则之和且以上级编码为前缀）。
3. 上级科目已有业务数据时，仅允许新增第一个下级且明确确认迁移，并要求新科目完整继承上级的余额方向与核算配置（否则抛 `SUBJECT_PARENT_IN_USE` / `SUBJECT_PARENT_CONFIG_INCOMPATIBLE`）。
4. 校验辅助核算类别与外币币别（外币核算不允许选本位币）。
5. 创建科目：按层级计算 level，状态默认启用。
6. 上级已有业务数据时，将上级的凭证分录、初始余额、辅助核算组合迁移到新科目；父科目变为非末级后清空其辅助核算配置。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_101_000 | 科目不存在 |
| 1_052_101_001 | 科目编码已存在 |
| 1_052_101_003 | 上级科目不属于当前账套，或科目类型、类别不一致 |
| 1_052_101_004 | 科目编码不符合科目级次规则 |
| 1_052_101_007 | 外币核算不能选择本位币 |
| 1_052_101_018 | 上级科目已有业务数据，新增下级前需要迁移历史数据 |
| 1_052_101_019 | 迁移历史数据时，下级科目的余额方向和核算配置必须与上级科目一致 |
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_107_000 | 币别不存在 |

### 3.2 更新科目

- **路径**: PUT /fms/config/subject/update
- **权限**: fms:config:subject:update
- **说明**: 修改科目配置；上级不可变更，已使用科目的可修改范围受严格限制。

**请求参数 (FmsSubjectSaveReqVO)**: 同 3.1（id 必填），另可携带 auxiliaryMappings 用于已用科目首次启用辅助核算时的历史数据迁移。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、账套已初始化、科目存在。
2. 校验上级科目不可变更（传入 parentId 必须与原值一致）。
3. 统计科目使用情况并校验修改范围：非末级不能改类型/类别/辅助核算；已用科目不能改余额方向；已用科目仅允许"从未启用辅助核算"迁移为启用；有数量数据时不能关闭数量核算。
4. 校验编码唯一、编码规则；有下级科目时不能修改编码。
5. 校验辅助核算类别和币别；已用科目首次启用辅助核算时，校验每个类别恰好对应一个启用状态的迁移项目（`auxiliaryMappings`）。
6. 更新科目（parentId 与 level 保持原值）。
7. 触发迁移时，为科目保存辅助核算组合，并把历史凭证分录的辅助核算迁移到该组合。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_101_000 | 科目不存在 |
| 1_052_101_001 | 科目编码已存在 |
| 1_052_101_003 | 上级科目不属于当前账套，或科目类型、类别不一致 |
| 1_052_101_004 | 科目编码不符合科目级次规则 |
| 1_052_101_005 | 科目下有子级科目，不能删除或修改编码 |
| 1_052_101_007 | 外币核算不能选择本位币 |
| 1_052_101_014 | 科目已有业务数据，不能修改余额方向 |
| 1_052_101_015 | 科目已有业务数据，不能直接修改辅助核算 |
| 1_052_101_016 | 非末级科目不能修改科目类型、类别或辅助核算 |
| 1_052_101_017 | 科目已有数量数据，不能关闭数量核算 |
| 1_052_101_020 | 科目已有业务数据，新增辅助核算时必须为每个类别选择有效的迁移项目 |
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_107_000 | 币别不存在 |

### 3.3 删除科目

- **路径**: DELETE /fms/config/subject/delete-list
- **权限**: fms:config:subject:delete
- **说明**: 批量删除科目，要求无下级且未被任何业务引用。

**请求参数 (FmsSubjectDeleteReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 科目编号数组 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验科目全部存在（数量不一致抛 `SUBJECT_NOT_EXISTS`）。
3. 校验科目没有下级科目。
4. 依次校验科目未被凭证分录、凭证模板、初始余额、辅助核算组合、结账方案、结账模板引用。
5. 批量删除科目。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_101_000 | 科目不存在 |
| 1_052_101_005 | 科目下有子级科目，不能删除或修改编码 |
| 1_052_101_008 | 科目已被 {} 条凭证分录使用，不能删除 |
| 1_052_101_009 | 科目已被 {} 个凭证模板使用，不能删除 |
| 1_052_101_010 | 科目已被 {} 条初始余额使用，不能删除 |
| 1_052_101_011 | 科目已被 {} 个辅助核算组合使用，不能删除 |
| 1_052_101_012 | 科目已被 {} 个结账方案使用，不能删除 |
| 1_052_101_021 | 科目已被 {} 个结账模板使用，不能删除 |

### 3.4 更新科目状态

- **路径**: PUT /fms/config/subject/update-status
- **权限**: fms:config:subject:update
- **说明**: 启用/停用科目，状态变更递归作用于全部子孙科目。

**请求参数 (FmsSubjectStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 科目编号数组 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 停用） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验科目全部存在。
3. 逐层递归收集选中科目的全部子孙科目编号。
4. 批量更新科目状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_101_000 | 科目不存在 |

### 3.5 获得科目

- **路径**: GET /fms/config/subject/get
- **权限**: fms:config:subject:query
- **说明**: 获得单个科目详情，附辅助核算类别名称。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 科目编号 |

**响应**: CommonResult&lt;FmsSubjectRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 科目编号 |
| accountSetId | Long | 账套编号 |
| code | String | 科目编码 |
| name | String | 科目名称 |
| parentId | Long | 上级科目编号 |
| type | Integer | 科目类型 |
| category | Integer | 科目类别 |
| categoryDictValue | String | 类别字典值（仅 Excel 导出使用） |
| balanceDirection | Integer | 余额方向 |
| auxiliaryTypeIds | List&lt;Long&gt; | 辅助核算类别编号数组 |
| auxiliaryTypeNames | List&lt;String&gt; | 辅助核算类别名称数组 |
| currencyIds | List&lt;Long&gt; | 外币核算币别编号数组 |
| quantityAccounting | Boolean | 是否启用数量核算 |
| quantityUnit | String | 数量单位（未启用数量核算时返回空串） |
| cash | Boolean | 是否现金及现金等价物 |
| status | Integer | 状态 |
| level | Integer | 层级 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询科目（校验属于当前账套）。
3. 批量查询辅助核算类别名称并拼接返回。

### 3.6 获得科目使用情况

- **路径**: GET /fms/config/subject/get-usage
- **权限**: fms:config:subject:query
- **说明**: 统计科目被下级科目与各业务（凭证分录、初始余额、辅助核算组合、数量数据）引用的情况，用于前端删除/修改前的提示。

**请求参数 (Query 参数)**: 同 3.5。

**响应**: CommonResult&lt;FmsSubjectUsageRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| childCount | Long | 下级科目数量 |
| voucherEntryCount | Long | 凭证分录数量 |
| initialBalanceCount | Long | 初始余额数量 |
| auxiliaryCombinationCount | Long | 辅助核算组合数量 |
| quantityDataCount | Long | 包含数量数据的记录数量 |
| used | Boolean | 是否已被业务使用 |

**业务逻辑**:
1. 校验账套读权限、科目存在。
2. 统计凭证分录、初始余额、辅助核算组合的引用数量。
3. 统计凭证分录与初始余额中含实际数量的记录数。
4. 组装使用情况，`used` = 三类业务引用数之和大于 0。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_101_000 | 科目不存在 |

### 3.7 获得科目列表

- **路径**: GET /fms/config/subject/list
- **权限**: fms:config:subject:query
- **说明**: 按账套（可选科目类型）查询科目列表，响应结构同 3.5。

**请求参数 (FmsSubjectListReqVO，Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| type | Integer | 否 | @InEnum(FmsSubjectTypeEnum) | 科目类型 |

**响应**: CommonResult&lt;List&lt;FmsSubjectRespVO&gt;&gt;

**业务逻辑**:
1. 校验账套读权限。
2. 按账套与类型查询科目列表并拼接辅助核算名称返回。

### 3.8 获得科目精简列表

- **路径**: GET /fms/config/subject/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 用于前端下拉选项，只返回 id/parentId/code/name/type/balanceDirection/status/level/auxiliaryTypeIds/quantityAccounting/quantityUnit 字段。

**请求参数 (FmsSubjectListReqVO，Query)**: 同 3.7。

**响应**: CommonResult&lt;List&lt;FmsSubjectRespVO&gt;&gt;（仅精简字段）

**业务逻辑**:
1. 校验账套读权限。
2. 查询科目列表并裁剪为精简字段返回。

### 3.9 导出科目

- **路径**: GET /fms/config/subject/export-excel
- **权限**: fms:config:subject:export
- **说明**: 按查询条件导出科目 Excel（科目设置.xlsx）。

**请求参数 (FmsSubjectListReqVO，Query)**: 同 3.7。

**响应**: Excel 文件流（列：编码、名称、类别、余额方向、辅助核算、数量、是否现金项）

**业务逻辑**:
1. 校验账套读权限并查询科目列表。
2. 拼接响应 VO（类别转字典值、辅助核算名称数组、未启用数量核算时清空单位）。
3. 通过 ExcelUtils 输出文件。

### 3.10 获得科目导入模板

- **路径**: GET /fms/config/subject/get-import-template
- **权限**: fms:config:subject:import
- **说明**: 下载科目导入 Excel 模板（含两行示例数据）。

**请求参数**: 无

**响应**: Excel 文件流（列：科目编码、科目名称、上级科目编码、余额方向、类别、辅助核算）

**业务逻辑**:
1. 构造示例行（一级科目"1001 库存现金"、二级科目"100101 人民币现金"）。
2. 输出"科目导入模板.xlsx"。

### 3.11 导入科目

- **路径**: POST /fms/config/subject/import
- **权限**: fms:config:subject:import
- **说明**: 从 Excel 批量导入科目，按编码级次从短到长依次创建；已存在且未被业务使用的科目允许覆盖。

**请求参数 (form-data)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| file | MultipartFile | 是 | - | Excel 文件（列：科目编码、科目名称、上级科目编码、余额方向、类别、辅助核算） |

**响应**: CommonResult&lt;FmsSubjectImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalCount | Integer | 总数量 |
| successSubjectCodes | List&lt;String&gt; | 成功科目编码数组 |
| failureReasons | Map&lt;String, String&gt; | 失败原因（键为"第 N 行（编码 名称）"） |

**业务逻辑**:
1. 校验导入数据非空、账套写权限、账套已初始化；加载已有科目（按编码索引）和辅助核算类别名称映射。
2. 按编码长度（级次）从短到长排序后逐行导入。
3. 逐行校验：字段必填、文件内编码不重复、类别名称与余额方向名称合法、上级科目存在且类型/类别一致、辅助核算类别名称存在。
4. 新科目走创建校验（编码唯一、编码规则、上级未占用、辅助核算类别有效）；已存在科目仅在其无下级且无业务引用时覆盖（保留主键与状态）。
5. 覆盖或创建后，将上级科目的辅助核算配置清空（避免残留配置占用辅助类别）。
6. 汇总成功编码与失败原因返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_101_000 | 科目不存在 |
| 1_052_101_001 | 科目编码已存在 |
| 1_052_101_004 | 科目编码不符合科目级次规则 |
| 1_052_101_013 | 导入科目数据不能为空 |
| 1_052_101_018 | 上级科目已有业务数据，新增下级前需要迁移历史数据 |

## 4. 辅助核算类别 (/fms/config/auxiliary-type)

### 4.1 创建辅助核算类别

- **路径**: POST /fms/config/auxiliary-type/create
- **权限**: fms:config:auxiliary:create
- **说明**: 在账套下创建自定义辅助核算类别（系统预置类别不可创建）。

**请求参数 (FmsAuxiliaryTypeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 名称 |

**响应**: CommonResult&lt;Long&gt;（类别编号）

**业务逻辑**:
1. 校验账套写权限。
2. 校验同账套内名称唯一。
3. 创建类别：`systemPreset = false`、类型为自定义（CUSTOM）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_001 | 辅助核算类别名称已存在 |

### 4.2 更新辅助核算类别

- **路径**: PUT /fms/config/auxiliary-type/update
- **权限**: fms:config:auxiliary:update
- **说明**: 修改自定义辅助核算类别名称，系统预置类别不允许修改。

**请求参数 (FmsAuxiliaryTypeSaveReqVO)**: 同 4.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验类别存在且属于当前账套；系统预置类别不可编辑。
3. 校验名称唯一。
4. 仅更新名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_001 | 辅助核算类别名称已存在 |
| 1_052_102_002 | 系统预置辅助核算类别不能编辑或删除 |

### 4.3 删除辅助核算类别

- **路径**: DELETE /fms/config/auxiliary-type/delete
- **权限**: fms:config:auxiliary:delete
- **说明**: 删除自定义辅助核算类别，要求类别下无项目且未被任何业务引用。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 辅助核算类别编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验类别存在且为自定义类别（预置不可删除）。
3. 依次校验：类别下没有项目、未被科目使用、未被凭证分录使用、未被凭证模板使用、未被初始余额使用。
4. 删除类别。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_002 | 系统预置辅助核算类别不能编辑或删除 |
| 1_052_102_003 | 辅助核算类别下有 {} 个项目，不能删除 |
| 1_052_102_006 | 辅助核算类别已被 {} 个科目使用，不能删除 |
| 1_052_102_012 | 辅助核算类别已被 {} 条凭证分录使用，不能删除 |
| 1_052_102_013 | 辅助核算类别已被 {} 个凭证模板使用，不能删除 |
| 1_052_102_014 | 辅助核算类别已被 {} 条初始余额使用，不能删除 |

### 4.4 获得辅助核算类别列表

- **路径**: GET /fms/config/auxiliary-type/list
- **权限**: fms:config:auxiliary:query
- **说明**: 获得账套下全部辅助核算类别（含系统预置与自定义）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsAuxiliaryTypeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 名称 |
| systemPreset | Boolean | 是否系统预置 |
| accountSetId | Long | 账套编号 |
| type | Integer | 类型（客户/供应商/存货/部门/职员/自定义等） |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套下全部类别返回。

### 4.5 获得辅助核算类别精简列表

- **路径**: GET /fms/config/auxiliary-type/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 用于前端下拉选项，只返回 id/name/type。

**请求参数 (Query 参数)**: 同 4.4。

**响应**: CommonResult&lt;List&lt;FmsAuxiliaryTypeRespVO&gt;&gt;（仅精简字段）

**业务逻辑**:
1. 校验账套读权限。
2. 查询类别并裁剪为精简字段返回。

## 5. 辅助核算项目 (/fms/config/auxiliary-item)

### 5.1 创建辅助核算项目

- **路径**: POST /fms/config/auxiliary-item/create
- **权限**: fms:config:auxiliary:create
- **说明**: 在指定辅助核算类别下创建项目，创建后默认启用。

**请求参数 (FmsAuxiliaryItemSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| auxiliaryTypeId | Long | 是 | @NotNull | 辅助核算类别编号 |
| code | String | 是 | @NotBlank、@Size(max=64) | 编码 |
| name | String | 是 | @NotBlank、@Size(max=255) | 名称 |
| remark | String | 否 | @Size(max=500) | 备注 |
| specification | String | 否 | @Size(max=255) | 规格（存货类） |
| unit | String | 否 | @Size(max=255) | 单位（存货类） |

**响应**: CommonResult&lt;Long&gt;（项目编号）

**业务逻辑**:
1. 校验账套写权限。
2. 校验辅助核算类别存在；校验同类别下编码唯一。
3. 创建项目，状态默认启用。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_005 | 辅助核算项目编码已存在 |

### 5.2 更新辅助核算项目

- **路径**: PUT /fms/config/auxiliary-item/update
- **权限**: fms:config:auxiliary:update
- **说明**: 修改辅助核算项目信息，所属类别不可变更，状态保持不变。

**请求参数 (FmsAuxiliaryItemSaveReqVO)**: 同 5.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验项目存在；传入的 auxiliaryTypeId 必须与原类别一致且类别存在。
3. 校验编码唯一。
4. 更新项目（状态保留原值）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_102_005 | 辅助核算项目编码已存在 |

### 5.3 删除辅助核算项目

- **路径**: DELETE /fms/config/auxiliary-item/delete-list
- **权限**: fms:config:auxiliary:delete
- **说明**: 批量删除辅助核算项目，要求未被业务引用；删除时级联清理派生的辅助核算组合。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 辅助核算项目编号数组 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验项目全部存在。
3. 依次校验项目未被凭证分录、凭证模板、初始余额使用。
4. 删除相关辅助核算组合，再批量删除项目。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_102_007 | 辅助核算项目已被 {} 条凭证分录使用，不能删除 |
| 1_052_102_009 | 辅助核算项目已被 {} 个凭证模板使用，不能删除 |
| 1_052_102_010 | 辅助核算项目已被 {} 条初始余额使用，不能删除 |

### 5.4 更新辅助核算项目状态

- **路径**: PUT /fms/config/auxiliary-item/update-status
- **权限**: fms:config:auxiliary:update
- **说明**: 启用/停用单个辅助核算项目。

**请求参数 (FmsAuxiliaryItemStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 停用） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验项目存在。
3. 更新状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_004 | 辅助核算项目不存在 |

### 5.5 获得辅助核算项目

- **路径**: GET /fms/config/auxiliary-item/get
- **权限**: fms:config:auxiliary:query
- **说明**: 获得单个辅助核算项目详情。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 辅助核算项目编号 |

**响应**: CommonResult&lt;FmsAuxiliaryItemRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| accountSetId | Long | 账套编号 |
| auxiliaryTypeId | Long | 辅助核算类别编号 |
| code | String | 编码 |
| name | String | 名称 |
| remark | String | 备注 |
| specification | String | 规格 |
| unit | String | 单位 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询并校验项目属于当前账套后返回。

### 5.6 获得辅助核算项目分页

- **路径**: GET /fms/config/auxiliary-item/page
- **权限**: fms:config:auxiliary:query / fms:voucher:create / fms:voucher:update（任一）
- **说明**: 按类别分页查询辅助核算项目，支持关键词模糊匹配编码或名称。

**请求参数 (FmsAuxiliaryItemPageReqVO，Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | PageParam 默认 1 | 页码 |
| pageSize | Integer | 否 | PageParam 默认 10 | 每页条数 |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| auxiliaryTypeId | Long | 是 | @NotNull | 辅助核算类别编号 |
| search | String | 否 | - | 关键词，匹配编码或名称 |

**响应**: CommonResult&lt;PageResult&lt;FmsAuxiliaryItemRespVO&gt;&gt;（列表结构同 5.5，另含 total）

**业务逻辑**:
1. 校验账套读权限。
2. 校验辅助核算类别存在。
3. 分页查询项目返回。

### 5.7 获得辅助核算项目精简列表

- **路径**: GET /fms/config/auxiliary-item/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 只返回指定类别下启用状态的项目，用于录凭证等前端下拉选项。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| auxiliaryTypeId | Long | 是 | @NotNull | 辅助核算类别编号 |

**响应**: CommonResult&lt;List&lt;FmsAuxiliaryItemRespVO&gt;&gt;（仅 id/code/name）

**业务逻辑**:
1. 校验账套读权限、类别存在。
2. 查询指定类别下启用状态的项目并裁剪字段返回。

### 5.8 导出辅助核算项目

- **路径**: GET /fms/config/auxiliary-item/export-excel
- **权限**: fms:config:auxiliary:export
- **说明**: 按查询条件导出辅助核算项目 Excel，文件名为类别名称，表头随类别类型动态变化（客户/供应商含备注，存货含规格与单位，其他仅编码与名称）。

**请求参数 (FmsAuxiliaryItemPageReqVO，Query)**: 同 5.6（pageSize 导出时强制不分页）。

**响应**: Excel 文件流

**业务逻辑**:
1. 将分页参数置为不分页，校验账套读权限与类别存在后查询全部项目。
2. 查询辅助核算类别，按类别类型构建动态表头与数据行。
3. 输出 Excel（文件名为"{类别名称}.xlsx"）。

### 5.9 获得辅助核算项目导入模板

- **路径**: GET /fms/config/auxiliary-item/get-import-template
- **权限**: fms:config:auxiliary:import
- **说明**: 下载辅助核算项目导入模板；存货类别模板额外包含规格与单位列。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| type | Integer | 是 | @InEnum(FmsAuxiliaryTypeEnum) | 辅助核算类别类型 |

**响应**: Excel 文件流（列：编码、名称、备注，存货类另含规格、单位）

**业务逻辑**:
1. 构造示例行（编码 001、名称"示例项目"）；类型为存货时补充规格与单位。
2. 输出"辅助核算项目导入模板.xlsx"。

### 5.10 导入辅助核算项目

- **路径**: POST /fms/config/auxiliary-item/import
- **权限**: fms:config:auxiliary:import
- **说明**: 从 Excel 批量导入辅助核算项目，仅新增（编码已存在视为失败行）。

**请求参数 (form-data)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| auxiliaryTypeId | Long | 是 | @NotNull | 辅助核算类别编号 |
| file | MultipartFile | 是 | - | Excel 文件（列：编码、名称、备注，存货类另含规格、单位） |

**响应**: CommonResult&lt;FmsAuxiliaryItemImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalCount | Integer | 总数量 |
| successItemCodes | List&lt;String&gt; | 成功编码数组 |
| failureReasons | Map&lt;String, String&gt; | 失败原因（键为"第 N 行（编码 名称）"） |

**业务逻辑**:
1. 校验导入数据非空、账套写权限、类别存在；加载该类别下已有项目（按编码索引）。
2. 逐行校验字段（编码/名称必填、长度限制）、文件内编码不重复、库内编码不重复。
3. 构造项目（状态默认启用）；类别为存货时写入规格与单位。
4. 逐行插入并汇总成功编码与失败原因返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_008 | 导入辅助核算项目数据不能为空 |

## 6. 币别 (/fms/config/currency)

### 6.1 创建币别

- **路径**: POST /fms/config/currency/create
- **权限**: fms:config:currency:create
- **说明**: 在账套下创建外币（本位币仅能通过账套初始化生成）。

**请求参数 (FmsCurrencySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 币别编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| code | String | 是 | @NotBlank、@Size(max=64)、@Pattern(以字母开头，仅字母/数字/下划线) | 币别编码 |
| name | String | 是 | @NotBlank、@Size(max=255) | 币别名称 |
| exchangeRate | BigDecimal | 是 | @NotNull、@DecimalMin(>0)、@Digits(integer=12, fraction=6) | 汇率 |

**响应**: CommonResult&lt;Long&gt;（币别编号）

**业务逻辑**:
1. 校验账套写权限。
2. 校验同账套内币别编码唯一。
3. 创建币别，`standard = false`。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_107_001 | 币别编码已存在 |

### 6.2 更新币别

- **路径**: PUT /fms/config/currency/update
- **权限**: fms:config:currency:update
- **说明**: 修改币别信息；本位币的编码与汇率不可修改（汇率固定为 1）。

**请求参数 (FmsCurrencySaveReqVO)**: 同 6.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、币别存在。
2. 本位币时强制保留原编码并将汇率置为 1。
3. 校验编码唯一后更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_107_000 | 币别不存在 |
| 1_052_107_001 | 币别编码已存在 |

### 6.3 删除币别

- **路径**: DELETE /fms/config/currency/delete
- **权限**: fms:config:currency:delete
- **说明**: 删除外币，本位币与已被科目使用的币别不允许删除。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 币别编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、币别存在。
2. 本位币不允许删除。
3. 校验币别未被科目外币核算使用。
4. 删除币别。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_107_000 | 币别不存在 |
| 1_052_107_002 | 本位币不允许删除 |
| 1_052_107_003 | 币别已被科目使用，不能删除 |

### 6.4 获得币别列表

- **路径**: GET /fms/config/currency/list
- **权限**: fms:config:currency:query
- **说明**: 获得账套下全部币别（含本位币）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsCurrencyRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 币别编号 |
| accountSetId | Long | 账套编号 |
| code | String | 币别编码 |
| name | String | 币别名称 |
| exchangeRate | BigDecimal | 汇率 |
| standard | Boolean | 是否本位币 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套下全部币别返回。

### 6.5 获得币别精简列表

- **路径**: GET /fms/config/currency/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 用于前端下拉选项，返回 id/code/name/exchangeRate/standard。

**请求参数 (Query 参数)**: 同 6.4。

**响应**: CommonResult&lt;List&lt;FmsCurrencyRespVO&gt;&gt;（仅精简字段）

**业务逻辑**:
1. 校验账套读权限。
2. 查询币别并裁剪为精简字段返回。

## 7. 凭证字 (/fms/config/voucher-word)

### 7.1 创建凭证字

- **路径**: POST /fms/config/voucher-word/create
- **权限**: fms:config:voucher-word:create
- **说明**: 在账套下创建凭证字（如"记"、"收"、"付"），支持设为默认凭证字。

**请求参数 (FmsVoucherWordSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 凭证字编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 凭证字 |
| printTitle | String | 否 | @Size(max=255) | 打印标题 |
| defaultStatus | Boolean | 是 | @NotNull | 是否默认凭证字 |

**响应**: CommonResult&lt;Long&gt;（凭证字编号）

**业务逻辑**:
1. 校验账套写权限、凭证字名称唯一。
2. 确定默认状态：账套内尚无凭证字时强制默认；设为默认时清除原默认凭证字。
3. 按账套内最大 sort + 1 追加排序后创建。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_012 | 凭证字已存在 |

### 7.2 修改凭证字

- **路径**: PUT /fms/config/voucher-word/update
- **权限**: fms:config:voucher-word:update
- **说明**: 修改凭证字名称、打印标题与默认状态；使用中的凭证字不能改内容，至少保留一个默认凭证字。

**请求参数 (FmsVoucherWordSaveReqVO)**: 同 7.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、凭证字存在。
2. 名称或打印标题变化且已被凭证使用时，禁止编辑。
3. 校验名称唯一。
4. 原为默认凭证字而请求改为非默认时，禁止（必须保留默认）。
5. 请求设为默认时，清除其他默认凭证字。
6. 更新凭证字。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |
| 1_052_103_012 | 凭证字已存在 |
| 1_052_103_013 | 请确保至少有一个默认凭证字 |
| 1_052_103_015 | 使用中的凭证字不能编辑 |

### 7.3 删除凭证字

- **路径**: DELETE /fms/config/voucher-word/delete
- **权限**: fms:config:voucher-word:delete
- **说明**: 删除非默认且未被使用的凭证字。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |
| id | Long | 是 | @RequestParam 必填 | 凭证字编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、凭证字存在。
2. 默认凭证字不允许删除。
3. 校验未被凭证使用、未被结账方案使用。
4. 删除凭证字。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_001 | 凭证字不存在 |
| 1_052_103_014 | 默认凭证字不允许删除 |
| 1_052_103_016 | 该凭证字已被 {} 张凭证使用，不能删除 |
| 1_052_103_030 | 该凭证字已被 {} 个结账方案使用，不能删除 |

### 7.4 获得凭证字管理列表

- **路径**: GET /fms/config/voucher-word/list
- **权限**: fms:config:voucher-word:query
- **说明**: 获得账套下全部凭证字（管理页使用，响应结构同 7.5）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsVoucherWordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 凭证字编号 |
| name | String | 凭证字 |
| printTitle | String | 打印标题 |
| defaultStatus | Boolean | 是否默认凭证字 |
| sort | Integer | 显示顺序 |
| accountSetId | Long | 账套编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套下全部凭证字返回。

### 7.5 获得凭证字精简列表

- **路径**: GET /fms/config/voucher-word/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 用于录凭证等前端下拉选项，返回 id/name/defaultStatus。

**请求参数 (Query 参数)**: 同 7.4。

**响应**: CommonResult&lt;List&lt;FmsVoucherWordRespVO&gt;&gt;（仅精简字段）

**业务逻辑**:
1. 校验账套读权限。
2. 查询凭证字并裁剪为精简字段返回。

## 8. 凭证模板 (/fms/config/voucher-template)

### 8.1 创建凭证模板

- **路径**: POST /fms/config/voucher-template/create
- **权限**: fms:config:voucher-template:create
- **说明**: 创建凭证模板（预置分录的凭证样式），供录凭证时套用。

**请求参数 (FmsVoucherTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 模板编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 模板名称 |
| categoryId | Long | 是 | @NotNull | 分类编号 |
| entries | List&lt;FmsVoucherTemplateEntryVO&gt; | 是 | @Valid、@NotEmpty、@Size(min=2) | 凭证模板分录数组，至少两条 |

FmsVoucherTemplateEntryVO 结构：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| digest | String | 是 | @NotBlank、@Size(max=500) | 摘要内容 |
| subjectId | Long | 是 | @NotNull | 科目编号 |
| quantity | BigDecimal | 否 | @DecimalMin(0)、@Digits(integer=14, fraction=4) | 数量 |
| unitPrice | BigDecimal | 否 | @DecimalMin(0)、@Digits(integer=12, fraction=6) | 单价 |
| debitAmount | BigDecimal | 否 | @Digits(integer=16, fraction=2) | 借方金额 |
| creditAmount | BigDecimal | 否 | @Digits(integer=16, fraction=2) | 贷方金额 |
| auxiliaries | List&lt;AuxiliaryItem&gt; | 否 | @Valid | 辅助核算项目数组 |

AuxiliaryItem 结构：type（辅助核算类型）、typeId（类别编号，@NotNull）、itemId（项目编号，@NotNull）、name（项目名称）。

**响应**: CommonResult&lt;Long&gt;（模板编号）

**业务逻辑**:
1. 校验账套写权限、模板分类存在。
2. 批量校验分录：科目存在且启用、必须为末级科目；单条分录只能填借方或贷方金额；数量核算科目需满足"数量 × 单价 = 金额"，非数量核算科目不允许填数量单价；存在金额时借贷必须平衡。
3. 批量校验辅助核算类别和项目存在；逐条校验辅助核算与科目启用的类别完全一致，项目属于对应类别且处于启用状态。
4. 构造模板 JSON 分录（补充辅助核算类型与名称）并创建模板。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_101_000 | 科目不存在 |
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_103_004 | 凭证分录只能填写借方或贷方金额 |
| 1_052_103_005 | 凭证借贷金额不平衡 |
| 1_052_103_008 | 凭证分录使用了已停用科目 |
| 1_052_103_009 | 凭证分录不能使用非末级科目 |
| 1_052_103_010 | 凭证分录的辅助核算项目不完整 |
| 1_052_103_011 | 凭证分录的数量核算信息不正确 |
| 1_052_103_017 | 凭证模板分类不存在 |

### 8.2 修改凭证模板

- **路径**: PUT /fms/config/voucher-template/update
- **权限**: fms:config:voucher-template:update
- **说明**: 修改模板名称、分类与分录，校验规则同创建。

**请求参数 (FmsVoucherTemplateSaveReqVO)**: 同 8.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、模板存在、模板分类存在。
2. 校验并构造模板分录（同 8.1 第 2~3 步）。
3. 更新模板名称、分类与分录。

**错误码**: 同 8.1，另含：

| 错误码 | 说明 |
|-------|------|
| 1_052_103_020 | 凭证模板不存在 |

### 8.3 删除凭证模板

- **路径**: DELETE /fms/config/voucher-template/delete
- **权限**: fms:config:voucher-template:delete
- **说明**: 删除单个凭证模板。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |
| id | Long | 是 | @RequestParam 必填 | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、模板存在。
2. 删除模板。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_020 | 凭证模板不存在 |

### 8.4 获得凭证模板列表

- **路径**: GET /fms/config/voucher-template/list
- **权限**: fms:config:voucher-template:query
- **说明**: 获得账套下全部凭证模板，附分类名称（管理页使用，响应结构同 8.5）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsVoucherTemplateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模板编号 |
| accountSetId | Long | 账套编号 |
| name | String | 模板名称 |
| categoryId | Long | 分类编号 |
| categoryName | String | 分类名称 |
| entries | List&lt;FmsVoucherTemplateEntryVO&gt; | 凭证模板分录数组（结构同 8.1） |

**业务逻辑**:
1. 校验账套读权限。
2. 查询模板分类 Map 与模板列表，回填 categoryName 后返回。

### 8.5 获得凭证模板精简列表

- **路径**: GET /fms/config/voucher-template/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize；Service 内校验账套读权限）
- **说明**: 用于录凭证时套用凭证模板，响应结构同 8.4。

**请求参数 (Query 参数)**: 同 8.4。

**响应**: CommonResult&lt;List&lt;FmsVoucherTemplateRespVO&gt;&gt;

**业务逻辑**:
1. 校验账套读权限。
2. 查询模板并回填分类名称返回。

## 9. 凭证模板分类 (/fms/config/voucher-template-category)

### 9.1 创建凭证模板分类

- **路径**: POST /fms/config/voucher-template-category/create
- **权限**: fms:config:voucher-template-category:create
- **说明**: 创建凭证模板的分类（如"日常收支"）。

**请求参数 (FmsVoucherTemplateCategorySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 分类编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=255) | 分类名称 |

**响应**: CommonResult&lt;Long&gt;（分类编号）

**业务逻辑**:
1. 校验账套写权限。
2. 校验同账套内分类名称唯一。
3. 创建分类。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_018 | 凭证模板分类已存在 |

### 9.2 修改凭证模板分类

- **路径**: PUT /fms/config/voucher-template-category/update
- **权限**: fms:config:voucher-template-category:update
- **说明**: 修改分类名称。

**请求参数 (FmsVoucherTemplateCategorySaveReqVO)**: 同 9.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验分类存在且属于当前账套、名称唯一。
3. 仅更新名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_017 | 凭证模板分类不存在 |
| 1_052_103_018 | 凭证模板分类已存在 |

### 9.3 删除凭证模板分类

- **路径**: DELETE /fms/config/voucher-template-category/delete
- **权限**: fms:config:voucher-template-category:delete
- **说明**: 删除未被模板使用的分类。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |
| id | Long | 是 | @RequestParam 必填 | 分类编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限、分类存在。
2. 分类下存在凭证模板时禁止删除。
3. 删除分类。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_017 | 凭证模板分类不存在 |
| 1_052_103_019 | 分类下存在凭证模板，不能删除 |

### 9.4 获得凭证模板分类列表

- **路径**: GET /fms/config/voucher-template-category/list
- **权限**: fms:config:voucher-template-category:query
- **说明**: 获得账套下全部模板分类（响应结构同 9.5）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsVoucherTemplateCategoryRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 分类编号 |
| accountSetId | Long | 账套编号 |
| name | String | 分类名称 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套下全部分类返回。

### 9.5 获得凭证模板分类精简列表

- **路径**: GET /fms/config/voucher-template-category/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize；Service 内校验账套读权限）
- **说明**: 用于前端下拉选项，返回 id/name。

**请求参数 (Query 参数)**: 同 9.4。

**响应**: CommonResult&lt;List&lt;FmsVoucherTemplateCategoryRespVO&gt;&gt;（仅精简字段）

**业务逻辑**:
1. 校验账套读权限。
2. 查询分类并裁剪为精简字段返回。

## 10. 常用摘要 (/fms/config/digest)

### 10.1 创建常用摘要

- **路径**: POST /fms/config/digest/create
- **权限**: fms:config:digest:create
- **说明**: 在账套下创建常用摘要，供录凭证时快速引用。

**请求参数 (FmsDigestSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 常用摘要编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| content | String | 是 | @NotBlank、@Size(max=500) | 摘要内容 |

**响应**: CommonResult&lt;Long&gt;（摘要编号）

**业务逻辑**:
1. 校验账套写权限。
2. 创建常用摘要。

### 10.2 修改常用摘要

- **路径**: PUT /fms/config/digest/update
- **权限**: fms:config:digest:update
- **说明**: 修改摘要内容。

**请求参数 (FmsDigestSaveReqVO)**: 同 10.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验摘要存在且属于当前账套。
3. 更新摘要。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_021 | 常用摘要不存在 |

### 10.3 删除常用摘要

- **路径**: DELETE /fms/config/digest/delete
- **权限**: fms:config:digest:delete
- **说明**: 删除单个常用摘要。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |
| id | Long | 是 | @RequestParam 必填 | 常用摘要编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验摘要存在。
3. 删除摘要。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_103_021 | 常用摘要不存在 |

### 10.4 获得常用摘要管理列表

- **路径**: GET /fms/config/digest/list
- **权限**: fms:config:digest:query
- **说明**: 获得账套下全部常用摘要（响应结构同 10.5）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsDigestRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 常用摘要编号 |
| accountSetId | Long | 账套编号 |
| content | String | 摘要内容 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套下全部摘要返回。

### 10.5 获得常用摘要精简列表

- **路径**: GET /fms/config/digest/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 用于录凭证等前端下拉选项，返回 id/accountSetId/content。

**请求参数 (Query 参数)**: 同 10.4。

**响应**: CommonResult&lt;List&lt;FmsDigestRespVO&gt;&gt;（仅精简字段）

**业务逻辑**:
1. 校验账套读权限。
2. 查询摘要并裁剪为精简字段返回。

## 11. 首页财务指标 (/fms/config/finance-indicator)

### 11.1 创建首页财务指标

- **路径**: POST /fms/config/finance-indicator/create
- **权限**: fms:config:finance-indicator:create
- **说明**: 创建首页展示的财务指标，公式支持行次公式（`L1+L2-L3`）或科目公式 JSON。

**请求参数 (FmsFinanceIndicatorSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 指标编号（新增时置空） |
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| name | String | 是 | @NotBlank、@Size(max=100) | 指标名称 |
| code | String | 是 | @NotBlank、@Size(max=64) | 指标编码 |
| type | Integer | 是 | @NotNull、@InEnum(FmsFinanceIndicatorTypeEnum) | 取数报表类型（利润表/资产负债表） |
| formula | String | 是 | @NotBlank、@Size(max=2000) | 指标公式，支持 `L1+L2` 行次公式或科目公式 JSON |
| sort | Integer | 是 | @NotNull | 展示顺序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态（0 开启 / 1 停用） |

**响应**: CommonResult&lt;Long&gt;（指标编号）

**业务逻辑**:
1. 校验账套写权限。
2. 校验公式合法性：匹配行次公式正则，或可解析为 JSON 数组（科目公式）。
3. 校验指标编码在同账套内唯一。
4. 公式归一化：去除空格；行次公式转换为 JSON 数组形式；科目公式按账套科目编码绑定科目信息后保存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_108_001 | 首页财务指标不正确（公式非法或指标不存在/编码重复时统一抛出） |

### 11.2 修改首页财务指标

- **路径**: PUT /fms/config/finance-indicator/update
- **权限**: fms:config:finance-indicator:update
- **说明**: 修改财务指标配置，公式处理逻辑同创建。

**请求参数 (FmsFinanceIndicatorSaveReqVO)**: 同 11.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验指标存在且属于当前账套。
3. 校验公式合法、编码唯一。
4. 公式归一化与科目绑定后更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_108_001 | 首页财务指标不正确 |

### 11.3 删除首页财务指标

- **路径**: DELETE /fms/config/finance-indicator/delete
- **权限**: fms:config:finance-indicator:delete
- **说明**: 删除单个首页财务指标。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |
| id | Long | 是 | @RequestParam 必填 | 指标编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限。
2. 校验指标存在。
3. 删除指标。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_108_001 | 首页财务指标不正确 |

### 11.4 获得首页财务指标

- **路径**: GET /fms/config/finance-indicator/get
- **权限**: fms:config:finance-indicator:query
- **说明**: 获得单个财务指标详情。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| id | Long | 是 | @NotNull | 指标编号 |

**响应**: CommonResult&lt;FmsFinanceIndicatorRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 指标编号 |
| accountSetId | Long | 账套编号 |
| name | String | 指标名称 |
| code | String | 指标编码 |
| type | Integer | 取数报表类型 |
| formula | String | 指标公式 |
| sort | Integer | 展示顺序 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询并校验指标属于当前账套后返回。

### 11.5 获得首页财务指标列表

- **路径**: GET /fms/config/finance-indicator/list
- **权限**: fms:config:finance-indicator:query
- **说明**: 获得账套下全部财务指标（含停用）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;List&lt;FmsFinanceIndicatorRespVO&gt;&gt;

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套下全部指标返回。

## 12. 财务参数 (/fms/config/finance-parameter)

### 12.1 获得财务参数

- **路径**: GET /fms/config/finance-parameter/get
- **权限**: fms:config:finance-parameter:query
- **说明**: 获得账套的财务参数（科目层级、编码规则、账簿余额方向模式、结账前凭证审核要求）。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @RequestParam 必填 | 账套编号 |

**响应**: CommonResult&lt;FmsFinanceParameterRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| accountSetId | Long | 账套编号 |
| level | Integer | 科目层级 |
| subjectCodeRule | String | 科目编码规则，如 `4-2-2-2` |
| ledgerBalanceMode | Integer | 账簿余额方向模式 |
| voucherReviewRequired | Boolean | 结账前是否要求凭证审核 |

**业务逻辑**:
1. 校验账套读权限。
2. 查询账套财务参数返回。

### 12.2 更新财务参数

- **路径**: PUT /fms/config/finance-parameter/update
- **权限**: fms:config:finance-parameter:update
- **说明**: 更新财务参数；只允许扩展科目层级与各级编码长度（避免既有科目编码失效），扩展时同步改写全部科目编码。

**请求参数 (FmsFinanceParameterUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| standard | Integer | 是 | @NotNull、@InEnum(FmsAccountingStandardEnum) | 会计制度 |
| level | Integer | 是 | @NotNull、@Min(1)、@Max(8) | 科目层级 |
| subjectCodeRule | String | 是 | @NotBlank、@Size(max=64) | 科目编码规则，如 `4-2-2-2` |
| ledgerBalanceMode | Integer | 是 | @NotNull、@InEnum(FmsLedgerBalanceModeEnum) | 账簿余额方向模式 |
| voucherReviewRequired | Boolean | 是 | @NotNull | 结账前是否要求凭证审核 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限；账套必须已完成初始化。
2. 解析新旧编码规则并校验：各级长度须为 2~5 位且与层级匹配；新层级与各级长度均不得小于原值。
3. 按新旧规则的各级增量扩展全部科目编码（一级在首位后补 0，其余层级在段前补 0）。
4. 会计制度变化时同步更新账套的会计制度。
5. 更新财务参数（层级、编码规则、余额方向模式、凭证审核要求），其他领域参数保持原值。
6. 记录差异日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_100_000 | 账套不存在 |
| 1_052_100_002 | 无权访问该账套 |
| 1_052_100_005 | 账套尚未完成初始化 |
| 1_052_100_006 | 科目编码规则不正确 |
| 1_052_100_007 | 科目级次和编码长度不能调小 |
| 1_052_100_008 | 财务参数不存在 |

## 13. 初始余额 (/fms/config/initial-balance)

### 13.1 获得初始余额列表

- **路径**: GET /fms/config/initial-balance/list
- **权限**: fms:config:initial-balance:query
- **说明**: 按科目类型查询账套的初始余额列表，父级科目余额由末级科目逐级汇总。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| subjectType | Integer | 是 | @NotNull | 科目类型 |

**响应**: CommonResult&lt;List&lt;FmsInitialBalanceRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 初始余额编号（无记录时为空） |
| subjectId | Long | 科目编号 |
| subjectCode | String | 科目编码 |
| subjectName | String | 科目名称 |
| parentId | Long | 上级科目编号 |
| type | Integer | 科目类型 |
| balanceDirection | Integer | 余额方向 |
| quantityAccounting | Boolean | 是否启用数量核算 |
| quantityUnit | String | 数量单位 |
| auxiliaryAccounting | Boolean | 是否启用辅助核算 |
| openingAmount | BigDecimal | 期初金额 |
| openingQuantity | BigDecimal | 期初数量 |
| yearDebitAmount | BigDecimal | 本年累计借方金额 |
| yearDebitQuantity | BigDecimal | 本年累计借方数量 |
| yearCreditAmount | BigDecimal | 本年累计贷方金额 |
| yearCreditQuantity | BigDecimal | 本年累计贷方数量 |
| yearOpeningAmount | BigDecimal | 年初金额 |
| yearOpeningQuantity | BigDecimal | 年初数量 |
| profitLossAmount | BigDecimal | 实际损益发生额 |
| profitLossQuantity | BigDecimal | 实际损益发生数量 |
| auxiliaryConfigs | List&lt;AuxiliaryConfig&gt; | 辅助核算配置数组（auxiliaryTypeId/type/name） |
| assistBalances | List&lt;AssistBalance&gt; | 辅助核算余额数组，字段同科目级金额字段，另含 assistCombinationId 与 auxiliaries（type/typeId/itemId/name） |

**业务逻辑**:
1. 校验账套读权限。
2. 加载科目（按类型过滤）、辅助核算类别与已有余额记录。
3. 为每个科目构建余额响应（无记录时金额按 0 返回），按科目编码排序，父级排在子级之前。
4. 非末级科目金额清零后自底向上汇总：期初、年初、损益发生额按余额方向"同向取正、反向取负"累加，累计发生额按借贷分别累加。

### 13.2 保存初始余额

- **路径**: PUT /fms/config/initial-balance/save
- **权限**: fms:config:initial-balance:update
- **说明**: 整批保存科目初始余额（含辅助核算余额明细），按科目自动新增或更新。

**请求参数 (FmsInitialBalanceSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| balances | List&lt;Balance&gt; | 是 | @Valid、@NotEmpty | 科目余额数组 |

Balance 结构（继承 Amounts）：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| subjectId | Long | 是 | @NotNull | 科目编号 |
| assistBalances | List&lt;AssistBalance&gt; | 否 | @Valid | 辅助核算余额数组 |
| openingAmount | BigDecimal | 否 | @DecimalMin(0) | 期初金额（以下均为 Amounts 字段，数量/金额均不得小于 0） |
| openingQuantity | BigDecimal | 否 | @DecimalMin(0) | 期初数量 |
| yearDebitAmount | BigDecimal | 否 | @DecimalMin(0) | 本年累计借方金额 |
| yearDebitQuantity | BigDecimal | 否 | @DecimalMin(0) | 本年累计借方数量 |
| yearCreditAmount | BigDecimal | 否 | @DecimalMin(0) | 本年累计贷方金额 |
| yearCreditQuantity | BigDecimal | 否 | @DecimalMin(0) | 本年累计贷方数量 |
| yearOpeningAmount | BigDecimal | 否 | @DecimalMin(0) | 年初金额 |
| yearOpeningQuantity | BigDecimal | 否 | @DecimalMin(0) | 年初数量 |
| profitLossAmount | BigDecimal | 否 | @DecimalMin(0) | 实际损益发生额 |
| profitLossQuantity | BigDecimal | 否 | @DecimalMin(0) | 实际损益发生数量 |

AssistBalance 结构（继承 Amounts）：auxiliaryItemIds（List&lt;Long&gt;，@NotEmpty，辅助核算项目编号数组）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验账套写权限；账套已结账（当前期间晚于启用期间）时不允许修改。
2. 逐条校验科目余额：科目存在、必须为末级科目、损益类科目年初余额必须为 0。
3. 构建余额记录：未启用辅助核算的科目直接复制金额；启用辅助核算的科目逐条校验辅助核算项目与科目启用的类别完全一致，获取或创建辅助核算组合（同科目同组合仅一条明细），科目级金额由辅助核算明细汇总。
4. 按科目查询已有余额，拆分为新增与更新两组。
5. 批量插入/更新余额记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_101_000 | 科目不存在 |
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_104_001 | 初始余额只能录入末级科目 |
| 1_052_104_002 | 辅助核算项目与科目配置不一致 |
| 1_052_104_003 | 损益类科目的年初余额必须为 0 |
| 1_052_104_009 | 账套已结账，不能修改初始余额 |

### 13.3 获得试算平衡结果

- **路径**: GET /fms/config/initial-balance/trial-balance
- **权限**: fms:config:initial-balance:query
- **说明**: 按末级科目汇总期初与本年累计的借贷金额，返回是否试算平衡。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: CommonResult&lt;FmsTrialBalanceRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| openingDebitAmount | BigDecimal | 期初借方金额（余额方向为借的末级科目期初金额之和） |
| openingCreditAmount | BigDecimal | 期初贷方金额 |
| openingDifferenceAmount | BigDecimal | 期初差额 |
| yearDebitAmount | BigDecimal | 本年累计借方金额 |
| yearCreditAmount | BigDecimal | 本年累计贷方金额 |
| yearDifferenceAmount | BigDecimal | 本年累计差额 |
| balanced | Boolean | 是否平衡（期初与本年累计差额均为 0） |

**业务逻辑**:
1. 校验账套读权限。
2. 加载末级科目的余额记录。
3. 期初金额按科目余额方向分别汇总借/贷两侧；本年累计借/贷金额直接求和。
4. 计算两组差额，二者均为 0 时判定平衡。

### 13.4 导出初始余额

- **路径**: GET /fms/config/initial-balance/export-excel
- **权限**: fms:config:initial-balance:export
- **说明**: 导出全部科目（不限类型）的初始余额 Excel。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: Excel 文件流（列：科目编码、科目名称、方向、辅助核算项目、期初数量/金额、本年累计借方数量/金额、本年累计贷方数量/金额、年初数量/金额、实际损益发生数量/金额）

**业务逻辑**:
1. 校验账套读权限，查询全部科目类型的初始余额列表。
2. 将余额列表展开为 Excel 行（辅助核算余额逐行展开）。
3. 输出"财务初始余额.xlsx"。

### 13.5 获得初始余额导入模板

- **路径**: GET /fms/config/initial-balance/get-import-template
- **权限**: fms:config:initial-balance:import
- **说明**: 按当前账套科目生成初始余额导入模板；账套一月份启用时仅需录入期初余额列。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |

**响应**: Excel 文件流（同 13.4 的列结构）

**业务逻辑**:
1. 校验账套读权限，查询初始余额列表并展开为模板行（不带金额）。
2. 判断账套启用期间是否为一月，据此裁剪模板列。
3. 输出"财务初始余额导入模板.xlsx"。

### 13.6 导入初始余额

- **路径**: POST /fms/config/initial-balance/import
- **权限**: fms:config:initial-balance:import
- **说明**: 从 Excel 导入初始余额，辅助核算科目按"类别:名称/类别:名称"逐行解析，复用页面保存校验与持久化逻辑。

**请求参数 (form-data)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| accountSetId | Long | 是 | @NotNull | 账套编号 |
| file | MultipartFile | 是 | - | Excel 文件（模板由 13.5 生成） |

**响应**: CommonResult&lt;Integer&gt;（导入的科目数量）

**业务逻辑**:
1. 解析 Excel，模板格式非法时抛 `INITIAL_BALANCE_IMPORT_TEMPLATE_INVALID`。
2. 校验账套写权限与结账状态（已结账不允许导入）。
3. 逐行校验：科目编码存在、只能为末级科目、方向与科目一致、金额数量不小于 0；辅助核算科目的全零明细行跳过；同一科目与辅助核算组合不允许重复。
4. 未启用辅助核算的科目直接取行金额；启用时按"类别:名称"文本逐段解析（类别不可重复，名称或编码匹配项目），缺失或不匹配时报行级错误。
5. 非一月份启用时按借贷方向反算年初余额，反算结果小于 0 报行级错误。
6. 转换为保存请求后复用 13.2 的校验与持久化逻辑，返回导入的科目数量。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_052_101_000 | 科目不存在 |
| 1_052_102_000 | 辅助核算类别不存在 |
| 1_052_102_004 | 辅助核算项目不存在 |
| 1_052_104_001 | 初始余额只能录入末级科目 |
| 1_052_104_002 | 辅助核算项目与科目配置不一致 |
| 1_052_104_003 | 损益类科目的年初余额必须为 0 |
| 1_052_104_006 | 初始余额导入模板格式不正确 |
| 1_052_104_008 | 第 {} 行导入失败：{} |
| 1_052_104_009 | 账套已结账，不能修改初始余额 |
