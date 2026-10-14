# CRUD 代码生成 Skill

> 整合性入口指南 —— 引用已有的模板文档

## 元信息

- **ID**：`crud-generator`
- **名称**：CRUD 代码生成
- **版本**：`1.0.0`
- **分类**：`design`
- **描述**：根据数据库表结构自动生成符合 yudao 项目规范完整 CRUD 功能代码
- **创建日期**：`2026-03-31`
- **更新日期**：`2026-03-31`

## 第一部分：触发条件

### 命令

- `/crud-gen`
- `/generate-crud`

### 关键词

- 生成 CRUD
- 创建实体代码
- 生成增删改查
- 实体类实现

### 事件

| 事件名 | 条件 |
|--------|------|
| `table_created` | 数据库表创建完成 |

## 第二部分：输入参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 | 示例 |
|--------|------|------|--------|------|------|
| `module` | string | 是 | — | 模块编码（`system`/`infra`/`pay`/`mes` 等） | `system`、`infra`、`pay`、`mes` |
| `feature` | string | 是 | — | 功能编码（`user`/`order`/`process` 等） | `user`、`order`、`process` |
| `entity_name` | string | 是 | — | 实体名称（中文） | `用户`、`订单`、`工序` |
| `entity_class` | string | 是 | — | 实体类名（英文，首字母大写） | `User`、`Order`、`Process` |
| `table_name` | string | 是 | — | 数据库表名 | `system_user`、`pay_order`、`mes_process` |
| `is_tenant` | boolean | 否 | `true` | 是否多租户实体（`true` 使用 `TenantBaseDO`，`false` 使用 `BaseDO`） | — |
| `fields` | array | 是 | — | 业务字段列表 | — |
| `enable_export` | boolean | 否 | `false` | 是否启用 Excel 导出功能 | — |
| `enable_import` | boolean | 否 | `false` | 是否启用 Excel 导入功能 | — |
| `enable_batch` | boolean | 否 | `true` | 是否启用批量删除功能 | — |

### `fields` item schema

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 字段名 |
| `type` | string | 是 | 字段类型 |
| `required` | boolean | 是 | 是否必填 |
| `description` | string | 是 | 描述 |

## 第三部分：执行流程（5 阶段）

CRUD 代码生成按以下 5 个阶段顺序执行：

### 阶段 1：结构分析

- **时长**：5min
- **描述**：分析表结构，确定实体属性和生成范围
- **步骤**：
  - **解析表名和字段定义**：读取表结构信息，提取字段列表
  - **确定 DO 基类**：根据 `is_tenant` 参数选择 `BaseDO` 或 `TenantBaseDO`
    - `is_tenant=true` → `TenantBaseDO`（含 `tenantId`）
    - `is_tenant=false` → `BaseDO`
  - **生成文件清单**：根据参数确定需要创建的文件列表

#### 文件清单决策表

| 条件 | 文件 |
|------|------|
| 默认 | `DO`、`Mapper`、`Service`、`ServiceImpl`、`Controller`、`SaveReqVO`、`PageReqVO`、`RespVO` |
| `enable_export=true` | 额外：`ExcelVO`、`export-excel` 接口 |
| `enable_import=true` | 额外：`ImportExcelVO`、`ImportRespVO`、`import` 接口 |
| `enable_batch=true` | 额外：`delete-list` 接口 |

- **分配错误码编号**：根据模块编号分配错误码段，参考 `api-designer.md` 第六部分 `module_codes`

### 阶段 2：VO 生成

- **时长**：5min
- **描述**：生成请求和响应 VO 类
- **参考**：`entity-implementation.md` 第 3.6 节
- **步骤**：

| 步骤 | 描述 | 模板路径 | 规则 |
|------|------|----------|------|
| 生成 `SaveReqVO` | 新增/修改共用请求对象 | `entity-implementation.md` 第 621-657 行 | 包含 `id` 字段（修改时必填）；包含所有可创建/更新字段；排除 `creator`、`createTime`、`updater`、`updateTime`、`deleted`、`tenantId`；添加校验注解（`@NotBlank`/`@NotNull`/`@Size`） |
| 生成 `PageReqVO` | 分页查询请求对象 | `entity-implementation.md` 第 661-695 行 | 继承 `PageParam`；包含常用查询条件字段；时间字段使用 `@DateTimeFormat` |
| 生成 `RespVO` | 响应对象 | `entity-implementation.md` 第 699-733 行 | 包含所有展示字段；包含 `createTime` 等只读字段 |
| 生成 `ExcelVO`（可选） | Excel 导出对象 | `entity-implementation.md` 第 737-773 行 | 当 `enable_export=true` 或 `enable_import=true` 时生成 |

