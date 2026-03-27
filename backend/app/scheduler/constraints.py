"""
约束验证模块
用于检测排程中的冲突和约束违反
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session
from collections import defaultdict

from .. import models
from ..datetime_compat import to_naive_utc


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

    def _eff_schedule(
        self,
        op: models.Operation,
        schedule_overlay: Optional[Dict[int, Any]],
    ) -> Tuple[Optional[datetime], Optional[datetime], Optional[int]]:
        """当前生效的排程（未保存缓存优先，否则数据库）。"""
        if schedule_overlay and op.id in schedule_overlay:
            c = schedule_overlay[op.id]
            return c.scheduled_start, c.scheduled_end, c.resource_id
        return op.scheduled_start, op.scheduled_end, op.resource_id

    def check_operation_move(
        self,
        operation_id: int,
        new_start: datetime,
        new_resource_id: int = None,
        schedule_overlay: Optional[Dict[int, Any]] = None,
    ) -> List[ConstraintViolation]:
        """检查工序移动是否违反约束。schedule_overlay：预览缓存 operation_id -> CachedOperation。"""
        violations = []
        new_start = to_naive_utc(new_start)
        if new_start is None:
            violations.append(ConstraintViolation(
                violation_type='invalid_time',
                severity='error',
                message='新的开始时间无效',
                operation_id=operation_id
            ))
            return violations

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

        if operation.run_time is None:
            violations.append(ConstraintViolation(
                violation_type='missing_runtime',
                severity='error',
                message='工序运行时间未维护，无法调整排程',
                operation_id=operation_id
            ))
            return violations

        eff_start, eff_end, eff_res = self._eff_schedule(operation, schedule_overlay)
        if eff_start is None:
            violations.append(ConstraintViolation(
                violation_type='unscheduled_operation',
                severity='error',
                message='工序尚未排程，无法通过拖拽调整',
                operation_id=operation_id,
                order_id=operation.order_id
            ))
            return violations
        
        target_res = new_resource_id if new_resource_id is not None else eff_res
        duration = operation.run_time
        new_end = new_start + timedelta(hours=duration)
        order = operation.order

        if new_resource_id is not None and new_resource_id != eff_res:
            violations.extend(
                self._cross_resource_violations(operation, new_resource_id)
            )
            if any(v.severity == 'error' for v in violations):
                return violations
        
        successor_ids: List[int] = []
        if order:
            for s in self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.sequence > operation.sequence,
            ).all():
                if self._eff_schedule(s, schedule_overlay)[0] is not None:
                    successor_ids.append(s.id)

        candidate_ids = set()
        for row in self.db.query(models.Operation.id).filter(
            models.Operation.scheduled_start != None
        ).all():
            candidate_ids.add(row[0])
        if schedule_overlay:
            candidate_ids |= set(schedule_overlay.keys())

        for oid in candidate_ids:
            o = self.db.query(models.Operation).filter(models.Operation.id == oid).first()
            if not o:
                continue
            os_t, oe_t, ors = self._eff_schedule(o, schedule_overlay)
            if os_t is None or oe_t is None or ors is None:
                continue
            if ors != target_res:
                continue
            if oid == operation_id:
                continue
            if oid in successor_ids:
                continue
            if new_start < oe_t and new_end > os_t:
                violations.append(ConstraintViolation(
                    violation_type='resource_conflict',
                    severity='error',
                    message=f'移动将导致与工序 {o.name} 冲突',
                    operation_id=operation_id,
                    resource_id=target_res,
                    details={'conflicting_operation_id': o.id}
                ))
        
        if order:
            prev_ops = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.sequence < operation.sequence,
            ).all()
            
            for prev in prev_ops:
                _, peff, _ = self._eff_schedule(prev, schedule_overlay)
                if peff is None:
                    continue
                if peff > new_start:
                    violations.append(ConstraintViolation(
                        violation_type='sequence_violation',
                        severity='error',
                        message=f'移动将违反与前道工序 {prev.name} 的顺序约束',
                        operation_id=operation_id,
                        details={'prev_operation_id': prev.id}
                    ))
            
            offset = new_start - eff_start
            next_ops = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.sequence > operation.sequence,
            ).all()
            
            for next_op in next_ops:
                ns, _, _ = self._eff_schedule(next_op, schedule_overlay)
                if ns is None:
                    continue
                projected_next_start = ns + offset
                if new_end > projected_next_start:
                    violations.append(ConstraintViolation(
                        violation_type='sequence_violation',
                        severity='error',
                        message=f'移动将违反与后道工序 {next_op.name} 的顺序约束',
                        operation_id=operation_id,
                        details={'next_operation_id': next_op.id}
                    ))
        
        return violations

    def _cross_resource_violations(
        self,
        operation: models.Operation,
        new_resource_id: int
    ) -> List[ConstraintViolation]:
        """拖拽改资源：仅允许与工艺路线指定资源同一工作中心下的资源。"""
        out: List[ConstraintViolation] = []
        ro = operation.routing_operation
        if not ro:
            out.append(ConstraintViolation(
                violation_type='invalid_resource',
                severity='error',
                message='工序缺少工艺路线定义，无法更换资源',
                operation_id=operation.id,
                resource_id=new_resource_id
            ))
            return out
        new_res = self.db.query(models.Resource).filter(
            models.Resource.id == new_resource_id
        ).first()
        if not new_res:
            out.append(ConstraintViolation(
                violation_type='invalid_resource',
                severity='error',
                message='目标资源不存在',
                operation_id=operation.id,
                resource_id=new_resource_id
            ))
            return out
        allowed = False
        if ro.resource_id:
            ref = self.db.query(models.Resource).filter(
                models.Resource.id == ro.resource_id
            ).first()
            if ref and ref.work_center_id is not None and new_res.work_center_id is not None:
                allowed = ref.work_center_id == new_res.work_center_id
            elif ro.resource_id == new_resource_id:
                allowed = True
        elif ro.work_center_id is not None and new_res.work_center_id is not None:
            allowed = ro.work_center_id == new_res.work_center_id
        if not allowed:
            out.append(ConstraintViolation(
                violation_type='invalid_resource',
                severity='error',
                message='目标资源与工艺路线资源不在同一工作中心，不允许拖拽到该资源',
                operation_id=operation.id,
                resource_id=new_resource_id,
                details={'routing_operation_id': ro.id}
            ))
        return out

    def check_whole_order_shift(
        self,
        operation_id: int,
        new_start: datetime,
        new_resource_id: int = None,
        schedule_overlay: Optional[Dict[int, Any]] = None,
    ) -> List[ConstraintViolation]:
        """整单已排程工序同一时间平移（锚点工序可换资源），用于 Shift+拖拽。"""
        violations: List[ConstraintViolation] = []
        new_start = to_naive_utc(new_start)
        if new_start is None:
            violations.append(ConstraintViolation(
                violation_type='invalid_time',
                severity='error',
                message='新的开始时间无效',
                operation_id=operation_id
            ))
            return violations

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
        if operation.run_time is None:
            violations.append(ConstraintViolation(
                violation_type='missing_runtime',
                severity='error',
                message='工序运行时间未维护，无法调整排程',
                operation_id=operation_id
            ))
            return violations
        eff_start, _, eff_res = self._eff_schedule(operation, schedule_overlay)
        if eff_start is None:
            violations.append(ConstraintViolation(
                violation_type='unscheduled_operation',
                severity='error',
                message='工序尚未排程，无法通过拖拽调整',
                operation_id=operation_id,
                order_id=operation.order_id
            ))
            return violations
        order = operation.order
        if not order:
            return violations

        delta = new_start - eff_start
        order_ops = self.db.query(models.Operation).filter(
            models.Operation.order_id == order.id
        ).order_by(models.Operation.sequence).all()
        scheduled_ops = [
            op for op in order_ops
            if self._eff_schedule(op, schedule_overlay)[0] is not None
            and self._eff_schedule(op, schedule_overlay)[1] is not None
        ]
        if not scheduled_ops:
            return violations

        moving_ids = {op.id for op in scheduled_ops}
        projections: List[tuple] = []
        for op in scheduled_ops:
            es, ee, er = self._eff_schedule(op, schedule_overlay)
            if op.id == operation.id:
                res = new_resource_id if new_resource_id is not None else er
                ps = new_start
                pe = new_start + timedelta(hours=op.run_time)
            else:
                res = er
                ps = es + delta
                pe = ee + delta
            projections.append((op, ps, pe, res))

        if new_resource_id is not None and new_resource_id != eff_res:
            violations.extend(self._cross_resource_violations(operation, new_resource_id))
            if any(v.severity == 'error' for v in violations):
                return violations

        projections.sort(key=lambda x: x[0].sequence)
        for i in range(len(projections) - 1):
            _, _, e1, _ = projections[i]
            _, s2, _, _ = projections[i + 1]
            if e1 > s2:
                violations.append(ConstraintViolation(
                    violation_type='sequence_violation',
                    severity='error',
                    message=f'平移后将违反工序顺序：{projections[i][0].name} 与 {projections[i + 1][0].name}',
                    operation_id=operation_id,
                    order_id=order.id
                ))
                break

        all_ids = set()
        for row in self.db.query(models.Operation.id).filter(
            models.Operation.scheduled_start != None
        ).all():
            all_ids.add(row[0])
        if schedule_overlay:
            all_ids |= set(schedule_overlay.keys())

        for op, ps, pe, res_id in projections:
            if res_id is None:
                continue
            for oid in all_ids:
                if oid == op.id:
                    continue
                o = self.db.query(models.Operation).filter(models.Operation.id == oid).first()
                if not o:
                    continue
                if o.order_id == order.id and oid in moving_ids:
                    continue
                os_t, oe_t, ors = self._eff_schedule(o, schedule_overlay)
                if os_t is None or oe_t is None or ors is None:
                    continue
                if ors != res_id:
                    continue
                if ps < oe_t and pe > os_t:
                    violations.append(ConstraintViolation(
                        violation_type='resource_conflict',
                        severity='error',
                        message=f'整单平移将导致工序 {op.name} 与 {o.name} 在资源上冲突',
                        operation_id=op.id,
                        resource_id=res_id,
                        details={'conflicting_operation_id': o.id}
                    ))

        return violations
