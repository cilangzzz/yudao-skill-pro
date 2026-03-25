# Skill 使用指南 - 实体类实现完整流程

本文档提供从 SQL 建表到实体类实现的完整流程提示词，帮助开发者快速创建符合项目规范的业务实体功能。

---

## 一、场景说明

### 何时使用实体类实现

实体类实现场景适用于以下情况：

| 场景类型 | 描述 | 典型示例 |
|---------|------|---------|
| **新增业务实体** | 创建全新的业务对象 CRUD | 新增工单、设备、产品等业务对象 |
| **扩展模块功能** | 在现有模块中添加新实体 | MES 模块新增工序实体、ERP 模块新增仓库实体 |
| **快速原型开发** | 快速搭建基础增删改查功能 | 管理后台的数据维护功能 |

### 实体类实现完整流程

```
SQL 建表 → DO 实体类 → Mapper 层 → Service 层 → Controller 层 → VO 类 → 错误码 → 权限配置
```

### 实现前检查清单

在开始实现前，请确认：

1. **明确业务需求** - 了解实体的业务含义和字段定义
2. **确定所属模块** - 明确实体应该放在哪个模块下
3. **准备表结构设计** - 完成数据库表结构设计
4. **阅读对应 Skill 文档** - 了解模块的技术规范

---

## 二、完整实现流程

### 流程总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           实体类实现完整流程                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SQL 建表                                                                 │
│     └─→ 设计表结构、字段、索引                                                 │
│                                                                             │
│  2. DO 实体类                                                                │
│     └─→ 创建数据对象，映射数据库表                                              │
│                                                                             │
│  3. Mapper 层                                                               │
│     └─→ 定义数据访问接口                                                      │
│                                                                             │
│  4. Service 层                                                              │
│     ├─→ Service 接口                                                        │
│     └─→ Service 实现                                                        │
│                                                                             │
│  5. Controller 层                                                           │
│     └─→ HTTP API 接口                                                        │
│                                                                             │
│  6. VO 类                                                                   │
│     ├─→ SaveReqVO (新增/修改请求)                                             │
│     ├─→ PageReqVO (分页查询请求)                                              │
│     └─→ RespVO (响应对象)                                                    │
│                                                                             │
│  7. 错误码定义                                                               │
│     └─→ 在 ErrorCodeConstants 中定义                                         │
│                                                                             │
│  8. 权限配置                                                                 │
│     └─→ 菜单和按钮权限 SQL                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、各层实现详解

### 3.1 第一步：SQL 建表

#### 表设计规范

```sql
-- 表名规范：小写字母，单词间用下划线分隔
-- 建议添加的通用字段：
-- - id：主键，BIGINT，自增或雪花算法
-- - creator：创建人，VARCHAR(64)
-- - create_time：创建时间，DATETIME
-- - updater：更新人，VARCHAR(64)
-- - update_time：更新时间，DATETIME
-- - deleted：逻辑删除，BIT，默认 0
-- - tenant_id：租户编号，BIGINT（多租户场景）

CREATE TABLE `表名` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    -- 业务字段
    `name` VARCHAR(100) NOT NULL COMMENT '名称',
    `code` VARCHAR(50) NOT NULL COMMENT '编码',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态（0正常 1停用）',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    -- 通用字段
    `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` BIT(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
    `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户编号',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`)  -- 唯一索引示例
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='表注释';
```

#### 表设计检查清单

- [ ] 主键设计合理（自增/雪花算法）
- [ ] 字段类型和长度合适
- [ ] 添加了必要的索引
- [ ] 包含通用字段（creator, create_time 等）
- [ ] 多租户场景包含 tenant_id
- [ ] 添加了表注释和字段注释

---

### 3.2 第二步：DO 实体类

#### 基础模板

```java
package cn.iocoder.yudao.module.{模块}.dal.dataobject.{功能};

import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

/**
 * {实体名称} DO
 *
 * @author {作者}
 */
@TableName("{表名}")
@KeySequence("{表名}_seq") // Oracle 场景使用
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class XxxDO extends BaseDO {

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
     * 编码
     */
    private String code;

    /**
     * 状态
     *
     * 枚举 {@link cn.iocoder.yudao.module.{模块}.enums.XxxStatusEnum}
     */
    private Integer status;

    /**
     * 备注
     */
    private String remark;

}
```

#### 多租户实体模板

```java
package cn.iocoder.yudao.module.{模块}.dal.dataobject.{功能};

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

