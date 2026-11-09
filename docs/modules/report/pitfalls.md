# 注意事项与已知坑点

> 使用 report 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 GoViewProjectDO 会被租户插件自动追加 tenant_id 条件

**问题**: 启用多租户（`yudao.tenant.enable=true`，yudao-server 默认开启）后，对 `report_go_view_project` 的所有查询/写入会被自动拼接 `tenant_id`；若物理表没有 `tenant_id` 列，`/admin-api/report/go-view/project/**` 的所有 SQL 直接报 `Unknown column 'tenant_id'`。

**原因**: `TenantDatabaseInterceptor#computeIgnoreTable` 的判定规则是：`TableInfo` 不存在（非本系统实体）或 DO 标注了 `@TenantIgnore` 才忽略租户。`GoViewProjectDO` 只继承了 `BaseDO`，既不是 `TenantBaseDO` 也没有 `@TenantIgnore` 注解，因此被判定为"不忽略"，租户插件（MyBatis-Plus `TenantLineInnerInterceptor`）会为它追加租户条件，INSERT 时还会自动补 `tenant_id` 列值。

**解决**: 建表 SQL 必须包含 `tenant_id bigint` 列（注意：本仓库 `sql/mysql/ruoyi-vue-pro.sql` 中没有该表的建表语句，只有菜单 INSERT，切勿仅按 DO 字段自建表）。若业务上确认该表不做租户隔离（按 creator 隔离即可），必须给 `GoViewProjectDO` 加 `@TenantIgnore` 注解，或将表名加入 `yudao.tenant.ignore-tables` 配置，两者选一。

### 1.2 认证失败路径泄漏 TenantIgnore 标志

**问题**: 携带无效 token 访问积木报表时，同一请求线程后续的数据库查询会跳过租户过滤，存在跨租户数据风险。

**原因**: `JmReportTokenServiceImpl#buildLoginUserByToken` 先执行 `TenantContextHolder.setIgnore(true)` 再调 `oauth2TokenApi.checkAccessToken(token)`，但三条失败路径——token 为空、`checkAccessToken` 返回 null、抛 `ServiceException`——都提前 `return null`，没有恢复 `setIgnore(false)`（只有认证成功的第 129 行才恢复）。且 `IGNORE` 是 `TransmittableThreadLocal`，会随 TTL 传播到 jmreport 异步导出等子线程。

**解决**: 二次开发时建议把标志恢复放进 `finally`：

```java
TenantContextHolder.setIgnore(true);
try {
    OAuth2AccessTokenCheckRespDTO accessToken = oauth2TokenApi.checkAccessToken(token);
    // ...
} finally {
    TenantContextHolder.setIgnore(false);
}
```

正常请求结束时由 `TenantContextWebFilter#doFilterInternal` 的 `finally TenantContextHolder.clear()` 兜底清理，但请求处理期间的窗口仍然存在。

### 1.3 积木报表链路的租户上下文全靠手工维护

**问题**: `/jmreport/**` 前端请求不携带 `tenant-id` Header，涉及租户表的 SQL 可能报 `TenantContextHolder 不存在租户编号`（`TenantContextHolder#getRequiredTenantId` 抛出的 NullPointerException）。

**原因**: `TenantSecurityWebFilter` 继承 `ApiRequestFilter`，只拦截 `/admin-api`、`/app-api` 前缀的请求，`/jmreport/**`、`/drag/**`、`/jimubi/**` 完全不走租户校验；`TenantContextWebFilter` 只从 Header 解析租户。唯一的租户来源是 `JmReportTokenServiceImpl` 在 `buildLoginUserByToken`、`getRoles`、`getPermissions` 三处手动执行 `TenantContextHolder.setTenantId(loginUser.getTenantId())`——未登录或未走到这三个方法的请求，租户上下文为空。

**解决**: 在积木报表里配置直连 yudao 业务表的数据集时，必须保证请求带有效 token（走 `verifyToken` → `buildLoginUserByToken` 的成功路径完成上下文注入）；公开分享/匿名场景不要依赖框架自动追加租户条件，应在数据集 SQL 中显式限定租户字段，或改写专用查询接口。

