import json
<<<<<<< HEAD
from typing import List, Dict, Optional, Tuple
=======
from typing import List, Dict, Optional, Tuple, Union
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
from datetime import datetime

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
from tools import ToolManager
from image_processor import ImageProcessor
<<<<<<< HEAD
from typing import Union
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63


class RAGAgent:
    def __init__(
        self,
        model: str = MODEL_NAME,
    ):
        self.model = model

        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

        self.vector_store = VectorStore()
        
        # 初始化图片处理器和工具管理器
        self.image_processor = ImageProcessor()
        self.tool_manager = ToolManager(rag_agent=self)
        
        # 【新增】保存策略开关状态
        self.enable_advanced_rag = ENABLE_ADVANCED_RAG

<<<<<<< HEAD
        # 初始化图片处理器
        self.image_processor = ImageProcessor()

        # 初始化工具管理器（传递自身引用以支持出题工具）
        self.tool_manager = ToolManager(rag_agent=self)

        """
        TODO: 实现并调整系统提示词，使其符合课程助教的角色和回答策略
        """
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
        self.system_prompt = """你是一位友好、严谨且专业的智能课程助教。
        你的任务是根据提供的【课程内容】来回答学生的问题。

        **回答策略（优先级顺序）：**
        1. **优先使用课程内容**：首先基于【课程内容】中的信息回答问题
        2. **补充联网搜索**：如果【课程内容】信息不足或没有相关内容，才使用联网搜索获取补充信息
        3. **直接回答**：对于不涉及课程知识的一般性问题（如时间、简单计算），直接回答无需追溯来源

        **图片输入说明：**
        - 当用户提交图片时，系统会先使用AI视觉模型分析图片内容，生成文字描述
        - 图片描述会包含在查询中，帮助你更好地理解用户的问题
        - 你应该将图片描述与课程内容相结合，提供准确、专业的解答

        **智能出题功能：**
        - 在适当的时机，你可以主动询问学生是否需要生成习题来巩固知识点
        - 当学生表达学习需求或完成某个知识点讲解后，你可以建议："需要我为你生成一些练习题来巩固这个知识点吗？"
        - 如果学生同意，你可以调用 `quiz_generation` 工具来生成相关习题
<<<<<<< HEAD
        - 习题应该基于当前对话的主题，难度适中，有详细的解析说明
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
        - 示例调用：quiz_generation(topic="词向量", difficulty="medium", question_type="multiple_choice", num_questions=3)
        - 重要：调用工具后，题目会自动显示在用户界面中，你不需要在回复中重复包含题目内容
        - 你的回复应该简洁地确认题目已生成，引导用户查看界面答题

        回答要求：
        1. **基于事实**：所有回答必须严格基于【课程内容】或者联网搜索中检索到的信息。
        2. **追溯来源**：在回答中使用课程内容时，必须在开头或末尾标注信息来源，格式为：[来源：文件名，页码 X 或 幻灯片 X] 或 [来源：文件名]（若无页码）。如果使用了联网搜索，标注为：[来源：网络搜索结果]。如果有多个来源，请合并或分别标注。
        3. **无法回答**：如果【课程内容】和联网搜索中都找不到足够的信息来回答学生的问题，请基于你自己的认知回答，并在最后告知学生："未寻找到相关课程材料，回答仅供参考，请查阅教材或者询问老师。"
        4. **语气专业**：保持助教的专业、友好和条理清晰的语气。
        """

    # def _construct_search_query(self, current_query: str, chat_history: Optional[List[Dict]] = None) -> str:
    #     """
    #     【新增】使用对话历史来提炼搜索关键词，提升多轮检索精度。
    #     仅在 self.enable_advanced_rag 开启时，才执行多轮增强。
    #     """
    #     if not self.enable_advanced_rag:
    #         return current_query
            
    #     # 排除包含图片描述的增强查询，避免重复嵌套
    #     if current_query.startswith("【用户提交的图片分析结果】"):
    #          return current_query

    #     if not chat_history or len(chat_history) < 2:
    #         return current_query
        
    #     # 提取最近的问答对
    #     last_exchange = chat_history[-2:]
        
    #     # 构造用于 RAG 检索的最终查询
    #     recent_context = f"最近的问题：{last_exchange[0]['content']}，最近的回答：{last_exchange[1]['content']}。"
    #     return f"{recent_context} 学生的新问题是：{current_query}"
    def _construct_search_query(self, current_query: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        【修正】使用对话历史来提炼搜索关键词，提升多轮检索精度。
        """
        if not self.enable_advanced_rag:
            return current_query
            
        # 排除包含图片描述的增强查询，避免重复嵌套
        if current_query.startswith("【用户提交的图片分析结果】"):
             return current_query

        # 检查是否有足够的历史记录
        if not chat_history or len(chat_history) < 2:
            return current_query
        
        # 提取最近的问答对
        # 遍历历史记录，找到最新的 User 和 Assistant 消息
        relevant_history = []
        for msg in reversed(chat_history):
            # 仅考虑 user 和 assistant 角色
            if msg.get('role') in ['user', 'assistant'] and 'content' in msg:
                # 排除工具调用相关的 assistant 消息
                if msg.get('role') == 'assistant' and msg.get('content', '').startswith("🎯 已生成习题"):
                     continue
                
                relevant_history.append(msg)
            if len(relevant_history) >= 2:
                break
        
        # 如果找不到最新的问答对，则返回原始查询
        if len(relevant_history) < 2:
            return current_query
        
        # 格式化上下文
        # relevant_history[0] 是最新的消息
        # 确保顺序是 [最新回复 (Assistant), 最新提问 (User)]
        
        # LLM 提炼 Prompt
        context_for_llm = f"""
        你是一个查询提炼助手。请根据以下对话历史来完善用户的最新查询，以更好地进行RAG检索。
        
        对话历史:
        - 上一次回复（助教）："{relevant_history[0]['content']}"
        - 上一次提问（学生）："{relevant_history[1]['content']}"
        - 用户的最新提问是："{current_query}"

        任务：请提取或重写一个**精确且独立**的检索查询（用于搜索知识库），该查询应结合对话历史中的指代关系或省略信息。
        例如，如果最新提问是"它有什么缺点?"，而上一次提问是"什么是Transformer模型"，那么你应返回"Transformer模型的缺点"。
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": context_for_llm}],
                temperature=0.0, # 确保输出稳定
                max_tokens=200
            )
            enhanced_query = response.choices[0].message.content.strip()
            # 排除引号，防止 JSON 解析问题
            enhanced_query = enhanced_query.strip().replace('"', '') 
            
            print(f"🔄 多轮对话增强查询: {enhanced_query}")
            return enhanced_query
        except Exception as e:
            print(f"❌ 多轮查询增强失败 ({e})，使用原始查询。")
            return current_query

    def _analyze_query_type(self, query: str) -> str:
        """
        【新增】使用 LLM 分析查询意图和类型，以决定最佳检索策略。
        """
        prompt = f"""
        你是一个专业的检索策略分析器。你的任务是根据用户查询的性质和意图，
        在严格限定的三种检索策略中，选择并返回最优化检索结果的那一个。
        分析时请同时考虑查询的**关键词稀有度**和**语义抽象度**。

        --- 策略定义和选择标准 ---

        1. 'DENSE' (密集检索/向量检索):
           - **适用场景：** 查询涉及定义、原理、比较、关系、广义概念或需要深度语义理解。
           - **典型特征：** 句子结构完整，关键词抽象度高。

        2. 'BM25' (稀疏检索/关键词检索):
           - **适用场景：** 查询包含罕见、专业、技术性名词、ID、代码片段或特定数字，且要求精确的字面匹配。
           - **典型特征：** 关键词稀有度高。

        3. 'HYBRID' (混合检索/RRF融合):
           - **适用场景：** 查询模糊、同时包含抽象概念和稀有关键词，或者在多轮对话中使用了代词（如“它”、“这个”）进行指代。
           - **典型特征：** 兼具语义和关键词特征。

        --- 任务和格式要求 ---

        用户查询: "{query}"

        请严格仅返回以下三种字符串之一，不添加任何解释、标点或其他文本：'HYBRID', 'BM25', 'DENSE'
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
        【重构】实现检索策略分派器 (Strategy Dispatcher)。
        新增逻辑：如果 self.enable_advanced_rag 为 False，则强制使用 DENSE 策略。
        """
        # 1. 构造用于检索的增强查询 (该函数内部会根据开关返回原始或增强查询)
        # 注意：这里将 chat_history 传递给 _construct_search_query
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
            # 

        # 2. 策略分派器 (Dispatching logic based on query_type)
        if query_type == 'DENSE':
            # 概念主导或退化策略：纯向量检索
            retrieved_docs = self.vector_store.search_dense(search_query, top_k=top_k)
            print("➡️ 采用纯向量密集检索 (search_dense)")
            
        elif query_type == 'BM25':
            # 关键词主导：纯稀疏检索
            retrieved_docs = self.vector_store.search_bm25(search_query, top_k=top_k)
            print("➡️ 采用纯 BM25 稀疏检索 (search_bm25)")

        elif query_type == 'HYBRID': 
            # 混合检索 (假设 self.vector_store.search 是 HYBRID 实现)
            retrieved_docs = self.vector_store.search(search_query, top_k=top_k)
            print("➡️ 采用 RRF 混合检索 (search)")
        
        else:
            # LLM分析失败时的兜底策略
            if DEFAULT_RETRIEVAL_STRATEGY == "BM25":
                 retrieved_docs = self.vector_store.search_bm25(search_query, top_k=top_k)
            elif DEFAULT_RETRIEVAL_STRATEGY == "DENSE":
                 retrieved_docs = self.vector_store.search_dense(search_query, top_k=top_k)
            else:
                 retrieved_docs = self.vector_store.search(search_query, top_k=top_k)
            print(f"⚠️ LLM 分析失败，回退到 DEFAULT 策略: {DEFAULT_RETRIEVAL_STRATEGY}")
            
        # --- 策略决策结束 ---

        # 3. 格式化检索结果（保持原逻辑不变）
        context_parts = []
        source_set = set()
        
        for doc in retrieved_docs:
            content = doc["content"]
            metadata = doc["metadata"]
            
            filename = metadata.get("filename", "未知文件")
            page_number = metadata.get("page_number", 0)
            
            if page_number and page_number > 0:
                source_label = "页码" if metadata.get("filetype") == ".pdf" else "幻灯片"
                source_info = f"[来源：{filename}, {source_label} {page_number}]"
                source_set.add(f"{filename}, {source_label} {page_number}")
            else:
                source_info = f"[来源：{filename}]"
                source_set.add(filename)
                
            context_parts.append(f"{source_info}\n{content}\n---")

        context_string = "\n".join(context_parts)
        
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

        {query}

        如果【课程内容】无法提供足够的信息，你可以选择使用提供的工具搜索网络信息、进行计算或获取当前时间。
        """

        messages.append({"role": "user", "content": user_text})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tool_manager.get_tool_definitions(),
<<<<<<< HEAD
                tool_choice="auto",  # 让AI自动决定是否调用工具
=======
                tool_choice="auto",
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                temperature=0.7,
                max_tokens=1500
            )

            response_message = response.choices[0].message

<<<<<<< HEAD
            # 检查是否有工具调用
            if response_message.tool_calls:
                # 执行工具调用
                tool_results = self._execute_tool_calls(response_message.tool_calls)

                # 将工具调用结果添加到消息历史
=======
            if response_message.tool_calls:
                tool_results = self._execute_tool_calls(response_message.tool_calls)

>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                messages.append(response_message)
                for tool_result in tool_results:
                    messages.append(tool_result)

<<<<<<< HEAD
                # 第二次调用：基于工具结果生成最终回答
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )

                return final_response.choices[0].message.content
            else:
<<<<<<< HEAD
                # 没有工具调用，直接返回结果
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                return response_message.content

        except Exception as e:
            return f"生成回答时出错: {str(e)}"

    def _execute_tool_calls(self, tool_calls) -> List[Dict]:
<<<<<<< HEAD
        """执行工具调用并返回结果"""
=======
        """执行工具调用并返回结果 (保持原逻辑不变)"""
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
        tool_results = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name

<<<<<<< HEAD
            # 解析工具参数，增加错误处理
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
            try:
                if isinstance(tool_call.function.arguments, str):
                    tool_args = json.loads(tool_call.function.arguments)
                elif isinstance(tool_call.function.arguments, dict):
                    tool_args = tool_call.function.arguments
                else:
                    tool_args = {}
                    print(f"⚠️ 工具参数格式异常: {type(tool_call.function.arguments)}")
            except json.JSONDecodeError as e:
                print(f"❌ 解析工具参数失败: {e}")
                tool_args = {}

            print(f"🔧 执行工具: {tool_name} 参数: {tool_args}")

<<<<<<< HEAD
            # 执行工具
            tool_result = self.tool_manager.execute_tool(tool_name, tool_args)

            # 特殊处理出题工具的结果
            if tool_name == "quiz_generation" and isinstance(tool_result, dict) and "quiz_data" in tool_result:
                # 将题目数据存储到session_state中
=======
            tool_result = self.tool_manager.execute_tool(tool_name, tool_args)

            if tool_name == "quiz_generation" and isinstance(tool_result, dict) and "quiz_data" in tool_result:
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                try:
                    import streamlit as st
                    if not hasattr(st.session_state, 'generated_quiz'):
                        st.session_state.generated_quiz = []
                    st.session_state.generated_quiz.append(tool_result["quiz_data"])
                    print(f"📚 已将 {len(tool_result['quiz_data']['questions'])} 道题目存储到UI")

<<<<<<< HEAD
                    # 同时保存习题生成记录到对话历史
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                    quiz_generation_record = {
                        "role": "assistant",
                        "content": f"🎯 已生成习题：{tool_result['quiz_data']['topic']} - {len(tool_result['quiz_data']['questions'])}道题目",
                        "quiz_generation": {
                            "topic": tool_result["quiz_data"]["topic"],
                            "difficulty": tool_result["quiz_data"]["difficulty"],
                            "question_type": tool_result["quiz_data"]["question_type"],
                            "num_questions": len(tool_result["quiz_data"]["questions"]),
                            "questions": tool_result["quiz_data"]["questions"],
                            "timestamp": datetime.now().isoformat()
                        }
                    }

<<<<<<< HEAD
                    # 添加到对话历史
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                    if not hasattr(st.session_state, 'chat_history'):
                        st.session_state.chat_history = []
                    st.session_state.chat_history.append(quiz_generation_record)

                except ImportError:
<<<<<<< HEAD
                    # 非Streamlit环境，跳过UI更新
                    pass

                # 使用消息部分作为工具结果
=======
                    pass

>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                tool_content = tool_result["message"]
            else:
                tool_content = tool_result

<<<<<<< HEAD
            # 格式化工具结果消息
=======
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
            tool_result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content
            }

            tool_results.append(tool_result_message)

        return tool_results

    def answer_question(
        self, query: str, chat_history: Optional[List[Dict]] = None, top_k: int = TOP_K
    ) -> str:
        """回答问题"""
        
        # 【修改】传入 chat_history 以支持多轮检索增强和策略分派
        context, retrieved_docs = self.retrieve_context(query, chat_history=chat_history, top_k=top_k)

        if not context:
            context = "（未检索到特别相关的课程材料）"

        answer = self.generate_response(query, context, chat_history)

        return answer

    def answer_image_question(
        self,
        query: str,
        image_base64: str,
        chat_history: Optional[List[Dict]] = None,
        top_k: int = TOP_K
    ) -> str:
<<<<<<< HEAD
        """回答包含图片的问题

        参数:
            query: 用户关于图片的问题
            image_base64: 图片的Base64编码
            chat_history: 对话历史
            top_k: 检索文档数量

        返回:
            生成的回答
        """
=======
        """回答包含图片的问题"""
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
        try:
            # 1. 使用Qwen-VL分析图片，生成文字描述
            print("🖼️ 正在分析图片...")
            image_description = self._analyze_image_with_vl(image_base64)

            if not image_description:
                return "❌ 图片分析失败，请检查图片格式或重试。"

            # 2. 将图片描述和用户问题合并，构造新的查询
            enhanced_query = f"""
