# 项目结构优化 - 迁移说明

## 概述

为了提高项目结构的清晰度和可维护性，我们将以下三个模块整合到了 `server/modules/` 目录下。

## 已迁移的模块

### 1. AST_module → server/modules/ast

**迁移内容**:
- 音频语音转写功能
- SenseVoice 服务集成
- 音频采集和处理
- ACRCloud 音乐识别

**导入示例**:
```python
# 旧
from AST_module.sensevoice_service import SenseVoiceConfig

# 新
from server.modules.ast.sensevoice_service import SenseVoiceConfig
```

### 2. DouyinLiveWebFetcher → server/modules/douyin

**迁移内容**:
- 抖音直播弹幕抓取
- WebSocket 连接管理
- 协议缓冲区定义
- JavaScript 签名算法

**导入示例**:
```python
# 旧
from DouyinLiveWebFetcher.liveMan import DouyinLiveWebFetcher

# 新
from server.modules.douyin.liveMan import DouyinLiveWebFetcher
```

### 3. StreamCap 后端 → server/modules/streamcap

**迁移内容**:
- 平台处理器（platform_handlers）
- FFmpeg 媒体构建器（ffmpeg_builders）
- 流媒体 URL 解析

**注意**: 只迁移了后端功能，StreamCap 的前端 GUI 仍然保留在 `StreamCap/` 目录。

**导入示例**:
```python
# 旧
from StreamCap.app.core.platforms.platform_handlers import get_platform_handler

# 新
from server.modules.streamcap.platforms import get_platform_handler
```

## 依赖管理

所有依赖已合并到 `server/requirements.txt`，解决了版本冲突并优化了依赖结构。

**安装依赖**:
```bash
pip install -r server/requirements.txt
```

## 打包影响

打包配置已更新，现在只需要打包 `server/` 目录即可包含所有必要模块。

## 向后兼容性

旧的根目录模块（`AST_module/`、`DouyinLiveWebFetcher/`）仍然保留但标记为弃用，用于向后兼容和开发参考。

## 迁移日期

2024-11-01

## 更多信息

- 详细的迁移说明请参考各模块目录下的 `DEPRECATED_README.md`
- 新的项目结构符合 Python 最佳实践
- 所有服务端代码现在集中在 `server/` 目录下

