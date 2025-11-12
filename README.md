# 提猫直播助手 · TalkingCat

> **重要声明：** 本项目仅依照仓库内的《提猫直播助手源代码许可协议（仅供学习研究）》授权，用于学习与研究目的。任何未经作者书面许可的商业化行为（含直接或间接盈利）均被严格禁止，违者作者保留追究法律责任的权利。请务必阅读根目录下的 `LICENSE` 文件。

基于 Electron + FastAPI 的抖音直播主播助手，整合本地 SenseVoice/FunASR 语音识别、Douyin 弹幕抓取、LangChain/Qwen AI 话术生成与直播复盘能力，默认在本机完成处理，直播数据不会离开本地环境。

## 功能亮点

- 🎯 **直播互动中台**：`server/modules/douyin` 模块拉取 WebSocket 弹幕/礼物，并通过 REST/SSE 向桌面端推送。
- 🎤 **本地实时语音转写**：`server/modules/ast` 使用 SenseVoice Small + VAD，实现直播音频直抓、断句校准与字幕流。
- 🧠 **AI 实时分析**：`server/ai` 基于 LangChain + Qwen/OpenAI 兼容接口生成热词洞察、实时提示与话术。
- 🚀 **AI 网关统一管理**：支持多 AI 服务商（Qwen/OpenAI/DeepSeek/豆包/ChatGLM）一键切换、集中配置、自动监控。
- 📊 **直播复盘留存**：自动生成 `comments.jsonl`、`transcript.txt`、`report.html` 等复盘素材，支撑离线分析。
- 🔒 **隐私与容错**：本地处理、离线可用，内置模型/接口降级策略，日志与缓存全部保存在本地 `logs/`、`records/`。

## 技术栈

- 桌面端：Electron 38、electron-builder、concurrently、wait-on。
- 渲染层：React 18、Vite 5、Tailwind CSS、Zustand。
- 后端：FastAPI + Uvicorn（主要 API）、Flask（遗留 SSE 工具）、WebSocket/SSE、SQLAlchemy + SQLite。
- AI & NLP：LangChain、Qwen 兼容接口、jieba、SnowNLP、RNNoise、FunASR、SenseVoiceSmall。
- 音频处理：ffmpeg、PyAudio、librosa、webrtc-audio-processing。
- 测试与质量：Jest、Pytest、ESLint、Playwright（Electron 测试脚手架）。

## 系统组件

```
electron/main.js
├─ 启动 renderer (Vite 30013) 渲染 React/Tailwind UI
├─ 启动 FastAPI：server/app/main.py → 127.0.0.1:8090 (REST + WebSocket)
│   ├─ server/app/api/*           直播音频、复盘、Douyin、AI 等路由
│   ├─ server/ingest/             抖音抓取与缓冲
│   ├─ server/nlp/                热词/情绪分析
│   └─ server/ai/                 LangChain/Qwen 实时策略
├─ 调用 server/modules/ast/*      SenseVoice 音频采集、后处理与降级
└─ （兼容）server/app.py          Flask SSE 与工具接口
```

## 目录导览

