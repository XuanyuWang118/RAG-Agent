import streamlit as st
import os
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional
from rag_agent import RAGAgent
from config import VECTOR_DB_PATH, MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP

# 设置页面配置
st.set_page_config(
    page_title="智能课程助教",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 对话历史存储目录
CHAT_HISTORY_DIR = "./chat_history"

# 确保对话历史目录存在
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# 初始化session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "rag_agent" not in st.session_state:
    st.session_state.rag_agent = None

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_list" not in st.session_state:
    st.session_state.chat_list = []

if "upload_counter" not in st.session_state:
    st.session_state.upload_counter = 0

if "knowledge_upload_counter" not in st.session_state:
    st.session_state.knowledge_upload_counter = 0

if "text_input_counter" not in st.session_state:
    st.session_state.text_input_counter = 0

def save_chat_history(chat_id: str, chat_history: list, title: str = None):
    """保存对话历史到文件"""
    if not chat_id:
        return

    # 如果没有标题，从第一条用户消息生成标题
    if not title and chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                title = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
                break
    title = title or f"对话 {chat_id[:8]}"

    chat_data = {
        "id": chat_id,
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "messages": chat_history
    }

    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存对话失败: {e}")
        return False

def load_chat_history(chat_id: str) -> list:
    """从文件加载对话历史"""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
                messages = chat_data.get("messages", [])

                # 历史记录中的题目只在对话历史中显示，不恢复到交互界面
                # 这样避免历史题目重新出现在答题UI中

                return messages
    except Exception as e:
        st.error(f"加载对话失败: {e}")
    return []

def load_chat_list() -> list:
    """加载所有对话列表"""
    chat_list = []
    try:
        for filename in os.listdir(CHAT_HISTORY_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(CHAT_HISTORY_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                        chat_list.append({
                            "id": chat_data["id"],
                            "title": chat_data["title"],
                            "timestamp": chat_data["timestamp"],
                            "message_count": len(chat_data.get("messages", []))
                        })
                except Exception:
                    continue
    except Exception:
        pass

    # 按时间戳排序，最新的在前面
    chat_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return chat_list

def delete_chat_history(chat_id: str):
    """删除指定的对话历史"""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        st.error(f"删除对话失败: {e}")
        return False

def create_new_chat():
    """创建新的对话"""
    chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = chat_id
    st.session_state.chat_history = []
    st.session_state.chat_list = load_chat_list()  # 刷新列表
    return chat_id

def display_chat_message(message):
    """增强的消息显示函数，支持图片信息和历史图片显示"""
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
            if message.get("has_image"):
                st.caption(f"📎 包含图片: {message.get('image_name', '未知')}")
                # 如果消息历史中有图片数据，显示缩略图
                if message.get("image_data"):
                    try:
                        st.image(
                            f"data:image/jpeg;base64,{message['image_data']}",
                            width=100,
                            caption=f"📷 {message.get('image_name', '图片')}"
                        )
                    except Exception as e:
                        st.caption(f"⚠️ 图片显示失败: {e}")
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])

            # 显示题目历史记录
            if "quiz_display" in message:
                quiz_data = message["quiz_display"]
                st.markdown("---")
                st.markdown(f"**🎯 习题回顾：{quiz_data['topic']}**")

                # 显示习题信息
                info_cols = st.columns(3)
                with info_cols[0]:
                    st.metric("题目数量", len(quiz_data["questions"]))
                with info_cols[1]:
                    st.metric("难度", quiz_data["difficulty"])
                with info_cols[2]:
                    st.metric("类型", quiz_data["question_type"])

                # 显示每个题目和答题结果
                answers = quiz_data.get("answers", {})
                for i, question in enumerate(quiz_data["questions"]):
                    question_id = f"q_{i}"
                    user_answer = answers.get(question_id, {})

                    with st.container():
                        st.markdown(f"**第 {i+1} 题：** {question['question']}")

                        # 根据题目类型显示选项
                        if question["type"] == "multiple_choice":
                            options = list(question["options"].values())
                            for j, option in enumerate(options):
                                option_letter = chr(65 + j)  # A, B, C, D...
                                if user_answer and user_answer.get("user_answer") == option_letter:
                                    if user_answer.get("is_correct"):
                                        st.success(f"✅ {option_letter}: {option}")
                                    else:
                                        st.error(f"❌ {option_letter}: {option}")
                                elif user_answer and user_answer.get("correct_answer") == option_letter:
                                    st.info(f"🎯 {option_letter}: {option} (正确答案)")
                                else:
                                    st.write(f"{option_letter}: {option}")

                        elif question["type"] == "true_false":
                            if user_answer and user_answer.get("user_answer") == "对":
                                if user_answer.get("is_correct"):
                                    st.success("✅ 对")
                                else:
                                    st.error("❌ 对")
                            elif user_answer and user_answer.get("user_answer") == "错":
                                if user_answer.get("is_correct"):
                                    st.success("✅ 错")
                                else:
                                    st.error("❌ 错")

                            if user_answer and not user_answer.get("is_correct"):
                                st.info(f"🎯 正确答案：{user_answer.get('correct_answer')}")

                        # 显示解析
                        if user_answer and user_answer.get("is_correct") is not None:
                            with st.expander("📖 查看解析", expanded=False):
                                st.write(question["explanation"])

                    if i < len(quiz_data["questions"]) - 1:
                        st.markdown("---")

            # 显示学习报告
            elif "learning_report" in message:
                report_data = message["learning_report"]
                st.markdown("---")
                st.markdown(f"**📊 {report_data['title']}**")
                st.caption(f"生成时间: {report_data['generated_at'][:19]}")

                # 显示对话统计
                stat_cols = st.columns(2)
                with stat_cols[0]:
                    st.metric("📝 消息数量", report_data['conversation_info']['message_count'])
                with stat_cols[1]:
                    st.metric("⏱️ 对话时长", report_data['conversation_info']['duration'])

                # 显示分析结果
                analysis = report_data['analysis']

                with st.expander("🎯 核心知识点", expanded=False):
                    for point in analysis['knowledge_points']:
                        st.markdown(f"• {point}")

                if analysis['confusion_points']:
                    with st.expander("❓ 用户困惑点", expanded=False):
                        for point in analysis['confusion_points']:
                            st.markdown(f"• {point}")

                with st.expander("📈 学习进度", expanded=False):
                    st.info(analysis['learning_progress'])

                if analysis['learning_suggestions']:
                    with st.expander("💡 学习建议", expanded=False):
                        for suggestion in analysis['learning_suggestions']:
                            st.markdown(f"• {suggestion}")

                with st.expander("📝 总体总结", expanded=True):
                    st.write(analysis['overall_summary'])

def process_uploaded_image(uploaded_file, for_history=False):
    """将上传的图片转换为base64

    参数:
        uploaded_file: 上传的文件对象
        for_history: 是否用于历史记录（会进一步压缩以节省空间）
    """
    from PIL import Image
    import io
    import base64

    try:
        # 读取上传的文件
        image = Image.open(uploaded_file)

        # 根据用途设置不同的压缩参数
        if for_history:
            # 用于历史记录：更小的尺寸和更低的质量以节省空间
            max_size = 150  # 历史记录中显示的小图
            quality = 50    # 更低的质量
        else:
            # 用于AI分析：保持较高品质
            max_size = 1024
            quality = 85

        # 压缩处理
        if image.size[0] > max_size:
            ratio = max_size / image.size[0]
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # 转换为RGB（处理RGBA图片）
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 保存为JPEG格式的bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
        image_bytes = buffer.getvalue()

        return base64.b64encode(image_bytes).decode('utf-8')

    except Exception as e:
        raise ValueError(f"图片处理失败: {e}")

def initialize_rag_agent():
    """初始化RAG Agent"""
    if not os.path.exists(VECTOR_DB_PATH):
        st.error("❌ 向量数据库不存在！请先运行数据处理脚本。")
        return None

    try:
        agent = RAGAgent(model=MODEL_NAME)
        count = agent.vector_store.get_collection_count()
        if count == 0:
            st.error("❌ 知识库为空！请先运行数据处理脚本。")
            return None
        return agent
    except Exception as e:
        st.error(f"❌ 初始化失败: {e}")
        return None

def main():
    # 初始化对话列表（如果还没有加载）
    if not st.session_state.chat_list:
        st.session_state.chat_list = load_chat_list()

    # 初始化对话（如果还没有当前对话）
    if not st.session_state.current_chat_id:
        create_new_chat()

    # 侧边栏
    with st.sidebar:
        st.title("🎓 智能课程助教")
        st.markdown("---")

        # 初始化按钮
        if st.button("🔄 初始化系统", type="primary"):
            with st.spinner("正在初始化RAG系统..."):
                st.session_state.rag_agent = initialize_rag_agent()
            if st.session_state.rag_agent:
                st.success("✅ 系统初始化成功！")
            else:
                st.error("❌ 系统初始化失败！")

        # 系统状态
        if st.session_state.rag_agent:
            st.markdown("### 📊 系统状态")
            try:
                doc_count = st.session_state.rag_agent.vector_store.get_collection_count()
                st.metric("知识库文档数", doc_count)
                st.success("🟢 系统运行正常")
            except Exception as e:
                st.error(f"获取状态失败: {e}")
        else:
            st.warning("⚠️ 系统未初始化")

        st.markdown("---")

        # 对话管理
        st.markdown("### 💬 对话管理")

        # 新建对话
        if st.button("➕ 新建对话", type="secondary"):
            create_new_chat()
            st.rerun()

        # 清空当前对话
        if st.button("🗑️ 清空当前对话", type="secondary", help="清空并删除当前对话的所有记录"):
            if st.session_state.current_chat_id:
                # 彻底删除对话记录文件
                if delete_chat_history(st.session_state.current_chat_id):
                    st.success("✅ 当前对话已删除")
                else:
                    st.error("❌ 删除对话失败")

                # 清空当前对话ID
                st.session_state.current_chat_id = None

            # 清空内存中的对话状态
            st.session_state.chat_history = []

            # 清空题目相关状态
            if 'generated_quiz' in st.session_state:
                st.session_state.generated_quiz = []
            if 'quiz_answers' in st.session_state:
                st.session_state.quiz_answers = {}
            if 'quiz_show_results' in st.session_state:
                st.session_state.quiz_show_results = {}

            # 刷新对话列表
            st.session_state.chat_list = load_chat_list()
            st.rerun()

        # 生成学习报告
        if st.button("📊 生成学习报告", type="secondary"):
            if not st.session_state.chat_history:
                st.warning("⚠️ 当前没有对话内容，无法生成学习报告")
            else:
                with st.spinner("🤔 正在分析对话内容并生成学习报告..."):
                    try:
                        from learning_report import LearningReportGenerator

                        # 创建学习报告生成器
                        report_generator = LearningReportGenerator(st.session_state.rag_agent)

                        # 计算当前对话标题
                        report_title = "未开始对话"
                        if st.session_state.current_chat_id:
                            # 在对话列表中查找当前对话的标题
                            for chat in st.session_state.chat_list:
                                if chat["id"] == st.session_state.current_chat_id:
                                    report_title = chat["title"]
                                    break
                        elif st.session_state.chat_history:
                            # 如果有消息历史但没有ID，是临时对话
                            report_title = "临时对话"

                        # 生成报告
                        result = report_generator.generate_learning_report(
                            st.session_state.chat_history,
                            report_title
                        )

                        if result["success"]:
                            report = result["report"]

                            # 自动保存学习报告到数据库
                            print(f"📊 正在自动保存学习报告: {report['title']}")
                            try:
                                save_success = report_generator.save_report_to_database(report)
                                if save_success:
                                    print("✅ 学习报告自动保存成功")

                                    # 更新系统状态显示
                                    try:
                                        new_count = st.session_state.rag_agent.vector_store.get_collection_count()
                                        st.metric("知识库文档数", new_count)
                                    except Exception as count_error:
                                        print(f"更新文档计数失败: {count_error}")

                                else:
                                    print("❌ 学习报告自动保存失败")
                            except Exception as save_error:
                                print(f"自动保存过程出现异常: {save_error}")

                            # 将学习报告添加到对话历史
                            report_message = {
                                "role": "assistant",
                                "content": f"📊 学习报告生成完成！报告已自动保存到知识库。\n\n{report['analysis']['overall_summary']}",
                                "learning_report": {
                                    "title": report['title'],
                                    "generated_at": report['generated_at'],
                                    "conversation_info": report['conversation_info'],
                                    "analysis": report['analysis']
                                }
                            }

                            # 添加到对话历史并保存
                            st.session_state.chat_history.append(report_message)
                            if st.session_state.current_chat_id:
                                save_chat_history(
                                    st.session_state.current_chat_id,
                                    st.session_state.chat_history
                                )
                                st.session_state.chat_list = load_chat_list()

                            # 显示成功消息
                            st.success("✅ 学习报告已生成并自动保存到知识库！")

                            # 显示简要预览
                            with st.expander("📋 报告预览", expanded=False):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("消息数量", report['conversation_info']['message_count'])
                                with col2:
                                    st.metric("对话时长", report['conversation_info']['duration'])

                                st.markdown("#### 🎯 核心知识点")
                                for point in report['analysis']['knowledge_points'][:3]:  # 只显示前3个
                                    st.markdown(f"• {point}")
                                if len(report['analysis']['knowledge_points']) > 3:
                                    st.markdown(f"• ... 等 {len(report['analysis']['knowledge_points'])} 个知识点")

                                if report['analysis']['confusion_points']:
                                    st.markdown("#### ❓ 用户困惑点")
                                    for point in report['analysis']['confusion_points'][:2]:  # 只显示前2个
                                        st.markdown(f"• {point}")

                                st.markdown("#### 📈 学习进度")
                                st.info(report['analysis']['learning_progress'])

                                st.markdown("*💡 完整报告已保存到对话历史和知识库中，可在对话框中查看详细内容*")

                        else:
                            st.error(f"❌ 生成失败: {result.get('error', '未知错误')}")

                    except Exception as e:
                        st.error(f"❌ 生成学习报告时出错: {str(e)}")
                        print(f"学习报告生成错误: {e}")

        # 当前对话状态
        current_title = "未开始对话"
        if st.session_state.current_chat_id:
            # 在对话列表中查找当前对话的标题
            for chat in st.session_state.chat_list:
                if chat["id"] == st.session_state.current_chat_id:
                    current_title = chat["title"]
                    break
        elif st.session_state.chat_history:
            # 如果有消息历史但没有ID，是临时对话
            current_title = "临时对话"

        st.markdown("**当前对话：**")
        st.info(f"📝 {current_title}")

        # 历史对话列表
        if st.session_state.chat_list:
            st.markdown("**历史对话：**")

            # 历史对话选择（排除当前对话）
            for chat in st.session_state.chat_list:
                if chat["id"] != st.session_state.current_chat_id:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(
                            f"📄 {chat['title'][:25]}{'...' if len(chat['title']) > 25 else ''}",
                            key=f"chat_{chat['id']}",
                            help=f"消息数: {chat['message_count']} | {chat['timestamp'][:10]}"
                        ):
                            # 切换到选中的对话
                            st.session_state.current_chat_id = chat["id"]

                            # 清空之前的题目状态
                            if 'generated_quiz' in st.session_state:
                                st.session_state.generated_quiz = []
                            if 'quiz_answers' in st.session_state:
                                st.session_state.quiz_answers = {}
                            if 'quiz_show_results' in st.session_state:
                                st.session_state.quiz_show_results = {}

                            st.session_state.chat_history = load_chat_history(chat["id"])
                            st.rerun()

                    with col2:
                        if st.button("🗑️", key=f"del_{chat['id']}", help="删除对话"):
                            if delete_chat_history(chat["id"]):
                                st.session_state.chat_list = load_chat_list()
                                st.success("已删除对话")
                                st.rerun()

        st.markdown("---")

        # 知识库管理
        st.markdown("### 📚 知识库管理")

        # 文档上传
        uploaded_docs = st.file_uploader(
            "上传文档到知识库",
            type=["pdf", "pptx", "docx", "txt"],
            accept_multiple_files=True,
            key=f"knowledge_upload_{st.session_state.knowledge_upload_counter}",
            help="上传文档来扩充知识库，支持PDF、PPTX、DOCX、TXT格式"
        )

        if uploaded_docs and st.button("📥 添加到知识库", type="secondary"):
            with st.spinner("正在处理文档并添加到知识库..."):
                try:
                    # 初始化组件
                    from document_loader import DocumentLoader
                    from text_splitter import TextSplitter

                    loader = DocumentLoader()
                    splitter = TextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

                    total_chunks = 0
                    # 处理每个上传的文件
                    for uploaded_file in uploaded_docs:
                        print(f"正在处理文件: {uploaded_file.name}")

                        # 使用DocumentLoader处理上传的文件
                        raw_docs = loader.process_uploaded_file(uploaded_file)
                        if raw_docs:
                            # 使用TextSplitter进行分块
                            chunks = splitter.split_documents(raw_docs)

                            # 添加到向量数据库
                            if chunks:
                                success = st.session_state.rag_agent.vector_store.add_documents_incremental(chunks)
                                if success:
                                    total_chunks += len(chunks)
                                    print(f"成功添加 {len(chunks)} 个块到知识库")
                                else:
                                    st.error(f"添加文件 {uploaded_file.name} 失败")

                    if total_chunks > 0:
                        st.success(f"✅ 成功添加到知识库：{total_chunks} 个文档块")

                        # 更新系统状态显示
                        new_count = st.session_state.rag_agent.vector_store.get_collection_count()
                        st.metric("知识库文档数", new_count)

                        # 清空文件上传区域
                        st.session_state.knowledge_upload_counter += 1
                        st.rerun()  # 强制重新渲染页面，清空上传组件

                    else:
                        st.warning("⚠️ 没有成功处理任何文档")

                except Exception as e:
                    st.error(f"❌ 添加知识失败: {e}")
                    print(f"添加知识失败: {e}")

        # 文本内容输入
        st.markdown("**或直接输入文本：**")
        text_content = st.text_area(
            "输入文本内容",
            placeholder="粘贴你想要添加到知识库的文本内容...",
            height=80,
            key=f"text_input_knowledge_{st.session_state.text_input_counter}"
        )

        if text_content.strip() and st.button("📝 添加文本到知识库", type="secondary"):
            with st.spinner("正在处理文本并添加到知识库..."):
                try:
                    # 初始化组件
                    from text_splitter import TextSplitter

                    splitter = TextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

                    # 处理文本内容
                    processed_text = [{
                        "content": text_content,
                        "filename": "manual_input.txt",
                        "filepath": "manual://text_input",
                        "filetype": ".txt",
                        "page_number": 0
                    }]

                    # 分块处理
                    chunks = splitter.split_documents(processed_text)

                    # 添加到向量数据库
                    if chunks:
                        success = st.session_state.rag_agent.vector_store.add_documents_incremental(chunks)
                        if success:
                            st.success(f"✅ 成功添加到知识库：{len(chunks)} 个文本块")

                            # 更新系统状态显示
                            new_count = st.session_state.rag_agent.vector_store.get_collection_count()
                            st.metric("知识库文档数", new_count)

                            # 清空文本输入框
                            st.session_state.text_input_counter += 1
                            st.rerun()  # 强制重新渲染页面，清空文本输入框
                        else:
                            st.error("❌ 添加文本失败")
                    else:
                        st.warning("⚠️ 文本内容为空或处理失败")

                except Exception as e:
                    st.error(f"❌ 添加文本失败: {e}")
                    print(f"添加文本失败: {e}")

        st.markdown("---")

        # 帮助信息
        with st.expander("ℹ️ 使用说明"):
            st.markdown("""
            **功能介绍：**
            - 📚 基于课程资料智能问答
            - 🔍 支持联网搜索补充信息
            - 🖼️ 支持PDF/PPT图片内容理解
            - 💬 保持对话上下文
            - 💾 自动保存对话历史

            **使用步骤：**
            1. 点击"初始化系统"
            2. 新建或选择历史对话
            3. 在下方输入问题
            4. 等待AI回答
            """)

    # 主界面
    st.title("🎓 智能课程助教系统")
    st.markdown("*基于多模态RAG技术的智能问答系统*")

    # 检查系统状态
    if not st.session_state.rag_agent:
        st.warning("⚠️ 请先在侧边栏初始化系统！")
        return

    # 对话界面
    st.markdown("---")

    # 显示对话历史
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.chat_history:
            display_chat_message(message)

    # 习题区域
    has_active_quiz = display_quiz_section()

    # 根据是否有活跃题目来控制输入框
    input_disabled = has_active_quiz

    # 输入区域 - 水平布局
    if input_disabled:
        st.info("📝 请先完成上面的习题后再继续对话")

        # 显示禁用状态的输入区域
        input_col1, input_col2 = st.columns([4, 1])

        with input_col1:
            st.text_input(
                "输入框已禁用",
                value="请先完成习题...",
                disabled=True,
                key="disabled_input"
            )

        with input_col2:
            st.button("📷 图片上传", disabled=True, help="请先完成习题")
    else:
        input_col1, input_col2 = st.columns([4, 1])

        with input_col1:
            prompt = st.chat_input("请输入您的问题...", key="user_input")

        with input_col2:
            uploaded_file = st.file_uploader(
                "图片",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                key=f"chat_image_{st.session_state.upload_counter}",
                help="可选：上传图片与问题一起发送",
                label_visibility="collapsed"
            )

    # 创建图片预览的占位符
    preview_placeholder = st.empty()

    # 显示当前附加的图片预览
    if uploaded_file:
        with preview_placeholder.container():
            st.info(f"📎 已附加图片: {uploaded_file.name}")
            # 小缩略图预览
            col_preview1, col_preview2, col_preview3 = st.columns([1, 2, 1])
            with col_preview2:
                st.image(uploaded_file, width=150, caption="待发送图片")

    # 处理用户输入
    if prompt and prompt.strip():
        # 检查是否有图片
        has_image = uploaded_file is not None

        # 发送消息时立即清空预览
        preview_placeholder.empty()

        # 将当前的交互式题目转换为对话历史
        convert_quiz_to_history()

        # 准备消息数据
        user_message = {
            "role": "user",
            "content": prompt,
            "has_image": has_image
        }

        # 如果有图片，保存图片数据到消息历史
        if has_image:
            user_message["image_name"] = uploaded_file.name
            # 将图片转换为base64并保存（用于历史记录显示，使用压缩版本节省空间）
            try:
                compressed_image_data = process_uploaded_image(uploaded_file, for_history=True)
                user_message["image_data"] = compressed_image_data
            except Exception as e:
                print(f"图片压缩失败: {e}")
                user_message["image_data"] = None

        # 添加用户消息到历史
        st.session_state.chat_history.append(user_message)

        # 显示用户消息
        with chat_container:
            display_chat_message(user_message)

        # 生成回答
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🤔 正在思考..." if not has_image else "🖼️ 正在分析图片..."):
                    try:
                        if has_image:
                            # 图片问答模式 - 使用高质量图片进行AI分析
                            image_base64 = process_uploaded_image(uploaded_file, for_history=False)
                            answer = st.session_state.rag_agent.answer_image_question(
                                query=prompt,
                                image_base64=image_base64,
                                chat_history=st.session_state.chat_history[:-1]  # 不包含当前问题
                            )
                        else:
                            # 普通文本问答
                            answer = st.session_state.rag_agent.answer_question(
                                prompt,
                                chat_history=st.session_state.chat_history[:-1]  # 不包含当前问题
                            )

                        st.write(answer)

                        # 添加助手消息到历史
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

                        # 自动保存对话历史
                        if st.session_state.current_chat_id:
                            save_chat_history(
                                st.session_state.current_chat_id,
                                st.session_state.chat_history
                            )
                            # 刷新对话列表
                            st.session_state.chat_list = load_chat_list()

                        # 清空图片上传区域并强制重新渲染
                        st.session_state.upload_counter += 1
                        st.rerun()  # 强制重新渲染页面，清空所有UI元素

                    except Exception as e:
                        error_msg = f"❌ 回答生成失败: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

                        # 即使出错也要保存对话历史
                        if st.session_state.current_chat_id:
                            save_chat_history(
                                st.session_state.current_chat_id,
                                st.session_state.chat_history,
                                "对话出错"
                            )

                        # 即使出错也要清空图片上传区域并强制重新渲染
                        st.session_state.upload_counter += 1
                        st.rerun()  # 强制重新渲染页面，清空所有UI元素


def display_quiz_section():
    """显示习题区域 - 只显示当前活跃的交互式题目

    Returns:
        bool: 是否有活跃的题目需要答题
    """
    # 检查是否有生成的习题
    if not hasattr(st.session_state, 'generated_quiz') or not st.session_state.generated_quiz:
        return False

    # 显示新题目生成提示
    if hasattr(st.session_state, 'quiz_timestamp') and st.session_state.quiz_timestamp:
        current_time = time.time()
        if current_time - st.session_state.quiz_timestamp < 10:  # 10秒内显示提示
            st.success("🎯 新习题已生成！请查看下方题目开始答题。")
            # 重置时间戳，避免重复显示
            st.session_state.quiz_timestamp = 0

    quiz_data = st.session_state.generated_quiz[-1]  # 获取最新的习题

    # 检查答题完成情况
    total_questions = len(quiz_data["questions"])
    answered_questions = len(getattr(st.session_state, 'quiz_answers', {}))

    st.markdown("---")
    st.markdown("### 🎯 智能习题")

    # 显示习题信息和进度
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("题目数量", f"{answered_questions}/{total_questions}")
    with col2:
        st.metric("难度", quiz_data["difficulty"])
    with col3:
        st.metric("类型", quiz_data["question_type"])

    # 检查是否答完所有题目
    if answered_questions >= total_questions:
        st.success("🎉 所有题目已完成！正在保存到对话历史...")
        convert_quiz_to_history()
        st.rerun()  # 刷新页面，隐藏题目区域
        return False

    # 初始化答题状态
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    if 'quiz_show_results' not in st.session_state:
        st.session_state.quiz_show_results = {}

    # 显示每个题目
    for i, question in enumerate(quiz_data["questions"]):
        question_id = f"q_{i}"

        with st.container():
            st.markdown(f"**第 {i+1} 题：** {question['question']}")

            # 根据题目类型显示不同的交互组件
            if question["type"] == "multiple_choice":
                # 选择题
                options = list(question["options"].values())
                user_answer = st.radio(
                    "请选择答案：",
                    options,
                    key=f"quiz_{question_id}",
                    label_visibility="collapsed"
                )

                # 提交按钮
                if st.button(f"提交答案 (第{i+1}题)", key=f"submit_{question_id}"):
                    # 找到选择的选项字母
                    selected_option = None
                    for opt_key, opt_value in question["options"].items():
                        if opt_value == user_answer:
                            selected_option = opt_key
                            break

                    # 检查答案
                    is_correct = selected_option == question["correct_answer"]
                    st.session_state.quiz_answers[question_id] = {
                        "user_answer": selected_option,
                        "is_correct": is_correct,
                        "correct_answer": question["correct_answer"]
                    }
                    st.session_state.quiz_show_results[question_id] = True

                    # 保存答题记录到对话历史
                    save_quiz_answer_to_history(question, selected_option, is_correct)

                    st.rerun()

            elif question["type"] == "true_false":
                # 判断题
                user_answer = st.radio(
                    "请选择：",
                    ["对", "错"],
                    key=f"quiz_{question_id}",
                    label_visibility="collapsed"
                )

                if st.button(f"提交答案 (第{i+1}题)", key=f"submit_{question_id}"):
                    is_correct = user_answer == question["correct_answer"]
                    st.session_state.quiz_answers[question_id] = {
                        "user_answer": user_answer,
                        "is_correct": is_correct,
                        "correct_answer": question["correct_answer"]
                    }
                    st.session_state.quiz_show_results[question_id] = True

                    # 保存答题记录到对话历史
                    save_quiz_answer_to_history(question, user_answer, is_correct)

                    st.rerun()


            # 显示结果
            if st.session_state.quiz_show_results.get(question_id, False):
                answer_data = st.session_state.quiz_answers[question_id]

                if answer_data["is_correct"] is True:
                    st.success("✅ 回答正确！")
                elif answer_data["is_correct"] is False:
                    st.error(f"❌ 回答错误。正确答案是：{answer_data['correct_answer']}")
                else:
                    st.info("📝 答案已提交")

                # 显示解析
                with st.expander("📖 查看解析", expanded=True):
                    st.markdown("**正确答案：** " + question["correct_answer"])
                    st.markdown("**详细解析：**")
                    st.write(question["explanation"])

            st.markdown("---")



def save_quiz_answer_to_history(question: Dict, user_answer: str, is_correct: bool):
    """保存答题记录到对话历史"""
    try:
        # 构建答题记录
        quiz_record = {
            "role": "user",
            "content": f"📝 答题记录：{question['question']}\n我的答案：{user_answer}\n结果：{'✅正确' if is_correct else '❌错误'}",
            "quiz_answer": {
                "question": question["question"],
                "question_type": question["type"],
                "user_answer": user_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "explanation": question["explanation"],
                "timestamp": datetime.now().isoformat()
            }
        }

        # 添加到对话历史
        st.session_state.chat_history.append(quiz_record)

        # 如果有当前对话ID，保存到文件
        if st.session_state.current_chat_id:
            save_chat_history(
                st.session_state.current_chat_id,
                st.session_state.chat_history
            )
            # 刷新对话列表
            st.session_state.chat_list = load_chat_list()

    except Exception as e:
        print(f"保存答题记录失败: {e}")


def convert_quiz_to_history():
    """将当前的交互式题目转换为对话历史"""
    try:
        # 检查是否有当前的交互式题目
        if (not hasattr(st.session_state, 'generated_quiz') or
            not st.session_state.generated_quiz):
            return

        quiz_data = st.session_state.generated_quiz[-1]  # 获取最新的题目

        # 创建题目历史记录
        quiz_history_record = {
            "role": "assistant",
            "content": f"🎯 习题：{quiz_data['topic']} ({len(quiz_data['questions'])}道题目)",
            "quiz_display": {
                "topic": quiz_data["topic"],
                "difficulty": quiz_data["difficulty"],
                "question_type": quiz_data["question_type"],
                "questions": quiz_data["questions"],
                "answers": getattr(st.session_state, 'quiz_answers', {}),
                "timestamp": datetime.now().isoformat()
            }
        }

        # 添加到对话历史
        st.session_state.chat_history.append(quiz_history_record)

        # 保存到文件
        if st.session_state.current_chat_id:
            save_chat_history(
                st.session_state.current_chat_id,
                st.session_state.chat_history
            )
            st.session_state.chat_list = load_chat_list()

        # 清空当前的交互式题目状态
        if 'generated_quiz' in st.session_state:
            st.session_state.generated_quiz.pop()  # 移除当前题目
        if 'quiz_answers' in st.session_state:
            st.session_state.quiz_answers = {}
        if 'quiz_show_results' in st.session_state:
            st.session_state.quiz_show_results = {}

        print(f"📚 已将题目转换为对话历史: {quiz_data['topic']}")

        # 强制刷新UI，立即隐藏题目区域
        st.rerun()

    except Exception as e:
        print(f"转换题目历史失败: {e}")


if __name__ == "__main__":
    main()
