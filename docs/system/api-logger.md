# 日志管理接口 (LoginLogController, OperateLogController)

> 提供管理后台的登录日志与操作日志查询、明细查看及 Excel 导出能力，日志数据由框架自动记录（登录事件、@ApiAccessLog 切面），本域仅提供只读查询与导出，无创建/修改/删除端点。

## 接口路径前缀

- /system/login-log  (Controller: LoginLogController) —— 登录日志
- /system/operate-log  (Controller: OperateLogController) —— 操作日志

说明：本域在 system 模块的 ErrorCodeConstants 中无专属错误码（查询类端点无业务校验失败场景），故各端点不再单列错误码表。

## 1. 登录日志（LoginLogController）

### 1.1 获得登录日志

- **路径**: GET /system/login-log/get
- **权限**: system:login-log:query
- **说明**: 按编号查询单条登录日志明细。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
| id | Long | 是 | @RequestParam 必传 | 日志编号 |

**响应**: CommonResult&lt;LoginLogRespVO&gt;

| 字段 | 类型 | 说明 |
| id | Long | 日志编号 |
| logType | Integer | 日志类型，参见 LoginLogTypeEnum 枚举 |
| userId | Long | 用户编号 |
| userType | Integer | 用户类型，参见 UserTypeEnum 枚举 |
| traceId | String | 链路追踪编号 |
| username | String | 用户账号 |
| result | Integer | 登录结果，参见 LoginResultEnum 枚举 |
| userIp | String | 用户 IP |
| userAgent | String | 浏览器 UserAgent |
| createTime | LocalDateTime | 登录时间 |

**业务逻辑**:
1. Controller 接收请求参数 id（日志编号）。
2. 调用 LoginLogService.getLoginLog(id)，Service 通过 LoginLogMapper.selectById 按主键查询 LoginLogDO。
3. 使用 BeanUtils.toBean 将 LoginLogDO 转换为 LoginLogRespVO 返回。

### 1.2 获得登录日志分页列表

- **路径**: GET /system/login-log/page
- **权限**: system:login-log:query
- **说明**: 按条件分页查询登录日志。

**请求参数 (LoginLogPageReqVO，继承 PageParam)**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| userIp | String | 否 | 无 | 用户 IP，模糊匹配 |
| username | String | 否 | 无 | 用户账号，模糊匹配 |
| status | Boolean | 否 | 无 | 操作状态：true 只查登录成功，false 只查登录失败 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 登录时间范围（起止区间） |

**响应**: CommonResult&lt;PageResult&lt;LoginLogRespVO&gt;&gt;，列表项字段同 1.1 的响应字段表。

**业务逻辑**:
1. Controller 通过 @Valid 校验分页与筛选参数。
2. 调用 LoginLogService.getLoginLogPage(pageReqVO)。
3. Mapper 构建 LambdaQueryWrapperX：userIp 模糊匹配、username 模糊匹配、createTime 区间过滤（均为条件存在才生效）。
4. status=true 时追加 result = LoginResultEnum.SUCCESS 条件；status=false 时追加 result > SUCCESS 条件（即失败）。
5. 按 id 降序排序，执行分页查询返回 PageResult。
6. Controller 使用 BeanUtils.toBean 将分页结果转换为 LoginLogRespVO 返回。

### 1.3 导出登录日志 Excel

- **路径**: GET /system/login-log/export-excel
- **权限**: system:login-log:export
- **说明**: 按与分页查询相同的筛选条件导出全部登录日志为 Excel 文件。

**请求参数 (LoginLogPageReqVO)**: 字段同 1.2 的请求参数表（pageSize 将被强制设置为不分页）。

**响应**: 无 CommonResult 包装，直接向 HttpServletResponse 输出 `登录日志.xls` 文件流（表头列：日志主键、日志类型、用户账号、登录结果、登录 IP、浏览器 UA、登录时间；字典字段经 DictConvert 按字典转换）。

**业务逻辑**:
1. Controller 将 exportReqVO 的 pageSize 设置为 PageParam.PAGE_SIZE_NONE（-1，不分页）。
2. 复用 LoginLogService.getLoginLogPage 查询全部符合条件的数据。
3. 使用 BeanUtils.toBean 将 LoginLogDO 列表转换为 LoginLogRespVO 列表。
4. ExcelUtils.write 输出为 `登录日志.xls` 文件流。
5. 方法标注 @ApiAccessLog(operateType = EXPORT)，本次导出行为本身会被记录为操作日志。

