# 站内信接口 (NotifyTemplateController / NotifyMessageController)

> 站内信域负责模版管理与消息发送/接收：管理员维护站内信模版并向指定用户发送消息，用户查看自己的站内信、标记已读并轮询未读数。

## 接口路径前缀
- /system/notify-template  (Controller: NotifyTemplateController) —— 站内信模版管理 + 消息发送
- /system/notify-message  (Controller: NotifyMessageController) —— 站内信管理 + 我的站内信

---

## 1. 站内信模版管理（NotifyTemplateController）

### 1.1 创建站内信模版
- **路径**: POST /system/notify-template/create
- **权限**: system:notify-template:create
- **说明**: 新增一个站内信模版，自动从模版内容中解析参数列表。

**请求参数 (NotifyTemplateSaveReqVO)**: 继承无（普通 VO）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | — | ID，创建时不传 |
| name | String | 是 | @NotEmpty | 模版名称 |
| code | String | 是 | @NotNull | 模版编码 |
| type | Integer | 是 | @NotNull | 模版类型，对应 system_notify_template_type 字典 |
| nickname | String | 是 | @NotEmpty | 发送人名称 |
| content | String | 是 | @NotEmpty | 模版内容，支持 `{变量}` 占位符 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态，参见 CommonStatusEnum 枚举 |
| remark | String | 否 | — | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 模版编号

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新建模版的 ID |

**业务逻辑**: 1. 校验模版编码是否重复（同编码存在即抛错）；2. 将 VO 转换为 NotifyTemplateDO；3. 用正则 `\{(.*?)}` 从模版内容中解析出参数名数组，存入 params 字段；4. 插入数据库并返回 ID。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_026_001 | 已经存在编码为【{}】的站内信模板 |

### 1.2 更新站内信模版
- **路径**: PUT /system/notify-template/update
- **权限**: system:notify-template:update
- **说明**: 修改已有站内信模版，并清空模版缓存。

**请求参数 (NotifyTemplateSaveReqVO)**: 与 1.1 相同（id 必传，用于定位记录）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 校验模版是否存在，不存在抛错；2. 校验模版编码是否被其他模版占用；3. 解析新模版内容的参数列表；4. 更新数据库；5. 通过 @CacheEvict 清空 NOTIFY_TEMPLATE 缓存的全部条目（因可能修改 code 字段，无法精确清理）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_026_000 | 站内信模版不存在 |
| 1_002_026_001 | 已经存在编码为【{}】的站内信模板 |

### 1.3 删除站内信模版
- **路径**: DELETE /system/notify-template/delete
- **权限**: system:notify-template:delete
- **说明**: 按编号删除单个站内信模版。

**请求参数**: Query 参数 `id`（Long，必填，编号）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 校验模版存在，不存在抛错；2. 删除记录；3. 清空 NOTIFY_TEMPLATE 缓存。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_026_000 | 站内信模版不存在 |

### 1.4 批量删除站内信模版
- **路径**: DELETE /system/notify-template/delete-list
- **权限**: system:notify-template:delete
- **说明**: 按编号列表批量删除站内信模版。

**请求参数**: Query 参数 `ids`（List&lt;Long&gt;，必填，编号列表）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 按 ids 批量删除记录（不做逐条存在性校验）；2. 清空 NOTIFY_TEMPLATE 缓存。

### 1.5 获得站内信模版
- **路径**: GET /system/notify-template/get
- **权限**: system:notify-template:query
- **说明**: 按编号查询单个模版详情。

**请求参数**: Query 参数 `id`（Long，必填，编号）

**响应**: CommonResult&lt;NotifyTemplateRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | ID |
| name | String | 模版名称 |
| code | String | 模版编码 |
| type | Integer | 模版类型，对应 system_notify_template_type 字典 |
| nickname | String | 发送人名称 |
| content | String | 模版内容 |
| params | List&lt;String&gt; | 参数数组（从内容解析） |
| status | Integer | 状态，参见 CommonStatusEnum 枚举 |
| remark | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询模版；2. 转换为 RespVO 返回。

