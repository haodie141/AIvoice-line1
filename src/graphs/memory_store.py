from typing import List, Dict, Any
from datetime import datetime


class MemoryStore:
    """内存存储类，用于管理孩子的对话历史和学习进度"""
    
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
                "speaking_practice_count": 0
            }
        return self._data[child_id]
    
    def get_conversation_history(self, child_id: str) -> List[dict]:
        """获取对话历史"""
        return self._get_child_data(child_id)["conversation_history"]
    
    def add_conversation(self, child_id: str, conversation: dict) -> None:
        """添加对话记录"""
        child_data = self._get_child_data(child_id)
        child_data["conversation_history"].append({
            **conversation,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近50条对话
        if len(child_data["conversation_history"]) > 50:
            child_data["conversation_history"] = child_data["conversation_history"][-50:]
    
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
