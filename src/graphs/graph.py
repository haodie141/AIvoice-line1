from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
    LoadMemoryWrapInput, LoadMemoryWrapOutput,
    HomeworkCheckWrapInput, HomeworkCheckWrapOutput,
    ActiveCareWrapInput, ActiveCareWrapOutput,
    SpeakingPracticeWrapInput, SpeakingPracticeWrapOutput,
    RealtimeConversationWrapInput, RealtimeConversationWrapOutput,
    VoiceSynthesisWrapInput, VoiceSynthesisWrapOutput,
    SaveMemoryWrapInput, SaveMemoryWrapOutput,
    LongTermMemoryInput, LongTermMemoryOutput,
    HomeworkCheckInput, HomeworkCheckOutput,
    ActiveCareInput, ActiveCareOutput,
    SpeakingPracticeInput, SpeakingPracticeOutput,
    RealtimeConversationInput, RealtimeConversationOutput,
    VoiceSynthesisInput, VoiceSynthesisOutput,
    RouteDecisionInput,
    RealtimeCallInput, RealtimeCallOutput
)
from graphs.node import (
    long_term_memory_node,
    homework_check_node,
    active_care_node,
    speaking_practice_node,
    realtime_conversation_node,
    voice_synthesis_node,
    route_decision,
    realtime_call_fast_node
)


