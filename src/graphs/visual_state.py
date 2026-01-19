"""
可视化模式的状态定义（步骤级拆分节点）

这个文件定义了可视化模式下拆分后的节点状态，
每个步骤都是独立的节点，对应扣子工作流的步骤级可视化。
"""

from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field
from utils.file.file import File


# ============== 可视化模式：口语练习拆分节点 ==============

# 1. 语音识别节点
class PracticeASRInput(BaseModel):
    """口语练习-ASR节点输入"""
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    user_input_text: str = Field(default="", description="用户输入文本（如果有）")
    child_name: str = Field(..., description="孩子姓名")

class PracticeASROutput(BaseModel):
    """口语练习-ASR节点输出"""
    recognized_text: str = Field(..., description="识别出的文本")
    has_audio: bool = Field(default=False, description="是否有音频输入")


# 2. 复习检查节点
class PracticeReviewCheckInput(BaseModel):
    """口语练习-复习检查节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    recognized_text: str = Field(default="", description="识别出的文本")

class PracticeReviewCheckOutput(BaseModel):
    """口语练习-复习检查节点输出"""
    has_review: bool = Field(default=False, description="是否有需要复习的知识点")
    review_knowledge: Optional[dict] = Field(default=None, description="复习知识点信息")
    should_review: bool = Field(default=False, description="是否应该优先复习")


# 3. 场景选择节点
class PracticeScenarioSelectInput(BaseModel):
    """口语练习-场景选择节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    child_interests: List[str] = Field(default=[], description="孩子兴趣爱好")
    recognized_text: str = Field(default="", description="识别出的文本")
    skip_scenario: bool = Field(default=False, description="是否跳过场景选择（因为有复习）")

class PracticeScenarioSelectOutput(BaseModel):
    """口语练习-场景选择节点输出"""
    scenario_key: str = Field(..., description="选择的场景key")
    scenario_name: str = Field(..., description="场景名称")
    topic: str = Field(..., description="选择的话题")
    is_review_mode: bool = Field(default=False, description="是否为复习模式")


# 4. 对话引擎节点（四阶段）
class PracticeDialogueInput(BaseModel):
    """口语练习-对话引擎节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    child_interests: List[str] = Field(default=[], description="孩子兴趣爱好")
    recognized_text: str = Field(default="", description="识别出的文本")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    
    # 场景信息
    scenario_key: str = Field(..., description="场景key")
    scenario_name: str = Field(..., description="场景名称")
    topic: str = Field(..., description="话题")
    is_review_mode: bool = Field(default=False, description="是否为复习模式")
    review_knowledge: Optional[dict] = Field(default=None, description="复习知识点")
    
    # 对话阶段
    practice_stage: Optional[str] = Field(default=None, description="当前阶段：initiate/question/followup/summarize")
    turn_count: int = Field(default=0, description="对话轮数")

class PracticeDialogueOutput(BaseModel):
    """口语练习-对话引擎节点输出"""
    ai_response: str = Field(..., description="AI的回复")
    corrected_text: str = Field(default="", description="纠正后的文本")
    next_stage: str = Field(..., description="下一阶段")
    turn_count: int = Field(default=0, description="当前轮数")


# 5. 知识点识别节点
class PracticeKnowledgeExtractInput(BaseModel):
    """口语练习-知识点识别节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    recognized_text: str = Field(..., description="识别出的文本")
    stage: str = Field(..., description="当前阶段")

class PracticeKnowledgeExtractOutput(BaseModel):
    """口语练习-知识点识别节点输出"""
    new_knowledge: List[dict] = Field(default=[], description="新识别的知识点列表")
    has_new_knowledge: bool = Field(default=False, description="是否有新知识点")


