# 设计模式索引

## 模式清单

### 创建型模式

#### 工厂模式

- **文件**：[factory-pattern.md](./factory-pattern.md)
- **适用模块**：pay、infra
- **描述**：创建对象实例的工厂接口，支持多类型扩展

### 行为型模式

#### 模板方法模式

- **文件**：[template-method-pattern.md](./template-method-pattern.md)
- **适用模块**：pay、infra
- **描述**：定义算法骨架，子类实现具体步骤

#### 策略模式

- **文件**：[strategy-pattern.md](./strategy-pattern.md)
- **适用模块**：pay、infra、ai
- **描述**：封装可互换的算法族

## 模式选择指南

| 场景 | 推荐模式 | 示例 |
|------|---------|------|
| 需要根据配置创建不同类型的客户端 | factory-pattern、strategy-pattern | 支付渠道、短信渠道 |
| 需要统一处理流程，但具体实现不同 | template-method-pattern | 支付下单流程、短信发送流程 |
| 需要动态切换算法或行为 | strategy-pattern | AI 模型切换、支付方式切换 |

## 模式组合

### 工厂 + 策略

- **描述**：工厂创建策略实例
- **用法**：PayClientFactory 创建 PayClient 实例

### 工厂 + 模板方法

- **描述**：工厂创建模板方法的具体实现
- **用法**：SmsClientFactory 创建 AbstractSmsClient 子类

### 模板方法 + 策略

- **描述**：模板方法定义骨架，策略实现变化部分
- **用法**：AbstractPayClient 定义骨架，具体 PayClient 实现策略

## 扩展指南

### 新增模式

1. 创建模式知识库文件：`skills/design/patterns/{pattern}-pattern.md`
2. 更新此索引文件
3. 关联应用到相关模块
