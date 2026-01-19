"""
实时通话工作流 - 低延迟版本
专为AI实时通话场景设计，去除非必要的节点，优化延迟

工作流程：ASR → LLM → TTS
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from utils.file.file import File


# ============== 全局状态定义 ==============
class RealtimeCallState(BaseModel):
    """实时通话全局状态（精简版）"""
    # 输入
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    user_input_text: str = Field(default="", description="用户输入文本")

    # 孩子信息（带默认值）
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")

    # 上下文（可选，用于连续对话）
    conversation_history: List[dict] = Field(default=[], description="对话历史（最近3条）")
    child_id: str = Field(default="default_child", description="孩子ID")

    # 处理结果
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(default="", description="AI响应文本")
    ai_response_audio: Optional[str] = Field(default=None, description="AI响应音频URL")

    # 时间
    current_time: str = Field(default="", description="当前时间")


# ============== 图的输入输出 ==============
class RealtimeCallInput(BaseModel):
    """实时通话输入（简化版）"""
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    user_input_text: str = Field(default="", description="用户输入文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史（可选）")
    child_id: str = Field(default="default_child", description="孩子ID")


class RealtimeCallOutput(BaseModel):
    """实时通话输出"""
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(..., description="AI响应文本")
    ai_response_audio: str = Field(..., description="AI响应音频URL")


# ============== 节点1：ASR语音识别 ==============
class ASRNodeInput(BaseModel):
    """ASR节点输入"""
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    user_input_text: str = Field(default="", description="用户输入文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    child_id: str = Field(default="default_child", description="孩子ID")


class ASRNodeOutput(BaseModel):
    """ASR节点输出"""
    recognized_text: str = Field(default="", description="识别出的文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    child_id: str = Field(default="default_child", description="孩子ID")
    current_time: str = Field(default="", description="当前时间")


def asr_node(
    state: ASRNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ASRNodeOutput:
    """
    title: 语音识别
    desc: 将音频转换为文本
    integrations: 语音大模型
    """
    ctx = runtime.context

    # 如果有文本，直接使用
    if state.user_input_text:
        return ASRNodeOutput(
            recognized_text=state.user_input_text,
            child_name=state.child_name,
            child_age=state.child_age,
            conversation_history=state.conversation_history,
            child_id=state.child_id,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    # 如果有音频，进行语音识别
    if state.user_input_audio:
        try:
            from coze_coding_dev_sdk import ASRClient
            asr_client = ASRClient(ctx=ctx)
            text, _ = asr_client.recognize(
                uid=f"{state.child_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                url=state.user_input_audio.url
            )
            print(f"🎤 ASR识别: {text}")
        except Exception as e:
            print(f"⚠️ ASR识别失败: {e}")
            text = ""

        return ASRNodeOutput(
            recognized_text=text,
            child_name=state.child_name,
            child_age=state.child_age,
            conversation_history=state.conversation_history,
            child_id=state.child_id,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    # 都没有，返回空
    return ASRNodeOutput(
        recognized_text="",
        child_name=state.child_name,
        child_age=state.child_age,
        conversation_history=state.conversation_history,
        child_id=state.child_id,
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


# ============== 节点2：LLM对话生成 ==============
class LLMNodeInput(BaseModel):
    """LLM节点输入"""
    recognized_text: str = Field(default="", description="识别出的文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    child_id: str = Field(default="default_child", description="孩子ID")
    current_time: str = Field(default="", description="当前时间")


class LLMNodeOutput(BaseModel):
    """LLM节点输出"""
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(default="", description="AI响应文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    child_id: str = Field(default="default_child", description="孩子ID")
    current_time: str = Field(default="", description="当前时间")


def llm_node(
    state: LLMNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> LLMNodeOutput:
    """
    title: 对话生成
    desc: 大模型生成回复（低延迟模式）
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 如果没有识别到文本，返回空响应
    if not state.recognized_text:
        return LLMNodeOutput(
            recognized_text=state.recognized_text,
            ai_response="",
            child_name=state.child_name,
            child_age=state.child_age,
            conversation_history=state.conversation_history,
            child_id=state.child_id,
            current_time=state.current_time
        )

    # 构建提示词
    prompt = f"""你是{state.child_name}的AI朋友，{state.child_age}岁。

孩子说：{state.recognized_text}

请友好地回应孩子，适合{state.child_age}岁的孩子理解。
要求：
1. 使用简单、生动的语言
2. 温暖、亲切的语气
3. 不要包含动作描述（如：（微笑）等）
4. 不要使用表情符号
5. 控制长度在100字以内（为了低延迟）

直接输出对话内容，不要其他文字。"""

    try:
        from coze_coding_dev_sdk import LLMClient
        from langchain_core.messages import HumanMessage

        client = LLMClient(ctx=ctx)
        messages = [HumanMessage(content=prompt)]

        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-8-251228",
            temperature=0.7,
            max_tokens=300  # 限制字数，减少延迟
        )

        ai_response = response.content if isinstance(response.content, str) else str(response.content)
        print(f"💬 LLM生成: {ai_response[:50]}...")

    except Exception as e:
        print(f"⚠️ LLM生成失败: {e}")
        ai_response = "不好意思，我没听清楚，能再说一遍吗？"

    return LLMNodeOutput(
        recognized_text=state.recognized_text,
        ai_response=ai_response.strip(),
        child_name=state.child_name,
        child_age=state.child_age,
        conversation_history=state.conversation_history,
        child_id=state.child_id,
        current_time=state.current_time
    )


