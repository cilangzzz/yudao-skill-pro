# 会员模块 (member)

> 会员中心：C 端用户体系，提供会员注册登录、资料、收件地址、等级经验、积分签到、标签分组，是商城的用户主数据源。

## 模块概述

- **模块路径**: yudao-module-member
- **业务定位**: 承载平台 C 端会员的完整生命周期：App 端手机验证码/微信社交登录自动注册会员，管理端维护会员资料、等级、积分、标签、分组；同时以积分/等级/地址等形式向商城交易、促销模块提供用户能力支撑。
- **技术栈**: Spring Boot 2.7.18（JDK8） / MyBatis-Plus / Swagger v3（springdoc） / Spring Security + @PreAuthorize 权限 / Spring 事件（用户创建消息） / Redis

## 设计原则

| 原则 | 说明 |
|-----|------|
| 双端 API 分离 | controller/admin 管理端与 controller/app 用户端独立成包，App 端有自己的认证体系（手机验证码、微信小程序/公众号登录） |
| 多租户 | 会员主表 MemberUserDO 继承 TenantBaseDO，会员数据按 tenantId 隔离；其余配置/记录类表继承 BaseDO |
| 变更留痕 | 等级、经验、积分每次变动都写流水表（member_level_record / member_experience_record / member_point_record），正负数区分增减 |
| 事务后事件 | 创建会员在事务提交后（TransactionSynchronization.afterCommit）发布 MemberUserCreateMessage（Spring 事件），下游模块（如促销注册发券）订阅响应 |
| 服务间解耦 | 对 mall 系列模块只通过 api 包（MemberUserApi 等 5 个 Api + RespDTO）暴露，不泄露 DO 内部结构 |
| 经验驱动等级 | 经验变动统一走 MemberLevelService#addExperience 入口，自动计算升级（calculateNewLevel）并写等级变更记录 |

## 核心功能点

| 功能域 | 说明 | 关键实体 |
|-------|------|---------|
| 会员用户 | 会员资料管理、分页查询、调整等级/积分；App 端注册登录、修改手机/密码 | MemberUserDO |
| 收件地址 | 查询用户收件地址列表（供交易模块下单使用） | MemberAddressDO |
| 会员配置 | 积分抵扣开关、抵扣单价/上限、1 元赠送积分等全局配置 | MemberConfigDO |
| 用户分组 | 会员分组维护（启用状态），用于营销圈选 | MemberGroupDO |
| 会员等级 | 等级配置（经验门槛、折扣）、等级变更记录、经验变动记录 | MemberLevelDO、MemberLevelRecordDO、MemberExperienceRecordDO |
| 积分 | 积分变动流水查询，提供 MemberPointApi 供下单抵扣/奖励 | MemberPointRecordDO |
| 签到 | 签到规则（第 x 天奖励积分/经验）配置、签到记录查询 | MemberSignInConfigDO、MemberSignInRecordDO |
| 会员标签 | 会员标签维护，标签 ID 列表挂在会员上 | MemberTagDO |

## API 接口索引

### 会员用户 (MemberUserController)

前缀：`/member/user`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/user/update | PUT | 更新会员用户 | member:user:update |
| /member/user/update-level | PUT | 更新会员用户等级 | member:user:update-level |
| /member/user/update-point | PUT | 更新会员用户积分 | member:user:update-point |
| /member/user/get | GET | 获得会员用户 | member:user:query |
| /member/user/page | GET | 获得会员用户分页 | member:user:query |

### 用户收件地址 (AddressController)

前缀：`/member/address`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/address/list | GET | 获得用户收件地址列表（按 userId） | member:user:query |

### 会员设置 (MemberConfigController)

前缀：`/member/config`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/config/save | PUT | 保存会员配置 | member:config:save |
| /member/config/get | GET | 获得会员配置 | member:config:query |

### 用户分组 (MemberGroupController)

前缀：`/member/group`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/group/create | POST | 创建用户分组 | member:group:create |
| /member/group/update | PUT | 更新用户分组 | member:group:update |
| /member/group/delete | DELETE | 删除用户分组 | member:group:delete |
| /member/group/get | GET | 获得用户分组 | member:group:query |
| /member/group/list-all-simple | GET | 获取会员分组精简信息列表（下拉选项） | 已认证（无 @PreAuthorize） |
| /member/group/page | GET | 获得用户分组分页 | member:group:query |

### 会员等级 (MemberLevelController)

前缀：`/member/level`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/level/create | POST | 创建会员等级 | member:level:create |
| /member/level/update | PUT | 更新会员等级 | member:level:update |
| /member/level/delete | DELETE | 删除会员等级 | member:level:delete |
| /member/level/get | GET | 获得会员等级 | member:level:query |
| /member/level/list-all-simple | GET | 获取会员等级精简信息列表（下拉选项） | 已认证（无 @PreAuthorize） |
| /member/level/list | GET | 获得会员等级列表 | member:level:query |

### 会员等级记录 (MemberLevelRecordController)

前缀：`/member/level-record`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/level-record/get | GET | 获得会员等级记录 | member:level-record:query |
| /member/level-record/page | GET | 获得会员等级记录分页 | member:level-record:query |

### 会员经验记录 (MemberExperienceRecordController)

前缀：`/member/experience-record`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/experience-record/get | GET | 获得会员经验记录 | member:experience-record:query |
| /member/experience-record/page | GET | 获得会员经验记录分页 | member:experience-record:query |

### 积分记录 (MemberPointRecordController)

