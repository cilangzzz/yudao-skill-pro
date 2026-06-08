# 积分系统 API

> 会员积分相关接口，包含积分查询、增减、记录追踪等功能。

## 1. 概述

| 项目 | 说明 |
|------|------|
| 管理后台 Controller | `admin/point/MemberPointRecordController` |
| Service | `MemberPointRecordService` |
| 路径前缀 | `/member/point-record` |
| 权限前缀 | `member:point:*` |

## 2. 管理后台接口

### 2.1 查询积分记录列表

| 项目 | 说明 |
|------|------|
| 权限 | `member:point:query` |
| 说明 | 分页查询积分变动记录，支持按用户 ID、业务类型筛选 |

### 2.2 查询用户积分记录

| 项目 | 说明 |
|------|------|
| 权限 | `member:point:query` |
| 说明 | 查询指定用户的积分变动历史 |

## 3. 跨模块 API

`MemberPointApi` 为其他模块提供的接口：

| 方法 | 说明 | 消费方 |
|------|------|--------|
| addPoint(Long userId, Integer point, Integer bizType, String bizId) | 增加积分 | mall-trade, mall-promotion |
| reducePoint(Long userId, Integer point, Integer bizType, String bizId) | 减少积分 | mall-trade, mall-promotion |

## 4. 积分业务流程

### 4.1 积分变更核心流程

```java
@Transactional(rollbackFor = Exception.class)
public void createPointRecord(Long userId, Integer point,
        MemberPointBizTypeEnum bizType, String bizId) {
    // 1. 校验用户积分余额
    MemberUserDO user = memberUserService.getUser(userId);
    int totalPoint = ObjectUtil.defaultIfNull(user.getPoint(), 0) + point;
    if (totalPoint < 0) {
        throw exception(USER_POINT_NOT_ENOUGH);
    }
    // 2. 更新用户积分
    memberUserService.updateUserPoint(userId, point);
    // 3. 增加积分记录
    MemberPointRecordDO record = new MemberPointRecordDO()
            .setUserId(userId).setBizId(bizId).setBizType(bizType.getType())
            .setPoint(point).setTotalPoint(totalPoint);
    memberPointRecordMapper.insert(record);
}
```

### 4.2 积分来源类型

通过 `MemberPointBizTypeEnum` 枚举定义：

| type | name | 说明 | 增减 |
|------|------|------|------|
| 1 | SIGN | 签到 | + |
| 2 | ADMIN | 管理员修改 | + |
| 11 | ORDER_USE | 订单积分抵扣 | - |
| 21 | ORDER_GIVE | 订单积分奖励 | + |

### 4.3 新增积分来源步骤

1. 在 `MemberPointBizTypeEnum` 中添加新的枚举值
2. 设置 type（唯一）、name、description、add（是否增加）
3. 在对应业务场景调用 `MemberPointApi.addPoint` 或 `reducePoint`

**示例：**

```java
// 新增积分来源
MemberPointApi.addPoint(userId, 10,
    MemberPointBizTypeEnum.NEW_TYPE.getType(), bizId);
```

## 5. 积分抵扣配置

积分抵扣相关配置通过 `MemberConfigApi` 获取，存储在 `member_config` 表中：

| 配置项 | 说明 |
|--------|------|
| point_trade_deduct_enable | 积分抵扣开关 |
| point_trade_deduct_unit_price | 积分抵扣单位（1 积分 = 多少分钱） |
| point_trade_deduct_max_price | 积分抵扣上限（分） |
| point_trade_give_point | 1 元赠送积分 |

### 积分抵扣流程（mall-trade 模块调用）

1. 查询 `MemberConfigApi.getConfig` 获取积分抵扣配置
2. 检查 `point_trade_deduct_enable` 是否开启
3. 计算可抵扣金额：`min(用户积分 * 单价, 订单金额, 抵扣上限)`
4. 调用 `MemberPointApi.reducePoint` 扣减积分

### 积分赠送流程（mall-trade 模块调用）

1. 查询配置获取 `point_trade_give_point`
2. 计算赠送积分：`订单金额(元) * point_trade_give_point`
3. 调用 `MemberPointApi.addPoint` 赠送积分，业务类型为 `ORDER_GIVE`

## 6. 数据模型

### member_point_record 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录 ID |
| user_id | Long | 用户 ID |
| biz_id | String | 业务编码（如订单号） |
| biz_type | Integer | 业务类型（枚举） |
| title | String | 积分标题 |
| description | String | 积分描述 |
| point | Integer | 变动积分（正为增加，负为减少） |
| total_point | Integer | 变动后积分余额 |

### MemberUserDO 中的积分字段

| 字段 | 类型 | 说明 |
|------|------|------|
| point | Integer | 当前积分（冗余字段，每次变更时实时更新） |

## 7. 错误码

| 错误码 | 说明 |
|--------|------|
| 1_004_001_003 | 用户积分余额不足 |
| 1_004_008_000 | 用户积分记录业务类型不支持 |

## 8. 注意事项

- 积分变更是原子操作：更新用户积分 + 写入积分记录在同一事务中
- `point` 字段为变动值（正数增加，负数减少），`total_point` 为变更后余额
- 用户表的 `point` 字段是冗余的实时余额，与积分记录表保持一致
- 跨模块调用应使用 `MemberPointApi`，不要直接操作 Mapper