# ============== 节点3：TTS语音合成 ==============
class TTSNodeInput(BaseModel):
    """TTS节点输入"""
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(default="", description="AI响应文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    child_id: str = Field(default="default_child", description="孩子ID")
    current_time: str = Field(default="", description="当前时间")


class TTSNodeOutput(BaseModel):
    """TTS节点输出"""
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(default="", description="AI响应文本")
    ai_response_audio: str = Field(default="", description="AI响应音频URL")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    child_id: str = Field(default="default_child", description="孩子ID")
    current_time: str = Field(default="", description="当前时间")


def tts_node(
    state: TTSNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> TTSNodeOutput:
    """
    title: 语音合成
    desc: 将文本转换为语音
    integrations: 语音大模型
    """
    ctx = runtime.context

    if not state.ai_response:
        return TTSNodeOutput(
            recognized_text=state.recognized_text,
            ai_response="",
            ai_response_audio="",
            child_name=state.child_name,
            child_age=state.child_age,
            conversation_history=state.conversation_history,
            child_id=state.child_id,
            current_time=state.current_time
        )

    try:
        from coze_coding_dev_sdk import TTSClient

        tts_client = TTSClient(ctx=ctx)

        # 选择语音
        if state.child_age <= 12:
            voice_id = "zh_female_xueayi_saturn_bigtts"  # 儿童语音
        else:
            voice_id = "zh_female_xiaohe_uranus_bigtts"  # 正常语音

        audio_url, audio_size = tts_client.synthesize(
            uid=f"{state.child_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            text=state.ai_response,
            speaker=voice_id,
            audio_format="mp3",
            sample_rate=24000,
            speech_rate=10,  # 稍微放慢，适合孩子
            loudness_rate=10
        )

        print(f"🔊 TTS合成完成: {audio_size} bytes")

    except Exception as e:
        print(f"⚠️ TTS合成失败: {e}")
        audio_url = ""

    return TTSNodeOutput(
        recognized_text=state.recognized_text,
        ai_response=state.ai_response,
        ai_response_audio=audio_url,
        child_name=state.child_name,
        child_age=state.child_age,
        conversation_history=state.conversation_history,
        child_id=state.child_id,
        current_time=state.current_time
    )


# ============== 创建实时通话图（低延迟版本） ==============
builder = StateGraph(RealtimeCallState, input_schema=RealtimeCallInput, output_schema=RealtimeCallOutput)

# 添加节点（只保留核心流程）
builder.add_node("asr", asr_node)
builder.add_node("llm", llm_node)
builder.add_node("tts", tts_node)

# 设置入口点
builder.set_entry_point("asr")

# 添加边（线性流程，无分支，最短路径）
builder.add_edge("asr", "llm")
builder.add_edge("llm", "tts")
builder.add_edge("tts", END)

# 编译图
realtime_call_graph = builder.compile()
