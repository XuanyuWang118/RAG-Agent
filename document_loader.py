import os
import io
from typing import List, Dict, Optional

import fitz
import pdfplumber
import docx2txt
from pptx import Presentation
from PIL import Image

from config import DATA_DIR


class DocumentLoader:
    def __init__(
        self,
        data_dir: str = DATA_DIR,
        # 新增一个参数用于存放提取出的图片
        image_output_dir: str = "./images_extracted", 
    ):
        self.data_dir = data_dir
        self.supported_formats = [".pdf", ".pptx", ".docx", ".txt"]
        self.image_output_dir = image_output_dir
        os.makedirs(self.image_output_dir, exist_ok=True) # 确保图片输出目录存在

    # def load_pdf(self, file_path: str) -> List[Dict]:
    #     """加载PDF文件，按页返回内容

    #     TODO: 实现PDF文件加载
    #     要求：
    #     1. 使用PdfReader读取PDF文件
    #     2. 遍历每一页，提取文本内容
    #     3. 格式化为"--- 第 X 页 ---\n文本内容\n"
    #     4. 返回pdf内容列表，每个元素包含 {"text": "..."}
    #     """
    #     pages = []
    #     try:
    #         # 使用 pdfplumber 读取PDF文件
    #         with pdfplumber.open(file_path) as pdf:
    #             num_pages = len(pdf.pages)
    #             filename_base = os.path.basename(file_path).replace(os.path.splitext(file_path)[1], "")
                
    #             for i, page in enumerate(pdf.pages):
    #                 # 提取文本
    #                 text = page.extract_text() or ""
                    
    #                 # 提取图片信息
    #                 image_info = []
    #                 for image_data in page.images:
    #                     # 尝试从 page.images 中提取图像对象
    #                     try:
    #                         # get_objid() 是一个内部方法，这里我们直接尝试提取原始图像数据
    #                         img = page.crop((image_data['x0'], image_data['y0'], image_data['x1'], image_data['y1']))
                            
    #                         # 获取图片二进制数据
    #                         img_bytes = img.to_image().original.tobytes() 
    #                         img_format = img.to_image().original.format 
                            
    #                         # 确定图片保存路径和文件名
    #                         img_filename = f"{filename_base}_p{i+1}_{image_data['name']}.{img_format or 'png'}"
    #                         img_save_path = os.path.join(self.image_output_dir, img_filename)
                            
    #                         # 使用PIL保存图片
    #                         Image.open(io.BytesIO(img_bytes)).save(img_save_path)

    #                         image_info.append({"path": img_save_path, "bbox": [image_data['x0'], image_data['y0']]})
    #                     except Exception as img_e:
    #                         # 很多 PDF 对象会被错误识别为图片，这里捕获异常并跳过
    #                         continue

    #                 formatted_text = f"--- 第 {i + 1} 页 ---\n{text.strip()}\n"
                    
    #                 pages.append({
    #                     "text": formatted_text,
    #                     "images": image_info  # 新增图片信息字段
    #                 })
    #     except Exception as e:
    #         print(f"加载PDF文件失败 {file_path}: {e}")
    #     return pages

    def load_pdf(self, file_path: str) -> List[Dict]:
        """
        加载PDF文件，按页返回内容，并使用 PyMuPDF 提取图片和保存到本地。
        最终返回的字典只包含 'text' 和 'images' 键，以供 load_document 统一封装元数据。
        """
        pages = []
        filename = os.path.basename(file_path)
        filename_base = os.path.splitext(filename)[0]

        # 封装图片保存逻辑作为内部辅助函数
        def _save_image_from_bytes(image_bytes: bytes, page_num: int, xref: int, ext: str) -> str:
            """将图片二进制数据保存到本地"""
            if not image_bytes:
                return None
            
            ext = ext.lower() if ext.lower() in ['png', 'jpg', 'jpeg', 'bmp', 'tiff'] else 'png'
            
            # 使用 PyMuPDF 的 xref 作为标识符
            img_filename = f"{filename_base}_p{page_num}_xref_{xref}.{ext}"
            img_save_path = os.path.join(self.image_output_dir, img_filename)
            
            try:
                # 使用 PIL 从字节流中加载并保存图片
                img = Image.open(io.BytesIO(image_bytes))
                img.save(img_save_path)
                return img_save_path
            except Exception:
                # 提取或保存失败
                return None

        try:
            # 1. 使用 PyMuPDF (fitz) 打开 PDF 文件
            with fitz.open(file_path) as pdf_document:
                for i, page in enumerate(pdf_document):
                    image_info = []
                    page_num = i + 1
                    
                    # 2. 提取文本内容
                    text = page.get_text() or ""
                    
                    # 3. 提取和保存图片
                    for img_tuple in page.get_images(full=True):
                        xref = img_tuple[0]
                        img_ext = img_tuple[7]
                        
                        try:
                            image_data = pdf_document.extract_image(xref)
                            if image_data and image_data['image']:
                                image_bytes = image_data['image']
                                
                                # 调用内部函数保存图片
                                img_save_path = _save_image_from_bytes(
                                    image_bytes, 
                                    page_num, 
                                    xref, 
                                    img_ext
                                )
                                
                                if img_save_path:
                                    # 记录图片路径信息
                                    # 注意：原 load_pdf 结构中没有 'name' 字段，但为了可追溯性保留
                                    image_info.append({"path": img_save_path, "name": f"xref_{xref}"})
                                    
                        except Exception:
                            continue

                    # 4. 格式化文本
                    formatted_text = f"--- 第 {page_num} 页 ---\n{text.strip()}\n"
                    
                    # 5. 存储结果：只返回 load_document 需要的核心数据
                    pages.append({
                        "text": formatted_text,
                        "images": image_info  
                    })
                    
        except Exception as e:
            print(f"加载PDF文件失败 {file_path}: {e}")
            return []
            
        return pages

    def load_pptx(self, file_path: str) -> List[Dict]:
        """加载PPT文件，按幻灯片返回内容

        TODO: 实现PPT文件加载
        要求：
        1. 使用Presentation读取PPT文件
        2. 遍历每一页，提取文本内容
        3. 格式化为"--- 幻灯片 X ---\n文本内容\n"
        4. 返回幻灯片内容列表，每个元素包含 {"text": "..."}
        """
        slides_content = []
        try:
            # 1. 使用Presentation读取PPT文件
            prs = Presentation(file_path)
            filename_base = os.path.basename(file_path).replace(os.path.splitext(file_path)[1], "")
            
            # 2. 遍历每一页，提取文本内容
            for i, slide in enumerate(prs.slides):
                slide_text = []
                image_info = []
                
                for shape in slide.shapes:
                    # 提取文本内容
                    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            # 拼接所有文本块内容
                            slide_text.append("".join(run.text for run in paragraph.runs))
                    
                    # 提取图片内容
                    if shape.shape_type == 13: # 形状类型 13 代表 PICTURE
                        try:
                            # 检查形状是否真的包含图片
                            if hasattr(shape, "image"):
                                image_part = shape.image
                                image_bytes = image_part.blob
                                image_ext = image_part.ext

                                # 保存图片
                                img_filename = f"{filename_base}_s{i+1}_{shape.name}.{image_ext}"
                                img_save_path = os.path.join(self.image_output_dir, img_filename)

                                with open(img_save_path, 'wb') as f:
                                    f.write(image_bytes)

                                image_info.append({"path": img_save_path, "name": shape.name})
                        except (AttributeError, Exception) as img_e:
                            # 有些形状被误识别为图片，跳过这些错误
                            continue

                text = "\n".join(filter(None, slide_text)).strip()
                formatted_text = f"--- 幻灯片 {i + 1} ---\n{text}\n"
                
                slides_content.append({
                    "text": formatted_text,
                    "images": image_info # 新增图片信息字段
                })
        except Exception as e:
            print(f"加载PPTX文件失败 {file_path}: {e}")
        return slides_content

    def load_docx(self, file_path: str) -> str:
        """加载DOCX文件
        TODO: 实现DOCX文件加载
        要求：
        1. 使用docx2txt读取DOCX文件
        2. 返回文本内容
        """
        try:
            # 1. 使用docx2txt读取DOCX文件并返回文本内容
            text = docx2txt.process(file_path)
            # 2. 返回文本内容
            return text.strip()
        except Exception as e:
            print(f"加载DOCX文件失败 {file_path}: {e}")
            return ""

    def load_txt(self, file_path: str) -> str:
        """加载TXT文件
        TODO: 实现TXT文件加载
        要求：
        1. 使用open读取TXT文件（注意使用encoding="utf-8"）
        2. 返回文本内容
        """
        try:
            # 1. 使用open读取TXT文件（注意使用encoding="utf-8"）
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            # 2. 返回文本内容
            return text.strip()
        except Exception as e:
            print(f"加载TXT文件失败 {file_path}: {e}")
            return ""

    def load_document(self, file_path: str) -> List[Dict[str, any]]:
        """加载单个文档，PDF和PPT按页/幻灯片分割，返回文档块列表"""
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        documents = []

        if ext == ".pdf":
            pages = self.load_pdf(file_path)
            for page_idx, page_data in enumerate(pages, 1):
                documents.append(
                    {
                        "content": page_data["text"],
                        "filename": filename,
                        "filepath": file_path,
                        "filetype": ext,
                        "page_number": page_idx,
                        "images": page_data["images"], # 传入图片信息
                    }
                )
        elif ext == ".pptx":
            slides = self.load_pptx(file_path)
            for slide_idx, slide_data in enumerate(slides, 1):
                documents.append(
                    {
                        "content": slide_data["text"],
                        "filename": filename,
                        "filepath": file_path,
                        "filetype": ext,
                        "page_number": slide_idx,
                        "images": slide_data["images"], # 传入图片信息
                    }
                )
        elif ext == ".docx":
            content = self.load_docx(file_path)
            if content:
                documents.append(
                    {
                        "content": content,
                        "filename": filename,
                        "filepath": file_path,
                        "filetype": ext,
                        "page_number": 0,
                    }
                )
        elif ext == ".txt":
            content = self.load_txt(file_path)
            if content:
                documents.append(
                    {
                        "content": content,
                        "filename": filename,
                        "filepath": file_path,
                        "filetype": ext,
                        "page_number": 0,
                    }
                )
        else:
            print(f"不支持的文件格式: {ext}")

        return documents

    def load_all_documents(self) -> List[Dict[str, any]]:
        """加载数据目录下的所有文档"""
        if not os.path.exists(self.data_dir):
            print(f"数据目录不存在: {self.data_dir}")
            return None

        documents = []

        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.supported_formats:
                    file_path = os.path.join(root, file)
                    print(f"正在加载: {file_path}")
                    doc_chunks = self.load_document(file_path)
                    if doc_chunks:
                        documents.extend(doc_chunks)

        return documents