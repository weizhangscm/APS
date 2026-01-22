"""
排程算法模块
支持正向排程、逆向排程、有限产能排程
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from collections import defaultdict

from .. import models


class SchedulingAlgorithm:
    """排程算法基类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.resource_calendar = {}  # 资源日历缓存
        self.resource_load = defaultdict(list)  # 资源负荷: {resource_id: [(start, end, op_id, product_id), ...]}
        self.setup_matrix_cache = {}  # 切换矩阵缓存
    
    def get_resource_capacity(self, resource_id: int) -> float:
        """获取资源每日产能(小时)"""
        resource = self.db.query(models.Resource).filter(models.Resource.id == resource_id).first()
        return resource.capacity_per_day if resource else 8.0
    
    def get_available_resources(self, work_center_id: int) -> List[models.Resource]:
        """获取工作中心的可用资源"""
        return self.db.query(models.Resource).filter(
            models.Resource.work_center_id == work_center_id
        ).all()
    
    def load_resource_schedule(self, start_date: datetime, end_date: datetime):
        """加载资源的已排程工序"""
        operations = self.db.query(models.Operation).filter(
            models.Operation.scheduled_start != None,
            models.Operation.scheduled_start >= start_date,
            models.Operation.scheduled_end <= end_date
        ).all()
        
        self.resource_load.clear()
        for op in operations:
            if op.resource_id:
                # 获取该工序所属订单的产品ID
                product_id = op.order.product_id if op.order else None
                self.resource_load[op.resource_id].append(
                    (op.scheduled_start, op.scheduled_end, op.id, product_id)
                )
    
    def get_last_product_on_resource(self, resource_id: int, before_time: datetime) -> Optional[int]:
        """获取资源在指定时间之前最后生产的产品ID"""
        slots = self.resource_load.get(resource_id, [])
        if not slots:
            return None
        
        # 找到在before_time之前结束的最后一个工序
        last_product_id = None
        last_end_time = None
        
        for start, end, op_id, product_id in slots:
            if end <= before_time:
                if last_end_time is None or end > last_end_time:
                    last_end_time = end
                    last_product_id = product_id
        
        return last_product_id
    
    def get_changeover_time(
        self, 
        from_product_id: Optional[int], 
        to_product_id: int, 
        resource_id: int,
        work_center_id: int
    ) -> float:
        """
        获取产品切换时间
        查找顺序: 资源级别 -> 工作中心级别 -> 全局
        """
        if from_product_id is None or from_product_id == to_product_id:
            return 0.0
        
        # 检查缓存
        cache_key = (from_product_id, to_product_id, resource_id, work_center_id)
        if cache_key in self.setup_matrix_cache:
            return self.setup_matrix_cache[cache_key]
        
        # 获取产品的切换组
        def get_setup_group_id(product_id: int, wc_id: int) -> Optional[int]:
            # 先找特定工作中心的
            assignment = self.db.query(models.ProductSetupGroup).filter(
                models.ProductSetupGroup.product_id == product_id,
                models.ProductSetupGroup.work_center_id == wc_id
            ).first()
            if assignment:
                return assignment.setup_group_id
            
            # 再找全局的
            assignment = self.db.query(models.ProductSetupGroup).filter(
                models.ProductSetupGroup.product_id == product_id,
                models.ProductSetupGroup.work_center_id == None
            ).first()
            return assignment.setup_group_id if assignment else None
        
        from_group_id = get_setup_group_id(from_product_id, work_center_id)
        to_group_id = get_setup_group_id(to_product_id, work_center_id)
        
        if not from_group_id or not to_group_id:
            self.setup_matrix_cache[cache_key] = 0.0
            return 0.0
        
        # 相同切换组
        if from_group_id == to_group_id:
            self.setup_matrix_cache[cache_key] = 0.0
            return 0.0
        
        changeover_time = 0.0
        
        # 1. 查找资源级别
        entry = self.db.query(models.SetupMatrix).filter(
            models.SetupMatrix.from_setup_group_id == from_group_id,
            models.SetupMatrix.to_setup_group_id == to_group_id,
            models.SetupMatrix.resource_id == resource_id
        ).first()
        if entry:
            changeover_time = entry.changeover_time
        else:
            # 2. 查找工作中心级别
            entry = self.db.query(models.SetupMatrix).filter(
                models.SetupMatrix.from_setup_group_id == from_group_id,
                models.SetupMatrix.to_setup_group_id == to_group_id,
                models.SetupMatrix.work_center_id == work_center_id,
                models.SetupMatrix.resource_id == None
            ).first()
            if entry:
                changeover_time = entry.changeover_time
            else:
                # 3. 查找全局
                entry = self.db.query(models.SetupMatrix).filter(
                    models.SetupMatrix.from_setup_group_id == from_group_id,
                    models.SetupMatrix.to_setup_group_id == to_group_id,
                    models.SetupMatrix.resource_id == None,
                    models.SetupMatrix.work_center_id == None
                ).first()
                if entry:
                    changeover_time = entry.changeover_time
        
        self.setup_matrix_cache[cache_key] = changeover_time
        return changeover_time
    
    def find_next_available_slot(
        self, 
        resource_id: int, 
        duration_hours: float, 
        earliest_start: datetime,
        consider_capacity: bool = True
    ) -> Tuple[datetime, datetime]:
        """
        找到资源的下一个可用时间段
        考虑有限产能约束
        """
        capacity_per_day = self.get_resource_capacity(resource_id)
        
        if not consider_capacity:
            # 无限产能模式，直接返回最早开始时间
            end_time = earliest_start + timedelta(hours=duration_hours)
            return earliest_start, end_time
        
        current_time = earliest_start
        existing_slots = sorted(self.resource_load.get(resource_id, []))
        
        # 简化算法：按天累计产能
        while True:
            day_start = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(hours=capacity_per_day)
            
            # 计算当天已用产能
            day_used = 0.0
            for slot_start, slot_end, *rest in existing_slots:
                if slot_start.date() == current_time.date():
                    day_used += (slot_end - slot_start).total_seconds() / 3600
            
            available_today = capacity_per_day - day_used
            
            if available_today >= duration_hours:
                # 当天有足够产能
                # 找到当天最后一个工序的结束时间
                last_end_today = day_start
                for slot_start, slot_end, *rest in existing_slots:
                    if slot_start.date() == current_time.date():
                        if slot_end > last_end_today:
                            last_end_today = slot_end
                
                start_time = max(last_end_today, current_time)
                if start_time < day_start:
                    start_time = day_start
                end_time = start_time + timedelta(hours=duration_hours)
                return start_time, end_time
            else:
                # 移动到下一天
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=8, minute=0, second=0, microsecond=0
                )
                
            # 防止无限循环
            if (current_time - earliest_start).days > 365:
                break
        
        # 回退到无限产能模式
        end_time = earliest_start + timedelta(hours=duration_hours)
        return earliest_start, end_time
    
    def find_latest_slot(
        self,
        resource_id: int,
        duration_hours: float,
        latest_end: datetime,
        consider_capacity: bool = True
    ) -> Tuple[datetime, datetime]:
        """
        逆向排程：从截止时间向前找可用时间段
        """
        if not consider_capacity:
            start_time = latest_end - timedelta(hours=duration_hours)
            return start_time, latest_end
        
        capacity_per_day = self.get_resource_capacity(resource_id)
        current_time = latest_end
        existing_slots = sorted(self.resource_load.get(resource_id, []), reverse=True)
        
        while True:
            day_start = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(hours=capacity_per_day)
            
            # 计算当天已用产能
            day_used = 0.0
            for slot_start, slot_end, *rest in existing_slots:
                if slot_start.date() == current_time.date():
                    day_used += (slot_end - slot_start).total_seconds() / 3600
            
            available_today = capacity_per_day - day_used
            
            if available_today >= duration_hours:
                # 当天有足够产能
                end_time = min(current_time, day_end)
                start_time = end_time - timedelta(hours=duration_hours)
                if start_time < day_start:
                    start_time = day_start
                    end_time = start_time + timedelta(hours=duration_hours)
                return start_time, end_time
            else:
                # 移动到前一天
                current_time = (current_time - timedelta(days=1)).replace(
                    hour=17, minute=0, second=0, microsecond=0
                )
            
            # 防止无限循环
            if (latest_end - current_time).days > 365:
                break
        
        start_time = latest_end - timedelta(hours=duration_hours)
        return start_time, latest_end


