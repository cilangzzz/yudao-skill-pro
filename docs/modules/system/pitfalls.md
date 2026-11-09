# 注意事项与已知坑点 (system)

> 本文档汇总 system 模块在菜单权限、OAuth2 令牌生命周期、回调地址校验以及跨数据库兼容方面的已知坑点与升级注意事项。

## 1. 菜单查询范围与超级管理员豁免

- `GET /system/menu/list`（【菜单管理】界面）与 `GET /system/menu/list-all-simple`（别名 `simple-list`，用于【角色分配菜单】等选项）**不再无条件返回全量菜单**，而是走 `MenuService.getMenuListByTenant`，按**当前租户套餐**（`system_tenant_package.menu_ids`）过滤未开通的菜单。
- 仅当登录用户在其**登录租户**下持有 `super_admin` 角色时跳过套餐过滤，返回全部菜单。判定在 `TenantUtils.execute(loginUser.getTenantId(), ...)` 上下文内通过 `permissionService.hasAnyRoles` 完成，因此超级管理员**切换到被访问租户后仍能看到全部菜单**。
- 排查「某个租户在【菜单管理】里看不到某个菜单」时，应先核对租户套餐的 `menu_ids` 是否包含该菜单，而不是直接怀疑菜单数据或菜单状态。
- 「超管豁免」用的是**登录租户**而不是被访问租户：在被访问租户里新建的 `super_admin` 角色不会让当前用户获得豁免。
- 多租户关闭（`yudao.tenant.enable=false`）时不做套餐过滤；系统租户（`package_id = 0`，`TenantDO.PACKAGE_ID_SYSTEM`）视为拥有全部菜单。

## 2. OAuth2 令牌生命周期（issue 1332）

- **刷新令牌时不再删除旧访问令牌**：`POST /system/auth/refresh-token` 与 `POST /system/oauth2/token`（`grant_type=refresh_token`）在刷新成功后，同一 `refresh_token` 名下的旧访问令牌（MySQL + Redis）都会保留，直到其自身 `expires_time` 自然失效。
- 设计取舍：多个标签页共享同一个刷新令牌时，若刷新即删除旧令牌，会导致其它标签页的访问令牌失效、互相刷新甚至被踢下线。代价是——在共享设备或令牌泄露场景下，用户「刷新」并不能踢掉已泄露的旧令牌。
- **仅当刷新令牌本身已过期时**，才会先删除该 `refresh_token` 名下的所有访问令牌，再删除刷新令牌，并抛出 401「刷新令牌已过期」。
- **登出/吊销会级联清理**：删除访问令牌时（`POST /system/auth/logout`、`DELETE /system/oauth2/token`、`DELETE /system/oauth2-token/delete`、`DELETE /system/oauth2-token/delete-list`），除目标访问令牌外，还会删除**同一 `refresh_token` 名下的其它访问令牌**（MySQL + Redis），并删除该刷新令牌。其它刷新令牌下的访问令牌不受影响。
- 影响面扩大：多标签页场景下任意一个标签页登出，会让其它标签页的访问令牌立即失效（刷新阶段保留、退出阶段收紧，是刻意的设计）。

## 3. OAuth2 回调地址校验（破坏性变更）

- `redirect_uri` 校验由「前缀匹配（`StrUtils.startWithAny`）」改为「与客户端注册的 `redirect_uris` **完全相等**（`CollUtil.contains`）」，依据 RFC 9700 4.1.3，防止 host、userinfo、路径、参数拼接绕过。
- 以下差异均视为不匹配，抛出错误码 `1_002_020_005`（`OAUTH2_CLIENT_REDIRECT_URI_NOT_MATCH`，消息 `无效 redirect_uri: {}`）：
  - host 混淆、userinfo 注入（如 `https://evil@app.example.com/...`）
  - 端口不同（`https://app.example.com:8443/...`）
  - 路径后缀/父路径（`.../callback/login`、`.../callback/`）
  - query、fragment（`...?next=...`、`...#...`）
  - 大小写差异
- **升级注意**：调用 `/system/oauth2/token`（authorization_code）或 `/system/oauth2/authorize` 的客户端，必须把注册的 `redirect_uris` 与前端/第三方应用实际传递的 `redirect_uri` 字面量完全对齐（含协议、host、端口、末尾斜杠、大小写）。原先「注册地址是前缀即可通过」的回调地址升级后会直接失败。

## 4. 跨数据库（信创）兼容约定

