# 积木报表集成接口 (JmReportConfiguration)

> 积木报表（JimuReport）与积木仪表盘（JimuBI）的薄壳集成域：报表设计、打印设计、图形设计、大屏设计等 HTTP 端点由官方 starter 注入，本模块负责将 yudao 的 OAuth2 认证、租户、权限体系桥接给积木设计器。

## 接口路径前缀

- `/jmreport/**`  (积木报表 starter: jimureport-spring-boot-starter 2.3.4)
- `/drag/**`、`/jimubi/**`  (积木仪表盘 starter: jimubi-spring-boot-starter 2.3.2)

**本域无 yudao 自研 Controller**。全部 HTTP 端点由 `JmReportConfiguration` 的 `@ComponentScan("org.jeecg.modules.jmreport")` 扫描积木包注册，端点明细定义在 starter 内部（不在本仓库源码中），故按端点组说明。本模块自身暴露给 starter 的是一组**认证/权限/租户桥接回调**（第 2、3 节），starter 在处理 HTTP 请求时回调它们完成适配。

前置入口（system_menu）：`207 报表管理` 下挂 `208 报表设计器`（前端组件 `report/jmreport/index`）与 `919 仪表盘设计器`（前端组件 `report/jmreport/bi`），设计器页面内所有数据请求走上述路径前缀。

## 1. Starter 暴露的端点组

### 1.1 积木报表端点组 /jmreport/**

- **路径**: `/jmreport/**`
- **权限**: 已认证（Spring Security 层 `permitAll` 放行，实际认证由 2.1 verifyToken 回调完成；管理能力按 2.3 getRoles / 2.5 getPermissions 映射）
- **说明**: 积木报表设计器、打印设计、图形设计、报表预览等能力的前端页面与数据接口，对应管理后台菜单「报表管理 → 报表设计器」。

**请求参数**: 无（端点由 starter 内部定义，不走 yudao ReqVO 体系）

**响应**: 无 CommonResult 包装（starter 自行定义响应格式）

**业务逻辑**（请求的认证桥接流程）:
1. 请求进入后 Spring Security 因 `permitAll` 不做拦截，由 starter 回调 `JmReportTokenServiceImpl`（`JmReportTokenServiceI` 实现）完成认证。
2. `verifyToken` 校验积木前端传递的 `X-Access-Token`（见 2.1），通过后 `LoginUser` 写入 Spring Security 上下文。
3. 租户上下文通过 `getTenantId` 回调补齐（积木前端请求不携带 `tenant-id` Header）；`application.yaml` 中 `/jmreport/*` 已加入 `yudao.tenant.ignore-urls`。
4. 设计器内数据源、数据集等管理操作按 `getPermissions` 返回的 drag 权限指令鉴权（见 2.5）。

### 1.2 积木仪表盘端点组 /drag/** 与 /jimubi/**

- **路径**: `/drag/**`（设计器数据接口）、`/jimubi/**`（设计器前端资源）
- **权限**: 已认证（同 1.1：Spring Security `permitAll` + 回调认证；drag 权限指令见 2.5）
- **说明**: JimuBI 大屏/仪表盘设计器能力，对应管理后台菜单「报表管理 → 仪表盘设计器」。

**请求参数**: 无（同 1.1，端点由 starter 内部定义）

**响应**: 无 CommonResult 包装

**业务逻辑**:
1. 请求进入后由 starter 回调 `JmReportTokenServiceImpl` 完成 Token 校验与登录用户注入。
2. 字典、分类树、用户/部门字典等扩展数据通过 `IOnlDragExternalService` 回调获取（见 3.1，当前为占位实现）。
3. 设计器操作日志通过 `addLog` 回调记录（见 3.1，当前为空实现）。
4. 超管用户获得全部 9 个 drag 权限指令（数据源/数据集/回收站等管理操作），普通用户由积木自身权限体系控制。

## 2. 认证桥接回调（JmReportTokenServiceImpl）

实现类 `cn.iocoder.yudao.module.report.framework.jmreport.core.service.JmReportTokenServiceImpl`，实现积木接口 `org.jeecg.modules.jmreport.api.JmReportTokenServiceI`，由 `JmReportConfiguration` 注册为 Bean（依赖 `OAuth2TokenCommonApi`、`PermissionCommonApi`、`SecurityProperties`）。积木前端 Token 头为 `X-Access-Token`，yudao 侧 Token 头由 `securityProperties.getTokenHeader()` 决定（默认 `Authorization`）。

### 2.1 Token 校验回调 verifyToken

- **路径**: 回调方法，无 HTTP 路径（starter 在请求处理链中调用）
- **权限**: 已认证（本回调即认证入口）
- **说明**: 校验积木前端传递的 Token 是否有效，即认证是否通过。

**请求参数（方法入参）**:

