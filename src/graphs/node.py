import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient, ASRClient, TTSClient, SearchClient
import requests

from graphs.state import (
    LongTermMemoryInput, LongTermMemoryOutput,
    HomeworkCheckInput, HomeworkCheckOutput,
    ActiveCareInput, ActiveCareOutput,
    SpeakingPracticeInput, SpeakingPracticeOutput,
    RealtimeConversationInput, RealtimeConversationOutput,
    VoiceSynthesisInput, VoiceSynthesisOutput,
    RouteDecisionInput
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
    desc: |
      【包含4个处理步骤】
      1. 加载作业列表 - 从记忆存储获取所有作业
      
      2. 时间过滤算法 - 应用时间推移规则
         - 过滤7天前的过期作业（不提醒）
         - 计算距离截止时间的优先级
      
      3. 智能提醒决策
         - 截止时间 < 1天 → 紧急提醒
         - 截止时间 1-3天 → 温和提醒
         - 截止时间 > 3天 → 不提醒
         - 所有作业已完成 → 无需提醒
      
      4. 生成提醒内容
         - 列出即将到期的作业
         - 语气友好，不施压
         - 鼓励孩子规划时间
      
      【核心特性】
      - 时间推移算法：自动过滤过期作业，避免无效提醒
      - 智能优先级：根据截止时间决定提醒方式
      - 人性化设计：避免催促感，保持温暖语气
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
    title: 主动关心（时间感知）
    desc: |
      【包含3个处理步骤】
      1. 时间上下文分析
         - 判断当前时间段（早晨/中午/晚上/放学时间）
         - 分析上次对话的时间间隔
         - 识别特殊时机（节日、周末等）
      
      2. 关心内容选择
         - 早晨：问候、鼓励一天
         - 放学：关心学校情况
         - 晚上：关心一天收获
         - 长时间未对话：询问最近情况
         - 特殊日子：节日祝福等
      
      3. 个性化生成 - 结合孩子特征生成关心话语
         - 年龄适配的语气
         - 结合孩子兴趣
         - 考虑对话历史和情绪
         - 保持温暖、亲切的语气
      
      【核心特性】
      - 时间感知：根据不同时间段选择关心角度
      - 情绪理解：识别孩子情绪，调整关心语气
      - 个性化：结合年龄、兴趣、对话历史
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


# ============== 节点4：口语练习节点（支持主动引导） ==============
def speaking_practice_node(
    state: SpeakingPracticeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SpeakingPracticeOutput:
    """
    title: 口语练习（智能多阶段）
    desc: |
      【包含7个处理步骤】
      1. 语音识别（ASR）- 将孩子说的话转换为文本
      2. 复习检查 - 查询到期复习的知识点（间隔重复算法）
      3. 场景选择 - 根据孩子兴趣选择练习场景（日常/兴趣/情感）
      4. 对话引擎 - 四阶段对话：
         - 主动发起：提出开放性问题
         - 苏格拉底式提问：引导孩子思考
         - 追问延伸：深入话题细节
         - 总结反馈：表扬和改进建议
      5. 知识追踪 - 自动识别新知识点（单词/概念）
      6. 间隔重复 - 应用SM-2算法安排复习时间
      7. TTS合成 - 生成语音回复
      
      【核心特性】
      - 知识点自动追踪：识别并记录孩子学到的新单词和概念
      - 智能复习：基于间隔重复算法，优先复习到期知识点
      - 场景化练习：日常生活、兴趣爱好、情感表达
      - 苏格拉底式提问：引导孩子主动思考和表达
    integrations: 语音大模型, 大语言模型
    """
    ctx = runtime.context
    
    from graphs.state import PracticeStage, PRACTICE_SCENARIOS
    
    # 构建学习进度信息
    practice_count = 0
    from graphs.memory_store import MemoryStore
    memory_store = MemoryStore.get_instance()
    learning_progress = memory_store.get_learning_progress(state.child_name)
    
    if learning_progress and "speaking_practice_count" in learning_progress:
        practice_count = learning_progress["speaking_practice_count"]
    
    # 判断当前练习阶段
    current_stage = "initiate"  # 默认阶段
    if state.practice_stage:
        current_stage = state.practice_stage.stage
        turn_count = state.practice_stage.turn_count
    else:
        turn_count = 0
    
    # 获取场景信息
    current_scenario = ""
    if state.practice_stage and state.practice_stage.current_scenario:
        current_scenario = state.practice_stage.current_scenario
    
    # 语音识别
    recognized_text = state.user_input_text
    if state.user_input_audio and not recognized_text:
        asr_client = ASRClient(ctx=ctx)
        try:
            text, data = asr_client.recognize(
                uid=f"{state.child_name}_practice",
                url=state.user_input_audio.url
            )
            recognized_text = text
        except Exception as e:
            recognized_text = state.user_input_text
    
    client = LLMClient(ctx=ctx)
    feedback = ""
    corrected_text = recognized_text
    next_stage = None
    followup_question = ""
    
    # ============== 阶段1：主动发起话题（第一轮，孩子没有输入） ==============
    if current_stage == "initiate" and not recognized_text.strip():
        # ========== 新增：优先检查是否有需要复习的知识点 ==========
        try:
            due_for_review = memory_store.get_due_for_review(state.child_name, limit=1)
            if due_for_review:
                # 有需要复习的知识点，优先复习
                review_kp = due_for_review[0]
                kp_type = "单词" if review_kp.get("type") == "word" else "概念"
                kp_content = review_kp.get("content", "")
                kp_context = review_kp.get("context", "")
                
                review_prompt = f"""你是{state.child_name}的口语练习伙伴，现在要帮助孩子复习之前学过的知识。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁

要复习的{kp_type}：{kp_content}
学习时的上下文：{kp_context}

请用友好、自然的方式引导孩子回忆这个知识点：

1. **温和提醒**：不要直接问"你还记得XXX吗"，要自然地提及
2. **情境带入**：结合学习时的上下文或相关场景
3. **鼓励回忆**：给孩子思考和回忆的空间
4. **不要直接给答案**：引导孩子自己说出来

要求：
- 语气要自然、亲切，像朋友聊天一样
- 不要包含任何动作描述
- 不要使用表情符号
- 只输出引导性的话语
- 如果孩子当时理解了这个知识点，可以给一个小提示

示例（复习单词"恐龙"）：
宝贝，上次我们聊到很多神奇的动物，你记得那种长得很大、很久很久以前就生活在地球上的动物叫什么吗？"""
                
                messages = [HumanMessage(content=review_prompt)]
                response = client.invoke(
                    messages=messages,
                    model="doubao-seed-1-8-251228",
                    temperature=0.8
                )
                
                feedback = str(response.content).strip()
                
                # 设置下一阶段为复习模式（标记这是复习）
                next_stage = PracticeStage(
                    stage="question",
                    current_scenario=f"复习·{kp_type}",
                    turn_count=turn_count + 1
                )
                
                # 存储当前复习的知识点ID
                memory_store.update_learning_progress(state.child_name, {
                    "current_review_kp_id": review_kp["id"]
                })
                
                print(f"✅ 发起复习：{kp_content}")
            else:
                # 没有需要复习的，正常发起新话题
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
                
                initiate_prompt = f"""你是{state.child_name}的口语练习伙伴，现在要主动发起对话，引导孩子开口说话。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
孩子兴趣：{', '.join(state.child_interests) if state.child_interests else '未知'}

当前场景：{scenario_info['name']}
选定的主题：{topic}

请用友好、热情的语气主动发起对话，提出一个开放性的问题，引导孩子开始表达。

要求：
1. 问题要简单易懂，适合{state.child_age}岁孩子理解
2. 问题要是开放式的，让孩子可以自由发挥
3. 语气要亲切，像朋友一样
4. 如果孩子有相关兴趣，可以结合兴趣提问
5. 不要包含任何动作描述（如：（微笑）、（点头）等）
6. 不要使用表情符号
7. 只输出一个问题，不要多问

示例场景和问题：
- 日常生活·学校生活：你好呀！今天在学校里发生了什么有趣的事情吗？
- 兴趣爱好·体育运动：你最喜欢什么运动呀？能告诉我为什么吗？
- 情感表达·开心的事情：今天有什么事情让你特别开心吗？"""
                
                messages = [HumanMessage(content=initiate_prompt)]
                response = client.invoke(
                    messages=messages,
                    model="doubao-seed-1-8-251228",
                    temperature=0.9
                )
                
                feedback = str(response.content).strip()
                
                # 设置下一阶段为提问
                next_stage = PracticeStage(
                    stage="question",
                    current_scenario=f"{scenario_info['name']}·{topic}",
                    turn_count=turn_count + 1
                )
        except Exception as e:
            print(f"⚠️ 复习检查失败，使用默认话题: {e}")
            # 降级：使用默认话题
        
    # ============== 阶段2：苏格拉底式提问（孩子第一次回答） ==============
    elif current_stage == "question":
        # 分析孩子的回答，给予鼓励并追问
        question_prompt = f"""你是{state.child_name}的口语练习伙伴，正在和孩子进行对话练习。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
当前场景：{current_scenario}
孩子刚才说：{recognized_text}

请对孩子进行苏格拉底式引导：

1. **肯定和鼓励**：首先表扬孩子的回答，具体指出回答中的亮点
2. **深入追问**：根据孩子的回答，提出一个引导性问题，让孩子继续深入表达
   - 不要直接问"为什么"，可以问"能多说说吗"、"还有呢"、"当时是什么样的"
   - 让孩子描述更多细节和感受
3. **温和纠正**：如果有明显的发音或语法错误，用示范的方式纠正，不要直接说"你错了"
   - 例如："这个问题可以说成XXX，这样说更自然哦"

要求：
- 只输出对话内容，不要包含任何动作描述
- 不要使用表情符号
- 保持友好、鼓励的语气
- 问题要是开放式的，引导孩子继续说下去"""
        
        messages = [HumanMessage(content=question_prompt)]
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-8-251228",
            temperature=0.85
        )
        
        feedback = str(response.content).strip()
        
        # ========== 新增：识别并记录知识点 ==========
        try:
            identify_prompt = f"""你是一个知识提取助手。请从以下孩子的回答中识别出新知识点（单词或概念）。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
孩子说：{recognized_text}

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
                
                # 记录识别到的知识点
                for kp in identify_result.get("knowledge_points", []):
                    kp_id = memory_store.add_knowledge_point(
                        child_id=state.child_name,
                        point_type=kp.get("type", "word"),
                        content=kp.get("content", ""),
                        context=f"在口语练习中学习：{recognized_text[:50]}"
                    )
                    print(f"✅ 记录新知识点：{kp.get('content', '')}")
        except Exception as e:
            print(f"⚠️ 知识点识别失败: {e}")
        
        # ========== 新增：检查是否有需要复习的知识点 ==========
        try:
            due_for_review = memory_store.get_due_for_review(state.child_name, limit=2)
            if due_for_review:
                # 暂时存储到学习进度中，供下次使用
                memory_store.update_learning_progress(state.child_name, {
                    "pending_review": due_for_review
                })
                print(f"✅ 发现{len(due_for_review)}个需要复习的知识点")
        except Exception as e:
            print(f"⚠️ 复习检查失败: {e}")
        
        # 设置下一阶段为追问
        next_stage = PracticeStage(
            stage="followup",
            current_scenario=current_scenario,
            turn_count=turn_count + 1
        )
        
    # ============== 阶段3：追问式延伸（深入话题） ==============
    elif current_stage == "followup":
        # 继续追问，控制轮数，适时总结
        if turn_count >= 3:
            # 进入反馈阶段
            feedback_prompt = f"""你是{state.child_name}的口语练习伙伴，要给孩子一个积极的总结反馈。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
当前场景：{current_scenario}
孩子的最后一句：{recognized_text}
对话轮数：{turn_count}

请给孩子一个温暖的总结：

1. **整体表扬**：总结孩子今天表现好的地方
2. **成长建议**：给出1-2个具体的改进建议（如果有）
3. **鼓励继续**：鼓励孩子下次再来练习

要求：
- 语气要温暖、真诚
- 不要包含任何动作描述
- 不要使用表情符号
- 控制在2-3句话以内"""
            
            messages = [HumanMessage(content=feedback_prompt)]
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-8-251228",
                temperature=0.7
            )
            
            feedback = str(response.content).strip()
            
            # 练习结束，不设置下一阶段
            next_stage = None
        else:
            # 继续追问
            followup_prompt = f"""你是{state.child_name}的口语练习伙伴，要继续引导孩子深入表达。

孩子姓名：{state.child_name}
孩子年龄：{state.child_age}岁
当前场景：{current_scenario}
孩子刚才说：{recognized_text}
对话轮数：{turn_count}/3

请继续用苏格拉底式提问引导孩子：

1. **肯定孩子的表达**
2. **提出新的追问**，引导孩子：
   - 描述更多细节
   - 分享更多感受
   - 联系相关经历
3. **适度纠正**（如果有错误）

要求：
- 只输出对话内容
- 不要使用表情符号
- 问题要逐步深入，但不要超出孩子的认知范围
- 如果接近3轮，要开始准备总结"""
            
            messages = [HumanMessage(content=followup_prompt)]
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-8-251228",
                temperature=0.85
            )
            
            feedback = str(response.content).strip()
            
            next_stage = PracticeStage(
                stage="followup",
                current_scenario=current_scenario,
                turn_count=turn_count + 1
            )
    
    # ============== 阶段4：反馈（传统模式） ==============
    else:
        # 传统的纠正和反馈模式
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
- 只输出对话内容，不要包含任何动作描述
- 不要使用表情符号
- 直接用文字表达你的鼓励和指导"""
        
        messages = [HumanMessage(content=feedback_prompt)]
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-8-251228",
            temperature=0.8
        )
        
        feedback = str(response.content).strip()
    
    # 更新练习次数
    new_practice_count = practice_count + 1
    memory_store.update_learning_progress(state.child_name, {
        "speaking_practice_count": new_practice_count,
        "last_practice_time": datetime.now().isoformat(),
        "last_scenario": current_scenario
    })
    
    return SpeakingPracticeOutput(
        recognized_text=recognized_text,
        corrected_text=corrected_text,
        feedback=feedback,
        practice_count=new_practice_count,
        next_stage=next_stage,
        followup_question=followup_question
    )


