# API 设计规范

> API 设计规范知识库：定义项目 REST API 的设计规范，包括接口命名、请求响应格式、权限控制、文档注解等，确保 API 设计的统一性和规范性

## 元信息

- **ID**：`api-designer`
- **名称**：API 设计规范
- **分类**：设计规范

## 第一部分：设计原则

### 设计原则 1：操作式 URL 设计

- **描述**：使用动词表达操作意图，而非 RESTful 资源式命名
- **示例**：`/system/user/create` 而非 `POST /users`

### 设计原则 2：统一响应格式

- **描述**：所有接口使用 `CommonResult` 包装，确保响应格式一致

### 设计原则 3：权限分级控制

- **描述**：通过 `@PermitAll` 和 `@PreAuthorize` 实现公开接口与权限接口的分离

### 设计原则 4：文档即代码

- **描述**：使用 OpenAPI 3.0 注解，接口文档与代码同步维护

## 第二部分：接口规范

### URL 命名规范

- **格式**：`/{模块}/{功能}/{操作}`
- **规则**：
  - 模块名与功能名使用小写字母
  - 操作名使用动词或动词短语
  - 多词使用连字符分隔（如 `update-status`）
- **示例**：

| 路径 | 描述 |
|------|------|
| `/system/user/create` | 创建用户 |
| `/system/user/page` | 用户分页列表 |
| `/pay/order/get` | 获取订单详情 |
| `/system/user/update-status` | 更新用户状态 |

### HTTP 方法映射

| 方法 | 操作 | 描述 | 幂等 |
|------|------|------|------|
| `POST` | create、import、send、login、logout | 创建类操作 | 否 |
| `PUT` | update、update-status、update-password | 更新类操作 | 是 |
| `DELETE` | delete、delete-list | 删除类操作 | 是 |
| `GET` | get、page、list、export-excel、get-import-template | 查询类操作（safe） | 是 |

### 标准端点定义

#### `/create`

- **方法**：`POST`
- **目的**：创建单个实体
- **请求**：`@RequestBody @Valid XxxSaveReqVO`
- **响应**：`CommonResult<Long>`
- **权限**：`{模块}:{功能}:create`

#### `/update`

- **方法**：`PUT`
- **目的**：更新单个实体
- **请求**：`@RequestBody @Valid XxxSaveReqVO`
- **响应**：`CommonResult<Boolean>`
- **权限**：`{模块}:{功能}:update`

#### `/delete`

- **方法**：`DELETE`
- **目的**：删除单个实体
- **请求**：`@RequestParam("id") Long id`
- **响应**：`CommonResult<Boolean>`
- **权限**：`{模块}:{功能}:delete`
- **参数注解**：`@Parameter(name = "id", description = "编号", required = true)`

#### `/delete-list`

- **方法**：`DELETE`
- **目的**：批量删除实体
- **请求**：`@RequestParam("ids") List<Long> ids`
- **响应**：`CommonResult<Boolean>`
- **权限**：`{模块}:{功能}:delete`
- **参数注解**：`@Parameter(name = "ids", description = "编号列表", required = true)`

#### `/get`

- **方法**：`GET`
- **目的**：获取单个实体详情
- **请求**：`@RequestParam("id") Long id`
- **响应**：`CommonResult<XxxRespVO>`
- **权限**：`{模块}:{功能}:query`
- **参数注解**：`@Parameter(name = "id", description = "编号", required = true)`

#### `/page`

- **方法**：`GET`
- **目的**：分页查询列表
- **请求**：`@Valid XxxPageReqVO`
- **响应**：`CommonResult<PageResult<XxxRespVO>>`
- **权限**：`{模块}:{功能}:query`

#### `/list`

- **方法**：`GET`
- **目的**：列表查询（不分页）
- **请求**：`@RequestParam("ids") List<Long>` 或无参数
- **响应**：`CommonResult<List<XxxLogVO>>`
- **权限**：`{模块}:{功能}:query`

#### `/export-excel`

