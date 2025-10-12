# 提猫直播助手 · TalkingCat

> **重要声明：** 本项目仅依照仓库内的《提猫直播助手源代码许可协议（仅供学习研究）》授权，用于学习与研究目的。任何未经作者书面许可的商业化行为（含直接或间接盈利）均被严格禁止，违者作者保留追究法律责任的权利。请务必阅读根目录下的 `LICENSE` 文件。

基于自研直播互动与本地语音识别能力的主播 AI 助手（隐私不出机）

## 技术栈

- **前端**: HTML + CSS + Element UI 2.15
- **后端**: FastAPI + SQLite + Redis
- **直播互动**: 项目内置 DouyinLiveWebFetcher 模块（WebSocket → SSE 桥接）
- **语音识别**: SenseVoice/FunASR 本地模型 (中文)
- **AI分析**: jieba + SnowNLP (本地NLP)
- **部署**: Docker + Nginx

## 项目结构

```
timao-douyin-live-manager/
├── AST_module/           # 本地语音采集与转写模块
│   ├── ast_service.py    # SenseVoice 集成入口
│   ├── audio_capture.py  # 音频采集与缓冲
│   └── requirements.txt  # AST 模块依赖
├── server/                # FastAPI后端服务
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务服务
│   │   └── main.py       # 应用入口
│   ├── requirements.txt  # Python依赖
│   └── Dockerfile        # Docker配置
├── frontend/             # 前端界面
│   ├── index.html        # 主页面
│   ├── css/              # 样式文件
│   ├── js/               # JavaScript文件
│   └── assets/           # 静态资源
├── docs/                 # 项目文档
└── docker-compose.yml    # 部署配置
```

## 快速开始（Electron + FastAPI）

### 1. 环境准备

```bash
# 安装依赖（一次性安装全栈）
pip install -r requirements.all.txt
npm ci

# 启动（Electron 会自启 FastAPI: 127.0.0.1:8090）
npm run dev
```

### 2. 两种工作流

- 直播直抓（推荐）：
  1) 在“直播音频转写”输入 Douyin 直播地址或 ID；
  2) 点击“开始转写”，同时启动弹幕抓取与音频拉流→SenseVoice 实时字幕；
  3) 通过 WS 端点 `/api/live_audio/ws` 接收增量/全文结果。

- 录制复盘（离线）：
  1) 点击“开始录制”（/api/report/live/start）→ ffmpeg 分段录制（默认30分钟）；
  2) 点击“停止录制”（/api/report/live/stop）；
  3) 点击“生成报告”（/api/report/live/generate）→ 生成 comments.jsonl、transcript.txt、report.html。

### 3. Docker部署

```bash
docker-compose up -d
```

### 4. Git 使用

有关 Git 使用的详细说明，请参阅以下文档：

- [Git 使用指南](docs/Git使用指南.md) - 完整的 Git 使用说明
- [Git 操作速查表](docs/Git操作速查表.md) - 常用 Git 命令快速参考
- [gitignore 配置说明](docs/gitignore配置说明.md) - 项目 .gitignore 配置说明

## 核心功能

- 🎯 **直播互动**: 实时同步抖音直播间弹幕、礼物、点赞
- 🎤 **本地语音转录**: SenseVoice 小型模型实时识别（默认“fast”档，支持 `LIVE_AUDIO_PROFILE=stable` 切换）
- 🧠 **AI智能分析**: 情感分析 + 热词提取
- 🎨 **可爱界面**: 猫咪主题Element UI界面

## MVP验证目标

- 弹幕抓取成功率 > 95%
- 语音识别准确率 > 80%
- 系统响应延迟 < 2秒
- 3天开发完成基础功能

---

**开发团队**: 提猫科技
**项目版本**: MVP v1.0
**最后更新**: 2025年9月21日
