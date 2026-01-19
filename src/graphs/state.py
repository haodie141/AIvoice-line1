from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from utils.file.file import File

# ============== 全局状态定义 ==============
class GlobalState(BaseModel):
    """AI陪伴孩子工作流的全局状态（支持时间感知）"""
    # 孩子基本信息（支持默认值）
    child_id: str = Field(default="default_child", description="孩子ID")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    child_interests: List[str] = Field(default=["阅读", "游戏"], description="孩子兴趣爱好")
    
    # 作业信息（支持时间有效性判断）
    homework_list: List[dict] = Field(default=[], description="作业列表（每个作业包含创建时间、截止时间等）")
    homework_status: str = Field(default="", description="作业状态：未开始/进行中/已完成/无作业")
    need_remind: bool = Field(default=False, description="是否需要提醒")
    
    # 长期记忆（支持时间维度的数据管理）
    conversation_history: List[dict] = Field(default=[], description="对话历史记录（每条包含时间戳）")
    learning_progress: dict = Field(default={}, description="学习进度记录")
    speaking_practice_count: int = Field(default=0, description="口语练习次数")
    
    # 对话相关
    user_input_text: str = Field(default="", description="用户输入的文本")
    user_input_audio: Optional[File] = Field(default=None, description="用户输入的音频")
    recognized_text: str = Field(default="", description="识别出的文本")
    
    # AI响应
    ai_response: str = Field(default="", description="AI的文本响应")
    ai_response_audio: Optional[str] = Field(default=None, description="AI的音频响应URL")
    
    # 触发场景
    trigger_type: str = Field(default="", description="触发类型：conversation/practice/care/remind")
    
    # 时间信息
    current_time: str = Field(default="", description="当前时间（ISO格式）")

# ============== 图的输入输出 ==============
class GraphInput(BaseModel):
    """工作流输入 - 支持纯音频输入，其他参数可选"""
    child_id: str = Field(default="default_child", description="孩子ID（默认：default_child）")
    child_name: str = Field(default="小朋友", description="孩子姓名（默认：小朋友）")
    child_age: int = Field(default=8, description="孩子年龄（默认：8岁）")
    child_interests: List[str] = Field(default=["阅读", "游戏"], description="孩子兴趣爱好（默认：阅读、游戏）")
    trigger_type: Literal["conversation", "practice", "care", "remind", "realtime_call"] = Field(
        default="realtime_call",
        description="触发类型（默认：实时通话，低延迟模式）"
    )
    user_input_text: str = Field(default="", description="用户输入文本（可选）")
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频（推荐）")
    homework_list: List[dict] = Field(default=[], description="作业列表（可选）")

class GraphOutput(BaseModel):
    """工作流输出"""
    ai_response: str = Field(..., description="AI的文本响应")
    ai_response_audio: Optional[str] = Field(default=None, description="AI的音频响应URL")
    trigger_type: str = Field(..., description="触发类型")
    homework_status: str = Field(default="", description="作业状态")
    speaking_practice_count: int = Field(default=0, description="口语练习次数")

# ============== 节点1：长期记忆节点 ==============
class LongTermMemoryInput(BaseModel):
    """长期记忆节点输入"""
    child_id: str = Field(..., description="孩子ID")
    action_type: Literal["load", "save"] = Field(..., description="操作类型：加载/保存")
    conversation_record: Optional[dict] = Field(default=None, description="要保存的对话记录")
    learning_progress: Optional[dict] = Field(default=None, description="学习进度数据")

class LongTermMemoryOutput(BaseModel):
    """长期记忆节点输出"""
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    learning_progress: dict = Field(default={}, description="学习进度")
    speaking_practice_count: int = Field(default=0, description="口语练习次数")
    load_success: bool = Field(default=False, description="加载是否成功")
    save_success: bool = Field(default=False, description="保存是否成功")

# ============== 节点2：作业检查节点 ==============
class HomeworkCheckInput(BaseModel):
    """作业检查节点输入"""
    homework_list: List[dict] = Field(default=[], description="作业列表")
    current_time: str = Field(..., description="当前时间")
    child_id: str = Field(..., description="孩子ID")

class HomeworkCheckOutput(BaseModel):
    """作业检查节点输出"""
    homework_status: str = Field(..., description="作业状态")
    need_remind: bool = Field(..., description="是否需要提醒")
    remind_message: str = Field(default="", description="提醒消息")