前缀：`/member/point/record`（类上 @Tag 误写为"签到记录"，实际是积分记录）

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/point/record/page | GET | 获得用户积分记录分页 | point:record:query |

### 签到规则 (MemberSignInConfigController)

前缀：`/member/sign-in/config`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/sign-in/config/create | POST | 创建签到规则 | point:sign-in-config:create |
| /member/sign-in/config/update | PUT | 更新签到规则 | point:sign-in-config:update |
| /member/sign-in/config/delete | DELETE | 删除签到规则 | point:sign-in-config:delete |
| /member/sign-in/config/get | GET | 获得签到规则 | point:sign-in-config:query |
| /member/sign-in/config/list | GET | 获得签到规则列表 | point:sign-in-config:query |

### 签到记录 (MemberSignInRecordController)

前缀：`/member/sign-in/record`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/sign-in/record/page | GET | 获得签到记录分页 | point:sign-in-record:query |

### 会员标签 (MemberTagController)

前缀：`/member/tag`

| 接口路径 | HTTP方法 | 说明 | 权限标识 |
|---------|---------|------|---------|
| /member/tag/create | POST | 创建会员标签 | member:tag:create |
| /member/tag/update | PUT | 更新会员标签 | member:tag:update |
| /member/tag/delete | DELETE | 删除会员标签 | member:tag:delete |
| /member/tag/get | GET | 获得会员标签 | member:tag:query |
| /member/tag/list-all-simple | GET | 获取会员标签精简信息列表（下拉选项） | 已认证（无 @PreAuthorize） |
| /member/tag/list | GET | 获得会员标签列表（按 ids） | member:tag:query |
| /member/tag/page | GET | 获得会员标签分页 | member:tag:query |

## 数据模型

| 表名 | 说明 | 继承基类 | 关键字段 |
|-----|------|---------|---------|
| member_user | 会员用户（mobile 唯一索引） | TenantBaseDO | mobile、password、status、point、tagIds（LongListTypeHandler 逗号分隔）、levelId、experience、groupId、areaId |
| member_address | 用户收件地址 | BaseDO | userId、name、mobile、areaId、detailAddress、defaultStatus |
| member_config | 会员配置 | BaseDO | pointTradeDeductEnable、pointTradeDeductUnitPrice、pointTradeDeductMaxPrice、pointTradeGivePoint |
| member_group | 用户分组 | BaseDO | name、remark、status |
| member_level | 会员等级 | BaseDO | name、level、experience（升级经验）、discountPercent、icon、backgroundUrl、status |
| member_level_record | 会员等级变更记录 | BaseDO | userId、levelId、level、discountPercent、experience（变动经验）、userExperience、description |
| member_experience_record | 会员经验变动记录 | BaseDO | userId、bizType（MemberExperienceBizTypeEnum）、bizId、title、experience、totalExperience |
| member_point_record | 用户积分变动记录 | BaseDO | userId、bizType（MemberPointBizTypeEnum）、bizId、point（正得负耗）、totalPoint |
| member_sign_in_config | 签到规则（第 x 天奖励） | BaseDO | day、point、experience、status |
| member_sign_in_record | 签到记录 | BaseDO | userId、day、point、experience |
| member_tag | 会员标签 | BaseDO | name |

## 依赖关系

- **上游**（本模块依赖）:
  - 业务模块：yudao-module-system（SmsCodeApi、SocialClientApi、SocialUserApi、LoginLogApi、OAuth2TokenCommonApi、SexEnum）、yudao-module-infra
  - framework starter：yudao-spring-boot-starter-biz-tenant、yudao-spring-boot-starter-security、yudao-spring-boot-starter-mybatis、yudao-spring-boot-starter-redis、yudao-spring-boot-starter-mq、yudao-spring-boot-starter-excel、yudao-spring-boot-starter-biz-ip（Area 地区）
- **下游**（依赖本模块）:
  - yudao-module-mall：yudao-module-product、yudao-module-trade（MemberUserApi/MemberAddressApi/MemberConfigApi/MemberLevelApi/MemberPointApi）、yudao-module-promotion、yudao-module-statistics
  - yudao-server（服务装配）

## 对外暴露的 API

| API接口 | 方法 | 消费方 |
|---------|------|-------|
| MemberUserApi | getUser、getUserList 等 | mall-trade、mall-promotion、mall-statistics |
| MemberAddressApi | getAddress（下单收货地址） | mall-trade |
| MemberConfigApi | getMemberConfig（积分抵扣/赠送规则） | mall-trade |
| MemberLevelApi | getMemberLevel（等级折扣） | mall-trade |
| MemberPointApi | reducePoint / addPoint（下单抵扣与奖励） | mall-trade |
| MemberUserCreateMessage（Spring 事件） | 用户注册事件 | mall-promotion（CouponTakeByRegisterConsumer 注册发券） |

## 详细文档

- [api-user.md](api-user.md) - 会员用户
- [api-address.md](api-address.md) - 收件地址
- [api-config.md](api-config.md) - 会员配置
- [api-group.md](api-group.md) - 用户分组
- [api-level.md](api-level.md) - 会员等级与经验
- [api-point.md](api-point.md) - 积分记录
- [api-signin.md](api-signin.md) - 签到
- [api-tag.md](api-tag.md) - 会员标签
- [data-model.md](data-model.md) - 数据模型详情
- [code-patterns.md](code-patterns.md) - 代码模式与扩展指南
- [pitfalls.md](pitfalls.md) - 注意事项与已知坑点
