# 🪟 Windows 部署指南

> 在 Windows 环境下部署到云服务器

## 🎯 部署方式

Windows环境下有两种部署方式：

### 方式1：使用WSL（推荐）⭐

WSL (Windows Subsystem for Linux) 提供完整的Linux环境。

### 方式2：使用Git Bash

使用Git自带的Bash环境执行部署脚本。

---

## 📋 方式1：使用WSL（推荐）

### 安装WSL

```powershell
# PowerShell（管理员）
wsl --install
```

重启电脑后，WSL会自动完成安装。

### 安装必需工具

```bash
# 在WSL中执行
sudo apt update
sudo apt install -y rsync openssh-client curl
```

### 执行部署

```bash
# 1. 进入WSL
wsl

# 2. 进入项目目录（注意路径转换）
cd /mnt/d/gsxm/timao-douyin-live-manager

# 3. 配置服务器信息
cp deploy/upload_config.env.template deploy/upload_config.env
vim deploy/upload_config.env

# 4. 一键部署
chmod +x deploy/deploy_all.sh
./deploy/deploy_all.sh
```

---

## 📋 方式2：使用Git Bash

### 安装Git Bash

如果已安装Git，Git Bash已经自带。

下载地址：https://git-scm.com/download/win

### 配置服务器信息

```bash
# 在项目根目录右键 -> Git Bash Here

# 复制配置模板
cp deploy/upload_config.env.template deploy/upload_config.env

# 使用记事本编辑
notepad deploy/upload_config.env
```

**填写配置**：
```env
SERVER_HOST="你的服务器IP"
SERVER_USER="root"
SERVER_PATH="/opt/timao-douyin"
SSH_KEY_PATH="/c/Users/你的用户名/.ssh/id_rsa"  # Windows路径格式
```

### 执行部署

```bash
# 在Git Bash中
chmod +x deploy/deploy_all.sh
./deploy/deploy_all.sh
```

---

## 🔐 SSH密钥配置

### 生成SSH密钥（如果没有）

```bash
# WSL或Git Bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 一路回车，使用默认配置
```

### 上传公钥到服务器

```bash
# 方法1：使用ssh-copy-id（WSL）
ssh-copy-id root@你的服务器IP

# 方法2：手动复制（Git Bash或WSL）
cat ~/.ssh/id_rsa.pub | ssh root@你的服务器IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 测试连接

```bash
ssh root@你的服务器IP
```

如果能免密登录，配置成功！

---

## 🛠️ 在Cursor中使用Remote-SSH

### 安装Remote-SSH扩展

1. 打开Cursor
2. 按 `Ctrl+Shift+X` 打开扩展
3. 搜索 "Remote - SSH"
4. 点击安装

### 配置SSH连接

1. 按 `F1` 打开命令面板
2. 输入 "Remote-SSH: Open SSH Configuration File"
3. 选择配置文件（通常是 `C:\Users\你的用户名\.ssh\config`）

**添加配置**：
```
Host timao-server
    HostName 你的服务器IP
    User root
    Port 22
    IdentityFile C:\Users\你的用户名\.ssh\id_rsa
```

### 连接到服务器

1. 按 `F1` 打开命令面板
2. 输入 "Remote-SSH: Connect to Host"
3. 选择 "timao-server"
4. 等待连接完成

### 在服务器上工作

连接成功后：
1. 点击 "Open Folder"
2. 输入 `/opt/timao-douyin`
3. 开始在服务器上直接编辑和操作

---

## 📦 方式3：直接在服务器上部署

如果使用Remote-SSH连接到了服务器，可以直接在服务器上执行：

### 1. 克隆代码（首次）

```bash
# 在服务器上执行
cd /opt
git clone https://github.com/your-repo/timao-douyin-live-manager.git
cd timao-douyin-live-manager
```

### 2. 配置环境

```bash
# 配置后端环境
cd server
cp env.production.template .env
vim .env  # 填写数据库配置等
```

### 3. 部署服务

```bash
# 返回项目根目录
cd ..

# 构建并启动
docker-compose -f docker-compose.full.yml up -d --build
```

---

## 🔄 更新部署

### 从Windows更新

```bash
# Git Bash或WSL
./deploy/2_upload_code.sh      # 上传代码
./deploy/4_deploy_services.sh  # 重新部署
```

### 使用Remote-SSH更新

1. 连接到服务器
2. 在Cursor终端中：
```bash
cd /opt/timao-douyin
git pull
docker-compose -f docker-compose.full.yml up -d --build
```

---

## 🎨 推荐工作流程

### 本地开发 → 云服务器部署

```
┌──────────────────────┐
│   Windows (Cursor)    │
│   本地开发环境         │
└──────────┬───────────┘
           │
           │ Git Push
           ▼
┌──────────────────────┐
│   GitHub/GitLab      │
│   代码仓库            │
└──────────┬───────────┘
           │
           │ Git Pull
           ▼
