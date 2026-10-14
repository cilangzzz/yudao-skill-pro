# 地区管理接口 (AreaController)

> 提供中国地区树查询与 IP 地址归属地解析能力，数据来源于框架内置的 area.csv 与 ip2region.xdb 内存缓存，无数据库表。

## 接口路径前缀

/system/area  (Controller: AreaController)

## 1. 地区查询（AreaController）

该域无独立 Service 层，业务逻辑直接位于 Controller 与框架工具类 `cn.iocoder.yudao.framework.ip.core.utils.AreaUtils` / `IPUtils`（yudao-spring-boot-starter-biz-ip 模块）中：

- `AreaUtils`：类加载时从 classpath 的 `area.csv` 逐行读取地区记录，构建 `Map<Integer, Area>` 内存缓存，并根据 parent 编号建立"省 → 市 → 区县"父子关系树，同时初始化"全球"虚拟根节点。
- `IPUtils`：类加载时将 `ip2region.xdb` 精简版数据整体读入内存（`Searcher.newWithBuffer`），提供 IP → 地区编号的检索能力。

### 1.1 获得地区树

- **路径**: GET /system/area/tree
- **权限**: 已认证（无 @PreAuthorize 注解）
- **说明**: 返回以中国为根的完整地区树（省/市/区县多级嵌套），供前端地区级联选择器使用。

**请求参数**: 无

**响应**: CommonResult<List<AreaNodeRespVO>>

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | Integer | 地区编号，例如 110000 |
| name | String | 地区名字，例如 北京 |
| children | List&lt;AreaNodeRespVO&gt; | 子节点列表，递归结构 |

**业务逻辑**:
1. 调用 `AreaUtils.getArea(Area.ID_CHINA)` 从内存缓存中取出编号为"中国"的根地区节点。
2. 使用 `Assert.notNull` 断言中国节点存在，不存在则抛出 IllegalStateException（提示"获取不到中国"）。
3. 通过 `BeanUtils.toBean` 将中国节点的 children（省级节点及其递归子孙）复制为 AreaNodeRespVO 列表。
4. 以 success 包装 CommonResult 返回，树的层级由 Area 对象自身的 children 递归承载。

### 1.2 获得 IP 对应的地区名

- **路径**: GET /system/area/get-by-ip
- **权限**: 已认证（无 @PreAuthorize 注解）
- **说明**: 解析指定 IPv4 地址的归属地，返回格式化的地区全路径名称。

**请求参数 (Query 参数)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|-----|
| ip | String | 是 | @RequestParam(required = true) | IP 地址，例如 127.0.0.1 |

**响应**: CommonResult&lt;String&gt;（地区名字符串，例如"上海 上海市 静安区"；无法解析时返回"未知"）

**业务逻辑**:
1. 调用 `IPUtils.getArea(ip)`：先由内存中的 ip2region Searcher 检索该 IP 得到地区编号（`search(ip.trim())`），再经 `AreaUtils.getArea` 从地区缓存中取得对应 Area 对象。
2. 若未命中地区（area 为 null，例如境外或无法识别的 IP），直接返回字符串"未知"。
3. 否则调用 `AreaUtils.format(area.getId())`，从当前节点沿 parent 链向上拼接全路径名称，以空格分隔。
4. format 过程中跳过"中国"与"全球"两级父节点（例如返回"上海 上海市 静安区"而非"中国 上海…"），拼接层数以 AreaTypeEnum 枚举长度上限防死循环，最终结果经 CommonResult 返回。

**错误码**: 该域在 ErrorCodeConstants 中无专属错误码（Controller 未引用 ErrorCodeConstants），异常仅来自步骤 2 的 Assert 断言与 IP 解析失败场景。
