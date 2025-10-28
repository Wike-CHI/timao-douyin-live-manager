# 提猫直播助手 - 一体化启动指南

## 🚀 快速启动

### 推荐方式（一键启动）

```bash
# 方式1: 使用批处理脚本（Windows）
npm run start:dev

# 方式2: 使用PowerShell脚本（推荐）
npm run start:dev:ps

# 方式3: 直接使用npm命令
npm run quick:start
```

### 高级启动选项

```bash
# 顺序启动模式（逐步启动各服务）
npm run start:dev:sequential

# 仅进行健康检查
npm run start:dev:check

# 详细健康检查
npm run health:detailed
```

## 📋 启动顺序说明

按照 `启动方法.md` 的要求，服务启动顺序为：

1. **后端 FastAPI 服务** (端口 9019)
2. **前端 Vite 开发服务器** (端口 10030)
3. **Electron 应用**

## 🛠️ 可用的启动脚本

### 基础启动脚本

| 命令 | 说明 |
|------|------|
| `npm run server` | 仅启动后端服务 |
| `npm run dev:renderer` | 仅启动前端开发服务器 |
| `npm run dev:electron` | 仅启动Electron应用 |

### 组合启动脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 并行启动所有服务（基础版） |
| `npm run dev:full` | 并行启动所有服务（完整版，带颜色标识） |
| `npm run quick:start` | 智能启动（等待健康检查后启动Electron） |

### 分步启动脚本

| 命令 | 说明 |
|------|------|
| `npm run dev:step1` | 第一步：启动后端服务 |
| `npm run dev:step2` | 第二步：启动前端服务 |
| `npm run dev:step3` | 第三步：启动Electron应用 |
| `npm run dev:sequential` | 按顺序执行所有步骤 |

### 健康检查脚本

| 命令 | 说明 |
|------|------|
| `npm run health:check` | 基础健康检查 |
| `npm run health:backend` | 检查后端服务 |
| `npm run health:frontend` | 检查前端服务 |
| `npm run health:all` | 检查所有服务 |
| `npm run health:detailed` | 详细健康检查（使用Node.js脚本） |

### 系统脚本

| 命令 | 说明 |
|------|------|
| `npm run start:dev` | Windows批处理启动脚本 |
| `npm run start:dev:ps` | PowerShell启动脚本 |
| `npm run start:dev:sequential` | PowerShell顺序启动 |
| `npm run start:dev:check` | PowerShell健康检查 |

## 🔧 配置说明

### 端口配置

- **后端 FastAPI**: `http://127.0.0.1:9019`
- **前端 Vite**: `http://127.0.0.1:10030`
- **健康检查**: `http://127.0.0.1:9019/health`

### 环境要求

1. **Node.js**: >= 16.0.0
2. **npm**: >= 8.0.0
3. **Python**: >= 3.8
4. **依赖安装**: 
   ```bash
   npm run setup:dev
   ```

## 🚨 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   netstat -ano | findstr :9019
   netstat -ano | findstr :10030
   ```

2. **依赖缺失**
   ```bash
   # 重新安装依赖
   npm run setup:dev
   ```

3. **服务启动失败**
   ```bash
   # 检查服务状态
   npm run health:detailed
   ```

### 调试模式

如果遇到问题，可以分别启动各个服务进行调试：

```bash
# 终端1: 启动后端
npm run server

# 终端2: 启动前端
npm run dev:renderer

# 终端3: 检查服务状态
npm run health:all

# 终端4: 启动Electron
npm run dev:electron
```

## 📝 注意事项

1. **启动顺序很重要**：必须先启动后端，再启动前端，最后启动Electron
2. **健康检查**：Electron启动前会自动等待后端和前端服务就绪
3. **环境变量**：确保项目根目录有 `.env` 文件
4. **防火墙**：确保端口9019和10030未被防火墙阻止

## 🎯 推荐工作流

### 开发环境

```bash
# 1. 安装依赖（首次运行）
npm run setup:dev

# 2. 启动开发环境
npm run start:dev:ps

# 3. 开发完成后，检查服务状态
npm run health:detailed
```

### 生产环境

```bash
# 1. 构建应用
npm run build

# 2. 启动生产服务
npm run server:prod
```

---

> 💡 **提示**: 推荐使用 `npm run start:dev:ps` 命令，它提供了最好的用户体验和错误处理。