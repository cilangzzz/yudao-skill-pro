# 会员代码模式与扩展指南 (member)

> 本文档移植自模块 Skill 知识库（skill-member.yaml），提供该模块的代码模式、扩展指南与关键文件索引。

## 代码模式

### Controller 层规范

管理后台 Controller 的标准注解组合：

- `@Tag(name = "管理后台 - XXX")` — Swagger 分组
- `@RestController` + `@RequestMapping("/member/xxx")` — REST 入口
- `@PreAuthorize("@ss.hasPermission('member:xxx:action')")` — 权限控制
- `@PermitAll` — 无需登录的接口（如登录接口）

代码示例（会员用户 Controller，管理端调整积分的入口）：

```java
@Tag(name = "管理后台 - 会员用户")
@RestController
@RequestMapping("/member/user")
@Validated
public class MemberUserController {
    @Resource
    private MemberUserService memberUserService;

    @PutMapping("/update-point")
    @Operation(summary = "更新会员用户积分")
    @PreAuthorize("@ss.hasPermission('member:user:update-point')")
    public CommonResult<Boolean> updateUserPoint(@Valid @RequestBody MemberUserUpdatePointReqVO updateReqVO) {
        memberPointRecordService.createPointRecord(updateReqVO.getId(), updateReqVO.getPoint(),
                MemberPointBizTypeEnum.ADMIN, String.valueOf(getLoginUserId()));
        return success(true);
    }
}
```

### Service 层规范

- 接口定义在 `service` 包下，以 `Service` 结尾；
- 实现类以 `ServiceImpl` 结尾，使用 `@Service` 注解；
- 涉及积分等余额变更的方法使用 `@Transactional(rollbackFor = Exception.class)` 保证一致性。

代码示例（积分记录服务，「校验余额 → 更新用户积分 → 写积分流水」的标准三段式）：

```java
// Service接口
public interface MemberPointRecordService {
    void createPointRecord(Long userId, Integer point, MemberPointBizTypeEnum bizType, String bizId);
}

// Service实现
@Service
@Validated
public class MemberPointRecordServiceImpl implements MemberPointRecordService {
    @Resource
    private MemberPointRecordMapper memberPointRecordMapper;
    @Resource
    private MemberUserService memberUserService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createPointRecord(Long userId, Integer point, MemberPointBizTypeEnum bizType, String bizId) {
        // 1. 校验用户积分余额
        MemberUserDO user = memberUserService.getUser(userId);
        int totalPoint = ObjectUtil.defaultIfNull(user.getPoint(), 0) + point;
        if (totalPoint < 0) {
            throw exception(USER_POINT_NOT_ENOUGH);
        }
        // 2. 更新用户积分
        memberUserService.updateUserPoint(userId, point);
        // 3. 增加积分记录
        MemberPointRecordDO record = new MemberPointRecordDO()
                .setUserId(userId).setBizId(bizId).setBizType(bizType.getType())
                .setPoint(point).setTotalPoint(totalPoint);
        memberPointRecordMapper.insert(record);
    }
}
```

### DAL 层规范

Mapper 继承 `BaseMapperX`，位于 `dal/mysql` 包下，常用查询写成 default 方法：

```java
@Mapper
public interface MemberUserMapper extends BaseMapperX<MemberUserDO> {
    default MemberUserDO selectByMobile(String mobile) {
        return selectOne(MemberUserDO::getMobile, mobile);
    }
    default int updatePointIncr(Long id, Integer point) {
        return update(new MemberUserDO().setPoint(point),
                new LambdaQueryWrapper<MemberUserDO>().eq(MemberUserDO::getId, id));
    }
}
```

### 异常处理

错误码使用 `1_004_XXX_XXX` 前缀，常用错误码：

| 错误码 | 说明 |
|-------|------|
| 1_004_001_000 | 用户不存在 |
| 1_004_001_003 | 用户积分余额不足 |
| 1_004_003_000 | 登录失败，账号密码不正确 |
| 1_004_006_000 | 用户标签不存在 |
| 1_004_008_000 | 用户积分记录业务类型不支持 |
| 1_004_010_000 | 今日已签到，请勿重复签到 |
| 1_004_011_000 | 用户等级不存在 |

### 统一响应

- 成功：`CommonResult.success(data)`
- 失败：`throw exception(ERROR_CODE, args...)`

### 业务枚举

积分与经验来源通过枚举定义（开闭原则：新增来源只需追加枚举值）：

**MemberPointBizTypeEnum（积分业务类型）**

| type | name | 说明 | 是否增加积分 |
|-----|------|------|------------|
| 1 | SIGN | 签到 | 是 |
| 2 | ADMIN | 管理员修改 | 是 |
| 11 | ORDER_USE | 订单积分抵扣 | 否 |
| 21 | ORDER_GIVE | 订单积分奖励 | 是 |

**MemberExperienceBizTypeEnum（经验业务类型）**

| type | name | 说明 | 是否增加经验 |
|-----|------|------|------------|
| 0 | ADMIN | 管理员调整 | 是 |
| 1 | INVITE_REGISTER | 邀新奖励 | 是 |
| 4 | SIGN_IN | 签到奖励 | 是 |
| 11 | ORDER_GIVE | 下单奖励 | 是 |

## 扩展指南

### 新增会员权益功能

1. 在 `dal/dataobject` 下创建 `MemberBenefitDO` 实体类；
2. 创建 `MemberBenefitMapper` 接口；
3. 创建 `MemberBenefitService` 接口和实现类；
4. 创建 admin 和 app 的 Controller；
5. 在 `ErrorCodeConstants` 中添加错误码；
6. 如需对外暴露 API，在 `api` 包下创建 `MemberBenefitApi`。

