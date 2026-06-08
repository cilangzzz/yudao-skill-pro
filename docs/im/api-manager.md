# 管理后台接口

## 概述

管理后台（Manager）接口为运营人员提供 IM 模块的管理能力，包括频道管理、表情管理、好友管理、群组管理、消息管理、RTC 管理、敏感词管理和统计面板等。所有接口均需要 RBAC 权限控制。

### 业务定位

- 与用户端 Controller 分离，独立的管理后台入口
- 所有接口通过 `@PreAuthorize` 进行 RBAC 权限校验
- 提供全局的 IM 数据查询和管理能力

## 频道管理

### 1. 获取频道分页列表

- **路径**: `GET /im/manager/channel/page`
- **说明**: 分页查询频道列表
- **权限**: `im:channel:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | String | 否 | 频道名称（模糊匹配） |
| status | Integer | 否 | 频道状态 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<ChannelDO>>`

### 2. 创建频道

- **路径**: `POST /im/manager/channel/create`
- **说明**: 创建新频道
- **权限**: `im:channel:create`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| code | String | 是 | 频道编码 |
| name | String | 是 | 频道名称 |
| avatar | String | 否 | 频道头像 |
| sort | Integer | 否 | 排序值 |
| status | Integer | 否 | 频道状态 |

- **响应**: `CommonResult<Long>` - 频道 ID

### 3. 更新频道

- **路径**: `PUT /im/manager/channel/update`
- **权限**: `im:channel:update`

### 4. 删除频道

- **路径**: `DELETE /im/manager/channel/delete`
- **权限**: `im:channel:delete`

### 5. 获取频道详情

- **路径**: `GET /im/manager/channel/get`
- **权限**: `im:channel:query`

## 频道素材管理

### 6. 获取素材分页列表

- **路径**: `GET /im/manager/channel/material/page`
- **说明**: 分页查询频道素材列表
- **权限**: `im:channel:query`

### 7. 创建素材

- **路径**: `POST /im/manager/channel/material/create`
- **权限**: `im:channel:create`

### 8. 更新素材

- **路径**: `PUT /im/manager/channel/material/update`
- **权限**: `im:channel:update`

### 9. 删除素材

- **路径**: `DELETE /im/manager/channel/material/delete`
- **权限**: `im:channel:delete`

### 10. 发送频道消息

- **路径**: `POST /im/manager/channel/message/send`
- **说明**: 向频道发送广播消息
- **权限**: `im:channel:send`

## 表情管理

### 11. 获取表情包分页列表

- **路径**: `GET /im/manager/face-pack/page`
- **说明**: 分页查询表情包列表
- **权限**: `im:face:query`

### 12. 创建表情包

- **路径**: `POST /im/manager/face-pack/create`
- **权限**: `im:face:create`

### 13. 更新表情包

- **路径**: `PUT /im/manager/face-pack/update`
- **权限**: `im:face:update`

### 14. 删除表情包

- **路径**: `DELETE /im/manager/face-pack/delete`
- **权限**: `im:face:delete`

### 15. 获取表情项分页列表

- **路径**: `GET /im/manager/face-pack-item/page`
- **说明**: 查询表情包下的表情项列表
- **权限**: `im:face:query`

### 16. 创建表情项

- **路径**: `POST /im/manager/face-pack-item/create`
- **权限**: `im:face:create`

### 17. 更新表情项

- **路径**: `PUT /im/manager/face-pack-item/update`
- **权限**: `im:face:update`

### 18. 删除表情项

- **路径**: `DELETE /im/manager/face-pack-item/delete`
- **权限**: `im:face:delete`

## 好友管理

### 19. 获取好友关系分页列表

- **路径**: `GET /im/manager/friend/page`
- **说明**: 分页查询好友关系列表
- **权限**: `im:friend:query`

### 20. 删除好友关系

- **路径**: `DELETE /im/manager/friend/delete`
- **说明**: 管理员删除好友关系
- **权限**: `im:friend:delete`

### 21. 获取好友请求分页列表

- **路径**: `GET /im/manager/friend-request/page`
- **说明**: 分页查询好友请求列表
- **权限**: `im:friend:query`

## 群组管理

### 22. 获取群组分页列表

- **路径**: `GET /im/manager/group/page`
- **说明**: 分页查询群组列表
- **权限**: `im:group:query`

### 23. 获取群组详情

- **路径**: `GET /im/manager/group/get`
- **权限**: `im:group:query`

### 24. 更新群组信息

- **路径**: `PUT /im/manager/group/update`
- **说明**: 管理员修改群组信息
- **权限**: `im:group:update`

### 25. 解散群组

- **路径**: `DELETE /im/manager/group/dissolve`
- **说明**: 管理员强制解散群组
- **权限**: `im:group:delete`

### 26. 获取群成员列表

