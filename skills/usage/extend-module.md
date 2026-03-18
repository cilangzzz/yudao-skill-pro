# Skill 使用指南 - 扩展模块场景

本文档提供完整的提示词模板，用于指导 AI 扩展现有模块功能。基于项目中 12 个模块的 Skill 文档提炼，覆盖最常见的扩展场景。

---

## 一、场景说明

### 何时使用扩展模块

扩展模块场景适用于以下情况：

| 场景类型 | 描述 | 典型示例 |
|---------|------|---------|
| **新增渠道/平台** | 为模块添加新的外部服务接入能力 | 新增支付渠道（银联）、新增AI平台（Claude）、新增存储类型（阿里云OSS） |
| **新增策略实现** | 扩展现有策略模式的新策略 | 新增审批人策略、新增消息推送渠道 |
| **新增业务实体** | 在模块内添加新的业务对象 | 新增审批类型（报销审批）、新增AI能力（语音合成） |
| **功能增强** | 扩展现有功能的能力范围 | 支付新增分期付款、工作流新增监听器 |

### 扩展前判断标准

在使用本文档前，请确认：

1. **模块已存在** - 目标模块在 `yudao-module-*` 中已定义
2. **有对应 Skill 文档** - 在 `skills/modules/{module}/skill-{module}.yaml` 中有知识文档
3. **扩展类型明确** - 明确是渠道扩展、策略扩展还是业务实体扩展
4. **遵循现有模式** - 参考现有实现，保持架构一致性

---

## 二、提示词模板

### 模板概述

以下模板遵循"角色-上下文-分析-输出"四段式结构，确保 AI 能够准确理解需求并生成符合项目规范的代码。

### 完整提示词模板

```markdown
## 角色

你是一位资深的 Java 架构师，精通 Spring Boot、MyBatis-Plus、设计模式，熟悉 yudao-vue-pro 项目架构。
你将帮助用户扩展现有模块的功能，确保新功能符合项目规范、代码风格一致。

## 上下文

### 项目信息
- 项目：yudao-vue-pro（芋道源码）
- 架构：分层架构（Controller -> Service -> DAL），模块化设计
- 技术栈：Spring Boot 3.x、MyBatis-Plus、Spring AI、Flowable 等

### 目标模块
- 模块名称：{模块名称，如 pay/ai/infra/bpm}
- 模块路径：yudao-module-{模块}
- Skill 文档：skills/modules/{模块}/skill-{模块}.yaml

### 扩展需求
- 扩展类型：{渠道扩展 | 策略扩展 | 业务实体扩展}
- 具体需求：{详细描述要扩展的功能}

### 参考实现
请参考模块中已有的类似实现：
- {参考实现1名称}：{参考实现路径}
- {参考实现2名称}：{参考实现路径}

## 分析步骤

请按以下步骤分析扩展需求：

### 步骤 1：分析扩展类型
确定本次扩展属于哪种类型：
- [ ] 渠道/平台扩展：需要创建新的 Client 实现类
- [ ] 策略扩展：需要实现策略接口
- [ ] 业务实体扩展：需要创建完整的 DO/Mapper/Service/Controller

### 步骤 2：识别需要创建/修改的文件
根据扩展类型，列出需要创建的文件清单：

**渠道/平台扩展**：
| 序号 | 文件类型 | 文件路径 | 说明 |
|-----|---------|---------|------|
| 1 | 枚举类 | enums/XxxEnum.java | 添加新渠道编码 |
| 2 | 配置类 | framework/.../XxxConfig.java | 定义配置字段 |
| 3 | 客户端类 | framework/.../XxxClient.java | 实现核心逻辑 |
| 4 | 工厂注册 | ...FactoryImpl.java | 注册到工厂 |
| 5 | 单元测试 | test/.../XxxClientTest.java | 验证功能 |

**策略扩展**：
| 序号 | 文件类型 | 文件路径 | 说明 |
|-----|---------|---------|------|
| 1 | 枚举类 | enums/XxxStrategyEnum.java | 添加策略类型 |
| 2 | 策略实现 | .../XxxStrategyImpl.java | 实现策略接口 |
| 3 | 单元测试 | test/.../XxxStrategyTest.java | 验证功能 |

**业务实体扩展**：
| 序号 | 文件类型 | 文件路径 | 说明 |
|-----|---------|---------|------|
| 1 | DO 实体 | dal/dataobject/XxxDO.java | 数据实体 |
| 2 | Mapper | dal/mysql/XxxMapper.java | 数据访问 |
| 3 | Service 接口 | service/XxxService.java | 业务接口 |
| 4 | Service 实现 | service/XxxServiceImpl.java | 业务实现 |
| 5 | Controller | controller/XxxController.java | HTTP 接口 |
| 6 | VO 类 | controller/.../vo/*.java | 请求/响应对象 |
| 7 | 错误码 | enums/ErrorCodeConstants.java | 错误码定义 |
| 8 | SQL 脚本 | sql/module/xxx.sql | 建表语句 |

### 步骤 3：设计实现细节
针对每个需要创建的文件，说明：
- 类的继承关系
- 需要实现的方法
- 关键业务逻辑
- 需要注意的规范

### 步骤 4：验证扩展完整性
确保扩展符合以下检查项：
- [ ] 代码风格符合项目规范（注解、命名、注释）
- [ ] 错误处理完整，使用项目错误码
- [ ] 事务处理正确（@Transactional 使用）
- [ ] 权限控制配置（@PreAuthorize）
- [ ] 单元测试覆盖核心逻辑

## 输出要求

### 输出格式
请按以下格式输出扩展实现：

#### 1. 文件清单
列出所有需要创建/修改的文件及其作用。

#### 2. 实现代码
为每个文件提供完整代码，格式如下：

```java
// 文件：{相对路径}
// 说明：{文件作用说明}

