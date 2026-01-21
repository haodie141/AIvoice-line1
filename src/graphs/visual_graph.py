"""
可视化模式的工作流图（步骤级拆分）

这个文件定义了可视化模式下的工作流图结构，
每个步骤都是独立的节点，对应扣子工作流的步骤级可视化。

使用方法：
export COZE_VISUAL_MODE=detailed
然后运行工作流，将使用可视化模式
"""

from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from .memory_store import MemoryStore

from .state import (
    GlobalState,
    GraphInput,
    GraphOutput,
    LongTermMemoryInput, LongTermMemoryOutput,
    HomeworkCheckInput, HomeworkCheckOutput,
    ActiveCareInput, ActiveCareOutput,
    VoiceSynthesisInput, VoiceSynthesisOutput,
    SaveMemoryWrapInput, SaveMemoryWrapOutput
)
from .visual_state import VisualGlobalState

from .node import (
    long_term_memory_node,
    homework_check_node,
    active_care_node,
    voice_synthesis_node
)

from .visual_node import (
    # 口语练习拆分节点
    practice_asr_node,
    practice_review_check_node,
    practice_scenario_select_node,
    practice_dialogue_node,
    practice_knowledge_extract_node,
    practice_update_memory_node,
    practice_tts_node,
    
    # 实时对话拆分节点
    realtime_search_judgment_node,
    realtime_web_search_node,
    realtime_context_builder_node,
    realtime_llm_generate_node,
    realtime_homework_check_node,
    
    # 路由决策
    visual_route_decision
)


