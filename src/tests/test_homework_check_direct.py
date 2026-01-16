"""直接测试作业检查节点"""
import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from graphs.memory_store import MemoryStore
from graphs.node import homework_check_node
from graphs.state import HomeworkCheckInput
from datetime import datetime

# 初始化MemoryStore
memory_store = MemoryStore.get_instance()
child_id = "test_child_003"

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

# 测试作业检查节点
print("\n测试作业检查节点...")
node_input = HomeworkCheckInput(
    homework_list=[],
    current_time=datetime.now().isoformat(),
    child_id=child_id
)

# 创建模拟的config和runtime
class MockConfig(dict):
    def __init__(self):
        super().__init__()
        self['metadata'] = {}

class MockRuntime:
    class MockContext:
        pass
    
    def __init__(self):
        self.context = self.MockContext()

config = MockConfig()
runtime = MockRuntime()

# 调用作业检查节点
try:
    result = homework_check_node(node_input, config, runtime)
    print(f"\n作业状态: {result.homework_status}")
    print(f"需要提醒: {result.need_remind}")
    print(f"提醒消息: {result.remind_message}")
    
    # 验证结果
    if result.need_remind and "数学" in result.remind_message and "英语" in result.remind_message:
        print("\n✅ 作业检查节点测试通过！")
    else:
        print(f"\n❌ 作业检查节点测试失败！")
        print(f"   预期提醒数学和英语作业")
        print(f"   实际消息: {result.remind_message}")
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
