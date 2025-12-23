#API配置
OPENAI_API_KEY = "sk-xxx"
OPENAI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-max"
OPENAI_EMBEDDING_MODEL = "text-embedding-v4"
OPENAI_VL_MODEL = "qwen3-vl-plus"

# Tavily搜索API配置
TAVILY_API_KEY = "xxx"

# 数据目录配置
DATA_DIR = "./data"

#向量数据库配置
VECTOR_DB_PATH = "./vector_db"
COLLECTION_NAME = "NLP_Project_Collection"

# 检索配置
ENABLE_ADVANCED_RAG = True
DEFAULT_RETRIEVAL_STRATEGY = "HYBRID"
RRF_K = 60

# 文本处理配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_TOKENS = 1500

# RAG配置
TOP_K = 5
