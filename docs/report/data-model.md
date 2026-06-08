# Report 模块数据模型

## 实体继承体系

所有 report 模块实体继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| creator | VARCHAR(64) | 创建人 |
| create_time | DATETIME | 创建时间 |
| updater | VARCHAR(64) | 更新人 |
| update_time | DATETIME | 更新时间 |
| deleted | BIT | 逻辑删除标记 |

## 核心数据表

### report_go_view_project -- GoView 大屏项目表

**实体类**：`GoViewProjectDO`
**继承**：`BaseDO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | BIGINT | 是 | 主键 ID，自增 |
| name | VARCHAR(255) | 是 | 项目名称 |
| pic_url | VARCHAR(1024) | 否 | 预览图片 URL |
| content | LONGTEXT | 否 | 报表内容，JSON 格式配置 |
| status | TINYINT | 是 | 发布状态：0-已发布，1-未发布 |
| remark | VARCHAR(255) | 否 | 项目备注 |

**索引**：

| 索引名 | 列 | 说明 |
|--------|------|------|
| idx_creator | creator | 创建人索引，用于按用户查询 |

**状态枚举**：

| 值 | 含义 |
|----|------|
| 0 | 已发布 |
| 1 | 未发布（默认） |

## ER 关系图

```
┌─────────────────────────┐       ┌───────────────┐
│ report_go_view_project  │       │ system_users  │
├─────────────────────────┤       ├───────────────┤
│ id (PK)                 │       │ id (PK)       │
│ name                    │  N:1  │ username      │
│ pic_url                 │──────>│ ...           │
│ content                 │ creator               │
│ status                  │       └───────────────┘
│ remark                  │
│ creator (FK -> users)   │
│ create_time             │
│ updater                 │
│ update_time             │
│ deleted                 │
└─────────────────────────┘
```

## 数据源说明

| 数据源 | 用途 | 实现 |
|--------|------|------|
| 主数据源 | GoView 项目 CRUD | MyBatis-Plus（GoViewProjectMapper） |
| 动态数据源 | SQL 查询报表数据 | JdbcTemplate（GoViewDataServiceImpl） |
| HTTP 数据源 | HTTP 接口报表数据 | RestTemplate / HttpClient |

## 值对象（VO）

### 请求 VO

| 类名 | 用途 |
|------|------|
| `GoViewProjectCreateReqVO` | 项目创建请求参数 |
| `GoViewProjectUpdateReqVO` | 项目更新请求参数 |
| `GoViewDataGetBySqlReqVO` | SQL 数据查询请求参数 |
| `GoViewDataGetByHttpReqVO` | HTTP 数据查询请求参数 |

### 响应 VO

| 类名 | 用途 |
|------|------|
| `GoViewDataRespVO` | 数据查询统一响应，包含 dimensions 和 source |

## 对象转换

`GoViewProjectConvert`（MapStruct）负责 DO 与 VO 之间的转换：

```
GoViewProjectCreateReqVO  ──convert()──> GoViewProjectDO
GoViewProjectUpdateReqVO  ──convert()──> GoViewProjectDO
```
