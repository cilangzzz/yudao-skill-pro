# 文件管理接口

## 概述

文件管理是 infra 模块的核心功能之一，提供统一的文件上传、下载、管理能力，支持多种存储渠道。

### 业务定位

- 统一的文件存储抽象层，屏蔽底层存储差异
- 支持本地存储、S3、FTP、SFTP、数据库等多种存储方式
- 通过 FileConfigDO 配置管理多存储渠道，支持主配置切换

### 核心实体

| 实体 | 说明 |
|-----|------|
| FileDO | 文件记录，存储文件元信息（路径、URL、大小、类型等） |
| FileConfigDO | 存储渠道配置，包含存储类型和连接配置 |
| FileContentDO | 文件内容表，仅数据库存储方式使用 |

## 接口列表

### 1. 上传文件

- **路径**: `POST /infra/file/upload`
- **说明**: 上传文件到主配置的存储渠道
- **权限**: 无需特定权限（App 端也可调用）
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| file | MultipartFile | 是 | 文件内容 |
| directory | String | 否 | 自定义目录 |

- **响应**: `CommonResult<String>` - 文件访问 URL
- **实现逻辑**:
  1. 读取文件字节内容
  2. 调用 `FileService.createFile()` 生成唯一路径并上传
  3. 保存文件记录到 `infra_file` 表
  4. 返回文件访问 URL

### 2. 文件列表查询

- **路径**: `GET /infra/file/list`
- **说明**: 分页查询文件列表
- **权限**: `infra:file:query`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| path | String | 否 | 文件路径（模糊匹配） |
| name | String | 否 | 文件名（模糊匹配） |
| createTime | Date[] | 否 | 创建时间范围 |
| pageNo | Integer | 是 | 页码 |
| pageSize | Integer | 是 | 每页大小 |

- **响应**: `CommonResult<PageResult<FileDO>>`

### 3. 删除文件

- **路径**: `DELETE /infra/file/delete`
- **说明**: 删除指定文件
- **权限**: `infra:file:delete`
- **请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | Long | 是 | 文件编号 |

- **响应**: `CommonResult<Boolean>`

## 文件配置接口

### 4. 文件配置列表

- **路径**: `GET /infra/file-config/list`
- **说明**: 查询所有文件存储配置
- **权限**: `infra:file-config:query`
- **响应**: `CommonResult<List<FileConfigDO>>`

### 5. 创建文件配置

- **路径**: `POST /infra/file-config/create`
- **说明**: 创建新的文件存储配置
- **权限**: `infra:file-config:create`
- **请求参数**: FileConfigDO 对象（含 name, storage, config 等字段）

### 6. 更新文件配置

- **路径**: `PUT /infra/file-config/update`
- **说明**: 更新文件存储配置
- **权限**: `infra:file-config:update`

### 7. 删除文件配置

- **路径**: `DELETE /infra/file-config/delete`
- **说明**: 删除文件存储配置
- **权限**: `infra:file-config:delete`

## App 端接口

### 8. App 端上传文件

- **路径**: `POST /app/infra/file/upload`
- **说明**: App 端专用文件上传接口
- **权限**: 需要 App 用户登录

## 存储类型

| 存储类型 | 枚举值 | 配置类 | 客户端类 |
|---------|-------|-------|---------|
| 数据库 | 0 | DatabaseFileClientConfig | DatabaseFileClient |
| 本地磁盘 | 10 | LocalFileClientConfig | LocalFileClient |
| S3/MinIO | 20 | S3FileClientConfig | S3FileClient |
| FTP | 30 | FtpFileClientConfig | FtpFileClient |
| SFTP | 40 | SftpFileClientConfig | SftpFileClient |

## 关键实现

- **FileService**: 文件管理服务接口，定义上传/下载/删除等操作
- **FileConfigService**: 文件配置服务，管理 FileClient 缓存和生命周期
- **FileClient**: 文件客户端接口，定义统一的存储操作
- **AbstractFileClient**: 抽象客户端，实现模板方法模式（init + refresh）
- **FileClientFactory**: 工厂类，根据 FileStorageEnum 创建对应客户端实例
- **FileClientFactoryImpl**: 工厂实现，使用 Guava LoadingCache 缓存客户端，10 秒异步刷新

## 模块间调用

其他模块通过 `FileApi` 接口调用文件服务：

```java
// 其他模块上传文件示例
String url = fileApi.createFile(content, name, directory, type);
```

- `FileApi.createFile()` - 上传文件，返回 URL
- `FileApi.presignGetUrl()` - 获取预签名访问地址
