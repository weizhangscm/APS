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
            
            # 优先使用工序已分配的资源
            if operation.resource_id:
                assigned_resource = self.db.query(models.Resource).filter(
                    models.Resource.id == operation.resource_id
                ).first()
                if assigned_resource:
                    resources = [assigned_resource]
                else:
                    resources = self.get_available_resources(work_center_id)
            else:
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
            
            # 优先使用工序已分配的资源
            if operation.resource_id:
                assigned_resource = self.db.query(models.Resource).filter(
                    models.Resource.id == operation.resource_id
                ).first()
                if assigned_resource:
                    resources = [assigned_resource]
                else:
                    resources = self.get_available_resources(work_center_id)
            else:
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


class StableForwardScheduler(SchedulingAlgorithm):
    """
    稳定向前计划算法 (Stable Forward Scheduling)
    
    基于 SAP S4 DS 的稳定向前计划启发式算法实现。
    算法标识符 (SAP): /SAPAPO/SFW_HEUR_FW_STABLE
    
    主要特点:
    1. 多层级有限产能排程 - 考虑多个生产步骤的资源约束
    2. 稳定性 - 对相同输入数据多次执行产生一致的结果
    3. 解决的问题:
       - 积压 (Backlog): 处理超过最早开始日期的订单
       - 产能过载 (Capacity Overload): 在资源过载时自动调整计划
       - 最小间隔违反 (Minimum Interval Violation): 确保工序间的最小间隔
       - 订单有效期违反 (Validity Interval Violation): 确保订单在有效期内排程
    
    策略参数（参照 SAP PP/DS 详细计划策略参数文件）:
    - sorting_rule: 排序规则（订单优先级）- 决定订单的排程顺序
    - direction: 计划方向（向前/向后）- 从期望日期搜索的方向
    - expected_date_mode: 期望日期（当前日期/指定日期）- 排程的起点
    - order_internal_relation: 订单内部关系（不考虑/始终考虑）- 是否维护订单内工序关系
    - adjust_related_operations: 是否调整关联工序
    - infinite_capacity_for_related: 关联工序是否使用无限产能
    - error_handling: 计划出错的操作（立即终止）- 错误处理方式
    """
    
    def __init__(
        self, 
        db: Session,
        finite_capacity: bool = True,
        resolve_backlog: bool = True,
        resolve_overload: bool = True,
        preserve_scheduled: bool = True,
        sorting_rule: str = "PRIORITY",
        planning_horizon: int = 90
    ):
        """
        初始化稳定向前计划器
        
        Args:
            db: 数据库会话
            finite_capacity: 是否考虑有限产能（计划模式=查找槽位时为True）
            resolve_backlog: 是否解决积压问题
            resolve_overload: 是否解决产能过载
            preserve_scheduled: 是否保持已排程订单不变
            sorting_rule: 排序规则 (PRIORITY, EDD, SPT, FIFO)
            planning_horizon: 计划时间范围(天)
        """
        super().__init__(db)
        self.finite_capacity = finite_capacity
        self.resolve_backlog = resolve_backlog
        self.resolve_overload = resolve_overload
        self.preserve_scheduled = preserve_scheduled
        self.sorting_rule = sorting_rule
        self.planning_horizon = planning_horizon
        
        # 策略参数（由 engine 设置）
        self.direction = 'forward'  # 计划方向: forward/backward
        self.expected_date_mode = '当前日期'  # 期望日期模式
        self.order_internal_relation = '不考虑'  # 订单内部关系
        self.adjust_related_operations = False  # 是否调整关联工序
        self.infinite_capacity_for_related = False  # 关联工序是否无限产能
        self.error_handling = '立即终止'  # 错误处理方式
        
        # 用于稳定性的确定性排序键
        self.order_sequence_counter = 0
        
        # 资源时间段占用表 - 用于有限产能计算
        # {resource_id: [(start, end, operation_id, product_id, is_fixed), ...]}
        self.resource_slots = defaultdict(list)
    
    def schedule_orders(
        self,
        orders: List[models.ProductionOrder],
        target_operation_ids: List[int] = None,
        selected_resource_ids: List[int] = None
    ) -> Dict:
        """
        对多个订单进行稳定向前计划
        
        Args:
            orders: 要排程的订单列表
            target_operation_ids: 目标工序ID列表，如果指定则只排这些工序
            selected_resource_ids: 选中的资源ID列表
        
        Returns:
            排程结果统计
        """
        results = {
            'scheduled_orders': 0,
            'scheduled_operations': 0,
            'backlog_resolved': 0,
            'overload_resolved': 0,
            'details': []
        }
        
        if not orders:
            return results
        
        # 保存目标工序和资源信息
        self.target_operation_ids = set(target_operation_ids) if target_operation_ids else None
        self.selected_resource_ids = set(selected_resource_ids) if selected_resource_ids else None
        
        # 步骤1: 加载现有的已排程工序（作为固定约束）
        self._load_existing_schedule()
        
        # 步骤2: 确定性排序订单（保证稳定性）
        sorted_orders = self._stable_sort_orders(orders)
        
        # 步骤3: 分离已排程和未排程订单
        # 注意：当指定了目标工序（target_operation_ids）时，即使 preserve_scheduled=True，
        # 也需要处理包含目标工序的订单，以便重新排程选中资源上的工序
        if self.preserve_scheduled and self.target_operation_ids is None:
            # 没有指定目标工序时，保留已排程的订单
            unscheduled_orders = [o for o in sorted_orders if o.status != models.OrderStatus.SCHEDULED.value]
            scheduled_orders = [o for o in sorted_orders if o.status == models.OrderStatus.SCHEDULED.value]
            
            # 将已排程订单的工序标记为固定
            for order in scheduled_orders:
                self._mark_order_as_fixed(order)
        elif self.preserve_scheduled and self.target_operation_ids is not None:
            # 指定了目标工序时，需要处理包含目标工序的订单
            # 即使订单已排程，也需要重新排程目标工序
            unscheduled_orders = []
            scheduled_orders_to_skip = []
            
            for order in sorted_orders:
                # 检查订单是否包含目标工序
                has_target_op = any(op.id in self.target_operation_ids for op in order.operations)
                
                if has_target_op:
                    # 包含目标工序的订单需要处理
                    unscheduled_orders.append(order)
                elif order.status == models.OrderStatus.SCHEDULED.value:
                    # 不包含目标工序的已排程订单，标记为固定
                    scheduled_orders_to_skip.append(order)
                else:
                    # 不包含目标工序的未排程订单，也跳过（不在本次排程范围内）
                    pass
            
            # 将不包含目标工序的已排程订单标记为固定
            for order in scheduled_orders_to_skip:
                self._mark_order_as_fixed(order)
        else:
            unscheduled_orders = sorted_orders
        
        # 步骤4: 逐个排程未排程的订单
        for order in unscheduled_orders:
            try:
                order_result = self._schedule_order_stable(
                    order, 
                    target_operation_ids=self.target_operation_ids
                )
                if order_result['success']:
                    results['scheduled_orders'] += 1
                    results['scheduled_operations'] += order_result['operations_count']
                    if order_result.get('backlog_resolved'):
                        results['backlog_resolved'] += 1
                    if order_result.get('overload_resolved'):
                        results['overload_resolved'] += 1
                results['details'].append(order_result)
            except Exception as e:
                # 根据 error_handling 策略决定如何处理错误
                error_handling = getattr(self, 'error_handling', '立即终止')
                results['details'].append({
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'success': False,
                    'error': str(e)
                })
                # 如果是"立即终止"，停止处理后续订单
                if error_handling == '立即终止':
                    break
                # 如果是"无限计划"，继续处理下一个订单
        
        return results
    
    def _load_existing_schedule(self):
        """加载现有的已排程工序"""
        end_date = datetime.now() + timedelta(days=self.planning_horizon)
        start_date = datetime.now() - timedelta(days=7)
        
        # 调用父类方法加载资源负荷
        self.load_resource_schedule(start_date, end_date)
        
        # 转换为资源时间段格式
        for resource_id, slots in self.resource_load.items():
            for start, end, op_id, product_id in slots:
                self.resource_slots[resource_id].append(
                    (start, end, op_id, product_id, False)  # False = 非固定
                )
    
    def _mark_order_as_fixed(self, order: models.ProductionOrder):
        """将订单的所有工序标记为固定（不可移动）"""
        for op in order.operations:
            if op.scheduled_start and op.scheduled_end and op.resource_id:
                # 查找并更新该工序的固定标志
                slots = self.resource_slots[op.resource_id]
                for i, (start, end, op_id, product_id, is_fixed) in enumerate(slots):
                    if op_id == op.id:
                        slots[i] = (start, end, op_id, product_id, True)
                        break
                else:
                    # 如果没找到，添加新的固定时间段
                    product_id = order.product_id
                    self.resource_slots[op.resource_id].append(
                        (op.scheduled_start, op.scheduled_end, op.id, product_id, True)
                    )
    
    def _stable_sort_orders(
        self, 
        orders: List[models.ProductionOrder]
    ) -> List[models.ProductionOrder]:
        """
        稳定排序订单 - 确保相同输入产生相同输出
        
        使用多级排序键确保确定性：
        1. 主排序键（根据sorting_rule）
        2. 订单ID作为打破平局的次级键
        """
        def get_sort_key(order):
            # 主排序键
            if self.sorting_rule == "EDD":
                primary = order.due_date
            elif self.sorting_rule == "SPT":
                total = sum(op.run_time for op in order.operations) if order.operations else 0
                primary = total
            elif self.sorting_rule == "PRIORITY":
                primary = order.priority
            else:  # FIFO
                primary = order.created_at
            
            # 次级排序键（订单ID）确保稳定性
            secondary = order.id
            
            return (primary, secondary)
        
        return sorted(orders, key=get_sort_key)
    
    def _schedule_order_stable(
        self, 
        order: models.ProductionOrder,
        target_operation_ids: set = None
    ) -> Dict:
        """
        对单个订单进行稳定排程（支持向前/向后计划方向）
        
        根据 SAP PP/DS 详细计划策略参数文件实现：
        - 计划方向决定搜索可用时间的方向
        - 期望日期决定排程的起点
        - 订单内部关系决定是否维护工序间的时间关系
        - 子计划模式决定关联工序的排程方式
        
        Args:
            order: 要排程的订单
            target_operation_ids: 目标工序ID集合（选中资源上的工序）
        
        Returns:
            排程结果
        """
        result = {
            'order_id': order.id,
            'order_number': order.order_number,
            'success': False,
            'operations_count': 0,
            'backlog_resolved': False,
            'overload_resolved': False,
            'operations': []
        }
        
        # 获取订单的所有工序（按序列号排序）
        operations = self.db.query(models.Operation).filter(
            models.Operation.order_id == order.id
        ).order_by(models.Operation.sequence).all()
        
        if not operations:
            result['error'] = '订单没有工序'
            return result
        
        # ========== 重新排程前，清除目标工序的旧时间槽 ==========
        # 这是为了避免重新排程时产生冲突
        for op in operations:
            is_target = (target_operation_ids is None or op.id in target_operation_ids)
            if is_target and op.resource_id and op.scheduled_start and op.scheduled_end:
                # 从 resource_slots 中移除此工序的旧时间槽
                if op.resource_id in self.resource_slots:
                    old_slots = self.resource_slots[op.resource_id]
                    new_slots = [(s, e, oid, pid, f) for s, e, oid, pid, f in old_slots if oid != op.id]
                    self.resource_slots[op.resource_id] = new_slots
        
        # ========== 确定期望日期（排程起点）==========
        now = datetime.now()
        expected_date_mode = getattr(self, 'expected_date_mode', '当前日期')
        direction = getattr(self, 'direction', 'forward')
        
        if expected_date_mode == '当前日期':
            # 使用当前日期作为期望日期
            desired_date = now
        else:
            # 使用指定日期（订单的最早开始日期或交期）
            if direction == 'forward':
                # 向前排程：从最早开始日期开始
                desired_date = order.earliest_start or now
            else:
                # 向后排程：从交期开始
                desired_date = order.due_date or (now + timedelta(days=30))
        
        # 处理积压：如果期望日期已过且是向前排程
        if direction == 'forward' and desired_date < now:
            if self.resolve_backlog:
                desired_date = now
                result['backlog_resolved'] = True
            else:
                result['error'] = '订单已积压且未启用积压解决'
                return result
        
        # ========== 获取策略参数 ==========
        adjust_related_operations = getattr(self, 'adjust_related_operations', False)
        infinite_capacity_for_related = getattr(self, 'infinite_capacity_for_related', False)
        selected_resource_ids = getattr(self, 'selected_resource_ids', None)
        order_internal_relation = getattr(self, 'order_internal_relation', '不考虑')
        
        current_product_id = order.product_id
        scheduled_ops = []
        
        # ========== 根据计划方向确定工序处理顺序 ==========
        if direction == 'backward':
            # 向后排程：从最后一道工序开始，逆序处理
            operations = list(reversed(operations))
            current_time = desired_date  # 从交期开始向前排
        else:
            # 向前排程：从第一道工序开始，顺序处理
            current_time = desired_date  # 从期望日期开始向后排
        
        # ========== 遍历工序进行排程 ==========
        for i, operation in enumerate(operations):
            # 检查此工序是否在选中资源上（目标工序）
            is_target_operation = (target_operation_ids is None or operation.id in target_operation_ids)
            is_on_selected_resource = (
                selected_resource_ids is None or 
                (operation.resource_id and operation.resource_id in selected_resource_ids)
            )
            
            # ========== 根据订单内部关系决定排程策略 ==========
            should_schedule = False
            use_infinite_capacity = False
            is_related_operation = False
            
            if is_target_operation and is_on_selected_resource:
                # 目标工序（在选中资源上），必须排程
                should_schedule = True
            elif order_internal_relation == '始终考虑':
                # 订单内部关系="始终考虑"：需要调整关联工序以维护时间关系
                # 即使不是目标工序，也需要排程以保持订单内工序的时间顺序
                should_schedule = True
                is_related_operation = True
                use_infinite_capacity = infinite_capacity_for_related
            elif target_operation_ids is None:
                # 没有目标工序限制，排程所有工序
                should_schedule = True
            
            if not should_schedule:
                # 跳过此工序，但需要考虑其已有排程时间
                if direction == 'forward' and operation.scheduled_end:
                    current_time = max(current_time, operation.scheduled_end)
                elif direction == 'backward' and operation.scheduled_start:
                    current_time = min(current_time, operation.scheduled_start)
                continue
            
            # ========== 获取工序的工作中心和可用资源 ==========
            routing_op = operation.routing_operation
            if not routing_op:
                continue
            
            work_center_id = routing_op.work_center_id
            
            # ========== 关键修改：目标工序只能在其已分配的资源上排程，不改变资源分配 ==========
            # 对于目标工序（选中资源上的工序）：只在已分配的资源上排程，不允许重新分配
            # 对于关联工序：也只在其已分配的资源上排程
            if operation.resource_id:
                assigned_resource = self.db.query(models.Resource).filter(
                    models.Resource.id == operation.resource_id
                ).first()
                if assigned_resource:
                    # 只使用已分配的资源，不允许重新分配到其他资源
                    resources = [assigned_resource]
                else:
                    # 如果已分配的资源不存在，跳过此工序
                    if direction == 'forward' and operation.scheduled_end:
                        current_time = max(current_time, operation.scheduled_end)
                    elif direction == 'backward' and operation.scheduled_start:
                        current_time = min(current_time, operation.scheduled_start)
                    continue
            else:
                # 工序没有分配资源，需要分配一个
                # 但只能从选中的资源中选择（如果有选中资源限制）
                if selected_resource_ids:
                    # 只从选中的资源中选择
                    available = self.get_available_resources(work_center_id)
                    resources = [r for r in available if r.id in selected_resource_ids]
                else:
                    resources = self.get_available_resources(work_center_id)
            
            if not resources:
                # 没有可用资源，跳过
                if direction == 'forward' and operation.scheduled_end:
                    current_time = max(current_time, operation.scheduled_end)
                elif direction == 'backward' and operation.scheduled_start:
                    current_time = min(current_time, operation.scheduled_start)
                continue
            
            # ========== 查找最佳时间槽（资源已固定，只查找时间）==========
            selected_resource, slot_start, slot_end, changeover_time = self._find_best_resource_slot(
                resources,
                current_time,
                operation.run_time,
                current_product_id,
                work_center_id,
                use_infinite_capacity=use_infinite_capacity,
                direction=direction
            )
            
            if selected_resource is None:
                # 计划出错：找不到可用时间槽
                result['error'] = f'工序 {operation.name} 在资源上找不到可用时间槽'
                # error_handling = '立即终止'，直接返回错误
                return result
            
            # 检查是否需要解决产能过载
            if self.resolve_overload:
                if direction == 'forward' and slot_start > current_time + timedelta(hours=1):
                    result['overload_resolved'] = True
                elif direction == 'backward' and slot_end < current_time - timedelta(hours=1):
                    result['overload_resolved'] = True
            
            # ========== 更新工序排程信息（保持原资源分配不变）==========
            # 注意：不改变 operation.resource_id，保持原有资源分配
            operation.scheduled_start = slot_start
            operation.scheduled_end = slot_end
            operation.changeover_time = changeover_time
            operation.status = models.OperationStatus.SCHEDULED.value
            
            # 记录资源时间段占用
            self.resource_slots[selected_resource.id].append(
                (slot_start, slot_end, operation.id, current_product_id, False)
            )
            self.resource_slots[selected_resource.id].sort(key=lambda x: x[0])
            
            scheduled_ops.append({
                'operation_id': operation.id,
                'operation_name': operation.name,
                'resource_id': selected_resource.id,
                'resource_name': selected_resource.name,
                'start': slot_start.isoformat(),
                'end': slot_end.isoformat(),
                'changeover_time': changeover_time,
                'is_related': is_related_operation,
                'direction': direction
            })
            
            # ========== 更新下一工序的期望时间 ==========
            if direction == 'forward':
                # 向前排程：下一工序的最早开始时间 = 当前工序结束时间
                current_time = slot_end
            else:
                # 向后排程：上一工序的最晚结束时间 = 当前工序开始时间
                current_time = slot_start
        
        if scheduled_ops:
            # 更新订单状态
            order.status = models.OrderStatus.SCHEDULED.value
            
            result['success'] = True
            result['operations_count'] = len(scheduled_ops)
            result['operations'] = scheduled_ops
        
        return result
    
    def _find_best_resource_slot(
        self,
        resources: List[models.Resource],
        desired_time: datetime,
        duration_hours: float,
        product_id: int,
        work_center_id: int,
        use_infinite_capacity: bool = False,
        direction: str = 'forward'
    ) -> Tuple[Optional[models.Resource], Optional[datetime], Optional[datetime], float]:
        """
        找到最佳资源和时间段（支持向前/向后排程方向）
        
        根据 SAP PP/DS 的计划模式"查找槽位"实现：
        - 在资源的现有排程中搜索足够大的空闲时间段
        - 向前排程：从期望日期向未来搜索
        - 向后排程：从期望日期向过去搜索
        
        考虑因素:
        1. 有限产能约束（计划模式=查找槽位）
        2. 切换时间最小化
        3. 资源负荷均衡
        
        Args:
            resources: 可用资源列表
            desired_time: 期望日期/时间（排程的起点）
            duration_hours: 工序时长（小时）
            product_id: 产品ID
            work_center_id: 工作中心ID
            use_infinite_capacity: 是否使用无限产能（子计划模式=以无限方式调度相关操作）
            direction: 计划方向 ('forward'=向前, 'backward'=向后)
        
        Returns:
            (最佳资源, 开始时间, 结束时间, 切换时间)
        """
        best_option = None
        best_cost = float('inf')
        
        for resource in resources:
            # 获取该产品在此资源上的切换时间
            if direction == 'forward':
                last_product_id = self._get_last_product_before(resource.id, desired_time)
            else:
                last_product_id = self._get_next_product_after(resource.id, desired_time)
            
            changeover_time = self.get_changeover_time(
                last_product_id, product_id, resource.id, work_center_id
            )
            
            total_duration = duration_hours + changeover_time
            
            # ========== 根据计划模式和方向查找可用时间段 ==========
            if use_infinite_capacity:
                # 无限产能模式：直接在期望日期排程，不考虑资源负荷
                if direction == 'forward':
                    slot_start = desired_time
                    slot_end = desired_time + timedelta(hours=total_duration)
                else:
                    slot_end = desired_time
                    slot_start = desired_time - timedelta(hours=total_duration)
            else:
                # 有限产能模式（查找槽位）：在资源负荷中寻找空闲时间段
                if direction == 'forward':
                    slot_start, slot_end = self._find_available_slot(
                        resource.id,
                        total_duration,
                        desired_time
                    )
                else:
                    slot_start, slot_end = self._find_available_slot_backward(
                        resource.id,
                        total_duration,
                        desired_time
                    )
            
            if slot_start is None:
                continue
            
            # ========== 计算成本函数 ==========
            # 成本 = 延迟/提前时间 + 切换时间权重 + 负荷均衡权重
            if direction == 'forward':
                # 向前排程：希望尽早开始，延迟越少越好
                delay = (slot_start - desired_time).total_seconds() / 3600
            else:
                # 向后排程：希望尽晚结束，提前越少越好
                delay = (desired_time - slot_end).total_seconds() / 3600
            
            cost = abs(delay) + changeover_time * 2  # 切换时间权重为2
            
            # 加入资源负荷均衡因素（无限产能模式不考虑负荷）
            if not use_infinite_capacity:
                current_load = self._calculate_resource_load(resource.id, slot_start)
                cost += current_load * 0.1  # 负荷权重为0.1
            
            if cost < best_cost:
                best_cost = cost
                best_option = (resource, slot_start, slot_end, changeover_time)
        
        if best_option:
            return best_option
        return None, None, None, 0
    
    def _get_next_product_after(
        self, 
        resource_id: int, 
        after_time: datetime
    ) -> Optional[int]:
        """获取资源在指定时间之后最先生产的产品ID（用于向后排程）"""
        slots = self.resource_slots.get(resource_id, [])
        next_product_id = None
        next_start_time = None
        
        for start, end, op_id, product_id, is_fixed in slots:
            if start >= after_time:
                if next_start_time is None or start < next_start_time:
                    next_start_time = start
                    next_product_id = product_id
        
        return next_product_id
    
    def _find_available_slot_backward(
        self,
        resource_id: int,
        duration_hours: float,
        latest_end: datetime
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        向后查找资源的可用时间段（从交期向前搜索）
        
        用于向后排程（backward scheduling），从交期开始向过去搜索空闲时间段。
        
        Args:
            resource_id: 资源ID
            duration_hours: 需要的时间长度（小时）
            latest_end: 最晚结束时间（通常是交期）
        
        Returns:
            (开始时间, 结束时间) 或 (None, None)
        """
        if not self.finite_capacity:
            # 无限产能模式：直接返回
            slot_end = latest_end
            slot_start = latest_end - timedelta(hours=duration_hours)
            return slot_start, slot_end
        
        slots = sorted(self.resource_slots.get(resource_id, []), key=lambda x: x[0], reverse=True)
        
        # 从最晚结束时间开始向前搜索
        current_end = latest_end
        duration = timedelta(hours=duration_hours)
        
        # 计划范围的最早时间（不能排到过去太远）
        earliest_allowed = datetime.now() - timedelta(days=7)
        
        for slot_start, slot_end, op_id, product_id, is_fixed in slots:
            if slot_end <= earliest_allowed:
                break
            
            # 检查当前时间段和已占用时间段之间的间隙
            if slot_end <= current_end:
                gap = current_end - slot_end
                if gap >= duration:
                    # 找到足够大的间隙
                    return (current_end - duration, current_end)
                # 移动到这个时间段之前继续搜索
                current_end = slot_start
        
        # 检查最后一个间隙（从最早时间到第一个占用时间段）
        if current_end - earliest_allowed >= duration:
            return (current_end - duration, current_end)
        
        # 如果没有找到间隙，使用最早可用时间
        if current_end >= earliest_allowed + duration:
            return (current_end - duration, current_end)
        
        return None, None
    
    def _get_last_product_before(
        self, 
        resource_id: int, 
        before_time: datetime
    ) -> Optional[int]:
        """获取资源在指定时间之前最后生产的产品ID"""
        slots = self.resource_slots.get(resource_id, [])
        last_product_id = None
        last_end_time = None
        
        for start, end, op_id, product_id, is_fixed in slots:
            if end <= before_time:
                if last_end_time is None or end > last_end_time:
                    last_end_time = end
                    last_product_id = product_id
        
        return last_product_id
    
    def _find_available_slot(
        self,
        resource_id: int,
        duration_hours: float,
        earliest_start: datetime
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        找到资源的下一个可用时间段（SAP式时间连续排程）
        
        实现有限产能约束：
        - 使用时间连续排程，允许工序跨天
        - 考虑已占用的时间段，寻找间隙
        - 工序可以从当天开始，跨越到下一个工作日完成
        
        SAP PP/DS 的做法：
        - 精确到秒的时间连续排程
        - 工序可以跨越工作时间边界
        - 非工作时间（夜间、周末）会被跳过，工序自动延续到下一个工作日
        """
        if not self.finite_capacity:
            # 无限产能模式
            end_time = earliest_start + timedelta(hours=duration_hours)
            return earliest_start, end_time
        
        capacity_per_day = self.get_resource_capacity(resource_id)
        existing_slots = sorted(self.resource_slots.get(resource_id, []), key=lambda x: x[0])
        
        # 从最早开始时间开始寻找可用时间段
        candidate_start = self._get_next_working_time(earliest_start, capacity_per_day)
        
        max_iterations = self.planning_horizon * 10  # 增加迭代次数以支持更长的搜索
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # 检查candidate_start是否与现有时间段冲突
            conflict_end = None
            for s, e, _, _, _ in existing_slots:
                if s <= candidate_start < e:
                    # 开始时间在某个已排程时间段内，需要移动到该时间段之后
                    conflict_end = e
                    break
            
            if conflict_end:
                # 移动到冲突时间段之后，并确保在工作时间内
                candidate_start = self._get_next_working_time(conflict_end, capacity_per_day)
                continue
            
            # 计算工序的实际结束时间（考虑非工作时间）
            candidate_end = self._calculate_end_time(candidate_start, duration_hours, capacity_per_day)
            
            # 检查整个工序时间段是否与现有排程冲突
            has_conflict = False
            for s, e, _, _, _ in existing_slots:
                if s < candidate_end and e > candidate_start:
                    # 有重叠，需要移动到该时间段之后
                    has_conflict = True
                    candidate_start = self._get_next_working_time(e, capacity_per_day)
                    break
            
            if not has_conflict:
                # 找到了可用时间段
                return candidate_start, candidate_end
        
        # 如果找不到可用时间段，回退到最早开始时间（无限产能模式）
        end_time = earliest_start + timedelta(hours=duration_hours)
        return earliest_start, end_time
    
    def _get_next_working_time(self, dt: datetime, capacity_per_day: float) -> datetime:
        """
        获取下一个工作时间点
        
        如果给定时间在工作时间内，返回该时间
        如果在非工作时间，返回下一个工作日的开始时间
        """
        work_start_hour = 8
        work_end_hour = work_start_hour + int(capacity_per_day)  # 例如8+8=16点
        
        if dt.hour < work_start_hour:
            # 在当天工作开始之前，移动到当天工作开始
            return dt.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        elif dt.hour >= work_end_hour:
            # 在当天工作结束之后，移动到下一天工作开始
            next_day = dt + timedelta(days=1)
            return next_day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        else:
            # 在工作时间内
            return dt
    
    def _calculate_end_time(
        self, 
        start_time: datetime, 
        duration_hours: float, 
        capacity_per_day: float
    ) -> datetime:
        """
        计算工序的实际结束时间（考虑跨天）
        
        SAP式时间连续排程：
        - 工序从start_time开始
        - 只在工作时间内计算，非工作时间自动跳过
        - 返回工序实际完成的时间
        """
        work_start_hour = 8
        work_end_hour = work_start_hour + int(capacity_per_day)
        
        remaining_hours = duration_hours
        current_time = start_time
        
        max_days = 365  # 防止无限循环
        days_checked = 0
        
        while remaining_hours > 0 and days_checked < max_days:
            days_checked += 1
            
            # 确保在工作时间内
            if current_time.hour < work_start_hour:
                current_time = current_time.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            elif current_time.hour >= work_end_hour:
                # 移动到下一天
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=work_start_hour, minute=0, second=0, microsecond=0
                )
                continue
            
            # 计算当天剩余的工作时间
            day_end = current_time.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
            available_hours_today = (day_end - current_time).total_seconds() / 3600
            
            if remaining_hours <= available_hours_today:
                # 当天可以完成
                end_time = current_time + timedelta(hours=remaining_hours)
                return end_time
            else:
                # 当天无法完成，消耗当天所有时间，移动到下一天
                remaining_hours -= available_hours_today
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=work_start_hour, minute=0, second=0, microsecond=0
                )
        
        # 回退：直接返回开始时间加上工序时长
        return start_time + timedelta(hours=duration_hours)
    
    def _calculate_resource_load(
        self, 
        resource_id: int, 
        reference_date: datetime
    ) -> float:
        """计算资源在参考日期当天的负荷（小时）"""
        day_start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        total_load = 0
        for start, end, _, _, _ in self.resource_slots.get(resource_id, []):
            if start < day_end and end > day_start:
                overlap_start = max(start, day_start)
                overlap_end = min(end, day_end)
                total_load += (overlap_end - overlap_start).total_seconds() / 3600
        
        return total_load
    
    def schedule_order(
        self,
        order: models.ProductionOrder,
        consider_capacity: bool = True
    ) -> List[Dict]:
        """
        对单个订单进行稳定向前排程（兼容接口）
        
        Args:
            order: 要排程的订单
            consider_capacity: 是否考虑有限产能
        
        Returns:
            排程结果列表
        """
        self.finite_capacity = consider_capacity
        self._load_existing_schedule()
        
        result = self._schedule_order_stable(order)
        
        if result['success']:
            return result.get('operations', [])
        return []


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
