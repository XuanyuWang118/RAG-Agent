#!/usr/bin/env python
"""
测试Web图片处理功能的脚本
"""

import os
import base64
from PIL import Image
import io

def test_image_processing():
    """测试图片处理功能"""
    print("🖼️ 测试图片处理功能...")
    print("=" * 50)

    # 检查是否有测试图片
    test_images = []
    if os.path.exists("images_extracted"):
        test_images = [f for f in os.listdir("images_extracted") if f.endswith(('.png', '.jpg', '.jpeg'))]

    if not test_images:
        print("⚠️ 没有找到测试图片，请先运行数据处理脚本")
        print("运行: python process_data.py")
        return

    # 选择第一张图片进行测试
    test_image_path = os.path.join("images_extracted", test_images[0])
    print(f"📸 使用测试图片: {test_image_path}")

    try:
        # 测试图片读取
        image = Image.open(test_image_path)
        print(f"✅ 图片读取成功: {image.size}, {image.mode}")

        # 测试图片处理函数（模拟app.py中的process_uploaded_image）
        def process_uploaded_image(uploaded_file) -> str:
            """处理上传的图片文件，返回Base64编码"""
            try:
                # 读取上传的文件
                image = Image.open(uploaded_file)

                # 压缩图片（可选，控制大小）
                max_size = 1024
                if image.size[0] > max_size or image.size[1] > max_size:
                    # 计算缩放比例
                    ratio = min(max_size / image.size[0], max_size / image.size[1])
                    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                    print(f"📏 图片已压缩: {image.size}")

                # 转换为RGB（处理RGBA图片）
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                    print(f"🎨 图片已转换为RGB模式")

                # 保存为JPEG格式的bytes
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85)
                image_bytes = buffer.getvalue()

                # 转换为base64
                base64_str = base64.b64encode(image_bytes).decode('utf-8')
                print(f"🔄 Base64编码完成: {len(base64_str)} 字符")

                return base64_str

            except Exception as e:
                print(f"❌ 图片处理失败: {e}")
                return None

        # 测试图片处理
        print("\n🔧 测试图片处理...")
        with open(test_image_path, 'rb') as f:
            base64_data = process_uploaded_image(f)

        if base64_data:
            print("✅ 图片处理成功！")

            # 测试RAG Agent的图片问答功能
            print("\n🤖 测试RAG Agent图片问答...")
            try:
                from rag_agent import RAGAgent
                agent = RAGAgent()

                test_question = "请描述这张图片的内容"
                print(f"❓ 测试问题: {test_question}")

                answer = agent.answer_image_question(
                    test_question,
                    base64_data,
                    chat_history=[]
                )

                print("✅ RAG图片问答测试成功！")
                print(f"📝 回答预览: {answer[:100]}...")

            except Exception as e:
                print(f"❌ RAG图片问答测试失败: {e}")

        else:
            print("❌ 图片处理失败")

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 图片处理功能测试完成！")

if __name__ == "__main__":
    test_image_processing()
