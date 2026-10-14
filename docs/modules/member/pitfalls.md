# 注意事项与已知坑点

> 使用 member 模块时的常见问题、易踩坑点和最佳实践。

## 1. 多租户相关

### 1.1 仅 member_user 表有租户隔离，其余 10 张表均为全局数据

**问题**: 多租户环境下，会员标签、等级、分组、积分记录、签到记录、收件地址等数据全局共享，不随租户隔离；而通过 `MemberUserApi` 查询用户时又会自动带上租户过滤，两类行为不一致容易踩坑。

**原因**: `cn.iocoder.yudao.module.member.dal.dataobject` 下 11 个 DO 中只有 `MemberUserDO` 继承 `TenantBaseDO`（`member_user` 表有 `tenant_id`），`MemberTagDO`、`MemberLevelDO`、`MemberGroupDO`、`MemberPointRecordDO`、`MemberSignInRecordDO`、`MemberSignInConfigDO`、`MemberLevelRecordDO`、`MemberExperienceRecordDO`、`MemberAddressDO`、`MemberConfigDO` 均继承 `BaseDO`，MyBatis 租户插件不会为这些表拼接 `tenant_id`。

**解决**:
- 在 member 模块上扩展新表时明确选择：需要租户隔离的 DO 继承 `TenantBaseDO` 并加 `tenant_id` 字段；
- 在无租户上下文的线程（定时任务、自建线程池）中调用 `MemberUserApi` 前需先设置 `TenantContextHolder`，否则连 `selectById` 都会因租户过滤查不到数据。

## 2. 消息与事务相关

### 2.1 "注册发券"消息是 Spring 事件而非 MQ，且在事务提交后才发布

**问题**: `MemberUserServiceImpl#createUser` 中注释写"发送 MQ 消息：用户创建"，实际是通过 `TransactionSynchronizationManager.registerSynchronization` 的 `afterCommit` 回调，由 `MemberUserProducer#sendUserCreateMessage` 调用 `applicationContext.publishEvent` 发布 `MemberUserCreateMessage`（Spring ApplicationEvent）。消费方是 mall-promotion 模块的 `CouponTakeByRegisterConsumer#onMessage`（`@EventListener + @Async`）。后果：事件无持久化、无重试，应用发布/崩溃窗口内提交的事件直接丢失，注册发券静默失效；若把 member 与 promotion 拆成独立服务部署，事件根本不会送达。

**原因**: `MemberUserCreateMessage` 位于 `member.api.message` 包，走的是进程内 Spring 事件总线；`@Async` 消费的上下文传递依赖 yudao-spring-boot-starter-job 的 `YudaoAsyncAutoConfiguration`（`@EnableAsync` + `executor.setTaskDecorator(TtlRunnable::get)`），`TenantContextHolder` 基于 `TransmittableThreadLocal`。另外 `MemberAuthServiceImpl#smsLogin`/`socialLogin` 标注了 `@Transactional`，整个登录事务（含 `useSmsCode`、`createUserIfAbsent`、`bindSocialUser`、`createAccessToken` 多个跨模块写操作）提交后事件才会发出；事务中途任一步失败，注册整体回滚、事件不发。

**解决**:
- 单体部署下可用；对发券可靠性有要求时改为本地消息表 + MQ 投递；
- 自定义异步线程池必须套 `TtlRunnable` 装饰器，否则异步消费丢失租户上下文；
- "注册后做 X"的扩展逻辑走同一个事件监听，不要塞进 `createUser` 事务内同步执行。

## 3. 积分相关

### 3.1 积分余额不足时静默跳过，调用方无法感知失败

**问题**: `MemberPointRecordServiceImpl#createPointRecord` 中，Java 层预计算 `totalPoint < 0` 时只 `log.error(USER_POINT_NOT_ENOUGH)` 后直接 `return`——不抛异常、不扣积分、不写流水。管理后台"更新积分"（`MemberUserController#updateUserPoint`，`MemberUserUpdatePointReqVO.point` 允许负数）调整负积分遇到余额不足时，接口仍返回 `success(true)` 假成功。类似地，`MemberPointApiImpl#addPoint` 在 bizType 非法时也只 `log.error` 后 `return`，而 `reducePoint` 同场景却抛 `POINT_RECORD_BIZ_NOT_SUPPORT`，加/扣行为不对称。

**原因**: 真正抛 `USER_POINT_NOT_ENOUGH` 的分支只有 `memberUserService.updateUserPoint` 更新行数为 0（用户不存在）这一种；余额不足被实现为"记日志跳过"。

