@echo off
REM Creeper 项目快速启动脚本 (Windows)
REM 用途: 自动创建虚拟环境并安装依赖

echo ======================================
echo   Creeper 项目初始化脚本 (Windows)
echo ======================================
echo.

REM 检查 Python 版本
echo 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python,请先安装 Python 3.8+
    pause
    exit /b 1
)
python --version
echo.

REM 创建虚拟环境
if exist venv (
    echo 虚拟环境已存在,跳过创建
) else (
    echo 创建虚拟环境...
    python -m venv venv
    echo 虚拟环境创建完成
)
echo.

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat
echo 虚拟环境已激活
echo.

REM 升级 pip
echo 升级 pip...
python -m pip install --upgrade pip -q
echo pip 升级完成
echo.

REM 安装依赖
echo 安装项目依赖...
pip install -r requirements.txt -q
echo 依赖安装完成
echo.

REM 安装 Playwright 浏览器
echo 安装 Playwright 浏览器...
playwright install chromium
echo Playwright 浏览器安装完成
echo.

REM 复制配置文件
if not exist .env (
    echo 创建配置文件...
    copy .env.example .env
    echo 配置文件已创建: .env
    echo (可根据需要编辑此文件)
) else (
    echo 配置文件已存在,跳过创建
)
echo.

echo ======================================
echo   初始化完成!
echo ======================================
echo.
echo 下一步操作:
echo 1. 激活虚拟环境:
echo    venv\Scripts\activate
echo.
echo 2. 运行爬虫:
echo    python creeper.py input.md
echo.
echo 3. 查看帮助:
echo    python creeper.py --help
echo.
echo 4. 退出虚拟环境:
echo    deactivate
echo.
pause
