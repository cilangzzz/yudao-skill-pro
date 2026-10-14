# 邮件管理接口 (MailAccountController / MailTemplateController / MailLogController)

> 提供邮箱账号管理、邮件模板管理与邮件发送日志查询能力，支持基于模板的异步邮件发送（含抄送/密送）。

## 接口路径前缀
- /system/mail-account  (Controller: MailAccountController)
- /system/mail-template  (Controller: MailTemplateController)
- /system/mail-log  (Controller: MailLogController)

---

## 1. 邮箱账号（MailAccountController）

### 1.1 创建邮箱账号
- **路径**: POST /system/mail-account/create
- **权限**: system:mail-account:create
- **说明**: 新增一个 SMTP 邮箱账号，返回账号编号。

**请求参数 (MailAccountSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（创建时无需传） |
| mail | String | 是 | @NotNull、@Email | 邮箱地址 |
| username | String | 是 | @NotNull | 用户名 |
| password | String | 是 | @NotNull | 密码 |
| host | String | 是 | @NotNull | SMTP 服务器域名 |
| port | Integer | 是 | @NotNull | SMTP 服务器端口 |
| sslEnable | Boolean | 是 | @NotNull | 是否开启 ssl |
| starttlsEnable | Boolean | 是 | @NotNull | 是否开启 starttls |

**响应**: CommonResult<Long>，数据为新建邮箱账号的编号。

**业务逻辑**: 1. 将 ReqVO 转换为 MailAccountDO；2. 插入数据库；3. 返回自增主键 id。

### 1.2 修改邮箱账号
- **路径**: PUT /system/mail-account/update
- **权限**: system:mail-account:update
- **说明**: 按编号修改邮箱账号信息。

**请求参数 (MailAccountSaveReqVO)**: 与 1.1 相同，但 id 必传（更新目标编号）。

**响应**: CommonResult<Boolean>，固定返回 true。

**业务逻辑**: 1. 校验账号是否存在，不存在抛 MAIL_ACCOUNT_NOT_EXISTS；2. 转换为 MailAccountDO 按 id 更新；3. 通过 @CacheEvict 清理该账号的 Redis 缓存（MAIL_ACCOUNT）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_023_000 | 邮箱账号不存在 |

### 1.3 删除邮箱账号
- **路径**: DELETE /system/mail-account/delete
- **权限**: system:mail-account:delete
- **说明**: 删除单个邮箱账号，若存在关联邮件模板则拒绝删除。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 邮箱账号编号 |

**响应**: CommonResult<Boolean>，固定返回 true。

**业务逻辑**: 1. 校验账号是否存在，不存在抛 MAIL_ACCOUNT_NOT_EXISTS；2. 统计该账号下邮件模板数量，大于 0 则抛 MAIL_ACCOUNT_RELATE_TEMPLATE_EXISTS；3. 按 id 删除并清理该账号缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_023_000 | 邮箱账号不存在 |
| 1_002_023_001 | 无法删除，该邮箱账号还有邮件模板 |

### 1.4 批量删除邮箱账号
- **路径**: DELETE /system/mail-account/delete-list
- **权限**: system:mail-account:delete
- **说明**: 按编号列表批量删除邮箱账号，任一账号存在关联模板则整体失败。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam("ids") | 邮箱账号编号列表 |

**响应**: CommonResult<Boolean>，固定返回 true。

**业务逻辑**: 1. 逐个校验每个账号下是否存在关联邮件模板，存在则抛 MAIL_ACCOUNT_RELATE_TEMPLATE_EXISTS；2. 批量删除；3. 通过 @CacheEvict(allEntries=true) 清空 MAIL_ACCOUNT 全部缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_023_001 | 无法删除，该邮箱账号还有邮件模板 |

### 1.5 获得邮箱账号
- **路径**: GET /system/mail-account/get
- **权限**: system:mail-account:query
- **说明**: 按编号查询单个邮箱账号详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 邮箱账号编号 |

**响应**: CommonResult&lt;MailAccountRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| mail | String | 邮箱 |
| username | String | 用户名 |
| password | String | 密码 |
| host | String | SMTP 服务器域名 |
| port | Integer | SMTP 服务器端口 |
| sslEnable | Boolean | 是否开启 ssl |
| starttlsEnable | Boolean | 是否开启 starttls |
| createTime | LocalDateTime | 创建时间 |

### 1.6 获得邮箱账号分页
- **路径**: GET /system/mail-account/page
- **权限**: system:mail-account:query
- **说明**: 分页查询邮箱账号，支持按邮箱、用户名过滤。

**请求参数 (MailAccountPageReqVO)**: 继承 PageParam（pageNo 页码从 1 开始、pageSize 每页条数最大 200）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码，默认 1 |
| pageSize | Integer | 否 | | 每页条数，默认 10 |
| mail | String | 否 | | 邮箱，模糊匹配 |
| username | String | 否 | | 用户名，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;MailAccountRespVO&gt;&gt;，list 元素结构同 1.5 响应。

### 1.7 获得邮箱账号精简列表
- **路径**: GET /system/mail-account/list-all-simple（兼容 GET /system/mail-account/simple-list）
- **权限**: 已认证（未加 @PreAuthorize）
- **说明**: 返回全部邮箱账号精简列表，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MailAccountSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 邮箱编号 |
| mail | String | 邮箱 |

---

## 2. 邮件模板（MailTemplateController）

### 2.1 创建邮件模板
- **路径**: POST /system/mail-template/create
- **权限**: system:mail-template:create
- **说明**: 新增邮件模板，自动从标题/内容中解析 `{key}` 形式的模板参数。

**请求参数 (MailTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（创建时无需传） |
| name | String | 是 | @NotNull | 模版名称 |
| code | String | 是 | @NotNull | 模版编码，全局唯一 |
| accountId | Long | 是 | @NotNull | 发送使用的邮箱账号编号 |
| nickname | String | 否 | | 发送人名称 |
| title | String | 是 | @NotEmpty | 邮件标题，支持 `{key}` 变量 |
| content | String | 是 | @NotEmpty | 邮件内容，支持 `{key}` 变量 |
| status | Integer | 是 | @NotNull | 状态，参见 CommonStatusEnum 枚举 |
| remark | String | 否 | | 备注 |

**响应**: CommonResult<Long>，数据为新建邮件模板的编号。

**业务逻辑**: 1. 校验模板 code 唯一性，重复则抛 MAIL_TEMPLATE_CODE_EXISTS；2. 用正则 `\{(.*?)}` 从标题与内容中提取参数列表并去重，写入 params 字段；3. 插入数据库并返回 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_024_001 | 邮件模版 code({}) 已存在 |

### 2.2 修改邮件模板
- **路径**: PUT /system/mail-template/update
- **权限**: system:mail-template:update
- **说明**: 按编号修改邮件模板，重新解析模板参数并清理缓存。

**请求参数 (MailTemplateSaveReqVO)**: 与 2.1 相同，但 id 必传（更新目标编号）。

**响应**: CommonResult<Boolean>，固定返回 true。

**业务逻辑**: 1. 校验模板是否存在，不存在抛 MAIL_TEMPLATE_NOT_EXISTS；2. 校验 code 唯一性（排除自身 id）；3. 重新解析标题/内容中的参数并按 id 更新；4. 清空 MAIL_TEMPLATE 全部缓存（因可能修改 code，无法按 key 清理）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_024_000 | 邮件模版不存在 |
| 1_002_024_001 | 邮件模版 code({}) 已存在 |

### 2.3 删除邮件模板
- **路径**: DELETE /system/mail-template/delete
- **权限**: system:mail-template:delete
- **说明**: 按编号删除单个邮件模板。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult<Boolean>，固定返回 true。

**业务逻辑**: 1. 校验模板是否存在，不存在抛 MAIL_TEMPLATE_NOT_EXISTS；2. 按 id 删除；3. 清空 MAIL_TEMPLATE 全部缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_024_000 | 邮件模版不存在 |

### 2.4 批量删除邮件模板
- **路径**: DELETE /system/mail-template/delete-list
- **权限**: system:mail-template:delete
- **说明**: 按编号列表批量删除邮件模板。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List&lt;Long&gt; | 是 | @RequestParam("ids") | 模板编号列表 |

**响应**: CommonResult<Boolean>，固定返回 true。

**业务逻辑**: 1. 批量删除模板；2. 清空 MAIL_TEMPLATE 全部缓存。

### 2.5 获得邮件模板
- **路径**: GET /system/mail-template/get
- **权限**: system:mail-template:query
- **说明**: 按编号查询单个邮件模板详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;MailTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模版名称 |
| code | String | 模版编码 |
| accountId | Long | 发送的邮箱账号编号 |
| nickname | String | 发送人名称 |
| title | String | 标题 |
| content | String | 内容 |
| params | List&lt;String&gt; | 参数数组（从标题/内容解析的 `{key}` 列表） |
| status | Integer | 状态，参见 CommonStatusEnum 枚举 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

### 2.6 获得邮件模板分页
- **路径**: GET /system/mail-template/page
- **权限**: system:mail-template:query
- **说明**: 分页查询邮件模板，支持状态、编码、名称、账号、创建时间过滤。

**请求参数 (MailTemplatePageReqVO)**: 继承 PageParam（pageNo/pageSize 同 1.6）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码，默认 1 |
| pageSize | Integer | 否 | | 每页条数，默认 10 |
| status | Integer | 否 | | 状态，参见 CommonStatusEnum 枚举 |
| code | String | 否 | | 模版编码，模糊匹配 |
| name | String | 否 | | 模版名称，模糊匹配 |
| accountId | Long | 否 | | 账号编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;MailTemplateRespVO&gt;&gt;，list 元素结构同 2.5 响应。

### 2.7 获得邮件模板精简列表
- **路径**: GET /system/mail-template/list-all-simple（兼容 GET /system/mail-template/simple-list）
- **权限**: 已认证（未加 @PreAuthorize）
- **说明**: 只包含开启（ENABLE）状态的邮件模板，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;MailTemplateSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 模版编号 |
| name | String | 模版名字 |
| code | String | 模版编码 |

### 2.8 发送邮件
- **路径**: POST /system/mail-template/send-mail
- **权限**: system:mail-template:send-mail
- **说明**: 按模板编码向指定收件人发送邮件，返回发送日志编号；模板被禁用时仅记录日志不实际发送。

**请求参数 (MailTemplateSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| toMails | List&lt;String&gt; | 是 | @NotEmpty | 接收邮箱列表 |
| ccMails | List&lt;String&gt; | 否 | | 抄送邮箱列表 |
| bccMails | List&lt;String&gt; | 否 | | 密送邮箱列表 |
| templateCode | String | 是 | @NotNull | 模板编码 |
| templateParams | Map&lt;String, Object&gt; | 否 | | 模板参数，对应模板中的 `{key}` |

**响应**: CommonResult<Long>，数据为邮件发送日志编号。

**业务逻辑**: 1. 按模板编码从缓存获取邮件模板，不存在抛 MAIL_TEMPLATE_NOT_EXISTS；2. 按模板的 accountId 从缓存获取邮箱账号，不存在抛 MAIL_ACCOUNT_NOT_EXISTS；3. 校验模板声明的每个参数在 templateParams 中是否缺失，缺失抛 MAIL_SEND_TEMPLATE_PARAM_MISS；4. 将当前登录管理员的邮箱加入收件人集合，并对 to/cc/bcc 邮箱做格式校验过滤，全部为空则抛 MAIL_SEND_MAIL_NOT_EXISTS；5. 用模板参数格式化标题与内容；6. 创建发送日志：模板开启时状态为 INIT，模板禁用时状态为 IGNORE（不实际发送，仅记日志）；7. 模板开启时发送 MQ 消息（MailProducer），由消费者调用 hutool MailUtil 通过 SMTP 异步发送，并根据结果回写日志的发送状态/消息 ID/异常信息；8. 返回发送日志编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_023_000 | 邮箱账号不存在 |
| 1_002_024_000 | 邮件模版不存在 |
| 1_002_025_000 | 模板参数({})缺失 |
| 1_002_025_001 | 邮箱不存在 |

---

## 3. 邮件日志（MailLogController）

### 3.1 获得邮箱日志分页
- **路径**: GET /system/mail-log/page
- **权限**: system:mail-log:query
- **说明**: 分页查询邮件发送日志，支持用户、邮箱、账号、模板、发送状态、发送时间过滤。

**请求参数 (MailLogPageReqVO)**: 继承 PageParam（pageNo/pageSize 同 1.6）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | | 页码，默认 1 |
| pageSize | Integer | 否 | | 每页条数，默认 10 |
| userId | Long | 否 | | 用户编号 |
| userType | Integer | 否 | | 用户类型，参见 UserTypeEnum 枚举 |
| toMail | String | 否 | | 接收邮箱地址，模糊匹配 |
| accountId | Long | 否 | | 邮箱账号编号 |
| templateId | Long | 否 | | 模板编号 |
| sendStatus | Integer | 否 | | 发送状态，参见 MailSendStatusEnum 枚举 |
| sendTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发送时间区间 |

**响应**: CommonResult&lt;PageResult&lt;MailLogRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| userId | Long | 用户编号 |
| userType | Byte | 用户类型，参见 UserTypeEnum 枚举 |
| toMails | List&lt;String&gt; | 接收邮箱地址 |
| ccMails | List&lt;String&gt; | 抄送邮箱地址 |
| bccMails | List&lt;String&gt; | 密送邮箱地址 |
| accountId | Long | 邮箱账号编号 |
| fromMail | String | 发送邮箱地址 |
| templateId | Long | 模板编号 |
| templateCode | String | 模板编码 |
| templateNickname | String | 模版发送人名称 |
| templateTitle | String | 邮件标题 |
| templateContent | String | 邮件内容（格式化后） |
| templateParams | Map&lt;String, Object&gt; | 邮件参数 |
| sendStatus | Byte | 发送状态，参见 MailSendStatusEnum 枚举 |
| sendTime | LocalDateTime | 发送时间 |
| sendMessageId | String | 发送返回的消息 ID |
| sendException | String | 发送异常信息 |
| createTime | LocalDateTime | 创建时间 |

### 3.2 获得邮箱日志
- **路径**: GET /system/mail-log/get
- **权限**: system:mail-log:query
- **说明**: 按编号查询单条邮件发送日志详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 日志编号 |

**响应**: CommonResult&lt;MailLogRespVO&gt;，字段结构同 3.1 响应。
