# 签到系统 API

> 会员签到相关接口，包含每日签到、签到规则配置、签到记录查询等功能。

## 1. 概述

| 项目 | 说明 |
|------|------|
| 管理后台 Controller | `admin/signin/MemberSignInConfigController` |
| C端 Controller | `app/signin/AppMemberSignInRecordController` |
| Service | `MemberSignInRecordService` / `MemberSignInConfigService` |

## 2. C端接口

### 2.1 每日签到

| 项目 | 说明 |
|------|------|
| 接口 | 每日签到 |
| 说明 | 用户执行签到，获得积分和经验奖励 |

**业务流程：**

1. 校验今日是否已签到（防重复签到）
2. 计算连续签到天数
3. 根据签到配置获取对应天数的奖励
4. 增加积分（调用 `MemberPointRecordService.createPointRecord`，类型为 `SIGN`）
5. 增加经验（调用 `MemberLevelApi.addExperience`，类型为 `SIGN_IN`）
6. 写入签到记录

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 1_004_010_000 | 今日已签到，请勿重复签到 |

### 2.2 查询签到记录

| 项目 | 说明 |
|------|------|
| 接口 | 查询当前用户的签到记录 |
| 说明 | 支持按月查询签到日历 |

### 2.3 查询连续签到天数

| 项目 | 说明 |
|------|------|
| 接口 | 获取当前连续签到天数 |
| 说明 | 用于前端展示签到进度 |

## 3. 管理后台接口

### 3.1 签到规则配置管理

#### 查询签到配置列表

| 项目 | 说明 |
|------|------|
| 权限 | `member:sign-in-config:query` |
| 说明 | 查询所有签到天数的奖励配置 |

#### 创建签到配置

| 项目 | 说明 |
|------|------|
| 权限 | `member:sign-in-config:create` |
| 说明 | 新增签到天数的奖励规则 |

#### 修改签到配置

| 项目 | 说明 |
|------|------|
| 权限 | `member:sign-in-config:update` |
| 说明 | 修改签到奖励规则 |

#### 删除签到配置

| 项目 | 说明 |
|------|------|
| 权限 | `member:sign-in-config:delete` |
| 说明 | 删除签到规则 |

## 4. 签到规则配置

签到规则存储在 `member_sign_in_config` 表中，支持连续签到奖励递增：

### 配置示例

| day | point | experience | 说明 |
|-----|-------|------------|------|
| 1 | 10 | 5 | 第1天签到 |
| 2 | 15 | 8 | 第2天连续签到 |
| 3 | 20 | 10 | 第3天连续签到 |
| 7 | 50 | 30 | 第7天连续签到（大奖） |
| 14 | 100 | 50 | 第14天连续签到 |
| 30 | 200 | 100 | 第30天连续签到 |

### 连续签到规则

- 连续签到天数按自然日计算
- 中断一天则重新从第 1 天开始
- 如果当前天数超过最大配置天数，使用最后一条配置的奖励
- 签到同时奖励积分和经验

## 5. 数据模型

### member_sign_in_config 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 配置 ID |
| day | Integer | 签到第 N 天 |
| point | Integer | 奖励积分 |
| experience | Integer | 奖励经验 |
| status | Integer | 状态（0-启用，1-禁用） |

### member_sign_in_record 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 记录 ID |
| user_id | Long | 用户 ID |
| day | Integer | 第几天签到 |
| point | Integer | 签到获得积分 |
| experience | Integer | 签到获得经验 |

## 6. 关联业务

签到会触发以下业务：

| 业务 | 调用方式 | 说明 |
|------|----------|------|
| 积分增加 | `MemberPointRecordService.createPointRecord` | 业务类型为 `SIGN` |
| 经验增加 | `MemberLevelApi.addExperience` | 业务类型为 `SIGN_IN`，可能触发等级升级 |

## 7. 注意事项

- 签到操作需要防重复提交，使用日期 + 用户 ID 唯一约束
- 签到配置的 day 值必须连续递增
- 修改签到配置不影响已签到的历史记录
- 签到积分和经验的变更在同一事务中完成
