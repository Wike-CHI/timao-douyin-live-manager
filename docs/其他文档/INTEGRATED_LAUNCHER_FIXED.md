# ✅ Integrated Launcher 已修复

> **修复时间**：2025-01-15  
> **分支**：local-view  
> **审查人**：叶维哲

---

## 🔧 修复的问题

### 1. ❌ 端口配置错误
- **integrated-launcher.js** 硬编码了旧端口（后端11111，前端10050）
- **electron/main.js** 默认连接10065端口

### 2. ❌ Electron 白屏
- Electron 尝试连接 `http://127.0.0.1:10065/`
- 但前端实际运行在 `http://127.0.0.1:3000/`
- 导致 `ERR_CONNECTION_REFUSED`

### 3. ❌ 字符显示乱码
- Python 输出中文显示为乱码
- 需要强制 UTF-8 编码

---

## ✅ 已修复的文件

### 1. scripts/构建与启动/integrated-launcher.js

```javascript
// 修改前
const backendPort = '11111';
const frontendPort = '10050';

// 修改后
const backendPort = '8080';
const frontendPort = '3000';
```

**UTF-8 编码配置**（已经存在，增强了）：
```javascript
const spawnEnv = {
    ...process.env,
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8: '1',
};
```

### 2. electron/main.js

```javascript
// 修改前
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:10065';

// 修改后
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:3000';
```

---

## 🚀 现在可以使用 integrated launcher

```bash
npm run start:integrated
```

或者直接：
```bash
node scripts/构建与启动/integrated-launcher.js start
```

---

## 📍 服务地址

| 服务 | 地址 |
|------|------|
| **后端API** | http://127.0.0.1:8080 |
| **前端开发** | http://127.0.0.1:3000 |
| **Electron应用** | 自动连接前端 3000 端口 |
| 健康检查 | http://127.0.0.1:8080/health |
| API文档 | http://127.0.0.1:8080/docs |

---

## 🎯 启动流程

Integrated Launcher 会自动执行：

1. ✅ 检查必要文件
2. ✅ 清理端口占用（8080, 9020, 9021, 3000）
3. ✅ 启动后端服务（端口 8080）
4. ✅ 启动前端开发服务器（端口 3000）
5. ✅ 启动 Electron 应用（连接到 3000）

---

## 🎉 优势

1. **一键启动** - 无需分别启动各个服务
2. **自动端口管理** - 自动清理端口占用
3. **健康检查** - 自动等待服务就绪
4. **统一日志** - 所有服务日志在一个终端
5. **优雅退出** - Ctrl+C 自动关闭所有服务
6. **UTF-8编码** - 中文显示正常
7. **常用端口** - 8080和3000无权限问题

---

## 🐛 故障排除

### Electron 仍然白屏？

检查前端是否正常启动：
```bash
curl http://127.0.0.1:3000
```

### 后端无法连接？

检查后端健康状态：
```bash
curl http://127.0.0.1:8080/health
```

### 端口被占用？

手动清理端口：
```bash
npm run kill:ports
```

---

## 📝 其他启动方式

如果 integrated launcher 有问题，可以使用：

```bash
# 方式1：标准启动
npm run dev

# 方式2：管理员启动（如果有权限问题）
start-as-admin.bat
```

