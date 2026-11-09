# UReport2 中国式报表集成接口 (UReport2FileController / UReportServlet)

> report 模块的第二套第三方报表能力：基于 UReport2（ureport2-spring-boot-starter 2.0.1，cn.iocoder 的 JDK8 适配分支）实现中国式报表的设计、预览、打印与 Excel/PDF/Word 导出。模板以 XML 存于 `report_ureport_file` 表并按租户隔离；UReport2 通过自定义 `ReportProvider`（前缀 `db:`）从数据库读写模板，取代其默认文件存储。管理后台仅提供模板列表与删除接口，模板的新建、设计、保存、预览、导出全部由 UReport2 自带页面完成。

## 接口路径前缀

- `/report/ureport2/file/**`：本模块自研的管理后台接口（`UReport2FileController`）
- `/ureport/**`：UReport2 设计器/预览/导出端点组（由 `ureport2-spring-boot-starter` 的 `UReportServlet` 按 Action 分发，代码不在本仓库）

> 前置入口（system_menu）：`PermissionConstants` 的注释约定在 `207 报表管理` 下挂「UReport2 报表」菜单（权限 `report:ureport:query`），其下挂「报表设计」按钮（权限 `report:ureport:design`）。注意：本仓库 `sql/` 目录尚未包含该菜单/按钮的 INSERT，也未包含 `report_ureport_file` 建表语句，启用前必须自行补齐（见 [pitfalls.md](pitfalls.md) 第 6 节）。

## 1. 管理后台接口（UReport2FileController）

### 1.1 获得 UReport2 报表模板分页

- **路径**: GET /report/ureport2/file/page
- **权限**: report:ureport:query 或 report:ureport:design（`@ss.hasAnyPermissions('report:ureport:query', 'report:ureport:design')`）
- **说明**: 分页查询当前租户的报表模板列表；为避免传输大字段，查询不包含模板内容 `content`