class ForwardScheduler(SchedulingAlgorithm):
    """正向排程算法 - 从最早开始时间向后排"""
    
    def schedule_order(
        self,
        order: models.ProductionOrder,
        consider_capacity: bool = True
    ) -> List[Dict]:
        """对单个订单进行正向排程"""
        results = []
        
        # 获取订单的所有工序
        operations = self.db.query(models.Operation).filter(
            models.Operation.order_id == order.id
        ).order_by(models.Operation.sequence).all()
        
        if not operations:
            return results
        
        # 确定最早开始时间
        earliest_start = order.earliest_start or datetime.now()
        if earliest_start < datetime.now():
            earliest_start = datetime.now()
        
        current_time = earliest_start
        current_product_id = order.product_id
        
        for operation in operations:
            # 获取工序对应的工作中心
            routing_op = operation.routing_operation
            if not routing_op:
                continue
            
            work_center_id = routing_op.work_center_id
            
            # 获取可用资源（选择第一个）
            resources = self.get_available_resources(work_center_id)
            if not resources:
                continue
            
            # 选择最佳资源（考虑负荷和切换时间）
            selected_resource = self._select_best_resource(
                resources, current_time, current_product_id, work_center_id
            )
            
            # 计算切换时间 (Setup Matrix)
            last_product_id = self.get_last_product_on_resource(selected_resource.id, current_time)
            changeover_time = self.get_changeover_time(
                last_product_id, 
                current_product_id, 
                selected_resource.id,
                work_center_id
            )
            
            # 计算工序时间 (基础时间 + 切换时间)
            duration = operation.run_time + changeover_time
            
            # 找到可用时间段
            start_time, end_time = self.find_next_available_slot(
                selected_resource.id,
                duration,
                current_time,
                consider_capacity
            )
            
            # 更新工序
            operation.resource_id = selected_resource.id
            operation.scheduled_start = start_time
            operation.scheduled_end = end_time
            operation.changeover_time = changeover_time  # 记录切换时间
            operation.status = models.OperationStatus.SCHEDULED.value
            
            # 更新资源负荷 (包含产品ID用于后续切换时间计算)
            self.resource_load[selected_resource.id].append(
                (start_time, end_time, operation.id, current_product_id)
            )
            
            # 下一工序的最早开始时间
            current_time = end_time
            
            results.append({
                'operation_id': operation.id,
                'resource_id': selected_resource.id,
                'start': start_time,
                'end': end_time,
                'changeover_time': changeover_time
            })
        
        # 更新订单状态
        order.status = models.OrderStatus.SCHEDULED.value
        
        return results
    
    def _select_best_resource(
        self, 
        resources: List[models.Resource], 
        current_time: datetime,
        product_id: Optional[int] = None,
        work_center_id: Optional[int] = None
    ) -> models.Resource:
        """
        选择最佳资源
        考虑因素: 负荷、切换时间
        """
        if len(resources) == 1:
            return resources[0]
        
        best_resource = resources[0]
        min_cost = float('inf')
        
        for resource in resources:
            # 计算当天负荷
            load = sum(
                (end - start).total_seconds() / 3600
                for start, end, *rest in self.resource_load.get(resource.id, [])
                if start.date() == current_time.date()
            )
            
            # 计算切换成本
            changeover = 0.0
            if product_id and work_center_id:
                last_product_id = self.get_last_product_on_resource(resource.id, current_time)
                changeover = self.get_changeover_time(
                    last_product_id, product_id, resource.id, work_center_id
                )
            
            # 综合成本 = 负荷 + 切换时间权重
            cost = load + changeover * 2  # 切换时间权重为2
            
            if cost < min_cost:
                min_cost = cost
                best_resource = resource
        
        return best_resource


