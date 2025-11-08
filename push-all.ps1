# 同步推送到GitHub和Gitee
# 审查人: 叶维哲

Write-Host "📤 准备推送代码..." -ForegroundColor Cyan

# 检查是否有未提交的更改
$status = git status --porcelain
if ($status) {
    Write-Host "⚠️  有未提交的更改，先提交代码" -ForegroundColor Yellow
    
    # 显示更改
    git status
    
    # 询问是否提交
    $commit = Read-Host "是否提交这些更改？(y/n)"
    if ($commit -eq "y") {
        git add .
        $message = Read-Host "请输入提交信息"
        git commit -m "$message"
    } else {
        Write-Host "❌ 取消推送" -ForegroundColor Red
        exit 1
    }
}

# 推送到origin（同时推送到GitHub和Gitee）
Write-Host "`n📤 推送到GitHub和Gitee..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 推送成功！" -ForegroundColor Green
    Write-Host "`n已同步到：" -ForegroundColor Cyan
    Write-Host "  - GitHub: https://github.com/Wike-CHI/timao-douyin-live-manager" -ForegroundColor Green
    Write-Host "  - Gitee:  https://gitee.com/businsssksksss/timao-douyin-live-manager" -ForegroundColor Green
} else {
    Write-Host "❌ 推送失败，请检查错误信息" -ForegroundColor Red
    exit 1
}

