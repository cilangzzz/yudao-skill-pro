# 客户管理接口 (CrmCustomerController)

> CRM 客户全生命周期管理：客户 CRUD、成交/锁定状态、公海（放入/领取/分配）、导入导出，以及客户限制配置与公海规则配置。

## 接口路径前缀

- `/crm/customer` (Controller: CrmCustomerController)
- `/crm/customer-limit-config` (Controller: CrmCustomerLimitConfigController) — 客户拥有/锁定数量上限配置
- `/crm/customer-pool-config` (Controller: CrmCustomerPoolConfigController) — 客户公海规则配置

服务层通过 `@CrmPermission` 注解在业务数据维度做读/写/负责人级权限校验；控制器层通过 `@PreAuthorize` 做菜单权限校验。以下"权限"均指 `@PreAuthorize` 值。

## 1. 客户管理（CrmCustomerController）

### 1.1 创建客户

- **路径**: POST /crm/customer/create
- **权限**: crm:customer:create
- **说明**: 创建客户，并将当前登录用户设为负责人（Owner）。

**请求参数 (CrmCustomerSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 否 | | 编号（服务端强制置空） |
| name | String | 是 | @NotEmpty | 客户名称 |
| contactNextTime | LocalDateTime | 否 | | 下次联系时间 |
| ownerUserId | Long | 是 | @NotNull | 负责人的用户编号 |
| mobile | String | 否 | @Mobile | 手机 |
| telephone | String | 否 | @Telephone | 电话 |
| qq | String | 否 | @Size(max=20) | QQ |
| wechat | String | 否 | @Size(max=255) | 微信 |
| email | String | 否 | @Email、@Size(max=255) | 邮箱 |
| areaId | Integer | 否 | | 地区编号 |
| detailAddress | String | 否 | | 详细地址 |
| industryId | Integer | 否 | 字典 CRM_CUSTOMER_INDUSTRY | 所属行业 |
| level | Integer | 否 | @InEnum(CrmCustomerLevelEnum) | 客户等级 |
| source | Integer | 否 | | 客户来源 |
| remark | String | 否 | | 备注 |

**响应**: CommonResult&lt;Long&gt; — 客户编号

**业务逻辑**:
1. 强制清空请求中的 id（保证新增语义）。
2. 校验新负责人的拥有客户数量是否到达上限（按该用户/部门的拥有客户限制配置，可选统计是否含已成交客户），超限抛 `CUSTOMER_OWNER_EXCEED_LIMIT`。
3. 转换为 DO 并初始化负责人（ownerUserId = 当前登录用户）与负责人时间，插入客户。
4. 创建数据权限：当前操作人为 OWNER 级别。
5. 记录操作日志上下文（@LogRecord）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_010 | 操作失败，超出客户数拥有上限 |

### 1.2 更新客户

- **路径**: PUT /crm/customer/update
- **权限**: crm:customer:update（服务层要求 WRITE 级数据权限）
- **说明**: 更新客户基本信息，负责人字段不可通过该接口修改。

**请求参数 (CrmCustomerSaveReqVO)**: 同 1.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 断言 id 非空；将请求中的 ownerUserId 置空，避免通过更新修改负责人。
2. 校验客户存在（不存在抛 `CUSTOMER_NOT_EXISTS`）。
3. 转换为 DO 后按 id 更新客户。
4. 恢复 ownerUserId 用于操作日志，记录新旧对象 diff 日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |

### 1.3 更新客户的成交状态

- **路径**: PUT /crm/customer/update-deal-status
- **权限**: 已认证（服务层要求 WRITE 级数据权限）
- **说明**: 标记客户成交/未成交。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| id | Long | 是 | 客户编号 |
| dealStatus | Boolean | 是 | 成交状态 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验客户存在。
2. 校验是否重复操作：状态相同抛 `CUSTOMER_UPDATE_DEAL_STATUS_FAIL`。
3. 更新客户的成交状态。
4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |
| 1_020_006_015 | 更新客户的成交状态失败，原因：已经是该状态，无需更新 |

### 1.4 删除客户

- **路径**: DELETE /crm/customer/delete
- **权限**: crm:customer:delete（服务层要求 OWNER 级数据权限）
- **说明**: 删除客户及其数据权限，删除前校验引用关系。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| id | Long | 是 | 客户编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验客户存在。
2. 校验引用：存在关联的联系人、商机或合同任一项时抛 `CUSTOMER_DELETE_FAIL_HAVE_REFERENCE`。
3. 删除客户。
4. 删除该客户的数据权限。
5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |
| 1_020_006_011 | 删除客户失败，有关联{联系人/商机/合同} |

### 1.5 获得客户详情

- **路径**: GET /crm/customer/get
- **权限**: crm:customer:query（服务层要求 READ 级数据权限）
- **说明**: 按编号获得客户详情，拼接负责人、创建人、地区、公海倒计时等展示字段。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| id | Long | 是 | 客户编号 |

**响应**: CommonResult&lt;CrmCustomerRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| id | Long | 编号 |
| name | String | 客户名称 |
| followUpStatus | Boolean | 跟进状态 |
| contactLastTime | LocalDateTime | 最后跟进时间 |
| contactLastContent | String | 最后跟进内容 |
| contactNextTime | LocalDateTime | 下次联系时间 |
| ownerUserId | Long | 负责人的用户编号 |
| ownerUserName | String | 负责人名字 |
| ownerUserDeptName | String | 负责人部门 |
| lockStatus | Boolean | 锁定状态 |
| dealStatus | Boolean | 成交状态 |
| mobile | String | 手机 |
| telephone | String | 电话 |
| qq | String | QQ |
| wechat | String | 微信 |
| email | String | 邮箱 |
| areaId | Integer | 地区编号 |
| areaName | String | 地区名称 |
| detailAddress | String | 详细地址 |
| industryId | Integer | 所属行业（字典） |
| level | Integer | 客户等级（字典） |
| source | Integer | 客户来源（字典） |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |
| creator | String | 创建人 |
| creatorName | String | 创建人名字 |
| poolDay | Long | 距离加入公海时间（天） |

**业务逻辑**:
1. 按编号查询客户（数据权限校验）。
2. 批量查询创建人、负责人的用户信息及负责人所属部门。
3. 计算距离进入公海的天数：仅当公海配置启用时，过滤掉无负责人、已成交、已锁定的客户；分别按「未成交天数」「未跟进天数」（取 ownerTime 与最后联系时间的较大者）计算剩余天数，取较小值（不小于 0）。
4. 转换为 VO 并填充地区名、创建人名、负责人名与部门名、poolDay。

### 1.6 获得客户分页

- **路径**: GET /crm/customer/page
- **权限**: crm:customer:query
- **说明**: 按条件分页查询客户（支持公海/负责人场景过滤），并拼接展示字段。

**请求参数 (CrmCustomerPageReqVO)**（继承 PageParam：pageNo、pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| pageNo | Integer | 否 | | 页码（PageParam） |
| pageSize | Integer | 否 | | 每页条数（PageParam） |
| name | String | 否 | | 客户名称 |
| mobile | String | 否 | | 手机 |
| industryId | Integer | 否 | | 所属行业 |
| level | Integer | 否 | | 客户等级 |
| source | Integer | 否 | | 客户来源 |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum) | 场景类型（null 表示全部） |
| pool | Boolean | 否 | | 是否为公海数据（null 表示非公海） |
| contactStatus | Integer | 否 | | 联系状态：1 今日需联系、2 已逾期、3 已联系 |
| followUpStatus | Boolean | 否 | | 跟进状态 |

