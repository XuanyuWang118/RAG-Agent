# 📸 Streamlit网页截图工具

用于截取和保存RAG智能课程助教系统的网页界面快照。

## 🚀 快速开始

### 方法1: 使用批处理脚本 (Windows推荐)

```bash
# 双击运行或命令行执行
capture_screenshot.bat
```

### 方法2: 使用Python脚本 (跨平台)

```bash
# 单个快照
python capture_streamlit_screenshot.py

# 指定输出文件
python capture_streamlit_screenshot.py --output my_screenshot.png

# 指定URL和等待时间
python capture_streamlit_screenshot.py --url http://localhost:8501 --wait 10
```

### 方法3: 使用完整工具 (支持批量截图)

```bash
# Linux/Mac
./take_screenshots.sh

# Windows
take_screenshots.bat
```

## 📋 功能特性

### ✅ 支持的截图方法
- **Selenium + Chrome**: 稳定可靠，推荐使用
- **Playwright**: 现代化的替代方案
- **自动选择**: 自动选择最佳可用方法

### ✅ 智能等待
- 自动检测Streamlit应用加载完成
- 可配置等待时间
- 全页截图支持

### ✅ 批量截图
- 预定义5个演示场景
- 一键生成完整界面展示

## 🔧 命令行参数

### Python脚本参数

```bash
python capture_streamlit_screenshot.py [选项]

选项:
  --url URL              Streamlit应用URL (默认: http://localhost:8501)
  --output FILE, -o FILE 输出文件名
  --method {auto,selenium,playwright}
                         截图方法 (默认: auto)
  --wait SECONDS, -w SECONDS
                         等待页面加载时间(秒，默认: 5)
  --install              安装必要的依赖包
```

### 完整工具参数

```bash
python screenshot_tool.py [选项]

选项:
  --url URL              Streamlit应用URL
  --method {auto,selenium,playwright}
  --output-dir DIR       输出目录 (默认: ./screenshots)
  --batch                批量截图演示场景
  --filename NAME        单个截图的文件名
  --wait-time SECONDS    等待时间
  --full-page            截取全页(默认开启)
```

## 📦 依赖安装

脚本会自动检查和安装必要的依赖：

```bash
# 方法1: 自动安装
python capture_streamlit_screenshot.py --install

# 方法2: 手动安装
pip install selenium
# 或
pip install playwright && playwright install
```

## 🎯 使用场景

### 1. 单个界面截图
```bash
python capture_streamlit_screenshot.py --output interface.png
```

### 2. 完整演示截图
```bash
python screenshot_tool.py --batch
```

### 3. 自定义URL截图
```bash
python capture_streamlit_screenshot.py --url http://192.168.1.100:8501 --output remote.png
```

## 📁 输出文件

- **单个截图**: `streamlit_screenshot_YYYYMMDD_HHMMSS.png`
- **批量截图**: `screenshots/scenario_XX_name.png`
- **自定义输出**: 指定文件名

## 🔧 故障排除

### 常见问题

**1. ChromeDriver错误**
```bash
# 确保Chrome浏览器已安装
# 或使用Playwright方法
python capture_streamlit_screenshot.py --method playwright
```

**2. 页面加载超时**
```bash
# 增加等待时间
python capture_streamlit_screenshot.py --wait 10
```

**3. 截图空白**
- 检查Streamlit应用是否正在运行
- 确认URL是否正确
- 尝试不同的截图方法

**4. 权限错误**
```bash
# 以管理员权限运行或更改输出目录
python capture_streamlit_screenshot.py --output ./my_screenshots/screenshot.png
```

## 🎨 输出示例

成功截图后会显示：
```
🌐 目标URL: http://localhost:8501
📁 输出文件: streamlit_screenshot_20241219_143052.png
⏱️  等待时间: 5 秒
🔧 使用Selenium进行截图...
✅ 截图已保存: streamlit_screenshot_20241219_143052.png

🎉 截图成功完成!
📁 文件位置: D:\project\RAG-agent\streamlit_screenshot_20241219_143052.png
```

## 📊 批量截图场景

批量模式会截取以下5个场景：
1. **初始界面** - 应用启动后的初始界面
2. **对话界面** - 用户与AI对话的界面
3. **知识库管理** - 知识库上传和管理界面
4. **学习报告** - 学习报告生成界面
5. **习题生成** - 智能习题生成界面

## 🤝 技术支持

如遇问题，请检查：
1. Python环境是否正确安装
2. Streamlit应用是否正在运行
3. 网络连接是否正常
4. 依赖包是否完整安装

---

**🎯 提示**: 建议在截图前先手动访问Streamlit应用，确保界面正常显示。
