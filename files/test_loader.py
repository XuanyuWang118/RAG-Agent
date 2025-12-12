# check_load.py

import os
from document_loader import DocumentLoader
from config import DATA_DIR

def check_document_loader():
    """
    检查 DocumentLoader 类中所有文档加载方法的成功性。
    """
    print("--- 📄 文档加载模块自检开始 ---")
    
    # 1. 初始化 DocumentLoader
    loader = DocumentLoader(data_dir=DATA_DIR)
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ 错误：数据目录 {DATA_DIR} 不存在。请创建该目录并放入测试文件。")
        return

    # 2. 遍历 DATA_DIR 中的文件
    for root, _, files in os.walk(DATA_DIR):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            ext = os.path.splitext(file_name)[1].lower()
            
            # 只处理支持的文件格式
            if ext not in loader.supported_formats:
                continue

            print(f"\n✅ 正在测试文件: {file_name} ({ext.upper()})")
            
            try:
                # 3. 调用 load_document 方法加载
                doc_chunks = loader.load_document(file_path)
                
                if doc_chunks:
                    print(f"   -> 成功加载！共生成 {len(doc_chunks)} 个文档块/页。")
                    
                    # 4. 打印加载结果的前几个文档块
                    sample_count = min(5, len(doc_chunks))
                    print(f"   -> 示例（前 {sample_count} 个块/页的内容预览）:")
                    
                    for i in range(sample_count):
                        chunk = doc_chunks[i]
                        content_preview = chunk["content"].replace('\n', ' ')
                        page_info = f"页码/幻灯片: {chunk.get('page_number', 'N/A')}" if chunk.get('page_number') != 0 else "整体内容"
                        
                        print(f"      - 块 {i+1} ({page_info}): {content_preview}")
                        
                else:
                    print(f"   -> ❌ 加载失败或内容为空。请检查文件内容和加载方法 {ext}。")
            
            except Exception as e:
                print(f"   -> 🛑 文件 {file_name} 加载过程中发生异常: {e}")

    print("\n--- 文档加载模块自检完成 ---")
    print("\n Note: 当前结果只能识别到文件中的文字内容，无法验证图片、表格等非文字内容的加载效果。后续可以在扩展方向中考虑加入对这些内容的支持和验证。")


if __name__ == "__main__":
    check_document_loader()