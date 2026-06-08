# 群组与群成员接口

## 概述

群组管理是 IM 模块的核心功能之一，提供群组的创建、解散、成员管理、权限控制、审批流程等完整的群聊管理能力。

### 业务定位

- 支持群主/管理员/普通成员三级角色体系
- 群主可转让群主、设置/取消管理员
- 支持入群审批、全员禁言、单人禁言
- 支持消息置顶功能

### 核心实体

| 实体 | 说明 |
|-----|------|
| GroupDO | 群组信息，包含名称、头像、公告、群主、入群审批开关等 |
| GroupMemberDO | 群成员关系，包含角色（OWNER/ADMIN/NORMAL）、禁言到期时间、加入来源 |
| GroupRequestDO | 入群请求，支持用户主动申请和成员邀请两种模式，包含审批流程 |

## 群组接口列表

### 1. 创建群组

- **路径**: `POST /im/group/create`
- **说明**: 创建新群组，创建者自动成为群主
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 是 | 群组名称 |
| avatar | String | 否 | 群组头像 URL |
| memberIds | List<Long> | 否 | 初始成员 ID 列表 |
| notice | String | 否 | 群公告 |

- **响应**: `CommonResult<Long>` - 群组 ID
- **实现逻辑**:
  1. 校验群名称非空
  2. 创建 `im_group` 记录，设置 ownerId 为当前用户
  3. 创建群主的 `im_group_member` 记录（角色为 OWNER）
  4. 为初始成员创建 `im_group_member` 记录（角色为 NORMAL）

### 2. 更新群组信息

- **路径**: `PUT /im/group/update`
- **说明**: 更新群组基本信息（名称、头像、公告等）
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| name | String | 否 | 群组名称 |
| avatar | String | 否 | 群组头像 |
| notice | String | 否 | 群公告 |
| joinApproval | Boolean | 否 | 是否开启入群审批 |

- **响应**: `CommonResult<Boolean>`

### 3. 解散群组

- **路径**: `DELETE /im/group/dissolve`
- **说明**: 解散群组（仅群主可操作）
- **权限**: 需要用户登录（群主）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验当前用户是群主
  2. 删除群组下所有成员记录
  3. 删除群组记录

### 4. 获取群组信息

- **路径**: `GET /im/group/get`
- **说明**: 获取群组详细信息
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |

- **响应**: `CommonResult<GroupDO>`

### 5. 获取群组列表

- **路径**: `GET /im/group/list`
- **说明**: 获取当前用户加入的群组列表
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| - | - | - | 无额外参数 |

- **响应**: `CommonResult<List<GroupDO>>`

## 群成员管理接口

### 6. 邀请成员

- **路径**: `POST /im/group/invite`
- **说明**: 邀请用户加入群组
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberIds | List<Long> | 是 | 被邀请用户 ID 列表 |

- **响应**: `CommonResult<Boolean>`
- **说明**: 根据群组是否开启入群审批，可能直接加入或创建邀请请求

### 7. 退出群组

- **路径**: `DELETE /im/group/quit`
- **说明**: 当前用户退出群组
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |

- **响应**: `CommonResult<Boolean>`
- **限制**: 群主不可退出，需先转让群主或解散群组

### 8. 踢出成员

- **路径**: `DELETE /im/group/kicking`
- **说明**: 将指定成员踢出群组
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberIds | List<Long> | 是 | 被踢出用户 ID 列表 |

- **响应**: `CommonResult<Boolean>`
- **限制**: 管理员不可踢出群主和其他管理员

### 9. 添加管理员

- **路径**: `PUT /im/group/add-admin`
- **说明**: 将群成员提升为管理员
- **权限**: 需要用户登录（群主）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberIds | List<Long> | 是 | 用户 ID 列表 |

- **响应**: `CommonResult<Boolean>`

### 10. 移除管理员

- **路径**: `PUT /im/group/remove-admin`
- **说明**: 将管理员降为普通成员
- **权限**: 需要用户登录（群主）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberIds | List<Long> | 是 | 用户 ID 列表 |

- **响应**: `CommonResult<Boolean>`

### 11. 转让群主

- **路径**: `PUT /im/group/transfer-owner`
- **说明**: 将群主身份转让给其他成员
- **权限**: 需要用户登录（群主）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberId | Long | 是 | 新群主用户 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验当前用户是群主
  2. 校验目标用户是群成员
  3. 更新 `im_group.ownerId` 为新群主
  4. 更新原群主角色为 NORMAL，新群主角色为 OWNER

