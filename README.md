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