- **方法**：`GET`
- **目的**：导出 Excel
- **请求**：`@Valid XxxPageReqVO`
- **响应**：`void`（直接写入 `HttpServletResponse`）
- **权限**：`{模块}:{功能}:export`
- **特殊注解**：`@ApiAccessLog(operateType = EXPORT)`

#### `/get-import-template`

- **方法**：`GET`
- **目的**：获取导入模板
- **请求**：无参数
- **响应**：`void`（直接写入 `HttpServletResponse`）
- **权限**：通常无需权限或 `{模块}:{功能}:import`

#### `/import`

- **方法**：`POST`
- **目的**：导入 Excel
- **请求**：`@RequestParam("file") MultipartFile file, @RequestParam("updateSupport") Boolean updateSupport`
- **响应**：`CommonResult<XxxImportRespVO>`
- **权限**：`{模块}:{功能}:import`
- **参数注解**：`@Parameters({...})`

## 第三部分：注解规范

### Controller 类注解

| 注解 | 格式 | 用途 | 引入 |
|------|------|------|------|
| `@Tag` | `@Tag(name = "管理后台 - {模块名}")` | OpenAPI 3.0 文档分组 | `io.swagger.v3.oas.annotations.tags.Tag` |
| `@RestController` | — | REST 控制器 | `org.springframework.web.bind.annotation.RestController` |
| `@RequestMapping` | `@RequestMapping("/{模块}/{功能}")` | 路由前缀 | `org.springframework.web.bind.annotation.RequestMapping` |
| `@Validated` | — | 参数校验支持 | `org.springframework.validation.annotation.Validated` |

### 方法注解

#### `@Operation`

- **格式**：`@Operation(summary = "{操作描述}")`
- **用途**：接口文档说明
- **引入**：`io.swagger.v3.oas.annotations.Operation`
- **示例**：
  - `@Operation(summary = "创建用户")`
  - `@Operation(summary = "获得用户分页列表")`
  - `@Operation(summary = "导出用户 Excel")`

#### `@PermitAll`

- **用途**：公开接口（无需登录）
- **引入**：`cn.iocoder.yudao.framework.security.core.annotations.PermitAll`
- **使用场景**：登录、登出、注册、验证码等无需认证的接口

#### `@PreAuthorize`

- **格式**：`@PreAuthorize("@ss.hasPermission('{模块}:{功能}:{操作}')")`
- **用途**：权限控制
- **引入**：`org.springframework.security.access.prepost.PreAuthorize`
- **示例**：
  - `@PreAuthorize("@ss.hasPermission('system:user:create')")`
  - `@PreAuthorize("@ss.hasPermission('pay:order:query')")`

#### `@Parameter`

- **格式**：`@Parameter(name = "{参数名}", description = "{描述}", required = {是否必填}, example = "{示例}")`
- **用途**：单参数文档
- **引入**：`io.swagger.v3.oas.annotations.Parameter`
- **使用场景**：单个 `@RequestParam` 参数时使用

#### `@Parameters`

- **格式**：`@Parameters({ @Parameter(name = "xxx", ...), @Parameter(name = "yyy", ...) })`
- **用途**：多参数文档
- **引入**：`io.swagger.v3.oas.annotations.Parameters`
- **使用场景**：多个 `@RequestParam` 参数时使用

#### `@ApiAccessLog`

- **格式**：`@ApiAccessLog(operateType = EXPORT)`
- **用途**：操作日志记录
- **引入**：`cn.iocoder.yudao.framework.apilog.core.annotation.ApiAccessLog`
- **使用场景**：导出、导入等需要记录日志的操作
- **常量引入**：`static cn.iocoder.yudao.framework.apilog.core.enums.OperateTypeEnum.EXPORT`

### 参数注解

| 注解 | 用途 | 引入 | 用法 |
|------|------|------|------|
| `@RequestBody` | 接收 JSON 请求体 | `org.springframework.web.bind.annotation.RequestBody` | `@RequestBody @Valid XxxReqVO reqVO` |
| `@RequestParam` | 接收 URL 查询参数 | `org.springframework.web.bind.annotation.RequestParam` | `@RequestParam("id") Long id` |
| `@Valid` | 参数校验 | `javax.validation.Valid` | `@Valid @RequestBody XxxReqVO reqVO` |

