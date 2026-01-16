"""测试作业提醒功能"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from src.graphs.memory_store import MemoryStore

# 初始化MemoryStore
memory_store = MemoryStore.get_instance()
child_id = "test_child_002"

# 清空测试数据
memory_store.clear_child_data(child_id)

# 添加有效作业（数学，1天后截止）
memory_store.add_homework(
    child_id=child_id,
    subject="数学",
    description="完成第5页的练习题",
    deadline_days=1
)
print("✓ 添加数学作业（1天后截止）")

# 添加有效作业（英语，2天后截止）
memory_store.add_homework(
    child_id=child_id,
    subject="英语",
    description="背诵单词",
    deadline_days=2
)
print("✓ 添加英语作业（2天后截止）")

# 获取有效作业
valid_homework = memory_store.get_valid_homework(child_id)
print(f"\n有效作业数量: {len(valid_homework)}")
for hw in valid_homework:
    print(f"  - {hw['subject']}: {hw['description']}")

print("\n现在测试作业提醒功能...")