package {完整包名};

// imports...

/**
 * {类说明}
 *
 * @author {作者}
 */
{类定义}
```

#### 3. 配置变更
说明需要修改的配置文件（如 pom.xml、application.yml）。

#### 4. 数据库变更
如果需要新建表，提供建表 SQL。

#### 5. 测试用例
提供核心功能的单元测试代码。

#### 6. 使用示例
提供扩展功能的使用示例代码。
```

---

## 三、实际示例

### 示例 1：新增支付渠道（银联支付）

**提示词输入：**

```markdown
## 角色

你是一位资深的 Java 架构师，精通 Spring Boot、MyBatis-Plus、设计模式，熟悉 yudao-vue-pro 项目架构。

## 上下文

### 目标模块
- 模块名称：pay
- 模块路径：yudao-module-pay
- Skill 文档：skills/modules/pay/skill-pay.yaml

### 扩展需求
- 扩展类型：渠道扩展
- 具体需求：新增银联支付渠道，支持扫码支付和手机支付两种方式

### 参考实现
请参考模块中已有的类似实现：
- 微信支付实现：framework/pay/core/client/impl/weixin/AbstractWxPayClient.java
- 支付宝支付实现：framework/pay/core/client/impl/alipay/AbstractAlipayPayClient.java

## 分析步骤

请按照扩展模块提示词模板的分析步骤进行分析。

## 输出要求

请提供完整的银联支付渠道扩展实现。
```

**预期输出关键内容：**

#### 1. 文件清单

| 序号 | 文件类型 | 文件路径 | 说明 |
|-----|---------|---------|------|
| 1 | 枚举修改 | enums/PayChannelEnum.java | 添加银联支付渠道编码 |
| 2 | 配置类 | framework/pay/core/client/impl/unionpay/UnionPayClientConfig.java | 银联支付配置 |
| 3 | 抽象客户端 | framework/pay/core/client/impl/unionpay/AbstractUnionPayClient.java | 银联公共逻辑 |
| 4 | 扫码客户端 | framework/pay/core/client/impl/unionpay/UnionPayQrPayClient.java | 扫码支付实现 |
| 5 | 手机客户端 | framework/pay/core/client/impl/unionpay/UnionPayAppPayClient.java | 手机支付实现 |
| 6 | 工厂修改 | framework/pay/core/client/impl/PayClientFactoryImpl.java | 注册客户端 |
| 7 | 单元测试 | test/.../UnionPayClientTest.java | 测试用例 |