### 阶段 3：DAL 生成

- **时长**：3min
- **描述**：生成数据访问层代码
- **参考**：`entity-implementation.md` 第 3.2-3.3 节
- **步骤**：

| 步骤 | 模板路径 | 规则 |
|------|----------|------|
| 生成 DO 实体类 | `entity-implementation.md` 第 128-180 行 | `@TableName` 指定表名；`@TableId` 标注主键；继承正确基类；枚举字段添加引用注释 |
| 生成 Mapper 接口 | `entity-implementation.md` 第 234-281 行 | 继承 `BaseMapperX<EntityDO>`；定义 `selectPage` 分页查询方法；使用 `LambdaQueryWrapperX` 构建条件；使用 `xxxIfPresent()` 方法链 |

### 阶段 4：Service 生成

- **时长**：5min
- **描述**：生成业务逻辑层代码
- **参考**：`entity-implementation.md` 第 3.4 节
- **步骤**：

#### 生成 Service 接口

- **模板路径**：`entity-implementation.md` 第 313-377 行
- **方法**：

| 方法 | 签名 |
|------|------|
| `createXxx(SaveReqVO)` | → `Long` |
| `updateXxx(SaveReqVO)` | → `void` |
| `deleteXxx(Long id)` | → `void` |
| `getXxx(Long id)` | → `XxxDO` |
| `getXxxPage(PageReqVO)` | → `PageResult<XxxDO>` |

#### 生成 ServiceImpl 实现

- **模板路径**：`entity-implementation.md` 第 382-485 行
- **规则**：
  - `@Service` + `@Validated` 注解
  - 新增方法校验唯一性
  - 更新/删除方法校验存在性
  - 使用 `exception(ERROR_CODE)` 抛异常
  - 使用 `BeanUtils.toBean()` 转换对象

### 阶段 5：Controller 生成

- **时长**：7min
- **描述**：生成 HTTP 接口层代码
- **参考**：`api-designer.md` 第七部分
- **步骤**：

#### 生成 Controller 类

- **模板路径**：`api-designer.md` 第 420-511 行
- **注解**：
  - `@Tag(name = '管理后台 - {实体名称}')`
  - `@RestController`
  - `@RequestMapping('/{module}/{feature}')`
  - `@Validated`

#### 生成标准端点

| 端点 | 方法 | 模板路径 |
|------|------|----------|
| `/create` | `POST` | `api-designer.md` 第 67-72 行 |
| `/update` | `PUT` | `api-designer.md` 第 74-79 行 |
| `/delete` | `DELETE` | `api-designer.md` 第 81-87 行 |
| `/get` | `GET` | `api-designer.md` 第 97-103 行 |
| `/page` | `GET` | `api-designer.md` 第 105-110 行 |

#### 生成扩展端点（可选）

| 条件 | 端点 | 模板路径 |
|------|------|----------|
| `enable_batch=true` | `/delete-list` | `api-designer.md` 第 523-531 行 |
| `enable_export=true` | `/export-excel` | `api-designer.md` 第 119-126 行 |
| `enable_import=true` | `/get-import-template`、`/import` | `api-designer.md` 第 534-557 行 |

- **生成权限 SQL**：参考 `api-designer.md` 第 333-344 行

## 第四部分：输出产物

- **基础路径**：`yudao-module-{module}-biz/src/main/java/cn/iocoder/yudao/module/{module}`

### 产物清单

#### DAL 层

| 名称 | 路径 | 描述 |
|------|------|------|
| DO 实体类 | `dal/dataobject/{feature}/{Entity}DO.java` | 数据库实体映射类 |
| Mapper 接口 | `dal/mysql/{feature}/{Entity}Mapper.java` | 数据访问接口 |

#### Service 层

| 名称 | 路径 | 描述 |
|------|------|------|
| Service 接口 | `service/{feature}/{Entity}Service.java` | 业务服务接口 |
| Service 实现 | `service/{feature}/{Entity}ServiceImpl.java` | 业务服务实现类 |

#### Controller 层

| 名称 | 路径 | 描述 |
|------|------|------|
| Controller | `controller/admin/{feature}/{Entity}Controller.java` | HTTP API 控制器 |

#### VO 类

| 名称 | 路径 | 描述 |
|------|------|------|
| `SaveReqVO` | `controller/admin/{feature}/vo/{Entity}SaveReqVO.java` | 新增/修改请求对象 |
| `PageReqVO` | `controller/admin/{feature}/vo/{Entity}PageReqVO.java` | 分页查询请求对象 |
| `RespVO` | `controller/admin/{feature}/vo/{Entity}RespVO.java` | 响应对象 |

