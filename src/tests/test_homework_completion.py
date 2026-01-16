"""测试作业自动完成功能"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from graphs.memory_store import MemoryStore

# 初始化MemoryStore
memory_store = MemoryStore.get_instance()
child_id = "test_homework_completion"

# 清空测试数据
memory_store.clear_child_data(child_id)

print("=" * 60)
print("测试1：添加数学作业")
print("=" * 60)

# 添加一个数学作业（1天后截止）
hw_id = memory_store.add_homework(
    child_id=child_id,
    subject="数学",
    description="完成第5页的练习题",
    deadline_days=1
)
print(f"✓ 添加数学作业: {hw_id}")

# 获取有效作业
valid_homework = memory_store.get_valid_homework(child_id)
print(f"当前有效作业数量: {len(valid_homework)}")
for hw in valid_homework:
    print(f"  - {hw['subject']}: {hw['description']}, 状态: {'完成' if hw['completed'] else '未完成'}")

print("\n" + "=" * 60)
print("测试2：模拟孩子说'我做完了数学作业'")
print("=" * 60)
print("注意：实际测试需要通过test_run调用工作流")
print("这里只是演示数据准备")
print("\n期望行为：")
print("1. AI识别到孩子说'做完了数学作业'")
print("2. AI确认：'你确定已经完成数学作业了吗？'")
print("3. 孩子再次确认")
print("4. AI返回JSON: {\"homework_completed\": true, \"subject\": \"数学\", \"confirmed\": true}")
print("5. 作业状态自动更新为已完成")
print("\n请使用以下test_run命令测试完整流程：")
print('test_run(params={\\"child_id\\": \\"test_homework_completion\\", \\"child_name\\": \\"小明\\", \\"child_age\\": 8, \\"child_interests\\": [\\"画画\\"], \\"trigger_type\\": \\"conversation\\", \\"user_input_text\\": \\"我做完了数学作业\\"})')
