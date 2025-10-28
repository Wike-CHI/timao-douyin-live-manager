## 中文显示
chcp 65001 >nul
## 第一步检测环境
echo 第一步检测环境...
echo.
## 检测Python
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python已安装
) else (
    echo ❌ 错误: 未找到Python
    echo 请先从 https://www.python.org/downloads/ 下载并安装Python 3.8+
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
#
