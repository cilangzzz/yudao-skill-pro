# 公文管理接口 (OaOfficialDocSendController / OaOfficialDocReceiveController / OaOfficialDocTemplateController)

> OA 公文管理：发文人起草公文并选择套红模板发起审批，审批通过后自动向主送/抄送部门投递收文，接收部门签收后对主送收文发起办理审批；套红模板独立维护红头样式。

## 接口路径前缀

- /oa/officialdoc-send  (Controller: OaOfficialDocSendController) —— 公文发文
- /oa/officialdoc-receive  (Controller: OaOfficialDocReceiveController) —— 公文收文
- /oa/officialdoc-template  (Controller: OaOfficialDocTemplateController) —— 套红模板

## 1. 公文发文

### 1.1 创建公文发文

- **路径**: POST /oa/officialdoc-send/create
- **权限**: oa:officialdoc-send:create
- **说明**: 创建发文草稿，单号与审批状态由服务端生成，发文字号由字号前缀 + 年份 + 序号组合。

**请求参数 (OaOfficialDocSendSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 发文编号（新增时不传） |
| templateId | Long | 是 | @NotNull | 套红模板编号 |
| title | String | 是 | @NotBlank、@Size(max=255) | 公文标题 |
| noPrefix | String | 否 | @Size(max=64) | 字号，如“芋办” |
| year | Integer | 否 | @Min(1)、@Max(9999) | 年份 |
| sequence | Integer | 否 | @Min(1) | 第几号文 |
| secrecyLevel | Integer | 是 | @NotNull、@InDict(OFFICIAL_DOC_SECRET_LEVEL) | 密级（字典） |
| urgencyLevel | Integer | 是 | @NotNull、@InDict(OFFICIAL_DOC_URGENCY_LEVEL) | 紧急程度（字典） |
| disclosureType | Integer | 是 | @NotNull、@InDict(OFFICIAL_DOC_PUBLIC_CATEGORY) | 公开类别（字典） |
| issueTime | LocalDateTime | 是 | @NotNull | 发文日期 |
| sendDeptId | Long | 是 | @NotNull | 发文部门编号 |
| mainDeptIds | List&lt;Long&gt; | 是 | @NotEmpty、元素 @NotNull | 主送部门编号列表 |
| copyDeptIds | List&lt;Long&gt; | 否 | 元素 @NotNull | 抄送部门编号列表 |
| content | String | 否 | - | 公文正文 |
| fileUrls | List&lt;String&gt; | 否 | 元素 @NotBlank | 附件地址列表 |
| formalFileUrl | String | 否 | @Size(max=2048) | 正式公文地址 |
| remark | String | 否 | @Size(max=500) | 附注 |

**响应**: CommonResult&lt;Long&gt; —— 发文编号。

**业务逻辑**:
1. 校验发文关联数据：套红模板存在且已启用、发文部门/主送部门/抄送部门合法。
2. 若字号前缀、年份、序号齐全，校验组合后的完整发文字号未被其他发文占用（草稿未编号的不参与查重）。
3. 通过 Redis 生成发文单号并校验唯一。
4. 转换为 DO 保存草稿：审批状态初始化为未开始（NOT_START），服务端组合发文字号 documentNo（前缀 + 〔年份〕 + 序号“号”）。
5. 返回发文编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_000 | 套红模板不存在 |
| 1_054_260_005 | 套红模板已停用 |
| 1_054_260_007 | 发文单据编号已存在 |
| 1_054_260_009 | 发文字号已存在 |

### 1.2 更新公文发文

- **路径**: PUT /oa/officialdoc-send/update
- **权限**: oa:officialdoc-send:update
- **说明**: 更新自己未提交的发文草稿，重新校验关联数据并重排发文字号。

**请求参数 (OaOfficialDocSendSaveReqVO)**: 同 [1.1 创建公文发文](#11-创建公文发文)，其中 `id` 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验发文存在且创建人为当前登录用户。
2. 校验发文为未提交草稿（审批状态 NOT_START）。
3. 校验发文关联数据（模板、部门、发文字号查重，排除自身）。
4. 更新表单字段并重新组合发文字号，不覆盖审批状态与归属。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |
| 1_054_260_000 | 套红模板不存在 |
| 1_054_260_005 | 套红模板已停用 |
| 1_054_260_009 | 发文字号已存在 |

### 1.3 删除公文发文

- **路径**: DELETE /oa/officialdoc-send/delete
- **权限**: oa:officialdoc-send:delete
- **说明**: 删除自己的发文，仅限未提交、审批不通过或已取消的单据。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 发文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验发文存在且创建人为当前登录用户。
2. 校验审批状态为未开始、审批不通过或已取消之一，否则不允许删除。
3. 删除发文记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |

### 1.4 提交公文发文审批

- **路径**: POST /oa/officialdoc-send/submit
- **权限**: oa:officialdoc-send:update
- **说明**: 将草稿发文提交 BPM 审批，返回流程实例编号。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 发文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功（Service 返回流程实例编号，控制器仅返回 true）。

**业务逻辑**:
1. 校验发文存在、归属当前用户，且为未提交草稿。
2. 重新校验发文关联数据（模板、部门、发文字号）。
3. 更新审批状态为审批中（RUNNING）。
4. 调用 BPM 发起“公文发文”审批流程（businessKey 为发文编号），绑定流程实例编号并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |
| 1_054_260_000 | 套红模板不存在 |
| 1_054_260_005 | 套红模板已停用 |
| 1_054_260_009 | 发文字号已存在 |

### 1.5 撤销公文发文审批

- **路径**: PUT /oa/officialdoc-send/cancel
- **权限**: oa:officialdoc-send:update
- **说明**: 撤销审批中的发文流程，审批事件回调同步单据状态。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 发文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验发文存在、归属当前用户。
2. 校验审批状态为审批中（RUNNING）。
3. 调用 BPM 按发起人撤销流程实例，理由为“申请人撤销公文发文”。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |

### 1.6 获得公文发文分页列表

- **路径**: GET /oa/officialdoc-send/page
- **权限**: oa:officialdoc-send:query
- **说明**: 分页查询当前登录用户创建的发文，拼接签发人与部门名称。

**请求参数 (OaOfficialDocSendPageReqVO)**，继承 PageParam（pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| title | String | 否 | - | 公文标题（模糊查询） |
| documentNo | String | 否 | - | 发文字号（模糊查询） |
| status | Integer | 否 | - | 流程状态 |

**响应**: CommonResult&lt;PageResult&lt;OaOfficialDocSendRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| templateId | Long | 套红模板编号 |
| title | String | 公文标题 |
| noPrefix | String | 字号 |
| year | Integer | 年份 |
| sequence | Integer | 第几号文 |
| secrecyLevel | Integer | 密级 |
| urgencyLevel | Integer | 紧急程度 |
| disclosureType | Integer | 公开类别 |
| issueTime | LocalDateTime | 发文日期 |
| sendDeptId | Long | 发文部门编号 |
| mainDeptIds | List&lt;Long&gt; | 主送部门编号列表 |
| copyDeptIds | List&lt;Long&gt; | 抄送部门编号列表 |
| content | String | 公文正文 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| formalFileUrl | String | 正式公文地址 |
| remark | String | 附注 |
| no | String | 单据编号 |
| documentNo | String | 公文文号 |
| signerUserId | Long | 签发人编号 |
| signerName | String | 签发人（关联查询） |
| sendDeptName | String | 发文部门（关联查询） |
| mainDeptNames | List&lt;String&gt; | 主送部门名称列表（关联查询） |
| copyDeptNames | List&lt;String&gt; | 抄送部门名称列表（关联查询） |
| status | Integer | 审批状态 |
| processInstanceId | String | 流程实例编号 |
| creator | String | 创建人编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按创建人等于当前登录用户，叠加标题（模糊）、发文字号（模糊）、流程状态条件分页查询，按编号倒序。
2. 批量查询签发人用户及发文、主送、抄送部门。
3. 拼接签发人姓名、发文部门名称、主送/抄送部门名称列表。

### 1.7 获得公文发文详情

- **路径**: GET /oa/officialdoc-send/get
- **权限**: oa:officialdoc-send:query 或 oa:officialdoc-receive:query（任一）
- **说明**: 查询发文详情，收文视角（查看来文信息）复用本接口。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 发文编号 |

**响应**: CommonResult&lt;OaOfficialDocSendRespVO&gt; —— 字段同 [1.6 分页列表](#16-获得公文发文分页列表)。

**业务逻辑**:
1. 按编号查询发文。
2. 拼接签发人姓名、发文部门名称、主送/抄送部门名称列表后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在（查询不存在时返回 null，不抛错；该错误码为本域通用校验码） |

## 2. 公文收文

### 2.1 创建公文收文

- **路径**: POST /oa/officialdoc-receive/create
- **权限**: oa:officialdoc-receive:create
- **说明**: 手工登记收文（区别于发文审批通过后的自动投递），单号由服务端生成。

**请求参数 (OaOfficialDocReceiveSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 收文编号（新增时不传） |
| title | String | 是 | @NotBlank、@Size(max=255) | 公文标题 |
| documentNo | String | 否 | @Size(max=64) | 来文字号 |
| secrecyLevel | Integer | 是 | @NotNull、@InDict(OFFICIAL_DOC_SECRET_LEVEL) | 密级（字典） |
| urgencyLevel | Integer | 是 | @NotNull、@InDict(OFFICIAL_DOC_URGENCY_LEVEL) | 紧急程度（字典） |
| receiveType | Integer | 是 | @NotNull、@InEnum(OaOfficialDocReceiveTypeEnum) | 收文类型：0 主送、1 抄送（服务端强制覆盖为主送） |
| receiveTime | LocalDateTime | 是 | @NotNull | 收文时间 |
| receiveDeptId | Long | 是 | @NotNull | 收文部门编号 |
| handlerUserId | Long | 否 | - | 主办人用户编号 |
| instruction | String | 否 | @Size(max=2000) | 领导批示 |
| result | String | 否 | @Size(max=2000) | 办理结果 |
| deadlineTime | LocalDateTime | 否 | - | 办理期限 |
| summary | String | 否 | - | 内容摘要 |
| remark | String | 否 | @Size(max=500) | 备注 |
| fileUrls | List&lt;String&gt; | 否 | 元素 @NotBlank | 附件地址列表 |
| formalFileUrl | String | 否 | @Size(max=2048) | 正式公文地址 |

**响应**: CommonResult&lt;Long&gt; —— 收文编号。

**业务逻辑**:
1. 通过 Redis 生成收文单号（前缀区分发文/收文）并校验唯一。
2. 转换为 DO 保存：收文类型强制为“主送”（手工收文），审批状态初始化为未开始（NOT_START），办理状态初始化为待签收（WAIT_CLAIM）。
3. 返回收文编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_006 | 收文单据编号已存在 |

### 2.2 更新公文收文

- **路径**: PUT /oa/officialdoc-receive/update
- **权限**: oa:officialdoc-receive:update
- **说明**: 更新自己未提交的收文，自动投递的收文不允许替换附件与正式公文。

**请求参数 (OaOfficialDocReceiveSaveReqVO)**: 同 [2.1 创建公文收文](#21-创建公文收文)，其中 `id` 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验收文存在、归属当前登录用户（creator 匹配）。
2. 校验收文为未提交草稿（审批状态 NOT_START）。
3. 更新表单字段，收文类型保留原值不覆盖。
4. 自动投递的收文（来源发文编号非空）保留投递时的附件与正式公文地址，不允许通过编辑替换。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |

### 2.3 删除公文收文

- **路径**: DELETE /oa/officialdoc-receive/delete
- **权限**: oa:officialdoc-receive:delete
- **说明**: 删除自己的收文，仅限未提交、审批不通过或已取消的单据。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 收文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验收文存在、归属当前登录用户。
2. 校验审批状态为未开始、审批不通过或已取消之一，否则不允许删除。
3. 删除收文记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |

### 2.4 提交公文收文审批

- **路径**: POST /oa/officialdoc-receive/submit
- **权限**: oa:officialdoc-receive:update
- **说明**: 主送收文发起办理审批；抄送收文仅知会，不允许提交。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 收文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功（Service 返回流程实例编号，控制器仅返回 true）。

**业务逻辑**:
1. 校验收文存在、归属当前用户，且为未提交草稿。
2. 校验收文类型为主送，抄送类型仅知会、不发起办理审批。
3. 更新审批状态为审批中（RUNNING）、办理状态为办理中（PROCESSING）。
4. 调用 BPM 发起“公文收文”审批流程（businessKey 为收文编号），绑定流程实例编号并返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |

### 2.5 撤销公文收文审批

- **路径**: PUT /oa/officialdoc-receive/cancel
- **权限**: oa:officialdoc-receive:update
- **说明**: 撤销审批中的收文办理流程。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 收文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验收文存在、归属当前用户。
2. 校验审批状态为审批中（RUNNING）。
3. 调用 BPM 按发起人撤销流程实例，理由为“申请人撤销公文收文”，审批事件回调同步单据状态。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |

### 2.6 签收公文收文

- **路径**: PUT /oa/officialdoc-receive/claim
- **权限**: oa:officialdoc-receive:update
- **说明**: 接收部门成员认领发文审批通过后自动投递的收文，签收后单据归属签收人。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 收文编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验收文存在。
2. 校验当前登录用户所属部门与收文部门一致，否则无权访问。
3. 校验为自动投递单据（来源发文编号非空）、尚无归属人（creator 为空）且办理状态为待签收。
4. 更新办理状态为已签收（CLAIMED），并将 creator 设置为签收人（确定单据归属）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文（当前用户部门与收文部门不一致） |
| 1_054_260_003 | 当前公文状态不允许该操作（非自动投递、已被签收或非待签收状态） |

### 2.7 获得公文收文分页列表

- **路径**: GET /oa/officialdoc-receive/page
- **权限**: oa:officialdoc-receive:query
- **说明**: 分页查询当前登录用户所属部门的收文（含主送/抄送与手工登记），并拼接发文侧展示信息。

**请求参数 (OaOfficialDocReceivePageReqVO)**，继承 PageParam（pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| title | String | 否 | - | 公文标题（模糊查询） |
| documentNo | String | 否 | - | 来文字号（模糊查询） |
| status | Integer | 否 | - | 流程状态 |

**响应**: CommonResult&lt;PageResult&lt;OaOfficialDocReceiveRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| sendId | Long | 来源发文编号 |
| sendDeptName | String | 发文部门（关联查询） |
| issueTime | LocalDateTime | 发文日期（来自关联发文） |
| signerName | String | 签发人（来自关联发文，关联查询） |
| disclosureType | Integer | 公开类别（来自关联发文） |
| receiveType | Integer | 收文类型：0 主送、1 抄送 |
| receiveTime | LocalDateTime | 收文时间 |
| receiveDeptId | Long | 收文部门编号 |
| handlerUserId | Long | 主办人用户编号 |
| instruction | String | 领导批示 |
| result | String | 办理结果 |
| deadlineTime | LocalDateTime | 办理期限 |
| summary | String | 内容摘要 |
| remark | String | 备注 |
| fileUrls | List&lt;String&gt; | 附件地址列表 |
| no | String | 单据编号 |
| title | String | 公文标题 |
| documentNo | String | 来文字号 |
| secrecyLevel | Integer | 密级 |
| urgencyLevel | Integer | 紧急程度 |
| formalFileUrl | String | 正式公文地址 |
| receiveDeptName | String | 收文部门（关联查询） |
| handlerName | String | 主办人（关联查询） |
| status | Integer | 审批状态 |
| handleStatus | Integer | 办理状态：0 待签收、1 已签收、2 办理中、3 已办结 |
| processInstanceId | String | 流程实例编号 |
| creator | String | 创建人编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 查询当前登录用户所属部门编号，无部门则返回空分页。
2. 按收文部门等于当前用户部门，叠加标题（模糊）、来文字号（模糊）、流程状态条件分页查询，按编号倒序。
3. 批量查询关联发文（手工收文不查）、主办人与签发人用户、收发文部门。
4. 拼接主办人姓名、收文部门名称，以及关联发文的发文部门、发文日期、签发人、公开类别。

### 2.8 获得公文收文详情

- **路径**: GET /oa/officialdoc-receive/get
- **权限**: oa:officialdoc-receive:query
- **说明**: 查询收文详情，展示字段拼接逻辑与分页一致。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 收文编号 |

**响应**: CommonResult&lt;OaOfficialDocReceiveRespVO&gt; —— 字段同 [2.7 分页列表](#27-获得公文收文分页列表)。

**业务逻辑**:
1. 按编号查询收文。
2. 按分页相同的规则拼接关联发文信息、用户与部门名称后返回。

## 3. 套红模板

### 3.1 创建套红模板

- **路径**: POST /oa/officialdoc-template/create
- **权限**: oa:officialdoc-template:create
- **说明**: 新增公文套红模板（红头名称、字号、印章、分隔线等样式配置）。

**请求参数 (OaOfficialDocTemplateSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | - | 模板编号（新增时不传） |
| name | String | 是 | @NotBlank、@Size(max=128) | 模板名称 |
| authorityName | String | 是 | @NotBlank、@Size(max=255) | 红头名称，如“芋道科技有限公司文件” |
| fontSize | Integer | 是 | @NotNull、@Min(18)、@Max(72) | 红头字号 |
| noPrefix | String | 否 | @Size(max=64) | 发文字号前缀 |
| sealPicUrl | String | 否 | @Size(max=2048) | 印章图片地址 |
| separatorType | Integer | 是 | @NotNull、@InDict(OFFICIAL_DOC_SEPARATOR_TYPE) | 分隔线类型（字典） |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum) | 状态：0 开启、1 停用 |
| sort | Integer | 是 | @NotNull | 显示顺序 |
| remark | String | 否 | @Size(max=500) | 备注 |

**响应**: CommonResult&lt;Long&gt; —— 模板编号。

**业务逻辑**:
1. 将请求 VO 转换为 DO（编号置空）。
2. 插入模板表并返回编号。

### 3.2 更新套红模板

- **路径**: PUT /oa/officialdoc-template/update
- **权限**: oa:officialdoc-template:update
- **说明**: 更新套红模板配置。

**请求参数 (OaOfficialDocTemplateSaveReqVO)**: 同 [3.1 创建套红模板](#31-创建套红模板)，其中 `id` 必传。

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验模板存在。
2. 按编号更新模板。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_000 | 套红模板不存在 |

### 3.3 删除套红模板

- **路径**: DELETE /oa/officialdoc-template/delete
- **权限**: oa:officialdoc-template:delete
- **说明**: 删除未被发文引用的套红模板，已有发文继续保留原模板内容。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 是否成功。

**业务逻辑**:
1. 校验模板存在。
2. 校验模板未被发文单据引用（引用计数大于 0 则拒绝删除）。
3. 删除模板记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_054_260_000 | 套红模板不存在 |
| 1_054_260_008 | 套红模板已有业务单据引用，不能删除 |

### 3.4 获得套红模板分页列表

- **路径**: GET /oa/officialdoc-template/page
- **权限**: oa:officialdoc-template:query
- **说明**: 按名称、状态分页查询模板，按显示顺序升序、编号倒序排列。

**请求参数 (OaOfficialDocTemplatePageReqVO)**，继承 PageParam（pageNo/pageSize）:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| name | String | 否 | - | 模板名称（模糊查询） |
| status | Integer | 否 | - | 状态：0 开启、1 停用 |

**响应**: CommonResult&lt;PageResult&lt;OaOfficialDocTemplateRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模板名称 |
| authorityName | String | 红头名称 |
| fontSize | Integer | 红头字号 |
| noPrefix | String | 发文字号前缀 |
| sealPicUrl | String | 印章图片地址 |
| separatorType | Integer | 分隔线类型 |
| status | Integer | 状态 |
| sort | Integer | 显示顺序 |
| remark | String | 备注 |
| creator | String | 创建人编号 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按名称（模糊）、状态条件分页查询模板。
2. 按 sort 升序、id 倒序排序，转换为 RespVO 返回。

### 3.5 获得套红模板精简列表

- **路径**: GET /oa/officialdoc-template/simple-list
- **权限**: 已认证（仅登录，无 @PreAuthorize 权限校验）
- **说明**: 供发文表单下拉选择，仅返回启用状态的模板编号与名称。

**请求参数**: 无

**响应**: CommonResult&lt;List&lt;OaOfficialDocTemplateRespVO&gt;&gt; —— 仅填充 id、name 字段。

**业务逻辑**:
1. 查询状态为启用（ENABLE）的模板列表，按 sort 升序、id 倒序。
2. 转换为仅含编号与名称的精简 RespVO 列表返回。

### 3.6 获得套红模板详情

- **路径**: GET /oa/officialdoc-template/get
- **权限**: oa:officialdoc-template:query
- **说明**: 查询套红模板完整配置。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam | 模板编号 |

**响应**: CommonResult&lt;OaOfficialDocTemplateRespVO&gt; —— 字段同 [3.4 分页列表](#34-获得套红模板分页列表)。

**业务逻辑**:
1. 按编号查询模板并转换为 RespVO 返回。

## 附：公文管理错误码汇总（1-054-260-000 段）

| 错误码 | 说明 |
|-------|------|
| 1_054_260_000 | 套红模板不存在 |
| 1_054_260_001 | 公文不存在 |
| 1_054_260_002 | 无权操作该公文 |
| 1_054_260_003 | 当前公文状态不允许该操作 |
| 1_054_260_004 | 公文与流程实例不匹配 |
| 1_054_260_005 | 套红模板已停用 |
| 1_054_260_006 | 收文单据编号已存在 |
| 1_054_260_007 | 发文单据编号已存在 |
| 1_054_260_008 | 套红模板已有业务单据引用，不能删除 |
| 1_054_260_009 | 发文字号已存在 |

> 说明：审批状态跟随 BPM 流程实例状态（未开始/审批中/审批通过/审批不通过/已取消）；发文审批通过后由流程回调按主送/抄送部门自动生成收文记录（同一类型部门不重复投递），回调时的流程实例不匹配会抛出 1_054_260_004。
