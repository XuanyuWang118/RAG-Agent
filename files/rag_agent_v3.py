import json
from typing import List, Dict, Optional, Tuple, Any

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    MODEL_NAME,
    TOP_K,
    DEFAULT_RETRIEVAL_STRATEGY, 
    ENABLE_ADVANCED_RAG,
)
from vector_store import VectorStore
from tools import tool_manager


class RAGAgent:
    def __init__(
        self,
        model: str = MODEL_NAME,
    ):
        self.model = model

        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

        self.vector_store = VectorStore()
        
        # 【新增】保存高级策略开关状态
        self.enable_advanced_rag = ENABLE_ADVANCED_RAG 

        self.system_prompt = """你是一位友好、严谨且专业的智能课程助教。
        你的任务是根据提供的【课程内容】来回答学生的问题。

        **回答策略（优先级顺序）：**
        1. **优先使用课程内容**：首先基于【课程内容】中的信息回答问题
        2. **补充联网搜索**：如果【课程内容】信息不足或没有相关内容，才使用联网搜索获取补充信息
        3. **直接回答**：对于不涉及课程知识的一般性问题（如时间、简单计算），直接回答无需追溯来源

        回答要求：
        1. **基于事实**：所有回答必须严格基于【课程内容】或者联网搜索中检索到的信息。
        2. **追溯来源**：在回答中使用课程内容时，必须在开头或末尾标注信息来源，格式为：[来源：文件名，页码 X 或 幻灯片 X] 或 [来源：文件名]（若无页码）。如果使用了联网搜索，标注为：[来源：网络搜索结果]。如果有多个来源，请合并或分别标注。
        3. **无法回答**：如果【课程内容】和联网搜索中都找不到足够的信息来回答学生的问题，请告知学生："我无法根据当前课程材料回答这个问题，请参考相关教材或联系老师。"
        4. **语气专业**：保持助教的专业、友好和条理清晰的语气。
        """

    def _construct_search_query(self, current_query: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        使用对话历史来提炼搜索关键词，提升多轮检索精度。
        【逻辑修改】仅在 self.enable_advanced_rag 开启时，才执行多轮增强。
        """
        if not self.enable_advanced_rag:
            return current_query
            
        if not chat_history or len(chat_history) < 2:
            return current_query
        
        # 提取最近的对话（例如，最近的问答对）
        last_exchange = chat_history[-2:]
        
        # 构造用于 RAG 检索的最终查询
        recent_context = f"最近的问题：{last_exchange[0]['content']}，最近的回答：{last_exchange[1]['content']}。"
        return f"{recent_context} 学生的新问题是：{current_query}"

    def _analyze_query_type(self, query: str) -> str:
        """
        使用 LLM 分析查询意图和类型，以决定最佳检索策略。
        """
        prompt = f"""分析以下用户查询的类型和意图，并严格以单字字符串形式返回最适合的检索策略。

        1. 'HYBRID': 如果查询是模糊的、使用了代词（如“它”、“这个”）或同时包含关键词和概念，需要平衡语义和精确匹配。
        2. 'BM25': 如果查询包含大量特定、罕见、技术性名词或ID，且明显是一个全新的、精确匹配的问题。
        3. 'DENSE': 如果查询是关于定义、关系、比较或广义主题，需要深度语义理解。

        查询: "{query}"

        仅返回以下字符串之一: 'HYBRID', 'BM25', 'DENSE'
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10
            )
            # 清理和规范化输出
            return response.choices[0].message.content.strip().upper().replace('"', '')
        except Exception:
            # 失败时默认使用 config 中的策略
            return DEFAULT_RETRIEVAL_STRATEGY

    def retrieve_context(
        self, query: str, chat_history: Optional[List[Dict]] = None, top_k: int = TOP_K
    ) -> Tuple[str, List[Dict]]:
        """
        【核心修改】实现检索策略分派器 (Strategy Dispatcher)。
        新增逻辑：如果 self.enable_advanced_rag 为 False，则强制使用 DENSE 策略。
        """
        # 1. 构造用于检索的增强查询 (该函数内部会根据开关返回原始或增强查询)
        search_query = self._construct_search_query(query, chat_history)

        retrieved_docs = []
        
        # --- 策略决策开始 ---
        if not self.enable_advanced_rag:
            # 【退化逻辑】如果高级RAG开关关闭，强制退化到纯向量（DENSE）策略。
            query_type = "DENSE"
            print("⚙️ 高级RAG增强已关闭，强制退化到纯向量密集检索 (DENSE) 策略。")
            
        else:
            # 启用高级策略：执行 LLM 策略分析
            query_type = self._analyze_query_type(search_query)
            print(f"⚙️ 高级RAG增强已启用 | LLM分析策略: {query_type}")

        # 3. 策略分派器 (Dispatching logic based on query_type)
        if query_type == 'DENSE':
            # 概念主导或退化策略：纯向量检索
            retrieved_docs = self.vector_store.search_dense(search_query, top_k=top_k)
            print("➡️ 采用纯向量密集检索 (search_dense)")
            
        elif query_type == 'BM25':
            # 关键词主导：纯稀疏检索
            retrieved_docs = self.vector_store.search_bm25(search_query, top_k=top_k)
            print("➡️ 采用纯 BM25 稀疏检索 (search_bm25)")

        elif query_type == 'HYBRID': 
            # 混合检索
            retrieved_docs = self.vector_store.search(search_query, top_k=top_k)
            print("➡️ 采用 RRF 混合检索 (search)")
        
        else:
            # LLM分析失败时的兜底策略 (仅在高级模式下可能发生)
            # 使用 config 中配置的 DEFAULT_RETRIEVAL_STRATEGY
            if DEFAULT_RETRIEVAL_STRATEGY == "BM25":
                 retrieved_docs = self.vector_store.search_bm25(search_query, top_k=top_k)
            elif DEFAULT_RETRIEVAL_STRATEGY == "DENSE":
                 retrieved_docs = self.vector_store.search_dense(search_query, top_k=top_k)
            else:
                 retrieved_docs = self.vector_store.search(search_query, top_k=top_k)
            print(f"⚠️ LLM 分析失败，回退到 DEFAULT 策略: {DEFAULT_RETRIEVAL_STRATEGY}")
            
        # --- 策略决策结束 ---

        # 4. 格式化检索结果，构建上下文字符串
        context_parts = []
        
        for doc in retrieved_docs:
            content = doc["content"]
            metadata = doc["metadata"]
            
            filename = metadata.get("filename", "未知文件")
            page_number = metadata.get("page_number", 0)
            
            # 5. 每个检索结果需要包含来源信息（文件名和页码）
            if page_number and page_number > 0:
                # 判断是页码 (PDF) 还是幻灯片 (PPTX)
                source_label = "页码" if metadata.get("filetype") == ".pdf" else "幻灯片"
                source_info = f"[来源：{filename}, {source_label} {page_number}]"
            else:
                # DOCX/TXT 或没有页码/幻灯片信息的文档
                source_info = f"[来源：{filename}]"
                
            # 将来源信息放在内容上方，用于 LLM 区分
            context_parts.append(f"{source_info}\n{content}\n---")

        context_string = "\n".join(context_parts)
        
        # 6. 返回格式化的上下文字符串和原始检索结果列表
        return context_string, retrieved_docs

    def generate_response(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict]] = None,
    ) -> str:
        """生成回答"""
        messages = [{"role": "system", "content": self.system_prompt}]

        if chat_history:
            messages.extend(chat_history)

        user_text = f"""
        请基于下面的【课程内容】来回答学生的问题。请严格遵循系统提示词中的所有要求。

        **优先级策略：**
        1. 首先基于【课程内容】回答问题
        2. 只有在【课程内容】信息不足时，才使用工具获取补充信息

        【课程内容】
        {context}

        【学生问题】
        {query}

        如果【课程内容】无法提供足够的信息，你可以选择使用提供的工具搜索网络信息、进行计算或获取当前时间。
        """

        messages.append({"role": "user", "content": user_text})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_manager.get_tool_definitions(),
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1500
            )

            response_message = response.choices[0].message

            # 检查是否有工具调用
            if response_message.tool_calls:
                # 执行工具调用
                tool_results = self._execute_tool_calls(response_message.tool_calls)

                # 将工具调用结果添加到消息历史
                messages.append(response_message)
                for tool_result in tool_results:
                    messages.append(tool_result)

                # 第二次调用：基于工具结果生成最终回答
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )

                return final_response.choices[0].message.content
            else:
                # 没有工具调用，直接返回结果
                return response_message.content

        except Exception as e:
            return f"生成回答时出错: {str(e)}"

    def _execute_tool_calls(self, tool_calls) -> List[Dict]:
        """执行工具调用并返回结果"""
        tool_results = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"🔧 执行工具: {tool_name} 参数: {tool_args}")

            # 执行工具
            tool_result = tool_manager.execute_tool(tool_name, tool_args)

            # 格式化工具结果消息
            tool_result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            }

            tool_results.append(tool_result_message)

        return tool_results

    def answer_question(
        self, query: str, chat_history: Optional[List[Dict]] = None, top_k: int = TOP_K
    ) -> str:
        """回答问题"""
        
        # 将 chat_history 传入 retrieve_context，实现多轮检索增强和策略分派
        context, retrieved_docs = self.retrieve_context(query, chat_history=chat_history, top_k=top_k)

        if not context:
            context = "（未检索到特别相关的课程材料）"

        answer = self.generate_response(query, context, chat_history)

        return answer

    def chat(self) -> None:
        """交互式对话"""
        print("=" * 60)
        print("欢迎使用智能课程助教系统！")
        print("当前 RAG 策略模式:", "高级增强模式" if self.enable_advanced_rag else "纯向量基线模式 (DENSE)")
        print("=" * 60)

        chat_history = []

        while True:
            try:
                query = input("\n学生: ").strip()

                if not query:
                    continue

                answer = self.answer_question(query, chat_history=chat_history)

                print(f"\n助教: {answer}")

                # 更新对话历史
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": answer})

            except Exception as e:
                print(f"\n错误: {str(e)}")