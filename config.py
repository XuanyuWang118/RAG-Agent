#API配置
OPENAI_API_KEY = "sk-e6dcc423c4cd497c92fe6b26047b119d"
OPENAI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-max"
OPENAI_EMBEDDING_MODEL = "text-embedding-v4"

# Tavily搜索API配置
TAVILY_API_KEY = "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"

# 数据目录配置
DATA_DIR = "./data"

#向量数据库配置
VECTOR_DB_PATH = "./vector_db"
COLLECTION_NAME = "NLP_Project_Collection"

# 文本处理配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_TOKENS = 1500

# RAG配置
TOP_K = 5
