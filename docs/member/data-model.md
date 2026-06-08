# Member 模块数据模型

> 会员模块的完整数据表设计、实体关系和字段说明。

## 1. 实体继承体系

```
BaseDO (通用基础字段)
  ├── MemberLevelDO
  ├── MemberPointRecordDO
  ├── MemberExperienceRecordDO
  ├── MemberLevelRecordDO
  ├── MemberSignInConfigDO
  ├── MemberSignInRecordDO
  ├── MemberTagDO
  ├── MemberGroupDO
  ├── MemberAddressDO
  └── MemberConfigDO

TenantBaseDO (多租户基础字段)
  └── MemberUserDO
```

**说明：** 会员核心表（MemberUserDO）继承 TenantBaseDO 支持多租户隔离，其他表继承 BaseDO。

## 2. ER 关系图

```
                    ┌──────────────┐
                    │ member_level │
                    │  (等级表)     │
                    └──────┬───────┘
                           │ N:1 (level_id)
                           │
┌──────────────┐    ┌──────┴───────┐    ┌──────────────┐
│ member_group │───→│ member_user  │←───│  member_tag  │
│  (分组表)     │N:1 │  (用户表)     │N:N │  (标签表)     │
└──────────────┘    └──────┬───────┘    └──────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │member_point│  │member_exp  │  │member_level│
   │_record     │  │_record     │  │_record     │
   │(积分记录)   │  │(经验记录)   │  │(等级记录)   │
   └────────────┘  └────────────┘  └────────────┘

            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │member_sign │  │member_sign │  │member_addr │
   │_in_config  │  │_in_record  │  │ess         │
   │(签到配置)   │  │(签到记录)   │  │(收货地址)   │
   └────────────┘  └────────────┘  └────────────┘

                    ┌──────────────┐
                    │member_config │
                    │  (会员配置)   │
                    └──────────────┘
```

## 3. 表关系明细

| 关系 | 类型 | 外键 | 说明 |
|------|------|------|------|
| member_user -> member_level | N:1 | level_id | 用户所属等级 |
| member_user -> member_group | N:1 | group_id | 用户所属分组 |
| member_user -> member_tag | N:N | tag_ids (JSON) | 用户标签列表 |
| member_point_record -> member_user | N:1 | user_id | 积分记录归属 |
| member_experience_record -> member_user | N:1 | user_id | 经验记录归属 |
| member_level_record -> member_user | N:1 | user_id | 等级记录归属 |
| member_level_record -> member_level | N:1 | level_id | 等级记录关联等级 |
| member_sign_in_record -> member_user | N:1 | user_id | 签到记录归属 |
| member_address -> member_user | N:1 | user_id | 地址归属 |

## 4. 表结构详细说明

### 4.1 member_user - 会员用户表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:----:|--------|------|
| id | Long | Y | 自增 | 用户 ID（主键） |
| mobile | String | Y | - | 手机号（唯一索引） |
| password | String | N | - | 加密密码（BCrypt） |
| status | Integer | Y | 0 | 状态：0-启用，1-禁用 |
| register_ip | String | N | - | 注册 IP |
| register_terminal | Integer | N | - | 注册终端 |
| login_ip | String | N | - | 最后登录 IP |
| login_date | LocalDateTime | N | - | 最后登录时间 |
| nickname | String | N | - | 昵称 |
| avatar | String | N | - | 头像 URL |
| name | String | N | - | 真实姓名 |
| sex | Integer | N | - | 性别 |
| birthday | LocalDateTime | N | - | 生日 |
| area_id | Integer | N | - | 地区 ID |
| mark | String | N | - | 用户备注 |
| point | Integer | N | 0 | 当前积分（冗余字段） |
| tag_ids | List\<Long\> | N | [] | 标签 ID 列表（JSON 存储） |
| level_id | Long | N | - | 等级 ID |
| experience | Integer | N | 0 | 当前经验（冗余字段） |
| group_id | Long | N | - | 分组 ID |

**索引：**