#### 2. 核心代码示例

```java
// 文件：framework/pay/core/client/impl/unionpay/UnionPayClientConfig.java
// 说明：银联支付配置类

package cn.iocoder.yudao.module.pay.framework.pay.core.client.impl.unionpay;

import cn.iocoder.yudao.module.pay.framework.pay.core.client.PayClientConfig;
import lombok.Data;

import javax.validation.constraints.NotBlank;

/**
 * 银联支付客户端配置
 *
 * @author 芋道源码
 */
@Data
public class UnionPayClientConfig implements PayClientConfig {

    /**
     * 商户号
     */
    @NotBlank(message = "商户号不能为空")
    private String merchantId;

    /**
     * API 密钥
     */
    @NotBlank(message = "API密钥不能为空")
    private String apiKey;

    /**
     * 证书路径
     */
    private String certPath;

    /**
     * 证书密码
     */
    private String certPassword;

    /**
     * 是否沙箱环境
     */
    private Boolean sandbox = false;
}
```

```java
// 文件：framework/pay/core/client/impl/unionpay/AbstractUnionPayClient.java
// 说明：银联支付抽象客户端，实现公共逻辑

package cn.iocoder.yudao.module.pay.framework.pay.core.client.impl.unionpay;

import cn.iocoder.yudao.module.pay.framework.pay.core.client.impl.AbstractPayClient;
import lombok.extern.slf4j.Slf4j;

/**
 * 银联支付抽象客户端
 *
 * 实现银联支付的公共逻辑：
 * 1. 签名验签
 * 2. 证书加载
 * 3. 请求构建
 *
 * @author 芋道源码
 */
@Slf4j
public abstract class AbstractUnionPayClient extends AbstractPayClient<UnionPayClientConfig> {

    public AbstractUnionPayClient(Long channelId, String channelCode, UnionPayClientConfig config) {
        super(channelId, channelCode, config);
    }

    @Override
    protected void doInit() {
        // 1. 加载证书
        loadCertificate();
        // 2. 初始化签名器
        initSigner();
    }

    /**
     * 加载银联证书
     */
    private void loadCertificate() {
        // 证书加载逻辑
    }

    /**
     * 初始化签名器
     */
    private void initSigner() {
        // 签名器初始化逻辑
    }

    /**
     * 构建银联请求参数
     */
    protected String buildRequestBody(Object params) {
        // 请求参数构建逻辑
        return null;
    }

    /**
     * 验证银联回调签名
     */
    protected boolean verifySign(String data, String sign) {
        // 验签逻辑
        return true;
    }
}
```

```java
// 文件：framework/pay/core/client/impl/unionpay/UnionPayQrPayClient.java
// 说明：银联扫码支付客户端

package cn.iocoder.yudao.module.pay.framework.pay.core.client.impl.unionpay;

import cn.iocoder.yudao.module.pay.enums.PayChannelEnum;
import cn.iocoder.yudao.module.pay.framework.pay.core.client.dto.order.PayOrderUnifiedReqDTO;
import cn.iocoder.yudao.module.pay.framework.pay.core.client.dto.order.PayOrderRespDTO;
import lombok.extern.slf4j.Slf4j;

/**
 * 银联扫码支付客户端
 *
 * 实现银联二维码支付功能：
 * 1. 主扫支付（商户二维码）
 * 2. 被扫支付（用户扫码）
 *
 * @author 芋道源码
 */
@Slf4j
public class UnionPayQrPayClient extends AbstractUnionPayClient {

    public UnionPayQrPayClient(Long channelId, UnionPayClientConfig config) {
        super(channelId, PayChannelEnum.UNION_PAY_QR.getCode(), config);
    }

    @Override
    protected PayOrderRespDTO doUnifiedOrder(PayOrderUnifiedReqDTO reqDTO) {
        // 1. 构建银联下单请求
        // 2. 调用银联 API
        // 3. 解析响应，返回二维码链接
        return PayOrderRespDTO.builder()
                .channelOrderNo("union_order_no")
                .qrCode("https://qr.unionpay.com/xxx")
                .build();
    }

    @Override
    protected PayOrderRespDTO doParseOrderNotify(String params) {
        // 解析银联支付回调
        return null;
    }

    // 实现其他抽象方法...
}
```

