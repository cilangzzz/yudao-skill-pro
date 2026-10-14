# 离职申请接口 (OaResignApplyController)

> 员工创建离职申请草稿、提交至 BPM 流程审批，并查询本人的离职申请记录。

## 接口路径前缀
/oa/resign-apply  (Controller: OaResignApplyController)

## 1. 申请管理

### 1.1 创建离职申请草稿
- **路径**: POST /oa/resign-apply/create
- **权限**: oa:resign-apply:create
- **说明**: 新建一条离职申请草稿，返回申请编号。

**请求参数 (OaResignApplySaveReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 申请编号（新增时不传） |
| title | String | 是 | @NotBlank、@Size(max=255) | 标题 |
| urgency | Integer | 是 | @NotNull、@InDict(DictTypeConstants.APPLY_URGENCY) | 紧急程度（字典值） |
| handoverUserId | Long | 是 | @NotNull | 工作交接人用户编号 |
| unfinishedWork | String | 是 | @NotBlank | 未完成事宜 |
| reason | String | 是 | @NotBlank、@Size(max=5000) | 申请原因 |
| hasPendingReimbursement | Boolean | 是 | @NotNull | 是否有费用报销未完成 |

**响应**: CommonResult&lt;Long&gt;
| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新建的申请编号 |

**业务逻辑**:
1. 调用 AdminUserApi 校验工作交接人（handoverUserId）存在。
2. 将请求 VO 转换为 DO，并设置审批状态为「未开始」（NOT_START）。
3. 插入离职申请记录，返回自增主键作为申请编号。

### 1.2 更新离职申请草稿
- **路径**: PUT /oa/resign-apply/update
- **权限**: oa:resign-apply:create
- **说明**: 修改本人尚未提交的离职申请草稿。

**请求参数 (OaResignApplySaveReqVO)**: 同 1.1，其中 id 必传（对应 @Schema 申请编号，Service 层校验非空及归属）。

**响应**: CommonResult&lt;Boolean&gt;
| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否更新成功（固定返回 true） |

**业务逻辑**:
1. 校验申请可修改：申请必须存在（否则 APPLY_NOT_EXISTS）、必须属于当前登录用户（否则 APPLY_ACCESS_DENIED）、状态必须为「未开始」草稿（否则 APPLY_STATUS_INVALID）。
2. 再次校验工作交接人（handoverUserId）存在。
3. 按编号更新离职申请记录。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

### 1.3 提交离职申请
- **路径**: POST /oa/resign-apply/submit
- **权限**: oa:resign-apply:create
- **说明**: 将本人的离职申请草稿提交发起 BPM 审批流程。

**请求参数 (OaResignApplySubmitReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 申请编号 |
| startUserSelectAssignees | Map&lt;String, List&lt;Long&gt;&gt; | 否 | - | 发起人自选审批人（key 为节点标识，value 为候选用户编号列表） |

**响应**: CommonResult&lt;Boolean&gt;
| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 是否提交成功（固定返回 true） |

**业务逻辑**:
1. 校验申请可提交：申请存在、归属当前登录用户、状态为「未开始」草稿（否则分别抛 APPLY_NOT_EXISTS / APPLY_ACCESS_DENIED / APPLY_STATUS_INVALID）。
2. 将申请状态更新为「审批中」（RUNNING）。
3. 以流程定义 key `oa_resign_apply`、businessKey 为申请编号发起流程实例，流程变量携带 `hasPendingReimbursement`（是否有未完成报销），并传入发起人自选审批人。
4. 将返回的流程实例编号回写到离职申请记录。

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_280_000 | 申请不存在 |
| 1_054_280_001 | 无权查看该申请 |
| 1_054_280_004 | 申请状态不允许该操作 |

### 1.4 获得本人离职申请分页
- **路径**: GET /oa/resign-apply/page
- **权限**: oa:resign-apply:query
- **说明**: 分页查询当前登录用户本人的离职申请列表。

**请求参数 (OaResignApplyPageReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承 PageParam，默认 10） |
| title | String | 否 | - | 标题（模糊匹配） |
| status | Integer | 否 | - | 审批状态 |

**响应**: CommonResult&lt;PageResult&lt;OaResignApplyRespVO&gt;&gt;
| 字段 | 类型 | 说明 |
|-----|------|------|
| list | List&lt;OaResignApplyRespVO&gt; | 申请列表 |
| total | Long | 总条数 |

OaResignApplyRespVO 字段:
| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| title | String | 标题 |
| urgency | Integer | 紧急程度 |
| reason | String | 申请原因 |
| handoverUserId | Long | 工作交接人用户编号 |
| unfinishedWork | String | 未完成事宜 |
| hasPendingReimbursement | Boolean | 是否有费用报销未完成 |
| suggestion | String | 申请人意见建议 |
| status | Integer | 审批状态 |
| processInstanceId | String | 流程实例编号 |
| creator | String | 申请人编号 |
| creatorName | String | 申请人昵称 |
| createTime | LocalDateTime | 申请时间 |

**业务逻辑**:
1. 以当前登录用户编号为条件，通过 Mapper 分页查询本人的离职申请。
2. 批量查询申请人（creator）对应的系统用户信息。
3. 将 DO 转换为 RespVO，并拼接申请人昵称（creatorName）。

### 1.5 获得离职申请详情
- **路径**: GET /oa/resign-apply/get
- **权限**: oa:resign-apply:query
- **说明**: 按编号查询单条离职申请详情；不存在时返回 null。

**请求参数 (Query 参数)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam(required) | 申请编号 |

**响应**: CommonResult&lt;OaResignApplyRespVO&gt;，字段同 1.4。

**业务逻辑**:
1. 按编号查询离职申请记录（selectById）。
2. 存在时批量查询申请人信息，转换为 RespVO 并拼接申请人昵称；不存在时返回 null。
