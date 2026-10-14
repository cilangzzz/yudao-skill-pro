# 分销接口 (BrokerageUserController / BrokerageRecordController / BrokerageWithdrawController)

> 管理后台分销域接口：管理分销用户（推广员绑定与推广资格）、查询佣金记录、审核佣金提现申请并处理转账结果回调。

## 接口路径前缀

- /trade/brokerage-user  (Controller: BrokerageUserController) —— 分销用户
- /trade/brokerage-record  (Controller: BrokerageRecordController) —— 佣金记录
- /trade/brokerage-withdraw  (Controller: BrokerageWithdrawController) —— 佣金提现

---

## 1. 分销用户（BrokerageUserController）

### 1.1 创建分销用户
- **路径**: POST /trade/brokerage-user/create
- **权限**: trade:brokerage-user:create
- **说明**: 手动创建一条分销用户记录（以会员编号作为分销用户编号），并绑定指定推广员。

**请求参数 (BrokerageUserCreateReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 分销用户编号（即会员编号） |
| bindUserId | Long | 是 | @NotNull | 推广员编号 |

**响应**: CommonResult&lt;Long&gt;（分销用户编号）

**业务逻辑**:
1. 校验分销用户是否已存在，已存在则抛出 `BROKERAGE_CREATE_USER_EXISTS` 错误。
2. 以 userId 为主键构造 BrokerageUserDO（记录成为分销员时间），调用 validateCanBindUser 校验绑定关系。
3. 校验内容包括：推广员（会员）必须存在、推广员必须已开通推广资格、不能绑定自己、下级不能绑定自己的上级（防止循环绑定）。
4. 插入分销用户记录，返回编号。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_007_000 | 分销用户不存在 |
| 1_011_007_002 | 不能绑定自己 |
| 1_011_007_003 | 绑定用户没有推广资格 |
| 1_011_007_007 | 下级不能绑定自己的上级 |
| 1_011_007_009 | 分销用户已存在 |

### 1.2 修改推广员
- **路径**: PUT /trade/brokerage-user/update-bind-user
- **权限**: trade:brokerage-user:update-bind-user
- **说明**: 修改分销用户绑定的推广员。

**请求参数 (BrokerageUserUpdateBrokerageUserReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| bindUserId | Long | 是 | @NotNull | 推广员编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验分销用户存在，不存在抛出 `BROKERAGE_USER_NOT_EXISTS`。
2. 若绑定关系未发生变化（bindUserId 相同），直接返回。
3. 修改推广员时执行 validateCanBindUser 校验：推广员存在、有推广资格、不能绑定自己、不能形成循环绑定。
4. 更新 bindUserId 并记录绑定时间 bindUserTime。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_007_000 | 分销用户不存在 |
| 1_011_007_002 | 不能绑定自己 |
| 1_011_007_003 | 绑定用户没有推广资格 |
| 1_011_007_007 | 下级不能绑定自己的上级 |

### 1.3 清除推广员
- **路径**: PUT /trade/brokerage-user/clear-bind-user
- **权限**: trade:brokerage-user:clear-bind-user
- **说明**: 清除分销用户已绑定的推广员。

**请求参数 (BrokerageUserClearBrokerageUserReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验分销用户存在。
2. 若绑定关系未发生变化，直接返回。
3. 将 bindUserId 与 bindUserTime 置空。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_007_000 | 分销用户不存在 |

### 1.4 修改推广资格
- **路径**: PUT /trade/brokerage-user/update-brokerage-enable
- **权限**: trade:brokerage-user:update-brokerage-enable
- **说明**: 开通或取消分销用户的推广资格。

**请求参数 (BrokerageUserUpdateBrokerageEnabledReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 用户编号 |
| enabled | Boolean | 是 | @NotNull | 推广资格（true 开通 / false 取消） |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验分销用户存在。
2. 开通（enabled=true）：更新 brokerageEnabled 为 true，并记录成为分销员时间 brokerageTime。
3. 取消（enabled=false）：更新 brokerageEnabled 为 false，并清空 brokerageTime。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_007_000 | 分销用户不存在 |

### 1.5 获得分销用户
- **路径**: GET /trade/brokerage-user/get
- **权限**: trade:brokerage-user:query
- **说明**: 按 id 获得分销用户详情。

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult&lt;BrokerageUserRespVO&gt;
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户编号 |
| bindUserId | Long | 推广员编号 |
| bindUserTime | LocalDateTime | 推广员绑定时间 |
| brokerageEnabled | Boolean | 推广资格 |
| brokerageTime | LocalDateTime | 成为分销员时间 |
| price | Integer | 可用佣金 |
| frozenPrice | Integer | 冻结佣金 |
| createTime | LocalDateTime | 创建时间 |
| avatar | String | 用户头像（来自会员模块） |
| nickname | String | 用户昵称（来自会员模块） |
| brokerageUserCount | Integer | 推广用户数量（1+2 级，仅分页接口填充） |
| brokerageOrderCount | Integer | 推广订单数量（仅分页接口填充） |
| brokerageOrderPrice | Integer | 推广订单金额（仅分页接口填充） |
| withdrawPrice | Integer | 已提现金额（仅分页接口填充） |
| withdrawCount | Integer | 已提现次数（仅分页接口填充） |

**业务逻辑**:
1. 查询分销用户记录。
2. 转换为 BrokerageUserRespVO。
3. 通过 MemberUserApi 查询会员信息，复制用户头像、昵称等字段。

### 1.6 获得分销用户分页
- **路径**: GET /trade/brokerage-user/page
- **权限**: trade:brokerage-user:query
- **说明**: 分页获得分销用户列表，并聚合推广、提现统计信息。

**请求参数 (BrokerageUserPageReqVO，继承 PageParam)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| bindUserId | Long | 否 | - | 推广员编号 |
| brokerageEnabled | Boolean | 否 | - | 推广资格 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间区间 |
| level | Integer | 否 | - | 推广层级（1 或 2，非会员等级；为空查 1+2 级） |
| bindUserTime | LocalDateTime[] | 否 | @DateTimeFormat | 绑定时间区间 |

**响应**: CommonResult&lt;PageResult&lt;BrokerageUserRespVO&gt;&gt;（字段同 1.5，其中推广/提现统计字段均有值）

**业务逻辑**:
1. 根据推广员编号 + 层级 level 递归查询下级用户编号列表（level=1 只查一级、level=2 只查二级、为空查 1+2 级；level 不支持时抛 `BROKERAGE_USER_LEVEL_NOT_SUPPORT`）。
2. 指定推广员编号但查不到下级时直接返回空分页，否则按条件分页查询。
3. 批量查询会员用户信息（头像、昵称）。
4. 合计已结算（SETTLEMENT）推广订单类型佣金的订单数量与金额。
5. 统计每个用户的推广用户数量（1+2 级）。
6. 合计审核通过 + 提现成功状态的提现金额与提现次数。
7. 拼接转换后返回。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_007_008 | 目前只支持 level 小于等于 2 |

---

## 2. 佣金记录（BrokerageRecordController）

### 2.1 获得佣金记录
- **路径**: GET /trade/brokerage-record/get
- **权限**: trade:brokerage-record:query
- **说明**: 按 id 获得佣金记录详情。

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult&lt;BrokerageRecordRespVO&gt;
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| bizId | String | 业务编号 |
| bizType | Integer | 业务类型（1 获得推广佣金 / 2 提现申请 / 3 提现申请驳回） |
| title | String | 标题 |
| price | Integer | 金额 |
| totalPrice | Integer | 当前总佣金 |
| description | String | 说明 |
| status | Integer | 状态（等待结算 / 已结算 / 已失效） |
| frozenDays | Integer | 冻结时间（天） |
| unfreezeTime | LocalDateTime | 解冻时间 |
| sourceUserLevel | Integer | 来源用户等级（1/2 级推广） |
| sourceUserId | Long | 来源用户编号 |
| createTime | LocalDateTime | 创建时间 |
| userAvatar | String | 用户头像（来自会员模块） |
| userNickname | String | 用户昵称（来自会员模块） |
| sourceUserAvatar | String | 来源用户头像（来自会员模块） |
| sourceUserNickname | String | 来源用户昵称（来自会员模块） |

**业务逻辑**:
1. 按 id 查询佣金记录。
2. 转换为 BrokerageRecordRespVO 返回（不拼接用户信息）。

### 2.2 获得佣金记录分页
- **路径**: GET /trade/brokerage-record/page
- **权限**: trade:brokerage-record:query
- **说明**: 分页获得佣金记录列表，拼接用户与来源用户信息。

**请求参数 (BrokerageRecordPageReqVO，继承 PageParam)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| userId | Long | 否 | - | 用户编号 |
| bizType | Integer | 否 | - | 业务类型 |
| status | Integer | 否 | - | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间区间 |
| sourceUserLevel | Integer | 否 | - | 用户类型（来源用户等级） |

**响应**: CommonResult&lt;PageResult&lt;BrokerageRecordRespVO&gt;&gt;（字段同 2.1）

**业务逻辑**:
1. 按条件分页查询佣金记录。
2. 收集记录中的 userId 与 sourceUserId，批量查询会员用户信息。
3. 拼接用户头像/昵称、来源用户头像/昵称后返回。

---

## 3. 佣金提现（BrokerageWithdrawController）

### 3.1 通过申请
- **路径**: PUT /trade/brokerage-withdraw/approve
- **权限**: trade:brokerage-withdraw:audit
- **说明**: 审核通过佣金提现申请，并根据提现类型自动打款或标记手动打款完成。

**请求参数**: 无（Query 参数 `id`：提现单编号，必填）

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验提现单存在；若状态为“提现失败”，先将其重置为“审核中”并清空转账错误信息（重新转账场景）。
2. 校验提现单状态必须为“审核中”，否则抛出 `BROKERAGE_WITHDRAW_STATUS_NOT_AUDITING`。
3. 乐观更新提现单状态为“审核通过”，记录审核原因与审核时间。
4. API 自动打款类型（钱包 / 微信零钱 / 支付宝余额）：按类型确定支付渠道（钱包需先获取或创建会员钱包，微信需附加报备信息），以（提现金额 - 手续费）作为转账金额调用 pay 模块创建转账单，并回写 payTransferId 与转账渠道编码，转账结果由支付回调异步更新。
5. 非 API 类型（银行卡、微信/支付宝收款码手动打款）：直接将状态更新为“提现成功”。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_008_000 | 佣金提现记录不存在 |
| 1_011_008_001 | 佣金提现记录状态不是审核中 |

### 3.2 驳回申请
- **路径**: PUT /trade/brokerage-withdraw/reject
- **权限**: trade:brokerage-withdraw:audit
- **说明**: 驳回佣金提现申请，并将提现时扣减的佣金返还给用户。

**请求参数 (BrokerageWithdrawRejectReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 编号 |
| auditReason | String | 是 | @NotEmpty | 审核驳回原因 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 校验提现单存在，且状态为“审核中”（提现失败状态同样会先重置为审核中，支持重新审核）。
2. 更新提现单状态为“审核不通过”，记录驳回原因与审核时间。
3. 以 WITHDRAW_REJECT（提现申请驳回）业务类型新增一条正向佣金记录，将提现扣减的佣金返还到用户可用佣金（返还前校验佣金余额）。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_008_000 | 佣金提现记录不存在 |
| 1_011_008_001 | 佣金提现记录状态不是审核中 |
| 1_011_008_003 | 您当前最多可提现 {} 元（返还佣金时余额不足） |

### 3.3 获得佣金提现
- **路径**: GET /trade/brokerage-withdraw/get
- **权限**: trade:brokerage-withdraw:query
- **说明**: 按 id 获得佣金提现详情。

**请求参数**: 无（Query 参数 `id`：编号，必填）

**响应**: CommonResult&lt;BrokerageWithdrawRespVO&gt;
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| userNickname | String | 用户昵称（来自会员模块） |
| price | Integer | 提现金额 |
| feePrice | Integer | 提现手续费 |
| totalPrice | Integer | 当前总佣金 |
| type | Integer | 提现类型（1 钱包 / 2 银行卡 / 3 微信收款码 / 4 支付宝收款码 / 5 微信零钱 / 6 支付宝余额） |
| userName | String | 真实姓名 |
| userAccount | String | 收款账号 |
| bankName | String | 银行名称 |
| bankAddress | String | 开户地址 |
| qrCodeUrl | String | 收款码 |
| status | Integer | 状态（0 审核中 / 10 审核通过 / 11 提现成功 / 20 审核不通过 / 21 提现失败） |
| auditReason | String | 审核驳回原因 |
| auditTime | LocalDateTime | 审核时间 |
| remark | String | 备注 |
| payTransferId | Long | 转账单编号 |
| transferErrorMsg | String | 转账错误提示 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询提现单。
2. 转换为 BrokerageWithdrawRespVO 返回（不拼接用户信息）。

### 3.4 获得佣金提现分页
- **路径**: GET /trade/brokerage-withdraw/page
- **权限**: trade:brokerage-withdraw:query
- **说明**: 分页获得佣金提现列表，拼接用户昵称。

**请求参数 (BrokerageWithdrawPageReqVO，继承 PageParam)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | - | 页码（PageParam） |
| pageSize | Integer | 否 | - | 每页条数（PageParam） |
| userId | Long | 否 | - | 用户编号 |
| type | Integer | 否 | @InEnum(BrokerageWithdrawTypeEnum) | 提现类型 |
| userName | String | 否 | - | 真实姓名 |
| userAccount | String | 否 | - | 账号 |
| bankName | String | 否 | - | 银行名称 |
| status | Integer | 否 | @InEnum(BrokerageWithdrawStatusEnum) | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;BrokerageWithdrawRespVO&gt;&gt;（字段同 3.3）

**业务逻辑**:
1. 按条件分页查询提现单。
2. 批量查询会员用户信息，拼接用户昵称后返回。

### 3.5 更新佣金提现的转账结果
- **路径**: POST /trade/brokerage-withdraw/update-transferred
- **权限**: @PermitAll（无需登录，由 pay 模块支付服务回调，见 PayNotifyJob；安全性由 Service 内部校验保证）
- **说明**: 接收 pay 模块转账结果通知，更新提现单为提现成功或提现失败。

**请求参数 (PayTransferNotifyReqDTO，pay 模块回调请求体)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| merchantTransferId | String | 是 | - | 商户转账单号（即提现单编号） |
| payTransferId | Long | 是 | - | 支付转账单编号 |

**响应**: CommonResult&lt;Boolean&gt;（是否成功）

**业务逻辑**:
1. 以 merchantTransferId 解析提现单编号，校验提现单存在。
2. 若提现单已结束（提现成功/提现失败）：转账单编号相同视为重复回调直接返回；不同则抛出转账单不匹配错误。
3. 校验转账单合法性：转账单存在、状态为成功或关闭、转账金额（提现金额 - 手续费）一致、商户转账单号匹配、转账渠道一致。
4. 转账成功则更新提现单为“提现成功”，转账关闭则更新为“提现失败”，并记录转账时间与渠道错误信息。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_011_008_000 | 佣金提现记录不存在 |
| 1_011_008_005 | 提现单更新转账状态失败，转账单不匹配 |
| 1_011_008_006 | 提现单更新转账状态失败，转账单状态不是成功或关闭状态 |
| 1_011_008_007 | 提现单更新转账状态失败，转账单金额不匹配 |
| 1_011_008_008 | 提现单更新转账状态失败，转账单的商户订单不匹配 |
| 1_011_008_009 | 提现单更新转账状态失败，转账渠道不匹配 |

---

## 附：分销域错误码汇总（trade 模块 1_011_007 / 1_011_008 段）

| 错误码 | 说明 |
|-------|------|
| 1_011_007_000 | 分销用户不存在 |
| 1_011_007_001 | 用户冻结佣金({})数量不足 |
| 1_011_007_002 | 不能绑定自己 |
| 1_011_007_003 | 绑定用户没有推广资格 |
| 1_011_007_004 | 仅可在后台绑定推广员 |
| 1_011_007_005 | 只有在注册时可以绑定 |
| 1_011_007_006 | 已绑定了推广人 |
| 1_011_007_007 | 下级不能绑定自己的上级 |
| 1_011_007_008 | 目前只支持 level 小于等于 2 |
| 1_011_007_009 | 分销用户已存在 |
| 1_011_008_000 | 佣金提现记录不存在 |
| 1_011_008_001 | 佣金提现记录状态不是审核中 |
| 1_011_008_002 | 提现金额不能低于 {} 元 |
| 1_011_008_003 | 您当前最多可提现 {} 元 |
| 1_011_008_005 | 提现单更新转账状态失败，转账单不匹配 |
| 1_011_008_006 | 提现单更新转账状态失败，转账单状态不是成功或关闭状态 |
| 1_011_008_007 | 提现单更新转账状态失败，转账单金额不匹配 |
| 1_011_008_008 | 提现单更新转账状态失败，转账单的商户订单不匹配 |
| 1_011_008_009 | 提现单更新转账状态失败，转账渠道不匹配 |
