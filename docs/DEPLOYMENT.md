# 提猫直播助手（TalkingCat）部署指南

本产品中文名：提猫直播助手；英文名：TalkingCat。

本指南覆盖本地开发、桌面端打包发布、以及仅将“登录/注册/支付”托管到腾讯云（保留 AST 与抖音互动在本地）的推荐流程与配置要点。

## 技术栈与产品特点
- 桌面端 UI（TalkingCat 桌面版）：Electron + React + Vite（跨平台）
- 本地后端：FastAPI（Python 3.10+），SSE + WebSocket 实时通道
- 语音识别：SenseVoiceSmall（FunASR 生态），本地低延时转写（安全/隐私不出机）
- 抖音互动：自研 DouyinLiveWebFetcher（WebSocket）→ FastAPI（SSE/WS）桥接
- 架构模式：Hybrid（云端仅承载账户/支付最小接口；核心数据与模型完全本地）

## 关键路径（TalkingCat 桌面版与本地服务）
- Electron 主进程：`electron/main.js`
- 前端渲染：`electron/renderer/`
- FastAPI 主应用：`server/app/main.py`
- Douyin → Web 桥接：`server/app/services/douyin_web_relay.py`
- 转写接口（直播直抓 + SenseVoice）：`server/app/api/live_audio.py`
- AST 模块（SenseVoice/FunASR）：`AST_module/`

## 环境变量
- 渲染进程（Vite）：
  - `VITE_FASTAPI_URL` 本地 FastAPI 地址（Electron 默认 `http://127.0.0.1:8090`）
  - `VITE_AUTH_BASE_URL` 云端鉴权/支付后端地址（未设置则使用本地 mock）
- 主进程（Electron）：
  - `ELECTRON_START_API` 是否由 Electron 自启本地 FastAPI（默认 `true`；设置为 `false` 跳过）

示例（开发）：
- PowerShell
  - `$env:VITE_AUTH_BASE_URL='https://auth.company.com'`
- Bash
  - `export VITE_AUTH_BASE_URL='https://auth.company.com'`

## 本地开发
1) 安装依赖
- Node：`npm ci`
- Python：`pip install -r requirements.all.txt`（包含 FastAPI + AST + 工具依赖）

2) 一键启动（推荐）
- `npm run dev`
- 行为：启动 Vite(30013) + Electron；Electron 自动拉起 FastAPI（uvicorn:8090）

3) GPU 依赖准备
- `npm run prepare:torch` (Windows) 或 `python tools/prepare_torch.py` (Linux/macOS) 确保安装 GPU 版 torch；可通过 `FORCE_TORCH_MODE=cpu|gpu` 控制安装策略

4) 模型缓存（建议）
- 设置模型缓存目录，避免下载到系统盘：
  - `MODELSCOPE_CACHE=./models`，`HF_HOME=./models/huggingface`

4) Windows 中文日志乱码
- PowerShell：`$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; chcp 65001`
- CMD：`set PYTHONUTF8=1 & set PYTHONIOENCODING=utf-8 & chcp 65001`

## 桌面端打包发布
1) 构建渲染进程
- `npm --prefix electron/renderer run build`

2) 打包 Electron
- `npm run build`（electron-builder）
- 已包含的打包目录：`electron/**/*`、`server/**/*`、`AST_module/**/*`、`DouyinLiveWebFetcher/**/*`、`frontend/**/*`

3) 运行
- 用户启动应用后，Electron 默认自启本地 FastAPI；渲染页连接本地 AST 与抖音互动。

## 仅云端托管“登录/注册/支付”（腾讯云）
目标：将登录/注册/支付托管到腾讯云（公司域名子域），其余能力留在本地。

### 一、云端最小接口契约
- `POST /api/auth/login`  { email, password } → { success, token, user, isPaid }
- `POST /api/auth/register`  { email, password, nickname } → { success, user }
- `POST /api/payment/upload`  multipart/form-data:file → { success, status:'PENDING_REVIEW', message }
- `GET  /api/payment/status` → { success, status:'APPROVED'|'REJECTED', message }

