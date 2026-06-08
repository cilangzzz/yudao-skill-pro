# 告警管理接口

> 告警模块负责配置告警规则、记录告警事件，并支持多用户通知。

## 关键文件

| 文件 | 说明 |
|-----|------|
| `IotAlertConfigController.java` | 告警配置 Controller |
| `IotAlertConfigService.java` | 告警配置服务接口 |
| `IotAlertConfigServiceImpl.java` | 告警配置服务实现 |
| `IotAlertConfigDO.java` | 告警配置实体类 |
| `IotAlertRecordDO.java` | 告警记录实体类 |

## API 接口列表

### 告警配置

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/alert/config/create` | POST | 创建告警配置 | iot:alert-config:create |
| `/iot/alert/config/update` | PUT | 更新告警配置 | iot:alert-config:update |
| `/iot/alert/config/delete` | DELETE | 删除告警配置 | iot:alert-config:delete |
| `/iot/alert/config/get` | GET | 获取告警配置详情 | iot:alert-config:query |
| `/iot/alert/config/page` | GET | 告警配置分页查询 | iot:alert-config:query |

### 告警记录

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/alert/record/page` | GET | 告警记录分页查询 | iot:alert-record:query |
| `/iot/alert/record/get` | GET | 获取告警记录详情 | iot:alert-record:query |

## 请求/响应示例

### 创建告警配置

**请求**: `POST /iot/alert/config/create`

```json
{
  "name": "设备高温告警",
  "level": 2,
  "status": 1,
  "sceneRuleIds": "1,2,3",
  "receiveUserIds": "100,101,102"
}
```

## 告警级别

| 级别值 | 说明 |
|-------|------|
| 1 | 提示 |
| 2 | 低 |
| 3 | 中 |
| 4 | 高 |
| 5 | 紧急 |

## 告警触发流程

1. 设备上报数据或状态变化
2. 场景联动规则匹配触发条件
3. 规则关联告警配置（通过 `scene_rule_ids`）
4. 系统创建告警记录
5. 根据 `receive_user_ids` 通知相关人员
6. 调用 `AdminUserApi` 获取用户信息进行通知
