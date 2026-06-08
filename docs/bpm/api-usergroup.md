# API - 审批用户组管理 (BpmUserGroupController)

> 路径前缀：`/bpm/user-group`
> 对应服务：基于 `BpmUserGroupMapper` 直接操作

## 概述

审批用户组是一组用户的集合，用于审批人策略中的"用户组分配"方式。通过用户组可以将审批任务分配给一组预定义的用户。

用户组数据存储在 `bpm_user_group` 表中。

---

## 接口列表

### 1. 创建用户组

- **接口：** `POST /bpm/user-group/create`
- **权限：** `bpm:user-group:create`

**请求参数（BpmUserGroupCreateReqVO）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 用户组名称 |
| description | String | 否 | 用户组描述 |
| status | Integer | 是 | 状态 |
| userIds | Set\<Long\> | 是 | 成员用户编号列表 |

**返回：** `CommonResult<Long>` -- 用户组编号

---

### 2. 修改用户组

- **接口：** `PUT /bpm/user-group/update`
- **权限：** `bpm:user-group:update`

---

### 3. 删除用户组

- **接口：** `DELETE /bpm/user-group/delete`
- **权限：** `bpm:user-group:delete`
- **说明：** 删除用户组。已在审批人策略中引用的用户组删除后会影响后续任务分配。

---

### 4. 获取用户组详情

- **接口：** `GET /bpm/user-group/get`
- **权限：** `bpm:user-group:query`

**返回（BpmUserGroupRespVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户组编号 |
| name | String | 用户组名称 |
| description | String | 用户组描述 |
| status | Integer | 状态 |
| userIds | Set\<Long\> | 成员用户编号列表 |

---

### 5. 分页查询用户组

- **接口：** `GET /bpm/user-group/page`
- **权限：** `bpm:user-group:query`

---

### 6. 获取用户组简单列表

- **接口：** `GET /bpm/user-group/list-all-simple`
- **权限：** 无（登录用户）
- **说明：** 获取所有启用状态的用户组简要列表，用于审批人策略配置时的下拉选择

---

## 设计要点

1. **与审批人策略的关系：** 当审批人策略选择"用户组"时，需要指定一个用户组编号，引擎会将任务分配给该组内所有用户
2. **用户组 vs 角色：** 用户组是 BPM 模块自有的概念，适用于审批场景的灵活分组；角色是 system 模块的权限概念
3. **userIds 存储格式：** 使用 `Set<Long>` 类型存储成员用户编号，数据库中以 JSON 数组格式存储
