#!/usr/bin/env python3
"""测试知识点复习到期功能"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graphs.memory_store import MemoryStore
from datetime import datetime

def test_due_for_review():
    """测试知识点复习到期检测"""
    
    memory_store = MemoryStore.get_instance()
    
    # 清除测试数据
    memory_store.clear_child_data("test_due_child")
    
    print("=" * 60)
    print("测试：知识点复习到期检测")
    print("=" * 60)
    
    # 添加一个知识点
    kp_id = memory_store.add_knowledge_point(
        child_id="test_due_child",
        point_type="word",
        content="蝴蝶",
        context="孩子在观察蝴蝶"
    )
    
    print(f"✅ 添加知识点：蝴蝶")
    print(f"   初始复习时间：{memory_store.get_knowledge_point_by_content('test_due_child', '蝴蝶')['next_review_time']}")
    
    # 获取数据并手动修改复习时间为过去
    child_data = memory_store._get_child_data("test_due_child")
    for kp in child_data["knowledge_points"]:
        if kp["id"] == kp_id:
            # 设置为5分钟前
            from datetime import timedelta
            past_time = datetime.now() - timedelta(minutes=5)
            kp["next_review_time"] = past_time.isoformat()
            print(f"✅ 手动设置复习时间：{past_time.isoformat()}")
    
    # 检查待复习
    due_kps = memory_store.get_due_for_review("test_due_child")
    print(f"\n📋 待复习知识点数量：{len(due_kps)}")
    for kp in due_kps:
        print(f"   - {kp['content']} (类型: {kp['type']})")
        print(f"     掌握程度：{kp['mastery_level']}/5")
        print(f"     复习次数：{kp['review_count']}")
    
    if len(due_kps) > 0:
        print("\n✅ 复习到期检测功能正常！")
    else:
        print("\n❌ 复习到期检测失败！")

if __name__ == "__main__":
    test_due_for_review()
