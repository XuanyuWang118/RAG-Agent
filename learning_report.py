"""
学习报告生成器
负责分析对话内容，生成学习总结报告
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from rag_agent import RAGAgent


class LearningReportGenerator:
    """学习报告生成器"""

    def __init__(self, rag_agent: RAGAgent):
        self.rag_agent = rag_agent

    def generate_learning_report(self, chat_history: List[Dict], chat_title: str = "") -> Dict[str, Any]:
        """
        生成学习报告

        Args:
            chat_history: 对话历史记录
            chat_title: 对话标题

        Returns:
            学习报告字典
        """
        try:
            # 1. 预处理对话历史
            conversation_text = self._format_conversation_history(chat_history)

            if not conversation_text.strip():
                return {
                    "success": False,
                    "error": "对话内容为空，无法生成学习报告"
                }

            # 2. 分析对话内容
            analysis_result = self._analyze_conversation(conversation_text)

            if not analysis_result:
                return {
                    "success": False,
                    "error": "对话分析失败"
                }

            # 3. 生成结构化报告
            report = self._create_structured_report(analysis_result, chat_title, chat_history)

            return {
                "success": True,
                "report": report
            }

        except Exception as e:
            print(f"生成学习报告失败: {e}")
            return {
                "success": False,
                "error": f"生成报告失败: {str(e)}"
            }

    def _format_conversation_history(self, chat_history: List[Dict]) -> str:
        """格式化对话历史为文本"""
        formatted_lines = []

        for message in chat_history:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                formatted_lines.append(f"用户: {content}")
            elif role == "assistant":
                formatted_lines.append(f"助手: {content}")

        return "\n\n".join(formatted_lines)

    def _analyze_conversation(self, conversation_text: str) -> Optional[Dict[str, Any]]:
        """使用AI分析对话内容"""
        try:
            analysis_prompt = f"""
请仔细分析以下对话内容，从学习者和助手的角度进行深入分析：

【对话内容】
{conversation_text}

请从以下几个维度进行分析：

1. **核心知识点**：对话中涉及的主要概念、原理和技术点
2. **用户困惑点**：学习者在学习过程中表现出的疑问、困难或不理解的地方
3. **学习进度评估**：学习者对相关知识的掌握程度（初学、理解中、掌握、深化）
4. **重点难点**：需要特别关注的知识点或容易混淆的概念
5. **学习建议**：针对学习者的困惑，给出具体的学习建议和改进方向

