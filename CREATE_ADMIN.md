# 创建管理员账号指南

## ✅ 已修复：脚本现在可以正常使用了！

## 方法1: 使用脚本（推荐）

### Windows (PowerShell)
```powershell
# 激活虚拟环境（如果使用）
.venv\Scripts\Activate.ps1

# 从项目根目录运行
python server\scripts\create_admin.py
```

### Linux/Mac
```bash
cd /path/to/timao-douyin-live-manager
python server/scripts/create_admin.py
```

### Linux/Mac
```bash
cd /path/to/timao-douyin-live-manager
python server/scripts/create_admin.py
```

### 硬编码管理员账号信息
- **用户名**: `tc1102Admin`
- **邮箱**: `tc1102admin@timao.com`
- **密码**: `xjystimao1115`
- **角色**: 超级管理员 (super_admin)

⚠️ **注意**: 此账号是硬编码在脚本中的，每次运行脚本都会确保此账号存在且密码正确。

⚠️ **重要**: 登录后请立即修改默认密码！

## 方法2: 直接注册（如果允许注册）

如果系统允许注册，你可以：
1. 先通过注册接口创建一个普通账号
2. 然后在数据库中手动将角色改为 `super_admin` 或 `admin`

## 方法3: 通过API创建（需要现有管理员）

如果已经有管理员账号，可以通过管理后台或API创建新管理员。

---

## CORS问题修复

已修复CORS配置，添加了 `http://localhost:3000` 和 `http://127.0.0.1:3000` 到允许列表。

**请重启后端服务使CORS配置生效**：

```bash
# 如果使用uvicorn
uvicorn server.app.main:app --reload --port 9019

# 或重启你的后端服务
```

## 验证步骤

1. 重启后端服务
2. 访问管理后台: http://localhost:3000
3. 使用默认账号登录:
   - 用户名: `admin`
   - 密码: `admin123456`

如果遇到问题，检查：
- 后端服务是否正常运行在 `http://127.0.0.1:9019`
- CORS配置是否已更新（需要重启服务）
- 数据库连接是否正常