## 第四部分：请求响应规范

### 统一响应结构 CommonResult

- **类**：`cn.iocoder.yudao.framework.common.pojo.CommonResult<T>`
- **结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | Integer | 0 表示成功 |
| `msg` | String | 错误提示信息 |
| `data` | T | 返回数据 |

- **用法**：

```java
return success(data);          // 返回数据
return success(true);          // 返回布尔
return success(id);            // 返回 id
```

- **引入**：`static cn.iocoder.yudao.framework.common.pojo.CommonResult.success`

### 分页响应结构 PageResult

- **类**：`cn.iocoder.yudao.framework.common.pojo.PageResult<T>`
- **结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | Long | 总记录数 |
| `list` | List\<T\> | 当前页数据列表 |

- **用法**：`CommonResult<PageResult<XxxRespVO>> getXxxPage(...)`
- **空构造**：`new PageResult<>(pageResult.getTotal())`

### 分页请求参数 PageParam

- **类**：`cn.iocoder.yudao.framework.common.pojo.PageParam`
- **字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `pageNo` | Integer | 页码，从 1 开始，默认 1，最小值 1 |
| `pageSize` | Integer | 每页条数，默认 10，范围 1-200 |

- **常量**：

| 常量 | 值 |
|------|------|
| `PAGE_NO` | 1 |
| `PAGE_SIZE` | 10 |
| `PAGE_SIZE_NONE` | -1（不分页，用于导出等场景） |

- **用法**：分页查询 VO 继承 `PageParam`

### 请求 VO 类型

| 类型 | 用途 | 命名 | 特性 |
|------|------|------|------|
| `SaveReqVO` | 新增/修改请求 | `XxxSaveReqVO` | 修改时包含 id 字段；包含 `@NotBlank`/`@NotNull` 校验注解；使用 `@Schema` 注解描述字段 |
| `PageReqVO` | 分页查询请求 | `XxxPageReqVO` | 继承 `PageParam`；包含查询条件字段；时间字段使用 `@DateTimeFormat` |
| `ImportReqVO` | 导入请求 | `XxxImportReqVO` 或使用 `@RequestParam` 接收 file | 包含 `file` 和 `updateSupport` 参数 |
| `RespVO` | 响应对象 | `XxxRespVO` | 包含 `@Schema` 注解描述字段；包含 `createTime` 等只读字段 |

### VO 注解规范

| 注解 | 用途 | 格式 | 引入 |
|------|------|------|------|
| `@Schema` | OpenAPI 3.0 字段描述 | `@Schema(description = "{字段描述}", requiredMode = Schema.RequiredMode.REQUIRED, example = "{示例}")` | `io.swagger.v3.oas.annotations.media.Schema` |
| `@ExcelProperty` | Excel 导出字段 | `@ExcelProperty("{列名}")` | `com.alibaba.excel.annotation.ExcelProperty` |
| `@DictFormat` | 字典转换 | `@DictFormat("{字典类型}")` | — |

## 第五部分：权限标识规范

- **格式**：`{模块}:{功能}:{操作}`
- **规则**：
  - 模块名与功能名使用小写字母
  - 操作名使用标准动词

### 标准操作

| 操作 | 描述 |
|------|------|
| `query` | 查询权限（包括 get、page、list） |
| `create` | 新增权限 |
| `update` | 修改权限 |
| `delete` | 删除权限 |
| `export` | 导出权限 |
| `import` | 导入权限 |

### 示例

- `system:user:query`
- `system:user:create`
- `system:user:update`
- `system:user:delete`
- `system:user:export`
- `system:user:import`
- `pay:order:query`
- `pay:order:create`

### 权限 SQL 配置

#### 菜单 SQL

```sql
INSERT INTO system_menu (name, permission, type, sort, parent_id, path, icon, component, status)
VALUES ('{功能名称}管理', '', 2, 0, {父菜单ID}, '{功能}', 'ep:document', '{模块}/{功能}/index', 0);
```

#### 按钮 SQL