# ============== 节点3：主动关心节点 ==============
class ActiveCareInput(BaseModel):
    """主动关心节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    child_interests: List[str] = Field(default=[], description="孩子兴趣爱好")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    current_time: str = Field(..., description="当前时间")

class ActiveCareOutput(BaseModel):
    """主动关心节点输出"""
    care_message: str = Field(..., description="关心的消息内容")

# ============== 节点4：口语练习节点 ==============
class SpeakingPracticeInput(BaseModel):
    """口语练习节点输入"""
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    user_input_text: str = Field(default="", description="用户输入文本（备用）")
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    practice_topic: str = Field(default="", description="练习主题")

class SpeakingPracticeOutput(BaseModel):
    """口语练习节点输出"""
    recognized_text: str = Field(..., description="识别出的文本")
    corrected_text: str = Field(default="", description="纠正后的文本")
    feedback: str = Field(..., description="反馈和指导")
    practice_count: int = Field(default=0, description="本次练习后的总次数")

# ============== 节点5：实时对话节点 ==============
class RealtimeConversationInput(BaseModel):
    """实时对话节点输入"""
    user_input_text: str = Field(..., description="用户输入文本")
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    context_info: str = Field(default="", description="上下文信息")

class RealtimeConversationOutput(BaseModel):
    """实时对话节点输出"""
    ai_response: str = Field(..., description="AI响应内容")

# ============== 节点6：语音合成节点 ==============
class VoiceSynthesisInput(BaseModel):
    """语音合成节点输入"""
    text: str = Field(..., description="要合成的文本")
    child_age: int = Field(..., description="孩子年龄")
    voice_type: str = Field(default="child", description="语音类型")

class VoiceSynthesisOutput(BaseModel):
    """语音合成节点输出"""
    audio_url: str = Field(..., description="生成的音频URL")
    audio_size: int = Field(default=0, description="音频大小")

# ============== 实时通话快速节点（低延迟专用）=============
class RealtimeCallInput(BaseModel):
    """实时通话快速节点输入（支持默认值）"""
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频（优先）")
    user_input_text: str = Field(default="", description="用户输入文本（备用）")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    child_id: str = Field(default="default_child", description="孩子ID")

class RealtimeCallOutput(BaseModel):
    """实时通话快速节点输出"""
    ai_response: str = Field(default="", description="AI文本响应")
    ai_response_audio: str = Field(default="", description="AI音频响应URL")
    recognized_text: str = Field(default="", description="识别出的用户语音文本")

# ============== 条件判断节点 ==============
class RouteDecisionInput(BaseModel):
    """路由决策输入"""
    trigger_type: str = Field(..., description="触发类型")
    need_remind: bool = Field(default=False, description="是否需要提醒")

# ============== 包装节点类型定义（用于图编排） ==============
class LoadMemoryWrapInput(BaseModel):
    """加载记忆包装节点输入（支持默认值）"""
    child_id: str = Field(default="default_child", description="孩子ID")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    child_interests: List[str] = Field(default=["阅读", "游戏"], description="孩子兴趣爱好")
    trigger_type: str = Field(default="conversation", description="触发类型")
    user_input_text: str = Field(default="", description="用户输入文本")
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    homework_list: List[dict] = Field(default=[], description="作业列表")

class LoadMemoryWrapOutput(BaseModel):
    """加载记忆包装节点输出"""
    child_id: str = Field(..., description="孩子ID")
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    child_interests: List[str] = Field(default=[], description="孩子兴趣爱好")
    trigger_type: str = Field(..., description="触发类型")
    user_input_text: str = Field(default="", description="用户输入文本")
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    homework_list: List[dict] = Field(default=[], description="作业列表")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    learning_progress: dict = Field(default={}, description="学习进度")
    speaking_practice_count: int = Field(default=0, description="口语练习次数")
    current_time: str = Field(default="", description="当前时间")

class HomeworkCheckWrapInput(BaseModel):
    """作业检查包装节点输入"""
    homework_list: List[dict] = Field(default=[], description="作业列表")
    current_time: str = Field(..., description="当前时间")
    child_id: str = Field(..., description="孩子ID")
    ai_response: str = Field(default="", description="AI响应")

class HomeworkCheckWrapOutput(BaseModel):
    """作业检查包装节点输出"""
    homework_status: str = Field(..., description="作业状态")
    need_remind: bool = Field(..., description="是否需要提醒")
    ai_response: str = Field(default="", description="AI响应")

class ActiveCareWrapInput(BaseModel):
    """主动关心包装节点输入"""
    child_name: str = Field(..., description="孩子姓名")
    child_age: int = Field(..., description="孩子年龄")
    child_interests: List[str] = Field(default=[], description="孩子兴趣爱好")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    current_time: str = Field(..., description="当前时间")

class ActiveCareWrapOutput(BaseModel):
    """主动关心包装节点输出"""
    ai_response: str = Field(..., description="AI响应")

class SpeakingPracticeWrapInput(BaseModel):
    """口语练习包装节点输入（支持默认值）"""
    user_input_audio: Optional[File] = Field(default=None, description="用户输入音频")
    user_input_text: str = Field(default="", description="用户输入文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")

class SpeakingPracticeWrapOutput(BaseModel):
    """口语练习包装节点输出"""
    recognized_text: str = Field(..., description="识别出的文本")
    ai_response: str = Field(..., description="AI反馈")
    speaking_practice_count: int = Field(default=0, description="练习次数")

class RealtimeConversationWrapInput(BaseModel):
    """实时对话包装节点输入（支持默认值）"""
    child_id: str = Field(default="default_child", description="孩子ID")
    user_input_text: str = Field(default="", description="用户输入文本")
    child_name: str = Field(default="小朋友", description="孩子姓名")
    child_age: int = Field(default=8, description="孩子年龄")
    conversation_history: List[dict] = Field(default=[], description="对话历史")
    homework_status: str = Field(default="", description="作业状态")

class RealtimeConversationWrapOutput(BaseModel):
    """实时对话包装节点输出"""
    ai_response: str = Field(..., description="AI响应")

class VoiceSynthesisWrapInput(BaseModel):
    """语音合成包装节点输入（支持默认值）"""
    ai_response: str = Field(default="", description="要合成的文本")
    child_age: int = Field(default=8, description="孩子年龄")

class VoiceSynthesisWrapOutput(BaseModel):
    """语音合成包装节点输出"""
    ai_response_audio: str = Field(..., description="音频URL")

class SaveMemoryWrapInput(BaseModel):
    """保存记忆包装节点输入（支持默认值）"""
    child_id: str = Field(default="default_child", description="孩子ID")
    trigger_type: str = Field(default="conversation", description="触发类型")
    user_input_text: str = Field(default="", description="用户输入文本")
    recognized_text: str = Field(default="", description="识别出的文本")
    ai_response: str = Field(default="", description="AI响应")
    speaking_practice_count: int = Field(default=0, description="练习次数")
    current_time: str = Field(default="", description="当前时间")

class SaveMemoryWrapOutput(BaseModel):
    """保存记忆包装节点输出"""
    saved: bool = Field(default=True, description="是否保存成功")
