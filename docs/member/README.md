# Member 模块文档

> 会员中心模块 (`yudao-module-member`)，负责管理C端用户的会员体系。

## 1. 模块概述

会员模块是系统的核心业务模块之一，定位为 **C端用户的核心数据层**，与 `system` 模块的 AdminUser 区分。主要职责：

- 为 mall 模块提供会员信息、积分抵扣、等级折扣等支持
- 通过 API 接口对外暴露会员服务，支持跨模块调用
- 管理会员全生命周期：注册、登录、等级成长、积分消费

### 设计原则

| 原则 | 说明 |
|------|------|
| 领域驱动设计 | MemberUser 作为聚合根，关联等级、积分、标签等实体 |
| 分层架构 | Controller -> Service -> DAL 清晰分层 |
| 单一职责 | 每个 Service 专注一个业务领域 |
| 开闭原则 | 通过枚举定义业务类型，便于扩展新的积分/经验来源 |
| 事务一致性 | 积分变更、等级变更使用 `@Transactional` 保证数据一致性 |
| 多租户隔离 | MemberUserDO 继承 TenantBaseDO，支持多租户 |

## 2. 核心功能

| 功能域 | 说明 | 关键服务 |
|--------|------|----------|
| 会员认证 | 注册、登录、登出、Token 刷新、社交登录 | MemberAuthService |
| 用户管理 | 个人信息、状态管理、用户查询 | MemberUserService |
| 等级体系 | 等级配置、经验累积、自动升降级 | MemberLevelService |
| 积分系统 | 积分获取、消费、记录追踪 | MemberPointRecordService |
| 签到功能 | 每日签到、连续签到奖励、签到规则配置 | MemberSignInRecordService / MemberSignInConfigService |
| 收货地址 | 多地址管理、默认地址切换 | AddressService |
| 标签分组 | 会员标签、会员分组分类管理 | MemberTagService / MemberGroupService |
| 会员配置 | 积分抵扣开关、抵扣比例等全局配置 | MemberConfigService |

## 3. API 索引

### 3.1 跨模块 API（供其他模块调用）

| API 接口 | 方法 | 消费方 |
|----------|------|--------|
| MemberUserApi | getUser / getUserList / getUserByMobile / validateUser | pay, mall-trade, mall-promotion |
| MemberPointApi | addPoint / reducePoint | mall-trade, mall-promotion |
| MemberLevelApi | getMemberLevel / addExperience / reduceExperience | mall-trade |
| MemberAddressApi | getAddress / getDefaultAddress | mall-trade |
| MemberConfigApi | getConfig | mall-trade |

### 3.2 HTTP 接口

| 接口分组 | Controller | 说明 | 详情链接 |
|----------|-----------|------|----------|
| 管理后台 - 用户 | MemberUserController | 会员用户管理 | [api-user.md](api-user.md) |
| 管理后台 - 等级 | MemberLevelController | 等级配置管理 | [api-level.md](api-level.md) |
| 管理后台 - 积分 | MemberPointRecordController | 积分记录查询 | [api-point.md](api-point.md) |
| 管理后台 - 签到 | MemberSignInConfigController | 签到规则配置 | [api-signin.md](api-signin.md) |
| 管理后台 - 标签 | MemberTagController | 标签管理 | [api-tag-group.md](api-tag-group.md) |
| 管理后台 - 分组 | MemberGroupController | 分组管理 | [api-tag-group.md](api-tag-group.md) |
| C端 - 认证 | AppAuthController | 登录、注册、登出 | [api-auth.md](api-auth.md) |
| C端 - 地址 | AppAddressController | 收货地址 | [api-address.md](api-address.md) |
| C端 - 签到 | AppMemberSignInRecordController | 每日签到 | [api-signin.md](api-signin.md) |

## 4. 数据模型

详见 [data-model.md](data-model.md)。

### 核心实体关系

```
MemberUser (聚合根)
  |-- N:1 --> MemberLevel (等级)
  |-- N:1 --> MemberGroup (分组)
  |-- N:N --> MemberTag  (标签, JSON数组)
  |-- 1:N --> MemberPointRecord (积分记录)
  |-- 1:N --> MemberExperienceRecord (经验记录)
  |-- 1:N --> MemberLevelRecord (等级记录)
  |-- 1:N --> MemberSignInRecord (签到记录)
  |-- 1:N --> MemberAddress (收货地址)
```

### 数据表清单

