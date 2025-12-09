from typing import List, Dict, Optional, Tuple

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    MODEL_NAME,
    TOP_K,
)
from vector_store import VectorStore


class RAGAgent:
    def __init__(
        self,
        model: str = MODEL_NAME,
    ):
        self.model = model

        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

        self.vector_store = VectorStore()

        """
        TODO: 实现并调整系统提示词，使其符合课程助教的角色和回答策略
        """
        self.system_prompt = """你是一位友好、严谨且专业的智能课程助教。
        你的任务是根据提供的【课程内容】来回答学生的问题。
        回答要求：
        1. **基于事实**：所有回答必须严格基于【课程内容】中检索到的信息。
        2. **追溯来源**：在回答的开头或末尾，必须清晰标注信息来源，格式为：[来源：文件名，页码 X 或 幻灯片 X] 或 [来源：文件名]（若无页码）。如果有多个来源，请合并或分别标注。
        3. **无法回答**：如果【课程内容】中找不到足够的信息来回答学生的问题，请礼貌地告知学生：“我无法根据当前课程材料回答这个问题，请参考相关教材或联系老师。”
        4. **语气专业**：保持助教的专业、友好和条理清晰的语气。
        """

    def retrieve_context(
        self, query: str, top_k: int = TOP_K
    ) -> Tuple[str, List[Dict]]:
        """检索相关上下文
        TODO: 实现检索相关上下文
        要求：
        1. 使用向量数据库检索相关文档
        2. 格式化检索结果，构建上下文字符串
        3. 每个检索结果需要包含来源信息（文件名和页码）
        4. 返回格式化的上下文字符串和原始检索结果列表
        """
        # 1. 使用向量数据库检索相关文档
        retrieved_docs = self.vector_store.search(query, top_k=top_k)
        
        # 2. 格式化检索结果，构建上下文字符串
        context_parts = []
        
        # 使用集合去重，避免重复引用相同的来源
        source_set = set()
        
        for doc in retrieved_docs:
            content = doc["content"]
            metadata = doc["metadata"]
            
            filename = metadata.get("filename", "未知文件")
            page_number = metadata.get("page_number", 0)
            
            # 3. 每个检索结果需要包含来源信息（文件名和页码）
            if page_number and page_number > 0:
                # 判断是页码 (PDF) 还是幻灯片 (PPTX)
                source_label = "页码" if metadata.get("filetype") == ".pdf" else "幻灯片"
                source_info = f"[来源：{filename}, {source_label} {page_number}]"
                source_set.add(f"{filename}, {source_label} {page_number}")
            else:
                # DOCX/TXT 或没有页码/幻灯片信息的文档
                source_info = f"[来源：{filename}]"
                source_set.add(filename)
                
            # 将来源信息放在内容上方，用于 LLM 区分
            context_parts.append(f"{source_info}\n{content}\n---")

        context_string = "\n".join(context_parts)
        
        # 4. 返回格式化的上下文字符串和原始检索结果列表
        return context_string, retrieved_docs

    def generate_response(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict]] = None,
    ) -> str:
        """生成回答
        
        参数:
            query: 用户问题
            context: 检索到的上下文
            chat_history: 对话历史
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        if chat_history:
            messages.extend(chat_history)

        """
        TODO: 实现用户提示词
        要求：
        1. 包含相关的课程内容
        2. 包含学生问题
        3. 包含来源信息（文件名和页码）
        4. 返回用户提示词
        """
        user_text = f"""
        请基于下面的【课程内容】来回答学生的问题。请严格遵循系统提示词中的所有要求。

        【课程内容】
        {context}

        【学生问题】
        {query}
        """

        messages.append({"role": "user", "content": user_text})
        
        # 多模态接口示意（如需添加图片支持，可参考以下格式）：
        # content_parts = [{"type": "text", "text": user_text}]
        # content_parts.append({
        #     "type": "image_url",
        #     "image_url": {"url": f"data:image/png;base64,{base64_image}"}
        # })
        # messages.append({"role": "user", "content": content_parts})

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=1500
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"生成回答时出错: {str(e)}"

    def answer_question(
        self, query: str, chat_history: Optional[List[Dict]] = None, top_k: int = TOP_K
    ) -> Dict[str, any]:
        """回答问题
        
        参数:
            query: 用户问题
            chat_history: 对话历史
            top_k: 检索文档数量
            
        返回:
            生成的回答
        """
        context, retrieved_docs = self.retrieve_context(query, top_k=top_k)

        if not context:
            context = "（未检索到特别相关的课程材料）"

        answer = self.generate_response(query, context, chat_history)

        return answer

    def chat(self) -> None:
        """交互式对话"""
        print("=" * 60)
        print("欢迎使用智能课程助教系统！")
        print("=" * 60)

        chat_history = []

        while True:
            try:
                query = input("\n学生: ").strip()

                if not query:
                    continue

                answer = self.answer_question(query, chat_history=chat_history)

                print(f"\n助教: {answer}")

                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": answer})

            except Exception as e:
                print(f"\n错误: {str(e)}")
