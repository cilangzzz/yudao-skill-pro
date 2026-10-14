# 配送接口 (DeliveryExpressController / DeliveryExpressTemplateController / DeliveryPickUpStoreController)

> 交易模块配送域：维护快递公司、快递运费模板（计费/包邮规则）与自提门店（含核销店员绑定）三类基础数据，为下单运费计算与订单发货/核销提供支撑。

## 接口路径前缀

- /trade/delivery/express （Controller: DeliveryExpressController，快递公司）
- /trade/delivery/express-template （Controller: DeliveryExpressTemplateController，快递运费模板）
- /trade/delivery/pick-up-store （Controller: DeliveryPickUpStoreController，自提门店）

---

## 1. 快递公司（DeliveryExpressController）

### 1.1 创建快递公司

- **路径**: POST /trade/delivery/express/create
- **权限**: trade:delivery:express:create
- **说明**: 新增一条快递公司记录，编码必须唯一。

**请求参数 (DeliveryExpressCreateReqVO)**: 继承 DeliveryExpressBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| code | String | 是 | @NotNull | 快递公司编码 |
| name | String | 是 | @NotNull | 快递公司名称 |
| logo | String | 否 | 无 | 快递公司 logo |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull | 状态（CommonStatusEnum：0 开启 1 停用） |

**响应**: CommonResult&lt;Long&gt;（新记录编号）

**业务逻辑**:
1. 校验快递公司编码唯一（按 code 查库，已存在则抛 EXPRESS_CODE_DUPLICATE）。
2. 转换为 DeliveryExpressDO 并插入数据库。
3. 返回新记录 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_004_001 | 已经存在该编码的快递公司 |

### 1.2 更新快递公司

- **路径**: PUT /trade/delivery/express/update
- **权限**: trade:delivery:express:update
- **说明**: 按 id 更新快递公司，编码唯一性排除自身。

**请求参数 (DeliveryExpressUpdateReqVO)**: 继承 DeliveryExpressBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 快递公司编号 |
| code | String | 是 | @NotNull | 快递公司编码 |
| name | String | 是 | @NotNull | 快递公司名称 |
| logo | String | 否 | 无 | 快递公司 logo |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull | 状态 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验快递公司存在（不存在抛 EXPRESS_NOT_EXISTS）。
2. 校验编码唯一，排除自身 id（冲突抛 EXPRESS_CODE_DUPLICATE）。
3. 转换为 DO 后 updateById 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_004_000 | 快递公司不存在 |
| 1_011_004_001 | 已经存在该编码的快递公司 |

### 1.3 删除快递公司

- **路径**: DELETE /trade/delivery/express/delete
- **权限**: trade:delivery:express:delete
- **说明**: 按 id 删除快递公司。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 快递公司编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验快递公司存在（不存在抛 EXPRESS_NOT_EXISTS）。
2. deleteById 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_004_000 | 快递公司不存在 |

### 1.4 获得快递公司

- **路径**: GET /trade/delivery/express/get
- **权限**: trade:delivery:express:query
- **说明**: 按编号查询单条快递公司详情。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 快递公司编号 |

**响应**: CommonResult&lt;DeliveryExpressRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| code | String | 快递公司编码 |
| name | String | 快递公司名称 |
| logo | String | 快递公司 logo |
| sort | Integer | 排序 |
| status | Integer | 状态 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. selectById 查询 DO（可能为 null）。
2. 通过 DeliveryExpressConvert 转换为 RespVO 返回。

### 1.5 获取快递公司精简信息列表

- **路径**: GET /trade/delivery/express/list-all-simple
- **权限**: 已认证（仅登录，无 @PreAuthorize 权限校验）
- **说明**: 获取开启状态的快递公司精简列表，用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DeliveryExpressSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 快递公司名称 |

**业务逻辑**:
1. 查询 status = 开启（CommonStatusEnum.ENABLE）的快递公司列表。
2. 转换为精简 RespVO 列表返回。

### 1.6 获得快递公司分页

- **路径**: GET /trade/delivery/express/page
- **权限**: trade:delivery:express:query
- **说明**: 分页查询快递公司，支持编码/名称/状态/创建时间过滤。

