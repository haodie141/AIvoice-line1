"""
可视化模式的节点函数（步骤级拆分）

这个文件包含所有拆分后的节点函数，每个步骤都是独立的节点，
对应扣子工作流的步骤级可视化。
"""

import os
import json
from datetime import datetime
from typing import Literal, Optional, List
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import ASRClient, LLMClient, SearchClient, TTSClient

from graphs.visual_state import (
    # 口语练习节点
    PracticeASRInput, PracticeASROutput,
    PracticeReviewCheckInput, PracticeReviewCheckOutput,
    PracticeScenarioSelectInput, PracticeScenarioSelectOutput,
    PracticeDialogueInput, PracticeDialogueOutput,
    PracticeKnowledgeExtractInput, PracticeKnowledgeExtractOutput,
    PracticeUpdateMemoryInput, PracticeUpdateMemoryOutput,
    PracticeTTSInput, PracticeTTSOutput,
    
    # 实时对话节点
    RealtimeSearchJudgmentInput, RealtimeSearchJudgmentOutput,
    RealtimeWebSearchInput, RealtimeWebSearchOutput,
    RealtimeContextBuilderInput, RealtimeContextBuilderOutput,
    RealtimeLLMGenerateInput, RealtimeLLMGenerateOutput,
    RealtimeHomeworkCheckInput, RealtimeHomeworkCheckOutput,
    
    # 路由决策
    VisualRouteDecisionInput
)

from .state import PracticeStage, PRACTICE_SCENARIOS
from .memory_store import MemoryStore


# ============== 口语练习拆分节点 ==============