#### 可选产物

| 名称 | 路径 | 条件 | 描述 |
|------|------|------|------|
| `ExcelVO` | `controller/admin/{feature}/vo/{Entity}ExcelVO.java` | `enable_export=true` | Excel 导出对象 |
| `ImportExcelVO` | `controller/admin/{feature}/vo/{Entity}ImportExcelVO.java` | `enable_import=true` | Excel 导入对象 |
| `ImportRespVO` | `controller/admin/{feature}/vo/{Entity}ImportRespVO.java` | `enable_import=true` | 导入结果响应 |

#### 配置文件

| 名称 | 路径 | 动作 | 描述 |
|------|------|------|------|
| 错误码定义 | `enums/ErrorCodeConstants.java` | 追加 | 业务错误码定义 |
| 权限配置 SQL | `sql/menu/{module}_{feature}_menu.sql` | — | 菜单和按钮权限 SQL |

## 第五部分：命名规范速查

### 文件命名

| 类型 | 格式 |
|------|------|
| DO | `{Entity}DO` |
| Mapper | `{Entity}Mapper` |
| Service | `{Entity}Service` |
| ServiceImpl | `{Entity}ServiceImpl` |
| Controller | `{Entity}Controller` |
| `SaveReqVO` | `{Entity}SaveReqVO` |
| `PageReqVO` | `{Entity}PageReqVO` |
| `RespVO` | `{Entity}RespVO` |
| `ExcelVO` | `{Entity}ExcelVO` |
| `ImportExcelVO` | `{Entity}ImportExcelVO` |

### 权限标识

- **格式**：`{module}:{feature}:{operation}`
- **操作**：`query`、`create`、`update`、`delete`、`export`、`import`
- **示例**：`system:user:create`

### 错误码

- **格式**：`1_{module_code}_{feature_code}_{seq}`
- **示例**：`1_002_001_000`

#### 模块段号速查（已按各模块源码 ErrorCodeConstants.java 核对，2026-10-14）

| 模块 | 段号 | 备注 |
|------|------|------|
| `infra` | `001` | — |
| `system` | `002` | — |
| `report` | `003` | — |
| `member` | `004` | — |
| `mp` | `006` | — |
| `pay` | `007` | — |
| `product` | `008` | — |
| `bpm` | `009` | — |
| `trade` | `011` | — |
| `promotion` | `013` | — |
| `crm` | `020` | — |
| `erp` | `030` | `erp` 段号；文件内另有 31 条 `1_020_` 残留（来自 crm 子段），CRUD 生成时以 `030` 为准 |
| `ai` | `040` | `040` 段现被 `ai`/`mes`/`im` 共用（源码现状），新模块勿再占用，待拆分 |
| `mes` | `040` | 同上 |
| `im` | `040` | 同上 |
| `iot` | `050` | `050` 段现被 `iot`/`hrm` 共用（源码现状），新模块勿再占用，待拆分 |
| `hrm` | `050` | 同上 |
| `iot-gateway` | `051` | — |
| `fms` | `052` | — |
| `pms` | `053` | — |
| `oa` | `054` | — |
| `wms` | `060` | — |

### 数据库表名

- **格式**：`{module}_{feature}`
- **示例**：`system_user`

## 第六部分：关联文档引用

### 主要文档

| 路径 | 描述 | 相关章节 |
|------|------|----------|
| `skills/design/api-designer.md` | API 设计规范、Controller 模板、权限标识、错误码体系 | 第二部分：接口规范（标准端点定义）；第五部分：权限标识规范；第六部分：错误码体系；第七部分：Controller 模板 |
| `skills/usage/entity-implementation.md` | 实体类实现完整流程、各层代码模板 | 3.2 节：DO 实体类模板；3.3 节：Mapper 层模板；3.4 节：Service 层模板；3.5 节：Controller 层模板；3.6 节：VO 类模板；3.7 节：错误码定义；3.8 节：权限配置 SQL |
| `skills/design/db-designer.md` | 数据库表结构设计规范（前置依赖） | — |

### 次要文档

| 路径 | 关系 | 描述 | 示例 |
|------|------|------|------|
| `docs/{module}/code-patterns.md` | 模块参考 | 具体模块的技术规范和扩展指南 | `docs/modules/system/code-patterns.md` |

## 第七部分：质量检查清单

### 生成前

| 检查项 | 校验内容 |
|--------|----------|
| 确认模块编码正确 | `module` 参数在 `module_codes` 中有对应编号 |
| 确认表名符合命名规范 | 表名格式为 `{module}_{feature}` |
| 阅读对应模块的 skill 文档 | 参考 `docs/{module}/code-patterns.md` |
| 确认字段类型映射正确 | 数据库类型与 Java 类型对应 |

