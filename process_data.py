import os
import json
import pickle
from document_loader import DocumentLoader
from text_splitter import TextSplitter
from vector_store import VectorStore

from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_DB_PATH

# 缓存文件路径
DOCUMENTS_CACHE = "./cache/documents.pkl"
CHUNKS_CACHE = "./cache/chunks.pkl"

def save_cache(data, cache_path):
    """保存数据到缓存文件"""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"✅ 已保存缓存: {cache_path}")

def load_cache(cache_path):
    """从缓存文件加载数据"""
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        print(f"✅ 已加载缓存: {cache_path}")
        return data
    return None

def clear_cache():
    """清理所有缓存文件"""
    cache_files = [DOCUMENTS_CACHE, CHUNKS_CACHE]
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"🗑️ 已删除缓存: {cache_file}")

def show_cache_info():
    """显示缓存信息"""
    print("\n📊 缓存状态:")
    for cache_name, cache_path in [("文档数据", DOCUMENTS_CACHE), ("切分数据", CHUNKS_CACHE)]:
        if os.path.exists(cache_path):
            size = os.path.getsize(cache_path) / 1024 / 1024  # MB
            print(f"  ✅ {cache_name}: {size:.2f} MB")
        else:
            print(f"  ❌ {cache_name}: 无缓存")


def main():
    if not os.path.exists(DATA_DIR):
        print(f"数据目录不存在: {DATA_DIR}")
        print("请创建数据目录并放入PDF、PPTX、DOCX或TXT文件")
        return

    # 初始化组件
    loader = DocumentLoader(
        data_dir=DATA_DIR,
    )
    splitter = TextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    vector_store = VectorStore(db_path=VECTOR_DB_PATH)

    print("🚀 开始数据处理流程...")
    show_cache_info()

    # 步骤1: 加载文档
    print("\n📚 步骤1: 加载文档...")
    documents = load_cache(DOCUMENTS_CACHE)
    if documents is None:
        print("未找到缓存，开始加载文档...")
        documents = loader.load_all_documents()
        if not documents:
            print("未找到任何文档")
            return
        save_cache(documents, DOCUMENTS_CACHE)
    else:
        print(f"使用缓存的文档数据，共 {len(documents)} 个文档")

    # 步骤2: 切分文档
    print("\n✂️ 步骤2: 切分文档...")
    chunks = load_cache(CHUNKS_CACHE)
    if chunks is None:
        print("未找到缓存，开始切分文档...")
        chunks = splitter.split_documents(documents)
        save_cache(chunks, CHUNKS_CACHE)
    else:
        print(f"使用缓存的切分数据，共 {len(chunks)} 个块")

    # 步骤3: 存储到向量数据库
    print("\n💾 步骤3: 存储到向量数据库...")
    vector_store.clear_collection()
    vector_store.add_documents(chunks)

    print("\n🎉 数据处理完成！可以运行main.py开始对话")

    # 可选：清理缓存文件
    print("\n🧹 缓存管理选项:")
    print("  1. 保留缓存 (默认，用于下次加速)")
    print("  2. 清理所有缓存")
    print("请选择 (1/2): ", end="")
    try:
        response = input().strip()
        if response == '2':
            clear_cache()
            print("✅ 缓存文件已清理")
        else:
            print("ℹ️ 缓存文件保留，可用于下次加速处理")
    except:
        print("ℹ️ 缓存文件保留，可用于下次加速处理")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "clear-cache":
            print("🧹 清理所有缓存文件...")
            clear_cache()
            print("✅ 缓存清理完成")
        elif command == "cache-info":
            show_cache_info()
        else:
            print("使用方法:")
            print("  python process_data.py          # 运行数据处理")
            print("  python process_data.py clear-cache  # 清理缓存")
            print("  python process_data.py cache-info   # 查看缓存状态")
    else:
        main()
