#!/usr/bin/env python3
"""
网页快照演示脚本
展示如何使用screenshot_tool.py
"""

import os
import subprocess
import time
import sys

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")

    try:
        import selenium
        print("✅ selenium 已安装")
    except ImportError:
        print("❌ selenium 未安装")
        return False

    try:
        from playwright.sync_api import sync_playwright
        print("✅ playwright 已安装")
    except ImportError:
        print("❌ playwright 未安装")
        return False

    return True

def check_streamlit_running():
    """检查Streamlit应用是否运行"""
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        return response.status_code == 200
    except:
        return False

def demo_single_screenshot():
    """演示单个截图"""
    print("\n" + "="*50)
    print("📸 演示：单个网页快照")
    print("="*50)

    if not check_streamlit_running():
        print("⚠️  Streamlit应用未运行，请先启动:")
        print("   python run_streamlit.py")
        return

    print("✅ Streamlit应用正在运行")
    print("🎯 开始截图...")

    try:
        # 运行截图工具
        result = subprocess.run([
            sys.executable, "screenshot_tool.py",
            "--method", "auto",
            "--wait-time", "3",
            "--filename", "demo_single"
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ 截图成功！")
            print("📁 查看文件: ./screenshots/demo_single.png")
        else:
            print("❌ 截图失败:")
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ 截图超时")
    except FileNotFoundError:
        print("❌ 找不到 screenshot_tool.py")

def demo_batch_screenshots():
    """演示批量截图"""
    print("\n" + "="*50)
    print("🎬 演示：批量场景截图")
    print("="*50)

    if not check_streamlit_running():
        print("⚠️  Streamlit应用未运行，请先启动:")
        print("   python run_streamlit.py")
        return

    print("✅ Streamlit应用正在运行")
    print("🎯 开始批量截图...")
    print("这将截取5个不同场景的快照")

    try:
        # 运行批量截图
        result = subprocess.run([
            sys.executable, "screenshot_tool.py",
            "--batch",
            "--method", "auto",
            "--wait-time", "3"
        ], capture_output=True, text=True, timeout=120)  # 2分钟超时

        if result.returncode == 0:
            print("✅ 批量截图成功！")
            print("📁 查看文件: ./screenshots/scenario_*.png")
        else:
            print("❌ 批量截图失败:")
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ 批量截图超时")
    except FileNotFoundError:
        print("❌ 找不到 screenshot_tool.py")

def show_available_options():
    """显示可用选项"""
    print("\n" + "="*50)
    print("🎯 网页快照工具使用选项")
    print("="*50)
    print("1. 单个快照 (推荐入门)")
    print("2. 批量演示场景")
    print("3. 查看详细文档")
    print("4. 退出")
    print()

def interactive_demo():
    """交互式演示"""
    while True:
        show_available_options()

        try:
            choice = input("请选择 (1-4): ").strip()

            if choice == "1":
                demo_single_screenshot()
                input("\n按回车键继续...")
            elif choice == "2":
                demo_batch_screenshots()
                input("\n按回车键继续...")
            elif choice == "3":
                print("\n📖 查看详细文档: README_screenshot.md")
                input("\n按回车键继续...")
            elif choice == "4":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请重新输入")
                continue

        except KeyboardInterrupt:
            print("\n👋 用户取消")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            break

def main():
    """主函数"""
    print("🌟 RAG智能课程助教 - 网页快照演示")
    print("="*50)

    if not check_dependencies():
        print("\n❌ 缺少必要依赖，请安装:")
        print("   pip install selenium")
        print("   或")
        print("   pip install playwright && playwright install")
        return

    print("✅ 依赖检查通过")

    # 检查是否是自动化模式
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("🤖 自动化模式：运行完整演示")
        demo_single_screenshot()
        time.sleep(2)
        demo_batch_screenshots()
    else:
        # 交互式模式
        interactive_demo()

if __name__ == "__main__":
    main()