### 1.6 获得站内信模版分页
- **路径**: GET /system/notify-template/page
- **权限**: system:notify-template:query
- **说明**: 条件分页查询模版列表。

**请求参数 (NotifyTemplatePageReqVO)**: 继承 PageParam（pageNo 页码，@NotNull、@Min(1)，默认 1；pageSize 每页条数，@NotNull、@Min(1)、@Max(200)，默认 10）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（父类 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（父类 PageParam） | 每页条数 |
| code | String | 否 | — | 模版编码，模糊匹配 |
| name | String | 否 | — | 模版名称，模糊匹配 |
| status | Integer | 否 | — | 状态，参见 CommonStatusEnum 枚举类 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;NotifyTemplateRespVO&gt;&gt;，列表元素字段同 1.5

**业务逻辑**: 1. 按编码/名称/状态/创建时间区间构建查询条件；2. 分页查询并转换为 RespVO 分页结果。

### 1.7 获得站内信模版精简列表
- **路径**: GET /system/notify-template/list-all-simple（兼容别名 /simple-list）
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 只包含被开启的站内信模版，主要用于前端的下拉选项。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;NotifyTemplateSimpleRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模版名称 |
| code | String | 模版编码 |

**业务逻辑**: 1. 查询状态为开启（CommonStatusEnum.ENABLE）的全部模版；2. 转换为精简 RespVO 列表返回。

---

## 2. 站内信发送（NotifyTemplateController）

### 2.1 发送站内信
- **路径**: POST /system/notify-template/send-notify
- **权限**: system:notify-template:send-notify
- **说明**: 基于模版向指定用户（管理员或会员）发送一条站内信。

**请求参数 (NotifyTemplateSendReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @NotNull | 接收用户编号 |
| userType | Integer | 是 | @NotNull | 用户类型（MEMBER=1 会员 / ADMIN=2 管理员） |
| templateCode | String | 是 | @NotEmpty | 模板编码 |
| templateParams | Map&lt;String, Object&gt; | 否 | — | 模板参数 |

**响应**: CommonResult&lt;Long&gt; —— 站内信消息编号（模版被禁用时返回 null）

**业务逻辑**: 1. 按 userType 分发：MEMBER 走 sendSingleNotifyToMember，否则 sendSingleNotifyToAdmin，二者统一委托 sendSingleNotify；2. 按编码从缓存获取模版（getNotifyTemplateByCodeFromCache，@Cacheable），不存在抛 NOTICE_NOT_FOUND；3. 若模版状态为禁用，记录日志后直接返回 null，不发送；4. 校验模板参数：遍历模版解析出的 params，任一参数缺失抛 NOTIFY_SEND_TEMPLATE_PARAM_MISS；5. 用 StrUtil.format 以 templateParams 渲染模版内容；6. 创建 NotifyMessageDO（readStatus=false）并落库，返回消息 ID。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_002_008_001 | 当前通知公告不存在（代码实际复用该错误码表示模版不存在） |
| 1_002_028_000 | 模板参数({})缺失 |

---

## 3. 站内信管理（NotifyMessageController）

### 3.1 获得站内信
- **路径**: GET /system/notify-message/get
- **权限**: system:notify-message:query
- **说明**: 按编号查询单条站内信详情（管理端）。

**请求参数**: Query 参数 `id`（Long，必填，编号）

**响应**: CommonResult&lt;NotifyMessageRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | ID |
| userId | Long | 用户编号 |
| userType | Byte | 用户类型，参见 UserTypeEnum 枚举 |
| templateId | Long | 模版编号 |
| templateCode | String | 模板编码 |
| templateNickname | String | 模版发送人名称 |
| templateContent | String | 模版内容（渲染后） |
| templateType | Integer | 模版类型 |
| templateParams | Map&lt;String, Object&gt; | 模版参数 |
| readStatus | Boolean | 是否已读 |
| readTime | LocalDateTime | 阅读时间 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 按 id 查询站内信；2. 转换为 RespVO 返回。

### 3.2 获得站内信分页
- **路径**: GET /system/notify-message/page
- **权限**: system:notify-message:query
- **说明**: 管理端按条件分页查询全部用户的站内信。

**请求参数 (NotifyMessagePageReqVO)**: 继承 PageParam（pageNo/pageSize 校验规则同 1.6）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（父类 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（父类 PageParam） | 每页条数 |
| userId | Long | 否 | — | 用户编号 |
| userType | Integer | 否 | — | 用户类型 |
| templateCode | String | 否 | — | 模板编码 |
| templateType | Integer | 否 | — | 模版类型 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;NotifyMessageRespVO&gt;&gt;，列表元素字段同 3.1

**业务逻辑**: 1. 按用户/用户类型/模板编码/模版类型/创建时间区间构建条件；2. 分页查询并转换为 RespVO 分页结果。

---

## 4. 我的站内信（NotifyMessageController）

### 4.1 获得我的站内信分页
- **路径**: GET /system/notify-message/my-page
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 当前登录管理员查询自己的站内信分页。

**请求参数 (NotifyMessageMyPageReqVO)**: 继承 PageParam（pageNo/pageSize 校验规则同 1.6）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1)（父类 PageParam） | 页码 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（父类 PageParam） | 每页条数 |
| readStatus | Boolean | 否 | — | 是否已读 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult&lt;PageResult&lt;NotifyMessageRespVO&gt;&gt;，列表元素字段同 3.1

