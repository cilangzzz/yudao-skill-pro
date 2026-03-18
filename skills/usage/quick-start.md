# Skill 快速上手指南

> 本文档提供快速使用 Skill 文档的提示词模板，帮助开发者快速定位代码、理解业务、完成日常开发任务。

---

## 一、Skill 快速使用指南

### 什么是 Skill 文档

Skill 文档是从 ruoyi-vue-pro 项目代码中提取的结构化知识库，包含：
- **设计理念**：业务定位、设计原则、领域模型
- **架构设计**：分层架构、设计模式、模块通信
- **数据表设计**：实体关系、表结构、字段说明
- **代码规范**：Controller/Service/DAL 层代码模式
- **扩展指南**：新增功能步骤、最佳实践

### 如何使用 Skill 文档

```
使用 Skill 文档，帮我 [任务描述]

参考 Skill 文档：
- skills/modules/[模块名]/skill-[模块名].yaml
```

**示例**：
```
使用 Skill 文档，帮我在 system 模块添加一个"操作日志"功能。
参考 skills/modules/system/skill-system.yaml
```

---

## 二、一分钟提示词模板

### 基础模板

```
参考 Skill 文档 skills/modules/[模块]/skill-[模块].yaml，帮我完成以下任务：

[具体任务描述]

要求：
1. 遵循项目现有的代码规范
2. 使用统一响应格式 CommonResult
3. 添加必要的权限控制
```

### 快速填充指南

| 场景 | 模块路径 | 模块名 |
|------|---------|--------|
| 用户/角色/权限/菜单 | yudao-module-system | system |
| 文件/配置/任务/日志 | yudao-module-infra | infra |
| 支付/退款/钱包 | yudao-module-pay | pay |
| 会员/积分/等级/签到 | yudao-module-member | member |
| 商品/订单/促销 | yudao-module-mall | mall |
| 客户/线索/合同 | yudao-module-crm | crm |
| 采购/销售/库存 | yudao-module-erp | erp |
| 工作流/审批 | yudao-module-bpm | bpm |
| AI/大模型 | yudao-module-ai | ai |
| 物联网设备 | yudao-module-iot | iot |
| 微信公众号 | yudao-module-mp | mp |
| 报表 | yudao-module-report | report |

---

## 三、常见场景快速提示词

### 3.1 查找代码位置

```
参考 Skill 文档，帮我找到 [功能] 相关的代码位置：
- Controller 入口
- Service 实现
- Mapper 接口
- 数据表定义

模块：[模块名]
功能关键词：[关键词]
```

**示例**：
```
参考 skills/modules/system/skill-system.yaml，帮我找到用户登录相关的代码位置：
- Controller 入口
- Service 实现
- 认证逻辑
```

---

### 3.2 理解业务逻辑

```
参考 Skill 文档 skills/modules/[模块]/skill-[模块].yaml，帮我理解 [业务场景] 的完整流程：

1. 业务入口在哪里？
2. 核心业务逻辑在哪个 Service？
3. 涉及哪些数据表？
4. 状态流转是怎样的？
```

**示例**：
```
参考 skills/modules/mall/skill-mall.yaml，帮我理解订单支付的完整流程：
1. 支付入口在哪里？
2. 核心支付逻辑在哪个 Service？
3. 支付回调如何处理？
4. 订单状态如何流转？
```

---

### 3.3 修复 Bug

```
参考 Skill 文档 skills/modules/[模块]/skill-[模块].yaml，帮我分析和修复以下问题：

问题描述：[Bug 描述]
错误信息：[错误日志或异常信息]
复现步骤：[如何复现]

请帮我：
1. 定位问题代码位置
2. 分析问题原因
3. 提供修复方案
4. 说明需要修改的文件
```

**示例**：
```
参考 skills/modules/pay/skill-pay.yaml，帮我分析和修复以下问题：

问题描述：支付回调后订单状态未更新
错误信息：无异常，但订单一直是待支付状态

请帮我：
1. 定位回调处理代码
2. 分析状态更新逻辑
3. 检查事务是否正确
```

---

### 3.4 添加字段