**响应**: CommonResult&lt;PageResult&lt;CrmCustomerRespVO&gt;&gt; — 列表项字段同 1.5。

**业务逻辑**:
1. 结合查询条件与数据权限（场景类型）分页查询客户。
2. 结果为空时直接返回空分页。
3. 拼接展示数据（同 1.5 的第 2-4 步）。

### 1.7 获得待进入公海客户分页

- **路径**: GET /crm/customer/put-pool-remind-page
- **权限**: crm:customer:query
- **说明**: 分页查询即将进入公海的客户（用于提前提醒）。

**请求参数 (CrmCustomerPageReqVO)**: 同 1.6。

**响应**: CommonResult&lt;PageResult&lt;CrmCustomerRespVO&gt;&gt; — 列表项字段同 1.5。

**业务逻辑**:
1. 读取公海规则配置；配置不存在、未启用公海或未开启提前提醒（notifyEnabled=false）时返回空分页。
2. 按配置的提醒天数分页查询即将到期的客户。
3. 拼接展示数据（同 1.5 的第 2-4 步）。

### 1.8 获得待进入公海客户数量

- **路径**: GET /crm/customer/put-pool-remind-count
- **权限**: crm:customer:query
- **说明**: 统计当前用户名下即将进入公海的客户数量（角标用）。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;

