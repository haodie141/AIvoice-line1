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
    RouteDecisionInput
)
from graphs.node import (
    long_term_memory_node,
    homework_check_node,
    active_care_node,
    speaking_practice_node,
    realtime_conversation_node,
    voice_synthesis_node,
    route_decision
)


# ============== 包装函数：使用独立的Input/Output类型 ==============
def wrap_load_memory(
    state: LoadMemoryWrapInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> LoadMemoryWrapOutput:
    """加载长期记忆"""
    node_input = LongTermMemoryInput(
        child_id=state.child_id,
        action_type="load"
    )
    node_output: LongTermMemoryOutput = long_term_memory_node(node_input, config, runtime)
    
    return LoadMemoryWrapOutput(
        child_id=state.child_id,
        child_name=state.child_name,
        child_age=state.child_age,
        child_interests=state.child_interests,
        trigger_type=state.trigger_type,
        user_input_text=state.user_input_text,
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
    """实时对话"""
    # 如果有音频但没有文本，先识别
    user_text = state.user_input_text
    from graphs.node import realtime_conversation_node
    from coze_coding_dev_sdk import ASRClient
    
    node_input = RealtimeConversationInput(
        user_input_text=user_text,
        child_name=state.child_name,
        child_age=state.child_age,
        conversation_history=state.conversation_history,
        context_info=f"作业状态：{state.homework_status}"
    )
    node_output: RealtimeConversationOutput = realtime_conversation_node(node_input, config, runtime)
    
    return RealtimeConversationWrapOutput(ai_response=node_output.ai_response)


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


# ============== 条件判断包装函数 ==============
def wrap_route_decision(state: LoadMemoryWrapOutput) -> str:
    """路由决策"""
    node_input = RouteDecisionInput(
        trigger_type=state.trigger_type,
        need_remind=False  # 这个参数在load阶段还不确定
    )
    return route_decision(node_input)


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
builder.add_node("voice_synthesis", wrap_voice_synthesis)
builder.add_node("save_memory", wrap_save_memory)

# 设置入口点
builder.set_entry_point("load_memory")

# 添加条件分支
builder.add_conditional_edges(
    source="load_memory",
    path=wrap_route_decision,
    path_map={
        "主动关心": "active_care",
        "作业提醒": "homework_check",
        "口语练习": "speaking_practice",
        "实时对话": "realtime_conversation"
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
