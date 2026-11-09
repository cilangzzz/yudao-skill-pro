# 设备影子接口 (IotDeviceShadowController)

> IoT 设备影子：以数据库 `iot_device_shadow` 为权威数据源，保存设备上报状态（reported）与管理端期望状态（desired），支持开关、重置与属性级更新时间对比。管理后台查询走 Redis 60s 读缓存加速，写入与版本校验始终读数据库。

## 接口路径前缀

- /iot/device/shadow (Controller: IotDeviceShadowController)

---

## 1. 获取设备影子
- **路径**: GET /iot/device/shadow/get
- **权限**: iot:device:shadow-query
- **说明**: 按设备编号获取影子，并左连接产品物模型的属性定义，返回 desired/reported 的属性级对比列表。影子不存在时按启用状态惰性创建一条空影子（desired/reported/metadata 均为空 Map、version=0）。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceId | Long | 是 | @RequestParam | 设备编号 |

**响应**: CommonResult&lt;IotDeviceShadowRespVO&gt;

| 字段 | 类型 | 说明 |
|------|------|------|
| version | Long | 影子版本号（乐观锁） |
| shadowTime | Long | 文档最后更新时间（epoch 秒） |
| status | Integer | 影子开关状态（CommonStatusEnum：0 开启 / 1 关闭） |
| properties | List&lt;IotDeviceShadowPropertyRespVO&gt; | 按物模型属性对齐的对比列表 |
| desired | Map&lt;String, Object&gt; | 期望状态（原始 Map） |
| reported | Map&lt;String, Object&gt; | 上报状态（原始 Map） |
| metadata | Map&lt;String, Object&gt; | 元数据：{ desired: { key: { timestamp } }, reported: { ... } } |

IotDeviceShadowPropertyRespVO 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| identifier | String | 属性标识符 |
| name | String | 属性名称 |
| dataType | String | 数据类型 |
| dataSpecs | ThingModelDataSpecs | 数据定义 |
| dataSpecsList | List&lt;ThingModelDataSpecs&gt; | 数据定义列表 |
| desiredValue | Object | 期望值（取自 desired） |
| reportedValue | Object | 上报值（取自 reported） |
| desiredTime | Long | 期望值更新时间（epoch 秒，取自 metadata.desired） |
| reportedTime | Long | 上报值更新时间（epoch 秒，取自 metadata.reported） |

**业务逻辑**:
1. 校验设备存在，不存在抛 DEVICE_NOT_EXISTS。
2. `getOrCreateShadow`：先读 Redis 缓存 `iot:device_shadow:{deviceId}`（TTL 60s，仅供展示，允许短暂读到旧值）；未命中则读 DB，不存在时以 `status=开启` 插入空影子并回填缓存。
3. 按设备产品查询物模型属性（type=1 属性），把 desired/reported 与 metadata 中的时间戳对齐到每个属性。
4. 返回影子 VO；desired/reported/metadata 为空时返回空 Map。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |

> 注意：影子未启用时该接口不会抛 DEVICE_SHADOW_NOT_ENABLED，仍返回影子内容（开关状态见 status）。

## 2. 更新设备影子期望状态
- **路径**: PUT /iot/device/shadow/update-desired
- **权限**: iot:device:shadow-update
- **说明**: 合并更新 desired（只覆盖传入的属性，未传属性保持不变），按 version 乐观锁递增；若设备在线，还会主动向设备推送一份全量影子。

