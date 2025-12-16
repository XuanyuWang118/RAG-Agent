"""
习题生成器
根据对话内容智能生成习题并提供答案解析
"""

import json
from typing import List, Dict, Any, Optional
from rag_agent import RAGAgent


class QuizGenerator:
    """智能习题生成器"""

    def __init__(self, rag_agent: RAGAgent):
        self.rag_agent = rag_agent

    def analyze_conversation_for_quiz(self, chat_history: List[Dict]) -> Dict[str, Any]:
        """
        分析对话内容，判断是否适合出题以及出题策略

        Args:
            chat_history: 对话历史

        Returns:
            分析结果，包含是否适合出题、推荐主题、难度等
        """
        try:
            # 格式化对话历史
            conversation_text = self._format_conversation(chat_history)

            if len(conversation_text) < 100:
                return {"suitable": False, "reason": "对话内容太短"}

            analysis_prompt = f"""
请分析以下学习对话，判断是否适合生成练习题：

【对话内容】
{conversation_text}

请从以下方面分析：
1. 是否涉及具体知识点
2. 用户是否在学习新概念
3. 对话是否有实质性内容
4. 推荐的出题主题
5. 合适的难度级别

返回JSON格式：
{{
    "suitable": true/false,
    "reason": "判断理由",
    "recommended_topic": "推荐主题",
    "difficulty": "easy/medium/hard",
    "confidence": 0.0-1.0
}}
"""

            analysis_result = self.rag_agent.generate_response(
                query=analysis_prompt,
                context="",
                chat_history=[]
            )

            # 解析JSON结果
            try:
                json_start = analysis_result.find('{')
                json_end = analysis_result.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = analysis_result[json_start:json_end]
                    result = json.loads(json_str)
                    return result
                else:
                    return {"suitable": False, "reason": "分析失败"}
            except:
                return {"suitable": False, "reason": "解析失败"}

        except Exception as e:
            print(f"对话分析失败: {e}")
            return {"suitable": False, "reason": f"分析异常: {str(e)}"}

    def generate_quiz_questions(self, topic: str, difficulty: str = "medium",
                               question_count: int = 3) -> List[Dict[str, Any]]:
        """
        根据主题生成习题

        Args:
            topic: 主题
            difficulty: 难度 (easy/medium/hard)
            question_count: 题目数量

        Returns:
            习题列表
        """
        try:
            # 首先检索相关课程内容作为上下文
            context_docs = self.rag_agent.retrieve_context(f"{topic} 相关知识", top_k=5)
            context_text = "\n".join([doc.get("content", "") for doc in context_docs])

            quiz_prompt = f"""
根据以下课程内容，为"{topic}"主题生成{question_count}道{difficulty}难度的练习题。

【课程内容参考】
{context_text[:2000]}

请生成包含题干、选项、正确答案和详细解析的题目。

每道题目格式要求：
题干：[具体问题]
A: [选项A]
B: [选项B]
C: [选项C]
D: [选项D]
正确答案：[A/B/C/D]
解析：[详细解析说明，引用相关知识点]

题目要：
- 考察关键概念的理解
- 难度适中，适合学习巩固
- 解析要详细，有助于理解

请直接返回题目，不要其他说明。
"""

            quiz_result = self.rag_agent.generate_response(
                query=quiz_prompt,
                context=context_text,
                chat_history=[]
            )

            # 解析生成的题目
            questions = self._parse_quiz_questions(quiz_result, question_count)

            return questions

        except Exception as e:
            print(f"生成习题失败: {e}")
            return []

    def _format_conversation(self, chat_history: List[Dict]) -> str:
        """格式化对话历史"""
        formatted_lines = []
        for message in chat_history[-10:]:  # 只分析最近10条消息
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                formatted_lines.append(f"学生: {content}")
            elif role == "assistant":
                formatted_lines.append(f"老师: {content}")

        return "\n".join(formatted_lines)

    def _parse_quiz_questions(self, quiz_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """解析生成的习题文本"""
        questions = []

        try:
            # 按题目分割
            question_blocks = quiz_text.split("\n\n")

            for block in question_blocks:
                if not block.strip():
                    continue

                lines = block.strip().split("\n")
                if len(lines) < 6:  # 最少需要题干+4个选项+答案+解析
                    continue

                question = {
                    "question": "",
                    "options": {"A": "", "B": "", "C": "", "D": ""},
                    "correct_answer": "",
                    "explanation": "",
                    "type": "multiple_choice"
                }

                current_line = 0

                # 解析题干
                if lines[current_line].startswith("题干：") or lines[current_line].startswith("题目："):
                    question["question"] = lines[current_line].replace("题干：", "").replace("题目：", "").strip()
                    current_line += 1

                # 解析选项
                option_mapping = {"A": "A:", "B": "B:", "C": "C:", "D": "D:"}
                for option_key, option_prefix in option_mapping.items():
                    if current_line < len(lines) and lines[current_line].startswith(option_prefix):
                        question["options"][option_key] = lines[current_line].replace(option_prefix, "").strip()
                        current_line += 1

                # 解析正确答案
                if current_line < len(lines) and lines[current_line].startswith("正确答案："):
                    answer_text = lines[current_line].replace("正确答案：", "").strip()
                    question["correct_answer"] = answer_text
                    current_line += 1

                # 解析答案解析
                if current_line < len(lines) and lines[current_line].startswith("解析："):
                    explanation = lines[current_line].replace("解析：", "").strip()
                    # 收集剩余的解析内容
                    for i in range(current_line + 1, len(lines)):
                        if not lines[i].startswith("题干：") and not any(lines[i].startswith(prefix) for prefix in ["A:", "B:", "C:", "D:", "正确答案：", "解析："]):
                            explanation += " " + lines[i].strip()
                        else:
                            break
                    question["explanation"] = explanation

                # 验证题目完整性
                if (question["question"] and
                    all(question["options"].values()) and
                    question["correct_answer"] and
                    question["explanation"]):
                    questions.append(question)

                if len(questions) >= expected_count:
                    break

        except Exception as e:
            print(f"解析习题失败: {e}")

        return questions[:expected_count]  # 确保不超过预期数量

    def check_answer(self, question: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        """
        检查用户答案

        Args:
            question: 题目字典
            user_answer: 用户选择的答案

        Returns:
            检查结果
        """
        is_correct = user_answer.upper() == question["correct_answer"].upper()

        return {
            "is_correct": is_correct,
            "user_answer": user_answer.upper(),
            "correct_answer": question["correct_answer"].upper(),
            "explanation": question["explanation"],
            "feedback": "✅ 回答正确！" if is_correct else f"❌ 回答错误，正确答案是：{question['correct_answer']}"
        }

    def get_quiz_statistics(self, questions: List[Dict], user_answers: Dict[int, str]) -> Dict[str, Any]:
        """
        计算答题统计

        Args:
            questions: 题目列表
            user_answers: 用户答案字典 {question_index: answer}

        Returns:
            统计结果
        """
        total_questions = len(questions)
        answered_count = len(user_answers)
        correct_count = 0

        for i, question in enumerate(questions):
            if i in user_answers:
                if user_answers[i].upper() == question["correct_answer"].upper():
                    correct_count += 1

        accuracy = correct_count / answered_count if answered_count > 0 else 0

        return {
            "total_questions": total_questions,
            "answered_count": answered_count,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "accuracy_percentage": f"{accuracy:.1%}"
        }
