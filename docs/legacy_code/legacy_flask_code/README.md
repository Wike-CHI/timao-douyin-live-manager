# 遗留Flask代码存档

本文件夹包含项目中原有的Flask应用代码，这些代码已不再被前后端调用，仅作为历史记录保存。

## 架构迁移说明

项目已从Flask架构迁移到FastAPI架构：

- **旧架构**: Flask (端口5001/10090) + Electron
- **新架构**: FastAPI (端口10090) + Electron

### 主要Flask应用文件

- `app.py` - 原Flask主应用，包含所有API路由和业务逻辑
- `websocket_handler.py` - WebSocket处理模块，用于实时通信
- `test_server.py` - AST模块的Flask测试服务器

### 启动脚本

- `auto_launch_service.py` - 自动启动Flask服务器脚本
- `launch_voice_transcription.py` - 语音转录Flask启动脚本

### 依赖文件

- `requirements_flask.txt` - Flask相关依赖包

## 原Flask应用功能

Flask应用提供了以下API接口：

- `/api/health` - 健康检查
- `/api/comments` - 评论数据获取
- `/api/stream/comments` - 评论流SSE
- `/api/hotwords` - 热词分析
- `/api/tips/latest` - 最新AI话术
- `/api/tips/<tip_id>/used` - 标记话术已使用
- `/api/config` - 配置管理

## 迁移完成状态

✅ **已完成的迁移任务**:

- Flask主应用代码已移动到 `docs/legacy_flask_code/`
- Electron主进程已更新，不再启动Flask服务
- requirements.txt中Flask依赖已注释
- 前后端已切换到FastAPI架构
- 所有API功能已在FastAPI中重新实现

⚠️ **注意事项**:

- 此文件夹中的代码仅供参考，不再维护
- 项目现在完全基于FastAPI架构运行
- 如需查看当前API实现，请参考 `server/app/` 目录

Flask代码于 2025年10月28 迁移到此存档文件夹，项目正式切换到FastAPI架构。