```sql
INSERT INTO system_menu (name, permission, type, sort, parent_id, status) VALUES
('{功能名称}查询', '{模块}:{功能}:query', 3, 1, @menuId, 0),
('{功能名称}新增', '{模块}:{功能}:create', 3, 2, @menuId, 0),
('{功能名称}修改', '{模块}:{功能}:update', 3, 3, @menuId, 0),
('{功能名称}删除', '{模块}:{功能}:delete', 3, 4, @menuId, 0),
('{功能名称}导出', '{模块}:{功能}:export', 3, 5, @menuId, 0);
```

## 第六部分：错误码体系

- **格式**：`1_模块编号_功能编号_错误序号`
- **成功码**：`0`

### 全局错误码

| 编码 | 描述 |
|------|------|
| 0 | 成功 |
| 400 | 请求参数不正确 |
| 401 | 账号未登录 |
| 403 | 没有该操作权限 |
| 404 | 请求未找到 |
| 405 | 请求方法不正确 |
| 423 | 请求失败，请稍后重试 |
| 429 | 请求过于频繁 |
| 500 | 系统异常 |
| 501 | 功能未实现/未开启 |
| 502 | 错误配置项 |
| 900 | 重复请求 |
| 901 | 演示模式，禁止写操作 |
| 999 | 未知错误 |

### 模块编号速查

| 模块 | 编码前缀 | 描述 |
|------|---------|------|
| `infra` | `1_001` | 基础设施模块 |
| `system` | `1_002` | 系统管理模块 |
| `member` | `1_003` | 会员模块 |
| `pay` | `1_007` | 支付模块 |
| `product` | `1_008` | 商品模块 |
| `trade` | `1_011` | 交易模块 |
| `promotion` | `1_013` | 促销模块 |

### 错误码定义模板

```java
// ========== {实体名称} 相关错误码 1_XXX_XXX_XXX ==========
ErrorCode XXX_NOT_EXISTS = new ErrorCode(1_002_001_000, "{实体名称}不存在");
ErrorCode XXX_CODE_DUPLICATE = new ErrorCode(1_002_001_001, "已存在该编码的{实体名称}");
ErrorCode XXX_NAME_DUPLICATE = new ErrorCode(1_002_001_002, "已存在该名称的{实体名称}");
ErrorCode XXX_CAN_NOT_DELETE = new ErrorCode(1_002_001_003, "{实体名称}不能删除，原因：{}");
ErrorCode XXX_STATUS_ERROR = new ErrorCode(1_002_001_004, "{实体名称}状态不正确");
```

## 第七部分：Controller 模板

### 基础 CRUD 模板

```java
package cn.iocoder.yudao.module.{模块}.controller.admin.{功能};

import cn.iocoder.yudao.framework.apilog.core.annotation.ApiAccessLog;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.framework.common.pojo.PageParam;
import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.framework.excel.core.util.ExcelUtils;
import cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo.*;
import cn.iocoder.yudao.module.{模块}.dal.dataobject.{功能}.XxxDO;
import cn.iocoder.yudao.module.{模块}.service.{功能}.XxxService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static cn.iocoder.yudao.framework.apilog.core.enums.OperateTypeEnum.EXPORT;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;

@Tag(name = "管理后台 - {实体名称}")
@RestController
@RequestMapping("/{模块}/{功能}")
@Validated
public class XxxController {

    @Resource
    private XxxService xxxService;

    @PostMapping("/create")
    @Operation(summary = "创建{实体名称}")
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:create')")
    public CommonResult<Long> createXxx(@Valid @RequestBody XxxSaveReqVO createReqVO) {
        return success(xxxService.createXxx(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新{实体名称}")
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:update')")
    public CommonResult<Boolean> updateXxx(@Valid @RequestBody XxxSaveReqVO updateReqVO) {
        xxxService.updateXxx(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除{实体名称}")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:delete')")
    public CommonResult<Boolean> deleteXxx(@RequestParam("id") Long id) {
        xxxService.deleteXxx(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得{实体名称}")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:query')")
    public CommonResult<XxxRespVO> getXxx(@RequestParam("id") Long id) {
        XxxDO xxx = xxxService.getXxx(id);
        return success(BeanUtils.toBean(xxx, XxxRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得{实体名称}分页")
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:query')")
    public CommonResult<PageResult<XxxRespVO>> getXxxPage(@Valid XxxPageReqVO pageReqVO) {
        PageResult<XxxDO> pageResult = xxxService.getXxxPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, XxxRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出{实体名称} Excel")
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportXxxExcel(@Valid XxxPageReqVO pageReqVO,
                               HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<XxxDO> list = xxxService.getXxxPage(pageReqVO).getList();
        List<XxxExcelVO> excelList = BeanUtils.toBean(list, XxxExcelVO.class);
        ExcelUtils.write(response, "{实体名称}.xls", "数据", XxxExcelVO.class, excelList);
    }
}
```

