# 跟进记录接口 (CrmFollowUpRecordController)

> 提供 CRM 各业务对象（客户/商机/线索/联系人/合同）的跟进记录创建、删除与查询能力，创建跟进时会联动更新对应业务对象的跟进信息与下次联系时间。

## 接口路径前缀

/crm/follow-up-record  (Controller: CrmFollowUpRecordController)

## 1. 跟进记录管理

### 1.1 创建跟进记录

- **路径**: POST /crm/follow-up-record/create
- **权限**: 已认证（Controller 未加 @PreAuthorize，Service 层通过 @CrmPermission 按 bizType/bizId 校验当前用户的 WRITE 权限）
- **说明**: 创建一条跟进记录，并联动更新关联业务对象（客户/商机/线索/联系人/合同）的跟进信息及下次联系时间。

**请求参数 (CrmFollowUpRecordSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 编号（新增时可不传） |
| bizType | Integer | 是 | @NotNull | 数据类型（来自 CrmBizTypeEnum：客户/商机/线索/联系人/合同等） |
| bizId | Long | 是 | @NotNull | 数据编号（关联业务对象的主键） |
| type | Integer | 是 | @NotNull | 跟进类型（字典 CRM_FOLLOW_UP_TYPE） |
| content | String | 是 | @NotEmpty | 跟进内容 |
| nextTime | LocalDateTime | 是 | @NotNull | 下次联系时间 |
| businessIds | List&lt;Long&gt; | 否 | - | 关联的商机编号数组 |
| contactIds | List&lt;Long&gt; | 否 | - | 关联的联系人编号数组 |
| picUrls | List&lt;String&gt; | 否 | - | 图片 |
| fileUrls | List&lt;String&gt; | 否 | - | 附件 |

**响应**: CommonResult&lt;Long&gt; —— 新创建的跟进记录编号。

**业务逻辑**:
1. 通过 @CrmPermission 注解按请求中的 bizType/bizId 校验当前用户对该业务数据拥有 WRITE 权限。
2. 将请求 VO 转换为 CrmFollowUpRecordDO 并插入跟进记录表。
3. 按 bizType 联动更新对应业务对象的跟进信息（最近跟进内容 content 与下次联系时间 nextTime）：客户走 customerService.updateCustomerFollowUp、商机走 businessService.updateBusinessFollowUp、线索走 clueService.updateClueFollowUp、联系人走 contactService.updateContactFollowUp、合同走 contractService.updateContractFollowUp。
4. 若 contactIds 非空，批量更新这些联系人的下次联系时间（updateContactContactNextTime）。
5. 若 businessIds 非空，批量更新这些商机的下次联系时间（updateBusinessContactNextTime）。
6. 返回新记录的编号。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_007_001 | {}操作失败，原因：没有权限（CRM_PERMISSION_DENIED，由 @CrmPermission 校验失败抛出） |

### 1.2 删除跟进记录

- **路径**: DELETE /crm/follow-up-record/delete
- **权限**: 已认证（Controller 未加 @PreAuthorize，Service 层校验当前用户对该记录所属业务数据拥有 OWNER 权限）
- **说明**: 删除指定跟进记录，仅业务数据负责人可删除。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 跟进记录编号 |

**响应**: CommonResult&lt;Boolean&gt; —— 固定返回 true。

**业务逻辑**:
1. 校验跟进记录是否存在，不存在抛出 FOLLOW_UP_RECORD_NOT_EXISTS。
2. 通过 permissionService.hasPermission 校验当前用户对该记录的 bizType/bizId 拥有 OWNER（负责人）权限，否则抛出 FOLLOW_UP_RECORD_DELETE_DENIED。
3. 执行 deleteById 逻辑删除该跟进记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_013_000 | 跟进记录不存在 |
| 1_020_013_001 | 删除跟进记录失败，原因：没有权限 |

### 1.3 获得跟进记录

- **路径**: GET /crm/follow-up-record/get
- **权限**: 已认证（Controller 内通过 permissionService.hasPermission 校验当前用户对该记录所属业务数据拥有 READ 权限）
- **说明**: 根据编号获得单条跟进记录详情。

**请求参数**: 无请求体，Query 参数：

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 跟进记录编号 |

**响应**: CommonResult&lt;CrmFollowUpRecordRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| bizType | Integer | 数据类型 |
| bizId | Long | 数据编号 |
| type | Integer | 跟进类型（字典 CRM_FOLLOW_UP_TYPE） |
| content | String | 跟进内容 |
| nextTime | LocalDateTime | 下次联系时间 |
| businessIds | List&lt;Long&gt; | 关联的商机编号数组 |
| businesses | List&lt;CrmBusinessRespVO&gt; | 关联的商机数组（仅分页接口填充） |
| contactIds | List&lt;Long&gt; | 关联的联系人编号数组 |
| contacts | List&lt;CrmBusinessRespVO&gt; | 关联的联系人名称数组（仅分页接口填充） |
| picUrls | List&lt;String&gt; | 图片 |
| fileUrls | List&lt;String&gt; | 附件 |
| creator | String | 创建人（用户编号） |
| creatorName | String | 创建人名字（仅分页接口填充） |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 查询跟进记录，不存在抛出 FOLLOW_UP_RECORD_NOT_EXISTS。
2. 通过 permissionService.hasPermission 校验当前用户对该记录的 bizType/bizId 拥有 READ 权限，否则抛出 CRM_PERMISSION_DENIED（提示对应业务类型名称）。
3. 将 DO 转换为 CrmFollowUpRecordRespVO 返回（get 接口不额外填充联系人/商机名称数组）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_013_000 | 跟进记录不存在 |
| 1_020_007_001 | {}操作失败，原因：没有权限 |

### 1.4 获得跟进记录分页

- **路径**: GET /crm/follow-up-record/page
- **权限**: 已认证（Controller 未加 @PreAuthorize，Service 层通过 @CrmPermission 按 bizType/bizId 校验当前用户的 READ 权限）
- **说明**: 分页获得指定业务对象（bizType + bizId）下的跟进记录列表，并填充关联联系人、商机与创建人信息。

**请求参数 (CrmFollowUpRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，最大 200（继承自 PageParam） |
| bizType | Integer | 否 | - | 数据类型（来自 CrmBizTypeEnum） |
| bizId | Long | 否 | - | 数据编号 |

**响应**: CommonResult&lt;PageResult&lt;CrmFollowUpRecordRespVO&gt;&gt;，列表元素字段同 1.3 的 CrmFollowUpRecordRespVO。

**业务逻辑**:
1. 通过 @CrmPermission 注解按请求中的 bizType/bizId 校验当前用户拥有 READ 权限。
2. 调用 Mapper 执行分页查询得到跟进记录分页结果。
3. 收集分页结果中所有记录的 contactIds，批量查询联系人 Map；收集所有 businessIds，批量查询商机 Map。
4. 收集所有记录的 creator（用户编号），批量查询系统用户 Map。
5. 逐条拼装 RespVO：将 contactIds/businessIds 转换为带 id 与名称的 contacts/businesses 数组，并设置 creatorName 为创建人昵称。
6. 返回填充后的分页结果。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_020_007_001 | {}操作失败，原因：没有权限 |
