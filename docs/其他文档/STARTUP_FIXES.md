# 🔧 启动问题修复说明

> **修复时间**：2025-01-15  
> **分支**：local-view  
> **审查人**：叶维哲

---

## 🐛 发现的问题

### 问题1：后端端口配置未生效

**症状**：
```
[SERVICES] 端口 11111 已被占用，尝试查找替代端口...
[SERVICES] 为服务 fastapi_main 分配新端口: 11112
```

**原因**：
- `service_launcher.py` 没有加载 `.env` 文件
- `os.getenv("BACKEND_PORT", "11111")` 返回默认值 11111
- 实际配置 `BACKEND_PORT=15000` 未被读取

**修复方案**：
```python
# 在 service_launcher.py 开头添加
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")
load_dotenv(project_root / "server" / ".env")
```

### 问题2：Python 无法导入 server 模块

**症状**：
```
ModuleNotFoundError: No module named 'server'
```

**原因**：
- `service_launcher.py` 的 `base_dir` 指向错误
- 原来：`Path(__file__).parent.parent` → `scripts/` 目录
- Python 从 `scripts/` 目录启动，找不到 `server` 模块

**修复方案**：
```python
# 修正 base_dir 指向项目根目录
self.base_dir = Path(__file__).parent.parent.parent
# scripts/构建与启动/ -> scripts -> 项目根目录
```

### 问题3：前端端口权限错误

**症状**：
```
[RENDERER] Error: listen EACCES: permission denied 127.0.0.1:10050
```

**可能原因**：
1. Windows 防火墙阻止
2. 需要管理员权限
3. 端口被安全软件拦截
4. Node.js 权限不足

**修复方案**：
参见下方"解决前端权限问题"部分

---

## ✅ 已修复的问题

### 1. 后端端口配置 ✅

- ✅ 添加 `python-dotenv` 支持
- ✅ 自动加载 `.env` 文件
- ✅ 正确读取 `BACKEND_PORT=15000`

### 2. Python 模块导入 ✅

- ✅ 修正 `base_dir` 指向项目根目录
- ✅ 确保 Python 能正确导入 `server` 模块

---

## 🔨 解决前端权限问题

### 方法1：以管理员身份运行（推荐）

#### Windows PowerShell：

```powershell
# 右键点击 PowerShell，选择"以管理员身份运行"
cd d:\gsxm\timao-douyin-live-manager
npm run dev
```

#### Windows CMD：

```cmd
# 右键点击 CMD，选择"以管理员身份运行"
cd d:\gsxm\timao-douyin-live-manager
npm run dev
```

### 方法2：配置防火墙规则

```powershell
# 以管理员身份运行 PowerShell
# 允许 Node.js 访问端口
New-NetFirewallRule -DisplayName "Node.js Dev Server" -Direction Inbound -Protocol TCP -LocalPort 10050 -Action Allow
```

### 方法3：修改 hosts 文件（可选）

如果上述方法都不行，可以尝试：

1. 以管理员身份打开记事本
2. 打开文件：`C:\Windows\System32\drivers\etc\hosts`
3. 添加：`127.0.0.1 localhost`
4. 保存并重启电脑

### 方法4：更换端口（临时方案）

如果 10050 端口有问题，可以临时更换端口：

**修改 `electron/renderer/vite.config.ts`：**

```typescript
export default defineConfig({
  server: {
    host: '127.0.0.1',
    port: 10060, // 改为 10060 或其他端口
    strictPort: true,
  },
  // ...
});
```

**同时修改 `package.json`：**

```json
{
  "scripts": {
    "health:frontend": "curl -f http://127.0.0.1:10060",
    "kill:frontend": "node scripts/诊断与排障/kill-port.js 10060",
    // ...
  }
}
```

---

## 🚀 修复后的启动流程

### 1. 验证修复

```bash
# 运行配置验证脚本
cmd /c test-local-setup.bat
```

**预期输出**：
```
[2/6] 验证后端端口配置...
BACKEND_PORT=15000  ✓

[6/6] 检查 npm 脚本...
✓ package.json 包含端口 15000 配置
```

### 2. 清理端口

```bash
npm run kill:ports
```

### 3. 以管理员身份启动

```powershell
# 右键 PowerShell，选择"以管理员身份运行"
cd d:\gsxm\timao-douyin-live-manager
npm run dev
```

### 4. 验证服务启动

```bash
# 新开终端，检查健康状态
npm run health:all
```

**预期输出**：
```
✅ 后端服务正常：http://127.0.0.1:15000/health
✅ 前端服务正常：http://127.0.0.1:10050
```

---

## 📝 修复检查清单

- [x] 修复 service_launcher.py 加载 .env 文件
- [x] 修正 base_dir 指向项目根目录
- [x] 提交代码到 local-view 分支
- [ ] 以管理员身份运行 PowerShell
- [ ] 成功启动后端服务（端口15000）
- [ ] 成功启动前端服务（端口10050）
- [ ] 成功启动 Electron 应用
- [ ] 验证健康检查通过

---

## 🐛 故障排查

### 如果后端仍然使用 11111 端口

**检查**：
```bash
# 1. 确认 .env 文件存在
type server\.env | findstr "BACKEND_PORT"

# 2. 确认 python-dotenv 已安装
pip show python-dotenv

# 3. 检查日志
tail -f logs/service_manager.log
```

### 如果前端权限错误持续

**尝试**：
1. 关闭所有杀毒软件和防火墙（临时）
2. 以管理员身份运行
3. 更换端口（如10060）
4. 检查是否有其他Node.js进程占用端口

```powershell
# 查找 Node.js 进程
Get-Process node
```

### 如果 Python 模块导入失败

**检查**：
```bash
# 1. 确认在项目根目录
cd d:\gsxm\timao-douyin-live-manager

# 2. 确认 server 目录存在
dir server\app\main.py

# 3. 手动测试导入
python -c "import server.app.main; print('OK')"
```

---

## 📚 相关文档

- [本地演示环境快速启动指南](docs/本地演示环境快速启动指南.md)
- [配置完成总结](LOCAL_VIEW_SETUP_COMPLETE.md)
- [端口配置说明](docs/部署与运维指南/PORT_CONFIGURATION.md)

---

## 🆘 紧急联系

如果上述方法都无法解决问题，请：

1. 检查日志：`logs/service_manager.log`
2. 查看错误详情并截图
3. 联系技术负责人：叶维哲

---

**修复完成时间**：2025-01-15  
**下一步**：以管理员身份运行 `npm run dev` 🚀

