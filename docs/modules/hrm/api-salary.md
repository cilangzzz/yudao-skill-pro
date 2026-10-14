# 薪资管理接口 (HrmSalaryConfigController 等)

> 提供 HRM 薪资管理全流程接口：计薪配置、薪资组、薪资项、计税规则、调薪模板等基础设置，员工定薪/调薪与导入，月度工资表核算，以及工资条模板、发放与查询。

## 接口路径前缀

| 前缀 | Controller |
|-----|-----------|
| /hrm/salary/config | HrmSalaryConfigController |
| /hrm/salary/group | HrmSalaryGroupController |
| /hrm/salary/option | HrmSalaryOptionController |
| /hrm/salary/tax-rule | HrmSalaryTaxRuleController |
| /hrm/salary/change-template | HrmSalaryChangeTemplateController |
| /hrm/salary/employee-info | HrmSalaryEmployeeInfoController |
| /hrm/salary/change-record | HrmSalaryChangeRecordController |
| /hrm/salary/month-record | HrmSalaryMonthRecordController |
| /hrm/salary/month-employee-record | HrmSalaryMonthEmployeeRecordController |
| /hrm/salary/slip-template | HrmSalarySlipTemplateController |
| /hrm/salary/slip-send-record | HrmSalarySlipSendRecordController |
| /hrm/salary/slip | HrmSalarySlipController |

---

## 1. 计薪配置（HrmSalaryConfigController）

### 1.1 创建薪资配置

- **路径**: POST /hrm/salary/config/create
- **权限**: `hrm:salary:config:update`
- **说明**: 初始化计薪配置，创建后自动生成开始月份的工资表（每个租户仅允许一条配置）