#### 3. 枚举注册

```java
// 在 PayChannelEnum.java 中添加
UNION_PAY_QR("union_pay_qr", "银联扫码支付"),
UNION_PAY_APP("union_pay_app", "银联手机支付");
```

#### 4. 工厂注册

```java
// 在 PayClientFactoryImpl 构造函数中添加
clientClass.put(UNION_PAY_QR, UnionPayQrPayClient.class);
clientClass.put(UNION_PAY_APP, UnionPayAppPayClient.class);
```

---

### 示例 2：新增 AI 平台（Claude）

**提示词输入：**

```markdown
## 角色

你是一位资深的 Java 架构师，精通 Spring Boot、Spring AI、设计模式，熟悉 yudao-vue-pro 项目架构。

## 上下文

### 目标模块
- 模块名称：ai
- 模块路径：yudao-module-ai
- Skill 文档：skills/modules/ai/skill-ai.yaml

### 扩展需求
- 扩展类型：平台扩展
- 具体需求：新增 Claude（Anthropic）AI 平台支持，需要支持对话模型和向量模型

### 参考实现
请参考模块中已有的类似实现：
- OpenAI 实现：framework/ai/core/model/AiModelFactoryImpl.java 中的 OpenAI 部分
- 智谱 AI 实现：framework/ai/core/model/AiModelFactoryImpl.java 中的 ZhiPu 部分

## 分析步骤

请按照扩展模块提示词模板的分析步骤进行分析。

## 输出要求

请提供完整的 Claude AI 平台扩展实现。
```

**预期输出关键内容：**

#### 1. 文件清单

| 序号 | 文件类型 | 文件路径 | 说明 |
|-----|---------|---------|------|
| 1 | 枚举修改 | enums/model/AiPlatformEnum.java | 添加 CLAUDE 平台 |
| 2 | 工厂修改 | framework/ai/core/model/AiModelFactoryImpl.java | 添加 Claude 模型创建方法 |
| 3 | 配置属性 | framework/ai/config/YudaoAiProperties.java | 添加 Claude 配置 |
| 4 | 自动配置 | framework/ai/config/AiAutoConfiguration.java | 添加 Claude Bean |

#### 2. 核心代码示例

```java
// 文件：enums/model/AiPlatformEnum.java（修改）
// 说明：在枚举中添加 Claude 平台

// 在枚举中添加：
CLAUDE("Claude", "Anthropic Claude"),

// 枚举完整结构：
public enum AiPlatformEnum {

    OPEN_AI("OpenAI", "OpenAI"),
    AZURE_OPEN_AI("AzureOpenAI", "Azure OpenAI"),
    OLLAMA("Ollama", "Ollama"),
    ZHI_PU("ZhiPu", "智谱 AI"),
    DEEP_SEEK("DeepSeek", "DeepSeek"),
    CLAUDE("Claude", "Anthropic Claude"),  // 新增
    ;

    // ...
}
```

```java
// 文件：framework/ai/core/model/AiModelFactoryImpl.java（修改）
// 说明：添加 Claude 模型创建方法

// 在 getOrCreateChatModel 方法的 switch 中添加：
case CLAUDE:
    return buildClaudeChatModel(apiKey, url);

// 新增方法：
/**
 * 构建 Claude ChatModel
 *
 * @param apiKey API 密钥
 * @param url API 地址（可选，使用默认地址）
 * @return ChatModel 实例
 */
private static ChatModel buildClaudeChatModel(String apiKey, String url) {
    AnthropicApi anthropicApi = new AnthropicApi(
            StringUtils.hasText(url) ? url : "https://api.anthropic.com",
            apiKey
    );
    return AnthropicChatModel.builder()
            .anthropicApi(anthropicApi)
            .toolCallingManager(getToolCallingManager())
            .build();
}

/**
 * 构建 Claude EmbeddingModel
 */
private static EmbeddingModel buildClaudeEmbeddingModel(String apiKey, String url) {
    // Claude 使用 Voyage AI 进行向量化
    // 如果需要，可以集成 VoyageEmbeddingModel
    return null;
}
```