```
参考 Skill 文档 skills/modules/[模块]/skill-[模块].yaml，帮我在 [实体] 中添加新字段：

字段名：[字段名]
字段类型：[类型]
字段用途：[用途说明]

需要修改：
1. DO 实体类
2. 数据库表（提供 SQL）
3. VO 类（请求/响应）
4. Controller（如有需要）
```

**示例**：
```
参考 skills/modules/member/skill-member.yaml，帮我在会员用户中添加新字段：

字段名：vipExpireTime
字段类型：LocalDateTime
字段用途：VIP 会员过期时间

需要修改：
1. MemberUserDO
2. member_user 表
3. 相关 VO 类
```

---

### 3.5 添加接口

```
参考 Skill 文档 skills/modules/[模块]/skill-[模块].yaml，帮我添加一个新接口：

接口名称：[接口名]
接口路径：[HTTP 方法和路径]
功能描述：[功能说明]
请求参数：[参数列表]
响应数据：[响应结构]
权限标识：[权限码]

请按照项目规范生成：
1. Controller 方法
2. Service 接口和实现
3. VO 类
```

**示例**：
```
参考 skills/modules/system/skill-system.yaml，帮我添加一个新接口：

接口名称：获取当前用户信息
接口路径：GET /system/user/current
功能描述：获取当前登录用户的详细信息
权限标识：system:user:query

请按照项目规范生成完整代码。
```

---

### 3.6 添加权限

```
参考 Skill 文档 skills/modules/system/skill-system.yaml，帮我添加一个新的权限：

权限名称：[权限名]
权限标识：[权限码，格式：模块:功能:操作]
父菜单ID：[父菜单 ID]
权限类型：[菜单/按钮]

请提供：
1. 菜单/按钮的 SQL 插入语句
2. Controller 中的 @PreAuthorize 注解示例
```

**示例**：
```
参考 skills/modules/system/skill-system.yaml，帮我添加一个新的权限：

权限名称：导出用户
权限标识：system:user:export
父菜单ID：用户管理菜单 ID
权限类型：按钮

请提供：
1. 按钮的 SQL 插入语句
2. Controller 中的权限注解示例
```

---

## 四、Skill 文档快速导航

### 4.1 模块索引

| 模块 | 文档路径 | 核心功能 | 关键实体 |
|------|---------|---------|---------|
| **system** | skills/modules/system/skill-system.yaml | 用户、角色、权限、菜单、租户、字典 | AdminUserDO, RoleDO, MenuDO |
| **infra** | skills/modules/infra/skill-infra.yaml | 文件、配置、任务、日志、代码生成 | FileDO, JobDO, ConfigDO |
| **pay** | skills/modules/pay/skill-pay.yaml | 支付、退款、钱包、转账 | PayOrderDO, PayRefundDO, PayWalletDO |
| **member** | skills/modules/member/skill-member.yaml | 会员、积分、等级、签到、地址 | MemberUserDO, MemberLevelDO |
| **mall** | skills/modules/mall/skill-mall.yaml | 商品、订单、促销、统计 | ProductSpuDO, TradeOrderDO, CouponDO |
| **crm** | skills/modules/crm/skill-crm.yaml | 线索、客户、商机、合同、回款 | CrmCustomerDO, CrmContractDO |
| **erp** | skills/modules/erp/skill-erp.yaml | 采购、销售、库存、财务 | ErpPurchaseDO, ErpSaleDO |
| **bpm** | skills/modules/bpm/skill-bpm.yaml | 流程定义、流程实例、任务 | BpmProcessDefinitionDO |
| **ai** | skills/modules/ai/skill-ai.yaml | AI 模型、对话、绘图 | AiChatMessageDO, AiImageDO |
| **iot** | skills/modules/iot/skill-iot.yaml | 设备、产品、物模型 | IotDeviceDO, IotProductDO |
| **mp** | skills/modules/mp/skill-mp.yaml | 公众号、菜单、消息 | MpAccountDO, MpMessageDO |
| **report** | skills/modules/report/skill-report.yaml | 报表、数据源、图表 | ReportDataSourceDO |

### 4.2 错误码前缀速查

