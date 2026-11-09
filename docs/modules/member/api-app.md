# App 端接口（AppXxxController 汇总）

> 会员模块 App 端（`controller/app`）接口汇总：认证登录、个人中心、收件地址、社交用户、签到、等级经验、积分记录。前缀统一走 `/app-api`（网关按 `app-api` 前缀路由，下表路径为 Controller 声明的相对路径）。除标注 `@PermitAll` 的接口外，均需登录后以当前用户身份访问（用户编号取自登录态，不接受前端传参）。

## 接口总览

### 认证 (AppAuthController)

前缀：`/member/auth`（全部 `@PermitAll` 免登录）

| 接口路径 | HTTP方法 | 说明 | 请求/响应 VO |
|---------|---------|------|-------------|
| /member/auth/login | POST | 使用手机 + 密码登录 | AppAuthLoginReqVO → AppAuthLoginRespVO |
| /member/auth/logout | POST | 登出系统（按请求头/参数中的 Token） | 无 → Boolean |
| /member/auth/refresh-token | POST | 刷新令牌（Query 参数 refreshToken） | 无 → AppAuthLoginRespVO |
| /member/auth/sms-login | POST | 使用手机 + 验证码登录 | AppAuthSmsLoginReqVO → AppAuthLoginRespVO |
| /member/auth/send-sms-code | POST | 发送手机验证码 | AppAuthSmsSendReqVO → Boolean |
| /member/auth/validate-sms-code | POST | 校验手机验证码 | AppAuthSmsValidateReqVO → Boolean |
| /member/auth/social-auth-redirect | GET | 社交授权的跳转（返回授权 URL） | type + redirectUri（Query）→ String |
| /member/auth/social-login | POST | 社交快捷登录，使用 code 授权码 | AppAuthSocialLoginReqVO → AppAuthLoginRespVO |
| /member/auth/weixin-mini-app-login | POST | 微信小程序的一键登录 | AppAuthWeixinMiniAppLoginReqVO → AppAuthLoginRespVO |
| /member/auth/create-weixin-jsapi-signature | POST | 创建微信 JS SDK 初始化所需的签名 | url（Query）→ SocialWxJsapiSignatureRespDTO |

**业务逻辑要点**: 密码/验证码/社交登录在 `MemberAuthServiceImpl` 中完成；`smsLogin` / `socialLogin` 标注 `@Transactional`，内部含 `useSmsCode`、`createUserIfAbsent`（新用户自动注册）、`bindSocialUser`、`createAccessToken`，登录事务提交后才会发出 `MemberUserCreateMessage`（见 pitfalls 2.1）。登录成功写登录日志（LoginLogApi）。

### 用户个人中心 (AppMemberUserController)

前缀：`/member/user`（除 reset-password 外均需登录）

| 接口路径 | HTTP方法 | 说明 | 请求/响应 VO |
|---------|---------|------|-------------|
| /member/user/get | GET | 获得基本信息（当前登录用户） | 无 → AppMemberUserInfoRespVO |
| /member/user/update | PUT | 修改基本信息 | AppMemberUserUpdateReqVO → Boolean |
| /member/user/update-mobile | PUT | 修改用户手机（短信验证码校验，oldCode 可选） | AppMemberUserUpdateMobileReqVO → Boolean |
| /member/user/update-mobile-by-weixin | PUT | 基于微信小程序的授权码，修改用户手机 | AppMemberUserUpdateMobileByWeixinReqVO → Boolean |
| /member/user/update-password | PUT | 修改用户密码（需手机验证码） | AppMemberUserUpdatePasswordReqVO → Boolean |
| /member/user/reset-password | PUT | 重置密码（忘记密码，手机号 + 验证码），`@PermitAll` 免登录 | AppMemberUserResetPasswordReqVO → Boolean |

**业务逻辑要点**:
- `get` 返回昵称、头像、手机、邮箱、性别、积分、经验及内嵌等级 `Level`（id/name/level/icon）、`brokerageEnabled`（分销开关，恒 true 由 Convert 填充）；`user.levelId` 为 0/null 时等级为 null。
- `update` 仅允许改昵称/头像/邮箱/性别，更新前校验邮箱唯一（被占用抛 `1_004_001_004`）。
- `update-mobile`：校验新手机唯一，旧手机验证码 oldCode 非空时一并校验；`update-mobile-by-weixin`：调 SocialClientApi 解析小程序授权码得到手机号后校验唯一并更新。

### 用户收件地址 (AppAddressController)

前缀：`/member/address`（均需登录，userId 取当前登录用户）

