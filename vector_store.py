import os
import joblib
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from tqdm import tqdm

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever 

from config import (
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_EMBEDDING_MODEL,
    TOP_K,
    RRF_K,
)

BM25_INDEX_PATH = os.path.join(VECTOR_DB_PATH, "bm25_index.joblib")

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
        
        # 【优化 1：引入 BM25 检索器】
        # BM25 检索器需要所有文档才能初始化，这里先初始化为 None。
        self.bm25_retriever: Optional[BM25Retriever] = None

        # 【启动时尝试加载 BM25 索引】
        if os.path.exists(BM25_INDEX_PATH):
            print("🚀 正在加载已存在的 BM25 稀疏检索器...")
            try:
                # 尝试从磁盘加载索引
                self.bm25_retriever = joblib.load(BM25_INDEX_PATH)
                print("✅ BM25 检索器加载完成。")
            except Exception as e:
                print(f"❌ BM25 索引加载失败: {e}")
                self.bm25_retriever = None
        else:
            print("⚠️ BM25 稀疏检索器文件不存在，需通过 add_documents 初始化。")


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

    def _initialize_bm25_retriever(self, lc_documents: List[Document]) -> None:
        """
        【优化 2：新增 BM25 初始化方法】
        私有方法：使用所有 LangChain Document 对象初始化 BM25 稀疏检索器，并持久化到磁盘。
        """
        if not lc_documents:
             print("⚠️ 无法初始化 BM25 检索器：没有文档。")
             return

        print("正在初始化 BM25 稀疏检索器...")
        # 从文档列表中创建 BM25 索引
        self.bm25_retriever = BM25Retriever.from_documents(lc_documents)
        self.bm25_retriever.k = TOP_K 
        print("✅ BM25 检索器初始化完成。")

        # 【将 BM25 检索器持久化到磁盘】
        try:
            joblib.dump(self.bm25_retriever, BM25_INDEX_PATH)
            print(f"💾 BM25 检索器已成功保存到 {BM25_INDEX_PATH}")
        except Exception as e:
            print(f"❌ 警告：BM25 检索器持久化失败: {e}")


    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """添加文档块到向量数据库
        TODO: 实现文档块添加到向量数据库
        要求：
        1. 遍历文档块
        2. 获取文档块内容
        3. 获取文档块元数据
        5. 打印添加进度
        【优化 3：改造 add_documents】
        添加文档块到向量数据库，并用于初始化 BM25 索引。
        """
        if not chunks:
            print("没有文档块可以添加。")
            return

        texts = [chunk['content'] for chunk in chunks]
        metadatas = []
        ids = []
        lc_documents = [] # 新增：用于 BM25 索引的 LangChain 文档列表

        # 批量获取 Embedding
        print("正在批量获取 Embedding 向量...")
        embeddings = []
        for text in tqdm(texts, desc="获取向量"):
            embeddings.append(self.get_embedding(text))
        
        # 准备 ChromaDB 数据和 LangChain Document 列表
        for i, chunk in enumerate(chunks):
            # 获取文档块元数据
            metadata = {
                "filename": chunk.get("filename"),
                "filetype": chunk.get("filetype"),
                "page_number": chunk.get("page_number"),
                "chunk_id": chunk.get("chunk_id"),
                "filepath": chunk.get("filepath"),
            }
            metadatas.append(metadata)

            # 使用文件名、页码、块ID组合生成唯一ID
            unique_id = f"{chunk.get('filename')}_{chunk.get('page_number')}_{chunk.get('chunk_id')}_{i}"
            ids.append(unique_id)
            
            # 创建 LangChain Document 对象 (用于 BM25)
            lc_doc = Document(page_content=chunk['content'], metadata=metadata)
            lc_documents.append(lc_doc)


        # 批量添加文档块到 ChromaDB
        print("正在批量添加文档块到 ChromaDB...")
        try:
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ 成功将 {len(ids)} 个文档块添加到向量数据库中。")
            
            # 初始化 BM25 检索器
            self._initialize_bm25_retriever(lc_documents)
            
        except Exception as e:
            print(f"❌ 添加文档到 ChromaDB 失败: {e}")


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
            new_lc_documents = [] # 新增：用于增量更新 BM25

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

            # 【增量更新 BM25 索引】
            # 增量添加后需要重新构建整个 BM25 索引，以包含新文档
            print("🔄 增量添加完成，正在重建 BM25 索引...")
            
            # 1. 从 ChromaDB 检索所有现有文档
            all_chroma_docs = self.collection.get(
                include=['documents', 'metadatas']
            )
            
            # 2. 将所有文档转换为 LangChain Document 格式
            all_lc_documents = [
                Document(page_content=all_chroma_docs['documents'][i], metadata=all_chroma_docs['metadatas'][i])
                for i in range(len(all_chroma_docs['documents']))
            ]
            
            # 3. 使用所有文档重新初始化 BM25 检索器
            self._initialize_bm25_retriever(all_lc_documents)
            
            print(f"✅ 增量添加成功：{len(ids)} 个文档块，BM25 索引已重建。")
            return True

        except Exception as e:
            print(f"❌ 增量添加失败: {e}")
            return False

    def search_dense(self, query: str, top_k: int = TOP_K) -> List[Dict]:
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

    def search_bm25(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        【新增/辅助方法】实现纯粹的 BM25 稀疏检索。
        注意：该方法仅供内部使用或 RRF 融合调用。
        """
        if self.bm25_retriever is None:
            print("⚠️ 警告: BM25 检索器未初始化，无法执行稀疏检索。")
            return []

        # BM25 返回 LangChain Document 对象，使用 invoke() 方法进行检索
        self.bm25_retriever.k = top_k # 确保使用传入的 top_k
        bm25_docs = self.bm25_retriever.invoke(query)
        
        # 格式化 LangChain Document 为 List[Dict] 格式
        formatted_results = []
        for doc in bm25_docs:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": dict(doc.metadata),
                "distance": 0.0 # BM25 本身不提供距离或相关性分数，设为 0.0
            })
        return formatted_results

    def search(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        【优化 4：实现混合检索 (RRF 融合)】 结合稀疏检索和密集检索的结果，使用 RRF 算法重新排序。
        """
        # 检查 BM25 是否已初始化，如果未初始化则退化为纯向量搜索
        if self.bm25_retriever is None:
            print("⚠️ 警告: 正在进行纯向量搜索，BM25 检索器未初始化。")
            return self.search_dense(query, top_k=top_k)

        # 1. 密集检索 (向量搜索) - 获取 Top_K * 2 的结果，留给 RRF 融合
        dense_results = self.search_dense(query, top_k=top_k * 2) 
        
        # 2. 稀疏检索 (BM25 关键词搜索) - 获取 Top_K * 2 的结果
        # BM25 返回 LangChain Document 对象，使用 invoke() 方法进行检索
        bm25_docs = self.bm25_retriever.invoke(query)
        
        # 3. 融合 (Reciprocal Rank Fusion, RRF) 
        fused_scores = {}
        all_results_map = {} # 用于存储所有独特的文档块，方便查找

        # 辅助函数：根据文件名、页码和块 ID 创建唯一键，用于融合
        def _get_unique_key(item: Dict[str, Any]) -> str:
            meta = item.get('metadata', {})
            # 这里的键必须与 add_documents 中的 ID 生成逻辑一致
            return f"{meta.get('filename')}_{meta.get('page_number')}_{meta.get('chunk_id')}"
        
        def _get_doc_key(doc: Document) -> str:
             return f"{doc.metadata.get('filename')}_{doc.metadata.get('page_number')}_{doc.metadata.get('chunk_id')}"

        # A. 处理密集检索结果
        for i, item in enumerate(dense_results):
            key = _get_unique_key(item)
            rank = i + 1
            score = 1 / (RRF_K + rank)
            fused_scores[key] = fused_scores.get(key, 0) + score
            all_results_map[key] = item
            
        # B. 处理稀疏检索结果
        for i, doc in enumerate(bm25_docs):
            key = _get_doc_key(doc)
            rank = i + 1
            score = 1 / (RRF_K + rank)
            fused_scores[key] = fused_scores.get(key, 0) + score
            
            # 如果是 BM25 独有的结果，将其加入 map 中（需转换为 Dict 格式）
            if key not in all_results_map:
                 all_results_map[key] = {
                    "content": doc.page_content,
                    "metadata": dict(doc.metadata),
                    "distance": 0.0 # RRF 融合后距离不再有意义
                }

        # 4. 排序和提取 Top-K 结果
        
        # 根据融合得分降序排列所有唯一的文档键
        sorted_keys = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        # 提取 Top-K 结果
        final_results = []
        for key in sorted_keys:
            if len(final_results) >= top_k:
                break
            final_results.append(all_results_map[key])
            
        return final_results
    
    def clear_collection(self) -> None:
        """清空collection"""
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name, metadata={"description": "课程向量数据库"}
        )
        print("向量数据库已清空")

    def get_collection_count(self) -> int:
        """获取collection中的文档数量"""
        return self.collection.count()
