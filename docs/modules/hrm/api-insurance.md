# 社保管理接口 (HrmInsuranceSchemeController / HrmInsuranceStandardController / HrmInsuranceEmployeeInfoController / HrmInsuranceMonthRecordController / HrmInsuranceMonthEmployeeRecordController)

> 提供 HRM 社保管理能力：社保方案（比例/金额两种计费类型）配置、各地区标准参保数据查询、员工参保信息维护、月度社保表生成与归档、员工月度参保项目调整与停保。

## 接口路径前缀

- /hrm/insurance/scheme  (Controller: HrmInsuranceSchemeController)
- /hrm/insurance/standard  (Controller: HrmInsuranceStandardController)
- /hrm/insurance/employee-info  (Controller: HrmInsuranceEmployeeInfoController)
- /hrm/insurance/month-record  (Controller: HrmInsuranceMonthRecordController)
- /hrm/insurance/month-employee-record  (Controller: HrmInsuranceMonthEmployeeRecordController)

通用说明：

- 社保方案类型 `type`：1-比例（按 缴纳基数 × 比例 自动计算金额）、2-金额（手工填写金额），见 `HrmInsuranceSchemeTypeEnum`
- 参保项目类型 `type`：1-养老、2-医疗、3-失业、4-工伤、5-生育、6-补充大病医疗、7-补充养老、8-残保金、9-社保自定义、10-公积金、11-公积金自定义，见 `HrmInsuranceProjectTypeEnum`
- 月度社保表状态：0-未归档（可编辑）、1-已归档（只读）
- 员工月度参保状态：0-停保、1-正常

---

## 1. 社保方案（HrmInsuranceSchemeController）

### 1.1 创建社保方案

- **路径**: POST /hrm/insurance/scheme/create
- **权限**: hrm:insurance:scheme:create
- **说明**: 创建社保方案及其参保项目，比例方案自动按基数与比例计算缴纳金额。

**请求参数 (HrmInsuranceSchemeSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 社保方案编号（创建时不传） |
| name | String | 是 | @NotBlank、@Size(max=64) | 方案名称 |
| areaId | Integer | 是 | @NotNull | 参保地区编号（城市或区县，服务端换算为城市编号） |
| householdType | String | 否 | @Size(max=64) | 户籍类型 |
| type | Integer | 是 | @NotNull、@InEnum(HrmInsuranceSchemeTypeEnum) | 方案类型：1-比例、2-金额 |
| projectList | List\<HrmInsuranceSchemeProjectSaveReqVO\> | 是 | @NotEmpty、元素 @NotNull @Valid | 社保（含公积金）项目列表 |

HrmInsuranceSchemeProjectSaveReqVO 字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 项目编号 |
| type | Integer | 是 | @NotNull、@InEnum(HrmInsuranceProjectTypeEnum) | 项目类型 |
| name | String | 是 | @NotBlank、@Size(max=64) | 项目名称 |
| baseAmount | BigDecimal | 否 | @DecimalMin("0.00")、@Digits(integer=10, fraction=2) | 缴纳基数 |
| corporateRate | BigDecimal | 否 | @DecimalMin("0.00")、@DecimalMax("100.00")、@Digits(integer=3, fraction=2) | 公司缴纳比例 |
| personalRate | BigDecimal | 否 | @DecimalMin("0.00")、@DecimalMax("100.00")、@Digits(integer=3, fraction=2) | 个人缴纳比例 |
| corporateAmount | BigDecimal | 否 | @DecimalMin("0.00")、@Digits(integer=10, fraction=2) | 公司缴纳金额 |
| personalAmount | BigDecimal | 否 | @DecimalMin("0.00")、@Digits(integer=10, fraction=2) | 个人缴纳金额 |

**响应**: CommonResult\<Long\>，返回新方案编号。

**业务逻辑**:
1. 校验方案名称唯一（重名抛错）
2. 校验项目规则：项目类型必须合法、非自定义项目类型不可重复、至少配置一个社保项目（不含公积金）
3. 校验参保地区并可换算到城市编号，否则抛错
4. 插入社保方案主表
5. 按方案类型构建项目并批量插入：比例方案按 缴纳基数×比例 自动计算公司/个人金额；金额方案保留填写金额并统一金额精度
6. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_001 | 社保方案名称已存在 |
| 1_050_500_011 | 社保方案至少需要一个社保项目 |
| 1_050_500_012 | 社保方案项目类型重复 |
| 1_050_500_024 | 参保地区必须选择城市或区县 |
| 1_050_500_007 | 社保数据不合法 |

### 1.2 更新社保方案

- **路径**: PUT /hrm/insurance/scheme/update
- **权限**: hrm:insurance:scheme:update
- **说明**: 更新社保方案；采用"删旧建新 + 迁移引用"策略，历史月度金额与项目快照保持不变。

**请求参数 (HrmInsuranceSchemeSaveReqVO)**: 同 1.1（id 必传）。

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 行锁校验原方案存在（selectByIdForUpdate）
2. 校验名称唯一、项目规则、参保地区（同创建）
3. 删除旧方案及全部项目，避免直接修改员工和月度记录已使用的方案版本
4. 以请求参数创建新方案及项目
5. 将员工参保信息和员工月度记录的 schemeId 迁移到新方案编号，历史月度金额及项目快照保持不变
6. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_000 | 社保方案不存在 |
| 1_050_500_001 | 社保方案名称已存在 |
| 1_050_500_011 | 社保方案至少需要一个社保项目 |
| 1_050_500_012 | 社保方案项目类型重复 |
| 1_050_500_024 | 参保地区必须选择城市或区县 |
| 1_050_500_007 | 社保数据不合法 |

### 1.3 删除社保方案

- **路径**: DELETE /hrm/insurance/scheme/delete
- **权限**: hrm:insurance:scheme:delete
- **说明**: 删除社保方案；被员工参保信息或月度记录使用时禁止删除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 方案编号 |

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 校验社保方案存在
2. 统计该方案在员工参保信息和员工月度社保记录中的使用人数，任一大于 0 则抛错
3. 删除方案下全部项目，再删除方案主记录
4. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_000 | 社保方案不存在 |
| 1_050_500_002 | 社保方案已被员工使用，不能删除 |

### 1.4 获得社保方案

- **路径**: GET /hrm/insurance/scheme/get
- **权限**: hrm:insurance:scheme:query
- **说明**: 获得单个社保方案详情，含项目明细、金额汇总与使用统计。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 社保方案编号 |

**响应**: CommonResult\<HrmInsuranceSchemeRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 社保方案编号 |
| name | String | 方案名称 |
| areaId | Integer | 参保地区编号 |
| areaName | String | 参保地区名（如 "广东省 深圳市"） |
| householdType | String | 户籍类型 |
| type | Integer | 方案类型：1-比例、2-金额 |
| projectList | List\<HrmInsuranceSchemeProjectRespVO\> | 全部项目 |
| socialSecurityProjectList | List\<HrmInsuranceSchemeProjectRespVO\> | 社保项目（非公积金） |
| providentFundProjectList | List\<HrmInsuranceSchemeProjectRespVO\> | 公积金项目 |
| personalInsuranceAmount | BigDecimal | 个人社保金额合计 |
| corporateInsuranceAmount | BigDecimal | 公司社保金额合计 |
| personalProvidentFundAmount | BigDecimal | 个人公积金金额合计 |
| corporateProvidentFundAmount | BigDecimal | 公司公积金金额合计 |
| useCount | Long | 使用人数（员工参保信息数） |
| monthRecordCount | Long | 历史月记录数（员工月度社保记录数） |
| createTime | LocalDateTime | 创建时间 |

HrmInsuranceSchemeProjectRespVO 字段：id、schemeId、type、name、baseAmount、corporateRate、personalRate、corporateAmount、personalAmount、createTime。

**业务逻辑**:
1. 按 id 查询方案（不存在返回 null）
2. 批量查询方案项目、员工参保信息使用人数、历史月记录数
3. 按 HrmInsuranceProjectTypeEnum 将项目拆分为社保/公积金两组，汇总四类金额，格式化地区名后拼接响应

### 1.5 获得社保方案列表

- **路径**: GET /hrm/insurance/scheme/list
- **权限**: hrm:insurance:scheme:query
- **说明**: 获得全部社保方案列表（按 id 倒序），响应结构与 1.4 完全一致。

**请求参数**: 无

**响应**: CommonResult\<List\<HrmInsuranceSchemeRespVO\>\>，每个元素结构同 1.4。

**业务逻辑**:
1. 查询全部方案（id 倒序）
2. 批量查询各方案的项目、使用人数、月记录数
3. 拼接响应（同 1.4 的组装逻辑）

### 1.6 获得社保方案精简列表

- **路径**: GET /hrm/insurance/scheme/simple-list
- **权限**: hrm:insurance:scheme:query
- **说明**: 获得社保方案精简列表（仅方案基础信息 + 地区名），用于下拉选择。

**请求参数**: 无

**响应**: CommonResult\<List\<HrmInsuranceSchemeRespVO\>\>，仅填充方案基础字段和 areaName，不含项目与统计字段。

**业务逻辑**:
1. 查询全部方案（id 倒序）
2. 转换为 RespVO 并通过 AreaUtils 格式化参保地区名

---

## 2. 标准参保数据（HrmInsuranceStandardController）

### 2.1 获得标准参保类型列表

- **路径**: GET /hrm/insurance/standard/type-list
- **权限**: hrm:insurance:scheme:query
- **说明**: 查询指定城市的标准参保方案类型（如"深户一档"），数据来自第三方平台并缓存 7 天。

**请求参数 (HrmInsuranceStandardTypeListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| areaId | Integer | 是 | @NotNull | 参保地区编号 |

**响应**: CommonResult\<List\<HrmInsuranceStandardTypeRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| code | String | 参保方案编码，如 "SS100173" |
| name | String | 参保方案名称，如 "深户一档" |

**业务逻辑**:
1. 将地区编号换算到城市并取城市名（去掉"市"/"城区"后缀），取不到返回空列表
2. 调用第三方接口（user.1renshi.com GetSocialTypeAndHouseRange）按城市名查询，超时 5 秒
3. 解析响应 JSON 中 data.SocialTypes 数组（AccountNo → code，InsuredType → name），过滤空值
4. 结果以 areaId 为 key 缓存 Redis 7 天；请求失败或响应异常时返回空列表

### 2.2 获得标准参保项目列表

- **路径**: GET /hrm/insurance/standard/project-list
- **权限**: hrm:insurance:scheme:query
- **说明**: 查询指定城市、指定参保方案编码下的标准参保项目及缴费基数/比例/金额，数据来自第三方平台并缓存 7 天。

**请求参数 (HrmInsuranceStandardProjectListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| areaId | Integer | 是 | @NotNull | 参保地区编号 |
| typeCode | String | 是 | @NotBlank | 参保方案编码（来自 2.1 的 code） |

**响应**: CommonResult\<List\<HrmInsuranceStandardProjectRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| type | Integer | 项目类型（HrmInsuranceProjectTypeEnum） |
| name | String | 项目名称 |
| baseAmount | BigDecimal | 缴纳基数 |
| corporateRate | BigDecimal | 公司缴纳比例 |
| personalRate | BigDecimal | 个人缴纳比例 |
| corporateAmount | BigDecimal | 公司缴纳金额 |
| personalAmount | BigDecimal | 个人缴纳金额 |

**业务逻辑**:
1. 城市名或 typeCode 为空时返回空列表
2. 调用第三方接口（shebao100.cn funbasequery，携带城市名与方案编码），超时 5 秒
3. 用 Jsoup 解析返回 HTML 表格行，按项目名称关键词（养老/医疗/失业/工伤/生育/大病/补充/残保/公积金）映射到项目类型枚举，无法识别的行跳过
4. 每个项目类型保留第一条，解析各列数值为基数/比例/金额
5. 结果以 areaId:typeCode 为 key 缓存 Redis 7 天；请求失败或解析异常时返回空列表

---

## 3. 员工参保信息（HrmInsuranceEmployeeInfoController）

### 3.1 获得员工参保信息

- **路径**: GET /hrm/insurance/employee-info/get
- **权限**: hrm:insurance:employee-info:query
- **说明**: 按员工编号获得其参保信息（社保/公积金账号、起缴月份、参保方案等）。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @RequestParam | 员工编号 |

**响应**: CommonResult\<HrmInsuranceEmployeeInfoRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 员工参保信息编号 |
| employeeId | Long | 员工编号 |
| firstSocialSecurity | Boolean | 是否本地首次缴纳社保 |
| firstAccumulationFund | Boolean | 是否本地首次缴纳公积金 |
| socialSecurityNumber | String | 社保账号 |
| accumulationFundNumber | String | 公积金账号 |
| socialSecurityStartMonth | LocalDateTime | 社保起缴月份 |
| schemeId | Long | 社保方案编号 |
| schemeName | String | 社保方案名称 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按员工编号查询参保信息（无则返回 null）
2. 若配置了方案编号，查询方案并回填 schemeName

### 3.2 保存员工参保信息

- **路径**: PUT /hrm/insurance/employee-info/save
- **权限**: hrm:insurance:employee-info:update
- **说明**: 新增或更新员工参保信息（按员工维度一条记录，未传 id 时按员工号复用已有记录）。

**请求参数 (HrmInsuranceEmployeeInfoSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 员工参保信息编号 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| firstSocialSecurity | Boolean | 是 | @NotNull | 是否本地首次缴纳社保 |
| firstAccumulationFund | Boolean | 是 | @NotNull | 是否本地首次缴纳公积金 |
| socialSecurityNumber | String | 否 | @Size(max=64) | 社保账号 |
| accumulationFundNumber | String | 否 | @Size(max=64) | 公积金账号 |
| socialSecurityStartMonth | LocalDateTime | 否 | - | 社保起缴月份 |
| schemeId | Long | 否 | - | 社保方案编号 |

**响应**: CommonResult\<Long\>，返回参保信息编号。

**业务逻辑**:
1. 行锁校验员工存在，并查询该员工现有参保信息
2. 若指定 id：校验参保信息存在，且其所属员工与请求一致，否则抛"员工参保信息不属于指定员工"
3. 若 schemeId 非空且与原方案不同：校验员工可参保（全职状态且在册，否则抛"员工参保状态不合法"），并校验方案存在
4. 起缴月份归一到当月 1 日；未传 id 但员工已有参保信息时复用已有记录 id
5. insertOrUpdate 保存参保信息
6. 记录操作日志（含新旧数据对比）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_100_029 | 员工参保信息不属于指定员工 |
| 1_050_500_003 | 员工参保信息不存在 |
| 1_050_500_018 | 员工参保状态不合法 |
| 1_050_500_000 | 社保方案不存在 |

### 3.3 更新员工参保方案

- **路径**: PUT /hrm/insurance/employee-info/update-scheme
- **权限**: hrm:insurance:employee-info:update
- **说明**: 单独为员工设置（或切换）参保方案，无参保信息时自动创建。

**请求参数 (HrmInsuranceEmployeeInfoUpdateSchemeReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| employeeId | Long | 是 | @NotNull | 员工编号 |
| schemeId | Long | 是 | @NotNull | 社保方案编号 |

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 行锁校验员工存在，并校验其可参保（全职状态且在册，否则抛"员工参保状态不合法"）
2. 校验新社保方案存在
3. 无参保信息时新建记录（首次缴纳标记均为 false 并写入 schemeId）；已有则仅更新 schemeId
4. 记录操作日志（含旧方案名、新方案名）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_018 | 员工参保状态不合法 |
| 1_050_500_000 | 社保方案不存在 |

---

## 4. 月度社保表（HrmInsuranceMonthRecordController）

### 4.1 创建首月社保表

- **路径**: POST /hrm/insurance/month-record/create-first
- **权限**: hrm:insurance:month-record:create
- **说明**: 创建系统内第一张月度社保表，并按员工参保信息批量生成员工月记录。

**请求参数 (HrmInsuranceMonthRecordCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| year | Integer | 是 | @NotNull、@Min(2000)、@Max(2100) | 年份 |
| month | Integer | 是 | @NotNull、@Min(1)、@Max(12) | 月份 |

**响应**: CommonResult\<Long\>，返回月度社保表编号。

**业务逻辑**:
1. 行锁校验系统内尚无任何社保表，否则抛"已存在社保表，请新建次月社保表"
2. 校验年月唯一后创建月表：标题为"%d年%d月社保表"，状态未归档，参保/停保人数与四类金额初始化为 0
3. 批量生成员工月记录：遍历所有已配置参保方案的员工资料，方案存在且有项目、员工当月可参保（非待入职、入职时间不晚于月末、离职时间不早于月初或未离职）才生成，项目按方案快照生成并计算金额
4. 为新参保员工回填社保起缴月份，并给绑定后台账号的员工发送"月度社保表生成"站内信
5. 按员工月记录重算月表汇总：参保人数、停保人数、个人/公司社保金额、个人/公司公积金金额
6. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_023 | 已存在社保表，请新建次月社保表 |
| 1_050_500_005 | 该月份社保表已存在 |

### 4.2 创建下月社保表

- **路径**: POST /hrm/insurance/month-record/create-next
- **权限**: hrm:insurance:month-record:create
- **说明**: 基于最近一张月度社保表创建次月社保表，创建前自动归档当前表。

**请求参数**: 无

**响应**: CommonResult\<Long\>，返回新月度社保表编号。

**业务逻辑**:
1. 行锁获取最近一张月度社保表，不存在则抛"月度社保表不存在"
2. 若最近月表状态为未归档，将其归档（之后不可修改）
3. 以最近月表年月 +1 创建次月社保表（年月重复会抛错）
4. 生成次月员工月记录、回填起缴月份、发送站内信（同 4.1 的生成逻辑）
5. 重算次月月表汇总并记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_004 | 月度社保表不存在 |
| 1_050_500_005 | 该月份社保表已存在 |

### 4.3 删除月度社保表

- **路径**: DELETE /hrm/insurance/month-record/delete
- **权限**: hrm:insurance:month-record:delete
- **说明**: 删除最新的月度社保表（连同其员工月记录），并将上一张表恢复为可编辑状态。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 月度社保表编号 |

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 行锁校验月表存在且未归档（已归档抛错）
2. 校验该表必须是当前最新一张，否则抛"只能删除最新的月度社保表"
3. 校验系统中至少保留一张社保表
4. 删除该月全部员工月记录，再删除月表
5. 将新的最近一张月表状态置为未归档（重新可编辑）
6. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_004 | 月度社保表不存在 |
| 1_050_500_009 | 月度社保表已归档，不能修改 |
| 1_050_500_020 | 只能删除最新的月度社保表 |
| 1_050_500_021 | 至少需要保留一张月度社保表 |

### 4.4 获得月度社保表

- **路径**: GET /hrm/insurance/month-record/get
- **权限**: hrm:insurance:month-record:query
- **说明**: 按编号获得月度社保表详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 月度社保表编号 |

**响应**: CommonResult\<HrmInsuranceMonthRecordRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 月度社保表编号 |
| year | Integer | 年份 |
| month | Integer | 月份 |
| title | String | 标题，如 "2026年7月社保表" |
| insuredEmployeeCount | Integer | 参保人数 |
| stoppedEmployeeCount | Integer | 停保人数 |
| status | Integer | 状态：0-未归档、1-已归档 |
| personalInsuranceAmount | BigDecimal | 个人社保金额 |
| personalProvidentFundAmount | BigDecimal | 个人公积金金额 |
| corporateInsuranceAmount | BigDecimal | 企业社保金额 |
| corporateProvidentFundAmount | BigDecimal | 企业公积金金额 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询月度社保表并转换为 RespVO（不存在返回 null）

### 4.5 获得最近月度社保表

- **路径**: GET /hrm/insurance/month-record/last
- **权限**: hrm:insurance:month-record:query
- **说明**: 获得最新一张月度社保表，用于判断是否可创建首月/次月表。

**请求参数**: 无

**响应**: CommonResult\<HrmInsuranceMonthRecordRespVO\>，结构同 4.4。

**业务逻辑**:
1. 查询最近一张月度社保表并转换为 RespVO（无则返回 null）

### 4.6 获得月度社保表列表

- **路径**: GET /hrm/insurance/month-record/list
- **权限**: hrm:insurance:month-record:query
- **说明**: 按年份（可选）获得月度社保表列表。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| year | Integer | 否 | @RequestParam(required=false) | 年份，不传查全部 |

**响应**: CommonResult\<List\<HrmInsuranceMonthRecordRespVO\>\>，元素结构同 4.4。

**业务逻辑**:
1. 按年份（可空）查询月度社保表列表并转换为 RespVO 列表

---

## 5. 员工月度社保（HrmInsuranceMonthEmployeeRecordController）

### 5.1 获得员工月度社保分页

- **路径**: GET /hrm/insurance/month-employee-record/page
- **权限**: hrm:insurance:month-record:query
- **说明**: 分页查询某月度社保表下的员工月记录，关联员工、部门、方案与参保项目信息。

**请求参数 (HrmInsuranceMonthEmployeeRecordPageReqVO)**：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 继承 PageParam（默认 1） | 页码 |
| pageSize | Integer | 否 | 继承 PageParam（默认 10） | 每页条数 |
| monthRecordId | Long | 是 | @NotNull | 月度社保表编号 |
| employeeId | Long | 否 | - | 员工编号 |
| employeeName | String | 否 | - | 员工姓名（模糊匹配，先转为员工编号集合） |
| schemeId | Long | 否 | - | 社保方案编号 |
| areaId | Integer | 否 | - | 参保地区编号（换算城市后匹配方案） |
| status | Integer | 否 | @InEnum(HrmInsuranceEmployeeStatusEnum) | 参保状态：0-停保、1-正常 |

**响应**: CommonResult\<PageResult\<HrmInsuranceMonthEmployeeRecordRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 记录编号 |
| monthRecordId | Long | 社保表编号 |
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| mobile | String | 手机号 |
| idNumber | String | 身份证号 |
| sex | Integer | 性别 |
| age | Integer | 年龄 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 职位名称 |
| entryStatus | Integer | 入职状态 |
| employeeStatus | Integer | 员工状态 |
| entryTime | LocalDateTime | 入职时间 |
| schemeId | Long | 社保方案编号 |
| schemeName | String | 社保方案名称 |
| areaId | Integer | 参保地区编号 |
| areaName | String | 参保地区 |
| houseType | String | 户籍类型（来自方案） |
| schemeType | Integer | 社保方案类型 |
| socialSecurityNumber | String | 个人社保号 |
| accumulationFundNumber | String | 个人公积金号 |
| year | Integer | 年份 |
| month | Integer | 月份 |
| personalInsuranceAmount | BigDecimal | 个人社保合计 |
| personalProvidentFundAmount | BigDecimal | 个人公积金合计 |
| corporateInsuranceAmount | BigDecimal | 公司社保合计 |
| corporateProvidentFundAmount | BigDecimal | 公司公积金合计 |
| status | Integer | 参保状态：0-停保、1-正常 |
| socialSecurityProjectList | List\<HrmInsuranceMonthEmployeeProjectRespVO\> | 社保项目列表 |
| providentFundProjectList | List\<HrmInsuranceMonthEmployeeProjectRespVO\> | 公积金项目列表 |
| createTime | LocalDateTime | 创建时间 |

HrmInsuranceMonthEmployeeProjectRespVO 字段：schemeProjectId（来源方案项目编号）、type、name、baseAmount、corporateRate、personalRate、corporateAmount、personalAmount。

**业务逻辑**:
1. 若传员工姓名，先按姓名查询员工编号集合，为空直接返回空页
2. 若传参保地区，先换算到城市并查询该城市下全部方案编号集合，为空直接返回空页
3. 分页查询员工月度社保记录
4. 批量查询员工、部门、社保方案、员工参保资料，拼接员工信息（姓名/工号/手机/身份证/性别/年龄/部门/职位/入职状态与时间）、方案信息（名称/地区/户籍/类型）、社保与公积金账号
5. 将记录上的项目快照拆分为社保项目列表和公积金项目列表

### 5.2 获得员工月度社保详情

- **路径**: GET /hrm/insurance/month-employee-record/get
- **权限**: hrm:insurance:month-record:query
- **说明**: 按编号获得单条员工月度社保记录详情，响应结构与 5.1 一致。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam | 员工月度社保记录编号 |

**响应**: CommonResult\<HrmInsuranceMonthEmployeeRecordRespVO\>，结构同 5.1。

**业务逻辑**:
1. 按 id 查询记录（不存在返回 null）
2. 复用 5.1 的组装逻辑拼接员工、方案、账号与项目信息

### 5.3 修改员工月度参保项目

- **路径**: PUT /hrm/insurance/month-employee-record/update
- **权限**: hrm:insurance:month-record:update
- **说明**: 修改某员工当月的参保方案与各项目基数/金额，并同步员工当前参保方案。

**请求参数 (HrmInsuranceMonthEmployeeRecordUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 员工月度社保记录编号 |
| schemeId | Long | 是 | @NotNull | 社保方案编号 |
| projects | List\<HrmInsuranceMonthEmployeeProjectUpdateReqVO\> | 是 | @NotEmpty、@Valid | 社保项目列表 |

HrmInsuranceMonthEmployeeProjectUpdateReqVO 字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| schemeProjectId | Long | 是 | @NotNull | 社保方案项目编号 |
| baseAmount | BigDecimal | 否 | @DecimalMin("0")、@Digits(integer=10, fraction=2) | 缴纳基数 |
| corporateAmount | BigDecimal | 否 | @DecimalMin("0")、@Digits(integer=10, fraction=2) | 公司缴纳金额 |
| personalAmount | BigDecimal | 否 | @DecimalMin("0")、@Digits(integer=10, fraction=2) | 个人缴纳金额 |

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 校验员工月记录存在，且所属月度社保表未归档
2. 校验新社保方案存在
3. 构建项目数据：请求中项目编号不可重复（重复抛"社保数据不合法"）；未切换方案时沿用月度项目快照，切换方案时加载新方案项目；校验请求项目均属于快照或新方案
4. 按方案类型覆盖数据并重算金额：比例方案取基数×比例，金额方案取填写金额；汇总四类金额合计
5. 更新月记录；若员工为全职在册，同步其员工参保信息的当前方案
6. 重算所属月度社保表汇总并记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_006 | 员工月度社保记录不存在 |
| 1_050_500_009 | 月度社保表已归档，不能修改 |
| 1_050_500_000 | 社保方案不存在 |
| 1_050_500_007 | 社保数据不合法 |

### 5.4 批量停止员工参保

- **路径**: PUT /hrm/insurance/month-employee-record/stop-list
- **权限**: hrm:insurance:month-record:update
- **说明**: 将一批员工月度社保记录置为停保状态，并重算月表汇总。

**请求参数 (HrmInsuranceMonthEmployeeRecordStopListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | List\<Long\> | 是 | @NotEmpty、元素 @NotNull | 员工月度社保记录编号列表 |

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 逐条校验员工月记录存在且所属月表未归档
2. 批量将记录状态更新为停保（0）
3. 按涉及的月度社保表逐个重算汇总（参保人数、停保人数、四类金额）
4. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_006 | 员工月度社保记录不存在 |
| 1_050_500_009 | 月度社保表已归档，不能修改 |

### 5.5 添加参保人员

- **路径**: POST /hrm/insurance/month-employee-record/create-list
- **权限**: hrm:insurance:month-record:update
- **说明**: 向指定月度社保表批量添加参保员工，按其当前方案生成项目快照。

**请求参数 (HrmInsuranceMonthEmployeeRecordCreateListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| monthRecordId | Long | 是 | @NotNull | 月度社保表编号 |
| employeeIds | List\<Long\> | 是 | @NotEmpty、元素 @NotNull | 员工编号列表 |

**响应**: CommonResult\<Boolean\>，固定 true。

**业务逻辑**:
1. 校验月度社保表存在且未归档，批量校验员工存在
2. 批量加载员工社保资料、对应方案及方案项目
3. 逐个员工校验：未配置有效社保方案抛"员工尚未配置有效的社保方案"；当月不符合参保条件（待入职/入职晚于月末/已离职早于月初）抛"员工在所选月份不符合参保条件"
4. 按方案项目生成项目快照并计算金额，新增或更新该员工的月记录（已存在则覆盖方案、状态与项目），并回填社保起缴月份
5. 重算月度社保表汇总
6. 记录操作日志

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_500_009 | 月度社保表已归档，不能修改 |
| 1_050_500_004 | 月度社保表不存在 |
| 1_050_500_025 | 员工尚未配置有效的社保方案 |
| 1_050_500_026 | 员工在所选月份不符合参保条件 |

### 5.6 获得本月未参保员工

- **路径**: GET /hrm/insurance/month-employee-record/uninsured-employee-list
- **权限**: hrm:insurance:month-record:query
- **说明**: 获得指定月度社保表下尚未参保、且当前配置了有效方案的员工列表。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| monthRecordId | Long | 是 | @RequestParam | 社保表编号 |

**响应**: CommonResult\<List\<HrmEmployeeRespVO\>\>，为员工模块的员工响应 VO（含姓名、工号、部门、岗位等基础字段）。

**业务逻辑**:
1. 月度社保表不存在时返回空列表
2. 查询该月状态为"正常参保"的员工编号集合
3. 加载全部员工及其参保资料，过滤出方案仍然有效的编号集合
4. 筛选同时满足以下条件的员工：本月未参保、配置了有效社保方案、当月可参保（非待入职、入职时间不晚于月末、未离职或离职时间不早于月初）
