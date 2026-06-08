# Report 模块踩坑与注意事项

## 1. 积木报表 Token 传递

**问题**：积木报表运行在 iframe 中，无法直接获取外层应用的 Token。

**解决**：通过 `JmReportTokenServiceImpl` 的 `customApiHeader` 方法将 yudao 的 OAuth2 Token 注入到积木报表的请求头中。

**注意**：
- Token 过期后积木报表会静默失败，需确保 Token 刷新机制正常
- 多 Tab 场景下 Token 可能冲突，建议使用 Session 级别存储

## 2. SQL 查询注入风险

**问题**：`GoViewDataController.getDataBySQL` 直接执行用户传入的 SQL 语句。

**风险**：生产环境中恶意用户可执行 `DROP TABLE`、`UPDATE` 等危险操作。

**建议**：
- 生产环境增加 SQL 白名单机制，仅允许 `SELECT` 语句
- 对查询结果行数做上限限制
- 使用独立的只读数据源执行报表查询
- 考虑使用参数化查询替代直接拼接

## 3. 大数据量查询性能

**问题**：JdbcTemplate 直接执行 SQL，无分页机制，大数据量查询可能导致 OOM。

**建议**：
- 前端限制查询时间范围
- 后端增加 `LIMIT` 强制截断
- 大数据量场景切换至 ClickHouse 等列式数据库
- 对高频查询结果做缓存

## 4. content 字段存储

**问题**：`report_go_view_project.content` 使用 `LONGTEXT` 存储 JSON 配置，复杂大屏配置可能达到 MB 级别。

**注意**：
- 数据库备份时注意 LONGTEXT 字段大小
- 接口传输大 JSON 时注意请求体大小限制（Spring Boot 默认 2MB）
- 建议前端做增量保存，避免全量提交

## 5. 项目数据隔离

**问题**：项目按 `creator` 字段隔离，但 `creator` 是 VARCHAR 而非外键。

**注意**：
- 删除用户后，其创建的项目仍存在，`creator` 字段变为脏数据
- 分页查询依赖 `creator` 索引，确保索引存在
- 管理员查看所有项目需额外实现接口，当前接口仅返回当前用户的项目

## 6. 发布状态默认值

**问题**：项目创建时默认状态为未发布（`status=1`），但前端可能期望默认已发布。

**注意**：
- 创建后需手动调用更新接口将状态改为已发布（`status=0`）
- 未发布项目在前端预览时应有明确提示
- 状态枚举使用 `CommonStatusEnum`，注意与业务含义的映射关系

## 7. 积木报表版本兼容

**问题**：`jimureport-spring-boot-starter` 和 `jimubi-spring-boot-starter` 版本由父 POM 管理。

**注意**：
- 升级积木报表版本前需在测试环境充分验证
- 积木报表升级可能导致已有报表模板不兼容
- 建议锁定版本，不使用 `LATEST`
- 积木仪表盘（jimubi）与积木报表（jimureport）版本需匹配

## 8. MapStruct 转换遗漏

**问题**：`GoViewProjectConvert` 使用 MapStruct 自动映射，字段名不一致时会静默丢失。

**注意**：
- 新增字段后需确认 VO 和 DO 字段名一致
- 建议编写单元测试验证转换完整性
- 特殊映射需使用 `@Mapping` 注解显式指定

## 9. HTTP 数据源超时

**问题**：`GoViewDataController.getDataByHttp` 调用外部 HTTP 接口，无超时控制。

**建议**：
- 配置连接超时和读取超时（建议 5-10 秒）
- 对外部接口做熔断降级
- 记录请求日志便于排查问题
