# 本地服务拆分实现进度

## 📋 已完成

### 1. 模型按需下载系统 ✅
- ✅ `.gitignore` 更新：排除模型二进制、临时文件
- ✅ `ModelDownloader`: HTTP Range 请求、断点续传、SHA256 校验
- ✅ `manifest-fallback.json`: CDN 降级配置
- ✅ `ensure-space.js`: 磁盘空间与写权限检查
- ✅ `ModelManager`: IPC 通信、状态管理、注册表

**路径**: `electron/main/model/`

### 2. 服务端拆分基础 ✅
- ✅ `server/cloud/main.py`: 云端服务入口（用户、鉴权、支付）
- ✅ `server/local/main.py`: 本地服务入口（弹幕、转写、AI）

**目标**:
- 云端 < 512MB 内存
- 本地重度服务打包到客户端

---

## 🚧 待完成

### 3. Electron 集成
- [ ] 更新 `electron/main/index.js`: 启动本地服务、集成 ModelManager
- [ ] 渲染进程：模型下载 UI 组件（进度条、暂停/继续/取消）

### 4. 服务路由迁移
- [ ] 云端路由：从现有 `server/app/api` 迁移轻量接口
  - `auth.py`: 登录、注册、Token
  - `user.py`: 用户信息
  - `payment.py`: 支付、订阅
- [ ] 本地路由：迁移重度服务
  - `live.py`: 弹幕拉取、WebSocket
  - `transcribe.py`: 语音转写
  - `ai.py`: AI 处理

### 5. 打包配置
- [ ] `package.json`: `extraResources` 包含 `server/local`（不含模型）
- [ ] Electron Builder 配置

### 6. 测试与文档
- [ ] 端到端测试：模型下载 → 本地服务启动 → API 调用
- [ ] 部署文档更新

---

## 📂 项目结构（新增）

```
electron/
  main/
    model/
      ✅ model-downloader.js      # 下载器
      ✅ model-manager.js          # 管理器
      ✅ ensure-space.js           # 空间检查
      ✅ manifest-fallback.json    # CDN 降级

server/
  ✅ cloud/
      main.py                      # 云端入口
      routers/                     # 待迁移
  ✅ local/
      main.py                      # 本地入口
      routers/                     # 待迁移
```

---

## 🔧 使用方式（计划）

### 开发环境
```bash
# 云端服务
cd server/cloud
python main.py  # 监听 15000

# 本地服务（在 Electron 中自动启动）
cd server/local
python main.py  # 监听 16000（仅本地）

# Electron
cd electron
npm run dev
```

### 生产环境
- 云端：PM2 部署 `server/cloud/main.py`
- 本地：打包进 Electron 安装包

---

## 📝 Commit 记录

1. `chore(gitignore): exclude model download temp files`
2. `feat(model-download): add ModelDownloader with HTTP Range and SHA256 verify`
3. `feat(model-download): add fallback CDN manifest config`
4. `feat(model-download): add disk space and write permission check`
5. `feat(model-download): add ModelManager with IPC and state management`
6. `feat(service-split): add cloud and local service skeleton`

---

**分支**: `local-test`  
**基线**: `main`  
**状态**: 🚧 进行中
