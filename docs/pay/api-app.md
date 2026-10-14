# 支付应用接口 (PayAppController)

> 支付应用是商户业务接入支付能力的主体，每个应用拥有全局唯一的 appKey 及支付/退款/转账回调地址；本域提供支付应用的创建、修改、状态管理、删除与查询。

## 接口路径前缀
/pay/app  (Controller: PayAppController)

## 1. 应用管理

### 1.1 创建支付应用
- **路径**: POST /pay/app/create
- **权限**: pay:app:create
- **说明**: 创建一个支付应用，应用标识 appKey 全局唯一。

**请求参数 (PayAppCreateReqVO)**（继承 PayAppBaseVO 全部字段）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| appKey | String | 是 | @NotEmpty | 应用标识，全局唯一 |
| name | String | 是 | @NotNull | 应用名 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 开启状态（0 开启、1 禁用） |
| remark | String | 否 | - | 备注 |
| orderNotifyUrl | String | 是 | @NotNull、@URL | 支付结果的回调地址 |
| refundNotifyUrl | String | 是 | @NotNull、@URL | 退款结果的回调地址 |
| transferNotifyUrl | String | 否 | @URL | 转账结果的回调地址 |

**响应**: CommonResult&lt;Long&gt;，返回新创建的应用编号。

**业务逻辑**:
1. 校验 appKey 是否已被占用（selectByAppKey 查重，存在即抛 APP_KEY_EXISTS）
2. 将请求 VO 转换为 PayAppDO 并插入数据库
3. 返回新应用的编号

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_007_000_005 | 支付应用标识已经存在 |

### 1.2 更新支付应用
- **路径**: PUT /pay/app/update
- **权限**: pay:app:update
- **说明**: 更新指定支付应用的基础信息。

**请求参数 (PayAppUpdateReqVO)**（继承 PayAppBaseVO，字段同 1.1，另增加）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @NotNull | 应用编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验应用是否存在（不存在抛 APP_NOT_FOUND）
2. 校验修改后的 appKey 不与其他应用冲突（排除自身 id，冲突抛 APP_KEY_EXISTS）
3. 将请求 VO 转换为 PayAppDO 后按 id 更新

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_007_000_000 | App 不存在 |
| 1_007_000_005 | 支付应用标识已经存在 |

### 1.3 更新支付应用状态
- **路径**: PUT /pay/app/update-status
- **权限**: pay:app:update
- **说明**: 开启或禁用指定支付应用。

**请求参数 (PayAppUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | @NotNull | 应用编号 |
| status | Integer | 是 | @NotNull | 状态（0 开启、1 禁用，见 CommonStatusEnum 枚举） |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验应用是否存在（不存在抛 APP_NOT_FOUND）
2. 仅更新该应用的 status 字段（new PayAppDO().setId(id).setStatus(status)）

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_007_000_000 | App 不存在 |

### 1.4 删除支付应用
- **路径**: DELETE /pay/app/delete
- **权限**: pay:app:delete
- **说明**: 删除支付应用；存在关联支付订单或退款订单时禁止删除。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | - | 应用编号 |

**响应**: CommonResult&lt;Boolean&gt;，固定返回 true。

**业务逻辑**:
1. 校验应用是否存在（不存在抛 APP_NOT_FOUND）
2. 若该应用下存在支付订单（orderService.getOrderCountByAppId(id) > 0），抛 APP_EXIST_ORDER_CANT_DELETE
3. 若该应用下存在退款订单（refundService.getRefundCountByAppId(id) > 0），抛 APP_EXIST_REFUND_CANT_DELETE
4. 按编号删除应用

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 1_007_000_000 | App 不存在 |
| 1_007_000_003 | 支付应用存在支付订单，无法删除 |
| 1_007_000_004 | 支付应用存在退款订单，无法删除 |

## 2. 应用查询

### 2.1 获得支付应用
- **路径**: GET /pay/app/get
- **权限**: pay:app:query
- **说明**: 按编号获取单个支付应用详情。

**请求参数**（Query 参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| id | Long | 是 | - | 应用编号 |

**响应**: CommonResult&lt;PayAppRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 应用编号 |
| appKey | String | 应用标识 |
| name | String | 应用名 |
| status | Integer | 开启状态（0 开启、1 禁用） |
| remark | String | 备注 |
| orderNotifyUrl | String | 支付结果的回调地址 |
| refundNotifyUrl | String | 退款结果的回调地址 |
| transferNotifyUrl | String | 转账结果的回调地址 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按编号查询支付应用（PayAppMapper.selectById）
2. 转换为 PayAppRespVO 返回；应用不存在时返回空数据，不抛错

### 2.2 获得支付应用分页
- **路径**: GET /pay/app/page
- **权限**: pay:app:query
- **说明**: 分页查询支付应用，并在结果中拼接每个应用已启用的支付渠道编码。

**请求参数 (PayAppPageReqVO)**（继承 PageParam 分页参数）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|----------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| name | String | 否 | - | 应用名，LIKE 模糊查询 |
| appKey | String | 否 | - | 应用标识，LIKE 模糊查询 |
| status | Integer | 否 | - | 开启状态，精确匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间范围（起止） |

**响应**: CommonResult&lt;PageResult&lt;PayAppPageItemRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 应用编号 |
| appKey | String | 应用标识 |
| name | String | 应用名 |
| status | Integer | 开启状态（0 开启、1 禁用） |
| remark | String | 备注 |
| orderNotifyUrl | String | 支付结果的回调地址 |
| refundNotifyUrl | String | 退款结果的回调地址 |
| transferNotifyUrl | String | 转账结果的回调地址 |
| createTime | LocalDateTime | 创建时间 |
| channelCodes | Set&lt;String&gt; | 已配置且处于启用状态的支付渠道编码集合（如 [alipay_pc, alipay_wap]） |

**业务逻辑**:
1. 按条件分页查询支付应用（name/appKey 模糊、status 精确、createTime 区间，按 id 倒序）
2. 若分页结果为空，直接返回空分页
3. 根据分页内所有应用编号，批量查询关联的支付渠道（channelService.getChannelListByAppIds）
4. 过滤掉未启用（非 CommonStatusEnum.ENABLE 状态）的渠道
5. 通过 PayAppConvert.convertPage 将渠道信息拼接进每条应用记录（channelCodes）后返回

### 2.3 获得应用列表
- **路径**: GET /pay/app/list
- **权限**: pay:merchant:query（复用商户查询权限）
- **说明**: 查询全部支付应用，返回精简列表（常用于下拉选择等场景）。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;PayAppRespVO&gt;&gt;，元素字段同 2.1 响应表。

**业务逻辑**:
1. 查询全部支付应用列表（PayAppMapper.selectList）
2. 转换为 PayAppRespVO 列表返回

## 域错误码总览（1_007_000_XXX 段）

| 错误码 | 说明 | 触发场景 |
|--------|------|----------|
| 1_007_000_000 | App 不存在 | 更新/改状态/删除时应用不存在 |
| 1_007_000_002 | App 已经被禁用 | 内部校验 validPayApp（支付/退款/转账发起时校验应用有效），admin 端点不直接抛出 |
| 1_007_000_003 | 支付应用存在支付订单，无法删除 | 删除应用时存在关联支付订单 |
| 1_007_000_004 | 支付应用存在退款订单，无法删除 | 删除应用时存在关联退款订单 |
| 1_007_000_005 | 支付应用标识已经存在 | 创建/更新时 appKey 重复 |
