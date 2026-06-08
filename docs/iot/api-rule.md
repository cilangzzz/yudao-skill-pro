# 规则引擎与数据流转接口

> 规则引擎基于触发器-条件-动作（Trigger-Condition-Action）模型，实现场景联动自动化和数据流转。

## 关键文件

| 文件 | 说明 |
|-----|------|
| `IotSceneRuleController.java` | 场景联动规则 Controller |
| `IotSceneRuleService.java` | 场景联动规则服务接口 |
| `IotSceneRuleServiceImpl.java` | 场景联动规则服务实现 |
| `IotDataSinkController.java` | 数据流转目的地 Controller |
| `IotDataSinkService.java` | 数据流转目的地服务接口 |
| `IotSceneRuleDO.java` | 场景联动规则实体类 |
| `IotDataSinkDO.java` | 数据流转目的地实体类 |

## API 接口列表

### 场景联动规则

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/scene-rule/create` | POST | 创建场景联动规则 | iot:scene-rule:create |
| `/iot/scene-rule/update` | PUT | 更新场景联动规则 | iot:scene-rule:update |
| `/iot/scene-rule/delete` | DELETE | 删除场景联动规则 | iot:scene-rule:delete |
| `/iot/scene-rule/get` | GET | 获取场景联动规则详情 | iot:scene-rule:query |
| `/iot/scene-rule/page` | GET | 场景联动规则分页查询 | iot:scene-rule:query |
| `/iot/scene-rule/update-status` | PUT | 更新规则启用状态 | iot:scene-rule:update |

### 数据流转目的地

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/data-sink/create` | POST | 创建数据流转目的地 | iot:data-sink:create |
| `/iot/data-sink/update` | PUT | 更新数据流转目的地 | iot:data-sink:update |
| `/iot/data-sink/delete` | DELETE | 删除数据流转目的地 | iot:data-sink:delete |
| `/iot/data-sink/get` | GET | 获取数据流转目的地详情 | iot:data-sink:query |
| `/iot/data-sink/page` | GET | 数据流转目的地分页查询 | iot:data-sink:query |

## 请求/响应示例

### 创建场景联动规则

**请求**: `POST /iot/scene-rule/create`

```json
{
  "name": "高温告警联动",
  "status": 1,
  "triggers": [
    {
      "type": "device_property",
      "productKey": "abc123",
      "deviceName": "sensor-001",
      "identifier": "temperature",
      "operator": ">=",
      "value": "40"
    }
  ],
  "actions": [
    {
      "type": "device_service",
      "productKey": "abc123",
      "deviceName": "actuator-001",
      "identifier": "switch",
      "value": "on"
    },
    {
      "type": "send_notification",
      "alertConfigId": 1
    }
  ]
}
```

### 创建数据流转目的地

**请求**: `POST /iot/data-sink/create`

```json
{
  "name": "Kafka 数据管道",
  "type": "Kafka",
  "config": {
    "bootstrapServers": "kafka:9092",
    "topic": "iot-device-data",
    "acks": "all"
  }
}
```

## 场景联动执行流程

```
设备消息上报
    |
    v
触发器匹配（Trigger Matcher）
    |
    v
执行条件判断（Condition Matcher）  <-- 责任链模式
    |
    v
动作执行（Action Executor）
    |
    +---> 设备服务调用
    +---> 发送通知
    +---> 数据流转
    +---> 延时执行
```

## 数据流转目的地类型

| 类型 | 说明 | 配置项 |
|-----|------|-------|
| HTTP | 推送到 HTTP 接口 | url, method, headers |
| MQTT | 转发到 MQTT 主题 | broker, topic, qos |
| Kafka | 写入 Kafka 主题 | bootstrapServers, topic |
| RabbitMQ | 发送到 RabbitMQ 交换机 | host, exchange, routingKey |
| Redis | 写入 Redis | host, key, dataType |
| RocketMQ | 写入 RocketMQ 主题 | namesrvAddr, topic |
| TCP | 转发到 TCP 服务 | host, port |
| WebSocket | 推送到 WebSocket 客户端 | url, headers |