| 表名 | 实体类 | 说明 | 继承 |
|------|--------|------|------|
| member_user | MemberUserDO | 会员用户表 | TenantBaseDO |
| member_level | MemberLevelDO | 会员等级表 | BaseDO |
| member_point_record | MemberPointRecordDO | 积分记录表 | BaseDO |
| member_experience_record | MemberExperienceRecordDO | 经验记录表 | BaseDO |
| member_level_record | MemberLevelRecordDO | 等级变更记录表 | BaseDO |
| member_sign_in_config | MemberSignInConfigDO | 签到配置表 | BaseDO |
| member_sign_in_record | MemberSignInRecordDO | 签到记录表 | BaseDO |
| member_tag | MemberTagDO | 会员标签表 | BaseDO |
| member_group | MemberGroupDO | 会员分组表 | BaseDO |
| member_address | MemberAddressDO | 收货地址表 | BaseDO |
| member_config | MemberConfigDO | 会员配置表 | BaseDO |

## 5. 设计模式

| 模式 | 位置 | 用途 |
|------|------|------|
| DTO 转换模式 | `api/*/dto/*.java` | API 层使用 DTO 隔离内部 DO，保护领域模型 |
| 策略模式（枚举实现） | `MemberPointBizTypeEnum` | 定义积分业务类型，支持多种积分来源 |
| 模板方法 | `MemberLevelServiceImpl` | 等级变更流程：记录变更 -> 更新经验 -> 计算新等级 -> 通知用户 |
| Facade 模式 | `*ApiImpl.java` | API 实现类封装 Service 调用，简化跨模块交互 |
| 观察者模式（MQ） | `MemberUserProducer` | 用户创建后发送消息，解耦后续处理逻辑 |

## 6. 依赖关系

### 6.1 内部依赖（本模块依赖其他模块）

| 模块 | API | 用途 |
|------|-----|------|
| system | SmsCodeApi | 短信验证码校验（登录、修改手机、重置密码） |
| system | SocialClientApi | 社交登录（微信、QQ 等）、微信小程序登录 |
| infra | 文件存储 | 头像上传存储 |

### 6.2 外部依赖（第三方库）

| 库 | 版本 | 用途 |
|----|------|------|
| spring-security-crypto | Spring Boot 自带 | 密码加密（BCryptPasswordEncoder） |
| mybatis-plus | 3.x | ORM 框架，数据访问增强 |
| hutool | 5.x | 工具类库 |

## 7. 枚举定义

### 积分业务类型 (MemberPointBizTypeEnum)

| type | name | 说明 | 增减 |
|------|------|------|------|
| 1 | SIGN | 签到 | + |
| 2 | ADMIN | 管理员修改 | + |
| 11 | ORDER_USE | 订单积分抵扣 | - |
| 21 | ORDER_GIVE | 订单积分奖励 | + |

### 经验业务类型 (MemberExperienceBizTypeEnum)

| type | name | 说明 | 增减 |
|------|------|------|------|
| 0 | ADMIN | 管理员调整 | + |
| 1 | INVITE_REGISTER | 邀新奖励 | + |
| 4 | SIGN_IN | 签到奖励 | + |
| 11 | ORDER_GIVE | 下单奖励 | + |

## 8. 错误码

错误码前缀：`1_004_XXX_XXX`

| 错误码 | 说明 |
|--------|------|
| 1_004_001_000 | 用户不存在 |
| 1_004_001_003 | 用户积分余额不足 |
| 1_004_003_000 | 登录失败，账号密码不正确 |
| 1_004_006_000 | 用户标签不存在 |
| 1_004_008_000 | 用户积分记录业务类型不支持 |
| 1_004_010_000 | 今日已签到，请勿重复签到 |
| 1_004_011_000 | 用户等级不存在 |

## 9. 详细文档链接

- [api-auth.md](api-auth.md) - 会员认证（注册、登录、登出、社交登录）
- [api-user.md](api-user.md) - 会员用户管理
- [api-level.md](api-level.md) - 会员等级体系
- [api-point.md](api-point.md) - 积分系统
- [api-signin.md](api-signin.md) - 签到系统
- [api-address.md](api-address.md) - 收货地址管理
- [api-tag-group.md](api-tag-group.md) - 标签与分组管理
- [data-model.md](data-model.md) - 数据模型详细设计
- [pitfalls.md](pitfalls.md) - 常见陷阱与注意事项
