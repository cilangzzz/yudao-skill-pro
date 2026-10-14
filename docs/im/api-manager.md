# 运营管理与数据看板接口 (ImSensitiveWordManagerController / ImStatisticsManagerController)

> 提供 IM 平台的运营管理能力（敏感词库维护，用于消息发送前的合规校验）与数据看板能力（用户/群/消息维度的概览、趋势与分布统计）。

## 接口路径前缀

- `/im/manager/sensitive-word` (Controller: ImSensitiveWordManagerController) —— 敏感词管理
- `/im/manager/statistics` (Controller: ImStatisticsManagerController) —— 数据看板

---

## 1. 敏感词管理（ImSensitiveWordManagerController）

敏感词通过 houbb sensitive-word 库（trie 树）构建检测器，支持忽略大小写、全/半角、数字风格（中文/阿拉伯）、繁简体；按租户维度缓存检测器实例，每分钟异步比对 `max(update_time)` 增量刷新，CRUD 后立即失效本机缓存，多实例部署最长 1 分钟内收敛。

### 1.1 新增敏感词

- **路径**: POST /im/manager/sensitive-word/create
- **权限**: im:manager:sensitive-word:create
- **说明**: 新增一个敏感词，入词库后即刻参与消息发送校验

**请求参数 (ImSensitiveWordSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 否 | | 编号（新增时不传） |
| word | String | 是 | @NotBlank / @Size(max=64) | 敏感词内容，长度不超过 64 |
| status | Integer | 是 | @NotNull / @InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |

**响应**: CommonResult\<Long\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新增敏感词编号 |

**业务逻辑**:
1. 校验敏感词唯一：按 word 精确查询，已存在则抛出 `SENSITIVE_WORD_DUPLICATED`
2. 将 ReqVO 转换为 DO 并插入 `im_sensitive_word` 表
3. 强制失效本机敏感词检测器缓存（多实例部署靠定时刷新收敛）

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_700_001 | 敏感词 '{}' 已存在 |

### 1.2 修改敏感词

- **路径**: PUT /im/manager/sensitive-word/update
- **权限**: im:manager:sensitive-word:update
- **说明**: 修改敏感词内容或状态

**请求参数 (ImSensitiveWordSaveReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 编号（修改时必填） |
| word | String | 是 | @NotBlank / @Size(max=64) | 敏感词内容，长度不超过 64 |
| status | Integer | 是 | @NotNull / @InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验敏感词存在，不存在则抛出 `SENSITIVE_WORD_NOT_EXISTS`
2. 校验敏感词唯一（排除自身记录）
3. 更新 `im_sensitive_word` 记录
4. 强制失效本机敏感词检测器缓存

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_700_000 | 敏感词不存在 |
| 1_040_700_001 | 敏感词 '{}' 已存在 |

### 1.3 删除敏感词

- **路径**: DELETE /im/manager/sensitive-word/delete
- **权限**: im:manager:sensitive-word:delete
- **说明**: 按编号删除单个敏感词

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 敏感词编号 |

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. 校验敏感词存在，不存在则抛出 `SENSITIVE_WORD_NOT_EXISTS`
2. 删除该记录
3. 强制失效本机敏感词检测器缓存

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_040_700_000 | 敏感词不存在 |

### 1.4 批量删除敏感词

- **路径**: DELETE /im/manager/sensitive-word/delete-list
- **权限**: im:manager:sensitive-word:delete
- **说明**: 按编号列表批量删除敏感词

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| ids | List\<Long\> | 是 | @Size(max=100) | 编号列表，批量删除最多 100 条 |

**响应**: CommonResult\<Boolean\> —— 固定返回 true

**业务逻辑**:
1. ids 为空时直接返回，不做处理
2. 批量删除对应记录
3. 强制失效本机敏感词检测器缓存

### 1.5 获得敏感词分页

- **路径**: GET /im/manager/sensitive-word/page
- **权限**: im:manager:sensitive-word:query
- **说明**: 分页查询敏感词，支持按内容模糊匹配、状态、创建时间区间过滤

**请求参数 (ImSensitiveWordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 是 | @NotNull | 页码（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull / @Max(200) | 每页条数（默认 10，最大 200） |
| word | String | 否 | | 敏感词，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum) | 状态（0 启用 / 1 禁用） |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间 |

**响应**: CommonResult\<PageResult\<ImSensitiveWordRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| list[].id | Long | 编号 |
| list[].word | String | 敏感词内容 |
| list[].status | Integer | 状态（0 启用 / 1 禁用） |
| list[].creator | String | 创建人 |
| list[].creatorName | String | 创建人昵称（由管理后台用户信息回填） |
| list[].createTime | LocalDateTime | 创建时间 |
| total | Long | 总条数 |

**业务逻辑**:
1. 按条件分页查询敏感词列表
2. 结果为空时直接返回空分页
3. 批量查询创建人（AdminUserApi.getUserMap）昵称
4. 转换为 RespVO 并填充 creatorName

### 1.6 获得敏感词详情

- **路径**: GET /im/manager/sensitive-word/get
- **权限**: im:manager:sensitive-word:query
- **说明**: 按编号查询单个敏感词详情

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | | 敏感词编号 |

**响应**: CommonResult\<ImSensitiveWordRespVO\>（字段同 1.5，不含 creatorName 回填逻辑）

**业务逻辑**:
1. 按编号查询敏感词记录
2. 转换为 RespVO 返回

---

## 2. 数据看板（ImStatisticsManagerController）

统计口径说明：日活/周活/月活为 N 天滚动窗口（含今天）内「发送过私聊或群聊消息」的去重用户数；用户数据来自 `system_users`，群数据来自 `im_group`，消息数据来自 `im_private_message` 与 `im_group_message` 联合聚合。

### 2.1 获得数据概览

- **路径**: GET /im/manager/statistics/overview
- **权限**: im:manager:statistics:query
- **说明**: 一次性返回用户、群、消息维度的核心指标卡片数据

**请求参数**: 无

**响应**: CommonResult\<ImStatisticsManagerOverviewRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| totalUser | Long | 用户总数 |
| newUserToday | Long | 今日新增用户数 |
| totalGroup | Long | 群总数（仅统计正常状态群） |
| newGroupToday | Long | 今日新建群数 |
| activeUserDaily | Long | 日活用户（今日发过消息的去重用户数） |
| activeUserWeekly | Long | 周活用户（最近 7 天发过消息的去重用户数） |
| activeUserMonthly | Long | 月活用户（最近 30 天发过消息的去重用户数） |
| privateMessageToday | Long | 今日私聊消息数 |
| groupMessageToday | Long | 今日群聊消息数 |
| privateMessageYesterday | Long | 昨日私聊消息数 |
| groupMessageYesterday | Long | 昨日群聊消息数 |

**业务逻辑**:
1. 计算时间窗口：今日 [0 点, 明日 0 点)、昨日、周活窗口（近 7 天含今日）、月活窗口（近 30 天含今日）
2. 查询用户总数与今日新增用户数（system_users）
3. 查询群总数与今日新建群数（im_group，正常状态）
4. 分别统计日/周/月活：时间窗口内私聊 + 群聊消息表发送者去重计数
5. 统计今日与昨日的私聊、群聊消息数，组装为概览 VO 返回

### 2.2 获得消息趋势（私聊 / 群聊双线）

- **路径**: GET /im/manager/statistics/message-trend
- **权限**: im:manager:statistics:query
- **说明**: 返回最近 N 天私聊与群聊消息量的每日双线趋势

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| days | Integer | 否 | @Min(1) / @Max(90) | 回看天数（含今日），默认 7 |

**响应**: CommonResult\<ImStatisticsManagerTrendRespVO\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| dates | List\<LocalDateTime\> | 横轴日期序列（每天 00:00:00，前端按需取日期部分） |
| series | Map\<String, List\<Long\>\> | 数据系列：key 为 private（私聊）/ group（群聊），value 为与 dates 等长的计数数组 |

**业务逻辑**:
1. 生成最近 days 天（含今日）的日期序列，并推导查询起止时间
2. 按天聚合私聊消息数（im_private_message 按 send_time 分组）
3. 按天聚合群聊消息数（im_group_message 按 send_time 分组）
4. 将每日聚合结果对齐到日期序列，缺失天补 0，组装 private/group 双系列返回

### 2.3 获得用户趋势（新增注册 / 日活双线）

- **路径**: GET /im/manager/statistics/user-trend
- **权限**: im:manager:statistics:query
- **说明**: 返回最近 N 天新增注册用户与日活用户的每日双线趋势

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| days | Integer | 否 | @Min(1) / @Max(90) | 回看天数（含今日），默认 7 |

**响应**: CommonResult\<ImStatisticsManagerTrendRespVO\>（字段同 2.2，series 的 key 为 register（新增注册）/ active（日活））

**业务逻辑**:
1. 生成最近 days 天（含今日）的日期序列，并推导查询起止时间
2. 按天聚合新增注册用户数（system_users 按 create_time 分组）
3. 按天聚合日活用户数（私聊 + 群聊消息表按天对发送者去重计数）
4. 对齐日期序列、缺失天补 0，组装 register/active 双系列返回

### 2.4 获得内容类型分布（最近 30 天）

- **路径**: GET /im/manager/statistics/message-type-distribution
- **权限**: im:manager:statistics:query
- **说明**: 统计最近 30 天私聊 + 群聊消息的内容类型（文本/图片/语音等）分布

**请求参数**: 无

**响应**: CommonResult\<List\<ImStatisticsManagerMessageTypeRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| type | Integer | 消息类型（参见 ImContentTypeEnum 枚举） |
| value | Long | 该类型消息数 |

**业务逻辑**:
1. 计算最近 30 天（含今日）的时间窗口
2. 联合聚合私聊与群聊消息，按消息类型 type 分组计数
3. 转换为 type/value 列表返回

### 2.5 获得群规模分布

- **路径**: GET /im/manager/statistics/group-size-distribution
- **权限**: im:manager:statistics:query
- **说明**: 按群成员数量级分桶统计群数量

**请求参数**: 无

**响应**: CommonResult\<List\<ImStatisticsManagerGroupSizeRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| range | String | 区间名称（"1-9 人" / "10-49 人" / "50-199 人" / "200+ 人"） |
| count | Long | 该区间群数量 |

**业务逻辑**:
1. 统计每个群的成员数量，按 1-9 / 10-49 / 50-199 / 200+ 人数分桶
2. 按固定的桶展示顺序输出，无数据的桶补 0

### 2.6 获得消息 TOP 发送者（最近 30 天）

- **路径**: GET /im/manager/statistics/top-senders
- **权限**: im:manager:statistics:query
- **说明**: 统计最近 30 天发送消息数最多的 10 个用户

**请求参数**: 无

**响应**: CommonResult\<List\<ImStatisticsManagerTopSenderRespVO\>\>

| 字段 | 类型 | 说明 |
|-----|------|------|
| userId | Long | 用户编号 |
| nickname | String | 用户昵称（由管理后台用户信息回填） |
| messageCount | Long | 消息数 |

**业务逻辑**:
1. 计算最近 30 天（含今日）的时间窗口
2. 联合聚合私聊与群聊消息，按发送者分组计数，取 TOP 10
3. 批量查询用户昵称（AdminUserApi.getUserMap）回填 nickname 后返回

---

## 错误码汇总

本域错误码使用 1-040-700-000 段（敏感词）；敏感词校验在消息发送链路抛出的运行时错误码如下。

| 错误码 | 说明 |
|-------|------|
| 1_040_700_000 | 敏感词不存在 |
| 1_040_700_001 | 敏感词 '{}' 已存在 |
| 1_040_300_004 | 消息包含敏感词，无法发送（消息发送时经 validateText 校验触发） |

数据看板接口为纯查询，无专属错误码。