**业务逻辑**:
1. 读取公海规则配置；未启用或未开启提前提醒时直接返回 0。
2. 以「非公海 + 今日需联系 + 负责人场景」条件统计待入公海客户数量。

### 1.9 获得今日需联系客户数量

- **路径**: GET /crm/customer/today-contact-count
- **权限**: crm:customer:query
- **说明**: 统计当前用户今日需联系的客户数量。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;

**业务逻辑**:
1. 按当前登录用户统计今日需联系（contactStatus = 今日需联系）的客户数量。

### 1.10 获得待跟进客户数量

- **路径**: GET /crm/customer/follow-count
- **权限**: crm:customer:query
- **说明**: 统计分配给当前用户、待跟进的客户数量。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;

**业务逻辑**:
1. 按当前登录用户统计待跟进（followUpStatus = false）的客户数量。

### 1.11 获取客户精简信息列表

- **路径**: GET /crm/customer/simple-list
- **权限**: 已认证（服务层按数据权限过滤，只包含有读权限的客户）
- **说明**: 用于前端下拉选项的精简客户列表。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;CrmCustomerRespVO&gt;&gt; — 仅返回 id、name 字段。

**业务逻辑**:
1. 构造不分页的查询请求（pageSize = PAGE_SIZE_NONE）。
2. 复用分页查询（含数据权限）获取全部可见客户。
3. 仅转换 id、name 两个精简字段返回。

### 1.12 导出客户 Excel

- **路径**: GET /crm/customer/export-excel
- **权限**: crm:customer:export
- **说明**: 按查询条件导出全部客户为 Excel（操作日志类型为导出）。

**请求参数 (CrmCustomerPageReqVO)**: 同 1.6（服务端强制不分页导出全量）。

**响应**: 二进制文件流 — `客户.xls`，列同 CrmCustomerRespVO 中 @ExcelProperty 标注字段（编号、客户名称、跟进状态、最后跟进时间、最后跟进内容、下次联系时间、负责人的用户编号、负责人名字、负责人部门、锁定状态、成交状态、手机、电话、QQ、wechat、email、地区编号、地区名称、详细地址、所属行业、客户等级、客户来源、备注、创建时间、更新时间、创建人、创建人名字）。

**业务逻辑**:
1. 强制 pageSize = PAGE_SIZE_NONE（不分页）。
2. 按条件与数据权限查询全部客户。
3. 拼接展示数据后通过 ExcelUtils 写出文件。

### 1.13 获得导入客户模板

- **路径**: GET /crm/customer/get-import-template
- **权限**: 已认证
- **说明**: 下载客户导入 Excel 模板（含两行示例数据）。

**请求参数**: 无

**响应**: 二进制文件流 — `客户导入模板.xls`，列：客户名称、手机、电话、QQ、微信、邮箱、地区（下拉选择）、详细地址、所属行业（字典下拉）、客户等级（字典下拉）、客户来源（字典下拉）、备注。

