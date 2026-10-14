# 短信管理接口 (SmsChannelController / SmsTemplateController / SmsLogController / SmsCallbackController)

> 提供短信渠道、短信模板的维护，短信发送与发送/接收日志查询，以及各短信云厂商的发送状态回调接收。

## 接口路径前缀

- `/system/sms-channel`（Controller: SmsChannelController）
- `/system/sms-template`（Controller: SmsTemplateController）
- `/system/sms-log`（Controller: SmsLogController）
- `/system/sms/callback`（Controller: SmsCallbackController）

---

## 1. 短信渠道（SmsChannelController）

### 1.1 创建短信渠道

- **路径**: POST /system/sms-channel/create
- **权限**: system:sms-channel:create
- **说明**: 新增一个短信渠道（阿里云、腾讯云等账号配置）。

**请求参数 (SmsChannelSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时无需） |
| signature | String | 是 | @NotNull | 短信签名，如「芋道源码」 |
| code | String | 是 | @NotNull | 渠道编码，参见 SmsChannelEnum 枚举类，如 YUN_PIAN |
| status | Integer | 是 | @NotNull | 启用状态 |
| remark | String | 否 | - | 备注 |
| apiKey | String | 是 | @NotNull | 短信 API 的账号 |
| apiSecret | String | 否 | - | 短信 API 的密钥 |
| callbackUrl | String | 否 | @URL | 短信发送回调 URL |

**响应**: CommonResult&lt;Long&gt; —— 渠道编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新建短信渠道的编号 |

**业务逻辑**:
1. 将请求 VO 转换为 SmsChannelDO。
2. 插入数据库（不做额外校验）。
3. 返回新渠道的编号。

### 1.2 更新短信渠道

- **路径**: PUT /system/sms-channel/update
- **权限**: system:sms-channel:update
- **说明**: 修改短信渠道配置。

**请求参数 (SmsChannelSaveReqVO)**: 字段同 1.1，其中 id 必传用于定位记录。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验渠道是否存在，不存在抛 SMS_CHANNEL_NOT_EXISTS。
2. 将请求 VO 转换为 SmsChannelDO，按 id 更新。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_011_000 | 短信渠道不存在 |

### 1.3 删除短信渠道

- **路径**: DELETE /system/sms-channel/delete
- **权限**: system:sms-channel:delete
- **说明**: 删除单个短信渠道。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 渠道编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验渠道是否存在，不存在抛 SMS_CHANNEL_NOT_EXISTS。
2. 校验该渠道下是否还有短信模板（getSmsTemplateCountByChannelId > 0 则抛 SMS_CHANNEL_HAS_CHILDREN）。
3. 删除渠道记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_011_000 | 短信渠道不存在 |
| 1_002_011_002 | 无法删除，该短信渠道还有短信模板 |

### 1.4 批量删除短信渠道

- **路径**: DELETE /system/sms-channel/delete-list
- **权限**: system:sms-channel:delete
- **说明**: 按编号列表批量删除短信渠道。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| ids | List&lt;Long&gt; | 是 | 渠道编号列表 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 逐个校验每个渠道下是否还有短信模板，任一渠道存在模板则抛 SMS_CHANNEL_HAS_CHILDREN（不校验渠道本身是否存在）。
2. 批量删除（deleteByIds）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_011_002 | 无法删除，该短信渠道还有短信模板 |

### 1.5 获得短信渠道

- **路径**: GET /system/sms-channel/get
- **权限**: system:sms-channel:query
- **说明**: 按编号获得短信渠道详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 渠道编号 |

**响应**: CommonResult&lt;SmsChannelRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| signature | String | 短信签名 |
| code | String | 渠道编码，参见 SmsChannelEnum 枚举类 |
| status | Integer | 启用状态 |
| remark | String | 备注 |
| apiKey | String | 短信 API 的账号 |
| apiSecret | String | 短信 API 的密钥 |
| callbackUrl | String | 短信发送回调 URL |
| createTime | LocalDateTime | 创建时间 |

### 1.6 获得短信渠道分页

- **路径**: GET /system/sms-channel/page
- **权限**: system:sms-channel:query
- **说明**: 分页查询短信渠道列表。

**请求参数 (SmsChannelPageReqVO)**（继承 PageParam，含 pageNo/pageSize 分页字段）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数（PageParam） | 页码 |
| pageSize | Integer | 否 | 分页参数（PageParam） | 每页条数 |
| status | Integer | 否 | - | 启用状态 |
| signature | String | 否 | - | 短信签名，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;SmsChannelRespVO&gt;&gt;，列表项字段同 1.5 响应。

### 1.7 获得短信渠道精简列表

- **路径**: GET /system/sms-channel/list-all-simple（别名 /simple-list）
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 获得全部短信渠道的精简下拉列表，包含被禁用的渠道，按编号升序排序。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;SmsChannelSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| signature | String | 短信签名 |
| code | String | 渠道编码，参见 SmsChannelEnum 枚举类 |

---

## 2. 短信模板（SmsTemplateController）

### 2.1 创建短信模板

- **路径**: POST /system/sms-template/create
- **权限**: system:sms-template:create
- **说明**: 新增短信模板，需先在短信云平台创建并通过审核。

**请求参数 (SmsTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（创建时无需） |
| type | Integer | 是 | @NotNull | 短信类型，参见 SmsTemplateTypeEnum 枚举类 |
| status | Integer | 是 | @NotNull | 开启状态，参见 CommonStatusEnum 枚举类 |
| code | String | 是 | @NotNull | 模板编码，如 test_01 |
| name | String | 是 | @NotNull | 模板名称 |
| content | String | 是 | @NotNull | 模板内容，支持 {key} 变量占位 |
| remark | String | 否 | - | 备注 |
| apiTemplateId | String | 是 | @NotNull | 短信 API 的模板编号，如 4383920 |
| channelId | Long | 是 | @NotNull | 短信渠道编号 |

**响应**: CommonResult&lt;Long&gt; —— 模板编号

**业务逻辑**:
1. 校验短信渠道存在且为开启状态（SMS_CHANNEL_NOT_EXISTS / SMS_CHANNEL_DISABLE）。
2. 校验模板编码唯一，重复抛 SMS_TEMPLATE_CODE_DUPLICATE。
3. 通过渠道对应的 SmsClient 远程校验 API 模板有效性：调用失败抛 SMS_TEMPLATE_API_ERROR；模板不存在抛 SMS_TEMPLATE_API_NOT_FOUND；审核中抛 SMS_TEMPLATE_API_AUDIT_CHECKING；审核不通过抛 SMS_TEMPLATE_API_AUDIT_FAIL。
4. 用正则 `\{(.*?)}` 解析模板内容中的参数名写入 params 字段，并冗余记录渠道编码 channelCode。
5. 插入数据库并返回模板编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_011_000 | 短信渠道不存在 |
| 1_002_011_001 | 短信渠道不处于开启状态，不允许选择 |
| 1_002_012_001 | 已经存在编码为【{}】的短信模板 |
| 1_002_012_002 | 短信 API 模板调用失败，原因是：{} |
| 1_002_012_003 | 短信 API 模版无法使用，原因：审批中 |
| 1_002_012_004 | 短信 API 模版无法使用，原因：审批不通过，{} |
| 1_002_012_005 | 短信 API 模版无法使用，原因：模版不存在 |

### 2.2 更新短信模板

- **路径**: PUT /system/sms-template/update
- **权限**: system:sms-template:update
- **说明**: 修改短信模板。

**请求参数 (SmsTemplateSaveReqVO)**: 字段同 2.1，其中 id 必传用于定位记录。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验模板存在（SMS_TEMPLATE_NOT_EXISTS）。
2. 校验短信渠道存在且开启、模板编码唯一、API 模板有效（同 2.1 的步骤 1-3）。
3. 重新解析模板内容参数并冗余渠道编码，按 id 更新。
4. 清空所有短信模板缓存（Redis SMS_TEMPLATE，因可能修改 code 无法精确清理）。

**错误码**: 同 2.1，另加：

| 错误码 | 说明 |
|-------|------|
| 1_002_012_000 | 短信模板不存在 |

### 2.3 删除短信模板

- **路径**: DELETE /system/sms-template/delete
- **权限**: system:sms-template:delete
- **说明**: 删除单个短信模板。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 校验模板存在，不存在抛 SMS_TEMPLATE_NOT_EXISTS。
2. 删除模板记录。
3. 清空所有短信模板缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_012_000 | 短信模板不存在 |

### 2.4 批量删除短信模板

- **路径**: DELETE /system/sms-template/delete-list
- **权限**: system:sms-template:delete
- **说明**: 按编号列表批量删除短信模板。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| ids | List&lt;Long&gt; | 是 | 模板编号列表 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**:
1. 直接按编号列表批量删除（不校验存在性）。
2. 清空所有短信模板缓存。

### 2.5 获得短信模板

- **路径**: GET /system/sms-template/get
- **权限**: system:sms-template:query
- **说明**: 按编号获得短信模板详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 模板编号 |

**响应**: CommonResult&lt;SmsTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| type | Integer | 短信类型，参见 SmsTemplateTypeEnum 枚举类 |
| status | Integer | 开启状态，参见 CommonStatusEnum 枚举类 |
| code | String | 模板编码 |
| name | String | 模板名称 |
| content | String | 模板内容 |
| params | List&lt;String&gt; | 从模板内容解析出的参数数组 |
| remark | String | 备注 |
| apiTemplateId | String | 短信 API 的模板编号 |
| channelId | Long | 短信渠道编号 |
| channelCode | String | 短信渠道编码 |
| createTime | LocalDateTime | 创建时间 |

### 2.6 获得短信模板分页

- **路径**: GET /system/sms-template/page
- **权限**: system:sms-template:query
- **说明**: 分页查询短信模板列表。

**请求参数 (SmsTemplatePageReqVO)**（继承 PageParam，含 pageNo/pageSize 分页字段）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数（PageParam） | 页码 |
| pageSize | Integer | 否 | 分页参数（PageParam） | 每页条数 |
| type | Integer | 否 | - | 短信类型 |
| status | Integer | 否 | - | 开启状态 |
| code | String | 否 | - | 模板编码，模糊匹配 |
| content | String | 否 | - | 模板内容，模糊匹配 |
| apiTemplateId | String | 否 | - | 短信 API 的模板编号，模糊匹配 |
| channelId | Long | 否 | - | 短信渠道编号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;SmsTemplateRespVO&gt;&gt;，列表项字段同 2.5 响应。

### 2.7 获得短信模板精简列表

- **路径**: GET /system/sms-template/list-all-simple（别名 /simple-list）
- **权限**: 已认证（无 @PreAuthorize，仅要求登录）
- **说明**: 只包含开启状态的短信模板，主要用于前端下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;SmsTemplateSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模板名称 |
| code | String | 模板编码 |

### 2.8 导出短信模板 Excel

- **路径**: GET /system/sms-template/export-excel
- **权限**: system:sms-template:export
- **说明**: 按分页查询条件导出全部短信模板 Excel。

**请求参数 (SmsTemplatePageReqVO)**: 字段同 2.6（导出时 pageSize 强制置为不分页，查询全部）。

**响应**: Excel 文件流（短信模板.xls），列同 SmsTemplateRespVO 的 @ExcelProperty 字段。

### 2.9 发送短信

- **路径**: POST /system/sms-template/send-sms
- **权限**: system:sms-template:send-sms
- **说明**: 使用指定模板向单个手机号发送短信（管理端测试发送）。

**请求参数 (SmsTemplateSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| mobile | String | 是 | @NotNull | 手机号 |
| templateCode | String | 是 | @NotNull | 模板编码，如 test_01 |
| templateParams | Map&lt;String, Object&gt; | 否 | - | 模板参数 |

**响应**: CommonResult&lt;Long&gt; —— 发送日志编号

**业务逻辑**:
1. 若 mobile 为空，则按 userId 加载管理员用户的手机号（sendSingleSmsToAdmin）。
2. 从缓存校验短信模板存在（按模板编码，SMS_SEND_TEMPLATE_NOT_EXISTS）。
3. 校验模板对应的短信渠道存在（SMS_CHANNEL_NOT_EXISTS）。
4. 校验手机号非空（SMS_SEND_MOBILE_NOT_EXISTS）。
5. 按模板 params 顺序构建有序参数数组，任一参数缺失抛 SMS_SEND_MOBILE_TEMPLATE_PARAM_MISS。
6. 渲染模板内容，先写入一条发送日志；仅当模板与渠道均为开启状态才实际发送，否则只记日志（状态 IGNORE）。
7. 若需发送，发送 MQ 消息异步执行：消费者通过渠道 SmsClient 调用短信 API，并将发送结果（成功/失败、API 编码、信息、请求 ID、序号）回写到发送日志。
8. 返回发送日志编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_011_000 | 短信渠道不存在 |
| 1_002_013_000 | 手机号不存在 |
| 1_002_013_001 | 模板参数({})缺失 |
| 1_002_013_002 | 短信模板不存在 |

---

## 3. 短信日志（SmsLogController）

### 3.1 获得短信日志分页

- **路径**: GET /system/sms-log/page
- **权限**: system:sms-log:query
- **说明**: 分页查询短信发送/接收日志。

**请求参数 (SmsLogPageReqVO)**（继承 PageParam，含 pageNo/pageSize 分页字段）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | 分页参数（PageParam） | 页码 |
| pageSize | Integer | 否 | 分页参数（PageParam） | 每页条数 |
| channelId | Long | 否 | - | 短信渠道编号 |
| templateId | Long | 否 | - | 模板编号 |
| mobile | String | 否 | - | 手机号 |
| sendStatus | Integer | 否 | - | 发送状态，参见 SmsSendStatusEnum 枚举类 |
| sendTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发送时间区间 |
| receiveStatus | Integer | 否 | - | 接收状态，参见 SmsReceiveStatusEnum 枚举类 |
| receiveTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 接收时间区间 |

**响应**: CommonResult&lt;PageResult&lt;SmsLogRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| channelId | Long | 短信渠道编号 |
| channelCode | String | 短信渠道编码 |
| templateId | Long | 模板编号 |
| templateCode | String | 模板编码 |
| templateType | Integer | 短信类型（字典 sms_template_type） |
| templateContent | String | 短信内容 |
| templateParams | Map&lt;String, Object&gt; | 短信参数 |
| apiTemplateId | String | 短信 API 的模板编号 |
| mobile | String | 手机号 |
| userId | Long | 用户编号 |
| userType | Integer | 用户类型（字典 user_type） |
| sendStatus | Integer | 发送状态（字典 sms_send_status） |
| sendTime | LocalDateTime | 发送时间 |
| apiSendCode | String | 短信 API 发送结果的编码 |
| apiSendMsg | String | 短信 API 发送失败的提示 |
| apiRequestId | String | 短信 API 发送返回的唯一请求 ID |
| apiSerialNo | String | 短信 API 发送返回的序号 |
| receiveStatus | Integer | 接收状态（字典 sms_receive_status） |
| receiveTime | LocalDateTime | 接收时间 |
| apiReceiveCode | String | API 接收结果的编码 |
| apiReceiveMsg | String | API 接收结果的说明 |
| createTime | LocalDateTime | 创建时间 |

### 3.2 获得短信日志

- **路径**: GET /system/sms-log/get
- **权限**: system:sms-log:query
- **说明**: 按编号获得短信日志详情。

**请求参数**: Query 参数

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 日志编号 |

**响应**: CommonResult&lt;SmsLogRespVO&gt;，字段同 3.1 响应。

### 3.3 导出短信日志 Excel

- **路径**: GET /system/sms-log/export-excel
- **权限**: system:sms-log:export
- **说明**: 按分页查询条件导出全部短信日志 Excel。

**请求参数 (SmsLogPageReqVO)**: 字段同 3.1（导出时 pageSize 强制置为不分页，查询全部）。

**响应**: Excel 文件流（短信日志.xls），列同 SmsLogRespVO 的 @ExcelProperty 字段。

---

## 4. 短信回调（SmsCallbackController）

> 四个回调端点均为 @PermitAll（匿名可访问）+ @TenantIgnore（忽略租户），请求体为短信云平台推送的原始报文，用于异步更新短信日志的接收状态。

### 4.1 阿里云短信回调

- **路径**: POST /system/sms/callback/aliyun
- **权限**: @PermitAll（匿名访问，忽略租户）
- **说明**: 接收阿里云短信发送状态回调。

**请求参数**: 无 VO，请求体为阿里云推送的原始 JSON 报文（HttpServletRequest 读取）。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

### 4.2 腾讯云短信回调

- **路径**: POST /system/sms/callback/tencent
- **权限**: @PermitAll（匿名访问，忽略租户）
- **说明**: 接收腾讯云短信发送状态回调。

**请求参数**: 无 VO，请求体为腾讯云推送的原始报文。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

### 4.3 华为云短信回调

- **路径**: POST /system/sms/callback/huawei
- **权限**: @PermitAll（匿名访问，忽略租户）
- **说明**: 接收华为云短信发送状态回调。

**请求参数**: 无 VO，请求体为华为云推送的原始报文（String requestBody）。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

### 4.4 七牛云短信回调

- **路径**: POST /system/sms/callback/qiniu
- **权限**: @PermitAll（匿名访问，忽略租户）
- **说明**: 接收七牛云短信发送状态回调。

**请求参数**: 无 VO，请求体为七牛云推送的原始报文（String requestBody）。

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**（四个回调共用 SmsSendService.receiveSmsStatus）:
1. 按渠道编码获得对应的 SmsClient 客户端。
2. 调用 SmsClient.parseSmsReceiveStatus 解析回调原文为接收结果列表（SmsReceiveRespDTO），为空则直接返回。
3. 逐条更新短信日志接收结果：按日志编号（为空时按 apiSerialNo 反查日志）更新接收状态（成功/失败）、接收时间、API 接收编码与说明。

---

## 附：错误码说明

| 错误码 | 说明 | 使用位置 |
|-------|------|---------|
| 1_002_011_000 | 短信渠道不存在 | 渠道更新/删除、模板创建/更新、短信发送 |
| 1_002_011_001 | 短信渠道不处于开启状态，不允许选择 | 模板创建/更新 |
| 1_002_011_002 | 无法删除，该短信渠道还有短信模板 | 渠道删除/批量删除 |
| 1_002_012_000 | 短信模板不存在 | 模板更新/删除 |
| 1_002_012_001 | 已经存在编码为【{}】的短信模板 | 模板创建/更新 |
| 1_002_012_002 | 短信 API 模板调用失败，原因是：{} | 模板创建/更新 |
| 1_002_012_003 | 短信 API 模版无法使用，原因：审批中 | 模板创建/更新 |
| 1_002_012_004 | 短信 API 模版无法使用，原因：审批不通过，{} | 模板创建/更新 |
| 1_002_012_005 | 短信 API 模版无法使用，原因：模版不存在 | 模板创建/更新 |
| 1_002_013_000 | 手机号不存在 | 短信发送 |
| 1_002_013_001 | 模板参数({})缺失 | 短信发送 |
| 1_002_013_002 | 短信模板不存在 | 短信发送 |

> 注：短信验证码相关错误码（1_002_014_000~1_002_014_005，如「验证码不存在」「验证码已过期」「超过每日短信发送数量」「短信发送过于频繁」等）由 SmsCodeService 提供，经 AuthController（短信验证码发送/校验、短信登录）与 SmsCodeApi 暴露，不在本域控制器的端点中直接出现。
