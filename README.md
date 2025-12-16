# RAG-Agent

NLP Course Project [Info](https://gpy5q03kes.feishu.cn/wiki/JgqTwaqG2ih6hdkWk6pcYBhAnPd)

**Members**: XuanyuWang, RuiTao, BoruiZhang

### Git usage
#### 初始化本地 git 仓库
```bash
git init
git remote add origin git@github.com:user-name/hub-name.git  
git remote -v
git status
git add .
git commit -m "init"
git push -u origin master
```
#### 基础提交指令
```bash
git pull                # 拉取仓库
git status              # 查看修改状态
git add .               # 把修改加入暂存区
git commit -m "message" # 提交到 github 仓库
git push                # 上传
```
#### 分支指令
```bash
git branch <-r>
git switch <branch-name>
git checkout <branch-name> -- <file-name> <...>
git stash <-u>
git stash pop
```

### Datasets
NLP Course PPts, ...


### Chat Examples
```
./chat.md
```

### 🖼️ 图像识别

本项目现已支持**多模态文档处理**，可对文档中的图像信息进行提取、理解与融合。

1. **增强的 PDF/PPDX 解析（`document_loader.py`）**：
   * 原有的 PDF 解析器已替换为 **PyMuPDF（fitz）**，显著提升了文本与图像提取的成功率和准确性。
   * 支持从 PDF 与 PPTX 文件中提取图像，并统一保存至 `./images_extracted/` 目录中。

2. **图像文本化（`text_splitter.py`）**：
   * 在文档切分（chunking）流程之前，新增了图像预处理步骤。
   * `TextSplitter` 会调用 **`ImageProcessor`**（定义于 `image_processor.py`），将每一页 / 每一张幻灯片中提取的图像转换为描述性文本。
   * 生成的图像描述文本将被**追加**到原始文档文本内容中，使 RAG 检索在文本之外同时感知并利用视觉信息。


### 🌐 联网查询功能

一个简单的toolcalling架构，利用tavily的联网查询功能。稍微修改了一下提示词来使用tool。


### 🔍 检索系统升级：混合检索与多轮增强

本次升级将原有的纯向量搜索（密集检索）架构，提升为智能混合检索（Hybrid Retrieval）系统，以应对复杂、多轮次以及包含专业术语的查询。

#### 1. 复合检索策略：弥补纯向量搜索的不足

我们集成了稀疏检索 BM25 和 Reciprocal Rank Fusion（RRF）算法，实现了精准与语义的平衡：

* **密集检索（Dense Retrieval）：** 利用 ChromaDB 向量搜索，擅长理解抽象概念、定义和原理，处理**语义相关**的查询。
* **稀疏检索（BM25 Retrieval）：** 基于关键词的匹配，擅长处理包含罕见、专业、技术性名词或 ID 等的**字面匹配**查询。
* **混合检索（Hybrid Retrieval）：** **核心策略**。同时执行两种检索，并使用 RRF 算法智能融合并重新排序结果，确保兼顾语义和关键词的最佳准确性。

> **持久化优化：** 我们解决了 BM25 索引需要重建的性能问题，通过序列化工具（如 `joblib`）将其持久化到磁盘，确保系统启动时能够快速加载索引。


#### 2. LLM 驱动的智能策略分派与决策

为了最大限度发挥复合检索的效能，我们让 LLM 动态选择最高效的检索策略：

* **策略分析：** 在执行检索前，系统调用 LLM（`_analyze_query_type`）分析用户的查询意图（概念主导、关键词主导或混合），并智能决策是采用纯 **DENSE**、纯 **BM25** 还是 **HYBRID** 策略。
* **动态分派：** 系统根据 LLM 的决策结果，自动分派到 `VectorStore` 中对应的搜索方法，避免了单一策略的局限性。

#### 3. 多轮对话检索增强（指代消解）

针对多轮对话场景中常见的上下文指代问题，我们实现了 LLM 驱动的查询重写：

* **指代消解：** `RAGAgent`（在 `_construct_search_query` 中）将当前查询和最近的对话历史发送给 LLM。
* **查询提炼：** LLM 将模糊查询（如“它有什么缺点？”）提炼成一个**精确且独立**的、无指代关系的检索查询（如“Transformer 模型的缺点”），从根本上解决了多轮问答中的检索漂移问题，极大地提升了用户体验。


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
