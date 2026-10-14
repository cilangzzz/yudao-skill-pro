# 流程评论接口 (BpmCommentController)

> 提供 BPM 流程实例的评论管理能力：查询指定流程实例下的全部评论（含审批操作记录），以及创建人工评论。

## 接口路径前缀

/bpm/comment  (Controller: BpmCommentController)

## 1. 评论查询

### 1.1 获得指定流程实例的评论列表

- **路径**: GET /bpm/comment/list-by-process-instance-id
- **权限**: bpm:task:query
- **说明**: 获得指定流程实例的评论列表，返回结果按 Flowable 评论记录拼装任务精简信息与评论人精简信息。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| processInstanceId | String | 是 | @Parameter required = true | 流程实例的编号 |

**响应**: CommonResult&lt;List&lt;BpmCommentRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | String | 评论编号 |
| taskId | String | 任务编号 |
| task | Task | 任务精简信息 |
| task.id | String | 任务编号 |
| task.name | String | 任务名称，例如“经理审批” |
| task.taskDefinitionKey | String | 任务定义的标识，例如 Activity_one |
| processInstanceId | String | 流程实例编号 |
| type | String | 评论类型，对应 BpmCommentTypeEnum（0 评论 / 1 审批通过 / 2 不通过 / 3 已取消 / 4 退回 / 5 委派发起 / 6 委派完成 / 7 转派 / 8 加签 / 9 减签） |
| message | String | 评论内容（取 Flowable Comment 的 fullMessage） |
| createTime | LocalDateTime | 创建时间（由 Flowable Comment 的 time 转换） |
| user | UserSimpleBaseVO | 评论人精简信息 |
| user.id | Long | 用户编号 |
| user.nickname | String | 用户昵称 |
| user.avatar | String | 用户头像 |
| user.deptId | Long | 部门编号 |
| user.deptName | String | 部门名称 |

**业务逻辑**:
1. 调用 BpmCommentService.getCommentListByProcessInstanceId，底层通过 Flowable TaskService.getProcessInstanceComments(processInstanceId) 获得该流程实例的全部评论；为空时直接返回空列表。
2. 收集评论关联的 taskId 集合，调用 taskService.getHistoricTaskMap 批量查询历史任务，构建任务 Map。
3. 收集评论的 userId（String 转 Long），调用 adminUserApi.getUserMap 批量查询管理员用户，构建用户 Map。
4. 遍历评论列表，将 Flowable Comment 转换为 BpmCommentRespVO：message 取 fullMessage、createTime 取 time 转换，并拼接 task（任务精简信息）与 user（用户精简信息）。
5. 返回评论 VO 列表。

## 2. 评论创建

### 2.1 创建流程评论

- **路径**: POST /bpm/comment/create
- **权限**: bpm:task:update
- **说明**: 在指定任务下创建一条类型为“评论”（COMMENT）的流程评论。

**请求参数 (BpmCommentCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| taskId | String | 是 | @NotEmpty | 任务编号 |
| message | String | 是 | @NotBlank、@Size(max = 500) | 评论内容，不能超过 500 个字符 |

**响应**: CommonResult&lt;Boolean&gt;，返回 true 表示创建成功。

**业务逻辑**:
1. 校验任务存在：调用 bpmTaskService.validateTaskExists(taskId)，任务不存在时抛出 TASK_NOT_EXISTS 错误。
2. 以任务所属的 processInstanceId 和任务 id，调用 Flowable TaskService.addComment 写入评论。
3. 评论类型固定为 BpmCommentTypeEnum.COMMENT（“0”），内容按模板 “{}” 直接格式化为 message。
4. 整个创建过程在事务中执行（@Transactional(rollbackFor = Exception.class)）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_009_005_002 | 流程任务不存在 |