**业务逻辑**:
1. 手工构造两条示例数据（芋道、源码）。
2. 按 CrmCustomerImportExcelVO 的表头写出模板文件。

### 1.14 导入客户

- **路径**: POST /crm/customer/import
- **权限**: crm:customer:import
- **说明**: 上传 Excel 批量导入客户，支持按名称匹配做新增或更新。

**请求参数 (CrmCustomerImportReqVO)**: multipart/form-data

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| file | MultipartFile | 是 | @NotNull | Excel 文件（列同 1.13 模板） |
| updateSupport | Boolean | 是 | @NotNull | 是否支持更新（名称已存在时） |
| ownerUserId | Long | 否 | | 负责人（为 null 则客户进入公海） |

**响应**: CommonResult&lt;CrmCustomerImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| createCustomerNames | List&lt;String&gt; | 创建成功的客户名数组 |
| updateCustomerNames | List&lt;String&gt; | 更新成功的客户名数组 |
| failureCustomerNames | Map&lt;String, String&gt; | 导入失败集合，key 为客户名，value 为失败原因 |

**业务逻辑**:
1. 读取上传的 Excel 解析为导入列表，过滤名称为空的行；全部为空抛 `CUSTOMER_IMPORT_LIST_IS_EMPTY`。
2. 逐条校验客户名称非空，不满足记入失败集合。
3. 按名称查重：不存在则插入客户（ownerUserId 非空时同时创建 OWNER 数据权限），记入创建成功名单并记录新增日志。
4. 已存在时：若不允许更新（updateSupport=false），按 `CUSTOMER_NAME_EXISTS` 记入失败集合；否则更新客户信息，记入更新成功名单并记录更新日志。
5. 返回创建/更新成功与失败明细。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_012 | 导入客户数据不能为空！ |
| 1_020_006_013 | 客户名称不能为空！ |
| 1_020_006_014 | 已存在名为【{}】的客户！ |

### 1.15 转移客户

- **路径**: PUT /crm/customer/transfer
- **权限**: crm:customer:update（服务层要求 OWNER 级数据权限）
- **说明**: 将客户转移给新负责人，可同时转移名下联系人、商机、合同。