### 公开接口模板

```java
@PostMapping("/login")
@PermitAll
@Operation(summary = "使用账号密码登录")
public CommonResult<AuthLoginRespVO> login(@RequestBody @Valid AuthLoginReqVO reqVO) {
    return success(authService.login(reqVO));
}
```

### 批量操作模板

```java
@DeleteMapping("/delete-list")
@Parameter(name = "ids", description = "编号列表", required = true)
@Operation(summary = "批量删除{实体名称}")
@PreAuthorize("@ss.hasPermission('{模块}:{功能}:delete')")
public CommonResult<Boolean> deleteXxxList(@RequestParam("ids") List<Long> ids) {
    xxxService.deleteXxxList(ids);
    return success(true);
}
```

### 导入导出模板

```java
@GetMapping("/get-import-template")
@Operation(summary = "获得导入{实体名称}模板")
public void importTemplate(HttpServletResponse response) throws IOException {
    // 手动创建导出 demo
    List<XxxImportExcelVO> list = Arrays.asList(
        XxxImportExcelVO.builder().name("示例1").code("TEST1").build(),
        XxxImportExcelVO.builder().name("示例2").code("TEST2").build()
    );
    ExcelUtils.write(response, "{实体名称}导入模板.xls", "数据", XxxImportExcelVO.class, list);
}

@PostMapping("/import")
@Operation(summary = "导入{实体名称}")
@Parameters({
    @Parameter(name = "file", description = "Excel 文件", required = true),
    @Parameter(name = "updateSupport", description = "是否支持更新，默认为 false", example = "true")
})
@PreAuthorize("@ss.hasPermission('{模块}:{功能}:import')")
public CommonResult<XxxImportRespVO> importExcel(@RequestParam("file") MultipartFile file,
                                                  @RequestParam(value = "updateSupport", required = false, defaultValue = "false") Boolean updateSupport) throws Exception {
    List<XxxImportExcelVO> list = ExcelUtils.read(file, XxxImportExcelVO.class);
    return success(xxxService.importXxxList(list, updateSupport));
}
```

## 第八部分：设计流程

### 步骤 1：实体分析

- **动作**：分析数据库设计或 PRD，确定实体字段和业务含义
- **输入**：`db_design_file`、`prd_file`、模块 skill 文档
- **输出**：实体字段清单
- **检查清单**：
  - 确认实体所属模块
  - 阅读对应模块的 skill 文档
  - 确定需要哪些标准端点

### 步骤 2：端点设计

- **动作**：根据业务需求确定需要的 API 端点
- **考量**：
  - 是否需要完整 CRUD（create/update/delete/get/page）
  - 是否需要批量操作（delete-list）
  - 是否需要导入导出（export-excel/import）
  - 是否需要状态切换（update-status）
  - 是否有公开接口需求（使用 `@PermitAll`）

### 步骤 3：请求响应设计

- **动作**：设计各端点的请求参数和响应格式
- **模板**：
  - 使用 `SaveReqVO` 处理新增/修改
  - 使用 `PageReqVO` 处理分页查询（继承 `PageParam`）
  - 使用 `RespVO` 处理响应
  - 使用 `CommonResult` 包装响应

### 步骤 4：权限设计

