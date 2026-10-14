# 数据模型详情

> member 模块的核心数据模型，包括 DO、DTO、VO 及其之间的关系。会员模块共 11 张表，围绕「会员用户 member_user」这一核心聚合展开：账户资料、收件地址、等级经验、积分签到、标签分组均直接或间接挂接在用户上。

---

## 1. 实体继承体系

```
cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO        （框架通用基类）
├── creator        String          创建者（用户编号，字符串预留扩展性，INSERT 时自动填充）
├── createTime     LocalDateTime   创建时间（INSERT 时自动填充）
├── updater        String          更新者（INSERT/UPDATE 时自动填充）
├── updateTime     LocalDateTime   最后更新时间（INSERT/UPDATE 时自动填充）
└── deleted        Boolean         逻辑删除标记（@TableLogic，查询自动过滤）
    │
    ├── cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO   （多租户基类）
    │   └── tenantId  Long  租户编号（租户隔离，MP 租户插件自动拼接入查询条件）
    │       └── MemberUserDO               会员用户（member_user）
    │
    └── member 模块其余 10 个 DO（无租户字段，平台级数据）
        ├── MemberAddressDO                收件地址（member_address）
        ├── MemberConfigDO                 会员配置（member_config）
        ├── MemberGroupDO                  用户分组（member_group）
        ├── MemberLevelDO                  会员等级（member_level）
        ├── MemberLevelRecordDO            等级变更记录（member_level_record）
        ├── MemberExperienceRecordDO       经验变更记录（member_experience_record）
        ├── MemberPointRecordDO            积分变更记录（member_point_record）
        ├── MemberSignInConfigDO           签到规则（member_sign_in_config）
        ├── MemberSignInRecordDO           签到记录（member_sign_in_record）
        └── MemberTagDO                    会员标签（member_tag）
```

**使用规则**：

| 场景 | 基类 | member 模块实例 |
|-----|------|----------------|
| C 端用户主数据（需租户隔离，与 system 租户体系对齐） | `TenantBaseDO` | 仅 `MemberUserDO`（member_user）继承，11 个 DO 中唯一的多租户表 |
| 平台级配置（全局一行，如积分抵扣规则） | `BaseDO` | `MemberConfigDO` |
| 用户从属数据（地址、标签、分组，业务上归属 C 端用户而非租户后台） | `BaseDO` | `MemberAddressDO`、`MemberTagDO`、`MemberGroupDO` |
| 等级/经验/积分/签到流水记录（只增不改的日志型数据） | `BaseDO` | `MemberLevelRecordDO`、`MemberExperienceRecordDO`、`MemberPointRecordDO`、`MemberSignInRecordDO` |
| 等级与签到规则配置 | `BaseDO` | `MemberLevelDO`、`MemberSignInConfigDO` |

---

## 2. 核心 DO 实体

按业务聚合分为四组：用户聚合、等级与经验聚合、积分与签到聚合、标签与分组聚合。共 11 个 DO，全部详细展开。

### 2.1 用户聚合

#### MemberUserDO (member_user)

会员用户表，模块的核心主数据，被商城 trade/promotion/product 等模块通过 `MemberUserApi` 引用。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 用户编号（主键，@TableId） |
| mobile | String | mobile | 手机号（登录账号） |
| email | String | email | 邮箱 |
| password | String | password | 加密后的密码（BCryptPasswordEncoder，无需单独盐值） |
| status | Integer | status | 帐号状态，枚举 CommonStatusEnum |
| registerIp | String | register_ip | 注册 IP |
| registerTerminal | Integer | register_terminal | 注册终端，枚举 TerminalEnum |
| loginIp | String | login_ip | 最后登录 IP |
| loginDate | LocalDateTime | login_date | 最后登录时间 |
| nickname | String | nickname | 用户昵称 |
| avatar | String | avatar | 用户头像 |
| name | String | name | 真实名字 |
| sex | Integer | sex | 性别，枚举 SexEnum（system 模块） |
| birthday | LocalDateTime | birthday | 出生日期 |
| areaId | Integer | area_id | 所在地，关联框架 `Area#getId()`（地区库） |
| mark | String | mark | 用户备注（管理员备注） |
| point | Integer | point | 当前积分（冗余，与 member_point_record 的 totalPoint 同步） |
| tagIds | List&lt;Long&gt; | tag_ids | 会员标签列表，`LongListTypeHandler` 以逗号分隔存储，配合 `autoResultMap = true` |
| levelId | Long | level_id | 会员等级编号，关联 MemberLevelDO#getId() |
| experience | Integer | experience | 当前会员经验 |
| groupId | Long | group_id | 用户分组编号，关联 MemberGroupDO#getId() |

