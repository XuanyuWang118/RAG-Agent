import streamlit as st
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from rag_agent import RAGAgent
from config import VECTOR_DB_PATH, MODEL_NAME

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
                return chat_data.get("messages", [])
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
        if st.button("🗑️ 清空当前对话", type="secondary"):
            if st.session_state.current_chat_id and st.session_state.chat_history:
                # 保存最后一次对话状态（用于恢复）
                save_chat_history(
                    st.session_state.current_chat_id,
                    st.session_state.chat_history,
                    "已清空对话"
                )
            st.session_state.chat_history = []
            st.rerun()

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
                            st.session_state.chat_history = load_chat_history(chat["id"])
                            st.rerun()

                    with col2:
                        if st.button("🗑️", key=f"del_{chat['id']}", help="删除对话"):
                            if delete_chat_history(chat["id"]):
                                st.session_state.chat_list = load_chat_list()
                                st.success("已删除对话")
                                st.rerun()

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
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])

    # 输入框
    if prompt := st.chat_input("请输入您的问题...", key="user_input"):
        if not prompt.strip():
            st.warning("请输入有效的问题！")
            return

        # 添加用户消息到历史
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # 显示用户消息
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)

        # 生成回答
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🤔 正在思考..."):
                    try:
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

if __name__ == "__main__":
    main()