```
timao-douyin-live-manager/
├── server/                   # 后端服务（所有后端代码统一在此）
│   ├── app/main.py          # FastAPI 入口
│   ├── app/api/             # REST/WebSocket 路由
│   ├── app/services/        # 业务逻辑服务
│   ├── app/models/          # 数据模型
│   ├── ai/                  # AI 相关模块（LangChain/Qwen 工作流）
│   ├── modules/             # 核心功能模块
│   │   ├── ast/             # 音频转写（SenseVoice/FunASR）
│   │   ├── douyin/          # 抖音弹幕抓取
│   │   └── streamcap/       # 流媒体处理
│   ├── utils/               # 配置、日志、工具函数
│   ├── tests/               # 测试文件（单元测试、集成测试）
│   └── requirements.txt     # Python 依赖
│
├── electron/                # 桌面端应用
│   ├── main.js              # Electron 主进程
│   └── renderer/            # React + Vite 前端，端口 30013（dev）
│       └── src/assets/      # 前端资源文件（图标、图片等）
│
├── scripts/                 # 工具脚本（中文分层）
│   ├── 构建与启动/          # build-all、integrated-launcher、service_launcher 等
│   ├── 部署与运维/          # docker_deploy_full 等部署脚本
│   ├── 检查与校验/          # check_backend、validate_port_config、verify-port-config 等
│   ├── 初始化与迁移/        # setup_env、init_*、migrate_env_config 等
│   ├── 诊断与排障/          # debug/diagnose、kill-port、port-manager 等
│   ├── 测试与验证/          # test_douyin_live、test_memory_redis 等
│   └── 辅助工具/            # list_users、simple_list_users 等
│
├── docs/                    # 文档目录（企业级分层管理）
│   ├── guides/              # 安装、部署、打包、使用指南
│   ├── runbooks/            # 故障处理、紧急变更操作手册
│   ├── reference/           # 端口、命令、配置基线
│   ├── reports/             # Fix/验收/总结报告
│   ├── internal/            # 内部凭证及敏感信息（受控访问）
│   ├── AI方案与集成/         # AI 网关、AST、ASR 等方案沉淀
│   ├── 直播音频方案/         # Douyin 抓取、录制链路与音频策略
│   ├── 部署与运维指南/       # 环境配置、脚本、运维与安全加固
│   ├── 产品使用手册/         # 启动、手册、脚本使用说明
│   ├── 开发规范与流程/       # Git/Code 规范、项目结构、Token 检查
│   ├── 测试与质量保障/       # 测试、Review、质量改进文档
│   └── 项目复盘与报告/       # 迁移总结、复盘报告、完成说明
│
├── deploy/                  # 部署相关文件（Docker、部署文档、脚本）
│   ├── Dockerfile           # Docker 镜像构建
│   ├── docker-compose.yml   # Docker Compose 配置
│   ├── scripts/             # 部署脚本
│   └── config/              # 部署配置
├── migrations/              # 数据库迁移文件
├── tests/                   # 全局测试文件（统一分层）
│   ├── integration/         # 跨服务端到端校验
│   ├── regression/          # 缺陷回归/修复验证
│   ├── scripts/             # Shell 驱动或环境校验脚本
│   ├── manual/              # 手工/可视化验证页面
│   └── reports/             # 测试报告、运行结果
├── electron/                # 桌面端应用
│   ├── main.js              # Electron 主进程
│   └── renderer/            # React + Vite 前端
│       └── src/
│           └── assets/      # 前端资源文件（图标、图片等）
├── tools/                   # 开发工具（模型下载、缓存清理等）
├── config/                  # 配置文件
├── records/                 # 记录文件（日志、数据等）
└── logs/                    # 日志文件
```

> **注意**：`AST_module`、`DouyinLiveWebFetcher`、`StreamCap` 等历史模块已迁移到 `server/modules/` 目录，历史代码保存在 `docs/legacy_code/` 仅用于参考。详细说明请参考 [docs/开发规范与流程/PROJECT_STRUCTURE.md](docs/开发规范与流程/PROJECT_STRUCTURE.md)。

## 文档与测试分层

- `docs/guides/`: 快速启动、部署、打包与日常操作指南（例如 `docs/guides/Electron打包指南.md`、`docs/guides/QUICKSTART_ENV_SETUP.md`）。
- `docs/runbooks/`: 生产值班/紧急处理手册，集中存放 CORS、依赖冲突、紧急修复等 SOP。
- `docs/reference/`: 端口、命令、配置等基线信息（例如 `docs/reference/PORTS_CONFIGURED.txt`、`docs/reference/README-端口配置.md`）。
- `docs/reports/`: 变更验收、修复总结、专项复盘（LangGraph、SenseVoice、部署完成说明等）。
- `docs/internal/`: 受控访问的信息（如 `docs/internal/帐号以及密码.txt`），建议按权限管理。
- `tests/integration/`: 跨服务/端到端校验脚本，包含 `tests/integration/test_admin_api.py`、`tests/integration/test_xfyun_asr.py` 等。
- `tests/regression/`: 针对缺陷修复与性能优化的验证用例（`tests/regression/test_ai_gateway_fix.py`、`tests/regression/test_sensevoice_optimization.py`）。
- `tests/scripts/`: Shell 驱动/环境检测脚本，例如 `tests/scripts/test_cors.sh`、`tests/scripts/test_ai_auth.sh`。
- `tests/manual/`: 需要人工操作或浏览器加载的用例（`tests/manual/test_history_api.html` 等）。
- `tests/reports/`: 测试产出与运行记录（`tests/reports/comprehensive_test_report.json`）。

## 环境准备

### 系统要求

- Windows 10+/macOS 13+/Ubuntu 20.04+（64 位）
- Node.js ≥ 16、npm ≥ 8、Python ≥ 3.9
- 建议安装 ffmpeg 并加入 PATH
- 至少 4 GB 内存，SenseVoiceSmall 建议 8 GB 以上

### 安装依赖

```bash
# Python（FastAPI + AST + 工具）
pip install -r requirements.all.txt

# Node（Electron 主进程 + Renderer）
npm ci
```

`npm ci` 会触发 `postinstall`，自动为 `electron/renderer` 安装前端依赖。

### 准备本地语音模型（首次部署）

```bash
python tools/download_sensevoice.py      # 下载 SenseVoiceSmall
python tools/download_vad_model.py       # 下载 VAD 模型
```

