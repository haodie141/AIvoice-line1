"""测试时间感知功能"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from src.graphs.memory_store import MemoryStore
from datetime import datetime, timedelta

# 初始化MemoryStore
memory_store = MemoryStore.get_instance()
child_id = "test_child_001"

# 清空测试数据
memory_store.clear_child_data(child_id)

# 添加有效作业（1天后截止）
homework_id_1 = memory_store.add_homework(
    child_id=child_id,
    subject="数学",
    description="完成第5页的练习题",
    deadline_days=1
)
print(f"✓ 添加有效作业: {homework_id_1}")

# 添加过期作业（-8天前就过期了，模拟7天前的作业）
homework_id_2 = memory_store.add_homework(
    child_id=child_id,
    subject="语文",
    description="背诵古诗",
    deadline_days=-8
)
print(f"✓ 添加过期作业: {homework_id_2}（应该被过滤）")

# 添加已完成的作业
homework_id_3 = memory_store.add_homework(
    child_id=child_id,
    subject="英语",
    description="背诵单词",
    deadline_days=1
)
memory_store.complete_homework(child_id, homework_id_3)
print(f"✓ 添加已完成作业: {homework_id_3}（应该被过滤）")

# 测试获取所有作业
all_homework = memory_store.get_homework_list(child_id)
print(f"\n所有作业数量: {len(all_homework)}")
for hw in all_homework:
    print(f"  - {hw['subject']}: {hw['description']}, 截止: {hw['deadline']}, 完成: {hw['completed']}")

# 测试获取有效作业（应该只返回未过期且未完成的作业）
valid_homework = memory_store.get_valid_homework(child_id)
print(f"\n有效作业数量: {len(valid_homework)}")
for hw in valid_homework:
    print(f"  - {hw['subject']}: {hw['description']}, 截止: {hw['deadline']}")

# 验证结果
assert len(valid_homework) == 1, f"应该只有1个有效作业，实际: {len(valid_homework)}"
assert valid_homework[0]['subject'] == "数学", "有效作业应该是数学"
print("\n✅ 时间感知功能测试通过！")
print("   - 过期作业被正确过滤")
print("   - 已完成作业被正确过滤")
print("   - 有效作业被正确保留")
