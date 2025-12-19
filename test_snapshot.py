#!/usr/bin/env python3
"""
测试快照功能
"""

import os
import json
import datetime
from unittest.mock import Mock

def test_snapshot_save():
    """测试快照保存功能"""

    # 模拟session_state
    mock_session_state = {
        "current_chat_id": "test_chat_123",
        "chat_history": [
            {"role": "user", "content": "什么是词向量？"},
            {"role": "assistant", "content": "词向量是..."}
        ],
        "chat_list": [
            {"id": "test_chat_123", "title": "测试对话", "timestamp": "2024-01-01", "message_count": 2}
        ],
        "generated_quiz": [{"question": "测试题目"}],
        "quiz_answers": {"q1": "A"},
        "quiz_show_results": {"q1": True},
        "rag_agent": Mock()
    }

    # 模拟rag_agent的方法
    mock_session_state["rag_agent"].vector_store.get_collection_count.return_value = 150
    mock_session_state["rag_agent"].model = "qwen3-max-2025-09-23"

    print("🧪 测试快照保存功能")
    print("=" * 40)

    try:
        # 创建快照数据（复制app.py中的逻辑）
        snapshot = {
            "timestamp": datetime.datetime.now().isoformat(),
            "current_chat_id": mock_session_state["current_chat_id"],
            "chat_history": mock_session_state["chat_history"],
            "chat_list": mock_session_state["chat_list"],
            "system_status": {
                "rag_agent_initialized": mock_session_state["rag_agent"] is not None,
                "collection_count": 0,
                "model_name": getattr(mock_session_state["rag_agent"], 'model', 'unknown') if mock_session_state["rag_agent"] else 'unknown'
            },
            "quiz_state": {
                "generated_quiz": mock_session_state.get('generated_quiz', []),
                "quiz_answers": mock_session_state.get('quiz_answers', {}),
                "quiz_show_results": mock_session_state.get('quiz_show_results', {})
            }
        }

        # 获取文档数量
        if mock_session_state["rag_agent"]:
            try:
                snapshot["system_status"]["collection_count"] = mock_session_state["rag_agent"].vector_store.get_collection_count()
            except Exception as e:
                print(f"获取文档数量失败: {e}")

        # 生成快照文件名
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"snapshot_{timestamp_str}.json"

        # 确保快照目录存在
        snapshot_dir = "./snapshots"
        os.makedirs(snapshot_dir, exist_ok=True)

        # 保存快照文件
        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        print(f"✅ 快照保存成功: {snapshot_filename}")
        print(f"📁 保存位置: {snapshot_path}")

        # 验证文件存在
        if os.path.exists(snapshot_path):
            print("✅ 快照文件已创建")

            # 读取并验证内容
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                loaded_snapshot = json.load(f)

            print("📊 快照内容验证:"            print(f"  - 时间戳: {loaded_snapshot['timestamp']}")
            print(f"  - 当前对话ID: {loaded_snapshot['current_chat_id']}")
            print(f"  - 消息数量: {len(loaded_snapshot['chat_history'])}")
            print(f"  - 系统状态: {loaded_snapshot['system_status']}")
            print(f"  - 题目状态: {loaded_snapshot['quiz_state']}")

            # 清理测试文件
            os.remove(snapshot_path)
            print("🧹 测试文件已清理")

        else:
            print("❌ 快照文件创建失败")

    except Exception as e:
        print(f"❌ 快照保存测试失败: {str(e)}")

def test_snapshot_load():
    """测试快照加载功能"""

    print("\n📂 测试快照加载功能")
    print("=" * 40)

    # 创建测试快照文件
    test_snapshot = {
        "timestamp": datetime.datetime.now().isoformat(),
        "current_chat_id": "load_test_chat",
        "chat_history": [{"role": "user", "content": "加载测试"}],
        "chat_list": [],
        "system_status": {"rag_agent_initialized": True, "collection_count": 100},
        "quiz_state": {"generated_quiz": [], "quiz_answers": {}, "quiz_show_results": {}}
    }

    snapshot_dir = "./snapshots"
    os.makedirs(snapshot_dir, exist_ok=True)
    test_file = os.path.join(snapshot_dir, "test_snapshot.json")

    try:
        # 保存测试快照
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_snapshot, f, ensure_ascii=False, indent=2)

        # 模拟加载过程
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_snapshot = json.load(f)

        print("✅ 快照加载成功")
        print(f"📊 加载的对话ID: {loaded_snapshot['current_chat_id']}")
        print(f"📝 加载的消息: {len(loaded_snapshot['chat_history'])}")

        # 清理测试文件
        os.remove(test_file)
        print("🧹 测试文件已清理")

    except Exception as e:
        print(f"❌ 快照加载测试失败: {str(e)}")

if __name__ == "__main__":
    test_snapshot_save()
    test_snapshot_load()
    print("\n🎯 快照功能测试完成！")
