# 设备管理接口

> 设备是 IoT 平台的核心实体，涵盖设备的注册、认证、状态管理、分组管理、属性存储和消息处理。

## 关键文件

| 文件 | 说明 |
|-----|------|
| `IotDeviceController.java` | 设备管理 Controller，管理后台接口 |
| `IotDeviceService.java` | 设备管理服务接口 |
| `IotDeviceServiceImpl.java` | 设备管理服务实现 |
| `IotDeviceMapper.java` | 设备数据访问层 |
| `IotDeviceDO.java` | 设备实体类 |
| `IotDeviceCommonApi.java` | 设备通用 API（供 gateway 层调用） |

## API 接口列表

### 设备 CRUD

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/device/create` | POST | 创建设备 | iot:device:create |
| `/iot/device/update` | PUT | 更新设备 | iot:device:update |
| `/iot/device/delete` | DELETE | 删除设备 | iot:device:delete |
| `/iot/device/get` | GET | 获取设备详情 | iot:device:query |
| `/iot/device/page` | GET | 设备分页查询 | iot:device:query |
| `/iot/device/get-by-ids` | GET | 批量获取设备 | iot:device:query |

### 设备业务操作

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/device/update-state` | PUT | 更新设备状态 | iot:device:update |
| `/iot/device/auth` | POST | 设备认证 | - |
| `/iot/device/register` | POST | 设备动态注册 | - |

### 设备分组

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/device-group/create` | POST | 创建设备分组 | iot:device-group:create |
| `/iot/device-group/update` | PUT | 更新设备分组 | iot:device-group:update |
| `/iot/device-group/delete` | DELETE | 删除设备分组 | iot:device-group:delete |
| `/iot/device-group/get` | GET | 获取设备分组详情 | iot:device-group:query |
| `/iot/device-group/page` | GET | 设备分组分页查询 | iot:device-group:query |

## 请求/响应示例

### 创建设备

**请求**: `POST /iot/device/create`

```json
{
  "deviceName": "sensor-001",
  "nickname": "温度传感器-001",
  "serialNumber": "SN20260001",
  "productId": 1,
  "gatewayId": null
}
```

**响应**: `CommonResult<Long>`

```json
{
  "code": 0,
  "msg": "",
  "data": 1
}
```

### 设备分页查询

**请求**: `GET /iot/device/page?pageNo=1&pageSize=10&productId=1&state=1`

**响应**: `CommonResult<PageResult<IotDeviceRespVO>>`

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "list": [
      {
        "id": 1,
        "deviceName": "sensor-001",
        "nickname": "温度传感器-001",
        "productKey": "abc123",
        "state": 1,
        "onlineTime": "2026-03-18 10:00:00"
      }
    ],
    "total": 1
  }
}
```

### 设备认证

**请求**: `POST /iot/device/auth`

```json
{
  "productKey": "abc123",
  "deviceName": "sensor-001",
  "deviceSecret": "xxxxxxxxxxxx"
}
```

**响应**: `CommonResult<Boolean>`

```json
{
  "code": 0,
  "msg": "",
  "data": true
}
```

### 设备动态注册

**请求**: `POST /iot/device/register`

```json
{
  "productKey": "abc123",
  "deviceName": "sensor-002",
  "sign": "signature_value",
  "signMethod": "hmacsha256",
  "timestamp": "1710739200000"
}
```

**响应**: `CommonResult<IotDeviceRegisterRespDTO>`

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "deviceSecret": "generated_secret"
  }
}
```

## 设备状态流转

```
未激活(0) --[设备认证/激活]--> 在线(1)
在线(1)   --[设备断开连接]--> 离线(2)
离线(2)   --[设备重新连接]--> 在线(1)
```

## 设备认证流程

1. 设备通过协议（MQTT/CoAP/HTTP 等）发起连接
2. 网关层调用 `IotDeviceCommonApi.authDevice()` 进行认证
3. 系统根据 `productKey + deviceName` 查询设备缓存
4. 校验 `deviceSecret` 是否匹配
5. 认证成功后更新设备状态为在线
6. 认证失败返回错误，设备连接被拒绝

## 设备动态注册流程

1. 产品开启动态注册功能（`register_enabled = true`）
2. 设备携带 `productKey` 发起注册请求
3. 系统验证签名（基于 `productSecret`）
4. 生成设备密钥 `deviceSecret`
5. 创建设备记录，返回 `deviceSecret` 给设备
6. 设备使用 `deviceSecret` 进行后续认证

## 设备消息处理

设备消息通过内部消息总线 `IotMessageBus` 在 gateway 和 biz 之间传递：

- **上行消息** (`device:message:upstream`): 设备 -> gateway -> biz 层处理
- **下行消息** (`device:message:downstream`): biz 层 -> gateway -> 设备

消息方法(method)包括：
- `thing.property.post` - 设备属性上报
- `thing.property.set` - 平台设置设备属性
- `thing.event.post` - 设备事件上报
- `thing.service.invoke` - 平台调用设备服务
