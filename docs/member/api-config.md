# 会员配置接口 (MemberConfigController)

> 管理后台的会员（积分）全局设置：维护积分抵扣与积分赠送规则，全局仅一条配置记录。

## 接口路径前缀

/member/config  (Controller: MemberConfigController)

## 1. 会员配置（MemberConfigController）

### 1.1 保存会员配置

- **路径**: PUT /member/config/save
- **权限**: member:config:save
- **说明**: 保存会员积分配置，存在记录则更新，不存在则新增（单条配置的 upsert 语义）。

**请求参数 (MemberConfigSaveReqVO)**:

继承自 MemberConfigBaseVO，无自有字段。

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pointTradeDeductEnable | Boolean | 是 | @NotNull | 积分抵扣开关 |
| pointTradeDeductUnitPrice | Integer | 是 | @NotNull | 积分抵扣，单位：分（1 积分抵扣多少分） |
| pointTradeDeductMaxPrice | Integer | 是 | @NotNull | 积分抵扣最大值 |
| pointTradeGivePoint | Integer | 是 | @NotNull | 1 元赠送多少分 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 保存成功返回 true |

**业务逻辑**:
1. 调用 `getConfig()` 查询当前数据库中的配置记录。
2. 若记录已存在，则将 SaveReqVO 转换为 MemberConfigDO 并回填已存在记录的 id，执行 `updateById` 更新。
3. 若记录不存在，则将 SaveReqVO 转换为 MemberConfigDO，执行 `insert` 新增。

### 1.2 获得会员配置

- **路径**: GET /member/config/get
- **权限**: member:config:query
- **说明**: 查询当前会员积分配置（全局唯一一条），用于后台设置页回显。

**请求参数**: 无

**响应**: CommonResult&lt;MemberConfigRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 自增主键 |
| pointTradeDeductEnable | Boolean | 积分抵扣开关 |
| pointTradeDeductUnitPrice | Integer | 积分抵扣，单位：分 |
| pointTradeDeductMaxPrice | Integer | 积分抵扣最大值 |
| pointTradeGivePoint | Integer | 1 元赠送多少分 |

**业务逻辑**:
1. 调用 `memberConfigMapper.selectList()` 查询 member_config 表全部记录。
2. 通过 `CollectionUtils.getFirst(...)` 取第一条记录作为当前配置（表中约定只存一条）。
3. 经 `MemberConfigConvert.INSTANCE.convert(...)` 转换为 MemberConfigRespVO 返回；无记录时转换结果为 null。
