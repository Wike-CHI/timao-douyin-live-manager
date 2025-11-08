# ============================================
# Windows PowerShell 部署脚本
# ============================================
# 职责：从Windows环境部署到云服务器
# 审查人：叶维哲
# ============================================

param(
    [string]$Server = "",
    [string]$ServerPath = "/opt/timao-douyin",
    [switch]$CheckOnly,
    [switch]$Help
)

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colors = @{
        "Green" = "Green"
        "Red" = "Red"
        "Yellow" = "Yellow"
        "Blue" = "Cyan"
    }
    
    if ($colors.ContainsKey($Color)) {
        Write-Host $Message -ForegroundColor $colors[$Color]
    } else {
        Write-Host $Message
    }
}

# 显示帮助信息
function Show-Help {
    @"
====================================
Windows PowerShell 部署脚本
====================================

用法:
  .\deploy\deploy.ps1 [-Server <服务器地址>] [-ServerPath <部署路径>] [-CheckOnly] [-Help]

参数:
  -Server       服务器地址（格式：user@host，如 root@123.45.67.89）
  -ServerPath   部署路径（默认：/opt/timao-douyin）
  -CheckOnly    仅检查环境，不执行部署
  -Help         显示此帮助信息

示例:
  # 部署到服务器
  .\deploy\deploy.ps1 -Server "root@123.45.67.89"

  # 检查环境
  .\deploy\deploy.ps1 -Server "root@123.45.67.89" -CheckOnly

  # 使用自定义路径
  .\deploy\deploy.ps1 -Server "root@123.45.67.89" -ServerPath "/var/www/timao"

配置文件:
  deploy/upload_config.env - 服务器配置文件

前提条件:
  1. 已安装 Git for Windows（包含Git Bash和SSH）
  2. 已配置SSH密钥或密码登录
  3. 服务器已安装Docker和Docker Compose

====================================
"@
}

# 检查前提条件
function Test-Prerequisites {
    Write-ColorOutput "`n检查前提条件..." "Yellow"
    
    $allOk = $true
    
    # 检查Git
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-ColorOutput "✅ Git已安装" "Green"
    } else {
        Write-ColorOutput "❌ Git未安装，请安装 Git for Windows" "Red"
        Write-ColorOutput "   下载地址: https://git-scm.com/download/win" "Yellow"
        $allOk = $false
    }
    
    # 检查SSH
    if (Get-Command ssh -ErrorAction SilentlyContinue) {
        Write-ColorOutput "✅ SSH已安装" "Green"
    } else {
        Write-ColorOutput "❌ SSH未安装" "Red"
        $allOk = $false
    }
    
    # 检查项目目录
    if (Test-Path "docker-compose.full.yml") {
        Write-ColorOutput "✅ 项目目录正确" "Green"
    } else {
        Write-ColorOutput "❌ 请在项目根目录运行此脚本" "Red"
        $allOk = $false
    }
    
    return $allOk
}

# 测试服务器连接
function Test-ServerConnection {
    param([string]$ServerAddress)
    
    Write-ColorOutput "`n测试服务器连接..." "Yellow"
    
    $result = ssh -o ConnectTimeout=5 -o BatchMode=yes $ServerAddress "echo 'Connection successful'" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ 服务器连接成功" "Green"
        return $true
    } else {
        Write-ColorOutput "❌ 无法连接到服务器" "Red"
        Write-ColorOutput "   请检查：" "Yellow"
        Write-ColorOutput "   1. 服务器地址是否正确" "Yellow"
        Write-ColorOutput "   2. SSH密钥是否配置正确" "Yellow"
        Write-ColorOutput "   3. 服务器防火墙是否允许SSH连接" "Yellow"
        return $false
    }
}

