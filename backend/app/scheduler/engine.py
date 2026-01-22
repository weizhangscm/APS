"""
排程引擎主模块
协调排程算法和约束验证
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from .. import models, schemas
from .algorithms import ForwardScheduler, BackwardScheduler, sort_orders_by_priority
from .constraints import ConstraintValidator


class SchedulingEngine:
    """排程引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = ConstraintValidator(db)
    
    def run_scheduling(
        self,
        order_ids: List[int] = None,
        direction: str = "forward",
        consider_capacity: bool = True,
        priority_rule: str = "EDD"
    ) -> schemas.SchedulingResult:
        """
        执行排程
        
        Args:
            order_ids: 要排程的订单ID列表，None表示所有待排订单
            direction: 排程方向 - "forward"(正向) 或 "backward"(逆向)
            consider_capacity: 是否考虑有限产能
            priority_rule: 优先级规则 - EDD, SPT, FIFO, PRIORITY
        
        Returns:
            排程结果
        """
        # 获取要排程的订单 - 只排程计划订单，不排程生产订单
        query = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,  # 只排程计划订单
            models.ProductionOrder.status.in_([
                models.OrderStatus.CREATED.value,
                models.OrderStatus.SCHEDULED.value
            ])
        )
        
        if order_ids:
            query = query.filter(models.ProductionOrder.id.in_(order_ids))
        
        orders = query.all()
        
        if not orders:
            return schemas.SchedulingResult(
                success=True,
                message="没有需要排程的订单",
                scheduled_orders=0,
                scheduled_operations=0,
                conflicts=[]
            )
        
        # 按优先级排序
        sorted_orders = sort_orders_by_priority(orders, priority_rule)
        
        # 选择排程算法
        if direction == "backward":
            scheduler = BackwardScheduler(self.db)
        else:
            scheduler = ForwardScheduler(self.db)
        
        # 加载现有排程（用于有限产能计算）
        if consider_capacity:
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now() + timedelta(days=90)
            scheduler.load_resource_schedule(start_date, end_date)
        
        # 执行排程
        scheduled_orders = 0
        scheduled_operations = 0
        
        for order in sorted_orders:
            try:
                results = scheduler.schedule_order(order, consider_capacity)
                if results:
                    scheduled_orders += 1
                    scheduled_operations += len(results)
            except Exception as e:
                print(f"排程订单 {order.order_number} 失败: {str(e)}")
        
        # 提交更改
        self.db.commit()
        
        # 验证约束
        violations = self.validator.validate_all(
            order_ids=[o.id for o in sorted_orders]
        )
        
        conflicts = [v.to_dict() for v in violations]
        
        return schemas.SchedulingResult(
            success=True,
            message=f"排程完成，共排程 {scheduled_orders} 个订单，{scheduled_operations} 道工序",
            scheduled_orders=scheduled_orders,
            scheduled_operations=scheduled_operations,
            conflicts=conflicts
        )
    
    def reschedule_operation(
        self,
        operation_id: int,
        new_start: datetime,
        new_resource_id: int = None
    ) -> Dict:
        """
        重新排程单个工序（用于拖拽调整）
        
        Args:
            operation_id: 工序ID
            new_start: 新的开始时间
            new_resource_id: 新的资源ID（可选）
        
        Returns:
            包含成功状态和冲突信息的字典
        """
        operation = self.db.query(models.Operation).filter(
            models.Operation.id == operation_id
        ).first()
        
        if not operation:
            return {
                'success': False,
                'message': '工序不存在',
                'conflicts': []
            }
        
        # 检查订单类型 - 生产订单不允许调整
        order = operation.order
        if order and order.order_type == models.OrderType.PRODUCTION.value:
            return {
                'success': False,
                'message': '生产订单已确认，不允许调整排程',
                'conflicts': []
            }
        
        # 检查约束
        violations = self.validator.check_operation_move(
            operation_id,
            new_start,
            new_resource_id
        )
        
        # 如果有错误级别的违反，不允许移动
        errors = [v for v in violations if v.severity == 'error']
        if errors:
            return {
                'success': False,
                'message': '移动违反约束',
                'conflicts': [v.to_dict() for v in violations]
            }
        
        # 更新工序
        duration = operation.run_time
        new_end = new_start + timedelta(hours=duration)
        
        operation.scheduled_start = new_start
        operation.scheduled_end = new_end
        
        if new_resource_id:
            operation.resource_id = new_resource_id
        
        self.db.commit()
        
        return {
            'success': True,
            'message': '工序已重新排程',
            'conflicts': [v.to_dict() for v in violations]  # 返回警告
        }
    
    def clear_scheduling(self, order_ids: List[int] = None):
        """清除排程结果"""
        query = self.db.query(models.Operation)
        
        if order_ids:
            query = query.filter(models.Operation.order_id.in_(order_ids))
        
        operations = query.all()
        
        for op in operations:
            op.scheduled_start = None
            op.scheduled_end = None
            op.resource_id = None
            op.status = models.OperationStatus.PENDING.value
        
        # 更新订单状态
        order_query = self.db.query(models.ProductionOrder)
        if order_ids:
            order_query = order_query.filter(models.ProductionOrder.id.in_(order_ids))
        
        for order in order_query.all():
            order.status = models.OrderStatus.CREATED.value
        
        self.db.commit()
        
        return {'message': f'已清除 {len(operations)} 个工序的排程'}
    
    def get_gantt_data(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        view_type: str = "order"  # "order" 或 "resource"
    ) -> schemas.GanttData:
        """
        获取甘特图数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            view_type: 视图类型 - "order"(按订单) 或 "resource"(按资源)
        
        Returns:
            甘特图数据
        """
        tasks = []
        links = []
        
        # 默认时间范围
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now() + timedelta(days=30)
        
        if view_type == "order":
            tasks, links = self._get_order_view_data(start_date, end_date)
        else:
            tasks, links = self._get_resource_view_data(start_date, end_date)
        
        return schemas.GanttData(data=tasks, links=links)
    
    def _get_order_view_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> tuple:
        """获取订单视图的甘特图数据"""
        tasks = []
        links = []
        
        # 获取有排程的计划订单和所有生产订单
        orders = self.db.query(models.ProductionOrder).filter(
            (
                (models.ProductionOrder.order_type == models.OrderType.PLANNED.value) &
                (models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value)
            ) | (
                models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value
            )
        ).all()
        
        # 状态颜色映射 - 区分计划订单和生产订单
        planned_colors = {
            'pending': '#909399',
            'scheduled': '#409EFF',
            'in_progress': '#E6A23C',
            'completed': '#67C23A'
        }
        # 生产订单使用灰色系 (已锁定)
        production_colors = {
            'pending': '#9CA3AF',
            'scheduled': '#6B7280',  # 灰色
            'in_progress': '#4B5563',
            'completed': '#374151'
        }
        
        for order in orders:
            is_production = order.order_type == models.OrderType.PRODUCTION.value
            status_colors = production_colors if is_production else planned_colors
            order_type_label = "[生产]" if is_production else "[计划]"
            
            # 生产订单使用确认时间，计划订单使用排程时间
            if is_production and order.confirmed_start and order.confirmed_end:
                # 生产订单：使用确认的时间
                order_start = order.confirmed_start
                order_end = order.confirmed_end
                
                # 获取工序（可能没有详细排程）
                operations = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order.id
                ).order_by(models.Operation.sequence).all()
            else:
                # 计划订单：使用排程的时间
                operations = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order.id,
                    models.Operation.scheduled_start != None
                ).order_by(models.Operation.sequence).all()
                
                if not operations:
                    continue
                
                # 计算订单的开始和结束时间
                order_start = min(op.scheduled_start for op in operations)
                order_end = max(op.scheduled_end for op in operations)
            
            # 计算进度
            completed_ops = sum(1 for op in operations if op.status == 'completed')
            progress = completed_ops / len(operations) if operations else 0
            
            # 添加订单任务
            tasks.append(schemas.GanttTask(
                id=f"order_{order.id}",
                text=f"{order_type_label} {order.order_number} - {order.product.name if order.product else ''}",
                start_date=order_start.strftime("%Y-%m-%d %H:%M"),
                end_date=order_end.strftime("%Y-%m-%d %H:%M"),
                progress=progress,
                type="project",
                order_id=order.id,
                status=order.status,
                color='#6B7280' if is_production else None  # 生产订单灰色
            ))
            
            # 添加工序任务
            prev_op_id = None
            for op in operations:
                resource_name = op.resource.name if op.resource else "未分配"
                
                # 生产订单工序可能没有排程时间，使用订单时间均分
                if op.scheduled_start and op.scheduled_end:
                    op_start = op.scheduled_start
                    op_end = op.scheduled_end
                elif is_production:
                    # 根据工序顺序均分时间
                    total_duration = (order_end - order_start).total_seconds()
                    op_count = len(operations)
                    op_duration = total_duration / op_count if op_count > 0 else 0
                    op_idx = operations.index(op)
                    op_start = order_start + timedelta(seconds=op_duration * op_idx)
                    op_end = op_start + timedelta(seconds=op_duration)
                else:
                    continue
                
                # 如果有切换时间，先添加切换工序（dummy product）
                # 注意：排程时间已经包含了切换时间，所以：
                # - 切换时段：scheduled_start 到 scheduled_start + changeover_time
                # - 实际加工：scheduled_start + changeover_time 到 scheduled_end
                changeover_time = getattr(op, 'changeover_time', 0) or 0
                
                if changeover_time > 0 and not is_production:
                    changeover_duration = timedelta(hours=changeover_time)
                    changeover_start = op_start
                    changeover_end = op_start + changeover_duration
                    actual_op_start = changeover_end  # 实际加工从切换结束后开始
                    
                    # 添加切换工序任务
                    tasks.append(schemas.GanttTask(
                        id=f"changeover_{op.id}",
                        text=f"🔄 切换 ({changeover_time:.1f}h)",
                        start_date=changeover_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=changeover_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"order_{order.id}",
                        progress=1.0 if op.status in ['completed', 'in_progress'] else 0,
                        operation_id=op.id,
                        resource_id=op.resource_id,
                        status='changeover',
                        color='#F59E0B',  # 橙黄色
                        task_type='changeover',
                        order_type=order.order_type,
                        changeover_time=changeover_time
                    ))
                    
                    # 切换工序到实际工序的链接
                    links.append(schemas.GanttLink(
                        id=f"link_changeover_{op.id}",
                        source=f"changeover_{op.id}",
                        target=f"op_{op.id}",
                        type="0"
                    ))
                    
                    # 实际工序从切换结束后开始
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{op.sequence} {op.name} ({resource_name})",
                        start_date=actual_op_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=op_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"order_{order.id}",
                        progress=1.0 if op.status == 'completed' else 0,
                        operation_id=op.id,
                        resource_id=op.resource_id,
                        status=op.status,
                        color=status_colors.get(op.status, '#6B7280' if is_production else '#409EFF'),
                        task_type='operation',
                        order_type=order.order_type,
                        changeover_time=changeover_time
                    ))
                else:
                    # 没有切换时间，直接显示工序
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{op.sequence} {op.name} ({resource_name})",
                        start_date=op_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=op_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"order_{order.id}",
                        progress=1.0 if op.status == 'completed' else 0,
                        operation_id=op.id,
                        resource_id=op.resource_id,
                        status=op.status,
                        color=status_colors.get(op.status, '#6B7280' if is_production else '#409EFF'),
                        task_type='operation',
                        order_type=order.order_type,
                        changeover_time=changeover_time
                    ))
                
                # 添加工序之间的链接
                if prev_op_id:
                    links.append(schemas.GanttLink(
                        id=f"link_{prev_op_id}_{op.id}",
                        source=f"op_{prev_op_id}",
                        target=f"op_{op.id}",
                        type="0"
                    ))
                prev_op_id = op.id
        
        return tasks, links
    
    def _get_resource_view_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> tuple:
        """获取资源视图的甘特图数据"""
        tasks = []
        links = []
        
        # 获取所有资源
        resources = self.db.query(models.Resource).all()
        
        for resource in resources:
            # 资源作为父任务
            tasks.append(schemas.GanttTask(
                id=f"resource_{resource.id}",
                text=f"{resource.name} ({resource.work_center.name if resource.work_center else ''})",
                start_date=start_date.strftime("%Y-%m-%d %H:%M"),
                end_date=end_date.strftime("%Y-%m-%d %H:%M"),
                type="project",
                resource_id=resource.id
            ))
            
            # 获取该资源的所有工序
            operations = self.db.query(models.Operation).filter(
                models.Operation.resource_id == resource.id,
                models.Operation.scheduled_start != None,
                models.Operation.scheduled_start >= start_date,
                models.Operation.scheduled_end <= end_date
            ).order_by(models.Operation.scheduled_start).all()
            
            for op in operations:
                order = op.order
                order_number = order.order_number if order else ""
                is_production = order.order_type == models.OrderType.PRODUCTION.value if order else False
                
                # 如果有切换时间，先添加切换工序（dummy product）
                # 排程时间已经包含了切换时间：
                # - 切换时段：scheduled_start 到 scheduled_start + changeover_time
                # - 实际加工：scheduled_start + changeover_time 到 scheduled_end
                changeover_time = getattr(op, 'changeover_time', 0) or 0
                
                if changeover_time > 0 and not is_production:
                    changeover_duration = timedelta(hours=changeover_time)
                    changeover_start = op.scheduled_start
                    changeover_end = op.scheduled_start + changeover_duration
                    actual_op_start = changeover_end
                    
                    # 添加切换工序任务
                    tasks.append(schemas.GanttTask(
                        id=f"changeover_{op.id}",
                        text=f"🔄 {order_number} 切换",
                        start_date=changeover_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=changeover_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"resource_{resource.id}",
                        progress=1.0 if op.status in ['completed', 'in_progress'] else 0,
                        operation_id=op.id,
                        order_id=op.order_id,
                        resource_id=resource.id,
                        status='changeover',
                        color='#F59E0B',  # 橙黄色
                        task_type='changeover',
                        order_type=order.order_type if order else None,
                        changeover_time=changeover_time
                    ))
                    
                    # 实际工序从切换结束后开始
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{order_number} - {op.sequence} {op.name}",
                        start_date=actual_op_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=op.scheduled_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"resource_{resource.id}",
                        progress=1.0 if op.status == 'completed' else 0,
                        operation_id=op.id,
                        order_id=op.order_id,
                        resource_id=resource.id,
                        status=op.status,
                        task_type='operation',
                        order_type=order.order_type if order else None,
                        changeover_time=changeover_time
                    ))
                else:
                    # 没有切换时间，直接显示工序
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{order_number} - {op.sequence} {op.name}",
                        start_date=op.scheduled_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=op.scheduled_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"resource_{resource.id}",
                        progress=1.0 if op.status == 'completed' else 0,
                        operation_id=op.id,
                        order_id=op.order_id,
                        resource_id=resource.id,
                        status=op.status,
                        task_type='operation',
                        order_type=order.order_type if order else None,
                        changeover_time=changeover_time
                    ))
        
        return tasks, links
    
    def get_kpi_data(self) -> schemas.KPIDashboard:
        """获取KPI仪表板数据"""
        # 资源利用率
        resource_utilization = self._calculate_resource_utilization()
        
        # 订单KPI
        order_kpi = self._calculate_order_kpi()
        
        # 平均提前期
        avg_lead_time = self._calculate_avg_lead_time()
        
        # 按日产能负荷
        capacity_load = self._calculate_capacity_load_by_day()
        
        return schemas.KPIDashboard(
            resource_utilization=resource_utilization,
            order_kpi=order_kpi,
            avg_lead_time_hours=avg_lead_time,
            capacity_load_by_day=capacity_load
        )
    
    def _calculate_resource_utilization(self) -> List[schemas.ResourceUtilization]:
        """计算资源利用率"""
        result = []
        
        # 计算未来7天的利用率
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        resources = self.db.query(models.Resource).all()
        
        for resource in resources:
            total_capacity = resource.capacity_per_day * 7
            
            # 获取该资源在时间范围内的已排程工序
            operations = self.db.query(models.Operation).filter(
                models.Operation.resource_id == resource.id,
                models.Operation.scheduled_start != None,
                models.Operation.scheduled_start >= start_date,
                models.Operation.scheduled_end <= end_date
            ).all()
            
            scheduled_hours = sum(
                (op.scheduled_end - op.scheduled_start).total_seconds() / 3600
                for op in operations
            )
            
            utilization = (scheduled_hours / total_capacity * 100) if total_capacity > 0 else 0
            
            result.append(schemas.ResourceUtilization(
                resource_id=resource.id,
                resource_name=resource.name,
                work_center_name=resource.work_center.name if resource.work_center else "",
                total_capacity_hours=total_capacity,
                scheduled_hours=scheduled_hours,
                utilization_percent=round(utilization, 1)
            ))
        
        return result
    
    def _calculate_order_kpi(self) -> schemas.OrderKPI:
        """计算订单KPI"""
        total = self.db.query(models.ProductionOrder).count()
        
        scheduled = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        # 计算准时率
        scheduled_orders = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).all()
        
        on_time = 0
        delayed = 0
        
        for order in scheduled_orders:
            last_op = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).order_by(models.Operation.sequence.desc()).first()
            
            if last_op and last_op.scheduled_end:
                if last_op.scheduled_end <= order.due_date:
                    on_time += 1
                else:
                    delayed += 1
        
        on_time_rate = (on_time / scheduled * 100) if scheduled > 0 else 0
        
        return schemas.OrderKPI(
            total_orders=total,
            scheduled_orders=scheduled,
            on_time_orders=on_time,
            delayed_orders=delayed,
            on_time_rate=round(on_time_rate, 1)
        )
    
    def _calculate_avg_lead_time(self) -> float:
        """计算平均提前期"""
        orders = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).all()
        
        if not orders:
            return 0.0
        
        total_lead_time = 0
        count = 0
        
        for order in orders:
            operations = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.scheduled_start != None
            ).all()
            
            if operations:
                start = min(op.scheduled_start for op in operations)
                end = max(op.scheduled_end for op in operations)
                lead_time = (end - start).total_seconds() / 3600
                total_lead_time += lead_time
                count += 1
        
        return round(total_lead_time / count, 1) if count > 0 else 0.0
    
    def _calculate_capacity_load_by_day(self) -> dict:
        """计算每日产能负荷"""
        result = {}
        
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day_offset in range(14):
            current_date = start_date + timedelta(days=day_offset)
            next_date = current_date + timedelta(days=1)
            
            date_key = current_date.strftime("%Y-%m-%d")
            
            # 获取当天的总产能和已用产能
            resources = self.db.query(models.Resource).all()
            total_capacity = sum(r.capacity_per_day for r in resources)
            
            operations = self.db.query(models.Operation).filter(
                models.Operation.scheduled_start >= current_date,
                models.Operation.scheduled_start < next_date
            ).all()
            
            used_capacity = sum(
                (op.scheduled_end - op.scheduled_start).total_seconds() / 3600
                for op in operations
                if op.scheduled_end
            )
            
            result[date_key] = {
                'total_capacity': total_capacity,
                'used_capacity': round(used_capacity, 1),
                'utilization': round(used_capacity / total_capacity * 100, 1) if total_capacity > 0 else 0
            }
        
        return result