```java
// 文件：framework/ai/config/YudaoAiProperties.java（修改）
// 说明：添加 Claude 配置属性

@Data
public class YudaoAiProperties {

    // 已有属性...

    /**
     * Claude 配置
     */
    private Claude claude = new Claude();

    @Data
    public static class Claude {
        /**
         * API 密钥
         */
        private String apiKey;

        /**
         * API 地址（可选）
         */
        private String baseUrl;

        /**
         * 默认模型
         */
        private String defaultModel = "claude-3-opus-20240229";
    }
}
```

```java
// 文件：framework/ai/config/AiAutoConfiguration.java（修改）
// 说明：添加 Claude 自动配置

@Configuration
public class AiAutoConfiguration {

    @Bean
    @ConditionalOnProperty(prefix = "yudao.ai.claude", name = "api-key")
    public ChatModel claudeChatModel(YudaoAiProperties properties) {
        YudaoAiProperties.Claude claude = properties.getClaude();
        return buildClaudeChatModel(claude.getApiKey(), claude.getBaseUrl());
    }
}
```

#### 3. 使用示例

```java
// 在数据库中配置 Claude 模型
// 1. 在 ai_api_key 表中添加 Claude API Key
INSERT INTO ai_api_key (name, api_key, platform, status)
VALUES ('Claude API Key', 'sk-ant-xxx', 'Claude', 0);

// 2. 在 ai_model 表中添加模型配置
INSERT INTO ai_model (key_id, name, model, platform, type, status)
VALUES (1, 'Claude 3 Opus', 'claude-3-opus-20240229', 'Claude', 1, 0);

// 3. 使用代码调用
@Resource
private AiModelService modelService;

public void chat() {
    ChatModel chatModel = modelService.getChatModel(modelId);
    ChatResponse response = chatModel.call(new Prompt("你好"));
}
```

---

### 示例 3：新增文件存储（阿里云 OSS）

**提示词输入：**

```markdown
## 角色

你是一位资深的 Java 架构师，精通 Spring Boot、云存储、设计模式，熟悉 yudao-vue-pro 项目架构。

## 上下文

### 目标模块
- 模块名称：infra
- 模块路径：yudao-module-infra
- Skill 文档：skills/modules/infra/skill-infra.yaml

### 扩展需求
- 扩展类型：渠道扩展
- 具体需求：新增阿里云 OSS 文件存储支持

### 参考实现
请参考模块中已有的类似实现：
- S3 存储：framework/file/core/client/S3FileClient.java
- 本地存储：framework/file/core/client/LocalFileClient.java

## 分析步骤

请按照扩展模块提示词模板的分析步骤进行分析。

## 输出要求

请提供完整的阿里云 OSS 文件存储扩展实现。
```

**预期输出关键内容：**

#### 1. 文件清单

| 序号 | 文件类型 | 文件路径 | 说明 |
|-----|---------|---------|------|
| 1 | 配置类 | framework/file/core/client/AliyunOssFileClientConfig.java | OSS 配置 |
| 2 | 客户端类 | framework/file/core/client/AliyunOssFileClient.java | OSS 客户端 |
| 3 | 枚举修改 | framework/file/core/enums/FileStorageEnum.java | 添加存储类型 |

#### 2. 核心代码示例

