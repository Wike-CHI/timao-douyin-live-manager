# 本地化模式启动指南

## 概述

本文档说明如何启动和使用本地化版本的抖音直播管理系统。

---

## 系统要求

### 软件依赖
- **Python**: 3.10 或以上
- **Node.js**: 16.x 或以上
- **FFmpeg**: 已安装并配置环境变量（系统会自动检测）

### 系统配置
- **内存**: 建议 8GB 以上（SenseVoice模型需要约2-3GB）
- **磁盘空间**: 建议 10GB 以上（包含AI模型）

---

## 快速启动

### 1. 安装Python依赖

```bash
cd D:\gsxm\timao-douyin-live-manager
pip install -r requirements.txt
```

**注意**：本地化版本已移除以下依赖：
- ~~pymysql~~ (已移除MySQL依赖)
- ~~redis~~ (已移除Redis依赖)
- ~~sqlalchemy~~ (已移除ORM依赖)

### 2. 启动后端服务

```bash
# Windows
python -m uvicorn server.app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用run_server.bat（如果存在）
run_server.bat
```

后端服务将在 `http://localhost:8000` 启动。

### 3. 启动前端应用

```bash
cd electron
npm install  # 首次运行需要安装依赖
npm run dev  # 开发模式
# 或
npm run build  # 构建生产版本
```

---

## 初次配置

### 自动启动向导

首次启动应用时，系统会自动检测配置状态：
- 如果未配置AI服务，会自动跳转到 **配置向导页面**
- 按照向导步骤完成配置即可

### 配置步骤

#### 步骤1：选择AI服务商

从以下服务商中选择一个或多个：
- **通义千问** (qwen)
- **讯飞星火** (xunfei)
- **DeepSeek** (deepseek)
- **智谱AI** (zhipu)
- **百度文心** (baidu)
- **Gemini** (gemini)

#### 步骤2：配置API Key

为每个选择的服务商填写：
- **API Key** (必填)
- **Base URL** (可选，默认使用官方地址)
- **默认模型** (可选，选择该服务商的默认模型)

**示例：通义千问**
```
API Key: sk-xxxxxxxxxxxxxxxxxxxxx
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1 (默认)
默认模型: qwen-plus
```

#### 步骤3：配置功能模型

为每个AI功能选择合适的模型：
- **直播总结** (live_summary)
- **弹幕分析** (danmaku_analysis)
- **话题推荐** (topic_suggestion)
- **内容生成** (content_generation)

**提示**：
- 可以为不同功能使用不同服务商的模型
- 建议先配置至少一个功能，其他功能可以后续添加

#### 步骤4：完成配置

点击"完成配置"后，系统会：
1. 保存配置到本地文件 (`data/ai_config.json`)
2. 初始化AI网关
3. 跳转到主界面

---

## 配置文件说明

### 数据目录结构

```
data/
├── config.json           # 应用全局配置
├── ai_config.json        # AI服务配置
├── ai_usage.json         # AI使用统计
└── sessions/             # 会话数据目录
    ├── 123.json          # 会话123的数据
    ├── 124.json
    └── ...
```

### AI配置格式 (`ai_config.json`)

```json
{
  "providers": {
    "qwen": {
      "provider_id": "qwen",
      "name": "通义千问",
      "api_key": "sk-xxxxxxxxxxxxx",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "default_model": "qwen-plus",
      "enabled": true,
      "models": ["qwen-plus", "qwen-turbo", "qwen-max"]
    }
  },
  "function_models": {
    "live_summary": {
      "provider": "qwen",
      "model": "qwen-plus"
    },
    "danmaku_analysis": {
      "provider": "qwen",
      "model": "qwen-turbo"
    }
  },
  "initialized": true,
  "last_updated": "2025-01-01T00:00:00Z"
}
```

---

## 常见问题

### Q1: 首次启动时提示"生成失败，请稍后重试"

**原因**：AI服务配置未完成或API Key无效。

**解决方案**：
1. 检查 `data/ai_config.json` 文件是否存在
2. 验证API Key是否有效
3. 检查网络连接是否正常
4. 访问 `AI网关` 页面重新配置

### Q2: SenseVoice模型下载失败

**原因**：网络问题或ModelScope访问受限。

**解决方案**：
1. 检查网络连接
2. 使用VPN或镜像源
3. 手动下载模型到 `server/modules/models/.cache/`

### Q3: FFmpeg未找到

**原因**：FFmpeg未安装或未配置环境变量。