| 参数 | 类型 | 说明 |
|-----|------|------|
| token | String | 积木前端传递的 `X-Access-Token` |

**响应**: `Boolean`（true 表示认证通过）

**业务逻辑**:
1. 先读取 Spring Security 上下文中的当前登录用户（`SecurityFrameworkUtils.getLoginUserId`），非空直接返回 true（yudao TokenAuthenticationFilter 已完成认证）。
2. 否则调用私有方法 `buildLoginUserByToken(token)`：token 为空返回 null。
3. 置 `TenantContextHolder.setIgnore(true)` 忽略租户，调用 `OAuth2TokenCommonApi#checkAccessToken(token)` 校验 accessToken（参考 TokenAuthenticationFilter 的认证逻辑）。
4. 校验通过则构建 `LoginUser`（userId、userType、tenantId、scopes），并通过 `SecurityFrameworkUtils.setLoginUser` 写入请求上下文。
5. 恢复租户上下文：`setIgnore(false)` 并 `setTenantId(user.getTenantId())`（参考 TenantContextWebFilter 的逻辑，避免后续数据库查询因缺租户报错）。
6. 校验过程抛出 `ServiceException` 则忽略（认证失败），最终返回 false。

### 2.2 用户编号回调 getUsername

- **路径**: 回调方法，无 HTTP 路径
- **权限**: 已认证
- **说明**: 返回 Token 对应的用户编号（方法名为 username，实际对应 yudao 用户编号）。

**请求参数（方法入参）**:

| 参数 | 类型 | 说明 |
|-----|------|------|
| token | String | 积木前端传递的 Token |

**响应**: `String`（用户编号字符串，认证失败返回 null）

**业务逻辑**:
1. 优先从 Spring Security 上下文取 `getLoginUserId`，非空直接返回其字符串形式。
2. 否则调用 `buildLoginUserByToken(token)` 完成 Token 校验并构建 LoginUser。
3. 返回 `LoginUser.getId()` 的字符串形式；校验失败返回 null。

### 2.3 角色映射回调 getRoles

- **路径**: 回调方法，无 HTTP 路径
- **权限**: 已认证
- **说明**: 将 yudao 角色映射为积木报表角色（超管映射为积木 admin，适配 prodSafe 安全模式）。

**请求参数（方法入参）**:

| 参数 | 类型 | 说明 |
|-----|------|------|
| token | String | 积木前端传递的 Token |

**响应**: `String[]`（积木角色编码数组，无匹配返回 null）

**业务逻辑**:
1. 从 Spring Security 上下文取 `LoginUser`，为 null 返回 null（`/jmreport/**` 纯前端地址不走 `buildLoginUserByToken` 逻辑）。
2. 设置租户上下文 `TenantContextHolder.setTenantId(loginUser.getTenantId())`。
3. 调用 `PermissionApi#hasAnyRoles(userId, RoleCodeEnum.SUPER_ADMIN.getCode())` 判断是否超管；是则返回 `{"admin"}`（映射为积木报表管理员），否则返回 null。

### 2.4 租户编号回调 getTenantId

- **路径**: 回调方法，无 HTTP 路径
- **权限**: 已认证
- **说明**: 向积木提供当前登录用户的租户编号（积木前端请求不携带 tenant-id Header，无法直接取 TenantContext）。

**请求参数**: 无

**响应**: `String`（租户编号字符串，未登录返回 null）

**业务逻辑**:
1. 从 Spring Security 上下文取 `LoginUser`，为 null 返回 null。
2. 返回 `loginUser.getTenantId()` 的字符串形式（`StrUtil.toStringOrNull`）。

### 2.5 权限指令回调 getPermissions

- **路径**: 回调方法，无 HTTP 路径
- **权限**: 已认证
- **说明**: 将 yudao 超管映射为积木仪表盘（drag）的全部管理权限指令（适配 prodSafe 安全模式，不处理会导致设计器管理操作被拒）。

**请求参数（方法入参）**:

| 参数 | 类型 | 说明 |
|-----|------|------|
| token | String | 积木前端传递的 Token |

**响应**: `String[]`（权限指令数组，非超管返回 null）

**业务逻辑**:
1. 从 Spring Security 上下文取 `LoginUser`，为 null 返回 null；同时设置租户上下文。
2. 若当前用户具有 `super_admin` 角色（`PermissionApi#hasAnyRoles`），返回全部 9 个 drag 权限指令：`drag:datasource:testConnection`（数据库连接测试）、`drag:datasource:saveOrUpate`（数据源保存）、`drag:datasource:delete`（数据源删除）、`drag:analysis:sql`（SQL 解析）、`drag:design:getTotalData`（展示 Online 表单数据）、`drag:dataset:save`（数据集保存）、`drag:dataset:delete`（数据集删除）、`onl:drag:clear:recovery`（清空回收站）、`onl:drag:page:delete`（数据删除）。
3. 非超管返回 null，由积木自身权限体系控制。

