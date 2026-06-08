# 会员用户管理 API

> 会员用户的增删改查、状态管理、积分/经验调整等管理后台接口。

## 1. 概述

| 项目 | 说明 |
|------|------|
| 管理后台 Controller | `admin/user/MemberUserController` |
| C端 Controller | `app/user/AppMemberUserController` |
| Service | `MemberUserService` |
| 路径前缀 | `/member/user`（管理后台）/ `/member/app/user`（C端） |
| 权限前缀 | `member:user:*` |

## 2. 管理后台接口

### 2.1 查询会员用户列表

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:query` |
| 说明 | 分页查询会员用户，支持按手机号、昵称、等级等条件筛选 |

### 2.2 查询会员用户详情

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:query` |
| 说明 | 根据用户 ID 获取完整用户信息 |

### 2.3 更新会员用户积分

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:update-point` |
| 说明 | 管理员手动调整用户积分（增加或减少） |

**业务流程：**

1. 调用 `MemberPointRecordService.createPointRecord`
2. 业务类型为 `MemberPointBizTypeEnum.ADMIN`
3. 事务内完成积分变更和记录写入

**代码示例：**

```java
@PutMapping("/update-point")
@Operation(summary = "更新会员用户积分")
@PreAuthorize("@ss.hasPermission('member:user:update-point')")
public CommonResult<Boolean> updateUserPoint(
        @Valid @RequestBody MemberUserUpdatePointReqVO updateReqVO) {
    memberPointRecordService.createPointRecord(
        updateReqVO.getId(), updateReqVO.getPoint(),
        MemberPointBizTypeEnum.ADMIN, String.valueOf(getLoginUserId()));
    return success(true);
}
```

### 2.4 更新会员用户经验

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:update-experience` |
| 说明 | 管理员手动调整用户经验，会自动触发等级计算 |

**业务流程：**

1. 调用 `MemberLevelApi.addExperience` / `reduceExperience`
2. 业务类型为 `MemberExperienceBizTypeEnum.ADMIN`
3. 系统自动判断是否需要升级/降级

### 2.5 更新会员用户信息

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:update` |
| 说明 | 更新用户基本信息（昵称、头像、备注等） |

### 2.6 更新会员用户状态

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:update` |
| 说明 | 启用/禁用会员用户 |

### 2.7 修改会员用户等级

| 项目 | 说明 |
|------|------|
| 权限 | `member:user:update` |
| 说明 | 管理员手动指定用户等级 |

## 3. C端接口

### 3.1 获取当前用户信息

| 项目 | 说明 |
|------|------|
| 说明 | 获取当前登录会员的个人信息 |

### 3.2 修改个人信息

| 项目 | 说明 |
|------|------|
| 说明 | 修改昵称、头像、性别、生日等 |

### 3.3 修改手机号

| 项目 | 说明 |
|------|------|
| 说明 | 需要验证原手机和新手机的短信验证码 |

**依赖：** system 模块 `SmsCodeApi`

### 3.4 实名认证

| 项目 | 说明 |
|------|------|
| 说明 | 填写真实姓名，用于后续业务 |

## 4. 跨模块 API

`MemberUserApi` 为其他模块提供的查询接口：

| 方法 | 说明 | 消费方 |
|------|------|--------|
| getUser(Long id) | 根据 ID 获取用户信息 | pay, mall-trade, mall-promotion |
| getUserList(Collection ids) | 批量获取用户信息 | pay, mall-trade |
| getUserByMobile(String mobile) | 根据手机号获取用户 | mall-trade |
| validateUser(Long id) | 校验用户是否存在且状态正常 | mall-trade, mall-promotion |

## 5. 数据说明

核心实体：`MemberUserDO`

| 关键字段 | 说明 |
|----------|------|
| mobile | 手机号，唯一索引，用作登录凭证 |
| password | BCrypt 加密密码 |
| status | 0-启用，1-禁用 |
| point | 当前积分（冗余字段，实时更新） |
| experience | 当前经验（冗余字段，实时更新） |
| level_id | 当前等级 ID |
| tag_ids | 标签 ID 列表，JSON 数组存储 |
| group_id | 分组 ID |

## 6. 错误码

| 错误码 | 说明 |
|--------|------|
| 1_004_001_000 | 用户不存在 |
| 1_004_001_003 | 用户积分余额不足 |
