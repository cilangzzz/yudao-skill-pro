# 支付渠道接口 (PayChannelController)

> 管理支付应用（PayApp）下的具体支付渠道（微信、支付宝等）的配置，包括渠道的创建、更新、删除与查询，渠道配置最终用于构建对应的支付客户端 PayClient。

## 接口路径前缀

/pay/channel  (Controller: PayChannelController)

## 1. 支付渠道管理（PayChannelController）

### 1.1 创建支付渠道

- **路径**: POST /pay/channel/create
- **权限**: pay:channel:create
- **说明**: 为指定支付应用新增一个支付渠道，同一应用下渠道编码不可重复。

**请求参数 (PayChannelCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 开启状态（CommonStatusEnum：0 开启、1 禁用） |
| remark | String | 否 | - | 备注 |
| feeRate | Double | 是 | @NotNull | 渠道费率，单位：百分比 |
| appId | Long | 是 | @NotNull | 应用编号 |
| code | String | 是 | @NotNull | 渠道编码，如 alipay_pc、wx_pub 等（枚举 PayChannelEnum） |
| config | String | 是 | @NotBlank | 渠道配置的 JSON 字符串（按渠道编码对应 AlipayPayClientConfig / WxPayClientConfig 等结构） |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的支付渠道编号 |

**业务逻辑**:
1. 根据 appId + code 查询数据库，若已存在相同渠道，抛出 CHANNEL_EXIST_SAME_CHANNEL_ERROR（已存在相同的渠道）。
2. 根据渠道编码 code 判定配置类型：支付宝渠道对应 AlipayPayClientConfig，微信渠道对应 WxPayClientConfig，其他渠道对应 NonePayClientConfig。
3. 将 config JSON 字符串反序列化为对应的 PayClientConfig 对象，并通过 Validator 校验配置参数的合法性（config.validate）。
4. 转换为 PayChannelDO 并插入 pay_channel 表，返回渠道编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |
| 1_007_001_004 | 已存在相同的渠道 |

### 1.2 更新支付渠道

- **路径**: PUT /pay/channel/update
- **权限**: pay:channel:update
- **说明**: 更新指定支付渠道的状态、费率、备注及配置。

**请求参数 (PayChannelUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 渠道编号 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 开启状态 |
| remark | String | 否 | - | 备注 |
| feeRate | Double | 是 | @NotNull | 渠道费率，单位：百分比 |
| appId | Long | 是 | @NotNull | 应用编号 |
| config | String | 是 | @NotBlank | 渠道配置的 JSON 字符串 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 更新成功返回 true |

**业务逻辑**:
1. 校验渠道是否存在，不存在则抛出 CHANNEL_NOT_FOUND。
2. 以数据库中已有渠道的编码 code 判定配置类型，将新的 config JSON 字符串反序列化并通过 Validator 校验。
3. 转换为 PayChannelDO 后按编号更新记录（更新时不修改渠道编码本身）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |

### 1.3 删除支付渠道

- **路径**: DELETE /pay/channel/delete
- **权限**: pay:channel:delete
- **说明**: 按编号删除指定支付渠道。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | -（@RequestParam） | 渠道编号 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**:
1. 校验渠道是否存在，不存在则抛出 CHANNEL_NOT_FOUND。
2. 按编号删除 pay_channel 记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |

### 1.4 获得支付渠道

- **路径**: GET /pay/channel/get
- **权限**: pay:channel:query
- **说明**: 支持两种查询方式：按渠道编号 id 查询，或按应用编号 appId + 渠道编码 code 组合查询。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | -（@RequestParam） | 渠道编号，与 appId+code 二选一 |
| appId | Long | 否 | -（@RequestParam） | 应用编号，需与 code 同时传入 |
| code | String | 否 | -（@RequestParam） | 渠道编码，需与 appId 同时传入 |

**响应**: CommonResult&lt;PayChannelRespVO&gt;（渠道不存在时 data 为 null）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 渠道编号 |
| code | String | 渠道编码 |
| config | String | 渠道配置 |
| status | Integer | 开启状态 |
| remark | String | 备注 |
| feeRate | Double | 渠道费率，单位：百分比 |
| appId | Long | 应用编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 若传入 id，则按编号查询渠道。
2. 否则若同时传入 appId 和 code，则按应用 + 渠道编码查询。
3. 将结果通过 PayChannelConvert 转换为 RespVO 返回。

### 1.5 获得指定应用的支付渠道列表

- **路径**: GET /pay/channel/list
- **权限**: pay:channel:query
- **说明**: 查询指定支付应用下的全部支付渠道（不分页），常用于渠道配置管理界面。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| appId | Long | 是 | -（@RequestParam） | 应用编号 |

**响应**: CommonResult&lt;List&lt;PayChannelRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 渠道编号 |
| code | String | 渠道编码 |
| config | String | 渠道配置 |
| status | Integer | 开启状态 |
| remark | String | 备注 |
| feeRate | Double | 渠道费率，单位：百分比 |
| appId | Long | 应用编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按应用编号 appId 查询该应用下的全部渠道记录。
2. 通过 PayChannelConvert 转换为 RespVO 列表返回。

### 1.6 获得指定应用的开启的支付渠道编码列表

- **路径**: GET /pay/channel/get-enable-code-list
- **权限**: 已认证（仅登录，未声明 @PreAuthorize 权限校验）
- **说明**: 查询指定应用下处于开启状态的渠道编码集合，常用于发起支付前判断可用的支付方式。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| appId | Long | 是 | -（@RequestParam） | 应用编号 |

**响应**: CommonResult&lt;Set&lt;String&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Set&lt;String&gt; | 开启状态的渠道编码集合，如 ["alipay_pc", "wx_pub"] |

**业务逻辑**:
1. 按应用编号 appId 查询状态为开启（CommonStatusEnum.ENABLE）的渠道列表。
2. 提取渠道编码 code 并转为 Set 集合返回。

## 2. 域内错误码汇总（CHANNEL 模块，1-007-001-000 段）

以下错误码属于支付渠道域，除上述端点外，还被 Service 内部方法 validPayChannel / getPayClient 使用（支付发起、退款、转账等流程校验渠道时触发）：

| 错误码 | 说明 |
|-------|------|
| 1_007_001_000 | 支付渠道的配置不存在 |
| 1_007_001_001 | 支付渠道已经禁用 |
| 1_007_001_004 | 已存在相同的渠道 |