<<<<<<< HEAD
【用户提交的图片分析结果】
{image_description}

【用户问题】
{query}

请基于用户提交的图片分析结果和相关课程资料，专业地回答用户的问题。
"""

            # 3. 使用RAG流程回答问题
            print("🔍 正在检索相关课程内容...")
            context, retrieved_docs = self.retrieve_context(enhanced_query, top_k=top_k)
=======
            【用户提交的图片分析结果】
            {image_description}

            【用户问题】
            {query}

            请基于用户提交的图片分析结果和相关课程资料，专业地回答用户的问题。
            """

            # 3. 使用RAG流程回答问题
            print("🔍 正在检索相关课程内容...")
            # 【修改】传入 chat_history 以支持多轮检索增强和策略分派
            context, retrieved_docs = self.retrieve_context(enhanced_query, chat_history=chat_history, top_k=top_k)
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63

            if not context:
                context = "（未检索到特别相关的课程材料）"

            # 4. 生成最终回答
            print("🤔 正在生成回答...")
            answer = self.generate_response(enhanced_query, context, chat_history)

            return answer

        except Exception as e:
            error_msg = f"图片问答处理失败: {str(e)}"
            print(f"❌ {error_msg}")
            return f"❌ {error_msg}"

    def _analyze_image_with_vl(self, image_base64: str) -> str:
<<<<<<< HEAD
        """使用Qwen-VL分析图片，返回文字描述"""
        try:
            # 直接使用image_processor的analyze_single_image方法
            result = self.image_processor.analyze_single_image(image_base64, "用户上传图片")

            # 提取纯描述内容（去掉格式化前缀）
            if result.startswith("--- 用户上传图片 分析结果 ---"):
                # 去掉格式化前缀，只保留分析结果
=======
        """使用Qwen-VL分析图片，返回文字描述 (保持原逻辑不变)"""
        try:
            result = self.image_processor.analyze_single_image(image_base64, "用户上传图片")

            if result.startswith("--- 用户上传图片 分析结果 ---"):
>>>>>>> 4ce53f2541db68d46cfaf9419f0cd50b06b35b63
                lines = result.strip().split('\n')
                if len(lines) > 1:
                    return '\n'.join(lines[1:]).strip()

            return result.strip()

        except Exception as e:
            print(f"图片分析失败: {e}")
            return None

    def chat(self) -> None:
        """交互式对话 (保持原逻辑不变)"""
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

                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": answer})

            except Exception as e:
                print(f"\n错误: {str(e)}")