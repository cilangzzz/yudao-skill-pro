# 支付统计接口 (PayStatisticsController)

> 提供管理后台的支付（钱包充值）统计数据查询，目前包含充值金额汇总统计。

## 接口路径前缀

/statistics/pay  (Controller: PayStatisticsController)

## 1. 支付汇总

### 1.1 获取充值金额

- **路径**: GET /statistics/pay/summary
- **权限**: 已认证（仅登录，未设置 `@PreAuthorize` 权限标识）
- **说明**: 统计已支付的钱包充值总金额（充值金额，单位分）。

**请求参数**: 无

**响应**: CommonResult<PaySummaryRespVO>

| 字段 | 类型 | 说明 |
|-----|------|-----|
| rechargePrice | Integer | 充值金额，单位分 |

**业务逻辑**:
1. Controller 调用 `PayWalletStatisticsService#getRechargePriceSummary()`，该 Service 实现类为 `PayWalletStatisticsServiceImpl`。
2. Service 委托 `PayWalletStatisticsMapper#selectRechargePriceSummary(payStatus=true)` 执行统计查询。
3. SQL 对 `pay_wallet_recharge`（钱包充值单）表执行 `SUM(pay_price)`，过滤条件为 `pay_status = TRUE`（仅统计已支付成功的充值单）且 `deleted = FALSE`。
4. 查询按当前租户隔离：当 `TenantContextHolder#getTenantId()` 不为空时追加 `tenant_id` 条件。
5. 无符合记录时 `IFNULL(SUM(pay_price), 0)` 返回 0；结果经 MapStruct 转换器 `PayStatisticsConvert#convert(Integer)` 包装为 `PaySummaryRespVO` 返回。

**补充说明**:
- `PayWalletStatisticsServiceImpl` 还提供 `getWalletSummary(beginTime, endTime)`（统计时间段内充值/退款/钱包支付金额，供交易统计对账使用）与 `getUserRechargeSummary(beginTime, endTime)`（按钱包分组统计用户充值），二者均为内部 Service 方法，被交易统计等模块调用，未在本控制器暴露 admin 端点。
- 本域为纯统计查询，无专属业务错误码。
