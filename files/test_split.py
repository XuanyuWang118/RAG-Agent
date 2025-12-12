# check_split.py

import os
from document_loader import DocumentLoader
from text_splitter import TextSplitter
from config import DATA_DIR

# --- 配置参数 ---
# 建议为 TXT 和 DOCX 设置一个合理的块大小和重叠量
CHUNK_SIZE = 100 
CHUNK_OVERLAP = 20 
# --------------

def check_data_processing_pipeline():
    """
    检查文档加载和文本切分模块的整合运行情况。
    """
    print("--- 🛠️ RAG 数据处理流水线第一阶段自检开始 ---")
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ 错误：数据目录 {DATA_DIR} 不存在。请创建该目录并放入测试文件。")
        return

    # 1. 实例化加载器和切分器
    loader = DocumentLoader(data_dir=DATA_DIR)
    splitter = TextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    # 2. 文档加载阶段 (Load)
    print("\n## 1. 文档加载 (Document Loading)")
    
    # load_all_documents 方法会遍历 DATA_DIR 并加载所有支持的文件
    initial_documents = loader.load_all_documents()

    if not initial_documents:
        print("❌ 文档加载失败或目录中没有支持的文件。请检查 data/ 目录和文件格式。")
        return

    # 统计加载结果
    pdf_count = sum(1 for doc in initial_documents if doc["filetype"] == ".pdf")
    pptx_count = sum(1 for doc in initial_documents if doc["filetype"] == ".pptx")
    docx_count = sum(1 for doc in initial_documents if doc["filetype"] == ".docx")
    txt_count = sum(1 for doc in initial_documents if doc["filetype"] == ".txt")
    
    print(f"\n✅ 文档加载完成！共加载 {len(initial_documents)} 个初始块 (页/幻灯片/整体文档)。")
    print(f"   - PDF 页数/块数: {pdf_count}")
    print(f"   - PPTX 幻灯片数/块数: {pptx_count}")
    print(f"   - DOCX 文档数: {docx_count}")
    print(f"   - TXT 文档数: {txt_count}")
    
    # 3. 文本切分阶段 (Split)
    print("\n## 2. 文本切分 (Text Splitting)")
    
    # split_documents 会对 DOCX/TXT 进行切分，对 PDF/PPTX 保持原样
    final_chunks = splitter.split_documents(initial_documents)
    
    if not final_chunks:
        print("❌ 文本切分失败。")
        return

    # 4. 结果检验与预览
    print(f"\n✅ 文本切分完成！最终生成 {len(final_chunks)} 个 Chunk。")
    print(f"   (使用参数: chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP})")
    
    # 打印前 5 个 Chunk 的预览
    print("\n### 最终 Chunk 结果预览 (前 5 个):")
    sample_count = min(5, len(final_chunks))
    
    for i in range(sample_count):
        chunk = final_chunks[i]
        content_preview = chunk["content"].replace('\n', ' ') + '...'
        
        # 提取元数据信息
        filename = chunk['filename']
        page_num = chunk['page_number']
        chunk_id = chunk['chunk_id']
        
        source_info = f"来源: {filename}"
        if chunk['filetype'] in ['.pdf', '.pptx']:
            source_info += f", 页/幻灯片: {page_num}"
        elif chunk['filetype'] in ['.docx', '.txt']:
            source_info += f", 块 ID: {chunk_id}"
            
        print(f"\n[{i+1}] {source_info} (长度: {len(chunk['content'])}):")
        print(f"    内容预览: {content_preview}")

    print("\n--- RAG 数据处理流水线第一阶段自检完成 ---")


if __name__ == "__main__":
    check_data_processing_pipeline()