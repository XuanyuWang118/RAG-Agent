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
    检查文档加载和文本切分模块的整合运行情况，并验证图片文本化结果。
    """
    print("--- 🛠️ RAG 数据处理流水线第一阶段自检开始 (多模态验证) ---")
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ 错误：数据目录 {DATA_DIR} 不存在。请创建该目录并放入测试文件。")
        return

    # 1. 实例化加载器和切分器
    # 🚨 注意：DocumentLoader 默认初始化时会创建 ./images_extracted 目录
    loader = DocumentLoader(data_dir=DATA_DIR)
    # 🚨 注意：TextSplitter 初始化时会实例化 ImageProcessor
    splitter = TextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    # 2. 文档加载阶段 (Load)
    print("\n## 1. 文档加载 (Document Loading)")
    initial_documents = loader.load_all_documents()

    if not initial_documents:
        print("❌ 文档加载失败或目录中没有支持的文件。")
        return

    # 统计加载结果和图片元数据
    pdf_count = sum(1 for doc in initial_documents if doc["filetype"] == ".pdf")
    pptx_count = sum(1 for doc in initial_documents if doc["filetype"] == ".pptx")
    total_image_meta = sum(len(doc.get("images", [])) for doc in initial_documents)

    print(f"\n✅ 文档加载完成！共加载 {len(initial_documents)} 个初始块。")
    print(f"   - PDF/PPTX 页数: {pdf_count + pptx_count}")
    print(f"   - 🖼️ 初步提取到的图片元数据总数: {total_image_meta} 张")
    
    # 3. 文本切分与图片文本化阶段 (Split & Process)
    print("\n## 2. 文本切分与图片文本化 (Multimodal Processing)")
    
    # 🚨 这一步将调用 ImageProcessor 对图片进行 OCR/MLLM 文本化，并将结果追加到 content 字段
    final_chunks = splitter.split_documents(initial_documents)
    
    if not final_chunks:
        print("❌ 文本切分或图片处理失败。")
        return

    # 4. 结果检验与预览
    print(f"\n✅ 文本切分完成！最终生成 {len(final_chunks)} 个 Chunk。")
    
    # 打印前 5 个 Chunk 的预览
    print("\n### 最终 Chunk 结果预览 (前 5 个 Chunk 的内容和图片分析验证):")
    sample_count = min(20, len(final_chunks))
    
    for i in range(sample_count):
        chunk = final_chunks[i]
        content = chunk["content"]
        
        # 检查是否包含图片分析的标记
        image_analysis_found = "--- 图像内容分析 ---" in content or "--- 图片 1" in content
        
        # 长度和内容预览
        content_preview = content.replace('\n', ' ')[:100] + '...'
        chunk_length = len(content)
        
        # 提取元数据信息
        filename = chunk['filename']
        page_num = chunk['page_number']
        chunk_id = chunk['chunk_id']
        image_count = len(chunk.get('images', []))
        
        source_info = f"来源: {filename}"
        if chunk['filetype'] in ['.pdf', '.pptx']:
            source_info += f", 页/幻灯片: {page_num}"
        elif chunk['filetype'] in ['.docx', '.txt']:
            source_info += f", 块 ID: {chunk_id}"
            
        
        print(f"\n[{i+1}] {source_info} (长度: {chunk_length}):")
        print(f"    内容预览: {content_preview}")
        
        # 重点：多模态验证
        if image_count > 0:
             # 检查图片元数据数量和内容中是否包含分析结果
            status = f"✅ 图片处理成功 ({image_count} 张图片元数据)" if image_analysis_found else f"⚠️ 图片处理失败/未找到分析标记 ({image_count} 张图片元数据)"
            print(f"    多模态验证: {status}")
        else:
            print(f"    多模态验证: 🔠 纯文本块（未提取到图片元数据）")


    print("\n--- RAG 数据处理流水线第一阶段自检完成 ---")


if __name__ == "__main__":
    check_data_processing_pipeline()