┌──────────────────────┐
│   云服务器            │
│   生产环境            │
└──────────────────────┘
```

**推荐流程**：

1. **本地开发**（Windows + Cursor）
   ```bash
   # 开发和测试
   cd d:\gsxm\timao-douyin-live-manager
   # 修改代码...
   ```

2. **提交代码**
   ```bash
   git add .
   git commit -m "功能更新"
   git push origin main
   ```

3. **服务器部署**（通过Remote-SSH）
   ```bash
   # 连接到服务器
   cd /opt/timao-douyin
   git pull
   docker-compose -f docker-compose.full.yml up -d --build
   ```

---

## 🚀 快速命令速查

### 连接服务器
```bash
# PowerShell
ssh root@服务器IP

# 或使用Cursor的Remote-SSH
Ctrl+Shift+P -> Remote-SSH: Connect to Host
```

### 查看服务状态
```bash
ssh root@服务器IP 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml ps'
```

### 查看日志
```bash
ssh root@服务器IP 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml logs -f'
```

### 重启服务
```bash
ssh root@服务器IP 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml restart'
```

---

## 🔍 常见问题

### Q1: WSL和Git Bash哪个好？

**WSL（推荐）**：
- ✅ 完整的Linux环境
- ✅ 支持所有Linux命令
- ✅ 性能更好
- ❌ 需要Windows 10/11

**Git Bash**：
- ✅ 轻量，无需安装额外软件
- ✅ 兼容性好
- ❌ 功能相对有限

### Q2: 路径格式问题？

Windows路径需要转换：

```bash
# Windows路径
C:\Users\Admin\.ssh\id_rsa

# WSL路径
/mnt/c/Users/Admin/.ssh/id_rsa

# Git Bash路径
/c/Users/Admin/.ssh/id_rsa
```

### Q3: 权限问题？

```bash
# SSH密钥权限
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# 脚本执行权限
chmod +x deploy/*.sh
```

### Q4: 无法连接服务器？

检查：
1. 服务器IP是否正确
2. SSH端口是否开放（默认22）
3. 防火墙是否允许
4. SSH密钥是否正确

```bash
# 测试连接
ssh -v root@服务器IP
```

---

## 📝 配置示例

### deploy/upload_config.env（Windows）

```env
# 服务器配置
SERVER_HOST="123.45.67.89"
SERVER_USER="root"
SERVER_PORT="22"
SERVER_PATH="/opt/timao-douyin"

# SSH密钥路径（根据你的环境选择）
# WSL
SSH_KEY_PATH="/home/你的用户名/.ssh/id_rsa"

# Git Bash
# SSH_KEY_PATH="/c/Users/你的用户名/.ssh/id_rsa"

# 传输方式
TRANSFER_METHOD="rsync"
```

### SSH配置文件（Windows）

位置：`C:\Users\你的用户名\.ssh\config`

```
# 生产服务器
Host timao-prod
    HostName 123.45.67.89
    User root
    Port 22
    IdentityFile C:\Users\你的用户名\.ssh\id_rsa

# 测试服务器（如果有）
Host timao-test
    HostName 123.45.67.90
    User root
    Port 22
    IdentityFile C:\Users\你的用户名\.ssh\id_rsa
```

使用：
```bash
ssh timao-prod
```

---

## ✅ 推荐方案

综合考虑，推荐以下方案：

### 开发阶段
- 使用 **Cursor + WSL** 或 **Cursor + Remote-SSH**
- 本地开发，远程调试

### 部署阶段
- 使用 **Remote-SSH** 直接连接服务器
- 在服务器上 `git pull` + `docker-compose up -d --build`

### 优势
- ✅ 开发体验好
- ✅ 部署简单直接
- ✅ 不需要从Windows传输大量文件
- ✅ 充分利用Git的版本控制

---

## 🎯 一键部署脚本（Windows版）

创建 `deploy.ps1`（PowerShell脚本）：

```powershell
# deploy.ps1 - Windows PowerShell部署脚本
param(
    [string]$Server = "root@your-server-ip",
    [string]$Path = "/opt/timao-douyin"
)

Write-Host "🚀 开始部署到服务器..." -ForegroundColor Green

# 1. 提交代码
Write-Host "`n📝 提交代码..." -ForegroundColor Yellow
git add .
git commit -m "Deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git push

# 2. 服务器部署
Write-Host "`n🔄 更新服务器代码..." -ForegroundColor Yellow
ssh $Server "cd $Path && git pull"

# 3. 重新构建
Write-Host "`n🏗️  重新构建服务..." -ForegroundColor Yellow
ssh $Server "cd $Path && docker-compose -f docker-compose.full.yml up -d --build"

# 4. 验证部署
Write-Host "`n✅ 验证部署..." -ForegroundColor Yellow
ssh $Server "cd $Path && docker-compose -f docker-compose.full.yml ps"

Write-Host "`n🎉 部署完成！" -ForegroundColor Green
```

使用：
```powershell
.\deploy.ps1 -Server "root@123.45.67.89" -Path "/opt/timao-douyin"
```

---

**审查人**: 叶维哲  
**创建时间**: 2024-01-15  
**适用环境**: Windows 10/11

---

祝部署顺利！🎉

