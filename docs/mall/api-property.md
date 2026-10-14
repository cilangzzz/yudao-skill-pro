# 商品属性接口 (ProductPropertyController / ProductPropertyValueController)

> 提供管理后台的商品属性管理能力：属性项（如「颜色」「尺码」）与挂在其下的属性值（如「红色」「XL」）的增删改查、分页与精简列表，属性项/属性值被商品 SPU/SKU 的规格组合引用。

## 接口路径前缀

/product/property  (Controller: ProductPropertyController，属性项)

/product/property/value  (Controller: ProductPropertyValueController，属性值)

---

## 1. 属性项管理（ProductPropertyController）

### 1.1 创建属性项

- **路径**: POST /product/property/create
- **权限**: product:property:create
- **说明**: 创建属性项；若同名属性项已存在则直接返回已有编号（幂等）。

**请求参数 (ProductPropertySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 主键，创建时不传 |
| name | String | 是 | @NotBlank | 属性项名称，如「颜色」 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 属性项编号（已存在同名时返回已有编号） |

**业务逻辑**:
1. 按名称查询属性项（`selectByName`），若已存在同名属性项，直接返回其编号，不再重复插入。
2. 将请求 VO 转换为 `ProductPropertyDO` 并插入 `product_property` 表。
3. 返回新属性项编号。

### 1.2 更新属性项

- **路径**: PUT /product/property/update
- **权限**: product:property:update
- **说明**: 根据编号更新属性项名称/备注，并同步更新 SKU 中引用的属性项名称。

**请求参数 (ProductPropertySaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 属性项编号 |
| name | String | 是 | @NotBlank | 属性项名称 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 `true`。

**业务逻辑**:
1. 校验属性项是否存在，不存在抛出 `PROPERTY_NOT_EXISTS`。
2. 校验名称唯一：按名称查询，若存在且编号不等于当前编号，抛出 `PROPERTY_EXISTS`。
3. 将请求 VO 转换为 `ProductPropertyDO` 并按编号更新。
4. 调用 `productSkuService.updateSkuProperty(id, name)` 同步更新所有 SKU 中冗余的属性项名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_003_000 | 属性项不存在 |
| 1_008_003_001 | 属性项的名称已存在 |

### 1.3 删除属性项

- **路径**: DELETE /product/property/delete
- **权限**: product:property:delete
- **说明**: 删除属性项；若其下存在属性值则拒绝删除，删除时级联删除其下属性值。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 属性项编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 `true`。

**业务逻辑**:
1. 校验属性项是否存在，不存在抛出 `PROPERTY_NOT_EXISTS`。
2. 统计其下属性值数量（`getPropertyValueCountByPropertyId`），大于 0 抛出 `PROPERTY_DELETE_FAIL_VALUE_EXISTS`。
3. 删除属性项记录。
4. 调用 `productPropertyValueService.deletePropertyValueByPropertyId(id)` 级联删除其下全部属性值。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_003_000 | 属性项不存在 |
| 1_008_003_002 | 属性项下存在属性值，无法删除 |

### 1.4 获得属性项

- **路径**: GET /product/property/get
- **权限**: product:property:query
- **说明**: 根据编号获取属性项详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 属性项编号 |

**响应**: CommonResult&lt;ProductPropertyRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 属性项编号 |
| name | String | 属性项名称 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询 `ProductPropertyDO`，转换为 `ProductPropertyRespVO` 返回（不存在时 data 为 null）。

### 1.5 获得属性项分页

- **路径**: GET /product/property/page
- **权限**: product:property:query
- **说明**: 分页查询属性项，支持名称模糊、创建时间区间过滤。

**请求参数 (ProductPropertyPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam，默认 1） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam，默认 10） |
| name | String | 否 | - | 名称，模糊匹配 |
| status | Integer | 否 | - | 状态（VO 中声明，DO 无此字段，当前查询条件未使用） |
| createTime | LocalDateTime[] | 否 | - | 创建时间区间，格式 yyyy-MM-dd HH:mm:ss |

**响应**: CommonResult&lt;PageResult&lt;ProductPropertyRespVO&gt;&gt;，列表元素结构同 1.4 的 ProductPropertyRespVO。

**业务逻辑**:
1. 按条件构建查询：`name` like 模糊匹配、`createTime` between 区间过滤，按 `id` 倒序分页（VO 中的 `status` 未参与查询）。
2. 分页结果转换为 `ProductPropertyRespVO` 返回。

### 1.6 获得属性项精简列表

- **路径**: GET /product/property/simple-list
- **权限**: 已认证（未标注 @PreAuthorize，仅需登录）
- **说明**: 获取全部属性项的精简列表，供前端下拉框选择规格使用，只返回 id、name。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;ProductPropertyRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 属性项编号 |
| name | String | 属性项名称 |

**业务逻辑**:
1. 查询全部属性项列表（`selectList`）。
2. 仅取 id、name 两个字段组装为精简 `ProductPropertyRespVO` 返回。

---

## 2. 属性值管理（ProductPropertyValueController）

### 2.1 创建属性值

- **路径**: POST /product/property/value/create
- **权限**: product:property:create
- **说明**: 在指定属性项下创建属性值；同一属性项下同名属性值已存在时直接返回已有编号（幂等）。

**请求参数 (ProductPropertyValueSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 主键，创建时不传 |
| propertyId | Long | 是 | @NotNull | 属性项的编号 |
| name | String | 是 | @NotEmpty | 属性值名称，如「红色」 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 属性值编号（已存在同名时返回已有编号） |

**业务逻辑**:
1. 按 propertyId + name 查询属性值（`selectByName`），若已存在直接返回其编号。
2. 将请求 VO 转换为 `ProductPropertyValueDO` 并插入 `product_property_value` 表。
3. 返回新属性值编号。

### 2.2 更新属性值

- **路径**: PUT /product/property/value/update
- **权限**: product:property:update
- **说明**: 根据编号更新属性值，并同步更新 SKU 中引用的属性值名称。

**请求参数 (ProductPropertyValueSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | - | 属性值编号 |
| propertyId | Long | 是 | @NotNull | 属性项的编号 |
| name | String | 是 | @NotEmpty | 属性值名称 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 `true`。

**业务逻辑**:
1. 校验属性值是否存在，不存在抛出 `PROPERTY_VALUE_NOT_EXISTS`。
2. 校验同一属性项下名称唯一：按 propertyId + name 查询，若存在且编号不同，抛出 `PROPERTY_VALUE_EXISTS`。
3. 将请求 VO 转换为 `ProductPropertyValueDO` 并按编号更新。
4. 调用 `productSkuService.updateSkuPropertyValue(id, name)` 同步更新所有 SKU 中冗余的属性值名称。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_004_000 | 属性值不存在 |
| 1_008_004_001 | 属性值的名称已存在 |

### 2.3 删除属性值

- **路径**: DELETE /product/property/value/delete
- **权限**: product:property:delete
- **说明**: 根据编号删除属性值。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 属性值编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 `true`。

**业务逻辑**:
1. 校验属性值是否存在，不存在抛出 `PROPERTY_VALUE_NOT_EXISTS`。
2. 按编号删除属性值记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_008_004_000 | 属性值不存在 |

### 2.4 获得属性值

- **路径**: GET /product/property/value/get
- **权限**: product:property:query
- **说明**: 根据编号获取属性值详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam required | 属性值编号 |

**响应**: CommonResult&lt;ProductPropertyValueRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 属性值编号 |
| propertyId | Long | 属性项的编号 |
| name | String | 属性值名称 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询 `ProductPropertyValueDO`，转换为 `ProductPropertyValueRespVO` 返回（不存在时 data 为 null）。

### 2.5 获得属性值分页

- **路径**: GET /product/property/value/page
- **权限**: product:property:query
- **说明**: 分页查询属性值，支持按属性项编号精确、名称模糊过滤。

**请求参数 (ProductPropertyValuePageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（继承 PageParam，默认 1） |
| pageSize | Integer | 否 | - | 每页条数（继承 PageParam，默认 10） |
| propertyId | String | 否 | - | 属性项的编号（VO 中为 String，查询时精确匹配） |
| name | String | 否 | - | 名称，模糊匹配 |
| status | Integer | 否 | - | 状态（VO 中声明，DO 无此字段，当前查询条件未使用） |

**响应**: CommonResult&lt;PageResult&lt;ProductPropertyValueRespVO&gt;&gt;，列表元素结构同 2.4 的 ProductPropertyValueRespVO。

**业务逻辑**:
1. 按条件构建查询：`propertyId` eq 精确匹配、`name` like 模糊匹配，按 `id` 倒序分页（VO 中的 `status` 未参与查询）。
2. 分页结果转换为 `ProductPropertyValueRespVO` 返回。

### 2.6 获得属性值精简列表

- **路径**: GET /product/property/value/simple-list
- **权限**: 已认证（未标注 @PreAuthorize，仅需登录）
- **说明**: 按属性项编号获取其下属性值精简列表，供前端下拉框选择规格值使用，只返回 id、name。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| propertyId | Long | 是 | @RequestParam required | 属性项编号 |

**响应**: CommonResult&lt;List&lt;ProductPropertyValueRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 属性值编号 |
| name | String | 属性值名称 |

**业务逻辑**:
1. 将传入的 propertyId 包装为单元素集合，调用 `getPropertyValueListByPropertyId` 按 propertyId in 条件查询属性值列表。
2. 仅取 id、name 两个字段组装为精简 `ProductPropertyValueRespVO` 返回。

---

## 附：本域相关错误码汇总（product 模块 1-008-003 / 1-008-004 段）

| 错误码 | 说明 |
|-------|------|
| 1_008_003_000 | 属性项不存在 |
| 1_008_003_001 | 属性项的名称已存在 |
| 1_008_003_002 | 属性项下存在属性值，无法删除 |
| 1_008_004_000 | 属性值不存在 |
| 1_008_004_001 | 属性值的名称已存在 |
