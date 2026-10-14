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

**解决**: 同时打开根 pom 的 `<module>` 与 yudao-server pom 的 `<dependency>` 两处注释；保持 `spring.ai.chat.client.enabled=false` 不要恢复；首次启用还需按上游/官方 SQL 建 `report_go_view_project` 表（含 `tenant_id`，见 1.1）以及积木报表自带的 `jimu_*`、`onl_drag_*` 表（由 starter 官方 SQL 维护，不在本仓库）。

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

### 5.2 错误码仅 1 个，ajreport 包是待删除的占位目录

**问题**: 扩展 report 模块时错误提示单一（除"GoView 项目不存在"外没有其它业务错误码）；`ajreport` 相关子包看似可用，实际为空壳。

**原因**: `ErrorCodeConstants` 仅定义了 `GO_VIEW_PROJECT_NOT_EXISTS(1_003_000_000)` 一个错误码；`controller/admin/ajreport`、`service/ajreport`、`convert/ajreport`、`dal/dataobject/ajreport`、`dal/mysql/ajreport` 等 5 个包只有 `package-info.java`，注释为"TODO 芋艿：占位，待删除"；`framework/jmreport/core/web` 包也标注了"占位，后续会基于 Filter 实现积木报表的认证等功能，替代 JmReportTokenServiceImpl"。

**解决**: 新增功能时在 `1_003_000_000` 段内顺延错误码（注意避开 system 的 1_002 段与 member 的 1_004 段）；不要在 ajreport 占位包里写代码，后续版本会被删除；jmreport 认证若要改造，参考 `framework/jmreport/core/web` 包注释的规划方向。