```java
// 文件：framework/file/core/client/AliyunOssFileClientConfig.java
// 说明：阿里云 OSS 配置类

package cn.iocoder.yudao.module.infra.framework.file.core.client;

import lombok.Data;
import javax.validation.constraints.NotBlank;

/**
 * 阿里云 OSS 文件客户端配置
 *
 * @author 芋道源码
 */
@Data
public class AliyunOssFileClientConfig implements FileClientConfig {

    /**
     * Endpoint，如 oss-cn-hangzhou.aliyuncs.com
     */
    @NotBlank(message = "Endpoint 不能为空")
    private String endpoint;

    /**
     * Access Key ID
     */
    @NotBlank(message = "Access Key ID 不能为空")
    private String accessKeyId;

    /**
     * Access Key Secret
     */
    @NotBlank(message = "Access Key Secret 不能为空")
    private String accessKeySecret;

    /**
     * Bucket 名称
     */
    @NotBlank(message = "Bucket 不能为空")
    private String bucketName;

    /**
     * 自定义域名（可选）
     */
    private String domain;

    /**
     * 存储路径前缀
     */
    private String basePath = "";
}
```

```java
// 文件：framework/file/core/client/AliyunOssFileClient.java
// 说明：阿里云 OSS 文件客户端实现

package cn.iocoder.yudao.module.infra.framework.file.core.client;

import cn.hutool.core.util.StrUtil;
import com.aliyun.oss.OSS;
import com.aliyun.oss.OSSClientBuilder;
import com.aliyun.oss.model.OSSObject;
import com.aliyun.oss.model.PutObjectRequest;
import lombok.extern.slf4j.Slf4j;

import java.io.ByteArrayInputStream;

/**
 * 阿里云 OSS 文件客户端
 *
 * @author 芋道源码
 */
@Slf4j
public class AliyunOssFileClient extends AbstractFileClient<AliyunOssFileClientConfig> {

    private OSS ossClient;

    public AliyunOssFileClient(Long id, AliyunOssFileClientConfig config) {
        super(id, config);
    }

    @Override
    protected void doInit() {
        // 创建 OSS 客户端
        this.ossClient = new OSSClientBuilder().build(
                getConfig().getEndpoint(),
                getConfig().getAccessKeyId(),
                getConfig().getAccessKeySecret()
        );
    }

    @Override
    public String upload(byte[] content, String path, String type) {
        // 1. 构建完整路径
        String fullPath = buildFullPath(path);

        // 2. 上传文件
        PutObjectRequest request = new PutObjectRequest(
                getConfig().getBucketName(),
                fullPath,
                new ByteArrayInputStream(content)
        );
        request.setMetadata(buildMetadata(type));
        ossClient.putObject(request);

        // 3. 返回访问 URL
        return buildUrl(fullPath);
    }

    @Override
    public void delete(String path) {
        String fullPath = buildFullPath(path);
        ossClient.deleteObject(getConfig().getBucketName(), fullPath);
    }

    @Override
    public byte[] getContent(String path) {
        String fullPath = buildFullPath(path);
        OSSObject object = ossClient.getObject(getConfig().getBucketName(), fullPath);
        try {
            return IoUtil.readBytes(object.getObjectContent());
        } finally {
            IoUtil.close(object);
        }
    }

    @Override
    public String presignGetUrl(String path, int expireSeconds) {
        String fullPath = buildFullPath(path);
        return ossClient.generatePresignedUrl(
                getConfig().getBucketName(),
                fullPath,
                DateUtil.offsetSecond(new Date(), expireSeconds)
        ).toString();
    }

    /**
     * 构建完整路径
     */
    private String buildFullPath(String path) {
        String basePath = getConfig().getBasePath();
        return StrUtil.isNotBlank(basePath) ? basePath + "/" + path : path;
    }

    /**
     * 构建访问 URL
     */
    private String buildUrl(String path) {
        String domain = getConfig().getDomain();
        if (StrUtil.isNotBlank(domain)) {
            return domain + "/" + path;
        }
        return String.format("https://%s.%s/%s",
                getConfig().getBucketName(),
                getConfig().getEndpoint(),
                path);
    }
}
```

#### 3. 枚举注册

```java
// 文件：framework/file/core/enums/FileStorageEnum.java（修改）
// 说明：添加阿里云 OSS 存储类型

public enum FileStorageEnum {

    LOCAL(1, LocalFileClientConfig.class, LocalFileClient.class),
    DB(2, DbFileClientConfig.class, DbFileClient.class),
    S3(10, S3FileClientConfig.class, S3FileClient.class),
    SFTP(11, SftpFileClientConfig.class, SftpFileClient.class),
    FTP(12, FtpFileClientConfig.class, FtpFileClient.class),
    ALIYUN_OSS(20, AliyunOssFileClientConfig.class, AliyunOssFileClient.class), // 新增
    ;

    // ...
}
```