**请求参数 (UReport2FilePageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| name | String | 否 | 无 | 模板名称，模糊匹配（likeIfPresent） |
| pageNo | Integer | 是 | PageParam 默认校验 | 页码，从 1 开始 |
| pageSize | Integer | 是 | PageParam 默认校验 | 每页条数 |

**响应**: CommonResult&lt;PageResult&lt;UReport2FileRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| name | String | 模板名称，不包含存储前缀，如 demo.ureport.xml |
| createTime | LocalDateTime | 创建时间 |
| updateTime | LocalDateTime | 更新时间 |

**业务逻辑**:
1. 调用 `UReport2FileServiceImpl#getFilePage`，委托 `UReport2FileMapper#selectPage`
2. 按 `name` 模糊匹配（`likeIfPresent`），按 `id` 倒序
3. 查询只 select `id`、`name`、`create_time`、`update_time`，不加载 `content`
4. 租户条件由多租户插件自动追加，只返回当前租户未删除的模板

### 1.2 删除 UReport2 报表模板

- **路径**: DELETE /report/ureport2/file/delete
- **权限**: report:ureport:design
- **说明**: 按编号逻辑删除模板；删除后发布新的模板版本号使各实例缓存失效，并移除本实例的模板缓存

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @RequestParam("id") | 模板编号 |

**响应**: CommonResult&lt;Boolean&gt;（删除成功返回 true）

**业务逻辑**:
1. 按编号查询模板，不存在抛出错误码 `UREPORT2_FILE_NOT_EXISTS`（1_003_001_000）
2. `deleteById` 逻辑删除（`deleted` 标记），删除后允许重新创建同名模板
3. 先落库（无外层事务、自动提交），再调用 `UReport2FileVersionRedisDAO#refresh` 发布新的随机版本号，使各实例的本地缓存失效
4. `finally` 中移除本实例的模板缓存（`UReport2ReportDefinitionCache#onFileDeleted`），即使发布版本号失败，也不再保留已删除模板的缓存

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_003_001_000 | UReport2 报表模板不存在 |

## 2. UReport2 设计器 / 预览 / 导出端点组（/ureport/**）

### 2.1 端点组说明

- **路径**: `/ureport/**`
- **分发**: `/ureport/**` 不是 Spring MVC Controller，而是由 `UReportServlet` 按「Action + 方法」反射分发（如 `/ureport/designer/saveReportFile`、`/ureport/preview/loadData`）
- **权限**: 必须已登录且为管理后台用户（`UserTypeEnum.ADMIN`）；设计权限可访问全部请求，查看权限仅可访问白名单 Action 且仅限已保存报表
- **说明**: 设计器、数据源管理、导入、未保存报表预览等需设计权限；预览、分页、打印与 Excel/PDF/Word 导出需查看权限。静态资源免登录。

**请求参数**: 无统一 ReqVO，由 UReport2 各 Action 自行定义；本模块关注的关键参数：

| 参数 | 说明 |
|-----|------|
| `_u` | 报表文件参数；已保存的数据库模板以 `db:` 开头，如 `db:demo.ureport.xml` |
| `tenantId` | 前端 iframe 地址透传的租户编号 URL 参数，仅用于与登录用户租户比对 |

**响应**: 无 CommonResult 包装（UReportServlet 自行定义响应格式）；安全校验失败时由过滤器返回 CommonResult JSON（如 401/403）。

### 2.2 权限分级矩阵

| 权限 | 可访问范围 | `_u` 约束 |
|-----|-----------|----------|
| report:ureport:design | 全部 `/ureport/**`（设计器、数据源、导入、预览、导出等） | 无（可访问设计中的未保存报表 `_u=p`） |
| report:ureport:query | 仅 `QUERY_ACTIONS` 白名单内的 Action | 必须以 `db:` 开头（仅已保存的数据库模板） |
| 无上述权限 | 一律 403 | — |

查看权限白名单 `QUERY_ACTIONS`（`UReport2SecurityFilter` 中定义，共 15 个）：

| 分类 | Action |
|-----|--------|
| 预览、分页、打印 | /preview、/preview/loadData、/preview/loadPrintPages、/preview/loadPagePaper |
| 导出 Excel | /excel、/excel/paging、/excel/sheet、/excel97、/excel97/paging、/excel97/sheet |
| 导出 PDF、PDF 在线打印 | /pdf、/pdf/show、/pdf/newPaging |
| 导出 Word | /word |
| 导出时回传预览页图表图片 | /chart/storeData |

> Action 解析规则：使用未解码的 `requestURI` 去掉 `contextPath + /ureport` 前缀，第一段为 Action 路径、剩余部分 trim 后为方法名；方法名为空时取 Action 路径。编码、大小写、路径参数、多余斜杠等变体不会与白名单精确匹配，需要设计权限。UReport2 升级新增 Action 时，若忘记同步 `QUERY_ACTIONS`，只持查看权限的用户会直接 403。

### 2.3 静态资源

- **路径**: GET `/ureport/res/ureport-asserts/**`（`UReportServlet.URL + "/res/ureport-asserts/"`）
- **权限**: 无（Spring Security 层 `permitAll`，`UReport2SecurityFilter#shouldNotFilter` 同样跳过）
- **说明**: 设计器与预览页的静态资源，免登录访问。若部署时 contextPath 或 starter 版本导致路径前缀变化，未登录用户会因静态资源被拦而出现页面空白。

## 3. 安全校验流程（UReport2SecurityFilter）

`UReport2SecurityFilter` 为 `OncePerRequestFilter`，由 `UReport2Configuration` 注册，URL 模式 `/ureport/*`，过滤器顺序为 `WebFilterOrderEnum.TENANT_SECURITY_FILTER`（在 Spring Security 之后，保证 token 认证已完成）。处理流程：

1. **登录与用户类型校验**：`SecurityFrameworkUtils.getLoginUser()` 为空返回 401（UNAUTHORIZED）；`userType` 非 `ADMIN` 返回 403。
2. **租户上下文注入与越权比对**：以 `LoginUser.getTenantId()` 为准设置 `TenantContextHolder`；若请求携带 `tenant-id` Header 或 `tenantId` 参数，必须与登录用户租户一致，否则返回 403「您无权访问该租户的数据」。随后调用 `TenantFrameworkService#validTenant` 校验租户合法（禁用、到期等）。
3. **权限分级校验**：`hasPermission(design) || (isQueryRequest && hasPermission(query))`；权限校验自身异常时写入异常响应且不放行。
4. **稳定 Session 编号**：用 `UReport2SessionRequestWrapper` 包装请求后继续过滤链（见 3.2）。
5. **清理**：`finally` 中调用 `UReport2ReportDefinitionCache#clearPendingVersions()` 清理当前线程的待写入版本号，并恢复原租户上下文。

> `/ureport/**` 不经过 `TenantSecurityWebFilter`（后者只拦截 `/admin-api`、`/app-api` 前缀），租户上下文完全由本过滤器依据 `LoginUser` 注入；越权校验依赖本过滤器而非框架。

### 3.1 异常日志脱敏

异常交由 `GlobalExceptionHandler#allExceptionHandler` 处理时，传入 `UReport2ErrorLogRequestWrapper` 包装请求：不对外提供请求参数、query string、请求体与上传文件，URI、方法、请求头、请求属性仍可读。目的是避免 UReport2 请求中的 token、`tenantId`、模板内容（可能包含数据源账号密码）写入日志。二次开发若自行打印 request 参数或模板内容，会造成凭据泄漏。

### 3.2 Session 编号稳定化

Spring Security 的 `SessionManagementFilter` 在每次 token 认证后调用 `changeSessionId()` 防护会话固定，导致物理 Session 编号每个请求都变化，UReport2 的未保存预览（`TempObjectCache`）与图表数据（`HttpSessionReportCache`）以 `getSession().getId()` 为 key 的缓存会跨请求丢失。`UReport2SessionRequestWrapper` 将返回 Session 的 `getId()` 替换为保存在真实 Session 属性中的随机编号：

- 编号基于「用户类型:用户编号:租户编号」身份生成，物理 Session 编号轮换后保持不变；
- 同一 Session 内登录用户或租户变化时重新生成编号，不会读取到其它身份的缓存；
- 通过 `WebUtils.getSessionMutex` 加锁，保证并发请求拿到同一编号。

## 4. 存储与缓存机制

### 4.1 数据库存储（UReport2DatabaseReportProvider）

自定义 `ReportProvider` 实现（前缀常量 `PREFIX = "db:"`，Provider 名称「数据库」，`disabled()` 返回 false），将 UReport2 的模板读写落到 `report_ureport_file` 表：

| 方法 | 行为 |
|-----|------|
| loadReport | 按 `removePrefix(file)` 查询模板，不存在抛 `UREPORT2_FILE_NOT_EXISTS`；返回 `content` 的 UTF-8 字节流 |
| saveReport | 调用 `saveFile` 保存（不存在创建、存在更新），随后 `onFileSaved` 记录本次发布的版本号 |
| deleteReport | 调用 `deleteFileByName` 删除并发布新版本号 |
| getReportFiles | 查询模板列表（不含 content），转换为 `ReportFile`（名称 + 更新时间） |

> 设计器加载存储列表时会把 Provider 序列化为 JSON，因此该类不得增加其它 getter 方法。模板名称规范化由 Service 与缓存各自完成，Provider 直接传递 UReport2 给出的原始名称。

### 4.2 多实例缓存一致性（UReport2ReportDefinitionCache + UReport2FileVersionRedisDAO）

- **本地缓存**：`UReport2ReportDefinitionCache` 在 JVM 内缓存解析后的 `ReportDefinition`，key 为「租户编号:规范化模板名」（`buildKey = tenantId + ":" + file`），避免不同租户同名模板互相覆盖。
- **Redis 版本号**：Redis 只保存每个模板的随机版本号（`UREPORT2_FILE_VERSION = "report:ureport2_file_version:%d:%s"`，参数为 tenantId 与含 `db:` 前缀的模板名），不保存模板定义对象图；Key 不设置过期时间，避免过期后被误判为「未修改」。
- **读取**：先读 Redis 版本号，再读本地缓存；版本号一致则命中，否则返回 null，由 UReport2 重新从数据库加载、解析。未命中时记录「加载数据库之前」读取到的版本号，写入缓存时使用（保证缓存中的模板定义至少与记录的版本号一样新）。
- **保存/删除**：先落库（无外层事务、自动提交），再刷新版本号；设计器保存后由 Provider 调用 `onFileSaved` 使用本次发布的版本号，避免重新读取 Redis 造成竞态。

> 数据库与 Redis 不在同一事务：若数据库已提交、发布版本号失败（如 Redis 不可用），会抛异常，各实例可能继续使用旧模板缓存，直到下一次保存/删除成功或实例重启。

### 4.3 模板名称规范化（UReport2FileNameUtils）

`report_ureport_file.name` 使用 MySQL `utf8mb4_bin` 排序规则（区分大小写，但属 PAD SPACE：尾部 ASCII 空格会被忽略）。为避免同一条记录的不同写法对应不同缓存/Redis key，所有以名称为身份的地方（数据库读写、本地缓存、Redis 版本号）都先经 `UReport2FileNameUtils#normalize`：只去掉尾部 ASCII 空格，不转换大小写、不去掉开头空格和其它空白字符。逻辑删除后允许重建同名模板。

## 5. 配置类与开关（UReport2Configuration）

`@Configuration(proxyBeanMethods = false)` + `@ConditionalOnProperty(prefix = "ureport", name = "enabled", havingValue = "true", matchIfMissing = true)`：

| Bean | 作用 |
|-----|------|
| ureport2ReportDefinitionCache | 注册模板缓存（依赖 `UReport2FileVersionRedisDAO`） |
| ureport2DatabaseReportProvider | 注册数据库 ReportProvider（依赖 `UReport2FileService`、模板缓存） |
| ureport2SecurityFilter | 注册安全过滤器，URL 模式 `/ureport/*`，顺序 `TENANT_SECURITY_FILTER` |

- `ureport.enabled` 默认开启（`matchIfMissing=true`）；关闭后不注册上述三个 Bean。
- `UReport2FileServiceImpl` 对 `reportDefinitionCache` 使用 `@Autowired(required = false)`，关闭 UReport2 时仍可保存与删除模板，但不会清理本实例缓存。

## 6. 安全配置放行（SecurityConfiguration）

report 模块的 `SecurityConfiguration#authorizeRequestsCustomizer` 在 Spring Security 层新增一条放行规则，既有积木报表规则保持不变：

| 路径 | 方法 | 规则 |
|-----|------|------|
| /jmreport/** | 任意 | permitAll |
| /drag/** | 任意 | permitAll |
| /jimubi/** | 任意 | permitAll |
| /ureport/res/ureport-asserts/** | GET | permitAll（UReport2 静态资源） |

> 其它 `/ureport/**` 请求需要登录，并由 `UReport2SecurityFilter` 校验租户与权限。

## 7. 权限标识

权限标识集中定义于 `PermissionConstants`（与菜单配置保持一致；接口上的 `@PreAuthorize` 仍直接书写标识）：

| 常量 | 权限标识 | 说明 |
|-----|---------|------|
| UREPORT2_QUERY | report:ureport:query | 查看：查看报表列表，预览、打印、导出已保存的报表（对应「UReport2 报表」菜单） |
| UREPORT2_DESIGN | report:ureport:design | 设计：新建、设计、保存、删除报表，配置数据源；包含查看权限的全部功能（对应「报表设计」按钮） |

## 8. 错误码

UReport2 使用 report 模块新增的 `1_003_001_000` 段（GoView 的 `1_003_000_000` 段保持不变）：

| 错误码 | 消息 | 常量名 |
|-------|------|--------|
| 1_003_001_000 | UReport2 报表模板不存在 | UREPORT2_FILE_NOT_EXISTS |

## 9. 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/controller/admin/ureport2/UReport2FileController.java | 管理后台模板列表/删除接口 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/service/ureport2/UReport2FileServiceImpl.java | 模板保存/删除、版本号发布、缓存刷新 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/dataobject/ureport2/UReport2FileDO.java | 模板实体（TenantBaseDO） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/mysql/ureport2/UReport2FileMapper.java | 模板 Mapper（selectByName/selectPage 均不含 content） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/dal/redis/ureport2/UReport2FileVersionRedisDAO.java | 模板版本号 Redis DAO |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/config/UReport2Configuration.java | UReport2 配置类与开关 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/provider/UReport2DatabaseReportProvider.java | 数据库 ReportProvider（db: 前缀） |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/cache/UReport2ReportDefinitionCache.java | 多实例模板缓存 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/web/UReport2SecurityFilter.java | /ureport/** 登录、租户、权限分级校验 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/web/UReport2SessionRequestWrapper.java | 稳定 Session 编号包装 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/web/UReport2ErrorLogRequestWrapper.java | 异常日志脱敏包装 |
| yudao-module-report/src/main/java/cn/iocoder/yudao/module/report/framework/ureport2/core/util/UReport2FileNameUtils.java | 模板名称规范化 |