- **动作**：确定各端点的权限标识
- **规则**：
  - 公开接口使用 `@PermitAll`
  - 权限接口使用 `@PreAuthorize`
  - 权限标识格式：`模块:功能:操作`
  - 查询类接口统一使用 query 权限

### 步骤 5：错误码设计

- **动作**：定义业务错误码
- **规则**：
  - 格式：`1_模块编号_功能编号_错误序号`
  - 常见错误：不存在、重复、状态错误、操作限制

### 步骤 6：文档生成

- **动作**：生成 Controller 代码和 API 文档
- **输出**：`Controller.java`、VO classes、错误码定义、权限 SQL

## 第九部分：检查清单

### 设计前

- 确认实体所属模块
- 阅读对应模块的 skill 文档
- 了解现有类似接口的设计模式
- 准备表结构设计

### 设计中

- URL 命名符合规范（`/{模块}/{功能}/{操作}`）
- HTTP 方法与操作类型匹配
- 请求 VO 类型选择正确
- 响应格式使用 `CommonResult`
- 权限标识命名正确
- 注解使用完整

### 设计后

- 所有接口添加 `@Operation` 注解
- 参数添加 `@Parameter` 或 `@Parameters` 注解
- 权限接口添加 `@PreAuthorize` 注解
- 公开接口添加 `@PermitAll` 注解
- 导出接口添加 `@ApiAccessLog` 注解
- 错误码定义完整

## 第十部分：与 entity-implementation.md 协同

### 关系定位

| 文档 | 角色 | 关注点 |
|------|------|--------|
| `api-designer.md` | API 设计阶段规范指导 | 设计决策、端点规划、权限标识 |
| `entity-implementation.md` | 完整实现流程指导 | 实现细节、模板代码、各层规范 |

### 使用流程

1. 使用 `api-designer.md` 进行 API 设计决策
2. 参考 `entity-implementation.md` 进行完整实现
3. 两者 Controller 模板保持一致

## 快速参考

### HTTP 方法

| 方法 | 说明 |
|------|------|
| `POST` | 创建类操作（create, import, send） |
| `PUT` | 更新类操作（update, update-status） |
| `DELETE` | 删除类操作（delete, delete-list） |
| `GET` | 查询类操作（get, page, list, export-excel） |

### 标准端点

| 端点 | 说明 |
|------|------|
| `/create` | 创建 → `CommonResult<Long>` |
| `/update` | 更新 → `CommonResult<Boolean>` |
| `/delete` | 删除 → `CommonResult<Boolean>` |
| `/delete-list` | 批量删除 → `CommonResult<Boolean>` |
| `/get` | 详情 → `CommonResult<XxxRespVO>` |
| `/page` | 分页 → `CommonResult<PageResult<XxxRespVO>>` |
| `/list` | 列表 → `CommonResult<List<XxxRespVO>>` |
| `/export-excel` | 导出 → `void` |
| `/import` | 导入 → `CommonResult<XxxImportRespVO>` |

### 权限操作

| 操作 | 说明 |
|------|------|
| `query` | 查询（get/page/list） |
| `create` | 新增 |
| `update` | 修改 |
| `delete` | 删除 |
| `export` | 导出 |
| `import` | 导入 |

### 响应类型

| 类型 | 说明 |
|------|------|
| `CommonResult<Long>` | 创建类响应 |
| `CommonResult<Boolean>` | 操作类响应 |
| `CommonResult<XxxRespVO>` | 详情类响应 |
| `CommonResult<PageResult<XxxRespVO>>` | 分页类响应 |
| `CommonResult<List<XxxRespVO>>` | 列表类响应 |

### VO 类型

| 类型 | 说明 |
|------|------|
| `XxxSaveReqVO` | 新增/修改请求 |
| `XxxPageReqVO` | 分页查询请求（继承 `PageParam`） |
| `XxxRespVO` | 响应对象 |
| `XxxExcelVO` | Excel 导出对象 |
| `XxxImportExcelVO` | Excel 导入对象 |
| `XxxImportRespVO` | 导入结果响应 |

### Controller 通用引入

```java
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import org.springframework.security.access.prepost.PreAuthorize;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.framework.common.pojo.PageResult;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
```
