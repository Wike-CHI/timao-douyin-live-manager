# ⚠️ 必须完全重启后端

## 问题
后端日志显示 OPTIONS 返回 400，但没有我们新增的日志，说明后端没有加载最新代码。

## 解决方案

### 1. 完全停止后端
在运行 `uvicorn` 的终端窗口：
- 按 `Ctrl + C` 停止服务
- 等待 5-10 秒，确保进程完全退出
- 如果进程没有退出，再按一次 `Ctrl + C`

### 2. 重新启动后端
```powershell
uvicorn server.app.main:app --reload --port 9019
```

### 3. 验证启动成功
启动后应该看到这些日志：

```
============================================================
🌐 CORS配置已加载
   允许的来源: 14 个
   - http://127.0.0.1:10030
   - http://localhost:10030
   ...
   - http://127.0.0.1:10050  ← 这个必须有
   - http://localhost:10050  ← 这个必须有
   ...
============================================================
```

### 4. 测试 OPTIONS 请求
在 PowerShell 中执行：

```powershell
curl.exe -X OPTIONS http://127.0.0.1:9019/api/auth/login `
  -H "Origin: http://localhost:10050" `
  -H "Access-Control-Request-Method: POST" `
  -H "Access-Control-Request-Headers: Content-Type" `
  -v
```

**预期结果**：
- 返回 `200 OK`
- 响应头包含 `Access-Control-Allow-Origin: http://localhost:10050`
- 后端日志显示：`🌐 [OPTIONS路由] 预检请求 - Origin: http://localhost:10050`

### 5. 浏览器测试
- 刷新管理后台页面 (F5)
- 清除浏览器缓存 (Ctrl+Shift+Delete)
- 尝试登录

---

## 如果仍然失败

### 检查端口占用
```powershell
netstat -ano | findstr :9019
```

如果端口被占用，杀掉进程：
```powershell
taskkill /PID <进程ID> /F
```

### 使用不同端口
```powershell
uvicorn server.app.main:app --reload --port 9020
```

然后修改 `admin-dashboard/vite.config.ts` 中的 proxy target 为 `http://127.0.0.1:9020`。

---

## 管理员账号
- 用户名：`tc1102Admin`
- 密码：`xjystimao1115`