def practice_asr_node(
    state: PracticeASRInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeASROutput:
    """
    title: 口语练习-语音识别
    desc: 将孩子说的话转换为文本
    integrations: 语音大模型
    """
    ctx = runtime.context
    
    recognized_text = state.user_input_text
    has_audio = False
    
    # 如果有音频但没有文本，进行语音识别
    if state.user_input_audio and not recognized_text:
        has_audio = True
        asr_client = ASRClient(ctx=ctx)
        try:
            text, data = asr_client.recognize(
                uid=f"{state.child_name}_practice",
                url=state.user_input_audio.url
            )
            recognized_text = text
        except Exception as e:
            print(f"语音识别失败: {e}")
            recognized_text = state.user_input_text
    
    return PracticeASROutput(
        recognized_text=recognized_text or "",
        has_audio=has_audio
    )


def practice_review_check_node(
    state: PracticeReviewCheckInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeReviewCheckOutput:
    """
    title: 口语练习-复习检查
    desc: 检查是否有需要复习的知识点（间隔重复算法）
    integrations: 
    """
    ctx = runtime.context
    
    memory_store = MemoryStore.get_instance()
    
    try:
        # 获取到期的复习知识点
        due_for_review = memory_store.get_due_for_review(state.child_name, limit=1)
        
        if due_for_review:
            review_kp = due_for_review[0]
            return PracticeReviewCheckOutput(
                has_review=True,
                review_knowledge=review_kp,
                should_review=True
            )
        else:
            return PracticeReviewCheckOutput(
                has_review=False,
                review_knowledge=None,
                should_review=False
            )
    except Exception as e:
        print(f"复习检查失败: {e}")
        return PracticeReviewCheckOutput(
            has_review=False,
            review_knowledge=None,
            should_review=False
        )


def practice_scenario_select_node(
    state: PracticeScenarioSelectInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeScenarioSelectOutput:
    """
    title: 口语练习-场景选择
    desc: 根据孩子兴趣选择练习场景
    integrations: 
    """
    ctx = runtime.context
    
    # 如果有复习任务，跳过场景选择
    if state.skip_scenario:
        return PracticeScenarioSelectOutput(
            scenario_key="review",
            scenario_name="复习模式",
            topic="知识点复习",
            is_review_mode=True
        )
    
    # 根据孩子兴趣选择场景
    scenario_key = "daily_life"
    if state.child_interests:
        if "画画" in state.child_interests or "绘画" in state.child_interests:
            scenario_key = "interests"
        elif any(emotion in str(state.child_interests) for emotion in ["开心", "难过", "生气"]):
            scenario_key = "emotions"
    
    scenario_info = PRACTICE_SCENARIOS[scenario_key]
    topics = scenario_info["topics"]
    
    # 随机选择一个话题
    import random
    topic = random.choice(topics)
    
    return PracticeScenarioSelectOutput(
        scenario_key=scenario_key,
        scenario_name=scenario_info["name"],
        topic=topic,
        is_review_mode=False
    )


def practice_dialogue_node(
    state: PracticeDialogueInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeDialogueOutput:
    """
    title: 口语练习-对话引擎
    desc: 四阶段对话引擎：主动发起→苏格拉底式提问→追问延伸→总结反馈
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    client = LLMClient(ctx=ctx)
    
    # 获取当前阶段
    current_stage = state.practice_stage or "initiate"
    turn_count = state.turn_count
    
    ai_response = ""
    corrected_text = state.recognized_text
    next_stage = "initiate"
    
    # ============== 阶段1：主动发起话题（复习模式或新模式） ==============
    if current_stage == "initiate" and not state.recognized_text.strip():
        if state.is_review_mode and state.review_knowledge:
            # 复习模式
            review_kp = state.review_knowledge
            kp_type = "单词" if review_kp.get("type") == "word" else "概念"
            kp_content = review_kp.get("content", "")
            kp_context = review_kp.get("context", "")
            
            review_prompt = f"""你是{state.child_name}的口语练习伙伴，现在要帮助孩子复习之前学过的知识。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁

要复习的{kp_type}：{kp_content}
学习时的上下文：{kp_context}

请用友好、自然的方式引导孩子回忆这个知识点：

1. 温和提醒：不要直接问"你还记得XXX吗"，要自然地提及
2. 情境带入：结合学习时的上下文或相关场景
3. 鼓励回忆：给孩子思考和回忆的空间
4. 不要直接给答案：引导孩子自己说出来

要求：
- 语气要自然、亲切，像朋友聊天一样
- 不要包含任何动作描述
- 不要使用表情符号
- 只输出引导性的话语"""
            
            messages = [HumanMessage(content=review_prompt)]
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-8-251228",
                temperature=0.8
            )
            
            ai_response = str(response.content).strip()
            next_stage = "question"
        else:
            # 新话题模式
            scenario_info = PRACTICE_SCENARIOS.get(state.scenario_key, PRACTICE_SCENARIOS["daily_life"])
            topics = scenario_info["topics"]
            topic = state.topic or (topics[0] if topics else "日常生活")
            
            initiate_prompt = f"""你是{state.child_name}的口语练习伙伴，现在要主动发起对话。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
孩子兴趣：{', '.join(state.child_interests) if state.child_interests else '未知'}

当前场景：{scenario_info['name']}
选定的主题：{topic}

请用友好、热情的语气主动发起对话，提出一个开放性问题。

要求：
1. 问题要简单易懂，适合{state.child_age}岁孩子
2. 问题要是开放式的，让孩子可以自由发挥
3. 语气要亲切，像朋友一样
4. 不要包含任何动作描述
5. 不要使用表情符号
6. 只输出一个问题"""
            
            messages = [HumanMessage(content=initiate_prompt)]
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-8-251228",
                temperature=0.85
            )
            
            ai_response = str(response.content).strip()
            next_stage = "question"
    
    # ============== 阶段2：苏格拉底式提问 ==============
    elif current_stage == "question":
        question_prompt = f"""你是{state.child_name}的口语练习伙伴，现在要用苏格拉底式提问引导孩子。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
孩子说：{state.recognized_text}

请分析孩子的回答，并给出反馈：

1. 肯定孩子的表达
2. 轻柔地纠正语法或用词错误（如有），不要直接批评
3. 通过追问引导孩子表达更多
4. 鼓励孩子思考

要求：
- 语气要温柔、鼓励性
- 不要包含任何动作描述
- 不要使用表情符号
- 控制在2-3句话以内"""
        
        messages = [HumanMessage(content=question_prompt)]
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-8-251228",
            temperature=0.7
        )
        
        ai_response = str(response.content).strip()
        next_stage = "followup"
    
    # ============== 阶段3：追问延伸 ==============
    elif current_stage == "followup":
        if turn_count >= 3:
            # 进入总结阶段
            next_stage = "summarize"
            summarize_prompt = f"""你是{state.child_name}的口语练习伙伴，要给孩子一个总结反馈。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
对话轮数：{turn_count}

请给孩子一个温暖的总结：

1. 表扬孩子的表现
2. 给出1-2个具体的改进建议（如果有）
3. 鼓励孩子下次再来练习

要求：
- 语气要温暖、真诚
- 不要包含任何动作描述
- 不要使用表情符号
- 控制在2-3句话以内"""
            
            messages = [HumanMessage(content=summarize_prompt)]
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-8-251228",
                temperature=0.7
            )
            
            ai_response = str(response.content).strip()
        else:
            # 继续追问
            followup_prompt = f"""你是{state.child_name}的口语练习伙伴，现在要继续追问。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
孩子的回答：{state.recognized_text}
对话轮数：{turn_count}

请继续深入话题，引导孩子表达更多：

1. 提出一个相关的问题
2. 引导孩子举例说明
3. 鼓励孩子分享更多细节
4. 避免是/否问题

要求：
- 问题要开放性
- 语气要亲切
- 不要包含任何动作描述
- 不要使用表情符号
- 只输出一个问题"""
            
            messages = [HumanMessage(content=followup_prompt)]
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-8-251228",
                temperature=0.75
            )
            
            ai_response = str(response.content).strip()
            next_stage = "followup"
    
    # ============== 阶段4：总结反馈 ==============
    elif current_stage == "summarize":
        next_stage = "summarize"
        ai_response = "今天的口语练习就到这里，你表现得很棒！下次我们继续加油！"
    
    return PracticeDialogueOutput(
        ai_response=ai_response,
        corrected_text=corrected_text,
        next_stage=next_stage,
        turn_count=turn_count + 1
    )


def practice_knowledge_extract_node(
    state: PracticeKnowledgeExtractInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeKnowledgeExtractOutput:
    """
    title: 口语练习-知识点识别
    desc: 自动识别新知识点（单词/概念）
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 只在提问和追问阶段识别知识点
    if state.stage not in ["question", "followup"]:
        return PracticeKnowledgeExtractOutput(
            new_knowledge=[],
            has_new_knowledge=False
        )
    
    memory_store = MemoryStore.get_instance()
    client = LLMClient(ctx=ctx)
    
    try:
        identify_prompt = f"""你是一个知识提取助手。请从以下孩子的回答中识别出新知识点（单词或概念）。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
孩子说：{state.recognized_text}

请识别以下内容：
1. 新单词：孩子可能刚学会或不熟悉的单词
2. 新概念：孩子可能刚理解的概念

要求：
- 只返回JSON格式
- 只识别真正的新内容，不要提取常见词
- 每个知识点包含type（word/concept）、content（内容）

返回格式：
{{"knowledge_points": [{{"type": "word", "content": "单词内容"}}]}}"""
        
        identify_messages = [HumanMessage(content=identify_prompt)]
        identify_response = client.invoke(
            messages=identify_messages,
            model="doubao-seed-1-8-251228",
            temperature=0.3
        )
        
        identify_text = str(identify_response.content).strip()
        if "{" in identify_text and "}" in identify_text:
            json_start = identify_text.find("{")
            json_end = identify_text.rfind("}") + 1
            json_str = identify_text[json_start:json_end]
            identify_result = json.loads(json_str)
            
            new_knowledge = identify_result.get("knowledge_points", [])
            
            # 记录识别到的知识点
            for kp in new_knowledge:
                memory_store.add_knowledge_point(
                    child_id=state.child_name,
                    point_type=kp.get("type", "word"),
                    content=kp.get("content", ""),
                    context=f"在口语练习中学习：{state.recognized_text[:50]}"
                )
            
            return PracticeKnowledgeExtractOutput(
                new_knowledge=new_knowledge,
                has_new_knowledge=len(new_knowledge) > 0
            )
        
    except Exception as e:
        print(f"知识点识别失败: {e}")
    
    return PracticeKnowledgeExtractOutput(
        new_knowledge=[],
        has_new_knowledge=False
    )


def practice_update_memory_node(
    state: PracticeUpdateMemoryInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeUpdateMemoryOutput:
    """
    title: 口语练习-更新记忆
    desc: 更新学习进度和记忆（间隔重复算法）
    integrations: 
    """
    ctx = runtime.context
    
    memory_store = MemoryStore.get_instance()
    
    # 更新练习次数
    new_practice_count = state.practice_count + 1
    
    memory_store.update_learning_progress(state.child_name, {
        "speaking_practice_count": new_practice_count,
        "last_practice_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "practice_stage": state.stage,
        "practice_turn_count": state.turn_count
    })
    
    # 如果有新知识点，记录到学习进度
    if state.new_knowledge:
        memory_store.update_learning_progress(state.child_name, {
            "last_new_knowledge": state.new_knowledge,
            "last_knowledge_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return PracticeUpdateMemoryOutput(
        practice_count=new_practice_count,
        memory_updated=True
    )


def practice_tts_node(
    state: PracticeTTSInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PracticeTTSOutput:
    """
    title: 口语练习-语音合成
    desc: 将AI回复转换为语音
    integrations: 语音大模型
    """
    ctx = runtime.context
    
    tts_client = TTSClient(ctx=ctx)
    
    try:
        # 根据年龄选择语音类型
        voice_type = "child" if state.child_age <= 12 else "normal"
        
        # 合成语音
        audio_url = tts_client.synthesize(
            text=state.ai_response,
            voice_type=voice_type,
            uid=f"{state.child_name}_practice"
        )
        
        return PracticeTTSOutput(audio_url=audio_url)
    
    except Exception as e:
        print(f"语音合成失败: {e}")
        # 返回空URL，上游会处理
        return PracticeTTSOutput(audio_url="")


# ============== 实时对话拆分节点 ==============

def realtime_search_judgment_node(
    state: RealtimeSearchJudgmentInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeSearchJudgmentOutput:
    """
    title: 实时对话-搜索判断
    desc: 判断是否需要联网搜索
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    client = LLMClient(ctx=ctx)
    
    judgment_prompt = f"""你是一个检索需求判断助手。判断以下孩子的问题是否需要联网搜索。

孩子的年龄：{state.child_age}岁
孩子的问题：{state.user_input_text}

需要联网搜索的场景：
- 询问实时信息（如天气、新闻、时事热点）
- 询问最新数据（如最近的比赛结果、新出的产品）
- 询问具体事实（如某个历史事件、科学知识）
- 询问时事话题（如近期的社会事件）

不需要联网搜索的场景：
- 日常聊天（如"你好"、"我喜欢你"）
- 作业相关（如"帮我检查作业"）
- 情感表达（如"我很开心"、"我很难过"）
- 学习辅导（如"这道题怎么做"）

请只返回JSON格式：
{{"need_search": true/false, "search_query": "搜索关键词或空字符串"}}"""
    
    try:
        judgment_messages = [HumanMessage(content=judgment_prompt)]
        judgment_response = client.invoke(
            messages=judgment_messages,
            model="doubao-seed-1-8-251228",
            temperature=0.1
        )
        
        judgment_text = str(judgment_response.content).strip()
        if "{" in judgment_text and "}" in judgment_text:
            json_start = judgment_text.find("{")
            json_end = judgment_text.rfind("}") + 1
            json_str = judgment_text[json_start:json_end]
            judgment_result = json.loads(json_str)
            
            return RealtimeSearchJudgmentOutput(
                need_search=judgment_result.get("need_search", False),
                search_query=judgment_result.get("search_query", "")
            )
    except Exception as e:
        print(f"搜索判断失败: {e}")
    
    return RealtimeSearchJudgmentOutput(
        need_search=False,
        search_query=""
    )


def realtime_web_search_node(
    state: RealtimeWebSearchInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeWebSearchOutput:
    """
    title: 实时对话-联网搜索
    desc: 调用搜索API获取信息
    integrations: 联网搜索
    """
    ctx = runtime.context
    
    if not state.search_query:
        return RealtimeWebSearchOutput(
            search_results="",
            search_success=False
        )
    
    try:
        search_client = SearchClient(ctx=ctx)
        results = search_client.search(query=state.search_query, mode="web")
        
        # 提取摘要
        summary = results.get("summary", "")
        if isinstance(results, list) and results:
            summary = "\n".join([r.get("content", "") for r in results[:3]])
        
        return RealtimeWebSearchOutput(
            search_results=summary,
            search_success=bool(summary)
        )
    except Exception as e:
        print(f"联网搜索失败: {e}")
        return RealtimeWebSearchOutput(
            search_results="",
            search_success=False
        )


def realtime_context_builder_node(
    state: RealtimeContextBuilderInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeContextBuilderOutput:
    """
    title: 实时对话-上下文构建
    desc: 构建完整的对话上下文
    integrations: 
    """
    ctx = runtime.context
    
    context_parts = []
    
    # 添加作业状态
    if state.homework_status:
        context_parts.append(f"作业状态：{state.homework_status}")
    
    # 添加搜索结果
    if state.search_results:
        context_parts.append(f"相关信息：{state.search_results}")
    
    # 添加对话历史（最近3轮）
    if state.conversation_history:
        recent_history = state.conversation_history[-3:] if len(state.conversation_history) > 3 else state.conversation_history
        history_text = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in recent_history])
        context_parts.append(f"对话历史：\n{history_text}")
    
    context_str = "\n\n".join(context_parts) if context_parts else "无特殊上下文"
    
    return RealtimeContextBuilderOutput(
        context_str=context_str,
        has_context=bool(context_parts)
    )


def realtime_llm_generate_node(
    state: RealtimeLLMGenerateInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeLLMGenerateOutput:
    """
    title: 实时对话-LLM生成
    desc: 生成AI回复
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), "config/realtime_conversation_llm_cfg.json")
    with open(cfg_file, 'r') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    client = LLMClient(ctx=ctx)
    
    # 构建消息
    messages = [
        {"role": "system", "content": sp},
        {"role": "user", "content": f"{up}\n\n{state.context_str}\n\n孩子说：{state.user_input_text}"}
    ]
    
    try:
        response = client.invoke(
            messages=messages,
            model=llm_config.get("model", "doubao-seed-1-8-251228"),
            temperature=llm_config.get("temperature", 0.7)
        )
        
        ai_response = str(response.content).strip()
        return RealtimeLLMGenerateOutput(ai_response=ai_response)
    except Exception as e:
        print(f"LLM生成失败: {e}")
        return RealtimeLLMGenerateOutput(ai_response="抱歉，我刚才没听清，能再说一遍吗？")


def realtime_homework_check_node(
    state: RealtimeHomeworkCheckInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeHomeworkCheckOutput:
    """
    title: 实时对话-作业意图识别
    desc: 识别是否提到作业完成并更新状态
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    if not state.valid_homework:
        return RealtimeHomeworkCheckOutput(
            homework_completed=False,
            subject="",
            confirmed=False,
            homework_updated=False
        )
    
    memory_store = MemoryStore.get_instance()
    subjects_str = "、".join([hw.get("subject", "") for hw in state.valid_homework])
    
    judgment_prompt = f"""你是一个作业状态识别助手。请分析以下对话，判断孩子是否确认完成了某个作业。

孩子的年龄：{state.child_age}岁
孩子说：{state.user_input_text}
AI回复：{state.ai_response}

未完成的作业列表：{subjects_str}

请只返回JSON格式：
{{"homework_completed": true/false, "subject": "学科名称或空字符串", "confirmed": true/false}}

规则：
- homework_completed: 孩子明确说"做完了"、"完成了"等，设为true
- subject: 提取学科名称（如"数学"、"语文"、"英语"）
- confirmed: 孩子确认完成（如"是的"、"真的做完了"等），设为true"""
    
    try:
        client = LLMClient(ctx=ctx)
        messages = [HumanMessage(content=judgment_prompt)]
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-8-251228",
            temperature=0.3
        )
        
        judgment_text = str(response.content).strip()
        if "{" in judgment_text and "}" in judgment_text:
            json_start = judgment_text.find("{")
            json_end = judgment_text.rfind("}") + 1
            json_str = judgment_text[json_start:json_end]
            homework_completed_info = json.loads(json_str)
            
            # 如果确认作业完成，更新作业状态
            if homework_completed_info.get("homework_completed", False) and homework_completed_info.get("confirmed", False):
                subject = homework_completed_info.get("subject", "")
                if subject:
                    for hw in state.valid_homework:
                        if subject in hw.get("subject", ""):
                            memory_store.complete_homework(state.child_id, hw["id"])
                            return RealtimeHomeworkCheckOutput(
                                homework_completed=True,
                                subject=subject,
                                confirmed=True,
                                homework_updated=True
                            )
        
    except Exception as e:
        print(f"作业意图识别失败: {e}")
    
    return RealtimeHomeworkCheckOutput(
        homework_completed=False,
        subject="",
        confirmed=False,
        homework_updated=False
    )


# ============== 路由决策函数 ==============
def visual_route_decision(state: VisualRouteDecisionInput) -> str:
    """
    title: 可视化模式-路由决策
    desc: 根据触发类型路由到不同的处理流程
    """
    if state.trigger_type == "care":
        return "主动关心"
    elif state.trigger_type == "remind":
        return "作业提醒"
    elif state.trigger_type == "practice":
        return "口语练习"
    else:
        return "实时对话"