- **路径**: `GET /im/manager/group/member/list`
- **说明**: 查询指定群组的成员列表
- **权限**: `im:group:query`

### 27. 获取群组请求分页列表

- **路径**: `GET /im/manager/group/request/page`
- **说明**: 分页查询入群请求列表
- **权限**: `im:group:query`

## 消息管理

### 28. 获取私聊消息分页列表

- **路径**: `GET /im/manager/message/private/page`
- **说明**: 分页查询私聊消息列表
- **权限**: `im:message:query`

### 29. 获取群聊消息分页列表

- **路径**: `GET /im/manager/message/group/page`
- **说明**: 分页查询群聊消息列表
- **权限**: `im:message:query`

### 30. 获取频道消息分页列表

- **路径**: `GET /im/manager/message/channel/page`
- **说明**: 分页查询频道消息列表
- **权限**: `im:message:query`

## RTC 管理

### 31. 获取 RTC 通话分页列表

- **路径**: `GET /im/manager/rtc/page`
- **说明**: 分页查询 RTC 通话记录列表
- **权限**: `im:rtc:query`

### 32. 获取 RTC 通话详情

- **路径**: `GET /im/manager/rtc/get`
- **说明**: 获取通话详情，包含参与者列表
- **权限**: `im:rtc:query`

### 33. 获取 RTC 参与者列表

- **路径**: `GET /im/manager/rtc/participant/list`
- **说明**: 查询指定通话的参与者列表
- **权限**: `im:rtc:query`

## 敏感词管理

### 34. 获取敏感词分页列表

- **路径**: `GET /im/manager/sensitive-word/page`
- **说明**: 分页查询敏感词列表
- **权限**: `im:sensitive-word:query`

### 35. 创建敏感词

- **路径**: `POST /im/manager/sensitive-word/create`
- **说明**: 添加敏感词
- **权限**: `im:sensitive-word:create`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| word | String | 是 | 敏感词内容 |
| status | Integer | 否 | 启用状态 |

- **响应**: `CommonResult<Long>` - 敏感词 ID

### 36. 更新敏感词

- **路径**: `PUT /im/manager/sensitive-word/update`
- **权限**: `im:sensitive-word:update`

### 37. 删除敏感词

- **路径**: `DELETE /im/manager/sensitive-word/delete`
- **权限**: `im:sensitive-word:delete`

## 统计面板

### 38. 获取 IM 统计概览

- **路径**: `GET /im/manager/statistics/overview`
- **说明**: 获取 IM 模块的整体统计数据
- **权限**: `im:statistics:query`
- **响应**:

| 字段 | 类型 | 说明 |
|-----|------|------|
| userCount | Long | 活跃用户数 |
| groupCount | Long | 群组总数 |
| messageCount | Long | 消息总数 |
| todayMessageCount | Long | 今日消息数 |

## 权限标识汇总

| 权限标识 | 说明 | 适用接口 |
|---------|------|---------|
| im:channel:query | 频道查询 | 频道列表、详情、素材列表 |
| im:channel:create | 频道创建 | 创建频道、素材 |
| im:channel:update | 频道更新 | 更新频道、素材 |
| im:channel:delete | 频道删除 | 删除频道、素材 |
| im:channel:send | 频道发送 | 发送频道消息 |
| im:face:query | 表情查询 | 表情包列表、表情项列表 |
| im:face:create | 表情创建 | 创建表情包、表情项 |
| im:face:update | 表情更新 | 更新表情包、表情项 |
| im:face:delete | 表情删除 | 删除表情包、表情项 |
| im:friend:query | 好友查询 | 好友列表、请求列表 |
| im:friend:delete | 好友删除 | 删除好友关系 |
| im:group:query | 群组查询 | 群组列表、详情、成员、请求 |
| im:group:update | 群组更新 | 更新群组信息 |
| im:group:delete | 群组删除 | 解散群组 |
| im:message:query | 消息查询 | 消息列表 |
| im:rtc:query | RTC 查询 | 通话列表、详情、参与者 |
| im:sensitive-word:query | 敏感词查询 | 敏感词列表 |
| im:sensitive-word:create | 敏感词创建 | 添加敏感词 |
| im:sensitive-word:update | 敏感词更新 | 更新敏感词 |
| im:sensitive-word:delete | 敏感词删除 | 删除敏感词 |
| im:statistics:query | 统计查询 | 统计面板 |

## 关键实现

- **双层 Controller 分离**: 用户端 Controller 通过登录态鉴权，管理端 Controller 通过 `@PreAuthorize` 进行 RBAC 权限校验
- **权限前缀**: 所有 IM 管理权限使用 `im:` 前缀，遵循 `im:模块:操作` 的命名规范
- **敏感词管理**: 管理员添加/修改敏感词后，敏感词库会自动更新，影响后续消息发送的过滤行为