## 消息管理接口

### 12. 置顶消息

- **路径**: `PUT /im/group/pin-message`
- **说明**: 在群组中置顶指定消息
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| messageId | Long | 是 | 消息 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**: 将消息 ID 追加到 `im_group.pinnedMessageIds` 数组中

### 13. 取消置顶消息

- **路径**: `PUT /im/group/unpin-message`
- **说明**: 取消群组中的消息置顶
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| messageId | Long | 是 | 消息 ID |

- **响应**: `CommonResult<Boolean>`

## 禁言接口

### 14. 全员禁言

- **路径**: `PUT /im/group/mute-all`
- **说明**: 开启/关闭全员禁言
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| muted | Boolean | 是 | 是否开启全员禁言 |

- **响应**: `CommonResult<Boolean>`

### 15. 禁言成员

- **路径**: `PUT /im/group/mute-member`
- **说明**: 禁言指定群成员
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberId | Long | 是 | 被禁言用户 ID |
| muteEndTime | Date | 是 | 禁言结束时间 |

- **响应**: `CommonResult<Boolean>`

### 16. 取消禁言成员

- **路径**: `PUT /im/group/cancel-mute-member`
- **说明**: 取消指定群成员的禁言
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 群组 ID |
| memberId | Long | 是 | 用户 ID |

- **响应**: `CommonResult<Boolean>`

## 群成员查询接口

### 17. 获取群成员信息

- **路径**: `GET /im/group-member/get`
- **说明**: 获取指定群成员信息
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |
| userId | Long | 是 | 用户 ID |

- **响应**: `CommonResult<GroupMemberDO>`

### 18. 获取群成员列表

- **路径**: `GET /im/group-member/list`
- **说明**: 获取群组的全部成员列表
- **权限**: 需要用户登录（群成员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |

- **响应**: `CommonResult<List<GroupMemberDO>>`

### 19. 更新群成员信息

- **路径**: `PUT /im/group-member/update`
- **说明**: 更新群成员的群内昵称等信息
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |
| nickname | String | 否 | 群内昵称 |

- **响应**: `CommonResult<Boolean>`

## 群组请求接口

### 20. 申请入群

- **路径**: `POST /im/group-request/apply`
- **说明**: 用户主动申请加入群组
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |
| applyContent | String | 否 | 申请附言 |

- **响应**: `CommonResult<Long>` - 请求 ID
- **说明**: 如果群组未开启入群审批，直接加入；否则创建审批请求

### 21. 同意入群请求

- **路径**: `PUT /im/group-request/agree`
- **说明**: 同意入群申请/邀请
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 请求 ID |

- **响应**: `CommonResult<Boolean>`
- **实现逻辑**:
  1. 校验请求存在且未处理
  2. 更新请求状态为"已同意"
  3. 创建 `im_group_member` 记录

### 22. 拒绝入群请求

- **路径**: `PUT /im/group-request/refuse`
- **说明**: 拒绝入群申请/邀请
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 请求 ID |

- **响应**: `CommonResult<Boolean>`

### 23. 获取未处理请求列表

- **路径**: `GET /im/group-request/unhandled-list`
- **说明**: 获取当前用户待处理的入群请求
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<GroupRequestDO>>`

### 24. 获取群组请求列表

- **路径**: `GET /im/group-request/list-by-group`
- **说明**: 获取指定群组的入群请求列表
- **权限**: 需要用户登录（群主或管理员）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| groupId | Long | 是 | 群组 ID |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<GroupRequestDO>>`

### 25. 获取单个请求详情

- **路径**: `GET /im/group-request/get`
- **说明**: 获取指定入群请求详情
- **权限**: 需要用户登录
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 请求 ID |

- **响应**: `CommonResult<GroupRequestDO>`

## 关键实现

- **GroupService**: 群组核心服务，管理群组生命周期
- **GroupMemberService**: 群成员服务，管理成员的加入/退出/角色变更
- **GroupRequestService**: 入群请求服务，管理申请和审批流程
- **角色权限校验**: 通过 `GroupMemberDO.role` 字段判断操作权限（OWNER > ADMIN > NORMAL）
- **入群审批开关**: `GroupDO.joinApproval` 控制是否需要审批，关闭时申请直接加入
