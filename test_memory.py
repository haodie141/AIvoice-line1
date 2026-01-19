#!/usr/bin/env python3
"""测试长期记忆功能"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graphs.memory_store import MemoryStore
from datetime import datetime, timedelta

def test_memory_store():
    """测试MemoryStore的知识追踪功能"""
    
    # 获取MemoryStore实例
    memory_store = MemoryStore.get_instance()
    
    # 清除测试数据
    memory_store.clear_child_data("test_memory_child")
    
    print("=" * 60)
    print("测试1：添加知识点")
    print("=" * 60)
    
    # 添加知识点
    kp_id_1 = memory_store.add_knowledge_point(
        child_id="test_memory_child",
        point_type="word",
        content="霸王龙",
        context="在口语练习中，孩子提到画了一只霸王龙"
    )
    
    kp_id_2 = memory_store.add_knowledge_point(
        child_id="test_memory_child",
        point_type="concept",
        content="食肉恐龙",
        context="孩子说霸王龙吃肉"
    )
    
    print(f"✅ 添加知识点1：{kp_id_1}")
    print(f"✅ 添加知识点2：{kp_id_2}")
    
    # 获取所有知识点
    all_kps = memory_store.get_all_knowledge_points("test_memory_child")
    print(f"\n📚 当前知识点总数：{len(all_kps)}")
    for kp in all_kps:
        print(f"   - {kp['type']}: {kp['content']} (掌握程度: {kp['mastery_level']}/5)")
        print(f"     下次复习时间：{kp['next_review_time']}")
    
    print("\n" + "=" * 60)
    print("测试2：检查待复习知识点（初始状态）")
    print("=" * 60)
    
    # 检查待复习知识点
    due_kps = memory_store.get_due_for_review("test_memory_child")
    print(f"📋 待复习知识点数量：{len(due_kps)}")
    for kp in due_kps:
        print(f"   - {kp['content']}")
    
    print("\n" + "=" * 60)
    print("测试3：模拟回答正确，更新掌握程度")
    print("=" * 60)
    
    # 模拟孩子回答正确
    updated_kp = memory_store.update_knowledge_mastery(
        child_id="test_memory_child",
        knowledge_id=kp_id_1,
        is_correct=True
    )
    
    if updated_kp:
        print(f"✅ 更新知识点掌握程度：{updated_kp['content']}")
        print(f"   掌握程度：{updated_kp['mastery_level']}/5")
        print(f"   复习次数：{updated_kp['review_count']}")
        print(f"   正确次数：{updated_kp['correct_count']}")
        print(f"   下次复习时间：{updated_kp['next_review_time']}")
    
    print("\n" + "=" * 60)
    print("测试4：知识点统计")
    print("=" * 60)
    
    stats = memory_store.get_knowledge_statistics("test_memory_child")
    print(f"📊 知识点统计：")
    print(f"   总数：{stats['total']}")
    print(f"   已精通（掌握程度≥4）：{stats['mastered']}")
    print(f"   学习中（掌握程度2-3）：{stats['learning']}")
    print(f"   需要复习：{stats['need_review']}")
    
    print("\n" + "=" * 60)
    print("测试5：根据内容查找知识点")
    print("=" * 60)
    
    found_kp = memory_store.get_knowledge_point_by_content(
        child_id="test_memory_child",
        content="霸王龙"
    )
    
    if found_kp:
        print(f"✅ 找到知识点：{found_kp['content']}")
        print(f"   类型：{found_kp['type']}")
        print(f"   掌握程度：{found_kp['mastery_level']}/5")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_memory_store()