**解决**: 外部调用（如订单积分抵扣 `MemberPointApi#reducePoint`）前自行校验用户余额；或修改 `createPointRecord`，将 `totalPoint < 0` 分支改为抛出 `USER_POINT_NOT_ENOUGH`。

### 3.2 积分扣减非原子，并发下可扣成负数

**问题**: 两个并发扣积分请求可能同时通过余额校验，把 `member_user.point` 扣成负数，且积分流水里的 `totalPoint` 与库中实际值对不上。

**原因**: 余额校验在 Java 层"先读后算"（`getUser` 取 `point` 再加变动值），而 `MemberUserMapper#updatePointDecr` 的 SQL 是 `point = point + 负数`，没有 `point + ? >= 0` 的条件保护；`updatePointIncr`/`updatePointDecr` 均用 `setSql(" point = point + " + incrCount)` 字符串拼接，入参必须保证是 `Integer`。

**解决**: 给扣减语句加余额条件并以更新行数判断成败，例如：

```java
LambdaUpdateWrapper<MemberUserDO> wrapper = new LambdaUpdateWrapper<MemberUserDO>()
        .setSql(" point = point + " + incrCount)
        .eq(MemberUserDO::getId, id)
        .apply("point + {0} >= 0", incrCount);
```

## 4. 签到相关

### 4.1 未配置签到规则时，签到接口直接 NPE（HTTP 500）

**问题**: 只要"签到规则"中没有启用状态的配置，App 端调用签到（`MemberSignInRecordServiceImpl#createSignRecord`）就抛空指针，返回 500 而非友好提示。

**原因**: `MemberSignInRecordConvert#convert` 中 `CollUtil.getLast(configs)` 在配置列表为空时返回 `null`，随后 `day > lastConfig.getDay()` 直接 NPE；`createSignRecord` 里 `getSignInConfigList(CommonStatusEnum.ENABLE.getStatus())` 查不到启用配置时列表为空。

**解决**: 开启签到功能前必须先配置启用状态的签到规则（连续签到奖励按 `day` 匹配）；或对 `lastConfig` 判空，返回"签到规则未配置"的业务异常。

### 4.2 重复签到校验无并发保护，可重复领积分经验

**问题**: 并发/双击签到可能插入两条签到记录，积分与经验双发。

**原因**: `createSignRecord` 靠"查最后一条记录（`selectLastRecordByUserId`）+ `DateUtils.isToday` 校验"防重，`member_signin_record` 无 `(user_id, 签到日期)` 唯一约束，查与插之间无原子性。连续天数同样依赖这条记录：上一条记录是昨天签的才 `day + 1`，否则重置为 1；超过最大配置天数（`CollUtil.getLast(configs)`）后从第 1 天开启新一轮。

**解决**: 对幂等要求高时加表级唯一约束兜底，或用分布式锁保证一人一天一条。

## 5. 等级与经验相关

### 5.1 member_user.level_id 用 0 表示"无等级"

**问题**: 按等级筛选、回显或自定义导出时，把"无等级"当成 `NULL` 处理会查不到数据或显示异常。

**原因**: `MemberUserServiceImpl#updateUserLevel` 中 `levelId = ObjectUtil.defaultIfNull(levelId, 0L)`，注释明确"0 代表无等级：防止 UpdateById 时，会被过滤掉的问题"。库中 `level_id = 0` 而非 `NULL`；`MemberLevelServiceImpl#getLevel` 对 `id <= 0` 返回 `null`，`MemberUserController#getUser` 因此能正常跳过等级名回显，但自己的查询代码需要同样处理。

**解决**: 查询"无等级"用户用 `level_id = 0`；关联等级时对 `0/null` 统一判空。

### 5.2 经验变更链路存在多处"静默"行为，等级变更无通知

**问题**:
- `MemberLevelServiceImpl#addExperience` 不校验用户存在，`getUser(userId)` 为 `null` 时 `user.getExperience()` 直接 NPE（对比 `updateUserLevel` 有 `USER_NOT_EXISTS` 校验）；
- `calculateNewLevel` 在等级配置为空/全部禁用、或经验低于所有启用等级阈值时，仅 `log.warn("计算会员等级失败...")` 返回 `null`——扣经验并不保证降级，等级保持原值；
- `notifyMemberLevelChange` 是空方法（`//todo: 给会员发消息`），等级升降没有任何通知或扩展钩子。