**解决方案**：
1. 下载FFmpeg: https://ffmpeg.org/download.html
2. 解压到任意目录（如 `C:\Program Files\ffmpeg`）
3. 添加到系统PATH环境变量
4. 重启应用

### Q4: 如何修改AI配置？

**方法1：通过UI界面**
- 访问 `AI网关` 页面
- 修改服务商配置或功能模型映射

**方法2：直接编辑配置文件**
- 打开 `data/ai_config.json`
- 修改相应配置
- 重启后端服务

### Q5: 数据存储在哪里？

**本地化模式**：
- 所有数据存储在 `data/` 目录
- 包括配置、会话、AI使用统计
- **无需数据库**，纯JSON文件存储

### Q6: 如何备份数据？

**简单备份**：
```bash
# 复制整个data目录
cp -r data/ data_backup/
```

**恢复数据**：
```bash
# 替换data目录
cp -r data_backup/ data/
```

---

## 高级配置

### 手动配置AI服务商

如果不想使用向导，可以手动创建配置文件：

```bash
cd data
```

创建 `ai_config.json`：
```json
{
  "providers": {
    "qwen": {
      "provider_id": "qwen",
      "name": "通义千问",
      "api_key": "你的API Key",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "default_model": "qwen-plus",
      "enabled": true
    }
  },
  "function_models": {
    "live_summary": {
      "provider": "qwen",
      "model": "qwen-plus"
    }
  },
  "initialized": true
}
```

### 自定义服务商

如果要添加自定义OpenAI兼容服务商：

```json
{
  "providers": {
    "custom": {
      "provider_id": "custom",
      "name": "自定义服务商",
      "api_key": "你的API Key",
      "base_url": "https://your-api-endpoint.com/v1",
      "default_model": "custom-model",
      "enabled": true,
      "models": ["custom-model-1", "custom-model-2"]
    }
  }
}
```

---

## 开发者指南

### 测试本地化模式

运行测试脚本：

```bash
python specs/local_mode/test_local_mode.py
```

测试内容包括：
- 本地存储服务
- AI配置管理
- 无数据库依赖
- AI网关本地配置
- 数据目录结构

### 调试模式

启用详细日志：

```bash
# 设置环境变量
export LOG_LEVEL=DEBUG

# 启动后端
python -m uvicorn server.app.main:app --reload --log-level debug
```

### API端点

本地化模式新增的API端点：

```
GET  /api/bootstrap/status              # 检查初始化状态
POST /api/bootstrap/provider            # 配置服务商
POST /api/bootstrap/function-models/batch  # 批量配置功能模型
GET  /api/bootstrap/templates           # 获取服务商模板
```

---

## 技术架构

### 架构变更

**原架构**：
```
Electron → FastAPI → MySQL + Redis
```

**新架构**：
```
Electron → FastAPI → Local JSON Files
```

### 关键变更

1. **移除数据库依赖**
   - 不再需要MySQL
   - 不再需要Redis
   - 所有数据存储在JSON文件

2. **移除认证系统**
   - 无需登录
   - 无需JWT验证
   - 自动使用本地用户（super_admin权限）

3. **移除订阅系统**
   - 无需付费验证
   - 所有功能默认可用

4. **本地AI配置**
   - AI服务配置存储在本地
   - 用户自行管理API Key
   - 支持多服务商

### 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 本地存储 | `server/local/local_storage.py` | JSON文件存储服务 |
| AI配置 | `server/local/local_config.py` | AI服务配置管理 |
| 启动检测 | `server/app/api/bootstrap.py` | 初始化状态检测API |
| 配置向导 | `electron/renderer/src/pages/setup/SetupWizard.tsx` | 首次启动向导 |
| 本地依赖 | `server/app/core/dependencies.py` | 返回固定本地用户 |

---

## 更新日志

### v1.0.0 (2025-01-25)

**本地化改造**：
- ✅ 移除MySQL和Redis依赖
- ✅ 实现本地JSON文件存储
- ✅ 移除用户认证系统
- ✅ 移除订阅验证系统
- ✅ 添加首次启动向导
- ✅ AI配置本地化
- ✅ 移除SenseVoice内存检查
- ✅ 自动检测SenseVoice模型
- ✅ 自动配置FFmpeg

---

## 联系方式

如有问题或建议，请联系：
- **项目负责人**：叶维哲
- **技术支持**：[您的联系方式]

---

**祝使用愉快！** 🎉

