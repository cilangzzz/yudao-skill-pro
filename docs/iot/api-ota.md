# OTA 升级管理接口

> OTA（Over-The-Air）升级模块管理固件版本、升级任务和升级记录，支持设备远程固件升级。

## 关键文件

| 文件 | 说明 |
|-----|------|
| `IotOtaFirmwareController.java` | 固件管理 Controller |
| `IotOtaFirmwareService.java` | 固件管理服务接口 |
| `IotOtaTaskController.java` | 升级任务 Controller |
| `IotOtaTaskService.java` | 升级任务服务接口 |
| `IotOtaFirmwareDO.java` | 固件实体类 |
| `IotOtaTaskDO.java` | 升级任务实体类 |
| `IotOtaTaskRecordDO.java` | 升级记录实体类 |

## API 接口列表

### 固件管理

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/ota/firmware/create` | POST | 创建固件 | iot:ota-firmware:create |
| `/iot/ota/firmware/update` | PUT | 更新固件 | iot:ota-firmware:update |
| `/iot/ota/firmware/delete` | DELETE | 删除固件 | iot:ota-firmware:delete |
| `/iot/ota/firmware/get` | GET | 获取固件详情 | iot:ota-firmware:query |
| `/iot/ota/firmware/page` | GET | 固件分页查询 | iot:ota-firmware:query |
| `/iot/ota/firmware/get-latest` | GET | 获取最新版本固件 | iot:ota-firmware:query |

### 升级任务

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/ota/task/create` | POST | 创建升级任务 | iot:ota-task:create |
| `/iot/ota/task/update` | PUT | 更新升级任务 | iot:ota-task:update |
| `/iot/ota/task/delete` | DELETE | 删除升级任务 | iot:ota-task:delete |
| `/iot/ota/task/get` | GET | 获取升级任务详情 | iot:ota-task:query |
| `/iot/ota/task/page` | GET | 升级任务分页查询 | iot:ota-task:query |
| `/iot/ota/task/update-status` | PUT | 更新任务状态 | iot:ota-task:update |

### 升级记录

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/ota/task-record/page` | GET | 升级记录分页查询 | iot:ota-task-record:query |

## 请求/响应示例

### 创建固件

**请求**: `POST /iot/ota/firmware/create`

```json
{
  "name": "v2.0.0 固件",
  "version": "2.0.0",
  "productId": 1,
  "fileUrl": "https://cdn.example.com/firmware/v2.0.0.bin",
  "fileSize": 1048576,
  "fileDigestAlgorithm": "SHA256",
  "fileDigestValue": "abcdef1234567890..."
}
```

### 创建升级任务

**请求**: `POST /iot/ota/task/create`

```json
{
  "name": "v2.0.0 全量升级",
  "firmwareId": 1,
  "productId": 1,
  "deviceIds": [1, 2, 3]
}
```

## OTA 升级流程

```
1. 上传固件 --> 创建固件记录
2. 创建升级任务 --> 关联固件和目标设备
3. 下发升级通知 --> 通过消息总线推送到设备
4. 设备下载固件 --> 设备请求固件下载地址
5. 设备安装固件 --> 设备执行升级
6. 设备上报结果 --> 更新升级记录状态
```

## 升级任务状态

| 状态值 | 说明 |
|-------|------|
| 0 | 待执行 |
| 1 | 执行中 |
| 2 | 已完成 |
| 3 | 已取消 |

## 升级记录状态

| 状态值 | 说明 |
|-------|------|
| 0 | 待升级 |
| 1 | 升级中 |
| 2 | 升级成功 |
| 3 | 升级失败 |
