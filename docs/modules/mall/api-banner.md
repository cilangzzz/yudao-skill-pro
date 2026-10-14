# Banner 管理接口 (BannerController)

> 提供 mall 首页及各活动页（秒杀、砍价、限时折扣、满减送）轮播 Banner 的管理能力，包括创建、更新、删除、查询与分页。

## 接口路径前缀

/promotion/banner  (Controller: BannerController)

## 1. Banner 管理（BannerController）

### 1.1 创建 Banner

- **路径**: POST /promotion/banner/create
- **权限**: promotion:banner:create
- **说明**: 创建一条 Banner 记录，返回新 Banner 编号。

**请求参数 (BannerCreateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| title | String | 是 | @NotNull | 标题 |
| url | String | 是 | @NotNull | 跳转链接 |
| picUrl | String | 是 | @NotNull | 图片地址 |
| position | Integer | 是 | @NotNull、@InEnum(BannerPositionEnum.class) | Banner 位置（1 首页 / 2 秒杀活动页 / 3 砍价活动页 / 4 限时折扣页 / 5 满减送页） |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum.class) | 状态（0 开启 / 1 关闭） |
| memo | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Long&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Long | 新创建的 Banner 编号 |

**业务逻辑**: 1. 将 BannerCreateReqVO 通过 BannerConvert 转换为 BannerDO；2. 调用 bannerMapper.insert 插入记录；3. 返回插入后生成的主键 id。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_002_000 | Banner 不存在（更新/删除时校验失败场景，创建时不涉及） |

### 1.2 更新 Banner

- **路径**: PUT /promotion/banner/update
- **权限**: promotion:banner:update
- **说明**: 根据 id 更新一条 Banner 记录。

**请求参数 (BannerUpdateReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @NotNull | Banner 编号 |
| title | String | 是 | @NotNull | 标题 |
| url | String | 是 | @NotNull | 跳转链接 |
| picUrl | String | 是 | @NotNull | 图片地址 |
| position | Integer | 是 | @NotNull、@InEnum(BannerPositionEnum.class) | Banner 位置 |
| sort | Integer | 是 | @NotNull | 排序 |
| status | Integer | 是 | @NotNull、@InEnum(CommonStatusEnum.class) | 状态 |
| memo | String | 否 | - | 备注 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 更新成功返回 true |

**业务逻辑**: 1. 校验指定 id 的 Banner 是否存在，不存在则抛出 BANNER_NOT_EXISTS 错误；2. 将 BannerUpdateReqVO 通过 BannerConvert 转换为 BannerDO；3. 调用 bannerMapper.updateById 按 id 更新记录。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_002_000 | Banner 不存在 |

### 1.3 删除 Banner

- **路径**: DELETE /promotion/banner/delete
- **权限**: promotion:banner:delete
- **说明**: 根据 id 删除一条 Banner 记录。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required = true) | Banner 编号 |

**响应**: CommonResult&lt;Boolean&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| data | Boolean | 删除成功返回 true |

**业务逻辑**: 1. 校验指定 id 的 Banner 是否存在，不存在则抛出 BANNER_NOT_EXISTS 错误；2. 调用 bannerMapper.deleteById 删除记录（逻辑删除）。

**错误码**:

| 错误码 | 说明 |
|-------|------|
| 1_013_002_000 | Banner 不存在 |

### 1.4 获得 Banner

- **路径**: GET /promotion/banner/get
- **权限**: promotion:banner:query
- **说明**: 根据编号查询单条 Banner 详情。

**请求参数**: 无（Query 参数）

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| id | Long | 是 | @RequestParam(required = true) | Banner 编号 |

**响应**: CommonResult&lt;BannerRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Long | Banner 编号 |
| title | String | 标题 |
| url | String | 跳转链接 |
| picUrl | String | 图片地址 |
| position | Integer | Banner 位置 |
| sort | Integer | 排序 |
| status | Integer | 状态 |
| memo | String | 备注 |
| createTime | LocalDateTime | 创建时间 |

**业务逻辑**: 1. 调用 bannerMapper.selectById 按 id 查询 BannerDO；2. 通过 BannerConvert 转换为 BannerRespVO 返回（未查到时返回 null）。

### 1.5 获得 Banner 分页

- **路径**: GET /promotion/banner/page
- **权限**: promotion:banner:query
- **说明**: 分页查询 Banner 列表，支持按标题、状态、创建时间区间过滤。

**请求参数 (BannerPageReqVO，继承 PageParam：pageNo 默认 1 / pageSize 默认 10)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|-----|---------|------|
| pageNo | Integer | 否 | - | 页码，从 1 开始（PageParam 继承字段） |
| pageSize | Integer | 否 | - | 每页条数（PageParam 继承字段） |
| title | String | 否 | - | 标题，模糊匹配 |
| status | Integer | 否 | @InEnum(CommonStatusEnum.class) | 状态 |
| createTime | LocalDateTime[] | 否 | @DateTimeFormat(yyyy-MM-dd HH:mm:ss) | 创建时间区间（起止两个元素） |

**响应**: CommonResult&lt;PageResult&lt;BannerRespVO&gt;&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| list | BannerRespVO[] | 当前页 Banner 列表，字段同 1.4 |
| total | Long | 总条数 |

**业务逻辑**: 1. 将 BannerPageReqVO 直接传给 bannerMapper.selectPage 执行条件分页查询（title 模糊、status 精确、createTime 区间）；2. 通过 BannerConvert.convertPage 将 PageResult&lt;BannerDO&gt; 转换为 PageResult&lt;BannerRespVO&gt; 返回。

## 补充说明

- **Banner 位置枚举 (BannerPositionEnum)**: 1 首页、2 秒杀活动页、3 砍价活动页、4 限时折扣页、5 满减送页。
- **错误码段**: Banner 相关错误码使用 1_013_002_000 段（promotion 模块 ErrorCodeConstants），目前仅 BANNER_NOT_EXISTS（1_013_002_000 "Banner 不存在"），由 update/delete 等操作的 validateBannerExists 校验触发。
- Service 还提供 addBannerBrowseCount（增加 Banner 点击次数）与 getBannerListByPosition（按位置查询启用 Banner 列表），两者由 App 端接口调用，不在本 admin 控制器端点范围内。
