# 📸 Streamlit网页快照工具

## 🎯 功能介绍

`screenshot_tool.py` 是专为RAG智能课程助教系统设计的网页快照工具，可以自动截取Streamlit应用的界面并保存为图片。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install selenium
# 或
pip install playwright && playwright install
```

### 2. 启动Streamlit应用

```bash
python run_streamlit.py
```

### 3. 截取快照

#### 单个快照
```bash
# 使用默认设置
python screenshot_tool.py

# 指定URL和输出目录
python screenshot_tool.py --url http://localhost:8501 --output-dir ./my_screenshots

# 指定截图方法
python screenshot_tool.py --method selenium
python screenshot_tool.py --method playwright
```

#### 批量截图演示场景
```bash
python screenshot_tool.py --batch
```

## 📋 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--url` | Streamlit应用URL | `http://localhost:8501` |
| `--method` | 截图方法 (`auto`, `selenium`, `playwright`) | `auto` |
| `--output-dir` | 输出目录 | `./screenshots` |
| `--batch` | 批量截图演示场景 | 否 |
| `--filename` | 单个截图文件名 | 自动生成 |
| `--wait-time` | 等待页面加载时间(秒) | `3` |
| `--full-page` | 截取全页 | 是 |

## 🎬 演示场景

批量截图时会自动截取以下场景：

1. **初始界面** - 应用启动后的初始界面
2. **对话界面** - 用户与AI对话的界面
3. **知识库管理** - 知识库上传和管理界面
4. **学习报告** - 学习报告生成界面
5. **习题生成** - 智能习题生成界面

## 🛠️ 技术实现

### 支持的截图方法

#### 1. Selenium + Chrome WebDriver
- **优点**: 稳定可靠，功能丰富
- **安装**: `pip install selenium`
- **特点**: 使用无头Chrome浏览器

#### 2. Playwright
- **优点**: 现代化的自动化工具，支持多种浏览器
- **安装**: `pip install playwright && playwright install`
- **特点**: 内置多种浏览器支持

#### 3. 自动选择
- **逻辑**: 优先尝试Selenium，失败则使用Playwright
- **推荐**: 使用 `--method auto` 让工具自动选择最佳方法

## 📁 输出文件

截图保存在 `./screenshots/` 目录中：

```
screenshots/
├── streamlit_screenshot_20241219_143022.png    # 单个截图
├── scenario_01_初始界面.png                   # 批量截图
├── scenario_02_对话界面.png
├── scenario_03_知识库管理.png
├── scenario_04_学习报告.png
└── scenario_05_习题生成.png
```

## 💡 使用建议

### 最佳实践

1. **确保应用运行**: 先启动Streamlit应用再截图
2. **等待加载**: 对于动态内容，适当增加 `--wait-time`
3. **全页截图**: 默认启用，适合长页面
4. **批量模式**: 演示多个功能场景时推荐

### 示例命令

```bash
# 基本截图
python screenshot_tool.py

# 高质量截图（等待更长时间）
python screenshot_tool.py --wait-time 5 --full-page

# 批量演示
python screenshot_tool.py --batch --method playwright

# 自定义输出
python screenshot_tool.py --output-dir ./docs/screenshots --filename interface_demo
```

## 🔧 故障排除

### 常见问题

#### 1. WebDriver错误
```
解决方案:
- 安装Chrome浏览器
- 或使用Playwright: --method playwright
```

#### 2. 页面加载超时
```
解决方案:
- 增加等待时间: --wait-time 10
- 检查Streamlit应用是否正常运行
```

#### 3. 截图为空白
```
解决方案:
- 确认URL正确
- 等待页面完全加载
- 检查防火墙设置
```

#### 4. 依赖安装失败
```
解决方案:
# Windows
pip install selenium webdriver-manager

# Linux/Mac
pip install selenium
# ChromeDriver会自动下载
```

## 📊 性能对比

| 方法 | 速度 | 稳定性 | 功能丰富度 | 推荐指数 |
|------|------|--------|-----------|----------|
| Selenium | 中等 | 高 | 高 | ⭐⭐⭐⭐⭐ |
| Playwright | 快 | 高 | 高 | ⭐⭐⭐⭐⭐ |
| 自动选择 | 自适应 | 高 | 高 | ⭐⭐⭐⭐⭐ |

## 🎨 自定义开发

如果需要自定义截图逻辑，可以修改 `screenshot_tool.py` 中的方法：

```python
# 自定义截图前处理
def custom_preprocessing(self, driver_or_page):
    # 添加自定义的页面预处理逻辑
    pass

# 自定义截图后处理
def custom_postprocessing(self, screenshot_path):
    # 添加水印、裁剪等后处理
    pass
```

## 📝 许可证

本工具遵循项目的许可证协议。