**请求参数 (HrmSalaryConfigCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| cycleStartDay | Integer | 是 | @NotNull、@Min(1)、@Max(31) | 计薪周期开始日 |
| socialSecurityMonthType | Integer | 是 | @NotNull、@InEnum(社保对应月份类型枚举) | 社保对应月份类型 |
| startYear | Integer | 是 | @NotNull、@Min(2000)、@Max(2100) | 工资开始年份 |
| startMonth | Integer | 是 | @NotNull、@Min(1)、@Max(12) | 工资开始月份 |

**响应**: CommonResult&lt;Long&gt; —— 配置编号

**业务逻辑**: 1. 校验计薪配置不存在，已存在则报「薪资配置已存在」；2. 创建配置，计薪周期结束日由开始日推导（开始日为 1 则结束日为 31，否则为开始日 - 1）；3. 按开始年月创建首张月度工资表。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_022 | 薪资配置已存在 |
| 1_050_400_009 | 该月份工资表已存在 |

### 1.2 更新薪资配置

- **路径**: PUT /hrm/salary/config/update
- **权限**: `hrm:salary:config:update`
- **说明**: 仅允许修改社保对应月份类型，支持操作日志字段对比

**请求参数 (HrmSalaryConfigUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| socialSecurityMonthType | Integer | 是 | @NotNull、@InEnum | 社保对应月份类型 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验计薪配置存在；2. 仅更新社保对应月份类型；3. 记录操作日志并对比新旧社保对应月份。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_000 | 薪资配置不存在 |

### 1.3 获得薪资配置

- **路径**: GET /hrm/salary/config/get
- **权限**: `hrm:salary:config:query`
- **说明**: 查询当前租户的计薪配置

**请求参数**: 无

**响应**: CommonResult&lt;HrmSalaryConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 配置编号 |
| cycleStartDay | Integer | 计薪周期开始日 |
| cycleEndDay | Integer | 计薪周期结束日 |
| socialSecurityMonthType | Integer | 社保对应月份类型 |
| startYear | Integer | 工资开始年份 |
| startMonth | Integer | 工资开始月份 |
| createTime | LocalDateTime | 创建时间 |

---

## 2. 薪资组（HrmSalaryGroupController）

### 2.1 创建薪资组

- **路径**: POST /hrm/salary/group/create
- **权限**: `hrm:salary:group:create`
- **说明**: 新建薪资组，绑定计税规则并圈定适用部门/员工

**请求参数 (HrmSalaryGroupSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | - | 薪资组编号 |
| name | String | 是 | @NotBlank、@Size(max=64) | 薪资组名称 |
| taxRuleId | Long | 是 | @NotNull | 计税规则编号 |
| deptIds | List&lt;Long&gt; | 否 | @AssertTrue：与员工不能同时为空 | 适用部门编号列表 |
| employeeIds | List&lt;Long&gt; | 否 | 同上 | 适用员工编号列表 |

**响应**: CommonResult&lt;Long&gt; —— 薪资组编号

**业务逻辑**: 1. 校验薪资组名称唯一、计税规则存在；2. 校验适用范围：所选部门（含上下级部门）未归属其他薪资组、所选员工存在且未归属其他薪资组；3. 创建薪资组并填充默认值（月计薪标准 21.75、转正/调薪月规则）；4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_002 | 薪资组名称已存在 |
| 1_050_400_020 | 所选员工已属于其他薪资组 |
| 1_050_400_021 | 所选部门或其上下级部门已属于其他薪资组 |
| 1_050_400_005 | 计税规则不存在 |

### 2.2 修改薪资组

- **路径**: PUT /hrm/salary/group/update
- **权限**: `hrm:salary:group:update`
- **说明**: 修改薪资组基础信息与适用范围

**请求参数**: 同 HrmSalaryGroupSaveReqVO（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验薪资组存在、名称唯一、计税规则存在及适用范围不与其他薪资组冲突；2. 更新薪资组并填充默认值；3. 记录操作日志并对比修改前后差异。

**错误码**: 同 2.1，另加：

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_001 | 薪资组不存在 |

### 2.3 删除薪资组

- **路径**: DELETE /hrm/salary/group/delete
- **权限**: `hrm:salary:group:delete`
- **说明**: 按编号删除薪资组

**请求参数**: id（Long，Query 参数，薪资组编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验薪资组存在；2. 删除薪资组；3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_001 | 薪资组不存在 |

### 2.4 获得薪资组

- **路径**: GET /hrm/salary/group/get
- **权限**: `hrm:salary:group:query`
- **说明**: 查询单个薪资组，拼接计税规则、部门、员工名称

**请求参数**: id（Long，Query 参数，薪资组编号）

**响应**: CommonResult&lt;HrmSalaryGroupRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 薪资组编号 |
| name | String | 薪资组名称 |
| salaryStandard | BigDecimal | 月计薪标准 |
| changeRule | String | 转正、调薪月规则 |
| taxRuleId | Long | 计税规则编号 |
| taxRuleName | String | 计税规则名称（拼接） |
| deptIds | List&lt;Long&gt; | 适用部门编号列表 |
| deptNames | List&lt;String&gt; | 适用部门名称列表（拼接） |
| employeeIds | List&lt;Long&gt; | 适用员工编号列表 |
| employeeNames | List&lt;String&gt; | 适用员工名称列表（拼接） |
| createTime | LocalDateTime | 创建时间 |

### 2.5 获得薪资组分页

- **路径**: GET /hrm/salary/group/page
- **权限**: `hrm:salary:group:query`
- **说明**: 分页查询薪资组，响应结构与 2.4 相同（拼接字段一致）

**请求参数 (HrmSalaryGroupPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo | Integer | 否 | 分页参数 | 页码 |
| pageSize | Integer | 否 | 分页参数 | 每页条数 |
| name | String | 否 | - | 薪资组名称（模糊） |
| taxRuleId | Long | 否 | - | 计税规则编号 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalaryGroupRespVO&gt;&gt;

### 2.6 获得薪资组精简列表

- **路径**: GET /hrm/salary/group/simple-list
- **权限**: `hrm:salary:group:query`
- **说明**: 下拉选择用精简列表，仅返回 id、name、taxRuleId

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmSalaryGroupRespVO&gt;&gt;（仅含 id/name/taxRuleId）

---

## 3. 薪资项（HrmSalaryOptionController）

### 3.1 创建薪资项

- **路径**: POST /hrm/salary/option/create
- **权限**: `hrm:salary:option:create`
- **说明**: 在指定分类下新增企业自定义薪资项

**请求参数 (HrmSalaryOptionSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| parentCode | Integer | 是 | @NotNull | 父薪资项（分类）编码 |
| name | String | 是 | @NotBlank、@Size(max=64) | 薪资项名称 |
| remark | String | 否 | @Size(max=255) | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 薪资项编号

**业务逻辑**: 1. 校验薪资项分类（必须是标准目录下企业可选的根分类且已启用）；2. 在企业自定义编码高位区间生成编码（含已逻辑删除记录，避免与标准目录编码碰撞），继承分类的类型、计税、参与计算属性并默认启用、显示；3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_028 | 薪资项分类不存在或不可用 |

### 3.2 更新薪资项启用状态

- **路径**: PUT /hrm/salary/option/update-enabled
- **权限**: `hrm:salary:option:update`
- **说明**: 启用/停用薪资项

**请求参数 (HrmSalaryOptionUpdateEnabledReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 薪资项编号 |
| enabled | Boolean | 是 | @NotNull | 是否启用 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验薪资项存在；2. 系统默认项不允许修改启用状态；3. 更新启用状态并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_003 | 薪资项不存在 |
| 1_050_400_029 | 标准薪资项不允许修改或删除 |

### 3.3 更新薪资项显示状态

- **路径**: PUT /hrm/salary/option/update-visible
- **权限**: `hrm:salary:option:update`
- **说明**: 控制薪资项是否在工资表中显示

**请求参数 (HrmSalaryOptionUpdateVisibleReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 薪资项编号 |
| visible | Boolean | 是 | @NotNull | 是否显示 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验薪资项存在；2. 非系统默认项（自定义项）不允许修改显示状态；3. 更新显示状态并记录操作日志。

**错误码**: 同 3.2

### 3.4 删除薪资项

- **路径**: DELETE /hrm/salary/option/delete
- **权限**: `hrm:salary:option:delete`
- **说明**: 删除企业自定义薪资项

**请求参数**: id（Long，Query 参数，薪资项编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验薪资项存在；2. 系统默认项和关联标准目录的标准薪资项不允许物理删除；3. 删除并记录操作日志。

**错误码**: 同 3.2

### 3.5 同步标准薪资项

- **路径**: PUT /hrm/salary/option/sync
- **权限**: `hrm:salary:option:update`
- **说明**: 按标准薪资项目录增量同步系统薪资项

**请求参数**: 无

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 查询标准薪资项目录（为空直接返回）；2. 对比现有薪资项计算待新增/待更新集合，若编码已被历史或企业自定义数据占用则报错；3. 批量新增与更新，并保留租户自行维护的启用、显示状态。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_029 | 薪资项编码 {} 已被历史或自定义数据占用，请先完成数据迁移 |

### 3.6 获得薪资项列表

- **路径**: GET /hrm/salary/option/list
- **权限**: `hrm:salary:option:query`
- **说明**: 管理端查询全部薪资项（含停用与隐藏）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmSalaryOptionRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 薪资项编号 |
| code | Integer | 薪资项编码 |
| parentCode | Integer | 父薪资项编码 |
| name | String | 薪资项名称 |
| remark | String | 备注 |
| systemFlag | Boolean | 是否系统默认项 |
| type | Integer | 薪资项类型 |
| taxEnabled | Boolean | 是否计税 |
| visible | Boolean | 是否显示 |
| calculateEnabled | Boolean | 是否参与计算 |
| enabled | Boolean | 是否启用 |
| templateId | Long | 标准薪资项目录编号 |
| createTime | LocalDateTime | 创建时间 |

### 3.7 获得薪资项精简列表

- **路径**: GET /hrm/salary/option/simple-list
- **权限**: `hrm:salary:option:query`
- **说明**: 只包含已启用的薪资项，过滤所属分类已停用的项；`adjustable=true` 时仅保留可调薪分类下的薪资项

**请求参数**: adjustable（Boolean，Query 参数，可选，是否可调薪）

**响应**: CommonResult&lt;List&lt;HrmSalaryOptionRespVO&gt;&gt;（仅含 code/parentCode/name/calculateEnabled）

---

## 4. 计税规则（HrmSalaryTaxRuleController）

### 4.1 创建计税规则

- **路径**: POST /hrm/salary/tax-rule/create
- **权限**: `hrm:salary:tax-rule:create`
- **说明**: 新建计税规则

**请求参数 (HrmSalaryTaxRuleSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | - | 计税规则编号 |
| name | String | 是 | @NotBlank、@Size(max=64) | 计税规则名称 |
| type | Integer | 是 | @NotNull、@InEnum(计税类型枚举) | 计税类型 |
| taxEnabled | Boolean | 是 | @NotNull | 是否计税 |
| threshold | BigDecimal | 条件必填 | @DecimalMin(0.00)、@Digits(10,2)、@AssertTrue：非不计税类型时不能为空 | 起征阈值 |
| decimalScale | Integer | 条件必填 | @Min(0)、@Max(4)、@AssertTrue：非不计税类型时不能为空 | 小数位数 |
| cycleType | Integer | 条件必填 | @InEnum(计税周期类型枚举)、@AssertTrue：工资薪金所得税时不能为空 | 计税周期类型 |

**响应**: CommonResult&lt;Long&gt; —— 计税规则编号

**业务逻辑**: 1. 校验计税规则名称唯一；2. 创建计税规则；3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_023 | 计税规则名称已存在 |

### 4.2 修改计税规则

- **路径**: PUT /hrm/salary/tax-rule/update
- **权限**: `hrm:salary:tax-rule:update`
- **说明**: 修改计税规则

**请求参数**: 同 HrmSalaryTaxRuleSaveReqVO（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验计税规则存在且名称唯一；2. 更新计税规则；3. 记录操作日志并对比修改前后差异。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_005 | 计税规则不存在 |
| 1_050_400_023 | 计税规则名称已存在 |

### 4.3 删除计税规则

- **路径**: DELETE /hrm/salary/tax-rule/delete
- **权限**: `hrm:salary:tax-rule:delete`
- **说明**: 删除未被薪资组使用的计税规则

**请求参数**: id（Long，Query 参数，计税规则编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验计税规则存在且未被任何薪资组使用；2. 删除计税规则；3. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_005 | 计税规则不存在 |
| 1_050_400_027 | 计税规则已被薪资组使用，不能删除 |

### 4.4 获得计税规则

- **路径**: GET /hrm/salary/tax-rule/get
- **权限**: `hrm:salary:tax-rule:query`
- **说明**: 按编号查询计税规则

**请求参数**: id（Long，Query 参数，计税规则编号）

**响应**: CommonResult&lt;HrmSalaryTaxRuleRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 计税规则编号 |
| name | String | 计税规则名称 |
| type | Integer | 计税类型 |
| taxEnabled | Boolean | 是否计税 |
| threshold | BigDecimal | 起征阈值 |
| decimalScale | Integer | 小数位数 |
| cycleType | Integer | 计税周期类型 |
| usedGroupCount | Long | 使用该规则的薪资组数量（仅 list 接口填充） |
| createTime | LocalDateTime | 创建时间 |

### 4.5 获得计税规则列表

- **路径**: GET /hrm/salary/tax-rule/list
- **权限**: `hrm:salary:tax-rule:query`
- **说明**: 查询全部计税规则，并统计各规则被薪资组使用的数量

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmSalaryTaxRuleRespVO&gt;&gt;（usedGroupCount 为使用该规则的薪资组数）

---

## 5. 调薪模板（HrmSalaryChangeTemplateController）

### 5.1 创建调薪模板

- **路径**: POST /hrm/salary/change-template/create
- **权限**: `hrm:salary:change-template:create`
- **说明**: 新建调薪模板，可指定调薪项集合与是否默认

**请求参数 (HrmSalaryChangeTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | - | 调薪模板编号 |
| name | String | 是 | @NotBlank、@Size(max=64) | 模板名称 |
| defaultStatus | Boolean | 是 | @NotNull | 是否默认模板 |
| options | List&lt;HrmSalaryChangeOptionVO&gt; | 是 | @Valid、@NotEmpty | 调薪项配置 |

HrmSalaryChangeOptionVO:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| code | Integer | 是 | @NotNull | 薪资项编码 |
| name | String | 否 | - | 薪资项名称（服务端以薪资项名称快照保存） |

**响应**: CommonResult&lt;Long&gt; —— 模板编号

**业务逻辑**: 1. 校验调薪项编码必须存在于可调薪薪资项中且不重复，并保存名称快照；2. 若设为默认模板，清理其他模板的默认标记；3. 创建调薪模板。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_800_004 | 调薪模板包含无效或重复的薪资项 |

### 5.2 更新调薪模板

- **路径**: PUT /hrm/salary/change-template/update
- **权限**: `hrm:salary:change-template:update`
- **说明**: 修改调薪模板

**请求参数**: 同 HrmSalaryChangeTemplateSaveReqVO（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验模板存在并校验调薪项；2. 若设为默认模板，清理其他模板（排除自身）的默认标记；3. 更新调薪模板。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_800_002 | 调薪模板不存在 |
| 1_050_800_004 | 调薪模板包含无效或重复的薪资项 |

### 5.3 删除调薪模板

- **路径**: DELETE /hrm/salary/change-template/delete
- **权限**: `hrm:salary:change-template:delete`
- **说明**: 删除非默认的调薪模板

**请求参数**: id（Long，Query 参数，调薪模板编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验模板存在且不是默认模板；2. 删除调薪模板。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_800_002 | 调薪模板不存在 |
| 1_050_800_003 | 默认调薪模板不能删除 |

### 5.4 获得调薪模板

- **路径**: GET /hrm/salary/change-template/get
- **权限**: `hrm:salary:change-template:query`
- **说明**: 按编号查询调薪模板

**请求参数**: id（Long，Query 参数，调薪模板编号）

**响应**: CommonResult&lt;HrmSalaryChangeTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 调薪模板编号 |
| name | String | 模板名称 |
| defaultStatus | Boolean | 是否默认模板 |
| options | List&lt;HrmSalaryChangeOptionVO&gt; | 调薪项配置 |
| createTime | LocalDateTime | 创建时间 |

### 5.5 获得调薪模板列表

- **路径**: GET /hrm/salary/change-template/list
- **权限**: `hrm:salary:change-template:query` 或 `hrm:salary:employee-info:query`
- **说明**: 查询全部调薪模板（调薪页面复用）

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmSalaryChangeTemplateRespVO&gt;&gt;

---

## 6. 员工薪资信息（HrmSalaryEmployeeInfoController）

### 6.1 获得员工薪资信息分页

- **路径**: GET /hrm/salary/employee-info/page
- **权限**: `hrm:salary:employee-info:query`
- **说明**: 以员工档案为主表分页查询薪资档案（含未定薪员工）

**请求参数 (HrmSalaryEmployeeInfoPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| employeeId | Long | 否 | - | 员工编号 |
| employeeIds | List&lt;Long&gt; | 否 | - | 员工编号列表 |
| changeType | Integer | 否 | - | 调整类型（薪资状态） |
| search | String | 否 | - | 员工姓名或工号 |
| deptId | Long | 否 | - | 部门编号 |
| postName | String | 否 | - | 岗位名称 |
| status | Integer | 否 | - | 员工状态 |
| entryStatus | Integer | 否 | - | 入职状态 |
| statusCategory | Integer | 否 | - | 员工状态页签 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalaryEmployeeInfoRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 员工薪资编号 |
| employeeId | Long | 员工编号 |
| employeeName | String | 员工姓名 |
| jobNumber | String | 工号 |
| mobile | String | 手机号 |
| deptId | Long | 部门编号 |
| deptName | String | 部门名称 |
| postName | String | 岗位名称 |
| entryStatus | Integer | 入职状态 |
| status | Integer | 员工状态 |
| entryTime | LocalDateTime | 入职时间 |
| regularTime | LocalDateTime | 转正时间 |
| changeReason | Integer | 调整原因（字典） |
| effectTime | LocalDateTime | 生效日期 |
| changeType | Integer | 薪资状态（未定薪/已定薪/已调薪） |
| probationSalary | BigDecimal | 试用期工资 |
| regularSalary | BigDecimal | 正式工资 |
| remark | String | 备注 |
| salaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 薪资项列表 |
| probationSalaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 试用期薪资项列表 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 将薪资查询条件转换为员工查询条件：未指定薪资状态时仅使用请求中的员工范围；查询「未定薪」时用已定薪员工列表做排除；其他状态取已定薪员工与请求员工范围的交集；2. 查询员工分页；3. 批量拼接薪资档案、部门等信息，无薪资档案时薪资状态为「未定薪」且薪资项为空。

**错误码**: 无（数据级错误不抛出）

### 6.2 获得员工薪资信息状态数量

- **路径**: GET /hrm/salary/employee-info/status-count
- **权限**: `hrm:salary:employee-info:query`
- **说明**: 按员工状态页签统计数量（用于页签角标）

**请求参数**: 同 HrmSalaryEmployeeInfoPageReqVO

**响应**: CommonResult&lt;List&lt;HrmEmployeeStatusCountRespVO&gt;&gt;（status + count）

**业务逻辑**: 1. 转换查询条件时忽略当前状态页签，保证各页签数量口径一致；2. 按员工状态页签（在职、待入职、待离职等）统计数量。

### 6.3 获得员工薪资信息

- **路径**: GET /hrm/salary/employee-info/get
- **权限**: `hrm:salary:employee-info:query`
- **说明**: 查询单个员工的薪资档案

**请求参数**: employeeId（Long，Query 参数，员工编号）

**响应**: CommonResult&lt;HrmSalaryEmployeeInfoRespVO&gt;（结构同 6.1；员工不存在时返回 null）

### 6.4 获得最早调薪生效日期

- **路径**: GET /hrm/salary/employee-info/get-adjustment-min-effect-date
- **权限**: `hrm:salary:employee-info:update`
- **说明**: 返回允许的最早调薪生效日期（最近工资表所在月 1 日）

**请求参数**: 无

**响应**: CommonResult&lt;LocalDate&gt;（无工资表时为 null）

### 6.5 修改员工薪资信息（定薪/调薪）

- **路径**: PUT /hrm/salary/employee-info/update
- **权限**: `hrm:salary:employee-info:update`
- **说明**: 对单个员工定薪或调薪，可编辑待生效/已取消记录

**请求参数 (HrmSalaryEmployeeInfoUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | - | 定薪/调薪记录编号；编辑待生效或已取消记录时传入 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| recordType | Integer | 是 | @NotNull、@InEnum(记录类型枚举) | 记录类型（定薪/调薪） |
| changeReason | Integer | 是 | @NotNull、@InEnum(调整原因枚举) | 调整原因 |
| effectTime | LocalDateTime | 否 | 调薪时必填且不早于最近工资月份 | 生效日期 |
| remark | String | 否 | @Size(max=500) | 备注 |
| salaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 否 | @Valid | 薪资项列表 |
| probationSalaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 否 | @Valid | 试用期薪资项列表 |

**响应**: CommonResult&lt;Long&gt; —— 定薪/调薪记录编号

**业务逻辑**: 1. 校验员工存在及待编辑记录（编辑时记录的员工与类型必须匹配，已生效的调薪记录不可编辑）；2. 业务校验：调薪时薪资档案必须存在、定薪时不能存在未取消的调薪记录、员工存在待生效记录时禁止再次提交、调薪生效日期不能早于最近工资月份；3. 标准化薪资项（编码必须有效、金额非负且最多 2 位小数），调薪时与员工原薪资项合并，并按参与计算的薪资项汇总正式/试用期工资总额；4. 确定生效日期：编辑定薪保留原生效日期，首次定薪未指定时从当月首日生效，调薪取当日开始时间；5. 非待生效记录立即更新员工当前薪资档案；6. 创建或更新定薪/调薪记录（待生效或已生效状态）并记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_006 | 员工薪资信息不存在 |
| 1_050_400_014 | 薪资数据不合法 |
| 1_050_400_016 | 员工存在待生效的定薪调薪记录 |
| 1_050_400_017 | 当前定薪调薪记录状态不允许执行该操作 |
| 1_050_400_030 | 调薪生效日期不能为空，且不能早于最近工资月份 |

### 6.6 批量调薪

- **路径**: PUT /hrm/salary/employee-info/update-list
- **权限**: `hrm:salary:employee-info:update`
- **说明**: 按金额或百分比对一批员工（部门或指定员工）统一调薪

**请求参数 (HrmSalaryEmployeeInfoUpdateListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| employeeIds | List&lt;Long&gt; | 否 | 元素 @NotNull；@AssertTrue：与部门至少选一 | 员工编号列表 |
| deptIds | List&lt;Long&gt; | 否 | 同上 | 部门编号列表 |
| type | Integer | 是 | @NotNull、@InEnum(调薪方式枚举) | 调薪方式（按金额/按百分比） |
| changeReason | Integer | 是 | @NotNull、@InEnum | 调整原因 |
| effectTime | LocalDateTime | 是 | @NotNull | 生效日期 |
| remark | String | 否 | @Size(max=500) | 备注 |
| salaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 是 | @NotEmpty、@Valid | 调薪项列表 |

**响应**: CommonResult&lt;HrmSalaryEmployeeInfoUpdateListRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| successEmployeeIds | List&lt;Long&gt; | 成功员工编号列表 |
| failureEmployeeReasons | Map&lt;Long, String&gt; | 失败员工及原因 |

**业务逻辑**: 1. 合并部门员工与指定员工范围（为空报「薪资数据不合法」）；2. 逐个员工调薪：校验已定薪，按调薪方式在员工当前薪资基础上计算调整后薪资项（百分比按原值乘以调整值百分比、金额直接叠加），试用期员工额外生成试用期薪资项；3. 复用单个调薪逻辑创建调薪记录，单个员工失败不影响其他员工并收集失败原因；4. 记录操作日志。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_014 | 薪资数据不合法 |
| 1_050_400_006 | 员工薪资信息不存在 |

### 6.7 获得薪资档案定薪导入模板

- **路径**: GET /hrm/salary/employee-info/get-fix-import-template
- **权限**: `hrm:salary:employee-info:import`
- **说明**: 下载定薪导入 Excel 模板，动态包含可调薪薪资项列并预填在职员工

**请求参数**: 无

**响应**: Excel 文件流（薪资档案定薪导入模板.xls）。表头：员工姓名、工号、部门编号、岗位、试用期-各项薪资项、正式-各项薪资项、备注

**业务逻辑**: 1. 获取导入可用的薪资项（可调薪分类下参与计算且不在导入排除范围的薪资项）；2. 生成「试用期-」「正式-」两组薪资项表头；3. 预填在职员工行（金额为 0），无员工时输出示例行。

### 6.8 导入薪资档案定薪

- **路径**: POST /hrm/salary/employee-info/import-fix
- **权限**: `hrm:salary:employee-info:import`
- **说明**: 按模板批量导入员工定薪

**请求参数**: file（MultipartFile，Excel 文件）

**响应**: CommonResult&lt;HrmSalaryEmployeeInfoImportRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| successJobNumbers | List&lt;String&gt; | 导入成功的工号数组 |
| failureJobNumbers | Map&lt;String, String&gt; | 导入失败的员工集合（key 为工号或行号，value 为原因） |

**业务逻辑**: 1. 校验导入数据非空；2. 逐行按工号定位员工并解析试用期/正式薪资项金额，执行定薪；3. 单行失败不影响其他行，按工号（或行号）汇总成功与失败结果。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_015 | 导入薪资档案数据不能为空 |
| 1_050_400_014 | 薪资数据不合法 |

### 6.9 获得薪资档案调薪导入模板

- **路径**: GET /hrm/salary/employee-info/get-change-import-template
- **权限**: `hrm:salary:employee-info:import`
- **说明**: 下载调薪导入 Excel 模板，含生效日期、调薪原因与每项「调整前/调整后」数值，预填员工当前薪资

**请求参数**: 无

**响应**: Excel 文件流（薪资档案调薪导入模板.xls）

**业务逻辑**: 1. 获取导入可用的薪资项并生成调整前/调整后成对表头；2. 计算建议生效日期（最早调薪生效日期与当天取较晚者）；3. 预填在职员工的当前薪资项数值。

### 6.10 导入薪资档案调薪

- **路径**: POST /hrm/salary/employee-info/import-change
- **权限**: `hrm:salary:employee-info:import`
- **说明**: 按模板批量导入员工调薪

**请求参数**: file（MultipartFile，Excel 文件）

**响应**: CommonResult&lt;HrmSalaryEmployeeInfoImportRespVO&gt;（结构同 6.8）

**业务逻辑**: 1. 校验导入数据非空；2. 逐行按工号定位员工并校验已定薪，解析生效日期、调薪原因与调整后薪资项；3. 执行调薪并按工号（或行号）汇总成功与失败结果。

**错误码**: 同 6.8，另加：

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_006 | 员工薪资信息不存在 |
| 1_050_400_030 | 调薪生效日期不能为空，且不能早于最近工资月份 |

---

## 7. 定薪/调薪记录（HrmSalaryChangeRecordController）

### 7.1 获得定薪/调薪记录

- **路径**: GET /hrm/salary/change-record/get
- **权限**: `hrm:salary:employee-info:query`
- **说明**: 按编号查询单条记录

**请求参数**: id（Long，Query 参数，记录编号）

**响应**: CommonResult&lt;HrmSalaryChangeRecordRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 记录编号 |
| employeeId | Long | 员工编号 |
| recordType | Integer | 记录类型 |
| recordTypeName | String | 记录类型名称（拼接） |
| changeReason | Integer | 调整原因（字典） |
| effectTime | LocalDateTime | 生效日期 |
| beforeTotal | BigDecimal | 调整前正式工资 |
| afterTotal | BigDecimal | 调整后正式工资 |
| probationBeforeTotal | BigDecimal | 调整前试用期工资 |
| probationAfterTotal | BigDecimal | 调整后试用期工资 |
| status | Integer | 状态（待生效/已生效/已取消，字典） |
| remark | String | 备注 |
| salaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 薪资项列表 |
| probationSalaryOptions | List&lt;HrmSalaryOptionValueVO&gt; | 试用期薪资项列表 |
| createTime | LocalDateTime | 创建时间 |

### 7.2 获得定薪/调薪记录列表

- **路径**: GET /hrm/salary/change-record/list
- **权限**: `hrm:salary:employee-info:query`
- **说明**: 查询指定员工的全部定薪/调薪记录

**请求参数**: employeeId（Long，Query 参数，员工编号）

**响应**: CommonResult&lt;List&lt;HrmSalaryChangeRecordRespVO&gt;&gt;

### 7.3 取消定薪/调薪记录

- **路径**: PUT /hrm/salary/change-record/cancel
- **权限**: `hrm:salary:employee-info:update`
- **说明**: 取消处于待生效状态的记录

**请求参数**: id（Long，Query 参数，记录编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验记录存在且处于待生效状态；2. 通过状态条件更新（待生效 → 已取消），并发抢占失败时报状态错误。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_007 | 定薪调薪记录不存在 |
| 1_050_400_017 | 当前定薪调薪记录状态不允许执行该操作 |

### 7.4 删除定薪/调薪记录

- **路径**: DELETE /hrm/salary/change-record/delete
- **权限**: `hrm:salary:change-record:delete`
- **说明**: 删除非已生效状态的记录

**请求参数**: id（Long，Query 参数，记录编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验记录存在且不是已生效状态；2. 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_007 | 定薪调薪记录不存在 |
| 1_050_400_017 | 当前定薪调薪记录状态不允许执行该操作 |

---

## 8. 月度工资表（HrmSalaryMonthRecordController）

### 8.1 创建下月工资表

- **路径**: POST /hrm/salary/month-record/create-next
- **权限**: `hrm:salary:month-record:create`
- **说明**: 基于最近工资表或计薪配置创建下一月工资表

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt; —— 工资表编号

**业务逻辑**: 1. 查询最近月度工资表；2. 首次创建时使用计薪配置的开始年月（配置缺失报「薪资配置不存在」）；非首次时先将最近工资表归档为「历史」状态，再取其年月加一个月；3. 创建工资表：校验年月唯一、按计薪周期开始/结束日推导计薪周期、生成默认标题「{年}年{月}工资表」与可见薪资项表头。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_000 | 薪资配置不存在 |
| 1_050_400_009 | 该月份工资表已存在 |

### 8.2 核算工资表

- **路径**: POST /hrm/salary/month-record/compute
- **权限**: `hrm:salary:month-record:compute`
- **说明**: 不带导入文件核算指定工资表（不同步社保/考勤模块数据）

**请求参数**: id（Long，Query 参数，工资表编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 与 8.3 相同，考勤、专项附加扣除、累计个税导入数据均为空且不同步考勤/社保模块。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_008 | 月度工资表不存在 |
| 1_050_400_018 | 当前工资表状态不允许执行该操作 |

### 8.3 带导入文件核算工资表

- **路径**: POST /hrm/salary/month-record/compute-import（multipart/form-data）
- **权限**: `hrm:salary:month-record:compute`
- **说明**: 核算工资表，支持上传考勤、专项附加扣除、上月个税累计文件，并可选择同步社保/考勤模块数据

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | - | 工资表编号 |
| syncInsuranceData | Boolean | 否 | 默认 true | 是否同步社保数据 |
| syncAttendanceData | Boolean | 否 | 默认 false | 是否同步考勤数据 |
| attendanceFile | MultipartFile | 否 | - | 考勤数据文件 |
| additionalDeductionFile | MultipartFile | 否 | - | 专项附加扣除数据文件 |
| cumulativeTaxFile | MultipartFile | 否 | - | 上月个税累计数据文件 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 加锁校验工资表存在且非「历史」状态，构造计薪周期；2. 获得计薪周期内已分配薪资组的员工；3. 加载薪资项、考勤数据（同步考勤模块或按工号解析导入文件）、社保数据（按社保对应月份类型解析年月并校验月度社保表存在）、专项附加扣除与累计个税导入数据、各薪资组计税规则；4. 逐员工获取计薪周期内生效薪资（无薪资档案时继承上月可维护薪资项），并依次合并考勤、社保、专项附加扣除、累计个税数据；5. 批量计算员工月工资（应发、应税、个税、实发）并保存员工记录（新增/更新，删除不在范围的记录）；6. 更新工资表为「已核算」状态、刷新薪资项表头并重算汇总金额。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_008 | 月度工资表不存在 |
| 1_050_400_018 | 当前工资表状态不允许执行该操作 |
| 1_050_500_004 | 月度社保表不存在（同步社保数据时） |

### 8.4 获得工资表考勤导入模板

- **路径**: GET /hrm/salary/month-record/get-attendance-import-template
- **权限**: `hrm:salary:month-record:compute`
- **说明**: 下载考勤导入模板，指定工资表时预填考勤扣款与实际计薪天数

**请求参数**: monthRecordId（Long，Query 参数，可选，月度工资表编号）

**响应**: Excel 文件流。表头：员工名称、岗位、工号、部门编号、加班工资、迟到扣款、早退扣款、旷工扣款、假期扣款、缺卡扣款、综合扣款、实际计薪天数

**业务逻辑**: 1. 取指定或最近工资表的计薪员工（仅保留已配置薪资组的员工）；2. 指定工资表时查询考勤月记录，预填迟到/早退/旷工/缺卡扣款与实际计薪天数；3. 未指定或工资表不存在时输出空白模板。

### 8.5 获得工资表上月个税累计导入模板

- **路径**: GET /hrm/salary/month-record/get-cumulative-tax-import-template
- **权限**: `hrm:salary:month-record:compute`
- **说明**: 下载上月个税累计导入模板，仅包含使用工资薪金计税规则的员工

**请求参数**: monthRecordId（Long，Query 参数，可选）

**响应**: Excel 文件流。业务表头：累计收入额（截至上月）、累计减除费用（截至上月）、累计专项扣除（截至上月）、累计已预缴税额

### 8.6 获得工资表专项附加扣除导入模板

- **路径**: GET /hrm/salary/month-record/get-additional-deduction-import-template
- **权限**: `hrm:salary:month-record:compute`
- **说明**: 下载专项附加扣除导入模板

**请求参数**: monthRecordId（Long，Query 参数，可选）

**响应**: Excel 文件流。业务表头：累计子女教育、累计住房租金、累计住房贷款利息、累计赡养老人、累计继续教育

### 8.7 删除月度工资表

- **路径**: DELETE /hrm/salary/month-record/delete
- **权限**: `hrm:salary:month-record:delete`
- **说明**: 仅允许删除最新的工资表且至少保留一张

**请求参数**: id（Long，Query 参数，工资表编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 加锁校验工资表可编辑；2. 校验待删除的是最新工资表且系统中不止一张工资表；3. 删除员工月度工资记录和工资表，并将上一张工资表恢复为「已核算」状态。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_008 | 月度工资表不存在 |
| 1_050_400_018 | 当前工资表状态不允许执行该操作 |
| 1_050_400_024 | 只能删除最新的月度工资表 |
| 1_050_400_025 | 至少需要保留一张月度工资表 |

### 8.8 获得月度工资表

- **路径**: GET /hrm/salary/month-record/get
- **权限**: `hrm:salary:month-record:query`
- **说明**: 按编号查询工资表

**请求参数**: id（Long，Query 参数，工资表编号）

**响应**: CommonResult&lt;HrmSalaryMonthRecordRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| year / month | Integer | 年份 / 月份 |
| title | String | 标题 |
| startTime / endTime | LocalDateTime | 计薪开始 / 结束日期 |
| employeeCount | Integer | 员工数量 |
| expectedPaySalary | BigDecimal | 应发工资 |
| personalInsuranceAmount | BigDecimal | 个人社保金额 |
| personalProvidentFundAmount | BigDecimal | 个人公积金金额 |
| personalTax | BigDecimal | 个人所得税 |
| realPaySalary | BigDecimal | 实发工资 |
| corporateInsuranceAmount | BigDecimal | 公司社保金额 |
| corporateProvidentFundAmount | BigDecimal | 公司公积金金额 |
| status | Integer | 核算状态 |
| optionHeaders | List&lt;HrmSalaryOptionNodeRespVO&gt; | 薪资项表头（两级树形） |
| createTime | LocalDateTime | 创建时间 |

### 8.9 获得月度工资表分页

- **路径**: GET /hrm/salary/month-record/page
- **权限**: `hrm:salary:month-record:query`
- **说明**: 分页查询工资表，响应结构同 8.8

**请求参数 (HrmSalaryMonthRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| year | Integer | 否 | - | 年份 |
| month | Integer | 否 | - | 月份 |
| status | Integer | 否 | @InEnum(工资表状态枚举) | 核算状态 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalaryMonthRecordRespVO&gt;&gt;

### 8.10 获得最近月度工资表

- **路径**: GET /hrm/salary/month-record/last
- **权限**: `hrm:salary:month-record:query`
- **说明**: 查询最近一张工资表，响应结构同 8.8

**请求参数**: 无

### 8.11 获得工资核算准备情况

- **路径**: GET /hrm/salary/month-record/payroll-readiness
- **权限**: `hrm:salary:month-record:query`
- **说明**: 核算前检查计薪人数、未定薪/未分配薪资组员工与周期内异动

**请求参数**: monthRecordId（Long，Query 参数，可选，默认取最近工资表）

**响应**: CommonResult&lt;HrmSalaryPayrollReadinessRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| monthRecordId | Long | 工资表编号 |
| title | String | 标题 |
| year / month | Integer | 年份 / 月份 |
| startTime / endTime | LocalDateTime | 计薪开始 / 结束日期 |
| socialSecurityYearMonth | String | 社保年月 |
| payrollEmployeeCount | Long | 计薪员工人数 |
| salaryEmployeeCount | Long | 已定薪员工人数 |
| noSalaryEmployeeCount | Long | 未定薪员工人数 |
| noSalaryGroupEmployeeCount | Long | 未分配薪资组员工人数 |
| changeEmployeeCount | Long | 异动员工人数 |
| changeTypeCountMap | Map&lt;Integer, Long&gt; | 变更类型数量映射（转正/调岗/晋升/降级/转全职） |
| noSalaryEmployees | List&lt;Employee&gt; | 未定薪员工列表 |
| noSalaryGroupEmployees | List&lt;Employee&gt; | 未分配薪资组员工列表 |

Employee 内嵌结构：employeeId、employeeName、jobNumber、deptId、deptName、postName、entryStatus、status、entryTime

**业务逻辑**: 1. 获得指定或最近工资表及计薪周期内员工；2. 按薪资组配置拆分已分配/未分配薪资组员工，并在已分配员工中统计已定薪与未定薪名单；3. 统计周期内员工异动记录并按类型计数；4. 填充未定薪、未分配薪资组员工的部门名称。

### 8.12 获得工资项汇总

- **路径**: GET /hrm/salary/month-record/option-summary
- **权限**: `hrm:salary:month-record:query`
- **说明**: 按条件查询员工月度工资并按薪资项汇总金额

**请求参数 (HrmSalaryMonthEmployeeRecordListReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| monthRecordId | Long | 是 | @NotNull | 工资表编号 |
| employeeId | Long | 否 | - | 员工编号 |
| employeeName | String | 否 | - | 员工姓名 |
| jobNumber | String | 否 | - | 工号 |
| deptId | Long | 否 | - | 部门编号 |
| employeeChangeType | Integer | 否 | @InEnum(员工异动分类枚举) | 员工异动类型 |

**响应**: CommonResult&lt;List&lt;HrmSalaryOptionValueVO&gt;&gt;（code/name/value 汇总）

**业务逻辑**: 1. 按条件筛选工资表员工记录（支持按员工信息与异动类型过滤）；2. 按薪资项编码累加全部员工金额并按编码排序返回。

---

## 9. 员工月度工资（HrmSalaryMonthEmployeeRecordController）

### 9.1 批量修改员工工资项

- **路径**: PUT /hrm/salary/month-employee-record/update-list
- **权限**: `hrm:salary:month-record:update`
- **说明**: 批量修改员工月度工资的可编辑薪资项并重算

**请求参数**: List&lt;HrmSalaryMonthEmployeeRecordUpdateReqVO&gt;（Body 数组，@NotEmpty）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 员工月度工资记录编号 |
| optionValues | List&lt;HrmSalaryOptionValueVO&gt; | 否 | @Valid | 薪资项值列表 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验记录编号不重复、全部存在且属于同一张可编辑（非历史）工资表；2. 将提交的薪资项值合并到员工现有薪资项（忽略计算项），并按员工薪资组的计税规则重新计算应发、应税、个税、实发；3. 更新员工记录并统一刷新工资表汇总；4. 记录操作日志（仅记录影响员工范围与薪资项名称，不记录薪资金额）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_010 | 员工月度工资记录不存在 |
| 1_050_400_014 | 薪资数据不合法 |
| 1_050_400_018 | 当前工资表状态不允许执行该操作 |

### 9.2 获得员工月度工资分页

- **路径**: GET /hrm/salary/month-employee-record/page
- **权限**: `hrm:salary:month-record:query`
- **说明**: 按工资表分页查询员工工资，拼接员工、部门与绩效系数

**请求参数 (HrmSalaryMonthEmployeeRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| monthRecordId | Long | 是 | @NotNull | 工资表编号 |
| employeeId | Long | 否 | - | 员工编号 |
| employeeName | String | 否 | - | 员工姓名（模糊） |
| jobNumber | String | 否 | - | 工号（模糊） |
| deptId | Long | 否 | - | 部门编号 |
| employeeChangeType | Integer | 否 | @InEnum(员工异动分类枚举) | 员工异动类型 |
| employeeIds | List&lt;Long&gt; | 否 | - | 员工编号列表 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalaryMonthEmployeeRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| monthRecordId | Long | 工资表编号 |
| employeeId | Long | 员工编号 |
| year / month | Integer | 年份 / 月份 |
| employeeName / jobNumber | String | 员工姓名 / 工号（拼接） |
| deptId / deptName | Long / String | 部门编号 / 名称（拼接） |
| postName | String | 职位名称 |
| actualWorkDay | BigDecimal | 计薪出勤天数 |
| needWorkDay | BigDecimal | 应出勤天数 |
| expectedPaySalary | BigDecimal | 应发工资 |
| taxableSalary | BigDecimal | 应税工资 |
| personalTax | BigDecimal | 个人所得税 |
| realPaySalary | BigDecimal | 实发工资 |
| performanceCoefficient | BigDecimal | 绩效系数（拼接） |
| optionValues | List&lt;HrmSalaryOptionValueVO&gt; | 薪资项值列表 |

**业务逻辑**: 1. 校验工资表存在；2. 按员工信息与异动类型（新入职/离职按入职离职时间、转正/调岗按异动记录）筛选员工编号；3. 分页查询并批量拼接员工、部门信息与绩效系数（仅同月记录查询绩效）。

### 9.3 获得指定员工的月度工资分页

- **路径**: GET /hrm/salary/month-employee-record/employee-page
- **权限**: `hrm:salary:month-record:query`
- **说明**: 员工个人工资条历史分页

**请求参数 (HrmSalaryEmployeeMonthRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| employeeId | Long | 是 | @NotNull | 员工编号 |
| monthRecordStatus | Integer | 否 | @InEnum(工资表状态枚举) | 月度工资表状态 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalaryMonthEmployeeRecordRespVO&gt;&gt;（结构同 9.2）

**业务逻辑**: 1. 按状态条件筛选月度工资表编号列表；2. 查询指定员工在这些工资表中的工资分页。

### 9.4 获得员工月度工资列表

- **路径**: GET /hrm/salary/month-employee-record/list
- **权限**: `hrm:salary:month-record:query`
- **说明**: 列表查询，请求参数与筛选逻辑同 8.12 的 HrmSalaryMonthEmployeeRecordListReqVO

**请求参数**: 同 HrmSalaryMonthEmployeeRecordListReqVO（monthRecordId 必填，其余同 9.2）

**响应**: CommonResult&lt;List&lt;HrmSalaryMonthEmployeeRecordRespVO&gt;&gt;（结构同 9.2）

### 9.5 获得工资表员工异动分类数量

- **路径**: GET /hrm/salary/month-employee-record/change-count
- **权限**: `hrm:salary:month-record:query`
- **说明**: 按其它筛选条件统计各员工异动分类（全部/新入职/离职/转正/调岗）数量

**请求参数**: 同 HrmSalaryMonthEmployeeRecordPageReqVO

**响应**: CommonResult&lt;Map&lt;Integer, Long&gt;&gt;（异动分类 → 数量）

**业务逻辑**: 1. 校验工资表存在；2. 按其它条件（忽略异动类型本身）筛选员工编号；3. 分别按异动类型（入职/离职按时间、转正/调岗按异动记录）过滤统计。

### 9.6 获得员工绩效系数

- **路径**: POST /hrm/salary/month-employee-record/performance-coefficients
- **权限**: `hrm:salary:month-record:query`
- **说明**: 查询指定年月员工绩效系数（仅统计同步到工资的绩效计划）

**请求参数 (HrmSalaryPerformanceCoefficientReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| year | Integer | 是 | @NotNull | 年份 |
| month | Integer | 是 | @NotNull | 月份 |
| employeeIds | List&lt;Long&gt; | 否 | - | 员工编号列表 |

**响应**: CommonResult&lt;Map&lt;Long, BigDecimal&gt;&gt;（员工编号 → 绩效系数）

**业务逻辑**: 1. 查询指定年月「发放同步到工资」的绩效计划；2. 返回员工在绩效归档中的绩效系数 Map。

---

## 10. 工资条模板（HrmSalarySlipTemplateController）

### 10.1 创建工资条模板

- **路径**: POST /hrm/salary/slip-template/create
- **权限**: `hrm:salary:slip:update`
- **说明**: 新建自定义工资条模板

**请求参数 (HrmSalarySlipTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 否 | - | 编号 |
| name | String | 是 | @NotBlank、@Size(max=64) | 模板名称 |
| hideEmpty | Boolean | 否 | - | 是否隐藏空值项 |
| options | List&lt;HrmSalarySlipTemplateOptionVO&gt; | 否 | @Valid | 选项列表 |

HrmSalarySlipTemplateOptionVO:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| name | String | 是 | @NotBlank、@Size(max=64) | 模板项名称 |
| type | Integer | 否 | - | 类型（分类/明细项） |
| code | Integer | 否 | 服务端校验非空且全局唯一 | 编码 |
| remark | String | 否 | @Size(max=255) | 备注 |
| parentCode | Integer | 否 | 校验必须指向合法分类或根 | 父级编码 |
| hidden | Boolean | 否 | - | 是否隐藏 |
| sort | Integer | 否 | - | 排序 |

**响应**: CommonResult&lt;Long&gt; —— 模板编号

**业务逻辑**: 1. 将前端扁平模板节点按排序重建为两层结构：校验节点类型、编码唯一性与父分类引用，缺少「实发工资」项时自动补全；2. 创建自定义模板（默认标记固定为 false）。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_014 | 薪资数据不合法 |

### 10.2 更新工资条模板

- **路径**: PUT /hrm/salary/slip-template/update
- **权限**: `hrm:salary:slip:update`
- **说明**: 更新自定义模板（默认模板不可修改）

**请求参数**: 同 HrmSalarySlipTemplateSaveReqVO（id 必传）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验模板存在且不是默认模板；2. 重建模板项并更新。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_011 | 工资条模板不存在 |
| 1_050_400_014 | 薪资数据不合法（默认模板不允许修改） |

### 10.3 删除工资条模板

- **路径**: DELETE /hrm/salary/slip-template/delete
- **权限**: `hrm:salary:slip:delete`
- **说明**: 删除非默认模板

**请求参数**: id（Long，Query 参数，模板编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验模板存在且不是默认模板；2. 删除模板。

**错误码**: 同 10.2

### 10.4 获得工资条模板

- **路径**: GET /hrm/salary/slip-template/get
- **权限**: `hrm:salary:slip:query`
- **说明**: 查询模板并动态补全薪资项

**请求参数**: id（Long，Query 参数，模板编号）

**响应**: CommonResult&lt;HrmSalarySlipTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| name | String | 模板名称 |
| hideEmpty | Boolean | 是否隐藏空值项 |
| defaultStatus | Boolean | 是否默认选项 |
| options | List&lt;HrmSalarySlipTemplateOptionVO&gt; | 选项列表（扁平化，parentCode 指向父分类） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 查询模板（租户内不存在时回退匹配平台级默认模板）；2. 动态补全：默认模板始终按当前有效薪资项重建「基本项」「明细项」两类；自定义模板保留用户布局，模板创建后新增的薪资项归入「未分类科目」；3. 将树形选项扁平化输出。

### 10.5 获得工资条模板列表

- **路径**: GET /hrm/salary/slip-template/list
- **权限**: `hrm:salary:slip:query`
- **说明**: 查询全部模板，无默认模板时附加平台级默认模板

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;HrmSalarySlipTemplateRespVO&gt;&gt;

---

## 11. 工资条发放记录（HrmSalarySlipSendRecordController）

### 11.1 发放工资条

- **路径**: POST /hrm/salary/slip-send-record/create
- **权限**: `hrm:salary:slip:create`
- **说明**: 对指定工资表批量发放工资条

**请求参数 (HrmSalarySlipSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| monthRecordId | Long | 是 | @NotNull | 工资表编号 |
| hideEmpty | Boolean | 是 | @NotNull | 是否隐藏空值项 |
| options | List&lt;HrmSalarySlipTemplateOptionVO&gt; | 否 | @Valid | 工资条模板项列表 |
| all | Boolean | 是 | @NotNull、@AssertTrue：按已选发放时员工不能为空 | 是否发放全部筛选结果 |
| employeeIds | List&lt;Long&gt; | 否 | - | 员工编号列表 |
| search | String | 否 | - | 员工姓名、工号或手机号 |
| deptId | Long | 否 | - | 部门编号 |
| sent | Boolean | 否 | - | 是否已发送 |

**响应**: CommonResult&lt;Long&gt; —— 发放记录编号

**业务逻辑**: 1. 加锁校验工资表存在，未核算的工资表不允许发放，并构建本次发放的模板快照；2. 筛选发放员工：发放全部时按搜索/部门/已发送状态筛选，否则按指定员工（全部必须存在工资记录）；3. 仅向已绑定后台账号的员工发放，指定发放时存在未绑定账号的员工则报错；4. 创建发放记录（计薪人数、发薪人数、年月）；5. 按模板快照生成员工工资条（同一员工同一月份只允许一张有效工资条，重复发放报错），并逐个发送站内信通知。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_008 | 月度工资表不存在 |
| 1_050_400_018 | 当前工资表状态不允许执行该操作 |
| 1_050_400_010 | 员工月度工资记录不存在 |
| 1_050_400_030 | 员工工资条已经发放，请勿重复操作 |
| 1_050_400_031 | 所选员工未绑定后台账号，无法发放工资条 |

### 11.2 获得工资条待发员工分页

- **路径**: GET /hrm/salary/slip-send-record/employee-page
- **权限**: `hrm:salary:slip:query`
- **说明**: 按工资表分页查询待发员工并标记发放状态

**请求参数 (HrmSalarySlipSendEmployeeReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| monthRecordId | Long | 是 | @NotNull | 月度工资表编号 |
| search | String | 否 | - | 员工姓名、工号或手机号 |
| deptId | Long | 否 | - | 部门编号 |
| sent | Boolean | 否 | - | 是否已发送 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalarySlipSendEmployeeRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| monthEmployeeRecordId | Long | 员工月度工资记录编号 |
| employeeId | Long | 员工编号 |
| employeeName / jobNumber / mobile | String | 姓名 / 工号 / 手机号（拼接） |
| deptId / deptName | Long / String | 部门编号 / 名称（拼接） |
| postName | String | 岗位名称 |
| expectedPaySalary | BigDecimal | 应发工资 |
| realPaySalary | BigDecimal | 实发工资 |
| sent | Boolean | 是否已发送 |

**业务逻辑**: 1. 校验工资表存在；2. 按搜索/部门条件筛选员工编号；3. 查询员工月度工资分页，批量拼接员工、部门信息，并按已有工资条标记是否已发送。

### 11.3 删除工资条发放记录

- **路径**: DELETE /hrm/salary/slip-send-record/delete
- **权限**: `hrm:salary:slip:delete`
- **说明**: 删除发放记录及其下全部工资条

**请求参数**: id（Long，Query 参数，发放记录编号）

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验发放记录存在；2. 级联删除该记录下的全部工资条和发放记录。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_012 | 工资条发放记录不存在 |

### 11.4 获得工资条发放记录分页

- **路径**: GET /hrm/salary/slip-send-record/page
- **权限**: `hrm:salary:slip:query`
- **说明**: 分页查询发放记录，统计已读人数与创建人

**请求参数 (HrmSalarySlipSendRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| year | Integer | 否 | - | 年份 |
| month | Integer | 否 | - | 月份 |

**响应**: CommonResult&lt;PageResult&lt;HrmSalarySlipSendRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| monthRecordId | Long | 工资表编号 |
| employeeCount | Integer | 计薪人数 |
| sendEmployeeCount | Integer | 发薪人数 |
| readCount | Integer | 已读人数（拼接） |
| year / month | Integer | 年份 / 月份 |
| creator / creatorName | String | 创建人编号 / 姓名（拼接） |
| createTime | LocalDateTime | 创建时间 |

### 11.5 获得工资条发放记录

- **路径**: GET /hrm/salary/slip-send-record/get
- **权限**: `hrm:salary:slip:query`
- **说明**: 按编号查询发放记录，响应结构同 11.4

**请求参数**: id（Long，Query 参数，发放记录编号）

---

## 12. 工资条（HrmSalarySlipController）

### 12.1 获得工资条分页

- **路径**: GET /hrm/salary/slip/page
- **权限**: `hrm:salary:slip:query`
- **说明**: 分页查询工资条，支持按员工姓名/工号搜索与部门过滤

**请求参数 (HrmSalarySlipPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| pageNo / pageSize | Integer | 否 | 分页参数 | 分页 |
| sendRecordId | Long | 否 | - | 工资条记录（发放记录）编号 |
| employeeId | Long | 否 | - | 员工编号 |
| employeeIds | List&lt;Long&gt; | 否 | - | 员工编号列表 |
| search | String | 否 | - | 搜索关键字（员工姓名/工号） |
| deptId | Long | 否 | - | 部门编号 |
| readStatus | Integer | 否 | - | 已读状态 |
| remark | String | 否 | - | 备注（模糊） |

**响应**: CommonResult&lt;PageResult&lt;HrmSalarySlipRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Long | 编号 |
| sendRecordId | Long | 工资条记录编号 |
| monthEmployeeRecordId | Long | 员工工资记录编号 |
| employeeId | Long | 员工编号 |
| employeeName / jobNumber / mobile | String | 姓名 / 工号 / 手机号（拼接） |
| deptId / deptName | Long / String | 部门编号 / 名称（拼接） |
| postName | String | 岗位名称 |
| year / month | Integer | 年份 / 月份 |
| readStatus | Integer | 已读状态 |
| realPaySalary | BigDecimal | 实际工资 |
| remark | String | 备注 |
| options | List&lt;HrmSalarySlipOptionRespVO&gt; | 工资条项列表（树形） |
| createTime | LocalDateTime | 创建时间 |

HrmSalarySlipOptionRespVO: name（名称）、type（类型）、code（编码）、value（值）、remark（备注）、sort（排序）、children（子工资条项）

**业务逻辑**: 1. 传入搜索关键字或部门时，先按条件查询员工编号，并与传入 employeeIds 求交集（交集为空直接返回空页）；2. 分页查询工资条并批量拼接员工、部门信息与工资条项。

### 12.2 获得工资条

- **路径**: GET /hrm/salary/slip/get
- **权限**: `hrm:salary:slip:query`
- **说明**: 按编号查询工资条，响应结构同 12.1

**请求参数**: id（Long，Query 参数，工资条编号）

### 12.3 修改工资条备注

- **路径**: PUT /hrm/salary/slip/remark
- **权限**: `hrm:salary:slip:update`
- **说明**: 管理端修改工资条备注

**请求参数 (HrmSalarySlipRemarkReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| id | Long | 是 | @NotNull | 工资条编号 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Boolean&gt;

**业务逻辑**: 1. 校验工资条存在；2. 更新备注。

**错误码**:

| 错误码 | 说明 |
|-------|-----|
| 1_050_400_013 | 工资条不存在 |
