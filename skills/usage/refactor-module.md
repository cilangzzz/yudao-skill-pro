---
# Skills 自动引用配置
# AI 读取本文档时会自动加载以下规范文件，确保生成的代码符合项目规范
references:
  design:
    - path: skills/design/api-designer.yaml
      reason: "API 接口设计规范 - 改造时需保持接口兼容性"
    - path: skills/design/entity-designer.yaml
      reason: "实体类设计规范 - 改造 DO 需遵循规范"
    - path: skills/design/db-designer.yaml
      reason: "数据库设计规范 - 表结构变更需遵循规范"
  module_guide:
    prompt: "请指定要改造的模块，AI 将加载对应模块的 skill 文档"
    mapping:
      system: skills/modules/system/skill-system.yaml
      infra: skills/modules/infra/skill-infra.yaml
      pay: skills/modules/pay/skill-pay.yaml
      member: skills/modules/member/skill-member.yaml
      mall: skills/modules/mall/skill-mall.yaml
      crm: skills/modules/crm/skill-crm.yaml
      erp: skills/modules/erp/skill-erp.yaml
      bpm: skills/modules/bpm/skill-bpm.yaml
      ai: skills/modules/ai/skill-ai.yaml
      iot: skills/modules/iot/skill-iot.yaml
      mp: skills/modules/mp/skill-mp.yaml
      report: skills/modules/report/skill-report.yaml
  patterns:
    - path: skills/patterns/strategy-pattern.yaml
      reason: "策略模式 - 重构时可引入策略模式解耦"
    - path: skills/patterns/factory-pattern.yaml
      reason: "工厂模式 - 重构时可引入工厂模式管理对象"
  usage_hint: "改造前请务必阅读目标模块的 Skill 文档，了解现有架构"
---

# 改造模块场景提示词指南

> 本文档提供完整的提示词模板，用于指导 AI 改造现有模块的架构或逻辑。

## 目录