**业务逻辑**: 1. 取当前登录用户 ID + 用户类型 ADMIN；2. 联合 readStatus/createTime 条件分页查询该用户的站内信。

### 4.2 标记站内信为已读
- **路径**: PUT /system/notify-message/update-read
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 将指定编号列表中属于当前用户的站内信标记为已读。

**请求参数**: Query 参数 `ids`（List&lt;Long&gt;，必填，编号列表，如 1024,2048）

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 取当前登录用户 ID + ADMIN 用户类型；2. 更新 ids 中属于该用户的记录：readStatus=true、readTime=当前时间；3. 返回实际更新条数（Controller 忽略）。

### 4.3 标记所有站内信为已读
- **路径**: PUT /system/notify-message/update-all-read
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 将当前登录用户的全部未读站内信标记为已读。

**请求参数**: 无

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true

**业务逻辑**: 1. 取当前登录用户 ID + ADMIN 用户类型；2. 将该用户所有未读记录批量置为已读；3. 返回实际更新条数（Controller 忽略）。

### 4.4 获取当前用户的最新未读站内信列表
- **路径**: GET /system/notify-message/get-unread-list
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 获取当前用户的最新站内信列表，默认 10 条。

**请求参数**: Query 参数 `size`（Integer，可选，默认 10，返回条数）

**响应**: CommonResult&lt;List&lt;NotifyMessageRespVO&gt;&gt;，列表元素字段同 3.1

**业务逻辑**: 1. 取当前登录用户 ID + ADMIN 用户类型；2. 按创建时间倒序查询指定数量的未读站内信；3. 转换为 RespVO 列表返回。

### 4.5 获得当前用户的未读站内信数量
- **路径**: GET /system/notify-message/get-unread-count
- **权限**: 已认证（无 @PreAuthorize）
- **说明**: 统计当前登录用户的未读站内信数量，前端轮询使用（@ApiAccessLog(enable=false) 关闭访问日志）。

**请求参数**: 无

**响应**: CommonResult&lt;Long&gt; —— 未读数量

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 未读站内信数量 |

**业务逻辑**: 1. 取当前登录用户 ID + ADMIN 用户类型；2. 按用户 + readStatus=false 统计未读数量并返回。

---

## 附：站内信域错误码汇总（ErrorCodeConstants）

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| 1_002_026_000 | 站内信模版不存在 | 模版更新/删除时校验 |
| 1_002_026_001 | 已经存在编码为【{}】的站内信模板 | 模版创建/更新时编码重复校验 |
| 1_002_028_000 | 模板参数({})缺失 | 发送站内信时模板参数缺失 |
| 1_002_008_001 | 当前通知公告不存在 | 发送站内信时模版不存在（代码复用通知公告错误码） |
