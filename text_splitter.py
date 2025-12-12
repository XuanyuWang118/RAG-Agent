import re
from typing import List, Dict
from tqdm import tqdm
from image_processor import ImageProcessor 

class TextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 初始化图像处理器
        self.image_processor = ImageProcessor() 

        self.separators = [
            "\n\n",  # 两个换行符（段落）
            "\n",    # 换行符
            "。|！|？", # 中文句号、感叹号、问号
            "\. |\! |\? ", # 英文句号、感叹号、问号（注意后面的空格）
            " ",     # 空格
            "",      # 任意字符（最后的兜底策略）
        ]

    def split_text(self, text: str) -> List[str]:
        """将文本切分为块

        TODO: 实现文本切分算法
        要求：
        1. 将文本按照chunk_size切分为多个块
        2. 相邻块之间要有chunk_overlap的重叠（用于保持上下文连续性）
        3. 尽量在句子边界处切分（查找句子结束符：。！？.!?\n\n）
        4. 返回切分后的文本块列表
        """
        if not text:
            return []

        chunks = []
        current_index = 0

        # 1 & 2. 迭代进行切分，直到文本结束
        while current_index < len(text):
            # 计算当前块的理论结束位置 (不考虑重叠)
            end_index = current_index + self.chunk_size
            
            # 确保当前块不超过文本长度
            if end_index >= len(text):
                chunks.append(text[current_index:])
                break

            # 3. 寻找最佳切分点 (尽量在句子边界处)
            # 我们在 [current_index, end_index] 区间内寻找切分点
            
            # 搜索范围：从当前块的末尾向前搜索
            search_start = max(current_index, end_index - self.chunk_overlap * 2) 
            
            # 使用最高优先级的分隔符 (如 "\n\n", "\n", 句号)
            best_split = -1
            
            for sep in self.separators[:-1]: # 排除最后的 "" 分隔符
                # 使用正则表达式查找分隔符
                try:
                    match_iter = re.finditer(sep, text[search_start:end_index])
                except Exception:
                    # 如果正则表达式解析失败（例如遇到转义问题），跳过
                    continue
                
                # 找到最靠后的一个分隔符，确保 chunk size 接近目标
                last_match = None
                for match in match_iter:
                    last_match = match
                
                if last_match:
                    # 计算实际切分位置：搜索起点 + 匹配到的位置 + 分隔符长度
                    split_position = search_start + last_match.start() + len(last_match.group())
                    
                    if split_position <= end_index:
                        best_split = split_position
                        # 找到一个句边界分隔符后，就可以确定切分位置，跳出分隔符搜索
                        break
            
            # 确定切分位置
            if best_split != -1:
                chunk = text[current_index:best_split]
                next_start_index = max(best_split - self.chunk_overlap, current_index + 1)
            else:
                # 如果在搜索范围内没有找到句子边界，则直接硬切到 chunk_size 处
                chunk = text[current_index:end_index]
                next_start_index = end_index - self.chunk_overlap
            
            # 确保切分出的块不为空
            if chunk.strip():
                chunks.append(chunk.strip())
            
            # 更新下一个块的起始位置 (考虑重叠)
            current_index = next_start_index

        return chunks

    def split_documents(self, documents: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """切分多个文档，并对 PDF/PPTX 中的图片进行文本化处理。"""
        chunks_with_metadata = []

        # 新增一个进度条，用于处理图片（这可能是最耗时的部分）
        processed_docs = []
        for doc in tqdm(documents, desc="图像和文本预处理", unit="文档"):
            filetype = doc.get("filetype", "")
            
            # --- 多模态 RAG 升级核心逻辑 ---
            if filetype in [".pdf", ".pptx"] and doc.get("images"):
                original_content = doc.get("content", "")
                image_paths = [img['path'] for img in doc['images']]
                
                # 调用图像处理器，将图片路径列表转换为描述文本
                # 图像处理器会返回一个描述所有图片的单个长字符串
                image_text = self.image_processor.process_images_to_text(image_paths)
                
                if image_text:
                    # 将图片描述文本追加到原始内容中，使用清晰的分隔符
                    new_content = f"{original_content}\n\n--- 图像内容分析 ---\n{image_text}"
                    doc["content"] = new_content
            
            processed_docs.append(doc)
        
        # --------------------------------

        for doc in tqdm(processed_docs, desc="文档切分", unit="文档块"):
            content = doc.get("content", "")
            filetype = doc.get("filetype", "")
            
            # PDF 和 PPTX 已经包含了文本化的图片信息，且我们仍然按页/幻灯片切分
            if filetype in [".pdf", ".pptx"]:
                # PDF/PPTX 的 content 可能包含了图片分析文本
                chunk_data = {
                    "content": content, 
                    "filename": doc.get("filename", "unknown"),
                    "filepath": doc.get("filepath", ""),
                    "filetype": filetype,
                    "page_number": doc.get("page_number", 0),
                    "chunk_id": 0,
                    # 注意：此时的 images 字段仍然保留，但内容已体现在 content 中
                    "images": doc.get("images", []), 
                }
                chunks_with_metadata.append(chunk_data)

            elif filetype in [".docx", ".txt"]:
                # DOCX/TXT 进行二次文本切分
                chunks = self.split_text(content)
                for i, chunk in enumerate(chunks):
                    chunk_data = {
                        "content": chunk,
                        "filename": doc.get("filename", "unknown"),
                        "filepath": doc.get("filepath", ""),
                        "filetype": filetype,
                        "page_number": 0,
                        "chunk_id": i,
                        "images": [], # DOCX/TXT 暂无图片处理
                    }
                    chunks_with_metadata.append(chunk_data)

        print(f"\n文档处理完成，共 {len(chunks_with_metadata)} 个块")
        return chunks_with_metadata