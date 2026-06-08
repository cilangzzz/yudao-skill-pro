# 积木报表集成 API

> 框架层：`framework/jmreport/`
> 依赖：`jimureport-spring-boot-starter`、`jimubi-spring-boot-starter`

## 概述

积木报表（JimuReport）是模块内置的报表引擎，提供报表设计、打印设计、图形设计、大屏设计等能力。本模块通过框架层扩展点将积木报表与 yudao 认证体系打通。

积木报表的 HTTP API 由框架自动注册（路径通常为 `/jmreport/**`），本模块不直接暴露接口，而是通过**实现框架扩展接口**来注入自定义逻辑。

## 扩展点

### 1. JmReportTokenServiceImpl -- Token 认证适配

**设计模式**：适配器模式

**职责**：将 yudao 的 OAuth2 认证体系适配到积木报表的 `JmReportTokenServiceI` 接口。

**核心方法**：

| 方法 | 说明 |
|------|------|
| `createToken()` | 创建 Token（委托给 yudao OAuth2 体系） |
| `verifyToken()` | 验证 Token 有效性 |
| `getUserInfo()` | 根据 Token 获取用户信息 |

**调用链**：

```
积木报表请求 -> JmReportTokenServiceImpl.verifyToken()
             -> OAuth2TokenCommonApi (system 模块)
             -> 返回用户信息
```

### 2. JmOnlDragExternalServiceImpl -- 仪表盘扩展

**职责**：为积木仪表盘（JimuBI）提供外部数据源扩展服务。

**说明**：实现积木仪表盘的拖拽式设计器所需的数据接口扩展。

### 3. JmReportConfiguration -- 积木报表配置

**职责**：配置积木报表运行参数。

**关键配置项**：

| 配置 | 说明 |
|------|------|
| 数据源配置 | 积木报表使用的数据源（默认复用应用主数据源） |
| Token 传递 | 通过 `customApiHeader` 方法处理 Token 传递 |
| 文件存储 | 报表模板文件存储路径 |

### 4. SecurityConfiguration -- 安全配置

**职责**：配置积木报表路径的安全策略，确保 `/jmreport/**` 路径正确走认证流程。

## 权限校验

积木报表的权限校验通过 `PermissionCommonApi`（system 模块）实现：

```
积木报表操作 -> JmReportTokenServiceImpl
             -> PermissionCommonApi.checkPermission()
             -> 允许/拒绝
```

## 使用流程

### 设计报表

1. 登录管理后台，进入报表设计页面
2. 积木报表设计器自动加载（前端通过 iframe 嵌入）
3. 设计器请求经过 `/jmreport/**` 路径
4. `JmReportTokenServiceImpl` 自动完成 Token 验证

### 设计大屏

1. 进入仪表盘设计页面
2. 积木仪表盘设计器加载
3. 拖拽组件并绑定数据源
4. `JmOnlDragExternalServiceImpl` 提供数据接口

## 配置依赖

```xml
<!-- 积木报表 -->
<dependency>
    <groupId>org.jeecgframework.jimureport</groupId>
    <artifactId>jimureport-spring-boot-starter</artifactId>
</dependency>

<!-- 积木仪表盘 -->
<dependency>
    <groupId>org.jeecgframework.jimubi</groupId>
    <artifactId>jimubi-spring-boot-starter</artifactId>
</dependency>
```

版本由父 POM 统一管理。
