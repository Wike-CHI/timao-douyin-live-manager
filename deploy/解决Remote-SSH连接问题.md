# 🔧 解决 Cursor Remote-SSH 连接问题

> **错误**: `'ssh' 不是内部或外部命令`

## 🎯 问题分析

根据你的错误日志：

```
'ssh' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```

**原因**：Windows系统找不到SSH命令，需要安装或配置SSH客户端。

---

## ✅ 解决方案（3种方式）

### 方案1: 启用Windows自带的OpenSSH（推荐）⭐

Windows 10/11自带OpenSSH，只需启用即可。

#### 步骤1: 检查是否已安装

```powershell
# 在PowerShell（管理员）中运行
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'
```

#### 步骤2: 安装OpenSSH客户端

```powershell
# PowerShell（管理员）
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

#### 步骤3: 验证安装

```powershell
# 检查SSH版本
ssh -V

# 测试连接
ssh root@129.211.218.135
```

#### 步骤4: 重启Cursor

完全关闭Cursor并重新打开，然后重试连接。

---

### 方案2: 使用Git自带的SSH

如果你已安装Git for Windows，可以使用Git自带的SSH。

#### 步骤1: 找到Git的SSH路径

```powershell
# 通常在这个位置
C:\Program Files\Git\usr\bin\ssh.exe
```

#### 步骤2: 添加到PATH环境变量

**图形界面方式**：

1. 右键"此电脑" → 属性
2. 高级系统设置 → 环境变量
3. 系统变量中找到 `Path`
4. 点击编辑 → 新建
5. 添加：`C:\Program Files\Git\usr\bin`
6. 确定保存

**PowerShell方式**（管理员）：

```powershell
$gitPath = "C:\Program Files\Git\usr\bin"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$gitPath", "Machine")
```

#### 步骤3: 验证

```powershell
# 关闭并重新打开PowerShell
ssh -V
```

#### 步骤4: 重启Cursor

---

### 方案3: 配置Cursor使用完整SSH路径

如果不想修改系统PATH，可以配置Cursor直接使用SSH的完整路径。

#### 步骤1: 找到SSH位置

```powershell
# Git的SSH
C:\Program Files\Git\usr\bin\ssh.exe

# 或Windows OpenSSH（如果已安装）
C:\Windows\System32\OpenSSH\ssh.exe
```

#### 步骤2: 配置Cursor

1. 打开Cursor设置（Ctrl+,）
2. 搜索 "remote.SSH.path"
3. 设置为SSH的完整路径

**或者编辑settings.json**：

```json
{
  "remote.SSH.path": "C:\\Program Files\\Git\\usr\\bin\\ssh.exe"
}
```

#### 步骤3: 重启Cursor

---

## 🔑 配置SSH密钥（推荐）

连接成功后，建议配置SSH密钥以免密登录。

### 步骤1: 生成SSH密钥

```powershell
# 在PowerShell中
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# 一路回车，使用默认配置
```

### 步骤2: 复制公钥到服务器

```powershell
# 方法1: 手动复制
type $env:USERPROFILE\.ssh\id_rsa.pub

# 然后SSH到服务器，将公钥内容添加到 ~/.ssh/authorized_keys
```

```bash
# 在服务器上执行
mkdir -p ~/.ssh
echo "你的公钥内容" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 步骤3: 配置SSH Config

创建或编辑 `C:\Users\你的用户名\.ssh\config`：

```
Host timao-server
    HostName 129.211.218.135
    User root
    Port 22
    IdentityFile C:\Users\你的用户名\.ssh\id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 步骤4: 测试连接

```powershell
# 应该可以免密登录
ssh timao-server
```

---

## 🚀 在Cursor中使用Remote-SSH

### 步骤1: 连接到服务器

1. 按 `F1` 打开命令面板
2. 输入 `Remote-SSH: Connect to Host`
3. 选择 `timao-server` 或直接输入 `root@129.211.218.135`
4. 等待连接

### 步骤2: 打开项目目录

连接成功后：

1. 点击 "Open Folder"
2. 输入项目路径（如果已存在）或创建新目录
3. 开始工作

---

## 📋 完整操作步骤（推荐流程）

### 1. 安装OpenSSH

```powershell
# PowerShell（管理员）
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### 2. 生成SSH密钥

```powershell
ssh-keygen -t rsa -b 4096
```

### 3. 复制公钥到服务器

```powershell
# 查看公钥
type $env:USERPROFILE\.ssh\id_rsa.pub

# 首次密码登录服务器
ssh root@129.211.218.135

# 在服务器上添加公钥
mkdir -p ~/.ssh
vim ~/.ssh/authorized_keys
# 粘贴公钥内容，保存

# 设置权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 4. 配置SSH Config

```powershell
# 创建配置文件
notepad $env:USERPROFILE\.ssh\config
```

添加内容：

```
Host timao
    HostName 129.211.218.135
    User root
    IdentityFile C:\Users\你的用户名\.ssh\id_rsa
```

### 5. 测试连接

```powershell
ssh timao
# 应该可以免密登录
```

### 6. 在Cursor中连接

```
F1 → Remote-SSH: Connect to Host → 选择 timao
```

---

## 🔍 故障排查

### 问题1: SSH命令仍然找不到

```powershell
# 检查PATH
echo $env:Path