## 2. 操作日志（OperateLogController）

### 2.1 查看操作日志

- **路径**: GET /system/operate-log/get
- **权限**: system:operate-log:query
- **说明**: 按编号查询单条操作日志明细。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
| id | Long | 是 | @RequestParam 必传 | 日志编号 |

**响应**: CommonResult&lt;OperateLogRespVO&gt;

| 字段 | 类型 | 说明 |
| id | Long | 日志编号 |
| traceId | String | 链路追踪编号 |
| userId | Long | 用户编号（@Trans 注解自动翻译） |
| userName | String | 用户昵称（操作人，由 userId 翻译 AdminUserDO.nickname 得到） |
| userType | Integer | 用户类型（字典 USER_TYPE） |
| type | String | 操作模块类型 |
| subType | String | 操作名 |
| bizId | Long | 操作模块业务编号 |
| action | String | 操作明细 |
| extra | String | 拓展字段 |
| requestMethod | String | 请求方法名 |
| requestUrl | String | 请求地址 |
| userIp | String | 用户 IP |
| userAgent | String | 浏览器 UserAgent |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. Controller 接收请求参数 id（日志编号）。
2. 调用 OperateLogService.getOperateLog(id)，Service 通过 OperateLogMapper.selectById 按主键查询 OperateLogDO。
3. 使用 BeanUtils.toBean 将 OperateLogDO 转换为 OperateLogRespVO 返回。

### 2.2 查看操作日志分页列表

- **路径**: GET /system/operate-log/page
- **权限**: system:operate-log:query
- **说明**: 按条件分页查询操作日志，结果自动翻译用户昵称。

**请求参数 (OperateLogPageReqVO，继承 PageParam)**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10 |
| userId | Long | 否 | 无 | 用户编号，精确匹配 |
| bizId | Long | 否 | 无 | 操作模块业务编号，精确匹配 |
| type | String | 否 | 无 | 操作模块，模糊匹配 |
| subType | String | 否 | 无 | 操作名，模糊匹配 |
| action | String | 否 | 无 | 操作明细，模糊匹配 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 开始时间范围（起止区间） |

**响应**: CommonResult&lt;PageResult&lt;OperateLogRespVO&gt;&gt;，列表项字段同 2.1 的响应字段表。

**业务逻辑**:
1. Controller 通过 @Valid 校验分页与筛选参数。
2. 调用 OperateLogService.getOperateLogPage(pageReqVO)。
3. Mapper 构建 LambdaQueryWrapperX：userId、bizId 精确匹配，type、subType、action 模糊匹配，createTime 区间过滤（均为条件存在才生效）。
4. 按 id 降序排序，执行分页查询返回 PageResult。
5. Controller 使用 BeanUtils.toBean 将分页结果转换为 OperateLogRespVO 返回。
6. 方法标注 @TransMethodResult，基于 RespVO 上的 @Trans(type = SIMPLE, target = AdminUserDO, fields = "nickname") 注解，将 userId 自动翻译为 userName（用户昵称）。

### 2.3 导出操作日志

- **路径**: GET /system/operate-log/export-excel
- **权限**: system:operate-log:export
- **说明**: 按与分页查询相同的筛选条件导出全部操作日志为 Excel 文件。

**请求参数 (OperateLogPageReqVO)**: 字段同 2.2 的请求参数表（pageSize 将被强制设置为不分页）。

**响应**: 无 CommonResult 包装，直接向 HttpServletResponse 输出 `操作日志.xls` 文件流（表头列：日志编号、操作人、用户类型、操作模块类型、操作名、操作模块业务编号）。

**业务逻辑**:
1. Controller 将 exportReqVO 的 pageSize 设置为 PageParam.PAGE_SIZE_NONE（-1，不分页）。
2. 复用 OperateLogService.getOperateLogPage 查询全部符合条件的数据。
3. 使用 BeanUtils.toBean 将 OperateLogDO 列表转换为 OperateLogRespVO 列表。
4. 调用 TranslateUtils.translate 对列表执行翻译（userId → userName 用户昵称）。
5. ExcelUtils.write 输出为 `操作日志.xls` 文件流。
6. 方法标注 @ApiAccessLog(operateType = EXPORT)，本次导出行为本身会被记录为操作日志。
