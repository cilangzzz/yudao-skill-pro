# OA 任务接口 (OaTaskController)

> OA 任务的发布与执行管理：发布人创建/更新/删除任务并指派接收人，接收人反馈进度，提供我的任务分页、状态统计与完成排行。

## 接口路径前缀
/oa/task  (Controller: OaTaskController)

## 1. 我发布的任务

### 1.1 创建任务
- **路径**: POST /oa/task/create
- **权限**: oa:task:create
- **说明**: 发布人创建任务并指派接收人，返回任务编号

**请求参数 (OaTaskSaveReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 否 | - | 任务编号（新增不传，更新必传） |
| type | Integer | 是 | @NotNull、@InEnum(OaTaskTypeEnum) | 任务类型（1 公事、2 私事） |
| status | Integer | 是 | @NotNull、@InEnum(OaTaskStatusEnum) | 任务状态（1 新任务、2 已接收、3 进行中、4 已提交、5 已完成） |
| top | Boolean | 是 | @NotNull | 是否置顶 |
| canceled | Boolean | 是 | @NotNull | 是否取消 |
| title | String | 是 | @NotBlank、@Size(max=255) | 任务标题 |
| description | String | 是 | @NotBlank、@Size(max=2000) | 任务描述 |
| comment | String | 否 | @Size(max=1000) | 任务评价 |
| startTime | LocalDateTime | 是 | @NotNull | 开始时间 |
| endTime | LocalDateTime | 是 | @NotNull、类级 @AssertTrue 须晚于 startTime | 结束时间 |
| receiverUserIds | List\<Long\> | 是 | @NotEmpty、元素 @NotNull | 接收人用户编号列表 |

**响应**: CommonResult\<Long\> — 任务编号

**业务逻辑**:
1. 校验接收人用户编号列表全部有效（AdminUserApi.validateUserList）
2. 新增任务，发布时间取当前时间
3. 批量新增任务接收人记录，每个接收人的初始进度与发布人选择的任务状态一致
4. 返回新任务编号

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_170_000 | 任务不存在 |
| 1_054_170_001 | 无权访问该任务 |

### 1.2 更新任务
- **路径**: PUT /oa/task/update
- **权限**: oa:task:update
- **说明**: 发布人修改任务信息、总体状态及接收人列表

**请求参数 (OaTaskSaveReqVO)**: 同 1.1（id 更新时必传）

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验任务存在且属于当前发布人（否则报无权访问），并校验接收人用户列表有效
2. 按发布人表单更新任务信息及总体状态，发布时间刷新为当前时间
3. 对比现有接收人与表单接收人：删除不再接收的关系，新增的接收人以表单状态作为初始进度
4. 表单状态同步覆盖全部当前接收人的进度

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_170_000 | 任务不存在 |
| 1_054_170_001 | 无权访问该任务 |

### 1.3 删除发布的任务
- **路径**: DELETE /oa/task/delete
- **权限**: oa:task:delete
- **说明**: 发布人删除自己发布的任务及其关联数据

**请求参数**: Query 参数
| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 任务编号 |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验任务存在且属于当前发布人（否则报无权访问）
2. 依次删除任务的反馈日志、接收人关系和任务本身

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_170_000 | 任务不存在 |
| 1_054_170_001 | 无权访问该任务 |

### 1.4 获得我发布的任务分页
- **路径**: GET /oa/task/published-page
- **权限**: oa:task:query
- **说明**: 分页返回当前登录用户发布的任务，附带接收人列表信息

**请求参数 (OaTaskPageReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数 |
| title | String | 否 | - | 标题（模糊匹配） |
| type | Integer | 否 | @InEnum(OaTaskTypeEnum) | 任务类型 |
| status | Integer | 否 | @InEnum(OaTaskStatusEnum) | 任务状态 |
| canceled | Boolean | 否 | - | 是否取消 |
| publisherUserId | Long | 否 | - | 发布人用户编号（本接口固定为当前登录用户） |
| publishTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 发布时间范围 |

**响应**: CommonResult\<PageResult\<OaTaskRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 任务编号 |
| publisherUserId | Long | 发布人用户编号 |
| publisherUserName | String | 发布人昵称 |
| publisherDeptName | String | 发布人部门名称 |
| type | Integer | 任务类型 |
| status | Integer | 总体状态 |
| receiverStatus | Integer | 当前登录用户作为接收人的状态 |
| title | String | 标题 |
| description | String | 任务描述 |
| comment | String | 任务评价 |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| top | Boolean | 是否置顶 |
| canceled | Boolean | 是否取消 |
| receivers | List\<OaTaskReceiverRespVO\> | 接收人列表（id、userId、userName、deptName、status、updateTime） |
| logs | List\<OaTaskLogRespVO\> | 反馈日志列表（id、userId、userName、status、content、createTime），分页接口为空 |
| publishTime | LocalDateTime | 发布时间 |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 修改时间 |

**业务逻辑**:
1. 按发布人 = 当前登录用户及查询条件分页查询任务
2. 批量查询任务接收人，汇总发布人、接收人相关用户与部门信息
3. 拼装响应：填充发布人昵称/部门、接收人昵称/部门/状态，以及当前登录用户的接收状态

**错误码**: 无

## 2. 我的任务

### 2.1 删除接收的任务
- **路径**: DELETE /oa/task/delete-received
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 接收人删除自己收到的任务（仅限发布人已取消的任务）

**请求参数**: Query 参数
| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 任务编号 |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验任务存在，且当前用户是该任务的接收人
2. 校验任务已被发布人取消（canceled=true），否则报"只能删除已取消的接收任务"
3. 仅删除当前用户的接收关系，不影响其他接收人和任务本身
4. 根据剩余接收人的最低进度回写任务总体状态

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_170_000 | 任务不存在 |
| 1_054_170_003 | 当前用户不是该任务的接收人 |
| 1_054_170_004 | 任务状态流转不合法 |
| 1_054_170_006 | 只能删除已取消的接收任务 |

### 2.2 获得我的任务分页
- **路径**: GET /oa/task/received-page
- **权限**: oa:task:query
- **说明**: 分页返回当前登录用户作为接收人的任务

**请求参数 (OaTaskPageReqVO)**: 同 1.4

**响应**: CommonResult\<PageResult\<OaTaskRespVO\>\> — 字段同 1.4

**业务逻辑**:
1. 查询当前登录用户（可按状态过滤）的任务接收记录，为空直接返回空分页
2. 按接收记录中的任务编号集合分页查询任务
3. 拼装响应：填充发布人昵称/部门、接收人昵称/部门/状态，以及当前登录用户的接收状态

**错误码**: 无

## 3. 公共操作

### 3.1 创建任务反馈
- **路径**: POST /oa/task/feedback
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 发布人调整任务总体状态，或接收人反馈自己的任务进度，并记录反馈日志

**请求参数 (OaTaskFeedbackReqVO)**:
| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| taskId | Long | 是 | @NotNull | 任务编号 |
| publisher | Boolean | 是 | @NotNull | 是否从发布管理反馈（true 发布人视角、false 接收人视角） |
| status | Integer | 是 | @NotNull、@InEnum(OaTaskStatusEnum) | 任务状态 |
| content | String | 否 | @Size(max=1000) | 反馈内容 |

**响应**: CommonResult\<Boolean\> — 是否成功

**业务逻辑**:
1. 校验任务存在且未取消，已取消任务报"任务状态流转不合法"
2. 发布人反馈（publisher=true）：校验当前用户是发布人，更新任务总体状态并同步覆盖全部接收人进度
3. 接收人反馈（publisher=false）：校验当前用户是接收人；当前进度须小于"已提交"，且目标状态在新任务~已提交（1-4）之间，否则报"任务状态流转不合法"；更新该接收人进度，并按所有接收人最低进度回写任务总体状态
4. 插入反馈日志，记录反馈人、状态变化和反馈内容

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_170_000 | 任务不存在 |
| 1_054_170_001 | 无权访问该任务 |
| 1_054_170_003 | 当前用户不是该任务的接收人 |
| 1_054_170_004 | 任务状态流转不合法 |

### 3.2 获得任务详情
- **路径**: GET /oa/task/get
- **权限**: oa:task:query
- **说明**: 获取任务详情，含接收人列表与反馈日志，仅发布人或接收人可见

**请求参数**: Query 参数
| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| id | Long | 是 | 任务编号 |

**响应**: CommonResult\<OaTaskRespVO\> — 字段同 1.4（logs 为该任务全部反馈日志，receiverStatus 为当前登录用户的接收状态）

**业务逻辑**:
1. 校验任务存在，且当前用户是发布人或接收人，否则报"无权访问该任务"
2. 查询任务的反馈日志列表
3. 拼装响应：填充发布人昵称/部门、接收人昵称/部门/状态、反馈日志昵称，以及当前登录用户的接收状态

**错误码**:
| 错误码 | 说明 |
|-------|------|
| 1_054_170_000 | 任务不存在 |
| 1_054_170_001 | 无权访问该任务 |

## 4. 任务统计

### 4.1 获得我的任务状态统计
- **路径**: GET /oa/task/get-status-count
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 统计当前登录用户在各接收状态下（按接收记录）的任务数量

**请求参数**: 无

**响应**: CommonResult\<Map\<Integer, Long\>\> — key 为任务状态（1-5），value 为任务数量

**业务逻辑**:
1. 按当前登录用户分组统计其接收记录中各状态的任务数量并返回

**错误码**: 无

### 4.2 获得任务完成排行
- **路径**: GET /oa/task/get-completed-ranking
- **权限**: 已认证（仅登录，无 @PreAuthorize）
- **说明**: 统计发布"已完成"任务数量最多的前 5 名用户

**请求参数**: 无

**响应**: CommonResult\<List\<OaTaskRankingRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| userName | String | 用户昵称 |
| completedCount | Long | 完成任务数量 |

**业务逻辑**:
1. 统计状态为"已完成"的任务按发布人分组的数量
2. 按完成数量降序、用户编号升序排序后取前 5 名
3. 批量查询用户信息，填充用户昵称；无完成数据时返回空列表

**错误码**: 无