/**
 * {实体名称} DO（多租户）
 *
 * @author {作者}
 */
@TableName("{表名}")
@KeySequence("{表名}_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class XxxDO extends TenantBaseDO {

    // 继承 TenantBaseDO 自动包含 tenantId 字段
    // 继承 BaseDO 自动包含 creator, createTime, updater, updateTime, deleted 字段

    @TableId
    private Long id;

    // 业务字段...

}
```

#### DO 实体类检查清单

- [ ] 继承正确的基类（BaseDO / TenantBaseDO）
- [ ] @TableName 指定正确的表名
- [ ] 主键字段使用 @TableId 注解
- [ ] 字段类型与数据库类型对应
- [ ] 添加了字段注释
- [ ] 枚举字段添加了枚举引用注释
- [ ] 使用 Lombok 注解简化代码

---

### 3.3 第三步：Mapper 层

#### 基础模板

```java
package cn.iocoder.yudao.module.{模块}.dal.mysql.{功能};

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo.XxxPageReqVO;
import cn.iocoder.yudao.module.{模块}.dal.dataobject.{功能}.XxxDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * {实体名称} Mapper
 *
 * @author {作者}
 */
@Mapper
public interface XxxMapper extends BaseMapperX<XxxDO> {

    /**
     * 分页查询
     */
    default PageResult<XxxDO> selectPage(XxxPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<XxxDO>()
                .likeIfPresent(XxxDO::getName, reqVO.getName())
                .eqIfPresent(XxxDO::getCode, reqVO.getCode())
                .eqIfPresent(XxxDO::getStatus, reqVO.getStatus())
                .betweenIfPresent(XxxDO::getCreateTime, reqVO.getCreateTime())
                .orderByDesc(XxxDO::getId));
    }

    /**
     * 根据编码查询
     */
    default XxxDO selectByCode(String code) {
        return selectOne(XxxDO::getCode, code);
    }

    /**
     * 根据状态查询列表
     */
    default List<XxxDO> selectListByStatus(Integer status) {
        return selectList(XxxDO::getStatus, status);
    }

}
```

#### Mapper 查询方法速查

| 方法 | 用途 | 示例 |
|------|------|------|
| `selectById` | 根据 ID 查询 | `selectById(id)` |
| `selectOne` | 查询单条记录 | `selectOne(XxxDO::getCode, code)` |
| `selectList` | 查询列表 | `selectList(XxxDO::getStatus, status)` |
| `selectPage` | 分页查询 | `selectPage(reqVO, wrapper)` |
| `selectCount` | 查询数量 | `selectCount(wrapper)` |
| `insert` | 插入 | `insert(xxx)` |
| `updateById` | 根据 ID 更新 | `updateById(xxx)` |
| `deleteById` | 根据 ID 删除 | `deleteById(id)` |

#### LambdaQueryWrapperX 常用方法

| 方法 | 用途 | 示例 |
|------|------|------|
| `eqIfPresent` | 等于（参数不为空时） | `.eqIfPresent(XxxDO::getStatus, status)` |
| `likeIfPresent` | 模糊匹配（参数不为空时） | `.likeIfPresent(XxxDO::getName, name)` |
| `betweenIfPresent` | 区间查询（参数不为空时） | `.betweenIfPresent(XxxDO::getCreateTime, times)` |
| `inIfPresent` | IN 查询（参数不为空时） | `.inIfPresent(XxxDO::getId, ids)` |
| `orderByDesc` | 降序排序 | `.orderByDesc(XxxDO::getId)` |
| `orderByAsc` | 升序排序 | `.orderByAsc(XxxDO::getSort)` |

---

### 3.4 第四步：Service 层

#### Service 接口模板

```java
package cn.iocoder.yudao.module.{模块}.service.{功能};

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo.XxxPageReqVO;
import cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo.XxxSaveReqVO;
import cn.iocoder.yudao.module.{模块}.dal.dataobject.{功能}.XxxDO;

import javax.validation.Valid;
import java.util.List;

/**
 * {实体名称} Service 接口
 *
 * @author {作者}
 */
public interface XxxService {

