# 新的 /run API 返回样例

> 版本: v2.0
> 更新日期: 2024-12-XX

---

## 目录

- [字段说明](#字段说明)
- [场景1：闲聊](#场景1闲聊)
- [场景2：作业查询](#场景2作业查询)
- [场景3：事实查询](#场景3事实查询)
- [场景4：口语练习](#场景4口语练习)
- [场景5：主动关心](#场景5主动关心)
- [场景6：作业提醒](#场景6作业提醒)
- [旧格式兼容性](#旧格式兼容性)

---

## 字段说明

### 响应结构

```typescript
interface GraphOutput {
  // ========== 新增字段 (v2.0) ==========
  quick_response: string;           // 快速回复（优先返回）
  followup_question: string;        // 追问内容
  scenario_type: string;            // 实际执行的场景类型
  execution_path: string[];         // 执行路径（节点列表）
  performance_metrics: PerformanceMetrics;  // 性能指标

  // ========== 原有字段 (v1.0) ==========
  ai_response: string;              // 完整AI响应
  ai_response_audio: string | null; // 音频响应URL
  trigger_type: string;             // 触发类型
  homework_status: string;          // 作业状态
  speaking_practice_count: number;  // 口语练习次数

  // ========== 元数据 ==========
  run_id: string;                   // 运行ID
  timestamp: string;                // 时间戳
}
```

### 性能指标结构

```typescript
interface PerformanceMetrics {
  total_time_ms: number;            // 总耗时（毫秒）
  llm_calls: number;                // LLM 调用次数
  nodes_executed: number;           // 执行的节点数
  memory_load_time_ms: number;      // 记忆加载耗时
  quick_reply_time_ms: number;      // 快速回复耗时
  [node_name: string]: number;      // 各节点耗时
}
```

---

## 场景1：闲聊

### 请求示例

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "child_interests": ["阅读", "运动"],
    "trigger_type": "conversation",
    "user_input_text": "你好呀，今天天气真好！",
    "scenario_type": "chat"
  }'
```

### 响应示例

```json
{
  "quick_response": "是的呢！想出去玩吗？",
  "followup_question": "今天在学校开心吗？",
  "ai_response": "是的呢！今天天气真好，阳光明媚的。你今天在学校过得怎么样？有没有什么开心的事情想和我分享？",
  "ai_response_audio": "https://example.com/audio/chat_response_123.mp3",
  "trigger_type": "conversation",
  "homework_status": "",
  "speaking_practice_count": 0,
  "scenario_type": "chat",
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "quick_chat",
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 1200,
    "llm_calls": 2,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "quick_chat_time_ms": 400,
    "voice_synthesis_time_ms": 450
  },
  "run_id": "run_202412XX_001",
  "timestamp": "2024-12-XX 10:30:45"
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `quick_response` | "是的呢！想出去玩吗？" | 快速回复，优先返回 |
| `followup_question` | "今天在学校开心吗？" | 追问，引导继续对话 |
| `ai_response` | "是的呢！今天天气真好..." | 完整回复 |
| `scenario_type` | "chat" | 识别为闲聊场景 |
| `execution_path` | [...] | 执行了6个节点 |
| `total_time_ms` | 1200 | 总耗时1.2秒 |
| `llm_calls` | 2 | 调用了2次LLM（quick_reply + quick_chat） |

---

## 场景2：作业查询

### 请求示例

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "trigger_type": "conversation",
    "user_input_text": "今天的数学作业写完了",
    "scenario_type": "homework",
    "homework_list": [
      {
        "id": "hw_001",
        "subject": "数学",
        "task": "练习册第10页",
        "due_date": "2024-12-20"
      }
    ]
  }'
```

### 响应示例

```json
{
  "quick_response": "太棒了！",
  "followup_question": "感觉难吗？",
  "ai_response": "太棒了！数学作业写完了，你真厉害！感觉这次练习册的题目难吗？有没有遇到什么难题需要我帮忙的？",
  "ai_response_audio": "https://example.com/audio/homework_response_456.mp3",
  "trigger_type": "conversation",
  "homework_status": "completed",
  "speaking_practice_count": 0,
  "scenario_type": "homework",
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "realtime_conversation",
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 2000,
    "llm_calls": 3,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "realtime_conversation_time_ms": 1200,
    "voice_synthesis_time_ms": 450,
    "homework_check_time_ms": 0  // 跳过了作业检查节点
  },
  "run_id": "run_202412XX_002",
  "timestamp": "2024-12-XX 14:20:30"
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `quick_response` | "太棒了！" | 快速鼓励 |
| `followup_question` | "感觉难吗？" | 关心题目难度 |
| `homework_status` | "completed" | 作业状态自动更新为完成 |
| `scenario_type` | "homework" | 识别为作业场景 |
| `llm_calls` | 3 | 3次LLM调用（quick_reply + realtime_conversation + 作业判断） |

---

## 场景3：事实查询

### 请求示例

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "trigger_type": "conversation",
    "user_input_text": "今天天气怎么样？",
    "scenario_type": "fact_query"
  }'
```

### 响应示例

```json
{
  "quick_response": "让我查一下！",
  "followup_question": "想出去玩吗？",
  "ai_response": "让我查一下！今天天气晴朗，温度15-25度，微风，很适合户外活动。要不要出去走走，或者叫上同学一起去公园玩？",
  "ai_response_audio": "https://example.com/audio/weather_response_789.mp3",
  "trigger_type": "conversation",
  "homework_status": "",
  "speaking_practice_count": 0,
  "scenario_type": "fact_query",
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "realtime_conversation",
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 2500,
    "llm_calls": 2,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "realtime_conversation_time_ms": 1700,
    "search_time_ms": 800,
    "voice_synthesis_time_ms": 450
  },
  "run_id": "run_202412XX_003",
  "timestamp": "2024-12-XX 09:15:22"
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `quick_response` | "让我查一下！" | 先回复，背后搜索 |
| `followup_question` | "想出去玩吗？" | 基于查询结果追问 |
| `scenario_type` | "fact_query" | 识别为事实查询 |
| `search_time_ms` | 800 | 搜索耗时800ms |
| `llm_calls` | 2 | 只调用了2次LLM（规则判断，未调用判断LLM） |

---

## 场景4：口语练习

### 请求示例

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "trigger_type": "practice",
    "user_input_audio": {
      "url": "https://example.com/audio/practice_input.mp3",
      "file_type": "audio"
    }
  }'
```

### 响应示例

```json
{
  "quick_response": "说得很好！",
  "followup_question": "还想说说其他兴趣吗？",
  "ai_response": "说得很好！你表达得很清楚，发音也很标准。还想和我聊聊其他兴趣爱好吗？比如运动、画画什么的？",
  "ai_response_audio": "https://example.com/audio/practice_response_012.mp3",
  "trigger_type": "practice",
  "homework_status": "",
  "speaking_practice_count": 5,
  "scenario_type": "practice",
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "speaking_practice",
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 4000,
    "llm_calls": 3,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "asr_time_ms": 500,
    "speaking_practice_time_ms": 2200,
    "voice_synthesis_time_ms": 950
  },
  "run_id": "run_202412XX_004",
  "timestamp": "2024-12-XX 16:45:10"
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `quick_response` | "说得很好！" | 快速反馈 |
| `followup_question` | "还想说说其他兴趣吗？" | 引导继续练习 |
| `speaking_practice_count` | 5 | 已练习5次 |
| `asr_time_ms` | 500 | 语音识别耗时 |
| `llm_calls` | 3 | 3次LLM调用（quick_reply + spoken_practice + 知识点识别） |

---

## 场景5：主动关心

### 请求示例

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "child_interests": ["阅读", "运动"],
    "trigger_type": "care",
    "user_input_text": ""
  }'
```

### 响应示例

```json
{
  "quick_response": "今天过得怎么样？",
  "followup_question": "有没有学到新知识？",
  "ai_response": "今天过得怎么样呀？我看你今天在学校待了这么久，有没有学到什么新知识或者遇到什么有趣的事情呢？",
  "ai_response_audio": "https://example.com/audio/care_response_345.mp3",
  "trigger_type": "care",
  "homework_status": "",
  "speaking_practice_count": 0,
  "scenario_type": "general",
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "active_care",
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 1800,
    "llm_calls": 2,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "active_care_time_ms": 1000,
    "voice_synthesis_time_ms": 450
  },
  "run_id": "run_202412XX_005",
  "timestamp": "2024-12-XX 18:00:00"
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `quick_response` | "今天过得怎么样？" | 快速关心 |
| `followup_question` | "有没有学到新知识？" | 引导分享 |
| `trigger_type` | "care" | 触发类型为关心 |
| `scenario_type` | "general" | 场景类型为通用 |

---

## 场景6：作业提醒

### 请求示例

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "trigger_type": "remind",
    "user_input_text": "",
    "homework_list": [
      {
        "id": "hw_001",
        "subject": "数学",
        "task": "练习册第10页",
        "due_date": "2024-12-20"
      },
      {
        "id": "hw_002",
        "subject": "语文",
        "task": "背诵古诗三首",
        "due_date": "2024-12-21"
      }
    ]
  }'
```

### 响应示例

```json
{
  "quick_response": "记得完成作业哦！",
  "followup_question": "想先做哪一科？",
  "ai_response": "记得完成作业哦！你还有数学练习册第10页和语文背诵古诗三首没完成，数学明天就截止了，要不要先做数学？需要我帮你一起规划时间吗？",
  "ai_response_audio": "https://example.com/audio/remind_response_678.mp3",
  "trigger_type": "remind",
  "homework_status": "pending",
  "speaking_practice_count": 0,
  "scenario_type": "homework",
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "homework_check",
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 1500,
    "llm_calls": 2,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "homework_check_time_ms": 700,
    "voice_synthesis_time_ms": 450
  },
  "run_id": "run_202412XX_006",
  "timestamp": "2024-12-XX 20:00:00"
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `quick_response` | "记得完成作业哦！" | 快速提醒 |
| `followup_question` | "想先做哪一科？" | 引导规划 |
| `homework_status` | "pending" | 作业状态为待完成 |
| `scenario_type` | "homework" | 识别为作业场景 |

---

## 旧格式兼容性

### 旧请求方式（仍然可用）

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_001",
    "child_name": "小明",
    "child_age": 10,
    "user_input_text": "你好"
  }'
```

### 响应示例

```json
{
  "quick_response": "你好！想聊什么呢？",
  "followup_question": "今天在学校开心吗？",
  "ai_response": "你好！很高兴见到你。今天在学校过得怎么样？有没有什么开心的事情想和我分享？",
  "ai_response_audio": "https://example.com/audio/compat_response_999.mp3",
  "trigger_type": "conversation",
  "homework_status": "",
  "speaking_practice_count": 0,
  "scenario_type": "general",  // 自动判定为通用场景
  "execution_path": [
    "load_memory",
    "quick_reply",
    "enhanced_route_decision",
    "quick_chat",  // 自动路由到轻量级聊天节点
    "voice_synthesis",
    "save_memory"
  ],
  "performance_metrics": {
    "total_time_ms": 1200,
    "llm_calls": 2,
    "nodes_executed": 6,
    "memory_load_time_ms": 50,
    "quick_reply_time_ms": 300,
    "quick_chat_time_ms": 400,
    "voice_synthesis_time_ms": 450
  },
  "run_id": "run_202412XX_007",
  "timestamp": "2024-12-XX 10:00:00"
}
```

### 兼容性说明

✅ **向后兼容**: 旧的调用方式仍然可用

- 不传 `scenario_type` → 自动判定为 `"general"`
- 不传 `child_interests` → 使用默认值 `[]`
- 不传 `homework_list` → 使用默认值 `[]`
- 响应中所有新字段都有默认值

---

## 错误响应示例

### 1. 缺少必填字段

```json
{
  "error_code": "VALIDATION_ERROR",
  "error_message": "缺少必填字段: child_id, child_name, child_age",
  "stack_trace": "..."
}
```

### 2. 音频文件无法访问

```json
{
  "quick_response": "我好像听不到你的声音，你能再说一次吗？",
  "followup_question": "或者用文字告诉我也可以哦！",
  "ai_response": "我好像听不到你的声音，可能是音频文件有问题。你能再用语音说一次，或者直接用文字告诉我你想说什么吗？",
  "ai_response_audio": null,
  "trigger_type": "conversation",
  "homework_status": "",
  "speaking_practice_count": 0,
  "scenario_type": "general",
  "error_info": {
    "type": "audio_access_error",
    "message": "无法访问音频文件",
    "url": "https://example.com/invalid_audio.mp3"
  },
  "performance_metrics": {
    "total_time_ms": 500,
    "llm_calls": 1,
    "nodes_executed": 3
  },
  "run_id": "run_202412XX_error_001",
  "timestamp": "2024-12-XX 10:00:00"
}
```

### 3. 服务超时

```json
{
  "error_code": "TIMEOUT",
  "error_message": "Execution timeout: exceeded 900 seconds",
  "status": "timeout",
  "run_id": "run_202412XX_timeout_001"
}
```

---

## 总结

### 关键变化

| 变化类型 | 说明 | 影响 |
|---------|------|------|
| 新增字段 | `quick_response`, `followup_question`, `scenario_type`, `execution_path`, `performance_metrics` | 客户端可选择显示快答或完整回复 |
| 优化字段 | `homework_status` 自动更新 | 实时跟踪作业状态 |
| 性能提升 | 响应时间减少 30-65% | 用户体验更佳 |
| 兼容性 | 完全向后兼容 | 旧客户端无需修改 |

### 推荐使用方式

1. **优先显示 `quick_response`** - 提升首字延迟
2. **后台加载 `ai_response`** - 补充完整内容
3. **显示 `followup_question`** - 引导用户继续对话
4. **监控 `performance_metrics`** - 了解系统性能

---

**文档版本**: v2.0
**最后更新**: 2024-12-XX
**维护者**: AI 陪伴团队