### 2.6 API 数据集请求头转换 customApiHeader

- **路径**: 回调方法，无 HTTP 路径（积木 API 数据集调用后端接口时触发）
- **权限**: 已认证
- **说明**: 为积木「API 数据集」自定义请求头，把积木系统的 Token 换成 yudao 系统的 Token，解决跨系统 Token 传递。

**请求参数**: 无

**响应**: `org.springframework.http.HttpHeaders`（附加了 yudao 认证头的请求头）

**业务逻辑**:
1. 从当前 `HttpServletRequest` 读取积木系统 Token 头 `X-Access-Token`。
2. 将其转换为 yudao 认证头 `{tokenHeader}: Bearer {token}`（头名取 `SecurityProperties.getTokenHeader()`，格式复用 `SecurityFrameworkUtils.AUTHORIZATION_BEARER`）。
3. 返回 `HttpHeaders`，积木 API 数据集据此向后端接口透传 Token 完成认证。

## 3. 仪表盘外部扩展服务（JmOnlDragExternalServiceImpl）

实现类 `cn.iocoder.yudao.module.report.framework.jmreport.core.service.JmOnlDragExternalServiceImpl`，实现积木仪表盘接口 `org.jeecg.modules.drag.service.IOnlDragExternalService`，由 `JmReportConfiguration` 注册为 Bean（`@Primary`，源码注释标注"暂时注释：可以按需实现后打开"）。

### 3.1 字典与日志扩展回调（占位实现）

- **路径**: 回调方法，无 HTTP 路径
- **权限**: 已认证
- **说明**: 为积木仪表盘设计器提供字典与操作日志的外部数据源扩展点，当前全部为接口默认空实现，按需扩展。

**请求参数（方法入参汇总）**:

| 方法 | 参数 | 说明 |
|-----|------|------|
| getDictItems | dictCode: String | 数据字典项查询 |
| getTableDictItems | dictTable / dictText / dictCode: String | 表字典项查询 |
| getCategoryTreeDictItems | ids: List&lt;String&gt; | 分类树字典项查询 |
| getUserDictItems | ids: List&lt;String&gt; | 用户字典项查询 |
| getDeptsDictItems | ids: List&lt;String&gt; | 部门字典项查询 |
| addLog | dto: DragLogDTO | 操作日志记录（DTO 形式） |
| addLog | logMsg: String, logType: int, operateType: int | 操作日志记录（散参形式） |

**响应**: `List<DragDictModel>`（字典类方法）／void（日志方法）

**业务逻辑**:
1. 全部 7 个方法直接调用 `IOnlDragExternalService` 接口的 default 实现（`super` 调用），即占位空逻辑。
2. 字典类方法尚未对接 yudao 字典体系（`system_dict`），日志类方法尚未对接 yudao 操作日志。
3. 官方参考实现为 jimureport-example 的 `JimuDragExternalServiceImpl` 与 JeecgBoot 的 `JimuDragExternalServiceImpl`，可按需补充真实逻辑。

## 4. 配置类（非端点，集成入口）

### 4.1 JmReportConfiguration

`@Configuration` 类，位于 `framework/jmreport/config/`。

**业务逻辑**:
1. `@ComponentScan(basePackages = "org.jeecg.modules.jmreport")` 扫描积木报表包，注册 starter 内全部 Controller / Service Bean（即第 1 节端点的来源）。
2. 注册 `JmReportTokenServiceI` Bean → `JmReportTokenServiceImpl`，注入 `OAuth2TokenCommonApi`、`PermissionCommonApi`、`SecurityProperties`。
3. 注册 `JmOnlDragExternalServiceImpl` Bean（`@Primary`，按需启用）。

### 4.2 SecurityConfiguration（reportAuthorizeRequestsCustomizer）

Report 模块安全配置，位于 `framework/security/config/`。

**业务逻辑**:
1. 对 `/jmreport/**`（积木报表）、`/drag/**` 与 `/jimubi/**`（积木仪表盘）在 Spring Security 层 `permitAll`。
2. 认证职责由 `JmReportTokenServiceImpl` 的回调承担（见第 2 节），形成"放行 + 内部回调认证"的组合。

## 错误码说明

本域无自定义错误码。report 模块错误码段 `1-003-000-000` 仅定义 `GO_VIEW_PROJECT_NOT_EXISTS`（GoView 域，见 api-goview-project.md），积木报表集成域未定义错误码；Token 校验失败复用 yudao OAuth2 体系抛出的 `ServiceException`（如 accessToken 无效/过期），由 `GlobalExceptionHandler`（`@Order(0)`，优先于积木默认异常处理器）统一处理。
