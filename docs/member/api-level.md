# 会员等级 API

> 会员等级体系相关接口，包含等级配置、经验管理、自动升降级等功能。

## 1. 概述

| 项目 | 说明 |
|------|------|
| 管理后台 Controller | `admin/level/MemberLevelController` |
| Service | `MemberLevelService` / `MemberLevelRecordService` / `MemberExperienceRecordService` |
| 路径前缀 | `/member/level` |
| 权限前缀 | `member:level:*` |

## 2. 管理后台接口

### 2.1 等级配置管理

#### 查询等级列表

| 项目 | 说明 |
|------|------|
| 权限 | `member:level:query` |
| 说明 | 查询所有等级配置，按 level 值排序 |

#### 创建等级

| 项目 | 说明 |
|------|------|
| 权限 | `member:level:create` |
| 说明 | 新增会员等级配置 |

**字段说明：**

| 字段 | 说明 |
|------|------|
| name | 等级名称 |
| level | 等级值，用于排序和比较 |
| experience | 升级所需经验 |
| discount_percent | 享受折扣百分比 |
| icon | 等级图标 |
| background_url | 等级背景图 |

#### 修改等级

| 项目 | 说明 |
|------|------|
| 权限 | `member:level:update` |
| 说明 | 修改等级配置信息 |

#### 删除等级

| 项目 | 说明 |
|------|------|
| 权限 | `member:level:delete` |
| 说明 | 删除等级（需确保无用户关联） |

### 2.2 等级变更记录查询

| 项目 | 说明 |
|------|------|
| 权限 | `member:level:query` |
| 说明 | 查询用户等级变更历史记录 |

### 2.3 经验记录查询

| 项目 | 说明 |
|------|------|
| 权限 | `member:level:query` |
| 说明 | 查询用户经验变动历史记录 |

## 3. 跨模块 API

`MemberLevelApi` 为其他模块提供的接口：

| 方法 | 说明 | 消费方 |
|------|------|--------|
| getMemberLevel(Long levelId) | 查询等级详情 | mall-trade |
| addExperience(Long userId, Integer experience, Integer bizType, String bizId) | 增加经验，自动触发等级计算 | mall-trade |
| reduceExperience(Long userId, Integer experience, Integer bizType, String bizId) | 减少经验，自动触发等级计算 | mall-trade |

## 4. 等级自动升级机制

### 核心流程（模板方法模式）

```
1. 记录经验变更 -> MemberExperienceRecordDO
2. 更新用户经验值 -> MemberUserDO.experience
3. 计算新等级 -> 根据经验匹配最高等级
4. 如果等级变更 -> 记录等级变更 -> 更新用户等级
5. 通知用户等级变更
```

### 等级计算规则

- 根据用户当前经验，查找 `experience <= 用户经验` 的最高等级
- 等级配置的 `experience` 字段表示升级到该等级所需的经验值
- 等级值（level 字段）必须递增，经验值也必须递增
- 系统自动校验等级配置的合理性

### 等级配置示例

| 等级 | level | experience | discount_percent | 说明 |
|------|-------|------------|-----------------|------|
| 普通会员 | 1 | 0 | 100 | 注册即获得 |
| 银卡会员 | 2 | 1000 | 98 | 消费满1000经验升级 |
| 金卡会员 | 3 | 5000 | 95 | 消费满5000经验升级 |
| 钻石会员 | 4 | 20000 | 90 | 消费满20000经验升级 |

## 5. 经验获取来源

通过 `MemberExperienceBizTypeEnum` 枚举定义：

| type | name | 说明 | 增减 |
|------|------|------|------|
| 0 | ADMIN | 管理员调整 | + |
| 1 | INVITE_REGISTER | 邀新奖励 | + |
| 4 | SIGN_IN | 签到奖励 | + |
| 11 | ORDER_GIVE | 下单奖励 | + |

### 新增经验来源

1. 在 `MemberExperienceBizTypeEnum` 中添加新枚举值
2. 在对应业务场景调用 `MemberLevelApi.addExperience`

## 6. 数据模型

### member_level 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 等级 ID |
| name | String | 等级名称 |
| level | Integer | 等级值 |
| experience | Integer | 升级所需经验 |
| discount_percent | Integer | 折扣百分比 |
| icon | String | 等级图标 |
| background_url | String | 背景图 |
| status | Integer | 状态（0-启用，1-禁用） |

### member_level_record 表

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | Long | 用户 ID |
| level_id | Long | 等级 ID |
| level | Integer | 等级值（冗余） |
| discount_percent | Integer | 折扣（冗余） |
| experience | Integer | 升级经验（冗余） |
| user_experience | Integer | 用户变更后经验 |

### member_experience_record 表

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | Long | 用户 ID |
| biz_type | Integer | 业务类型 |
| biz_id | String | 业务编号 |
| experience | Integer | 变动经验（正负） |
| total_experience | Integer | 变动后经验 |

## 7. 错误码

| 错误码 | 说明 |
|--------|------|
| 1_004_011_000 | 用户等级不存在 |
