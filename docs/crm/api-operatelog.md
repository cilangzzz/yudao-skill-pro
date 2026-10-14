# 操作日志接口 (CrmOperateLogController)

> 提供 CRM 各业务实体（线索/客户/联系人/商机/合同/产品/回款/回款计划）的操作日志查询，日志数据由 mzt-biz-log 操作日志框架记录在 system 模块的 `system_operate_log` 表中，本域仅做读取展示。

## 接口路径前缀

/crm/operate-log  (Controller: CrmOperateLogController)

## 1. 操作日志查询

### 1.1 获得操作日志

- **路径**: GET /crm/operate-log/page
- **权限**: 已认证（无 @PreAuthorize 权限标识，仅需登录）
- **说明**: 按数据类型 + 数据编号查询某个 CRM 业务对象的全部操作日志，默认不分页（一次返回全部记录）

**请求参数 (CrmOperateLogPageReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| bizType | Integer | 是 | @NotNull、@InEnum(CrmBizTypeEnum.class) | 数据类型：1-线索、2-客户、3-联系人、4-商机、5-合同、6-产品、7-回款、8-回款计划 |
| bizId | Long | 是 | @NotNull | 数据编号（对应业务实体的主键 ID） |
| pageNo | Integer | 是 | @NotNull、@Min(1) | 页码，从 1 开始，默认 1（当前实现不生效，见业务逻辑） |
| pageSize | Integer | 是 | @NotNull、@Min(1)、@Max(200) | 每页条数，默认 10（当前实现不生效，见业务逻辑） |

**响应**: CommonResult<PageResult<CrmOperateLogRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | 日志编号 |
| userId | Long | 操作人用户编号 |
| userName | String | 操作人用户名称（由 @Trans 注解翻译 AdminUserDO.nickname） |
| userType | Integer | 用户类型 |
| type | String | 操作模块类型，如 "CRM 客户"、"CRM 线索" |
| subType | String | 操作名，如 "修改客户"、"新建商机" |
| bizId | Long | 操作模块业务编号 |
| action | String | 操作内容，如 "将什么从什么改为了什么" |
| extra | String | 拓展字段（JSON 字符串） |
| createTime | LocalDateTime | 操作时间 |

**业务逻辑**:
1. Controller 内维护静态映射 BIZ_TYPE_MAP：将 CrmBizTypeEnum 的数字类型（1~8）映射为 LogRecordConstants 中定义的日志模块类型字符串（如 CRM_CUSTOMER_TYPE = "CRM 客户"、CRM_CLUE_TYPE = "CRM 线索"）。
2. 构造 system 模块的 OperateLogPageReqDTO，并将 pageSize 强制设置为 PAGE_SIZE_NONE（-1），即默认不分页、一次性返回该业务对象的所有操作日志（代码注释：需要分页需自行调整）。
3. 以 bizType 映射出的 type 字符串和 bizId 作为查询条件，调用 system 模块的 OperateLogApi.getOperateLogPage 查询操作日志。
4. system 模块 OperateLogServiceImpl.getOperateLogPage 委托 OperateLogMapper.selectPage，按 type、bizId、userId 等值匹配查询（eqIfPresent），并按 id 倒序排列。
5. 查询结果先转换为 OperateLogRespDTO（方法带 @TransMethodResult，用户编号自动翻译出 userName），再由 BeanUtils 转换为 CrmOperateLogRespVO 分页返回。

**错误码**: 无（该域未定义专属错误码，参数校验失败由框架返回 400）