参考 Node/Express 模板见：`docs/cloud/auth-backend-node/`。

### 二、在腾讯云托管后端
> 可选：云托管（CloudBase Run，容器）或 云函数（HTTP 网关）。以下以 CloudBase Run 容器为例。

1) 准备镜像（示例 Dockerfile：Node 18 + Express）
```
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD ["node","index.js"]
```

2) 推送镜像到 TCR（腾讯云容器镜像服务）
- 创建 TCR 实例，登录并 `docker build` / `docker push` 镜像

3) 创建云托管服务
- 选择镜像来源（TCR），端口 8080，最小副本 1，按量计费或包月
- 设置环境变量：`ALLOW_ORIGINS`（允许跨域来源，逗号分隔）

4) 绑定自定义域名
- 使用公司域名子域，如 `auth.company.com` 绑定到该服务
- 控制台提示添加 DNS CNAME；证书可自动签发

5) CORS 配置
- 云端后端返回：`Access-Control-Allow-Origin: <你的来源>`, `Access-Control-Allow-Credentials: true`
- 开发来源：`http://127.0.0.1:30013`；发行版 Electron 可能 `Origin:null`，可显式放行或通过本地后端转发

### 三、渲染端指向云端鉴权
- 设置 `VITE_AUTH_BASE_URL='https://auth.company.com'`
- AST/抖音互动继续走 `VITE_FASTAPI_URL`（Electron 默认 `http://127.0.0.1:8090`）

## 运行拓扑（推荐）
- 桌面端（本地）：Electron 渲染页（Vite 构建）
  - 本地 FastAPI：转写（/api/live_audio/*）、抖音互动（/api/douyin/web/*）
- 云端：鉴权/支付（/api/auth/*, /api/payment/*）→ 绑定 `auth.company.com`

## 故障排查
- Electron 白屏（开发）：确认已启动 Vite(30013)
- 端口冲突（8090）：避免重复拉起 uvicorn；或改端口并设置 `VITE_FASTAPI_URL`

## 模型与生成物不入库（重要）
- 仓库已清理并忽略模型权重、音频日志与运行记录（例如 `models/**`, `records/**`, `**/audio_logs/**`, `**/artifacts/**`）。
- 运行前请配置模型缓存目录与路径，避免下载到系统盘：
  - Windows/Powershell 示例：
    - `$env:MODELSCOPE_CACHE='D:\\models'`
    - `$env:HF_HOME='D:\\models\\huggingface'`
  - Bash 示例：
    - `export MODELSCOPE_CACHE="$HOME/models"`
    - `export HF_HOME="$HOME/models/huggingface"`
- 可选：在 `AST_module/config.py` 中将 SenseVoice Small 与 VAD 指到本地目录；详见 `AST_module/README_SenseVoice.md`。
- 生成的直播记录/话术等运行产物默认写入 `records/`，不会被 Git 跟踪，可按需自行清理。
- SSE/WS 断开：检查反向代理超时；前端已含重连提示
- 云端 4xx/5xx：核对 CORS、域名生效、证书、接口路径

## 安全与合规
- 生产收紧 CORS，仅允许受信任来源（公司域名/Electron 应用）
- 登录密码加盐哈希（bcrypt 等），支付图片存储加鉴权
- 正式接入微信/支付宝支付需备案且使用自有域名

## 清单（Checklist）
- [ ] 本地可运行（Electron + FastAPI + AST + Douyin）
- [ ] 云端鉴权/支付接口可用且已绑定子域
- [ ] 渲染端已设置 `VITE_AUTH_BASE_URL`
- [ ] CORS/证书/域名生效
- [ ] 打包产物可在目标机器稳定运行

---

更多参考：`docs/cloud/auth-backend-node/README.md`