请用JSON格式返回分析结果，格式如下：
{{
    "knowledge_points": ["知识点1", "知识点2", ...],
    "confusion_points": ["困惑点1", "困惑点2", ...],
    "learning_progress": "学习进度描述",
    "key_difficulties": ["难点1", "难点2", ...],
    "learning_suggestions": ["建议1", "建议2", ...],
    "overall_summary": "总体学习情况总结"
}}
"""

            # 使用RAG Agent进行分析（不使用检索，只用生成能力）
            analysis_result = self.rag_agent.generate_response(
                query=analysis_prompt,
                context="",  # 不使用外部上下文，只分析对话内容
                chat_history=[]  # 不使用对话历史，避免干扰
            )

            # 尝试解析JSON结果
            try:
                # 提取JSON部分
                json_start = analysis_result.find('{')
                json_end = analysis_result.rfind('}') + 1

                if json_start != -1 and json_end != -1:
                    json_str = analysis_result[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # 如果没有找到JSON，创建默认结构
                    return self._create_default_analysis(analysis_result)

            except json.JSONDecodeError:
                # JSON解析失败，创建默认结构
                return self._create_default_analysis(analysis_result)

        except Exception as e:
            print(f"对话分析失败: {e}")
            return None

    def _create_default_analysis(self, raw_analysis: str) -> Dict[str, Any]:
        """创建默认分析结构"""
        return {
            "knowledge_points": ["对话中涉及的知识点"],
            "confusion_points": ["需要进一步澄清的问题"],
            "learning_progress": "正在学习中",
            "key_difficulties": ["关键概念理解"],
            "learning_suggestions": ["建议继续深入学习"],
            "overall_summary": raw_analysis[:500] + "..." if len(raw_analysis) > 500 else raw_analysis
        }

    def _create_structured_report(self, analysis: Dict[str, Any], chat_title: str, chat_history: List[Dict]) -> Dict[str, Any]:
        """创建结构化的学习报告"""
        report = {
            "title": f"学习报告 - {chat_title or '未命名对话'}",
            "generated_at": datetime.now().isoformat(),
            "conversation_info": {
                "title": chat_title,
                "message_count": len(chat_history),
                "duration": self._estimate_conversation_duration(chat_history)
            },
            "analysis": {
                "knowledge_points": analysis.get("knowledge_points", []),
                "confusion_points": analysis.get("confusion_points", []),
                "learning_progress": analysis.get("learning_progress", "未知"),
                "key_difficulties": analysis.get("key_difficulties", []),
                "learning_suggestions": analysis.get("learning_suggestions", []),
                "overall_summary": analysis.get("overall_summary", "")
            },
            "metadata": {
                "report_type": "learning_summary",
                "source": "conversation_analysis",
                "version": "1.0"
            }
        }

        return report

    def _estimate_conversation_duration(self, chat_history: List[Dict]) -> str:
        """估算对话持续时间"""
        if len(chat_history) < 2:
            return "短暂对话"

        # 这里可以根据时间戳估算，暂时基于消息数量估算
        message_count = len(chat_history)

        if message_count <= 4:
            return "短暂学习讨论"
        elif message_count <= 10:
            return "中等长度学习讨论"
        else:
            return "深入学习讨论"

    def save_report_to_database(self, report: Dict[str, Any]) -> bool:
        """
        将学习报告保存到向量数据库

        Args:
            report: 学习报告字典

        Returns:
            保存是否成功
        """
        try:
            # 将报告转换为文档格式
            report_content = self._format_report_for_storage(report)

            report_document = {
                "content": report_content,
                "filename": f"learning_report_{report['generated_at'][:19].replace(':', '-')}.json",
                "filepath": f"generated://learning_reports/{report['generated_at'][:10]}",
                "filetype": ".json",
                "page_number": 0,
                "metadata": {
                    "report_type": "learning_summary",
                    "generated_at": report["generated_at"],
                    "conversation_title": report["conversation_info"]["title"],
                    "knowledge_points_count": len(report["analysis"]["knowledge_points"]),
                    "confusion_points_count": len(report["analysis"]["confusion_points"])
                }
            }

            # 添加到向量数据库
            success = self.rag_agent.vector_store.add_documents_incremental([report_document])

            if success:
                print(f"学习报告已成功添加到知识库: {report['title']}")

            return success

        except Exception as e:
            print(f"保存学习报告失败: {e}")
            return False

    def _format_report_for_storage(self, report: Dict[str, Any]) -> str:
        """将报告格式化为适合存储的文本"""
        content_parts = []

        content_parts.append(f"# {report['title']}")
        content_parts.append(f"生成时间: {report['generated_at'][:19]}")
        content_parts.append("")

        content_parts.append("## 对话信息")
        content_parts.append(f"- 对话标题: {report['conversation_info']['title']}")
        content_parts.append(f"- 消息数量: {report['conversation_info']['message_count']}")
        content_parts.append(f"- 对话时长: {report['conversation_info']['duration']}")
        content_parts.append("")

        content_parts.append("## 学习分析")
        content_parts.append(f"**学习进度**: {report['analysis']['learning_progress']}")
        content_parts.append("")

        content_parts.append("**核心知识点**:")
        for point in report['analysis']['knowledge_points']:
            content_parts.append(f"- {point}")
        content_parts.append("")

        content_parts.append("**用户困惑点**:")
        for point in report['analysis']['confusion_points']:
            content_parts.append(f"- {point}")
        content_parts.append("")

        content_parts.append("**重点难点**:")
        for point in report['analysis']['key_difficulties']:
            content_parts.append(f"- {point}")
        content_parts.append("")

        content_parts.append("**学习建议**:")
        for suggestion in report['analysis']['learning_suggestions']:
            content_parts.append(f"- {suggestion}")
        content_parts.append("")

        content_parts.append("## 总体总结")
        content_parts.append(report['analysis']['overall_summary'])

        return "\n".join(content_parts)