模型默认保存在 `models/models/iic/`，`/api/live_audio/health` 可检查准备情况。若需要 GPU/CUDA，请先运行 `python server/server/tools/prepare_torch.py`。

## 启动流程

### Electron 一体化开发（推荐）

```bash
npm run dev
```

- `renderer` 以 Vite 模式运行在 http://127.0.0.1:30013
- Electron 主进程自动等待端口并拉起桌面窗口
- `uvicorn` 在后台启动 FastAPI（127.0.0.1:8090），提供 REST `/api/*`、WebSocket `/api/live_audio/ws`、文档 `/docs`

如需关闭，只需退出 Electron 窗口或在终端中 `Ctrl+C`。

### 仅启动 FastAPI 后端

```bash
uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8090
```

手动启动时，请在 `electron/renderer/.env` 设置 `VITE_FASTAPI_URL=http://127.0.0.1:8090` 以便前端指向正确 API。

### 仅启动遗留 Flask SSE 服务

```bash
python server/app.py
```

Flask 服务用于旧版字幕面板与 SSE 工具，Electron 正式流程无需手动启动。

### AST 模块本地调试

参阅 `AST_README.md` 或执行：

```bash
python start_ast_test.py      # 启动 AST FastAPI
python start_web_server.py    # 启动测试页面（8080）
```

浏览器访问 http://127.0.0.1:8080/AST_test_page.html 进行语音链路验证。

## 测试与质量保障

- `npm test`：运行 Electron/renderer Jest 用例。
- `npm run lint`：对 `electron/` 目录执行 ESLint。
- `pytest`：运行 Python 测试（`tests/` 与 `server/tests/`）。
- `pytest server/tests/test_live_audio.py::TestLiveAudioAPI`：聚焦关键接口。
- `npm run build` 前建议先通过上述测试与 `npm run lint`。

## 打包与发布

- `npm run build`：使用 electron-builder 构建当前平台安装包，输出 `dist/`。
- `npm run build:win[32|64]`：生成指定架构的 Windows 便携包。
- `npm run release`：构建 + 生成 `release/` 目录（自动写入默认 AI `.env`）。
- 推荐在打包前执行 `pip install -r requirements.all.txt --upgrade` 与 `npm ci`，保持依赖一致。

## 配置与数据目录

### AI 网关配置（.env 文件）

```bash
# 主服务商（必填）
AI_SERVICE=qwen
AI_API_KEY=sk-your-api-key
AI_MODEL=qwen-plus

# 备用服务商（可选）
DEEPSEEK_API_KEY=sk-deepseek-key
OPENAI_API_KEY=sk-openai-key
```

**AI 网关管理**：http://localhost:10090/static/ai_gateway_manager.html

### 其他配置

- `.env`（根目录）：AI 配置、环境变量。
- `electron/renderer/.env`：前端 API 地址、调试开关（默认继承 Electron 主进程环境）。
- `config.json`：Douyin 房间号、Cookie、缓存等业务参数，可在设置页写入。
- 持久化：
  - `records/`：直播复盘生成的中间文件
  - `logs/` 与 `logs/uvicorn.log`：FastAPI/Electron 日志
  - `audio_logs/`：语音转写音频片段（开启持久化时）

## 文档与资源

- `docs/产品使用手册/启动说明.md`：桌面端启动流程与故障排查。
- `AST_README.md` / `AST_module/docs/`：语音模块架构、测试方法。
- `docs/部署与运维指南/MODELS.md`：模型下载、目录规划与容量建议。
- `docs/部署与运维指南/Windows打包部署指南.md`：Windows 构建/签名注意事项。
- `docs/AI方案与集成/AI_GATEWAY_SIMPLE.md`：AI 网关快速指南。
- `docs/AI方案与集成/AI_GATEWAY_API_KEY_MANAGEMENT.md`：API Key 管理文档。
- `docs/部署与运维指南/MONITORING_GUIDE.md`：AI 成本监控指南。
- `docs/直播音频方案/提猫直播助手_API_数据模型与接口规范.md`：REST API 字段约定。
- `docs/部署与运维指南/安全加固实施指南.md`：生产环境安全配置 Checklist。

## 注意事项

- `npm run dev` 会尝试占用 30013（Vite）与 9019（FastAPI，默认端口，可通过环境变量 `BACKEND_PORT` 修改）；若端口被占用，会跳过后端启动，请手动校验。
- SenseVoice/VAD 缺失时，`/api/live_audio/health` 会给出自动修复脚本提示。
- 若需代理出站流量，请为 `.env` 中的 AI 配置设置合规值。
- 对于离线部署，可通过 `tools/create_release.py` 打出便携包并在 `.env` 中关闭云端 AI（例如设置 `AI_SERVICE=offline`）。

---

**开发团队**：提猫科技  
**应用版本**：v1.0.0  
**最后更新**：2025年10月26日
