# image_processor.py

import os
import base64
from typing import List
from openai import OpenAI

from config import (
    OPENAI_API_KEY, 
    OPENAI_API_BASE, 
    OPENAI_VL_MODEL
)

class ImageProcessor:
    def __init__(self):
        # 初始化 LLM 客户端，用于调用 Qwen-VL
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
        self.model = OPENAI_VL_MODEL

    def _image_to_base64(self, image_path: str) -> str:
        """将图片文件转换为 Base64 编码"""
        if not os.path.exists(image_path):
            print(f"警告：图片文件不存在: {image_path}")
            return None
        
        try:
            with open(image_path, "rb") as image_file:
                # Base64 编码并转换为字符串
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"转换图片为 Base64 失败 {image_path}: {e}")
            return None

    def process_images_to_text(self, image_paths: List[str]) -> str:
        """
        处理图片路径列表，调用 MLLM 或 OCR 转换为文本描述。
        
        参数:
            image_paths: 本地图片路径列表
        返回:
            整合了所有图片信息的文本描述
        """
        if not image_paths:
            return ""

        full_description = []
        
        for i, path in enumerate(image_paths):
            base64_image = self._image_to_base64(path)
            
            if base64_image:
                # 1. 构建多模态输入内容
                # 使用 data:image/jpeg;base64, 作为前缀
                image_url = f"data:image/jpeg;base64,{base64_image}"
                
                # 提示词要求模型同时进行 OCR 和语义分析
                prompt_text = (
                    f"请对图片 {i+1} 进行详细分析，并输出一段综合描述。描述应包含图中的**所有文字内容（OCR结果）**，以及对**图表、流程图或示意图的语义分析（如趋势、步骤、结论）**。请用中文回答，并保持描述专业、客观。"
                )
                
                content_parts = [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
                
                messages = [{"role": "user", "content": content_parts}]

                # 2. 调用 Qwen-VL API
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.0, # 低温度保证客观描述
                        max_tokens=1000
                    )
                    
                    analysis_text = response.choices[0].message.content
                    full_description.append(f"--- 图片 {i+1} ({os.path.basename(path)}) 分析结果 ---\n{analysis_text}\n")
                    
                except Exception as e:
                    full_description.append(f"图片 {i+1} 处理失败: {e}\n")

        return "\n".join(full_description)