### 新增会员等级

1. 通过管理后台或直接插入 `member_level` 表；
2. 设置等级名称、等级值、升级所需经验；
3. 配置享受折扣百分比；
4. 上传等级图标和背景图；
5. 确保升级经验值在相邻等级之间。

### 新增积分来源类型

1. 在 `MemberPointBizTypeEnum` 中添加新的枚举值；
2. 设置 `type`（唯一）、`name`、`description`、`add`（是否增加）；
3. 在对应业务场景调用 `MemberPointApi.addPoint` 或 `reducePoint`；
4. 示例：`MemberPointApi.addPoint(userId, 10, MemberPointBizTypeEnum.NEW_TYPE.getType(), bizId)`。

### 最佳实践

- 积分变更使用 `MemberPointApi`，保证记录完整性；
- 经验变更使用 `MemberLevelApi`，自动触发等级计算；
- 用户创建后发送 MQ 消息，便于其他模块处理；
- 等级经验配置需确保递增顺序，系统会自动校验；
- 积分抵扣配置通过 `MemberConfigApi` 获取，支持动态调整；
- 签到规则配置支持连续签到奖励递增；
- 地址管理支持多地址，需处理默认地址切换逻辑。

## 设计与架构补充

以下内容为现有文档（README.md、data-model.md）未覆盖的补充，避免与既有文档重复。

### 补充设计原则

除 README「设计原则」一节已列的双端分离、多租户、变更留痕、事务后事件等原则外，模块还遵循：

- **领域驱动设计（DDD）**：会员用户（MemberUser）作为聚合根，等级、分组、标签、收货地址等实体均挂接其上（详见 [data-model.md](data-model.md)）；
- **单一职责**：每个 Service 专注一个业务领域，如 `MemberUserService`、`MemberLevelService`；
- **开闭原则**：通过枚举定义业务类型（`MemberPointBizTypeEnum`），便于扩展新的积分/经验来源；
- **事务一致性**：积分变更、等级变更使用 `@Transactional` 保证数据一致性（见上文 Service 层代码示例）。

### Service 分层清单

controller 层（admin/app 双端）与 api 层已在 [README.md](README.md) 的「API 接口索引」「对外暴露的 API」中列出，dal 层见 [data-model.md](data-model.md)；此处补充业务逻辑层的完整服务清单：

| 业务域 | 服务 | 职责 |
|-------|------|------|
| 用户 | user/MemberUserService | 会员用户核心服务 |
| 认证 | auth/MemberAuthService | 会员认证（登录、登出、token 刷新） |
| 等级 | level/MemberLevelService | 等级配置、经验管理、自动升级 |
| 等级 | level/MemberLevelRecordService | 等级变更记录 |
| 等级 | level/MemberExperienceRecordService | 经验记录 |
| 积分 | point/MemberPointRecordService | 积分记录 |
| 签到 | signin/MemberSignInRecordService | 签到服务 |
| 签到 | signin/MemberSignInConfigService | 签到配置 |
| 标签 | tag/MemberTagService | 标签服务 |
| 分组 | group/MemberGroupService | 分组服务 |
| 地址 | address/AddressService | 收货地址服务 |
| 配置 | config/MemberConfigService | 配置服务 |

### 设计模式应用

| 模式 | 位置 | 用途 |
|-----|------|------|
| DTO 转换模式 | api/*/dto/*.java | API 层使用 DTO 隔离内部 DO，保护领域模型 |
| 策略模式（枚举实现） | enums/point/MemberPointBizTypeEnum.java | 定义积分业务类型，支持多种积分来源 |
| 模板方法 | service/level/MemberLevelServiceImpl.java | 等级变更流程：记录变更 → 更新经验 → 计算新等级 → 通知用户 |
| Facade 模式 | api/*ApiImpl.java | API 实现类封装 Service 调用，简化跨模块交互 |
| 观察者模式（MQ） | mq/producer/user/MemberUserProducer.java | 用户创建后发送消息，解耦后续处理逻辑 |

## 模块依赖

模块级依赖（上游业务模块）：

| 模块 | API/能力 | 用途 |
|-----|---------|------|
| system | SmsCodeApi | 短信验证码校验（登录、修改手机、重置密码） |
| system | SocialClientApi | 社交登录（微信、QQ 等）、微信小程序登录 |
| infra | 文件存储 | 头像上传存储 |

外部依赖（第三方库）：

| 依赖 | 版本 | 用途 |
|-----|------|------|
| spring-security-crypto | Spring Boot 自带 | 密码加密（BCryptPasswordEncoder） |
| mybatis-plus | 3.x | ORM 框架，数据访问增强 |
| hutool | 5.x | 工具类库 |

> 完整的依赖清单（framework starter、下游 mall 系列消费方）见 [README.md](README.md) 的「依赖关系」一节。

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/dal/dataobject/user/MemberUserDO.java | 会员用户实体，聚合根 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/service/user/MemberUserService.java | 会员用户服务接口 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/service/level/MemberLevelService.java | 会员等级服务，含经验管理和自动升级 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/api/point/MemberPointApi.java | 积分 API 接口，供其他模块调用 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/enums/point/MemberPointBizTypeEnum.java | 积分业务类型枚举 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/enums/ErrorCodeConstants.java | 错误码常量定义 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/controller/app/auth/AppAuthController.java | C 端认证控制器 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/service/signin/MemberSignInRecordService.java | 签到服务 |
| yudao-module-member/src/main/java/cn/iocoder/yudao/module/member/dal/dataobject/config/MemberConfigDO.java | 会员配置（积分抵扣设置） |
