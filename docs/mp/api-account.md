# 公众号账号接口 (MpAccountController)

> 管理微信公众号账号（appId/appSecret 等接入配置），提供账号的增删改查、二维码生成与 API 配额清空能力，并在后台维护全局账号缓存供消息回调路由使用。

## 接口路径前缀

/mp/account  (Controller: MpAccountController)

---

## 1. 账号管理

### 1.1 创建公众号账号

- **路径**: POST /mp/account/create
- **权限**: mp:account:create
- **说明**: 创建一个新的公众号账号配置，校验 appId 全局唯一后入库并刷新本地缓存。

**请求参数 (MpAccountCreateReqVO)**: 继承 MpAccountBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 是 | @NotEmpty | 公众号名称，如「芋道源码」 |
| account | String | 是 | @NotEmpty | 公众号微信号，如「yudaoyuanma」 |
| appId | String | 是 | @NotEmpty | 公众号 appId，如「wx5b23ba7a5589ecbb」 |
| appSecret | String | 是 | @NotEmpty | 公众号密钥 |
| token | String | 是 | @NotEmpty | 公众号 token |
| aesKey | String | 否 | - | 加密密钥（明文模式/兼容模式下无需填写） |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;（新创建的账号编号）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 账号编号 id |

**业务逻辑**:
1. 校验 appId 全局唯一：忽略多租户隔离（TenantUtils.executeIgnore）查询同 appId 的账号，若已存在（新增场景或更新时 id 不一致）则抛出异常（复用 system 模块的 USER_USERNAME_EXISTS 错误码）。appId 全局不能重复，否则公众号回调无法识别归属账号。
2. 通过 MpAccountConvert 将请求 VO 转换为 MpAccountDO，插入数据库。
3. 调用 initLocalCache() 刷新本地账号缓存，并重建 MpServiceFactory 中的 WxMpService 客户端。
4. 返回新账号的编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_003_000 | 用户账号已经存在（appId 重复时复用该错误码） |

---

### 1.2 更新公众号账号

- **路径**: PUT /mp/account/update
- **权限**: mp:account:update
- **说明**: 更新指定公众号账号的配置信息，校验存在性与 appId 唯一性后更新并刷新缓存。

**请求参数 (MpAccountUpdateReqVO)**: 继承 MpAccountBaseVO

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 账号编号 |
| name | String | 是 | @NotEmpty | 公众号名称 |
| account | String | 是 | @NotEmpty | 公众号微信号 |
| appId | String | 是 | @NotEmpty | 公众号 appId |
| appSecret | String | 是 | @NotEmpty | 公众号密钥 |
| token | String | 是 | @NotEmpty | 公众号 token |
| aesKey | String | 否 | - | 加密密钥 |
| remark | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否成功 |

**业务逻辑**:
1. 校验账号存在：按 id 查询，不存在则抛出 ACCOUNT_NOT_EXISTS。
2. 校验 appId 全局唯一（同创建逻辑，忽略多租户，排除自身 id）。
3. 转换为 MpAccountDO 后按 id 更新数据库。
4. 刷新本地账号缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_002_003_000 | 用户账号已经存在（appId 重复时复用该错误码） |

---

### 1.3 删除公众号账号

- **路径**: DELETE /mp/account/delete
- **权限**: mp:account:delete
- **说明**: 删除指定公众号账号，删除后刷新本地缓存。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必填 | 账号编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否成功 |

**业务逻辑**:
1. 校验账号存在，不存在则抛出 ACCOUNT_NOT_EXISTS。
2. 按 id 删除账号记录。
3. 刷新本地账号缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |

---

### 1.4 获得公众号账号详情

- **路径**: GET /mp/account/get
- **权限**: mp:account:query
- **说明**: 按编号查询单个公众号账号的完整配置。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必填 | 账号编号，示例 1024 |

**响应**: CommonResult&lt;MpAccountRespVO&gt;，MpAccountRespVO 继承 MpAccountBaseVO

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 账号编号 |
| name | String | 公众号名称 |
| account | String | 公众号微信号 |
| appId | String | 公众号 appId |
| appSecret | String | 公众号密钥 |
| token | String | 公众号 token |
| aesKey | String | 加密密钥 |
| remark | String | 备注 |
| qrCodeUrl | String | 二维码图片 URL |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询 MpAccountDO（不存在时返回 null，由前端处理）。
2. 通过 MpAccountConvert 转换为 RespVO 返回。

