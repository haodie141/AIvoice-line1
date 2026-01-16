from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


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
                "homework_list": []  # 作业列表，包含时间信息
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
    
    def clear_child_data(self, child_id: str) -> None:
        """清除孩子所有数据"""
        if child_id in self._data:
            del self._data[child_id]
