# -*- coding: utf-8 -*-
"""
排程缓存管理器

用于存储临时排程结果，支持预览模式：
- 运行启发式/重新计划时，结果存入缓存，不写入数据库
- 点击"保存计划"时，将缓存数据写入数据库
- 点击"丢弃计划"或刷新时，清除缓存
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading


@dataclass
class CachedOperation:
    """缓存的工序排程数据"""
    operation_id: int
    order_id: int
    resource_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    changeover_time: float = 0
    status: str = 'scheduled'


@dataclass
class CachedScheduleResult:
    """缓存的排程结果"""
    created_at: datetime = field(default_factory=datetime.now)
    operations: Dict[int, CachedOperation] = field(default_factory=dict)  # operation_id -> CachedOperation
    affected_order_ids: List[int] = field(default_factory=list)
    message: str = ""
    
    def add_operation(self, op: CachedOperation):
        """添加工序到缓存"""
        self.operations[op.operation_id] = op
        if op.order_id not in self.affected_order_ids:
            self.affected_order_ids.append(op.order_id)
    
    def get_operation(self, operation_id: int) -> Optional[CachedOperation]:
        """获取缓存的工序"""
        return self.operations.get(operation_id)
    
    def clear(self):
        """清除缓存"""
        self.operations.clear()
        self.affected_order_ids.clear()
        self.message = ""


class ScheduleCache:
    """
    排程缓存单例
    
    使用内存存储临时排程结果，支持多用户（通过session_id区分）
    简化版：单用户模式，全局缓存
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = CachedScheduleResult()
                    cls._instance._has_unsaved_changes = False
        return cls._instance
    
    @property
    def has_unsaved_changes(self) -> bool:
        """是否有未保存的更改"""
        return self._has_unsaved_changes
    
    @property
    def cache(self) -> CachedScheduleResult:
        """获取缓存"""
        return self._cache
    
    def set_schedule(self, operations: List[CachedOperation], message: str = "", merge: bool = True):
        """
        设置排程缓存
        
        Args:
            operations: 要缓存的工序列表
            message: 操作消息
            merge: 是否合并到现有缓存（True=合并，False=替换）
        """
        if not merge or not self._has_unsaved_changes:
            # 替换模式：创建新缓存
            self._cache = CachedScheduleResult(message=message)
        else:
            # 合并模式：保留现有缓存，更新消息
            self._cache.message = message
        
        for op in operations:
            self._cache.add_operation(op)
        self._has_unsaved_changes = True
    
    def add_operation(self, op: CachedOperation):
        """添加单个工序到缓存"""
        self._cache.add_operation(op)
        self._has_unsaved_changes = True
    
    def get_operation(self, operation_id: int) -> Optional[CachedOperation]:
        """获取缓存的工序"""
        return self._cache.get_operation(operation_id)
    
    def get_all_operations(self) -> List[CachedOperation]:
        """获取所有缓存的工序"""
        return list(self._cache.operations.values())
    
    def get_affected_order_ids(self) -> List[int]:
        """获取受影响的订单ID"""
        return self._cache.affected_order_ids
    
    def clear(self):
        """清除缓存"""
        self._cache.clear()
        self._has_unsaved_changes = False
    
    def mark_saved(self):
        """标记为已保存"""
        self._has_unsaved_changes = False
        self._cache.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            'has_unsaved_changes': self._has_unsaved_changes,
            'cached_operations': len(self._cache.operations),
            'affected_orders': len(self._cache.affected_order_ids),
            'message': self._cache.message,
            'created_at': self._cache.created_at.isoformat() if self._cache.created_at else None
        }


# 全局缓存实例
schedule_cache = ScheduleCache()
