import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient, ASRClient, TTSClient
import requests

from graphs.state import (
    LongTermMemoryInput, LongTermMemoryOutput,
    HomeworkCheckInput, HomeworkCheckOutput,
    ActiveCareInput, ActiveCareOutput,
    SpeakingPracticeInput, SpeakingPracticeOutput,
    RealtimeConversationInput, RealtimeConversationOutput,
    VoiceSynthesisInput, VoiceSynthesisOutput,
    RouteDecisionInput,
    RealtimeCallInput, RealtimeCallOutput
)


# ============== 节点1：长期记忆节点（内存方式） ==============
def long_term_memory_node(
    state: LongTermMemoryInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> LongTermMemoryOutput:
    """
    title: 长期记忆管理
    desc: 使用内存方式管理孩子的对话历史和学习进度记录
    """
    ctx = runtime.context
    
    # 使用内存存储管理孩子的对话历史和学习进度
    from graphs.memory_store import MemoryStore
    
    memory_store = MemoryStore.get_instance()
    
    if state.action_type == "load":
        # 加载数据
        conversation_history = memory_store.get_conversation_history(state.child_id)
        learning_progress = memory_store.get_learning_progress(state.child_id)
        speaking_practice_count = memory_store.get_speaking_practice_count(state.child_id)
        
        return LongTermMemoryOutput(
            conversation_history=conversation_history,
            learning_progress=learning_progress,
            speaking_practice_count=speaking_practice_count,
            load_success=True,
            save_success=False
        )
    
    elif state.action_type == "save":
        # 保存数据
        if state.conversation_record:
            memory_store.add_conversation(state.child_id, state.conversation_record)
        if state.learning_progress:
            memory_store.update_learning_progress(state.child_id, state.learning_progress)
        
        return LongTermMemoryOutput(
            load_success=False,
            save_success=True
        )
    
    return LongTermMemoryOutput(
        load_success=False,
        save_success=False
    )


# ============== 节点2：作业检查节点 ==============
def homework_check_node(
    state: HomeworkCheckInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> HomeworkCheckOutput:
    """
    title: 作业检查与提醒
    desc: 检查作业完成状态，基于时间有效性过滤过期作业，生成提醒消息
    """
    ctx = runtime.context
    
    homework_status = "无作业"
    need_remind = False
    remind_message = ""
    
    # 使用MemoryStore获取有效的作业（自动过滤过期和已完成的作业）
    from graphs.memory_store import MemoryStore
    memory_store = MemoryStore.get_instance()
    
    # 获取有效的作业列表
    valid_homework = memory_store.get_valid_homework(state.child_id)
    
    if valid_homework:
        homework_status = "未开始"
        need_remind = True
        
        # 生成提醒消息（包含截止时间信息）
        subjects_with_deadline = []
        for hw in valid_homework:
            subject = hw.get("subject", "未知")
            deadline_str = hw.get("deadline", "")
            
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str)
                    now = datetime.now()
                    hours_left = (deadline - now).total_seconds() / 3600
                    
                    if hours_left < 24:
                        subjects_with_deadline.append(f"{subject}（剩余{int(hours_left)}小时）")
                    else:
                        days_left = int(hours_left / 24)
                        subjects_with_deadline.append(f"{subject}（剩余{days_left}天）")
                except (ValueError, TypeError):
                    subjects_with_deadline.append(subject)
            else:
                subjects_with_deadline.append(subject)
        
        remind_message = f"宝贝，你还有{len(valid_homework)}项作业需要完成哦：{', '.join(subjects_with_deadline)}。要不要现在开始做作业呢？"
    else:
        homework_status = "无作业"
        remind_message = "今天没有需要完成的作业，真棒！可以尽情玩耍啦～"
    
    return HomeworkCheckOutput(
        homework_status=homework_status,
        need_remind=need_remind,
        remind_message=remind_message
    )


# ============== 节点3：主动关心节点（Agent节点） ==============
def active_care_node(
    state: ActiveCareInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ActiveCareOutput:
    """
    title: 主动关心
    desc: 基于孩子的状态和历史对话，主动发起关心的对话
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    # 使用jinja2模板渲染提示词
    sp_tpl = Template(sp)
    up_tpl = Template(up)
    
    system_prompt = sp_tpl.render({
        "child_name": state.child_name,
        "child_age": state.child_age,
        "interests": ", ".join(state.child_interests)
    })
    
    user_prompt = up_tpl.render({
        "current_time": state.current_time,
        "conversation_history": state.conversation_history[-3:] if state.conversation_history else [],
        "interests": ", ".join(state.child_interests)
    })
    
    # 初始化LLM客户端
    client = LLMClient(ctx=ctx)
    
    # 构建消息
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    # 调用大模型
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.8)
    )
    
    # 提取响应文本
    if isinstance(response.content, str):
        care_message = response.content
    else:
        care_message = str(response.content)
    
    return ActiveCareOutput(care_message=care_message.strip())


# ============== 节点4：口语练习节点 ==============
def speaking_practice_node(
    state: SpeakingPracticeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SpeakingPracticeOutput:
    """
    title: 口语练习
    desc: 语音识别、纠正和反馈，帮助孩子练习口语
    integrations: 语音大模型, 大语言模型
    """
    ctx = runtime.context
    
    recognized_text = state.user_input_text
    
    # 如果有音频输入，进行语音识别
    if state.user_input_audio and not recognized_text:
        asr_client = ASRClient(ctx=ctx)
        
        try:
            # 使用URL进行语音识别
            text, data = asr_client.recognize(
                uid=f"{state.child_name}_practice",
                url=state.user_input_audio.url
            )
            recognized_text = text
        except Exception as e:
            recognized_text = state.user_input_text  # 降级到使用文本输入
    
    # 构建学习进度信息
    practice_count = 0
    from graphs.memory_store import MemoryStore
    memory_store = MemoryStore.get_instance()
    learning_progress = memory_store.get_learning_progress(state.child_name)
    
    if learning_progress and "speaking_practice_count" in learning_progress:
        practice_count = learning_progress["speaking_practice_count"]
    
    # 使用大模型进行语音纠正和反馈
    client = LLMClient(ctx=ctx)
    
    feedback_prompt = f"""孩子的姓名：{state.child_name}，年龄：{state.child_age}岁
孩子刚才说：{recognized_text}
已练习次数：{practice_count}

请对孩子的口语表达进行评价和指导：
1. 纠正发音或语法错误（如果有）
2. 给予鼓励和肯定
3. 提供改进建议
4. 提出一个相关的问题引导继续对话

请用友好、鼓励的语气回复，适合{state.child_age}岁的孩子理解。

重要提醒：
- 只输出对话内容，不要包含任何动作描述（如：（微笑）、（点头）、（鼓掌）等）
- 不要包含括号内的任何文字
- 不要使用表情符号
- 直接用文字表达你的鼓励和指导"""
    
    messages = [
        HumanMessage(content=feedback_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model="doubao-seed-1-8-251228",
        temperature=0.8
    )
    
    if isinstance(response.content, str):
        feedback = response.content
    else:
        feedback = str(response.content)
    
    # 更新练习次数
    new_practice_count = practice_count + 1
    memory_store.update_learning_progress(state.child_name, {
        "speaking_practice_count": new_practice_count,
        "last_practice_time": datetime.now().isoformat()
    })
    
    return SpeakingPracticeOutput(
        recognized_text=recognized_text,
        corrected_text=recognized_text,  # LLM会自动在反馈中纠正
        feedback=feedback.strip(),
        practice_count=new_practice_count
    )


# ============== 节点5：实时对话节点（Agent节点） ==============
def realtime_conversation_node(
    state: RealtimeConversationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeConversationOutput:
    """
    title: 实时对话
    desc: 与孩子进行实时对话，回应孩子的问题和需求（支持时间感知的上下文）
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    # 渲染系统提示词
    sp_tpl = Template(sp)
    system_prompt = sp_tpl.render({
        "child_name": state.child_name,
        "child_age": state.child_age
    })
    
    # 获取当前时间信息
    current_time = datetime.now()
    time_of_day = "早上" if current_time.hour < 12 else "下午" if current_time.hour < 18 else "晚上"
    current_date = current_time.strftime("%Y年%m月%d日")
    
    # 渲染用户提示词（包含时间信息）
    up_tpl = Template(up)
    user_prompt = up_tpl.render({
        "user_input": state.user_input_text,
        "context_info": state.context_info,
        "conversation_history": state.conversation_history[-3:] if state.conversation_history else [],
        "current_time": current_time.strftime("%H:%M"),
        "time_of_day": time_of_day,
        "current_date": current_date
    })
    
    # 初始化LLM客户端
    client = LLMClient(ctx=ctx)
    
    # 构建消息
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    # 调用大模型
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.8)
    )
    
    # 提取响应文本
    if isinstance(response.content, str):
        ai_response = response.content
    else:
        ai_response = str(response.content)
    
    return RealtimeConversationOutput(ai_response=ai_response.strip())


