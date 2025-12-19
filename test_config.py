#!/usr/bin/env python3
"""
测试配置是否正确加载
"""

from config import TOP_K, ENABLE_ADVANCED_RAG, DEFAULT_RETRIEVAL_STRATEGY
from tools import QuizGenerationTool
from quiz_generator import QuizGenerator

def test_config():
    """测试配置值"""
    print("🔧 配置测试")
    print("=" * 30)

    print(f"TOP_K = {TOP_K}")
    print(f"ENABLE_ADVANCED_RAG = {ENABLE_ADVANCED_RAG}")
    print(f"DEFAULT_RETRIEVAL_STRATEGY = {DEFAULT_RETRIEVAL_STRATEGY}")

    # 检查TOP_K是否为20
    assert TOP_K == 20, f"TOP_K 应该是 20，但当前是 {TOP_K}"
    print("✅ TOP_K 配置正确：20")

    print("\n🎯 所有配置测试通过！")

if __name__ == "__main__":
    test_config()
