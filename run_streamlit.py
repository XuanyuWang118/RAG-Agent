#!/usr/bin/env python
"""
Streamlit应用启动脚本
运行命令：python run_streamlit.py
"""

import subprocess
import sys
import os

def main():
    """启动Streamlit应用"""
    try:
        print("🔍 检查系统状态...")
        print()

        # 检查streamlit是否安装
        import streamlit
        print(f"✅ Streamlit 已安装 (版本: {streamlit.__version__})")

        # 检查向量数据库是否存在
        if not os.path.exists("./vector_db"):
            print("⚠️  警告：向量数据库不存在！")
            print("请先运行数据处理：python process_data.py")
            print("-" * 50)

        # 检查数据目录
        if os.path.exists("./data"):
            files = [f for f in os.listdir("./data") if f.endswith(('.pdf', '.pptx', '.docx'))]
            print(f"✅ 数据目录存在，包含 {len(files)} 个文档文件")
        else:
            print("❌ 数据目录不存在")

        # 测试应用导入
        print("🔧 测试应用导入...")
        try:
            from app import main as app_main
            print("✅ 应用导入成功")
        except Exception as e:
            print(f"❌ 应用导入失败: {e}")
            return

        print()
        print("🚀 启动智能课程助教系统...")
        print("📱 浏览器将自动打开: http://localhost:8501")
        print("❌ 按 Ctrl+C 停止服务")
        print("🔍 如果无法访问，请尝试:")
        print("   - 检查防火墙设置")
        print("   - 尝试其他端口: streamlit run app.py --server.port 8502")
        print("   - 手动打开浏览器访问 http://localhost:8501")
        print("-" * 60)

        # 使用subprocess启动streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true"]
        subprocess.run(cmd)

    except ImportError:
        print("❌ Streamlit 未安装！")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
