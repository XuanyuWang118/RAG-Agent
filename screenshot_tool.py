#!/usr/bin/env python3
"""
Streamlit网页快照工具
用于截取和保存Streamlit应用的网页界面
"""

import os
import time
import json
from datetime import datetime
from typing import Optional
import subprocess
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class StreamlitScreenshot:
    """Streamlit网页快照工具"""

    def __init__(self, url: str = "http://localhost:8501", output_dir: str = "./screenshots"):
        self.url = url
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def take_screenshot_selenium(self, filename: Optional[str] = None,
                                wait_time: int = 3,
                                full_page: bool = True) -> str:
        """
        使用Selenium + Chrome WebDriver截图

        Args:
            filename: 输出文件名（不含扩展名）
            wait_time: 等待页面加载的时间（秒）
            full_page: 是否截取全页

        Returns:
            截图文件路径
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("需要安装selenium: pip install selenium")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"streamlit_screenshot_{timestamp}"

        output_path = os.path.join(self.output_dir, f"{filename}.png")

        print(f"📸 使用Selenium截取网页快照...")

        # Chrome选项设置
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url)

            # 等待页面加载
            print(f"⏳ 等待 {wait_time} 秒页面加载...")
            time.sleep(wait_time)

            # 等待Streamlit应用加载完成
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "stApp"))
                )
                print("✅ Streamlit应用已加载")
            except:
                print("⚠️  等待Streamlit加载超时，继续截图")

            # 截取全页或可见区域
            if full_page:
                # 获取页面总高度
                total_height = driver.execute_script("return document.body.scrollHeight")
                driver.set_window_size(1920, total_height)
                time.sleep(1)  # 等待页面重新渲染

            # 截图
            driver.save_screenshot(output_path)
            print(f"✅ 截图已保存: {output_path}")

            return output_path

        except Exception as e:
            print(f"❌ Selenium截图失败: {e}")
            raise
        finally:
            if driver:
                driver.quit()

    def take_screenshot_playwright(self, filename: Optional[str] = None,
                                  wait_time: int = 3,
                                  full_page: bool = True) -> str:
        """
        使用Playwright截图

        Args:
            filename: 输出文件名（不含扩展名）
            wait_time: 等待页面加载的时间（秒）
            full_page: 是否截取全页

        Returns:
            截图文件路径
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("需要安装playwright: pip install playwright && playwright install")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"streamlit_screenshot_{timestamp}"

        output_path = os.path.join(self.output_dir, f"{filename}.png")

        print(f"📸 使用Playwright截取网页快照...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            try:
                page.goto(self.url)

                # 等待页面加载
                print(f"⏳ 等待 {wait_time} 秒页面加载...")
                page.wait_for_timeout(wait_time * 1000)

                # 等待Streamlit应用加载完成
                try:
                    page.wait_for_selector(".stApp", timeout=10000)
                    print("✅ Streamlit应用已加载")
                except:
                    print("⚠️  等待Streamlit加载超时，继续截图")

                # 设置全页截图
                screenshot_options = {
                    "path": output_path,
                    "full_page": full_page
                }

                page.screenshot(**screenshot_options)
                print(f"✅ 截图已保存: {output_path}")

                return output_path

            except Exception as e:
                print(f"❌ Playwright截图失败: {e}")
                raise
            finally:
                browser.close()

    def take_screenshot_auto(self, method: str = "auto", **kwargs) -> str:
        """
        自动选择最佳的截图方法

        Args:
            method: 截图方法 ('auto', 'selenium', 'playwright')
            **kwargs: 传递给截图方法的参数

        Returns:
            截图文件路径
        """
        if method == "selenium" or (method == "auto" and SELENIUM_AVAILABLE):
            try:
                return self.take_screenshot_selenium(**kwargs)
            except Exception as e:
                if method == "selenium":
                    raise
                print(f"⚠️  Selenium失败，尝试Playwright: {e}")

        if method == "playwright" or (method == "auto" and PLAYWRIGHT_AVAILABLE):
            try:
                return self.take_screenshot_playwright(**kwargs)
            except Exception as e:
                if method == "playwright":
                    raise
                print(f"⚠️  Playwright失败: {e}")

        raise RuntimeError("没有可用的截图方法。请安装selenium或playwright")

    def batch_screenshot(self, scenarios: list, method: str = "auto") -> list:
        """
        批量截图不同场景

        Args:
            scenarios: 场景列表，每个场景包含name和描述
            method: 截图方法

        Returns:
            截图文件路径列表
        """
        results = []

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 场景 {i}/{len(scenarios)}: {scenario['name']}")
            print(f"📝 描述: {scenario['description']}")

            try:
                screenshot_path = self.take_screenshot_auto(
                    method=method,
                    filename=f"scenario_{i:02d}_{scenario['name']}",
                    wait_time=scenario.get('wait_time', 3)
                )
                results.append({
                    'scenario': scenario['name'],
                    'path': screenshot_path,
                    'success': True
                })
            except Exception as e:
                print(f"❌ 场景截图失败: {e}")
                results.append({
                    'scenario': scenario['name'],
                    'path': None,
                    'success': False,
                    'error': str(e)
                })

        return results

def create_demo_scenarios() -> list:
    """创建演示场景列表"""
    return [
        {
            'name': '初始界面',
            'description': '应用启动后的初始界面',
            'wait_time': 2
        },
        {
            'name': '对话界面',
            'description': '用户与AI对话的界面',
            'wait_time': 3
        },
        {
            'name': '知识库管理',
            'description': '知识库上传和管理界面',
            'wait_time': 2
        },
        {
            'name': '学习报告',
            'description': '学习报告生成界面',
            'wait_time': 3
        },
        {
            'name': '习题生成',
            'description': '智能习题生成界面',
            'wait_time': 3
        }
    ]

def main():
    """主函数：启动Streamlit应用并截图"""

    import argparse

    parser = argparse.ArgumentParser(description='Streamlit网页快照工具')
    parser.add_argument('--url', default='http://localhost:8501',
                       help='Streamlit应用URL (默认: http://localhost:8501)')
    parser.add_argument('--method', choices=['auto', 'selenium', 'playwright'],
                       default='auto', help='截图方法')
    parser.add_argument('--output-dir', default='./screenshots',
                       help='输出目录 (默认: ./screenshots)')
    parser.add_argument('--batch', action='store_true',
                       help='批量截图演示场景')
    parser.add_argument('--filename', help='单个截图的文件名')
    parser.add_argument('--wait-time', type=int, default=3,
                       help='等待页面加载时间(秒)')
    parser.add_argument('--full-page', action='store_true', default=True,
                       help='截取全页(默认开启)')

    args = parser.parse_args()

    # 检查依赖
    if not SELENIUM_AVAILABLE and not PLAYWRIGHT_AVAILABLE:
        print("❌ 需要安装截图依赖:")
        print("   pip install selenium")
        print("   或")
        print("   pip install playwright && playwright install")
        return

    # 创建截图工具
    screenshot_tool = StreamlitScreenshot(args.url, args.output_dir)

    try:
        if args.batch:
            # 批量截图
            print("🎬 开始批量截图演示场景...")
            scenarios = create_demo_scenarios()
            results = screenshot_tool.batch_screenshot(scenarios, args.method)

            # 输出结果
            print("\n📊 批量截图结果:")
            print("=" * 50)
            success_count = 0
            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['scenario']}")
                if result['success']:
                    success_count += 1
                    print(f"   📁 {result['path']}")
                else:
                    print(f"   ❌ {result['error']}")

            print(f"\n🎯 总计: {success_count}/{len(results)} 个场景截图成功")

        else:
            # 单个截图
            print("📸 截取单个网页快照...")
            screenshot_path = screenshot_tool.take_screenshot_auto(
                method=args.method,
                filename=args.filename,
                wait_time=args.wait_time,
                full_page=args.full_page
            )
            print(f"✅ 截图完成: {screenshot_path}")

    except Exception as e:
        print(f"❌ 截图失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
