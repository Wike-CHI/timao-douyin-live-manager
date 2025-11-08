# setup-ssh-alias.ps1
# 为Cursor终端配置SSH快捷命令

Write-Host "📝 配置SSH快捷命令..." -ForegroundColor Green

# 获取PowerShell配置文件路径
$profilePath = $PROFILE

# 检查配置文件是否存在
if (!(Test-Path $profilePath)) {
    Write-Host "创建PowerShell配置文件..." -ForegroundColor Yellow
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
}

# 添加SSH别名到配置文件
$aliasContent = @"

# ========== 云服务器SSH快捷命令 ==========
function Connect-TimaoServer {
    Write-Host "🚀 连接到淘淘云服务器..." -ForegroundColor Green
    ssh timao-server
}

# 快捷命令别名
Set-Alias -Name server -Value Connect-TimaoServer
Set-Alias -Name timao -Value Connect-TimaoServer

Write-Host "✅ SSH快捷命令已加载 (使用 'server' 或 'timao' 快速连接)" -ForegroundColor Green
# ==========================================

"@

# 检查是否已经添加过
$currentContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($currentContent -notlike "*Connect-TimaoServer*") {
    Add-Content -Path $profilePath -Value $aliasContent
    Write-Host "✅ 快捷命令已添加到PowerShell配置文件" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 使用方法：" -ForegroundColor Cyan
    Write-Host "   1. 重启Cursor终端或运行: . `$PROFILE" -ForegroundColor White
    Write-Host "   2. 输入 'server' 或 'timao' 即可快速连接" -ForegroundColor White
    Write-Host ""
    Write-Host "配置文件路径: $profilePath" -ForegroundColor Gray
} else {
    Write-Host "⚠️  快捷命令已经存在，无需重复添加" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 配置完成！重启Cursor终端后生效" -ForegroundColor Green

