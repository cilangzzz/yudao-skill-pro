# 音乐生成 API

> Controller: `AiMusicController`
> 路径前缀：`/ai/music`

## 业务概述

音乐生成基于 Suno AI 实现音乐创作，支持歌词生成、风格标签、异步任务模式。

## Controller 接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 生成音乐 | POST | `/ai/music/generate` | 提交音乐生成任务 |
| 创建 | POST | `/ai/music/create` | 创建音乐记录 |
| 更新 | PUT | `/ai/music/update` | 更新音乐记录 |
| 删除 | DELETE | `/ai/music/delete` | 删除音乐记录 |
| 获取详情 | GET | `/ai/music/get` | 获取音乐详情 |
| 分页查询 | GET | `/ai/music/page` | 分页查询音乐列表 |

## Service 接口

### AiMusicService

```java
public interface AiMusicService {
    // 音乐生成与 CRUD
}
```

## 数据表

### ai_music

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 编号 |
| user_id | Long | 用户编号 |
| title | String | 音乐名称 |
| lyric | String | 歌词 |
| image_url | String | 图片地址 |
| audio_url | String | 音频地址 |
| video_url | String | 视频地址 |
| status | Integer | 音乐状态 |
| generate_mode | Integer | 生成模式 |
| description | String | 描述词 |
| platform | String | 平台 |
| model | String | 模型 |
| tags | List<String> | 音乐风格标签 |
| duration | Double | 音乐时长 |
| public_status | Boolean | 是否公开 |
| task_id | String | 任务编号 |
| error_message | String | 错误信息 |