| 名称 | 列 | 类型 |
|------|-----|------|
| uk_mobile | mobile | 唯一索引 |

### 4.2 member_level - 会员等级表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 等级 ID |
| name | String | Y | 等级名称 |
| level | Integer | Y | 等级值（用于排序比较） |
| experience | Integer | Y | 升级所需经验 |
| discount_percent | Integer | Y | 折扣百分比（如 95 表示 95 折） |
| icon | String | N | 等级图标 |
| background_url | String | N | 等级背景图 |
| status | Integer | Y | 状态：0-启用，1-禁用 |

### 4.3 member_point_record - 积分记录表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 记录 ID |
| user_id | Long | Y | 用户 ID |
| biz_id | String | Y | 业务编码（如订单号） |
| biz_type | Integer | Y | 业务类型（枚举） |
| title | String | N | 积分标题 |
| description | String | N | 积分描述 |
| point | Integer | Y | 变动积分（正数增加，负数减少） |
| total_point | Integer | Y | 变动后积分余额 |

### 4.4 member_experience_record - 经验记录表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 记录 ID |
| user_id | Long | Y | 用户 ID |
| biz_type | Integer | Y | 业务类型（枚举） |
| biz_id | String | N | 业务编号 |
| title | String | N | 标题 |
| description | String | N | 描述 |
| experience | Integer | Y | 变动经验（正负） |
| total_experience | Integer | Y | 变动后经验 |

### 4.5 member_level_record - 等级变更记录表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 记录 ID |
| user_id | Long | Y | 用户 ID |
| level_id | Long | Y | 等级 ID |
| level | Integer | Y | 等级值（冗余） |
| discount_percent | Integer | Y | 折扣（冗余） |
| experience | Integer | Y | 升级经验（冗余） |
| user_experience | Integer | Y | 用户变更后经验 |
| remark | String | N | 备注 |
| description | String | N | 描述 |

### 4.6 member_sign_in_config - 签到配置表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 配置 ID |
| day | Integer | Y | 签到第 N 天 |
| point | Integer | Y | 奖励积分 |
| experience | Integer | Y | 奖励经验 |
| status | Integer | Y | 状态 |

### 4.7 member_sign_in_record - 签到记录表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 记录 ID |
| user_id | Long | Y | 用户 ID |
| day | Integer | Y | 第几天签到 |
| point | Integer | Y | 签到获得积分 |
| experience | Integer | Y | 签到获得经验 |

### 4.8 member_tag - 会员标签表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 标签 ID |
| name | String | Y | 标签名称 |

### 4.9 member_group - 会员分组表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 分组 ID |
| name | String | Y | 分组名称 |
| remark | String | N | 备注 |
| status | Integer | Y | 状态 |

### 4.10 member_address - 收货地址表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 地址 ID |
| user_id | Long | Y | 用户 ID |
| name | String | Y | 收件人名称 |
| mobile | String | Y | 手机号 |
| area_id | Long | Y | 地区 ID |
| detail_address | String | Y | 详细地址 |
| default_status | Boolean | Y | 是否默认地址 |

### 4.11 member_config - 会员配置表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | Long | Y | 配置 ID |
| point_trade_deduct_enable | Boolean | Y | 积分抵扣开关 |
| point_trade_deduct_unit_price | Integer | Y | 积分抵扣单位（1 积分 = 多少分钱） |
| point_trade_deduct_max_price | Integer | Y | 积分抵扣上限（分） |
| point_trade_give_point | Integer | Y | 1 元赠送积分 |

## 5. 冗余字段设计说明

MemberUserDO 中存在以下冗余字段：

| 字段 | 数据来源 | 更新时机 |
|------|----------|----------|
| point | member_point_record 汇总 | 每次积分变更时实时更新 |
| experience | member_experience_record 汇总 | 每次经验变更时实时更新 |
| level_id | 等级计算结果 | 经验变更后自动计算更新 |
| tag_ids | 标签关联关系 | 标签变更时更新 |

**设计理由：** 冗余字段避免了频繁的关联查询，提高了读取性能。写入时通过事务保证一致性。