    /**
     * 创建{实体名称}
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createXxx(@Valid XxxSaveReqVO createReqVO);

    /**
     * 更新{实体名称}
     *
     * @param updateReqVO 更新信息
     */
    void updateXxx(@Valid XxxSaveReqVO updateReqVO);

    /**
     * 删除{实体名称}
     *
     * @param id 编号
     */
    void deleteXxx(Long id);

    /**
     * 获得{实体名称}
     *
     * @param id 编号
     * @return {实体名称}
     */
    XxxDO getXxx(Long id);

    /**
     * 获得{实体名称}分页
     *
     * @param pageReqVO 分页查询
     * @return {实体名称}分页
     */
    PageResult<XxxDO> getXxxPage(XxxPageReqVO pageReqVO);

    /**
     * 获得{实体名称}列表
     *
     * @param ids 编号列表
     * @return {实体名称}列表
     */
    List<XxxDO> getXxxList(List<Long> ids);

}
```

#### Service 实现模板

```java
package cn.iocoder.yudao.module.{模块}.service.{功能};

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo.XxxPageReqVO;
import cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo.XxxSaveReqVO;
import cn.iocoder.yudao.module.{模块}.dal.dataobject.{功能}.XxxDO;
import cn.iocoder.yudao.module.{模块}.dal.mysql.{功能}.XxxMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.util.List;

import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.{模块}.enums.ErrorCodeConstants.*;

/**
 * {实体名称} Service 实现类
 *
 * @author {作者}
 */
@Service
@Validated
public class XxxServiceImpl implements XxxService {

    @Resource
    private XxxMapper xxxMapper;

    @Override
    public Long createXxx(XxxSaveReqVO createReqVO) {
        // 1. 校验编码唯一性
        validateXxxCodeUnique(null, createReqVO.getCode());
        // 2. 插入
        XxxDO xxx = BeanUtils.toBean(createReqVO, XxxDO.class);
        xxxMapper.insert(xxx);
        // 3. 返回
        return xxx.getId();
    }

    @Override
    public void updateXxx(XxxSaveReqVO updateReqVO) {
        // 1. 校验存在
        validateXxxExists(updateReqVO.getId());
        // 2. 校验编码唯一性
        validateXxxCodeUnique(updateReqVO.getId(), updateReqVO.getCode());
        // 3. 更新
        XxxDO updateObj = BeanUtils.toBean(updateReqVO, XxxDO.class);
        xxxMapper.updateById(updateObj);
    }

    @Override
    public void deleteXxx(Long id) {
        // 1. 校验存在
        validateXxxExists(id);
        // 2. 删除
        xxxMapper.deleteById(id);
    }

    /**
     * 校验{实体名称}是否存在
     */
    private void validateXxxExists(Long id) {
        if (xxxMapper.selectById(id) == null) {
            throw exception(XXX_NOT_EXISTS);
        }
    }

