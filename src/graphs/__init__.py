"""
主入口 - 支持多种模式
1. realtime_call: 低延迟实时通话（ASR→LLM→TTS）
2. full_companion: 完整陪伴机器人（包含作业管理、主动关心等）
3. detailed: 可视化模式（步骤级拆分，类似扣子工作流）
"""

from .graph import main_graph as full_companion_graph
from .realtime_call_graph import realtime_call_graph

# 默认使用完整陪伴机器人
default_graph = full_companion_graph

# 可用的图
AVAILABLE_GRAPHS = {
    "full_companion": full_companion_graph,      # 完整陪伴机器人
    "realtime_call": realtime_call_graph         # 低延迟实时通话
}


def get_graph(mode: str = "full_companion"):
    """
    获取指定模式的图

    Args:
        mode: 模式名称
            - full_companion: 完整陪伴机器人（默认）
            - realtime_call: 低延迟实时通话

    Returns:
        编译后的图
    """
    if mode in AVAILABLE_GRAPHS:
        return AVAILABLE_GRAPHS[mode]
    else:
        print(f"⚠️ 未知模式: {mode}，使用默认模式: full_companion")
        return default_graph


# 向后兼容：保持 main_graph 变量
main_graph = default_graph