### 生成中

| 检查项 | 校验内容 |
|--------|----------|
| DO 类继承正确基类 | `TenantBaseDO`（多租户）或 `BaseDO`（单租户） |
| Mapper 使用 `BaseMapperX` 和 `LambdaQueryWrapperX` | 继承 `BaseMapperX`，条件构建使用 `xxxIfPresent()` |
| Service 包含业务校验方法 | 新增校验唯一性，更新/删除校验存在性 |
| Controller 注解完整 | `@Tag`/`@RestController`/`@RequestMapping`/`@Validated` |
| 接口方法注解完整 | `@Operation`/`@PreAuthorize`/`@Parameter` |

### 生成后

| 检查项 | 校验内容 |
|--------|----------|
| 错误码编号符合规范 | 格式 `1_{module_code}_{feature_code}_{seq}` |
| 权限标识格式正确 | 格式 `{module}:{feature}:{operation}` |
| 所有文件包路径正确 | 基础路径 `cn.iocoder.yudao.module.{module}` |
| VO 类添加 `@Schema` 注解 | 所有字段有 `description` |
| 导入语句无缺失 | 所有注解有对应 import |

## 第八部分：与原 skill 的差异调整

### 命名规范调整

| 原命名 | 目标命名 | 原因 |
|--------|----------|------|
| `CreateDTO` | `XxxSaveReqVO` | yudao 系统新增/修改共用一个 VO |
| `UpdateDTO` | `XxxSaveReqVO` | 与 `CreateDTO` 合并，通过 `id` 字段区分 |
| `QueryDTO` | `XxxPageReqVO` | yudao 系统分页查询 VO 继承 `PageParam` |
| `VO` | `XxxRespVO` | 响应对象命名规范 |
| `ListVO` | `XxxRespVO` | 分页列表使用同一响应 VO |

### 技术栈调整

| 原技术 | 目标技术 | 原因 |
|--------|----------|------|
| `BaseMapper<Entity>` | `BaseMapperX<XxxDO>` | yudao 扩展的 Mapper 基类 |
| `LambdaQueryWrapper` | `LambdaQueryWrapperX` | 支持 `xxxIfPresent()` 简化条件构建 |
| `Result<T>` | `CommonResult<T>` | yudao 统一响应包装类 |
| `Page<T>` | `PageResult<T>` | yudao 分页结果类 |
| `@Api (Swagger 2)` | `@Tag (OpenAPI 3)` | Swagger 版本升级 |
| `@ApiOperation` | `@Operation` | OpenAPI 3.0 注解 |

### 目录结构调整

| 原路径 | 目标路径 |
|--------|----------|
| `controller/{Entity}Controller.java` | `controller/admin/{feature}/{Entity}Controller.java` |
| `dto/{Entity}DTO.java` | `controller/admin/{feature}/vo/{Entity}VO.java` |
| `mapper/{Entity}Mapper.java` | `dal/mysql/{feature}/{Entity}Mapper.java` |
| `entity/{Entity}.java` | `dal/dataobject/{feature}/{Entity}DO.java` |

## 快速参考

### 标准端点

| 端点 | 说明 |
|------|------|
| `POST /create` | 创建 → `CommonResult<Long>` |
| `PUT /update` | 更新 → `CommonResult<Boolean>` |
| `DELETE /delete` | 删除 → `CommonResult<Boolean>` |
| `GET /get` | 详情 → `CommonResult<XxxRespVO>` |
| `GET /page` | 分页 → `CommonResult<PageResult<XxxRespVO>>` |
| `DELETE /delete-list` | 批量删除 → `CommonResult<Boolean>` |
| `GET /export-excel` | 导出 → `void` |
| `POST /import` | 导入 → `CommonResult<XxxImportRespVO>` |

### 权限操作

| 操作 | 说明 |
|------|------|
| `query` | 查询（get/page/list） |
| `create` | 新增 |
| `update` | 修改 |
| `delete` | 删除 |
| `export` | 导出 |
| `import` | 导入 |

### 基类选择

| 基类 | 使用场景 |
|------|----------|
| `BaseDO` | 单租户场景 —— `creator`/`createTime`/`updater`/`updateTime`/`deleted` |
| `TenantBaseDO` | 多租户场景 —— 额外含 `tenantId` |

### Mapper 方法

| 方法 | 用途 |
|------|------|
| `selectPage` | 分页查询 |
| `selectOne` | 查询单条 |
| `selectList` | 查询列表 |
| `insert` | 插入 |
| `updateById` | 更新 |
| `deleteById` | 删除 |
