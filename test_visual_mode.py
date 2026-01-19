#!/usr/bin/env python
"""
测试可视化模式是否能正常工作
"""

import os
import sys

# 添加项目根目录到PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_visual_mode():
    """测试可视化模式"""
    print("=" * 60)
    print("测试可视化模式导入")
    print("=" * 60)
    
    try:
        # 设置环境变量
        os.environ["COZE_GRAPH_MODE"] = "detailed"
        
        # 尝试导入可视化图
        from src.graphs.visual_graph import visual_graph
        
        print("✅ 可视化图导入成功")
        
        # 检查图的节点
        nodes = list(visual_graph.nodes.keys())
        print(f"\n图中的节点数量: {len(nodes)}")
        print(f"节点列表: {nodes}")
        
        # 检查边的数量
        edges = list(visual_graph.edges.keys())
        print(f"\n边的数量: {len(edges)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 可视化模式导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_mode():
    """测试完整模式"""
    print("\n" + "=" * 60)
    print("测试完整模式导入")
    print("=" * 60)
    
    try:
        # 设置环境变量
        os.environ["COZE_GRAPH_MODE"] = "full_companion"
        
        # 尝试导入完整图
        from src.graphs.graph import main_graph
        
        print("✅ 完整图导入成功")
        
        # 检查图的节点
        nodes = list(main_graph.nodes.keys())
        print(f"\n图中的节点数量: {len(nodes)}")
        print(f"节点列表: {nodes}")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整模式导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    visual_ok = test_visual_mode()
    full_ok = test_full_mode()
    
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"可视化模式: {'✅ 通过' if visual_ok else '❌ 失败'}")
    print(f"完整模式: {'✅ 通过' if full_ok else '❌ 失败'}")
    
    if visual_ok and full_ok:
        print("\n🎉 所有测试通过！两种模式都可以正常工作。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
        sys.exit(1)