## 2. 安全与权限相关

### 2.1 /get-by-sql 可执行任意 SQL

**问题**: 拥有 `report:go-view-data:get-by-sql` 权限的用户可以通过请求体直接执行任意 SQL，等于开放主库的任意查询能力。

**原因**: `GoViewDataController#getDataBySQL` 把请求体 `GoViewDataGetBySqlReqVO` 的 `sql` 字符串原样交给 `GoViewDataServiceImpl#getDataBySQL` 的 `jdbcTemplate.queryForRowSet(sql)` 执行，没有白名单、没有只读校验（仅有 `@NotEmpty` 非空校验）。另外该端点用的是 `@RequestMapping("/get-by-sql")`，未限定 HTTP 方法，GET/POST/PUT/DELETE 均可命中。

**解决**: 该权限（菜单 id 345"使用 SQL 查询数据"）只能授予可信的报表管理员角色。二次开发可加固：仅允许 SELECT 语句、拆解并校验表白名单、或改为前端传数据集 ID 而非 SQL 原文。注意项目 CSRF 已全局禁用（`YudaoWebSecurityConfigurerAdapter` 中 `csrf(AbstractHttpConfigurer::disable)`），切勿将该端点暴露到公网。

### 2.2 GoView 项目查询/更新/删除不校验归属，存在水平越权

**问题**: 知道项目 id 的用户可以查看、修改、删除他人创建的大屏项目。

**原因**: `GoViewProjectServiceImpl#getProject`、`updateProject`、`deleteProject` 都只调用 `validateProjectExists(id)` 校验存在性，不比对 `creator`；只有 `getMyProjectPage` 通过 `GoViewProjectMapper#selectPage` 的 `eq(GoViewProjectDO::getCreator, userId)` 实现了"我的项目"过滤。

**解决**: 二次开发时在 Service 层补归属校验：

```java
GoViewProjectDO project = goViewProjectMapper.selectById(id);
if (project == null || !Objects.equals(project.getCreator(), String.valueOf(getLoginUserId()))) {
    throw exception(GO_VIEW_PROJECT_NOT_EXISTS);
}
```

`creator` 由 `DefaultDBFieldHandler#insertFill` 自动填充为 `userId.toString()`，比较时注意类型是 String。

### 2.3 积木报表端点 permitAll 且版本锁死，生产必须网络隔离

**问题**: `/jmreport/**`、`/drag/**`、`/jimubi/**` 全部 permitAll，未登录请求也能到达积木报表的服务端点，认证完全依赖积木 starter 内部回调；而 jimureport 版本被锁定，无法通过升级获得安全修复。

**原因**: report 模块 `SecurityConfiguration#customize` 对三个路径前缀 `permitAll()`，认证委托给 `JmReportTokenServiceImpl#verifyToken`（由积木 starter 在自己的过滤器里调用）；`yudao-dependencies/pom.xml` 将 `jimureport.version` 锁定在 2.3.4。

**解决**: 生产环境通过网关/Nginx 限制 `/jmreport/**`、`/drag/**`、`/jimubi/**` 的来源 IP，或仅内网开放；不要把积木报表的匿名分享链接直接暴露公网；关注 jeecg 官方安全通告，升级前先解决 JimuBI 版本配套问题（见 3.1）。

## 3. 依赖与版本相关

### 3.1 jimureport 锁定 2.3.4，擅自升级会导致启动失败

**问题**: 直接把 `jimureport-spring-boot-starter` 升到 2.5.x 后项目启动失败。

**原因**: `yudao-dependencies/pom.xml` 中 `<jimureport.version>2.3.4</jimureport.version>` 的注释明确说明：JimuBI 2.3.2 依赖该版本中的 `JimuAiConfigBean`，升级到 2.5.4 会导致启动失败。同时依赖管理里还做了多处 exclusion——jimureport 排除 `swagger-annotations-jakarta`、`fastjson`，jimubi 排除 `jsqlparser`、`hutool-core`、`fastjson`，这些包都由 yudao 统一管理版本。