| 接口路径 | HTTP方法 | 说明 | 请求/响应 VO |
|---------|---------|------|-------------|
| /member/address/create | POST | 创建用户收件地址 | AppAddressCreateReqVO → Long（新地址编号） |
| /member/address/update | PUT | 更新用户收件地址 | AppAddressUpdateReqVO → Boolean |
| /member/address/delete | DELETE | 删除用户收件地址（Query 参数 id） | 无 → Boolean |
| /member/address/get | GET | 获得用户收件地址（Query 参数 id） | 无 → AppAddressRespVO |
| /member/address/get-default | GET | 获得默认的用户收件地址 | 无 → AppAddressRespVO |
| /member/address/list | GET | 获得用户收件地址列表 | 无 → List\<AppAddressRespVO\> |

**业务逻辑要点**: 增删改查均按「当前登录用户 + 地址编号」双重校验，地址不存在抛 `1_004_004_000`；设为默认地址时自动取消该用户原默认地址（`updateDefault`）；创建第 1 条地址自动设为默认。`AppAddressRespVO` 含 id/name/mobile/areaId/areaName/detailAddress/defaultStatus/createTime。

### 社交用户 (AppSocialUserController)

前缀：`/member/social-user`

| 接口路径 | HTTP方法 | 说明 | 免登录 | 请求/响应 VO |
|---------|---------|------|-------|-------------|
| /member/social-user/bind | POST | 社交绑定，使用 code 授权码 | `@PermitAll` | AppSocialUserBindReqVO → String（openid） |
| /member/social-user/unbind | DELETE | 取消社交绑定 | 需登录 | AppSocialUserUnbindReqVO → Boolean |
| /member/social-user/get | GET | 获得社交用户（Query 参数 type，SocialTypeEnum） | 需登录 | 无 → AppSocialUserRespVO |
| /member/social-user/wxa-qrcode | POST | 获得微信小程序码（返回 base64 image） | `@PermitAll` | AppSocialWxaQrcodeReqVO → String |
| /member/social-user/get-subscribe-template-list | GET | 获得微信小程序订阅模板列表 | `@PermitAll` | 无 → List\<AppSocialWxaSubscribeTemplateRespVO\> |

**业务逻辑要点**: bind/unbind/get 委托 system 模块 `SocialUserApi`（绑定关系按 `userType = MEMBER` + 当前登录用户）；wxa-qrcode / 订阅模板列表委托 `SocialClientApi`。

### 签到 (AppMemberSignInConfigController / AppMemberSignInRecordController)

| 接口路径 | HTTP方法 | 说明 | 免登录 | 响应 VO |
|---------|---------|------|-------|---------|
| /member/sign-in/config/list | GET | 获得签到规则列表（仅启用状态） | `@PermitAll` | List\<AppMemberSignInConfigRespVO\> |
| /member/sign-in/record/get-summary | GET | 获得个人签到统计（总天数/连续天数/今日是否已签） | 需登录 | AppMemberSignInRecordSummaryRespVO |
| /member/sign-in/record/create | POST | 签到（按规则发积分与经验） | 需登录 | AppMemberSignInRecordRespVO |
| /member/sign-in/record/page | GET | 获得签到记录分页（仅当前用户，PageParam） | 需登录 | PageResult\<AppMemberSignInRecordRespVO\> |

**业务逻辑要点**: 签到 `create` 在事务内：取最近一条记录判重（今日已签抛 `1_004_010_000`）→ 按连续天数匹配规则（无启用规则或配置列表为空会 NPE，见 pitfalls 4.1）→ 插入记录 → 发积分（MemberPointBizTypeEnum.SIGN）→ 加经验（MemberExperienceBizTypeEnum.SIGN_IN）。

### 等级与经验 (AppMemberLevelController / AppMemberExperienceRecordController)

| 接口路径 | HTTP方法 | 说明 | 免登录 | 响应 VO |
|---------|---------|------|-------|---------|
| /member/level/list | GET | 获得会员等级列表（仅启用状态，按 level 升序） | `@PermitAll` | List\<AppMemberLevelRespVO\> |
| /member/experience-record/page | GET | 获得当前用户的经验记录分页（PageParam） | 需登录 | PageResult\<AppMemberExperienceRecordRespVO\> |

### 积分记录 (AppMemberPointRecordController)

| 接口路径 | HTTP方法 | 说明 | 免登录 | 响应 VO |
|---------|---------|------|-------|---------|
| /member/point/record/page | GET | 获得当前用户的积分记录分页（AppMemberPointRecordPageReqVO：createTime 区间等） | 需登录 | PageResult\<AppMemberPointRecordRespVO\> |

## 错误码

App 端常用错误码与各业务域一致，见 [api-user.md](api-user.md)、[api-tag.md](api-tag.md) 等域文档；认证域独有：`1_004_003_000`（账号密码不正确）、`1_004_003_001`（账号被禁用）、`1_004_003_005`（解析不到三方登录信息）、`1_004_003_007`（手机号已经被使用）。
