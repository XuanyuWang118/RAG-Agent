import os
import uuid
from datetime import datetime
from typing import List, Dict

import chromadb
from chromadb.config import Settings
from openai import OpenAI
from tqdm import tqdm

from config import (
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_EMBEDDING_MODEL,
    TOP_K,
)


class VectorStore:

    def __init__(
        self,
        db_path: str = VECTOR_DB_PATH,
        collection_name: str = COLLECTION_NAME,
        api_key: str = OPENAI_API_KEY,
        api_base: str = OPENAI_API_BASE,
    ):
        self.db_path = db_path
        self.collection_name = collection_name

        # 初始化OpenAI客户端
        self.client = OpenAI(api_key=api_key, base_url=api_base)

        # 初始化ChromaDB
        os.makedirs(db_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=db_path, settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name, metadata={"description": "课程材料向量数据库"}
        )

    def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示

        TODO: 使用OpenAI API获取文本的embedding向量

        """
        try:
            # 调用 OpenAI API 获取 embedding
            response = self.client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=text
            )
            # 返回第一个（也是唯一的）embedding 向量
            return response.data[0].embedding
        except Exception as e:
            print(f"获取 Embedding 失败: {e}")
            return []

    def add_documents(self, chunks: List[Dict[str, str]]) -> None:
        """添加文档块到向量数据库
        TODO: 实现文档块添加到向量数据库
        要求：
        1. 遍历文档块
        2. 获取文档块内容
        3. 获取文档块元数据
        5. 打印添加进度
        """
        if not chunks:
            print("没有文档块可以添加。")
            return

        texts = [chunk['content'] for chunk in chunks]
        metadatas = []
        ids = []

        # 批量获取 Embedding
        print("正在批量获取 Embedding 向量...")
        
        # ⚠️ 注意：OpenAI/自定义 API 通常支持批量请求，但为了简洁和兼容性，
        # 这里使用 tqdm 循环调用 get_embedding（适用于少量文档，大量文档应优化为批量请求）。
        # 如果您的 API 支持批量请求，应优化此处的逻辑。
        embeddings = []
        for text in tqdm(texts, desc="获取向量"):
            embeddings.append(self.get_embedding(text))
        
        # 准备 ChromaDB 所需的数据格式
        for i, chunk in enumerate(chunks):
            # 2. 获取文档块元数据
            metadata = {
                "filename": chunk.get("filename"),
                "filetype": chunk.get("filetype"),
                "page_number": chunk.get("page_number"),
                "chunk_id": chunk.get("chunk_id"),
                "filepath": chunk.get("filepath"),
            }
            metadatas.append(metadata)
            
            # 3. 批量生成唯一ID
            # 使用文件名、页码、块ID组合生成唯一ID
            unique_id = f"{chunk.get('filename')}_{chunk.get('page_number')}_{chunk.get('chunk_id')}_{i}"
            ids.append(unique_id)

        # 4. 批量添加文档块到 ChromaDB
        print("正在批量添加文档块到 ChromaDB...")
        try:
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ 成功将 {len(ids)} 个文档块添加到向量数据库中。")
        except Exception as e:
            print(f"❌ 添加文档到 ChromaDB 失败: {e}")

    def search(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """搜索相关文档

        TODO: 实现向量相似度搜索
        要求：
        1. 首先获取查询文本的embedding向量（调用self.get_embedding）
        2. 使用self.collection进行向量搜索, 得到top_k个结果
        3. 格式化返回结果，每个结果包含：
           - content: 文档内容
           - metadata: 元数据（文件名、页码等）
        4. 返回格式化的结果列表
        """

        # 1. 获取查询文本的 embedding 向量
        query_embedding = self.get_embedding(query)
        
        if not query_embedding:
            return []

        # 2. 使用 self.collection 进行向量搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances'] # 包含文档内容和元数据
        )

        # 3. 格式化返回结果
        formatted_results = []
        
        # results 结构通常是嵌套列表，我们提取第一个结果集
        if results and results.get("documents"):
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": dist # 可以用于调试或排序
                })

        # 4. 返回格式化的结果列表
        return formatted_results

    def clear_collection(self) -> None:
        """清空collection"""
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name, metadata={"description": "课程向量数据库"}
        )
        print("向量数据库已清空")

    def add_documents_incremental(self, chunks: List[Dict[str, str]]) -> bool:
        """增量添加文档到向量数据库

        参数:
            chunks: 文档块列表，每个块包含content和metadata

        返回:
            bool: 是否添加成功
        """
        if not chunks:
            print("没有文档块需要添加")
            return True

        try:
            # 获取现有文档数量，用于生成新ID
            current_count = self.collection.count()

            texts = [chunk['content'] for chunk in chunks]
            metadatas = []
            ids = []

            # 批量获取embeddings（复用现有的get_embedding方法）
            print(f"正在向量化 {len(texts)} 个新文档块...")
            embeddings = []
            for i, text in enumerate(texts):
                if (i + 1) % 10 == 0:  # 每10个显示一次进度
                    print(f"已处理 {i + 1}/{len(texts)} 个文档块")
                embeddings.append(self.get_embedding(text))

            # 准备metadata和IDs
            for i, chunk in enumerate(chunks):
                metadata = {
                    "filename": chunk.get("filename", "unknown"),
                    "filetype": chunk.get("filetype", ""),
                    "page_number": chunk.get("page_number", 0),
                    "chunk_id": chunk.get("chunk_id", i),
                    "filepath": chunk.get("filepath", ""),
                    "added_at": datetime.now().isoformat(),  # 标记添加时间
                    "added_incrementally": True  # 标记为增量添加
                }
                metadatas.append(metadata)

                # 生成唯一ID（避免与现有ID冲突）
                unique_id = f"incremental_{current_count + i}_{uuid.uuid4().hex[:8]}"
                ids.append(unique_id)

            # 批量添加到ChromaDB（复用现有的collection操作）
            print(f"正在添加到向量数据库...")
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )

            print(f"✅ 增量添加成功：{len(ids)} 个文档块")
            return True

        except Exception as e:
            print(f"❌ 增量添加失败: {e}")
            return False

    def get_collection_count(self) -> int:
        """获取collection中的文档数量"""
        return self.collection.count()