**解决**: 保持 `jimureport 2.3.4 + jimubi 2.3.2` 的版本组合不变；确需升级时必须同步升级 jimubi 并验证启动与核心功能，且不要删除任何 exclusion。

### 3.2 模块默认未启用，启用需改两处 pom 并保留 AI 冲突配置

**问题**: 打开 report 模块时，要么编译不进来（根聚合没加），要么与 ai 模块同时启用时报 ChatClient 相关的启动错误。

**原因**: 根 `pom.xml` 的 `<module>yudao-module-report</module>` 与 `yudao-server/pom.xml` 的依赖声明默认都被注释；`application.yaml` 中 `spring.ai.chat.client.enabled=false` 的注释说明：`ChatClient.Builder` 自动配置要求唯一的 ChatModel Bean，而项目会创建多个，ai + report 模块同时引入时会启动报错。

**解决**: 同时打开根 pom 的 `<module>` 与 yudao-server pom 的 `<dependency>` 两处注释；保持 `spring.ai.chat.client.enabled=false` 不要恢复；首次启用还需按上游/官方 SQL 建 `report_go_view_project` 表（含 `tenant_id`，见 1.1）以及积木报表自带的 `jimu_*`、`onl_drag_*` 表（由 starter 官方 SQL 维护，不在本仓库）。集成 UReport2 后还额外需要 `report_ureport_file` 表与 Redis（见第 6 节）。

## 4. 功能限制相关

### 4.1 /get-by-http 是随机数示例接口

**问题**: 前端大屏接 `/admin-api/report/go-view/data/get-by-http` 拿到的 PV/UV 是随机数，正式环境图表数据不对。

**原因**: `GoViewDataController#getDataByHttp` 用 `RandomUtil.randomInt(1000, 10000)` 造数，接口 `@Operation` 描述也写明"这个只是示例接口，实际应该每个查询，都要写一个接口"。

**解决**: 参照该 Controller 的写法为每个图表新建真实查询接口，注意补上 `@PreAuthorize` 权限并显式限定 `@GetMapping`/`@PostMapping`，不要沿用示例接口。

### 4.2 getDataBySQL 只查主数据源且全量加载结果集

**问题**: 大数据量查询响应慢甚至 OOM；也无法直接查询项目库以外的数据源。

**原因**: `GoViewDataServiceImpl` 注入的是默认 `JdbcTemplate`（主数据源），`getDataBySQL` 用 `queryForRowSet` 后通过 `while (sqlRowSet.next())` 把所有行装进 `LinkedList` 一次性返回；类注释也说明"可能数据量比较大的情况下，会比较慢，可以考虑后续使用 Click House 等等"。

**解决**: 大数据集在 SQL 层做聚合/分页；需要查其它数据源时按类注释的思路，为对应数据源新建 `JdbcTemplate` Bean 再注入使用，不要复用默认实例。

### 4.3 积木仪表盘的字典与日志是空实现

**问题**: 仪表盘（drag）里配置系统数据字典、记录操作日志不生效。

**原因**: `JmOnlDragExternalServiceImpl` 的 `getDictItems`、`getTableDictItems`、`getCategoryTreeDictItems`、`getUserDictItems`、`getDeptsDictItems`、`addLog` 等方法全部直接调用 `IOnlDragExternalService` 接口的 default 方法返回，没有任何对接 yudao 的业务逻辑；`JmReportConfiguration` 中对应 Bean 名为 `jmOnlDragExternalService2`，注释写着"暂时注释：可以按需实现后打开"。

**解决**: 需要字典/日志能力时，实现 `IOnlDragExternalService` 接口，把 yudao 的 `DictDataApi`、日志服务等对接进去，并在 `JmReportConfiguration` 中替换该 Bean。

## 5. 其它

### 5.1 status 字段语义是"发布状态"而非"启用禁用"

