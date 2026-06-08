# IoT 模块数据模型

> 本文档描述 IoT 模块所有数据表的完整字段定义、索引和表间关系。

## 实体继承体系

| 基类 | 说明 | 适用场景 |
|-----|------|---------|
| TenantBaseDO | 租户基础类，包含租户 ID | 设备、产品、场景规则等需要租户隔离的实体 |
| BaseDO | 通用基础类，包含创建/更新时间、创建/更新人 | 设备分组、固件、告警记录等不需要租户隔离的实体 |

## 核心数据表

### iot_device（设备表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 设备 ID，主键 |
| device_name | VARCHAR(64) | 设备名称，产品内唯一 |
| nickname | VARCHAR(64) | 设备备注名称 |
| serial_number | VARCHAR(64) | 设备序列号 |
| product_id | BIGINT | 产品编号 |
| product_key | VARCHAR(32) | 产品标识（冗余） |
| device_type | INT | 设备类型（冗余） |
| gateway_id | BIGINT | 网关设备编号（子设备） |
| state | INT | 设备状态：0未激活、1在线、2离线 |
| device_secret | VARCHAR(64) | 设备密钥 |
| group_ids | VARCHAR(255) | 设备分组编号集合（JSON） |
| firmware_id | BIGINT | 固件编号 |
| latitude | DECIMAL(10,6) | 纬度 |
| longitude | DECIMAL(10,6) | 经度 |
| online_time | DATETIME | 最后上线时间 |
| offline_time | DATETIME | 最后离线时间 |
| active_time | DATETIME | 激活时间 |

**索引**:
- `idx_product_id` - 普通索引，product_id
- `idx_product_key_device_name` - 唯一索引，product_key + device_name

### iot_device_group（设备分组表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 分组 ID |
| name | VARCHAR(64) | 分组名称 |
| status | INT | 分组状态 |
| description | VARCHAR(255) | 分组描述 |

### iot_device_message（设备消息表）

> 存储引擎：TDengine 时序数据库

| 字段 | 类型 | 说明 |
|-----|------|------|
| device_id | BIGINT | 设备编号 |
| product_key | VARCHAR(32) | 产品标识 |
| device_name | VARCHAR(64) | 设备名称 |
| method | VARCHAR(64) | 消息方法 |
| request_id | VARCHAR(64) | 请求 ID |
| payload | TEXT | 消息内容 |

### iot_product（产品表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 产品 ID |
| name | VARCHAR(64) | 产品名称 |
| product_key | VARCHAR(32) | 产品标识 |
| product_secret | VARCHAR(64) | 产品密钥 |
| category_id | BIGINT | 产品分类编号 |
| device_type | INT | 设备类型 |
| net_type | INT | 联网方式 |
| protocol_type | VARCHAR(32) | 协议类型 |
| serialize_type | VARCHAR(32) | 序列化类型 |
| status | INT | 产品状态 |
| register_enabled | BOOLEAN | 是否开启动态注册 |

### iot_product_category（产品分类表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 分类 ID |
| name | VARCHAR(64) | 分类名称 |
| parent_id | BIGINT | 父分类 ID |
| sort | INT | 排序 |

### iot_thing_model（物模型功能表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 物模型功能 ID |
| product_id | BIGINT | 产品编号 |
| product_key | VARCHAR(32) | 产品标识 |
| identifier | VARCHAR(64) | 功能标识符 |
| name | VARCHAR(64) | 功能名称 |
| type | INT | 功能类型：1属性、2事件、3服务 |
| property | JSON | 属性定义 |
| event | JSON | 事件定义 |
| service | JSON | 服务定义 |

### iot_scene_rule（场景联动规则表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 场景联动 ID |
| name | VARCHAR(64) | 场景名称 |
| status | INT | 状态 |
| triggers | JSON | 触发器配置 |
| actions | JSON | 动作配置 |
| last_trigger_time | DATETIME | 最后触发时间 |

### iot_data_sink（数据流转目的地表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 数据目的地 ID |
| name | VARCHAR(64) | 名称 |
| type | VARCHAR(32) | 类型：HTTP/MQTT/Kafka/RabbitMQ/Redis/RocketMQ/TCP/WebSocket |
| config | JSON | 配置信息 |

### iot_alert_config（告警配置表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 告警配置 ID |
| name | VARCHAR(64) | 告警名称 |
| level | INT | 告警级别 |
| status | INT | 状态 |
| scene_rule_ids | VARCHAR(255) | 关联的场景规则 ID 列表 |
| receive_user_ids | VARCHAR(255) | 接收用户 ID 列表 |

### iot_ota_firmware（OTA 固件表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 固件 ID |
| name | VARCHAR(64) | 固件名称 |
| version | VARCHAR(32) | 版本号 |
| product_id | BIGINT | 产品编号 |
| file_url | VARCHAR(512) | 固件文件 URL |
| file_size | BIGINT | 文件大小 |
| file_digest_algorithm | VARCHAR(32) | 签名算法 |
| file_digest_value | VARCHAR(128) | 签名值 |

### iot_ota_task（OTA 升级任务表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 任务 ID |
| name | VARCHAR(64) | 任务名称 |
| firmware_id | BIGINT | 固件编号 |
| product_id | BIGINT | 产品编号 |
| status | INT | 任务状态 |

### iot_ota_task_record（OTA 升级记录表）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | BIGINT | 记录 ID |
| task_id | BIGINT | 任务 ID |
| device_id | BIGINT | 设备 ID |
| status | INT | 升级状态 |

## 表间关系（ER 关系）

```
iot_product_category (1) <-- (N) iot_product (1) <-- (N) iot_device
                                    |                        |
                                    |                        +-- (N:1) iot_device (gateway_id, 子设备->网关)
                                    |
                                    +-- (1) <-- (N) iot_thing_model
                                    |
                                    +-- (1) <-- (N) iot_ota_firmware (1) <-- (N) iot_ota_task
                                                                              |
                                                                              +-- (1) <-- (N) iot_ota_task_record

iot_scene_rule <--> iot_alert_config (通过 scene_rule_ids 关联)
```

| 源表 | 目标表 | 关系 | 外键 | 说明 |
|-----|-------|------|-----|------|
| iot_device | iot_product | N:1 | product_id | 设备属于某个产品 |
| iot_device | iot_device | N:1 | gateway_id | 子设备关联网关设备 |
| iot_product | iot_product_category | N:1 | category_id | 产品属于某个分类 |
| iot_thing_model | iot_product | N:1 | product_id | 物模型属于某个产品 |
| iot_ota_firmware | iot_product | N:1 | product_id | 固件属于某个产品 |
| iot_ota_task | iot_ota_firmware | N:1 | firmware_id | 升级任务使用某个固件 |
| iot_ota_task_record | iot_ota_task | N:1 | task_id | 升级记录属于某个任务 |
| iot_ota_task_record | iot_device | N:1 | device_id | 升级记录关联设备 |
