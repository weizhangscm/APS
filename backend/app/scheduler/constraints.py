"""
约束验证模块
用于检测排程中的冲突和约束违反
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from collections import defaultdict

from .. import models


class ConstraintViolation:
    """约束违反记录"""
    
    def __init__(
        self,
        violation_type: str,
        severity: str,  # 'error', 'warning'
        message: str,
        operation_id: int = None,
        order_id: int = None,
        resource_id: int = None,
        details: dict = None
    ):
        self.violation_type = violation_type
        self.severity = severity
        self.message = message
        self.operation_id = operation_id
        self.order_id = order_id
        self.resource_id = resource_id
        self.details = details or {}
    
    def to_dict(self) -> dict:
        return {
            'type': self.violation_type,
            'severity': self.severity,
            'message': self.message,
            'operation_id': self.operation_id,
            'order_id': self.order_id,
            'resource_id': self.resource_id,
            'details': self.details
        }


class ConstraintValidator:
    """约束验证器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.violations: List[ConstraintViolation] = []
    
    def validate_all(
        self, 
        order_ids: List[int] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[ConstraintViolation]:
        """执行所有约束验证"""
        self.violations = []
        
        # 获取要验证的订单
        query = self.db.query(models.ProductionOrder)
        if order_ids:
            query = query.filter(models.ProductionOrder.id.in_(order_ids))
        orders = query.all()
        
        # 获取已排程的工序
        op_query = self.db.query(models.Operation).filter(
            models.Operation.scheduled_start != None
        )
        if start_date:
            op_query = op_query.filter(models.Operation.scheduled_start >= start_date)
        if end_date:
            op_query = op_query.filter(models.Operation.scheduled_end <= end_date)
        operations = op_query.all()
        
        # 执行各项验证
        self._check_resource_conflicts(operations)
        self._check_sequence_constraints(orders)
        self._check_due_date_constraints(orders)
        self._check_capacity_constraints(operations)
        
        return self.violations
    
    def _check_resource_conflicts(self, operations: List[models.Operation]):
        """检查资源冲突（同一资源同一时间多个工序）"""
        # 按资源分组
        resource_ops = defaultdict(list)
        for op in operations:
            if op.resource_id and op.scheduled_start and op.scheduled_end:
                resource_ops[op.resource_id].append(op)
        
        # 检查每个资源的时间冲突
        for resource_id, ops in resource_ops.items():
            # 按开始时间排序
            sorted_ops = sorted(ops, key=lambda x: x.scheduled_start)
            
            for i in range(len(sorted_ops) - 1):
                current = sorted_ops[i]
                next_op = sorted_ops[i + 1]
                
                # 检查是否有重叠
                if current.scheduled_end > next_op.scheduled_start:
                    overlap_minutes = (current.scheduled_end - next_op.scheduled_start).total_seconds() / 60
                    
                    self.violations.append(ConstraintViolation(
                        violation_type='resource_conflict',
                        severity='error',
                        message=f'资源冲突: 工序 {current.name} 与 {next_op.name} 在资源上存在时间重叠',
                        operation_id=current.id,
                        resource_id=resource_id,
                        details={
                            'conflicting_operation_id': next_op.id,
                            'overlap_minutes': overlap_minutes,
                            'current_end': current.scheduled_end.isoformat(),
                            'next_start': next_op.scheduled_start.isoformat()
                        }
                    ))
    
    def _check_sequence_constraints(self, orders: List[models.ProductionOrder]):
        """检查工序顺序约束（前道工序必须在后道工序之前完成）"""
        for order in orders:
            operations = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.scheduled_start != None
            ).order_by(models.Operation.sequence).all()
            
            for i in range(len(operations) - 1):
                current = operations[i]
                next_op = operations[i + 1]
                
                if current.scheduled_end and next_op.scheduled_start:
                    if current.scheduled_end > next_op.scheduled_start:
                        self.violations.append(ConstraintViolation(
                            violation_type='sequence_violation',
                            severity='error',
                            message=f'顺序约束违反: 订单 {order.order_number} 的工序 {current.name} 应在 {next_op.name} 之前完成',
                            operation_id=current.id,
                            order_id=order.id,
                            details={
                                'current_sequence': current.sequence,
                                'next_sequence': next_op.sequence,
                                'current_end': current.scheduled_end.isoformat(),
                                'next_start': next_op.scheduled_start.isoformat()
                            }
                        ))
    
    def _check_due_date_constraints(self, orders: List[models.ProductionOrder]):
        """检查交货期约束"""
        for order in orders:
            # 获取最后一道工序
            last_operation = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).order_by(models.Operation.sequence.desc()).first()
            
            if last_operation and last_operation.scheduled_end:
                if last_operation.scheduled_end > order.due_date:
                    delay_hours = (last_operation.scheduled_end - order.due_date).total_seconds() / 3600
                    
                    self.violations.append(ConstraintViolation(
                        violation_type='due_date_violation',
                        severity='warning',
                        message=f'交期延误: 订单 {order.order_number} 预计延误 {delay_hours:.1f} 小时',
                        order_id=order.id,
                        details={
                            'due_date': order.due_date.isoformat(),
                            'scheduled_end': last_operation.scheduled_end.isoformat(),
                            'delay_hours': delay_hours
                        }
                    ))
    
    def _check_capacity_constraints(self, operations: List[models.Operation]):
        """检查产能约束（每日产能是否超载）"""
        # 按资源和日期分组计算负荷
        daily_load = defaultdict(lambda: defaultdict(float))
        
        for op in operations:
            if op.resource_id and op.scheduled_start and op.scheduled_end:
                # 简化：假设工序不跨天
                date_key = op.scheduled_start.date()
                duration = (op.scheduled_end - op.scheduled_start).total_seconds() / 3600
                daily_load[op.resource_id][date_key] += duration
        
        # 检查每个资源每天的负荷
        for resource_id, date_loads in daily_load.items():
            resource = self.db.query(models.Resource).filter(
                models.Resource.id == resource_id
            ).first()
            
            if not resource:
                continue
            
            capacity = resource.capacity_per_day
            
            for date, load in date_loads.items():
                if load > capacity:
                    overload_percent = ((load - capacity) / capacity) * 100
                    
                    self.violations.append(ConstraintViolation(
                        violation_type='capacity_overload',
                        severity='warning',
                        message=f'产能超载: 资源 {resource.name} 在 {date} 超载 {overload_percent:.1f}%',
                        resource_id=resource_id,
                        details={
                            'date': str(date),
                            'load_hours': load,
                            'capacity_hours': capacity,
                            'overload_percent': overload_percent
                        }
                    ))
    
    def check_operation_move(
        self,
        operation_id: int,
        new_start: datetime,
        new_resource_id: int = None
    ) -> List[ConstraintViolation]:
        """检查工序移动是否违反约束"""
        violations = []
        
        operation = self.db.query(models.Operation).filter(
            models.Operation.id == operation_id
        ).first()
        
        if not operation:
            violations.append(ConstraintViolation(
                violation_type='not_found',
                severity='error',
                message='工序不存在',
                operation_id=operation_id
            ))
            return violations
        
        resource_id = new_resource_id or operation.resource_id
        duration = operation.run_time
        new_end = new_start + timedelta(hours=duration)
        
        # 检查与同资源其他工序的冲突
        other_ops = self.db.query(models.Operation).filter(
            models.Operation.resource_id == resource_id,
            models.Operation.id != operation_id,
            models.Operation.scheduled_start != None
        ).all()
        
        for other in other_ops:
            if new_start < other.scheduled_end and new_end > other.scheduled_start:
                violations.append(ConstraintViolation(
                    violation_type='resource_conflict',
                    severity='error',
                    message=f'移动将导致与工序 {other.name} 冲突',
                    operation_id=operation_id,
                    resource_id=resource_id,
                    details={
                        'conflicting_operation_id': other.id
                    }
                ))
        
        # 检查工序顺序约束
        order = operation.order
        if order:
            # 前道工序
            prev_ops = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.sequence < operation.sequence,
                models.Operation.scheduled_end != None
            ).all()
            
            for prev in prev_ops:
                if prev.scheduled_end > new_start:
                    violations.append(ConstraintViolation(
                        violation_type='sequence_violation',
                        severity='error',
                        message=f'移动将违反与前道工序 {prev.name} 的顺序约束',
                        operation_id=operation_id,
                        details={
                            'prev_operation_id': prev.id
                        }
                    ))
            
            # 后道工序
            next_ops = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.sequence > operation.sequence,
                models.Operation.scheduled_start != None
            ).all()
            
            for next_op in next_ops:
                if new_end > next_op.scheduled_start:
                    violations.append(ConstraintViolation(
                        violation_type='sequence_violation',
                        severity='error',
                        message=f'移动将违反与后道工序 {next_op.name} 的顺序约束',
                        operation_id=operation_id,
                        details={
                            'next_operation_id': next_op.id
                        }
                    ))
        
        return violations
