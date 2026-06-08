# 图像生成 API

> Controller: `AiImageController`
> 路径前缀：`/ai/image`

## 业务概述

图像生成支持多种 AI 绘画平台，包括 OpenAI DALL-E、Stable Diffusion、Midjourney、硅基流动等。支持异步任务模式（Midjourney）和同步生成模式。

## Controller 接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 生成图像 | POST | `/ai/image/generate` | 提交图像生成任务 |
| 获取详情 | GET | `/ai/image/get` | 获取图像生成记录详情 |
| 分页查询 | GET | `/ai/image/page` | 分页查询图像列表 |
| 删除 | DELETE | `/ai/image/delete` | 删除图像记录 |

## Service 接口

### AiImageService

```java
public interface AiImageService {
    // 生成图像
    AiImageDO generateImage(AiImageGenerateReqVO reqVO, Long userId);
}
```

### 模型调用

```java
// 获取 ImageModel
ImageModel imageModel = modelService.getImageModel(modelId);

// 生成图片
ImageResponse response = imageModel.call(new ImagePrompt(prompt, options));
```

## 数据表

### ai_image

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| user_id | Long | 用户编号 |
| prompt | String | 提示词 |
| platform | String | 平台 |
| model_id | Long | 模型编号 |
| model | String | 模型标识 |
| width | Integer | 图片宽度 |
| height | Integer | 图片高度 |
| status | Integer | 生成状态 |
| finish_time | LocalDateTime | 完成时间 |
| error_message | String | 错误信息 |
| pic_url | String | 图片地址 |
| public_status | Boolean | 是否公开 |
| options | Map<String,Object> | 绘制参数 |
| buttons | List<Button> | MJ 按钮 |
| task_id | String | 任务编号 |

## 平台差异

| 平台 | 模式 | 说明 |
|------|------|------|
| OpenAI DALL-E | 同步 | 直接返回图片 URL |
| Stable Diffusion | 同步 | 直接返回图片 URL |
| Midjourney | 异步 | 通过 task_id 轮询状态，支持 buttons 操作 |
| 硅基流动 | 同步 | 直接返回图片 URL |
