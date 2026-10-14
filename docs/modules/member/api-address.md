# 用户收件地址接口 (AddressController)

> 管理后台查询会员（用户）收件地址的接口。地址的新增、修改、删除由 App 端 `AppAddressController`（`/member/address/*`，已认证用户操作本人地址）提供，管理后台仅提供按用户查看地址列表的能力。

## 接口路径前缀
/member/address  (Controller: AddressController)

## 1. 地址查询

### 1.1 获得用户收件地址列表

- **路径**: GET /member/address/list
- **权限**: member:user:query
- **说明**: 按用户编号查询该会员的全部收件地址（含默认与非默认地址），供管理后台查看会员地址信息。

**请求参数 (Query)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| userId | Long | 是 | @RequestParam(required = true) | 用户编号 |

**响应**: `CommonResult<List<AddressRespVO>>`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 收件地址编号 |
| name | String | 收件人名称 |
| mobile | String | 手机号 |
| areaId | Long | 地区编码 |
| areaName | String | 地区名称（如“上海上海市普陀区”，由 areaId 格式化得到） |
| detailAddress | String | 收件详细地址 |
| defaultStatus | Boolean | 是否默认 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**:
1. 接收查询参数 `userId`，调用 `AddressService#getAddressList(userId)`。
2. Service 调用 `MemberAddressMapper#selectListByUserIdAndDefaulted(userId, null)` 查询该用户全部收件地址（`defaulted` 传 `null` 表示不过滤是否默认）。
3. 通过 `AddressConvert.INSTANCE.convertList2` 将 `MemberAddressDO` 列表转换为 `AddressRespVO` 列表，转换时基于 `areaId` 调用 `AreaUtils.format` 生成完整地区名称 `areaName`。
4. 包装为 `CommonResult` 成功结果返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_004_000 | 用户收件地址不存在（AddressService 更新/删除地址时校验抛出） |
