# 🚀 Pake 使用指南

**遵循：奥卡姆剃刀 + KISS 原则**

> Pake 是 Electron 的轻量级替代品，用 Rust 编写，体积更小、性能更好

---

## 📋 什么是 Pake？

**Pake** 是一个用 Rust 编写的工具，可以将网页打包成桌面应用：
- ✅ 体积小（比 Electron 小 10-20 倍）
- ✅ 性能好（启动快、内存占用低）
- ✅ 简单易用（一条命令打包）

---

## 🎯 安装 Pake

### Windows

```powershell
# 使用 Scoop 安装（推荐）
scoop install pake

# 或使用 Cargo（需要先安装 Rust）
cargo install pake-cli
```

### Linux/Mac

```bash
# 使用 Homebrew (Mac)
brew install pake

# 或使用 Cargo
cargo install pake-cli
```

---

## 🚀 基本用法

### 最简单的用法

```bash
# 将网页打包成桌面应用
pake https://your-website.com
```

### 完整参数

```bash
pake <url> [options]

# 示例：打包你的后端管理界面
pake http://129.211.218.135:11111 \
  --name "提猫直播助手" \
  --icon icon.png \
  --width 1200 \
  --height 800
```

### 常用参数

```bash
--name <name>          # 应用名称
--icon <path>          # 图标路径
--width <number>       # 窗口宽度（默认 1200）
--height <number>      # 窗口高度（默认 800）
--fullscreen           # 全屏启动
--transparent          # 透明窗口
--resizable            # 可调整大小
--user-agent <ua>      # 自定义 User-Agent
```

---

## 📦 打包你的项目

### 方案1：打包前端管理界面（推荐）

如果你的前端已经部署到服务器：

```bash
# 打包前端管理界面
pake http://129.211.218.135:11111 \
  --name "提猫直播助手" \
  --icon electron/renderer/src/assets/icon.png \
  --width 1200 \
  --height 800 \
  --output dist/pake
```

### 方案2：打包本地开发服务器

```bash
# 先启动本地开发服务器
npm run dev:renderer

# 然后打包
pake http://127.0.0.1:10050 \
  --name "提猫直播助手-开发版" \
  --icon electron/renderer/src/assets/icon.png
```

---

## ⚙️ 高级配置

### 创建配置文件 `pake.json`

```json
{
  "name": "提猫直播助手",
  "url": "http://129.211.218.135:11111",
  "icon": "electron/renderer/src/assets/icon.png",
  "width": 1200,
  "height": 800,
  "resizable": true,
  "transparent": false,
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

然后运行：

```bash
pake --config pake.json
```

---

## 🔄 与 Electron 对比

| 特性 | Pake | Electron |
|------|------|----------|
| 体积 | ~5-10 MB | ~100-200 MB |
| 启动速度 | 快 | 较慢 |
| 内存占用 | 低 | 高 |
| 功能 | 基础（网页打包） | 完整（Node.js 集成） |
| 适用场景 | 简单网页应用 | 复杂桌面应用 |

---

## 📝 适用场景

### ✅ 适合用 Pake

- 前端是纯网页应用
- 后端已部署到服务器
- 只需要简单的桌面窗口
- 不需要 Node.js 集成功能

### ❌ 不适合用 Pake

- 需要本地文件系统访问
- 需要启动本地后端服务
- 需要复杂的桌面集成功能
- 需要 Node.js 模块支持

---

## 🎯 针对你的项目

### 如果后端在服务器（129.211.218.135）

**推荐使用 Pake**，因为：
- ✅ 后端已部署，前端只是网页
- ✅ 不需要打包后端代码
- ✅ 体积小、启动快

**打包命令：**

```bash
pake http://129.211.218.135:11111 \
  --name "提猫直播助手" \
  --icon electron/renderer/src/assets/icon.png \
  --width 1200 \
  --height 800 \
  --output dist/pake
```

### 如果需要本地后端

**继续使用 Electron**，因为：
- ❌ Pake 无法启动本地 Python 后端
- ❌ Pake 无法集成 Node.js 模块
- ❌ 需要完整的 Electron 功能

---

## 🚀 快速开始

### 1. 安装 Pake

```bash
# Windows (PowerShell)
scoop install pake

# Mac
brew install pake

# Linux
cargo install pake-cli
```

### 2. 打包应用

```bash
pake http://129.211.218.135:11111 \
  --name "提猫直播助手" \
  --icon electron/renderer/src/assets/icon.png
```

### 3. 运行打包后的应用

打包完成后，会在当前目录生成可执行文件，直接运行即可。

---

## 📚 更多资源

- Pake 官方文档：https://github.com/tw93/pake
- Pake 示例：https://github.com/tw93/pake/tree/master/examples

---

## 💡 总结

**Pake 适合：**
- 简单的网页应用打包
- 后端已部署的场景
- 追求小体积和快速启动

**Electron 适合：**
- 需要本地功能集成
- 需要启动本地服务
- 需要完整的桌面应用功能

**对于你的项目：**
- 如果后端在服务器 → **用 Pake**（更简单）
- 如果需要本地后端 → **用 Electron**（功能完整）

