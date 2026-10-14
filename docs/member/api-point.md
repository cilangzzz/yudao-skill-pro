# 积分记录接口 (MemberPointRecordController)

> 管理后台查询会员积分变动流水（签到、管理员修改、订单抵扣/奖励等业务产生的积分记录）。积分记录由各业务通过 `MemberPointRecordService#createPointRecord` 在事务中写入，管理端仅提供分页查询，不提供手工新增/修改/删除接口。

## 接口路径前缀
/member/point/record  (Controller: MemberPointRecordController)

## 1. 积分记录查询

### 1.1 获得用户积分记录分页
- **路径**: GET /member/point/record/page
- **权限**: point:record:query
- **说明**: 分页查询全平台的用户积分变动记录，支持按用户昵称、用户编号、业务类型、积分标题过滤，返回结果已拼接用户昵称。

**请求参数 (MemberPointRecordPageReqVO，继承 PageParam)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始（继承自 PageParam，默认 1） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数（继承自 PageParam，默认 10，最大 200） |
| nickname | String | 否 | 无 | 用户昵称，先按昵称模糊匹配会员用户，再按匹配到的用户过滤 |
| userId | Long | 否 | 无 | 用户编号，精确匹配 |
| bizType | Integer | 否 | 无 | 业务类型，对应 MemberPointBizTypeEnum：1 签到、2 管理员修改、11 订单积分抵扣、12 订单积分抵扣（整单取消）、13 订单积分抵扣（单个退款）、21 订单积分奖励、22 订单积分奖励（整单取消）、23 订单积分奖励（单个退款） |
| title | String | 否 | 无 | 积分标题，模糊匹配 |

**响应**: CommonResult&lt;PageResult&lt;MemberPointRecordRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 自增主键 |
| userId | Long | 用户编号 |
| nickname | String | 昵称（服务端按 userId 批量查询会员用户后拼接） |
| bizId | String | 业务编码（产生该记录的业务单据编号） |
| bizType | Integer | 业务类型（见请求参数 bizType 枚举说明） |
| title | String | 积分标题（即业务类型名称，如"签到"） |
| description | String | 积分描述（按业务类型描述模板格式化变动积分） |
| point | Integer | 变动积分（正数为增加，负数为扣减） |
| totalPoint | Integer | 变动后的积分余额 |
| createTime | LocalDateTime | 发生时间 |

**业务逻辑**:
1. Controller 调用 Service 执行分页查询；若请求传入了 `nickname`，先按昵称模糊查询会员用户列表。
2. 昵称匹配的用户为空时直接返回空分页，不再查询积分记录表。
3. Mapper 将昵称匹配到的 userId 集合（IN 条件）与 userId、bizType、title 条件组装查询，按 id 倒序分页查询 `member_point_record`。
4. 分页结果为空时，Controller 直接返回空 PageResult（保留 total）。
5. 否则按本页记录的 userId 集合批量查询会员用户，将 DO 转换为 RespVO 并拼接用户昵称后返回。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_004_001_003 | 用户积分余额不足（积分记录域内部 `createPointRecord` 扣减积分时，若更新用户积分失败抛出；余额不足时仅记录 error 日志、不写入记录） |
| 1_004_008_000 | 用户积分记录业务类型不支持（RPC 接口 MemberPointApiImpl 增加/减少积分时，业务类型无法匹配 MemberPointBizTypeEnum 抛出） |

## 补充说明

- 记录写入链路（非管理端点，供理解数据来源）：各业务（签到、订单、管理员调整等）调用 `MemberPointRecordService#createPointRecord(userId, point, bizType, bizId)`，在事务中：变动积分为 0 直接跳过 → 校验变动后积分不小于 0（不足则记 error 日志并跳过）→ 调用 `MemberUserService#updateUserPoint` 更新用户积分（失败抛 1_004_001_003）→ 插入积分记录（title 取业务类型名，description 按业务类型描述模板格式化，totalPoint 为变动后余额）。
- 源码中该控制器的 `@Tag` 标注为"管理后台 - 签到记录"，实为积分记录域，属源码文案遗留问题。
- VO 目录名为 `vo/recrod`（Record 的拼写笔误），属源码既有命名。
