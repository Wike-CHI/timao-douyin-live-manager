# 前端端口更新说明

## 问题原因

**日期**: 2025-11-16

**问题**: 前端开发服务器（Vite）启动失败，报错：
```
Error: listen EACCES: permission denied 127.0.0.1:10065
```

**根本原因**: 
端口 `10065` 在 Windows 的保留端口范围 `10017-10116` 内。这是 Windows 或 Hyper-V 为动态端口分配保留的范围，普通应用程序无法使用。

可能是以下原因导致昨天能用今天不能用：
1. Windows 系统更新调整了保留端口范围
2. Hyper-V、Docker 或其他虚拟化服务启动后保留了这个范围
3. Windows 动态端口范围配置发生变化

## 解决方案

将前端开发端口从 `10065` 更改为 `10200`，避开 Windows 保留端口范围。

## 更改文件清单

### 1. 前端配置
- ✅ `electron/renderer/vite.config.ts` - Vite 服务器端口
- ✅ `electron/renderer/package.json` - npm dev 脚本端口
- ✅ `electron/renderer/src/services/apiConfig.ts` - 注释更新

### 2. Electron 主进程
- ✅ `electron/main.js` - 开发服务器 URL

### 3. 启动脚本
- ✅ `scripts/构建与启动/integrated-launcher.js` - 集成启动器端口配置

### 4. 根目录配置
- ✅ `package.json` - 多个脚本命令中的端口引用
  - `dev:electron`
  - `dev:step3`
  - `health:frontend`
  - `kill:ports`
  - `kill:frontend`
  - `quick:start`

## 端口配置总结

| 服务 | 旧端口 | 新端口 | 说明 |
|-----|--------|--------|------|
| 后端 API | 11111 | 11111 | 未变更 |
| 前端开发服务器 | 10065 | **10200** | ✅ 已更新 |
| WebSocket | 11111 | 11111 | 未变更（共用后端端口） |

## 验证步骤

1. **检查 Windows 保留端口**:
   ```powershell
   netsh interface ipv4 show excludedportrange protocol=tcp
   ```

2. **确认端口未占用**:
   ```powershell
   netstat -ano | findstr "10200"
   ```

3. **启动服务**:
   ```bash
   npm run start:integrated
   ```

4. **验证服务**:
   - 后端健康检查: http://127.0.0.1:11111/health
   - 前端开发服务器: http://127.0.0.1:10200

## 常见问题

### Q1: 为什么昨天能用今天不能用？
A: 可能是 Windows 更新或某个服务（Hyper-V、Docker）启动后保留了端口范围。

### Q2: 如何避免类似问题？
A: 使用高端口号（如 10200+）可以避开大多数系统保留范围。Windows 动态端口范围通常是 49152-65535，但也会保留一些低端口范围。

### Q3: 如果新端口也不能用怎么办？
A: 
1. 检查端口是否在保留范围内
2. 尝试其他端口（推荐 10200-10999 范围）
3. 以管理员权限运行（不推荐，只是临时方案）

### Q4: 需要重新安装依赖吗？
A: 不需要。这只是配置更改，不影响依赖包。

## 影响范围

### ✅ 已更新
- 所有开发启动脚本
- Electron 主进程配置
- 前端开发服务器配置
- 健康检查脚本
- 端口清理脚本

### ⚠️ 注意事项
- **admin-dashboard** 的配置未更改（它是独立的管理后台，使用单独的端口配置）
- 生产环境不受影响（生产环境不使用开发服务器）

## 测试清单

- [x] Vite 配置更新
- [x] package.json 脚本更新
- [x] Electron 主进程更新
- [x] 启动脚本更新
- [ ] 实际启动测试
- [ ] 功能验证测试

## 技术审查

**审查人**: 叶维哲  
**更新日期**: 2025-11-16  
**状态**: ✅ 配置已更新，等待测试验证

## 参考资料

- [Windows 动态端口范围文档](https://docs.microsoft.com/en-us/troubleshoot/windows-server/networking/default-dynamic-port-range-tcpip-chang)
- [Hyper-V 保留端口说明](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/reference/tlfs)

---

**下次启动前必读**: 如果遇到类似的端口权限问题，首先检查 Windows 保留端口范围：
```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

