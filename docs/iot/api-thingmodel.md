# 物模型管理接口

> 物模型（Thing Model）是 IoT 平台对设备功能的标准化描述，通过属性（Property）、事件（Event）、服务（Service）三要素定义设备能力。

## 关键文件

| 文件 | 说明 |
|-----|------|
| `IotThingModelController.java` | 物模型管理 Controller |
| `IotThingModelService.java` | 物模型管理服务接口 |
| `IotThingModelServiceImpl.java` | 物模型管理服务实现 |
| `IotThingModelMapper.java` | 物模型数据访问层 |
| `IotThingModelDO.java` | 物模型实体类 |

## API 接口列表

### 物模型功能 CRUD

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/thing-model/create` | POST | 创建物模型功能 | iot:thing-model:create |
| `/iot/thing-model/update` | PUT | 更新物模型功能 | iot:thing-model:update |
| `/iot/thing-model/delete` | DELETE | 删除物模型功能 | iot:thing-model:delete |
| `/iot/thing-model/get` | GET | 获取物模型功能详情 | iot:thing-model:query |
| `/iot/thing-model/list` | GET | 物模型功能列表（按产品） | iot:thing-model:query |

## 物模型三要素

### 属性（Property）

属性描述设备的可读/可写状态值。

```json
{
  "type": 1,
  "identifier": "temperature",
  "name": "温度",
  "property": {
    "dataType": "double",
    "unit": "摄氏度",
    "min": -40,
    "max": 85,
    "step": 0.1,
    "accessMode": "r"
  }
}
```

### 事件（Event）

事件描述设备主动上报的通知信息。

```json
{
  "type": 2,
  "identifier": "overheat_alarm",
  "name": "过温告警",
  "event": {
    "type": "alert",
    "outputData": [
      { "identifier": "temperature", "dataType": "double" },
      { "identifier": "threshold", "dataType": "double" }
    ]
  }
}
```

### 服务（Service）

服务描述平台可调用的设备功能。

```json
{
  "type": 3,
  "identifier": "set_report_interval",
  "name": "设置上报周期",
  "service": {
    "inputData": [
      { "identifier": "interval", "dataType": "int", "unit": "秒" }
    ],
    "outputData": [
      { "identifier": "result", "dataType": "bool" }
    ]
  }
}
```

## 功能类型枚举

| 类型值 | 说明 | 用途 |
|-------|------|------|
| 1 | 属性（Property） | 设备状态读写，如温度、湿度、开关状态 |
| 2 | 事件（Event） | 设备主动上报，如告警、故障通知 |
| 3 | 服务（Service） | 平台调用设备功能，如重启、设置参数 |

## 物模型与消息的关系

设备消息的 `method` 字段与物模型标识符关联：

| 消息方向 | method 格式 | 示例 |
|---------|------------|------|
| 属性上报 | `thing.property.post` | 设备上报温度值 |
| 属性设置 | `thing.property.set` | 平台设置设备开关 |
| 事件上报 | `thing.event.post` | 设备上报告警事件 |
| 服务调用 | `thing.service.{identifier}` | 平台调用设备重启服务 |
