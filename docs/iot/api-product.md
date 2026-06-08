# 产品管理接口

> 产品是设备的模板，定义物模型（属性、事件、服务）、协议配置和序列化方式。同一产品下的设备共享相同的物模型定义。

## 关键文件

| 文件 | 说明 |
|-----|------|
| `IotProductController.java` | 产品管理 Controller |
| `IotProductService.java` | 产品管理服务接口 |
| `IotProductServiceImpl.java` | 产品管理服务实现 |
| `IotProductMapper.java` | 产品数据访问层 |
| `IotProductDO.java` | 产品实体类 |
| `IotProductCategoryDO.java` | 产品分类实体类 |

## API 接口列表

### 产品 CRUD

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/product/create` | POST | 创建产品 | iot:product:create |
| `/iot/product/update` | PUT | 更新产品 | iot:product:update |
| `/iot/product/delete` | DELETE | 删除产品 | iot:product:delete |
| `/iot/product/get` | GET | 获取产品详情 | iot:product:query |
| `/iot/product/page` | GET | 产品分页查询 | iot:product:query |
| `/iot/product/get-by-product-key` | GET | 根据产品标识获取产品 | iot:product:query |

### 产品分类

| 接口路径 | HTTP 方法 | 说明 | 权限标识 |
|---------|----------|------|---------|
| `/iot/product-category/create` | POST | 创建产品分类 | iot:product-category:create |
| `/iot/product-category/update` | PUT | 更新产品分类 | iot:product-category:update |
| `/iot/product-category/delete` | DELETE | 删除产品分类 | iot:product-category:delete |
| `/iot/product-category/get` | GET | 获取产品分类详情 | iot:product-category:query |
| `/iot/product-category/list` | GET | 产品分类列表 | iot:product-category:query |

## 请求/响应示例

### 创建产品

**请求**: `POST /iot/product/create`

```json
{
  "name": "智能温湿度传感器",
  "categoryId": 1,
  "deviceType": 1,
  "netType": 1,
  "protocolType": "mqtt",
  "serializeType": "json",
  "registerEnabled": true
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

### 产品分页查询

**请求**: `GET /iot/product/page?pageNo=1&pageSize=10&name=传感器`

**响应**: `CommonResult<PageResult<IotProductRespVO>>`

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "智能温湿度传感器",
        "productKey": "abc123",
        "deviceType": 1,
        "protocolType": "mqtt",
        "status": 1,
        "deviceCount": 50
      }
    ],
    "total": 1
  }
}
```

## 产品配置项说明

| 字段 | 说明 | 可选值 |
|-----|------|-------|
| deviceType | 设备类型 | 直连设备、网关设备、网关子设备 |
| netType | 联网方式 | WiFi、蜂窝网络（2G/3G/4G/5G）、以太网、LoRa、NB-IoT 等 |
| protocolType | 协议类型 | mqtt、coap、http、tcp、udp、websocket、modbus、emqx |
| serializeType | 序列化类型 | json、protobuf、custom |
| registerEnabled | 动态注册 | true / false |

## 产品与设备的关系

- 产品是设备的模板，设备通过 `product_id` 关联产品
- 设备创建时自动继承产品的 `product_key`、`device_type`、协议配置
- 产品定义物模型，设备上报的数据遵循物模型规范
- 删除产品前需确保无设备关联
