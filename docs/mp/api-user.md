# 公众号粉丝接口 (MpUserController)

> 提供微信公众号粉丝的分页查询、详情查询、基本信息与标签更新，以及从微信服务器异步全量同步粉丝的能力。

## 接口路径前缀

/mp/user  (Controller: MpUserController)

## 1. 粉丝查询

### 1.1 获得公众号粉丝分页

- **路径**: GET /mp/user/page
- **权限**: mp:user:query
- **说明**: 按公众号账号分页查询粉丝列表，支持 openid、unionId、昵称模糊匹配。

**请求参数 (MpUserPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | 继承 PageParam | 页码，从 1 开始 |
| pageSize | Integer | 是 | 继承 PageParam | 每页条数 |
| accountId | Long | 是 | @NotNull | 公众号账号的编号 |
| openid | String | 否 | 无 | 公众号粉丝标识，模糊匹配 |
| unionId | String | 否 | 无 | 微信生态唯一标识，模糊匹配 |
| nickname | String | 否 | 无 | 公众号粉丝昵称，模糊匹配 |

**响应**: `CommonResult<PageResult<MpUserRespVO>>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 编号 |
| openid | String | 公众号粉丝标识 |
| unionId | String | 微信生态唯一标识 |
| subscribeStatus | Integer | 关注状态，参见 CommonStatusEnum 枚举 |
| subscribeTime | LocalDateTime | 关注时间 |
| unsubscribeTime | LocalDateTime | 取消关注时间 |
| nickname | String | 昵称 |
| headImageUrl | String | 头像地址 |
| language | String | 语言 |
| country | String | 国家 |
| province | String | 省份 |
| city | String | 城市 |
| remark | String | 备注 |
| tagIds | List\<Long\> | 标签编号数组 |
| accountId | Long | 公众号账号的编号 |
| appId | String | 公众号账号的 appId |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 接收分页查询条件，账号编号为必填，openid / unionId / 昵称均为模糊匹配。
2. 调用 `MpUserMapper.selectPage` 按条件分页查询粉丝记录。
3. 通过 `MpUserConvert.convertPage` 将 DO 分页结果转换为 RespVO 分页结果返回。

### 1.2 获得公众号粉丝

- **路径**: GET /mp/user/get
- **权限**: mp:user:query
- **说明**: 按编号查询单个粉丝详情。

**请求参数**: 无（查询参数 `id`：编号，Long，必填）

**响应**: `CommonResult<MpUserRespVO>`，字段结构同 1.1 的 MpUserRespVO 字段表。

**业务逻辑**:
1. 调用 `MpUserMapper.selectById` 按编号查询粉丝记录。
2. 通过 `MpUserConvert.convert` 将 DO 转换为 RespVO 返回。

## 2. 粉丝维护

### 2.1 更新公众号粉丝

- **路径**: PUT /mp/user/update
- **权限**: mp:user:update
- **说明**: 更新粉丝的昵称、备注，并同步粉丝标签到微信公众号。

**请求参数 (MpUserUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull | 粉丝编号 |
| nickname | String | 否 | 无 | 昵称 |
| remark | String | 否 | 无 | 备注 |
| tagIds | List\<Long\> | 否 | 无 | 标签编号数组 |

**响应**: `CommonResult<Boolean>`，更新成功返回 true。

**业务逻辑**:
1. 校验粉丝是否存在，不存在则抛出 `USER_NOT_EXISTS`（粉丝不存在）异常。
2. 第一步，更新标签到公众号：通过 `MpServiceFactory` 获取 appId 对应的 `WxMpService`，先查询粉丝在公众号上的原有标签列表，逐个调用 `batchUntagging` 取消旧标签。
3. 再遍历新传入的标签编号数组，逐个调用 `batchTagging` 为粉丝打上新标签；若微信接口调用失败（WxErrorException），抛出 `USER_UPDATE_TAG_FAIL`（更新粉丝标签失败，原因：{}）。
4. 第二步，更新基本信息到数据库：将 ReqVO 转换为 `MpUserDO`，以原粉丝编号执行 `updateById` 持久化昵称、备注等字段。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_003_000 | 粉丝不存在 |
| 1_006_003_001 | 更新粉丝标签失败，原因：{} |

### 2.2 同步公众号粉丝

- **路径**: POST /mp/user/sync
- **权限**: mp:user:sync
- **说明**: 从微信服务器异步全量拉取指定公众号的粉丝列表并落库（新增或更新）。

**请求参数**: 无（查询参数 `accountId`：公众号账号的编号，Long，必填）

**响应**: `CommonResult<Boolean>`，任务提交成功返回 true。

**业务逻辑**:
1. 方法标注 `@Async` 异步执行：根据账号编号调用 `MpAccountService.getRequiredAccount` 获取公众号账号（不存在时抛出 `ACCOUNT_NOT_EXISTS`）。
2. 使用 for 循环而非递归调用 `syncUser0`，避免递归出意外导致死循环；每次以 `nextOpenid` 为游标，调用微信 `userList` 流式加载一批粉丝 openid 列表。
3. 若本批 openid 列表为空，直接返回 null 结束同步。
4. 将 openid 列表按 100 个一批切分，调用微信 `userInfoList` 批量加载粉丝详细信息。
5. `batchSaveUser`：按 appId + openid 批量查询数据库中已存在的粉丝，构建 openid 到 DO 的映射；已存在的粉丝逐条 `updateById` 更新，不存在的收集后 `insertBatch` 批量插入。
6. 返回微信接口的 `nextOpenid` 作为下一次拉取游标；游标为空表示同步完毕，期间发生 `WxErrorException` 则记录错误日志并终止同步。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_006_000_000 | 公众号账号不存在 |