**请求参数 (CrmCustomerTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | @NotNull | 客户编号 |
| newOwnerUserId | Long | 是 | @NotNull | 新负责人的用户编号 |
| oldOwnerPermissionLevel | Integer | 否 | | 老负责人加入团队后的权限级别（null 表示移除），关联 CrmPermissionLevelEnum |
| toBizTypes | List&lt;Integer&gt; | 否 | | 同时转移的业务类型（联系人/商机/合同） |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验客户存在。
2. 校验新负责人的拥有客户数量上限（超限抛 `CUSTOMER_OWNER_EXCEED_LIMIT`）。
3. 数据权限转移：按老负责人保留级别转移 OWNER 权限，并更新客户负责人与负责人时间。
4. toBizTypes 非空时，逐个将当前老负责人名下的联系人、商机、合同转移给新负责人。
5. 记录转移操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |
| 1_020_006_010 | 操作失败，超出客户数拥有上限 |

### 1.16 锁定/解锁客户

- **路径**: PUT /crm/customer/lock
- **权限**: crm:customer:update（服务层要求 OWNER 级数据权限）
- **说明**: 切换客户的锁定状态，锁定数量受限制配置约束。

**请求参数 (CrmCustomerLockReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 是 | 无强制校验注解 | 客户编号 |
| lockStatus | Boolean | 是 | 无强制校验注解 | 目标锁定状态 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验客户存在。
2. 校验重复操作：状态与目标相同抛 `CUSTOMER_LOCK_FAIL_IS_LOCK`（锁定中）或 `CUSTOMER_UNLOCK_FAIL_IS_UNLOCK`（未锁定）。
3. 锁定时校验锁定数量上限：按用户的锁定客户限制配置取最大上限，已达上限抛 `CUSTOMER_LOCK_EXCEED_LIMIT`。
4. 更新客户锁定状态。
5. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |
| 1_020_006_007 | 锁定客户失败，它已经处于锁定状态 |
| 1_020_006_008 | 解锁客户失败，它已经处于未锁定状态 |
| 1_020_006_009 | 锁定客户失败，超出锁定规则上限 |

### 1.17 数据放入公海

- **路径**: PUT /crm/customer/put-pool
- **权限**: crm:customer:update（服务层要求 OWNER 级数据权限）
- **说明**: 将客户放入公海，清除负责人及负责人数据权限。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| id | Long | 是 | 客户编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验客户存在（不存在抛 `CUSTOMER_NOT_EXISTS`）。
2. 校验是否已是公海数据：负责人为空抛 `CUSTOMER_IN_POOL`；校验锁定状态：已锁定抛 `CUSTOMER_LOCKED_PUT_POOL_FAIL`。
3. 将客户负责人置空（更新影响行数为 0 抛 `CUSTOMER_UPDATE_OWNER_USER_FAIL`），并记录负责人变更历史。
4. 名下联系人的负责人同步置空。
5. 删除该客户的 OWNER 级数据权限（放在联系人处理后执行，保证操作期间权限仍有效）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |
| 1_020_006_004 | 客户【{}】放入公海失败，原因：已经是公海客户 |
| 1_020_006_005 | 客户【{}】放入公海失败，原因：客户已锁定 |
| 1_020_006_006 | 更新客户【{}】负责人失败, 原因：系统异常 |

### 1.18 领取公海客户

- **路径**: PUT /crm/customer/receive
- **权限**: crm:customer:receive
- **说明**: 当前登录用户从公海领取一个或多个客户。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| ids | List&lt;Long&gt; | 是 | 客户编号数组，如 1,2,3 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 批量校验客户全部存在（数量不一致抛 `CUSTOMER_NOT_EXISTS`）。
2. 校验目标负责人（当前登录用户）为有效用户。
3. 逐个校验：负责人已存在（非公海）抛 `CUSTOMER_OWNER_EXISTS`、已锁定抛 `CUSTOMER_LOCKED`、已成交抛 `CUSTOMER_ALREADY_DEAL`。
4. 校验负责人拥有客户数量上限（附加数量为本次领取数）。
5. 批量更新客户负责人与负责人时间、批量创建 OWNER 数据权限、记录负责人从公海到指定人员的变更历史。
6. 记录领取操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_006_000 | 客户不存在 |
| 1_020_006_001 | 客户【{}】已存在所属负责人 |
| 1_020_006_002 | 客户【{}】状态已锁定 |
| 1_020_006_003 | 客户已交易 |
| 1_020_006_010 | 操作失败，超出客户数拥有上限 |

### 1.19 分配公海给对应负责人

- **路径**: PUT /crm/customer/distribute
- **权限**: crm:customer:distribute
- **说明**: 管理员将公海客户分配给指定负责人（复用领取逻辑）。

**请求参数 (CrmCustomerDistributeReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| ids | List&lt;Long&gt; | 是 | @NotEmpty | 客户编号数组 |
| ownerUserId | Long | 是 | @NotNull | 目标负责人 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 复用 1.18 的 `receiveCustomer` 流程（isReceive=false）：校验存在、负责人有效、非公海/未锁定/未成交、拥有上限。
2. 批量更新负责人、创建数据权限、记录负责人变更历史。
3. 记录分配操作日志（日志中带目标负责人昵称）。

**错误码**: 同 1.18。

## 2. 客户限制配置（CrmCustomerLimitConfigController）

> 配置「拥有客户数上限」「锁定客户数上限」两类规则，按用户/部门生效。规则类型：1 拥有客户数限制、2 锁定客户数限制（CrmCustomerLimitConfigTypeEnum）。

### 2.1 创建客户限制配置

- **路径**: POST /crm/customer-limit-config/create
- **权限**: crm:customer-limit-config:create
- **说明**: 新建一条数量限制规则。

**请求参数 (CrmCustomerLimitConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| id | Long | 否 | | 编号 |
| type | Integer | 是 | @NotNull | 规则类型（1 拥有客户数限制 / 2 锁定客户数限制） |
| userIds | List&lt;Long&gt; | 否 | | 规则适用人群 |
| deptIds | List&lt;Long&gt; | 否 | | 规则适用部门 |
| maxCount | Integer | 是 | @NotNull | 数量上限 |
| dealCountEnabled | Boolean | 否 | | 成交客户是否占有拥有客户数（type = 1 时生效） |

**响应**: CommonResult&lt;Long&gt; — 配置编号

**业务逻辑**:
1. 校验适用用户、适用部门均真实存在。
2. 转换为 DO 并插入配置。
3. 记录操作日志（带规则类型名称）。

### 2.2 更新客户限制配置

- **路径**: PUT /crm/customer-limit-config/update
- **权限**: crm:customer-limit-config:update
- **说明**: 更新一条数量限制规则。

**请求参数 (CrmCustomerLimitConfigSaveReqVO)**: 同 2.1（id 必填）。

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验配置存在（不存在抛 `CUSTOMER_LIMIT_CONFIG_NOT_EXISTS`）。
2. 校验适用用户、部门存在。
3. 按 id 更新配置。
4. 记录新旧对象 diff 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_012_001 | 客户限制配置不存在 |

### 2.3 删除客户限制配置

- **路径**: DELETE /crm/customer-limit-config/delete
- **权限**: crm:customer-limit-config:delete
- **说明**: 删除一条数量限制规则。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| id | Long | 是 | 编号 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 校验配置存在。
2. 删除配置。
3. 记录操作日志（带规则类型名称）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_020_012_001 | 客户限制配置不存在 |

### 2.4 获得客户限制配置

- **路径**: GET /crm/customer-limit-config/get
- **权限**: crm:customer-limit-config:query
- **说明**: 按编号获得限制配置详情，含适用用户/部门明细。

**请求参数**: Query 参数（无 VO）

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| id | Long | 是 | 编号 |

**响应**: CommonResult&lt;CrmCustomerLimitConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| id | Long | 编号 |
| type | Integer | 规则类型 |
| userIds | List&lt;Long&gt; | 规则适用人群 |
| deptIds | List&lt;Long&gt; | 规则适用部门 |
| maxCount | Integer | 数量上限 |
| dealCountEnabled | Boolean | 成交客户是否占有拥有客户数 |
| users | List&lt;AdminUserRespDTO&gt; | 规则适用人群明细 |
| depts | List&lt;DeptRespDTO&gt; | 规则适用部门明细 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询配置。
2. 批量查询适用用户与部门详情并填充进 VO。

### 2.5 获得客户限制配置分页

- **路径**: GET /crm/customer-limit-config/page
- **权限**: crm:customer-limit-config:query
- **说明**: 分页查询限制配置列表，含适用用户/部门明细。

**请求参数 (CrmCustomerLimitConfigPageReqVO)**（继承 PageParam：pageNo、pageSize）:

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| pageNo | Integer | 否 | 页码 |
| pageSize | Integer | 否 | 每页条数 |
| type | Integer | 否 | 规则类型 |

**响应**: CommonResult&lt;PageResult&lt;CrmCustomerLimitConfigRespVO&gt;&gt; — 字段同 2.4。

**业务逻辑**:
1. 按条件分页查询配置；结果为空直接返回。
2. 批量查询各条配置的适用用户与部门详情并填充。

## 3. 客户公海配置（CrmCustomerPoolConfigController）

> 全局唯一的公海规则：是否启用公海、未跟进/未成交放入公海天数、是否提前提醒及提醒天数。

### 3.1 获取客户公海规则设置

- **路径**: GET /crm/customer-pool-config/get
- **权限**: crm:customer-pool-config:query
- **说明**: 获取全局唯一的公海规则配置。

**请求参数**: 无

**响应**: CommonResult&lt;CrmCustomerPoolConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| enabled | Boolean | 是否启用客户公海 |
| contactExpireDays | Integer | 未跟进放入公海天数 |
| dealExpireDays | Integer | 未成交放入公海天数 |
| notifyEnabled | Boolean | 是否开启提前提醒 |
| notifyDays | Integer | 提前提醒天数 |

**业务逻辑**:
1. 查询全局唯一配置记录。
2. 转换为 VO 返回（不存在时各字段为 null）。

### 3.2 更新客户公海规则设置

- **路径**: PUT /crm/customer-pool-config/save
- **权限**: crm:customer-pool-config:update
- **说明**: 保存公海规则，存在则更新，不存在则插入。

**请求参数 (CrmCustomerPoolConfigSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|-----|-----|---------|-----|
| enabled | Boolean | 是 | @NotNull | 是否启用客户公海 |
| contactExpireDays | Integer | 条件必填 | @AssertTrue（enabled=true 时必填） | 未跟进放入公海天数 |
| dealExpireDays | Integer | 条件必填 | @AssertTrue（enabled=true 时必填） | 未成交放入公海天数 |
| notifyEnabled | Boolean | 否 | | 是否开启提前提醒 |
| notifyDays | Integer | 条件必填 | @AssertTrue（notifyEnabled=true 时必填） | 提前提醒天数 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**:
1. 查询现有配置。
2. 已存在则按原 id 更新。
3. 不存在则插入新配置。
4. 记录操作日志（区分新增/更新）。

## 附：客户域错误码汇总（ErrorCodeConstants）

| 错误码 | 常量 | 说明 |
|-------|-----|-----|
| 1_020_006_000 | CUSTOMER_NOT_EXISTS | 客户不存在 |
| 1_020_006_001 | CUSTOMER_OWNER_EXISTS | 客户【{}】已存在所属负责人 |
| 1_020_006_002 | CUSTOMER_LOCKED | 客户【{}】状态已锁定 |
| 1_020_006_003 | CUSTOMER_ALREADY_DEAL | 客户已交易 |
| 1_020_006_004 | CUSTOMER_IN_POOL | 客户【{}】放入公海失败，原因：已经是公海客户 |
| 1_020_006_005 | CUSTOMER_LOCKED_PUT_POOL_FAIL | 客户【{}】放入公海失败，原因：客户已锁定 |
| 1_020_006_006 | CUSTOMER_UPDATE_OWNER_USER_FAIL | 更新客户【{}】负责人失败, 原因：系统异常 |
| 1_020_006_007 | CUSTOMER_LOCK_FAIL_IS_LOCK | 锁定客户失败，它已经处于锁定状态 |
| 1_020_006_008 | CUSTOMER_UNLOCK_FAIL_IS_UNLOCK | 解锁客户失败，它已经处于未锁定状态 |
| 1_020_006_009 | CUSTOMER_LOCK_EXCEED_LIMIT | 锁定客户失败，超出锁定规则上限 |
| 1_020_006_010 | CUSTOMER_OWNER_EXCEED_LIMIT | 操作失败，超出客户数拥有上限 |
| 1_020_006_011 | CUSTOMER_DELETE_FAIL_HAVE_REFERENCE | 删除客户失败，有关联{} |
| 1_020_006_012 | CUSTOMER_IMPORT_LIST_IS_EMPTY | 导入客户数据不能为空！ |
| 1_020_006_013 | CUSTOMER_CREATE_NAME_NOT_NULL | 客户名称不能为空！ |
| 1_020_006_014 | CUSTOMER_NAME_EXISTS | 已存在名为【{}】的客户！ |
| 1_020_006_015 | CUSTOMER_UPDATE_DEAL_STATUS_FAIL | 更新客户的成交状态失败，原因：已经是该状态，无需更新 |
| 1_020_012_001 | CUSTOMER_LIMIT_CONFIG_NOT_EXISTS | 客户限制配置不存在 |
