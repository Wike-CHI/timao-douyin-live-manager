# 快速开始：打包Electron应用（连接公网后端）

## 🎯 一分钟快速上手

您的后端已部署在：`http://129.211.218.135`

现在只需3步，即可打包出连接到公网后端的桌面应用！

---

## 🚀 第一步：运行打包脚本

### Linux/macOS用户

```bash
# 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 运行打包脚本（首次使用）
./scripts/build-electron-production.sh
```

### Windows用户

```batch
REM 进入项目目录
cd C:\path\to\timao-douyin-live-manager

REM 双击运行或命令行执行
scripts\build-electron-production.bat
```

---

## ⏱️ 第二步：等待完成（约10-15分钟）

脚本会自动完成以下步骤：

1. ✅ 环境检查（Node.js、npm）
2. ✅ 清理旧构建
3. ✅ 配置生产环境（连接到 `http://129.211.218.135`）
4. ✅ 安装依赖
5. ✅ 构建前端
6. ✅ 打包Electron应用
7. ✅ 验证结果

**您无需任何操作，脚本会自动完成所有工作！**

---

## 📦 第三步：测试安装包

打包完成后，在 `dist/` 目录找到安装包：

### Windows

```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe    # 便携版（推荐）
└── TalkingCat-Setup-1.0.0-x64.exe       # 安装版
```

**测试方法**：

```bash
# 方法1：双击运行便携版
cd dist
start TalkingCat-Portable-1.0.0-x64.exe

# 方法2：或安装安装版
start TalkingCat-Setup-1.0.0-x64.exe
```

### macOS

```
dist/
└── TalkingCat-1.0.0-x64.dmg
```

**测试方法**：双击 `.dmg` 文件，拖动到应用程序文件夹

### Linux

```
dist/
├── TalkingCat-1.0.0-x64.AppImage
└── TalkingCat-1.0.0-x64.deb
```

**测试方法**：

```bash
# AppImage
chmod +x dist/TalkingCat-1.0.0-x64.AppImage
./dist/TalkingCat-1.0.0-x64.AppImage

# 或安装deb
sudo dpkg -i dist/TalkingCat-1.0.0-x64.deb
```

---

## 🔍 验证后端连接

打开应用后，验证是否连接到公网后端：

### 方法1：打开开发者工具（推荐）

1. 启动应用
2. 按 `Ctrl+Shift+I`（Windows/Linux）或 `Cmd+Option+I`（macOS）
3. 切换到 **Console** 标签
4. 输入以下命令：

```javascript
fetch('http://129.211.218.135/health')
  .then(r => r.json())
  .then(data => console.log('✅ 后端连接成功:', data))
  .catch(err => console.error('❌ 后端连接失败:', err))
```

5. 查看输出：
   - ✅ 成功：显示 `后端连接成功: { status: "healthy", ... }`
   - ❌ 失败：显示网络错误

### 方法2：使用应用功能

1. 在应用中尝试登录
2. 或访问任何需要后端数据的功能
3. 查看是否正常加载数据

---

## ⚡ 快速重新打包（代码修改后）

如果您只是修改了代码，无需重新安装依赖，使用快速构建：

```bash
# 快速构建（3-5分钟）
./scripts/quick-build.sh
```

**速度提升**：比完整构建快 **3-5倍** ⚡

---

## 🎨 自定义后端地址

如果需要更改后端地址，有3种方法：

### 方法1：修改脚本（永久）

编辑 `scripts/build-electron-production.sh`：

```bash
# 找到这一行（约第42行）
PRODUCTION_API_URL="http://129.211.218.135"

# 修改为你的后端地址
PRODUCTION_API_URL="https://your-domain.com"
```

### 方法2：环境变量（临时）

```bash
PRODUCTION_API_URL="https://your-domain.com" ./scripts/build-electron-production.sh
```

### 方法3：手动配置文件

创建 `electron/renderer/.env.production`：

```env
VITE_FASTAPI_URL=https://your-domain.com
VITE_STREAMCAP_URL=https://your-domain.com
VITE_DOUYIN_URL=https://your-domain.com
```

然后运行快速构建：

```bash
./scripts/quick-build.sh
```

---

## 🐛 遇到问题？

### 问题1：npm依赖安装慢

**解决**：使用国内镜像

```bash
npm config set registry https://registry.npmmirror.com
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
```

### 问题2：Electron下载超时

**解决**：设置镜像环境变量

```bash
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/
```

### 问题3：脚本权限不足

**解决**：添加执行权限

```bash
chmod +x scripts/build-electron-production.sh
chmod +x scripts/quick-build.sh
```

### 问题4：应用打包后无法连接后端

**排查步骤**：

1. **检查后端是否运行**
   ```bash
   curl http://129.211.218.135/health
   ```

2. **检查防火墙**
   ```bash
   # 确保80端口已开放
   sudo ufw status
   ```

3. **查看应用日志**
   - Windows: `%APPDATA%\提猫直播助手\logs\`
   - macOS: `~/Library/Application Support/提猫直播助手/logs/`
   - Linux: `~/.config/提猫直播助手/logs/`

---

## 📚 完整文档

详细的使用说明、故障排除和高级配置，请查看：

- **[Electron打包脚本使用指南](docs/Electron打包脚本使用指南.md)** - 完整教程
- **[脚本目录说明](scripts/README.md)** - 所有脚本索引
- **[Electron打包教程](docs/Electron打包教程.md)** - 手动打包步骤
- **[数据传输检查报告](docs/数据传输检查报告.md)** - 后端连接验证

---

## 🎉 成功了吗？

如果一切顺利，您现在应该有：

- ✅ 一个可运行的Electron桌面应用
- ✅ 应用已连接到公网后端（`http://129.211.218.135`）
- ✅ 可分发给最终用户的安装包

**恭喜！您已完成Electron应用的打包！🚀**

---

## 📞 需要帮助？

1. 查看 [完整使用指南](docs/Electron打包脚本使用指南.md)
2. 查看构建日志：`./scripts/build-electron-production.sh 2>&1 | tee build.log`
3. 提交Issue并附上错误日志

---

**最后更新**：2025-11-13  
**维护团队**：提猫直播助手团队