| 模块 | 错误码前缀 | 示例 |
|------|-----------|------|
| system | 1_002_XXX_XXX | 1_002_000_000 登录失败 |
| infra | 1_001_XXX_XXX | 1_001_000_000 文件不存在 |
| pay | 1_007_XXX_XXX | 1_007_002_000 支付订单不存在 |
| member | 1_004_XXX_XXX | 1_004_001_000 用户不存在 |
| product | 1_008_XXX_XXX | 1_008_005_000 商品不存在 |
| trade | 1_011_XXX_XXX | 1_011_000_011 订单不存在 |
| promotion | 1_013_XXX_XXX | 1_013_004_000 优惠券模板不存在 |

### 4.3 权限标识规范

```
格式：模块:功能:操作

示例：
- system:user:query    # 查询用户
- system:user:create   # 创建用户
- system:user:update   # 更新用户
- system:user:delete   # 删除用户
- system:user:export   # 导出用户
```

---

## 五、常用代码片段

### 5.1 Controller 层

```java
@Tag(name = "管理后台 - [功能名]")
@RestController
@RequestMapping("/[模块]/[功能]")
@Validated
public class XxxController {

    @Resource
    private XxxService xxxService;

    @PostMapping("/create")
    @Operation(summary = "创建[功能]")
    @PreAuthorize("@ss.hasPermission('[模块]:[功能]:create')")
    public CommonResult<Long> createXxx(@Valid @RequestBody XxxSaveReqVO createReqVO) {
        return success(xxxService.createXxx(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新[功能]")
    @PreAuthorize("@ss.hasPermission('[模块]:[功能]:update')")
    public CommonResult<Boolean> updateXxx(@Valid @RequestBody XxxSaveReqVO updateReqVO) {
        xxxService.updateXxx(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除[功能]")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('[模块]:[功能]:delete')")
    public CommonResult<Boolean> deleteXxx(@RequestParam("id") Long id) {
        xxxService.deleteXxx(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得[功能]")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('[模块]:[功能]:query')")
    public CommonResult<XxxRespVO> getXxx(@RequestParam("id") Long id) {
        XxxDO xxx = xxxService.getXxx(id);
        return success(BeanUtils.toBean(xxx, XxxRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得[功能]分页")
    @PreAuthorize("@ss.hasPermission('[模块]:[功能]:query')")
    public CommonResult<PageResult<XxxRespVO>> getXxxPage(@Valid XxxPageReqVO pageReqVO) {
        PageResult<XxxDO> pageResult = xxxService.getXxxPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, XxxRespVO.class));
    }
}
```

### 5.2 Service 层

```java
// 接口
public interface XxxService {
    Long createXxx(@Valid XxxSaveReqVO createReqVO);
    void updateXxx(@Valid XxxSaveReqVO updateReqVO);
    void deleteXxx(Long id);
    XxxDO getXxx(Long id);
    PageResult<XxxDO> getXxxPage(XxxPageReqVO pageReqVO);
}

// 实现
@Service
@Validated
public class XxxServiceImpl implements XxxService {

    @Resource
    private XxxMapper xxxMapper;

    @Override
    public Long createXxx(XxxSaveReqVO createReqVO) {
        XxxDO xxx = BeanUtils.toBean(createReqVO, XxxDO.class);
        xxxMapper.insert(xxx);
        return xxx.getId();
    }

    @Override
    public void updateXxx(XxxSaveReqVO updateReqVO) {
        // 校验存在
        validateXxxExists(updateReqVO.getId());
        // 更新
        XxxDO updateObj = BeanUtils.toBean(updateReqVO, XxxDO.class);
        xxxMapper.updateById(updateObj);
    }

    @Override
    public void deleteXxx(Long id) {
        // 校验存在
        validateXxxExists(id);
        // 删除
        xxxMapper.deleteById(id);
    }

    private void validateXxxExists(Long id) {
        if (xxxMapper.selectById(id) == null) {
            throw exception(XXX_NOT_EXISTS);
        }
    }

    @Override
    public XxxDO getXxx(Long id) {
        return xxxMapper.selectById(id);
    }

    @Override
    public PageResult<XxxDO> getXxxPage(XxxPageReqVO pageReqVO) {
        return xxxMapper.selectPage(pageReqVO);
    }
}
```

