# 快速修复SSH连接
# 审查人: 叶维哲

Write-Host "=== 快速修复SSH连接 ===" -ForegroundColor Cyan

# 1. 检查OpenSSH是否已安装
Write-Host "`n[1/4] 检查OpenSSH安装状态..." -ForegroundColor Yellow
$sshClient = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'

if ($sshClient.State -eq "Installed") {
    Write-Host "✅ OpenSSH客户端已安装" -ForegroundColor Green
} else {
    Write-Host "❌ OpenSSH客户端未安装，正在安装..." -ForegroundColor Yellow
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    Write-Host "✅ OpenSSH客户端安装完成" -ForegroundColor Green
}

# 2. 查找SSH安装位置
Write-Host "`n[2/4] 查找SSH安装位置..." -ForegroundColor Yellow
$sshPaths = @(
    "C:\Windows\System32\OpenSSH\ssh.exe",
    "C:\Program Files\Git\usr\bin\ssh.exe"
)

$foundSSH = $null
foreach ($path in $sshPaths) {
    if (Test-Path $path) {
        $foundSSH = $path
        Write-Host "✅ 找到SSH: $path" -ForegroundColor Green
        break
    }
}

if (-not $foundSSH) {
    Write-Host "❌ 未找到SSH可执行文件" -ForegroundColor Red
    Write-Host "请重启电脑后再试" -ForegroundColor Yellow
    exit 1
}

# 3. 检查PATH环境变量
Write-Host "`n[3/4] 检查PATH环境变量..." -ForegroundColor Yellow
$sshDir = Split-Path $foundSSH -Parent
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

if ($currentPath -like "*$sshDir*") {
    Write-Host "✅ SSH目录已在PATH中: $sshDir" -ForegroundColor Green
} else {
    Write-Host "⚠️  SSH目录不在PATH中，需要手动添加" -ForegroundColor Yellow
    Write-Host "SSH目录: $sshDir" -ForegroundColor Cyan
    Write-Host "请以管理员身份运行以下命令:" -ForegroundColor Yellow
    Write-Host "`$env:Path += `";$sshDir`"" -ForegroundColor Cyan
    Write-Host "[Environment]::SetEnvironmentVariable(`"Path`", `$env:Path + `";$sshDir`", `"Machine`")" -ForegroundColor Cyan
}

# 4. 测试SSH命令
Write-Host "`n[4/4] 测试SSH命令..." -ForegroundColor Yellow
Write-Host "请在新的PowerShell窗口中运行以下命令测试:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ssh -V" -ForegroundColor Green
Write-Host "  ssh root@129.211.218.135" -ForegroundColor Green
Write-Host ""

# 5. 提示下一步操作
Write-Host "=== 下一步操作 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  关闭当前PowerShell窗口" -ForegroundColor Yellow
Write-Host "2️⃣  重新打开PowerShell（无需管理员权限）" -ForegroundColor Yellow
Write-Host "3️⃣  运行: ssh -V" -ForegroundColor Yellow
Write-Host "4️⃣  如果仍然找不到SSH，请重启电脑" -ForegroundColor Yellow
Write-Host "5️⃣  重启后重新打开Cursor，尝试连接远程服务器" -ForegroundColor Yellow
Write-Host ""
Write-Host "✨ 如果SSH命令可用，在Cursor中:" -ForegroundColor Cyan
Write-Host "   按F1 → 输入 'Remote-SSH: Connect to Host' → 输入 'root@129.211.218.135'" -ForegroundColor Green
Write-Host ""

