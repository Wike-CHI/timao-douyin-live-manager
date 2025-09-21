# 提猫直播助手 MVP 项目

基于自研抖音直播抓取器 + VOSK本地语音识别的主播AI助手

## 技术栈

- **前端**: HTML + CSS + Element UI 2.15
- **后端**: FastAPI + SQLite + Redis
- **数据抓取**: 项目内置 DouyinLiveWebFetcher 模块
- **语音识别**: VOSK本地模型 (中文)
- **AI分析**: jieba + SnowNLP (本地NLP)
- **部署**: Docker + Nginx

## 项目结构

```
timao-douyin-live-manager/
├── vosk-api/              # VOSK语音识别
│   ├── python/vosk/       # VOSK Python API
│   └── vosk-model-cn-0.22/ # 中文语音模型
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

## 快速开始

### 1. 环境准备

```bash
# Python 3.11+
pip install -r server/requirements.txt

# 启动服务
cd server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端访问

```bash
# 打开浏览器访问
http://localhost:3000
```

### 3. Docker部署

```bash
docker-compose up -d
```

## 核心功能

- 🎯 **直播弹幕抓取**: 实时抓取抖音直播间弹幕
- 🎤 **VOSK语音转录**: 本地中文语音识别
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