#### 4. 依赖添加

```xml
<!-- 在 yudao-module-infra/pom.xml 中添加 -->
<dependency>
    <groupId>com.aliyun.oss</groupId>
    <artifactId>aliyun-sdk-oss</artifactId>
    <version>3.17.1</version>
</dependency>
```

---

## 四、关键参数说明

### 扩展类型参数

| 参数名 | 可选值 | 说明 |
|-------|-------|------|
| 扩展类型 | `渠道扩展` | 新增外部服务接入，如支付渠道、存储类型 |
| | `策略扩展` | 新增策略实现，如审批人策略 |
| | `业务实体扩展` | 新增完整业务功能，需要 DO/Mapper/Service/Controller |

### 模块路径参数

| 模块 | 路径 | Skill 文档 |
|-----|------|-----------|
| pay | yudao-module-pay | skills/modules/pay/skill-pay.yaml |
| ai | yudao-module-ai | skills/modules/ai/skill-ai.yaml |
| infra | yudao-module-infra | skills/modules/infra/skill-infra.yaml |
| bpm | yudao-module-bpm | skills/modules/bpm/skill-bpm.yaml |
| system | yudao-module-system | skills/modules/system/skill-system.yaml |
| member | yudao-module-member | skills/modules/member/skill-member.yaml |
| mall | yudao-module-product | skills/modules/mall/skill-mall.yaml |
| crm | yudao-module-crm | skills/modules/crm/skill-crm.yaml |
| erp | yudao-module-erp | skills/modules/erp/skill-erp.yaml |
| mp | yudao-module-mp | skills/modules/mp/skill-mp.yaml |
| iot | yudao-module-iot | skills/modules/iot/skill-iot.yaml |
| report | yudao-module-report | skills/modules/report/skill-report.yaml |

### 命名规范参数

| 类型 | 命名规范 | 示例 |
|-----|---------|------|
| 枚举类 | XxxEnum | PayChannelEnum |
| 配置类 | XxxConfig/XxxClientConfig | UnionPayClientConfig |
| 客户端类 | XxxClient | UnionPayQrPayClient |
| 抽象类 | AbstractXxx | AbstractUnionPayClient |
| DO 实体 | XxxDO | PayOrderDO |
| Mapper | XxxMapper | PayOrderMapper |
| Service 接口 | XxxService | PayOrderService |
| Service 实现 | XxxServiceImpl | PayOrderServiceImpl |
| Controller | XxxController | PayOrderController |
| VO 请求 | XxxReqVO | PayOrderCreateReqVO |
| VO 响应 | XxxRespVO | PayOrderSubmitRespVO |

### 注解规范

| 层级 | 必备注解 |
|-----|---------|
| Controller | `@RestController`, `@RequestMapping`, `@Validated`, `@Tag` |
| Service | `@Service`, `@Validated` |
| ServiceImpl | `@Service`, `@Validated`, `@Slf4j` |
| Mapper | `@Mapper` |
| DO | `@TableName`, `@Data`, `@Builder` |

---

## 五、最佳实践

### 1. 渠道/平台扩展最佳实践

```markdown
**遵循策略模式 + 工厂模式**

1. **抽象公共逻辑**
   - 如果有多种实现方式（如扫码、APP、H5），创建抽象类封装公共逻辑
   - 参考：AbstractWxPayClient、AbstractAlipayPayClient

2. **配置类设计**
   - 使用 JSR-303 注解校验必填字段
   - 敏感信息考虑加密存储
   - 支持沙箱环境配置

3. **客户端实现**
   - 继承 AbstractXxxClient，实现 doInit() 和业务方法
   - 使用 try-catch 处理异常，记录日志
   - 回调处理必须验证签名

4. **工厂注册**
   - 在工厂构造函数或静态块中注册
   - 使用反射创建实例，支持配置热刷新

5. **测试覆盖**
   - 测试正常流程
   - 测试异常情况
   - 测试签名验证
```

