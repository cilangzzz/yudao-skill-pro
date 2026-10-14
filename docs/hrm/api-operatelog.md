# 操作日志接口 (HrmOperateLogController)

> 查询 HRM 各业务（招聘职位、招聘候选人、员工档案、绩效考核、绩效计划）的操作日志，实际数据由 system 模块 `OperateLogApi` 提供，HRM 本地无日志表。日志写入由各业务 `ServiceImpl` 的 `@LogRecord` 注解（mzt-biz-log 切面）自动完成，文案常量定义于 `enums/LogRecordConstants`。

## 接口路径前缀

/hrm/operate-log  (Controller: HrmOperateLogController)

## 1. 操作日志查询

### 1.1 获得操作日志（分页查询某业务对象的全部操作日志）

- **路径**: GET /hrm/operate-log/page
- **权限**: `hrm:recruit:post:query` / `hrm:recruit:candidate:query` / `hrm:employee:query` / `hrm:performance:plan:query`（@PreAuthorize hasAnyPermissions，拥有任一权限即可访问）
- **说明**: 按业务类型 + 业务编号查询该对象的操作日志列表，一次性返回全部记录（内部不分页）。

**请求参数 (HrmOperateLogPageReqVO)**: （继承 PageParam，分页参数仅作占位，实际查询不分页）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 否 | — | 页码（继承 PageParam，实际不生效） |
| pageSize | Integer | 否 | — | 每页条数（继承 PageParam，实际被强制置为 -1 全量查询） |
| bizType | Integer | 是 | @NotNull、@InEnum(HrmBizTypeEnum.class) | 业务类型：1 招聘职位、2 招聘候选人、3 员工档案、4 绩效考核、5 绩效计划 |
| bizId | Long | 是 | @NotNull | 业务编号（对应业务对象的主键） |

**响应**: CommonResult&lt;PageResult&lt;HrmOperateLogRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 日志编号 |
| userId | Long | 操作用户编号 |
| userName | String | 操作用户名称 |
| userType | Integer | 操作用户类型 |
| type | String | 日志类型（模块类型字符串，如 "HRM 招聘职位"） |
| subType | String | 日志子类型（操作动作，如 "更新招聘职位"） |
| bizId | Long | 业务编号 |
| action | String | 操作内容（@LogRecord 模板渲染后的文案） |
| extra | String | 拓展字段（JSON 字符串，如差量信息） |
| createTime | LocalDateTime | 操作时间 |

**业务逻辑**:
1. 校验请求参数：`bizType` 必填且必须为 `HrmBizTypeEnum` 枚举值，`bizId` 必填。
2. 控制器通过静态 `BIZ_TYPE_MAP` 将 HRM 业务类型映射为操作日志的模块类型字符串：1→`HRM 招聘职位`、2→`HRM 招聘候选人`、3→`HRM 员工档案`、4→`HRM 绩效考核`、5→`HRM 绩效计划`（常量定义于 `LogRecordConstants`）。
3. 构造 system 模块的 `OperateLogPageReqDTO`：`pageSize` 固定设置为 `PAGE_SIZE_NONE`（-1，即不分页、一次查出全部日志），仅复用 `type` + `bizId` 作为过滤条件。
4. 调用 system 模块 `OperateLogApi#getOperateLogPage`（本进程内 API），其委托 `OperateLogService` → `OperateLogMapper#selectPage`，按 `type` 精确 + `bizId` 精确匹配查询 `system_operate_log` 表，并按 id 倒序返回。
5. 通过 `BeanUtils` 将 `OperateLogRespDTO` 分页结果转换为 `HrmOperateLogRespVO` 后返回。

**错误码**: HRM 模块无操作日志专属错误码（该端点为只读查询，业务对象不存在时返回空列表）。以下为查询目标业务对象的相关错误码，供参考：

| 错误码 | 说明 |
|-------|------|
| 1_050_200_000 | 招聘职位不存在（bizType=1 对应对象） |
| 1_050_200_001 | 招聘候选人不存在（bizType=2 对应对象） |
| 1_050_100_000 | 员工档案不存在（bizType=3 对应对象） |
| 1_050_600_006 | 员工绩效考核不存在（bizType=4 对应对象） |
| 1_050_600_004 | 绩效计划不存在（bizType=5 对应对象） |
