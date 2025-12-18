from typing import List, Dict
from tqdm import tqdm


class TextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

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
                match_iter = re.finditer(sep, text[search_start:end_index])
                
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

    def split_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """切分多个文档。
        对于PDF和PPT，已经按页/幻灯片分割，不再进行二次切分
        对于DOCX和TXT，进行文本切分
        """
        chunks_with_metadata = []

        for doc in tqdm(documents, desc="处理文档", unit="文档"):
            content = doc.get("content", "")
            filetype = doc.get("filetype", "")

            if filetype in [".pdf", ".pptx"]:
                chunk_data = {
                    "content": content,
                    "filename": doc.get("filename", "unknown"),
                    "filepath": doc.get("filepath", ""),
                    "filetype": filetype,
                    "page_number": doc.get("page_number", 0),
                    "chunk_id": 0,
                    "images": doc.get("images", []),
                }
                chunks_with_metadata.append(chunk_data)

            elif filetype in [".docx", ".txt"]:
                chunks = self.split_text(content)
                for i, chunk in enumerate(chunks):
                    chunk_data = {
                        "content": chunk,
                        "filename": doc.get("filename", "unknown"),
                        "filepath": doc.get("filepath", ""),
                        "filetype": filetype,
                        "page_number": 0,
                        "chunk_id": i,
                        "images": [],
                    }
                    chunks_with_metadata.append(chunk_data)

        print(f"\n文档处理完成，共 {len(chunks_with_metadata)} 个块")
        return chunks_with_metadata