**问题**: 按 `CommonStatusEnum` 的常规习惯把 1 当"正常"处理，会导致已发布的大屏被误判为未发布。

**原因**: `GoViewProjectDO#status` 复用 `CommonStatusEnum`，但语义反转为 0=已发布（ENABLE）、1=未发布（DISABLE），DO 注释有明确说明；`GoViewProjectServiceImpl#createProject` 强制 `setStatus(CommonStatusEnum.DISABLE.getStatus())`（新建即未发布），发布动作通过 `updateProject` 修改 status 完成。

**解决**: 判断"已发布"用 `CommonStatusEnum.ENABLE.getStatus()`；入参校验沿用 `GoViewProjectUpdateReqVO#status` 上的 `@InEnum(CommonStatusEnum.class)`，新增 VO 时保持一致。

### 5.2 错误码分两段，ajreport 包是待删除的占位目录

**问题**: 扩展 report 模块时错误提示较少（目前仅 GoView 项目不存在、UReport2 报表模板不存在两个业务错误码）；`ajreport` 相关子包看似可用，实际为空壳。

**原因**: `ErrorCodeConstants` 定义了 `GO_VIEW_PROJECT_NOT_EXISTS(1_003_000_000)`（GoView 域）与 `UREPORT2_FILE_NOT_EXISTS(1_003_001_000)`（UReport2 域）两个错误码；`controller/admin/ajreport`、`service/ajreport`、`convert/ajreport`、`dal/dataobject/ajreport`、`dal/mysql/ajreport` 等 5 个包只有 `package-info.java`（多数注释为"TODO 芋艿：占位，待删除"，`convert/ajreport` 为"TODO 占位，后续删除"，`controller/admin/ajreport` 无注释）；`framework/jmreport/core/web` 包也标注了"占位，后续会基于 Filter 实现积木报表的认证等功能，替代 JmReportTokenServiceImpl"。

**解决**: 新增功能时按子域在对应段内顺延错误码（GoView 用 `1_003_000_xxx`，UReport2 用 `1_003_001_xxx`；注意避开 system 的 1_002 段与 member 的 1_004 段）；不要在 ajreport 占位包里写代码，后续版本会被删除；jmreport 认证若要改造，参考 `framework/jmreport/core/web` 包注释的规划方向。

## 6. UReport2 集成相关

### 6.1 仓库缺 UReport2 建表 SQL 与菜单/权限

**问题**: 按仓库 `sql/` 初始化数据库后启用 UReport2，访问报表时报 `Unknown column 'tenant_id'`，或权限标识无人拥有导致 403。

**原因**: `sql/mysql/ruoyi-vue-pro.sql`（及其它数据库脚本）中没有 `report_ureport_file` 建表语句，也没有 `report:ureport:query`、`report:ureport:design` 的 `system_menu` 记录。仓库内唯一的 DDL 是测试脚本 `yudao-module-report/src/test/resources/sql/create_tables.sql`（含 `tenant_id bigint NOT NULL DEFAULT 0`），不能直接用于生产。

**解决**: 启用前自行补建含 `tenant_id` 的 `report_ureport_file` 表（可参考测试 DDL 与 data-model.md 的字段表），并为「报表管理」下的「UReport2 报表」菜单与「报表设计」按钮补齐 `report:ureport:query` / `report:ureport:design` 权限，再分配给相应角色。

### 6.2 数据库与 Redis 不在同一事务

**问题**: 模板保存/删除成功但发布版本号失败（例如 Redis 不可用）时，各实例可能继续使用旧模板缓存。

**原因**: `UReport2FileServiceImpl#saveFile`/`deleteFile` 没有外层事务（自动提交），先写数据库、再调用 `UReport2FileVersionRedisDAO#refresh` 发布新的随机版本号；二者不是同一事务。发布失败会抛异常，但数据库已提交。Redis 版本号 Key 不设置过期时间，是为避免过期后被误判为「未修改」。

