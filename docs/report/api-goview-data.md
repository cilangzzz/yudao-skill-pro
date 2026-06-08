# GoView 数据查询 API

> 路径前缀：`/report/go-view/data`
> Controller：`GoViewDataController`

## 概述

GoView 数据查询提供大屏报表的数据源接入能力，采用**策略模式**支持多种查询方式。当前支持 SQL 查询和 HTTP 查询两种数据源策略，可按需扩展（如 Elasticsearch、ClickHouse 等）。

所有查询统一返回 `GoViewDataRespVO` 结构，包含 `dimensions`（维度）和 `source`（数据明细）。

## 接口列表

### 1. SQL 数据源查询

- **路径**：`POST /report/go-view/data/get-by-sql`
- **权限**：`report:go-view-data:get-by-sql`
- **请求体**：`GoViewDataGetBySqlReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sql | String | 是 | SQL 查询语句 |

- **响应**：`CommonResult<GoViewDataRespVO>`
- **业务逻辑**：
  1. 接收 SQL 查询语句
  2. 通过 `JdbcTemplate` 执行查询
  3. 解析结果集，提取列名作为 `dimensions`，行数据作为 `source`
  4. 返回统一数据结构

### 2. HTTP 数据源查询

- **路径**：`POST /report/go-view/data/get-by-http`
- **权限**：`report:go-view-data:get-by-http`
- **请求体**：`GoViewDataGetByHttpReqVO`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | String | 是 | HTTP 数据接口地址 |
| method | String | 否 | 请求方法（默认 GET） |
| params | Map | 否 | 请求参数 |

- **响应**：`CommonResult<GoViewDataRespVO>`
- **业务逻辑**：
  1. 接收 HTTP 请求配置
  2. 发起 HTTP 请求获取数据
  3. 解析 JSON 响应，转换为统一数据结构
  4. 返回 `GoViewDataRespVO`

## 响应数据结构

### GoViewDataRespVO

```json
{
  "dimensions": ["column1", "column2", "column3"],
  "source": [
    { "column1": "value1", "column2": "value2", "column3": "value3" },
    { "column1": "value4", "column2": "value5", "column3": "value6" }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| dimensions | List\<String\> | 维度/列名列表 |
| source | List\<Map\> | 数据明细，每行为一个 Map |

## 服务层设计

### GoViewDataService

```java
public interface GoViewDataService {
    GoViewDataRespVO getDataBySQL(GoViewDataGetBySqlReqVO reqVO);
    GoViewDataRespVO getDataByHttp(GoViewDataGetByHttpReqVO reqVO);
}
```

### 策略扩展

新增数据源类型时，按以下步骤操作：

1. 在 `GoViewDataController` 中新增查询方法
2. 在 `GoViewDataService` 接口中定义新方法
3. 在 `GoViewDataServiceImpl` 中实现查询逻辑
4. 创建对应的请求 VO
5. 添加权限注解

**扩展示例**（Elasticsearch 数据源）：

```java
@RequestMapping("/get-by-es")
@Operation(summary = "使用 Elasticsearch 查询数据")
@PreAuthorize("@ss.hasPermission('report:go-view-data:get-by-es')")
public CommonResult<GoViewDataRespVO> getDataByEs(
        @Valid @RequestBody GoViewDataGetByEsReqVO reqVO) {
    return success(goViewDataService.getDataByEs(reqVO));
}
```

## 数据源底层实现

- **默认实现**：使用 Spring `JdbcTemplate` 执行 SQL 查询
- **可扩展**：支持切换至 ClickHouse 等大数据引擎
- **注意**：SQL 查询直接执行用户传入的 SQL，需注意 SQL 注入风险，生产环境建议增加白名单或参数化机制
