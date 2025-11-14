# Windows 打包脚本使用说明

**审查人**: 叶维哲

## 🚀 快速使用

### 在项目根目录运行以下命令之一：

```bash
# 方法1: 完整打包（推荐首次使用）
npm run package:windows

# 方法2: PowerShell版本（更好的视觉效果）
npm run package:windows:ps

# 方法3: 快速打包（依赖已安装时）
npm run package:windows:quick
```

## 📦 输出结果

打包完成后，在 `dist/` 目录下会生成：

- `TalkingCat-Portable-1.0.0-x64.exe` - 便携版（免安装）
- `TalkingCat-Setup-1.0.0-x64.exe` - 安装包版本

## ✅ 测试验证

运行自动测试验证环境配置：

```bash
node scripts/检查与校验/test-package-windows.js
```

## 📖 完整文档

详细使用说明请查看：`docs/Windows打包指南.md`

## ⚡ 脚本说明

| 脚本 | 说明 | 使用场景 |
|------|------|----------|
| `package-windows.bat` | 完整打包流程 | 首次打包或依赖更新后 |
| `package-windows.ps1` | PowerShell版本 | 喜欢彩色输出的用户 |
| `package-windows-quick.bat` | 快速打包 | 频繁重新打包时 |

## 🔧 常见问题

### 打包失败？

1. 确保 Node.js >= 16.0.0
2. 运行 `npm install` 安装依赖
3. 检查 `electron/renderer/src/assets/icon.ico` 文件是否存在
4. 查看完整文档了解更多解决方案

---

**提示**: 首次打包需要下载 Electron 二进制文件，可能需要 10-30 分钟。

