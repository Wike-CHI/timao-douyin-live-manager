<p align="center">
  <img src="https://img.shields.io/badge/Electron-38-47848F?style=for-the-badge&logo=electron" alt="Electron">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/AI-LangChain-1C3C3C?style=for-the-badge" alt="LangChain">
</p>

<h1 align="center">🐱 提猫直播助手 · TalkingCat</h1>

<p align="center">
  <strong>AI驱动的抖音直播助手 | 实时语音识别 | 弹幕互动 | 智能话术</strong>
</p>

<p align="center">
  <a href="#-核心功能">核心功能</a> •
  <a href="#-技术架构">技术架构</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-演示">演示</a> •
  <a href="#-部署">部署</a>
</p>

---

> ⚠️ **重要声明**: 本项目仅依照《提猫直播助手源代码许可协议》授权，用于学习与研究目的。任何未经作者书面许可的商业化行为均被严格禁止。请务必阅读根目录下的 `LICENSE` 文件。

---

## 🎯 项目亮点

✨ **完整的直播辅助解决方案** - 从弹幕抓取到AI话术生成，一站式服务

🎤 **本地实时语音转写** - SenseVoice + VAD，直播音频直抓、断句校准

🧠 **AI实时分析** - LangChain + Qwen，生成热词洞察、实时提示与话术

🔒 **隐私优先** - 本地处理，直播数据不离开本地环境

---

## 🌟 核心功能

### 🎯 直播互动中台
- **实时弹幕抓取**: WebSocket连接，毫秒级响应
- **礼物/打赏监控**: 自动记录所有互动
- **REST/SSE推送**: 桌面端实时同步

### 🎤 本地实时语音转写
- **SenseVoice Small**: 高精度中文语音识别
- **VAD语音检测**: 自动断句校准
- **字幕流生成**: 实时字幕输出
- **降噪处理**: RNNoise音频增强

### 🧠 AI实时分析
- **热词洞察**: 自动识别直播热词
- **实时提示**: AI智能建议
- **话术生成**: LangChain + Qwen驱动
- **多AI支持**: Qwen/OpenAI/DeepSeek/豆包/ChatGLM

### 📊 直播复盘留存
- **自动生成**:
  - `comments.jsonl` - 弹幕记录
  - `transcript.txt` - 语音转录
  - `report.html` - 可视化报告
- **离线分析**: 支持离线查看历史数据

### 🔒 隐私与容错
- **本地处理**: 所有数据本地保存
- **离线可用**: 内置模型降级策略
- **完整日志**: `logs/`、`records/` 本地存储

---

## 📸 演示

### 功能截图

![主界面](docs/screenshots/main-interface.png)
*实时直播数据监控*

![AI分析](docs/screenshots/ai-analysis.png)
*AI实时分析与建议*

![语音转写](docs/screenshots/voice-transcript.png)
*实时语音转字幕*

---

## 🏗️ 技术架构

### 技术栈

| 层级 | 技术 |
|-----|------|
| **桌面端** | Electron 38, electron-builder |
| **渲染层** | React 18, Vite 5, Tailwind CSS, Zustand |
| **后端** | FastAPI, Uvicorn, Flask, WebSocket/SSE |
| **数据库** | SQLAlchemy, SQLite |
| **AI & NLP** | LangChain, Qwen, jieba, SnowNLP |
| **语音处理** | FunASR, SenseVoice, RNNoise, PyAudio |
| **音频处理** | ffmpeg, librosa, webrtc-audio-processing |
| **测试** | Jest, Pytest, ESLint, Playwright |

### 系统组件

```
electron/main.js
├─ 启动 renderer (Vite 30013) 渲染 React/Tailwind UI
├─ 启动 FastAPI：server/app/main.py → 127.0.0.1:8090
│   ├─ server/app/api/*           直播音频、复盘、Douyin、AI 路由
│   ├─ server/ingest/             抖音抓取与缓冲
│   ├─ server/nlp/                热词/情绪分析
│   └─ server/ai/                 LangChain/Qwen 实时策略
├─ 调用 server/modules/ast/*      SenseVoice 音频采集
└─ （兼容）server/app.py          Flask SSE 工具接口
```

### 目录结构

```
timao-douyin-live-manager/
├── server/                   # 后端服务
│   ├── app/main.py          # FastAPI 入口
│   ├── app/api/             # REST/WebSocket 路由
│   ├── app/services/        # 业务逻辑服务
│   ├── app/models/          # 数据模型
│   ├── ai/                  # AI 模块（LangChain/Qwen）
│   ├── modules/             # 核心功能模块
│   │   ├── ast/             # 音频转写（SenseVoice）
│   │   ├── douyin/          # 抖音弹幕抓取
│   │   └── nlp/             # 自然语言处理
│   └── utils/               # 工具函数
│
├── electron/                 # Electron 桌面端
│   ├── main.js              # 主进程
│   └── preload.js           # 预加载脚本
│
├── src/                      # React 前端
│   ├── components/          # React 组件
│   ├── pages/               # 页面
│   ├── hooks/               # 自定义 Hooks
│   ├── stores/              # Zustand 状态管理
│   └── utils/               # 工具函数
│
├── docs/                     # 文档
│   ├── API.md               # API 文档
│   ├── DEPLOYMENT.md        # 部署指南
│   └── USAGE.md             # 使用手册
│
├── tests/                    # 测试
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── e2e/                 # 端到端测试
│
├── records/                  # 直播记录（自动生成）
├── logs/                     # 日志文件（自动生成）
│
├── package.json             # Node.js 依赖
├── requirements.txt         # Python 依赖
├── LICENSE                  # 许可证
└── README.md                # 本文档
```