**请求参数 (IotDeviceShadowUpdateDesiredReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceId | Long | 是 | @NotNull | 设备编号 |
| desired | Map&lt;String, Object&gt; | 是 | @NotNull | 期望状态；为空 Map 时直接返回成功，不做更新 |

**响应**: CommonResult&lt;Boolean&gt; — 成功返回 true

**业务逻辑**:
1. 校验设备存在，读取 DB 影子（不存在则创建）。
2. 影子未启用时抛 DEVICE_SHADOW_NOT_ENABLED。
3. desired 为空时直接返回（不更新、不推送）。
4. 乐观锁合并：每轮读取 DB 最新影子重新合并（避免并发丢失），合并后属性数超过 128 抛 DEVICE_SHADOW_PROPERTY_COUNT_EXCEEDED；按 version 条件更新，最多重试 3 次，仍冲突抛 DEVICE_SHADOW_VERSION_CONFLICT。
5. 更新成功后在事务提交后删除 Redis 缓存，并记录每个属性的 desired 时间戳。
6. 若设备在线（Redis 中存在 serverId），通过 `thing.shadow.update` 回复封套主动推送全量影子（requestId 为空）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_007_100 | 设备影子未启用 |
| 1_050_007_101 | 设备影子版本冲突 |
| 1_050_007_102 | 设备影子属性数超过限制 |

## 3. 更新设备影子开关状态
- **路径**: PUT /iot/device/shadow/update-status
- **权限**: iot:device:shadow-update
- **说明**: 开启/关闭某设备的影子功能；影子不存在时按目标状态直接创建。

**请求参数 (IotDeviceShadowUpdateStatusReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceId | Long | 是 | @NotNull | 设备编号 |
| status | Integer | 是 | @NotNull / @InEnum(CommonStatusEnum) | 影子状态：0 开启 / 1 关闭 |

**响应**: CommonResult&lt;Boolean&gt; — 成功返回 true

**业务逻辑**:
1. 校验设备存在。
2. 读取 DB 影子；不存在时按目标 status 创建空影子。
3. 状态与目标不一致时按 deviceId 更新 status。
4. 删除 Redis 缓存，确保后续读取到最新开关。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |

## 4. 重置设备影子
- **路径**: DELETE /iot/device/shadow/reset
- **权限**: iot:device:shadow-update
- **说明**: 清空设备的 desired、reported、metadata，并将 version 归 0；**不删除影子记录**。影子本来不存在时视为成功。

**请求参数**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| deviceId | Long | 是 | @RequestParam | 设备编号 |

**响应**: CommonResult&lt;Boolean&gt; — 成功返回 true

**业务逻辑**:
1. 校验设备存在。
2. 以乐观锁方式（最多 3 次重试）将 desired/reported/metadata 置为空 Map、version 置 0、shadowTime 置当前秒；记录不存在直接返回成功。
3. 更新成功后删除 Redis 缓存；3 次仍版本冲突抛 DEVICE_SHADOW_VERSION_CONFLICT。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_050_003_000 | 设备不存在 |
| 1_050_007_101 | 设备影子版本冲突 |

---

## 5. 设备端影子协议（thing.shadow.update）

管理后台之外，设备也可通过上行消息 `thing.shadow.update` 读写影子；biz 处理后以 `thing.shadow.update` 回复（网关下发到 Topic `thing/shadow/update_reply`）。

**上行 params (IotDeviceShadowUpdateReqDTO)**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| method | String | 内层方法：get（读取全量影子）/ update（合并上报） |
| state | ShadowState | 影子状态，update 时必填；内含 `reported` Map |
| version | Long | 设备已知版本号，可缺省；为 -1 时清空影子（无需 state） |

**处理规则**:
1. 影子未启用时忽略上行，不回复。
2. method=get：回复全量 desired/reported/version/shadowTime。
3. method=update 且 version=-1：清空影子（同重置），回复 version=0 与当前时间。
4. method=update：校验 state/reported 非空后合并 reported，按期望 version 校验并递增；合并后属性数超过 128 返回错误。
5. 处理异常时回复 SERVER_ERROR，但回复发送失败只记日志，不影响上行处理。

**回复错误码（code，见 IotDeviceShadowErrorCodeEnum）**:

| 错误码 | 说明 |
|-------|------|
| 400 | JSON 格式错误 |
| 401 | 缺少 method |
| 402 | 缺少 state |
| 404 | 缺少 reported |
| 405 | reported 为空 |
| 406 | 无效内层 method |
| 408 | 影子属性数超过限制 |
| 409 | 影子版本冲突 |
| 500 | 服务端异常 |

> 说明：以上为设备影子协议回复中的业务 code（非系统错误码）；管理后台接口的业务异常使用 biz 的 1_050_007_100 段错误码。