# 检查服务器环境
function Test-ServerEnvironment {
    param([string]$ServerAddress)
    
    Write-ColorOutput "`n检查服务器环境..." "Yellow"
    
    # 检查Docker
    $dockerCheck = ssh $ServerAddress "command -v docker" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ Docker已安装" "Green"
    } else {
        Write-ColorOutput "❌ Docker未安装" "Red"
        Write-ColorOutput "   请先在服务器上安装Docker" "Yellow"
        return $false
    }
    
    # 检查Docker Compose
    $composeCheck = ssh $ServerAddress "command -v docker-compose" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ Docker Compose已安装" "Green"
    } else {
        Write-ColorOutput "❌ Docker Compose未安装" "Red"
        return $false
    }
    
    return $true
}

# 部署到服务器
function Deploy-ToServer {
    param(
        [string]$ServerAddress,
        [string]$DeployPath
    )
    
    Write-ColorOutput "`n开始部署..." "Blue"
    
    # 1. 提交代码（可选）
    Write-ColorOutput "`n[1/5] 检查Git状态..." "Yellow"
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-ColorOutput "⚠️  发现未提交的更改" "Yellow"
        $commit = Read-Host "是否提交更改？(y/n)"
        if ($commit -eq "y") {
            git add .
            $message = Read-Host "输入提交信息（留空使用默认）"
            if ([string]::IsNullOrEmpty($message)) {
                $message = "Deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            }
            git commit -m $message
            Write-ColorOutput "✅ 代码已提交" "Green"
        }
    } else {
        Write-ColorOutput "✅ 没有未提交的更改" "Green"
    }
    
    # 2. 推送到远程（如果有）
    Write-ColorOutput "`n[2/5] 推送代码到远程..." "Yellow"
    $pushResult = git push 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ 代码已推送到远程" "Green"
    } else {
        Write-ColorOutput "⚠️  推送失败或未配置远程仓库" "Yellow"
    }
    
    # 3. 在服务器上拉取代码
    Write-ColorOutput "`n[3/5] 更新服务器代码..." "Yellow"
    
    # 检查项目目录是否存在
    $dirExists = ssh $ServerAddress "test -d $DeployPath && echo 'exists'" 2>&1
    
    if ($dirExists -match "exists") {
        # 目录存在，拉取更新
        Write-ColorOutput "项目目录已存在，拉取更新..." "Blue"
        ssh $ServerAddress "cd $DeployPath && git pull"
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 代码已更新" "Green"
        } else {
            Write-ColorOutput "❌ 代码更新失败" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "❌ 项目目录不存在: $DeployPath" "Red"
        Write-ColorOutput "   请先在服务器上克隆项目：" "Yellow"
        Write-ColorOutput "   git clone <your-repo-url> $DeployPath" "Yellow"
        return $false
    }
    
    # 4. 配置环境（如果需要）
    Write-ColorOutput "`n[4/5] 检查环境配置..." "Yellow"
    $envExists = ssh $ServerAddress "test -f $DeployPath/server/.env && echo 'exists'" 2>&1
    
    if (-not ($envExists -match "exists")) {
        Write-ColorOutput "⚠️  环境配置文件不存在" "Yellow"
        Write-ColorOutput "   请手动配置环境变量：" "Yellow"
        Write-ColorOutput "   ssh $ServerAddress" "Yellow"
        Write-ColorOutput "   cd $DeployPath/server && cp env.production.template .env && vim .env" "Yellow"
        $continue = Read-Host "按回车继续（需要先配置环境）或输入 n 取消"
        if ($continue -eq "n") {
            return $false
        }
    } else {
        Write-ColorOutput "✅ 环境配置文件已存在" "Green"
    }
    
    # 5. 部署服务
    Write-ColorOutput "`n[5/5] 部署服务..." "Yellow"
    
    $deployCmd = @"
