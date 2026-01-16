"""完整的作业流程测试"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from graphs.memory_store import MemoryStore

child_id = "test_full_homework"
memory_store = MemoryStore.get_instance()

# 清空测试数据
memory_store.clear_child_data(child_id)

print("=" * 60)
print("步骤1：添加数学作业")
print("=" * 60)

hw_id = memory_store.add_homework(
    child_id=child_id,
    subject="数学",
    description="完成第5页的练习题",
    deadline_days=1
)
print(f"✓ 添加数学作业: {hw_id}")

valid_homework = memory_store.get_valid_homework(child_id)
print(f"有效作业数量: {len(valid_homework)}")
for hw in valid_homework:
    print(f"  - {hw['subject']}: {hw['description']}, 状态: {'完成' if hw['completed'] else '未完成'}")

print("\n" + "=" * 60)
print("步骤2：测试完整流程")
print("=" * 60)
print("\n请按照以下步骤进行test_run测试：")
print("\n第1次对话（孩子说要做完作业）：")
print('test_run(params={\\"child_id\\": \\"test_full_homework\\", \\"child_name\\": \\"小明\\", \\"child_age\\": 8, \\"child_interests\\": [\\"画画\\"], \\"trigger_type\\": \\"conversation\\", \\"user_input_text\\": \\"我做完了数学作业\\"})')
print("\n期望AI确认：'你确定已经完成数学作业了吗？'")
print("\n第2次对话（孩子确认）：")
print('test_run(params={\\"child_id\\": \\"test_full_homework\\", \\"child_name\\": \\"小明\\", \\"child_age\\": 8, \\"child_interests\\": [\\"画画\\"], \\"trigger_type\\": \\"conversation\\", \\"user_input_text\\": \\"是的，我做完了\\"})')
print("\n期望AI：表扬并更新作业状态")
print("\n第3次对话（再次检查）：")
print('test_run(params={\\"child_id\\": \\"test_full_homework\\", \\"child_name\\": \\"小明\\", \\"child_age\\": 8, \\"child_interests\\": [\\"画画\\"], \\"trigger_type\\": \\"remind\\"})')
print("\n期望：没有需要完成的作业")