**解决**: 接受最终一致：待 Redis 恢复后，该模板下一次保存/删除成功、或实例重启即恢复；不要在发布版本号失败时回滚已提交的模板数据（会与 UReport2 的保存流程冲突）。监控 Redis 可用性，避免长期不一致。

### 6.3 UReport2FileDO 是显式租户表，与 GoView 表方向相反

**问题**: 按 GoView 表的经验省略 `tenant_id`，或误以为「报告模块的表都没有 tenant_id」。

**原因**: `UReport2FileDO` 继承 `TenantBaseDO`，`report_ureport_file` 必须有 `tenant_id` 列（测试 DDL 为 `bigint NOT NULL DEFAULT 0`），租户插件会自动追加租户过滤。这与 `GoViewProjectDO` 只继承 `BaseDO`、却仍被租户插件追加条件的坑点（见 1.1）方向相反。

**解决**: `report_ureport_file` 建表时必须包含 `tenant_id`；不要给 `UReport2FileDO` 加 `@TenantIgnore`，否则模板将失去租户隔离。

### 6.4 模板名称是 PAD SPACE，必须规范化

**问题**: 通过别名（尾部带空格）删除、保存模板后，原名称的缓存没有失效，预览仍是旧内容。

**原因**: `report_ureport_file.name` 为 `varchar(128)`，MySQL `utf8mb4_bin` 属 PAD SPACE 比较规则，尾部 ASCII 空格会被忽略，`demo.ureport.xml` 与 `demo.ureport.xml ` 是同一条记录。若缓存、Redis 版本号直接使用原始名称，同一条记录的不同写法会对应不同的 key。另外该表除主键外无唯一索引，并发新增同名模板没有数据库兜底。

**解决**: 所有以名称为身份的地方（数据库读写、本地缓存、Redis 版本号）都必须先经 `UReport2FileNameUtils#normalize`；扩展代码不要绕过它直接拼缓存 key。

### 6.5 ureport.enabled 默认开启，引入模块即依赖 Redis 与表

**问题**: 只放开 report 模块，未准备 Redis 或 `report_ureport_file` 表，启动/访问即报错。

**原因**: `UReport2Configuration` 的 `@ConditionalOnProperty(prefix = "ureport", name = "enabled", havingValue = "true", matchIfMissing = true)` 默认开启；模块 `pom.xml` 已依赖 `yudao-spring-boot-starter-redis`。而根 `pom.xml` 的 `<module>yudao-module-report</module>` 与 `yudao-server/pom.xml` 的依赖仍处于注释状态，需手动打开两处。

**解决**: 部署前同时准备 Redis、`report_ureport_file` 表与菜单权限；确实不启用 UReport2 时显式配置 `ureport.enabled=false`，但注意此时 `UReport2FileService` 仍可保存/删除模板（不会清理本实例缓存）。

### 6.6 /ureport/** 不走租户过滤器，租户校验依赖自建过滤器

**问题**: 误以为框架的 `TenantSecurityWebFilter` 会处理 `/ureport/**` 的租户校验。

**原因**: `TenantSecurityWebFilter` 只拦截 `/admin-api`、`/app-api` 前缀；`/ureport/**` 的租户上下文完全由 `UReport2SecurityFilter` 依据 `LoginUser` 注入。`tenant-id` Header 与 `tenantId` URL 参数仅用于比对，与登录用户租户不一致直接返回 403。`yudao.tenant.ignore-urls` 也未加入 `/ureport/*`（因为没有对应拦截器处理）。

**解决**: 越权校验必须依赖 `UReport2SecurityFilter`；二次开发新增 `/ureport` 之外的 UReport2 路径时，确保仍经过该过滤器，不要绕过它直接暴露模板数据。

### 6.7 查看权限白名单非常脆弱

**问题**: 只持 `report:ureport:query` 的用户访问预览/导出有时 403；UReport2 升级后原本可用的查看功能突然 403。