- OAuth2 访问令牌/刷新令牌的过期批量删除，已由 MySQL 专属的 `DELETE ... LIMIT` 改为 `SqlDialectUtils.deleteBatchByLessThan` 按方言生成 SQL：
  - PostgreSQL：`IN (SELECT ... LIMIT ...)`
  - Oracle：`ROWNUM`
  - SQL Server：`TOP`
  - 其余（含 MySQL）：`LIMIT`
  自定义 SQL 中继续手写 `DELETE ... LIMIT` 会在 Oracle/SQL Server 上报错。
- 布尔列在非 MySQL 数据库（如 SQL Server）不一定支持 `bit`，统一按 0/1 整数存储。`SmsCodeDO.used` 显式绑定 `IntegerBooleanTypeHandler`（写入 1/0，读取时 `!= 0` 视为 true），并将 `@TableName` 改为 `autoResultMap = true` 以启用结果映射；对应建表脚本中 `used` 为 `tinyint`（SQL Server 为 `smallint`）。
- `SmsCodeMapper.selectLastByMobile`（`LambdaQueryWrapperX` + `selectFirstOne`）与 `NotifyMessageMapper.selectUnreadListByUserIdAndUserType`（`LambdaQueryWrapperX` + `selectListLimitN`）只是内部查询写法统一，接口语义与返回值不变。

## 5. 扫码登录（二维码）的状态机与一次性领取

- 扫码登录共三个接口：`POST /system/auth/create-qrcode`（生成）、`POST /system/auth/confirm-qrcode`（手机确认）、`POST /system/auth/qrcode-login`（电脑轮询领取）。
- 状态存放在 Redis（`AdminAuthQrcodeRedisDAO`），key 为 `auth_qrcode:{qrcodeId}:{tenantId}`（关闭多租户时无租户后缀），Hash 字段为 `status`（0 WAITING / 1 CONFIRMED）、`secretHash`、`userId`，TTL 固定 180 秒。
- **领取凭证 secret 只保存在生成二维码的页面**，二维码内容为 `YuDaoLogin:{qrcodeId}`，不包含 secret；Redis 中只存 secret 的 SHA-256 摘要。
- 三个操作（创建、确认、轮询）都通过 Lua 脚本原子执行：
  - 创建：编号已存在则不覆盖，直接失败；
  - 确认：二维码不存在/已过期抛 `1_002_000_009`（AUTH_QRCODE_INVALID），被**其它**用户确认抛 `1_002_000_010`（AUTH_QRCODE_ALREADY_CONFIRMED），同一用户重复确认幂等成功；确认**不刷新 TTL**；
  - 轮询：secret 摘要不匹配、二维码过期、已被领取都返回空并抛 `1_002_000_009`；状态为 CONFIRMED 时**原子删除 key**（只能领取一次）。
- 常见坑：电脑端轮询成功后二维码即被删除，若此时登录流程失败或响应丢失，**必须重新扫码**（无法重试领取）。

## 6. 部门批量删除的数据权限校验

- `DELETE /system/dept/delete-list` 会先执行 `DeptServiceImpl.validateDeptListDataScope`：待删部门必须**全部**位于当前用户的数据权限范围内，任一不在即抛 `1_002_004_008`（DEPT_NOT_IN_SCOPE，「部门({})不在数据权限范围内，禁止操作」）。
- 该校验与数据权限插件的过滤规则保持一致，避免插件只删除范围内部门造成的「部分成功」。
- 跳过校验的场景：`ids` 为空、`skipPermissionCheck()` 为 true（跨租户访问/内部调用）、`@DataPermission(enable = false)`、数据权限为「全部」。

---

## 7. 文档与源码一致性提醒

- 菜单接口实际路径为 `GET /system/menu/list`、`GET /system/menu/list-all-simple`（别名 `simple-list`），另有 `DELETE /system/menu/delete-list` 批量删除；不要沿用旧文档中的 `/system/menu/get-list`、`/system/menu/get-simple-list`。
- 管理后台 Controller 位于 `controller.admin` 包，统一挂载在 `/admin-api` 前缀；`controller.app` 包下的 Controller 挂载在 `/app-api` 前缀（`WebProperties.adminApi` / `appApi`，按包路径 `**.controller.admin.**` / `**.controller.app.**` 匹配）。因此 App 端的字典与地区接口实际路径为 `GET /app-api/system/dict-data/type`、`GET /app-api/system/area/tree`、`GET /app-api/system/tenant/get-by-website`，与管理后台同名相对路径并不冲突。
- 角色与菜单的接口详情已合并到 [api-permission.md](api-permission.md)（不再有独立的 `api-role.md` / `api-menu.md`）。
