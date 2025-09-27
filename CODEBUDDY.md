说中文

你是 CodeBuddy Code。请严格按本仓库的专用约定工作。

常用命令

- 安装 Node 依赖：npm ci
- 启动桌面应用（同时启动 Flask 后端）：npm run dev
- 仅启动 Electron：npm run electron
- 构建安装包：npm run build
- 前端/Electron 代码 Lint：npm run lint
- JS 测试：npm test
- 运行单个 Jest 用例：npx jest 路径/到/测试 -t "用例名片段"
- Python 环境依赖（统一）：pip install -r requirements.all.txt
- 启动后端 A（Flask）：python server/app.py
  （包含 FastAPI + AST + 工具依赖，无需分模块安装）
- 启动后端 B（FastAPI）：uvicorn server.app.main:app --reload --host 0.0.0.0 --port 8000
- Python 代码格式/检查（server/）：black . && flake8
- Python 测试（server/ 或根目录 pytest.ini 所在处）：pytest
- 运行单个 pytest 用例：pytest 路径/到/test_file.py -k 用例名片段

架构与关键模块（高层）

- 桌面壳（Electron）：electron/，入口 electron/main.js。应用启动时通过 spawn 启动 Python Flask（server/app.py），轮询 http://127.0.0.1:5001/api/health 就绪后加载 renderer/index.html。打包由 package.json 的 electron-builder 配置生成 dist/ 安装包。
- 后端 A（当前 Electron 目标）：Flask 应用 server/app.py，提供 /api/*（健康检查、评论流 SSE、热词、话术等）。整合领域服务：
  - 数据抓取与处理：server/ingest/*、server/nlp/*、server/ai/*
  - 公共工具与配置：server/utils/*（Config、日志等）
  - SSE：/api/stream/comments 持续推送评论
- 后端 B（现行）：FastAPI 应用 server/app/main.py，挂载直播音频直抓转写路由 server/app/api/live_audio.py，提供 REST 与 WebSocket（/api/live_audio/ws）。如有 frontend/ 会通过 StaticFiles 提供静态页。
- 语音/AST 集成：AST_module/ 提供 SenseVoice 识别（sensevoice_service.py），直播直抓由 live_audio 路由负责启动/停止、回传结果。
- 直播抓取：douyin_live_fecter_module/ 集成 DouyinLiveWebFetcher，提供抖音直播间弹幕抓取、消息适配与状态管理能力。

关键运行流

- Electron 启动流：electron/main.js → 启动 server/app.py → 轮询 /api/health → 显示 UI
- Flask SSE：/api/stream/comments 通过 CommentFetcher 推送事件；客户端使用 EventSource 订阅
- FastAPI 实时转写：POST /api/live_audio/start 后，通过 WebSocket /api/live_audio/ws 持续下发转写结果；/api/live_audio/status 查询状态，/stop 终止

重要约定与参考

- 双后端并存：Electron 目前固定检查 127.0.0.1:5001（Flask）。FastAPI 为独立进程与端口，不要混淆。
- 修改 Electron 启动行为需同时校对 electron/main.js 中 FLASK_URL 与 Python 启动路径。
- Python 依赖分离：根 requirements.txt（Flask 栈）；server/requirements.txt（FastAPI+AST 栈）。按需安装对应集合。
- 语音功能依赖本地音频与 SenseVoice 模型（如使用实时转写，需安装 pyaudio 等）。
- 6A 工作流：按 .qoder/rules/6A_workflow.md 的 ALIGNMENT/CONSENSUS/DESIGN/TASK/ACCEPTANCE/FINAL/TODO 文档产物流程推进较大改动。
- 安全披露：遵循内部安全流程，定期审查抓取与语音模块的依赖风险。

常用路径索引

- Electron 入口：electron/main.js
- Flask 入口：server/app.py
- FastAPI 入口：server/app/main.py
- 转写 API：server/app/api/live_audio.py
- 直播抓取模块：douyin_live_fecter_module/

示例（单文件/接口调试）

- 启动 FastAPI 并调试：uvicorn server.app.main:app --reload
- 连接转写 WS：ws://127.0.0.1:8007/api/live_audio/ws
- 订阅 Flask SSE：curl -N http://127.0.0.1:5001/api/stream/comments
