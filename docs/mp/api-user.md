# 粉丝管理 API

> 对应 Controller：`MpUserController` | 路径前缀：`/mp/user`

## 功能说明

管理公众号粉丝信息，包括粉丝同步、信息更新、标签分组、关注/取消关注状态跟踪。

## 数据模型

### MpUserDO

继承 `BaseDO`。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| openid | String | 粉丝标识 OpenId |
| union_id | String | 微信生态唯一标识 |
| subscribe_status | Integer | 关注状态（1 已关注 / 2 取消关注） |
| subscribe_time | LocalDateTime | 关注时间 |
| unsubscribe_time | LocalDateTime | 取消关注时间 |
| nickname | String | 昵称 |
| head_image_url | String | 头像地址 |
| language | String | 语言 |
| country | String | 国家 |
| province | String | 省份 |
| city | String | 城市 |
| remark | String | 备注 |
| tag_ids | List\<Long\> | 标签 ID 数组 |
| account_id | Long | 公众号账号 ID |
| app_id | String | 公众号 AppId（冗余） |

### 索引

- `idx_account_id` - 账号 ID 索引
- `uk_appid_openid` - AppId + OpenId 唯一索引

## 核心服务

### MpUserService

| 方法 | 说明 |
|------|------|
| saveUser | 保存粉丝信息（关注事件触发） |
| updateUser | 更新粉丝信息 |
| getRequiredUser | 获取粉丝详情（不存在则抛异常） |
| 同步粉丝 | 从微信 API 同步粉丝列表 |

## 事件处理

### SubscribeHandler（关注事件）

1. 调用微信 API 获取粉丝信息
2. 保存粉丝信息到数据库
3. 触发关注自动回复

### UnsubscribeHandler（取消关注事件）

1. 更新粉丝关注状态为"取消关注"
2. 记录取消关注时间

## 与其他模块的关系

- 通过 `account_id` 关联 `mp_account`
- 通过 `tag_ids` 关联 `mp_tag`
- `mp_message` 通过 `user_id` 关联粉丝

## 设计要点

- OpenId + AppId 作为唯一标识，同一粉丝在不同公众号下独立存储
- 粉丝信息通过微信 API 实时同步，本地缓存加速查询
- 关注/取消关注通过事件驱动更新状态
