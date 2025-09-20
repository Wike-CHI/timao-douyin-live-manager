# 提猫直播助手

一个基于 Electron + Flask 的抖音直播评论实时分析与AI话术生成工具。

## 功能特性

- 🔄 **实时评论抓取**: 抓取抖音直播间评论流
- 🔥 **热词分析**: 智能提取评论热词，实时排序
- 🤖 **AI话术生成**: 基于评论内容生成互动话术
- 💻 **桌面端看板**: 三区域实时展示（评论流/热词榜/题词区）
- ⚡ **低延迟**: 评论到话术生成延迟 ≤ 2s

## 技术栈

- **前端**: Electron + HTML/CSS + JavaScript
- **后端**: Python Flask + Server-Sent Events
- **AI服务**: DeepSeek/OpenAI/豆包（可切换）
- **数据存储**: 内存环形缓冲区

## 快速开始

### 环境要求

- Node.js ≥ 16.x
- Python ≥ 3.8
- 网络连接（访问AI API）

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd timao-douyin-live-manager
```

2. 安装依赖
```bash
npm install
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

4. 启动应用
```bash
npm run dev
```

## 项目结构

```
timao-douyin-live-manager/
├── electron/                 # Electron 桌面端
│   ├── main.js              # 主进程
│   ├── preload.js           # 预加载脚本
│   └── renderer/            # 渲染进程
│       ├── index.html       # 主界面
│       ├── styles.css       # 样式文件
│       └── app.js           # 前端逻辑
├── server/                  # Flask 后端
│   ├── app.py              # 主应用
│   ├── ingest/             # 评论抓取
│   ├── nlp/                # 热词分析
│   ├── ai/                 # AI话术生成
│   └── utils/              # 工具模块
├── docs/                   # 项目文档
├── package.json            # Node.js 配置
├── requirements.txt        # Python 依赖
└── .env.example           # 环境变量模板
```

## API 接口

- `GET /api/health` - 健康检查
- `GET /api/stream/comments` - 评论流推送 (SSE)
- `GET /api/hotwords` - 热词排行
- `GET /api/tips/latest` - 最新话术
- `POST /api/config` - 配置管理

## 开发指南

详细的开发文档请参考 `docs/` 目录：

- [需求对齐文档](docs/提猫直播助手_ALIGNMENT_项目初始化.md)
- [架构设计文档](docs/提猫直播助手_DESIGN_架构设计.md)
- [任务拆分文档](docs/提猫直播助手_TASK_任务拆分.md)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！