    /**
     * 校验编码唯一性
     */
    private void validateXxxCodeUnique(Long id, String code) {
        XxxDO xxx = xxxMapper.selectByCode(code);
        if (xxx == null) {
            return;
        }
        // 如果 id 为空，说明不用比较是否为相同 id 的{实体名称}
        if (id == null) {
            throw exception(XXX_CODE_DUPLICATE);
        }
        if (!xxx.getId().equals(id)) {
            throw exception(XXX_CODE_DUPLICATE);
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

    @Override
    public List<XxxDO> getXxxList(List<Long> ids) {
        return xxxMapper.selectBatchIds(ids);
    }

}
```

#### Service 层检查清单

- [ ] 接口方法命名规范（create/update/delete/get）
- [ ] 实现类添加 @Service 和 @Validated 注解
- [ ] 新增/修改方法进行必要的业务校验
- [ ] 删除方法校验数据是否存在
- [ ] 使用 exception() 方法抛出业务异常
- [ ] 复杂业务添加 @Transactional 注解

---

### 3.5 第五步：Controller 层

#### Controller 完整模板

```java
package cn.iocoder.yudao.module.{模块}.controller.admin.{功能};

import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.framework.common.pojo.PageParam;
import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.framework.excel.core.util.ExcelUtils;
import cn.iocoder.yudao.framework.operatelog.core.annotations.OperateLog;
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

import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
import static cn.iocoder.yudao.framework.operatelog.core.enums.OperateTypeEnum.EXPORT;

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

    @GetMapping("/list")
    @Operation(summary = "获得{实体名称}列表")
    @Parameter(name = "ids", description = "编号列表", required = true)
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:query')")
    public CommonResult<List<XxxRespVO>> getXxxList(@RequestParam("ids") List<Long> ids) {
        List<XxxDO> list = xxxService.getXxxList(ids);
        return success(BeanUtils.toBean(list, XxxRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出{实体名称} Excel")
    @PreAuthorize("@ss.hasPermission('{模块}:{功能}:export')")
    @OperateLog(type = EXPORT)
    public void exportXxxExcel(@Valid XxxPageReqVO pageReqVO,
                               HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<XxxDO> list = xxxService.getXxxPage(pageReqVO).getList();
        // 导出 Excel
        List<XxxExcelVO> excelList = BeanUtils.toBean(list, XxxExcelVO.class);
        ExcelUtils.write(response, "{实体名称}.xls", "数据", XxxExcelVO.class, excelList);
    }

}
```

#### Controller 层检查清单

- [ ] 添加 @Tag 注解定义 Swagger 分组
- [ ] 添加 @RestController 和 @RequestMapping 注解
- [ ] HTTP 方法与操作对应（POST 创建、PUT 更新、DELETE 删除、GET 查询）
- [ ] 添加 @Operation 注解描述接口功能
- [ ] 添加 @PreAuthorize 注解进行权限控制
- [ ] 使用 @Parameter 描述路径参数
- [ ] 返回值使用 CommonResult 包装
- [ ] 导出功能添加 @OperateLog 注解

---

### 3.6 第六步：VO 类

#### SaveReqVO 模板（新增/修改共用）

```java
package cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

/**
 * {实体名称} 新增/修改 Request VO
 */
@Schema(description = "管理后台 - {实体名称}新增/修改 Request VO")
@Data
public class XxxSaveReqVO {

    @Schema(description = "编号", example = "1")
    private Long id; // 更新时需要传递

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "测试")
    @NotBlank(message = "名称不能为空")
    private String name;

    @Schema(description = "编码", requiredMode = Schema.RequiredMode.REQUIRED, example = "TEST")
    @NotBlank(message = "编码不能为空")
    private String code;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "0")
    @NotNull(message = "状态不能为空")
    private Integer status;

    @Schema(description = "备注", example = "备注信息")
    private String remark;

}
```

#### PageReqVO 模板（分页查询）

```java
package cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo;

import cn.iocoder.yudao.framework.common.pojo.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;

import static cn.iocoder.yudao.framework.common.util.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

/**
 * {实体名称} 分页 Request VO
 */
@Schema(description = "管理后台 - {实体名称}分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
public class XxxPageReqVO extends PageParam {

    @Schema(description = "名称，模糊匹配", example = "测试")
    private String name;

    @Schema(description = "编码", example = "TEST")
    private String code;

    @Schema(description = "状态", example = "0")
    private Integer status;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

}
```

#### RespVO 模板（响应）

```java
package cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * {实体名称} Response VO
 */
@Schema(description = "管理后台 - {实体名称} Response VO")
@Data
public class XxxRespVO {

    @Schema(description = "编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "测试")
    private String name;

    @Schema(description = "编码", requiredMode = Schema.RequiredMode.REQUIRED, example = "TEST")
    private String code;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "0")
    private Integer status;

    @Schema(description = "备注", example = "备注信息")
    private String remark;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime createTime;

}
```

#### ExcelVO 模板（导出）

```java
package cn.iocoder.yudao.module.{模块}.controller.admin.{功能}.vo;

import cn.iocoder.yudao.framework.excel.core.annotations.DictFormat;
import cn.iocoder.yudao.framework.excel.core.convert.DictConvert;
import com.alibaba.excel.annotation.ExcelProperty;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * {实体名称} Excel VO
 */
@Data
public class XxxExcelVO {

    @ExcelProperty("编号")
    private Long id;

    @ExcelProperty("名称")
    private String name;

    @ExcelProperty("编码")
    private String code;

    @ExcelProperty("状态")
    @DictFormat("common_status") // 使用字典转换
    private Integer status;

    @ExcelProperty("备注")
    private String remark;

    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}
```

#### VO 类检查清单

- [ ] SaveReqVO 用于新增和修改，修改时传递 id
- [ ] PageReqVO 继承 PageParam
- [ ] 添加 @Schema 注解描述字段
- [ ] 添加必要的校验注解（@NotBlank, @NotNull 等）
- [ ] 时间字段使用 @DateTimeFormat 注解
- [ ] Excel 导出字段使用 @ExcelProperty 注解

---

### 3.7 第七步：错误码定义

#### 错误码定义模板

```java
// 在 cn.iocoder.yudao.module.{模块}.enums.ErrorCodeConstants 中添加

// ========== {实体名称} 相关错误码 1_XXX_XXX_XXX ==========
ErrorCode XXX_NOT_EXISTS = new ErrorCode(1_002_001_000, "{实体名称}不存在");
ErrorCode XXX_CODE_DUPLICATE = new ErrorCode(1_002_001_001, "已存在该编码的{实体名称}");
ErrorCode XXX_NAME_DUPLICATE = new ErrorCode(1_002_001_002, "已存在该名称的{实体名称}");
ErrorCode XXX_CAN_NOT_DELETE = new ErrorCode(1_002_001_003, "{实体名称}不能删除，原因：{}");
ErrorCode XXX_STATUS_ERROR = new ErrorCode(1_002_001_004, "{实体名称}状态不正确");
```

#### 错误码编号规范

```
格式：1_模块编号_功能编号_错误序号

示例：
- 1_002_001_000  →  系统模块(002) → 用户管理功能(001) → 错误序号(000)
- 1_007_002_001  →  支付模块(007) → 支付订单功能(002) → 错误序号(001)

模块编号速查：
- 001: infra（基础设施）
- 002: system（系统管理）
- 003: member（会员）
- 007: pay（支付）
- 008: product（商品）
- 011: trade（交易）
- 013: promotion（促销）
```

---

### 3.8 第八步：权限配置

#### 菜单权限 SQL

```sql
-- 添加菜单（假设父菜单 ID 为 100）
INSERT INTO system_menu (name, permission, type, sort, parent_id, path, icon, component, status)
VALUES ('{功能名称}管理', '', 2, 0, {父菜单ID}, '{功能}', 'ep:document', '{模块}/{功能}/index', 0);

-- 获取刚插入的菜单 ID（假设为 1001）
SET @menuId = LAST_INSERT_ID();

-- 添加按钮权限
INSERT INTO system_menu (name, permission, type, sort, parent_id, status) VALUES
('{功能名称}查询', '{模块}:{功能}:query', 3, 1, @menuId, 0),
('{功能名称}新增', '{模块}:{功能}:create', 3, 2, @menuId, 0),
('{功能名称}修改', '{模块}:{功能}:update', 3, 3, @menuId, 0),
('{功能名称}删除', '{模块}:{功能}:delete', 3, 4, @menuId, 0),
('{功能名称}导出', '{模块}:{功能}:export', 3, 5, @menuId, 0);
```

#### 权限标识规范

```
格式：{模块}:{功能}:{操作}

操作类型：
- query  : 查询（包括列表、详情）
- create : 新增
- update : 修改
- delete : 删除
- export : 导出

示例：
- system:user:query     # 查询用户
- system:user:create    # 新增用户
- system:user:update    # 修改用户
- system:user:delete    # 删除用户
- system:user:export    # 导出用户
```

---

## 四、完整提示词模板

### 一键生成完整实体功能

```markdown
## 角色

你是一位资深的 Java 架构师，精通 Spring Boot、MyBatis-Plus，熟悉 yudao-vue-pro 项目架构。
你将帮助用户创建完整的业务实体功能，从 SQL 建表到完整的 CRUD 接口。

## 上下文

### 项目信息
- 项目：yudao-vue-pro（芋道源码）
- 架构：分层架构（Controller -> Service -> DAL）
- 技术栈：Spring Boot 3.x、MyBatis-Plus、Swagger v3

### 目标模块
- 模块名称：{模块名，如 system/infra/pay}
- 模块路径：yudao-module-{模块}
- Skill 文档：skills/modules/{模块}/skill-{模块}.yaml

### 实体需求
- 实体名称：{实体中文名}
- 实体编码：{实体英文名，如 WorkOrder}
- 业务描述：{业务功能描述}
- 字段列表：
  | 字段名 | 字段类型 | 是否必填 | 说明 |
  |-------|---------|---------|------|
  | name | String | 是 | 名称 |
  | code | String | 是 | 编码 |
  | status | Integer | 是 | 状态 |
  | ... | ... | ... | ... |

## 分析步骤

请按以下步骤分析并实现：

### 步骤 1：设计数据库表
根据字段列表设计数据库表结构，包括：
- 主键设计
- 索引设计
- 通用字段（creator, create_time 等）

### 步骤 2：创建文件清单
列出需要创建的所有文件：
- DO 实体类
- Mapper 接口
- Service 接口和实现
- Controller
- VO 类（SaveReqVO、PageReqVO、RespVO）
- 错误码定义

### 步骤 3：验证设计
- 检查命名是否符合项目规范
- 检查注解是否完整
- 检查权限标识是否正确

## 输出要求

请按以下顺序输出：

### 1. 建表 SQL
提供完整的建表语句，包括注释和索引。

### 2. DO 实体类
完整代码，包括所有注解和注释。

### 3. Mapper 接口
包含分页查询和常用查询方法。

### 4. Service 层
- Service 接口
- Service 实现类（包含业务校验逻辑）

### 5. Controller 层
完整的 CRUD 接口，包含权限控制。

### 6. VO 类
- XxxSaveReqVO
- XxxPageReqVO
- XxxRespVO
- XxxExcelVO（如需导出功能）

### 7. 错误码定义
在 ErrorCodeConstants 中添加的错误码。

### 8. 权限配置 SQL
菜单和按钮权限的 SQL 语句。
```

---

## 五、实际示例

### 示例：MES 工序实体实现

**提示词输入：**

```markdown
## 角色

你是一位资深的 Java 架构师，精通 Spring Boot、MyBatis-Plus，熟悉 yudao-vue-pro 项目架构。

## 上下文

### 目标模块
- 模块名称：mes
- 模块路径：yudao-module-mes

### 实体需求
- 实体名称：工序
- 实体编码：Process
- 业务描述：生产制造中的工序管理，用于定义产品的加工步骤
- 字段列表：
  | 字段名 | 字段类型 | 是否必填 | 说明 |
  |-------|---------|---------|------|
  | name | String | 是 | 工序名称 |
  | code | String | 是 | 工序编码，唯一 |
  | description | String | 否 | 工序描述 |
  | status | Integer | 是 | 状态（0正常 1停用）|
  | sort | Integer | 否 | 排序 |
  | workShopId | Long | 是 | 所属车间ID |

请按照实体类实现完整流程提示词模板输出。
```

**预期输出关键内容：**

#### 1. 建表 SQL

```sql
CREATE TABLE `mes_process` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `name` VARCHAR(100) NOT NULL COMMENT '工序名称',
    `code` VARCHAR(50) NOT NULL COMMENT '工序编码',
    `description` VARCHAR(500) DEFAULT NULL COMMENT '工序描述',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态（0正常 1停用）',
    `sort` INT NOT NULL DEFAULT 0 COMMENT '排序',
    `work_shop_id` BIGINT NOT NULL COMMENT '所属车间ID',
    `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` BIT(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
    `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户编号',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_work_shop_id` (`work_shop_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MES工序表';
```

#### 2. DO 实体类

```java
@TableName("mes_process")
@Data
@EqualsAndHashCode(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MesProcessDO extends TenantBaseDO {

    @TableId
    private Long id;

    /** 工序名称 */
    private String name;

    /** 工序编码 */
    private String code;

    /** 工序描述 */
    private String description;

    /** 状态 */
    private Integer status;

    /** 排序 */
    private Integer sort;

    /** 所属车间ID */
    private Long workShopId;

}
```

#### 3. Mapper 接口

```java
@Mapper
public interface MesProcessMapper extends BaseMapperX<MesProcessDO> {

    default PageResult<MesProcessDO> selectPage(MesProcessPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<MesProcessDO>()
                .likeIfPresent(MesProcessDO::getName, reqVO.getName())
                .eqIfPresent(MesProcessDO::getCode, reqVO.getCode())
                .eqIfPresent(MesProcessDO::getStatus, reqVO.getStatus())
                .eqIfPresent(MesProcessDO::getWorkShopId, reqVO.getWorkShopId())
                .betweenIfPresent(MesProcessDO::getCreateTime, reqVO.getCreateTime())
                .orderByAsc(MesProcessDO::getSort)
                .orderByDesc(MesProcessDO::getId));
    }

    default MesProcessDO selectByCode(String code) {
        return selectOne(MesProcessDO::getCode, code);
    }

}
```

（其他层代码按模板生成，此处省略）

---

## 六、快速参考

### 文件创建顺序

```
1. SQL 建表          → sql/module/xxx.sql
2. DO 实体类         → dal/dataobject/xxx/XxxDO.java
3. Mapper 接口       → dal/mysql/xxx/XxxMapper.java
4. Service 接口      → service/xxx/XxxService.java
5. Service 实现      → service/xxx/XxxServiceImpl.java
6. VO 类            → controller/admin/xxx/vo/*.java
7. Controller       → controller/admin/xxx/XxxController.java
8. 错误码定义        → enums/ErrorCodeConstants.java
9. 权限配置 SQL      → sql/menu/xxx_menu.sql
```

### 命名规范速查

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 数据库表 | 小写下划线 | mes_process |
| DO 类 | XxxDO | MesProcessDO |
| Mapper | XxxMapper | MesProcessMapper |
| Service 接口 | XxxService | MesProcessService |
| Service 实现 | XxxServiceImpl | MesProcessServiceImpl |
| Controller | XxxController | MesProcessController |
| 保存 VO | XxxSaveReqVO | MesProcessSaveReqVO |
| 分页 VO | XxxPageReqVO | MesProcessPageReqVO |
| 响应 VO | XxxRespVO | MesProcessRespVO |
| 权限标识 | 模块:功能:操作 | mes:process:create |

### 包路径规范

```
cn.iocoder.yudao.module.{模块}
├── controller
│   └── admin
│       └── {功能}
│           ├── XxxController.java
│           └── vo
│               ├── XxxSaveReqVO.java
│               ├── XxxPageReqVO.java
│               └── XxxRespVO.java
├── dal
│   ├── dataobject
│   │   └── {功能}
│   │       └── XxxDO.java
│   └── mysql
│       └── {功能}
│           └── XxxMapper.java
├── service
│   └── {功能}
│       ├── XxxService.java
│       └── XxxServiceImpl.java
└── enums
    └── ErrorCodeConstants.java
```

---

## 七、常见问题

### Q1: DO 实体应该继承 BaseDO 还是 TenantBaseDO？

**A:** 根据业务需求选择：
- **BaseDO**：单租户场景，包含 creator, createTime, updater, updateTime, deleted
- **TenantBaseDO**：多租户场景，额外包含 tenantId 字段

### Q2: SaveReqVO 和 PageReqVO 可以合并吗？

**A:** 不建议合并：
- SaveReqVO 用于新增/修改，需要校验注解
- PageReqVO 用于查询，继承 PageParam
- 分离更清晰，便于维护

### Q3: 如何处理枚举字段？

**A:** 两种方式：
1. 使用 Integer 存储，DO 字段添加枚举引用注释
2. 使用 MyBatis-Plus 枚举处理器，添加 @EnumValue 注解

### Q4: 错误码如何分配编号？

**A:** 按照模块编号规则：
- 查看项目中已有的错误码定义
- 按功能模块分段分配
- 同一功能的错误码连续编号

### Q5: 如何实现软删除？

**A:** 项目已内置软删除支持：
- BaseDO 包含 deleted 字段
- 配置 MyBatis-Plus 逻辑删除
- 调用 deleteById 会自动变成 UPDATE

---

## 八、最佳实践

### 1. 字段设计

- 使用有意义的中文名称作为注释
- 状态字段使用 Integer 配合枚举
- 金额字段使用 DECIMAL 而非 DOUBLE
- 大文本使用 TEXT 而非 VARCHAR

### 2. 索引设计

- 主键使用自增 BIGINT
- 唯一约束字段创建唯一索引
- 外键字段创建普通索引
- 查询条件字段考虑索引

### 3. 代码规范

- DO 字段与数据库字段对应
- Service 层进行业务校验
- Controller 层仅做参数校验
- 使用 BeanUtils 进行对象转换

### 4. 权限设计

- 所有接口都需要权限控制
- 查询类接口使用 query 权限
- 操作类接口区分 create/update/delete
- 导出接口单独设置 export 权限

---

> 提示：使用本文档的提示词模板，可以让 AI 快速生成符合项目规范的完整实体功能代码。