---

## 🚀 快速开始

### 环境要求

- **Node.js**: 18+
- **Python**: 3.10+
- **RAM**: 8GB+ (推荐16GB运行大型语音模型)
- **可选**: NVIDIA GPU (加速语音识别)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Wike-CHI/timao-douyin-live-manager.git
cd timao-douyin-live-manager

# 2. 安装Node.js依赖
npm install
# 或
pnpm install

# 3. 安装Python依赖
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件，配置API密钥

# 5. 启动应用
npm run dev
```

### 配置说明

编辑 `.env` 文件：

```env
# AI服务配置（选择一个或多个）
QWEN_API_KEY=your-qwen-api-key
OPENAI_API_KEY=your-openai-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key

# 语音识别配置
SENSEVOICE_MODEL=sensevoice-small
VAD_SENSITIVITY=medium

# 抖音直播间配置
DOUYIN_ROOM_ID=your-room-id

# 服务配置
FASTAPI_PORT=8090
ELECTRON_PORT=30013
```

---

## 📊 使用场景

### 🎬 直播主播
- **实时互动**: 自动抓取弹幕，快速响应观众
- **话术辅助**: AI生成互动话术，提升直播效果
- **数据复盘**: 直播后自动生成分析报告

### 🎯 运营团队
- **数据监控**: 实时监控直播间互动数据
- **用户分析**: 分析观众行为和偏好
- **效果评估**: 评估直播效果和ROI

### 📈 MCN机构
- **多账号管理**: 支持管理多个主播账号
- **数据统计**: 汇总分析多个直播数据
- **培训素材**: 生成主播培训材料

---

## 🔧 高级功能

### AI网关统一管理

```python
# 支持多AI服务商一键切换
AI_PROVIDERS = {
    "qwen": {
        "api_key": "your-qwen-key",
        "model": "qwen-max"
    },
    "openai": {
        "api_key": "your-openai-key",
        "model": "gpt-4"
    },
    "deepseek": {
        "api_key": "your-deepseek-key",
        "model": "deepseek-chat"
    }
}
```

### 自定义话术模板

```python
# 配置话术生成模板
TEMPLATE = """
基于以下直播数据生成互动话术：
- 弹幕数量: {comment_count}
- 热词: {hot_words}
- 观众情绪: {sentiment}

请生成3条互动话术建议。
"""
```

---

## 🚀 部署

### 开发环境

```bash
npm run dev
```

### 生产环境

```bash
# 构建桌面应用
npm run build

# 打包安装程序
npm run package

# 生成的安装包在 dist/ 目录
```

### Docker部署

```bash
# 构建镜像
docker build -t timao-live-manager .

# 运行容器
docker run -p 8090:8090 timao-live-manager
```

---

## 📚 API文档

### REST API

```python
# 获取直播数据
GET /api/live/data

# 开始录制
POST /api/live/start
{
  "room_id": "123456"
}

# 停止录制
POST /api/live/stop

# 获取AI分析
GET /api/ai/analysis
```

### WebSocket事件

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8090/ws');

// 接收弹幕
ws.on('comment', (data) => {
  console.log('新弹幕:', data);
});

// 接收语音转写
ws.on('transcript', (data) => {
  console.log('语音转写:', data);
});

// 接收AI建议
ws.on('ai_suggestion', (data) => {
  console.log('AI建议:', data);
});
```

完整API文档: [docs/API.md](docs/API.md)

---

## 🧪 测试

```bash
# 运行单元测试
npm run test:unit

# 运行集成测试
npm run test:integration

# 运行E2E测试
npm run test:e2e

# 测试覆盖率
npm run test:coverage
```

---

## 🤝 贡献指南

欢迎贡献代码、报告Bug或提出新功能建议！

详见: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📝 更新日志

### v1.2.0 (2024-01-20)
- ✨ 新增AI网关统一管理
- ✨ 支持多AI服务商切换
- 🎨 UI界面优化
- ⚡ 性能提升30%

### v1.1.0 (2024-01-10)
- ✨ 新增SenseVoice语音识别
- 🐛 修复弹幕抓取延迟问题
- 📝 完善文档

详见: [CHANGELOG.md](CHANGELOG.md)

---

## 📄 许可证

本项目采用《提猫直播助手源代码许可协议》- 详见 [LICENSE](LICENSE) 文件

**重要**: 仅供学习研究，禁止商业化使用

---

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - AI框架
- [FunASR](https://github.com/alibaba-damo-academy/FunASR) - 语音识别
- [Electron](https://www.electronjs.org/) - 桌面应用框架
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架

---

## 📞 联系方式

- **邮箱**: 3132812664@qq.com
- **GitHub**: [@Wike-CHI](https://github.com/Wike-CHI)
- **项目地址**: [GitHub](https://github.com/Wike-CHI/timao-douyin-live-manager)

---

## 💼 商业合作

如果您需要：
- 🔧 定制开发
- 🏢 商业授权
- 📊 企业版功能
- 🎓 技术培训

请联系: 3132812664@qq.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个Star支持！⭐**

Made with ❤️ by Wike

</div>
