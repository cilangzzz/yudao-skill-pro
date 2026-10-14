# 转账单接口 (PayTransferController)

> 管理后台转账单管理：提供转账单的详情查询、分页查询与 Excel 导出能力。转账单（向用户/商户打款）由业务系统通过 `PayTransferApi` 发起创建，由渠道回调与定时轮询驱动状态流转（等待转账 → 转账进行中 → 转账成功 / 转账关闭）。

## 接口路径前缀

/pay/transfer  (Controller: PayTransferController)

---

## 1. 转账单查询

### 1.1 获得转账订单

- **路径**: GET /pay/transfer/get
- **权限**: pay:transfer:query
- **说明**: 按编号查询单笔转账单详情，并拼接所属支付应用的名称；单据不存在时返回空对象而非报错。

**请求参数**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| id | Long | 是 | @RequestParam 必传 | 转账单编号 |

**响应**: CommonResult&lt;PayTransferRespVO&gt;

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 编号（转账单编号） |
| no | String | 转账单号 |
| appId | Long | 应用编号 |
| appName | String | 应用名称（控制器拼接） |
| channelId | Long | 转账渠道编号 |
| channelCode | String | 转账渠道编码 |
| merchantTransferId | String | 商户转账单编号 |
| status | Integer | 转账状态（0 等待转账 / 5 转账进行中 / 10 转账成功 / 20 转账关闭） |
| successTime | LocalDateTime | 转账成功时间 |
| price | Integer | 转账金额（单位：分） |
| subject | String | 转账标题 |
| userName | String | 收款人姓名 |
| userAccount | String | 收款人账号 |
| notifyUrl | String | 异步通知商户地址 |
| userIp | String | 用户 IP |
| channelExtras | Map&lt;String, String&gt; | 渠道的额外参数 |
| channelTransferNo | String | 渠道转账单号 |
| channelErrorCode | String | 调用渠道的错误码 |
| channelErrorMsg | String | 调用渠道的错误提示 |
| channelNotifyData | String | 渠道的同步/异步通知的内容 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 按 id 调用 `payTransferService.getTransfer` 查询转账单（`transferMapper.selectById`）。
2. 若转账单不存在，直接返回空的 `PayTransferRespVO`（不抛出异常）。
3. 若存在，按转账单的 `appId` 调用 `payAppService.getApp` 查询所属支付应用。
4. 通过 `BeanUtils.toBean` 将 `PayTransferDO` 转换为 `PayTransferRespVO`，并将应用名称写入 `appName`。
5. 包装为 `CommonResult` 成功结果返回。

**错误码**: 转账模块（1_007_009_XXX 段）全量错误码，供该域参考（查询接口未命中数据时返回空对象，不抛错；创建/通知类错误码由业务系统调用 PayTransferApi 发起转账及渠道回调、轮询流程触发）：

| 错误码 | 说明 |
|---|---|
| 1_007_009_001 | 转账单不存在 |
| 1_007_009_002 | 转账发起失败，原因：两次相同转账请求的类型不匹配 |
| 1_007_009_003 | 转账发起失败，原因：两次相同转账请求的金额不匹配 |
| 1_007_009_004 | 转账发起失败，原因：已经存在相同的转账单，且状态不是已关闭 |
| 1_007_009_006 | 通知转账结果失败，原因：转账单不处于待转账 |
| 1_007_009_007 | 通知转账结果失败，原因：转账单不处于待转账或转账中 |

### 1.2 获得转账订单分页

- **路径**: GET /pay/transfer/page
- **权限**: pay:transfer:query
- **说明**: 按多条件分页查询转账单列表，并批量拼接所属支付应用名称。

**请求参数 (PayTransferPageReqVO)**: | 字段 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| pageNo | Integer | 是 | @NotNull、@Min(1)（继承 PageParam） | 页码，从 1 开始，默认 1 |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200)（继承 PageParam） | 每页条数，默认 10 |
| no | String | 否 | - | 转账单号 |
| appId | Long | 否 | - | 应用编号 |
| channelCode | String | 否 | - | 渠道编码，例：wx_app |
| merchantOrderId | String | 否 | - | 商户转账单编号 |
| status | Integer | 否 | - | 转账状态（0/5/10/20，取值同 1.1） |
| userName | String | 否 | - | 收款人姓名 |
| userAccount | String | 否 | - | 收款人账号 |
| channelTransferNo | String | 否 | - | 渠道转账单号 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat（yyyy-MM-dd HH:mm:ss） | 创建时间范围（起止区间） |

**响应**: CommonResult&lt;PageResult&lt;PayTransferRespVO&gt;&gt;，`PayTransferRespVO` 字段结构同 1.1（`appName` 为控制器拼接的批量应用名称）。

**业务逻辑**:
1. 调用 `payTransferService.getTransferPage` 按条件分页查询转账单（`transferMapper.selectPage`，支持单号、应用、渠道、商户单号、状态、收款人、渠道单号、创建时间等条件）。
2. 提取分页结果中所有转账单的 `appId` 集合，调用 `payAppService.getAppMap` 批量查询支付应用。
3. 通过 `BeanUtils.toBean` 将分页结果批量转换为 `PayTransferRespVO`，逐条按 `appId` 拼接 `appName`（应用不存在时跳过）。
4. 包装为 `CommonResult` 成功结果返回分页数据。

---

## 2. 转账单导出

### 2.1 导出转账订单 Excel

- **路径**: GET /pay/transfer/export-excel
- **权限**: pay:transfer:export
- **说明**: 按与分页查询相同的过滤条件导出全量转账单 Excel（文件名"转账订单.xls"）；`@ApiAccessLog(operateType = EXPORT)` 记录导出操作日志。

**请求参数 (PayTransferPageReqVO)**: 过滤字段同 1.2 分页查询；入参中的 `pageSize` 不生效，控制器内部强制置为 `PAGE_SIZE_NONE`（-1）以不分页查询全部数据。

**响应**: 无 `CommonResult` 包装，直接向 HttpServletResponse 输出 Excel 文件流；单行结构即 `PayTransferRespVO`（`@ExcelProperty` 定义列名，金额字段经 `MoneyConvert` 由分转元，转账状态、转账渠道经 `DictConvert` 按字典翻译）。

**业务逻辑**:
1. 将 `pageReqVO` 的 `pageSize` 置为 `PAGE_SIZE_NONE`（-1），关闭分页以查询全部符合条件的转账单。
2. 复用 1.2 的分页查询逻辑（调用 `getTransferPage`）获取全量数据，并完成应用名称 `appName` 拼接。
3. 调用 `ExcelUtils.write` 以 `PayTransferRespVO` 为表结构、文件名"转账订单.xls"向响应流写出 Excel 文件。