# ============== 节点6：语音合成节点 ==============
def voice_synthesis_node(
    state: VoiceSynthesisInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> VoiceSynthesisOutput:
    """
    title: 语音合成
    desc: 将文本转换为语音输出
    integrations: 语音大模型
    """
    ctx = runtime.context
    
    # 初始化TTS客户端
    tts_client = TTSClient(ctx=ctx)
    
    # 根据孩子年龄选择合适的语音
    # 12岁以下使用儿童语音，否则使用正常语音
    if state.child_age <= 12:
        voice_id = "zh_female_xueayi_saturn_bigtts"  # 儿童读物声音
    else:
        voice_id = "zh_female_xiaohe_uranus_bigtts"  # 默认女声
    
    # 语音合成
    audio_url, audio_size = tts_client.synthesize(
        uid=f"child_{state.child_age}",
        text=state.text,
        speaker=voice_id,
        audio_format="mp3",
        sample_rate=24000,
        speech_rate=10,  # 稍微放慢语速，适合孩子
        loudness_rate=10  # 提高音量
    )
    
    return VoiceSynthesisOutput(
        audio_url=audio_url,
        audio_size=audio_size
    )


# ============== 条件判断函数：路由决策 ==============
def route_decision(state: RouteDecisionInput) -> str:
    """
    title: 路由决策
    desc: 根据触发类型和作业状态决定执行哪个分支
    """
    if state.trigger_type == "care":
        return "主动关心"
    elif state.trigger_type == "remind":
        return "作业提醒"
    elif state.trigger_type == "practice":
        return "口语练习"
    elif state.trigger_type == "conversation":
        return "实时对话"
    elif state.trigger_type == "realtime_call":
        return "实时通话"
    else:
        return "实时对话"  # 默认分支


# ============== 实时通话快速节点（低延迟专用）=============
def realtime_call_fast_node(
    state: RealtimeCallInput,  # 使用RealtimeCallInput
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeCallOutput:
    """
    title: 实时通话快速节点
    desc: 整合ASR+LLM+TTS，专为实时通话优化，最小化延迟
    integrations: 语音大模型, 大语言模型
    """
    from coze_coding_dev_sdk import ASRClient, LLMClient, TTSClient

    ctx = runtime.context

    # ============== 步骤1: 语音识别（ASR）=============
    user_text = state.user_input_text

    # 如果有音频输入且没有文本，进行语音识别
    if state.user_input_audio and not user_text:
        asr_client = ASRClient(ctx=ctx)
        try:
            text, _ = asr_client.recognize(
                uid=f"realtime_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                url=state.user_input_audio.url
            )
            user_text = text
            print(f"🎤 ASR识别成功: {user_text}")
        except Exception as e:
            print(f"⚠️ ASR识别失败: {e}")
    
    if not user_text:
        user_text = "你好"
    
    # ============== 步骤2: 大模型生成（LLM）=============
    llm_client = LLMClient(ctx=ctx)
    
    # 获取当前时间信息
    current_time = datetime.now()
    time_of_day = "早上" if current_time.hour < 12 else "下午" if current_time.hour < 18 else "晚上"
    
    # 简化的提示词，减少token数量
    simple_prompt = f"""你是{state.child_name}的好朋友，{state.child_age}岁。

当前时间：{time_of_day}
孩子说：{user_text}

请用简单、友好的语言回复{state.child_age}岁的孩子。保持温暖和关爱。

重要：
- 只输出对话内容
- 不要包含动作描述（如微笑、点头等）
- 不要使用表情符号
- 回复要简短精炼（50-100字）
- 直接回答问题或回应
"""
    
    messages = [
        HumanMessage(content=simple_prompt)
    ]
    
    # 使用低延迟配置
    response = llm_client.invoke(
        messages=messages,
        model="doubao-seed-1-8-251228",
        temperature=0.7,  # 稍高温度，更自然
        max_tokens=150    # 限制输出长度，减少延迟
    )
    
    ai_response = response.content if isinstance(response.content, str) else str(response.content)
    ai_response = ai_response.strip()
    print(f"🤖 LLM生成: {ai_response}")
    
    # ============== 步骤3: 语音合成（TTS）=============
    tts_client = TTSClient(ctx=ctx)
    
    # 使用快速TTS配置
    # 选择低延迟音色
    if state.child_age <= 12:
        voice_id = "zh_female_xueayi_saturn_bigtts"  # 儿童音色
    else:
        voice_id = "zh_female_xiaohe_uranus_bigtts"  # 默认女声
    
    # 低延迟配置
    audio_url, audio_size = tts_client.synthesize(
        uid=f"realtime_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        text=ai_response,
        speaker=voice_id,
        audio_format="mp3",
        sample_rate=16000,   # 降低采样率以减少延迟
        speech_rate=10,      # 标准语速
        loudness_rate=10     # 提高音量
    )
    
    print(f"🔊 TTS合成完成: {audio_url}")
    
    return RealtimeCallOutput(
        ai_response=ai_response,
        ai_response_audio=audio_url,
        recognized_text=user_text
    )