**继承**: TenantBaseDO（BaseDO + tenantId，本模块唯一多租户表）
**索引**: `uk_mobile`（mobile 字段唯一索引，源码 Javadoc 明确标注）；email 的唯一性由 Service 层 `validateEmailUnique` 应用级校验保证

#### MemberAddressDO (member_address)

用户收件地址表，一个用户可有多条地址，其中一条可为默认地址；被 mall-trade 下单流程通过 `MemberAddressApi` 消费。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 用户编号，关联 MemberUserDO#getId() |
| name | String | name | 收件人名称 |
| mobile | String | mobile | 收件人手机号 |
| areaId | Long | area_id | 地区编号（省市区） |
| detailAddress | String | detail_address | 收件详细地址 |
| defaultStatus | Boolean | default_status | 是否默认收件地址（true 为默认） |

**继承**: BaseDO
**索引**: 源码未声明额外索引；常规查询路径为 `selectListByUserIdAndDefaultStatus`（按 user_id 过滤）

#### MemberConfigDO (member_config)

会员全局配置表（单行记录），定义积分在交易场景的抵扣与赠送规则；被 mall-trade 通过 `MemberConfigApi` 消费。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 自增主键 |
| pointTradeDeductEnable | Boolean | point_trade_deduct_enable | 积分抵扣开关 |
| pointTradeDeductUnitPrice | Integer | point_trade_deduct_unit_price | 积分抵扣比例，单位：分（1 积分抵扣多少分钱） |
| pointTradeDeductMaxPrice | Integer | point_trade_deduct_max_price | 单笔订单积分抵扣上限（分） |
| pointTradeGivePoint | Integer | point_trade_give_point | 每消费 1 元赠送多少积分 |

**继承**: BaseDO
**索引**: 全局单行配置表，`@TableName(autoResultMap = true)`，无业务索引

### 2.2 等级与经验聚合

等级变更统一入口为 `MemberLevelService#addExperience`：写经验记录（member_experience_record）→ 自动 `calculateNewLevel` 判断升级 → 若升级则同步更新 member_user 的 levelId/experience 并写等级记录（member_level_record）。

#### MemberLevelDO (member_level)

会员等级配置表，定义等级阶梯与权益；被商城模块通过 `MemberLevelApi` 消费（如按等级折扣）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| name | String | name | 等级名称 |
| level | Integer | level | 等级值（数字越大等级越高） |
| experience | Integer | experience | 升级所需经验值 |
| discountPercent | Integer | discount_percent | 享受折扣（百分比） |
| icon | String | icon | 等级图标 |
| backgroundUrl | String | background_url | 等级背景图 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 源码未声明数据库唯一索引；name 与 level 的唯一性由 Service 层 `validateNameUnique` / `validateLevelUnique` 应用级校验保证

#### MemberLevelRecordDO (member_level_record)

会员等级变更日志表，用户每次等级发生变更（升级/降级/管理员调整）时记录一条。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 用户编号，关联 MemberUserDO#getId() |
| levelId | Long | level_id | 等级编号，关联 MemberLevelDO#getId() |
| level | Integer | level | 变更后的会员等级值（冗余 MemberLevelDO#level，避免等级配置后续修改影响历史记录） |
| discountPercent | Integer | discount_percent | 该等级对应的享受折扣（同样冗余快照） |
| experience | Integer | experience | 该等级的升级经验（冗余快照） |
| userExperience | Integer | user_experience | 变更时会员的累计经验 |
| remark | String | remark | 备注 |
| description | String | description | 变更描述 |

