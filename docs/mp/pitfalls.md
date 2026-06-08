# 常见陷阱

## 1. 多账号 WxMpService 获取

**问题**：直接注入 `WxMpService` 导致多账号场景下无法区分。

**正确做法**：通过 `MpServiceFactory` 获取指定账号的 `WxMpService`。

```java
// 错误
@Resource
private WxMpService wxMpService;

// 正确
@Resource
private MpServiceFactory mpServiceFactory;

WxMpService mpService = mpServiceFactory.getRequiredMpService(appId);
```

## 2. MpContextHolder 生命周期

**问题**：`MpContextHolder` 使用 ThreadLocal 存储 appId，在异步处理或线程池中丢失上下文。

**正确做法**：在进入异步处理前保存上下文，异步任务中手动设置。

```java
String appId = MpContextHolder.getAppId();
executor.execute(() -> {
    MpContextHolder.setAppId(appId);
    try {
        // 处理逻辑
    } finally {
        MpContextHolder.clear();
    }
});
```

## 3. WxErrorException 异常处理

**问题**：未捕获 `WxErrorException`，导致微信 API 错误直接抛出到前端。

**正确做法**：捕获并转换为业务异常。

```java
try {
    mpService.someOperation();
} catch (WxErrorException e) {
    throw exception(ERROR_CODE, e.getError().getErrorMsg());
}
```

## 4. 消息路由规则顺序

**问题**：`WxMpMessageRouter` 规则按添加顺序匹配，规则顺序错误导致消息被错误处理器拦截。

**正确做法**：将精确匹配规则放在前面，通用规则放在后面。

```java
// 先匹配关键词回复（精确）
router.rule().async(false).keyword("xxx").handler(keywordHandler).end();
// 再匹配消息类型回复（通用）
router.rule().async(false).msgType(WxConsts.XmlMsgType.TEXT).handler(defaultHandler).end();
```

## 5. 素材 media_id 有效期

**问题**：临时素材 `media_id` 有效期 3 天，过期后无法使用。

**正确做法**：永久素材使用 `media_id` 不会过期，临时素材需及时使用或重新上传。

## 6. 微信回调签名校验

**问题**：签名校验失败导致回调请求被拒绝。

**正确做法**：确保 `MpOpenController` 中的签名校验逻辑正确，Token、AppId、AES Key 配置一致。

## 7. 循环依赖

**问题**：`MpServiceFactory` 与其他 Service 之间可能存在循环依赖。

**正确做法**：使用 `@Lazy` 注解延迟加载。

```java
@Resource
@Lazy
private MpServiceFactory mpServiceFactory;
```

## 8. 粉丝信息同步时机

**问题**：粉丝信息未及时同步，本地数据与微信数据不一致。

**正确做法**：关注事件触发时实时同步，定期批量同步更新。

## 9. 模板消息发送限制

**问题**：模板消息发送频率超限或模板 ID 无效。

**正确做法**：发送前校验模板有效性，控制发送频率。

```java
// 校验模板存在
MpMessageTemplateDO template = validateMsgTemplateExists(sendReqVO.getId());
// 构建并发送
mpServiceFactory.getRequiredMpService(template.getAppId())
    .getTemplateMsgService().sendTemplateMsg(templateMessage);
```

## 10. 多租户数据隔离

**问题**：`MpAccountDO` 使用 `TenantBaseDO`，查询时需注意租户过滤。

**正确做法**：确保查询条件包含租户信息，框架自动过滤。

## 11. 错误码规范

模块错误码前缀为 `1-006-XXX-XXX`，常见错误码：

| 错误码 | 说明 |
|--------|------|
| 1_006_000_000 | 公众号账号不存在 |
| 1_006_003_000 | 粉丝不存在 |
| 1_006_005_000 | 发送消息失败 |
| 1_006_009_000 | 自动回复不存在 |
| 1_006_010_004 | 发送模版消息失败 |
