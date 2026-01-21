from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random


class MemoryStore:
    """内存存储类，用于管理孩子的对话历史、作业和学习进度（支持时间感知）"""
    
    _instance = None
    _data: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls) -> 'MemoryStore':
        if cls._instance is None:
            cls._instance = super(MemoryStore, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化（由于单例模式，实际只会在第一次创建时调用）"""
        if not hasattr(self, 'initialized'):
            self._data: Dict[str, Dict[str, Any]] = {}
            self._short_cache: Dict[str, Dict[str, Any]] = {}  # 短期缓存（1-2分钟）
            self.initialized = True
    
    @classmethod
    def get_instance(cls) -> 'MemoryStore':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _get_child_data(self, child_id: str) -> Dict[str, Any]:
        """获取孩子的数据"""
        if child_id not in self._data:
            self._data[child_id] = {
                "conversation_history": [],
                "learning_progress": {},
                "speaking_practice_count": 0,
                "homework_list": [],  # 作业列表，包含时间信息
                "knowledge_points": []  # 知识点列表（长期记忆）
            }
        return self._data[child_id]
    
    def get_conversation_history(self, child_id: str) -> List[dict]:
        """获取对话历史"""
        return self._get_child_data(child_id)["conversation_history"]
    
    def get_conversation_history_by_time_range(
        self, 
        child_id: str, 
        days: int = 7
    ) -> List[dict]:
        """获取指定天数范围内的对话历史"""
        now = datetime.now()
        cutoff_time = now - timedelta(days=days)
        
        history = self._get_child_data(child_id)["conversation_history"]
        filtered = []
        
        for conv in history:
            timestamp_str = conv.get("timestamp", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= cutoff_time:
                        filtered.append(conv)
                except (ValueError, TypeError):
                    # 时间戳解析失败，仍然保留（向后兼容）
                    filtered.append(conv)
        
        return filtered
    
    def add_conversation(self, child_id: str, conversation: dict) -> None:
        """添加对话记录（自动添加时间戳）"""
        child_data = self._get_child_data(child_id)
        child_data["conversation_history"].append({
            **conversation,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近100条对话（增加容量以支持更长的历史）
        if len(child_data["conversation_history"]) > 100:
            child_data["conversation_history"] = child_data["conversation_history"][-100:]
    
    def add_homework(
        self, 
        child_id: str, 
        subject: str, 
        description: str,
        deadline_days: int = 1
    ) -> str:
        """
        添加作业（自动计算截止时间）
        
        Args:
            child_id: 孩子ID
            subject: 学科
            description: 作业描述
            deadline_days: 截止天数（默认1天）
        
        Returns:
            作业ID
        """
        child_data = self._get_child_data(child_id)
        
        # 生成作业ID
        homework_id = f"hw_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(child_data['homework_list'])}"
        
        # 计算截止时间
        deadline = datetime.now() + timedelta(days=deadline_days)
        
        homework = {
            "id": homework_id,
            "subject": subject,
            "description": description,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "deadline": deadline.isoformat(),
            "deadline_days": deadline_days
        }
        
        child_data["homework_list"].append(homework)
        return homework_id
    
    def get_homework_list(self, child_id: str) -> List[dict]:
        """获取作业列表"""
        return self._get_child_data(child_id)["homework_list"]
    
    def get_valid_homework(self, child_id: str) -> List[dict]:
        """
        获取有效的作业（未过期且未完成）
        过期作业不会被返回
        """
        now = datetime.now()
        homework_list = self._get_child_data(child_id)["homework_list"]
        valid_homework = []
        
        for hw in homework_list:
            # 跳过已完成的作业
            if hw.get("completed", False):
                continue
            
            # 检查是否过期
            deadline_str = hw.get("deadline", "")
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str)
                    if deadline < now:
                        # 作业已过期，跳过
                        continue
                except (ValueError, TypeError):
                    # 时间戳解析失败，视为有效（向后兼容）
                    pass
            
            valid_homework.append(hw)
        
        return valid_homework
    
    def complete_homework(self, child_id: str, homework_id: str) -> bool:
        """标记作业为已完成"""
        child_data = self._get_child_data(child_id)
        
        for hw in child_data["homework_list"]:
            if hw.get("id") == homework_id:
                hw["completed"] = True
                hw["completed_at"] = datetime.now().isoformat()
                return True
        
        return False
    
    def get_learning_progress(self, child_id: str) -> Dict[str, Any]:
        """获取学习进度"""
        return self._get_child_data(child_id)["learning_progress"]
    
    def update_learning_progress(self, child_id: str, progress: Dict[str, Any]) -> None:
        """更新学习进度"""
        child_data = self._get_child_data(child_id)
        child_data["learning_progress"].update(progress)
    
    def get_speaking_practice_count(self, child_id: str) -> int:
        """获取口语练习次数"""
        return self._get_child_data(child_id)["speaking_practice_count"]
    
    def update_speaking_practice_count(self, child_id: str, count: int) -> None:
        """更新口语练习次数"""
        self._get_child_data(child_id)["speaking_practice_count"] = count
    
    # ============== 知识追踪和间隔重复系统 ==============
    
    def add_knowledge_point(
        self, 
        child_id: str, 
        point_type: str, 
        content: str,
        context: str = ""
    ) -> str:
        """
        添加知识点（长期记忆）
        
        Args:
            child_id: 孩子ID
            point_type: 知识点类型（word/concept/skill）
            content: 知识点内容
            context: 学习上下文
        
        Returns:
            知识点ID
        """
        child_data = self._get_child_data(child_id)
        
        # 检查是否已存在相同知识点
        for kp in child_data["knowledge_points"]:
            if kp.get("content", "").lower() == content.lower():
                return kp["id"]
        
        # 生成知识点ID
        kp_id = f"kp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(child_data['knowledge_points'])}"
        
        # 计算首次复习时间（10分钟后）
        first_review_time = datetime.now() + timedelta(minutes=10)
        
        knowledge_point = {
            "id": kp_id,
            "type": point_type,
            "content": content,
            "context": context,
            "mastery_level": 0,  # 掌握程度 0-5
            "learned_at": datetime.now().isoformat(),
            "next_review_time": first_review_time.isoformat(),
            "review_count": 0,
            "correct_count": 0,
            "is_due": False
        }
        
        child_data["knowledge_points"].append(knowledge_point)
        return kp_id
    
    def update_knowledge_mastery(
        self, 
        child_id: str, 
        knowledge_id: str, 
        is_correct: bool
    ) -> Optional[Dict[str, Any]]:
        """
        更新知识点掌握程度（基于简化版SM-2算法）
        
        Args:
            child_id: 孩子ID
            knowledge_id: 知识点ID
            is_correct: 是否回答正确
        
        Returns:
            更新后的知识点，如果不存在则返回None
        """
        child_data = self._get_child_data(child_id)
        
        for kp in child_data["knowledge_points"]:
            if kp["id"] == knowledge_id:
                kp["review_count"] += 1
                
                if is_correct:
                    kp["correct_count"] += 1
                    # 正确，提高掌握程度
                    if kp["mastery_level"] < 5:
                        kp["mastery_level"] += 1
                else:
                    # 错误，降低掌握程度（但不低于1）
                    if kp["mastery_level"] > 1:
                        kp["mastery_level"] -= 1
                
                # 计算下次复习时间（基于掌握程度）
                kp["next_review_time"] = self._calculate_next_review(
                    kp["mastery_level"],
                    kp["review_count"]
                ).isoformat()
                
                return kp
        
        return None
    
    def _calculate_next_review(
        self, 
        mastery_level: int, 
        review_count: int
    ) -> datetime:
        """
        计算下次复习时间（简化版间隔重复算法）
        
        Args:
            mastery_level: 掌握程度 0-5
            review_count: 复习次数
        
        Returns:
            下次复习时间
        """
        # 间隔时间表（根据掌握程度）
        intervals = {
            0: timedelta(minutes=10),    # 刚学习：10分钟后
            1: timedelta(hours=1),      # 初步掌握：1小时后
            2: timedelta(days=1),       # 熟悉：1天后
            3: timedelta(days=3),       # 掌握：3天后
            4: timedelta(days=7),       # 熟练：7天后
            5: timedelta(days=14)       # 精通：14天后
        }
        
        # 获取基础间隔
        base_interval = intervals.get(mastery_level, timedelta(days=1))
        
        # 添加随机波动（±20%），避免所有知识点在同一时间复习
        random_factor = random.uniform(0.8, 1.2)
        actual_interval = timedelta(
            seconds=int(base_interval.total_seconds() * random_factor)
        )
        
        return datetime.now() + actual_interval
    
    def get_due_for_review(
        self, 
        child_id: str, 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取需要复习的知识点
        
        Args:
            child_id: 孩子ID
            limit: 最多返回数量
        
        Returns:
            需要复习的知识点列表
        """
        now = datetime.now()
        child_data = self._get_child_data(child_id)
        due_points = []
        
        for kp in child_data.get("knowledge_points", []):
            # 检查是否到期
            next_review_str = kp.get("next_review_time", "")
            if not next_review_str:
                continue
            
            try:
                next_review = datetime.fromisoformat(next_review_str)
                if next_review <= now:
                    # 到期，添加到列表
                    due_points.append({
                        **kp,
                        "is_due": True
                    })
            except (ValueError, TypeError):
                continue
        
        # 按到期时间排序
        due_points.sort(key=lambda x: x.get("next_review_time", ""))
        
        # 限制返回数量
        return due_points[:limit]
    
    def get_knowledge_point_by_content(
        self, 
        child_id: str, 
        content: str
    ) -> Optional[Dict[str, Any]]:
        """
        根据内容查找知识点
        
        Args:
            child_id: 孩子ID
            content: 知识点内容
        
        Returns:
            知识点字典，如果不存在则返回None
        """
        child_data = self._get_child_data(child_id)
        
        for kp in child_data.get("knowledge_points", []):
            if kp.get("content", "").lower() == content.lower():
                return kp
        
        return None
    
    def get_all_knowledge_points(self, child_id: str) -> List[Dict[str, Any]]:
        """获取所有知识点"""
        return self._get_child_data(child_id).get("knowledge_points", [])
    
    def get_knowledge_statistics(self, child_id: str) -> Dict[str, Any]:
        """获取知识点统计信息"""
        knowledge_points = self.get_all_knowledge_points(child_id)
        
        total = len(knowledge_points)
        if total == 0:
            return {
                "total": 0,
                "mastered": 0,
                "learning": 0,
                "need_review": 0
            }
        
        mastered = sum(1 for kp in knowledge_points if kp.get("mastery_level", 0) >= 4)
        learning = sum(1 for kp in knowledge_points if 2 <= kp.get("mastery_level", 0) < 4)
        need_review = len(self.get_due_for_review(child_id, limit=100))

    # ============== 短期缓存系统（v2.0优化） ==============
    
    def _get_cache_key(self, scenario: str, query: str) -> str:
        """生成缓存键"""
        import hashlib
        key_str = f"{scenario}:{query.lower().strip()}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cached_response(
        self, 
        scenario: str, 
        query: str,
        cache_duration: int = 90
    ) -> Optional[str]:
        """
        获取缓存的响应
        
        Args:
            scenario: 场景类型（如quick_reply, quick_chat）
            query: 用户输入
            cache_duration: 缓存时长（秒），默认90秒（1.5分钟）
        
        Returns:
            缓存的响应，如果过期或不存在则返回None
        """
        cache_key = self._get_cache_key(scenario, query)
        cached_item = self._short_cache.get(cache_key)
        
        if not cached_item:
            return None
        
        # 检查缓存是否过期
        cached_time_str = cached_item.get("timestamp", "")
        if not cached_time_str:
            return None
        
        try:
            cached_time = datetime.fromisoformat(cached_time_str)
            now = datetime.now()
            
            if (now - cached_time).total_seconds() > cache_duration:
                # 缓存过期，删除
                del self._short_cache[cache_key]
                return None
            
            # 返回缓存的响应
            return cached_item.get("response")
        except (ValueError, TypeError):
            return None
    
    def cache_response(
        self, 
        scenario: str, 
        query: str, 
        response: str
    ) -> None:
        """
        缓存响应
        
        Args:
            scenario: 场景类型
            query: 用户输入
            response: 响应内容
        """
        cache_key = self._get_cache_key(scenario, query)
        
        self._short_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "query": query
        }
        
        # 限制缓存大小（最多1000条）
        if len(self._short_cache) > 1000:
            # 删除最旧的缓存（按时间排序）
            sorted_items = sorted(
                self._short_cache.items(),
                key=lambda x: x[1].get("timestamp", "")
            )
            # 删除最旧的10%
            remove_count = len(sorted_items) // 10
            for key, _ in sorted_items[:remove_count]:
                del self._short_cache[key]
    
    def clear_expired_cache(self, max_age_seconds: int = 180) -> int:
        """
        清理过期缓存
        
        Args:
            max_age_seconds: 最大缓存时长（秒），默认180秒（3分钟）
        
        Returns:
            删除的缓存数量
        """
        now = datetime.now()
        remove_count = 0
        expired_keys = []
        
        for cache_key, cache_item in self._short_cache.items():
            timestamp_str = cache_item.get("timestamp", "")
            if not timestamp_str:
                continue
            
            try:
                cached_time = datetime.fromisoformat(timestamp_str)
                if (now - cached_time).total_seconds() > max_age_seconds:
                    expired_keys.append(cache_key)
            except (ValueError, TypeError):
                continue
        
        # 删除过期缓存
        for key in expired_keys:
            del self._short_cache[key]
            remove_count += 1
        
        return remove_count
    
    def record_homework_check(self, child_id: str) -> None:
        """记录作业检查时间（用于降频机制）"""
        child_data = self._get_child_data(child_id)
        child_data["last_homework_check"] = datetime.now().isoformat()
    
    def get_last_homework_check(self, child_id: str) -> Optional[datetime]:
        """获取最后检查作业的时间"""
        child_data = self._get_child_data(child_id)
        last_check_str = child_data.get("last_homework_check", "")
        
        if not last_check_str:
            return None
        
        try:
            return datetime.fromisoformat(last_check_str)
        except (ValueError, TypeError):
            return None
        
        return {
            "total": total,
            "mastered": mastered,
            "learning": learning,
            "need_review": need_review
        }
    
    def clear_child_data(self, child_id: str) -> None:
        """清除孩子所有数据"""
        if child_id in self._data:
            del self._data[child_id]
