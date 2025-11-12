# 📦 快速打包 Electron 应用

## 🎯 目标
在 Linux 云服务器上打包 Windows 版 Electron 应用（不包含后端）

---

## ⚡ 快速开始

### 一键打包
```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
./scripts/构建与启动/build-electron-only.sh
```

### 下载打包文件
```bash
# 在本地 Windows 电脑上运行
scp user@129.211.218.135:/www/wwwroot/wwwroot/timao-douyin-live-manager/dist/*.exe .
```

---

## 📋 打包前检查

### 1. 确认后端服务运行
```bash
curl http://127.0.0.1:8181/health
# 应该返回：{"status":"ok"}
```

### 2. 确认前端配置
```bash
# 检查后端地址配置
grep -r "129.211.218.135:8181" electron/
```

### 3. 确认版本号
```bash
# 查看当前版本
cat package.json | grep version
```

---

## 🔧 配置后端地址

如果需要修改后端地址，编辑以下文件：

### 1. electron/main.js
```javascript
const BACKEND_URL = 'http://129.211.218.135:8181';
```

### 2. electron/renderer/src/config.js (如果存在)
```javascript
export const API_BASE_URL = 'http://129.211.218.135:8181';
```

### 3. config.json (如果存在)
```json
{
  "backend": {
    "url": "http://129.211.218.135:8181"
  }
}
```

---

## 🚀 打包步骤详解

### 步骤 1：清理旧文件
```bash
rm -rf dist
rm -rf electron/renderer/dist
```

### 步骤 2：构建前端
```bash
cd electron/renderer
npm run build
cd ../..
```

### 步骤 3：打包应用
```bash
npx electron-builder --win --x64
```

### 步骤 4：检查输出
```bash
ls -lh dist/*.exe
```

---

## 📥 输出文件

打包成功后会生成：
```
dist/
└── 提猫直播助手-1.0.0-x64.exe  # Windows 便携版
```

---

## 🧪 测试应用

### 1. 下载到本地
```bash
# 使用 scp
scp user@server:/path/to/dist/*.exe .

# 或使用 SFTP
sftp user@server
get /path/to/dist/*.exe
```

### 2. 在 Windows 上测试
1. 双击运行 .exe 文件
2. 检查是否能连接到后端
3. 测试登录功能
4. 测试直播录制功能

---

## ❌ 常见问题

### Q1: 打包失败 - 内存不足
```bash
# 解决：增加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Q2: 打包失败 - Wine 相关错误
```bash
# 解决：安装 Wine (在 Linux 上打包 Windows 应用需要)
# Ubuntu/Debian
sudo apt-get install wine

# CentOS/RHEL
sudo yum install wine
```

### Q3: 应用无法连接后端
```bash
# 检查后端地址配置
grep -r "BACKEND_URL" electron/

# 确认后端服务运行
curl http://129.211.218.135:8181/health
```

### Q4: 前端构建失败
```bash
# 重新安装依赖
cd electron/renderer
rm -rf node_modules
npm install
npm run build
```

---

## 📊 版本更新流程

### 1. 更新版本号
```bash
vi package.json
# 修改 "version": "1.0.1"
```

### 2. 打包新版本
```bash
./scripts/构建与启动/build-electron-only.sh
```

### 3. 上传新版本
```bash
# 上传到文件服务器
# 用户启动应用时会自动检查更新
```

---

## 📞 需要帮助？

查看详细文档：
- **完整指南**：`docs/guides/Electron打包指南.md`
- **问题排查**：`docs/runbooks/紧急修复指南.md`

---

## ✅ 快速检查清单

打包前：
- [ ] 后端服务运行正常
- [ ] 后端地址配置正确
- [ ] 版本号已更新
- [ ] 磁盘空间充足

打包后：
- [ ] dist/ 目录有 .exe 文件
- [ ] 文件大小合理（50-100MB）
- [ ] 在 Windows 上测试正常

---

**快速命令参考**：

```bash
# 一键打包
./scripts/构建与启动/build-electron-only.sh

# 查看版本
cat package.json | grep version

# 检查后端
curl http://127.0.0.1:8181/health

# 查看输出
ls -lh dist/

# 下载文件（在本地运行）
scp user@server:/www/wwwroot/wwwroot/timao-douyin-live-manager/dist/*.exe .
```
