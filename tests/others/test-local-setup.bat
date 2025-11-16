@echo off
chcp 65001 >nul
echo ========================================
echo local-view 分支配置验证
echo ========================================
echo.

echo [1/6] 检查当前分支...
git branch | findstr "*" 
echo.

echo [2/6] 验证后端端口配置...
type server\.env | findstr "BACKEND_PORT"
echo.

echo [3/6] 验证数据库配置...
type server\.env | findstr "MYSQL_HOST"
echo.

echo [4/6] 检查文档文件...
if exist "docs\本地演示环境快速启动指南.md" (
    echo ✓ 本地启动指南存在
) else (
    echo ✗ 本地启动指南不存在
)
if exist "LOCAL_VIEW_SETUP_COMPLETE.md" (
    echo ✓ 配置完成文档存在
) else (
    echo ✗ 配置完成文档不存在
)
echo.

echo [5/6] 检查端口占用...
echo 检查 15000 端口（后端）...
netstat -ano | findstr ":15000" >nul
if %errorlevel% equ 0 (
    echo ⚠ 端口 15000 已被占用
) else (
    echo ✓ 端口 15000 空闲
)

echo 检查 10050 端口（前端）...
netstat -ano | findstr ":10050" >nul
if %errorlevel% equ 0 (
    echo ⚠ 端口 10050 已被占用
) else (
    echo ✓ 端口 10050 空闲
)
echo.

echo [6/6] 检查 npm 脚本...
echo 验证 package.json 中的端口配置...
type package.json | findstr "15000" >nul
if %errorlevel% equ 0 (
    echo ✓ package.json 包含端口 15000 配置
) else (
    echo ✗ package.json 不包含端口 15000 配置
)
echo.

echo ========================================
echo 验证完成！
echo ========================================
echo.
echo 💡 下一步：
echo    1. 如果端口被占用，运行：npm run kill:ports
echo    2. 启动本地环境：npm run dev
echo    3. 查看文档：docs\本地演示环境快速启动指南.md
echo.
pause