### 2. 策略扩展最佳实践

```markdown
**遵循策略模式**

1. **枚举定义**
   - 在策略枚举中添加新类型
   - 每个策略有唯一标识和描述

2. **策略实现**
   - 实现策略接口的所有方法
   - validateParam() 校验参数合法性
   - calculateUsers() 等业务方法返回正确结果

3. **Spring 注册**
   - 使用 @Component 注解，Spring 自动注入
   - 策略工厂通过 Map<String, Strategy> 自动收集

4. **参考实现**
   - BPM 审批人策略：BpmTaskCandidateRoleStrategy
```

### 3. 业务实体扩展最佳实践

```markdown
**遵循分层架构**

1. **DO 实体设计**
   - 继承 BaseDO 获得通用字段
   - 使用 @TableName 指定表名
   - 使用 @TableId 指定主键

2. **Mapper 设计**
   - 继承 BaseMapperX 获得通用 CRUD
   - 使用 LambdaQueryWrapper 构建查询
   - 分页返回 PageResult<XxxDO>

3. **Service 设计**
   - 接口定义业务方法
   - 实现类使用 @Transactional 控制事务
   - 使用 exception(ERROR_CODE) 抛出业务异常

4. **Controller 设计**
   - 使用 @PreAuthorize 控制权限
   - 使用 @Validated 校验参数
   - 返回 CommonResult<Xxx> 统一格式

5. **错误码管理**
   - 在 ErrorCodeConstants 中定义
   - 格式：1-XXX-YYY-ZZZ（模块-子模块-功能-具体错误）

6. **SQL 脚本**
   - 包含建表语句
   - 包含初始数据（如需要）
   - 字段添加注释
```

### 4. 通用最佳实践

```markdown
1. **代码风格一致**
   - 参考 Alibaba Java 编码规范
   - 使用项目统一的格式化配置

2. **异常处理**
   - 使用项目错误码体系
   - 记录完整错误日志
   - 用户友好的错误提示

3. **事务管理**
   - 写操作使用 @Transactional
   - 注意事务传播行为
   - 避免大事务

4. **性能优化**
   - 合理使用缓存
   - 避免循环查询数据库
   - 使用批量操作

5. **安全考虑**
   - 敏感信息加密
   - 权限校验
   - SQL 注入防护

6. **文档完善**
   - 类和方法添加 JavaDoc
   - 复杂逻辑添加注释
   - 更新 README 或使用文档
```

---

## 六、常见问题

### Q1: 扩展后如何测试？

```markdown
1. **单元测试**
   - 创建 test 类，使用 @SpringBootTest
   - Mock 外部依赖（如第三方 SDK）
   - 测试核心业务逻辑

2. **集成测试**
   - 使用测试配置连接测试环境
   - 验证完整流程

3. **手工测试**
   - 启动项目，通过 Postman 测试接口
   - 检查数据库记录
```

### Q2: 如何处理第三方 SDK 依赖？

```markdown
1. 在模块 pom.xml 中添加依赖
2. 检查依赖冲突，使用 exclusion 排除
3. 将 SDK 初始化逻辑放在 Client 的 doInit() 方法中
4. 使用 try-with-resources 或手动关闭资源
```

### Q3: 扩展功能如何配置？

```markdown
1. **数据库配置**
   - 在管理后台添加配置记录
   - 配置 JSON 字段存储客户端配置

2. **配置文件配置**
   - 在 application.yml 中添加
   - 使用 @ConfigurationProperties 绑定

3. **动态配置**
   - 支持管理后台修改
   - 使用缓存 + 刷新机制
```

---

## 七、文档版本

| 版本 | 日期 | 说明 |
|-----|------|------|
| 1.0.0 | 2026-03-18 | 初始版本，基于 pay/ai/infra/bpm 四个模块提炼 |

---

**相关文档：**
- [Skill 文档索引](../index.yaml)
- [模块 Skill 文档](../modules/)
- [代码模式文档](../patterns/)