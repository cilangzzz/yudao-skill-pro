# 线索管理接口 (CrmClueController)

> 提供 CRM 线索的全生命周期管理：线索的创建/更新/删除/查询、负责人转移、线索转化为客户，以及待跟进线索数量统计。

## 接口路径前缀

/crm/clue  (Controller: CrmClueController)

## 1. 线索基础管理

### 1.1 创建线索

- **路径**: POST /crm/clue/create
- **权限**: crm:clue:create
- **说明**: 创建一条线索，同时为负责人建立 OWNER 级数据权限，并记录操作日志。

**请求参数 (CrmClueSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 编号（更新时必传，创建时不传） |
| name | String | 是 | @NotEmpty | 线索名称 |
| contactLastTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 最后跟进时间 |
| contactNextTime | LocalDateTime | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 下次联系时间 |
| ownerUserId | Long | 是 | @NotNull | 负责人编号 |
| mobile | String | 否 | @Mobile | 手机号 |
| telephone | String | 否 | @Telephone | 电话 |
| qq | String | 否 | @Size(max = 20) | QQ |
| wechat | String | 否 | @Size(max = 255) | 微信 |
| email | String | 否 | @Email、@Size(max = 255) | 邮箱 |
| areaId | Integer | 否 | - | 地区编号 |
| detailAddress | String | 否 | - | 详细地址 |
| industryId | Integer | 否 | @DictFormat(CRM_CUSTOMER_INDUSTRY) | 所属行业（字典） |
| level | Integer | 否 | @InEnum(CrmCustomerLevelEnum) | 客户等级 |
| source | Integer | 否 | - | 客户来源 |
| description | String | 否 | @Size(max = 4096) | 客户描述 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 线索编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的线索编号 |

**业务逻辑**:
1. 校验关联数据：负责人编号非空时校验用户存在，否则抛出「用户不存在」错误。
2. 校验负责人用户存在（adminUserApi.validateUser）。
3. 将请求 VO 转换为 CrmClueDO 并插入数据库。
4. 创建数据权限：bizType 为 CRM_CLUE，负责人获得 OWNER 级别权限。
5. 记录操作日志上下文（@LogRecord 线索创建日志），返回线索编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_003 | 用户不存在（负责人校验，来自 system 模块） |

### 1.2 更新线索

- **路径**: PUT /crm/clue/update
- **权限**: crm:clue:update
- **说明**: 更新指定线索，要求当前用户为线索负责人（@CrmPermission OWNER）。

**请求参数 (CrmClueSaveReqVO)**: 同 1.1，其中 id 为更新目标线索编号（必传）。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 断言请求中线索编号（id）非空。
2. 校验线索是否存在，不存在抛出 CLUE_NOT_EXISTS。
3. 校验关联数据（负责人用户存在性）。
4. 转换为 CrmClueDO 后按 id 更新线索。
5. 将 ownerUserId 回写为旧值以避免操作日志出现「删除负责人」，并记录新旧对象 diff 操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_001_000 | 线索不存在 |
| 1_002_003_003 | 用户不存在（负责人校验，来自 system 模块） |

### 1.3 删除线索

- **路径**: DELETE /crm/clue/delete
- **权限**: crm:clue:delete
- **说明**: 删除指定线索，同时级联删除其数据权限与跟进记录，要求负责人权限（@CrmPermission OWNER）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 线索编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验线索存在，不存在抛出 CLUE_NOT_EXISTS。
2. 删除线索记录。
3. 删除该线索对应的数据权限（bizType = CRM_CLUE）。
4. 删除该线索关联的跟进记录。
5. 记录删除操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_001_000 | 线索不存在 |

### 1.4 获得线索详情

- **路径**: GET /crm/clue/get
- **权限**: crm:clue:query
- **说明**: 按编号查询单条线索详情，要求 READ 级数据权限（@CrmPermission READ）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 线索编号 |

**响应**: CommonResult&lt;CrmClueRespVO&gt;（线索不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号，主键自增 |
| name | String | 线索名称 |
| followUpStatus | Boolean | 跟进状态 |
| contactLastTime | LocalDateTime | 最后跟进时间 |
| contactLastContent | String | 最后跟进内容 |
| contactNextTime | LocalDateTime | 下次联系时间 |
| ownerUserId | Long | 负责人编号 |
| ownerUserName | String | 负责人名字 |
| ownerUserDeptName | String | 负责人部门名称 |
| transformStatus | Boolean | 转化状态 |
| customerId | Long | 客户编号 |
| customerName | String | 客户名称 |
| mobile | String | 手机号 |
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
| creator | String | 创建人 |
| creatorName | String | 创建人名字 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 按编号查询线索（数据权限校验要求 READ 级别）。
2. 批量填充关联信息：客户名称（按 customerId）。
3. 填充创建人、负责人的用户昵称及负责人所属部门名称。
4. 按地区编号格式化地区名称（AreaUtils.format）。

### 1.5 获得线索分页

- **路径**: GET /crm/clue/page
- **权限**: crm:clue:query
- **说明**: 分页查询当前用户可见的线索列表（按数据权限拼接查询条件），响应结构同 1.4。

**请求参数 (CrmCluePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | -（继承 PageParam） | 页码 |
| pageSize | Integer | 否 | -（继承 PageParam） | 每页条数 |
| name | String | 否 | - | 线索名称（模糊匹配） |
| transformStatus | Boolean | 否 | - | 转化状态 |
| telephone | String | 否 | - | 电话（模糊匹配） |
| mobile | String | 否 | - | 手机号（模糊匹配） |
| sceneType | Integer | 否 | @InEnum(CrmSceneTypeEnum) | 场景类型（null 表示全部） |
| industryId | Integer | 否 | - | 所属行业 |
| level | Integer | 否 | - | 客户等级 |
| source | Integer | 否 | - | 客户来源 |
| followUpStatus | Boolean | 否 | - | 跟进状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;CrmClueRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | CrmClueRespVO[] | 线索列表，字段同 1.4 |
| total | Long | 总条数 |

**业务逻辑**:
1. 按当前登录用户拼接数据权限查询条件（结合 sceneType 场景类型）。
2. 拼接自身查询条件：名称/电话/手机号模糊匹配，转化状态、行业、等级、来源、跟进状态精确匹配，创建时间区间过滤，按 id 倒序分页。
3. 将结果转换为 RespVO 列表并填充客户名称、负责人/创建人昵称、部门名称、地区名称等关联信息。

### 1.6 导出线索 Excel

- **路径**: GET /crm/clue/export-excel
- **权限**: crm:clue:export
- **说明**: 按与分页相同的筛选条件导出全部线索 Excel（文件名「线索.xls」），并记录导出操作日志（@ApiAccessLog EXPORT）。

**请求参数 (CrmCluePageReqVO)**: 同 1.5（pageSize 强制设为 PAGE_SIZE_NONE 以导出全部数据）。

**响应**: Excel 文件流（Content-Type 由 ExcelUtils 写入，非 CommonResult），列定义取自 CrmClueRespVO 的 @ExcelProperty 注解。

**业务逻辑**:
1. 将分页参数的 pageSize 设置为 PAGE_SIZE_NONE（不分页）。
2. 按当前登录用户的数据权限与筛选条件查询全部线索。
3. 转换为 RespVO 列表（含客户名称、负责人、创建人、地区等关联信息）。
4. 通过 ExcelUtils 写出「线索.xls」文件流。

## 2. 线索转移与转化

### 2.1 线索转移

- **路径**: PUT /crm/clue/transfer
- **权限**: crm:clue:update
- **说明**: 将线索负责人转移给新用户，原负责人可按指定权限级别加入团队或被移除，要求负责人权限（@CrmPermission OWNER）。

**请求参数 (CrmClueTransferReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | 线索编号 |
| newOwnerUserId | Long | 是 | @NotNull | 新负责人的用户编号 |
| oldOwnerPermissionLevel | Integer | 否 | @InEnum(CrmPermissionLevelEnum) | 老负责人加入团队后的权限级别；为 null 表示移除 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验线索存在，不存在抛出 CLUE_NOT_EXISTS。
2. 调用数据权限服务执行转移：新负责人获得 OWNER 权限，老负责人按 oldOwnerPermissionLevel 保留团队权限或移除。
3. 更新线索的负责人为新用户编号。
4. 记录转移操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_001_000 | 线索不存在 |
| 1_020_007_001 | 操作失败，原因：没有权限 |
| 1_020_007_003 | 操作失败，原因：转移对象已经是该负责人 |

### 2.2 线索转化为客户

- **路径**: PUT /crm/clue/transform
- **权限**: crm:clue:update
- **说明**: 将未转化的线索转化为客户，复制跟进记录到新客户，要求负责人权限（@CrmPermission OWNER）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam required | 线索编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验线索存在，不存在抛出 CLUE_NOT_EXISTS。
2. 若线索转化状态已为 true，抛出 CLUE_TRANSFORM_FAIL_ALREADY。
3. 基于线索数据创建对应客户，得到客户编号。
4. 更新线索：转化状态置为 true，并写入 customerId。
5. 查询线索的跟进记录，批量复制为新客户（bizType = CRM_CUSTOMER）下的跟进记录。
6. 记录转化操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_001_000 | 线索不存在 |
| 1_020_001_001 | 线索已经转化过了，请勿重复转化 |

## 3. 统计

### 3.1 获得分配给我的、待跟进的线索数量

- **路径**: GET /crm/clue/follow-count
- **权限**: crm:clue:query
- **说明**: 统计当前用户负责的、未跟进且未转化的线索数量，常用于工作台角标。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 待跟进线索数量 |

**业务逻辑**:
1. 按数据权限拼接查询条件，限定「我负责的」（sceneType = OWNER）场景。
2. 追加过滤条件：跟进状态为 false 且转化状态为 false。
3. 执行 count 查询并返回数量。