**请求参数 (DeliveryExpressPageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 无 | 页码（PageParam 默认 1） |
| pageSize | Integer | 否 | 无 | 每页条数（PageParam 默认 10） |
| code | String | 否 | 无 | 快递公司编码 |
| name | String | 否 | 无 | 快递公司名称 |
| status | Integer | 否 | 无 | 状态（0 正常 1 停用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;DeliveryExpressRespVO&gt;&gt;，列表元素字段同 1.4 响应。

**业务逻辑**:
1. 调用 Mapper selectPage 按条件分页查询。
2. 转换分页结果为 RespVO 返回。

### 1.7 导出快递公司 Excel

- **路径**: GET /trade/delivery/express/export-excel
- **权限**: trade:delivery:express:export
- **说明**: 按条件查询并导出快递公司 Excel（.xls），操作日志记为导出（@ApiAccessLog EXPORT）。

**请求参数 (DeliveryExpressExportReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| code | String | 否 | 无 | 快递公司编码 |
| name | String | 否 | 无 | 快递公司名称 |
| status | Integer | 否 | 无 | 状态（0 正常 1 停用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: 无 CommonResult 包装，直接以文件流输出 Excel（文件名「快递公司.xls」），列含编号/编码/名称/logo/排序/状态（字典转换）/创建时间。

**业务逻辑**:
1. 按导出条件查询快递公司列表。
2. 转换为 DeliveryExpressExcelVO 列表（状态经 DictConvert 字典转换）。
3. ExcelUtils.write 写入响应流。

---

## 2. 快递运费模板（DeliveryExpressTemplateController）

### 2.1 创建快递运费模板

- **路径**: POST /trade/delivery/express-template/create
- **权限**: trade:delivery:express-template:create
- **说明**: 创建运费模板主表记录，并同步保存区域运费（charges）与包邮规则（frees）从表，整体在事务内执行。

**请求参数 (DeliveryExpressTemplateCreateReqVO)**: 继承 DeliveryExpressTemplateBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotNull | 模板名称 |
| chargeMode | Integer | 是 | @NotNull | 配送计费方式：1 按件 2 按重量 3 按体积 |
| sort | Integer | 是 | @NotNull | 排序 |
| charges | List&lt;DeliveryExpressTemplateChargeBaseVO&gt; | 否 | @Valid（元素校验见下） | 区域运费列表 |
| frees | List&lt;DeliveryExpressTemplateFreeBaseVO&gt; | 否 | @Valid（元素校验见下） | 包邮区域列表 |

charges（DeliveryExpressTemplateChargeBaseVO）元素字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | 无 | 运费设置编号（更新时复用，创建时无需） |
| areaIds | List&lt;Integer&gt; | 是 | @NotEmpty | 区域编号列表 |
| startCount | Double | 是 | @NotNull | 首件/首重/首方数量 |
| startPrice | Integer | 是 | @NotNull | 起步价（单位分） |
| extraCount | Double | 是 | @NotNull | 续件/续重/续方数量 |
| extraPrice | Integer | 是 | @NotNull | 额外价（单位分） |

frees（DeliveryExpressTemplateFreeBaseVO）元素字段：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| areaIds | List&lt;Integer&gt; | 是 | @NotEmpty | 区域编号列表 |
| freePrice | Integer | 是 | @NotNull | 包邮金额（单位分） |
| freeCount | Integer | 是 | @NotNull | 包邮件数 |

**响应**: CommonResult&lt;Long&gt;（新模板编号）

**业务逻辑**:
1. 校验模板名唯一（按 name 查库，重复抛 EXPRESS_TEMPLATE_NAME_DUPLICATE）。
2. 插入运费模板主表 DeliveryExpressTemplateDO。
3. charges 非空时，将 chargeMode 冗余到每条计费记录并批量插入计费从表。
4. frees 非空时，批量插入包邮从表。
5. 返回模板 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_005_000 | 已经存在该运费模板名 |

### 2.2 更新快递运费模板

- **路径**: PUT /trade/delivery/express-template/update
- **权限**: trade:delivery:express-template:update
- **说明**: 更新模板主表，并按 diff 增量更新运费/包邮两组从表，事务内执行。

**请求参数 (DeliveryExpressTemplateUpdateReqVO)**: 继承 DeliveryExpressTemplateBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 模板编号 |
| name | String | 是 | @NotNull | 模板名称 |
| chargeMode | Integer | 是 | @NotNull | 配送计费方式：1 按件 2 按重量 3 按体积 |
| sort | Integer | 是 | @NotNull | 排序 |
| charges | List&lt;DeliveryExpressTemplateChargeBaseVO&gt; | 否 | @Valid | 区域运费列表（元素字段同 2.1，含 id 时为更新既有记录） |
| frees | List&lt;DeliveryExpressTemplateFreeBaseVO&gt; | 否 | @Valid | 包邮区域列表（元素字段同 2.1） |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验模板存在（不存在抛 EXPRESS_TEMPLATE_NOT_EXISTS）。
2. 校验模板名唯一，排除自身 id。
3. 计费从表增量更新：diffList 对比新老 charges（按 id 匹配，匹配项同步 chargeMode），分批执行插入/更新/删除。
4. 包邮从表增量更新：同样按 id diff 后分批插入/更新/删除。
5. 更新模板主表。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_005_001 | 运费模板不存在 |
| 1_011_005_000 | 已经存在该运费模板名 |

### 2.3 删除快递运费模板

- **路径**: DELETE /trade/delivery/express-template/delete
- **权限**: trade:delivery:express-template:delete
- **说明**: 删除模板主表及对应的运费/包邮从表记录，事务内执行。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验模板存在（不存在抛 EXPRESS_TEMPLATE_NOT_EXISTS）。
2. 删除主表记录。
3. 按 templateId 删除运费计费从表记录。
4. 按 templateId 删除包邮从表记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_005_001 | 运费模板不存在 |

### 2.4 获得快递运费模板（详情）

- **路径**: GET /trade/delivery/express-template/get
- **权限**: trade:delivery:express-template:query
- **说明**: 查询模板主表 + 运费设置 + 包邮规则的完整详情。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 模板编号 |

**响应**: CommonResult&lt;DeliveryExpressTemplateDetailRespVO&gt;（继承 DeliveryExpressTemplateBaseVO）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模板名称 |
| chargeMode | Integer | 计费方式：1 按件 2 按重量 3 按体积 |
| sort | Integer | 排序 |
| charges | List&lt;DeliveryExpressTemplateChargeBaseVO&gt; | 运费设置列表（元素字段同 2.1 charges 表，含 id/areaIds/startCount/startPrice/extraCount/extraPrice） |
| frees | List&lt;DeliveryExpressTemplateFreeBaseVO&gt; | 包邮区域列表（元素字段同 2.1 frees 表：areaIds/freePrice/freeCount） |

**业务逻辑**:
1. 按 templateId 查询运费计费从表列表。
2. 按 templateId 查询包邮从表列表。
3. 按 id 查询模板主表。
4. 通过 Convert 将三者组装为 DetailRespVO 返回。

### 2.5 获得快递运费模板列表

- **路径**: GET /trade/delivery/express-template/list
- **权限**: trade:delivery:express-template:query
- **说明**: 按编号集合批量查询运费模板。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Collection&lt;Long&gt; | 是 | @RequestParam required | 编号列表，逗号分隔，如 1024,2048 |

**响应**: CommonResult&lt;List&lt;DeliveryExpressTemplateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模板名称 |
| chargeMode | Integer | 计费方式 |
| sort | Integer | 排序 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 ids 批量查询模板 DO 列表。
2. 转换为 RespVO 列表返回。

### 2.6 获取快递模板精简信息列表

- **路径**: GET /trade/delivery/express-template/list-all-simple
- **权限**: 已认证（仅登录，无 @PreAuthorize 权限校验）
- **说明**: 获取运费模板精简列表，用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DeliveryExpressTemplateSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模版编号 |
| name | String | 模板名称 |

**业务逻辑**:
1. 查询运费模板列表（服务层 selectList 全量查询；控制器注释说明意图为仅开启状态）。
2. 转换为精简 RespVO 列表返回。

### 2.7 获得快递运费模板分页

- **路径**: GET /trade/delivery/express-template/page
- **权限**: trade:delivery:express-template:query
- **说明**: 分页查询运费模板，支持名称/计费方式/创建时间过滤。

**请求参数 (DeliveryExpressTemplatePageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 无 | 页码 |
| pageSize | Integer | 否 | 无 | 每页条数 |
| name | String | 否 | 无 | 模板名称 |
| chargeMode | Integer | 否 | 无 | 计费方式：1 按件 2 按重量 3 按体积 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;DeliveryExpressTemplateRespVO&gt;&gt;，元素字段同 2.5。

**业务逻辑**:
1. 调用 Mapper selectPage 按条件分页查询。
2. 转换分页结果为 RespVO 返回。

---

## 3. 自提门店（DeliveryPickUpStoreController）

### 3.1 创建自提门店

- **路径**: POST /trade/delivery/pick-up-store/create
- **权限**: trade:delivery:pick-up-store:create
- **说明**: 新增自提门店基础信息。

**请求参数 (DeliveryPickUpStoreCreateReqVO)**: 继承 DeliveryPickUpStoreBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotBlank | 门店名称 |
| introduction | String | 否 | 无 | 门店简介 |
| phone | String | 是 | @NotBlank、@Mobile | 门店手机 |
| areaId | Integer | 是 | @NotNull | 区域编号 |
| detailAddress | String | 是 | @NotBlank | 门店详细地址 |
| logo | String | 是 | @NotBlank | 门店 logo |
| openingTime | LocalTime | 是 | @NotNull，JSON 格式 HH:mm | 营业开始时间 |
| closingTime | LocalTime | 是 | @NotNull，JSON 格式 HH:mm | 营业结束时间 |
| latitude | Double | 是 | @NotNull | 纬度 |
| longitude | Double | 是 | @NotNull | 经度 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 门店状态 |

**响应**: CommonResult&lt;Long&gt;（新门店编号）

**业务逻辑**:
1. 转换为 DeliveryPickUpStoreDO 并插入数据库。
2. 返回新记录 id。

### 3.2 更新自提门店

- **路径**: PUT /trade/delivery/pick-up-store/update
- **权限**: trade:delivery:pick-up-store:update
- **说明**: 按 id 更新自提门店信息。

**请求参数 (DeliveryPickUpStoreUpdateReqVO)**: 继承 DeliveryPickUpStoreBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 门店编号 |
| 其余字段 | — | — | — | 同 3.1 的 BaseVO 字段（name/introduction/phone/areaId/detailAddress/logo/openingTime/closingTime/latitude/longitude/status） |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验门店存在（不存在抛 PICK_UP_STORE_NOT_EXISTS）。
2. 转换为 DO 后 updateById 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_006_000 | 自提门店不存在 |

### 3.3 删除自提门店

- **路径**: DELETE /trade/delivery/pick-up-store/delete
- **权限**: trade:delivery:pick-up-store:delete
- **说明**: 按 id 删除自提门店。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 门店编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验门店存在（不存在抛 PICK_UP_STORE_NOT_EXISTS）。
2. deleteById 删除记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_006_000 | 自提门店不存在 |

### 3.4 获得自提门店

- **路径**: GET /trade/delivery/pick-up-store/get
- **权限**: trade:delivery:pick-up-store:query
- **说明**: 查询门店详情，附带核销用户（店员）精简信息。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 门店编号 |

**响应**: CommonResult&lt;DeliveryPickUpStoreRespVO&gt;（继承 DeliveryPickUpStoreBaseVO）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 门店名称 |
| introduction | String | 门店简介 |
| phone | String | 门店手机 |
| areaId | Integer | 区域编号 |
| detailAddress | String | 门店详细地址 |
| logo | String | 门店 logo |
| openingTime | LocalTime | 营业开始时间（HH:mm） |
| closingTime | LocalTime | 营业结束时间（HH:mm） |
| latitude | Double | 纬度 |
| longitude | Double | 经度 |
| status | Integer | 门店状态 |
| createTime | LocalDateTime | 创建时间 |
| areaName | String | 地区名称 |
| verifyUsers | List&lt;UserSimpleBaseVO&gt; | 核销用户数组（元素含 id/nickname/avatar） |

**业务逻辑**:
1. selectById 查询门店，不存在则返回 null 数据。
2. 若 verifyUserIds 非空，调用 AdminUserApi.getUserList 批量查询核销用户。
3. 转换为 RespVO 并填充 verifyUsers 后返回。

### 3.5 获得自提门店精简信息列表

- **路径**: GET /trade/delivery/pick-up-store/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize 权限校验）
- **说明**: 获取开启状态的自提门店精简列表，用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;DeliveryPickUpStoreSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 门店名称 |
| phone | String | 门店手机 |
| areaId | Integer | 区域编号 |
| areaName | String | 区域名称 |
| detailAddress | String | 门店详细地址 |
| verifyUserIds | List&lt;Long&gt; | 绑定用户编号数组 |

**业务逻辑**:
1. 查询 status = 开启（CommonStatusEnum.ENABLE）的门店列表。
2. 转换为精简 RespVO 列表返回。

### 3.6 获得自提门店列表

- **路径**: GET /trade/delivery/pick-up-store/list
- **权限**: trade:delivery:pick-up-store:query
- **说明**: 按编号集合批量查询自提门店。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Collection&lt;Long&gt; | 是 | @RequestParam required | 编号列表，逗号分隔，如 1024,2048 |

**响应**: CommonResult&lt;List&lt;DeliveryPickUpStoreRespVO&gt;&gt;，元素字段同 3.4。

**业务逻辑**:
1. 按 ids 批量查询门店 DO 列表。
2. 转换为 RespVO 列表返回。

### 3.7 获得自提门店分页

- **路径**: GET /trade/delivery/pick-up-store/page
- **权限**: trade:delivery:pick-up-store:query
- **说明**: 分页查询自提门店，支持名称/手机/区域/状态/创建时间过滤。

**请求参数 (DeliveryPickUpStorePageReqVO)**: 继承 PageParam（pageNo、pageSize）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 无 | 页码 |
| pageSize | Integer | 否 | 无 | 每页条数 |
| name | String | 否 | 无 | 门店名称 |
| phone | String | 否 | 无 | 门店手机 |
| areaId | Integer | 否 | 无 | 区域编号 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 门店状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;DeliveryPickUpStoreRespVO&gt;&gt;，元素字段同 3.4。

**业务逻辑**:
1. 调用 Mapper selectPage 按条件分页查询。
2. 转换分页结果为 RespVO 返回。

### 3.8 绑定自提店员

- **路径**: POST /trade/delivery/pick-up-store/bind
- **权限**: trade:delivery:pick-up-store:create（复用创建权限）
- **说明**: 为自提门店绑定核销店员（verifyUserIds）。

**请求参数 (DeliveryPickUpBindReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 门店编号 |
| verifyUserIds | List&lt;Long&gt; | 是 | @NotEmpty | 绑定用户编号数组 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**:
1. 校验门店存在（不存在抛 PICK_UP_STORE_NOT_EXISTS）。
2. 调用 AdminUserApi.validateUserList 校验绑定用户均存在。
3. 将 verifyUserIds 更新到门店记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_011_006_000 | 自提门店不存在 |

---

## 附：本域相关错误码汇总（trade 模块 1-011-004/005/006 段）

| 错误码 | 说明 |
|-------|------|
| 1_011_004_000 | 快递公司不存在 |
| 1_011_004_001 | 已经存在该编码的快递公司 |
| 1_011_004_002 | 需要接入快递服务商，比如【快递100】 |
| 1_011_004_003 | 快递公司未启用 |
| 1_011_004_101 | 快递查询接口异常 |
| 1_011_004_102 | 快递查询返回失败，原因：{} |
| 1_011_005_000 | 已经存在该运费模板名 |
| 1_011_005_001 | 运费模板不存在 |
| 1_011_006_000 | 自提门店不存在 |
| 1_011_003_001 | 计算快递运费异常，找不到对应的运费模板（价格计算时使用模板） |

> 备注：快递公司未启用（1_011_004_003）在订单发货校验快递公司（validateDeliveryExpress）时抛出；运费模板相关在交易价格计算（getExpressTemplateMapByIdsAndArea）中消费；源码中 PICK_UP_STORE_STAFF_NOT_EXISTS 与 PICK_UP_STORE_NOT_EXISTS 共用错误码 1_011_006_000。
