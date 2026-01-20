#!/usr/bin/env python
"""获取工作流的输入输出Schema"""
import sys
import os
import json

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graphs.graph import main_graph

print("=" * 80)
print("工作流输入 Schema (Input Schema)")
print("=" * 80)
input_schema = main_graph.get_input_schema().model_json_schema()
print(json.dumps(input_schema, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("工作流输出 Schema (Output Schema)")
print("=" * 80)
output_schema = main_graph.get_output_schema().model_json_schema()
print(json.dumps(output_schema, indent=2, ensure_ascii=False))