---

### 1.5 获得公众号账号分页

- **路径**: GET /mp/account/page
- **权限**: mp:account:query
- **说明**: 分页查询公众号账号列表，支持名称/微信号/appId 模糊匹配。

**请求参数 (MpAccountPageReqVO)**: 继承 PageParam

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，最大 200，默认 10 |
| name | String | 否 | - | 公众号名称，模糊匹配 |
| account | String | 否 | - | 公众号账号，模糊匹配 |
| appId | String | 否 | - | 公众号 appid，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;MpAccountRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | MpAccountRespVO[] | 账号列表，字段同「1.4 获得公众号账号详情」响应 |
| total | Long | 总条数 |

**业务逻辑**:
1. 组装分页与模糊查询条件，调用 MpAccountMapper.selectPage 查询分页结果。
2. 通过 MpAccountConvert.convertPage 转换为 RespVO 分页对象返回。

---

### 1.6 获取公众号账号精简信息列表

- **路径**: GET /mp/account/list-all-simple
- **权限**: mp:account:query
- **说明**: 查询全部账号的精简信息（id + name），用于下拉框选择公众号场景。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MpAccountSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 账号编号 |
| name | String | 公众号名称 |

**业务逻辑**:
1. 调用 MpAccountMapper.selectList 查询全部账号。
2. 通过 MpAccountConvert.convertList02 转换为精简 RespVO 列表返回。

---

## 2. 运维操作

### 2.1 生成公众号二维码

- **路径**: PUT /mp/account/generate-qr-code
- **权限**: mp:account:qr-code
- **说明**: 调用微信接口生成公众号二维码，并将图片 URL 持久化到账号记录。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必填 | 账号编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否成功 |

**业务逻辑**:
1. 校验账号存在，不存在则抛出 ACCOUNT_NOT_EXISTS。
2. 通过 MpServiceFactory 按 appId 获取对应的 WxMpService 实例。
3. 调用微信二维码服务 qrCodeCreateLastTicket("default") 创建永久二维码 ticket，再通过 qrCodePictureUrl 拼出二维码图片 URL。
4. 微信调用失败（WxErrorException）时抛出 ACCOUNT_GENERATE_QR_CODE_FAIL，附带微信返回的错误信息。
5. 将生成的二维码 URL 更新到账号记录的 qrCodeUrl 字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_000_001 | 生成公众号二维码失败，原因：{} |

---

### 2.2 清空公众号 API 配额

- **路径**: PUT /mp/account/clear-quota
- **权限**: mp:account:clear-quota
- **说明**: 调用微信接口清空该公众号的 API 调用配额（当日调用次数重置）。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam 必填 | 账号编号 |

**响应**: CommonResult&lt;Boolean&gt;（固定返回 true）

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否成功 |

**业务逻辑**:
1. 校验账号存在，不存在则抛出 ACCOUNT_NOT_EXISTS。
2. 通过 MpServiceFactory 按 appId 获取对应的 WxMpService 实例。
3. 调用 mpService.clearQuota(appId) 清空微信 API 配额。
4. 微信调用失败（WxErrorException）时抛出 ACCOUNT_CLEAR_QUOTA_FAIL，附带微信返回的错误信息。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_000_002 | 清空公众号的 API 配额失败，原因：{} |

---

## 附：账号缓存机制说明

MpAccountServiceImpl 内部维护 `volatile Map<String, MpAccountDO> accountCache`（key 为 appId）：

1. **初始化**：@PostConstruct 时执行 initLocalCache()，忽略多租户（TenantUtils.executeIgnore）查询全部账号，构建缓存并调用 MpServiceFactory.init(accounts) 创建各账号的 WxMpService 客户端。若表不存在（表结构未导入），仅记录 error 日志并跳过，避免启动失败。
2. **定时刷新**：@Scheduled 每 60 秒执行 refreshLocalCache()：缓存为空时直接重建；否则取缓存中最大 updateTime，若存在更新时间更晚的记录则触发 initLocalCache() 全量刷新，用于多节点部署下的最终一致。
