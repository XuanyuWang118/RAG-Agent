import json
import time
from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime
import re

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

from config import TAVILY_API_KEY, OPENAI_API_KEY, OPENAI_API_BASE, MODEL_NAME

if TYPE_CHECKING:
    from rag_agent import RAGAgent


class ToolManager:
    """工具管理器"""

    def __init__(self, rag_agent = None):
        self.rag_agent = rag_agent
        self.tools = {
            "web_search": WebSearchTool(),
            "calculator": CalculatorTool(),
            "current_time": CurrentTimeTool(),
        }

        # 延迟初始化quiz_generation工具，避免循环导入
        if rag_agent is not None:
            from rag_agent import RAGAgent  # 延迟导入
            self.tools["quiz_generation"] = QuizGenerationTool(rag_agent)

    def get_tool_definitions(self) -> List[Dict]:
        """获取所有工具的定义，用于OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "搜索网络信息，获取最新的网络搜索结果。适用于查找当前事件、最新资讯或网络上的专业知识。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词或问题"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "返回结果数量，默认5个",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算。适用于算术运算、数学表达式计算。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "数学表达式，如'2+3*4'、'sqrt(16)'、'sin(30)'等"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "current_time",
                    "description": "获取当前时间和日期。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "quiz_generation",
                    "description": "根据课程内容生成习题。用于创建学习测试题目，帮助巩固知识点。会自动生成包含解析的题目，并显示在用户界面中供交互答题。示例：当学生讨论完'词向量'概念后，可以调用此工具生成相关选择题进行巩固练习。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "习题主题，必须基于当前对话内容，如'词向量'、'神经网络'、'序列标注'、'Transformer架构'等。建议使用对话中提到的具体概念。"
                            },
                            "difficulty": {
                                "type": "string",
                                "description": "题目难度，根据学生当前学习进度选择：'easy'(基础概念复习)、'medium'(中等难度，适合巩固)、'hard'(挑战性，深入理解)",
                                "enum": ["easy", "medium", "hard"],
                                "default": "medium"
                            },
                            "question_type": {
                                "type": "string",
                                "description": "题目类型：'multiple_choice'(选择题，A/B/C/D选项，适合概念辨识)、'true_false'(判断题，对错判断，适合快速检验理解)",
                                "enum": ["multiple_choice", "true_false"],
                                "default": "multiple_choice"
                            },
                            "num_questions": {
                                "type": "integer",
                                "description": "生成题目数量，默认3道",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 10
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, parameters) -> str:
        """执行指定的工具"""
        if tool_name not in self.tools:
            return f"错误：未知工具 '{tool_name}'"

        # 验证参数格式
        if not isinstance(parameters, dict):
            return f"错误：工具参数必须是字典格式，收到: {type(parameters)}"

        try:
            tool = self.tools[tool_name]
            return tool.execute(parameters)
        except Exception as e:
            print(f"工具 {tool_name} 执行失败: {e}")
            return f"工具执行失败：{str(e)}"


class WebSearchTool:
    """网络搜索工具（基于Tavily）"""

    def __init__(self):
        try:
            self.client = TavilyClient(api_key=TAVILY_API_KEY) if TavilyClient else None
        except Exception as e:
            print(f"初始化Tavily客户端失败: {e}")
            self.client = None
        self.max_retries = 3

    def execute(self, parameters: Dict[str, Any]) -> str:
        """执行网络搜索"""
        query = parameters.get("query", "")
        num_results = parameters.get("num_results", 5)

        if not query:
            return "错误：搜索关键词不能为空"

        if not self.client:
            return "错误：Tavily搜索客户端未初始化"

        try:
            # 执行搜索
            # 使用advanced搜索深度以获得更好的结果
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=min(num_results, 10),  # Tavily最大支持10个结果
                include_answer=True,  # 包含AI生成的答案
                include_raw_content=False,  # 不包含原始HTML
                include_images=False  # 不包含图片
            )

            if not response or not response.get('results'):
                return f"未找到关于'{query}'的搜索结果"

            results = response['results']

            # 格式化结果
            formatted_results = []

            # 如果有AI生成的答案，先添加
            if response.get('answer'):
                formatted_results.append(
                    f"**AI摘要**: {response['answer']}\n"
                )

            # 添加搜索结果
            for i, result in enumerate(results, 1):
                title = result.get('title', '无标题')
                url = result.get('url', '')
                content = result.get('content', '')

                formatted_results.append(
                    f"{i}. **{title}**\n"
                    f"   链接：{url}\n"
                    f"   摘要：{content[:200]}..."
                )

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"搜索失败：{str(e)}"


class CalculatorTool:
    """计算器工具"""

    def __init__(self):
        # 允许使用的数学函数
        self.allowed_functions = {
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
            'sinh', 'cosh', 'tanh',
            'sqrt', 'log', 'log10', 'exp',
            'abs', 'round', 'ceil', 'floor',
            'pi', 'e', 'tau'
        }

    def execute(self, parameters: Dict[str, Any]) -> str:
        """执行数学计算"""
        expression = parameters.get("expression", "").strip()

        if not expression:
            return "错误：数学表达式不能为空"

        try:
            # 安全检查：只允许基本数学运算和预定义函数
            if not self._is_safe_expression(expression):
                return "错误：表达式包含不允许的运算或函数"

            # 使用eval执行计算（在安全检查后）
            result = eval(expression, {"__builtins__": {}}, self._get_math_context())

            return f"计算结果：{expression} = {result}"

        except Exception as e:
            return f"计算失败：{str(e)}"

    def _is_safe_expression(self, expression: str) -> bool:
        """检查表达式是否安全"""
        # 移除所有空白字符
        expr = re.sub(r'\s+', '', expression)

        # 检查是否只包含允许的字符
        allowed_chars = set('0123456789.+-*/()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
        if not all(c in allowed_chars for c in expr):
            return False

        # 检查是否包含危险的关键字
        dangerous_keywords = ['import', 'exec', 'eval', 'open', '__', 'class', 'def']
        for keyword in dangerous_keywords:
            if keyword in expr.lower():
                return False

        return True

    def _get_math_context(self) -> Dict:
        """获取安全的数学上下文"""
        import math
        context = {}

        # 添加math模块的函数
        for name in self.allowed_functions:
            if hasattr(math, name):
                context[name] = getattr(math, name)

        return context


class CurrentTimeTool:
    """当前时间工具"""

    def execute(self, parameters: Dict[str, Any] = None) -> str:
        """获取当前时间"""
        now = datetime.now()

        # 北京时间（UTC+8）
        beijing_time = now  # 假设服务器在北京时区

        result = (
            f"当前时间：{beijing_time.strftime('%Y年%m月%d日 %H:%M:%S')}\n"
            f"日期：{beijing_time.strftime('%Y-%m-%d')}\n"
            f"星期：{beijing_time.strftime('%A')}\n"
            f"时间戳：{int(beijing_time.timestamp())}"
        )

        return result


class QuizGenerationTool:
    """习题生成工具"""

    def __init__(self, rag_agent):
        self.rag_agent = rag_agent

    def execute(self, parameters: Dict[str, Any]) -> str:
        """生成习题"""
        topic = parameters.get("topic", "")
        difficulty = parameters.get("difficulty", "medium")
        question_type = parameters.get("question_type", "multiple_choice")
        num_questions = parameters.get("num_questions", 3)

        print(f"🎯 生成习题 - 主题: {topic}, 难度: {difficulty}, 类型: {question_type}, 数量: {num_questions}")

        if not topic:
            return "错误：必须提供习题主题。示例：'词向量'、'神经网络'、'序列标注'等"

        try:
            print(f"📚 获取 '{topic}' 相关上下文...")
            # 获取相关课程内容作为上下文
            try:
                context_string, retrieved_docs = self.rag_agent.retrieve_context(
                    query=f"{topic} 相关概念和知识点",
                    top_k=5
                )
                print(f"📖 上下文检索完成，context_string长度: {len(context_string)}, retrieved_docs长度: {len(retrieved_docs)}")

                # 使用retrieved_docs而不是context_string
                context_docs = retrieved_docs

            except Exception as context_error:
                print(f"⚠️ 上下文检索失败: {context_error}，将使用空上下文继续")
                context_docs = []

            context_text = ""
            if context_docs:
                # 使用前10个最相关的文档片段
                selected_docs = context_docs[:10]
                context_parts = []

                for doc in selected_docs:
                    if isinstance(doc, dict):
                        content = doc.get("content", "")
                    else:
                        content = str(doc)

                    if content and content.strip():
                        # 限制每个文档的内容长度
                        if len(content) > 800:
                            content = content[:800] + "..."
                        context_parts.append(content)

                context_text = "\n\n".join(context_parts)
                print(f"📖 使用 {len(context_parts)} 个文档片段作为上下文")
            else:
                print("⚠️ 未找到相关上下文文档，将基于通用知识生成题目")

            print(f"🔨 构建习题生成prompt...")
            # 构建生成习题的prompt
            quiz_prompt = self._build_quiz_prompt(
                topic=topic,
                context=context_text,
                difficulty=difficulty,
                question_type=question_type,
                num_questions=num_questions
            )

            print(f"🤖 调用AI生成习题内容...")
            # 直接调用OpenAI API，避免递归工具调用
            try:
                from config import OPENAI_API_KEY, OPENAI_API_BASE, MODEL_NAME

                messages = [
                    {"role": "system", "content": "你是一个专业的教育内容生成助手，负责生成高质量的习题和解析。"},
                    {"role": "user", "content": quiz_prompt}
                ]

                response = self.rag_agent.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )

                quiz_content = response.choices[0].message.content

            except Exception as ai_error:
                print(f"❌ AI调用失败: {ai_error}")
                return f"生成习题失败：AI调用异常 - {str(ai_error)}"

            print(f"📝 解析生成的习题内容...")
            # 解析生成的习题
            questions = self._parse_quiz_content(quiz_content, question_type)

            if not questions:
                print(f"❌ 解析失败，未生成有效题目")
                return "生成习题失败：无法解析生成的题目内容，请重试"

            print(f"✅ 成功生成 {len(questions)} 道题目")

            # 格式化返回结果
            result = {
                "topic": topic,
                "difficulty": difficulty,
                "question_type": question_type,
                "questions": questions
            }

            # 将结果存储在session_state中，供UI使用
            # 注意：这里不直接导入streamlit，避免在非UI环境中出错
            # 实际的session_state修改需要在UI上下文中进行

            # 返回包含题目的完整结果，让调用者处理存储
            return {
                "message": f"✅ 已生成 {len(questions)} 道关于 '{topic}' 的习题！请查看界面下方的题目区域开始答题。",
                "quiz_data": result,
                "should_display_quiz": True
            }

        except Exception as e:
            return f"生成习题失败：{str(e)}"

    def _build_quiz_prompt(self, topic: str, context: str, difficulty: str,
                          question_type: str, num_questions: int) -> str:
        """构建生成习题的prompt"""

        difficulty_map = {
            "easy": "简单",
            "medium": "中等",
            "hard": "困难"
        }

        type_map = {
            "multiple_choice": "选择题",
            "true_false": "判断题"
        }

        prompt = f"""