class BackwardScheduler(SchedulingAlgorithm):
    """逆向排程算法 - 从交货期向前排"""
    
    def schedule_order(
        self,
        order: models.ProductionOrder,
        consider_capacity: bool = True
    ) -> List[Dict]:
        """对单个订单进行逆向排程"""
        results = []
        
        # 获取订单的所有工序（逆序）
        operations = self.db.query(models.Operation).filter(
            models.Operation.order_id == order.id
        ).order_by(models.Operation.sequence.desc()).all()
        
        if not operations:
            return results
        
        # 从交货期开始
        current_end = order.due_date
        current_product_id = order.product_id
        
        for operation in operations:
            routing_op = operation.routing_operation
            if not routing_op:
                continue
            
            work_center_id = routing_op.work_center_id
            resources = self.get_available_resources(work_center_id)
            if not resources:
                continue
            
            selected_resource = self._select_best_resource(
                resources, current_end, current_product_id, work_center_id
            )
            
            # 计算切换时间
            last_product_id = self.get_last_product_on_resource(selected_resource.id, current_end)
            changeover_time = self.get_changeover_time(
                last_product_id, current_product_id, selected_resource.id, work_center_id
            )
            
            duration = operation.run_time + changeover_time
            
            # 逆向找可用时间段
            start_time, end_time = self.find_latest_slot(
                selected_resource.id,
                duration,
                current_end,
                consider_capacity
            )
            
            operation.resource_id = selected_resource.id
            operation.scheduled_start = start_time
            operation.scheduled_end = end_time
            operation.changeover_time = changeover_time
            operation.status = models.OperationStatus.SCHEDULED.value
            
            self.resource_load[selected_resource.id].append(
                (start_time, end_time, operation.id, current_product_id)
            )
            
            # 前一工序的最晚结束时间
            current_end = start_time
            
            results.append({
                'operation_id': operation.id,
                'resource_id': selected_resource.id,
                'start': start_time,
                'end': end_time,
                'changeover_time': changeover_time
            })
        
        order.status = models.OrderStatus.SCHEDULED.value
        
        return results


def sort_orders_by_priority(
    orders: List[models.ProductionOrder],
    rule: str = "EDD"
) -> List[models.ProductionOrder]:
    """
    按优先级规则排序订单
    
    规则:
    - EDD: 最早交期优先 (Earliest Due Date)
    - SPT: 最短加工时间优先 (Shortest Processing Time)
    - FIFO: 先进先出
    - PRIORITY: 按优先级字段
    """
    if rule == "EDD":
        return sorted(orders, key=lambda x: x.due_date)
    elif rule == "SPT":
        # 按总加工时间排序
        def get_total_time(order):
            total = sum(op.run_time for op in order.operations) if order.operations else 0
            return total
        return sorted(orders, key=get_total_time)
    elif rule == "PRIORITY":
        return sorted(orders, key=lambda x: x.priority)
    else:  # FIFO
        return sorted(orders, key=lambda x: x.created_at)
