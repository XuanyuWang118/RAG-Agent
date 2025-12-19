#!/usr/bin/env python3
"""
测试网页快照功能
"""

import requests
from bs4 import BeautifulSoup

def test_web_scraping():
    """测试网页抓取功能"""

    test_url = "https://example.com"

    print("🧪 测试网页抓取功能")
    print("=" * 40)

    try:
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print(f"🌐 正在抓取: {test_url}")

        # 发送请求
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        print(f"✅ HTTP状态码: {response.status_code}")
        print(f"📏 内容长度: {len(response.content)} bytes")

        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取标题
        title = soup.title.string if soup.title else "无标题"
        print(f"📄 网页标题: {title}")

        # 清理内容
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()

        main_content = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in main_content.split('\n') if line.strip()]
        cleaned_content = '\n'.join(lines)

        print(f"📝 提取的文本长度: {len(cleaned_content)} 字符")
        print(f"📄 文本预览: {cleaned_content[:200]}...")

        print("\n✅ 网页抓取测试成功！")
        return True

    except Exception as e:
        print(f"❌ 网页抓取测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_web_scraping()
    if success:
        print("\n🎉 网页快照功能可以正常工作！")
    else:
        print("\n⚠️ 网页快照功能可能存在问题，请检查网络连接和依赖库。")