# 6. 更新记忆节点
class PracticeUpdateMemoryInput(BaseModel):
    """口语练习-更新记忆节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    new_knowledge: List[dict] = Field(default=[], description="新知识点")
    stage: str = Field(..., description="当前阶段")
    practice_count: int = Field(default=0, description="当前练习次数")
    turn_count: int = Field(default=0, description="对话轮数")

class PracticeUpdateMemoryOutput(BaseModel):
    """口语练习-更新记忆节点输出"""
    practice_count: int = Field(..., description="更新后的练习次数")
    memory_updated: bool = Field(default=True, description="记忆是否更新成功")


# 7. TTS节点
class PracticeTTSInput(BaseModel):
    """口语练习-TTS节点输入"""
    ai_response: str = Field(..., description="AI的回复")
    child_age: int = Field(..., description="孩子年龄")

class PracticeTTSOutput(BaseModel):
    """口语练习-TTS节点输出"""
    audio_url: str = Field(..., description="生成的音频URL")


# ============== 可视化模式：实时对话拆分节点 ==============

# 1. 搜索判断节点
class RealtimeSearchJudgmentInput(BaseModel):
    """实时对话-搜索判断节点输入"""
    user_input_text: str = Field(..., description="用户输入文本")
    child_age: int = Field(..., description="孩子年龄")

class RealtimeSearchJudgmentOutput(BaseModel):
    """实时对话-搜索判断节点输出"""
    need_search: bool = Field(..., description="是否需要搜索")
    search_query: str = Field(default="", description="搜索关键词")


# 2. 联网搜索节点
class RealtimeWebSearchInput(BaseModel):
    """实时对话-联网搜索节点输入"""
    search_query: str = Field(..., description="搜索关键词")

class RealtimeWebSearchOutput(BaseModel):
    """实时对话-联网搜索节点输出"""
    search_results: str = Field(default="", description="搜索结果摘要")
    search_success: bool = Field(default=False, description="搜索是否成功")


# 3. 上下文构建节点
class RealtimeContextBuilderInput(BaseModel):
    """实时对话-上下文构建节点输入"""
    user_input_text: str = Field(..., description="用户输入文本")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    search_results: str = Field(default="", description="搜索结果")
    homework_status: str = Field(default="", description="作业状态")
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")

class RealtimeContextBuilderOutput(BaseModel):
    """实时对话-上下文构建节点输出"""
    context_str: str = Field(..., description="构建的上下文字符串")
    has_context: bool = Field(default=True, description="是否有上下文")


# 4. LLM生成节点
class RealtimeLLMGenerateInput(BaseModel):
    """实时对话-LLM生成节点输入"""
    user_input_text: str = Field(..., description="用户输入文本")
    context_str: str = Field(..., description="上下文")
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")

class RealtimeLLMGenerateOutput(BaseModel):
    """实时对话-LLM生成节点输出"""
    ai_response: str = Field(..., description="AI生成的回复")


# 5. 作业意图识别节点
class RealtimeHomeworkCheckInput(BaseModel):
    """实时对话-作业意图识别节点输入"""
    user_input_text: str = Field(..., description="用户输入文本")
    ai_response: str = Field(..., description="AI回复")
    valid_homework: List[dict] = Field(default=[], description="有效作业列表")
    child_age: int = Field(..., description="孩子年龄")
    child_id: str = Field(..., description="孩子ID")

class RealtimeHomeworkCheckOutput(BaseModel):
    """实时对话-作业意图识别节点输出"""
    homework_completed: bool = Field(default=False, description="是否识别到作业完成")
    subject: str = Field(default="", description="完成的学科")
    confirmed: bool = Field(default=False, description="是否确认")
    homework_updated: bool = Field(default=False, description="作业状态是否更新")


# ============== 可视化模式：路由决策 ==============
class VisualRouteDecisionInput(BaseModel):
    """可视化模式路由决策输入"""
    trigger_type: str = Field(..., description="触发类型")
    has_user_input: bool = Field(default=True, description="是否有用户输入")
    current_time: str = Field(default="", description="当前时间")


# ============== 可视化模式的全局状态扩展 ==============
class VisualGlobalState(BaseModel):
    """可视化模式的全局状态（继承自GlobalState，添加拆分节点的中间状态）"""
    # 原有字段
    child_id: str = Field(..., description="孩子ID")
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    child_interests: List[str] = Field(default=[], description="孩子兴趣爱好")
    homework_list: List[dict] = Field(default=[], description="作业列表")
    homework_status: str = Field(default="", description="作业状态")
    need_remind: bool = Field(default=False, description="是否需要提醒")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    learning_progress: dict = Field(default={}, description="学习进度")
    speaking_practice_count: int = Field(default=0, description="口语练习次数")
    user_input_text: str = Field(default="", description="用户输入文本")
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(default="", description="AI的文本响应")
    ai_response_audio: Optional[str] = Field(default=None, description="AI的音频响应URL")
    trigger_type: str = Field(default="", description="触发类型")
    current_time: str = Field(default="", description="当前时间")
    
    # 可视化模式特有的中间状态
    # 口语练习拆分节点的中间状态
    practice_has_review: bool = Field(default=False, description="是否有需要复习的知识点")
    practice_scenario_key: str = Field(default="", description="选择的场景key")
    practice_scenario_name: str = Field(default="", description="场景名称")
    practice_topic: str = Field(default="", description="选择的话题")
    practice_is_review_mode: bool = Field(default=False, description="是否为复习模式")
    practice_review_knowledge: Optional[dict] = Field(default=None, description="复习知识点")
    practice_stage: Optional[str] = Field(default=None, description="当前阶段")
    practice_turn_count: int = Field(default=0, description="对话轮数")
    practice_new_knowledge: List[dict] = Field(default=[], description="新识别的知识点")
    
    # 实时对话拆分节点的中间状态
    realtime_need_search: bool = Field(default=False, description="是否需要搜索")
    realtime_search_query: str = Field(default="", description="搜索关键词")
    realtime_search_results: str = Field(default="", description="搜索结果")
    realtime_context_str: str = Field(default="", description="上下文字符串")
    realtime_homework_completed: bool = Field(default=False, description="是否识别到作业完成")
