# ⚡ 权限问题快速修复

## 🎯 问题原因

Windows 系统默认不允许普通用户绑定某些端口（即使是 >1024 的端口），需要管理员权限。

---

## ✅ 立即解决（3种方法）

### 方法1：使用管理员脚本（最简单） ⭐

1. **关闭当前 PowerShell 终端**（按 Ctrl+C）
2. **双击运行**：`start-as-admin.bat`
3. 在 UAC 对话框点击"是"
4. 等待服务启动完成

### 方法2：重新打开管理员 PowerShell ⚡

1. **关闭当前 PowerShell**
2. **右键点击 PowerShell 图标** → 选择 **"以管理员身份运行"**
3. 切换到项目目录：
   ```powershell
   cd d:\gsxm\timao-douyin-live-manager
   ```
4. 启动服务：
   ```powershell
   npm run dev
   ```

### 方法3：一次性配置防火墙（永久解决） 🔧

**以管理员身份**打开 PowerShell，执行：

```powershell
# 允许 Node.js 绑定端口（只需执行一次）
New-NetFirewallRule -DisplayName "Timao Dev Server" -Direction Inbound -Program "C:\Program Files\nodejs\node.exe" -Action Allow

# 或针对具体端口
New-NetFirewallRule -DisplayName "Timao Port 10050" -Direction Inbound -Protocol TCP -LocalPort 10050 -Action Allow
```

配置后，以后可以**正常启动，不需要管理员权限**。

---

## 🚀 推荐流程

```bash
# 1. 关闭当前终端（Ctrl+C）
# 2. 双击运行
start-as-admin.bat

# 等待看到：
# [SERVICES] [OK] 服务 fastapi_main 已启动
# [RENDERER] ➜ Local: http://127.0.0.1:10050/
# [ELECTRON] Electron app started
```

---

## 🔍 验证成功

启动成功后，新开终端检查：

```bash
npm run health:all
```

应该看到：
```
✅ 后端：http://127.0.0.1:15000/health
✅ 前端：http://127.0.0.1:10050
```

---

## ❓ 为什么需要管理员权限？

虽然 10050 > 1024（通常不需要管理员权限），但以下情况仍可能需要：

1. **Windows Defender 防火墙**阻止
2. **杀毒软件**（如 360、腾讯管家）拦截
3. **企业安全策略**限制
4. **之前的进程**未完全释放端口

---

## 🎯 立即行动

**关闭当前终端 → 双击 `start-as-admin.bat` → 完成！** ✨