**原因**: 查看权限仅允许 `QUERY_ACTIONS` 中的 15 个 Action（预览、分页、打印、Excel/PDF/Word 导出、chart/storeData），且要求 `_u` 以 `db:` 开头（仅已保存的数据库模板）。URI 大小写、URL 编码、路径参数、多余斜杠等变体都不会被识别为查看请求（需要设计权限）；UReport2 升级新增 Action 时若忘记同步白名单，只持查看权限的用户会 403。

**解决**: 新增查看类 Action 时同步维护 `UReport2SecurityFilter#QUERY_ACTIONS`；前端 iframe/导出链接保持标准路径与 `db:` 前缀；不要把设计类 Action 误加入白名单。

### 6.8 静态资源路径变化会导致页面空白

**问题**: 部署后 UReport2 设计器/预览页未登录时空白，浏览器控制台显示静态资源 401/403。

**原因**: 仅放行 `GET /ureport/res/ureport-asserts/**`（由 `UReportServlet.URL + "/res/ureport-asserts/"` 拼接）。若部署时 contextPath 或 starter 版本导致路径前缀变化，静态资源会被 Spring Security 拦截。

**解决**: 部署时校验 contextPath 与 `UReportServlet.URL`，必要时同步调整 `SecurityConfiguration` 的放行路径与 `UReport2SecurityFilter#STATIC_RESOURCE_PREFIX`。

### 6.9 模板内容可能含凭据，日志脱敏不能绕过

**问题**: 二次开发自行打印 request 参数或模板内容，导致数据源账号密码泄漏到日志。

**原因**: UReport2 请求参数包含 token、`tenantId`、`_u`，保存模板时还包含模板内容（可能有数据源账号密码）。本模块已用 `UReport2ErrorLogRequestWrapper` 在 `GlobalExceptionHandler` 记录异常时屏蔽请求参数、query string、请求体与上传文件。

**解决**: 不要在 `UReport2SecurityFilter` 或 UReport2 扩展代码中直接打印原始 request/模板内容；需要排查时只记录 URI、方法、用户编号等非敏感信息。

### 6.10 Session 编号变化会导致未保存预览/图表缓存丢失

**问题**: UReport2 未保存预览报数据为空，图表数据跨请求丢失。

**原因**: Spring Security 的 `SessionManagementFilter` 在每次 token 认证后调用 `changeSessionId()`，物理 Session 编号每个请求都变化，而 UReport2 的 `TempObjectCache`、`HttpSessionReportCache` 以 `getSession().getId()` 为缓存 key。

**解决**: 不要移除链路中的 `UReport2SessionRequestWrapper` 包装；它按「用户类型:用户编号:租户编号」生成稳定编号，切换用户或租户时重新生成，不会串用他人缓存。

### 6.11 ureport2 版本锁定 2.0.1（JDK8 适配分支）

**问题**: 升级或替换 ureport2 依赖后编译/启动/运行异常。

**原因**: `yudao-dependencies/pom.xml` 将 `<ureport2.version>` 锁定为 `2.0.1`，且 groupId 为 `cn.iocoder.ureport2`（JDK8 适配分支）。模块原有的 `jimureport 2.3.4 + jimubi 2.3.2` 版本约束（见 3.1）依然生效，两套报表引擎的版本约束互不影响。

**解决**: 升级前验证 JDK8 兼容性与 `UReportServlet` 的 URL/Action 分发规则（影响 `QUERY_ACTIONS` 与静态资源前缀）；不要只升级 jimureport 或 ureport2 其中一个。

### 6.12 reportDefinitionCache 可能不存在

**问题**: 扩展代码假设 `UReport2ReportDefinitionCache` Bean 一定存在，在 `ureport.enabled=false` 时启动报依赖缺失。

**原因**: `UReport2FileServiceImpl` 对 `reportDefinitionCache` 使用 `@Autowired(required = false)`，因为 `ureport.enabled=false` 时 `UReport2Configuration` 不注册该 Bean，保存/删除仍可用但不会清理本实例缓存。

**解决**: 扩展代码注入缓存时同样使用 `required = false` 或 `ObjectProvider`，并判空处理。