# ============== 包装函数：使用独立的Input/Output类型 ==============
def wrap_load_memory(
    state: LoadMemoryWrapInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> LoadMemoryWrapOutput:
    """加载长期记忆（支持自动语音识别）"""
    ctx = runtime.context
    
    node_input = LongTermMemoryInput(
        child_id=state.child_id,
        action_type="load"
    )
    node_output: LongTermMemoryOutput = long_term_memory_node(node_input, config, runtime)
    
    # 如果有音频输入但没有文本，自动进行语音识别
    recognized_text = state.user_input_text
    if state.user_input_audio and not state.user_input_text:
        try:
            from coze_coding_dev_sdk import ASRClient
            asr_client = ASRClient(ctx=ctx)
            text, _ = asr_client.recognize(
                uid=f"{state.child_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                url=state.user_input_audio.url
            )
            recognized_text = text
            print(f"🎤 语音识别成功：{recognized_text}")
        except Exception as e:
            print(f"⚠️ 语音识别失败：{e}")
            recognized_text = state.user_input_text
    
    return LoadMemoryWrapOutput(
        child_id=state.child_id,
        child_name=state.child_name,
        child_age=state.child_age,
        child_interests=state.child_interests,
        trigger_type=state.trigger_type,
        user_input_text=recognized_text,  # 使用识别后的文本
        user_input_audio=state.user_input_audio,
        homework_list=state.homework_list,
        conversation_history=node_output.conversation_history,
        learning_progress=node_output.learning_progress,
        speaking_practice_count=node_output.speaking_practice_count,
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def wrap_homework_check(
    state: HomeworkCheckWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> HomeworkCheckWrapOutput:
    """作业检查"""
    node_input = HomeworkCheckInput(
        homework_list=state.homework_list,
        current_time=state.current_time,
        child_id=state.child_id
    )
    node_output: HomeworkCheckOutput = homework_check_node(node_input, config, runtime)
    
    return HomeworkCheckWrapOutput(
        homework_status=node_output.homework_status,
        need_remind=node_output.need_remind,
        ai_response=node_output.remind_message
    )


def wrap_active_care(
    state: ActiveCareWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> ActiveCareWrapOutput:
    """主动关心"""
    node_input = ActiveCareInput(
        child_name=state.child_name,
        child_age=state.child_age,
        child_interests=state.child_interests,
        conversation_history=state.conversation_history,
        current_time=state.current_time
    )
    node_output: ActiveCareOutput = active_care_node(node_input, config, runtime)
    
    return ActiveCareWrapOutput(ai_response=node_output.care_message)


def wrap_speaking_practice(
    state: SpeakingPracticeWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> SpeakingPracticeWrapOutput:
    """口语练习"""
    node_input = SpeakingPracticeInput(
        user_input_audio=state.user_input_audio,
        user_input_text=state.user_input_text,
        child_name=state.child_name,
        child_age=state.child_age,
        conversation_history=state.conversation_history,
        practice_topic=""
    )
    node_output: SpeakingPracticeOutput = speaking_practice_node(node_input, config, runtime)
    
    return SpeakingPracticeWrapOutput(
        recognized_text=node_output.recognized_text,
        ai_response=node_output.feedback,
        speaking_practice_count=node_output.practice_count
    )


def wrap_realtime_conversation(
    state: RealtimeConversationWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> RealtimeConversationWrapOutput:
    """实时对话（支持作业状态自动更新）"""
    import json
    from graphs.memory_store import MemoryStore
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # 如果有音频但没有文本，先识别
    user_text = state.user_input_text
    from graphs.node import realtime_conversation_node
    from coze_coding_dev_sdk import ASRClient, LLMClient
    
    # 获取有效作业信息，用于AI判断作业完成情况
    memory_store = MemoryStore.get_instance()
    valid_homework = memory_store.get_valid_homework(state.child_id)
    homework_info = ""
    if valid_homework:
        subjects = [hw.get("subject", "") for hw in valid_homework]
        homework_info = f"未完成作业：{', '.join(subjects)}"
    else:
        homework_info = "所有作业已完成"
    
    node_input = RealtimeConversationInput(
        user_input_text=user_text,
        child_name=state.child_name,
        child_age=state.child_age,
        conversation_history=state.conversation_history,
        context_info=f"作业状态：{state.homework_status}，{homework_info}"
    )
    node_output: RealtimeConversationOutput = realtime_conversation_node(node_input, config, runtime)
    
    ai_response_text = node_output.ai_response
    
    # 使用第二个LLM调用来判断是否提到了作业完成
    # 这样更可靠，不依赖主对话LLM的格式输出
    if valid_homework:
        subjects_str = "、".join([hw.get("subject", "") for hw in valid_homework])
        
        # 使用LLM判断对话中是否提到作业完成
        judgment_prompt = f"""你是一个作业状态识别助手。请分析以下对话，判断孩子是否确认完成了某个作业。

孩子的年龄：{state.child_age}岁
孩子说：{user_text}
AI回复：{ai_response_text}

未完成的作业列表：{subjects_str}

请判断：
1. 孩子是否明确表示完成了某个作业？
2. 如果完成了，是哪个学科的作业？

只返回JSON格式，不要其他文字：
{{"homework_completed": true/false, "subject": "学科名称或空字符串", "confirmed": true/false}}

规则：
- homework_completed: 如果孩子明确说"做完了"、"完成了"等，设为true，否则false
- subject: 提取学科名称（如"数学"、"语文"、"英语"），如果不确定则为空字符串
- confirmed: 如果孩子确认完成（如"是的"、"真的做完了"等），设为true，否则false"""
        
        try:
            client = LLMClient(ctx=runtime.context)
            messages = [HumanMessage(content=judgment_prompt)]
            response = client.invoke(messages=messages, model="doubao-seed-1-8-251228", temperature=0.3)
            
            # 解析LLM的判断结果
            judgment_text = str(response.content).strip()
            # 提取JSON部分
            if "{" in judgment_text and "}" in judgment_text:
                json_start = judgment_text.find("{")
                json_end = judgment_text.rfind("}") + 1
                json_str = judgment_text[json_start:json_end]
                
                homework_completed_info = json.loads(json_str)
                
                # 如果确认作业完成，更新作业状态
                if homework_completed_info.get("homework_completed", False) and homework_completed_info.get("confirmed", False):
                    subject = homework_completed_info.get("subject", "")
                    if subject:
                        # 查找匹配的作业并标记为完成
                        for hw in valid_homework:
                            if subject in hw.get("subject", ""):
                                memory_store.complete_homework(state.child_id, hw["id"])
                                print(f"✅ 自动更新作业状态：{subject} 作业标记为已完成")
                                break
        except Exception as e:
            print(f"⚠️  作业完成判断失败: {e}")
    
    return RealtimeConversationWrapOutput(ai_response=ai_response_text)


def wrap_voice_synthesis(
    state: VoiceSynthesisWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> VoiceSynthesisWrapOutput:
    """语音合成"""
    node_input = VoiceSynthesisInput(
        text=state.ai_response,
        child_age=state.child_age,
        voice_type="child" if state.child_age <= 12 else "normal"
    )
    node_output: VoiceSynthesisOutput = voice_synthesis_node(node_input, config, runtime)
    
    return VoiceSynthesisWrapOutput(ai_response_audio=node_output.audio_url)


def wrap_save_memory(
    state: SaveMemoryWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> SaveMemoryWrapOutput:
    """保存长期记忆"""
    from graphs.memory_store import MemoryStore
    
    memory_store = MemoryStore.get_instance()
    
    # 构建对话记录
    conversation_record = {
        "role": "user",
        "content": state.user_input_text or state.recognized_text,
        "type": state.trigger_type
    }
    memory_store.add_conversation(state.child_id, conversation_record)
    
    # 添加AI回复
    if state.ai_response:
        ai_record = {
            "role": "assistant",
            "content": state.ai_response,
            "type": state.trigger_type
        }
        memory_store.add_conversation(state.child_id, ai_record)
    
    # 更新学习进度
    if state.trigger_type == "practice":
        memory_store.update_learning_progress(state.child_id, {
            "speaking_practice_count": state.speaking_practice_count,
            "last_practice_time": state.current_time
        })
    
    return SaveMemoryWrapOutput(saved=True)


# ============== 实时通话快速包装函数 ==============
def wrap_realtime_call(
    state: LoadMemoryWrapInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> GraphOutput:
    """
    实时通话快速路径
    直接整合ASR+LLM+TTS，最小化延迟
    """
    # 构建输入 - 使用RealtimeCallInput
    node_input = RealtimeCallInput(
        user_input_text=state.user_input_text,
        user_input_audio=state.user_input_audio,  # 直接传递音频
        child_name=state.child_name,
        child_age=state.child_age,
        child_id=state.child_id
    )

    # 调用快速节点
    result: RealtimeCallOutput = realtime_call_fast_node(node_input, config, runtime)

    # 异步保存记忆（不阻塞主流程）
    try:
        from graphs.memory_store import MemoryStore
        memory_store = MemoryStore.get_instance()

        # 保存对话记录
        if result.recognized_text:
            memory_store.add_conversation(state.child_id, {
                "role": "user",
                "content": result.recognized_text,
                "type": "realtime_call",
                "timestamp": datetime.now().isoformat()
            })

        if result.ai_response:
            memory_store.add_conversation(state.child_id, {
                "role": "assistant",
                "content": result.ai_response,
                "type": "realtime_call",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        print(f"⚠️ 异步保存记忆失败（不影响主流程）：{e}")

    return GraphOutput(
        ai_response=result.ai_response,
        ai_response_audio=result.ai_response_audio,
        trigger_type="realtime_call",
        homework_status="",
        speaking_practice_count=0
    )





# ============== 创建主图 ==============
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点（使用包装函数）
builder.add_node("load_memory", wrap_load_memory)
builder.add_node("homework_check", wrap_homework_check)
builder.add_node("active_care", wrap_active_care, metadata={
    "type": "agent",
    "llm_cfg": "config/active_care_llm_cfg.json"
})
builder.add_node("speaking_practice", wrap_speaking_practice)
builder.add_node("realtime_conversation", wrap_realtime_conversation, metadata={
    "type": "agent",
    "llm_cfg": "config/realtime_conversation_llm_cfg.json"
})
builder.add_node("realtime_call", wrap_realtime_call)  # 实时通话快速节点
builder.add_node("voice_synthesis", wrap_voice_synthesis)
builder.add_node("save_memory", wrap_save_memory)

# 设置入口点
builder.set_entry_point("load_memory")

# 添加条件分支
builder.add_conditional_edges(
    source="load_memory",
    path=route_decision,
    path_map={
        "主动关心": "active_care",
        "作业提醒": "homework_check",
        "口语练习": "speaking_practice",
        "实时对话": "realtime_conversation",
        "实时通话": "realtime_call"
    }
)

# 添加后续边 - 所有处理分支都汇聚到语音合成
builder.add_edge("active_care", "voice_synthesis")
builder.add_edge("homework_check", "voice_synthesis")
builder.add_edge("speaking_practice", "voice_synthesis")
builder.add_edge("realtime_conversation", "voice_synthesis")

# 语音合成后保存记忆
builder.add_edge("voice_synthesis", "save_memory")

# 结束
builder.add_edge("save_memory", END)

# 编译图
main_graph = builder.compile()