- [场景说明](#场景说明)
- [改造分析框架](#改造分析框架)
- [提示词模板](#提示词模板)
- [实际示例](#实际示例)
- [风险提示](#风险提示)
- [回滚策略](#回滚策略)

---

## 场景说明

### 何时需要改造模块

模块改造通常发生在以下场景：

| 改造类型 | 触发条件 | 典型示例 |
|---------|---------|---------|
| 重构代码结构 | 代码腐化、可维护性差 | 拆分大Service、提取公共组件 |
| 优化性能 | 响应慢、资源消耗高 | 优化数据库查询、引入缓存 |
| 更换技术栈 | 技术升级、框架迁移 | 升级Spring版本、更换ORM框架 |
| 修改业务逻辑 | 需求变更、规则调整 | 修改订单状态流转、调整审批流程 |
| 添加新特性 | 功能扩展、新需求 | 添加多租户支持、增加审计日志 |

### 改造前置条件

在发起改造前，请确认：

1. **已阅读目标模块的 Skill 文档**：了解模块的设计理念、架构设计、数据模型
2. **已识别改造范围**：明确需要修改的文件、表、接口
3. **已评估影响面**：了解上下游依赖关系
4. **已制定回滚方案**：确保可安全回退

---

## 改造分析框架

在编写改造提示词前，建议按以下框架进行分析：

### 一、现状分析

```
1. 当前架构
   - 模块分层结构
   - 核心类和接口
   - 数据表和关系

2. 存在问题
   - 性能瓶颈
   - 代码坏味道
   - 架构缺陷

3. 依赖关系
   - 上游调用方
   - 下游被调用方
   - 外部系统集成
```

### 二、目标分析

```
1. 改造目标
   - 要解决什么问题？
   - 期望达到什么效果？

2. 约束条件
   - 向后兼容性要求
   - 性能要求
   - 时间约束

3. 成功标准
   - 可量化的指标
   - 验收条件
```

### 三、方案设计

```
1. 改造方案
   - 具体实施步骤
   - 技术选型
   - 关键代码变更

2. 影响评估
   - 接口变更影响
   - 数据迁移影响
   - 配置变更影响

3. 风险预案
   - 潜在风险点
   - 应对措施
```

---

## 提示词模板

### 模板一：改造分析提示词

```markdown
# 改造分析任务

## 角色定义
你是一个资深的企业级 Java 应用架构师，精通 DDD 领域驱动设计和 Spring Boot 生态。

## 目标模块
模块名称：{模块名}
Skill 文档位置：skills/modules/{模块}/skill-{模块}.yaml

## 改造需求
{详细描述改造需求，包括：}
- 当前存在的问题
- 期望达到的目标
- 约束条件

## 分析要求

请按以下维度进行分析：

### 1. 现状分析
- 分析当前模块的架构设计（参考 Skill 文档的 architecture 部分）
- 识别与改造需求相关的核心类和接口
- 分析数据模型（参考 Skill 文档的 data_model 部分）

### 2. 影响范围评估
- 列出需要修改的文件清单
- 识别受影响的 API 接口（参考 Skill 文档的 communication.apis 部分）
- 识别受影响的上下游模块（参考 Skill 文档的 dependencies 部分）

### 3. 改造方案设计
- 提出改造方案（如涉及设计模式，参考 skills/patterns/ 目录）
- 给出关键代码变更示例
- 说明数据迁移方案（如需要）

### 4. 风险评估
- 列出潜在风险点
- 提出风险应对措施
- 评估改造优先级

## 输出格式

请按以下格式输出分析报告：

```yaml
analysis:
  current_state:
    architecture: "当前架构描述"
    core_components: ["核心组件列表"]
    data_model: "相关数据模型"

  impact_scope:
    files_to_modify: ["文件路径列表"]
    apis_affected: ["受影响的API列表"]
    modules_affected: ["受影响的模块列表"]

  solution:
    approach: "改造方案描述"
    key_changes:
      - file: "文件路径"
        change: "变更说明"
        code_example: |
          // 代码示例
    data_migration: "数据迁移方案（如需要）"

  risks:
    - risk: "风险描述"
      probability: "高/中/低"
      impact: "高/中/低"
      mitigation: "应对措施"

  priority: "P0/P1/P2"
```
```

### 模板二：代码改造提示词

```markdown
# 代码改造任务

## 改造背景
{描述改造背景，引用分析报告的关键结论}

## 目标模块 Skill 文档
{粘贴相关模块的 Skill 文档内容，或指定文件路径}

## 改造任务

### 任务一：{任务名称}
**目标**：{任务目标}
**涉及文件**：
- `{文件路径1}` - {变更说明}
- `{文件路径2}` - {变更说明}

**实现要求**：
1. 遵循项目代码规范（参考 Skill 文档的 code_patterns 部分）
2. 保持向后兼容性（如需要）
3. 添加必要的单元测试

**期望输出**：
- 完整的代码变更
- 变更说明

### 任务二：{任务名称}
{同上格式}

## 代码规范提醒

在编写代码时，请遵循以下规范：

### Controller 层
```java
@Tag(name = "管理后台 - XXX")
@RestController
@RequestMapping("/xxx")
@Validated
public class XxxController {
    // 使用 @PreAuthorize 进行权限控制
    // 使用 CommonResult 统一返回
}
```

### Service 层
```java
@Service
@Validated
public class XxxServiceImpl implements XxxService {
    // 使用 @Transactional 标记事务方法
    // 使用 @Resource 注入依赖
}
```

### 数据访问层
```java
@Mapper
public interface XxxMapper extends BaseMapperX<XxxDO> {
    // 使用 LambdaQueryWrapper 构建查询
}
```

### 异常处理
```java
// 使用统一错误码
throw exception(ERROR_CODE, params);
// 错误码格式：1-XXX-XXX-XXX
```

## 验证要求

请提供：
1. 关键代码的单元测试用例
2. 接口测试的请求示例
3. 数据迁移脚本（如需要）
```

### 模板三：影响评估提示词

```markdown
# 改造影响评估任务

## 改造内容
{描述具体的改造内容}

## 评估维度

### 1. API 兼容性评估
请分析：
- 哪些 API 接口签名会发生变化？
- 是否会导致调用方报错？
- 是否需要版本兼容处理？

### 2. 数据兼容性评估
请分析：
- 数据表结构是否需要变更？
- 历史数据是否需要迁移？
- 是否需要数据回填？

### 3. 配置兼容性评估
请分析：
- 是否需要新增配置项？
- 现有配置是否需要修改？
- 配置迁移方案是什么？

### 4. 性能影响评估
请分析：
- 改造对性能的影响（正面/负面）
- 是否需要性能测试？
- 预期性能指标是什么？

### 5. 运维影响评估
请分析：
- 是否需要重启服务？
- 是否需要停机维护？
- 发布顺序有什么要求？

## 输出格式

```yaml
compatibility_report:
  api:
    breaking_changes: ["破坏性变更列表"]
    compatible_changes: ["兼容性变更列表"]
    version_strategy: "版本兼容策略"

  data:
    schema_changes: ["表结构变更列表"]
    migration_required: true/false
    migration_script: "迁移脚本路径"

  configuration:
    new_configs: ["新增配置项列表"]
    modified_configs: ["修改配置项列表"]

  performance:
    impact: "正面/负面/无影响"
    test_required: true/false
    expected_metrics: "预期性能指标"

  operations:
    restart_required: true/false
    downtime_required: true/false
    deployment_sequence: ["发布顺序列表"]
```
```

### 模板四：改造计划生成提示词

```markdown
# 改造计划生成任务

## 改造需求
{描述改造需求}

## 分析报告
{引用或粘贴改造分析报告}

## 计划生成要求

请生成详细的改造实施计划，包括：

### 1. 任务分解
将改造任务分解为可执行的最小单元，每个任务包含：
- 任务名称
- 任务描述
- 涉及文件
- 预估工时
- 前置依赖

### 2. 实施顺序
确定任务执行顺序，考虑：
- 依赖关系
- 风险优先级
- 可验证性

### 3. 里程碑定义
定义关键里程碑：
- 里程碑名称
- 验收标准
- 预计完成时间

### 4. 回滚方案
为每个关键步骤制定回滚方案：
- 回滚触发条件
- 回滚操作步骤
- 数据恢复方案

## 输出格式

```yaml
refactor_plan:
  tasks:
    - id: "T001"
      name: "任务名称"
      description: "任务描述"
      files: ["涉及文件列表"]
      estimated_hours: 4
      dependencies: ["前置任务ID列表"]
      risks: ["风险列表"]
      rollback: "回滚方案"

  milestones:
    - name: "里程碑名称"
      tasks: ["包含的任务ID列表"]
      acceptance_criteria: "验收标准"

  execution_sequence:
    - phase: "阶段名称"
      tasks: ["任务ID列表"]
      duration: "预估时长"

  rollback_plan:
    trigger_conditions: ["触发条件列表"]
    steps: ["回滚步骤列表"]
    data_recovery: "数据恢复方案"
```
```

### 模板五：代码变更清单生成提示词

```markdown
# 代码变更清单生成任务

## 改造内容
{描述改造内容}

## 相关 Skill 文档
{指定相关模块的 Skill 文档路径}

## 生成要求

请生成完整的代码变更清单，按以下格式：

### 变更清单模板

```yaml
change_list:
  summary:
    total_files: 0
    new_files: 0
    modified_files: 0
    deleted_files: 0

  changes:
    # 新增文件
    - type: "NEW"
      path: "文件路径"
      purpose: "文件用途"
      module: "所属模块"
      layer: "所属层级（controller/service/dal等）"
      description: |
        详细描述文件内容
      dependencies: ["依赖的其他文件"]
      tests_required: true/false

    # 修改文件
    - type: "MODIFY"
      path: "文件路径"
      purpose: "修改目的"
      changes:
        - location: "变更位置（类名/方法名）"
          before: |
            修改前代码
          after: |
            修改后代码
          reason: "修改原因"
      compatibility: "兼容性说明"

    # 删除文件
    - type: "DELETE"
      path: "文件路径"
      reason: "删除原因"
      migration: "功能迁移去向"

  database_changes:
    - type: "DDL"
      sql: "SQL语句"
      purpose: "变更目的"
      rollback_sql: "回滚SQL"

  config_changes:
    - file: "配置文件路径"
      additions: ["新增配置项"]
      modifications: ["修改配置项"]
      deletions: ["删除配置项"]

  api_changes:
    - type: "NEW/MODIFY/DELETE"
      endpoint: "API路径"
      method: "HTTP方法"
      description: "变更说明"
      breaking: true/false
```
```

---

## 实际示例

### 示例一：将单模块拆分为微服务

**改造需求**：将 `yudao-module-pay` 支付模块拆分为独立的微服务。

**使用提示词**：

```markdown
# 改造分析任务

## 角色定义
你是一个资深的企业级 Java 应用架构师，精通 DDD 领域驱动设计和 Spring Cloud 微服务架构。

## 目标模块
模块名称：pay
Skill 文档位置：skills/modules/pay/skill-pay.yaml

## 改造需求
当前支付模块作为单体应用的一部分运行，需要拆分为独立的微服务，以实现：
1. 独立部署和扩展
2. 与其他业务模块解耦
3. 支持多团队并行开发

约束条件：
- 保持 API 接口向后兼容
- 最小化数据迁移
- 支持灰度发布

## 分析要求

请按以下维度进行分析：

### 1. 现状分析
参考 Skill 文档，分析当前模块的：
- 分层架构设计
- 核心服务组件
- 数据模型设计
- 模块间通信方式

### 2. 微服务拆分方案
- 定义服务边界
- 设计服务间通信方案
- 数据库拆分策略
- 分布式事务方案

### 3. 影响范围评估
- 列出受影响的 API 接口
- 识别需要修改的调用方
- 评估数据迁移工作量

### 4. 实施计划
- 分阶段实施步骤
- 灰度发布方案
- 回滚预案

## 输出格式
按模板一要求的 YAML 格式输出分析报告。
```

**预期分析输出**：

```yaml
analysis:
  current_state:
    architecture: |
      支付模块采用标准分层架构：
      - api层：PayOrderApi, PayRefundApi, PayWalletApi
      - controller层：PayOrderController, PayRefundController等
      - service层：PayOrderServiceImpl, PayRefundServiceImpl等
      - dal层：PayOrderMapper, PayRefundMapper等
      - framework层：PayClient工厂和策略实现

    core_components:
      - "PayClient: 支付客户端接口，支持多渠道策略"
      - "PayOrderService: 订单核心服务"
      - "PayRefundService: 退款核心服务"
      - "PayClientFactory: 客户端工厂"

    data_model: |
      核心表：pay_order, pay_refund, pay_channel, pay_app, pay_wallet
      关系：pay_app 1:N pay_channel 1:N pay_order 1:N pay_refund

  impact_scope:
    files_to_modify:
      - "pom.xml: 添加 Spring Cloud 依赖"
      - "application.yaml: 添加 Nacos 配置"
      - "PayOrderApi.java: 改为 Feign 接口"
      - "PayRefundApi.java: 改为 Feign 接口"

    apis_affected:
      - "PayOrderApi.createOrder: 调用方式从本地改为远程"
      - "PayRefundApi.createRefund: 调用方式从本地改为远程"
      - "PayWalletApi.addBalance: 需要考虑分布式事务"

    modules_affected:
      - "yudao-module-order: 通过 PayOrderApi 调用支付模块"
      - "yudao-module-member: 通过 PayWalletApi 调用钱包功能"

  solution:
    approach: |
      分阶段微服务拆分方案：
      阶段一：基础设施准备
      - 添加 Spring Cloud 依赖
      - 配置 Nacos 注册中心
      - 配置 Sentinel 限流熔断

      阶段二：API 层改造
      - 将 Api 接口改为 Feign 接口
      - 添加 fallback 降级处理
      - 保持接口签名不变

      阶段三：服务部署
      - 独立部署支付服务
      - 配置网关路由
      - 灰度发布验证

    key_changes:
      - file: "yudao-module-pay-api/pom.xml"
        change: "添加 Spring Cloud OpenFeign 依赖"
        code_example: |
          <dependency>
              <groupId>org.springframework.cloud</groupId>
              <artifactId>spring-cloud-starter-openfeign</artifactId>
          </dependency>

      - file: "PayOrderApi.java"
        change: "改为 Feign 接口"
        code_example: |
          @FeignClient(name = "pay-service", fallback = PayOrderApiFallback.class)
          public interface PayOrderApi {
              @PostMapping("/rpc/pay/order/create")
              CommonResult<Long> createOrder(@RequestBody PayOrderCreateReqDTO reqDTO);
          }

      - file: "PayOrderApiFallback.java"
        change: "新增降级处理类"
        code_example: |
          @Component
          public class PayOrderApiFallback implements PayOrderApi {
              @Override
              public CommonResult<Long> createOrder(PayOrderCreateReqDTO reqDTO) {
                  return CommonResult.error("支付服务不可用，请稍后重试");
              }
          }

    data_migration: |
      数据库无需迁移，保持现有表结构
      仅需配置独立的数据库连接

  risks:
    - risk: "分布式事务一致性问题"
      probability: "高"
      impact: "高"
      mitigation: "使用 Seata 分布式事务框架，或采用最终一致性方案"

    - risk: "服务间调用超时"
      probability: "中"
      impact: "中"
      mitigation: "配置合理的超时时间和重试策略，添加 fallback 降级处理"

    - risk: "灰度发布期间数据不一致"
      probability: "中"
      impact: "高"
      mitigation: "采用蓝绿部署，确保流量切换的原子性"

  priority: "P1"
```

---

### 示例二：优化数据库查询性能

**改造需求**：优化 `yudao-module-system` 模块中用户查询的性能问题。

**使用提示词**：

```markdown
# 性能优化改造任务

## 目标模块
模块名称：system
Skill 文档位置：skills/modules/system/skill-system.yaml

## 改造需求
当前用户列表查询接口响应慢（平均 2s+），需要优化：
- 问题现象：分页查询用户列表，关联部门名称显示，响应时间超过 2 秒
- 数据规模：用户表 10 万+ 数据，部门表 1000+ 数据
- 期望目标：响应时间降低到 200ms 以内

约束条件：
- 不能改变接口签名
- 不能影响数据权限功能

## 分析要求

### 1. 性能瓶颈分析
- 分析当前 SQL 执行计划
- 识别慢查询原因
- 评估索引使用情况

### 2. 优化方案设计
- 索引优化建议
- 查询语句优化
- 缓存策略设计

### 3. 影响评估
- 评估优化对现有功能的影响
- 评估缓存一致性问题

## 输出格式
按模板一要求的 YAML 格式输出分析报告。
```

**预期分析输出**：

```yaml
analysis:
  current_state:
    architecture: |
      用户查询流程：
      1. Controller 接收分页请求
      2. Service 调用 Mapper 查询用户列表
      3. Service 循环查询部门名称（N+1 问题）
      4. Convert 转换为 VO 返回

    core_components:
      - "AdminUserMapper: 用户数据访问"
      - "DeptApi: 部门信息查询"
      - "AdminUserServiceImpl: 用户业务逻辑"

    data_model: |
      system_users 表：10万+ 数据
      system_dept 表：1000+ 数据
      关联关系：system_users.dept_id -> system_dept.id

  impact_scope:
    files_to_modify:
      - "AdminUserMapper.java: 优化查询语句"
      - "AdminUserServiceImpl.java: 修改查询逻辑"
      - "AdminUserPageReqVO.java: 可能需要调整参数"

    apis_affected: []

    modules_affected: []

  solution:
    approach: |
      性能优化三步走：
      1. 索引优化：为 dept_id 添加索引
      2. 查询优化：改为 JOIN 查询，避免 N+1 问题
      3. 缓存优化：部门信息使用 Redis 缓存

    key_changes:
      - file: "AdminUserMapper.java"
        change: "优化分页查询，使用 JOIN 代替循环查询"
        code_example: |
          // 优化前：先查用户，再循环查部门
          // 优化后：JOIN 查询
          @Mapper
          public interface AdminUserMapper extends BaseMapperX<AdminUserDO> {

              default PageResult<AdminUserDO> selectPage(AdminUserPageReqVO reqVO) {
                  MPJLambdaWrapper<AdminUserDO> wrapper = new MPJLambdaWrapper<AdminUserDO>()
                      .selectAll(AdminUserDO.class)
                      .selectAs(DeptDO::getName, AdminUserDO::getDeptName)
                      .leftJoin(DeptDO.class, DeptDO::getId, AdminUserDO::getDeptId)
                      .likeIfPresent(AdminUserDO::getUsername, reqVO.getUsername())
                      .likeIfPresent(AdminUserDO::getNickname, reqVO.getNickname())
                      .eqIfPresent(AdminUserDO::getStatus, reqVO.getStatus())
                      .betweenIfPresent(AdminUserDO::getCreateTime, reqVO.getCreateTime())
                      .orderByDesc(AdminUserDO::getId);
                  return selectJoinPage(reqVO, AdminUserDO.class, wrapper);
              }
          }

      - file: "system_users 表索引"
        change: "添加 dept_id 索引"
        code_example: |
          -- 添加索引
          CREATE INDEX idx_dept_id ON system_users(dept_id);

          -- 复合索引（根据查询条件）
          CREATE INDEX idx_status_dept ON system_users(status, dept_id);

      - file: "DeptApiImpl.java"
        change: "添加 Redis 缓存"
        code_example: |
          @Service
          public class DeptApiImpl implements DeptApi {

              @Resource
              private DeptService deptService;

              @Cacheable(value = "dept", key = "#id")
              @Override
              public DeptRespDTO getDept(Long id) {
                  return deptService.getDept(id);
              }

              @Cacheable(value = "dept:list", key = "#ids.hashCode()")
              @Override
              public List<DeptRespDTO> getDeptList(Collection<Long> ids) {
                  return deptService.getDeptList(ids);
              }
          }

    data_migration: "无需数据迁移"

  risks:
    - risk: "JOIN 查询可能影响数据权限过滤"
      probability: "中"
      impact: "高"
      mitigation: "确保 @DataPermission 注解正确应用于新查询方法"

    - risk: "缓存一致性问题"
      probability: "中"
      impact: "中"
      mitigation: "部门修改时清除缓存 @CacheEvict"

    - risk: "索引创建期间锁表"
      probability: "低"
      impact: "中"
      mitigation: "在低峰期执行索引创建，或使用 ONLINE DDL"

  priority: "P0"

performance_optimization:
  before:
    response_time: "2000ms+"
    sql_count: "N+1"
    index_usage: "部分索引"

  after:
    response_time: "<200ms"
    sql_count: "1"
    index_usage: "完全索引"

  cache_strategy:
    type: "Redis + Spring Cache"
    ttl: "30 minutes"
    eviction: "on update"
```

---

### 示例三：添加多租户支持

**改造需求**：为 `yudao-module-pay` 支付模块添加多租户支持。

**使用提示词**：

```markdown
# 多租户改造任务

## 目标模块
模块名称：pay
Skill 文档位置：skills/modules/pay/skill-pay.yaml

## 改造需求
当前支付模块不支持多租户，需要改造以支持：
1. 租户数据隔离：不同租户的支付订单完全隔离
2. 租户配置隔离：不同租户可配置不同的支付渠道
3. 租户统计独立：各租户独立的订单统计

约束条件：
- 兼容现有单租户部署模式
- 保持 API 接口不变
- 历史数据需要迁移

## 分析要求

### 1. 多租户架构分析
- 参考 system 模块的 TenantBaseDO 实现
- 分析哪些表需要租户隔离
- 分析哪些数据不需要租户隔离

### 2. 改造方案设计
- 实体类改造
- Mapper 改造
- Service 层改造
- 数据迁移方案

### 3. 影响评估
- API 接口影响
- 数据迁移影响
- 配置变更影响

## 输出格式
按模板一要求的 YAML 格式输出分析报告。
```

**预期分析输出**：

```yaml
analysis:
  current_state:
    architecture: |
      支付模块当前不支持多租户：
      - 所有 DO 继承 BaseDO（不含 tenant_id）
      - 无租户上下文传递
      - 无租户数据隔离

    core_components:
      - "PayOrderDO: 支付订单实体"
      - "PayChannelDO: 支付渠道配置实体"
      - "PayAppDO: 支付应用实体"

    data_model: |
      核心表均无 tenant_id 字段：
      pay_order, pay_refund, pay_channel, pay_app, pay_wallet

  impact_scope:
    files_to_modify:
      # 实体类改造
      - "PayOrderDO.java: 继承 TenantBaseDO"
      - "PayRefundDO.java: 继承 TenantBaseDO"
      - "PayChannelDO.java: 继承 TenantBaseDO"
      - "PayAppDO.java: 继承 TenantBaseDO"
      - "PayWalletDO.java: 继承 TenantBaseDO"

      # 数据迁移
      - "新增数据迁移脚本"

      # 配置文件
      - "application.yaml: 添加多租户配置"

    apis_affected: []
    # API 接口签名不变，租户上下文通过 Header 传递

    modules_affected:
      - "yudao-module-system: 提供租户上下文"

  solution:
    approach: |
      多租户改造四步走：
      1. 实体类改造：DO 继承 TenantBaseDO
      2. 数据库改造：添加 tenant_id 字段
      3. 历史数据迁移：为现有数据分配租户
      4. 测试验证：确保数据隔离正确

    key_changes:
      - file: "PayOrderDO.java"
        change: "继承 TenantBaseDO"
        code_example: |
          // 改造前
          @TableName("pay_order")
          @Data
          @EqualsAndHashCode(callSuper = true)
          public class PayOrderDO extends BaseDO {
              // ...
          }

          // 改造后
          @TableName("pay_order")
          @Data
          @EqualsAndHashCode(callSuper = true)
          public class PayOrderDO extends TenantBaseDO {
              // ...
          }

      - file: "PayChannelDO.java"
        change: "继承 TenantBaseDO"
        code_example: |
          // 支付渠道配置需要租户隔离
          @TableName("pay_channel")
          @Data
          @EqualsAndHashCode(callSuper = true)
          public class PayChannelDO extends TenantBaseDO {
              // ...
          }

      - file: "数据库迁移脚本"
        change: "添加 tenant_id 字段"
        code_example: |
          -- 为所有表添加 tenant_id 字段
          ALTER TABLE pay_order ADD COLUMN tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '租户编号';
          ALTER TABLE pay_refund ADD COLUMN tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '租户编号';
          ALTER TABLE pay_channel ADD COLUMN tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '租户编号';
          ALTER TABLE pay_app ADD COLUMN tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '租户编号';
          ALTER TABLE pay_wallet ADD COLUMN tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '租户编号';

          -- 添加索引
          ALTER TABLE pay_order ADD INDEX idx_tenant_id (tenant_id);
          ALTER TABLE pay_refund ADD INDEX idx_tenant_id (tenant_id);
          ALTER TABLE pay_channel ADD INDEX idx_tenant_id (tenant_id);
          ALTER TABLE pay_app ADD INDEX idx_tenant_id (tenant_id);
          ALTER TABLE pay_wallet ADD INDEX idx_tenant_id (tenant_id);

          -- 历史数据迁移（假设默认租户ID为1）
          UPDATE pay_order SET tenant_id = 1 WHERE tenant_id IS NULL;
          UPDATE pay_refund SET tenant_id = 1 WHERE tenant_id IS NULL;
          UPDATE pay_channel SET tenant_id = 1 WHERE tenant_id IS NULL;
          UPDATE pay_app SET tenant_id = 1 WHERE tenant_id IS NULL;
          UPDATE pay_wallet SET tenant_id = 1 WHERE tenant_id IS NULL;

    data_migration: |
      数据迁移步骤：
      1. 创建数据库备份
      2. 添加 tenant_id 字段（允许 NULL）
      3. 为历史数据设置默认租户ID
      4. 设置 NOT NULL 约束
      5. 添加索引
      6. 验证数据完整性

  risks:
    - risk: "数据迁移期间服务不可用"
      probability: "高"
      impact: "高"
      mitigation: "选择低峰期执行，预估迁移时间，提前通知用户"

    - risk: "历史数据租户归属不明确"
      probability: "中"
      impact: "高"
      mitigation: "与业务方确认历史数据归属，制定明确的数据分配规则"

    - risk: "跨租户数据泄露"
      probability: "低"
      impact: "高"
      mitigation: "严格测试租户隔离，添加集成测试用例"

    - risk: "性能下降（tenant_id 过滤）"
      probability: "低"
      impact: "中"
      mitigation: "为 tenant_id 添加索引，确保查询计划使用索引"

  priority: "P1"

tenant_isolation_strategy:
  implementation: "TenantLineInnerInterceptor (MyBatis-Plus)"
  context_propagation: "TenantContextHolder (ThreadLocal)"
  header_name: "tenant-id"

tables_to_isolate:
  - "pay_order"
  - "pay_refund"
  - "pay_channel"
  - "pay_app"
  - "pay_wallet"
  - "pay_wallet_transaction"
  - "pay_transfer"

tables_to_ignore:
  # 以下表不需要租户隔离
  - "pay_notify_task"  # 通知任务按业务隔离即可
```

---

## 风险提示

### 高风险场景

| 风险场景 | 风险等级 | 应对措施 |
|---------|---------|---------|
| 修改核心数据表结构 | 高 | 必须有数据备份和回滚脚本 |
| 修改对外 API 签名 | 高 | 版本兼容处理，渐进式迁移 |
| 分布式事务改造 | 高 | 充分测试，准备补偿方案 |
| 大规模数据迁移 | 高 | 分批迁移，灰度验证 |

### 中风险场景

| 风险场景 | 风险等级 | 应对措施 |
|---------|---------|---------|
| 引入新依赖 | 中 | 评估依赖稳定性，锁定版本 |
| 性能优化改造 | 中 | 性能基准测试，监控告警 |
| 缓存策略变更 | 中 | 缓存穿透/雪崩预案 |
| 定时任务改造 | 中 | 幂等性设计，失败重试 |

### 风险检查清单

在执行改造前，请逐项检查：

```markdown
## 改造前检查清单

### 代码层面
- [ ] 已阅读目标模块的 Skill 文档
- [ ] 已识别所有需要修改的文件
- [ ] 已评估对现有测试用例的影响
- [ ] 已准备新的测试用例

### 数据层面
- [ ] 已备份相关数据表
- [ ] 已准备数据迁移脚本
- [ ] 已准备数据回滚脚本
- [ ] 已评估数据迁移时间

### 接口层面
- [ ] 已确认 API 兼容性
- [ ] 已通知调用方（如有破坏性变更）
- [ ] 已准备 API 文档更新

### 运维层面
- [ ] 已制定发布计划
- [ ] 已准备回滚方案
- [ ] 已配置监控告警
- [ ] 已通知相关干系人
```

---

## 回滚策略

### 回滚原则

1. **快速回滚优先**：优先恢复服务可用性，再排查问题
2. **数据优先保护**：回滚代码前，确保数据可恢复
3. **分步回滚**：按依赖关系逆序回滚

### 回滚方案模板

```yaml
rollback_plan:
  # 基本信息meta:
    change_id: "CHANGE-001"
    change_name: "XXX改造"
    rollback_owner: "负责人"

  # 回滚触发条件trigger_conditions:
    - "服务错误率超过 5%"
    - "接口响应时间超过 5s"
    - "出现数据不一致问题"
    - "核心功能不可用"

  # 回滚步骤steps:
    # 第一阶段：流量切换
    - phase: "流量切换"
      order: 1
      actions:
        - action: "切换流量到旧版本服务"
          command: "kubectl rollout undo deployment/xxx-service"
          verify: "kubectl get pods -l app=xxx-service"
          timeout: "60s"

      rollback_point: "流量切换完成"

    # 第二阶段：代码回滚
    - phase: "代码回滚"
      order: 2
      actions:
        - action: "回滚代码到上一版本"
          command: "git revert <commit-hash>"
          verify: "git log -1"
          timeout: "30s"

        - action: "重新构建部署"
          command: "mvn clean package && kubectl apply -f deployment.yaml"
          verify: "kubectl get pods -l app=xxx-service"
          timeout: "300s"

      rollback_point: "代码回滚完成"

    # 第三阶段：数据回滚
    - phase: "数据回滚"
      order: 3
      condition: "涉及数据变更时执行"
      actions:
        - action: "执行数据回滚脚本"
          command: "mysql -h host -u user -p < rollback.sql"
          verify: "SELECT COUNT(*) FROM xxx_table"
          timeout: "600s"

        - action: "清除缓存"
          command: "redis-cli FLUSHDB"
          verify: "redis-cli DBSIZE"
          timeout: "30s"

      rollback_point: "数据回滚完成"

  # 验证步骤verification:
    - "服务健康检查通过"
    - "核心接口调用成功"
    - "监控指标恢复正常"
    - "数据一致性校验通过"

  # 数据恢复脚本data_recovery:
    file: "rollback/V20240318__rollback_xxx.sql"
    content: |
      -- 回滚表结构变更
      ALTER TABLE xxx_table DROP COLUMN new_column;

      -- 恢复数据
      UPDATE xxx_table SET status = old_status WHERE id IN (SELECT id FROM backup_table);

  # 联系人contacts:
    - name: "技术负责人"
      phone: "138xxxxxxxx"
    - name: "DBA"
      phone: "139xxxxxxxx"
    - name: "运维负责人"
      phone: "137xxxxxxxx"
```

### 数据回滚脚本模板

```sql
-- =====================================================
-- 数据回滚脚本
-- 变更ID: CHANGE-001
-- 变更名称: XXX改造
-- 创建时间: 2024-03-18
-- 执行前请先备份数据
-- =====================================================

-- 开启事务
START TRANSACTION;

-- 1. 回滚表结构变更（如需要）
-- ALTER TABLE xxx_table DROP COLUMN new_column;

-- 2. 恢复数据（如有数据迁移）
-- 方式一：从备份表恢复
-- INSERT INTO xxx_table SELECT * FROM xxx_table_backup_20240318;

-- 方式二：执行反向更新
-- UPDATE xxx_table SET status = 0 WHERE status = 1;

-- 3. 清理临时数据
-- DROP TABLE IF EXISTS xxx_table_backup_20240318;

-- 验证数据
SELECT COUNT(*) AS total_count FROM xxx_table;
-- SELECT SUM(amount) AS total_amount FROM xxx_table;

-- 确认无误后提交
-- COMMIT;

-- 如有问题，执行回滚
-- ROLLBACK;
```

### 回滚演练检查清单

```markdown
## 回滚演练检查清单

### 演练前准备
- [ ] 已准备回滚脚本并验证语法
- [ ] 已准备数据备份
- [ ] 已通知相关干系人
- [ ] 已准备监控大盘

### 演练执行
- [ ] 执行代码回滚
- [ ] 执行数据回滚（如需要）
- [ ] 执行配置回滚（如需要）
- [ ] 验证服务可用性
- [ ] 验证数据一致性

### 演练后总结
- [ ] 记录回滚耗时
- [ ] 记录遇到的问题
- [ ] 优化回滚脚本
- [ ] 更新文档
```

---

## 附录

### 相关文档

- [模块 Skill 文档位置](../modules/)
- [设计模式文档](../patterns/)
- [Skill 模板](../templates/)
- [Skill 索引](../index.yaml)

### 参考命令

```bash
# 查看 Skill 文档
cat skills/modules/{module}/skill-{module}.yaml

# 查看设计模式文档
cat skills/patterns/{pattern}-pattern.yaml

# 数据库备份
mysqldump -h host -u user -p database > backup_$(date +%Y%m%d).sql

# 数据库恢复
mysql -h host -u user -p database < backup_20240318.sql

# Git 回滚
git log --oneline -10
git revert <commit-hash>
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-18
**维护者**: 技术文档团队