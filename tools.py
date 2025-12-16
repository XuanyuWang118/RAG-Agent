import json
import time
from typing import List, Dict, Any
from datetime import datetime
import re

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

from config import TAVILY_API_KEY


class ToolManager:
    """工具管理器"""

    def __init__(self):
        self.tools = {
            "web_search": WebSearchTool(),
            "calculator": CalculatorTool(),
            "current_time": CurrentTimeTool(),
        }

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
            }
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """执行指定的工具"""
        if tool_name not in self.tools:
            return f"错误：未知工具 '{tool_name}'"

        try:
            tool = self.tools[tool_name]
            return tool.execute(parameters)
        except Exception as e:
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


# 全局工具管理器实例
tool_manager = ToolManager()
