"""检查作业状态"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from graphs.memory_store import MemoryStore

child_id = "test_full_homework"
memory_store = MemoryStore.get_instance()

print("=" * 60)
print("检查作业状态")
print("=" * 60)

# 获取孩子的所有数据
child_data = memory_store._get_child_data(child_id)
print(f"孩子数据结构: {list(child_data.keys())}")
print()

valid_homework = memory_store.get_valid_homework(child_id)
print(f"有效作业数量: {len(valid_homework)}")

if len(valid_homework) == 0:
    print("✅ 所有作业已完成或已过期！")
else:
    print("未完成的作业：")
    for hw in valid_homework:
        print(f"  - {hw['subject']}: {hw['description']}")

print("\n所有作业（包括已完成的）：")
all_homework = memory_store.get_homework_list(child_id)
if not all_homework:
    print("⚠️  没有找到任何作业记录")
else:
    for hw in all_homework:
        status = "✓ 已完成" if hw.get("completed", False) else "✗ 未完成"
        print(f"  - {hw['subject']}: {hw['description']} [{status}]")
        print(f"    ID: {hw.get('id', '')}")
        print(f"    创建时间: {hw.get('created_at', '')}")
        print(f"    截止时间: {hw.get('deadline', '')}")
        if hw.get("completed"):
            print(f"    完成时间: {hw.get('completed_at', '')}")