cd $DeployPath && docker-compose -f docker-compose.full.yml up -d --build
"@
    
    ssh $ServerAddress $deployCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ 服务部署成功" "Green"
        
        # 等待服务启动
        Write-ColorOutput "`n等待服务启动（30秒）..." "Yellow"
        Start-Sleep -Seconds 30
        
        # 验证部署
        Write-ColorOutput "`n验证部署..." "Yellow"
        ssh $ServerAddress "cd $DeployPath && docker-compose -f docker-compose.full.yml ps"
        
        return $true
    } else {
        Write-ColorOutput "❌ 服务部署失败" "Red"
        Write-ColorOutput "   查看日志：" "Yellow"
        ssh $ServerAddress "cd $DeployPath && docker-compose -f docker-compose.full.yml logs --tail=50"
        return $false
    }
}

# 显示部署信息
function Show-DeploymentInfo {
    param([string]$ServerAddress)
    
    $serverHost = $ServerAddress -replace "^.*@", ""
    
    Write-ColorOutput "`n====================================" "Blue"
    Write-ColorOutput "🎉 部署成功！" "Green"
    Write-ColorOutput "====================================" "Blue"
    Write-ColorOutput ""
    Write-ColorOutput "服务访问地址:" "Yellow"
    Write-ColorOutput "  前端: http://$serverHost" "Blue"
    Write-ColorOutput "  后端: http://$serverHost:11111" "Blue"
    Write-ColorOutput "  API文档: http://$serverHost:11111/docs" "Blue"
    Write-ColorOutput ""
    Write-ColorOutput "管理命令:" "Yellow"
    Write-ColorOutput "  查看日志: ssh $ServerAddress 'cd $ServerPath && docker-compose -f docker-compose.full.yml logs -f'" "Blue"
    Write-ColorOutput "  重启服务: ssh $ServerAddress 'cd $ServerPath && docker-compose -f docker-compose.full.yml restart'" "Blue"
    Write-ColorOutput "  停止服务: ssh $ServerAddress 'cd $ServerPath && docker-compose -f docker-compose.full.yml down'" "Blue"
    Write-ColorOutput ""
    Write-ColorOutput "====================================" "Blue"
}

# 主执行流程
function Main {
    # 显示帮助
    if ($Help) {
        Show-Help
        exit 0
    }
    
    Write-ColorOutput "====================================" "Blue"
    Write-ColorOutput "  Windows PowerShell 部署脚本" "Blue"
    Write-ColorOutput "====================================" "Blue"
    
    # 检查前提条件
    if (-not (Test-Prerequisites)) {
        Write-ColorOutput "`n❌ 前提条件检查失败" "Red"
        exit 1
    }
    
    # 获取服务器地址
    if ([string]::IsNullOrEmpty($Server)) {
        Write-ColorOutput "`n请输入服务器地址（格式：user@host）" "Yellow"
        $Server = Read-Host "服务器地址"
    }
    
    if ([string]::IsNullOrEmpty($Server)) {
        Write-ColorOutput "❌ 服务器地址不能为空" "Red"
        exit 1
    }
    
    # 测试连接
    if (-not (Test-ServerConnection -ServerAddress $Server)) {
        exit 1
    }
    
    # 检查服务器环境
    if (-not (Test-ServerEnvironment -ServerAddress $Server)) {
        exit 1
    }
    
    # 仅检查环境
    if ($CheckOnly) {
        Write-ColorOutput "`n✅ 环境检查完成" "Green"
        exit 0
    }
    
    # 确认部署
    Write-ColorOutput "`n准备部署到服务器：$Server" "Yellow"
    Write-ColorOutput "部署路径：$ServerPath" "Yellow"
    $confirm = Read-Host "确认部署？(y/n)"
    
    if ($confirm -ne "y") {
        Write-ColorOutput "❌ 部署已取消" "Yellow"
        exit 0
    }
    
    # 执行部署
    if (Deploy-ToServer -ServerAddress $Server -DeployPath $ServerPath) {
        Show-DeploymentInfo -ServerAddress $Server
        exit 0
    } else {
        Write-ColorOutput "`n❌ 部署失败" "Red"
        exit 1
    }
}

# 执行主流程
Main

