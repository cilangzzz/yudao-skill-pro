# 微信回调接口 (MpOpenController)

> 接收微信官方服务器的两类回调请求：服务器接入时的签名校验（GET echostr 验证），以及粉丝消息/事件推送的接收与自动回复路由；接口直接返回 XML/纯文本字符串而非 CommonResult，供微信服务器协议对接使用。

## 接口路径前缀

/mp/open  (Controller: MpOpenController)

> 两个端点均标注 `@TenantIgnore`（不按请求头解析租户），并在 yudao-server 的 application.yaml 中通过 `security.permit-all-urls` 配置 `/admin-api/mp/open/**` 放行——微信服务器回调不携带登录凭证，无需认证。租户归属由回调参数 appId 反查账号后确定。

---

## 1. 微信服务器回调

### 1.1 校验签名（服务器接入验证）

- **路径**: GET /mp/open/{appId}
- **权限**: 无需认证（permit-all 放行，微信服务器回调）
- **说明**: 微信公众号后台配置服务器 URL 时，微信服务器发起的接入验证请求；校验通过原样返回 echostr，否则返回「非法请求」。

**请求参数 (MpOpenCheckSignatureReqVO)**: 路径参数 appId + Query 参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| appId | String | 是 | 路径参数 | 公众号 appId，如「wx5b23ba7a5589ecbb」 |
| signature | String | 是 | @NotEmpty | 微信加密签名 |
| timestamp | String | 是 | @NotEmpty | 时间戳 |
| nonce | String | 是 | @NotEmpty | 随机数 |
| echostr | String | 是 | @NotEmpty | 随机字符串（校验通过时需原样返回） |

**响应**: String（produces = text/plain;charset=utf-8，非 CommonResult 包装）

| 值 | 说明 |
|-----|------|
| echostr | 校验通过时，原样返回随机字符串，微信服务器确认接入成功 |
| 非法请求 | 校验不通过时返回的固定文本 |

**业务逻辑**:
1. 记录日志：appId 与微信服务器推送的认证消息参数（signature/timestamp/nonce/echostr）。
2. 通过 MpServiceFactory.getRequiredMpService(appId) 获取该公众号对应的 WxMpService 实例（其配置来自本地账号缓存，appId 不存在时直接抛出异常）。
3. 调用 WxMpService.checkSignature(timestamp, nonce, signature) 按微信接入签名算法校验。
4. 校验通过：返回 echostr；校验不通过：返回文本「非法请求」。

### 1.2 处理消息（消息/事件推送回调）

- **路径**: POST /mp/open/{appId}
- **权限**: 无需认证（permit-all 放行，微信服务器回调）
- **说明**: 接收微信服务器推送的粉丝消息或事件 XML，校验签名、解析后交给该公众号的消息路由器（WxMpMessageRouter）处理，并将自动回复以 XML 形式同步返回。

**请求参数 (MpOpenHandleMessageReqVO)**: 路径参数 appId + Query 参数 + 请求体

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| appId | String | 是 | 路径参数 | 公众号 appId |
| signature | String | 是 | @NotEmpty | 微信加密签名 |
| timestamp | String | 是 | @NotEmpty | 时间戳 |
| nonce | String | 是 | @NotEmpty | 随机数 |
| openid | String | 是 | @NotEmpty | 粉丝 openid |
| encrypt_type | String | 否 | - | 消息加密类型；为空表示明文模式，「aes」表示 AES 加密模式 |
| msg_signature | String | 否 | - | 消息体签名，AES 加密模式下解密必需 |

请求体为 XML 字符串（@RequestBody String content），即微信推送的消息原文（明文 XML 或加密 XML）。

**响应**: String（produces = application/xml; charset=UTF-8，非 CommonResult 包装）

| 值 | 说明 |
|-----|------|
| 回复消息 XML | 明文模式返回 outMessage.toXml()；AES 模式返回 outMessage.toEncryptedXml(...) 加密后的 XML |
| 空字符串 | 路由无回复消息（outMessage 为 null）或加密类型不匹配时返回 "" |

**业务逻辑**:
1. 根据 appId 从本地账号缓存获取公众号账号（MpAccountServiceImpl.initLocalCache 启动时全量构建、refreshLocalCache 每 60 秒按 updateTime 增量刷新），appId 不存在则断言失败提示「公众号 appId 不存在」。
2. 将 appId 写入 MpContextHolder 上下文，并以账号所属租户执行 TenantUtils.execute，使后续消息处理在正确租户下运行，finally 中清理上下文。
3. 校验请求签名：WxMpService.checkSignature(timestamp, nonce, signature)，不通过则断言失败「非法请求」。
4. 解析消息体：encrypt_type 为空走明文模式 WxMpXmlMessage.fromXml(content)；encrypt_type=aes 走 AES 加密模式 WxMpXmlMessage.fromEncryptedXml(content, 配置, timestamp, nonce, msg_signature)；解析结果为空则报「消息解析失败」。
5. 从 MpServiceFactory 获取该公众号的 WxMpMessageRouter 并 route(inMessage) 分发处理（按消息类型/关键字匹配自动回复规则），得到回复消息 outMessage；无回复则返回空串。
6. 按加密模式序列化并返回回复：明文模式 outMessage.toXml()，AES 模式 outMessage.toEncryptedXml(mppService.getWxMpConfigStorage())；其他 encrypt_type 返回空串。

---

## 错误码说明

本域两个端点不使用 mp 模块（1-006-000-000 段）的错误码：签名校验失败与 appId 不存在均通过 Assert 断言抛出全局异常（「非法请求」「公众号 appId({}) 不存在」「消息解析失败」），或以纯文本「非法请求」返回给微信服务器。回调链路依赖的账号数据来自公众号账号域（见 api-account.md），相关错误码如下：

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在（账号域维护缓存时的存在性校验） |