**继承**: BaseDO
**索引**: 源码未声明额外索引；查询路径为按 user_id 查询变更历史

#### MemberExperienceRecordDO (member_experience_record)

会员经验变更流水表，记录每一次经验增减（签到、下单、管理员调整等）。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 用户编号，关联 MemberUserDO#getId() |
| bizType | Integer | biz_type | 业务类型，枚举 MemberExperienceBizTypeEnum（管理员调整 0 / 邀新奖励 1 / 签到奖励 4 / 抽奖奖励 5 / 下单奖励 11 / 下单奖励取消 12、13） |
| bizId | String | biz_id | 业务编号（触发本次变更的业务单据号） |
| title | String | title | 变更标题 |
| description | String | description | 变更描述 |
| experience | Integer | experience | 本次变更经验值（正负号表示增减） |
| totalExperience | Integer | total_experience | 变更后会员的累计经验（冗余 member_user.experience 快照） |

**继承**: BaseDO
**索引**: 源码未声明额外索引；查询路径为按 user_id 查询经验流水

### 2.3 积分与签到聚合

积分变更通过 `MemberPointRecordService` 落库，同时回写 member_user.point。业务类型枚举 `MemberPointBizTypeEnum` 位于 `enums/point` 子包（注意与经验的 `MemberExperienceBizTypeEnum` 路径不同）。签到记录由 App 端发起，奖励值来自签到规则配置。

#### MemberPointRecordDO (member_point_record)

用户积分变更流水表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 自增主键 |
| userId | Long | user_id | 用户编号，对应 MemberUserDO#getId() |
| bizId | String | biz_id | 业务编码（如订单号） |
| bizType | Integer | biz_type | 业务类型，枚举 MemberPointBizTypeEnum（签到 1 / 管理员修改 2 / 订单积分抵扣 11 及其取消 12、13 / 订单积分奖励 21 及其取消 22、23） |
| title | String | title | 积分标题 |
| description | String | description | 积分描述 |
| point | Integer | point | 变动积分：正数获得、负数消耗 |
| totalPoint | Integer | total_point | 变动后的积分（冗余 member_user.point 快照） |

**继承**: BaseDO
**索引**: 源码未声明额外索引；查询路径为按 user_id 分页查询积分流水

#### MemberSignInConfigDO (member_sign_in_config)

签到规则配置表，按「连续签到第 x 天」配置奖励。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 规则自增主键 |
| day | Integer | day | 签到第 x 天 |
| point | Integer | point | 该天签到的奖励积分 |
| experience | Integer | experience | 该天签到的奖励经验 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 源码未声明额外索引；签到时按 day 匹配对应规则，无规则则走默认奖励

#### MemberSignInRecordDO (member_sign_in_record)

签到记录表，用户每次签到写一条。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| userId | Long | user_id | 签到用户编号，关联 MemberUserDO#getId() |
| day | Integer | day | 第几天签到（连续签到的天数序号） |
| point | Integer | point | 本次签到获得的积分 |
| experience | Integer | experience | 本次签到获得的经验 |

**继承**: BaseDO
**索引**: 源码未声明额外索引；查询路径为按 user_id 查询最近签到（计算连续签到天数、判断当日是否已签）

### 2.4 标签与分组聚合

标签与分组是运营侧对用户的两套标记体系：标签多选（member_user.tagIds 逗号分隔存储），分组单选（member_user.groupId 外键）。

#### MemberTagDO (member_tag)

会员标签表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| name | String | name | 标签名称 |

**继承**: BaseDO
**索引**: 源码未声明数据库唯一索引；name 唯一性由 Service 层 `validateTagNameUnique` 应用级校验保证

#### MemberGroupDO (member_group)

用户分组表。

| 字段 | 类型 | 数据库列 | 说明 |
|-----|------|---------|-----|
| id | Long | id | 编号（主键） |
| name | String | name | 分组名称 |
| remark | String | remark | 分组备注 |
| status | Integer | status | 状态，枚举 CommonStatusEnum |