请根据以下课程内容，生成 {num_questions} 道{difficulty_map.get(difficulty, '中等')}难度的{type_map.get(question_type, '选择题')}。

课程内容：
{context[:2000] if context else f"关于{topic}的相关知识"}

要求：
1. 题目要基于课程内容或相关知识点
2. 难度要符合要求
3. 每个题目都要有详细的解析说明
"""

        if question_type == "multiple_choice":
            prompt += """
选择题格式要求：
题目：[题干]
A: [选项A]
B: [选项B]
C: [选项C]
D: [选项D]
正确答案：[A/B/C/D]
解析：[详细解析]
---
"""
        elif question_type == "true_false":
            prompt += """
判断题格式要求：
题目：[判断语句]
正确答案：[对/错]
解析：[详细解析]
---
"""

        return prompt

    def _parse_quiz_content(self, content: str, question_type: str) -> List[Dict]:
        """解析生成的习题内容"""
        try:
            questions = []

            # 按题目分割
            question_blocks = content.split("---")
            question_blocks = [block.strip() for block in question_blocks if block.strip()]

            for block in question_blocks:
                if not block:
                    continue

                lines = block.split('\n')
                lines = [line.strip() for line in lines if line.strip()]

                if not lines:
                    continue

                question = {}

                if question_type == "multiple_choice":
                    question = self._parse_multiple_choice(lines)
                elif question_type == "true_false":
                    question = self._parse_true_false(lines)

                if question:
                    questions.append(question)

            return questions[:10]  # 最多返回10道题

        except Exception as e:
            print(f"解析习题内容失败: {e}")
            return []

    def _parse_multiple_choice(self, lines: List[str]) -> Dict:
        """解析选择题"""
        try:
            question_text = ""
            options = {}
            correct_answer = ""
            explanation = ""

            i = 0
            while i < len(lines):
                line = lines[i]

                if line.startswith("题目：") or line.startswith("题目:"):
                    question_text = line.replace("题目：", "").replace("题目:", "").strip()
                elif line.startswith("A:") or line.startswith("A："):
                    options["A"] = line.replace("A:", "").replace("A：", "").strip()
                elif line.startswith("B:") or line.startswith("B："):
                    options["B"] = line.replace("B:", "").replace("B：", "").strip()
                elif line.startswith("C:") or line.startswith("C："):
                    options["C"] = line.replace("C:", "").replace("C：", "").strip()
                elif line.startswith("D:") or line.startswith("D："):
                    options["D"] = line.replace("D:", "").replace("D：", "").strip()
                elif line.startswith("正确答案：") or line.startswith("正确答案:"):
                    correct_answer = line.replace("正确答案：", "").replace("正确答案:", "").strip()
                elif line.startswith("解析：") or line.startswith("解析:"):
                    explanation = line.replace("解析：", "").replace("解析:", "").strip()
                    # 收集后续的解析内容
                    i += 1
                    while i < len(lines) and not any(lines[i].startswith(prefix) for prefix in ["题目", "A:", "B:", "C:", "D:", "正确答案", "---"]):
                        explanation += " " + lines[i]
                        i += 1
                    i -= 1  # 回退一个，因为外层循环会+1

                i += 1

            if question_text and options and correct_answer:
                return {
                    "type": "multiple_choice",
                    "question": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "explanation": explanation
                }

        except Exception as e:
            print(f"解析选择题失败: {e}")

        return {}

    def _parse_true_false(self, lines: List[str]) -> Dict:
        """解析判断题"""
        try:
            question_text = ""
            correct_answer = ""
            explanation = ""

            for line in lines:
                if line.startswith("题目：") or line.startswith("题目:"):
                    question_text = line.replace("题目：", "").replace("题目:", "").strip()
                elif line.startswith("正确答案：") or line.startswith("正确答案:"):
                    answer = line.replace("正确答案：", "").replace("正确答案:", "").strip()
                    correct_answer = "对" if "对" in answer else "错"
                elif line.startswith("解析：") or line.startswith("解析:"):
                    explanation = line.replace("解析：", "").replace("解析:", "").strip()

            if question_text and correct_answer:
                return {
                    "type": "true_false",
                    "question": question_text,
                    "correct_answer": correct_answer,
                    "explanation": explanation
                }

        except Exception as e:
            print(f"解析判断题失败: {e}")

        return {}



# 全局工具管理器实例
tool_manager = ToolManager()