### 5.3 Mapper 层

```java
@Mapper
public interface XxxMapper extends BaseMapperX<XxxDO> {

    default PageResult<XxxDO> selectPage(XxxPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<XxxDO>()
                .likeIfPresent(XxxDO::getName, reqVO.getName())
                .eqIfPresent(XxxDO::getStatus, reqVO.getStatus())
                .betweenIfPresent(XxxDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(XxxDO::getId));
    }

    default List<XxxDO> selectListByStatus(Integer status) {
        return selectList(XxxDO::getStatus, status);
    }
}
```

### 5.4 DO 实体类

```java
@TableName("[表名]")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class XxxDO extends TenantBaseDO {  // 或 BaseDO

    /**
     * 主键ID
     */
    @TableId
    private Long id;

    /**
     * 名称
     */
    private String name;

    /**
     * 状态
     */
    private Integer status;

    // ... 其他字段
}
```

### 5.5 VO 类

```java
// 请求 VO（新增/修改共用）
@Data
public class XxxSaveReqVO {

    @Schema(description = "编号", example = "1")
    private Long id;  // 更新时必填

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "测试")
    @NotBlank(message = "名称不能为空")
    private String name;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "0")
    @NotNull(message = "状态不能为空")
    private Integer status;
}

// 分页请求 VO
@Data
@EqualsAndHashCode(callSuper = true)
public class XxxPageReqVO extends PageParam {

    @Schema(description = "名称", example = "测试")
    private String name;

    @Schema(description = "状态", example = "0")
    private Integer status;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;
}

// 响应 VO
@Data
public class XxxRespVO {

    @Schema(description = "编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "测试")
    private String name;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "0")
    private Integer status;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime createTime;
}
```

### 5.6 错误码定义

```java
// 在 ErrorCodeConstants.java 中添加
ErrorCode XXX_NOT_EXISTS = new ErrorCode(1_002_XXX_000, "[功能]不存在");
ErrorCode XXX_NAME_DUPLICATE = new ErrorCode(1_002_XXX_001, "已存在该名字的[功能]");
```

### 5.7 跨模块 API 调用

```java
// API 接口定义
public interface XxxApi {
    CommonResult<XxxRespDTO> getXxx(Long id);
    CommonResult<List<XxxRespDTO>> getXxxList(Collection<Long> ids);
}

// API 实现
@RestController
@FeignClient(name = ApiConstants.NAME)
public class XxxApiImpl implements XxxApi {

    @Resource
    private XxxService xxxService;

    @Override
    public CommonResult<XxxRespDTO> getXxx(Long id) {
        XxxDO xxx = xxxService.getXxx(id);
        return success(BeanUtils.toBean(xxx, XxxRespDTO.class));
    }
}

// 调用方式
@Resource
private XxxApi xxxApi;

public void someMethod() {
    XxxRespDTO xxx = xxxApi.getXxx(id).getCheckedData();
}
```

---

## 六、快速参考

### 6.1 分层架构速记

```
Controller (HTTP入口)
    ↓
Service (业务逻辑)
    ↓
Mapper (数据访问)
    ↓
Database
```

### 6.2 常用注解速查

| 层级 | 常用注解 |
|------|---------|
| Controller | @RestController, @RequestMapping, @Tag, @Operation, @PreAuthorize |
| Service | @Service, @Validated, @Transactional |
| Mapper | @Mapper |
| DO | @TableName, @TableId, @Data |
| VO | @Data, @Schema, @NotBlank, @NotNull |

### 6.3 命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| Controller | XxxController | UserController |
| Service接口 | XxxService | UserService |
| Service实现 | XxxServiceImpl | UserServiceImpl |
| Mapper | XxxMapper | UserMapper |
| DO | XxxDO | UserDO |
| 请求VO | XxxSaveReqVO / XxxPageReqVO | UserSaveReqVO |
| 响应VO | XxxRespVO | UserRespVO |
| API接口 | XxxApi | UserApi |
| 错误码 | XXX_NOT_EXISTS | USER_NOT_EXISTS |

---

**提示**：使用 Skill 文档时，直接复制对应的提示词模板，替换占位符即可快速获得准确的代码生成和问题解答。