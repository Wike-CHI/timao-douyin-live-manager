# 以管理员身份启动本地演示环境
# PowerShell 版本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "以管理员身份启动本地演示环境" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否以管理员身份运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️ 需要管理员权限！" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "正在请求管理员权限..." -ForegroundColor Yellow
    Write-Host "请在UAC对话框中选择'是'" -ForegroundColor Yellow
    Write-Host ""
    
    # 请求管理员权限并重新运行脚本
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Admin" -Verb RunAs
    exit
}

if ($args -contains "-Admin") {
    Write-Host "✅ 已获得管理员权限" -ForegroundColor Green
    Write-Host ""
    
    # 切换到脚本所在目录
    Set-Location $PSScriptRoot
    
    Write-Host "[1/3] 清理端口..." -ForegroundColor Blue
    npm run kill:ports
    Write-Host ""
    
    Write-Host "[2/3] 验证配置..." -ForegroundColor Blue
    Get-Content server\.env | Select-String "BACKEND_PORT"
    Write-Host ""
    
    Write-Host "[3/3] 启动服务..." -ForegroundColor Blue
    Write-Host "提示：按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
    Write-Host ""
    
    # 启动服务
    npm run dev
    
    Write-Host ""
    Write-Host "服务已停止。" -ForegroundColor Yellow
    Write-Host "按任意键关闭窗口..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

