#!/bin/bash

# Streamlit网页快照脚本 (Linux/Mac)
# 用于快速截取RAG智能课程助教系统的界面

echo "============================================"
echo "📸 RAG智能课程助教 - 网页快照工具"
echo "============================================"
echo

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装或不在PATH中"
    echo "请安装Python"
    exit 1
fi

echo "✅ Python环境检查通过"
echo

# 检查依赖
echo "🔍 检查依赖包..."

if ! python -c "import selenium" &> /dev/null; then
    echo "⚠️  selenium未安装，尝试安装..."
    if ! pip install selenium; then
        echo "❌ selenium安装失败"
        echo "请手动运行: pip install selenium"
        exit 1
    fi
fi

if ! python -c "from playwright.sync_api import sync_playwright" &> /dev/null; then
    echo "⚠️  playwright未安装，尝试安装..."
    if ! pip install playwright && playwright install; then
        echo "❌ playwright安装失败"
        echo "请手动运行: pip install playwright && playwright install"
        exit 1
    fi
fi

echo "✅ 依赖检查完成"
echo

# 选择截图模式
echo "请选择截图模式:"
echo "[1] 单个快照 (推荐)"
echo "[2] 批量演示场景"
echo "[3] 退出"
echo
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo
        echo "📸 单个快照模式"
        echo "请确保Streamlit应用已启动 (http://localhost:8501)"
        echo "按回车键开始截图..."
        read

        python screenshot_tool.py --method auto --wait-time 5
        ;;
    2)
        echo
        echo "🎬 批量演示模式"
        echo "这将截取5个不同场景的快照"
        echo "请确保Streamlit应用已启动 (http://localhost:8501)"
        echo "按回车键开始截图..."
        read

        python screenshot_tool.py --batch --method auto --wait-time 5
        ;;
    3)
        echo "👋 已取消"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo
echo "✅ 截图完成！"
echo "查看 screenshots/ 目录中的图片文件"
echo