**继承**: BaseDO
**索引**: 源码未声明额外索引

---

## 3. 实体关系

核心外键/从属关系（均为逻辑外键，无数据库级 FK 约束）：

```
                    ┌──────────────────┐
                    │   member_user    │  ← 会员主数据（TenantBaseDO）
                    └───────┬──────────┘
        ┌───────────────┬───┴────────┬──────────────┬───────────────┐
        │               │            │              │               │
   user_id         user_id      user_id        user_id        tag_ids(逗号分隔)
        │               │            │              │               │
┌───────▼──────┐ ┌──────▼───────┐ ┌──▼───────────┐ ┌▼──────────────┐ │
│member_address│ │member_level_ │ │member_       │ │member_sign_in_│ │
│  收件地址 1:N │ │record 等级记录│ │experience_   │ │record 签到记录 │ │
└──────────────┘ └───┬──────────┘ │record 经验记录│ └───────────────┘ │
                     │ level_id   └──────────────┘                   │
                     │     ┌─────────────────────────────────────────┘
                     ▼     │
             ┌────────────┐│  group_id
             │member_level││     ┌────────────┐
             │  等级配置   ││     │member_group│
             └────────────┘│     └────────────┘
                           │            ▲
                     tag_ids│            │ id
                           ▼            │
                    ┌─────────────┐     │
                    │ member_tag  │     │
                    └─────────────┘     │

独立配置表（不挂用户）：
  member_config           —— 积分抵扣/赠送全局规则（单行）
  member_sign_in_config   —— 签到规则（day → point/experience），签到时被 member_sign_in_record 按天匹配
```

**关系要点**：

- `member_user` 是模块中心表，其余 9 张含 `user_id` 的表均通过 `user_id` 逻辑关联（member_address、member_level_record、member_experience_record、member_point_record、member_sign_in_record）。
- `member_user.levelId → member_level.id`、`member_user.groupId → member_group.id` 为单值逻辑外键；等级变更时 member_level_record 会额外冗余 level/discountPercent/experience 三个字段作历史快照。
- `member_user.tagIds → member_tag.id` 为多值关联，不建中间表，而是用 `LongListTypeHandler` 在 tag_ids 列以逗号分隔存储 `List<Long>`，查询时通过 `FIND_IN_SET(tag_ids, ?)` 匹配（见 MemberUserMapper）。
- `member_config` 与 `member_sign_in_config` 是纯配置表，不直接引用用户。
- 跨模块引用：mall-trade 消费 `MemberAddressApi`/`MemberConfigApi`/`MemberPointApi`（下单、积分抵扣）、mall-promotion 消费 `MemberUserApi`（注册发券，监听 member 模块事务提交后发布的 `MemberUserCreateMessage` Spring 事件）、mall-statistics/product 消费 `MemberUserApi`/`MemberLevelApi`。

---

## 4. 全部数据表清单

| 表名 | DO | 说明 |
|-----|-----|-----|
| member_user | MemberUserDO | 会员用户（唯一多租户表，账号 + 资料 + 积分/经验/等级/分组/标签冗余字段） |
| member_address | MemberAddressDO | 用户收件地址 |
| member_config | MemberConfigDO | 会员全局配置（积分抵扣与赠送规则，单行） |
| member_group | MemberGroupDO | 用户分组 |
| member_level | MemberLevelDO | 会员等级配置（等级阶梯与折扣权益） |
| member_level_record | MemberLevelRecordDO | 会员等级变更记录（含等级快照冗余） |
| member_experience_record | MemberExperienceRecordDO | 会员经验变更流水 |
| member_point_record | MemberPointRecordDO | 用户积分变更流水 |
| member_sign_in_config | MemberSignInConfigDO | 签到规则（按天配置积分/经验奖励） |
| member_sign_in_record | MemberSignInRecordDO | 签到记录 |
| member_tag | MemberTagDO | 会员标签 |