# 手动添加PATH（临时）
$env:Path += ";C:\Program Files\Git\usr\bin"

# 永久添加（管理员权限）
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Git\usr\bin", "Machine")
```

### 问题2: 连接超时

```powershell
# 测试网络连接
ping 129.211.218.135

# 测试SSH端口
Test-NetConnection -ComputerName 129.211.218.135 -Port 22
```

如果端口无法连接：
- 检查服务器防火墙
- 检查云服务器安全组规则

### 问题3: 权限被拒绝

```bash
# 在服务器上检查SSH配置
sudo vim /etc/ssh/sshd_config

# 确保以下配置启用
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# 重启SSH服务
sudo systemctl restart sshd
```

### 问题4: Cursor连接慢或失败

在SSH配置中添加优化选项：

```
Host timao
    HostName 129.211.218.135
    User root
    IdentityFile C:\Users\你的用户名\.ssh\id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    Compression yes
```

---

## 🎯 快速诊断脚本

创建 `test_ssh.ps1`：

```powershell
# SSH连接诊断脚本

Write-Host "=== SSH连接诊断 ===" -ForegroundColor Cyan

# 1. 检查SSH命令
Write-Host "`n[1/5] 检查SSH命令..." -ForegroundColor Yellow
if (Get-Command ssh -ErrorAction SilentlyContinue) {
    Write-Host "✅ SSH命令可用" -ForegroundColor Green
    ssh -V
} else {
    Write-Host "❌ SSH命令不可用" -ForegroundColor Red
    Write-Host "请安装OpenSSH或Git for Windows" -ForegroundColor Yellow
}

# 2. 检查SSH密钥
Write-Host "`n[2/5] 检查SSH密钥..." -ForegroundColor Yellow
$keyPath = "$env:USERPROFILE\.ssh\id_rsa"
if (Test-Path $keyPath) {
    Write-Host "✅ SSH密钥存在: $keyPath" -ForegroundColor Green
} else {
    Write-Host "⚠️  SSH密钥不存在" -ForegroundColor Yellow
    Write-Host "运行: ssh-keygen -t rsa -b 4096" -ForegroundColor Yellow
}

# 3. 检查网络连接
Write-Host "`n[3/5] 检查网络连接..." -ForegroundColor Yellow
if (Test-Connection -ComputerName 129.211.218.135 -Count 2 -Quiet) {
    Write-Host "✅ 服务器可达" -ForegroundColor Green
} else {
    Write-Host "❌ 服务器不可达" -ForegroundColor Red
}

# 4. 检查SSH端口
Write-Host "`n[4/5] 检查SSH端口..." -ForegroundColor Yellow
$connection = Test-NetConnection -ComputerName 129.211.218.135 -Port 22
if ($connection.TcpTestSucceeded) {
    Write-Host "✅ SSH端口(22)可访问" -ForegroundColor Green
} else {
    Write-Host "❌ SSH端口(22)不可访问" -ForegroundColor Red
}

# 5. 测试SSH连接
Write-Host "`n[5/5] 测试SSH连接..." -ForegroundColor Yellow
Write-Host "运行: ssh -o ConnectTimeout=5 root@129.211.218.135 'echo Connection OK'" -ForegroundColor Cyan
```

运行诊断：

```powershell
.\test_ssh.ps1
```

---

## ✅ 成功标志

当一切配置正确后，你应该能够：

```powershell
# 1. SSH命令可用
ssh -V
# OpenSSH_for_Windows_8.x...

# 2. 免密登录服务器
ssh timao
# 直接登录，无需密码

# 3. Cursor连接成功
# F1 → Remote-SSH: Connect to Host → timao
# 连接成功，可以打开远程文件夹
```

---

## 🎓 推荐后续步骤

连接成功后：

### 1. 克隆项目

```bash
cd /opt
git clone https://github.com/your-repo/timao-douyin-live-manager.git
cd timao-douyin-live-manager
```

### 2. 配置环境

```bash
cd server
cp env.production.template .env
vim .env  # 填写配置
```

### 3. 部署服务

```bash
cd ..
docker-compose -f docker-compose.full.yml up -d --build
```

### 4. 验证部署

```bash
docker-compose -f docker-compose.full.yml ps
curl http://localhost:11111/health
```

---

## 📞 仍然有问题？

### 方案A: 使用PowerShell脚本部署

如果Remote-SSH仍然有问题，可以使用我们的PowerShell部署脚本：

```powershell
.\deploy\deploy.ps1 -Server "root@129.211.218.135"
```

### 方案B: 使用Git Bash

```bash
# 在项目根目录右键 -> Git Bash Here
./deploy/deploy_all.sh
```

### 方案C: 手动SSH部署

```powershell
# 1. SSH登录
ssh root@129.211.218.135

# 2. 克隆项目
cd /opt
git clone <your-repo-url> timao-douyin-live-manager

# 3. 配置和部署
cd timao-douyin-live-manager
# 参考 DOCKER_FULL.md
```

---

**审查人**: 叶维哲  
**更新时间**: 2024-01-15

祝连接成功！🎉

