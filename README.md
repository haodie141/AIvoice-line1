# AI 陪伴孩子智能体工作流

> 一个基于 LangGraph 的智能 AI 陪伴系统，支持实时对话、作业提醒、口语练习、联网检索和长期记忆功能。

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [运行模式](#运行模式)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [更新日志](#更新日志)

## 项目简介

AI 陪伴孩子智能体是一个基于 LangGraph 框架构建的智能陪伴系统，旨在为孩子提供一个温暖、智能、有趣的 AI 伙伴。系统通过语音交互、实时对话、作业辅导、口语练习等功能，全方位陪伴孩子的成长。

### 核心价值

- **温暖陪伴**：使用适合孩子年龄的简单、生动语言，保持亲切关爱的语气
- **智能辅导**：基于时间推移算法的作业提醒和苏格拉底式口语练习
- **长期记忆**：使用间隔重复算法（简化版 SM-2）自动管理知识点和复习计划
- **低延迟**：实时通话模式确保 1-2 秒的响应时间
- **可视化友好**：提供类似扣子工作流的可视化模式，方便理解和调试

## 功能特性

### 1. 实时对话与语音交互
- 支持纯音频输入，无需填写其他参数
- 实时语音识别（ASR）和语音合成（TTS）
- 智能意图识别和上下文理解
- 联网检索功能，基于 LLM 判断是否需要搜索

### 2. 作业提醒系统
- 基于时间推移算法，自动提醒待办作业
- 智能判断作业完成意图（双 LLM 架构）
- 过期作业自动过滤（7 天前的作业不再提醒）
- 作业状态持久化管理

### 3. 主动关心功能
- 定时主动发起关心对话
- 情绪识别和情感回应
- 根据孩子的状态提供个性化建议

### 4. 口语练习引擎
- **主动引导模式**：区别于传统一问一答，多阶段对话
  - 场景化练习库（日常生活、学校、兴趣等）
  - 苏格拉底式提问，引导孩子深入思考
  - 追问延伸，拓展对话深度
  - 总结反馈，提供正面鼓励
- **知识追踪系统**：自动识别对话中的知识点
- **智能复习**：基于间隔重复算法（简化版 SM-2）自动安排复习计划

### 5. 长期记忆管理
- 知识点自动识别和存储
- 间隔重复复习算法
- 复习时机智能计算
- 知识掌握度评估

### 6. 多模式运行
- **完整模式**（full_companion）：功能完整，性能优先
- **可视化模式**（detailed）：步骤级节点拆分，类似扣子工作流
- **实时通话模式**（realtime_call）：低延迟，1-2 秒响应

## 技术栈

- **核心框架**
  - Python 3.12
  - LangGraph 1.0
  - LangChain 1.0
  - Pydantic
  - Jinja2

- **集成服务**
  - 大语言模型（集成豆包、DeepSeek、Kimi）
  - 语音识别（豆包语音）
  - 语音合成（豆包语音）
  - 联网搜索（融合信息搜索）

- **数据处理**
  - 内存存储（MemoryStore）
  - 知识追踪系统
  - 间隔重复算法（简化版 SM-2）

- **部署工具**
  - coze-coding-dev-sdk
  - 环境变量配置

## 项目结构

```
├── config/                          # 配置目录
│   ├── main_dialogue_llm_cfg.json   # 主对话大模型配置
│   ├── judgment_llm_cfg.json        # 判断LLM配置（作业意图识别）
│   ├── spoken_practice_llm_cfg.json # 口语练习大模型配置
│   ├── realtime_call_llm_cfg.json   # 实时通话大模型配置
│   ├── prologue_llm_cfg.json        # 开场白大模型配置
│   ├── prologue_reminder_llm_cfg.json # 作业提醒开场白配置
│   ├── review_guidance_llm_cfg.json # 复习引导大模型配置
│   └── search_judgment_llm_cfg.json # 搜索判断大模型配置
├── docs/                            # 文档目录
│   ├── 可视化模式快速开始.md         # 可视化模式使用指南
│   ├── 模式切换指南.md               # 模式切换详细说明
│   ├── 节点内部流程说明.md           # 各节点详细流程
│   └── 可视化优化说明.md             # 可视化优化思路
├── scripts/                         # 脚本目录
│   ├── local_run.sh                 # 本地运行脚本
│   └── http_run.sh                  # HTTP服务启动脚本
├── src/                             # 项目源码
│   ├── agents/                      # Agent代码目录（当前为空）
│   ├── graphs/                      # 工作流编排代码
│   │   ├── state.py                 # 状态定义（完整模式）
│   │   ├── node.py                  # 节点函数（完整模式）
│   │   ├── graph.py                 # 主图编排（完整模式）
│   │   ├── visual_state.py          # 状态定义（可视化模式）
│   │   ├── visual_node.py           # 节点函数（可视化模式）
│   │   └── visual_graph.py          # 主图编排（可视化模式）
│   ├── storage/                     # 数据存储代码
│   │   ├── memory_store.py          # 内存存储实现
│   │   ├── knowledge_tracker.py     # 知识追踪系统
│   │   └── database.py              # 数据库连接（已优化为内存优先）
│   ├── tools/                       # 工具定义
│   │   ├── web_search_tool.py       # 联网搜索工具
│   │   └── voice_tool.py            # 语音处理工具
│   ├── utils/                       # 工具函数
│   │   ├── file/                    # 文件处理工具
│   │   └── runtime_ctx/             # 运行时上下文
│   ├── tests/                       # 单元测试
│   └── main.py                      # 运行主入口
├── assets/                          # 资源目录
│   └── mock/                        # 测试数据
├── test_visual_mode.py              # 可视化模式测试脚本
├── requirements.txt                 # 依赖包列表
├── README.md                        # 项目文档
└── .coze                           # Coze配置文件
```

## 快速开始

### 环境准备

- Python 3.12 或更高版本
- pip 包管理器
- 有效的互联网连接（用于访问大模型 API）

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/haodie141/AIvoice-line1.git
cd AIvoice-line1

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件（可选）：

```bash
# 设置运行模式（可选，默认为 full_companion）
COZE_GRAPH_MODE=full_companion  # 完整模式
# COZE_GRAPH_MODE=detailed        # 可视化模式
# COZE_GRAPH_MODE=realtime_call   # 实时通话模式

# 设置工作目录（可选，默认为当前目录）
COZE_WORKSPACE_PATH=/path/to/workspace
```

### 运行测试

```bash
# 测试完整模式
COZE_GRAPH_MODE=full_companion python test_visual_mode.py

# 测试可视化模式
COZE_GRAPH_MODE=detailed python test_visual_mode.py

# 测试实时通话模式
COZE_GRAPH_MODE=realtime_call python test_visual_mode.py
```

## 使用指南

### 本地运行

#### 运行完整工作流

```bash
bash scripts/local_run.sh -m flow
```

#### 运行单个节点

```bash
bash scripts/local_run.sh -m node -n node_name
```

### 启动 HTTP 服务

```bash
# 默认端口 5000
bash scripts/http_run.sh -m http -p 5000

# 自定义端口
bash scripts/http_run.sh -m http -p 8080
```

### 工作流输入

工作流支持以下输入参数：

```python
{
    "audio_file": "https://example.com/audio.mp3",  # 音频文件URL（必需）
    "session_id": "session_123",                     # 会话ID（可选）
    "user_profile": {                                # 用户画像（可选）
        "age": 10,
        "name": "小明",
        "interests": ["编程", "阅读", "运动"]
    }
}
```

### 工作流输出

工作流返回以下结果：

```python
{
    "response_text": "你好！我是你的AI朋友，今天有什么可以帮你的吗？",  # 回复文本
    "audio_url": "https://example.com/response.mp3",                    # 语音合成URL
    "spoken_practice": {                                                 # 口语练习信息（如有）
        "is_active": True,
        "scenario": "daily_conversation",
        "feedback": "说得很好！继续加油！"
    },
    "homework_reminder": {                                               # 作业提醒（如有）
        "has_reminder": True,
        "subject": "数学",
        "task": "完成练习册第10页",
        "due_date": "2024-12-20"
    },
    "review_suggestions": [                                             # 复习建议（如有）
        {
            "topic": "英语单词",
            "reason": "上次学习后已过7天，建议复习"
        }
    ]
}
```

## 运行模式

### 1. 完整模式（full_companion）

**适用场景**：日常使用，功能完整，性能优先

**特点**：
- 包含所有功能模块
- 节点整合度高，执行效率高
- 适合生产环境部署

**节点列表**：
- ASR 节点（语音识别）
- 开场白生成节点
- 作业提醒节点
- 口语练习节点（多阶段）
- 实时对话节点（含联网检索）
- 主对话路由
- 保存记忆节点

**启动方式**：
```bash
export COZE_GRAPH_MODE=full_companion
python src/main.py
```

**详细文档**：见 `docs/节点内部流程说明.md`

### 2. 可视化模式（detailed）

**适用场景**：调试、学习、理解工作流结构

**特点**：
- 步骤级节点拆分，类似扣子工作流
- 每个处理步骤独立为一个节点
- 清晰展示数据流转
- 便于性能监控和问题定位

**节点列表**（共17个节点）：
- ASR 节点
- 开场白生成节点
- 作业提醒节点
- **口语练习拆分为7个节点**：
  1. ASR 节点（口语练习专用）
  2. 复习检查节点
  3. 场景选择节点
  4. 对话引擎节点
  5. 知识点识别节点
  6. 更新记忆节点
  7. TTS 节点（口语练习专用）
- **实时对话拆分为5个节点**：
  1. 搜索判断节点
  2. 联网搜索节点
  3. 上下文构建节点
  4. LLM 生成节点
  5. 作业意图识别节点
- 主对话路由
- 保存记忆节点

**启动方式**：
```bash
export COZE_GRAPH_MODE=detailed
python src/main.py
```

**详细文档**：
- `docs/可视化模式快速开始.md`
- `docs/可视化优化说明.md`

### 3. 实时通话模式（realtime_call）

**适用场景**：实时语音对话，低延迟要求

**特点**：
- 精简节点，只保留核心流程
- ASR → LLM → TTS 三步完成
- 响应时间控制在 1-2 秒
- 去除路由、保存记忆等非必要步骤
- 限制 LLM 的 max_tokens 为 300

**节点列表**：
- ASR 节点（语音识别）
- LLM 节点（对话生成）
- TTS 节点（语音合成）

**启动方式**：
```bash
export COZE_GRAPH_MODE=realtime_call
python src/main.py
```

**性能指标**：
- 平均响应时间：1.5 秒
- 网络要求：稳定的 4G/WiFi
- 推荐场景：实时语音聊天、快速问答

## 配置说明

### 大模型配置

所有大模型配置文件位于 `config/` 目录，使用 JSON 格式：

```json
{
    "config": {
        "model": "model_id",
        "temperature": 0.7,
        "topk": 0.9,
        "max_tokens": 1000
    },
    "tools": ["tool1", "tool2"],
    "sp": "你是一个AI朋友，负责陪伴孩子...",
    "up": "用户说：{{user_input}}"
}
```

**配置项说明**：
- `model`: 模型 ID（豆包、DeepSeek、Kimi 等）
- `temperature`: 温度参数（0.0-1.0），控制回答的随机性
- `topk`: Top-k 采样参数
- `max_tokens`: 最大生成 tokens 数
- `tools`: 使用的工具列表
- `sp`: System Prompt（系统提示词），支持 Jinja2 模板
- `up`: User Prompt（用户提示词），支持 Jinja2 模板

### 提示词优化规则

**严格禁止的内容**：
- 动作描述（如：（微笑）、（点头）、（眨眼）等）
- 表情符号（如：😊、🌟、💡等）

**推荐的语言风格**：
- 适合孩子年龄的简单、生动语言
- 温暖、亲切、充满关爱的语气
- 避免生硬的问答，多用引导式对话

**示例**：

❌ **错误示例**：
```
你好呀！（微笑）今天过得怎么样？😊
```

✅ **正确示例**：
```
你好呀，今天过得怎么样？有没有什么开心的事情想和我分享？
```

### 数据存储配置

系统默认使用内存存储（MemoryStore），无需配置数据库。

如需使用 PostgreSQL 数据库，修改 `src/storage/database.py`：

```python
DATABASE_URL = "postgresql://username:password@localhost:5432/ai_companion"
```

**容错机制**：
- 数据库连接失败时自动降级为内存存储
- 不会抛出异常，保证系统正常运行

## 开发指南

### 添加新节点

1. 在 `src/graphs/state.py` 中定义节点输入输出类型：
```python
class NewNodeInput(BaseModel):
    input_field: str = Field(..., description="输入字段")

class NewNodeOutput(BaseModel):
    output_field: str = Field(..., description="输出字段")
```

2. 在 `src/graphs/node.py` 中实现节点函数：
```python
def new_node(
    state: NewNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> NewNodeOutput:
    """
    title: 新节点标题
    desc: 节点功能描述
    integrations: 使用的集成服务名
    """
    ctx = runtime.context
    # 业务逻辑实现
    return NewNodeOutput(output_field="结果")
```

3. 在 `src/graphs/graph.py` 中添加节点：
```python
builder.add_node("new_node", new_node)
```

### 添加新集成

1. 查询集成详情：
```python
integration_detail(integration_slug_id="integration-xxx")
```

2. 根据集成文档实现工具函数
3. 在 `config/` 中创建配置文件
4. 在节点函数中调用集成服务

### 调试技巧

1. **启用详细日志**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **使用可视化模式**：
```bash
export COZE_GRAPH_MODE=detailed
```

3. **测试单个节点**：
```bash
bash scripts/local_run.sh -m node -n node_name
```

4. **查看工作流状态**：
```python
# 在节点函数中
print(f"当前状态: {state}")
print(f"上下文: {ctx}")
```

### 代码规范

- **导入规范**：禁止使用 `from src.xxx` 绝对导入，使用相对导入 `from .xxx`
- **类型注解**：所有函数参数和返回值必须有类型注解
- **节点隔离**：节点函数使用独立的 Input/Output 类型，禁止使用 GlobalState
- **防御性编程**：外部输入必须判空和类型检查

## 常见问题

### Q1: 如何切换运行模式？

**A**: 设置环境变量 `COZE_GRAPH_MODE`：

```bash
export COZE_GRAPH_MODE=full_companion  # 完整模式
export COZE_GRAPH_MODE=detailed        # 可视化模式
export COZE_GRAPH_MODE=realtime_call   # 实时通话模式
```

详细说明见 `docs/模式切换指南.md`

### Q2: 数据库连接失败怎么办？

**A**: 系统已优化为内存优先模式，数据库连接失败会自动降级为内存存储，不会影响系统运行。如需使用数据库，请检查：
1. 数据库服务是否启动
2. 连接字符串是否正确
3. 网络是否通畅

### Q3: 如何自定义提示词？

**A**: 修改 `config/` 目录下的对应配置文件：
- `main_dialogue_llm_cfg.json` - 主对话提示词
- `spoken_practice_llm_cfg.json` - 口语练习提示词
- 等等...

注意：提示词中禁止包含动作描述和表情符号。

### Q4: 实时通话模式响应速度慢怎么办？

**A**:
1. 检查网络连接是否稳定
2. 确认使用的是实时通话模式（`COZE_GRAPH_MODE=realtime_call`）
3. 减少 LLM 的 `max_tokens` 配置
4. 使用更快的模型（如豆包 Pro）

### Q5: 如何添加新的口语练习场景？

**A**: 修改 `config/spoken_practice_llm_cfg.json`，在系统提示词中添加新场景描述：

```json
{
    "sp": "你是一个口语练习老师，支持以下场景：\n1. 日常生活\n2. 学校场景\n3. 兴趣爱好\n4. [新场景名称]\n\n请根据孩子选择的话题进行对话..."
}
```

### Q6: 作业提醒为什么有时不出现？

**A**: 作业提醒有以下过滤规则：
1. 已完成的作业不提醒
2. 7 天前的过期作业不提醒
3. 非对话模式时不主动提醒
4. 判断为作业完成意图时跳过提醒

### Q7: 如何优化内存占用？

**A**:
1. 使用实时通话模式（节点少，内存占用小）
2. 定期清理过期记忆（修改 `memory_store.py`）
3. 减少 LLM 的 `max_tokens` 配置
4. 限制会话历史长度

### Q8: 支持哪些语音格式？

**A**: 支持常见的音频格式：
- 输入：MP3, WAV, M4A, OGG
- 输出：MP3（默认）

建议使用 MP3 格式，兼容性最好。

### Q9: 如何部署到生产环境？

**A**:
1. 使用 Docker 容器化
2. 配置环境变量（`COZE_GRAPH_MODE`、`COZE_WORKSPACE_PATH`）
3. 使用 HTTP 服务模式（`bash scripts/http_run.sh -m http`）
4. 配置负载均衡和健康检查
5. 监控日志和性能指标

### Q10: 如何贡献代码？

**A**: 欢迎 Pull Request！请遵循以下规范：
1. 保持代码风格一致
2. 添加必要的注释和文档
3. 更新相关文档
4. 确保测试通过

## 更新日志

### v1.0.0 (2024-12-XX)

**新增功能**：
- ✅ 完整的 AI 陪伴系统
- ✅ 三种运行模式（完整、可视化、实时通话）
- ✅ 实时对话与语音交互
- ✅ 作业提醒系统（基于时间推移算法）
- ✅ 口语练习引擎（苏格拉底式提问）
- ✅ 长期记忆管理（间隔重复算法）
- ✅ 联网检索功能
- ✅ 主动关心功能

**技术优化**：
- ✅ 内存存储优先，降级机制完善
- ✅ 双 LLM 架构实现作业意图识别
- ✅ 提示词优化，禁止动作描述和表情符号
- ✅ 低延迟实时通话模式（1-2秒响应）
- ✅ 可视化模式步骤级节点拆分
- ✅ 知识追踪系统和智能复习

**文档完善**：
- ✅ README.md 详细文档
- ✅ 可视化模式快速开始指南
- ✅ 模式切换指南
- ✅ 节点内部流程说明
- ✅ 可视化优化说明

---

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目地址：https://github.com/haodie141/AIvoice-line1
- 问题反馈：提交 GitHub Issue

## 致谢

感谢以下开源项目和工具的支持：
- LangGraph & LangChain
- Pydantic
- 豆包、DeepSeek、Kimi 等大语言模型服务

---

**让 AI 温暖每一个孩子的成长之路** 🌟