# ============== 节点5：实时对话节点（Agent节点，支持联网检索） ==============
def realtime_conversation_node(
    state: RealtimeConversationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RealtimeConversationOutput:
    """
    title: 实时对话（智能检索）
    desc: |
      【包含5个处理步骤】
      1. 智能判断 - 分析问题是否需要联网检索
         - 实时信息（天气、新闻、时事）→ 需要搜索
         - 具体事实（历史、科学知识）→ 需要搜索
         - 日常聊天、情感表达 → 不需要搜索
      
      2. 联网检索 - 如需搜索，调用搜索API获取信息
         - 提取搜索关键词
         - 获取搜索结果摘要
         - 整合到对话上下文
      
      3. 上下文构建 - 组合完整的对话背景
         - 对话历史（最近5轮）
         - 搜索结果（如有）
         - 作业状态信息
         - 孩子年龄和兴趣
      
      4. 智能回复生成 - 调用大语言模型生成回答
         - 使用系统提示词设定角色
         - 结合上下文生成个性化回复
         - 约束：无动作描述、无表情符号
      
      5. 作业意图识别（双LLM架构）
         - 判断孩子是否提到作业完成
         - 自动更新作业状态
         - 使用低temperature提高识别准确性
      
      【核心特性】
      - 联网检索：智能判断是否需要搜索，获取最新信息
      - 双LLM架构：一个生成内容，一个识别意图（更准确）
      - 自动作业更新：识别作业完成，自动标记状态
      - 个性化回复：结合孩子年龄、兴趣、对话历史
    integrations: 大语言模型, 联网搜索
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
    
    # ============== 新增：判断是否需要联网检索 ==============
    search_context = ""
    try:
        # 使用轻量级LLM判断是否需要联网搜索
        judgment_prompt = f"""你是一个检索需求判断助手。判断以下孩子的问题是否需要联网搜索获取最新信息。

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
- 已经有明确答案的问题

请只返回JSON格式，不要其他文字：
{{"need_search": true/false, "search_query": "搜索关键词或空字符串"}}

规则：
- need_search: 需要联网搜索设为true，否则false
- search_query: 提取搜索关键词，如果不需要搜索则为空字符串"""
        
        client = LLMClient(ctx=ctx)
        judgment_messages = [HumanMessage(content=judgment_prompt)]
        judgment_response = client.invoke(
            messages=judgment_messages,
            model="doubao-seed-1-8-251228",
            temperature=0.1
        )
        
        # 解析判断结果
        judgment_text = str(judgment_response.content).strip()
        if "{" in judgment_text and "}" in judgment_text:
            json_start = judgment_text.find("{")
            json_end = judgment_text.rfind("}") + 1
            json_str = judgment_text[json_start:json_end]
            judgment_result = json.loads(json_str)
            
            if judgment_result.get("need_search", False):
                search_query = judgment_result.get("search_query", state.user_input_text)
                
                # 调用联网搜索
                try:
                    search_client = SearchClient(ctx=ctx)
                    search_response = search_client.web_search_with_summary(
                        query=search_query,
                        count=3
                    )
                    
                    # 提取搜索摘要作为上下文
                    if search_response.summary:
                        search_context = f"\n\n联网检索信息：\n{search_response.summary}\n"
                except Exception as search_error:
                    # 搜索失败，继续正常对话
                    print(f"联网搜索失败: {search_error}")
    except Exception as e:
        # 判断失败，继续正常对话
        print(f"检索需求判断失败: {e}")
    
    # ============== 渲染用户提示词（包含时间信息和搜索上下文） ==============
    up_tpl = Template(up)
    user_prompt = up_tpl.render({
        "user_input": state.user_input_text,
        "context_info": state.context_info,
        "conversation_history": state.conversation_history[-3:] if state.conversation_history else [],
        "current_time": current_time.strftime("%H:%M"),
        "time_of_day": time_of_day,
        "current_date": current_date,
        "search_context": search_context  # 新增：搜索上下文
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
    else:
        return "实时对话"  # 默认分支
