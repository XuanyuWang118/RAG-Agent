@echo off
REM Streamlit网页快照批处理脚本
REM 用于快速截取RAG智能课程助教系统的界面

echo ============================================
echo 📸 RAG智能课程助教 - 网页快照工具
echo ============================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    echo 请安装Python并添加到系统PATH
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 检查依赖
echo 🔍 检查依赖包...
python -c "import selenium" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  selenium未安装，尝试安装...
    pip install selenium
    if errorlevel 1 (
        echo ❌ selenium安装失败
        echo 请手动运行: pip install selenium
        pause
        exit /b 1
    )
)

python -c "from playwright.sync_api import sync_playwright" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  playwright未安装，尝试安装...
    pip install playwright
    playwright install
    if errorlevel 1 (
        echo ❌ playwright安装失败
        echo 请手动运行: pip install playwright && playwright install
        pause
        exit /b 1
    )
)

echo ✅ 依赖检查完成
echo.

REM 选择截图模式
echo 请选择截图模式:
echo [1] 单个快照 (推荐)
echo [2] 批量演示场景
echo [3] 退出
echo.
set /p choice="请输入选择 (1-3): "

if "%choice%"=="1" goto single
if "%choice%"=="2" goto batch
if "%choice%"=="3" goto exit

echo ❌ 无效选择
pause
exit /b 1

:single
echo.
echo 📸 单个快照模式
echo 请确保Streamlit应用已启动 (http://localhost:8501)
echo 按任意键开始截图...
pause >nul

python screenshot_tool.py --method auto --wait-time 5
goto end

:batch
echo.
echo 🎬 批量演示模式
echo 这将截取5个不同场景的快照
echo 请确保Streamlit应用已启动 (http://localhost:8501)
echo 按任意键开始截图...
pause >nul

python screenshot_tool.py --batch --method auto --wait-time 5
goto end

:exit
echo 👋 已取消
goto end

:end
echo.
echo ✅ 截图完成！
echo 查看 screenshots/ 目录中的图片文件
echo.
echo 按任意键退出...
pause >nul