**原因**: 经验变动统一入口 `addExperience`（管理员调整入口 `updateUserLevel`）在同一事务内写经验记录（`MemberExperienceRecordService#createExperienceRecord`）、等级记录（`MemberLevelRecordService#createLevelRecord`）并更新 `member_user`，等级匹配基于 `getEnableLevelList()`（仅启用状态等级）。

**解决**: 变更经验必须走 `MemberLevelService#addExperience` / `updateUserLevel`，不要直接 update `member_user.experience`（否则记录缺失、等级不联动）；需要等级变更通知时在 `notifyMemberLevelChange` 中补实现。

## 6. 权限与接口相关

### 6.1 权限标识与接口元数据三处不一致

**问题**: 配菜单权限、看 Swagger 文档时容易对不上号：
- 权限前缀不统一：用户/等级/标签/分组/配置用 `member:*`（如 `member:user:query`、`member:level-record:query`），而积分与签到相关用 `point:*`（`point:record:query`、`point:sign-in-config:create`、`point:sign-in-record:query`）；`AddressController` 查地址复用的还是 `member:user:query`；
- `MemberPointRecordController` 的 `@Tag(name = "管理后台 - 签到记录")` 实为积分记录，且与 `MemberSignInRecordController` 的 `@Tag` 完全同名，文档中两组接口混在一起；
- `MemberLevelController`、`MemberGroupController`、`MemberTagController` 的 `/list-all-simple` 精简下拉接口没有 `@PreAuthorize`，仅登录即可访问全部等级/分组/标签数据。

**原因**: point/sign-in 相关 Controller 沿用了早期 `point:` 前缀未迁移；`@Tag` 复制粘贴未改；下拉接口按"登录即可"约定省略了权限注解。

**解决**: 配置菜单权限字符必须按代码中实际字符串（`point:sign-in-config:*` 等），不能全按 `member:` 前缀猜；下拉数据如敏感需自行补权限注解；新接口避免照抄 `@Tag`。

## 7. 错误码与数据模型相关

### 7.1 错误码段 1_004_XXX_XXX：AUTH 段跳号，validateUser 抛错语义错位

**问题**: 新增错误码按"连续编号"假设分配可能与保留号冲突；跨模块校验用户时报错文案误导排查。

**原因**: `ErrorCodeConstants` 使用 1_004 段，AUTH 段已跳号（1_004_003_002~004、1_004_003_006 缺失）；`MemberUserApiImpl#validateUser` 按 **id** 校验用户存在性，失败时抛的却是 `USER_MOBILE_NOT_EXISTS`（"手机号未注册用户"），mall-* 模块调用方看到的错误与实际校验方式不符。

**解决**: 新增错误码前先核对现有段占用，避开跳号；知晓 `MemberUserApi#validateUser` 的报错语义即"用户不存在"类，必要时调用方自行包装错误信息。

### 7.2 tagIds 逗号分隔存储，FIND_IN_SET 查询无法走索引

**问题**: 用户量大时，管理后台按标签筛选用户（`MemberUserMapper#selectPage` 的 `tagIds` 条件）、统计标签下用户数（`selectCountByTagId`，标签删除校验 `TAG_HAS_USER` 也走它）都是全表扫描。

**原因**: `MemberUserDO#tagIds` 用 `LongListTypeHandler` 以逗号分隔字符串存 `List<Long>`，查询用 `FIND_IN_SET`（`MyBatisUtils#findInSet`/`findInSetWithParamIndex`），无法命中索引；DO 依赖 `@TableName(value = "member_user", autoResultMap = true)` 才能在查询时正确反序列化为 `List<Long>`。

**解决**: 数据规模大时改为关联表方案；自定义 XML 查询 `tag_ids` 字段时记得指定 `typeHandler`，否则查出的是逗号分隔字符串。

### 7.3 member_config 单行配置表无并发保护

**问题**: 表为空时并发调用"保存会员设置"（`MemberConfigController` → `MemberConfigServiceImpl#saveConfig`）可能插入多条配置记录。

**原因**: `saveConfig` 是"先 `getConfig()` 查、无则 insert"的模式，`getConfig()` 取 `selectList()` 第一条（`CollectionUtils.getFirst`），无唯一约束兜底；一旦产生多条，之后永远只有第一条生效。

**解决**: 给 `member_config` 加单行约束（固定主键 + `INSERT ... ON DUPLICATE KEY UPDATE`），或保存时加分布式锁。
