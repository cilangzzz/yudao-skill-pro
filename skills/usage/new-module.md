# Skill 使用指南 - 新增模块场景

本文档提供从零开始创建新模块的完整提示词模板，基于 ruoyi-vue-pro 项目的模块化架构规范。

---

## 目录

1. [场景说明](#1-场景说明)
2. [提示词模板](#2-提示词模板)
   - [需求分析阶段](#21-需求分析阶段)
   - [架构设计阶段](#22-架构设计阶段)
   - [数据库设计阶段](#23-数据库设计阶段)
   - [代码生成阶段](#24-代码生成阶段)
   - [测试阶段](#25-测试阶段)
3. [实际示例](#3-实际示例)
   - [示例1：内容管理CMS模块](#31-示例1内容管理cms模块)
   - [示例2：消息通知模块](#32-示例2消息通知模块)
   - [示例3：工单系统模块](#33-示例3工单系统模块)
4. [模块结构清单](#4-模块结构清单)
5. [必要文件模板](#5-必要文件模板)

---

## 1. 场景说明

### 何时需要新增模块

在以下场景中，应当考虑创建新的业务模块：

| 场景特征 | 说明 | 示例 |
|---------|------|------|
| **独立业务领域** | 业务功能独立，不依附于现有模块 | CMS内容管理、工单系统 |
| **完整生命周期** | 具有独立的业务对象生命周期管理 | 订单管理、项目管理 |
| **多表关联** | 涉及5个以上数据表，有复杂关联关系 | 商品管理（SPU/SKU/分类/品牌等） |
| **跨模块调用** | 需要被其他模块调用，或调用其他模块 | 支付模块、消息通知模块 |
| **可插拔部署** | 业务功能可选，不同租户/场景可能不需要 | IoT设备管理、ERP进销存 |

### 不应创建新模块的情况

- 简单的增删改查功能，可在现有模块中扩展
- 仅增加几张配置表，不具备独立业务含义
- 功能与现有模块高度耦合，无法独立运行

---

## 2. 提示词模板

### 2.1 需求分析阶段

**提示词模板：**

```markdown
# 需求分析任务

我需要在 ruoyi-vue-pro 项目中新增一个 [模块名称] 模块，请帮我进行需求分析。

## 业务背景
[描述业务背景和目标，如：需要为系统增加内容管理能力，支持文章发布、栏目管理等功能]

## 核心功能需求
1. [功能点1]：[详细描述]
2. [功能点2]：[详细描述]
3. [功能点3]：[详细描述]

## 分析要求

请参考 skills/modules/system/skill-system.yaml 和 skills/modules/mall/skill-mall.yaml 的格式，帮我完成以下分析：

### 1. 业务定位分析
- 模块解决什么业务问题？
- 在整个系统中的定位是什么？
- 与现有模块的关系是什么？

### 2. 领域模型分析
参考 DDD 方法论，识别：
- 聚合根（Aggregate Root）：哪些实体是核心聚合根？
- 实体（Entity）：有哪些业务实体？
- 值对象（Value Object）：有哪些值对象？
- 领域服务（Domain Service）：需要哪些领域服务？
- 聚合边界：聚合内部的一致性边界是什么？

### 3. 设计原则确定
基于 SOLID 原则和项目规范，确定：
- 应采用哪些设计模式？（策略模式、工厂模式、模板方法模式等）
- 是否需要多租户支持？（继承 TenantBaseDO 还是 BaseDO）
- 是否需要数据权限控制？
- 是否需要工作流集成？

请输出结构化的分析结果。
```

---

### 2.2 架构设计阶段

**提示词模板：**

```markdown
# 架构设计任务

基于前面的需求分析结果，请为 [模块名称] 模块设计架构。

## 参考文档
- skills/modules/system/skill-system.yaml（基础模块结构参考）
- skills/modules/pay/skill-pay.yaml（设计模式应用参考）
- skills/modules/mall/skill-mall.yaml（复杂业务模块参考）

## 设计要求

### 1. 分层架构设计
按照项目规范设计以下层次：

| 层次 | 目录 | 职责 | 组件列表 |
|------|------|------|----------|
| api | yudao-module-{module}-api | 模块间API接口 | [列出API接口] |
| controller | yudao-module-{module}/controller | HTTP接口 | [列出Controller] |
| service | yudao-module-{module}/service | 业务逻辑 | [列出Service] |
| dal | yudao-module-{module}/dal | 数据访问 | [列出Mapper] |
| framework | yudao-module-{module}/framework | 框架扩展 | [如有] |

### 2. 设计模式选择
根据业务特点，选择合适的设计模式：

**场景1：需要支持多种类型切换（如支付渠道、存储类型）**
- 采用策略模式 + 工厂模式
- 参考：skills/patterns/strategy-pattern.yaml、skills/patterns/factory-pattern.yaml

**场景2：需要统一处理流程（如审批流程、发送流程）**
- 采用模板方法模式
- 参考：skills/patterns/template-method-pattern.yaml

### 3. 模块间通信设计
- **对外API**：哪些功能需要暴露给其他模块？
- **依赖API**：需要调用哪些其他模块的API？
- **消息队列**：是否需要异步消息通知？

### 4. 子模块划分（如果模块较大）
如果模块包含多个独立子域，建议拆分子模块：
- yudao-module-{module}-api：API 定义
- yudao-module-{domain1}：子域1实现
- yudao-module-{domain2}：子域2实现

请输出详细的架构设计文档。
```

---

### 2.3 数据库设计阶段

**提示词模板：**

```markdown
# 数据库设计任务

请为 [模块名称] 模块设计数据库表结构。

## 参考规范
- 所有表继承 BaseDO 或 TenantBaseDO 基类
- BaseDO 包含：id, creator, create_time, updater, update_time, deleted
- TenantBaseDO 额外包含：tenant_id
- 主键使用 BIGINT 类型，雪花算法生成

## 设计要求

### 1. 实体继承体系设计
为每个表确定继承关系：
- 需要多租户隔离：继承 TenantBaseDO
- 不需要多租户隔离：继承 BaseDO
- 忽略租户隔离：使用 @TenantIgnore 注解

### 2. 数据表设计
按照以下格式设计每张表：

```sql
-- 表名：{table_name}
-- 说明：{table_comment}
-- 继承：{BaseDO/TenantBaseDO}
CREATE TABLE `{table_name}` (
    -- 基础字段（由基类提供）
    `id` BIGINT NOT NULL COMMENT '主键',
    `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` BIT(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
    -- 租户字段（如果继承 TenantBaseDO）
    `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户编号',

    -- 业务字段
    `{field1}` VARCHAR(100) NOT NULL COMMENT '字段1说明',
    `{field2}` INT NOT NULL DEFAULT 0 COMMENT '字段2说明',
    -- ...

    PRIMARY KEY (`id`),
    INDEX `idx_{field}` (`{field}`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{table_comment}';
```

### 3. 表关系设计
描述表之间的关联关系：
- 一对一关系（1:1）
- 一对多关系（1:N）
- 多对多关系（N:N）

### 4. 索引设计
为高频查询字段设计索引，考虑：
- 唯一索引：唯一性约束字段
- 普通索引：高频查询字段
- 联合索引：组合查询条件

### 5. 状态枚举设计
为状态字段设计枚举值：

```java
public enum {Entity}StatusEnum {
    STATUS_1(0, "状态1"),
    STATUS_2(1, "状态2");
    // ...
}
```

请输出完整的数据库设计文档，包括建表SQL。
```

---

### 2.4 代码生成阶段

**提示词模板：**

```markdown
# 代码生成任务

请根据前面的设计和数据表结构，为 [模块名称] 模块生成代码框架。

## 项目结构参考
参考 yudao-module-system 模块的结构：

```
yudao-module-{module}/
├── yudao-module-{module}-api/          # API 模块
│   └── src/main/java/.../module/{module}/
│       ├── api/                        # API 接口定义
│       │   ├── {Entity}Api.java
│       │   └── dto/                    # DTO 对象
│       │       └── {Entity}RespDTO.java
│       └── enums/                      # 枚举定义
│           └── ErrorCodeConstants.java
│
└── yudao-module-{module}-biz/          # 业务实现模块
    └── src/main/java/.../module/{module}/
        ├── controller/                 # Controller 层
        │   ├── admin/                  # 管理后台接口
        │   │   └── {entity}/
        │   │       ├── {Entity}Controller.java
        │   │       └── vo/             # VO 对象
        │   │           ├── {Entity}SaveReqVO.java
        │   │           ├── {Entity}PageReqVO.java
        │   │           └── {Entity}RespVO.java
        │   └── app/                    # 用户端接口（如有）
        ├── service/                    # Service 层
        │   └── {entity}/
        │       ├── {Entity}Service.java
        │       └── {Entity}ServiceImpl.java
        ├── dal/                        # 数据访问层
        │   ├── dataobject/             # DO 实体
        │   │   └── {entity}/
        │   │       └── {Entity}DO.java
        │   └── mysql/                  # Mapper
        │       └── {entity}/
        │           └── {Entity}Mapper.java
        ├── convert/                    # 对象转换（可选）
        │   └── {Entity}Convert.java
        └── framework/                  # 框架扩展（如有）
```

## 生成要求

### 1. DO 实体类
按照规范生成，参考 skills/modules/system/skill-system.yaml 的 data_model 部分：

```java
@TableName("{table_name}")
@KeySequence("{table_name}_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class {Entity}DO extends {BaseDO/TenantBaseDO} {

    /**
     * {字段说明}
     */
    private {Type} {fieldName};

    // ... 其他字段
}
```

### 2. Mapper 接口
继承 BaseMapperX，提供通用 CRUD 和自定义查询：

```java
@Mapper
public interface {Entity}Mapper extends BaseMapperX<{Entity}DO> {

    default PageResult<{Entity}DO> selectPage({Entity}PageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<{Entity}DO>()
                .likeIfPresent({Entity}DO::getName, reqVO.getName())
                .eqIfPresent({Entity}DO::getStatus, reqVO.getStatus())
                .betweenIfPresent({Entity}DO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc({Entity}DO::getId));
    }
}
```

### 3. Service 接口和实现

**接口：**
```java
public interface {Entity}Service {

    Long create{Entity}(@Valid {Entity}SaveReqVO createReqVO);

    void update{Entity}(@Valid {Entity}SaveReqVO updateReqVO);

    void delete{Entity}(Long id);

    {Entity}DO get{Entity}(Long id);

    PageResult<{Entity}DO> get{Entity}Page({Entity}PageReqVO pageReqVO);
}
```

**实现：**
```java
@Service
@Validated
public class {Entity}ServiceImpl implements {Entity}Service {

    @Resource
    private {Entity}Mapper {entity}Mapper;

    @Override
    public Long create{Entity}({Entity}SaveReqVO createReqVO) {
        // 1. 参数校验
        // 2. 数据转换
        {Entity}DO {entity} = BeanUtils.toBean(createReqVO, {Entity}DO.class);
        // 3. 数据保存
        {entity}Mapper.insert({entity});
        return {entity}.getId();
    }

    // ... 其他方法实现
}
```

### 4. Controller 类

```java
@Tag(name = "管理后台 - {实体中文名}")
@RestController
@RequestMapping("/{module}/{entity}")
@Validated
public class {Entity}Controller {

    @Resource
    private {Entity}Service {entity}Service;

    @PostMapping("/create")
    @Operation(summary = "创建{实体中文名}")
    @PreAuthorize("@ss.hasPermission('{module}:{entity}:create')")
    public CommonResult<Long> create{Entity}(@Valid @RequestBody {Entity}SaveReqVO createReqVO) {
        return success({entity}Service.create{Entity}(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新{实体中文名}")
    @PreAuthorize("@ss.hasPermission('{module}:{entity}:update')")
    public CommonResult<Boolean> update{Entity}(@Valid @RequestBody {Entity}SaveReqVO updateReqVO) {
        {entity}Service.update{Entity}(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除{实体中文名}")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('{module}:{entity}:delete')")
    public CommonResult<Boolean> delete{Entity}(@RequestParam("id") Long id) {
        {entity}Service.delete{Entity}(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得{实体中文名}")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('{module}:{entity}:query')")
    public CommonResult<{Entity}RespVO> get{Entity}(@RequestParam("id") Long id) {
        {Entity}DO {entity} = {entity}Service.get{Entity}(id);
        return success(BeanUtils.toBean({entity}, {Entity}RespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得{实体中文名}分页")
    @PreAuthorize("@ss.hasPermission('{module}:{entity}:query')")
    public CommonResult<PageResult<{Entity}RespVO>> get{Entity}Page(@Valid {Entity}PageReqVO pageReqVO) {
        PageResult<{Entity}DO> pageResult = {entity}Service.get{Entity}Page(pageReqVO);
        return success(BeanUtils.toBean(pageResult, {Entity}RespVO.class));
    }
}
```

### 5. VO 类

**保存请求 VO：**
```java
@Data
public class {Entity}SaveReqVO {

    @Schema(description = "编号", example = "1")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "示例")
    @NotBlank(message = "名称不能为空")
    private String name;

    @Schema(description = "状态", example = "0")
    private Integer status;

    // ... 其他字段
}
```

**分页请求 VO：**
```java
@Data
@EqualsAndHashCode(callSuper = true)
public class {Entity}PageReqVO extends PageParam {

    @Schema(description = "名称", example = "示例")
    private String name;

    @Schema(description = "状态", example = "0")
    private Integer status;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;
}
```

**响应 VO：**
```java
@Data
public class {Entity}RespVO {

    @Schema(description = "编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "示例")
    private String name;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "0")
    private Integer status;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime createTime;

    // ... 其他字段
}
```

### 6. API 接口（跨模块调用）

```java
public interface {Entity}Api {

    /**
     * 获取{实体中文名}
     *
     * @param id 编号
     * @return {实体中文名}
     */
    {Entity}RespDTO get{Entity}(Long id);
}
```

### 7. 错误码定义

```java
public interface ErrorCodeConstants {
    // ========== {模块中文名} 1-0XX-XXX-XXX ==========
    ErrorCode {ENTITY}_NOT_EXISTS = new ErrorCode(1_0XX_000_000, "{实体中文名}不存在");
    ErrorCode {ENTITY}_NAME_DUPLICATE = new ErrorCode(1_0XX_000_001, "已存在该名字的{实体中文名}");
    // ... 其他错误码
}
```

请按照以上规范生成完整的代码框架。
```

---

### 2.5 测试阶段

**提示词模板：**

```markdown
# 测试任务

请为 [模块名称] 模块编写测试代码。

## 测试类型

### 1. 单元测试
为 Service 层编写单元测试：

```java
@SpringBootTest
class {Entity}ServiceImplTest {

    @Resource
    private {Entity}Service {entity}Service;

    @Test
    void testCreate{Entity}() {
        // 准备数据
        {Entity}SaveReqVO reqVO = new {Entity}SaveReqVO();
        reqVO.setName("测试名称");
        // ... 设置其他字段

        // 执行测试
        Long id = {entity}Service.create{Entity}(reqVO);

        // 验证结果
        assertNotNull(id);
        {Entity}DO entity = {entity}Service.get{Entity}(id);
        assertEquals("测试名称", entity.getName());
    }

    @Test
    void testUpdate{Entity}() {
        // 更新测试
    }

    @Test
    void testDelete{Entity}() {
        // 删除测试
    }

    @Test
    void testGet{Entity}Page() {
        // 分页查询测试
    }
}
```

### 2. 集成测试
为 Controller 层编写集成测试：

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class {Entity}ControllerTest {

    @Resource
    private MockMvc mockMvc;

    @Test
    void testCreate{Entity}() throws Exception {
        // 准备请求体
        String requestBody = """
            {
                "name": "测试名称",
                "status": 0
            }
            """;

        // 执行请求
        mockMvc.perform(post("/{module}/{entity}/create")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").isNumber());
    }
}
```

### 3. 功能测试清单

请生成以下测试场景：

| 测试项 | 测试场景 | 预期结果 |
|--------|----------|----------|
| 创建 | 正常创建 | 返回ID，数据入库 |
| 创建 | 缺少必填项 | 返回参数校验错误 |
| 更新 | 正常更新 | 数据更新成功 |
| 更新 | 不存在的ID | 返回数据不存在错误 |
| 删除 | 正常删除 | 数据标记删除 |
| 删除 | 不存在的ID | 返回数据不存在错误 |
| 查询 | 单条查询 | 返回正确数据 |
| 查询 | 分页查询 | 返回分页数据 |
| 查询 | 条件筛选 | 返回筛选结果 |

请输出完整的测试代码和测试清单。
```

---

## 3. 实际示例

### 3.1 示例1：内容管理CMS模块

**完整提示词：**

```markdown
# 新增模块任务：内容管理CMS模块

我需要在 ruoyi-vue-pro 项目中新增一个 CMS（内容管理系统）模块，请帮我完成从需求分析到代码生成的全过程。

## 业务背景
系统需要一个内容管理模块，支持：
1. 文章发布和管理（富文本、图片）
2. 栏目/分类管理（树形结构）
3. 标签管理
4. 评论管理
5. 内容审核流程

## 参考文档
请参考以下 Skill 文档：
- skills/modules/system/skill-system.yaml：基础模块结构、多租户、树形结构
- skills/modules/mall/skill-mall.yaml：SPU/SKU 模型参考（文章类似SPU）
- skills/modules/bpm/skill-bpm.yaml：审核流程集成

## 任务要求

### 阶段1：需求分析
1. 确定 CMS 模块的业务定位
2. 识别聚合根、实体、值对象
3. 确定设计原则（多租户支持、数据权限等）

### 阶段2：架构设计
1. 设计分层架构
2. 设计模块间通信（是否需要 API）
3. 确定是否需要工作流集成

### 阶段3：数据库设计
1. 设计文章表（cms_article）
2. 设计栏目表（cms_category）
3. 设计标签表（cms_tag）
4. 设计文章标签关联表（cms_article_tag）
5. 设计评论表（cms_comment）
6. 设计表关系和索引

### 阶段4：代码生成
按照项目规范生成：
1. DO 实体类
2. Mapper 接口
3. Service 接口和实现
4. Controller 类
5. VO 类
6. 错误码定义

### 阶段5：测试
生成单元测试和集成测试代码

请按顺序输出各阶段的设计文档和代码。
```

**预期输出结构：**

```
yudao-module-cms/
├── yudao-module-cms-api/
│   └── src/main/java/.../module/cms/
│       ├── api/
│       │   ├── ArticleApi.java
│       │   └── dto/
│       │       └── ArticleRespDTO.java
│       └── enums/
│           ├── ArticleStatusEnum.java
│           └── ErrorCodeConstants.java
│
└── yudao-module-cms-biz/
    └── src/main/java/.../module/cms/
        ├── controller/
        │   └── admin/
        │       ├── article/
        │       │   ├── ArticleController.java
        │       │   └── vo/
        │       ├── category/
        │       │   ├── CategoryController.java
        │       │   └── vo/
        │       ├── tag/
        │       └── comment/
        ├── service/
        │   ├── article/
        │   ├── category/
        │   ├── tag/
        │   └── comment/
        ├── dal/
        │   ├── dataobject/
        │   │   ├── article/ArticleDO.java
        │   │   ├── category/CategoryDO.java
        │   │   ├── tag/TagDO.java
        │   │   └── comment/CommentDO.java
        │   └── mysql/
        └── convert/
```

---

### 3.2 示例2：消息通知模块

**完整提示词：**

```markdown
# 新增模块任务：消息通知模块

我需要新增一个消息通知模块，统一管理系统内的各类消息通知。

## 业务背景
当前系统需要统一的消息通知能力，支持：
1. 站内信（系统通知、用户消息）
2. 短信通知（验证码、业务通知）
3. 邮件通知
4. WebSocket 实时推送
5. 消息模板管理
6. 发送记录和状态追踪

## 参考文档
请参考以下 Skill 文档：
- skills/modules/system/skill-system.yaml：短信/邮件/站内信现有实现
- skills/modules/pay/skill-pay.yaml：策略模式 + 工厂模式（渠道切换）
- skills/modules/infra/skill-infra.yaml：文件存储渠道参考

## 特殊要求
1. 消息发送采用策略模式，支持多渠道切换
2. 使用工厂模式创建消息客户端
3. 支持异步发送和重试机制
4. 支持消息模板变量替换

## 任务要求

### 阶段1：架构设计
重点设计：
1. MessageClient 接口（策略模式）
2. MessageClientFactory 工厂类
3. AbstractMessageClient 抽象类（模板方法模式）
4. 各渠道实现类（SmsMessageClient、EmailMessageClient、WebSocketMessageClient）

### 阶段2：数据库设计
1. 消息模板表（notify_template）
2. 消息发送记录表（notify_send_log）
3. 消息配置表（notify_channel_config）

### 阶段3：代码生成
重点生成：
1. 策略模式相关代码
2. 工厂模式相关代码
3. 模板方法模式相关代码
```

**设计模式应用示例：**

```java
// 策略模式：消息客户端接口
public interface MessageClient {

    /**
     * 发送消息
     */
    MessageSendResultDTO send(MessageSendReqDTO reqDTO);

    /**
     * 获取渠道类型
     */
    MessageChannelEnum getChannel();
}

// 模板方法模式：抽象基类
public abstract class AbstractMessageClient implements MessageClient {

    @Override
    public final MessageSendResultDTO send(MessageSendReqDTO reqDTO) {
        // 1. 参数校验
        validateParams(reqDTO);
        // 2. 模板变量替换
        String content = processTemplate(reqDTO);
        // 3. 执行发送（子类实现）
        return doSend(reqDTO, content);
    }

    protected abstract MessageSendResultDTO doSend(MessageSendReqDTO reqDTO, String content);
}

// 工厂模式：客户端工厂
@Component
public class MessageClientFactory {

    private final Map<MessageChannelEnum, MessageClient> clients = new ConcurrentHashMap<>();

    public MessageClient getClient(MessageChannelEnum channel) {
        return clients.get(channel);
    }
}
```

---

### 3.3 示例3：工单系统模块

**完整提示词：**

```markdown
# 新增模块任务：工单系统模块

我需要新增一个工单系统模块，用于企业内部的工单流转和管理。

## 业务背景
企业需要一个工单系统，支持：
1. 工单类型管理（故障报修、服务请求、问题反馈等）
2. 工单创建和分配
3. 工单状态流转（新建-处理中-已解决-已关闭）
4. 工单流转记录
5. 工单评价
6. SLA 服务时效管理
7. 工作流集成（审批流程）

## 参考文档
请参考以下 Skill 文档：
- skills/modules/bpm/skill-bpm.yaml：工作流集成
- skills/modules/mall/skill-mall.yaml：订单状态机参考
- skills/modules/system/skill-system.yaml：用户/部门关联

## 特殊要求
1. 工单状态采用状态机模式
2. 与 BPM 模块集成，支持审批流程
3. 支持 SLA 超时提醒
4. 支持数据权限（仅查看本部门工单）

## 任务要求

### 阶段1：领域模型设计
1. 识别聚合根：Ticket（工单）
2. 识别实体：TicketType、TicketLog、TicketComment
3. 识别值对象：TicketStatus、TicketPriority
4. 设计状态流转规则

### 阶段2：工作流集成设计
1. 工单创建时可选发起审批流程
2. 监听流程状态变更事件
3. 更新工单状态

### 阶段3：数据库设计
1. 工单表（ticket）
2. 工单类型表（ticket_type）
3. 工单流转记录表（ticket_log）
4. 工单评价表（ticket_evaluation）
```

**状态机设计示例：**

```java
public enum TicketStatusEnum {

    NEW(0, "新建"),
    ASSIGNED(10, "已分配"),
    PROCESSING(20, "处理中"),
    RESOLVED(30, "已解决"),
    CLOSED(40, "已关闭"),
    REJECTED(50, "已拒绝");

    // 状态流转规则
    private static final Map<TicketStatusEnum, Set<TicketStatusEnum>> TRANSITIONS = Map.of(
        NEW, Set.of(ASSIGNED, REJECTED),
        ASSIGNED, Set.of(PROCESSING, NEW),
        PROCESSING, Set.of(RESOLVED, ASSIGNED),
        RESOLVED, Set.of(CLOSED, PROCESSING),
        CLOSED, Set.of(),
        REJECTED, Set.of(NEW)
    );

    public boolean canTransitionTo(TicketStatusEnum target) {
        return TRANSITIONS.getOrDefault(this, Set.of()).contains(target);
    }
}
```

---

## 4. 模块结构清单

### 4.1 标准 Maven 模块结构

```
yudao-module-{module}/
├── pom.xml                              # 父 POM
├── yudao-module-{module}-api/           # API 模块
│   ├── pom.xml
│   └── src/main/java/.../module/{module}/
│       ├── api/                         # API 接口
│       │   ├── {Entity}Api.java
│       │   └── dto/                     # DTO 对象
│       │       ├── {Entity}CreateReqDTO.java
│       │       └── {Entity}RespDTO.java
│       └── enums/                       # 枚举和常量
│           ├── {Entity}StatusEnum.java
│           └── ErrorCodeConstants.java
│
└── yudao-module-{module}-biz/           # 业务实现模块
    ├── pom.xml
    └── src/
        ├── main/java/.../module/{module}/
        │   ├── controller/              # Controller 层
        │   │   ├── admin/               # 管理后台接口
        │   │   │   └── {entity}/
        │   │   │       ├── {Entity}Controller.java
        │   │   │       └── vo/
        │   │   │           ├── {Entity}SaveReqVO.java
        │   │   │           ├── {Entity}PageReqVO.java
        │   │   │           └── {Entity}RespVO.java
        │   │   └── app/                 # 用户端接口
        │   ├── service/                 # Service 层
        │   │   └── {entity}/
        │   │       ├── {Entity}Service.java
        │   │       └── {Entity}ServiceImpl.java
        │   ├── dal/                     # 数据访问层
        │   │   ├── dataobject/          # DO 实体
        │   │   │   └── {entity}/
        │   │   │       └── {Entity}DO.java
        │   │   └── mysql/               # Mapper
        │   │       └── {entity}/
        │   │           └── {Entity}Mapper.java
        │   ├── convert/                 # 对象转换
        │   │   └── {Entity}Convert.java
        │   ├── api/                     # API 实现
        │   │   └── {Entity}ApiImpl.java
        │   └── framework/               # 框架扩展
        │       └── {domain}/            # 领域特定扩展
        │           └── {Custom}Client.java
        │
        └── test/java/.../module/{module}/
            └── service/
                └── {entity}/
                    └── {Entity}ServiceImplTest.java
```

### 4.2 多子模块结构（大型模块）

```
yudao-module-{module}/
├── pom.xml
├── yudao-module-{module}-api/           # 统一 API
│
├── yudao-module-{domain1}-biz/          # 子域1
│   ├── controller/
│   ├── service/
│   └── dal/
│
├── yudao-module-{domain2}-biz/          # 子域2
│   ├── controller/
│   ├── service/
│   └── dal/
│
└── yudao-module-{module}-biz/           # 主模块（聚合）
```

---

## 5. 必要文件模板

### 5.1 POM 文件模板

**父 POM（yudao-module-{module}/pom.xml）：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <parent>
        <groupId>cn.iocoder.boot</groupId>
        <artifactId>yudao</artifactId>
        <version>${revision}</version>
    </parent>
    <modelVersion>4.0.0</modelVersion>

    <artifactId>yudao-module-{module}</artifactId>
    <packaging>pom</packaging>
    <name>${project.artifactId}</name>
    <description>{模块中文名}模块</description>

    <modules>
        <module>yudao-module-{module}-api</module>
        <module>yudao-module-{module}-biz</module>
    </modules>
</project>
```

**API 模块 POM（yudao-module-{module}-api/pom.xml）：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <parent>
        <groupId>cn.iocoder.boot</groupId>
        <artifactId>yudao-module-{module}</artifactId>
        <version>${revision}</version>
    </parent>
    <modelVersion>4.0.0</modelVersion>

    <artifactId>yudao-module-{module}-api</artifactId>
    <packaging>jar</packaging>
    <name>${project.artifactId}</name>
    <description>{模块中文名}模块 API</description>

    <dependencies>
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-common</artifactId>
        </dependency>

        <!-- Validation -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>
</project>
```

**业务模块 POM（yudao-module-{module}-biz/pom.xml）：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <parent>
        <groupId>cn.iocoder.boot</groupId>
        <artifactId>yudao-module-{module}</artifactId>
        <version>${revision}</version>
    </parent>
    <modelVersion>4.0.0</modelVersion>

    <artifactId>yudao-module-{module}-biz</artifactId>
    <packaging>jar</packaging>
    <name>${project.artifactId}</name>
    <description>{模块中文名}模块业务实现</description>

    <dependencies>
        <!-- API 模块 -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-module-{module}-api</artifactId>
            <version>${revision}</version>
        </dependency>

        <!-- System API（用户、部门等） -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-module-system-api</artifactId>
            <version>${revision}</version>
        </dependency>

        <!-- Web -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-spring-boot-starter-web</artifactId>
        </dependency>

        <!-- Security -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-spring-boot-starter-security</artifactId>
        </dependency>

        <!-- MyBatis -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-spring-boot-starter-mybatis</artifactId>
        </dependency>

        <!-- Tenant -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-spring-boot-starter-biz-tenant</artifactId>
        </dependency>

        <!-- Test -->
        <dependency>
            <groupId>cn.iocoder.boot</groupId>
            <artifactId>yudao-spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

### 5.2 数据库 SQL 模板

```sql
-- ----------------------------
-- {模块中文名}模块表结构
-- ----------------------------

-- {表说明}
CREATE TABLE `{table_name}` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` BIT(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
    `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户编号',

    -- 业务字段
    `name` VARCHAR(100) NOT NULL COMMENT '名称',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',

    PRIMARY KEY (`id`),
    INDEX `idx_name` (`name`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{表说明}';
```

### 5.3 菜单权限 SQL 模板

```sql
-- 菜单 SQL
INSERT INTO system_menu(name, permission, type, sort, parent_id, path, icon, component, component_name, status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted)
VALUES ('{菜单名称}', '', 2, 0, {父菜单ID}, '{路径}', 'ep:document', '{组件路径}', '{组件名}', 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

-- 按钮权限 SQL（假设新菜单ID为 @parentId）
SELECT @parentId := LAST_INSERT_ID();

INSERT INTO system_menu(name, permission, type, sort, parent_id, path, icon, component, component_name, status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted)
VALUES ('{功能}查询', '{module}:{entity}:query', 3, 1, @parentId, '', '', '', '', 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu(name, permission, type, sort, parent_id, path, icon, component, component_name, status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted)
VALUES ('{功能}新增', '{module}:{entity}:create', 3, 2, @parentId, '', '', '', '', 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu(name, permission, type, sort, parent_id, path, icon, component, component_name, status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted)
VALUES ('{功能}修改', '{module}:{entity}:update', 3, 3, @parentId, '', '', '', '', 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu(name, permission, type, sort, parent_id, path, icon, component, component_name, status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted)
VALUES ('{功能}删除', '{module}:{entity}:delete', 3, 4, @parentId, '', '', '', '', 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu(name, permission, type, sort, parent_id, path, icon, component, component_name, status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted)
VALUES ('{功能}导出', '{module}:{entity}:export', 3, 5, @parentId, '', '', '', '', 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');
```

### 5.4 错误码定义模板

```java
package cn.iocoder.yudao.module.{module}.enums;

import cn.iocoder.yudao.framework.common.exception.ErrorCode;

/**
 * {模块中文名}错误码枚举类
 *
 * {模块} 系统，使用 1-0XX-000-000 段
 */
public interface ErrorCodeConstants {

    // ========== {实体1} 1-0XX-000-000 ==========
    ErrorCode {ENTITY1}_NOT_EXISTS = new ErrorCode(1_0XX_000_000, "{实体中文名}不存在");
    ErrorCode {ENTITY1}_NAME_DUPLICATE = new ErrorCode(1_0XX_000_001, "已存在该名字的{实体中文名}");
    ErrorCode {ENTITY1}_STATUS_ERROR = new ErrorCode(1_0XX_000_002, "{实体中文名}状态不正确");

    // ========== {实体2} 1-0XX-001-000 ==========
    ErrorCode {ENTITY2}_NOT_EXISTS = new ErrorCode(1_0XX_001_000, "{实体中文名}不存在");
    // ... 其他错误码
}
```

### 5.5 Spring 配置模板

**application.yaml：**

```yaml
yudao:
  info:
    version: 1.0.0
    base-package: cn.iocoder.yudao.module.{module}

spring:
  application:
    name: yudao-module-{module}-biz

  # 数据源配置（如使用独立数据源）
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://127.0.0.1:3306/ruoyi-vue-pro?useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&nullCatalogMeansCurrent=true
    username: root
    password: root

# MyBatis 配置
mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true
  global-config:
    db-config:
      id-type: none
      logic-delete-field: deleted
  type-aliases-package: ${yudao.info.base-package}.dal.dataobject

# 日志配置
logging:
  level:
    cn.iocoder.yudao.module.{module}: debug
```

---

## 附录：快速检查清单

### 新增模块检查清单

| 检查项 | 说明 | 状态 |
|--------|------|------|
| **需求分析** | | |
| 业务定位明确 | 清晰定义模块职责和边界 | [ ] |
| 领域模型识别 | 聚合根、实体、值对象已识别 | [ ] |
| 设计原则确定 | 多租户、数据权限、设计模式 | [ ] |
| **架构设计** | | |
| 分层架构设计 | api/controller/service/dal | [ ] |
| 模块间通信设计 | 对外API和依赖API | [ ] |
| 设计模式选择 | 策略/工厂/模板方法等 | [ ] |
| **数据库设计** | | |
| 表结构设计 | 字段类型、长度、默认值 | [ ] |
| 表关系设计 | 外键、关联关系 | [ ] |
| 索引设计 | 高频查询字段索引 | [ ] |
| 状态枚举设计 | 状态值、流转规则 | [ ] |
| **代码实现** | | |
| DO 实体类 | 继承正确的基类 | [ ] |
| Mapper 接口 | 继承 BaseMapperX | [ ] |
| Service 接口和实现 | @Service, @Validated 注解 | [ ] |
| Controller 类 | @RestController, 权限注解 | [ ] |
| VO 类 | 参数校验注解 | [ ] |
| API 接口 | 跨模块调用支持 | [ ] |
| 错误码定义 | 统一错误码格式 | [ ] |
| **配置文件** | | |
| POM 文件 | 依赖配置正确 | [ ] |
| Spring 配置 | 数据源、MyBatis配置 | [ ] |
| 菜单权限 SQL | 功能权限配置 | [ ] |
| **测试** | | |
| 单元测试 | Service 层测试 | [ ] |
| 集成测试 | Controller 层测试 | [ ] |
| 功能测试 | 业务场景测试 | [ ] |

---

**文档版本：** 1.0.0
**最后更新：** 2026-03-18
**维护者：** AI Assistant