# ============== 创建可视化模式的工作流图 ==============
def create_visual_graph():
    """
    创建可视化模式的工作流图（步骤级拆分）
    
    结构：
    输入 → 加载记忆 → 路由决策
        ↓
        ├─ 主动关心 → TTS → 保存记忆 → 输出
        ├─ 作业提醒 → TTS → 保存记忆 → 输出
        ├─ 口语练习（7个步骤）→ TTS → 保存记忆 → 输出
        └─ 实时对话（5个步骤）→ TTS → 保存记忆 → 输出
    """
    
    # ============== 包装函数：拆分节点的输入输出 ==============
    
    # 加载记忆包装
    def wrap_load_memory_visual(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        node_input = LongTermMemoryInput(
            child_id=state.child_id,
            action_type="load"
        )
        node_output: LongTermMemoryOutput = long_term_memory_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            conversation_history=node_output.conversation_history,
            learning_progress=node_output.learning_progress,
            speaking_practice_count=node_output.speaking_practice_count,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    # 作业检查包装
    def wrap_homework_check_visual(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        node_input = HomeworkCheckInput(
            homework_list=state.homework_list,
            current_time=state.current_time,
            child_id=state.child_id
        )
        node_output: HomeworkCheckOutput = homework_check_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            homework_status=node_output.homework_status,
            need_remind=node_output.need_remind,
            ai_response=node_output.remind_message
        )
    
    # 主动关心包装
    def wrap_active_care_visual(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        node_input = ActiveCareInput(
            child_name=state.child_name,
            child_age=state.child_age,
            child_interests=state.child_interests,
            conversation_history=state.conversation_history,
            current_time=state.current_time
        )
        node_output: ActiveCareOutput = active_care_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            ai_response=node_output.care_message
        )
    
    # ============== 口语练习拆分节点包装 ==============
    
    # 1. ASR
    def wrap_practice_asr(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeASRInput
        node_input = PracticeASRInput(
            user_input_audio=state.user_input_audio,
            user_input_text=state.user_input_text,
            child_name=state.child_name
        )
        node_output = practice_asr_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            recognized_text=node_output.recognized_text
        )
    
    # 2. 复习检查
    def wrap_practice_review_check(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeReviewCheckInput
        node_input = PracticeReviewCheckInput(
            child_name=state.child_name,
            recognized_text=state.recognized_text
        )
        node_output = practice_review_check_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            practice_has_review=node_output.has_review,
            practice_review_knowledge=node_output.review_knowledge,
            should_review=node_output.should_review
        )
    
    # 3. 场景选择
    def wrap_practice_scenario_select(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeScenarioSelectInput
        node_input = PracticeScenarioSelectInput(
            child_name=state.child_name,
            child_age=state.child_age,
            child_interests=state.child_interests,
            recognized_text=state.recognized_text,
            skip_scenario=state.practice_has_review and state.should_review
        )
        node_output = practice_scenario_select_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            practice_scenario_key=node_output.scenario_key,
            practice_scenario_name=node_output.scenario_name,
            practice_topic=node_output.topic,
            practice_is_review_mode=node_output.is_review_mode
        )
    
    # 4. 对话引擎
    def wrap_practice_dialogue(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeDialogueInput
        # 获取当前阶段
        current_stage = state.practice_stage or "initiate"
        
        node_input = PracticeDialogueInput(
            child_name=state.child_name,
            child_age=state.child_age,
            child_interests=state.child_interests,
            recognized_text=state.recognized_text,
            conversation_history=state.conversation_history,
            scenario_key=state.practice_scenario_key,
            scenario_name=state.practice_scenario_name,
            topic=state.practice_topic,
            is_review_mode=state.practice_is_review_mode,
            review_knowledge=state.practice_review_knowledge,
            practice_stage=current_stage,
            turn_count=state.practice_turn_count
        )
        node_output = practice_dialogue_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            ai_response=node_output.ai_response,
            practice_stage=node_output.next_stage,
            practice_turn_count=node_output.turn_count
        )
    
    # 5. 知识点识别
    def wrap_practice_knowledge_extract(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeKnowledgeExtractInput
        node_input = PracticeKnowledgeExtractInput(
            child_name=state.child_name,
            child_age=state.child_age,
            recognized_text=state.recognized_text,
            stage=state.practice_stage or "initiate"
        )
        node_output = practice_knowledge_extract_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            practice_new_knowledge=node_output.new_knowledge
        )
    
    # 6. 更新记忆
    def wrap_practice_update_memory(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeUpdateMemoryInput
        node_input = PracticeUpdateMemoryInput(
            child_name=state.child_name,
            new_knowledge=state.practice_new_knowledge,
            stage=state.practice_stage or "initiate",
            practice_count=state.speaking_practice_count,
            turn_count=state.practice_turn_count
        )
        node_output = practice_update_memory_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            speaking_practice_count=node_output.practice_count
        )
    
    # 7. TTS
    def wrap_practice_tts(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import PracticeTTSInput
        node_input = PracticeTTSInput(
            ai_response=state.ai_response,
            child_age=state.child_age
        )
        node_output = practice_tts_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            ai_response_audio=node_output.audio_url
        )
    
    # ============== 实时对话拆分节点包装 ==============
    
    # 1. 搜索判断
    def wrap_realtime_search_judgment(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import RealtimeSearchJudgmentInput
        node_input = RealtimeSearchJudgmentInput(
            user_input_text=state.user_input_text,
            child_age=state.child_age
        )
        node_output = realtime_search_judgment_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            realtime_need_search=node_output.need_search,
            realtime_search_query=node_output.search_query
        )
    
    # 2. 联网搜索
    def wrap_realtime_web_search(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import RealtimeWebSearchInput
        node_input = RealtimeWebSearchInput(
            search_query=state.realtime_search_query
        )
        node_output = realtime_web_search_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            realtime_search_results=node_output.search_results
        )
    
    # 3. 上下文构建
    def wrap_realtime_context_builder(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import RealtimeContextBuilderInput
        
        # 获取有效作业信息
        memory_store = MemoryStore.get_instance()
        valid_homework = memory_store.get_valid_homework(state.child_id)
        
        node_input = RealtimeContextBuilderInput(
            user_input_text=state.user_input_text,
            conversation_history=state.conversation_history,
            search_results=state.realtime_search_results,
            homework_status=state.homework_status,
            child_name=state.child_name,
            child_age=state.child_age
        )
        node_output = realtime_context_builder_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            realtime_context_str=node_output.context_str
        )
    
    # 4. LLM生成
    def wrap_realtime_llm_generate(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import RealtimeLLMGenerateInput
        node_input = RealtimeLLMGenerateInput(
            user_input_text=state.user_input_text,
            context_str=state.realtime_context_str,
            child_name=state.child_name,
            child_age=state.child_age
        )
        node_output = realtime_llm_generate_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            ai_response=node_output.ai_response
        )
    
    # 5. 作业意图识别
    def wrap_realtime_homework_check(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from graphs.visual_state import RealtimeHomeworkCheckInput
        
        # 获取有效作业信息
        memory_store = MemoryStore.get_instance()
        valid_homework = memory_store.get_valid_homework(state.child_id)
        
        node_input = RealtimeHomeworkCheckInput(
            user_input_text=state.user_input_text,
            ai_response=state.ai_response,
            valid_homework=valid_homework,
            child_age=state.child_age,
            child_id=state.child_id
        )
        node_output = realtime_homework_check_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            realtime_homework_completed=node_output.homework_completed
        )
    
    # TTS合成（所有分支共享）
    def wrap_tts_visual(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        node_input = VoiceSynthesisInput(
            text=state.ai_response,
            child_age=state.child_age,
            voice_type="child" if state.child_age <= 12 else "normal"
        )
        node_output = voice_synthesis_node(node_input, config, runtime)
        
        return VisualGlobalState(
            **state.dict(),
            ai_response_audio=node_output.audio_url
        )
    
    # 保存记忆（所有分支共享）
    def wrap_save_memory_visual(state: VisualGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> VisualGlobalState:
        from .memory_store import MemoryStore
        
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
        
        return VisualGlobalState(
            **state.dict()
        )
    
    # 路由决策包装
    def wrap_route_decision_visual(state: VisualGlobalState) -> str:
        from graphs.visual_state import VisualRouteDecisionInput
        node_input = VisualRouteDecisionInput(
            trigger_type=state.trigger_type,
            has_user_input=bool(state.user_input_text or state.user_input_audio),
            current_time=state.current_time
        )
        return visual_route_decision(node_input)
    
    # ============== 创建图 ==============
    builder = StateGraph(VisualGlobalState, input_schema=GraphInput, output_schema=GraphOutput)
    
    # 添加公共节点
    builder.add_node("load_memory", wrap_load_memory_visual)
    
    # 添加主动关心分支
    builder.add_node("active_care", wrap_active_care_visual, metadata={
        "type": "agent",
        "llm_cfg": "config/active_care_llm_cfg.json"
    })
    
    # 添加作业提醒分支
    builder.add_node("homework_check", wrap_homework_check_visual, metadata={
        "type": "agent",
        "llm_cfg": "config/homework_check_llm_cfg.json"
    })
    
    # ============== 添加口语练习分支（7个步骤） ==============
    builder.add_node("practice_asr", wrap_practice_asr, metadata={
        "title": "口语练习-语音识别",
        "desc": "将孩子说的话转换为文本"
    })
    builder.add_node("practice_review_check", wrap_practice_review_check, metadata={
        "title": "口语练习-复习检查",
        "desc": "检查是否有需要复习的知识点（间隔重复算法）"
    })
    builder.add_node("practice_scenario_select", wrap_practice_scenario_select, metadata={
        "title": "口语练习-场景选择",
        "desc": "根据孩子兴趣选择练习场景"
    })
    builder.add_node("practice_dialogue", wrap_practice_dialogue, metadata={
        "title": "口语练习-对话引擎",
        "desc": "四阶段对话：主动发起→苏格拉底式提问→追问延伸→总结反馈"
    })
    builder.add_node("practice_knowledge_extract", wrap_practice_knowledge_extract, metadata={
        "title": "口语练习-知识点识别",
        "desc": "自动识别新知识点（单词/概念）"
    })
    builder.add_node("practice_update_memory", wrap_practice_update_memory, metadata={
        "title": "口语练习-更新记忆",
        "desc": "更新学习进度和记忆（间隔重复算法）"
    })
    builder.add_node("practice_tts", wrap_practice_tts, metadata={
        "title": "口语练习-语音合成",
        "desc": "将AI回复转换为语音"
    })
    
    # ============== 添加实时对话分支（5个步骤） ==============
    builder.add_node("realtime_search_judgment", wrap_realtime_search_judgment, metadata={
        "title": "实时对话-搜索判断",
        "desc": "判断是否需要联网搜索"
    })
    builder.add_node("realtime_web_search", wrap_realtime_web_search, metadata={
        "title": "实时对话-联网搜索",
        "desc": "调用搜索API获取信息"
    })
    builder.add_node("realtime_context_builder", wrap_realtime_context_builder, metadata={
        "title": "实时对话-上下文构建",
        "desc": "构建完整的对话上下文"
    })
    builder.add_node("realtime_llm_generate", wrap_realtime_llm_generate, metadata={
        "title": "实时对话-LLM生成",
        "desc": "生成AI回复"
    })
    builder.add_node("realtime_homework_check", wrap_realtime_homework_check, metadata={
        "title": "实时对话-作业意图识别",
        "desc": "识别是否提到作业完成并更新状态"
    })
    
    # 添加TTS和保存记忆节点（所有分支共享）
    builder.add_node("tts", wrap_tts_visual)
    builder.add_node("save_memory", wrap_save_memory_visual)
    
    # 设置入口点
    builder.set_entry_point("load_memory")
    
    # 添加条件分支
    builder.add_conditional_edges(
        source="load_memory",
        path=wrap_route_decision_visual,
        path_map={
            "主动关心": "active_care",
            "作业提醒": "homework_check",
            "口语练习": "practice_asr",
            "实时对话": "realtime_search_judgment"
        }
    )
    
    # ============== 连接口语练习分支 ==============
    builder.add_edge("practice_asr", "practice_review_check")
    builder.add_edge("practice_review_check", "practice_scenario_select")
    builder.add_edge("practice_scenario_select", "practice_dialogue")
    builder.add_edge("practice_dialogue", "practice_knowledge_extract")
    builder.add_edge("practice_knowledge_extract", "practice_update_memory")
    builder.add_edge("practice_update_memory", "practice_tts")
    
    # ============== 连接实时对话分支 ==============
    builder.add_edge("realtime_search_judgment", "realtime_web_search")
    builder.add_edge("realtime_web_search", "realtime_context_builder")
    builder.add_edge("realtime_context_builder", "realtime_llm_generate")
    builder.add_edge("realtime_llm_generate", "realtime_homework_check")
    builder.add_edge("realtime_homework_check", "tts")
    
    # 连接主动关心和作业提醒
    builder.add_edge("active_care", "tts")
    builder.add_edge("homework_check", "tts")
    
    # TTS后保存记忆
    builder.add_edge("tts", "save_memory")
    
    # 结束
    builder.add_edge("save_memory", END)
    
    return builder.compile()


# 创建可视化模式图
visual_graph = create_visual_graph()
