# RAG-Agent

NLP Course Project [Info](https://gpy5q03kes.feishu.cn/wiki/JgqTwaqG2ih6hdkWk6pcYBhAnPd)

Members: XuanyuWang, RuiTao, BoruiZhang

### Git usage
```bash
git pull                # 拉取仓库
git status              # 查看修改状态
git add .               # 把修改加入暂存区
git commit -m "message" # 提交到 github 仓库
git push                # 上传
```

### Data
NLP Course PPts


### Chat Examples
```
./chat.md
```

### 🖼️ Image Recognition

This project now supports multimodal document processing, enabling the extraction and handling of image information.

1.  **Enhanced PDF Extraction (`document_loader.py`)**:
    * The original PDF parser has been replaced with **PyMuPDF (fitz)**, which significantly improves the success rate and accuracy of text and image extraction.
    * Images from PDF and PPTX files are now extracted and saved to the `./images_extracted/` directory.

2.  **Image Textualization (`text_splitter.py`)**:
    * A new image preprocessing step has been added before the document chunking process.
    * The `TextSplitter` calls the **`ImageProcessor`** (implemented in `image_processor.py`) to convert extracted images from each page/slide into descriptive text.
    * This image description text is **appended** to the original document text content, ensuring that RAG retrieval considers visual information alongside the text. 


### 🌐 联网查询功能

一个简单的toolcalling架构，利用tavily的联网查询功能。稍微修改了一下提示词来使用tool。


### 🚀 Streamlit 可视化界面

项目现在支持现代化的Web界面！使用Streamlit构建的交互式聊天界面。

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 运行可视化界面
```bash

python run_streamlit.py

```

#### 界面功能
- 🖥️ **现代化Web界面**：直观的聊天界面替代命令行
- 📊 **系统状态监控**：实时显示知识库状态
- 💬 **对话历史持久化**：自动保存和恢复对话历史
- 📁 **多对话管理**：新建、切换、删除多个对话
- 🔄 **一键初始化**：简化系统启动流程
- 💾 **数据持久化**：对话数据保存到本地文件

#### 使用步骤
1. 确保向量数据库已创建（运行 `python process_data.py`）
2. 启动Streamlit应用：`python run_streamlit.py`
3. 浏览器自动打开 `http://localhost:8501`
4. 点击侧边栏的"初始化系统"
5. 开始与AI助教对话！

#### 对话持久化功能

**自动保存机制：**
- 📝 **实时保存**：每条消息发送后自动保存
- 💾 **本地存储**：对话数据保存为JSON文件在 `./chat_history/` 目录
- 🔄 **自动恢复**：重新启动应用时可恢复历史对话
- 📁 **多对话支持**：支持同时管理多个独立对话

**对话管理：**
- ➕ **新建对话**：创建全新的对话会话
- 🗑️ **清空当前对话**：清空当前对话的消息历史
- 📝 **当前对话**：高亮显示正在进行的对话
- 📄 **历史对话**：浏览和切换到之前的对话（排除当前对话）
- 🗑️ **删除对话**：清理不需要的对话记录
- 📊 **对话统计**：显示每条对话的消息数量和时间

**数据结构：**
```json
{
  "id": "对话唯一ID",
  "title": "对话标题（自动生成）",
  "timestamp": "2024-12-12T10:30:00",
  "messages": [
    {"role": "user", "content": "用户消息"},
    {"role": "assistant", "content": "AI回答"}
  ]
}
```

#### 界面预览
```
🎓 智能课程助教
├── 🔄 初始化系统按钮
├── 📊 系统状态显示
├── 💬 对话管理
│   ├── ➕ 新建对话
│   ├── 🗑️ 清空当前对话
│   ├── 📝 当前对话：[高亮显示]
│   ├── 📄 历史对话列表
│   └── 🗑️ 删除对话
├── 💬 对话界面
│   ├── 用户消息气泡
│   └── AI回答气泡
└── 📝 输入框
```
